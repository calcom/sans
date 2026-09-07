#!/usr/bin/env python3
"""
Publish the built house faces into wm-primitives — the copy every app is MEANT to read.

wm-primitives/fonts/ is the intended single copy, and pushing there fires
wm-primitives' notify.yml, which dispatches font-proofer, ReCal and opsz-proofer.

What that does NOT do is change the font on any of those pages. Only opsz-proofer
actually reads shared/fonts/ (build.py:69). font-proofer loads its own src/fonts/
(index.css:33) and ReCal its own public/fonts/ (main.tsx:15), neither of which any build
step refreshes. So the dispatch fires, the deploys go green, and the rendered font does
not move. ReCal served a 58-day-old face through six successful --bump runs; see
MarkFonts/calbuild#55 for the measurements.

This function therefore publishes and notifies. It cannot verify, and must not claim,
that anything downstream now renders this build. The consumer-side repair is tracked in
MarkFonts/wm-primitives#6; until it lands, treat a green run as "the submodule moved",
not "the font is live".

Hand-copying is what this replaces, and it had already rotted: fonts/README.md said
1.999 (fcf0594) while the binary beside it was 2.000, and font-proofer's own copy was a
third build again. A version you have to remember to type is a version that goes stale.

Nothing here builds. It moves what the pipeline just produced.
"""

import re
import shutil
import subprocess
import sys
import time
from pathlib import Path

from fontTools.ttLib import TTFont

from scripts import config


# src (in calbuild) -> name in wm-primitives/fonts/, and the FeatureVariations count that
# proves the file is intact. See THE GATE below for why the count is the thing checked.
FACES = [
    ("fonts/calsans-var-full/CalSansVF.ttf",               "CalSansVF.ttf",        15),
    ("fonts/calsans-var-full/CalSansVF.woff2",             "CalSansVF.woff2",      15),
    ("fonts/calsans-var-flex/CalSansFlexVF.ttf",           "CalSansFlexVF.ttf",    15),
    ("fonts/calsans-var-flex/CalSansFlexVF.woff2",         "CalSansFlexVF.woff2",  15),
]

# NOT published, and deliberately absent from FACES: wm-primitives/fonts/CalSans-Bold.woff2
# is the 2021 Cal Sans, Version 1.000, 613 glyphs — a historical reference kept for
# font-proofer's before/after page, not a house face. calbuild can build a file with that
# exact name (a v2 static at GEOM 50 / opsz 45), and publishing it would silently replace
# the only copy of the old drawing with a new one, leaving the comparison showing v2
# against v2. It shares a filename with something this pipeline produces and is otherwise
# unrelated to it. Leave it alone.
DO_NOT_PUBLISH = {"CalSans-Bold.woff2"}


def _git(repo, *args, check=True):
    r = subprocess.run(["git", "-C", str(repo), *args], capture_output=True, text=True)
    if check and r.returncode != 0:
        raise RuntimeError(f"git {' '.join(args)} failed:\n{r.stderr.strip()}")
    return r.stdout.strip()


def _gate():
    """THE GATE.

    Three things, all cheap, each aimed at a failure that has actually happened.

    1. FeatureVariations survived. The one failure that looks correct and is not: a
       subsetter told to keep only the features you named drops GSUB FeatureVariations.
       Every letterform is still there, so the font renders and proofs fine — but GEOM
       and opsz stop swapping glyphs, so `a`, `G`, `f`, `j`, `t`, `y` freeze and the
       small-optical `a` never appears.

    2. The four faces agree with each other, on glyph count and on name ID 5. They come
       from one build and must be one build. font-proofer once carried a CalSansVF at
       1541 glyphs while canonical was 1545 — a mixed set nothing was checking for
       (calbuild#55). Deliberately a consistency check and not a hardcoded 1545, which
       would need editing every time a glyph is drawn and would be quietly wrong until
       someone noticed.

    3. The version is readable at all. _sync_readme writes fonts/README.md from name ID 5,
       so an unparseable one means the README silently keeps its previous text.

    Publishing pushes to a repo three apps track. Without this, that is an automatic way
    to ship a broken or mismatched font to all of them, which is worse than no automation.
    """
    problems, rows, seen = [], [], {}
    for src, _, want in FACES:
        p = Path(src)
        if not p.exists():
            problems.append(f"{src}: missing — has the build run?")
            continue
        font = TTFont(p)
        fv = getattr(font["GSUB"].table, "FeatureVariations", None)
        got = len(fv.FeatureVariationRecord) if fv else 0
        glyphs = font["maxp"].numGlyphs
        ver = font["name"].getDebugName(5) or ""
        seen[p.name] = (glyphs, ver)
        rows.append(f"   {p.name:22} FeatureVariations={got:<3} (want {want})  "
                    f"{glyphs} glyphs  {ver}")
        if got != want:
            problems.append(f"{src}: FeatureVariations={got}, expected {want}")
        if not re.search(r"Version\s+[\d.]+", ver):
            problems.append(f"{src}: name ID 5 is {ver!r} — _sync_readme cannot parse that")
    print("\n".join(rows))

    # One build, or none. A set that disagrees with itself is two runs mixed together.
    for label, idx in (("glyph count", 0), ("version", 1)):
        values = {v[idx] for v in seen.values()}
        if len(values) > 1:
            detail = ", ".join(f"{n}={v[idx]}" for n, v in sorted(seen.items()))
            problems.append(f"faces disagree on {label}: {detail}")

    if problems:
        print("\n   REFUSING TO PUBLISH:")
        for prob in problems:
            print(f"     • {prob}")
        raise SystemExit(1)


def _sync_readme(primitives: Path):
    """Read the version off the font instead of trusting the prose.

    The first line of fonts/README.md carries `Cal Sans <version> (<sha>)`. It is derived
    here because the hand-maintained one was wrong within a single release cycle.
    """
    name5 = TTFont("fonts/calsans-var-full/CalSansVF.ttf")["name"].getDebugName(5) or ""
    m = re.search(r"Version\s+([\d.]+);\s*([0-9a-f]+)", name5)
    if not m:
        print(f"   ! could not read a version from name ID 5 ({name5!r}) — README left alone")
        return
    readme = primitives / "fonts" / "README.md"
    if not readme.exists():
        return
    s = readme.read_text()
    s2 = re.sub(r"Cal Sans \d+\.\d+ \([0-9a-f]+\)", f"Cal Sans {m.group(1)} ({m.group(2)})", s, count=1)
    if s2 != s:
        readme.write_text(s2)
        print(f"   README → Cal Sans {m.group(1)} ({m.group(2)})")


def bump_primitives(path=None, push=True):
    """Copy the built faces into a wm-primitives checkout, commit, and push."""
    primitives = Path(path or config.PRIMITIVES_PATH).expanduser().resolve()
    dest = primitives / "fonts"
    if not dest.is_dir():
        # Two very different people see this: someone outside WORDMARK who found the flag
        # and has no such checkout, and Mark with a typo in a path. Keep the path in the
        # message so the second case is still debuggable.
        raise SystemExit(
            f"\n     🚫 ACCESS DENIED. You're not WORDMARK, are you?\n"
            f"     Nice try though. This one only works from Mark's laptop, and\n"
            f"     even he has to be on the right branch.\n\n"
            f"     (Looked for fonts/ in {primitives} and found nothing.\n"
            f"      If you ARE Mark: check the path, you've fat-fingered it again.)")

    _gate()

    # Refuse to publish on top of someone's work in progress. A commit here reaches four
    # repos, so it may not carry anything the person running a font build did not intend.
    branch = _git(primitives, "rev-parse", "--abbrev-ref", "HEAD")
    if branch != "main":
        raise SystemExit(f"{primitives} is on '{branch}', not main — refusing to publish")
    if _git(primitives, "status", "--porcelain", "--", "fonts"):
        raise SystemExit(f"{primitives}/fonts has uncommitted changes — refusing to publish over them")

    clash = DO_NOT_PUBLISH & {name for _, name, _ in FACES}
    if clash:
        raise SystemExit(
            f"{', '.join(sorted(clash))} is in FACES but must never be published — "
            "see DO_NOT_PUBLISH")

    changed = []
    for src, name, _ in FACES:
        target = dest / name
        if target.exists() and target.read_bytes() == Path(src).read_bytes():
            continue
        shutil.copy2(src, target)
        changed.append(name)

    _sync_readme(primitives)

    if not _git(primitives, "status", "--porcelain", "--", "fonts"):
        print("   primitives already matches this build — nothing to publish")
        return
    print(f"   copied: {', '.join(changed) or '(README only)'}")

    sha = _git(Path("."), "rev-parse", "--short", "HEAD")
    _git(primitives, "add", "fonts")
    _git(primitives, "commit", "-m", f"fonts: publish from calbuild {sha}")

    if not push:
        print(f"   committed in {primitives}. Push it to start the deploy chain:")
        print(f"     git -C {primitives} push origin main")
        return

    # Retry on a rebase rather than a bare push. A bare push is what took every consumer
    # deploy down for a day: another run lands first, this one is rejected
    # non-fast-forward, and the step fails after the work is already done.
    for n in range(5):
        r = subprocess.run(["git", "-C", str(primitives), "push", "origin", "HEAD:main"],
                           capture_output=True, text=True)
        if r.returncode == 0:
            print("   pushed — notify.yml will dispatch font-proofer, ReCal and opsz-proofer")
            print("   NOTE: that updates the submodule and redeploys them. It does NOT")
            print("         change the rendered font in font-proofer or ReCal, which load")
            print("         their own bundled copies (calbuild#55). Only opsz-proofer")
            print("         reads shared/fonts/.")
            return
        print(f"   push rejected (attempt {n + 1}) — rebasing on origin/main…")
        _git(primitives, "pull", "--rebase", "origin", "main")
        time.sleep(3)
    raise SystemExit("push failed after 5 attempts")
