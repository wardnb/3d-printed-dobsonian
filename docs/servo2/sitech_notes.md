# SiTech Servo II: working notes distilled from the documentation (crawled 2026-11-08)

The PDFs themselves could not be saved from the cloud session (siderealtechnology.com is outside its network allow-list);
these notes keep what this build needs. Sources: ServoConfig Manual (2006), Basic Quick Start for Alt-Az (Rev J), Setup
Manual, SiTechEXE Help Files, Servo Controller II Wiring Diagram (2012-11-24), SiTech Serial Protocol (Google Doc),
Firmware Notes. Download list: https://www.siderealtechnology.com (Documentation section).

## Hardware facts

- Power: +12–28 V on the barrel jack (Servo II wiring diagram), centre positive. Reverse polarity blows the fuse and can
  damage parts (protection diode is after the fuse). Servo I limits: 2.4 A per motor, 4 A total; Servo II "double the
  amperage" per a dealer, number asked of SiTech by email 2026-11-08.
- Encoder inputs (motor and scope) are TTL 0–5 V; RS422 option: A+ → A, B+ → B. Later controllers have the pull-ups built in.
- Terminal blocks (left → right): ALT/DEC INPUTS (+LIMIT −LIMIT HOME PSYNC AN IN +5V GND) · AZM/RA INPUTS (same) ·
  ALT/DEC MOTORS (M.E. A, M.E. B, S.E. A, S.E. B, +5V, GND, MOT+, MOT−) · AZM/RA MOTORS (same). Printable strip:
  `terminal_legend.pdf`.
- Axis naming in the protocol and in ServoConfig's bit boxes: **X = Altitude/Dec, Y = Azimuth/RA** (main-screen columns
  are the other way round: Az/RA left, Alt/Dec right).
- Never swap motor and encoder leads: it can destroy the controller. Flat cable preferred; CAT5 acceptable, kept short
  and away from encoder leads.
- Scope-encoder resolution: Setup Manual says "as much as 500,000" counts per rev before ticks are missed at fast slews;
  the Quick Start says ~200,000+ tick encoders use Tick Management mode, lower ones Precise/Polite with the supervisory
  threshold at ~2.5× (SiTechExe help: 1.5–2×) the encoder resolution. The Astro Devices 311,296-step kit fits this;
  a 1.2 M count tape does not unless SiTech confirms a higher Servo II limit. Plan (2026-11-08, `drive_bringup.md` §5a):
  Astro Devices ring at the az pivot (311,296), RLS LM10 on 2 mm tape at 10 µm on the alt D rim (~223 k). Nexus DSC Pro
  RJ45 for testing the Astro Devices sensors: 1 B-az, 2 +5V, 3 A-az, 4 GND, 5 B-alt, 6 +5V, 7 A-alt, 8 GND (TTL, 5 V).

## Our numbers (motor encoder 500 CPR × 4 = 2000; gearbox TRUE ratio 19.658119658:1, not 19.7)

| | Alt | Az |
| --- | --- | --- |
| Counts per gearbox output rev | 39,316.2 | 39,316.2 |
| Final ratio (2:1 belt × rim/pinion) | 112.48 | 120.48 |
| **Ticks per scope rev (enter in ServoConfig)** | **4,422,291** | **4,736,821** |
| Ticks per arcsec | 3.41 | 3.66 |
| Test rim (old DobStuff D, R 12.19 + 0.06, 2:1: 98.0) | 3,853,000 | — |

Keep the raw slew below ~6,500,000 (manual). Guide speed is ADDED to the tracking speed, not absolute. Author's speeds:
slew 3.5°/s (start at 1–2), pan ~15′/s visual alt-az (we set 3′/s for the bench), guide ~7″/s for autoguiding.

## ServoConfig essentials

- Enter ticks per rev FIRST (the DPS/MPS/SPS boxes convert from them). Type numbers without commas: the field keeps
  only the first digit otherwise (seen 2026-11-08).
- Defaults/our bench values: PID 15000 / 1500 / 4000, acceleration 1000 (author uses 1000–1500), error limit 12,800,
  output limit 100 % (set 50 % only for a 12 V motor on 24 V: ours are 24 V motors), current limit 0.70 A (default
  2.4), integral limit 22,000.
- Inversion rule: motor runs away then stops → toggle **Invert Motor Encoder** (or rewire), not motor direction. Moves
  cleanly but the wrong way → toggle BOTH Invert Motor and Invert Motor Encoder.
- Manual ("Blinky") mode: LED blinks ~1/s; entered when the error reaches the error limit while the motor is slow or
  moving the wrong way; a motor lagging in the right direction is tolerated (setpoint held at position ± error limit).
  Recover with Auto in Test and Tune or Reset.
- Memory: firmware flash / configuration flash (copied to RAM at power-up) / RAM. Hot Mode and Test-and-Tune edits go to
  RAM only; **Send Configuration To Controller** or **Write Flash** persists them. Config files are `.car`.
- Test and Tune is live. PID order: I = 0, P = 0; raise D until it hums, back off (it should still resist the hand);
  raise P by a few thousand until unstable, back off; raise I from ~1000 until unstable, back off; check several speeds,
  if rough lower I then P. At slow speed the error should read −1/0/+1.
- Ticks Determination (for roller drives; geared axes are calculated): Step One zeros at start, Step Two move to end,
  Step Three store, Step Four move back, Step One again; repeat until stable; approach marks from the same direction.
- Backlash Help: centre a fixed object with UP+LEFT only, click; recentre with DOWN+RIGHT only, click; result in ticks
  and arcmin per axis. If an axis is unbalanced so friction already removes backlash, set it to zero. Backlash speed
  ~30,000 raw slow / ~500,000 quick. Do not also set backlash in SiTechExe (doubles it).
- On-screen hand pad buttons latch over USB in v1.30: second click or All-Stop stops them. Commanding an axis with
  no motor trips it to Manual.

## SiTechExe (alt-az) essentials

- Config → Scope Info: lat/long/elevation (refraction uses them), focal length. Mount Parms: Alt/Az; Altitude Limit
  (or horizon file `SiTech.hrz`); **Azimuth No Wrap** (no-go zone centred on due north: a NW→NE slew goes via south);
  Keep Above Horizon Limit while Slewing; Motors to Manual on Park; Gain 0.9; **Slew Before Amount** = a little more
  than the mechanical backlash (0 for direct drive). Misc: COM port, comm loop 100 ms (75 fastest; quick start says
  250), Refraction on, Init window timeout 4–5 s.
- Scope Encoders tab: Ignore / Precise (re-centres the motor position when the disagreement exceeds the Supervisory
  Threshold) / Polite (encoders only while slewing and initialising; good for imaging) / Tick Management (medium-res
  encoders) / Cascade (high-res) / Drag (clutched mounts, no offset tracking). A 10° motor-vs-scope mismatch trips
  Blinky mode (check for a slipping belt).
- Direction check: RIGHT = azimuth clockwise seen from above; UP = altitude toward the zenith (N hemisphere); both
  motor and scope encoder counts increase. Fix directions in ServoConfig, not SiTechExe.
- Init: nothing tracks or slews until the first Init. Offset Init (ESC / top-left) shifts the sky and starts tracking.
  Load Cal Star (RTN / top-right) feeds PointXP. Alt-az model: Polaris first, then a star at similar altitude ~120° away,
  then one well separated in altitude; ≥ 16 stars for best accuracy; no Offset Inits while adding Cal Stars.
- Park / Set Park (axis angles, stop tracking first) / UnPark (no GoTo). Right-click for two extra park positions.
- Handpad in SiTechExe: inner arrows pan, outer arrows slew; Jog ArcMins option. SPD cycles slew/pan/guide; RTN toggles
  tracking; ESC starts a spiral search.
- Save the servo clock calibration after ~30 min running (typical 0.99995).

## Serial protocol (ASCII, uppercase, `\r` terminated; address 1 = X/Y, 3 = T/U, 5 = V/W)

- Bare `\r` → `X# Y# XZ# YZ# XC# YC# V# T# X[AM] Y[AM] K#`: motor positions, scope encoder positions, motor current × 100,
  supply × 10, CPU °F, Auto/Manual, handpad bits (1 L, 2 R, 4 U, 8 D, 16 pan, 32 RTN, 64 ESC).
- `X#` / `Y#` go to absolute motor position (± 2^31), `X#S#` with speed; `X` reads position; `XF#` forces the position
  (stops the axis); `XS#` speed in counts per servo loop × 65,536 (loop 1953 Hz: 1000 counts/s → `XS33555`); `XR#` ramp
  0–3900; `XP# XI# XD#` PID; `XE#` error limit, `XE` current error; `XO#` PWM limit; `XC#` current limit × 100.
- `XN`/`YN` normal stop, `XG`/`YG` emergency stop, `XM#` manual mode with PWM −255…255, `XA` auto.
- `XZ`/`YZ` read scope encoder, `XZ#` set; `XXT#` / `XXZ#` scope encoder ticks per rev (X / Y).
- `XW` save RAM config to flash, `XT` reload from flash, `XU` factory defaults, `XQ` reboot, `SB#` baud (1 = 9600,
  2 = 19200).
- `Q` returns Tangent-format encoder data (resolution fixed at 18000); `0xAA` switches to PicServo emulation.
