"""Rocker, ground board and bearing cut files (DXF per part for Aspire), fit checks and a cut sheet.
Run dob_model.py first (reads out/params.json), then: .venv/bin/python export_rocker.py"""
import json
import math
import os

import cadquery as cq
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

import rocker

IN = rocker.IN
HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "out", "rocker")
os.makedirs(OUT, exist_ok=True)
D = json.load(open(os.path.join(HERE, "out", "params.json")))
G = D["rocker"]
F = D["frame"]
ALTMILL = (48.6, 24.4)        # AltMill 2x4 cutting area, inches
SHEET = (60.0, 60.0)          # 5 x 5 Baltic birch

solids, flats, holes = rocker.build(G)
report = {}

# ---- box swing: everything inside the box's x range must stay outside its swing circle about the alt axis
swing, za, bx = G["swing"], G["z_alt"], F["bearing_x_in"]
clear = {}
for name, (sol, _) in solids.items():
    worst = None
    for sub in sol.solids().vals():                    # unions of separate pieces: check each piece
        bb = sub.BoundingBox()
        x0, x1 = bb.xmin / IN, bb.xmax / IN
        if x1 < -bx or x0 > bx:
            continue                                   # entirely outboard of the box
        y0, y1, z0, z1 = bb.ymin / IN, bb.ymax / IN, bb.zmin / IN, bb.zmax / IN
        dy = 0.0 if y0 <= 0 <= y1 else min(abs(y0), abs(y1))
        dz = 0.0 if z0 <= za <= z1 else min(abs(z0 - za), abs(z1 - za))
        c = math.hypot(dy, dz) - swing
        worst = c if worst is None else min(worst, c)
    if worst is not None:
        clear[name] = round(worst, 2)
report["box_swing_ok"] = all(v_ > 0 for v_ in clear.values())

# ---- bearings against the rocker at three altitudes (touching pads are fine; anything else is a clash)
def bearing_world(x_lo, alt):
    b = rocker.bearing_outline(G).translate(rocker.v(x_lo, 0, 0))
    b = b.rotate((0, 0, 0), (1, 0, 0), alt)                 # tube frame -> world: alt deg about X
    return b.translate(rocker.v(0, 0, za))

def bb_overlap(a, b):
    p, q = a.val().BoundingBox(), b.val().BoundingBox()
    return p.xmin <= q.xmax and q.xmin <= p.xmax and p.ymin <= q.ymax and q.ymin <= p.ymax and p.zmin <= q.zmax and q.zmin <= p.zmax

clash = {}
fixed = {k: s_ for k, (s_, _) in solids.items() if k not in ("alt_ptfe_pads",)}
for alt in (G["alt_min"], 45, 90):
    for side, x_lo in (("drive", F["bearing_x_in"]), ("plain", -F["bearing_x_out"])):
        b = bearing_world(x_lo, alt)
        for k, s_ in fixed.items():
            vol = b.intersect(s_).val().Volume() / IN ** 3 if bb_overlap(b, s_) else 0
            if vol > 0.002:
                clash[f"alt{alt}_{side}_{k}"] = round(vol, 3)
report["bearing_clashes_in3"] = clash

# ---- pads sit under the Ebony band, pinion inside the belt band, head over the tape
xi = F["bearing_x_in"]
eb, belt, tape = G["bands"]["ebony"], G["bands"]["belt"], G["bands"]["tape"]
pad = (G["pad_x"] - G["pad_w"] / 2 - xi, G["pad_x"] + G["pad_w"] / 2 - xi)
report["pad_inside_ebony_band"] = eb[0] <= pad[0] and pad[1] <= eb[1]
report["rim_bands_from_inner_face_in"] = G["bands"]

# ---- parts, DXFs and sizes
parts = []
for name, fl in flats.items():
    fn = f"{name}_18mm-birch.dxf"
    sec = fl["solid"].section(0.05 * IN)
    cq.exporters.export(sec, os.path.join(OUT, fn))
    w, h = fl["size"]
    parts.append(dict(part=name, qty=fl["qty"], size_in=(round(w, 2), round(h, 2)), stock=fl["stock"], dxf=fn,
                      fits_altmill=min(w, h) <= ALTMILL[1] and max(w, h) <= ALTMILL[0]))
report["parts"] = parts
report["all_parts_fit_altmill_2x4"] = all(p["fits_altmill"] for p in parts)
report["bracket_holes_yh_in"] = {k: [(round(a, 2), round(b, 2)) for a, b in v_] for k, v_ in holes.items()}
report["dims"] = {k: (round(G[k], 2) if isinstance(G[k], float) else G[k]) for k in (
    "inside_w", "box_clearance", "floor_w", "floor_l", "h_alt", "h_pad", "h_dip", "h_horn", "y_horn", "end_h", "end_h_max",
    "rocker_top", "chord_e", "alt_min", "pad_angle", "ring_od", "ring_id", "foot_r", "az_pad_r", "cap_z")}
report["ev6_ok_under_23in"] = G["rocker_top"] <= 23.0
report["bearing_lb_each"] = round(rocker.bearing_area_in2(G) * G["bearing_t"] * 0.0243, 2)

# ---- cut sheets (matplotlib)
def outline_xy(solid):
    """Sample the bottom face's wires into polylines (inches)."""
    polys = []
    for e in solid.faces("<Z").edges().vals():      # one polyline per edge (wire edge order is not contiguous)
        n = 1 if e.geomType() == "LINE" else 48
        pts = [(p.x / IN, p.y / IN) for p in e.positions([i / n for i in range(n + 1)], mode="length")]
        polys.append(pts)
    return polys

def place(ax, name, x, y, rot=0, label=None):
    fl = flats[name]
    bb = fl["solid"].val().BoundingBox()
    for poly in outline_xy(fl["solid"]):
        xs, ys = zip(*poly)
        if rot:
            xs, ys = [-(v_ - bb.ymin / IN) for v_ in ys], [v_ - bb.xmin / IN for v_ in xs]
            xs = [v_ + (bb.ylen / IN) for v_ in xs]
        else:
            xs, ys = [v_ - bb.xmin / IN for v_ in xs], [v_ - bb.ymin / IN for v_ in ys]
        ax.plot([x + v_ for v_ in xs], [y + v_ for v_ in ys], color="#333", lw=0.8)
    w, h = (bb.ylen, bb.xlen) if rot else (bb.xlen, bb.ylen)
    ax.text(x + w / IN / 2, y + h / IN / 2, label or name, ha="center", va="center", fontsize=7, color="#844")

fig, axes = plt.subplots(1, 2, figsize=(16, 8.4))
for ax, title in zip(axes, ("Sheet A: rocker + ground board (60 x 60, 18 mm birch)", "Sheet B: four bearing layers (60 x 60, 18 mm birch)")):
    ax.add_patch(plt.Rectangle((0, 0), *SHEET, fill=False, lw=1.5, color="#888"))
    ax.set_xlim(-1, 61); ax.set_ylim(-1, 61); ax.set_aspect("equal"); ax.set_title(title, fontsize=10)
    ax.set_xlabel("in")
A, B = axes
place(A, "ground_ring_half", 0.5, 0.5); place(A, "ground_ring_half", 30.5, 0.5)
place(A, "rocker_floor", 0.5, 16.0, rot=True)            # 27.4 wide x 24.05 tall
place(A, "rocker_wall_drive", 29.0, 16.0); place(A, "rocker_wall_plain", 29.0, 30.0)
place(A, "rocker_end", 0.5, 41.0); place(A, "rocker_end", 0.5, 45.5)
place(A, "ground_hub", 24.0, 41.0)
for i in range(3):
    place(A, "ground_arm", 33.0, 44.5 + i * 4.0)
for i, (x, y) in enumerate([(1.0, 1.0), (30.5, 1.0), (1.0, 20.0), (30.5, 20.0)]):
    place(B, "bearing_layer", x, y, label=f"bearing layer {i + 1}")
fig.tight_layout()
fig.savefig(os.path.join(OUT, "cut_sheet_rocker.png"), dpi=110)
json.dump(report, open(os.path.join(OUT, "fit_report.json"), "w"), indent=2)
print(json.dumps({k: v_ for k, v_ in report.items() if k not in ("parts", "bracket_holes_yh_in")}, indent=1))
for p in parts:
    print(f"{p['part']:20s} x{p['qty']}  {p['size_in'][0]:6.2f} x {p['size_in'][1]:6.2f}  {'ok' if p['fits_altmill'] else 'TOO BIG'}")
