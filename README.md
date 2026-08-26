<!-- markdownlint-disable MD033 MD036 MD041 -->

# Cal Sans v2

[![npm](https://badgen.net/npm/v/cal-sans)](https://www.npmjs.com/package/cal-sans)
[![packagephobia/install](https://badgen.net/packagephobia/install/cal-sans)](https://www.npmjs.com/package/cal-sans)
[![packagephobia/publish](https://badgen.net/packagephobia/publish/cal-sans)](https://www.npmjs.com/package/cal-sans)
[![interactive showcase](documentation/images/isite.svg)](https://cal.com/font)

**Every size. Every surface. One file.**

Cal Sans is an open-source variable font built for product design and brand in the same breath. One file spans fine-print UI at 8 pt through hero display at 45, adapting its proportions, spacing, and geometry at every step along the way.

Write it once:

```css
font-family: "Cal Sans";
font-optical-sizing: auto;
```

That's the whole integration. The font handles the rest.

Commissioned by Peer Richelsen for [Cal.com](https://cal.com). Drawn, engineered, and shipped from a single hand-drawn source by [WORDMARK](https://wordmark.nyc). Free for commercial and personal use, thanks to the [SIL Open Font License, Version 1.1](#license).

## Shift the geometry.

`GEOM` is the axis the others orbit. Slide it and the letterforms travel from accessibility-first neutrality to full geometry, landing on four named families as they go:

**A11y** (0) · **UI** (25) · **Base** (50) · **Geo** (100)

Four typefaces in one axis. In the standard build, compatible letterforms switch cleanly at the boundaries. In **Cal Sans Flex**, they even morph between each other, humanist flowing into geometric mid-slide.

## Tune the rest.

Set the weight, 400 to 700. Raise the ascenders with `YTAS` for taller, airier headlines. Sharpen the corners with `SHRP` for display work. Lean into the real italics, drawn at 9.5°, not slanted by the browser.

The named instances cover one optical size and the four weights per family. Every other axis is a tweak from there. That's deliberate: instances are the starting points, the axes are the range.

Full axis documentation lives in [fonts/README](fonts/README.md).

## Pick your cut.

Every release is a different cut of the same source, sorted and ready in [`fonts/`](fonts/):

| Cut | What it is |
|-----|------------|
| **calsans-var-full** | Every axis. One file. The default choice. |
| **calsans-var-flex** | Cal Sans, morphing. Letterforms blend along `GEOM` instead of switching. The first finished family to ship HOI in the open. |
| **calsans-cossui** | The lean product build. Alternates subset out, italics style-linked, and `opsz` re-tuned to peak at 32 pt so headlines hit harder, sooner. Made for Cal.com, ready for Framer. |
| **calsans-static-essentials** | Two families, sixteen fonts, zero decisions. Start here. |

The full catalog (384 static styles, per-family subsets, Google Fonts packages) is in [fonts/README](fonts/README.md).

## Build it yourself.

```bash
python3 -m scripts
```

One command runs **calBuild**, a compiler built for this typeface alone. Using Cal Sans takes one line. Building it takes one command.

**Cal Sans VF.** The complete variable font, interpolated from the master drawings. calBuild starts by measuring the drawings themselves, taking true stem readings from the letters before a single style is compiled, then lifts the lowercase accents into the room taller ascenders create.

**Cal Sans Flex.** The morphing build. Powered by avar2, the axes coordinate on their own: shrink the size and the ascenders rise to meet it, for fine print that reads like it was set by hand. And a new HOI interpolation engine moves every point along curves instead of straight lines, so letterforms bend through the geometry as if redrawn, never recalculated.

**Cal Sans Statics.** All 384, cut from the variable font with the right letterforms already inside, ready for every platform that has never heard of an axis.

Setup, flags, and troubleshooting are in the [build README](scripts/README.md).

Copyright (c) 2026, Mark Davis mark@wordmark.nyc, with typefaces "Cal Sans," "Cal Sans UI," "Cal Sans A11y," and "Cal Sans Geo." Commissioned by Peer Richelsen for Cal.com. This Font Software is licensed under the SIL Open Font License, Version 1.1, available with a FAQ at: https://openfontlicense.org

## License

This Font Software is licensed under the [SIL Open Font License, Version 1.1](https://github.com/calcom/sans/blob/main/OFL.txt).
The full license lives in [OFL.txt](https://github.com/calcom/sans/blob/main/OFL.txt), and is also available with a FAQ at <https://openfontlicense.org>

## Repository Layout

This font repository structure is inspired by [Unified Font Repository](https://github.com/googlefonts/Unified-Font-Repository), modified for the Google Fonts workflow.
