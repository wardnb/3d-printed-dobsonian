"""
Truss joint detail: cone-ended pole plugs, socket blocks on the mirror-box stubs, bonded pair blocks
under the cage's lower ring. Reads out/params.json (run dob_model.py first).

Outputs (out/truss_joints/):
  joints_full.glb      all three pairs, six sockets, with ring and stub context
  socket_detail.glb    one socket block with its two pole ends and knobs
  socket_section.glb   the same, cut on the vertical tangential plane through the node
  pair_detail.glb      one pair block under the cage ring
  *.step               the machined parts, millimetres
"""
import json, math, os
import cadquery as cq

IN = 25.4
P = json.load(open("out/params.json"))
F, PR = P["frame"], P["params"]

# --- geometry from the model -------------------------------------------------------------
R_TOP = PR["truss_top_radius"]                                         # 9.6
STUB_XZ = {int(k): tuple(v) for k, v in F["stub_xz"].items()}            # stub positions from the STEP pilots


def base_xz(deg):
    d = deg % 360
    for a, xz in STUB_XZ.items():
        if abs((d - a + 180) % 360 - 180) < 1:
            return xz
    raise KeyError(deg)
TOPS = [30, 150, 270]
Y_RING_LO = F["y_ring_lo"]                     # cage lower ring, mirror-side face
Y_STUB_TOP = F["y_mcage_top"] + PR["stub_proud"]
Y_NODE = Y_STUB_TOP + PR.get("socket_node_above_stub", 0.6)   # cone apex (FE node) height
NODE_OFF = 0.8                                 # the two cups at a socket sit +/-0.8" tangentially
POLE_OD, POLE_WALL = PR["truss_pole_od"], 0.0575  # Rock West 45562: 1.125 ID x 1.24 OD (ordered 2026-11-03); measure before cutting plugs
BORE = POLE_OD - 2 * POLE_WALL
STUB_OD, STUB_WALL = PR["mcage_tube_od"], PR["mcage_tube_wall"]   # 45 x 2.5 mm DobStuff strut (measured)
HALF = math.radians(30)                        # 60 deg included cone
NOSE_D = 0.40
S_NOSE = (NOSE_D / 2) / math.tan(HALF)         # apex -> nose along the pole axis
S_SHOULDER = (POLE_OD / 2) / math.tan(HALF)    # apex -> full diameter
SHOULDER_L, SHANK_L = 0.40, 1.75
BLOCK_T, BLOCK_R, BLOCK_H = 3.6, 2.0, 2.1      # socket block: tangential x radial x tall (2.1: room for the wheel pocket)
# GIB CLAMP (2026-11-08) replaces the drawbolt + thumbwheel of 2026-10-31: that wheel sat 1.0" inside the block behind a
# 1.0 x 0.75 pocket mouth and could not be reached, let alone turned to 100 lb. Now: a 1/4-20 x 1 SHCS screwed into the
# plug's nose (head down, a 1/4" spherical washer set riding on the head) hangs through a 0.70 hole at the cup apex. A 5/8" steel gib pin slides in a horizontal bore
# drilled in from the block's OUTSIDE face, just above the apex; its forked tip straddles the screw shank and its underside
# is milled to an 8 deg wedge that bears on the washer on the screw head, pulling the cone into the cup. A 1/4-20 knob stud
# threaded through a 1/8" steel plate (PEM nut) on the outside face pushes the gib in; the stud tip is captive in the gib
# so backing the knob off withdraws it. 5 in-lb on a 1.25" knob -> ~100 lb push -> ~200-300 lb pull (wedge 8 deg,
# mu 0.1-0.15, self-locking). Poles carry up to ~27 lb TENSION near the horizon (truss_fe), so friction-only side knobs
# were never enough; this keeps the cone preloaded with the knob where a hand can reach it.
HEAD_D, HEAD_H, HEAD_SHANK = 0.375, 0.25, 0.50      # 1/4-20 x 1 SHCS (0.5 in the nose): head dia/height, exposed shank below the nose face
WASHER_D, WASHER_T = 0.625, 0.19                    # 1/4" SPHERICAL washer set on the head (the screw leans 13 deg, the gib is horizontal:
                                                    # a flat washer would load one tine only); the gib's tines bear on its flat seat, 0.14 each side
APEX_HOLE_D = 0.70                                  # through the cup apex; head + washer pass down it (cone contact then r 0.35-0.62)
GIB_D, GIB_L, GIB_SLOT, GIB_ANGLE_DEG = 0.625, 1.20, 0.34, 8.0   # slot clears the 0.25 shank leaning 13 deg; tines 0.14 thick
GIB_Z = 0.0                                         # gib bore axis at the apex level (bore spans +/-0.3125; washer top at -0.094)
GIB_TIP_ENGAGED = 1.15                              # tip depth from the outside face when tight (shank at BLOCK_R/2 = 1.0)
GIB_BORE_DEPTH = 1.25                               # from the outside face; 0.75 wall left to the inside face
GIB_TRAVEL = 0.35                                   # released tip at 0.80 (0.2 behind the head) -> ~7 turns of 1/4-20
PLATE_T, PLATE_W, PLATE_H = 0.125, 1.6, 1.2         # steel retainer plate on the outside face, 1/4-20 PEM nut, 2 x #8-32 at +/-0.55
KNOB_D, KNOB_T = 1.25, 0.45
# Spigot = a separate turned 6061 part (2026-10-31: integral it made the socket stock 3.6" tall, too tall for the AltMill's
# Z on the wedge fixtures). Short Ø0.50 x 0.11 pilot into a matching register in the block's underside, bonded, and a
# 1/4-20 x 1-3/4 SHCS up from the spigot's bottom (counterbored) into the block (tapped 0.60 deep on the centreline).
# The block's underside bears on the stub's end face; the spigot only locates it and takes side/uplift loads.
SPIGOT_L = 1.5
SPIGOT_PILOT_D, SPIGOT_PILOT_H = 0.50, 0.11       # register depth 0.12 (pocket floor is 0.15 above the underside)
SPIGOT_CB_D, SPIGOT_CB_H = 0.39, 0.26              # SHCS head counterbore in the spigot's bottom
SPIGOT_TAP_DEPTH, SPIGOT_DRILL_DEPTH = 0.60, 0.70  # 1/4-20 in the block (#7 drill 0.201)
# pair end (2026-10-31 detailing): the carbon tube runs 0.30" PAST the pair node into a blind bonded bore, so ~1.33" of
# tube is bonded (it was 0.43": the tube stopped 0.6" short of the node); the bore floor locates the tube length
TUBE_PAST_APEX = 0.05                          # was 0.30: trimmed 2026-11-03 so two poles come out of one 72" tube
COLLAR_OD, COLLAR_W = 2.75, 0.55               # 45 mm two-piece shaft clamp collars, one each side of the box's top ring
# board pin (2026-10-31): the stubs end flush with the mirror board's underside and a collar on top of the board would
# hit the bearing wings, so each stub is also pinned at the mirror board by a 1/4" steel dowel drilled radially in from
# the board's edge through both stub walls (double shear). mcage_fe: stubs held at both boards 0.023 mm vs 0.059 at the
# top ring only. Board edge along the stub's ray: the point tip (12.125") at 90, the back corners (~12.5") at 210/330.
PIN_D = 0.25
PIN_EDGE_R = {90: 12.125, 210: 12.5, 330: 12.5}
PAIR_T, PAIR_R, PAIR_H = 3.6, 1.6, 1.6         # pair block under the ring
PAIR_STUD_R = -0.45                            # knob stud 0.45 inboard of the block centre: on the centre it broke into both bores
PAIR_DOWEL_R = 0.35                            # one 1/4 dowel 0.35 outboard (t = 0), 0.5 deep; dowels at +/-1.35 t hit the bores' high rims
PAIR_DOWEL = 0.0                               # (tangential position of the dowel)


def v(*a):
    return cq.Vector(*[x * IN for x in a])


def polar(r, deg):
    a = math.radians(deg)
    return r * math.cos(a), r * math.sin(a)


def rad_tan(deg):
    a = math.radians(deg)
    return (math.cos(a), 0, math.sin(a)), (-math.sin(a), 0, math.cos(a))


def cyl(r, length, p0, d):
    d = cq.Vector(*d).normalized()
    return cq.Workplane("XY").add(cq.Solid.makeCylinder(r * IN, length * IN, v(*p0), d))


def cone(r0, r1, length, p0, d):
    d = cq.Vector(*d).normalized()
    return cq.Workplane("XY").add(cq.Solid.makeCone(r0 * IN, r1 * IN, length * IN, v(*p0), d))


TOP_ROUND = 0.25          # socket block: the whole top perimeter is rounded (crowned), 2026-11-08; cup-rim wall 0.365 at the top


def block(center, deg, t, h, r, fillet=0.2, top_round=0.0):
    """Box centred at `center`, t along the tangent, h vertical, r along the radius at angle deg.
    fillet = vertical corner radius; top_round = radius on the whole top perimeter (else a 0.06 chamfer)."""
    rd, td = rad_tan(deg)
    pl = cq.Plane(origin=v(*center), xDir=cq.Vector(*td), normal=cq.Vector(*rd))
    w = cq.Workplane(pl).box(t * IN, h * IN, r * IN)
    if fillet:
        w = w.edges("|Y").fillet(fillet * IN)
        try:                                                   # looks: crown or 0.06 chamfer on top, 0.06 chamfer below
            if top_round:
                w = w.faces(">Y").fillet(top_round * IN).faces("<Y").chamfer(0.06 * IN)
            else:
                w = w.faces(">Y or <Y").chamfer(0.06 * IN)
        except Exception:
            pass
    return w


def along(p, d, s):
    d = cq.Vector(*d).normalized()
    return (p[0] + d.x * s, p[1] + d.y * s, p[2] + d.z * s)


def ring_sector(y0, thick, rin, rout, deg, half_span):
    w = (cq.Workplane("XZ").circle(rout * IN).circle(rin * IN).extrude(-thick * IN).translate(v(0, y0, 0)))
    a0, a1 = math.radians(deg - half_span), math.radians(deg + half_span)
    big = 40 * IN
    wedge = (cq.Workplane("XZ").moveTo(0, 0).lineTo(big * math.cos(a0), big * math.sin(a0))
             .lineTo(big * math.cos(deg * math.pi / 180), big * math.sin(deg * math.pi / 180))
             .lineTo(big * math.cos(a1), big * math.sin(a1)).close()
             .extrude(-(thick + 2) * IN).translate(v(0, y0 - 1, 0)))
    return w.intersect(wedge)


# --- node layout ---------------------------------------------------------------------------
# apex i (angle t) sends poles to bases at t-60 and t+60. At a base b the pole from apex b+60
# attaches at tangential offset +NODE_OFF, the pole from apex b-60 at -NODE_OFF (and the apex
# ends mirror that so each pole stays parallel to the ideal line).
def node_points(t, side):
    """side = -1: pole to base t-60; +1: pole to base t+60. Returns (apex_pt, base_pt)."""
    b = (t + 60 * side) % 360
    ax, az = polar(R_TOP, t); bx, bz = base_xz(b)
    _, tt = rad_tan(t); _, tb = rad_tan(b)
    # at the apex the pole toward +60 sits on the +tangent side, toward -60 on the -tangent side;
    # at the base the pole that came from the +60 apex (i.e. this base's "-side" neighbour) sits on -tangent
    A = (ax + tt[0] * NODE_OFF * side, Y_RING_LO - 0.6, az + tt[2] * NODE_OFF * side)
    B = (bx - tb[0] * NODE_OFF * side, Y_NODE, bz - tb[2] * NODE_OFF * side)
    return A, B


ALU = cq.Color(0.76, 0.78, 0.80)
CARBON = cq.Color(0.10, 0.10, 0.11)
BRASS = cq.Color(0.80, 0.62, 0.25)
KNOB = cq.Color(0.15, 0.15, 0.16)
BIRCH = cq.Color(0.86, 0.72, 0.50)
STUB = cq.Color(0.62, 0.63, 0.66)
CUTFACE = cq.Color(0.95, 0.45, 0.20)


def pole_parts(A, B, full_pole=True):
    """Carbon tube + two bonded plugs along the line A (apex) -> B (base). Base end is the cone."""
    d_up = cq.Vector(*[a - b for a, b in zip(A, B)]).normalized()      # base -> apex
    d_dn = d_up * -1
    L = math.dist(A, B)
    # cone plug at the base: nose at S_NOSE from the apex point B, growing toward the pole
    plug = cone(NOSE_D / 2, POLE_OD / 2, S_SHOULDER - S_NOSE, along(B, d_up, S_NOSE), d_up)
    plug = plug.union(cyl(POLE_OD / 2, SHOULDER_L, along(B, d_up, S_SHOULDER), d_up))
    plug = plug.union(cyl(BORE / 2 - 0.003, SHANK_L, along(B, d_up, S_SHOULDER + SHOULDER_L), d_up))
    tube_start = S_SHOULDER + SHOULDER_L
    tube_len = (L + TUBE_PAST_APEX - tube_start) if full_pole else 4.0
    tube = cyl(POLE_OD / 2, tube_len, along(B, d_up, tube_start), d_up)
    tube = tube.cut(cyl(BORE / 2, tube_len, along(B, d_up, tube_start), d_up))
    return plug, tube, d_up


def socket_block(b):
    """Block bonded into the stub at base angle b with two cups. Returns dict of solids."""
    bx, bz = base_xz(b)
    rd, td = rad_tan(b)
    centre = (bx, Y_STUB_TOP + BLOCK_H / 2, bz)
    blk = block(centre, b, BLOCK_T, BLOCK_H, BLOCK_R, top_round=TOP_ROUND)
    spigot = cyl(STUB_OD / 2 - STUB_WALL - 0.003, SPIGOT_L, (bx, Y_STUB_TOP, bz), (0, -1, 0))
    spigot = spigot.union(cyl(SPIGOT_PILOT_D / 2, SPIGOT_PILOT_H, (bx, Y_STUB_TOP, bz), (0, 1, 0)))
    spigot = spigot.cut(cyl(0.133, SPIGOT_L + 0.2, (bx, Y_STUB_TOP + 0.15, bz), (0, -1, 0)))
    spigot = spigot.cut(cyl(SPIGOT_CB_D / 2, SPIGOT_CB_H, (bx, Y_STUB_TOP - SPIGOT_L, bz), (0, 1, 0)))
    blk = blk.cut(cyl(SPIGOT_PILOT_D / 2 + 0.002, SPIGOT_PILOT_H + 0.01, (bx, Y_STUB_TOP, bz), (0, 1, 0)))   # register
    blk = blk.cut(cyl(0.1005, SPIGOT_DRILL_DEPTH, (bx, Y_STUB_TOP, bz), (0, 1, 0)))                       # tap drill
    sbolt = cyl(0.125, 1.75, (bx, Y_STUB_TOP - SPIGOT_L + SPIGOT_CB_H, bz), (0, 1, 0))
    sbolt = sbolt.union(cyl(0.1875, 0.25, (bx, Y_STUB_TOP - SPIGOT_L + 0.01, bz), (0, 1, 0)))
    knobs, screws = None, None
    for side in (-1, +1):
        t = (b - 60 * side) % 360                       # the apex this cup's pole comes from
        A, B = node_points(t, side)
        d_up = cq.Vector(*[a - c for a, c in zip(A, B)]).normalized()
        d_dn = d_up * -1
        cup = cone(0.02, 3.0 * math.tan(HALF), 3.0 - 0.02 / math.tan(HALF), along(B, d_up, 0.02 / math.tan(HALF)), d_up)
        blk = blk.cut(cup)
        # apex hole for the head screw: from the plug's nose level down past the head
        blk = blk.cut(cyl(APEX_HOLE_D / 2, S_NOSE + 0.02 + 0.50, along(B, d_up, S_NOSE + 0.02), d_dn))   # to apex - 0.50, as the G-code cuts
        # gib bore: horizontal, radial, in from the outside face, axis GIB_Z above the apex, under this cup
        p_ax = (B[0], B[1] + GIB_Z, B[2])
        # B sits on the stub's radial line +/- NODE_OFF tangentially, so the face point is B moved out radially
        p_face = (B[0] + rd[0] * BLOCK_R / 2, p_ax[1], B[2] + rd[2] * BLOCK_R / 2)
        blk = blk.cut(cyl(GIB_D / 2, GIB_BORE_DEPTH + 0.2, along(p_face, rd, 0.2), (-rd[0], 0, -rd[2])))
        for dt in (-0.55, 0.55):                       # #8-32 tap drill for the retainer plate
            q = (p_face[0] + td[0] * dt, p_face[1], p_face[2] + td[2] * dt)
            blk = blk.cut(cyl(0.068, 0.40, along(q, rd, 0.01), (-rd[0], 0, -rd[2])))
        # solids: gib (engaged), retainer plate, knob + stud, head screw on the plug
        gib = cyl(GIB_D / 2, GIB_TIP_ENGAGED, p_face, (-rd[0], 0, -rd[2]))
        tip = along(p_face, (-rd[0], 0, -rd[2]), GIB_TIP_ENGAGED)
        slot = block((tip[0] + rd[0] * 0.3, tip[1], tip[2] + rd[2] * 0.3), b, GIB_SLOT, GIB_D + 0.1, 0.6, fillet=0)
        gib = gib.cut(slot)
        # wedge underside: drawn flat at the head-top level (the real face rises 8 deg toward the tip)
        y_head_top = B[1] - (HEAD_SHANK - WASHER_T - S_NOSE) * abs(d_dn.y)    # washer top
        gib = gib.cut(cq.Workplane("XY").box(6 * IN, 2 * IN, 6 * IN).translate(v(B[0], y_head_top - 1.0, B[2])))
        plate = block((p_face[0] + rd[0] * PLATE_T / 2, p_face[1], p_face[2] + rd[2] * PLATE_T / 2), b, PLATE_W, PLATE_H, PLATE_T, fillet=0)
        knob = cyl(KNOB_D / 2, KNOB_T, along(p_face, rd, PLATE_T + 0.05), rd)
        stud = cyl(0.125, PLATE_T + 0.05 + KNOB_T + 0.3, along(p_face, (-rd[0], 0, -rd[2]), 0.3), rd)
        hw = gib.union(plate).union(knob).union(stud)
        knobs = hw if knobs is None else knobs.union(hw)
        screw = cyl(0.125, HEAD_SHANK, along(B, d_up, S_NOSE), d_dn)
        screw = screw.union(cyl(HEAD_D / 2, HEAD_H, along(B, d_dn, HEAD_SHANK - S_NOSE), d_dn))
        screw = screw.union(cyl(WASHER_D / 2, WASHER_T, along(B, d_dn, HEAD_SHANK - S_NOSE - WASHER_T), d_dn))
        screws = screw if screws is None else screws.union(screw)
    return dict(block=blk, knobs=knobs, pads=screws, spigot=spigot, spigot_bolt=sbolt)

def pair_block(t):
    ax, az = polar(R_TOP, t)
    rd, td = rad_tan(t)
    centre = (ax, Y_RING_LO - PAIR_H / 2, az)
    blk = block(centre, t, PAIR_T, PAIR_H, PAIR_R)
    for side in (-1, +1):
        A, B = node_points(t, side)
        d_dn = cq.Vector(*[c - a for a, c in zip(A, B)]).normalized()
        blk = blk.cut(cyl(POLE_OD / 2 + 0.002, 3.0, along(A, d_dn, -TUBE_PAST_APEX), d_dn))   # blind bonded bore (floor = tube end)
        fl = along(A, d_dn, -TUBE_PAST_APEX)
        blk = blk.cut(cyl(0.125, 2.0, (fl[0], fl[1] - 0.05, fl[2]), (0, 1, 0)))              # 1/4" vertical vent from the floor up through the top
    # stud + knob under the block, two dowels into the ring
    sx, sz = ax + rd[0] * PAIR_STUD_R, az + rd[2] * PAIR_STUD_R
    blk = blk.cut(cyl(0.14, PAIR_H + 1, (sx, Y_RING_LO + 0.5, sz), (0, -1, 0)))
    knob = cyl(0.125, PAIR_H + 0.9, (sx, Y_RING_LO + 0.3, sz), (0, -1, 0)).union(
        cyl(0.45, 0.5, (sx, Y_RING_LO - PAIR_H - 0.05, sz), (0, -1, 0)))
    p = (ax + rd[0] * PAIR_DOWEL_R, Y_RING_LO - 0.5, az + rd[2] * PAIR_DOWEL_R)
    blk = blk.cut(cyl(0.125, 0.5, p, (0, 1, 0)))
    dowels = cyl(0.125, 0.75, p, (0, 1, 0))
    return dict(block=blk, knob=knob, dowels=dowels)


def pole_tube_cut_at_pair(tube, t):
    return tube


def stub_and_ring(b):
    bx, bz = base_xz(b)
    stub = cyl(STUB_OD / 2, Y_STUB_TOP - (F["y_mcage_top"] - 2.5), (bx, F["y_mcage_top"] - 2.5, bz), (0, 1, 0))
    stub = stub.cut(cyl(STUB_OD / 2 - STUB_WALL, 10, (bx, F["y_mcage_top"] - 3, bz), (0, 1, 0)))
    ring = ring_sector(F["y_mcage_top"] - PR["ply"], PR["ply"], PR["mcage_ring_id"] / 2, PR["mcage_ring_od"] / 2, b, 22)
    ring = ring.cut(cyl(STUB_OD / 2 + 0.01, 3, (bx, F["y_mcage_top"] - 2, bz), (0, 1, 0)))
    collars = None
    for y0 in (F["y_mcage_top"], F["y_mcage_top"] - PR["ply"] - COLLAR_W):   # above and below the box's top ring
        c = cyl(COLLAR_OD / 2, COLLAR_W, (bx, y0, bz), (0, 1, 0)).cut(cyl(STUB_OD / 2, COLLAR_W, (bx, y0, bz), (0, 1, 0)))
        collars = c if collars is None else collars.union(c)
    return stub, ring.union(collars) if False else ring, collars


def board_pin(b):
    """1/4" dowel pin, radial, through the mirror board's edge at mid-thickness and both walls of the stub."""
    bx, bz = base_xz(b)
    rc = math.hypot(bx, bz)
    ux, uz = bx / rc, bz / rc
    r0 = rc - STUB_OD / 2 - 0.10                 # just past the far wall
    r1 = PIN_EDGE_R[b] - 0.06                    # flush, slightly countersunk
    y = F["y_mcage_bot"] + PR["ply"] / 2
    return cyl(PIN_D / 2, r1 - r0, (ux * r0, y, uz * r0), (ux, 0, uz)), round(r1 - r0, 2)


def cage_ring_sector(t):
    return ring_sector(Y_RING_LO, PR["ring_thick"], PR["ring_id"] / 2, PR["ring_od"] / 2, t, 22)


def build_full():
    a = cq.Assembly(name="truss_joints")
    for t in TOPS:
        pb = pair_block(t)
        a.add(pb["block"], name=f"pair_block_{t}", color=ALU)
        a.add(pb["knob"], name=f"pair_knob_{t}", color=KNOB)
        a.add(pb["dowels"], name=f"pair_dowels_{t}", color=BRASS)
        a.add(cage_ring_sector(t), name=f"cage_ring_{t}", color=ALU)
        for side in (-1, 1):
            A, B = node_points(t, side)
            plug, tube, _ = pole_parts(A, B)
            a.add(plug, name=f"plug_{t}_{side}", color=ALU)
            a.add(tube, name=f"pole_{t}_{side}", color=CARBON)
    for b in (90, 210, 330):
        sb = socket_block(b)
        a.add(sb["block"], name=f"socket_{b}", color=ALU)
        a.add(sb["spigot"], name=f"spigot_{b}", color=ALU)
        a.add(sb["knobs"], name=f"gib_clamps_{b}", color=KNOB)
        a.add(sb["pads"], name=f"head_screws_{b}", color=BRASS)
        stub, ring, collars = stub_and_ring(b)
        a.add(stub, name=f"stub_{b}", color=STUB)
        a.add(ring, name=f"box_ring_{b}", color=BIRCH)
        a.add(collars, name=f"stub_collars_{b}", color=KNOB)
        a.add(board_pin(b)[0], name=f"board_pin_{b}", color=BRASS)
    return a


def build_viewer():
    """The chosen truss as the main 3D viewer shows it: poles, plugs, pair blocks with knobs and dowels, socket
    blocks with head screws and gib clamps, stub collars (the stubs and rings come from dob_model)."""
    a = cq.Assembly(name="truss_zigzag")
    poles = plugs = pblk = pk = dw = None
    U = lambda acc, s: s if acc is None else acc.union(s)
    for t in TOPS:
        pb = pair_block(t)
        pblk, pk, dw = U(pblk, pb["block"]), U(pk, pb["knob"]), U(dw, pb["dowels"])
        for side in (-1, 1):
            A, B = node_points(t, side)
            plug, tube, _ = pole_parts(A, B)
            plugs, poles = U(plugs, plug), U(poles, tube)
    sb_ = wh = st = col = None
    for b in (90, 210, 330):
        sb = socket_block(b)
        sb_, wh, st = U(U(sb_, sb["block"]), sb["spigot"]), U(wh, sb["knobs"]), U(st, sb["pads"])
        col = U(col, stub_and_ring(b)[2])
        st = U(st, board_pin(b)[0])
    for name, part, color in (("truss_poles", poles, CARBON), ("pole_plugs", plugs, ALU), ("pair_blocks", pblk, ALU),
                              ("pair_knobs", pk, KNOB), ("pair_dowels", dw, BRASS), ("socket_blocks", sb_, ALU),
                              ("gib_clamps", wh, KNOB), ("head_screws_and_board_pins", st, BRASS), ("stub_collars", col, KNOB)):
        a.add(part, name=name, color=color)
    return a


def build_socket_detail(b=90, section=False):
    a = cq.Assembly(name="socket_detail" + ("_section" if section else ""))
    bx, bz = base_xz(b)
    rd, td = rad_tan(b)
    half = None
    if section:
        pl = cq.Plane(origin=v(bx, Y_NODE, bz), xDir=cq.Vector(*td), normal=cq.Vector(*rd))
        half = cq.Workplane(pl).rect(60 * IN, 60 * IN).extrude(30 * IN)      # radial-outside half

    def add(solid, name, color):
        if half is not None:
            solid = solid.cut(half)
        a.add(solid, name=name, color=color)

    sb = socket_block(b)
    add(sb["block"], "socket_block", ALU)
    add(sb["spigot"], "spigot", ALU)
    add(sb["spigot_bolt"], "spigot_bolt", BRASS)
    add(sb["knobs"], "gib_clamps", KNOB)
    add(sb["pads"], "head_screws", BRASS)
    stub, ring, collars = stub_and_ring(b)
    add(stub, "stub", STUB)
    add(ring, "box_ring", BIRCH)
    add(collars, "stub_collars", KNOB)
    for side in (-1, 1):
        t = (b - 60 * side) % 360
        A, B = node_points(t, side)
        plug, tube, _ = pole_parts(A, B, full_pole=False)
        add(plug, f"plug_{side}", ALU)
        add(tube, f"pole_{side}", CARBON)
    return a


def build_pair_detail(t=30):
    a = cq.Assembly(name="pair_detail")
    pb = pair_block(t)
    a.add(pb["block"], name="pair_block", color=ALU)
    a.add(pb["knob"], name="knob", color=KNOB)
    a.add(pb["dowels"], name="dowels", color=BRASS)
    a.add(cage_ring_sector(t), name="cage_ring", color=ALU)
    for side in (-1, 1):
        A, B = node_points(t, side)
        d_dn = cq.Vector(*[c - x for x, c in zip(A, B)]).normalized()
        tube = cyl(POLE_OD / 2, 6.0, along(A, d_dn, -TUBE_PAST_APEX), d_dn)
        tube = tube.cut(cyl(BORE / 2, 6.0, along(A, d_dn, -TUBE_PAST_APEX), d_dn))
        a.add(tube, name=f"pole_{side}", color=CARBON)
    return a


if __name__ == "__main__":
    out = "out/truss_joints"
    os.makedirs(out, exist_ok=True)
    full = build_full(); full.save(f"{out}/joints_full.glb")
    sd = build_socket_detail(); sd.save(f"{out}/socket_detail.glb")
    ss = build_socket_detail(section=True); ss.save(f"{out}/socket_section.glb")
    pd = build_pair_detail(); pd.save(f"{out}/pair_detail.glb")
    _sb = socket_block(90)
    _sb["block"].val().exportStep(f"{out}/socket_block_90.step")
    _sb["spigot"].val().exportStep(f"{out}/socket_spigot.step")
    pair_block(30)["block"].val().exportStep(f"{out}/pair_block_30.step")
    A, B = node_points(30, 1)
    pole_parts(A, B)[0].val().exportStep(f"{out}/pole_plug.step")
    L = math.dist(*node_points(30, 1))
    lens = {f'{t}->{(t + 60 * s) % 360}': round(math.dist(*node_points(t, s)), 3) for t in TOPS for s in (-1, 1)}
    print(json.dumps(dict(pole_node_to_node_in=round(L, 2), pole_lengths_in=lens, tube_len_in=round(L + TUBE_PAST_APEX - S_SHOULDER - SHOULDER_L, 2),
                          plug_nose_to_shoulder_in=round(S_SHOULDER - S_NOSE, 3), shank_od_in=round(BORE - 0.006, 3),
                          cup_depth_in=round(S_SHOULDER, 3), node_offset_in=NODE_OFF,
                          spigot_od_in=round(STUB_OD - 2 * STUB_WALL - 0.006, 3), stub_od_in=STUB_OD,
                          board_pin_len_in={b: board_pin(b)[1] for b in (90, 210, 330)}), indent=1))
