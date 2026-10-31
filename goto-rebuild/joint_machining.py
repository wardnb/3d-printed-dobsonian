"""
Machining package for the truss joint blocks (2026-10-31). Run after truss_joints.py (reads out/params.json).

Every cup in a socket block and every bonded bore in a pair block lies on its pole's axis, which leans ~13.3-13.6 deg on
a compound angle. The AltMill is 3-axis, so each one is cut with the block sitting on a small 3D-printed wedge fixture
(one per station, Voron) that stands that axis vertical; the cut itself is generated G-code (helical, so no special tools).

Block frames (inches): t tangential (+ toward increasing angle), u up the tube, r radial outward.
  socket block: datum = centre of the block's underside (= stub top); stock 3.6 t x 2.0 r x 2.1 u. The 1.569" spigot
                is a separate turned part (truss_joints.SPIGOT_*), bolted and bonded into a register in the underside, so
                the stack on the fixture stays ~3.6" (it was 5.1" with integral spigot stock: too tall for the AltMill).
  pair block:   datum = centre of the top face (against the cage ring); 3.6 t x 1.6 r x 1.6 u.
Station frame: the block's resting face lies on the fixture's sloped face ("plate"); the plate is rotated by beta about its
normal and tilted by tau about machine X so the feature axis comes out exactly vertical. Machine origin for the G-code =
the top front-left corner of the fixture's datum post (touch-plate XYZ zero on that corner).

Writes out/joint_machining/: report.json (angles, stations, op lists), fixture_<station>.stl/.step, <station>.nc,
DXFs for the 2.5D ops, sheet.png (one-page drawing).
"""
import json
import math
import os

import numpy as np
import cadquery as cq

import truss_joints as T

IN = 25.4
OUT = os.path.join("out", "joint_machining")
os.makedirs(OUT, exist_ok=True)

SOCK_STOCK = (T.BLOCK_T, T.BLOCK_R, T.BLOCK_H)                  # t, r, u (spigot is a separate turned part)
PAIR_STOCK = (T.PAIR_T, T.PAIR_R, T.PAIR_H)
K30 = math.tan(T.HALF)                                          # cone wall: r = K30 * (z - apex)
FIX_WALL, FIX_WALL_H, FIX_MIN = 0.25, 0.45, 0.40                # fence wall thickness/height, fixture min thickness
POST = 0.75                                                     # datum post (square)


def unit(v):
    v = np.asarray(v, float)
    return v / np.linalg.norm(v)


def to_block(deg, vec):
    rd, td = T.rad_tan(deg)
    return np.array([vec[0] * td[0] + vec[2] * td[2], vec[1], vec[0] * rd[0] + vec[2] * rd[2]])


def features():
    """Every machined pole feature in its block frame. Socket 330 is the same part as 210 (checked)."""
    out = []
    for b, name in ((90, "socket_point"), (210, "socket_back"), (330, "socket_back_check")):
        bx, bz = T.base_xz(b)
        for side in (-1, 1):
            t = (b - 60 * side) % 360
            A, B = T.node_points(t, side)
            a = to_block(b, unit(np.subtract(A, B)))                       # out of the cup = toward the apex
            p = to_block(b, np.subtract(B, (bx, T.Y_STUB_TOP, bz)))       # cup apex, datum = stub top centre
            out.append(dict(part=name, base=b, side=side, kind="cup", axis=a, point=p,
                            label=f"{name}_{'L' if side < 0 else 'R'}"))
    for t in T.TOPS:
        ax, az = T.polar(T.R_TOP, t)
        for side in (-1, 1):
            A, B = T.node_points(t, side)
            dn = unit(np.subtract(B, A))
            a = to_block(t, dn)                                           # out of the bore = down the pole
            node = to_block(t, np.subtract(A, (ax, T.Y_RING_LO, az)))
            floor = node - T.TUBE_PAST_APEX * a                           # bore floor centre (= tube end)
            out.append(dict(part=f"pair_{t}", base=t, side=side, kind="bore", axis=a, point=floor, node=node,
                            label=f"pair_{t}_{'L' if side < 0 else 'R'}"))
    return out


def plate_frame(f, p):
    """block (t, u, r) -> plate (x, y, z), z = out of the resting face."""
    t, u, r = p
    if f["kind"] == "cup":
        return np.array([t, r, u])                                        # block underside on the plate
    return np.array([t, -r, -u])                                          # pair block upside down (top face on the plate)


def plate_axis(f):
    t, u, r = f["axis"]
    return unit([t, r, u]) if f["kind"] == "cup" else unit([t, -r, -u])


def Rz(b):
    c, s = math.cos(b), math.sin(b)
    return np.array([[c, -s, 0], [s, c, 0], [0, 0, 1]])


def Rx(a):
    c, s = math.cos(a), math.sin(a)
    return np.array([[1, 0, 0], [0, c, -s], [0, s, c]])


def station(f):
    ap = plate_axis(f)
    tau = math.acos(ap[2])
    phi = math.atan2(ap[1], ap[0])
    beta = -math.pi / 2 - phi
    M = Rx(-tau) @ Rz(beta)
    assert np.allclose(M @ ap, [0, 0, 1], atol=1e-9)
    return dict(tau=tau, beta=beta, M=M)


def footprint(f):
    """Block footprint corners in plate xy (before beta), and the stock height above the plate."""
    if f["kind"] == "cup":
        T_, R_, H_ = SOCK_STOCK
    else:
        T_, R_, H_ = PAIR_STOCK
    return [(-T_ / 2, -R_ / 2), (T_ / 2, -R_ / 2), (T_ / 2, R_ / 2), (-T_ / 2, R_ / 2)], H_


def build(f):
    """Fixture solid (machine frame, inches -> mm), the block in place, and the machine coords of everything."""
    st = station(f)
    M = st["M"]
    corners, H = footprint(f)
    # plate polygon: footprint + fences + clamp lugs, rotated by beta
    pad = 0.75
    xs = [c[0] for c in corners]; ys = [c[1] for c in corners]
    plate_poly = [(min(xs) - pad, min(ys) - pad), (max(xs) + pad, min(ys) - pad),
                  (max(xs) + pad, max(ys) + pad), (min(xs) - pad, max(ys) + pad)]
    Rb = Rz(st["beta"])

    def mach(p):  # plate (x, y, z) in the block's own orientation -> machine
        return M @ Rz(0) @ (Rb @ np.asarray(p, float) * 0 + np.asarray(p, float)) if False else Rx(-st["tau"]) @ (Rb @ np.asarray(p, float))
    # fixture body: plate prism from z = -10 to 0 (plate frame, rotated by beta), tilted, then cut flat at the bottom
    pts = [mach((x, y, 0.0)) for x, y in plate_poly]
    zmin = min(p[2] for p in pts) - FIX_MIN
    prism = (cq.Workplane("XY").polyline([(x * IN, y * IN) for x, y in plate_poly]).close().extrude(-10 * IN))
    walls = None
    # fences: along the block's -r edge (y = min) and its -t end (x = min), FIX_WALL thick, outside the footprint
    w1 = cq.Workplane("XY").center(0, (min(ys) - FIX_WALL / 2) * IN).rect((max(xs) - min(xs) + 2 * FIX_WALL) * IN, FIX_WALL * IN).extrude(FIX_WALL_H * IN)
    w2 = cq.Workplane("XY").center((min(xs) - FIX_WALL / 2) * IN, 0).rect(FIX_WALL * IN, (max(ys) - min(ys)) * IN).extrude(FIX_WALL_H * IN)
    body = prism.union(w1).union(w2)
    # clamp inserts: two 1/4-20 heat-set holes on the free sides (strap clamps over the block)
    for cx, cy in ((max(xs) + 0.4, 0.0), (0.0, max(ys) + 0.4)):
        body = body.cut(cq.Workplane("XY").center(cx * IN, cy * IN).circle(0.18 * IN).extrude(-0.9 * IN).translate((0, 0, 0.01)))
    # rotate into machine: beta about z, tilt about x
    body = body.rotate((0, 0, 0), (0, 0, 1), math.degrees(st["beta"])).rotate((0, 0, 0), (1, 0, 0), -math.degrees(st["tau"]))
    cut = cq.Workplane("XY").box(40 * IN, 40 * IN, 20 * IN).translate((0, 0, (zmin - 10) * IN))
    body = body.cut(cut)
    # datum post: machine-aligned square post at the fixture's front-left corner, top 0.1 above the highest fixture point
    bb = body.val().BoundingBox()
    x0, y0 = bb.xmin / IN, bb.ymin / IN
    top = bb.zmax / IN + 0.1
    post = cq.Workplane("XY").box(POST * IN, POST * IN, (top - zmin) * IN).translate(
        ((x0 - POST / 2 + 0.02) * IN, (y0 - POST / 2 + 0.02) * IN, ((top + zmin) / 2) * IN))
    base_web = cq.Workplane("XY").box((POST + 0.5) * IN, (POST + 0.5) * IN, FIX_MIN * IN).translate(
        ((x0 - POST / 2 + 0.25) * IN, (y0 - POST / 2 + 0.25) * IN, (zmin + FIX_MIN / 2) * IN))
    bb2 = body.val().BoundingBox()
    slab = cq.Workplane("XY").box((bb2.xmax / IN - (x0 - POST)) * IN, (bb2.ymax / IN - (y0 - POST)) * IN, FIX_MIN * IN).translate(
        (((bb2.xmax / IN + x0 - POST) / 2) * IN, ((bb2.ymax / IN + y0 - POST) / 2) * IN, (zmin + FIX_MIN / 2) * IN))
    body = body.union(post).union(base_web).union(slab)
    origin = np.array([x0 - POST + 0.02, y0 - POST + 0.02, top])            # WCS zero: post's top front-left corner
    # block in place (for the picture) and the feature in machine coordinates relative to the WCS
    blk = (cq.Workplane("XY").polyline([(x * IN, y * IN) for x, y in corners]).close().extrude(H * IN)
           .rotate((0, 0, 0), (0, 0, 1), math.degrees(st["beta"])).rotate((0, 0, 0), (1, 0, 0), -math.degrees(st["tau"])))
    feat = mach(plate_frame(f, f["point"])) - origin
    # highest point of the block's top face (for the start height)
    top_face = [mach((x, y, H)) - origin for x, y in corners]
    zbot = zmin - origin[2]
    return dict(body=body, block=blk, feat=feat, top_z=max(p[2] for p in top_face), st=st, zbot=zbot,
                origin=origin, H=H)


# ---------------------------------------------------------------- G-code
RPM = 18000


def g_header(title):
    return [f"( {title} )", "( units inch, WCS zero = datum post top front-left corner; the block top is ABOVE Z0, rapids at block top + 0.5; check every number before cutting )",
            "G20 G90 G17 G94", f"M3 S{RPM}", "G4 P3"]


SAFE_ABOVE_TOP = 0.50      # rapid height above the highest point of the block (fences, clamps and inserts are lower)


def safe_z(g):
    return round(g["top_z"] + SAFE_ABOVE_TOP, 3)


def g_footer(sz):
    return [f"G0 Z{sz:.3f}", "M5", "M30"]


def helix_ring(cx, cy, r, z_from, z_to, step, feed, pts=48):
    """Helix of radius r around (cx, cy) from z_from down to z_to, then one flat lap."""
    out = []
    if r <= 0.001:
        out.append(f"G1 X{cx:.4f} Y{cy:.4f} Z{z_to:.4f} F{feed / 3:.0f}")
        return out
    n_turns = max(1, math.ceil((z_from - z_to) / step))
    out.append(f"G0 X{cx + r:.4f} Y{cy:.4f}")
    out.append(f"G1 Z{z_from:.4f} F{feed / 2:.0f}")
    for k in range(n_turns * pts + 1):
        a = 2 * math.pi * k / pts
        z = z_from - (z_from - z_to) * min(1.0, k / (n_turns * pts))
        out.append(f"G1 X{cx + r * math.cos(a):.4f} Y{cy + r * math.sin(a):.4f} Z{z:.4f} F{feed:.0f}")
    for k in range(pts + 1):
        a = 2 * math.pi * k / pts
        out.append(f"X{cx + r * math.cos(a):.4f} Y{cy + r * math.sin(a):.4f}")
    return out


def gcode_cup(f, g):
    """Socket cup: rough with a 1/4" 3-flute flat end mill in stepped rings, finish with a 1/8" ball on one continuous
    helix that follows the 60 deg cone, then a 0.29" stud hole through the 0.10" web into the wheel pocket."""
    cx, cy, za = g["feat"]
    z0 = g["top_z"] + 0.05
    sz = safe_z(g)
    L = g_header(f"{f['label']}: 60 deg cup + stud hole; fixture tilt {math.degrees(g['st']['tau']):.2f} deg")
    L += ["( T1 = 1/4 3FL carbide flat end mill, rough )", f"G0 Z{sz:.3f}", f"G0 X{cx:.4f} Y{cy:.4f}"]
    z = z0
    while z > za + 0.25:
        z = max(z - 0.035, za + 0.25)
        rmax = K30 * (z - za) - 0.125 - 0.010
        if rmax <= 0:
            continue
        L.append(f"G1 Z{z:.4f} F15")
        r = 0.0
        while r < rmax:
            r = min(r + 0.09, rmax)
            L.append(f"G1 X{cx + r:.4f} Y{cy:.4f} F40")
            L.append(f"G2 X{cx + r:.4f} Y{cy:.4f} I{-r:.4f} J0 F40")
        L.append(f"G1 X{cx:.4f} Y{cy:.4f}")
    L += [f"G0 Z{sz:.3f}", "M5", "( T2 = 1/8 ball end mill, finish )", "M0 (change to 1/8 ball, re-zero Z on the post)", f"M3 S{RPM}", "G4 P3"]
    rb = 0.0625
    zw_end = za + rb * math.cos(T.HALF) / K30 + 0.002
    zw = z0 - rb * math.sin(T.HALF)
    pts, step = 72, 0.004
    first = True
    while zw > zw_end:
        for k in range(pts):
            zw_k = max(zw - step * k / pts, zw_end)
            rc = K30 * (zw_k - za) - rb * math.cos(T.HALF)
            zc = zw_k + rb * math.sin(T.HALF)
            a = 2 * math.pi * k / pts
            x, y = cx + rc * math.cos(a), cy + rc * math.sin(a)
            if first:
                L += [f"G0 X{x:.4f} Y{y:.4f}", f"G1 Z{zc:.4f} F15"]
                first = False
            L.append(f"G1 X{x:.4f} Y{y:.4f} Z{zc:.4f} F35")
        zw -= step
    L += [f"G0 Z{sz:.3f}", "M5", "( T3 = 1/8 flat end mill, stud hole 0.290 )", "M0 (change to 1/8 flat, re-zero Z)", f"M3 S{RPM}", "G4 P3"]
    L += helix_ring(cx, cy, 0.145 - 0.0625, za + 0.05, za - 0.30, 0.01, 12)
    L += g_footer(sz)
    return L


def gcode_bore(f, g):
    """Pair bore: 1.254" blind bore by helical interpolation with a 1/2" 3-flute flat end mill, flat floor at the tube end."""
    cx, cy, zf = g["feat"]
    z0 = g["top_z"] + 0.05
    sz = safe_z(g)
    L = g_header(f"{f['label']}: 1.254 blind bonded bore; fixture tilt {math.degrees(g['st']['tau']):.2f} deg")
    L += ["( T1 = 1/2 3FL carbide flat end mill )", f"G0 Z{sz:.3f}"]
    r_tool = 0.25
    for r in (0.627 - r_tool - 0.12, 0.627 - r_tool - 0.010):
        L += helix_ring(cx, cy, r, z0, zf + 0.005, 0.03, 30)
        L.append(f"G1 X{cx:.4f} Y{cy:.4f} F20")
        L.append(f"G0 Z{sz:.3f}")
    L += ["( finish pass, full depth )"] + helix_ring(cx, cy, 0.627 - r_tool, z0, zf, 0.06, 25)
    L.append(f"G1 X{cx:.4f} Y{cy:.4f} F20")
    L += g_footer(sz)
    return L


# ---------------------------------------------------------------- 2.5D ops (Aspire DXFs)
def socket_pocket_dxf():
    """Outside (radial) face of the socket block, viewed from outside: the two thumbwheel pockets."""
    T_, R_, H_ = SOCK_STOCK
    w = cq.Workplane("XY").rect(T_ * IN, H_ * IN).extrude(0.1 * IN)              # x = t, y = u
    ys = -H_ / 2                                                                 # datum (stub top) in this view
    for side in (-1, 1):
        apex_u = 1.0
        top = apex_u - T.POCKET_TOP
        cxp = 0.8 * (1 if side < 0 else -1) * -1
        w = w.cut(cq.Workplane("XY").center(cxp * IN, (ys + top - T.POCKET_H / 2) * IN).rect(T.POCKET_W * IN, T.POCKET_H * IN).extrude(0.1 * IN))
    cq.exporters.export(w.section(0.05 * IN), os.path.join(OUT, "socket_op2_wheel_pockets_outside_face.dxf"))


def socket_spigot_dxf():
    """Underside of the socket block: Ø0.504 x 0.12 register + 1/4-20 tap drill on the centreline."""
    T_, R_, H_ = SOCK_STOCK
    w = cq.Workplane("XY").rect(T_ * IN, R_ * IN).extrude(0.1 * IN)
    w = w.cut(cq.Workplane("XY").circle((T.SPIGOT_PILOT_D / 2 + 0.002) * IN).extrude(0.1 * IN))
    w = w.cut(cq.Workplane("XY").circle(0.1005 * IN).extrude(0.1 * IN))
    cq.exporters.export(w.section(0.05 * IN), os.path.join(OUT, "socket_op5_underside_register_and_tap.dxf"))
    for old in ("socket_op5_spigot_pocket_around_1.569_island.dxf",):
        if os.path.exists(os.path.join(OUT, old)):
            os.remove(os.path.join(OUT, old))


def pair_top_dxf(t, feats):
    T_, R_, H_ = PAIR_STOCK
    w = cq.Workplane("XY").rect(T_ * IN, R_ * IN).extrude(0.1 * IN)
    holes = [(0, T.PAIR_STUD_R, 0.281), (0, T.PAIR_DOWEL_R, 0.250)]
    for f in feats:
        if f["part"] == f"pair_{t}":
            holes.append((f["point"][0], f["point"][2], 0.25))                    # bond vent above the bore floor
    for x, y, d in holes:
        w = w.cut(cq.Workplane("XY").center(x * IN, y * IN).circle(d / 2 * IN).extrude(0.1 * IN))
    cq.exporters.export(w.section(0.05 * IN), os.path.join(OUT, f"pair_{t}_op1_top_face_holes.dxf"))
    return holes


def wedge_washer():
    tau = math.radians(13.43)
    d = T.WEDGE_D
    w = (cq.Workplane("XY").rect(0.95 * IN, (T.POCKET_H - 0.02) * IN).extrude((T.WEDGE_MIN + d * math.tan(tau)) * IN)
         .cut(cq.Workplane("XY").circle(0.15 * IN).extrude(1 * IN)))
    cutter = cq.Workplane("XY").box(3 * IN, 3 * IN, 2 * IN).translate((0, 0, (1 + T.WEDGE_MIN + d / 2 * math.tan(tau)) * IN))
    cutter = cutter.rotate((0, 0, (T.WEDGE_MIN + d / 2 * math.tan(tau)) * IN), (1 * IN, 0, (T.WEDGE_MIN + d / 2 * math.tan(tau)) * IN), 13.43)
    w = w.cut(cutter)
    w.val().exportStep(os.path.join(OUT, "wedge_washer_x6.step"))
    return round(T.WEDGE_MIN + d * math.tan(tau), 3)


def main():
    feats = features()
    # the 330 socket must equal the 210 one
    back = [f for f in feats if f["part"] == "socket_back"]
    chk = [f for f in feats if f["part"] == "socket_back_check"]
    same = all(np.allclose(a["axis"], b["axis"], atol=1e-6) and np.allclose(a["point"], b["point"], atol=1e-6) for a, b in zip(back, chk))
    feats = [f for f in feats if f["part"] != "socket_back_check"]
    rep = dict(socket_210_equals_330=bool(same), stations=[])
    for f in feats:
        g = build(f)
        tag = f["label"]
        cq.exporters.export(g["body"], os.path.join(OUT, f"fixture_{tag}.stl"))
        g["body"].val().exportStep(os.path.join(OUT, f"fixture_{tag}.step"))
        code = gcode_cup(f, g) if f["kind"] == "cup" else gcode_bore(f, g)
        open(os.path.join(OUT, f"{tag}.nc"), "w").write("\n".join(code) + "\n")
        a = f["axis"]
        rep["stations"].append(dict(
            station=tag, part=f["part"], kind=f["kind"],
            axis_in_block_t_u_r=[round(x, 4) for x in a],
            tilt_deg=round(math.degrees(math.acos(abs(a[1]))), 2),
            lean_az_deg_from_t=round(math.degrees(math.atan2(a[2], a[0] * (1 if a[1] > 0 else 1))), 2),
            point_in_block_t_u_r=[round(x, 3) for x in f["point"]],
            fixture_tilt_deg=round(math.degrees(g["st"]["tau"]), 3), block_rotation_deg=round(math.degrees(g["st"]["beta"]), 2),
            feature_xyz_from_post_corner=[round(x, 4) for x in g["feat"]],
            block_top_highest_z=round(g["top_z"], 3), fixture_bottom_z=round(g["zbot"], 3),
            gcode=f"{tag}.nc", gcode_lines=len(code)))
    socket_pocket_dxf()
    socket_spigot_dxf()
    pair_holes = {t: [(round(x, 3), round(y, 3), d) for x, y, d in pair_top_dxf(t, feats)] for t in T.TOPS}
    rep["pair_top_face_holes_t_r_dia"] = pair_holes
    rep["wedge_washer_max_thickness_in"] = wedge_washer()
    rep["tube_bond_length_in"] = round((T.PAIR_H - 0.6 + T.TUBE_PAST_APEX * 0.972) / 0.972, 2)
    rep["ops"] = {
        "socket block (x3: 1 point, 2 back), stock 2.0 x 4 flat bar cut 2.20 (faced to 3.6 t x 2.0 r x 2.1 u)": [
            "Op1 vise: square the stock to 3.60 x 2.00 x 2.10",
            "Op2 vise, outside (radial) face up: two wheel pockets 1.00 wide x 0.75 tall, 1.25 deep (socket_op2 DXF)",
            "Op3/Op4 printed fixture, station L then R: 60 deg cup + 0.29 stud hole (.nc files, touch-plate zero on the post corner)",
            "Op5 vise, underside up: Ø0.504 register 0.12 deep + #7 (0.201) drill 0.70 deep on the centre, tap 1/4-20 0.60 deep (socket_op5 DXF)",
            "Spigot (turned, x3, from 1 3/4 round with the cone plugs): Ø1.569 x 1.50 (fit to the measured stub bore, 0.003 radial bond gap), Ø0.50 x 0.11 pilot on top, 0.266 through hole, Ø0.39 x 0.26 counterbore in the bottom (socket_spigot STEP)",
            "Assemble: bond the spigot's top face and pilot to the block (structural epoxy) and pull up with a 1/4-20 x 1-3/4 SHCS + Loctite from below; then bond the spigot into the stub as before",
            "Wedge washer x2 per block under the thumbwheels (wedge_washer STEP, 13.4 deg; flat-bottomed, key in the pocket)"],
        "pair block (x3: 30, 150 mirror, 270), stock 2 x 2 square bar cut 3.70 (faced to 3.6 t x 1.6 r x 1.6 u)": [
            "Op1 vise, top (ring) face up: 0.281 stud hole through at r -0.45, 1 x 1/4 dowel hole reamed 0.50 deep at r +0.35 (1/4 x 3/4 dowel; stud + dowel locate it, rotation slop ±0.6° moves a node 0.008 in), 2 x 1/4 bond vents down to the bore floors (pair_<t> DXF)",
            "Op2/Op3 printed fixture, block upside down, station L then R: 1.254 blind bore to the tube-end floor (.nc files)",
            "Bond the tubes to the floor with a length jig (node-to-node 37.30 / 37.35)"],
    }
    json.dump(rep, open(os.path.join(OUT, "report.json"), "w"), indent=1)
    for s in rep["stations"]:
        print(f"{s['station']:16s} tilt {s['tilt_deg']:6.2f}  fixture {s['fixture_tilt_deg']:6.2f}  rot {s['block_rotation_deg']:8.2f}  "
              f"feature {s['feature_xyz_from_post_corner']}  lines {s['gcode_lines']}")
    print("210 == 330:", same, " tube bond length", rep["tube_bond_length_in"], " wedge washer max t", rep["wedge_washer_max_thickness_in"])
    return rep, feats




def sheet():
    """One-page drawing: socket block (top, outside face, side), pair block top, station table, ops."""
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from matplotlib.patches import Rectangle, Circle, FancyBboxPatch
    rep = json.load(open(os.path.join(OUT, "report.json")))
    fig = plt.figure(figsize=(17, 11))
    fig.suptitle("Truss joint blocks: machining sheet (inches; 6061-T6)  —  joint_machining.py, 2026-10-31", fontsize=13, x=0.02, ha="left")
    T_, R_, H_ = SOCK_STOCK

    def dim(ax, x0, y0, x1, y1, txt, off=0.25, horiz=True):
        if horiz:
            ax.annotate("", (x0, y0 - off), (x1, y1 - off), arrowprops=dict(arrowstyle="<->", lw=0.7))
            ax.text((x0 + x1) / 2, y0 - off - 0.12, txt, ha="center", va="top", fontsize=7)
        else:
            ax.annotate("", (x0 - off, y0), (x1 - off, y1), arrowprops=dict(arrowstyle="<->", lw=0.7))
            ax.text(x0 - off - 0.08, (y0 + y1) / 2, txt, ha="right", va="center", fontsize=7, rotation=90)

    # socket top view
    ax = fig.add_axes([0.02, 0.56, 0.22, 0.36]); ax.set_title("Socket block, top (cup) face", fontsize=9)
    ax.add_patch(Rectangle((-T_ / 2, -R_ / 2), T_, R_, fill=False, lw=1.2))
    top_h = T.BLOCK_H - 1.0
    for s in (-1, 1):
        ax.add_patch(Circle((0.8 * s, 0), top_h * K30, fill=False, lw=0.8, ls="--"))
        ax.plot(0.8 * s, 0, "k+", ms=8)
    ax.add_patch(Circle((0, 0), (T.STUB_OD - 2 * T.STUB_WALL - 0.006) / 2, fill=False, lw=0.6, ls=":", color="gray"))
    dim(ax, -T_ / 2, -R_ / 2, T_ / 2, -R_ / 2, f"{T_:.2f}")
    dim(ax, -T_ / 2, -R_ / 2, -T_ / 2, R_ / 2, f"{R_:.2f}", horiz=False)
    dim(ax, -0.8, R_ / 2 + 0.75, 0.8, R_ / 2 + 0.75, "cup apexes 1.600 apart, 1.000 above the datum")
    ax.text(0, -0.15, "spigot (below)", ha="center", fontsize=6, color="gray")
    ax.text(T_ / 2, R_ / 2 + 0.08, "outside face ↑", ha="right", fontsize=6)
    ax.set_xlim(-2.4, 2.4); ax.set_ylim(-1.8, 2.0); ax.set_aspect("equal"); ax.axis("off")
    # socket outside-face view (pockets + spigot)
    ax = fig.add_axes([0.25, 0.56, 0.22, 0.36]); ax.set_title("Socket block, outside face (Op2), underside register (Op5), turned spigot", fontsize=9)
    ax.add_patch(Rectangle((-T_ / 2, 0), T_, T.BLOCK_H, fill=False, lw=1.2))
    d_sp = T.STUB_OD - 2 * T.STUB_WALL - 0.006
    SPIGOT_L = T.SPIGOT_L
    ax.add_patch(Rectangle((-d_sp / 2, -SPIGOT_L), d_sp, SPIGOT_L, fill=False, lw=1.0, ls="--"))
    ax.add_patch(Rectangle((-T.SPIGOT_PILOT_D / 2, 0), T.SPIGOT_PILOT_D, T.SPIGOT_PILOT_H + 0.01, fill=True, color="#ddd", lw=0))
    ax.add_patch(Rectangle((-0.1, 0), 0.2, T.SPIGOT_DRILL_DEPTH, fill=False, lw=0.6))
    for s in (-1, 1):
        top = 1.0 - T.POCKET_TOP
        ax.add_patch(Rectangle((0.8 * s - T.POCKET_W / 2, top - T.POCKET_H), T.POCKET_W, T.POCKET_H, fill=True, color="#ddd", lw=0))
        ax.plot(0.8 * s, 1.0, "k+", ms=8)
    ax.text(0, -SPIGOT_L / 2, f"turned spigot (separate part)\nØ{d_sp:.3f} x {SPIGOT_L:.2f}, bolted + bonded\n(bond in stub bore)", ha="center", va="center", fontsize=7)
    ax.text(0.8, 1.0 - T.POCKET_TOP - T.POCKET_H / 2, f"{T.POCKET_W:.2f} x {T.POCKET_H:.2f}\n1.25 deep", ha="center", va="center", fontsize=6)
    dim(ax, -T_ / 2, 0, -T_ / 2, T.BLOCK_H, f"{T.BLOCK_H:.2f} block", horiz=False)
    ax.text(T_ / 2 + 0.05, 0, "← datum (stub top)", ha="left", fontsize=6)
    ax.set_xlim(-2.6, 2.2); ax.set_ylim(-2.0, 2.6); ax.set_aspect("equal"); ax.axis("off")
    # pair block top
    ax = fig.add_axes([0.48, 0.60, 0.22, 0.30]); ax.set_title("Pair block, top (ring) face, Op1 holes  [30 shown]", fontsize=9)
    Tp, Rp, Hp = PAIR_STOCK
    ax.add_patch(Rectangle((-Tp / 2, -Rp / 2), Tp, Rp, fill=False, lw=1.2))
    for x, y, d in rep["pair_top_face_holes_t_r_dia"]["30"]:
        ax.add_patch(Circle((x, y), d / 2, fill=False, lw=0.9))
        ax.text(x, y + 0.22, f"Ø{d:.3f}", ha="center", fontsize=6)
    for f in features():
        if f["part"] == "pair_30":
            ax.add_patch(Circle((f["point"][0], f["point"][2]), 0.627, fill=False, lw=0.6, ls="--"))
    dim(ax, -Tp / 2, -Rp / 2, Tp / 2, -Rp / 2, f"{Tp:.2f}")
    dim(ax, -Tp / 2, -Rp / 2, -Tp / 2, Rp / 2, f"{Rp:.2f}", horiz=False)
    ax.text(0, -Rp / 2 - 0.55, "stud r −0.45, dowel r +0.35, vents over the bore floors; bores (dashed) cut from below on the fixture", ha="center", fontsize=6)
    ax.set_xlim(-2.4, 2.4); ax.set_ylim(-1.6, 1.4); ax.set_aspect("equal"); ax.axis("off")
    # fixture picture
    import matplotlib.image as mpimg
    ax = fig.add_axes([0.72, 0.55, 0.27, 0.38]); ax.set_title("Station fixture (printed), block in place: feature axis vertical", fontsize=9)
    pic = os.path.join(OUT, "fixture_view.png")
    if os.path.exists(pic):
        ax.imshow(mpimg.imread(pic))
    ax.axis("off")
    # station table
    ax = fig.add_axes([0.02, 0.05, 0.55, 0.45]); ax.axis("off")
    rows = []
    seen = {}
    for s in rep["stations"]:
        key = (s["fixture_tilt_deg"], s["block_rotation_deg"], tuple(s["feature_xyz_from_post_corner"]))
        shared = seen.get(key)
        seen.setdefault(key, s["station"])
        rows.append([s["station"], s["kind"], f"{s['fixture_tilt_deg']:.2f}", f"{s['block_rotation_deg']:.2f}",
                     "  ".join(f"{v:.3f}" for v in s["feature_xyz_from_post_corner"]),
                     f"same fixture as {shared}" if shared else f"fixture_{s['station']}"])
    tb = ax.table(cellText=rows, colLabels=["station", "feature", "tilt °", "block rot °", "feature X Y Z from post corner", "fixture"],
                  loc="upper left", cellLoc="left", colWidths=[0.14, 0.07, 0.07, 0.09, 0.30, 0.25])
    tb.auto_set_font_size(False); tb.set_fontsize(8); tb.scale(1, 1.35)
    ax.text(0, 0.02, "Cup: 60° included, apex at the X Y Z shown (stud hole Ø0.290 continues 0.30 below). Bore: Ø1.254 blind, floor at Z shown "
            "(= tube end, 0.30 past the pair node).\nTools: 1/4 3FL flat (cup rough, LOC ≥ 1.25), 1/8 ball and 1/8 flat (≥ 1.5 reach), 1/2 3FL flat (bore, LOC ≥ 1.5). "
            "Socket 210 and 330 are the same part (checked).", fontsize=7, va="bottom")
    # ops
    ax = fig.add_axes([0.60, 0.05, 0.39, 0.45]); ax.axis("off")
    y = 0.98
    for k, ops in rep["ops"].items():
        ax.text(0, y, k, fontsize=8, weight="bold", va="top", wrap=True); y -= 0.07
        for o in ops:
            ax.text(0.02, y, "• " + o, fontsize=7, va="top", wrap=True); y -= 0.075
        y -= 0.03
    ax.text(0, y, f"Bonded tube length into the pair block: {rep['tube_bond_length_in']} in (was 0.43). Wedge washer: 13.4°, max {rep['wedge_washer_max_thickness_in']} in.",
            fontsize=7, va="top")
    fig.savefig(os.path.join(OUT, "sheet.png"), dpi=110)
    plt.close(fig)


def fixture_view(label="socket_back_L"):
    """Small 3D picture of one fixture with its block, for the sheet."""
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from mpl_toolkits.mplot3d.art3d import Poly3DCollection
    f = [x for x in features() if x["label"] == label][0]
    g = build(f)

    def tris(s):
        vs, ts = [], []
        for fc in s.val().Faces():
            v, t = fc.tessellate(0.2, 0.3)
            b = len(vs); vs += [(p.x / IN, p.y / IN, p.z / IN) for p in v]; ts += [(a + b, c + b, d + b) for a, c, d in t]
        vs = np.array(vs); return [vs[list(t)] for t in ts]
    fig = plt.figure(figsize=(5, 4.4)); ax = fig.add_subplot(111, projection="3d")
    ax.add_collection3d(Poly3DCollection(tris(g["body"]), facecolor="#e8a34a", edgecolor="#8a5a20", lw=0.05, alpha=0.9))
    ax.add_collection3d(Poly3DCollection(tris(g["block"]), facecolor="#c0c4ca", edgecolor="#666", lw=0.05, alpha=0.85))
    cx, cy, cz = g["feat"] + g["origin"]
    ax.plot([cx, cx], [cy, cy], [cz - 0.5, cz + 2.0], "r-", lw=1.5)
    bb = g["body"].val().BoundingBox()
    ax.set_xlim(bb.xmin / IN, bb.xmax / IN); ax.set_ylim(bb.ymin / IN, bb.ymax / IN); ax.set_zlim(bb.zmin / IN, bb.zmin / IN + 5)
    ax.set_box_aspect((bb.xlen, bb.ylen, 5 * IN)); ax.view_init(22, -60); ax.axis("off")
    ax.set_title(f"{label}: red = cup axis (vertical)", fontsize=8)
    fig.savefig(os.path.join(OUT, "fixture_view.png"), dpi=110, bbox_inches="tight"); plt.close(fig)


if __name__ == "__main__":
    if not os.environ.get("SHEET_ONLY"):
        main()
    fixture_view()
    sheet()
