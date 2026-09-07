# Fontbakery report — Cal Sans v2

`fontbakery 1.0.1`, `check-googlefonts --skip-network`, run per family. Fontbakery
treats every font handed to it in one invocation as one family, so the workspace folder
— which ships Cal Sans and Cal Sans Text UI side by side — is checked as two runs, not
one.

```bash
fontbakery check-googlefonts --skip-network -l WARN fonts/calsans-gf-api/*.ttf
fontbakery check-googlefonts --skip-network -l WARN fonts/calsans-gf-api-textui/*.ttf
fontbakery check-googlefonts --skip-network -l WARN fonts/calsans-gf-workspace/CalSans-*.ttf
fontbakery check-googlefonts --skip-network -l WARN fonts/calsans-gf-workspace/CalSansTextUI-*.ttf
```

## Results

| delivery | FAIL | WARN | PASS |
|---|---|---|---|
| `calsans-gf-api` | **4** | 7 | 242 |
| `calsans-gf-api-textui` | **0** | 8 | 245 |
| `calsans-gf-workspace` — Cal Sans | **0** | 54 | 783 |
| `calsans-gf-workspace` — Cal Sans Text UI | **0** | 55 | 782 |

Three of the four deliveries pass with zero failures.

## The remaining four, all on `calsans-gf-api`

```
2  googlefonts/STAT/axisregistry            → invalid-name, bad-coordinate
2  googlefonts/axisregistry/fvar_axis_defaults → not-registered
```

Both are Google Fonts Axis Registry membership, not defects in the font:

- **`opsz`** — STAT fallback names must come from the registry's point-size list, and the
  axis max is 45, which is not in it (the list goes 36 → 48). Remapping this build's max
  to 48 resolves it without a registry change.
- **`GEOM`** — the font's default is 25; the registry lists only `Default = 0`.
- **`YTAS`** — the font's default is 720; the registry lists only `Normal = 750`.

Cal Sans Text UI is unaffected because it exposes no `GEOM`, `YTAS` or `opsz` axis —
all three are baked, leaving `wght` alone.

Worth noting that Google's own [roboto-delta](https://github.com/googlefonts/roboto-delta/blob/main/.github/workflows/build.yaml)
skips `fvar_axis_defaults` in CI, with the reasoning that axis defaults "should be
whatever the designer deems appropriate, not a hardcoded value"
([axisregistry#222](https://github.com/googlefonts/axisregistry/issues/222)).

## What was fixed to get here

Vertical metrics per family preset, `fsSelection` bit 7, `nameID` 16/17 removed from the
variable fonts and kept on non-RIBBI statics, `nameID` 25 added carrying the slope,
italic `fvar` instance names corrected, `opsz` STAT values un-elided, `ital` STAT axis
normalised, `meta` table added, `gasp` and a smart-dropout `prep` written into every
font, underline pinned family-wide on the GF cuts, and in the source: `xi` and
`divisionslash` drawn, the three zero-width glyphs zeroed, `softhyphen` removed,
`linesep`/`paragraphsep` added, em/en/nbspace respaced, tabular figures respaced.
