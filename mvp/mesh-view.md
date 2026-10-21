# Desktop mesh view

**Status**: Built and checked on 2026-10-20
**Scope**: Qt window over the existing watertight checker. Does not change `mvp/requirements.md`.

## What this is

`solid_view` shows one triangle mesh, the checker's own sentence, and three fixture buttons.

`mvp/requirements.md` has no GUI section. Creation tools, the units toggle, and edge selection are recorded in [create-export.md](create-export.md).

## Window

- Buttons: Closed box, Open box, Flipped box. Closed box is selected when the window opens.
- The viewport fills the center.
- The line under the viewport is `check_watertight(...).message` unchanged.

The view uses the fixture coordinates as stored. Z is up. The camera starts at a front-top-right view of the unit box. Left drag orbits. Right drag pans. The scroll wheel zooms. A left click selects the nearest edge. Front faces are gray. Back faces are orange. Edges are drawn.

Sketch, Solid, and Inspect sit on the top row. The left tree is the browser. The list under the view is the timeline. The right panel is properties, with Millimeters / Inches and the measure readout. Closed box is still selected when the window opens, and the result line is still the checker sentence.

`open_box` has no top face, so the starting view looks through that opening at the orange inside of the bottom. `flipped_box` reverses a bottom triangle. That orange triangle is on the underside, so the starting picture matches the closed box. The result line is the check. Orbit down to see the orange face.

## Checker boundary

`solid_view` links `solid` and includes `src/solid/fixtures.hpp`. These files were not edited:

- `src/solid/mesh.hpp`, `src/solid/mesh.cpp`
- `src/solid/watertight.hpp`, `src/solid/watertight.cpp`
- `src/solid/fixtures.hpp`
- `src/check_solid.cpp`
- `tests/test_watertight.cpp`

## Build

Qt 6.8.3 MSVC 64-bit is installed at `C:\Qt\6.8.3\msvc2022_64`. CMake adds `solid_view` when Qt 6 Widgets and OpenGLWidgets are found. The prefix used here was `C:/Qt/6.8.3/msvc2022_64`. `solid`, `check_solid`, and `test_watertight` still configure when Qt is absent.

Built with MSVC 19.51 and the existing NMake build in `builds/solid-check`. CTest `watertight` passed. The window was launched and Windows UI Automation read:

```text
closed_box: PASS: closed triangle mesh, every edge shared by two triangles, outward winding, no zero-area triangles.
open_box: FAIL: edge (4,5) is shared by 1 triangle (need 2).
flipped_box: FAIL: edge (0,1) is wound the same way by two triangles.
```

Screenshots of the three states showed the closed box, the open top, and the flipped box with its result line.

## Out of this slice

Units, healing, import, export, measurements, selection, snapping, OpenCASCADE, and the Manifold library.
