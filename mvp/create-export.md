# Create to export

**Status**: Built
**Date**: 2026-10-20
**Scope**: Mesh creation, the Qt test-harness panels, manifold repair, and STL/3MF export, as built on 2026-10-20. Does not change the legacy mesh checker.

> Current rule (Erik, 2026-10-22 02:17 MT): watertight checks and tests are dropped. The units (mm) check stays and gates Export. The OCCT shape-validity check after operations stays, but it does not block Export. The PASS-sentence export condition below describes the 2026-10-20 build; it is no longer the rule.

`mvp/common-tools.md` is not in this tree. This note follows [requirements.md](requirements.md).

## What is implemented

OpenCASCADE is not installed. Solids are triangle meshes. Every stored coordinate is millimeters.

- Box and cylinder (`box_mm`, `cylinder_mm`). Dimensions entered in the properties panel are converted with `UnitLock` and stored in millimeters.
- Sketch on the XY plane: Line, Rectangle, Circle, Distance, Radius, Horizontal, Vertical, and Coincident. Finish Sketch runs 40 relaxation passes. Extrude moves +Z by one distance.
- Union. Overlapping axis-aligned boxes become one rectilinear shell. Any other pair is appended.
- Cut. Two boxes use that cell difference. A box cutter strictly inside another closed mesh becomes an interior void shell.
- Constant-radius fillet on the box edge that runs along X at minimum Y and maximum Z. The GUI uses the edge selected in the view.
- `repair_manifold` welds identical vertices, drops degenerate triangles, and flips an inward shell, then calls `check_watertight` again. A mesh that is still open returns `cannot repair: ` plus the checker sentence. That path does not write files.
- As built, export wrote binary STL and 3MF only after the checker PASS sentence (legacy; the current gate is the units check). STL coordinates are millimeters. The 3MF model `unit` is `millimeter`.
- `solid_view` keeps Closed box, Open box, Flipped box, and 20 mm box. It adds Sketch, Solid, and Inspect, a left browser, a bottom timeline, and a right properties panel. The panel toggles millimeters and inches by 25.4 and does not scale stored vertices. The measure readout uses the current display unit. Left drag orbits, right drag pans, the wheel zooms, and a left click selects the nearest edge of the hit triangle. The window opens on the closed box and shows that fixture's checker sentence.

## Deferred

- A general constraint solver. Sketch solving is only the relaxation pass above.
- Revolve and chamfer.
- Fillet on any edge other than the box edge along X at minimum Y and maximum Z. Other edges return `cannot fillet: choose the box edge along X at minimum Y and maximum Z.`
- General mesh booleans beyond the box grid and the interior box void.
- OpenCASCADE solids.

## Sample part

1. Solid tab. Width 40, Depth 30, Height 20, Fillet 3. Click Box.
2. Click the top edge along X at Y = 0. Click Fillet.
3. Width 8, Depth 8, Height 6, X 16, Y 12, Z 7. Click Box, then Cut.
4. The result line is the checker PASS sentence. Export STL + 3MF writes `builds/export/box.stl` and `builds/export/box.3mf`.

`build_demo_part` builds that solid. `export_part` writes it through the same export gate.

## Slicer check

OrcaSlicer `--info` on the exported STL and 3MF reports `size_x/y/z` of 40, 30, and 20, `manifold = yes`, and `number_of_parts = 2`. The second part is the closed interior void from the cut, not an open edge. The reported volume is the filleted box minus that pocket (about 23537), which is smaller than the unfilleted pocketed box (23616). The 3MF file stores `unit="millimeter"` and vertices from the origin. Orca recenters that same 40 × 30 × 20 mm extent when it prints the 3MF bounds. The properties toggle rewrites the spin boxes by 25.4 and does not scale this export.
