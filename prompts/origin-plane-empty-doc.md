# Origin plane on an empty document

Team-chosen by 3T, 2026-10-24 (America/Denver). T1–T5 are locked. P5c is on main via #70 (`7c83b2a`). Research for this slice is on #74: `research/gui/origin-plane-sketch.md`. Also read `research/gui/sketch-mvp-p5c.md`, `prompts/p5c-sketch-extrude.md`, and `research/gui/post-p5c-next.md`. Feed this to Grok Build / Cursor. This file is the spec. It does not change the app.

## Context
- WASM UI in `web/` (mostly `web/index.html`, plus related JS). Work in the Z13 repo (`C:\Dev\cadcam-mvp`).
- Units stay millimetres.
- After modeling ops, keep the OCCT shape-validity check and the millimetre units check. Watertight was dropped (02:17 rule).
- P5c already runs from Create → Sketch (`data-action="newSketch"`). A tap on a planar face sets `state.sketchPlane`. Rectangle (corner, L×W mm) and center circle (Ø mm) build a closed profile. Finish Sketch (`data-action="finishSketch"`) returns to Model. Blind / Distance opens at **10 mm** (`SKETCH_BLIND_DEPTH_MM` in `web/occt-ops.mjs`). Commit goes through `makePrismSolid` / `BRepPrimAPI_MakePrism` and adds a new body. That path needs a face. An empty document has no face to tap.
- The default session still seeds a 20 mm cube. The origin picker is only for the no-body case (blank project or every body deleted).
- Do not commit `.wasm`, `web/cadcam.wasm`, or `web/dist/`. Do not edit `UPDATES.md`. Do not add or edit a root `PROGRESS.md`.
- Prefer JS, CSS, and HTML, plus the existing libcascade 3.1.0 JS bindings. No kernel, C++, `src/`, `web/bindings.cpp`, or `cadcam.wasm` rebuild. If a needed binding is missing, mark that TBD and stop.
- Commit on a PR branch. Never push to main. Repo Keeper merges after `ci.yml` is green.

## Team-chosen behaviour
When Create → Sketch runs and the document has no body, show an origin-plane picker. Picking a plane stores a world-origin sketch frame. Then reuse P5c. When any body exists, keep the P5c face tap.

### T1 — Planes
XY, XZ, and YZ. All three.

### T2 — UX path A
Explicit plane-picker chips. Each chip is at least 44 CSS px. The chips do not cover the bottom bar.

### T3 — Labels
Top, Front, and Right. Top is XY. Front is XZ. Right is YZ.

### T4 — Extrude normal
The extrude direction is the right-hand outward normal, the same sense as the face frame field `outward` that P5c already uses. On Top / XY that outward is +Z.

### T5 — Empty document
The empty-doc predicate is `state.bodies.length === 0`. Pilot may confirm that against `projectBlank` in the current code. Do not invent another predicate.

### Plane frame
Picking Top, Front, or Right sets `state.sketchPlane` to a frame at the world origin. No `faceId` is required. Use the same frame shape the face path already stores (`origin`, `u`, `v`, `outward`, and `point` in millimetres) so the rectangle, the circle, and Blind extrude keep calling the P5c code. On Top / XY, `outward` is +Z. Front / XZ and Right / YZ use that same right-hand `outward` rule.

### When a body exists
Create → Sketch on the default 20 mm cube still sets the plane from a planar-face tap. The origin picker stays off while `state.bodies.length` is not 0. Leave `setSketchPlane(faceId)` and the exclusive vertex / edge / face highlight as they are.

### After the plane is set
Reuse P5c. Corner rectangle (L×W mm) and center circle (Ø mm), typed with `inputmode="decimal"` and an mm suffix. Finish Sketch keeps the closed profile and returns to Model. Extrude is Blind / Distance only. The depth field opens at **10 mm** (`SKETCH_BLIND_DEPTH_MM`). A typed depth in mm overrides that default. The result is a new body. Kernel: `makePrismSolid` / `BRepPrimAPI_MakePrism`. After commit, run the OCCT validity check and the mm units gate. No watertight re-check (02:17).

### Phone
Every new plane chip is at least 44 CSS px. Do not cover the bottom bar. The portrait check is 390×844.

## Acceptance
- Empty doc (`state.bodies.length === 0`): Create → Sketch shows Top / Front / Right chips. Each chip is at least 44 CSS px and does not cover the bottom bar. Picking Top sets the XY plane with +Z outward.
- A rectangle of 10×10 mm on Top / XY, extruded Blind at the default depth of 10 mm, commits through `makePrismSolid` / `BRepPrimAPI_MakePrism` as a new body. OCCT validity passes and the mm gate passes.
- A center circle of Ø10 mm on Top / XY, extruded Blind 10 mm, commits the same way as a new body. OCCT validity passes and the mm gate passes.
- With a body present (the default 20 mm cube): the face-tap path is unchanged. The origin picker is not forced.
- Finish Sketch and Extrude reuse P5c. Join and Cut are out of scope.
- Portrait 390×844: the new chips are at least 44 CSS px and do not cover the bottom bar.

## Tests
Extend the smoke that already exists. Do not add a new smoke file or a new harness.

- `tests/deploy_smoke.py` and `tests/phone_smoke.py`: add a check only where one already fits. Phone smoke already uses the 390×844 viewport.
- Empty doc (`state.bodies.length === 0`): Create → Sketch shows Top / Front / Right. Picking Top sets XY with +Z outward. Rectangle 10×10 mm extruded Blind 10 mm, and circle Ø10 mm extruded Blind 10 mm. Assert a new body, OCCT validity, and the mm gate.
- Phone: the new chips are at least 44 CSS px at 390×844, and they do not cover the bottom bar.
- Regression: on the default 20 mm cube, a planar-face tap still sets the sketch plane, and the origin picker is not forced. Create → Sketch still toggles Model ↔ Sketch. Box, cylinder, and disc primitives are unchanged.

## Out of scope
- Join and Cut. This slice creates a new body only.
- A constraint solver.
- Offset and angled construction planes.
- Mate connectors, and a FreeCAD Body invent.
- A watertight gate.
- A kernel or WASM rebuild.
- Changing the face path when bodies exist.

## Done
`ci.yml` green on the PR (a docs-only diff may skip the native build). Tip-match reviews. Repo Keeper undrafts and plain-merges. Report the PR link and the tip SHA.
