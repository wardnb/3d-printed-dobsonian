"""Storage case and lifting handles for the lift-out mirror cell (2026-11-07).

The mirror + cell comes out of the box as one unit (cell.py, C["lift_out"]) and lives in this case between sessions.
The frame, not the mirror, takes the weight: three blocks under the 90/210/330 arms at the collimation-bolt radius,
two of them with a 5/16 pin that drops into the bolt's tapped hole so the unit cannot slide. The fan hangs below the
frame between the blocks. Lid with a foam ring that bears only on the frame's lugs/arms outside the mirror (never on
the glass), weatherstrip seal, two side handles.

Lifting handles: 3/8-16 T handles that screw into the frame's lugs at 60/240 deg and rise past the mirror face; removed
for observing (they stand in the light path).

Frame: same as cell.py (mirror face y = 0, tube axis +Y). Run from goto-rebuild/: python3 cell_case.py -> out/cell/case_*.
ASSUMED: 12 mm (0.47") birch for the case (18 mm works and weighs 40% more); fan 25 mm thick under the frame.
"""
import json
import math
import os

import cadquery as cq
from shapely.geometry import box as sbox, Point
from shapely.ops import unary_union

import cell

IN = 25.4
OUT = "out/cell"
os.makedirs(OUT, exist_ok=True)

K = dict(
    ply=0.47,                       # 12 mm Baltic birch (ASSUMED stock; 0.71 for 18 mm)
    clear=0.25,                     # radial clearance around the unit's r 8.75
    block=(2.0, 1.6, 1.6),          # support blocks (tangential x radial x tall): clear the 1.0" fan + 0.6
    block_r=None,                   # at the collimation-bolt radius (set from cell.C)
    pin_d=0.30, pin_h=0.4,          # 5/16 dowel into two of the bolt holes (the third block is plain)
    lid_gap=1.0,                    # foam-compressed gap over the mirror face
    foam_t=0.85,                    # closed-cell foam ring under the lid: rests on the guard-post tabs (top at +0.165), 0.25 off the glass
    seal=0.25,                      # weatherstrip on the top edge
    handle_rod=5.5, handle_grip=4.0, handle_d=0.75,   # T handles: 3/8-16 stud, rod rises past the face by ~1"
)


def derive(c=cell.C, k=K):
    L = cell.levels(c)
    R_unit = c["ring_id"] / 2 - c["lift_clear"]              # 8.75: everything on the unit is inside this
    inside = 2 * (R_unit + k["clear"])                       # 18.0 square inside
    k = dict(k)
    k["block_r"] = c["r_bolt"]
    depth_unit = -L["frame_bot"]                             # face to frame underside, 4.48
    inside_h = k["block"][2] + depth_unit + k["lid_gap"]     # floor to lid underside
    k.update(R_unit=R_unit, inside=inside, inside_h=round(inside_h, 2),
             outside=round(inside + 2 * k["ply"], 2), outside_h=round(inside_h + 2 * k["ply"], 2),
             fan_clear=round(k["block"][2] - 1.0, 2),
             handle_above_face=round(k["handle_rod"] - (-L["frame_top"]), 2),
             L=L)
    return k


def build(c=cell.C, k=None):
    k = k or derive(c)
    L = k["L"]
    ply, ins, h = k["ply"], k["inside"], k["inside_h"]
    y_floor_top = L["frame_bot"] - k["block"][2]              # the frame sits on the blocks
    S = {}
    def box(cx, cy, cz, sx, sy, sz):
        return cq.Workplane("XY").box(sx * IN, sy * IN, sz * IN).translate((cx * IN, cy * IN, cz * IN))
    S["case_floor"] = box(0, y_floor_top - ply / 2, 0, ins + 2 * ply, ply, ins + 2 * ply)
    yw = y_floor_top + h / 2
    S["case_walls"] = (box(0, yw, 0, ins + 2 * ply, h, ins + 2 * ply).cut(box(0, yw, 0, ins, h + 1, ins)))
    S["case_lid"] = box(0, y_floor_top + h + ply / 2, 0, ins + 2 * ply, ply, ins + 2 * ply)
    # foam ring under the lid: outside r R_unit+clear, inside r = mirror R + 0.25, 0.75 thick (bears on lugs/arms)
    R = c["mirror_dia"] / 2
    ring = (cq.Workplane("XZ").circle((k["R_unit"] + k["clear"]) * IN).circle((R + 0.25) * IN)
            .extrude(-k["foam_t"] * IN).translate((0, (y_floor_top + h - k["foam_t"]) * IN, 0)))
    S["case_foam"] = ring
    blocks = pins = None
    for i, a in enumerate(c["tri_angles"]):
        x, z = cell.pol(k["block_r"], a)
        b = (cq.Workplane("XY").box(k["block"][0] * IN, k["block"][2] * IN, k["block"][1] * IN)
             .translate((0, (y_floor_top + k["block"][2] / 2) * IN, k["block_r"] * IN))
             .rotate((0, 0, 0), (0, 1, 0), -(a - 90)))
        blocks = b if blocks is None else blocks.union(b)
        if i < 2:
            p = cell.cyl(x, z, y_floor_top + k["block"][2] - 0.05, k["pin_h"] + 0.05, k["pin_d"] / 2)
            pins = p if pins is None else pins.union(p)
    S["case_blocks"] = blocks
    S["case_pins"] = pins
    # T handles in the frame lugs
    hs = None
    for a in c["handle_lugs"]:
        x, z = cell.pol(c["handle_r"], a)
        rod = cell.cyl(x, z, L["frame_top"] - 0.5, k["handle_rod"] + 0.5, 0.1875)
        grip = (cq.Workplane("XY").cylinder(k["handle_grip"] * IN, k["handle_d"] / 2 * IN, direct=(1, 0, 0))
                .rotate((0, 0, 0), (0, 1, 0), -a).translate((x * IN, (L["frame_top"] + k["handle_rod"]) * IN, z * IN)))
        hh = rod.union(grip)
        hs = hh if hs is None else hs.union(hh)
    S["handles"] = hs
    return S, k


def flats(k):
    """2D parts for the DXFs (inches): floor, lid, two wall sizes, blocks."""
    ply, ins, h = k["ply"], k["inside"], k["inside_h"]
    F = {}
    F["case_floor_and_lid_x2"] = sbox(0, 0, ins + 2 * ply, ins + 2 * ply)
    F["case_wall_long_x2"] = sbox(0, 0, ins + 2 * ply, h)
    F["case_wall_short_x2"] = sbox(0, 0, ins, h)
    F["case_block_x3"] = sbox(0, 0, k["block"][0], k["block"][1])
    return F


def export(c=cell.C):
    S, k = build(c)
    F = flats(k)
    for name, poly in F.items():
        wp = cq.Workplane("XY").polyline([(x * IN, y * IN) for x, y in poly.exterior.coords[:-1]]).close().extrude(0.05 * IN)
        cq.exporters.export(wp.section(0.025 * IN), os.path.join(OUT, f"{name}_{'12mm' if k['ply'] < 0.6 else '18mm'}-birch.dxf"))
    asm = cq.Assembly(name="cell_case")
    P, L = cell.build(c)
    cols = dict(case_floor=(0.78, 0.66, 0.42), case_walls=(0.78, 0.66, 0.42), case_lid=(0.82, 0.72, 0.5), case_foam=(0.3, 0.3, 0.32),
                case_blocks=(0.7, 0.58, 0.36), case_pins=(0.3, 0.3, 0.3), handles=(0.5, 0.52, 0.55))
    for n, s in S.items():
        asm.add(s, name=n, color=cq.Color(*cols[n]))
    for n in ("frame", "edge_posts", "guard_posts", "mirror", "fan"):
        asm.add(P[n], name=n, color=cq.Color(0.74, 0.76, 0.79) if n != "mirror" else cq.Color(0.75, 0.85, 0.95))
    asm.save(os.path.join(OUT, "cell_case.step"))
    # checks: unit clear of the walls, fan clear of the floor, foam clear of the glass, handles above the face
    unit_r = c["ring_id"] / 2 - c["lift_clear"]
    case_lb = (2 * k["outside"] ** 2 + 4 * k["outside"] * k["outside_h"]) * k["ply"] * 0.025   # birch ~0.025 lb/in3
    rep = dict(inside_in=k["inside"], inside_h_in=k["inside_h"], outside_in=k["outside"], outside_h_in=k["outside_h"],
               unit_to_wall_in=round(k["inside"] / 2 - unit_r, 2), fan_to_floor_in=k["fan_clear"],
               foam_inner_r_minus_mirror_r_in=0.25, foam_bottom_above_face_in=round(k['lid_gap'] - k['foam_t'], 3), handle_grip_above_face_in=k["handle_above_face"],
               case_lb_est=round(case_lb, 1), carry_lb_est=round(23 + 6.1 + case_lb, 1),
               case_lb_if_18mm=round(case_lb * 0.71 / k["ply"], 1), case_lb_if_6mm=round(case_lb * 0.24 / k["ply"], 1),
               blocks_under_arms_deg=list(c["tri_angles"]), pins_in_bolt_holes=2,
               ok=k["inside"] / 2 - unit_r >= 0.2 and k["fan_clear"] >= 0.3 and k["handle_above_face"] >= 0.75)
    json.dump(rep, open(os.path.join(OUT, "case_report.json"), "w"), indent=1)
    return rep


if __name__ == "__main__":
    print(json.dumps(export(), indent=1))
