# Item 3: Project file save/load
Save the whole project to a file and load it back exactly. The file format is exactly the Chief ruling below (.cadmvp JSON, units mm, version, parts with parameters + BREP text). Save downloads the file; Load opens a file picker (works on iPhone Safari). Loading replaces the scene after a confirm and runs the OCCT shape-validity check on every body; an invalid or unreadable file gives a clean error and leaves the current model unchanged. Print SAVELOAD_DONE.

## Rules for every session
- Work in a fresh clone on a PR branch off main. Never push to main. Any C++ or bindings change goes in its own commit and is flagged for Erik review.
- Touch first: targets at least 44x44 CSS px. Test in portrait at 390x844: Chromium in CI; WebKit via tests/phone_smoke.py (Playwright, iPhone 13 profile; exits 77 skip in CI when Playwright is missing, keep that). Add new checks to both deploy_smoke and phone_smoke.
- Every default is a team choice recorded in web/PROGRESS.md. Invent no Erik specs.
- The Blink bracket is a test fixture only: never shipped, never pushed.
- Units stay mm. Done means CTest with CI=1 passes (occt_gate Passed), deploy_smoke and phone_smoke pass including the new tests, and the secrets/Blink scan is clean. Commit only on your PR branch and open a PR; Repo Keeper merges after the build check is green.

## Tests
- Round trip: build a box + a cylinder (Booleans are not built yet; add a Boolean case later), save, reload; part count and names match, each part's volume and AddOptimal bounding box match within 0.01, unit is mm.
- Corrupt and empty files give a clean error and the model is unchanged.
- Save/Load buttons are at least 44 px and reachable at 390x844 without covering the viewport rule.

## File format (Chief ruling, 2026-10-22 02:21 MT; replaces any TBD above)
- Extension `.cadmvp` (plain JSON inside, not `.cadmvp.json`).
- Top level: `"units": "mm"`, `"version"`, and a parts list.
- Each part: name, placement (mm), material tag, primitive parameters, features, and the shape as OCCT BREP text (`BRepTools::Write` / `BRepTools::Read`).
- Load rebuilds from the parameters; if a rebuild fails, it falls back to the BREP. Wrong or missing units, or a failed validity check, gives a clean error and leaves the model unchanged.
- Smoke test: save, reload, load, and each part's volume and bounding box (BRepBndLib::AddOptimal) match within 0.01; units are still mm.
- `*.cadmvp` is gitignored (Repo Keeper).

## Done means
- ci.yml is green on the PR, then Repo Keeper merges. No direct merge by the agent.

## Pilot review fixes (2026-10-22)
- No BREP serialize path exists yet (bindings export gate, loadFixture, checkShape, export3mf, etc.). Add BRepTools::Write and BRepTools::Read through a new binding, preferably via std::stringstream (BRepTools Write/Read accept streams), so no Emscripten virtual file system is needed. New binding goes in its own commit, flagged for Erik. First check the symbols link in the WASM build; if not, stop and report.
- File format is exactly the Chief's ruling in the section above. Do not change it.
- Chief ruling: loading asks first if there are unsaved changes, then clears the undo stack. Undo/redo comes from the gizmo batch (Chief 04:33); call its clear. If it isn't on main yet, add a clearUndo hook only.
- Units test: switch UI to inches, save, reload. File still says units mm, and sizes show no 25.4x drift. Use BRepBndLib::AddOptimal for bounding-box checks, tolerance 0.01.
- Tests go in tests/deploy_smoke.py through a window test hook, since the file picker cannot be clicked headless. The iPhone file-picker check is manual and is logged in web/PROGRESS.md.

## Routing (Chief)
- Confirmed Cursor job: CI builds cadcam.wasm from source (pages.yml, emsdk). OCCT is prebuilt libcascade 3.1.0, so BRepTools Write/Read must be exported by it; run the symbol check first.
- Launch only after phone fix and ci.yml are on main (Repo Keeper posts).
