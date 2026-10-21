# Box export

**Status**: Built
**Date**: 2026-10-20
**Scope**: One dimensioned box to binary STL and 3MF. Does not change `mvp/requirements.md`.

`box_mm(width, depth, height)` builds a triangle mesh in millimeters from the origin. The twelve triangles use the same outward order as `closed_box()`. A non-positive size returns no triangles. No tessellator is used.

`export_mesh_if_closed` runs `check_watertight`. It writes `box.stl` and `box.3mf` only when that check passes. A failure does not create the directory.

Binary STL coordinates are millimeters. The 80-byte header says so and does not start with `solid`. Reading that STL keeps three vertices per triangle and does not weld them, so the index-based checker stays the pre-export gate.

3MF is a stored ZIP of `[Content_Types].xml`, `_rels/.rels`, and `3D/3dmodel.model`. The model `unit` is `millimeter` from `ExportUnitRecord`. lib3mf is not used.

`export_box` writes the 20 × 20 × 20 mm box under `builds/export/` when started from the repo. `solid_view` keeps the three fixtures. **20 mm box** writes the same files, reads the STL back, frames that mesh, and shows the checker sentence.
