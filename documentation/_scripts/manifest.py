"""
Cal Sans static style catalog — derived from CalSansStyleNames.csv.
The CSV is a planning reference only; this file is the build-time source of truth.

Axes for static instances:
  GEOM : a11y (0-10), ui (15-30), base (40-60), geo (80-100)
  opsz : display (32pt), text (10pt), micro (8pt)
  wght : Regular, Medium, SemiBold, Bold
  YTAS : base (720), tall (800)
  SHRP : base (0), sharp (100)
  slnt : roman, italic

Total: 4 × 3 × 4 × 2 × 2 × 2 = 384 styles (192 roman + 192 italic)
"""

_GEOM = [("a11y", "A11y"), ("ui", "UI"), ("base", ""), ("geo", "Geo")]
_OPSZ = [("display", ""), ("text", "Text"), ("micro", "Micro")]
_WGHT = [("regular", "Regular"), ("medium", "Medium"), ("semibold", "SemiBold"), ("bold", "Bold")]
_YTAS = [("base", ""), ("tall", "Tall")]
_SHRP = [("base", ""), ("sharp", "Sharp")]
_SLNT = [("roman", ""), ("italic", "Italic")]

# Axis user-space coordinates for fontTools instancer
AXIS_VALUES = {
    "geom":  {"a11y": 0,   "ui": 25,  "base": 50,  "geo": 100},
    "opsz":  {"display": 32, "text": 10, "micro": 8},
    "wght":  {"regular": 400, "medium": 500, "semibold": 600, "bold": 700},
    "ytas":  {"base": 720, "tall": 800},
    "shrp":  {"base": 0,   "sharp": 100},
    "slnt":  {"roman": 0,  "italic": -12},
}

_WEIGHT_TOKENS = {"Regular", "Medium", "SemiBold", "Bold"}


def style_name_to_filename(style_name: str) -> str:
    """
    Derive the expected fontmake static TTF filename from a style name.
    "Cal Sans A11y Tall Regular"      → "CalSansA11yTall-Regular.ttf"
    "Cal Sans Geo Text SemiBold Italic" → "CalSansGeoText-SemiBoldItalic.ttf"
    Adjust if actual fontmake output differs.
    """
    tokens = style_name.split()
    split_at = next((i for i, t in enumerate(tokens) if t in _WEIGHT_TOKENS), -1)
    if split_at == -1:
        return style_name.replace(" ", "") + ".ttf"
    family = "".join(tokens[:split_at])
    style  = "".join(tokens[split_at:])
    return f"{family}-{style}.ttf"


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
                        for slnt_id, slnt_lbl in _SLNT:
                            if slnt_id == "italic" and not build_italic:
                                continue
                            parts = ["Cal Sans"] + [
                                lbl for lbl in (geom_lbl, tall_lbl, sharp_lbl, opsz_lbl, wght_lbl, slnt_lbl)
                                if lbl
                            ]
                            name = " ".join(parts)
                            styles.append({
                                "style_name": name,
                                "filename":   style_name_to_filename(name),
                                "geom":  geom_id,
                                "opsz":  opsz_id,
                                "wght":  wght_id,
                                "ytas":  ytas_id,
                                "shrp":  shrp_id,
                                "slnt":  slnt_id,
                                "axes": {
                                    "GEOM": AXIS_VALUES["geom"][geom_id],
                                    "opsz": AXIS_VALUES["opsz"][opsz_id],
                                    "wght": AXIS_VALUES["wght"][wght_id],
                                    "YTAS": AXIS_VALUES["ytas"][ytas_id],
                                    "SHRP": AXIS_VALUES["shrp"][shrp_id],
                                },
                            })
    return styles
