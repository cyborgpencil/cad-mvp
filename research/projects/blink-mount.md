# Blink camera mount + door-casing bracket: research digest (2026-10-21)

For `mvp/projects/blink-l-bracket.md`. Official = Blink/Amazon. Measured = community, unofficial. TBD = Erik measures.

## 1. Blink mount (XT, XT2, Indoor/Outdoor gen 2/3)
- XT: ships with 1 mounting bracket + 1 screw. The mount plugs into the round opening in the battery cover and has a hinge with side thumb screws. Official: https://support.blinkforhome.com/en_US/mounting-your-blink-xt
- XT2: ships with mount + mount riser + 2 wood screws. Riser holes line up with the mount. Camera snaps on: the mount's circle goes into the center circle on the camera back. Official: https://support.blinkforhome.com/en_US/xt-camera-setup-guide ; FCC quick start: https://fccid.co/api/files/s1/2af77_h1981653_usersmanual_4589197_3aa9131452.pdf
- No anchors are included. The screws are for wood only. Official: https://support.blinkforhome.com/en_US/xt2-and-xt-technical-specifications
- Amazon 3-pack mount (B07PTMRBWH): 3 mounts + 6 screws (2 per mount). Fits the new Indoor, Outdoor, XT2, XT and gen-1 Indoor, so it is one shared stock mount. Official: https://www.amazon.com/dp/B07PTMRBWH
- Attachment: snap-fit, NOT a 1/4-20 thread and NOT a user ball joint (per Blink's pages above). A third-party snap-on adapter converts it to 1/4-20 female, 30.48 mm / 1.20 in dia x 8.89 mm / 0.35 in thick (unofficial): https://www.batteryeliminatorkits.com/product-p/bcma-1.htm
- Measured, unofficial: Outdoor 2K+ mount has 36 mm (1.42 in) hole spacing and a 55 mm (2.17 in) disc. The author used M3/M4, and M4 needed the stock holes drilled out to 4 mm. That is a newer model, so don't assume it matches the XT/XT2. https://makerworld.com/en/models/2961340-blink-outdoor-camera-45-degree-mount
- XT2 mount remix "with original drill holes" (no spacing published; check the STL in CAD): https://www.printables.com/model/440400-blink-xt2-mount
- XT/XT2 bracket system used #6 pan-head wood screws about 1 in (25.4 mm) long between its own printed parts (unofficial): https://www.thingiverse.com/thing:3084995
- No source gives an official base-plate diameter, hole spacing, or screw gauge/length for XT/XT2/Indoor/Outdoor.
- TBD (Erik measures with calipers): stock base diameter, base thickness, hole count (2 expected), hole center spacing, hole diameter and countersink, supplied screw diameter/length/head, and which Blink model Erik has.

## 2. US door casing (millwork)
- WM 356 colonial: 11/16 x 2-1/4 in = 17.5 x 57.2 mm (Lowe's lists actual 0.6875 x 2.25 in). https://www.lowes.com/pl/moulding/window-door-moulding/casing/colonial/3163521573-4294517664-4294815071
- 2-1/2 in (63.5 mm) casings at 11/16 in (17.5 mm): WM 315/351/452. Some 2-1/2 in profiles are 9/16 in (14.3 mm), e.g. 472. 3-1/4 in (82.6 mm): 445. 3-1/2 in (88.9 mm): 444, 412. 1-1/16 in (27 mm) thick: DC97, 470. https://www.colonialsnd.com/wp-content/uploads/2015/05/2013-Mid-Atlantic-Profile-Guide.pdf ; https://wm.triath.com/resources/WM-Profile-Book.pdf
- WM 444 is 0.688 x 3.5 in (17.5 x 88.9 mm), finger-joint pine. https://www.homedepot.com/p/330750524
- 2-1/4 in is the standard width, and anything over 3-1/2 in is custom. https://www.angi.com/articles/door-casing-sizes.htm
- Colonial casing tapers and is thinner at the edge, so the bracket won't sit flat on its full face.
- TBD: Erik's actual casing width, thickness, profile, and edge thickness on both corner faces. "Flat door frame" might mean flat stock (e.g. 1x4) rather than moulding. Confirm.

## 3. Screws into wood trim
| Gauge | Shank | Pilot softwood | Pilot hardwood | Clearance (printed hole) | 82° csk dia |
|---|---|---|---|---|---|
| #6 | 0.138 in / 3.5 mm | 5/64 in / 2.0 mm | 3/32 in / 2.4 mm | 9/64 in / 3.6 mm | 17/64 in / 6.7 mm |
| #8 | 0.164 in / 4.2 mm | 5/64-7/64 in / 2.0-2.8 mm | 7/64-1/8 in / 2.8-3.2 mm | 11/64 in / 4.4 mm | 5/16 in / 7.9 mm |
Sources: https://theplanstack.com/fasteners/pilot-hole-chart/ (NDS 2018 Table L3) ; https://drilltable.feijoalabs.com/pilot-hole-chart.html (DIY charts run 1 size larger) ; https://www.engineeringtoolbox.com/wood-screws-holes-d_1519.html
- Pilot holes matter near ends and edges because they prevent splitting there (planstack). Casing is narrow, so drill pilots.
- Fine-thread screws are recommended for MDF casing (whatdrillbit): https://whatdrillbit.com/pilot-hole-chart.pdf
- Length: with a 4 mm bracket into 11/16 in (17.5 mm) casing, the screw is plate + casing depth. No sourced rule found for thin trim. TBD: Erik picks a length, and it must not go through the casing. A 5/8-3/4 in (16-19 mm) screw would be a derived guess only.
- Head: countersunk head needs a printed 82° countersink (diameter above). Pan head needs a flat seat. Choice TBD.
- Printed clearance: the chart values are for drilled holes. FDM holes print undersize, so compensation is TBD and should be checked with a test print.

## Official vs measured
Official: kit contents, snap-fit attachment, wood screws, mount compatibility. Measured/unofficial: 36 mm/55 mm (Outdoor 2K+ only), adapter 30.48 mm, #6x1 in hobby use. Mount geometry for XT/XT2/gen 2-3 is unknown, so all of it is TBD.
