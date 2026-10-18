"""Export the secondary holder, carrier and gluing jig."""
import os

import cadquery as cq

import secondary_holder as sh

IN = sh.IN
OUT = os.path.join(os.path.dirname(__file__), "out", "secondary_holder")
os.makedirs(OUT, exist_ok=True)

parts = sh.build()
carrier = sh.carrier_flat()
base, bridge = sh.jig_flat()

# flat cut files (DXF at mid-thickness so every through feature shows)
def dxf(solid, z_in, name):
    sec = solid.section(z_in * IN)
    cq.exporters.export(sec, os.path.join(OUT, name + ".dxf"))
    return sec

s_car = dxf(carrier, sh.P["pad_h"] + 0.02, "carrier_quarter-inch-6061")
s_base = dxf(base, 0.45, "jig_base_half-inch")
s_bridge = dxf(bridge, 0.12, "jig_bridge_quarter-inch")

# holder on the scope
asm = cq.Assembly(name="secondary_holder")
asm.add(parts["secondary_mirror"], name="mirror", color=cq.Color(0.7, 0.85, 0.95))
asm.add(parts["carrier"], name="carrier", color=cq.Color(0.74, 0.76, 0.79))
asm.add(parts["body"], name="body", color=cq.Color(0.15, 0.15, 0.16))
asm.save(os.path.join(OUT, "secondary_holder_v2.step"))

# gluing stack in the jig: mirror face down, carrier on its back, bridge on 1/2" standoffs
t = sh.P["thick"]
floor = 0.5 - sh.P["jig_pocket"]
mirror_flat = cq.Workplane("XY").ellipse(sh.MAJOR / 2 * IN, sh.P["minor"] / 2 * IN).extrude(t * IN)
jig = cq.Assembly(name="gluing_jig")
jig.add(base, name="jig_base", color=cq.Color(0.86, 0.72, 0.5))
jig.add(mirror_flat.translate((0, 0, floor * IN)), name="mirror_face_down", color=cq.Color(0.7, 0.85, 0.95))
jig.add(carrier.translate((0, 0, (floor + t) * IN)), name="carrier", color=cq.Color(0.74, 0.76, 0.79))
standoff = 0.625   # 5/8" for the 0.70" thick 3.5" secondary (standoff = mirror thickness - 0.11")
L = sh.MAJOR + 1.8
for x in (-(L / 2 - 0.45), L / 2 - 0.45):
    jig.add(cq.Workplane("XY").center(x * IN, 0).polygon(6, 0.25 * IN).extrude(standoff * IN)
            .translate((0, 0, 0.5 * IN)), name=f"standoff_{x:+.1f}", color=cq.Color(0.6, 0.6, 0.6))
jig.add(bridge.translate((0, 0, (0.5 + standoff) * IN)), name="jig_bridge", color=cq.Color(0.86, 0.72, 0.5))
jig.save(os.path.join(OUT, "gluing_jig.step"))
gap = 0.5 + standoff - (floor + t + sh.P["pad_h"] + sh.P["carrier_t"])

# cut sheet
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt


def draw(ax, sec, title, note):
    for e in sec.val().Edges():
        n = max(32, int(e.Length() / IN * 24))
        pts = [e.positionAt(k / n) for k in range(n + 1)]
        ax.plot([p.x / IN for p in pts], [p.y / IN for p in pts], color="#1a2430", lw=0.9)
    ax.set_aspect("equal")
    ax.set_title(title, loc="left", fontsize=11, fontweight="bold")
    ax.text(0, -0.12, note, transform=ax.transAxes, fontsize=8.5, va="top", color="#3b4654")
    ax.grid(True, color="#dde3e8", lw=0.5)
    ax.tick_params(labelsize=7)
    ax.axvline(sh.holder_axis_local()[0], color="#9a6d1f", lw=0.8, ls="--")


fig, axs = plt.subplots(1, 3, figsize=(16, 5.8))
draw(axs[0], s_car, "Carrier (1/4\" 6061)",
     f"Ellipse {2*(sh.MAJOR/2-sh.P['inset_major']):.2f}\" x {2*(sh.P['minor']/2-sh.P['inset']):.2f}\", stays inside the mirror's shadow\n"
     f"3 pads 0.35\" dia, {sh.P['pad_h']:.3f}\" proud · 3 RTV wells 0.50\" x 0.04\"\n"
     f"3x #8 clr · 1/8\" dowel hole + slot · dashed = holder axis ({sh.OFF_MAJOR:.3f}\" off centre)")
draw(axs[1], s_base, "Jig base (1/2\" birch or 6061)",
     f"Mirror pocket {sh.MAJOR+2*sh.P['jig_clear']:.3f}\" x {sh.P['minor']+2*sh.P['jig_clear']:.3f}\", {sh.P['jig_pocket']}\" deep\n"
     "finger notches at the minor-axis ends · 2x #8-32 tapped for standoffs")
draw(axs[2], s_bridge, "Jig bridge (1/4\")",
     "2x 1/8\" press-fit pins on the holder-axis pattern\n"
     f"2x #8 clr · on 5/8\" standoffs: {gap:.3f}\" above the carrier")
fig.suptitle("Self-aligning secondary holder v2 — flat parts", fontsize=13, x=0.01, ha="left")
fig.tight_layout(rect=(0, 0.08, 1, 0.95))
fig.savefig(os.path.join(OUT, "holder_cut_sheet.png"), dpi=150)
print("bridge gap over carrier (in):", round(gap, 3))
print(sorted(os.listdir(OUT)))
