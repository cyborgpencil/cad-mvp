# Sketch line follow-up (post-P6)

Team-chosen and authored by Doc Steward, 2026-10-24 (America/Denver). Locks T1–T6 are 3T final, 2026-10-24 ~1:50 PM MT (America/Denver). They come from Digest’s sketching-follow-up plan against main `3b485f8` and are final. App facts were checked at `3b485f8` (BREP-only save/load, merge of #104). `9934436` (#105) adds only the `UPDATES.md` line for #104. Nothing under `web/` or `tests/` changed between those tips. Feed this to Grok Build / Cursor. This file is the spec. It does not change the app.

Units: **mm**. Gate: OCCT validity + units (watertight dropped, 02:17 rule). Do not reopen P1–P6. Shipped on main and closed: face sketch and Blind extrude #70 (`7c83b2a`), origin-plane empty-doc #77 (`347888e`), Extrude New/Join/Cut #83 (`99063c9`), measure angle/area and sketch L×W/Ø callouts #98 (`56c2528`), BREP-only save/load #104 (`3b485f8`). Touch gestures #21 (`50980eb`), #22 (`b61b881`), and #24 (`0e73596`) stay closed. Sources: `research/gui/sketch-mvp-p5c.md`, `research/gui/measure-sketch-next.md`, `research/gui/origin-plane-sketch.md`, `mvp/gui-plan.md` §4, `prompts/p5c-sketch-extrude.md`, `prompts/measure-sketch-next.md`, `prompts/origin-plane-empty-doc.md`, `prompts/extrude-join-cut.md`.

## Context
- WASM UI in `web/` (mostly `web/index.html`, plus `web/occt-ops.mjs`). Work in the Z13 repo (`C:\Dev\cadcam-mvp`).
- Create → Sketch is `data-action="newSketch"`. Finish Sketch is `#finishBar [data-action="finishSketch"]`. A planar-face tap calls `setSketchPlane` (`window.__cadcamSketch.tapFace` / `topFace`). Empty doc (`state.bodies.length === 0`) shows `#originPlanes` (`data-action="originPlane"`, Top `xy` / Front `xz` / Right `yz`) and `setOriginSketchPlane`. `sketchPlanePrompt()` is `Pick Top, Front, or Right` when there is no body, and `Tap a planar face` otherwise.
- Rectangle is `data-action="sketchRect"` → `openSketchSheet('rect')` → `#sketchL` / `#sketchW` → `#sketchConfirm` (`data-action="confirmSketch"`) → `commitSketchRect` → `opsApi.makeRectFace`. Circle is `data-action="sketchCircle"` → `#sketchD` → `commitSketchCircle` → `makeCircleFace`. Both call `storeSketchProfile` with `closed: true`. Extrude is `data-action="sketchExtrude"` → `openSketchSheet('extrude')` → `#sketchDepth` (default `SKETCH_BLIND_DEPTH_MM`, 10) → New / Join / Cut chips `data-action="sketchExtrudeMode"` → `commitSketchExtrude` → `makePrismSolid` / `BRepPrimAPI_MakePrism`. Join and Cut go through `installExtrudeOnBody`. `confirmSketch` sends `circle` to `commitSketchCircle`, `extrude` to `commitSketchExtrude`, and **every other mode to `commitSketchRect`**.
- The sketch plane frame (face from `faceFrameFromTriangles`, origin from `originPlaneFrame`) stores `origin`, `u`, `v`, `outward`, `point(uMm, vMm)`, and `uvOf(p)`, in millimetres. Viewer mapping is `cadToThree` (CAD x, y, z → THREE x, z, y) and `threeDeltaToCad` (THREE dx, dy, dz → CAD x, z, y). There is no `threeToCad` point helper.
- Line is inert chrome. The ribbon button is `data-tool="Line"` with no `data-action`. `TOOL_CATALOG` is `{ name: 'Line', tab: 'sketch' }` with no `action`. Arc is the same kind of chrome: `data-tool="Arc"`, catalog `{ name: 'Arc', tab: 'sketch' }`, no action. Polygon, sketch fillet, trim, offset, dimension, and the constraint buttons are chrome with no actions.
- `makeRectFace` builds a closed wire with `new oc.BRepBuilderAPI_MakePolygon(p1, p2, p3, p4, true)`, then `BRepBuilderAPI_MakeFace(wire, true)` through `ownedFace`. `web/occt-gate.mjs` calls the 3-point constructor `BRepBuilderAPI_MakePolygon(p1, p2, p3, true)` for a gate check, not for sketch. `makeCircleFace` uses `BRepBuilderAPI_MakeEdge` on a `gp_Circ` and `BRepBuilderAPI_MakeWire` on that one edge. No `web/` call uses a `MakePolygon` empty constructor, `Add(gp_Pnt)`, or `Close()`. No `web/` call uses `MakeEdge` on two points, or `MakeWire.Add`. A variable-length polyline (N other than 3 or 4) is not wrapped. If the existing libcascade JS bindings do not already expose that call, stop and report **TBD**. Do not add a binding. Do not hard-code a face.
- Sketch callouts are `#calloutLayer` / `paintCallouts` / `calloutSpecs` for rect L×W (`#sketchL`, `#sketchW`) and circle Ø (`#sketchD`) only. Measure angle and area stay on `updateMeasure`. Save/load stays BREP-only (`partFromBody` / `loadShapes`, null `primitive` for extrude). Do not retune those.
- Phone portrait checks are 390×844. `tests/deploy_smoke.py` `portrait_origin_plane_problems` runs `ORIGIN_PLANE_EXPR` (Top rect 10×10 Blind 10 mm → `assertSolid('rect', 1000)`, circle Ø10, then Join/Cut cases that still expect `profile === 'rect'`). `portrait_sketch_problems` runs `SKETCH_PORTRAIT_EXPR` (face join volume 9000 mm³, face New, 44 px targets). `tests/phone_smoke.py` calls `deploy_smoke.run_portrait`, which calls both. It does not have its own sketch expression.
- Viewport taps already go through `viewport` `pointerdown` / `onPointerDone`. A sketch-tab tap that `phoneApi.shouldSelect` accepts and that hits a face calls `pickSketchFace` → `setSketchPlane` and returns. `beginGizmoDrag` already builds a `THREE.Plane` and calls `pointerNdc` then `raycaster.ray.intersectPlane`. Do not add a second raycaster.
- Do not commit `.wasm`, `web/cadcam.wasm`, or `web/dist/`. Do not edit `UPDATES.md`. Do not add or edit a root `PROGRESS.md`. Leave `web/PROGRESS.md` for a separate scrub. Do not edit `research/`.
- Prefer JS, HTML, and CSS, plus the existing libcascade bindings already used from `web/occt-ops.mjs`. No kernel, C++, `src/`, `web/bindings.cpp`, or `cadcam.wasm` rebuild.
- Commit on a PR branch. Never push to main. Repo Keeper merges after `ci.yml` is green.

## Team-chosen behaviour
Keep the shipped sketch path. Add a line / polyline tool: click-click vertices, Confirm closes when N≥3, then the existing MakeFace and Blind extrude path. No typed-length line. No arc. No solver.

`mvp/gui-plan.md` §4 lists line, arc, polygon, fillet, trim, offset, dimension, and a PlaneGCS solver. This slice is only the line tool below. P5c and P6 left line and arc out. P6 has shipped. This slice adds line only.

### T1 — Keep shipped path and OCCT / mm
Keep Create → Sketch, face pick (`setSketchPlane`), origin-plane pick (`setOriginSketchPlane`, only when `state.bodies.length === 0`), rectangle, circle, Finish Sketch, Blind extrude New / Join / Cut (default 10 mm, `#sketchDepth`, `SKETCH_BLIND_DEPTH_MM`), sketch L×W / Ø callouts, and Measure angle / area.

After a successful extrude commit, the gate stays the one `commitSketchExtrude` already runs (`inspectSolid`: OCCT validity and `units === 'mm'`). Watertight stays dropped.

Do not retune those paths except where the line mode has to be an explicit branch so it does not fall through to `commitSketchRect`. `portrait_sketch_problems` (face join ~9000 mm³, face New, two bodies) and the existing rect / circle asserts in `portrait_origin_plane_problems` stay as they are.

### T2 — Line tool
Wire the existing Line control the way Rectangle and Circle are wired.

- Ribbon: `data-tool="Line"` gets `data-action="sketchLine"`.
- `TOOL_CATALOG` Line row gets `action: 'sketchLine'`. Phone `sheetBtn('Line')` clicks that catalog row (`pickCatalogItem` → `runAction`).
- `sketchLine` sets `state.activeTool` to `Line`, switches to the Sketch tab, and opens the sketch sheet in a new mode `state.sketchSheetMode === 'line'` (`openSketchSheet('line')`).
- That mode hides `#sketchRectRow`, `#sketchCircRow`, and `#sketchDepthRow`. It does not show `#sketchL`, `#sketchW`, or `#sketchD`. It does not add a length field. `#sketchNote` says Line once a plane is set, and `sketchPlanePrompt()` when it is not.
- `#sketchConfirm` is the same button (`data-action="confirmSketch"`). `confirmSketch` must call a new `commitSketchLine` when the mode is `line`. It must not call `commitSketchRect`.
- `setSketchPlane` and `setOriginSketchPlane` already reopen the sheet for `rect` and `circle`. Do the same for `line`.

A vertex is a click on the sketch plane, in millimetres. The plane must already be set (face tap or origin chip). The same tap does not both set the plane and drop a vertex. With no plane, a face tap still calls `setSketchPlane` and an empty doc still uses the origin chips.

Place the click on the existing viewport pointer-up path (`onPointerDone`, the branch that already requires `phoneApi.shouldSelect`). A drag still orbits. Do not change `tapSlopPx`, view-cube swipe, or three-finger undo.

When the line tool is active and `state.sketchPlane.frame` is set, intersect the existing ray with that plane: `pointerNdc`, then `raycaster.ray.intersectPlane`, same calls `beginGizmoDrag` uses. Build the `THREE.Plane` from `frame.origin` and `frame.outward` after `cadToThree`. Map the hit back with the same swap as `threeDeltaToCad` (CAD x = THREE x, CAD y = THREE z, CAD z = THREE y). Read plane millimetres with `frame.uvOf`. Do not invent a second axis map. If that hit cannot be mapped with this swap, stop and report.

Each accepted click appends one vertex. N is the number of clicks. Do not repeat the first point in N. Do not snap the vertex through `data-action="snap"`. Do not add a typed length.

`window.__cadcamSketch` is the existing hook (`topFace`, `tapFace`, `state`). Add `placeLineVertex(uMm, vMm)` on that same object. It appends `frame.point(uMm, vMm)` while the line tool is active and a plane is set, and returns false otherwise. The viewport click and this method call the same append. After each append, refresh `#sketchConfirm`: disabled until N≥3. `state()` gains `lineVertices` (the in-progress click count; after a successful line Confirm, the stored loop length, until that profile is cleared). Do not add a second `window.__cadcam*` hook. The portrait expressions place faces with `tapFace` and typed fields. They do not click the canvas for profile points, so the new solid check calls `placeLineVertex`.

### T2a — Click-click, close at N≥3
Confirm closes the wire only when **N≥3**. With fewer than 3 vertices, `#sketchConfirm` stays disabled (`disabled` and `aria-disabled`, the same gate `openSketchSheet` uses). Those clicks stay stored. Confirm does not build a face and does not set `closed`.

On Confirm with N≥3, close the wire and build one face with the existing MakeFace path (`BRepBuilderAPI_MakeFace(wire, true)` / `ownedFace`), then `storeSketchProfile` with `kind: 'line'`, `closed: true`, and the vertex loop. `lengthMm`, `widthMm`, and `diameterMm` stay 0. Then `closeSketchSheet()`, the same way `commitSketchRect` and `commitSketchCircle` do. Finish Sketch still returns to Model and keeps that closed profile.

Extrude is the existing sheet. Blind default 10 mm. New, Join, and Cut stay `commitSketchExtrude` / `makePrismSolid` / `installExtrudeOnBody`. An empty doc still opens Extrude on New. A face sketch still opens on Join. Do not add a second extrude path.

The 3-point `MakePolygon` constructor is already called in `web/occt-gate.mjs`. The 4-point constructor is already called in `makeRectFace`. Put the line face in a helper next to `makeRectFace` and `makeCircleFace` in `web/occt-ops.mjs`. A polyline whose count is not 3 or 4 needs `MakePolygon` `Add` / `Close`, or an equivalent already exported on the libcascade object. Those calls are not in `web/` today. If they are missing from the prebuilt JS bindings, stop and report **TBD**. Do not edit `src/`, `web/bindings.cpp`, or the wasm. Do not ship a stand-in face. A failed face build does not set `closed`, keeps the vertices, and uses the existing `setHint` / `toast` failure path.

No typed-length-only path. No length-typed segment as the way to create the line. Click-click vertices only.

### T3 — Arc out
Do not add arc. Leave the Arc button as it is: `data-tool="Arc"`, no `data-action`, catalog entry with no `action`. Clicking it does not open `#sketchSheet` and does not set a profile. No arc sheet, no arc commit, no arc geometry.

### T4 — No solver
No PlaneGCS, no constraint solver, no driving dimensions, no trim, no offset, no spline, no revolve. No dimensions-as-constraints. The constraint, trim, offset, dimension, and polygon buttons stay inert chrome. Line does not write `#calloutLayer`. Rect L×W and circle Ø callouts stay on their own sheets. `commitCalloutEntry` stays on `editingBasicShape()`.

### T5 — Phone
Any new Confirm and any new tappable line-tool control is at least **44 CSS px**. `#sketchConfirm` is the Confirm. The Line control that `sheetBtn('Line')` clicks is a tappable control. Display-only note text has no hit-target rule.

Do not cover the bottom bar (`.phone-tabbar`), Home (`#vcHome`), Export (`#exportBtn`), or the units status (`#statusUnits`). The portrait checks are 390×844, the same viewport `portrait_origin_plane_problems` and `portrait_sketch_problems` already require.

### T6 — Out
- View-cube swipe and the other gesture work in #21, #22, and #24. Do not redo them.
- Measure retune. Save/load retune. Feature-history rebuild on load. BREP-only save/load stays as #104.
- WASM rebuild. A kernel, C++, `src/`, or `web/bindings.cpp` change.
- Reopening P1–P6. Origin-plane retune. Extrude Join/Cut retune. Touch Booleans and fillet retune.
- Typed-length-only line entry. Arc, spline, and a solver (T3, T4).

## Acceptance
- T1. `portrait_sketch_problems` still passes, including face Join ~9000 mm³ within 0.5 mm³ and face New with two bodies. `portrait_origin_plane_problems` still passes its rect `assertSolid('rect', 1000)` and its circle Ø10 solid, and the later cases still see `profile === 'rect'` until the line case at the end. Create → Sketch, Finish Sketch, face pick, and origin chips behave as on main. The accept gate on a new solid is still OCCT validity + mm. Watertight stays dropped.
- T2 / T2a. Empty doc, Top / XY (`outward` +Z). Line tool. `placeLineVertex(0, 0)`, then `(10, 0)`. `lineVertices === 2`, `closed === false`, `#sketchConfirm` disabled, body count unchanged. Third call `placeLineVertex(0, 10)`. Confirm (`#sketchConfirm`) closes. Before Finish Sketch, `state().profile === 'line'`, `closed === true`, and `lineVertices === 3`. Finish Sketch, Extrude opens on **New**, `#sketchDepth` 10, Confirm. One solid, `kind` extrude, volume **500 mm³** within 0.5 (right triangle area 50 mm² times Blind 10 mm), mesh bounds about 0..10 on x, y, and z (tolerance 0.05, the rect check in that expression). `occtGate === true`, `gateOcct === 'PASS'`, `unitsPass === true`. No `#sketchL` / `#sketchW` / `#sketchD` on the line sheet. A missing variable-N polygon binding stops the slice instead of shipping a stand-in face.
- T3. With `#sketchSheet` hidden, `sheetBtn('Arc')` leaves it hidden and leaves `profile` empty. Arc still has no `data-action` and no catalog `action`.
- T4. The line sheet does not show sketch callout rows (`sketchL`, `sketchW`, `sketchD`). No solver control gains a `data-action`. Rect and circle callouts in `portrait_sketch_problems` still pass.
- T5. At 390×844, `#sketchConfirm` on the line sheet and the Line sheet button are each at least 44 CSS px. The line sheet does not cover `.phone-tabbar`, `#vcHome`, `#exportBtn`, or `#statusUnits`.
- T6. No typed-length line field. No arc geometry. No wasm diff. Measure, save/load, view-cube swipe, and Modify Union / Cut / Intersect plus fillet behave as on main. Extrude New / Join / Cut for rect and circle behave as on main.

## Tests
Extend the smoke that already exists. Do not add a new smoke file or a new harness. Do not retarget unrelated hooks.

- Add the T2 / T2a solid at the **end** of `ORIGIN_PLANE_EXPR` in `tests/deploy_smoke.py`, after the contain-cut block. Start from an empty doc (`deleteAll` / `ensureEmpty`) so the earlier `profile === 'rect'` asserts are unchanged. Reuse `startSketch`, `pickPlane('xy', ...)`, `sheetBtn`, `confirmSketch`, `extrude`, and `assertSolid`. `extrude` already finishes the sketch, sets `#sketchDepth` to 10, requires the New chip, and clicks `#sketchConfirm`.
- In that same expression, the two-vertex check (Confirm disabled, `lineVertices === 2`, not closed) runs before the third vertex. `placeLineVertex` is on `window.__cadcamSketch`. Read `lineVertices`, `profile`, and `closed` from `state()`.
- `portrait_sketch_problems` / `SKETCH_PORTRAIT_EXPR` stays the face-path regression. Do not add a line solid there. A 44 px check for `sheetBtn('Line')` may sit next to the existing Rectangle and Circle `need()` calls in that expression. Do not change the face-join volume, the face-New body count, or the callout asserts.
- `tests/phone_smoke.py` already calls `deploy_smoke.run_portrait`, which runs both portrait functions at 390×844. Do not add a phone-only sketch probe.
- Leave `SAVELOAD_EXPR`, `measure_tool_problems`, `overlap_boolean_problems`, and the Join/Cut blocks inside `ORIGIN_PLANE_EXPR` passing. Do not retarget them.

## Out of scope
- Reopening P1–P6. Retuning face pick, origin-plane chips, rect, circle, sketch callouts, or Measure.
- Extrude Join/Cut retune, including a new Join or Cut line smoke. The line profile uses the existing `commitSketchExtrude` switch. One New solid is the new check.
- A typed length, a length field, or dimensions-as-constraints. Arc, spline, polygon, trim, offset, fillet-in-sketch, revolve, and PlaneGCS.
- A rubber-band preview mesh. The committed result is the face on `state.sketchProfile`, then the existing extrude.
- A second `window.__cadcam*` hook. A new smoke file. A new harness.
- View-cube swipe and gesture retune (#21, #22, #24). Feature rebuild on load. A change to `checkOcctShape` or the watertight gate.
- A kernel, C++, `src/`, `web/bindings.cpp`, or WASM rebuild. `.wasm` and `web/dist/`.
- `UPDATES.md`, `web/PROGRESS.md`, a root `PROGRESS.md`, and `research/`.

## Done
`ci.yml` green on the PR (a docs-only diff may skip the native build; a code diff runs the build). This prompt PR stays draft until Research Digest tip-matches (primary). Doc Steward is second if needed. The author does not self-APPROVE. Repo Keeper undrafts and plain-merges. Report the PR link and the tip SHA.
