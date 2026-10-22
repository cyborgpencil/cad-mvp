# Mobile step 1: Primitives

> Rule update (Erik, 2026-10-22 02:17 MT): watertight checks and tests are dropped. Units (mm) checks stay and gate Export. The OCCT shape-validity check after operations stays, but a failure is a clean error/revert and never blocks Export. Any watertight gate or watertight test below is superseded by this rule.
Add box, cylinder and disc from a touch toolbar. Each one opens an editable dimension panel in mm (numeric keypad, inputmode=decimal) and can be edited after creation. Defaults: 20 mm (team choice already in PROGRESS.md); disc 18 mm across, 4 mm thick. Test: on a portrait viewport, tap-create each primitive, edit a dimension, check the result through the gate. Print MOBILE1_DONE.

## Rules for every session
- Work in C:\Dev\cadcam-mvp on Z13 only. Write no C++ kernel code unless the step needs it, and Erik reviews any core diff.
- Reuse the occt-ops.mjs wrappers. Check IsDone() before Shape(), free OCCT handles with delete(), and run the watertight and mm gate after every op. On a failed or empty result, revert and keep the inputs.
- Use the Booleans mesh settings for display and export.
- Touch first: targets at least 44x44 CSS px (WCAG 2.5.5 / Apple HIG). Touch pick radius about 20 px (team choice), mouse stays 8 px. Test in portrait at 390x844.
- Every default is a team choice recorded in web/PROGRESS.md. Physical-fit values are tagged "unverified fit". Invent no Erik specs.
- The Blink bracket is a test fixture only: no baked-in scene, no shipped demo, and its geometry is never pushed.
- Done means CTest with CI=1 passes (occt_gate Passed), deploy_smoke passes including the new portrait test, and the STLs are watertight and in mm. Don't commit; Repo Keeper commits after the checks.

## First task in this session (Chief, 21:17)
Before anything else, move BLINK_DEFAULTS into tests/fixtures/ (assemble_site.py already excludes it) and take ?demo=blink out of the deployed app. Check that the fixture URL returns 404 on the built site. The step 1 push must not ship ?demo=blink.
