"""
Cut plan for the aluminium plate parts: nests every DXF part (real outlines, 1/4" end mill) on candidate stock
pieces so the stock can be priced. Writes out/cut_plan/plan.json (parts, stock options, placements as outlines).
Run from goto-rebuild/ after the export scripts:  python cut_plan.py
"""
import json
import math
import os

import cadquery as cq
from shapely.geometry import Polygon, Point, box
from shapely.ops import unary_union
from shapely import affinity

IN = 25.4
GAP = 0.30       # between parts: 1/4" end mill + a skin
EDGE = 0.30      # from the stock edge (tabs, clamping screws in the waste)
OUT = os.path.join("out", "cut_plan")
os.makedirs(OUT, exist_ok=True)


def dxf_poly(path):
    """Closed DXF profile -> shapely polygon (largest wire = outline, the rest = holes), in inches, at the origin."""
    w = cq.importers.importDXF(path)
    wires = []
    for wire in w.wires().vals():
        pts = []
        for e in wire.Edges():
            n = max(4, int(e.Length() / IN * 8))
            pts += [(p.x / IN, p.y / IN) for p in (e.positionAt(t / n) for t in range(n))]
        if len(pts) >= 3:
            wires.append(Polygon(pts).buffer(0))
    wires.sort(key=lambda p: -p.area)
    outer = wires[0]
    holes = [h for h in wires[1:] if outer.contains(h.representative_point())]
    poly = outer
    for h in holes:
        poly = poly.difference(h)
    minx, miny, *_ = poly.bounds
    return affinity.translate(poly, -minx, -miny)


# part, file, thickness, qty, material note, optional
PARTS = [
    ("Upper cage ring (lower)", "out/upper_cage/ring_lower_quarter-inch-6061.dxf", 0.25, 1, "cast plate ideal", False),
    ("Upper cage ring (upper)", "out/upper_cage/ring_upper_quarter-inch-6061.dxf", 0.25, 1, "cast plate ideal", False),
    ("Focuser board", "out/upper_cage/focuser_board_quarter-inch-6061.dxf", 0.25, 1, "cast plate ideal", False),
    ("Cell flotation triangle", "out/cell/cell_triangle_x3_quarter-inch-6061.dxf", 0.25, 3, "", False),
    ("Finder cradle bar", "out/upper_cage/finder_cradle_bar_quarter-inch-6061.dxf", 0.25, 1, "", False),
    ("Finder tilt plate", "out/upper_cage/finder_tilt_plate_quarter-inch-6061.dxf", 0.25, 1, "", False),
    ("Secondary carrier", "out/secondary_holder/carrier_quarter-inch-6061.dxf", 0.25, 1, "", False),
    ("Gluing jig bridge", "out/secondary_holder/jig_bridge_quarter-inch.dxf", 0.25, 1, "jig: any material", True),
    ("Cell frame", "out/cell/cell_frame_half-inch-6061-or-MIC6.dxf", 0.5, 1, "cast plate ideal; steel inserts for the 5/16-24 bolts", False),
    ("Cell edge gusset", "out/cell/cell_edge_gusset_x2_half-inch-6061.dxf", 0.5, 2, "", False),
    ("Finder angle block", "out/upper_cage/finder_cradle_angle-block_x2_half-inch-6061.dxf", 0.5, 2, "", False),
    ("Finder yaw yoke", "out/upper_cage/finder_yaw_yoke_half-inch-6061.dxf", 0.5, 1, "", False),
    ("Gluing jig base", "out/secondary_holder/jig_base_half-inch.dxf", 0.5, 1, "jig: any material", True),
]


def pieces(thick, include_optional=True, skip=()):
    out = []
    for name, f, t, q, note, opt in PARTS:
        if t != thick or name in skip or (opt and not include_optional):
            continue
        p = dxf_poly(f)
        for k in range(q):
            out.append(dict(name=name, poly=p, idx=k + 1, qty=q))
    return sorted(out, key=lambda d: -d["poly"].area)


def place(stock, items, step=0.15, angles=(0, 90, 180, 270), fixed=()):
    """Greedy lowest-then-leftmost placement inside a stock polygon. fixed = [(name, polygon)] already placed."""
    from shapely.prepared import prep
    usable = stock.buffer(-EDGE)
    U = prep(usable)
    placed = [dict(name=n, poly=p) for n, p in fixed]
    taken = unary_union([d["poly"].buffer(GAP) for d in placed]) if placed else Polygon()
    minx, miny, maxx, maxy = usable.bounds
    left = []
    for it in items:
        best = None
        for a in angles:
            pr = affinity.rotate(it["poly"], a, origin=(0, 0))
            bx0, by0, bx1, by1 = pr.bounds
            pr = affinity.translate(pr, -bx0, -by0)
            w, h = bx1 - bx0, by1 - by0
            T = prep(taken) if not taken.is_empty else None
            y, found = miny, None
            while y + h <= maxy + 1e-9 and found is None:
                if best and y > best[0]:
                    break
                x = minx
                while x + w <= maxx + 1e-9:
                    cand = affinity.translate(pr, x, y)
                    if U.contains(cand) and (T is None or not T.intersects(cand)):
                        found = (y, x, cand)
                        break
                    x += step
                y += step
            if found and (best is None or found[:2] < best[:2]):
                best = found
        if best is None:
            left.append(it)
            continue
        placed.append(dict(name=it["name"] + (f' {it["idx"]}/{it["qty"]}' if it["qty"] > 1 else ""), poly=best[2]))
        taken = unary_union([taken, best[2].buffer(GAP)])
    return placed, left


def geo(poly):
    """polygon -> list of rings (outer first) as [[x, y], ...] rounded, for SVG."""
    polys = list(poly.geoms) if poly.geom_type == "MultiPolygon" else [poly]
    out = []
    for p in polys:
        out.append([[round(x, 3), round(y, 3)] for x, y in p.exterior.coords])
        for h in p.interiors:
            out.append([[round(x, 3), round(y, 3)] for x, y in h.coords])
    return out


def sheet(label, stock, placed, thick, kind):
    return dict(label=label, thick=thick, kind=kind, w=round(stock.bounds[2], 2), h=round(stock.bounds[3], 2),
                stock=geo(stock), parts=[dict(name=d["name"], rings=geo(d["poly"])) for d in placed],
                used_area=round(sum(d["poly"].area for d in placed), 1), stock_area=round(stock.area, 1),
                lb=round(stock.area * thick * 0.0975, 2))


def run():
    plan = dict(gap_in=GAP, edge_in=EDGE, options=[])
    ring = dxf_poly(PARTS[0][1])
    ring2 = dxf_poly(PARTS[1][1])
    R = ring.bounds[2] / 2
    small_q = pieces(0.25, skip=("Upper cage ring (lower)", "Upper cage ring (upper)"))
    small_h = pieces(0.5)

    # ---- 1/4": A) two square blanks, small parts inside the rings' centres
    sheetsA = []
    rest = small_q
    for nm, rp, side in (("lower", ring, 21.5), ("upper", ring2, 21.5)):
        stock = box(0, 0, side, side)
        off = (side - 2 * R) / 2
        rpl = affinity.translate(rp, off, off)
        hole = Point(off + R, off + R).buffer(R - 1.5, 128)       # the ring's centre disc (ID 17.5)
        inner = Polygon(hole.exterior).buffer(0)
        pl, rest = place(inner, rest, fixed=())
        pl = [dict(name=f"Upper cage ring ({nm})", poly=rpl)] + pl
        sheetsA.append(sheet(f"1/4\" plate {side}\" × {side}\"", stock, pl, 0.25, "square"))
    plan["options"].append(dict(key="A", title="Square blanks: rings plus every small 1/4\" part in their centres",
                                sheets=sheetsA, leftover=[d["name"] for d in rest]))
    # ---- B) 21" circle cuts, same idea
    sheetsB = []
    rest = small_q
    for nm, rp in (("lower", ring), ("upper", ring2)):
        D = 21.0
        stock = Point(D / 2, D / 2).buffer(D / 2, 128)
        off = (D - 2 * R) / 2
        rpl = affinity.translate(rp, off, off)
        inner = Point(D / 2, D / 2).buffer(R - 1.5, 128)
        pl, rest = place(inner, rest)
        pl = [dict(name=f"Upper cage ring ({nm})", poly=rpl)] + pl
        s = sheet(f"1/4\" circle {D}\" dia", stock, pl, 0.25, "circle")
        s["edge_note"] = "0.25\" all round the ring: hold it with screws through the centre waste; check their circle tolerance is plus-only"
        sheetsB.append(s)
    plan["options"].append(dict(key="B", title="Circle cuts: same nest on 21\" discs", sheets=sheetsB,
                                leftover=[d["name"] for d in rest]))
    # ---- C) rings bought as rings + one small plate for everything else
    sheetsC = []
    for nm in ("lower", "upper"):
        stock = Point(10.5, 10.5).buffer(10.5, 128).difference(Point(10.5, 10.5).buffer(8.6, 128))
        sheetsC.append(dict(label="1/4\" ring 21\" OD × 17.2\" ID", thick=0.25, kind="ring", w=21, h=21,
                            stock=geo(stock), parts=[dict(name=f"Upper cage ring ({nm})",
                                                         rings=geo(affinity.translate(ring, 0.25, 0.25)))],
                            used_area=round(ring.area, 1), stock_area=round(stock.area, 1),
                            lb=round(stock.area * 0.25 * 0.0975, 2)))
    for wv, hv in ((12, 12), (12, 18), (12, 24), (18, 18), (24, 24)):
        pl, rest = place(box(0, 0, wv, hv), small_q)
        if not rest:
            sheetsC.append(sheet(f"1/4\" plate {wv}\" × {hv}\"", box(0, 0, wv, hv), pl, 0.25, "square"))
            break
    plan["options"].append(dict(key="C", title="Rings bought as rings (machine both edges) + one small 1/4\" plate",
                                sheets=sheetsC, leftover=[]))

    # ---- 1/2": the cell frame with the small 1/2" parts in its open spaces
    from shapely import minimum_bounding_circle
    frame = [d for d in small_h if d["name"] == "Cell frame"][0]
    others = [d for d in small_h if d["name"] != "Cell frame"]
    fx, fy = frame["poly"].bounds[2], frame["poly"].bounds[3]
    halfopts = []
    for wv, hv in ((17, 18), (18, 18), (18, 24)):
        stock = box(0, 0, wv, hv)
        if wv - 2 * EDGE < fx or hv - 2 * EDGE < fy:
            continue
        fpl = affinity.translate(frame["poly"], EDGE, EDGE)
        pl, rest = place(stock, others, fixed=[("Cell frame", fpl)])
        if not rest:
            halfopts.append(dict(key="R", title="Rectangle", sheets=[sheet(f"1/2\" plate {wv}\" × {hv}\"", stock, pl, 0.5, "square")]))
            break
    mc = minimum_bounding_circle(frame["poly"])
    for D in (20.5, 21, 22, 24):
        if mc.length / math.pi + 2 * EDGE > D:
            continue
        stock = Point(D / 2, D / 2).buffer(D / 2, 128)
        c = mc.centroid
        fpl = affinity.translate(frame["poly"], D / 2 - c.x, D / 2 - c.y)
        pl, rest = place(stock, others, fixed=[("Cell frame", fpl)])
        if not rest:
            halfopts.append(dict(key="D", title="Circle cut", sheets=[sheet(f"1/2\" circle {D}\" dia", stock, pl, 0.5, "circle")]))
            break
    plan["half"] = halfopts
    json.dump(plan, open(os.path.join(OUT, "plan.json"), "w"))
    for o in plan["options"]:
        print(o["key"], [(s["label"], len(s["parts"]), s["lb"]) for s in o["sheets"]], "left:", o["leftover"])
    print("1/2:", [(o["key"], s["label"], len(s["parts"]), s["lb"]) for o in plan["half"] for s in o["sheets"]])


if __name__ == "__main__":
    run()
