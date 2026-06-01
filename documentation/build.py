import sys
import os
import subprocess
import glyphsLib
from fontTools.ttLib import TTFont
from fontTools.ttLib.tables import otTables

from scripts.step0_read import export_metrics
from scripts.step1_scaler import generate_micro_masters
from scripts.step5_release import compress_build_outputs, build_release_folders

# ── Configuration ─────────────────────────────────────────────────────────────
SOURCE_PATH         = "sources/CalSans.glyphs"
OUTPUT_PATH         = "sources/CalSans_READY.glyphs"
OUTPUT_PATH_STATIC  = "sources/CalSans_READY_static.glyphs"
BUILD_DIR    = "build"
RELEASE_DIR  = "sans"
BUILD_ITALIC = False  # set True when italic source is ready

# ── Old slant flags (kept for reference) ──────────────────────────────────────
# SLANT_ONLY = "slant=only" in sys.argv
# DO_SLANT = "slant=true" in sys.argv or SLANT_ONLY
# TEMP1_PATH = "sources/CalSansUI_tmp1.glyphs"
# TEMP2_PATH = "sources/CalSansUI_tmp2.glyphs"

def patch_smart_components(font):
    """Fill missing pole mappings on smart-component base layers (pulled from convert_for_kerning.py).
    Prevents glyphsLib from producing mixed contour/component structures at build time."""
    MIN_POLE = 1
    patches = 0
    for glyph in font.glyphs:
        if not glyph.smartComponentAxes:
            continue
        declared = [ax.name for ax in glyph.smartComponentAxes]
        layers_by_master = {}
        for layer in glyph.layers:
            layers_by_master.setdefault(layer.associatedMasterId, []).append(layer)
        for layers in layers_by_master.values():
            base = layers[0]
            mapping = base.smartComponentPoleMapping
            for axis_name in declared:
                if axis_name not in mapping:
                    mapping[axis_name] = MIN_POLE
                    patches += 1
    if patches:
        print(f"   ✅ Patched {patches} smart component pole(s)")


def remove_non_exported_glyphs(font):
    """Remove non-exported glyphs that nothing references. Keep any used as components or smart component parts."""
    referenced = set()
    for glyph in font.glyphs:
        for layer in glyph.layers:
            for component in layer.components:
                referenced.add(component.name)

    names = [g.name for g in font.glyphs if not g.export and g.name not in referenced]
    for name in names:
        del font.glyphs[name]

    kept = [g.name for g in font.glyphs if not g.export and g.name in referenced]
    if names:
        print(f"   ✅ Removed {len(names)} non-exported glyphs from build")
    if kept:
        print(f"   ℹ️  Kept {len(kept)} non-exported component source(s)")


def prepare_for_fontmake(font):
    """Switch dialects: disable rclt (Glyphs condition syntax), enable VARIATIONS prefix (fontmake conditionset syntax)."""
    # Leave rclt active — glyphsLib converts Glyphs condition syntax to FeatureVariations.
    # The Glyphs-built rclt works in Chrome; our VARIATIONS prefix approach does not.
    for feat in font.features:
        if getattr(feat, "name", "").lower() == "rclt" and not feat.disabled:
            print("   ✅ rclt feature left active (glyphsLib will convert condition syntax)")

    # Filter the auto-generated All class to exported glyphs only.
    # SkipExportGlyphsIFilter removes non-exported glyphs from the glyph set
    # but the compiled @All class still references them, causing feature errors.
    exported = {g.name for g in font.glyphs if g.export}
    for cls in getattr(font, "classes", []):
        if cls.name == "All":
            before = len(cls.code.split())
            cls.code = " ".join(n for n in cls.code.split() if n in exported)
            after = len(cls.code.split())
            if before != after:
                print(f"   ✅ @All class filtered ({before - after} non-exported glyphs removed)")

    # Remove "Replace Glyph" instance parameters — rclt feature handles substitution,
    # and Replace Glyph causes cyclical component references when alternates use base as component.
    removed = 0
    for instance in getattr(font, "instances", []):
        params = [p for p in instance.customParameters if p.name != "Rename Glyphs"]
        if len(params) != len(instance.customParameters):
            removed += len(instance.customParameters) - len(params)
            instance.customParameters = params
    if removed:
        print(f"   ✅ Removed Rename Glyphs from {removed} instance(s) (rclt feature handles substitution)")

    for prefix in getattr(font, "featurePrefixes", []):
        if getattr(prefix, "name", "") == "VARIATIONS":
            prefix.disabled = False
            # Temporarily strip tracking kern variation blocks to isolate GPOS overflow source
            import re
            prefix.code = re.sub(r'variation kern cond_micro_\w+\s*\{[^}]*\}\s*kern\s*;', '', prefix.code, flags=re.DOTALL)
            prefix.code = re.sub(r'conditionset cond_micro_\w+\s*\{[^}]*\}\s*cond_micro_\w+\s*;', '', prefix.code, flags=re.DOTALL)
            print("   ✅ VARIATIONS prefix enabled (fontmake dialect) [tracking stripped for overflow test]")


def merge_gsub_feature_variations(ttf_path: str):
    """
    feaLib emits one FeatureVariation record per variation block, evaluated
    first-match-wins. Overlapping GEOM ranges mean only the first matching
    record fires. This rebuilds the table with non-overlapping regions where
    each record carries ALL lookups that should apply in that region.
    """
    font = TTFont(ttf_path)
    gsub = font["GSUB"].table
    fvar = font["fvar"]

    if not hasattr(gsub, "FeatureVariations") or not gsub.FeatureVariations:
        return

    geom_idx = next(i for i, a in enumerate(fvar.axes) if a.axisTag == "GEOM")
    rclt_idx = next(
        (i for i, fr in enumerate(gsub.FeatureList.FeatureRecord) if fr.FeatureTag == "rclt"),
        None,
    )
    if rclt_idx is None:
        return

    # Parse existing records into (geom_min, geom_max, other_conditions, lookups)
    parsed = []
    for r in gsub.FeatureVariations.FeatureVariationRecord:
        gmin = gmax = None
        other = []
        for c in r.ConditionSet.ConditionTable:
            if c.AxisIndex == geom_idx:
                gmin, gmax = c.FilterRangeMinValue, c.FilterRangeMaxValue
            else:
                other.append(c)
        lookups = []
        for s in r.FeatureTableSubstitution.SubstitutionRecord:
            if s.FeatureIndex == rclt_idx:
                lookups = sorted(s.Feature.LookupListIndex)
        if gmin is not None:
            parsed.append((gmin, gmax, other, lookups))

    # Compute non-overlapping GEOM breakpoints
    pts = sorted({v for gmin, gmax, _, _ in parsed for v in (gmin, gmax)})

    def make_cond(axis, lo, hi):
        c = otTables.ConditionTable()
        c.Format = 1
        c.AxisIndex = axis
        c.FilterRangeMinValue = lo
        c.FilterRangeMaxValue = hi
        return c

    def make_combined_lookup(lk_list):
        """Merge multiple SingleSubst lookups into one so HarfBuzz applies all mappings.
        HarfBuzz only applies the first lookup referenced by a FeatureVariations feature."""
        combined_mapping = {}
        for lk_idx in lk_list:
            lk = gsub.LookupList.Lookup[lk_idx]
            lk.ensureDecompiled(recurse=True)
            for st in lk.SubTable:
                if hasattr(st, "mapping"):
                    combined_mapping.update(st.mapping)

        new_st = otTables.SingleSubst()
        new_st.mapping = combined_mapping

        new_lk = otTables.Lookup()
        new_lk.LookupType = 1  # SingleSubst
        new_lk.LookupFlag = 0
        new_lk.SubTable = [new_st]
        new_lk.SubTableCount = 1
        new_lk.MarkFilterSet = None
        gsub.LookupList.Lookup.append(new_lk)
        return len(gsub.LookupList.Lookup) - 1

    def make_record(conds, lk_list):
        combined_idx = make_combined_lookup(lk_list)
        feat = otTables.Feature()
        feat.LookupListIndex = [combined_idx]
        feat.LookupCount = 1
        feat.FeatureParams = None
        sub = otTables.FeatureTableSubstitutionRecord()
        sub.FeatureIndex = rclt_idx
        sub.Feature = feat
        fts = otTables.FeatureTableSubstitution()
        fts.Version = 0x00010000
        fts.SubstitutionRecord = [sub]
        fts.SubstitutionCount = 1
        cs = otTables.ConditionSet()
        cs.ConditionTable = conds
        cs.ConditionCount = len(conds)
        rec = otTables.FeatureVariationRecord()
        rec.ConditionSet = cs
        rec.FeatureTableSubstitution = fts
        return rec

    multi_records = []
    pure_records = []

    for i in range(len(pts) - 1):
        lo, hi = pts[i], pts[i + 1]
        mid = (lo + hi) / 2

        # Pure GEOM lookups for this region
        pure_lks = sorted({
            lk for gmin, gmax, other, lks in parsed
            if not other and gmin <= mid <= gmax
            for lk in lks
        })
        if pure_lks:
            pure_records.append(make_record([make_cond(geom_idx, lo, hi)], pure_lks))

        # Multi-condition (e.g. GEOM+opsz) records — merged with pure lookups
        for gmin, gmax, other, lks in parsed:
            if not other or not (gmin <= mid <= gmax):
                continue
            combined = sorted(set(lks + pure_lks))
            multi_records.append(
                make_record([make_cond(geom_idx, lo, hi)] + other, combined)
            )

    new_records = multi_records + pure_records
    gsub.FeatureVariations.FeatureVariationRecord = new_records
    gsub.FeatureVariations.FeatureVariationCount = len(new_records)
    font.save(ttf_path)
    print(f"   ✅ GSUB FeatureVariations merged: {len(parsed)} → {len(new_records)} non-overlapping records")


def run_fontmake(ready_path: str, static_ready_path: str, build_dir: str):
    os.makedirs(f"{build_dir}/variable", exist_ok=True)
    os.makedirs(f"{build_dir}/static", exist_ok=True)

    print("🔨 Building variable font...")
    result = subprocess.run(
        ["fontmake", "-g", ready_path, "-o", "variable",
         "--output-dir", f"{build_dir}/variable",
         "--master-dir", f"{build_dir}/master_ufo",
         "--filter", "FlattenComponentsFilter"],
        capture_output=True, text=True,
    )
    if result.returncode != 0:
        print(result.stdout)
        print(result.stderr)
        raise subprocess.CalledProcessError(result.returncode, result.args)
    print("   ✅ Variable font built")

    for ttf in __import__("pathlib").Path(f"{build_dir}/variable").glob("*.ttf"):
        merge_gsub_feature_variations(str(ttf))

    print("🔨 Building static instances...")
    subprocess.run(
        ["fontmake", "-g", static_ready_path, "-o", "ttf", "-i", "--output-dir", f"{build_dir}/static"],
        check=True,
    )


def validate_font_setup(font):
    print("🔎 Running pre-flight validation...")
    expected_axes = ["opsz", "GEOM", "wght", "YTAS", "SHRP"]
    actual_axes = [a.axisTag for a in font.axes]
    if actual_axes != expected_axes:
        print(f"❌ Axis order wrong. Found: {actual_axes}")
        sys.exit(1)

    opsz_values = sorted(set(round(m.axes[0]) for m in font.masters))
    if opsz_values != [10, 32]:
        print(f"❌ Expected 10pt and 32pt masters. Found opsz values: {opsz_values}")
        sys.exit(1)

    if len(font.masters) != 4:
        print(f"❌ Expected 4 masters, found {len(font.masters)}.")
        sys.exit(1)

    print(f"   ✅ 4 masters: {[m.name for m in font.masters]}")

def main():
    print("🚀 Starting build")
    print(f"   Source: {SOURCE_PATH}")

    if not os.path.exists(SOURCE_PATH):
        print(f"❌ File not found: {SOURCE_PATH}")
        sys.exit(1)

    export_metrics(SOURCE_PATH)

    font = glyphsLib.load(SOURCE_PATH)
    font.filepath = SOURCE_PATH

    validate_font_setup(font)

    # ── Step 1: Generate 8pt masters, tighten 10pt sidebearings ──────────────
    # generate_micro_masters(font)

    # ── ITALIC ────────────────────────────────────────────────────────────────
    # Italic masters are hand-drawn and in progress — not building yet.
    # from scripts.step_italic import prepare_italic_masters
    # prepare_italic_masters(font)

    # ── Pre-process for fontmake ──────────────────────────────────────────────
    patch_smart_components(font)
    prepare_for_fontmake(font)

    # ── Save variable-ready (VARIATIONS prefix active) ────────────────────────
    print(f"💾 Saving to {OUTPUT_PATH}...")
    font.save(OUTPUT_PATH)

    # ── Save static-ready (VARIATIONS prefix disabled — statics have no fvar) ─
    for p in getattr(font, "featurePrefixes", []):
        if p.name == "VARIATIONS":
            p.disabled = True
    font.save(OUTPUT_PATH_STATIC)
    for p in getattr(font, "featurePrefixes", []):
        if p.name == "VARIATIONS":
            p.disabled = False

    # ── Compile ───────────────────────────────────────────────────────────────
    run_fontmake(OUTPUT_PATH, OUTPUT_PATH_STATIC, BUILD_DIR)
    compress_build_outputs(BUILD_DIR)

    # ── Package releases ──────────────────────────────────────────────────────
    build_release_folders(BUILD_DIR, RELEASE_DIR, build_italic=BUILD_ITALIC)

if __name__ == "__main__":
    main()
