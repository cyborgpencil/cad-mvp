# Antigravity L-bracket rebuild (Q5 phone acceptance)

Q5 queue item 5. Phone acceptance rebuild on the live app. This file is the Antigravity feed. It does not change the app by itself.

**Hard lock:** Implementation is **Antigravity-only on Z13**. Pilot stages the worktree and owns the `agy` run after this brief is on main. Do not use Grok Build or Cursor for the handoff into code. Keep `C:\Dev\cadcam-mvp` main clean.

**Source of truth:** Q5 in `mvp/requirements.md` (locked #150 @ `a38d89d`). Sizes that Q5 does not lock stay **TBD**. Do not invent them.

## Goal
Rebuild the L-bracket for phone acceptance: sketch → Blind Extrude → Union/Cut. Units **mm**. No printer send.

## Workflow
1. Sketch the L-profile (two legs, **90°**) on XY, or on the face that matches the existing app sketch plane.
2. Blind Extrude to the locked **4 mm** wall thickness.
3. Disc: sketch a circle, Extrude, **Union** onto the appropriate leg. Off-centre disc (Q5 / Acceptance). Disc thickness is the locked **4 mm**.
4. Holes: sketch circles and Extrude, or Cut cylinders. **3 CSK per leg**. Use **Cut** for holes.
5. After each op: units check (**mm**) and OCCT shape-validity. Watertight is INFO-only and does not block Export.
6. Export STL and 3MF when `Module.gate()` allows. Units stay mm.

## Do not bake
`mvp/projects/blink-l-bracket.md` and any prior Blink part are **reference only**. Do not copy Blink layout or numeric sizes into the app, the scene, or this run.

Locked only: wall **4 mm**, disc **4 mm**, corner **90°**, units **mm**, plus the qualitative constraints **3 CSK/leg** and an **off-centre disc**. Any other size (leg length/width, hole diameter, countersink, spacing, disc diameter, which leg, placement) is **TBD** — leave it TBD.

Booleans: **Union/Cut only**. Intersect is not required. No printer.

## Done
Draft until Doc Steward tip-matches (primary COMMENT) and Research Digest tip-matches (second). Author does not self-APPROVE. Repo Keeper undrafts and plain-merges. After this file is on main, Pilot runs Antigravity-only from it. Report the prompt PR link and tip SHA; Pilot reports any impl PR separately.
