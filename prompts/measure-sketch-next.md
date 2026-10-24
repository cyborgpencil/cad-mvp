# P6: Measure angle and area, then sketch callouts

Team-chosen by Doc Steward, 2026-10-24 (America/Denver). Locks T1–T6 are 3T final, 2026-10-24 ~10:23 AM MT (America/Denver). They come from `research/gui/measure-sketch-next.md` and are final. That note is on main via #94 (`b1afab7`). This prompt was written on main `ca60ba6` (#95 is the UPDATES line for #94). App facts in the note were checked at `e0d32e3`. Nothing under `web/` changed between that tip and `ca60ba6`. Feed this to Grok Build / Cursor. This file is the spec. It does not change the app.

Units: **mm**. Angle: **degrees**. Area: **mm²**. Gate: OCCT validity + units (watertight dropped, 02:17 rule). Measure stays read-only. Do not reopen P1–P5. Origin-plane (#77), Extrude Join/Cut (#83), and touch Booleans + fillet (#91, merge `73408c4`) stay closed.

## Context
- WASM UI in `web/` (mostly `web/index.html`, plus `web/occt-ops.mjs`). Work in the Z13 repo (`C:\Dev\cadcam-mvp`).
- Erik’s 2026-10-23 queue item #5 (measure/callouts, then sketching) is done. P5a Measure is on main via #60 (`ec00e2f`). P5b callouts are on main via #64 (`7bcb81d`). P5c sketch is on main via #70 (`7c83b2a`). This slice is only the delta those slices parked.
- Units stay millimetres. The existing inch display branch on `formatLength` / `formatArea` / `formatVolume` stays as it is. Angle is degrees. Do not add a radian unit or any other new secondary unit.
- After modeling ops, keep the OCCT shape-validity check and the millimetre units check. Watertight was dropped (02:17 rule). Measure does not change the solid, Export, or that gate. Do not bring the watertight check back.
- Measure on draws two-point distance or one-edge length, plus volume. `updateMeasure` writes `#measureSpanLabel` as `Length` or `Distance` via `formatLength`, and `#measureVolume` as `Volume` + `formatVolume(state.volumeMm3)`.
- One edge is a length only when `state.selection === 'edge'` and exactly one id is selected (`selectedEdgeLengthMm`). That length is `polylineLengthMm`: the polyline sum of `edge.pts`. The comment on `polylineLengthMm` stands: curved-edge accuracy is TBD. `BRepGProp::LinearProperties` is not used.
- Two-point distance is two `state.measurePicks`, or two selected vertices. Volume is `web/occt-ops.mjs` `solidVolumeMm3` → `BRepGProp.VolumeProperties` → `Mass()`, stored on `state.volumeMm3`.
- Primitive callouts are edit-scoped. `#calloutLayer`. `paintCallouts` uses `calloutSpecs()` only while `editingBasicShape()`: box L/W/H (`boxSx` / `boxSy` / `boxSz`), cylinder Ø/H (`cylD` / `cylH`), disc Ø/T (`discD` / `discT`). The value text is `formatLength`. `layer.hidden` when none show. `placeCallouts` keeps the layer off Home (`#vcHome`), Export (`#exportBtn`), and the units status (`#statusUnits`).
- Sketch profile fields exist. Sketch does not drive `#calloutLayer`. `#sketchSheet` opens through `openSketchSheet`. `state.sketchSheetMode === 'rect'` shows `#sketchL` and `#sketchW` (default 10). `state.sketchSheetMode === 'circle'` shows `#sketchD` (Ø, default 10). `calloutSpecs()` returns `[]` unless the active edit is box, cylinder, or disc. `closeSketchSheet` clears the mode and hides the sheet. Profile commit is still `#sketchConfirm` (`commitSketchRect` / `commitSketchCircle`). Extrude mode is `state.sketchSheetMode === 'extrude'`.
- `formatArea(mm2)` already returns rounded `mm²` when `state.unit === 'mm'` (`Math.round(mm2) + ' mm²'`). It is used for property kv rows with kind `area`. `updateMeasure` does not call it. There is no `formatAngle` in `web/index.html`.
- Phone rule already on the books: a tappable target is at least 44 CSS px (`research/mobile-touch-cad.md`; P5b). Display-only text has no hit-target rule.
- Do not commit `.wasm`, `web/cadcam.wasm`, or `web/dist/`. Do not edit `UPDATES.md`. Do not add or edit a root `PROGRESS.md`. Leave `web/PROGRESS.md` for a separate scrub.
- Prefer JS, CSS, and HTML, plus the existing libcascade 3.1.0 JS bindings already used from `web/occt-ops.mjs`. No kernel, C++, `src/`, `web/bindings.cpp`, or `cadcam.wasm` rebuild. Face area and the angle between two edges, or between one edge and one face, are not wrapped next to `solidVolumeMm3` today. If the existing libcascade JS bindings do not already expose the call this slice needs, stop and report. Do not add a second measure path. Do not add `BRepGProp::LinearProperties` in this slice.
- Commit on a PR branch. Never push to main. Repo Keeper merges after `ci.yml` is green.

## Team-chosen behaviour
Keep two-point distance, one-edge polyline length, and volume on the Measure toggle that already exists (`data-action="measure"`, `#measureSvg`, `updateMeasure`). Add angle and one-face area on that same readout. Add rect/circle sketch callouts on the P5b `#calloutLayer`. Measure stays read-only.

`#measureSpanLabel` stays `Length` or `Distance` for the T3 cases. An angle selection or a one-face area selection uses that same label line. Volume stays on `#measureVolume` whenever `updateMeasure` already shows it. Do not add a second readout.

### T1 — Measure angle
With Measure on, two edges, or one edge and one face, show the angle in **degrees** from `updateMeasure`. One edge and one face is this angle, not the face area in T2.

There is no `formatAngle` today. A degree label in JS on `#measureSpanLabel` is this readout. Do not add a radian unit. Do not add a new angle convention on top of whatever the existing binding returns. If the existing libcascade JS bindings do not already expose that angle, stop and report. Do not hard-code a degree value. Do not add a second measure path, and do not rebuild the kernel or WASM to add one.

Collect the two entities on the Measure-on path. Exclusive vertex / edge / face highlight (P1) still holds when Measure is off. Turning Measure off still clears the picks and hides the layer.

Measure does not change the solid, Export, or the OCCT validity gate.

### T2 — Measure area
With Measure on and exactly one face selected, show that face’s area in **mm²**. Reuse `formatArea` when `state.unit === 'mm'`. Measure does not call `formatArea` today. Put the text on `#measureSpanLabel`. Leave `#measureVolume` on the T3 path.

Exactly one face means this area. Two edges, or one edge and one face, stay T1. The existing inch branch inside `formatArea` stays (`in²` when `state.unit` is not `mm`). Do not add a new secondary unit.

If the existing libcascade JS bindings do not already expose that face’s area, stop and report. Do not hard-code an area. Do not add a second measure path, and do not rebuild the kernel or WASM to add one.

### T3 — Keep
Two-point distance, one-edge polyline length, and volume stay as they are (`updateMeasure`, `polylineLengthMm`, `state.volumeMm3` / `solidVolumeMm3`).

Exactly one selected edge still shows `Length` via `formatLength` of `polylineLengthMm`. Curved-edge length stays that polyline sum. `BRepGProp::LinearProperties` stays **TBD later**. Do not add that binding in this slice.

Two `state.measurePicks`, or two selected vertices, still show `Distance` via `formatLength`. Volume still shows `Volume` + `formatVolume(state.volumeMm3)` when a solid with a shape is present. Do not invent a second volume formula.

The inch display branch `measure_tool_problems` already checks stays. Switching the existing unit control still goes through `formatLength` / `formatArea` / `formatVolume` only.

### T4 — Sketch callouts
While `state.sketchSheetMode` is `rect` or `circle`, show live callouts on `#calloutLayer` through `paintCallouts` / `calloutSpecs`.

- Rectangle: **L×W** from `#sketchL` and `#sketchW`.
- Circle: **Ø** from `#sketchD`.

Value text uses `formatLength`, the same helper the primitive rows use. The numbers stay the sheet fields. A fresh sheet is 10 and 10, or Ø 10, because those inputs already default to 10. Changing a field updates the callout while that edit is open.

`paintCallouts` today takes specs only while `editingBasicShape()`, and `calloutSpecs()` returns `[]` for anything else. Extend that gate so the rect or circle sheet supplies these rows. Box L/W/H, cylinder Ø/H, and disc Ø/T stay on `editingBasicShape()` with the current dims (`boxSx` / `boxSy` / `boxSz`, `cylD` / `cylH`, `discD` / `discT`). Do not show sketch rows during a box, cylinder, or disc edit. Hide rows that have no spec. `layer.hidden` when none show.

Hide the sketch callouts when the rect or circle edit ends. That includes `closeSketchSheet` and the extrude sheet (`state.sketchSheetMode === 'extrude'`). Same edit-scoped rule as P5b.

This is not a Fusion driving-dimension solver. `#sketchConfirm` still owns the profile commit (`commitSketchRect` / `commitSketchCircle`). `commitCalloutEntry` and `openCalloutEntry` return unless `editingBasicShape()`, and that commit calls `onPrimitiveCommit`. Do not send sketch callouts through `onPrimitiveCommit` or the primitive `dimStep` path.

Display-only text meets T4. A visible sketch-row button is a tappable control: the only write it may do is the matching sheet field (`#sketchL`, `#sketchW`, or `#sketchD`).

### T5 — Phone
Any new callout or control that can be tapped is at least **44 CSS px**. Display-only text has no hit-target rule. Do not cover Home (`#vcHome`), Export (`#exportBtn`), or the units status (`#statusUnits`). Keep using `placeCallouts` for `#calloutLayer`.

The existing portrait checks are 390×844.

### T6 — Out
- No new sketch geometry: no line, arc, or spline, and no constraint solver.
- No persistent saved dimensions, no multi-body compare, no XYZ delta, and no new secondary units.
- Save/load stays queued (`research/project-save-load.md`). View-cube swipe stays queued (`research/touch-gestures.md`).
- No Join/Cut retune, no origin-plane retune, no touch Booleans or fillet retune, no watertight gate, and no kernel or WASM rebuild.

## Acceptance
- T1. Measure on, on the default 20 mm cube: two edges show a finite angle in degrees on `#measureSpanLabel`. One edge and one face shows a finite angle in degrees on that same label, not an area. The label is not a `formatLength` millimetre string. Measure off clears the picks and hides the layer. Body count, Export, and volume stay unchanged. A missing binding stops the slice instead of shipping a stand-in number.
- T2. Measure on, exactly one face of that cube selected: `#measureSpanLabel` is `formatArea` of that face while `state.unit === 'mm'`. The face is 20 mm × 20 mm, so the readout is `400 mm²`. It is not also a length or a distance. `#measureVolume` still shows the volume. A missing binding stops the slice instead of hard-coding `400 mm²`.
- T3. `measure_tool_problems` still passes on that cube: one edge polyline ~20 mm with at least three `edge.pts`, label `Length` plus `formatLength`; opposite-corner distance ~sqrt(3) × 20, including the two-tap pick path; volume ~8000 mm³ as `Volume` plus `formatVolume`; the existing inch length and volume lines still pass; Export stays allowed; one body remains. No `BRepGProp::LinearProperties` binding is added. `polylineLengthMm` is still the edge length.
- T4. While the rectangle sketch sheet is open, `#calloutLayer` shows L and W as `formatLength` of `#sketchL` and `#sketchW` (default `10 mm` and `10 mm`) and hides the unused row. While the circle sketch sheet is open, it shows Ø as `formatLength` of `#sketchD` (default `10 mm`). Editing the field updates the callout. `closeSketchSheet`, Finish Sketch, and the extrude sheet hide it. Box, cylinder, and disc callouts still match the portrait checks. Sketch callouts do not call `onPrimitiveCommit`, `commitSketchRect`, `commitSketchCircle`, or `commitSketchExtrude`.
- T5. At 390×844, any new tappable callout or control is at least 44 CSS px. Display-only sketch text has no hit-target check. The callout layer does not cover `#vcHome`, `#exportBtn`, or `#statusUnits`. The Measure control stays at least 44 CSS px.
- T6. No new sketch tool, no saved dimension, no multi-body compare, no XYZ delta, and no new unit. Save/load and view-cube swipe are untouched. Extrude New / Join / Cut, origin-plane, and Modify Union / Cut / Intersect plus fillet/chamfer behave as on main. The accept gate is still OCCT validity + mm. Watertight stays dropped. No `.wasm` change.

## Tests
Extend the smoke that already exists. Do not add a new smoke file or a new harness.

- `tests/deploy_smoke.py` `measure_tool_problems` already loads the default 20 mm cube through `window.__cadcamMeasure.probe`: one edge polyline ~20 mm, opposite-corner distance ~sqrt(3) × 20, volume ~8000 mm³, Measure control at least 44 px, inch display, Export unchanged. Extend that probe for T1 and T2 where it already fits. Keep the T3 asserts.
- `tests/deploy_smoke.py` `callout_problems` and `callout_hidden_problems` already check box, cylinder, and disc callouts. Leave those passing.
- `tests/deploy_smoke.py` `portrait_sketch_problems` already opens the sketch sheet on the default cube at 390×844 (Finish Sketch, Rectangle, Circle, L×W / Ø / Blind, 44 px targets, sheet clearance). Extend that function for the T4 callouts and the T5 hit targets where it already fits.
- `tests/phone_smoke.py` reuses those portrait checks at 390×844. It has no separate Measure probe. Do not add one. A phone check belongs on the portrait path that already runs.
- `hook.measures()` in the save/load portion of `tests/deploy_smoke.py` is the project measure, not this Measure tool. Do not retarget it. The 20 mm box at 8000 mm³ on that hook stays.

## Out of scope
- P1–P5 retune. Exclusive vertex / edge / face highlight stays when Measure is off. Origin-plane empty-doc. Extrude Join/Cut retune, including `commitSketchExtrude` and the New / Join / Cut chips.
- Touch Booleans and fillet/chamfer retune.
- Angle between anything other than two edges, or one edge and one face. Area of anything other than exactly one face. Radian. XYZ delta. Multi-body compare. Persistent saved dimensions. A new secondary unit.
- New sketch geometry: line, arc, spline, constraint solver, dimensions-as-constraints.
- `BRepGProp::LinearProperties`. A second length, area, volume, or angle path. A kernel, C++, `src/`, `web/bindings.cpp`, or WASM rebuild.
- A watertight gate.
- Save/load (`research/project-save-load.md`). View-cube swipe (`research/touch-gestures.md`).

## Done
`ci.yml` green on the PR (a docs-only diff may skip the native build; a code diff runs the build). This prompt PR stays draft until Research Digest tip-matches (primary). Doc Steward is second if needed. The author does not self-APPROVE. Repo Keeper undrafts and plain-merges. Report the PR link and the tip SHA.
