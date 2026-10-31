"""
Altitude D bearing + its joint to the mirror box, in-plane FE (plane stress, scikit-fem P2 triangles).

Question (Nick, 2026-10-31): the D only meets the box through the web overlap on the 3" side strip
(two 3/8" dowels + two 1/4" bolts). Is that enough?

What matters for a GoTo scope is not strength (loads are tens of lb) but how far the TUBE turns relative to
  * the drive pinion (windup: tracking error when the friction torque changes), and
  * the rim encoder read head (the encoder reads the rim, not the tube),
under gravity (altitude sweep) and per in-lb of drive torque. The box is held rigid at the fasteners (its own
flex is in mcage_fe.py); the strip's in-plane stiffness (3" deep, glued into both boards) is far above the
fastener springs and is treated as rigid.

Fastener stiffness (per fastener, in-plane):
  dowel 3/8" in birch ply: EC5 slip modulus Kser = rho^1.5 d / 23 (rho 680 kg/m^3) ~ 42,000 lb/in per shear plane
  1/4" bolt in a clearance hole: 0 once the clamp slips; while friction holds the clamped faces act like a
  bonded patch around the washer (modelled as springs to ground over a 1.25" circle, 1e6 lb/in total)
Run from goto-rebuild/:  python3 bearing_fe.py   (writes out/bearing_fe/report.json + plots)
"""
import json
import math
import os
import sys

import numpy as np
import triangle as tr
from shapely.geometry import Point, Polygon, box
from shapely.ops import unary_union
from skfem import Basis, BilinearForm, ElementTriP2, ElementVector, MeshTri, asm, solve, condense

import rocker

OUT = os.path.join("out", "bearing_fe")
os.makedirs(OUT, exist_ok=True)
P = json.load(open("out/params.json"))
G = P["rocker"]
PP = P["params"]
F = P["frame"]
R, E_CH = G["R"], G["chord_e"]
T_PLY = G["bearing_t"]                       # both layers laminated (glued) = 1.418"
E_PLY, NU, G_PLY = 1.3e6, 0.05, 0.11e6       # Baltic birch in-plane, cross-ply average (ASSUMED); panel shear 110 ksi
K_DOWEL = 42000.0
K_CLAMP = 1.0e6
TUBE_LB = P["checks"]["tube_weight_lb"]
W_PAD = TUBE_LB / 2                          # pad reaction per bearing (lb)
Y_BOX_TOP = F["y_mcage_top"]


def outline(fasteners, rib=0.0, windows=True, rim_w=None):
    """D bearing as a shapely polygon in the tube frame (Y along the tube, Z across), same as rocker.bearing_outline.
    rib > 0 adds a diagonal rib of that width across each window, from the web root to the rim/bar corner."""
    d = Point(0, 0).buffer(R, 256).intersection(box(-R - 1, -R - 1, E_CH, R + 1))
    r_in = R - (rim_w or G["rim_w"])
    if windows:
        for sz in (1, -1):
            clip = box(-r_in, G["web_w"] / 2, E_CH - G["bar_w"], r_in) if sz > 0 else \
                box(-r_in, -r_in, E_CH - G["bar_w"], -G["web_w"] / 2)
            d = d.difference(Point(0, 0).buffer(r_in, 256).intersection(clip))
    if rib:
        from shapely.geometry import LineString
        yb = E_CH - G["bar_w"]
        zc = math.sqrt(r_in ** 2 - yb ** 2)
        for sz in (1, -1):
            d = d.union(LineString([(-9.5, 0), (yb + 0.3, sz * (zc + 0.3))]).buffer(rib / 2, cap_style=2)
                        .intersection(Point(0, 0).buffer(R - 0.05, 256)))
    d = d.intersection(Point(0, 0).buffer(R, 256).intersection(box(-R - 1, -R - 1, E_CH, R + 1)))
    for f in fasteners:
        d = d.difference(Point(f["y"], f["z"]).buffer(f["d"] / 2, 24))
    return d


def mesh(poly, max_area=0.06):
    """Triangulate a polygon or MultiPolygon (disjoint parts), holes respected."""
    verts, segs, holes = [], [], []

    def add_ring(coords):
        coords = list(coords)[:-1]
        i0 = len(verts)
        verts.extend(coords)
        n = len(coords)
        segs.extend([(i0 + k, i0 + (k + 1) % n) for k in range(n)])
    for g in (poly.geoms if poly.geom_type == "MultiPolygon" else [poly]):
        add_ring(g.exterior.coords)
        for ring in g.interiors:
            add_ring(ring.coords)
            holes.append(Polygon(ring).representative_point().coords[0])
    A = dict(vertices=np.array(verts), segments=np.array(segs))
    if holes:
        A["holes"] = np.array(holes)
    B = tr.triangulate(A, f"pq30a{max_area}")
    return MeshTri(B["vertices"].T, B["triangles"].T)


# The box side the D bolts to, meshed as its own plane-stress part (18 mm ply), glued along its top and bottom edges to
# the top ring and the mirror board (held rigid: the box itself is in mcage_fe.py). It is meshed shifted by OFF in y.
OFF = 40.0
Y_PANEL_TOP = F["y_mcage_top"] - PP["ply"]      # top ring's underside (-6.34)
Y_PANEL_BOT = F["y_mcage_bot"] + PP["ply"]      # mirror board's top face (-17.72)
T_PANEL = PP["ply"]
STRIP = (-1.5, 1.5)                             # the existing 3" strip (z range)
WING = (-6.4, 1.5)                              # strip + new back wing out to the end of the board's flat (z -6.49, ASSUMED)


COLLAR_NOTCH = (-6.4, -4.1, 0.70)               # z range and depth of the wing's top-corner notch around the 330/210 deg stub's lower collar


def panel_poly(zr):
    p = box(Y_PANEL_BOT + OFF, zr[0], Y_PANEL_TOP + OFF, zr[1])
    if zr[0] < COLLAR_NOTCH[1]:
        p = p.difference(box(Y_PANEL_TOP + OFF - COLLAR_NOTCH[2], COLLAR_NOTCH[0] - 1, Y_PANEL_TOP + OFF + 1, COLLAR_NOTCH[1]))
    return p


D11 = E_PLY / (1 - NU ** 2)
D12 = NU * D11


@BilinearForm
def stiff(u, v, w):
    from skfem.helpers import sym_grad
    eu, ev = sym_grad(u), sym_grad(v)
    t = np.where(w.x[0] > OFF / 2, T_PANEL, T_PLY)
    return t * (D11 * (eu[0, 0] * ev[0, 0] + eu[1, 1] * ev[1, 1]) + D12 * (eu[0, 0] * ev[1, 1] + eu[1, 1] * ev[0, 0])
                    + 4 * G_PLY * eu[0, 1] * ev[0, 1])


FASTENERS = [dict(kind="dowel", y=-8.4, z=0.0, d=0.375), dict(kind="dowel", y=-13.2, z=0.0, d=0.375),
             dict(kind="bolt", y=-10.8, z=0.9, d=0.26), dict(kind="bolt", y=-10.8, z=-0.9, d=0.26)]


def rim_point(phi_r, alt, r=R):
    """Rocker-frame angle phi_r (from straight down, + toward the front) -> tube-frame (Y, Z) at altitude alt."""
    a = math.radians(phi_r - alt)
    return np.array([r * math.sin(a), -r * math.cos(a)]), np.array([math.cos(a), math.sin(a)])


class Model:
    def __init__(self, fasteners=FASTENERS, joint="clamped", poly=None, extra=(), panel=STRIP, **okw):
        from scipy.sparse import coo_matrix
        from shapely.geometry import MultiPolygon
        self.f = list(fasteners) + list(extra)
        self.poly = poly if poly is not None else outline(self.f, **okw)
        self.lb = self.poly.area * T_PLY * 0.0246          # Baltic birch ~ 680 kg/m^3
        self.panel = panel
        self.m = mesh(MultiPolygon([self.poly, panel_poly(panel)]) if panel else self.poly)
        self.ib = Basis(self.m, ElementVector(ElementTriP2()))
        K = asm(stiff, self.ib)
        p = self.m.p
        nd = self.ib.nodal_dofs                      # (2, n_vertices)
        self.isD = p[0] < OFF / 2
        self.springs = []
        rows, cols, vals = [], [], []
        for f in self.f:
            dist = np.hypot(p[0] - f["y"], p[1] - f["z"])
            distP = np.hypot(p[0] - f["y"] - OFF, p[1] - f["z"])
            if f["kind"] == "dowel":
                r, k = f["d"] / 2 + 0.02, K_DOWEL
            elif joint == "clamped":
                r, k = 0.625, K_CLAMP
            else:
                continue
            sel = np.where((dist < max(r, 0.3)) & self.isD)[0]
            selP = np.where((distP < max(r, 0.3)) & ~self.isD)[0] if panel else np.array([], int)
            if panel and len(selP) == 0:
                raise ValueError(f"fastener at {f['y']},{f['z']} is off the panel")
            for c in (0, 1):
                idx = list(nd[c, sel]) + list(nd[c, selP])
                a = np.r_[np.full(len(sel), 1 / len(sel)), np.full(len(selP), -1 / len(selP)) if len(selP) else []]
                for ii, ai in zip(idx, a):
                    for jj, aj in zip(idx, a):
                        rows.append(ii); cols.append(jj); vals.append(k * ai * aj)
            self.springs.append((f, sel, selP, k))
        n = K.shape[0]
        self.K = (K + coo_matrix((vals, (rows, cols)), shape=(n, n))).tocsr()
        self.nd = nd
        # fixed: the panel's glued top and bottom edges
        fixed = []
        if panel:
            edge = (~self.isD) & ((np.abs(p[0] - (Y_PANEL_TOP + OFF)) < 1e-6) | (np.abs(p[0] - (Y_PANEL_BOT + OFF)) < 1e-6))
            vs = np.where(edge)[0]
            fixed = list(nd[0, vs]) + list(nd[1, vs])
            # P2 edge dofs on those facets too
            fac = self.m.boundary_facets()
            mids = self.m.p[:, self.m.facets[:, fac]].mean(axis=1)
            on = ((np.abs(mids[0] - (Y_PANEL_TOP + OFF)) < 1e-6) | (np.abs(mids[0] - (Y_PANEL_BOT + OFF)) < 1e-6))
            fixed += list(self.ib.facet_dofs[:, fac[on]].ravel())
        self.fixed = np.array(sorted(set(fixed)), int)

    def nearest(self, yz):
        return int(np.argmin(np.hypot(self.m.p[0] - yz[0], self.m.p[1] - yz[1])))

    def boundary_near(self, yz, half_len):
        """outer-boundary vertices within half_len (arc) of a rim point."""
        bv = np.unique(self.m.facets[:, self.m.boundary_facets()])
        p = self.m.p[:, bv]
        rr = np.hypot(p[0], p[1])
        ok = (np.abs(rr - R) < 0.02) & (np.hypot(p[0] - yz[0], p[1] - yz[1]) < half_len)
        return bv[ok]

    def solve(self, loads):
        """loads = [(yz, force_vec, spread)] ; returns displacement (2, nverts)."""
        Fv = np.zeros(self.K.shape[0])
        for yz, fv, spread in loads:
            vs = self.boundary_near(yz, spread) if spread else [self.nearest(yz)]
            if len(vs) == 0:
                vs = [self.nearest(yz)]
            for v in vs:
                for c in (0, 1):
                    Fv[self.nd[c, v]] += fv[c] / len(vs)
        if len(self.fixed):
            u = solve(*condense(self.K, Fv, D=self.fixed))
        else:
            u = solve(self.K, Fv)
        self.u = u
        return np.vstack([u[self.nd[0]], u[self.nd[1]]])

    def tangential(self, U, phi_r, alt):
        yz, t = rim_point(phi_r, alt)
        vs = self.boundary_near(yz, 0.6)
        if len(vs) == 0:
            vs = [self.nearest(yz)]
        return float(np.mean([U[:, v] @ t for v in vs]))

    def spring_forces(self, U):
        out = []
        for f, sel, selP, k in self.springs:
            fv = k * (U[:, sel].mean(axis=1) - (U[:, selP].mean(axis=1) if len(selP) else 0))
            out.append((f["kind"], f["y"], f["z"], float(np.hypot(*fv))))
        return out


def pad_loads(alt, w=W_PAD, pad=G["pad_angle"]):
    """Pad normal reactions on the rim (toward the axis) for altitude alt: two pads at +/-pad from straight down."""
    n = w / (2 * math.cos(math.radians(pad)))
    out = []
    for ph in (pad, -pad):
        yz, t = rim_point(ph, alt)
        if yz[0] > E_CH + 1e-6:          # pad past the straight edge (below alt_min)
            continue
        out.append((yz, -n * yz / R, 0.8))
    return out


def drive_loads(alt, torque=1.0):
    """Unit drive torque (in-lb) applied by the pinion at the bottom of the rim (phi_r = 0), tangential."""
    yz, t = rim_point(0, alt)
    return [(yz, torque / R * t, 0.3)]


AS = 206264.8


def sweep(model, alts=(15, 30, 45, 60, 75, 90)):
    rows = []
    for a in alts:
        Ug = model.solve(pad_loads(a))
        g_pin = model.tangential(Ug, 0, a) / R * AS
        g_enc = model.tangential(Ug, G["alt_head_angle"], a) / R * AS
        Ud = model.solve(drive_loads(a, 1.0))
        d_pin = model.tangential(Ud, 0, a) / R * AS
        d_enc = model.tangential(Ud, G["alt_head_angle"], a) / R * AS
        fmax = max(f[3] for f in model.spring_forces(Ug))
        rows.append(dict(alt=a, grav_pinion_as=g_pin, grav_encoder_as=g_enc, drive_pinion_as_per_inlb=d_pin,
                         drive_encoder_as_per_inlb=d_enc, fastener_max_lb=fmax))
    return rows


def show(label, rows, model=None):
    print(f"\n{label}" + (f"   [{model.lb:.2f} lb per D]" if model else ""))
    print("  alt  grav@pinion  grav@enc   windup@pinion  windup@enc    max fastener")
    for r in rows:
        print(f"  {r['alt']:3d}  {r['grav_pinion_as']:8.2f}\"  {r['grav_encoder_as']:8.2f}\"   "
              f"{r['drive_pinion_as_per_inlb']:7.4f}\"/in-lb {r['drive_encoder_as_per_inlb']:7.4f}\"/in-lb  {r['fastener_max_lb']:6.1f} lb")
    gp = [r["grav_pinion_as"] for r in rows]
    print(f"  gravity: tube vs pinion moves {max(gp) - min(gp):.2f}\" over the sweep (repeatable -> pointing model)")
    w = max(abs(r["drive_pinion_as_per_inlb"]) for r in rows)
    print(f"  windup: worst {w:.4f}\"/in-lb -> {w * 170:.1f}\" at 170 in-lb, +/-{w * 35:.1f}\" for a +/-35 in-lb friction swing")


def plot(model, U, title, path, scale=None):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from matplotlib.tri import Triangulation
    p, t = model.m.p, model.m.t
    tD = t[:, model.isD[t].all(axis=0)]
    tP = t[:, (~model.isD)[t].all(axis=0)]
    mag = np.hypot(U[0], U[1])
    s = scale or 1.5 / max(mag[model.isD].max(), 1e-12)
    fig, ax = plt.subplots(figsize=(6.5, 7.5))
    if tP.size:      # the box side the D bolts to (behind it), deformed, in red
        ax.tripcolor(Triangulation(p[1] + s * U[1], p[0] - OFF + s * U[0], tP.T), np.zeros(tP.shape[1]),
                     cmap="Reds", vmin=-4, vmax=1, alpha=0.6)
        z0, z1 = model.panel
        ax.text(z1 + 0.2, Y_PANEL_BOT + 0.4, "box side\n(behind)", color="#c33", fontsize=8)
    ax.triplot(Triangulation(p[1], p[0], tD.T), lw=0.15, color="#bbb")
    tri = Triangulation(p[1] + s * U[1], p[0] + s * U[0], tD.T)
    tc = ax.tripcolor(tri, mag * 1e3, shading="gouraud", cmap="viridis", vmax=mag[model.isD].max() * 1e3)
    fig.colorbar(tc, ax=ax, label="displacement (thou)", shrink=0.6)
    ax.axhline(Y_BOX_TOP, color="#c33", lw=1, ls="--")
    ax.text(-14, Y_BOX_TOP + 0.3, "box top ring", color="#c33", fontsize=8)
    ax.axhline(F["y_mcage_bot"] + PP["ply"], color="#c33", lw=1, ls="--")
    for f in model.f:
        ax.add_patch(plt.Circle((f["z"], f["y"]), f["d"] / 2, fill=f["kind"] == "dowel", color="k", lw=0.8))
    ax.set_xlim(-15.5, 15.5); ax.set_ylim(-19, 5.5)
    ax.set_aspect("equal"); ax.set_xlabel("across the tube (in), + = toward the shield point")
    ax.set_ylabel("along the tube from the altitude axis (in)")
    ax.set_title(title + f"\n(deformation ×{s:.0f})", fontsize=10)
    fig.tight_layout(); fig.savefig(path, dpi=130); plt.close(fig)


def onrim(z, r=None):
    r = r or R - G["rim_w"] / 2
    return -math.sqrt(r * r - z * z)


def _D(y, z):
    return dict(kind="dowel", y=round(y, 3), z=round(z, 3), d=0.375)


def _B(y, z):
    return dict(kind="bolt", y=round(y, 3), z=round(z, 3), d=0.26)


# Chosen 2026-10-31: the strip plus a new back wing (one 18 mm side panel z -6.4..+1.5, between the boards), the D on
# two 3/8 dowels as far apart as the panel allows and six 1/4-20 bolts into threaded inserts in the panel.
WING_FASTENERS = [_D(onrim(-5.6), -5.6), _D(-7.0, 0.9),
                  _B(-7.2, -0.9), _B(-10.0, 0.9), _B(-10.0, -0.9), _B(-12.6, -1.0), _B(-13.2, 0.9),
                  _B(onrim(-3.8), -3.8)]


def main():
    res = {}
    cases = [("as_drawn_clamped", "AS DRAWN (3\" strip, 2 dowels + 2 bolts), bolts tight", dict(joint="clamped")),
             ("as_drawn_slipped", "AS DRAWN, bolts slipped (dowels only)", dict(joint="slipped")),
             ("wing_clamped", "SIDE PANEL (strip + back wing), 2 dowels + 6 bolts tight",
              dict(joint="clamped", fasteners=WING_FASTENERS, panel=WING)),
             ("wing_slipped", "SIDE PANEL, bolts slipped (dowels only)",
              dict(joint="slipped", fasteners=WING_FASTENERS, panel=WING))]
    models = {}
    for key, label, kw in cases:
        m = Model(**kw)
        models[key] = m
        rows = sweep(m)
        show(label, rows, m)
        U = m.solve([(yz, 3 * f, s) for yz, f, s in pad_loads(15)])
        fz = m.spring_forces(U)
        print("  3 g at 15 deg, fastener loads (lb):", [round(x[3]) for x in fz])
        res[key] = dict(rows=rows, shock_3g_fastener_lb=fz)
    json.dump(res, open(os.path.join(OUT, "report.json"), "w"), indent=1)
    a, b = models["as_drawn_clamped"], models["wing_clamped"]
    Ua = a.solve(drive_loads(15, 170)); Ub = b.solve(drive_loads(15, 170))
    sc = 1.5 / np.hypot(*Ua)[a.isD].max()
    plot(a, Ua, "170 in-lb drive torque at 15° altitude, as drawn, bolts tight", os.path.join(OUT, "windup_15deg.png"), sc)
    plot(b, Ub, "Same load, D on the side panel (strip + back wing)", os.path.join(OUT, "windup_15deg_side_panel.png"), sc)
    from PIL import Image
    ia, ib_ = Image.open(os.path.join(OUT, "windup_15deg.png")), Image.open(os.path.join(OUT, "windup_15deg_side_panel.png"))
    w = Image.new("RGB", (ia.width + ib_.width, max(ia.height, ib_.height)), "white")
    w.paste(ia, (0, 0)); w.paste(ib_, (ia.width, 0))
    w.save(os.path.join(OUT, "compare_windup.png"))


def plots_only():
    a = Model(joint="clamped")
    b = Model(joint="clamped", fasteners=WING_FASTENERS, panel=WING)
    Ua = a.solve(drive_loads(15, 170)); Ub = b.solve(drive_loads(15, 170))
    sc = 1.5 / np.hypot(*Ua)[a.isD].max()
    plot(a, Ua, "170 in-lb drive torque at 15° altitude, as drawn, bolts tight", os.path.join(OUT, "windup_15deg.png"), sc)
    plot(b, Ub, "Same load, D on the side panel (strip + back wing)", os.path.join(OUT, "windup_15deg_side_panel.png"), sc)
    from PIL import Image
    ia, ib_ = Image.open(os.path.join(OUT, "windup_15deg.png")), Image.open(os.path.join(OUT, "windup_15deg_side_panel.png"))
    w = Image.new("RGB", (ia.width + ib_.width, max(ia.height, ib_.height)), "white")
    w.paste(ia, (0, 0)); w.paste(ib_, (ia.width, 0))
    w.save(os.path.join(OUT, "compare_windup.png"))


if __name__ == "__main__":
    plots_only() if "plots" in sys.argv else main()
