# Healing: B-Rep and mesh repair

Checked 2026-10-20.

## Findings
- `BRepCheck_Analyzer::IsValid` checks a shape's topology, edge parameterization, wire and face orientation, and that the shells of a solid are closed. [1]
- The ShapeFix package repairs shapes that break OCCT rules (missing or deviating curves, tolerances, wire connections, self-intersecting wires, small edges). It runs ShapeAnalysis itself before fixing. [2][3]
- `BRepMesh_IncrementalMesh` tessellates B-Rep. A valid closed solid is expected to give a watertight mesh, but BRepMesh does not verify that itself. Check `GetStatusFlags()` and run an independent mesh check. [4][5]
- Manifold (elalish/manifold, Apache-2.0, C++ with a WASM build) guarantees manifold output and can merge small defects on import. It's a candidate for the mesh-side check and repair. [6]

## Pipeline proposal (for Erik to confirm)
Shape, then BRepCheck, then ShapeFix if invalid, then BRepCheck again, then BRepMesh (check status flags), then the units gate, then export. A BRepCheck failure rolls the op back; Export is gated on units only (02:17 rule), and no watertight check blocks it.

## Gaps / TBD
- Tessellation tolerances (linear and angular deflection): TBD for Erik.
- Whether to adopt Manifold or write our own edge-manifold check: TBD.

## Status (2026-10-20)

`src/solid` is our own triangle edge check for an in-memory mesh. Manifold and ShapeFix stay TBD. The check does not repair anything.

## Next steps
1. Grok Build: write tests in tests\ that feed known-bad shapes through the pipeline and assert that export is blocked or repaired.

## Sources
1. https://occt3d.com/dev/doc/refman/html/class_b_rep_check___analyzer.html
2. https://occt3d.com/dev/doc/refman/html/class_shape_fix.html
3. https://occt3d.com/dev/doc/overview/html/occt_user_guides__shape_healing.html
4. https://occt3d.com/dev/doc/refman/html/package_brepmesh.html
5. https://occt3d.com/dev/content/questions-brepmeshincrementalmesh/
6. https://github.com/elalish/manifold