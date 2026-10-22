# Type-in resize (queue: before selection-and-delete)
Let the user resize a body by typing sizes in the property panel. Print RESIZE_DONE.

## Behaviour (chief rulings)
- Primitives edit their own parameters and rebuild: box L x W x H, cylinder diameter x H, disc diameter x thickness.
- Any other body shows its bounding box X / Y / Z and resizes to the typed values.
- Lock proportions toggle, ON by default. When OFF, show the note: circles may become ellipses.
- Measure bbox with BRepBndLib::AddOptimal(shape, box, useTriangulation=false).
- Each resize = exactly one undo step.
- Units are always mm internally. Inch UI converts at display only (MM_PER_IN in web/index.html); typing then reading back must not drift and must never apply 25.4x to a stored value.
- Run BRepCheck_Analyzer on the result; if invalid or the op throws, roll back to the last good shape (follow the "last good shape was kept" pattern in web/occt-ops.mjs).

## Existing hooks to reuse
- Property panel / #primNote ("Dimensions for a box, cylinder, or disc open on the model"), data-mm fields, units buttons (data-action="units").
- Gizmo scale mode (data-action="gizmoMode" data-mode="scale"), viewport-selection.mjs MIN_SIZE_MM, STEPPER_MM, STEPPER_FINE_MM.
- occt-ops.mjs already uses BRepPrimAPI_MakeBox and BRepBuilderAPI_Transform.

## OCCT symbols to verify in libcascade 3.1.0
BRepBndLib.AddOptimal, Bnd_Box, BRepCheck_Analyzer, BRepPrimAPI_MakeBox, BRepPrimAPI_MakeCylinder, gp_Trsf.SetScale, BRepBuilderAPI_Transform, gp_GTrsf, BRepBuilderAPI_GTransform (unlocked non-uniform path).

## Smoke tests (deploy_smoke + phone_smoke, via window test hook)
- Set a box to 30 mm on one side: AddOptimal bbox reads 30 mm within 0.01 mm.
- One resize then one undo restores the previous size (one undo step).
- Switch to inches, type a value, switch back: stored mm unchanged (no drift, no 25.4x).
- Lock ON keeps ratios; lock OFF shows the ellipse note.
- Result passes BRepCheck_Analyzer; forced-invalid case rolls back.

## TBD (do not invent)
- Undo/redo is not implemented yet: the undo/redo buttons only call setHint. A minimal undo stack is a prerequisite; TBD whether this batch or a separate item builds it (chief to rule).
- Non-primitive bodies with lock OFF: research recommended uniform-only for MVP (GTransform changes geometry types). Chief ruled the note instead; confirm GTransform is allowed.
- Disc vs cylinder: confirm disc is a cylinder primitive with its own label/params in occt-primitives.mjs.
- Tolerance for inch round-trip check: TBD (suggest exact mm equality of stored value).

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
