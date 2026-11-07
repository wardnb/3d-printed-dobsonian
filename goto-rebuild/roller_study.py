"""Roller bearings instead of PTFE/laminate pads on both axes (study 2026-11-07, adopted).

Why: Ebony Star is discontinued, the PTFE/laminate friction (alt ~145 in-lb, az ~183 in-lb at mu 0.12 ASSUMED) left
only ~1.7x torque margin on the 45 oz-in gearboxes, and that friction is larger than the imbalance, so the alt gear
train crossed its backlash at every direction reversal (transit, guide pulses). Steel ball-bearing rollers on an
aluminium track take the friction down ~15x: the gearbox margin becomes ~9x and the imbalance alone keeps the train
preloaded. Cost: a brake for hand pushing (the tube no longer stays put on its own), rollers that must sit on a true
track, and point loads on the D rims (checked with bearing_fe: no change).

Numbers here are the design basis for rocker.py (bearing_kind = "rollers") and the Decisions table. Run from
goto-rebuild/ after dob_model.py; writes out/roller_study/report.json and prints the table.
ASSUMED: bearing seal drag 10 N mm per 2RS bearing (ZZ shields are ~1/5 of that), mu PTFE tab 0.10, brake pad mu 0.5,
E ply in-plane 7 GPa (edge-loaded birch), gearbox continuous 45 oz-in.
"""
import json
import math
import os

P = json.load(open("out/params.json"))
G = P["rocker"]
OUT = "out/roller_study"
os.makedirs(OUT, exist_ok=True)

LB, IN, N_MM = 4.448, 25.4, 1.0

# --- loads
W_TUBE = P["checks"]["tube_weight_lb"]                   # 74.3 lb on the alt bearings
W_ROCKER = 28.0                                          # ASSUMED: rocker + drives + electronics (birch 15.9" tall)
W_AZ = W_TUBE + W_ROCKER                                 # on the az rollers
R, PAD = G["R"], G["pad_angle"]
R_AZ = G["az_pad_r"]

# --- rollers: R10-2RS/ZZ deep-groove ball bearing used as a wheel, on a 5/8 shoulder bolt
ROLLER = dict(name="R10 (5/8 x 1-3/8 x 11/32)", od=1.375, bore=0.625, w=0.344, C0_lb=830, C_lb=1400)
TRACK_ALT = dict(t=0.0625, w=0.625, alloy="6061-T6 flat, bent elastically around the rim, epoxy-bonded")
TRACK_AZ = dict(t=0.125, alloy="6061 plate ring, 3 x 120 deg segments, r 12.25-13.25")
E_ST, E_AL, NU = 200e3, 69e3, 0.3                        # MPa
E_PLY_INPLANE = 7000.0                                    # MPa, ASSUMED (edge-loaded Baltic birch)
PLY_DEPTH = 25.0                                          # mm of ply under the strip that carries the foundation
SEAL_DRAG = 10.0                                          # N mm per bearing, ASSUMED (2RS); ZZ ~2
MU_TAB = 0.10                                             # PTFE lateral tab on the D's face
MU_BRAKE = 0.5                                            # rubber/cork shoe on the aluminium track, ASSUMED
IMBALANCE = 25.0                                          # in-lb (Decisions: Drives)
GEARBOX_OZIN = 45.0


def hertz_line(F_N, L_mm, r_mm, E1, E2):
    """Max contact pressure (MPa) for a cylinder of radius r on a flat, line contact of length L."""
    Es = 1.0 / ((1 - NU ** 2) / E1 + (1 - NU ** 2) / E2)
    return math.sqrt(F_N * Es / (2 * math.pi * L_mm * r_mm))


def foundation(F_N, L_mm, t_mm, E_strip, E_found, depth_mm):
    """Thin strip on an elastic foundation under a line load: peak foundation pressure and strip deflection."""
    k = E_found / depth_mm                                # N/mm^3
    EI = E_strip * t_mm ** 3 / 12.0                       # per mm width
    beta = (k / (4 * EI)) ** 0.25
    q = F_N / L_mm                                        # N/mm along the roller
    p = q * beta / 2.0                                    # MPa under the line
    d = q * beta / (2 * k)                                # mm
    return p, d, 1.0 / beta


rows = {}
# ---- altitude: four rollers, two per side at +/-PAD under the rim
n_alt = W_TUBE / (4 * math.cos(math.radians(PAD)))        # lb per roller (static)
r_mm, L_mm = ROLLER["od"] / 2 * IN, ROLLER["w"] * IN
p_alt = hertz_line(n_alt * LB, L_mm, r_mm, E_ST, E_AL)
p3_alt = hertz_line(3 * n_alt * LB, L_mm, r_mm, E_ST, E_AL)
pf, df, lchar = foundation(n_alt * LB, L_mm, TRACK_ALT["t"] * IN, E_AL, E_PLY_INPLANE, PLY_DEPTH)
k_roller = (n_alt * LB) / df / LB * IN                    # lb/in radial stiffness of strip-on-ply
# friction at the rim: seal drag referred to the roller radius + rolling resistance (negligible) + lateral tab rub
f_rim_alt = 4 * SEAL_DRAG / r_mm                          # N tangential at the rim
t_alt_rollers = f_rim_alt / LB * R                        # in-lb
t_alt_tab = MU_TAB * (W_TUBE * math.sin(math.radians(2.0))) * R   # 2 deg ground slope, ASSUMED
t_alt = t_alt_rollers + t_alt_tab
t_alt_old = 145.0
rows["alt"] = dict(roller_load_lb=round(n_alt, 1), hertz_MPa=round(p_alt), hertz_3g_MPa=round(p3_alt),
                   al_yield_MPa=276, foundation_MPa=round(pf, 2), strip_deflection_in=round(df / IN, 5),
                   strip_char_length_in=round(lchar / IN, 2), roller_support_stiffness_lb_in=round(k_roller, -3),
                   friction_in_lb=round(t_alt, 1), friction_old_in_lb=t_alt_old,
                   drive_in_lb=round(t_alt + IMBALANCE, 1), drive_old_in_lb=t_alt_old + IMBALANCE)
# ---- azimuth: four rollers at r 12.75 (45/135/225/315) on a 1/8 plate ring
n_az = W_AZ / 4
p_az = hertz_line(n_az * LB, L_mm, r_mm, E_ST, E_AL)
pf_az, df_az, _ = foundation(n_az * LB, L_mm, TRACK_AZ["t"] * IN, E_AL, 500.0, 18.0)   # face-loaded ply, E_perp 0.5 GPa
f_rim_az = 4 * SEAL_DRAG / r_mm
t_az = f_rim_az / LB * R_AZ
t_az_old = 183.0
rows["az"] = dict(roller_load_lb=round(n_az, 1), hertz_MPa=round(p_az), foundation_MPa=round(pf_az, 2),
                  friction_in_lb=round(t_az, 1), friction_old_in_lb=t_az_old)

# ---- drive margin (2:1 belt stage x gearbox 112:1 alt / 120:1 az, pinion 0.5 PD on the rim)
def margin(t_axis, ratio):
    t_out = t_axis / ratio * 16.0                          # oz-in at the gearbox output
    return round(t_out, 1), round(GEARBOX_OZIN / t_out, 1)
rows["drive"] = dict(alt=dict(zip(("gearbox_oz_in", "margin"), margin(t_alt + IMBALANCE, G["alt_ratio"]))),
                     alt_old=dict(zip(("gearbox_oz_in", "margin"), margin(t_alt_old + IMBALANCE, G["alt_ratio"]))),
                     az=dict(zip(("gearbox_oz_in", "margin"), margin(t_az + 10.0, G["az_ratio"]))),   # +10 wind/cable ASSUMED
                     az_old=dict(zip(("gearbox_oz_in", "margin"), margin(t_az_old, G["az_ratio"]))))
# ---- backlash: the train stays preloaded while |imbalance| > friction
rows["preload"] = dict(alt_friction_in_lb=round(t_alt, 1), imbalance_in_lb=IMBALANCE,
                       train_preloaded=t_alt < IMBALANCE,
                       bias_recommended_in_lb=(20, 30),
                       note="balance with the lightest eyepiece and let every heavier one add nose-heavy bias; "
                            "with ~10 in-lb of friction the drive torque never reverses, so no backlash crossing at transit")
# ---- brake for hand pushing: restore a Dob-like feel when the pinion is lifted
for ax, r_, want in (("alt", R, 100.0), ("az", R_AZ, 120.0)):
    f_t = want / r_
    rows.setdefault("brake", {})[ax] = dict(hold_in_lb=want, tangential_lb=round(f_t, 1),
                                           shoe_normal_lb=round(f_t / MU_BRAKE, 1),
                                           eyepiece_push_lb=round(want / 63.6, 1) if ax == "alt" else None)
# ---- rim runout -> pointing (absorbed by the pointing model; here for scale)
rows["runout"] = dict(radial_runout_in=0.010, tube_tilt_arcsec=round(0.010 / (2 * G["bearing_x_in"]) * 206265),
                      note="differential left/right rim runout tilts the tube about the vertical; smooth with altitude")
# ---- bearing_fe check: pad load width 0.8 -> 0.15 (2026-11-07 run, wing clamped)
rows["bearing_fe_point_loads"] = dict(grav_pinion_15deg_as=(24.56, 24.80), fastener_3g_max_lb=(145, 148),
                                      note="D rim/joint windup unchanged with point loads: the joint, not the rim, sets it")
rows["assumed"] = dict(seal_drag_N_mm=SEAL_DRAG, rocker_weight_lb=W_ROCKER, mu_tab=MU_TAB, mu_brake=MU_BRAKE,
                       e_ply_inplane_MPa=E_PLY_INPLANE, gearbox_oz_in=GEARBOX_OZIN, imbalance_in_lb=IMBALANCE)
rows["parts"] = dict(roller=ROLLER, track_alt=TRACK_ALT, track_az=TRACK_AZ, qty_rollers=8,
                     axle="5/8 x 1 shoulder bolt, 1/2-13 thread, 8 off", pivot="3/8 shoulder bolt in an FR6-2RS flanged bearing (zero play)")
json.dump(rows, open(os.path.join(OUT, "report.json"), "w"), indent=1)

if __name__ == "__main__":
    a, z, d = rows["alt"], rows["az"], rows["drive"]
    print(f"ALT  {a['roller_load_lb']} lb/roller  Hertz {a['hertz_MPa']} MPa (3 g {a['hertz_3g_MPa']}; 6061 yield 276)  "
          f"ply foundation {a['foundation_MPa']} MPa  support {a['roller_support_stiffness_lb_in']:.0f} lb/in")
    print(f"     friction {a['friction_in_lb']} in-lb (was {a['friction_old_in_lb']})  drive {a['drive_in_lb']} in-lb (was {a['drive_old_in_lb']})  "
          f"gearbox {d['alt']['gearbox_oz_in']} oz-in, margin {d['alt']['margin']}x (was {d['alt_old']['margin']}x)")
    print(f"AZ   {z['roller_load_lb']} lb/roller  Hertz {z['hertz_MPa']} MPa  foundation {z['foundation_MPa']} MPa  "
          f"friction {z['friction_in_lb']} in-lb (was {z['friction_old_in_lb']})  margin {d['az']['margin']}x (was {d['az_old']['margin']}x)")
    print(f"PRELOAD  friction {rows['preload']['alt_friction_in_lb']} < imbalance {IMBALANCE}: train preloaded = {rows['preload']['train_preloaded']}")
    print("BRAKE   ", rows["brake"])
    print("RUNOUT  ", rows["runout"])
