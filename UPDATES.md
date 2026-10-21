# Project Updates Log

**Purpose**: Quick chronological record of changes so anyone (or future-you) can see what moved without reading every file.  
Newest entries at the top.

## 2026-10-21

- Research Digest checked every volume formula in `mvp/test-matrix.md` (no corrections needed), added per-row measurement methods, failure reasons for coplanar, tiny-feature, thin-wall, and curved cases, proposed tolerances derived from mesh chord error (needs Erik's sign-off), and a Sources section.
- Recorded the agreed push cadence in `AGENTS.md`. Corrected the internal-void note in `mvp/test-matrix.md`: the Qt run's 23536.9 mm3 comes from fillet-then-cut, not a defect. Added row O5b (filleted internal void, 23538.74 mm3) and marked chamfer, sphere, cone, and intersect as test-only until Erik confirms scope.

## 2026-10-20

- Added `mvp/test-matrix.md`: 9 shape and 12 operation cases on OpenCASCADE, each exported to STL and 3MF and checked for watertight, volume, bounding box, `unit="millimeter"`, and Orca read-back. Tolerances and tiny-feature behavior are TBD. Chamfer, sphere, cone, and intersect need Erik to confirm they are in scope.
- Re-check after Grok Build's create-to-export run (finished 11:47 PM MT, goal marked achieved), run by Grok Build Pilot at 11:55 PM MT: the MSVC/NMake build passed, CTest passed 4 of 4 (watertight, units, export, create), and the CLI `export_part` wrote `box.stl` and `box.3mf`. Watertight: `check_solid` exited 0, and OrcaSlicer reports manifold yes for both files at 40 × 30 × 20 mm, with 2 parts (the outer solid plus the closed interior void). Units: the 3MF carries `unit="millimeter"` and the units test passed. Logs are in `builds/logs/20261020-2355-*`.
- Files that run changed: edits to `CMakeLists.txt`, `UPDATES.md`, `mvp/mesh-view.md`, `research/occt-wasm/README.md`, and `src/gui/main_window.*` and `mesh_view.*`. New files: `mvp/create-export.md`, `mvp/export.md`, `mvp/units.md`, `src/export/`, `src/export_box.cpp`, `src/export_part.cpp`, `src/model/`, `src/units/`, and `tests/test_create.cpp`, `test_export.cpp`, `test_units.cpp`. Also new: `prompts/wasm-occt-core.md`, the prompt for the next headless WASM + OCCT 8.0.1 session (Chrome on Windows, Android, and iPhone; mm with an inch toggle; STL/3MF only).
- Open doc issue: the "Published the initial tree to GitHub" entry below doesn't match `git status`, which shows branch `main` with no commits yet. That entry needs to be confirmed or corrected.
- Fillet now rejects every box edge except the one along X at minimum Y and maximum Z, before it builds a mesh. Edges 1–2 and 3–7 of a 40 × 30 × 20 mm box no longer come back as swapped 30 × 20 × 40 or 20 × 40 × 30 solids. `test_create` keeps that box unchanged.
- Drove `solid_view` through a 40 × 30 × 20 mm box, a 3 mm fillet, and an interior cut. The on-screen checker line stayed PASS, the inch toggle scaled the spin readouts by 25.4, and the exported STL/3MF stayed 40 × 30 × 20 mm. OrcaSlicer reports `manifold = yes` and two shells (outer solid plus the closed void). Note: `mvp/create-export.md`.
- Added the create-to-export mesh path: box, cylinder, XY sketch (line, rectangle, circle, distance, radius, horizontal, vertical, coincident), one-direction extrude, union, cut, and a constant-radius fillet on one box edge. `repair_manifold` rechecks with the existing watertight checker and blocks export when it cannot repair. `solid_view` adds Sketch, Solid, and Inspect, a browser, a timeline, and a properties panel with the millimeters/inches toggle. Contract: `mvp/create-export.md`.
- Added a 20 mm box export. `export_box` writes binary STL and 3MF under `builds/export/` only after `check_watertight` passes. `solid_view` keeps the three fixtures and adds **20 mm box**, which loads that STL and shows the checker sentence. Contract: `mvp/export.md`.
- Added the units lock in `src/units`. Stored lengths stay millimeters. The display toggle converts by 25.4 and does not scale stored numbers. `ExportUnitRecord` keeps STL/3MF coordinates in millimeters. Checker sources and `solid_view` were not edited. Contract: `mvp/units.md`.
- Published the initial tree to https://github.com/cyborgpencil/cad-mvp. README points at `mvp/requirements.md` and states millimeters with an inch switch, the Qt GUI, and the required watertight check. Added the LGPL-2.1 `LICENSE` and C++/Qt/CMake ignore rules.
- Added `solid_view`, a Qt 6.8.3 window that draws a fixture mesh and shows the existing watertight sentence. Checker sources were not edited. CTest `watertight` passed. UI Automation read the closed, open, and flipped result lines. Contract: `mvp/mesh-view.md`.
- Built the watertight check with MSVC 19.51 (Visual Studio Community 2026, NMake). CTest `watertight` passed. `check_solid` exited 0 and printed pass for the closed box, a boundary failure for the open box, and a winding failure for the flipped box.
- Added the first code slice: in-memory triangle mesh and watertight check (`src/solid`, `src/check_solid.cpp`, `tests/test_watertight.cpp`, `CMakeLists.txt`). Contract: `mvp/solid-check.md`. A throwaway Python mirror of the same rules produced the expected pass/fail lines. The C++ was not compiled: Visual Studio Community 2026 is installed, and its C++ toolset is not.
- Created general reusable skill `.grok/skills/tooling-priority/` (SKILL.md + evals) for prioritizing Grok Build → Cursor → Grok Bots across any project.
- Added reusable prompt `prompts/tooling-priority.md`.
- Updated `mvp/tooling-priority.md` to reference the skill.
- Added MVP software engineer prompt at `prompts/mvp-software-engineer.md` (design-to-print scope only).
- Created `project-organizer` skill at `.grok/skills/project-organizer/SKILL.md` for correct file placement and structure.
- Existing `document-upgrader` skill remains for content consistency.


- Created separate `mvp/` and `vision/` folders.
- Added `mvp/requirements.md` (design-to-print MVP with healing, units, validation, MCP).
- Added `vision/full-project.md` (post-MVP goals, kept independent).
- Added `ORGANIZATION.md` with folder rules.
- Updated `research/INDEX.md` with links to MVP and vision docs.
- Created `document-upgrader` skill for consistent doc maintenance.
- Initial research knowledge base populated under `research/`.

> [!TIP]
> When making significant changes, add a short bullet here and (if relevant) a note in the affected document.  
> Use the document-upgrader skill for research or requirements updates.
