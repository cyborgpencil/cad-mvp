# Mobile step 3: Hole tool

> Rule update (Erik, 2026-10-22 02:17 MT): watertight checks and tests are dropped. Units (mm) checks stay and gate Export. The OCCT shape-validity check after operations stays, but a failure is a clean error/revert and never blocks Export. Any watertight gate or watertight test below is superseded by this rule.
Tap a face, then type the position (mm from the face edges), the diameter and the depth (through or blind). Optional countersink with a diameter and an editable angle, default 82 degrees (#8 flat-head wood screw; 90 degrees is the metric ISO angle). Defaults: 4.5 mm hole, 9.5 mm countersink (#8 wood screw, sourced, unverified fit). Build each hole as one parametric cut using the Boolean wrappers. Test: put 3 countersunk holes on a plate in portrait. Print MOBILE3_DONE.

## Rules for every session
- Work in C:\Dev\cadcam-mvp on Z13 only. Write no C++ kernel code unless the step needs it, and Erik reviews any core diff.
- Reuse the occt-ops.mjs wrappers. Check IsDone() before Shape(), free OCCT handles with delete(), and run the watertight and mm gate after every op. On a failed or empty result, revert and keep the inputs.
- Use the Booleans mesh settings for display and export.
- Touch first: targets at least 44x44 CSS px (WCAG 2.5.5 / Apple HIG). Touch pick radius about 20 px (team choice), mouse stays 8 px. Test in portrait at 390x844.
- Every default is a team choice recorded in web/PROGRESS.md. Physical-fit values are tagged "unverified fit". Invent no Erik specs.
- The Blink bracket is a test fixture only: no baked-in scene, no shipped demo, and its geometry is never pushed.
- Done means CTest with CI=1 passes (occt_gate Passed), deploy_smoke passes including the new portrait test, and the STLs are watertight and in mm. Don't commit; Repo Keeper commits after the checks.

## Carried from step 2 (2026-10-21 22:33 MT)
- Face picking: extend web/viewport-selection.mjs (step 2) instead of adding a new picker. Hole position fields go in the portrait bottom sheet, not a new panel.
- Placement: use step 2's transformShape / snap (1 mm) for the hole centre; typed values override snap.
- Portrait overflow: at 390x844 the sheet and toolbar must not overflow sideways. Keep deploy_smoke's checks (scrollWidth <= clientWidth, every visible button and the status line right <= innerWidth) passing; wrap or scroll rows, never shrink targets below 44 px.
- Countersink geometry: BRepPrimAPI_MakeCone(R1 = countersink dia/2, R2 = hole dia/2, H = (R1-R2)/tan(angle/2)), cone cut fused with the hole cylinder, then one Boolean cut on the target body; check watertight and mm after the cut. Report volumes before and after.
- Smoke test: add a portrait test placing 3 countersunk holes on a plate; STL watertight, mm header, volume reported.
- Closed right panel: mark it inert or visibility:hidden when closed (not just slid off-screen); the smoke test asserts its buttons have zero on-screen size and cannot be tapped or focused.
- Leak fix: tests/test_occt_gate.mjs (about line 479) writes the Blink hole offsets in a label and comparison. Compare against the local fixture values (or hole count only) so no Blink layout numbers appear in tracked files.
