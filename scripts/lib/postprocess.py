"""Post-compile fix-ups applied to the fontmake-compiled variable TTF, shared by the main variable
build and the Flex build: merge the overlapping GEOM FeatureVariations into non-overlapping bands,
pin the shipping axis defaults, and rebuild the STAT table + fvar instance names."""
from fontTools.ttLib import TTFont, newTable
from fontTools.ttLib.tables import otTables

from scripts import config
from scripts.lib.utils import axis_index


def append_distribution_sha(font: TTFont):
    """Swap the live calcom/sans build hash into the version string (nameID 5), keeping the
    font's own version number and dropping any existing '; <hash>' suffix (the source carries
    a stale one). In-memory; no-op when the hash can't be resolved (build stays unbroken)."""
    from scripts.lib.release import _distribution_sha   # lazy: release imports build_flex
    sha = _distribution_sha()
    if not sha:
        return
    name = font["name"]
    cur = name.getDebugName(5) or f"Version {font['head'].fontRevision:.3f}"
    v = f"{cur.split(';')[0].rstrip()}; {sha}"
    if v == cur:
        return
    name.setName(v, 5, 3, 1, 0x0409)  # Windows, English (US)
    name.setName(v, 5, 1, 0, 0)        # Mac, Roman


def stamp_distribution_sha(ttf_path: str):
    """Path wrapper for append_distribution_sha — used for the compiled variable TTF, whose
    stamped nameID 5 is then inherited by every static/subset instanced from it."""
    font = TTFont(ttf_path)
    before = font["name"].getDebugName(5)
    append_distribution_sha(font)
    if font["name"].getDebugName(5) != before:
        font.save(ttf_path)


def merge_gsub_feature_variations(ttf_path: str):
    """feaLib emits one FeatureVariation record per variation block, evaluated
    first-match-wins. Overlapping GEOM ranges mean only the first matching record
    fires. This rebuilds the table into NON-OVERLAPPING GEOM bands where each record
    carries ALL substitutions that should apply in that band (what the Glyphs app does
    internally). Without this, glyphs drop back to default when crossing a band edge."""
    font = TTFont(ttf_path)
    gsub = font["GSUB"].table
    fvar = font["fvar"]
    if not getattr(gsub, "FeatureVariations", None):
        return
    geom_idx = axis_index(fvar.axes, config.GEOM_AXIS_TAG)
    rclt_idx = next((i for i, fr in enumerate(gsub.FeatureList.FeatureRecord)
                     if fr.FeatureTag == config.RCLT_FEATURE_TAG), None)
    if rclt_idx is None:
        return

    # Parse existing records into (geom_min, geom_max, other_conditions, lookups)
    parsed = []
    for record in gsub.FeatureVariations.FeatureVariationRecord:
        gmin = gmax = None
        other = []
        for condition in record.ConditionSet.ConditionTable:
            if condition.AxisIndex == geom_idx:
                gmin, gmax = condition.FilterRangeMinValue, condition.FilterRangeMaxValue
            else:
                other.append(condition)
        lookups = []
        for substitution in record.FeatureTableSubstitution.SubstitutionRecord:
            if substitution.FeatureIndex == rclt_idx:
                lookups = sorted(substitution.Feature.LookupListIndex)
        if gmin is not None:
            parsed.append((gmin, gmax, other, lookups))

    pts = sorted({v for gmin, gmax, _, _ in parsed for v in (gmin, gmax)})

    def make_cond(lo, hi):
        condition = otTables.ConditionTable()
        condition.Format = 1
        condition.AxisIndex = geom_idx
        condition.FilterRangeMinValue = lo
        condition.FilterRangeMaxValue = hi
        return condition

    def make_combined_lookup(lookup_indices):
        # Merge multiple SingleSubst lookups into one so HarfBuzz applies all mappings
        # (it only applies the first lookup referenced by a FeatureVariations feature).
        combined = {}
        for lookup_idx in lookup_indices:
            existing = gsub.LookupList.Lookup[lookup_idx]
            existing.ensureDecompiled(recurse=True)
            for subtable in existing.SubTable:
                if hasattr(subtable, "mapping"):
                    combined.update(subtable.mapping)
        merged = otTables.SingleSubst()
        merged.mapping = combined
        lookup = otTables.Lookup()
        lookup.LookupType = 1
        lookup.LookupFlag = 0
        lookup.SubTable = [merged]
        lookup.SubTableCount = 1
        lookup.MarkFilterSet = None
        gsub.LookupList.Lookup.append(lookup)
        return len(gsub.LookupList.Lookup) - 1

    def make_record(conditions, lookup_indices):
        feature = otTables.Feature()
        feature.LookupListIndex = [make_combined_lookup(lookup_indices)]
        feature.LookupCount = 1
        feature.FeatureParams = None
        subst_record = otTables.FeatureTableSubstitutionRecord()
        subst_record.FeatureIndex = rclt_idx
        subst_record.Feature = feature
        feature_sub = otTables.FeatureTableSubstitution()
        feature_sub.Version = 0x00010000
        feature_sub.SubstitutionRecord = [subst_record]
        feature_sub.SubstitutionCount = 1
        condition_set = otTables.ConditionSet()
        condition_set.ConditionTable = conditions
        condition_set.ConditionCount = len(conditions)
        record = otTables.FeatureVariationRecord()
        record.ConditionSet = condition_set
        record.FeatureTableSubstitution = feature_sub
        return record

    multi_records = []
    pure_records = []
    for i in range(len(pts) - 1):
        lo, hi = pts[i], pts[i + 1]
        mid = (lo + hi) / 2
        pure_lks = sorted({lk for gmin, gmax, other, lks in parsed
                           if not other and gmin <= mid <= gmax for lk in lks})
        if pure_lks:
            pure_records.append(make_record([make_cond(lo, hi)], pure_lks))
        for gmin, gmax, other, lks in parsed:
            if not other or not (gmin <= mid <= gmax):
                continue
            multi_records.append(make_record([make_cond(lo, hi)] + other,
                                             sorted(set(lks + pure_lks))))

    new_records = multi_records + pure_records
    gsub.FeatureVariations.FeatureVariationRecord = new_records
    gsub.FeatureVariations.FeatureVariationCount = len(new_records)
    font.save(ttf_path)
    print(f"   ✅ GSUB FeatureVariations merged: {len(parsed)} → {len(new_records)} non-overlapping records")


def shift_axis_defaults(ttf_path: str):
    """Pin the shipping defaults at opsz=14, GEOM=25 while keeping full axis ranges.
    instancer re-normalizes gvar/avar/GSUB FeatureVariations to the new default, so the
    conditional GEOM substitutions keep firing correctly."""
    from fontTools.varLib.instancer import instantiateVariableFont
    font = TTFont(ttf_path)
    fvar = font["fvar"]
    coords = {}
    for tag, default in config.SHIPPING_DEFAULTS.items():
        axis = next(a for a in fvar.axes if a.axisTag == tag)
        coords[tag] = (axis.minValue, default, axis.maxValue)
    instantiateVariableFont(font, coords, inplace=True, optimize=True)
    font.save(ttf_path)
    shifted = ", ".join(f"{tag}→{default}" for tag, default in config.SHIPPING_DEFAULTS.items())
    print(f"   ✅ Axis defaults shifted: {shifted}")


def _instance_subfamily_name(coords) -> str:
    """Compose a unique fvar instance subfamily name from the static token tables
    (config.INSTANCE_NAME_ORDER), e.g. opsz=10,GEOM=25,wght=400 → 'Text UI Regular'.
    Empty-label tokens (Display opsz, base GEOM/YTAS/SHRP, Roman) drop out, so the
    opsz=32 sibling becomes 'UI Regular' — distinct from the opsz=10 'Text' one."""
    parts = []
    for tag, vkey, tokens in config.INSTANCE_NAME_ORDER:
        coord = coords.get(tag)
        if coord is None:
            continue
        values = config.STATIC_AXIS_VALUES[vkey]
        tok_id = next((tid for tid, v in values.items() if v == coord), None)
        if tok_id is None:
            continue
        label = dict(tokens)[tok_id]
        if label:
            parts.append(label)
    # RIBBI: the default "Regular" weight is implied once a style is present, so
    # an Italic instance is "… Italic", never "… Regular Italic".
    if "Italic" in parts and "Regular" in parts:
        parts.remove("Regular")
    return " ".join(parts) if parts else "Regular"


def apply_stat_and_instance_names(font: TTFont) -> tuple[int, str]:
    """glyphsLib leaves the variable font with an empty STAT AxisValueArray and
    opsz absent from the named-instance names, so the opsz=10/32 instances collide
    and Adobe can't pin optical size. Rebuild the STAT table from config.STAT_AXES
    and give every fvar instance a unique, opsz-aware subfamily name. Operates on an
    open font so every variable build (main pipeline + Flex) can share it.
    Returns (instances_renamed, default_full_name)."""
    from fontTools.otlLib.builder import buildStatTable

    name, fvar = font["name"], font["fvar"]

    name_cache = {}
    def name_id(string):
        if string in name_cache:
            return name_cache[string]
        for rec in name.names:
            if rec.nameID >= 256 and rec.toUnicode() == string:
                name_cache[string] = rec.nameID
                return rec.nameID
        nid = name.addName(string)
        name_cache[string] = nid
        return nid

    renamed = 0
    for inst in fvar.instances:
        new = _instance_subfamily_name(inst.coordinates)
        if name.getDebugName(inst.subfamilyNameID) != new:
            inst.subfamilyNameID = name_id(new)
            renamed += 1

    # glyphsLib bakes the pre-shift default opsz into the legacy family records
    # (name 1 "Cal Sans 10", 4 "Cal Sans 10 Regular", 6 "CalSans-10Regular",
    # 17 "10 Regular"). Re-pinning the default to opsz=14 leaves that stale, so
    # rebuild the legacy/full/PS/typo-subfamily records from the typographic
    # family (16) + default style (2) → "Cal Sans" / "Cal Sans Regular".
    typo_family = name.getDebugName(16) or name.getDebugName(1)
    default_style = name.getDebugName(2) or "Regular"
    full = f"{typo_family} {default_style}"
    ps = f"{typo_family}-{default_style}".replace(" ", "")
    for nid, value in [(1, typo_family), (4, full), (6, ps), (17, default_style)]:
        for rec in [r for r in name.names if r.nameID == nid]:
            name.setName(value, nid, rec.platformID, rec.platEncID, rec.langID)

    # Describe every fvar axis in the DesignAxisRecord, but emit no AxisValues for
    # HIDDEN axes (e.g. YTAS in the Flex build, slaved to opsz via avar2) so they
    # don't surface as selectable styles.
    fvar_tags = {a.axisTag for a in fvar.axes}
    hidden = {a.axisTag for a in fvar.axes if a.flags & 0x0001}
    axes, ordering = [], 0
    for ax in config.STAT_AXES:
        if ax["tag"] not in fvar_tags:
            continue
        values = [] if ax["tag"] in hidden else [dict(v) for v in ax["values"]]
        axes.append({"tag": ax["tag"], "name": ax["name"], "ordering": ordering, "values": values})
        ordering += 1
    buildStatTable(font, axes, elidedFallbackName=config.STAT_ELIDED_FALLBACK)

    return renamed, full


def ensure_gasp(ttf_path: str):
    """Write the gasp table (config.GASP_RANGES). Runs on the compiled variable fonts, so
    every static instanced from them — and every package cut from those — inherits it."""
    font = TTFont(ttf_path)
    gasp = newTable("gasp")
    gasp.version = config.GASP_VERSION
    gasp.gaspRange = dict(config.GASP_RANGES)
    font["gasp"] = gasp
    font.save(ttf_path)


def build_stat_and_instance_names(ttf_path: str):
    """Path wrapper for the main-pipeline post-fontmake pass."""
    font = TTFont(ttf_path)
    renamed, full = apply_stat_and_instance_names(font)
    font.save(ttf_path)
    print(f"   ✅ STAT rebuilt, {renamed} fvar instance names disambiguated, "
          f"default family → \"{full}\"")
