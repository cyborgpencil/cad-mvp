# P5c: Sketch, then Blind extrude

Team-chosen by 3T final, 2026-10-24 (America/Denver). P5a Measure is on main via #60 (`ec00e2f`). P5b live callouts are on main via #64 (`7bcb81d`). P5c is unblocked. Research on main via #45 (`57bd8c7`): `research/gui/sketch-mvp-p5c.md`. Feed this to Grok Build / Cursor. This file is the spec. It does not change the app.

Recorded in `web/PROGRESS.md` (P5 section, after #66). Status there: P5a on main via #60, P5b on main via #64, P5c sketch open (`research/gui/sketch-mvp-p5c.md`, Blind default 10 mm).

## Context
- WASM UI in `web/` (mostly `web/index.html`, plus related JS). Work in the Z13 repo (`C:\Dev\cadcam-mvp`).
- Units stay millimetres.
- After modeling ops, keep the OCCT shape-validity check and the millimetre units check. Watertight was dropped (02:17 rule).
- Sketch today is a shell. Create → Sketch (`data-action="newSketch"`) switches to the Sketch tab. Finish Sketch (`data-action="finishSketch"`) returns to Model. Rectangle (`data-tool="Rectangle"`), Circle (`data-tool="Circle"`), and Extrude (`data-tool="Extrude (Push/Pull)"`) are chrome. They do not build geometry.
- Do not commit `.wasm`, `web/cadcam.wasm`, or `web/dist/`. Do not edit `UPDATES.md`. Do not add or edit a root `PROGRESS.md`.
- Prefer JS, CSS, and HTML, plus the existing libcascade 3.1.0 JS bindings. Primitives already call `BRepPrimAPI_MakeBox` and `BRepPrimAPI_MakeCylinder` from `web/occt-primitives.mjs`. Extrude uses `BRepPrimAPI_MakePrism` on that same module. No kernel, C++, `src/`, `web/bindings.cpp`, or `cadcam.wasm` rebuild. If `BRepPrimAPI_MakePrism` is missing from libcascade 3.1.0, mark that TBD and stop.
- Commit on a PR branch. Never push to main. Repo Keeper merges after `ci.yml` is green.

## Team-chosen behaviour
Minimal rectangle or circle on a planar face, then a Blind extrude. No constraint solver. Sizes are millimetres. The default Blind depth is **10 mm** (3T final; overrides the interim 5 mm). A typed depth overrides that default.

### Enter Sketch
Enter from the existing Create → Sketch shell. A tap on a planar face sets the sketch plane. That pick is exclusive with vertex / edge / face highlight. The phone target is at least 44 CSS px.

### Profile tools
Tools in this slice: rectangle (corner or 2-point) and center circle. Typed size is L×W for the rectangle and Ø for the circle, in mm (`inputmode="decimal"`, mm suffix). Finish Sketch keeps the closed profile and returns to Model.

### Extrude
Blind / Distance only. The depth field opens at **10 mm**. A typed value in mm overrides it. The result is a new body. Kernel: closed face or wire through `BRepPrimAPI_MakePrism`. After commit, run the OCCT validity check and the mm units gate, the same standing rule as the primitives. No watertight re-check (02:17).

### Phone
Every new Sketch control and every new Extrude control is at least 44 CSS px. Do not cover the bottom bar.

Origin-plane fallback when no body exists is not locked. The acceptance path starts from the 20 mm cube, which already has a face.

## Acceptance
- Create → Sketch still opens the Sketch shell, and Finish Sketch still returns to Model.
- Tapping a planar face on the default 20 mm cube sets the sketch plane, exclusive with vertex / edge / face highlight. The phone target is at least 44 CSS px.
- A rectangle of 10×10 mm on that face, extruded Blind at the default depth of 10 mm, commits through `BRepPrimAPI_MakePrism` as a new body. OCCT validity passes and the mm gate passes.
- A center circle of Ø10 mm on that face, extruded Blind 10 mm, commits the same way as a new body. OCCT validity passes and the mm gate passes.
- Typed L×W and Ø are millimetres. A typed depth overrides the 10 mm default.
- Portrait 390×844: Sketch tools and Extrude Confirm are at least 44 CSS px and do not cover the bottom bar.
- Box, cylinder, and disc primitives are unchanged.

## Tests
Extend the smoke that already exists. Do not add a new smoke file or a new harness.

- `tests/deploy_smoke.py` and `tests/phone_smoke.py`: add a check only where one already fits. Phone smoke already uses the 390×844 viewport.
- On the default 20 mm cube face: rectangle 10×10 mm extruded to depth 10 mm, and circle Ø10 mm extruded to depth 10 mm. Assert a new body, OCCT validity, and the mm gate.
- Phone: new Sketch controls and Extrude Confirm are at least 44 CSS px at 390×844, and they do not cover the bottom bar.
- Regression: Create → Sketch still toggles Model ↔ Sketch. The primitives path is unchanged. Exclusive vertex / edge / face highlight (P1) still holds outside this face-to-plane pick.

## Out of scope
- Constraint solver, dimensions-as-constraints, construction geometry, and multi-profile booleans inside the sketch.
- Arcs, splines, and fillets drawn in the sketch.
- Revolve, sweep, and loft.
- Join and Cut. This slice creates a new body only.
- A watertight gate.
- Origin-plane fallback on an empty document (not locked).
- A kernel or WASM rebuild.

## Done
`ci.yml` green on the PR, then Repo Keeper merges. Report the PR link and the tip SHA.
