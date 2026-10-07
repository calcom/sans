#!/usr/bin/env python3
"""
fonts/README.md specimen sheets, drawn from the freshly built fonts.

    python3 -m scripts.lib.docsheets            # reads fonts/, writes the SVGs

Every sheet is outlined text — no webfont, no system font — so it reads the same
on GitHub in every browser. Each one is written twice with its palette baked in
(name.svg, name-dark.svg) rather than switched by a media query, because Safari
does not honour prefers-color-scheme inside an SVG loaded through <img>; the
README picks the file with <picture>. Same reasoning as charalts.py.

Each sheet is drawn as specimen only — no label, no background, no margin, ink
starting at x=0 — because the README sets every one in a table row beside a text
label (real, searchable text, never scaled). The rows of one table share a size and
a viewBox width, so they compare honestly.

Sheets (one file pair per row, plus the README table that holds them):
    tiers-<tier>        display, text, micro: "Cal v2" at one size, each letter's
                        advance marked; the tiers differ in spacing, not in height
    waterfall-<px>      one file per size, 08 to 192, at real pixels (the viewBox is
                        the displayed size), each in the tier made for it
    families-<family>   a11y, ui, base, geo on the letters that tell them apart
    textui-l-<family>   a11y, ui: Cal Sans A11y Text against Cal Sans Text UI, how
                        I, l and 1 are told apart
    cuts-<variant>      default, tall, sharp, tall-sharp: the four weights, roman
                        over italic, a figure with a margin under each static heading
    header              animated: the README banner, this page's specimens drifting
                        right to left in three lanes, feathered at the edges
    metrics             animated: cap height, x-height and width of each tier,
                        overlaid. The only sheet that keeps a label and a card.
"""
import argparse
import gzip
import math
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
OUT = Path("documentation/images/fonts-readme")

# No background and no margin, like the character-alternative cells and CalLines:
# the page shows through. `card` is only for the metrics sheet's plate.
PALETTE = {
    "light": {"ink": "#242424", "dim": "#898989", "card": "#f8f8f8"},
    "dark":  {"ink": "#e6edf3", "dim": "#777777", "card": "#151515"},
}
# metrics alone keeps the svgshow card, as the Interoperable card it is a turn on:
# inset 3.04% of the artboard, corner 7.208% of the card's own width, shown at full README width.
CARD_INSET, CARD_R, CARD_PAD = 0.030397, 0.072084, 64.0

CUT_MARGIN = 0.031    # the cuts figures' margin, a share of W (CalLines' inset)
W = 1520.0            # viewBox width of the scaled sheets (the README shows them at 640) and of the metrics artboard

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

    def bounds(self, text):
        """The shaped text's real ink box (xMin, yMin, xMax, yMax) in em, origin at
        the first pen position, y up. Not the advance: an italic's last stroke leans
        out of its box, and the tallest letter sets the top."""
        pen, box = 0, [None] * 4
        for name, adv, xo, yo in self.shape(text):
            bp = BoundsPen(self.gs)
            self.gs[name].draw(bp)
            if bp.bounds:
                x0, y0, x1, y1 = bp.bounds
                new = (pen + xo + x0, yo + y0, pen + xo + x1, yo + y1)
                box = [n if o is None else (min if k < 2 else max)(o, n) for k, (o, n) in enumerate(zip(box, new))]
            pen += adv
        return tuple(v / self.upm for v in box)

    def height(self, ch):
        b = BoundsPen(self.gs)
        self.gs[self.tt.getBestCmap()[ord(ch)]].draw(b)
        return b.bounds[3] / self.upm


@lru_cache(None)
def face(path, wght=None):
    return Face(path, {"wght": wght} if wght else None)


VALUE = lambda: face(static("Text", "UI"))   # the metrics sheet's captions


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
        shown = w   # full README width, like GeomAxis and geometry-mach-5
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
#
# Every sheet is a set of specimen-only SVGs: no label, no background, no margin,
# ink starting at x=0. The README sets each one in a table row, with the label as
# real text in the left cell. The rows of one table share one size and one viewBox
# width (and, where the text is the same, one height, so baselines line up), so they
# compare honestly. Extents come from the glyphs' real ink bounds, never advances.

CELL = 640            # the waterfall's width: drawn 1:1, so it is also the README cell
TICK = 3.0            # advance-tick stroke width
PAD_EM = 0.2          # breathing room on every side, in em of the specimen, like the
                      # character-alternative cells (their glyph sits ~0.17 em in)


def rows_sheet(rows, text, ticks=False):
    """rows: [(file slug, Face, aria-label)], all setting `text` at one shared size.
    The viewBox is the union of the rows' ink (and, with ticks, of their advance
    marks), so every file has the same width and height and the same baseline."""
    tick = TICK / 2 if ticks else 0.0
    bs = [f.bounds(text) for _, f, _ in rows]
    x0, x1 = min(b[0] for b in bs), max(b[2] for b in bs)
    y0, y1 = min(b[1] for b in bs), max(b[3] for b in bs)
    if ticks:   # the marks run from the origin to the end of the advance, and below the baseline
        x0, x1 = min(x0, 0), max(x1, max(f.advance(text, 1) for _, f, _ in rows))
        y0 = min(y0, -0.12)
    size = (W - 2 * tick) / (x1 - x0 + 2 * PAD_EM)
    pad = tick + PAD_EM * size
    w, h = W, math.ceil((y1 - y0) * size + 2 * pad)
    ox, base = pad - x0 * size, pad + y1 * size
    for slug, f, aria in rows:
        body = [f'<path fill="{{ink}}" d="{f.outline(text, size, ox, base)}"/>']
        if ticks:
            x, marks = 0.0, []
            for _, adv, _, _ in [(None, 0, 0, 0)] + f.shape(text):
                x += adv * size / f.upm
                marks.append(f"M{ox + x:.1f},{pad:.1f}V{base - y0 * size:.1f}")
            body.append(f'<path d="{"".join(marks)}" stroke="{{dim}}" stroke-width="{TICK:g}"/>')
        document(slug, w, h, "\n".join(body), aria)


def tiers():
    """One word in Display, Text and Micro at one size, left-aligned, with every
    letter's advance marked as in a font editor — the small tiers give each letter
    more room, not more height. The README label says how much wider each sets."""
    word = "Cal v2"
    rows = [(f"tiers-{n.lower()}", face(static(t, "UI")),
             f"Cal v2 in Cal Sans UI {n}, each letter's advance marked")
            for t, n, _ in TIERS]
    rows_sheet(rows, word, ticks=True)
    wide = {n: face(static(t, "UI")).advance(word, 1) for t, n, _ in TIERS}
    print("   label widths:", ", ".join(f"{n} opsz {o} +{(wide[n] / wide['Display'] - 1) * 100:.0f}%"
                                         for _, n, o in TIERS))


WATERFALL_SIZES = [8, 9, 10, 11, 12, 13, 14, 16, 18, 20, 24, 32, 40, 48, 64, 96, 128, 192]
WATERFALL_TEXT = ["Scheduling Infrastructure", "Sched Infra", "Infra"]


def tier_for(px):
    """The static tier made for a pixel size. Boundaries sit halfway between the
    tiers' optical sizes on a log scale: 8 · 10 · 45."""
    return TIERS[2] if px < 9.5 else TIERS[1] if px < 21 else TIERS[0]


def waterfall():
    """One file per size at real pixels: the viewBox IS the displayed size, so 8px
    is 8px on the page. Each takes the longest copy whose ink fits the 640px cell
    on one line, set in the tier made for it."""
    for px in WATERFALL_SIZES:
        t, tname, _ = tier_for(px)
        f = face(static(t, "UI"))
        fits = lambda s: (lambda b: b[2] - b[0])(f.bounds(s)) * px <= CELL
        s = next(s for s in WATERFALL_TEXT if fits(s))
        x0, y0, x1, y1 = f.bounds(s)
        base = math.ceil(y1 * px)           # baseline on a pixel boundary
        h = base + math.ceil(-y0 * px)
        document(f"waterfall-{px:02d}", CELL, h,
                 f'<path fill="{{ink}}" d="{f.outline(s, px, -x0 * px, base)}"/>',
                 f"{s} at {px}px in Cal Sans UI {tname}")
        print(f"      {px}px {tname}: {s!r}")


def families():
    """The four GEOM families on a line that shows what moves between them."""
    rows = [(f"families-{k.lower() or 'base'}", face(static("", k)), f"2160 just Groovy, I’ll Magic in {n}")
            for k, n, _ in FAMILIES]
    rows_sheet(rows, "2160 just Groovy, I’ll Magic")


def textui_l():
    """How I, l and 1 are told apart: Cal Sans A11y Text draws a serifed I and a
    curved l; Cal Sans Text UI, the release's static cut (calsans-static-essentials),
    keeps the plain ones. Not the Google Fonts family, which bakes the curved l in."""
    rows = [("textui-l-a11y", face(static("Text", "A11y")), "Il1 Illinois in Cal Sans A11y Text"),
            ("textui-l-ui", face(static("Text", "UI")), "Il1 Illinois in Cal Sans Text UI")]
    rows_sheet(rows, "Il1 Illinois")


def cuts():
    """Per static variant: the four weights of Cal Sans, roman on top and the
    italics beneath, nudged right — a large crop of CalStatics. One size for all
    four variants. Not in a table: each opens its section as a figure under the
    heading, with a margin around it (CalLines' ~3%) to set it apart from the
    tables below."""
    word, gap, nudge, pitch = "Cal v2", 0.5, 0.4, 1.14   # em
    made = []
    for slug, var, ytas, shrp in VARIANTS:
        rom = [face(static("", "", var, wt)) for wt in WEIGHTS]
        ita = [face(static("", "", var, italic(wt))) for wt in WEIGHTS]
        rows = []
        for fs, dx in ((rom, 0.0), (ita, nudge)):
            x, items = dx, []
            for f in fs:
                items.append((f, x))
                x += f.advance(word, 1) + gap
            rows.append(items)
        bs = [[(f.bounds(word), x) for f, x in r] for r in rows]
        left = min(b[0] + x for r in bs for b, x in r)
        right = max(b[2] + x for r in bs for b, x in r)
        top = max(b[3] for r in bs for b, _ in r)
        bottom = min(b[1] for b, _ in bs[1])      # the italic row is the lower one
        made.append((slug, rows, left, right, top, bottom))
    margin = round(W * CUT_MARGIN)
    size = (W - 2 * margin) / max(m[3] - m[2] for m in made)
    for slug, rows, left, right, top, bottom in made:
        base0 = top * size
        h = math.ceil(base0 + pitch * size - bottom * size) + 2 * margin
        body = [f'<path fill="{{ink}}" d="{f.outline(word, size, margin + (x - left) * size, margin + base0 + k * pitch * size)}"/>'
                for k, items in enumerate(rows) for f, x in items]
        name = "Cal Sans" + {"tall": " Tall", "sharp": " Sharp", "tall-sharp": " Tall Sharp"}.get(slug, "")
        document(f"cuts-{slug}", W, h, "\n".join(body),
                 f"{name} in Regular, Medium, SemiBold and Bold, roman and italic")


def metrics():
    """Interoperable, turned on Cal Sans itself: “Hax” in Cal Sans UI Regular
    (solid) with every tier, Regular and Bold, overlaid as outlines from the same
    origin. Cap height, ascender and descender never move; x-height is the one
    vertical metric that does, more at Bold. The small tiers also set wider, so
    width is measured against the Display cut of the same weight. Six lozenges
    light each cut in turn. Only opacity animates."""
    EM = 460.0
    PILL_TEXT, PILL_H, PILL_PAD, PILL_GAP = 26.0, 54.0, 22.0, 10.0
    INTRO, SPOT, FADE = 2.5, 2.2, 0.35
    # Micro gets a dagger: the variable fonts reach opsz 8 but name no instance there
    # (only Text, 10, and Display, 45); Micro exists by name only as static fonts.
    fs = [(face(static(t, "UI", "", wt)), n + ("†" if n == "Micro" else ""), t, wt)
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
    wide = max(f.advance("Hax", EM) for f, _, _, _ in fs)
    # Centre between the solid word and the widest outline, so the solid "Hax" sits
    # near the middle while the wider tiers still fit inside the guides.
    x0 = mid - (ref.advance("Hax", EM) + wide) / 4
    pill_y = 1.0
    base = pill_y + PILL_H + 80 + 0.72 * EM
    cap, xh = ref.height("H"), ref.height("x")
    gx0, gx1 = x0 - 40, x0 + wide + 40
    ref_d = ref.outline("Hax", EM, x0, base, merge=True)

    def dotted(y):
        """A dotted line that stays visible where it crosses the solid “Hax”: ink
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
    for k, (f, _, tier, _) in enumerate(fs):
        d = f.outline("Hax", EM, x0, base, merge=True)
        w = f.advance("Hax", EM)
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

    # Two groups, each led by its weight as a dim label: "Regular  Display Text Micro",
    # a gap, "Bold  Display Text Micro". The pills carry only the tier.
    GROUP_GAP, LABEL_GAP = 56.0, 14.0
    widths = [VALUE().advance(n, PILL_TEXT) + 2 * PILL_PAD for _, n, _, _ in fs]
    groups = ["Regular", "Bold"]
    label_w = {g: VALUE().advance(g, PILL_TEXT) + LABEL_GAP for g in groups}
    total_w = (sum(widths) + PILL_GAP * (len(fs) - len(groups)) + sum(label_w.values())
               + GROUP_GAP * (len(groups) - 1))
    px = mid - total_w / 2
    pills = []
    for k, (_, n, _, wt) in enumerate(fs):
        if k == 0 or fs[k - 1][3] != wt:            # first pill of a group: its label first
            if k:
                px += GROUP_GAP - PILL_GAP
            pills.append(txt(wt, PILL_TEXT, px, pill_y + PILL_H / 2 + PILL_TEXT * 0.36, "dim"))
            px += label_w[wt]
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
    body.append(txt("† Micro is a static font only. The variable fonts reach its size, opsz 8, but don’t name it.",
                    22, mid, base + 62 + 90 + 46, "dim", "middle"))
    style = ("<style>@media(prefers-reduced-motion:reduce){.face{opacity:.12!important}.spot{opacity:0!important}}</style>")
    document("metrics", W, base + 62 + 90 + 46 + 8, "\n".join(body),
             "Cal Sans UI Display, Text and Micro in Regular and Bold overlaid: "
             "only the x-height moves, and the small tiers set wider",
             style=style, card=True)


def header():
    """The README's opening banner: the specimens from further down the page, at
    one shared scale, drifting right to left in three lanes and looping without a
    seam, feathered out at both edges. Animated (SMIL translate, linear), so the
    build leaves it alone like metrics.

    Each lane is drawn once into <defs> and placed twice, one lane-width apart; the
    pair slides left by exactly that width and repeats, so the second copy lands
    where the first began. Every lane moves at the same speed, so they read as one
    surface, each with its own period."""
    size, gap, speed = 120.0, 0.55, 70.0          # px, em between items, px/s
    pitch = 1.32 * size
    weights = [static("", "", v, st) for v in ("", "Tall", "Sharp")
               for wt in WEIGHTS for st in (wt, italic(wt))]
    lanes = [
        [(face(p), "Cal v2") for p in weights],
        [(face(static("", k)), "2160 just Groovy, I’ll Magic") for k, _, _ in FAMILIES],
        [(face(static(t, "UI")), "Scheduling Infrastructure") for t, _, _ in TIERS]
        + [(face(static("Text", "A11y")), "Il1 Illinois"), (face(static("Text", "UI")), "Il1 Illinois")],
    ]
    top = max(f.bounds(t)[3] for lane in lanes for f, t in lane) * size
    h = math.ceil(top + (len(lanes) - 1) * pitch + 0.3 * size)
    defs, moving = [], []
    for k, lane in enumerate(lanes):
        x, paths = 0.0, []
        for f, text in lane:
            paths.append(f'<path d="{f.outline(text, size, x, 0)}"/>')
            x += f.advance(text, size) + gap * size
        width = x                                  # includes the trailing gap: the seam
        defs.append(f'<g id="lane{k}">{"".join(paths)}</g>')
        y = top + k * pitch
        moving.append(
            f'<g transform="translate(0 {y:.1f})"><g>'
            f'<use href="#lane{k}"/><use href="#lane{k}" x="{width:.1f}"/>'
            f'<animateTransform attributeName="transform" type="translate" '
            f'from="0 0" to="{-width:.1f} 0" dur="{width / speed:.2f}s" '
            f'repeatCount="indefinite" calcMode="linear"/></g></g>')
    feather = 0.08
    body = (f'<defs>{"".join(defs)}'
            f'<linearGradient id="fade" x1="0" x2="1" y1="0" y2="0">'
            f'<stop offset="0" stop-color="#fff" stop-opacity="0"/>'
            f'<stop offset="{feather}" stop-color="#fff"/>'
            f'<stop offset="{1 - feather}" stop-color="#fff"/>'
            f'<stop offset="1" stop-color="#fff" stop-opacity="0"/></linearGradient>'
            f'<mask id="feather"><rect width="{W:.0f}" height="{h}" fill="url(#fade)"/></mask></defs>'
            f'<g fill="{{ink}}" mask="url(#feather)">{"".join(moving)}</g>')
    document("header", W, h, body,
             "Cal Sans specimens from this page drifting past: the weights, the four families, the tiers")


SHEETS = {"tiers": tiers, "waterfall": waterfall, "families": families,
          "metrics": metrics, "textui-l": textui_l, "cuts": cuts,
          "header": header}


def build(only=None):
    OUT.mkdir(parents=True, exist_ok=True)
    for name, fn in SHEETS.items():
        if not only or name in only:
            fn()


# Animated sheets are judged by eye before they ship, so a build never redraws
# them; run `python3 -m scripts.lib.docsheets metrics` by hand.
ANIMATED = {"metrics", "header"}


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
