# P5: Measure, then live callouts

Team-chosen by 3T final, 2026-10-24 ~1:14 AM MT (America/Denver). Erik parked measure + callouts, then sketching, on 2026-10-23. Research on main via #52 (`4cdf7c0`): `research/gui/measure-callouts-p5.md`. Feed this to Grok Build / Cursor after P4. Ship P5a, then P5b. This file is the spec. It does not change the app.

Recorded in `web/PROGRESS.md` (parked queue). Status there: spec ready / waiting Pilot after P4.

## Context
- WASM UI in `web/` (mostly `web/index.html`, plus related JS). Work in the Z13 repo (`C:\Dev\cadcam-mvp`). Volume already goes through `solidVolumeMm3` in `web/occt-ops.mjs` (`BRepGProp.VolumeProperties` → `Mass()`).
- Units stay millimetres. The inch control is display-only.
- Units checks and the OCCT shape-validity check after modeling ops stay. Watertight was dropped (02:17 rule). Validity does not block Export.
- Do not commit `.wasm`, `web/cadcam.wasm`, or `web/dist/`. Do not edit `UPDATES.md`. Do not add or edit a root `PROGRESS.md`.
- Prefer JS, CSS, and HTML for the Measure UI. No kernel, C++, `src/`, `web/bindings.cpp`, or WASM rebuild unless selected-edge length needs `BRepGProp::LinearProperties`. No LinearProperties binding is in the repo today. If that binding is required, mark it TBD and keep the polyline sum of `edge.pts` as the interim length.
- Commit on a PR branch. Never push to main. Repo Keeper merges after `ci.yml` is green.

## Team-chosen behaviour
Order stays P5a Measure, then P5b live callouts, then P5c sketch. Measure values are millimetres. The property sheet is not the only place sizes appear while a primitive is being edited.

### P5a — Measure (ship first)
The Measure toggle already exists (`data-action="measure"`, `#measureSvg`). Turning Measure on shows `#measureSvg`. Leaving Measure clears the picks and hides the layer.

Replace the hard-coded `updateMeasure` demo. On main it draws a fixed 20 mm span between world points `(-10, 0, 13)` and `(10, 0, 13)` and labels `formatLength(20)`. That demo is not this measure set.

- Two-point distance: with Measure on, two vertices or two picks. Display the distance with `formatLength` (mm). Draw the dimension with the existing `setLine` and `setArrow` helpers.
- Selected-edge length: when exactly one edge is selected, show its length in mm. Ship the polyline sum of `edge.pts` (samples already in JS; `selectedEdgeEnds` is the existing helper). Curved-edge accuracy is TBD. Add `BRepGProp::LinearProperties` only if this slice cannot ship without it; if you do, mark that TBD and keep the polyline sum as the interim result.
- Volume: with Measure on and a solid body present, show `solidVolumeMm3` through the existing `formatVolume` in the Measure UI (mm³). Status / Properties may already show that volume. Measure still exposes it. Do not invent a second volume formula.
- Gates: displayed values are mm. Measure is read-only. It does not change the model and it does not change Export.

### P5b — Live callouts (after P5a)
While a box, cylinder, or disc is the active edit, show viewport callouts for the same millimetre fields as `#dimPanel` (`#primBox`, `#primCyl`, `#primDisc`): L×W×H or Ø×H. Callouts update live as the dim steppers or fields change. Hide them when that edit ends. That matches P4: callouts are edit-scoped, not always-on chrome. Reuse `#measureSvg` patterns or a lightweight HTML overlay.

If a callout is tappable, it writes the same state as the sheet. If it is not tappable, it is display-only and the sheet stays editable.

Phone: a tappable callout is at least 44 CSS px. A display-only callout has no hit-target rule. Callouts never cover Home (`#vcHome`), Export (`#exportBtn`), or the units status (`#statusUnits`).

### Then P5c
Do not start sketch → extrude until P5a and P5b have landed. Follow `research/gui/sketch-mvp-p5c.md` (Blind default 10 mm, tap face = sketch plane, exclusive with V/E/F).

## Acceptance
- Measure on shows `#measureSvg`. Measure off clears picks and hides the layer.
- The hard-coded ±10 world-point demo and the fixed `formatLength(20)` label are gone.
- Two vertices or two picks show a mm distance from `formatLength`, drawn with `setLine` / `setArrow`.
- Exactly one selected edge shows a mm length from the polyline sum of `edge.pts`, unless a TBD LinearProperties binding is added and the PR says so.
- Measure shows volume from `solidVolumeMm3` via `formatVolume` (mm³) without a second formula.
- Display stays mm. Measure does not change Export.
- While editing a box, cylinder, or disc, viewport callouts show L×W×H or Ø×H bound to the same mm fields as `#dimPanel`, update live, and hide when the edit ends.
- A tappable callout is at least 44 CSS px and writes the same state as the sheet. A display-only callout leaves the sheet editable.
- Callouts do not cover Home, Export, or units.
- No sketch → extrude code in this slice.

## Tests
Extend the smoke that already exists. Do not add a new smoke file or a new harness.

- `tests/deploy_smoke.py` and `tests/phone_smoke.py`: add a check only where one already fits. Phone smoke already uses the 390×844 viewport.
- Suggest console asserts on the default 20 mm cube: one edge is 20 mm, and volume is 8000 mm³ (`solidVolumeMm3` / `formatVolume`). The research note also names the space diagonal of two opposite corners as sqrt(3) * 20 mm. Use that only as a two-point assert, not as a new suite.
- Phone: the Measure control is at least 44 CSS px. Callouts are readable at 390×844. A tappable callout is at least 44 CSS px.
- Regression: Properties / status volume stays on the existing `solidVolumeMm3` path. Save/load smoke already expects the 20 mm box at 8000 mm³ through `hook.measures()` in `tests/deploy_smoke.py`. That hook is the project measure, not this Measure tool. Do not retarget it. Exclusive vertex / edge / face highlight (P1) still holds. P4 shelves stay non-always-on.

## Out of scope
- Angle, area, XYZ delta, persistent saved dimensions, multi-body compare, and secondary units.
- P5c sketch → extrude (`research/gui/sketch-mvp-p5c.md`). Do not start it here.
- P3 shaders and P4 shelf show/hide, except that P5b callouts follow the P4 rule that edit chrome is not always on.
- A watertight gate. A kernel or WASM change other than the TBD LinearProperties note above.

## Done
`ci.yml` green on the PR, then Repo Keeper merges. Report the PR link, the tip SHA, and any team-chosen value that changed so it can be logged in `web/PROGRESS.md`.
