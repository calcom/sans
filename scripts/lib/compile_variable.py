"""Run fontmake to compile the variable fonts (main build + Flex), then hand the result to the
post-compile fix-ups in postprocess.py (GEOM band merge, default shift, STAT/instance names)."""
import os
import sys
import shutil
import signal
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


def _run_fontmake(args, log_path):
    """Run fontmake with its output streamed to `log_path` rather than held in this process:
    a full run's log is large, and a file survives when the child is killed mid-compile."""
    with open(log_path, "w") as log:
        code = subprocess.run([*FONTMAKE, *args], stdout=log, stderr=subprocess.STDOUT).returncode
    if code != 0:
        with open(log_path) as log:
            print(log.read())
        why = f"killed by {signal.Signals(-code).name}" if code < 0 else f"exit status {code}"
        print(f"   ❌ fontmake {why} — full log: {log_path}")
        raise subprocess.CalledProcessError(code, [*FONTMAKE, *args])


def _keep_premerge(ttf, build_dir, prefix=""):
    """Keep fontmake's raw output (before the GSUB merge) so the merge can be tested on it."""
    os.makedirs(f"{build_dir}/premerge", exist_ok=True)
    shutil.copy(ttf, f"{build_dir}/premerge/{prefix}{Path(ttf).name}")


def run_fontmake_variable(ready_path: str, build_dir: str):
    # Start clean so stale outputs from a prior run (e.g. an old output name)
    # don't get re-globbed and duplicated through post-processing/packaging.
    shutil.rmtree(f"{build_dir}/variable", ignore_errors=True)
    os.makedirs(f"{build_dir}/variable", exist_ok=True)

    print("🔨 Building variable font...")
    _run_fontmake(
        ["-g", ready_path, "-o", "variable",
         "--output-dir", f"{build_dir}/variable",
         "--master-dir", f"{build_dir}/master_ufo",
         "--filter", "FlattenComponentsFilter",
         "--debug-feature-file", f"{build_dir}/debug_features.fea"],
        f"{build_dir}/variable.fontmake.log")
    print("   ✅ Variable font built")

    for ttf in Path(f"{build_dir}/variable").glob("*.ttf"):
        _keep_premerge(ttf, build_dir)
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
    _run_fontmake(
        ["-g", flex_path, "-o", "variable",
         "--output-dir", out_dir, "--master-dir", f"{build_dir}/flex_ufo",
         "--filter", "FlattenComponentsFilter"],
        f"{build_dir}/flex_variable.fontmake.log")

    ttf = str(sorted(Path(out_dir).glob("*.ttf"))[0])
    _keep_premerge(ttf, build_dir, "flex-")
    merge_gsub_feature_variations(ttf)
    ensure_gasp(ttf)
    ensure_smart_dropout(ttf)
    print(f"   ✅ HOI (Flex) variable font built → {ttf}")
    return ttf


def run_fontmake_masters(glyphs_path: str, master_dir: str) -> str:
    """fontmake's own Glyphs → UFO step (the build_masters every `-g` compile runs), stopped
    there so sources can be added to the designspace before compiling. Returns its path."""
    shutil.rmtree(master_dir, ignore_errors=True)
    ds_path = f"{master_dir}/{Path(glyphs_path).stem}.designspace"
    print("🧱 Writing master UFOs...")
    _run_fontmake(["-g", glyphs_path, "-o", "ufo", "--master-dir", master_dir,
                   "--designspace-path", ds_path], f"{master_dir}.fontmake.log")
    return ds_path


def run_fontmake_flex_hoi(ds_path: str, build_dir: str) -> str:
    """Compile the true-HOI designspace (stock sources + helper axes + helper sources) and run
    the same post-compile passes as the piecewise Flex. Returns the compiled TTF path."""
    out_dir = f"{build_dir}/flexhoi_variable"
    shutil.rmtree(out_dir, ignore_errors=True)
    os.makedirs(out_dir, exist_ok=True)

    print("🪄 Compiling true-HOI (Flex) variable font...")
    _run_fontmake(["-m", ds_path, "-o", "variable", "--output-dir", out_dir,
                   "--filter", "FlattenComponentsFilter"],
                  f"{build_dir}/flexhoi_variable.fontmake.log")

    ttf = str(sorted(Path(out_dir).glob("*.ttf"))[0])
    _keep_premerge(ttf, build_dir, "flexhoi-")
    merge_gsub_feature_variations(ttf)
    ensure_gasp(ttf)
    ensure_smart_dropout(ttf)
    print(f"   ✅ true-HOI (Flex) variable font built → {ttf}")
    return ttf
