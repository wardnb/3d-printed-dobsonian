"""Rocker, ground board and the rebuilt 14" D bearings (design, 2026-10-19).

Inches in, mm solids out (IN = 25.4). World frame: ground z = 0, azimuth axis = Z, altitude axis along X at
z = z_alt, +Y = the direction the tube points at the horizon (front), -Y = mirror end at the horizon (back).
The drive side is +X; the focuser is on -X.

derive(P, R, swing, panel_x) -> G   all the numbers the rocker needs, from the model's params and the box
bearing_outline(G)                   D bearing as a 2D solid in the tube frame (for dob_model and the DXF)
build(G) -> (solids, flats)          world-frame solids for the base assembly and 2D flats for export_rocker.py
"""
import math
import cadquery as cq

IN = 25.4


def v(*a):
    return cq.Vector(*[x * IN for x in a])


def box(cx, cy, cz, sx, sy, sz):
    return cq.Workplane("XY").box(sx * IN, sy * IN, sz * IN).translate(v(cx, cy, cz))


def cyl_z(z0, length, r, x=0, y=0):
    return cq.Workplane("XY").circle(r * IN).extrude(length * IN).translate(v(x, y, z0))


def cyl_x(x0, length, r, y=0, z=0):
    return cq.Workplane("YZ").circle(r * IN).extrude(length * IN).translate(v(x0, y, z))


def polar(r, deg):
    a = math.radians(deg)
    return r * math.cos(a), r * math.sin(a)


# --------------------------------------------------------------------------
def derive(P, R, swing, panel_x):
    """All rocker/bearing numbers (inches). P = dob_model params, R = bearing radius, swing = lower tube swing
    radius about the altitude axis, panel_x = inner face of the box's side strips."""
    ply = P["ply"]
    G = dict(ply=ply, R=R, swing=swing)
    # --- bearings: two laminated 18 mm layers bolted to the side strips' outer faces
    G["bearing_t"] = 2 * ply                                   # 1.418
    G["bearing_x_in"] = panel_x + ply                          # inner face = strip outer face (10.84)
    G["bearing_x_out"] = G["bearing_x_in"] + G["bearing_t"]    # 12.26
    G["bearing_x"] = G["bearing_x_in"] + G["bearing_t"] / 2    # mid-plane
    # straight edge pushed past the axis plane so the front pad stays under the arc down to alt_min
    G["pad_angle"] = P["alt_pad_angle"]
    G["alt_min"] = P["alt_min_deg"]
    G["chord_e"] = R * math.sin(math.radians(G["pad_angle"] - G["alt_min"]))   # 3.62 for 30/15
    G["rim_w"] = 2.6                                           # running rim width (radial)
    G["bar_w"] = 1.2                                           # bar along the straight edge
    G["web_w"] = 3.0                                           # vertical web on the box's side strip
    # box side the D bolts to: the existing 3" strip (z +/-1.5) + a new 18 mm back wing between the boards (2026-10-31)
    G["box_inside_h"] = P["mcage_height"] - 2 * ply            # 11.38 (measured 11 3/8)
    G["wing_z"] = (-6.4, -1.5)                                 # to the end of the boards' side flat (z -6.49, ASSUMED)
    G["wing_notch"] = (-6.4, -4.1, 0.70)                       # clears the 330/210 deg stub's lower collar (2.75" OD)
    # bearing kind (2026-11-07): "rollers" = R10 ball-bearing wheels on an aluminium track (adopted), "ptfe" = the
    # earlier PTFE-on-laminate pads (kept for comparison; Ebony Star is discontinued)
    G["kind"] = P.get("bearing_kind", "rollers")
    rollers = G["kind"] == "rollers"
    # drive-side rim bands, inboard -> outboard (x from the inner face); the running band is the roller track
    # (1/16 x 5/8 6061 strip bonded to the rim) or the Ebony Star laminate
    bands = ([("bare", 0.16), ("belt", 0.36), ("track", 0.63), ("tape", 0.26)] if rollers      # "tape" = spare band since 2026-11-08 (no alt encoder)
             else [("bare", 0.15), ("belt", 0.36), ("ebony", 0.64), ("tape", 0.26)])
    x = 0.0
    G["bands"] = {}
    for name, w in bands:
        G["bands"][name] = (x, x + w)
        x += w
    assert x <= G["bearing_t"] + 1e-6, "rim bands exceed the bearing thickness"
    eb = G["bands"]["track" if rollers else "ebony"]
    G["run_band"] = eb
    G["pad_x"] = G["bearing_x_in"] + (eb[0] + eb[1]) / 2          # running band (and wall) centre, ~11.675
    G["pad_w"] = 0.55                                              # PTFE pad width, inside the Ebony band
    # --- rocker walls sit centred under the pads
    G["wall_in"] = G["pad_x"] - ply / 2
    G["wall_out"] = G["wall_in"] + ply
    G["box_clearance"] = G["wall_in"] - G["bearing_x_in"]          # wall inner face to the box strip
    G["inside_w"] = 2 * G["wall_in"]
    # --- heights
    G["arm_t"] = 0.75                                              # ground board arms + hub (3/4 ply)
    G["foot_h"] = 0.75
    G["ring_z0"] = G["foot_h"] + G["arm_t"]                        # ground ring bottom, 1.5
    G["ground_top"] = G["ring_z0"] + ply                           # ring top (az running surface), 2.21
    G["az_pad_t"] = 0.15
    # --- rollers (roller_study.py): R10 bearing 5/8 x 1-3/8 x 11/32 on a 5/8 shoulder bolt in a 6061 block
    G["roller_od"], G["roller_w"], G["axle_d"] = 1.375, 0.344, 0.625
    G["track_t"] = 0.0625                                          # alt: 1/16 x 5/8 strip on the rim
    G["az_track_t"] = 0.125                                        # az: 1/8 plate ring on the ground ring
    G["blk_w"], G["blk_l"] = 1.4, 2.0                              # block: across the roller axis x along it... see build()
    G["axle_from_top"] = 0.45                                      # roller protrudes od/2 - 0.45 = 0.24 past the block
    G["slot_w"] = 0.45
    G["slot_d"] = round(G["axle_from_top"] + G["roller_od"] / 2 + 0.05, 2)   # 1.19: the roller + 0.05 clearance
    G["blk_h_alt"], G["blk_h_az"] = 2.2, 1.5                       # az: 0.31 bridge over the slot (was 1.1: the slot cut it in two)
    G["saddle_d"] = 0.5                                            # alt block straddles the wall top this deep
    G["tab_t"], G["tab_clear"] = 0.125, 0.05                       # 1/8 Al lateral tab + 1/16 PTFE, 0.05 off the D's face
    G["az_blk_below_floor"] = G["blk_h_az"] - ply                  # the az block hangs through a floor cutout, 0.39 below
    G["az_stack"] = G["az_track_t"] + G["az_blk_below_floor"] + (G["roller_od"] / 2 - G["axle_from_top"])
    G["floor_z0"] = G["ground_top"] + (G["az_stack"] if rollers else G["az_pad_t"])   # rocker floor underside
    G["floor_top"] = G["floor_z0"] + ply
    G["z_alt"] = G["floor_top"] + swing + 0.5                      # 0.5 under the box at the bottom of its swing
    G["h_alt"] = G["z_alt"] - G["floor_top"]                       # axis above the floor top
    # --- wall profile (h above the floor top)
    G["arc_r"] = R + 0.4                                           # wall top edge between the pads
    G["lam_t"] = 0.06                                              # Ebony Star laminate on the rim
    G["pad_seat_r"] = R + G["lam_t"] + 0.19                        # 3/16 PTFE pad: top on the laminate
    G["pad_len"] = 1.6
    # roller stations at +/-pad_angle: contact on the strip, axle od/2 further out, block below, saddle on the wall
    G["r_track"] = R + G["track_t"]
    G["r_axle"] = G["r_track"] + G["roller_od"] / 2
    G["r_blk_top"] = G["r_axle"] - G["axle_from_top"]              # R + 0.30: 0.2 under the belt teeth
    G["r_blk_bot"] = G["r_blk_top"] + G["blk_h_alt"]
    G["r_notch"] = G["r_blk_bot"] - G["saddle_d"]                  # wall top inside the notch, R + 2.0
    G["blk_bolt_r"] = G["r_notch"] + 0.30                          # two 1/4-20 cross bolts through block cheeks + wall
    G["horn_angle"] = P["rocker_horn_angle"]
    G["depth"] = P["rocker_inside_depth"]
    G["L"] = G["depth"] + 2 * ply                                  # walls run the full floor length
    G["end_h"] = P["rocker_end_height"]
    G["h_pad"] = G["h_alt"] - R * math.cos(math.radians(G["pad_angle"]))
    G["h_dip"] = G["h_alt"] - G["arc_r"]
    G["h_horn"] = G["h_alt"] - G["arc_r"] * math.cos(math.radians(G["horn_angle"]))
    G["y_horn"] = G["arc_r"] * math.sin(math.radians(G["horn_angle"]))
    G["y_pad"] = R * math.sin(math.radians(G["pad_angle"]))
    # end boards must stay under the box's swing circle (0.3 clearance)
    d = G["depth"] / 2
    G["end_h_max"] = G["h_alt"] - math.sqrt(swing ** 2 - d ** 2) - 0.3
    # --- floor
    G["floor_w"] = 2 * G["wall_out"]
    G["floor_l"] = G["L"]
    # --- ground board
    G["ring_od"] = P["ground_ring_od"]
    G["ring_id"] = P["ground_ring_id"]
    G["foot_r"] = P["ground_foot_radius"]
    G["az_pad_r"] = P["ground_pad_radius"]
    G["ground_angles"] = (90, 210, 330)
    G["az_roller_angles"] = (45, 135, 225, 315)                    # four rollers at the floor's corners (clear of the end boards)
    G["pivot_d"] = 0.375
    # --- drives
    G["pinion_pd"] = 0.5
    G["cap_z"] = G["z_alt"] - R - 0.09 - G["pinion_pd"] / 2        # alt pinion axis, under the rim at theta = 0
    G["alt_head_angle"] = -50                                      # (unused since 2026-11-08: no alt tape head)
    G["lateral_stop_angle"] = G["pad_angle"] + 7                   # PTFE stop just ahead of the front pad
    G["az_y"] = 6.0                                                # az pinion station (drive.py): the arm's tail stays outboard of the drive wall
    G["az_pinion_r"] = G["ring_od"] / 2 + 0.09 + G["pinion_pd"] / 2
    G["az_pinion_xy"] = (math.sqrt(G["az_pinion_r"] ** 2 - G["az_y"] ** 2), G["az_y"])
    G["az_ratio"] = ((G["ring_od"] / 2 + 0.06) / (G["pinion_pd"] / 2)) * 2
    G["alt_ratio"] = ((R + 0.06) / (G["pinion_pd"] / 2)) * 2
    # overall
    G["rocker_top"] = G["floor_top"] + G["h_horn"]
    return G


# --------------------------------------------------------------------------
# D-to-box joint (2026-10-31, bearing_fe.py): the D bolts to the box side = the existing 3" strip + a new 18 mm back
# wing (z -6.4 .. -1.5, between the boards). Tube-frame (y, z, dia, kind). Dowels: 3/8 steel pins pressed into the D,
# running in 3/8 ID x 1/2 OD steel drill bushings set blind in the panel. Bolts: 1/4-20 into threaded inserts in the
# panel (drill the panel through the D as a template). See bearing_fe.WING_FASTENERS for the FE copy.
def _rim_y(z, r=12.7):
    return -math.sqrt(r * r - z * z)


BEARING_HOLES = [(_rim_y(-5.6), -5.6, 0.375, "dowel"), (-7.0, 0.9, 0.375, "dowel"),
                 (-7.2, -0.9, 0.26, "bolt"), (-10.0, 0.9, 0.26, "bolt"), (-10.0, -0.9, 0.26, "bolt"),
                 (-12.6, -1.0, 0.26, "bolt"), (-13.2, 0.9, 0.26, "bolt"), (_rim_y(-3.8), -3.8, 0.26, "bolt")]


def bearing_outline(G, thick=None):
    """D bearing in the TUBE frame on a YZ workplane (local (Y, Z)): arc toward -Y (mirror), straight edge at
    y = +chord_e, rim + bar + a web at z = 0 that lands on the box's side strip; two lightening windows;
    the dowel and bolt holes of BEARING_HOLES. Extruded +X from x = 0."""
    R, e, t = G["R"], G["chord_e"], (thick or G["bearing_t"])
    c = math.sqrt(R ** 2 - e ** 2)
    outer = (cq.Workplane("YZ").moveTo(e * IN, -c * IN).threePointArc((-R * IN, 0), (e * IN, c * IN))
             .close().extrude(t * IN))
    r_in = R - G["rim_w"]
    for sz in (1, -1):
        win = cq.Workplane("YZ").circle(r_in * IN).extrude(t * IN)
        clip = (cq.Workplane("YZ").center(((e - G["bar_w"]) - r_in) / 2 * IN,
                                          sz * (r_in + G["web_w"] / 2) / 2 * IN)
                .rect((r_in + e - G["bar_w"]) * IN, (r_in - G["web_w"] / 2) * IN).extrude(t * IN))
        outer = outer.cut(win.intersect(clip))
    for y, z, d, _k in BEARING_HOLES:
        outer = outer.cut(cq.Workplane("YZ").center(y * IN, z * IN).circle(d / 2 * IN).extrude(t * IN))
    return outer


def bearing_area_in2(G):
    return bearing_outline(G, 0.1).val().Volume() / (0.1 * IN) / IN ** 2


# --------------------------------------------------------------------------
def _rot_x(solid, deg, z0):
    """Rotate a solid about the altitude axis (line along X through (0, 0, z0))."""
    return solid.rotate(v(0, 0, z0), v(1, 0, z0), deg)


def wall_flat(G, drive, thick):
    """Rocker wall profile as an XY solid: local X = y (front +), local Y = h above the floor top."""
    L, ha = G["L"], G["h_alt"]
    h_top = G["h_horn"]
    w = cq.Workplane("XY").center(0, h_top / 2 * IN).rect(L * IN, h_top * IN).extrude(thick * IN)
    # dip: the arc under the bearing
    w = w.cut(cq.Workplane("XY").center(0, ha * IN).circle(G["arc_r"] * IN).extrude(thick * IN))
    # slopes from each horn tip down to the end height
    for sy in (1, -1):
        yh, hh = sy * G["y_horn"], G["h_horn"]
        ye, he = sy * (L / 2 + 0.2), G["end_h"]
        pts = [(yh, hh + 0.001), (ye, he), (ye, hh + 1), (yh, hh + 1)]
        w = w.cut(cq.Workplane("XY").polyline([(a * IN, b * IN) for a, b in pts]).close().extrude(thick * IN))
    rollers = G["kind"] == "rollers"
    for ang in (G["pad_angle"], -G["pad_angle"]):
        if rollers:
            # roller notch: the wall top drops from arc_r to r_notch over the block length; the block's saddle sits on
            # the notch floor and two 1/4-20 cross bolts pass through its cheeks and the wall
            r_hi = G["arc_r"] - 0.3
            r_mid = (G["r_notch"] + r_hi) / 2
            notch = (cq.Workplane("XY").center(0, (ha - r_mid) * IN).rect((G["blk_l"] + 0.04) * IN, (G["r_notch"] - r_hi) * IN)
                     .extrude(thick * IN).rotate((0, ha * IN, 0), (0, ha * IN, 1), ang))
            w = w.cut(notch)
            for dy in (-0.6, 0.6):
                h_ = (cq.Workplane("XY").center(dy * IN, (ha - G["blk_bolt_r"]) * IN).circle(0.13 * IN)
                      .extrude(thick * IN).rotate((0, ha * IN, 0), (0, ha * IN, 1), ang))
                w = w.cut(h_)
        else:
            # pad seats: material back up to pad_seat_r over pad_len
            r_hi = G["arc_r"] + 0.3
            r_mid = (G["pad_seat_r"] + r_hi) / 2
            boss = (cq.Workplane("XY").center(0, (ha - r_mid) * IN).rect(G["pad_len"] * IN, (r_hi - G["pad_seat_r"]) * IN)
                    .extrude(thick * IN).rotate((0, ha * IN, 0), (0, ha * IN, 1), ang))
            w = w.union(boss)
    if drive:   # sprung pinion shaft passes over the wall top at theta = 0
        w = w.cut(cq.Workplane("XY").center(0, (ha - G["arc_r"] - 0.3) * IN).rect(1.0 * IN, 1.4 * IN).extrude(thick * IN))
    # bracket holes (1/4") through the wall, as (y, h) pairs
    holes = []
    if not rollers:                                                                  # lateral stop bracket (the roller blocks carry tabs)
        sa = G["lateral_stop_angle"]
        ys = G["arc_r"] * math.sin(math.radians(sa))
        h_edge = ha - G["arc_r"] * math.cos(math.radians(sa))
        holes += [(ys, h_edge - 2.0), (ys, h_edge - 1.0)]
    if drive:
        import drive
        holes += [(y_, z_ - G["floor_top"]) for y_, z_ in drive.wall_holes(G)]       # alt base plate + az bracket leg
    else:
        holes += [(yb, hz) for yb in (4.5, 9.5) for hz in (1.5, 4.5)]               # electronics box (plain wall)
    for y, h in holes:
        w = w.cut(cq.Workplane("XY").center(y * IN, h * IN).circle(0.13 * IN).extrude(thick * IN))
    return w, holes


def wall(G, side, drive):
    """One rocker wall as a world-frame solid. side = +1 (drive, +X) or -1."""
    w, holes = wall_flat(G, drive, G["ply"])
    # local (X, Y, Z) = (y, h, thickness) -> world (thickness, y, h)
    w = w.rotate((0, 0, 0), (1, 0, 0), 90).rotate((0, 0, 0), (0, 0, 1), 90)
    x0 = G["wall_in"] if side > 0 else -G["wall_out"]
    return w.translate(v(x0, 0, G["floor_top"])), holes


def roller_block(G, h, saddle):
    """6061 roller block in its own frame: X = along the roller AXIS (block width blk_w),
    Y = tangential (blk_l), Z = radial with the roller side at +Z (top at z = 0, block extends to -h). Roller slot
    slot_w wide (X) x slot_d deep from the top, axle hole along X at -axle_from_top, saddle groove (ply + 0.02 wide in X)
    saddle_d deep from the bottom (alt only), two 1/4 cross holes along X through the saddle cheeks."""
    b = box(0, 0, -h / 2, G["blk_w"], G["blk_l"], h)
    # looks (2026-11-08): the roller-side face is an arch concentric-ish with the axle (R 0.9 centred 0.9 below the
    # top) so the cheeks fall away 0.33" at the corners, and the long edges carry a 0.06 chamfer
    arch = (cq.Workplane("XZ").circle(0.9 * IN).extrude(-(G["blk_l"] + 1) * IN, both=True)
            .translate((0, 0, -0.9 * IN)))
    keep = box(0, 0, -h / 2 - 0.5, G["blk_w"] + 1, G["blk_l"] + 1, h - 0.9 + 1.0)      # everything below the arch's centre line
    b = b.intersect(arch.union(keep))
    try:
        b = b.edges("|Y").chamfer(0.06 * IN)
    except Exception:
        pass
    b = b.cut(box(0, 0, -G["slot_d"] / 2, G["slot_w"], G["blk_l"] + 0.1, G["slot_d"]))
    b = b.cut(cyl_x(-1, 2 + G["blk_w"], G["axle_d"] / 2, 0, -G["axle_from_top"]))
    if saddle:
        b = b.cut(box(0, 0, -h + G["saddle_d"] / 2, G["ply"] + 0.02, G["blk_l"] + 0.1, G["saddle_d"]))
        for dy in (-0.6, 0.6):
            b = b.cut(cyl_x(-1, 2 + G["blk_w"], 0.13, dy, -h + G["saddle_d"] - 0.30))
    else:
        # az: the block hangs roller-side DOWN; four #10-32 tapped 0.6 into the cheeks' upper face (-h) for the flange plate
        for dx in (-0.46, 0.46):
            for dy in (-0.6, 0.6):
                b = b.cut(cyl_z(-h - 0.01, 0.61, 0.08, dx, dy))
    roller = cyl_x(-G["roller_w"] / 2, G["roller_w"], G["roller_od"] / 2, 0, -G["axle_from_top"])
    # 5/8 x 1 shoulder bolt from the +X cheek (head 0.9 dia x 0.4 outside that face), 1/2-13 in the -X cheek
    axle = cyl_x(-G["blk_w"] / 2 + 0.2, G["blk_w"] - 0.2, G["axle_d"] / 2, 0, -G["axle_from_top"])
    axle = axle.union(cyl_x(G["blk_w"] / 2, 0.4, 0.45, 0, -G["axle_from_top"]))
    return b, roller, axle


def roller_parts(G):
    """Alt roller blocks on the wall notches (+ lateral tabs) and four az blocks hanging through the floor at its corners
    (2026-11-07). Four az rollers (not three): a block at 90/210/330 would sit under an end board; the ply floor flexes
    more than the track mismatch, so all four carry load."""
    R, za, ft, ply = G["R"], G["z_alt"], G["floor_top"], G["ply"]
    S = {}
    blocks = rollers = axles = tabs = None
    for sx in (1, -1):
        for ang in (G["pad_angle"], -G["pad_angle"]):
            b, r, a = roller_block(G, G["blk_h_alt"], True)
            # block frame -> world: block top at radius r_blk_top straight below the axis, then rotated about X by ang
            def place(p):
                if sx < 0:                                                 # bolt head outboard on both sides
                    p = p.mirror("YZ")
                p = p.translate(v(sx * G["pad_x"], 0, za - G["r_blk_top"]))
                return _rot_x(p, ang, za)
            # lateral tab: 1/8 Al on the block's outer face + 1/16 PTFE, face tab_clear off the D's outer face
            xo = G["bearing_x_out"]
            x_tab_in = xo + G["tab_clear"]
            t_tab = G["tab_t"] + 0.0625
            h_tab = G["r_blk_top"] - (R - 0.5)                             # from the block top up alongside the rim
            tab = box(x_tab_in + t_tab / 2 - G["pad_x"], 0, h_tab / 2, t_tab, 1.0, h_tab)      # +X = outboard; place() mirrors
            tab_w = place(tab)
            bw, rw, aw = place(b), place(r), place(a)
            blocks = bw if blocks is None else blocks.union(bw)
            rollers = rw if rollers is None else rollers.union(rw)
            axles = aw if axles is None else axles.union(aw)
            tabs = tab_w if tabs is None else tabs.union(tab_w)
    S["alt_roller_blocks"] = (blocks, "ALU")
    S["alt_rollers"] = (rollers, "STEEL")
    S["alt_axles"] = (axles, "STEEL")
    S["alt_lateral_tabs"] = (tabs, "PTFE")
    # (the rim track strips rotate with the D: dob_model.py draws them on the tube, not here)
    # az blocks: hang through the floor cutouts, roller axis radial, flange plate on the floor top
    blocks = rollers = axles = plates = None
    z_top = G["floor_z0"] + ply                                            # block's upper face flush with the floor top
    for a in G["az_roller_angles"]:
        x, y = polar(G["az_pad_r"], a)
        b, r, ax = roller_block(G, G["blk_h_az"], False)
        def place(p):
            # block frame has the roller side at z = 0 and the body at -z: flip it so the roller faces DOWN, then the
            # block's -h face (now up) sits flush with the floor top and the roller hangs below the floor onto the track
            p = p.rotate((0, 0, 0), (0, 1, 0), 180).translate(v(0, 0, -G["blk_h_az"]))
            return p.rotate((0, 0, 0), (0, 0, 1), a).translate(v(x, y, z_top))
        bw, rw, aw = place(b), place(r), place(ax)
        pl = (box(0, 0, 0.125, G["blk_w"] + 1.0, G["blk_l"] + 1.0, 0.25)                        # flange plate on the floor top
              .rotate((0, 0, 0), (0, 0, 1), a).translate(v(x, y, z_top)))
        blocks = bw if blocks is None else blocks.union(bw)
        rollers = rw if rollers is None else rollers.union(rw)
        axles = aw if axles is None else axles.union(aw)
        plates = pl if plates is None else plates.union(pl)
    S["az_roller_blocks"] = (blocks, "ALU")
    S["az_rollers"] = (rollers, "STEEL")
    S["az_axles"] = (axles, "STEEL")
    S["az_flange_plates"] = (plates, "ALU")
    return S


def build(G):
    """World-frame solids (dict name -> (solid, colour key)) and 2D flats for the DXFs."""
    ply, ft, za, R = G["ply"], G["floor_top"], G["z_alt"], G["R"]
    S = {}
    # ---- ground board
    gb = cyl_z(G["foot_h"], G["arm_t"], 4.0)
    for a in G["ground_angles"]:
        x, y = polar(G["ring_od"] / 4 + 1.0, a)
        arm = (cq.Workplane("XY").box((G["ring_od"] / 2 - 2.0) * IN, 3.5 * IN, G["arm_t"] * IN)
               .rotate((0, 0, 0), (0, 0, 1), a).translate(v(x, y, G["foot_h"] + G["arm_t"] / 2)))
        gb = gb.union(arm)
    gb = gb.cut(cyl_z(0, 2, G["pivot_d"] / 2 + 0.01))
    S["ground_board"] = (gb, "BIRCH")
    ring = cyl_z(G["ring_z0"], ply, G["ring_od"] / 2).cut(cyl_z(G["ring_z0"], ply, G["ring_id"] / 2))
    S["ground_ring"] = (ring, "BIRCH")
    feet = None
    for a in G["ground_angles"]:
        x, y = polar(G["foot_r"], a)
        f = cyl_z(0, G["foot_h"], 1.0, x, y)
        feet = f if feet is None else feet.union(f)
    S["feet"] = (feet, "BLACK")
    rollers = G["kind"] == "rollers"
    if rollers:
        # az track: 1/8 6061 ring (four 90 deg segments, joints at 45+k90 off the birch ring's joints) on the ground ring
        ra = G["az_pad_r"]
        S["az_track"] = (cyl_z(G["ground_top"], G["az_track_t"], ra + 0.5).cut(cyl_z(G["ground_top"], G["az_track_t"], ra - 0.5)), "ALU")
        # pivot: 3/8 shoulder bolt in a flanged FR6 bearing housed in a 6061 disc on the floor top (zero play)
        S["pivot_housing"] = (cyl_z(G["floor_z0"] + ply, 0.3, 0.75).cut(cyl_z(0, 9, 0.44)), "ALU")   # FR6 is 9/32 wide; box passes 0.2 over
    else:
        pads = None
        for a in G["ground_angles"]:
            x, y = polar(G["az_pad_r"], a)
            p = box(x, y, G["ground_top"] + G["az_pad_t"] / 2, 1.5, 1.5, G["az_pad_t"])
            pads = p if pads is None else pads.union(p)
        S["az_ptfe"] = (pads, "PTFE")
        S["pivot_disc"] = (cyl_z(G["ground_top"], G["az_pad_t"], 1.5).cut(cyl_z(0, 3, G["pivot_d"] / 2)), "ALU")
    S["pivot_stud"] = (cyl_z(G["foot_h"], ft - G["foot_h"] + 0.35, G["pivot_d"] / 2), "ALU")   # fixed in the hub; low nut: the box passes 0.5 over the floor
    # belt (upper 0.36 of the ring rim, teeth out) on the ground ring; no az tape since 2026-11-08 (shaft encoder at the pivot)
    S["az_belt_on_rim"] = (cyl_z(G["ground_top"] - 0.36, 0.36, G["ring_od"] / 2 + 0.09)
                           .cut(cyl_z(G["ground_top"] - 0.4, 0.5, G["ring_od"] / 2)), "BLACK")
    # ---- rocker
    floor = box(0, 0, G["floor_z0"] + ply / 2, G["floor_w"], G["floor_l"], ply).cut(cyl_z(0, 5, G["pivot_d"] / 2 + 0.02))
    if rollers:
        for a in G["az_roller_angles"]:
            x, y = polar(G["az_pad_r"], a)
            # cutout = block + 0.02 each side, plus 0.5 radially outboard for the shoulder bolt's head
            cut = (cq.Workplane("XY").box((G["blk_w"] + 0.54) * IN, (G["blk_l"] + 0.04) * IN, 3 * IN).translate(v(0.25, 0, 0))
                   .rotate((0, 0, 0), (0, 0, 1), a).translate(v(x, y, G["floor_z0"] + ply / 2)))
            floor = floor.cut(cut)
    S["rocker_floor"] = (floor, "BIRCH")
    wd, holes_d = wall(G, +1, True)
    wp, holes_p = wall(G, -1, False)
    S["rocker_wall_drive"] = (wd, "BIRCH")
    S["rocker_wall_plain"] = (wp, "BIRCH")
    ends = None
    for sy in (1, -1):
        e = box(0, sy * (G["depth"] / 2 + ply / 2), ft + G["end_h"] / 2, 2 * G["wall_in"], ply, G["end_h"])
        ends = e if ends is None else ends.union(e)
    S["rocker_ends"] = (ends, "BIRCH")
    if rollers:
        S.update(roller_parts(G))
    else:
        # altitude PTFE pads on the seats, centred under the Ebony band
        apads = None
        for sx in (1, -1):
            for ang in (G["pad_angle"], -G["pad_angle"]):
                p = box(sx * G["pad_x"], 0, za - (R + G["lam_t"] + 0.095), G["pad_w"], G["pad_len"], 0.19)
                p = _rot_x(p, ang, za)
                apads = p if apads is None else apads.union(p)
        S["alt_ptfe_pads"] = (apads, "PTFE")
        # lateral stops: L-brackets on each wall's outer face, PTFE face 0.06 off the bearing's outer face
        stops = None
        for sx in (1, -1):
            sa = G["lateral_stop_angle"]
            y = G["arc_r"] * math.sin(math.radians(sa))
            h_edge = G["h_alt"] - G["arc_r"] * math.cos(math.radians(sa))        # wall top there
            xo = G["wall_out"]
            leg = box(sx * (xo + 0.45), y, ft + h_edge - 1.3, 0.9, 1.0, 2.4)
            xf = G["bearing_x_out"] + 0.06
            up = box(sx * ((xf + xo + 0.9) / 2), y, ft + h_edge + 1.2, (xo + 0.9) - xf, 1.0, 2.6)
            part = leg.union(up)
            stops = part if stops is None else stops.union(part)
        S["lateral_stops"] = (stops, "ALU")
    # ---- drive modules (drive.py, 2026-10-31): the same swing arm on both axes, 2:1 pulleys drawn
    import drive
    for _ax in ("alt", "az"):
        S.update(drive.module(G, _ax))
    xi = G["bearing_x_in"]
    # scope encoders (2026-11-08): NO tape heads. Plate solving (Waypoint) gives absolute position; the only scope
    # encoder is the owned Astro Devices HD azimuth assembly (RLS MR ring Ø48 on a carrier disc, 76 poles x 4096 =
    # 311,296 steps/rev; RLC2HD reader potted in a block on a 3 mm floating plate whose Ø6.2 bearing rides the disc's
    # boss). Mounted the way the kit is meant to be (Nick, 2026-11-08): the pivot bolt is fixed in the ground hub, the
    # ring disc is pressed onto it (kit's printed hub) and sits on the hub top, static with the ground; the plate hangs
    # under the rocker floor on the disc boss and the reader goes round WITH the rocker, so its cable stays on the
    # rocker with the SiTech (nothing crosses the az axis). The 15 mm reader block is pocketed up into the 18 mm floor;
    # one screw through the plate's slot into the floor stops it rotating. MEASURED: ring OD 48, plate 3, bearing bore
    # 6.2, block 18 incl. plate. ASSUMED: disc thickness 11 mm, boss Ø6 x 6 mm, plate 130 x 25 mm.
    PLATE_T, BLOCK_H, DISC_T, DISC_R, BOSS_H = 3 / 25.4, 15 / 25.4, 11 / 25.4, 24 / 25.4, 6 / 25.4
    z_disc0 = G["ground_top"] + 0.02                                 # disc on the hub top (0.02 washer)
    z_plate0 = z_disc0 + DISC_T + 0.02                                # plate rides the boss just above the disc
    S["az_enc_disc"] = (cyl_z(z_disc0, DISC_T, DISC_R), "BLACK")
    S["az_enc_ring"] = (cyl_z(z_disc0 + 0.05, DISC_T - 0.1, DISC_R + 0.01).cut(cyl_z(0, 9, DISC_R - 0.12)), "STRIP")
    S["az_enc_boss"] = (cyl_z(z_disc0 + DISC_T, BOSS_H, 3 / 25.4), "BLACK")
    S["az_enc_plate"] = (box(0, 2.0, z_plate0 + PLATE_T / 2, 1.0, 5.1, PLATE_T).cut(cyl_z(0, 9, 0.25)), "ALU")
    S["az_enc_reader"] = (box(0, DISC_R + 0.45, z_plate0 + PLATE_T + BLOCK_H / 2, 0.9, 0.8, BLOCK_H), "ELEC")
    G["az_enc_block_top"] = z_plate0 + PLATE_T + BLOCK_H
    G["az_enc_floor_pocket"] = max(0.0, G["az_enc_block_top"] - G["floor_z0"] + 0.05)   # pocket depth into the floor underside
    assert G["az_enc_floor_pocket"] <= ply - 0.3, "az encoder block would break through the floor"
    assert z_plate0 + PLATE_T <= G["floor_z0"] - 0.02, "az encoder plate hits the floor underside"
    # ---- electronics box on the plain wall, front
    S["electronics_box_sitech"] = (box(-(G["wall_out"] + 1.3), 7.0, ft + 3.2, 2.4, 8.0, 5.0), "ELEC")

    # ---- 2D flats for the DXFs (XY plane, inches -> mm, thickness 0.1 to section)
    F = {}
    F["rocker_floor"] = dict(solid=_flat_floor(G), stock="18 mm Baltic birch", qty=1,
                             size=(G["floor_w"], G["floor_l"]))
    F["rocker_wall_drive"] = dict(solid=wall_flat(G, True, 0.1)[0], stock="18 mm Baltic birch", qty=1,
                                  size=(G["L"], G["h_horn"]))
    F["rocker_wall_plain"] = dict(solid=wall_flat(G, False, 0.1)[0], stock="18 mm Baltic birch", qty=1,
                                  size=(G["L"], G["h_horn"]))
    F["rocker_end"] = dict(solid=cq.Workplane("XY").rect(2 * G["wall_in"] * IN, G["end_h"] * IN).extrude(0.1 * IN),
                           stock="18 mm Baltic birch", qty=2, size=(2 * G["wall_in"], G["end_h"]))
    F["ground_hub"] = dict(solid=cq.Workplane("XY").circle(4.0 * IN).circle(G["pivot_d"] / 2 * IN).extrude(0.1 * IN),
                           stock="18 mm Baltic birch", qty=1, size=(8.0, 8.0))
    arm_l = G["ring_od"] / 2 - 3.0
    arm = cq.Workplane("XY").rect(arm_l * IN, 3.5 * IN).extrude(0.1 * IN)
    for dx in (-arm_l / 2 + 1.0, arm_l / 2 - 1.5):
        arm = arm.cut(cq.Workplane("XY").center(dx * IN, 0).circle(0.1 * IN).extrude(0.1 * IN))
    F["ground_arm"] = dict(solid=arm, stock="18 mm Baltic birch", qty=3, size=(arm_l, 3.5))
    # ring in three 120-degree segments (a 30 x 15 half ring will not share an AltMill blank with anything);
    # the joints sit on the arms at G["ground_angles"], each end screwed to the arm through two pilot holes
    ro, ri = G["ring_od"] / 2, G["ring_id"] / 2
    s60, c60 = math.sin(math.radians(60)), math.cos(math.radians(60))
    third = (cq.Workplane("XY").moveTo(-ro * s60 * IN, ro * c60 * IN).threePointArc((0, ro * IN), (ro * s60 * IN, ro * c60 * IN))
             .lineTo(ri * s60 * IN, ri * c60 * IN).threePointArc((0, ri * IN), (-ri * s60 * IN, ri * c60 * IN)).close()
             .extrude(0.1 * IN))
    for sgn in (-1, 1):
        for r_, da in ((12.3, 4.0), (14.2, 3.5)):          # 2 pilots per end, 0.86-0.99" in from the joint, on the arm
            a = math.radians(60 - da)
            third = third.cut(cq.Workplane("XY").center(sgn * r_ * math.sin(a) * IN, r_ * math.cos(a) * IN)
                              .circle(0.07 * IN).extrude(0.1 * IN))
    F["ground_ring_third"] = dict(solid=third, stock="18 mm Baltic birch", qty=3, size=(2 * ro * s60, ro - ri * c60))
    bl = bearing_outline(G, 0.1)
    # bring the YZ-built D into the XY plane: (X, Y) = (z, y), straight edge at the top
    bl = bl.rotate((0, 0, 0), (0, 1, 0), 90).translate((0, 0, 0.1 * IN))
    bl = cq.Workplane("XY").add(bl.val())          # re-home on XY so section()/DXF cut the flat, not the edge
    F["bearing_layer"] = dict(solid=bl, stock="18 mm Baltic birch", qty=4, size=(2 * R, R + G["chord_e"]))
    F["box_side_wing"] = dict(solid=wing_flat(G), stock="18 mm Baltic birch", qty=2,
                              size=(G["wing_z"][1] - G["wing_z"][0], G["box_inside_h"]))
    return S, F, dict(drive=holes_d, plain=holes_p)


def wing_flat(G, thick=0.1):
    """New back wing of the box side, as an XY flat: X = z (tube frame), Y = height above the mirror board's top face.
    Glued to the strip's back edge and between the boards (Confirmat screws down through the top ring and up through
    the mirror board at z -2.3 and -3.6, clear of the stub collar). The D's dowel bushing and insert holes are drilled
    through the D as a template, so the flat carries only the outline; it is the same part for both sides (flip it)."""
    z0, z1 = G["wing_z"]
    h = G["box_inside_h"]
    nz0, nz1, nd = G["wing_notch"]
    pts = [(z0, 0), (z1, 0), (z1, h), (nz1, h), (nz1, h - nd), (z0, h - nd)]
    return (cq.Workplane("XY").polyline([(a * IN, b * IN) for a, b in pts]).close().extrude(thick * IN)
            .translate((-(z0 + z1) / 2 * IN, -h / 2 * IN, 0)))


def _flat_floor(G):
    ply = G["ply"]
    f = cq.Workplane("XY").rect(G["floor_w"] * IN, G["floor_l"] * IN).extrude(0.1 * IN)
    f = f.cut(cq.Workplane("XY").circle((G["pivot_d"] / 2 + 0.02) * IN).extrude(0.1 * IN))
    # screw pilots up into the walls and end boards (countersink from below)
    pts = [(sx * (G["wall_in"] + ply / 2), y) for sx in (1, -1) for y in (-12, -6, 0, 6, 12)]
    pts += [(x, sy * (G["depth"] / 2 + ply / 2)) for sy in (1, -1) for x in (-7, 0, 7)]
    for x, y in pts:
        f = f.cut(cq.Workplane("XY").center(x * IN, y * IN).circle(0.07 * IN).extrude(0.1 * IN))
    return f
