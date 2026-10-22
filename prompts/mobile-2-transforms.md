# Mobile step 2: Transforms
Add a touch gizmo for move, rotate and resize (handles at least 44 px), with typed mm and degree values as an alternative. Parameters stay editable after creation. Use Research Digest's mobile touch digest for hit sizes and tap-versus-drag rules. Test: move, rotate and resize a box in portrait using taps and typed values. Print MOBILE2_DONE.

## Rules for every session
- Work in C:\Dev\cadcam-mvp on Z13 only. Write no C++ kernel code unless the step needs it, and Erik reviews any core diff.
- Reuse the occt-ops.mjs wrappers. Check IsDone() before Shape(), free OCCT handles with delete(), and run the watertight and mm gate after every op. On a failed or empty result, revert and keep the inputs.
- Use the Booleans mesh settings for display and export.
- Touch first: targets at least 44x44 CSS px (WCAG 2.5.5 / Apple HIG). Touch pick radius about 20 px (team choice), mouse stays 8 px. Test in portrait at 390x844.
- Every default is a team choice recorded in web/PROGRESS.md. Physical-fit values are tagged "unverified fit". Invent no Erik specs.
- The Blink bracket is a test fixture only: no baked-in scene, no shipped demo, and its geometry is never pushed.
- Done means CTest with CI=1 passes (occt_gate Passed), deploy_smoke passes including the new portrait test, and the STLs are watertight and in mm. Don't commit; Repo Keeper commits after the checks.

## Inputs (2026-10-21 20:48 MT)
Follow research/mobile-touch-cad.md: touch-action none on the viewport, Pointer Events, under 8 px of movement counts as a tap, finger gizmo zones of at least 44 px, one Move/Rotate/Scale mode at a time behind a 44 px switch, and an mm panel kept in sync with the gizmo. Snap and stepper sizes are open: pick them as team choices and record them in web/PROGRESS.md.

Snap and steppers are settled (Chief, 20:48): 1 mm and 15 degree snap, on by default; steppers 1 mm, or 0.1 mm on long press. See web/PROGRESS.md.

## Carried over from step 1 (21:20)
In portrait, the dimension panel must collapse or become a bottom sheet so it doesn't cover the view, and it must not overlap the Home button. Add this to the 390x844 portrait smoke test.
