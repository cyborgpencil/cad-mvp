# Item 4: Assemblies (flat parts list, Combine, per-part 3MF)
Add a flat list of separate parts to the app, a Combine command that fuses selected parts, and a 3MF export with one object per part and its material. Scope is exactly the Chief ruling of 02:21 MT: a flat parts list, one solid per part, a placement in mm and a material tag, Combine fuses the selected parts into a new part, no mates or joints, and export writes one 3MF object per part with its material. Source: research/assemblies.md. Print ASSEMBLIES_DONE.

## Rules for every session
- Work in a fresh clone on a PR branch off the latest main. Never push to main. Any C++ or bindings change goes in its own commit and is flagged for Erik review.
- Touch first: targets at least 44x44 CSS px. Test in portrait at 390x844: Chromium in CI; WebKit via tests/phone_smoke.py (Playwright, iPhone 13 profile; exits 77 skip in CI when Playwright is missing, keep that). Add new checks to both deploy_smoke and phone_smoke.
- Every default is a team choice recorded in web/PROGRESS.md. Invent no Erik specs.
- The Blink bracket is a test fixture only: never shipped, never pushed.
- Units stay mm, and the units check is required on every export. The OCCT validity check runs after every operation and doesn't block Export. Watertight checks are dropped (Erik, 02:17).
- Done means CTest with CI=1 passes (occt_gate Passed), deploy_smoke and phone_smoke pass including the new tests, and the secrets/Blink scan is clean. Commit only on your PR branch and open a PR; Repo Keeper merges after a rebase onto the latest main and a green build check.

## Model
- Each part has a name, its own solid (a deep copy, no shared instances), a placement stored as a TopLoc_Location in mm, and a material tag.
- The placement is applied to the shape only at Combine and at export.
- The parts list shows in the property sheet. Select one or more parts by tap, with targets at least 44 px.
- Save/load (.cadmvp, PR #2) already stores parts with placement and material tag. Keep that format and don't change it.

## Combine
- Runs BRepAlgoAPI_Fuse on the selected parts (2 or more), then the validity check. If that fails, roll back with a clean error and leave the model unchanged.
- The result replaces the selected parts as one new part, recorded as one undo step in the existing undo stack (web/undo.mjs).
- Mixed materials (Chief 07:06): Combine is refused with a clean error and the model unchanged when the selected parts have different material tags. Same-material parts produce a part with that tag.

## Export
- 3MF with unit="millimeter", one mesh object per part with its placement applied, and the material written through core-spec base materials (no extension). Don't write a material on objects that hold components; write plain mesh objects.
- One 3MF file holding all parts, one mesh object per part (Chief 07:06).
- Material tags: PLA, PETG, TPU; default PLA (Chief 07:06).

## Tests
- Two parts (a box and a cylinder) with different placements: save, reload, and the names, placements, tags and exact volumes (BRepGProp, within 0.01) match.
- Combine two overlapping parts: the result is valid, its exact volume is within 0.01 of the reference fused volume, and undo restores both parts.
- A failed Combine (forced through a test hook) and a mixed-material Combine (PLA + TPU) each leave the model unchanged with a clean error.
- The exported 3MF parses, has unit="millimeter", one object per part, the right material per object, and bounding boxes matching the placed parts within 0.01 mm.
- Phone: the parts list and the Combine button are at least 44 px and reachable at 390x844.

## Routing
- Rulings are in (07:06). Final for launch; land it in the landing order after delete, with a rebase and a green build.