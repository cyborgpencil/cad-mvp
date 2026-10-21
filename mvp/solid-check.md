# In-memory watertight check

**Status**: Built and tested with MSVC 19.51 on 2026-10-20
**Date**: 2026-10-20
**Scope**: First MVP slice only. Triangle mesh in memory. Does not change `mvp/requirements.md`.

## What this is

A C++17 static library, `solid`, plus the console program `check_solid`. The desktop window `solid_view` calls `check_watertight` and does not change this checker. See `mesh-view.md`.

- `MeshSolid` stores vertices (`double` x, y, z) and triangles (three indices).
- `check_watertight` returns `pass` and one message. The first failing rule stops the check.
- Positions have no unit. The unit lock is still TBD.

## Rules, in order

1. The mesh must contain at least one triangle, and every index must refer to a vertex.
2. A triangle with a repeated index fails. A triangle whose cross product is exactly `(0, 0, 0)` fails. There is no area epsilon.
3. Each undirected edge must be shared by exactly two triangles. The message names the lexicographically smallest failing pair and the count. Count 1 is a boundary. Count greater than 2 is non-manifold.
4. Each directed edge must appear once, so the two triangles wind in opposite directions. The message names the lexicographically smallest directed edge that appears more than once.
5. Outward winding means a positive triple sum, `Σ v0 · (v1 × v2)`. The sum is not divided by 6, so an exact zero stays exact. A negative sum fails as inward. An exact zero fails as zero volume.

Pass message:

`PASS: closed triangle mesh, every edge shared by two triangles, outward winding, no zero-area triangles.`

## Fixtures

Built in `src/solid/fixtures.hpp` and printed by `check_solid`.

| Fixture | Shape | Expected line |
|---------|--------|----------------|
| `closed_box` | 8 corners, 12 triangles, right-hand outward | the pass message |
| `open_box` | same box with the `z = 1` face removed | `FAIL: edge (4,5) is shared by 1 triangle (need 2).` |
| `flipped_box` | closed box with triangle 0 reversed | `FAIL: edge (0,1) is wound the same way by two triangles.` |

`check_solid` prints those three lines. It exits 0 when every line matches the table. The open and flipped lines are expected failures, so a successful run still prints `FAIL` for them.

## Other cases covered by `tests/test_watertight.cpp`

- No triangles.
- Vertex index past the vertex list.
- Repeated vertex index.
- Exact zero area.
- One edge shared by 3 triangles: `FAIL: edge (0,1) is shared by 3 triangles (need 2).`
- Every triangle of the closed box reversed: `FAIL: winding is inward (signed volume is negative).`

The zero-volume branch has no fixture. A non-degenerate closed mesh with an exact zero triple sum was not specified.

## Out of this slice

B-Rep, OpenCASCADE, ShapeFix, the Manifold library, STL, 3MF, STEP, units, healing, and vertex-manifold or self-intersection tests.

## Build

`CMakeLists.txt` defines `solid`, `check_solid`, and CTest target `watertight`. No third-party libraries.

Built with Visual Studio Community 2026, MSVC 19.51.36247, CMake, and the NMake generator. Output is in `builds/solid-check`. CTest `watertight` passed. `check_solid` exited 0 and printed:

```text
closed_box: PASS: closed triangle mesh, every edge shared by two triangles, outward winding, no zero-area triangles.
open_box: FAIL: edge (4,5) is shared by 1 triangle (need 2).
flipped_box: FAIL: edge (0,1) is wound the same way by two triangles.
```

## Assumptions

- A watertight solid here is an edge-manifold triangle mesh with outward winding, as already required for meshes in `research/formats/validation.md`.
- The smallest index pair is the edge named when several edges fail the same rule.
- Vertices that land on the same point under different indices are not welded.

## Open questions

- Unit lock (millimeter or inch), tessellation tolerances, and whether repair should be our code, OCCT ShapeFix, or Manifold.
