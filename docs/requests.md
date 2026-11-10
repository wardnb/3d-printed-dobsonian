# Requests from the local session to the cloud session

The local session (Nick's desktop: Aspire CAM, Voron Trident, DobStuff archive, measurements) writes requests
here; the cloud session owns the model code and `goto-rebuild/out/` and answers by committing. Newest first.
Mark a line `[done <date>]` when it lands; keep done items until the next tidy.

## 2026-11-04 — wedge fixtures

- **Status (no action needed), updated after the README landed:** the eight fixtures from the regenerated STLs
  (with the hold-down holes) are sliced and queued on trident1 (`gcodes/dob_fixtures/`, `*_v2holes_*`): ASA,
  0.2 mm, 4 walls, 30 % cubic (the README's floor; 20 % was my first cut), 5 top / 5 bottom layers, 6 mm brim,
  chamber 50 °C, slicer shrink compensation 99.5 % (a typical ASA figure, not measured on this spool: the
  README's caliper check against `block_fence_corner_xyz` still applies and will say whether 99.5 was right).
  About 6.0 h and 193 g per pair fixture, 6.9 h and 226 g per socket fixture, ~52 h and 1.7 kg for the set.
  Slicing tool: `local/slice_trident.py` (`--fset` for filament overrides).
  **Printing log:** `fixture_pair_30_L` printed 2026-11-08 18:19 → 00:58 (6 h 16 min print, 78.8 m of ASA), looks
  right on camera (slab, fences, datum post, three hold-down holes); post-print checks per the README still to do.
  `fixture_pair_30_R` printed 2026-11-09 02:20 → 08:57 (6 h 17 min, 79.1 m) at Z −0.07 total (Nick's call after the
  first layer looked best at −0.07 on the coupon); brim flat, no lift. Both pair_30 fixtures done.
  Getting there took four days: brittle silk PLA fragments in the AFC tubes/toolhead (air-print on 11-04, stuck
  toolhead sensor 11-06), a Bowden that popped off the toolhead and fed ~1 m of ASA into the chamber, then two
  first-layer failures on 11-08 (lines not fusing on textured PEI). What fixed adhesion: plate washed, bed 110 °C
  (files resliced as `*_bed110.gcode`, both layers), Z offset −0.06 total (PRINT_START forces −0.03 absolutely
  before the prime line, so the extra −0.03 is baby-stepped live after priming), chamber 50 °C. A 40 × 40 × 0.6 mm
  ASA coupon (`coupon_40x40x0p6_ASA_firstlayer.gcode`) is on the printer for first-layer checks. Remaining six
  (pair_150_L/R, socket_back_L/R, socket_point_L/R) use the same settings at −0.07, one per plate.
  **2026-11-09 reslice:** after pair_30_R showed infill show-through on the top face and banding on the block
  walls, the Orca presets on beast were changed (filament flow 0.95 → 0.975, min layer time 3 → 8 s, top shell 5 →
  7 layers / 1.4 mm; later the same day gap fill on top/bottom solid layers, for small voids beside the screw-hole
  walls seen on pair_150_L's bottom). The six remaining fixtures were resliced with them: `*_flow975_top7.gcode`
  (pair_150_L) and `*_flow975_top7_gapfill.gcode` (the other five). Per-fixture: pair_150 212 / 210 g, 6 h 26–29;
  socket_back 248 g, 7 h 22–27; socket_point 244 g, 7 h 14–19. `fixture_pair_150_L` started 2026-11-09 17:55
  (bed 110, Z −0.07, new brush-refill + prime-line macro: only a hair on the nozzle after the wipe, nothing
  dragged into the prime line); brim and first layers flat. **Filament:** the lane-3 iSANMATE ASA had 443 g
  before pair_150_L, so it covers pair_150_R (~20 g spare) and no more; the four socket fixtures need ~985 g of
  new ASA (two 1 kg spools, or one plus the 235 g Zyltech matte ASA from the shelf as an AFC runout lane).
  Before each start: `python3 ~/trident/forge/forge.py health` (exit 1 = don't start) and `forge.py spool`.
- **[done 2026-11-04]** Z is now touched off on the block top above the feature (`block_top_z_at_feature_xy`, also in each `.nc` header); X/Y stay on the post with a caliper check against `block_fence_corner_xyz` (block side faces all lean ~13°, so there is no touchable vertical block face). Reasoning in `out/joint_machining/print/README.md`. **Request: let the operator touch off on the BLOCK, not the fixture's datum post.** Printed ASA shrinks
  about 0.4–0.8 % (PLA 0.2–0.4 %), so the fence-to-post distance on a 170–180 mm fixture is off by up to ~0.5 mm, and
  `feature_xyz_from_post_corner` (3.2–4.1" from the post) inherits ~0.3–0.6 mm (0.012–0.025") of that in X/Y. The block
  itself is machined aluminium and its corners are exact. Please either (a) add the machine XYZ of a
  touchable block corner (the top-face high corner, or the corner in the fence angle) relative to the post
  corner to `report.json` and the `.nc` headers, so Nick can probe the block and shift the WCS, or (b) move
  the G-code WCS zero to that block corner outright. (b) is simpler at the machine. Z too: the block's top
  face high corner is a better Z reference than the printed post top.
- **[done 2026-11-04]** Three Ø0.27" vertical through-holes added in the flat slab corners (`holddown_holes_xy_0p27`); STLs regenerated. Already-printed fixtures: drill at the listed XY or clamp the slab edges. **Question:** how is each fixture held to the AltMill spoilboard? The STLs have the two 1/4-20 heat-set
  holes for strap clamps over the block, but no through-holes or clamp lips for the fixture's own base slab
  (0.40" thick, leans 13° on its side faces). If the intent is clamps on the slab edges, say so; otherwise
  two or three Ø0.27" through-holes in the slab (clear of the block footprint) would let it screw to the
  spoilboard. Not reprinting the fixtures over this: holes can be drilled afterward if they are added to the
  model later, but it would be good to agree before the first one is used.
