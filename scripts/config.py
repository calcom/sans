"""Central configuration for the Cal Sans build pipeline.
"""

# ── Paths ─────────────────────────────────────────────────────────────────
SOURCE_PATH        = "sources/CalSans.glyphspackage"
OUTPUT_PATH        = "sources/CalSans_READY.glyphspackage"
OUTPUT_PATH_STATIC = "sources/CalSans_READY_static.glyphspackage"
OUTPUT_PATH_FLEX   = "sources/CalSans_FLEX.glyphspackage"   # disposable HOI brace-injected source
BUILD_DIR    = "scripts/temp"
RELEASE_DIR  = "fonts"
BUILD_ITALIC = True  # True → 384 styles (roman + italic); False → 192 roman. Default builds italics; CLI --roman opts out.


# ── Static style manifest (scripts/lib/manifest.py) ─────────────────────
# (id, name-label) tokens for each axis, in the order they combine into style names.
STATIC_GEOM_TOKENS = [("a11y", "A11y"), ("ui", "UI"), ("base", ""), ("geo", "Geo")]
STATIC_OPSZ_TOKENS = [("display", ""), ("text", "Text"), ("micro", "Micro")]
STATIC_WGHT_TOKENS = [("regular", "Regular"), ("medium", "Medium"), ("semibold", "SemiBold"), ("bold", "Bold")]
STATIC_YTAS_TOKENS = [("base", ""), ("tall", "Tall")]
STATIC_SHRP_TOKENS = [("base", ""), ("sharp", "Sharp")]
STATIC_ITAL_TOKENS = [("roman", ""), ("italic", "Italic")]

# Axis user-space coordinates for fontTools instancer, keyed by the same ids above.
STATIC_AXIS_VALUES = {
    "geom":  {"a11y": 0,   "ui": 25,  "base": 50,  "geo": 100},
    # display pins the large-optical master, which now sits at opsz=45 (was 32) after
    # the source relabel — pinning 45 keeps the Display statics identical in appearance.
    "opsz":  {"display": 45, "text": 10, "micro": 8},
    "wght":  {"regular": 400, "medium": 500, "semibold": 600, "bold": 700},
    "ytas":  {"base": 720, "tall": 800},
    "shrp":  {"base": 0,   "sharp": 100},
    # The font's italic axis is `ital` (0–1), NOT a slnt degree axis. Roman=0, Italic=1.
    "ital":  {"roman": 0,  "italic": 1},
}


# ── Release packaging (step5_release) ────
RELEASE_PACKAGE_PREFIX = "calsans"
PER_GEOM_PACKAGE_IDS = ("a11y", "ui", "base", "geo")


# ── Micro optical-size tracking (instance_statics) ───────────────────────
# The Micro (opsz=8) statics get +N units added to every spacing glyph's advance
# width (LSB unchanged → outlines/anchors don't move, so no accent/component drift;
# zero-advance combining marks are skipped). Looser spacing for the smallest size
# without editing source sidebearings.
MICRO_TRACKING_ADVANCE = 10


# ── Flex build / avar2 ───────
FLEX_FAMILY_NAME = "Cal Sans Flex"
FLEX_STYLE_NAME  = "Regular"
# (input opsz, output YTAS) calibration points for the avar2 axis mapping
FLEX_OPSZ_TO_YTAS = [(16.0, 720.0), (10.0, 750.0), (8.0, 800.0)]


# ── Expected source shape (pre-flight validation) ────────────────────────
EXPECTED_AXES         = ["opsz", "GEOM", "wght", "YTAS", "SHRP", "ital"]
EXPECTED_MASTER_COUNT = 8
EXPECTED_OPSZ_VALUES  = [10, 45]


# ── Dialect translation: Glyphs app → feaLib (prepare_for_fontmake) ──────
RCLT_FEATURE_TAG       = "rclt"
VARIATIONS_PREFIX_NAME = "VARIATIONS"
ALL_CLASS_NAME         = "All"
RENAME_GLYPHS_PARAM    = "Rename Glyphs"
# frac's `sub @Figures' fraction by @Numerators` rules need these three classes equal-length and
# index-aligned; prepare_for_fontmake drops any position where they disagree (commented / non-export).
FRACTION_PARALLEL_CLASSES = ("Figures", "Numerators", "Denominators")
CV_PARAM_PLATFORM_LANG = (3, 1, 0x0409)  # Windows, English (US) — used in cvParameters rewrite


# ── GSUB FeatureVariations merge (merge_gsub_feature_variations) ─────────
GEOM_AXIS_TAG = "GEOM"


# ── Shipping axis defaults (shift_axis_defaults / build_flex.shift_defaults) ─
# Pinned post-compile so the shipped default coordinate differs from the
# masters' authored default while keeping the full axis range available.
SHIPPING_DEFAULTS = {"opsz": 14, "GEOM": 25}

# cossui presents a narrower optical-size range than the full source: the opsz
# axis max is RELABELED from 45 down to 32 (pure fvar metadata — see
# release._relabel_opsz_max), so the display drawing the full build labels 45 is
# the same drawing cossui labels 32. var-full / gf-api / var-flex keep 8–45.
COSSUI_OPSZ_MAX = 32

# post.italicAngle for italic outputs. The source carries 9.5° on all four italic
# masters, and that reaches hhea's caret slope (rise 1000 / run 167), but varLib has
# no MVAR 'itlc' entry — italic angle cannot ride an axis into the variable font, so
# every font instanced from it inherits post.italicAngle = 0. Injected per-style
# instead (instance_statics._apply_static_names, release._set_style_names).
# Negative per the OpenType spec: a right-leaning face has a negative angle.
ITALIC_ANGLE = -9.5

# gf-api: per the Google Fonts fvar spec, a variable font's named instances must be
# Weight-only (Regular/Medium/SemiBold/Bold), each pinned at the shipping default of
# every OTHER axis (GEOM=25, opsz=14 from SHIPPING_DEFAULTS; SHRP/YTAS/ital at their
# fvar default). Default ON; set False to ship the full GEOM×opsz instance matrix.
# Settled with Dave (google/fonts#9970): GEOM-named instances stay out of GF — the
# UI/Text position ships as its own second family instead (gf-api-textui below).
GF_TRIM_INSTANCES = True
GF_WEIGHT_INSTANCES = [(400, "Regular"), (500, "Medium"), (600, "SemiBold"), (700, "Bold")]

# gf-api-textui: the second GF deliverable agreed in google/fonts#9970 — "Cal Sans
# Text UI", a small-optical-size variable font with ONE active axis (wght 400–700),
# shipped Roman + Italic like gf-api. Every other axis is baked at the Text UI
# position, except YTAS which is raised 720→760 for this family:
GF_TEXTUI_FAMILY = "Cal Sans Text UI"
GF_TEXTUI_PINNED = {"opsz": 10, "GEOM": 25, "YTAS": 760, "SHRP": 0}
# The curved l (l.rcltA11y) becomes the DEFAULT l for I/l differentiation — as a
# glyph-identity change, not a feature: release.py retargets cmap at the curved
# glyphs, renames them to the canonical names (l, lacute, …) on the final binary,
# and keeps a small rclt backstop + locl-chain twins for straight glyphs GSUB
# itself emits (see _make_curved_l_default / _save_with_curved_l_names). The
# kerning/contextual rules for the curved forms already exist and bind by glyph.
# The whole lowercase-l family goes, by COMPILED (production) glyph name:
# uni013C lcommaaccent · uni1E37 ldotbelow · uni1E39 ldotbelowmacron ·
# uni1E3B lmacronbelow. Uppercase I keeps its geometric form.
# ldot (ŀ U+0140) is deliberately NOT swapped: ccmp decomposes it to l +
# periodcentered.loclCAT — spaced/kerned as the long-term sub solution — and the
# emitted straight l is then caught by the rclt backstop, so ŀ rides the swap
# through its components exactly like typed l·.
GF_TEXTUI_CURVED_L_GLYPHS = (
    "l", "lacute", "lcaron", "lslash",
    "uni013C", "uni013C.loclMAH", "uni1E37", "uni1E39", "uni1E3B",
)
GF_TEXTUI_ALT_SUFFIX = ".rcltA11y"

# gf-api: axes to flag HIDDEN in fvar (parametric_axes_hidden). Only YTAS is a
# parametric axis (its registry entry: "A parametric axis for varying the height of
# lowercase ascenders") — GEOM (Geometric Form) and SHRP (Sharpness) are FEATURE axes
# and stay user-visible. YTAS is also slaved to opsz via avar2 in the Flex build.
GF_HIDDEN_AXES = ["YTAS"]

# gasp — applied to EVERY compiled font, not just the GF deliverables. Glyphs has no
# clean way to author this, so the pipeline writes it post-compile: version 1 with a
# single 0xFFFF range set to 15 (GRIDFIT | DOGRAY | SYMMETRIC_GRIDFIT | SYMMETRIC_SMOOTHING),
# i.e. "hint and antialias at every size". Deterministic here, and impossible to
# re-edit by accident in the source.
GASP_VERSION = 1
GASP_RANGES  = {65535: 15}

# gf vertical metrics. GF ships its own house scheme, which is NOT the one the main
# build uses. The main build follows Stephen Nixon's cap-centred scheme (hhea drives
# layout, bit 7 off, ~1.145 em); GF wants hhea/typo/win in agreement with bit 7 on and
# ~1.3 em. Both are internally consistent; they are simply different specs for different
# audiences, which is the entire reason the GF folders are cut separately.
#
# These exact values come from Emma Marichal's review (calcom/sans#36) and are the ones
# ALREADY LIVE on Google Fonts for Cal Sans — Text UI is a promotion of instances that
# shipped in 1.9, so changing them would reflow existing users' layouts. They are not
# negotiable on GF's side, and they clear all of the font's ink: 1029 covers the tallest
# stacked Vietnamese case accent (uni03060309.case) and 283 covers the deepest comma
# accent (-275), so the GF cut clips nothing.
GF_USE_TYPO_METRICS = True          # fsSelection bit 7

# Per-family presets. Cal Sans Text UI is its own family and draws to its own extremes,
# so it gets its own clipping box. The typographic and hhea values are Emma's for both
# families; only the win box differs, because only the win box describes outlines.
#
# Both extremes come from Bold and Bold Italic, and the two families differ for two
# unrelated reasons. The ASCENT differs because YTAS is baked at 760 in Text UI against
# 720 in the main family (1074 vs 1073 — one unit; the axis moves accents far less than
# it looks). The DESCENT differs because the families cover different design space, not
# because of any ascender: the main family spans the full GEOM and opsz ranges, while
# Text UI has both baked, so its Bold Italic never reaches as deep (-322 vs -342).
#
# These are measured across every file each family SHIPS, variable and static together.
# Emma's review quotes 1029/283 for Text UI, which is the variable font's default
# instance only — a variable font's stored bounds do not describe the extremes of its
# design space, and the static Bold in the workspace folder exceeds them.
#
# win_* is a FLOOR, not the final value: _unify_family_win_metrics measures the ink of
# every style actually shipped in a family and raises the pair to cover it, so a future
# design change cannot silently start clipping. The two families are resolved separately
# even where they share a delivery folder — they are separate families on GF.
GF_METRICS_DEFAULT = {
    "typo_ascender": 1000, "typo_descender": -300, "typo_line_gap": 0,
    "hhea_ascent":   1000, "hhea_descent":   -300, "hhea_line_gap": 0,
    "win_ascent":    1073, "win_descent":     342,
}
GF_METRICS_BY_FAMILY = {
    GF_TEXTUI_FAMILY: {"win_ascent": 1074, "win_descent": 322},
}


def gf_metrics_for(family: str) -> dict:
    """Vertical-metric preset for a family name, defaults filled in.

    Matched by longest prefix so a style-bearing name ("Cal Sans Text UI SemiBold",
    which is what a non-RIBBI static carries in nameID 1) resolves to its family, and
    "Cal Sans Text UI" wins over "Cal Sans" rather than the other way round."""
    preset = dict(GF_METRICS_DEFAULT)
    best = ""
    for known in GF_METRICS_BY_FAMILY:
        if family and family.startswith(known) and len(known) > len(best):
            best = known
    if best:
        preset.update(GF_METRICS_BY_FAMILY[best])
    return preset


# gf underline. GF requires ONE underlineThickness across a family, but Cal Sans
# interpolates it with weight (Regular/Italic 78, Medium 84, SemiBold 94, Bold 100) —
# which is the right design call and the wrong thing for their check. The GF cuts are
# pinned to the Medium values, the middle of that range, so no weight is badly served.
# This is a GF-only override: every other package keeps the interpolated value.
GF_UNDERLINE_THICKNESS = 84
GF_UNDERLINE_POSITION  = -77

# gf name-table shape. nameIDs 16/17 (typographic family/subfamily) are redundant when
# the variable font's origin is the Regular instance — fontbakery's googlefonts/font_names
# FAILs on their presence.
GF_DROP_TYPOGRAPHIC_NAMES = True

# gf STAT. Optical-size axis values must never be elidable (a reader has to be able to
# see which optical size they are looking at), and every VF needs an 'ital' axis record.
GF_OPSZ_NEVER_ELIDABLE = True
GF_ENSURE_ITAL_STAT    = True

# gf meta table. ScriptLangTags declaring what the font is designed and supported for.
GF_META_DESIGN_LANGS   = ["Latn"]
GF_META_SUPPORT_LANGS  = ["Latn"]

# smart dropout control. Applied to EVERY font, not just GF, exactly like gasp: the
# `prep` program below is the standard SCANCTRL/SCANTYPE pair that turns on smart
# dropout at all sizes. fontbakery FAILs its absence (opentype/smart_dropout) and there
# is no way to author it in a Glyphs source.
#   PUSHW[] 511 / SCANCTRL[] / PUSHB[] 4 / SCANTYPE[]
SMART_DROPOUT_PREP = b"\xb8\x01\xff\x85\xb0\x04\x8d"

# gf-api version string (name/version_format): GF requires the "Version X.YYY" prefix.
# Base version = head.fontRevision (the Glyphs Version field). A short git hash is
# appended for traceability (#54), auto-pulled from the DISTRIBUTION repo — the one whose
# git 'origin' is calcom/sans, NEVER calbuild.
GF_VERSION_PREFIX  = "Version "
GF_VERSION_SHA_ENV = "CALCOM_FONTS_SHA"   # CI override, wins if set
# Repos probed in order; the first whose 'origin' remote is calcom/sans wins. "." covers
# the builder running INSIDE calcom/sans (its duped scripts/ — the production case);
# "../sans" covers dev from a sibling calbuild checkout. Any other user (no calcom/sans
# remote found) simply gets no hash appended — the build never breaks for them.
GF_SHA_REPO_CANDIDATES = [".", "../sans"]
GF_SHA_REMOTE_MATCH    = "calcom/sans"

# gf-api-only name-table overrides — GF requires these, but the source's own values
# (Designer/Copyright = "Default" in Glyphs) ship on every OTHER build unchanged.
GF_DESIGNER  = "Mark Davis (Wordmark)"                 # nameID 9  (name/mandatory_entries)
GF_COPYRIGHT = ("Copyright 2026 The Cal Sans Project Authors "
                "(https://github.com/calcom/sans)")   # nameID 0  (font_copyright pattern)


# ── STAT table + fvar instance names (build_stat_and_instance_names) ─────
# glyphsLib ships the variable font with an empty STAT AxisValueArray and with
# opsz NOT encoded in the named-instance names, so the opsz=10 ("Text") and
# opsz=32 ("Display") instances collide (e.g. two "UI Regular") and Adobe can't
# pin optical size. We rebuild both post-compile.
#
# STAT axis values, in name-composition order (list index = AxisOrdering, so
# opsz composes before GEOM → "Text UI Regular", matching the source's
# Variable Style Names). flag 0x2 = ELIDABLE (hidden from composed names).
STAT_ELIDABLE = 0x2
STAT_AXES = [
    {"tag": "opsz", "name": "Optical size", "values": [
        {"value": 8,  "name": "Micro"},
        {"value": 10, "name": "Text"},
        {"value": 14, "name": "Default", "flags": STAT_ELIDABLE},
        {"value": 45, "name": "Display", "flags": STAT_ELIDABLE},
    ]},
    {"tag": "GEOM", "name": "Geometric Form", "values": [
        {"value": 0,   "name": "A11y"},
        {"value": 25,  "name": "UI"},
        {"value": 50,  "name": "Default", "flags": STAT_ELIDABLE},
        {"value": 100, "name": "Geo"},
    ]},
    {"tag": "wght", "name": "Weight", "values": [
        {"value": 400, "name": "Regular", "flags": STAT_ELIDABLE, "linkedValue": 700},
        {"value": 500, "name": "Medium"},
        {"value": 600, "name": "SemiBold"},
        {"value": 700, "name": "Bold"},
    ]},
    {"tag": "YTAS", "name": "Ascender Height", "values": [
        {"value": 720, "name": "Default", "flags": STAT_ELIDABLE},
        {"value": 800, "name": "Tall"},
    ]},
    {"tag": "SHRP", "name": "Sharp", "values": [
        {"value": 0,   "name": "Default", "flags": STAT_ELIDABLE},
        {"value": 100, "name": "Sharp"},
    ]},
    {"tag": "ital", "name": "Italic", "values": [
        {"value": 0, "name": "Roman", "flags": STAT_ELIDABLE, "linkedValue": 1},
        {"value": 1, "name": "Italic"},
    ]},
]
STAT_ELIDED_FALLBACK = "Regular"

# fvar instance subfamily names are composed from the static token tables (so
# they match the static families): opsz first, then GEOM, YTAS, SHRP, wght,
# ital. Empty-label tokens (Display opsz, base GEOM/YTAS/SHRP, Roman) drop out,
# so opsz=10 → "Text UI Regular" while its opsz=32 sibling stays "UI Regular".
INSTANCE_NAME_ORDER = [
    ("opsz", "opsz", STATIC_OPSZ_TOKENS),
    ("GEOM", "geom", STATIC_GEOM_TOKENS),
    ("YTAS", "ytas", STATIC_YTAS_TOKENS),
    ("SHRP", "shrp", STATIC_SHRP_TOKENS),
    ("wght", "wght", STATIC_WGHT_TOKENS),
    ("ital", "ital", STATIC_ITAL_TOKENS),
]


# ── YTAS accent-ascend  ───────────────────────────────────────────────────
# Lowercase base glyphs whose stacked top-marks (acute, grave, circumflex,
# dieresis, ring, dot-above, etc.) should ascend with the YTAS axis — "the way
# i and j were, only moving the top anchor". The i/j bases are idotless and
# jdotless in this font (an earlier note guessed dotlessi/uni0237 — wrong names,
# so the whole i/j family was silently skipped). Tall ascender letters
# (b d f h k l) carry their own YTAS brace layers, so their BASE extends with the
# axis (the inject guard skips an already-braced base). But their PRECOMPOSED
# accented composites (lacute, ldotbelowmacron, hcircumflex, …) have no brace, so
# the accent gets left behind as the ascender grows — issue #49. Listing the
# ascender bases pulls those composites into scope so the top mark rides 1:1.
# Uppercase stays out (cap height, not governed by YTAS).
YTAS_ACCENT_ASCEND_BASES = (
    "a", "a.alt", "a.rcltA11y", "a.rcltBase", "ae", "ae.rcltBase", "c", "c.rcltGeo", "idotless", "e",
    "g", "g.rcltA11y", "m", "n", "o", "oe", "p", "r", "s", "u", "u.rcltGeo", "uhorn", "uhorn.rcltGeo",
    "jdotless", "jdotless.rcltBase", "jdotless.rcltGeo", "w", "y", "y.rcltBase", "y.rcltGeo", "z",
    "b", "d", "h", "k", "l",  # ascenders — see note above (issue #49)
)
YTAS_ACCENT_ASCEND_DY = 80   # 1:1 with the 80u ascender extent (YTAS 720→800); issue #49
ITALIC_SLANT_DEGREES = 9.5  # used to derive the italic horizontal compensation (dx = dy·tan(angle))




# ── Character-alternative documentation ───────────────────────────────────────
# Every cvXX/ssXX feature, one row per feature, each glyph the feature PRODUCES
# drawn as its own cell. Regenerated from the compiled VF on every build — in a
# separate python process, so a 900-file SVG write never delays the font build's
# own success report. --no-docs (or BUILD_CHARVARIANTS=False) skips the regen and
# leaves whatever is already on disk untouched.
BUILD_CHARALTS   = True
CHARALTS_MD      = "docs/character-alternatives.md"
CHARALTS_SVG_DIR = "docs/images/character-alternatives"
