#!/usr/bin/env python3
"""
Character-alternative documentation build step.

Walks every cvXX / ssXX feature in the compiled variable font, collects the
glyphs each one PRODUCES, draws each distinct produced glyph as a light and a
dark SVG, and writes a single markdown table — one row per feature.

    python3 -m scripts.lib.charalts fonts/calsans-var-full/CalSansVF.ttf \
        -o docs/character-alternatives.md

Layout follows Iosevka's character-variants.md: a 128x160 cell, the outline
pre-negated in a <defs> path, and the fill baked in (rather than a CSS media
query) because Safari does not honour prefers-color-scheme inside an SVG
loaded through <img>. GitHub picks the right file with <picture>.
"""
import argparse
import os
import re
import subprocess
import sys

from fontTools.ttLib import TTFont
from fontTools.pens.svgPathPen import SVGPathPen
from fontTools.pens.transformPen import TransformPen

from scripts import config

CELL_W, CELL_H = 128, 160
SCALE = 0.096
BASELINE_Y = 104.99201
FILL_LIGHT = "#20242e"
FILL_DARK = "#dee4e3"


# ---------------------------------------------------------------- GSUB walk

def _lookup(gsub, index):
    return gsub.LookupList.Lookup[index]


def _targets_from_lookup(gsub, lookup, out, seen_lookups):
    """Every glyph name this lookup can OUTPUT, recursing through context."""
    lid = id(lookup)
    if lid in seen_lookups:
        return
    seen_lookups.add(lid)

    for sub in lookup.SubTable:
        t = lookup.LookupType
        # Extension — unwrap and re-dispatch on the real subtable.
        if t == 7:
            inner = sub.ExtSubTable
            shim = type("L", (), {"LookupType": sub.ExtensionLookupType,
                                  "SubTable": [inner]})()
            _targets_from_lookup(gsub, shim, out, seen_lookups)
            continue
        if t == 1:                                   # single
            out.update(sub.mapping.values())
        elif t == 2:                                 # multiple
            for seq in sub.mapping.values():
                out.update(seq)
        elif t == 3:                                 # alternate
            for alts in sub.alternates.values():
                out.update(alts)
        elif t == 4:                                 # ligature
            for ligs in sub.ligatures.values():
                out.update(l.LigGlyph for l in ligs)
        elif t in (5, 6):                            # (chain) context
            for rec in _nested_records(sub):
                _targets_from_lookup(gsub, _lookup(gsub, rec.LookupListIndex),
                                     out, seen_lookups)


def _nested_records(sub):
    """The SubstLookupRecords of any context/chain-context format."""
    for attr in ("SubstLookupRecord",):
        if getattr(sub, attr, None):
            yield from getattr(sub, attr)
    for attr in ("SubRuleSet", "SubClassSet", "ChainSubRuleSet", "ChainSubClassSet"):
        for rs in getattr(sub, attr, None) or []:
            if rs is None:
                continue
            for rules in ("SubRule", "SubClassRule", "ChainSubRule", "ChainSubClassRule"):
                for rule in getattr(rs, rules, None) or []:
                    yield from getattr(rule, "SubstLookupRecord", None) or []


def _count_substitutions(gsub, lookup, seen_lookups):
    """How many individual rules the feature carries — the '71 substitutions'
    figure. Counted separately from the distinct outputs because several rules
    routinely land on the same glyph (a, a.rclt1, a.rclt2 -> a.ss01)."""
    n = 0
    for sub in lookup.SubTable:
        t = lookup.LookupType
        if t == 7:
            inner = sub.ExtSubTable
            shim = type("L", (), {"LookupType": sub.ExtensionLookupType,
                                  "SubTable": [inner]})()
            n += _count_substitutions(gsub, shim, seen_lookups)
        elif t == 1:
            n += len(sub.mapping)
        elif t == 2:
            n += len(sub.mapping)
        elif t == 3:
            n += len(sub.alternates)
        elif t == 4:
            n += sum(len(v) for v in sub.ligatures.values())
        elif t in (5, 6):
            for rec in _nested_records(sub):
                l = _lookup(gsub, rec.LookupListIndex)
                if id(l) not in seen_lookups:
                    seen_lookups.add(id(l))
                    n += _count_substitutions(gsub, l, set())
    return n


def features(font):
    """[(tag, label, [produced glyph names], substitution count)] in tag order.

    A tag can appear once per script/language; the records are merged so a
    feature registered for both latn and DFLT is documented once."""
    gsub = font["GSUB"].table
    names = font["name"]
    merged = {}
    for fr in gsub.FeatureList.FeatureRecord:
        tag = fr.FeatureTag
        if not re.fullmatch(r"(cv\d\d|ss\d\d)", tag):
            continue
        entry = merged.setdefault(tag, {"ui": None, "lookups": set()})
        fp = fr.Feature.FeatureParams
        if fp is not None and entry["ui"] is None:
            entry["ui"] = getattr(fp, "UINameID", None) or \
                          getattr(fp, "FeatUILabelNameID", None)
        entry["lookups"].update(fr.Feature.LookupListIndex)

    out = []
    # ss before cv: the stylistic sets are the headline feature, the character
    # variants are the per-glyph fine print underneath them.
    for tag in sorted(merged, key=lambda t: (t[:2] != "ss", t)):
        entry = merged[tag]
        label = names.getDebugName(entry["ui"]) if entry["ui"] else tag
        produced, seen, count = set(), set(), 0
        for li in sorted(entry["lookups"]):
            lk = _lookup(gsub, li)
            _targets_from_lookup(gsub, lk, produced, seen)
            count += _count_substitutions(gsub, lk, set())
        out.append((tag, label or tag, sorted(produced), count))
    return out


# ------------------------------------------------------------------- SVG

def draw(glyph_set, hmtx, name, fill):
    """One 128x160 cell. The path is emitted Y-DOWN (pre-negated) to match the
    reference cells, so the <g> carries a positive scale — a TransformPen does
    the flip, not a negative scale, which would also mirror the winding."""
    pen = SVGPathPen(glyph_set, ntos=lambda v: str(int(round(v))))
    glyph_set[name].draw(TransformPen(pen, (1, 0, 0, -1, 0, 0)))
    d = pen.getCommands()
    x = (CELL_W - hmtx[name][0] * SCALE) / 2
    return (
        '<?xml version="1.0" encoding="UTF-8" standalone="no"?>\n'
        f'<svg height="{CELL_H}" viewBox="0 0 {CELL_W} {CELL_H}" '
        f'width="{CELL_W}" xmlns="http://www.w3.org/2000/svg">\n'
        f'<defs>\n<path d="{d}" id="path1"/>\n</defs>\n<g>\n'
        f'<g data-glyph="{name}" fill="{fill}" '
        f'transform="translate({x:.5f} {BASELINE_Y:.5f}) rotate(0) scale({SCALE})">\n'
        f'<use href="#path1"/>\n</g>\n</g>\n</svg>\n'
    )


def slug(name):
    """Glyph name -> filename stem. '.' is the only character Glyphs names
    carry that reads badly in a path next to the .light/.dark suffix."""
    return name.replace(".", "-")


# ------------------------------------------------------------------ markdown

def anchor(tag, label):
    """GitHub's heading slug for '## `cv01` \u2014 Geometric a'. Backticks and the
    em dash vanish, spaces become hyphens, '/' is dropped."""
    text = f"{tag} \u2014 {label}".lower()
    text = re.sub(r"[^\w\s-]", "", text)
    return re.sub(r"\s+", "-", text.strip())


def cell(rel, name):
    s = slug(name)
    return (f'<td align="center"><picture>'
            f'<source media="(prefers-color-scheme: dark)" srcset="{rel}/{s}.dark.svg">'
            f'<img alt="{name}" src="{rel}/{s}.light.svg" width="46"></picture></td>')


def table(tag, label, glyphs, rel):
    head = (f'<td rowspan="2" align="left"><code><b>{tag}</b></code>'
            f'<br><sub>{label}</sub><br><sub>{len(glyphs)} forms</sub></td>')
    imgs = "".join(cell(rel, g) for g in glyphs)
    labs = "".join(f'<td align="center"><sub><code>{g}</code></sub></td>' for g in glyphs)
    return (f"<table>\n<tr>{head}{imgs}</tr>\n<tr>{labs}</tr>\n</table>\n")



def build(font_path, out_md=None, svg_dir=None, quiet=False):
    """Regenerate the whole doc. Returns (feature count, cell count, files written).

    Every cell is rewritten rather than skipped-if-present: the outlines change
    with the font, so a stale SVG is worse than a slow write. Cells for glyphs
    that no longer exist are pruned, so the folder can never accumulate orphans."""
    out_md = out_md or config.CHARALTS_MD
    svg_dir = svg_dir or config.CHARALTS_SVG_DIR

    font = TTFont(font_path)
    glyph_set = font.getGlyphSet()
    hmtx = font["hmtx"]
    version = font["name"].getDebugName(5) or ""

    os.makedirs(os.path.dirname(os.path.abspath(out_md)) or ".", exist_ok=True)
    os.makedirs(svg_dir, exist_ok=True)
    rel = os.path.relpath(svg_dir, os.path.dirname(os.path.abspath(out_md)))

    feats = features(font)
    written, keep, body = 0, set(), []
    for tag, label, glyphs, count in feats:
        glyphs = [g for g in glyphs if g in glyph_set]
        for g in glyphs:
            for suffix, fill in (("light", FILL_LIGHT), ("dark", FILL_DARK)):
                fname = f"{slug(g)}.{suffix}.svg"
                keep.add(fname)
                with open(os.path.join(svg_dir, fname), "w") as fh:
                    fh.write(draw(glyph_set, hmtx, g, fill))
                written += 1
        plural = "form" if len(glyphs) == 1 else "forms"
        body.append(f"## `{tag}` \u2014 {label}\n\n"
                    f"{count} substitutions produce **{len(glyphs)} distinct {plural}**.\n\n"
                    + table(tag, label, glyphs, rel))

    pruned = 0
    for stale in os.listdir(svg_dir):
        if stale.endswith(".svg") and stale not in keep:
            os.remove(os.path.join(svg_dir, stale))
            pruned += 1

    header = (
        "# Character Alternatives of Cal Sans\n\n"
        f"Generated from `{os.path.basename(font_path)}` \u2014 {version}.\n\n"
        "Every glyph each feature **produces**, one row per feature. Rows scroll "
        "horizontally. Light and dark cells are separate files because Safari "
        "ignores `prefers-color-scheme` inside an SVG loaded through `<img>`.\n\n"
    )
    def toc_line(prefix):
        links = [f"[`{t}`](#{anchor(t, l)})" for t, l, _, _ in feats
                 if t.startswith(prefix)]
        return " \u00b7 ".join(links)

    # Two separate paragraphs, not one run-on list: at a glance the reader has to
    # be able to see where the stylistic sets stop and the character variants start.
    toc = (f"**Stylistic sets**\n\n{toc_line('ss')}\n\n"
           f"**Character variants**\n\n{toc_line('cv')}\n\n---\n\n")
    with open(out_md, "w") as fh:
        fh.write(header + toc + "\n".join(body))

    cells = sum(len([g for g in gl if g in glyph_set]) for _, _, gl, _ in feats)
    if not quiet:
        print(f"{len(feats)} features, {cells} cells, {written} SVGs written"
              + (f", {pruned} stale pruned" if pruned else ""))
        print(f"wrote {out_md}")
    return len(feats), cells, written


def spawn(font_path, log_path=None):
    """Kick the regen off as its OWN python process and return immediately.

    The build's own success report must not wait on ~900 SVG writes, and a
    failure in the docs must not fail the font build, so this is deliberately
    fire-and-forget: the child is detached into its own session and everything
    it prints goes to a log."""
    log_path = log_path or os.path.join(config.BUILD_DIR, "character-alternatives.log")
    os.makedirs(os.path.dirname(os.path.abspath(log_path)) or ".", exist_ok=True)
    log = open(log_path, "w")
    proc = subprocess.Popen(
        [sys.executable, "-m", "scripts.lib.charalts", str(font_path)],
        stdout=log, stderr=subprocess.STDOUT,
        cwd=os.getcwd(), start_new_session=True,
    )
    return proc, log_path


def main():
    ap = argparse.ArgumentParser(description="Build the character-alternatives doc")
    ap.add_argument("font")
    ap.add_argument("-o", "--out", default=None)
    ap.add_argument("--svg-dir", default=None)
    args = ap.parse_args()
    build(args.font, args.out, args.svg_dir)


if __name__ == "__main__":
    main()
