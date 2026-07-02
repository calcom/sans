import os
import re
import shutil
import subprocess
from multiprocessing import Pool
from pathlib import Path

from tqdm import tqdm
from fontTools import subset
from fontTools.ttLib import TTFont
from fontTools.ttLib.tables._f_v_a_r import NamedInstance
from scripts.lib.manifest import all_styles
from scripts.lib.build_flex import build_flex
from scripts.lib.utils import axis_by_tag
from scripts import config

_PFX = config.RELEASE_PACKAGE_PREFIX


# ── Helpers ───────────────────────────────────────────────────────────────────

def _compress_one(ttf_path: str):
    font = TTFont(ttf_path)
    font.flavor = "woff2"
    font.save(str(Path(ttf_path).with_suffix(".woff2")))


def _compress_dir(dir_path: Path):
    """WOFF2-compress every TTF in dir_path. Brotli is CPU-bound and per-file
    independent, so the files are farmed out across processes (like instancing)."""
    ttfs = [str(p) for p in sorted(dir_path.glob("*.ttf"))]
    if not ttfs:
        return
    workers = min(os.cpu_count() or 4, len(ttfs))
    with Pool(processes=workers) as pool:
        for _ in tqdm(pool.imap_unordered(_compress_one, ttfs), total=len(ttfs),
                      desc=f"   ↳ WOFF2 {dir_path.name}", leave=False):
            pass


def _copy_pair(src_dir: Path, filename: str, dest_dir: Path, woff2: bool = True) -> bool:
    """Copy TTF (+ WOFF2 unless woff2=False) to dest_dir. Returns True if TTF was found."""
    dest_dir.mkdir(parents=True, exist_ok=True)
    stem = Path(filename).stem
    found = False
    exts = (".ttf", ".woff2") if woff2 else (".ttf",)
    for ext in exts:
        src = src_dir / (stem + ext)
        if src.exists():
            shutil.copy2(src, dest_dir / src.name)
            if ext == ".ttf":
                found = True
    return found


def _subset_ss_cv(font: TTFont):
    """Strip ss/cv stylistic-set / character-variant features—and their now-
    unreferenced alternate glyphs—from an open font, in place."""
    feature_tags = set()
    for tag in ("GSUB", "GPOS"):
        if tag in font:
            feature_tags.update(fr.FeatureTag for fr in font[tag].table.FeatureList.FeatureRecord)
    # aalt ("access all alternates") points directly at ss/cv glyphs, so it
    # must go too or those glyphs survive subsetting via its closure
    keep_features = [t for t in feature_tags if t[:2].lower() not in ("ss", "cv") and t != "aalt"]

    options = subset.Options()
    options.layout_features = keep_features
    options.glyph_names = True
    options.notdef_outline = True
    options.recalc_bounds = True
    options.recalc_timestamp = False

    subsetter = subset.Subsetter(options=options)
    subsetter.populate(unicodes=font.getBestCmap().keys())
    subsetter.subset(font)


def _relabel_opsz_max(font: TTFont, new_max: float):
    """Relabel the opsz axis maximum down to new_max WITHOUT resampling outlines: gvar
    deltas live in normalized space and the large-optical master sits at normalized +1.0,
    so after lowering fvar maxValue, input=new_max still maps to that master design. This
    is a pure relabel (fvar/STAT/instance metadata) — not an instancer range-limit, which
    would interpolate a milder design at new_max. Used so cossui presents opsz 8–new_max
    while shipping the same display drawing the full build labels at the source max."""
    fvar = font["fvar"]
    axis = axis_by_tag(fvar.axes, "opsz")
    old_max = axis.maxValue
    if new_max >= old_max:
        return
    axis.maxValue = new_max
    for inst in fvar.instances:
        if inst.coordinates.get("opsz") == old_max:
            inst.coordinates["opsz"] = new_max
    if "STAT" in font and font["STAT"].table.AxisValueArray:
        stat = font["STAT"].table
        opsz_idx = next((i for i, a in enumerate(stat.DesignAxisRecord.Axis)
                         if a.AxisTag == "opsz"), None)
        if opsz_idx is not None:
            for axv in stat.AxisValueArray.AxisValue:
                if getattr(axv, "AxisIndex", None) == opsz_idx and getattr(axv, "Value", None) == old_max:
                    axv.Value = new_max


def _strip_ss_cv(src_ttf: Path, dest_dir: Path, woff2: bool = True, opsz_max: float = None):
    """Write TTF (+ WOFF2 unless woff2=False) to dest_dir with ss/cv features subset out.
    If opsz_max is set, the opsz axis max is also relabeled down to it (see _relabel_opsz_max)."""
    dest_dir.mkdir(parents=True, exist_ok=True)
    font = TTFont(str(src_ttf))
    _subset_ss_cv(font)
    if opsz_max is not None:
        _relabel_opsz_max(font, opsz_max)

    dest_ttf = dest_dir / src_ttf.name
    font.save(str(dest_ttf))
    if woff2:
        font.flavor = "woff2"
        font.save(str(dest_ttf.with_suffix(".woff2")))


def _set_style_names(font: TTFont, subfamily: str):
    """Set the RIBBI + typographic name records for a single-style VF (Roman or Italic).
    Subsetting drops nameID 16/17, and the combined VF's defaults are the Roman ones, so
    rewrite both name IDs and the family/full/PS records on Windows + Mac platforms."""
    name = font["name"]
    family = name.getDebugName(16) or name.getDebugName(1) or "Cal Sans"
    full = f"{family} {subfamily}"
    ps = f"{family}-{subfamily}".replace(" ", "")
    for nid, val in ((1, family), (2, subfamily), (4, full), (6, ps), (16, family), (17, subfamily)):
        name.setName(val, nid, 3, 1, 0x0409)  # Windows, English (US)
        name.setName(val, nid, 1, 0, 0)        # Mac, Roman
    if subfamily == "Italic":
        if "OS/2" in font:
            os2 = font["OS/2"]
            os2.fsSelection = (os2.fsSelection & ~0x0040) | 0x0001  # clear REGULAR, set ITALIC
        if "head" in font:
            font["head"].macStyle |= 0x0002


def _trim_gf_instances(font: TTFont, ps_suffix: str = ""):
    """Google Fonts fvar spec: named instances must be Weight-only, each pinned at the
    shipping default of every OTHER axis. Replace fvar.instances with the config-defined
    GF weights (Regular/Medium/SemiBold/Bold) at GEOM=25 / opsz=14 (SHRP/YTAS at their
    fvar default). Re-adds PostScript-name entries so fvar_instance_ps_names stays happy."""
    fvar = font["fvar"]
    name = font["name"]
    family_ps = (name.getDebugName(6) or "CalSans").split("-")[0]
    axis_tags = [a.axisTag for a in fvar.axes]
    coords0 = {a.axisTag: a.defaultValue for a in fvar.axes}
    for tag, val in config.SHIPPING_DEFAULTS.items():      # GEOM=25, opsz=14
        if tag in coords0:
            coords0[tag] = val

    ital = ps_suffix == "-Italic"
    instances = []
    for wght, style in config.GF_WEIGHT_INSTANCES:
        coords = dict(coords0); coords["wght"] = wght
        ps_style = (("Italic" if style == "Regular" else style.replace(" ", "") + "Italic")
                    if ital else style.replace(" ", ""))
        inst = NamedInstance()
        inst.coordinates      = {t: coords[t] for t in axis_tags}
        inst.subfamilyNameID  = name.addName(style)
        inst.postscriptNameID = name.addName(f"{family_ps}-{ps_style}")
        instances.append(inst)
    fvar.instances = instances


def _hide_gf_parametric_axes(font: TTFont):
    """parametric_axes_hidden: set the fvar HIDDEN flag (bit 0) on the axes named in
    config.GF_HIDDEN_AXES. The axes still function; they're just not offered in UI."""
    for a in font["fvar"].axes:
        if a.axisTag in config.GF_HIDDEN_AXES:
            a.flags |= 0x0001  # HIDDEN_AXIS


def _distribution_sha() -> str:
    """Short git hash of the calcom/sans DISTRIBUTION repo for the version stamp — never
    calbuild. Env var wins (CI). Otherwise probe GF_SHA_REPO_CANDIDATES in order and use
    the first whose 'origin' remote is calcom/sans (so it works whether the builder runs
    inside calcom/sans or from a sibling calbuild). Returns "" if none match — the build
    stays unbroken for anyone else who runs this pipeline."""
    sha = os.environ.get(config.GF_VERSION_SHA_ENV, "").strip()
    if sha:
        return sha
    def _git(repo, *args):
        try:
            r = subprocess.run(["git", "-C", repo, *args], capture_output=True, text=True, timeout=5)
            return r.stdout.strip() if r.returncode == 0 else None
        except Exception:
            return None
    for repo in config.GF_SHA_REPO_CANDIDATES:
        origin = _git(repo, "remote", "get-url", "origin")
        if origin and config.GF_SHA_REMOTE_MATCH in origin:
            head = _git(repo, "rev-parse", "--short", "HEAD")
            if head:
                return head
    return ""


def _set_gf_version(font: TTFont):
    """name/version_format: nameID 5 must read 'Version X.YYY'. Base version comes from
    head.fontRevision (the Glyphs Version field); the calcom/sans build hash is appended
    for traceability (see _distribution_sha)."""
    v = f"{config.GF_VERSION_PREFIX}{font['head'].fontRevision:.3f}"
    sha = _distribution_sha()
    if sha:
        v += f"; {sha}"
    name = font["name"]
    name.setName(v, 5, 3, 1, 0x0409)  # Windows, English (US)
    name.setName(v, 5, 1, 0, 0)        # Mac, Roman


def _set_gf_name_overrides(font: TTFont):
    """gf-api-only: Designer (nameID 9, GF-mandatory) + Copyright (nameID 0, GF canonical
    pattern). Every other build keeps the source's own Designer/Copyright values."""
    name = font["name"]
    for val, nid in ((config.GF_DESIGNER, 9), (config.GF_COPYRIGHT, 0)):
        name.setName(val, nid, 3, 1, 0x0409)  # Windows, English (US)
        name.setName(val, nid, 1, 0, 0)        # Mac, Roman


def _build_gf_api(src_ttf: Path, dest_dir: Path):
    """gf-api ships roman + italic as TWO variable fonts (Google Fonts spec): the ital
    axis is instanced out of fvar and survives only as a STAT style-link record (Roman
    elidable, linkedValue → Italic). Both files derive from the combined VF — its masters
    sit exactly at ital 0/1, so the pin is lossless. ss/cv are subset out like cossui."""
    from fontTools.varLib.instancer import instantiateVariableFont
    dest_dir.mkdir(parents=True, exist_ok=True)

    probe = TTFont(str(src_ttf))
    has_ital = any(a.axisTag == "ital" for a in probe["fvar"].axes)
    family_ps = (probe["name"].getDebugName(16) or "Cal Sans").replace(" ", "")
    m = re.search(r"\[([^\]]*)\]", src_ttf.stem)
    tags = m.group(1).split(",") if m else [a.axisTag for a in probe["fvar"].axes]
    # canonical_filename: GF wants axis tags sorted (ASCII → uppercase axes first).
    bracket = ",".join(sorted(t.strip() for t in tags if t.strip() != "ital"))

    targets = [(0, "", "Regular")] + ([(1, "-Italic", "Italic")] if has_ital else [])
    for ital_value, suffix, subfamily in targets:
        font = TTFont(str(src_ttf))
        _subset_ss_cv(font)
        if has_ital:
            instantiateVariableFont(font, {"ital": ital_value}, inplace=True, updateFontNames=False)
        _set_style_names(font, subfamily)
        if config.GF_TRIM_INSTANCES:
            _trim_gf_instances(font, ps_suffix=suffix)
        _hide_gf_parametric_axes(font)   # parametric_axes_hidden
        _set_gf_version(font)            # name/version_format ("Version X.YYY"[; sha])
        _set_gf_name_overrides(font)     # GF Designer (nameID 9) + Copyright (nameID 0)
        dest_ttf = dest_dir / f"{family_ps}{suffix}[{bracket}].ttf"
        font.save(str(dest_ttf))
        font.flavor = "woff2"
        font.save(str(dest_ttf.with_suffix(".woff2")))


def _report(pkg_dir: Path, label: str):
    count = sum(1 for p in pkg_dir.rglob("*") if p.is_file()) if pkg_dir.exists() else 0
    print(f"   ✅ {label} ({count} files)")


# ── Public API ────────────────────────────────────────────────────────────────

def compress_build_outputs(build_dir: str):
    """Compress all TTFs in scripts/temp/variable and scripts/temp/static to WOFF2."""
    build_path = Path(build_dir)
    print("🗜  Compressing TTFs to WOFF2...")
    for sub in ("variable", "static"):
        d = build_path / sub
        if d.exists():
            _compress_dir(d)


def build_release_folders(build_dir: str, output_dir: str, build_italic: bool = False,
                          flex_var_ttf: str = None):
    build_path = Path(build_dir)
    out_path   = Path(output_dir)
    var_dir    = build_path / "variable"
    static_dir = build_path / "static"

    styles = all_styles(build_italic)

    if out_path.exists():
        shutil.rmtree(out_path)
    out_path.mkdir()

    # fonts/ is wiped above, so re-emit its README each run from the source copy.
    readme_src = Path(__file__).parent / "fonts_README.md"
    if readme_src.exists():
        shutil.copy2(readme_src, out_path / "README.md")

    print("📦 Building release folders...")
    missing = 0

    def copy_styles(subset: list, dest: Path, woff2: bool = True):
        nonlocal missing
        for s in subset:
            if not _copy_pair(static_dir, s["filename"], dest, woff2=woff2):
                missing += 1

    # ── Variable packages ─────────────────────────────────────────────────────

    pkg = out_path / f"{_PFX}-var-full"
    for ttf in sorted(var_dir.glob("*.ttf")):
        _copy_pair(var_dir, ttf.name, pkg)
    _report(pkg, f"{_PFX}-var-full")

    # var-flex: the HOI morphing build (Flex-family only) → avar2, YTAS hidden/slaved to opsz.
    # Uses the HOI variable TTF when the flex stage produced one; else falls back to the base VF.
    pkg = out_path / f"{_PFX}-var-flex"
    pkg.mkdir(parents=True, exist_ok=True)
    flex_input = flex_var_ttf or next((str(t) for t in sorted(var_dir.glob("*.ttf"))), None)
    if flex_input:
        build_flex(flex_input, str(pkg))
    _report(pkg, f"{_PFX}-var-flex")

    # cossui: combined VF (ital axis retained), ss/cv stripped — single file.
    # opsz capped at 32 (source tops out at 45); default optical size unchanged.
    pkg = out_path / f"{_PFX}-cossui"
    for ttf in sorted(var_dir.glob("*.ttf")):
        _strip_ss_cv(ttf, pkg, opsz_max=config.COSSUI_OPSZ_MAX)
    _report(pkg, f"{_PFX}-cossui")

    # gf-api: GF spec — roman + italic shipped as TWO variable fonts, ital instanced
    # out of fvar and kept only as a STAT style-link record.
    pkg = out_path / f"{_PFX}-gf-api"
    if config.GF_TRIM_INSTANCES:
        print("   ⚠️  GF fvar spec: trimming named instances to Weight-only "
              "(Regular/Medium/SemiBold/Bold) at GEOM=25, opsz=14 —")
        print("      confirm with Dave if differently named GEOM builds would be "
              "allowed into Google Fonts.")
    for ttf in sorted(var_dir.glob("*.ttf")):
        _build_gf_api(ttf, pkg)
    _report(pkg, f"{_PFX}-gf-api")

    # ── Static packages ───────────────────────────────────────────────────────

    # static-full: every static instance (192 roman, 384 with italic),
    # split into ttf/ and woff2/ subfolders.
    pkg = out_path / f"{_PFX}-static-full"
    ttf_dir, woff2_dir = pkg / "ttf", pkg / "woff2"
    ttf_dir.mkdir(parents=True, exist_ok=True)
    woff2_dir.mkdir(parents=True, exist_ok=True)
    for s in styles:
        stem = Path(s["filename"]).stem
        src_ttf, src_woff2 = static_dir / f"{stem}.ttf", static_dir / f"{stem}.woff2"
        if src_ttf.exists():
            shutil.copy2(src_ttf, ttf_dir / src_ttf.name)
        else:
            missing += 1
        if src_woff2.exists():
            shutil.copy2(src_woff2, woff2_dir / src_woff2.name)
    _report(pkg, f"{_PFX}-static-full")

    # per-GEOM: base YTAS/SHRP only → 12 roman now, 24 when italic is added
    for geom_id in config.PER_GEOM_PACKAGE_IDS:
        subset = [s for s in styles if s["geom"] == geom_id and s["ytas"] == "base" and s["shrp"] == "base"]
        pkg = out_path / f"{_PFX}-static-{geom_id}"
        copy_styles(subset, pkg)
        _report(pkg, f"{_PFX}-static-{geom_id}")

    # Cal Sans (Display/Base) + Cal Sans UI Text, base YTAS/SHRP, all 4 weights,
    # roman + italic → 8 roman / 16 with italic. Shared by essentials + gf-workspace.
    def is_text_family(s):
        if s["ytas"] != "base" or s["shrp"] != "base":
            return False
        return ((s["opsz"] == "display" and s["geom"] == "base") or
                (s["opsz"] == "text" and s["geom"] == "ui"))

    text_family_styles = [s for s in styles if is_text_family(s)]

    # static-essentials: the text family, ss/cv kept, TTF-only.
    pkg = out_path / f"{_PFX}-static-essentials"
    copy_styles(text_family_styles, pkg, woff2=False)
    _report(pkg, f"{_PFX}-static-essentials")

    # gf-workspace: same family for Google Fonts onboarding, but ss/cv (+ aalt and
    # their alternate glyphs) stripped like cossui/gf-api; TTF-only.
    pkg = out_path / f"{_PFX}-gf-workspace"
    pkg.mkdir(parents=True, exist_ok=True)
    for s in text_family_styles:
        src = static_dir / s["filename"]
        if src.exists():
            _strip_ss_cv(src, pkg, woff2=False)
        else:
            missing += 1
    _report(pkg, f"{_PFX}-gf-workspace")

    if not build_italic:
        print("⚠️  Built without italics (BUILD_ITALIC=False) — Cal Sans Display/Base "
              "italic styles are missing from calsans-static-essentials and calsans-gf-workspace")

    if missing:
        print(f"\n⚠️  {missing} expected static files not found in {static_dir}/")
        print(f"   Run fontmake first, or check style_name_to_filename() in scripts/manifest.py")

    print(f"\n✅ Release folders written to {output_dir}/")
