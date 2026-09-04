"""Run fontmake to compile the variable fonts (main build + Flex), then hand the result to the
post-compile fix-ups in postprocess.py (GEOM band merge, default shift, STAT/instance names)."""
import os
import sys
import shutil
import subprocess
from pathlib import Path

# Always invoke the fontmake of the interpreter running this pipeline (the venv),
# NOT a bare "fontmake" off PATH — a stale system install (older glyphsLib) keys
# brace-layer sources by raw name, silently dropping empty-named intermediate
# (SHRP etc.) layers. See the positional-figures SHRP regression.
FONTMAKE = [sys.executable, "-m", "fontmake"]

from scripts.lib.postprocess import (merge_gsub_feature_variations, shift_axis_defaults,
                                      build_stat_and_instance_names, stamp_distribution_sha,
                                      ensure_gasp, ensure_smart_dropout)


def run_fontmake_variable(ready_path: str, build_dir: str):
    # Start clean so stale outputs from a prior run (e.g. an old output name)
    # don't get re-globbed and duplicated through post-processing/packaging.
    shutil.rmtree(f"{build_dir}/variable", ignore_errors=True)
    os.makedirs(f"{build_dir}/variable", exist_ok=True)

    print("🔨 Building variable font...")
    result = subprocess.run(
        [*FONTMAKE, "-g", ready_path, "-o", "variable",
         "--output-dir", f"{build_dir}/variable",
         "--master-dir", f"{build_dir}/master_ufo",
         "--filter", "FlattenComponentsFilter",
         "--debug-feature-file", f"{build_dir}/debug_features.fea"],
        capture_output=True, text=True,
    )
    if result.returncode != 0:
        print(result.stdout)
        print(result.stderr)
        raise subprocess.CalledProcessError(result.returncode, result.args)
    print("   ✅ Variable font built")

    for ttf in Path(f"{build_dir}/variable").glob("*.ttf"):
        merge_gsub_feature_variations(str(ttf))
        shift_axis_defaults(str(ttf))
        build_stat_and_instance_names(str(ttf))
        stamp_distribution_sha(str(ttf))   # statics/subsets inherit this nameID 5
        ensure_gasp(str(ttf))              # ditto — every downstream cut inherits gasp
        ensure_smart_dropout(str(ttf))     # ditto — the `prep` smart-dropout program


def run_fontmake_flex(flex_path: str, build_dir: str) -> str:
    """Compile the HOI brace-injected source → the morphing variable TTF and merge the overlapping
    GEOM conditionsets. Shipping defaults / avar2 / STAT are applied afterward by build_flex, so
    this stops after the GSUB merge. Returns the compiled TTF path."""
    out_dir = f"{build_dir}/flex_variable"
    shutil.rmtree(out_dir, ignore_errors=True)
    os.makedirs(out_dir, exist_ok=True)

    print("🪄 Compiling HOI (Flex) variable font...")
    result = subprocess.run(
        [*FONTMAKE, "-g", flex_path, "-o", "variable",
         "--output-dir", out_dir, "--master-dir", f"{build_dir}/flex_ufo",
         "--filter", "FlattenComponentsFilter"],
        capture_output=True, text=True,
    )
    if result.returncode != 0:
        print(result.stdout)
        print(result.stderr)
        raise subprocess.CalledProcessError(result.returncode, result.args)

    ttf = str(sorted(Path(out_dir).glob("*.ttf"))[0])
    merge_gsub_feature_variations(ttf)
    ensure_gasp(ttf)
    ensure_smart_dropout(ttf)
    print(f"   ✅ HOI (Flex) variable font built → {ttf}")
    return ttf
