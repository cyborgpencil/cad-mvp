# Spec: interactive Booleans (MODO-style, but reliable)

Status: DRAFT (Doc Steward, 2026-10-21). From Erik (2:05 AM MT). Research input pending from Research Digest (why MODO Booleans fail; OCCT BRepAlgoAPI and fuzzy options).

## Goal
Union, Cut and Intersect that feel like MODO (pick tool, drag, live preview) but don't fail. First use: placing the off-centre disc on the Blink bracket (`mvp/projects/blink-l-bracket.md`).

## Behaviour
- Pick a target body and a tool body, then choose Union, Cut or Intersect.
- **Live preview while dragging:** the tool body moves with gizmo or snapping, and the result previews. The preview may be lower fidelity, but the commit runs the full B-rep Boolean.
- On commit, run the real watertight and units check. If the result is invalid, don't commit: show why and keep the prior state (undo-safe).
- Snapping to faces, edges and centres, so the off-centre disc can be placed exactly. Numeric offset entry in mm.

## Reliability requirements (method TBD pending research)
- B-rep Booleans via OCCT (`BRepAlgoAPI_*`), not mesh Booleans.
- Handle coplanar faces and touching or near-touching geometry. The tolerance or fuzzy value is **TBD** (research to propose, Erik to approve).
- Validate inputs and outputs (`BRepCheck_Analyzer`). Failure is reported, never silent.
- Test cases (CTest): coplanar union, coplanar cut, tangent cylinder, disc on bracket at an off-centre position, and repeated drag and commit cycles. All results must be watertight.

## Performance
Preview frame rate and the max commit time on phones are TBD.

## Open TBDs for Erik
Fuzzy tolerance value; whether Intersect stays test-only (per `ui-redesign.md` it is test-only today); preview fidelity targets.
## Research findings (research/occt-wasm/booleans.md, 2026-10-21)
- Coplanar faces are the known failure case, and the bracket disc sits flush on the leg top.
- OCCT settings: SetFuzzyValue (mm value TBD); SetGlue(BOPAlgo_GlueShift) only for the flush disc on leg, never for the holes or any real intersection; SetNonDestructive so undo and re-drag work; SimplifyResult after the operation.
- Checks: BOPAlgo_ArgumentAnalyzer before the operation; BRepCheck_Analyzer plus ShapeFix_Shape after; then our watertight and units gate.
- Live drag: a see-through ghost of the tool body, updated once per frame. A live cut or union preview with manifold-3d (Apache-2.0, single-threaded WASM build) is optional and needs Erik's yes. three-bvh-csg is rejected.
- On failure: keep the last good shape, show the error, snap the tool body back, and keep Export disabled.
- Pilot to confirm the API names in a libcascade 3.1.0 test build.
- Still TBD: fuzzy tolerance, preview mesh coarseness, WASM Boolean timing, manifold-3d download size, Push/Pull scope.
## Chief decision (2026-10-21)
- MVP live drag: a see-through ghost while dragging. On release, the exact OCCT Boolean runs, then check and repair, then the watertight and units gate; roll back on any failure.
- manifold-3d stays out unless Erik asks to watch the cut or union happen live.
- Open for Erik: fuzzy tolerance (mm), Intersect as a user tool or test-only, phone preview speed target, ghost vs live preview.
