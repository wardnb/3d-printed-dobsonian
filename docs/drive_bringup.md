# Drive and electronics bring-up (2026-11-08)

Everything the drives need is either in hand (two Pittman gearmotors, SiTech Servo Controller II, Nexus DSC Pro, Pegasus
Pocket Powerbox) or cheap and on the `BUY` list (GT2 pulleys, belts, F608 bearings, shoulder bolts, springs). None of it
depends on the rocker or the birch, so the drive train can be proven on the bench now and the rocker gets a known-good
module bolted to it later. This file is the plan and the numbers; `drive.py` is the geometry.

## 1. Architecture

| Item | Where | Why |
| --- | --- | --- |
| SiTech Servo II | Rocker, plain wall (drawn as `electronics_box_sitech`, 2.4 × 8 × 5") | Both motors, both tape heads and the handpad are on the rocker, so no drive cable crosses either axis |
| Alt gearmotor (GM9413) | Rocker drive wall, on the alt arm | Pinion on the D's rim belt |
| Az gearmotor (GM9213) | Rocker floor edge, on the az arm | Pinion on the ground ring's rim belt; the ring is fixed, the motor goes round with the rocker |
| Mini PC (SiTechExe, ASCOM, plate solving) + USB hub | Rocker, same wall | USB to the SiTech, Waypoint camera, focuser if motorised |
| Pegasus Pocket Powerbox | Rocker | 12 V distribution + two dew outputs; it cuts out above ~14–14.5 V so it must see a 12 V bus, never 24 V |
| Battery | Rocker floor, front (under the box's swing, nothing to balance) | 12.8 V LiFePO4 20–30 Ah |
| 12 → 24 V boost, ≥ 6 A | Next to the SiTech | Motors are 24 V; the SiTech takes 11.5–28 V (Servo I spec, see §5). One battery, one boost for the SiTech alone |
| What crosses the altitude axis | Secondary heater, Waypoint USB + 12 V, cage dew strap | The USB3 + 12 V trunk at the D's straight edge (Wiring row in CLAUDE.md). The drives add nothing to it |

Bench alternative for stage 0–2: a 12 V bench supply. At 12 V the 24 V motors run at half speed (~140 rpm at the gearbox
output, ~6°/s slew) with full torque authority at our loads; that is enough to prove everything except the top slew rate.

## 2. SiTech numbers (from the model; confirm with ServoConfig's tick determination)

Motor encoder 500 CPR × 4 (quadrature) = **2,000 counts per motor rev**; gearbox nominal 19.7:1 but the true tooth ratio is
**19.658119658:1** (SiTech Setup Manual §2.3.4, GM9400 table: "19.7:1 … 19.658119658:1"; found 2026-11-08 evening, 0.21 % off
nominal = 11′ over a 90° slew if ignored) → **39,316.2 counts per gearbox output rev**.

| | Alt (`alt_ratio` 112.48 incl. 2:1) | Az (`az_ratio` 120.48 incl. 2:1) |
| --- | --- | --- |
| Rim radius / pinion pitch radius | (14.0 + 0.06) / 0.25 = 56.24 | (15.0 + 0.06) / 0.25 = 60.24 |
| Ticks per axis rev, 2:1 belt stage | 39,316.2 × 112.48 = **4,422,291** | 39,316.2 × 120.48 = **4,736,821** |
| Ticks per axis rev, 3:1 | 6,633,400 | 7,105,200 |
| Resolution (2:1) | 0.293"/tick (3.41 ticks/") | 0.274"/tick (3.66 ticks/") |
| Motor-encoder count rate at 12°/s slew (2:1) | 148 kHz | 158 kHz |
| Raw speed for 12°/s (ticks × dps × 0.09321) | 4.96 M | 5.31 M |

Cross-checked 2026-11-08 with SiTech's online Drive Calculator using the nominal 19.7 (4,431,712 / 4,746,912); with the exact 19.658119658 the calculator gives the values in the table. Enter the gearbox as the fraction 2300/117 if the calculator or ServoConfig takes fractions (2300/117 = 19.65812). The stage-2 test rim (R 12.19 + 0.06, 2:1): 39,316.2 × 98.0 = 3,853,000.

SiTech's own guidance (Servo I manual): 4–10 million ticks per rev is the good range, raw speed below ~6 M, motor
encoder inputs up to 248 kHz. Both ratios fit; 2:1 sits at the low end of the tick range, 3:1 in the middle. The belt
glued on the rim adds ~0.06" to the radius, which is in the ratio above; the real number comes from ServoConfig's tick
determination (slew a measured angle) or, later, from the tape encoders.

Motor at 24 V: ~5,600 rpm no-load → 187 kHz at the encoder, under the 248 kHz input limit. At 12 V, half of all rates.

Starting parameters (the Hubble UL SiTech quick-start values are a reasonable seed for a Dob of this size): PID P 15000,
I 2500, D 4000; acceleration 500 (raw); error limit 12,800; integral limit 22,000; current limit 2.4 A; output limit 100 %;
backlash 0 until the Backlash Help Tool is run. Pan 3′/s, guide 60"/s, slew 12°/s target (start at 2°/s on the bench).

## 3. Wiring

Both motors came with SiTech's own motor adapter boards (Hansen Motor 116-8224B-5M, photo 2026-11-08): a small PCB
on the encoder end with an 8-pin modular jack for the encoder (pads silkscreened GND, A, 5V, B) and a 2.1 mm barrel
jack for the motor (pads +, −). The GM9213's board is soldered to its 5-pin encoder header (white/orange/blue/green)
and motor leads (red/black); the GM9413's board has a six-wire lead and still has to go on the motor. SiTech's standard
motor cable mates with exactly this pair (modular plug + barrel plug) and runs to the Servo II's terminal blocks, so
two of those cables are the whole motor wiring.

Pittman encoder (HEDS-5500 family / Pittman "H" 500-line): header pin 1 ground, 2 index (unused), 3 channel A, 4 +5 V,
5 channel B; single-ended TTL, 85 mA at 5 V. Pin 1 is normally marked with a dot or square pad. Before first power,
verify on each board that 5 V and GND land on the right header pins (a swap there destroys the encoder); an A/B swap
only reverses the count and is fixed with the invert bit in ServoConfig.

Order of operations on first power (SiTech manual): all grounds to the battery negative first; white-striped lead is
positive; reversed polarity blows the fuse and can take components with it. Plug in ONE motor only for the first test.

### Servo II panel (photo 2026-11-08; silkscreen flaking, so recorded here; printable strip `docs/servo2/terminal_legend.pdf`)

Top edge, left to right: GUIDE (RJ) · POWER barrel (+ centre, rating worn, reads 12–28 V) · USB-B with COMM/DATA LED ·
RS232 (RJ) · HAND PAD (RJ). LEDs SLEW/PAN/GUIDE top left, a MOTOR STATUS LED under each motor block.
Bottom edge, four pluggable terminal blocks (5.08 mm), left to right:

| Block | Terminals |
| --- | --- |
| ALT/DEC INPUTS | +LIMIT · −LIMIT · HOME · PSYNC · AN IN · +5V · GND |
| AZM/R.A. INPUTS | +LIMIT · −LIMIT · HOME · PSYNC · AN IN · +5V · GND |
| ALT/DEC MOTORS | M.E. A · M.E. B · S.E. A · S.E. B · +5V · GND · MOT+ · MOT− |
| AZM/R.A. MOTORS | M.E. A · M.E. B · S.E. A · S.E. B · +5V · GND · MOT+ · MOT− |

M.E. = motor encoder, S.E. = scope encoder. A motor cable therefore lands on six screws of its block (A, B, +5V, GND,
MOT+, MOT−); the scope encoder for that axis shares the block's +5V/GND on S.E. A/B. Leads from a previous installation
were still in the terminals: check whether the matching motor cables came with the controller before buying.

## 4. Bench sequence

**Stage 0 — controller and motors, no mechanics (now).**
1. USB to the mini PC (or any Windows laptop) → ServoConfig communicates. Firmware version noted.
2. Measure both motors while they are on the bench: gearbox face (bolt circle, screw size, pilot boss), shaft diameter
   and length, body diameter and length, encoder pins. These replace the ASSUMED values in `drive.MOTOR_HOLES`,
   `FLANGE_SQ`, `MOTOR_R/L` and the plate B hole pattern.
3. One motor, 12 V supply, default parameters. Runaway → the LED blinks at 1 s: swap A/B (or invert in ServoConfig),
   not the motor leads if the handpad sense is right. Repeat for the second motor.
4. Enter the ticks per rev from §2, set slew to 2°/s, confirm a commanded 360° of the gearbox output is 360° (mark the
   shaft). Save to flash.

**Stage 0 results (2026-11-08):** ServoConfig 1.30 talks over USB; firmware **9.7** (current, no flash needed), serial 57447,
12.2 V bench supply, CPU 80 °F. GM9213 on the AZM/RA block (= protocol axis **Y**; ALT/DEC is **X**, per ServoConfig's
"Azimuth/RA YBits / Altitude/Dec XBits"): counts up with RIGHT, no inversion bits needed, holds position at error ±1 with
0.00–0.01 A, **0.03 A at 2°/s no-load**, even running; `Y<pos+39400>` from the Terminal Window turned the output shaft
one revolution to the eye (39,316 is exact; the 84-tick difference is 0.8° of shaft, below what a pen mark shows). Ticks per rev entered: az 4,746,912, alt 4,431,712 (nominal 19.7 — **to be corrected to 4,736,821 / 4,422,291** for the
true 19.658:1 gearbox; type without commas: the field keeps only the first digit otherwise); slew 2 DPS, pan 3 MPS, guide 60 SPS; PID 15000/1500/4000,
accel 1000, error limit 12,800, current limit 0.70 A, integral limit 22,000. ServoConfig's on-screen hand pad buttons
latch over USB: All-Stop or a second click stops them; commanding a channel with no motor (`X…` here) trips it to
MANUAL, cleared by Reset. GM9413 on the ALT/DEC block (axis X): board soldered, `X39400` = one output turn, no inversion needed, ~0.16 A start-up peak then the same as the other motor (at rest holding: az 0.04 A / alt 0.06 A, error 0, output ~40 = integrator bias against gearbox stiction, normal). The two motors are equivalent; assignment stays GM9413 alt / GM9213 az for cable reach. **Stage 0 complete 2026-11-08.**

**Stage 1 — one drive module, no rim.** Cut the four arm plates (1/4" 6061, from the centre drop of the cage-ring discs
in the cut plan) and assemble one module: jackshaft in the F608s, 20T pinion, 16T on the motor, 32T + 152 mm loop.
Run it in air: belt tracking, tension, pulley set-screw security, pinion runout. Swap to the 48T/170 mm set and keep
whichever gives the quieter belt; the ratio choice is otherwise made in stage 2.

**Stage 2 — the old DobStuff D bearing as a test rim.** Glue ~24" of 9 mm GT2 belt teeth-out on the old bearing's
running edge (R 12 3/16", bare ply, or on the Ebony Star if it is still bonded), bolt the bearing to a plywood scrap
that can turn on a 3/8" bolt through its axis, and clamp the module to the bench with its base plate so the pinion
meshes with the 19 lb spring preload. Ratio for this rim: 2 × (12.19 + 0.06) / 0.25 = 98.0 → 3,861,000 ticks/rev (2:1).
This is the test that matters:
- Preload: hang 20–30 lb at the rim's edge (the real imbalance is ~25 in-lb; at r 12" that is only ~2 lb, so start light)
  and drive both ways at slew and at sidereal; no ratcheting, no belt climbing.
- Backlash Help Tool → the number the gearbox actually has; it should be ≤ ~1° of gearbox output (≈ 32" on the sky).
- PID tune under this load with the manual's order (I = 0, P = 0, raise D to the edge of vibration, then P, then I).
- Tracking error readout ±1 tick while tracking.
- Clutch: throw the cam, confirm the pinion lifts ~3 mm clear, re-engage anywhere; the spring must drop it in without
  the belt jumping. Measure the real cam lift and spring force → `drive.LIFT`, `PRELOAD_LB`.
- Starting-force number for `docs/predictions.md` (the drive torque at the rim with the luggage scale).

**Stage 3 — az module** is the same module on the same test rim (the ring is only a bigger radius); nothing new to
prove except the vertical motor orientation.

**Stage 4 — az ring encoder** (the owned Astro Devices HD assembly) on the SiTech AZM S.E. inputs: set 311296 ticks, one turn of the disc by hand = ±311,296. No alt scope encoder (decision 2026-11-08, §5a).

Parts to add to the bench order beyond what `BUY` already lists: two SiTech motor cables (modular + barrel ends; or
flat 8-conductor + 2.1 mm barrel plugs to make them), 12 V bench supply ≥ 5 A if none on hand, USB-B cable, 3/8" bolt +
nylon washers for the test-rim pivot.

## 5. Open checks (answer from the Servo II manual before buying heads)

1. **Servo II input voltage and motor current.** The Servo I manual says 11.5–28 V, 2.4 A per motor, 4 A total; Astrofox
   says the Servo II doubles the motor amperage. Our motors need < 0.5 A at 24 V, so either is fine, but the boost
   converter is sized from this.
2. **Scope-encoder input limits.** Servo I: telescope encoder inputs up to 25 kHz and "about 500,000" counts per rev
   before missed ticks. A 2 mm-pole magnetic tape at r 14" read by an AS5311-class head gives ~1.2 M counts per rev and
   ~39 kHz at 12°/s, over both limits on a Servo I; the Servo II advertises "extremely high speed" encoder inputs but no
   number. If the Servo II is still ~25 kHz / 500 k, the right answer is the Astro Devices HD kit Nick already owns
   (~311,296 steps/rev = 4.2"/step, 10 kHz at 12°/s), moved from the Nexus to the SiTech's scope-encoder inputs if its
   outputs are 5 V quadrature (to confirm from Astro Devices' sensor spec), and the tape idea is dropped. Position-only
   duty (pointing, slip recovery) does not need better than 4".
3. **Servo II connector pinouts** (motor, encoder, scope encoders, handpad): from the manual, written into this file
   when known.

### 5a. Scope encoders: decision 2026-11-08 — none on alt, the owned 8192 shaft encoder on az, plate solving for position

Every encoder on this mount is incremental (motor encoders, any tape head, a shaft encoder): none "knows" position; the
SiTech learns it from an Init on a star or from a Waypoint plate solve, then dead-reckons on counts. A scope encoder
therefore only adds (a) position kept through a hand push with the pinion lifted and (b) belt-slip detection. Both are
also covered by re-solving after a push, which takes seconds. So:

- **Alt: no scope encoder.** Nothing on the D rim but the roller track and belt (the 0.26" "tape" band is spare).
  The tape idea (RLS LM10 at 10 µm, 223 k counts) is dropped: $250, a bonded track, a 0.3–0.8 mm gap to hold, and it
  only saved a plate solve. Gravity keeps the alt train loaded one way, so a belt skip is unlikely and shows at once.
- **Az: the owned Astro Devices HD azimuth assembly** on the pivot. It is an RLS MR magnetic ring (OD 48 mm MEASURED →
  76 poles × 4096 = **311,296 steps/rev**, 4.2"/step, 10.4 kHz at 12°/s; the HD guide's number) bonded to a carrier disc
  with a Ø6 boss, read by an RLC2HD potted in a block on a 3 mm floating plate whose Ø6.2 bearing rides the boss (gap
  fixed by the kit), the plate held against rotation by a slot. Mounted the way the kit is meant to go (Nick): the pivot
  bolt fixed in the ground hub (FR6 in the floor housing, as first drawn), the ring disc pressed onto the bolt by the
  kit's printed hub and sitting on the hub top, static with the ground; the plate hangs under the rocker floor on the
  boss with the 15 mm reader block in a ~0.1" relief pocket in the floor underside; its anchor slot (130 mm from the
  bearing, MEASURED) takes a #8 shoulder screw from the floor, close-fitting, with the kit's wire spring keeping the slot
  loaded against it: slot play reads straight into azimuth (0.1 mm at 130 mm = 2.6'). The reader goes round with the rocker, so its cable stays on the rocker with the SiTech and nothing crosses
  the az axis. Stack = 11 (disc, ASSUMED) + 3 + 15 mm in the 1.15" hub-to-floor gap; feet stay 0.75", rocker 16.0".
  SiTech: 311296 ticks, Tick Management (or Polite) mode. Still to measure: disc thickness, boss, printed-hub bore, plate
  length. (An earlier draft today hung the assembly under the hub on an inverted pivot with 1.5" feet: superseded.)
- **Home switch** at the zenith parking position on the Servo II HOME input: from park the counts are already right, so
  the first slew lands within the model error before any star or solve. Drawn with the brake and parking lock.

**What Nick owns (from Gmail):** EyepiecesEtc order 5746, 2022-01-08, code 9409988 "NEXUS DSC ENCODER KIT FOR GSO
DOBS", $299.95: azimuth = 8192-step shaft encoder on a tangent arm (10 mA); altitude = Renishaw magnetic-tape reader,
716,000 steps/rev on the GSO bearing (20 mA), tape ~180° supplied, 0.4 mm gap (Astro Devices GSO installation guide;
Serge Antonov, Jan 2022 thread "Magnetic tape": tape and readers are Renishaw, extra tape US$50/m). The tape reader
(photographed 2026-11-08: Astro Devices "HD SENSOR" carrier, 8P8C jack J1, two slotted mounting holes) carries an
**RLS RLC2HD** miniature PCB readhead (2 mm pole, TTL A/B/Z, 5 V, < 20 mA; resolution fixed by part code = 2,000 µm ÷
interpolation: 2D0 = 1 µm, 1D0 = 2 µm, D20 = 10 µm). The 716,000 steps on a GSO bearing put ours at 1–2 µm, i.e.
1.1–2.2 M steps/rev on our 28" D, over both controllers' limits, so it is not used. If an alt scope encoder is ever
wanted after all, an RLC2HD-D20 (10 µm) on RLS MS tape at R 14" gives 223 k counts (5.8"/step, 7.4 kHz at 12°/s) for
~$100, not the $250 LM10 quoted earlier.

Bench test of the az encoder on the SiTech: A → AZM/RA S.E. A, B → S.E. B, +5 V and GND to that block (meter the
cable first: a supply swap destroys the encoder; the Nexus DSC Pro RJ45 it was wired for is 1 B-az, 2 +5 V, 3 A-az,
4 GND, 5 B-alt, 6 +5 V, 7 A-alt, 8 GND, TTL 5 V). Set 311296 scope-encoder ticks on az, one turn by hand → ±311,296 on
"Scope Encoder Location" (`YZ` in the terminal). The SiTech count-rate question to sales@ is now moot (311,296 × 12°/s / 360 = 10.4 kHz, under 25 kHz); the support@ address bounced.

Sources: Nexus DSC Pro User Manual (astrodevices.com), Astro Devices GSO Encoder Installation guide, Gmail (EyepiecesEtc order 5746; Astro Devices thread Jan 2022),
SiTech Setup Manual, RLS LM10 datasheet.

Sources: SiTech Servo I manual (`ServoDoc.pdf`, Sidereal Technology), Hubble Optics UL SiTech GOTO Quick Start R1.6
(2019), Astrofox Servo II listing, Pittman incremental encoder catalogue (H series).
