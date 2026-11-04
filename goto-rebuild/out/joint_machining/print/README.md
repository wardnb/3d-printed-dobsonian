# Wedge fixtures: printing notes

Eight 3D-printed fixtures that hold the truss socket and pair blocks on the AltMill while their 60° cups and
Ø1.244 bores are cut (one per machining station; see `../report.json` and `../sheet.png`). They are tooling only:
not part of the finished scope. STLs here are in mm with the flat base on z = 0, print as exported.

| File | Holds | Footprint (mm) | Height |
| --- | --- | --- | --- |
| fixture_socket_point_L / _R | 90° socket block, left / right cup | 165 × 183 | 56 |
| fixture_socket_back_L / _R | 210° and 330° socket blocks (same part), left / right cup | 167 × 183 | 57 |
| fixture_pair_30_L / _R | pair block 30°; `_L` also does pair 270° left bore | 144–147 × 176 | 50–55 |
| fixture_pair_150_L / _R | pair block 150°; `_R` also does pair 270° right bore | 144–147 × 176 | 51–54 |

## Slicer settings (Voron Trident)

- Material: ASA or PETG (PLA creeps under clamp load and chips come off warm).
- Orientation: as exported, flat side down. No supports: slope, fences and datum post all face up.
- Layer height 0.2 mm; first layer slow and well squished (the base is the machine datum).
- Perimeters 4–5, top/bottom 5 layers, infill 30–40 % gyroid or cubic. Stiffness under the strap clamps matters
  more than strength.
- No brim unless ASA warps on your bed; the base is large and flat.
- Expect roughly 150–200 g and 6–10 h per fixture (28–34 in³ each), ~1.5 kg for the set. Print the four pair
  fixtures first (smaller; the pair bores are the easier first cut).

## After printing

- Press two 1/4-20 heat-set inserts into the Ø0.36" × 0.9" holes beside each slope. They are normal to the sloped
  face so the strap clamps sit square to the block.
- Check the square datum post is square to the base with a machinist's square: it is the XYZ touch-off reference
  for the station's G-code, so any lean goes straight into the cut.
- Check the sloped face is flat (pencil on the block's underside, rub, scrape high spots).
- Label each fixture with its station name; the pairs look alike.

## Touching off (answers `docs/requests.md`, 2026-11-04)

Printed ASA shrinks ~0.5 % unless the slicer compensates, so the post-to-block distance on a 7" fixture can be
0.3–0.5 mm off. What that error does: it shifts the cup or bore sideways on the block by that amount. The cone
self-centres in its cup, so the only effect is the pole-base position, which collimation absorbs; the things that
have to be right (cup angle, axis direction, depth) come from the tool, the fixture's slope angle (unchanged by
uniform shrink) and Z. So:

- **Z: touch off on the block, not the post.** Before cutting, touch the block's top face directly above the
  feature (X, Y in the `.nc` header and `report.json: block_top_z_at_feature_xy`) and set that reading to the Z
  given. The block is machined aluminium, so depth (= pole length) is then exact.
- **X/Y: post corner, then a caliper check.** `report.json: block_fence_corner_xyz` is the model's position of the
  fence inner corner (where the block's corner seats) from the post corner. Measure the print; shift G54 by any
  difference. Enable the slicer's shrinkage compensation for ASA on future prints and the check becomes a formality.
- `block_top_high_vertex_xyz` is the block's highest corner, for a sanity check of the whole setup with a dial.

## Holding the fixture down

Three vertical Ø0.27" through-holes in the flat slab corners (`report.json: holddown_holes_xy_0p27`, from the post
corner), clear of the sloped body so a 1/4" screw head seats on the flat slab top. Screw into the spoilboard
(T-nuts or threaded inserts). Fixtures printed before 2026-11-04 don't have them: drill them at the listed XY
(the slab is flat there), or clamp the slab edges.

## On the AltMill

- Fixture base clamped flat to the spoilboard, datum post toward the machine's front-left; G-code zero =
  the post's top front-left corner (touch plate X, Y, Z).
- Z need with the socket fixtures: ~5.7" from spoilboard to collet nut at full retract (stack 3.65" + 0.5"
  retract + ~1.55" tool stickout). Measure this before cutting the sockets.
- Feeds in the `.nc` files are conservative guesses: cut one cup in scrap first.
