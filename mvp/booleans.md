# Spec: interactive Booleans (MODO-style, but reliable)

> Rule update (Erik, 2026-10-22 02:17 MT): watertight checks and tests are dropped. Units (mm) checks stay and gate Export. The OCCT shape-validity check after operations stays, but a failure is a clean error/revert and never blocks Export. Any watertight gate or watertight test below is superseded by this rule.

Status: DRAFT (Doc Steward, 2026-10-21). From Erik (2:05 AM MT). Research input pending from Research Digest (why MODO Booleans fail; OCCT BRepAlgoAPI and fuzzy options).

## Goal
Union, Cut and Intersect that feel like MODO (pick tool, drag, live preview) but don't fail. First use: placing the off-centre disc on the Blink bracket (`mvp/projects/blink-l-bracket.md`).

## Behaviour
- Pick a target body and a tool body, then choose Union, Cut or Intersect.
- **Drag preview (Option C, team-chosen, Chief lock 2026-10-26):** ghost transform while the drag is in progress. On release, the exact OCCT Boolean runs. Extrude Intersect stays out of the Join/Cut MVP slice.
- On commit, run the real watertight and units check. If the result is invalid, don't commit: show why and keep the prior state (undo-safe).
- Snapping to faces, edges and centres, so the off-centre disc can be placed exactly. Numeric offset entry in mm.

## Reliability requirements (method TBD pending research)
- B-rep Booleans via OCCT (`BRepAlgoAPI_*`), not mesh Booleans.
- Handle coplanar faces and touching or near-touching geometry. OCCT `SetFuzzyValue` for near-coincident Booleans is **0.01 mm** (Chief lock 2026-10-26; **team-chosen**; OCCT example 1e-5 scaled for our mm).
- Validate inputs and outputs (`BRepCheck_Analyzer`). Failure is reported, never silent.
- Test cases (CTest): coplanar union, coplanar cut, tangent cylinder, disc on bracket at an off-centre position, and repeated drag and commit cycles. All results must be watertight.

## Performance
Preview frame rate and the max commit time on phones are TBD.

## Open TBDs for Erik
Preview fidelity targets stay open. Fuzzy value, drag preview, and Extrude Intersect in the Join/Cut MVP slice are the Chief lock (2026-10-26) below.
## Research findings (research/occt-wasm/booleans.md, 2026-10-21)
- Coplanar faces are the known failure case, and the bracket disc sits flush on the leg top.
- OCCT settings: `SetFuzzyValue` **0.01 mm** (Chief lock 2026-10-26, **team-chosen**; OCCT example 1e-5 scaled for our mm); SetGlue(BOPAlgo_GlueShift) only for the flush disc on leg, never for the holes or any real intersection; SetNonDestructive so undo and re-drag work; SimplifyResult after the operation.
- Checks: BOPAlgo_ArgumentAnalyzer before the operation; BRepCheck_Analyzer plus ShapeFix_Shape after; then our watertight and units gate.
- Live drag: Chief lock 2026-10-26 (**team-chosen**, Option C) is a ghost transform while dragging and the exact OCCT Boolean on release. A live cut or union preview with manifold-3d (Apache-2.0, single-threaded WASM build) stays out unless Erik asks. three-bvh-csg is rejected.
- On failure: keep the last good shape, show the error, snap the tool body back, and keep Export disabled.
- Pilot to confirm the API names in a libcascade 3.1.0 test build.
- Still TBD: preview mesh coarseness, WASM Boolean timing, manifold-3d download size, Push/Pull scope. Fuzzy tolerance is locked at **0.01 mm** (Chief lock 2026-10-26).
## Chief decision (2026-10-21)
- MVP live drag: a see-through ghost while dragging. On release, the exact OCCT Boolean runs, then check and repair, then the watertight and units gate; roll back on any failure.
- manifold-3d stays out unless Erik asks to watch the cut or union happen live.
- Still open (not locked 2026-10-26): phone preview speed target. Fuzzy tolerance, Extrude Intersect in the Join/Cut MVP slice, and ghost vs live preview are closed by the Chief lock below.

## Chief lock (2026-10-26 ~1:02 PM MT)

Chief lock via Digest sketch→Boolean shortlist. Do not invent. (1) and (2) are **Erik TBD**. (3), (4), and (5) are **team-chosen**.

1. L-bracket dimensions beyond wall/disc **4 mm**, corner **90°**, **3 CSK/leg**, and the off-centre disc stay **Erik TBD**. Do not invent. Recorded in `mvp/requirements.md`.
2. Truck discuss parts (bed, spokes, tread, interior, doors) stay **Erik TBD**. Do not invent. Recorded in `mvp/requirements.md`.
3. OCCT `SetFuzzyValue` for near-coincident Booleans = **0.01 mm** (OCCT example 1e-5 scaled for our mm). **Team-chosen.**
4. Drag preview = **Option C**: ghost transform while drag; exact OCCT Boolean on release. Extrude Intersect stays out of the Join/Cut MVP slice. **Team-chosen.**
5. Fillet/chamfer defaults = **2 mm / 0.5 mm** (Chief: already in code). **Team-chosen.** Supersedes "fillet/chamfer non-blocking / no values until sourced" for these defaults only. Other TBD dimensions stay TBD.
