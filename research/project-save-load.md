# Project save and load (.cadmvp): end-to-end check (Research Digest, 2026-10-22)
What the file stores, from the code: `PROJECT_VERSION` 1, `units` "mm", and per part a name, material tag, placement, the primitive kind and parameters when there are any, and the shape as OCCT BREP text written by `BRepTools.Write` and read back with `BRepTools.Read`. Load refuses empty, unreadable, non-mm, wrong-version and shape-check-failing files with "The model was not changed." The file stores no undo history.
1. P1 build: on the live build, make three bodies: a 20 x 20 x 20 mm box, a cylinder, and a box combined with another box. Give one PETG and one TPU, and leave the third with no material set so it reads as the PLA default (PR #8, `web/assemblies.mjs`: `MATERIALS` PLA, PETG, TPU; missing or "default" reads as PLA). Resize one body by typing a new size and move another.
2. P2 record: note each body's name, material, size and position, and its volume from the log (BRepGProp, mm3).
3. P3 save: save the `.cadmvp` file. Open it as text and check it has `"units": "mm"`, version 1, and one entry per body.
4. P4 reload: open the app in a fresh tab (new tab, not a refresh), then load the file.
5. P5 compare: there are the same number of bodies with the same names. Material tags survive: the PETG and TPU bodies keep their tags and display colors, and the untagged body still reads as PLA, not blank or another material. Each size and position is within 0.05 mm, and each volume is within 0.01 mm3. The shape check passes on every body, and Units still shows mm.
6. P6 edit after reload: resize, move and delete one body each, then undo and redo all three. Undo stops at the loaded state; the edits made after the reload undo and redo as normal.
7. P7 bad files: loading an empty file, a file with `"units": "in"`, and a file with version 2 each shows the matching message and leaves the model untouched.
Pass means P1 through P7 all pass. Ruling (3T and Chief, 2026-10-22 08:46 MT): `.cadmvp` saves no undo history; loading clears the undo stack, the same as most CAD apps.

Source: `web/project-file.mjs` on main `e970aba` (PR #2); material tags from `web/assemblies.mjs` (PR #8, `46af321`). Run by Pilot on the live build after wrap-up; gaps go to 3T as a Cursor fix.

