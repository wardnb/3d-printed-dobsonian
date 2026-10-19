# DobStuff 16" strut kit: what the blog shows

Crawled 2026-10-18 from dobstuff.blogspot.com (Dennis Steele, closed 2024-12-31). All 1381 posts were indexed
and the images from 219 kit-related posts (502 files) were saved to `~/Documents/dobstuff-blog-archive/`
(`posts_index.md`, `posts_full.json`, `img/`). Nick's own 2022 kit never appeared on the blog (2022 has
twelve posts, none about it; the "Nick" posts are other customers with a 13.1" and a 14"). The nearest
siblings, which share the same design, are:

| Post | Why it matters |
| --- | --- |
| [A 16" Strut Kit for Matt (2019-08-23)](https://dobstuff.blogspot.com/2019/08/a-16-strut-kit-for-matt-in-hillsborough.html), [Matt's 16" Strut Kit (08-27)](https://dobstuff.blogspot.com/2019/08/matts-16-strut-kit.html), [Completed (08-31)](https://dobstuff.blogspot.com/2019/08/matts-16-strut-kit-completed.html) | Same product as Nick's: a 16" strut *kit* (customer supplies mirror, cell, focuser, spider). Shows the top ring with its three strut holes, the altitude-bearing clamp block, 24" altitude bearings, the rocker side blank. |
| [Chuck's 16" String-Strut (2020-02-28)](https://dobstuff.blogspot.com/2020/02/chucks-16-string-strut-9999-complete.html) | Best assembled 16" strut views: struts clamped at the bearing tops, mirror board from behind, strings, ETT ring. |
| [Al's 16" F3.9 Strut (2020-08-18 to 08-26)](https://dobstuff.blogspot.com/2020/08/and-als-16-f39-strut-telescope.html) | Same focal ratio as Nick's Hubble mirror; mirror board with two fans; Feather Touch on the ring. |
| [Dan's 17.5" F4.5 Strut Completed (2021-04-26)](https://dobstuff.blogspot.com/2021/04/dans-175-f45-telescope-completed.html) | Closest in date to a 2022 kit; clear photos of strut collars on the top ring, cell plate and knobs from behind, rocker and ground board. |
| [A 16" Truss Kit for Daniel (2023-10-23)](https://dobstuff.blogspot.com/2023/10/a-16-truss-kit-for-daniel.html) | The 16" 9-point non-flotation cell plate and mirror board, bare, on the bench. |
| [From Ron and his 16" Dobstuff: GOTO (2023-05-07)](https://dobstuff.blogspot.com/2023/05/from-ron-and-his-16-dobstuff-goto.html) | SiTech conversion of the same scope family. |

## Kit anatomy as built by DobStuff (strut variant)

**Mirror box.** Not a conventional box. It is a wide plywood "mirror board" at the bottom (shield-shaped
plate with a round cutout for the cell), a wide plywood ring at the top, and the two altitude bearings
closing the sides. The three 1.25" aluminium struts pass through holes in the top ring and run down to
the mirror board. On the 16" and 17.5" scopes the top ring has three strut holes: two near the bearing
sides and one at the back, not three evenly spaced holes clear of the bearings.

**Strut clamps.** Each altitude bearing carries a split wooden block with a 1.25" bore and a knob on its
straight top edge ("altitude bearing clamp" in Matt's kit). The two bearing-side struts pass through these
blocks and are clamped there, so the bearings are located by the struts as much as by the wingnut bolts
into the box. Nick's own photo (`images/dob_v1.jpg`) shows exactly this: a strut passing through a knobbed
block at the top of each D.

**Cell.** The 16" 9-point non-flotation cell is a triangular plate (aluminium on most, plywood on Daniel's
2023 kit) with nine pads at Plop positions, hung on three spring-loaded knobs through the mirror board.
Dennis bonded every mirror he built to its cell with silicone ("no clamps, just a bit of silicone at 120°
intervals", 24 h to cure, "two weeks" for the 20"), and kit cells ship with a tube of RTV. A kit builder
following his instructions ends up with a bonded mirror, so Nick's is most likely silicone-bonded; this is
the "keep the cell, no sling" branch of the cell decision. Confirm by looking for RTV blobs between the
mirror back and the pads.

**Fans.** Mirror boards carry one or two 80 mm fans in the cell's lightening holes.

**Altitude bearings.** Laminated plywood D shapes with a lightening cutout, Ebony Star on the curved rim,
riding on PTFE pads at the top of the rocker sides. Matt's 16" kit used 24" diameter bearings (12" radius);
Tom's 12.5" used 21". The model assumes 14" radius for the *rebuilt* bearings, which is a design choice,
but the as-built radius sets today's rocker height and the nested transport height.

**Rocker.** A rectangular plywood box: two tall sides with the cradle arc and three lightening holes, a low
front, a floor, and a round ground board with three feet and a central azimuth bolt. The mirror box nests
inside the rocker for transport ("Easy Transport Telescope", ETT, when ordered, also halves the struts with
an intermediate ring; Nick's photo shows full-length struts, so no ETT).

**Upper ring.** A single plywood ring. The struts terminate in blocks under the ring with knobs. Strings
between the struts and the ring were Dennis's rigidity fix ("string-strut").

**Ron's GoTo.** A flexible plastic gear rack glued around the rim of a full-radius altitude bearing, driven
by a servo pinion on a bracket on the rocker side; same arrangement underneath for azimuth; SiTech
controller, battery hung on the rocker. This is the "gear and rack" CLAUDE.md cites. It confirms the
rim-drive approach but note his bearing was full-radius, not a detachable D.

## Implications for the model, ranked by how much they change

1. **`mcage_tube_angles` (90, 210, 330) is probably wrong.** The comment in `dob_model.py` says the
   tubes must clear the side panels at 0/180. On the real kit two tubes sit *at* the bearing sides, clamped
   in the bearing blocks, and the third sits at the back. The truss model puts its three base sockets on
   stubs of these tubes, so the whole wide-pair layout (pair blocks at 30/150/270, sockets at 90/210/330)
   depends on this angle. Do not re-run `truss_fe.py` for the truss layout until the holes are measured.
   If the holes really are at the bearing plane, the options are: keep two stubs there and move the third,
   or abandon the stub idea and bolt three new sockets to the top ring at the chosen angles.
2. **The side panels do not exist as separate parts.** The bearings *are* the sides. The rebuilt 14" D
   bearings therefore need their own attachment to the box (the dowel plan in the decisions table) and
   the box needs something structural where the old bearings used to close it.
3. **Cell is most likely bonded.** Takes the sling off the table and makes the push-pull conversion the
   only cell work. Verify before ordering anything.
4. **Rocker and ground board.** The model's round rocker floor (`rocker_disc_dia`) is a new-design choice;
   the existing rocker is a box on a round ground board. Nothing to change until the az ground ring is
   detailed.
5. **Bearing radius today is probably 12", not 14".** Affects only the as-is transport height check.

## What to photograph (phone is fine, shoot square-on, put a tape measure in frame)

1. Mirror box from directly above the top ring, bearings in frame: shows all three strut holes and the
   bearing clamp blocks. A tape across the ring diameter lets me scale it.
2. Each side of the box: the D bearing, its clamp block, and every wingnut or bolt that attaches it.
3. The back: mirror board, cell plate, the three knobs, fans.
4. Mirror edge, close, looking for silicone between the mirror back and the pads.
5. The box nested in the rocker, and the rocker alone from the front and from one side, plus the
   ground board underneath.
6. Upper ring from above and from below: strut blocks and knobs, spider, focuser bracket.
7. One strut: both ends, and the ring hole it passes through.
8. The whole scope assembled, from the side, bearings level.

## What to measure

Replace every ASSUMED value in `goto-rebuild/dob_model.py` and the open list in `CLAUDE.md`.

**Top ring**
- OD, ID, thickness (count laminations).
- Strut hole diameter and the radius from ring centre to each hole centre.
- Hole angles: measure the three centre-to-centre chord distances between the holes and the distance from
  each hole centre to the bearing's flat (or to the bearing bolt line). I'll solve the angles.
- Distance from the ring's top face to the mirror face (sets `mcage_top_above_axis` once the axis is known).

**Struts**
- Tube OD, wall, length, and how far each one stands above the ring when clamped.

**Altitude bearings**
- Radius (measure chord and sagitta if the arc is partial), thickness, width of the Ebony Star band.
- Height of the arc centre above the mirror face (this is the altitude axis).
- Bolt pattern into the box and the clamp block position relative to the arc centre.

**Mirror board and cell**
- Board outline (width, height, thickness) and the cell cutout diameter.
- Knob bolt circle, bolt thread (expected 5/16-18 or 1/4-20), spring free length.
- Whether the mirror is bonded; mirror diameter and edge thickness; centre spot present.
- Depth from mirror face to the back of the board (`cell_depth`).

**Rocker and ground board**
- Rocker inside width, side height, floor size; angle positions of the PTFE pads; ground board diameter
  and the radius to the three feet.

**Upper ring and focuser**
- OD, ID, thickness; strut block positions; FTF2015 base bolt circle and hole size.

**Weights and forces**
- Bathroom scale: mirror box with mirror, upper ring with focuser and spider, one strut, one bearing.
- Luggage scale: force to start motion on each axis, at the eyepiece and at the rim.
