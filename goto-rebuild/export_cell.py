"""Fit-check the new mirror cell and export its cut files (DXF per part), a STEP and a cut sheet.
Run from goto-rebuild/:  python export_cell.py"""
import itertools
import json
import math
import os

import cadquery as cq

import cell

IN = cell.IN
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "out", "cell")
os.makedirs(OUT, exist_ok=True)
c = cell.C
P, L = cell.build()
rep = cell.report()

# --- fit checks (inside the cell; the ball-in-seat and bolt-in-thread overlaps are by design)
skip = [{"triangles", "pivots"}, {"frame", "collimation_bolts"}]
rep["clashes_in3"] = [(a, b, round(pa.intersect(pb).val().Volume() / IN ** 3, 4))
                      for (a, pa), (b, pb) in itertools.combinations(P.items(), 2)
                      if "fan" not in (a, b) and {a, b} not in skip
                      and pa.intersect(pb).val().Volume() / IN ** 3 > 1e-4]
# --- against the box: stubs (45 mm) and spacer tubes at the model's positions, mirror board opening ASSUMED
params = json.load(open("out/params.json"))["params"]
stubs = list(zip(params["mcage_tube_angles"], params["mcage_tube_radii"]))
R = c["mirror_dia"] / 2
frame = cell.frame_poly()
from shapely.geometry import Point
hits = []
for a, r in stubs:
    if frame.intersects(Point(*cell.pol(r, a)).buffer(params["mcage_tube_od"] / 2 + 0.1)):
        hits.append(f"stub {a}")
for a in params["mcage_spacer_angles"]:
    if frame.intersects(Point(*cell.pol(9.9, a)).buffer(params["mcage_spacer_od"] / 2 + 0.1)):
        hits.append(f"spacer {a}")
rep["box_clashes"] = hits
rep["frame_r_max_in"] = round(max(math.hypot(x, z) for x, z in frame.exterior.coords), 2)
rep["bolt_circle_r_in"] = c["r_bolt"]

# --- cut files
def dxf(flat, t, name):
    sec = flat.section(t * IN / 2)
    cq.exporters.export(sec, os.path.join(OUT, name + ".dxf"))
    return sec


secs = dict(
    frame=dxf(cell.frame_flat(), c["frame_t"], "cell_frame_half-inch-6061-or-MIC6"),
    triangle=dxf(cell.tri_flat(cell.pads()[0]), c["tri_t"], "cell_triangle_x3_quarter-inch-6061"),
    gusset=dxf(cell.gusset_flat(), c["gusset_t"], "cell_edge_gusset_x2_half-inch-6061"),
)
asm = cq.Assembly(name="mirror_cell")
cols = dict(frame=(0.74, 0.76, 0.79), triangles=(0.6, 0.62, 0.65), pads=(0.95, 0.95, 0.9), pivots=(0.3, 0.3, 0.3),
            edge_posts=(0.74, 0.76, 0.79), guard_posts=(0.6, 0.62, 0.65), collimation_bolts=(0.2, 0.2, 0.2),
            fan=(0.1, 0.1, 0.1), mirror=(0.75, 0.85, 0.95))
for k, p in P.items():
    asm.add(p, name=k, color=cq.Color(*cols[k]))
asm.save(os.path.join(OUT, "mirror_cell.step"))

# --- cut sheet
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt


def draw(ax, sec, title, notes):
    for e in sec.val().Edges():
        n = max(8, int(e.Length() / IN * 12))
        pts = [e.positionAt(t / n) for t in range(n + 1)]
        ax.plot([p.x / IN for p in pts], [p.y / IN for p in pts], color="#1a2430", lw=0.8)
    ax.set_aspect("equal")
    ax.set_title(title, fontsize=11, loc="left", fontweight="bold")
    ax.text(0.0, -0.16, notes, transform=ax.transAxes, fontsize=8.5, va="top", color="#3b4654")
    ax.grid(True, color="#dde3e8", lw=0.5)
    ax.tick_params(labelsize=7)


fig, axs = plt.subplots(1, 3, figsize=(17, 8.5), gridspec_kw=dict(width_ratios=[1.5, 0.8, 0.6]))
draw(axs[0], secs["frame"], "Cell frame (1 off)",
     "1/2\" 6061, or MIC-6 cast plate (stays flat after pocketing)\n"
     f"3× 5/16-24 tap at r {c['r_bolt']}\" (90/210/330°, next to the truss stubs): collimation bolts\n"
     f"3× 1/4-20 tap at r {rep['pivot_r']}\": pivot posts · 4× #6 for the 80 mm fan\n"
     "radial slots: 2 per load gusset (225/315°), 1 per guard post (90/210/330°)")
draw(axs[1], secs["triangle"], "Flotation triangle (3 off)",
     "1/4\" 6061 · 3× #10-32 tap: pad screws from below\n"
     "centre: 1/4\" hole, 90° countersink on the underside\nfor the 3/8\" steel ball (pivot)\n"
     f"pads: r1 {c['r1'] * R:.2f}\", r2 {c['r2'] * R:.2f}\" at ±{c['beta']}°\nmove pads under the pucks before drilling")
draw(axs[2], secs["gusset"], "Edge gusset (2 off)",
     "1/2\" 6061, stands on edge\n2× 1/4-20 tap 0.6\" deep in the bottom edge\n"
     "1/8\" Delrin face on the inner edge,\n1.4\" tall, centred on the mirror's mid-thickness")
fig.suptitle("16\" mirror cell — 9-point flotation, edge gussets at ±45° from down, push-pull in bushings", fontsize=13, x=0.01, ha="left")
fig.tight_layout(rect=(0, 0.08, 1, 0.95), w_pad=3)
fig.savefig(os.path.join(OUT, "cut_sheet_cell.png"), dpi=150)

json.dump(rep, open(os.path.join(OUT, "fit_report.json"), "w"), indent=1)
print(json.dumps({k: v for k, v in rep.items() if k != "pads_in"}, indent=1))
