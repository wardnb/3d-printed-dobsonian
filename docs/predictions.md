# Predictions register: what the models say, and how to check them

Every number the simulations have produced that a measurement on the real scope can confirm or refute. Fill the
**Measured** column as tests happen (date + value + how); a prediction that misses by more than its stated uncertainty is a
reason to look at the model's assumptions, listed with each item. Units: focal-plane motion in mm (0.5 mm is the coma budget
for the whole scope), angles in arcsec (") or arcmin (′), stiffness in lb/in. "0→90" means the change as the tube goes from the
horizon to the zenith. Last model run: 2026-11-07.

Conventions for the tests: collimate at 45°, then read at 15°, 45° and 90°; a Barlowed laser or a Cheshire with a reticle
eyepiece gives focal-plane shift directly (1 mm at the focal plane of this f/3.9 ≈ 0.4° of secondary tilt-equivalent — read
the return spot on the collimator's target in mm). A dial indicator on the cage ring against a fixed reference measures ring
motion; a star drift or plate-solve series measures pointing.

## 1. Collimation drift (focal-plane motion of the primary's focus vs the eyepiece)

| ID | Prediction | Value | Assumptions / notes | Model | How to measure | Measured |
| --- | --- | --- | --- | --- | --- | --- |
| C1 | Upper cage v3 + quad spider, drift 0→90 | 0.012 mm (0.009 after collimating at 45°); focuser-board tilt 0.05 mrad at the horizon | Rings 1/4" slotted 6061, four 3/4" posts, six 5/8 × 0.058 inverted-V diagonals, finder cradle at 150°; cage rigidly supported at the pair blocks; focuser load 3 lb + eyepiece | `cage_fe.py` | Laser in the focuser, cage on a rigid stand (or on the finished truss with the truss term subtracted); return spot at 0/45/90 | |
| C2 | Same cage, old 3/8" post-only design (for reference) | 0.024 mm | | `cage_fe.py tri` | n/a | |
| C3 | Truss alone (six carbon poles, ideal joints), drift 0→90 | 0.038 mm (0.027 after collimating at 45°) with the designed 1.25 × 0.062 tube; 0.032 after 45° with the bought 1.24 × 0.058 tube; cage sag at the horizon 0.032 mm | Rock West 45562: 1.24 OD × 0.058 wall, E 13.3 Msi, poles 37.30/37.35" node to node; cage and box rigid | `truss_fe.py` | Laser at 0/45/90 with the cage mounted; dial indicator on the cage ring vs a floor reference | |
| C4 | Truss with 20,000 lb/in base joints (what a clamp block would do) | 0.29 mm drift (0.21 after 45°); 0.92 mm at 5,000 lb/in | Shows the joints dominate: this is why the cones are preloaded with drawbolts | `truss_fe.py` | If measured truss drift is ≫ C3, suspect joint play; test by pushing the cage sideways and watching the indicator return | |
| C5 | Truss with preloaded cone joints (≥ 50,000 lb/in) | ≤ 0.03–0.05 mm | Drawbolt pulled 80–150 lb by hand; plugs bonded with zero play | `mcage_fe.py` sweep of `sock_k` | Same as C3 | |
| C6 | Mirror box as built (ply, spacers bolted, stubs pinned at both boards), extra drift 0→90 | 0.012–0.016 mm over the rigid-box truss (0.054 total vs 0.038 rigid; 0.035 with both-board pins) | Ply E 1.2 Msi; stubs pinned axially at the top ring and mirror board | `mcage_fe.py` | Laser with everything assembled minus the cell term (C6 is the remainder after C1 + C3) | |
| C7 | Mirror box with the cell studs clocked away from the stubs (60° off) | 0.17–0.23 mm | Shows why the new cell's collimation bolts sit next to the stubs at 90/210/330° | `mcage_fe.py cell_angles` | n/a (design choice) | |
| C8 | Primary mirror lateral shift at the horizon in the new cell | 0.008 mm | Two edge gussets at 225/315°, 74,000 lb/in each, set touching; 23 lb mirror | `cell.py report()` | Dial indicator on the mirror's edge (through the box) horizon vs zenith; was 0.2–0.8 mm possible on the old spring-knob cell | |
| C9 | Collimation-bolt bushing play at the focal plane | ≤ 0.05 mm | 5/16 bolt in SAE 841 bushing, 0.001–0.002" clearance, r 6.5" bolt circle | geometry | Push the cell sideways with the box horizontal; indicator on the mirror edge | |
| C10 | Whole-scope drift 0→90 | ≈ 0.2–0.25 mm (sum of C1 + C5 + C6 + C8 + C9 with margins) | | budget | Barlowed laser at 15/45/90 after collimating at 45°; repeat after three cage off/on cycles | |
| C11 | Secondary mirror tilt from spider vane thermal change, 20 °C drop | ≈ 0 (vane tension falls 2.6 lb, geometry unchanged) | 0.020" stainless vanes, 4 studs | hand calc | Laser spot at dusk vs 2 h later, tube stationary | |
| C13 | Truss lateral natural frequency (1 lb at the cage CG) | 93 Hz carbon; 74 Hz if 1.25" Al; 35 Hz with 20,000 lb/in joints | Cage and box rigid | `truss_fe.py` | Rap the cage and time the wobble on a star at high power (or phone accelerometer on the cage); ≥ 50 Hz means the joints are doing their job | |
| C12 | Hub sag (secondary centre, gravity) at 0° / 90° | 0.008 / 0.009 mm (v3; the v2 post-only cage was 0.07–0.08) | | `cage_fe.py` | Not separately measurable; included in C1 | |

## 2. Finder (Waypoint plate-solving guide scope) pointing

| ID | Prediction | Value | Assumptions / notes | Model | How to measure | Measured |
| --- | --- | --- | --- | --- | --- | --- |
| F1 | Waypoint tilt relative to the main axis, 0→90, adjustable cradle at 150° | 0.70′ (≈ 0.5′ after syncing at 45°) | 1/4 × 1.0" bar on 1/2" angle blocks, 1/4" tilt plate, 515 g finder | `cage_fe.py finder` | Plate-solve the Waypoint and the main camera (or a centred star) at 15/45/90; difference of the two solved centres | |
| F2 | Same with a riser on the upper ring (rejected) | 2.2′ | Twists the 1/4" ring | `cage_fe.py finder` | n/a | |

## 3. Altitude bearing and D-to-box joint (`bearing_fe.py`, plane-stress FE of the D and the box side)

| ID | Prediction | Value | Assumptions / notes | Model | How to measure | Measured |
| --- | --- | --- | --- | --- | --- | --- |
| B1 | Tube windup vs the alt pinion per in-lb of drive torque, 15° / 45° / 90°, bolts tight | 0.058 / 0.021 / 0.008 "/in-lb | Box side = 3" strip + back wing; 2 dowels + 6 bolts; ply E 1.2 Msi in-plane | `bearing_fe.py` wing_clamped | Lock the motor (or hold the pinion), hang 5 lb at the eyepiece (≈ 320 in-lb) and read the eyepiece/laser shift: expect ~19" at 15°, ~7" at 45° | |
| B2 | Same with bolts slipped (dowels only) | 0.133 / 0.059 / 0.045 "/in-lb | | `bearing_fe.py` wing_slipped | If B1 reads ≈ 2× prediction, the bolts have slipped: re-torque | |
| B3 | Tube rotation vs pinion from gravity alone over the 15→90 sweep (repeatable, pointing-model term) | 25" | | `bearing_fe.py` | Shows as a smooth altitude-dependent pointing term in the SiTech model | |
| B4 | Rim read-head sees gravity term 15→90 | 3.3" → −1.1" (≈ 4" range) | | `bearing_fe.py` | Plate-solve vs tape encoder over the sweep (needs the tape) | |
| B5 | Fastener load at 1 g / 3 g jolt (max single bolt or dowel) | 49 lb / 146 lb | | `bearing_fe.py` | n/a; the 3 g case is why the 2-bolt design was dropped (403 lb) | |
| B6 | Point loads from rollers vs 0.8" pads change B1 | < 1% | | `bearing_fe.py` 2026-11-07 run | n/a | |
| B7 | Differential rim runout → tube tilt about vertical | 95" per 0.010" | Smooth in altitude; pointing model absorbs it | `roller_study.py` | Dial indicator on each rim while the tube sweeps; compare to the pointing-model residual | |

## 4. Rollers, friction and drives (`roller_study.py`, `drive.py`)

| ID | Prediction | Value | Assumptions / notes | Model | How to measure | Measured |
| --- | --- | --- | --- | --- | --- | --- |
| R1 | Alt friction torque | ~11 in-lb (was ~145 with PTFE/Ebony Star at μ 0.12) | Seal drag 10 N·mm per 2RS bearing ASSUMED (ZZ ~1/5); tab rub on a 2° slope | `roller_study.py` | Luggage scale at the eyepiece (63.6" from the axis): expect ~0.2 lb to start the tube moving when balanced; the old design would have needed ~2.3 lb | |
| R2 | Az friction torque | ~7 in-lb (was ~183) | Four rollers, 26 lb each; rocker 28 lb ASSUMED | `roller_study.py` | Luggage scale at the rocker edge (r 13.7"): expect ~0.5 lb to start | |
| R3 | Alt drive torque at the rim | 36 in-lb (friction + 25 in-lb imbalance) → 5 oz-in at the gearbox, 8.8× margin | Imbalance 25 in-lb ASSUMED; 45 oz-in continuous rating from a parts listing | `roller_study.py` | Motor current while tracking and slewing (Kt ≈ 5.6 oz-in/A → ~0.06 A at the output torque above, through 19.7:1 and 2:1) | |
| R4 | Az drive torque | ~17 in-lb (with 10 in-lb wind ASSUMED) → 20× margin | | `roller_study.py` | Motor current | |
| R5 | Alt train stays preloaded (no backlash crossing at transit) | friction 11 < imbalance 25 | Requires a deliberate 20–30 in-lb nose-heavy bias | `roller_study.py` | Track a star through transit at high power; no jump expected. With the bias removed (balanced), expect a ~32" jump | |
| R6 | Gearbox backlash on the sky | ~32" (≈ 1° at the gearbox output / 112) | Pittman GM9413 spec backlash ASSUMED ~1° | ratio | Reverse the alt drive by hand-controller and measure the dead band in motor counts (0.28"/count) | |
| R7 | Slew rate at 24 V | 12–13°/s both axes | 284 rpm no-load at the gearbox output, 2:1 belt, 112:1 / 120:1 rim ratio | motor data | Stopwatch a 90° slew | |
| R8 | Roller contact stress | 75 MPa alt (130 at 3 g), 82 MPa az | 6061 yield 276 MPa | `roller_study.py` | Inspect the strips after the first season for tracks or brinelling; none expected | |
| R9 | Rim strip support stiffness under a roller | ~120,000 lb/in | Birch in-plane E 7 GPa ASSUMED | `roller_study.py` | Not directly; shows up in B1 if far off | |
| R10 | Pinion spring preload needed against ratcheting | ~6 lb (19 lb spring fitted) | Rim force ~3 lb | `drive.py` | Slew against the hand pushing the tube: the pinion should not skip teeth | |
| R11 | Brake hold with the pinion lifted | ~100 in-lb alt (1.6 lb at the eyepiece), ~120 in-lb az | Shoe μ 0.5 ASSUMED, 15–19 lb spring | `roller_study.py` | Luggage scale at the eyepiece with the brake on | |
| R12 | Tube weight / balance | 74.3 lb; balanced with no counterweight at mirror face 12.5" below the axis; eyepiece 63.8" at zenith | Component weights from the model (box with mirror NOT yet weighed) | `dob_model.py` | Weigh the box with mirror, one bearing, the cage; check the tube balances with the lightest eyepiece | |

## 5. Mirror support figure (`cell_support_fe.py`, Morley plate FE)

| ID | Prediction | Value | Assumptions / notes | Model | How to measure | Measured |
| --- | --- | --- | --- | --- | --- | --- |
| M1 | Surface error of the 9-point flotation layout, zenith | 1.0 nm RMS / 4.6 nm P-V (power removed) | Plate rigidity D ≈ 4e5 N·m ASSUMED for the sandwich; equal pad loads; pads at 0.431 R and 0.670 R | `cell_support_fe.py` | Star test / Roddier at the zenith vs 45°; any trefoil or astigmatism change is support, not figure | |
| M2 | 3-point support, for comparison | 8.3 nm RMS | | `cell_support_fe.py` | n/a | |
| M3 | Collimation bolt sensitivity | 1/16 turn ≈ 0.4 mm at focus | 5/16-24 thread, r 6.5" | geometry | Count turns between two laser readings | |

## 6. Optics and focus (`dob_model.py checks.coma_corrector_fit`)

| ID | Prediction | Value | Assumptions / notes | Model | How to measure | Measured |
| --- | --- | --- | --- | --- | --- | --- |
| O1 | ES HR corrector reaches focus at L = 12.5" | spare in-travel 12–31 mm depending on the unpublished focal-plane height (57–76 mm bracketed) | FL 62.4" (f/3.9) from Hubble's listing, not the test report | `dob_model.py` | Focuser position at focus with the ES + Panorama 28; compare to the model's 1.4" + spare | |
| O2 | Corrector nose into the incoming beam | ≤ 0.46" (≈ 0.6% light) | | `dob_model.py` | Look down the tube from the eyepiece side at 90°; none visible expected | |
| O3 | Fully illuminated field with the 3.5" secondary | 0.30" diameter | | `dob_model.py` | Flat-frame vignetting with the ASI533 | |
| O4 | Obstruction | 21.9% by diameter | | `dob_model.py` | n/a | |
| O5 | Paracorr 2 / no corrector needs a 1" extension | 4 mm spare without, 29 mm with | | `dob_model.py` | Only if a Paracorr is used | |

## 7. Pointing and tracking

| ID | Prediction | Value | Assumptions / notes | Model | How to measure | Measured |
| --- | --- | --- | --- | --- | --- | --- |
| P1 | Motor-encoder resolution on the sky | 0.28"/count both axes | 500 CPR × 4 × 19.7 × 2 × 112 (alt) | ratio | SiTech reports counts; compare to a plate-solved slew | |
| P2 | Magnetic tape encoder | ~1.1"/count, ±6" cyclic error with a ~19′ period, ~2" hysteresis | AS5311-class head on 2 mm-pole tape | datasheet | Plate-solve series vs tape readings | |
| P3 | Lowest altitude with the front roller still under the rim | 15° | D chord offset 3.62" | `rocker.py` | Point at 15°; the rim must still cover the front roller | |
| P4 | Az pivot play effect | 69" per 0.005" of play | | `roller_study.py` | Push the rocker sideways with the brake on; plate-solve before/after | |

## 8. Weights and sizes the model carries (checked on the scale, not simulated)

| ID | Item | Model value | Measured |
| --- | --- | --- | --- |
| W1 | Upper cage metal (rings, posts, diagonals, board, rails) | 9.3 lb (12.2 lb with focuser, finder cradle, spider) | |
| W2 | Each D bearing (two 18 mm layers) | 6.6 lb | |
| W3 | New mirror cell | 4.9 lb | |
| W4 | Drive arm plates per axis | 0.43 lb | |
| W5 | Tube total (everything that tilts) | 74.3 lb | |
| W6 | Rocker (birch, drives, electronics) | 28 lb ASSUMED | |
| W7 | Rocker height / eyepiece height at zenith / nested transport height | 15.6" / 63.8" / 13.5" | |

## Known weaknesses of the models (where to expect the largest misses)

1. Every plywood modulus is assumed (1.2 Msi in-plane; 7 GPa edge-loaded under the roller strips). Birch varies ±20% and
   more across the grain, so the box (C6) and joint (B1) terms could be 30% off either way.
2. Joint stiffnesses are the biggest unknown in the whole budget: bonded cone plugs with drawbolt preload are modelled as ≥ 50,000 lb/in.
   If the truss drift (C3/C5) measures several times the prediction, the joints — not the poles — are the cause.
3. Friction numbers hang on seal drag (R1, R2) and μ (brake). A spin test of one R10 by hand settles the first; the luggage scale the rest.
4. The mirror's plate rigidity (M1) is a guess for a sandwich; the layout is forgiving (3-pt vs 9-pt differs 8×, so even a 2× error leaves margin).
5. Nothing dynamic has been modelled except the truss lateral mode (93 Hz with the carbon poles, 74 Hz with 1.25" aluminium, 35 Hz if the base joints were only 20,000 lb/in — so a rap on the cage is a cheap joint-stiffness test: a slow wobble means soft joints); damping time after a focuser touch is unknown.
6. Thermal: only the spider vanes were checked. Carbon poles (≈ 0 CTE) against the aluminium cage rings and the ply box will move
   focus with temperature by roughly the aluminium parts' expansion only (~0.1 mm per 10 °C over the 20" cage); not yet modelled.

## Recording a test

Put the result in the Measured column as `YYYY-MM-DD value (method)` and, if the model was wrong by more than the stated
assumptions allow, add a line to `docs/measurements.md` and a note in the Decisions table of `CLAUDE.md` saying which
assumption moved. Keep the model honest: change the input (ply E, seal drag, joint stiffness), re-run the script, and
re-export this register rather than editing a predicted number by hand.
