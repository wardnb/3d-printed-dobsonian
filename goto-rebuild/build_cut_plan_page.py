"""Builds the cut-plan page (out/cut_plan/index.html) from out/cut_plan/plan.json. Run after cut_plan.py."""
import json
import os

from shapely.geometry import LinearRing

plan = json.load(open("out/cut_plan/plan.json"))


def slim(rings):
    out = []
    for r in rings:
        lr = LinearRing(r).simplify(0.008)
        out.append([[round(x, 2), round(y, 2)] for x, y in lr.coords])
    return out


for o in plan["options"]:
    for s in o["sheets"]:
        s["stock"] = slim(s["stock"])
        for p in s["parts"]:
            p["rings"] = slim(p["rings"])
for o in plan["half"]:
    for s in o["sheets"]:
        s["stock"] = slim(s["stock"])
        for p in s["parts"]:
            p["rings"] = slim(p["rings"])

BARS = [
    dict(id="sq34", stock="6061 square bar 3/4\" × 3/4\"", order="36\"", cuts="4 × 7.50\"", parts="Upper cage posts (spider studs through them)"),
    dict(id="fl34x114", stock="6061 flat bar 3/4\" × 1 1/4\"", order="12\"", cuts="3 × 1.20\" + 6 × 0.60\"", parts="Diagonal node blocks (3) and clevis blocks (6)"),
    dict(id="fl12x34", stock="6061 flat bar 1/2\" × 3/4\"", order="18\"", cuts="2 × 7.50\"", parts="Focuser board rails"),
    dict(id="sq12", stock="6061 square bar 1/2\" × 1/2\"", order="18\"", cuts="3 × 4.15\"", parts="Cell guard posts (safety tabs)"),
    dict(id="rd12", stock="6061 round bar 1/2\"", order="12\"", cuts="3 × 1.65\"", parts="Cell pivot posts"),
    dict(id="tube58", stock="6061 round tube 5/8\" OD × 0.058\" wall", order="6 ft", cuts="6 × 9.27\"", parts="Upper cage diagonals"),
    dict(id="rd3", stock="6061 round bar 3\"", order="6\"", cuts="1 × 5\"", parts="Secondary holder body (45° face milled)"),
    dict(id="fl2x4", stock="6061 flat bar 2\" × 4\"", order="12\"", cuts="3 × 3.70\"", parts="Truss socket blocks (provisional: detail drawings pending)"),
    dict(id="sq2", stock="6061 square bar 2\" × 2\"", order="12\"", cuts="3 × 3.70\"", parts="Truss pair blocks (provisional)"),
    dict(id="rd134", stock="6061 round bar 1 3/4\"", order="40\"", cuts="12 × 3.10\"", parts="Truss cone plugs (provisional; needs a lathe or a turning service)"),
]
OTHER = [
    dict(id="delrin1", stock="Delrin (acetal) rod 1\"", order="6\"", cuts="9 × 0.25\"", parts="Cell pads"),
    dict(id="delrin18", stock="Delrin sheet 1/8\"", order="small offcut", cuts="2 × 0.5\" × 1.4\"", parts="Edge gusset faces"),
    dict(id="cork", stock="Cork sheet 1/16\"", order="6\" × 6\"", cuts="9 × 1\" discs", parts="Pad faces"),
    dict(id="ss020", stock="301/302 stainless strip 0.020\" × 1.5\"", order="36\"", cuts="4 × 8.5\"", parts="Quad spider vanes"),
    dict(id="carbon", stock="Roll-wrapped carbon tube 1.25\" OD × 0.062\" wall", order="6 × 1 m (39.4\")", cuts="38.15\" and 38.20\" (3 each)", parts="Truss poles (carbon supplier, not Midwest)"),
]

def inch(o):
    if isinstance(o, str):
        return o.replace('"', "\u2033")
    if isinstance(o, list):
        return [inch(x) for x in o]
    if isinstance(o, dict):
        return {k: inch(v) for k, v in o.items()}
    return o


data = inch(dict(plan=plan, bars=BARS, other=OTHER))
tpl = open("site_cutplan/template.html").read()
html = tpl.replace("/*__DATA__*/null", json.dumps(data, separators=(",", ":")))
os.makedirs("out/cut_plan", exist_ok=True)
open("out/cut_plan/index.html", "w").write(html)
print("wrote out/cut_plan/index.html", len(html) // 1024, "kB")
