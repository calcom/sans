# final

The shipping exports. Six components, each baked to a light and a dark file.

These are what `font-proofer/README.md` points at via `<picture>`; nothing else
in `out/` is published. Regenerate with:

    python3 -c "from pathlib import Path; from bake import bake; \
      [ (Path('out/final')/o).write_text(bake((Path('out')/f'{n}.svg').read_text(), m)) \
        for n in ['CalGraphics-top','CalThreeWays','OpticalSize','StickerCode', \
                  'VariableMorph','VariableMorph2'] \
        for m, o in (('light', f'{n}.svg'), ('dark', f'{n}-dark.svg')) ]"

The sources are the six same-named files in `out/`, which keep their
`prefers-color-scheme` media query. Do NOT bake a baked file — the media query
is gone by then and both modes come out the same.

`../archive/` holds superseded scraped exports, kept only for reference.
