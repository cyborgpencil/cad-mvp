# Antigravity basic sketch (Arc + Polygon)

Team-chosen and authored by Doc Steward, 2026-10-25 (America/Denver). Aligns with Digest cover plan in CAD CAM MVP room (draw-only Arc + Polygon; solver/C7 and phone T2 out). App facts checked against main `9676455` (after #115). This file is the Antigravity feed. It does not change the app by itself.

**Hard lock (Erik via 3T, 2026-10-25 ~5:59 PM MT):** sketches **implementation** is **Antigravity-only on ErmoZ13**. Do **not** use Grok Build or Cursor for this work — not for the handoff into code, not for fixes, not as a fallback. Pilot owns the Antigravity run after this brief is on main. Same worktree style as the Select trial (`C:\Dev\cadcam-antigravity-select` pattern); keep `C:\Dev\cadcam-mvp` main clean.

Units: **mm**. Gate: OCCT validity + units (watertight dropped, 02:17 rule). Do not reopen P1–P5. Do not reopen phone T2 / gizmo / typed-resize. Standing: Erik tests features and reports issues before anyone works on fixes (no speculative fix slices).

Shipped on main and closed (keep; do not retune except where Arc/Polygon need an explicit branch so Confirm does not fall through to rect): face sketch and Blind extrude #70 (`7c83b2a`), origin-plane empty-doc #77 (`347888e`), Extrude New/Join/Cut #83 (`99063c9`), measure angle/area and sketch L×W/Ø callouts #98 (`56c2528`), click-click Line N≥3 #108 (`a5f4763`), BREP-only save/load #104 (`3b485f8`). Touch gestures #21/#22/#24 stay closed. Select polish #114 stays as shipped.

Sources: `research/gui/sketch-mvp-p5c.md`, `mvp/gui-plan.md` §4, `prompts/p5c-sketch-extrude.md`, `prompts/sketch-line-followup.md`, `prompts/measure-sketch-next.md`, `prompts/origin-plane-empty-doc.md`, `prompts/extrude-join-cut.md`, `web/PROGRESS.md` P5 rows, UPDATES #70/#77/#83/#98/#108/#114/#115.

## Context
- WASM UI in `web/` (mostly `web/index.html`, plus `web/occt-ops.mjs`). Worktree off main on Z13; Antigravity only.
- Create → Sketch is `data-action="newSketch"`. Finish Sketch is `#finishBar [data-action="finishSketch"]`. Face tap → `setSketchPlane`. Empty doc → `#originPlanes` Top `xy` / Front `xz` / Right `yz` → `setOriginSketchPlane`.
- Rectangle / Circle / Line / Extrude paths already ship (see `prompts/sketch-line-followup.md`). `confirmSketch` must branch on sheet mode; **every other mode must not silently become rect**.
- Arc is inert chrome today: `data-tool="Arc"`, catalog `{ name: 'Arc', tab: 'sketch' }`, no `action`. Polygon is the same kind of chrome (catalog / ribbon with no action). Trim, offset, sketch fillet, dimension, and constraint buttons stay inert.
- Prefer JS/HTML/CSS + existing libcascade bindings already used from `web/occt-ops.mjs`. **No** kernel, C++, `src/`, `web/bindings.cpp`, or `cadcam.wasm` rebuild. If a needed OCCT call is missing from the prebuilt JS bindings, **stop and report TBD** — do not add a binding and do not ship a stand-in face.
- Do not commit `.wasm`, `web/cadcam.wasm`, or `web/dist/`. Do not edit `UPDATES.md`. Do not add or edit a root `PROGRESS.md`. Leave `web/PROGRESS.md` for a separate scrub. Do not edit `research/`.
- Commit on a PR branch. Never push to main. Repo Keeper merges after tip-match + `ci.yml` green.

## Team-chosen behaviour

Keep the shipped sketch path. Add **Arc** and **Polygon** as closed-profile draw tools that feed the existing MakeFace → Blind extrude New/Join/Cut path. No PlaneGCS. No trim/offset/sketch-fillet/dimension-as-constraint this wave.

`mvp/gui-plan.md` §4 lists line, rectangle, circle, arc, polygon, fillet, trim, offset, and dimension. Line/rect/circle already ship. This brief is Arc + Polygon only. Solver stays out (C7 + prior T4).

### T1 — Keep shipped path and OCCT / mm
Keep Create → Sketch, face pick, origin-plane pick (empty doc only), rectangle, circle, line (click-click N≥3), Finish Sketch, Blind extrude New/Join/Cut (default 10 mm), sketch L×W/Ø callouts, Measure angle/area/distance/volume.

After a successful extrude commit, the gate stays `inspectSolid`: OCCT validity and `units === 'mm'`. Watertight stays dropped.

`portrait_sketch_problems` and `portrait_origin_plane_problems` (including the line case at the end of `ORIGIN_PLANE_EXPR`) stay green. Do not retune those asserts except to append new Arc/Polygon cases at the **end** of the origin-plane expression (same pattern as Line).

### T2 — Arc tool (3-point arc closed by chord)
Wire the existing Arc control the way Line / Rectangle / Circle are wired.

- Ribbon: `data-tool="Arc"` gets `data-action="sketchArc"`.
- `TOOL_CATALOG` Arc row gets `action: 'sketchArc'`. Phone `sheetBtn('Arc')` clicks that catalog row.
- `sketchArc` sets `state.activeTool` to `Arc`, Sketch tab, `openSketchSheet('arc')` with `state.sketchSheetMode === 'arc'`.
- That mode hides `#sketchRectRow`, `#sketchCircRow`, `#sketchDepthRow`, and any line-only UI. No typed length/radius fields. `#sketchNote` says Arc once a plane is set, else `sketchPlanePrompt()`.
- `#sketchConfirm` (`confirmSketch`) calls a new `commitSketchArc` when mode is `arc` — never `commitSketchRect`.
- `setSketchPlane` / `setOriginSketchPlane` reopen the sheet for `arc` the same way they do for `rect` / `circle` / `line`.

**Clicks:** three plane clicks, in order: start, through (on-arc), end. Same ray→plane hit path as Line (`pointerNdc`, `raycaster.ray.intersectPlane`, `cadToThree` / `threeDeltaToCad` swap, `frame.uvOf`). Plane must already be set; a tap does not both set the plane and place a point. Drag still orbits. Do not change `tapSlopPx`, view-cube swipe, or three-finger undo.

`window.__cadcamSketch` gains `placeArcPoint(uMm, vMm)` (same object as `placeLineVertex`). Appends while Arc is active and a plane is set; returns false otherwise. After each append, refresh Confirm: disabled until 3 points. `state()` gains `arcPoints` (in-progress count; after successful Confirm, 3 until the profile is cleared).

**On Confirm with 3 points:** build one closed wire = circular arc (start→through→end) + straight chord (end→start), then `BRepBuilderAPI_MakeFace(wire, true)` / `ownedFace`, then `storeSketchProfile` with `kind: 'arc'`, `closed: true`. `lengthMm` / `widthMm` / `diameterMm` stay 0. Then `closeSketchSheet()` like rect/circle/line.

Use an OCCT path already exposed on the libcascade object (typical pattern: arc-of-circle edge + line edge → `MakeWire` → face). If the needed constructor is missing from the prebuilt bindings, **stop and report TBD**. Do not edit `src/` / bindings / wasm. A failed face build does not set `closed`, keeps the points, and uses the existing toast/hint failure path.

No typed-radius-only path. No open arc left as the profile (extrude needs a face).

Extrude stays the existing sheet (Blind 10 mm, New/Join/Cut via `commitSketchExtrude`).

### T3 — Polygon tool (regular N-gon)
Wire Polygon the same way.

- Ribbon / catalog: give Polygon `data-action="sketchPolygon"` and catalog `action: 'sketchPolygon'` (match whatever label already appears in the sketch chrome — do not invent a second Polygon control).
- `sketchPolygon` → `openSketchSheet('polygon')`, `state.sketchSheetMode === 'polygon'`.
- Sheet shows typed **sides** N (integer, default **6**, minimum **3**) and **diameter** mm (default **10**), same mm/`inputmode=decimal` pattern as `#sketchD`. Hide rect/circle/line/arc click UI and depth row.
- `#sketchConfirm` → `commitSketchPolygon` (not rect).
- Place the regular N-gon **centered on the sketch-plane origin** (same placement family as center circle), in plane millimetres. Vertices at diameter/2. Build a closed wire (`MakePolygon` 3/4-point constructors already used in-repo; for N≠3,4 use `Add`/`Close` if exported — else **TBD stop**). Then MakeFace / `storeSketchProfile` with `kind: 'polygon'`, `closed: true`, `diameterMm` set, sides recorded for tests (expose `state().polygonSides` or equivalent on `window.__cadcamSketch.state()`).

`setSketchPlane` / `setOriginSketchPlane` reopen the polygon sheet when that mode is active.

### T4 — No solver; leave advanced chrome inert
No PlaneGCS, no constraint solver, no driving dimensions, no trim, no offset, no sketch fillet, no spline, no revolve. Constraint / trim / offset / dimension / fillet-in-sketch buttons stay inert (no new `data-action`). Arc and Polygon do not write `#calloutLayer` (rect L×W and circle Ø callouts stay on their sheets). `commitCalloutEntry` stays on `editingBasicShape()`.

### T5 — Phone
Any new Confirm and any new tappable Arc/Polygon control is at least **44 CSS px**. Do not cover `.phone-tabbar`, `#vcHome`, `#exportBtn`, or `#statusUnits`. Portrait checks stay 390×844.

### T6 — Out
- View-cube swipe / gestures #21/#22/#24. Measure retune. Save/load retune. Feature-history rebuild.
- WASM / kernel / C++ / `src/` / `web/bindings.cpp`.
- Reopening P1–P5. Phone T2 / move-gizmo / typed-resize. Hit-zone widen.
- Speculative polish of shipped Line/Rect/Circle/Extrude (Erik tests → reports before fixes).
- Trim, offset, sketch fillet, dimensions-as-constraints, PlaneGCS (C7).
- Typed-length line redo. A second `window.__cadcam*` hook. A new smoke file / harness.
- `UPDATES.md`, `web/PROGRESS.md`, root `PROGRESS.md`, `research/`.

## Acceptance
- T1. Existing `portrait_sketch_problems` and `portrait_origin_plane_problems` (rect/circle/line blocks) still pass. Create→Sketch / Finish / face / origin chips unchanged. Gate on new solids: OCCT + mm.
- T2. Empty doc, Top/XY. Arc tool. `placeArcPoint(0,0)`, `(10,5)`, `(10,0)`. Confirm. Before Finish: `profile === 'arc'`, `closed === true`, `arcPoints === 3`. Finish → Extrude New, depth 10 → one solid, `occtGate === true`, `unitsPass === true`, volume within 0.5 mm³ of the analytic D-shape (half-disk when through-point is on the semicircle; if the three points are colinear, Confirm fails cleanly and leaves `closed === false`). Missing arc binding → TBD stop, no stand-in.
- T3. Empty doc, Top/XY. Polygon tool. N=6, diameter 10. Confirm → `profile === 'polygon'`, `closed === true`. Extrude Blind 10 New → one solid; volume within 0.5 mm³ of regular-hexagon area × 10 mm; `occtGate` / mm pass. N=2 or blank diameter → Confirm disabled or clean error, no solid.
- T4. `sheetBtn` on trim/offset/constraint (if present) still opens nothing new. No solver `data-action`.
- T5. At 390×844, Arc and Polygon sheet buttons and `#sketchConfirm` on those sheets are each ≥44 CSS px; sheets do not cover the bottom bar / Home / Export / units.
- T6. No wasm diff. No phone-T2 / gizmo edits. Line/rect/circle/extrude regressions green.

## Tests
Extend existing smoke only (`tests/deploy_smoke.py`). No new smoke file.

- Append Arc then Polygon solids at the **end** of `ORIGIN_PLANE_EXPR`, after the line case, each from `ensureEmpty` / `deleteAll` so earlier `profile === 'rect'` asserts stay valid.
- Reuse `startSketch`, `pickPlane('xy', ...)`, `sheetBtn`, `confirmSketch`, `extrude`, `assertSolid`. Hook points via `window.__cadcamSketch.placeArcPoint` (and polygon typed fields / confirm).
- Optional 44 px `need()` for `sheetBtn('Arc')` and Polygon next to Rectangle/Circle/Line in `SKETCH_PORTRAIT_EXPR`. Do not change face-join volume or callout asserts there.
- `tests/phone_smoke.py` already runs `deploy_smoke.run_portrait` — no phone-only sketch probe.
- Leave `SAVELOAD_EXPR`, measure, boolean, and Join/Cut blocks passing.

## Out of scope
- Reopening P1–P5; phone T2; gizmo/resize; hit-zone widen.
- Trim, offset, sketch fillet, constraints / PlaneGCS, typed-length line redo.
- Measure/save retune; gesture retune; kernel/wasm.
- Speculative fixes to shipped sketch tools before Erik reports an issue.
- `UPDATES.md` / PROGRESS / research edits in this PR.

## Done
`ci.yml` green on the PR (docs-only may skip native build; code diff runs the build). **This prompt PR** stays draft until Research Digest tip-matches (primary). Doc Steward is second if needed. Author does not self-APPROVE. Repo Keeper undrafts and plain-merges. After the prompt is on main, Pilot runs Antigravity-only on Z13 from this file (worktree off main). Report the PR link and tip SHA for the prompt; Pilot reports the impl PR separately.
