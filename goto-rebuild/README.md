# 16" f/3.9 GoTo Dob rebuild — parametric model

Parametric CadQuery model of the DobStuff 16" rebuild: 3/8" 6061 upper cage, straight quad spider on the
posts between the rings, self-aligning 3.5" secondary holder, wide-pair 6-pole truss on the mirror cage's
stub tubes, belt-on-rim SiTech drives (GM9413 alt, GM9213 az on the rocker).

Design doc: [`../docs/design.md`](../docs/design.md) (exported) · living doc: https://claude.ai/code/artifact/a2bd133b-cebf-4c55-a572-9a930c1ab10f · project context: [`../CLAUDE.md`](../CLAUDE.md)
3D viewer: https://claude.ai/artifact/J1dg2GqFYWfny88NzJT5gF

## Run

    pip install cadquery numpy matplotlib shapely
    python dob_model.py        # whole scope -> out/*.glb, out/dob16_alt45.step, out/params.json
    python export_cage.py      # upper cage fit checks + DXF/STEP -> out/upper_cage/
    python export_holder.py    # secondary holder, carrier, gluing jig -> out/secondary_holder/
    python export_rocker.py    # rocker, ground board, bearing layers: fit checks + DXFs + cut layout on 24.4 x 48 AltMill blanks -> out/rocker/
    python cage_fe.py quad     # cage + spider collimation-drift FE
    python truss_fe.py         # truss FE (layouts, joint stiffness)
    python build_site.py       # viewer -> dist/ (GLBs base64 as .txt for the artifact host)

## Files

| File | What |
| --- | --- |
| `dob_model.py` | Whole scope, balance solve, mirror cage, truss, bearings, drives |
| `upper_cage.py` | Rings, posts, rails, focuser board, spiders (quad/Destiny/wire), finder, tools |
| `secondary_holder.py` | Carrier, 45° body, gluing jig |
| `rocker.py` | Rocker, ground board, 14" D bearings (derive numbers, build solids and flats) |
| `cage_fe.py`, `truss_fe.py`, `wire_geo*.py` | Frame FE studies |
| `site/index.html` | three.js viewer template |

## Inputs still assumed (measure)

Box ring back outline (swing radius), weights, carbon tube bore; Feather Touch FTF2015 bolt circle; secondary thickness; cell (silicone-bonded or loose on pads). Full list in `../docs/design.md`.
