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

# gf vertical metrics. Three GF conformance fixes, applied to every GF deliverable:
#  1. fsSelection bit 7 (USE_TYPO_METRICS). Without it Windows apps lay out from win
#     (1024/245) while everyone else uses typo (900/245) — one font, two line heights.
#     This is the only vertical-metrics FAIL in the GF check set.
#  2. hhea mirrors win (1024 / -245). It currently copies typo, so mac and Windows
#     disagree for the same reason. win is NOT lowered to meet hhea: YTAS pushes accents
#     to 800, so the 1024 headroom has to stay or tall accents clip.
#  3. sTypoLineGap 55. typo sums to 900 + 245 + 0 = 1145/1000 = 1.145 em; GF's house
#     default is ~1.2, and 55 lands exactly on 1200 without moving a drawn outline.
GF_USE_TYPO_METRICS = True
GF_TYPO_LINE_GAP    = 55
GF_HHEA_MIRRORS_WIN = True

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


