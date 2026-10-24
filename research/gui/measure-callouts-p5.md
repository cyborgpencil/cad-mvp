# P5a/P5b — Measure + live callouts (implementation prep)

MVP Research Digest. **P5a Measure** then **P5b live callouts**, before sketch (**P5c**). Team lock (3T final, 2026-10-24 ~1:14 AM MT America/Denver). Units: **mm**. Invent nothing; TBD marks need Erik or the team.

Context: P2 UI-gap digest on `main` ([`ui-gap-p2.md`](ui-gap-p2.md)). P5c sketch→extrude note already on `main` ([`sketch-mvp-p5c.md`](sketch-mvp-p5c.md)). This note is the missing **implementation prep** for P5a/P5b so Doc Steward can write `prompts/p5-measure-callouts.md` and Pilot/Cursor can build.

## Current MVP (repo facts on `main` ~`3f8f687`)

| Fact | Where |
|---|---|
| Measure toggle exists (`data-action="measure"`, `#measureSvg`) | `web/index.html` |
| `updateMeasure()` draws a **fixed 20 mm** span between hard-coded world points `(-10,0,13)`–`(10,0,13)` and labels `formatLength(20)` | `web/index.html` (`updateMeasure`) |
| Status / Properties already show **Width / Depth / Height / Volume** in mm; volume via `opsApi.solidVolumeMm3` → `BRepGProp.VolumeProperties` → `Mass()` | `web/index.html`, `web/occt-ops.mjs` `solidVolumeMm3` |
| Edge selection exposes polyline ends (`selectedEdgeEnds`, topology `edge.pts`) | `web/index.html` |
| Prim edit sheet `#dimPanel` / `#primBox` / `#primCyl` / `#primDisc` holds typed L×W×H / Ø×H; `#hudSize` shows W×D×H on the HUD | `web/index.html` |
| Phone target **≥44 CSS px**; mm lock; OCCT validity + units on commit (watertight dropped, 02:17) | standing rules; [`../mobile-touch-cad.md`](../mobile-touch-cad.md) |

`web/PROGRESS.md` (P5 section): Measure first (two-point distance, selected-edge length, volume); callouts live L×W×H or diameter×height on the active primitive while editing; sketch after. The fixed 20 mm overlay is **not** this set.

## Typical CAD (sourced)

### Measure (P5a)

| Capability | Fusion | Onshape | FreeCAD | MVP slice |
|---|---|---|---|---|
| Two-object / two-point distance | Inspect → Measure: distance between two selections; edge Length on one edge [1][2] | Measure tool: min / max / center distance between entities; Length [4][5] | Std Measure (1.0+): Distance / Distance Free / Length [6][7] | **In:** two-point distance (vertex→vertex or pick→pick). **In:** selected-edge length. |
| Volume | Body Properties / API `BRepBody.volume` (cm³); not the Measure dialog [3][8] | Mass Properties: volume [5][9] | Std Measure volume mode on solids [6] | **In:** volume of active body (or sum of bodies) via existing `solidVolumeMm3`, shown in Measure UI in **mm³** (display may use existing `formatVolume`). |
| Angle / area / XYZ delta | Fusion Measure supports angle, area, XYZ Delta [1] | Area, angles, etc. [4] | Area, Angle, Position [6] | **Out** this slice (park; do not invent). |

OCCT (kernel, not product UX): volumes already use `BRepGProp::VolumeProperties`. Edge length for a `TopoDS_Edge` is typically `BRepGProp::LinearProperties` → `Mass()` (curve length), or a polyline sum of `edge.pts` when topology samples are already in JS. Prefer OCCT LinearProperties if a binding exists or is cheap to add; otherwise document polyline sum as interim and mark **TBD** if accuracy on curved edges matters. [10]

### Live callouts (P5b)

| Pattern | What official / product docs say | Sources |
|---|---|---|
| Canvas manipulators + typed values while creating/editing a Box | Fusion Box: drag Length/Width/Height handles **or** type exact values in the dialog; values update as you edit [11][12] | Fusion Create Box / Solid primitives |
| Property sheet alone is not enough | Team lock (P2 / PROGRESS): sizes must appear **on the model** while the primitive is being edited, Fusion-style | [`ui-gap-p2.md`](ui-gap-p2.md), `web/PROGRESS.md` P5 |
| MVP already has typed dims | `#dimPanel` + `#hudSize` | `web/index.html` |

**P5b MVP:** while a basic shape (box / cylinder / disc) is the active edit, show live **L×W×H** or **Ø×H** callouts in the viewport (reuse `#measureSvg` patterns or lightweight HTML overlays), bound to the same mm fields as `#dimPanel`. Hide when that edit ends (aligns with P4 “no always-on shelves” — callouts are edit-scoped, not chrome). Phone: callout hit targets ≥44 px if tappable; otherwise display-only with sheet still editable.

## Gap vs MVP today

| Area | Typical | MVP today | Gap |
|---|---|---|---|
| Measure distance | Two picks → shortest / point distance | Fixed 20 mm demo in `updateMeasure` | Wire picks to real mm distance; draw `#measureSvg` between them |
| Edge length | Select edge → Length | Selection + `edge.pts` exist; no Measure readout | One selected edge → length in mm on overlay + sheet |
| Volume | Body / mass properties | Status bar / Properties already compute `solidVolumeMm3` | Surface volume in Measure mode (reuse API); do not duplicate false numbers |
| Live callouts | Canvas dims while editing | `#dimPanel` + `#hudSize` only | Viewport callouts tied to live params |
| Units | Product units | **mm** lock | Keep mm; inch display-only if already present |

## Recommended MVP slice

### P5a — Measure (ship first)

1. **Mode:** existing Measure toggle shows `#measureSvg`; exiting clears picks and hides the layer.
2. **Two-point distance:** with Measure on, pick two vertices (or two snap points). Display distance with `formatLength` (mm). Draw dimension line + extensions using existing `setLine` / `setArrow` helpers (replace the hard-coded ±10 demo).
3. **Selected-edge length:** if selection mode is edge and exactly one edge is selected, show its length in mm. Prefer OCCT LinearProperties when available; else polyline sum of `edge.pts` and note curved-edge accuracy **TBD**.
4. **Volume:** with Measure on and a solid body present, show `solidVolumeMm3` via existing `formatVolume` (status bar may already show it — Measure should still expose it so the tool is complete per PROGRESS).
5. **Out of scope:** angle, area, XYZ delta, persistent saved dimensions, multi-body compare, secondary units.
6. **Gates:** display values are mm; no export change. After any future kernel edit from Measure: N/A (Measure is read-only).

### P5b — Live callouts (after P5a)

1. While editing box / cylinder / disc, show viewport callouts for the same params as `#dimPanel` (L×W×H or Ø×H).
2. Callouts update live as dim steppers / fields change; editing a callout (if tappable) writes the same state as the sheet.
3. Hidden when not editing that primitive (P4 alignment).
4. Phone: ≥44 CSS px if interactive; never cover Home / Export / units status.

### Then P5c

Do not start sketch→extrude code until P5a/P5b land. Follow [`sketch-mvp-p5c.md`](sketch-mvp-p5c.md) (Blind default **10 mm**, tap face = sketch plane, exclusive with V/E/F).

## Next steps (Grok Build / Cursor)

1. **Doc Steward:** write `prompts/p5-measure-callouts.md` from this note; fix `web/PROGRESS.md` P5 “Not implemented” → link this research; drop stale “#47 draft” wording if still present.
2. **Pilot / Cursor (P5a):** replace `updateMeasure` demo; two-point + edge length + volume; unit tests or console asserts on a 20 mm cube (edge 20 mm; space diagonal √3·20 if two opposite corners; volume 8000 mm³).
3. **Pilot / Cursor (P5b):** viewport callouts bound to prim params; hide when edit ends.
4. **Phone smoke:** Measure control ≥44 px; callouts readable at 390×844.
5. **Regression:** Properties / status volume unchanged; exclusive V/E/F (P1) still holds; P4 shelves stay non-always-on.

## Team decisions (locked)

1. Order: **P5a Measure → P5b callouts → P5c sketch** (3T final, 2026-10-24).
2. Measure set: two-point distance, selected-edge length, volume — all **mm**.
3. Callouts: live L×W×H or Ø×H on the active primitive while editing; property sheet is not the only place.
4. No inventing angle/area/XYZ this slice.

## Sources

1. Autodesk Fusion — Measure objects: https://help.autodesk.com/cloudhelp/ENU/Fusion-Model/files/SLD-MEASURE.htm  
2. Autodesk Fusion — Measure reference: https://help.autodesk.com/cloudhelp/ENU/Fusion-Model/files/GUID-D070A3CB-729F-410F-9DA4-D9DF7F4D55B5.htm  
3. Autodesk Fusion — BRepBody.volume (cm³): https://help.autodesk.com/cloudhelp/ENU/Fusion-360-API/files/BRepBody_volume.htm  
4. Onshape — Measure Tool: https://cad.onshape.com/help/Content/View/measure_tool.htm  
5. Onshape — Mass Properties Tool: https://cad.onshape.com/help/Content/View/mass_properties_tool.htm  
6. FreeCAD — Std Measure: https://wiki.freecad.org/Std_Measure  
7. FreeCAD — Part Measure Linear (obsolete → Std Measure): https://wiki.freecad.org/Part_Measure_Linear  
8. Autodesk — volume via body Properties / Boundary Fill note: https://www.autodesk.com/support/technical/article/caas/sfdcarticles/sfdcarticles/How-to-create-a-solid-body-with-a-boundary-fill-command-to-check-volume-in-Fusion-360.html  
9. Onshape Learn — Measure & Mass Properties (course overview): https://learn.onshape.com/courses/measure-and-mass-properties-d1ds  
10. Open CASCADE — `BRepGProp` VolumeProperties / LinearProperties (refman): https://dev.opencascade.org/doc/refman/html/class_b_rep_g_prop.html  
11. Autodesk Fusion — Create a primitive box (manipulators + typed values): https://help.autodesk.com/cloudhelp/ENU/Fusion-Patch/files/SFC-BOX.htm  
12. Autodesk Fusion — Solid primitives: https://help.autodesk.com/cloudhelp/ENU/Fusion-Model/files/SLD-CREATE-SOLID-PRIMITIVE.htm  
13. In-repo: `web/index.html` (`updateMeasure`, `formatLength`, `formatVolume`, `selectedEdgeEnds`, `#measureSvg`, `#dimPanel`, `#hudSize`); `web/occt-ops.mjs` (`solidVolumeMm3`); `web/PROGRESS.md` P5; [`ui-gap-p2.md`](ui-gap-p2.md); [`sketch-mvp-p5c.md`](sketch-mvp-p5c.md).
