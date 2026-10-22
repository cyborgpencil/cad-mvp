# Item 3: Project file save/load
Save the whole project to a file and load it back exactly. The file stores bodies as OCCT BRep plus each body's name, primitive parameters, transform and op history needed for undo, and the unit (mm). Save downloads the file; Load opens a file picker (works on iPhone Safari). Loading replaces the scene after a confirm and runs the OCCT shape-validity check on every body; an invalid or unreadable file gives a clean error and leaves the current model unchanged. File extension and format version are team choices recorded in web/PROGRESS.md. Print SAVELOAD_DONE.

## Rules for every session
- Work in C:\Dev\cadcam-mvp on Z13 only. Run git pull --ff-only first. Write no C++ kernel code unless the step needs it, and Erik reviews any core diff.
- Touch first: targets at least 44x44 CSS px. Test in portrait at 390x844 in Chromium and WebKit iPhone 13 profile.
- Every default is a team choice recorded in web/PROGRESS.md. Invent no Erik specs.
- The Blink bracket is a test fixture only: never shipped, never pushed.
- Units stay mm. Done means CTest with CI=1 passes (occt_gate Passed), deploy_smoke passes including the new tests, and the secrets/Blink scan is clean. Don't commit; Repo Keeper merges via PR after CI is green.

## Tests
- Round trip: build box + cylinder + one Boolean, save, reload; body count, names, volumes (within 0.1%) and bounding boxes (within 0.01 mm) match, unit is mm.
- Corrupt and empty files give a clean error and the model is unchanged.
- Save/Load buttons are at least 44 px and reachable at 390x844 without covering the viewport rule.

## File format (Chief ruling, 2026-10-22 02:21 MT; replaces any TBD above)
- Extension `.cadmvp` (plain JSON inside, not `.cadmvp.json`).
- Top level: `"units": "mm"`, `"version"`, and a parts list.
- Each part: name, placement (mm), material tag, primitive parameters, features, and the shape as OCCT BREP text (`BRepTools::Write` / `BRepTools::Read`).
- Load rebuilds from the parameters; if a rebuild fails, it falls back to the BREP. Wrong or missing units, or a failed validity check, gives a clean error and leaves the model unchanged.
- Smoke test: save, reload, load, and each part's volume and bounding box (BRepBndLib::AddOptimal) match within 0.01; units are still mm.
- `*.cadmvp` is gitignored (Repo Keeper).
