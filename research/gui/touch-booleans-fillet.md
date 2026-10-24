# Touch Booleans + fillet/chamfer (after Extrude Join/Cut) — 2026-10-24

MVP Research Digest. Implementation prep for the next GB slice after Extrude Join/Cut. Units: **mm**. Gate: OCCT validity + units (watertight dropped, 02:17 rule). Invent nothing; **TBD** marks need 3T or Erik. Research only — no `web/`, prompts, UPDATES, PROGRESS, kernel, or WASM edits in this PR.

Related (reuse; do not contradict): [`extrude-join-cut.md`](extrude-join-cut.md) (Join/Cut shipped — do not reopen), [`booleans-fillet-chamfer.md`](booleans-fillet-chamfer.md), [`../occt-wasm/booleans.md`](../occt-wasm/booleans.md), [`../mobile-touch-cad.md`](../mobile-touch-cad.md), [`post-p5c-next.md`](post-p5c-next.md). Save/load stays in [`../project-save-load.md`](../project-save-load.md) and is **not** this slice.

## 1. Context (repo facts on `main`)

Extrude Join/Cut is on `main` via [#83](https://github.com/cyborgpencil/cad-mvp/pull/83) (merge `99063c9`). UPDATES line for that merge is [#84](https://github.com/cyborgpencil/cad-mvp/pull/84) (`4e69f01`). Later docs-only merges [#85](https://github.com/cyborgpencil/cad-mvp/pull/85) and [#86](https://github.com/cyborgpencil/cad-mvp/pull/86) put the tip at `ac47757` at write time. Pages deploy for `99063c9` succeeded ([run 40101083529](https://github.com/cyborgpencil/cad-mvp/actions/runs/40101083529)); that job runs CTest, including `deploy_smoke`, before upload. This note does not re-run Pages.

P1–P5 stay done ([#70](https://github.com/cyborgpencil/cad-mvp/pull/70)). Origin-plane empty-doc stays done ([#77](https://github.com/cyborgpencil/cad-mvp/pull/77)). Extrude T1–T5 stay the shipped Join/Cut behavior. Do not reopen them.

`web/PROGRESS.md` on this tip still has the 2026-10-24 ~8:06 AM MT line that the next slice was “boolean/fillet **or** save/load”. The later lock (below) picks touch Booleans + fillet/chamfer and withdraws save/load. This PR does not edit PROGRESS.

Facts from `web/index.html`, `web/occt-ops.mjs`, and `web/phone-select.mjs` on `main` @ `ac47757`:

**Two different Boolean paths**

- **Extrude Join/Cut** (done): sketch sheet chips New / Join / Cut. `commitSketchExtrude` → `makePrismSolid`, then `finishBooleanExtrude` calls `fuseShapes` or `cutShapes` into **one** target body. `worldOperand` copies the target first. Comment in that function: `fuseShapes` and `cutShapes` do not set NonDestructive, so a failed op must leave the stored body alone. Empty cut is rejected. No Intersect on the Extrude sheet.
- **Modify body Booleans** (this slice): Union / Cut / Intersect, `data-action="boolean"`, `data-op` union|cut|intersect. Desktop Model ribbon and phone `#modifyShelf`. `applySceneBoolean` → `applyBooleanSolids` → `fuseShapes` / `cutShapes` / `commonShapes`. Exactly two Item-selected bodies. Order is `selectedIds` order: **1 = target, 2 = tool** (`orderedBodies`, `#boolOrder`, viewport `.bool-badge` “1” and “2”). Cut title on the desktop button: “1 minus 2.” Result replaces those two bodies. Buttons stay `disabled` until Item selection contains exactly two bodies.

**Fillet / chamfer (already wired)**

- Desktop Fillet and Chamfer (`data-action="armEdge"`) and the same two buttons on `#modifyShelf`.
- `armEdgeTool` switches the pick filter to Edge and writes the sheet default: fillet **2 mm**, chamfer **0.5 mm** (`FILLET_DEFAULT_MM` / `CHAMFER_DEFAULT_MM` in `web/phone-select.mjs`; `EDGE_FILLET_RADIUS_MM` / `EDGE_CHAMFER_DISTANCE_MM` in `web/occt-ops.mjs`). Team-chosen 2026-10-23 (PROGRESS). These are the edge-tool defaults, not L-bracket dimensions.
- `#edgeSheet`: `#edgeSize` (starts as `type="number"`, `inputmode="decimal"`, value 2) and Confirm (`#edgeConfirm`, 44 CSS px). Hint: “Pick an edge, then Confirm. Nothing changes until Confirm.”
- Confirm calls `applyPickedEdgeOp` → `filletEdges` / `chamferEdges` (`BRepFilletAPI_MakeFillet.Add(radius, edge)` / `MakeChamfer.Add(distance, edge)` for every picked edge, one size). `checkEdgeOp` accepts OCCT validity + mm + one non-empty solid. Its comment says it does not consult the mesh watertight check.
- Several edges on **one** body can Confirm together. Edges on two bodies: Confirm stays off and the note is `pick edges on one body` (`CROSS_BODY_MESSAGE`).
- OCCT size failures toast `Try a smaller size.` (`SMALLER_SIZE_MESSAGE`). Other failures toast a “last good shape was kept” line. Success is a status hint (“Fillet applied.” / “Chamfer applied.”), not a toast.
- Fillet/chamfer Confirm goes through `runUndoable`. The Modify Boolean click does **not**: `action === 'boolean'` calls `applySceneBoolean` and returns.

**Keep-last-good (wired)**

- Boolean failure toasts and leaves both inputs in the body list (“Both inputs were kept.”), including empty results inside `applyBooleanSolids`.
- Fillet/chamfer: an OCCT rejection never replaces the body. If the new mesh is refused after the swap, the previous shape is put back.
- `SetNonDestructive(true)` is only on the glue-shift branch inside `booleanOp` (`fuseFlushShapes`). `fuseShapes` / `cutShapes` / `commonShapes` use `new Ctor(shapeA, shapeB)` and do not set it. `applySceneBoolean` copies a body only when `shapeLocal === true` (`placedCopy`). A world-space body is passed through as stored. Extrude Join/Cut already copies first for this reason. This note does not claim a failed Modify Boolean mutates those shapes; that check is T6.

**Preview (what is wired)**

- Modify Boolean runs exact OCCT on the button press. There is no ghost of a Boolean result while dragging.
- Fillet/chamfer run exact OCCT on Confirm. `LBRACKET_FILLET_LIVE_PREVIEW` is `false`. `buildLBracket` logs “Live preview is out of scope. The fillet is applied once.”
- Move-gizmo `previewOwnedShift` is a placement preview, not a Boolean or fillet preview.
- [`../occt-wasm/booleans.md`](../occt-wasm/booleans.md) still recommends a ghost while dragging a tool body and the exact OCCT Boolean on release, with manifold-3d only if asked. That drag-tool preview is not the current Modify Boolean.

**Phone chrome**

- `#modifyShelf` buttons (Move, Rotate, Resize, Fillet, Chamfer, Union, Cut, Intersect, Delete) are min 44×44 CSS px. Pick-chooser rows and phone-tabbar tabs are min 44 CSS px. Edge Confirm is 44 CSS px.
- Narrow layout (`max-width: 820px`, or `max-height: 520px`) hides `.group-label`, so the desktop sentence in `#boolOrder` (“1 = target, 2 = tool”) is hidden. Portrait and `max-width: 820px` also hides the model ribbon (`.toolbox .tools:not(.export-tools) { display: none }`). Phone Union/Cut/Intersect are on `#modifyShelf`. Those titles are “Union” / “Cut” / “Intersect”, without “1 with 2”.
- Badges still paint in `#viewport` when two bodies are Item-selected. `.bool-badge` is 22 px tall, `pointer-events: none` (a label, not a hit target).
- Phone Body filter maps to Item (`modeForFilter`). Multi off replaces the selection (`selectionFromTap`). A second body is added only while Multi is on, in tap order. Edge touch radius is `EDGE_TOUCH_TOLERANCE_PX` **32** (team-locked 2026-10-23 in PROGRESS; larger than the 20 px body/face touch pick). Do not reopen 32.
- `#edgeSheet` sits inside `#viewport` at `bottom: 76px`. The phone tab bar is outside that box. Whether the sheet clears the in-viewport view bar on a 390×844 portrait was not measured here.

**Gate mismatch (repo fact)**

- `applyBooleanSolids` still requires `view.watertight.pass === true` along with the OCCT gate, mm, a non-empty volume, and at least one solid. `checkEdgeOp` for fillet/chamfer does not. The 02:17 rule is OCCT validity + units. Watertight stays dropped.

**Helpers already present (libcascade 3.1.0, no new WASM)**

- `fuseShapes`, `cutShapes`, `commonShapes`, `filletEdges`, `chamferEdges`, `applyBooleanSolids`, `applyPickedEdgeOp`, `buildLBracket`.
- Fuse calls `SimplifyResult(true, true)` when `IsDone()` is true. Cut and Common do not. `SetFuzzyValue` is not called. Fuzzy millimetres stay the open TBD in [`../occt-wasm/booleans.md`](../occt-wasm/booleans.md). No number is proposed here.
- `buildLBracket` remains the demo/fixture path. L-bracket L1, W, T, H, inner radius, and chamfer edges stay the open TBDs in [`booleans-fillet-chamfer.md`](booleans-fillet-chamfer.md). This slice does not set them.

Sketch-tab “Fillet” is a `data-tool` button with no `data-action`. It is not the solid-edge Fillet.

Chief/3T lock (2026-10-24, America/Denver): next GB slice is **touch Booleans + fillet/chamfer** (modeling-first). Save/load is withdrawn for this slice. P1–P5 stay closed.

## 2. Typical CAD patterns (sourced)

| Product | Body vs body | Edge round / bevel | How this differs from Extrude Join/Cut | Sources |
|---|---|---|---|---|
| **Fusion** | A separate body Combine tool is **not** described in the related digests. This note does not invent its UI. | — | Cited Extrude Operation is Join / Cut / Intersect / New Body on a **sketch prism**. That path is already shipped. | Fusion Extrude [14]; solids from sketches [15] |
| **Onshape** | The cited Boolean Options lesson is Extrude merge scope (first Extrude is New). A separate body-Boolean page is not cited here. | — | Extrude result types are New / Add / Remove / Intersect. Shipped Extrude uses New / Join / Cut only. | Onshape Extrude [16]; Boolean Options lesson [17] |
| **FreeCAD** | Part **Fuse** unites shapes into one solid. PartDesign **Boolean** is Fuse / Cut / Common across bodies. | OCCT fillet/chamfer classes below are the kernel. A FreeCAD Part Fillet page is not cited in the related digests. | Pad is additive and Pocket is subtractive on the active Body. Those are the Extrude analogues, already mapped in the Join/Cut note. | Part Fuse [18]; PartDesign Boolean [19]; Pad [20]; Pocket [21] |
| **Modo** | Mesh Boolean wants watertight meshes and cleanup. MeshFusion keeps sources and can update live; docs ship draft/deferred modes because continuous updates get heavy. | Edge Bevel is the mesh analogue cited in the Modo tools note. | Not a sketch-prism operation. MVP stays on OCCT B-rep, not mesh Booleans. | Modo Boolean [22]; MeshFusion intro [23]; Fusion Item [24]; Edge Bevel [25] |
| **OCCT 8.0.1** | `BRepAlgoAPI_Fuse` / `Cut` / `Common`. Check `IsDone()` before `Shape()`. Options include `SetNonDestructive`, `SetFuzzyValue`, `SetGlue`, `SimplifyResult` on fuse. | `BRepFilletAPI_MakeFillet.Add(radius, edge)` then `Build()`. `MakeChamfer.Add(distance, edge)` symmetric. Asymmetric `Add(d1, d2, …)` / `AddDA` exist on the class. `IsDone()` false: `Shape()` throws `StdFail_NotDone`. | Prism is `BRepPrimAPI_MakePrism` / `makePrismSolid` (Extrude). | Boolean guide [26]; BooleanOperation [27]; MakeFillet [28]; MakeChamfer [29]; MakePrism [30]; BRepCheck_Analyzer [31] |

## 3. Gap vs MVP today

| Area | Already on `main` @ `ac47757` | Incomplete for touch |
|---|---|---|
| Selection order 1 = target, 2 = tool | `orderedBodies` + badges + desktop `#boolOrder`. Toast if not exactly two: “Select exactly two bodies. 1 is the target and 2 is the tool.” | Phone shelf has no order sentence (ribbon and `.group-label` hidden on narrow portrait). Second body needs Multi on. No swap control. |
| Union / Cut / Intersect | Buttons on desktop and `#modifyShelf`, ≥44 CSS px, disabled until two Item bodies. `applyBooleanSolids` on click. Failure toast, both inputs kept. | Not an undo step. World-space operands are not copied before the op. Accept path still requires watertight. No ghost result while dragging. |
| Edge pick → sheet → Confirm | Arming Fillet/Chamfer sets Edge mode, 2 mm or 0.5 mm, shows `#edgeSheet`. Confirm runs OCCT and keeps the last good shape. Phone shelf has both tools. | `#edgeSize` is `type="number"`. Sketch length/depth fields are `type="text"` `inputmode="decimal"` with an mm suffix. Edge sheet has no mm suffix and no +/- stepper. |
| Multi-edge | One radius or distance on every picked edge of **one** body. Cross-body Confirm stays off. | Variable-radius fillet and asymmetric chamfer are not in the UI (OCCT has them). Left out of this slice unless 3T asks. |
| Failure toasts | Boolean: cause plus “Both inputs were kept.” Fillet/chamfer: “Try a smaller size.” or “last good shape was kept.” | Success fillet/chamfer is a hint only. Boolean success toasts the new body name. Copy is not a new lock. |
| Preview | Exact OCCT on Boolean click and on fillet/chamfer Confirm. | Ghost-during-drag and live fillet radius from the booleans digests are not wired. `LBRACKET_FILLET_LIVE_PREVIEW` is false. |
| Extrude Join/Cut | Shipped. Prism + `fuseShapes`/`cutShapes`, one target, copy-first. | Out of this slice. Do not edit `commitSketchExtrude`. |
| Phone hit size | Shelf, Confirm, pick chips ≥44 CSS px. Edge touch radius 32 px (locked). | Badge is a 22 px label. Do not treat it as a control. |

## 4. Recommended MVP slice (propose — locks TBD)

Prefer JS + existing libcascade 3.1.0 bindings in `web/occt-ops.mjs`. No kernel / WASM rebuild. Modeling-first. Save/load stays deferred.

1. **Keep** Modify Union / Cut / Intersect on `fuseShapes` / `cutShapes` / `commonShapes` via `applyBooleanSolids`, and edge fillet/chamfer on `filletEdges` / `chamferEdges` via `applyPickedEdgeOp`.
2. **Keep** order 1 = target, 2 = tool, exactly two bodies, badges, keep-last-good, phone controls ≥44 CSS px, fillet default 2 mm, chamfer default 0.5 mm, edge touch radius 32 px.
3. **Keep** Extrude New / Join / Cut as shipped. Do not retune T1–T5.
4. **Phone order (T1, T2):** surface the existing “1 = target, 2 = tool” sentence with the Modify shelf. Leave Multi as the way to add body 2.
5. **Edge sheet (T3):** propose the sketch decimal pattern (`type="text"`, `inputmode="decimal"`, visible mm) so a phone keypad can type the radius. Stepper step stays unnumbered.
6. **Preview (T4):** propose no drag-Boolean and no live radius this slice. Exact OCCT stays on the Boolean button and on fillet/chamfer Confirm.
7. **Undo (T5):** propose one undo step for a successful Modify Boolean, same stack as fillet Confirm. A failure does not push.
8. **Operands (T6):** propose the Extrude copy-first pattern (or `SetNonDestructive`) on the interactive Boolean so a failed op leaves stored shapes alone. Do not set Glue on Cut/Common. Do not invent a fuzzy millimetre.
9. **Gate (T7):** propose `applyBooleanSolids` accept on OCCT validity + mm + non-empty, matching `checkEdgeOp` and the 02:17 rule. Leave the hole `checkSolidGate` alone.
10. **Out of scope:** P1–P5 queue; origin-plane T1–T5; Extrude Join/Cut; save/load; MCP tool list; assemblies Orca filament mapping; L-bracket dimension locks; kernel/WASM rebuild; manifold-3d; variable-radius fillet; asymmetric chamfer; three-or-more-body Boolean; history tree that keeps both source bodies after a successful op (Modo Fusion Item pattern stays a lesson, not this slice).

## 5. TBD locks for 3T / Erik (non-binding proposes)

| # | Question | Propose (non-binding) |
|---|---|---|
| T1 | Show “1 = target, 2 = tool” on the phone Modify shelf? | **Yes.** Reuse the desktop sentence. Badges stay. No new copy. |
| T2 | How does a phone pick body 2? | **Keep Multi.** Multi off still replaces the selection. Do not auto-enable Multi when Union/Cut/Intersect is tapped. |
| T3 | Edge size control? | Match the sketch fields: `type="text"`, `inputmode="decimal"`, visible **mm**. +/- step size stays **TBD** (no number). Keep 2 mm and 0.5 mm defaults. |
| T4 | Ghost or live preview in this slice? | **No.** Exact OCCT on Boolean click and on fillet/chamfer Confirm. Leave `LBRACKET_FILLET_LIVE_PREVIEW` false. Manifold-3d stays out. |
| T5 | Modify Boolean on the undo stack? | **Yes**, one step, same as fillet Confirm and Combine. Failure does not push. No history tree. |
| T6 | Protect stored bodies on a failed Modify Boolean? | **Yes.** Copy operands before `fuseShapes` / `cutShapes` / `commonShapes`, same reason as `worldOperand`. Fuzzy value stays unset. Glue stays on `fuseFlushShapes` only. |
| T7 | Drop watertight from `applyBooleanSolids` accept? | **Yes**, this function only. OCCT validity + mm + non-empty. Do not edit hole `checkSolidGate` here. |

## 6. Next steps

1. **3T:** lock T1–T7 (or mark Pilot-discretion).
2. **Doc Steward:** tip-match this research PR (Digest is the author — do not self-APPROVE). After it is on `main`, write the GB prompt. PROGRESS/UPDATES stay with their owners.
3. **Pilot:** hold GB until that prompt’s tip is on `main`. Then JS-only: phone order sentence, edge mm field per T3, Boolean undo per T5, copy-first per T6, Boolean accept gate per T7. Smoke: two bodies, Union then undo; Cut that misses toasts and keeps both; oversize fillet toasts “Try a smaller size.” and keeps the solid; phone shelf and Confirm ≥44 CSS px; Extrude New/Join/Cut unchanged. Check the edge sheet against the view bar at 390×844 (clearance was not measured here).
4. **Repo Keeper:** plain-merge this research PR when the docs review is in.

## 7. Sources

Repo (`main` @ `ac47757`):

1. `web/index.html` — Modify Union/Cut/Intersect, `#boolOrder`, `#boolBadges`, `#modifyShelf`, `#edgeSheet`, `applySceneBoolean`, `confirmPickedEdge`, `commitSketchExtrude`, `worldOperand`, `finishBooleanExtrude`
2. `web/occt-ops.mjs` — `fuseShapes`, `cutShapes`, `commonShapes`, `filletEdges`, `chamferEdges`, `applyBooleanSolids`, `applyPickedEdgeOp`, `checkEdgeOp`, `buildLBracket`, `EDGE_FILLET_RADIUS_MM` 2, `EDGE_CHAMFER_DISTANCE_MM` 0.5, `LBRACKET_FILLET_LIVE_PREVIEW` false
3. `web/phone-select.mjs` — `selectionFromTap`, `armEdgeTool`, `confirmEdgeDecision`, `EDGE_TOUCH_TOLERANCE_PX` 32, `FILLET_DEFAULT_MM` 2, `CHAMFER_DEFAULT_MM` 0.5, `SMALLER_SIZE_MESSAGE`, `CROSS_BODY_MESSAGE`
4. `research/gui/extrude-join-cut.md` — Join/Cut prep; do not reopen
5. `research/gui/booleans-fillet-chamfer.md` — MakeFillet / MakeChamfer / Fuse; L-bracket dims still TBD
6. `research/occt-wasm/booleans.md` — ghost on drag, exact OCCT on release; fuzzy TBD
7. `research/mobile-touch-cad.md` — ≥44 CSS px; `type="text"` `inputmode="decimal"` proposal
8. `research/gui/post-p5c-next.md` — earlier pickup list; this lock supersedes the next slice only
9. `web/PROGRESS.md` — 02:17 gate; phone fillet/chamfer choices 2026-10-23; edge touch 32 px; 8:06 AM MT “boolean/fillet or save/load” line (superseded for the next slice by the lock below)
10. PR #83: https://github.com/cyborgpencil/cad-mvp/pull/83 (merge `99063c9`)
11. PR #84: https://github.com/cyborgpencil/cad-mvp/pull/84 (`4e69f01`)
12. Pages deploy for `99063c9`: https://github.com/cyborgpencil/cad-mvp/actions/runs/40101083529
13. Team lock (Chief / 3T, 2026-10-24, America/Denver): next GB slice is touch Booleans + fillet/chamfer; save/load withdrawn; modeling-first; P1–P5 stay done.

Official / docs already used in the related digests:

14. Fusion Help, Extrude reference (Operation Join / Cut / Intersect / New Body): https://help.autodesk.com/cloudhelp/ENU/Fusion-Model/files/SLD-REF-EXTRUDE.htm
15. Fusion Help, Solids from sketches: https://help.autodesk.com/cloudhelp/ENU/Fusion-Model/files/SLD-CREATE-SOLID-FROM-SKETCH.htm
16. Onshape Help, Extrude (New / Add / Remove / Intersect; Merge scope): https://cad.onshape.com/help/Content/PartStudio/extrude.htm
17. Onshape Learning, Boolean Options (first Extrude New; Merge scope): https://learn.onshape.com/learn/video/boolean-options
18. FreeCAD documentation, Part Fuse: https://wiki.freecad.org/Part_Fuse
19. FreeCAD documentation, PartDesign Boolean (Fuse / Cut / Common): https://wiki.freecad.org/PartDesign_Boolean
20. FreeCAD documentation, PartDesign Pad: https://wiki.freecad.org/PartDesign_Pad
21. FreeCAD documentation, PartDesign Pocket: https://wiki.freecad.org/PartDesign_Pocket
22. Modo Boolean: https://learn.foundry.com/modo/current/content/help/pages/modeling/edit_geometry/boolean.html
23. Modo MeshFusion introduction: https://learn.foundry.com/modo/content/help/pages/meshfusion/mf_introduction.html
24. Modo Fusion Item (sources kept): https://modosdk.foundry.com/modo/12.0/content/help/pages/meshfusion/mf_fusion_item.html
25. Modo Edge Bevel: https://modosdk.foundry.com/modo/content/help/pages/modeling/vert_edge_poly_comp_tools/edge_bevel.html
26. OCCT Boolean Operations guide: https://dev.opencascade.org/doc/overview/html/specification__boolean_operations.html
27. OCCT `BRepAlgoAPI_BooleanOperation`: https://dev.opencascade.org/doc/refman/html/class_b_rep_algo_a_p_i___boolean_operation.html
28. OCCT `BRepFilletAPI_MakeFillet`: https://dev.opencascade.org/doc/refman/html/class_b_rep_fillet_a_p_i___make_fillet.html
29. OCCT `BRepFilletAPI_MakeChamfer`: https://dev.opencascade.org/doc/refman/html/class_b_rep_fillet_a_p_i___make_chamfer.html
30. OCCT `BRepPrimAPI_MakePrism`: https://dev.opencascade.org/doc/refman/html/class_b_rep_prim_a_p_i___make_prism.html
31. OCCT `BRepCheck_Analyzer`: https://dev.opencascade.org/doc/refman/html/class_b_rep_check___analyzer.html
32. WCAG 2.5.5 target size (44 CSS px), via `research/mobile-touch-cad.md`: https://www.w3.org/WAI/WCAG21/Understanding/target-size.html
