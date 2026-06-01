Copyright (c) 2026, Mark Davis mark@wordmark.nyc, with typefaces “Cal Sans,” “Cal Sans UI,” “Cal Sans A11y,” and “Cal Sans Geo.” Commissioned by Peer Richelsen for Cal.com. This Font Software is licensed under the SIL Open Font License, Version 1.1. This license is copied below, and is also available with a FAQ at: https://openfontlicense.org

<!-- markdownlint-disable MD033 MD036 MD041 -->

# Cal Sans v1.900

[![npm](https://badgen.net/npm/v/cal-sans)](https://www.npmjs.com/package/cal-sans)
[![packagephobia/install](https://badgen.net/packagephobia/install/cal-sans)](https://www.npmjs.com/package/cal-sans)
[![packagephobia/publish](https://badgen.net/packagephobia/publish/cal-sans)](https://www.npmjs.com/package/cal-sans)
[![interactive showcase](documentation/images/isite.svg)](https://cal.com/font)


Cal Sans (v2.000) is an open-source variable font purpose-built for both product design and brand — a single file that spans fine-print UI at 8 pt through large display headlines, adapting its proportions, spacing, and geometry at every step. It belongs to the same generation of optically-scaling geometric typefaces as Google Sans Flex, Inter, and Anthropic Sans, the latter a variable Geist fork with a 16–48 pt optical size range. Cal Sans 2 pushes that range further: **8–32 pt**, covering the full stack from dense data UI through hero type with a single `font-optical-sizing: auto` declaration.

![Specimen Example](documentation/images/1_opengraph.png)

Cal Sans is an Open Source typeface designed by [Mark Davis](https://twitter.com/MarkFonts) for [Cal.com](https://cal.com/), founded by [Peer Richelsen](https://twitter.com/peer_rich) and [Bailey Pumfleet](https://twitter.com/BaileyPumfleet), with interface design by [Ciarán Hanrahan](https://twitter.com/CiaranHan). 

---

**Table of contents**

- [Introduction](#introduction)
- [Installation Instructions](#installation-instructions)
  - [Desktop](#desktop)
- [NPM Package](#npm-package)
- [Example Usage](#example-usage)
  - [Recommended: `font-optical-sizing: auto`](#recommended-font-optical-sizing-auto)
  - [Manual `font-variation-settings`](#manual-font-variation-settings)
  - [Next.js 13+](#nextjs-13)
  - [With Tailwind CSS](#with-tailwind-css)
- [Design Philosophy and Unique Characteristics](#design-philosophy-and-unique-characteristics)
- [Variable Axes](#variable-axes)
- [Named Instances](#named-instances)
- [Solved Problems to Feedback Since v1.500](#Solved-Problems-to-Feedback-Since-v1.500)
- [Latin Language Support](#latin-language-support)
- [Special Thanks](#special-thanks)
- [License](#license)
- [Repository Layout](#repository-layout)

---

## Introduction

Cal Sans (v1.000, 2021) was a single static weight built for display — tight, geometric, and intentionally extreme at large sizes. [Cal Sans (UI) v1.500 (2025)](https://github.com/calcom/sans-ui) rebuilt the proportions for product interfaces. Cal Sans 2 fuses both into a single variable font, connected through an optical size axis (`opsz`) that continuously adapts from small UI reading size through large display, covering every context in the Cal.com or anyone using [COSS UI](https://coss.com/ui) type system with one token.

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
  font-variation-settings: "opsz" 8, "GEOM" 25, "wght" 400;
}

/* Sharpen corners for display use */
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

For GEOM, SHRP, and YTAS variants in Tailwind utility classes:

```css
@layer utilities {
  .font-geo    { font-variation-settings: "GEOM" 100; }
  .font-base   { font-variation-settings: "GEOM" 50;  }
  .font-ui     { font-variation-settings: "GEOM" 25;  }
  .font-a11y   { font-variation-settings: "GEOM" 0;   }
  .font-sharp  { font-variation-settings: "SHRP" 100; }
  .font-tall   { font-variation-settings: "YTAS" 800; }

}
```

---

## Design Philosophy and Unique Characteristics

**Display end geometric sans(opsz 20–32).** The original Cal Sans vision: “tight but not touching” geometric headlines. Letters are spaced for large-size use right out of the box. The proportions are pure, circular, and close to Futura in spirit. At this end of the optical size axis, positive letter-spacing should be applied as size decreases. We relegated any v1.000 Sharp parts to `SHRP` or extending ascenders to `YTAS`.

**UI and text end neo-grotesque (opsz 8–14).** Proportions are re-optimized: x-heights lower (improving sentence-shape legibility around capitals), circular characters flatten by approximately 7–8% of their width for economy, and built-in sidebearings expand by 40–42 units compared to display end. Minuscule gaps open to blunt stroke joints, and terminals rotate away from counter forms by 8%, all contributing to clarity at small sizes. It remains tighter than comparable Open Source UI fonts by design.

**The optical size axis ties it together.** Cal Sans 2 was [discussed publicly](https://www.reddit.com/r/typography/comments/1lhs7j5/cal_sans_but_with_a_size_axisopen_source_and/) as the long-term direction: a fully responsive single font where optical compensation is built in. That font is this one. Set `font-optical-sizing: auto` in CSS and the browser passes the rendered point size to the font, which then adapts on its own.

**Geometric Form axis (`GEOM`).** A second design axis controls how geometric the letterforms appear independently of size or weight. At `GEOM: 0`, an accessibility-first neutrality takes priority. At `GEOM: 25` (the default), the font behaves as a refined UI face. At `GEOM: 50`, you get the Cal Sans character that has been the brand standard. At `GEOM: 100`, full Futura-esque geometry for maximum display impact.

![Geometry animation](documentation/images/Cal_Sans_UI_GEOM_Variable_axis.gif)

Over 1,300 glyphs, 3,000 kern pairs, and Latin diacritics covering Vietnamese, Marshallese, and more.

![Character set](documentation/images/2_CSUI_charset.png)

![Proportions comparison](documentation/images/3_proportions.png)

The two optical size ends do more than space letters out, the letterforms adapt automatically. Two versions of double-story **a** makes its debut in Cal Sans (v2), essential for disambiguation in numeral/letter mixed environments at small UI sizes, while the geometric single-story **a** remains available for brand applications begining at `GEOM: 35` up to `GEOM: 100`.

![Double-story a](documentation/images/2_haveit.png)

![Usage examples](documentation/images/2_CSUI_examples.png)

## Variable Axes

| Axis              | Tag    | Range     | Default | Description                                                                         |
| :---------------- | :----- | :-------- | :------ | :---------------------------------------------------------------------------------- |
| Optical Size      | `opsz` | 8 – 32    | 14      | Adapts spacing, proportion, and detail from<br>**08** pt fine print / UI to<br>**32** pt display     |
| Geometric Form    | `GEOM` | 0 – 100   | 25      | **000** → Accessibility<br>**025** → Neutrality/UI default<br>**050** → Cal Sans brand<br>**100** → Geo    |
| Weight            | `wght` | 400 – 700 | 400     | Regular → Bold                                                                      |
| Ascender Height   | `YTAS` | 720 – 800 | 720     | Adjusts ascenders for metric compatibility or visual preferences, with no impact on line height      |
| Sharp             | `SHRP` | 0 – 100   | 0       | **000** Blunt or<br>**100** Sharp corners and details                                   |

## Named Instances

The following named instances are included as presets across two optical sizes and four GEOM zones:

### Cal Sans ~42px

| Instance      | opsz | GEOM | wght |
| :------------ | :--- | :--- | :--- |
| Regular       | 32   | 50   | 400  |
| Medium        | 32   | 50   | 500  |
| SemiBold      | 32   | 50   | 600  |
| Bold          | 32   | 50   | 700  |
| UI Regular    | 32   | 25   | 400  |
| UI Medium     | 32   | 25   | 500  |
| UI SemiBold   | 32   | 25   | 600  |
| UI Bold       | 32   | 25   | 700  |
| Geo Regular   | 32   | 100  | 400  |
| Geo Medium    | 32   | 100  | 500  |
| Geo SemiBold  | 32   | 100  | 600  |
| Geo Bold      | 32   | 100  | 700  |
| A11y Regular  | 32   | 0    | 400  |
| A11y Medium   | 32   | 0    | 500  |
| A11y SemiBold | 32   | 0    | 600  |
| A11y Bold     | 32   | 0    | 700  |

### Cal Sans Text ~14px

| Instance           | opsz | GEOM | wght |
| :----------------- | :--- | :--- | :--- |
| Text Regular       | 10   | 50   | 400  |
| Text Medium        | 10   | 50   | 500  |
| Text SemiBold      | 10   | 50   | 600  |
| Text Bold          | 10   | 50   | 700  |
| Text UI Regular    | 10   | 25   | 400  |
| Text UI Medium     | 10   | 25   | 500  |
| Text UI SemiBold   | 10   | 25   | 600  |
| Text UI Bold       | 10   | 25   | 700  |
| Text Geo Regular   | 10   | 100  | 400  |
| Text Geo Medium    | 10   | 100  | 500  |
| Text Geo SemiBold  | 10   | 100  | 600  |
| Text Geo Bold      | 10   | 100  | 700  |
| Text A11y Regular  | 10   | 0    | 400  |
| Text A11y Medium   | 10   | 0    | 500  |
| Text A11y SemiBold | 10   | 0    | 600  |
| Text A11y Bold     | 10   | 0    | 700  |

## Solved Problems to Feedback Since v1.500
###[Adding Weights, gh-issue №2](https://github.com/calcom/sans/issues/2)
We have renamed Cal Sans’ original style as Bold as it is quite suitable to be called that. Then, we added Regular, along with two weights between, many fine-tunable styles between these for one-off project titles or size-specific needs.

###New default: ascenders match cap-height
The modern design system preferred behavior, as most text is short and can pop into display from time to time, is for the capital height glyphs to match vertically with tall lowercase, or ascending glyphs.

Instead of placing the original height ascenders in stylistic sets, we have added a [Parametric Ascender Height axis (YTAS)](https://fonts.google.com/knowledge/glossary/ytas_axis) so designers can choose the height they want. Use `YTAS: 750` to match build v1.500 or wire YTAS and opsz together with avar2 to change the ascenders as type size reaches 8pt. We built an experimental font called Cal Sans Magic that link these axes as a preset, and change the default YTAS height for apps that respect variable fonts.

###New default: blunt corners
Shipping without parametric axes, Cal Sans (v1.000 and v1.500) tried to strike a balance between Futura’s sharp corner details (< > ≤ ≥ ẞ Z z 2 4 5 7) that truly cost some visibility. Then, by adding a `SHRP` axis, we were able add consistency across *more* glyphs <>≤≥ (v w y z A M N V W Z ẞ 2 4 5 7) and control through size-specific variation in sharpness. User-level control of how sharp the details are felt like the way to go.

###Customary cap- and x-height
We used metrics from v1.000 that caused details of the font to feel comparatively small to other typefaces, we also learned since shipping v1.500 it isn’t standard to make adjustments to a production type scale. Our many revisions (1.600) since was “enbiggening” the caps proportionally by 3% and the lowercase by 5%. [We also raised the vertical metrics](https://github.com/calcom/sans-ui/issues/8).

###Confusing character shapes

Google fonts doesnt like "mode" or sliders that are only toggles

###Better multilingual support
Typified by [GH Issue №12](https://github.com/calcom/sans/issues/12) we have improved the display of  

## Latin Language Support

Afrikaans • Albanian • Asturian • Asu • Azerbaijani • Basque • Bemba • Bena • Bosnian • Breton • Catalan • Cebuano • Chiga • Colognian • Cornish • Corsican • Croatian • Czech • Danish • Embu • English • Esperanto • Estonian • Faroese • Filipino • Finnish • French • Friulian • Galician • Ganda • German • Gusii • Haitian Creole • Hawaiian • Hungarian • Icelandic • Ido • Igbo • Inari Sami • Indonesian • Interlingua • Irish • Italian • Javanese • Jju • Jola-Fonyi • Kabuverdianu • Kalaallisut • Kalenjin • Kamba • Kikuyu • Kinyarwanda • Latvian • Lithuanian • Lojban • Lower Sorbian • Luo • Luxembourgish • Luyia • Machame • Makhuwa-Meetto • Makonde • Malagasy • Malay • Maltese • Manx • Māori • Mapuche • Marshalleese • Meru • Mohawk • Morisyen • Mvskoke • North Ndebele • North Sámi • Northern Sotho • Norwegian Bokmål • Norwegian Nynorsk • Nyanja • Nyankole • Occitan • Oromo • Pite Sámi • Polish • Portuguese • Quechua • Romanian • Romansh • Rombo • Rundi • Rwa • Samburu • Samoan • Sango • Sangu • Sardinian • Scottish Gaelic • Sena • Serbian • Shambala • Shona • Sicilian • Slovak • Slovenian • Soga • Somali • South Ndebele • Southern Sotho • Spanish • Sundanese • Swahili • Swati • Swedish • Swiss German • Taita • Taroko • Teso • Tongan • Tsonga • Tswana • Turkish • Turkmen • Ume Sámi • Upper Sorbian • Uzbek • Vietnamese • Vunjo • Walloon • Welsh • Wolastoqey • Wolof • Xhosa • Zulu

## Special Thanks

Thank you to Peer for commissioning this project from the start, and for [Maxim Leyzerovich](https://twitter.com/round) for the original recommendation. Bold Monday’s Futura Today remains a design I love and a quiet reference. Thanks to Wei Huang for his Open Source “Perfect Glyphs Example File” that is [Work Sans dot glyphs](https://github.com/weiweihuanghuang/Work-Sans/blob/master/sources/WorkSans.glyphs) — incredibly helpful, and exhibits genius.

The following people were invaluable to this project, in no specific order, with an undisclosed amount of personal (or impersonal) influence:

- Stephen “Thunder” Nixon
- Luke Shuman
- Paul Renner
- Roger Black, David Berlow, Tobias Frere-Jones, Matthew Carter, Jonathan Hoefler, Kris Sowersby
- Troy Leinster, David Jonathan Ross, Hannes Famira, Cara Di Edwardo, Andy Clymer, Thomas Jockin
- Doriel Jacov, Jamaal Nelson
- [ArrowType’s Type-x Chrome Extension](https://github.com/arrowtype/type-x)
- Eva Roa, ᴡᴏʀᴅᴍᴀʀᴋ COO and resident Python expert and evaGPT terminal; Doriel Jacov
- Cal Sans is my baby, all the more grateful to my parents Scott & Lori Davis

## License

This Font Software is licensed under the [SIL Open Font License, Version 1.1](https://github.com/calcom/sans/blob/main/OFL.txt).
This license is copied below, and is also available with a FAQ at <https://openfontlicense.org>

## Repository Layout

This font repository structure is inspired by [Unified Font Repository](https://github.com/googlefonts/Unified-Font-Repository), modified for the Google Fonts workflow.
