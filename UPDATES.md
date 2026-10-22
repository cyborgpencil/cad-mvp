# Project Updates Log

**Purpose**: Quick chronological record of changes so anyone (or future-you) can see what moved without reading every file.  
Newest entries at the top.

## 2026-10-21

- Wired the approved mockup layout into `web/` as a single-threaded WASM page. The status bar and the one Export button call `evaluate_export_gate` (`src/export/gate.cpp`), which reads `check_watertight` and the millimeter `ExportUnitRecord` and reports the triple-sum volume. `src/solid`, `src/units`, and `src/model` are unchanged. CTest `gate` covers the block. Build steps are in `web/BUILD.md`. The `.wasm` is gitignored. No OCCT and no FixGaps in this slice.
- Research Digest reworded `research/gui/README.md` (feasibility, scope conflict 6, next step 1) per Erik's rule: OCCT fillet/chamfer/cut/extrude would sit alongside the existing mesh code, not replace it; existing tests and values including O5b stay; post a reason in the room before changing existing code.
- Research Digest filled four `mvp/gui-plan.md` TBDs with sourced proposals needing Erik's sign-off: sketch solver (PlaneGCS WASM), rendering stack (three.js + camera-controls + three-mesh-bvh), screenshot tool (Playwright), and inset feasibility (`BRepOffsetAPI_MakeOffset` + `BRepAlgoAPI_Splitter`). Pixel-diff tolerance and other TBDs unchanged.
- Research Digest added `research/gui/README.md`: sourced GUI reference (Fusion layout, Blender ops with B-rep/OCCT equivalents, three.js parts and licenses, PlaneGCS/SolveSpace solvers, Pointer Events input, Playwright screenshot tests) and 7 scope conflicts for Erik. Indexed in `research/INDEX.md`.
- Research Digest checked every volume formula in `mvp/test-matrix.md` (no corrections needed), added per-row measurement methods, failure reasons for coplanar, tiny-feature, thin-wall, and curved cases, proposed tolerances derived from mesh chord error (needs Erik's sign-off), and a Sources section.
- Recorded the agreed push cadence in `AGENTS.md`. Corrected the internal-void note in `mvp/test-matrix.md`: the Qt run's 23536.9 mm3 comes from fillet-then-cut, not a defect. Added row O5b (filleted internal void, 23538.74 mm3) and marked chamfer, sphere, cone, and intersect as test-only until Erik confirms scope (merged Research Digest's duplicate note; 3T set this interim, not Erik).

## 2026-10-20

- Added `mvp/test-matrix.md`: 9 shape and 12 operation cases on OpenCASCADE, each exported to STL and 3MF and checked for watertight, volume, bounding box, `unit="millimeter"`, and Orca read-back. Tolerances and tiny-feature behavior are TBD. Chamfer, sphere, cone, and intersect need Erik to confirm they are in scope.
- Re-check after Grok Build's create-to-export run (finished 11:47 PM MT, goal marked achieved), run by Grok Build Pilot at 11:55 PM MT: the MSVC/NMake build passed, CTest passed 4 of 4 (watertight, units, export, create), and the CLI `export_part` wrote `box.stl` and `box.3mf`. Watertight: `check_solid` exited 0, and OrcaSlicer reports manifold yes for both files at 40 ÃƒÆ’Ã¢â‚¬â€ 30 ÃƒÆ’Ã¢â‚¬â€ 20 mm, with 2 parts (the outer solid plus the closed interior void). Units: the 3MF carries `unit="millimeter"` and the units test passed. Logs are in `builds/logs/20261020-2355-*`.
- Files that run changed: edits to `CMakeLists.txt`, `UPDATES.md`, `mvp/mesh-view.md`, `research/occt-wasm/README.md`, and `src/gui/main_window.*` and `mesh_view.*`. New files: `mvp/create-export.md`, `mvp/export.md`, `mvp/units.md`, `src/export/`, `src/export_box.cpp`, `src/export_part.cpp`, `src/model/`, `src/units/`, and `tests/test_create.cpp`, `test_export.cpp`, `test_units.cpp`. Also new: `prompts/wasm-occt-core.md`, the prompt for the next headless WASM + OCCT 8.0.1 session (Chrome on Windows, Android, and iPhone; mm with an inch toggle; STL/3MF only).
- Resolved 2026-10-21: the publish entry below is now true. Repo Keeper pushed `main` to https://github.com/cyborgpencil/cad-mvp at `10e7c76` (4/4 CTest passed, secrets scan clean, no force-push).
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
- 2026-10-21 00:42 MT (Doc Steward): AGENTS.md now documents the handoff folder %USERPROFILE%\Pictures\cadmvp-shots\ (handoff copies only, because the app's file copy only reads under the user profile).
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
- 2026-10-21 01:09 MT (Doc Steward): ui-redesign.md decision 3 and prompts/gui-mockup.md now list Research Digest's proposed Repair tools (Check shape, Find open edges, Auto-heal, Mesh repair). The small-gaps fix is TBD for Erik.
- 2026-10-21 01:11 MT (Doc Steward): Model tools now list Fillet instead of Bevel (Fillet/Chamfer) in ui-redesign.md and gui-mockup.md, because Chief ruled Chamfer test-only and out of the MVP strip.
- 2026-10-21 01:13 MT (Doc Steward): Chief confirmed Fillet only; also removed [Chamfer] from the ui-redesign.md layout sketch.
- 2026-10-21 01:07 MT (Doc Steward): Erik approved the wireframes and asked for the GUI to be implemented now. Grok Build builds it on Z13 from mvp/ui-redesign.md and prompts/gui-mockup.md, with checkpoints in mockup\PROGRESS.md. Every export must pass the watertight and units check, and FixGaps stays out (TBD). Marked ui-redesign.md approved and removed the approval wait from the prompt.
- 2026-10-21 01:09 MT (Doc Steward): Made the public docs generic at Chief's request. The user-folder path is now %USERPROFILE% and the dev machine is now 'the dev PC' in AGENTS.md, UPDATES.md and prompts/wasm-occt-core.md. The cyborgpencil handle stays because it owns the repo. Also marked the old publish note resolved, since main was pushed at 10e7c76.
- 2026-10-21 01:31 MT (Doc Steward): GUI run done (1:07-1:25 MT, CTest 4/4, only mockup/index.html and mockup/PROGRESS.md changed). The Model tab's extra tools (Union/Cut, Inset, Loop Cut, Knife, Grab, Rotate, Scale, Snapping) match ui-redesign.md and gui-mockup.md. The wireframe strip was a trimmed preview, so nothing is out of scope. 12 of 26 usability checks pass and the rest are untested. The phone screenshot is being redone.

- 2026-10-21 01:33 MT (Doc Steward): Phone screenshot redone at true 390x844 (gui-impl-phone.png, frame render, 1x, no touch emulation); all four bottom tabs incl. Export visible. T1 partial per Research Digest (29 visible controls >=44px, no sideways scroll; scrolling-strip controls still to measure), T2 pass at 1440x900 (63 controls). Off-screen strip controls unmeasured; T4 and real-phone checks still untested. L2 fails for now: Info button clipped at right edge, Part1 title truncated. CTest 4/4; no source changes.
- 2026-10-21 01:35 MT (Doc Steward): Drafted prompts/gui-wire-app.md (target TBD for Erik: Qt src/ or WASM). Real watertight and units checks gate Export; FixGaps out; 5 checkpoints; 60-minute cap.
- 2026-10-21 01:45 MT (Doc Steward): Repo Keeper pushed main at 0878700 (10e7c76..0878700, 5 commits, CTest 4/4, no force, scan clean). Pilot phone fix (mockup only): Info button fully visible, Part1 title ellipsis with full name on tap. T1 at 390: 63/64 controls >=44px, Part name button 30x44 fails; T2 pass. Follow-up pending Chief OK.
- 2026-10-21 01:47 MT (Doc Steward): Erik decided target = WASM only (01:45 MT): one WASM app for desktop and mobile, Qt path folded in, hosted on GitHub Pages. prompts/gui-wire-app.md set READY with target WASM, the responsive and orientation requirement (desktop, phone portrait, phone landscape), and Pages constraints (no custom headers; flag COOP/COEP). Model tool list unchanged.
- 2026-10-21 01:49 MT (Doc Steward): gui-wire-app.md now says single-threaded WASM build (no -pthread, so no COOP/COEP; pages-hosting.md), .wasm never committed (Actions builds it), and checks against R1-R5. Pages enablement waits on Erik's go in his 1:1 with Repo Keeper, and the deploy waits on the wired check plus CTest passing.
- 2026-10-21 01:54 MT (Doc Steward): Pilot title fix in (mockup only): T1 64/64 and T2 63/63 pass, CTest 4/4. Z13 has no emsdk, no OCCT build and no WASM page. The wiring run has started: phase 1 compiles the existing C++ checks (src/solid/watertight.cpp mesh check, src/units, src/model/repair) to WASM in web/; phase 2 is the OCCT WASM build (BRepCheck plus free bounds).
- 2026-10-21 01:57 MT (Doc Steward): Erik added Chamfer as an MVP user tool (via 3T); ui-redesign.md, gui-mockup.md and gui-wire-app.md updated to match. New mvp/projects/blink-l-bracket.md is the first end-to-end test case (4 mm bracket and disc given; all other dimensions TBD pending Erik and Research Digest).
- 2026-10-21 01:59 MT (Doc Steward): Chief ruled that the Pages deploy waits for phase 2 (real OCCT WASM check); the phase 1 mesh-check wiring is an interim checkpoint only. Repo Keeper committed 2c027d5 locally (3 commits unpushed); push and Pages enablement wait on Erik's go in his 1:1 chat with Repo Keeper.
- 2026-10-21 02:00 MT (Doc Steward): Research Digest recommends libcascade 3.1.0 (OCCT 8.0.1, single-threaded, 42.8 MB .wasm uncompressed) over building OCCT ourselves; a trimmed build needs Docker (Z13 status unknown). Open TBD for Erik: LGPL relinking obligations when OCCT is statically linked into the WASM. T1 is now PASS.
- 2026-10-21 02:01 MT (Doc Steward): gui-wire-app.md records Chief's checkpoint 2 plan: prebuilt libcascade first, no Docker without Erik, wasm_build.bat as fallback. 3T is passing the LGPL relinking TBD to Erik.
- 2026-10-21 02:03 MT (Doc Steward): blink-l-bracket.md updated from Research Digest's blink-mount.md. It adds reference notes and TBD rows for casing profile, screw spec and hole oversize. Every dimension except the 4 mm thicknesses is still TBD for Erik to measure.
- 2026-10-21 02:08 MT (Doc Steward): Erik direction change (2:05 AM MT): visuals first, MODO-style teal restyle, research into MODO's Booleans and interactive Booleans with live preview. Added prompts/modo-restyle.md (palette TBD, no MODO assets, gates kept) and mvp/booleans.md (B-rep OCCT Booleans, live preview, commit-time watertight check; tolerance, Intersect scope and performance targets TBD).
- 2026-10-21 02:10 MT (Doc Steward): Interim Pages deploy approved by Chief and 3T: 'Interim build: OCCT check pending' banner, Export disabled until the OCCT gate is green, push only after Erik's go in his 1:1 chat with Repo Keeper. Recorded in gui-wire-app.md.
- 2026-10-21 02:12 MT (Doc Steward): Research Digest's MODO findings folded into mvp/booleans.md, prompts/modo-restyle.md and prompts/gui-wire-app.md. Open for Erik: the teal reference image, fuzzy tolerance, and whether to add manifold-3d for the live preview.
- 2026-10-21 02:14 MT (Doc Steward): Chief's live-drag decision (ghost preview, then exact Boolean on release with rollback; manifold-3d out unless Erik asks) recorded in mvp/booleans.md, along with Erik's 5 open questions.
- 2026-10-21 02:58 MT (Doc Steward): Checkpoint 1 (Pilot, session 01a15d74, about $1.56). The interim WASM app runs locally on Z13 using the phase-1 mesh watertight checker and the units check. The open box FAILs on edge (4,5) and Export is blocked; the closed box PASSes. Native CTest passes 5/5, including the new gate test. R1-R5 pass (R2 and R3 by code reading only). T1 passes. Open items: the landscape 844x390 gate panel squeezes the view and the ViewCube overlaps the view bar; the interim banner is missing; Export still unlocks on the mesh check alone. Pilot is fixing all three in the restyle session. Nothing committed yet. Grok's process idled from 2:15 until the 60-minute cap.
- 2026-10-21 03:00 MT (Doc Steward): Chief rulings recorded in gui-wire-app.md: deploy is held until the banner is up and Export is locked; stop the session when Grok reports done; R2 and R3 stay provisional until a live rotation test.
- 2026-10-21 03:16 MT (Doc Steward): Restyle checkpoint (Pilot, session 01a15dae, 2:57-3:13 MT, $1.59). The interim banner shows at all 3 sizes. Export stays locked until the OCCT gate passes (off until phase 2). The landscape overlap is fixed. MODO layout is in, with all palette colours as TBD CSS variables. CTest 5/5, T1 passes. R2 passed a live resize in a headless browser, not on a phone; R3's live test isn't reported yet. This checkpoint is the candidate for the first deploy, pending Erik's go. Next: phase 2 libcascade OCCT gate.
- 2026-10-21 15:46 MT (Doc Steward): New direction from Erik via 3T: a MODO-like feel based on the reference video https://youtu.be/HhuccQ20YVM, with high-contrast active buttons, a selection gizmo for faces, edges and vertices, and editable primitives. Erik has approved Pages deploys of passing builds. Phase 2 OCCT gate has started (Pilot). R3 stays provisional until a live check. Added to web/PROGRESS.md.
- 2026-10-21 15:48 MT (Doc Steward): The restyle build is live on Pages as 6a04ad5 (https://cyborgpencil.github.io/cad-mvp/), pushed by Repo Keeper after Erik's 10:22 AM approval; the banner is on and Export is locked. Correction: phase 2 had not launched. Chief's order: OCCT gate session now, then the UI session following Research Digest's spec.
- 2026-10-21 15:49 MT (Doc Steward): Chief ruled that selection colours stay TBD variables because Erik asked for teal and MODO's docs show orange; the question is with Erik through 3T. Pilot has started the OCCT gate session.

- 2026-10-21 15:50 MT: Research Digest spec landed at research/gui/modo-selection-primitives.md (linked in research/INDEX.md). UI session follows it after the OCCT gate; colours stay TBD vars (--sel-color, --hover-color); Box centred via half-size offset; Cylinder base = centre - axis*h/2; primitives must pass watertight + units checks; banner and Export gate unchanged.

- 2026-10-21 16:15 MT: Phase 2 OCCT gate done (Pilot, session 01a1606d, 3:45-3:58 PM MT, $1.21). closed_box passes (BRepCheck valid, 0 free edges, watertight+units pass, Export unlocks, banner hides); open_box fails (4 free edges, Export locked). CTest 6/6 incl. occt_gate. libcascade 3.1.0 / OCCT 8.0.1 prebuilt, single-threaded, 42.8 MB wasm, gitignored. R3 passes live in headless browser; real-phone check still pending (also for 42.8 MB wasm). Erik to review pages.yml (fetches libcascade at deploy) and index.html diffs. Next: selection/primitives UI session; colours stay TBD vars.

- 2026-10-21 16:20 MT: prompts/gui-wire-app.md: added rule that occt_gate fails in CI when libcascade is missing (skip only locally), per Research Digest.

- 2026-10-21 16:58 MT: Phase 2 OCCT gate pushed and live (code 644affb, UPDATES 3cc3c3f). Clean rebuild CTest 6/6, occt_gate ran (not skipped), secret scan clean, no .wasm/dist committed. Actions fetched libcascade 3.1.0 (sha256 0592690a...f330). Pages serves wasm gzipped: ~12.4 MB download (12,359,983 bytes) vs 42.8 MB raw. Open_box Export lock not yet clicked through on live site (covered by test). Erik to review pages.yml + index.html in 644affb. Docs 10aaac8 local, ships with UI checkpoint.

- 2026-10-21 17:07 MT: Phase 2 closed. Live open_box (headless Chromium) shows banner up, OCCT FAIL (4 free edges), watertight FAIL, units PASS, Export disabled; shot cadmvp-shots\openbox-live.png. UI checkpoint shots from 5:06 were stale (old wasm); Pilot rebuilding and re-shooting before commit/push.

- 2026-10-21 17:08 MT: Selection + primitives checkpoint done (Pilot, session 01a16088, 4:15-4:42 PM MT, $2.11; hung after done marker, killed 5:06). CTest 6/6, uncommitted, +964/-62 on 10aaac8. Fresh 5:07 shots (cache off): wasm-desktop, wasm-portrait, wasm-landscape, wasm-cylinder-desktop. Box and cylinder pass OCCT/watertight/units (Export on); open_box still locked. Live R3 PASS in headless browser. Erik to review web/bindings.cpp (new replaceMesh C++ glue, no kernel change). Open/TBD: colours, default primitive sizes, 8 px pick tolerance, tessellation settings; hotkey 4 -> Export tab is unspecced (spec only defines 1/2/3/5), needs Erik's call; gizmo hidden inside cylinder; real-phone R2/R3 pending. Next: CI occt_gate session.

## 2026-10-21 17:20 MT - UI checkpoint pushed and live
- a03e1d1: UI checkpoint (selection + primitives) plus 17:08 UPDATES entry and research size edit, on top of 10aaac8.
- 2f6b458: prompts/gui-wire-app.md queued items, plus pages.yml fix to copy all web/*.mjs (first deploy crashed with makeGizmo of null because three new modules 404'd).
- Live shots (headless, cache busted): box face select with gizmo, OCCT and watertight PASS; cylinder Item mode with gizmo hidden inside solid (fix queued); portrait and landscape watertight PASS.
- Secrets scan clean, no .wasm committed. Next: Pilot CI session (occt_gate CI fail, gizmo depth, hotkey 4 TBD, watcher fix); Research Digest MODO Booleans + OCCT fillet/chamfer digest feeds the next Grok Build prompt.

## 2026-10-21 17:23 MT - L-bracket prompt drafted
- prompts/l-bracket-fillet-chamfer.md from research/gui/booleans-fillet-chamfer.md; gate after every op, TBDs listed for Erik. Queued after the CI session.

## 2026-10-21 17:35 MT - Deploy smoke test (local, uncommitted)
- Grok Build session 01a160c4 (5:21-5:34 PM MT, $0.53, +36/-4 on 96ebafd). CTest 7/7 on Z13.
- web/assemble_site.py is now the single site file list for pages.yml and the smoke test. tests/deploy_smoke.py loads the site headless with the cache off and fails on any non-2xx response, console/page error or unhandled rejection. It checks three scenes: closed_box PASS with Export enabled, open_box FAIL with Export locked, box with a face selected PASS.
- Negative check: leaving out selection.mjs makes the test exit 1 with HTTP 404. Favicon is now a data URI so /favicon.ico no longer 404s.
- Not yet proven: first CI run on the Linux runner. Erik to review the pages.yml diff.
- Still open: occt_gate CI fail, gizmo drawn on top, hotkey 4 removal (Pilot follow-up).

## 2026-10-21 17:50 MT - Smoke test live; CI follow-up green locally
- 6945311 pushed 5:36 PM MT (carried 96ebafd): smoke-test files, favicon lines only in index.html, L-bracket prompt, UPDATES 17:23/17:35. Pages run 39694451250 passed the smoke test on Linux and deployed. Pushed before the Chief's hold, but verified: no half-done gizmo or hotkey edits went live.
- Follow-up session 01a160d2 (5:37-5:47 PM MT, $0.72, +62/-26 on 6945311, uncommitted). CTest 7/7. occt_gate is always registered: exit 1 in CI (CI or GITHUB_ACTIONS) when libcascade is missing, skip 77 locally, verified both ways. Gizmo drawn with depth test and writes off, above the selection overlays; the cylinder shot shows it on top. Hotkey 4 unbound and TBD; Alt+1 to Alt+4 still switch tabs.
- Grok hung after its done marker again; the watcher killed it within about a minute.
- Fresh shots at 5:49 PM MT in cadmvp-shots: wasm-desktop, wasm-portrait, wasm-landscape, wasm-cylinder-desktop.
- Erik to review the pages.yml and CMakeLists.txt diffs. Next: Repo Keeper push and confirm occt_gate runs on Linux (not skipped); then Pilot runs the L-bracket prompt with TBD constants.

## 2026-10-21 17:52 MT - CI follow-up pushed
- 5c2918c (Pilot's five files) pushed; Pages run 39696038487 passed and deployed.
- Gap: no workflow runs ctest, so occt_gate's CI-fail path is still untested on Linux. Fix: add a CTest step to pages.yml or a separate test workflow (Erik reviews, with the CMakeLists.txt diff).
- Tree clean; L-bracket prompt cleared to start.

## 2026-10-21 17:57 MT - CTest gates the deploy (local, uncommitted)
- Session 01a160e1 (5:53-5:56 PM MT, $0.18). pages.yml now has a Native CTest step (Node 22, g++, cmake; builds builds/native, runs ctest --output-on-failure with CI=true; deploy_smoke runs inside the suite). It sits after the libcascade fetch and site assembly, before configure-pages and the upload, so a failing occt_gate blocks the release.
- Files: pages.yml and web/PROGRESS.md. Z13 CTest 7/7.
- Risk: first GCC build on Linux. Next: Repo Keeper pushes and confirms occt_gate ran and passed (not skipped) in the Linux log; then L-bracket. Erik to review the pages.yml diff.

## 2026-10-21 18:04 MT - CTest gate blocked first Linux release
- 9dfc0c8 pushed; Actions run 39696764181 failed in the Native CTest build step before CTest started: tests/test_create.cpp uses std::fabs without including <cmath> (GCC error, lines 109-110 and 184-186). The gate blocked the release as designed; the live site stays on 5c2918c.
- Next: Pilot adds #include <cmath>; Repo Keeper pushes and confirms occt_gate shows Passed (no Skipped or Not Run line, since SKIP_RETURN_CODE 77 counts as skipped). L-bracket waits.

- 2026-10-21 18:10 MT: GCC include fix ready, not yet committed (Grok session 01a160ed, 6:05-6:09 PM MT). Adds <cmath>/<cstddef> to tests/test_create.cpp, plus missing <cstddef>/<cstdint> includes in 8 src files (include lines only). Erik to review the src/ diffs as core. Z13 CTest with CI=1: 7/7 pass incl. occt_gate; deploy_smoke pass. Pending: Repo Keeper commit+push, Linux CI must show occt_gate Passed (not Skipped). L-bracket session starts after green.

- 2026-10-21 18:12 MT: 27e54d5 pushed (GCC include fix). Linux CI run 39698121674: GCC build OK, occt_gate Passed 1.13 s (no Skipped/Not Run), 7/7 tests, site deployed. Release gate cleared; L-bracket session unblocked. Erik review of include-only src/ diffs still pending.

- 2026-10-21 18:57 MT: L-bracket session 01a160f4 (6:13-6:29 PM MT, on 6dfa176) ran; Z13 dropped offline ~6:30 PM and returned 6:57 PM. Checks pending (out.json, diff, CTest CI=1, smoke, WASM, watertight/mm, screenshots). Chief guardrail added to prompts/l-bracket-fillet-chamfer.md: fixture numbers in test files only, app constants stay TBD. Nothing committed until checks pass.

- 2026-10-21 18:58 MT: L-bracket session 01a160f4 done (LBRACKET_DONE, $0.90, 7 files +259/-8, new web/occt-ops.mjs; no src/ or bindings.cpp change). Guardrail breach: LBRACKET_TBD_* app constants hold real numbers and PROGRESS.md lists them as defaults. Fix session queued: app constants null, builder refuses 'dimensions TBD', numbers moved to tests/fixtures/lbracket.json via query params, test that bare ?demo=lbracket stays locked. Commit on hold.

- 2026-10-21 19:00 MT: Erik delegated the open decisions to the team (thickness stays 4 mm). Priority: 1) solid modeling tools (shapes, gizmo, Booleans, fillet/chamfer), 2) export. Safety rules unchanged. The L-bracket prompt's TBD guardrail is replaced by this rule. Decisions table added to PROGRESS.md; preview mode and colour hex values are still open, for Pilot to record. Session thickness 10 mm must be corrected to 4 mm before commit.

- 2026-10-21 19:13 MT: L-bracket fix session 01a16120 (7:01-7:10 PM MT, $0.73) passed: 10 files +448/-44, no src/ change, no *_TBD_* names left. Team values recorded in web/PROGRESS.md (40x20x40, 4 mm thick, R2 inner fillet, 0.5 mm chamfer, preview on apply, hotkey 4 selects whole body, 8 px pick, hover #d7f4ff, selection #ff4fd8, 20 mm primitives). CTest CI=1 7/7 (occt_gate Passed), smoke pass, fixtures return 404, WASM OK. Pilot's own STL check: watertight, mm, 0-40x0-20x0-40, 6092.69 mm3. Gaps: coarse fillet tessellation, no hotkey-4 key-press test. Correction: the 19:00 decisions table went into a new root PROGRESS.md by mistake; web/PROGRESS.md is the canonical file. Do not commit the root file. Erik to review occt-ops.mjs and index.html.

- 2026-10-21 19:15 MT: Added prompts/interactive-booleans.md (union/cut/intersect on selected bodies, gate on every result, revert on failure, hotkey 4 browser test). Chief rulings: Repo Keeper commits the L-bracket checkpoint without root PROGRESS.md (Erik decides on that duplicate); Research Digest preps OCCT mesh deflection settings for smoother fillets.
