# CLAUDE.md: 16" GoTo Dob rebuild

Context for Claude sessions on this repo. Read this first. The living design doc is the source of truth for
decisions; this file is the working knowledge needed to continue the engineering without re-deriving it.

- Design doc (Claude Docs, editable): https://claude.ai/code/artifact/a2bd133b-cebf-4c55-a572-9a930c1ab10f
  (project id a2bd133b-cebf-4c55-a572-9a930c1ab10f, tab 765a3677-140b, body node ae7985e7-5528).
  `docs/design.md` is a Markdown export; re-export after changes.
- `docs/measurements.md` is the log of as-built measurements; `docs/dobstuff_kit_reference.md` is what the DobStuff blog shows.
- 3D viewer artifact: https://claude.ai/artifact/J1dg2GqFYWfny88NzJT5gF (republish from `goto-rebuild/dist/index.html`
  with the seven `*.glb.txt` files; see "Viewer" below).
- Truss joints viewer: https://claude.ai/artifact/1scoQ7z6AcpRmrQ3ZDc6of (source `goto-rebuild/site_joints/index.html`,
  models from `truss_joints.py` → `out/truss_joints/`; bundle to `dist_joints/` as base64 `.glb.txt` and republish).

## Owner and working style

- Nick (wardnb). Intermediate Python; fine with other languages if needed.
- Wants an engineer's review, not reassurance: run numbers, rank findings by cost to image quality, fix them in
  the model, say plainly what is assumed.
- Visual observing first. Imaging (ASI533 + OAG) is a future option only; no field rotator, EQ platform maybe later.
- Machines: AltMill 2×4 CNC (primary for aluminium and birch), LongMill CNC, Voron Trident 3D printer.
  CAM is Vectric Aspire (Windows): DXF per part from the export scripts → Aspire toolpaths → gSender. No Fusion.
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
- WO UniGuide 50 + ToupTek G3M662C = "Waypoint" plate-solving finder (standard Synta-style finder foot).
- ZWO ASI533 and an OAG (imaging only; OAG not used for Waypoint).
- 2" eyepieces: Apertura Panorama 21 and 28 mm (82°), Celestron E-Lux 26/32/40 mm (56°); 1.25" SVBONY 6/9/15/20 mm.
  ES 2" 2× Focal Extender (telecentric). Filters: Optolong L-Pro, Astronomik OIII 12 nm (2"). ES field flattener
  (refractor only, not for the Dob).

## Decisions (and why) — do not reopen without new data

| Topic | Decision | Why / rejected alternatives |
| --- | --- | --- |
| Upper cage | Two solid 3/8" 6061 rings, ID 17.5", OD 20.5", 7.5" clear gap; four 3/4" square 6061 posts at 45/135/225/315°; 1/4" focuser board on two 1/2"×3/4" rails, 3-point push-pull | 1/4" slotted rings flexed ~3× more (cage FE). Lightening slots cost 8× in-plane stiffness for 1.3 lb. Aluminium chosen over ply for repeatable bolted joints. The 3D-printed cage failed and is retired. |
| Spider | Straight 4-vane, 0.020" stainless × 1.5" tall, vanes at 45/135/225/315° anchored on the POSTS between the rings (#10-32 studs through the posts, nut outside = tension). Hub (2.6" dia, 2.0" bore) = secondary holder top plate, just under the upper ring | Cage+spider FE: 0.02 mm drift. Anchoring on blocks above the ring was 0.08 mm. Wire spider (8 × 0.025", long hub) reached 0.12 mm and obstructs more; shelved. Destiny curved needs towers on the ring and ~0.3 mm drift (curved vanes bend); kept only as a drawn alternative. Nick explicitly wants load-bearing anchors between the rings, not cantilevered off one ring. |
| Secondary | 3.5" minor axis (not 3.1") | At L = 11.9" the 3.1" has only ~0.05" fully illuminated; 3.5" gives ~0.45", obstruction 21.9% (invisible visually). |
| Secondary holder | Mirror bonded face-down in a jig to a carrier on three 0.012" pads (RTV in wells); carrier doweled to a 45° body; push screws tapped in the hub at r 1.1", pull screws in ±4° arc slots at r 0.8" for clocking; 1/4-20 centre retainer; Kapton heater + NTC on the Pegasus | Solves "glued it on twisted"; clocking is a normal collimation step. Offset built into the dowel pattern (0.317" along the major axis for 3.5"). |
| Focal plane | L (secondary centre to focus) = 11.9" | FTF2015 + coma corrector (needs ~0.75" in-travel) sits mid-travel; racked-out shoulder-plane eyepieces still focus; drawtube clears the 8" beam when in use. |
| Coma corrector | Always in. Explore Scientific HR 2" (~$200 on sale) chosen on price; Paracorr 2 (~$577) equivalent for this use | Reducers and refractor flatteners are wrong for this scope. Extender stacks eyepiece → extender → corrector. |
| Truss | Wide-pair octahedron: three pre-joined pairs of **1.25" × 0.062" roll-wrapped carbon poles, ~38.5" long** (decided 2026-10-18 after measuring: the box's top ring sits 7" below the altitude axis, not 1" above). Pair blocks under the cage's lower ring at 30/150/270°; each pair spreads ±60° to cone sockets on two neighbouring 45 mm stubs at 90/210/330°: back holes at r 10.625", point hole at r 10.25" (from Nick's wooden_cage.step pilot holes; 18.5" back to back, 18.0" to the point). Poles come in two lengths, 38.15" and 38.20" node to node, and the pair blocks at 30° and 150° are mirror images | Narrow pairs (±30°) were 2× softer. Truss FE at 38.5", wide pairs, ideal joints: 1" Al 0.086 mm, 1.25" Al 0.070, 1.25" carbon 0.042 (lateral mode 88 Hz vs 62). With 20,000 lb/in base joints carbon still drifts 0.32 mm, so the joints, not the poles, set the result: cone plugs must be bonded into the pole bore with zero play. Raising the sockets on taller stubs rejected (7" cantilever of the 45 × 2.5 mm tube ≈ 16,000 lb/in, still in series with the joints). |
| Truss joints | Bonded 6061 plugs with 60° cone ends into countersunk sockets; side knob presses a brass pad (only to stop lift-off). Base sockets have a 1.569" spigot bonded into the 40 mm bore of the DobStuff stubs left in the cage's holes, 1" proud. Nine knobs total | Zero play by construction; loads go straight to the bottom ring. No aluminium plate on the cage top ring needed. |
| Mirror cell | Keep DobStuff 9-point cell. Replace spring knobs with push-pull (3 × 5/16-24 + lock). If silicone-bonded: keep, no sling. If loose: 1/2" × 0.010" stainless strap at the CG plane | Sandwich is stiff (Hubble uses 6 points). Springs move with altitude. |
| Altitude bearings | Rebuilt: 14" radius D, two laminated 3/4" Baltic birch layers, cut with dowel holes in one AltMill setup; Ebony Star on PTFE pads at ±35°; drive-side rim = 0.6" Ebony Star band + 0.4" GT2 belt band + 0.3" sealed tape band | Concentric rim for the belt and encoder; dowels for repeatable detach. Aluminium rejected (edge too narrow, heavier). |
| Drives | Belt-on-rim on both axes: 9 mm GT2 glued teeth-out, sprung 20T pinion (0.5" PD), 2:1 GT2 stage. Alt GM9413 112:1; Az GM9213 on the ROCKER driving a fixed 30" ground ring (cut to 480 teeth), 120:1 | 1.9× torque margin each axis, ~10–11°/s slew, ~0.28"/motor count. Friction capstan rejected (μ≈0.2 → 150 lb preload). Az motor on the rocker so no cable crosses the az axis. Cable drive is the fallback. Ron's DobStuff GoTo uses SiTech + "gear and rack", confirming the approach. |
| Encoders | Magnetic tape (not optical) on bearing rim and ground-ring rim, sprung read heads into SiTech encoder inputs | Floating PTFE bearing can't hold an optical head gap. |
| Backlash | Keep 20–30 in-lb mirror-end imbalance | Keeps the gear train loaded one way. |
| Balance | Solved with no counterweight: mirror face 13.9" below the altitude axis, eyepiece ~63.5" at zenith, nested transport height ~13.5" (measured box) | DobStuff spacing (axis ~7" above the mirror) would need ~34 lb counterweight. The new 14" D bearings stand ~7" above the box's top ring and bolt to its side strips. |
| Rocker | **Rebuild** (decided 2026-10-19): 3/4" Baltic birch cut on the AltMill from the model's DXFs, sides cut to the new axis height with pad pockets, alt pinion and encoder brackets, az motor bracket and the pivot bore machined in; new ground board carrying the fixed az ring. The existing rocker (22 1/4 × 23" inside, 11/16" ply, pads 15 3/8" apart at 14 3/4") is kept intact as a fallback | Width would have worked as-is (bearings ride on top of the side panels), but 14" bearings on the existing pads put the axis 2.6" higher than the 23.9" the box needs (eyepiece 66" not 63.6"), and lowering the pads means cutting an assembled box. Retrofit = a few afternoons of hand-fitted brackets on an old box; rebuild = one 5×5 sheet (~$100) and a Saturday with every bracket face machined where the model says. The ground board is new either way (fixed az ring). |
| Wiring | Cage hub; USB3 + 12 V trunk crosses the altitude axis at the D-bearing's straight edge (twist loop, no rim groove) | Electronics box on the rocker; mini PC for ASCOM/plate solving. |
| Guiding | OAG only (imaging); a separate guide scope suffers differential flexure at 1626 mm | |

## Error budget (focal-plane drift horizon→zenith, 0.5 mm tolerance)

Cage + quad spider 0.02 mm (cage_fe.py) · truss 0.04 mm ideal, ~0.1–0.15 mm with real cone joints, 1.25" carbon at the
measured 38.5" (truss_fe.py) · cell ~0.05–0.12 mm · total ≈ 0.25 mm. Collimate at 45° and the visible error halves.

## Model code (`goto-rebuild/`)

- Python + CadQuery 2.x (`pip install cadquery numpy matplotlib`). Units: inches in, mm out (`IN = 25.4`).
- Frame: tube axis +Y toward the sky, focuser on −X, altitude axis along X. In `upper_cage.py` y = 0 is the
  secondary centre; `dob_model.py` translates into the scope frame (`y_sec`).
- Environment: `goto-rebuild/.venv` (CadQuery installed 2026-10-18); run as `cd goto-rebuild && .venv/bin/python dob_model.py`.
- `dob_model.py`: params `P` (ASSUMED values flagged; mirror cage now measured: `mcage_top_above_mirror`, `mcage_height`;
  stubs at `mcage_tube_angles` with per-hole `mcage_tube_radii`, exported as `frame.stub_xz` for the FE and joint scripts; model frame has the point hole at 90°), balance solve by bisection on `net_moment`, mirror cage,
  truss (`truss` narrow, `truss_zig` = chosen wide pairs), bearings, drives; writes `out/*.glb`, `out/dob16_alt45.step`,
  `out/params.json`. Key params: `L_secondary_to_focus=11.9`, `secondary_minor=3.5`, `mcage_tube_angles`, `stub_proud`.
- `upper_cage.py`: INPUTS dict (plate 0.375, board_t 0.25, lighten False); STRUTS, QUAD, TOPS (Destiny seats),
  APEX (truss pair blocks), FINDER=150°; `quad_spider()`, `spider_blocks()`, `wire_spider()`, `alignment_bar()`,
  `centering_gauge()` (X-bars with a plug into the hub bore), `build()`.
- `secondary_holder.py`: P (minor 3.5, thick 0.70 ASSUMED), `carrier_flat()`, `jig_flat()`, `build()`.
  Jig standoff = mirror thickness − 0.11" (5/8" for 0.70").
- `export_cage.py`: fit checks (clashes, beam r = 8", board holes, focuser cone, spider/gauge clashes) → `out/upper_cage/fit_report.json`, DXFs, STEPs, cut sheet.
- `export_holder.py`: carrier/jig DXFs, holder STEP, gluing jig STEP.
- `cage_fe.py`: 3D frame FE (custom `Frame` class) of the cage + spider; `python cage_fe.py quad`. Metric = primary's
  focus reflected by the deflected secondary, minus eyepiece motion, swept 0–90°.
- `truss_fe.py`: truss FE (cage rigid); reads `out/params.json`, run from `goto-rebuild/`.
- `truss_joints.py`: joint detail (60° cone plugs bonded in the carbon poles, socket blocks with a spigot bonded into the
  45 mm stubs and two cups at ±0.8" on the tangent, pair blocks bonded to both poles with two dowels and one knob under
  the cage ring). Reads `out/params.json`; writes GLBs and STEPs to `out/truss_joints/`. Plug shank sized for a
  1.126" bore: re-run after measuring the real tube.
- `wire_geo2.py`, `wire_geo3.py`: wire-spider layout studies (historical).
- Always re-run `export_cage.py` after cage/spider edits and check `clashes_in3`, `quad_spider_clashes`,
  `quad_vanes_in_focuser_cone` are empty/False.

## Viewer

- `site/index.html` (three.js 0.160.0 from jsdelivr) + `build_site.py` → `dist/`. GLBs are shipped as base64
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
- [~] Cell: 1/4" spring studs; mirror sits on a thin ply disc over the 3/4" triangle; bond still unconfirmed (no RTV visible at the edge)
- [x] Altitude bearing measured: running radius 12 3/16", lip 12 3/8", 18 mm ply + 3/16" lip, axis on the straight edge (`docs/measurements.md`). Pad positions, rocker width, ground board still open
- [~] Box rings: strut positions from the strut bolt holes in `docs/wooden_cage.step` (the ORIGINAL UPPER RING, not the box) and
      `docs/printed_cage.step`: back r 10.625" at 30/150, point r 10.25"; straight struts through the box, so the box holes match.
      The box ring outline is drawn as that upper ring (flats ±10.75", point 12.125", back arc r 15.7 with corners at r 12.56")
      and the back shape is ASSUMED: measure on the box tip to back edge on the centreline and tip to a back corner (sets the
      swing radius). Still open: back hole to point hole 18.0" by tape, weights (box with mirror, one bearing, one strut),
      a caliper reading on a spacer tube, how the strut ends were bolted.
- [ ] FTF2015 base bolt circle and hole size
- [ ] 3.5" secondary thickness when ordered
- [ ] Mirror ROC from the Hubble test report (confirms f/3.9)
- [ ] Starting force on each axis (luggage scale) to confirm motor assignment
- [~] Existing encoders are Astro Devices HD Sensor + 2" magnetic ring (Nexus DSC Pro kit, ~311,296 steps/rev per their guides). Still to settle: whether the SiTech can take them, or they stay on the Nexus and the SiTech gets its own tape encoders

## Next design work

Rocker and ground board (next up, decided 2026-10-19): size the rocker to the measured box (bearings on the side strips at
±10.84", 1.5" thick, pads on the panel tops), walls to the model's axis height, pad pockets, alt pinion + encoder bracket faces,
az motor bracket, pivot, fixed az ring on the ground board, EV6 height check; export DXFs per part for Aspire. Then socket
blocks and pair blocks (detail drawings + wedge fixture), push-pull cell conversion, electronics box layout, and a
cage-on-truss combined FE once the weights are in.
