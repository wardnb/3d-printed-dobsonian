"""
Truss review: six poles between the mirror box and the upper cage, modelled as a 3D frame.
Inches, lb. Axis frame: tube axis +Y toward the sky, focuser on -X, altitude axis X.

Cage = rigid body (its own flex is in cage_fe.py: 0.02 mm with the quad spider).
Mirror box = rigid (base nodes fixed). The error is the primary's reflected focus against the
eyepiece's axis, as in cage_fe.py, with gravity swept through the altitude range.
"""
import json
import math
import numpy as np

from cage_fe import Frame, RIGID

P = json.load(open("out/params.json"))
F = P["frame"]
Y_SEC = F["y_sec"]                     # secondary centre above the altitude axis
Y_RING_LO = F["y_ring_lo"]
L_FOCUS = 11.9
X_FOC = -L_FOCUS                        # focal point (eyepiece) at (-11.9, y_sec, 0)
Y_MCAGE_TOP = F["y_mcage_top"]              # top ring's top face, from the measured box (below the axis)
R_TOP, R_BOT = P["params"]["truss_top_radius"], P["params"]["truss_bottom_radius"]
STUB_XZ = {int(k): tuple(v) for k, v in F["stub_xz"].items()}   # measured stub positions (zigzag bases)


def base_xz(deg, layout):
    d = deg % 360
    if layout == "zigzag":
        for a, xz in STUB_XZ.items():
            if abs((d - a + 180) % 360 - 180) < 1:
                return xz
    return pol(R_BOT, d)
Y_APEX, Y_BASE = Y_RING_LO - 0.6, Y_MCAGE_TOP + 1.6
FL = P["params"]["aperture"] * P["params"]["focal_ratio"]
Y_MIRROR = F["y_mirror"]
F_P = np.array([0.0, Y_MIRROR + FL, 0.0])          # primary's focus (rigid to the box)
N0 = np.array([-1, -1, 0]) / math.sqrt(2)
E_AL, G_AL = 10.0e6, 3.8e6

CAGE_LB, EYEPIECE_LB = 14.0, 3.3


def tube_props(od, wall, E=E_AL, G=G_AL):
    idd = od - 2 * wall
    A = math.pi / 4 * (od ** 2 - idd ** 2)
    I = math.pi / 64 * (od ** 4 - idd ** 4)
    return dict(E=E, G=G, A=A, Iy=I, Iz=I, J=2 * I), A


def pol(r, deg):
    a = math.radians(deg)
    return r * math.cos(a), r * math.sin(a)


def build(layout="pairs", od=1.0, wall=0.058, E=E_AL, G=G_AL, base="pinned", apex="rigid",
          base_spring=None, n_seg=4, pole_dens=0.0975):
    """layout: 'pairs' (apex 0/120/240, bases at +/-30 from each apex: 6 base points) or
    'zigzag' (bases at +/-60: 3 shared base points, octahedral).
    base: 'pinned' (translations fixed, free to rotate) or 'clamped' (all 6 fixed).
    apex: 'rigid' (the pair block ties both poles and the cage rigidly) or 'pinned' (ball joints).
    base_spring: lateral stiffness (lb/in) of each base clamp, None = rigid to the box."""
    fr = Frame()
    props, A = tube_props(od, wall, E, G)
    masses = []
    tops = [0, 120, 240]
    spread = 30 if layout == "pairs" else 60
    cage = fr.node(0, Y_SEC, 0)                       # cage CG on axis at the secondary height
    sec = cage
    eyep = fr.node(X_FOC, Y_SEC, 0); fr.beam(cage, eyep, RIGID)
    masses += [(cage, CAGE_LB), (eyep, EYEPIECE_LB)]
    base_nodes = {}
    for t in tops:
        tx, tz = pol(R_TOP, t)
        apex_node = fr.node(tx, Y_APEX, tz)
        if apex == "rigid":
            fr.beam(cage, apex_node, RIGID)
        for b in (t - spread, t + spread):
            b = b % 360
            bx, bz = base_xz(b, layout)
            if b not in base_nodes:
                bn = fr.node(bx, Y_BASE, bz)
                if base_spring is None:
                    fr.fix(bn, (0, 1, 2) if base == "pinned" else (0, 1, 2, 3, 4, 5))
                else:
                    anchor = fr.node(bx, Y_BASE - 0.5, bz)
                    fr.fix(anchor, (0, 1, 2, 3, 4, 5))
                    k = base_spring
                    # a short 'spring' beam whose EA/L and 12EI/L^3 both equal k
                    Ls = 0.5
                    fr.beam(anchor, bn, dict(E=k * Ls, G=k * Ls, A=1.0, Iy=k * Ls ** 3 / 12, Iz=k * Ls ** 3 / 12, J=k * Ls ** 3 / 6))
                base_nodes[b] = bn
            bn = base_nodes[b]
            # pole from base to apex, in segments (so its own weight and buckling-free bending show)
            p0, p1 = np.array(fr.nodes[bn]), np.array(fr.nodes[apex_node])
            prev = bn
            for s in np.linspace(0, 1, n_seg + 1)[1:]:
                q = p0 + (p1 - p0) * s
                nd = apex_node if s == 1 else fr.node(*q)
                if apex == "pinned" and s == 1:
                    nd = fr.node(*q); fr.beam(cage, nd, dict(E=1e9, G=1e9, A=1.0, Iy=1e-9, Iz=1e-9, J=1e-9))
                fr.beam(prev, nd, props)
                masses.append((nd, pole_dens * A * np.linalg.norm(p1 - p0) / n_seg))
                prev = nd
    return fr, masses, dict(cage=cage, eyep=eyep, sec=sec)


def error_at(fr, masses, ids, alt):
    g = np.array([0, -math.sin(math.radians(alt)), -math.cos(math.radians(alt))])
    fr.loads = {}
    for nd, lb in masses:
        fr.load(nd, np.r_[lb * g, 0, 0, 0])
    u = fr.solve()
    th = u[ids["cage"], 3:6]
    C = np.array(fr.nodes[ids["sec"]]) + u[ids["sec"], :3]
    n = N0 + np.cross(th, N0)
    Fr = F_P - 2 * np.dot(F_P - C, n) * n
    F0 = np.array([X_FOC, Y_SEC, 0.0])
    e = (Fr - F0) - u[ids["eyep"], :3]
    return np.array([0, e[1], e[2]]), e[0], u[ids["cage"], :3]


def sweep(label, **kw):
    fr, masses, ids = build(**kw)
    res = [error_at(fr, masses, ids, a) for a in (0, 45, 90)]
    errs = [r[0] for r in res]
    swing = np.linalg.norm(errs[0] - errs[2]) * 25.4
    resid = max(np.linalg.norm(e - errs[1]) * 25.4 for e in errs)
    focus = (res[2][1] - res[0][1]) * 25.4
    sag = np.linalg.norm(res[0][2]) * 25.4
    # lowest lateral mode: 1 lb at the cage CG along Z
    fr.loads = {}; fr.load(ids["cage"], [0, 0, 1.0, 0, 0, 0]); d = fr.solve()[ids["cage"], 2]
    W = CAGE_LB + EYEPIECE_LB
    f_lat = math.sqrt(386.1 / (d * W)) / (2 * math.pi)
    print(f"{label:52s} drift 0->90 {swing:6.3f} mm | after 45deg collimation {resid:6.3f} | cage sag @0 {sag:5.3f} mm"
          f" | focus shift {focus:6.3f} mm | lateral mode {f_lat:5.1f} Hz")
    return swing


if __name__ == "__main__":
    print(f"apex y {Y_APEX:.1f}, base y {Y_BASE:.1f}, pole length {math.dist(pol(R_BOT,30)+(Y_BASE,), pol(R_TOP,0)+(Y_APEX,)):.1f} in")
    sweep("pairs, 1.0 x 0.058 Al, base pinned (as drawn)")
    sweep("pairs, 1.0 x 0.058 Al, base clamped", base="clamped")
    sweep("pairs, 1.0 x 0.058 Al, apex pinned (ball joints)", apex="pinned")
    sweep("zigzag, 1.0 x 0.058 Al, base pinned", layout="zigzag")
    sweep("zigzag, 1.0 x 0.058 Al, base clamped", layout="zigzag", base="clamped")
    sweep("pairs, 1.0 x 0.065 Al", wall=0.065)
    sweep("pairs, 1.25 x 0.058 Al", od=1.25)
    sweep("pairs, 0.875 x 0.058 Al", od=0.875)
    sweep("pairs, 1.0 x 0.062 carbon (E 15 Msi)", wall=0.062, E=15e6, G=1.0e6, pole_dens=0.057)
    sweep("zigzag, 1.25 x 0.062 carbon (CHOSEN)", layout="zigzag", od=1.25, wall=0.062, E=15e6, G=1.0e6, pole_dens=0.057)
    sweep("zigzag, 1.25 carbon, base clamps 20,000 lb/in", layout="zigzag", od=1.25, wall=0.062, E=15e6, G=1.0e6, pole_dens=0.057, base_spring=20000)
    sweep("zigzag, 1.25 carbon, base clamps 5,000 lb/in", layout="zigzag", od=1.25, wall=0.062, E=15e6, G=1.0e6, pole_dens=0.057, base_spring=5000)
    sweep("zigzag, 1.25 x 0.058 Al (for comparison)", layout="zigzag", od=1.25)
    sweep("pairs, 1.0 Al, base clamps 20,000 lb/in", base_spring=20000)
    sweep("pairs, 1.0 Al, base clamps 5,000 lb/in", base_spring=5000)
    sweep("pairs, 1.0 Al, base clamps 1,000 lb/in (sloppy)", base_spring=1000)
