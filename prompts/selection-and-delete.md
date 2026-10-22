# Selection and delete (queue: after type-in-resize)
Let the user delete a solid, a face, or an edge/vertex's owning feature. Print DELETE_DONE.

## Behaviour (chief rulings)
- Whole solid: deleted via a trash icon or the Del key (skip when focus is in an input).
- Face: remove with BRepAlgoAPI_Defeaturing (SetToFillHistory true). Treat IsDone false, HasErrors, or warning AlertUnableToRemoveTheFeature as failure; on failure the model is unchanged and the user sees an error.
- Edge / vertex: deletes its owning fillet, chamfer or feature (defeature that feature's faces). If none, show exactly: "Can't delete this edge on its own."
- BRepCheck_Analyzer after every delete; invalid -> roll back to the last good shape.
- Each delete = exactly one undo step.

## Selection: what exists vs what to add
- Exists: mode buttons Vertex/Edge/Face/Item (data-action="select", hotkeys 1-4), state.selection / state.selectedIds, web/selection.mjs (SELECTION_MODES, occtShapeType, applyPointerSelection, PICK/TOUCH tolerances, groupMeshFaces), overlays in viewport-selection.mjs.
- Verify and add as needed: picking that maps a tap/click to a real OCCT sub-shape (TopExp_Explorer / TopTools_IndexedMapOfShape index for face, edge, vertex), not only mesh groups; highlight of the picked sub-shape; a trash icon (none exists today); Del key binding.
- Add an op history map: fillet/chamfer op -> generated faces (from BRepFilletAPI Generated/Modified in occt-ops.mjs) so edge/vertex delete can find its owner.

## OCCT symbols to verify in libcascade 3.1.0
BRepAlgoAPI_Defeaturing (SetShape, AddFaceToRemove, SetToFillHistory, Build, IsDone, HasErrors, HasWarnings, Shape, Modified/IsDeleted), BRepCheck_Analyzer, TopExp_Explorer, TopTools_IndexedMapOfShape, TopExp.MapShapes, BRepFilletAPI_MakeFillet/MakeChamfer Generated. Defeaturing is the most likely gap: if absent, stop and report.

## Smoke tests (deploy_smoke + phone_smoke, via window test hook)
- Delete a box (trash and Del): body gone; one undo restores it.
- Defeature a face on a fixture (e.g. hole in a box from tests/fixtures): result valid, face count drops. A failing face delete leaves the model unchanged.
- Edge with no owning feature: message is exactly "Can't delete this edge on its own." and model unchanged.
- Edge on a fillet: the fillet is removed, result valid.

## TBD (do not invent)
- Undo/redo is not implemented (buttons only setHint); depends on the undo stack from type-in-resize.
- Trash icon placement on phone (top row vs bottom sheet) and 44 px target: TBD, chief to rule.
- Which fixture to use for face defeature: TBD (pick an existing tests/fixtures file; no Blink bracket shipped).
- Vertex owning feature rule (vertex shared by several features): TBD.
- Exact error text for failed face delete: TBD.

## Rules for every session (Pilot conventions)
- Work in a fresh clone on a PR branch off main. Never push to main. Done = ci.yml green on the PR, then Repo Keeper merges.
- Any C++ or bindings change (web/bindings.cpp, src/) goes in its own commit, flagged for Erik review.
- Before coding, verify every OCCT symbol below exists in the prebuilt libcascade 3.1.0 (opencascade_single.wasm) as used by web/occt-ops.mjs. If one is missing, stop and report; do not rebuild OCCT.
- Tests go in tests/deploy_smoke.py and tests/phone_smoke.py through a window test hook (pattern: window.__cadcam*). Chromium 390x844 in CI; WebKit via phone_smoke.
- No watertight requirement (dropped by Erik). OCCT validity check (BRepCheck_Analyzer) after every op and an mm units check are required.
- Strict MVP scope. Defaults are team choices recorded in web/PROGRESS.md DECISIONS log. Invent no specs; gaps are TBD.

## Chief rulings (2026-10-22 04:33 MT; replace any TBD above)
- Undo/redo: built by Pilot's gizmo batch (a command stack holding before and after shape snapshots). This prompt launches only after that is on main; use that stack and don't build your own.
- Unlocked resize of non-primitive bodies is in scope via BRepBuilderAPI_GTransform. Show the ellipse note, and run the validity check with rollback after every resize. Lock stays on by default.
- Trash icon: in the property sheet header, at least 44 px, shown only when something is selected (phone and desktop). On desktop the Del key also deletes.
- Face-delete fixture is built in the test, not from Blink: a 40x20x10 mm box with a 6 mm through-hole. Deleting the hole's wall face brings the volume back to the plain box's value within 0.01 and passes the validity check. As the failure case, deleting a box face leaves the model unchanged with a clean error.
