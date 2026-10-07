# calBuild

The Cal Sans build pipeline: a single automated build for a 6-axis variable font (`opsz`,
`GEOM`, `wght`, `YTAS`, `SHRP`, `ital`). The `scripts` package takes the
hand-drawn Glyphs source and produces the variable font, 384 static instances (192 roman-only), and a set of
curated release packages, all without ever modifying the source file.

## Setup

You'll need Python 3.9+ and a virtual environment.

### MacOS

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```
### Windows (PowerShell)

```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

`requirements.txt` installs:
- **glyphsLib** — reads the `.glyphspackage` source
- **fontTools** — low-level font table manipulation (instancing, avar2, etc.)
- **fontmake** — compiles UFOs/designspace into variable & static binaries
- **tqdm** — progress bars for the long-running steps
- **uharfbuzz** — gives fontTools access to HarfBuzz's `hb.repack` table
  packer, which is needed to correctly resolve GPOS table overflow during
  compilation (without it, fontTools falls back to a legacy packer that
  crashes on this font's large `@All`-class GPOS table)
- **brotli** — required by fontTools to write `.woff2` files (step 10/11
  compresses the variable font and all static instances to WOFF2)
- **skia-pathops** — unions overlapping contours so the animated README sheet
  can draw glyphs as clean outlines (only `docsheets metrics` needs it)

## Run the build

```bash
python3 -m scripts
```

This runs the entire pipeline end-to-end — source → packaged release folders —
printing a numbered, timed `[n/11]` header for each step. Expect it to take a
while: `glyphsLib.load` alone takes ~45s, and the instancing/compiling steps
are CPU-heavy (the full run can take well over ten minutes).

Useful flags:

- `--varonly` (alias `--variable-only`) — compile just the variable font and
  stop, skipping instancing, compression, and packaging. The variable build
  still runs its post-compile passes (GEOM merge, YTAS accent-rise, axis-default
  shift, STAT + instance names), so it's a fast way to test variable-font output.
- `--roman` — build roman styles only (192), skipping the italic statics.
  Italics are built by default (384 styles).
- `--no-flex` — skip the morphing variable-font builds (step 8), including
  **Cal Sans Flex**, the true-HOI font. They are built **by default** on every
  full run; this opts out for a faster build when you only need the base/static
  families. `--no-flex-hoi` skips only Cal Sans Flex.
- `--no-docs` — skip regenerating the documentation: the character-alternatives
  doc (step 7) and the static `fonts/README.md` sheets (after step 11). Both are
  rebuilt on **every** run by default. Use this when you only want fonts: it
  leaves `documentation/` exactly as committed and shaves ~1,800 file writes off
  the run. `fonts/README.md` itself is still re-emitted and stamped. See
  [Documentation](#documentation).
- `--verbose` — show full glyph/instance name lists in the pre-processing
  stage (step 4); by default only counts and the first few names are printed.

### What it does

1. **Extract metrics** — dumps master metrics/stems to `sources/metrics.json`.
2. **Load source** — reads `sources/CalSans.glyphspackage` via glyphsLib.
3. **Validate** — checks axes, master count, and opsz values match expectations.
4. **Pre-process for fontmake** — translates the source from the Glyphs-app
   feature dialect to the fontmake/feaLib dialect entirely in memory.
5. **Save `_READY` packages** — writes disposable `CalSans_READY*.glyphspackage`
   intermediates that fontmake compiles from.
6. **Compile the variable font** — runs `fontmake`, then post-processes the
   result (merges overlapping GEOM feature variations, shifts axis defaults).
7. **Document character alternatives** — regenerates `documentation/character-alternatives.md`
   from the freshly compiled variable font: every `ssXX`/`cvXX` feature, one row
   each, with every glyph the feature *produces* drawn as its own SVG cell in
   `documentation/images/character-alternatives/`. Runs in a **separate Python process
   that nothing waits on**, so ~1,760 SVG writes never delay the font build's
   success report and a failure in the docs can never fail the fonts. The build
   prints the child's pid and a log path (`scripts/temp/character-alternatives.log`)
   and moves straight on. Skip with `--no-docs`.
8. **Compile the morphing fonts** — **Cal Sans Flex** is true HOI: it
   re-preps a fresh copy of the source, keeps the stock `rclt` GEOM swaps, adds
   three hidden helper axes (`GE1M`, `GE2M`, `GE3M`) and writes the morph
   windows as sparse masters on them, then compiles a **second** variable font
   from that disposable `_FLEXHOI` package. A post-process applies avar2 (the
   helpers follow `GEOM`, the hidden `YTAS` follows `opsz`), hides those axes
   and renames it to **Cal Sans Flex**. The base build is untouched. Skip with
   `--no-flex`.
9. **Instance statics** — generates all static styles (384 with italics by
   default, or 192 roman-only with `--roman`) into `scripts/temp/static/`, baking
   the correct GEOM substitutions into each.
10. **Compress** — generates `.woff2` siblings for the variable font and statics.
11. **Package releases** — sorts the finished exports into the `fonts/` release
    folders (e.g. `calsans-var-full`, `calsans-var-flex`, `calsans-static-essentials`,
    `calsans-gf-workspace`, etc.)
    It also re-emits `fonts/README.md` from its template, stamped with the built
    version, then starts the README sheets redrawing in a background process
    (log: `scripts/temp/docsheets.log`). Skip the sheets with `--no-docs`.

### Configuration

A few constants in `scripts/config.py` control the run:

- `BUILD_ITALIC` — `True` (default) builds the full 384 styles (roman + italic);
  `False` builds 192 roman-only. The CLI `--roman` flag forces roman-only for a
  single run.
- `SOURCE_PATH` / `OUTPUT_PATH` / `BUILD_DIR` / `RELEASE_DIR` — paths for the
  source, intermediate `_READY` files, build artifacts, and final release
  folders, respectively.
- `STATIC_*_TOKENS` / `STATIC_AXIS_VALUES` — the per-axis style-name tokens
  and instancer coordinates that `scripts/lib/manifest.py` combines into the
  full static-style catalog.
- `BUILD_CHARALTS` — `True` (default) regenerates the character-alternatives
  doc on every run; `False` is the permanent form of `--no-docs`.
  `CHARALTS_MD` / `CHARALTS_SVG_DIR` set where the markdown and its cells land.

## Output

There are two output locations, serving different purposes:

- **`scripts/temp/`** — raw/intermediate compiled output, the working area used
  before final packaging:
  - `scripts/temp/variable/` — compiled variable font(s)
  - `scripts/temp/static/` — all instanced static styles (TTF + WOFF2)
- **`fonts/`** — the final, curated, ready-to-ship release packages, sorted
  from `scripts/temp/`'s output by step 11/11. **This directory is wiped and
  regenerated from scratch on every run.** The packages are:

  | Package | Contents |
  |---------|----------|
  | `calsans-var-full` | The full variable font, all axes exposed |
  | `calsans-var-flex` | **Cal Sans Flex** — the true-HOI morphing font: GEOM letterforms blend along curved paths on hidden helper axes (`GE1M`–`GE3M`) that avar2 drives from `GEOM`, with `YTAS` hidden and following `opsz`. Built by default (step 8); skip with `--no-flex`. The folder's full contents are listed in `fonts/README.md`. |
  | `calsans-cossui` | Variable font with `ss*`/`cv*`/`aalt` features and their alternate glyphs subset out |
  | `calsans-gf-api` | Same subsetting as `cossui`, packaged for the Google Fonts API |
  | `calsans-gf-api-textui` | **Cal Sans Text UI** — second GF family ([google/fonts#9970](https://github.com/google/fonts/issues/9970)): `wght`-only (400–700) VF pair, `opsz` 10 / `GEOM` 25 / `YTAS` 760 baked, curved l (`l.rcltA11y`) as default |
  | `calsans-static-full` | All static instances (384 with italics by default, or 192 roman-only with `--roman`) |
  | `calsans-static-{a11y,ui,base,geo}` | Per-GEOM-family static subsets (base YTAS/SHRP only) |
  | `calsans-static-essentials` | Curated minimal set: Text+UI (roman) and Display+Base (incl. italics), TTF-only |
  | `calsans-gf-workspace` | Same two families as `static-essentials`, without `opsz`-axis awareness; the Text UI half is instanced fresh at the `gf-api-textui` position (`YTAS` 760, curved l) |

## Documentation

The build writes two sets of documentation, both drawn from the fonts it just
made, so they can never describe a build that no longer exists. Both run in
their own Python process that nothing waits on (a failure there never fails the
fonts), both are skipped by `--no-docs`, and both are committed with the fonts.

| What | Made by | When | Lands in |
|------|---------|------|----------|
| Character alternatives: every `ssXX`/`cvXX`, every glyph it produces | `scripts/lib/charalts.py` | step 7, from the variable font | `documentation/character-alternatives.md` + `documentation/images/character-alternatives/` |
| `fonts/README.md`, version stamped | `scripts/lib/release.py` | step 11, every run, even with `--no-docs` | `fonts/README.md` |
| The specimen sheets `fonts/README.md` shows | `scripts/lib/docsheets.py` | after step 11, from the packaged statics | `documentation/images/fonts-readme/` |

### `fonts/README.md` is generated: edit the template

`fonts/` is wiped every run, so its README is re-emitted from
**`scripts/lib/fonts_README.md`**. Edit that, never `fonts/README.md`. Write the
version as `vX.XXX`; the build stamps every one with the version read from the
built variable font's name ID 5, so the README can never disagree with the
binary beside it. Two packages are left out of it on purpose: `adobe-vf` and
`gf-api-static` still build but are not described. Each run ends with a
reminder to edit the template if a package changed.

### The README sheets

Outlined text, no webfonts: they render the same in every browser. Every sheet
is written twice, `name.svg` and `name-dark.svg`, with the palette baked in,
because Safari ignores `prefers-color-scheme` inside an SVG loaded through
`<img>`; the README picks one with `<picture>`. They sit on the page with no
background or margin, like the character-alternative cells. Each is a table:
the label is README text on the left, the SVG holds only the specimen, and every
row of one table shares a scale (the waterfall's rows are drawn at real pixels).

| Sheet | Shows | Built by the build |
|-------|-------|--------------------|
| `tiers-{display,text,micro}` | Rows of a table: "Cal v2" in UI Display, Text and Micro at one size, each letter's advance marked. The text label says the opsz and how much wider each sets than Display | yes |
| `waterfall-{08…192}` | One row per size, 8px to 192px, each at **real pixels** (640 wide, drawn 1:1, `<img>` given explicit width and height), in its tier: Micro below 10px, Text 10–20px, Display from 24px. The longest of "Scheduling Infrastructure", "Sched Infra" and "Infra" that fits one line. The label (`8px`, tier) is text | yes |
| `families-{a11y,ui,base,geo}` | Rows of a table: "2160 just Groovy, I’ll Magic" in A11y, UI, Base and Geo, the family and its `GEOM` as a text label | yes |
| `textui-l-{a11y,ui}` | Two rows: Cal Sans A11y Text against Cal Sans Text UI (the static cut), how I, l and 1 are told apart; the text label spells out which I and l each draws | yes |
| `cuts-{default,tall,sharp,tall-sharp}` | A one-row table per static table: the four weights, roman over italic; the text label gives the name and its `YTAS`, `SHRP` and `opsz` | yes |
| `header` | **Animated.** The README's banner: this page's specimens at one scale, drifting right to left in three lanes, looping seamlessly, feathered at both edges | **no** — by hand |
| `metrics` | **Animated.** "Hax" in every tier, Regular and Bold: only x-height moves, the small tiers set wider. Keeps a card, full width | **no** — by hand |

Animated sheets are judged by eye before they ship, so a build never redraws
them (`ANIMATED` in `docsheets.py`). Redraw any sheet by hand, from the repo
root, after a full build has filled `fonts/`:

```bash
python3 -m scripts.lib.docsheets              # every static sheet
python3 -m scripts.lib.docsheets metrics      # the animated one
python3 -m scripts.lib.docsheets tiers cuts   # just these
```

The README points at them with relative paths
(`../documentation/images/fonts-readme/…`), so the same file works in this repo
and in `calcom/sans`. When populating `sans`, copy `fonts/README.md` **and**
`documentation/images/fonts-readme/` together, or the pictures 404.

## Troubleshooting

- **`fontmake: Error: ... Generating fonts from Designspace failed`** during
  step 6/11, with a `GPOS` `OTLOffsetOverflowError` in the log — make sure
  `uharfbuzz` is installed (`pip install uharfbuzz` or re-run
  `pip install -r requirements.txt`). Without it, fontTools uses a legacy
  table packer that can crash on this font's large GPOS table.
- **`ImportError: No module named brotli`** during step 10/11 (WOFF2
  compression) — install `brotli` (`pip install brotli` or re-run
  `pip install -r requirements.txt`).
- **`command not found: fontmake`** — the `fontmake` console script may have
  installed outside your `PATH` (commonly under
  `~/Library/Python/<version>/bin` on macOS if not using a venv). Activating
  the venv from Setup avoids this; otherwise add that directory to `PATH`.
- **README sheets did not change after a build** — they redraw in the
  background; check `scripts/temp/docsheets.log`. `No module named 'pathops'`
  there means `skia-pathops` is missing (`pip install -r requirements.txt`); only
  the animated `metrics` sheet needs it, and builds do not draw that one.
