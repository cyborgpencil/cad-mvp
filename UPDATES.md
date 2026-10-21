# Project Updates Log

**Purpose**: Quick chronological record of changes so anyone (or future-you) can see what moved without reading every file.  
Newest entries at the top.

## 2026-10-21

- Research Digest reworded `research/gui/README.md` (feasibility, scope conflict 6, next step 1) per Erik's rule: OCCT fillet/chamfer/cut/extrude would sit alongside the existing mesh code, not replace it; existing tests and values including O5b stay; post a reason in the room before changing existing code.
- Research Digest filled four `mvp/gui-plan.md` TBDs with sourced proposals needing Erik's sign-off: sketch solver (PlaneGCS WASM), rendering stack (three.js + camera-controls + three-mesh-bvh), screenshot tool (Playwright), and inset feasibility (`BRepOffsetAPI_MakeOffset` + `BRepAlgoAPI_Splitter`). Pixel-diff tolerance and other TBDs unchanged.
- Research Digest added `research/gui/README.md`: sourced GUI reference (Fusion layout, Blender ops with B-rep/OCCT equivalents, three.js parts and licenses, PlaneGCS/SolveSpace solvers, Pointer Events input, Playwright screenshot tests) and 7 scope conflicts for Erik. Indexed in `research/INDEX.md`.
- Research Digest checked every volume formula in `mvp/test-matrix.md` (no corrections needed), added per-row measurement methods, failure reasons for coplanar, tiny-feature, thin-wall, and curved cases, proposed tolerances derived from mesh chord error (needs Erik's sign-off), and a Sources section.
- Recorded the agreed push cadence in `AGENTS.md`. Corrected the internal-void note in `mvp/test-matrix.md`: the Qt run's 23536.9 mm3 comes from fillet-then-cut, not a defect. Added row O5b (filleted internal void, 23538.74 mm3) and marked chamfer, sphere, cone, and intersect as test-only until Erik confirms scope (merged Research Digest's duplicate note; 3T set this interim, not Erik).

## 2026-10-20

- Added `mvp/test-matrix.md`: 9 shape and 12 operation cases on OpenCASCADE, each exported to STL and 3MF and checked for watertight, volume, bounding box, `unit="millimeter"`, and Orca read-back. Tolerances and tiny-feature behavior are TBD. Chamfer, sphere, cone, and intersect need Erik to confirm they are in scope.
- Re-check after Grok Build's create-to-export run (finished 11:47 PM MT, goal marked achieved), run by Grok Build Pilot at 11:55 PM MT: the MSVC/NMake build passed, CTest passed 4 of 4 (watertight, units, export, create), and the CLI `export_part` wrote `box.stl` and `box.3mf`. Watertight: `check_solid` exited 0, and OrcaSlicer reports manifold yes for both files at 40 ÃƒÆ’Ã¢â‚¬â€ 30 ÃƒÆ’Ã¢â‚¬â€ 20 mm, with 2 parts (the outer solid plus the closed interior void). Units: the 3MF carries `unit="millimeter"` and the units test passed. Logs are in `builds/logs/20261020-2355-*`.
- Files that run changed: edits to `CMakeLists.txt`, `UPDATES.md`, `mvp/mesh-view.md`, `research/occt-wasm/README.md`, and `src/gui/main_window.*` and `mesh_view.*`. New files: `mvp/create-export.md`, `mvp/export.md`, `mvp/units.md`, `src/export/`, `src/export_box.cpp`, `src/export_part.cpp`, `src/model/`, `src/units/`, and `tests/test_create.cpp`, `test_export.cpp`, `test_units.cpp`. Also new: `prompts/wasm-occt-core.md`, the prompt for the next headless WASM + OCCT 8.0.1 session (Chrome on Windows, Android, and iPhone; mm with an inch toggle; STL/3MF only).
- Open doc issue: the "Published the initial tree to GitHub" entry below doesn't match `git status`, which shows branch `main` with no commits yet. That entry needs to be confirmed or corrected.
- Fillet now rejects every box edge except the one along X at minimum Y and maximum Z, before it builds a mesh. Edges 1ÃƒÂ¢Ã¢â€šÂ¬Ã¢â‚¬Å“2 and 3ÃƒÂ¢Ã¢â€šÂ¬Ã¢â‚¬Å“7 of a 40 ÃƒÆ’Ã¢â‚¬â€ 30 ÃƒÆ’Ã¢â‚¬â€ 20 mm box no longer come back as swapped 30 ÃƒÆ’Ã¢â‚¬â€ 20 ÃƒÆ’Ã¢â‚¬â€ 40 or 20 ÃƒÆ’Ã¢â‚¬â€ 40 ÃƒÆ’Ã¢â‚¬â€ 30 solids. `test_create` keeps that box unchanged.
- Drove `solid_view` through a 40 ÃƒÆ’Ã¢â‚¬â€ 30 ÃƒÆ’Ã¢â‚¬â€ 20 mm box, a 3 mm fillet, and an interior cut. The on-screen checker line stayed PASS, the inch toggle scaled the spin readouts by 25.4, and the exported STL/3MF stayed 40 ÃƒÆ’Ã¢â‚¬â€ 30 ÃƒÆ’Ã¢â‚¬â€ 20 mm. OrcaSlicer reports `manifold = yes` and two shells (outer solid plus the closed void). Note: `mvp/create-export.md`.
- Added the create-to-export mesh path: box, cylinder, XY sketch (line, rectangle, circle, distance, radius, horizontal, vertical, coincident), one-direction extrude, union, cut, and a constant-radius fillet on one box edge. `repair_manifold` rechecks with the existing watertight checker and blocks export when it cannot repair. `solid_view` adds Sketch, Solid, and Inspect, a browser, a timeline, and a properties panel with the millimeters/inches toggle. Contract: `mvp/create-export.md`.
- Added a 20 mm box export. `export_box` writes binary STL and 3MF under `builds/export/` only after `check_watertight` passes. `solid_view` keeps the three fixtures and adds **20 mm box**, which loads that STL and shows the checker sentence. Contract: `mvp/export.md`.
- Added the units lock in `src/units`. Stored lengths stay millimeters. The display toggle converts by 25.4 and does not scale stored numbers. `ExportUnitRecord` keeps STL/3MF coordinates in millimeters. Checker sources and `solid_view` were not edited. Contract: `mvp/units.md`.
- Published the initial tree to https://github.com/cyborgpencil/cad-mvp. README points at `mvp/requirements.md` and states millimeters with an inch switch, the Qt GUI, and the required watertight check. Added the LGPL-2.1 `LICENSE` and C++/Qt/CMake ignore rules.
- Added `solid_view`, a Qt 6.8.3 window that draws a fixture mesh and shows the existing watertight sentence. Checker sources were not edited. CTest `watertight` passed. UI Automation read the closed, open, and flipped result lines. Contract: `mvp/mesh-view.md`.
- Built the watertight check with MSVC 19.51 (Visual Studio Community 2026, NMake). CTest `watertight` passed. `check_solid` exited 0 and printed pass for the closed box, a boundary failure for the open box, and a winding failure for the flipped box.
- Added the first code slice: in-memory triangle mesh and watertight check (`src/solid`, `src/check_solid.cpp`, `tests/test_watertight.cpp`, `CMakeLists.txt`). Contract: `mvp/solid-check.md`. A throwaway Python mirror of the same rules produced the expected pass/fail lines. The C++ was not compiled: Visual Studio Community 2026 is installed, and its C++ toolset is not.
- Created general reusable skill `.grok/skills/tooling-priority/` (SKILL.md + evals) for prioritizing Grok Build ÃƒÂ¢Ã¢â‚¬Â Ã¢â‚¬â„¢ Cursor ÃƒÂ¢Ã¢â‚¬Â Ã¢â‚¬â„¢ Grok Bots across any project.
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
- Created `mvp/gui-plan.md` (draft GUI plan per Erik via 3T): Fusion-style layout, Blender-style operations mapped to B-rep, exploring the model, sketch, input, WASM feasibility, phases P1-P5 with GUI test matrices. Watertight and units checks are now a gate, not the main focus. Scope conflicts C1-C5 are flagged for Erik.
- `mvp/gui-plan.md`: added C6 (Qt harness vs product), the faces-and-edges rule for Blender tools, Pilot's note that Qt fillet and cut are mesh code today, the tests/gui/baselines/ path, and a link to research/gui/README.md.
- `mvp/gui-plan.md`: pulled in Research Digest's research/gui/README.md picks (three.js stack, OCCT routes, PlaneGCS, Pointer Events, Playwright, Web Worker) and added scope conflicts C7-C9.
- Added `prompts/gui-mockup.md` for the clickable GUI mockup (Erik via 3T: pipeline first, C1-C9 deferred, team picks the options). Includes the Chief's no-CDN, touch and mockup-only rules.
- `prompts/gui-mockup.md`: three.js must be inlined and pinned (Chrome blocks module files over file://), per Research Digest and Repo Keeper.
- `AGENTS.md`: added Erik's keep-finished-work rule (no rewrites or deletions, reason posted first, tests keep passing, OCCT next to the mesh path). `mvp/gui-plan.md` C9 reworded to match.
- `mvp/gui-plan.md` section 6: changed 'move to OCCT' to 'add OCCT alongside the mesh code', matching AGENTS.md and research/gui/README.md.
- 2026-10-21 00:32 MT (Doc Steward): prompts/gui-mockup.md now says Pilot takes the mockup screenshots with headless Edge (same sizes and paths), not Grok.
- 2026-10-21 00:33 MT (Doc Steward): AGENTS.md has a new Z13-only execution rule (direct Shell on Z13, no Ally or WinRM route), per Erik via 3T.
- 2026-10-21 00:42 MT (Doc Steward): AGENTS.md now documents the handoff folder C:\Users\cybor\Pictures\cadmvp-shots\ (handoff copies only, because the app's file copy only reads under the user profile).
- 2026-10-21 00:43 MT (Doc Steward): AGENTS.md handoff section now says to delete nothing in the staging folder without Erik's go, and it points to the shared skill pull-files-from-user-pc.
- 2026-10-21 00:50 MT (Doc Steward): mvp/gui-plan.md section 8 adds the workbench tab redesign proposal (layout sketch, shared tools, tab-by-tool map, open questions). Design only, no code changes.
- 2026-10-21 00:55 MT (Doc Steward): moved the redesign proposal into mvp/ui-redesign.md (per Chief), left a pointer in gui-plan.md section 8, and added Research Digest's takeaways plus TBDs for units/export placement and Sketch as a mode.
- 2026-10-21 00:54 MT (Doc Steward): AGENTS.md gains Erik's flexibility/takeover and research-first rules. ui-redesign.md gains the mockup control map from Repo Keeper's inventory, flags the missing export gate in the mockup, and adds TBDs for tab names and shortcut keys.
- 2026-10-21 00:56 MT (Doc Steward): ui-redesign.md marks the export gate as a must-have and rules out Ctrl+PageUp/PageDown, which Chrome reserves.
- 2026-10-21 00:58 MT (Doc Steward): ui-redesign.md records the team's UI decisions (tabs, Sketch mode, Repair tab, shared view bar, no radial menu, units, export gate, no timeline, style). Shortcut keys are still pending.
- 2026-10-21 01:00 MT (Doc Steward): ui-redesign.md decisions are final. Tabs are Sketch/Model/Repair/Export, with one gated Export button and no quick export, Slate dark style with 44 px targets, keys 1 to 4 plus X for tool search (untested), and volume in the status bar.
- 2026-10-21 01:02 MT (Doc Steward): ui-redesign.md renames every remaining Export/Print to Export, matching the settled tab name.
- 2026-10-21 01:03 MT (Doc Steward): Pilot's mockup run ended partial. Grok Build was force-stopped at the 25-minute timeout, with no exit code. mockup/index.html is 749 KB with three.js r160 inlined, the screenshots are in builds/screenshots/, and copies are in cadmvp-shots. The mockup predates the UI redesign (it still has Solid/Inspect tabs and the radial menu). Keeping it or rerunning it is Erik's call.
- 2026-10-21 01:05 MT (Doc Steward): prompts/gui-mockup.md now follows the final decisions in ui-redesign.md and adds checkpoints, so the next run saves partial work (shell first, then one tab at a time, with PROGRESS.md). No run was started; it waits for Erik's approval.
- 2026-10-21 01:07 MT (Doc Steward): Pilot rendered the UI wireframe (desktop and phone PNGs in cadmvp-shots, nothing in the repo changed). Revolve on its Model strip is not in ui-redesign.md and is illustrative only (Chamfer is part of Bevel). The Repair strip waits on Research Digest's tool list.
