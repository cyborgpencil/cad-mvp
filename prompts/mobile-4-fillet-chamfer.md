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

## Acceptance numbers (Research Digest, 2026-10-22)
One straight edge of length L on a box:
- Fillet r (BRepFilletAPI_MakeFillet, Add(r, edge), Build): removes r^2*(1-pi/4)*L; new face is GeomAbs_Cylinder of radius r.
- Equal-distance chamfer d (BRepFilletAPI_MakeChamfer, Add(d, edge)): removes d^2/2*L; new face is a 45 deg plane.
- Topology for both: faces 6->7, edges 12->15, vertices 8->10 (V-E+F=2).
- Generic test case: 20 mm cube, r=d=2 mm -> fillet 8000 to 7982.832 mm3 (-17.168), chamfer 8000 to 7960.000 mm3 (-40.000).
- Checks: IsDone true, analyzer valid, zero free bounds; BRep volume within 0.1%, STL within 0.5% (team-chosen tolerances); STL watertight with mm header.
- UI rejects r or d >= the shortest adjacent face width (single edge; the half-width limit applies only when two parallel edges of one face are both treated). Do not assume where IsDone turns false: the test treats IsDone false or an invalid analyzer result as a clean error (revert, message), never a crash.
- These asserts go in tracked tests/test_occt_gate.mjs, not only a side script.
Sources: OCCT modeling algos guide (fillets/chamfers), MakeFillet and MakeChamfer class references.
- Viewer normals (Chief, 2026-10-22): smoke test fails if any vertex normal on a fillet/chamfer face points into the solid (TopAbs_REVERSED faces need flipped winding in the viewer mesh). Screenshot from above and at an angle.
