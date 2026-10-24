# Touch Booleans and fillet/chamfer

Team-chosen by Doc Steward, 2026-10-24 (America/Denver). Locks T1–T7 adopt the Digest proposes in `research/gui/touch-booleans-fillet.md` and are final. That note is on main via #87 (`bd7dcc0`, merge `0c795bd`). Its TBD table is closed by the locks below. App facts in the note were checked at `ac47757`. This prompt was written on main `6acde93` (#88 is the UPDATES line for #87). Extrude Join/Cut stays closed (#83, merge `99063c9`; UPDATES #84 at `4e69f01`). Also read `prompts/extrude-join-cut.md` and `prompts/mobile-4-fillet-chamfer.md`. Feed this to Grok Build / Cursor. This file is the spec. It does not change the app.

## Context
- WASM UI in `web/` (mostly `web/index.html`, plus `web/occt-ops.mjs` and `web/phone-select.mjs`). Work in the Z13 repo (`C:\Dev\cadcam-mvp`).
- Units stay millimetres.
- After modeling ops, keep the OCCT shape-validity check and the millimetre units check. Watertight was dropped (02:17 rule). This slice applies that rule to `applyBooleanSolids` only (T7).
- Modify Union / Cut / Intersect are already wired. `data-action="boolean"`, `data-op` union|cut|intersect, on the desktop Model ribbon and on phone `#modifyShelf`. `applySceneBoolean` calls `applyBooleanSolids`, which calls `fuseShapes`, `cutShapes`, or `commonShapes`. Exactly two Item-selected bodies. Order is `selectedIds` order: **1 = target, 2 = tool** (`orderedBodies`, `#boolOrder`, viewport `.bool-badge` “1” and “2”). Cut on the desktop button is “1 minus 2.” The result replaces those two bodies. Buttons stay disabled until Item selection contains exactly two bodies.
- Fillet and chamfer are already wired. Desktop and `#modifyShelf` use `data-action="armEdge"`. `armEdgeTool` switches the pick filter to Edge and writes the sheet default: fillet **2 mm**, chamfer **0.5 mm** (`FILLET_DEFAULT_MM` / `CHAMFER_DEFAULT_MM`; `EDGE_FILLET_RADIUS_MM` / `EDGE_CHAMFER_DISTANCE_MM`). Confirm calls `applyPickedEdgeOp` → `filletEdges` / `chamferEdges` (one size on every picked edge of one body). `checkEdgeOp` accepts OCCT validity + mm + one non-empty solid and does not consult the mesh watertight check. Confirm goes through `runUndoable`. OCCT size failures toast `Try a smaller size.` (`SMALLER_SIZE_MESSAGE`). The last good shape stays.
- The Modify Boolean click does not use that stack. `action === 'boolean'` calls `applySceneBoolean` and returns.
- `fuseShapes` and `cutShapes` do not set NonDestructive. `worldOperand` copies the Extrude target first so a failed Join or Cut leaves the stored body alone. `applySceneBoolean` copies a body only when `shapeLocal === true` (`placedCopy`). A world-space body is passed through as stored.
- `SetNonDestructive(true)` and `SetGlue` are only on the glue-shift branch inside `booleanOp` (`fuseFlushShapes`). `SetFuzzyValue` is not called.
- `applyBooleanSolids` still requires `view.watertight.pass === true` along with `view.gate.pass`, the millimetre units check, and a non-empty result (volume above `BOOLEAN_EMPTY_VOLUME_MM3`, at least one solid, at least one triangle). Hole cuts use `checkSolidGate`, which still requires watertight. Leave `checkSolidGate` as it is.
- Narrow layout (`max-width: 820px`, or `max-height: 520px`) hides `.group-label`, so the desktop sentence in `#boolOrder` is hidden. Phone Union / Cut / Intersect live on `#modifyShelf`. Badges still paint. `.bool-badge` is a 22 px label with `pointer-events: none`.
- Phone Body filter maps to Item. Multi off replaces the selection (`selectionFromTap`). A second body is added only while Multi is on, in tap order. Tapping Union / Cut / Intersect does not turn Multi on today.
- `#edgeSize` is `type="number"` with `min="0.01"` and `step="0.1"`. Sketch length, width, diameter, and blind depth are `type="text"`, `inputmode="decimal"`, with a visible `mm` suffix. `readField` trims and maps a comma to a dot.
- `#modifyShelf` buttons and `#edgeConfirm` are at least 44 CSS px. Edge touch radius is `EDGE_TOUCH_TOLERANCE_PX` **32**. Leave 32 as it is.
- `#edgeSheet` is `position: absolute; bottom: 76px` inside `#viewport`. On a narrow portrait, `.vp-bar` sits at `bottom: 8px` inside that same box. `#sketchSheet` shares `.edge-sheet`. Clearance of the open edge sheet against the view bar at 390×844 was not measured in the research note.
- Exact OCCT runs on the Boolean click and on fillet/chamfer Confirm. `LBRACKET_FILLET_LIVE_PREVIEW` is `false`. There is no ghost of a Boolean result.
- A failed or empty Modify Boolean toasts and leaves both inputs in the body list. The existing empty case is Intersect of the disjoint pair (`tests/test_occt_gate.mjs`: `buildOverlapBoolean` with `BOOLEAN_DISJOINT_SHIFT_MM`, message contains “empty” and “kept”, `inputsKept === true`).
- Overlap pair `/?pair=overlap`: two 20 mm boxes, second shifted `BOOLEAN_OVERLAP_SHIFT_MM` (10) on X. Volumes are `expectedOverlapVolumes()` (union 12000 mm³, cut 4000 mm³, intersect 4000 mm³) within `BOOLEAN_VOLUME_TOL_MM3` (1e-3). Hotkey 4 selects both in Item order. Disjoint pair `/?pair=disjoint` uses `BOOLEAN_DISJOINT_SHIFT_MM` (40).
- The default session seeds one 20 mm cube, centre (0, 0, 10). Volume is 8000 mm³.
- Do not commit `.wasm`, `web/cadcam.wasm`, or `web/dist/`. Do not edit `UPDATES.md`. Do not add or edit a root `PROGRESS.md`. Leave `web/PROGRESS.md` for a separate scrub.
- Prefer JS, CSS, and HTML, plus the existing libcascade 3.1.0 JS bindings in `web/occt-ops.mjs`. No kernel, C++, `src/`, `web/bindings.cpp`, or `cadcam.wasm` rebuild. If a needed binding is missing, stop and report it. Do not add a second Boolean path or a second fillet path.
- Commit on a PR branch. Never push to main. Repo Keeper merges after `ci.yml` is green.

## Team-chosen behaviour
Keep Modify Union / Cut / Intersect on `fuseShapes` / `cutShapes` / `commonShapes` via `applyBooleanSolids`. Keep edge fillet/chamfer on `filletEdges` / `chamferEdges` via `applyPickedEdgeOp` and `runUndoable`. Keep order 1 = target, 2 = tool, exactly two bodies, badges, keep-last-good, phone controls at least 44 CSS px, fillet default 2 mm, chamfer default 0.5 mm, and edge touch radius 32 px. Keep Extrude New / Join / Cut as shipped.

### T1 — Phone order sentence
When `#modifyShelf` is open, the shelf shows the existing sentence `1 = target, 2 = tool`. That is the desktop wording in `#boolOrder`. No new copy. Desktop `#boolOrder` keeps the live lines `paintBooleanChrome` already writes. Badges stay in the viewport. The phone sentence is a label, not a hit target, same as `.bool-badge`.

Narrow layout hides `.group-label`, and the desktop ribbon is hidden on portrait, so the desktop node is not enough. The sentence has to be visible with the open Modify shelf at 390×844. Leave the other group labels hidden. Hide this sentence when the shelf is closed.

Shelf buttons stay at least 44 CSS px. The sentence does not cover the phone tab bar.

### T2 — Multi stays the way to pick body 2
Keep Multi. Multi off still replaces the selection (`selectionFromTap`). A second body is added only while Multi is on, in tap order. Opening the Modify shelf, or tapping Union, Cut, or Intersect, does not set `state.phoneMulti`. There is no swap control.

### T3 — Edge size field
`#edgeSize` matches the sketch fields: `type="text"`, `inputmode="decimal"`, `autocomplete="off"`, `spellcheck="false"`, and a visible `mm` suffix on the label. Keep `aria-label="Edge size mm"` and the existing title. Arming Fillet still writes **2**. Arming Chamfer still writes **0.5**. No +/- stepper and no `min` / `step` on this slice.

Parse a typed size as a positive number of millimetres. Accept a comma decimal the way `readField` does (trim, comma to dot) so the phone keypad still Confirms. Blank, zero, and negative stay rejected before OCCT, through `parseEdgeSize` / `confirmEdgeDecision`. Confirm stays on `runUndoable` → `confirmPickedEdge` → `applyPickedEdgeOp`. The hint stays “Pick an edge, then Confirm. Nothing changes until Confirm.”

### T4 — No ghost or live preview
Exact OCCT stays on the Boolean click and on fillet/chamfer Confirm. Leave `LBRACKET_FILLET_LIVE_PREVIEW` false. No drag-Boolean ghost. No live radius while the size is typed. Manifold-3d stays out.

### T5 — Boolean undo
A successful Modify Boolean is one undo step on the same `runUndoable` stack as fillet Confirm and Combine. The click becomes `runUndoable` with the op name already used for the result (Union, Cut, or Intersect). `applySceneBoolean` returns true only after the result body is installed and the mesh is accepted. Every failure returns not true: `runUndoable` does not push, and it does not roll the scene back by itself, so the failure path must leave both bodies in place before it returns.

Undo of a successful Boolean restores both source bodies. Success still replaces the two bodies with one result. There is no history tree that keeps the sources after a successful op.

A failure toasts with the existing “Both inputs were kept.” line (or the existing mesh-reject line) and does not push. That includes an empty result, an OCCT reject, a units reject, and a rejected mesh.

### T6 — Copy operands first
Before `applyBooleanSolids`, copy both operands with `worldOperand`, the same helper Extrude Join/Cut uses. A local solid is placed into world millimetres. A world solid is copied in place. Pass that helper’s shape into `fuseShapes`, `cutShapes`, or `commonShapes`. Drop owned copies after the call, the way `finishBooleanExtrude` drops `world.shape`.

If `worldOperand` returns no shape, toast, keep both stored bodies, and do not push undo.

Do not edit `worldOperand`, `fuseShapes`, `cutShapes`, `commonShapes`, or `fuseFlushShapes`. Do not set `SetNonDestructive` or `SetGlue` on the Modify path. Glue stays on `fuseFlushShapes` only. Do not call `SetFuzzyValue`. Do not invent a fuzzy millimetre.

### T7 — Boolean accept gate
In `applyBooleanSolids` only, drop `view.watertight.pass` from the accept. Accept when the result is non-empty, `view.gate.pass === true` (OCCT `BRepCheck_Analyzer` valid and `ShapeAnalysis_FreeBounds` free-edge count 0), and `unitsLockGate().pass === true`. Non-empty stays the current check: volume above `BOOLEAN_EMPTY_VOLUME_MM3`, at least one solid, and at least one triangle.

A watertight miss alone does not reject. Keep returning the `watertight` object on the result. Keep the empty, OCCT, and units error text, including “Both inputs were kept.”

Do not edit hole `checkSolidGate`. Do not switch `applyBooleanSolids` over to `checkEdgeOp`. Do not change the input-kept watertight check inside `buildOverlapBoolean` (that checks the operands after a failed op). `buildLBracket` stays on its own gate.

## Acceptance
- T1. Portrait 390×844, Modify shelf open: the visible shelf label reads `1 = target, 2 = tool`, including when two Item bodies are selected. Badges “1” and “2” still paint. The label is not a hit target. Shelf buttons stay at least 44 CSS px and do not cover the phone tab bar. Closing the shelf hides the sentence. Other `.group-label` rows stay hidden on the narrow layout. Desktop `#boolOrder` still updates its live lines.
- T2. With Multi off, a second body tap replaces the selection. Tapping Union, Cut, or Intersect does not turn Multi on. With Multi on, the second tap adds body 2 in tap order. Buttons stay disabled until exactly two Item bodies are selected.
- T5, overlap Union. `/?pair=overlap`, hotkey 4 (two Item bodies, order kept). Union succeeds. One body remains. `booleanOp` is `union`. OCCT gate passes and the mm gate passes. Volume is 12000 mm³ within `BOOLEAN_VOLUME_TOL_MM3` (1e-3). Undo depth increases by one. Undo restores both boxes and the previous depth.
- T5, failure. A Boolean `applyBooleanSolids` rejects does not push undo. Body count stays 2. The toast keeps both (existing “Both inputs were kept.” copy). Concrete empty case already in `tests/test_occt_gate.mjs`: `/?pair=disjoint`, two Item-selected bodies, Intersect. Message contains “empty” and “kept”. Both boxes stay. Each box volume stays 8000 mm³ within `BOOLEAN_VOLUME_TOL_MM3`. Undo depth is unchanged.
- Cut that misses / fails. On `/?pair=disjoint`, two Item-selected bodies, Cut. If the gate rejects it (empty, OCCT, or units), the toast keeps both, body count stays 2, volumes stay 8000 mm³ within tolerance, and undo depth is unchanged. If OCCT returns a valid non-empty solid, that Cut is a T5 success: one body, one undo step that restores both. Do not add a separate “tool missed” reject on top of T7.
- T6. On that rejected disjoint Intersect, the stored shapes are still the pre-op solids (volumes unchanged, OCCT gate still passing on each). The op ran on copies.
- T7. Overlap union, cut, and intersect still pass OCCT validity, mm, and the existing volume checks in `tests/test_occt_gate.mjs`. A watertight miss is not what rejects them. Hole `checkSolidGate` still requires watertight. Disjoint Intersect still fails empty.
- T3. Arming Fillet shows `#edgeSize` as text, decimal keypad, visible `mm`, value 2. Arming Chamfer shows 0.5. No +/- stepper. A typed positive size, including a comma decimal, still enables Confirm for edges on one body. Cross-body Confirm stays off (`pick edges on one body`).
- Oversize fillet. The existing phone check stands: `?part=l`, Fillet, size 80, Confirm. Toast is `Try a smaller size.` The solid is kept. Undo depth does not increase.
- T4. `LBRACKET_FILLET_LIVE_PREVIEW` is still false. No ghost mesh appears before Boolean click or before fillet/chamfer Confirm.
- Phone shelf and Confirm. At 390×844, each `#modifyShelf` button and `#edgeConfirm` is at least 44 CSS px.
- Edge sheet vs view bar. At 390×844 with Fillet armed and `#edgeSheet` open, the sheet box does not overlap `.vp-bar` and does not cover the phone tab bar. Confirm and the size field stay at least 44 CSS px. `#sketchSheet` shares `.edge-sheet`. The Extrude New / Join / Cut chips stay at least 44 CSS px and stay off the bottom bar, as on main.
- Extrude New / Join / Cut still works as on main. `commitSketchExtrude`, `finishBooleanExtrude`, and the shipped T1–T5 behaviour are unchanged.

## Tests
Extend the smoke that already exists. Do not add a new smoke file or a new harness.

- `tests/deploy_smoke.py` already loads `/?pair=overlap`, presses 4, and runs Union / Cut / Intersect. Add the undo check on Union where that flow already fits: depth increases by one, undo restores two bodies. Add the disjoint failure where it fits: `/?pair=disjoint`, Intersect keeps both and does not push; Cut follows the acceptance rule above.
- `tests/phone_smoke.py` already uses the 390×844 viewport and checks Extrude chips. Add the open-shelf sentence `1 = target, 2 = tool`, shelf button size, and the edge-sheet vs `.vp-bar` check only where one already fits.
- `tests/edge_fillet_smoke.py` already toasts `Try a smaller size.` for size 80 and keeps the solid. Leave that check passing. Extend it only if the text field or the sheet clearance needs a line in that file.
- `tests/test_occt_gate.mjs` stays green. Overlap volumes stay. Disjoint Intersect stays an empty reject with inputs kept. Do not drop watertight assertions on holes or on solids that are still watertight. Do not edit `checkSolidGate` to make a hole test pass.

## Out of scope
- P1–P5 retune. Origin-plane empty-doc. Extrude Join/Cut retune, including `commitSketchExtrude` and `finishBooleanExtrude`.
- Save/load. MCP tool list. Assemblies and Orca filament mapping.
- L-bracket dimensions. `buildLBracket`. Variable-radius fillet. Asymmetric chamfer (`Add(d1, d2)` / `AddDA`).
- Kernel or WASM rebuild. Manifold-3d. A fuzzy millimetre. Glue on Cut or Common.
- Ghost or live preview. A +/- stepper on the edge size.
- A body picker, a swap control, or auto-enable Multi.
- Three-or-more-body Boolean. A history tree that keeps both source bodies after a successful op.
- Hole `checkSolidGate`. Sketch-tab Fillet (`data-tool` only, no `data-action`). Edge touch radius 32.
- New toast copy. The Boolean failure line and `Try a smaller size.` stay as they are.

## Done
`ci.yml` green on the PR (a docs-only diff may skip the native build; a code diff runs the build). Tip-match reviews. This prompt PR stays draft until Research Digest tip-matches (primary). Doc Steward is second. If Digest is busy, Doc Steward tip-matches; the research note was already tip-matched by Doc Steward. Repo Keeper undrafts and plain-merges. Report the PR link and the tip SHA.
