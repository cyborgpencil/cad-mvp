# Project save and load (.cadmvp): end-to-end check (Research Digest, 2026-10-22)
What the file stores, from the code: `PROJECT_VERSION` 1, `units` "mm", and per part a name, material tag, placement, the primitive kind and parameters when there are any, and the shape as OCCT BREP text written by `BRepTools.Write` and read back with `BRepTools.Read`. Load refuses empty, unreadable, non-mm, wrong-version and shape-check-failing files with "The model was not changed." The file stores no undo history.
1. P1 build: on the live build, make three bodies: a 20 x 20 x 20 mm box, a cylinder, and a box combined with another box. Give one of them PETG. Resize one body by typing a new size and move another.
2. P2 record: note each body's name, material, size and position, and its volume from the log (BRepGProp, mm3).
3. P3 save: save the `.cadmvp` file. Open it as text and check it has `"units": "mm"`, version 1, and one entry per body.
4. P4 reload: open the app in a fresh tab (new tab, not a refresh), then load the file.
5. P5 compare: there are the same number of bodies with the same names and materials. Each size and position is within 0.05 mm, and each volume is within 0.01 mm3. The shape check passes on every body, and Units still shows mm.
6. P6 edit after reload: resize, move and delete one body each, then undo and redo all three. Undo has to stop at the loaded state.
7. P7 bad files: loading an empty file, a file with `"units": "in"`, and a file with version 2 each shows the matching message and leaves the model untouched.
Pass means P1 through P7 all pass. TBD for Erik: should Undo go back past a load? The file has no history, so this plan expects it not to.
=======
## Wrap-up additions (Erik 2026-10-22 08:40 MT)
- For A (Blink bracket) and B (11-part truck), take Orca screenshots of every sliced plate. Stage them on Z13 in C:\Users\cybor\Pictures\cadmvp-shots\, then copy them to /workspace/cad-mvp-updates/shots. Don't send anything to the printer.
- Project file check: save each model as .cadmvp, reload it in a fresh tab, and confirm every body, its edits and its material tags come back, with the same bounding box and volume tolerances as above. Fix any gaps before sign-off.
>>>>>>> theirs

Source: `web/project-file.mjs` on main `e970aba` (PR #2). Run by Pilot on the live build after wrap-up; gaps go to 3T as a Cursor fix.

