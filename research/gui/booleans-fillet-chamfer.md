# Booleans, fillet and chamfer: MODO lessons + OCCT for the L-bracket (2026-10-21)

Owner: MVP Research Digest. Scope: research only, no src changes. Related: [occt-wasm/booleans.md](../occt-wasm/booleans.md), [gui/modo-tools.md](modo-tools.md).

## 1. MODO interactive Booleans (MeshFusion)

**What made them good (per Foundry docs/users)**
- Live, non-destructive: a Fusion Item keeps the source meshes; deleting the Fusion Item keeps sources. https://modosdk.foundry.com/modo/12.0/content/help/pages/meshfusion/mf_fusion_item.html
- Intersection "strips" give an editable blend at the join; width and smoothing can be adjusted to soften the join. https://learn.foundry.com/modo/content/help/pages/meshfusion/mf_introduction.html
- Edges weighted 100% can be converted to strips automatically (closed, non-crossing edges only). https://modosdk.foundry.com/modo/content/help/pages/meshfusion/mf_strips.html
- Users: "great for certain tasks", used on production pieces. https://polycount.com/discussion/156821/mesh-fusion

**Documented problems / limits**
- Performance: docs ship Deferred Update, Boolean+Mesh caching, Draft Union and Design Mode specifically because "continuous updates are not smooth" on complex meshes; Draft mode is fastest but not for final output. https://modosdk.foundry.com/modo/17.1/content/help/pages/meshfusion/mf_fusion_item.html
- Users: "gets heavy and slow pretty quickly". https://polycount.com/discussion/156821/mesh-fusion
- Topology: n-gons, 3-edge poles etc. need subdivision; those topologies stay incompatible at zero subdivision. https://learn.foundry.com/modo/content/help/pages/meshfusion/mf_zero_subdiv_workflow.html
- Stability/units: a user reported repeated crashes in MODO 9 while working in millimetres at small scale; advice was to freeze scale. https://community.foundry.com/discuss/topic/129597/15-crashes-with-meshfusion-in-30-minutes
- Product status: Foundry wound down Modo development after 17.1 (announced 2024-11-07; 17.1v1 = final release, 2024-11-26). https://www.foundry.com/news-and-awards/foundry-winds-down-modo-development , https://learn.foundry.com/modo/17.1v1/content/release_notes/17/modo_17.1v1_releasenotes.html
- "Failed": no source found saying MeshFusion itself failed. The product was discontinued for business focus reasons per Foundry; nothing ties that to Booleans. Treat "failed" as unsourced.

**Takeaway for MVP:** copy the live/non-destructive model (keep source solids, recompute result) and the "draft while dragging, exact on release" pattern. Our OCCT B-rep avoids the mesh-subdivision topology limits, and our mm units gate guards against the scale problem reported above.

## 2. OCCT fillet, chamfer, booleans, checks

Refs: Modeling Algorithms guide https://dev.opencascade.org/doc/overview/html/occt_user_guides__modeling_algos.html ; Boolean Operations guide https://dev.opencascade.org/doc/overview/html/specification__boolean_operations.html ; Shape Healing guide https://dev.opencascade.org/doc/overview/html/occt_user_guides__shape_healing.html

- **BRepFilletAPI_MakeFillet(shape)**: `Add(radius, edge)` (also variable-radius forms), then `Build()` / `Shape()`. `IsDone()` false means no result; `Shape()` then throws `StdFail_NotDone`. Diagnostics: `NbFaultyContours`, `FaultyContour`, `StripeStatus`, `HasResult`/`BadShape` (partial result). https://dev.opencascade.org/doc/refman/html/class_b_rep_fillet_a_p_i___make_fillet.html
- **BRepFilletAPI_MakeChamfer(shape)**: `Add(dist, edge)` symmetric; `Add(d1, d2, edge, face)` or `AddDA(dist, angle, edge, face)` for asymmetric, where the face picks the reference side. https://dev.opencascade.org/doc/refman/html/class_b_rep_fillet_a_p_i___make_chamfer.html
- **Failure modes** (guide, fillets section): radius/distance too large for adjacent faces, or edges where fillets interfere, make the build fail. OCCT gives no documented max radius; we must catch and report. Guide above.
- **Booleans**: `BRepAlgoAPI_Fuse/Cut/Common(a, b)`; check `IsDone()` and `HasErrors()`/`DumpErrors()`; options `SetFuzzyValue`, `SetNonDestructive`, `SetGlue`, `SimplifyResult` (unify coplanar faces after Fuse). https://dev.opencascade.org/doc/refman/html/class_b_rep_algo_a_p_i___boolean_operation.html
- **Gate**: `BRepCheck_Analyzer(shape).IsValid()` for topology/geometry validity https://dev.opencascade.org/doc/refman/html/class_b_rep_check___analyzer.html ; `ShapeAnalysis_FreeBounds` returns closed/open free-edge wires; zero free bounds = closed (watertight) shell. https://dev.opencascade.org/doc/refman/html/class_shape_analysis___free_bounds.html
- **libcascade 3.1.0 bindings: VERIFIED.** `npm pack libcascade@3.1.0`, `dist/types.d.ts` declares classes BRepFilletAPI_MakeFillet, BRepFilletAPI_MakeChamfer, BRepAlgoAPI_Fuse, BRepAlgoAPI_Cut, BRepAlgoAPI_Common, BRepCheck_Analyzer, ShapeAnalysis_FreeBounds (checked 2026-10-21). Package is OCCT 8.0.1 + native wasm exceptions (decode via `oc.getExceptionMessage`); 3.1.0 makes `delete()`/`using` really free memory, so do not delete handles still in use. https://www.npmjs.com/package/libcascade , https://github.com/taucad/opencascade.js/blob/main/CHANGELOG.md , fillet example: https://libcascade.vercel.app/docs/package/getting-started/quick-start-npm
- Individual method signatures were checked in `builds/libcascade/pkg/package/dist/types.d.ts` (libcascade 3.1.0) and then called from Node. Confirmed: `BRepAlgoAPI_Fuse` / `Cut` / `Common` `constructor(S1, S2)`, `SimplifyResult(unifyEdges?, unifyFaces?, angularTol?)` on fuse, `IsDone()`, `HasErrors()`, `Shape()`; `BRepFilletAPI_MakeFillet` `constructor(S)` and `Add(radius, edge)` then `Build()`; `BRepFilletAPI_MakeChamfer` `constructor(S)` and `Add(distance, edge)` then `Build()`. `Shape()` throws `StdFail_NotDone` (`BRep_API: command not done`) when `IsDone()` is false. `BRepBuilderAPI_Copy(shape, true, false)` then `Shape()` stays valid after the algorithm is deleted. A radius of 100 mm on the placeholder L-bracket returns `IsDone() === false`.

## 3. L-bracket application (PROPOSAL, not spec)

PROPOSAL sequence, all numbers TBD for Erik (see projects/blink-mount.md for mount context):
1. Box A (base leg) `BRepPrimAPI_MakeBox(L1, W, T)`: L1, W, T = TBD mm.
2. Box B (upright leg) `BRepPrimAPI_MakeBox(T, W, H)`: H = TBD mm; placement/overlap = TBD.
3. `BRepAlgoAPI_Fuse(A, B)` + `SimplifyResult()`; require IsDone and no errors.
4. Pick the inner (concave) corner edge; how it is picked (UI edge select vs. geometric query) = TBD. `MakeFillet.Add(R_inner, edge)`; R_inner = TBD (must be < T, guard in code).
5. `MakeChamfer` on outer edges: which edges and distance = TBD.
6. Gate: BRepCheck_Analyzer valid + FreeBounds zero open wires (watertight) + units locked to mm; then mesh to STL/3MF. Fail = show error, keep last good shape.

## 4. Next steps

**Grok Build (first)**
- Add C++ ops `fuse`, `filletEdges(r, edgeIds)`, `chamferEdges(d, edgeIds)` wrapping IsDone/StdFail_NotDone into a clean error, with the gate after every op.
- Tests: box+box fuse passes gate; oversize fillet fails cleanly (no crash, prior shape kept).
- Keep non-destructive history (sources + op list) so params can be re-applied, MODO-style.

**Cursor (second)**
- Wire edge pick (Edge mode) -> fillet/chamfer panel with radius/distance inputs, values TBD until Erik sets them.
- Erik reviews the C++ diff.

## Open TBDs for Erik
- L-bracket dims (L1, W, T, H), inner fillet radius, chamfer edges + distance.
- Inner-edge selection method (user pick vs auto).
- Whether live drag preview is needed for fillet, or apply-on-release only.
