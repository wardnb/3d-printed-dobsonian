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
    # drive-side rim bands, inboard -> outboard (x from the inner face)
    bands = [("bare", 0.15), ("belt", 0.36), ("ebony", 0.64), ("tape", 0.26)]
    x = 0.0
    G["bands"] = {}
    for name, w in bands:
        G["bands"][name] = (x, x + w)
        x += w
    assert x <= G["bearing_t"] + 1e-6, "rim bands exceed the bearing thickness"
    eb = G["bands"]["ebony"]
    G["pad_x"] = G["bearing_x_in"] + (eb[0] + eb[1]) / 2          # pad (and wall) centre, 11.675
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
    G["floor_z0"] = G["ground_top"] + G["az_pad_t"]                # rocker floor underside
    G["floor_top"] = G["floor_z0"] + ply
    G["z_alt"] = G["floor_top"] + swing + 0.5                      # 0.5 under the box at the bottom of its swing
    G["h_alt"] = G["z_alt"] - G["floor_top"]                       # axis above the floor top
    # --- wall profile (h above the floor top)
    G["arc_r"] = R + 0.4                                           # wall top edge between the pads
    G["lam_t"] = 0.06                                              # Ebony Star laminate on the rim
    G["pad_seat_r"] = R + G["lam_t"] + 0.19                        # 3/16 PTFE pad: top on the laminate
    G["pad_len"] = 1.6
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
    G["pivot_d"] = 0.375
    # --- drives
    G["pinion_pd"] = 0.5
    G["cap_z"] = G["z_alt"] - R - 0.09 - G["pinion_pd"] / 2        # alt pinion axis, under the rim at theta = 0
    G["alt_head_angle"] = -50                                      # alt tape read head on the back horn
    G["lateral_stop_angle"] = G["pad_angle"] + 7                   # PTFE stop just ahead of the front pad
    G["az_y"] = 8.5                                                # az drive station on the drive wall, front (clear of the 330 deg arm)
    G["az_pinion_r"] = G["ring_od"] / 2 + 0.09 + G["pinion_pd"] / 2
    G["az_pinion_xy"] = (math.sqrt(G["az_pinion_r"] ** 2 - G["az_y"] ** 2), G["az_y"])
    G["az_ratio"] = ((G["ring_od"] / 2 + 0.06) / (G["pinion_pd"] / 2)) * 2
    G["alt_ratio"] = ((R + 0.06) / (G["pinion_pd"] / 2)) * 2
    # overall
    G["rocker_top"] = G["floor_top"] + G["h_horn"]
    return G


# --------------------------------------------------------------------------
def bearing_outline(G, thick=None):
    """D bearing in the TUBE frame on a YZ workplane (local (Y, Z)): arc toward -Y (mirror), straight edge at
    y = +chord_e, rim + bar + a web at z = 0 that lands on the box's side strip; two lightening windows;
    two 3/8 dowel and two 1/4 bolt holes in the web. Extruded +X from x = 0."""
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
    holes = [(-8.4, 0, 0.375), (-13.2, 0, 0.375), (-10.8, 0.9, 0.26), (-10.8, -0.9, 0.26)]
    for y, z, d in holes:
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
    # pad seats: material back up to pad_seat_r over pad_len
    for ang in (G["pad_angle"], -G["pad_angle"]):
        r_hi = G["arc_r"] + 0.3
        r_mid = (G["pad_seat_r"] + r_hi) / 2
        boss = (cq.Workplane("XY").center(0, (ha - r_mid) * IN).rect(G["pad_len"] * IN, (r_hi - G["pad_seat_r"]) * IN)
                .extrude(thick * IN).rotate((0, ha * IN, 0), (0, ha * IN, 1), ang))
        w = w.union(boss)
    if drive:   # sprung pinion shaft passes over the wall top at theta = 0
        w = w.cut(cq.Workplane("XY").center(0, (ha - G["arc_r"] - 0.3) * IN).rect(1.0 * IN, 1.4 * IN).extrude(thick * IN))
    # bracket holes (1/4") through the wall, as (y, h) pairs
    holes = []
    sa = G["lateral_stop_angle"]
    ys = G["arc_r"] * math.sin(math.radians(sa))
    h_edge = ha - G["arc_r"] * math.cos(math.radians(sa))
    holes += [(ys, h_edge - 2.0), (ys, h_edge - 1.0)]                                # lateral stop bracket
    if drive:
        hc = G["cap_z"] - G["floor_top"]
        holes += [(dy, hc - 2.8 + dz) for dy in (-1.3, 1.3) for dz in (0.0, 1.6)]    # alt drive arm
        yh = G["arc_r"] * math.sin(math.radians(G["alt_head_angle"]))
        hh = (G["h_horn"] + G["end_h"]) / 2
        holes += [(yh, hh - 1.6), (yh, hh - 0.6)]                                   # alt read head bracket
        holes += [(G["az_y"] + dy, hz) for dy in (-0.9, 0.9) for hz in (1.6, 3.6)]  # az drive bracket
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
    pads = None
    for a in G["ground_angles"]:
        x, y = polar(G["az_pad_r"], a)
        p = box(x, y, G["ground_top"] + G["az_pad_t"] / 2, 1.5, 1.5, G["az_pad_t"])
        pads = p if pads is None else pads.union(p)
    S["az_ptfe"] = (pads, "PTFE")
    S["pivot_disc"] = (cyl_z(G["ground_top"], G["az_pad_t"], 1.5).cut(cyl_z(0, 3, G["pivot_d"] / 2)), "ALU")
    S["pivot_stud"] = (cyl_z(G["foot_h"], ft - G["foot_h"] + 0.35, G["pivot_d"] / 2), "ALU")   # low nut: the box passes 0.5 over the floor
    # belt (upper 0.36 of the ring rim, teeth out) and magnetic tape (lower 0.26) on the ground ring
    S["az_belt_on_rim"] = (cyl_z(G["ground_top"] - 0.36, 0.36, G["ring_od"] / 2 + 0.09)
                           .cut(cyl_z(G["ground_top"] - 0.4, 0.5, G["ring_od"] / 2)), "BLACK")
    S["encoder_strip_az"] = (cyl_z(G["ring_z0"], 0.26, G["ring_od"] / 2 + 0.03)
                             .cut(cyl_z(G["ring_z0"] - 0.1, 0.5, G["ring_od"] / 2 - 0.05)), "STRIP")
    # ---- rocker
    floor = box(0, 0, G["floor_z0"] + ply / 2, G["floor_w"], G["floor_l"], ply).cut(cyl_z(0, 5, G["pivot_d"] / 2 + 0.02))
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
    # ---- altitude drive (drive side): sprung pinion in the belt band, arm + GM9413 on the wall's outer face
    b = G["bands"]["belt"]
    xi = G["bearing_x_in"]
    cz = G["cap_z"]
    S["alt_pinion"] = (cyl_x(xi + b[0], b[1] - b[0], G["pinion_pd"] / 2, 0, cz), "ALU")
    S["alt_pinion_shaft"] = (cyl_x(xi + b[1], G["wall_out"] + 1.0 - (xi + b[1]), 0.125, 0, cz), "ALU")
    xa = G["wall_out"] + 0.3                                        # arm stands 0.06 off the bearing face
    S["alt_arm"] = (box(xa + 0.125, 0, cz - 1.3, 0.25, 2.8, 4.4), "ALU")
    S["alt_pulley_32T"] = (cyl_x(xa + 0.4, 0.5, 0.5, 0, cz), "BLACK")
    S["alt_motor_GM9413"] = (cyl_x(xa + 0.4, 4.6, 0.8, 0, cz - 2.6), "MOTOR")
    S["alt_pulley_16T"] = (cyl_x(xa + 0.4, 0.5, 0.25, 0, cz - 2.6), "BLACK")
    # alt tape read head on the back horn, over the tape band
    ha = math.radians(G["alt_head_angle"])
    yh, zh = (R + 0.4) * math.sin(ha), za - (R + 0.4) * math.cos(ha)
    tb = G["bands"]["tape"]
    head = box(xi + (tb[0] + tb[1]) / 2 + 0.1, yh, zh, 0.45, 0.8, 0.5)
    y_br = G["arc_r"] * math.sin(ha)
    h_br = (G["h_horn"] + G["end_h"]) / 2
    z_lo = ft + h_br - 2.2
    bracket = box(G["wall_out"] + 0.125, y_br, (z_lo + zh) / 2, 0.25, 1.2, zh - z_lo)
    S["alt_read_head"] = (head.union(bracket), "ELEC")
    # ---- azimuth drive on the drive wall, reaching the ground ring's rim
    px, py = G["az_pinion_xy"]
    S["az_pinion"] = (cyl_z(G["ground_top"] - 0.36, 0.36, G["pinion_pd"] / 2, px, py), "ALU")
    S["az_pinion_shaft"] = (cyl_z(G["ring_z0"] - 0.6, 1.6, 0.125, px, py), "ALU")
    plate = box(G["wall_out"] + 0.125, py, (0.8 + ft + 4.6) / 2, 0.25, 2.6, ft + 4.6 - 0.8)
    foot = box((G["wall_out"] + px + 1.9) / 2, py, G["floor_z0"] + 0.125, px + 1.9 - G["wall_out"], 2.6, 0.25)
    S["az_bracket"] = (plate.union(foot), "ALU")
    S["az_motor_GM9213"] = (cyl_z(G["floor_z0"] + 0.25, 4.6, 0.8, px + 1.25, py), "MOTOR")
    S["az_pulley_32T"] = (cyl_z(G["ring_z0"] - 0.55, 0.4, 0.5, px, py), "BLACK")
    S["az_pulley_16T"] = (cyl_z(G["ring_z0"] - 0.55, 0.4, 0.25, px + 1.25, py), "BLACK")
    # az tape read head beside the pinion, on the lower band
    phi = math.degrees(math.atan2(py, px)) + 7
    hx, hy = polar(G["ring_od"] / 2 + 0.3, phi)
    S["az_read_head"] = (box(hx, hy, G["ring_z0"] + 0.13, 0.5, 0.8, 0.45), "ELEC")
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
    half = (cq.Workplane("XY").moveTo(-G["ring_od"] / 2 * IN, 0).threePointArc((0, G["ring_od"] / 2 * IN), (G["ring_od"] / 2 * IN, 0))
            .lineTo(G["ring_id"] / 2 * IN, 0).threePointArc((0, G["ring_id"] / 2 * IN), (-G["ring_id"] / 2 * IN, 0)).close()
            .extrude(0.1 * IN))
    F["ground_ring_half"] = dict(solid=half, stock="18 mm Baltic birch", qty=2, size=(G["ring_od"], G["ring_od"] / 2))
    bl = bearing_outline(G, 0.1)
    # bring the YZ-built D into the XY plane: (X, Y) = (z, y), straight edge at the top
    bl = bl.rotate((0, 0, 0), (0, 1, 0), 90).translate((0, 0, 0.1 * IN))
    bl = cq.Workplane("XY").add(bl.val())          # re-home on XY so section()/DXF cut the flat, not the edge
    F["bearing_layer"] = dict(solid=bl, stock="18 mm Baltic birch", qty=4, size=(2 * R, R + G["chord_e"]))
    return S, F, dict(drive=holes_d, plain=holes_p)


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
