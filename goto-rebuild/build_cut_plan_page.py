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
        s["label"] = s["label"].replace('.0"', '"')
        s["stock"] = slim(s["stock"])
        for p in s["parts"]:
            p["rings"] = slim(p["rings"])
for o in plan["half"]:
    for s in o["sheets"]:
        s["stock"] = slim(s["stock"])
        for p in s["parts"]:
            p["rings"] = slim(p["rings"])

BARS = [
    # Midwest and OnlineMetals prices checked 2-3 Nov 2026 (plates and the 3" round / 1-3/4 square from Midwest, the rest from OnlineMetals) (their per-piece cut fee is ~$7.50, so fewer, longer pieces win; a 72" piece of
    # 3/4" square costs less than a 48" one). 6061-T6 throughout.
    dict(id="sq34", stock="6061 square bar 3/4\" × 3/4\"", order="48\"", cuts="4 × 7.50\" + 3 × 4.15\"", parts="Upper cage posts; cell guard posts milled down to 1/2\" square"),
    dict(id="fl34x114", stock="6061 flat bar 3/4\" × 1 1/4\"", order="36\"", cuts="3 × 1.20\" + 6 × 0.60\" + 2 × 7.50\" + 6\"", parts="Diagonal node (3) and clevis (6) blocks; focuser rails ripped to 1/2\" × 3/4\"; 6\" for the six wedge washers"),
    dict(id="rd12", stock="6061 round bar 1/2\"", order="12\"", cuts="3 × 1.65\"", parts="Cell pivot posts"),
    dict(id="tube58", stock="6061-T6 drawn round tube 5/8\" OD × 0.058\" wall", order="72\"", cuts="6 × 9.27\"", parts="Upper cage diagonals (OnlineMetals has 0.058\"; Midwest only 0.065\")"),
    dict(id="rd3", stock="6061 round bar 3\"", order="6\"", cuts="1 × 5\"", parts="Secondary holder body (45° face milled)"),
    dict(id="sq214", stock="6061 square bar 2 1/4\" × 2 1/4\"", order="12\"", cuts="3 × 3.70\"", parts="Truss socket blocks (faced to 3.6 × 2.0 × 2.1)"),
    dict(id="sq134", stock="6061 square bar 1 3/4\" × 1 3/4\"", order="20\"", cuts="3 × 3.70\" + 3 × 2.40\"", parts="Truss pair blocks (faced to 1.6 × 1.6) and socket spigots (milled upright, 0.75\" grip)"),
    dict(id="rd138", stock="6061 round bar 1 3/8\"", order="48\"", cuts="12 × 3.10\"", parts="Truss cone plugs (1.25\" max dia) if made in-house; skip if the turning service supplies material"),
]
OTHER = [
    dict(id="delrin1", stock="Delrin (acetal) rod 1\"", order="6\"", cuts="9 × 0.25\"", parts="Cell pads"),
    dict(id="delrin18", stock="Delrin sheet 1/8\"", order="small offcut", cuts="2 × 0.5\" × 1.4\"", parts="Edge gusset faces"),
    dict(id="cork", stock="Cork sheet 1/16\"", order="6\" × 6\"", cuts="9 × 1\" discs", parts="Pad faces"),
    dict(id="ss020", stock="301/302 stainless strip 0.020\" × 1.5\"", order="36\"", cuts="4 × 8.5\"", parts="Quad spider vanes"),
    dict(id="carbon", stock="Roll-wrapped carbon tube 1.25\" OD × 0.062\" wall", order="6 × 1 m (39.4\")", cuts="36.11\" ×2 and 36.16\" ×4", parts="Truss poles (carbon supplier, not Midwest)"),
]

# Everything else to buy (2026-10-31). when: "now" = drawn and fixed; "measure" = wait for a measurement or the part it
# fits; "test" = wait for the friction test; "later" = not designed yet. n = quantity the line total multiplies.
def B(id, item, n, spec, when, src=""):
    return dict(id="buy:" + id, item=item, n=n, spec=spec, when=when, src=src)


BUY = [
    dict(group="Truss and joints", items=[
        B("turn", "Turning job: cone plugs (only if not made in-house)", 1, "12 plugs from the pole_plug STEP, 6061; skip if the rotary-axis trial plug seats well. Plug shank is sized to a 1.126\" bore: send the measured carbon bore with the order. Spigots are milled on the AltMill", "measure", "local shop / Xometry"),
        B("collar45", "45 mm two-piece shaft collar", 6, "Aluminium or steel clamp collar, 45 mm bore, ~2.75\" OD; one each side of the box's top ring on every stub", "now", "Ruland / McMaster"),
        B("pin14x234", "Steel dowel pin 1/4\" × 2-3/4\"", 3, "Board pins, radial through the mirror board's edge and both stub walls", "now", "McMaster"),
        B("pin14x34", "Steel dowel pin 1/4\" × 3/4\"", 3, "Pair block locating dowels (reamed 0.250\")", "now", "McMaster"),
        B("stud14", "1/4-20 stainless stud, 1-1/2\" fully threaded", 8, "Drawbolts along the pole axis (6 + 2 spare); Loctite 0.6\" into the plug nose", "now", "McMaster"),
        B("wheel14", "1/4-20 knurled thumb nut, ~0.9\" dia", 8, "Drawbolt thumbwheels (6 + 2 spare); ≤ 0.30\" thick to fit the 0.75\" pocket with its wedge washer", "now", "McMaster"),
        B("knob14", "1/4-20 male-thread knob, 2-1/2\" stud", 3, "Pair block to cage ring, from below (check the stud length on the parts)", "now", "McMaster"),
        B("shcs1474", "1/4-20 × 1-3/4\" SHCS", 3, "Spigot to socket block, from below", "now", "McMaster"),
        B("rollpin", "1/8\" roll pin × 1\"", 8, "Keeps each thumbwheel captive across its pocket mouth", "now", "McMaster"),
        B("epoxy", "Structural epoxy + gun + nozzles", 1, "3M DP420 or DP460 (50 ml cartridges, 2–3): plugs in poles, poles in pair blocks, spigots in blocks and stubs", "now", ""),
    ]),
    dict(group="Upper cage, spider, finder", items=[
        B("cage14", "1/4-20 stainless FHCS / SHCS assortment", 1, "~24 screws: 8 ring-to-post, 6 diagonal node, 4 focuser rails, 3 focuser push-pull pairs; buy 5/8\" and 3/4\" lengths", "now", "McMaster / Bolt Depot"),
        B("cage10", "#10-32 stainless assortment", 1, "~30: 4 vane tension studs (+ nuts, washers), 12 diagonal clevis pins/bolts with nyloc nuts, 6 clevis-to-post, 4 finder ring FHCS + cradle screws", "now", ""),
        B("setscr", "#10-32 ball-point set screws", 6, "Finder tilt plate (3) and yaw yoke (2) + spare", "now", "McMaster"),
        B("shoe", "Synta-style metal finder shoe", 1, "For the Waypoint (WO slide base); drill the tilt plate to the shoe you get", "now", ""),
        B("shroud", "Light shroud (black Lycra/Spandex)", 1, "Around the truss; not drawn yet, size once the truss is up", "later", ""),
    ]),
    dict(group="Optics", items=[
        B("sec", "3.5\" minor axis secondary", 1, "1/10 wave or better, enhanced coating; its thickness sets the holder (0.70\" ASSUMED)", "now", "Antares / Protostar / Hubble"),
        B("escc", "Explore Scientific HR coma corrector 2\" (HRCC02-01)", 1, "Always in the train", "now", ""),
        B("ext1", "2\" extension tube, 1\"", 1, "Only for the Paracorr or no-corrector use", "later", ""),
        B("heater", "Kapton heater ~2\" + 10k NTC", 1, "Secondary dew heater on the Pegasus RCA output", "now", ""),
        B("rtv", "Neutral-cure RTV silicone", 1, "Secondary bonding pads (not acetic: it attacks the coating)", "now", ""),
    ]),
    dict(group="Mirror cell", items=[
        B("ball38", "3/8\" chrome-steel ball", 6, "Triangle pivots (3 + spare)", "now", "McMaster"),
        B("bolt516", "5/16-24 bolt + large collimation knob", 3, "Collimation; big knobs (1/16 turn ≈ 0.4 mm at focus)", "now", ""),
        B("bush516", "Flanged SAE 841 bronze bushing, 5/16\" ID", 3, "In the mirror board around the collimation bolts", "measure", "McMaster"),
        B("ins516", "5/16-24 steel thread insert", 3, "In the cell frame if it is cast plate", "now", ""),
        B("push14", "1/4-20 push screws + threaded inserts for ply", 3, "Lock the cell against the bolts", "now", ""),
        B("fan80", "80 mm 12 V fan + finger guard", 1, "Under the hub, #6 screws", "measure", ""),
        B("wiresaw", "Debonding line (braided fishing line or 0.010\" piano wire)", 1, "Saw through the 9 old glue dabs", "now", ""),
    ]),
    dict(group="Birch, bearings, rocker, ground board", items=[
        B("birch", "Baltic birch 18 mm, 5 × 5 ft", 3, "D bearings, rocker, ground board, box wings (ripped to 24.4\" strips)", "now", ""),
        B("ebony", "Ebony Star laminate", 1, "D bearing rims and the rocker floor's underside (az): a 4 × 8 sheet covers both", "now", ""),
        B("ptfe", "Virgin PTFE sheet 3/16\"", 1, "Alt pads (4), lateral stops (2), az pads (3); 6 × 6\" is plenty", "now", ""),
        B("dowel38", "Steel dowel pin 3/8\" + drill bushing 3/8\" ID × 1/2\" OD", 4, "D bearing to box (2 per side)", "now", "McMaster"),
        B("bolt14", "1/4-20 bolts + threaded inserts for ply", 12, "D bearing to box side (6 per side)", "now", ""),
        B("confirmat", "Confirmat screws + step drill", 1, "Box back wings through both boards (8)", "now", ""),
        B("pivot", "3/8\" pivot bolt, nyloc, fender + PTFE washers", 1, "Rocker on ground board", "now", ""),
        B("feet", "Levelling feet", 3, "Ground board feet at r 14\"", "now", ""),
        B("glue", "Wood glue (Titebond III) + contact cement", 1, "Laminating the D layers; Ebony Star", "now", ""),
    ]),
    dict(group="Drives (two identical modules)", items=[
        B("belt9", "GT2 9 mm open belt, 5 m", 1, "Glued teeth-out on the alt rim (~23\") and around the 30\" ground ring (~95\")", "now", ""),
        B("pin20", "GT2 20T flangeless pinion, 8 mm bore, ≥ 9 mm wide", 3, "2 + spare", "now", ""),
        B("p16", "GT2 16T, 6 mm belt, bore to suit the motor shaft", 2, "On the gearmotor (1/4\" ASSUMED: measure the Pittman shaft)", "measure", ""),
        B("p32", "GT2 32T + 152 mm loop (2:1)", 2, "Buy both ratio sets; they are cheap", "test", ""),
        B("p48", "GT2 48T + 170 mm loop (3:1)", 2, "", "test", ""),
        B("shaft8", "8 mm ground shaft, 100 mm + shaft collars", 2, "Jackshafts", "now", ""),
        B("f608", "F608ZZ flanged bearing", 4, "", "now", ""),
        B("shoulder", "3/8\" shoulder bolt + flanged bronze bushing 3/8 × 1/2", 2, "Arm pivots", "now", ""),
        B("stand10", "#10-32 standoff 0.80\"", 6, "Between arm plates A and B", "now", ""),
        B("springs", "Clutch springs (alt compression ~19 lb, az extension)", 1, "Rate them once the brackets are detailed", "later", ""),
        B("cam", "Over-centre cam levers", 2, "Clutch", "later", ""),
    ]),
    dict(group="Encoders and electronics", items=[
        B("enc", "Magnetic tape + read heads (2 axes)", 1, "Waiting on the SiTech input decision (or keep the Astro Devices on the Nexus)", "later", ""),
        B("power", "LiFePO4 battery + 12 V regulator, 24 V boost for the motors", 1, "Pegasus cuts out above ~14 V", "later", ""),
        B("pc", "Mini PC, USB3 + 12 V trunk, enclosure, connectors", 1, "Electronics box not laid out yet", "later", ""),
    ]),
    dict(group="Shop consumables (truss blocks and fixtures)", items=[
        B("tools", "Carbide end mills", 1, "1/8\" ball, ≥ 1.5\" reach; 1/8\" flat, ≥ 1.5\" reach; 1/4\" 3FL, ≥ 1.25\" LOC; 1/2\" 3FL, ≥ 1.5\" LOC (aluminium geometry)", "now", ""),
        B("taps", "1/4-20 tap, #7 drill, 0.250\" reamer", 1, "Socket undersides, pair blocks", "now", ""),
        B("bush29", "Drill bushing 0.29\" OD × 0.201\" ID", 1, "Plug-nose drill guide: pressed into a socket cup's stud hole so the tap drill follows the cone axis", "now", "McMaster"),
        B("hsi", "1/4-20 heat-set inserts + strap clamps", 1, "16 inserts for the 8 printed fixtures; low-profile straps (≤ 0.35\" above the block)", "now", ""),
        B("fil", "PETG or ASA filament", 1, "8 wedge fixtures", "now", ""),
        B("loctite", "Loctite 243 / 263", 1, "Drawbolts, spigot bolts", "now", ""),
    ]),
]


def inch(o):
    if isinstance(o, str):
        return o.replace('"', "\u2033")
    if isinstance(o, list):
        return [inch(x) for x in o]
    if isinstance(o, dict):
        return {inch(k): inch(v) for k, v in o.items()}
    return o


# prices Nick saw at Midwest Steel Supply (cast tool & jig plate), 2026-10-31; keys = page line ids
SEEN = {
    "sq34": ["33.26", "1", "$33.26 (48\"; Midwest $63.50 for 72\")", "2 Nov", "OnlineMetals"],
    "fl34x114": ["47.15", "1", "$47.15 (36\"; Midwest $75.31 for 30\")", "2 Nov", "OnlineMetals"],
    "rd12": ["4.50", "1", "$4.50 (12\"; Midwest $29.00)", "2 Nov", "OnlineMetals"],
    "tube58": ["20.50", "1", "$20.50 (72\", 0.058 wall; Midwest $37.84 for 0.065)", "2 Nov", "OnlineMetals"],
    "rd3": ["88.42", "1", "$88.42 (6\"; OnlineMetals $127.59 for 12\")", "2 Nov", "Midwest"],
    "sq214": ["80.75", "1", "$80.75 (12\"; Midwest $87.63)", "2 Nov", "OnlineMetals"],
    "sq134": ["88.03", "1", "$88.03 (20\"; OnlineMetals $109.45 for 24\")", "2 Nov", "Midwest"],
    "rd138": ["91.84", "1", "$91.84 (48\"; Midwest $117.08 for 40\")", "2 Nov", "OnlineMetals"],
    'A:1/4" plate 21.5" × 21.5"': ["170.74", "2", "$170.74 each at 2, $168.24 at 3"],
    'B:1/4" circle 21" dia': ["144.54", "2", "$144.54 each at 2 (21.25\" quoted), $142.04 at 3"],
    'HR:1/2" plate 17" × 18"': ["148.41", "1", "$148.41 for 1, $140.91 each at 2"],
}
data = inch(dict(plan=plan, bars=BARS, other=OTHER, buy=BUY, seen=SEEN))
tpl = open("site_cutplan/template.html").read()
html = tpl.replace("/*__DATA__*/null", json.dumps(data, separators=(",", ":")))
os.makedirs("out/cut_plan", exist_ok=True)
open("out/cut_plan/index.html", "w").write(html)
print("wrote out/cut_plan/index.html", len(html) // 1024, "kB")
