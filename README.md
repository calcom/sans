Copyright (c) 2026, Mark Davis mark@designermarkdavis.com, with Font "Cal Sans". Commissioned by Peer Richelsen for Cal.com. This Font Software is licensed under the SIL Open Font License, Version 1.1. This license is copied below, and is also available with a FAQ at: https://openfontlicense.org

<!-- markdownlint-disable MD033 MD036 MD041 -->

# Cal Sans 2.000

[![npm](https://badgen.net/npm/v/cal-sans)](https://www.npmjs.com/package/cal-sans)
[![packagephobia/install](https://badgen.net/packagephobia/install/cal-sans)](https://www.npmjs.com/package/cal-sans)
[![packagephobia/publish](https://badgen.net/packagephobia/publish/cal-sans)](https://www.npmjs.com/package/cal-sans)

Geometric sans-serif variable font for every size of Cal.com — display headlines, subheadings, UI, and fine print — in a single file.

---

**Table of contents**

- [Introduction](#introduction)
- [Design Philosophy and Unique Characteristics](#design-philosophy-and-unique-characteristics)
- [Variable Axes](#variable-axes)
- [Named Instances](#named-instances)
- [OpenType Features](#opentype-features)
- [Installation Instructions](#installation-instructions)
  - [Desktop](#desktop)
- [NPM Package](#npm-package)
- [Example Usage](#example-usage)
  - [Recommended: `font-optical-sizing: auto`](#recommended-font-optical-sizing-auto)
  - [Manual `font-variation-settings`](#manual-font-variation-settings)
  - [Next.js 13+](#nextjs-13)
  - [With Tailwind CSS](#with-tailwind-css)
- [Special Thanks](#special-thanks)
- [License](#license)
- [Repository Layout](#repository-layout)

---

## Introduction

Cal Sans is a geometric sans-serif Open Source typeface for [Cal.com](https://cal.com/), a company founded by [Peer Richelsen](https://twitter.com/peer_rich) and [Bailey Pumfleet](https://twitter.com/BaileyPumfleet), with interface design by [Ciarán Hanrahan](https://twitter.com/CiaranHan). Designed by [Mark Davis](https://twitter.com/MarkFonts).

Version 2 is a single variable font that replaces the need for separate display and UI families. Whether you are typesetting a large hero headline, a 14 px UI label, or fine print at 8 px, one file handles everything — and adapts automatically when you use `font-optical-sizing: auto`.

![Specimen Example](/documentation/images/1_opengraph.png)

The design lineage: Cal Sans 1.0 (2021) was built strictly for display — tight, geometric, and intentionally extreme. The companion release Cal Sans UI (2025) rebuilt proportions for UI and text use. Cal Sans 2 fuses both, connecting them through an optical size axis (`opsz`) so that the font continuously transitions from UI reading size through display, letting the same type system cover every context in a single token.

## Design Philosophy and Unique Characteristics

**Display end (opsz 20–32).** The original Cal Sans vision: "tight but not touching" geometric headlines. Letters are spaced for large-size use right out of the box. The proportions are pure, circular, and close to Futura in spirit. At this end of the optical size axis, positive letter-spacing should be applied as size decreases.

**UI and text end (opsz 8–14).** Proportions are re-optimized: extenders lengthen, x-heights lower (improving sentence-shape legibility around capitals), circular characters flatten by approximately 7–8% of their width for economy, and built-in sidebearings expand by 40–42 units compared to the original design. Minuscule gaps open at stroke joins, and terminals rotate away from counter forms by 8%, all contributing to clarity at small sizes. It remains tighter than comparable Open Source UI fonts by design.

**The optical size axis ties it together.** Cal Sans 2 was [discussed publicly](https://www.reddit.com/r/typography/comments/1lhs7j5/cal_sans_but_with_a_size_axisopen_source_and/) as the long-term direction: a fully responsive single font where optical compensation is built in. That font is this one. Set `font-optical-sizing: auto` in CSS and the browser passes the rendered point size to the font, which then adapts on its own.

**Geometric Form axis (`GEOM`).** A second design axis controls how geometric the letterforms appear independently of size or weight. At GEOM 0, an accessibility-first neutrality takes priority. At GEOM 25 (the default), the font behaves as a refined UI face. At GEOM 50, you get the Cal Sans character that has been the brand standard. At GEOM 100, full Futura-esque geometry for maximum display impact.

![Geometry animation](/documentation/images/4_geometry.gif)

Nearly 1,000 glyphs, 3,000 kern pairs, and Latin diacritics covering Vietnamese, Marshallese, and more.

![Character set](/documentation/images/2_CSUI_charset.png)

![Proportions comparison](/documentation/images/3_proportions.png)

The two optical size poles do not simply scale spacing — the letterforms themselves shift. The double-story **a** makes its debut in Cal Sans 2, essential for disambiguation in numeral/letter mixed environments at small UI sizes, while the geometric single-story **a** remains available via Stylistic Set 01.

![Double-story a](/documentation/images/2_haveit.png)

![Usage examples](/documentation/images/2_CSUI_examples.png)

## Variable Axes

| Axis              | Tag    | Range     | Default | Description                                                                         |
| :---------------- | :----- | :-------- | :------ | :---------------------------------------------------------------------------------- |
| Optical Size      | `opsz` | 8 – 32    | 14      | Adapts spacing, proportion, and detail from fine print / UI (8) to display (32)     |
| Geometric Form    | `GEOM` | 0 – 100   | 25      | Neutrality/accessibility (0) → UI default (25) → Cal Sans brand (50) → Geo (100)   |
| Weight            | `wght` | 400 – 700 | 400     | Regular → Bold                                                                      |
| Ascender Height   | `YTAS` | 720 – 800 | 720     | Adjusts ascender and cap height for metric compatibility or visual preferences      |
| Sharp             | `SHRP` | 0 – 100   | 0       | Softens (0) or sharpens (100) terminals and joins                                   |

## Named Instances

The following named instances are included as presets across two optical sizes and four GEOM levels:

| Instance            | opsz | GEOM | wght |
| :------------------ | :--- | :--- | :--- |
| Regular             | 32   | 50   | 400  |
| Medium              | 32   | 50   | 500  |
| SemiBold            | 32   | 50   | 600  |
| Bold                | 32   | 50   | 700  |
| UI Regular          | 32   | 25   | 400  |
| UI Medium           | 32   | 25   | 500  |
| UI SemiBold         | 32   | 25   | 600  |
| UI Bold             | 32   | 25   | 700  |
| Geo Regular         | 32   | 100  | 400  |
| Geo Medium          | 32   | 100  | 500  |
| Geo SemiBold        | 32   | 100  | 600  |
| Geo Bold            | 32   | 100  | 700  |
| A11y Regular        | 32   | 0    | 400  |
| A11y Medium         | 32   | 0    | 500  |
| A11y SemiBold       | 32   | 0    | 600  |
| A11y Bold           | 32   | 0    | 700  |
| Text Regular        | 10   | 50   | 400  |
| Text Medium         | 10   | 50   | 500  |
| Text SemiBold       | 10   | 50   | 600  |
| Text Bold           | 10   | 50   | 700  |
| Text UI Regular     | 10   | 25   | 400  |
| Text UI Medium      | 10   | 25   | 500  |
| Text UI SemiBold    | 10   | 25   | 600  |
| Text UI Bold        | 10   | 25   | 700  |
| Text Geo Regular    | 10   | 100  | 400  |
| Text Geo Medium     | 10   | 100  | 500  |
| Text Geo SemiBold   | 10   | 100  | 600  |
| Text Geo Bold       | 10   | 100  | 700  |
| Text A11y Regular   | 10   | 0    | 400  |
| Text A11y Medium    | 10   | 0    | 500  |
| Text A11y SemiBold  | 10   | 0    | 600  |
| Text A11y Bold      | 10   | 0    | 700  |

## OpenType Features

**Stylistic Set 01 (ss01) — Futura Alternates.** The default design is ahistorical in certain respects; ss01 activates Futura-specific alternates including diacritic variants — 48 alternates in total.

![A sample of ss01](/documentation/images/blog-specimen_ss01.jpg)

**Stylistic Set 02 (ss02) — Futura Ligatures.** Identical to ss01, but also combines eligible letters as historical Futura ligatures. Included as a stylistic set rather than discretionary ligatures because the default letterforms do not match these historical joins.

![A sample of ss02](/documentation/images/blog-specimen_ss02.jpg)

**Stylistic Set 03 (ss03) — Diagonal Crash Kerning.** The most unusual feature. "Tight but not touching" produces consistent texture, but consecutive diagonals (AV, VA, WA, etc.) receive conservative kerning by default to prevent overlap. ss03 overrides those pairs with new values that let diagonal corners make contact — for designers who prefer rhythmic consistency over separation.

![Open Source Fonts' Default Spacing](/documentation/images/ss03_kerning.gif)

**Character Variants.** Six character variants for fine-grained control, continuing from Cal Sans 1.0:

| Feature | Glyph | Description               |
| :------ | :---- | :------------------------ |
| cv01    | Cc    | Alternate C/c             |
| cv02    | j     | Alternate j               |
| cv03    | t     | Alternate t               |
| cv04    | u     | Alternate u               |
| cv05    | 0     | Alternate zero            |
| cv06    | 1     | Alternate one             |

Thanks to Tal Leming's [OpenType Cook Book](https://opentypecookbook.com/rules/) for technical guidance, and to [Rasmus Andersson](https://twitter.com/rsms) for demonstrating Character Variants in [Inter](https://github.com/rsms/inter).

## Installation Instructions

### Desktop

- [GNU+Linux](https://wiki.archlinux.org/index.php/fonts#Manual_installation)
- [macOS](https://support.apple.com/en-us/HT201749)
- [Windows](https://support.microsoft.com/en-us/help/314960/how-to-install-or-remove-a-font-in-windows)

## NPM Package

```sh
# using npm
npm install cal-sans

# using yarn
yarn add cal-sans
```

## Example Usage

### Recommended: `font-optical-sizing: auto`

The simplest integration. The browser resolves the rendered size and passes it to the `opsz` axis automatically.

```css
html,
body {
  font-family: "Cal Sans", sans-serif;
  font-optical-sizing: auto;
}
```

Because `opsz` handles optical adaptation, letter-spacing adjustments at different sizes are smaller than with Cal Sans 1.0. Still, adding a little positive tracking at intermediate sizes improves texture:

```css
h1 { font-size: 56px; }
h2 { font-size: 40px; letter-spacing: 0.005em; }
h3 { font-size: 32px; letter-spacing: 0.01em; }
h4 { font-size: 24px; letter-spacing: 0.015em; }
h5 { font-size: 20px; letter-spacing: 0.02em; }
h6 { font-size: 16px; letter-spacing: 0.025em; }
p  { font-size: 14px; letter-spacing: 0.01em; }
```

### Manual `font-variation-settings`

For explicit control over every axis:

```css
/* Large display headline — full geometric Cal Sans character */
.hero {
  font-family: "Cal Sans", sans-serif;
  font-variation-settings: "opsz" 32, "GEOM" 50, "wght" 600;
}

/* UI body text — neutral, accessibility-friendly */
.body {
  font-family: "Cal Sans", sans-serif;
  font-variation-settings: "opsz" 14, "GEOM" 25, "wght" 400;
}

/* Fine print */
.caption {
  font-family: "Cal Sans", sans-serif;
  font-variation-settings: "opsz" 8, "GEOM" 0, "wght" 400;
}

/* Sharpen terminals for high-contrast display use */
.display-sharp {
  font-family: "Cal Sans", sans-serif;
  font-variation-settings: "opsz" 32, "GEOM" 50, "wght" 700, "SHRP" 80;
}
```

### Next.js 13+

```tsx
import localFont from "next/font/local";

const calSans = localFont({
  src: "../fonts/CalSans-VariableFont.woff2",
  variable: "--font-cal-sans",
});

export default function RootLayout({ children }) {
  return (
    <html lang="en" className={calSans.variable}>
      <body>{children}</body>
    </html>
  );
}
```

```css
/* globals.css */
body {
  font-family: var(--font-cal-sans), sans-serif;
  font-optical-sizing: auto;
}
```

### With Tailwind CSS

**Tailwind v4** — `tailwind.css`:

```css
@theme {
  --font-sans: var(--font-cal-sans), ui-sans-serif, sans-serif;
}
```

**Tailwind v3** — `tailwind.config.js`:

```js
module.exports = {
  theme: {
    extend: {
      fontFamily: {
        sans: ["var(--font-cal-sans)", "sans-serif"],
      },
    },
  },
};
```

For GEOM and SHRP variants in Tailwind utility classes:

```css
@layer utilities {
  .font-geo    { font-variation-settings: "GEOM" 100; }
  .font-ui     { font-variation-settings: "GEOM" 25; }
  .font-a11y   { font-variation-settings: "GEOM" 0; }
  .font-sharp  { font-variation-settings: "SHRP" 100; }
}
```

## Latin Language Support

Afrikaans • Albanian • Asturian • Asu • Azerbaijani • Basque • Bemba • Bena • Bosnian • Breton • Catalan • Cebuano • Chiga • Colognian • Cornish • Corsican • Croatian • Czech • Danish • Embu • English • Esperanto • Estonian • Faroese • Filipino • Finnish • French • Friulian • Galician • Ganda • German • Gusii • Haitian Creole • Hawaiian • Hungarian • Icelandic • Ido • Igbo • Inari Sami • Indonesian • Interlingua • Irish • Italian • Javanese • Jju • Jola-Fonyi • Kabuverdianu • Kalaallisut • Kalenjin • Kamba • Kikuyu • Kinyarwanda • Latvian • Lithuanian • Lojban • Lower Sorbian • Luo • Luxembourgish • Luyia • Machame • Makhuwa-Meetto • Makonde • Malagasy • Malay • Maltese • Manx • Māori • Mapuche • Marshalleese • Meru • Mohawk • Morisyen • Mvskoke • North Ndebele • North Sámi • Northern Sotho • Norwegian Bokmål • Norwegian Nynorsk • Nyanja • Nyankole • Occitan • Oromo • Pite Sámi • Polish • Portuguese • Quechua • Romanian • Romansh • Rombo • Rundi • Rwa • Samburu • Samoan • Sango • Sangu • Sardinian • Scottish Gaelic • Sena • Serbian • Shambala • Shona • Sicilian • Slovak • Slovenian • Soga • Somali • South Ndebele • Southern Sotho • Spanish • Sundanese • Swahili • Swati • Swedish • Swiss German • Taita • Taroko • Teso • Tongan • Tsonga • Tswana • Turkish • Turkmen • Ume Sámi • Upper Sorbian • Uzbek • Vietnamese • Vunjo • Walloon • Welsh • Wolastoqey • Wolof • Xhosa • Zulu

## Special Thanks

Thank you to Peer for commissioning this project from the start, and for [Maxim Leyzerovich](https://twitter.com/round) for the original recommendation. Bold Monday's Futura Today remains a design I love and a quiet reference. Thanks to Wei Huang for his Open Source "Perfect Glyphs Example File" that is [Work Sans dot glyphs](https://github.com/weiweihuanghuang/Work-Sans/blob/master/sources/WorkSans.glyphs) — incredibly helpful, and exhibits genius.

The following people were invaluable to this project, in no specific order, with an undisclosed amount of personal (or impersonal) influence:

- Mirko Velimirovic & Stephen "Thunder" Nixon
- Luke Shuman
- Paul Renner
- Roger Black, David Berlow, Tobias Frere-Jones, Matthew Carter, Jonathan Hoefler, Kris Sowersby
- Hannes Famira, Cara Di Edwardo, Andy Clymer, David Jonathan Ross, Troy Leinster, Thomas Jockin
- Jamaal Nelson, Florante Generoso, jen hung, Laura Van Wyk
- [ArrowType's Type-x Chrome Extension](https://github.com/arrowtype/type-x)
- Eva Roa, ᴡᴏʀᴅᴍᴀʀᴋ COO and resident Python expert and evaGPT terminal; Doriel Jacov
- As Cal Sans is the fruit of my labor, I am the fruit of Scott & Lori Davis

## License

This Font Software is licensed under the [SIL Open Font License, Version 1.1](https://github.com/calcom/sans/blob/main/OFL.txt).
This license is copied below, and is also available with a FAQ at <https://openfontlicense.org>

## Repository Layout

This font repository structure is inspired by [Unified Font Repository](https://github.com/googlefonts/Unified-Font-Repository), modified for the Google Fonts workflow.
