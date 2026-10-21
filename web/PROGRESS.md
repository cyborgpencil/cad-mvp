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
