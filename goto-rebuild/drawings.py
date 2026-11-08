"""Dimensioned drawing sheets (PDF) for the parts with 3D features, straight from the CadQuery solids (2026-11-08).

Hidden-line projections come from OCC's HLR through the same solids the DXFs and fit checks use, so the drawings
cannot disagree with the model. Dimensions are the ones you need at the machine, taken from the module constants.
Run from goto-rebuild/: python3 drawings.py -> out/drawings/*.pdf (+ a combined all_sheets.pdf).

Sheets: socket block (top, outside face, underside, section A-A), gib pin + retainer plate, cone plug, alt and az roller blocks.
"""
import math
import os

import cadquery as cq
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages
from OCP.HLRBRep import HLRBRep_Algo, HLRBRep_HLRToShape
from OCP.HLRAlgo import HLRAlgo_Projector
from OCP.gp import gp_Ax2, gp_Pnt, gp_Dir

import truss_joints as T
import rocker
import json

IN = 25.4
OUT = os.path.join("out", "drawings")
os.makedirs(OUT, exist_ok=True)
INK, HID, DIM = "#1a2430", "#8a96a3", "#b8520a"


# ------------------------------------------------------------------ projection
def project(shape, view_dir, up):
    """Visible and hidden edge polylines (inches) of `shape` seen along view_dir (looking from +view_dir toward the
    origin), with `up` pointing up the page. Returns (visible, hidden) lists of [(x, y), ...]."""
    d = cq.Vector(*view_dir).normalized()
    u = cq.Vector(*up).normalized()
    x = u.cross(d).normalized()          # page x = up × view
    algo = HLRBRep_Algo()
    algo.Add(shape.val().wrapped if hasattr(shape, "val") else shape.wrapped)
    proj = HLRAlgo_Projector(gp_Ax2(gp_Pnt(0, 0, 0), gp_Dir(d.x, d.y, d.z), gp_Dir(x.x, x.y, x.z)))
    algo.Projector(proj)
    algo.Update()
    algo.Hide()
    hs = HLRBRep_HLRToShape(algo)
    out = []
    for comp in (hs.VCompound(), hs.OutLineVCompound(), hs.Rg1LineVCompound()), (hs.HCompound(), hs.OutLineHCompound()):
        polys = []
        for c in comp:
            if c.IsNull():
                continue
            for e in cq.Shape.cast(c).Edges():
                n = 1 if e.geomType() == "LINE" else 32
                pts = e.positions([i / n for i in range(n + 1)], mode="length")
                polys.append([(p.x / IN, p.y / IN) for p in pts])
        out.append(polys)
    return out


def draw_view(ax, shape, view_dir, up, title, hidden=True, scale_note=True):
    vis, hid = project(shape, view_dir, up)
    if hidden:
        for pl in hid:
            xs, ys = zip(*pl)
            ax.plot(xs, ys, color=HID, lw=0.5, ls=(0, (3, 2)))
    for pl in vis:
        xs, ys = zip(*pl)
        ax.plot(xs, ys, color=INK, lw=0.9)
    ax.set_aspect("equal")
    ax.set_title(title, fontsize=9, loc="left", fontweight="bold")
    ax.axis("off")
    return vis, hid


def dim(ax, p0, p1, off, text, vertical=False, fs=7):
    """Linear dimension between p0 and p1, offset `off` from the measured line (perpendicular)."""
    (x0, y0), (x1, y1) = p0, p1
    if vertical:
        xa = x0 + off
        ax.plot([x0, xa + 0.05 * (1 if off > 0 else -1)], [y0, y0], color=DIM, lw=0.5)
        ax.plot([x1, xa + 0.05 * (1 if off > 0 else -1)], [y1, y1], color=DIM, lw=0.5)
        ax.annotate("", xy=(xa, y0), xytext=(xa, y1), arrowprops=dict(arrowstyle="<->", color=DIM, lw=0.7))
        ax.text(xa + 0.06, (y0 + y1) / 2, text, color=DIM, fontsize=fs, va="center", ha="left", rotation=90)
    else:
        ya = y0 + off
        ax.plot([x0, x0], [y0, ya + 0.05 * (1 if off > 0 else -1)], color=DIM, lw=0.5)
        ax.plot([x1, x1], [y1, ya + 0.05 * (1 if off > 0 else -1)], color=DIM, lw=0.5)
        ax.annotate("", xy=(x0, ya), xytext=(x1, ya), arrowprops=dict(arrowstyle="<->", color=DIM, lw=0.7))
        ax.text((x0 + x1) / 2, ya + 0.06, text, color=DIM, fontsize=fs, ha="center", va="bottom")


def leader(ax, p, q, text, fs=7, ha="left"):
    ax.annotate(text, xy=p, xytext=q, fontsize=fs, color=DIM, ha=ha, va="center",
                arrowprops=dict(arrowstyle="-", color=DIM, lw=0.5))


def diam(ax, c, r, text, ang=45, L=0.6, fs=7):
    a = math.radians(ang)
    p = (c[0] + r * math.cos(a), c[1] + r * math.sin(a))
    q = (p[0] + L * math.cos(a), p[1] + L * math.sin(a))
    leader(ax, p, q, text, fs=fs)


def notes(fig, lines, x=0.04, y=0.17, fs=7.5):
    fig.text(x, y, "\n".join(lines), fontsize=fs, va="top", family="monospace", color=INK)


def title_block(fig, name, material, qty, sheet):
    fig.text(0.04, 0.955, f"16\" GoTo Dob rebuild  —  {name}", fontsize=14, fontweight="bold", color=INK)
    fig.text(0.04, 0.925, f"{material}  ·  qty {qty}  ·  inches  ·  from the CadQuery model, 2026-11-08  ·  {sheet}", fontsize=8.5, color="#3b4654")


# ------------------------------------------------------------------ parts in their own frames
def socket_block_local():
    """Socket block at base 90 moved so the datum (stub top centre) is the origin: x = tangential (-td... see note),
    y = up, z = radial (+z = outside face). At 90 deg rad_tan gives rd = +Z, td = -X, so block t = -x."""
    sb = T.socket_block(90)
    bx, bz = T.base_xz(90)
    sh = lambda s: s.translate(cq.Vector(-bx * IN, -T.Y_STUB_TOP * IN, -bz * IN))
    return {k: sh(v) for k, v in sb.items()}, sb


def gib_local():
    """Gib pin along +x (tip at +x), axis on the origin; slot through in y, wedge flat on the -y side."""
    g = cq.Workplane("YZ").circle(T.GIB_D / 2 * IN).extrude(T.GIB_L * IN)          # x from 0 to GIB_L
    slot = cq.Workplane("XY").box(0.6 * IN, 2 * IN, T.GIB_SLOT * IN).translate(((T.GIB_L - 0.3) * IN, 0, 0))
    g = g.cut(slot)
    # wedge flat: plane rising toward the tip at GIB_ANGLE; at the contact point (0.35 from the tip) the flat is
    # 0.154 below the axis (washer top when engaged); z-up here is the bore's up = +y of the drawing
    a = math.radians(T.GIB_ANGLE_DEG)
    x_c = T.GIB_L - 0.35
    y_c = -0.154
    cutter = (cq.Workplane("XY").box(4 * IN, 2 * IN, 4 * IN).translate((x_c * IN, (y_c - 1.0) * IN, 0))
              .rotate((x_c * IN, y_c * IN, 0), (x_c * IN, y_c * IN, 1 * IN), math.degrees(a)))
    g = g.cut(cutter)
    # rear: 0.26 hole 0.35 deep for the knob stud tip + 1/16 cross pin
    g = g.cut(cq.Workplane("YZ").circle(0.13 * IN).extrude(0.35 * IN))
    g = g.cut(cq.Workplane("XZ").circle(0.032 * IN).extrude(1 * IN, both=True).translate((0.2 * IN, 0, 0)))
    return g


def plate_local():
    p = cq.Workplane("XY").box(T.PLATE_W * IN, T.PLATE_H * IN, T.PLATE_T * IN)
    p = p.cut(cq.Workplane("XY").circle(0.13 * IN).extrude(1 * IN, both=True))
    for dt in (-0.55, 0.55):
        p = p.cut(cq.Workplane("XY").center(dt * IN, 0).circle(0.085 * IN).extrude(1 * IN, both=True))
    return p


def plug_local():
    """Cone plug with its axis along +y, cup apex (geometric) at the origin, nose face at S_NOSE."""
    plug = T.cone(T.NOSE_D / 2, T.POLE_OD / 2, T.S_SHOULDER - T.S_NOSE, (0, T.S_NOSE, 0), (0, 1, 0))
    plug = plug.union(T.cyl(T.POLE_OD / 2, T.SHOULDER_L, (0, T.S_SHOULDER, 0), (0, 1, 0)))
    plug = plug.union(T.cyl(T.BORE / 2 - 0.003, T.SHANK_L, (0, T.S_SHOULDER + T.SHOULDER_L, 0), (0, 1, 0)))
    plug = plug.cut(T.cyl(0.1005, 0.55, (0, T.S_NOSE, 0), (0, 1, 0)))                  # 1/4-20 tap drill
    screw = T.cyl(0.125, T.HEAD_SHANK, (0, T.S_NOSE, 0), (0, -1, 0))
    screw = screw.union(T.cyl(T.HEAD_D / 2, T.HEAD_H, (0, T.S_NOSE - T.HEAD_SHANK, 0), (0, -1, 0)))
    return plug, screw


# ------------------------------------------------------------------ sheets
def sheet_socket(pdf):
    P, _ = socket_block_local()
    blk = P["block"]
    Tt, Rr, Hh = T.BLOCK_T, T.BLOCK_R, T.BLOCK_H
    fig = plt.figure(figsize=(17, 11))
    title_block(fig, "Socket block (truss cone sockets, gib clamps)", "6061-T6 from 2-1/4 sq bar, faced 3.60 t × 2.00 r × 2.10 u", "3 (point + 2 back; 210 = 330)", "sheet 1/4")
    # top view: look down -y, page up = -z (inside face at the top of the page? keep outside face at the top)
    ax = fig.add_axes([0.04, 0.50, 0.44, 0.40])
    draw_view(ax, blk, (0, 1, 0), (0, 0, 1), "TOP (cup face). Outside face at the top of the view; x = tangential")
    ax.set_xlim(-2.6, 2.6); ax.set_ylim(-1.9, 2.3)
    dim(ax, (-Tt / 2, -Rr / 2), (Tt / 2, -Rr / 2), -0.35, f"{Tt:.2f}")
    dim(ax, (Tt / 2, -Rr / 2), (Tt / 2, Rr / 2), 0.35, f"{Rr:.2f}", vertical=True)
    dim(ax, (-0.8, Rr / 2), (0.8, Rr / 2), 0.55, "1.600 (cup apexes, on the stub's radial line)")
    for sx in (-1, 1):
        ax.plot(0.8 * sx, 0, "+", color=DIM, ms=9)
    leader(ax, (0.8, 0.3), (1.6, 1.6), f"cup: 60° included, apex 1.000 above the datum,\naxis leans 13.3–13.6° (compound; cut on the printed\nwedge fixture, station L/R) · Ø{T.APEX_HOLE_D:.2f} apex hole\nfrom apex +0.62 to apex −0.50")
    leader(ax, (0, 0), (-2.4, -1.5), "underside: Ø0.504 × 0.12 register\n+ #7 drill 0.70, tap 1/4-20 × 0.60\n(spigot bolt, on the centreline)")
    # outside face view: look along -z from +z, up = +y
    ax = fig.add_axes([0.52, 0.50, 0.44, 0.40])
    draw_view(ax, blk, (0, 0, 1), (0, 1, 0), "OUTSIDE FACE (Op2, block on its inside face, no fixture)")
    ax.set_xlim(-2.6, 2.6); ax.set_ylim(-0.8, 2.9)
    dim(ax, (-Tt / 2, 0), (Tt / 2, 0), -0.35, f"{Tt:.2f}")
    dim(ax, (Tt / 2, 0), (Tt / 2, Hh), 0.35, f"{Hh:.2f}", vertical=True)
    dim(ax, (-Tt / 2, 0), (-Tt / 2, 1.0 + T.GIB_Z), -0.45, f"{1.0 + T.GIB_Z:.3f} to the gib bore axis", vertical=True)
    dim(ax, (-0.8, 1.0 + T.GIB_Z), (0.8, 1.0 + T.GIB_Z), 0.9, "1.600")
    diam(ax, (-0.8, 1.0 + T.GIB_Z), T.GIB_D / 2, f"Ø{T.GIB_D:.3f} × {T.GIB_BORE_DEPTH:.2f} deep (×2)\nhelical with a 1/4 flat, LOC ≥ 1.3", ang=215, L=0.7)
    diam(ax, (0.8 + 0.55, 1.0 + T.GIB_Z), 0.068, "#8-32 tap drill (0.136) × 0.40 (×4)\nat ±0.55 from each bore", ang=-70, L=0.9)
    leader(ax, (-0.8, 1.0), (-2.3, 2.6), "+ = cup apex (inside, 1.0 above the datum)")
    # underside view: look up (+y), up = +z (outside face at the top)
    ax = fig.add_axes([0.04, 0.06, 0.30, 0.40])
    draw_view(ax, blk, (0, -1, 0), (0, 0, 1), "UNDERSIDE (Op5): register + spigot bolt tap")
    ax.set_xlim(-2.6, 2.6); ax.set_ylim(-1.9, 1.9)
    diam(ax, (0, 0), T.SPIGOT_PILOT_D / 2, f"Ø{T.SPIGOT_PILOT_D + 0.004:.3f} × 0.12 register", ang=30, L=0.9)
    diam(ax, (0, 0), 0.1, "#7 (0.201) × 0.70, tap 1/4-20 × 0.60", ang=-120, L=1.0)
    # section A-A through one cup along the radial direction: slab at x = +0.8 (t = -0.8 side)
    ax = fig.add_axes([0.36, 0.06, 0.60, 0.40])
    slab = cq.Workplane("XY").box(0.02 * IN, 20 * IN, 20 * IN).translate((-0.8 * IN, 0, 0))
    half = cq.Workplane("XY").box(20 * IN, 20 * IN, 20 * IN).translate((10 * IN - 0.8 * IN, 0, 0))   # keep x > -0.8
    sec_parts = []
    for k, c in (("block", INK), ("knobs", "#c0392b"), ("pads", "#8e6b1e")):
        s = P[k].intersect(slab)
        for f in s.faces().vals():
            for w in f.Wires():
                pts = []
                for e in w.Edges():
                    n = 1 if e.geomType() == "LINE" else 24
                    pts += [(p.z / IN, p.y / IN) for p in e.positions([i / n for i in range(n + 1)], mode="length")]
                sec_parts.append((pts, c))
    for pts, c in sec_parts:
        xs, ys = zip(*pts); ax.plot(xs, ys, color=c, lw=0.9)
    ax.set_aspect("equal"); ax.axis("off")
    ax.set_title("SECTION through the left cup, radial plane (x = tangential −0.8): +z = outside face. red = gib, plate, knob; brown = head screw", fontsize=9, loc="left", fontweight="bold")
    ax.set_xlim(-1.6, 3.2); ax.set_ylim(-0.4, 2.6)
    dim(ax, (-Rr / 2, 0), (Rr / 2, 0), -0.25, f"{Rr:.2f}")
    dim(ax, (Rr / 2, 0), (Rr / 2, 1.0), 0.25, "1.000 apex", vertical=True)
    dim(ax, (Rr / 2, 1.0), (Rr / 2 - T.GIB_BORE_DEPTH, 1.0), 0.55, f"{T.GIB_BORE_DEPTH:.2f} bore depth")
    leader(ax, (Rr / 2 + 0.3, 1.0), (2.0, 2.3), f"1/4-20 × 1-3/4 stud knob Ø{T.KNOB_D} through the\n1/8 steel plate (PEM nut); tip captive in the gib")
    leader(ax, (0.0, 0.7), (-1.5, 2.3), "1/4-20 × 1 SHCS head-down in the plug nose\n+ 1/4 spherical washer set; gib wedges under it")
    notes(fig, [
        "Datum: stub top centre (block underside centre). t = tangential, r = radial (+ = outside face), u = up.",
        "Op1 square the stock  ·  Op2 outside face up: gib bores + tap drills (socket_op2_gib_bores.nc)  ·  Op3/Op4 cups + apex holes on the",
        "printed wedge fixtures (socket_*_L/R.nc)  ·  Op5 underside: register + tap  ·  tap #8-32 ×4 and 1/4-20 ×1 by hand.",
        "Cone contact after the apex hole: r 0.35–0.62 on the 60° cup. The screw leans 13° while the gib is horizontal: spherical washer, not flat.",
        "Preload: 5 in-lb on the knob → ~100 lb push → ~200–300 lb pull through the 8° wedge (self-locking). Poles see ≤ 27 lb tension.",
    ], y=0.045)
    pdf.savefig(fig); fig.savefig(os.path.join(OUT, "sheet1_socket_block.png"), dpi=110); plt.close(fig)


def sheet_gib(pdf):
    g = gib_local(); pl = plate_local()
    fig = plt.figure(figsize=(17, 11))
    title_block(fig, "Gib pin and retainer plate (gib clamp)", "gib: O1 drill rod 5/8; plate: 1/8 steel", "6 + 6", "sheet 2/4")
    ax = fig.add_axes([0.04, 0.52, 0.55, 0.38])
    draw_view(ax, g, (0, 0, 1), (0, 1, 0), "GIB, side view (tip at the right; wedge flat on the underside; slot through, vertical)")
    ax.set_xlim(-0.6, 2.0); ax.set_ylim(-0.9, 0.9)
    dim(ax, (0, -T.GIB_D / 2), (T.GIB_L, -T.GIB_D / 2), -0.3, f"{T.GIB_L:.2f}")
    dim(ax, (T.GIB_L, -T.GIB_D / 2), (T.GIB_L, T.GIB_D / 2), 0.3, f"Ø{T.GIB_D:.3f}", vertical=True)
    dim(ax, (T.GIB_L - 0.6, T.GIB_D / 2), (T.GIB_L, T.GIB_D / 2), 0.25, "0.60 slot")
    leader(ax, (T.GIB_L - 0.35, -0.154), (1.0, -0.75), f"wedge flat: {T.GIB_ANGLE_DEG:.0f}° rising toward the tip; 0.154 below the axis\nat 0.35 from the tip (= washer top, engaged)")
    leader(ax, (0.15, 0), (-0.5, 0.7), "rear: Ø0.26 × 0.35 for the knob stud tip,\n1/16 cross pin at 0.20 through a 0.09 groove in the stud")
    ax = fig.add_axes([0.62, 0.52, 0.34, 0.38])
    draw_view(ax, g, (1, 0, 0), (0, 1, 0), "GIB, end view from the tip")
    ax.set_xlim(-0.8, 0.8); ax.set_ylim(-0.8, 0.8)
    dim(ax, (-T.GIB_SLOT / 2, T.GIB_D / 2), (T.GIB_SLOT / 2, T.GIB_D / 2), 0.25, f"{T.GIB_SLOT:.2f} slot")
    leader(ax, (T.GIB_SLOT / 2 + 0.07, -0.3), (0.6, -0.6), "tines 0.14 thick: bear on the\nspherical washer's seat")
    ax = fig.add_axes([0.04, 0.08, 0.45, 0.38])
    draw_view(ax, pl, (0, 0, 1), (0, 1, 0), "RETAINER PLATE, face view")
    ax.set_xlim(-1.2, 1.2); ax.set_ylim(-1.0, 1.0)
    dim(ax, (-T.PLATE_W / 2, -T.PLATE_H / 2), (T.PLATE_W / 2, -T.PLATE_H / 2), -0.25, f"{T.PLATE_W:.2f}")
    dim(ax, (T.PLATE_W / 2, -T.PLATE_H / 2), (T.PLATE_W / 2, T.PLATE_H / 2), 0.25, f"{T.PLATE_H:.2f}", vertical=True)
    dim(ax, (-0.55, T.PLATE_H / 2), (0.55, T.PLATE_H / 2), 0.25, "1.100")
    diam(ax, (0, 0), 0.13, "Ø0.26: press a 1/4-20 PEM nut (or tap + Loctite insert)", ang=-60, L=0.5)
    diam(ax, (-0.55, 0), 0.085, "Ø0.17 ×2: #8-32 × 1/2 into the block face", ang=120, L=0.4)
    notes(fig, [
        "Gib: cut 1.20 from 5/8 drill rod; mill the 0.34 slot 0.60 deep from the tip and the 8° flat along the whole underside with the rod in a V-block on the",
        "AltMill (flat 0.105 below the axis at the tip, 0.154 at 0.35 from the tip = the contact when engaged, 0.27 at the rear). The round top and sides guide it in the bore.",
        "Released: tip 0.80 in from the face (head passes). Engaged: tip ~1.15 in. Travel 0.35 = ~7 turns of the 1/4-20 knob.",
        "If a tightened joint will not release with a tap after the knob is backed off, recut the wedge at 10° (20% less pull, still > 150 lb).",
    ], y=0.07)
    pdf.savefig(fig); fig.savefig(os.path.join(OUT, "sheet2_gib_and_plate.png"), dpi=110); plt.close(fig)


def sheet_plug(pdf):
    plug, screw = plug_local()
    fig = plt.figure(figsize=(17, 11))
    title_block(fig, "Cone plug (bonded into each carbon pole's base end)", "6061 from 1-3/8 round bar (Vortex rotary, continuous spiral)", "6 (+ 6 pair-end plugs are plain spigots)", "sheet 3/4")
    ax = fig.add_axes([0.04, 0.12, 0.60, 0.78])
    draw_view(ax, plug.union(screw), (0, 0, 1), (0, 1, 0), "SIDE VIEW, pole axis vertical; cup apex at y = 0; head screw fitted")
    ax.set_xlim(-2.2, 2.4); ax.set_ylim(-0.8, 3.6)
    y_sh = T.S_SHOULDER
    dim(ax, (-T.POLE_OD / 2, y_sh + T.SHOULDER_L), (T.POLE_OD / 2, y_sh + T.SHOULDER_L), 0.25, f"Ø{T.POLE_OD:.3f} shoulder (= tube OD)")
    dim(ax, (-(T.BORE / 2 - 0.003), 3.4), ((T.BORE / 2 - 0.003), 3.4), 0.0, f"Ø{T.BORE - 0.006:.3f} shank (tube ID − 0.006; re-cut to the measured tube)")
    dim(ax, (-T.NOSE_D / 2, T.S_NOSE), (T.NOSE_D / 2, T.S_NOSE), -0.45, f"Ø{T.NOSE_D:.2f} nose")
    dim(ax, (1.0, T.S_NOSE), (1.0, y_sh), 0.0, f"{y_sh - T.S_NOSE:.3f} cone (60° incl.)", vertical=True)
    dim(ax, (1.0, y_sh), (1.0, y_sh + T.SHOULDER_L), 0.0, f"{T.SHOULDER_L:.2f}", vertical=True)
    dim(ax, (1.0, y_sh + T.SHOULDER_L), (1.0, y_sh + T.SHOULDER_L + T.SHANK_L), 0.0, f"{T.SHANK_L:.2f} shank", vertical=True)
    dim(ax, (-1.0, 0), (-1.0, T.S_NOSE), 0.0, f"{T.S_NOSE:.3f} apex→nose", vertical=True)
    leader(ax, (0, T.S_NOSE + 0.3), (-2.0, 2.4), "1/4-20 tap × 0.55 deep on the axis\n(#7 drill 0.70): head screw")
    leader(ax, (0.19, -0.25), (1.4, -0.6), "1/4-20 × 1 SHCS head-down,\n1/4 spherical washer set on the head")
    ax2 = fig.add_axes([0.66, 0.35, 0.30, 0.45])
    draw_view(ax2, plug, (0, -1, 0), (0, 0, 1), "END VIEW from the nose")
    ax2.set_xlim(-0.9, 0.9); ax2.set_ylim(-0.9, 0.9)
    notes(fig, [
        "Turn as one continuous spiral on the Vortex (A one way, X/Z following nose → cone → shoulder → shank); rough in depth passes, one finish pass.",
        "Bond 1.75 shank into the tube with structural epoxy (DP420); the shoulder stops against the tube end. Cone seats in the 60° cup from r 0.35 to 0.62.",
        "The geometric apex (y = 0) is the truss node; the nose face sits 0.346 above it. Pole node-to-node 37.30 / 37.35 sets the tube cut length (35.87 / 35.92).",
    ], y=0.10)
    pdf.savefig(fig); fig.savefig(os.path.join(OUT, "sheet3_cone_plug.png"), dpi=110); plt.close(fig)


def sheet_rollers(pdf):
    G = json.load(open("out/params.json"))["rocker"]
    fig = plt.figure(figsize=(17, 11))
    title_block(fig, "Roller blocks (alt: saddle on the wall; az: hung through the floor)", "6061 from 1-1/2 × 2 bar, faced 1.40 wide", "4 alt + 4 az", "sheet 4/4")
    for col, (h, saddle, name) in enumerate(((G["blk_h_alt"], True, "ALT block"), (G["blk_h_az"], False, "AZ block"))):
        b, r, a = rocker.roller_block(G, h, saddle)
        x0 = 0.04 + col * 0.48
        ax = fig.add_axes([x0, 0.52, 0.22, 0.38])
        draw_view(ax, b, (0, 1, 0), (0, 0, 1), f"{name}: end view (X = roller axis)")
        ax.set_xlim(-1.5, 1.5); ax.set_ylim(-h - 0.9, 0.9)
        dim(ax, (-G["blk_w"] / 2, -h), (G["blk_w"] / 2, -h), -0.3, f"{G['blk_w']:.2f}")
        dim(ax, (-G["slot_w"] / 2, 0), (G["slot_w"] / 2, 0), 0.3, f"{G['slot_w']:.2f} slot × {G['slot_d']:.2f} deep")
        dim(ax, (G["blk_w"] / 2, 0), (G["blk_w"] / 2, -G["axle_from_top"]), 0.3, f"{G['axle_from_top']:.2f}", vertical=True)
        dim(ax, (G["blk_w"] / 2, -h), (G["blk_w"] / 2, 0), 0.75, f"{h:.2f}", vertical=True)
        if saddle:
            dim(ax, (-(G["ply"] + 0.02) / 2, -h), ((G["ply"] + 0.02) / 2, -h), -0.65, f"{G['ply'] + 0.02:.2f} saddle × {G['saddle_d']:.2f} deep (wall)")
        ax = fig.add_axes([x0 + 0.24, 0.52, 0.22, 0.38])
        draw_view(ax, b, (1, 0, 0), (0, 0, 1), f"{name}: side view (Y = along the track)")
        ax.set_xlim(-1.5, 1.5); ax.set_ylim(-h - 0.9, 0.9)
        dim(ax, (-G["blk_l"] / 2, -h), (G["blk_l"] / 2, -h), -0.3, f"{G['blk_l']:.2f}")
        diam(ax, (0, -G["axle_from_top"]), G["axle_d"] / 2, f"Ø{G['axle_d']:.3f} through (5/8 × 1 shoulder bolt;\nfar cheek tapped 1/2-13)", ang=-35, L=0.4)
        if saddle:
            dim(ax, (-0.6, -h + G["saddle_d"] - 0.30), (0.6, -h + G["saddle_d"] - 0.30), -0.9, "1.20: Ø0.26 ×2 cross holes (1/4-20 × 2 through the wall)")
        else:
            dim(ax, (-0.6, -h), (0.6, -h), -0.75, "1.20 × 0.92: 4× #10-32 tapped 0.6 into the cheeks' upper face (flange plate)")
        ax = fig.add_axes([x0, 0.08, 0.46, 0.40])
        draw_view(ax, b, (0, 0, 1), (0, 1, 0), f"{name}: top (slot and roller)")
        ax.set_xlim(-1.4, 1.4); ax.set_ylim(-1.0, 1.0)
    notes(fig, [
        "Frame: X = roller axis (block width 1.40), Y = tangential along the track (2.00), Z = toward the track. Roller R10 5/8 × 1-3/8 × 11/32 on a 5/8 × 1 shoulder bolt,",
        "bolt head outboard (alt) / radially outboard (az, the floor cutout is 0.5 wider on that side). Roller protrudes 0.24 past the block top.",
        "Alt: block saddles the wall top in its notch (wall top at R + 2.0), two 1/4-20 × 2 cross bolts; 1/8 Al + 1/16 PTFE tab on the outer face as the lateral stop.",
        "Az: roller side DOWN; block hangs through a 1.94 × 2.04 floor cutout, 0.79 below the floor, under a 1/8 flange plate (2.4 × 3.0) on 4× #10-32.",
    ], y=0.06)
    pdf.savefig(fig); fig.savefig(os.path.join(OUT, "sheet4_roller_blocks.png"), dpi=110); plt.close(fig)


if __name__ == "__main__":
    with PdfPages(os.path.join(OUT, "all_sheets.pdf")) as pdf:
        sheet_socket(pdf)
        sheet_gib(pdf)
        sheet_plug(pdf)
        sheet_rollers(pdf)
    print("wrote", OUT)
