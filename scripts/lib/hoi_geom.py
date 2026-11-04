"""Cal Sans Flex Geom: the true-HOI Flex morphs on GEOM alone, behind pipeline.stage_compile_flex_geom
(--flex-geom). No helper axes, no avar2 for HOI; build_flex still adds the opsz→YTAS avar2.

Input is the designspace stage_compile_flex_hoi compiled Flex from (stock sources, helper axes, the
sparse helper sources of add_true_hoi / add_digit_hoi / add_a11y_hoi). It is evaluated the way varLib
does, one VariationModel per glyph, on the avar2 diagonal GE1M = GE2M = GE3M = normalized GEOM. That
is hoi_flex's fitted polynomials as compiled (solve_sources asserts the diagonal to 1e-6), and it
keeps everything the add_* steps did around the fit (decomposed composites, UFO row order, the
stroke parts, a's opsz-8 twins) without redoing it. Each path is sampled at GEOM knots and written
as sparse GEOM-only sources at every location the helpers had; helper axes and sources go.

Knots, one set per family (carriers joined by an rclt swap or a component): every breakpoint of the
true-HOI function (each member's helper points: window ends, R edges, polynomial joins; −1, 0, 1),
plus greedy knots in each piece until every member at every location is within FLEXGEOM_TOL units
in every coordinate. Shared knots keep the swaps invisible: X + D_X = M holds at each knot, so it
holds on the straight lines between. A member drops the knots where its own path is straight there
(lossless), and a whole side of the default it does not move on.

Semantics: GEOM is a real axis, so every renderer shows the morph; there is no no-avar2 fallback for
HOI any more. The stock rclt swaps and the R ramps stay as Flex has them (they keep each alternate at
its own drawing at the default). Pilot: reference/geom-only-hoi/README.md.
"""
import copy
from pathlib import Path

import numpy as np
import ufoLib2
from fontTools.designspaceLib import DesignSpaceDocument, SourceDescriptor
from fontTools.varLib.models import VariationModel, normalizeLocation

from scripts import config
from scripts.lib.hoi_flex import HELPERS, F2, _q14, _ufo_vector_mixed, _set_vector_mixed, _SUB, _VARIATION

SAMPLES = 257            # grid per piece for the greedy knots (F2Dot14-rounded)
FLAT_TOL = 0.01          # units: a member's knot this close to its neighbours' chord is dropped
DIAG = ("GEOM", *HELPERS)


def _scalars(supports, base, S):
    """varLib's supportScalar (ot) for each support at `base` (normalized, master axes) with GEOM
    and the helpers all at S: [len(S), len(supports)]."""
    out = np.zeros((len(S), len(supports)))
    for j, sup in enumerate(supports):
        col = np.ones(len(S))
        for axis, (lo, peak, hi) in sup.items():
            if peak == 0 or lo > peak or peak > hi or (lo < 0 < hi):
                continue
            if axis in DIAG:
                sc = np.where(S < peak, (S - lo) / (peak - lo or 1), (hi - S) / (hi - peak or 1))
                col *= np.where(S == peak, 1.0, np.where((S <= lo) | (hi <= S), 0.0, sc))
            else:
                v = base.get(axis, 0.0)
                col *= 1.0 if v == peak else 0.0 if (v <= lo or hi <= v) else \
                    (v - lo) / (peak - lo) if v < peak else (hi - v) / (hi - peak)
            if not col.any():
                break
        out[:, j] = col
    return out


class TrueHOI:
    """The true-HOI designspace, readable along the diagonal per glyph and master location."""

    def __init__(self, ds_path):
        self.ds = DesignSpaceDocument.fromfile(str(ds_path))
        self.tag = {a.name: a.tag for a in self.ds.axes}
        self.triples = {a.tag: tuple(a.map_forward(v) for v in (a.minimum, a.default, a.maximum))
                        for a in self.ds.axes}
        self.order = [a.tag for a in self.ds.axes]
        self.fonts = {p: ufoLib2.Font.open(p) for p in {s.path for s in self.ds.sources}}
        self.sources = []                 # (tag location, layer, descriptor, helper?)
        for s in self.ds.sources:
            f = self.fonts[s.path]
            layer = f.layers[s.layerName] if s.layerName else f.layers.defaultLayer
            loc = {self.tag[k]: v for k, v in s.location.items()}
            for t, (lo, d, hi) in self.triples.items():
                loc.setdefault(t, d)
            self.sources.append((loc, layer, s, any(loc.get(h, 0) for h in HELPERS)))
        self.carriers = sorted({n for _, layer, _, h in self.sources if h for n in layer.keys()})
        self._models = {}

    def norm(self, loc):
        full = {t: loc.get(t, d) for t, (lo, d, hi) in self.triples.items()}
        return {k: v for k, v in normalizeLocation(full, self.triples).items() if v}

    def model(self, name):
        """(supports, deltas [n, coords], locations {L: normalized base}, helper points) of a carrier:
        L = master-axis location (tag, design value) where it has helper sources, GEOM at default."""
        if name not in self._models:
            locs, vals, Ls, ks = [], [], {}, set()
            for loc, layer, _, helper in self.sources:
                if name in layer:
                    locs.append(self.norm(loc))
                    vals.append(_ufo_vector_mixed(layer[name]))
                    if helper:
                        L = tuple(sorted((t, v) for t, v in loc.items() if t not in HELPERS))
                        Ls[L] = self.norm(dict(L))
                        ks.add(_q14(loc[HELPERS[0]]))
            assert len({v.shape for v in vals}) == 1, f"{name}: incompatible sources"
            model = VariationModel(locs, axisOrder=self.order)
            deltas = np.stack(model.getDeltas(vals)).reshape(len(vals), -1)
            self._models[name] = (model.supports, deltas, Ls, ks, vals[0].shape)
        return self._models[name]

    def values(self, name, L, S):
        """[len(S), coords]: `name` at master location L with GEOM (and the helpers) at S."""
        supports, deltas, Ls, _, _ = self.model(name)
        return _scalars(supports, Ls[L], np.asarray(S, float)) @ deltas


def families(hoi, code):
    """Carriers joined by a GEOM rclt swap or a component (through plain composites): one knot set each."""
    parent = {g: g for g in hoi.carriers}

    def root(g):
        while parent[g] != g:
            g = parent[g]
        return g

    def join(a, b):
        parent[root(a)] = root(b)
    for _, body in _VARIATION.findall(code):
        for line in body.split("\n"):
            m = _SUB.match(line)
            if m and m.group(1) in parent and m.group(2) in parent:
                join(m.group(1), m.group(2))
    default = hoi.fonts[hoi.ds.findDefault().path].layers.defaultLayer

    def reached(n):
        return {n} if n in parent else {r for c in default[n].components for r in reached(c.baseGlyph)}
    for g in hoi.carriers:
        for c in default[g].components:
            for r in reached(c.baseGlyph):
                join(g, r)
    out = {}
    for g in hoi.carriers:
        out.setdefault(root(g), []).append(g)
    return sorted(out.values(), key=lambda f: min(f))


def _hats(S, K):
    """Piecewise-linear interpolation matrix: values at knots K → values at S."""
    W = np.zeros((len(S), len(K)))
    i = np.clip(np.searchsorted(K, S, side="right") - 1, 0, len(K) - 2)
    t = (S - K[i]) / (K[i + 1] - K[i])
    W[np.arange(len(S)), i] = 1 - t
    W[np.arange(len(S)), i + 1] = t
    return W


def family_knots(hoi, fam, tol):
    """Breakpoints of every member plus greedy knots per piece; (knots, breakpoints, worst error)."""
    bps = sorted({-1.0, 0.0, 1.0} | {k for g in fam for k in hoi.model(g)[3]})
    knots, worst = set(bps), 0.0
    for a, b in zip(bps, bps[1:]):
        S = np.unique(np.round(np.linspace(a, b, SAMPLES) * F2) / F2)
        F = [hoi.values(g, L, S) for g in fam for L in hoi.model(g)[2]]
        K = [0, len(S) - 1]
        while True:
            W = _hats(S, S[K])
            err = np.max([np.abs(W @ f[K] - f).max(axis=1) for f in F], axis=0)
            i = int(np.argmax(err))
            if err[i] <= tol:
                break
            K = sorted(set(K) | {i})
        worst = max(worst, float(err.max()))
        knots |= {float(S[k]) for k in K}
    return sorted(knots), bps, worst


def member_knots(hoi, g, knots):
    """The family knots `g` needs: drop runs on its own chord, and a side where it never moves."""
    K = np.array(knots)
    F = np.stack([hoi.values(g, L, K) for L in hoi.model(g)[2]])        # [L, knot, coords]
    z = int(np.searchsorted(K, 0.0))
    keep = []
    for side in (list(range(z, -1, -1)), list(range(z, len(K)))):      # outward from the default
        if np.abs(F[:, side] - F[:, [z]]).max() < FLAT_TOL:
            continue
        kept = [0]                                                       # positions in `side`
        for n in range(1, len(side) - 1):
            a, b = side[kept[-1]], side[n + 1]
            run = side[kept[-1] + 1:n + 1]
            t = (K[run] - K[a]) / (K[b] - K[a])
            chord = F[:, [a]] + (F[:, [b]] - F[:, [a]]) * t[None, :, None]
            if np.abs(F[:, run] - chord).max() >= FLAT_TOL:
                kept.append(n)
        keep += [side[n] for n in kept[1:]] + [side[-1]]
    return sorted(float(K[i]) for i in set(keep))


def geom_only(ds_path, out_dir, tol=config.FLEXGEOM_TOL):
    """Write the GEOM-only designspace (+ UFOs) for `ds_path` into `out_dir`; returns its path."""
    hoi = TrueHOI(ds_path)
    ds = hoi.ds
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    geom = next(a for a in ds.axes if a.tag == "GEOM")
    to_user = lambda s: geom.default + (geom.maximum - geom.default if s > 0 else geom.default - geom.minimum) * s
    code = hoi.fonts[ds.findDefault().path].features.text
    plain = [(loc, s) for loc, _, s, helper in hoi.sources if not helper]

    def source_at(L):
        hits = [s for loc, s in plain if all(abs(loc[t] - v) < 1e-9 for t, v in L)]
        assert len(hits) == 1, f"{len(hits)} plain sources at {L}"
        return hits[0]

    layers, n_glyphs, report = {}, 0, {}
    for fam in families(hoi, code):
        knots, bps, worst = family_knots(hoi, fam, tol)
        report[min(fam)] = dict(members=fam, knots=[round(to_user(k), 4) for k in knots], worst=round(worst, 3))
        print(f"   ↳ {min(fam)} ({len(fam)} glyphs): {len(bps)} breakpoints → {len(knots)} knots, "
              f"worst {worst:.2f}u")
        for g in fam:
            for k in member_knots(hoi, g, knots):
                if k == 0.0:
                    continue
                for L in hoi.model(g)[2]:
                    src = source_at(L)
                    font = hoi.fonts[src.path]
                    key = (src.path, src.layerName, k)
                    if key not in layers:
                        lname = f"geomonly {to_user(k):.4f}" + (f" @{src.layerName}" if src.layerName else "")
                        layers[key] = (font.layers.newLayer(lname), src, to_user(k))
                    base = font.layers[src.layerName] if src.layerName else font.layers.defaultLayer
                    glyph = copy.deepcopy(base[g] if g in base else font.layers.defaultLayer[g])
                    _set_vector_mixed(glyph, hoi.values(g, L, [k])[0].reshape(hoi.model(g)[4]))
                    layers[key][0].insertGlyph(glyph, g, overwrite=True, copy=False)
                    n_glyphs += 1

    for _, layer, s, helper in hoi.sources:
        if helper and s.layerName in hoi.fonts[s.path].layers:
            del hoi.fonts[s.path].layers[s.layerName]
    ds.sources = [s for _, _, s, helper in hoi.sources if not helper]
    for layer, src, g_user in layers.values():
        ds.addSource(SourceDescriptor(filename=src.filename, path=src.path, layerName=layer.name,
                                      name=f"{src.name} {layer.name}",
                                      location={**{n: v for n, v in src.location.items() if n not in HELPERS},
                                                geom.name: g_user}))
    ds.axes = [a for a in ds.axes if a.tag not in HELPERS]
    for vf in ds.variableFonts:
        vf.axisSubsets = [a for a in vf.axisSubsets if a.name not in HELPERS]
    for path, font in hoi.fonts.items():
        font.save(out_dir / Path(path).name, overwrite=True)
    for s in ds.sources:
        s.path = str(out_dir / Path(s.path).name)
    out = out_dir / Path(ds_path).name.replace("FLEXHOI", "FLEXGEOM")
    ds.write(out)
    total = sum(len(r["knots"]) for r in report.values())
    print(f"   ✅ GEOM-only sources — {len(report)} families, {total} knots, {len(layers)} GEOM layers, "
          f"{n_glyphs} glyph sources (tolerance {tol:g}u)")
    return str(out), report
