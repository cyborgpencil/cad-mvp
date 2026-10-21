# Project 1: Blink camera L-bracket (first end-to-end test case)

Status: spec draft (Doc Steward, 2026-10-21). Erik picked this part; every dimension he hasn't given is **TBD**. Don't guess values. Ask Erik through the chief.

## Part
A 3D-printed L-bracket that fits over the 90° outside corner of a flat door frame, with 3 screw holes in each leg. On top of one leg sits a disc that's the mount point for an older-style Amazon Blink camera base, held by a couple of screws. The user can fillet or chamfer edges interactively.

## Dimensions
| Item | Value | Source |
|---|---|---|
| Units | mm (locked) | requirements |
| Bracket wall thickness | 4 mm | Erik |
| Corner angle | 90° outside | Erik |
| Leg A length × width | TBD | |
| Leg B length × width | TBD | |
| Fit to frame casing (clearance) | TBD | Research Digest: typical casing widths |
| Leg screw holes | 3 per leg; size, countersink and spacing TBD | Research Digest: wood screw sizes |
| Disc thickness | 4 mm | Erik |
| Blink round boss size (diameter, height) | TBD, Erik to measure | |
| Disc diameter | TBD | Research Digest: Blink mount specs |
| Which leg the disc is on, and where | TBD | |
| Disc screw holes | "a couple"; count, size and pattern TBD | Research Digest: Blink base pattern |
| Blink model (XT/XT2 or older Indoor/Outdoor) | TBD | Erik |
| Fillet / chamfer edges and sizes | user choice in app; defaults TBD | Erik |
| Casing width, thickness and profile (colonial casing tapers, so a flat leg may not sit flush) | TBD, Erik to measure | Reference only: US colonial is often 57 x 17.5 mm (research/projects/blink-mount.md) |
| Screw gauge, length and head type | TBD | Proposal only: #6 or #8 wood screw |
| Printed hole oversize | TBD, settle with a test print | |
| Material / printer | TBD | |

## Reference notes (not specs)
- Blink publishes no mount dimensions for the XT, XT2 or Indoor/Outdoor; Erik measures his own base plate (diameter, hole spacing, hole size).
- One mount fits the XT, XT2 and Indoor/Outdoor; the camera snaps onto a round boss (no 1/4-20 thread). The XT2 ships with 2 wood screws.
- The only measured numbers found (36 mm hole spacing, 55 mm disc) are for the newer Outdoor 2K+ mount, a different model. Don't use them as values.

## Test steps (each one must pass)
1. **Sketch:** the L profile on a plane, with units shown as mm.
2. **Extrude** the L to leg width.
3. **Add the disc:** a 4 mm thick circle on the chosen leg, unioned with the bracket.
4. **Holes:** 3 per leg plus the disc screw holes, cut through.
5. **Fillet or Chamfer:** the user picks edges and a size, with undo working.
6. **Watertight and units check:** real check, result shown in the status bar and Export tab; it must be PASS, with volume and bounding box shown.
7. **Export STL and 3MF:** only after step 6 passes. Re-import to confirm it's still watertight and the units and dimensions match.
8. Screenshots of desktop, phone portrait and phone landscape. Each step gets a test (CTest or a scripted UI check).

## Out of scope
FixGaps (TBD for Erik). Anything not listed above.