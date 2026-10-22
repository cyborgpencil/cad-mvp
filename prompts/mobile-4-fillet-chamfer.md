# Mobile step 4: Fillet and chamfer
Tap edges to pick them (a touch pick radius of about 20 px, with the picks highlighted), choose fillet or chamfer, type a size, and apply on confirm. Defaults: R2 fillet, 0.5 mm chamfer. A failed op reverts. Test: fillet the inner edge and chamfer the outer edges of an L shape in portrait. Print MOBILE4_DONE.

## Rules for every session
- Work in C:\Dev\cadcam-mvp on Z13 only. Write no C++ kernel code unless the step needs it, and Erik reviews any core diff.
- Reuse the occt-ops.mjs wrappers. Check IsDone() before Shape(), free OCCT handles with delete(), and run the watertight and mm gate after every op. On a failed or empty result, revert and keep the inputs.
- Use the Booleans mesh settings for display and export.
- Touch first: targets at least 44x44 CSS px (WCAG 2.5.5 / Apple HIG). Touch pick radius about 20 px (team choice), mouse stays 8 px. Test in portrait at 390x844.
- Every default is a team choice recorded in web/PROGRESS.md. Physical-fit values are tagged "unverified fit". Invent no Erik specs.
- The Blink bracket is a test fixture only: no baked-in scene, no shipped demo, and its geometry is never pushed.
- Done means CTest with CI=1 passes (occt_gate Passed), deploy_smoke passes including the new portrait test, and the STLs are watertight and in mm. Don't commit; Repo Keeper commits after the checks.

## Carried from steps 2-3 (2026-10-21 23:05 MT)
- Edge picking: extend web/viewport-selection.mjs (face picking from step 3) to edges; highlight picks and show the count in the portrait bottom sheet. Size field and Fillet/Chamfer switch live in that sheet, not a new panel.
- Ops: BRepFilletAPI_MakeFillet / BRepFilletAPI_MakeChamfer through new occt-ops.mjs wrappers that check IsDone and keep the input on failure (same pattern as transformShape). Report volumes before and after; watertight and mm gate after every op.
- Portrait: keep deploy_smoke's horizontal-overflow checks and the closed-panel inert/zero-size check passing; wrap rows, never shrink targets below 44 px.
- Tests: no Blink layout numbers in tracked files; use the local fixture or generic shapes. Smoke test fillets the inner edge and chamfers the outer edges of a generic L shape at 390x844.
- From step 3 gaps: tracked tests must assert face count and key edge dimensions; the portrait screenshot must show the feature part, not the default box.
