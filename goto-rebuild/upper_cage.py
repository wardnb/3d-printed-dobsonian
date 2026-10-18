"""
Upper cage, detailed for machining (v1).

Frame: inches in, millimetres out. Tube frame: optical axis = +Y (toward the
sky), focuser on -X, altitude axis along X. y=0 here is the SECONDARY CENTRE;
dob_model.py translates the assembly into place.

Every value in INPUTS marked INPUT is a placeholder until Nick confirms it.
"""
import math
import cadquery as cq

IN = 25.4

INPUTS = dict(
    plate=0.375,            # ring plate thickness: 3/8" 6061 (v2; the 1/4" v1 rings flexed ~3x more, see cage_fe.py)
    board_t=0.25,           # focuser board plate
    lighten=False,          # v2: no lightening slots (they cost ~3x in collimation hold for 1.3 lb saved)
    ring_id=17.5,
    ring_od=20.5,
    ring_gap=7.5,           # clear space between ring inner faces
    pole_od=1.0,            # INPUT: truss pole OD (reuse DobStuff pipes?)
    ft_clear_dia=2.5,       # INPUT: board hole for the Feather Touch drawtube
    ft_bolt_circle=3.0,     # INPUT: Feather Touch base bolt circle
    ft_bolt_n=4,            # INPUT
    ft_bolt_tap="#8-32",    # INPUT
    vane_tip_hole=0.257,    # INPUT: Destiny vane-tip bolt (1/4" clearance assumed)
    endmill=0.25,           # INPUT: smallest end mill for aluminium profiles
)
I = INPUTS
T = I["plate"]
R_IN, R_OUT = I["ring_id"] / 2, I["ring_od"] / 2
R_BOLT = (R_IN + R_OUT) / 2          # 9.5"
CLR_14 = 0.257                       # 1/4-20 clearance
TAP_14 = 0.201                       # 1/4-20 tap drill
CLR_10 = 0.201                       # #10 clearance
TAP_10 = 0.159                       # #10-32 tap drill

# angular layout (degrees from +X toward +Z, looking from the sky end)
TOPS = [0, 120, 240]                 # Destiny spider tower seats (upper ring)
APEX = [30, 150, 270]                # truss pair blocks (lower ring): bases at +/-60 land on the mirror cage's stub tubes at 90/210/330
STRUTS = [45, 135, 225, 315]         # 3/4" square posts between the rings; also the wire-spider anchors
CLOCK_DEG = 4                        # secondary clocking range (+/- deg) from the hub's pull-screw slots
STRUT_SQ = 0.75
QUAD = [0, 90, 180, 270]             # straight 4-vane spider blocks (0 deg shared with the curved set)
FINDER = 150                         # Waypoint finder (UniGuide 50) bracket on the upper ring
FOCUSER = 180
RAIL_Z = 2.6                         # focuser board rails at z = +/-2.6
PP_GAP = 0.06                        # nominal push-pull gap between board and rails
BOARD_Y, BOARD_Z = 7.3, 6.4
PP = [(-3.0, +RAIL_Z), (-3.0, -RAIL_Z), (+3.0, +RAIL_Z)]   # push-pull points (y, z) on the board

TB = I["board_t"]
RAIL_X = -(R_IN + TB + PP_GAP + 0.25)
# Destiny 180 Professional: aluminium vanes 1.5" tall x 1/16" thick, each end has a
# built-in 1/4-20 clinch nut fed by a radial screw from outside the tube wall.
VANE_H = 1.5
SPIDER_BLK = dict(radial=0.75, tang=1.0, tall=1.75)   # cut from 3/4" 6061 plate
SPIDER_SEAT_R = R_IN + SPIDER_BLK["radial"] / 2      # seat bolt circle (block centre)
y_lo_in = -I["ring_gap"] / 2         # lower ring inner (sky-side) face
y_hi_in = +I["ring_gap"] / 2         # upper ring inner (mirror-side) face


def pol(r, deg):
    a = math.radians(deg)
    return r * math.cos(a), r * math.sin(a)


def ang_of(x, z):
    return math.degrees(math.atan2(z, x)) % 360


# ---------------------------------------------------------------- 2D profiles
def ring_holes(kind):
    """List of (x, z, dia, note) in the ring plane."""
    h = []
    for a in STRUTS:
        x, z = pol(R_BOLT, a)
        h.append((x, z, CLR_14, "strut 1/4-20"))
    if kind == "lower":
        for a in APEX:                       # pair block: 2 bolts, tangential +/-0.5"
            for d in (-0.5, 0.5):
                x, z = pol(R_BOLT, a + math.degrees(d / R_BOLT))
                h.append((x, z, CLR_14, "pair connector 1/4-20"))
    else:
        for a in sorted(set(TOPS) | set(QUAD)):   # spider block seats: curved (0/120/240) + quad (0/90/180/270)
            for d in (-0.3, 0.3):
                x, z = pol(SPIDER_SEAT_R, a + math.degrees(d / SPIDER_SEAT_R))
                h.append((x, z, CLR_14, "spider block 1/4-20"))
        for d in (-0.45, 0.45):              # finder bracket: 2 bolts
            x, z = pol(R_BOLT, FINDER + math.degrees(d / R_BOLT))
            h.append((x, z, CLR_14, "finder bracket 1/4-20"))
    rail_x = RAIL_X                          # rail centre (rails are 0.5" deep in x)
    for z in (RAIL_Z, -RAIL_Z):
        h.append((rail_x, z, CLR_14, "board rail 1/4-20"))
    return h


def lightening_slots(holes, r1=9.2, r2=9.8, land=0.45, max_span=22.0):
    """Arc slots in the gaps between features; returns (a_start, a_end) degree pairs."""
    w = (r2 - r1) / 2
    rc = (r1 + r2) / 2
    feats = sorted(ang_of(x, z) for x, z, d, _ in holes)
    margin = math.degrees((w + land + max(d for *_, d, _n in holes) / 2) / rc)
    slots = []
    for i, a in enumerate(feats):
        b = feats[(i + 1) % len(feats)] + (360 if i == len(feats) - 1 else 0)
        s, e = a + margin, b - margin
        if e - s < 6:
            continue
        n = max(1, math.ceil((e - s) / max_span))
        rib = math.degrees(0.6 / rc) + 2 * math.degrees(w / rc)
        seg = (e - s - (n - 1) * rib) / n
        for k in range(n):
            a0 = s + k * (seg + rib)
            slots.append((a0, a0 + seg))
    return slots, rc, w


def slot_wire(a0, a1, rc, w):
    """Closed arc-slot outline in the XY sketch plane (x, z mapped to X, Y)."""
    p = lambda r, a: (r * math.cos(math.radians(a)) * IN, r * math.sin(math.radians(a)) * IN)
    am = (a0 + a1) / 2
    wp = (cq.Workplane("XY").moveTo(*p(rc + w, a0))
          .threePointArc(p(rc + w, am), p(rc + w, a1))
          .threePointArc((p(rc, a1)[0] + w * IN * math.cos(math.radians(a1 + 90)),
                          p(rc, a1)[1] + w * IN * math.sin(math.radians(a1 + 90))),
                         p(rc - w, a1))
          .threePointArc(p(rc - w, am), p(rc - w, a0))
          .threePointArc((p(rc, a0)[0] - w * IN * math.cos(math.radians(a0 + 90)),
                          p(rc, a0)[1] - w * IN * math.sin(math.radians(a0 + 90))),
                         p(rc + w, a0))
          .close())
    return wp


def ring_plate(kind):
    holes = ring_holes(kind)
    plate = (cq.Workplane("XY").circle(R_OUT * IN).circle(R_IN * IN).extrude(T * IN))
    for x, z, d, _ in holes:
        plate = plate.cut(cq.Workplane("XY").center(x * IN, z * IN).circle(d / 2 * IN).extrude(T * IN))
    slots, rc, w = lightening_slots(holes) if I["lighten"] else ([], 0, 0)
    for a0, a1 in slots:
        plate = plate.cut(slot_wire(a0, a1, rc, w).extrude(T * IN))
    return plate, holes, slots


def board_plate():
    """Focuser board in its own XY sketch plane: X = tube Y (along axis), Y = tube Z."""
    b = cq.Workplane("XY").rect(BOARD_Y * IN, BOARD_Z * IN).extrude(TB * IN)
    b = b.edges("|Z").fillet(0.25 * IN)
    b = b.cut(cq.Workplane("XY").circle(I["ft_clear_dia"] / 2 * IN).extrude(TB * IN))
    for k in range(I["ft_bolt_n"]):
        a = 45 + k * 360 / I["ft_bolt_n"]
        x, y = pol(I["ft_bolt_circle"] / 2, a)
        b = b.cut(cq.Workplane("XY").center(x * IN, y * IN).circle(0.136 / 2 * IN).extrude(TB * IN))  # #8-32 tap
    for yy, zz in PP:
        b = b.cut(cq.Workplane("XY").center((yy - 0.3) * IN, -zz * IN).circle(TAP_10 / 2 * IN).extrude(TB * IN))  # pull (tapped)
    return b


# ---------------------------------------------------------------- 3D placement
def to_tube_ring(plate, y_face, facing_up):
    """Sketch XY (x, z) -> tube (x, y, z): rotate so sketch +Y -> tube +Z, thickness along Y."""
    s = plate.rotate((0, 0, 0), (1, 0, 0), 90)          # sketch Y -> Z, thickness Z -> -Y
    if facing_up:                                         # thickness should grow +Y from y_face
        s = s.translate((0, (y_face + T) * IN, 0))
    else:
        s = s.translate((0, y_face * IN, 0))
    return s


def spider_blocks(angles, tip_hole=None):
    """Spider towers on the sky face of the upper ring. Each is cut flat from 3/4" plate
    (1.0" tangential x 1.75" tall), stands on the ring with 2x 1/4-20 tapped into its foot,
    and presents a 1.75" tall face at the ring ID, standing in for the tube wall the Destiny
    vanes were made to screw against. A radial 1/4" screw passes through the tower into the
    vane's clinch nut at mid-vane height. The quad set uses the same tower with a through
    hole for a threaded tension rod and outside nut."""
    tip = tip_hole or I["vane_tip_hole"]
    b = SPIDER_BLK
    y_mid = y_hi_in + T + b["tall"] / 2
    y_hole = y_hi_in + T + 0.125 + VANE_H / 2            # vane sits 1/8" above the ring
    blocks = None
    for a in angles:
        x, z = pol(SPIDER_SEAT_R, a)
        blk = (cq.Workplane("XY").box(b["radial"] * IN, b["tall"] * IN, b["tang"] * IN)
               .rotate((0, 0, 0), (0, 1, 0), -a)
               .translate((x * IN, y_mid * IN, z * IN)))
        hx, hz = pol(R_IN - 0.05, a)
        hole = cq.Solid.makeCylinder(tip / 2 * IN, (b["radial"] + 0.1) * IN,
                                     cq.Vector(hx * IN, y_hole * IN, hz * IN),
                                     cq.Vector(math.cos(math.radians(a)), 0, math.sin(math.radians(a))))
        blk = blk.cut(cq.Workplane("XY").add(hole))
        blocks = blk if blocks is None else blocks.union(blk)
    return blocks


WIRE_SENSE = {45: +1, 135: -1, 225: +1, 315: -1}   # both wires of a post land on the same side; neighbours alternate
EXT_H = 2.3                                          # post extension blocks above the upper ring (wire anchors)
EXT_RAD = 1.0                                        # ...1.0" radial x 0.75" tangential, one 5/16-18 bolt into the post end


def post_extensions():
    """4 blocks, 1.0" radial x 3/4" tangential, standing on the sky face of the upper ring at
    the post angles, each held by one 5/16-18 x 3" through block + ring into the post's tapped
    end (plus a 1/8" dowel so it cannot rotate). They carry the upper wire anchors ~1.9" above
    the ring; the wire pull (~75 lb) puts ~140 in-lb on the joint, which a 5/16 preload of
    ~2500 lb holds with a 3x margin against the face lifting."""
    y0 = y_hi_in + T
    blocks = None
    for a in STRUTS:
        x, z = pol(R_BOLT, a)
        b = (cq.Workplane("XY").box(EXT_RAD * IN, EXT_H * IN, STRUT_SQ * IN)
             .rotate((0, 0, 0), (0, 1, 0), -a).translate((x * IN, (y0 + EXT_H / 2) * IN, z * IN)))
        b = b.cut(cq.Workplane("XZ").center(x * IN, z * IN).circle(0.332 / 2 * IN).extrude(-EXT_H * IN)
                  .translate((0, y0 * IN, 0)))
        blocks = b if blocks is None else blocks.union(b)
    return blocks


def wire_spider(wire_dia=0.025, hub_dia=2.4, hub_wall=0.25, hub_y0=2.66, hub_top=5.9,
                y_anchor_hi=None, y_anchor_lo=0.9, offset_deg=50, stud_tang=0.15, senses=None):
    """Wire spider v2: long hollow hub, wires in two planes 3" apart.

    Why v2: the v1 hub was 1.3" tall, so its two wire planes were only 1.1" apart while the
    secondary's weight hangs ~2.4" below the hub centre. Tilt stiffness was ~1900 in-lb/rad
    and the focal point wandered ~1.2 mm from horizon to zenith (cage_fe.py). The v2 hub is a
    2.4" OD tube from the holder's top plate up past the upper ring; the upper wires anchor on
    post-extension blocks above the ring, the lower wires on the posts between the rings.
    Each post's high anchor runs DOWN to the hub's low rim and its low anchor runs UP to the
    high rim (a V, for axial stiffness); both land on the same side of the hub, offset_deg
    round from the post (50 deg, so the two posts feeding one side of the hub land 0.2" apart),
    and neighbouring posts alternate sides so no gravity load twists
    the hub. The two studs of a post sit +/-stud_tang either side of its centre line so the
    V's two wires pass ~0.1" apart where they cross. Projected on the aperture the 8 wires
    lie in only 2 directions: a 4-spike star image (78/102 deg X).
    Wire ends: ball-end (guitar) or crimped stop inside the hub bore, through 8 radial holes
    in the wall; #10-32 studs through the posts/extensions with the nut outside.
    Heights from the secondary centre (y = 0). Hub bottom plate = holder top plate."""
    senses = senses or WIRE_SENSE
    hub_r = hub_dia / 2
    if y_anchor_hi is None:
        y_anchor_hi = y_hi_in + T + EXT_H - 0.4
    hub_h = hub_top - hub_y0
    plate_h = 0.3
    hub = (cq.Workplane("XZ").circle(hub_r * IN).extrude(-hub_h * IN).translate((0, hub_y0 * IN, 0)))
    bore = (cq.Workplane("XZ").circle((hub_r - hub_wall) * IN).extrude(-(hub_h - plate_h) * IN)
            .translate((0, (hub_y0 + plate_h) * IN, 0)))
    hub = hub.cut(bore)
    hub = hub.cut(cq.Workplane("XZ").circle(0.135 * IN).extrude(-hub_h * IN).translate((0, hub_y0 * IN, 0)))
    for k in range(3):
        a0 = 90 + 120 * k
        # push screws: #10-32 tapped through the bottom plate at r 1.0, tips bear on the body's top face
        hx, hz = pol(1.0, a0)
        hub = hub.cut(cq.Workplane("XZ").center(hx * IN, hz * IN).circle(0.159 / 2 * IN)
                      .extrude(-plate_h * IN).translate((0, hub_y0 * IN, 0)))
        # pull screws at r 0.7 pass through +/-CLOCK_DEG arc slots (clock the secondary, then lock)
        for d in [x * 0.5 for x in range(-2 * CLOCK_DEG, 2 * CLOCK_DEG + 1)]:
            hx, hz = pol(0.7, a0 + d)
            hub = hub.cut(cq.Workplane("XZ").center(hx * IN, hz * IN).circle(0.1 * IN)
                          .extrude(-plate_h * IN).translate((0, hub_y0 * IN, 0)))
    y_hub_lo, y_hub_hi = hub_y0 + plate_h + 0.15, hub_top - 0.15
    r_face = R_BOLT - STRUT_SQ / 2                       # post inner face radius
    wires = studs = None
    runs = []
    for a in STRUTS:
        ux, uz = math.cos(math.radians(a)), math.sin(math.radians(a))
        tx, tz = pol(1.0, a + 90)                        # tangential unit vector on the post face
        for y_anchor, y_hub, tg, rf in ((y_anchor_hi, y_hub_lo, +stud_tang, R_BOLT - EXT_RAD / 2),
                                        (y_anchor_lo, y_hub_hi, -stud_tang, r_face)):
            ax, az = rf * ux + tg * tx, rf * uz + tg * tz
            p0 = cq.Vector(ax * IN, y_anchor * IN, az * IN)
            hx, hz = pol(hub_r, a + senses[a] * offset_deg)
            p1 = cq.Vector(hx * IN, y_hub * IN, hz * IN)
            d = p1 - p0
            w = cq.Workplane("XY").add(cq.Solid.makeCylinder(wire_dia / 2 * IN, d.Length, p0, d.normalized()))
            wires = w if wires is None else wires.union(w)
            runs.append((a, y_anchor, round(d.Length / IN, 2)))
            # wire hole through the hub wall (ball end / stop sleeve sits inside the bore)
            hub = hub.cut(cq.Workplane("XY").add(cq.Solid.makeCylinder(
                0.02 * IN, (hub_wall + 0.2) * IN, cq.Vector((hx - 0.1 * hx / hub_r) * IN, y_hub * IN, (hz - 0.1 * hz / hub_r) * IN),
                cq.Vector(hx, 0, hz).normalized() * -1)))
            # #10-32 tension stud radially through the post / extension, nut + washer on the outside
            stud = cq.Workplane("XY").add(cq.Solid.makeCylinder(
                0.095 * IN, (R_BOLT + STRUT_SQ / 2 - rf + 0.6) * IN,
                cq.Vector((ax - 0.1 * ux) * IN, y_anchor * IN, (az - 0.1 * uz) * IN),
                cq.Vector(ux, 0, uz)))
            nx, nz = (R_BOLT + STRUT_SQ / 2) * ux + tg * tx, (R_BOLT + STRUT_SQ / 2) * uz + tg * tz
            nut = cq.Workplane("XY").add(cq.Solid.makeCylinder(
                0.19 * IN, 0.18 * IN, cq.Vector(nx * IN, y_anchor * IN, nz * IN), cq.Vector(ux, 0, uz)))
            sn = stud.union(nut)
            studs = sn if studs is None else studs.union(sn)
    return dict(hub=hub, wires=wires, studs=studs, extensions=post_extensions()), runs


QUAD_VANE = dict(t=0.020, h=1.5)                     # 0.5 mm stainless, 1.5" tall
QUAD_HUB_DIA = 2.6                                   # inside the 3.5" secondary's shadow with the offset
QUAD_HUB_BORE = 2.0                                  # hollow upper part; the centring gauge plug drops into it


def quad_spider(hub_y0=2.66):
    """Straight 4-vane spider anchored on the four posts BETWEEN the rings (45/135/225/315 deg).

    Vanes: 0.020" x 1.5" stainless strips from the hub to the posts, just under the upper ring
    (vane top 0.05" below the ring's inner face). Outer end: a 1/2" fold riveted to a #10-32
    stud that passes radially through the post, nut and washer outside = tension, so the
    pull lands on a beam bolted to both rings, not on a block cantilevered off one ring.
    Inner end: the vane enters a 0.025" saw slot in the hub wall and is pinned by two #4-40
    screws. Hub: 2.6" dia 6061 from the holder's top plate (y = 2.66) to just under the ring;
    the bottom 0.3" is the holder's top plate (centre retainer, 3 push screws at r 1.1,
    3 pull screws in +/-4 deg clocking slots at r 0.8), reached from the sky end through the
    2.0" bore. Spikes at 45 deg to the altitude axis. Cage FE: see cage_fe.py spider='quad'."""
    t, h = QUAD_VANE["t"], QUAD_VANE["h"]
    y_top = y_hi_in - 0.05                             # vane top just under the upper ring
    y_c = y_top - h / 2
    hub_r = QUAD_HUB_DIA / 2
    hub_h = y_top - hub_y0
    plate_h = 0.3
    hub = cq.Workplane("XZ").circle(hub_r * IN).extrude(-hub_h * IN).translate((0, hub_y0 * IN, 0))
    hub = hub.cut(cq.Workplane("XZ").circle(QUAD_HUB_BORE / 2 * IN).extrude(-(hub_h - plate_h) * IN)
                  .translate((0, (hub_y0 + plate_h) * IN, 0)))
    hub = hub.cut(cq.Workplane("XZ").circle(0.135 * IN).extrude(-hub_h * IN).translate((0, hub_y0 * IN, 0)))
    for k in range(3):
        a0 = 90 + 120 * k
        hx, hz = pol(1.1, a0)
        hub = hub.cut(cq.Workplane("XZ").center(hx * IN, hz * IN).circle(0.159 / 2 * IN)
                      .extrude(-plate_h * IN).translate((0, hub_y0 * IN, 0)))
        for d in [x * 0.5 for x in range(-2 * CLOCK_DEG, 2 * CLOCK_DEG + 1)]:
            hx, hz = pol(0.8, a0 + d)
            hub = hub.cut(cq.Workplane("XZ").center(hx * IN, hz * IN).circle(0.1 * IN)
                          .extrude(-plate_h * IN).translate((0, hub_y0 * IN, 0)))
    r_face = R_BOLT - STRUT_SQ / 2
    vanes = studs = None
    for a in STRUTS:
        ux, uz = pol(1.0, a)
        r0, r1 = QUAD_HUB_BORE / 2 + 0.05, r_face - 0.05   # slot 0.25" into the hub wall; ends just short of the post face
        L = r1 - r0
        v = (cq.Workplane("XY").box(L * IN, h * IN, t * IN)
             .translate(((r0 + L / 2) * IN, y_c * IN, 0))
             .rotate((0, 0, 0), (0, 1, 0), -a))
        hub = hub.cut(cq.Workplane("XY").box(0.3 * IN, (h + 0.1) * IN, 0.025 * IN)
                      .translate(((hub_r - 0.125) * IN, y_c * IN, 0)).rotate((0, 0, 0), (0, 1, 0), -a))
        vanes = v if vanes is None else vanes.union(v)
        stud = cq.Workplane("XY").add(cq.Solid.makeCylinder(
            0.095 * IN, (STRUT_SQ + 0.7) * IN,
            cq.Vector(r1 * ux * IN, y_c * IN, r1 * uz * IN), cq.Vector(ux, 0, uz)))
        nut = cq.Workplane("XY").add(cq.Solid.makeCylinder(
            0.19 * IN, 0.18 * IN,
            cq.Vector((R_BOLT + STRUT_SQ / 2) * ux * IN, y_c * IN, (R_BOLT + STRUT_SQ / 2) * uz * IN),
            cq.Vector(ux, 0, uz)))
        sn = stud.union(nut)
        studs = sn if studs is None else studs.union(sn)
    return dict(hub=hub, vanes=vanes, studs=studs), dict(
        vane_len_in=round(L, 2), vane_centre_y=round(y_c, 3), hub_top_y=round(y_top, 3), vane_angles=STRUTS)


ALIGN_BAR_X = 6.0          # alignment bar centre plane (in), on the side opposite the focuser


def alignment_bar():
    """Removable tool for squaring the focuser: a 1/2" square 6061 bar at secondary height
    (y = 0) spanning the 45 and 315 degree posts, ends cut at 45 degrees to sit flat on the
    posts' inner faces, one #10-32 screw into each post. A 1/16" target hole on the X axis
    (the designed focuser axis) faces the focuser. Remove before observing: it sits in the beam."""
    r_face = R_BOLT - STRUT_SQ / 2
    z_end = (r_face - ALIGN_BAR_X * math.cos(math.radians(45))) / math.sin(math.radians(45))
    bar = cq.Workplane("XY").box(0.5 * IN, 0.5 * IN, 2 * (z_end + 0.6) * IN).translate((ALIGN_BAR_X * IN, 0, 0))
    for a in (45, 315):                                  # trim each end flush with the post face
        ux, uz = math.cos(math.radians(a)), math.sin(math.radians(a))
        cutter = (cq.Workplane("XY").box(4 * IN, 4 * IN, 4 * IN)
                  .translate(((r_face + 2) * IN, 0, 0))
                  .rotate((0, 0, 0), (0, 1, 0), -a))
        bar = bar.cut(cutter)
    target = cq.Workplane("YZ").circle(0.03125 * IN).extrude(0.5 * IN).translate(((ALIGN_BAR_X - 0.25) * IN, 0, 0))
    return bar.cut(target)


GAUGE_ARMS = (45, 135)     # the two bars of the X gauge (deg), over the posts: clear of the quad vanes, towers and finder
GAUGE_PLUG = 1.95          # drops into the quad hub's 2.0" bore (the hub sits just under the ring)


def centering_gauge():
    """Removable plywood X-gauge for centring the wire-spider hub while the wires are tensioned:
    two 1/2" x 1.5" bars across the ring (along 30-210 and 90-270 deg, clear of every tower,
    bracket, extension block and wire), four 1/4" spigot feet that locate on the ring ID, and a
    2.45" centre bore that must slip freely over the 2.40" hub (centred to +/-0.025")."""
    y0 = y_hi_in + T
    g = None
    for a in GAUGE_ARMS:
        bar = (cq.Workplane("XY").box(2 * (R_OUT - 0.1) * IN, 0.5 * IN, 1.5 * IN)
               .rotate((0, 0, 0), (0, 1, 0), -a).translate((0, (y0 + 0.25) * IN, 0)))
        g = bar if g is None else g.union(bar)
        for sgn in (1, -1):                                   # spigot feet on the ring ID
            x, z = pol(sgn * (R_IN - 0.01 - 0.25), a)
            foot = (cq.Workplane("XY").box(0.5 * IN, 0.25 * IN, 1.5 * IN)
                    .rotate((0, 0, 0), (0, 1, 0), -a).translate((x * IN, (y0 - 0.125) * IN, z * IN)))
            foot = foot.intersect(cq.Workplane("XZ").circle((R_IN - 0.01) * IN).extrude(-1 * IN).translate((0, (y0 - 0.5) * IN, 0)))
            g = g.union(foot)
    for a in STRUTS:                                          # pockets over the post bolt heads
        x, z = pol(R_BOLT, a)
        g = g.cut(cq.Workplane("XY").box(1.0 * IN, 0.6 * IN, 1.6 * IN).rotate((0, 0, 0), (0, 1, 0), -a)
                  .translate((x * IN, y0 * IN, z * IN)))
    plug = (cq.Workplane("XZ").circle(GAUGE_PLUG / 2 * IN).extrude(1.0 * IN)
            .translate((0, y0 * IN, 0)))                  # hangs 1.0" below the bar bottom, into the hub bore
    g = g.union(plug)
    return g, None


def build():
    parts = {}
    lower, lower_holes, lower_slots = ring_plate("lower")
    upper, upper_holes, upper_slots = ring_plate("upper")
    parts["ring_lower"] = to_tube_ring(lower, y_lo_in - T, True)      # occupies y_lo_in-T .. y_lo_in
    parts["ring_upper"] = to_tube_ring(upper, y_hi_in, True)          # occupies y_hi_in .. y_hi_in+T

    # struts: 3/4" square 6061 posts, ends tapped 1/4-20, square to the radius
    struts = None
    for a in STRUTS:
        x, z = pol(R_BOLT, a)
        s = (cq.Workplane("XY").box(STRUT_SQ * IN, I["ring_gap"] * IN, STRUT_SQ * IN)
             .rotate((0, 0, 0), (0, 1, 0), -a).translate((x * IN, 0, z * IN)))
        struts = s if struts is None else struts.union(s)
    parts["struts"] = struts

    # board rails: 0.5 (x) x 0.75 (z) 6061 bar between the rings
    rails = None
    rx = RAIL_X
    for z in (RAIL_Z, -RAIL_Z):
        r = (cq.Workplane("XY").box(0.5 * IN, I["ring_gap"] * IN, 0.75 * IN)
             .translate((rx * IN, 0, z * IN)))
        rails = r if rails is None else rails.union(r)
    parts["board_rails"] = rails

    # focuser board: inner face at R_IN, outer face at R_IN + T
    b = board_plate()
    b = b.rotate((0, 0, 0), (0, 1, 0), -90)               # sketch Z (thickness) -> tube -X ... check below
    bb = b.val().BoundingBox()
    b = b.translate((-(R_IN * IN) - bb.xmax, 0, 0))       # inner face flush at x = -R_IN
    # sketch X was along the tube axis: turn it onto tube Y
    cx = -(R_IN + TB / 2) * IN
    parts["focuser_board"] = b.rotate((cx, 0, 0), (cx + 1, 0, 0), -90)

    parts["spider_blocks"] = spider_blocks(TOPS)

    # Waypoint finder bracket: riser on the sky face of the upper ring at FINDER deg,
    # reaching out past the ring OD; a bought Synta-style finder shoe bolts to its outer face.
    rb0, rb1 = R_BOLT - 0.6, R_OUT + 1.1                # radial span of the riser
    riser = (cq.Workplane("XY").box((rb1 - rb0) * IN, 0.75 * IN, 1.0 * IN)
             .translate(((rb0 + rb1) / 2 * IN, (y_hi_in + T + 0.375) * IN, 0)))
    plate = (cq.Workplane("XY").box(0.375 * IN, 2.75 * IN, 1.4 * IN)        # shoe mounting plate, hangs toward the mirror
             .translate(((rb1 - 0.1875) * IN, (y_hi_in + T + 0.75 - 1.375) * IN, 0)))
    bracket = riser.union(plate).rotate((0, 0, 0), (0, 1, 0), -FINDER)
    parts["finder_bracket"] = bracket

    # UniGuide 50 (265 mm, ~60 mm body) + G3M662C, axis parallel to the tube, objective toward the sky
    fr = R_OUT + 1.1 + 0.5 + 1.25                       # shoe height + half body
    fx, fz = pol(fr, FINDER)
    scope = (cq.Workplane("XZ").center(fx * IN, fz * IN).circle(1.2 * IN)
             .extrude(-10.4 * IN).translate((0, (y_hi_in + T + 1.6 - 10.4) * IN, 0)))
    cam = (cq.Workplane("XZ").center(fx * IN, fz * IN).circle(0.8 * IN)
           .extrude(-1.6 * IN).translate((0, (y_hi_in + T + 1.6 - 10.4 - 1.6) * IN, 0)))
    parts["waypoint_finder"] = scope.union(cam)

    # pair connectors under the lower ring (concept: needs an angle fixture to drill pole bores)
    conns = None
    for a in APEX:
        x, z = pol(R_BOLT, a)
        c = (cq.Workplane("XY").box(1.6 * IN, 1.25 * IN, 1.6 * IN)
             .rotate((0, 0, 0), (0, 1, 0), -a)
             .translate((x * IN, (y_lo_in - T - 0.625) * IN, z * IN)))
        conns = c if conns is None else conns.union(c)
    parts["pair_connectors_concept"] = conns

    info = dict(lower_holes=lower_holes, upper_holes=upper_holes,
                lower_slots=lower_slots, upper_slots=upper_slots)
    return parts, info, dict(lower=lower, upper=upper, board=board_plate())


if __name__ == "__main__":
    parts, info, flats = build()
    for k, v in parts.items():
        bb = v.val().BoundingBox()
        print(f"{k:26s} x {bb.xmin/IN:6.2f}..{bb.xmax/IN:6.2f}  y {bb.ymin/IN:6.2f}..{bb.ymax/IN:6.2f}  z {bb.zmin/IN:6.2f}..{bb.zmax/IN:6.2f}")
