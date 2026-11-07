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
fixed = {k: s_ for k, (s_, _) in solids.items() if k not in ("alt_ptfe_pads", "alt_rollers", "alt_track_strips")}
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
eb, belt, tape = G["run_band"], G["bands"]["belt"], G["bands"]["tape"]
pw = G["roller_w"] if G["kind"] == "rollers" else G["pad_w"]
pad = (G["pad_x"] - pw / 2 - xi, G["pad_x"] + pw / 2 - xi)
report["pad_inside_running_band"] = eb[0] <= pad[0] and pad[1] <= eb[1]
report["bearing_kind"] = G["kind"]
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

# ---- drive modules (drive.py): arm plate DXFs (1/4" 6061, same parts on both axes), numbers, az sweep check
import drive
DOUT = os.path.join("out", "drive")
os.makedirs(DOUT, exist_ok=True)
for name, fl in drive.flats().items():
    cq.exporters.export(fl["solid"].section(0.05 * IN), os.path.join(DOUT, f"{name}_x{fl['qty']}_quarter-inch-6061.dxf"))
drep = drive.numbers()
drep["arm_plates_lb_per_axis"] = drive.arm_lb()
drep["arm_plate_size_in"] = drive._size()
drep["holes_A"] = [(round(u, 3), round(w, 3), round(d, 3), k) for u, w, d, k in drive.arm_holes("A")]
drep["holes_B"] = [(round(u, 3), round(w, 3), round(d, 3), k) for u, w, d, k in drive.arm_holes("B")]
ground = {k: solids[k][0] for k in ("ground_board", "ground_ring", "feet", "az_ptfe", "az_track") if k in solids}
azm = {k: s_ for k, (s_, _) in drive.module(G, "az").items() if "pinion" not in k}
sweep = []
for ang in range(0, 360, 20):
    for mk, ms in azm.items():
        r_ = ms.rotate((0, 0, 0), (0, 0, 1), ang)
        for gk, gs in ground.items():
            if bb_overlap(r_, gs) and r_.intersect(gs).val().Volume() / IN ** 3 > 0.002:
                sweep.append((ang, mk, gk))
drep["az_module_clears_ground_board_360"] = not sweep
drep["az_sweep_clashes"] = sweep
drep["pinion_lift_in"] = drive.LIFT
report["drive"] = drep
json.dump(drep, open(os.path.join(DOUT, "drive_report.json"), "w"), indent=1)

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
    "bearing 2 (+ box wings)": (BLANK, [("bearing_layer", 0.5, 0.5, 0), ("box_side_wing", 29.5, 0.5, 0), ("box_side_wing", 35.0, 0.5, 0)]),
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
# ---- roller bearings (2026-11-07): az track ring thirds + flange plates (1/8 6061 DXF, nested on a 12 x 48 blank),
# roller block STEPs (1-1/2 x 2 bar), and the numbers the blocks are built from
if G["kind"] == "rollers":
    ra, tt = G["az_pad_r"], G["az_track_t"]
    # four 90 deg segments (bbox 18.7 x 4.6: four nest on a 12 x 48 blank; 120 deg thirds would need 24 x 24),
    # joints at 45/135/225/315 so none lands on the birch ring's joints at 90/210/330
    s45 = math.sin(math.radians(45))
    ro, ri = ra + 0.5, ra - 0.5
    quarter = (cq.Workplane("XY").moveTo(-ro * s45 * IN, ro * s45 * IN).threePointArc((0, ro * IN), (ro * s45 * IN, ro * s45 * IN))
               .lineTo(ri * s45 * IN, ri * s45 * IN).threePointArc((0, ri * IN), (-ri * s45 * IN, ri * s45 * IN)).close()
               .extrude(0.05 * IN))
    for da in (-36, -18, 0, 18, 36):                        # #8 FHCS countersunk flush every 18 deg (rollers roll over them)
        a = math.radians(da)
        quarter = quarter.cut(cq.Workplane("XY").center(ra * math.sin(a) * IN, ra * math.cos(a) * IN).circle(0.085 * IN).extrude(0.05 * IN))
    cq.exporters.export(quarter.section(0.025 * IN), os.path.join(OUT, "az_track_quarter_x4_eighth-inch-6061.dxf"))
    plate = cq.Workplane("XY").rect((G["blk_w"] + 1.0) * IN, (G["blk_l"] + 1.0) * IN).extrude(0.05 * IN)
    plate = plate.cut(cq.Workplane("XY").slot2D(1.5 * IN, 0.5 * IN, 90).extrude(0.05 * IN))      # roller clearance slot
    for dx, dy in ((0, -0.6), (0, 0.6)):                      # 1/4-20 into the block
        plate = plate.cut(cq.Workplane("XY").center(dx * IN, dy * IN).circle(0.135 * IN).extrude(0.05 * IN))
    for dx in (-(G["blk_w"] / 2 + 0.3), G["blk_w"] / 2 + 0.3):   # #10 wood screws into the floor
        for dy in (-1.0, 1.0):
            plate = plate.cut(cq.Workplane("XY").center(dx * IN, dy * IN).circle(0.1 * IN).extrude(0.05 * IN))
    cq.exporters.export(plate.section(0.025 * IN), os.path.join(OUT, "az_flange_plate_x4_eighth-inch-6061.dxf"))
    # nest check on 12 x 48: quarters in two columns x two rows, plates in the leftover strip
    from shapely.geometry import Polygon as _Poly
    from shapely import affinity as _aff
    def _arc(r, a0, a1, n=90):
        return [(r * math.sin(math.radians(a0 + (a1 - a0) * i / n)), r * math.cos(math.radians(a0 + (a1 - a0) * i / n))) for i in range(n + 1)]
    qp = _Poly(_arc(ro, -45, 45) + _arc(ri, 45, -45))
    qb = qp.bounds
    q_w, q_h = qb[2] - qb[0], qb[3] - qb[1]
    placed_ = [_aff.translate(qp, 0.5 - qb[0] + col * (q_w + 0.6), 0.5 - qb[1] + row * (q_h + 0.6))
               for col in (0, 1) for row in (0, 1)]
    pl_w, pl_h = G["blk_w"] + 1.0, G["blk_l"] + 1.0
    px0 = 2 * (q_w + 0.6) + 0.5
    for i in range(4):
        x0_, y0_ = px0 + (i // 2) * (pl_w + 0.4), 0.5 + (i % 2) * (pl_h + 0.4)
        placed_.append(_Poly([(x0_, y0_), (x0_ + pl_w, y0_), (x0_ + pl_w, y0_ + pl_h), (x0_, y0_ + pl_h)]))
    okn = all(p.bounds[2] <= 48 and p.bounds[3] <= 12 for p in placed_)
    okn = okn and all(placed_[i].distance(placed_[j]) >= 0.3 for i in range(len(placed_)) for j in range(i + 1, len(placed_)))
    report["az_track_nest_12x48_ok"] = bool(okn)
    report["az_track_quarter_bbox_in"] = (round(q_w, 2), round(q_h, 2))
    for nm, hh, sad in (("alt_roller_block", G["blk_h_alt"], True), ("az_roller_block", G["blk_h_az"], False)):
        b_, r_, a_ = rocker.roller_block(G, hh, sad)
        cq.exporters.export(b_, os.path.join(OUT, f"{nm}.step"))
    report["rollers"] = dict(roller="R10 5/8 x 1-3/8 x 11/32", axle="5/8 x 1 shoulder bolt", track_alt="1/16 x 5/8 6061 strip on the rim",
                             track_az="1/8 6061 ring r 12.25-13.25 in four 90 deg segments", block_w_l_in=(G["blk_w"], G["blk_l"]),
                             block_h_alt_az_in=(G["blk_h_alt"], G["blk_h_az"]), axle_below_block_top_in=G["axle_from_top"],
                             slot_w_d_in=(G["slot_w"], G["slot_d"]), saddle_depth_in=G["saddle_d"],
                             r_track=round(G["r_track"], 4), r_axle=round(G["r_axle"], 4), r_block_top=round(G["r_blk_top"], 3),
                             r_notch_wall_top=round(G["r_notch"], 3), cross_bolt_r=round(G["blk_bolt_r"], 3),
                             floor_over_ground_ring_in=round(G["floor_z0"] - G["ground_top"], 3),
                             lateral_tab_clearance_in=G["tab_clear"])
json.dump(report, open(os.path.join(OUT, "fit_report.json"), "w"), indent=2)
print(json.dumps({k: v_ for k, v_ in report.items() if k not in ("parts", "bracket_holes_yh_in", "blanks")}, indent=1))
for b in blank_report:
    print(f"{b['blank']:28s} {b['size_in'][0]:5.1f} x {b['size_in'][1]:4.1f}  inside={b['inside_margin']}  {b['parts']}")
for p in parts:
    print(f"{p['part']:20s} x{p['qty']}  {p['size_in'][0]:6.2f} x {p['size_in'][1]:6.2f}  {'ok' if p['fits_altmill'] else 'TOO BIG'}")
