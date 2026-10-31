import numpy as np
from skfem import *
from skfem.models.poisson import unit_load
from skfem.helpers import dd, ddot, trace, eye
import scipy.sparse as sp
import scipy.sparse.linalg as spl

nu = 0.22
M = MeshTri.init_circle(6)
ib = Basis(M, ElementTriMorley())

@BilinearForm
def bilin(u, v, w):
    C = lambda T: (1 - nu) * T + nu * eye(trace(T), 2)
    return ddot(C(dd(u)), dd(v))

K = asm(bilin, ib).tocsc()
f = asm(unit_load, ib)
vd = ib.nodal_dofs[0]
x, y = M.p
A4 = np.c_[np.ones_like(x), x, y, x ** 2 + y ** 2]

def solve(pads, fixk=1e6):
    Pm = ib.probes(np.array(pads).T).tocsr()  # (n, ndof)
    F = -f + Pm.T @ np.full(len(pads), np.pi / len(pads))
    S = Pm[:3]
    Kp = (K + fixk * (S.T @ S)).tocsc()
    u = spl.spsolve(Kp, F)
    w = u[vd]
    c, *_ = np.linalg.lstsq(A4, w, rcond=None)
    r = w - A4 @ c
    return np.sqrt(np.mean(r ** 2)), r.max() - r.min(), r

def ring(n, r, phi0=90):
    a = np.radians(phi0 + 360 / n * np.arange(n))
    pts = np.c_[r * np.cos(a), r * np.sin(a)]
    order = list(range(0, n, max(1, n // 3)))[:3]
    return pts[order + [i for i in range(n) if i not in order]]

def nine(r1, r2, b, phi0=90):
    pts = []
    for k in range(3):
        p = np.radians(phi0 + 120 * k)
        pts.append((r1 * np.cos(p), r1 * np.sin(p)))
    for k in range(3):
        p = np.radians(phi0 + 120 * k)
        for s in (-1, 1):
            q = p + s * np.radians(b)
            pts.append((r2 * np.cos(q), r2 * np.sin(q)))
    return np.array(pts)

if __name__ == "__main__":
    from scipy.optimize import minimize
    S = 3380
    for n in (3, 6):
        rs = np.arange(0.3, 0.95, 0.01)
        v = [solve(ring(n, r))[0] for r in rs]
        i = int(np.argmin(v)); rms, pv, _ = solve(ring(n, rs[i]))
        print(f"{n}-point ring: best r {rs[i]:.2f}R rms {rms*S:.2f} nm pv {pv*S:.1f} nm")
    obj = lambda v: solve(nine(*v))[0] if (0.1 < v[0] < 0.9 and 0.3 < v[1] < 0.98 and 5 < v[2] < 58) else 1
    best = min((obj((a, b, c)), (a, b, c)) for a in (0.25, 0.35, 0.45) for b in (0.65, 0.75, 0.85) for c in (20, 30, 40))
    res = minimize(obj, best[1], method="Nelder-Mead", options=dict(xatol=1e-4, fatol=1e-10, maxiter=400))
    rms, pv, _ = solve(nine(*res.x))
    print("9-pt optimum r1 %.3f r2 %.3f beta %.1f" % tuple(res.x), f"rms {rms*S:.2f} nm pv {pv*S:.1f} nm")
    res2 = minimize(lambda v: obj((v[0], v[1], 30)), res.x[:2], method="Nelder-Mead", options=dict(xatol=1e-4))
    rms, pv, _ = solve(nine(res2.x[0], res2.x[1], 30))
    print("9-pt, outer six evenly spaced: r1 %.3f r2 %.3f" % tuple(res2.x), f"rms {rms*S:.2f} nm pv {pv*S:.1f} nm")
    np.save("opt.npy", np.r_[res.x, res2.x])
