# P5c — Minimal sketch → extrude follow-on (2026-10-24)

MVP Research Digest. Parked follow-on **P5c** (3T lock after Measure + live callouts): minimal **rect / circle on face → extrude**; **no full constraint solver**. Units: **mm**. Invent nothing; TBD marks need Erik or the team.

Context: P2 digest landed on `main` (PR #43 → tip ~`4fd4dbe`). This note opens the sketch slice that P2 parked until that merge. [`research/gui/ui-gap-p2.md`](ui-gap-p2.md)

## Current MVP (repo facts)

- **Sketch today:** Create → Sketch / New Sketch switches the Sketch tab shell; Finish Sketch returns to Model. No sourced claim that sketch geometry or constraints are implemented beyond that UI shell. [`research/gui/ui-gap-p2.md`](ui-gap-p2.md) (citing `web/index.html`)
- **Layout already treats Sketch as a mode:** prior layout review proposes Sketch as a contextual mode entered from Model and returning on finish (Fusion / FreeCAD pattern). [`research/gui/ui-layout-review.md`](ui-layout-review.md)
- **Phone / touch:** standing target size **≥44 CSS px** (WCAG AAA / Apple HIG); mm-locked numeric entry. [`research/mobile-touch-cad.md`](../mobile-touch-cad.md)
- **Solids today:** Box / Cylinder primitives map to OCCT `BRepPrimAPI_MakeBox` / `MakeCylinder` with Position/size in **mm** and an OCCT validity check after commit (watertight check dropped per 02:17 rule). [`research/gui/modo-selection-primitives.md`](modo-selection-primitives.md)

## Typical CAD: minimal sketch → extrude (sourced)

Shared pattern across Fusion, Onshape, and FreeCAD PartDesign — **not** a full sketcher clone:

| Step | What official docs say | Sources |
|---|---|---|
| 1. Enter sketch on a plane or **planar face** | Fusion: 2D sketch on construction / planar / origin planes. Onshape: Sketch → select plane **or part face**. FreeCAD PartDesign NewSketch: select a plane or a face on the active body. | Fusion sketches [1]; Onshape Sketch Basics [2]; FreeCAD PartDesign NewSketch [3] |
| 2. Draw a closed profile | Fusion: 2-Point / Center Rectangle; Center Diameter Circle. Onshape: Corner Rectangle (two clicks or drag); circle tools on Sketch toolbar. FreeCAD: Sketcher CreateRectangle / CreateCircle. | Fusion rectangles [4]; Onshape Corner Rectangle [5], Sketch Tools [6]; FreeCAD CreateRectangle [7], CreateCircle [8] |
| 3. Extrude / Pad to a solid | Fusion Extrude: select closed sketch profile(s), Distance extent, Operation New Body / Join / Cut / Intersect. Onshape Extrude: Solid + Blind depth (or Up to …); New / Add / Remove / Intersect. FreeCAD PartDesign Pad: extrude sketch/face by **Dimension** Length (or To last / To face / …). | Fusion Extrude solid [9]; Onshape Extrude [10]; FreeCAD PartDesign Pad [11] |
| 4. Constraints / full solver | All three products expose constraint systems (Onshape inferencing + manual constraints [2]; Fusion sketch constraints [1]; FreeCAD Sketcher). **Out of scope for this MVP slice** per team lock. | ui-gap-p2 team decisions [12] |

OCCT side (kernel, not CAD product UX): a linear sweep of a base shape is `BRepPrimAPI_MakePrism` (prism of base `S` and vector `V`). [13]

## Gap vs MVP today

| Area | Typical (sourced above) | MVP today | Gap |
|---|---|---|---|
| Sketch mode | Real geometry + dims on a face/plane | Create→Sketch **UI shell only** [12] | Need face/plane pick + profile tools |
| Profiles | Rect + circle (minimum usable set) | None | Add corner/2-point rect + center circle, mm dims |
| Extrude | Blind / Distance depth → solid | None from sketch (primitives only) | Closed profile → `MakePrism` (or equivalent) in mm |
| Constraints | Full solvers in Fusion/Onshape/FreeCAD | N/A | **Explicitly skipped** this slice [12] |
| Phone | 44 px targets; mm entry [14] | 44 px chips/sheets already used for Create/Modify [12] | Keep 44 px for Sketch tools + extrude Confirm |

## Recommended MVP slice (P5c)

Aligned with the 3T lock in P2 [12]. Prefer OSS / OCCT paths already used in-repo.

1. **Enter Sketch** from Create → Sketch (shell already exists); **tap a planar face sets the sketch plane** (exclusive with V/E/F highlight; phone ≥44 px) — locked 3T 2026-10-24.
2. **Tools only:** rectangle (corner or 2-point) + center circle. Typed L×W / Ø in **mm** (`inputmode=decimal`, mm suffix) [14]. No arcs, splines, fillets-in-sketch, or constraint icons.
3. **Finish Sketch** returns to Model with a closed profile retained (implementation owned by Grok Build / Cursor).
4. **Extrude:** Blind / Distance only; **default depth 10 mm** (typed override in mm); result = new body (Join/Cut later if cheap). Kernel: closed face/wire → `BRepPrimAPI_MakePrism` [13]. After commit: **OCCT validity + units (mm) gate** — same standing rule as primitives [15][14]; no watertight re-check (02:17).
5. **Phone:** all new Sketch / Extrude controls ≥ **44 CSS px**; do not cover the bottom bar [12][14].
6. **Out of scope this slice:** constraint solver, dimensions-as-constraints, construction geometry, multi-profile boolean in sketch, revolve/sweep/loft, imprint / disable-imprint (Onshape-only detail [2]).

## Next steps (Grok Build / Cursor)

1. Doc Steward: PROGRESS lock row for P5c + prompt once P5a/P5b Measure+callouts land (P2 order) [12].
2. Pilot / Cursor: tap-face → sketch plane; rect + circle tools; Finish Sketch; Extrude Blind default **10 mm** → `MakePrism`; unit tests on a 20 mm cube face (rect 10×10 mm × depth 10 mm; circle Ø10 mm).
3. Phone smoke: Sketch tools + Extrude Confirm ≥44 px; portrait 390×844.
4. Regression: existing Create→Sketch shell still toggles Model ↔ Sketch; primitives path unchanged.

## Team decisions (3T final, 2026-10-24 America/Denver)

1. **Default Blind extrude depth:** **10 mm** (3T final; overrides interim 5 mm). Typed override still allowed.
2. **Face-pick:** tap face sets the sketch plane (exclusive with V/E/F highlight); phone targets ≥44 px.

Measure + live callouts (P5a/P5b) still ship before sketch code.

## Still open (implementation detail)

- Origin-plane fallback when no body exists (not locked; only needed for empty-document first sketch).

## Sources

1. Fusion Help, Sketches in Fusion (2D on planar faces / origin planes): https://help.autodesk.com/view/fusion360/ENU/?guid=SKT-3D-SKETCH  
2. Onshape Help, Sketch Basics (plane or part face; Extrude from sketches): https://cad.onshape.com/help/Content/Sketch/sketch_basics.htm  
3. FreeCAD documentation, PartDesign NewSketch: https://github.com/FreeCAD/FreeCAD-documentation/blob/main/wiki/PartDesign_NewSketch.md (also https://wiki.freecad.org/PartDesign_NewSketch)  
4. Fusion Help, Create rectangles: https://help.autodesk.com/view/fusion360/ENU/?guid=SKT-CREATE-RECTANGLES  
5. Onshape Help, Corner Rectangle: https://cad.onshape.com/help/Content/Sketch/corner_rectangle.htm  
6. Onshape Help, Sketch Tools: https://cad.onshape.com/help/Content/Sketch/sketch_tools.htm  
7. FreeCAD documentation, Sketcher CreateRectangle: https://github.com/FreeCAD/FreeCAD-documentation/blob/main/wiki/Sketcher_CreateRectangle.md  
8. FreeCAD documentation, Sketcher CreateCircle: https://github.com/FreeCAD/FreeCAD-documentation/blob/main/wiki/Sketcher_CreateCircle.md  
9. Fusion Help, Extrude a solid body: https://help.autodesk.com/view/fusion360/ENU/?contextId=SLD-EXTRUDE-SOLID  
10. Onshape Help, Extrude: https://cad.onshape.com/help/Content/PartStudio/extrude.htm  
11. FreeCAD documentation, PartDesign Pad: https://github.com/FreeCAD/FreeCAD-documentation/blob/main/wiki/PartDesign_Pad.md  
12. Repo: `research/gui/ui-gap-p2.md` (P2 gap table + 3T decisions 2026-10-24: park sketch until P2; then rect/circle-on-face → extrude; no full constraint solver)  
13. OCCT 8.0.1 refman, `BRepPrimAPI_MakePrism`: https://dev.opencascade.org/doc/refman/html/class_b_rep_prim_a_p_i___make_prism.html (canonical: https://occt3d.com/dev/doc/refman/html/class_b_rep_prim_a_p_i___make_prism.html)  
14. Repo: `research/mobile-touch-cad.md` (WCAG/HIG 44 px; mm `inputmode=decimal`)  
15. Repo: `research/gui/modo-selection-primitives.md` (mm primitives; OCCT validity after commit)  
16. Repo: `research/gui/ui-layout-review.md` (Sketch as contextual mode)  
17. Team lock (3T / CAD CAM MVP room, 2026-10-24 America/Denver): after Measure+live callouts, minimal sketch = rect/circle-on-face → extrude; no full constraint solver; Blind default 10 mm; tap face = sketch plane exclusive with V/E/F (≥44 px). Recorded in [12] + Chief 2026-10-24.
