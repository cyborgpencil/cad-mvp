# Prompt: Blink L-bracket screw holes, mount disc, and user-picked fillet/chamfer

Spec: mvp/projects/blink-l-bracket.md. Booleans rules: mvp/booleans.md. Values: web/PROGRESS.md decisions table.

## Values
Erik delegated design values to the team (2026-10-21 19:00 MT). Use the values Research Digest proposes and the Chief approves, as recorded in web/PROGRESS.md and marked team-chosen. Put every value in one named constants block. Thickness stays 4 mm.
Physical-fit values can't be confirmed without Erik's measurements: the Blink boss size, the disc hole pattern, the casing width and profile, and the printed-hole oversize. Use the team-chosen values, mark these as "unverified fit" in PROGRESS.md, and flag them before anything is printed.

## Build
1. Holes: 3 through-holes per leg, using the team-chosen diameter, spacing and countersink. Cut them with the existing Boolean wrappers. Never use SetGlue on holes.
2. Disc: a 4 mm thick disc on top of one leg, fused flush. SetGlue(BOPAlgo_GlueShift) is allowed only for this flush fuse. The disc screw holes are cut through.
3. Fillet and chamfer on user-picked edges (edge mode, hotkey 2): apply on confirm, not live. A fillet or chamfer that's too large is caught, and the last good shape is kept.
4. Use the mesh settings from the Booleans session for both display and export.

## Gate (every op)
Check IsDone() before Shape(). Run OCCT validity, watertight and mm checks. Revert on failure. Free handles with delete().

## Tests
- Node: the bracket with holes and disc passes the gate, with a single solid and volume close to the analytic estimate. The leg holes go fully through, with no blind or zero-thickness walls. An oversized fillet on a picked edge is rejected.
- Browser smoke: ?demo=blink builds and passes the gate. Edge-pick a fillet, then a chamfer. There are no page errors. Fixtures still return 404.
- CTest with CI=1: all tests pass, and occt_gate shows Passed, not Skipped.
- Pilot's own STL check: watertight, mm, expected bounds and volume.

## Rules
Don't commit. Flag any src/ change for Erik's review. Strict MVP scope. Print BLINK_DONE at the end.

## Update 2026-10-21 19:58 MT - Chief rulings
- Leg holes are clearance holes for #8 wood screws. The size is TBD until Research Digest posts it from a sourced table. Don't start the session before then.
- M3 holes are only for the disc screws.
- The team picks the disc diameter, its position on one leg and its hole pattern, and each is labelled a team choice in web/PROGRESS.md. The four sizes only Erik can measure stay marked "unverified fit". Don't use the Outdoor 2K+ numbers.
- Booleans stay two-body for the MVP.
- Two UI fixes are part of this session: make the op buttons easier to see, and show the gizmo when a body is selected in Item mode.
- Start only after CI is green on the Booleans push.

## Update 2026-10-21 20:05 MT - Hole and disc values (team choices, all "unverified fit")
- Leg holes for #8 wood screws: 4.5 mm through (the free fit per the UVA clearance chart), 90 degree countersink 9.5 mm across (Engineering ToolBox), on the leg centreline at 10, 20 and 30 mm from the corner. This replaces the earlier 8.5 mm countersink.
- Disc: 18 mm across and 4 mm thick, fused flush on top of the vertical leg so it stays inside the 20 mm leg width. It sits between two leg holes; Pilot's clearance check sets the final offset. This replaces the earlier 30 mm disc, which would hang over the leg.
- If the disc still covers a leg hole, drop that hole rather than move the disc, and log it (Chief ruling).
- M3 disc screw holes only. The hole pattern is a team choice and stays marked "unverified fit".
