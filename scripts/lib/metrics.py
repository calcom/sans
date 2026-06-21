"""Step 1 of the build — measure each master's metrics and stem widths and dump them to
sources/metrics.json (an optical-size design reference)."""
import os
import json
import glyphsLib

def measure_round_targets(font, master, stems_dict):
    """Measures the O and o bounding boxes to find the true optical target thickness."""
    deltas = {}
    
    # Grab base stems, default to 0 if missing so it doesn't crash
    stem_v_val = stems_dict.get("Stem_V", 0) 
    stem_h_val = stems_dict.get("Stem_H", 0)

    for glyph_name in ["O", "o"]:
        if glyph_name not in font.glyphs: continue
        glyph = font.glyphs[glyph_name]
        
        layer = next((l for l in glyph.layers if l.layerId == master.id), None)
        if not layer or len(layer.paths) < 2: continue 

        # Sort paths by area. Largest is outer, smallest is inner.
        paths_sorted = sorted(layer.paths, key=lambda p: p.bounds.size.width * p.bounds.size.height, reverse=True)
        outer, inner = paths_sorted[0], paths_sorted[1]

        # Calculate exact bounding box extremes
        outer_top = outer.bounds.origin.y + outer.bounds.size.height
        inner_top = inner.bounds.origin.y + inner.bounds.size.height
        outer_bottom = outer.bounds.origin.y
        inner_bottom = inner.bounds.origin.y
        
        outer_left = outer.bounds.origin.x
        inner_left = inner.bounds.origin.x
        outer_right = outer.bounds.origin.x + outer.bounds.size.width
        inner_right = inner.bounds.origin.x + inner.bounds.size.width

        # Calculate average thicknesses
        avg_h_thick = ((outer_top - inner_top) + (inner_bottom - outer_bottom)) / 2
        avg_v_thick = ((inner_left - outer_left) + (outer_right - inner_right)) / 2

        prefix = "UC" if glyph_name == "O" else "LC"
        
        # Save the optical deltas and the absolute targets
        if stem_h_val > 0: deltas[f"{prefix}_Round_H_Delta"] = round(avg_h_thick - stem_h_val, 2)
        if stem_v_val > 0: deltas[f"{prefix}_Round_V_Delta"] = round(avg_v_thick - stem_v_val, 2)
        
        deltas[f"{prefix}_Target_H"] = round(avg_h_thick, 2)
        deltas[f"{prefix}_Target_V"] = round(avg_v_thick, 2)

    return deltas

def export_metrics(source_path):
    print("📊 Extracting Master Metrics, Stems, and Optical Targets...")
    font = glyphsLib.load(source_path)
    
    data = {
        "masters": {},
        "kerning": {}
    }

    # Map the font's stem names to their index
    stem_names = [s.name for s in font.stems] if hasattr(font, 'stems') else []

    for master in font.masters:
        master_data = {
            "name": master.name,
            "metrics": {},
            "stems": {},
            "optical_targets": {}
        }

        # 1. Extract Metrics
        if hasattr(master, "metrics"):
            for metric in master.metrics:
                if metric.position is not None:
                    # Glyphs 3 uses metric types, but we can store them by index/position
                    master_data["metrics"][f"metric_{metric.position}"] = metric.position
        
        # Fallback for core properties if needed
        master_data["metrics"]["capHeight"] = master.capHeight
        master_data["metrics"]["xHeight"] = master.xHeight
        master_data["metrics"]["ascender"] = master.ascender
        master_data["metrics"]["descender"] = master.descender

        # 2. Extract Stems
        for i, stem_val in enumerate(master.stems):
            name = stem_names[i] if i < len(stem_names) else f"stem_{i}"
            master_data["stems"][name] = stem_val

        # 3. Extract Optical Targets (The Delta Engine!)
        master_data["optical_targets"] = measure_round_targets(font, master, master_data["stems"])

        data["masters"][master.id] = master_data

        # 4. Extract Kerning
        if master.id in font.kerning:
            data["kerning"][master.id] = font.kerning[master.id]

    # Save it
    json_path = os.path.join(os.path.dirname(source_path), "metrics.json")
    with open(json_path, "w") as f:
        json.dump(data, f, indent=4)
        
    print(f"   ✅ Saved to {json_path}")