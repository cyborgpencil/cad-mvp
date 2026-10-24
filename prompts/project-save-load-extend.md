# Save/load: BREP-only round-trip after P6

Team-chosen and authored by Doc Steward, 2026-10-24 (America/Denver). Locks T1–T6 are 3T final, 2026-10-24 (America/Denver). They come from `research/gui/save-load-roundtrip.md` and are final. That note is on tip `a1c0d93` (PR #100; base main was `4163538`) and is on main via #100 (merge `0c4c220`). This prompt was written on main `c5af8ba` (#101 is the UPDATES line for #100). App facts were checked at `a1c0d93`. Nothing under `web/` changed between that tip and `c5af8ba`. Feed this to Grok Build / Cursor. This file is the spec. It does not change the app.

Units: **mm**. Volume: **mm³**. Gate: OCCT validity + units (watertight dropped, 02:17 rule). Do not reopen P1–P6. Keep v1 / mm / existing FS `BRepTools.Write` / `Read`. No WASM rebuild. No format v2. Closed on main: P6 #98 (`56c2528`), UPDATES #99 (`4163538`). Origin-plane, Extrude Join/Cut, and touch Booleans + fillet stay closed.

## Context
- WASM UI in `web/` (`web/project-file.mjs`, `web/index.html`, `web/assemblies.mjs`, `web/occt-gate.mjs`). Work in the Z13 repo (`C:\Dev\cadcam-mvp`).
- `.cadmvp` is on main via #2 (`c08ef3d`). The older prompt `prompts/project-save-load.md` said load rebuilds from the parameters and, if that fails, falls back to the BREP. Its Pilot section also said to add `BRepTools::Write` / `Read` through a `std::stringstream` binding. **This prompt replaces both of those instructions.** Boolean, fillet, and sketch→extrude bodies reload BREP-only: the part’s `primitive` is null, the reloaded body’s `params` is null, and there is no feature rebuild. Keep the existing temp-file FS path (`writeBrepText` / `readBrepText`). Do not add a `std::stringstream` binding. Do not rebuild WASM to add one.
- `state.primitive` in `web/index.html` is the edit sheet. `applyLoadedProject` already sets that sheet to null. The lock’s “null `primitive`” is the `.cadmvp` part field and the reloaded body’s `params`, so `rebuildShape` cannot rebuild that solid. `source` on that solid is `'brep'`.
- Format is version **1**, units **`mm`**, extension `.cadmvp` (`PROJECT_VERSION`, `PROJECT_UNITS`, `PROJECT_EXTENSION` in `web/project-file.mjs`). `parseProject` rejects a version other than 1 with `ERR_VERSION` (`'This file version is not supported. The model was not changed.'`). Wrong or missing units use `ERR_UNITS`. Empty text uses `ERR_EMPTY`. Unreadable JSON uses `ERR_READ`. A failed shape check uses `ERR_SHAPE`. Each of those says the model was not changed.
- Shape text is `BRepTools.Write` / `BRepTools.Read` through the Emscripten FS. `writeBrepText` writes a temp file (`/cadmvp-brep-N.brep`), reads the text back, and deletes the file. `readBrepText` does the reverse. The file comment on `web/project-file.mjs` stands: the `std::ostream` / `std::istream` overloads are not in the symbol map, and a `std::stringstream` wrapper cannot be compiled here. Leave that path as it is.
- Volume is `BRepGProp.VolumeProperties` → `Mass()`. Bounds are `BRepBndLib.AddOptimal` (`useTriangulation` false, `useShapeTolerance` false). `measureShape` returns `{ volumeMm3, bounds }` with `xmin` / `ymin` / `zmin` / `xmax` / `ymax` / `zmax`. Tolerance for this slice is **0.01** (`Math.abs(a - b) <= 0.01`), the same `near()` `SAVELOAD_EXPR` already uses.
- `partFromBody` writes `primitive: { kind, parameters }` only when `body.kind` and `body.params` are both set. Otherwise the part field is `null`. Union and Cut already store `kind: 'boolean'` and `params: null` (`applySceneBoolean`), so the saved primitive is already null. Sketch→extrude New (`commitSketchExtrude`) and Join/Cut extrude (`installExtrudeOnBody`) store `kind: 'extrude'` and a params object, so the file currently gets `{ kind: 'extrude', parameters }` and reload keeps that object with `source: 'brep'`. This slice changes save (`partFromBody` and/or its callers) and/or load so those bodies **persist and reload** with null `primitive`, null body `params`, and `source: 'brep'`.
- `rebuildShape` returns null when there is no primitive, when `part.features` is non-empty, or when `kind` is not `box`, `cylinder`, or `disc`. `loadShapes` keeps a parameter rebuild only when `rebuildShape` returns a shape and `checkOcctShape(...).pass === true` (`source: 'parameters'`). Otherwise it reads the BREP text, requires the same `pass === true`, and sets `source: 'brep'`. When `primitive` is null, `kind` becomes `'brep'` and `params` stays null. A failed read or a failed check aborts the load with `ERR_SHAPE`. Do not change `checkOcctShape` (`web/occt-gate.mjs`: `BRepCheck_Analyzer.IsValid()` and zero free edges).
- Fillet and chamfer do not clear `kind` or `params` (`web/index.html`, the edge-op apply that assigns `body.shape` and then appends features). When `result.featureFaces` is non-empty it appends `{ kind, faces }` onto `body.features`. Non-empty `features` already makes `rebuildShape` return null, but the old primitive’s kind and params stay on the part and on the reloaded body. If no feature faces were stored, `rebuildShape` can still rebuild the box, cylinder, or disc. Fillet shares the null-primitive rule. Do not invent a new fillet marker for the empty-features case. No separate fillet smoke.
- Box, cylinder, and disc still reload with `source: 'parameters'` when `kind` and `params` are set and `features` is empty. `rebuildShape` already handles those three kinds. The live pair in `SAVELOAD_EXPR` is box + cylinder (`preparePair`). Disc uses that same rebuild branch. Do not drop the parameters path for those three.
- Materials the file can carry are the part `material` string. `web/assemblies.mjs`: `MATERIALS` is `PLA`, `PETG`, `TPU`. `materialTag` maps a missing tag or `"default"` to PLA. `MATERIAL_COLOR` is PLA `#F4F4F4`, PETG `#B9D6F2`, TPU `#E7C36A`. `partFromBody` stores `body.material`, or `DEFAULT_MATERIAL` (`'default'`) when that string is empty. `makeOwned` stores `material: 'PLA'`. `#partMaterial` writes `PLA`, `PETG`, or `TPU` onto the selected bodies. `checkPart` requires `material` to be a string; a missing material key is `ERR_READ`, not a successful PLA load. `multi_body_color_problems` already asserts the PETG and TPU colours. Leave that check. This slice asserts the tags survive save/load.
- `window.__cadcamProject` is the save/load hook: `preparePair`, `saveText`, `loadText(text, confirm)`, `measures`, `unit`, `dirty`, `setDirty`. `measures()` today returns `name`, `volumeMm3`, `bounds`, and `source` only. It does not return `params` or `material`. Extend that same row with the reloaded body’s `params` (null or the object) so the smoke can see null. Read `primitive` from `JSON.parse(saveText().text).parts`. Do not add a second project hook.
- `boolean_unique_names_problems` loads `?pair=overlap`, cuts twice, and already checks that `Cut 1` and `Cut 2` survive `saveText` / `loadText`. `overlap_boolean_problems` runs Union, Cut, and Intersect on that pair and undoes Union. `union_undo_problems` requires the overlap Union scene volume at 12000 mm³ (`BOOLEAN_MM3_TOL` 1e-3). `expectedOverlapVolumes` in `web/occt-ops.mjs` is two 20 mm boxes, the second shifted +10 mm on X: union 12000, cut 4000, intersect 4000. Do not retarget `overlap_boolean_problems` or that undo check.
- `portrait_origin_plane_problems` already builds one New extrude: Top (`xy`), rectangle `#sketchL` / `#sketchW` 10, `#sketchConfirm`, Extrude (Push/Pull) on New, `#sketchDepth` 10, `#sketchConfirm` (`commitSketchExtrude`). `assertSolid('rect', 1000)` expects one body, kind `extrude`, volume 1000 mm³ (tolerance 0.5), mesh bounds about 0..10 (tolerance 0.05). That function does not save. Do not retarget it. The round-trip in this slice uses `measureShape` within 0.01.
- `tests/phone_smoke.py` already calls `deploy_smoke.run_saveload`. It does not call `boolean_unique_names_problems`. Do not add a phone-only probe.
- Do not commit `.wasm`, `web/cadcam.wasm`, or `web/dist/`. Do not edit `UPDATES.md`. Do not add or edit a root `PROGRESS.md`. Leave `web/PROGRESS.md` for a separate scrub. Do not edit `research/`.
- Prefer JS in `web/project-file.mjs`, a minimal `web/index.html` change (the `measures()` row, and only the save/load caller if the part has to be written null from there), and `tests/deploy_smoke.py`. No kernel, C++, `src/`, `web/bindings.cpp`, or `cadcam.wasm` rebuild.
- Commit on a PR branch. Never push to main. Repo Keeper merges after `ci.yml` is green.

## Team-chosen behaviour
`prompts/project-save-load.md` said load rebuilds from parameters first, and it suggested a `std::stringstream` binding. **This prompt replaces both.** Boolean, fillet, and sketch→extrude bodies reload as solids with null `primitive` and no feature rebuild. Keep `writeBrepText` / `readBrepText`. Do not add a `std::stringstream` binding.

Union and Cut already save `primitive: null` because `params` is null. Sketch→extrude currently saves `{ kind: 'extrude', parameters }`, and reload keeps those parameters with `source: 'brep'`. The lock needs null `primitive` **and** null body `params` on reload for Union, Cut, and sketch→extrude, so `rebuildShape` cannot rebuild. Adjust save (`partFromBody` / callers) and/or load so the **file** persists `primitive: null` and the reload stores null `params` and `source: 'brep'`. Write that null on the part. Do not clear the live body’s `params` just to make `partFromBody` skip the primitive. Box, cylinder, and disc still reload with `source: 'parameters'`.

Measure with the existing `measureShape` (volume and AddOptimal bounds) within **0.01**. Names stay `part.name`. `checkOcctShape` must pass or the load returns `ERR_SHAPE`. When `primitive` is null, `loadShapes` sets `kind` to `'brep'`. Do not keep an `extrude` primitive just to preserve `kind`.

### T1 — Format
Keep version **1**, units **`mm`**, and the existing FS `BRepTools.Write` / `BRepTools.Read` path in `web/project-file.mjs` (`writeBrepText`, `readBrepText`, temp file, then delete). `PROJECT_VERSION` stays 1. `PROJECT_UNITS` stays `'mm'`. `PROJECT_EXTENSION` stays `.cadmvp`.

No WASM rebuild. No format v2. No new top-level field. `features` stays an array on the part. Do not add a `std::stringstream` binding, and do not switch Write/Read off the file-path overloads the prebuild already exports.

`parseProject` still rejects a version other than 1, units other than `mm`, empty text, unreadable JSON, and a part that fails `checkPart`.

### T2 — Boolean
Union and Cut results round-trip BREP-only. The saved part’s `primitive` is null. After `loadText`, `measures()` reports `source === 'brep'` and `params === null` on that body. Volume and AddOptimal bounds match the pre-save `measureShape` within **0.01** (mm³ and mm). Names are kept (`uniqueOpName`: `Union 1`, `Cut 1`, and the `Cut 2` the name smoke already builds).

`checkOcctShape` passes: a successful `loadText` is that check inside `loadShapes`. A failed check still returns `ERR_SHAPE` and leaves the previous model unchanged.

Build them the way the overlap pair already works (`?pair=overlap`, two 20 mm boxes, second shifted +10 mm on X). `expectedOverlapVolumes` is union 12000 mm³ and cut 4000 mm³. `union_undo_problems` already requires 12000 mm³ at 1e-3. This slice’s compare is still before versus after at 0.01. Intersect already saves `primitive: null` because its `params` is null. Do not add an Intersect smoke. Do not change `overlap_boolean_problems`.

### T3 — Materials
PETG, TPU, and PLA-default tags survive save/load.

`MATERIALS` stays `PLA`, `PETG`, `TPU`. `materialTag` stays: a missing tag or `"default"` reads as PLA; PETG and TPU stay those strings. Do not change `MATERIAL_COLOR` or `materialColor`. PETG `#B9D6F2` and TPU `#E7C36A` stay asserted in `multi_body_color_problems`. Do not retarget that function.

Set PETG and TPU with the `#partMaterial` change listener. A body `makeOwned` created stays `PLA`. After save and load, the file part’s `material` and the reloaded body are those strings. `window.__cadcamPartColor` uses `materialTag`: its `tag` is `PETG`, `TPU`, or `PLA` for those bodies.

`partFromBody` still writes `DEFAULT_MATERIAL` (`'default'`) when `body.material` is empty. A part whose material string is `'default'` still loads. The stored string stays `'default'`. `materialTag` / `__cadcamPartColor.tag` still reads PLA. Do not treat a missing `material` key as success. `checkPart` returns null for that part, and `parseProject` still returns `ERR_READ`.

### T4 — Sketch→extrude
One extruded solid round-trips BREP-only. Same shared null-primitive rule as Boolean. The saved part’s `primitive` is null, not `{ kind: 'extrude', parameters }`. After load, `source` is `'brep'` and body `params` is null. Volume and AddOptimal bounds match the pre-save `measureShape` within **0.01**.

Use one New body: the solid `portrait_origin_plane_problems` already builds (Top `xy`, rectangle 10 by 10, Blind 10 mm, Extrude New, `commitSketchExtrude`). That portrait check expects about 1000 mm³. The save/load check is `measureShape` before versus after within 0.01. Do not change the portrait tolerance (volume 0.5, mesh bounds 0.05) or its `kind === 'extrude'` assert, which runs before any save.

`installExtrudeOnBody` (Join / Cut extrude) also sets `kind: 'extrude'` and a params object. Those bodies use this same save/load rule. Do not add a separate Join or Cut extrude smoke. Do not retune Extrude Join/Cut.

Fillet and chamfer use this same rule when `body.features` has a fillet or chamfer entry: saved `primitive` null, reloaded `params` null, `source: 'brep'`. If no feature faces were stored, the body is still box, cylinder, or disc and stays on the parameters path. Do not invent a marker for that case. No fillet smoke in this slice.

### T5 — Keep
Keep the current `SAVELOAD_EXPR` behaviour.

- `preparePair` (box + cylinder), save, `units === 'mm'`, `version === 1`.
- Reload: each of those parts `source === 'parameters'`, volume and `xmin` / `ymin` / `zmin` / `xmax` / `ymax` / `zmax` within 0.01. The box volume check stays 8000.
- Display switched to inches (`[data-action="units"][data-unit="in"]`), save again, file `units` still `mm`, load, display unit still `in`, volumes still within 0.01.
- `clearProjectUndo` / `window.__cadcamClearUndo` once per accepted load. Undo and redo depth 0 after load. Cancel (`loadText(..., false)`) does not call clear.
- Corrupt JSON, empty, blank, `"units": "in"`, and missing `units` leave the model and the dirty flag untouched (`unchanged === true`, `ok === false`).

Box and cylinder stay `source: 'parameters'`. Disc stays on that same `rebuildShape` path when its kind and params are set and `features` is empty. Do not add a disc case to the pair.

Add the missing version-2 bad-file case. `research/project-save-load.md` P7 asks for a file with version 2. `parseProject` already returns `ERR_VERSION` when `version !== 1`. Copy a saved document, set `version` to 2, `loadText` it, and use the same unchanged-model check as the other bad files. Clear is not called. Do not drop the existing bad-file cases.

### T6 — Out
- No feature rebuild and no parametric replay. `rebuildShape` returns null for Boolean, fillet/chamfer-with-features, and sketch→extrude, so `loadShapes` reads the BREP.
- View-cube swipe stays next (`research/touch-gestures.md`). Do not implement it here.
- Do not reopen P1–P6. Origin-plane, Extrude Join/Cut, and touch Booleans + fillet stay closed.
- No format v2. No `std::stringstream` binding. No kernel, C++, `src/`, `web/bindings.cpp`, or WASM change.
- No new smoke file and no new harness. No Intersect round-trip case. No separate fillet smoke. No Join/Cut extrude smoke.

## Acceptance
- T1. A saved document from `window.__cadcamProject.saveText()` has `units === 'mm'`, `version === 1`, and one part per body. Shape text still round-trips through `writeBrepText` / `readBrepText` (the FS temp file). No new binding, no WASM, no version 2 writer. `parseProject` still rejects version 2 with `ERR_VERSION`.
- T2. One Union and one Cut of the overlap pair: the saved part’s `primitive` is null; after `loadText`, `measures()` has `source === 'brep'` and `params === null`; volume and AddOptimal bounds are within 0.01 of the pre-save `measureShape`. That Union is the 12000 mm³ body `union_undo_problems` already checks. That Cut is the 4000 mm³ body from `expectedOverlapVolumes` (first box minus the overlap). The two-cut scene in `boolean_unique_names_problems` keeps `Cut 1` and `Cut 2` and matches its own pre-save `measureShape` within 0.01; do not expect that scene to be a single 4000 mm³ body. `loadText` returns `ok === true` (`checkOcctShape` passed). `overlap_boolean_problems` still passes, including Union undo back to two 8000 mm³ boxes.
- T3. After `#partMaterial` sets PETG and TPU, and a `makeOwned` body stays PLA, save/load keeps those strings on the part and on the body. `__cadcamPartColor.tag` is `PETG`, `TPU`, or `PLA`. A part material of `'default'` loads, the stored string stays `'default'`, and `__cadcamPartColor.tag` is PLA. `multi_body_color_problems` still passes (PETG `#B9D6F2`, TPU `#E7C36A`). `MATERIALS` and `materialTag` are unchanged.
- T4. One New extrude (10×10 rectangle, Blind 10 mm) saves with `primitive: null`. After load, `source === 'brep'`, `params === null`, and volume and AddOptimal bounds are within 0.01 of the pre-save `measureShape`. `portrait_origin_plane_problems` still passes, including its pre-save kind `extrude` and volume ~1000 mm³. Fillet has no new smoke. Join/Cut extrude has no new smoke. A box, cylinder, or disc with empty `features` is not forced onto the BREP path.
- T5. `SAVELOAD_EXPR` still passes: box + cylinder `source === 'parameters'`, box volume 8000, bounds within 0.01, inch display with file units `mm` and no volume drift, `clearUndo` once per accepted load and not on cancel, undo/redo depth 0, and the existing bad files (corrupt, empty, blank, `"units": "in"`, missing `units`) leave the model and the dirty flag untouched. Version 2 is the same kind of unchanged failure, with `ERR_VERSION`, and does not call clear.
- T6. No feature rebuild, no view-cube swipe, no format v2, no `std::stringstream` binding, no kernel or WASM diff. Origin-plane, Extrude New / Join / Cut, and Modify Union / Cut / Intersect plus fillet/chamfer behave as on main aside from the null-primitive save/load rule above. The accept gate is still OCCT validity + mm. Watertight stays dropped.

## Tests
Extend the smoke that already exists. Do not add a new smoke file or a new harness. Do not retarget unrelated hooks.

- `tests/deploy_smoke.py` `SAVELOAD_EXPR` / `run_saveload` already drives `window.__cadcamProject` (`preparePair`, `saveText`, `loadText`, `measures`). Keep the box + cylinder `source === 'parameters'` loop. Extend this expression for the material tags, the one-extrude round-trip, and the version-2 bad file. `measures()` has to grow a `params` field on the row it already returns. Do not add a second hook.
- Union and Cut volume, bounds, `source`, and null `primitive` go in `SAVELOAD_EXPR` or in `boolean_unique_names_problems` (it already save/loads Cut names on `?pair=overlap`). One of those, not a new function. If they live only in `boolean_unique_names_problems`, leave `run_saveload` as the phone path. Do not drop `Cut 1` / `Cut 2`.
- `tests/phone_smoke.py` already calls `deploy_smoke.run_saveload`. Do not add a phone-only save/load probe. A check that must run on the phone belongs in `SAVELOAD_EXPR`.
- Leave `overlap_boolean_problems`, `union_undo_problems`, `portrait_origin_plane_problems`, `multi_body_color_problems`, and `SAVELOAD_BUTTONS_EXPR` passing. Do not retarget them.
- `hook.measures()` in `SAVELOAD_EXPR` is this project measure. The new `source === 'brep'` rows must not replace the `source === 'parameters'` check on the box + cylinder pair.

## Out of scope
- Reopening P1–P6. Origin-plane empty-doc. Extrude Join/Cut retune, including a new Join or Cut extrude smoke. Touch Booleans and fillet/chamfer retune. A fillet smoke.
- An Intersect round-trip case. `overlap_boolean_problems` already runs Intersect.
- Feature rebuild, a parametric history, or a second shape path beside `measureShape` / `rebuildShape` / `readBrepText`.
- Format v2. A `std::stringstream` binding. A kernel, C++, `src/`, `web/bindings.cpp`, or WASM rebuild. A change to `checkOcctShape` or the watertight gate.
- A new disc case on the box + cylinder pair. A new smoke file. A new harness. A new `window.__cadcamProject` method.
- View-cube swipe (`research/touch-gestures.md`).
- `UPDATES.md`, `web/PROGRESS.md`, a root `PROGRESS.md`, and `research/`.

## Done
`ci.yml` green on the PR (a docs-only diff may skip the native build; a code diff runs the build). This prompt PR stays draft until Research Digest tip-matches (primary). Doc Steward is second if needed. The author does not self-APPROVE. Repo Keeper undrafts and plain-merges. Report the PR link and the tip SHA.
