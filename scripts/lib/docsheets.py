#!/usr/bin/env python3
"""
fonts/README.md specimen sheets, drawn from the freshly built fonts.

    python3 -m scripts.lib.docsheets            # reads fonts/, writes the SVGs

Every sheet is outlined text — no webfont, no system font — so it reads the same
on GitHub in every browser. Each one is written twice with its palette baked in
(name.svg, name-dark.svg) rather than switched by a media query, because Safari
does not honour prefers-color-scheme inside an SVG loaded through <img>; the
README picks the file with <picture>. Same reasoning as charalts.py.

Sheets:
    tiers          Display / Text / Micro at one size: the tiers differ in spacing,
                   not in height
    waterfall      8px upward at real pixels, each size in the tier made for it
    families       A11y / UI / Base / Geo on the letters that tell them apart
    metrics        animated: cap height, x-height and width of each tier, overlaid
    textui-l       the curved l Cal Sans Text UI ships as its default
    cuts-<variant> the four weights, roman over italic, before each static table
"""
import argparse
import gzip
import os
import subprocess
import sys
from functools import lru_cache
from pathlib import Path

import uharfbuzz as hb
from fontTools.pens.boundsPen import BoundsPen
from fontTools.pens.svgPathPen import SVGPathPen
from fontTools.pens.transformPen import TransformPen
from fontTools.ttLib import TTFont

STATIC = Path("fonts/calsans-static-full/ttf")
TEXTUI = Path("fonts/calsans-gf-api-textui/CalSansTextUI[wght].ttf")
OUT = Path("documentation/images/fonts-readme")

# No background and no margin, like the character-alternative cells and CalLines:
# the page shows through. `card` is only for the metrics sheet's plate.
PALETTE = {
    "light": {"ink": "#242424", "dim": "#898989", "card": "#f8f8f8"},
    "dark":  {"ink": "#e6edf3", "dim": "#777777", "card": "#151515"},
}
# metrics alone keeps the svgshow card, as the Interoperable card it is a turn on:
# inset 3.04% of the artboard, corner 7.208% of the card's own width, shown at 800.
CARD_INSET, CARD_R, CARD_PAD = 0.030397, 0.072084, 64.0

W = 1520.0            # artboard and displayed width of the scaled sheets, as CalLines
REAL = 880            # the waterfall's, drawn 1:1 so 8px is 8px
LAB = 44.0            # label size
TOP = LAB * 0.8       # first label's baseline: its cap height and overshoot, so ink starts at y=0

TIERS = [("", "Display", 45), ("Text", "Text", 10), ("Micro", "Micro", 8)]
FAMILIES = [("A11y", "Cal Sans A11y", 0), ("UI", "Cal Sans UI", 25),
            ("", "Cal Sans", 50), ("Geo", "Cal Sans Geo", 100)]
WEIGHTS = ["Regular", "Medium", "SemiBold", "Bold"]
VARIANTS = [("default", "", 720, 0), ("tall", "Tall", 800, 0),
            ("sharp", "Sharp", 720, 100), ("tall-sharp", "TallSharp", 800, 100)]


def static(tier="", family="", variant="", style="Regular"):
    """fonts/calsans-static-full/ttf/CalSans{tier}{family}{variant}-{style}.ttf"""
    return STATIC / f"CalSans{tier}{family}{variant}-{style}.ttf"


def italic(weight):
    return "Italic" if weight == "Regular" else weight + "Italic"


# ---------------------------------------------------------------- outlines

class Face:
    def __init__(self, path, location=None):
        self.tt = TTFont(path)
        self.upm = self.tt["head"].unitsPerEm
        self.gs = self.tt.getGlyphSet(location=location)
        self.names = self.tt.getGlyphOrder()
        self.hb = hb.Font(hb.Face(Path(path).read_bytes()))
        if location:
            self.hb.set_variations(location)

    def shape(self, text):
        buf = hb.Buffer()
        buf.add_str(text)
        buf.guess_segment_properties()
        hb.shape(self.hb, buf, {"kern": True, "liga": True})
        return [(self.names[i.codepoint], p.x_advance, p.x_offset, p.y_offset)
                for i, p in zip(buf.glyph_infos, buf.glyph_positions)]

    def advance(self, text, size):
        return sum(a for _, a, _, _ in self.shape(text)) * size / self.upm

    def outline(self, text, size, x, y, anchor="start", merge=False):
        x -= {"start": 0, "middle": self.advance(text, size) / 2,
              "end": self.advance(text, size)}[anchor]
        s, pen, d = size / self.upm, 0, []
        for name, adv, xo, yo in self.shape(text):
            svg = SVGPathPen(self.gs, ntos=lambda v: f"{v:.1f}".rstrip("0").rstrip("."))
            t = TransformPen(svg, (s, 0, 0, -s, x + (pen + xo) * s, y - yo * s))
            if merge:   # union the contours, so a stroked outline draws no seams
                from pathops import Path as SkPath   # skia-pathops, only the metrics sheet
                sk = SkPath()
                self.gs[name].draw(sk.getPen(glyphSet=self.gs))
                sk.simplify()
                sk.draw(t)
            else:
                self.gs[name].draw(t)
            d.append(svg.getCommands())
            pen += adv
        return "".join(d)

    def height(self, ch):
        b = BoundsPen(self.gs)
        self.gs[self.tt.getBestCmap()[ord(ch)]].draw(b)
        return b.bounds[3] / self.upm


@lru_cache(None)
def face(path, wght=None):
    return Face(path, {"wght": wght} if wght else None)


LABEL = lambda: face(static("Text", "UI", "", "Medium"))
VALUE = lambda: face(static("Text", "UI"))


def label(x, y, name, value, size, fill_name="ink"):
    """'Cal Sans UI  opsz 45' — the name in ink, its coordinates dimmed after it."""
    out = [f'<path fill="{{{fill_name}}}" d="{LABEL().outline(name, size, x, y)}"/>']
    if value:
        vx = x + LABEL().advance(name, size) + size * 0.5
        out.append(f'<path fill="{{dim}}" d="{VALUE().outline(value, size, vx, y)}"/>')
    return "".join(out)


# ---------------------------------------------------------------- document

def document(name, w, h, body, aria, style="", card=False):
    """Write name.svg and name-dark.svg, each with its palette baked in. With
    card, the body is set on a rounded plate inside a transparent margin."""
    shown = w
    if card:
        i = w * CARD_INSET
        dy = i + CARD_PAD
        h += 2 * dy
        cw = w - 2 * i
        body = (f'<rect x="{i:.2f}" y="{i:.2f}" width="{cw:.2f}" height="{h - 2 * i:.2f}" '
                f'rx="{cw * CARD_R:.2f}" fill="{{card}}"/>\n'
                f'<g transform="translate(0 {dy:.2f})">{body}</g>')
        shown = 800
    svg = (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {w:.0f} {h:.0f}" '
           f'width="{shown:.0f}" height="{shown * h / w:.0f}" role="img" aria-label="{aria}">\n'
           f'{style}{body}\n</svg>\n')
    for mode, suffix in (("light", ""), ("dark", "-dark")):
        out = OUT / f"{name}{suffix}.svg"
        text = svg
        for k, v in PALETTE[mode].items():
            text = text.replace("{" + k + "}", v)
        out.write_text(text)
    print(f"   {name}.svg  {w:.0f}x{h:.0f}  {len(gzip.compress(svg.encode())):,} B gzipped")


# ---------------------------------------------------------------- sheets

def tiers():
    """One word in Display, Text and Micro at one size, left-aligned, with every
    letter's advance marked as in a font editor — the small tiers give each letter
    more room, not more height. Deltas are per letter in 1000-UPM units (the
    sources' units; the fonts ship at 2000)."""
    word = "Cal v2"
    fs = [(face(static(t, "UI")), f"Cal Sans UI {n}".replace(" Display", ""),
           f"opsz {o}") for t, n, o in TIERS]
    size = W / fs[-1][0].advance(word, 1)
    # nominal advances (hmtx), not shaped ones: kerning is not spacing
    per = lambda f: [f.tt['hmtx'][n][0] * 1000 / f.upm for n, _, _, _ in f.shape(word)]
    y, body, prev = TOP, [], None
    for k, (f, name, value) in enumerate(fs):
        body.append(label(0, y, name, value, LAB))
        if prev:
            d = sum(a - b for a, b in zip(per(f), per(prev[0]))) / len(per(f))
            body.append(f'<path fill="{{dim}}" d="{VALUE().outline(f"+{d:.0f} units a letter on {prev[1]}", LAB, W, y, "end")}"/>')
        y += 0.72 * size + 34
        body.append(f'<path fill="{{ink}}" d="{f.outline(word, size, 0, y)}"/>')
        x, ticks = 0.0, []
        for _, adv, _, _ in [(None, 0, 0, 0)] + f.shape(word):
            x += adv * size / f.upm
            ticks.append(f"M{min(max(x, 1), W - 1):.1f},{y - 0.72 * size - 12:.1f}V{y + 0.12 * size:.1f}")
        body.append(f'<path d="{"".join(ticks)}" stroke="{{dim}}" stroke-width="2.5"/>')
        y += 0.12 * size + (TOP + 40 if k < len(fs) - 1 else 0)
        prev = (f, name.replace("Cal Sans UI", "").strip() or "Display")
    document("tiers", W, y, "\n".join(body),
             "Cal v2 in Cal Sans UI, UI Text and UI Micro at one size, each letter's advance marked")


WATERFALL_SIZES = [8, 9, 10, 11, 12, 13, 14, 16, 18, 20, 24, 32, 40, 48, 64, 96, 128, 192]
WATERFALL_TEXT = ["Scheduling Infrastructure", "Sched Infra", "Infra"]


def tier_for(px):
    """The static tier made for a pixel size. Boundaries sit halfway between the
    tiers' optical sizes on a log scale: 8 · 10 · 45."""
    return TIERS[2] if px < 9.5 else TIERS[1] if px < 21 else TIERS[0]


def waterfall():
    """Real pixels: the viewBox IS the displayed width, so 8px is 8px on the page.
    Each size takes the longest copy that fits: the full phrase on one line, then
    on two, then Sched Infra, then Infra alone."""
    w, col = float(REAL), 112.0
    room = w - col
    y, body = 0.0, []
    for n, px in enumerate(WATERFALL_SIZES):
        t, tname, _ = tier_for(px)
        f = face(static(t, "UI"))
        full = WATERFALL_TEXT[0]
        options = [[full], full.split(" ", 1)] + [[s] for s in WATERFALL_TEXT[1:]]
        lines = next(o for o in options if all(f.advance(s, px) <= room for s in o))
        lead = px * 1.2
        y += 0.85 * max(px, 12) if n == 0 else max(lead, 22)
        body.append(label(0, y, f"{px}px", tname, 12))
        for k, s in enumerate(lines):
            body.append(f'<path fill="{{ink}}" d="{f.outline(s, px, col, y + k * lead)}"/>')
        y += (len(lines) - 1) * lead + max(px * 0.3, 12)
    document("waterfall", w, y - max(px * 0.3, 12) + px * 0.25, "\n".join(body),
             "Cal Sans UI from 8px to 192px, each size in its optical tier")


def stack(fs, line):
    """Labelled lines of one text, sized so the widest fills the width.
    Returns (height, body)."""
    size = min(W / f.advance(line, 1) for f, _, _ in fs)
    y, body = TOP, []
    for k, (f, name, value) in enumerate(fs):
        body.append(label(0, y, name, value, LAB))
        y += 0.72 * size + 30
        body.append(f'<path fill="{{ink}}" d="{f.outline(line, size, 0, y)}"/>')
        y += 0.25 * size + (TOP + 40 if k < len(fs) - 1 else 0)
    return y, "\n".join(body)


def families():
    """The four GEOM families on a line that shows what moves between them."""
    line = "2160 just Groovy, I’ll Magic"
    fs = [(face(static("", k)), n, f"GEOM {g}") for k, n, g in FAMILIES]
    document("families", W, *stack(fs, line),
             "Cal Sans A11y, Cal Sans UI, Cal Sans and Cal Sans Geo")


def textui_l():
    """Where Cal Sans Text UI's default l comes from: Cal Sans A11y draws it, and
    the Google Fonts family takes that l alone, keeping UI's I, so I, l and 1
    never collide."""
    line = "Il1 Illinois"
    fs = [(face(static("Text", "A11y")), "Cal Sans A11y Text", "where the curved l comes from"),
          (face(str(TEXTUI), 400), "Cal Sans Text UI", "takes only the l, by default")]
    document("textui-l", W, *stack(fs, line),
             "Il1 Illinois in Cal Sans A11y Text and Cal Sans Text UI")


def cuts():
    """Per static variant: the four weights of Cal Sans, roman on top and the
    italics beneath, nudged right — a large crop of CalStatics."""
    word, gap = "Cal v2", 0.5
    for slug, var, ytas, shrp in VARIANTS:
        rom = [face(static("", "", var, wt)) for wt in WEIGHTS]
        ita = [face(static("", "", var, italic(wt))) for wt in WEIGHTS]
        nudge = 0.4   # em the italic row sits right of the roman
        span = lambda fs: sum(f.advance(word, 1) for f in fs) + gap * (len(fs) - 1)
        size = W / (max(span(rom), span(ita)) + nudge)
        y = TOP
        name = "Cal Sans" + {"tall": " Tall", "sharp": " Sharp", "tall-sharp": " Tall Sharp"}.get(slug, "")
        body = [label(0, y, name, f"YTAS {ytas}  SHRP {shrp}  opsz 45", LAB)]
        for row, fs, dx in ((0, rom, 0), (1, ita, nudge * size)):
            y += 0.72 * size + (36 if row == 0 else 0.42 * size)
            x = dx
            for f in fs:
                body.append(f'<path fill="{{ink}}" d="{f.outline(word, size, x, y)}"/>')
                x += f.advance(word, size) + gap * size
        document(f"cuts-{slug}", W, y + 0.25 * size, "\n".join(body),
                 f"{name} in Regular, Medium, SemiBold and Bold, roman and italic")


def metrics():
    """Interoperable, turned on Cal Sans itself: “Hx” in Cal Sans UI Regular
    (solid) with every tier, Regular and Bold, overlaid as outlines from the same
    origin. Cap height, ascender and descender never move; x-height is the one
    vertical metric that does, more at Bold. The small tiers also set wider, so
    width is measured against the Display cut of the same weight. Six lozenges
    light each cut in turn. Only opacity animates."""
    EM = 460.0
    PILL_TEXT, PILL_H, PILL_PAD, PILL_GAP = 26.0, 54.0, 22.0, 10.0
    INTRO, SPOT, FADE = 2.5, 2.2, 0.35
    fs = [(face(static(t, "UI", "", wt)), (n + (" Bold" if wt == "Bold" else "")).strip(), t)
          for wt in ("Regular", "Bold") for t, n, _ in TIERS]
    total = INTRO + SPOT * len(fs) + FADE
    mid = W / 2

    def anim(vals):
        frames, t = [(0.0, vals[0]), (INTRO, vals[0])], INTRO
        for v in vals[1:]:
            frames += [(t + FADE, v), (t + SPOT, v)]
            t += SPOT
        frames.append((total, vals[0]))
        return (f'<animate attributeName="opacity" dur="{total:g}s" repeatCount="indefinite" '
                f'keyTimes="{";".join(f"{a / total:.4f}" for a, _ in frames)}" '
                f'values="{";".join(f"{v:g}" for _, v in frames)}"/>')

    phase = lambda k, rest, on, off: [rest] + [on if j == k else off for j in range(len(fs))]
    txt = lambda s, size, x, y, fill="ink", anchor="start": (
        f'<path fill="{{{fill}}}" d="{VALUE().outline(s, size, x, y, anchor)}"/>')

    ref = fs[0][0]
    wide = max(f.advance("Hx", EM) for f, _, _ in fs)
    x0 = mid - wide / 2 - 30
    pill_y = 1.0
    base = pill_y + PILL_H + 80 + 0.72 * EM
    cap, xh = ref.height("H"), ref.height("x")
    gx0, gx1 = x0 - 40, x0 + wide + 40
    ref_d = ref.outline("Hx", EM, x0, base, merge=True)

    def dotted(y):
        """A dotted line that stays visible where it crosses the solid “Hx”: ink
        over the card, card colour over the ink."""
        line = lambda c: (f'<path d="M{gx0:.1f},{y:.1f}H{gx1:.1f}" stroke="{{{c}}}" stroke-width="2.5" '
                          f'stroke-linecap="round" stroke-dasharray="0 9"/>')
        return f'{line("ink")}<g clip-path="url(#ref-shape)">{line("card")}</g>'

    body = [f'<defs><clipPath id="ref-shape"><path d="{ref_d}"/></clipPath></defs>']
    body += [f'<path d="M{gx0:.1f},{base - v * EM:.1f}H{gx1:.1f}" stroke="{{ink}}" '
             f'stroke-opacity="0.6" stroke-width="1.5"/>' for v in (0, xh, cap)]
    body.append(txt("cap height", 22, gx1 + 16, base - cap * EM + 8, "dim"))
    body.append(txt("x-height", 22, gx1 + 16, base - xh * EM + 8, "dim"))
    body.append(txt("baseline", 22, gx1 + 16, base + 8, "dim"))
    body.append(txt("100%", 26, gx0 - 16, base - cap * EM + 9, anchor="end"))
    display_w = {}
    faces, spots = [], []
    for k, (f, _, tier) in enumerate(fs):
        d = f.outline("Hx", EM, x0, base, merge=True)
        w = f.advance("Hx", EM)
        if tier == "":
            display_w = w
        if k:
            faces.append(f'<g class="face" opacity="0.12">{anim(phase(k, 0.12, 0.7, 0.12))}'
                         f'<path fill="none" stroke="{{ink}}" stroke-width="2.5" '
                         f'stroke-linejoin="round" d="{d}"/></g>')
        fx = f.height("x")
        ty = base + 62
        more = "" if tier == "" else f"  +{(w / display_w - 1) * 100:.1f}%"
        spot = [anim(phase(k, 0, 1, 0)), dotted(base - fx * EM),
                txt(f"{fx / cap * 100:.1f}%", 26, gx0 - 16, base - fx * EM + 9, anchor="end"),
                f'<path d="M{x0:.1f},{ty:.1f}H{x0 + w:.1f}M{x0:.1f},{ty - 12:.1f}v24'
                f'M{x0 + w:.1f},{ty - 12:.1f}v24" stroke="{{ink}}" stroke-width="2.5"/>',
                txt(f"width{more}", 26, x0 + w + 18, ty + 9)]
        spots.append(f'<g class="spot" opacity="0">{"".join(spot)}</g>')

    widths = [VALUE().advance(n, PILL_TEXT) + 2 * PILL_PAD for _, n, _ in fs]
    px = mid - (sum(widths) + PILL_GAP * (len(fs) - 1)) / 2
    pills = []
    for k, (_, n, _) in enumerate(fs):
        wd, by = widths[k], pill_y + PILL_H / 2 + PILL_TEXT * 0.36
        shape = (f'x="{px:.1f}" y="{pill_y:.1f}" width="{wd:.1f}" height="{PILL_H:.1f}" '
                 f'rx="{PILL_H / 2:.1f}"')
        pills.append(f'<rect {shape} fill="none" stroke="{{ink}}" stroke-opacity="0.3" stroke-width="2"/>'
                     f'<path fill="{{ink}}" opacity="0.7" d="{VALUE().outline(n, PILL_TEXT, px + wd / 2, by, "middle")}"/>'
                     f'<g class="spot" opacity="0">{anim(phase(k, 0, 1, 0))}<rect {shape} fill="{{ink}}"/>'
                     f'<path fill="{{card}}" d="{VALUE().outline(n, PILL_TEXT, px + wd / 2, by, "middle")}"/></g>')
        px += wd + PILL_GAP

    body += faces + [f'<path fill="{{ink}}" d="{ref_d}"/>'] + spots + pills
    body.append(txt("Cal Sans UI tiers at one size: only the x-height moves", 30, mid, base + 62 + 90, "dim", "middle"))
    style = ("<style>@media(prefers-reduced-motion:reduce){.face{opacity:.12!important}.spot{opacity:0!important}}</style>")
    document("metrics", W, base + 62 + 90 + 8, "\n".join(body),
             "Cal Sans UI Display, Text and Micro in Regular and Bold overlaid: "
             "only the x-height moves, and the small tiers set wider",
             style=style, card=True)


SHEETS = {"tiers": tiers, "waterfall": waterfall, "families": families,
          "metrics": metrics, "textui-l": textui_l, "cuts": cuts}


def build(only=None):
    OUT.mkdir(parents=True, exist_ok=True)
    for name, fn in SHEETS.items():
        if not only or name in only:
            fn()


# Animated sheets are judged by eye before they ship, so a build never redraws
# them; run `python3 -m scripts.lib.docsheets metrics` by hand.
ANIMATED = {"metrics"}


def spawn(log_path="scripts/temp/docsheets.log"):
    """Redraw the static sheets in their own python process, not waited on — like
    charalts.spawn, a failure here must never fail the font build."""
    os.makedirs(os.path.dirname(log_path), exist_ok=True)
    static = [n for n in SHEETS if n not in ANIMATED]
    return subprocess.Popen([sys.executable, "-m", "scripts.lib.docsheets", *static],
                            stdout=open(log_path, "w"), stderr=subprocess.STDOUT,
                            cwd=os.getcwd(), start_new_session=True), log_path


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("only", nargs="*", help=f"sheets to draw (default: all): {', '.join(SHEETS)}")
    build(ap.parse_args().only)


if __name__ == "__main__":
    main()
