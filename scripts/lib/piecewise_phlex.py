"""HOI / variable-morph injection (GEOM glyph morphing for Cal Sans Flex), factored out of reference/dev-scripts/hoi_calsans.py so
the build pipeline can call it. `inject_hoi(font, geom_i)` mutates a prepared glyphsLib GSFont in
place: it morphs chosen conditionset glyphs by injecting GEOM brace layers (linear leaf-morphs +
y/6/9 HOI sweeps + curated C/M/I) and strips those glyphs' `sub` rules from the VARIATIONS prefix.

These morphs ship Flex-family only — see scripts/lib/build_flex.py. The standalone A/B proofing
harness is reference/dev-scripts/hoi_calsans.py (imports from here).
"""
import copy
import math
import re
import unicodedata
import uuid

from glyphsLib import glyphdata
from glyphsLib.types import Point

from scripts.lib.prepare import _clone_layer, _is_top_mark
from scripts.lib.utils import axis_index

# ── tuning knobs (config-driven, per-glyph) ───────────────────────────────────
BASE_WIN = (35, 40)
GEO_WIN = (75, 80)
AXIS_MAX = 100
OPEN = 32767              # conditionset "to axis max" sentinel
HOI_STRENGTH = 0.3        # 6/9 forward arc sweep: 0 = straight, 1 = full parabola
INTERLACE_STRENGTH = 0.3  # 6/9 interlace rewind arc (swept opposite the forward sweep)
SWEEP_MAX = 1.2           # 6/9 back-transition (r3→six) overshoot at full strength
DIGIT_HOOK = 0.6          # 6/9 transient r1→r2 hook (curviest→semi), 0 = none
Y_SWEEP = 0.9             # y Geo-window HOI sweep: 1.0 = straight, <1 swings out, >1 up-and-over
Y_TWIST = -9.5            # y mid-swing: rotate left foot edge (22-23) about foot centroid (toward crotch)
Y_FOOT_NUDGE = {22: (-1.0, -3.9), 23: (8.6, 1.5)}  # mid-swing node nudges (font units; dialed on 10 Regular)
HOI_SWEEP = {"tpart.comb": 1.2,   # t  (opposite swing)
             "jdotless":   0.8}   # j  (swing out)   — f stays fully linear (not listed)
# Nodes held OUT of the sweep, by leaf, in SOURCE node order (the order _sweep_path matches
# form-to-form; not the compiled glyf point numbers, which cu2qu renumbers). The sweep is for
# terminals that travel — t's foot retracts 429–562 units into the stem — and a stem has no
# business being swung perpendicular to itself: tpart's 9–12 are the stem's own corners
# (484/202 x, 352→1360 y), so they interpolate straight while the foot still swings.
HOI_SWEEP_SKIP = {"tpart.comb": frozenset({9, 10, 11, 12})}

# Underware's demo draws one arc per EDGE of a stroke, not one path applied to every node.
# _sweep offsets each node along its own normal, scaled by its own travel, so the two edges of
# six's tail move by different amounts: the stroke measures 194u mid-arc where no drawn form
# exceeds 180u, and waists to 161u where none is thinner than 167u. DIGIT_RUNGS names the tail's
# opposing edges instead — read off the drawing, which runs up 12,13,14, caps at 15,16 and comes
# back down 17,18,19 — so the morph moves a RUNG, swinging its centre about the hinge, and the
# two edges cannot drift apart. Node numbers are source (PostScript) indices.
DIGIT_RUNGS = {"six": dict(pairs=[(15, 16), (14, 17), (13, 18), (12, 19),
                                  (11, 20), (10, 21), (9, 22)],
                           hinge=(9, 22), open_tip=2.5, open_hinge=1.0)}

# y and jdotless are the same shape of problem as six's tail: a descender hook retracting into the
# stem, whose two edges bunch and cross mid-swing because each node is swept on its own normal.
# Pairs run tip → hinge; the hinge is the stem's own cross-section, which barely moves while the
# tip travels 250-420u. Node numbers are source (PostScript) indices.
HOOK_RUNGS = {"y":        dict(pairs=[(22, 23), (21, 24), (20, 25), (19, 26),
                                      (18, 0), (17, 1), (16, 2)], hinge=(16, 2),
                           keep_straight=True),
              "jdotless": dict(pairs=[(11, 12), (10, 13), (9, 14), (8, 15),
                                      (7, 0), (6, 1), (5, 2)], hinge=(5, 2),
                           keep_straight=True),
              # λ is y drawn upside down, contour reversed: λ node j is y node (25 - j) % 27
              "lambda":   dict(pairs=[(3, 2), (4, 1), (5, 0), (6, 26),
                                      (7, 25), (8, 24), (9, 23)], hinge=(9, 23),
                           keep_straight=True)}
# Glyphs that swap wherever another does: the source has no swaps of their own for them (λ's
# .rcltBase/.rcltGeo are drawn but unwired). add_follower_swaps copies the leader's subs (Flex only).
SWAP_FOLLOWERS = {"lambda": "y"}


def add_follower_swaps(font):
    """For each SWAP_FOLLOWERS pair, add `sub F by F.sfx;` to every variation block holding
    `sub L by L.sfx;`, so F swaps at exactly L's GEOM thresholds."""
    prefix = next(p for p in font.featurePrefixes if p.name == "VARIATIONS")
    n = 0
    for f, lead in SWAP_FOLLOWERS.items():
        def add(m):
            nonlocal n
            sfx, form = m.group(2), f + m.group(2)
            if font.glyphs[f] is None or font.glyphs[form] is None:
                return m.group(0)
            n += 1
            return f"{m.group(0)}\n{m.group(1)}sub {f} by {form};"
        prefix.code = re.sub(rf"^([ \t]*)sub {re.escape(lead)} by {re.escape(lead)}(\.\S+);",
                             add, prefix.code, flags=re.M)
    print(f"   ✅ follower swaps added (Flex only): {n} — {SWAP_FOLLOWERS}")
    return n
# A rung's thickness must reach the drawn value at both ends, but marching there linearly fattens
# the stroke through the middle: at `six` the tail HAS become the bowl, so 12/19 measures 405u
# across open counter rather than any stroke weight. `open` holds the drawn weight and opens late.
# It cannot be one number for the whole tail — 1 reads right at the hinge (the bowl's left flank)
# and 2.5 at the tip, and forcing the tip's value on the hinge crushes the left side into the
# counter — so it tapers, tip to hinge.
# The small sixes — six.numr, six.dnom, sixsuperior, sixinferior and their .rclt1-3 — are drawn
# with exactly six's structure (38 nodes, same on/off order, contours [26, 12]), so six's pairing
# applies to them verbatim. They were keyed out only because the lookup is by exact name.
def _digit_rungs(base):
    return DIGIT_RUNGS.get(base) or (DIGIT_RUNGS.get("six") if base.startswith("six") else None)


# The six↔r3 swing is authored ONCE and emitted at both ends of the axis. It used to exist only
# at the top (77-80); at the bottom GEOM 12 held `six` and 12.5 held r3 with nothing between, so
# the same transition ran eight times faster as an accident of two adjacent holds.
DIGIT_SWING_LOW = (8.5, 12.5)   # six → r3, ending where the interlace rewind begins
DIGIT_SWING_HIGH = (76, 80)     # r3 → six
DIGIT_SWING_KNOTS = 8           # braces per swing; 4 left visible facets mid-window
DIGIT_SWING_EASE = False        # the swing's t stays linear; knot count is what buys smoothness


def _ease(u):
    """Identity unless DIGIT_SWING_EASE. Easing t makes the swing leave and arrive at rest, which
    is a different motion, not a smoother one — the visible stepping is the brace count cutting
    chords across the arc, and DIGIT_SWING_KNOTS is the knob for that."""
    return u * u * (3 - 2 * u) if DIGIT_SWING_EASE else u

# ── A11y morph (GEOM 0-11/13 forms) ───────────────────────────────────────────
# The A11y drawings (curved-tail l, spurred a) are substituted at the BOTTOM of GEOM and swap
# out by 11 (13 for a). Morph them across this window instead of hard-swapping. Unlike
# handle_I, the braces go on the DEFAULT glyph: its masters all sit at GEOM 25 holding the
# default outline, which is what is wanted there, so nothing competes and no rename is needed.
A11Y_WIN = (5, 8)                  # default morph window
# Per-LEAF window override. a and l are staggered rather than sharing one: a goes first, at the
# point six begins its own morph, and l follows once a has landed, so the two are never mid-swing
# together in a word like "all".
# ldot is listed separately because it is its own leaf: lacute/lslash/ldotbelow all resolve
# down to `l` and inherit its window, but ldot draws the stem itself, so without an entry it
# falls through to A11Y_WIN and morphs at 5-8 while l waits until 13.
A11Y_WINDOW = {"a": (10, 13), "l": (13, 15), "ldot": (13, 15)}


def _a11y_window(leaf):
    """The leaf's A11y window, by exact name (a.alt keeps its own early 5-8 window, by design)."""
    return A11Y_WINDOW.get(leaf, A11Y_WIN)
A11Y_SKIP_BASES = {"I"}            # I is role-flipped by handle_I; leave it alone
# Per-leaf model for the A11y leg. "stroke" pairs the outer contour against the inner one and
# swings the CENTRELINE, holding the drawn stroke weight (a per-node morph thins it to a sliver);
# hinge_k > 1 keeps the stem junction low for longer. "sweep" is the plain perpendicular bulge.
A11Y_MODEL = {
    "l": dict(kind="stroke",
              pairs=[(12, 9), (13, 8), (14, 7), (15, 6), (0, 5), (1, 4), (2, 3)],
              hinge=(12, 9), hinge_k=2.4),
    "a": dict(kind="sweep", sweep=1.1,
              skip=frozenset(set(range(46)) - {5, 6, 7, 8})),
}

HOI_BASES = {"y"}
HOI_NAMES = {"six", "nine"}


# ── grouping / conditionset parsing ───────────────────────────────────────────
def _nodes(layer):
    return [n for path in layer.paths for n in path.nodes]


def base_of(name):
    """Base letter for grouping — NFD-decompose the glyph's unicode (yacute→y, tcaron→t),
    special-casing dotless j. Uppercase stays uppercase (C→C)."""
    root = name.split(".")[0]
    if root == "jdotless":
        return "j"
    u = glyphdata.get_glyph(root).unicode
    if u:
        return unicodedata.normalize("NFD", chr(int(u, 16)))[0]
    return root


def group_of(name):
    base_form = base_of(name)
    if base_form in HOI_BASES or name.split(".")[0] in HOI_NAMES:
        return "hoi"
    if base_form.isupper():     # uppercase → discrete GSUB swap
        return "discrete"
    return "linear"             # lowercase + digits → morph


def parse_variations(code):
    """glyph → (target, lo, hi) for the Base, Geo and A11y substitutions. A finite Base window
    (f: 39–76) means return-to-default; open (…32767) means stay. A11y windows sit at the bottom
    of the axis (l: 0–11, a: 0–13) and are morphed by _inject_a11y_braces, not timeline_for."""
    conds = {n: (int(lo), int(hi)) for n, lo, hi in
             re.findall(r"conditionset\s+(\w+)\s*\{\s*GEOM\s+(-?\d+)\s+(-?\d+)\s*;\s*\}", code)}
    base, geo, a11y = {}, {}, {}
    for cond, body in re.findall(r"variation\s+rclt\s+(\w+)\s*\{(.*?)\}\s*rclt\s*;", code, re.DOTALL):
        lo, hi = conds.get(cond, (0, OPEN))
        for source, target in re.findall(r"sub\s+(\S+)\s+by\s+(\S+)\s*;", body):
            bucket = (base if target.endswith(".rcltBase") else
                      geo if target.endswith(".rcltGeo") else
                      a11y if target.endswith(".rcltA11y") else {})
            bucket[source] = (target, lo, hi)
    return base, geo, a11y


def timeline_for(default_form, base_entry, geo_entry):
    """(geom, form_glyph) knots across the two herald windows."""
    knots, current_form = [], default_form
    if base_entry:
        knots += [(BASE_WIN[0], current_form), (BASE_WIN[1], base_entry[0])]
        current_form = base_entry[0]
    if geo_entry:
        knots += [(GEO_WIN[0], current_form), (GEO_WIN[1], geo_entry[0])]
        current_form = geo_entry[0]
    elif base_entry and base_entry[2] < OPEN:     # finite Base → morph back to default
        knots += [(GEO_WIN[0], current_form), (GEO_WIN[1], default_form)]
        current_form = default_form
    knots.append((AXIS_MAX, current_form))
    return knots


def collect(font, name, timeline, out, composites=None):
    """Resolve `name` morphing through `timeline` down to PATH leaves, filling out[leaf]=leaf_timeline.
    Recurses composites to the components that differ. Returns False on any incompatibility.
    With `composites`, also records every composite passed through (composites[name]=timeline): its
    advance and mark offsets have to follow the leaf, which the leaf's braces cannot do for them."""
    g = font.glyphs[name]
    if g is None:
        return False
    L0 = g.layers[font.masters[0].id]
    if L0.paths and not L0.components:                 # a path leaf to morph
        if name in out:
            return True
        for m in font.masters:
            n = len(_nodes(g.layers[m.id]))
            for _, form in timeline:
                fg = font.glyphs[form]
                if fg is None or fg.layers[m.id] is None or len(_nodes(fg.layers[m.id])) != n:
                    return False
        out[name] = timeline
        return True
    if L0.components:                                  # composite → recurse leaves
        if composites is not None:
            composites.setdefault(name, timeline)
        for i in range(len(L0.components)):
            leaf_tl, base_leaf = [], L0.components[i].name
            for geom, form in timeline:
                comps = font.glyphs[form].layers[font.masters[0].id].components
                if i >= len(comps):
                    return False
                leaf_tl.append((geom, comps[i].name))
            if all(leaf == base_leaf for _, leaf in leaf_tl):
                continue
            if not collect(font, base_leaf, leaf_tl, out, composites):
                return False
        return True
    return False


# ── interpolation primitives ──────────────────────────────────────────────────
def _sweep(p0, p1, t, sweep):
    """Swept (parabolic) interpolation p0→p1 — a perpendicular overshoot peaking mid-transition
    (sweep 1.0 = straight line)."""
    lx, ly = (1 - t) * p0[0] + t * p1[0], (1 - t) * p0[1] + t * p1[1]
    dx, dy = p1[0] - p0[0], p1[1] - p0[1]
    d = math.hypot(dx, dy)
    if d == 0:
        return (lx, ly)
    nx, ny = -dy / d, dx / d
    off = d * (sweep - 1.0) * 4 * t * (1 - t)
    return (lx + nx * off, ly + ny * off)


def _rung_centres(pts, pairs):
    return [((pts[o][0] + pts[i][0]) / 2, (pts[o][1] + pts[i][1]) / 2) for o, i in pairs]


def _rung_perp(cen):
    """Perpendicular to the stroke at each rung, from the centreline's local tangent.

    `pairs` runs tip → hinge, so a central difference along the chain IS the stroke direction.
    """
    out = []
    for j in range(len(cen)):
        a = cen[max(j - 1, 0)]
        b = cen[min(j + 1, len(cen) - 1)]
        vx, vy = a[0] - b[0], a[1] - b[1]
        out.append(math.atan2(-vx, vy))
    return out


def _rung_dev(pts, pairs):
    """How far each drawn rung sits off perpendicular — carried, not re-derived."""
    perp = _rung_perp(_rung_centres(pts, pairs))
    dev = []
    for j, (o, i) in enumerate(pairs):
        a = math.atan2(pts[o][1] - pts[i][1], pts[o][0] - pts[i][0])
        dev.append((a - perp[j] + math.pi) % (2 * math.pi) - math.pi)
    return dev


def _rung_swing(p0, p1, t, pairs, hinge, types, smooth, contours,
                open_tip=1.0, open_hinge=1.0, slaved=True, keep_straight=False):
    """Swing a stroke from p0 to p1 by moving RUNGS, not nodes.

    Each rung (a pair of opposing edge nodes) has its centre expressed in polar coordinates about
    the hinge; radius and angle interpolate independently, and the two edges are re-planted either
    side of the moved centre at the interpolated thickness and direction. The rotation sense is
    whatever the drawings state — six's tip swings +15 deg while its inner rungs counter-rotate
    -6 deg, which no single perpendicular offset can express. Nodes outside `pairs` interpolate
    linearly; they travel under 90u and go straight anyway.

    G1 is enforced afterwards because three adjacent nodes can sit in three different rungs, each
    on its own arc: without it node 12's tangent kinks by 12 degrees mid-swing.
    """
    out = [((1 - t) * a[0] + t * b[0], (1 - t) * a[1] + t * b[1]) for a, b in zip(p0, p1)]
    ha = ((p0[hinge[0]][0] + p0[hinge[1]][0]) / 2, (p0[hinge[0]][1] + p0[hinge[1]][1]) / 2)
    hb = ((p1[hinge[0]][0] + p1[hinge[1]][0]) / 2, (p1[hinge[0]][1] + p1[hinge[1]][1]) / 2)
    H = (ha[0] + (hb[0] - ha[0]) * t, ha[1] + (hb[1] - ha[1]) * t)
    last = max(len(pairs) - 1, 1)
    if slaved:
        # Interpolating a rung's own angle lets the terminal cut drift off perpendicular mid-leg,
        # which is what points 15/16. Derive the cut from the stroke instead and interpolate only
        # the drawn deviation from it: at t=0 and t=1 that reproduces the drawing exactly.
        dev0, dev1 = _rung_dev(p0, pairs), _rung_dev(p1, pairs)
        moved = []
        for j, (o, i) in enumerate(pairs):
            ca = ((p0[o][0] + p0[i][0]) / 2 - ha[0], (p0[o][1] + p0[i][1]) / 2 - ha[1])
            cb = ((p1[o][0] + p1[i][0]) / 2 - hb[0], (p1[o][1] + p1[i][1]) / 2 - hb[1])
            ra, rb = math.hypot(*ca), math.hypot(*cb)
            tha, thb = math.atan2(ca[1], ca[0]), math.atan2(cb[1], cb[0])
            dth = (thb - tha + math.pi) % (2 * math.pi) - math.pi
            th, r = tha + dth * t, ra + (rb - ra) * t
            moved.append((H[0] + r * math.cos(th), H[1] + r * math.sin(th)))
        perp = _rung_perp(moved)
    for j, (o, i) in enumerate(pairs):
        op = open_tip + (open_hinge - open_tip) * (j / last)
        ca = ((p0[o][0] + p0[i][0]) / 2 - ha[0], (p0[o][1] + p0[i][1]) / 2 - ha[1])
        cb = ((p1[o][0] + p1[i][0]) / 2 - hb[0], (p1[o][1] + p1[i][1]) / 2 - hb[1])
        ra, rb = math.hypot(*ca), math.hypot(*cb)
        tha, thb = math.atan2(ca[1], ca[0]), math.atan2(cb[1], cb[0])
        dth = (thb - tha + math.pi) % (2 * math.pi) - math.pi
        th, r = tha + dth * t, ra + (rb - ra) * t
        C = (H[0] + r * math.cos(th), H[1] + r * math.sin(th))
        ua = (p0[o][0] - p0[i][0], p0[o][1] - p0[i][1])
        ub = (p1[o][0] - p1[i][0], p1[o][1] - p1[i][1])
        ta, tb = math.hypot(*ua), math.hypot(*ub)
        pa, pb = math.atan2(ua[1], ua[0]), math.atan2(ub[1], ub[0])
        dp = (pb - pa + math.pi) % (2 * math.pi) - math.pi
        W = ta + (tb - ta) * (t ** op)
        if slaved:
            C = moved[j]
            dd = (dev1[j] - dev0[j] + math.pi) % (2 * math.pi) - math.pi
            ph = perp[j] + dev0[j] + dd * t
        else:
            ph = pa + dp * t
        ox, oy = math.cos(ph) * W / 2, math.sin(ph) * W / 2
        out[o] = (C[0] + ox, C[1] + oy)
        out[i] = (C[0] - ox, C[1] - oy)
    out = _enforce_g1(out, types, smooth, contours)
    return _keep_straight(out, p0, p1, t, types, smooth, contours) if keep_straight else out


def _keep_straight(pts, p0, p1, t, types, smooth, contours, tol=2.0):
    """A curve segment that is a straight line in BOTH drawings stays one in between. Its two
    handles sit on different rungs, each planted at its own thickness, so mid-swing they leave the
    chord by different amounts (y's tip edge 19→22: 7u and 1u) and the edge wiggles. Put them back
    at their interpolated place along the chord and their interpolated (sub-`tol`) distance off
    it, so both drawings are still reproduced exactly; a smooth end node then takes its tangent
    from the straight edge, as it would from a line, so its other handle turns to stay collinear."""
    out = list(pts)

    def along(q, a, b):                 # per handle: (fraction along a→b, distance off it)
        dx, dy = q[b][0] - q[a][0], q[b][1] - q[a][1]
        L = math.hypot(dx, dy) or 1.0
        return [(((q[k][0] - q[a][0]) * dx + (q[k][1] - q[a][1]) * dy) / (L * L),
                 ((q[k][0] - q[a][0]) * dy - (q[k][1] - q[a][1]) * dx) / L) for k in (a + 1, a + 2)]

    start = 0
    for n in contours:
        idx = lambda k: start + k % n
        for k in range(n):
            a, h1, h2, b = idx(k), idx(k + 1), idx(k + 2), idx(k + 3)
            if h2 != a + 2 or types[a] == "offcurve" or types[b] == "offcurve" \
                    or types[h1] != "offcurve" or types[h2] != "offcurve":
                continue                # not a curve segment, or it wraps the contour start
            f0, f1 = along(p0, a, b), along(p1, a, b)
            if max(abs(d) for _, d in f0 + f1) > tol:
                continue
            dx, dy = out[b][0] - out[a][0], out[b][1] - out[a][1]
            L = math.hypot(dx, dy) or 1.0
            for h, (u0, d0), (u1, d1) in zip((h1, h2), f0, f1):
                u, off = u0 + (u1 - u0) * t, d0 + (d1 - d0) * t
                out[h] = (out[a][0] + dx * u + dy / L * off, out[a][1] + dy * u - dx / L * off)
            for node, inner, outer in ((a, h1, idx(k - 1)), (b, h2, idx(k + 4))):
                if smooth[node] and types[outer] == "offcurve":
                    dx, dy = out[node][0] - out[inner][0], out[node][1] - out[inner][1]
                    d = math.hypot(dx, dy)
                    if d:
                        L = math.hypot(out[outer][0] - out[node][0], out[outer][1] - out[node][1])
                        out[outer] = (out[node][0] + dx / d * L, out[node][1] + dy / d * L)
        start += n
    return out


def _scalar3(a, m_, b, t, strength):
    """Scalar version of _arc3 — piecewise-linear blended toward the Lagrange parabola."""
    pw = a + (m_ - a) * (t / 0.5) if t <= 0.5 else m_ + (b - m_) * ((t - 0.5) / 0.5)
    l0, l1, l2 = 2 * (t - .5) * (t - 1), -4 * t * (t - 1), 2 * t * (t - .5)
    return pw + (l0 * a + l1 * m_ + l2 * b - pw) * strength


def _rung_arc3(p0, pm, p1, t, pairs, hinge, types, smooth, contours, strength,
               hook=0.0, open_tip=1.0, open_hinge=1.0):
    """The forward arc r1→r2→r3, moved as rungs rather than nodes.

    Same three drawn forms and the same parabola as _arc3, but a rung's radius, angle, thickness
    and edge direction about the hinge each take the arc, so the stroke's two edges cannot pick up
    different amplitudes. That per-node scaling is what made the tail measure 194u mid-arc where
    no drawing exceeds 180u, and what made DIGIT_HOOK distort the stroke instead of just delaying
    it — the hook is applied to the rung's CENTRE here, so both edges carry it together.
    """
    out = [_arc3(p0[i], pm[i], p1[i], t, strength) for i in range(len(p0))]
    hs = [((q[hinge[0]][0] + q[hinge[1]][0]) / 2,
           (q[hinge[0]][1] + q[hinge[1]][1]) / 2) for q in (p0, pm, p1)]
    H = _arc3(hs[0], hs[1], hs[2], t, strength)
    last = max(len(pairs) - 1, 1)
    for j, (o, i) in enumerate(pairs):
        op = open_tip + (open_hinge - open_tip) * (j / last)
        rs, ths, ws, phs = [], [], [], []
        for q, h in zip((p0, pm, p1), hs):
            c = ((q[o][0] + q[i][0]) / 2 - h[0], (q[o][1] + q[i][1]) / 2 - h[1])
            u = (q[o][0] - q[i][0], q[o][1] - q[i][1])
            rs.append(math.hypot(*c)); ths.append(math.atan2(c[1], c[0]))
            ws.append(math.hypot(*u)); phs.append(math.atan2(u[1], u[0]))
        for seq in (ths, phs):                                   # unwrap so the arc takes the
            for k in (1, 2):                                     # short way round, like the swing
                seq[k] = seq[k - 1] + ((seq[k] - seq[k - 1] + math.pi) % (2 * math.pi) - math.pi)
        r = _scalar3(rs[0], rs[1], rs[2], t, strength)
        th = _scalar3(ths[0], ths[1], ths[2], t, strength)
        ph = _scalar3(phs[0], phs[1], phs[2], t, strength)
        W = _scalar3(ws[0], ws[1], ws[2], t ** op, strength)
        C = [H[0] + r * math.cos(th), H[1] + r * math.sin(th)]
        if hook and t < 0.5:                                     # transient r1→r2 hook, on the centre
            s_ = t / 0.5
            bump = hook * 4 * s_ * (1 - s_)
            c0 = ((p0[o][0] + p0[i][0]) / 2, (p0[o][1] + p0[i][1]) / 2)
            c1 = ((pm[o][0] + pm[i][0]) / 2, (pm[o][1] + pm[i][1]) / 2)
            C[0] += (c0[0] - c1[0]) * bump
            C[1] += (c0[1] - c1[1]) * bump
        ox, oy = math.cos(ph) * W / 2, math.sin(ph) * W / 2
        out[o] = (C[0] + ox, C[1] + oy)
        out[i] = (C[0] - ox, C[1] - oy)
    return _enforce_g1(out, types, smooth, contours)


def _stroke_path(p0, p1, t, pairs, hinge, hinge_k, types, smooth, contours):
    """Constant-weight stroke morph: pair the outer contour against the inner one, swing the
    CENTRELINE about the hinge and re-offset both edges by the interpolated thickness.

    A per-node morph collapses a stroke that is retracting into a stem — the two edges sit at
    different radii from any pivot, so rotating them converges the gap and the foot becomes a
    sliver. Pairing them keeps the drawn weight: l's thickness is 158-203 in the A11y form and
    176-201 in the target, so it should never thin at all, and the centreline is what actually
    turns (-35 deg to -90 deg over the window). hinge_k > 1 holds the stem junction low longer.

    Nodes not named in `pairs` interpolate linearly. Endpoints are exact at t=0 and t=1.
    """
    out = [((1 - t) * q0[0] + t * q1[0], (1 - t) * q0[1] + t * q1[1]) for q0, q1 in zip(p0, p1)]
    hi_a = ((p0[hinge[0]][0] + p0[hinge[1]][0]) / 2, (p0[hinge[0]][1] + p0[hinge[1]][1]) / 2)
    hi_b = ((p1[hinge[0]][0] + p1[hinge[1]][0]) / 2, (p1[hinge[0]][1] + p1[hinge[1]][1]) / 2)
    ht = t ** hinge_k
    H = (hi_a[0] + (hi_b[0] - hi_a[0]) * ht, hi_a[1] + (hi_b[1] - hi_a[1]) * ht)
    for o, i in pairs:
        ca = ((p0[o][0] + p0[i][0]) / 2, (p0[o][1] + p0[i][1]) / 2)
        cb = ((p1[o][0] + p1[i][0]) / 2, (p1[o][1] + p1[i][1]) / 2)
        va = (ca[0] - hi_a[0], ca[1] - hi_a[1])
        vb = (cb[0] - hi_b[0], cb[1] - hi_b[1])
        ra, rb = math.hypot(*va), math.hypot(*vb)
        tha, thb = math.atan2(va[1], va[0]), math.atan2(vb[1], vb[0])
        dth = (thb - tha + math.pi) % (2 * math.pi) - math.pi
        th, r = tha + dth * t, ra + (rb - ra) * t
        C = (H[0] + r * math.cos(th), H[1] + r * math.sin(th))
        ua = (p0[o][0] - p0[i][0], p0[o][1] - p0[i][1])
        ub = (p1[o][0] - p1[i][0], p1[o][1] - p1[i][1])
        ta, tb = math.hypot(*ua), math.hypot(*ub)
        pa_, pb_ = math.atan2(ua[1], ua[0]), math.atan2(ub[1], ub[0])
        dp = (pb_ - pa_ + math.pi) % (2 * math.pi) - math.pi
        ph, T = pa_ + dp * t, ta + (tb - ta) * t
        ox, oy = math.cos(ph) * T / 2, math.sin(ph) * T / 2
        out[o] = (C[0] + ox, C[1] + oy)
        out[i] = (C[0] - ox, C[1] - oy)
    return _enforce_g1(out, types, smooth, contours)


def _enforce_g1(pts, types, smooth, contours):
    """G1 continuity enforcer. Linear interpolation of handle *positions* doesn't preserve the
    tangent *angle*, so a node the designer marked SMOOTH can develop a kink mid-sweep. For each
    smooth on-curve node, derive one tangent and snap its handle(s) onto it, preserving handle
    lengths: with two handles, average the in/out directions; with a line on one side, that line's
    direction fixes the tangent and only the curve-side handle moves. Corner nodes are untouched."""
    out = list(pts)
    contour_start = 0
    for contour_len in contours:
        for k in range(contour_len):
            i = contour_start + k
            if types[i] == "offcurve" or not smooth[i]:
                continue
            prev_idx = contour_start + (k - 1) % contour_len
            next_idx = contour_start + (k + 1) % contour_len
            has_in, has_out = types[prev_idx] == "offcurve", types[next_idx] == "offcurve"
            if not (has_in or has_out):
                continue
            P = out[i]
            din = (P[0] - out[prev_idx][0], P[1] - out[prev_idx][1])     # direction arriving at P
            dout = (out[next_idx][0] - P[0], out[next_idx][1] - P[1])    # direction leaving P
            def _unit(v):
                d = math.hypot(*v); return (v[0] / d, v[1] / d) if d else (0.0, 0.0)
            if has_in and has_out:                            # curve↔curve: average both
                ux, uy = _unit(din); vx, vy = _unit(dout); tx, ty = ux + vx, uy + vy
            elif has_out:                                     # line on the in side fixes the tangent
                tx, ty = din
            else:                                             # line on the out side
                tx, ty = dout
            tl = math.hypot(tx, ty)
            if tl == 0:
                continue
            tx, ty = tx / tl, ty / tl
            if has_in:
                L = math.hypot(P[0] - out[prev_idx][0], P[1] - out[prev_idx][1])
                out[prev_idx] = (P[0] - tx * L, P[1] - ty * L)
            if has_out:
                L = math.hypot(out[next_idx][0] - P[0], out[next_idx][1] - P[1])
                out[next_idx] = (P[0] + tx * L, P[1] + ty * L)
        contour_start += contour_len
    return out


def _sweep_path(p0, p1, types, smooth, contours, t, sweep, skip=()):
    """Sweep a whole node list, computing the perpendicular swing (see _sweep) on ON-CURVE nodes
    ONLY. Each OFF-CURVE handle does NOT swing on its own chord — it borrows the exact (dx, dy)
    shift of the on-curve node it belongs to (the adjacent on-curve node within its contour:
    the previous one for an outgoing handle, the next for an incoming one). This keeps each
    curve segment rigid through the sweep instead of warping its curvature. `contours` is the
    per-contour node count so ownership wraps within a contour, not across the flat list.
    Smooth nodes are then re-collinearized via _enforce_g1 (the linear blend breaks tangents)."""
    def lin(i):
        return ((1 - t) * p0[i][0] + t * p1[i][0], (1 - t) * p0[i][1] + t * p1[i][1])
    on = [ty != "offcurve" for ty in types]
    out = [None] * len(p0)
    contour_start = 0
    for contour_len in contours:
        idx = range(contour_start, contour_start + contour_len)
        shift = {}
        for i in idx:
            if on[i]:
                # A skipped node interpolates straight; its handles inherit the zero shift below,
                # so the segments it owns travel linearly with it.
                bx, by = lin(i) if i in skip else _sweep(p0[i], p1[i], t, sweep)
                lx, ly = lin(i)
                shift[i] = (bx - lx, by - ly)
        for k, i in enumerate(idx):
            lx, ly = lin(i)
            if on[i]:
                dx, dy = shift[i]
            else:
                prev_idx = contour_start + (k - 1) % contour_len
                next_idx = contour_start + (k + 1) % contour_len
                dx, dy = shift.get(prev_idx if on[prev_idx] else next_idx, (0.0, 0.0))
            out[i] = (lx + dx, ly + dy)
        contour_start += contour_len
    return _enforce_g1(out, types, smooth, contours)


def _lagrange3(p0, pm, p1, t):
    l0, l1, l2 = 2 * (t - .5) * (t - 1), -4 * t * (t - 1), 2 * t * (t - .5)
    return (l0 * p0[0] + l1 * pm[0] + l2 * p1[0], l0 * p0[1] + l1 * pm[1] + l2 * p1[1])


def _linear3(p0, pm, p1, t):
    if t <= 0.5:
        s = t / 0.5
        return (p0[0] + (pm[0] - p0[0]) * s, p0[1] + (pm[1] - p0[1]) * s)
    s = (t - 0.5) / 0.5
    return (pm[0] + (p1[0] - pm[0]) * s, pm[1] + (p1[1] - pm[1]) * s)


def _lerp3(a, mid, b, t):
    """Scalar 3-point linear (a→mid→b) — advance-width blend matching _linear3."""
    return a + (mid - a) * (t / 0.5) if t <= 0.5 else mid + (b - mid) * ((t - 0.5) / 0.5)


def _arc3(p0, pm, p1, t, strength):
    """Blend straight (0) → full Lagrange-3 parabola (1) by `strength`."""
    pw, lg = _linear3(p0, pm, p1, t), _lagrange3(p0, pm, p1, t)
    return (pw[0] + (lg[0] - pw[0]) * strength, pw[1] + (lg[1] - pw[1]) * strength)


def _brace_coord_name(m, geom_i, geom):
    """Canonical brace coordinates + name for a GEOM value (int 15 and float 15.0 collapse to one)."""
    gv = int(geom) if float(geom).is_integer() else round(float(geom), 3)
    coords = [round(v) for v in m.axes]
    coords[geom_i] = gv
    return coords, f"GEOM{gv}"


# ── injectors ─────────────────────────────────────────────────────────────────
def _add_brace_layer(glyph, base_layer, master, geom_i, geom, pts, width,
                     types, smooth, contours, shrp=0, si=None, anchors=None):
    """Build ONE GEOM brace layer on `glyph`: clone the master layer, label it for this GEOM (and
    optional SHRP) coordinate, set its advance width, and write the G1-cleaned point positions.
    The single home for "how a brace layer is built" — shared by all three injectors below.
    `anchors` (name → position) moves the cloned master's anchors to the form's: without it every
    brace carried the master's anchors, so a live mark sat where the DEFAULT drawing wants it at
    every GEOM (I's top anchor stayed at the serifed 492 over a 272-centred stem)."""
    pts = _enforce_g1(pts, types, smooth, contours)   # G1 on every injected HOI brace
    br = _clone_layer(base_layer)
    br.layerId = uuid.uuid4().hex.upper()
    br.associatedMasterId = master.id
    coords, name = _brace_coord_name(master, geom_i, geom)
    if shrp:
        coords[si], name = shrp, name + f"_SHRP{shrp}"
    br.attributes["coordinates"], br.name = coords, name
    br.width = width
    for nb, p in zip(_nodes(br), pts):
        nb.position = Point(p[0], p[1])
    for a in br.anchors:
        if anchors and a.name in anchors:
            a.position = Point(*anchors[a.name])
    glyph.layers.append(br)
    return br


def _anchors(layer, names):
    """`layer`'s anchors restricted to `names` — the ones every form of the morph carries. An anchor
    only some forms have stays at the master's position throughout rather than jumping at a knot."""
    return {a.name: (a.position.x, a.position.y) for a in layer.anchors if a.name in names}


def _common_anchors(layers):
    names = None
    for L in layers:
        here = {a.name for a in L.anchors}
        names = here if names is None else names & here
    return names or set()


def _lerp_anchors(a0, a1, t):
    return {k: ((1 - t) * a0[k][0] + t * a1[k][0], (1 - t) * a0[k][1] + t * a1[k][1])
            for k in a0.keys() & a1.keys()}


def _inject_morph_braces(font, leaf, timeline, geom_i, sweep=1.0, skip=()):
    """Inject GEOM brace layers on a path glyph (`leaf`), copying each timeline form's outline AND
    advance width. A composite that swaps one component inherits via its component reference.
    sweep != 1.0 curves the Geo-window transition via _sweep (Base herald stays linear).

    Injects on the SHRP=0 master edge AND the SHRP=100 edge (when every timeline form has a
    node-compatible SHRP=100 brace), pulling each form's SHRP=100 brace — so the morph lands on the
    DRAWN SHRP=100 form instead of the default-edge sharpening delta misfitting the morphed shape
    (the same SHRP-composition fix inject_y_hoi has). Stays linear; this is not the sweep."""
    g = font.glyphs[leaf]
    si = axis_index(font.axes, "SHRP")
    forms = {f for _, f in timeline} | {leaf}
    shrps = [0, 100] if _shrp100_compatible(font, [font.glyphs[fm] for fm in forms], si) else [0]
    for m in font.masters:
        base_layer = g.layers[m.id]
        types = [n.type for n in _nodes(base_layer)]
        smooth = [bool(n.smooth) for n in _nodes(base_layer)]
        contours = [len(p.nodes) for p in base_layer.paths]
        names = _common_anchors(font.glyphs[fm].layers[m.id] for fm in forms)
        for shrp in shrps:
            def lyr(form, shrp=shrp):
                return _shrp_layer(font.glyphs[form], m, shrp, si)

            def pos(form, shrp=shrp):
                return [(n.position.x, n.position.y) for n in _nodes(lyr(form))]

            def add(geom, pts, width, anchors, shrp=shrp):
                _add_brace_layer(g, base_layer, m, geom_i, geom, pts, width,
                                 types, smooth, contours, shrp, si, anchors=anchors)

            for i, (geom, form) in enumerate(timeline):
                if (sweep != 1.0 and i > 0 and timeline[i - 1][1] != form
                        and timeline[i - 1][0] >= GEO_WIN[0]):
                    pgeom, pform = timeline[i - 1]
                    p0, p1 = pos(pform), pos(form)
                    w0, w1 = lyr(pform).width, lyr(form).width
                    a0, a1 = _anchors(lyr(pform), names), _anchors(lyr(form), names)
                    for k in (0.25, 0.5, 0.75):
                        add(pgeom + k * (geom - pgeom),
                            _sweep_path(p0, p1, types, smooth, contours, k, sweep, skip),
                            w0 + (w1 - w0) * k, _lerp_anchors(a0, a1, k))
                add(geom, pos(form), lyr(form).width, _anchors(lyr(form), names))


# ── composites follow their morphing leaves ──────────────────────────────────
# A leaf's braces reshape its outline inside every composite that uses it, but a composite's advance
# and its other components' offsets are its own: ccedilla kept c's 1105 advance while c narrowed to
# 905, Iacute kept the plain I's 524 and its acute over the stem while I widened to 969 under it, J
# in IJ stayed put. follow_composites braces every composite that reaches a morphed glyph (any depth)
# at every GEOM knot its morphing components have. It only READS the leaves' spacing (advance and
# anchors) at their knots — _spacing_states gets that from their brace layers — so it does not care
# how the outline morph itself is carried.
def _spacing_states(font, name, geom_i):
    """{master_id: [(geom, width, anchors, offsets), …]} — a morphed glyph's advance, anchors and
    component offsets at each GEOM knot, read off its GEOM-only brace layers plus the master."""
    g, out = font.glyphs[name], {}
    masters = {m.id: m for m in font.masters}

    def state(geom, L):
        return (geom, L.width, _anchors(L, {a.name for a in L.anchors}),
                [(c.transform[4], c.transform[5]) for c in L.components])
    for L in g.layers:
        c, m = L.attributes.get("coordinates"), masters.get(L.associatedMasterId)
        if not c or m is None or float(c[geom_i]) == float(m.axes[geom_i]):
            continue
        if any(round(a) != round(b) for i, (a, b) in enumerate(zip(c, m.axes)) if i != geom_i):
            continue                                   # a SHRP/YTAS-edge brace: not read
        out.setdefault(m.id, []).append(state(float(c[geom_i]), L))
    for mid, knots in out.items():
        m = masters[mid]
        knots.append(state(float(m.axes[geom_i]), g.layers[m.id]))
        knots.sort(key=lambda k: k[0])
    return out


def _state_at(knots, geom):
    """(advance, anchors, offsets) at `geom`, piecewise-linear between knots and held beyond them —
    which is what the variation model does with braces along GEOM."""
    if geom <= knots[0][0]:
        return knots[0][1:]
    for k0, k1 in zip(knots, knots[1:]):
        if geom <= k1[0]:
            t = (geom - k0[0]) / (k1[0] - k0[0]) if k1[0] > k0[0] else 1.0
            return (k0[1] + (k1[1] - k0[1]) * t, _lerp_anchors(k0[2], k1[2], t),
                    [(p[0] + (q[0] - p[0]) * t, p[1] + (q[1] - p[1]) * t) for p, q in zip(k0[3], k1[3])])
    return knots[-1][1:]


def _mark_attach(font, name, m):
    """The anchor names a component glyph attaches by ('_top' → 'top'); empty for a base. A mark
    drawn without anchors (brevecomb_acutecomb) attaches by kind: above-base to top, else bottom."""
    cg = font.glyphs[name]
    if cg is None:
        return set()
    names = {a.name[1:] for a in cg.layers[m.id].anchors if a.name.startswith("_")}
    if names or (cg.category or glyphdata.get_glyph(name).category) != "Mark":
        return names
    return {"top"} if _is_top_mark(name) else {"bottom"}


def _view(font, name, m, geom, states):
    """A glyph's advance, own anchors and components [(name, transform)] at `geom`: from its spacing
    states if it morphs, else its (static) master layer."""
    L = font.glyphs[name].layers[m.id]
    ks = states.get(name, {}).get(m.id)
    if not ks:
        return L.width, _anchors(L, {a.name for a in L.anchors}), [(c.name, list(c.transform)) for c in L.components]
    w, an, offs = _state_at(ks, geom)
    return w, an, [(c.name, list(c.transform)[:4] + list(o)) for c, o in zip(L.components, offs)]


def _effective_anchors(font, name, m, geom, states):
    """Own anchors plus those inherited through components, as glyphsLib propagates them: the first
    base supplies what the glyph lacks, a mark's anchors replace the base's (an acute's top is the top
    of 'á'). A composite like t carries no anchors of its own; its cedilla anchor is tpart's."""
    _, own, parts = _view(font, name, m, geom, states)
    out = dict(own)
    for cname, t in parts:
        mark = bool(_mark_attach(font, cname, m))
        for n, (x, y) in _effective_anchors(font, cname, m, geom, states).items():
            if n.startswith("_") or n in own or (n in out and not mark):
                continue
            out[n] = (t[0] * x + t[2] * y + t[4], t[1] * x + t[3] * y + t[5])
    return out


def _derive_spacing(font, base, m, geom, states):
    """`base` (a composite layer) with its morphing components at `geom`: advance, component offsets,
    anchors — "leaf + same offsets". A base component pushes every base after it by its own advance
    change; a mark rides the anchor of the component it sits on (the last one before it carrying that
    anchor), so an acute follows c's top and _part.stroke follows f's partstroke; a component turned
    180 degrees (nine's six) is placed by its right edge, so its own advance change moves it. The
    composite's own anchors ride the component that carries the same anchor."""
    mg = float(m.axes[axis_index(font.axes, "GEOM")])
    run, deltas, carried = 0.0, [], []                 # carried: (anchor deltas, anchor names)
    for c in base.components:
        t = list(c.transform)
        dw = _view(font, c.name, m, geom, states)[0] - _view(font, c.name, m, mg, states)[0]
        e1 = _effective_anchors(font, c.name, m, geom, states)
        e0 = _effective_anchors(font, c.name, m, mg, states)
        da = {}
        for n in e0.keys() & e1.keys():
            dx, dy = e1[n][0] - e0[n][0], e1[n][1] - e0[n][1]
            da[n] = (t[0] * dx + t[2] * dy, t[1] * dx + t[3] * dy)
        attach = _mark_attach(font, c.name, m)
        host = next((j for j in range(len(deltas) - 1, -1, -1) if attach & carried[j][1]), None)
        if host is not None:
            n = sorted(attach & carried[host][1])[0]
            d = (deltas[host][0] + carried[host][0].get(n, (0, 0))[0],
                 deltas[host][1] + carried[host][0].get(n, (0, 0))[1])
        elif attach:
            d = (run, 0.0)                             # a mark with nothing to sit on rides the run
        else:
            d = (run + (dw if t[0] < 0 else 0.0), 0.0)
            run += dw
        deltas.append(d)
        carried.append((da, set(e0)))
    anchors = {}
    for a in base.anchors:
        j = next((j for j in range(len(deltas) - 1, -1, -1) if a.name in carried[j][1]), None)
        dx, dy = (0.0, 0.0) if j is None else (deltas[j][0] + carried[j][0].get(a.name, (0, 0))[0],
                                               deltas[j][1] + carried[j][0].get(a.name, (0, 0))[1])
        anchors[a.name] = (a.position.x + dx, a.position.y + dy)
    offsets = [(c.transform[4] + d[0], c.transform[5] + d[1]) for c, d in zip(base.components, deltas)]
    return base.width + run, offsets, anchors


def follow_composites(font, geom_i, leaves, drawn=None):
    """Brace every composite that reaches a morphed glyph so its advance, component offsets and
    anchors follow — any depth, whichever pass morphed the leaf. Public: the true-HOI stage calls it.

    `leaves`  the morphed glyph names. Each must already carry its GEOM brace layers; their advance
              and anchors at each knot are all that is read, so it does not matter how the outline
              morph itself is carried.
    `drawn`   {composite: [(geom, form), …]} — the composite's own timeline where the designer drew
              its alternates (ccedilla → ccedilla.rcltGeo at 80, Iacute → Iacute.rcltA11y at 0-5 …).
              At those knots the composite is pinned to the drawn form's advance, offsets and anchors;
              between them the difference from "leaf + same offsets" (_derive_spacing) is blended
              linearly in GEOM, which is the leaf's own blend. Everywhere else it is derived.

    Knots are the union of every morphing component's knots and the drawn timeline's. Braces sit at
    SHRP 0 / YTAS 1440 only: a composite answers SHRP and YTAS through its OWN layers (the accent-
    ascend YTAS braces), additively, as in the stock font, so an accent rises with YTAS by the same
    amount at every GEOM. A composite whose spacing never moves gets no layers. Returns {composite: (gap, where)}: the worst
    |drawn − derived| in units at its drawn knots, for the designer — a big gap is an alternate
    that is not spaced as leaf + same offsets.
    """
    drawn = drawn or {}
    states = {n: _spacing_states(font, n, geom_i) for n in leaves if font.glyphs[n]}
    m0 = font.masters[0]
    comps = {g.name: [c.name for c in g.layers[m0.id].components]
             for g in font.glyphs if g.layers[m0.id] is not None and g.layers[m0.id].components}
    report, done = {}, set(states)
    progress = True
    while progress:                                   # depth order: a composite after its parts
        progress = False
        for name, parts in comps.items():
            if name in done or not any(p in states for p in parts):
                continue
            if any(p in comps and p not in done and _reaches(p, comps, states) for p in parts):
                continue
            done.add(name); progress = True
            gap = _follow_one(font, geom_i, name, drawn.get(name), states)
            if gap is not None:
                states[name] = _spacing_states(font, name, geom_i)
                report[name] = gap
    return report


def _reaches(name, comps, states, seen=None):
    """True if composite `name` contains a morphed glyph at any depth."""
    seen = seen if seen is not None else set()
    if name in states:
        return True
    if name in seen or name not in comps:
        return False
    seen.add(name)
    return any(_reaches(p, comps, states, seen) for p in comps[name])


def _follow_one(font, geom_i, name, timeline, states):
    """Brace one composite (see follow_composites). Returns (worst drawn−derived gap, where), or
    None if nothing moves and no layer was added."""
    g = font.glyphs[name]
    parts = {c.name for m in font.masters for c in g.layers[m.id].components}
    knots = {k[0] for p in parts if p in states for ks in states[p].values() for k in ks}
    if timeline:
        forms = [font.glyphs[f] for _, f in timeline]
        if any(f is None or any(len(f.layers[m.id].components) != len(g.layers[m.id].components)
                                for m in font.masters) for f in forms):
            timeline = None                    # drawn alternate built differently: derive only
        else:
            knots |= {float(k) for k, _ in timeline}
    plan, moved, worst = [], False, (0.0, "")
    for m in font.masters:
        mg, base = float(m.axes[geom_i]), g.layers[m.id]
        corr = []                                       # (geom, dwidth, [doffsets], {danchor})
        for k, form in (timeline or []):
            F = font.glyphs[form].layers[m.id]
            w, off, an = _derive_spacing(font, base, m, float(k), states)
            fo = [(c.transform[4], c.transform[5]) for c in F.components]
            fa = _anchors(F, set(an))
            co = [(a[0] - b[0], a[1] - b[1]) for a, b in zip(fo, off)]
            gap = max([abs(F.width - w)] + [abs(v) for d in co for v in d])
            if gap > worst[0]:
                worst = (gap, f"{m.name} GEOM{k} vs {form}")
            corr.append((float(k), F.width - w, co,
                         {n: (fa[n][0] - an[n][0], fa[n][1] - an[n][1]) for n in fa}))
        for k in sorted(knots - {mg}):
            w, off, an = _derive_spacing(font, base, m, k, states)
            if corr:
                w, off, an = _apply_corr(corr, k, w, off, an)
            if (abs(w - base.width) > 0.5
                    or any(abs(o[0] - c.transform[4]) + abs(o[1] - c.transform[5]) > 0.5
                           for o, c in zip(off, base.components))
                    or any(abs(an[a.name][0] - a.position.x) + abs(an[a.name][1] - a.position.y) > 0.5
                           for a in base.anchors if a.name in an)):
                moved = True
            plan.append((m, k, w, off, an))
    if not moved:
        return None
    for m, k, w, off, an in plan:
        br = _add_brace_layer(g, g.layers[m.id], m, geom_i, k, [], w, [], [], [], anchors=an)
        for c, o in zip(br.components, off):
            t = list(c.transform)
            c.transform = type(c.transform)(t[0], t[1], t[2], t[3], o[0], o[1])
    return worst


def _apply_corr(corr, k, w, off, an):
    """Add the drawn−derived correction at GEOM k, linear between the drawn knots, held beyond."""
    if k <= corr[0][0]:
        t, a, b = 0.0, corr[0], corr[0]
    elif k >= corr[-1][0]:
        t, a, b = 0.0, corr[-1], corr[-1]
    else:
        a, b = next((x, y) for x, y in zip(corr, corr[1:]) if x[0] <= k <= y[0])
        t = (k - a[0]) / (b[0] - a[0]) if b[0] > a[0] else 0.0
    w += a[1] + (b[1] - a[1]) * t
    off = [(o[0] + p[0] + (q[0] - p[0]) * t, o[1] + p[1] + (q[1] - p[1]) * t)
           for o, p, q in zip(off, a[2], b[2])]
    an = dict(an)
    for n in an:
        if n in a[3] and n in b[3]:
            an[n] = (an[n][0] + a[3][n][0] + (b[3][n][0] - a[3][n][0]) * t,
                     an[n][1] + a[3][n][1] + (b[3][n][1] - a[3][n][1]) * t)
    return w, off, an


def _match_contour_from(font, target, donor, idx=0):
    """Give `target`'s contour `idx` the node structure of `donor`'s only contour, on EVERY layer.

    ldot draws its stem as a 5-node rectangle while ldot.rcltA11y carries the 16-node curved l,
    so collect() vetoes the pair and it keeps hard-swapping. The two are the same shape — bbox
    identical in every master — so lifting l's contour over is lossless and makes the counts
    agree (17 -> 28).

    Every layer has to be covered, masters AND the SHRP=100 braces: fixing only the masters
    leaves eight brace layers at the old count and fontmake rejects the glyph outright. Layers
    are matched by id, then by associatedMasterId. Bounding boxes are checked before each copy
    and the whole repair is abandoned if any pair disagrees, so a mismatched map cannot silently
    reshape the glyph. Flex-only: this mutates the disposable _FLEX font, not the source.
    """
    import copy
    gt, gd = font.glyphs[target], font.glyphs[donor]
    if gt is None or gd is None:
        return False
    by_id = {l.layerId: l for l in gd.layers}
    by_assoc = {}
    for l in gd.layers:
        am = getattr(l, "associatedMasterId", None)
        if am and am != l.layerId:
            by_assoc.setdefault(am, l)

    def bbox(path):
        xs = [n.position.x for n in path.nodes]
        ys = [n.position.y for n in path.nodes]
        return (min(xs), min(ys), max(xs), max(ys))

    plan = []
    for lt in gt.layers:
        if idx >= len(lt.paths):
            continue
        src = by_id.get(lt.layerId) or by_assoc.get(getattr(lt, "associatedMasterId", None))
        if src is None or len(src.paths) != 1:
            return False
        if max(abs(a - b) for a, b in zip(bbox(lt.paths[idx]), bbox(src.paths[0]))) > 1.0:
            return False                      # not the same shape — leave the glyph alone
        plan.append((lt, src))
    for lt, src in plan:
        lt.paths[idx] = copy.deepcopy(src.paths[0])
    return bool(plan)


def _inject_a11y_braces(font, leaf, a11y_form, geom_i):
    """Morph `leaf` from its A11y drawing up to itself across A11Y_WIN.

    Braces go on the DEFAULT glyph, not on the .rcltA11y one: every master sits at GEOM 25
    holding the default outline, which is exactly what belongs there, so unlike handle_I there is
    no competing gvar source to neutralise and no rename. Knots are A11y at 0 and at the window
    start, the model's samples across the window, then the default at the window end (8→25 is
    flat because both ends are the same drawing).
    """
    model = A11Y_MODEL.get(leaf, dict(kind="linear"))
    g, ga = font.glyphs[leaf], font.glyphs[a11y_form]
    si = axis_index(font.axes, "SHRP")
    shrps = [0, 100] if _shrp100_compatible(font, (g, ga), si) else [0]
    lo, hi = _a11y_window(leaf)
    for m in font.masters:
        base_layer = g.layers[m.id]
        types = [n.type for n in _nodes(base_layer)]
        smooth = [bool(n.smooth) for n in _nodes(base_layer)]
        contours = [len(pth.nodes) for pth in base_layer.paths]
        names = _common_anchors((g.layers[m.id], ga.layers[m.id]))
        for shrp in shrps:
            la, ld = _shrp_layer(ga, m, shrp, si), _shrp_layer(g, m, shrp, si)
            pa = [(n.position.x, n.position.y) for n in _nodes(la)]
            pd = [(n.position.x, n.position.y) for n in _nodes(ld)]
            wa, wd = la.width, ld.width
            aa, ad = _anchors(la, names), _anchors(ld, names)

            def add(geom, pts, width, anchors, shrp=shrp):
                _add_brace_layer(g, base_layer, m, geom_i, geom, pts, width,
                                 types, smooth, contours, shrp, si, anchors=anchors)

            add(0, pa, wa, aa)
            add(lo, pa, wa, aa)
            for k in (0.25, 0.5, 0.75):
                if model["kind"] == "stroke":
                    frame = _stroke_path(pa, pd, k, model["pairs"], model["hinge"],
                                         model["hinge_k"], types, smooth, contours)
                elif model["kind"] == "sweep":
                    frame = _sweep_path(pa, pd, types, smooth, contours, k,
                                        model["sweep"], model.get("skip", ()))
                else:
                    frame = [((1 - k) * q0[0] + k * q1[0], (1 - k) * q0[1] + k * q1[1])
                             for q0, q1 in zip(pa, pd)]
                add(lo + k * (hi - lo), frame, wa + (wd - wa) * k, _lerp_anchors(aa, ad, k))
            add(hi, pd, wd, ad)
    return True


def _twist_y_foot(P, types, w):
    """y mid-swing foot shaping, folded into the existing geo-window sweep samples (NO new brace
    layers), scaled by bump `w` (0 at the rcltBase/rcltGeo ends, ~1 at mid-swing). Rotate the left
    edge {22,23}+handles about the foot centroid {19,22,23,26} by Y_TWIST (parallelogram-style twist
    toward the crotch), then nudge n22/n23 (handles ride along) to keep n23 from spiking. On-curve
    driven; the caller's _enforce_g1 cleans tangents. Indices are specific to the y outline (27 nodes,
    foot 19–26)."""
    if w <= 0 or len(P) != 27:
        return P
    P = list(P)
    cx = sum(P[i][0] for i in (19, 22, 23, 26)) / 4.0
    cy = sum(P[i][1] for i in (19, 22, 23, 26)) / 4.0
    a = math.radians(Y_TWIST * w); co, si = math.cos(a), math.sin(a)
    for i in (22, 23):                                  # rotate the left-edge ON-CURVE nodes only; their
        x, y = P[i][0] - cx, P[i][1] - cy               # handles ride along RIGIDLY (translate by the owner's
        nx, ny = cx + x * co - y * si, cy + x * si + y * co   # shift, NEVER rotated — rotating a handle folds
        dx, dy = nx - P[i][0], ny - P[i][1]                   # the curve over, which buckled the sheared italic)
        P[i] = (nx, ny)
        for h in ((i - 1) % 27, (i + 1) % 27):
            if types[h] == "offcurve":
                P[h] = (P[h][0] + dx, P[h][1] + dy)
    for i, (dx, dy) in Y_FOOT_NUDGE.items():            # n22/n23 nudge, handles ride along
        ddx, ddy = dx * w, dy * w
        P[i] = (P[i][0] + ddx, P[i][1] + ddy)
        for h in ((i - 1) % 27, (i + 1) % 27):
            if types[h] == "offcurve":
                P[h] = (P[h][0] + ddx, P[h][1] + ddy)
    return P


def _shrp_layer(glyph, m, shrp, si):
    """Master layer (shrp=0) or the glyph's SHRP=`shrp` brace layer at master m (None if absent)."""
    if shrp == 0:
        return glyph.layers[m.id]
    for L in glyph.layers:
        c = L.attributes.get("coordinates")
        if c and L.associatedMasterId == m.id and round(c[si]) == shrp:
            return L
    return None


def _shrp100_compatible(font, glyphs, si):
    """True if every glyph carries a node-compatible SHRP=100 brace at every master, so the GEOM
    morph can be braced on the SHRP=100 edge as well as the SHRP=0 master edge (the GEOM × SHRP
    corner). False (→ SHRP=0 only) when SHRP is absent or any form lacks a compatible SHRP=100 brace."""
    if si is None:
        return False
    return all(
        (layer := _shrp_layer(glyph, master, 100, si)) is not None
        and len(_nodes(layer)) == len(_nodes(glyph.layers[master.id]))
        for glyph in glyphs for master in font.masters
    )


def inject_y_hoi(font, geom_i, base="y", sweep=Y_SWEEP):
    """y: linear default→rcltBase (35–40), hold (40–75), swept HOI rcltBase→rcltGeo (75–80) with a
    bump-tapered mid-swing foot twist (_twist_y_foot, folded into the samples), clamp. Injected on
    BOTH the SHRP=0 master edge AND the SHRP=100 edge (if drawn) — otherwise the GEOM-morphed hook
    at high GEOM gets the SHRP delta drawn for the *default* terminal added on top, which doesn't fit
    it and wiggles (the SHRP=100 corner is unbraced)."""
    g = font.glyphs[base]
    rb, rg = font.glyphs[base + ".rcltBase"], font.glyphs[base + ".rcltGeo"]
    if not (g and rb and rg):
        return False
    for m in font.masters:
        if not (len(_nodes(g.layers[m.id])) == len(_nodes(rb.layers[m.id])) == len(_nodes(rg.layers[m.id]))):
            return False
    si = axis_index(font.axes, "SHRP")
    # Brace SHRP=100 too, but only if all three forms have a node-compatible SHRP=100 brace everywhere.
    shrps = [0, 100] if _shrp100_compatible(font, (g, rb, rg), si) else [0]
    samples = [i / 5 for i in range(1, 6)]
    for m in font.masters:
        base_layer = g.layers[m.id]
        types = [n.type for n in _nodes(base_layer)]
        smooth = [bool(n.smooth) for n in _nodes(base_layer)]
        contours = [len(p.nodes) for p in base_layer.paths]
        names = _common_anchors(gl.layers[m.id] for gl in (g, rb, rg))
        for shrp in shrps:
            ly, lb, lg = (_shrp_layer(gl, m, shrp, si) for gl in (g, rb, rg))
            yb = [(n.position.x, n.position.y) for n in _nodes(ly)]
            bp = [(n.position.x, n.position.y) for n in _nodes(lb)]
            gp = [(n.position.x, n.position.y) for n in _nodes(lg)]
            yw, bw, gw = ly.width, lb.width, lg.width
            ya, ba, ga = (_anchors(L, names) for L in (ly, lb, lg))

            def add(geom, pts, width, anchors, shrp=shrp):
                _add_brace_layer(g, base_layer, m, geom_i, geom, pts, width,
                                 types, smooth, contours, shrp, si, anchors=anchors)

            add(BASE_WIN[0], yb, yw, ya)
            add(BASE_WIN[1], bp, bw, ba)
            add(GEO_WIN[0], bp, bw, ba)
            rungs = HOOK_RUNGS.get(base)
            for t in samples:
                if rungs:
                    # the hook moves as rungs, so its two edges cannot cross — the notch at 77-78
                    frame = _rung_swing(bp, gp, t, types=types, smooth=smooth,
                                        contours=contours, **rungs)
                else:
                    frame = _sweep_path(bp, gp, types, smooth, contours, t, sweep)
                    frame = _twist_y_foot(frame, types, 4 * t * (1 - t))   # foot twist (handles ride rigidly — italic-safe)
                add(GEO_WIN[0] + t * (GEO_WIN[1] - GEO_WIN[0]), frame, bw + (gw - bw) * t,
                    _lerp_anchors(ba, ga, t))
            add(AXIS_MAX, gp, gw, ga)
    return True


def digit_plan(font, geom_i, base, strength=HOI_STRENGTH):
    """The six/nine timeline as data: {master_id: [(geom, points, width), ...]}.

    Split out of inject_digit_hoi so the same plan can either be written as intermediate layers
    (the brace path) or solved straight into gvar tuples (scripts/lib/inject_deltas), without the
    two drifting apart. Returns {} when the .rclt set is missing or point-incompatible.
    """
    g = font.glyphs[base]
    F = {s_: font.glyphs[base + s_] for s_ in ("", ".rclt1", ".rclt2", ".rclt3")}
    if g is None or any(v is None for v in F.values()):
        return {}
    for m in font.masters:
        n = len(_nodes(g.layers[m.id]))
        if n == 0 or any(len(_nodes(v.layers[m.id])) != n for v in F.values()):
            return {}
    out = {}
    for m in font.masters:
        out[m.id] = _digit_plan_for_master(font, g, F, m, base, strength)
    return out


def _digit_plan_for_master(font, g, F, m, base, strength):
    """One master's timeline: [(geom, points, width), ...]."""
    base_layer = g.layers[m.id]
    types = [n.type for n in _nodes(base_layer)]
    smooth = [bool(n.smooth) for n in _nodes(base_layer)]
    contours = [len(p.nodes) for p in base_layer.paths]
    P = {s: [(x.position.x, x.position.y) for x in _nodes(F[s].layers[m.id])] for s in F}
    six, r1, r2, r3 = P[""], P[".rclt1"], P[".rclt2"], P[".rclt3"]
    sw, w1, w2, w3 = (F[s].layers[m.id].width for s in ("", ".rclt1", ".rclt2", ".rclt3"))
    back_sweep = 1.0 + strength * (SWEEP_MAX - 1.0)
    travel = [math.hypot(six[i][0] - r3[i][0], six[i][1] - r3[i][1]) for i in range(len(r3))]
    tmax = max(travel) or 1.0
    rungs = _digit_rungs(base)
    def swing(t):
        """r3 → six at t (0 = r3, 1 = six). One definition, emitted at both ends."""
        if rungs:
            return _rung_swing(r3, six, t, types=types, smooth=smooth, contours=contours,
                               **rungs)
        return _sweep_path(r3, six, types, smooth, contours, t, back_sweep)

    lo0, lo1 = DIGIT_SWING_LOW
    N = DIGIT_SWING_KNOTS
    plan = [(0, six, sw), (lo0, six, sw)]                            # hold six (low clamp)
    for k in range(1, N):                                            # six → r3, the swing reversed
        t = 1.0 - _ease(k / N)
        plan.append((lo0 + (lo1 - lo0) * k / N, swing(t), w3 + (sw - w3) * t))
    for t in (0.0, 0.25, 0.5, 0.75, 1.0):                            # interlace rewind r3→r2→r1
        arc = [_arc3(r3[i], r2[i], r1[i], t, -INTERLACE_STRENGTH) for i in range(len(r1))]
        plan.append((12.5 + t * 2.5, _enforce_g1(arc, types, smooth, contours),
                     _lerp3(w3, w2, w1, t)))
    plan.append((36, r1, w1))                                        # hold r1 (curviest)
    for tt in (0.17, 0.33, 0.5, 0.67, 0.83, 1.0):                    # forward arc r1→r2→r3 (+ hook)
        geom = 36 + tt * 4
        pts = [_arc3(r1[i], r2[i], r3[i], tt, strength) for i in range(len(r1))]
        if DIGIT_HOOK and tt < 0.5:                                  # transient r1→r2 hook
            s = tt / 0.5
            bump = DIGIT_HOOK * 4 * s * (1 - s)
            pts = [(pts[i][0] + (r1[i][0] - r2[i][0]) * bump * travel[i] / tmax,
                    pts[i][1] + (r1[i][1] - r2[i][1]) * bump * travel[i] / tmax)
                   for i in range(len(r1))]
        plan.append((geom, _enforce_g1(pts, types, smooth, contours), _lerp3(w1, w2, w3, tt)))
    hi0, hi1 = DIGIT_SWING_HIGH
    plan.append((hi0, r3, w3))                                       # hold r3 (plain)
    for k in range(1, N + 1):                                        # r3 → six, the same swing
        t = _ease(k / N)
        plan.append((hi0 + (hi1 - hi0) * k / N, swing(t), w3 + (sw - w3) * t))
    plan.append((100, six, sw))                                      # hold six (clamp)
    return plan


def inject_digit_hoi(font, geom_i, base, strength=HOI_STRENGTH):
    """six/nine sweep: hold six → interlace rewind r3→r2→r1 (12.5–15) → hold r1 → forward arc
    r1→r2→r3 with a transient r1→r2 hook (36–40) → hold r3 → back-sweep r3→six (76–80) → hold six.
    Masters sit at GEOM=25 (the r1 plateau), so the held form is baked onto them (see end) to keep
    the gvar origin from dragging the morph back to default — same fix as handle_I.
    nine is a rotated six COMPONENT (path-less) → returns False and inherits the sweep."""
    g = font.glyphs[base]
    F = {s: font.glyphs[base + s] for s in ("", ".rclt1", ".rclt2", ".rclt3")}
    if g is None or any(v is None for v in F.values()):
        return False
    for m in font.masters:
        n = len(_nodes(g.layers[m.id]))
        if n == 0 or any(len(_nodes(v.layers[m.id])) != n for v in F.values()):
            return False
    for m in font.masters:
        base_layer = g.layers[m.id]
        types = [n.type for n in _nodes(base_layer)]
        smooth = [bool(n.smooth) for n in _nodes(base_layer)]
        contours = [len(p.nodes) for p in base_layer.paths]
        plan = _digit_plan_for_master(font, g, F, m, base, strength)
        for geom, pts, width in plan:
            _add_brace_layer(g, base_layer, m, geom_i, geom, pts, width, types, smooth, contours)
    # Masters sit at GEOM=25 — inside the r1 hold plateau (15–36) — so the master's default
    # `six` outline competes with the injected r1 hold and drags the morph back toward default
    # around GEOM 25 (same failure handle_I fixes for I). Bake the held form (.rclt1) onto the
    # masters so the gvar origin matches what the timeline holds there. The brace outlines were
    # captured above before this overwrite, so the rendered sweep is unchanged.
    r1 = F[".rclt1"]
    for m in font.masters:
        ml = g.layers[m.id]
        for nb, rn in zip(_nodes(ml), _nodes(r1.layers[m.id])):
            nb.position = Point(rn.position.x, rn.position.y)
        ml.width = r1.layers[m.id].width
    return True


def strip_subs(code, pairs):
    """Remove specific `sub A by B;` lines (pairs = {(A, B)}); drop empty `variation` blocks."""
    def keep(ln):
        m = re.match(r"\s*sub\s+(\S+)\s+by\s+(\S+)\s*;", ln)
        return not (m and (m.group(1), m.group(2)) in pairs)
    code = "\n".join(ln for ln in code.split("\n") if keep(ln))
    return re.sub(r"variation\s+rclt\s+\w+\s*\{\s*\}\s*rclt\s*;", "", code)


def handle_I(font, geom_i):
    """Role-flip for I: morph the cmap'd default I from the A11y form (low GEOM) UP to the geometric
    form, then hold geometric. Every master sits at GEOM=25, so the *hold* shape (geometric) must BE
    the master outline — otherwise the A11y master is a competing gvar source that drags the morph
    back to A11y around GEOM 25 (the "to I then back to rcltA11y" bug). Bake the low A11y brace +
    geometric transition first, then copy the geometric outline onto I.rcltA11y's masters so it holds
    flat across the master location. Finally rename I.rcltA11y→I (moving U+0049 so the cmap follows the
    morph) and the geometric I→I.rcltDflt.

    The serifed drawing itself is put back as a STATIC I.rcltA11y, and every component that named
    I.rcltA11y keeps naming it. Those are the swap targets (Iacute.rcltA11y, IJ.rcltA11y …) and ss18
    (I.ss18, Iacute.ss18 → Iacute.rcltA11y): repointed at the morphing I they showed a plain stem in
    a 969-wide advance at GEOM 25, where ss18 asks for the serifed I at every GEOM."""
    gI, gA = font.glyphs["I"], font.glyphs["I.rcltA11y"]
    if gI is None or gA is None:
        return False
    if any(len(_nodes(gA.layers[m.id])) != len(_nodes(gI.layers[m.id])) for m in font.masters):
        return False  # point-incompatible → leave I as a discrete GSUB swap
    serifed = copy.deepcopy(gA, {id(font): font})        # before any brace or bake touches it
    _inject_morph_braces(font, "I.rcltA11y", [(0, "I.rcltA11y"), (5, "I.rcltA11y"), (8, "I"), (AXIS_MAX, "I")], geom_i)
    for m in font.masters:
        gl = gI.layers[m.id]
        for nb, gn in zip(_nodes(gA.layers[m.id]), _nodes(gl)):
            nb.position = Point(gn.position.x, gn.position.y)
        gA.layers[m.id].width = gl.width
        top = _anchors(gl, {a.name for a in gl.anchors})   # the plain I's anchors hold at GEOM 25 too
        for a in gA.layers[m.id].anchors:
            if a.name in top:
                a.position = Point(*top[a.name])
    gI.name, gI.unicode = "I.rcltDflt", None
    gA.name, gA.unicode = "I", "0049"
    serifed.name, serifed.unicode = "I.rcltA11y", None
    font.glyphs.append(serifed)
    # glyphsLib caches name → index on first lookup and renames do not clear it: font.glyphs["I"]
    # would keep returning the plain I, now I.rcltDflt. Drop the cache so later lookups see the flip.
    font._glyph_name_index = None
    # The rename also orphans rclt-state coverage subs in the ss/cv features
    # (`sub I.rcltA11y by I.ss14;`): no rclt sub produces I.rcltA11y any more, so they are dead.
    # The base `sub I by I.ss14;` in the same feature already covers it — drop the dead lines.
    dead_cov = re.compile(r"^[ \t]*sub +I\.rcltA11y +by +[^;]+;[ \t]*\n?", re.MULTILINE)
    for feat in font.features:
        if "I.rcltA11y" in feat.code:
            feat.code = dead_cov.sub("", feat.code)
    return True


# ── entry point ───────────────────────────────────────────────────────────────
def inject_hoi(font, geom_i, verbose=False):
    """Morph the chosen conditionset glyphs in place: inject GEOM brace layers (linear leaf-morphs +
    y/6/9 HOI + curated C/I) and strip those glyphs' subs from the VARIATIONS prefix. Incompatible
    forms stay discrete and are reported. Returns the per-group counts dict."""
    # Repair first: this rewrites master outlines, so it has to happen before ANY brace is
    # injected, or the Base/Geo pass bakes braces at the old node count and fontmake rejects
    # the glyph as incompatible.
    _match_contour_from(font, "ldot", "l")      # 5-node stem -> l's 16, so ldot can morph too

    prefix = next(p for p in font.featurePrefixes if p.name == "VARIATIONS")
    base_map, geo_map, a11y_map = parse_variations(prefix.code)
    candidates = sorted(set(base_map) | set(geo_map))

    linear, discrete, hoi, skipped, swept, leaves = [], [], [], [], [], {}
    drawn = {}          # composite → its drawn timeline, for follow_composites

    def note_drawn(tc, own):
        """Only a composite's OWN swap timeline pins it. One met inside a parent describes the parent's
        swaps, not the leaf's: ij reaches j with ij's Geo-only timeline, which knows nothing of j's
        Base morph at 35-40. Composites without their own are derived (follow_composites)."""
        if own in tc:
            drawn[own] = tc[own]

    for a in candidates:
        if font.glyphs[a] is None:
            continue
        # jdotless is the same morph shape as y — a hook retracting into the stem — so it takes
        # the same path rather than the generic leaf sweep, and picks up HOOK_RUNGS with it.
        if a in HOOK_RUNGS and inject_y_hoi(font, geom_i, base=a):
            swept.append(a); continue
        grp = group_of(a)
        if grp == "discrete":
            discrete.append(a); continue
        tmp, tc = {}, {}
        ok = collect(font, a, timeline_for(a, base_map.get(a), geo_map.get(a)), tmp, tc)
        if grp == "hoi":
            # yacute & co.: y itself is already swept on its rungs (sorted, y comes first), so its
            # composites only need to follow it (follow_composites). Left deferred they kept their
            # swaps to the static yacute.rcltBase/.rcltGeo while the y inside them morphed.
            if ok and tmp and set(tmp) <= set(swept):
                note_drawn(tc, a); linear.append(a)
            else:
                hoi.append(a)
            continue
        if ok:
            leaves.update(tmp); linear.append(a); note_drawn(tc, a)
        else:
            skipped.append(a)

    # Any base that owns a complete .rclt1/2/3 set gets the interlace sweep (six, and future
    # derived figures like sixsuperior once drawn). inject_digit_hoi gates on point-compatibility,
    # so incomplete sets are skipped; flipped-component twins (nine, ninesuperior) are path-less,
    # return False, and inherit the sweep through their component refs. See VISION.md §8.
    digit_bases = sorted({
        g.name for g in font.glyphs
        if not g.name.endswith((".rclt1", ".rclt2", ".rclt3"))
        and all(font.glyphs[g.name + s] for s in (".rclt1", ".rclt2", ".rclt3"))
    })
    for digit in digit_bases:
        if inject_digit_hoi(font, geom_i, digit):
            swept.append(digit)

    for leaf, tl in leaves.items():
        if leaf in swept:                           # j/ij/jcircumflex resolve to jdotless, which
            continue                                # inject_y_hoi already morphed on its rungs
        _inject_morph_braces(font, leaf, tl, geom_i, sweep=HOI_SWEEP.get(leaf, 1.0),
                             skip=HOI_SWEEP_SKIP.get(leaf, ()))

    remove = set()
    for a in linear:                                # linear → drop all its subs
        for mp in (base_map, geo_map):
            if mp.get(a):
                remove.add((a, mp[a][0]))
    for a in swept:                                 # y/6/9 → drop both subs
        for mp in (base_map, geo_map):
            if mp.get(a):
                remove.add((a, mp[a][0]))

    # curated overrides the auto-grouping skips (uppercase / A11y)
    curated = []
    for up, start in (("C", 76), ("M", 75)):
        if not (font.glyphs[up] and font.glyphs[up + ".rcltGeo"]):
            continue
        # M is also reached through Mcommaaccent's linear timeline (the same 75-80 morph), and was
        # braced twice: every M brace layer existed in duplicate. Brace it once.
        if up not in leaves:
            _inject_morph_braces(font, up, [(start, up), (80, up + ".rcltGeo"),
                                            (AXIS_MAX, up + ".rcltGeo")], geom_i)
        remove.add((up, up + ".rcltGeo")); curated.append(up)
        # Ç Ć Č … contain the morphing C but kept their discrete swap to the static .rcltGeo at 79,
        # mid-morph: a 53u outline jump and a 181u advance jump, where ç beside them morphs. They
        # morph with C now, like the lowercase composites, unless a swap changes more than C.
        for src in discrete:
            if src == up or base_of(src) != up or not geo_map.get(src):
                continue
            form = geo_map[src][0]
            tmp, tc = {}, {}
            if (collect(font, src, [(start, src), (80, form), (AXIS_MAX, form)], tmp, tc)
                    and set(tmp) == {up}):
                note_drawn(tc, src)
                remove.add((src, form))

    # I's composites (Í Ī Į …) follow the role-flipped I; at the A11y end they are pinned to the drawn
    # Iacute.rcltA11y & co. Collected before handle_I renames anything.
    i_family = set()                    # IJ is I's too, though NFD does not take Ĳ to I
    for src, (form, _lo, _hi) in sorted(a11y_map.items()):
        if src != "I" and font.glyphs[src] and font.glyphs[form]:
            tmp, tc = {}, {}
            if collect(font, src, [(0, form), (A11Y_WIN[0], form), (A11Y_WIN[1], src),
                                   (AXIS_MAX, src)], tmp, tc) and set(tmp) == {"I"}:
                note_drawn(tc, src); i_family.add(src)
    if handle_I(font, geom_i):
        remove |= set(re.findall(r"sub\s+(I\w*)\s+by\s+(\S+\.rcltA11y)\s*;", prefix.code))
        curated.append("I")

    # A11y leg (GEOM 0-11/13). Independent of the Base/Geo timelines above: a's Base form is
    # point-incompatible (46 vs 31 nodes) and would veto the whole glyph if they shared a
    # timeline, but its A11y form matches exactly, so that half can still morph.
    a11y_done, a11y_seen, a11y_kept = [], set(), []
    for src, (form, _lo, _hi) in sorted(a11y_map.items()):
        if (base_of(src) in A11Y_SKIP_BASES or src in i_family
                or font.glyphs[src] is None or font.glyphs[form] is None):
            continue
        found, tc = {}, {}
        if not collect(font, src, [(0, form), (A11Y_WIN[0], form),
                                   (A11Y_WIN[1], src), (AXIS_MAX, src)], found, tc):
            continue                      # point-incompatible → keep the discrete swap
        # lacute.rcltA11y also swaps acutecomb → acutecomb.case. Morphing that leaf would move the
        # accent on every glyph that uses it, so any src whose swap changes a shared mark stays discrete.
        if any(not tl[0][1].endswith(".rcltA11y") for tl in found.values()):
            a11y_kept.append(src)
            continue
        # Many sources share a leaf (lacute/lslash/ldotbelow all resolve to `l`); inject once.
        for lf, tl in found.items():
            if lf not in a11y_seen:
                _inject_a11y_braces(font, lf, tl[0][1], geom_i)
                a11y_seen.add(lf)
        # aacute & co. on the leaf's own window (a: 10-13), not the A11Y_WIN placeholder knots
        lo, hi = _a11y_window(next(iter(found)))
        note_drawn({n: [(g_, f) for g_, (_, f) in zip((0, lo, hi, AXIS_MAX), tl)]
                    for n, tl in tc.items()}, src)
        remove.add((src, form))
        a11y_done.append(src)

    prefix.code = strip_subs(prefix.code, remove)

    # Every composite of every glyph morphed above follows it in advance, offsets and anchors.
    morphed = set(leaves) | set(swept) | a11y_seen | set(curated)
    followed = follow_composites(font, geom_i, morphed, drawn)

    counts = {"a11y": len(a11y_done), "linear": len(linear), "swept": len(swept),
              "discrete": len(discrete), "deferred": len(hoi), "incompatible": len(skipped),
              "leaves": len(leaves), "curated": curated}
    print(f"   ✅ HOI injected — a11y:{counts['a11y']} linear:{counts['linear']} y/6/9:{counts['swept']} "
          f"leaves:{counts['leaves']} curated:{curated} discrete(upper):{counts['discrete']} "
          f"incompatible:{counts['incompatible']}")
    if a11y_kept:
        print(f"   ↳ a11y kept discrete (swap changes a shared mark): {a11y_kept}")
    if skipped and verbose:
        print(f"   ⚠️  incompatible (kept discrete): {skipped}")
    off = {n: round(v[0]) for n, v in followed.items() if v[0] > 1}
    print(f"   ↳ {len(followed)} composites follow their morphing leaves"
          + (f"; drawn alternate ≠ leaf + offsets (units): {off}" if off else ""))
    counts["composites"] = followed
    return counts
