"""Wire-spider layout search with the full 6-DOF hub and the REAL load: 1.3 lb of secondary
+ carrier + body hanging ~2.4" below the hub centre, plus 0.5 lb of hub, swept through the
altitude range. Posts rigid (cage compliance is added by cage_fe.py)."""
import itertools
import math
import numpy as np
from cage_fe import Frame, RIGID, E_W
import upper_cage as uc

F_P = np.array([0, 11.9, 0.0])
N0 = np.array([-1, -1, 0]) / math.sqrt(2)
SENSES = dict(same={a: (+1, -1) for a in uc.STRUTS},
              alt={45: (+1, -1), 135: (-1, +1), 225: (+1, -1), 315: (-1, +1)},
              paired={45: (+1, +1), 135: (-1, -1), 225: (+1, +1), 315: (-1, -1)})


def model(rims=(2.76, 3.86), anchors=(3.5, 0.9), cross=True, senses="same", offset=90,
          wire_dia=0.025, hub_r=1.2, sec_cg=0.9, stud_tang=0.0):
    """rims: (low rim y, high rim y); anchors: (high anchor y, low anchor y).
    cross=True: high anchor -> low rim, low anchor -> high rim."""
    Aw = math.pi * wire_dia ** 2 / 4
    wire = dict(E=E_W, G=E_W / 2.6, A=Aw, Iy=1e-9, Iz=1e-9, J=1e-9)
    fr = Frame()
    hub = fr.node(0, (rims[0] + rims[1]) / 2, 0)
    sec = fr.node(0, 0, 0); fr.beam(hub, sec, RIGID)
    cg = fr.node(0, sec_cg, 0); fr.beam(hub, cg, RIGID)
    r_face = uc.R_BOLT - uc.STRUT_SQ / 2
    dirs = []
    S = SENSES[senses]
    for a in uc.STRUTS:
        tx, tz = uc.pol(1.0, a + 90)
        pairs = ((anchors[0], rims[0] if cross else rims[1], S[a][0], +stud_tang),
                 (anchors[1], rims[1] if cross else rims[0], S[a][1], -stud_tang))
        for y_a, y_h, s, tg in pairs:
            hx, hz = uc.pol(hub_r, a + s * offset)
            nh = fr.node(hx, y_h, hz); fr.beam(hub, nh, RIGID)
            px, pz = uc.pol(r_face, a)
            npn = fr.node(px + tg * tx, y_a, pz + tg * tz); fr.fix(npn, (0, 1, 2, 3, 4, 5))
            fr.beam(npn, nh, wire)
            dirs.append(round(math.degrees(math.atan2(pz - hz, px - hx)) % 180, 0))
    return fr, dict(hub=hub, sec=sec, cg=cg), sorted(set(dirs))


def focal_err(fr, ids, alt):
    g = np.array([0, -math.sin(math.radians(alt)), -math.cos(math.radians(alt))])
    fr.loads = {}
    fr.load(ids["cg"], np.r_[1.3 * g, 0, 0, 0])
    fr.load(ids["hub"], np.r_[0.5 * g, 0, 0, 0])
    u = fr.solve()
    th = u[ids["hub"], 3:6]
    C = u[ids["sec"], :3]
    n = N0 + np.cross(th, N0)
    F = F_P - 2 * np.dot(F_P - C, n) * n
    return F - np.array([-11.4, 0, 0]), u[ids["sec"], :3], th


def evaluate(**kw):
    fr, ids, dirs = model(**kw)
    errs = [focal_err(fr, ids, a)[0] for a in (0, 45, 90)]
    swing = np.linalg.norm((errs[0] - errs[2])[1:]) * 25.4
    resid = max(np.linalg.norm((e - errs[1])[1:]) * 25.4 for e in errs)
    C = np.zeros((6, 6))
    for d in range(6):
        fr.loads = {}; f = [0] * 6; f[d] = 1.0; fr.load(ids["hub"], f); C[:, d] = fr.solve()[ids["hub"]]
    K = np.linalg.inv(C)
    return dict(swing=swing, resid=resid, Kdiag=np.diag(K), dirs=dirs, spikes=2 * len(dirs))


def show(label, **kw):
    r = evaluate(**kw)
    k = r["Kdiag"]
    print(f"{label:58s} swing {r['swing']:6.3f} mm  resid@45 {r['resid']:6.3f} | tilt Mx {k[3]:6.0f} Mz {k[5]:6.0f} twist {k[4]:6.0f} | Fy {k[1]:5.0f} | spikes {r['spikes']}")
    return r


if __name__ == "__main__":
    print("--- short hub (as built: rims 2.76 / 3.86) ---")
    show("v1 as drawn", )
    show("v1, lo anchors -2.5", anchors=(3.5, -2.5))
    show("alt senses", senses="alt")
    show("alt senses, lo -2.5", senses="alt", anchors=(3.5, -2.5))
    show("paired, lo -2.5", senses="paired", anchors=(3.5, -2.5))
    show("v1, not crossing", cross=False)
    print("--- long hub: top rim 5.2 on post extensions above the upper ring, anchors 5.3 ---")
    for senses in ("same", "alt", "paired"):
        for anchors in ((5.3, 0.9), (5.3, -2.5), (5.3, 3.5)):
            for cross in (True, False):
                show(f"long hub rims 2.8/5.2, {senses:6s} anchors {anchors} cross={cross}",
                     rims=(2.8, 5.2), anchors=anchors, senses=senses, cross=cross)
    print("--- long hub, offset 60 ---")
    show("long hub, same, (5.3,0.9) cross, offset 60", rims=(2.8, 5.2), anchors=(5.3, 0.9), senses="same", offset=60)
    show("long hub, same, (5.3,0.9) cross, offset 45", rims=(2.8, 5.2), anchors=(5.3, 0.9), senses="same", offset=45)
    show("long hub, same, (5.3,0.9) cross, offset 30", rims=(2.8, 5.2), anchors=(5.3, 0.9), senses="same", offset=30)
    show("long hub, alt, (5.3,0.9) cross, offset 45", rims=(2.8, 5.2), anchors=(5.3, 0.9), senses="alt", offset=45)
