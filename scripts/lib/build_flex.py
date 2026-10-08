#!/usr/bin/env python3
"""
Cal Sans Flex — avar2 experimental build.

Usage:
    python scripts/build_flex.py input.ttf [output_dir]

Outputs:
    CalSansFlex-Regular.ttf
    CalSansFlex-Regular.woff2

Pipeline order (critical — do not reorder):
    1. instancer  (shift defaults — must be first)
    2. avar2      (reads post-shift fvar ranges; opsz→YTAS, plus GEOM→helpers when the
                   font has the true-HOI helper axes — see scripts/lib/hoi_flex.py)
    3. hide YTAS + helpers  (logically follows avar2)
    4. rename     (last — no interaction with above)
"""

import os
import sys
import tempfile

from fontTools.ttLib import TTFont
from fontTools.varLib.instancer import instantiateVariableFont
from fontTools.designspaceLib import DesignSpaceDocument, AxisDescriptor, AxisMappingDescriptor
from fontTools.varLib.avar.build import build as build_avar

from scripts import config
from scripts.lib import hoi_flex as hoi_axes
from scripts.lib.postprocess import apply_stat_and_instance_names, append_distribution_sha
from scripts.lib.utils import axis_by_tag

_AXIS_NAMES = {
    "opsz": "Optical size",
    "wght": "Weight",
    "GEOM": "Geometric Form",
    "YTAS": "Ascender Height",
    "SHRP": "Sharpness",
}


def shift_defaults(font):
    fvar = font["fvar"]
    coords = {}
    for tag, default in config.SHIPPING_DEFAULTS.items():
        axis = axis_by_tag(fvar.axes, tag)
        coords[tag] = (axis.minValue, default, axis.maxValue)
    return instantiateVariableFont(font, coords, inplace=False, optimize=True)


def _build_avar2_ds(font, helper_ramps=None):
    ds = DesignSpaceDocument()
    info = {}
    for fvar_axis in font["fvar"].axes:
        axis = AxisDescriptor()
        axis.tag     = fvar_axis.axisTag
        axis.name    = _AXIS_NAMES.get(fvar_axis.axisTag, fvar_axis.axisTag)
        axis.minimum = fvar_axis.minValue
        axis.default = fvar_axis.defaultValue
        axis.maximum = fvar_axis.maxValue
        ds.addAxis(axis)
        info[fvar_axis.axisTag] = {"min": fvar_axis.minValue, "default": fvar_axis.defaultValue, "max": fvar_axis.maxValue}

    def make_loc(overrides):
        return {axis.name: overrides.get(axis.tag, axis.default) for axis in ds.axes}

    for opsz_val, ytas_out in config.FLEX_OPSZ_TO_YTAS:
        m = AxisMappingDescriptor()
        m.inputLocation  = make_loc({"opsz": opsz_val})
        m.outputLocation = make_loc({"opsz": opsz_val, "YTAS": ytas_out})
        ds.axisMappings.append(m)

    # GEOM → helpers: one mapping per GEOM breakpoint of any ramp. GEOM maps to itself, and YTAS
    # (like every other axis) stays at default here, as the helpers do in the opsz mappings —
    # single-axis inputs add, so (opsz 8, GEOM 77) gets YTAS(opsz) + helpers(GEOM), no double count.
    if helper_ramps:
        assert set(helper_ramps) <= set(info), f"ramps for axes not in fvar: {set(helper_ramps) - set(info)}"
        geom = info["GEOM"]
        for g in sorted({geom["min"], geom["max"]} | {g for ramp in helper_ramps.values() for g, _ in ramp}):
            out = {tag: hoi_axes.ramp_value(ramp, g) for tag, ramp in helper_ramps.items()}
            if g == geom["default"]:
                # the default location is avar2's base: a helper away from 0 here would move the default outline
                assert not any(out.values()), f"helpers must rest at the GEOM default {g}: {out}"
                continue
            m = AxisMappingDescriptor()
            m.inputLocation  = make_loc({"GEOM": g})
            m.outputLocation = make_loc({"GEOM": g, **out})
            ds.axisMappings.append(m)

    return ds


def inject_avar2(font, helper_ramps=None):
    ds = _build_avar2_ds(font, helper_ramps)
    # build_avar rebuilds avar from the designspace, which has no axis maps, so the compiled
    # font's avar1 segments (the wght curve) would come out as identity and Flex's wght 500/600
    # would drift from Cal Sans. Keep them. The axes avar2 maps must themselves be unmapped,
    # or the mapping locations above would be normalized differently from the font.
    segments = {tag: dict(seg) for tag, seg in font["avar"].segments.items()} if "avar" in font else {}
    mapped = {"opsz", "YTAS", "GEOM"} | set(helper_ramps or ())
    bent = sorted(tag for tag in mapped if any(k != v for k, v in segments.get(tag, {}).items()))
    assert not bent, f"avar2 maps axes that carry an avar1 curve: {bent}"
    with tempfile.NamedTemporaryFile(suffix=".designspace", delete=False) as f:
        ds_path = f.name
    try:
        ds.write(ds_path)
        build_avar(font, ds_path)
    finally:
        os.unlink(ds_path)
    for tag, seg in segments.items():
        font["avar"].segments[tag] = seg
    return font


def hide_axes(font, tags):
    for tag in tags:
        axis = axis_by_tag(font["fvar"].axes, tag)
        if axis:
            axis.flags |= 0x0001  # HIDDEN_AXIS — axis still functions via avar2
    return font


def add_stat_axis_records(font, tags):
    """apply_stat_and_instance_names builds STAT from config.STAT_AXES, which has no helper axes.
    Every fvar axis needs a STAT DesignAxisRecord (fontbakery FAILs otherwise); hidden helpers get
    the record and no AxisValues, appended last so existing AxisValue indices stay valid."""
    from fontTools.ttLib.tables import otTables
    stat = font["STAT"].table
    records = stat.DesignAxisRecord.Axis
    for tag in tags:
        if any(r.AxisTag == tag for r in records):
            continue
        rec = otTables.AxisRecord()
        rec.AxisTag = tag
        rec.AxisNameID = axis_by_tag(font["fvar"].axes, tag).axisNameID
        rec.AxisOrdering = len(records)
        records.append(rec)
    stat.DesignAxisCount = len(records)
    return font


def rename_font(font, family=config.FLEX_FAMILY_NAME, style=config.FLEX_STYLE_NAME):
    name = font["name"]
    fvar = font["fvar"]

    # Detach named instances from nameIDs 2/17 before we overwrite them
    max_id = max(r.nameID for r in name.names)
    for inst in fvar.instances:
        if inst.subfamilyNameID in (2, 17):
            max_id += 1
            orig = name.getDebugName(inst.subfamilyNameID)
            name.setName(orig, max_id, 3, 1, 0x409)
            inst.subfamilyNameID = max_id

    ps_family = family.replace(" ", "")
    for nameID, value in {
        1: family, 2: style, 4: f"{family} {style}",
        6: f"{ps_family}-{style}", 16: family, 17: style,
    }.items():
        for r in name.names:
            if r.nameID == nameID:
                name.setName(value, nameID, r.platformID, r.platEncID, r.langID)

    return font


def _verify(font):
    print("\n=== Verification ===")
    for axis in font["fvar"].axes:
        hidden = " [HIDDEN]" if axis.flags & 0x0001 else ""
        print(f"  {axis.axisTag}: {axis.minValue} → {axis.defaultValue} → {axis.maxValue}{hidden}")
    avar = font.get("avar")
    has_v2 = avar and hasattr(avar, "table") and avar.table is not None
    print(f"  avar2: {'present ✓' if has_v2 else 'MISSING ✗'}")
    for r in font["name"].names:
        if r.nameID in (1, 4, 6) and r.platformID == 3:
            print(f"  nameID {r.nameID}: {r.toUnicode()}")


def build_flex(input_path: str, output_dir: str = ".", helper_ramps=None,
               family: str = config.FLEX_FAMILY_NAME) -> tuple[str, str]:
    print(f"Loading {input_path}...")
    font = TTFont(input_path)

    # True-HOI input carries the hidden helper axes; their ramps default to the settled design
    # (helpers = normalized GEOM). A plain input has none and no ramps.
    helpers = [tag for tag in hoi_axes.HELPER_AXES if axis_by_tag(font["fvar"].axes, tag)]
    if helpers and helper_ramps is None:
        geom = axis_by_tag(font["fvar"].axes, "GEOM")
        helper_ramps = hoi_axes.default_ramps(geom.minValue, geom.defaultValue, geom.maxValue)  # compiled (pre-shift) normalization

    shifted = ", ".join(f"{tag}→{default}" for tag, default in config.SHIPPING_DEFAULTS.items())
    print(f"Shifting defaults ({shifted})...")
    font = shift_defaults(font)

    print(f"Injecting avar2 (YTAS follows opsz{', ' + '/'.join(helper_ramps) + ' follow GEOM' if helper_ramps else ''})...")
    font = inject_avar2(font, helper_ramps)

    print(f"Hiding {', '.join(['YTAS', *helpers])}...")
    font = hide_axes(font, ["YTAS", *helpers])

    print(f"Renaming to {family}...")
    font = rename_font(font, family=family)

    print("Building STAT + disambiguating instance names...")
    renamed, _ = apply_stat_and_instance_names(font)
    print(f"  STAT rebuilt (YTAS hidden → no STAT values), {renamed} instance names disambiguated")
    add_stat_axis_records(font, helpers)

    append_distribution_sha(font)   # live calcom/sans hash in nameID 5 (before save → both ttf+woff2)

    _verify(font)

    # Match the base VF filename convention ("CalSansVF.ttf") rather than appending a
    # "-Regular" style suffix — this is a variable font, not the Regular master.
    stem = f"{family.replace(' ', '')}VF"
    ttf_path   = os.path.join(output_dir, f"{stem}.ttf")
    woff2_path = os.path.join(output_dir, f"{stem}.woff2")

    font.save(ttf_path)
    print(f"\nTTF:   {os.path.getsize(ttf_path):,} bytes → {ttf_path}")

    font.flavor = "woff2"
    font.save(woff2_path)
    print(f"WOFF2: {os.path.getsize(woff2_path):,} bytes → {woff2_path}")

    return ttf_path, woff2_path


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python scripts/build_flex.py <input.ttf> [output_dir]")
        sys.exit(1)
    build_flex(sys.argv[1], sys.argv[2] if len(sys.argv) > 2 else ".")
