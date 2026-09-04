import os
import re
import shutil
import subprocess
from io import BytesIO
from multiprocessing import Pool
from pathlib import Path

from tqdm import tqdm
from fontTools import subset
from fontTools.ttLib import TTFont, newTable
from fontTools.ttLib.tables import otTables
from fontTools.ttLib.tables._f_v_a_r import NamedInstance
from scripts.lib.manifest import all_styles, style_name_to_filename
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

    # The subsetter drops name records it no longer sees referenced. For ss/cv UI names
    # that is exactly right — the features are gone. But it takes nameIDs 16/17 with them,
    # and a non-RIBBI static (Medium, SemiBold) needs those to style-link into its family
    # at all: without them Word and Docs list "Cal Sans Medium" as its own one-style family
    # instead of a weight of Cal Sans. Bold/Italic are unaffected, being genuine RIBBI.
    # _set_style_names already rebuilds them for the variable cuts; the statics had nothing
    # putting them back, so preserve them across the subset here for every caller.
    typographic = [n for n in font["name"].names if n.nameID in (16, 17)]

    subsetter = subset.Subsetter(options=options)
    subsetter.populate(unicodes=font.getBestCmap().keys())
    subsetter.subset(font)

    name = font["name"]
    for rec in typographic:
        # Only for platforms the subsetter kept. It prunes the Mac (platform 1) copies of
        # IDs 1/2 outright, so restoring a Mac 16/17 there would leave an orphan pair with
        # no legacy record to override.
        if name.getName(1, rec.platformID, rec.platEncID, rec.langID) is None:
            continue
        if name.getName(rec.nameID, rec.platformID, rec.platEncID, rec.langID) is None:
            name.names.append(rec)
    name.names.sort(key=lambda n: (n.platformID, n.platEncID, n.langID, n.nameID))


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


def _strip_ss_cv(src_ttf: Path, dest_dir: Path, woff2: bool = True, opsz_max: float = None,
                 gf_metrics: bool = False):
    """Write TTF (+ WOFF2 unless woff2=False) to dest_dir with ss/cv features subset out.
    If opsz_max is set, the opsz axis max is also relabeled down to it (see _relabel_opsz_max).
    gf_metrics applies the GF vertical-metrics conformance pass (gf-workspace ships to GF)."""
    dest_dir.mkdir(parents=True, exist_ok=True)
    font = TTFont(str(src_ttf))
    _subset_ss_cv(font)
    if opsz_max is not None:
        _relabel_opsz_max(font, opsz_max)
    if gf_metrics:
        _apply_gf_conformance(font)

    dest_ttf = dest_dir / src_ttf.name
    font.save(str(dest_ttf))
    if woff2:
        font.flavor = "woff2"
        font.save(str(dest_ttf.with_suffix(".woff2")))


def _set_style_names(font: TTFont, subfamily: str, family: str = None):
    """Set the RIBBI + typographic name records for a single-style VF (Roman or Italic).
    Subsetting drops nameID 16/17, and the combined VF's defaults are the Roman ones, so
    rewrite both name IDs and the family/full/PS records on Windows + Mac platforms.
    `family` overrides the inherited family name (gf-api-textui renames the whole family)."""
    name = font["name"]
    family = family or name.getDebugName(16) or name.getDebugName(1) or "Cal Sans"
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
        if "post" in font:
            font["post"].italicAngle = config.ITALIC_ANGLE


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
        # The SUBFAMILY has to carry the slope too, not just the PostScript name: an
        # italic file whose instances read "Regular/Medium/SemiBold/Bold" claims to be
        # the roman. RIBBI elision applies — the 400 instance is "Italic", never
        # "Regular Italic".
        sub_style = (("Italic" if style == "Regular" else f"{style} Italic")
                     if ital else style)
        inst = NamedInstance()
        inst.coordinates      = {t: coords[t] for t in axis_tags}
        inst.subfamilyNameID  = name.addName(sub_style)
        inst.postscriptNameID = name.addName(f"{family_ps}-{ps_style}")
        instances.append(inst)
    fvar.instances = instances
    # Guard the exact regression this function shipped once: an italic cut whose named
    # instances read Regular/Medium/SemiBold/Bold, claiming to be the roman. Cheap, and
    # it fires at the point of generation rather than in a QA run weeks later.
    if ital:
        missing = [name.getDebugName(i.subfamilyNameID) for i in instances
                   if "Italic" not in (name.getDebugName(i.subfamilyNameID) or "")]
        if missing:
            raise AssertionError(
                f"italic fvar instances without a slope in the name: {missing}")


def _hide_gf_parametric_axes(font: TTFont):
    """parametric_axes_hidden: set the fvar HIDDEN flag (bit 0) on the axes named in
    config.GF_HIDDEN_AXES. The axes still function; they're just not offered in UI."""
    for a in font["fvar"].axes:
        if a.axisTag in config.GF_HIDDEN_AXES:
            a.flags |= 0x0001  # HIDDEN_AXIS


# What the underline override did in the package currently being written, so the build
# log can say so once per folder instead of once per file.
_UNDERLINE_NOTICE = {"count": 0, "was": set()}


def _set_gf_underline(font: TTFont):
    """Pin underline thickness/position to the Medium values across every GF style.

    Cal Sans interpolates underline thickness with weight; GF requires one value for the
    whole family (opentype/family/underline_thickness). Medium is the midpoint of the
    78-100 range the family spans."""
    post = font["post"]
    if post.underlineThickness != config.GF_UNDERLINE_THICKNESS:
        _UNDERLINE_NOTICE["was"].add(post.underlineThickness)
        _UNDERLINE_NOTICE["count"] += 1
    post.underlineThickness = config.GF_UNDERLINE_THICKNESS
    post.underlinePosition  = config.GF_UNDERLINE_POSITION


def _family_name(font: TTFont) -> str:
    """The family a font belongs to, for preset lookup. nameID 16 is authoritative where
    it exists; nameID 1 carries the style for non-RIBBI names ("Cal Sans Text UI
    SemiBold"), which gf_metrics_for resolves by prefix."""
    name = font["name"]
    return name.getDebugName(16) or name.getDebugName(1) or ""


def _set_gf_vertical_metrics(font: TTFont):
    """GF vertical-metrics conformance — see the GF_* notes in config.

    Every value is set explicitly rather than derived from what the source happened to
    carry: GF's scheme wants hhea, typo and win in agreement, which is a different shape
    from the main build's cap-centred one, so deriving any of them from the other would
    quietly reintroduce the main build's numbers."""
    os2, hhea = font["OS/2"], font["hhea"]
    m = config.gf_metrics_for(_family_name(font))
    if config.GF_USE_TYPO_METRICS:
        os2.fsSelection |= 1 << 7                  # USE_TYPO_METRICS
    os2.sTypoAscender  = m["typo_ascender"]
    os2.sTypoDescender = m["typo_descender"]
    os2.sTypoLineGap   = m["typo_line_gap"]
    hhea.ascent  = m["hhea_ascent"]
    hhea.descent = m["hhea_descent"]
    hhea.lineGap = m["hhea_line_gap"]
    # win is the clipping box. Emma's 1029/283 fits the Text UI VF exactly, but a cut at
    # a wider GEOM/YTAS position reaches further, so her numbers are a FLOOR rather than
    # the value — and GF checks win at FAMILY level, requiring one shared pair covering
    # every style's ink. _unify_family_win_metrics does that once the folder is written;
    # this only guarantees the floor for a font examined on its own.
    head = font["head"]
    os2.usWinAscent  = max(m["win_ascent"],  head.yMax)
    os2.usWinDescent = max(m["win_descent"], -head.yMin)


def _set_variations_ps_prefix(font: TTFont):
    """nameID 25 — the prefix apps build a PostScript name from for an arbitrary point in
    the design space (not just the named instances). GF requires it on an italic variable
    font, ending in "Italic", so a synthesised name cannot come out claiming the roman.

    Derived from nameID 6 with the hyphen and any style dropped, since ID 6 is already the
    family's own PostScript spelling."""
    if "fvar" not in font:
        return
    name = font["name"]
    ps = name.getDebugName(6) or ""
    prefix = ps.split("-")[0]
    if not prefix:
        return
    if font["OS/2"].fsSelection & 0x0001:
        prefix += "Italic"
    for pid, eid, lid in ((3, 1, 0x409), (1, 0, 0)):
        name.setName(prefix, 25, pid, eid, lid)


def _drop_typographic_names(font: TTFont):
    """Remove nameIDs 16/17 wherever they say nothing IDs 1/2 don't already.

    Variable: always. With the VF origin at Regular the two pairs are necessarily the
    same, which is why Emma's review cites this one against the VFs.

    Static: only when redundant. "Cal Sans"/"Bold" duplicates IDs 1/2 exactly and GF
    reports it as an error (expected "N/A"); "Cal Sans"/"Medium" does NOT, because a
    non-RIBBI style has to pose as "Cal Sans Medium"/"Regular" in IDs 1/2 and would
    otherwise show up in Word and Docs as its own one-style family."""
    if not config.GF_DROP_TYPOGRAPHIC_NAMES:
        return
    name = font["name"]
    if "fvar" in font:
        name.names = [n for n in name.names if n.nameID not in (16, 17)]
        return
    keep = []
    for rec in name.names:
        if rec.nameID in (16, 17):
            # getDebugName falls back across platforms: a record whose same-platform
            # counterpart was pruned is still redundant if the name exists at all.
            plain = name.getName(rec.nameID - 15, rec.platformID, rec.platEncID, rec.langID)
            plain = str(plain) if plain is not None else name.getDebugName(rec.nameID - 15)
            if plain is not None and plain == str(rec):
                continue
        keep.append(rec)
    name.names = keep


def _fix_gf_stat(font: TTFont):
    """Un-elide the opsz axis values and make sure an 'ital' axis record exists.

    An elided axis value is one a UI is allowed to omit from the style name; that is
    wrong for optical size, where the reader has to be able to tell 8pt from 45pt. The
    ital record is what tells a browser the roman and italic VFs are one family."""
    if "STAT" not in font:
        return
    stat = font["STAT"].table
    axes = [a.AxisTag for a in stat.DesignAxisRecord.Axis]

    if config.GF_OPSZ_NEVER_ELIDABLE and "opsz" in axes:
        opsz_i = axes.index("opsz")
        for axv in getattr(stat.AxisValueArray, "AxisValue", []) or []:
            if getattr(axv, "AxisIndex", None) == opsz_i:
                axv.Flags &= ~0x0002                 # ELIDABLE_AXIS_VALUE_NAME

    if not config.GF_ENSURE_ITAL_STAT:
        return
    is_italic = bool(font["OS/2"].fsSelection & 0x0001)
    if "ital" in axes:
        ital_i = axes.index("ital")
    else:
        rec = otTables.AxisRecord()
        rec.AxisTag, rec.AxisOrdering = "ital", len(axes)
        rec.AxisNameID = font["name"].addName("Italic")
        stat.DesignAxisRecord.Axis.append(rec)
        stat.DesignAxisCount = len(stat.DesignAxisRecord.Axis)
        ital_i = len(axes)

    values = getattr(stat.AxisValueArray, "AxisValue", None) or []
    if is_italic:
        # An italic cut instanced out of the combined VF inherits the ROMAN's ital
        # records — both the elidable 0.0 and the style-link 1.0. fontbakery reads the
        # first it finds and sees an italic font asserting ital=0, so the italic must
        # carry exactly one record: 1.0, not elidable.
        values = [a for a in values if getattr(a, "AxisIndex", None) != ital_i]
        av = otTables.AxisValue()
        av.Format, av.AxisIndex, av.Value, av.Flags = 1, ital_i, 1.0, 0x0000
        av.ValueNameID = font["name"].addName("Italic")
        values.append(av)
        stat.AxisValueArray.AxisValue = values
        stat.AxisValueCount = len(values)
        return

    # Roman: leave an existing record set alone — it carries the style link to the
    # italic file, which is not ours to rebuild. Only add one if there is none at all.
    if any(getattr(a, "AxisIndex", None) == ital_i for a in values):
        return
    av = otTables.AxisValue()
    av.Format, av.AxisIndex, av.Value = 1, ital_i, 0.0
    av.Flags = 0x0002                                   # ELIDABLE — "Cal Sans", not "Cal Sans Roman"
    av.ValueNameID = font["name"].addName("Roman")
    values.append(av)
    stat.AxisValueArray.AxisValue = values
    stat.AxisValueCount = len(values)


def _add_meta(font: TTFont):
    """ScriptLangTags — what the font is designed for (dlng) and supports (slng)."""
    meta = font["meta"] if "meta" in font else newTable("meta")
    meta.data["dlng"] = ", ".join(config.GF_META_DESIGN_LANGS)
    meta.data["slng"] = ", ".join(config.GF_META_SUPPORT_LANGS)
    font["meta"] = meta


def _apply_gf_conformance(font: TTFont):
    """Every GF-only table fix, in one call so the four GF builders cannot drift apart."""
    _set_gf_name_overrides(font)
    _set_gf_underline(font)
    _set_gf_vertical_metrics(font)
    _set_variations_ps_prefix(font)
    _drop_typographic_names(font)
    _fix_gf_stat(font)
    _add_meta(font)


def _unify_family_win_metrics(pkg_dir: Path):
    """Give every style in a FAMILY one usWin pair, covering that family's own ink.

    Cal Sans and Cal Sans Text UI are separate families with separate design spaces, and
    they are onboarded to GF separately, so each gets the box its own outlines need rather
    than a shared one sized for whichever draws furthest. They happen to be delivered in
    the same workspace folder; that is a packaging detail, not a family relationship.

    Consequence worth knowing: fontbakery treats every font handed to it in one run as one
    family, so pointing family/win_ascent_and_descent at the whole workspace folder will
    report a mismatch between the two. Check each family separately —
    `fontbakery check-googlefonts <pkg>/CalSans-*.ttf` and then `<pkg>/CalSansTextUI-*.ttf`
    — which is how GF will look at them anyway.

    The per-family preset is the floor; measured ink can only raise it, never lower it."""
    families = {}
    for path in sorted(pkg_dir.glob("*.ttf")):
        font = TTFont(str(path), lazy=True)
        fam = _family_name(font) or path.name
        head = font["head"]
        families.setdefault(fam, []).append((path, head.yMax, -head.yMin))
        font.close()

    for fam, entries in sorted(families.items()):
        m = config.gf_metrics_for(fam)
        asc  = max([m["win_ascent"]]  + [e[1] for e in entries])
        desc = max([m["win_descent"]] + [e[2] for e in entries])
        for path, _, _ in entries:
            font = TTFont(str(path))
            os2 = font["OS/2"]
            if (os2.usWinAscent, os2.usWinDescent) == (asc, desc):
                font.close()
                continue
            os2.usWinAscent, os2.usWinDescent = asc, desc
            font.save(str(path))
            woff2 = path.with_suffix(".woff2")
            if woff2.exists():
                font.flavor = "woff2"
                font.save(str(woff2))
        print(f"   \U0001f4d0 {fam}: usWin {asc}/{desc} across {len(entries)} file(s)")


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
    """Every GF deliverable: Designer (nameID 9, GF-mandatory) + Copyright (nameID 0, GF
    canonical pattern). Non-GF builds keep the source's own Designer/Copyright values.

    Called from _apply_gf_conformance rather than the individual builders — it used to be
    wired into the two API paths only, so the workspace statics shipped the source string
    ("Copyright © 2026 by Designer Mark Davis DBA Wordmark") and failed font_copyright."""
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
        _apply_gf_conformance(font)      # names, v-metrics, STAT, meta
        dest_ttf = dest_dir / f"{family_ps}{suffix}[{bracket}].ttf"
        font.save(str(dest_ttf))
        font.flavor = "woff2"
        font.save(str(dest_ttf.with_suffix(".woff2")))


def _make_curved_l_default(font: TTFont):
    """gf-api-textui: make the curved l (.rcltA11y) the font's REAL default — a glyph-
    identity change, not just a feature. Three coordinated edits, all pre-pin/pre-subset:

    1. cmap: the l-family codepoints map directly to the curved glyphs, so shaping-free
       consumers (glyph palettes, PDF text extraction, thumbnailers) get the curved l too.
       Kerning/contextual GSUB for the curved forms already exist (the A11y statics use
       them), and GPOS binds by glyph — nothing else to move.
    2. curved twins for straight-keyed SingleSubst rules: chains like Marshallese locl
       (uni013C → uni013C.loclMAH) are keyed on the straight glyph the cmap no longer
       emits, so each such rule gets a parallel curved entry (→ the .rcltA11y target
       where one exists), keeping language forms reachable from the new defaults.
    3. rclt backstop: an unconditional SingleSubst (straight → curved) appended to the
       base rclt feature, catching straight glyphs GSUB itself emits mid-chain (e.g.
       ccmp decomposing ŀ to l + periodcentered). Appending must happen BEFORE
       instancing: at the Text UI pin (GEOM=25/opsz=10) no FeatureVariations record is
       active — the UI forms are the interpolation default — so the instancer sees an
       empty base rclt and prunes the whole feature (the matrix statics have no rclt).

    After this, the straight originals are typically unreachable and the ss/cv subset
    drops them; _save_with_curved_l_names then renames the curved glyphs to the
    canonical names on the final binary."""
    from fontTools.otlLib.builder import buildSingleSubstSubtable
    from fontTools.ttLib.tables import otTables as ot

    glyphs = set(font.getGlyphOrder())
    pairs = {g: g + config.GF_TEXTUI_ALT_SUFFIX for g in config.GF_TEXTUI_CURVED_L_GLYPHS
             if g in glyphs and g + config.GF_TEXTUI_ALT_SUFFIX in glyphs}
    dropped = sorted(set(config.GF_TEXTUI_CURVED_L_GLYPHS) - set(pairs))
    if dropped:
        print(f"   ⚠️  curved-l swap: {len(dropped)} pair(s) missing from the font, "
              f"skipped: {', '.join(dropped)}")

    # 1. cmap retarget
    for table in font["cmap"].tables:
        for code, gname in list(table.cmap.items()):
            if gname in pairs:
                table.cmap[code] = pairs[gname]

    gsub = font["GSUB"].table

    # 2. curved twins for straight-keyed SingleSubst rules (locl chains etc.)
    def _subtables(lookup):
        for st in lookup.SubTable:
            yield st.ExtSubTable if hasattr(st, "ExtSubTable") else st
    for lookup in gsub.LookupList.Lookup:
        for st in _subtables(lookup):
            m = getattr(st, "mapping", None)
            if not m:
                continue
            for straight, curved in pairs.items():
                out = m.get(straight)
                # str = SingleSubst; MultipleSubst/AlternateSubst map to lists — their
                # straight outputs are caught downstream by the rclt backstop instead
                if isinstance(out, str) and curved not in m and out != curved:
                    m[curved] = out + config.GF_TEXTUI_ALT_SUFFIX \
                        if out + config.GF_TEXTUI_ALT_SUFFIX in glyphs else out

    # 2b. drop ligature rules built on a straight swap glyph (fl, f_f_l, fl.rcltBase):
    # their components are GIDs typed text no longer produces, and the U+FB02 path
    # would otherwise decompose early (ccmp) then RE-ligate to the straight-l ligature
    # before the backstop can curve the l. Removing the rules makes compat codepoints
    # decompose and stay decomposed — identical to typed f + l. (fi keeps ligating:
    # i is not swapped, and the fi ligature carries no l.)
    straights = set(pairs)
    pruned = 0
    for lookup in gsub.LookupList.Lookup:
        for st in _subtables(lookup):
            ligs = getattr(st, "ligatures", None)
            if not ligs:
                continue
            for first, rules in list(ligs.items()):
                if first in straights:
                    pruned += len(rules)
                    del ligs[first]
                    continue
                kept = [r for r in rules if not (set(r.Component) & straights)]
                if len(kept) != len(rules):
                    pruned += len(rules) - len(kept)
                    ligs[first] = kept
    if pruned:
        print(f"   ✂️  curved-l swap: removed {pruned} ligature rule(s) built on the straight l")

    # 3. rclt backstop
    lookup = ot.Lookup()
    lookup.LookupType = 1
    lookup.LookupFlag = 0
    lookup.SubTable = [buildSingleSubstSubtable(pairs)]
    lookup.SubTableCount = 1
    gsub.LookupList.Lookup.append(lookup)
    gsub.LookupList.LookupCount = len(gsub.LookupList.Lookup)
    idx = gsub.LookupList.LookupCount - 1

    rclt_records = [fr for fr in gsub.FeatureList.FeatureRecord
                    if fr.FeatureTag == config.RCLT_FEATURE_TAG]
    if not rclt_records:
        print("   ⚠️  curved-l swap: no rclt feature in GSUB — backstop not applied")
    for fr in rclt_records:
        fr.Feature.LookupListIndex.append(idx)
        fr.Feature.LookupCount = len(fr.Feature.LookupListIndex)


def _save_with_curved_l_names(font: TTFont, dest_ttf: Path, woff2: bool = True):
    """Serialize, then rename glyphs on the reloaded binary: curved *.rcltA11y take
    over the canonical names (l, lacute, …) and any surviving straight originals
    become *.rcltDflt (hoi.py's I.rcltDflt convention). Glyph names live only in the
    post table, and GIDs don't move, so relabeling the lazy-loaded binary is safe —
    renaming the DECOMPILED font would be corruption: every fontTools table is keyed
    by name there, so a rename silently rebinds outlines, kerning, and rules."""
    buf = BytesIO()
    buf.name = "<in-memory>"  # TTFont.save on a lazy font probes reader.file.name
    font.save(buf)
    buf.seek(0)
    f2 = TTFont(buf, lazy=True)
    order = f2.getGlyphOrder()
    present = set(order)
    ren = {}
    for base in config.GF_TEXTUI_CURVED_L_GLYPHS:
        curved = base + config.GF_TEXTUI_ALT_SUFFIX
        if curved in present:
            ren[curved] = base
            if base in present:
                ren[base] = base + ".rcltDflt"
    new_order = [ren.get(g, g) for g in order]
    assert len(set(new_order)) == len(new_order), "curved-l rename produced duplicate names"
    f2.setGlyphOrder(new_order)
    if getattr(f2["post"], "glyphOrder", None) is not None:
        f2["post"].glyphOrder = new_order
    f2.save(str(dest_ttf))
    if woff2:
        f2.flavor = "woff2"
        f2.save(str(dest_ttf.with_suffix(".woff2")))


def _instance_textui(src_ttf: Path, axes: dict) -> TTFont:
    """Load the full VF, make the curved l the default (before pinning — see
    _make_curved_l_default), pin `axes` (the instancer resolves the GEOM/opsz
    FeatureVariations exactly as it does for the static matrix), then subset ss/cv out.
    Subsetting last also sweeps up the variation alternates (.rcltGeo, the a/g/I A11y
    forms, …) that pinning orphans — and usually the straight l-family too — while the
    closure keeps the curved-l glyphs the retargeted cmap now reaches."""
    from fontTools.varLib.instancer import instantiateVariableFont
    font = TTFont(str(src_ttf))
    _make_curved_l_default(font)
    instantiateVariableFont(font, axes, inplace=True, updateFontNames=False)
    if "gvar" in font:
        # partial pinning drops gvar entries for glyphs left with no deltas, but the
        # subsetter indexes gvar by every retained glyph (KeyError otherwise)
        gv = font["gvar"].variations
        font["gvar"].variations = {g: (gv[g] if g in gv else [])
                                   for g in font.getGlyphOrder()}
    _subset_ss_cv(font)
    return font


def _build_gf_textui(src_ttf: Path, dest_dir: Path):
    """gf-api-textui (google/fonts#9970): 'Cal Sans Text UI' — the second GF deliverable.
    Roman + Italic variable fonts with wght (400–700) as the only live axis; opsz/GEOM/
    YTAS/SHRP baked per config.GF_TEXTUI_PINNED and ital instanced out per file like
    gf-api. STAT is rebuilt to wght + the ital style-link record only — the inherited
    6-axis STAT would compose 'Text UI' into style names on top of the family name."""
    from fontTools.otlLib.builder import buildStatTable
    dest_dir.mkdir(parents=True, exist_ok=True)

    has_ital = any(a.axisTag == "ital" for a in TTFont(str(src_ttf))["fvar"].axes)
    family_ps = config.GF_TEXTUI_FAMILY.replace(" ", "")
    stat_axes = [a for a in config.STAT_AXES if a["tag"] in ("wght", "ital")]

    targets = [(0, "", "Regular")] + ([(1, "-Italic", "Italic")] if has_ital else [])
    for ital_value, suffix, subfamily in targets:
        axes = dict(config.GF_TEXTUI_PINNED)
        if has_ital:
            axes["ital"] = ital_value
        font = _instance_textui(src_ttf, axes)
        _set_style_names(font, subfamily, family=config.GF_TEXTUI_FAMILY)
        buildStatTable(font, stat_axes, elidedFallbackName=config.STAT_ELIDED_FALLBACK)
        if config.GF_TRIM_INSTANCES:
            _trim_gf_instances(font, ps_suffix=suffix)
        _set_gf_version(font)            # name/version_format ("Version X.YYY"[; sha])
        _apply_gf_conformance(font)      # names, v-metrics, STAT, meta
        _save_with_curved_l_names(font, dest_dir / f"{family_ps}{suffix}[wght].ttf")


def _build_gf_workspace_textui(var_ttf: Path, dest_dir: Path, build_italic: bool):
    """Workspace statics for the Text UI half: instanced fresh from the VF at the
    gf-api-textui position (YTAS=760, curved l default — google/fonts#9970) instead of
    copied from the static matrix, which pins YTAS=720 with the straight l. Same
    filenames as the matrix statics they replace; ss/cv subset out; TTF-only."""
    from scripts.lib.instance_statics import _apply_static_names
    dest_dir.mkdir(parents=True, exist_ok=True)

    itals = ((0, True), (1, False)) if build_italic else ((0, True),)
    for wght, wght_label in config.GF_WEIGHT_INSTANCES:
        for ital_value, roman in itals:
            style = f"{config.GF_TEXTUI_FAMILY} {wght_label}"
            if not roman:
                # RIBBI elision: "Regular Italic" → "Italic"
                style = style.removesuffix(" Regular") + " Italic"
            font = _instance_textui(var_ttf, dict(config.GF_TEXTUI_PINNED,
                                                  wght=wght, ital=ital_value))
            _apply_static_names(font, style)
            _apply_gf_conformance(font)
            _save_with_curved_l_names(font, dest_dir / style_name_to_filename(style),
                                      woff2=False)


def _build_cossui(src_ttf: Path, dest_dir: Path):
    """cossui ships roman + italic as TWO variable fonts — the same split as gf-api, and
    for the same reason: browsers do not activate an `ital` axis from `font-style: italic`,
    they synthesize a fake oblique instead (web-platform-tests/interop#64). Instancing ital
    out of fvar leaves the STAT style-link record (Roman elidable, linkedValue → Italic), so
    a host that only knows "italic" style-links to the drawn italic. ss/cv are subset out and
    the opsz axis max is relabeled to COSSUI_OPSZ_MAX. Roman keeps the original filename."""
    from fontTools.varLib.instancer import instantiateVariableFont
    dest_dir.mkdir(parents=True, exist_ok=True)

    has_ital = any(a.axisTag == "ital" for a in TTFont(str(src_ttf))["fvar"].axes)
    targets = [(0, "", "Regular")] + ([(1, "-Italic", "Italic")] if has_ital else [])
    for ital_value, suffix, subfamily in targets:
        font = TTFont(str(src_ttf))
        _subset_ss_cv(font)
        _relabel_opsz_max(font, config.COSSUI_OPSZ_MAX)
        if has_ital:
            instantiateVariableFont(font, {"ital": ital_value}, inplace=True, updateFontNames=False)
        _set_style_names(font, subfamily)   # also injects post.italicAngle on the italic
        dest_ttf = dest_dir / f"{src_ttf.stem}{suffix}.ttf"
        font.save(str(dest_ttf))
        font.flavor = "woff2"
        font.save(str(dest_ttf.with_suffix(".woff2")))


def _audit_italic_instances(pkg_dir: Path) -> list:
    """Every italic variable font in a package whose named instances forget the slope.

    A package-level net for the same bug, catching any path that builds instances without
    going through _trim_gf_instances (cossui keeps the source's own, for instance)."""
    bad = []
    for path in sorted(pkg_dir.rglob("*.ttf")):
        font = TTFont(str(path), lazy=True)
        if "fvar" in font and font["OS/2"].fsSelection & 0x0001:
            name = font["name"]
            names = [name.getDebugName(i.subfamilyNameID) for i in font["fvar"].instances]
            if any("Italic" not in (s or "") for s in names):
                bad.append((path.name, names))
        font.close()
    return bad


def _report(pkg_dir: Path, label: str):
    count = sum(1 for p in pkg_dir.rglob("*") if p.is_file()) if pkg_dir.exists() else 0
    print(f"   ✅ {label} ({count} files)")
    if _UNDERLINE_NOTICE["count"]:
        was = ", ".join(str(v) for v in sorted(_UNDERLINE_NOTICE["was"]))
        print(f"   \u270f\ufe0f  underline pinned to Medium "
              f"({config.GF_UNDERLINE_THICKNESS}/{config.GF_UNDERLINE_POSITION}) on "
              f"{_UNDERLINE_NOTICE['count']} file(s) — was {was} — GF requires one "
              f"thickness family-wide")
        _UNDERLINE_NOTICE["count"] = 0
        _UNDERLINE_NOTICE["was"] = set()
    for fname, names in _audit_italic_instances(pkg_dir):
        print(f"   ❌ {fname}: italic instances missing the slope → {names}")


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

    # cossui: roman + italic as TWO variable fonts (ital instanced out), ss/cv stripped.
    # opsz capped at 32 (source tops out at 45); default optical size unchanged.
    pkg = out_path / f"{_PFX}-cossui"
    for ttf in sorted(var_dir.glob("*.ttf")):
        _build_cossui(ttf, pkg)
    _report(pkg, f"{_PFX}-cossui")

    # gf-api: GF spec — roman + italic shipped as TWO variable fonts, ital instanced
    # out of fvar and kept only as a STAT style-link record.
    pkg = out_path / f"{_PFX}-gf-api"
    if config.GF_TRIM_INSTANCES:
        print("   ⚠️  GF fvar spec: trimming named instances to Weight-only "
              "(Regular/Medium/SemiBold/Bold) at GEOM=25, opsz=14 "
              "(settled in google/fonts#9970 — the UI/Text position ships as "
              "gf-api-textui instead).")
    for ttf in sorted(var_dir.glob("*.ttf")):
        _build_gf_api(ttf, pkg)
    _unify_family_win_metrics(pkg)
    _report(pkg, f"{_PFX}-gf-api")

    # gf-api-textui: the second GF delivery folder (google/fonts#9970) — "Cal Sans
    # Text UI", wght-only (400–700) roman + italic VFs; opsz=10, GEOM=25, YTAS=760
    # baked, curved l (l.rcltA11y) as the shipped default.
    pkg = out_path / f"{_PFX}-gf-api-textui"
    for ttf in sorted(var_dir.glob("*.ttf")):
        _build_gf_textui(ttf, pkg)
    _unify_family_win_metrics(pkg)
    _report(pkg, f"{_PFX}-gf-api-textui")

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
    # their alternate glyphs) stripped like cossui/gf-api; TTF-only. The Display/Base
    # half copies from the static matrix; the Text UI half is instanced fresh at the
    # gf-api-textui position (YTAS=760, curved l — google/fonts#9970), which the
    # matrix statics (YTAS=720, straight l) no longer represent.
    pkg = out_path / f"{_PFX}-gf-workspace"
    pkg.mkdir(parents=True, exist_ok=True)
    for s in [s for s in text_family_styles if s["geom"] == "base"]:
        src = static_dir / s["filename"]
        if src.exists():
            _strip_ss_cv(src, pkg, woff2=False, gf_metrics=True)
        else:
            missing += 1
    workspace_var = next((t for t in sorted(var_dir.glob("*.ttf"))), None)
    if workspace_var:
        _build_gf_workspace_textui(workspace_var, pkg, build_italic)
    _unify_family_win_metrics(pkg)
    _report(pkg, f"{_PFX}-gf-workspace")

    if not build_italic:
        print("⚠️  Built without italics (BUILD_ITALIC=False) — Cal Sans Display/Base "
              "italic styles are missing from calsans-static-essentials and calsans-gf-workspace")

    if missing:
        print(f"\n⚠️  {missing} expected static files not found in {static_dir}/")
        print(f"   Run fontmake first, or check style_name_to_filename() in scripts/manifest.py")

    print(f"\n✅ Release folders written to {output_dir}/")
