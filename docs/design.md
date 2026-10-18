# 16" f/3.9 GoTo Dobsonian Rebuild — Design Doc

> Exported from the living design doc (https://claude.ai/code/artifact/a2bd133b-cebf-4c55-a572-9a930c1ab10f) on 2026-10-18. The doc is the source of truth; re-export after changes.


Oct 18, 2026 · @Nickolous Ward

## Goals and requirements

Rebuild the 16" f/3.9 DobStuff strut Dob into a visual-first GoTo and tracking scope that holds collimation across the full altitude range. Figures marked *est.* are placeholders until measured.

- **Primary use:** visual observing; live stacking with the ASI533 is a possible later add-on, long-exposure imaging is out of scope.
- **GoTo accuracy:** land within 10–15 arcmin, so targets fall in a low-power field (about 1° true field).
- **Tracking:** smooth at 200x and above; DragNTrack so the scope can still be pushed by hand without losing position.
- **Collimation:** laser spot stays put from 20° altitude to zenith after one collimation at setup.
- **Usability:** eyepiece no higher than about 65" at zenith; field setup under 20 minutes; runs from one battery.
- **Fabrication:** structural birch and precision aluminum parts cut on the AltMill 2×4; buy only optics, bearings and electronics.

## Parts on hand and parts to buy

The electronics and focuser are already owned; the open purchases are the secondary, axis encoders, power and bearing materials.

| Part | Status | Notes |
| --- | --- | --- |
| Hubble Optics 16" f/4 sandwich primary | Owned | In the DobStuff cell |
| SiTech Servo Controller II | Owned | 12–28V, 5A min; servo motors + scope encoders |
| Nexus DSC Pro | Owned | Talks to SiTech over RS232; Wi-Fi to SkySafari |
| Pittman GM9413 24V 19.7:1 500 CPR | Owned | Higher torque; goes on the harder axis |
| Pittman GM9213 24V 19.7:1 500 CPR | Owned | Second axis |
| 1800Destiny 180 Series curved-vane spider | Owned | 10–18" range; ¼-20 center |
| Feather Touch 2" Crayford | Owned | 1.405" racked-in height; travel version TBD |
| 3.5" secondary mirror | To buy | 1/20 wave, enhanced aluminum |
| 3.5" secondary holder (own design, see below) | To buy | ¼-20 center bolt, 3 push-pull tilt screws |
| Axis encoders ×2 | To buy | For SiTech S.E. inputs; 8k–32k steps/rev |
| Nexus–SiTech serial cable | Check | RJ11 to RJ22 |
| 12V LiFePO4, 10Ah+ | To buy | Must supply 5A; powers both units |
| Ebonystar, PTFE pads, Dyneema or SS cable, GT2 belts and pulleys | To buy | Bearings and drive stages |
| ¼" 6061 plate, 12–18mm Baltic birch | To buy | Cage, cell, brackets; box, rocker, ground board |

## Optical design

Use a 3.5" secondary (decided after the design review; 3.1" was the first choice), offset 0.22" toward the primary and away from the focuser, with the focal plane 11.9" from the secondary's center to suit the FTF2015 with a coma corrector in.

| Parameter | Value |
| --- | --- |
| Aperture / focal ratio | 16" (406 mm) / f/3.9 |
| Focal length | 62.4" (1,585 mm); confirm from the test report's ROC |
| Cage ring inside diameter | 17.5" |
| Focuser board inner face to optical axis | 8.75" (board 1/4" on rails between the 3/8" rings) |
| Feather Touch FTF2015 racked-in / out | 1.4" / 3.0" |
| Secondary center to focal plane (L) | 11.9" (coma corrector mid-travel) |
| Primary face to secondary center | 50.5" |

| Secondary | Fully illuminated field | Obstruction | Offset |
| --- | --- | --- | --- |
| 3.1" (first choice) | 0.30" / 7.7mm | 19.4% | 0.19" |
| 3.5" (chosen; figures at L = 11.4", about 0.45" fully illuminated at 11.9") | 0.79" / 20.1mm | 21.9% | 0.22" |

Fully illuminated field = (minor axis − L/N) / (1 − L/F). Focus position along the tube is set at setup by how far the truss poles seat, not by the cage. Coma at f/3.9 is obvious, so a coma corrector is part of the design: the Explore Scientific HR (about $200) or the Paracorr 2; L = 11.9" puts either at mid-travel in the FTF2015.

## Primary mirror cell

Keep the DobStuff 9-point non-flotation cell (triangular 3/4" plate, nine fixed pads, hung on three knobs through the bottom ring). The Hubble Optics sandwich is stiff enough for fixed pads; Hubble uses 6 points on its own UL16. Two changes:

- Replace the spring-loaded collimation knobs with push-pull: three 5/16-24 bolts with locking pull screws.
- If the mirror is silicone-bonded to the pads, keep it that way and add no sling; if it sits loose on pads, add a 1/2" × 0.010" stainless strap at the mirror's centre-of-gravity plane.

Mirror (Hubble Optics spec): 406 mm diameter, about 42 mm thick, about 10.5 kg (23 lb). Details in the mirror box and cell review below.

## Upper cage

Two solid 3/8" 6061 rings (round, with the focuser board spanning between them; cage v11/v12 used only as a measurement reference) joined by aluminum struts, with a separately adjustable focuser board, targeting under 8 lb with focuser, secondary and holder.

- **Rings:** 17.5" ID × 20.5" OD, 3/8" 6061, solid (design review, v2: the 1/4" pocketed rings of v1 were five times floppier out of plane than a 3/4" plywood ring and doubled the collimation drift). About 3.25 lb each.
- **Ring spacing:** 7.5" clear between the rings.
- **Struts:** four 3/4" square 6061 posts bolted into both rings at 45/135/225/315°; they also anchor the quad spider's vanes and the alignment bar.
- **Focuser board:** ¼" aluminum, Feather Touch base pattern machined in, mounted on three push-pull screws for tilt adjustment square to the optical axis.
- **Spider blocks:** three machined blocks at 120° for the Destiny three-vane curved spider, aligned with the truss pair-clamps so vane loads go straight into the poles. The upper ring is also drilled for a straight 4-vane spider at 0/90/180/270° (0° seat shared), so either spider bolts in without re-machining the ring; the quad set uses its own four blocks with through holes for tension rods and nuts.
- **Lower ring:** three truss pair blocks at 30/150/270° for the wide-pair 6-pole truss.
- **Extras:** light baffle opposite the focuser; shroud attachment lip; mount point for a secondary dew heater.
- **CAD approach:** one parametric CadQuery script exporting DXF for the AltMill and STEP for Fusion; ring size, secondary size, focuser height and pole layout are inputs.

## Spider and secondary holder

Decided after the design review: a straight 4-vane spider of 0.020" (0.5 mm) stainless vanes, 1.5" tall, anchored on the four posts between the rings at 45/135/225/315° by #10-32 studs, tensioned from outside. The hub is the secondary holder's top plate. Cage plus spider hold the focal point to 0.02 mm horizon to zenith. Four spikes at 45° to the altitude axis.

- Holder: the self-aligning 3.5" holder below (carrier bonded in a jig, doweled to a 45° body, push-pull tilt, ±4° clocking).
- The Destiny curved spider remains a drawn alternative on towers above the ring (about 0.3 mm drift, no spikes); the wire spider is shelved.

## Truss, mirror box, rocker and ground board

Keep the DobStuff mirror cage and rocker layout; replace the three struts and strings with a 6-pole truss.

- Mirror cage as built: two 3/4" plywood rings, six short tubes between them, two side panels for the bearings, and three 1.25" tube holes through the top ring to mounts on the bottom ring. Short stubs of those tubes stay in the holes, 1" proud, and the truss sockets plug into them.
- Truss: wide pairs (an octahedron). Three pre-joined pairs of 1" × 0.058" 6061 poles, about 30" long, each pair joined at a block under the cage's lower ring (30/150/270°) and spreading to cone sockets on two neighbouring stubs (90/210/330°). Cone-ended plugs, nine knobs, no tools.
- Altitude bearings: 14" radius D, two laminated layers of 3/4" Baltic birch, Ebony Star on PTFE pads at ±35°, doweled so they return to the same place. Drive side carries the GT2 belt and the magnetic tape.
- Rocker and ground board: rocker carries both motors; the ground board gets a 30" ring whose rim carries the azimuth belt and tape.
- Balance: solved with no counterweight; mirror face 14.6" below the altitude axis, eyepiece about 60.6" at zenith.

## Portability and setup

The scope breaks into five pieces, none over about 60 lb or 23" tall, and assembles in under 20 minutes with no tools and no re-tensioning.

| Piece | Contents | Weight (est.) | How it travels |
| --- | --- | --- | --- |
| Rocker with nested mirror cage | Mirror cage with primary in cell, rocker, alt motor, electronics box | 50–60 lb | One unit, mirror cover on, 23" tall or less |
| Ground board + D bearings | 30" ring with belt and tape, feet; two altitude bearings | 15–18 lb | Flat; bearings in a padded sleeve so the Ebonystar edges stay clean |
| Upper cage | Spider, secondary, Feather Touch, dew heater | under 8 lb | Padded case, focuser board facing up |
| Truss | Six poles as three pre-joined pairs | 6–8 lb | Padded pole bag |
| Power and Nexus | 12V LiFePO4, Nexus, cables | 6–8 lb | Small case |

**Design choices that make setup fast and repeatable**

- **Pole pairs, not loose poles:** each pair is joined at the top by a machined connector, so three units go in, not six. All pairs are identical and interchangeable.
- **Clamps:** mirror-box clamps with captive cam levers; cage connectors with captive knobs. Pole ends register against a hard stop so the cage seats at the same height every time.
- **Keyed cage:** one connector is shaped differently so the cage only goes on one way, keeping the focuser in the same orientation and collimation repeatable.
- **Drives stay mounted:** both motors and pinions ride on the rocker; the belts stay glued on the bearing and the ground ring; spring-loaded pinions lift off for hand pushing.
- **One electronics box on the rocker:** SiTech, fuse block and connectors inside; GX16 aviation connectors for motors, encoders and power, each keyed so cables can't be swapped.
- **Setup sequence:** ground board, rocker and mirror box, three pole pairs, cage, power cable, laser collimation check, two-star align on the Nexus.
- **Vehicle fit:** Kia EV6. Published figures put the liftgate opening at about 41" wide by about 25" tall (height is an estimate), cargo width 43", and floor length about 31" seats up and about 65" seats down. Height is the binding constraint: every piece must load at 23" tall or less, so the D-shaped altitude bearings come off and the mirror cage nests inside the rocker, as the DobStuff design already does. The nested unit must measure 23" or less. Verify the 25" opening with a tape before cutting. Sources: [itemfits](https://itemfits.com/fit/vehicle/kia-ev6/cargo), [Recharged](https://recharged.com/articles/kia-ev6-cargo-space-dimensions/).

## Drive mechanics

Both axes use a GT2 belt glued teeth-out on the rim and a sprung 20T pinion on a 2:1 stage from the gearmotor. Full numbers are in the bearings and drives review below.

| Axis | Drive | External ratio | Motor | Torque margin | Slew |
| --- | --- | --- | --- | --- | --- |
| Altitude | Belt on the 14" bearing rim | 112:1 | GM9413 | 1.9× | about 11°/s |
| Azimuth | Belt on the 30" ground ring, motor on the rocker | 120:1 | GM9213 | 1.9× | about 10°/s |

- Motor encoders: 500 CPR, 0.27–0.29" per count. Scope encoders: magnetic tape on the bearing rim and the ground ring, sprung read heads.
- Keep a 20–30 in-lb mirror-end imbalance so the gear train stays loaded one way.

## Electronics

The SiTech runs the motors and reads all four encoders; the Nexus sits on top as the user interface, so no PC is needed at the scope.

&#91;embedded content: control and power wiring · 7 parts\]

- **Connections:** Nexus serial port to SiTech RS232; both scope encoders to the SiTech S.E. inputs, not the Nexus encoder port; encoder step values entered identically in both units.
- **Power-up order:** SiTech first, then Nexus. If the SiTech loses power, redo the two-star alignment.
- **Power:** one 12V LiFePO4 pack feeding both units through a fused distribution block. 24V would double slew speed but needs a separate supply for the Nexus (max 16V).
- **Setup tools:** ServoConfig on a Windows laptop for motor PID tuning and encoder scaling, one time on the bench.
- **Optional later:** plate-solving finder with the G3M662C to sync pointing automatically.

## Fabrication plan on the AltMill 2×4

Aluminum for every part that holds alignment; birch for the large structure; buy thin vanes, bearings and fasteners.

| Part | Material | Notes |
| --- | --- | --- |
| Cage rings ×2 | ¼" 6061 | 20.5" OD fits the 24" width; pocketed; tabbed hold-down |
| Focuser board | ¼" 6061 | Feather Touch base pattern, 3 push-pull holes |
| Spider and strut blocks | ½"–¾" 6061 bar | Small parts, batch on one fixture |
| Truss clamps | 6061 bar | Both ends; matched to pole diameter |
| Mirror cell (if new) | ¼" 6061 + small bar stock | 9-point triangles and rockers |
| Motor brackets, belt plates | ¼" 6061 | Slotted for belt tension |
| Encoder mounts | 6061 | Concentric to bearing pivot and az bolt |
| Mirror box, rocker | 18mm Baltic birch | Finger joints or dados |
| Altitude bearings | 18mm birch, doubled | Exact radius; Ebonystar applied after |
| Ground board, az disc | 18mm birch | Disc edge machined true for roller |
| Spider vanes (fallback) | 0.040" spring steel | Bought strip, cut to length |

All profiles come from the parametric CadQuery script so a dimension change regenerates every affected DXF.

## Phased build and test plan

Six phases, each ending in a pass/fail gate before the next starts; the electronics bench test can run in parallel with phase 1.

1. **Measure and model.** Measure the mirror, poles, spider tips and DobStuff cell; finalize the CadQuery script.
   - Gate: all *est.* values replaced with measurements.
2. **Upper cage.** Cut rings, board and blocks; install the quad spider, holder, 3.5" secondary and Feather Touch.
   - Gate: laser collimation holds within a few millimeters at the primary from 20° to zenith.
3. **Primary cell.** Inspect and modify the DobStuff cell, or cut the new 9-point cell.
   - Gate: star test at 300x shows no astigmatism or pinching at any altitude.
4. **Electronics bench test (parallel).** Wire both Pittmans and encoders to the SiTech; tune PID in ServoConfig; pair the Nexus.
   - Gate: smooth motion both directions, clean encoder counts, Nexus shows live position.
5. **Mount and drives.** Build mirror box, rocker, ground board, altitude bearings and drive stages; install motors and encoders.
   - Gate: balanced at all altitudes with eyepiece swaps; clutches release cleanly; hand-push keeps position.
6. **Field commissioning.** Two-star align, GoTo test across the sky, tracking at high power.
   - Gate: 10 of 10 GoTos land in a 1° field; a planet stays centered at 250x for 10 minutes.

## Model v1 results (superseded; current figures in the reviews below)

The first parametric model balances with no counterweight once the mirror face sits 12.7" below the altitude axis; the DobStuff spacing of about 8" would need roughly 21 lb. Viewer: [16-inch Dob Rebuild](https://claude.ai/artifact/J1dg2GqFYWfny88NzJT5gF).

| Result | Value |
| --- | --- |
| Mirror face below altitude axis | 12.7" (solved for balance) |
| Altitude axis height | 22.3" |
| Eyepiece height at zenith | 62.2" |
| Nested transport height | 17.9" |
| Truss poles | 6 × 34.0" |
| Tube weight | about 68 lb |
| Altitude bearing radius / external ratio | 14" / 112:1 (1" capstan, 4:1 belt) |
| Azimuth external ratio | 90:1 (1" roller on 30" rocker disc, 3:1 belt) |

The az drive now runs on the rocker's round floor disc, with the motor and roller on the ground board. These numbers supersede the earlier drive-ratio estimates and will change once the open measurements are in.

## Wiring plan

Everything on the upper cage plugs into a cage hub, so only one trunk of two cables (USB3 and 12 V) runs down the truss. Moving the az drive onto the rocker means nothing electrical crosses the azimuth bearing.

&#91;embedded content: wiring plan · cage hub, one trunk, rocker box\]

| Device | Location | Power | Data |
| --- | --- | --- | --- |
| ASI533 Pro camera (EAA, optional) | Focuser | 12 V, up to about 3 A with cooling | USB3 |
| Focus motor (ZWO EAF on Feather Touch, or Starlight MicroTouch) | Focuser | 12 V or USB, depending on model | USB |
| Waypoint finder: G3M662C in the William Optics UniGuide 50 mm (200 mm f/4, slide base, 515 g): 1.6° × 0.9° field at 3.0"/px | Upper ring, near the focuser | USB | USB2 |
| Secondary heater | Spider vane | Pegasus channel 1 (RCA) | None |
| Finder dew strap | Finder | Pegasus channel 2 (RCA) | None |
| Pegasus ambient probe | Upper cage, shaded | From Pegasus | None |
| Red-dot or Telrad | Upper ring | Own battery | None |
| Spare | Cage hub | One 12 V port, one USB port | For later |

- **Cage hub:** powered USB3 hub plus the Pegasus, mounted on the lower ring on the side opposite the focuser. It offsets some of the focuser's weight and stays out of the light path. Weigh both parts and add them to the cage weight for balance.
- **Trunk:** one USB3 cable and one 16 AWG 12 V pair, clipped to one pole pair. A locking power connector and USB3 bulkhead on the cage hub let the cage come off. A slack loop near the altitude bearing centre keeps the cables from tugging from horizon to zenith.
- **Rocker box:** LiFePO4, 12 V regulator (also fixes the Pegasus over-voltage issue), mini PC, SiTech, Nexus. The battery rides on the rocker so no cable crosses azimuth.
- **Az drive change:** put the az motor and read head on the rocker, rolling on a fixed drive ring on the ground board, rather than on the ground board turning the rocker. The alternative is a slip ring at the centre bolt.
- **Mini PC:** runs SiTechExe (ASCOM), plate solving for the finder camera, and live stacking. Check that the SiTech will talk over USB to the PC while the Nexus uses its RS232 port.
- **Mirror cage tap:** one 12 V connector at the mirror cage for an optional boundary-layer fan.
- **Guider:** not needed for visual or live stacking. If an EQ platform comes later, use an off-axis guider in the camera train. A separate guide scope anywhere on the truss scope (mirror cage or upper cage) sees differential flexure: 1 arcsec over a 34" truss is about 4 microns of relative movement, far below what disturbs collimation (about 0.5 mm tolerance at f/3.9) but enough to smear an exposure. An OAG looks through the same primary, secondary and focuser, so any flex moves the guide star and the image together.
- **Cable management:** clips on both rings and every pole pair; no cable crosses the light path; drip loops point down.

**Tensioning the wire spider:** tune it by ear. In the v2 layout the upper wires are 8.8" and the lower 9.7". At 40 lb a 0.025" wire plucks at about 600 Hz (upper) and 545 Hz (lower); at 20 lb, 425 and 385 Hz; at 10 lb, 300 and 270 Hz. Any phone tuner app reads it. A #10-32 stud adds about 11.5 lb per quarter turn, and full tension is under one turn from snug.

1. Fit the hub and holder (or a 1.3 lb dummy) with the centring gauge in place.
2. Hook each wire at the hub (ball-end plain-steel guitar strings sit in counterbores; plain stainless wire uses a crimp sleeve), thread it through its stud, pull out the slack and clamp.
3. Bring all eight to about 280 Hz, working in opposite pairs like wheel lug nuts.
4. Raise in quarter-turn rounds to about 560 Hz, keeping the gauge rod dropping freely into the hub.
5. Finish with every wire within ±10 Hz of the others; recheck after a few days of settling. A 20°C cold night drops tension by only about 2.6 lb (aluminium shrinks more than steel).

## Optical axis alignment

The CNC-cut rings, rails and board put the focuser on the designed axis; a removable alignment bar lets you prove it once and square the board.

- **Alignment bar (tool):** 1/2" square 6061, about 14.3" long, ends cut at 45° to sit on the 45° and 315° posts at secondary height, one #10-32 screw each. A 1/16" target hole on the designed focuser axis faces the focuser. It sits in the light path: remove it before observing.
- **Hub centring gauge (tool):** two 1/2" plywood bars across the upper ring (along 30–210° and 90–270°, clear of towers, finder bracket, extension blocks and wires), four 1/4" spigot feet that locate on the 17.5" ring ID, and a 2.45" centre bore. Tension opposite studs until its 1.95" plug drops freely into the quad hub's 2.0" bore, which centres it to ±0.025".

1. Secondary out, bar in. Put the laser in the focuser and adjust the board's three push-pull screws until the beam goes through the bar's target hole. Remove the bar.
2. Centre the hub with the gauge (wire spider) or the spider's own adjustment (Destiny).
3. Fit the secondary. Through a sight tube it should look round and centred.
4. Laser back in: rotate and tilt the secondary until the beam hits the primary's centre spot.
5. Tilt the primary until the beam returns on itself; confirm with a barlowed laser or Cheshire.

Steps 1–3 are one-time; nightly collimation is steps 4–5. File: `alignment_tools.step`.

## Secondary holder and gluing jig

The mirror is bonded to a flat carrier in a jig, never straight onto the 45° body, so it cannot be glued twisted, tilted or off-centre, and the 0.20" offset is built in.

| Part | Stock | Key features |
| --- | --- | --- |
| Carrier | 1/4" 6061 | 4.35" × 3.26" ellipse for the 3.5" secondary (inside the mirror's shadow); 3 pads 0.012" proud set the glue gap; 3 RTV wells; 3× #8 screws and two 1/8" dowels (hole + slot) on the holder axis, 0.317" from the mirror centre along the major axis |
| Body | 3.0" dia 6061 bar | Cut at 45°, matching #8 taps and 1/8" dowel holes on the face; 1/4-20 centre tap and 3 push-pull pairs on top. Needs a 45° fixture on the AltMill, or start from a bought holder body and drill to the carrier pattern |
| Jig base | 1/2" birch or 6061 | Mirror-outline pocket 0.375" deep with finger notches; 2 standoffs |
| Jig bridge | 1/4" plate | Two 1/8" pins on the carrier's dowel pattern, on 5/8" standoffs (0.038" above the 0.70" thick mirror's carrier; standoff = mirror thickness − 0.11") |

Gluing procedure:

1. Lay lens tissue in the jig pocket and set the mirror in face down.
2. Fill the three carrier wells with neutral-cure (alkoxy) RTV, slightly domed.
3. Lower the carrier onto the mirror's back, pads down, then fit the bridge so its pins drop through the carrier's dowel hole and slot.
4. Let it cure 24 hours undisturbed; the pads keep the gap even, so no weight is needed.
5. Lift out with the finger notches and trim any RTV squeeze-out.
6. Bolt the carrier to the body on its dowels. It only goes on one way and returns to the same place after cleaning.

Standoff length is about mirror thickness minus 0.11"; recheck when the mirror arrives (0.60" assumed).

## Secondary dew heater

A 2–3 W heater on the back of the 3.5" secondary, run by a thermostatic controller in the electronics box, keeps the secondary about 2°C above the dew point without making heat plumes in the light path.

- **Heater:** thin Kapton or resistor heater about 2.5" across on the back of the secondary, behind a thin thermal pad; 12 V at about 50 Ω gives roughly 3 W. A 10k NTC thermistor sits beside it. Off-the-shelf alternative: AstroSystems Dew Guard DG-1 (sized for 2.4–3.1" minor axis, self-regulating).
- **Wiring:** a thin twisted pair (26 AWG heater, 28 AWG sensor) bonded along the trailing edge of one spider vane, so it stays edge-on to the light and adds no diffraction. A small locking connector at that vane's spider block lets the cage come off; the lead then runs down one truss pole to the electronics box.
- **Control:** the Pegasus Pocket Powerbox already owned (2 RCA PWM dew outputs, external temperature/humidity probe, auto mode from the dew point). Channel 1 runs the secondary heater; channel 2 is spare for a finder or eyepiece heater. The heater needs an RCA plug. Mount the Pegasus in the rocker electronics box and put its probe in shade on the upper cage. The Pegasus has no heater-side sensor, so control is open loop on the mirror; the thermistor is optional.
- **Alternative control:** an ESP32 (ESPHome) controller with closed-loop control on the secondary thermistor, if the Pegasus proves too coarse.
- **Power:** about 0.25 A at 12 V for the secondary. Caution: the Pegasus cuts power above about 14–14.5 V depending on model, and a LiFePO4 straight off the charger sits near 14.4 V. Feed the Pegasus through a 12 V regulator, or let the pack settle below 13.6 V before powering up.
- **Cage changes:** a connector pocket and cable clip on one spider block; a cable clip at each ring; a pass-through on the board rail side so the lead clears the focuser.

## Focal length adjustment

The mirror is about f/3.9 (focal length about 62.4"), so the model now uses that. Any remaining difference is absorbed at the lower truss clamps, not in the cage.

- **Coarse, set once:** lower clamps allow about ±1.5" of pole slide. After first light, fix a stop collar on each pole so the cage seats at the same height every setup.
- **Fine, every night:** Feather Touch travel (1.5" assumed) handles eyepiece and Paracorr differences. Set the stops so typical eyepieces focus near mid-travel.
- **Measure first:** take the radius of curvature from the Hubble Optics test report (focal length = ROC ÷ 2), or focus the Sun or a distant light on a card.
- **Secondary at f/3.9:** 3.5" chosen, 0.22" offset per axis; see Optical design.

## Upper cage: machining package

The upper cage is detailed to part level and passes fit checks: no part clashes, nothing intrudes into the 16" beam, and the board's pull holes land on the rails. Metal weight is 6.9 lb; with the focuser, secondary and spider the cage is about 9.6 lb. That heavier upper end moved the balance point: the mirror face now sits 13.8" below the altitude axis.

| Part | Qty | Stock | Machining | Status |
| --- | --- | --- | --- | --- |
| Lower ring (truss end) | 1 | 3/8" 6061 plate | AltMill profile, 12 holes, solid (v2: no lightening slots) | DXF ready, inputs pending |
| Upper ring (sky end) | 1 | 3/8" 6061 plate | AltMill profile, 12 holes, solid (v2: no lightening slots) | DXF ready, inputs pending |
| Focuser board | 1 | 1/4" 6061 plate | AltMill profile; tap 3× #10-32 and 4× #8-32 | DXF ready, focuser pattern pending |
| Struts | 4 | 3/4" 6061 square bar | Cut 7.50", mill ends square and to identical length; tap 1/4-20 (bottom) and 5/16-18 (top, takes the extension bolt); two #10-32 clearance holes at 0.9" for the lower wire studs | Drawing only |
| Post extensions (wire spider v2) | 4 | 1" × 3/4" 6061 bar | Cut 2.30"; 5/16 clearance bore lengthwise; #10-32 clearance hole 1.9" up for the upper wire stud; 1/8" dowel into the ring | Drawing only |
| Quad spider (chosen) | 4 vanes, 1 hub, 4 studs | 0.020" stainless shim, 2.6" dia 6061 bar, #10-32 stainless studs | Vanes 8.0" × 1.5" at 45/135/225/315°, top edge 0.05" under the upper ring; outer end folded 1/2" and riveted to a #10-32 stud through the post at 2.95" above the secondary centre, nut and washer outside; hub 2.6" × 1.04" with a 2.0" bore, 4 saw slots 0.025" and a 0.3" bottom plate = holder top plate (push at r 1.1, pull in ±4° slots at r 0.8, 1/4-20 retainer); the posts get one more radial #10-32 clearance hole each | STEP ready (quad\_spider.step) |
| Board rails | 2 | 1/2" × 3/4" 6061 bar | Cut 7.50", tap ends 1/4-20; 3 push-pull pairs (#10-32 clearance + tapped) | Drawing only |
| Spider blocks | 3 | 1" 6061 square bar | 1" cubes, tap 2× 1/4-20 from below, radial vane-tip hole | Tip hole pending |
| Pair connectors | 3 | 6061 block | Concept only: pole bores need an angle fixture | Needs design pass |

**Spider towers:** the Destiny 180 Professional's aluminum vanes are 1.5" tall by 1/16" thick, and each vane end has a built-in 1/4-20 clinch nut meant to take a screw through a tube wall. A 1/4" ring has no wall, so each vane lands on a tower: 1.0" wide by 1.75" tall, cut flat from 3/4" 6061 plate, standing on the upper ring with 2× 1/4-20 tapped into its foot. Its inner face sits at the ring ID like a short piece of tube wall (the face is flat; over 1" the curvature difference is 0.014", well within the clinch-nut tab's fit). A 1/4-20 × 1" screw passes radially through the tower into the clinch nut at mid-vane height. Same tower for the quad option, with a through hole for a tension rod. Hardware: 3× 1/4-20 × 1" button-head screws (vanes) plus 6× 1/4-20 × 5/8" (tower feet).

**Wire spider v2 (after the design review):** a 2.4" OD hollow hub runs from the secondary holder's top plate up past the upper ring, so its two wire planes sit 3" apart instead of 1.1". The upper wires anchor on four blocks standing on the ring at the post angles; the lower wires anchor on the posts 0.9" above the secondary centre. Each post's high anchor runs down to the hub's low rim and its low anchor up to the high rim, both landing 50° round the hub on the same side; neighbouring posts alternate sides. No gravity load can twist or tilt the hub, and because the eight wires project in only two directions the star image shows four spikes (a 78°/102° X), not eight. With 3/8" solid rings the cage model holds the focal point to 0.12 mm from horizon to zenith; the v1 layout on 1/4" slotted rings wandered 1.8 mm. It still swaps with the Destiny without touching the rings, passes the fit check, no wire enters the cone from the secondary to the focuser, and the two wires of each post pass 0.08" apart where they cross.

| Part | Qty | Spec |
| --- | --- | --- |
| Posts (shared with the cage) | 4 | 3/4" square 6061, 7.50" long, ends tapped (1/4-20 bottom, 5/16-18 top); two #10-32 clearance holes 0.9" above the secondary centre, ±0.15" either side of the centre line; the 45° and 315° posts also get a #10-32 tapped hole at secondary height for the alignment bar |
| Post extensions | 4 | 1" × 3/4" 6061, 2.30" tall, on the ring's sky face at 45/135/225/315°; one 5/16-18 × 3" bolt through block and ring into the post, one 1/8" dowel; two #10-32 clearance holes 1.9" up, ±0.15" off centre. The wire pull puts about 140 in-lb on the joint; a 5/16 bolt preloaded to 2,500 lb holds it with a 3× margin |
| Hub | 1 | 2.4" OD × 3.24" 6061 tube, 1/4" wall, with a 0.3" bottom plate that is the secondary holder's top plate (1/4-20 centre retainer, 3 push screws at r 1.0", 3 pull screws in ±4° clocking slots at r 0.7"; all reached through the bore from the sky end); eight 0.040" radial wire holes through the wall, ball ends inside the bore. About 0.6 lb |
| Wires | 8 | 0.025" plain-steel (music wire) guitar strings or 302 stainless; 8.8" upper, 9.7" lower; 40 lb each (about a third of breaking strength). 0.020" is also fine (cage model: no measurable change) and cuts the diffracted light by 20% |
| Tension studs | 8 | #10-32 stainless, hollow (a threaded hex standoff works), through the post or block with the nut and washer outside; the wire passes through the bore and its stop sits on the outer end |

- **Geometry:** each tower's high wire runs to the hub's low rim and its low wire to the high rim, crossing fore/aft. The two wires land on the hub ±90° from the tower direction, so they pull tangentially in opposite senses. Tilt, side shift, axial motion and rotation are all held by tension.
- **Centring:** adjust opposite studs to slide the hub; collimation tilt stays on the holder's push-pull screws.
- **Diffraction:** 0.020" wire is about one-third the width of the 1/16" Destiny vane, so any spikes are faint.
- **Heater lead:** a fine twisted pair taped along one wire to the hub.
- **File:** `wire_spider_option.step`.

**Waypoint finder mount:** a riser bracket on the upper ring at 150° (30° up from the focuser), cut from 6061 and fixed with 2× 1/4-20. A bought Synta-style finder shoe bolts to its outer face; the UniGuide 50 slides in as it does on your other scopes. Struts moved from 140°/220° to 130°/230° to make room. Adding the finder (about 1.4 lb with camera) moved the balance point again: mirror face 14.2" below the axis, eyepiece about 60.4" at zenith, nested transport height 19.4". The cage hub is not yet in the weight.

**Hardware:** 18× 1/4-20 × 5/8" SHCS (struts, rails, connectors); 6× 1/4-20 × 3/4" SHCS (spider blocks); 3× #10-32 × 1" SHCS (pull); 3× #10-32 × 1/2" nylon-tip set screws (push); 4× #8-32 focuser screws (pending base plate).

**Inputs to confirm before cutting:** Feather Touch base bolt circle and hole size; Destiny vane-tip hole and tip geometry; truss pole OD; plate thickness (1/4" assumed; 3/8" is stiffer and about 1.6 lb heavier); smallest end mill for aluminum (1/4" assumed, so slots are 0.60" wide and holes are drilled or helix-milled).

**Cut files:** `ring_lower_3-8-inch-6061.dxf`, `ring_upper_3-8-inch-6061.dxf`, `focuser_board_quarter-inch-6061.dxf`, and `upper_cage_v2.step` in Fusion for CAM. Hold-down tabs are added in CAM.

## Upper cage design review (v2)

Verdict on the v1 cage: the light path, focuser board, secondary holder and fit all pass, but it would not have held collimation. A frame finite-element model of the whole cage (`cage_fe.py`, 788 nodes: rings as Vierendeel lands, posts, rails, rigid board and hub, wires as bars, truss apexes pinned) predicts the primary's focus wandering 1.8 mm across the eyepiece between horizon and zenith, against a 0.5 mm tolerance at f/3.9. Two causes, both now fixed in the model: the wire spider's hub was too short to resist tilt, and the 1/4" slotted rings were too floppy out of plane. The findings, ranked by what they cost:

| # | Finding | Effect on the image | Fix (status) |
| --- | --- | --- | --- |
| 1 | Wire spider v1: the two wire planes were 1.1" apart while the secondary's 1.3 lb hangs 2.4" below the hub centre. Tilt stiffness was about 1,900 in-lb/rad, and the earlier sag figures (6/55 µm) ignored tilt and the axial-to-twist coupling of the ±90° layout | 1.2 mm of focal-point drift horizon to zenith from the spider alone | Long hollow hub (planes 3" apart), wires paired per post, neighbours alternating, 50° landing: 0.05 mm standalone (done, in the model and viewer) |
| 2 | 1/4" rings with lightening slots: a flat plate ring has an out-of-plane stiffness (I = 0.002 in⁴) five times lower than a 3/4" plywood ring, and the slots cut the in-plane stiffness a further 8× for 1.3 lb saved | Cage flexure alone doubles the spider's drift; 0.86 mm with v2 spider on v1 rings | 3/8" solid rings: 0.12 mm total. Costs 3.3 lb at the top; the balance re-solve moves the mirror 1.9" further below the axis (done) |
| 3 | Destiny fallback on a 1/4" stalk 2.3" long from the towers down to the holder | 0.45–0.73 mm drift; curved vanes carry side loads in bending (thin direction), so even with a rigid stalk about 0.3 mm | 3/4" stalk in the model (done); accept 0.3 mm, or use a straight 4-vane spider on the quad seats (0.02 mm) if spikes are acceptable |
| 4 | Back focus was set for the FTF2008 "Shorty"; the focuser is an FTF2015 (1.4–3.0" travel, 1.55" of drawtube into the tube when racked in). With the Paracorr Type 2, which needs about 3/4" of in-travel, L = 11.4" put the Paracorr 0.25" from the in-stop with the drawtube 0.3" into the beam | A 31 Nagler or any eyepiece with its field stop below the shoulder will not reach focus without the Paracorr; with it, barely | L = 11.9" (done): the Paracorr sits mid-travel with the drawtube clear of the beam. At f/3.9 the Paracorr is not optional |
| 5 | Stray light: the flat 7×9" baffle opposite the focuser covers a third of what the drawtube sees; bare aluminium inside the cage; no shroud attachment | Lower contrast on faint objects and planets | Curved baffle panel on the ring ID over ±60°, full height (in the model, 0.03" aluminium or Kydex, flat black); black anodize or flat-black paint on everything inside the ring ID; Velcro strip on the lower ring OD for a shroud |
| 6 | Wire terminations were "clamps": a 0.025" wire kinked over an edge at 40 lb is a fatigue point | Wire failure in use | Ball ends (plain-steel guitar strings, 0.024–0.026") seated inside the hollow hub; hollow #10-32 studs with the stop on the outer end; no bends under load |
| 7 | Extension-block joint: 2 wires × 40 lb at 1.9" is about 140 in-lb on a block held by one bolt | Block face lifts off the ring and the anchor moves | 5/16-18 bolt (2,500 lb preload, 3× margin) plus a dowel; block 1" radial |
| 8 | Secondary heater leads: a cable taped to a wire would turn it into a thick vane | Diffraction | Run the heater current through two of the spider wires (0.5 Ω each): nylon shoulder washers under those two nuts, nylon bushings at the hub holes |
| 9 | Diffraction budget: 8 × 0.025" wires obstruct about the same area as the three 1/16" Destiny vanes (1.2 vs 1.3 in²) | Same total scattered light as the Destiny, but as four spikes instead of a halo; each spike is about as bright as a 0.5 mm 4-vane spider's | Your call: spikes (wire) or halo (Destiny). 0.020" wire cuts the spike energy 20% at no cost in collimation hold |
| 10 | Posts and rings: single end bolts, mill-flat rings | Ring parallelism and repeatability | Face the post ends on the mill to identical length; add a 1/8" dowel beside each end bolt; cut the rings from stress-relieved plate, rough and finish in two passes |

What passed: the 17.5" ring ID clears a 1.5° true field without vignetting; the drawtube bottom (8.05" from the axis with the Shorty) clears the 8" beam; the 1/4" focuser board tilts only 0.1 mrad under 6 lb of focuser and eyepiece; the hub, holder and carrier stay inside the secondary's shadow; the first vibration modes of the hub are near 100 Hz; a 20°C drop costs 2.6 lb of wire tension and nothing in collimation.

**Spider decision (2026-10-18): straight 4-vane, 0.020" (0.5 mm) stainless vanes 1.5" tall, anchored on the four posts between the rings (not on blocks above the ring), hub = holder top plate just under the upper ring.** Modelled against the alternatives with the secondary's real mass and lever: quad 0.012 mm of focal-point drift horizon to zenith on its own and 0.02 mm with the cage (0.08 mm when it was drawn on the tower blocks above the ring; anchoring on the posts shortens the hub and puts the pull on beams bolted to both rings); wire spider v2 0.05 / 0.12 mm; Destiny curved with a 3/4" stalk about 0.3 mm. The quad also obstructs 0.52 in² of vane against 1.2 in² for the wires and 1.3 in² for the Destiny, and it is the simplest to build and to collimate. Four spikes. The wire spider and the Destiny stay in the model as drawn alternatives; the extension blocks are wire-spider parts only. Secondary: 3.5" (see Optical design). Coma corrector: Explore Scientific HR (about $200 on sale) rather than the $577 Paracorr 2; L = 11.9" suits either.

## Collimation hold: model results

&#91;embedded content: cage\_fe.py, 2026-10-18 · 7 configurations, each swept 0–90° altitude\]

The number is how far the primary's focus moves across the eyepiece between the horizon and the zenith, with the truss and mirror box taken as rigid. Collimating at 45° halves what you see at either end. The spider change does most of the work; the ring change matters because the hub's position depends on eight anchor points spread round the cage, so any out-of-plane flexure of the rings tilts the secondary. Diagonal braces were tried and made it worse: they stiffened some anchors and not others. Thicker rings help evenly.

## Back focus: Feather Touch and Paracorr

The focuser is the FTF2015BCR. Starlight's page for the [FTF2015BCR](https://www.starlightinstruments.com/product/ftf2015bcr-feather-touch-rotatable-2-0-diameter-dual-speed-1-5-draw-tube-travel-brake-and-compression-ring/) gives 1.4" racked in and 3.0" racked out from the mounting face (1.5" travel), 1.55" of drawtube below the face when racked in, and 3 lb. TeleVue's [Paracorr Type 2 manual](https://www.manualsdir.com/manuals/365275/tele-vue-vip-2010-paracorr-type-2.html) says the corrector needs "about 3/4" focuser in-travel compared to using the eyepiece alone". At f/3.9 the Paracorr lives in the focuser, so its case is the one to centre: **L = 11.9"** (secondary centre to focus), which is now in the model. With the mounting face 9.0" from the axis that puts the focal plane 2.9" above the face.

| Case (L = 11.9") | Drawtube top above the mounting face | Reachable with the FTF2015 (1.4–3.0")? | Drawtube bottom from the axis (beam edge 8.0") |
| --- | --- | --- | --- |
| Paracorr + any eyepiece set by its chart | 2.15" (mid-travel) | Yes, 0.75" margin each way | 8.25", clear |
| Eyepiece alone, field stop at the shoulder | 2.90" | Yes, 0.1" from the out-stop | 9.0", clear |
| Eyepiece alone, field stop 0.5" below the shoulder (31 Nagler class) | 3.40" | No; needs a 1/2" extension | — |
| Fully racked in (not a focus position) | 1.40" | — | 7.45", 0.55" into the beam edge; harmless but do not observe there |

Moving the secondary 0.5" toward the primary costs a little illumination: the 3.1" secondary's fully illuminated spot shrinks from 0.22" to 0.05", about 90% at 8 mm off axis and about 72% at 21 mm, still fine for visual use. So the secondary is now 3.5": 0.45" fully illuminated, about 85% at 21 mm, at the price of a 22% obstruction (4.8% by area), which is not visible at the eyepiece. The Paracorr's 1.15× also means a 31 Nagler's 42 mm field stop only uses 36.5 mm of the native field, which is better illuminated.

## Collimation error budget

The cage and spider now use about a quarter of the 0.5 mm coma budget over the full altitude range, which leaves room for the parts not yet designed. The truss apex connectors are the biggest unknown and the usual place a truss Dob loses collimation.

| Source | Horizon to zenith, mm | Basis |
| --- | --- | --- |
| Wire spider v2 on 3/8" rings (cage + spider together) | 0.12 | cage\_fe.py |
| Focuser board flexure | < 0.02 | 1/4" plate, 6 lb at 3.5", 0.1 mrad |
| Thermal, 20°C drop | \~0 | wire tension falls 2.6 lb; geometry unchanged |
| Truss pole pairs and apex connectors | not yet modelled; target ≤ 0.2 | needs the connector design and pole clamps |
| Mirror cell and primary tilt | not yet modelled; target ≤ 0.1 | 18-point cell, DobStuff or new |
| Total | ≤ 0.45 target | collimate at 45° and the visible error halves |

Two measures keep the budget honest once the parts exist: a laser or Barlowed laser check at 0°, 45° and 90° after assembly, written down in mm at the focal plane, and a repeat after the cage has been off and on the truss three times.

## Truss design review

Verdict: the poles are fine as drawn; the layout should widen, and the joints are the whole game. A frame model of the six poles (`truss_fe.py`: cage as a rigid 17.3 lb body with the eyepiece outboard, box rigid, gravity swept 0–90°) gives the primary's focus drift across the eyepiece:

| Configuration | Drift horizon to zenith, mm | Lateral mode, Hz |
| --- | --- | --- |
| Narrow pairs (bases ±30° from each apex), 1" × 0.058" 6061, ideal joints | 0.089 | 57 |
| **Wide pairs (bases ±60°, shared sockets: an octahedron), same poles, ideal joints** | **0.046** | 86 |
| Wide pairs, 1" × 0.062" carbon fibre | 0.028 | 108 |
| Wide pairs, 1.25" × 0.058" 6061 | 0.037 | 96 |
| Wide pairs, aluminium, base joints 50,000 lb/in each | 0.129 | 53 |
| Wide pairs, aluminium, base joints 20,000 lb/in | 0.249 | 38 |
| Wide pairs, aluminium, base joints 5,000 lb/in (a pole in a loose hole) | 0.79 | 22 |

Findings, ranked:

| # | Finding | Fix (status) |
| --- | --- | --- |
| 1 | **Joint stiffness, not pole stiffness, sets the result.** Going from ideal joints to 20,000 lb/in costs 5×; any play at all is worse: 0.002" of radial play in a 1" socket lets a pole tilt 2 mrad and moves the cage 1.4 mm. | Zero-play seats: each pole end gets a bonded 6061 plug ending in a 60° cone; the socket block has a matching countersink; a 1/4-20 knob through the block side presses a brass pad on the plug's shank above the cone. The cone locates (repeatable to about 0.001"), the knob only keeps it seated when the pole goes into tension at low altitude. |
| 2 | The ±30° pair layout has a 10" base per triangle. Widening to ±60° makes neighbouring pairs share a socket, closes the triangulation (an octahedron) and doubles the stiffness for the same six poles. Still three pre-joined pairs to carry. | Wide layout chosen; viewer default (done). Pole length 30.0" instead of 28.8". The pairs are 30" × 18" triangles; they stack flat in the car. |
| 3 | Pole section is a second-order choice: 7/8" to 1-1/4" aluminium spans 0.10 to 0.07 mm with ideal joints. | Keep 1" × 0.058" 6061-T6 (0.5 lb each, clampable, cheap). Carbon fibre is a later upgrade: 1.5 lb lighter at the far end and no focus drift with temperature (aluminium: 0.35 mm of focus shift over a 20°C night, i.e. one refocus). |
| 4 | Apex joint: the pair block was a concept. | Pair block: 6061, two compound-angle bores (one wedge fixture serves all six bores: 11.2° radial lean, 16.4° tangential lean), poles' plugs threaded 1/4-20 into them; a 60° cone boss on top into a socket block under the lower ring, one 1/4-20 knob down through the ring. Three knobs. |
| 5 | Base blocks sit on the mirror cage's 18 mm plywood top ring: the ring's local flex becomes joint flex. | Base blocks 3" × 2" × 1.25" 6061, each with two cone sockets, through-bolted with three 1/4-20 to the ring and placed over the side panels where possible. To be checked in the mirror box review; an aluminium plate ring on top of the ply is the fallback. |
| 6 | Buckling, strength, vibration are all far inside limits: Euler load 2,200 lb per pole against under 40 lb; first lateral mode 50–90 Hz with good joints. | None. |
| 7 | Thermal: a 1°C difference between sunlit and shaded poles tilts the cage 35 µrad, 0.03 mm at the focal plane. | None, beyond the shroud. |
| 8 | Cable trunk from the cage: taped to a pole it is a snag and a shadow in the shroud. | Run the USB3 and 12 V trunk inside one pole (0.88" bore), out through a slot in the plug at each end, or along a pole under the shroud. |

Setup: pairs into the three double sockets (six knobs), cage onto the three pair blocks (three knobs); the box points up, sockets at 27" and pair blocks at 55" above the ground. Pole lengths matched to ±0.01" by the plugs, which also carry the heater and finder wiring if wanted.

Error budget after this review: cage with quad spider 0.02 mm, truss with cone joints about 0.09 mm (ideal 0.05, allowing 100,000 lb/in joints), mirror cell not yet modelled; total so far 0.11 mm of the 0.5 mm.

## Pole attach and detach

Nothing is tooled: nine knobs, three pairs, one cage. Transport state: mirror cage nested in the rocker (19.8" tall), the upper cage on its own (20.5" × 10"), three pole pairs stacked flat (31" × 18" triangles, 1" thick).

1. Rocker and mirror cage set down, bearings on, tube pointing up. The three socket blocks on the mirror cage's top ring are at about 27" above the ground.
2. Each pair is permanently joined at its top by its pair block. Lower a pair so its two cone-ended plugs drop into two sockets (one in each of two neighbouring blocks); the cones self-centre. Turn the two side knobs finger-tight. Repeat for the other two pairs: six knobs. The pairs stand on their own.
3. Lift the upper cage (about 17 lb) onto the three pair blocks: each block's cone boss enters a socket under the lower ring. Drop a knob through the ring into each boss and turn it down: three knobs. The cage is now located to about 0.001" at each point, so collimation should return within a fraction of the tolerance; check with the laser the first few nights and then only when it drifts.
4. Shroud on, Velcro at the lower ring and the mirror cage. Plug the trunk cable into the cage hub.

Take-down is the reverse; the trunk cable, if it runs inside a pole, stays with that pair. Pole lengths are set by the plugs, so a pair is never the wrong length; the pairs are interchangeable because all six sockets share one angle.

## Mirror box and cell review

The mirror is heavier than assumed: Hubble Optics lists the [16" f/4 sandwich](https://hubble-optics.com/mirrors) at 406 mm, about 42 mm thick and about 10.5 kg (23 lb), and their own [UL16](https://www.hubble-optics.com/UL16) carries it on a 6-point flotation cell with a sling. With 23 lb at the bottom the balance re-solves to the mirror face 14.6" below the axis (was 16.0"), nested height 19.8", eyepiece 59.8" at zenith, tube 81 lb. Model and viewer updated.

The primary's own tolerance: its axis must cross the focal plane within 0.5 mm, which at 62.4" is a tilt of 0.32 mrad. The cell and box together have to hold about 0.1 mrad over the altitude range to leave room for the rest.

| # | Finding | Fix |
| --- | --- | --- |
| 1 | **Edge support stretch is a collimation term.** A 1/8" Kevlar sling stretches about 0.12 mm under the 23 lb mirror at the horizon and nothing at the zenith, and the mirror moves with it: 0.12 mm of error, a quarter of the budget. A 1/16" steel cable is worse (0.24 mm) because its cross-section is smaller. | The DobStuff cell bonds the mirror to its nine pads with silicone dabs (to confirm from a photo of the back), so there is no sling: the dabs carry the side load in shear, about 0.12 mm of sag for nine 3/4" dabs 1/8" thick, elastic and repeatable, stiffer in the cold. Keep it; do not add a sling to a bonded mirror. If the mirror is ever re-mounted, a 1/2" × 0.010" stainless strap at the centre-of-gravity plane is the alternative (about 0.05 mm). |
| 2 | Spring-loaded collimation bolts let the cell move on the springs as gravity rotates; at 23 lb plus cell the springs must carry 28 lb at the horizon. | Push-pull collimation: three 5/16-24 bolts (0.042" per turn; 1/16 turn on a 6.5" radius is 0.07 mrad) with locking pull screws, no springs. Brass knobs on the back. |
| 3 | The cell is the DobStuff 9-point non-flotation cell (nine fixed pads, no pivoting triangles, per the kit invoice). Fixed pads do not share the load, so a low pad carries nothing; for a stiff sandwich that is acceptable (Hubble Optics uses 6 points) as long as the pads are coplanar. | Keep the cell. With the mirror bonded, the pads are set by the bond and need no truing; check that every dab is attached and nothing is glued at the mirror's edge. Silicone creeps over years, which shows as slow collimation drift: re-collimate, not redesign. Collimation hardware per item 2. |
| 4 | **Socket blocks on a plywood ring span.** Two of the three truss sockets (60° and 300°) land on the top ring 2.5" beyond the side-panel edges. On an unsupported 18 mm ring span a 40 lb pole reaction moves the socket about 0.1 mm, which the truss turns into about 0.17 mm at the eyepiece. | Nick's photo of the lower cage shows the real construction: three continuous aluminium tubes (about 1.25") through a thick bottom ring and two thin plywood rings, cell on the bottom ring, bearings on side plates. So: cut the tubes just above the cage's top ring and put the three socket blocks on the tube tops, each with a turned plug into the tube bore and a bolt through the ring. The pole loads go straight down the tubes; no plate, no doubler. Rotate the truss pattern to match the tubes' angle to the bearings. Racking of the three-tube cage: test with the scope horizontal (push the top ring, watch a laser); gusset tube-to-bottom-ring only if it moves. |
| 5 | Box stiffness between sockets and bearings: gravity loads the side panels in their own plane (stiff) at every altitude; the D-bearings bolt over the panels from the axis down 14", so the top ring sits 1" above a rigid zone. | None needed beyond item 4. The panels' out-of-plane softness is only loaded by the pole reactions' X components, which the posts carry. |
| 6 | Mirror lateral position along the altitude axis (X) has no restraint but friction on the pads. | No gravity component ever acts along X, so it stays put; a pair of nylon stops with 0.5 mm clearance at the ±X edges guards against transport knocks. |
| 7 | Cooling: the sandwich cools fast and needs no fan; a fan still helps the boundary layer. | One 80 mm fan behind the cell centre, Pegasus-controlled, on a 15° tilt so it blows across the face and not into it. |

From the DobStuff kit photos: the cell is a triangular 3/4" plate with the nine pads at the corners of three pencilled triangles and three cooling holes, hung on three three-lobe knobs through the bottom ring (spring-loaded bolts, so item 2 applies). Still to measure: tube OD, the three tubes' angle relative to the bearings, the spacing of the two upper rings, how the tubes are fixed in the rings, and silicone dabs or pads on the cell.

## Bearings and drives review

Verdict: the ratios and motors are right for the job; two layout changes make the drives slip-free and keep every cable off the azimuth axis. Both are now in the model and viewer (v17).

|  | Altitude | Azimuth |
| --- | --- | --- |
| Drive | GT2 timing belt (9 mm) glued teeth-out round the drive bearing's arc, 20T pinion (0.5" pitch dia) on a 2:1 stage (16:32) from the gearbox. Slip-free like a rack, no anchors or drum, essentially no mesh backlash with the pinion sprung into the belt. Alternative if ever wanted: a 1/16" cable in a rim groove on a 1.25" drum | GT2 belt glued round the rim of a new 30" × 2" plywood ring on the ground board, cut on the AltMill to a whole number of teeth (480 teeth: 29.9" ring diameter), 20T pinion on a 2:1 stage. Motor and pinion hang from the rocker's edge, so the rocker carries everything and nothing crosses the axis; continuous rotation, no roller preload |
| Motor | GM9413, 19.7:1, about 70 oz-in continuous (confirm from the label) | GM9213, 19.7:1, about 47 oz-in (the GM9213-2 lists 33 N·cm, 129 rpm at 12 V) |
| External ratio | 56 × 2 = 112:1 | 60 × 2 = 120:1 |
| Torque at the axis | about 440 in-lb against about 230 needed (pads at 0.12 friction plus a 60 in-lb eyepiece imbalance): 1.9× | about 350 in-lb against about 180 needed: 1.9× (the old 3:1 belt gave 1.5×) |
| Slew | 1.8 rpm, about 11°/s | 1.7 rpm, about 10°/s |
| Motor-encoder resolution | 0.29" per count (4.4 M counts per rev) | 0.27" per count |
| Telescope encoder | Magnetic tape on the bearing rim, read head on the rocker wall | Magnetic tape on the lower band of the ground ring's rim (belt on the upper band), read head on the rocker beside the pinion |

Findings:

| # | Finding | Fix (status) |
| --- | --- | --- |
| 1 | A friction capstan on an Ebony Star rim has a friction coefficient near 0.2; holding 35 lb of rim force would need a 150 lb preload pressing the bearing off its pads. | Belt-on-rim on both axes (done in the model, v20), the DIY-SiTech form of the gear-and-rack Ron's 16" DobStuff GoTo uses: a GT2 belt glued teeth-out on the rim and a sprung pinion. Rim force at full torque about 31 lb altitude, 23 lb azimuth, well inside a 9 mm GT2 belt's rating. |
| 2 | The azimuth motor was drawn on the ground board driving the rocker's disc, so its cable and the azimuth read head's cable would cross the azimuth axis. | Motor on the rocker, roller on a fixed ground ring; tape on the ring, head on the rocker (done). Belt 4:1 for a 1.9× torque margin. Eyepiece height rises 0.75" to 60.6". |
| 3 | A groove on the bearing rim was reserved for the trunk cable. | Not needed: the D-bearing's straight edge passes through the altitude axis, so the trunk crosses there with a short twist loop and never changes length. The rim band now carries the drive belt. |
| 4 | Gearbox backlash (about 1° at the output) sits between the motor encoder and the load, so a balanced tube can wander inside it. | Keep a deliberate 20–30 in-lb mirror-end imbalance so the gear train stays loaded one way, and let the tape encoders close the position loop (SiTech telescope-encoder inputs, Nexus for the sky model). |
| 5 | Optical tape encoders need the read head within about 0.1 mm of the tape; a bearing floating on PTFE pads will not hold that. | Magnetic tape (SiTech or RLS LM10 kits, gap tolerance about 0.5 mm) with the head on a sprung guide shoe riding the rim. At 4,000 counts per inch: 3.7" per count on the 14" bearing, 2.4" on the 30" ring. |
| 6 | Rim eccentricity reads as a pointing error: 0.5 mm off-centre on a 14" radius is 5' peak. | Cut each bearing's arc and its dowel holes in one AltMill setup; two 1/4" dowels and four bolts locate it on the box. Plate solving absorbs what is left. |
| 7 | PTFE pads at ±40° raise pad load and friction by 1/cos. | ±35°, 1.5" virgin PTFE on Ebony Star; the belt pinion's spring load is a few pounds and adds nothing to the pads. |
| 8 | Azimuth pivot: the tape needs the rocker to turn about a fixed centre. | 1/2" stainless pivot bolt in a flanged bronze bushing in the ground board hub; three PTFE pads on the ground ring at 12.5" radius. |

Siderial tracking turns the altitude motor at about 1.5 rpm (51 counts per second), which is where a low-cog motor like the GM9413 earns its keep; the LO-COG series is the right family for this.

**Altitude bearings, construction:** both sides two layers of 3/4" Baltic birch laminated (1.5", about 4 lb each, so the tube stays balanced), cut on the AltMill in one setup: 14" arc, inner cut-out, four 1/4-20 bolt holes and two 1/4" dowel holes, so the rim is concentric with the mounting pattern to about 0.1 mm and the detachable bearings go back to the same place. Drive-side rim across the 1.5" edge: 0.6" Ebony Star band for the PTFE pads, 0.4" band for the glued GT2 belt, 0.3" band epoxy-sealed and sanded flat for the magnetic tape. Plain side: Ebony Star across the edge. Not aluminium: a plate edge is too narrow for the pads and would need a band anyway at three times the weight.

## Open measurements and decisions

- [ ] Mirror cage: angle of the three tube holes relative to the bearings, tube OD, ring OD/ID, height bottom ring to top ring
- [ ] Cell: silicone-bonded or loose on pads; collimation bolt thread
- [ ] Altitude bearing radius, and where the pads sit
- [ ] Rocker width and ground board size
- [ ] Feather Touch FTF2015 base bolt circle and hole size
- [ ] Secondary blank thickness once ordered (3.5")
- [ ] Starting force on each axis (luggage scale), to confirm motor assignment
- [ ] Magnetic tape and read-head model; confirm the SiTech encoder inputs
- [ ] Coma corrector: Explore Scientific HR (chosen on price) or Paracorr 2
- [ ] Imaging (option, not in this build): an equatorial platform under the ground board would be needed for long exposures
