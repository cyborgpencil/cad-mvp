# Box export

**Status**: Built
**Date**: 2026-10-20
**Scope**: One dimensioned box to binary STL and 3MF. Does not change `mvp/requirements.md`.

`box_mm(width, depth, height)` builds a triangle mesh in millimeters from the origin. The twelve triangles use the same outward order as `closed_box()`. A non-positive size returns no triangles. No tessellator is used.

As built (2026-10-20), `export_mesh_if_closed` runs `check_watertight` and writes `box.stl` and `box.3mf` only when it passes. Current rule (Erik, 2026-10-22 02:17 MT): watertight checks and tests are dropped. The units (mm) check stays and gates Export. The OCCT shape-validity check after operations stays, but it does not block Export. A watertight pass is no longer required to export. An empty mesh (no triangles) or a signed volume at or below 1e-9 mm3, including an inside-out shell, also blocks the write. `check_watertight` is still stored on the attempt and does not decide the write by itself.

Binary STL coordinates are millimeters. The 80-byte header says so and does not start with `solid`. Reading that STL keeps three vertices per triangle and does not weld them, so the index-based checker was the pre-export gate in this build (legacy).

3MF is a stored ZIP of `[Content_Types].xml`, `_rels/.rels`, and `3D/3dmodel.model`. The model `unit` is `millimeter` from `ExportUnitRecord`. lib3mf is not used.

`export_box` writes the 20 × 20 × 20 mm box under `builds/export/` when started from the repo. `solid_view` keeps the three fixtures. **20 mm box** writes the same files, reads the STL back, frames that mesh, and shows the checker sentence.
