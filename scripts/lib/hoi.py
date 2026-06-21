"""HOI / variable-morph injection (GEOM glyph morphing for Cal Sans Flex), factored out of reference/dev-scripts/hoi_calsans.py so
the build pipeline can call it. `inject_hoi(font, geom_i)` mutates a prepared glyphsLib GSFont in
place: it morphs chosen conditionset glyphs by injecting GEOM brace layers (linear leaf-morphs +
y/6/9 HOI sweeps + curated C/M/I) and strips those glyphs' `sub` rules from the VARIATIONS prefix.

These morphs ship Flex-family only — see scripts/lib/build_flex.py. The standalone A/B proofing
harness is reference/dev-scripts/hoi_calsans.py (imports from here).
"""
import math
import re
import unicodedata
import uuid

from glyphsLib import glyphdata
from glyphsLib.types import Point

from scripts.lib.prepare import _clone_layer
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
    """glyph → (Base target, lo, hi), glyph → (Geo target, lo, hi). A finite Base window
    (f: 39–76) means return-to-default; open (…32767) means stay."""
    conds = {n: (int(lo), int(hi)) for n, lo, hi in
             re.findall(r"conditionset\s+(\w+)\s*\{\s*GEOM\s+(-?\d+)\s+(-?\d+)\s*;\s*\}", code)}
    base, geo = {}, {}
    for cond, body in re.findall(r"variation\s+rclt\s+(\w+)\s*\{(.*?)\}\s*rclt\s*;", code, re.DOTALL):
        lo, hi = conds.get(cond, (0, OPEN))
        for source, target in re.findall(r"sub\s+(\S+)\s+by\s+(\S+)\s*;", body):
            (base if target.endswith(".rcltBase") else geo if target.endswith(".rcltGeo") else {})[source] = (target, lo, hi)
    return base, geo


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


def collect(font, name, timeline, out):
    """Resolve `name` morphing through `timeline` down to PATH leaves, filling out[leaf]=leaf_timeline.
    Recurses composites to the components that differ. Returns False on any incompatibility."""
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
        for i in range(len(L0.components)):
            leaf_tl, base_leaf = [], L0.components[i].name
            for geom, form in timeline:
                comps = font.glyphs[form].layers[font.masters[0].id].components
                if i >= len(comps):
                    return False
                leaf_tl.append((geom, comps[i].name))
            if all(leaf == base_leaf for _, leaf in leaf_tl):
                continue
            if not collect(font, base_leaf, leaf_tl, out):
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


def _sweep_path(p0, p1, types, smooth, contours, t, sweep):
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
                bx, by = _sweep(p0[i], p1[i], t, sweep)
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
                     types, smooth, contours, shrp=0, si=None):
    """Build ONE GEOM brace layer on `glyph`: clone the master layer, label it for this GEOM (and
    optional SHRP) coordinate, set its advance width, and write the G1-cleaned point positions.
    The single home for "how a brace layer is built" — shared by all three injectors below."""
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
    glyph.layers.append(br)


def _inject_morph_braces(font, leaf, timeline, geom_i, sweep=1.0):
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
        for shrp in shrps:
            def lyr(form, shrp=shrp):
                return _shrp_layer(font.glyphs[form], m, shrp, si)

            def pos(form, shrp=shrp):
                return [(n.position.x, n.position.y) for n in _nodes(lyr(form))]

            def add(geom, pts, width, shrp=shrp):
                _add_brace_layer(g, base_layer, m, geom_i, geom, pts, width,
                                 types, smooth, contours, shrp, si)

            for i, (geom, form) in enumerate(timeline):
                if (sweep != 1.0 and i > 0 and timeline[i - 1][1] != form
                        and timeline[i - 1][0] >= GEO_WIN[0]):
                    pgeom, pform = timeline[i - 1]
                    p0, p1 = pos(pform), pos(form)
                    w0, w1 = lyr(pform).width, lyr(form).width
                    for k in (0.25, 0.5, 0.75):
                        add(pgeom + k * (geom - pgeom),
                            _sweep_path(p0, p1, types, smooth, contours, k, sweep), w0 + (w1 - w0) * k)
                add(geom, pos(form), lyr(form).width)


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
        for shrp in shrps:
            ly, lb, lg = (_shrp_layer(gl, m, shrp, si) for gl in (g, rb, rg))
            yb = [(n.position.x, n.position.y) for n in _nodes(ly)]
            bp = [(n.position.x, n.position.y) for n in _nodes(lb)]
            gp = [(n.position.x, n.position.y) for n in _nodes(lg)]
            yw, bw, gw = ly.width, lb.width, lg.width

            def add(geom, pts, width, shrp=shrp):
                _add_brace_layer(g, base_layer, m, geom_i, geom, pts, width,
                                 types, smooth, contours, shrp, si)

            add(BASE_WIN[0], yb, yw)
            add(BASE_WIN[1], bp, bw)
            add(GEO_WIN[0], bp, bw)
            for t in samples:
                frame = _sweep_path(bp, gp, types, smooth, contours, t, sweep)
                frame = _twist_y_foot(frame, types, 4 * t * (1 - t))   # foot twist (handles ride rigidly — italic-safe)
                add(GEO_WIN[0] + t * (GEO_WIN[1] - GEO_WIN[0]), frame, bw + (gw - bw) * t)
            add(AXIS_MAX, gp, gw)
    return True


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
        P = {s: [(x.position.x, x.position.y) for x in _nodes(F[s].layers[m.id])] for s in F}
        six, r1, r2, r3 = P[""], P[".rclt1"], P[".rclt2"], P[".rclt3"]
        sw, w1, w2, w3 = (F[s].layers[m.id].width for s in ("", ".rclt1", ".rclt2", ".rclt3"))
        back_sweep = 1.0 + strength * (SWEEP_MAX - 1.0)
        travel = [math.hypot(six[i][0] - r3[i][0], six[i][1] - r3[i][1]) for i in range(len(r3))]
        tmax = max(travel) or 1.0
        plan = [(0, six, sw), (12, six, sw)]                             # hold six (low clamp + interlace start)
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
                        pts[i][1] + (r1[i][1] - r2[i][1]) * bump * travel[i] / tmax) for i in range(len(r1))]
            plan.append((geom, _enforce_g1(pts, types, smooth, contours), _lerp3(w1, w2, w3, tt)))
        plan.append((76, r3, w3))                                        # hold r3 (plain)
        for geom in (77, 78, 79, 80):                                    # back sweep r3→six
            t = (geom - 76) / 4.0
            plan.append((geom, _sweep_path(r3, six, types, smooth, contours, t, back_sweep),
                         w3 + (sw - w3) * t))
        plan.append((100, six, sw))                                      # hold six (clamp)
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
    morph), the geometric I→I.rcltDflt, and repoint dangling I.rcltA11y component refs."""
    gI, gA = font.glyphs["I"], font.glyphs["I.rcltA11y"]
    if gI is None or gA is None:
        return False
    if any(len(_nodes(gA.layers[m.id])) != len(_nodes(gI.layers[m.id])) for m in font.masters):
        return False  # point-incompatible → leave I as a discrete GSUB swap
    _inject_morph_braces(font, "I.rcltA11y", [(0, "I.rcltA11y"), (5, "I.rcltA11y"), (8, "I"), (AXIS_MAX, "I")], geom_i)
    for m in font.masters:
        gl = gI.layers[m.id]
        for nb, gn in zip(_nodes(gA.layers[m.id]), _nodes(gl)):
            nb.position = Point(gn.position.x, gn.position.y)
        gA.layers[m.id].width = gl.width
    gI.name, gI.unicode = "I.rcltDflt", None
    gA.name, gA.unicode = "I", "0049"
    for g in font.glyphs:
        for L in g.layers:
            for c in L.components:
                if c.name == "I.rcltA11y":
                    c.name = "I"
    return True


# ── entry point ───────────────────────────────────────────────────────────────
def inject_hoi(font, geom_i, verbose=False):
    """Morph the chosen conditionset glyphs in place: inject GEOM brace layers (linear leaf-morphs +
    y/6/9 HOI + curated C/I) and strip those glyphs' subs from the VARIATIONS prefix. Incompatible
    forms stay discrete and are reported. Returns the per-group counts dict."""
    prefix = next(p for p in font.featurePrefixes if p.name == "VARIATIONS")
    base_map, geo_map = parse_variations(prefix.code)
    candidates = sorted(set(base_map) | set(geo_map))

    linear, discrete, hoi, skipped, swept, leaves = [], [], [], [], [], {}
    for a in candidates:
        if font.glyphs[a] is None:
            continue
        if a == "y" and inject_y_hoi(font, geom_i):
            swept.append(a); continue
        grp = group_of(a)
        if grp == "hoi":
            hoi.append(a); continue
        if grp == "discrete":
            discrete.append(a); continue
        tmp = {}
        if collect(font, a, timeline_for(a, base_map.get(a), geo_map.get(a)), tmp):
            leaves.update(tmp); linear.append(a)
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
        _inject_morph_braces(font, leaf, tl, geom_i, sweep=HOI_SWEEP.get(leaf, 1.0))

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
    if font.glyphs["C"] and font.glyphs["C.rcltGeo"]:
        _inject_morph_braces(font, "C", [(76, "C"), (80, "C.rcltGeo"), (AXIS_MAX, "C.rcltGeo")], geom_i)
        remove.add(("C", "C.rcltGeo")); curated.append("C")
    if font.glyphs["M"] and font.glyphs["M.rcltGeo"]:
        _inject_morph_braces(font, "M", [(75, "M"), (80, "M.rcltGeo"), (AXIS_MAX, "M.rcltGeo")], geom_i)
        remove.add(("M", "M.rcltGeo")); curated.append("M")
    if handle_I(font, geom_i):
        remove |= set(re.findall(r"sub\s+(I\w*)\s+by\s+(\S+\.rcltA11y)\s*;", prefix.code))
        curated.append("I")

    prefix.code = strip_subs(prefix.code, remove)

    counts = {"linear": len(linear), "swept": len(swept),
              "discrete": len(discrete), "deferred": len(hoi), "incompatible": len(skipped),
              "leaves": len(leaves), "curated": curated}
    print(f"   ✅ HOI injected — linear:{counts['linear']} y/6/9:{counts['swept']} "
          f"leaves:{counts['leaves']} curated:{curated} discrete(upper):{counts['discrete']} "
          f"incompatible:{counts['incompatible']}")
    if skipped and verbose:
        print(f"   ⚠️  incompatible (kept discrete): {skipped}")
    return counts
