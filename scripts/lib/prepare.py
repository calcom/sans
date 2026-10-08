import copy
import math
import re
import unicodedata
import uuid

from glyphsLib import glyphdata
from glyphsLib.types import Point
from tqdm import tqdm

from scripts import config


def _format_names(names, verbose):
    """Render a glyph/instance name list — full list when verbose, else just
    the first 4 names plus a "(N more)" hint, per issue #17 feedback that the
    full lists made step 4's output too noisy to read by default."""
    if verbose or len(names) <= 4:
        return str(names)
    shown = ", ".join(repr(n) for n in names[:4])
    return f"[{shown}, ... ({len(names) - 4} more)]"


def patch_smart_components(font):
    """Diagnostic only — smart component pole mappings are defined in the source.
    Filling in missing axes causes duplicate variation model locations, so we leave them alone."""
    smart_glyphs = [g for g in font.glyphs if g.smartComponentAxes]
    print(f"   Found {len(smart_glyphs)} smart component glyph(s) — no patching applied")


def prepare_for_fontmake(font, verbose=False):
    """Swap Glyphs dialect → feaLib dialect:
    - rclt: strip Glyphs-proprietary 'condition' lines; lookup bodies stay
    - VARIATIONS prefix: enable (now has correct top-level variation rclt syntax)
    """
    # REMOVE condition-based rclt features entirely (not just disable). Disabling leaves an
    # empty `feature rclt {}` shell in the compiled features.fea, which registers rclt under
    # DFLT only — so the VARIATIONS variation blocks attach to a DFLT-only feature and never
    # apply to latn text. Removing the shell lets feaLib auto-register rclt under all
    # languagesystems (DFLT + latn), matching the known-good exemplar.
    to_remove = [f for f in font.features
                 if getattr(f, "name", "").lower() == config.RCLT_FEATURE_TAG and re.search(r'\s*condition\s', f.code)]
    for f in to_remove:
        font.features.remove(f)
    print(f"   ✅ Removed {len(to_remove)} condition-based {config.RCLT_FEATURE_TAG} feature(s) — VARIATIONS prefix handles substitution")

    # Move ccmp to the FRONT of the feature list. The source has it dead last (after
    # ss20), and feaLib assigns GSUB lookup indices in source order — but shapers apply
    # lookups in INDEX order, so ccmp's decompositions (fi/fl/ldot/Ldot → components)
    # compiled to indices ABOVE liga's and re-decomposed every liga-formed fi/fl
    # ligature. First in source → lowest indices → decompose-then-religate, the
    # intended chain (typed U+FB01 ≡ typed f,i).
    ccmp = [f for f in font.features if getattr(f, "name", "").lower() == "ccmp"]
    if ccmp:
        rest = [f for f in font.features if f not in ccmp]
        font.features = ccmp + rest  # the glyphsLib proxy rejects slice assignment
        print(f"   ✅ Moved {len(ccmp)} ccmp feature(s) to the front (was after ss20 — "
              f"its late lookup indices undid the fi/fl liga ligatures)")

    # Convert Glyphs shorthand cvParameters to AFDKO/feaLib format:
    #   cvParameters { FeatUILabelNameID { name "Label"; }; };
    # → cvParameters { FeatUILabelNameID { name 3 1 0x0409 "Label"; }; };
    # Also strip #ifdef VARIABLE ... #endif blocks (Glyphs preprocessor syntax feaLib can't parse).
    def _fix_cv_params(code):
        platform, lang, langid = config.CV_PARAM_PLATFORM_LANG
        code = re.sub(
            r'cvParameters\s*\{\s*FeatUILabelNameID\s*\{\s*name\s*"([^"]+)"\s*;\s*\}\s*;\s*\}',
            # Keep the rewrite on a single line: a #-commented cvParameters in the
            # source (one line, one '#') must stay fully commented — a multi-line
            # expansion would leak FeatUILabelNameID onto uncommented lines.
            lambda m: (
                f'cvParameters {{ FeatUILabelNameID {{ '
                f'name {platform} {lang} {hex(langid)} "{m.group(1)}"; }}; }}'
            ),
            code
        )
        code = re.sub(r'#ifdef\s+VARIABLE.*?#endif', '', code, flags=re.DOTALL)
        return code

    fixed = 0
    for feat in font.features:
        if feat.disabled:
            continue
        new_code = _fix_cv_params(feat.code)
        if new_code != feat.code:
            feat.code = new_code
            fixed += 1
    print(f"   ✅ Fixed cvParameters + stripped #ifdef VARIABLE blocks in {fixed} feature(s)")

    # Filter the auto-generated All class to exported glyphs only.
    # SkipExportGlyphsIFilter removes non-exported glyphs from the glyph set
    # but the compiled @All class still references them, causing feature errors.
    exported = {g.name for g in font.glyphs if g.export}
    for cls in getattr(font, "classes", []):
        if cls.name == config.ALL_CLASS_NAME:
            before = len(cls.code.split())
            cls.code = " ".join(n for n in cls.code.split() if n in exported)
            after = len(cls.code.split())
            if before != after:
                print(f"   ✅ @{config.ALL_CLASS_NAME} class filtered ({before - after} non-exported glyphs removed, {after} remaining)")
            else:
                print(f"   @{config.ALL_CLASS_NAME} class unchanged — all {before} glyphs are exported")

    # Keep the parallel fraction classes index-aligned. feaLib requires @Figures/@Numerators/
    # @Denominators to be equal-length in frac's `sub @Figures' fraction by @Numerators` rules,
    # but inconsistent `#` commenting across the three (half-finished numr/dnom work) desyncs them
    # (e.g. zero.rcltGeo active while #zero.numr.rcltGeo is commented). Drop any index where the
    # three disagree (a partner is commented or non-exported); what survives is parallel and valid,
    # so frac keeps working for the finished figures.
    by_name = {c.name: c for c in getattr(font, "classes", [])}
    triple = [by_name.get(n) for n in config.FRACTION_PARALLEL_CLASSES]
    if all(triple) and len({len(c.code.split()) for c in triple}) == 1:
        toks = [c.code.split() for c in triple]
        live = [i for i in range(len(toks[0]))
                if all(not t[i].startswith("#") and t[i] in exported for t in toks)]
        dropped = len(toks[0]) - len(live)
        for c, t in zip(triple, toks):
            c.code = " ".join(t[i] for i in live)
        if dropped:
            print(f"   ✅ Aligned fraction classes {config.FRACTION_PARALLEL_CLASSES} — "
                  f"dropped {dropped} unaligned index(es), {len(live)} kept")

    # Remove "Replace Glyph" instance parameters — rclt feature handles substitution,
    # and Replace Glyph causes cyclical component references when alternates use base as component.
    removed = 0
    affected = []
    for instance in getattr(font, "instances", []):
        if any(p.name == config.RENAME_GLYPHS_PARAM for p in instance.customParameters):
            affected.append(instance.name)
        params = [p for p in instance.customParameters if p.name != config.RENAME_GLYPHS_PARAM]
        if len(params) != len(instance.customParameters):
            removed += len(instance.customParameters) - len(params)
            instance.customParameters = params
    if removed:
        print(f"   ✅ Removed {config.RENAME_GLYPHS_PARAM} from {removed} instance(s): {_format_names(affected, verbose)}")
    else:
        print(f"   No {config.RENAME_GLYPHS_PARAM} parameters found in any instance")

    # Enable the VARIATIONS prefix. It is authored in correct top-level feaLib syntax
    # (variation rclt cond_X { <direct subs> } rclt;) but kept disabled in source so the
    # Glyphs app — which can't compile conditionset syntax — ignores it. fontmake needs it on.
    enabled = 0
    for prefix in getattr(font, "featurePrefixes", []):
        if getattr(prefix, "name", "") == config.VARIATIONS_PREFIX_NAME:
            prefix.disabled = False
            enabled += 1
    print(f"   ✅ Enabled {config.VARIATIONS_PREFIX_NAME} prefix ({enabled})")

    # Reorder prefixes so languagesystem declarations come FIRST. feaLib only registers a
    # feature under languagesystems declared BEFORE it; the VARIATIONS prefix (variation rclt
    # blocks) was emitted before the Languagesystems prefix, so rclt registered under DFLT
    # only and never applied to latn (Latin) text. Putting languagesystems first fixes it.
    prefixes = list(getattr(font, "featurePrefixes", []))
    lang = [p for p in prefixes if "languagesystem" in (getattr(p, "code", "") or "")]
    rest = [p for p in prefixes if "languagesystem" not in (getattr(p, "code", "") or "")]
    if lang and prefixes != lang + rest:
        font.featurePrefixes = lang + rest
        print(f"   ✅ Moved {len(lang)} languagesystem prefix(es) before variation blocks")

    align_composite_braces(font)


def align_composite_braces(font):
    """Give auto-aligned composites the brace layers their components have, as Glyphs does live.

    In Glyphs an auto-aligned composite takes its advance from its base and seats its marks on the
    base's anchors at EVERY location, braces included. glyphsLib only reads the composite's own
    layers, so where only the base has a brace the composite keeps the master's advance and mark
    positions: y narrows to 1080 at SHRP 100 (opsz 10) while ý stays 1098, ź is 108u off z, Á 113u
    off A. Here each missing brace is added: bases keep their order and push what follows by their
    own advance change, a mark rides the anchor it attaches to on the last base carrying it.
    Composites with any alignment-disabled component (.tf figures, fractions) hold their own width
    and are left alone. YTAS braces are skipped: inject_ytas_ascend_braces owns them."""
    axes = [a.axisTag for a in font.axes]
    ytas_i = axes.index("YTAS")
    masters = {m.id: m for m in font.masters}

    def braces(glyph, mid):
        """{coords: layer} — the non-YTAS braces of `glyph` on master `mid`."""
        out, m = {}, masters[mid]
        for L in glyph.layers:
            c = (getattr(L, "attributes", {}) or {}).get("coordinates")
            if not c or L.associatedMasterId != mid or L.layerId == mid:
                continue
            moved = [i for i, (a, b) in enumerate(zip(c, m.axes)) if float(a) != float(b)]
            if moved and ytas_i not in moved:
                out[tuple(float(v) for v in c)] = L
        return out

    def anchors(layer):
        return {a.name: (a.position.x, a.position.y) for a in layer.anchors}

    done, added, glyphs_touched = set(), 0, set()

    def visit(glyph):
        nonlocal added
        if glyph.name in done:
            return
        done.add(glyph.name)
        for mid in masters:
            ml = glyph.layers[mid]
            if ml is None or not ml.components:
                continue
            parts = [font.glyphs[c.name] for c in ml.components]
            if any(p is None for p in parts) or any(c.alignment == -1 for c in ml.components):
                return
            for p in parts:
                visit(p)                                  # nested composites first
            mine = braces(glyph, mid)
            wanted = set().union(*(braces(p, mid) for p in parts)) - set(mine)
            for coords in sorted(wanted):
                br, run, bases, moved = _clone_layer(ml), 0.0, [], False
                for c, p in zip(br.components, parts):
                    pm, pb = p.layers[mid], braces(p, mid).get(coords)
                    pb = pb or pm
                    da = {n: (pb_xy[0] - pm_xy[0], pb_xy[1] - pm_xy[1])
                          for n, pm_xy in anchors(pm).items()
                          for pb_xy in [anchors(pb).get(n, pm_xy)]}
                    attach = {n[1:] for n in anchors(pm) if n.startswith("_")}
                    host = next((b for b in reversed(bases) if attach & set(b[1])), None)
                    if attach and host is not None:
                        n = sorted(attach & set(host[1]))[0]
                        dx = host[0] + host[1][n][0] - da.get("_" + n, (0, 0))[0]
                        dy = host[1][n][1] - da.get("_" + n, (0, 0))[1]
                    else:
                        dx, dy = run, 0.0
                        if not attach:
                            bases.append((run, da))
                            run += pb.width - pm.width
                    if abs(dx) > 0.5 or abs(dy) > 0.5:
                        c.position = Point(c.position.x + dx, c.position.y + dy)
                        moved = True
                for a in br.anchors:                     # own anchors ride the base carrying them
                    host = next((b for b in reversed(bases) if a.name in b[1]), None)
                    if host is not None:
                        a.position = Point(a.position.x + host[0] + host[1][a.name][0],
                                           a.position.y + host[1][a.name][1])
                br.width = ml.width + run
                if not moved and abs(run) <= 0.5:
                    continue
                br.layerId = str(uuid.uuid4()).upper()
                br.associatedMasterId = mid
                br.attributes["coordinates"] = list(coords)
                br.name = "{" + ", ".join(f"{v:g}" for v in coords) + "}"
                glyph.layers.append(br)
                added += 1
                glyphs_touched.add(glyph.name)

    for g in list(font.glyphs):
        visit(g)
    print(f"   ✅ Aligned composite braces: {added} brace layer(s) on {len(glyphs_touched)} composite(s) "
          f"follow their components' advance and anchors")


def propagate_anchors_for_fontmake(font):
    """Run glyphsLib's anchor propagation here, with axis ranges that include the Virtual
    Masters, and switch it off for fontmake.

    glyphsLib takes each axis's range from the real masters only. SHRP exists only through
    Virtual Masters, so it reads 0–0 and every SHRP=100 brace normalizes onto its master: the
    composite braces align_composite_braces adds then fail to interpolate their components'
    anchors (~1,650 'failed to interpolate anchor' warnings) and lose the ones they don't carry
    themselves (bottom/ogonek on acircumflex & co). Same transformations, same order, just the
    right ranges. Call it last, after every pass that adds layers, right before saving."""
    from glyphsLib.builder.transformations import align_alternate_layers
    from glyphsLib.builder.transformations import propagate_anchors as pa

    orig = pa._get_design_space_info

    def with_virtual_masters(f):
        locs, triples = orig(f)
        for cp in f.customParameters:
            if cp.name != "Virtual Master" or cp.disabled:
                continue
            for v in cp.value:
                name, loc = v["Axis"], float(v["Location"])
                if name in triples:
                    lo, default, hi = triples[name]
                    triples[name] = (min(lo, loc), default, max(hi, loc))
        return locs, triples

    pa._get_design_space_info = with_virtual_masters
    try:
        align_alternate_layers(font)
        pa.propagate_all_anchors(font)
    finally:
        pa._get_design_space_info = orig
    font.customParameters["Propagate Anchors"] = False
    print("   ✅ Propagated anchors (Virtual Master axis ranges); fontmake's own pass switched off")


def _clone_layer(layer):
    """deepcopy a GSLayer without dragging the whole font. A layer reaches the
    GSFont two ways: via `.parent` (the glyph) AND, on outline glyphs, through its
    paths/nodes — so detaching `.parent` alone still clones the entire font graph
    per path glyph (~5s each). Pre-seed the deepcopy memo with the font and glyph
    so deepcopy treats them as already-copied (reuses the originals) and only
    duplicates the layer's own paths/anchors/components. ~600× faster on outline
    glyphs (5s → 0.01s); composites were already fast."""
    glyph = layer.parent
    font = glyph.parent if glyph is not None else None
    layer.parent = None
    try:
        memo = {}
        if font is not None:
            memo[id(font)] = font
        if glyph is not None:
            memo[id(glyph)] = glyph
        return copy.deepcopy(layer, memo)
    finally:
        layer.parent = glyph


SS_ALL_CASE = frozenset({"ss01", "ss02", "ss03", "ss04", "ss07"})
SS_LOWER_ONLY = frozenset({"ss10", "ss14", "ss16"})


def _is_target_stylistic_set(glyph_name):
    """The .ssNN alternates are component-references to .rclt forms; after fontmake
    flattens components they lose the YTAS variation they'd otherwise inherit, so
    they need their own brace (a plain clone — the ascend re-resolves through the
    flattened .rclt component at YTAS=1600). Target sets, per design: ss01–04 and
    ss07 (all members), plus ss10/ss14 LOWERCASE only — those two sets also carry
    uppercase alternates, whose accents don't move."""
    suffixes = glyph_name.split(".")[1:]
    if any(s in SS_ALL_CASE for s in suffixes):
        return True
    if any(s in SS_LOWER_ONLY for s in suffixes):
        root = glyph_name.split(".")[0]
        u = glyphdata.get_glyph(root).unicode
        return bool(u) and chr(int(u, 16)).islower()
    return False


def _is_top_mark(name):
    """True if every combining piece of `name` is an above-base (combining class
    230) mark — acute/grave/circumflex/dieresis/ring/macron/breve, the i/j dot
    (dotaccentcomb), and combined marks like brevecomb_acutecomb — but not
    cedilla/ogonek/dot-below. Resolves Glyphs-style mark names via glyphsLib's own
    GlyphData (fontTools' AGL only knows a handful), splitting ligature mark names
    on '_' so stacked accents are judged as a whole."""
    cps = []
    for part in name.split(".")[0].split("_"):
        u = glyphdata.get_glyph(part).unicode
        if u:
            cps.append(int(u, 16))
    cccs = [c for c in (unicodedata.combining(chr(cp)) for cp in cps) if c != 0]
    return bool(cccs) and all(c == 230 for c in cccs)


def inject_ytas_ascend_braces(font, verbose=False):
    """Add a YTAS=1600 brace (intermediate) layer to every targeted glyph and, on
    that brace, move the `top` anchor and any above-base mark components up by
    config.YTAS_ACCENT_ASCEND_DY (with a calculated italic dx = dy·tan(angle)).

    fontmake compiles these braces into BOTH a variable GPOS `top` anchor — so
    live mark-to-base / mark-to-mark accents ascend (the mkmk stack rides the base
    anchor) — AND gvar component deltas, so precomposed accents ascend too. This
    replaces the old post-compile gvar pass, which could only reach precomposed
    glyphs. Scope is the curated lowercase bases in config.YTAS_ACCENT_ASCEND_BASES
    (a glyph qualifies if it IS one of them or its base/first component is)."""
    axes = [a.axisTag for a in font.axes]
    ytas_i, ital_i = axes.index("YTAS"), axes.index("ital")
    ytas_top = config.STATIC_AXIS_VALUES["ytas"]["tall"]
    ytas_extent = ytas_top - config.STATIC_AXIS_VALUES["ytas"]["base"]
    dy_asc = config.YTAS_ACCENT_ASCEND_DY                 # accents on ascenders: full travel
    dy_xht = config.YTAS_ACCENT_ASCEND_DY_XHEIGHT         # accents on x-height bases: half
    tan_ital = math.tan(math.radians(config.ITALIC_SLANT_DEGREES))
    bases = set(config.YTAS_ACCENT_ASCEND_BASES)
    asc_bases = set(config.YTAS_ACCENT_ASCEND_BASES_ASCENDER)

    def travel_for(glyph):
        """An accent rides its BASE: full travel on an ascender that extends with YTAS, half on
        an x-height letter whose outline does not move. Composites are judged by their first
        component (lacute -> l -> ascender)."""
        if glyph.name in asc_bases:
            return dy_asc
        for layer in (glyph.layers[m.id] for m in font.masters):
            if layer and layer.components and layer.components[0].name in asc_bases:
                return dy_asc
        return dy_xht

    def in_scope(glyph):
        if glyph.name in bases:
            return True
        if any(layer and layer.components and layer.components[0].name in bases
               for layer in (glyph.layers[m.id] for m in font.masters)):
            return True
        return _is_target_stylistic_set(glyph.name)

    targets = [g for g in font.glyphs if in_scope(g)]
    anchors = 0
    for glyph in tqdm(targets, desc="   ↳ YTAS ascend braces", leave=False):
        for m in font.masters:
            ml = glyph.layers[m.id]
            if ml is None:
                continue
            # Don't double-brace: skip if this glyph already ships a YTAS-top brace
            # for this master (ascender letters do — they're out of scope, but guard
            # anyway so a re-run or future source can't stack duplicate braces).
            if any((getattr(layer, "attributes", {}) or {}).get("coordinates")
                   and round(layer.attributes["coordinates"][ytas_i]) == ytas_top
                   and layer.associatedMasterId == m.id
                   for layer in glyph.layers):
                continue
            dy = travel_for(glyph)
            dx = round(dy * tan_ital) if round(m.axes[ital_i]) == 1 else 0
            br = _clone_layer(ml)
            br.layerId = str(uuid.uuid4()).upper()
            br.associatedMasterId = m.id
            coords = [round(v) for v in m.axes]
            coords[ytas_i] = ytas_top
            br.attributes["coordinates"] = coords
            br.name = f"YTAS{ytas_top}"

            top = next((a for a in br.anchors if a.name == "top"), None)
            if top is not None:
                top.position = Point(top.position.x + dx, top.position.y + dy)
                anchors += 1
            for c in br.components:
                if _is_top_mark(c.name):
                    c.position = Point(c.position.x + dx, c.position.y + dy)
            glyph.layers.append(br)

    print(f"   ✅ coordinated {anchors} top anchors — ascender bases ascend {dy_asc}u (1:1), "
          f"x-height bases {dy_xht}u (2:1), as ascenders extend {ytas_extent}u")
