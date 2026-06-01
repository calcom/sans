"""
Strip every background layer from a .glyphs file.

Brace layers and bracket layers are NOT affected — only the per-layer
.background reference layers are cleared.

Usage:
    python3 strip_backgrounds.py MyFont.glyphs
        -> writes MyFont.stripped.glyphs next to the original

    python3 strip_backgrounds.py MyFont.glyphs --inplace
        -> overwrites MyFont.glyphs
"""
import sys
from pathlib import Path

from glyphsLib import GSFont


def strip(font: GSFont) -> int:
    cleared = 0
    for glyph in font.glyphs:
        for layer in glyph.layers:
            if layer._background is not None:
                layer._background = None  # bypass getter-only .background
                cleared += 1
    return cleared


def main(argv):
    if len(argv) < 2:
        print(__doc__)
        return 2

    src = Path(argv[1])
    inplace = "--inplace" in argv[2:]

    if not src.exists():
        print(f"File not found: {src}")
        return 1

    print(f"Loading {src} ...")
    font = GSFont(str(src))

    print("Stripping backgrounds ...")
    n = strip(font)
    print(f"  cleared {n} background layer(s)")

    if inplace:
        dst = src
    else:
        dst = src.with_suffix(".stripped.glyphs")

    print(f"Saving {dst} ...")
    font.save(str(dst))
    print("Done.")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
