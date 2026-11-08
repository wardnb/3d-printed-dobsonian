"""
Drive modules (2026-10-31): the same swing-arm on both axes.

    gearmotor (Pittman, 19.7:1) -> 16T GT2 -> 6 mm GT2 loop -> 32T (2:1) or 48T (3:1) on an 8 mm jackshaft
    -> 20T flangeless GT2 pinion meshing the 9 mm GT2 belt glued teeth-out on the rim.

The arm is two 1/4" 6061 plates (A next to the pinion, B carrying the motor) joined by three standoffs. It pivots on a
3/8" shoulder bolt placed ON THE RIM TANGENT through the pinion, so the drive force passes through the pivot (it
neither pulls the pinion in nor out); only the tooth separating force acts on the spring. The motor rides on the arm,
so the belt centre distance never changes with the swing; its mounting holes are slotted for tension and for the
2:1 / 3:1 swap (152 mm and 170 mm closed loops both fall at c ~ 52 mm).

Clutch: a compression spring under the arm's tail pushes the pinion into the belt (~25 lb at the pinion); a guide rod
through the tail carries an over-centre cam lever that pulls the tail back ~4 mm, lifting the pinion ~3 mm clear.

Local module frame (inches): origin at the pinion centre on the belt mid-plane; u along the rim tangent from the
pinion toward the pivot; w from the pinion toward the rim (the direction the spring pushes the pinion); s along the
shaft, from the pinion toward the arm stack. place(axis, G) maps it into the world.
"""
import math

import cadquery as cq
from shapely.geometry import Point
from shapely.ops import unary_union

IN = 25.4

# ---- bought parts (GT2 2 mm pitch)
PITCH = 2.0                                     # mm
PD = lambda n: n * PITCH / math.pi / IN         # pitch diameter, in
OD = lambda n: PD(n) - 0.508 / IN               # GT2 outside diameter
PINION_T = 20
MOTOR_T = 16                                    # 1/4" bore (the gearbox shaft is 1/4")
JACK_T = {"2:1": 32, "3:1": 48}
LOOP_MM = {"2:1": 152, "3:1": 170}              # standard GT2-6 mm closed loops
SHAFT_D = 8 / IN
MOTOR_SHAFT_L = 0.70                            # MEASURED 2026-11-08 flange face to tip (drawing said 0.75); dia 0.245 (1/4" bore pulley, set screw on the flat)
PULLEY_W = 0.55                                 # GT2 pulley hub + teeth width
S_PULLEY_FROM_B = 0.62                          # pulleys this far inboard of plate B: 16T engages the outer 0.38" of the 0.70" shaft (the flats), 0.07 clear of plate B
BRG_OD, BRG_W, BRG_FL = 22 / IN, 7 / IN, 25 / IN     # F608ZZ flanged
PLATE_T = 0.25
PLATE_GAP = 0.80                                # between plates A and B (pulleys live here)
# ---- arm layout along u (inches)
C_NOM = 52.0 / IN                               # motor-to-jackshaft centre distance
SLOT = 0.10                                     # +/- motor slot along u
U_PIVOT = 4.0
U_TAIL = -1.3                                   # spring / cam rod
R_LOBE = dict(jack=0.75, motor=1.32, pivot=0.50, tail=0.42)   # motor lobe takes the Ø1.125 pilot slot + the 1.63" square screw pattern
# ---- motor (Pittman GM9000 family) -- ASSUMED until Nick measures the gearbox face
MOTOR_R, MOTOR_L = 0.80, 4.6
MOTOR_HOLES = [(sx * 0.815, sw * 0.815) for sx in (1, -1) for sw in (1, -1)]   # MEASURED 2026-11-08: four Ø0.15 clearance holes
                                                # (not tapped) on a 1.63" square at the flange corners -> #6-32 screws through the
                                                # flange and plate B's slots, nyloc nuts between the plates
# ---- spring / clutch
PRELOAD_LB = 25.0                               # at the pinion (rim force ~12 lb; GT2 rack-style mesh needs ~2x)
LIFT = 0.12                                     # pinion lift when the cam is thrown (3 mm)


def belt_c(n1, n2, loop_mm):
    """Centre distance (mm) for a closed GT2 loop."""
    p1, p2 = n1 * PITCH / math.pi, n2 * PITCH / math.pi
    L = loop_mm
    b = L - math.pi * (p1 + p2) / 2
    return (b + math.sqrt(b * b - 2 * (p2 - p1) ** 2)) / 4


def numbers():
    out = {}
    for k, n in JACK_T.items():
        c = belt_c(MOTOR_T, n, LOOP_MM[k])
        out[k] = dict(jack_teeth=n, loop_mm=LOOP_MM[k], centre_mm=round(c, 2),
                      slot_offset_in=round(c / IN - C_NOM, 3))
    lever = (U_PIVOT - U_TAIL) / U_PIVOT
    out["spring_force_lb"] = round(PRELOAD_LB / lever, 1)
    out["tail_stroke_in"] = round(LIFT * lever, 3)
    return out


# hardware drawn so that every part touches what it mounts to (2026-11-08; all ASSUMED until the parts are in hand)
FLANGE_SQ, FLANGE_T = 2.0, 0.20                 # Pittman GM9000 gearbox face: 2.00" square (measured 2026-11-08, 1.992-1.997), thickness ASSUMED
PILOT_R, PILOT_H = 0.5625, 0.06                 # gearbox pilot boss Ø1.125 (-0.002/+0, GM9000 drawing) into a 1.13" hole in plate B; height ASSUMED
PIVOT_SPACER_R = 0.35                           # turned 6061 spacer on the pivot bolt between the bracket and plate A/B
NUT_AF, NUT_T = 0.5625, 0.22                    # 3/8-16 nyloc on the pivot bolt
ROD_R = 0.125                                   # 1/4" guide rod through the tail
SPRING_R, SPRING_WIRE = 0.28, 0.06              # alt compression spring (19 lb at the working length)


def arm_poly():
    """Arm plate outline in (u, w) as a shapely polygon (convex hull of the four lobes)."""
    lobes = [Point(0, 0).buffer(R_LOBE["jack"], 64), Point(C_NOM, 0).buffer(R_LOBE["motor"], 64),
             Point(U_PIVOT, 0).buffer(R_LOBE["pivot"], 64), Point(U_TAIL, 0).buffer(R_LOBE["tail"], 64)]
    return unary_union(lobes).convex_hull


STANDOFFS = [(-0.55, 0.55), (U_PIVOT - 0.9, 0.45), (U_PIVOT - 0.9, -0.45)]   # third moved off the motor lobe 2026-11-08 (it sat on the #10-32 screw)


def arm_holes(plate):
    """(u, w, dia, kind) for plate 'A' (pinion side) or 'B' (motor side)."""
    h = [(0, 0, BRG_OD, "F608 bearing bore"), (U_PIVOT, 0, 0.500, "3/8 shoulder bolt in a 3/8 x 1/2 flanged bronze bushing"),
         (U_TAIL, 0, 0.281, "1/4 guide rod")]
    h += [(u, w, 0.201, "#10 standoff") for u, w in STANDOFFS]
    if plate == "B":
        h.append((C_NOM, 0, 2 * PILOT_R + 0.005, f"gearbox pilot Ø1.125, slot +/-{SLOT} (locates the motor in w, slides for belt tension)"))
        h += [(C_NOM + du, dw, 0.15, f"#6-32 motor screw, slot +/-{SLOT}") for du, dw in MOTOR_HOLES]
    return h


def arm_flat(plate, thick=0.1):
    p = arm_poly()
    wp = cq.Workplane("XY").polyline([(x * IN, y * IN) for x, y in list(p.exterior.coords)[:-1]]).close().extrude(thick * IN)
    for u, w, d, kind in arm_holes(plate):
        if "slot" in kind:
            wp = wp.cut(cq.Workplane("XY").center(u * IN, w * IN).slot2D((2 * SLOT + d) * IN, d * IN).extrude(thick * IN))
        else:
            wp = wp.cut(cq.Workplane("XY").center(u * IN, w * IN).circle(d / 2 * IN).extrude(thick * IN))
    return wp


def arm_lb():
    return round(arm_poly().area * PLATE_T * 0.0975 * 2, 2)


# --------------------------------------------------------------------------
def frames(G):
    """Per-axis placement: origin, e_u, e_w, e_s (world, inches) and the s of plate A's inner face."""
    xi = G["bearing_x_in"]
    b = G["bands"]["belt"]
    alt = dict(O=(xi + (b[0] + b[1]) / 2, 0.0, G["cap_z"]), e_u=(0, 1, 0), e_w=(0, 0, 1), e_s=(1, 0, 0),
               sA=(G["bearing_x_out"] + 0.16) - (xi + (b[0] + b[1]) / 2))
    px, py = G["az_pinion_xy"]
    r = math.hypot(px, py)
    ew = (-px / r, -py / r, 0.0)
    eu = (py / r, -px / r, 0.0)                  # tangent, away from the drive wall
    az = dict(O=(px, py, G["ground_top"] - 0.18), e_u=eu, e_w=ew, e_s=(0, 0, 1), sA=(G["floor_z0"] + 0.04) - (G["ground_top"] - 0.18))
    return dict(alt=alt, az=az)


def _plane(F):
    O, eu, es = F["O"], F["e_u"], F["e_s"]
    pl = cq.Plane(origin=cq.Vector(*[c * IN for c in O]), xDir=cq.Vector(*eu), normal=cq.Vector(*es))
    ydir = pl.yDir
    sgn = 1.0 if (ydir.x * F["e_w"][0] + ydir.y * F["e_w"][1] + ydir.z * F["e_w"][2]) > 0 else -1.0
    return pl, sgn


def _cyl(pl, sgn, u, w, s0, length, r):
    return cq.Workplane(pl).center(u * IN, sgn * w * IN).circle(r * IN).extrude(length * IN).translate(
        pl.zDir.multiply(s0 * IN))


def _box(pl, sgn, u, w, s0, du, dw, ds):
    return cq.Workplane(pl).center(u * IN, sgn * w * IN).rect(du * IN, dw * IN).extrude(ds * IN).translate(
        pl.zDir.multiply(s0 * IN))


def _strip(pl, sgn, p0, p1, width, s0, ds):
    """A flat strip of the given width from local (u, w) p0 to p1, extruded along s."""
    (u0, w0), (u1, w1) = p0, p1
    L = math.hypot(u1 - u0, w1 - w0)
    nx, ny = -(w1 - w0) / L * width / 2, (u1 - u0) / L * width / 2
    pts = [(u0 + nx, w0 + ny), (u1 + nx, w1 + ny), (u1 - nx, w1 - ny), (u0 - nx, w0 - ny)]
    return (cq.Workplane(pl).polyline([(u * IN, sgn * w * IN) for u, w in pts]).close().extrude(ds * IN)
            .translate(pl.zDir.multiply(s0 * IN)))


def _wpt(F, u, w, s):
    """Local (u, w, s) -> world cq.Vector in mm."""
    O, eu, ew, es = F["O"], F["e_u"], F["e_w"], F["e_s"]
    return cq.Vector(*[(O[i] + u * eu[i] + w * ew[i] + s * es[i]) * IN for i in range(3)])


def _cyl_w(F, u, w0, w1, s, r):
    """Cylinder along the local w axis from w0 to w1 (springs, guide rods)."""
    d = cq.Vector(*F["e_w"]) if w1 > w0 else cq.Vector(*F["e_w"]) * -1
    return cq.Workplane("XY").add(cq.Solid.makeCylinder(r * IN, abs(w1 - w0) * IN, _wpt(F, u, min(w0, w1) if w1 > w0 else max(w0, w1), s), d))


def _hex(pl, sgn, u, w, s0, length, af):
    """Hex nut / bolt head across-flats af, axis along s."""
    return cq.Workplane(pl).center(u * IN, sgn * w * IN).polygon(6, af / math.cos(math.pi / 6) * IN).extrude(length * IN).translate(
        pl.zDir.multiply(s0 * IN))


def module(G, axis, ratio="2:1", engaged=True):
    """World-frame solids of one drive module: dict name -> (solid, colour key)."""
    F = frames(G)[axis]
    pl, sgn = _plane(F)
    dw = 0.0 if engaged else -LIFT
    sA = F["sA"]
    sB = sA + PLATE_T + PLATE_GAP
    # rotate the arm about the pivot for the lift (small angle): w offset proportional to (U_PIVOT - u)
    def wof(u):
        return dw * (U_PIVOT - u) / U_PIVOT
    S = {}
    # arm plates (outline extruded along s); the lift is drawn as a w shift at the pinion (rotation about the pivot)
    p = arm_poly()
    for name, s0 in (("A", sA), ("B", sB)):
        flat = arm_flat(name, PLATE_T)
        solid = cq.Workplane(pl).add(flat.val().transformShape(pl.rG)).translate(pl.zDir.multiply(s0 * IN))
        if sgn < 0:
            solid = cq.Workplane(pl).add(flat.mirror("XZ").val().transformShape(pl.rG)).translate(pl.zDir.multiply(s0 * IN))
        if not engaged:
            ang = math.degrees(math.atan2(LIFT, U_PIVOT)) * sgn
            piv = cq.Vector(*[c * IN for c in F["O"]]) + cq.Vector(*F["e_u"]).multiply(U_PIVOT * IN)
            solid = solid.rotate(piv, piv + cq.Vector(*F["e_s"]), -ang)
        S[f"{axis}_arm_plate_{name}"] = (solid, "ALU")
    j = JACK_T[ratio]
    parts = {
        "pinion_20T": (_cyl(pl, sgn, 0, wof(0), -0.20, 0.40, OD(PINION_T) / 2), "ALU"),
        # hub no bigger than the teeth (0.24 r): with the roller track strip on the rim (R + 1/16, 2026-11-07) a stock
        # 16 mm hub would touch it. Use a hubless/long-toothed 20T pinion or turn the hub down to <= 12.5 mm
        "pinion_hub": (_cyl(pl, sgn, 0, wof(0), 0.20, 0.28, 0.24), "ALU"),
        "jackshaft_8mm": (_cyl(pl, sgn, 0, wof(0), -0.22, sB + PLATE_T + 0.1 + 0.22, SHAFT_D / 2), "ALU"),
        # F608ZZ flanged bearings: flange on the inner face of each plate
        "jack_bearing_A": (_cyl(pl, sgn, 0, wof(0), sA + PLATE_T, 0.06, 0.43), "ALU"),
        "jack_bearing_B": (_cyl(pl, sgn, 0, wof(0), sB - 0.06, 0.06, 0.43), "ALU"),
        f"pulley_{j}T": (_cyl(pl, sgn, 0, wof(0), sB - S_PULLEY_FROM_B, PULLEY_W, OD(j) / 2 + 0.03), "BLACK"),
        "pulley_16T": (_cyl(pl, sgn, C_NOM, wof(C_NOM), sB - S_PULLEY_FROM_B, PULLEY_W, 0.26), "BLACK"),
        # gearmotor: 1/4" output shaft through plate B to the 16T, square gearbox face on plate B, body behind it
        "motor_shaft": (_cyl(pl, sgn, C_NOM, wof(C_NOM), sB + PLATE_T - MOTOR_SHAFT_L, MOTOR_SHAFT_L, 0.1225), "ALU"),
        "motor_flange": (_box(pl, sgn, C_NOM, wof(C_NOM), sB + PLATE_T, FLANGE_SQ, FLANGE_SQ, FLANGE_T), "MOTOR"),
        "motor_GM9000": (_cyl(pl, sgn, C_NOM, wof(C_NOM), sB + PLATE_T + FLANGE_T, MOTOR_L - FLANGE_T, MOTOR_R), "MOTOR"),
        # pivot: 3/8 shoulder bolt with a turned spacer between the plates and a nyloc on the far end
        "pivot_spacer_AB": (_cyl(pl, sgn, U_PIVOT, 0, sA + PLATE_T, PLATE_GAP, 0.30), "ALU"),
    }
    for i, (mu, mw) in enumerate(MOTOR_HOLES):                                  # #6-32 screws through the flange and plate B
        parts[f"motor_screw_{i}"] = (_cyl(pl, sgn, C_NOM + mu, mw + wof(C_NOM), sB - 0.12, 0.12 + PLATE_T + FLANGE_T, 0.11), "BLACK")
    for (u, w) in STANDOFFS:
        parts[f"standoff_{u:+.2f}"] = (_cyl(pl, sgn, u, w + wof(u), sA + PLATE_T, PLATE_GAP, 0.19), "ALU")
    for k, v_ in parts.items():
        S[f"{axis}_{k}"] = v_
    # spring + guide rod + cam lever at the tail; base = the axis-specific bracket below
    tw = wof(U_TAIL)
    if axis == "alt":
        # base plate on the wall's outer face (s between the wall and plate A): it carries the pivot (u 4.0, w 0, where
        # the wall top is 0.5 above it) and a spring block under the tail; its top edge stays 0.14 under the jackshaft
        s_wall = G["wall_out"] - F["O"][0]
        outline = [(-1.1, -2.2), (4.8, -2.2), (4.8, 0.45), (3.0, 0.45), (3.0, -0.3), (-1.1, -0.3)]
        base = (cq.Workplane(pl).polyline([(u * IN, sgn * w * IN) for u, w in outline]).close().extrude(PLATE_T * IN)
                .translate(pl.zDir.multiply(s_wall * IN)))
        try:
            base = base.edges("|Z").fillet(0.2 * IN)
        except Exception:
            pass
        S["alt_base_plate"] = (base, "ALU")
        S["alt_pivot_spacer"] = (_cyl(pl, sgn, U_PIVOT, 0, s_wall + PLATE_T, sA - (s_wall + PLATE_T), PIVOT_SPACER_R), "ALU")
        S["alt_pivot_bolt"] = (_cyl(pl, sgn, U_PIVOT, 0, s_wall - 0.02, sB + PLATE_T + NUT_T - s_wall + 0.02, 0.1875), "BLACK")
        S["alt_pivot_nut"] = (_hex(pl, sgn, U_PIVOT, 0, sB + PLATE_T, NUT_T, NUT_AF), "BLACK")
        # tail: a block between the plates that the spring pushes and the rod passes through
        s_blk = sB + PLATE_T - (s_wall + PLATE_T)
        S["alt_spring_block"] = (_box(pl, sgn, U_TAIL, -1.85, s_wall + PLATE_T, 0.9, 0.5, s_blk), "ALU")
        S["alt_tail_block"] = (_box(pl, sgn, U_TAIL, tw, sA + PLATE_T, 0.6, 0.6, PLATE_GAP), "ALU")
        sm = (sA + sB + PLATE_T) / 2
        S["alt_spring"] = (_cyl_w(F, U_TAIL, -1.6, -0.3 + tw, sm, SPRING_R)
                           .cut(_cyl_w(F, U_TAIL, -1.65, -0.25 + tw, sm, SPRING_R - SPRING_WIRE)), "BLACK")
        S["alt_guide_rod"] = (_cyl_w(F, U_TAIL, -2.1, 1.05 + tw, sm, ROD_R), "ALU")
        S["alt_cam_lever"] = (_box(pl, sgn, U_TAIL + 0.6, 0.5 + tw, sm - 0.25, 1.8, 0.4, 0.5), "BLACK")
    else:
        # bracket: a 1/4" strip from the pivot (above plate B) back to an angle on the drive wall's outer face;
        # an extension spring from a post on the wall pulls the tail toward the ring (+w); the cam pushes it out
        sb = sB + PLATE_T + 0.35
        Ox, Oy = F["O"][0], F["O"][1]
        eu, ew = F["e_u"], F["e_w"]
        def loc(xw, yw):
            dx, dy = xw - Ox, yw - Oy
            return dx * eu[0] + dy * eu[1], dx * ew[0] + dy * ew[1]
        piv_w = (Ox + U_PIVOT * eu[0], Oy + U_PIVOT * eu[1])
        wu, ww = loc(G["wall_out"] + PLATE_T, piv_w[1])
        S["az_base_bracket"] = (_strip(pl, sgn, (U_PIVOT, 0.0), (wu, ww), 0.9, sb, PLATE_T), "ALU")
        S["az_pivot_spacer"] = (_cyl(pl, sgn, U_PIVOT, 0, sB + PLATE_T, sb - (sB + PLATE_T), PIVOT_SPACER_R), "ALU")
        S["az_pivot_bolt"] = (_cyl(pl, sgn, U_PIVOT, 0, sA - 0.30, sb + PLATE_T + NUT_T - sA + 0.30, 0.1875), "BLACK")
        S["az_pivot_head"] = (_hex(pl, sgn, U_PIVOT, 0, sA - 0.30, 0.30, NUT_AF), "BLACK")
        S["az_pivot_nut"] = (_hex(pl, sgn, U_PIVOT, 0, sb + PLATE_T, NUT_T, NUT_AF), "BLACK")
        zb = F["O"][2] + sb
        S["az_bracket_leg"] = (cq.Workplane("XY").box(PLATE_T * IN, 1.0 * IN, 1.6 * IN).translate(
            cq.Vector((G["wall_out"] + PLATE_T / 2) * IN, piv_w[1] * IN, (zb + 0.8) * IN)), "ALU")
        tu, twl = loc(G["wall_out"], Oy + U_TAIL * eu[1])
        sm = sA + PLATE_T + PLATE_GAP / 2
        S["az_spring_post"] = (_box(pl, sgn, U_TAIL, twl - 0.1, sm - 0.5, 0.6, 0.5, 1.0), "ALU")   # 0.15 into the wall face: screwed to it
        S["az_spring"] = (_strip(pl, sgn, (U_TAIL, R_LOBE["tail"] + 0.05 + tw), (U_TAIL, twl - 0.3), 0.35, sm - 0.17, 0.34), "BLACK")
        S["az_cam_lever"] = (_box(pl, sgn, U_TAIL + 0.55, (R_LOBE["tail"] + twl) / 2, sB + PLATE_T, 0.3, 0.6, 0.35), "BLACK")
    return S


def wall_holes(G):
    """1/4" bolt holes the drive brackets need in the drive wall, as (y, z_world)."""
    F = frames(G)
    cz = F["alt"]["O"][2]
    hol = [(u, cz + w) for u in (-0.75, 3.45) for w in (-0.75, -1.85)]          # alt base plate
    az = F["az"]
    sB = az["sA"] + PLATE_T + PLATE_GAP
    zb = az["O"][2] + sB + PLATE_T + 0.35
    py = az["O"][1] + U_PIVOT * az["e_u"][1]
    hol += [(py, zb + 0.55), (py, zb + 1.3)]                                     # az bracket leg (rises from the strip)
    return hol


def flats():
    """2D flats for the DXFs: the arm plates (same for both axes: 2 x A, 2 x B)."""
    return {"drive_arm_plate_A": dict(solid=arm_flat("A"), qty=2, size=_size()),
            "drive_arm_plate_B": dict(solid=arm_flat("B"), qty=2, size=_size())}


def _size():
    x0, y0, x1, y1 = arm_poly().bounds
    return (round(x1 - x0, 2), round(y1 - y0, 2))


if __name__ == "__main__":
    import json
    print(json.dumps(numbers(), indent=1), "arm plates (pair) lb", arm_lb(), "size", _size())
