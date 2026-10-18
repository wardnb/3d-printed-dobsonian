"""
3D frame finite-element check of the upper cage's collimation hold.

Everything in inches and pounds. Cage frame as in upper_cage.py: tube axis +Y toward
the sky, focuser on -X, altitude axis along X (so gravity always lies in the Y-Z plane).

Model
  * each ring = two concentric "lands" (inner / outer) of beam elements, tied by rigid
    ribs wherever the ring is solid; in the lightening-slot zones there are no ribs, so
    the slotted ring behaves as the Vierendeel it really is
  * 4 posts, 2 board rails, rigid focuser board hung on its 3 push-pull points, rigid
    hub tied to the posts by the 8 spider wires (EA bars), finder + bracket as a mass
    on a rigid arm, truss apexes pinned (translations fixed) at 0/120/240 on the lower ring
  * loads: self weight + focuser/eyepiece/Paracorr, gravity rotated through the altitude
    range; result = where the primary's focus lands on the eyepiece's axis, i.e. the
    collimation error at the focal plane, as a function of altitude
"""
import math
import numpy as np

import upper_cage as uc

E_AL, G_AL = 10.0e6, 3.8e6
E_W = 28.0e6                                  # steel wire
R_C = uc.R_BOLT                               # ring centroid radius (9.5)
T = uc.T
GAP = uc.I["ring_gap"]                        # 7.5 between ring inner faces
Y_LO, Y_HI = -(GAP / 2 + T / 2), (GAP / 2 + T / 2)   # ring mid-planes
RIGID = dict(E=E_AL, G=G_AL, A=50.0, Iy=50.0, Iz=50.0, J=50.0)


def rect_props(b, h):
    """b x h rectangle: Iy about the b-axis... we return (A, I_b, I_h, J)."""
    A = b * h
    I_h = b * h ** 3 / 12          # bending that flexes the h dimension
    I_b = h * b ** 3 / 12
    a, c = max(b, h), min(b, h)
    J = a * c ** 3 * (1 / 3 - 0.21 * c / a * (1 - c ** 4 / (12 * a ** 4)))
    return A, I_b, I_h, J


class Frame:
    def __init__(self):
        self.nodes = []
        self.elems = []
        self.loads = {}
        self.fixed = {}

    def node(self, x, y, z):
        self.nodes.append((x, y, z))
        return len(self.nodes) - 1

    def beam(self, i, j, props, ref=None):
        self.elems.append((i, j, props, ref))

    def load(self, n, f):
        self.loads[n] = self.loads.get(n, np.zeros(6)) + np.asarray(f, float)

    def fix(self, n, dofs=(0, 1, 2)):
        self.fixed[n] = dofs

    @staticmethod
    def k_local(L, E, G, A, Iy, Iz, J):
        k = np.zeros((12, 12))
        a = E * A / L
        k[0, 0] = k[6, 6] = a; k[0, 6] = k[6, 0] = -a
        t = G * J / L
        k[3, 3] = k[9, 9] = t; k[3, 9] = k[9, 3] = -t
        for (I, i1, i2, s) in ((Iz, 1, 5, 1), (Iy, 2, 4, -1)):
            c1, c2, c3, c4 = 12 * E * I / L ** 3, 6 * E * I / L ** 2 * s, 4 * E * I / L, 2 * E * I / L
            idx = [i1, i2, i1 + 6, i2 + 6]
            kk = np.array([[c1, c2, -c1, c2],
                           [c2, c3, -c2, c4],
                           [-c1, -c2, c1, -c2],
                           [c2, c4, -c2, c3]])
            for p in range(4):
                for q in range(4):
                    k[idx[p], idx[q]] += kk[p, q]
        return k

    def solve(self):
        n = len(self.nodes)
        K = np.zeros((6 * n, 6 * n))
        for i, j, pr, ref in self.elems:
            xi, xj = np.array(self.nodes[i]), np.array(self.nodes[j])
            d = xj - xi
            L = np.linalg.norm(d)
            ex = d / L
            if ref is None:
                ref = np.array([0, 1, 0.0]) if abs(ex[1]) < 0.9 else np.array([1, 0, 0.0])
            ez = np.cross(ex, ref); ez /= np.linalg.norm(ez)
            ey = np.cross(ez, ex)
            R = np.vstack([ex, ey, ez])
            Tm = np.zeros((12, 12))
            for b in range(4):
                Tm[3 * b:3 * b + 3, 3 * b:3 * b + 3] = R
            k = Tm.T @ self.k_local(L, pr["E"], pr["G"], pr["A"], pr["Iy"], pr["Iz"], pr["J"]) @ Tm
            dofs = list(range(6 * i, 6 * i + 6)) + list(range(6 * j, 6 * j + 6))
            K[np.ix_(dofs, dofs)] += k
        F = np.zeros(6 * n)
        for nd, f in self.loads.items():
            F[6 * nd:6 * nd + 6] += f
        free = np.ones(6 * n, bool)
        for nd, dofs in self.fixed.items():
            for d in dofs:
                free[6 * nd + d] = False
        # tiny rotational springs on every node keep unused rotational dofs from being singular
        K[np.diag_indices_from(K)] += 1e-6
        u = np.zeros(6 * n)
        u[free] = np.linalg.solve(K[free][:, free], F[free])
        return u.reshape(n, 6)


SENSES = dict(same={a: (+1, -1) for a in uc.STRUTS},
              alt={45: (+1, -1), 135: (-1, +1), 225: (+1, -1), 315: (-1, +1)},
              paired={45: (+1, +1), 135: (-1, -1), 225: (+1, +1), 315: (-1, -1)})


def build(ring_t=T, ring_w=1.5, slotted=True, apex="pinned", wire_dia=0.025,
          focuser_lb=6.0, focuser_arm=3.5, E_ring=E_AL, G_ring=G_AL, rigid_wires=False,
          y_anchor=(6.025, 0.9), rims=(3.11, 5.75), senses="paired", cross=True, offset=50,
          stud_tang=0.15, v1_layout=False, sec_cg=0.9, diagonals=False, spider="wire"):
    """y_anchor = (high anchor y, low anchor y) on the posts (above the upper ring = on a
    post extension block); rims = (hub low rim y, hub high rim y); cross: high anchor ->
    low rim and low anchor -> high rim; senses: which side of the hub each post's wires
    land on (see SENSES); offset: degrees round the hub from the post direction."""
    if v1_layout:
        y_anchor, rims, senses, cross, offset, stud_tang = (3.5, 0.9), (2.76, 3.86), "same", True, 90, 0.0
    S = SENSES[senses]
    fr = Frame()
    r_in_c, r_out_c = R_C - ring_w / 2, R_C + ring_w / 2
    land_w = 0.45 if slotted else ring_w / 2
    # land centroid radii
    r_li = r_in_c + land_w / 2
    r_lo = r_out_c - land_w / 2
    A, I_b, I_h, J = rect_props(land_w, ring_t)     # land: radial width x thickness
    land = dict(E=E_ring, G=G_ring, A=A, Iy=I_b, Iz=I_h, J=J)   # see ref vector below
    # slot zones from upper_cage (per ring kind)
    zones = {}
    for kind in ("lower", "upper"):
        holes = uc.ring_holes(kind)
        slots, rc, w = uc.lightening_slots(holes)
        zones[kind] = slots if slotted else []

    def in_slot(kind, a):
        return any(a0 <= a <= a1 for a0, a1 in zones[kind])

    feature_angles = set(uc.STRUTS) | set(uc.TOPS) | {uc.FINDER}
    rail_angles = [uc.ang_of(uc.RAIL_X, z) for z in (uc.RAIL_Z, -uc.RAIL_Z)]
    feature_angles |= set(round(a, 3) for a in rail_angles)
    grid = set(np.round(np.arange(0, 360, 3.0), 3)) | feature_angles
    angles = sorted(grid)
    rings = {}
    for kind, y in (("lower", Y_LO), ("upper", Y_HI)):
        inner, outer, centre = {}, {}, {}
        for a in angles:
            x, z = uc.pol(r_li, a); inner[a] = fr.node(x, y, z)
            x, z = uc.pol(r_lo, a); outer[a] = fr.node(x, y, z)
            x, z = uc.pol(R_C, a); centre[a] = fr.node(x, y, z)
        for k, a in enumerate(angles):
            b = angles[(k + 1) % len(angles)]
            for ring_nodes in (inner, outer):
                fr.beam(ring_nodes[a], ring_nodes[b], land, ref=np.array([0, 1, 0.0]))
            am = (a + (b if b > a else b + 360)) / 2 % 360
            # rib (solid ring) wherever this arc is not inside a slot
            if not in_slot(kind, am) or a in feature_angles:
                fr.beam(inner[a], centre[a], RIGID); fr.beam(centre[a], outer[a], RIGID)
            else:
                # keep the centre node attached (rigid to inner land) so masses can hang on it
                fr.beam(inner[a], centre[a], RIGID)
        # also always tie at the node itself when that node is in a solid zone
        for a in angles:
            if not in_slot(kind, a):
                fr.beam(centre[a], outer[a], RIGID)
        rings[kind] = dict(inner=inner, outer=outer, centre=centre)

    # ring self weight (slots already reflected in the fit report weights)
    wt = dict(lower=1.59, upper=1.71) if slotted else dict(lower=2.18, upper=2.18)
    wt = {k: v * (ring_t / T) * (ring_w / 1.5) for k, v in wt.items()}
    masses = []            # (node, lb)
    for kind in ("lower", "upper"):
        per = wt[kind] / len(angles)
        for a in angles:
            masses.append((rings[kind]["centre"][a], per))

    # posts between the rings, with nodes at the wire anchor heights
    Ap, Ib, Ih, Jp = rect_props(uc.STRUT_SQ, uc.STRUT_SQ)
    post = dict(E=E_AL, G=G_AL, A=Ap, Iy=Ib, Iz=Ih, J=Jp)
    post_nodes = {}
    for a in uc.STRUTS:
        x, z = uc.pol(R_C, a)
        ys = sorted({Y_LO, Y_HI, *y_anchor, -3.0, -1.5, 0.0, 1.5, 3.0, uc.quad_spider.__defaults__ and round(uc.y_hi_in - 0.05 - uc.QUAD_VANE["h"] / 2, 3)})
        ns = []
        for y in ys:
            if y == Y_LO:
                ns.append(rings["lower"]["centre"][a])
            elif y == Y_HI:
                ns.append(rings["upper"]["centre"][a])
            else:
                ns.append(fr.node(x, y, z))
        Ae, Ibe, Ihe, Je = rect_props(uc.EXT_RAD, uc.STRUT_SQ)
        ext = dict(E=E_AL, G=G_AL, A=Ae, Iy=Ibe, Iz=Ihe, J=Je)
        for i in range(len(ns) - 1):
            fr.beam(ns[i], ns[i + 1], post if ys[i] < Y_HI else ext, ref=np.array([x, 0, z]) / R_C)
        post_nodes[a] = dict(zip(ys, ns))
        inner = [n for y, n in zip(ys, ns) if y not in (Y_LO, Y_HI)]
        for nd in inner:
            masses.append((nd, 1.65 / 4 / len(inner)))

    if diagonals:   # 1/2" round 6061 diagonals: lower-ring apex -> upper-ring post, 4 off
        Ad = math.pi * 0.25 ** 2; Id = math.pi * 0.5 ** 4 / 64
        diag = dict(E=E_AL, G=G_AL, A=Ad, Iy=Id, Iz=Id, J=2 * Id)
        for lo_a, hi_a in ((0, 45), (0, 315), (120, 135), (240, 225)):
            fr.beam(rings["lower"]["centre"][lo_a], rings["upper"]["centre"][hi_a], diag)
            masses.append((rings["upper"]["centre"][hi_a], 0.0975 * Ad * 11.0))

    # rails
    Ar, Ibr, Ihr, Jr = rect_props(0.5, 0.75)
    rail = dict(E=E_AL, G=G_AL, A=Ar, Iy=Ibr, Iz=Ihr, J=Jr)
    pp_y = sorted({p[0] - 0.3 for p in uc.PP})          # -3.3, 2.7 (pull hole positions)
    rail_nodes = {}
    for z in (uc.RAIL_Z, -uc.RAIL_Z):
        a = round(uc.ang_of(uc.RAIL_X, z), 3)
        ys = sorted({Y_LO, Y_HI, *pp_y, 0.0})
        ns = [rings["lower"]["centre"][a]] + [fr.node(uc.RAIL_X, y, z) for y in ys[1:-1]] + [rings["upper"]["centre"][a]]
        for i in range(len(ns) - 1):
            fr.beam(ns[i], ns[i + 1], rail, ref=np.array([1, 0, 0.0]))
        rail_nodes[z] = dict(zip(ys, ns))
        for nd in ns[1:-1]:
            masses.append((nd, 0.55 / 2 / (len(ns) - 2)))

    # rigid focuser board on its 3 push-pull points; focuser + eyepiece mass outboard
    xb = -(uc.R_IN + T / 2)
    board = fr.node(xb, 0, 0)
    for (yy, zz) in uc.PP:
        fr.beam(board, rail_nodes[zz][yy - 0.3], RIGID)
    foc = fr.node(xb - focuser_arm, 0, 0)
    fr.beam(board, foc, RIGID)
    eyep = fr.node(xb - 2.65, 0, 0)                       # focal plane centre on the eyepiece axis
    fr.beam(board, eyep, RIGID)
    masses += [(board, 1.0), (foc, focuser_lb)]

    r_face = R_C - uc.STRUT_SQ / 2
    if spider == "quad":
        # straight 4-vane spider: 0.020 x 1.5 stainless vanes from a 2.6" hub to the towers on the upper ring
        qp = uc.quad_spider()[1]
        y_c, hub_top = qp["vane_centre_y"], qp["hub_top_y"]
        hub_r = uc.QUAD_HUB_DIA / 2
        hub = fr.node(0, (2.66 + hub_top) / 2, 0)
        sec = fr.node(0, 0.0, 0); cg = fr.node(0, sec_cg, 0)
        fr.beam(hub, sec, RIGID); fr.beam(hub, cg, RIGID)
        masses += [(hub, 0.45), (cg, 1.6)]
        Av, Ib, Ih, Jv = rect_props(uc.QUAD_VANE["t"], uc.QUAD_VANE["h"])
        vane = dict(E=29e6, G=11e6, A=Av, Iy=Ib, Iz=Ih, J=Jv)
        r_in = uc.QUAD_HUB_BORE / 2 + 0.05
        for a in uc.STRUTS:
            hx, hz = uc.pol(r_in, a); prev = fr.node(hx, y_c, hz); fr.beam(hub, prev, RIGID)
            for s in np.linspace(0, 1, 7)[1:]:
                r = r_in + (r_face - r_in) * s
                px, pz = uc.pol(r, a); nd = fr.node(px, y_c, pz)
                fr.beam(prev, nd, vane, ref=np.array([0, 1, 0.0])); prev = nd
            fr.beam(prev, post_nodes[a][y_c], RIGID)      # stud through the post at vane height
        # finder
        fx, fz = uc.pol(uc.R_OUT + 2.85, uc.FINDER)
        fn = fr.node(fx, Y_HI - 4.0, fz)
        fr.beam(rings["upper"]["centre"][uc.FINDER], fn, RIGID)
        masses.append((fn, 1.7))
        for a in uc.TOPS:
            nd = rings["lower"]["centre"][a]
            fr.fix(nd, (0, 1, 2) if apex == "pinned" else (0, 1, 2, 3, 4, 5))
        return fr, masses, dict(board=board, eyep=eyep, hub=hub, sec=sec, foc=foc)

    # hub + secondary, hung on the 8 wires
    hub_r = 1.2
    hub = fr.node(0, (rims[0] + rims[1]) / 2, 0)
    sec = fr.node(0, 0.0, 0)                              # secondary centre (reference point)
    cg = fr.node(0, sec_cg, 0)                            # secondary + carrier + body CG
    fr.beam(hub, sec, RIGID); fr.beam(hub, cg, RIGID)
    masses += [(hub, 0.5), (cg, 1.3)]
    Aw = math.pi * wire_dia ** 2 / 4
    wire = dict(E=E_W, G=E_W / 2.6, A=Aw, Iy=1e-9, Iz=1e-9, J=1e-9)
    if rigid_wires:
        wire = RIGID
    r_face = R_C - uc.STRUT_SQ / 2
    for a in uc.STRUTS:
        tx, tz = uc.pol(1.0, a + 90)
        pairs = ((y_anchor[0], rims[0] if cross else rims[1], +stud_tang, S[a][0]),
                 (y_anchor[1], rims[1] if cross else rims[0], -stud_tang, S[a][1]))
        for y_a, y_h, tg, sense in pairs:
            hx, hz = uc.pol(hub_r, a + sense * offset)
            nh = fr.node(hx, y_h, hz); fr.beam(hub, nh, RIGID)
            px, pz = uc.pol(r_face if y_a < Y_HI else R_C - uc.EXT_RAD / 2, a)
            npn = fr.node(px + tg * tx, y_a, pz + tg * tz); fr.beam(post_nodes[a][y_a], npn, RIGID)
            fr.beam(npn, nh, wire)

    # Waypoint finder + bracket: 1.7 lb at ~3" outboard, 4" below the upper ring
    fx, fz = uc.pol(uc.R_OUT + 2.85, uc.FINDER)
    fn = fr.node(fx, Y_HI - 4.0, fz)
    fr.beam(rings["upper"]["centre"][uc.FINDER], fn, RIGID)
    masses.append((fn, 1.7))

    # truss apexes
    for a in uc.TOPS:
        nd = rings["lower"]["centre"][a]
        fr.fix(nd, (0, 1, 2) if apex == "pinned" else (0, 1, 2, 3, 4, 5))
    return fr, masses, dict(board=board, eyep=eyep, hub=hub, sec=sec, foc=foc)


def collimation_error(fr, masses, ids, alt_deg):
    """Gravity at altitude alt (deg above horizon): g = (0, -sin, -cos) in the cage frame."""
    g = np.array([0, -math.sin(math.radians(alt_deg)), -math.cos(math.radians(alt_deg))])
    fr.loads = {}
    for nd, lb in masses:
        fr.load(nd, np.r_[lb * g, 0, 0, 0])
    u = fr.solve()
    # secondary plane: through sec, front normal n0 = (-1,-1,0)/sqrt2 ; rotation = hub rotation
    th = u[ids["hub"], 3:6]
    C = np.array(fr.nodes[ids["sec"]]) + u[ids["sec"], :3]
    n0 = np.array([-1, -1, 0]) / math.sqrt(2)
    n = n0 + np.cross(th, n0)
    Fp = np.array([0, 11.9, 0])                      # primary's focus, rigid to the apexes
    F = Fp - 2 * np.dot(Fp - C, n) * n
    F0 = np.array([-11.9, 0, 0])
    dF = F - F0
    d_eye = u[ids["eyep"], :3]
    e = dF - d_eye
    lateral = np.array([0, e[1], e[2]])              # perpendicular to the focuser axis (X)
    return dict(alt=alt_deg, err_in=lateral, err_mm=np.linalg.norm(lateral) * 25.4,
                focus_shift_mm=e[0] * 25.4, hub_mm=u[ids["sec"], :3] * 25.4,
                board_mm=u[ids["board"], :3] * 25.4, board_tilt_mrad=u[ids["board"], 3:6] * 1e3,
                hub_tilt_mrad=th * 1e3)


def sweep(label, **kw):
    fr, masses, ids = build(**kw)
    res = [collimation_error(fr, masses, ids, a) for a in (0, 30, 45, 60, 90)]
    errs = np.array([r["err_in"] for r in res])
    swing = np.linalg.norm(errs[0] - errs[-1]) * 25.4
    # collimate at 45 deg: residual elsewhere
    resid = max(np.linalg.norm(e - errs[2]) * 25.4 for e in errs)
    print(f"{label:38s} swing 0->90: {swing:5.3f} mm | max residual after collimating at 45: {resid:5.3f} mm"
          f" | hub sag @0: {np.linalg.norm(res[0]['hub_mm']):.3f} mm, @90: {np.linalg.norm(res[-1]['hub_mm']):.3f} mm"
          f" | board tilt @0: {np.linalg.norm(res[0]['board_tilt_mrad']):.3f} mrad")
    return res


if __name__ == "__main__":
    import sys
    which = sys.argv[1] if len(sys.argv) > 1 else "quad"
    if which == "quad":
        sweep("QUAD spider, 3/8 solid rings, 3.5in secondary", slotted=False, ring_t=0.375, spider="quad")
        sweep("QUAD spider, 1/4 solid rings", slotted=False, ring_t=0.25, spider="quad")
        sweep("QUAD spider, 3/8 rings, 8 lb focuser", slotted=False, ring_t=0.375, spider="quad", focuser_lb=8.0)
