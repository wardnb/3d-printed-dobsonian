"""Fit-check the detailed upper cage and export cut files."""
import itertools
import json
import math
import os

import cadquery as cq

import upper_cage as uc

IN = uc.IN
OUT = os.path.join(os.path.dirname(__file__), "out", "upper_cage")
os.makedirs(OUT, exist_ok=True)

parts, info, flats = uc.build()
report = {}

# ---- interference: any two parts sharing volume (touching faces are fine)
clashes = []
for (a, pa), (b, pb) in itertools.combinations(parts.items(), 2):
    vol = pa.intersect(pb).val().Volume() if pa.val().BoundingBox().xmax else 0
    if vol > 1.0:  # mm^3
        clashes.append((a, b, round(vol / IN**3, 4)))
report["clashes_in3"] = clashes

# ---- light path: incoming 16" beam (r = 8.0") must be clear through the cage
beam = (cq.Workplane("XZ").circle(8.0 * IN).extrude(-12 * IN).translate((0, -6 * IN, 0)))
report["beam_hits"] = [k for k, p in parts.items() if p.intersect(beam).val().Volume() > 1.0]

# ---- focuser board pull holes: where did they land in the tube frame?
board = parts["focuser_board"].val()
pull = []
for e in board.Edges():
    if e.geomType() == "CIRCLE" and abs(e.radius() - uc.TAP_10 / 2 * IN) < 0.05:
        c = e.Center()
        if c.x > -(uc.R_IN + 0.01) * IN:          # inner face copy only
            pull.append((round(c.y / IN, 2), round(c.z / IN, 2)))
report["board_pull_holes_yz"] = sorted(set(pull))
report["rails_at_z"] = [uc.RAIL_Z, -uc.RAIL_Z]

# ---- weights (6061: 0.0975 lb/in^3)
dens = 0.0975
wt = {k: round(p.val().Volume() / IN**3 * dens, 2) for k, p in parts.items() if k != "waypoint_finder"}
report["weights_lb"] = wt
report["cage_metal_lb"] = round(sum(wt.values()), 2)

# ---- cut files
def flat_dxf(plate, name, t=uc.T):
    sec = plate.section(t * IN / 2)
    cq.exporters.export(sec, os.path.join(OUT, name + ".dxf"))
    return sec


secs = {
    "ring_lower": flat_dxf(flats["lower"], "ring_lower_3-8-inch-6061"),
    "ring_upper": flat_dxf(flats["upper"], "ring_upper_3-8-inch-6061"),
    "focuser_board": flat_dxf(flats["board"], "focuser_board_quarter-inch-6061", uc.TB),
}

asm = cq.Assembly(name="upper_cage")
colors = dict(ring_lower=(0.74, 0.76, 0.79), ring_upper=(0.74, 0.76, 0.79), struts=(0.6, 0.62, 0.65),
              board_rails=(0.6, 0.62, 0.65), focuser_board=(0.74, 0.76, 0.79),
              spider_blocks=(0.12, 0.12, 0.13), pair_connectors_concept=(0.85, 0.55, 0.25),
              finder_bracket=(0.74, 0.76, 0.79), waypoint_finder=(0.55, 0.12, 0.12))
for k, p in parts.items():
    asm.add(p, name=k, color=cq.Color(*colors[k]))
asm.save(os.path.join(OUT, "upper_cage_v2.step"))

# straight quad spider option: its four blocks (0 deg seat is shared with the curved set)
quad = uc.spider_blocks(uc.QUAD, tip_hole=0.257)
cq.exporters.export(quad, os.path.join(OUT, "spider_blocks_quad_option.step"))
report["quad_block_clashes"] = [k for k, p in parts.items()
                                if k != "spider_blocks" and p.intersect(quad).val().Volume() > 1.0]
report["quad_beam_hit"] = quad.intersect(beam).val().Volume() > 1.0

# quad spider (chosen): vanes, hub, studs and towers
qsp, qinfo = uc.quad_spider()
report["quad_spider"] = qinfo
report["quad_spider_clashes"] = [f"{k}/{w}" for w, wp in qsp.items() for k, p in parts.items()
                                 if not (w == "studs" and k == "struts")        # studs pass through the posts by design
                                 and k != "spider_blocks" and p.intersect(wp).val().Volume() > 1.0]
report["quad_spider_internal"] = [f"{a}/{b}" for a, b in itertools.combinations(qsp, 2)
                                  if not {a, b} == {"studs", "vanes"} and qsp[a].intersect(qsp[b]).val().Volume() > 1.0]
report["quad_vanes_in_focuser_cone"] = None   # filled after the cone exists
qasm = cq.Assembly(name="quad_spider")
for k, qp in qsp.items():
    qasm.add(qp, name=k)
qasm.save(os.path.join(OUT, "quad_spider.step"))
report["quad_spider_weights_lb"] = {k: round(p.val().Volume() / IN**3 * (0.283 if k in ("vanes", "studs") else dens), 2) for k, p in qsp.items()}
report["quad_alignment_bar_clash"] = bar_clash = None

# wire spider option: anchored on the posts between the rings
wsp, runs = uc.wire_spider()
report["wire_runs_in"] = runs
report["wire_spider_clashes"] = [f"{k}/{w}" for w, wp in wsp.items() for k, p in parts.items()
                                 if not (w == "studs" and k == "struts")       # studs pass through the posts by design
                                 and not (w == "extensions" and k == "ring_upper")   # extension bolt seats on the ring
                                 and k != "spider_blocks" and p.intersect(wp).val().Volume() > 1.0]
report["wire_spider_internal_clashes"] = [f"{a}/{b}" for a, b in itertools.combinations(wsp, 2)
                                          if not {a, b} == {"studs", "extensions"}
                                          and wsp[a].intersect(wsp[b]).val().Volume() > 1.0]
# the two wires of each post must not touch where they cross
import numpy as np
r_face = uc.R_BOLT - uc.STRUT_SQ / 2
seps = []
for a in uc.STRUTS:
    tx, tz = uc.pol(1.0, a + 90); ux, uz = uc.pol(1.0, a)
    hx, hz = uc.pol(1.2, a + uc.WIRE_SENSE[a] * 50)
    y_hi_anchor = uc.y_hi_in + uc.T + uc.EXT_H - 0.4
    A0 = np.array([r_face * ux + 0.15 * tx, y_hi_anchor, r_face * uz + 0.15 * tz]); A1 = np.array([hx, 2.66 + 0.45, hz])
    B0 = np.array([r_face * ux - 0.15 * tx, 0.9, r_face * uz - 0.15 * tz]); B1 = np.array([hx, 5.9 - 0.15, hz])
    best = 9
    for sa in np.linspace(0, 1, 400):
        pa = A0 + (A1 - A0) * sa
        pb = B0[None, :] + (B1 - B0)[None, :] * np.linspace(0, 1, 400)[:, None]
        best = min(best, np.min(np.linalg.norm(pb - pa, axis=1)))
    seps.append(round(best - 0.025, 3))
report["wire_pair_min_gap_in"] = seps
# reflected cone from the secondary to the focus (focuser on -X) must stay clear of the wires
L_focus = 11.9
cone = cq.Workplane("XY").add(cq.Solid.makeCone(1.65 * IN, 0.15 * IN, L_focus * IN,
                                                cq.Vector(0.5 * IN, 0, 0), cq.Vector(-1, 0, 0)))
report["wires_in_focuser_cone"] = wsp["wires"].intersect(cone).val().Volume() > 0.01
report["quad_vanes_in_focuser_cone"] = qsp["vanes"].intersect(cone).val().Volume() > 0.01
# beam checks: 2 wires x 40 lb pulling inward on an extension block (cantilever off the ring)
E = 10.0e6
STRUT_I = uc.STRUT_SQ ** 4 / 12
L_ext = uc.EXT_H - 0.4
EXT_I = uc.STRUT_SQ * uc.EXT_RAD ** 3 / 12
report["extension_tip_deflection_in"] = round(75.0 * L_ext ** 3 / (3 * E * EXT_I), 6)
report["extension_root_moment_inlb"] = round(75.0 * L_ext, 1)
# ...and on the post between the rings at y = 0.9 (simply supported at the rings)
a_lo = 0.9 - uc.y_lo_in; b_lo = uc.I["ring_gap"] - a_lo
report["post_deflection_in"] = round(75.0 * a_lo**2 * b_lo**2 / (3 * E * STRUT_I * uc.I["ring_gap"]), 6)
# alignment tools
bar = uc.alignment_bar()
gauge, rod = uc.centering_gauge()
report["alignment_bar_clashes"] = [k for k, p in parts.items() if k != "struts" and p.intersect(bar).val().Volume() > 1.0]
report["alignment_bar_len_in"] = round(bar.val().BoundingBox().zlen / IN, 2)
report["gauge_clashes"] = [k for k, p in parts.items() if k not in ("spider_blocks",) and p.intersect(gauge).val().Volume() > 1.0]
report["gauge_clashes"] += [f"quad_{k}" for k, p in qsp.items() if p.intersect(gauge).val().Volume() > 1.0]
tools = cq.Assembly(name="alignment_tools")
tools.add(bar, name="alignment_bar", color=cq.Color(0.85, 0.2, 0.2))
tools.add(gauge, name="centering_gauge", color=cq.Color(0.86, 0.72, 0.5))
tools.save(os.path.join(OUT, "alignment_tools.step"))
cq.exporters.export(gauge, os.path.join(OUT, "centering_gauge.step"))
report["wire_spider_weights_lb"] = {k: round(p.val().Volume() / IN**3 * (0.283 if k in ("wires", "studs") else dens), 2) for k, p in wsp.items()}
wasm = cq.Assembly(name="wire_spider")
for k, wp in wsp.items():
    wasm.add(wp, name=k)
wasm.save(os.path.join(OUT, "wire_spider_option.step"))

# ---- cut-sheet image
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt


def draw(ax, sec, title, dims):
    for e in sec.val().Edges():
        n = max(8, int(e.Length() / IN * 12))
        pts = [e.positionAt(t / n) for t in range(n + 1)]
        ax.plot([p.x / IN for p in pts], [p.y / IN for p in pts], color="#1a2430", lw=0.8)
    ax.set_aspect("equal")
    ax.set_title(title, fontsize=11, loc="left", fontweight="bold")
    ax.text(0.0, -0.08, dims, transform=ax.transAxes, fontsize=8.5, va="top", color="#3b4654")
    ax.grid(True, color="#dde3e8", lw=0.5)
    ax.tick_params(labelsize=7)


fig, axs = plt.subplots(1, 3, figsize=(16, 7.4), gridspec_kw=dict(width_ratios=[1, 1, 0.55]))
draw(axs[0], secs["ring_lower"], "Lower ring (truss end)",
     "3/8\" 6061 · ID 17.50\" · OD 20.50\" · solid (no lightening slots)\n4 strut + 2 rail + 6 pair-connector holes, 0.257\" (1/4-20 clr)")
draw(axs[1], secs["ring_upper"], "Upper ring (sky end)",
     "3/8\" 6061 · ID 17.50\" · OD 20.50\" · solid\n4 strut/extension + 2 rail + 12 spider-seat + 2 finder holes, 0.257\"\nSpider seats: curved 0/120/240°, quad 0/90/180/270° · finder 150°")
draw(axs[2], secs["focuser_board"], "Focuser board",
     "1/4\" 6061 · 7.30\" × 6.40\" · R0.25\" corners\n2.50\" drawtube hole · 4× #8-32 on 3.00\" BC (INPUT)\n3× #10-32 pull holes (tap 0.159\")")
for ax in axs:
    ax.set_xlabel("inches", fontsize=7)
fig.suptitle("16\" Dob upper cage v2 — flat parts (assumed inputs marked)", fontsize=13, x=0.01, ha="left")
fig.tight_layout(rect=(0, 0.06, 1, 0.97))
fig.savefig(os.path.join(OUT, "cut_sheet_v2.png"), dpi=150)

json.dump(report, open(os.path.join(OUT, "fit_report.json"), "w"), indent=2)
print(json.dumps(report, indent=2))
