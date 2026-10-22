# WASM GUI wiring progress

## Checkpoint 1 — plan

Done. Written here, then the session continued. No OCCT. No `-pthread`. No FixGaps. `mockup/` was not edited. `src/solid`, `src/units`, and `src/model` were not edited. The gate only reads them. See `web/BUILD.md`.

## Checkpoint 2 — status bar

Done. `evaluate_export_gate` calls `check_watertight` and `export_units`. The status bar shows the checker sentence, `mm` or `in`, and the triple-sum volume (`sum / 6` from `mvp/solid-check.md`).

Open box: `FAIL: edge (4,5) is shared by 1 triangle (need 2).` Volume `0.667 mm³`.
Closed box: the PASS sentence. Volume `1 mm³`.
20 mm box: volume `8000 mm³` (CTest). The display toggle does not change the stored millimeters or the export unit.

## Checkpoint 3 — gated export

Done. One Export button. It stays disabled unless watertight and the millimeter lock both pass. The button title and the gate line are the block reason (watertight sentence first, otherwise the units sentence). STL and 3MF are the existing writers. A browser download of the closed box wrote `Part1.stl` (684 bytes, header `cadcam-m…`, not `solid`, header contains `millimeter`) and `Part1.3mf` (ZIP, `PK`).

## Checkpoint 4 — tools

Repair calls the existing code: Check shape and Find open edges use `check_watertight`. Auto-heal and Mesh repair both call `repair_manifold` (weld, drop degenerates, flip an inward shell). A mesh that stays open returns `cannot repair:` plus the checker sentence.

Sketch tools and the other Model tools stay the approved buttons. Their solvers are TBD (no PlaneGCS, no OCCT). Chamfer is a user tool in `mvp/ui-redesign.md`, and the approved mockup has no chamfer control and `src/` has no chamfer function, so no button was added. Sphere, cone, and intersect stay out. FixGaps stays out.

File → Load closed box, Load open box, Load 20 mm box, Load flipped box.

## Checkpoint 5 — CTest and screenshots

CTest in `builds/solid-check`: 5/5 passed (`watertight`, `units`, `export`, `gate`, `create`).

Screenshots (Edge headless, `http://127.0.0.1:8765/`):

- `builds/screenshots/wasm-1440x900-open.png` and `wasm-1440x900-closed.png`
- `builds/screenshots/wasm-390x844-open.png`
- `builds/screenshots/wasm-844x390-open.png`

Copies are also in `%USERPROFILE%\Pictures\cadmvp-shots\`.

Rotation checks, measured in that Edge session (not a physical phone):

- R1: Sketch, Model, Repair, and Export are reachable at 390×844 and 844×390. The Export button is on screen. `scrollWidth` equals the viewport width (no horizontal scroll).
- R2: resize and orientation listeners only re-layout. They do not reload, clear the tab, or close a dialog.
- R3: no `screen.orientation.lock()` and no rotate-only block.
- R4: every visible `button` at 844×390, 390×844, and 1440×900 measured at least 44×44 CSS px.
- R5: on all four tabs the status bar shows `mm`, watertight PASS/FAIL, and the volume, and the bar stays inside the viewport.

Not done: a physical phone pass (T4, K5–K8). The export tab at 844×390 leaves a short viewport, so the view cube sits over the view bar. The status bar and the Export button stay clear.

## Left

- OCCT WASM, Pages workflow (Repo Keeper), and committing the build. `web/cadcam.js` and `web/cadcam.wasm` are gitignored.
- Chamfer control, once Erik places it and there is a function to call.
- Sketch solver and the rest of Model. TBD.
- No commit and no push this session.

## Checkpoint 6 — OCCT gate, landscape, MODO restyle

Done in `web/index.html` only. No `src/` or kernel edits. No commit and no push.

- Banner text is `Interim build: OCCT check pending`.
- `occtGate` stays `false`. Export enables only when `occtGate && watertight && units`. Mesh PASS/FAIL still shows on the status bar and the gate panel. The disabled reason is `Export blocked: the OCCT check is pending.`
- Short landscape (including 844×390): the Export gate is one 52px row, so it does not take the viewport. The view cube is sized to sit above the view bar. Home sits beside the cube.
- Desktop layout: toolbox tabs and tool settings on the left, viewport in the center, Items on the top right, Properties / Channels / Display / Lists under that. Preview toggles axis handles. Accent is the single CSS variable `--accent`.
- Teal panel colours in `:root` are the earlier stand-ins listed in `mockup/PROGRESS.md`. Hover, selection, axis, and active-button hex values are the team choice below. No Modo assets.
- CTest in `builds/solid-check`: 5/5 passed (`watertight`, `units`, `export`, `gate`, `create`).
- Screenshots were not taken. This session does not start an http server.

## Next: selection, primitives, MODO feel (Erik, 2026-10-21 3:44 PM MT)
- Reference video: https://youtu.be/HhuccQ20YVM. The GUI should feel similar, not match exactly, with clearly contrasting buttons when selected or active.
- A selection gizmo showing which faces, edges or vertices are selected.
- Primitives (box, cylinder, etc.) with editable parameters, which can then be modified.
- Keep the Export gate and the interim banner. Selection, axis, and active-button hex values are the team choice recorded below.
- Phase 2 (libcascade OCCT gate) is in progress with Pilot.
- R3 is still provisional (code read only); a live R3 check is due at the next checkpoint.
- Correction (3:46 PM MT): phase 2 never launched after the 3:15 AM plan. Order of work per Chief: the OCCT gate session first, then the selection and primitives session following Research Digest's spec (research/gui/modo-selection-primitives.md, in progress).
- Live: the restyle build is deployed as 6a04ad5 at https://cyborgpencil.github.io/cad-mvp/ (banner on, Export locked). Each push to main now deploys through Actions.
- Chief ruling (3:48 PM MT): selection and hover colours are named CSS variables. Superseded the same day: the team set the hex values below.

- 15:50 MT: UI spec ready: research/gui/modo-selection-primitives.md. Use for selection/gizmo/primitives session after OCCT gate.

## Phase 2 — libcascade OCCT gate (2026-10-21)

Done. Prebuilt taucad libcascade 3.1.0 single-threaded WASM (OCCT V8_0_1, Emscripten 6.0.5) from `https://registry.npmjs.org/libcascade/-/libcascade-3.1.0.tgz`. Canonical files stay under gitignored `builds/libcascade/`; `web/fetch-libcascade.py` stages `web/dist/` (gitignored). Loaded next to `cadcam.wasm` with no `-pthread`.

`web/occt-gate.mjs` sews the current mesh, then requires `BRepCheck_Analyzer.IsValid()` and `ShapeAnalysis_FreeBounds` with zero free edges. Export enables only when watertight, units, and OCCT all pass. The interim banner hides only while the OCCT badge is green for the current shape.

`src/` was not edited. OCCT runs in JS beside the existing mesh WASM.

Acceptance (headless Edge + CTest `occt_gate`):
- `closed_box`: OCCT PASS, Export enabled, banner hidden.
- `open_box`: OCCT FAIL (4 free edges), Export locked, banner stays.
- CTest 6/6: watertight, units, export, gate, occt_gate, create.

## Selection, move gizmo, box and cylinder (2026-10-21)

Done in `web/` plus `tests/test_occt_gate.mjs` and `tests/test_occt_page.ps1`. No `src/` edits. No commit and no push. `web/cadcam.js` and `web/cadcam.wasm` were rebuilt so `replaceMesh` exists; both stay gitignored.

- Selection: Vertex (1), Edge (2), Face (3), Item (4) selects the whole body. Key 5 also selects Item. Alt+1..4 still switch tabs (Alt+4 is Export). Click replaces, Shift+click adds, Ctrl+click removes. Empty Vertex/Edge/Face means all, with no highlight. Hotkey 4 enters Item mode and selects the whole object.
- Hover uses `--hover-color`. Selection uses `--sel-color`. Active buttons use `--active-fill` and `--active-border`. Axis arrows use `--axis-x`, `--axis-y`, `--axis-z`. The hex values are the team choice below.
- Move gizmo only: X/Y/Z arrows, three planar handles, centre view-plane handle, Position XYZ in millimetres. No scale or rotate handles. Dragging a sub-element translates the whole solid and rebuilds once on pointer-up.
- Box: `BRepPrimAPI_MakeBox(gp_Pnt(cx-sx/2, cy-sy/2, cz-sz/2), sx, sy, sz)` after `Build()`. Cylinder: `BRepPrimAPI_MakeCylinder(gp_Ax2(base, dir), R, H)` after `Build()`, base = centre - dir*H/2. Signatures match libcascade 3.1.0. No partial angle. No Sides control.
- Each solid goes through `BRepCheck_Analyzer`, `ShapeAnalysis_FreeBounds`, the mesh watertight check, and the locked millimetre unit. Export stays off unless all three pass. The banner hides only when the OCCT gate is green.
- `?primitive=box&select=face` builds a box and selects one face. `window.__cadcamExportState` includes `selectionMode`, `selectionCount`, and `selectionAll`.

Node `tests/test_occt_gate.mjs`: ok. `closed_box` PASS. `open_box` FAIL, 4 free edges. Box gate and watertight PASS, 6 faces, 8 vertices, 12 edges, units mm. Cylinder Z and X PASS and watertight; Z has 3 faces, 2 vertices, 3 edges.

Headless Edge `tests/test_occt_page.ps1`: ok. `closed_box` green, Export on, banner hidden. `open_box` locked, banner stays. `?primitive=box&select=face` green, Export on, banner hidden, face mode, count 1. `?primitive=cylinder&select=item` green, Export on, banner hidden, item count 1. The script stops only Edge processes whose command line contains the test profile.

Still open, and not part of the team choice below: coplanar dot 0.999, tessellation deflection 0.5 mm and 0.5 rad, Sides/Segments, and the reference video frames. Mesh picking is the fallback when no OCCT solid is loaded. Box, cylinder, sphere diameter, pick tolerance, and the colour hex values are app defaults in the decisions table.

## Deploy smoke test (2026-10-21)

`web/assemble_site.py` is the only Pages file list. `pages.yml` calls it before the upload step, then runs `tests/deploy_smoke.py`. The inline `cp web/*.mjs` already included `selection.mjs`, `viewport-selection.mjs`, and `occt-primitives.mjs`; those names are now required in the assembler so a dropped module fails before upload.

The smoke test copies that same tree into gitignored `builds/deploy-smoke/_site`, serves it, and loads it in headless Edge with CDP cache disabled. It fails on any same-origin non-2xx, console error, page exception, or unhandled rejection. Local run: `closed_box` OCCT PASS, Export on (10 responses, all 2xx). `open_box` OCCT FAIL, Export locked. `?primitive=box&select=face` occtReady, gate PASS, one face. CTest `deploy_smoke` passed in 12.91s. Omitting `selection.mjs` from the temp site failed on HTTP 404 and `console.error: selection failed`; the source file was not removed. CTest skips with code 77 only when the browser or libcascade is missing and `CI` is unset. A data-URI favicon was added so headless Chrome does not 404 `/favicon.ico`. No `src/` edits. No commit.

## Native CTest before Pages upload (2026-10-21)

`pages.yml` installs Node 22, Ninja, g++, and CMake, fetches libcascade with `web/fetch-libcascade.py`, then configures and builds the native project at `builds/native` before `upload-pages-artifact`. The gate is `ctest --test-dir builds/native --output-on-failure` with `CI=true`, so `occt_gate` cannot skip when `builds/libcascade/dist` or Node is missing. `deploy_smoke` stays inside that CTest. Chrome is still installed first, and the old standalone smoke step is gone so the browser run happens once and still blocks upload. No `src/` or `CMakeLists.txt` edits: the native targets are C++17 and Qt stays optional. Banner and Export gate unchanged. No commit.

## L-bracket fuse, fillet, chamfer (2026-10-21)

Done in `web/occt-ops.mjs`, `web/index.html` (`?demo=lbracket`), `web/occt-primitives.mjs` (`inspectSolid` only), `tests/test_occt_gate.mjs`, `tests/fixtures/lbracket.json`, and `tests/deploy_smoke.py`. No `src/` edit. No `web/bindings.cpp` edit. No commit and no push. Banner text and the Export enable rule are unchanged.

libcascade 3.1.0 signatures used as declared in `builds/libcascade/pkg/package/dist/types.d.ts`: `BRepAlgoAPI_Fuse` / `Cut` / `Common` `constructor(S1, S2)`, fuse `SimplifyResult(true, true)`, `IsDone`, `HasErrors`, `Shape`; `BRepFilletAPI_MakeFillet` `constructor(S)` and `Add(radius, edge)`; `BRepFilletAPI_MakeChamfer` `constructor(S)` and `Add(distance, edge)`. `Shape()` is not called when `IsDone()` is false. A copy (`BRepBuilderAPI_Copy`, copyGeom true) is what the next step keeps. `delete()` runs only on wrappers that step has finished with.

`?demo=lbracket` builds the bracket from the app defaults. No query parameters are required. Optional query overrides (`legLengthMm`, `thicknessMm`, and the other spec fields) may be passed; absent fields stay on the defaults. `window.__cadcamExportState` gains `demo`, `opLog`, and `lastError`.

## App defaults

Every value in this table is a team choice (Erik 7:00 PM MT), not a sourced spec.

| What | Value |
| --- | --- |
| `LBRACKET_LEG_LENGTH_MM` | 40 mm |
| `LBRACKET_LEG_WIDTH_MM` | 20 mm |
| `LBRACKET_UPRIGHT_HEIGHT_MM` | 40 mm |
| `LBRACKET_THICKNESS_MM` | 4 mm |
| `LBRACKET_OVERLAP_MM` | 4 mm |
| `LBRACKET_CORNER_X_MM`, `LBRACKET_CORNER_Y_MM`, `LBRACKET_CORNER_Z_MM` | 0, 0, 0 |
| `LBRACKET_INNER_FILLET_RADIUS_MM` | 2 mm |
| `LBRACKET_CHAMFER_DISTANCE_MM` | 0.5 mm on the outer edges |
| `LBRACKET_INNER_EDGE_MODE` | `auto` |
| `LBRACKET_CHAMFER_EDGE_RULE` | `outer-leg-end-edges-along-width` |
| `LBRACKET_FILLET_LIVE_PREVIEW` | off (preview updates on apply) |
| Final bounding box | 40 × 20 × 40 mm |
| Hotkey 4 | Item mode, select the whole body. Key 5 also selects Item. Alt+4 still opens Export. |
| `PICK_TOLERANCE_PX` | 8 px |
| `--hover-color` | `#d7f4ff` (light highlight) |
| `--sel-color` | `#ff4fd8` (strong accent) |
| `--axis-x`, `--axis-y`, `--axis-z` | `#ff2d2d`, `#2ee66b`, `#3d7eff` |
| `--active-fill`, `--active-border` | `#5b3cc4`, `#ffffff` |
| `BOX_EDGE_MM` | 20 mm (20×20×20) |
| `CYLINDER_DIAMETER_MM`, `CYLINDER_HEIGHT_MM` | 20 mm, 20 mm (radius 10 mm) |
| `SPHERE_DIAMETER_MM` | 20 mm. Constant only. No sphere primitive. |

Overlap is 4 mm, the same as the thickness, so the upright is 4 mm stock, the two boxes share the corner block, and the inner edge is one line. The corner is the origin, so the fused solid is 40 × 20 × 40 mm. The chamfer is 0.5 mm on the two outer edges that run along the width (the base tip's top edge and the upright's outer top edge). Those cuts stay inside the silhouette, so the bounding box stays 40 × 20 × 40 mm. `auto` finds the concave corner edge. Live preview is off: the fillet is applied once, when the build runs.

`tests/fixtures/lbracket.json` matches these values (thickness 4). The node test builds `builds/export/lbracket.stl` from the app defaults and checks that STL for a 40×20×40 mm watertight box. `web/assemble_site.py` does not copy `tests/` or `tests/fixtures/` into the site. The deploy smoke test requires `/tests/fixtures/lbracket.json` and `/fixtures/lbracket.json` to return 404, and requires `?demo=lbracket` to pass the gate with op log `fuse,fillet,chamfer`.

## Interactive Booleans (2026-10-21)

Done in `web/occt-ops.mjs`, `web/occt-primitives.mjs`, `web/index.html`, `tests/test_occt_gate.mjs`, and `tests/deploy_smoke.py`. No `src/` edit. No commit and no push. Banner text and the Export enable rule are unchanged. Union, Cut, and Intersect call the existing `fuseShapes`, `cutShapes`, and `commonShapes` wrappers. `Shape()` is still skipped unless `IsDone()` is true. A failed or empty result is deleted and both inputs stay in the scene.

The user selects whole bodies with hotkey 4 (Item). The order is shown as `1` target and `2` tool on the Boolean label, the Items row, and viewport badges. Cut is body 1 minus body 2. The toolbar buttons stay disabled unless exactly two bodies are selected, and the enabled or active state uses the existing `.is-on` and `:disabled` button styles. The result replaces those two bodies. There is no undo stack, no history tree, and no Boolean of three or more bodies.

`?demo=booleans` cuts a Z cylinder (diameter 10 mm, height 30 mm, same centre as the box) from the 20 mm box. `?demo=booleans&op=union|cut|intersect` selects the op. `?pair=overlap` leaves the two boxes in the scene so the buttons can run the op.

## App defaults — Booleans and mesh

Boolean values are a team choice, 2026-10-21. Mesh values are a team proposal, sourced from the OCCT Mesh user guide (https://dev.opencascade.org/doc/overview/html/occt_user_guides__mesh.html), and the same team choice date. Confirmed field names in libcascade 3.1.0 `IMeshTools_Parameters`: `Relative`, `Deflection`, `Angle`, `ControlSurfaceDeflection`, `InParallel`. They are passed to `BRepMesh_IncrementalMesh(shape, parameters)`. Display and export both use that call.

| What | Value |
| --- | --- |
| `BOOLEAN_BOX_EDGE_MM` | 20 mm, centred on the existing box primitive `(0, 0, 10)` |
| `BOOLEAN_OVERLAP_SHIFT_MM` | 10 mm on X. Overlap is 10 × 20 × 20 mm |
| Overlap volumes | Union 12000 mm³, Cut 4000 mm³, Intersect 4000 mm³. Tolerance `BOOLEAN_VOLUME_TOL_MM3` = 1e-3 mm³ |
| Overlap bounds tolerance | `BOOLEAN_BOUNDS_TOL_MM` = 1e-3 mm (`BRepBndLib.Add`, exact geometry) |
| `BOOLEAN_DISJOINT_SHIFT_MM` | 40 mm. Intersect is empty, reported, and both inputs are kept |
| Empty result | volume ≤ `BOOLEAN_EMPTY_VOLUME_MM3` (1e-4 mm³), or no solid, or no triangles |
| `BOOLEAN_DEMO_CYLINDER_DIAMETER_MM` | 10 mm |
| `BOOLEAN_DEMO_CYLINDER_HEIGHT_MM` | 30 mm, axis Z, same centre as the box |
| `BOOLEAN_DEMO_OP` | `cut` (box minus cylinder) |
| Demo curve volume tolerance | `BOOLEAN_CURVE_VOLUME_TOL_MM3` = 1e-2 mm³ |
| `TESSELLATION_RELATIVE` | `false` (`IMeshTools_Parameters.Relative`) |
| `TESSELLATION_DEFLECTION_MM` | 0.05 mm (`IMeshTools_Parameters.Deflection`) |
| `TESSELLATION_ANGULAR` | 0.2 rad (`IMeshTools_Parameters.Angle`) |
| `TESSELLATION_CONTROL_SURFACE` | `true` (`IMeshTools_Parameters.ControlSurfaceDeflection`) |
| `TESSELLATION_IN_PARALLEL` | `false` (`IMeshTools_Parameters.InParallel`) |

Re-export of `builds/export/lbracket.stl` with those mesh settings: 92 triangles, 4684 bytes, final tessellation 5.2 ms (CTest `occt_gate`, 2026-10-21). Node also writes `builds/export/boolean-union.stl`, `boolean-cut.stl`, `boolean-intersect.stl`, and `boolean-demo.stl`. The demo cut STL was 268 triangles and 13484 bytes, watertight, millimetre header, box bounds.

## Blink L-bracket (2026-10-21)

Withdrawn layouts and the acceptance-fixture dimensions are kept only in the gitignored local notes (tests/fixtures/blink.notes.md). The app has no baked-in Blink layout.


### Change of plan 2026-10-21 20:46 MT (Erik)
The baked-in Blink layout above is withdrawn and kept as a test fixture only. Work now follows prompts/mobile-1..5 (primitives, transforms, holes, fillet and chamfer, touch Booleans). New team choices: 44 px touch targets, a 20 px touch pick radius (mouse stays 8 px), and the hole tool defaults to 4.5 mm with a 9.5 mm countersink (unverified fit).

### Mobile touch team choices (Chief, 2026-10-21 20:48 MT; source research/mobile-touch-cad.md)
| Item | Value | Status |
|---|---|---|
| Snap | 1 mm for move and resize, 15 degrees for rotate, on by default, 44 px toggle | team choice |
| Steppers | 1 mm per tap, 0.1 mm per tap on long press (400 ms, Android default) | team choice |
| Tap vs drag | under 8 px of movement counts as a tap | team choice (Android touch slop 8 dp) |
| Gizmo zones (finger) | at least 44 px; one Move/Rotate/Scale mode at a time behind a 44 px switch | team choice |
| Touch edge pick | about 20 px radius, edges win over faces, Face/Edge filter, tap again to cycle | team choice |
| Number fields | type=text inputmode=decimal, fixed mm label, steppers at least 44 px | team choice |

## Mobile step 1: primitives (2026-10-21)

Team choices for this step. None of these are Erik measurements.

| Item | Value | Status |
| --- | --- | --- |
| Touch target | at least 44×44 CSS px (WCAG 2.5.5 / Apple HIG) | team choice |
| Touch pick radius | 20 px. Mouse stays 8 px | team choice |
| Box | 20 mm | team choice |
| Cylinder | diameter 20 mm, height 20 mm | team choice |
| Disc | diameter 18 mm, thickness 4 mm | team choice |

The existing bottom-on-zero placement stays. A disc sits with its centre at z = thickness / 2, so the default centre is (0, 0, 2) mm and the axis is Z.

The narrow layout shows a touch toolbar for Box, Cylinder, and Disc. Each one opens the millimetre dimension panel (`type=text`, `inputmode=decimal`, 44 px steppers). The same panel edits a primitive after it exists. A rejected edit keeps the last solid and the typed values. `?primitive=disc` is the test hook. `?demo=lbracket` (40 mm) and `?demo=booleans` stay.

Countersunk through-holes, flush-disc fuse, fillet and chamfer on Confirm, Union / Cut / Intersect, and the Item-mode gizmo stay as general tools. Fillet and chamfer defaults are `EDGE_FILLET_RADIUS_MM` 2 and `EDGE_CHAMFER_DISTANCE_MM` 0.5 in `web/occt-ops.mjs`.

The camera-bracket acceptance solid is in local, gitignored tests/fixtures/blink.* files only. Its dimensions are in tests/fixtures/blink.notes.md. `web/assemble_site.py` does not ship `tests/`. Node writes `builds/export/prim-box.stl`, `prim-cylinder.stl`, `prim-disc.stl`, and `blink.stl` when the fixture is present.

### Mobile step 1 results (Pilot, 21:17 MT)
PASS, not yet committed. Box, Cylinder and Disc touch toolbar with editable mm panels, 44 px targets and a 20 px touch pick. ?demo=blink is out of web/, and the layout lives in tests/fixtures/. CTest 7/7, occt_gate passed, deploy_smoke passed including a 390x844 portrait run, and the fixture URLs return 404. STLs are watertight and in mm (box 8000 mm3 exact, cylinder 6272.8/6283.2, disc 1016.2/1017.9). Gaps: the portrait panel covers the view and the Home button overlaps it (moved to step 2), touch has only been tested in emulation, and Erik still needs to review the index.html and occt-ops.mjs diffs.

## Mobile step 2: transforms (2026-10-21)

Team choices for this step. None of these are Erik measurements. Snap and steppers were settled by Chief at 20:48 MT.

| Item | Value | Status |
| --- | --- | --- |
| Gizmo modes | one of Move, Rotate, Scale at a time, 44 px switch | team choice |
| Handle pick zone | 44×44 CSS px square (Chebyshev), finger and mouse | team choice |
| Tap vs drag | movement under 8 CSS px is a tap | team choice |
| Snap | on by default; 1 mm move/resize, 15 deg rotate | team choice |
| Steppers | 1 mm or 15 deg per tap; long press 400 ms then 0.1 mm or 1 deg | team choice |
| Euler | CAD X then Y then Z, around the primitive centre | team choice |
| Resize | axis handles change that size, centre stays, floor 0.1 mm | team choice |
| Portrait sheet | collapsed bottom sheet; expanded max 40% of the view, never over Home | team choice |

`web/occt-ops.mjs` `transformShape` uses `gp_Trsf` + `BRepBuilderAPI_Transform` (copyGeom true), `IsDone()` before `Shape()`, then a copy. A failed or empty result leaves the input. Box, cylinder, and disc still rebuild from parameters; rotation is applied after the solid is made. Typed mm and degree fields stay in the dimension sheet and stay editable after creation.

The portrait 390×844 sheet starts collapsed above the touch toolbar. Expanding it keeps Home clear. The 8 px tap/drag rule is on the viewport Pointer Events path (`touch-action: none` already on `#viewport` and `#canvas`).

### Mobile step 2 results
PASS, not committed. CTest with CI=1: 7/7 passed (`occt_gate` Passed). `deploy_smoke` passed, including 390×844 portrait: box/cylinder/disc create and edit, Home clear of the bottom sheet, gizmo handles 44 px, then box move (cx 5, stepper to 6), rotate Z 15°, resize sy 22, snap on, gate PASS. Node wrote watertight millimetre STLs `prim-box-moved.stl`, `prim-box-rotated.stl`, and `prim-box-resized.stl`. No `src/` edits. Gaps: touch is still emulation only; Erik still reviews `index.html`, `occt-ops.mjs`, and `viewport-selection.mjs`.

2026-10-21 — Portrait 390: the mode row, primitive toolbar, mm/in toggle, and status line wrap inside the screen. The tool strip's actions stay on the Tools sheet so nothing is cut off at the right edge. Touch targets stay at least 44×44.

- Team choice (Chief, 2026-10-21 22:48 MT): the narrow tool strip is hidden in portrait; its actions open from the Tools button. On Erik's approval list.

## Queue - next after step 3 push (Erik, 2026-10-21 23:14 MT)
- Tool menu back to a single row, one icon high, so it no longer blocks the 3D viewport. Extra icons scroll or overflow (no wrapping), targets stay at least 44 px. Smoke test: tool menu stays one icon high on desktop and at 390x844. This replaces the step 2 wrap behaviour for the tool menu only. Owner: Pilot.
- Chief detail (23:16 MT): the menu scrolls sideways inside its own container (flex-wrap: nowrap, overflow-x: auto, scroll-snap-type: x mandatory, buttons flex: none at 44 px, explicit toolbar height). Smoke test: all buttons share one top, toolbar height is one button plus padding, page scrollWidth <= innerWidth at 390x844 (the toolbar itself may scroll). Sheet rows keep wrapping.
- Erik request (23:17 MT), same session as the tool menu: move the Info button up into the Tree button's row in the top menu so it stops taking viewport space. Erik suggests left of the part name box; final spot is a team call, recorded here once chosen. Targets >= 44 px. Smoke test: Info and Tree share the same getBoundingClientRect().top on desktop and at 390x844, and the page-level overflow check still passes.
- Team choice (Chief, 23:19 MT): Info sits in the Tree row, left of the part name box. At 390 px the part name text truncates with an ellipsis; buttons keep 44 px. Smoke test adds the ellipsis/44 px check.

2026-10-21 — Hole tool team choice: 4.5 mm hole, 9.5 mm countersink at 82° (#8 wood screw, unverified fit; 90° stays the editable metric ISO angle), through or blind (blind default 6 mm), countersink on, 1 mm snap with typed values overriding it, plate 80×40×6 mm with holes at 20×20, 40×20 and 60×20 mm from the face edges, closed inspector inert.
- Erik request (23:19 MT), same session: Home must aim the camera at the world origin (0,0,0). First report what Home aims at now (selection or scene bounding-box centre?). Keep the zoom-to-fit distance; change only the target. Test: after Home, camera target is (0,0,0) within 1e-6, with and without a selection.

- Home fix detail (Research Digest, 23:21): target is set to bbox centre at web/index.html:4385 and goView('home') (4198-4200) never resets it. Fix: set target (0,0,0) in goView('home'); fit radius = distance from origin to farthest bbox corner. Test adds: all 8 bbox corners project on-screen after Home. Leave section/clip cy alone.
- Queue 4 (Erik 23:21, after Home fix, same UI session if it fits): Search collapses to icon only (>=44 px). Tap/click opens box + results; Esc, tap outside, or icon again collapses. Test: collapsed box takes zero space and can't be focused; open shows box and results on desktop and at 390x844.
- Search detail (Chief accepted 23:2x): WAI-ARIA disclosure (button with aria-expanded/aria-controls; collapsed box hidden). Open focuses input and sets aria-expanded=true; Esc collapses and returns focus to icon. Phones: opens over the viewport, does not push tool row; results stay visible when on-screen keyboard shrinks the view. Session limited to these 4 items, one combined result.

- Check policy (Chief, 2026-10-22 00:52 MT, team choice): Must-haves: units gate on Export (watertight dropped 2026-10-22 02:17 MT, Erik's call); CI green before Pages deploy; secrets+Blink scan before each push; geometry asserts (volume, faces) when occt-ops/kernel changes. UI-only (web/ + docs) pushes: skip geometry asserts, extra local re-runs and the local C++ rebuild; rely on CI plus one 390x844 smoke test (closed-panel and toolbar checks merged into it). Screenshots once per batch. .wasm check folded into the pre-push secrets scan. Never push a failing build.
- 2026-10-22 — Home before the fix: mesh reload sets the orbit target to the bbox centre; goView('home') then recenters it to (0, 10, 0), not the selection and not (0, 0, 0). Fit distance still uses half the bbox diagonal.
- 2026-10-22 — Part name keeps a 72 px minimum at 390 px with ellipsis. One search button remains. Viewer meshes flip triangle order on the Y/Z swap so countersink normals point out of the material.
- TOP PRIORITY (Erik 01:53 MT, iPhone on live ca5a38f, 'Tools still blocking'): first check whether Pages serves ca5a38f or a cache. On ~390 px iPhone Safari: top bar one row with Info in the Tree row, search icon-only, tool row one icon high and scrolling sideways, Home not floating over the view, property panel collapsed by default or small. Smoke test for visible viewport fraction at 390x844 (Chief ruling: >=70% clear with panel collapsed, >=50% with panel open, panel opens on tap only; gate runs in WebKit iPhone 13 profile as well as Chromium; 100dvh plus safe-area insets; visible build stamp on page and script URLs) plus a screenshot. Ahead of undo/redo, shading, tooltips and step 4.
- Folded into the phone fix (Erik 02:00 MT): Box, Cylinder, Disc and Hole move out of the viewport row into a new 'Create' menu on the bottom bar, with Sketch inside it too. Team to choose (record as team-chosen): icon, sheet vs popover, and what happens to the existing bottom-bar Sketch tab. Create menu covered by the smoke test and the viewport-clear check (>=70% collapsed / >=50% open, WebKit iPhone 13); screenshot with build stamp.
- Create menu, team-chosen (Chief 02:01 MT): '+' icon labelled Create on the bottom bar replaces the old Sketch tab (removed). Opens as a bottom sheet on phones, popover on desktop; holds Box, Cylinder, Disc, Hole, Sketch; targets >=44 px; closes after a pick, on Esc or a tap outside. Primitive buttons removed from the viewport row entirely. Smoke test: menu opens with all five items and no primitive buttons remain elsewhere. 70% clear rule measured with the menu closed; the transient sheet is exempt from the 50% rule.
- Part name, team-chosen (Chief 02:01 MT): 72 px truncated it to 'Pa...' on Erik's 1:53 live screenshot (new build, not cache). Name takes the remaining Tree-row width (flex: 1, min 96 px). Smoke test: 'Part 1' shown in full at 390 px.
- Overnight queue (Erik via 3T, 02:14 MT; team decides, safety rules unchanged; 30-min check-ins; screenshots with live link): after the phone fix, 1) decide Grok Build vs Cursor cloud agents for coding, with reasons; 2) nav cube visible on mobile; 3) project file save/load; 4) assembly system (separate parts, then combine); 5) more tools incl. selection, team picks; 6) Acceptance A: Blink bracket built in app, exported/saved, opened and sliced in OrcaSlicer on Z13 (Blink stays out of public repo); 7) Acceptance B: toy truck assembly, PLA wheels + TPU tires, multi-plate Orca slice, no printer send. Undo/redo, shading, tooltips and step 4 still queued; order relative to items 2-5 TBD by team.

- Watertight checks/tests DROPPED (Erik's call 2026-10-22 02:17 MT, confirmed by 3T, decided by the Chief). Export no longer waits on a watertight result. Kept: units checks unchanged, and the OCCT shape-validity check after fillet, chamfer, Boolean and delete (a failed op becomes a clean error; never blocks Export). Pilot removes the watertight assertions from the gate and CI as a separate small commit. Older Done entries above that mention watertight are history and stay as written.
- CI (Chief 02:19 MT, team choice): new .github/workflows/ci.yml approved, goes in the phone fix batch. Runs the same build and tests on pull_request, no Pages deploy (pages.yml still runs only on push to main). Repo Keeper turns on branch protection requiring ci.yml after its first green run, admin enforcement off.
- Free-edge count (Research Digest suggestion, Chief 02:19 MT, team choice): approved as information only in the export log. Does not fail CI, does not block Export.
- Next small Grok Build batch, in order (Chief 02:19 MT, team choice): 1) gizmo drag bug FIRST (Erik 02:19 MT: dragging the move gizmo doesn't work right). Pilot reproduces with a mouse drag on desktop and a touch drag in WebKit iPhone 13 profile, posts the root cause before the fix. Smoke test: an X drag moves the body by the expected mm within 0.1 mm and counts as one undo step. 2) undo/redo, 3) shading, 4) tooltip.
- Item 5 tools (more tools incl. selection):
  - Selection tools (team picks).
  - Delete (Chief spec): whole solid: select it, then the trash icon in the selection bar or Del; confirmation optional because undo restores it. Face: deleting a face removes holes, fillets, chamfers and bosses with the rest healed closed; if OCCT can't close it, clean error and the model is unchanged. Edges and vertices can't be deleted on their own: delete removes the owning fillet, chamfer or feature, otherwise shows 'Can't delete this edge on its own' and the model is unchanged. After every delete the validity check runs, a failure rolls the change back, and each delete is one undo step.
  - Fillet and chamfer (step 4), then type-in resize right after (Erik 02:19 MT request; Chief 02:19 MT spec): with a body selected the panel shows its size fields in mm, at least 44 px tall. Primitives show their own parameters (box LxWxH, cylinder diameter x H, disc diameter x T); any other body shows bounding-box X, Y, Z with a lock-proportions toggle. Applies on Enter or blur. Zero, negative or blank gives a clean error. Each change is one undo step. Smoke test: set a box to 30 mm and its bounding box is 30 mm within 0.01 mm.
- Research notes (Research Digest, 02:20 MT). Gizmo drag bug, things to check: turn camera controls off on TransformControls 'dragging-changed'; set touch-action: none on the canvas for iOS; apply the drag as a transform on the OCCT shape when the drag ends so the body doesn't snap back. Type-in resize: primitives rebuild from their real parameters; other bodies scale per axis with BRepBuilderAPI_GTransform, and the UI warns that circles can become ellipses. Bounding box for the size fields and the 30 mm test: use BRepBndLib::AddOptimal (useTriangulation=false), not Add, which pads the box by the shape's tolerance.
- Tooling (Chief 02:17 MT, team choice, tonight only): HYBRID Grok Build + Cursor cloud agents, merge rules and git pull --ff-only per the "Overnight override 2026-10-22" section in mvp/tooling-priority.md. Final order: phone fix (with ci.yml) -> gizmo drag bug -> undo/redo -> shading -> tooltip -> item 2 nav cube (prompts/nav-cube-mobile.md) -> item 3 save/load (prompts/project-save-load.md) -> item 4 assembly -> item 5 tools (step 4 fillet/chamfer, type-in resize, step 5 Booleans, then selection tools and delete) -> Acceptance A -> Acceptance B.
- Chief rulings 02:21 MT (team-chosen): assemblies are a flat parts list (one solid each, with a placement in mm and a material tag); Combine fuses the selected parts into a new part; no mates or joints; export writes one 3MF object per part with its material. Resize lock-proportions is ON by default, and turning it off shows a note that circles may become ellipses. Save format is .cadmvp JSON (see prompts/project-save-load.md). Orca filament/plate assignment check moves into Acceptance B (Pilot). Shapr3D touch patterns dropped for now. Cursor nav-cube launch goes first after Pilot reviews the prompts.
- Overnight ground rules (Erik via 3T, 02:22 MT): the team works without Erik's input. Cursor launches: post the final prompt in the room and tag 3T; 3T launches it and posts the PR link. Anything that truly needs Erik is logged here as PARKED and the team moves on; never wait on him. Pick the cheaper path when options are equal. If Z13 drops or sleeps, post it and switch to work that doesn't need Z13 (docs, research, Cursor PRs).

## DECISIONS log (Doc Steward keeps this; Erik 2:23 AM MT: nothing is parked for Erik. Team discusses, Chief rules, contested items go to 3T)
- 2026-10-22 Nav cube merged onto main `fbd0947` (gizmo drag, undo stack, phone pixel-ratio fix). The drawn cube still comes from `cubeRect` (safe-area top and right, 88 px on a phone). Its WebGL viewport and scissor are those CSS pixels. This three.js multiplies them by the pixel ratio, which is the gizmo batch's buffer fix. Multiplying again would draw the cube off the phone buffer.
- 2026-10-22 Nav cube phone defaults (Chief 02:23 ruling, applied on the PR branch): the existing `#viewCube` is 88 CSS px on the narrow layout, top-right. The inset is 8 px or the part of the screen safe-area inset that still overlaps the viewport, whichever is larger, so the top bar's own safe-area padding is not applied twice. Home sits 8 px left of a 44 px hit pad. That pad is left of and below the cube, inside the viewport. It holds 6 face zones and 8 corner zones, each 44×44 CSS px, with every center outside the visible cube so the rect extends past it. Phones have no edge zones. Taps on the drawn cube still pick the face or corner under the finger; an edge hit on the mesh snaps to that face. Desktop keeps raycast face, edge, and corner picks on the larger cube. A snap copies the three.js r160 ViewHelper move without importing it: the camera orbits the current target at a fixed distance, eased over 250 ms (1 ms when prefers-reduced-motion is set). The 250 ms clock starts on the first animation frame. A headless frame can be timestamped later without lengthening the ease. Taps during that move are ignored, except a second cube tap within 320 ms, which is the double-tap home iso (same direction as the Home button, current distance, current target). The smoke check sends those two pointer-ups 80 ms apart inside one page turn, because a CDP round trip between taps can pass the 320 ms window and leave the camera on the first face. A pointerup that ends a drag past the 8 px slop does not snap. Units stay mm. No C++ or bindings change.
- 02:23 Nav cube: adapt #viewCube, 88 px phone cube top-right, 6 face + 8 corner taps, corner hit areas at least 44 px, edge taps desktop-only, double-tap home, snaps 250 ms or less, no ViewHelper (Chief).
- 02:23 Save/load: loading clears undo, prompts first on unsaved changes; BREP via own binding with stringstream; stays Cursor since CI builds cadcam.wasm from source (Chief, Pilot confirmed).
- 02:23 Launches wait until phone fix + ci.yml are on main (Repo Keeper, Chief).
- 02:49 Root PROGRESS.md stays untracked and untouched (Blink layout and local paths fail public-repo rules) (Chief).
- 2026-10-22 — UI session 2: viewport stays at least 70% clear with the dimension panel collapsed and 50% with it open, Create menu, visible build stamp on the page and script URLs, WebKit iPhone 13 phone smoke.
- 02:49 Push of phone fix held until WebKit blank-view fix and canvas pixel check pass (Pilot; Repo Keeper holds).
- 02:49 Fix session adds: canvas pixel check that fails in WebKit before the fix and passes after; sheet-vs-popover test (390 px sheet only, desktop popover only); any src/ change posted first and kept in its own commit (Chief). Real-iPhone check stays open, since Playwright WebKit is not iOS Safari (Research Digest).
- 2026-10-22 — UI session 3: the blank WebKit 3D view was #occtBanner leaving the flex column when the OCCT gate passed. The viewport grew, ResizeObserver called renderer.setSize, and headless WebKit stopped compositing the canvas. The framebuffer still held the plate (WebGL2, no context loss). The banner is now an overlay, and setSize is skipped when the buffer already matches. Phone smoke canvas check failed before the change and passed after in WebKit and Chromium. Title tooltips clear on pointerup, touchend, and blur. Create is a bottom sheet at 390x844 and a popover at 1440x900.
- 03:38 WebKit blank view was our bug and is fixed; pixel check stays a hard failure (Pilot, per Chief's 02:49 ruling). Push pending Chief go.
- 03:39 Push approved (Chief, 3T final). Screenshot cleanup and Dimensions-box check go in the next Grok batch after the gizmo bug, before undo/redo. Pilot logs start/done/end times per run and investigates the post-done-marker hang (Chief).
## Project file save/load (2026-10-22)

BREP symbols in the prebuilt libcascade 3.1.0 (`builds/libcascade/dist/opencascade_single.js.symbols`, plus a runtime probe):

- `BRepTools` is exported to JavaScript.
- The linked `Write` symbol is the file-path overload `BRepTools::Write(TopoDS_Shape const&, char const*, bool, bool, TopTools_FormatVersion, Message_ProgressRange const&)`. A box write returned true. The text starts with `DBRep_DrawableShape` and contains `CASCADE Topology`.
- File-path `BRepTools::Read(TopoDS_Shape&, char const*, BRep_Builder const&, Message_ProgressRange const&)` is exported. The probe read the box back and `IsNull` was false.
- The `std::ostream` / `std::istream` overloads of `Write` and `Read` are not in the symbol map.
- `cadcam.wasm` does not link OCCT, so a `std::stringstream` wrapper cannot be compiled into that module.

The binding is `web/project-file.mjs`. It calls those file-path methods, copies the BREP text out with `FS.readFile`, and `FS.unlink`s the temporary file. The `.cadmvp` document is plain JSON and stores that text. This is the binding the prebuild can actually call. It is flagged for Erik review. It is not a stringstream binding, and the stored file is not a virtual path.

Team choices for the format and the load path (not Erik measurements):

- `version` is the number `1`. Any other value, including `"1"`, is an error.
- The extension is `.cadmvp`. The top-level `units` field is always `"mm"`.
- Each part has `name`, `placement` `{x,y,z}` in millimetres, `material`, `primitive` (`{kind, parameters}` or null), `features` (an array), and `shape` (BREP text that contains `CASCADE Topology`).
- `placement` is taken from `params.cx/cy/cz`, or 0 when those are missing. On load, `placement` is copied onto `cx/cy/cz` before a parameter rebuild.
- Missing `material` is saved as `"default"`.
- Parameter rebuild runs for `box`, `cylinder`, and `disc` only when `features` is empty. A non-empty `features` list, or any other kind, keeps the BREP text. A rebuilt shape that fails `checkOcctShape` falls back to BREP. A failed BREP validity check rejects the whole file.
- BREP write flags: triangles on, normals off, `TopTools_FormatVersion_CURRENT`.
- The round-trip box is `BRepBndLib::AddOptimal` with `useTriangulation` false and `useShapeTolerance` false.
- An empty `parts` array is a valid empty project. `replaceMesh` rejects an empty index list, so the viewer hides the solid and the previous kernel mesh is left unloaded from the screen. An empty file, bad JSON, a missing or non-`mm` `units` field, or an unknown version is an error and does not change the model.
- Load does not change the mm/inch display toggle. Save reads millimetre parameters and the OCCT shape, not the displayed numbers.
- The download name is the document name with characters outside `[A-Za-z0-9._-]` replaced by `_`, plus `.cadmvp`. The blob type is `application/json`.
- The file input `accept` is `.cadmvp,application/json,text/plain` so iOS can see the file. The control is a label with the input at opacity 0, `font-size: 16px`, and no `capture`. The File menu stays open until a file is chosen.
- Confirm runs after a successful parse. Dirty model: "Replace the current model? Unsaved changes will be lost." Clean model: "Replace the current model with this file?" Cancel leaves the model unchanged.
- A successful load calls the real `window.__cadcamClearUndo` from the gizmo batch. That function runs `commandStack.clear()` in `web/undo.mjs` and frees the before/after snapshots. Save/load does not install a no-op over it. Undo and redo buttons still call `doUndo` and `doRedo`.
- Save uses an `<a download>` blob. `showSaveFilePicker` is not used; it is not available on iOS Safari.

Manual iPhone file-picker check: not run on a physical device. Playwright WebKit is not iOS Safari. `tests/phone_smoke.py` covers the 44 px Save and Load controls, the hidden-input rule (`display` is not `none`), and the same hook round trip as `tests/deploy_smoke.py`.

Error strings: empty file "This file is empty. The model was not changed."; unreadable file "This file could not be read. The model was not changed."; units "This file is not in millimetres. The model was not changed."; version "This file version is not supported. The model was not changed."; shape "A part failed the shape check. The model was not changed."; save "The project could not be saved."; cancel "Load cancelled. The model was not changed."

- 04:31 Phone fix + ci.yml on main (d8d04df); ci.yml green on main; docs in 57e6d47. Branch protection on main requires CI build check, admin enforcement off (Repo Keeper). Nav cube launch cleared (3T).

- 04:33 MT (Chief): undo/redo is built in the gizmo batch (before and after snapshot command stack, Ctrl+Z/Ctrl+Y, a drag counts as one step, load clears the stack), and resize and delete launch after it merges. Unlocked GTransform resize is in scope, with the ellipse note, validity check plus rollback, and lock on by default. The trash icon goes in the property sheet header (44 px or more, shown only when something is selected), and Del also deletes on desktop. The face-delete fixture is a 40x20x10 box with a 6 mm hole, built in the test and not from Blink.
- 04:50 MT (Chief): landing order is (1) the gizmo batch, green and pushed, then (2) PR #1, rebased on the new main with build green, then (3) save/load, rebased the same way. Save/load launches now and only calls the clearUndo hook. Pilot takes the nav cube phone screenshot after PR #1 deploys.
- 05:16 MT (3T final call, replaces the 04:50 order): the new landing order is PR #1 (green on 61cb5b2, 7/7 CTest) merged now, then the gizmo batch rebased on top, then save/load.
- 05:16 MT (settled after crossed messages; 3T, latest, replaces the 05:16 final call above): PR #1 is held until Pilot says where the gizmo batch is editing. If it is editing files on Z13, the gizmo batch lands first, then PR #1 rebased, then save/load. If it isn't, PR #1 merges right away. Docs get committed locally now and are not pushed until main settles.
- 05:25 MT: PR #2 (save/load) deviates from the prompt. libcascade 3.1.0 exports only the file-path versions of BRepTools::Write/Read, not the stream versions, so web/project-file.mjs writes a temp file in the Emscripten virtual file system and deletes it afterward (commit b2f43b1, flagged for Erik). Load calls window.__cadcamClearUndo, a hook only. Settled: the gizmo batch is editing on Z13 (Grok PID 33776), so it lands first, then PR #1, then PR #2, each rebased. Gizmo root cause: commitGizmoDrag calls translateBody, which never transforms the actual shape.
- 2026-10-22 — Gizmo batch: a move drag transforms the OCCT solid and is one before/after undo step (Ctrl+Z / Ctrl+Y, load clears the stack). Phone plate shots press Home and clear the selection; the Dimensions chip was the opening toast. The phone plate and view cube were drawn off the buffer because setViewport was given buffer pixels; it now gets CSS pixels.
- 06:05 MT: PR #2's temp-file BRep approach replaces Research Digest's earlier C++ stream suggestion, since libcascade 3.1.0 exports only the file-path versions. The gizmo batch is done (web only): the drag moves the solid with transformShape, kept only if the OCCT gate passes; web/undo.mjs adds a before and after snapshot stack, one undo step per drag, Ctrl+Z/Ctrl+Y, and window.__cadcamClearUndo for PR #2; the phone pixel-ratio bug is fixed. Open for the next batch: status bar volume 18706.522 vs smoke log 18704.789 mm3, a yellow plate outline when nothing is selected, no Undo/Redo buttons on the phone, and gizmo_drag_smoke not yet in CTest.
- 2026-10-22 — Selection delete (this PR): the trash icon is in the property sheet header (`#deleteBtn`, 44 px, hidden until something is selected) on phone and desktop. Del deletes only when the viewport is at least 821 px wide, and not while an input is focused. Face delete calls `BRepAlgoAPI_Defeaturing` with `SetToFillHistory(true)`. `IsDone` false, `HasErrors`, or `AlertUnableToRemoveTheFeature` leaves the model unchanged and shows "Can't remove this face. The model was not changed." The hole fixture is built in the test (40×20×10 mm box, 6 mm through-hole), not from Blink. Volume is `BRepGProp` and must match the plain box within 0.01. An edge or vertex deletes every recorded fillet or chamfer whose generated face contains that sub-shape, as one undo step. Assumption, not a chief ruling: a vertex shared by several recorded features removes all of them. No owner shows exactly "Can't delete this edge on its own." `TopTools_IndexedMapOfShape` is the libcascade alias `NCollection_IndexedMap_TopoDS_Shape_TopTools_ShapeMapHasher`. Deleting the last body sets `sceneCleared` so the viewer and export ignore the stale kernel mesh. `replaceMesh` still rejects an empty index list, so there is no bindings change. Each delete is one step on `web/undo.mjs`. Success prints `DELETE_DONE`. An empty-project load still uses `projectBlank` and does not clear that undo step. Type-in resize stays its own undo step.
- 2026-10-22 — Type-in resize: lock on by default. A locked primitive rebuilds from its own parameters (box L×W×H, cylinder diameter×height, disc diameter×thickness) and scales every size by the first changed field. A locked non-primitive uses gp_Trsf.SetScale about the AddOptimal centre (BRepBndLib.AddOptimal with useTriangulation false and useShapeTolerance false). Lock off, on any body, uses BRepBuilderAPI_GTransform in the body's local axes and shows "Circles may become ellipses." Every resize runs BRepCheck_Analyzer; an invalid result or a throw drops the new shape and keeps the last good one, with no undo step. A successful resize is one step on the gizmo command stack in web/undo.mjs. Stored lengths stay millimetres; the inch toggle only changes the field text (MM_PER_IN 25.4). Zero, negative, or blank is a clean error and does not resize. A body with holes is resized from its bounding box so the holes stay. No src/ or bindings.cpp change. Smoke: window.__cadcamResize in deploy_smoke and phone_smoke.
