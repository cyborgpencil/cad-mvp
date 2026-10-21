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