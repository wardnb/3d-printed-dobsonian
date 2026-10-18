"""
Self-aligning secondary holder (v2).

The mirror is never glued straight onto the 45-degree body. It is bonded on the bench to a
flat CARRIER plate inside a GLUING JIG:

  * jig base: a pocket that matches the mirror outline; the mirror lies in it FACE DOWN on
    lens tissue, so its front surface is the reference and it cannot rotate or slide;
  * carrier: rests on the mirror's back on three 0.012" pads, with neutral-cure RTV in
    three wells (the pads set an even glue gap so the bond cannot tilt the glass);
  * jig bridge: a strip on two 1/2" standoffs whose two pins drop through the carrier's
    dowel holes, fixing the carrier's position and rotation relative to the mirror.

The carrier's dowel and screw pattern is centred on the HOLDER AXIS, which sits
OFF_MAJOR from the mirror centre along the major axis, so the diagonal offset is built
in. On the scope, the carrier bolts to the body's 45-degree face on the same two dowels
(one round hole, one slot), so it only fits one way and returns to the same place.
Carrier and body stay inside the mirror's shadow, so they add no obstruction.

Frame: inches in, mm out. Origin = where the tube axis meets the mirror's front surface;
tube axis = +Y toward the sky; focuser on -X; mirror front faces -X-Y.
"""
import math

import cadquery as cq

IN = 25.4
P = dict(
    minor=3.5,            # secondary minor axis (v2: 3.5", decided after the review)
    thick=0.70,           # INPUT: secondary thickness (3.5" diagonals are typically ~0.7")
    focal_ratio=3.9,
    pad_h=0.012,          # three contact pads set the RTV gap
    inset=0.12,           # carrier inset from the mirror edge along the minor axis
    inset_major=0.30,     # ...and along the major axis (it sits deeper, so needs more to stay in the shadow)
    carrier_t=0.25,       # carrier plate (1/4" 6061)
    body_r=1.50,          # body cylinder radius: inside the mirror's shadow even with the offset
    body_top=2.6,         # body top face height above the origin (along Y)
    dowel_dx=1.35,        # dowels at holder axis +/- this along the major axis
    jig_clear=0.010,      # jig pocket clearance per side
    jig_pocket=0.375,     # jig pocket depth (mirror sits face down in it)
)
MAJOR = P["minor"] * math.sqrt(2)
OFFSET = P["minor"] / (4 * P["focal_ratio"])          # per-axis offset (toward primary, away from focuser)
OFF_MAJOR = OFFSET * math.sqrt(2)                     # the same offset measured along the major axis

U = cq.Vector(1, -1, 0).normalized()                  # in-plane major axis (toward the primary)
NB = cq.Vector(1, 1, 0).normalized()                  # mirror-back normal


def holder_axis_local():
    """Holder (tube) axis point in the mirror-centred local frame."""
    return -OFF_MAJOR, 0.0


def carrier_flat():
    """Carrier in a mirror-centred frame: X = major axis toward the primary, Y = minor axis,
    Z = thickness; the pads touch the mirror back at Z = 0, plate from Z = pad_h up."""
    a = MAJOR / 2 - P["inset_major"]
    b = P["minor"] / 2 - P["inset"]
    t, ph = P["carrier_t"], P["pad_h"]
    c = cq.Workplane("XY").ellipse(a * IN, b * IN).extrude(t * IN).translate((0, 0, ph * IN))
    for k in range(3):                                  # pads, 0.35" dia, at 120 deg
        ang = math.radians(90 + 120 * k)
        px, py = 0.55 * a * math.cos(ang), 0.55 * b * math.sin(ang)
        c = c.union(cq.Workplane("XY").center(px * IN, py * IN).circle(0.175 * IN).extrude(ph * IN))
    for k in range(3):                                  # RTV wells, 0.5" dia x 0.04" deep
        ang = math.radians(30 + 120 * k)
        wx, wy = 0.55 * a * math.cos(ang), 0.55 * b * math.sin(ang)
        c = c.cut(cq.Workplane("XY").center(wx * IN, wy * IN).circle(0.25 * IN)
                  .extrude(0.04 * IN).translate((0, 0, ph * IN)))
    ax, _ = holder_axis_local()
    for k in range(3):                                  # 3x #8 clearance into the body, clear of pads and wells
        ang = math.radians(120 * k)
        sx, sy = ax + 0.75 * math.cos(ang), 0.75 * math.sin(ang)
        c = c.cut(cq.Workplane("XY").center(sx * IN, sy * IN).circle(0.177 / 2 * IN).extrude(1 * IN))
    c = c.cut(cq.Workplane("XY").center((ax - P["dowel_dx"]) * IN, 0).circle(0.0635 * IN).extrude(1 * IN))
    c = c.cut(cq.Workplane("XY").center((ax + P["dowel_dx"]) * IN, 0)
              .slot2D(0.25 * IN, 0.127 * IN, 0).extrude(1 * IN))
    return c


def jig_flat():
    """Jig base and bridge, flat, in the same mirror-centred frame."""
    a, b = MAJOR / 2 + P["jig_clear"], P["minor"] / 2 + P["jig_clear"]
    L, W = MAJOR + 1.8, P["minor"] + 1.4
    base = cq.Workplane("XY").rect(L * IN, W * IN).extrude(0.5 * IN)
    base = base.edges("|Z").fillet(0.25 * IN)
    base = base.cut(cq.Workplane("XY").ellipse(a * IN, b * IN).extrude(P["jig_pocket"] * IN)
                    .translate((0, 0, (0.5 - P["jig_pocket"]) * IN)))
    # finger notches at the minor-axis ends to lift the mirror out
    for sy in (-1, 1):
        base = base.cut(cq.Workplane("XY").center(0, sy * b * IN).circle(0.4 * IN)
                        .extrude(P["jig_pocket"] * IN).translate((0, 0, (0.5 - P["jig_pocket"]) * IN)))
    sx = L / 2 - 0.45
    for x in (-sx, sx):                                  # standoff holes (#8-32 tapped)
        base = base.cut(cq.Workplane("XY").center(x * IN, 0).circle(0.136 / 2 * IN).extrude(0.5 * IN))
    bridge = cq.Workplane("XY").rect(L * IN, 1.0 * IN).extrude(0.25 * IN)
    bridge = bridge.edges("|Z").fillet(0.2 * IN)
    ax, _ = holder_axis_local()
    for x in (ax - P["dowel_dx"], ax + P["dowel_dx"]):   # press-fit 1/8" pins
        bridge = bridge.cut(cq.Workplane("XY").center(x * IN, 0).circle(0.1240 / 2 * IN).extrude(0.25 * IN))
    for x in (-sx, sx):
        bridge = bridge.cut(cq.Workplane("XY").center(x * IN, 0).circle(0.177 / 2 * IN).extrude(0.25 * IN))
    return base, bridge


def place(solid_local, n0, mirror_centred=True):
    """Local frame -> tube frame. n0 = depth (in) of local Z=0 behind the mirror front along NB.
    Mirror-centred frames are shifted OFF_MAJOR along U (toward the primary)."""
    origin = NB * (n0 * IN) + (U * (OFF_MAJOR * IN) if mirror_centred else cq.Vector(0, 0, 0))
    plane = cq.Plane(origin=origin.toTuple(), xDir=U.toTuple(), normal=NB.toTuple())
    return cq.Workplane("XY").add(solid_local.val().moved(cq.Location(plane)))


def build():
    t = P["thick"]
    parts = {}
    m = cq.Workplane("XY").ellipse(MAJOR / 2 * IN, P["minor"] / 2 * IN).extrude(t * IN)
    parts["secondary_mirror"] = place(m, 0.0)
    parts["carrier"] = place(carrier_flat(), t)
    n_back = t + P["pad_h"] + P["carrier_t"]
    cyl = (cq.Workplane("XZ").circle(P["body_r"] * IN).extrude(-(P["body_top"] + 4.0) * IN)
           .translate((0, -4.0 * IN, 0)))
    cutter = place(cq.Workplane("XY").box(30 * IN, 30 * IN, 30 * IN).translate((0, 0, -15 * IN)),
                   n_back, mirror_centred=False)
    body = cyl.cut(cutter)
    for k in range(3):                                   # pull-screw taps (r 0.7); push screws (r 1.0)
        a = math.radians(90 + 120 * k)                   # bear on the plain top face, so it can rotate
        hx, hz = 0.7 * math.cos(a), 0.7 * math.sin(a)
        body = body.cut(cq.Workplane("XZ").center(hx * IN, hz * IN).circle(0.159 / 2 * IN)
                        .extrude(0.6 * IN).translate((0, P["body_top"] * IN, 0)))
    body = body.cut(cq.Workplane("XZ").circle(0.201 / 2 * IN).extrude(1.0 * IN)
                    .translate((0, P["body_top"] * IN, 0)))        # 1/4-20 centre tap
    parts["body"] = body
    return parts


def shadow_check(parts):
    """Project each part down the tube axis and compare with the mirror's shadow."""
    out = {}
    for k, p in parts.items():
        bb = p.val().BoundingBox()
        out[k] = dict(x=(round(bb.xmin / IN, 3), round(bb.xmax / IN, 3)),
                      z=(round(bb.zmin / IN, 3), round(bb.zmax / IN, 3)))
    return out


if __name__ == "__main__":
    parts = build()
    print(shadow_check(parts))
    print("mirror/carrier", round(parts["secondary_mirror"].intersect(parts["carrier"]).val().Volume(), 3),
          "carrier/body", round(parts["carrier"].intersect(parts["body"]).val().Volume(), 3))
    print("offset per axis", round(OFFSET, 3), "along major", round(OFF_MAJOR, 3))
