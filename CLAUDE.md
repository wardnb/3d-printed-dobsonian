# CLAUDE.md: 16" GoTo Dob rebuild

Context for Claude sessions on this repo. Read this first. The living design doc is the source of truth for
decisions; this file is the working knowledge needed to continue the engineering without re-deriving it.

- Design doc (Claude Docs, editable): https://claude.ai/code/artifact/a2bd133b-cebf-4c55-a572-9a930c1ab10f
  (project id a2bd133b-cebf-4c55-a572-9a930c1ab10f, tab 765a3677-140b, body node ae7985e7-5528).
  `docs/design.md` is a Markdown export; re-export after changes.
- `docs/measurements.md` is the log of as-built measurements; `docs/dobstuff_kit_reference.md` is what the DobStuff blog shows.
- 3D viewer artifact: https://claude.ai/artifact/J1dg2GqFYWfny88NzJT5gF (republish from `goto-rebuild/dist/index.html`
  with the seven `*.glb.txt` files; see "Viewer" below).
- Cut plan (aluminium stock, nests + price fields): https://claude.ai/artifact/237LEPgBL1Bg77qVBxu3X3 — `cut_plan.py` (nests the DXFs → `out/cut_plan/plan.json`) then
  `build_cut_plan_page.py` (template `site_cutplan/template.html` → `out/cut_plan/index.html`); re-run both after any part change and republish.
- Truss joints viewer: https://claude.ai/artifact/1scoQ7z6AcpRmrQ3ZDc6of (source `goto-rebuild/site_joints/index.html`,
  models from `truss_joints.py` → `out/truss_joints/`; bundle to `dist_joints/` as base64 `.glb.txt` and republish).

## Owner and working style

- Nick (wardnb). Intermediate Python; fine with other languages if needed.
- Wants an engineer's review, not reassurance: run numbers, rank findings by cost to image quality, fix them in
  the model, say plainly what is assumed.
- Visual observing first. Imaging (ASI533 + OAG) is a future option only; no field rotator, EQ platform maybe later.
- Machines: AltMill 2×4 CNC (primary for aluminium and birch), LongMill CNC, Voron Trident 3D printer.
  CAM is Vectric Aspire (Windows): DXF per part from the export scripts → Aspire toolpaths → gSender. No Fusion.
- Material: every Al alloy has the same stiffness (~10 Msi) and the designs are stiffness-limited, so 6061-T6 is the default.
  Flat, heavily pocketed plates (cage rings, cell frame, focuser board) may be cast tooling plate (ATP-5 = cast 5083, or MIC-6):
  stress-relieved, milled faces, stays flat. Its yield is well below 6061-T6, so loaded threads in it (cell collimation bolts) get steel inserts;
  truss plugs, sockets and clamped/threaded blocks stay 6061.
- Transport: Kia EV6; liftgate opening about 25" tall is the binding limit (every piece ≤ about 23" tall).
- Many dimensions are ASSUMED until Nick measures; keep them flagged and say so in answers.

## Hardware on hand

- Hubble Optics 16" plate-glass sandwich mirror, about f/3.9 (FL about 62.4"; confirm from test-report ROC).
  Hubble lists 406 mm, about 42 mm thick, about 10.5 kg (23 lb).
- DobStuff 16" strut kit (Dennis Steele, 2022): 9-point non-flotation cell (triangular 3/4" plate, nine fixed pads,
  hung on three spring knobs through the bottom ring), mirror cage = two 3/4" ply rings + six short spacer tubes +
  two ply side panels; three 45 × 2.5 mm aluminium strut tubes (measured 2026-10-19, 50.5" long) slide through 45 mm holes in the top ring and mount on the bottom ring;
  originally strings and a single upper ring "pre-installed for a 3-vane spider". Ebony Star on Teflon bearings,
  detachable D bearings with wingnuts. DobStuff closed 2024-12-31 (densteele@gmail.com).
- SiTech Servo Controller II; Nexus DSC Pro.
- Pittman GM9213 and GM9413 gearmotors, 24 V, 19.7:1, 500 CPR encoders (LO-COG family).
- 1800Destiny 180 Series Professional curved 3-vane spider (vanes 1.5" × 1/16", 1/4-20 clinch nut at each tip).
- Feather Touch FTF2015BCR focuser: 1.4" racked in, 3.0" out, 1.5" travel, 1.55" of drawtube below the
  mounting face when racked in, 3 lb.
- Pegasus Pocket Powerbox (two RCA dew outputs; cuts out above about 14–14.5 V, so regulate LiFePO4 to 12 V).
- WO UniGuide 50 + ToupTek G3M662C = "Waypoint" plate-solving finder (WO slide base, 515 g, 265 mm; goes in a Synta-style shoe).
- ZWO ASI533 and an OAG (imaging only; OAG not used for Waypoint).
- 2" eyepieces: Apertura Panorama 21 and 28 mm (82°), Celestron E-Lux 26/32/40 mm (56°); 1.25" SVBONY 6/9/15/20 mm.
  ES 2" 2× Focal Extender (telecentric). Filters: Optolong L-Pro, Astronomik OIII 12 nm (2"). ES field flattener
  (refractor only, not for the Dob).

## Decisions (and why) — do not reopen without new data

| Topic | Decision | Why / rejected alternatives |
| --- | --- | --- |
| Upper cage | **v3 (2026-10-30): triangulated.** Two 1/4" 6061 rings with arc lightening slots, ID 17.5", OD 20.5", 7.5" clear gap; four 3/4" square 6061 posts at 45/135/225/315° (carry the spider studs); six 5/8" × 0.058" 6061 diagonals in inverted Vs from node blocks on the lower ring at 0/90/270° up to clevis blocks on the side faces of the neighbouring posts near the top; focuser bay (135–225°) left open; 1/4" focuser board on two 1/2"×3/4" rails, 3-point push-pull. Cage metal 9.3 lb | Idea from the iOptron Photron 16" RC truss cage. cage_fe.py: 0.007 mm drift after 45° collimation vs 0.024 mm for the v2 3/8" solid post-only cage, and 2 lb lighter. Inverted V beat upright V and X (3–4×) because its lower ends land at the truss pair-block supports; bracing the focuser bay made the light rings worse (loads the rails). Slots are only acceptable because the cage is triangulated. The 3D-printed cage failed and is retired. |
| Finder mount | **Adjustable cradle between the rings at 150° (v3.2, lightened 2026-10-30)**: 1/4 × 1.0" bar 0.55" outside the OD on a 1/2" angle block at each ring (#10 FHCS countersunk through the ring at r 9.15/9.85"); 1/4" × 0.85" tilt plate with a bought metal Synta-style shoe, standing on three ball-point 10-32 set screws (two at ±0.3" at the mirror end = pitch hinge, so it cannot roll; one at the sky end = pitch, 23′/turn) with a clamp screw at each end (sky one in a slot) and a 1/2" yaw yoke with opposed 10-32s (29′/turn), ±0.7° pitch, ±1.1° yaw. Cradle metal 0.50 lb + shoe; `upper_cage_lb` 12.2 | A riser on the upper ring twisted the 1/4" ring: Waypoint moved 2.2′ horizon→zenith (2.0′ even with a rigid bracket). Cradle 0.70′ (`cage_fe.py finder`); the first 3/8" bar / 3/4" blocks version was 0.57′ at 0.83 lb, not worth the weight because the rings, not the bar, set it. v3.1 single spherical pivot + single push point left the plate free to roll on its centreline (held only by friction): fixed with the two-screw hinge. The 135° post mount was as stiff but sits further from the eyepiece next to a vane stud. Shroud is slit around the blocks. Shoe hole spacing ASSUMED. Destiny towers (0.37 lb) are no longer counted in cage metal (curved option only). |
| Spider | Straight 4-vane, 0.020" stainless × 1.5" tall, vanes at 45/135/225/315° anchored on the POSTS between the rings (#10-32 studs through the posts, nut outside = tension). Hub (2.6" dia, 2.0" bore) = secondary holder top plate, just under the upper ring | Cage+spider FE: 0.02 mm drift. Anchoring on blocks above the ring was 0.08 mm. Wire spider (8 × 0.025", long hub) reached 0.12 mm and obstructs more; shelved. Destiny curved needs towers on the ring and ~0.3 mm drift (curved vanes bend); kept only as a drawn alternative. Nick explicitly wants load-bearing anchors between the rings, not cantilevered off one ring. |
| Secondary | 3.5" minor axis (not 3.1") | At L = 11.9" the 3.1" has only ~0.05" fully illuminated; 3.5" gives ~0.45", obstruction 21.9% (invisible visually). |
| Secondary holder | Mirror bonded face-down in a jig to a carrier on three 0.012" pads (RTV in wells); carrier doweled to a 45° body; push screws tapped in the hub at r 1.1", pull screws in ±4° arc slots at r 0.8" for clocking; 1/4-20 centre retainer; Kapton heater + NTC on the Pegasus | Solves "glued it on twisted"; clocking is a normal collimation step. Offset built into the dowel pattern (0.317" along the major axis for 3.5"). |
| Focal plane | L (secondary centre to focus) = 11.9" | FTF2015 + coma corrector (needs ~0.75" in-travel) sits mid-travel; racked-out shoulder-plane eyepieces still focus; drawtube clears the 8" beam when in use. |
| Coma corrector | Always in. Explore Scientific HR 2" (~$200 on sale) chosen on price; Paracorr 2 (~$577) equivalent for this use | Reducers and refractor flatteners are wrong for this scope. Extender stacks eyepiece → extender → corrector. |
| Truss | Wide-pair octahedron: three pre-joined pairs of **1.25" × 0.062" roll-wrapped carbon poles, ~38.5" long** (decided 2026-10-18 after measuring: the box's top ring sits 7" below the altitude axis, not 1" above). Pair blocks under the cage's lower ring at 30/150/270°; each pair spreads ±60° to cone sockets on two neighbouring 45 mm stubs at 90/210/330°: back holes at r 10.625", point hole at r 10.25" (from Nick's wooden_cage.step pilot holes; 18.5" back to back, 18.0" to the point). Poles come in two lengths, 37.88" and 37.93" node to node (since the 2026-10-31 socket change), and the pair blocks at 30° and 150° are mirror images | Narrow pairs (±30°) were 2× softer. Truss FE at 38.5", wide pairs, ideal joints: 1" Al 0.086 mm, 1.25" Al 0.070, 1.25" carbon 0.042 (lateral mode 88 Hz vs 62). With 20,000 lb/in base joints carbon still drifts 0.32 mm, so the joints, not the poles, set the result: cone plugs must be bonded into the pole bore with zero play. Raising the sockets on taller stubs rejected (7" cantilever of the 45 × 2.5 mm tube ≈ 16,000 lb/in, still in series with the joints). Two-piece poles studied 2026-10-30 (`truss_fe.py split`; pole EA/L ≈ 90,000 lb/in): a threaded coupler pulled to a shoulder costs 0.027→0.032 mm, a slip spigot with a knob 0.11 mm (×4), a loose slip joint 0.27 mm, plus any play shows directly because pole loads reverse with altitude; also 6 more joints at setup and the pairs can no longer be pre-joined. Not adopted: 38.5" poles already lie flat in the EV6. |
| Truss joints | Bonded 6061 plugs with 60° cone ends into countersunk cups in socket blocks; **drawbolt preload (2026-10-31):** a 1/4-20 stainless stud Loctited along the pole axis into the plug nose runs through the cup apex into a pocket milled in from the block's outside face, where a 0.9" knurled thumbwheel nut pulls the cone in (~80–150 lb by hand; a retaining pin across the pocket mouth keeps the wheel captive). Socket block 3.6 × 2.0 × 2.1" with a 1.569" spigot bonded into the 40 mm bore of the stub, cone apex 1.0" above the stub top (`socket_node_above_stub`). Stubs held axially by two 45 mm two-piece clamp collars, one each side of the box's top ring. Pair blocks: poles bonded, 2 reamed dowels + 1 knob on a stud into the cage ring. Setup: 6 thumbwheels + 3 knobs. Poles now 37.88"/37.93" node to node, carbon cut 35.8" | `truss_fe` pole forces: near the horizon two poles carry 21–27 lb TENSION and one socket is pulled up 46 lb, so the earlier side knob on a brass pad (friction only, no axial preload) would let cones lift and the stub slide. Preloaded cones are far stiffer than 50,000 lb/in, above which `mcage_fe` shows the joints cost ≤ 0.03 mm (the 20,000 lb/in case, 0.17 mm, was a clamp-block guess). The drawbolt axis below the cup heads into the stub (0.55–0.69" from its axis), so a bottom-exit nut is impossible: hence the side pocket. Pair-block loads are small (≤ 8 lb pull, 12 lb side): one knob's friction holds them, dowels only locate. |
| Mirror box | **Keep the DobStuff box as is; no doublers** (`mcage_fe.py`, 2026-10-30), except the two back wings beside the side strips that the D bearings bolt to (2026-10-31, see Altitude bearings). At the push-pull conversion clock the cell so its three studs sit next to the stubs at 90/210/330°; pin each stub axially at both boards; keep the spacer bolts tight | Box + truss + mirror FE: the ply box adds ~0.012 mm (0.028 rigid → 0.040 as built). Cell studs between the stubs 0.12 mm, 60° off 0.11 (the mirror board bends between supports); stubs pinned at both boards 0.022, top ring only 0.060; loose spacer ends 0.073; a 6061 ring under the board only recovers 0.049. Sockets at 20,000 lb/in still dominate (0.17). Mirror lateral support was the biggest term at this end; the new cell (Mirror cell row) takes it to ~0.01 mm. |
| Mirror cell | **New 6061 9-point flotation cell (decided 2026-10-30; `cell.py`, `export_cell.py` → `out/cell/`).** Debond the mirror from the old glued triangle (wire saw through the 9 dabs). Y frame of 1/2" 6061/MIC-6 with arms to three 5/16-24 collimation bolts at r 6.5" clocked to the stubs (90/210/330°), bolts through flanged SAE 841 bronze bushings in the mirror board, 1/4-20 push screws in board inserts, no springs. Three 1/4" triangles on 3/8" balls at r 4.14"; pads 1" Delrin + cork at r 3.45" (0.431 R) and 5.36" (0.670 R, ±33.1°), moved under the sandwich's pucks before drilling. Edge: two 1/2" gussets at 225/315° with 1.4" Delrin faces spanning both plates at mid-thickness, slotted, set touching. Guard posts 0.5 mm off at 90/210/330° with safety tabs 1 mm above the face. 80 mm fan under the hub. Cell 4.9 lb (`cell_lb`, CG 3.46" below the face) | Old cell: mirror glued to a ply triangle on spring studs held sideways only by knob friction (0.2–0.8 mm possible) + glue shear (0.04–0.43 mm). `cell_support_fe.py` (scikit-fem Morley plate, equal loads, power removed, D ~4e5 N m ASSUMED): 3-pt 8.3 nm RMS, 6-pt ring 1.2, chosen 9-pt 1.0 nm RMS / 4.6 nm P-V surface, so the layout is not critical; pad-over-puck matters more for a sandwich. Edge gussets 74,000 lb/in → 0.008 mm shift. Mirror face lands where it was (board top within 0.01"). 1/16 turn of a bolt ≈ 0.4 mm at focus: big knobs. |
| Altitude bearings | Rebuilt (drawn 2026-10-19, `rocker.py`): 14" radius D, two 18 mm Baltic birch layers (1.42" thick) bolted to the box side's outer face: a 2.6" running rim + 1.2" bar along the straight edge + 3" vertical web, two lightening windows, 6.6 lb each. **Joint (2026-10-31, `bearing_fe.py`):** the box side = the existing 3" strip + a new 18 mm back wing glued between the boards (z −6.4 to −1.5, 4.9 × 11.38", top-back corner notched 2.3 × 0.70" around the 330/210° stub's lower collar, Confirmat screws through both boards at z −2.3/−3.6); the D sits on two 3/8" steel dowels pressed into the D (one on the rim at z −5.6, one on the web top at z +0.9) running in blind steel drill bushings, plus six 1/4-20 bolts into threaded inserts (`rocker.BEARING_HOLES`); drill the box through the D as a template. The straight edge sits 3.6" past the axis plane so the front pad stays under the arc down to 15° altitude. PTFE pads at ±30°. Drive-side rim from the inner face: 0.15" bare, 0.36" GT2 belt, 0.64" Ebony Star, 0.26" magnetic tape | A plain semicircle with pads at ±30° loses the front pad below 30° altitude; the chord offset e = R·sin(pad − alt_min) fixes it at the cost of the D standing 10.1" above the box's top ring. The web is the only place the hoop can reach the box (the box side is open except the 3" strip and the ring edges). Aluminium rejected (edge too narrow, heavier). Joint: as first drawn (2 dowels + 2 × 1/4" bolts in a 4.8 × 1.8" patch on the 3" strip) the tube wound up 0.25"/in-lb against the alt pinion at 15° (0.49 once the bolts slip onto the dowels), 0.09 at 45°, and a 3 g jolt put ~400 lb on each bolt (more than their friction in ply), after which dowel-hole play shows as alt backlash (0.001" ≈ 85"). With the wing: 0.058"/in-lb at 15°, 0.021 at 45° (0.13 slipped), 3 g bolt load ≤ 146 lb. Ribs or a solid D barely help (the patch, not the D, sets it). The wing cannot run forward of the strip: the boards' edge is the r 10.75 front arc there. |
| Drives | Belt-on-rim on both axes: 9 mm GT2 glued teeth-out, sprung 20T pinion (0.5" PD), 2:1 GT2 stage. Alt GM9413 112:1; Az GM9213 on the ROCKER driving a fixed 30" ground ring (cut to 480 teeth), 120:1 | 1.9× torque margin each axis, ~10–11°/s slew, ~0.28"/motor count. Friction capstan rejected (μ≈0.2 → 150 lb preload). Az motor on the rocker so no cable crosses the az axis. Cable drive is the fallback. Ron's DobStuff GoTo uses SiTech + "gear and rack", confirming the approach. |
| Encoders | Magnetic tape (not optical) on bearing rim and ground-ring rim, sprung read heads into SiTech encoder inputs, used for POSITION only (pointing, slip recovery); tracking runs on the motor encoders (0.28"/count), with OAG guiding when imaging (Nick, 2026-10-31) | Floating PTFE bearing can't hold an optical head gap. AS5311-class heads on 2 mm-pole tape: ~1.1"/count quadrature, ±10 µm cyclic INL = ±6" with a ~19′ period, ~2" hysteresis: fine for location, not for tracking at 0.48"/px. RLS LM10 hysteresis < 3 µm but SDE unpublished. |
| Backlash | Keep 20–30 in-lb mirror-end imbalance | Keeps the gear train loaded one way. |
| Balance | Solved with no counterweight: mirror face 13.5" below the altitude axis (13.1 lb of bearings in the solve), eyepiece ~63.6" at zenith, nested transport height ~13.5" (measured box) | DobStuff spacing (axis ~7" above the mirror) would need ~34 lb counterweight. The new 14" D bearings stand ~10" above the box's top ring (7" to the axis + the 3.6" chord offset) and bolt to its side strips through a web. |
| Rocker | **Rebuild, drawn 2026-10-19** (`rocker.py`, DXFs from `export_rocker.py`): 18 mm Baltic birch; walls 27.4" long centred under the pads (inner faces ±11.31", 0.48" off the box), top edge an arc 0.4" under the bearing rim from −42° to +42° with 1.6" pad seats at ±30°, horns 12.8" above the floor, sloping to 4" end boards; floor 24.05 × 27.42" on the walls, 3/8" pivot; drive wall carries the sprung alt pinion (notch at the bottom of the arc, arm + GM9413 outboard), the alt tape read head on the back horn at −50°, the az bracket at y = +8.5" reaching the ground ring's rim, a PTFE lateral stop at +37°; SiTech box on the plain wall. Ground board: 8" hub + three 3.5" arms (90/210/330°) + a 30" OD × 23" ID ring in three 120° segments joined on the arms (two pilots per end) with az PTFE pads at r 12.75" and feet at r 14". Rocker 15.9" tall overall (EV6 ok). Existing rocker (22 1/4 × 23" inside, 11/16" ply, pads 15 3/8" apart at 14 3/4") kept as a fallback | 14" bearings on the existing pads put the axis 2.6" too high; lowering the pads means cutting an assembled box. Every bracket face is a drilled hole pattern on the DXF. End boards are limited to 4.2" by the box's 23" swing circle (checked in `export_rocker.py`). The AltMill bed is 48.6 × 24.4, so 5×5 sheets are ripped into 24.4 × 60 strips and every blank is checked (shapely) in `export_rocker.py`: one blank per bearing layer (the D is 28 × 17.6; two never share a blank), both walls nested inverted on one blank with the arms, the ring thirds on a 32" blank; the floor (24.05 × 27.42) is table-sawn from a strip and only drilled on the AltMill. Three 5×5 sheets. Ring halves (30 × 15) were dropped because they needed a blank each. |
| Wiring | Cage hub; USB3 + 12 V trunk crosses the altitude axis at the D-bearing's straight edge (twist loop, no rim groove) | Electronics box on the rocker; mini PC for ASCOM/plate solving. |
| Guiding | OAG only (imaging); a separate guide scope suffers differential flexure at 1626 mm | |

## Error budget (focal-plane drift horizon→zenith, 0.5 mm tolerance)

Cage + quad spider 0.012 mm with the v3 triangulated cage and finder cradle (0.007 with the old ring bracket) (cage_fe.py; 0.024 mm for the old 3/8" post-only cage) · truss 0.04 mm ideal, ≤ 0.03–0.05 mm with preloaded cone joints (drawbolts), 1.25" carbon at the
measured 38.5" (truss_fe.py) · mirror box 0.012 mm (mcage_fe.py, cell studs at the stubs) · new cell: edge support ~0.01 mm, bushing play ≤ 0.05 mm, support figure ~1 nm RMS · total ≈ 0.2–0.25 mm. Collimate at 45° and the visible error halves.

## Model code (`goto-rebuild/`)

- Python + CadQuery 2.x (`pip install cadquery numpy matplotlib shapely`). Units: inches in, mm out (`IN = 25.4`).
- Frame: tube axis +Y toward the sky, focuser on −X, altitude axis along X. In `upper_cage.py` y = 0 is the
  secondary centre; `dob_model.py` translates into the scope frame (`y_sec`).
- Environment: `goto-rebuild/.venv` (CadQuery installed 2026-10-18); run as `cd goto-rebuild && .venv/bin/python dob_model.py`.
- `dob_model.py`: params `P` (ASSUMED values flagged; mirror cage now measured: `mcage_top_above_mirror`, `mcage_height`;
  stubs at `mcage_tube_angles` with per-hole `mcage_tube_radii`, exported as `frame.stub_xz` for the FE and joint scripts; model frame has the point hole at 90°), balance solve by bisection on `net_moment`, mirror cage,
  truss (`truss` narrow, `truss_zig` = chosen wide pairs), bearings, drives; writes `out/*.glb`, `out/dob16_alt45.step`,
  `out/params.json`. Key params: `L_secondary_to_focus=11.9`, `secondary_minor=3.5`, `mcage_tube_angles`, `stub_proud`.
- `upper_cage.py`: INPUTS dict (plate 0.25, board_t 0.25, lighten True); STRUTS, QUAD, TOPS (Destiny seats), DIAG_LO + `diagonals()` (v3),
  APEX (truss pair blocks), FINDER=150°, FC + `finder_cradle()` (adjustable Waypoint cradle); `quad_spider()`, `spider_blocks()`, `wire_spider()`, `alignment_bar()`,
  `centering_gauge()` (X-bars with a plug into the hub bore), `build()`.
- `secondary_holder.py`: P (minor 3.5, thick 0.70 ASSUMED), `carrier_flat()`, `jig_flat()`, `build()`.
  Jig standoff = mirror thickness − 0.11" (5/8" for 0.70").
- `export_cage.py`: fit checks (clashes, beam r = 8", board holes, focuser cone, spider/gauge clashes) → `out/upper_cage/fit_report.json`, DXFs, STEPs, cut sheet.
- `export_holder.py`: carrier/jig DXFs, holder STEP, gluing jig STEP.
- `rocker.py`: `derive(P, R, swing, panel_x)` → all rocker/bearing numbers (`G`, also written to `params.json["rocker"]`);
  `bearing_outline(G)` (the D used by `dob_model.py` for both bearings); `build(G)` → world-frame solids for the base
  assembly + 2D flats + bracket hole lists. Rocker params in `P`: `alt_pad_angle`, `alt_min_deg`, `rocker_horn_angle`,
  `rocker_inside_depth`, `rocker_end_height`, `ground_ring_od/id`, `ground_foot_radius`, `ground_pad_radius`.
- `export_rocker.py`: reads `params.json`; swing-circle clearance of every rocker piece inside the box's width, bearing-vs-rocker
  interference at 15/45/90°, pad-inside-Ebony-band check, AltMill size check; DXF per part (`out/rocker/*_18mm-birch.dxf`),
  `cut_sheet_rocker.png` (one panel per 24.4 × 48 AltMill blank, placements in `LAYOUT`, overlap/margin check with shapely → `layout_ok`), `fit_report.json`. Run after `dob_model.py`.
- `cage_fe.py`: 3D frame FE (custom `Frame` class) of the cage + spider; defaults = v3 (quad spider, diagonals="vinv0", ring_t from upper_cage); `python cage_fe.py tri` compares bracing patterns; `python cage_fe.py finder` compares Waypoint mounts (finder tilt in arcmin; default finder="cradle"). Metric = primary's
  focus reflected by the deflected secondary, minus eyepiece motion, swept 0–90°.
- `truss_fe.py`: truss FE (cage rigid, box rigid); reads `out/params.json`, run from `goto-rebuild/`. Zigzag apexes at 30/150/270 (fixed 2026-10-30: they were at 0/120/240, so the bases fell back to R_BOT instead of the measured stubs; 0.027 → 0.028 mm). `python truss_fe.py split` = two-piece pole study.
- `mcage_fe.py`: mirror box (ply rings, spacers, stubs, side strips, bearing-web supports) + truss + mirror + rigid upper cage in one frame; mirror carries the primary's focus (shift and tilt). Options: `spacer_ends`, `stub_axial`, `cell_angles`, `board_plate`, `e_ply`, `hole_k`, `strip_k`, `sock_k`.
- `cell.py`: new mirror cell (params `C`, `pads()`, `frame_poly()`, `build()` with the mirror face at y = 0, `report()` with weights and edge stiffness); `dob_model.py` places it at `y_mirror`. `export_cell.py`: fit checks (inside the cell, against stubs and spacers) → `out/cell/fit_report.json`, DXFs (frame, triangle ×3, gusset ×2), STEP, cut sheet. `cell_support_fe.py`: plate support optimiser (scikit-fem; `pip install --break-system-packages scikit-fem`).
- `bearing_fe.py` (2026-10-31): in-plane plane-stress FE (scikit-fem P2 + `triangle` mesher, `pip install --break-system-packages triangle`) of the D bearing
  and its fasteners to the box's 3" side strip. Metrics: tube rotation vs the alt pinion and vs the rim read head, under gravity (alt sweep) and per in-lb of
  drive torque; "clamped" (bolt friction holds) vs "slipped" (dowels only). As drawn (2 dowels + 2 bolts in a 4.8 × 1.8" patch): windup 0.17"/in-lb at 15°
  (0.39 slipped), 0.058 at 45°; fasteners see 144 lb at 1 g, ~430 lb per bolt at 3 g (more than two 1/4" bolts' friction in ply). Half of it is the joint,
  half the D pivoting about the small patch; ribs or a solid D barely help. A ~13" wide side panel between the boards with dowels on the rim at ±6.2"
  takes it to 0.044 (0.092 slipped). Since then the box side is meshed too (its own plane-stress part, glued edges fixed), which made the as-drawn
  case worse (0.25 at 15°, 0.49 slipped); the chosen back wing (`WING`, `WING_FASTENERS`) gives 0.058 (0.13 slipped). `python3 bearing_fe.py plots` redraws
  `out/bearing_fe/compare_windup.png`. Not modelled: out-of-plane (lateral) stiffness of the D/strip.
- `truss_joints.py`: joint detail (60° cone plugs bonded in the carbon poles, socket blocks with a spigot bonded into the
  45 mm stubs and two cups at ±0.8" on the tangent, pair blocks bonded to both poles with two dowels and one knob under
  the cage ring). Reads `out/params.json`; writes GLBs and STEPs to `out/truss_joints/`. Plug shank sized for a
  1.126" bore: re-run after measuring the real tube.
- `wire_geo2.py`, `wire_geo3.py`: wire-spider layout studies (historical).
- Always re-run `export_cage.py` after cage/spider edits and check `clashes_in3`, `quad_spider_clashes`,
  `quad_vanes_in_focuser_cone` are empty/False.

## Viewer

- `site/index.html` (three.js 0.160.0 from jsdelivr) + `build_site.py` → `dist/`. `build_site.py` also rebuilds `out/truss_zigzag.glb` from
  `truss_joints.build_viewer()` (real socket blocks, drawbolts, collars, pair blocks), so run it after `dob_model.py`; the cage's
  `pair_connectors_concept` is no longer drawn by `dob_model.py`. GLBs are shipped as base64
  `.glb.txt` because the artifact host does not serve `.glb`; the page decodes them with `GLTFLoader.parse`.
- Spider radio: Quad (default), Curved, Wire. Truss radio: Wide pairs (default), Narrow pairs.
- Screenshots: Playwright with `executablePath: /opt/pw-browsers/chromium-1194/chrome-linux/chrome`, routing the
  CDN to a local three install (`tools/shot*.js`).

## Environment gotchas (Claude cloud sessions)

- Outbound network is allowlisted; Blogger image URLs (blogger.googleusercontent.com) are blocked, so DobStuff blog
  photos can't be downloaded there. On Nick's desktop (beast) they load fine, and the whole blog is already archived at
  `~/Documents/dobstuff-blog-archive/` (index, full post text, 502 images). Findings are in `docs/dobstuff_kit_reference.md`.
- Claude Docs edits: use find/replace with text quoted exactly; whole-block replaces need ifHash + ifRev.

## Open measurements (replace ASSUMED values)

- [x] Mirror cage: long struts 45 mm OD × 40 mm ID aluminium in 45 mm ring holes (calipers); seven 1 1/4" spacer tubes (three at the back, two per side at the front). Tube holes confirmed at the model's 120° pattern (one square to the bearings); hole circle radius 10.7" (18.5" chords, tape),
      ring ID 18", box 11 3/8" between the boards, mirror face about 7" below the top ring (photo readings, see `docs/measurements.md`).
      The bearings are the box's sides (narrow ply strips, no side panels).
- [ ] Mirror board: opening diameter (about 10" from a photo) and old stud holes, so the new bolt circle (r 6.5") lands on clean board; black baffle clearance at r 8.0–10.8" at the cell; how the stubs are held along their axis in each board
- [ ] After debonding: puck map of the sandwich back (pads go under pucks), 80 mm fan size check
- [~] Cell: 1/4" studs with ~1" coil-spring stacks between the 3/4" ply triangle and the mirror board, wing knobs on the back (photos 2026-10-30); the light "disc" seen from the back is the triangle with three cooling holes; mirror GLUED to the triangle's pads (thin dark layer). Still to get: stud-hole diameter in the board, knob angles relative to the stubs, and the two dial-indicator readings (indicator on the box → total mirror shift; on the triangle → cell slop alone)
- [x] Altitude bearing measured: running radius 12 3/16", lip 12 3/8", 18 mm ply + 3/16" lip, axis on the straight edge (`docs/measurements.md`). Pad positions, rocker width, ground board still open
- [~] Box rings: strut positions from the strut bolt holes in `docs/wooden_cage.step` (the ORIGINAL UPPER RING, not the box) and
      `docs/printed_cage.step`: back r 10.625" at 30/150, point r 10.25"; straight struts through the box, so the box holes match.
      The box ring outline is drawn as that upper ring (flats ±10.75", point 12.125", back arc r 15.7 with corners at r 12.56")
      and the back shape is ASSUMED: measure on the box tip to back edge on the centreline and tip to a back corner (sets the
      swing radius). Still open: back hole to point hole 18.0" by tape, weights (box with mirror, one bearing, one strut),
      a caliper reading on a spacer tube, how the strut ends were bolted.
- [ ] Box side flats (for the D-bearing back wings): on both boards, how far the flat side edge runs back from the strip's back edge (model: to z −6.49 from the bearing axis, i.e. 4.99" past the strip), and how the existing strip is fixed to the boards (notched in? glued to the board edges?). Also confirm the 330/210° stubs sit ~0.04" inside the side plane.
- [ ] ES HR coma corrector (if/when imaging with a rotator): measure the barrel shoulder to the M48 face (d). Camera focus needs the CC's M48 face 55 mm in front of the sensor and the
      sensor ~35 mm outside native focus (one blog source), so the drawtube end sits at native − 20 mm − d; the FTF2015 racked in is 38 mm inside native at L = 11.9", so d ≤ ~18 mm
      or the camera can't reach focus. Train within the 55 mm: ASI533 Pro 6.5 + ZWO OAG ~16.5 (which OAG Nick owns: ASSUMED) + Falcon v2 16 + adapters ~3 ≈ 42 mm, ~13 mm spare;
      a 20 mm filter drawer does not fit (filter on the CC nose or in a thin M48 cell). Rotator goes before the OAG.
- [ ] FTF2015 base bolt circle and hole size
- [ ] 3.5" secondary thickness when ordered
- [ ] Mirror ROC from the Hubble test report (confirms f/3.9)
- [ ] Starting force on each axis (luggage scale) to confirm motor assignment
- [~] Existing encoders are Astro Devices HD Sensor + 2" magnetic ring (Nexus DSC Pro kit, ~311,296 steps/rev per their guides). Still to settle: whether the SiTech can take them, or they stay on the Nexus and the SiTech gets its own tape encoders

## Next design work

Rocker and ground board drawn 2026-10-19 (`out/rocker/`). Before cutting: Nick to confirm the 15° minimum altitude (it sets the
D's 3.6" chord offset and the 10.1" stand-off above the box; 20° would give 2.4"/8.9"), the pad angle, and tape the box's
back outline (swing radius → wall height ±0.4"). Bracket parts themselves (sprung alt arm with the 2:1 stage, az bracket, read-head
brackets, lateral stops) are drawn as envelopes only; detail them once the GT2 pulleys and read heads are in hand. Then socket
blocks and pair blocks (detail drawings + wedge fixture), push-pull cell conversion, electronics box layout, and a
cage-on-truss combined FE once the weights are in.
