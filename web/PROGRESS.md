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
- Palette values are TBD placeholders in `:root`. Listed in `mockup/PROGRESS.md`. No Modo assets.
- CTest in `builds/solid-check`: 5/5 passed (`watertight`, `units`, `export`, `gate`, `create`).
- Screenshots were not taken. This session does not start an http server.

## Next: selection, primitives, MODO feel (Erik, 2026-10-21 3:44 PM MT)
- Reference video: https://youtu.be/HhuccQ20YVM. The GUI should feel similar, not match exactly, with clearly contrasting buttons when selected or active.
- A selection gizmo showing which faces, edges or vertices are selected.
- Primitives (box, cylinder, etc.) with editable parameters, which can then be modified.
- Keep the Export gate and the interim banner. Palette hex values stay TBD until Research Digest samples them.
- Phase 2 (libcascade OCCT gate) is in progress with Pilot.
- R3 is still provisional (code read only); a live R3 check is due at the next checkpoint.
- Correction (3:46 PM MT): phase 2 never launched after the 3:15 AM plan. Order of work per Chief: the OCCT gate session first, then the selection and primitives session following Research Digest's spec (research/gui/modo-selection-primitives.md, in progress).
- Live: the restyle build is deployed as 6a04ad5 at https://cyborgpencil.github.io/cad-mvp/ (banner on, Export locked). Each push to main now deploys through Actions.
- Chief ruling (3:48 PM MT): selection and hover colours are named CSS variables marked TBD. Don't hardcode orange (MODO docs) or teal (Erik) until Erik decides.

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

- Selection: Vertex (1), Edge (2), Face (3), Item (5). Digit 4 still opens Export. Alt+1..4 still switch tabs. Click replaces, Shift+click adds, Ctrl+click removes. Empty Vertex/Edge/Face means all, with no highlight. Item stays empty until it is selected.
- Hover uses `--hover-color`. Selection uses `--sel-color`. Active buttons use `--active-fill` and `--active-border`. Axis arrows use `--axis-x`, `--axis-y`, `--axis-z`. All of those hex values are TBD placeholders.
- Move gizmo only: X/Y/Z arrows, three planar handles, centre view-plane handle, Position XYZ in millimetres. No scale or rotate handles. Dragging a sub-element translates the whole solid and rebuilds once on pointer-up.
- Box: `BRepPrimAPI_MakeBox(gp_Pnt(cx-sx/2, cy-sy/2, cz-sz/2), sx, sy, sz)` after `Build()`. Cylinder: `BRepPrimAPI_MakeCylinder(gp_Ax2(base, dir), R, H)` after `Build()`, base = centre - dir*H/2. Signatures match libcascade 3.1.0. No partial angle. No Sides control.
- Each solid goes through `BRepCheck_Analyzer`, `ShapeAnalysis_FreeBounds`, the mesh watertight check, and the locked millimetre unit. Export stays off unless all three pass. The banner hides only when the OCCT gate is green.
- `?primitive=box&select=face` builds a box and selects one face. `window.__cadcamExportState` includes `selectionMode`, `selectionCount`, and `selectionAll`.

Node `tests/test_occt_gate.mjs`: ok. `closed_box` PASS. `open_box` FAIL, 4 free edges. Box gate and watertight PASS, 6 faces, 8 vertices, 12 edges, units mm. Cylinder Z and X PASS and watertight; Z has 3 faces, 2 vertices, 3 edges.

Headless Edge `tests/test_occt_page.ps1`: ok. `closed_box` green, Export on, banner hidden. `open_box` locked, banner stays. `?primitive=box&select=face` green, Export on, banner hidden, face mode, count 1. `?primitive=cylinder&select=item` green, Export on, banner hidden, item count 1. The script stops only Edge processes whose command line contains the test profile.

TBD placeholders, not decided values: hover/selection/axis/active hex, box 20×20×20 mm at centre (0, 0, 10), cylinder radius 10 mm and height 20 mm on Z at the same centre, pick tolerance 8 px, coplanar dot 0.999, tessellation deflection 0.5 mm and 0.5 rad, Sides/Segments, and the reference video frames. Mesh picking is the fallback when no OCCT solid is loaded.

## Deploy smoke test (2026-10-21)

`web/assemble_site.py` is the only Pages file list. `pages.yml` calls it before the upload step, then runs `tests/deploy_smoke.py`. The inline `cp web/*.mjs` already included `selection.mjs`, `viewport-selection.mjs`, and `occt-primitives.mjs`; those names are now required in the assembler so a dropped module fails before upload.

The smoke test copies that same tree into gitignored `builds/deploy-smoke/_site`, serves it, and loads it in headless Edge with CDP cache disabled. It fails on any same-origin non-2xx, console error, page exception, or unhandled rejection. Local run: `closed_box` OCCT PASS, Export on (10 responses, all 2xx). `open_box` OCCT FAIL, Export locked. `?primitive=box&select=face` occtReady, gate PASS, one face. CTest `deploy_smoke` passed in 12.91s. Omitting `selection.mjs` from the temp site failed on HTTP 404 and `console.error: selection failed`; the source file was not removed. CTest skips with code 77 only when the browser or libcascade is missing and `CI` is unset. A data-URI favicon was added so headless Chrome does not 404 `/favicon.ico`. No `src/` edits. No commit.

