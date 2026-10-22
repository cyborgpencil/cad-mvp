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

