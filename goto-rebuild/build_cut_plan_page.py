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
    dict(id="fl34x114", stock="6061 flat bar 3/4\" × 1 1/4\"", order="36\"", cuts="3 × 1.20\" + 6 × 0.60\" + 2 × 7.50\" + 6\"", parts="Diagonal node (3) and clevis (6) blocks; focuser rails ripped to 1/2\" × 3/4\" (the 6\" once meant for wedge washers is spare)"),
    dict(id="rd12", stock="6061 round bar 1/2\"", order="12\"", cuts="3 × 1.65\"", parts="Cell pivot posts"),
    dict(id="tube58", stock="6061-T6 drawn round tube 5/8\" OD × 0.058\" wall", order="72\"", cuts="6 × 9.27\"", parts="Upper cage diagonals (OnlineMetals has 0.058\"; Midwest only 0.065\")"),
    dict(id="rd3", stock="6061 round bar 3\"", order="6\"", cuts="1 × 5\"", parts="Secondary holder body (45° face milled)"),
    dict(id="sq214", stock="6061 square bar 2 1/4\" × 2 1/4\"", order="12\"", cuts="3 × 3.70\"", parts="Truss socket blocks (faced to 3.6 × 2.0 × 2.1)"),
    dict(id="sq134", stock="6061 square bar 1 3/4\" × 1 3/4\"", order="20\"", cuts="3 × 3.70\" + 3 × 2.40\"", parts="Truss pair blocks (faced to 1.6 × 1.6) and socket spigots (milled upright, 0.75\" grip)"),
    dict(id="rd138", stock="6061 round bar 1 3/8\"", order="48\"", cuts="12 × 3.10\"", parts="Truss cone plugs (1.25\" max dia) if made in-house; skip if the turning service supplies material"),
    # roller bearings (2026-11-07, roller_study.py): not yet ordered
    dict(id="bar1520", stock="6061 rectangular bar 1 1/2\" × 2\"", order="18\"", cuts="4 × 2.20\" + 4 × 1.50\"", parts="Alt roller blocks (2.2 tall, saddle over the wall) and four az roller blocks (1.5, roller down, hung through the floor at its corners); faced to 1.4 wide"),
    dict(id="fl116x58", stock="6061-T6 flat bar 1/16\" × 5/8\"", order="2 × 48\"", cuts="2 × ~40\" (trim on the rim)", parts="Alt roller tracks, bent around the D rims and epoxy-bonded (elastic at R 14: strap-clamp while curing)"),
    dict(id="pl18", stock="6061 plate 1/8\" × 12\" × 48\"", order="1", cuts="4 × 90° ring segments (r 12.25–13.25, 18.7 × 4.6 each) + 4 flange plates 2.4 × 3.0", parts="Az roller track ring on the ground ring (joints at 45°+k·90°, off the birch joints); az block flange plates (DXFs in out/rocker/)"),
]
OTHER = [
    dict(id="delrin1", stock="Delrin (acetal) rod 1\"", order="6\"", cuts="9 × 0.25\"", parts="Cell pads"),
    dict(id="delrin18", stock="Delrin sheet 1/8\"", order="small offcut", cuts="2 × 0.5\" × 1.4\"", parts="Edge gusset faces"),
    dict(id="cork", stock="Cork sheet 1/16\"", order="6\" × 6\"", cuts="9 × 1\" discs", parts="Pad faces"),
    dict(id="ss020", stock="301/302 stainless strip 0.020\" × 1.5\"", order="36\"", cuts="4 × 8.5\"", parts="Quad spider vanes"),
    dict(id="carbon", stock="Roll-wrapped carbon tube, Rock West 45562: 1.125\" ID × 1.240\" OD × 72\", unidirectional", order="3 × 72\" (ORDERED 3 Nov, ~$564 delivered)", cuts="35.87\" ×2 and 35.92\" ×4, two per tube (pair-block bond trimmed to 1.08\" so a pair fits in 72\")", parts="Truss poles. Also priced: Clearwater 1.125-1.253-TW-72 $164 ea (twill skin, $535 shipped), DragonPlate FDPT1.125*1.25*72 $169.43 ea."),
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
        B("shcs14", "1/4-20 × 1\" SHCS, alloy steel", 8, "Head screws in the plug noses (6 + 2 spare), head down; the gib wedges under the washer on the head", "now", "McMaster"),
        B("sphw14", "1/4\" spherical washer set (ball + seat), steel", 6, "On each head screw: the screw leans 13° and the gib is horizontal", "now", "McMaster"),
        B("gibrod", "5/8\" O1 drill rod, 12\"", 1, "Six 1.20\" gibs: 0.34 slot 0.6 deep from the tip, underside milled to an 8° wedge, 0.26 hole + 1/16 roll pin at the rear for the captive stud tip", "now", "McMaster"),
        B("gibknob", "1/4-20 × 1-3/4\" stud knob, Ø1.25", 6, "Gib clamp knobs on the socket blocks' outside faces (~7 turns engaged ↔ released); cut a 0.09 groove near the tip for the roll pin", "now", "McMaster"),
        B("gibplate", "1/8\" steel strip 1-1/4 × 12\" + 1/4-20 PEM nuts (6) + #8-32 × 1/2 screws (12)", 1, "Six gib retainer plates 1.6 × 1.2 (gib_retainer_plate DXF) on the socket blocks' outside faces", "now", "McMaster"),
        B("rollpin", "1/16\" roll pin × 5/8\"", 8, "Captive stud tip in each gib (6 + 2 spare)", "now", "McMaster"),
        B("epoxy", "Structural epoxy + gun + nozzles", 1, "3M DP420 or DP460 (50 ml cartridges, 3): plugs in poles, poles in pair blocks, spigots in blocks and stubs, and the 1/16\" roller track strips on the D rims", "now", ""),
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
        B("birch", "Baltic birch 18 mm, 5 × 5 ft — BOUGHT 2026-11-07, ~$460 for three sheets ripped to 24-3/8\" strips", 3, "D bearings, rocker, ground board, box wings. Measure the real thickness with calipers before cutting (model uses 0.71\"; 18 mm birch runs 17.5–18.2) and put it in P[\"ply\"]", "now", "bought"),
        B("r10", "R10-2RS or R10-ZZ ball bearing (5/8 × 1-3/8 × 11/32)", 9, "Roller wheels: 4 alt + 4 az + spare (roller_study.py: 21–34 lb each, Hertz ≤ 130 MPa at 3 g on 6061). ZZ shields drag ~1/5 of 2RS seals", "now", "McMaster / VXB"),
        B("sb58", "5/8\" × 1\" shoulder bolt, 1/2-13 thread, 18-8", 8, "Roller axles; the far cheek of each block is tapped 1/2-13", "now", "McMaster"),
        B("fr6", "FR6-2RS flanged bearing (3/8 × 7/8 × 9/32) + 3/8 × 1-1/2 shoulder bolt", 1, "Zero-play az pivot in a 6061 housing on the floor; 5/16-18 steel insert in the ground hub", "now", "McMaster"),
        B("thandle", "3/8-16 T handles (or lifting eye bolts), 5.5\" rod", 2, "Screw into the cell frame's lugs at 60/240° to lift the mirror + cell out through the top ring; removed for observing (`cell_case.py`)", "later", "McMaster"),
        B("case", "Mirror-cell case: 1/2\" birch 19 × 19 × 8\" (or 18 mm offcuts), 3/4\" closed-cell foam ring, weatherstrip, 2 side handles, 2 draw latches", 1, "Mirror + cell lives in it between sessions; three blocks with two 5/16 pins locate the frame (DXFs out/cell/case_*). ~16 lb case, ~45 lb carried", "later", ""),
        B("xbolt", "1/4-20 × 2\" bolts + nyloc nuts", 8, "Alt roller block cross bolts, through both cheeks and the wall", "now", ""),
        B("trackscr", "#8 × 3/4\" stainless FHCS (az track segments, countersunk flush) + #10 × 1\" wood screws (flange plates)", 1, "~20 of the #8, 16 of the #10 (flange plates: #10-32 × 3/4 machine screws into the block cheeks, 16)", "now", ""),
        B("ptfe", "Virgin PTFE sheet 1/16\"", 1, "Lateral tab faces (4) on the alt roller blocks, 0.05\" off the D; 3 × 3\"", "now", ""),
        B("brake", "Brake shoes: 1\" neoprene/cork pads + compression springs", 2, "Hand-push brake on each axis, pressed on by the same cam lever that lifts the pinion (~15–20 lb on the track = 100–120 in-lb hold); not drawn yet", "later", ""),
        B("dowel38", "Steel dowel pin 3/8\" + drill bushing 3/8\" ID × 1/2\" OD", 4, "D bearing to box (2 per side)", "now", "McMaster"),
        B("bolt14", "1/4-20 bolts + threaded inserts for ply", 12, "D bearing to box side (6 per side)", "now", ""),
        B("confirmat", "Confirmat screws + step drill", 1, "Box back wings through both boards (8)", "now", ""),
        B("feet", "Levelling feet", 3, "Ground board feet at r 14\"", "now", ""),
        B("glue", "Wood glue (Titebond III)", 1, "Laminating the D layers (no laminate: the rollers run on aluminium tracks)", "now", ""),
    ]),
    dict(group="Drives (two identical modules)", items=[
        B("belt9", "GT2 9 mm open belt, 5 m", 1, "Glued teeth-out on the alt rim (~23\") and around the 30\" ground ring (~95\")", "now", ""),
        B("pin20", "GT2 20T flangeless pinion, 8 mm bore, ≥ 9 mm wide", 3, "2 + spare. Hub ≤ 12.5 mm dia (hubless long-toothed type, or turn/file a 16 mm hub down): on the alt rim it runs 0.04\" under the roller track strip", "now", ""),
        B("p16", "GT2 16T, 6 mm belt, 1/4\" (6.35 mm) bore, set screw", 2, "On the gearmotor: shaft measured Ø0.245 = 1/4\" with a flat (not 6 mm)", "now", ""),
        B("p32", "GT2 32T + 152 mm loop (2:1)", 2, "Buy both ratio sets; they are cheap", "test", ""),
        B("p48", "GT2 48T + 170 mm loop (3:1)", 2, "", "test", ""),
        B("shaft8", "8 mm ground shaft, 100 mm + shaft collars", 2, "Jackshafts", "now", ""),
        B("f608", "F608ZZ flanged bearing", 4, "", "now", ""),
        B("m6fh", "#6-32 × 3/4 socket-head screws + nyloc nuts", 8, "Motor flange to plate B through the four free Ø0.15 holes on the 1.63\" square (the countersunk set is the gearbox's own screws)", "now", ""),
        B("shoulder", "3/8\" shoulder bolt + flanged bronze bushing 3/8 × 1/2", 2, "Arm pivots", "now", ""),
        B("stand10", "#10-32 standoff 0.80\"", 6, "Between arm plates A and B", "now", ""),
        B("springs", "Clutch springs (alt compression ~19 lb, az extension)", 1, "Rate them once the brackets are detailed", "later", ""),
        B("cam", "Over-centre cam levers", 2, "Clutch", "later", ""),
    ]),
    dict(group="Encoders and electronics", items=[
        B("enc", "Az encoder: the owned Astro Devices HD ring assembly on the pivot bolt (311,296 steps), reader plate under the floor; NO alt encoder (plate solving, 2026-11-08)", 0, "Nothing to buy beyond one anchor screw; floor relief pocket set by the disc thickness. Home microswitch at the zenith park on the Servo II HOME input, ~$5", "later", ""),
        B("power", "12.8 V LiFePO4 20–30 Ah + 12→24 V boost ≥ 6 A for the SiTech only", 1, "One 12 V bus (Pegasus cuts out above ~14 V); the boost feeds the SiTech/motors. Battery + boost on the rocker floor (docs/drive_bringup.md)", "now", ""),
        B("bench", "Bench: 2 × SiTech motor cables (modular + barrel; the motors have SiTech adapter boards), 12 V ≥ 5 A supply, USB-B cable, 3/8 bolt + nylon washers (test-rim pivot)", 1, "Stage 0–2 of docs/drive_bringup.md; the old DobStuff D bearing is the test rim", "now", ""),
        B("pc", "Mini PC, USB3 + 12 V trunk, enclosure, connectors", 1, "Electronics box not laid out yet", "later", ""),
    ]),
    dict(group="Cutting tools, workholding and shop consumables (2026-11-09: everything needed to cut the whole build)", items=[
        # --- aluminium end mills (ER20 collets 1/8, 1/4, 3/8, 1/2: check the AltMill's set) ---
        B("em14al", "1/4\" single-flute (O-flute) upcut carbide for aluminium, 1\" CL, ×3", 3, "The workhorse on a router: cage rings, cell frame/triangles, arm and base plates, roller blocks, spider blocks, focuser board, az track. One flute keeps the chip load right at 8–24k rpm (0.002\"/tooth = 36 ipm at 18k) and clears the slot; a 3-flute would need 50–145 ipm and welds when the feed drops", "now", "Amana 51411 / SpeTool / Datron-style"),
        B("em14long", "1/4\" 2-flute carbide for aluminium, ≥ 1.25\" LOC (≥ 1.5\" reach)", 2, "Socket cup roughing (1.4\" deep), gib bores 1.25 deep, roller-block axle slot 1.19 deep, F608 bores", "now", ""),
        B("em12al", "1/2\" 2-flute carbide for aluminium, ≥ 1.5\" LOC (3FL only if no 2FL in that reach)", 1, "Pair-block blind bores Ø1.244 by helix (joint_machining) at the spindle's lowest rpm; also facing block stock", "now", ""),
        B("em18ball", "1/8\" 2FL ball carbide, ≥ 1.5\" reach (reduced neck)", 2, "Socket cup 60° cone finish spiral to the apex 1.4\" down; one spare: they snap", "now", ""),
        B("em18flat", "1/8\" 2FL flat carbide, ≥ 1.5\" reach, ×3", 3, "#8-32 tap drills in the blocks, #10 holes and slots in plates, small pockets; spares", "now", ""),
        B("em38al", "3/8\" 2FL carbide for aluminium, 1\" LOC (optional)", 1, "Faster roughing of the 1/2\" cell frame and 1-1/2 × 2 roller-block bar", "later", ""),
        B("chamfer", "90° carbide V-bit / chamfer mill, 1/2\" dia, 1/4\" shank", 1, "The 0.06\" cosmetic chamfers on every block and plate edge (last pass) and spot drilling", "now", ""),
        B("csk82", "82° countersink, 3/8\" body, 1/4\" shank (3- or 6-flute)", 1, "#8 and #10 flat-head screws: ring-to-post FHCS, az track #8 FHCS, finder cradle. 90° V-bits are the wrong angle for FHCS", "now", ""),
        B("emsteel", "1/4\" 4FL carbide (AlTiN) for steel", 1, "Gib pins: 0.34 slot and the 8° wedge face in O1 rod (annealed), light cuts at the spindle's lowest rpm; the 1/8\" steel retainer plates can be sawn/drilled by hand instead", "now", ""),
        # --- birch ---
        B("comp14", "1/4\" compression bit, 1\" CL, 1/4\" shank, ×2", 2, "Profiling the 18 mm birch (walls, floor, D bearings, ring thirds, wings): clean top and bottom edges in 2 passes", "now", "Amana 46170 / SpeTool"),
        B("down14", "1/4\" downcut spiral, ×2", 2, "Pockets, notches and the D lightening windows (keeps the face clean); one spare", "now", ""),
        B("down18", "1/8\" downcut spiral", 1, "Small holes/pilots in birch, the encoder plate relief pocket", "now", ""),
        B("fors", "Forstner bits 1/2\" and 1-3/4\"", 1, "Drill-bushing seats (1/2\" OD) in the box strips; 45 mm stub holes if any ply is re-drilled (1-3/4 = 44.5 mm, then ream/sand)", "now", ""),
        # --- drills, taps, reamers (hand/drill press unless noted) ---
        B("tapset", "Taps: #8-32, #10-32, 1/4-20, 5/16-18, 3/8-16, 1/2-13 (plug/bottoming) + tap wrench", 1, "#8 retainer plates, #10 spider studs/standoffs, 1/4-20 everywhere (plug noses, spigots, pair knobs, cross bolts), 5/16-18 pivot insert, 3/8-16 lifting lugs, 1/2-13 roller-block cheeks", "now", ""),
        B("drills", "Tap/clearance drills: #29, #21, #7, F, 5/16, 27/64, 17/64, 0.201 stub (for the 0.29 bushing), 1/4, 3/8, 13/32", 1, "Number/letter set covers it; cobalt or carbide-tipped for the 1/8\" steel strip", "now", ""),
        B("reamers", "Chucking reamers: 0.2495\" (press) and 0.2510\" (slip) for 1/4\" dowels; 0.3745\" for the 3/8\" D dowels; 5/8\" (0.6250) for the roller axles", 1, "Pair-block dowels press in the block (0.2495) and slip in the cage ring (0.2510); 5/8 shoulder bolts want ≤ 0.001 clearance in the block cheeks, or helix-bore to 0.627 and skip the reamer", "now", "McMaster"),
        B("inserts14", "Threaded inserts: 1/4-20 brass EZ-Lok for wood (×30), 5/16-24 steel Keensert/Heli-Coil kit (×3), 5/16-18 steel insert (×1), 1/2-13 Heli-Coil (optional, roller block cheeks if 6061 threads gall)", 1, "D-to-box bolts (12), cell push screws (3), fixture/misc; cell collimation bolts in cast plate", "now", "McMaster"),
        # --- workholding ---
        B("vise", "Low-profile 3\" or 4\" CNC vise (fixed jaw ≤ 2.5\" tall) + parallels + soft jaws stock", 1, "Socket Op2 (gib bores, block on its inside face) and Op5 (underside), pair-block top holes, roller blocks, spigots upright, gib pins. Bolts to the spoilboard inserts", "now", "Sienci / Amazon 4\" low-profile"),
        B("clamps", "Spoilboard T-track hold-down kit + 1/4-20 hold-down bolts, strap clamps (×6, ≤ 0.35\" tall over the block) + 1/4-20 × 1-1/2 SHCS, cam clamps (×4)", 1, "Fixtures (two straps each), plate blanks, birch blanks; the 8 printed fixtures already have the 2 heat-set inserts each", "now", ""),
        B("tapeca", "Blue painter's tape (2\") + thin CA glue + activator; double-sided CNC tape", 1, "Holding the 21\" ring discs, arm plates and the 1/8\" track ring flat on the spoilboard with no clamps in the tool path", "now", ""),
        B("spoil", "3/4\" MDF spoilboard sheet + 1/4-20 threaded inserts (×30)", 1, "A fresh surfaced spoilboard before the rings: flatness sets the 1/4\" ring's thickness uniformity", "now", ""),
        # --- rotary ---
        B("vortex", "Vortex rotary: 4-jaw chuck + tailstock live centre (if not already in the kit), 1-3/8 round stock stubs", 1, "Cone plugs (12) and spigots (3) as continuous spirals; a 60° centre drill for the tailstock end", "now", "Sienci"),
        # --- measuring and finishing ---
        B("meas", "Dial test indicator 0.0005\" + magnetic base; 1-2-3 blocks (pair); gauge pins 0.250 / 0.625 / 1.100 (or a pin set 0.251–0.500); thread pitch gauge", 1, "Tram the fixtures and vise, check cup apex depth and bore sizes, verify the plug shank against the measured 1.10 bore before bonding", "now", ""),
        B("finish", "Deburring tool + blades, needle files, Scotch-Brite, 1/4-20 and 10-32 thread chasers", 1, "Every edge before bead blasting; chasing threads after anodize", "now", ""),
        B("cool", "Aluminium cutting fluid (A9 / WD-40 Specialist) in a spray bottle; air blast nozzle; chip brush; shop vac with a cyclone", 1, "Mist or air blast on every aluminium cut (dry 6061 at router rpm welds to the tool whatever the flute count); set feeds from chip load (≥ 0.001\"/tooth, aim 0.002) not by feel; vacuum off the birch", "now", ""),
        B("bush29", "Drill bushing 0.29\" OD × 0.201\" ID", 1, "Plug-nose drill guide: pressed into a socket cup's stud hole so the tap drill follows the cone axis", "now", "McMaster"),
        B("hsi", "1/4-20 heat-set inserts (16) + 1/4-20 × 1-1/2 SHCS (16)", 1, "The 8 printed fixtures (2 each)", "now", ""),
        B("fil", "ASA filament, 2 kg", 1, "8 wedge fixtures (~1.7 kg total; two printed by 2026-11-09)", "now", ""),
        B("loctite", "Loctite 243 (blue) + 263 (red)", 1, "Spigot bolts, head screws in the plug noses, set screws", "now", ""),
        B("ppe", "Safety glasses, hearing protection, nitrile gloves for epoxy, respirator cartridges for the shroud/anodize prep", 1, "", "now", ""),
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
    "carbon": ["170.99", "3", "$170.99 (72\"; + $51.30 ground; Clearwater $164, DragonPlate $169.43)", "3 Nov", "Rock West"],
    "sq34": ["33.26", "1", "$33.26 (48\"; Midwest $63.50 for 72\", Metals Depot ~$40)", "3 Nov", "OnlineMetals"],
    "fl34x114": ["47.15", "1", "$47.15 (36\"; Midwest $75.31 for 30\")", "2 Nov", "OnlineMetals"],
    "rd12": ["4.50", "1", "$4.50 (12\"; Midwest $29.00)", "2 Nov", "OnlineMetals"],
    "tube58": ["20.50", "1", "$20.50 (72\", 0.058 wall; Midwest $37.84 for 0.065)", "2 Nov", "OnlineMetals"],
    "rd3": ["88.42", "1", "$88.42 (6\"; OnlineMetals $127.59 for 12\")", "2 Nov", "Midwest"],
    "sq214": ["80.75", "1", "$80.75 (12\"; Midwest $87.63)", "2 Nov", "OnlineMetals"],
    "sq134": ["88.03", "1", "$88.03 (20\"; OnlineMetals $109.45 for 24\")", "2 Nov", "Midwest"],
    "rd138": ["91.84", "1", "$91.84 (48\"; Midwest $117.08 for 40\")", "2 Nov", "OnlineMetals"],
    'A:1/4" plate 21.5" × 21.5"': ["170.74", "2", "$170.74 each at 2, $168.24 at 3"],
    'B:1/4" circle 21" dia': ["141.39", "2", "$141.39 each at 2, $138.89 at 3 (3 Nov; was $144.54 on 31 Oct)", "3 Nov"],
    'HR:1/2" plate 17" × 18"': ["148.41", "1", "$148.41 for 1, $140.91 each at 2"],
}
data = inch(dict(plan=plan, bars=BARS, other=OTHER, buy=BUY, seen=SEEN))
tpl = open("site_cutplan/template.html").read()
html = tpl.replace("/*__DATA__*/null", json.dumps(data, separators=(",", ":")))
os.makedirs("out/cut_plan", exist_ok=True)
open("out/cut_plan/index.html", "w").write(html)
print("wrote out/cut_plan/index.html", len(html) // 1024, "kB")
