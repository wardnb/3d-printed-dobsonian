"""
Mirror box (lower cage) + truss + mirror, modelled together as a 3D frame (inches, lb).

Same metric as cage_fe.py / truss_fe.py: the primary's focus (carried rigidly by the mirror, so mirror shift
AND tilt count), reflected by the secondary on the (rigid) upper cage, minus the eyepiece's motion,
perpendicular to the focuser axis, swept horizon -> zenith; the worst residual after collimating at 45 deg.

The box as built (DobStuff, measured 2026-10-18/19, see docs/measurements.md):
  * top ring and mirror board: 18 mm Baltic birch, shield outline, 18" ID; modelled as circular rings at the
    centroid radius R_RING with a RING_W-wide section (the shield is wider at the back and point, so this is
    on the soft side);
  * seven 1.25" aluminium spacer tubes between them (wall ASSUMED 0.058", ends ASSUMED bolted through);
  * three 45 x 2.5 mm stub tubes (the cut-down DobStuff struts) through 45 mm holes in both boards, 1" proud;
    the truss sockets sit on them. How they are held axially is not known yet (`stub_axial`);
  * a 3" x 18 mm ply strip on each side between the boards; the new D bearing's web bolts to it at
    y = -8.4 .. -13.2 (two dowels + two bolts), which is where the whole tube is supported;
  * the 9-point cell hangs on three studs through the mirror board (angles ASSUMED at the stubs' 90/210/330).
Run from goto-rebuild/:  python mcage_fe.py
"""
import json
import math
import sys

import numpy as np

from cage_fe import Frame, RIGID
import truss_fe as tf

P = json.load(open("out/params.json"))
F, PP = P["frame"], P["params"]
PLY = PP["ply"]
Y_TOP, Y_BOT = F["y_mcage_top"], F["y_mcage_bot"]
Y_TR, Y_MB = Y_TOP - PLY / 2, Y_BOT + PLY / 2            # ring mid-planes
R_RING, RING_W = 9.9, 1.8                               # centroid radius, radial width (ASSUMED equivalent)
STRIP_X = PP["mcage_flat_half_width"] + PLY / 2          # strip mid-plane
WEB_Y = (-8.4, -10.8, -13.2)                             # bearing web dowels/bolts (rocker.bearing_outline)
E_PLY, G_PLY = 1.3e6, 0.10e6                             # Baltic birch, ASSUMED (panel shear governs twist)
E_AL, G_AL = 10.0e6, 3.8e6
Y_MIR = F["y_mirror"]
MIR_CG = Y_MIR - PP["mirror_thick"] / 2
CELL_Y = Y_MIR - PP.get("cell_cg_below_face", PP["mirror_thick"] + 0.7)


def rect(b, h, E, G):
    A = b * h
    a, c = max(b, h), min(b, h)
    J = a * c ** 3 * (1 / 3 - 0.21 * c / a * (1 - c ** 4 / (12 * a ** 4)))
    return dict(E=E, G=G, A=A, Iy=b * h ** 3 / 12, Iz=h * b ** 3 / 12, J=J)


def tube(od, wall, E=E_AL, G=G_AL):
    return tf.tube_props(od, wall, E, G)[0]


def pol(r, a):
    return r * math.cos(math.radians(a)), r * math.sin(math.radians(a))


def build(box="ply", spacer_ends="fixed", spacer_wall=0.058, stub_axial="board", cell_angles=(90, 210, 330),
          ring_w=RING_W, board_plate=None, ring_plate=None, strip_w=3.0, stub_brace=False, web_ties=False,
          truss_kw=None, e_ply=E_PLY, strip_k=None, hole_k=None, sock_k=None):
    """box: 'rigid' (stub tops and mirror fixed, the truss_fe baseline) or 'ply' (as built).
    spacer_ends: 'fixed' (bolted, end moments carried) or 'pinned'.
    stub_axial: where the stubs are held along the tube axis: 'board', 'ring' or 'both' (they always bear
    sideways in both holes).
    board_plate / ring_plate: (t, w) of a 6061 ring bonded/bolted to the mirror board / top ring.
    stub_brace: an aluminium tie from each stub's top to the nearest side strip's web zone.
    web_ties: the bearing web also bolts through to the top ring and the mirror board (a full-height web).
    e_ply: plywood modulus. strip_k: stiffness (lb/in) of each strip-to-board joint (None = rigid glue line).
    hole_k: sideways stiffness (lb/in) of each stub in its 45 mm hole (None = snug, ~rigid).
    sock_k: stiffness (lb/in) of each truss socket on its stub (None = rigid; truss_fe's 20,000 case)."""
    fr = Frame()
    masses = []
    tk = dict(layout="zigzag", od=1.25, wall=0.062, E=15e6, G=1.0e6, pole_dens=0.057)
    tk.update(truss_kw or {})
    # --- truss + rigid upper cage (as truss_fe.build), bases = stub-top socket points
    props, A = tf.tube_props(tk["od"], tk["wall"], tk["E"], tk["G"])
    cage = fr.node(0, tf.Y_SEC, 0)
    eyep = fr.node(tf.X_FOC, tf.Y_SEC, 0); fr.beam(cage, eyep, RIGID)
    masses += [(cage, tf.CAGE_LB), (eyep, tf.EYEPIECE_LB)]
    stub_xz = {int(k): tuple(v) for k, v in F["stub_xz"].items()}
    sock = {a: fr.node(x, tf.Y_BASE, z) for a, (x, z) in stub_xz.items()}
    for t in (30, 150, 270):                                  # pair blocks (upper_cage.APEX), +/-60 to the stubs
        tx, tz = pol(PP["truss_top_radius"], t)
        apex = fr.node(tx, tf.Y_APEX, tz); fr.beam(cage, apex, RIGID)
        for b in (t - 60, t + 60):
            b %= 360
            bn = sock[b]
            p0, p1 = np.array(fr.nodes[bn]), np.array(fr.nodes[apex])
            prev = bn
            for s in np.linspace(0, 1, 5)[1:]:
                nd = apex if s == 1 else fr.node(*(p0 + (p1 - p0) * s))
                fr.beam(prev, nd, props)
                masses.append((nd, tk["pole_dens"] * A * np.linalg.norm(p1 - p0) / 4))
                prev = nd
    # --- mirror + cell: one rigid body
    mir = fr.node(0, MIR_CG, 0)
    cell = fr.node(0, CELL_Y, 0); fr.beam(mir, cell, RIGID)
    masses += [(mir, PP["mirror_lb"]), (cell, PP["cell_lb"])]
    ids = dict(cage=cage, sec=cage, eyep=eyep, mir=mir)
    if box == "rigid":
        for nd in sock.values():
            fr.fix(nd, (0, 1, 2))
        fr.fix(mir, (0, 1, 2, 3, 4, 5))
        return fr, masses, ids

    # --- the two boards as rings of beams at the centroid radius
    feat = set(range(0, 360, 10)) | set(stub_xz) | set(cell_angles) | set(PP["mcage_spacer_angles"]) | {0, 180}
    angs = sorted(feat)
    gp = G_PLY * e_ply / E_PLY
    ringp = rect(ring_w, PLY, e_ply, gp)
    rings = {}
    for kind, y in (("top", Y_TR), ("board", Y_MB)):
        nodes = {a: fr.node(*_xz(R_RING, a, y)) for a in angs}
        for k, a in enumerate(angs):
            b = angs[(k + 1) % len(angs)]
            fr.beam(nodes[a], nodes[b], ringp, ref=np.array([0, 1, 0.0]))
        plate = board_plate if kind == "board" else ring_plate
        if plate:
            t_, w_ = plate
            yp = y + (PLY / 2 + t_ / 2) * (-1 if kind == "board" else 1)
            pn = {a: fr.node(*_xz(R_RING, a, yp)) for a in angs}
            pp_ = rect(w_, t_, E_AL, G_AL)
            for k, a in enumerate(angs):
                b = angs[(k + 1) % len(angs)]
                fr.beam(pn[a], pn[b], pp_, ref=np.array([0, 1, 0.0]))
                fr.beam(nodes[a], pn[a], RIGID)                 # bonded + bolted
            masses += [(pn[a], 0.0975 * t_ * w_ * 2 * math.pi * R_RING / len(angs)) for a in angs]
        rings[kind] = nodes
        area = 128.0                                          # shield ring area, in^2 (approx.)
        masses += [(nodes[a], area * PLY * 0.024 / len(angs)) for a in angs]
    # --- spacers
    sp = tube(PP["mcage_spacer_od"], spacer_wall)
    if spacer_ends == "pinned":
        sp = dict(sp, Iy=sp["Iy"] * 1e-4, Iz=sp["Iz"] * 1e-4)    # no end moments (a loose bolt in ply)
    for a in PP["mcage_spacer_angles"]:
        n0, n1 = rings["board"][a], rings["top"][a]
        mid = fr.node(*_xz(R_RING, a, (Y_TR + Y_MB) / 2))
        fr.beam(n0, mid, sp); fr.beam(mid, n1, sp)
        masses.append((mid, 0.0975 * math.pi * PP["mcage_spacer_od"] * spacer_wall * (Y_TR - Y_MB)))
    # --- side strips and the bearing supports
    stp = rect(strip_w, PLY, e_ply, gp)         # wide along z, thin along x
    for sx in (1, -1):
        a = 0 if sx > 0 else 180
        ys = sorted({Y_MB, Y_TR, *WEB_Y})
        sn = {y: fr.node(sx * STRIP_X, y, 0) for y in ys}
        for y0, y1 in zip(ys, ys[1:]):
            fr.beam(sn[y0], sn[y1], stp, ref=np.array([1, 0, 0.0]))
        jt = RIGID if strip_k is None else spring(strip_k, STRIP_X - R_RING)
        fr.beam(rings["board"][a], sn[Y_MB], jt)           # glued + screwed into the board edge (ASSUMED rigid)
        fr.beam(rings["top"][a], sn[Y_TR], jt)
        for y in WEB_Y:
            fr.fix(sn[y], (0, 1, 2, 3, 4, 5))                  # the D bearing is stiff and sits on its pads
        if web_ties:
            for y in (Y_MB, Y_TR):
                fr.fix(sn[y], (0, 1, 2, 3, 4, 5))
        masses += [(sn[y], strip_w * PLY * (Y_TR - Y_MB) * 0.024 / len(ys)) for y in ys]
    # --- stubs: 45 x 2.5 mm tubes through both boards, socket on top
    stub = tube(PP["mcage_tube_od"], PP["mcage_tube_wall"])
    lat = dict(E=E_AL, G=G_AL, A=50.0, Iy=50.0, Iz=1e-6, J=1e-6)      # hole bearing: sideways only
    for a, (x, z) in stub_xz.items():
        r = math.hypot(x, z)
        ys = [Y_MB, Y_TR, Y_TOP + PP["stub_proud"]]
        sn = [fr.node(x, y, z) for y in ys]
        fr.beam(sn[0], sn[1], stub); fr.beam(sn[1], sn[2], stub)
        fr.beam(sn[2], sock[a], RIGID if sock_k is None else spring(sock_k, tf.Y_BASE - ys[2]))
        for k, (kind, y) in enumerate((("board", Y_MB), ("top", Y_TR))):
            held = (stub_axial == "both") or (stub_axial == kind) or (stub_axial == "ring" and kind == "top")
            rn = rings[kind][a]
            if held:
                fr.beam(rn, sn[k], RIGID)
            else:
                lk = lat if hole_k is None else dict(spring(hole_k, abs(r - R_RING)), Iz=1e-6, J=1e-6)
                fr.beam(rn, sn[k], lk, ref=np.array([0, 1, 0.0]))   # radial link: stiff radially + tangentially
        masses += [(n, 0.0975 * math.pi * PP["mcage_tube_od"] * PP["mcage_tube_wall"] * (ys[-1] - ys[0]) / 3) for n in sn]
        if stub_brace and abs(x) > 1:
            fr.beam(sn[1], _strip_node(fr, 1 if x > 0 else -1), tube(0.75, 0.065))
    # --- cell on three studs through the mirror board
    for a in cell_angles:
        fr.beam(cell, rings["board"][a], RIGID)
    return fr, masses, ids


def spring(k, L):
    """Beam of length L whose axial and both shear stiffnesses equal k (lb/in)."""
    E = k * L
    I = L ** 2 / 12
    return dict(E=E, G=E, A=1.0, Iy=I, Iz=I, J=2 * I)


def _strip_node(fr, sx):
    for i, (x, y, z) in enumerate(fr.nodes):
        if abs(x - sx * STRIP_X) < 1e-6 and abs(y - WEB_Y[0]) < 1e-6 and abs(z) < 1e-6:
            return i
    raise KeyError


def _xz(r, a, y):
    x, z = pol(r, a)
    return x, y, z


def error_at(fr, masses, ids, alt):
    g = np.array([0, -math.sin(math.radians(alt)), -math.cos(math.radians(alt))])
    fr.loads = {}
    for nd, lb in masses:
        fr.load(nd, np.r_[lb * g, 0, 0, 0])
    u = fr.solve()
    m0 = np.array(fr.nodes[ids["mir"]])
    Fp = tf.F_P + u[ids["mir"], :3] + np.cross(u[ids["mir"], 3:6], tf.F_P - m0)   # focus carried by the mirror
    th = u[ids["cage"], 3:6]
    C = np.array(fr.nodes[ids["sec"]]) + u[ids["sec"], :3]
    n = tf.N0 + np.cross(th, tf.N0)
    Fr = Fp - 2 * np.dot(Fp - C, n) * n
    e = (Fr - np.array([tf.X_FOC, tf.Y_SEC, 0.0])) - u[ids["eyep"], :3]
    return np.array([0, e[1], e[2]]), e[0], u[ids["mir"]]


def sweep(label, **kw):
    fr, masses, ids = build(**kw)
    res = [error_at(fr, masses, ids, a) for a in (0, 30, 45, 60, 90)]
    errs = [r[0] for r in res]
    swing = np.linalg.norm(errs[0] - errs[-1]) * 25.4
    resid = max(np.linalg.norm(e - errs[2]) for e in errs) * 25.4
    tilt = max(np.linalg.norm(r[2][3:6] - res[2][2][3:6]) for r in res) * 206265
    shift = max(np.linalg.norm(r[2][:3] - res[2][2][:3]) for r in res) * 25.4
    print(f"{label:58s} drift 0->90 {swing:6.3f} mm | after 45 {resid:6.3f} mm | mirror tilt {tilt:5.1f}\" shift {shift:6.3f} mm")
    return resid


if __name__ == "__main__":
    print("residual = worst focal-plane error after collimating at 45 deg (mirror tilt/shift include the whole tube's")
    print("rigid motion on the bearings, so they are not collimation errors by themselves)")
    sweep("rigid box (truss_fe baseline)", box="rigid")
    sweep("as built: ply, spacers bolted, stubs held at the board")
    sweep("  ply E 0.9 Msi", e_ply=0.9e6)
    sweep("  spacers pinned (loose bolts)", spacer_ends="pinned")
    sweep("  stubs held axially at the top ring only", stub_axial="ring")
    sweep("  stubs pinned at both boards", stub_axial="both")
    sweep("  cell studs between the stubs (30/150/270)", cell_angles=(30, 150, 270))
    sweep("  cell studs 60 deg off (0/120/240)", cell_angles=(0, 120, 240))
    sweep("  studs between + 1/4 x 1.5 6061 ring under the board", cell_angles=(30, 150, 270), board_plate=(0.25, 1.5))
    sweep("  sockets on the stubs 20,000 lb/in", sock_k=20000)
    sweep("  realistic: sockets + holes + strip screws 20,000 lb/in", sock_k=20000, hole_k=20000, strip_k=20000)
