import sys
import os
import time
from pathlib import Path
from contextlib import contextmanager
import glyphsLib

from scripts import config
from scripts.config import (
    SOURCE_PATH, OUTPUT_PATH, OUTPUT_PATH_STATIC, OUTPUT_PATH_FLEX,
    BUILD_DIR, RELEASE_DIR, BUILD_ITALIC,
)
from scripts.lib.metrics import export_metrics
from scripts.lib.validate import validate_font_setup
from scripts.lib.prepare import patch_smart_components, prepare_for_fontmake, inject_ytas_ascend_braces
from scripts.lib.compile_variable import run_fontmake_variable, run_fontmake_flex
from scripts.lib.hoi import inject_hoi
from scripts.lib.utils import axis_index
from scripts.lib.instance_statics import run_instancer_statics
from scripts.lib.release import compress_build_outputs, build_release_folders
from scripts.lib import charalts


# ── Build step progress ───────────────────────────────────────────────────────
_STEP = {"n": 0, "total": 0}

@contextmanager
def step(label):
    """Print a numbered, timed step header around a build phase."""
    _STEP["n"] += 1
    print(f"\n▶ [{_STEP['n']}/{_STEP['total']}] {label}")
    t0 = time.time()
    yield
    print(f"   ⏱  {time.time() - t0:.1f}s")


class _Ctx:
    """Carries state (the in-memory font, compiled paths, run options) between stages."""
    def __init__(self, build_italic=BUILD_ITALIC, verbose=False, flex=True, docs=True):
        self.font = None
        self.var_ttf = None
        self.flex_var_ttf = None
        self.build_italic = build_italic
        self.verbose = verbose
        self.flex = flex
        self.docs = docs
        self.docs_proc = None
        self.docs_log = None


def stage_metrics(ctx):
    export_metrics(SOURCE_PATH)


def stage_load(ctx):
    ctx.font = glyphsLib.load(SOURCE_PATH)
    ctx.font.filepath = SOURCE_PATH


def stage_validate(ctx):
    validate_font_setup(ctx.font)


def stage_prepare(ctx):
    patch_smart_components(ctx.font)
    prepare_for_fontmake(ctx.font, verbose=ctx.verbose)
    inject_ytas_ascend_braces(ctx.font, verbose=ctx.verbose)


def stage_save_ready_sources(ctx):
    font = ctx.font
    print(f"💾 Saving to {OUTPUT_PATH}...")
    font.save(OUTPUT_PATH)
    os.makedirs(BUILD_DIR, exist_ok=True)
    fea_path = os.path.join(BUILD_DIR, "compiled_features_debug.fea")
    with open(fea_path, "w") as f:
        for prefix in getattr(font, "featurePrefixes", []):
            if not prefix.disabled:
                f.write(f"# PREFIX: {prefix.name}\n{prefix.code}\n\n")
        for feat in getattr(font, "features", []):
            if not feat.disabled:
                f.write(f"# FEATURE: {feat.name}\n{feat.code}\n\n")
    print(f"   📄 Feature code dumped to {fea_path}")

    for p in getattr(font, "featurePrefixes", []):
        if p.name == config.VARIATIONS_PREFIX_NAME:
            p.disabled = True
    font.save(OUTPUT_PATH_STATIC)
    for p in getattr(font, "featurePrefixes", []):
        if p.name == config.VARIATIONS_PREFIX_NAME:
            p.disabled = False


def stage_compile_variable(ctx):
    run_fontmake_variable(OUTPUT_PATH, BUILD_DIR)
    ctx.var_ttf = sorted(Path(f"{BUILD_DIR}/variable").glob("*.ttf"))[0]


def stage_docs(ctx):
    """Regenerate docs/character-alternatives.md + its ~900 SVG cells from the freshly
    compiled VF — in a SEPARATE python process that we do not wait on. The font
    build owns the terminal; the docs just have to be finished by the time anyone
    reads them. Skipped by --no-docs, which leaves the committed doc untouched."""
    if not (ctx.docs and config.BUILD_CHARALTS):
        print("   (skipped \u2014 --no-docs)")
        return
    ctx.docs_proc, ctx.docs_log = charalts.spawn(ctx.var_ttf)
    print(f"   \U0001f9ec character alternatives regenerating in pid {ctx.docs_proc.pid} "
          f"\u2192 {config.CHARALTS_MD}")
    print(f"   \U0001f4c4 log: {ctx.docs_log}")


def stage_compile_flex(ctx):
    """Cal Sans Flex = the HOI morphing build (Flex-family only). Re-prep a fresh font (so the
    base build's ctx.font stays untouched), inject the HOI braces + strip morphed conditionset
    swaps, save the disposable _FLEX source, and compile → the morphing variable TTF. build_flex
    (defaults/avar2/hide-YTAS/rename) runs later in packaging on this VF."""
    if not ctx.flex:
        print("   (skipped — --no-flex)")
        return
    font = glyphsLib.load(SOURCE_PATH)
    font.filepath = SOURCE_PATH
    patch_smart_components(font)
    prepare_for_fontmake(font, verbose=ctx.verbose)
    inject_ytas_ascend_braces(font, verbose=ctx.verbose)
    geom_i = axis_index(font.axes, "GEOM")
    inject_hoi(font, geom_i, verbose=ctx.verbose)
    # the HOI rename (handle_I) + sub-strip can orphan class refs → filter classes to live glyphs
    existing = {g.name for g in font.glyphs}
    for cls in list(getattr(font, "classes", [])):
        cls.code = " ".join(n for n in cls.code.split() if n in existing)
    print(f"💾 Saving HOI source to {OUTPUT_PATH_FLEX}...")
    font.save(OUTPUT_PATH_FLEX)
    ctx.flex_var_ttf = run_fontmake_flex(OUTPUT_PATH_FLEX, BUILD_DIR)


def stage_instance_statics(ctx):
    run_instancer_statics(str(ctx.var_ttf), BUILD_DIR, build_italic=ctx.build_italic)


def stage_compress(ctx):
    compress_build_outputs(BUILD_DIR)


def stage_package(ctx):
    build_release_folders(BUILD_DIR, RELEASE_DIR, build_italic=ctx.build_italic,
                          flex_var_ttf=ctx.flex_var_ttf)


# Ordered (name, function, step-header) — the subset a runner can select from.
STAGES = [
    ("metrics",          stage_metrics,          "Extracting metrics"),
    ("load",             stage_load,             "Loading source (glyphsLib)"),
    ("validate",         stage_validate,         "Validating font setup"),
    ("prepare",          stage_prepare,          "Pre-processing for fontmake"),
    ("save_ready_sources", stage_save_ready_sources, "Saving variable/static-ready sources"),
    ("compile_variable", stage_compile_variable, "Compiling variable font (fontmake)"),
    ("docs",             stage_docs,             "Documenting character alternatives (background)"),
    ("compile_flex",     stage_compile_flex,     "Compiling HOI (Flex) variable font"),
    ("instance_statics", stage_instance_statics, "Instancing static styles"),
    ("compress",         stage_compress,         "Compressing to WOFF2"),
    ("package",          stage_package,          "Packaging release folders"),
]

# A run that stops here produces just the variable font — no statics/packaging.
VARIABLE_ONLY_STAGES = ("metrics", "load", "validate", "prepare", "save_ready_sources",
                        "compile_variable", "docs")


def run(only=None, build_italic=None, verbose=False, flex=True, docs=True):
    """Run the named subset of STAGES in order (default: all of them).

    build_italic, if given, overrides config.BUILD_ITALIC for this run.
    verbose enables full glyph/instance name listings in the prepare stage.
    flex=False skips the HOI (Cal Sans Flex) compile.
    docs=False skips regenerating the character-alternative doc.
    """
    stages = [s for s in STAGES if only is None or s[0] in only]

    print("🚀 Starting build")
    print(f"   Source: {SOURCE_PATH}")

    if not os.path.exists(SOURCE_PATH):
        print(f"❌ File not found: {SOURCE_PATH}")
        sys.exit(1)

    _STEP["n"] = 0
    _STEP["total"] = len(stages)
    ctx = _Ctx(build_italic=BUILD_ITALIC if build_italic is None else build_italic,
               verbose=verbose, flex=flex, docs=docs)
    for _, fn, label in stages:
        with step(label):
            fn(ctx)

    # The fonts are done and reported. Only now is it worth mentioning the docs,
    # and only if they somehow outlived the whole rest of the build.
    if ctx.docs_proc and ctx.docs_proc.poll() is None:
        print(f"\n   \U0001f9ec character-alternative doc still writing (pid "
              f"{ctx.docs_proc.pid}) \u2014 see {ctx.docs_log}")


def _parse_args(argv=None):
    import argparse
    parser = argparse.ArgumentParser(description="Cal Sans build pipeline")
    parser.add_argument(
        "--varonly", "--variable-only", dest="variable_only", action="store_true",
        help="Compile only the variable font and stop, skipping instancing, compression, "
             "and packaging. The variable build still runs its post-compile passes "
             "(GEOM merge, YTAS accent-rise, axis-default shift, STAT + instance names).",
    )
    parser.add_argument(
        "--roman", action="store_true",
        help="Build roman styles only (192), skipping the italic statics. "
             "Italics are built by default (384 styles).",
    )
    parser.add_argument(
        "--verbose", action="store_true",
        help="Show full glyph/instance name lists in the pre-processing stage "
             "(default: just the counts and first few names)",
    )
    parser.add_argument(
        "--no-flex", dest="flex", action="store_false",
        help="Skip the HOI / Cal Sans Flex compile (the morphing variable build). "
             "Flex is built by default.",
    )
    parser.add_argument(
        "--no-docs", dest="docs", action="store_false",
        help="Do NOT regenerate docs/character-alternatives.md or its SVG cells. "
             "The doc is rebuilt on every build by default, in its own process.",
    )
    return parser.parse_args(argv)


def main(argv=None):
    args = _parse_args(argv)
    only = VARIABLE_ONLY_STAGES if args.variable_only else None
    # Italics are the default (config.BUILD_ITALIC=True); --roman opts out.
    build_italic = False if args.roman else None
    run(only=only, build_italic=build_italic, verbose=args.verbose, flex=args.flex,
        docs=args.docs)

if __name__ == "__main__":
    main()
