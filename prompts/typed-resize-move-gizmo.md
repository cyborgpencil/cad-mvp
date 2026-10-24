# Typed exact resize and move-gizmo drag

Team-chosen and authored by Doc Steward, 2026-10-24 (America/Denver). Locks T1–T6 are 3T/Digest final, 2026-10-24 ~3:10 PM America/Denver. They come from Digest’s note against main `23e54b7` (merge of #109, the UPDATES line for #108) and are final. App facts were checked at `23e54b7`. Feed this to Grok Build / Cursor. This file is the spec. It does not change the app.

Units: **mm**. Gate: OCCT validity + units (watertight dropped, 02:17 rule). Do not reopen P1–P5. Shipped on main and closed: P1 selection overlays #47 (`cc769e1`), P3 shaders #58 (`aa36137`), P4 shelves #54 (`1578ad0`), P5a Measure #60 (`ec00e2f`), P5b callouts #64 (`7bcb81d`), P5c sketch #70 (`7c83b2a`). P2 stays the UI-gap digest #43 (`4fd4dbe`). Touch gestures #21 (`50980eb`), #22 (`b61b881`), and #24 (`0e73596`) stay closed. Do not redo sketch (face sketch and Blind extrude #70, origin-plane empty-doc #77 `347888e`, Extrude New/Join/Cut #83 `99063c9`, measure angle/area and sketch callouts #98 `56c2528`, click-click line #108 `a5f4763`). Sources: `prompts/type-in-resize.md`, `research/selection-and-delete.md`, `tests/gizmo_drag_smoke.py`, the gizmo and resize hooks in `web/index.html` and `web/occt-ops.mjs`, and Digest’s note against #16 (`4117e42`, multi-body size and move) and #31 (`80858f6`, phone pick).

## Context
- WASM UI in `web/` (mostly `web/index.html`, plus `web/occt-ops.mjs` and `web/assemblies.mjs`). Work in the Z13 repo (`C:\Dev\cadcam-mvp`).
- This slice keeps the shipped move and typed-resize path and makes two things true on it: a grabbed move handle commits a millimetre translation, and a typed size is the exact millimetre size. It builds on #16 and on the phone pick in #31. It does not replace that path.
- Move drag is `beginGizmoDrag` → `dragGizmo` → `commitGizmoDrag`. A move commit calls `runUndoable('Move', …)` → `translateBody`. `translateBody` calls `moveOwnedShape`. A part with `shapeLocal === true` and a `placement` goes through `assemblyApi.moveLocalPart` (`moveLocalPart` in `web/assemblies.mjs`): the placement changes and the stored solid is the same object. Any other solid, including a Boolean result, goes through `opsApi.transformShape` and bakes the translation into a new shape. `finishMove` records `state.lastMove` (`baked`, `shapeSame`, `placement`, `id`).
- `window.__cadcamGizmoDrag(axis, mm)` only plans a drag. It returns `{ axis, mm, handle, down, up }` from `pickHandle` on the axis shaft. It does not commit. `tests/gizmo_drag_smoke.py` and `MOVE_DRAG_EXPR` in `tests/deploy_smoke.py` fire pointer events from that plan. The commit is still `pointerup` → `commitGizmoDrag`.
- Typed resize is `window.__cadcamResize` → `stageResizeSpec` / `onPrimitiveCommit`. One body with a box, cylinder, or disc calls `commitPrimitiveResize`. Several bodies and a box, cylinder, or disc call `commitSelectedPrimitive`. Digest’s name `commitPrimitiveResize` is the one-body function. The several-body primitive function is `commitSelectedPrimitive`. A body that is not a box, cylinder, or disc calls `commitBBoxResize` (`bboxMode` for one body, `sheetBBoxBody` when several). Both bbox paths call `opsApi.resizeShape`.
- Size fields, all millimetres: box Size X/Y/Z are `#boxSx` / `#boxSy` / `#boxSz`. Cylinder Ø×H is `#cylD` / `#cylH` (`radius * 2` and `height`). Disc Ø×T is `#discD` / `#discT`. A non-primitive Size X/Y/Z is `#bboxX` / `#bboxY` / `#bboxZ`. `fieldMm` / `stageExactMm` / `parseEntry` convert inches at the field only (`MM_PER_IN` is 25.4). Stored values stay millimetres.
- Bounds are `measureBodyBounds` → `opsApi.optimalBounds`. On this tip that is `BRepBndLib.AddOptimal(shape, box, false, false)` (`useTriangulation` false, `useShapeTolerance` false). `prompts/type-in-resize.md` wrote the 3-argument C++ form. The binding here is the 4-argument call already in `optimalBounds`. `window.__cadcamResize` returns those sizes as `dx` / `dy` / `dz`.
- Lock starts ON (`state.lockProportions: true`). `#lockProportions` and `#lockProportionsSide` (`data-action="lockProportions"`) start `aria-pressed="true"`. `paintLock` hides `#ellipseNote` and `#primEllipse` while the lock is on. Off shows the note text `Circles may become ellipses.` `scaleLocked` keeps ratios while the lock is on.
- Unlocked non-primitives use `resizeShape` with `uniform: false`: `gp_GTrsf` and `BRepBuilderAPI_GTransform` (`method` `gtransform`). Locked non-primitives use `uniform: true`: `gp_Trsf.SetScale` and `BRepBuilderAPI_Transform` (`method` `scale`). `research/selection-and-delete.md` had recommended uniform-only for other bodies. The Chief ruling in `prompts/type-in-resize.md` (2026-10-22 04:33 MT) replaced that: unlocked non-primitives are in scope via `BRepBuilderAPI_GTransform`, with the ellipse note, the validity check, and rollback. Follow that ruling.
- A primitive with the lock on rebuilds its parameters (`rebuildResize` / `rebuildOwned`, `method` `rebuild`). One-body lock OFF already calls `resizeShape` with `uniform: false` inside `commitPrimitiveResize`. Several-body lock OFF stays `commitSelectedPrimitive` rebuild. That function’s comment stands: a GTransform of a meshed cylinder kept a scaled triangulation and a stale volume. `multi_body_size_problems` expects `method === 'rebuild'` for the unlocked cylinder. Keep that split.
- `resizeShape` runs `checkOcctShape` (`BRepCheck_Analyzer`). A throw, `forceInvalid`, or a failed check drops the new shape and returns rollback (`kept: true`). `installResized` requires `view.gate.pass === true` and otherwise keeps the previous solid. The hint is the existing “last good shape was kept” line. Do not accept on `view.watertight`.
- Undo is the gizmo-batch stack. `web/undo.mjs` `createCommandStack` is `commandStack` in `web/index.html`. `runUndoable` pushes one `{ label, before, after }` only when the apply function returns true. `doUndo` / `doRedo` install that snapshot. The Chief ruling in `prompts/type-in-resize.md` says to use this stack. Do not build a second one. A rejected resize or move is not a stack entry.
- One selected part among several bodies is `activeEditBody`: `state.selection === 'item'` and exactly one body in `orderedBodies`. `gizmoShouldShow` is false for several bodies unless that part exists and `state.gizmoMode` is `move`. `positionEditable` matches that. `writePosFields` disables `#posX` / `#posY` / `#posZ` when it is false, and sets their title to `Select one part to move it.` `paintPrimFields` hides `#primBox` / `#primCyl` / `#primDisc` / `#primBbox` unless `sheetPrimitive` or `sheetBBoxBody` is that one part. `window.__cadcamPickPart` selects one part.
- Pointers: `viewport` `pointerdown` calls `pickHandle` when `gizmoShouldShow()` and button 0. A hit calls `beginGizmoDrag` and sets `gesture.type` to `gizmo`. `pointermove` then calls `dragGizmo` and returns before the orbit branch. `pointerup` calls `commitGizmoDrag(g.moved)`. `pickHandle` uses `viewApi.pickGizmoHandle` with `gizmoZonePx()` (`GIZMO_TOUCH_ZONE_PX` is 44 in `web/viewport-selection.mjs`). Move deltas go through `threeDeltaToCad` and `snapMm`.
- #31 phone pick stays. `web/phone-select.mjs` `shouldSelect` / `classifyPointer`: movement under `tapSlopPx` (8) is a tap, and a drag does not select. `phoneAims` treats a visible `pickHandle` hit as blocked, so a body tap is aimed off the handle. That aim-past-gizmo search is how phone tests pick a body while the gizmo is up. It must not take a pointer that already grabbed a handle.
- Handle and dimension hit targets are already 44 CSS px: `GIZMO_TOUCH_ZONE_PX`, `.dim-step`, `.dim-panel input`, `.lock-btn`, `.dim-toggle`. Display-only labels (`.dim-label`, the ellipse note) have no hit-target rule.
- `tests/gizmo_drag_smoke.py` loads `/?primitive=box&select=item`. Chromium is a mouse drag at 1440×900. WebKit is an iPhone 13 pointerType `touch` drag at 390×844. Both drag X by `MOVE_MM` (10) through `__cadcamGizmoDrag`. A mid-drag hint of `Orbit`, or “stays put”, fails. The move check is 0.1 mm. Undo and redo use the same stack (0.01 mm). `tests/deploy_smoke.py` `multi_body_size_problems` and `multi_body_move_problems` load `/?demo=assembly` and call `__cadcamResize` through `resize_call`.
- Do not commit `.wasm`, `web/cadcam.wasm`, or `web/dist/`. Do not edit `UPDATES.md`. Do not add or edit a root `PROGRESS.md`. Leave `web/PROGRESS.md` for a separate scrub. Do not edit `research/`.
- Prefer JS, HTML, and CSS, plus the existing libcascade 3.1.0 bindings already used from `web/occt-ops.mjs`. No kernel, C++, `src/`, `web/bindings.cpp`, or `cadcam.wasm` rebuild. If a symbol this keep-path already calls is missing from those bindings, stop and report **TBD**. Do not add a binding. Symbols already called: `BRepBndLib.AddOptimal`, `Bnd_Box`, `BRepCheck_Analyzer`, `BRepPrimAPI_MakeBox`, `BRepPrimAPI_MakeCylinder`, `gp_Trsf.SetScale`, `BRepBuilderAPI_Transform`, `gp_GTrsf`, `BRepBuilderAPI_GTransform`.
- Commit on a PR branch. Never push to main. Repo Keeper merges after `ci.yml` is green.

## Team-chosen behaviour
Keep the shipped move and typed-resize path. A grabbed move handle commits one millimetre translation of the one selected body. Typed Size X/Y/Z or Ø×H / Ø×T apply that exact size in millimetres. One undo step each, on the stack that already exists.

`prompts/type-in-resize.md` is the standing resize rule (AddOptimal, lock ON by default, ellipse note, GTransform for unlocked non-primitives, one undo, millimetres, `BRepCheck_Analyzer` rollback). #16 is the multi-body rule. #31 is the phone-pick rule. This slice does not reopen them.

### T1 — Keep path
Keep `beginGizmoDrag`, `commitGizmoDrag`, `translateBody`, `moveLocalPart`, `window.__cadcamResize`, `commitPrimitiveResize`, `commitBBoxResize`, and the several-body primitive commit `commitSelectedPrimitive`. Units stay millimetres. The accept gate stays OCCT validity plus the millimetre units check, with rollback to the last good shape. Watertight stays dropped.

Do not add C++ unless a libcascade 3.1.0 symbol this path already calls is missing from the prebuilt bindings. Then stop and report **TBD**. Do not rebuild OCCT. Do not add a second undo stack. Use `commandStack` / `runUndoable`.

### T2 — Move-gizmo drag
One selected body. A handle drag commits a millimetre translation. A local primitive updates its placement through `moveLocalPart` (`baked === false`, `shapeSame === true`). A Boolean result bakes through `transformShape` (`baked === true`, `shapeSame === false`). One undo on `commandStack`. Desktop mouse and phone touch both commit.

Orbit, and the #31 aim-past-gizmo pick, must not steal an axis drag once a handle is grabbed. Once `beginGizmoDrag` has set `gesture.type` to `gizmo`, `pointermove` stays on `dragGizmo` and `pointerup` calls `commitGizmoDrag`. The orbit branch and `phoneAims` / `shouldSelect` must not clear that drag or turn it into a camera move or a selection change. A tap that never grabbed a handle still selects as #31 does.

**TBD (do not invent):** whether Erik’s “broken” drag is desktop, phone, or both. Assume both until Pilot repro. `gizmo_drag_smoke.py` already runs Chromium mouse and WebKit touch. Both stay in scope.

The drag delta stays the existing `snapMm` value. Do not turn snap off to make the drag pass.

### T3 — Typed exact resize
Size X/Y/Z (`#boxSx` / `#boxSy` / `#boxSz`, or `#bboxX` / `#bboxY` / `#bboxZ` for a non-primitive), cylinder Ø×H (`#cylD` / `#cylH`), and disc Ø×T (`#discD` / `#discT`) apply the typed millimetres. `optimalBounds` (AddOptimal, the 4-argument call above) reads the applied size within **0.01** mm. `__cadcamResize` returns those sizes as `dx` / `dy` / `dz`.

Lock stays ON by default. ON keeps ratios through `scaleLocked` (a locked non-primitive is uniform `scale`). OFF shows `Circles may become ellipses.` on `#ellipseNote` and `#primEllipse`. OFF on a non-primitive uses `BRepBuilderAPI_GTransform` (`resizeShape` with `uniform: false`). One successful resize is one `runUndoable('Resize', …)` step. A failed analyzer or a throw rolls back and does not push.

Inch display still converts only in `parseEntry` / `formatEntry`. Typing a value and switching back to millimetres must not drift and must not multiply a stored value by 25.4.

Keep the primitive split in the Context section. Several-body primitives stay `commitSelectedPrimitive` rebuild, including lock OFF. Do not move that path onto GTransform.

### T4 — Multi-body stay (#16)
Only the selected part moves or resizes. Other parts keep their placement and their sizes. None selected, or several selected: the gizmo stays hidden (`gizmoShouldShow` false) and the position fields stay disabled (`#posX` / `#posY` / `#posZ`, title `Select one part to move it.`). Size groups for a part that is not the single selection stay hidden (`paintPrimFields`). Do not add a second disable flag. `window.__cadcamPickPart` remains the way a test selects one part.

### T5 — Targets and tests
Move handles and dimension controls stay at least **44 CSS px** (`GIZMO_TOUCH_ZONE_PX`, `.dim-step`, `.dim-panel input`, `.lock-btn`). Display-only note text has no hit-target rule.

These stay green: `tests/gizmo_drag_smoke.py` (mouse and touch), `tests/deploy_smoke.py` `multi_body_size_problems` and `multi_body_move_problems`, and the existing `window.__cadcamResize` cases those functions call.

### T6 — Out
- P1–P5. Do not reopen selection overlays, the P2 digest, shaders, shelves, Measure, callouts, or sketch.
- Gestures #21, #22, and #24. View-cube swipe, three-finger undo, and field-nudge swipe stay as they are. A second finger that already cancels a gizmo drag for pinch stays that pinch. Do not retune it.
- Sketch. Do not redo face sketch, origin planes, Extrude New/Join/Cut, sketch callouts, or the line tool.
- Rotate and scale feature work. `data-action="gizmoMode"` rotate and scale stay as they are. A pointer-path change is allowed only so a **move** handle drag commits. Do not add rotate or scale behaviour.

## Acceptance
- T1. The move still enters through `beginGizmoDrag` / `commitGizmoDrag` / `translateBody` / `moveLocalPart`. The resize still enters through `__cadcamResize` and `commitPrimitiveResize`, `commitSelectedPrimitive`, or `commitBBoxResize`. No new `window.__cadcam*` hook. No second undo stack. No `src/` or `web/bindings.cpp` diff. A missing libcascade symbol stops the slice. Watertight stays dropped. A rejected op keeps the last good shape and does not push `commandStack`.
- T2. One selected box. `__cadcamGizmoDrag('x', 10)` then the pointer sequence in `gizmo_drag_smoke.py`. Desktop mouse and phone touch each move `cx` by 10 mm within the smoke’s 0.1 mm check, leave `cy` and `cz`, set `undoDepth` to 1, and keep `gateOcct === 'PASS'`. The mid-drag hint is not `Orbit` and does not say the solid stays put. One undo restores the origin within 0.01 mm. On `/?demo=assembly`, one selected cylinder drag keeps `lastMove.baked === false` and `shapeSame === true` and moves only that placement. The Boolean union move keeps `baked === true` and `shapeSame === false` and does not move the other part. Assume desktop and phone are both in scope until Pilot says which one Erik hit.
- T3. Lock starts ON (`aria-pressed="true"`, ellipse notes hidden). A 20 mm box typed to Size X 30 mm with the lock on becomes 30×30×30. `__cadcamResize` `dx` / `dy` / `dz` (AddOptimal) match within 0.01. One undo restores 20×20×20 and is one stack step. Lock OFF shows `Circles may become ellipses.` A non-primitive unlocked resize reports `method === 'gtransform'`. A locked non-primitive reports `method === 'scale'`. A several-body cylinder typed to diameter 30 mm with the lock off stays `method === 'rebuild'`, radius 15, height 20, and the other body unchanged. Switching the UI to inches, typing, and switching back does not change the stored millimetres and does not apply 25.4 twice. `forceInvalid` rolls back, `rolledBack === true`, and `undoDepth` does not increase.
- T4. `/?demo=assembly` with both parts selected: `gizmoVisible === false`, `#posX` disabled, title contains `Select one part`. Size groups stay hidden. After `__cadcamPickPart` on one part, only that part’s fields show, and a resize or move does not change the other part’s size or placement.
- T5. At 390×844 and at desktop width, a visible move handle’s pick zone and the visible size inputs, steppers, and lock button are each at least 44 CSS px. `gizmo_drag_smoke.py`, `multi_body_size_problems`, `multi_body_move_problems`, and the `__cadcamResize` cases they already run pass.
- T6. View-cube swipe, three-finger undo, and field nudge behave as on main. Sketch, Measure, Extrude New/Join/Cut, and Modify Union / Cut / Intersect plus fillet behave as on main. Rotate and scale commits behave as on main.

## Tests
Extend the smoke that already exists. Do not add a new smoke file or a new harness. Do not retarget unrelated hooks.

- `tests/gizmo_drag_smoke.py` stays the T2 drag. Chromium mouse and WebKit touch both stay. Do not drop either while the desktop-versus-phone TBD is open. The 10 mm X move, the `Orbit` / “stays put” mid-drag fail, `undoDepth === 1`, `gateOcct === 'PASS'`, and undo/redo on `commandStack` stay.
- `multi_body_size_problems` and `multi_body_move_problems` in `tests/deploy_smoke.py` stay the T3 and T4 checks, including both-selected gizmo hidden and position fields disabled, `__cadcamPickPart`, lock-on rebuild, lock-off cylinder rebuild with the ellipse note, union `method === 'scale'`, primitive `moveLocalPart` (`baked === false`), and Boolean bake (`baked === true`). One undo per successful resize or move.
- AddOptimal within 0.01 is the `dx` / `dy` / `dz` already returned by `__cadcamResize` (`optimalBounds`). If a current assert checks only `params` and not those bounds, add the bounds assert beside that `resize_call`. Do not add a new tolerance helper. `_near` in `deploy_smoke.py` already defaults to 0.01.
- Leave `phone_select_smoke.py`, `view_cube_swipe_smoke.py`, `three_finger_smoke.py`, `field_nudge_smoke.py`, and `edge_fillet_smoke.py` passing. Do not retarget them. Do not add a CTest name.

## Out of scope
- Reopening P1–P5. Selection-overlay, shader, shelf, Measure, callout, or sketch retune.
- Sketch redo, including origin planes, Extrude Join/Cut, and the line tool.
- View-cube swipe, three-finger undo/redo, and field-nudge swipe (#21, #22, #24).
- Rotate or scale feature work beyond a pointer-path fix that lets **move** drag commit.
- A second undo stack. A new `window.__cadcam*` hook. A new smoke file.
- Turning snap off. Changing `tapSlopPx`. Rebuilding watertight into the accept gate.
- A kernel, C++, `src/`, `web/bindings.cpp`, or WASM rebuild. `.wasm` and `web/dist/`.
- `UPDATES.md`, `web/PROGRESS.md`, a root `PROGRESS.md`, and `research/`.
- Inventing which of desktop or phone Erik’s broken drag was. Assume both until Pilot repro.

## Done
`ci.yml` green on the PR (a docs-only diff may skip the native build; a code diff runs the build). This prompt PR stays draft until Research Digest tip-matches (primary). Doc Steward is the author and does not self-APPROVE. Repo Keeper undrafts and plain-merges. Report the PR link and the tip SHA.
