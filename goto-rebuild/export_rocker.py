"""Rocker, ground board and bearing cut files (DXF per part for Aspire), fit checks and a cut layout on AltMill-sized blanks (24.4 x 48, ripped from 5 x 5 sheets).
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
BLANK = (48.0, 24.4)          # one blank = a 24.4 x 60 strip ripped from a 5 x 5 sheet, crosscut to 48 (fills the AltMill bed)
MARGIN, GAP = 0.5, 0.5        # part to blank edge, part to part

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

# ---- cut layout on AltMill-sized blanks (shapely checks every placement)
from shapely.geometry import Polygon, box as sbox
from shapely import affinity

def wire_pts(wire):
    """Ordered points (inches) around a CadQuery wire: sample each edge, then chain the edges by their endpoints."""
    segs = []
    for e in wire.Edges():
        n = 1 if e.geomType() == "LINE" else 64
        segs.append([(p.x / IN, p.y / IN) for p in e.positions([i / n for i in range(n + 1)], mode="length")])
    out = segs.pop(0)
    while segs:
        for i, sg in enumerate(segs):
            if abs(sg[0][0] - out[-1][0]) + abs(sg[0][1] - out[-1][1]) < 1e-6:
                out += sg[1:]; break
            if abs(sg[-1][0] - out[-1][0]) + abs(sg[-1][1] - out[-1][1]) < 1e-6:
                out += sg[::-1][1:]; break
        else:
            raise RuntimeError("open wire")
        segs.pop(i)
    return out

def flat_poly(name):
    f = flats[name]["solid"].faces("<Z").val()
    return Polygon(wire_pts(f.outerWire()), [wire_pts(w) for w in f.innerWires()])

def placed(name, x, y, rot=0):
    """Part rotated by rot degrees, then moved so its bounding box starts at (x, y) on the blank."""
    p = affinity.rotate(flat_poly(name), rot, origin="centroid")
    bx0, by0, _, _ = p.bounds
    return affinity.translate(p, x - bx0, y - by0)

# blanks: name -> (size, [(part, x, y, rot)])
Lw, s_wall = G["L"], 13.0                   # the second wall nests inverted, shifted 13" along the first
LAYOUT = {
    "bearing 1 (+ ends, hub)": (BLANK, [("bearing_layer", 0.5, 0.5, 0), ("rocker_end", 29.5, 0.5, 90), ("rocker_end", 34.0, 0.5, 90),
                                        ("ground_hub", 38.5, 0.5, 0)]),
    "bearing 2": (BLANK, [("bearing_layer", 0.5, 0.5, 0)]),
    "bearing 3": (BLANK, [("bearing_layer", 0.5, 0.5, 0)]),
    "bearing 4": (BLANK, [("bearing_layer", 0.5, 0.5, 0)]),
    "walls (+ arms)": (BLANK, [("rocker_wall_drive", 0.5, 0.5, 0), ("rocker_wall_plain", 0.5 + s_wall, BLANK[1] - 0.5 - G["h_horn"], 180),
                               ("ground_arm", 0.5, 13.9, 0), ("ground_arm", 0.5, 17.9, 0), ("ground_arm", 0.5 + s_wall + Lw + 0.6, 0.5, 90)]),
    "ring thirds": ((32.3, 24.4), [("ground_ring_third", 0.5, 0.5, 0), ("ground_ring_third", 0.5, 6.7, 0), ("ground_ring_third", 0.5, 12.9, 0)]),
}
FLOOR_NOTE = ("rocker_floor: rip the 24.4 strip to %.2f and crosscut to %.2f on the table saw; "
              "the AltMill (or a hand drill from the DXF) does the pivot and pilot holes" % (G["floor_w"], G["floor_l"]))

blank_report, overlaps, polys_by_blank = [], [], {}
for bname, (size, items) in LAYOUT.items():
    inner = sbox(MARGIN - 1e-4, MARGIN - 1e-4, size[0] - MARGIN + 1e-4, size[1] - MARGIN + 1e-4)
    ps = [(n, placed(n, x, y, r)) for n, x, y, r in items]
    polys_by_blank[bname] = ps
    inside = all(inner.contains(p) for _, p in ps)
    for i in range(len(ps)):
        for j in range(i + 1, len(ps)):
            d = ps[i][1].distance(ps[j][1])
            if d < GAP - 1e-6:
                overlaps.append((bname, ps[i][0], ps[j][0], round(d, 3)))
    blank_report.append(dict(blank=bname, size_in=size, parts=[n for n, _ in ps], inside_margin=inside,
                             fits_altmill=size[0] <= ALTMILL[0] and size[1] <= ALTMILL[1]))
placed_counts = {}
for _, (_, items) in LAYOUT.items():
    for n, *_ in items:
        placed_counts[n] = placed_counts.get(n, 0) + 1
missing = {n: f["qty"] - placed_counts.get(n, 0) for n, f in flats.items() if placed_counts.get(n, 0) != f["qty"]}
report["blanks"] = blank_report
report["blank_overlaps"] = overlaps
report["blank_parts_unplaced"] = missing            # rocker_floor is table-sawn (see floor_note)
report["floor_note"] = FLOOR_NOTE
report["sheets_5x5"] = "3: each ripped into two 24.4 x 60 strips; sheet 3 strip B = floor (27.4) + ring thirds blank (32.3)"
report["layout_ok"] = all(b["inside_margin"] and b["fits_altmill"] for b in blank_report) and not overlaps and missing == {"rocker_floor": 1}

fig, axes = plt.subplots(2, 4, figsize=(22, 11.5))
axes = axes.ravel()
for ax, (bname, (size, _)) in zip(axes, LAYOUT.items()):
    ax.add_patch(plt.Rectangle((0, 0), *size, fill=False, lw=1.5, color="#888"))
    ax.add_patch(plt.Rectangle((MARGIN, MARGIN), size[0] - 2 * MARGIN, size[1] - 2 * MARGIN, fill=False, lw=0.5, ls=":", color="#aaa"))
    for n, p in polys_by_blank[bname]:
        xs, ys = p.exterior.xy
        ax.plot(xs, ys, color="#333", lw=0.8)
        for ring in p.interiors:
            ax.plot(*ring.xy, color="#333", lw=0.6)
        c = p.centroid
        x0_, y0_, x1_, y1_ = p.bounds
        ax.text(c.x, c.y, n.replace("_", " "), ha="center", va="center", fontsize=7, color="#844",
                rotation=90 if (y1_ - y0_) > (x1_ - x0_) else 0)
    ax.set_xlim(-1, 49); ax.set_ylim(-1, 25.4); ax.set_aspect("equal")
    ax.set_title(f"{bname}  ({size[0]:.1f} x {size[1]:.1f} blank)", fontsize=10); ax.set_xlabel("in")
ax = axes[len(LAYOUT)]
axes[-1].axis("off")
fw, fl_ = G["floor_w"], G["floor_l"]
ax.add_patch(plt.Rectangle((0, 0), fl_, fw, fill=False, lw=1.5, color="#888"))
fp = placed("rocker_floor", 0, 0, 90)
for ring in fp.interiors:
    ax.plot(*ring.xy, color="#333", lw=0.6)
ax.text(fl_ / 2, fw / 2, "rocker floor\n(table saw; AltMill drills)", ha="center", va="center", fontsize=8, color="#844")
ax.set_xlim(-1, 49); ax.set_ylim(-1, 25.4); ax.set_aspect("equal")
ax.set_title(f"floor  ({fl_:.2f} x {fw:.2f}, ripped from a 24.4 strip)", fontsize=10); ax.set_xlabel("in")
fig.suptitle("Cut layout, 18 mm Baltic birch: three 5 x 5 sheets ripped into 24.4 x 60 strips; every blank fits the AltMill 2x4 (48.6 x 24.4)", fontsize=11)
fig.tight_layout()
fig.savefig(os.path.join(OUT, "cut_sheet_rocker.png"), dpi=110)
json.dump(report, open(os.path.join(OUT, "fit_report.json"), "w"), indent=2)
print(json.dumps({k: v_ for k, v_ in report.items() if k not in ("parts", "bracket_holes_yh_in", "blanks")}, indent=1))
for b in blank_report:
    print(f"{b['blank']:28s} {b['size_in'][0]:5.1f} x {b['size_in'][1]:4.1f}  inside={b['inside_margin']}  {b['parts']}")
for p in parts:
    print(f"{p['part']:20s} x{p['qty']}  {p['size_in'][0]:6.2f} x {p['size_in'][1]:6.2f}  {'ok' if p['fits_altmill'] else 'TOO BIG'}")
