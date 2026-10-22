# Acceptance A and B test plans (draft, Doc Steward 2026-10-22)
Owner: Grok Build Pilot runs both on Z13 (Chief 02:17 and 02:21 MT). Sources: web/PROGRESS.md overnight queue items 6 and 7, Chief rulings 02:21, mvp/test-matrix.md, mvp/projects/blink-l-bracket.md. Watertight checks and tests were dropped (Erik, 02:17). Units checks and the OCCT validity check still apply. Screenshots go in builds\screenshots\<ID>-<step>.png. Nothing is sent to a printer.

## Acceptance A: Blink bracket built in the app and sliced in OrcaSlicer
The Blink layout stays out of the public repo. Its dimensions are only in the gitignored tests/fixtures/blink.notes.md, and this file must not copy them.
Preconditions: main has gizmo/undo (fbd0947), PR #1 nav cube, PR #2 save/load, and the Booleans, fillet/chamfer and delete tools the build needs. Any missing tool is a blocker, reported as such.
Steps and checks:
1. A1 build: using only the live app UI (phone portrait 390x844 and desktop), build the bracket from blink.notes.md: L-bracket with 4 mm thickness, 3 countersunk holes per leg, and an off-centre disc. No baked-in layout or script shortcut. Screenshot the result.
2. A2 validity and units: the OCCT validity check passes after each operation, and the units read mm throughout.
3. A3 measure: the bounding box and exact-shape volume (BRepGProp) match blink.notes.md within 0.01 mm and 0.01 mm3. The pass/fail values are recorded locally only.
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
## Item 4: project save and load, end to end (Research Digest 2026-10-22, from web/project-file.mjs on main)
What the file stores, from the code: `PROJECT_VERSION` 1, `units` "mm", and per part a name, material tag, placement, the primitive kind and parameters when there are any, and the shape as OCCT BREP text written by `BRepTools.Write` and read back with `BRepTools.Read`. Load refuses empty, unreadable, non-mm, wrong-version and shape-check-failing files with "The model was not changed." The file stores no undo history.
1. P1 build: on the live build, make three bodies: a 20 x 20 x 20 mm box, a cylinder, and a box combined with another box. Give one of them PETG. Resize one body by typing a new size and move another.
2. P2 record: note each body's name, material, size and position, and its volume from the log (BRepGProp, mm3).
3. P3 save: save the `.cadmvp` file. Open it as text and check it has `"units": "mm"`, version 1, and one entry per body.
4. P4 reload: open the app in a fresh tab (new tab, not a refresh), then load the file.
5. P5 compare: there are the same number of bodies with the same names and materials. Each size and position is within 0.05 mm, and each volume is within 0.01 mm3. The shape check passes on every body, and Units still shows mm.
6. P6 edit after reload: resize, move and delete one body each, then undo and redo all three. Undo has to stop at the loaded state.
7. P7 bad files: loading an empty file, a file with `"units": "in"`, and a file with version 2 each shows the matching message and leaves the model untouched.
Pass means P1 through P7 all pass. TBD for Erik: should Undo go back past a load? The file has no history, so this plan expects it not to.
