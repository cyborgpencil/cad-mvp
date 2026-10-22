# Mobile step 5: Touch Booleans and acceptance test
Show big labelled Union, Cut and Intersect buttons that are clearly visible on desktop and phone. Tap to pick the target first, then the tool, with a clear label for each role. Run the gate on every result. Acceptance script (headless, portrait, UI only, added to deploy_smoke): build an L-bracket from boxes, 3 countersunk holes per leg, and an off-centre disc fused on one leg, then export an STL that is watertight and in mm. Print MOBILE5_DONE.

## Rules for every session
- Work in C:\Dev\cadcam-mvp on Z13 only. Write no C++ kernel code unless the step needs it, and Erik reviews any core diff.
- Reuse the occt-ops.mjs wrappers. Check IsDone() before Shape(), free OCCT handles with delete(), and run the watertight and mm gate after every op. On a failed or empty result, revert and keep the inputs.
- Use the Booleans mesh settings for display and export.
- Touch first: targets at least 44x44 CSS px (WCAG 2.5.5 / Apple HIG). Touch pick radius about 20 px (team choice), mouse stays 8 px. Test in portrait at 390x844.
- Every default is a team choice recorded in web/PROGRESS.md. Physical-fit values are tagged "unverified fit". Invent no Erik specs.
- The Blink bracket is a test fixture only: no baked-in scene, no shipped demo, and its geometry is never pushed.
- Done means CTest with CI=1 passes (occt_gate Passed), deploy_smoke passes including the new portrait test, and the STLs are watertight and in mm. Don't commit; Repo Keeper commits after the checks.

## Fixture (Chief, 20:48 MT)
BLINK_DEFAULTS moves to tests/fixtures/ as the acceptance geometry only. It stays out of the deployed scene, and assemble_site.py keeps excluding tests/fixtures/.

Note (21:17): the BLINK_DEFAULTS move now happens in step 1. Here, just confirm it's still in tests/fixtures/ and that ?demo=blink is gone.

Note (21:28): the Blink fixture should have 8 through-holes, 6 countersunk leg holes plus 2 disc screw holes (sizes in the local fixture notes). The fixture is local-only (tests/fixtures/blink.* is gitignored, Chief's final ruling at 21:38). occt_gate skips it on a clean checkout and logs 'skipped, local fixture'. It's only published if Erik approves.
