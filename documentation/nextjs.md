# Using Cal Sans with the Next.js App Router

Cal Sans ships as a single variable font (`CalSansVF.woff2` / `CalSansVF.ttf`), so it works well with
[`next/font/local`](https://nextjs.org/docs/app/building-your-application/optimizing/fonts#local-fonts) —
one font file, self-hosted, no layout shift, no request to Google Fonts at runtime.

## 1. Install

```bash
npm install cal-sans
```

## 2. Copy the variable font into your app

`next/font/local` needs a file path it can bundle, so copy the variable font out of
`node_modules` and into your project once (re-run this after upgrading the package):

```bash
mkdir -p src/assets/fonts
cp node_modules/cal-sans/fonts/calsans-var-full/CalSansVF.woff2 src/assets/fonts/
```

## 3. Load it in `app/layout.tsx`

```tsx
// app/layout.tsx
import localFont from "next/font/local";

const calSans = localFont({
  src: "../src/assets/fonts/CalSansVF.woff2",
  variable: "--font-cal-sans",
  weight: "400 700", // the font's whole wght axis range — pick any value in between
  display: "swap",
});

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en" className={calSans.variable}>
      <body>{children}</body>
    </html>
  );
}
```

Because `CalSansVF.woff2` is a variable font, `weight: "400 700"` gives you every weight in
that range from one file — no separate imports per weight.

## 4. Wire it into Tailwind

```ts
// tailwind.config.ts
import { fontFamily } from "tailwindcss/defaultTheme";

export default {
  theme: {
    extend: {
      fontFamily: {
        cal: ["var(--font-cal-sans)", ...fontFamily.sans],
      },
    },
  },
};
```

```tsx
<h1 className="font-cal">Scheduling infrastructure for everyone.</h1>
```

## Notes

- `font-optical-sizing: auto` (on by default in modern browsers) lets the `opsz` axis respond to
  `font-size` automatically — no extra setup needed.
- For the other variable axes (`GEOM`, `YTAS`, `SHRP`, `ital`) and the static, single-weight
  cuts under `fonts/`, see the main [README](../README.md) and [fonts/README](../fonts/README.md).
