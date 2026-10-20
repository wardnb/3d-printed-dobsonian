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
Y_NODE = Y_STUB_TOP + 0.6                      # cone apex (FE node) height
NODE_OFF = 0.8                                 # the two cups at a socket sit +/-0.8" tangentially
POLE_OD, POLE_WALL = PR["truss_pole_od"], 0.062   # 1.25 x 0.062 carbon
BORE = POLE_OD - 2 * POLE_WALL
STUB_OD, STUB_WALL = PR["mcage_tube_od"], PR["mcage_tube_wall"]   # 45 x 2.5 mm DobStuff strut (measured)
HALF = math.radians(30)                        # 60 deg included cone
NOSE_D = 0.40
S_NOSE = (NOSE_D / 2) / math.tan(HALF)         # apex -> nose along the pole axis
S_SHOULDER = (POLE_OD / 2) / math.tan(HALF)    # apex -> full diameter
SHOULDER_L, SHANK_L = 0.40, 1.75
BLOCK_T, BLOCK_R, BLOCK_H = 3.6, 2.0, 1.7      # socket block: tangential x radial x tall
PAIR_T, PAIR_R, PAIR_H = 3.6, 1.6, 1.6         # pair block under the ring


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


def block(center, deg, t, h, r):
    """Box centred at `center`, t along the tangent, h vertical, r along the radius at angle deg."""
    rd, td = rad_tan(deg)
    pl = cq.Plane(origin=v(*center), xDir=cq.Vector(*td), normal=cq.Vector(*rd))
    return cq.Workplane(pl).box(t * IN, h * IN, r * IN).edges("|Y").fillet(0.2 * IN)


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
    tube_len = (L - 0.6 - tube_start) if full_pole else 4.0
    tube = cyl(POLE_OD / 2, tube_len, along(B, d_up, tube_start), d_up)
    tube = tube.cut(cyl(BORE / 2, tube_len, along(B, d_up, tube_start), d_up))
    return plug, tube, d_up


def socket_block(b):
    """Block bonded into the stub at base angle b with two cups. Returns dict of solids."""
    bx, bz = base_xz(b)
    rd, td = rad_tan(b)
    centre = (bx, Y_STUB_TOP + BLOCK_H / 2, bz)
    blk = block(centre, b, BLOCK_T, BLOCK_H, BLOCK_R)
    spigot = cyl(STUB_OD / 2 - STUB_WALL - 0.003, 1.5, (bx, Y_STUB_TOP, bz), (0, -1, 0))
    blk = blk.union(spigot)
    knobs, pads = None, None
    for side in (-1, +1):
        t = (b - 60 * side) % 360                       # the apex this cup's pole comes from
        A, B = node_points(t, side)
        d_up = cq.Vector(*[a - c for a, c in zip(A, B)]).normalized()
        cup = cone(0.0, 3.0 * math.tan(HALF), 3.0, B, d_up)
        blk = blk.cut(cup)
        # knob: 1/4-20 from the radial-outside face, aimed at the plug flank at mid-cone height
        hit = along(B, d_up, (S_NOSE + S_SHOULDER) / 2)
        outer = (hit[0] + rd[0] * (BLOCK_R / 2 + 0.6), hit[1], hit[2] + rd[2] * (BLOCK_R / 2 + 0.6))
        bore = cyl(0.14, BLOCK_R + 1.0, outer, (-rd[0], 0, -rd[2]))
        blk = blk.cut(bore)
        screw = cyl(0.125, BLOCK_R / 2 + 0.6 - 0.15, outer, (-rd[0], 0, -rd[2]))
        head = cyl(0.40, 0.45, outer, (rd[0], 0, rd[2]))
        pad_p = along(hit, (rd[0], 0, rd[2]), 0.12)
        pad = cyl(0.19, 0.28, pad_p, (rd[0], 0, rd[2]))
        knobs = screw.union(head) if knobs is None else knobs.union(screw).union(head)
        pads = pad if pads is None else pads.union(pad)
    return dict(block=blk, knobs=knobs, pads=pads)


def pair_block(t):
    ax, az = polar(R_TOP, t)
    rd, td = rad_tan(t)
    centre = (ax, Y_RING_LO - PAIR_H / 2, az)
    blk = block(centre, t, PAIR_T, PAIR_H, PAIR_R)
    for side in (-1, +1):
        A, B = node_points(t, side)
        d_dn = cq.Vector(*[c - a for a, c in zip(A, B)]).normalized()
        blk = blk.cut(cyl(POLE_OD / 2 + 0.002, 3.0, along(A, d_dn, -1.5), d_dn))   # bonded bore
    # stud + knob under the block, two dowels into the ring
    blk = blk.cut(cyl(0.14, PAIR_H + 1, (ax, Y_RING_LO + 0.5, az), (0, -1, 0)))
    knob = cyl(0.125, PAIR_H + 0.9, (ax, Y_RING_LO + 0.3, az), (0, -1, 0)).union(
        cyl(0.45, 0.5, (ax, Y_RING_LO - PAIR_H - 0.05, az), (0, -1, 0)))
    dowels = None
    for s in (-1, 1):
        p = (ax + td[0] * 1.1 * s, Y_RING_LO - 0.6, az + td[2] * 1.1 * s)
        dw = cyl(0.125, 1.0, p, (0, 1, 0))
        dowels = dw if dowels is None else dowels.union(dw)
    return dict(block=blk, knob=knob, dowels=dowels)


def pole_tube_cut_at_pair(tube, t):
    return tube


def stub_and_ring(b):
    bx, bz = base_xz(b)
    stub = cyl(STUB_OD / 2, Y_STUB_TOP - (F["y_mcage_top"] - 2.5), (bx, F["y_mcage_top"] - 2.5, bz), (0, 1, 0))
    stub = stub.cut(cyl(STUB_OD / 2 - STUB_WALL, 10, (bx, F["y_mcage_top"] - 3, bz), (0, 1, 0)))
    ring = ring_sector(F["y_mcage_top"] - PR["ply"], PR["ply"], PR["mcage_ring_id"] / 2, PR["mcage_ring_od"] / 2, b, 22)
    ring = ring.cut(cyl(STUB_OD / 2 + 0.01, 3, (bx, F["y_mcage_top"] - 2, bz), (0, 1, 0)))
    return stub, ring


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
        a.add(sb["knobs"], name=f"socket_knobs_{b}", color=KNOB)
        a.add(sb["pads"], name=f"socket_pads_{b}", color=BRASS)
        stub, ring = stub_and_ring(b)
        a.add(stub, name=f"stub_{b}", color=STUB)
        a.add(ring, name=f"box_ring_{b}", color=BIRCH)
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
    add(sb["knobs"], "knobs", KNOB)
    add(sb["pads"], "brass_pads", BRASS)
    stub, ring = stub_and_ring(b)
    add(stub, "stub", STUB)
    add(ring, "box_ring", BIRCH)
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
        tube = cyl(POLE_OD / 2, 6.0, along(A, d_dn, -0.9), d_dn)
        tube = tube.cut(cyl(BORE / 2, 6.0, along(A, d_dn, -0.9), d_dn))
        a.add(tube, name=f"pole_{side}", color=CARBON)
    return a


if __name__ == "__main__":
    out = "out/truss_joints"
    os.makedirs(out, exist_ok=True)
    full = build_full(); full.save(f"{out}/joints_full.glb")
    sd = build_socket_detail(); sd.save(f"{out}/socket_detail.glb")
    ss = build_socket_detail(section=True); ss.save(f"{out}/socket_section.glb")
    pd = build_pair_detail(); pd.save(f"{out}/pair_detail.glb")
    socket_block(90)["block"].val().exportStep(f"{out}/socket_block_90.step")
    pair_block(30)["block"].val().exportStep(f"{out}/pair_block_30.step")
    A, B = node_points(30, 1)
    pole_parts(A, B)[0].val().exportStep(f"{out}/pole_plug.step")
    L = math.dist(*node_points(30, 1))
    lens = {f'{t}->{(t + 60 * s) % 360}': round(math.dist(*node_points(t, s)), 3) for t in TOPS for s in (-1, 1)}
    print(json.dumps(dict(pole_node_to_node_in=round(L, 2), pole_lengths_in=lens, tube_len_in=round(L - 0.6 - S_SHOULDER - SHOULDER_L, 2),
                          plug_nose_to_shoulder_in=round(S_SHOULDER - S_NOSE, 3), shank_od_in=round(BORE - 0.006, 3),
                          cup_depth_in=round(S_SHOULDER, 3), node_offset_in=NODE_OFF,
                          spigot_od_in=round(STUB_OD - 2 * STUB_WALL - 0.006, 3), stub_od_in=STUB_OD), indent=1))
