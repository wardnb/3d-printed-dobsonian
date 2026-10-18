"""Wire-spider geometry study with the full 6-DOF hub (twist coupling included).
Posts are taken as rigid here; the cage's own contribution comes from cage_fe.py."""
import math
import numpy as np
from cage_fe import Frame, RIGID, E_W
import upper_cage as uc

W_HUB = 1.8          # lb: secondary + carrier + body + hub
F_P = np.array([0, 11.4, 0.0])
N0 = np.array([-1, -1, 0]) / math.sqrt(2)


def hub_model(senses, y_anchor=(3.5, 0.9), hub_y=(2.66, 1.3), hub_r=1.2, wire_dia=0.025, offset=90):
    """senses[a] = (sense of the hi-anchor wire, sense of the lo-anchor wire) for post angle a."""
    Aw = math.pi * wire_dia ** 2 / 4
    wire = dict(E=E_W, G=E_W / 2.6, A=Aw, Iy=1e-9, Iz=1e-9, J=1e-9)
    hub_y0, hub_h = hub_y
    y_hub_lo, y_hub_hi = hub_y0 + 0.1, hub_y0 + hub_h - 0.1
    fr = Frame()
    hub = fr.node(0, hub_y0 + hub_h / 2, 0)
    sec = fr.node(0, 0, 0); fr.beam(hub, sec, RIGID)
    r_face = uc.R_BOLT - uc.STRUT_SQ / 2
    dirs = []
    for a in uc.STRUTS:
        s_hi, s_lo = senses[a]
        for y_a, y_h, s in ((y_anchor[0], y_hub_lo, s_hi), (y_anchor[1], y_hub_hi, s_lo)):
            hx, hz = uc.pol(hub_r, a + s * offset)
            nh = fr.node(hx, y_h, hz); fr.beam(hub, nh, RIGID)
            px, pz = uc.pol(r_face, a)
            npn = fr.node(px, y_a, pz); fr.fix(npn, (0, 1, 2, 3, 4, 5))
            fr.beam(npn, nh, wire)
            dirs.append(round(math.degrees(math.atan2(pz - hz, px - hx)) % 180, 1))
    return fr, hub, sec, sorted(set(dirs))


def focal_shift(fr, hub, sec, g):
    fr.loads = {}
    fr.load(hub, np.r_[W_HUB * g, 0, 0, 0])
    u = fr.solve()
    th = u[hub, 3:6]
    C = u[sec, :3]
    n = N0 + np.cross(th, N0)
    F = F_P - 2 * np.dot(F_P - C, n) * n
    dF = F - np.array([-11.4, 0, 0])
    return dF, u[sec, :3], th


def study(label, **kw):
    fr, hub, sec, dirs = hub_model(**kw)
    dF_h, u_h, th_h = focal_shift(fr, hub, sec, np.array([0, 0, -1.0]))
    dF_z, u_z, th_z = focal_shift(fr, hub, sec, np.array([0, -1.0, 0]))
    swing = np.linalg.norm((dF_h - dF_z)[1:]) * 25.4
    # torsional stiffness: unit torque about Y
    fr.loads = {}; fr.load(hub, [0, 0, 0, 0, 1.0, 0]); u = fr.solve()
    k_t = 1.0 / u[hub, 4]
    print(f"{label:46s} hub sag horizon {np.linalg.norm(u_h)*25400:5.0f} um, zenith {np.linalg.norm(u_z)*25400:5.0f} um"
          f" | focal-plane swing {swing:5.3f} mm | twist {k_t:7.0f} in-lb/rad | spike lines {len(dirs)}: {dirs}")
    return swing


same = {a: (+1, -1) for a in uc.STRUTS}                                   # as drawn
alt = {45: (+1, -1), 135: (-1, +1), 225: (+1, -1), 315: (-1, +1)}         # alternate senses per post
paired = {45: (+1, +1), 135: (-1, -1), 225: (+1, +1), 315: (-1, -1)}      # both wires of a post same side
if __name__ == "__main__":
    study("A  as drawn (hi +90 / lo -90 at every post)", senses=same)
    study("B  alternate senses post to post", senses=alt)
    study("C  paired senses (4-spike pattern)", senses=paired)
    study("D  B + lo anchors at -2.5", senses=alt, y_anchor=(3.5, -2.5))
    study("E  C + lo anchors at -2.5", senses=paired, y_anchor=(3.5, -2.5))
    study("F  B + taller hub (1.5..3.96)", senses=alt, hub_y=(1.5, 2.46))
    study("G  D + taller hub (1.5..3.96)", senses=alt, y_anchor=(3.5, -2.5), hub_y=(1.5, 2.46))
    study("H  C + lo -2.5 + taller hub", senses=paired, y_anchor=(3.5, -2.5), hub_y=(1.5, 2.46))
    study("I  D with 0.031 wire", senses=alt, y_anchor=(3.5, -2.5), wire_dia=0.031)
    study("J  D with offset 60", senses=alt, y_anchor=(3.5, -2.5), offset=60)
    study("K  A with lo anchors at -2.5 (old 'far low')", senses=same, y_anchor=(3.5, -2.5))
