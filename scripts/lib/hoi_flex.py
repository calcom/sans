"""Cal Sans Flex: true higher-order interpolation (HOI), behind pipeline.stage_compile_flex_hoi.

The morphs ride three hidden helper axes (GE1M, GE2M, GE3M) that avar2 drives from GEOM; their
products give the curved (order 2-3) paths. The designed paths come from the piecewise builder
(piecewise_phlex.inject_hoi, run on a throwaway copy of the font and read back), are fitted to
polynomials here and written as sparse helper sources into the designspace. The stock rclt swaps
stay; every glyph a swap can show carries the morph where it is shown, so without avar2 a renderer
sees the drawn forms.

Sections: the core and the families whose windows sit above the default (y, λ, j, f, t, M, C, c);
the no-avar2 fallback rule; the helper axes; the six family; the A11y legs below the default
(a, l, I).

── core ──
True HOI for Cal Sans Flex (behind --flex-hoi): each morph window rides the hidden helper axes
GE1M/GE2M/GE3M (the helper axes section) as a polynomial, carried by sparse SOURCES that fontmake
compiles like any other, so cu2qu converts every source of a glyph together.

Two halves, called by pipeline.stage_compile_flex_hoi:

  designed_paths(font)   GSFont side. Runs the piecewise injector (hoi.inject_hoi) on a THROWAWAY
                         prepared font and reads back the GEOM brace layers it emits: the designed
                         path, at the knots the designer approved, in cubic source order. Leaves
                         read their nodes; composites (when the injector braces them) read their
                         component offsets. Advance widths ride along as one more coordinate.
  add_true_hoi(ds, …)    designspace side (after `fontmake -o ufo`, before `fontmake -m`). Fits each
                         window per location (16 = 8 masters × SHRP 0/100), appends the helper axes
                         and writes sparse layers at helper locations that make varLib's
                         VariationModel produce exactly that polynomial on the GE1M = GE2M = GE3M
                         diagonal avar2 drives (reference/hoi-work/build/NOTES.md).

Fallback (ungated, settled): the stock rclt swaps are untouched. Every glyph a swap puts on screen
gets  D_X = Σ_live W_k + (Σ_folded travel_k − (X − F0))·R_X  (display_plan), so with
avar2 the swap is invisible and with the helpers at 0 each glyph is its own stock drawing.

── fallback ──
True-HOI fallback: how the stock rclt swaps and the helper-axis morphs share one font, so a renderer
without avar2 (helpers at 0) shows exactly stock CalSansVF. Text in, data or text out; nothing here
touches a font. Proofs and the decision record: reference/hoi-work/fallback/IMPLEMENTATION.md.

The pipeline's design (`display_plan`, "ungated"): the stock swaps stay as they are. Every glyph a
swap can put on screen carries helper tuples so that, wherever it is displayed, it looks like the
morph. Swap conditions never read a hidden axis, so split-brain renderers agree with themselves.

── helper axes ──
Hidden helper axes for the true-HOI Cal Sans Flex — the single source of truth for their tags,
ranges and avar2 ramps. Used at the designspace stage (add_helper_axes, before `fontmake -m`) and
by build_flex (default_ramps → one avar2 table with opsz→YTAS).

    GE1M, GE2M, GE3M   signed, −1…0…1. avar2 drives each to the normalized GEOM
                       (GEOM 0 → −1, 25 → 0, 100 → +1). Per-glyph morph windows are carried by
                       intermediate regions on these axes, never by the ramp
                       (reference/hoi-work/segmentation/verify_subwindow.py).

Without avar2 every helper rests at 0: nothing morphs and the stock swaps, which are left
untouched and read GEOM alone, show the drawn alternates. With avar2 the swapped-in alternates
carry the morph too, so the swap is not seen (reference/hoi-work/fallback/IMPLEMENTATION.md).

Ramps are `{tag: [(geom_user, helper_value), …]}`. Helper user value = helper normalized value
(default 0, extremes ±1), so a ramp value is what gvar regions and FeatureVariations conditions see.
avar2 interpolates linearly in NORMALIZED GEOM between its input points, and the font default is
always one of them; normalized GEOM is linear in user GEOM on each side of the default. So a ramp
that is piecewise-linear in user GEOM is reproduced exactly as long as its own breakpoints are given
— GE1M–GE3M need no intermediate points. This holds after build_flex.shift_defaults because
SHIPPING_DEFAULTS keeps GEOM at its compiled default (25): normalized GEOM is unchanged by the
shift. If the shipping GEOM default ever differs from the compiled one, the helper at the new
default would be non-zero and build_flex refuses (see _build_avar2_ds).

── six family ──
True HOI for the six family (behind --flex-hoi): the Phlex six sweep (hoi.inject_digit_hoi) on the
hidden helper axes, with Flex-only rclt swaps as the no-avar2 fallback. It reuses the core's fitting and
UFO plumbing and writes into the same helper layers.

Stock six has no rclt swap and no GEOM variation: `.rclt1-3` are reached only through cv30/ss16/
numr …. The Phlex timeline holds r1 across the default (15-36), which a helper morph cannot do from
the stock six (every helper is 0 at GEOM 25). So the builder adds GEOM-only rclt swaps here, and the
glyph the swaps show at the default (`.rclt1`, the ANCHOR) plays the part the core's F0 plays for y:

    M(s)  = A + Σ_p W_p(q_p(s))                  the Phlex path, A = the anchor's drawing
    D_X   = Σ_p W_p(q_p(s)) − (X − A)·R(s)        every displayed X, every piece p on its side

R rises from 0 at the default to 1 at the anchor hold's ends (GEOM 15 / 36) and holds. That is the
ungated rule with every window folded or live and R's edge moved in to the anchor hold: X + D_X = M
at EVERY GEOM outside 15-36, whichever form the swaps show, and inside the hold the swaps show the
anchor (D = 0 there). So the swap thresholds are invisible with avar2 wherever they sit outside the
hold, glyphs no swap reaches (six.tf with tnum: no .tf.rclt2/3 exist) are exact outside it too, and
without avar2 every form is its own drawing. Pieces: each moving run between two holds is cut at
Phlex knots into the fewest polynomials (order ≤ 3) that hit every knot at every location within
ORDER_TOL; runs land exactly on the drawings at their hold ends (as the core's windows do).

Call order (pipeline.stage_compile_flex_hoi): digit_add_swaps → save → digit_snapshot → designed_paths
(runs the injector) → digit_read_back → … → add_true_hoi → add_digit_hoi.

── A11y legs ──
True HOI for the A11y legs below the default (behind --flex-hoi): l and a, with their
composites. Companion to the core (y & co., windows above the default) and the six family section.

Phlex morphs each leaf from its A11y drawing up to itself across a window below GEOM 25
(hoi._inject_a11y_braces: a 10-13, l 13-15). Here that path rides the helpers on their
negative side (helper = normalized GEOM, −1 at GEOM 0), and the stock swaps stay:

    m(s)  = A − D + W(q(s))       the morph relative to the cmap drawing D: A − D below the window,
                                  the Phlex path inside it, 0 above (W lands on D − A)
    f_g   = m                     the cmap glyph: shown from the swap edge E up (and everywhere
                                  without GSUB), so it carries the whole morph
    f_X   = D − X + m(s)          the A11y form X, shown below E: looks like the morph there …
            ramped to 0 at s = 0  … and returns to its own drawing by the default, unseen (the
                                  default must stay the drawing)

So with avar2 the swap at E is invisible; without it every form is its own drawing. l's swap (11)
sits below its window (13-15): f_X is 0 there and l.rcltA11y gets no sources. a's swap (13) is the
window's end: a.rcltA11y carries the morph and then ramps back.

opsz ≤ 8: the stock keeps a.rcltA11y on to GEOM 34 (cond_opsz_8_A11y), the static A11y drawing. Its
helper sources get a twin at each opsz-8 corner holding the plain drawing, which cancels the morph at
opsz 8 (fading out to opsz 10, where that swap is off).

Call order (pipeline.stage_compile_flex_hoi): a11y_snapshot → designed_paths (runs the injector)
→ a11y_read_back → … → add_true_hoi → add_a11y_hoi.
"""
import copy
import re

import numpy as np
from fontTools.designspaceLib import SourceDescriptor
from fontTools.pens.transformPen import TransformPen
from fontTools.varLib.models import VariationModel, supportScalar

from scripts.lib import piecewise_phlex as phlex
from scripts.lib.piecewise_phlex import OPEN
from scripts.lib.utils import axis_index


# ════════════════════════════════════════════════════════════════════════════════════════════════
# helper axes
# ════════════════════════════════════════════════════════════════════════════════════════════════
# tag: (min, default, max). Name = tag, so designspace locations can key on either.
HELPER_AXES = {
    "GE1M": (-1.0, 0.0, 1.0),
    "GE2M": (-1.0, 0.0, 1.0),
    "GE3M": (-1.0, 0.0, 1.0),
}


def add_helper_axes(ds):
    """Append the hidden helper axes to a DesignSpaceDocument (after build_masters, before
    fontmake), so sparse sources at helper locations are legal. Every existing source and
    instance sits at the helpers' default 0 without being touched."""
    from fontTools.designspaceLib import AxisDescriptor, RangeAxisSubsetDescriptor
    present = {axis.tag for axis in ds.axes}
    assert not present & set(HELPER_AXES), f"helper axes already present: {present & set(HELPER_AXES)}"
    for tag, (lo, default, hi) in HELPER_AXES.items():
        axis = AxisDescriptor()
        axis.tag = axis.name = tag
        axis.minimum, axis.default, axis.maximum = lo, default, hi
        axis.hidden = True
        ds.addAxis(axis)
        # glyphsLib writes a format-5 <variable-fonts> whose axis subsets list the source axes
        # only; without this, fontmake compiles the VF without the helpers and drops their sources
        for vf in ds.variableFonts:
            vf.axisSubsets.append(RangeAxisSubsetDescriptor(name=tag))
    return ds


def default_ramps(geom_min, geom_default, geom_max):
    """GE1M–GE3M = normalized GEOM."""
    return {tag: [(geom_min, -1.0), (geom_default, 0.0), (geom_max, 1.0)] for tag in HELPER_AXES}


def ramp_value(ramp, geom):
    """A ramp read piecewise-linearly in user GEOM, held flat past its ends."""
    pts = sorted(ramp)
    if geom <= pts[0][0]:
        return pts[0][1]
    for (g0, v0), (g1, v1) in zip(pts, pts[1:]):
        if geom == g1:
            return v1
        if geom < g1:
            return v0 + (v1 - v0) * (geom - g0) / (g1 - g0)
    return pts[-1][1]

# ════════════════════════════════════════════════════════════════════════════════════════════════
# no-avar2 fallback rule
# ════════════════════════════════════════════════════════════════════════════════════════════════
GEOM_DEFAULT = 25.0

_CONDSET = re.compile(r"conditionset\s+(\w+)\s*\{(.*?)\}\s*\1\s*;", re.DOTALL)
_COND = re.compile(r"(\w+)\s+(-?[\d.]+)\s+(-?[\d.]+)\s*;")
_VARIATION = re.compile(r"variation\s+rclt\s+(\w+)\s*\{(.*?)\}\s*rclt\s*;", re.DOTALL)
_SUB = re.compile(r"^\s*sub\s+(\S+)\s+by\s+(\S+)\s*;\s*$")


def _conditionsets(code):
    """name → {axis: (lo, hi)} in user units, as written."""
    return {name: {axis: (float(lo), float(hi)) for axis, lo, hi in _COND.findall(body)}
            for name, body in _CONDSET.findall(code)}


# ── ungated ───────────────────────────────────────────────────────────────────────────────
def display_plan(code, chains):
    """Which helper tuples each displayed glyph needs, read off the stock swaps.

    `chains` maps a cmap glyph F0 to its morph windows, ordered outward from the GEOM default on
    each side: [(geom_from, geom_to, form_after), …] in user GEOM, geom_from nearer the default.
    The morph is M = F0 + Σ dF_k·q_k with q_k the window's clamped progress (0 before, 1 after).

    Returns {glyph: [entry, …]}, one entry per side the glyph is displayed on (default opsz):
        side    +1 / -1
        shown   (lo, hi) user GEOM where the stock swaps display it
        edge    the end of `shown` nearest the default: where its plateau ramp R must reach 1
        live    indices of windows that move inside `shown`: these carry the cubic tuples
        folded  {index: 1} windows already complete inside `shown`: folded into the plateau

    The glyph then needs  D = Σ_live dF_k·q_k + (Σ_folded c_k·dF_k − (glyph − F0))·R,  which is the
    designer's "plateau from the swap threshold, then the morph down to its own drawing". F0 itself
    has no R term. Swaps in conditionsets with any non-GEOM axis are not modelled; they come back in
    `other_axes` [(F0, glyph, conditions)], since a display range that crosses the default there
    has to be cancelled on that axis (opsz-8 `a`).
    """
    conds = _conditionsets(code)
    blocks = []                      # (geom range, {source: target}) in block order
    other_axes = []
    for name, body in _VARIATION.findall(code):
        cs = conds.get(name, {"GEOM": (0.0, OPEN)})
        subs = {}
        for line in body.split("\n"):
            m = _SUB.match(line)
            if m and m.group(1) in chains:
                subs[m.group(1)] = m.group(2)
        if not subs:
            continue
        if set(cs) != {"GEOM"}:
            other_axes += [(src, dst, cs) for src, dst in subs.items()]
            continue
        blocks.append((cs["GEOM"], subs))

    plan = {}
    for f0, windows in chains.items():
        cuts = sorted({0.0, GEOM_DEFAULT, 100.0} | {min(v, 100.0) for (lo, hi), s in blocks
                                                  if f0 in s for v in (lo, hi)})
        segments = {}                # (glyph, side) → [(lo, hi)]; a later block wins, as the merge does
        for lo, hi in zip(cuts, cuts[1:]):
            glyph = f0
            for (blo, bhi), subs in blocks:
                if f0 in subs and blo <= (lo + hi) / 2 <= bhi:
                    glyph = subs[f0]
            segments.setdefault((glyph, 1 if lo >= GEOM_DEFAULT else -1), []).append((lo, hi))
        forms = {f0} | {form for *_, form in windows}
        for (glyph, side), segs in segments.items():
            if glyph not in forms:
                continue                                 # a discrete swap (a.rcltBase): stays plain
            segs = _merge(segs)
            assert glyph == f0 or len(segs) == 1, f"{glyph} shown on split ranges {segs}: not modelled"
            live, folded = set(), {}
            for s_lo, s_hi in segs:
                edge, far = (s_lo, s_hi) if side > 0 else (s_hi, s_lo)
                for k, (g0, g1, _form) in enumerate(windows):
                    if (g1 - GEOM_DEFAULT) * side <= 0:
                        continue                         # other side of the default
                    if (g1 - edge) * side <= 0:
                        folded[k] = 1                    # finished before the glyph appears
                    elif (g0 - far) * side < 0:
                        live.add(k)                      # moves while the glyph is shown
            if glyph == f0:                              # no plateau term: every non-zero window is carried
                live |= set(folded)
                folded = {}
            lo, hi = segs[0][0], segs[-1][1]
            plan.setdefault(glyph, []).append(dict(
                side=side, shown=(lo, hi), edge=lo if side > 0 else hi,
                live=sorted(live), folded={k: 1 for k in folded if k not in live}))
    return plan, other_axes


def _merge(segs):
    out = []
    for lo, hi in sorted(segs):
        if out and out[-1][1] == lo:
            out[-1] = (out[-1][0], hi)
        else:
            out.append((lo, hi))
    return out


# ════════════════════════════════════════════════════════════════════════════════════════════════
# core, and the families whose windows sit above the default (y, λ, j, f, t, M, C, c)
# ════════════════════════════════════════════════════════════════════════════════════════════════
TRUE_HOI = ("y", "lambda", "jdotless", "fpart.comb", "tpart.comb", "M", "C", "c")   # leaves whose morph rides the helpers (f: its component leaf)
ORDER_TOL = 1.5          # lowest polynomial order (1-3) that fits every location this well, units
HOLD_TOL = 4.0           # consecutive knots closer than this (units) everywhere are a hold
HELPERS = list(HELPER_AXES)
F2 = 16384


def _q14(v):
    return round(v * F2) / F2


# ── GSFont side: the designed path, read back from the piecewise injector ─────────────────
def _vector(layer):
    """A layer as one coordinate array: path nodes (source order) or component offsets, then
    the advance width as a last (width, 0) row."""
    pts = ([(n.position.x, n.position.y) for n in phlex._nodes(layer)] if layer.paths else
           [(c.position.x, c.position.y) for c in layer.components])
    return np.array(pts + [(layer.width, 0.0)], float)


def _family(font, prefix_code, f0):
    """f0 and every cmap'd composite built on it, each with its rclt forms in GEOM order:
    {glyph: [glyph, form_1, …]}, and `via`. A composite belongs when each of its forms has the
    corresponding leaf form among its components and its swaps change nothing else (f_t also
    swaps t: not a member). A finite last swap returns to the glyph (f: 39-76 → [f, f.rcltBase, f]).
    A leaf no swap names (fpart.comb) takes its forms from the first glyph that swaps it, `via`
    (that glyph's forms; the leaf is displayed where they are), else via is None."""
    swaps = {}
    for cond, body in re.findall(r"variation\s+rclt\s+(\w+)\s*\{(.*?)\}\s*rclt\s*;", prefix_code, re.DOTALL):
        lo = re.search(rf"conditionset\s+{cond}\s*\{{\s*GEOM\s+(-?\d+)\s+(-?\d+)", prefix_code)
        for src, dst in re.findall(r"sub\s+(\S+)\s+by\s+(\S+)\s*;", body):
            swaps.setdefault(src, []).append((int(lo.group(1)), int(lo.group(2))) + (dst,) if lo
                                             else (0, phlex.OPEN, dst))

    def chain(g):
        s = sorted(swaps.get(g, []))
        return [g] + [d for *_, d in s] + ([g] if s and s[-1][1] < phlex.OPEN else [])
    m0 = font.masters[0].id
    comps = lambda fm: [c.name for c in font.glyphs[fm].layers[m0].components]
    leaf, via = chain(f0), None
    if len(leaf) == 1:
        for g in font.glyphs:
            forms = chain(g.name)
            if len(forms) > 1 and f0 in comps(g.name):
                i = comps(g.name).index(f0)
                leaf, via = [comps(fm)[i] for fm in forms], forms
                break
    fam = {f0: leaf}
    for g in font.glyphs:
        forms = chain(g.name)
        if g.name == f0 or len(forms) != len(leaf) or font.glyphs[forms[0]] is None:
            continue
        cs = [comps(fm) for fm in forms]
        rest = [sorted(n for n in c if n != lf) for lf, c in zip(leaf, cs)]
        if all(lf in c for lf, c in zip(leaf, cs)) and all(r == rest[0] for r in rest):
            fam[g.name] = forms

    # composites of members that swap on their own schedule (ij = i + j: no ij.rcltBase), their
    # forms read where each leaf form is displayed. Without its own helper sources ij keeps j's dot
    # where j's master has it: fontmake flattens j into ij, so j's offset morph never reaches it.
    def form_at(g, x):
        out = g
        for lo, hi, d in swaps.get(g, []):                # prefix order: a later block wins
            if lo <= x <= hi:
                out = d
        return out
    src = via[0] if via else f0
    reps = []
    for x in np.arange(25.5, 100, 1.0):
        if not reps or form_at(src, x) != form_at(src, reps[-1]):
            reps.append(x)
    assert len(reps) == len(leaf), f"{f0}: displayed forms {[form_at(src, x) for x in reps]} vs {leaf}"
    member_forms = {fm for fs in fam.values() for fm in fs}
    for g in font.glyphs:
        if g.name in fam or not swaps.get(g.name):
            continue
        forms = [form_at(g.name, x) for x in reps]
        if len(set(forms)) == 1 or any(font.glyphs[fm] is None for fm in forms):
            continue
        cs = [comps(fm) for fm in forms]
        hits = [[n for n in c if n in member_forms] for c in cs]
        rest = [sorted(n for n in c if n not in member_forms) for c in cs]
        if all(len(h) == 1 for h in hits) and all(r == rest[0] for r in rest):
            fam[g.name] = forms
    return fam, via


def _master_axes(font, mid):
    return tuple(float(c) for c in next(m.axes for m in font.masters if m.id == mid))


def _layer_key(font, layer, gi):
    """Where a layer sits once GEOM is set aside: (master id, design coordinates with GEOM at the
    master's). A brace at GEOM 35 on the SHRP 100 edge keys with that edge's own drawing."""
    master = _master_axes(font, layer.associatedMasterId)
    coords = list(layer.attributes.get("coordinates") or master)
    coords[gi] = master[gi]
    return (layer.associatedMasterId, tuple(float(c) for c in coords))


def designed_paths(font, names=TRUE_HOI):
    """Run phlex.inject_hoi on `font` (a prepared GSFont that is thrown away afterwards: it is
    mutated) and read back what it braced. Returns (paths, followers, locations):

        paths      {f0: {glyph: dict(forms=[glyph, form_1, …],
                                     base={loc: {form: vector}},       the drawings, before injection
                                     knots={loc: [(geom, vector)]})}}  the injected braces, by GEOM
        followers  every form of every family member, braced or not: composites shown wherever
                   their leaf form shows, so they may inherit its morph through the component
        locations  {loc: {axis tag: design value}}

    for f0 and every composite family member the injector braced, at every location it braced
    (master × SHRP edge for the leaf; composites also per YTAS edge). A form with no drawing of its
    own at a location is its master drawing there (it does not vary on that axis)."""
    prefix = next(p for p in font.featurePrefixes if p.name == "VARIATIONS").code
    gi = axis_index(font.axes, "GEOM")
    tags = [a.axisTag for a in font.axes]
    fams, via = {}, {}
    for f0 in names:
        fams[f0], via[f0] = _family(font, prefix, f0)
    forms = {fm for fam in fams.values() for fs in fam.values() for fm in fs}
    drawn = {fm: {_layer_key(font, L, gi): _vector(L) for L in font.glyphs[fm].layers
                  if L.associatedMasterId and (L.layerId == L.associatedMasterId
                                               or L.attributes.get("coordinates"))}
             for fm in forms}
    before = {fm: {L.layerId for L in font.glyphs[fm].layers} for fm in forms}
    phlex.inject_hoi(font, gi)
    paths, followers, locations = {}, set(), {}
    for f0, fam in fams.items():
        followers |= {fm for fs in fam.values() for fm in fs}
        paths[f0] = {}
        for g, fs in fam.items():
            knots = {}
            for L in font.glyphs[g].layers:
                if L.layerId not in before[g]:
                    knots.setdefault(_layer_key(font, L, gi), []).append(
                        (L.attributes["coordinates"][gi], _vector(L)))
            if not knots:
                assert g != f0, f"{f0}: the piecewise injector did not brace it"
                continue                        # composite not braced: follows its leaf's outline only
            if g != f0:
                # a composite answers SHRP through its own layers (prepare.align_composite_braces),
                # which differ per form (ý.rcltGeo ≠ ý at SHRP 100): carry the morph on those edges too,
                # landing on each form's own SHRP drawing, with the path's shape from the master edge
                for k in {k for fm in fs for k in drawn[fm]} - set(knots):
                    m = (k[0], _master_axes(font, k[0]))
                    if m in knots and all(a == b or t == "SHRP" for t, a, b in zip(tags, k[1], m[1])):
                        knots[k] = knots[m]
            base = {k: {fm: drawn[fm].get(k, drawn[fm][(k[0], _master_axes(font, k[0]))]) for fm in fs}
                    for k in knots}
            m0 = font.masters[0].id                # Glyphs component names: f's _part.stroke is decomposed in the UFO
            comps = {fm: [c.name for c in font.glyphs[fm].layers[m0].components] for fm in fs}
            paths[f0][g] = dict(forms=fs, base=base, comps={fm: c for fm, c in comps.items() if c},
                                knots={k: sorted(v, key=lambda kv: kv[0]) for k, v in knots.items()})
            if g == f0 and via[f0]:
                paths[f0][g]["shown_as"] = via[f0]      # a component leaf, displayed where these are
            locations.update({k: dict(zip(tags, k[1])) for k in knots})
        # SHRP coverage (builder-plan §2.7): the leaf carries its morph on every SHRP edge it is drawn on
        edges = {k for k in drawn[f0] if all(a == b or t == "SHRP" for t, a, b in
                                              zip(tags, k[1], _master_axes(font, k[0])))}
        missing = edges - set(paths[f0][f0]["knots"])
        assert not missing, f"{f0}: no morph braced at {sorted(missing)}"
        print(f"   ✅ true-HOI path read back — {f0}: braced {sorted(paths[f0])}, leaf at "
              f"{len(paths[f0][f0]['knots'])} locations; family {sorted(fam)}")
    return paths, followers, locations


# ── fitting: windows → per-location polynomials ───────────────────────────────────────────
def _windows(leaf):
    """Windows from the leaf's knots: a run of knots that move, between two holds. Consecutive
    knots within HOLD_TOL everywhere are a hold: the injector's frames are G1-cleaned and
    straight-kept, so a hold's ends can differ by a unit (y 80 → 100), while a window moves tens
    of units per knot. The morph lands on the drawings, so that drift is dropped. Returns
    [(g0, g1, form_after, knot_geoms)]; the forms come from the leaf's rclt chain in order."""
    geoms = [g for g, _ in next(iter(leaf["knots"].values()))]
    step = [max(np.abs(kn[i + 1][1] - kn[i][1]).max() for kn in leaf["knots"].values())
            for i in range(len(geoms) - 1)]
    moving = [d > HOLD_TOL for d in step]
    wins, i = [], 0
    while i < len(moving):
        if not moving[i]:
            i += 1
            continue
        j = i
        while j < len(moving) and moving[j]:
            j += 1
        wins.append((geoms[i], geoms[j], geoms[i:j + 1]))
        i = j
    held = [d for d, m in zip(step, moving) if not m]
    print(f"   ↳ {leaf['forms'][0]} knots {geoms}: holds drift ≤ {max(held, default=0):.2f}u, "
          f"window steps ≥ {min((d for d, m in zip(step, moving) if m), default=0):.1f}u")
    assert len(wins) == len(leaf["forms"]) - 1, f"{len(wins)} windows for forms {leaf['forms']}"
    return [(g0, g1, form, kn) for (g0, g1, kn), form in zip(wins, leaf["forms"][1:])]


def _poly_fit(U, S, order):
    """Pinned least squares: U[i] (displacement, U[0] = 0) at window position S[i] ∈ [0, 1] →
    coefficients c_1…c_order of Σ c_j t^j, summing to the travel U[-1]."""
    D = U[-1]
    if order == 1:
        return np.stack([D])
    A = np.stack([S ** j - S ** order for j in range(1, order)], 1)
    rhs = U - D[None] * (S ** order).reshape(-1, 1, 1)
    c = np.einsum("ij,j...->i...", np.linalg.pinv(A), rhs)
    return np.concatenate([c, (D - c.sum(0))[None]])


def _poly(c, t):
    return sum(c[j] * t ** (j + 1) for j in range(len(c)))


def _order(U, S):
    """Lowest order 1-3 whose pinned fit hits every knot within ORDER_TOL: (order, worst)."""
    for order in (1, 2, 3):
        worst = max(np.abs(_poly(_poly_fit(u, S, order), S[:, None, None]) - u).max() for u in U.values())
        if worst <= ORDER_TOL:
            break
    return order, worst


def fit_windows(paths, nG):
    """Per morph family: windows, the order chosen for each, and per (glyph, loc) each window's
    coefficients. A window's displacement is the drawn travel F_b − F_a plus the designed path's
    deviation from its own chord, so it starts and lands exactly on the stock drawings (the
    injector's hold braces are G1-cleaned copies, a few units off the drawings) and keeps the
    designed curve in between. nG maps user GEOM to the helper value avar2 gives it.

    A window no cubic fits within ORDER_TOL is split at the interior knot that fits best (j's
    75-80 at 78, as reference/hoi-work/fit/j found): two consecutive windows, C0 at the cut, both
    with `fi` = the index of the form the whole window lands on."""
    fits = {}
    for f0, fam in paths.items():
        wins = _windows(fam[f0])
        fit = dict(windows=[], coeffs={})
        for k, (g0, g1, form, kn) in enumerate(wins):
            s0, s1 = _q14(nG(g0)), _q14(nG(g1))
            S = np.array([(_q14(nG(g)) - s0) / (s1 - s0) for g in kn])
            U = {}
            for g, d in fam.items():
                fa, fb = d["forms"][k], d["forms"][k + 1]
                for loc, knots in d["knots"].items():
                    P = np.stack([v for gg, v in knots if gg in kn])
                    assert len(P) == len(kn), f"{g} {loc}: knots {[gg for gg, _ in knots]} miss {kn}"
                    chord = P[0] + (P[-1] - P[0]) * S.reshape(-1, 1, 1)
                    drawn = d["base"][loc][fb] - d["base"][loc][fa]
                    U[(g, loc)] = drawn * S.reshape(-1, 1, 1) + (P - chord)

            def piece(i, j):                   # knots i..j of the window, re-based at knot i
                ss0, ss1 = _q14(nG(kn[i])), _q14(nG(kn[j]))
                SS = np.array([(_q14(nG(g)) - ss0) / (ss1 - ss0) for g in kn[i:j + 1]])
                UU = {key: u[i:j + 1] - u[i] for key, u in U.items()}
                return (kn[i], kn[j], ss0, ss1, SS, UU, *_order(UU, SS))
            pieces = [piece(0, len(kn) - 1)]
            if pieces[0][-1] > ORDER_TOL and len(kn) > 3:
                cuts = [[piece(0, c), piece(c, len(kn) - 1)] for c in range(1, len(kn) - 1)]
                best = min(cuts, key=lambda ps: max(p[-1] for p in ps))
                if max(p[-1] for p in best) < pieces[0][-1]:
                    pieces = best
            for pg0, pg1, ps0, ps1, SS, UU, order, worst in pieces:
                for key, u in UU.items():
                    fit["coeffs"].setdefault(key, []).append(_poly_fit(u, SS, order))
                fit["windows"].append(dict(g0=pg0, g1=pg1, s0=ps0, s1=ps1, form=form, fi=k + 1,
                                           order=order, knots=[g for g in kn if pg0 <= g <= pg1],
                                           resid=worst))
                print(f"   ↳ {f0} window {pg0:g}–{pg1:g} → {form}: order {order}, "
                      f"worst knot residual {worst:.2f}u")
        fits[f0] = fit
    return fits


# ── the D_X rule, as a function of the helper value s on the avar2 diagonal ───────────────
def _ramp(t):
    return np.clip(t, 0.0, 1.0)


def displays(paths, fits, prefix_code, nG):
    """Per displayed glyph X (each form of each family member): its helper function as pieces
    and the locations it is defined at. Returns {X: dict(member, pieces, edge, shown)} where
    pieces = [(k, sign)] live windows, edge is R_X's peak (None for the cmap glyph) and shown the
    user-GEOM range where X looks like the morph: from its swap edge (0 for the cmap glyph) to the
    first window it does not carry (j: 0-75, j.rcltGeo 74-100). A component leaf
    (fpart.comb) is displayed where the glyph it was read through (`shown_as`, f) displays its forms."""
    out = {}
    for f0, fam in paths.items():
        wins = fits[f0]["windows"]
        for g, d in fam.items():
            shown = d.get("shown_as", d["forms"])
            chain = {shown[0]: [(w["g0"], w["g1"], shown[w["fi"]]) for w in wins]}
            plan, _ = display_plan(prefix_code, chain)
            for X, XS in zip(d["forms"], shown):
                assert not any(e["live"] for e in plan[XS] if e["side"] < 0), f"{X}: windows below the default"
                (entry,) = [e for e in plan[XS] if e["side"] > 0]
                lo = 0.0 if X == g else entry["edge"]
                pending = [w["g0"] for k, w in enumerate(wins) if w["g0"] >= lo
                           and k not in entry["live"] and k not in entry["folded"]]
                out[X] = dict(member=g, live=entry["live"], folded=sorted(entry["folded"]),
                              edge=None if X == g else _q14(nG(entry["edge"])),
                              shown=(lo, min(pending, default=100.0)))
    return out


def helper_function(X, disp, paths, fits, f0, loc):
    """f_X(s) at `loc`: (vector-valued) callable on helper values s, plus its knots and the
    highest polynomial order present."""
    d = paths[f0][disp["member"]]
    wins = fits[f0]["windows"]
    co = [fits[f0]["coeffs"][(disp["member"], loc)][k] for k in range(len(wins))]
    travel = [c.sum(0) for c in co]
    forms = d["forms"]
    C = None
    if disp["edge"] is not None:
        C = sum((travel[k] for k in disp["folded"]), np.zeros_like(travel[0])) \
            - (d["base"][loc][X] - d["base"][loc][forms[0]])

    def f(s):
        v = np.zeros_like(travel[0])
        for k in disp["live"]:
            w = wins[k]
            v = v + _poly(co[k], _ramp((s - w["s0"]) / (w["s1"] - w["s0"])))
        if C is not None:
            v = v + C * _ramp(s / disp["edge"])
        return v
    return f


def _helper_locs(X, disp, fits, f0):
    """Helper source points for X: every knot on GE1M; the diagonal (k, k) and (k, k, k) from
    the start of the first live window that needs that order onward (the start itself has a
    zero delta: it only cuts the next region down to the window). Plus 1, for the hold."""
    wins = fits[f0]["windows"]
    K = {1.0} | {wins[k][e] for k in disp["live"] for e in ("s0", "s1")}
    if disp["edge"] is not None:
        K.add(disp["edge"])
    locs = [(k,) for k in sorted(K)]
    for p in (2, 3):
        starts = [wins[k]["s0"] for k in disp["live"] if wins[k]["order"] >= p]
        if starts:
            locs += [(k,) * p for k in sorted(K) if k >= min(starts)]
    return [dict(zip(HELPERS, h)) for h in locs]


def solve_sources(f, locs):
    """Helper-source values (relative to the location's own drawing) that make varLib's
    VariationModel reproduce f on the diagonal GE1M = GE2M = GE3M = s. The model's regions are
    rebuilt here exactly as varLib builds them from these locations (master axes only multiply
    them), the deltas are solved on the diagonal and pushed back into source values."""
    model = VariationModel([{}] + locs, axisOrder=HELPERS)
    sups = model.supports[1:]
    S = np.unique(np.concatenate([np.linspace(0, 1, 401)] + [[l[HELPERS[0]]] for l in locs]))
    phi = np.array([[supportScalar(dict.fromkeys(HELPERS, s), sp) for sp in sups] for s in S])
    F = np.stack([f(s) for s in S])
    shape = F.shape[1:]
    d, *_ = np.linalg.lstsq(phi, F.reshape(len(S), -1), rcond=None)
    resid = np.abs(phi @ d - F.reshape(len(S), -1)).max()
    assert resid < 1e-6, f"helper sources cannot carry this path (diagonal residual {resid:.3g})"
    A = np.array([[supportScalar(model.locations[i], sp) for sp in sups] for i in range(1, len(locs) + 1)])
    vals = (A @ d).reshape(-1, *shape)
    by = {tuple(sorted(model.locations[i].items())): vals[i - 1] for i in range(1, len(locs) + 1)}
    return [by[tuple(sorted({k: v for k, v in l.items() if v}.items()))] for l in locs]


# ── designspace side ─────────────────────────────────────────────────────────────────────
def _ufo_order(glyph_ufo, n_points):
    """Index map from source (Glyphs) node order to UFO point order: glyphsLib stores a closed
    contour's start node last in Glyphs and first in the UFO."""
    order, o = [], 0
    for contour in glyph_ufo:
        n = len(contour)
        order += [o + n - 1] + list(range(o, o + n - 1))
        o += n
    assert o == n_points
    return order


def _ufo_vector(glyph):
    if len(glyph):
        pts = [(p.x, p.y) for c in glyph for p in c]
    else:
        pts = [(c.transformation[4], c.transformation[5]) for c in glyph.components]
    return np.array(pts + [(glyph.width, 0.0)], float)


def _set_vector(glyph, v):
    if len(glyph):
        for p, (x, y) in zip((p for c in glyph for p in c), v[:-1]):
            p.x, p.y = float(x), float(y)
    else:
        for c, (x, y) in zip(glyph.components, v[:-1]):
            c.transformation = (*c.transformation[:4], float(x), float(y))
    glyph.width = float(v[-1][0])


def _ufo_rows(glyph, comps):
    """For a UFO glyph that may mix contours and components: its rows (contour points in UFO
    order, then component offsets, then the advance) as Glyphs-vector row indices, and which rows
    are the Glyphs coordinates themselves. A path glyph maps by _ufo_order. A composite's
    components map by name (`comps`, the Glyphs layer's); one glyphsLib decomposed (f's unexported
    _part.stroke) became the contours, which then ride that component's offset (not exact)."""
    n = sum(len(c) for c in glyph)
    if not comps:
        rows = _ufo_order(glyph, n)
        return rows + [len(rows)], [True] * (n + 1)
    names, rows, gone = [c.baseGlyph for c in glyph.components], [], []
    for i, name in enumerate(comps):
        (rows if len(rows) < len(names) and names[len(rows)] == name else gone).append(i)
    assert len(rows) == len(names) and len(gone) == (1 if n else 0), f"{glyph.name}: {comps} vs {names}"
    return gone * n + rows + [len(comps)], [False] * n + [True] * (len(rows) + 1)


def _ufo_vector_mixed(glyph):
    return np.array([(p.x, p.y) for c in glyph for p in c]
                    + [(c.transformation[4], c.transformation[5]) for c in glyph.components]
                    + [(glyph.width, 0.0)], float)


def _set_vector_mixed(glyph, v):
    n = sum(len(c) for c in glyph)
    for p, (x, y) in zip((p for c in glyph for p in c), v[:n]):
        p.x, p.y = float(x), float(y)
    for c, (x, y) in zip(glyph.components, v[n:-1]):
        c.transformation = (*c.transformation[:4], float(x), float(y))
    glyph.width = float(v[-1][0])


def _shown(code, name):
    """User-GEOM ranges where the stock GEOM swaps put `name` on screen: where they swap it in if
    it is a swap target, else wherever they do not swap it away (everywhere if none names it)."""
    conds = _conditionsets(code)
    blocks = []
    for cs_name, body in _VARIATION.findall(code):
        cs = conds.get(cs_name, {"GEOM": (0.0, phlex.OPEN)})
        if set(cs) == {"GEOM"}:
            blocks.append((cs["GEOM"], dict(m.groups() for m in map(_SUB.match, body.split("\n")) if m)))
    sources = {s for _, subs in blocks for s, d in subs.items() if d == name} or {name}
    out = []
    for src in sources:
        cuts = sorted({0.0, 100.0} | {min(v, 100.0) for (lo, hi), subs in blocks if src in subs for v in (lo, hi)})
        for lo, hi in zip(cuts, cuts[1:]):
            g = src
            for (blo, bhi), subs in blocks:          # a later block wins, as the merge does
                if src in subs and blo <= (lo + hi) / 2 <= bhi:
                    g = subs[src]
            if g == name:
                out.append((lo, hi))
    return out


def _decompose(fonts, layer_sources, name, reaches):
    """Turn every component of `name` that reaches a helper-carrying glyph (`reaches(base)`, at any
    depth: f.ss14 = f.rcltBase = fpartrcltBase.comb + …) into contours, in every source layer where
    `name` or a glyph under it is drawn. Used for composites that are NOT displayed where their
    carrier looks like the morph (y.ss08 = y.rcltBase): left as components they would inherit a
    morph meant for another glyph."""
    for (path, layer_name) in layer_sources:
        font = fonts[path]
        layer = font.layers[layer_name] if layer_name else font.layers.defaultLayer
        default = font.layers.defaultLayer
        get = lambda n: layer[n] if n in layer else default[n]

        def under(n):
            return {n} | {u for c in get(n).components for u in under(c.baseGlyph)}
        src = get(name)
        bases = {u for c in src.components if reaches(c.baseGlyph) for u in under(c.baseGlyph)}
        if name not in layer and not any(b in layer for b in bases):
            continue

        def flat(n, pen):
            for contour in get(n):
                contour.draw(pen)
            for c in get(n).components:
                flat(c.baseGlyph, TransformPen(pen, c.transformation))
        g = copy.deepcopy(src)
        g.clearComponents()
        for c in src.components:
            if reaches(c.baseGlyph):
                flat(c.baseGlyph, TransformPen(g.getPen(), c.transformation))
            else:
                g.components.append(copy.deepcopy(c))
        layer.insertGlyph(g, name, overwrite=True, copy=False)


def _stroke_function(X, dx, wins, forms, layer, default, gone):
    """The decomposed smart part's own outline across the chain (t's crossbar is a _part.stroke whose
    `width` differs per form: 375 in t, 371 in t.rcltGeo). Each form's drawn part, blended linearly
    across each window, with the same live/folded/R structure as helper_function — so the part grows
    or shrinks through the morph instead of jumping at the swaps. None if the forms' parts differ."""
    S = []
    for fm in forms:
        gl = layer[fm] if fm in layer else default[fm]
        v = _ufo_vector_mixed(gl)
        if len(v) != len(gone):
            return None
        S.append(v[gone])
    Sx = S[forms.index(X)] if X in forms else None
    if Sx is None:
        return None
    span = {}
    for w in wins:
        a, b = span.get(w["fi"], (w["s0"], w["s1"]))
        span[w["fi"]] = (min(a, w["s0"]), max(b, w["s1"]))

    def share(k):
        w = wins[k]
        a, b = span[w["fi"]]
        return (S[w["fi"]] - S[w["fi"] - 1]) * (w["s1"] - w["s0"]) / (b - a)
    C = None
    if dx["edge"] is not None:
        C = sum((share(k) for k in dx["folded"]), np.zeros_like(Sx)) - (Sx - S[0])

    def f(s):
        v = np.zeros_like(Sx)
        for k in dx["live"]:
            w = wins[k]
            v = v + share(k) * _ramp((s - w["s0"]) / (w["s1"] - w["s0"]))
        if C is not None:
            v = v + C * _ramp(s / dx["edge"])
        return v
    return f


def add_true_hoi(ds, fonts, paths, followers, locations, prefix_code):
    """Append the helper axes to `ds` and the sparse helper sources to it and to the master
    UFOs in `fonts` ({path: ufoLib2.Font}). `paths`, `followers` and `locations` come from
    designed_paths."""
    from fontTools.designspaceLib import SourceDescriptor
    geom = next(a for a in ds.axes if a.tag == "GEOM")
    assert not geom.map or all(i == o for i, o in geom.map), "GEOM must be unmapped (avar SPEC rule 6)"
    nG = lambda g: ((g - geom.default) / (geom.default - geom.minimum) if g < geom.default
                    else (g - geom.default) / (geom.maximum - geom.default))
    tag_name = {a.tag: a.name for a in ds.axes}
    add_helper_axes(ds)

    def source_at(loc):
        want = {tag_name[t]: v for t, v in loc.items()}
        hits = [s for s in ds.sources if all(abs(s.location.get(n, 0) - v) < 1e-9 for n, v in want.items())]
        assert len(hits) == 1, f"{len(hits)} sources at {loc}"
        return hits[0]

    fits = fit_windows(paths, nG)
    disp = displays(paths, fits, prefix_code, nG)
    carriers = set(disp)
    plain = [(s.path, s.layerName) for s in ds.sources]

    # composites that reference a carrier but are not one of its displayed family members, and
    # are displayed where that carrier does not look like the morph (y.ss08 = y.rcltBase, at every
    # GEOM). Those shown only where it does keep it: ij (j), f_t (fpart.comb), ij.rcltGeo (j.rcltGeo)
    default_layer = fonts[ds.findDefault().path].layers.defaultLayer

    def reached(n):                                   # carriers under n, through plain composites
        return {n} if n in carriers else {r for c in default_layer[n].components for r in reached(c.baseGlyph)}
    covered = lambda name, c: all(disp[c]["shown"][0] - 1e-6 <= lo and hi <= disp[c]["shown"][1] + 1e-6
                                  for lo, hi in _shown(prefix_code, name))
    reaching = sorted(g.name for g in default_layer if g.name not in followers
                      and any(reached(c.baseGlyph) for c in g.components))
    stray = [n for n in reaching if any(not covered(n, r) for c in default_layer[n].components
                                        for r in reached(c.baseGlyph))]
    kept = [n for n in reaching if n not in stray]
    if kept:
        print(f"   ↳ composites kept (shown only where their carrier is the morph): {kept}")
    for name in stray:
        _decompose(fonts, plain, name, lambda n: bool(reached(n)))
    if stray:
        print(f"   ↳ decomposed (would inherit a morph they are not displayed with): {stray}")

    layers, n_glyphs = {}, 0
    for f0, fam in paths.items():
        for X, dx in disp.items():
            if dx["member"] not in fam:
                continue
            hl = _helper_locs(X, dx, fits, f0)
            for loc_key in fam[dx["member"]]["base"]:
                src = source_at(locations[loc_key])
                font = fonts[src.path]
                layer = font.layers[src.layerName] if src.layerName else font.layers.defaultLayer
                base_glyph = layer[X] if X in layer else font.layers.defaultLayer[X]
                vec = _ufo_vector_mixed(base_glyph)
                order, exact = _ufo_rows(base_glyph, paths[f0][dx["member"]]["comps"].get(X))
                gs = paths[f0][dx["member"]]["base"][loc_key][X][order]
                assert np.abs(gs - vec)[exact].max() < 1e-6, f"{X} {loc_key}: UFO and Glyphs drawings differ"
                f = helper_function(X, dx, paths, fits, f0, loc_key)
                vals = [v[order] for v in solve_sources(f, hl)]
                gone = np.array([not e for e in exact])
                if gone.any():                      # a decomposed smart part (t/f's _part.stroke)
                    sf = _stroke_function(X, dx, fits[f0]["windows"], paths[f0][dx["member"]]["forms"],
                                          layer, font.layers.defaultLayer, gone)
                    if sf is not None:
                        for v, sv in zip(vals, solve_sources(sf, hl)):
                            v[gone] = sv
                for h, val in zip(hl, vals):
                    key = (src.path, src.layerName, tuple(h.values()))
                    if key not in layers:
                        lname = "truehoi " + " ".join(f"{v:.6g}" for v in h.values()) + \
                                (f" @{src.layerName}" if src.layerName else "")
                        layers[key] = (font.layers.newLayer(lname), src, h)
                    g = copy.deepcopy(base_glyph)
                    _set_vector_mixed(g, vec + val)
                    layers[key][0].insertGlyph(g, X, overwrite=True, copy=False)
                    n_glyphs += 1
    for (path, _, _), (layer, src, h) in layers.items():
        ds.addSource(SourceDescriptor(filename=src.filename, path=src.path, layerName=layer.name,
                                      name=f"{src.name} {layer.name}",
                                      location={**src.location, **h}))
    print(f"   ✅ true-HOI sources — {len(layers)} helper layers, {n_glyphs} glyph sources, "
          f"carriers {sorted(carriers)}")
    return fits, disp


# ════════════════════════════════════════════════════════════════════════════════════════════════
# six family
# ════════════════════════════════════════════════════════════════════════════════════════════════
DIGIT_HOI = ("six", "six.numr", "six.dnom", "sixsuperior", "sixinferior")   # path leaves with .rclt1-3
SFX = (".rclt1", ".rclt2", ".rclt3")
ANCHOR = ".rclt1"
# Flex true-HOI only. GEOM bands of the added rclt swaps: midpoints of the Phlex timeline (Mark,
# 2026-10-05). Outside them the cmap glyph shows. A member without the band's form keeps its own glyph.
SWAPS = ((10.5, 13.125, ".rclt3"), (13.125, 14.375, ".rclt2"), (14.375, 37, ".rclt1"),
         (37, 39, ".rclt2"), (39, 78, ".rclt3"))
# Phlex holds (phlex._digit_plan_for_master): six | swing + interlace rewind | r1 | forward arc | r3 | swing | six
HOLDS = ((0, phlex.DIGIT_SWING_LOW[0], ""), (15, 36, ANCHOR), (40, phlex.DIGIT_SWING_HIGH[0], ".rclt3"),
         (phlex.DIGIT_SWING_HIGH[1], 100, ""))


# ── GSFont side ───────────────────────────────────────────────────────────────────────────
def members(font, leaf):
    """`leaf` and every glyph built on it (any depth) that has an .rclt1 of its own: nine, six.tf,
    nine.tf, six.lf, nine.lf. {glyph: {suffix: form}} over the suffixes it has ('' = itself)."""
    m0 = font.masters[0].id
    reaches = lambda n: n == leaf or any(reaches(c.name) for c in font.glyphs[n].layers[m0].components)
    return {g.name: {s: g.name + s for s in ("",) + SFX if font.glyphs[g.name + s] is not None}
            for g in font.glyphs if not g.name.endswith(SFX) and font.glyphs[g.name + ANCHOR] is not None
            and reaches(g.name)}


def digit_add_swaps(font, leaves=DIGIT_HOI):
    """Append the SWAPS bands to the VARIATIONS prefix, for every member of every leaf. Returns the
    number of subs. Conditions are user GEOM, as the stock blocks; the GSUB merge bands them."""
    prefix = next(p for p in font.featurePrefixes if p.name == "VARIATIONS")
    fams = [members(font, leaf) for leaf in leaves]
    code, n = ["\n\n# Flex true-HOI only (scripts/lib/hoi_flex.py): six-family swaps"], 0
    for i, (lo, hi, sfx) in enumerate(SWAPS):
        subs = [f"    sub {g} by {forms[sfx]};" for fam in fams for g, forms in fam.items() if sfx in forms]
        n += len(subs)
        code.append(f"conditionset cond_flexhoi_six_{i} {{\n    GEOM {lo:g} {hi:g};\n}} cond_flexhoi_six_{i};\n"
                    f"variation rclt cond_flexhoi_six_{i} {{\n" + "\n".join(subs) + "\n} rclt;")
    prefix.code += "\n\n".join(code) + "\n"
    print(f"   ✅ six-family rclt swaps added (Flex true-HOI only): {n} subs in {len(SWAPS)} GEOM bands")
    return n


def digit_snapshot(font, leaves=DIGIT_HOI):
    """Before the injector runs: each leaf's members, their drawings per location, their layer ids."""
    gi = axis_index(font.axes, "GEOM")
    fams = {leaf: members(font, leaf) for leaf in leaves}
    forms = {fm for fam in fams.values() for fs in fam.values() for fm in fs.values()}
    drawn = {fm: {_layer_key(font, L, gi): _vector(L) for L in font.glyphs[fm].layers
                  if L.associatedMasterId and (L.layerId == L.associatedMasterId
                                               or L.attributes.get("coordinates"))}
             for fm in forms}
    before = {g: {L.layerId for L in font.glyphs[g].layers} for fam in fams.values() for g in fam}
    return dict(fams=fams, drawn=drawn, before=before)


def digit_read_back(font, snap):
    """After phlex.inject_hoi: the braces it added to each member, by location and GEOM. Returns
    {leaf: {member: dict(forms, base={loc: {form: vector}}, knots={loc: [(geom, vector)]})}},
    the followers (every member form) and {loc: {tag: value}}. Members the injector did not brace
    follow their leaf's outline only."""
    gi = axis_index(font.axes, "GEOM")
    tags = [a.axisTag for a in font.axes]
    out, followers, locations = {}, set(), {}
    for leaf, fam in snap["fams"].items():
        out[leaf] = {}
        for g, forms in fam.items():
            followers |= set(forms.values())
            knots = {}
            for L in font.glyphs[g].layers:
                if L.layerId not in snap["before"][g]:
                    knots.setdefault(_layer_key(font, L, gi), []).append(
                        (L.attributes["coordinates"][gi], _vector(L)))
            if not knots:
                assert g != leaf, f"{leaf}: the piecewise injector did not brace it"
                continue
            d = snap["drawn"]
            base = {k: {fm: d[fm].get(k, d[fm][(k[0], _master_axes(font, k[0]))]) for fm in forms.values()}
                    for k in knots}
            out[leaf][g] = dict(forms=forms, base=base,
                                knots={k: sorted(v, key=lambda kv: kv[0]) for k, v in knots.items()})
            locations.update({k: dict(zip(tags, k[1])) for k in knots})
        print(f"   ✅ six-family path read back — {leaf}: braced {sorted(out[leaf])} at "
              f"{len(out[leaf][leaf]['knots'])} locations; members {sorted(fam)}")
    return out, followers, locations


# ── fitting: runs between holds → pieces → per-location polynomials ───────────────────────
def _runs():
    """[(near, far, near hold suffix, far hold suffix)] for each moving run, near = the end nearer
    the default; in order outward on each side."""
    runs = [(a[1], b[0], a[2], b[2]) for a, b in zip(HOLDS, HOLDS[1:])]
    runs = [(hi, lo, sb, sa) if hi <= GEOM_DEFAULT else (lo, hi, sa, sb) for lo, hi, sa, sb in runs]
    return sorted(runs, key=lambda r: (r[0] > GEOM_DEFAULT, abs(r[0] - GEOM_DEFAULT)))


def _displacements(fam, nG):
    """Y[(member, loc)] = {geom: vector}: the Phlex path minus the anchor drawing, corrected per run
    so it starts and lands on the drawings at the hold ends. A member with no drawing of a hold's
    form (six.tf has no .rclt3) holds its own drawing there: Phlex derives composite spacing from
    the r1-baked master, so its nine/six.tf advances run 42u (Regular) to 70u (Bold) under the
    drawings at the six and r3 holds, and six.tf stops being tabular."""
    Y = {}
    for g, d in fam.items():
        for loc, knots in d["knots"].items():
            P = dict(knots)
            A = d["base"][loc][d["forms"][ANCHOR]]

            def held(sfx):
                return d["base"][loc][d["forms"].get(sfx, d["forms"][""])]
            y = {}
            for near, far, sa, sb in _runs():
                kn = sorted((k for k in P if min(near, far) <= k <= max(near, far)),
                            key=lambda k: abs(k - GEOM_DEFAULT))
                assert kn[0] == near and kn[-1] == far, f"{g} {loc}: run {near}-{far} knots {kn}"
                ca, cb = held(sa) - P[near], held(sb) - P[far]
                s0, s1 = _q14(nG(near)), _q14(nG(far))
                for k in kn:
                    t = (_q14(nG(k)) - s0) / (s1 - s0)
                    y[k] = P[k] + ca + (cb - ca) * t - A
            Y[(g, loc)] = y
    return Y


def _digit_order(Y, kn, nG):
    """Lowest order (1-3) fitting the knots kn (outward) at every (member, loc) within ORDER_TOL,
    or None; with the worst knot residual."""
    s = np.array([_q14(nG(k)) for k in kn])
    S = (s - s[0]) / (s[-1] - s[0])
    U = {key: np.stack([y[k] - y[kn[0]] for k in kn]) for key, y in Y.items()}
    for order in (1, 2, 3):
        worst = max(np.abs(_poly(_poly_fit(u, S, order), S[:, None, None]) - u).max() for u in U.values())
        if worst <= ORDER_TOL:
            return order, worst
    return None, None


def fit_digit(leaf, fam, nG):
    """Pieces for one leaf's family, the fewest per run (then the lowest total order), and each
    (member, loc)'s coefficients. Returns dict(pieces=[…], coeffs={(member, loc): [c, …]})."""
    Y = _displacements(fam, nG)
    pieces = []
    for near, far, *_ in _runs():
        kn = sorted((k for k in next(iter(Y.values())) if min(near, far) <= k <= max(near, far)),
                    key=lambda k: abs(k - GEOM_DEFAULT))
        best = {0: ((0, 0), [])}
        for j in range(1, len(kn)):
            for i in range(j):
                if i not in best:
                    continue
                o, worst = _digit_order(Y, kn[i:j + 1], nG)
                if o is None:
                    continue
                cost = (best[i][0][0] + 1, best[i][0][1] + o)
                if j not in best or cost < best[j][0]:
                    best[j] = (cost, best[i][1] + [(kn[i:j + 1], o, worst)])
        for k, o, worst in best[len(kn) - 1][1]:
            pieces.append(dict(g0=k[0], g1=k[-1], s0=_q14(nG(k[0])), s1=_q14(nG(k[-1])), knots=k,
                               order=o, resid=worst))
    coeffs = {}
    for key, y in Y.items():
        for p in pieces:
            s = np.array([_q14(nG(k)) for k in p["knots"]])
            S = (s - s[0]) / (s[-1] - s[0])
            u = np.stack([y[k] - y[p["knots"][0]] for k in p["knots"]])
            coeffs.setdefault(key, []).append(_poly_fit(u, S, p["order"]))
    for p in pieces:
        print(f"   ↳ {leaf} piece {p['g0']:g}–{p['g1']:g} ({len(p['knots'])} knots): order {p['order']}, "
              f"worst knot residual {p['resid']:.2f}u")
    return dict(pieces=pieces, coeffs=coeffs)


def _bands(sfx, nG):
    """The helper-value bands where the Flex-only swaps show form `sfx` (SWAPS, in user GEOM)."""
    return [(_q14(nG(lo)), _q14(nG(hi))) for lo, hi, x in SWAPS if x == sfx]


def digit_helper_function(X, g, d, fit, loc, edges, nG):
    """f_X(s) at `loc`, for form X of member g.

    The cmap glyph carries the whole path, f = Σ_p W_p(q_p(s)) − (X − A)·R(s): renderers that skip
    GSUB show it at every GEOM. A swap form (.rclt1-3) is only ever on screen inside its SWAPS bands,
    so it carries the path there and nothing more. Per side of the default and per band, with e the
    band's edge nearer the default: f = (A − X + Σ_folded T_p)·R_e(s) + Σ_live W_p(q_p(s)), where
    live are the pieces overlapping the band, folded those wholly between the default and e (fully
    travelled by the band), R_e rises 0 → 1 from the default to e. On the band that is exactly M − X;
    at the default it is 0; outside the band the form is not shown. A band holding the default
    (.rclt1's 14.375-37) needs no R: there X is the anchor."""
    co = fit["coeffs"][(g, loc)]
    A = d["base"][loc][d["forms"][ANCHOR]]
    sfx = next(k for k, v in d["forms"].items() if v == X)
    if sfx == "":
        C = d["base"][loc][X] - A

        def f(s):
            v = -C * _ramp(s / (edges[0] if s < 0 else edges[1]))
            for p, c in zip(fit["pieces"], co):
                v = v + _poly(c, _ramp((s - p["s0"]) / (p["s1"] - p["s0"])))
            return v
        return f, digit_helper_locs(fit, edges, nG)
    off = A - d["base"][loc][X]
    sides = []                                       # (sign, e, C, live pieces)
    for b0, b1 in _bands(sfx, nG):
        for sign in (-1, 1):
            lo, hi = (min(b0, b1), max(b0, b1))
            lo, hi = (max(lo, 0.0), hi) if sign > 0 else (lo, min(hi, 0.0))
            if hi <= lo and not (lo == hi == 0):
                continue
            e = lo if sign > 0 else hi                # the edge nearer the default
            live = [(p, c) for p, c in zip(fit["pieces"], co) if p["s0"] * sign > 0
                    and min(p["s0"], p["s1"]) < hi and max(p["s0"], p["s1"]) > lo]
            taken = {id(p) for p, _ in live}
            folded = [c for p, c in zip(fit["pieces"], co) if p["s0"] * sign > 0
                      and abs(p["s1"]) <= abs(e) + 1e-9 and id(p) not in taken]
            C = off + sum((c.sum(0) for c in folded), np.zeros_like(off))
            if abs(e) < 1e-9:
                assert np.abs(C).max() < 1e-6, f"{X}: a band at the default must be the anchor"
            sides.append((sign, e, C, live))

    def f(s):
        v = np.zeros_like(off)
        for sign, e, C, live in sides:
            if s * sign <= 0:
                continue
            if abs(e) > 1e-9:
                v = v + C * _ramp(s / e)
            for p, c in live:
                v = v + _poly(c, _ramp((s - p["s0"]) / (p["s1"] - p["s0"])))
        return v
    # its own helper points: ±1, each side's R edge and its live pieces' ends on GE1M; the diagonals
    # from the start of its first live piece of that order onward, on that side only
    K = {-1.0, 1.0}
    for sign, e, C, live in sides:
        if abs(e) > 1e-9:
            K.add(e)
        K |= {p[k] for p, _ in live for k in ("s0", "s1")}
    locs = [(k,) for k in sorted(K)]
    for order in (2, 3):
        for sign, e, C, live in sides:
            starts = [abs(p["s0"]) for p, _ in live if p["order"] >= order]
            if starts:
                locs += [(k,) * order for k in sorted(K) if k * sign > 0 and abs(k) >= min(starts)
                         and (k,) * order not in locs]
    return f, [dict(zip(HELPERS, h)) for h in locs]


def digit_helper_locs(fit, edges, nG):
    """Every piece end, R's edges (the cmap's two, and each swap band's) and ±1 on GE1M; the (k, k) /
    (k, k, k) diagonals on each side from the start of its first piece of that order onward. One set
    for the whole family."""
    K = {-1.0, 1.0, *edges} | {p[e] for p in fit["pieces"] for e in ("s0", "s1")}
    locs = [(k,) for k in sorted(K)]
    for order in (2, 3):
        for side in (-1, 1):
            starts = [abs(p["s0"]) for p in fit["pieces"] if p["order"] >= order and p["s0"] * side > 0]
            if starts:
                locs += [(k,) * order for k in sorted(K) if k * side > 0 and abs(k) >= min(starts)]
    return [dict(zip(HELPERS, h)) for h in locs]


def solve_sources_signed(f, locs):
    """solve_sources over both sides of the default (helpers −1…1)."""
    model = VariationModel([{}] + locs, axisOrder=HELPERS)
    sups = model.supports[1:]
    S = np.unique(np.concatenate([np.linspace(-1, 1, 801)] + [[l[HELPERS[0]]] for l in locs]))
    phi = np.array([[supportScalar(dict.fromkeys(HELPERS, s), sp) for sp in sups] for s in S])
    F = np.stack([f(s) for s in S])
    shape = F.shape[1:]
    d, *_ = np.linalg.lstsq(phi, F.reshape(len(S), -1), rcond=None)
    resid = np.abs(phi @ d - F.reshape(len(S), -1)).max()
    assert resid < 1e-6, f"helper sources cannot carry this path (diagonal residual {resid:.3g})"
    A = np.array([[supportScalar(model.locations[i], sp) for sp in sups] for i in range(1, len(locs) + 1)])
    vals = (A @ d).reshape(-1, *shape)
    by = {tuple(sorted(model.locations[i].items())): vals[i - 1] for i in range(1, len(locs) + 1)}
    return [by[tuple(sorted({k: v for k, v in l.items() if v}.items()))] for l in locs]


# ── designspace side ─────────────────────────────────────────────────────────────────────
def _flat(layer, default, name, pen, followers):
    """Draw `name` from `layer` (default layer where it has none) with every follower component
    flattened to contours, any depth."""
    g = layer[name] if name in layer else default[name]
    for contour in g:
        contour.draw(pen)
    for c in g.components:
        _flat(layer, default, c.baseGlyph, TransformPen(pen, c.transformation), followers)


def _decompose_deep(fonts, layer_sources, name, followers, deps):
    """_decompose, through nested composites (nine.ss16 → nine.rclt1 → six.rclt1)."""
    for path, layer_name in layer_sources:
        font = fonts[path]
        default = font.layers.defaultLayer
        layer = font.layers[layer_name] if layer_name else default
        if name not in layer and not any(b in layer for b in deps(name)):
            continue
        src = layer[name] if name in layer else default[name]
        g = copy.deepcopy(src)
        g.clearComponents()
        for c in src.components:
            if c.baseGlyph in followers:
                _flat(layer, default, c.baseGlyph, TransformPen(g.getPen(), c.transformation), followers)
            else:
                g.components.append(copy.deepcopy(c))
        layer.insertGlyph(g, name, overwrite=True, copy=False)


def add_digit_hoi(ds, fonts, digits, followers, locations):
    """After add_true_hoi (helper axes present): the six family's sparse helper sources,
    in the same helper layers where they exist. Composites that reach a member form but are not
    one (six.ss16, six.ss17, ⅙ …) are decomposed: they are shown at every GEOM, static in stock."""
    from fontTools.designspaceLib import SourceDescriptor
    geom = next(a for a in ds.axes if a.tag == "GEOM")
    nG = lambda g: ((g - geom.default) / (geom.default - geom.minimum) if g < geom.default
                    else (g - geom.default) / (geom.maximum - geom.default))
    edges = (_q14(nG(HOLDS[1][0])), _q14(nG(HOLDS[1][1])))
    tag_name = {a.tag: a.name for a in ds.axes}
    plain = [s for s in ds.sources if not any(s.location.get(h, 0) for h in HELPERS)]

    def source_at(loc):
        want = {tag_name[t]: v for t, v in loc.items()}
        hits = [s for s in plain if all(abs(s.location.get(n, 0) - v) < 1e-9 for n, v in want.items())]
        assert len(hits) == 1, f"{len(hits)} sources at {loc}"
        return hits[0]

    default_layer = fonts[ds.findDefault().path].layers.defaultLayer
    comps = {g.name: [c.baseGlyph for c in g.components] for g in default_layer if g.components}

    def deps(n):
        return {d for c in comps.get(n, ()) for d in {c} | deps(c)}
    stray = sorted(n for n, cs in comps.items() if n not in followers and any(c in followers for c in cs))
    for name in stray:
        _decompose_deep(fonts, [(s.path, s.layerName) for s in plain], name, followers, deps)
    print(f"   ↳ six family: decomposed {len(stray)} composites shown apart from it: {stray}")

    by_layer = {(s.path, s.layerName): s for s in ds.sources if s.layerName}
    fits, n_glyphs, new = {}, 0, 0
    for leaf, fam in digits.items():
        fit = fits[leaf] = fit_digit(leaf, fam, nG)
        for g, d in fam.items():
            for X in d["forms"].values():
                for loc_key in d["base"]:
                    src = source_at(locations[loc_key])
                    font = fonts[src.path]
                    layer = font.layers[src.layerName] if src.layerName else font.layers.defaultLayer
                    base_glyph = layer[X] if X in layer else font.layers.defaultLayer[X]
                    vec = _ufo_vector(base_glyph)
                    order = (_ufo_order(base_glyph, len(vec) - 1) if len(base_glyph)
                             else list(range(len(vec) - 1))) + [len(vec) - 1]
                    assert np.abs(d["base"][loc_key][X][order] - vec).max() < 1e-6, \
                        f"{X} {loc_key}: UFO and Glyphs drawings differ"
                    f, hl = digit_helper_function(X, g, d, fit, loc_key, edges, nG)
                    for h, val in zip(hl, solve_sources_signed(f, hl)):
                        lname = "truehoi " + " ".join(f"{v:.6g}" for v in h.values()) + \
                                (f" @{src.layerName}" if src.layerName else "")
                        hit = by_layer.get((src.path, lname))
                        if hit is None:
                            hit = by_layer[src.path, lname] = SourceDescriptor(
                                filename=src.filename, path=src.path, layerName=lname,
                                name=f"{src.name} {lname}", location={**src.location, **h})
                            font.layers.newLayer(lname)
                            ds.addSource(hit)
                            new += 1
                        assert hit.location == {**src.location, **h}, f"{lname}: {hit.location}"
                        gl = copy.deepcopy(base_glyph)
                        _set_vector(gl, vec + val[order])
                        font.layers[hit.layerName].insertGlyph(gl, X, overwrite=True, copy=False)
                        n_glyphs += 1
    print(f"   ✅ six-family true-HOI sources — {n_glyphs} glyph sources, {new} new helper layers")
    return fits

# ════════════════════════════════════════════════════════════════════════════════════════════════
# A11y legs below the default (a, l, I)
# ════════════════════════════════════════════════════════════════════════════════════════════════
A11Y_TRUE = ("a", "l", "I")              # leaves Phlex morphs on their A11y leg (a.alt: unused so far)
# I: Phlex braces I.rcltA11y and renames it to I (phlex.handle_I); read back from the renamed glyph, its
# brace layers are the A11y → I path in the same node order. Here nothing is renamed: I keeps the cmap
# and its drawing, I.rcltA11y (shown below GEOM 11) carries the morph, and I.ss18 & co., built on
# I.rcltA11y, are decomposed below so they stay the static serifed I.
A11Y = ".rcltA11y"
# Stock swaps Flex true HOI drops, as Phlex does: the A11y form has a contour the default lacks
# (IJ.rcltA11y draws a J serif), so it cannot carry the morph; IJ morphs through its I instead.
DROP_SWAPS = {("IJ", "IJ.rcltA11y"), ("IJacute", "IJacute.rcltA11y")}


def a11y_drop_swaps(font):
    prefix = next(p for p in font.featurePrefixes if p.name == "VARIATIONS")
    prefix.code = phlex.strip_subs(prefix.code, DROP_SWAPS)
    print(f"   ✅ dropped stock swaps (Flex true HOI, as Phlex): {sorted(DROP_SWAPS)}")
OPSZ_HOLD = {"a.rcltA11y"}               # shown to GEOM 34 at opsz 8 by the stock swap: kept static there


def _swaps(prefix_code):
    """{src: (dst, lo, hi)} for GEOM-only A11y swaps (opsz-conditioned blocks are not GEOM swaps)."""
    conds = {n: (float(lo), float(hi)) for n, lo, hi in
             re.findall(r"conditionset\s+(\w+)\s*\{\s*GEOM\s+(-?[\d.]+)\s+(-?[\d.]+)\s*;\s*\}", prefix_code)}
    out = {}
    for cond, body in re.findall(r"variation\s+rclt\s+(\w+)\s*\{(.*?)\}\s*rclt\s*;", prefix_code, re.DOTALL):
        if cond not in conds:
            continue
        for src, dst in re.findall(r"sub\s+(\S+)\s+by\s+(\S+)\s*;", body):
            if dst.endswith(A11Y):
                out[src] = (dst, *conds[cond])
    return out


# ── GSFont side ───────────────────────────────────────────────────────────────────────────
def a11y_snapshot(font, leaves=A11Y_TRUE):
    """Before the injector: every glyph's layer ids and drawings, for the leaves and whatever
    composite reaches them (follow_composites braces those too)."""
    gi = axis_index(font.axes, "GEOM")
    m0 = font.masters[0].id
    reach = {}

    def reaches(n):
        if n not in reach:
            g = font.glyphs[n]
            reach[n] = n in leaves or bool(g and any(reaches(c.name) for c in g.layers[m0].components))
        return reach[n]
    names = [g.name for g in font.glyphs if reaches(g.name)]
    names += [n + A11Y for n in names if font.glyphs[n + A11Y] is not None]
    drawn = {n: {_layer_key(font, L, gi): _vector(L) for L in font.glyphs[n].layers
                 if L.associatedMasterId and (L.layerId == L.associatedMasterId
                                              or L.attributes.get("coordinates"))}
             for n in set(names)}
    before = {n: {L.layerId for L in font.glyphs[n].layers} for n in set(names)}
    return dict(names=sorted(set(names)), drawn=drawn, before=before)


def a11y_read_back(font, snap, prefix_code, taken=(), leaves=A11Y_TRUE):
    """After phlex.inject_hoi: each braced glyph g (a leaf or a composite of one, not itself an A11y
    form) with its knots below the default, its A11y form X (if the stock swaps it) and the swap
    edge E. Glyphs braced only above the default (a composite of two morphing leaves) are not ours.
    Returns ({g: dict(X, E, window, base, knots)}, followers, locations)."""
    gi = axis_index(font.axes, "GEOM")
    tags = [a.axisTag for a in font.axes]
    swaps = _swaps(prefix_code)
    out, followers, locations = {}, set(), {}
    for g in snap["names"]:
        if g.endswith(A11Y) or g in taken:      # f_f_l, fl …: another true-HOI family carries them
            continue
        knots = {}
        for L in font.glyphs[g].layers:
            c = L.attributes.get("coordinates")
            if L.layerId not in snap["before"][g] and c and float(c[gi]) < 25:
                knots.setdefault(_layer_key(font, L, gi), []).append(
                    (float(L.attributes["coordinates"][gi]), _vector(L)))
        if not knots:
            continue
        X, E = (swaps[g][0], swaps[g][2]) if g in swaps else (None, None)
        m0 = font.masters[0].id
        cg = [c.name for c in font.glyphs[g].layers[m0].components]
        cx = [c.name for c in font.glyphs[X].layers[m0].components] if X else []
        if X is not None and (X not in snap["drawn"] or any(
                snap["drawn"][X][k].shape != v[0][1].shape for k, v in knots.items() if k in snap["drawn"][X])
                or any(x not in (c, c + A11Y) for c, x in zip(cg, cx))):
            # A11y form built differently (lacute.rcltA11y carries acutecomb.case): it stays the stock
            # swap, static; g takes its A11y look from the Phlex path's GEOM-0 frame instead
            X, E = None, None
        d = snap["drawn"]
        forms = [g] + ([X] if X else [])
        base = {k: {fm: d[fm].get(k, d[fm][(k[0], _master_axes(font, k[0]))]) for fm in forms} for k in knots}
        out[g] = dict(X=X, E=E, base=base, knots={k: sorted(v, key=lambda kv: kv[0]) for k, v in knots.items()})
        followers |= set(forms)
        locations.update({k: dict(zip(tags, k[1])) for k in knots})
    print(f"   ✅ A11y legs read back — {len(out)} glyphs: "
          + ", ".join(f"{g}{'→' + v['X'] + f' @{v[chr(69)]:g}' if v['X'] else ''}" for g, v in sorted(out.items())))
    return out, followers, locations


# ── fitting ───────────────────────────────────────────────────────────────────────────────
def _window(d):
    """The moving run of g's knots (first location's geoms): (g0, g1, knot geoms)."""
    kn = next(iter(d["knots"].values()))
    geoms = [g for g, _ in kn]
    step = [max(np.abs(k[i + 1][1] - k[i][1]).max() for k in d["knots"].values()) for i in range(len(geoms) - 1)]
    mv = [i for i, s in enumerate(step) if s > 4.0]
    assert mv and mv == list(range(mv[0], mv[-1] + 1)), f"{geoms}: {step}"
    return geoms[mv[0]], geoms[mv[-1] + 1], geoms[mv[0]:mv[-1] + 2]


def a11y_fit(d, nG):
    """Per location: the window's pieces as (s0, s1, coefficients) — the drawn travel A → D plus
    the Phlex path's deviation from its chord, so it leaves A and lands on D exactly. Split once
    at the best interior knot if no cubic fits."""
    g0, g1, kn = _window(d)
    s = {g: _q14(nG(g)) for g in kn}

    def piece(i, j, loc):
        P = np.stack([v for gg, v in d["knots"][loc] if gg in kn])[i:j + 1]
        S = np.array([(s[g] - s[kn[i]]) / (s[kn[j]] - s[kn[i]]) for g in kn[i:j + 1]])
        A, D = d["base"][loc][d["X"]] if d["X"] else P[0] * 0 + d["knot0"][loc], d["base"][loc][d["g"]]
        a, b = (A if i == 0 else None), (D if j == len(kn) - 1 else None)
        start, end = (a if a is not None else P[0]), (b if b is not None else P[-1])
        chord = P[0] + (P[-1] - P[0]) * S.reshape(-1, 1, 1)
        return S, (end - start) * S.reshape(-1, 1, 1) + (P - chord), start
    best = None
    for cut in [None] + list(range(1, len(kn) - 1)):
        spans = [(0, len(kn) - 1)] if cut is None else [(0, cut), (cut, len(kn) - 1)]
        res, worst = {}, 0.0
        for loc in d["knots"]:
            res[loc] = []
            for i, j in spans:
                S, U, start = piece(i, j, loc)
                for order in (1, 2, 3):
                    c = _poly_fit(U, S, order)
                    w = np.abs(_poly(c, S[:, None, None]) - U).max()
                    if w <= ORDER_TOL:
                        break
                worst = max(worst, w)
                res[loc].append((s[kn[i]], s[kn[j]], c, order, start))
        if best is None or worst < best[0] - 1e-9:
            best = (worst, res)
        if worst <= ORDER_TOL:
            break
    return best[1], best[0], (g0, g1)


def a11y_helper_function(d, pieces, loc, X, sE):
    """f(s) for the cmap glyph (X None) or its A11y form X, at `loc` (see the module doc)."""
    D = d["base"][loc][d["g"]]
    A0 = pieces[0][4]                                   # A at the window's start

    def m(s):
        v = A0 - D
        for s0, s1, c, _, _ in pieces:
            v = v + _poly(c, _ramp((s - s0) / (s1 - s0)))
        return v if s <= 0 else 0 * v
    if X is None:
        return m
    off = D - d["base"][loc][X]
    edge = off + m(sE)

    def f(s):
        if s <= sE:
            return off + m(s)
        return edge * (s / sE) if s < 0 else 0 * edge
    return f


def a11y_helper_locs(pieces_all, sE, order):
    K = {-1.0} | {p[e] for p in pieces_all for e in (0, 1)} | ({sE} if sE is not None else set())
    K = sorted(k for k in K if k < 0)
    locs = [(k,) for k in K]
    for p in (2, 3):
        if order >= p:
            locs += [(k,) * p for k in K]
    return [dict(zip(HELPERS, h)) for h in locs]


# ── designspace side ─────────────────────────────────────────────────────────────────────
def add_a11y_hoi(ds, fonts, legs, followers, locations):
    """After add_true_hoi: the A11y legs' helper sources, in the shared helper layers.
    Composites reaching a leg form that are not themselves carried (lacute: its swap also changes
    the accent) are decomposed, as stock shows them: swapped, static."""
    geom = next(a for a in ds.axes if a.tag == "GEOM")
    nG = lambda g: (g - geom.default) / (geom.default - geom.minimum)
    tag_name = {a.tag: a.name for a in ds.axes}
    plain = [s for s in ds.sources if not any(s.location.get(h, 0) for h in HELPERS)]

    def source_at(loc):
        want = {tag_name[t]: v for t, v in loc.items()}
        hits = [s for s in plain if all(abs(s.location.get(n, 0) - v) < 1e-9 for n, v in want.items())]
        assert len(hits) == 1, f"{len(hits)} sources at {loc}"
        return hits[0]

    default_layer = fonts[ds.findDefault().path].layers.defaultLayer
    comps = {g.name: [c.baseGlyph for c in g.components] for g in default_layer if g.components}

    def deps(n):
        return {d for c in comps.get(n, ()) for d in {c} | deps(c)}
    carried = {n for font in fonts.values() for L in font.layers if L.name.startswith("truehoi ") for n in L.keys()}
    stray = sorted(n for n, cs in comps.items() if n not in followers and n not in carried
                   and any(c in followers for c in cs))        # fl, f_f_l: the f family carries them
    for name in stray:
        _decompose_deep(fonts, [(s.path, s.layerName) for s in plain], name, followers, deps)
    print(f"   ↳ A11y legs: decomposed {len(stray)} composites shown apart from them: {stray}")

    opsz = next(a for a in ds.axes if a.tag == "opsz")
    by_layer = {(s.path, s.layerName): s for s in ds.sources if s.layerName}
    n_glyphs, new, worst_all, skipped = 0, 0, 0.0, set()

    def put(src, h, X, gl_value, base_glyph):
        nonlocal new, n_glyphs
        font = fonts[src.path]
        lname = "truehoi " + " ".join(f"{v:.6g}" for v in h.values()) + (f" @{src.layerName}" if src.layerName else "")
        hit = by_layer.get((src.path, lname))
        if hit is None:
            hit = by_layer[src.path, lname] = SourceDescriptor(
                filename=src.filename, path=src.path, layerName=lname,
                name=f"{src.name} {lname}", location={**src.location, **h})
            font.layers.newLayer(lname)
            ds.addSource(hit)
            new += 1
        assert hit.location == {**src.location, **h}, f"{lname}: {hit.location}"
        gl = copy.deepcopy(base_glyph)
        _set_vector(gl, gl_value)
        font.layers[hit.layerName].insertGlyph(gl, X, overwrite=True, copy=False)
        n_glyphs += 1

    for g, d in sorted(legs.items()):
        d["g"] = g
        d["knot0"] = {loc: kn[0][1] for loc, kn in d["knots"].items()}
        per_loc, worst, (g0, g1) = a11y_fit(d, nG)
        worst_all = max(worst_all, worst)
        order = max(p[3] for ps in per_loc.values() for p in ps)
        sE = _q14(nG(d["E"])) if d["E"] is not None else None
        print(f"   ↳ {g} window {g0:g}–{g1:g}{f', swap {d[chr(69)]:g} → ' + d['X'] if d['X'] else ''}: "
              f"order {order}, worst knot residual {worst:.2f}u")
        for X in [g] + ([d["X"]] if d["X"] else []):
            for loc_key in d["knots"]:
                pieces = per_loc[loc_key]
                hl = a11y_helper_locs(pieces, sE if X != g else None, order)
                f = a11y_helper_function(d, pieces, loc_key, None if X == g else X, sE)
                S = np.linspace(-1, 0, 201)
                if max(np.abs(f(s)).max() for s in S) < 0.01:
                    continue                          # l.rcltA11y: nothing to carry
                src = source_at(locations[loc_key])
                font = fonts[src.path]
                layer = font.layers[src.layerName] if src.layerName else font.layers.defaultLayer
                base_glyph = layer[X] if X in layer else font.layers.defaultLayer[X]
                vec = _ufo_vector(base_glyph)
                order_ix = (_ufo_order(base_glyph, len(vec) - 1) if len(base_glyph)
                            else list(range(len(vec) - 1))) + [len(vec) - 1]
                gv = d["base"][loc_key][X]
                if len(order_ix) != len(gv) or np.abs(gv[order_ix] - vec).max() > 1e-6:
                    skipped.add(X)                    # stored differently in the UFO: left static
                    continue
                vals = solve_sources_signed(f, hl)
                for h, val in zip(hl, vals):
                    put(src, h, X, vec + val[order_ix], base_glyph)
                if X in OPSZ_HOLD:                    # opsz-8 twin: the plain drawing, cancelling the morph
                    corner = {**locations[loc_key], "opsz": opsz.minimum}
                    for h in hl:
                        put(src_opsz(ds, plain, tag_name, corner, fonts), h, X, vec, base_glyph)
    print(f"   ✅ A11y-leg true-HOI sources — {n_glyphs} glyph sources, {new} new helper layers, "
          f"worst knot residual {worst_all:.2f}u" + (f"; left static (UFO ≠ Glyphs): {sorted(skipped)}" if skipped else ""))


def src_opsz(ds, plain, tag_name, loc, fonts):
    """The plain source at an opsz-min corner; made (an empty sparse layer on the master's UFO) if
    the designspace has none there."""
    want = {tag_name[t]: v for t, v in loc.items()}
    hits = [s for s in plain if all(abs(s.location.get(n, 0) - v) < 1e-9 for n, v in want.items())]
    if hits:
        return hits[0]
    master = min(plain, key=lambda s: sum(abs(s.location.get(n, 0) - v) for n, v in want.items() if n != tag_name["opsz"]))
    lname = "a11y opsz " + " ".join(f"{v:g}" for v in loc.values())
    src = SourceDescriptor(filename=master.filename, path=master.path, layerName=lname,
                           name=f"{master.name} {lname}", location=dict(want))
    if lname not in fonts[master.path].layers:
        fonts[master.path].layers.newLayer(lname)
    ds.addSource(src)
    plain.append(src)
    return src
