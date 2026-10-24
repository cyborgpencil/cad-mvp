# P2 — UI gap analysis vs typical CAD (2026-10-24)

MVP Research Digest. Parked queue item **P2** (Erik via 3T, 2026-10-23 ~9:17 PM America/Denver): analyze the current UI, then name what is missing vs Fusion / similar. Related parked: **P1** selection clarity V/E/F, **P3** flatter Fusion-like shaders, **P4** show/hide every tool shelf, **P5** measure/callouts then sketching. Units: **mm**. Invent nothing; TBD marks need Erik or the team.

Repo snapshot: `main` tip `a688c71` (merge of #37). Facts below are from that tip’s `web/PROGRESS.md`, `web/index.html`, and `web/phone-select.mjs` unless a citation says otherwise.

## Current MVP UI (repo facts)

- **Pick filter chip + chooser:** Body / Face / Edge / Vertex; Multi toggle; chip min **44 px**; Edge touch radius **32 px** (face/body touch stay **20 px**). Fillet/Chamfer arm Edge and open a phone **edge sheet** (`#edgeSize` + Confirm, 44 px). Defaults fillet **2 mm**, chamfer **0.5 mm**. [`web/phone-select.mjs`](../../web/phone-select.mjs), [`web/PROGRESS.md`](../../web/PROGRESS.md)
- **Create menu:** Box, Cylinder, Disc, Hole, Sketch (sheet/popover). **Modify shelf** (toggled): Move, Rotate, Resize, Fillet, Chamfer, Union, Cut, Intersect, Delete. [`web/index.html`](../../web/index.html)
- **Viewport chrome:** view cube (`#viewCube`); display modes Shaded / **Shaded + Edges** (default) / Wireframe / X-Ray; Measure toggle; tool search; mm typed fields on primitives/holes; assemblies part list + PLA/PETG/TPU. Body mesh uses `THREE.MeshStandardMaterial` (`metalness: 0.1`, `roughness: 0.42`). [`web/index.html`](../../web/index.html)
- **Measure today:** toggling Measure shows `#measureSvg`, but `updateMeasure()` draws a **fixed** 20 mm callout between hardcoded world points `(-10,0,13)` and `(10,0,13)` — not selection-driven. [`web/index.html`](../../web/index.html)
- **Sketch today:** Create → Sketch / New Sketch switches the Sketch tab shell; Finish Sketch returns to Model. No sourced claim that sketch geometry or constraints are implemented beyond that UI shell. [`web/index.html`](../../web/index.html)
- **Parked table** still lists P1–P5 as *Parked / not started*. [`web/PROGRESS.md`](../../web/PROGRESS.md) (Parked queue)

## Gap table

| Area | Typical CAD (sourced) | MVP today | Gap / recommendation | Feeds |
|---|---|---|---|---|
| Selection clarity / filters | Fusion Selection Filters (Bodies, Body Edges/Faces/Vertices, …) [1]; FreeCAD Part SelectFilter (vertex/edge/face) [2]; Onshape selection + Select Other for overlaps [3][4]; prior in-repo modes V/E/F/Item [5] | Body/Face/Edge/Vertex chip + Multi; hover/sel CSS vars | **Decided (3T, 2026-10-24):** exclusive V/E/F highlight (click replaces; multi-filter later). Select-Other only if cheap (else PR follow-up). Box-select still open from prior digest [6]. | **P1** |
| Measure / inspect | Fusion Inspect → Measure: length/area/radius/distance/angle; filter Face/Edge/Vertex vs Body vs Component; canvas feedback [7][8]. Onshape Measure: dynamic on selection; min/max/center; length/radius/angle/area; mm units [9]. FreeCAD Std Measure: distance/length/position/area/radius (+ delta) with 3D labels [10] | Demo overlay only (fixed 20 mm); status/volume via BRepGProp elsewhere | **Decided (3T, 2026-10-24):** selection-based Measure first — two-point distance + selected-edge length + **volume**, all **mm**-locked; SVG callouts; phone ≥44 px. (Vertex XYZ / face area / angle still optional later.) | **P5** |
| Callouts while editing | Fusion/Onshape show live measure lines in the canvas [7][9]; FreeCAD saves measure labels in the 3D view [10] | Primitive dim sheet + hole Edge U/V fields; no general callouts on selection | **Decided (3T, 2026-10-24):** live **L×W×H / Ø×H** callouts on the active primitive while editing (Fusion-style), not property-sheet only. Sketch dims after Measure. | **P5** |
| Display / shaders | Fusion Visual Style includes shaded-with-visible-edges (common “readable solid” style) [11][12] | Shaded / Shaded+Edges / Wire / X-Ray; body uses lit Standard material (metalness 0.1) | **Decided (3T, 2026-10-24):** flatter default — metalness **0**, roughness **~0.55–0.65** (tune in PR if phone preview fails). Keep Shaded+Edges. | **P3** |
| Tool shelf show/hide | Fusion contextual tabs; Onshape toolbar collapses on small screens [13][14]; MVP already has Modify toggle (PROGRESS wrap-up) | One Modify shelf toggle; Create menu; dim sheet chevron for primitives | **Decided (3T, 2026-10-24):** every cluttering shelf show/hide; **none always-on** except the active tool’s shelf (Tools-sheet affordance; Doc Steward slice). | **P4** |
| Sketch | Fusion/Onshape/FreeCAD: sketch is a real mode with geometry + dimensions [13][14][15] | Sketch tab / Create→Sketch UI shell only | **Decided (3T, 2026-10-24):** park sketch until this P2 lands; then minimal **rect/circle-on-face → extrude** follow-on (not full constraint solver). | **P5** (after Measure) |
| Browser / phone | Onshape: 1-finger orbit, 2-finger pan/pinch, View Cube menu [16]; WCAG/HIG 44 px targets [17] | 44 px chips/sheets; tap-vs-drag; view cube present; Create/Modify phone patterns | Keep 44 px; do not cover bottom bar with banners (already ruled). Measure/Select-Other must fit portrait 390×844 smokes. | P1, P4, P5 |

## Next steps (Grok Build / Cursor)

1. **P1 first:** exclusive V/E/F/Body highlight on pick; regression in `test_phone_select.mjs` + phone smoke aims; optional Select-Other cycle chip.
2. **P3 (decided):** default body material metalness `0`, roughness `0.55–0.65`; screenshot before/after on 20 mm cube; keep Shaded+Edges.
3. **P4 (decided):** inventory shelves; show/hide each; none always-on except active tool’s shelf (Doc Steward / `prompts/p4-tool-shelf-show-hide.md`).
4. **P5a Measure (decided):** replace demo `updateMeasure()` with mm-locked two-point distance, selected-edge length, and volume; unit tests on a 20 mm cube; phone Confirm/readout ≥44 px.
5. **P5b Callouts (decided):** live L×W×H / Ø×H overlays on the active primitive while editing (not sheet-only).
6. **P5c Sketch (parked until P2 merges):** minimal rect/circle-on-face → extrude; no full constraint solver in that slice.

## Team decisions (3T, 2026-10-24 America/Denver)

1. **P1:** exclusive V/E/F highlight (click replaces); multi-filter later if needed.
2. **P3:** flatter default — metalness **0**, roughness **~0.55–0.65** (tune in PR if needed).
3. **P4:** every cluttering shelf show/hide; none always-on except the active tool’s shelf.
4. **P5 Measure first — yes:** two-point distance + selected-edge length + volume, mm-locked.
5. **P5 Callouts:** live L×W×H / Ø×H on the active primitive while editing (Fusion-style), not property-sheet only.
6. **P5 Sketch:** park until this P2 digest lands; then minimal rect/circle-on-face → extrude follow-on.

## Still open (implementation detail, not Erik park)

- **P5 sketch detail (after P2 merges):** exact extrude defaults / face-pick UX once the parked follow-on starts.
- **P1 Select-Other:** only if cheap in Pilot’s P1 PR; else follow-up note.

## Sources

1. Fusion Help, Use selection filters: https://help.autodesk.com/cloudhelp/ENU/Fusion-Model/files/SLD-SELECTION-FILTERS.htm  
2. FreeCAD wiki, Part SelectFilter: https://wiki.freecad.org/Part_SelectFilter  
3. Onshape Help, Selection: https://cad.onshape.com/help/Content/Home/selection.htm (also cited in `research/selection-and-delete.md`)  
4. Onshape Help, Select Other: https://cad.onshape.com/help/Content/select-other.htm  
5. Repo: `research/gui/modo-selection-primitives.md`  
6. Repo: `research/selection-and-delete.md`  
7. Fusion Help, Measure reference: https://help.autodesk.com/cloudhelp/ENU/Fusion-Model/files/GUID-D070A3CB-729F-410F-9DA4-D9DF7F4D55B5.htm  
8. Fusion Help, Analysis tools (Inspect → Measure): https://help.autodesk.com/cloudhelp/ENU/Fusion-Model/files/SLD-INSPECT-TOOLS.htm  
9. Onshape Help, Measure Tool: https://cad.onshape.com/help/Content/View/measure_tool.htm  
10. FreeCAD documentation, Std Measure: https://github.com/FreeCAD/FreeCAD-documentation/blob/main/wiki/Std_Measure.md  
11. Autodesk support, turn on/off model edge lines (Display Settings → Visual Style): https://www.autodesk.com/support/technical/article/caas/sfdcarticles/sfdcarticles/How-to-hide-edge-line-of-3D-model-in-Fusion.html  
12. Autodesk support, shaded vs wireframe visual style: https://www.autodesk.com/support/technical/article/caas/sfdcarticles/sfdcarticles/Model-is-shown-in-wireframes-instead-of-the-realistic-bodies-in-Fusion-360.html  
13. Repo prior digest: `research/gui/ui-layout-review.md` (Fusion workspaces/tabs, Onshape toolbar)  
14. Onshape Help, User Interface Basics: https://cad.onshape.com/help/Content/Home/user_interface_basics.htm  
15. FreeCAD wiki, PartDesign NewSketch: https://wiki.freecad.org/PartDesign_NewSketch  
16. Onshape Help, View Navigation and the View Cube: https://cad.onshape.com/help/Content/View/view_navigation_and_the_view_cube.htm  
17. Repo: `research/mobile-touch-cad.md` (WCAG 44 px, HIG 44 pt)  
18. Repo parked queue: `web/PROGRESS.md` (P1–P5, 2026-10-23)
19. Team locks (3T / Chief in CAD CAM MVP room, 2026-10-24): P1 exclusive V/E/F; P3 metalness 0 / roughness 0.55–0.65; P4 no always-on shelves; P5 Measure+callouts first, sketch after P2.
