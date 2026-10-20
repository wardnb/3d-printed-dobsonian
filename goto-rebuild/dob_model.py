"""
Parametric model of the 16" f/4 GoTo Dobsonian rebuild.

All inputs are in INCHES in the PARAMS block. Values marked ASSUMED are
placeholders until Nick measures the real parts; change them and re-run.

Outputs (in ./out):
  base.glb          ground board, rocker, az drive, alt drive (fixed frame)
  tube.glb          everything that tilts in altitude, modelled pointing
                    horizontally (+Y) with the altitude axis at the origin
  dob16_alt45.step  whole scope at 45 deg altitude, millimetres, for Fusion
  params.json       resolved dimensions + checks for the web viewer
"""
import json
import math
import os

import cadquery as cq

IN = 25.4  # mm per inch; the model is built in mm

# --------------------------------------------------------------------------
# PARAMS (inches, pounds)
# --------------------------------------------------------------------------
P = dict(
    # Optics (known)
    aperture=16.0,
    focal_ratio=3.9,          # Nick: mirror is about f/3.9 (confirm from Hubble test report ROC)
    secondary_minor=3.5,
    L_secondary_to_focus=11.9,
    # Primary mirror (ASSUMED until measured)
    mirror_dia=16.0,          # Hubble Optics 16" f/4 sandwich: 406 mm
    mirror_thick=1.65,        # 42 mm (Hubble Optics spec)
    mirror_lb=23.1,           # 10.5 kg (Hubble Optics spec)
    # Mirror cage as built by DobStuff (measured 2026-10-18, see docs/measurements.md)
    mirror_face_below_axis=None,  # None = solve for balance (the as-built axis is ~7" above the mirror face)
    alt_bearing_radius=14.0,      # DESIGN: rebuilt bearings (as-built DobStuff D is 12 3/16" radius)
    mcage_ring_od=21.5,           # wooden_cage.step: the front quadrants are r 10.75 arcs and the bearing-side flats are at x = +/-10.75
    mcage_flat_back_z=6.49,       # the flats run from the bearing axis to 6.49" behind it
    mcage_back_arc_r=15.706,      # the back is one broad arc, centred 4.96" ahead of the ring centre (corners at r 12.56)
    mcage_back_arc_cz=4.96,
    mcage_point_radius=12.125,    # from Nick's wooden_cage.step (tip 12.125" from the ring centre); agrees with 10.25" hole + 1 13/16" to the tip
    mcage_flat_half_width=10.13,  # measured: 21 11/16" across the side strips' outer faces, minus the 18 mm strip
    mcage_ring_id=18.0,           # measured
    mcage_top_above_mirror=7.0,   # measured: top ring's top face above the mirror face
    mcage_height=12.8,            # measured: 11 3/8" between the boards + two 18 mm boards
    cell_depth=3.0,               # measured: mirror face down to the bottom of the cell triangle
    # Rocker / ground board (ASSUMED)
    rocker_disc_dia=30.0,         # ASSUMED: round rocker floor, az drive edge
    rocker_width=26.5,            # ASSUMED
    ground_foot_radius=17.0,      # ASSUMED
    ply=0.709,                    # 18 mm Baltic birch
    # Upper cage (design)
    ring_id=17.5,
    ring_od=20.5,
    ring_thick=0.375,             # from upper_cage.py (v2: 3/8" solid rings)
    ring_spacing=8.25,
    board_inner_from_axis=8.75,
    focuser_racked_in=1.405,      # Feather Touch 2" spec
    # Truss (design)
    truss_pole_od=1.25,           # DECIDED 2026-10-18: 1.25" x 0.062" roll-wrapped carbon poles
    truss_top_radius=9.6,
    truss_bottom_radius=10.68,    # narrow-pair layout only (historical); the stubs use mcage_tube_radii
    mcage_tube_od=1.772,          # measured 2026-10-19 (calipers): DobStuff struts 45 mm OD x 40 mm ID, ring holes 45 mm
    mcage_tube_wall=0.098,        # 2.5 mm wall
    mcage_tube_angles=(90, 210, 330),   # point hole at 90 (square to the bearings), back holes 30 deg off the bearing axis
    mcage_tube_radii=(10.25, 10.625, 10.625),   # from wooden_cage.step pilot holes: back holes 18.5" apart, 18.0" to the point hole
    mcage_spacer_od=1.25,         # measured: seven short tubes between the two rings
    mcage_spacer_angles=(20, 40, 140, 160, 260, 270, 280),   # six from wooden_cage.step (r 9.875); 270 is the seventh Nick counted at the back, position ASSUMED
    stub_proud=1.0,               # stub tubes stand this far above the top ring; sockets plug into them
    # Masses for balance (ASSUMED)
    cell_lb=6.0, mcage_lb_per_in=1.1, bearings_lb=9.0, poles_lb=3.6,   # six 1.25" x 0.062" carbon poles, ~38.5" at 0.48 lb + plugs
    upper_cage_lb=14.0, eyepiece_lb=3.3,   # cage v2 11.3 lb + wire spider 1.3 + Waypoint 1.4 (cage hub not yet included); 31 Nagler + Paracorr
)

ASSUMED = [k for k in P if k in (
    "mirror_dia", "mirror_thick", "mirror_lb", "mirror_face_below_axis",
    "rocker_disc_dia", "rocker_width",
    "ground_foot_radius")]

# --------------------------------------------------------------------------
# Derived geometry (inches)
# --------------------------------------------------------------------------
FL = P["aperture"] * P["focal_ratio"]
R = P["alt_bearing_radius"]
y_sec_rel = FL - P["L_secondary_to_focus"]          # secondary above mirror face


def net_moment(s_):
    """lb-in about the altitude axis for mirror face s_ below it (+ = top heavy)."""
    top = -s_ + P["mcage_top_above_mirror"]
    bot = top - P["mcage_height"]
    mc_len = top - bot
    ring_lo = y_sec_rel - s_ - 4.5
    m = [
        (P["mirror_lb"], -s_ - P["mirror_thick"] / 2),
        (P["cell_lb"], -s_ - P["mirror_thick"] - 1.0),
        (P["mcage_lb_per_in"] * mc_len, (top + bot) / 2),
        (P["bearings_lb"], -4 * R / (3 * math.pi)),
        (P["poles_lb"], (top + ring_lo) / 2),
        (P["upper_cage_lb"], y_sec_rel - s_),
        (P["eyepiece_lb"], y_sec_rel - s_),
    ]
    return sum(a * b for a, b in m), sum(a for a, _ in m)


s_dobstuff = 8.0
net_dobstuff, _ = net_moment(s_dobstuff)
if P["mirror_face_below_axis"] is None:
    lo, hi = 4.0, 30.0
    for _ in range(60):
        mid = (lo + hi) / 2
        lo, hi = (mid, hi) if net_moment(mid)[0] > 0 else (lo, mid)
    s = round(lo, 2)
else:
    s = P["mirror_face_below_axis"]
y_mirror = -s
y_sec = FL - P["L_secondary_to_focus"] - s          # secondary centre
import upper_cage as _uc
y_ring_lo = y_sec - (_uc.I["ring_gap"] / 2 + _uc.T)   # lower ring outer face (7.5" gap + two 3/8" rings)
y_ring_hi = y_sec + (_uc.I["ring_gap"] / 2 + _uc.T)   # upper ring outer (sky) face
y_mcage_top = -s + P["mcage_top_above_mirror"]       # top ring's top face (below the axis in the rebuild)
y_mcage_bot = y_mcage_top - P["mcage_height"]          # mirror board's bottom face
mc_r = P["mcage_ring_od"] / 2

# swing radius of the lower tube and the altitude axis height that clears it
mcage_corner_r = math.hypot(P["mcage_ring_od"] / 2, P["mcage_flat_back_z"])          # back corners, 12.56"
swing = math.hypot(-y_mcage_bot, max(P["mcage_point_radius"], mcage_corner_r))
ground_top = 1.5 + 0.75                           # feet + ground board + az drive ring
rocker_floor_top = ground_top + 0.15 + P["ply"]   # PTFE + rocker floor
z_alt = rocker_floor_top + swing + 0.5

# bearing / rocker x positions
panel_x = P["mcage_flat_half_width"]              # side strip inner face, on the ring's flat
bearing_x = panel_x + P["ply"] + P["ply"] / 2     # bearing mid-plane
rocker_wall_in = bearing_x + P["ply"] / 2 + 0.6
rw = P["rocker_width"] / 2

# truss
tops = [30, 150, 270]             # pair blocks under the lower ring (upper_cage.APEX)
bots = [0, 60, 120, 180, 240, 300]


def polar(r, deg):
    a = math.radians(deg)
    return r * math.cos(a), r * math.sin(a)        # (x, z) around the tube axis


def base_xz(deg):
    """(x, z) of the stub tube at angle deg (the three socket positions, from the STEP)."""
    d = deg % 360
    for a, r in zip(P["mcage_tube_angles"], P["mcage_tube_radii"]):
        if abs((d - a + 180) % 360 - 180) < 1:
            return polar(r, a)
    return polar(P["truss_bottom_radius"], deg)


truss = []
for k, t in enumerate(tops):
    tx, tz = polar(P["truss_top_radius"], t)
    for b in (t - 30, t + 30):
        bx, bz = polar(P["truss_bottom_radius"], b)
        truss.append(((bx, y_mcage_top + P["stub_proud"] + 0.6, bz), (tx, y_ring_lo - 0.6, tz)))
pole_len = math.dist(*truss[0])

# alternative: zigzag (octahedral) truss, lower nodes shared by neighbouring pairs
zig_bots = list(P["mcage_tube_angles"])    # shared sockets on the three stub tubes
truss_zig = []
for t in tops:
    tx, tz = polar(P["truss_top_radius"], t)
    for b in (t - 60, t + 60):
        bx, bz = base_xz(b)
        truss_zig.append(((bx, y_mcage_top + P["stub_proud"] + 0.6, bz), (tx, y_ring_lo - 0.6, tz)))
pole_len_zig = math.dist(*truss_zig[0])

net, tube_lb = net_moment(s)
cw_arm = -(y_mcage_bot + 0.5)
counterweight = max(0.0, net / cw_arm)
cw_dobstuff = net_dobstuff / (s_dobstuff + P["cell_depth"] + 0.5)
eyepiece_zenith = z_alt + y_sec
nested_height = P["ply"] + (y_mcage_top - y_mcage_bot)

# drive ratios
# belt-on-rim drives (SiTech style): GT2 belt glued teeth-out round the bearing arc / ground ring,
# 20T pinion (0.5" pitch dia) on a 2:1 reduction from the gearbox (16:32)
PINION_PD, STAGE = 0.5, 2
alt_ratio = ((R + 0.06) / (PINION_PD / 2)) * STAGE
az_ratio = ((P["rocker_disc_dia"] / 2 + 0.06) / (PINION_PD / 2)) * STAGE


# --------------------------------------------------------------------------
# helpers (inputs in inches, output solids in mm)
# --------------------------------------------------------------------------
def v(*a):
    return cq.Vector(*[x * IN for x in a])


def box(cx, cy, cz, sx, sy, sz):
    return cq.Workplane("XY").box(sx * IN, sy * IN, sz * IN).translate(v(cx, cy, cz))


def ring_y(y0, thick, rin, rout):
    """Annulus around the Y (optical) axis, from y0 to y0+thick."""
    w = cq.Workplane("XZ").circle(rout * IN)
    if rin:
        w = w.circle(rin * IN)
    # XZ workplane extrudes toward -Y; flip so it grows +Y from y0
    return w.extrude(-thick * IN).translate(v(0, y0, 0))


def shield_y(y0, thick, rin):
    """The DobStuff ring outline from wooden_cage.step: flats on the bearing sides, r 10.75 front arcs to a point
    at +Z, one broad arc across the back. Local XZ-workplane coords are (X, Z)."""
    fx, fz = P["mcage_ring_od"] / 2, P["mcage_flat_back_z"]
    tip = P["mcage_point_radius"]; ar, acz = P["mcage_back_arc_r"], P["mcage_back_arc_cz"]
    # front arc meets the point line where the STEP puts it: (4.97, 9.53) on the r 10.75 circle
    pa = math.atan2(9.53, 4.97); qx, qz = fx * math.cos(pa), fx * math.sin(pa)
    ma = (pa + 0) / 2; mx, mz = fx * math.cos(ma), fx * math.sin(ma)
    w = (cq.Workplane("XZ").moveTo(fx * IN, 0).lineTo(fx * IN, -fz * IN)
         .threePointArc((0, (acz - ar) * IN), (-fx * IN, -fz * IN))
         .lineTo(-fx * IN, 0).threePointArc((-mx * IN, mz * IN), (-qx * IN, qz * IN))
         .lineTo(0, tip * IN).lineTo(qx * IN, qz * IN).threePointArc((mx * IN, mz * IN), (fx * IN, 0)).close())
    if rin:
        w = w.circle(rin * IN)
    return w.extrude(-thick * IN).translate(v(0, y0, 0))


def cyl_y(y0, length, r, x=0, z=0):
    return cq.Workplane("XZ").circle(r * IN).extrude(-length * IN).translate(v(x, y0, z))


def cyl_x(x0, length, r, y=0, z=0):
    return cq.Workplane("YZ").circle(r * IN).extrude(length * IN).translate(v(x0, y, z))


def cyl_z(z0, length, r, x=0, y=0):
    return cq.Workplane("XY").circle(r * IN).extrude(length * IN).translate(v(x, y, z0))


def rod(p0, p1, r):
    a, b = cq.Vector(*[c * IN for c in p0]), cq.Vector(*[c * IN for c in p1])
    d = b - a
    solid = cq.Solid.makeCylinder(r * IN, d.Length, a, d.normalized())
    return cq.Workplane("XY").add(solid)


def d_bearing(x_mid, thick, r_out, r_in):
    """Half-disc altitude bearing in the YZ plane, flat edge on the axis
    plane y=0, curved side toward the mirror (-Y)."""
    w = (cq.Workplane("YZ")
         .moveTo(0, -r_out * IN).threePointArc((-r_out * IN, 0), (0, r_out * IN))
         .close())
    solid = w.extrude(thick * IN)
    cut = (cq.Workplane("YZ")
           .moveTo(-1.2 * IN, -r_in * IN)
           .threePointArc((-r_in * IN, 0), (-1.2 * IN, r_in * IN))
           .close().extrude(thick * IN))
    return solid.cut(cut).translate(v(x_mid - thick / 2, 0, 0))


BIRCH = cq.Color(0.86, 0.72, 0.50)
ALU = cq.Color(0.74, 0.76, 0.79)
BLACK = cq.Color(0.12, 0.12, 0.13)
EBONY = cq.Color(0.05, 0.05, 0.05)
PTFE = cq.Color(0.95, 0.95, 0.93)
MIRROR = cq.Color(0.70, 0.85, 0.95)
MOTOR = cq.Color(0.30, 0.31, 0.33)
STRIP = cq.Color(0.80, 0.45, 0.20)
ELEC = cq.Color(0.20, 0.35, 0.55)

# --------------------------------------------------------------------------
# TUBE assembly (tilts). Local frame: alt axis = X, optical axis = +Y.
# --------------------------------------------------------------------------
tube = cq.Assembly(name="tube")

# primary mirror + cell
tube.add(cyl_y(y_mirror - P["mirror_thick"], P["mirror_thick"], P["mirror_dia"] / 2),
         name="primary_mirror", color=MIRROR)
cell = ring_y(y_mirror - P["mirror_thick"] - 1.6, 0.25, 0, P["mirror_dia"] / 2 - 0.3)
for a in (90, 210, 330):
    x, z = polar(5.5, a)
    cell = cell.union(box(x, y_mirror - P["mirror_thick"] - 0.7, z, 2.4, 1.6, 0.5))
tube.add(cell, name="mirror_cell_9pt", color=ALU)

# mirror cage as DobStuff built it (measured 2026-10-18): an 18 mm shield-shaped top ring and mirror board,
# seven 1.25" spacer tubes between them, a narrow 18 mm strip on each side that the bearings bolt to (no
# side panels, strips flush with the ring flats), and three 45 mm holes at the STEP pilot positions for the strut tubes. For the truss, short stubs
# of those tubes stay in place and the socket blocks plug into their tops.
mc = shield_y(y_mcage_bot, P["ply"], P["mcage_ring_id"] / 2)                             # mirror board
mc = mc.union(shield_y(y_mcage_top - P["ply"], P["ply"], P["mcage_ring_id"] / 2))         # top ring
for sx in (-1, 1):                                                                       # bearing side strips
    mc = mc.union(box(sx * (panel_x + P["ply"] / 2), (y_mcage_top + y_mcage_bot) / 2, 0,
                      P["ply"], y_mcage_top - y_mcage_bot, 3.0))
tubes = None
for a in P["mcage_spacer_angles"]:                                                       # seven short tubes
    x, z = polar(mc_r - 0.8, a)
    t_ = cyl_y(y_mcage_bot + P["ply"], y_mcage_top - y_mcage_bot - 2 * P["ply"], P["mcage_spacer_od"] / 2, x, z)
    tubes = t_ if tubes is None else tubes.union(t_)
for a in P["mcage_tube_angles"]:                                                         # three stub tubes
    x, z = base_xz(a)
    t_ = cyl_y(y_mcage_bot, y_mcage_top - y_mcage_bot + P["stub_proud"], P["mcage_tube_od"] / 2, x, z)
    tubes = t_ if tubes is None else tubes.union(t_)
tube.add(tubes, name="mirror_cage_tubes", color=cq.Color(0.72, 0.73, 0.75))
tube.add(mc, name="mirror_cage", color=BIRCH)

# trusses are separate assemblies so the viewer can swap them
def truss_assy(name, poles_list, bottom_angles, blk_w):
    a = cq.Assembly(name=name)
    blocks = None
    for b in bottom_angles:
        x, z = base_xz(b)
        # socket block: blk_w tangential x 1.6 radial x 1.2 tall, square to the radius, on the tube top
        y_top = y_mcage_top + P["stub_proud"]
        blk = (cq.Workplane("XY").box(1.6 * IN, 1.2 * IN, blk_w * IN)
               .rotate((0, 0, 0), (0, 1, 0), -b).translate(v(x, y_top + 0.6, z)))
        blk = blk.union(cyl_y(y_top - 1.5, 1.5, P["mcage_tube_od"] / 2 - P["mcage_tube_wall"] - 0.003, x, z))   # spigot into the stub bore
        blocks = blk if blocks is None else blocks.union(blk)
    a.add(blocks, name="truss_sockets_lower", color=ALU)
    poles = None
    for p0, p1 in poles_list:
        r_ = rod(p0, p1, P["truss_pole_od"] / 2)
        poles = r_ if poles is None else poles.union(r_)
    a.add(poles, name="truss_poles", color=BLACK)
    return a


truss_pairs = truss_assy("truss_pairs", truss, bots, 1.6)
truss_zigzag = truss_assy("truss_zigzag", truss_zig, zig_bots, 2.6)

# altitude bearings: drive side (+X) laminated, plain side (-X)
drive_b = d_bearing(bearing_x, P["ply"] * 2 + 0.25, R, R - 2.6)
plain_b = d_bearing(-bearing_x, P["ply"], R, R - 2.6)
tube.add(drive_b, name="alt_bearing_drive", color=BIRCH)
tube.add(plain_b, name="alt_bearing_plain", color=BIRCH)
# ebonystar running edges + encoder strip + cable groove on drive bearing
def rim(x_mid, width, r_out, r_in):
    w = (cq.Workplane("YZ").moveTo(0, -r_out * IN)
         .threePointArc((-r_out * IN, 0), (0, r_out * IN))
         .lineTo(0, r_in * IN).threePointArc((-r_in * IN, 0), (0, -r_in * IN)).close())
    return w.extrude(width * IN).translate(v(x_mid - width / 2, 0, 0))


tube.add(rim(-bearing_x, P["ply"], R + 0.06, R), name="ebony_plain", color=EBONY)
tube.add(rim(bearing_x - 0.45, 0.6, R + 0.06, R), name="ebony_drive", color=EBONY)
tube.add(rim(bearing_x + 0.25, 0.3, R + 0.04, R - 0.02), name="encoder_strip_alt", color=STRIP)
tube.add(rim(bearing_x + 0.62, 0.35, R + 0.09, R), name="alt_belt_on_rim", color=BLACK)   # GT2 belt, 9 mm, teeth out

# upper cage: detailed parts from upper_cage.py (machining v1)
import upper_cage
cage_parts, _, _ = upper_cage.build()
cage_colors = dict(ring_lower=ALU, ring_upper=ALU, struts=ALU, board_rails=ALU, focuser_board=ALU,
                   spider_blocks=BLACK, pair_connectors_concept=cq.Color(0.85, 0.55, 0.25),
                   finder_bracket=ALU, waypoint_finder=cq.Color(0.55, 0.12, 0.12))
for k, part in cage_parts.items():
    if k == "spider_blocks":
        continue                                   # spider towers live in the spider assemblies
    tube.add(part.translate(v(0, y_sec, 0)), name="cage_" + k, color=cage_colors[k])

# light baffle opposite the focuser (+X side): a thin curved panel on the ring ID spanning
# +/-60 deg, full height between the rings. The drawtube sees the far wall over ~+/-30 deg from
# its axis, which is +/-65 deg of the cage wall; the shroud closes what the panel does not.
_r_b = P["ring_id"] / 2 - 0.05
_baf = (cq.Workplane("XZ").circle(_r_b * IN).circle((_r_b - 0.03) * IN).extrude(-7.4 * IN)
        .translate((0, (y_sec - 3.7) * IN, 0)))
_wedge = (cq.Workplane("XZ").moveTo(0, 0).lineTo(12 * IN * math.cos(math.radians(60)), 12 * IN * math.sin(math.radians(60)))
          .lineTo(12 * IN, 0).lineTo(12 * IN * math.cos(math.radians(-60)), 12 * IN * math.sin(math.radians(-60))).close()
          .extrude(-8 * IN).translate((0, (y_sec - 4) * IN, 0)))
tube.add(_baf.intersect(_wedge), name="baffle", color=BLACK)

# Feather Touch on the board (board inner face at x = -8.75)
bx = -(P["board_inner_from_axis"] + 0.125)
foc = cyl_x(bx - 0.125 - 0.45, 0.45, 1.85, y=y_sec)                 # base
foc = foc.union(box(bx - 0.125 - 0.45 - 0.75, y_sec, 0, 1.5, 3.3, 3.3))  # body
foc = foc.union(cyl_x(bx - 0.125 - P["focuser_racked_in"] - 0.3, 0.6, 1.2, y=y_sec))  # drawtube
foc = foc.union(cyl_y(y_sec - 2.6, 5.2, 0.25, x=bx - 0.125 - 1.0, z=-1.9))  # knob shaft
for yk in (y_sec - 2.6, y_sec + 2.3):
    foc = foc.union(cyl_y(yk, 0.3, 0.75, x=bx - 0.125 - 1.0, z=-1.9))
tube.add(foc, name="feather_touch", color=BLACK)
tube.add(cyl_x(bx - 0.125 - P["focuser_racked_in"] - 2.6, 2.3, 1.1, y=y_sec),
         name="eyepiece", color=MOTOR)

# secondary mirror (elliptical flat at 45 deg) + holder + spider
minor = P["secondary_minor"]
# self-aligning secondary holder (secondary_holder.py): mirror bonded to a carrier in a jig,
# carrier dowelled to a 45-degree body, offset built in
import secondary_holder as sh
sh.P["focal_ratio"] = P["focal_ratio"]
sh.P["minor"] = P["secondary_minor"]
hparts = sh.build()
tube.add(hparts["secondary_mirror"].translate(v(0, y_sec, 0)), name="secondary_mirror", color=MIRROR)
tube.add(hparts["carrier"].translate(v(0, y_sec, 0)), name="secondary_carrier", color=ALU)
tube.add(hparts["body"].translate(v(0, y_sec, 0)), name="secondary_body", color=BLACK)
# Destiny option only: a 3/4" stalk from the holder body up to the spider hub (a 1/4" stalk
# this long would flex ~0.4 mm at the focal plane between horizon and zenith)
_stalk = cyl_y(y_sec + sh.P["body_top"], y_ring_hi + 0.875 - y_sec - sh.P["body_top"], 0.375)

vanes = cyl_y(y_ring_hi + 0.125, 1.5, 0.65)
for t in tops:
    tip = polar(P["ring_id"] / 2, t)
    hub = polar(0.6, t + 120)
    mid_ang = math.radians(t + 50)
    mid = (4.6 * math.cos(mid_ang), 4.6 * math.sin(mid_ang))
    arc = (cq.Workplane("XY").moveTo(hub[0] * IN, hub[1] * IN)
           .threePointArc((mid[0] * IN, mid[1] * IN), (tip[0] * IN, tip[1] * IN)))
    wire = arc.val()
    thick = cq.Workplane("XY").add(cq.Wire.assembleEdges([wire])).toPending().offset2D(0.03125 * IN)
    vane = thick.extrude(1.5 * IN)
    vane = vane.rotate((0, 0, 0), (1, 0, 0), 90)       # XY plane -> XZ, extrude -> -Y
    vanes = vanes.union(vane.translate(v(0, y_ring_hi + 1.625, 0)))
spider_curved = cq.Assembly(name="spider_curved")
spider_curved.add(vanes, name="destiny_curved_3vane", color=BLACK)
spider_curved.add(cage_parts["spider_blocks"].translate(v(0, y_sec, 0)), name="towers_curved", color=ALU)
spider_curved.add(_stalk, name="secondary_stalk", color=BLACK)

wire_parts, wire_runs = upper_cage.wire_spider()
spider_wire = cq.Assembly(name="spider_wire")
WIRE = cq.Color(0.85, 0.86, 0.88)
for k, col in (("hub", BLACK), ("wires", WIRE), ("studs", cq.Color(0.55, 0.57, 0.6)), ("extensions", ALU)):
    spider_wire.add(wire_parts[k].translate(v(0, y_sec, 0)), name="wire_" + k, color=col)

# quad spider (chosen): 0.020" stainless vanes on the quad towers, hub = holder top plate
quad_parts, quad_info = upper_cage.quad_spider()
spider_quad = cq.Assembly(name="spider_quad")
for k, col in (("hub", BLACK), ("vanes", WIRE), ("studs", cq.Color(0.55, 0.57, 0.6))):
    spider_quad.add(quad_parts[k].translate(v(0, y_sec, 0)), name="quad_" + k, color=col)

# --------------------------------------------------------------------------
# BASE assembly (fixed). World: ground at z=0, alt axis at (0,0,z_alt).
# --------------------------------------------------------------------------
base = cq.Assembly(name="base")

# ground board: three arms + feet + centre hub + PTFE pads
gb = cyl_z(0.75, 0.75, 4.0)
for a in (90, 210, 330):
    x, y = polar(P["ground_foot_radius"] / 2, a)
    arm = (cq.Workplane("XY").box(P["ground_foot_radius"] * IN, 3.5 * IN, 0.75 * IN)
           .rotate((0, 0, 0), (0, 0, 1), a).translate(v(x, y, 1.125)))
    gb = gb.union(arm)
tube_feet = None
for a in (90, 210, 330):
    x, y = polar(P["ground_foot_radius"] - 0.8, a)
    foot = cyl_z(0, 0.75, 1.0, x, y)
    tube_feet = foot if tube_feet is None else tube_feet.union(foot)
gb = gb.union(cyl_z(1.5, 0.75, P["rocker_disc_dia"] / 2).cut(cyl_z(1.5, 0.75, P["rocker_disc_dia"] / 2 - 2.0)))   # az drive ring
base.add(gb, name="ground_board", color=BIRCH)
base.add(tube_feet, name="feet", color=BLACK)
pads = None
for a in (90, 210, 330):
    x, y = polar(12.5, a)
    pad = box(x, y, ground_top + 0.075, 1.5, 1.5, 0.15)   # PTFE pads on the ground ring
    pads = pad if pads is None else pads.union(pad)
base.add(pads, name="az_ptfe", color=PTFE)

# rocker: round floor disc (az drive edge), two side walls, front/back boards
floor_z0 = ground_top + 0.15
rk = cyl_z(floor_z0, P["ply"], P["rocker_disc_dia"] / 2)
wall_top = z_alt - R * math.cos(math.radians(40)) + 0.3
wall_h = wall_top - rocker_floor_top
for sx in (-1, 1):
    rk = rk.union(box(sx * (rocker_wall_in + P["ply"] / 2), 0,
                      rocker_floor_top + wall_h / 2, P["ply"], P["rocker_width"], wall_h))
for sy in (-1, 1):
    rk = rk.union(box(0, sy * (rw - P["ply"] / 2), rocker_floor_top + 3.0,
                      2 * rocker_wall_in, P["ply"], 6.0))
base.add(rk, name="rocker", color=BIRCH)
base.add(cyl_z(1.52, 0.3, P["rocker_disc_dia"] / 2 + 0.03).cut(cyl_z(1.5, 1.0, P["rocker_disc_dia"] / 2 - 0.05)),
         name="encoder_strip_az", color=STRIP)        # magnetic tape on the lower 0.3" of the ground ring's rim

# altitude PTFE pads at +/-40 deg under each bearing
apads = None
for xm in (bearing_x, -bearing_x):
    for ang in (-40, 40):
        a = math.radians(ang)
        y = R * math.sin(a)
        z = z_alt - R * math.cos(a)
        blk = (cq.Workplane("XY").box(1.4 * IN, 1.6 * IN, 0.5 * IN)
               .rotate((0, 0, 0), (1, 0, 0), -ang)
               .translate(v(xm, y + 0.25 * math.sin(a), z - 0.25 * math.cos(a))))
        stand = box(xm + (0.9 if xm > 0 else -0.9), y, (z + rocker_floor_top) / 2,
                    0.5, 1.4, z - rocker_floor_top)
        part = blk.union(stand)
        apads = part if apads is None else apads.union(part)
base.add(apads, name="alt_ptfe_pads", color=PTFE)

# altitude drive: pinion under the drive bearing meshing with the rim belt, motor outside the wall
cap_z = z_alt - R - 0.09 - PINION_PD / 2
base.add(cyl_x(bearing_x + 0.45, 0.4, PINION_PD / 2, y=0, z=cap_z), name="alt_pinion", color=ALU)
base.add(cyl_x(bearing_x + 0.85, rocker_wall_in + P["ply"] + 1.2 - bearing_x - 0.85, 0.2, y=0, z=cap_z), name="alt_pinion_shaft", color=ALU)
m_x0 = rocker_wall_in + P["ply"] + 0.5
base.add(cyl_x(m_x0 + 0.3, 5.2, 0.75, y=0, z=cap_z - 2.6), name="alt_motor_GM9413", color=MOTOR)
base.add(box(m_x0 + 0.15, 0, cap_z - 1.3, 0.3, 2.4, 4.0), name="alt_belt_plate", color=ALU)
base.add(box(m_x0 - 0.3 - P["ply"] / 2 + 0.1, 0.0, z_alt - R + 0.4, 0.4, 1.0, 1.4),
         name="alt_read_head", color=ELEC)

# azimuth drive on the ground board: vertical motor, roller on the disc edge
az_ang = 300
rx, ry = polar(P["rocker_disc_dia"] / 2 + 0.09 + PINION_PD / 2, az_ang)
mx, my = polar(P["rocker_disc_dia"] / 2 + 2.2, az_ang)
# (rocker-mounted: the motor hangs from a bracket on the rocker floor's edge and its roller runs on the
#  ground ring's rim, so nothing crosses the azimuth axis; the read head for the az tape sits beside it)
base.add(cyl_z(1.85, 0.4, PINION_PD / 2, rx, ry), name="az_pinion", color=ALU)   # meshes with the belt on the upper 0.4" of the ring rim
base.add(cyl_z(1.85, 0.35, P["rocker_disc_dia"] / 2 + 0.09).cut(cyl_z(1.8, 0.5, P["rocker_disc_dia"] / 2)),
         name="az_belt_on_rim", color=BLACK)
base.add(cyl_z(1.2, 5.2, 0.75, mx, my), name="az_motor_GM9213", color=MOTOR)
base.add(box((rx + mx) / 2, (ry + my) / 2, floor_z0 + 0.5, 3.0, 2.2, 0.3)
         .rotate(v(rx, ry, 0), v(rx, ry, 1), 0), name="az_belt_plate", color=ALU)
base.add(box(mx, my, floor_z0 + P["ply"] + 0.4, 4.0, 4.0, 0.8), name="az_drive_bracket", color=ALU)
base.add(box(rx * 0.97 + 1.6 * math.cos(math.radians(az_ang + 90)), ry * 0.97 + 1.6 * math.sin(math.radians(az_ang + 90)), 1.67, 1.2, 0.8, 0.5), name="az_read_head", color=ELEC)

# electronics box on the front board
base.add(box(0, rw + 1.2, rocker_floor_top + 3.5, 8.0, 2.4, 5.0), name="electronics_box_sitech",
         color=ELEC)

# --------------------------------------------------------------------------
# Export
# --------------------------------------------------------------------------
out = os.path.join(os.path.dirname(__file__), "out")
os.makedirs(out, exist_ok=True)
base.save(os.path.join(out, "base.glb"))
tube.save(os.path.join(out, "tube.glb"))
truss_pairs.save(os.path.join(out, "truss_pairs.glb"))
truss_zigzag.save(os.path.join(out, "truss_zigzag.glb"))
spider_curved.save(os.path.join(out, "spider_curved.glb"))
spider_quad.save(os.path.join(out, "spider_quad.glb"))
spider_wire.save(os.path.join(out, "spider_wire.glb"))

full = cq.Assembly(name="dob16")
full.add(base, name="base")
tube.add(truss_pairs, name="truss_pairs")
tube.add(spider_curved, name="spider_curved")
full.add(tube, name="tube",
         loc=cq.Location(v(0, 0, z_alt), (1, 0, 0), 45))
full.save(os.path.join(out, "dob16_alt45.step"))

checks = dict(
    focal_length_in=FL,
    z_alt_axis_in=round(z_alt, 2),
    lower_tube_swing_radius_in=round(swing, 2),
    secondary_y_in=round(y_sec, 2),
    truss_pole_length_in=round(pole_len, 2),
    truss_zigzag_pole_length_in=round(pole_len_zig, 2),
    eyepiece_height_zenith_in=round(eyepiece_zenith, 1),
    nested_transport_height_in=round(nested_height, 1),
    rocker_wall_height_in=round(wall_h, 1),
    mirror_face_below_axis_in=s,
    tube_weight_lb=round(tube_lb, 1),
    net_moment_lb_in=round(net, 0),
    dobstuff_layout_counterweight_lb=round(cw_dobstuff, 1),
    counterweight_lb_at_mirror_end=round(counterweight, 1),
    counterweight_arm_in=round(cw_arm, 1),
    alt_external_ratio=round(alt_ratio, 0),
    az_external_ratio=round(az_ratio, 0),
)
json.dump(dict(params=P, assumed=ASSUMED, checks=checks,
               frame=dict(z_alt=z_alt, y_sec=y_sec, y_mirror=y_mirror,
                          y_ring_hi=y_ring_hi, y_ring_lo=y_ring_lo,
                          y_mcage_top=y_mcage_top, y_mcage_bot=y_mcage_bot,
                          focuser_x=bx - 0.125 - P["focuser_racked_in"] - 1.0,
                          bearing_x=bearing_x, R=R,
                          stub_xz={str(a): base_xz(a) for a in P["mcage_tube_angles"]})),
          open(os.path.join(out, "params.json"), "w"), indent=2)
print(json.dumps(checks, indent=2))
