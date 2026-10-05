# Cal Sans Variable and Static Fonts, vX.XXX

> “This Font Software is licensed under the SIL Open Font License, Version 1.1.”

This folder holds the finished, ready-to-ship Cal Sans releases. Every package
here is generated from a single hand-drawn source by the build pipeline (see the
repo [README](../README.md)); the folders below are
just different cuts of the same font for different jobs. **This whole directory is wiped and regenerated on every build** — don’t hand-edit anything in it. That includes this README: it is generated from the template [`scripts/lib/fonts_README.md`](../scripts/lib/fonts_README.md), with the version stamped from the built font, and its pictures are drawn from the fonts by [`scripts/lib/docsheets.py`](../scripts/lib/docsheets.py). Edit those instead.

## Which folder do I want?

If you’re not sure, take **`calsans-var-full/`** — it’s the complete variable font.

### Variable fonts (one file, every style inside)

| Folder | File | What it is |
|--------|------|------------|
| **`calsans-var-full`** | `CalSansVF` | The complete variable font — all six axes exposed (`opsz`, `GEOM`, `wght`, `YTAS`, `SHRP`, `ital`). The default choice for most uses. See [Variable axes](#variable-axes). |
| **`calsans-var-flex`** | `CalSansFlexVF` + `CalSansPhlexVF` | The morphing variable fonts (`.ttf` and `.woff2`). Along the `GEOM` axis compatible letterforms *blend* between forms instead of flipping, and `avar2` lengthens tall ascenders at small optical sizes (`YTAS` is hidden and follows `opsz`). Two builds of the same idea:<br>**Cal Sans Flex** — true higher-order interpolation (HOI). HOI fonts require multiple hidden `avar2` axes: the blends ride three hidden helper axes (`GE1M`, `GE2M`, `GE3M`) that `avar2` drives from `GEOM`, and their products are what let letters follow curved paths (one axis only moves in straight lines). Nothing morphs on `GEOM` alone. The regular form swaps are kept, and each swapped-in alternate carries the blend, so with `avar2` the swap is invisible; renderers without `avar2` show every drawn form, swapping at the stock thresholds. Covers y, λ, j, f, t, M, C, c, 6/9, a, l, I and their accented forms; `a.alt`, the `ss` alternates, `fl.ss14` and `f_f_l.ss14` stay static.<br>**Cal Sans Phlex** — a phony Flex, hence the name: it fakes the curved paths with piecewise interpolation. The blends ride `GEOM` directly as many intermediate (brace) masters, and the form swaps they replace are removed. It morphs anywhere variations work, but a renderer that applies GSUB without the outline variations sees only the default forms where swaps were removed. |
| **`calsans-cossui`** | `CalSansVF` + `CalSansVF-Italic` | The full variable font after removing stylistic-set / character-variant features (`ssXX`/`cvXX`/`aalt` glyphs) via subset — the lean [cal.com](http://refer.cal.com/davis), Framer-friendly, and [COSS UI](https://coss.com/ui) build. Delivered as two variable fonts (upright + italic) like `gf-api`, so `font-style: italic` style-links to the real italic instead of a browser-faked slant. The `opsz` axis also peaks at 32pt instead of 45, giving punchier, functional headlines at smaller sizes. Same 8–14pt performance. |
| **`calsans-gf-api`** | `CalSans` + `CalSans-Italic` | The full variable font delivered as two variable fonts (upright + italic) packaged to the Google Fonts spec after removing stylistic-set / character-variant features (`ssXX`/`cvXX`/`aalt` glyphs) via subset out. Same subsetting as `cossui`. The `opsz` axis is relabeled to peak at **48** instead of 45 — the same display drawing, answering to a rounder number. |
| **`calsans-gf-api-textui`** | `CalSansTextUI` + `CalSansTextUI-Italic` | **Cal Sans Text UI** — the second Google Fonts family ([google/fonts#9970](https://github.com/google/fonts/issues/9970)): a small-optical-size variable font with `wght` (400–700) as its only live axis, upright + italic. Baked in: `opsz` 10, `GEOM` 25 (UI), `YTAS` raised to 760, and the curved l (`l.rcltA11y` + its accented family) as the default for I/l differentiation. Same subsetting as `gf-api`. |

<picture>
  <source media="(prefers-color-scheme: dark)" srcset="../documentation/images/fonts-readme/textui-l-dark.svg">
  <img alt="Il1 Illinois in Cal Sans UI Text, with a straight l, and Cal Sans Text UI, with the curved l it ships as its default" src="../documentation/images/fonts-readme/textui-l.svg">
</picture>

<br>

### Static instances (one file per style)

Each `GEOM` family ships in three optical tiers, all with italics: **Cal Sans** (display, 45pt-ready), **Cal Sans Text** (10pt-ready), and **Cal Sans Micro** (8pt-ready).

| Folder | Count | What it is |
|--------|-------|------------|
| **`calsans-static-full`** | 384 | Every static instance, TTF + WOFF2 (sorted into `ttf/` and `woff2/`). |
| **`calsans-static-base`** | 24 | The canonical “Cal Sans” families with uniquely simplified terminals and single-story a. In the v2 variable font, the base family is instanced at `GEOM` (50).|
| **`calsans-static-a11y`** | 24 | The **A11y** static families — accessibility-first neutrality. In the variable font, the A11y family is instanced at `GEOM` (0).|
| **`calsans-static-ui`** | 24 | The **UI** static families — the refined UI face. In the variable font, this UI family is the default, at `GEOM` (25).|
| **`calsans-static-geo`** | 24 | The **Geo** static families — fully geometric, always clean, unmistakable. Respectfully reverent glyphs to Bauhaus design history in character. In the variable font, the Geo family is instanced at `GEOM` (100).|
| **`calsans-static-essentials`** | 16 | A curated minimal set in two families: 32pt-ready **Cal Sans**, along with 10pt-ready **Cal Sans Text UI**, all with their italics. TTF-only. |
| **`calsans-gf-workspace`** | 16 | The same two families as `static-essentials`, deployed without `opsz`-axis awareness for the Google Fonts workspace, TTF-only — but the **Cal Sans Text UI** half is instanced at the `gf-api-textui` position (`YTAS` 760, curved l default) rather than copied from the static matrix. |

## Display, Text or Micro?

Each static family comes in three optical tiers, and they differ in spacing and proportion, not in height. Cap height, ascender and descender are the same in all three; only the x-height moves, by under a percent (a little more at Bold). What the small tiers add is room: Text sets about 15% wider than Display and Micro about 18%, so letters stay apart at small sizes.

Use the tier made for the size you set it at: **Micro** below 10px, **Text** from 10px to about 20px (body copy, prices, reviews, labels), **Display** — the family with no tier in its name — from about 24px (headlines). The variable fonts make this choice for you along `opsz`.

<picture>
  <source media="(prefers-color-scheme: dark)" srcset="../documentation/images/fonts-readme/tiers-dark.svg">
  <img alt="Cal v2 in Cal Sans UI, Cal Sans UI Text and Cal Sans UI Micro at one size: the smaller tiers set wider" src="../documentation/images/fonts-readme/tiers.svg">
</picture>

<br>

<picture>
  <source media="(prefers-color-scheme: dark)" srcset="../documentation/images/fonts-readme/metrics-dark.svg">
  <img alt="Hx in every tier, Regular and Bold, overlaid: only the x-height moves, and the small tiers set wider" src="../documentation/images/fonts-readme/metrics.svg">
</picture>

<br>

<picture>
  <source media="(prefers-color-scheme: dark)" srcset="../documentation/images/fonts-readme/waterfall-dark.svg">
  <img alt="Cal Sans UI from 8px to 192px, each size in the tier made for it" src="../documentation/images/fonts-readme/waterfall.svg">
</picture>

<br>

## Variable Axes

| Axis | Tag | Range | Default | Description |
|------|-----|-------|---------|-------------|
| Optical Size | `opsz` | 8 – 45 | 14 | Adapts the design from small UI reading sizes to large display. (`calsans-cossui` relabels this axis to peak at 32 and `calsans-gf-api` at 48 — see their rows above.) |
| Geometric Form | `GEOM` | 0 – 100 | 25 | How geometric the letterforms are, from Humanist and Neo Grotesque glyphs to the fully Geometric:<br/> A11y (0) → UI (25) → Base (50) → Geo (100). |
| Weight | `wght` | 400 – 700 | 400 | Regular, Medium, SemiBold, Bold. |
| Ascender Height | `YTAS` | 720 – 800 | 720 | Ascender and lowercase marks’ height. |
| Sharp | `SHRP` | 0 – 100 | 0 | Corner sharpness for display use, tuned per optical size. |
| Italic | `ital` | 0 – 1 | 0 | Upright to italic (9.5°). |

<picture>
  <source media="(prefers-color-scheme: dark)" srcset="https://raw.githubusercontent.com/calcom/sans/main/documentation/images/svg/GeomAxis-dark.svg">
  <img alt="The GEOM axis from A11y (0) to Geo (100)" src="https://raw.githubusercontent.com/calcom/sans/main/documentation/images/svg/GeomAxis.svg">
</picture>

<br>

### Named instances

The static families combine four `GEOM` zones — **A11y** (0), **UI** (25),
**Base** (50, the brand standard), **Geo** (100) — across four weights
(Regular / Medium / SemiBold / Bold), three optical tiers (**Display** ≈ 45,
**Text** ≈ 10, **Micro** ≈ 8), and upright + italic.

<picture>
  <source media="(prefers-color-scheme: dark)" srcset="../documentation/images/fonts-readme/families-dark.svg">
  <img alt="2160 just Groovy, I’ll Magic in Cal Sans A11y, Cal Sans UI, Cal Sans and Cal Sans Geo" src="../documentation/images/fonts-readme/families.svg">
</picture>

<br>

## Full Static Instance List

All **384** named static instances (vX.XXX) — four `GEOM` families × four weights × three optical tiers (Display ≈ 45, Text ≈ 10, Micro ≈ 8) × upright + italic, across the base, Tall, Sharp, and Tall Sharp variants. Each cell lists the Display / Text / Micro tier.

### Default — optical sizes only

<picture>
  <source media="(prefers-color-scheme: dark)" srcset="../documentation/images/fonts-readme/cuts-default-dark.svg">
  <img alt="Cal Sans in Regular, Medium, SemiBold and Bold, roman and italic" src="../documentation/images/fonts-readme/cuts-default.svg">
</picture>

**Roman**

| Weight | A11y · GEOM 0–10 | UI · GEOM 15–30 | Base (Cal Sans) · GEOM 40–60 | Geo · GEOM 80–100 |
|--------|--------|--------|--------|--------|
| Regular | Cal Sans A11y Regular<br>Cal Sans A11y Text Regular<br>Cal Sans A11y Micro Regular | Cal Sans UI Regular<br>Cal Sans UI Text Regular<br>Cal Sans UI Micro Regular | Cal Sans Regular<br>Cal Sans Text Regular<br>Cal Sans Micro Regular | Cal Sans Geo Regular<br>Cal Sans Geo Text Regular<br>Cal Sans Geo Micro Regular |
| Medium | Cal Sans A11y Medium<br>Cal Sans A11y Text Medium<br>Cal Sans A11y Micro Medium | Cal Sans UI Medium<br>Cal Sans UI Text Medium<br>Cal Sans UI Micro Medium | Cal Sans Medium<br>Cal Sans Text Medium<br>Cal Sans Micro Medium | Cal Sans Geo Medium<br>Cal Sans Geo Text Medium<br>Cal Sans Geo Micro Medium |
| SemiBold | Cal Sans A11y SemiBold<br>Cal Sans A11y Text SemiBold<br>Cal Sans A11y Micro SemiBold | Cal Sans UI SemiBold<br>Cal Sans UI Text SemiBold<br>Cal Sans UI Micro SemiBold | Cal Sans SemiBold<br>Cal Sans Text SemiBold<br>Cal Sans Micro SemiBold | Cal Sans Geo SemiBold<br>Cal Sans Geo Text SemiBold<br>Cal Sans Geo Micro SemiBold |
| Bold | Cal Sans A11y Bold<br>Cal Sans A11y Text Bold<br>Cal Sans A11y Micro Bold | Cal Sans UI Bold<br>Cal Sans UI Text Bold<br>Cal Sans UI Micro Bold | Cal Sans Bold<br>Cal Sans Text Bold<br>Cal Sans Micro Bold | Cal Sans Geo Bold<br>Cal Sans Geo Text Bold<br>Cal Sans Geo Micro Bold |

**Italic**

| Weight | A11y · GEOM 0–10 | UI · GEOM 15–30 | Base (Cal Sans) · GEOM 40–60 | Geo · GEOM 80–100 |
|--------|--------|--------|--------|--------|
| Regular | Cal Sans A11y Italic<br>Cal Sans A11y Text Italic<br>Cal Sans A11y Micro Italic | Cal Sans UI Italic<br>Cal Sans UI Text Italic<br>Cal Sans UI Micro Italic | Cal Sans Italic<br>Cal Sans Text Italic<br>Cal Sans Micro Italic | Cal Sans Geo Italic<br>Cal Sans Geo Text Italic<br>Cal Sans Geo Micro Italic |
| Medium | Cal Sans A11y Medium Italic<br>Cal Sans A11y Text Medium Italic<br>Cal Sans A11y Micro Medium Italic | Cal Sans UI Medium Italic<br>Cal Sans UI Text Medium Italic<br>Cal Sans UI Micro Medium Italic | Cal Sans Medium Italic<br>Cal Sans Text Medium Italic<br>Cal Sans Micro Medium Italic | Cal Sans Geo Medium Italic<br>Cal Sans Geo Text Medium Italic<br>Cal Sans Geo Micro Medium Italic |
| SemiBold | Cal Sans A11y SemiBold Italic<br>Cal Sans A11y Text SemiBold Italic<br>Cal Sans A11y Micro SemiBold Italic | Cal Sans UI SemiBold Italic<br>Cal Sans UI Text SemiBold Italic<br>Cal Sans UI Micro SemiBold Italic | Cal Sans SemiBold Italic<br>Cal Sans Text SemiBold Italic<br>Cal Sans Micro SemiBold Italic | Cal Sans Geo SemiBold Italic<br>Cal Sans Geo Text SemiBold Italic<br>Cal Sans Geo Micro SemiBold Italic |
| Bold | Cal Sans A11y Bold Italic<br>Cal Sans A11y Text Bold Italic<br>Cal Sans A11y Micro Bold Italic | Cal Sans UI Bold Italic<br>Cal Sans UI Text Bold Italic<br>Cal Sans UI Micro Bold Italic | Cal Sans Bold Italic<br>Cal Sans Text Bold Italic<br>Cal Sans Micro Bold Italic | Cal Sans Geo Bold Italic<br>Cal Sans Geo Text Bold Italic<br>Cal Sans Geo Micro Bold Italic |

### Tall — `YTAS` 800

<picture>
  <source media="(prefers-color-scheme: dark)" srcset="../documentation/images/fonts-readme/cuts-tall-dark.svg">
  <img alt="Cal Sans Tall in Regular, Medium, SemiBold and Bold, roman and italic" src="../documentation/images/fonts-readme/cuts-tall.svg">
</picture>

**Roman**

| Weight | A11y · GEOM 0–10 | UI · GEOM 15–30 | Base (Cal Sans) · GEOM 40–60 | Geo · GEOM 80–100 |
|--------|--------|--------|--------|--------|
| Regular | Cal Sans A11y Tall Regular<br>Cal Sans A11y Tall Text Regular<br>Cal Sans A11y Tall Micro Regular | Cal Sans UI Tall Regular<br>Cal Sans UI Tall Text Regular<br>Cal Sans UI Tall Micro Regular | Cal Sans Tall Regular<br>Cal Sans Tall Text Regular<br>Cal Sans Tall Micro Regular | Cal Sans Geo Tall Regular<br>Cal Sans Geo Tall Text Regular<br>Cal Sans Geo Tall Micro Regular |
| Medium | Cal Sans A11y Tall Medium<br>Cal Sans A11y Tall Text Medium<br>Cal Sans A11y Tall Micro Medium | Cal Sans UI Tall Medium<br>Cal Sans UI Tall Text Medium<br>Cal Sans UI Tall Micro Medium | Cal Sans Tall Medium<br>Cal Sans Tall Text Medium<br>Cal Sans Tall Micro Medium | Cal Sans Geo Tall Medium<br>Cal Sans Geo Tall Text Medium<br>Cal Sans Geo Tall Micro Medium |
| SemiBold | Cal Sans A11y Tall SemiBold<br>Cal Sans A11y Tall Text SemiBold<br>Cal Sans A11y Tall Micro SemiBold | Cal Sans UI Tall SemiBold<br>Cal Sans UI Tall Text SemiBold<br>Cal Sans UI Tall Micro SemiBold | Cal Sans Tall SemiBold<br>Cal Sans Tall Text SemiBold<br>Cal Sans Tall Micro SemiBold | Cal Sans Geo Tall SemiBold<br>Cal Sans Geo Tall Text SemiBold<br>Cal Sans Geo Tall Micro SemiBold |
| Bold | Cal Sans A11y Tall Bold<br>Cal Sans A11y Tall Text Bold<br>Cal Sans A11y Tall Micro Bold | Cal Sans UI Tall Bold<br>Cal Sans UI Tall Text Bold<br>Cal Sans UI Tall Micro Bold | Cal Sans Tall Bold<br>Cal Sans Tall Text Bold<br>Cal Sans Tall Micro Bold | Cal Sans Geo Tall Bold<br>Cal Sans Geo Tall Text Bold<br>Cal Sans Geo Tall Micro Bold |

**Italic**

| Weight | A11y · GEOM 0–10 | UI · GEOM 15–30 | Base (Cal Sans) · GEOM 40–60 | Geo · GEOM 80–100 |
|--------|--------|--------|--------|--------|
| Regular | Cal Sans A11y Tall Italic<br>Cal Sans A11y Tall Text Italic<br>Cal Sans A11y Tall Micro Italic | Cal Sans UI Tall Italic<br>Cal Sans UI Tall Text Italic<br>Cal Sans UI Tall Micro Italic | Cal Sans Tall Italic<br>Cal Sans Tall Text Italic<br>Cal Sans Tall Micro Italic | Cal Sans Geo Tall Italic<br>Cal Sans Geo Tall Text Italic<br>Cal Sans Geo Tall Micro Italic |
| Medium | Cal Sans A11y Tall Medium Italic<br>Cal Sans A11y Tall Text Medium Italic<br>Cal Sans A11y Tall Micro Medium Italic | Cal Sans UI Tall Medium Italic<br>Cal Sans UI Tall Text Medium Italic<br>Cal Sans UI Tall Micro Medium Italic | Cal Sans Tall Medium Italic<br>Cal Sans Tall Text Medium Italic<br>Cal Sans Tall Micro Medium Italic | Cal Sans Geo Tall Medium Italic<br>Cal Sans Geo Tall Text Medium Italic<br>Cal Sans Geo Tall Micro Medium Italic |
| SemiBold | Cal Sans A11y Tall SemiBold Italic<br>Cal Sans A11y Tall Text SemiBold Italic<br>Cal Sans A11y Tall Micro SemiBold Italic | Cal Sans UI Tall SemiBold Italic<br>Cal Sans UI Tall Text SemiBold Italic<br>Cal Sans UI Tall Micro SemiBold Italic | Cal Sans Tall SemiBold Italic<br>Cal Sans Tall Text SemiBold Italic<br>Cal Sans Tall Micro SemiBold Italic | Cal Sans Geo Tall SemiBold Italic<br>Cal Sans Geo Tall Text SemiBold Italic<br>Cal Sans Geo Tall Micro SemiBold Italic |
| Bold | Cal Sans A11y Tall Bold Italic<br>Cal Sans A11y Tall Text Bold Italic<br>Cal Sans A11y Tall Micro Bold Italic | Cal Sans UI Tall Bold Italic<br>Cal Sans UI Tall Text Bold Italic<br>Cal Sans UI Tall Micro Bold Italic | Cal Sans Tall Bold Italic<br>Cal Sans Tall Text Bold Italic<br>Cal Sans Tall Micro Bold Italic | Cal Sans Geo Tall Bold Italic<br>Cal Sans Geo Tall Text Bold Italic<br>Cal Sans Geo Tall Micro Bold Italic |

### Sharp — `SHRP` 100

<picture>
  <source media="(prefers-color-scheme: dark)" srcset="https://raw.githubusercontent.com/calcom/sans/main/documentation/images/svg/geometry-mach-5-dark.svg">
  <img alt="Mach 5 across GEOM, SHRP and optical size" src="https://raw.githubusercontent.com/calcom/sans/main/documentation/images/svg/geometry-mach-5.svg">
</picture>

<br>

<picture>
  <source media="(prefers-color-scheme: dark)" srcset="../documentation/images/fonts-readme/cuts-sharp-dark.svg">
  <img alt="Cal Sans Sharp in Regular, Medium, SemiBold and Bold, roman and italic" src="../documentation/images/fonts-readme/cuts-sharp.svg">
</picture>

**Roman**

| Weight | A11y · GEOM 0–10 | UI · GEOM 15–30 | Base (Cal Sans) · GEOM 40–60 | Geo · GEOM 80–100 |
|--------|--------|--------|--------|--------|
| Regular | Cal Sans A11y Sharp Regular<br>Cal Sans A11y Sharp Text Regular<br>Cal Sans A11y Sharp Micro Regular | Cal Sans UI Sharp Regular<br>Cal Sans UI Sharp Text Regular<br>Cal Sans UI Sharp Micro Regular | Cal Sans Sharp Regular<br>Cal Sans Sharp Text Regular<br>Cal Sans Sharp Micro Regular | Cal Sans Geo Sharp Regular<br>Cal Sans Geo Sharp Text Regular<br>Cal Sans Geo Sharp Micro Regular |
| Medium | Cal Sans A11y Sharp Medium<br>Cal Sans A11y Sharp Text Medium<br>Cal Sans A11y Sharp Micro Medium | Cal Sans UI Sharp Medium<br>Cal Sans UI Sharp Text Medium<br>Cal Sans UI Sharp Micro Medium | Cal Sans Sharp Medium<br>Cal Sans Sharp Text Medium<br>Cal Sans Sharp Micro Medium | Cal Sans Geo Sharp Medium<br>Cal Sans Geo Sharp Text Medium<br>Cal Sans Geo Sharp Micro Medium |
| SemiBold | Cal Sans A11y Sharp SemiBold<br>Cal Sans A11y Sharp Text SemiBold<br>Cal Sans A11y Sharp Micro SemiBold | Cal Sans UI Sharp SemiBold<br>Cal Sans UI Sharp Text SemiBold<br>Cal Sans UI Sharp Micro SemiBold | Cal Sans Sharp SemiBold<br>Cal Sans Sharp Text SemiBold<br>Cal Sans Sharp Micro SemiBold | Cal Sans Geo Sharp SemiBold<br>Cal Sans Geo Sharp Text SemiBold<br>Cal Sans Geo Sharp Micro SemiBold |
| Bold | Cal Sans A11y Sharp Bold<br>Cal Sans A11y Sharp Text Bold<br>Cal Sans A11y Sharp Micro Bold | Cal Sans UI Sharp Bold<br>Cal Sans UI Sharp Text Bold<br>Cal Sans UI Sharp Micro Bold | Cal Sans Sharp Bold<br>Cal Sans Sharp Text Bold<br>Cal Sans Sharp Micro Bold | Cal Sans Geo Sharp Bold<br>Cal Sans Geo Sharp Text Bold<br>Cal Sans Geo Sharp Micro Bold |

**Italic**

| Weight | A11y · GEOM 0–10 | UI · GEOM 15–30 | Base (Cal Sans) · GEOM 40–60 | Geo · GEOM 80–100 |
|--------|--------|--------|--------|--------|
| Regular | Cal Sans A11y Sharp Italic<br>Cal Sans A11y Sharp Text Italic<br>Cal Sans A11y Sharp Micro Italic | Cal Sans UI Sharp Italic<br>Cal Sans UI Sharp Text Italic<br>Cal Sans UI Sharp Micro Italic | Cal Sans Sharp Italic<br>Cal Sans Sharp Text Italic<br>Cal Sans Sharp Micro Italic | Cal Sans Geo Sharp Italic<br>Cal Sans Geo Sharp Text Italic<br>Cal Sans Geo Sharp Micro Italic |
| Medium | Cal Sans A11y Sharp Medium Italic<br>Cal Sans A11y Sharp Text Medium Italic<br>Cal Sans A11y Sharp Micro Medium Italic | Cal Sans UI Sharp Medium Italic<br>Cal Sans UI Sharp Text Medium Italic<br>Cal Sans UI Sharp Micro Medium Italic | Cal Sans Sharp Medium Italic<br>Cal Sans Sharp Text Medium Italic<br>Cal Sans Sharp Micro Medium Italic | Cal Sans Geo Sharp Medium Italic<br>Cal Sans Geo Sharp Text Medium Italic<br>Cal Sans Geo Sharp Micro Medium Italic |
| SemiBold | Cal Sans A11y Sharp SemiBold Italic<br>Cal Sans A11y Sharp Text SemiBold Italic<br>Cal Sans A11y Sharp Micro SemiBold Italic | Cal Sans UI Sharp SemiBold Italic<br>Cal Sans UI Sharp Text SemiBold Italic<br>Cal Sans UI Sharp Micro SemiBold Italic | Cal Sans Sharp SemiBold Italic<br>Cal Sans Sharp Text SemiBold Italic<br>Cal Sans Sharp Micro SemiBold Italic | Cal Sans Geo Sharp SemiBold Italic<br>Cal Sans Geo Sharp Text SemiBold Italic<br>Cal Sans Geo Sharp Micro SemiBold Italic |
| Bold | Cal Sans A11y Sharp Bold Italic<br>Cal Sans A11y Sharp Text Bold Italic<br>Cal Sans A11y Sharp Micro Bold Italic | Cal Sans UI Sharp Bold Italic<br>Cal Sans UI Sharp Text Bold Italic<br>Cal Sans UI Sharp Micro Bold Italic | Cal Sans Sharp Bold Italic<br>Cal Sans Sharp Text Bold Italic<br>Cal Sans Sharp Micro Bold Italic | Cal Sans Geo Sharp Bold Italic<br>Cal Sans Geo Sharp Text Bold Italic<br>Cal Sans Geo Sharp Micro Bold Italic |

### Tall Sharp — `YTAS` 800 + `SHRP` 100

<picture>
  <source media="(prefers-color-scheme: dark)" srcset="../documentation/images/fonts-readme/cuts-tall-sharp-dark.svg">
  <img alt="Cal Sans Tall Sharp in Regular, Medium, SemiBold and Bold, roman and italic" src="../documentation/images/fonts-readme/cuts-tall-sharp.svg">
</picture>

**Roman**

| Weight | A11y · GEOM 0–10 | UI · GEOM 15–30 | Base (Cal Sans) · GEOM 40–60 | Geo · GEOM 80–100 |
|--------|--------|--------|--------|--------|
| Regular | Cal Sans A11y Tall Sharp Regular<br>Cal Sans A11y Tall Sharp Text Regular<br>Cal Sans A11y Tall Sharp Micro Regular | Cal Sans UI Tall Sharp Regular<br>Cal Sans UI Tall Sharp Text Regular<br>Cal Sans UI Tall Sharp Micro Regular | Cal Sans Tall Sharp Regular<br>Cal Sans Tall Sharp Text Regular<br>Cal Sans Tall Sharp Micro Regular | Cal Sans Geo Tall Sharp Regular<br>Cal Sans Geo Tall Sharp Text Regular<br>Cal Sans Geo Tall Sharp Micro Regular |
| Medium | Cal Sans A11y Tall Sharp Medium<br>Cal Sans A11y Tall Sharp Text Medium<br>Cal Sans A11y Tall Sharp Micro Medium | Cal Sans UI Tall Sharp Medium<br>Cal Sans UI Tall Sharp Text Medium<br>Cal Sans UI Tall Sharp Micro Medium | Cal Sans Tall Sharp Medium<br>Cal Sans Tall Sharp Text Medium<br>Cal Sans Tall Sharp Micro Medium | Cal Sans Geo Tall Sharp Medium<br>Cal Sans Geo Tall Sharp Text Medium<br>Cal Sans Geo Tall Sharp Micro Medium |
| SemiBold | Cal Sans A11y Tall Sharp SemiBold<br>Cal Sans A11y Tall Sharp Text SemiBold<br>Cal Sans A11y Tall Sharp Micro SemiBold | Cal Sans UI Tall Sharp SemiBold<br>Cal Sans UI Tall Sharp Text SemiBold<br>Cal Sans UI Tall Sharp Micro SemiBold | Cal Sans Tall Sharp SemiBold<br>Cal Sans Tall Sharp Text SemiBold<br>Cal Sans Tall Sharp Micro SemiBold | Cal Sans Geo Tall Sharp SemiBold<br>Cal Sans Geo Tall Sharp Text SemiBold<br>Cal Sans Geo Tall Sharp Micro SemiBold |
| Bold | Cal Sans A11y Tall Sharp Bold<br>Cal Sans A11y Tall Sharp Text Bold<br>Cal Sans A11y Tall Sharp Micro Bold | Cal Sans UI Tall Sharp Bold<br>Cal Sans UI Tall Sharp Text Bold<br>Cal Sans UI Tall Sharp Micro Bold | Cal Sans Tall Sharp Bold<br>Cal Sans Tall Sharp Text Bold<br>Cal Sans Tall Sharp Micro Bold | Cal Sans Geo Tall Sharp Bold<br>Cal Sans Geo Tall Sharp Text Bold<br>Cal Sans Geo Tall Sharp Micro Bold |

**Italic**

| Weight | A11y · GEOM 0–10 | UI · GEOM 15–30 | Base (Cal Sans) · GEOM 40–60 | Geo · GEOM 80–100 |
|--------|--------|--------|--------|--------|
| Regular | Cal Sans A11y Tall Sharp Italic<br>Cal Sans A11y Tall Sharp Text Italic<br>Cal Sans A11y Tall Sharp Micro Italic | Cal Sans UI Tall Sharp Italic<br>Cal Sans UI Tall Sharp Text Italic<br>Cal Sans UI Tall Sharp Micro Italic | Cal Sans Tall Sharp Italic<br>Cal Sans Tall Sharp Text Italic<br>Cal Sans Tall Sharp Micro Italic | Cal Sans Geo Tall Sharp Italic<br>Cal Sans Geo Tall Sharp Text Italic<br>Cal Sans Geo Tall Sharp Micro Italic |
| Medium | Cal Sans A11y Tall Sharp Medium Italic<br>Cal Sans A11y Tall Sharp Text Medium Italic<br>Cal Sans A11y Tall Sharp Micro Medium Italic | Cal Sans UI Tall Sharp Medium Italic<br>Cal Sans UI Tall Sharp Text Medium Italic<br>Cal Sans UI Tall Sharp Micro Medium Italic | Cal Sans Tall Sharp Medium Italic<br>Cal Sans Tall Sharp Text Medium Italic<br>Cal Sans Tall Sharp Micro Medium Italic | Cal Sans Geo Tall Sharp Medium Italic<br>Cal Sans Geo Tall Sharp Text Medium Italic<br>Cal Sans Geo Tall Sharp Micro Medium Italic |
| SemiBold | Cal Sans A11y Tall Sharp SemiBold Italic<br>Cal Sans A11y Tall Sharp Text SemiBold Italic<br>Cal Sans A11y Tall Sharp Micro SemiBold Italic | Cal Sans UI Tall Sharp SemiBold Italic<br>Cal Sans UI Tall Sharp Text SemiBold Italic<br>Cal Sans UI Tall Sharp Micro SemiBold Italic | Cal Sans Tall Sharp SemiBold Italic<br>Cal Sans Tall Sharp Text SemiBold Italic<br>Cal Sans Tall Sharp Micro SemiBold Italic | Cal Sans Geo Tall Sharp SemiBold Italic<br>Cal Sans Geo Tall Sharp Text SemiBold Italic<br>Cal Sans Geo Tall Sharp Micro SemiBold Italic |
| Bold | Cal Sans A11y Tall Sharp Bold Italic<br>Cal Sans A11y Tall Sharp Text Bold Italic<br>Cal Sans A11y Tall Sharp Micro Bold Italic | Cal Sans UI Tall Sharp Bold Italic<br>Cal Sans UI Tall Sharp Text Bold Italic<br>Cal Sans UI Tall Sharp Micro Bold Italic | Cal Sans Tall Sharp Bold Italic<br>Cal Sans Tall Sharp Text Bold Italic<br>Cal Sans Tall Sharp Micro Bold Italic | Cal Sans Geo Tall Sharp Bold Italic<br>Cal Sans Geo Tall Sharp Text Bold Italic<br>Cal Sans Geo Tall Sharp Micro Bold Italic |
