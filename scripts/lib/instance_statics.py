"""Instance the static styles from the compiled variable font (fontTools instancer): each style
pins its axis coordinates (from manifest.py) and bakes in the matching GEOM FeatureVariations.
See VISION.md §7."""
import os
from io import BytesIO
from multiprocessing import Pool

from tqdm import tqdm
from fontTools.ttLib import TTFont
from fontTools.varLib.instancer import instantiateVariableFont

from scripts import config
from scripts.lib.manifest import all_styles

# The variable font is loaded once into bytes and handed to each worker process
# via the Pool initializer, so we don't re-read/decompile it 384 times.
_VAR_FONT_BYTES = None


def _init_worker(font_bytes):
    global _VAR_FONT_BYTES
    _VAR_FONT_BYTES = font_bytes


def _widen_advances(font, delta):
    """Add `delta` to every spacing glyph's advance width, leaving LSB untouched so
    outlines and anchors don't move (no accent/component drift). Zero-advance combining
    marks are skipped. hhea's derived metrics (advanceWidthMax etc.) are recomputed."""
    hmtx = font["hmtx"]
    for name in font.getGlyphOrder():
        adv, lsb = hmtx[name]
        if adv > 0:
            hmtx[name] = (adv + delta, lsb)
    font["hhea"].recalc(font)


def _instance_one(task):
    axes, out_path, widen = task
    font = TTFont(BytesIO(_VAR_FONT_BYTES))
    instantiateVariableFont(font, axes, inplace=True, optimize=True, updateFontNames=False)
    if widen:
        _widen_advances(font, config.MICRO_TRACKING_ADVANCE)
    font.save(out_path)


def run_instancer_statics(var_ttf: str, build_dir: str, build_italic: bool = False):
    """Generate static instances by pinning the variable font at each style's coordinates.
    instancer bakes the GEOM FeatureVariations per instance, so each family (A11y/UI/Text/Geo)
    gets the correct substituted glyphs — which a plain fontmake static build (VARIATIONS
    disabled) cannot do. Source of truth for coordinates + filenames: scripts/lib/manifest.py.

    Instances are independent, so they're farmed out across processes."""
    static_dir = os.path.join(build_dir, "static")
    os.makedirs(static_dir, exist_ok=True)
    styles = all_styles(build_italic)

    with open(var_ttf, "rb") as f:
        font_bytes = f.read()
    tasks = [(dict(s["axes"]), os.path.join(static_dir, s["filename"]), s["opsz"] == "micro")
             for s in styles]
    workers = os.cpu_count() or 4

    print(f"🔨 Instancing {len(styles)} static styles from {os.path.basename(var_ttf)} "
          f"across {workers} workers...")
    with Pool(processes=workers, initializer=_init_worker, initargs=(font_bytes,)) as pool:
        for _ in tqdm(pool.imap_unordered(_instance_one, tasks), total=len(tasks),
                      desc="   ↳ Instancing", leave=False):
            pass
    print(f"   ✅ {len(styles)} static instances written to {static_dir}/")
