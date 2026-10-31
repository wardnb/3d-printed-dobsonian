"""
New primary mirror cell (2026-10-30): 9-point flotation, rigid edge support, zero-play push-pull.

Replaces the DobStuff cell (mirror glued to a 3/4" ply triangle that rides on spring studs and is only held
sideways by knob friction). The mirror is debonded and floats on nine pads.

  * 9-point flotation: three 1/4" 6061 triangles, each on a 3/8" steel ball in 90-degree seats at its
    centroid; pads at r1 (one per triangle, on its axis) and r2 at +/-BETA. Radii from cell_support_fe.py
    (Kirchhoff plate, equal pad loads, power removed): r1 = 0.431 R, r2 = 0.670 R, BETA = 33.1 deg gives
    ~1 nm RMS surface for a plate of the sandwich's stiffness (D ~ 4e5 N m ASSUMED).
    For a sandwich, put each pad under a puck: map the pucks through the back plate before drilling.
  * frame: 1/2" 6061 (MIC-6 preferred: it stays flat after pocketing), triangular, corners on the three
    collimation bolts at r_bolt next to the truss stubs (90/210/330 deg, mcage_fe.py), lugs out to the
    edge posts.
  * edge support: two posts at 225 and 315 deg (+/-45 deg from straight down at the horizon, -Z) whose
    Delrin faces span BOTH glass plates of the sandwich, centred on the mirror's mid-thickness; set touching
    (radial slots), then clamped. Guard posts at 0, 90, 180 deg sit 0.5 mm off the edge and carry safety
    tabs 1 mm above the face (they never touch the glass in use).
  * collimation: three 5/16-24 bolts through close-fit flanged bronze bushings in the mirror board,
    threaded into the frame corners; three 1/4-20 push screws in threaded inserts in the board bear on the
    frame. No springs. The bolts hold the cell sideways; friction under the push screws takes the first
    load, the bushing clearance (0.001-0.002") is the worst case.
  * an 80 mm fan under the frame's centre hole blows on the back plate.

Frame: tube axis +Y toward the sky, mirror face at y = 0 here (dob_model translates by y_mirror);
angles in the x-z plane from +X toward +Z, as everywhere else (stubs at 90/210/330, down at the horizon = 270).
"""
import math

import cadquery as cq
from shapely.geometry import Polygon, Point, box as sbox
from shapely.ops import unary_union
from shapely import affinity

IN = 25.4
C = dict(
    mirror_dia=16.0, mirror_thick=1.65,
    r1=0.431, r2=0.670, beta=33.1,         # pad layout as a fraction of R (cell_support_fe.py)
    tri_angles=(90, 210, 330),             # triangles and bolts clocked to the truss stubs
    pad_dia=1.0, pad_t=0.25, cork=0.0625,  # Delrin pads with a cork face
    tri_t=0.25, ball=0.375,
    frame_t=0.5, r_bolt=6.5,
    fan_hole=3.2,
    load_posts=(225, 315), guard_posts=(90, 210, 330),
    post_guard=(0.5, 0.5),                 # (radial, tangential)
    gusset_t=0.5, gusset_base=1.8, gusset_top=0.75,   # load posts: 1/2" 6061 gussets standing on edge
    arm_w=1.5, hub_r=2.45, branch_w=1.4, fan_holes=2.815,
    edge_pad_t=0.125, edge_pad_h=1.4,     # Delrin face on the load posts, spans both plates
    guard_gap=0.02, tab_over=0.2, tab_gap=0.04, tab_t=0.125,
    board_gap=0.6,                         # frame underside to mirror-board top (push-pull range +/-0.25)
)


def pol(r, a):
    return r * math.cos(math.radians(a)), r * math.sin(math.radians(a))


def levels(c=C):
    """y of each layer, mirror face = 0."""
    L = {}
    L["face"] = 0.0
    L["back"] = -c["mirror_thick"]
    L["tri_top"] = L["back"] - c["pad_t"] - c["cork"]
    L["tri_bot"] = L["tri_top"] - c["tri_t"]
    L["post_top"] = L["tri_bot"] - 0.12            # ball sits in 90-deg seats in both
    L["frame_top"] = L["post_top"] - 1.65
    L["frame_bot"] = L["frame_top"] - c["frame_t"]
    L["board_top"] = L["frame_bot"] - c["board_gap"]
    L["cg"] = -c["mirror_thick"] / 2
    return L


def pads(c=C):
    R = c["mirror_dia"] / 2
    out = []
    for a in c["tri_angles"]:
        tri = [pol(c["r1"] * R, a)] + [pol(c["r2"] * R, a + s * c["beta"]) for s in (-1, 1)]
        out.append(tri)
    return out


def pivot_xy(tri):
    return sum(p[0] for p in tri) / 3, sum(p[1] for p in tri) / 3


def _poly_to_wp(poly, t):
    """shapely polygon (with holes) -> extruded cq solid, sketch XY, thickness +Z."""
    def ring(coords):
        pts = [(x * IN, y * IN) for x, y in list(coords)[:-1]]
        return cq.Workplane("XY").polyline(pts).close().extrude(t * IN)
    s = ring(poly.exterior.coords)
    for h in poly.interiors:
        s = s.cut(ring(h.coords))
    return s


def frame_poly(c=C):
    """Y frame: hub around the fan hole, an arm to each collimation bolt (and guard post), and a branch
    from the 210/330 arms out to the load gussets at 225/315."""
    R = c["mirror_dia"] / 2
    parts = [Point(0, 0).buffer(c["hub_r"], 64)]
    r_end = R + c["guard_gap"] + c["post_guard"][0] + 0.2
    for a in c["tri_angles"]:
        arm = sbox(0, -c["arm_w"] / 2, r_end, c["arm_w"] / 2)
        parts.append(affinity.rotate(arm, a, origin=(0, 0)))
    for a in c["load_posts"]:
        arm = min(c["tri_angles"], key=lambda t: abs((t - a + 180) % 360 - 180))
        p0 = Point(*pol(c["r_bolt"] - 0.3, arm))
        r_out = R + c["edge_pad_t"] + c["gusset_base"] + 0.2
        p1 = Point(*pol(R + c["edge_pad_t"] - 0.2, a)); p2 = Point(*pol(r_out, a))
        foot = unary_union([p1, p2]).buffer(c["branch_w"] / 2, 16)
        link = unary_union([p0, p1]).buffer(c["branch_w"] / 2, 16)
        parts += [foot.convex_hull, link.convex_hull]
    poly = unary_union(parts).buffer(0.25).buffer(-0.25)
    return poly.difference(Point(0, 0).buffer(c["fan_hole"] / 2, 64))


def frame_holes(c=C):
    """(x, z, dia, note) drilled in the frame."""
    h = []
    for tri in pads(c):
        px, pz = pivot_xy(tri)
        h.append((px, pz, 0.201, "1/4-20 tap: pivot post"))
    for a in c["tri_angles"]:
        x, z = pol(c["r_bolt"], a)
        h.append((x, z, 0.272, "5/16-24 tap: collimation bolt (or a steel insert)"))
    for k in range(4):
        x, z = pol(c["fan_holes"] / math.sqrt(2), 45 + 90 * k)
        h.append((x, z, 0.144, "#6 clearance: 80 mm fan"))
    return h


def post_slots(c=C):
    """Radial slots (centre r, angle, tangential offset, length, width) for the post screws: posts slide
    radially until they touch the edge, then clamp."""
    R = c["mirror_dia"] / 2
    s = []
    for a in c["load_posts"]:
        r0 = R + c["edge_pad_t"]
        for u in (0.4, c["gusset_base"] - 0.4):
            s.append((r0 + u, a, 0.0, 0.4, 0.27))
    for a in c["guard_posts"]:
        s.append((R + c["guard_gap"] + c["post_guard"][0] / 2, a, 0.0, 0.3, 0.205))
    return s


def frame_flat(c=C):
    f = _poly_to_wp(frame_poly(c), c["frame_t"])
    for x, z, d, _ in frame_holes(c):
        f = f.cut(cq.Workplane("XY").center(x * IN, z * IN).circle(d / 2 * IN).extrude(c["frame_t"] * IN))
    for r0, a, d, L, w in post_slots(c):
        tx, tz = pol(1, a + 90)
        x, z = pol(r0, a)
        f = f.cut(cq.Workplane("XY").center((x + d * tx) * IN, (z + d * tz) * IN)
                  .slot2D(L * IN, w * IN, a).extrude(c["frame_t"] * IN))
    return f


def tri_flat(tri, c=C):
    px, pz = pivot_xy(tri)
    hull = unary_union([Point(*p).buffer(c["pad_dia"] / 2 + 0.15, 32) for p in tri]).convex_hull
    t = _poly_to_wp(hull, c["tri_t"])
    for x, z in tri:     # #10-32 tap: pad screw from below
        t = t.cut(cq.Workplane("XY").center(x * IN, z * IN).circle(0.159 / 2 * IN).extrude(c["tri_t"] * IN))
    t = t.cut(cq.Workplane("XY").center(px * IN, pz * IN).circle(0.25 / 2 * IN).extrude(c["tri_t"] * IN))
    return t


def gusset_profile(c=C, L=None):
    """Side profile (u = radius, v = height above the frame top) of a load gusset, Delrin face included."""
    L = L or levels(c)
    R = c["mirror_dia"] / 2
    r0 = R + c["edge_pad_t"]
    h = L["cg"] + c["edge_pad_h"] / 2 - L["frame_top"]
    return [(r0, 0), (r0 + c["gusset_base"], 0), (r0 + c["gusset_top"], h), (r0, h)], h


def gusset_flat(c=C, L=None):
    pts, h = gusset_profile(c, L)
    return cq.Workplane("XY").polyline([(u * IN, v * IN) for u, v in pts]).close().extrude(c["gusset_t"] * IN)


def gusset_solid(c, L, a):
    pts, h = gusset_profile(c, L)
    R = c["mirror_dia"] / 2
    # build in the x-y plane of the tube (x = radius, y = height), thickness along z, then turn to angle a
    g = (cq.Workplane("XY").polyline([(u * IN, (L["frame_top"] + v) * IN) for u, v in pts]).close()
         .extrude(c["gusset_t"] * IN).translate((0, 0, -c["gusset_t"] / 2 * IN)))
    pad = (cq.Workplane("XY").box(c["edge_pad_t"] * IN, c["edge_pad_h"] * IN, c["gusset_t"] * IN)
           .translate(((R + c["edge_pad_t"] / 2) * IN, L["cg"] * IN, 0)))
    return g.union(pad).rotate((0, 0, 0), (0, 1, 0), -a)


def to_tube(flat, y_top):
    """sketch (X, Y) -> tube (x, z); thickness grows downward from y_top."""
    return flat.rotate((0, 0, 0), (1, 0, 0), 90).translate((0, y_top * IN, 0))


def cyl(x, z, y0, h, r):
    """Cylinder along +Y from y0 (the XZ workplane's normal is -Y, so extrude(-h) goes up)."""
    return cq.Workplane("XZ").center(x * IN, z * IN).circle(r * IN).extrude(-h * IN).translate((0, y0 * IN, 0))


def blk(cx, cy, cz, sx, sy, sz, a):
    return (cq.Workplane("XY").box(sx * IN, sy * IN, sz * IN)
            .rotate((0, 0, 0), (0, 1, 0), -a).translate((cx * IN, cy * IN, cz * IN)))


def build(c=C):
    """Parts in the tube frame with the mirror face at y = 0."""
    L = levels(c)
    R = c["mirror_dia"] / 2
    P = {}
    P["frame"] = to_tube(frame_flat(c), L["frame_top"])
    tris, pd, posts = None, None, None
    for tri in pads(c):
        t = to_tube(tri_flat(tri, c), L["tri_top"])
        tris = t if tris is None else tris.union(t)
        for x, z in tri:
            p = cyl(x, z, L["tri_top"], c["pad_t"] + c["cork"], c["pad_dia"] / 2)
            pd = p if pd is None else pd.union(p)
        px, pz = pivot_xy(tri)
        p = cyl(px, pz, L["frame_top"], L["post_top"] - L["frame_top"], 0.25)
        p = p.union(cq.Workplane("XY").sphere(c["ball"] / 2 * IN).translate((px * IN, (L["post_top"] + 0.06) * IN, pz * IN)))
        posts = p if posts is None else posts.union(p)
    P["triangles"], P["pads"], P["pivots"] = tris, pd, posts
    ep = None
    for a in c["load_posts"]:
        g = gusset_solid(c, L, a)
        ep = g if ep is None else ep.union(g)
    P["edge_posts"] = ep
    gp = None
    for a in c["guard_posts"]:
        rad, tan_ = c["post_guard"]
        r0 = R + c["guard_gap"]
        top = L["face"] + c["tab_gap"] + c["tab_t"]
        h = top - L["frame_top"]
        x, z = pol(r0 + rad / 2, a)
        b = blk(x, L["frame_top"] + h / 2, z, rad, h, tan_, a)
        r_in, r_out = R - c["tab_over"], r0 + rad
        x, z = pol((r_in + r_out) / 2, a)
        tab = blk(x, top - c["tab_t"] / 2, z, r_out - r_in, c["tab_t"], tan_, a)
        b = b.union(tab)
        gp = b if gp is None else gp.union(b)
    P["guard_posts"] = gp
    bolts = None
    for a in c["tri_angles"]:
        x, z = pol(c["r_bolt"], a)
        y0 = L["board_top"] - 0.709 - 0.25                # head under the mirror board
        b = cyl(x, z, y0, L["frame_top"] - 0.05 - y0, 0.156)
        bolts = b if bolts is None else bolts.union(b)
    P["collimation_bolts"] = bolts
    P["fan"] = cq.Workplane("XZ").rect(3.15 * IN, 3.15 * IN).extrude(1.0 * IN).translate((0, (L["frame_bot"]) * IN, 0))
    P["mirror"] = cyl(0, 0, L["back"], c["mirror_thick"], R)
    return P, L


def report(c=C):
    P, L = build(c)
    dens = dict(frame=0.0975, triangles=0.0975, pivots=0.0975, edge_posts=0.0975, guard_posts=0.0975,
                pads=0.051, collimation_bolts=0.283, fan=0.0)
    wt = {k: round(P[k].val().Volume() / IN ** 3 * d, 2) for k, d in dens.items()}
    R = c["mirror_dia"] / 2
    E = 10e6
    # gusset: a tapered cantilever (depth gusset_base at the root, gusset_top at the pad), load at the CG plane
    pts, hg = gusset_profile(c, L)
    h_load = L["cg"] - L["frame_top"]
    n = 200
    flex = 0.0
    for i in range(n):
        v = (i + 0.5) / n * h_load
        d = c["gusset_base"] + (c["gusset_top"] - c["gusset_base"]) * v / hg
        I = c["gusset_t"] * d ** 3 / 12
        flex += (h_load - v) ** 2 / (E * I) * h_load / n
    k_post = 1 / (flex + 1 / 150000)      # + the bolted root (two 1/4-20 at 1.7", ASSUMED 150,000 lb/in)
    k_lat = 2 * k_post * math.cos(math.radians(45)) ** 2
    return dict(levels={k: round(v, 3) for k, v in L.items()}, weights_lb=wt, cell_lb=round(sum(wt.values()) + 0.4, 2),
                pivot_r=round(math.hypot(*pivot_xy(pads(c)[0])), 3),
                pads_in=[[(round(x, 3), round(z, 3)) for x, z in t] for t in pads(c)],
                edge_post_k_lbin=round(k_post), edge_support_k_lbin=round(k_lat),
                mirror_shift_horizon_mm=round(23.1 / k_lat * 25.4, 4))


if __name__ == "__main__":
    import json
    print(json.dumps(report(), indent=1))
