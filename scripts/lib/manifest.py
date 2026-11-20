"""
Cal Sans static style catalog — derived from CalSansStyleNames.csv.
The CSV is a planning reference only; this file is the build-time source of truth.

Axes for static instances:
  GEOM : a11y (0-10), ui (15-30), base (40-60), geo (80-100)
  opsz : display (32pt), text (10pt), micro (8pt)
  wght : Regular, Medium, SemiBold, Bold
  YTAS : base (720), tall (800)
  SHRP : base (0), sharp (100)
  ital : roman, italic

Total: 4 × 3 × 4 × 2 × 2 × 2 = 384 styles (192 roman + 192 italic)
"""

from scripts import config

_GEOM = config.STATIC_GEOM_TOKENS
_OPSZ = config.STATIC_OPSZ_TOKENS
_WGHT = config.STATIC_WGHT_TOKENS
_YTAS = config.STATIC_YTAS_TOKENS
_SHRP = config.STATIC_SHRP_TOKENS
_ITAL = config.STATIC_ITAL_TOKENS

# Axis user-space coordinates for fontTools instancer
AXIS_VALUES = config.STATIC_AXIS_VALUES

_WEIGHT_TOKENS = {"Regular", "Medium", "SemiBold", "Bold"}
# Family/style split anchors: a weight word, or "Italic" (for the Regular-Italic
# case where "Regular" is elided so there's no weight word before "Italic").
_STYLE_TOKENS = _WEIGHT_TOKENS | {"Italic"}


def style_name_to_filename(style_name: str) -> str:
    """
    Derive the expected fontmake static TTF filename from a style name.
    "Cal Sans A11y Tall Regular"      → "CalSansA11yTall-Regular.ttf"
    "Cal Sans Geo Text SemiBold Italic" → "CalSansGeoText-SemiBoldItalic.ttf"
    "Cal Sans A11y Italic"              → "CalSansA11y-Italic.ttf"
    Adjust if actual fontmake output differs.
    """
    tokens = style_name.split()
    split_at = next((i for i, t in enumerate(tokens) if t in _STYLE_TOKENS), -1)
    if split_at == -1:
        return style_name.replace(" ", "") + ".ttf"
    family = "".join(tokens[:split_at])
    style  = "".join(tokens[split_at:])
    return f"{family}-{style}.ttf"


_RIBBI_STYLES = {"Regular", "Bold", "Italic", "Bold Italic"}


def style_name_records(style_name: str) -> dict:
    """OpenType name records for a static style, e.g. "Cal Sans Micro A11y Medium Italic".

    nameID 16/17 carry the FULL typographic family/subfamily; 1/2 carry RIBBI-legacy
    names — Medium/SemiBold fold their weight into the family (nameID 1) so the 4-slot
    legacy grouping (Regular/Italic/Bold/Bold Italic) still style-links in old apps.
    Returns {"records": {nameID: value}, "italic": bool}."""
    tokens = style_name.split()
    split_at = next((i for i, t in enumerate(tokens) if t in _STYLE_TOKENS), len(tokens))
    typo_family = " ".join(tokens[:split_at]) or "Cal Sans"
    typo_subfamily = " ".join(tokens[split_at:]) or "Regular"
    italic = "Italic" in tokens
    if typo_subfamily in _RIBBI_STYLES:
        legacy_family, legacy_subfamily = typo_family, typo_subfamily
    else:  # Medium / SemiBold (+ Italic): fold the weight into the legacy family
        weight = typo_subfamily.replace("Italic", "").strip()
        legacy_family = f"{typo_family} {weight}"
        legacy_subfamily = "Italic" if italic else "Regular"
    full = f"{typo_family} {typo_subfamily}"
    ps = f"{typo_family}-{typo_subfamily}".replace(" ", "")
    return {
        "records": {1: legacy_family, 2: legacy_subfamily, 4: full, 6: ps,
                    16: typo_family, 17: typo_subfamily},
        "italic": italic,
        # Bold in the RIBBI sense, which is what fsSelection and macStyle describe — the
        # legacy slot, not the weight. Medium and SemiBold fold their weight into the
        # legacy FAMILY and sit in the Regular slot, so they are not "bold" here even
        # though they are heavier than Regular.
        "bold": legacy_subfamily in ("Bold", "Bold Italic"),
    }


def all_styles(build_italic: bool = False) -> list[dict]:
    """
    Return all style records for the current build.
    build_italic=False → 192 roman styles
    build_italic=True  → 384 styles (roman + italic)
    """
    styles = []
    for geom_id, geom_lbl in _GEOM:
        for opsz_id, opsz_lbl in _OPSZ:
            for wght_id, wght_lbl in _WGHT:
                for ytas_id, tall_lbl in _YTAS:
                    for shrp_id, sharp_lbl in _SHRP:
                        for ital_id, ital_lbl in _ITAL:
                            if ital_id == "italic" and not build_italic:
                                continue
                            # opsz first, matching the master order + INSTANCE_NAME_ORDER
                            # (so statics read "Cal Sans Micro A11y Regular", not GEOM-first).
                            parts = ["Cal Sans"] + [
                                lbl for lbl in (opsz_lbl, geom_lbl, tall_lbl, sharp_lbl, wght_lbl, ital_lbl)
                                if lbl
                            ]
                            # RIBBI: "Regular" is implied once Italic is present → "… Italic".
                            if "Italic" in parts and "Regular" in parts:
                                parts.remove("Regular")
                            name = " ".join(parts)
                            styles.append({
                                "style_name": name,
                                "filename":   style_name_to_filename(name),
                                "geom":  geom_id,
                                "opsz":  opsz_id,
                                "wght":  wght_id,
                                "ytas":  ytas_id,
                                "shrp":  shrp_id,
                                "ital":  ital_id,
                                "axes": {
                                    "GEOM": AXIS_VALUES["geom"][geom_id],
                                    "opsz": AXIS_VALUES["opsz"][opsz_id],
                                    "wght": AXIS_VALUES["wght"][wght_id],
                                    "YTAS": AXIS_VALUES["ytas"][ytas_id],
                                    "SHRP": AXIS_VALUES["shrp"][shrp_id],
                                    "ital": AXIS_VALUES["ital"][ital_id],
                                },
                            })
    return styles
