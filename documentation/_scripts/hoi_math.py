import os
import math
import ufoLib2
from fontTools.designspaceLib import DesignSpaceDocument

DESIGNSPACE_PATH = "sources/CalSansUI_y_quads.designspace"
TARGET_GLYPHS = ["y"]

def get_hoi_point(p0, p100, t):
    """Calculates the parabolic shift for your manually placed quadratic nodes."""
    mid_x, mid_y = (p0[0] + p100[0]) / 2, (p0[1] + p100[1]) / 2
    dx, dy = p100[0] - p0[0], p100[1] - p0[1]
    dist = math.sqrt(dx**2 + dy**2)
    
    if dist == 0: return p0
    
    # Using the 14.6% arc offset to find the virtual P1
    offset = dist * 0.146
    nx, ny = -dy / dist, dx / dist 
    p1_x, p1_y = mid_x + (nx * offset), mid_y + (ny * offset)
    
    # Quadratic Bezier formula: (1-t)^2*P0 + 2(1-t)*t*P1 + t^2*P2
    res_x = (1-t)**2 * p0[0] + 2*(1-t)*t*p1_x + t**2 * p100[0]
    res_y = (1-t)**2 * p0[1] + 2*(1-t)*t*p1_y + t**2 * p100[1]
    return (res_x, res_y)

def clean_and_inject():
    if not os.path.exists(DESIGNSPACE_PATH):
        print(f"❌ Error: {DESIGNSPACE_PATH} not found.")
        return

    doc = DesignSpaceDocument.fromfile(DESIGNSPACE_PATH)
    
    # 1. DEDUPLICATE (Still necessary to prevent fontmake crash)
    unique_locs = set()
    cleaned_sources = []
    for s in doc.sources:
        loc_tuple = tuple(sorted(s.location.items()))
        if loc_tuple not in unique_locs:
            unique_locs.add(loc_tuple)
            cleaned_sources.append(s)
    doc.sources = cleaned_sources
    
    # 2. MAP GEOM AXIS
    axis = next((a for a in doc.axes if a.tag == "GEOM" or a.name == "Geometric Form"), None)
    if not axis:
        print("❌ Error: GEOM axis not found.")
        return
    
    # 3. LOAD FONTS (Directly from UFO, no conversion)
    loaded_fonts = {s.path: ufoLib2.Font.open(s.path) for s in doc.sources}

    # 4. GROUP BY SHARED COORDINATES (opsz, wght, slnt)
    groups = {}
    for s in doc.sources:
        loc = dict(s.location)
        g_val = loc.pop(axis.name, 0)
        group_key = tuple(sorted(loc.items()))
        if group_key not in groups: groups[group_key] = {}
        groups[group_key][g_val] = loaded_fonts[s.path]

    # 5. APPLY HOI SHIFT
    for group_key, masters in groups.items():
        g_min, g_max = min(masters.keys()), max(masters.keys())
        if g_min == g_max: continue
        
        f0, f100 = masters[g_min], masters[g_max]
        for g_val, ufo in masters.items():
            if g_val in [g_min, g_max]: continue
            
            t = (g_val - g_min) / (g_max - g_min)
            print(f"🌀 Adjusting {TARGET_GLYPHS} at {group_key} | GEOM:{g_val} (t={t})")
            
            for name in TARGET_GLYPHS:
                if name not in ufo or name not in f0 or name not in f100: continue
                
                for c_idx, contour in enumerate(ufo[name].contours):
                    # Safety check for contour index
                    if c_idx >= len(f0[name].contours) or c_idx >= len(f100[name].contours):
                        continue
                        
                    for p_idx, point in enumerate(contour.points):
                        try:
                            p0 = (f0[name].contours[c_idx].points[p_idx].x, 
                                  f0[name].contours[c_idx].points[p_idx].y)
                            p100 = (f100[name].contours[c_idx].points[p_idx].x, 
                                    f100[name].contours[c_idx].points[p_idx].y)
                            
                            point.x, point.y = get_hoi_point(p0, p100, t)
                        except IndexError:
                            # If point counts still mismatch, skip and warn
                            print(f"⚠️ Index mismatch in {name} at pt {p_idx} (Group: {group_key})")
                            continue
            ufo.save()

    # 6. SAVE DESIGNSPACE
    doc.write(DESIGNSPACE_PATH)
    print("✅ HOI Injection complete using manual quadratic nodes.")

if __name__ == "__main__":
    clean_and_inject()