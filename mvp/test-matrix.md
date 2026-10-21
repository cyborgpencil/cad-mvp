# MVP Test Matrix

Purpose: prove the OpenCASCADE core and the GUI both work across MVP scope. Every case runs as a CTest case and as a GUI pass on Z13, and every case exports STL and 3MF.

Rules:
- Geometry uses OpenCASCADE (OCCT 8.0.1) solids and booleans (`BRepAlgoAPI_Fuse/Cut/Common`, `BRepFilletAPI_MakeFillet/MakeChamfer`). No mesh-only shortcuts.
- Units are millimeters. Dimensions below are test values chosen by the team, not product specs.
- Commit only passing tests. Report anything unverifiable as unverifiable.

## Checks on every case
1. Watertight and manifold: the existing checker passes on both STL and 3MF, and a read-back check passes.
2. Shell count matches the "Shells" column.
3. Volume is within tolerance of "Volume (mm3)". Tolerance: **TBD** (Research Digest to propose; Erik to approve).
4. Bounding box matches "BBox (mm)" within tolerance (**TBD**).
5. The 3MF has `unit="millimeter"`.
6. OrcaSlicer import reads back the same size (screenshot of the plate with size/object info, saved under `builds\screenshots\`).

## Shapes
| ID | Case | Definition | BBox (mm) | Volume (mm3) | Shells |
|---|---|---|---|---|---|
| S1 | Box | 40 x 30 x 20 | 40x30x20 | 24000 | 1 |
| S2 | Cylinder | r 10, h 20 | 20x20x20 | 2000pi = 6283.19 | 1 |
| S3 | Sphere | r 10 | 20x20x20 | 4000pi/3 = 4188.79 | 1 |
| S4 | Cone | base r 10, tip r 0, h 20 | 20x20x20 | 2000pi/3 = 2094.40 | 1 |
| S5 | Extruded rectangle | 30 x 20 sketch, extrude 10 | 30x20x10 | 6000 | 1 |
| S6 | Extruded circle | r 10 sketch, extrude 10 | 20x20x10 | 1000pi = 3141.59 | 1 |
| S7 | Extruded L-profile | 30 x 30 square minus 20 x 20 corner, extrude 10 | 30x30x10 | 5000 | 1 |
| S8 | Polygon with hole | 30 x 30 square with r 5 centered hole, extrude 10 | 30x30x10 | 9000 - 250pi = 8214.60 | 1 |
| S9 | Thin walls | 40x30x20 box minus 38x28x19 open-top cut (1 mm walls and floor) | 40x30x20 | 24000 - 20216 = 3784 | 1 |

## Operations
| ID | Case | Definition | BBox (mm) | Volume (mm3) | Shells |
|---|---|---|---|---|---|
| O1 | Union, overlapping | two 20 cubes, second at X+10 | 30x20x20 | 12000 | 1 |
| O2 | Union, touching (coplanar) | two 20 cubes, second at X+20 (shared face) | 40x20x20 | 16000 | 1 |
| O3 | Cut, open through-pocket | S1 minus 8x8 at X16 Y12, full height | 40x30x20 | 24000 - 1280 = 22720 | 1 |
| O4 | Cut, blind pocket | S1 minus 8x8x6 at X16 Y12, Z14 to 20 (open at top) | 40x30x20 | 24000 - 384 = 23616 | 1 |
| O5 | Internal void | S1 minus 8x8x6 at X16 Y12 Z7 (fully enclosed) | 40x30x20 | 23616 | 2 |
| O5b | Internal void, filleted | S1 with r 3 fillet on one 40 mm edge, then the O5 enclosed cut | 40x30x20 | 24000 - 9(1-pi/4)40 - 384 = 23538.74 | 2 |
| O6 | Intersect | 20 cube at origin with 20 cube at (10,10,10) | 10x10x10 | 1000 | 1 |
| O7 | Fillet, one edge | S1, r 3 on one 40 mm edge | 40x30x20 | 24000 - 9(1-pi/4)40 = 23922.74 | 1 |
| O8 | Fillet, multiple edges | S1, r 3 on the four 20 mm vertical edges | 40x30x20 | 24000 - 4(9)(1-pi/4)20 = 23845.49 | 1 |
| O9 | Chamfer, one edge | S1, 3 mm equal-distance on one 40 mm edge | 40x30x20 | 24000 - 180 = 23820 | 1 |
| O10 | Chamfer, multiple edges | S1, 3 mm on the four 20 mm vertical edges | 40x30x20 | 24000 - 360 = 23640 | 1 |
| O11 | Tiny feature near tolerance | S1 plus a 0.2 mm cube boss on the top face | 40x30x20.2 | 24000.008 | 1 |
| O12 | mm/inch toggle mid-edit | create 20 mm cube, toggle to inch (shows 0.787 in), edit edge to 1.000 in, toggle back (shows 25.4 mm), export | 25.4x25.4x25.4 | 16387.06 | 1 |

Notes:
- O5 has no fillet, so it expects 23616. The Qt run's 23536.9 came from a part filleted before the cut, which matches `mvp/create-export.md` ("the filleted box minus that pocket"). That is not a defect. Fillet-plus-cut combinations use their own formula.
- O11: expected behavior when a feature is below tolerance (keep, heal, or reject with a clear message) is **TBD**, for Erik to decide.
- O12 checks that stored values stay in mm and only the display converts (factor 25.4).

## Formula check (Research Digest, 2026-10-21)
All volume formulas above were re-derived by hand. No corrections were needed.
- S2/S6 pi r^2 h, S3 (4/3) pi r^3, S4 (1/3) pi r^2 h: correct for the stated sizes.
- S7: (900 - 400) x 10 = 5000. S8: (900 - 25pi) x 10 = 9000 - 250pi. S9: 38 x 28 x 19 = 20216, so 3784. All correct.
- O3: 8 x 8 x 20 = 1280. O4/O5: 8 x 8 x 6 = 384. O6: 10^3. All correct.
- Fillets: a radius-r fillet on a 90-degree edge removes r^2 - pi r^2/4 = r^2(1 - pi/4) per mm of edge. O7: 9(0.214602)(40) = 77.26, so 23922.74. O8: 4 x 9(0.214602)(20) = 154.51, so 23845.49. O5b: 24000 - 77.26 - 384 = 23538.74. All correct.
- Chamfers: an equal-distance chamfer d on a 90-degree edge removes d^2/2 per mm. O9: 4.5 x 40 = 180. O10: 4 x 4.5 x 20 = 360. Correct.
- O11: 0.2^3 = 0.008. O12: 25.4^3 = 16387.064. Correct.
- O5b vs the Qt run: the Qt mesh read 23536.9, 1.84 mm3 (0.008%) under the exact 23538.74. A tessellated fillet always reads low (see chord error below), so this gap is the expected sign and size, not a defect. It only proves the B-rep value once the B-rep check below is run.

## How each row is measured (all rows)
| Layer | Check | How |
|---|---|---|
| B-rep | Valid solid | `BRepCheck_Analyzer(shape).IsValid()` must be true. OCCT's Boolean guide requires valid arguments "in terms of BRepCheck_Analyzer" and post-processes results to keep that validity. |
| B-rep | Volume | `BRepGProp::VolumeProperties(shape, props)`, then `props.Mass()` against the Volume column. This is the exact value; compare it with the tight B-rep tolerance below. |
| B-rep | Shells | Count `TopAbs_SHELL` with `TopExp_Explorer`. O5/O5b expect 2 (outer plus void), the rest 1. |
| Mesh (STL and 3MF) | Watertight/manifold | After `BRepMesh_IncrementalMesh`, every edge is shared by exactly 2 triangles (no free edges, no non-manifold edges), orientation is consistent. This is the 3MF core spec's own rule for `type="model"` meshes. |
| Mesh | Shell count | Connected components of the triangle mesh equal the Shells column. |
| Mesh | Volume, bbox | Signed-tetrahedron volume and min/max of vertices, compared with the mesh tolerances below. |
| 3MF | Units | Read the file back with lib3mf and check the model unit is millimeter. Also check the raw XML has `unit="millimeter"`: the spec makes millimeter the default when the attribute is missing, so an explicit attribute is what this test asserts. |
| Orca | Size | Screenshot of the size readout; must match the BBox column within the mesh bbox tolerance. |

## Likely failure reasons for tricky rows
| ID | Why it can fail | Source |
|---|---|---|
| O2 (touching union) | The cubes share a face. OCCT treats shapes as interfering when their distance is within the sum of tolerances, so coincident faces become same-domain faces. A good result is one solid with the shared face removed (Boolean guide, "Two Solids that have overlapping faces": Fuse gives one new solid). Failure looks like 2 solids, a leftover internal face, or a non-manifold mesh. If tiny gaps appear, the fix to try is the fuzzy value (`SetFuzzyValue`, default `Precision::Confusion()`) or the Gluing option for coinciding arguments. | Boolean Operations guide |
| O3 (through-pocket) | The cut tool's top and bottom faces are coplanar with the box faces. Same same-domain-face handling as O2. Failure: a zero-thickness skin left over the pocket, or open edges. Making the tool taller than the box is the usual workaround but changes nothing in the expected volume. | Boolean Operations guide |
| O4, O6 | O4's tool top is coplanar with the box top; O6's cubes share face planes. Same risk as O2/O3. | Boolean Operations guide |
| O5, O5b | The void must come out as an inner shell, not a separate solid or a dropped cut. Failure: shell count 1 (void lost) or 2 solids. | Boolean Operations guide (solid splitting builds closed shells) |
| O11 (tiny feature) | A 0.2 mm boss is far above `Precision::Confusion()` (1e-7) but near typical mesh deflections. If the mesh linear deflection is set below shape tolerance, BRepMesh uses the shape tolerance instead. Features near the fuzzy value or the deflection can merge, vanish, or produce slivers. Expected behavior is TBD for Erik. | Boolean guide (fuzzy value); Mesh guide (deflection vs tolerance) |
| S9 (thin walls) | 1 mm walls are fine for OCCT but close to print limits; for the mesh, both wall faces are planar so no chord error. Failure risk is mainly coplanar faces at the open top (the cut's top face lies on the box top, same as O3). | Boolean Operations guide |
| S2-S4, S6, S8, O7, O8, O5b | Curved faces: the mesh is inscribed, so mesh volume and bbox read slightly low. Failure is only a tolerance-setting issue; see the proposal below. | Mesh guide (linear deflection) |
## Scope flags for Erik
Until Erik answers, chamfer (O9, O10), sphere (S3), cone (S4), and intersect (O6) run as test-only cases, not MVP features.

- Chamfer (O9, O10) was listed as out of scope in `prompts/wasm-occt-core.md`. Erik's matrix request includes it, so it needs his confirmation that chamfer is now in MVP scope.
- Sphere, cone, and intersect are also new compared with the WASM prompt's scope. Same confirmation needed.

## Outputs
- CTest: one test per ID, named `matrix_<ID>`.
- GUI pass on Z13: screenshot each operation and each Orca import into `builds\screenshots\<ID>-<step>.png`.
- Failures are posted in the CAD CAM MVP group. Only passing tests get committed.

## Proposed tolerances (Research Digest proposal, needs Erik's sign-off)
None of these numbers are Erik's specs. They are proposals until he approves them.

Mesh setting assumed: linear deflection d = 0.01 mm, angular deflection 0.5 rad, absolute (not relative). These are the values in OCCT's own `BRepMesh_IncrementalMesh` example; the Mesh guide says linear deflection "limits the distance between a curve and its tessellation". If the export uses another d, recompute the bands with the formulas below.

**Chord-error math.** A circle of radius r cut into chords with sagitta (max gap) d has half-angle per chord t where d = r(1 - cos t), so t is about sqrt(2d/r). Each chord leaves a circular segment of area about (2/3)(chord)(d). Summed around the circle, the lost area is about (2/3)(2 pi r)d = (4 pi/3) r d, which is a relative area loss of (4 pi r d/3)/(pi r^2) = **4d/(3r)**. For a sphere, the inscribed mesh sits at most d inside the surface over area 4 pi r^2, so the loss is at most 4 pi r^2 d, or **3d/r** of (4/3) pi r^3 (an upper bound). A quarter-round fillet of radius r loses about (2/3)(pi r/2)d = **pi r d/3 per mm of edge**. Meshes are inscribed, so curved cases always read low, never high.

| Check | Case type | Proposed tolerance | Example at d = 0.01 mm |
|---|---|---|---|
| B-rep volume | All rows | 1e-6 relative | BRepGProp is exact up to its integration accuracy |
| Mesh volume | Planar only (S1, S5, S7, S9, O1-O4, O5, O6, O9-O12) | 1e-6 relative (float rounding only) | 24000 +/- 0.024 mm3 |
| Mesh volume | Curved | mesh value between exact x (1 - 2B) and exact x (1 + 1e-6), where B is the row's chord bound; 2x margin | S2/S6 r 10: B = 4d/3r = 0.13%, band -0.27%. S3 r 10: B = 3d/r = 0.3%, band -0.6%. S4 cone r 10: B <= 0.13%, band -0.27%. S8 hole r 5: the hole shrinks, so volume reads high by up to (4 pi/3)(5)(0.01)(10) = 2.09 mm3 (0.026%); band +0.05%. O7: 40 pi d = 1.26 mm3 (0.005%), band -0.011%. O8: 80 pi d = 2.51 mm3, band -0.021%. O5b: same as O7. |
| BBox | Planar only | +/- 1e-4 mm per axis | 40.0000 +/- 0.0001 |
| BBox | Curved | +/- (d + 1e-4) mm per axis; may only shrink | S2: 20 x 20 within 0.0101 mm |
| Orca size | All | Orca's display rounding (check its readout precision) or the bbox tolerance, whichever is larger | TBD once the first screenshots show the readout precision |

Notes: the sign rule (curved meshes read low; holes make parts read high) is a cheap extra check. OCCT ignores a linear deflection smaller than the shape tolerance and uses the tolerance instead (Mesh guide), so d must stay above the part's tolerance.

**Tiny-feature behavior (O11): TBD for Erik.** Options:
1. Keep: export the feature as modeled, even if it prints poorly.
2. Heal: merge or remove features below a threshold (for example the fuzzy value or d) and tell the user what changed.
3. Reject with a message: block export and name the feature and its size.

## Sources (fetched 2026-10-21)
- OCCT Boolean Operations user guide (interference within summed tolerances, fuzzy value with default `Precision::Confusion()`, Gluing option, arguments valid "in terms of BRepCheck_Analyzer", overlapping-face fuse cases): https://dev.opencascade.org/doc/overview/html/specification__boolean_operations.html
- OCCT Mesh user guide (`BRepMesh_IncrementalMesh`, linear and angular deflection, example values 0.01 and 0.5, deflection below shape tolerance is replaced by the tolerance): https://dev.opencascade.org/doc/overview/html/occt_user_guides__mesh.html
- 3MF Core Specification 1.4.0 (`unit` attribute on `<model>`, values micron/millimeter/centimeter/inch/foot/meter, default millimeter; manifold-edge and orientation rules for model meshes): https://raw.githubusercontent.com/3MFConsortium/spec_core/master/3MF%20Core%20Specification.md
- lib3mf v2.5.0 documentation (official 3MF read/write library; per-language API pages): https://lib3mf.readthedocs.io/en/latest/
