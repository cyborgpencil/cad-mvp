# P6 — Measure/callouts delta → sketch profile dims (prep)

MVP Research Digest. Next slice after P5a–c. Units: **mm**. Angle: **degrees**. Area: **mm²**. Gate: OCCT validity + units (watertight dropped, 02:17 rule). Invent nothing. Research only — no `web/`, prompts, UPDATES, PROGRESS, kernel, or WASM edits in this PR.

Erik’s 2026-10-23 queue item **#5** (measure/callouts, then sketching) is **done**. P5a Measure [#60](https://github.com/cyborgpencil/cad-mvp/pull/60) (`ec00e2f`), P5b callouts [#64](https://github.com/cyborgpencil/cad-mvp/pull/64) (`7bcb81d`), and P5c sketch [#70](https://github.com/cyborgpencil/cad-mvp/pull/70) (`7c83b2a`) are on `main`. This note is only the **delta** from items those slices parked. Do not reopen P1–P5. Also already on `main`, and not this slice: origin-plane [#77](https://github.com/cyborgpencil/cad-mvp/pull/77), Extrude Join/Cut [#83](https://github.com/cyborgpencil/cad-mvp/pull/83), touch Booleans + fillet [#91](https://github.com/cyborgpencil/cad-mvp/pull/91) (merge `73408c4`). UPDATES for #91 is [#92](https://github.com/cyborgpencil/cad-mvp/pull/92). Tip at write: `e0d32e3`.

3T asked for the next slice on 2026-10-24 ~10:22 AM MT (America/Denver): measuring tools + visual callouts, then sketching. **3T locked P6 on 2026-10-24 ~10:23 AM MT (America/Denver).** T1–T6 below are final. Save/load and view-cube swipe stay queued after this slice.

## 1. Parked items this delta comes from

These files describe the P5 prep, including what P5 left out. They are not a claim that P5 is still unbuilt.

| Parked item | Where it was written |
|---|---|
| Measure set that shipped was two-point distance, one-edge length, and volume. Angle, area, and XYZ delta were out. | [`measure-callouts-p5.md`](measure-callouts-p5.md) (P5a table: angle / area / XYZ delta **Out**); [`ui-gap-p2.md`](ui-gap-p2.md) (vertex XYZ / face area / angle “optional later”) |
| Out of the P5a/P5b spec: angle, area, XYZ delta, persistent saved dimensions, multi-body compare, secondary units. | [`prompts/p5-measure-callouts.md`](../../prompts/p5-measure-callouts.md) § Out of scope |
| Edge length: polyline sum of `edge.pts`. `BRepGProp::LinearProperties` was not in the repo; curved-edge accuracy stayed TBD. | [`measure-callouts-p5.md`](measure-callouts-p5.md); [`prompts/p5-measure-callouts.md`](../../prompts/p5-measure-callouts.md) |
| Sketch dimensions come after Measure. P5c is rect/circle on a face → Blind extrude, with no constraint solver and no dimensions-as-constraints. | [`ui-gap-p2.md`](ui-gap-p2.md) (callouts row: “Sketch dims after Measure”); [`sketch-mvp-p5c.md`](sketch-mvp-p5c.md) (out: constraint solver, dimensions-as-constraints, arcs, splines) |

## 2. Shipped MVP at tip `e0d32e3` (repo facts)

`web/PROGRESS.md` (P5 section) records P5a–c on `main` as above. Checked in `web/index.html` on this tip:

| Fact | Where |
|---|---|
| Measure on draws two-point distance or one-edge length, plus volume | `updateMeasure`: `#measureSpanLabel` is `Length` or `Distance` via `formatLength`; `#measureVolume` is `Volume` + `formatVolume(state.volumeMm3)` |
| Edge length is the polyline sum. LinearProperties is unused | Comment on `polylineLengthMm`: “Length is the polyline sum of edge.pts. Curved-edge accuracy is TBD. BRepGProp::LinearProperties is not used.” |
| Volume path is unchanged | `web/occt-ops.mjs` `solidVolumeMm3` → `BRepGProp.VolumeProperties` → `Mass()` |
| Primitive callouts are edit-scoped | `#calloutLayer`. `paintCallouts` uses `calloutSpecs()` only while `editingBasicShape()`: box L/W/H (`boxSx`/`boxSy`/`boxSz`), cylinder Ø/H (`cylD`/`cylH`), disc Ø/T (`discD`/`discT`). `layer.hidden` when none show |
| Sketch profile fields exist; sketch does not drive `#calloutLayer` | `#sketchSheet`: `#sketchL` / `#sketchW` (rect, default 10) and `#sketchD` (circle Ø, default 10). `calloutSpecs()` returns `[]` unless the active edit is box, cylinder, or disc |
| mm² helper already exists and is not the Measure readout | `formatArea(mm2)` returns rounded `mm²` when `state.unit === 'mm'`. It is used for property kv rows with kind `area`, not by `updateMeasure` |
| No degree formatter | Length, area, and volume formatters exist. There is no `formatAngle` in `web/index.html` |

Phone rule already on the books: tappable targets **≥44 CSS px** ([`../mobile-touch-cad.md`](../mobile-touch-cad.md); P5b prompt).

## 3. Typical CAD (sourced)

Fetched 2026-10-24. Claims below are only what those pages state.

| Product | What the page states | URL fetched |
|---|---|---|
| **Onshape Measure** | Measure type filter includes Min distance, Max distance, Length, Diameter, Radius, **Angle**, Face tangent angle, and **Surface area**. Center distance, min distance, and max distance are also listed, including X, Y, Z components. Angle unit choices are **Degree** or **Radian**. Length unit choices include Millimeter. Area is “Area of a surface.” iOS/Android copy includes minimum distance, total surface area, angles, and length. | https://cad.onshape.com/help/Content/View/measure_tool.htm |
| **Fusion Sketch Dimension** | In an active sketch: Create > Sketch Dimension. Single lines, parallel lines, or two points create **linear** dimensions. Non-parallel lines create **angular** dimensions. Circles create **diameter** dimensions. Arcs create **radius** dimensions. The dimension displays in the canvas. A value can be typed. Driving vs driven (Toggle Driven / Toggle Driving) is how Fusion constrains sketch geometry. | https://help.autodesk.com/cloudhelp/ENU/Fusion-Sketch/files/SKT-CREATE-DIMENSIONS.htm — same article title as https://help.autodesk.com/view/fusion360/ENU/?contextId=SKT-CREATE-DIMENSIONS . The `contextId` URL returned an empty body on fetch; the sentences above are from the cloudhelp file. |
| **FreeCAD Std Measure** | Tools → Measure (version 1.0). Modes include **Angle** (“angle between the selected entities”), **Area** (“area of the selected face”), Length, Distance, Distance Free, Position, Radius. Distance modes can **Show Delta** (three projected measurements). **Save** keeps the measurement in a Measurements group in the tree. | Wiki https://wiki.freecad.org/Std_Measure returned an Anubis interstitial, not the article. Body verified at https://raw.githubusercontent.com/FreeCAD/FreeCAD-documentation/main/wiki/Std_Measure.md |

Onshape’s Degree/Radian choice, FreeCAD’s saved measurements, and Fusion’s driving/driven sketch dimensions are product behavior. They are not extra MVP requirements. The locks in §5 say what this slice includes.

## 4. Gap vs MVP today (P5a–c shipped)

| Area | Typical (section 3) | MVP today (§2) | Gap this slice |
|---|---|---|---|
| Angle | Onshape Angle (degree or radian). FreeCAD Angle between selected entities | Measure labels distance, length, and volume only | **In (T1):** two edges, or one edge and one face, in **degrees** |
| Face area | Onshape Surface area. FreeCAD Area of the selected face | `formatArea` exists; Measure does not show a face area | **In (T2):** one selected face, **mm²** |
| Distance, edge length, volume | Onshape min/max/center and length. FreeCAD Distance and Length | Two-point distance, polyline edge length, `solidVolumeMm3` | **Keep (T3).** Curved edges stay polyline. LinearProperties stays TBD |
| Sketch dimensions on the profile | Fusion shows linear and diameter dimensions in the canvas while the sketch is active, and those dimensions can drive geometry | `#sketchL` / `#sketchW` / `#sketchD` are sheet fields. `#calloutLayer` does not run during sketch edit | **In (T4):** live L×W or Ø while the rect or circle sketch sheet is open, bound to those fields, P5b `#calloutLayer` pattern. Hide when the sketch edit ends |
| Persistent / driving dimensions | FreeCAD Save; Fusion driving dimensions (constraint) | None for Measure or sketch | **Out (T6)** |
| XYZ delta, multi-body compare, extra units | Onshape X/Y/Z distance components; FreeCAD Show Delta; Onshape radian angle unit | Not in Measure | **Out (T6)** |
| New sketch curves or a solver | Fusion also dimensions arcs; all three products have richer sketch tools | Rect + circle only (P5c) | **Out (T6)** |

## 5. P6 slice (3T final, 2026-10-24 ~10:23 AM MT)

### P6a — Measure

1. **Angle (T1).** With Measure on, two edges, or one edge and one face, show the angle in **degrees**.
2. **Area (T2).** With Measure on and exactly one face selected, show that face’s area in **mm²**. `formatArea` already prints mm² when `state.unit === 'mm'`. Measure does not call it today.
3. **Keep (T3).** Two-point distance, one-edge polyline length, and volume stay as they are (`updateMeasure`, `polylineLengthMm`, `state.volumeMm3` / `solidVolumeMm3`). Curved-edge length stays the polyline sum. `BRepGProp::LinearProperties` stays **TBD later**. Do not add that binding in this slice.
4. Measure stays read-only, same as P5a. It does not change the solid, Export, or the OCCT validity gate. The standing gate on later commits remains OCCT validity + units. Watertight stays dropped.

### P6b — Sketch callouts

1. **While editing a sketch rectangle or circle (T4),** show live **L×W** (rectangle: `#sketchL`, `#sketchW`) or **Ø** (circle: `#sketchD`) using the P5b `#calloutLayer` pattern (`paintCallouts` / `calloutSpecs` are the primitive path to extend). Values stay the sketch sheet fields.
2. **Hide when the sketch edit ends (T4).** Same edit-scoped rule as P5b primitive callouts.
3. This is not a Fusion driving-dimension solver. Confirm still owns the profile commit that already exists.

### Phone

**T5.** Any new callout or control that can be tapped is **≥44 CSS px**. Display-only text has no hit-target rule (P5b prompt). Do not cover Home, Export, or the units status (P5b).

### Out of this slice (T6)

- No new sketch geometry: no line, arc, or spline, and no constraint solver.
- No persistent saved dimensions, no multi-body compare, no XYZ delta, and no new secondary units. The existing inch display branch on `formatLength` / `formatArea` / `formatVolume` stays as it is.
- Save/load stays queued ([`../project-save-load.md`](../project-save-load.md)). View-cube swipe stays queued ([`../touch-gestures.md`](../touch-gestures.md)).
- Join/Cut retune, origin-plane retune, touch Booleans/fillet retune, a watertight gate, and a kernel or WASM rebuild are not this slice.

## 6. Team locks (3T final, 2026-10-24 ~10:23 AM MT America/Denver)

Numbering is 3T’s list. These are locks, not proposals.

| # | Lock |
|---|---|
| T1 | Measure angle — two edges or edge+face, degrees. |
| T2 | Measure area — one face, mm². |
| T3 | Keep — two-point / edge length / volume unchanged; curved-edge stays polyline (LinearProperties TBD later). |
| T4 | Sketch callouts — while editing rect/circle, live L×W / Ø on-sheet (P5b pattern); hide when sketch ends. |
| T5 | Phone — any tappable callout/control ≥44 px. |
| T6 | Out of this slice — no new sketch geometry (no line/arc/solver); no persistent dims, multi-body compare, XYZ delta, or secondary units. Save/load and view-cube swipe stay queued after. |

No open TBD inside T1–T6. The only leftover TBD named here is LinearProperties, and T3 puts it **later**, not in P6.

## 7. Next steps

1. **Doc Steward:** tip-match this research PR, then write the P6 prompt from T1–T6. Locks are already final. Do not edit `UPDATES.md` or `web/PROGRESS.md` in the research PR.
2. **Pilot / Grok Build:** implement after that prompt. P6a angle + one-face area on the existing Measure toggle; keep polyline length and volume. P6b sketch L×W / Ø on `#calloutLayer` bound to `#sketchL` / `#sketchW` / `#sketchD`, hidden when the sketch edit ends. Phone targets per T5.
3. **Repo Keeper:** plain-merge this research PR when review is in. Digest is the author and does not self-APPROVE.

## 8. Sources

Repo (this tip `e0d32e3` unless a merge SHA is named):

1. `research/gui/measure-callouts-p5.md` — P5a/P5b prep; angle, area, XYZ delta out; LinearProperties vs polyline.
2. `research/gui/sketch-mvp-p5c.md` — rect/circle, no constraint solver, no dimensions-as-constraints.
3. `research/gui/ui-gap-p2.md` — face area / angle optional later; sketch dims after Measure.
4. `prompts/p5-measure-callouts.md` — out of scope list; polyline interim; LinearProperties TBD.
5. `web/PROGRESS.md` — P5a #60 `ec00e2f`, P5b #64 `7bcb81d`, P5c #70 `7c83b2a`.
6. `web/index.html` — `updateMeasure`, `polylineLengthMm`, `#calloutLayer`, `calloutSpecs`, `paintCallouts`, `#sketchL`, `#sketchW`, `#sketchD`, `formatArea`.
7. `web/occt-ops.mjs` — `solidVolumeMm3` / `BRepGProp.VolumeProperties`.
8. `research/mobile-touch-cad.md` — ≥44 CSS px.
9. `research/project-save-load.md` — save/load queued after P6 (T6).
10. `research/touch-gestures.md` — view-cube swipe queued after P6 (T6).
11. Merges named above: #60, #64, #70, #77, #83, #91 (`73408c4`), #92, tip `e0d32e3`.

Official pages fetched for section 3:

12. Onshape Measure Tool: https://cad.onshape.com/help/Content/View/measure_tool.htm
13. Fusion Dimension sketch geometry: https://help.autodesk.com/cloudhelp/ENU/Fusion-Sketch/files/SKT-CREATE-DIMENSIONS.htm (contextId alias https://help.autodesk.com/view/fusion360/ENU/?contextId=SKT-CREATE-DIMENSIONS returned an empty body)
14. FreeCAD Std Measure (GitHub documentation source): https://raw.githubusercontent.com/FreeCAD/FreeCAD-documentation/main/wiki/Std_Measure.md (wiki page https://wiki.freecad.org/Std_Measure was blocked by an interstitial)

Team lock: 3T, CAD CAM MVP, 2026-10-24 ~10:23 AM MT (America/Denver). T1–T6 in section 6.
