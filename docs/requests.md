# Requests from the local session to the cloud session

The local session (Nick's desktop: Aspire CAM, Voron Trident, DobStuff archive, measurements) writes requests
here; the cloud session owns the model code and `goto-rebuild/out/` and answers by committing. Newest first.
Mark a line `[done <date>]` when it lands; keep done items until the next tidy.

## 2026-11-04 — wedge fixtures

- **Status (no action needed):** the eight fixtures in `out/joint_machining/print/` are sliced and queued on
  trident1 (`gcodes/dob_fixtures/`): **ASA** (not PLA, per the cloud session's advice: creep under the clamp
  preload), 0.2 mm, 4 walls, 20 % cubic, 6 top / 5 bottom layers, 6 mm brim, chamber 50 °C.
  About 5.0 h and 160 g each for the pair fixtures, 5.75 h and 186 g for the socket fixtures (40 % gyroid was
  22 h each; the fixtures are in compression, so 20 % cubic is plenty). Slicing tool: `local/slice_trident.py`.
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
