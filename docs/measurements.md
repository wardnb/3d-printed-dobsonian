# Measured values (as built)

Running log of measurements taken from the real scope. Each entry says how it was obtained. Values go into
`goto-rebuild/dob_model.py` only once the row is marked confirmed; until then they are "read from photo".

## Altitude bearing (one of two), 2026-10-18, photos with a Stanley tape

| Item | Value | How | Status |
| --- | --- | --- | --- |
| Straight edge, end to end incl. clamp block | 24.8" | tape close-up, hook on the block end | confirmed |
| Pivot/pilot hole on the straight edge | 12.4" from the block end, at the edge | tape close-up | confirmed; this is the arc centre |
| Height, outer apex of arc to outer straight edge | 13.25" and 13 3/8" | tape close-ups | superseded: inconsistent with the radius from the centre hole, taken at a slant |
| Arc band radial width | 3.0" | tape, apex | read from photo |
| Straight bar width | 1.8" | tape close-up | read from photo |
| Cutout | from 3.0" to 11.45" below the apex | tape | read from photo |
| Clamp block | wooden split clamp on the straight edge at one end, 1.25" bore perpendicular to the edge in the D plane, bore centre about 2.4" from the end, knob on a saw slot | photo | read from photo |
| Face holes | three small through holes near the apex, mid inner edge, and corner | photo | read from photo |
| Rim | textured black laminate (Ebony Star type) band 11/16" wide on the edge of the main ply | Nick, tape | confirmed |
| Lip | a 3/16" ply strip glued to the outer face with a slightly larger radius, overhanging the laminate; Dennis's lateral guide so the bearing stays on the rocker pads. Nick: "didn't work that well for me" | photos + Nick | confirmed |
| Thickness | 7/8" overall at the rim: 18 mm (11/16", 0.709") Baltic birch main D plus a 3/16" lip ply on the outer face | Nick, tape | confirmed |

**Radius: resolved.** Measured from the pilot hole on the straight edge, the distance to the outer edge of the
laminate is 12 3/16" and to the outer edge of the lip is 12 3/8", constant all the way round, so the hole is the
arc centre and sits on the straight edge at mid-chord (lip diameter 24.75" matches the 24.8" edge). The earlier
13.25" and 13 3/8" height readings were taken off-apex or at a slant and are superseded.

| Running radius (laminate on PTFE) | 12 3/16" (12.19") |
| --- | --- |
| Lip radius | 12 3/8" (12.375") |
| Altitude axis | on the bearing's straight edge, at its midpoint |

The rebuild's 14" radius is a design choice and stands.

**Ply stock.** The laminate band at 11/16" says the main D is 18 mm (0.709") Baltic birch, which is what the
model's `ply` parameter already assumes; the 7/8" overall includes the lip. Confirm on the top ring.

**Design note from the lip.** The as-built bearing relied on an overhanging 1/4" ply lip on the outer face to keep
the bearing tracking on the pads, and it did not track well. The rebuilt bearings should get positive lateral
location that does not depend on a lip: for example a thrust pad bearing on the inner face of each D, or pads
with a shoulder. The drive-side rim already needs its belt and encoder bands held at fixed axial positions, so
the lateral constraint belongs in the same place.

## Rocker and ground board, 2026-10-18, photos

| Item | Value | How | Status |
| --- | --- | --- | --- |
| Construction | two side panels with the cradle arc and three lightening holes, a floor, one end panel (the other end open), ply throughout | photo | confirmed |
| Altitude pads | four small white PTFE pads, one at each end of each cradle arc, on the top edge of the sides | photo | confirmed |
| Small block with a wingnut on one side's top edge | purpose not yet known (bearing retainer or pad carrier?) | photo | ask |
| Azimuth encoder | on the floor at the centre bolt, bracket to the floor | photo | confirmed |
| Underside | a band of textured laminate on the rocker's underside as the azimuth running surface | photo | confirmed |
| Ground board | D-shaped plywood plate, three rubber feet, aluminium centre pivot disc, marked "DobStuff 7-22" | photo | confirmed |
| Inside width between side panels | 22.25" | Nick, tape | confirmed |
| Inside depth, front to back | 23" | Nick, tape | confirmed |
| Side panel thickness | 11/16" (18 mm Baltic birch, same stock as the bearings) | Nick, tape | confirmed |
| Side panel height, floor surface to tip | 16" | Nick, tape | confirmed |
| Side panel height, floor surface to the bottom of the dip | 11 7/8" | Nick, tape | confirmed |
| PTFE pads, centre to centre on one side | 15 3/8" | Nick, tape | confirmed |
| Floor surface to pad centre | 14 3/4" | Nick, tape | confirmed |
| Derived: pad half-angle from the vertical | 39.1° (bearing R 12 3/16") | computed | |
| Derived: altitude axis above the rocker floor | 24.2" | computed | |
| End panels | short panel 3" tall, tall panel 12" tall | Nick, tape | confirmed; from Nick's assembled photo the 12" panel with three holes is on the side the struts lean toward, i.e. the focuser end (to confirm) |
| Azimuth encoder | Renishaw magnetic encoder (Nick's recollection) on a slotted aluminium bar, coupled to the centre pivot; part number still to read off the head | Nick, photo | confirmed |
| Small block with wingnut on a side panel | Nick's own earlier encoder experiment, not part of the kit, no longer needed | Nick | ignore |
| Ground board, foot to the far edge through the pivot | 19" | Nick, tape | confirmed |
| Ground board, foot centre to pivot centre | 10" | Nick, tape | confirmed |
| Ground board shape | roughly square with three corners cut, a flat on the fourth side; pivot disc is aluminium | photo | confirmed |
| Azimuth encoder | Astro Devices "HD Sensor": a small RLS-style magnetic chip (module marked M1, RJ-type connector J1) in a 3D-printed housing, reading a 2" magnetic ring (serial about 305057) in a printed carrier. These are the Nexus DSC Pro high-resolution kits; Astro Devices' installation guides quote 311,296 steps/rev for the ring variants. Output format (quadrature or serial) and SiTech input compatibility unverified | Nick, photos, web | identified; spec to confirm |
| Azimuth running surface on the rocker underside | white textured laminate disc, rough cut, about 22 3/4" dia, nearly full disc (3/8" centre hole only) | Nick, tape | confirmed |
| Centre pivot bolt | 3/8" | Nick | confirmed |
| Azimuth bearing detail | the laminate disc is on the rocker floor's underside; the ground board carries three square PTFE pads at the 10" foot radius (the pads, not the feet, are the bearing), an aluminium pivot disc under the centre hole, and the bolt is a 3/8" stud up through the ground board | photos | confirmed |

## Original DobStuff upper ring (secondary end), 2026-10-18, photos

The original single plywood ring. Superseded first by Nick's 3D-printed cage (retired) and now by the aluminium
cage in the model, so these are for the record only; nothing in the rebuild depends on them.

| Item | Value | How | Status |
| --- | --- | --- | --- |
| Identification | ring with three lobes at roughly 120°, each lobe with a pair of small screw holes (strut end blocks mount here); pairs of small holes around the ring for spider and focuser bracket | Nick, photo | confirmed |
| Inside diameter | 18" | Nick, tape | confirmed |
| Front to back including the lobe point | 23 3/8" | Nick, tape | confirmed |
| Ring width between lobes | about 3" | photo | read from photo |
| Thickness | 18 mm ply assumed | | not needed |

## Mirror box (cage), 2026-10-18, photos

| Item | Value | How | Status |
| --- | --- | --- | --- |
| Construction | shield-shaped top ring and mirror board, six aluminium spacer tubes, a black tube baffle inside, a narrow vertical ply strip on each side between the rings where the bearings bolt (not a full side panel) | photos | confirmed |
| Strut holes | three 45 mm holes through the top ring and the mirror board; seen from above they sit at about 30° and 150° from the bearing axis and at 270° on the point, i.e. the model's 120° pattern with one tube on the plane square to the bearings | photo from above | read from photo; confirm with hole-to-hole and hole-to-flat distances |
| Bearing attachment | studs through the side strips, bearing goes on with knobs/wingnuts | photo | confirmed |
| Strings | two eye hooks on the top ring | photo | confirmed |
| Mirror | 16" with centre spot, sits in the baffle tube; cell is a round plywood plate with three large round openings showing the grey sandwich back, hung on three spring knobs through the mirror board | photos | confirmed |
| Feet | black rubber feet on the mirror board so the box stands mirror-down | photo | confirmed |
| Top ring inside diameter | 18" (model assumed 17.25) | Nick, tape | confirmed |
| Top ring outside, across the flats to the point | about 22 to 23" | tape photos | read from photo |
| Top ring thickness | about 3/4" (18 mm) | tape photo | read from photo |
| Strut hole chords, centre to centre | 18.5" (all three) | Nick, tape | confirmed |
| Derived: strut hole circle radius | 10.68" if equilateral (superseded: the STEP pilots put the back holes at r 10.625" and the point hole at r 10.25", 18.0" from each back hole) | computed | superseded 2026-10-19 |
| Strut hole angles | one hole on the plane square to the bearings (the point), the other two 30° off the bearing axis: the model's (90, 210, 330) pattern | overhead photo | confirmed |
| Box height, inside, mirror board top face to top ring bottom face | 11 3/8" | Nick, tape | confirmed |
| Box height, overall | 11 3/8" + two 18 mm boards = about 12 13/16" (photo read 12 5/8) | computed | |
| Spacer tubes | SEVEN short tubes, 1 1/4" OD, 11 3/8" long: three at the back of the box and two on each side near the front (model assumed six at 1" OD, 60° apart) | Nick, tape | confirmed |
| Spacer tube positions | on a circle just inside the ring's outer edge. In the model frame (bearings at 0/180, point hole at 270, back holes at 30/150): three across the back between the 30° and 150° holes at roughly 60/90/120; two per side toward the front at roughly 200/240 and 300/340, the pair nearest the point carrying the string eye bolts | overhead photo | read from photo, good to about 10° |
| Point of the top ring | faces the front (eyepiece side); the string eye bolts flank it | photo | likely, confirm when assembled |
| Long struts | **45 mm OD x 40 mm ID aluminium (1.772" x 1.575", 2.5 mm wall)**, 50 1/2" long, plain tube ends (no fittings). Earlier tape/eyeball readings of 1 5/8 and 1 3/4 superseded | Nick, calipers 2026-10-19 | confirmed |
| Strut hole diameter | 45 mm (the 1 5/8" tape reading was wrong; a caliper photo with the outside jaws in the hole reads 43.5 mm, which is 45–46 mm once the jaw tips are added) | Nick, calipers 2026-10-19 | confirmed |
| Top ring top face to mirror face | about 7" (the 3 3/4" photo reading was the tape bending over the baffle, not the glass) | Nick | confirmed, roughly |
| Mirror face to the bottom of the cell (the triangle) | about 3" (glass 1.65" + disc + pads). The model's `cell_depth` of 3.5 counts down to the mirror board; with the springs it is about 7" top ring to mirror face + 3" cell = 10" from the top ring to the cell bottom, leaving about 1 3/8" of spring and board gap above the 11 3/8" inside height | Nick | confirmed, roughly |
| Mirror | 16", centre spot, held in a black baffle tube | photo | confirmed |

## Cell, 2026-10-18, photo

| Item | Value | How | Status |
| --- | --- | --- | --- |
| Mirror | Hubble sandwich, open edge: two glass plates with round glass spacer pucks visible between them | photo | confirmed |
| Stack, top to bottom | mirror; a thin plywood disc about the mirror's diameter (the round plate with three openings seen from behind); the 3/4" ply triangle; springs on 1/4" studs through the mirror board | photo | confirmed |
| Collimation studs | 1/4" (1/4-20 assumed) with compression springs | Nick, photo | confirmed, thread to check |
| Bond | no silicone visible at the edge; Nick can't tell by hand whether the glass moves on the disc | photo, Nick | unresolved; settle it when the cell comes out for the push-pull conversion (lift the glass with the box face-up and a helper, or look for RTV blobs through the disc openings from behind) |
| Pads | not visible; whether the disc sits on nine pads on the triangle or directly on it is unknown | | photo from below through the triangle |

## Effect on the model (dob_model.py re-run 2026-10-18 with the values above)

| Check | Assumed | Measured |
| --- | --- | --- |
| Truss pole length, wide pairs | 30.1" | 38.5" |
| Truss drift horizon to zenith, wide pairs, ideal joints | 0.046 mm | 0.086 mm |
| Same with 20,000 lb/in base joints (narrow pairs) | 0.25 mm | 0.48 mm |
| Mirror face below the altitude axis (balance solve) | 14.6" | 14.3" |
| Eyepiece height at zenith | 60.6" | 62.3" |
| Nested transport height | 19.8" | 13.5" |
| Altitude axis above the rocker floor | 24.7" | 25.9" |

The one real consequence: the box's top ring is 7" below the altitude axis, not 1" above it as assumed, so truss
sockets on stubs at the ring put the base nodes 7" lower and the poles grow from 30" to 38.5". Truss drift roughly
doubles; the total budget is still about 0.3 mm against 0.5 mm. Raising the sockets on taller stubs does not help
(a 7" cantilever of 1 5/8" tube was put at 7,600 lb/in; with the measured 45 × 2.5 mm tube it is about 16,000 lb/in, still in series with the joints). Options are to accept it, go to 1.25"
aluminium or carbon poles, or bridge the sockets to the new bearings. Decision pending.

**Bearing attachment, as built.** The D bearings are located by the long struts: each strut passes through the clamp
block on the bearing's straight edge, so the struts tie the bearings to the box. The struts go away in the rebuild, so
the bearing mounting is a new design regardless (the dowelled 14" D's in the decisions table). The ring's flat-to-flat
width cannot be taped with the bearings on; the width across the two bearings' outer faces gives it.

## Retired 3D-printed upper cage, 2026-10-18, photo

Two printed rings (segmented, shield-shaped like the DobStuff ring) on threaded-rod posts, the Destiny 3-vane
curved spider, and the Feather Touch on a printed focuser board; carried on the 50.5" DobStuff struts. Retired in
favour of the aluminium cage in the model; the spider and focuser carry over.

**cagev11.f3d on main is not the cage.** Opened in the Autodesk Viewer: it holds two small bodies only, "mirror"
(3.6" x 4.4" x 3.6", a tilted secondary) and "eye" (3" x 3.5" x 4.5"), an optical-layout study. The printed cage
design (v12) is not in the repo, so the strut bore has to come from a tape round a strut.
| Point hole centre to the tip of the point | 1 13/16" | Nick, tape | confirmed |
| Derived: tube axis to the point tip (swing radius input) | 12.125" (STEP tip; 10.25 + 1.81 = 12.06 by tape) | computed | agrees two ways |

**Nick's STEP files (2026-10-18).** `wooden_cage.step` models the DobStuff ring: 3/4" thick, 18" ID, 21.5" OD on the
round part, shield sides as 31.4" arcs, 22.9" to the point (real ring taped at 23 3/8"). `cage.step` is the retired
printed cage (ten ring segments on the same outline, four 8" posts, focuser board with a 2.75" hole, 3.5" secondary
holder); its strut clamps are not included, so the strut bore is still unknown. Both kept in the session scratchpad only.
| Box width across the side strips' outer faces, no bearings | 21 11/16" | Nick, tape | confirmed |
| Bearing position, as built | the D rides on the PTFE pads on TOP of the rocker side panels, lip hanging outside the panel; the bearing plane is over the panel (about 11.5" from the tube axis), not inside the 22 1/4" rocker width, which only clears the 21 11/16" box | Nick | confirmed |

**Truss decision (2026-10-18):** 1.25" x 0.062" roll-wrapped carbon poles, wide pairs. FE at 38.5": 0.042 mm ideal
joints (1" Al 0.086, 1.25" Al 0.070), lateral mode 88 Hz. With 20,000 lb/in base joints 0.32 mm, so joint quality
is the whole game; the plugs get bonded into the pole bore. Mirror face 13.9" below the axis, eyepiece 63.5" at zenith.

## Top ring from `wooden_cage.step`, 2026-10-19

Nick's STEP of the DobStuff ring, taken as accurate. Read with CadQuery (`importers.importStep`, circular edges). Angles in the
model frame: bearings on 0/180°, point hole at 90°.

| Item | Value | Status |
| --- | --- | --- |
| Outline | 18" ID, 21.5" OD round part, point tip 12.125" from the centre, point sides are arcs of r 15.7" centred 4.96" behind the centre, 3/4" thick | from the STEP |
| Strut hole pilots (0.26") | back holes at r 10.625" (210° and 330°), point hole at r 10.25" (90°). Back to back 18.5", back to point 18.0" | from the STEP; 18.5" taped, 18.0" to tape |
| Spacer pilots (0.26") | six at r 9.875": 20/40, 140/160, 260/280 (two per side, two at the back). Nick counted seven with three at the back; the seventh is assumed at 270° | from the STEP; seventh to confirm |
| 1" holes | two at r 10.25", 25° either side of the back (205° and 335°); purpose unknown | from the STEP |
| Edge vs 45 mm holes | a 45 mm hole at r 10.625" reaches r 11.51", but the round edge is at r 10.75": breaks out by 3/4" as drawn. The photo shows ply all round the hole, so the as-built ring is wider there | **conflict, measure** |
| Effect on the model | `mcage_tube_radii=(10.25, 10.625, 10.625)`, `mcage_point_radius=12.125`; poles 38.15" to the point socket and 38.20" to the back sockets; pair blocks at 30° and 150° are mirror images; truss FE unchanged (0.042 mm); eyepiece 63.3" | applied |
