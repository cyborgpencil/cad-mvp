# Booleans: why mesh Booleans fail (Modo) and how OCCT 8.0.1 handles them, plus live preview (2026-10-21)

## Why Modo's Booleans fail (polygon mesh)
- Modo's own prerequisites: no coincident (non-manifold) verts, edges or faces at the same position, no floating verts, and both meshes watertight with volume. Run Mesh Cleanup first. [1]
- Results often have n-gons that pinch on SubD and need manual cleanup. Modo suggests Edge Bevel on the new edges, or Axis/Solid Drill instead. [1]
- MeshFusion is more advanced (live update, blends) but wants quads. N-gons in seams degrade the Fusion strips. [2]
- Coplanar/coincident faces are a common failure cause in other mesh and CAD tools too (FreeCAD forum: "coplanar faces causing issues"; run BOPCheck). [3]
- Our bracket hits this: the disc's bottom face is coplanar with the leg's top face, and holes through the leg share planes with its faces.

## How OCCT avoids it (B-rep, tolerance-based) [4]
- API: `BRepAlgoAPI_Fuse` / `_Cut` / `_Common`, all built on `BRepAlgoAPI_BooleanOperation`. Inputs are Objects and Tools groups.
- Shapes interfere within the sum of their tolerances, not exact equality, so touching faces become "same domain" faces instead of slivers.
- Inputs must be valid per `BRepCheck_Analyzer`, not self-interfered, and C1-continuous. `BOPAlgo_ArgumentAnalyzer` is the pre-check. [4]
- `SetFuzzyValue(tol)`: extra tolerance for "touching and near-coincident, misaligned entities", e.g. gaps or embeddings. The default is Precision::Confusion. The doc example uses 1.e-5. Our value: TBD, set relative to our mm units and tested.
- `SetGlue(BOPAlgo_GlueShift)` is for partial coincidence and `BOPAlgo_GlueFull` for full coincidence. Glue is a speed-up only for shapes that overlap with no real intersections. It "cannot be used on shapes having real intersections" or the result can be wrong. So use it for disc-on-leg contact only, never for holes that cut through.
- `SetNonDestructive(true)`: inputs stay untouched (no tolerance growth or added p-curves). We need this so the user can undo or re-drag.
- `SimplifyResult()` runs `ShapeUpgrade_UnifySameDomain` and merges split coplanar faces after Fuse. That gives clean faces for fillet/chamfer.
- Errors: check `HasErrors()` / `HasWarnings()` after `Build()`.
- Afterwards: `BRepCheck_Analyzer` on the result, `ShapeFix_Shape` if it's invalid, then our watertight + units check before Export.
- Open solids: OCCT says results "cannot always be guaranteed", so reject open input (our watertight check gates this).
- Bound in libcascade 3.1.0 `api-reference.json` (grep, 2026-10-21) [5]: BRepAlgoAPI_Fuse, BRepAlgoAPI_Cut, BRepAlgoAPI_Common, BRepAlgoAPI_BooleanOperation, SetFuzzyValue, SetGlue, BOPAlgo_GlueShift, BOPAlgo_GlueFull, SetNonDestructive, BOPAlgo_ArgumentAnalyzer, BRepCheck_Analyzer, ShapeFix_Shape, ShapeUpgrade_UnifySameDomain, HasErrors, SimplifyResult, SetUseOBB and SetRunParallel are all present. The grep matched names only; method-to-class binding isn't verified, so test them in a smoke build.

## Live preview while dragging the disc (single-threaded WASM)
- Problem: an exact OCCT Boolean plus remesh on every pointer move blocks the only thread. Timing on our model: TBD, measure it.
- Option A, manifold-3d (Apache-2.0, npm, WASM in any modern browser). It guarantees manifold output from manifold triangle-mesh input and returns an error status on non-manifold input. It runs single-threaded by pipelining. Its README warns against `MANIFOLD_PAR` in emscripten (memory corruption risk). JS objects need manual `delete()`. Version 3.5.4 on npm. [6][7][8]
- Option B, three-bvh-csg (MIT, three.js). It's fast but described as experimental, and coplanar triangles can be a "large performance cost", which is exactly our case. [9][10]
- Option C, no CSG during drag: show the disc as a ghost mesh moved by a transform, with the exact result on release. Cheapest.
- During drag also: throttle to animation frames, and use a coarser `BRepMesh_IncrementalMesh` deflection for preview tessellation. Deflection values TBD.

## Verdict
- Preview: Option C (ghost transform) by default. Add manifold-3d mesh CSG only if Erik wants to see the cut or union during drag. Preview is visual only and never exported.
- Final: exact OCCT Boolean on mouse-up (pointerup) with NonDestructive on, Fuzzy (TBD value), GlueShift only for coplanar contact, then SimplifyResult, BRepCheck/ShapeFix, and the watertight + units gate.

## Failure UX
- Keep the last valid shape. Never replace it with a failed or invalid result.
- Show an inline error naming the cause (ArgumentAnalyzer or HasErrors text), and snap the tool back to its last good position.
- Offer "retry with fuzzy tolerance" (TBD steps). Export stays disabled until the check passes.

## Gaps / TBD
Teal-vs-orange (see `../gui/modo-tools.md`), fuzzy tolerance in mm, preview deflection, Boolean timing in WASM, manifold-3d wasm size (TBD), embind method signatures in libcascade.

## Sources
1. https://learn.foundry.com/modo/current/content/help/pages/modeling/edit_geometry/boolean.html
2. https://learn.foundry.com/modo/current/content/help/pages/meshfusion/mf_introduction.html
3. https://forum.freecad.org/viewtopic.php?t=80945
4. OCCT 8.0.1 Boolean Operations user guide: https://dev.opencascade.org/doc/overview/html/specification__boolean_operations.html
5. https://unpkg.com/libcascade@3.1.0/dist/api-reference.json
6. https://github.com/elalish/manifold
7. https://www.npmjs.com/package/manifold-3d
8. https://manifoldcad.org/docs/jsapi/documents/Using_Manifold.html
9. https://github.com/gkjohnson/three-bvh-csg
10. https://github.com/gkjohnson/three-bvh-csg/issues/199
