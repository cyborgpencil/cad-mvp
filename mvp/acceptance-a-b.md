# Acceptance A and B test plans (draft, Doc Steward 2026-10-22)
Owner: Grok Build Pilot runs both on Z13 (Chief 02:17 and 02:21 MT). Sources: web/PROGRESS.md overnight queue items 6 and 7, Chief rulings 02:21, mvp/test-matrix.md, mvp/projects/blink-l-bracket.md. Watertight checks and tests were dropped (Erik, 02:17). Units checks and the OCCT validity check still apply. Screenshots go in builds\screenshots\<ID>-<step>.png. Nothing is sent to a printer.

## Acceptance A: Blink bracket built in the app and sliced in OrcaSlicer
The Blink layout stays out of the public repo. Its dimensions are only in the gitignored tests/fixtures/blink.notes.md, and this file must not copy them.
Preconditions: main has gizmo/undo (fbd0947), PR #1 nav cube, PR #2 save/load, and the Booleans, fillet/chamfer and delete tools the build needs. Any missing tool is a blocker, reported as such.
Steps and checks:
1. A1 build: using only the live app UI (phone portrait 390x844 and desktop), build the bracket from blink.notes.md: L-bracket with 4 mm thickness, 3 countersunk holes per leg, and an off-centre disc. No baked-in layout or script shortcut. Screenshot the result.
2. A2 validity and units: the OCCT validity check passes after each operation, and the units read mm throughout.
3. A3 measure: the exported bracket's bounding box is within 0.1 mm of the mm sizes typed into the UI, and its trimesh volume is within 1% of the app's own exact-shape volume (BRepGProp). Targets are the typed values, not blink.notes.md (3T ruling, 2026-10-22). The pass/fail values are recorded locally only.
4. A4 save/load: save as .cadmvp, reload, and the A3 values still match.
5. A5 export: export STL and 3MF. The 3MF says unit="millimeter".
6. A6 Orca: open both files in OrcaSlicer on Z13. `--info` and the size readout match A3 within 0.05 mm on every axis (Chief 07:06), with no scale prompt and no errors.
7. A7 slice: slice with printer profile "Ermo X1C", stock Bambu 0.20 mm Standard process, stock Bambu PLA Basic (Chief/3T 07:06). It slices with no errors. Screenshot the plate and the slice preview. No printer send.
Pass means A1 through A7 all pass. The public log records only pass/fail and the screenshot names.

## Acceptance B: toy truck assembly, PLA wheels and TPU tires, multi-plate Orca slice
Model per Chief 02:21: a flat parts list (one solid per part, a placement in mm, a material tag), Combine fuses the selected parts, no mates, and export writes one 3MF object per part with its material.
Preconditions: assemblies (prompts/assemblies.md) are merged, plus A's tool set.
Steps and checks:
1. B1 build: build the truck in the app as separate parts: the team-chosen parts below (10-21 rule).
2. B2 per-part checks: each part passes the validity check, and units read mm.
3. B3 combine: Combine fuses the body parts that are meant to be one piece. The fused part is valid, its volume is within 0.01 of the summed exact volumes minus overlaps, and undo restores the separate parts.
4. B4 save/load: save and reload. Part count, names, material tags, placements and volumes match.
5. B5 export: the 3MF has one object per part with its material tag, unit="millimeter", and placements kept.
6. B6 Orca plates: in OrcaSlicer on Z13, PLA parts go on one plate and TPU parts on another, PLA plate on Bambu PLA Basic, TPU plate on stock TPU 95A (3T 07:06; the Chief said Generic TPU, use the stock TPU 95A profile and note it) (the filament/plate check moved here, Chief 02:21). Screenshot each plate.
7. B7 slice: every plate slices with no errors. Screenshot the previews. No printer send.
Pass means B1 through B7 all pass.

## Truck parts (team-chosen 07:10 MT, recorded in web/PROGRESS.md)
All mm. 11 parts after the cab is combined into the chassis (Chief and 3T, 07:15 MT). TPU profile: stock TPU 95A (3T final).
- Chassis (PLA): 80 x 30 x 6 plate, two Ø4.4 through-holes across the 30 mm width, 10 mm in from each end, 3 mm up.
- Cab (PLA): 30 x 30 x 25 box on the chassis top at the front, combined with the chassis into one PLA body part (exercises Combine).
- Axles x2 (PLA): Ø4 x 44 cylinders.
- Wheel hubs x4 (PLA): Ø16 x 8 cylinders with a Ø4.2 bore.
- Tires x4 (TPU): ring OD 24, ID 15.6 (0.2 stretch on the Ø16 hub), width 8.
After the cab Combine the parts list is 11 parts. Combine of a hub with a tire must be refused (mixed materials), which B3 also checks.

## Wrap-up additions (Erik 2026-10-22 08:40 MT)
- For A (Blink bracket) and B (11-part truck), take Orca screenshots of every sliced plate. Stage them in the Z13 staging folder (cadmvp-shots). Don't send anything to the printer.
- Item 4 project file check: follow research/project-save-load.md (save as .cadmvp, reload in a fresh tab, compare). Fix any gaps before sign-off.
