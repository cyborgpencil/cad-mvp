# GUI plan (Fusion-style layout, Blender-style operations)

Status: a draft plan only, with no code yet. Owner: Doc Steward. References: Research Digest (open-source first). Coordinator: Chief.
Watertight and units checks stay a release gate on every export. They are no longer the main test focus.

## 0. Scope conflicts for Erik (unresolved, do not build until answered)
- C1. A parametric timeline reopens parametric history, which was cut from the MVP. Options: (a) cut it, (b) undo history shown as a timeline with no replay, or (c) full parametric replay. Erik decides.
- C2. Blender mesh operations (loop cut, knife, inset on arbitrary mesh, vertex grab) reopen freeform, which was also cut. On B-rep, most of these only have face, edge or body equivalents. Erik decides between a B-rep-only take and a separate mesh mode.
- C3. "Full suite like Fusion" is much bigger than the MVP. Erik needs to say which phases are MVP and which come after.
- C4. Chamfer, sphere, cone and intersect are still test-only until Erik answers (from the test matrix).
- C5. Is iPhone/Android touch MVP or post-MVP? TBD.
- C7. Sketch solver license: PlaneGCS WASM (@salusoft89/planegcs, LGPL, single maintainer) fits. SolveSpace (GPL-3.0) clashes with our LGPL-2.1 and is out unless Erik says otherwise.
- C8. Timeline via OCAF/TNaming would be an architecture change (ties to C1).
- C9. OCCT fillet and cut are added next to the existing mesh code, not replacing it (Erik's keep-finished-work rule in AGENTS.md). Current tests keep passing as they are; OCCT cases get their own expectations. The touch gesture map in section 5 is a proposal; Erik sets the UX spec.
- C6. Platform: the GUI targets the browser app (WebGL2 on Chrome for Windows, Android, iPhone). The Qt app is a native test harness only. Should Qt stay a real product? Erik decides.

## 1. Fusion-style layout
- Ribbon/toolbar with tabs per workspace (Sketch, Solid, Inspect, Export). Exact tab list TBD.
- Browser tree: bodies, sketches, construction planes, with visibility and isolate toggles.
- Timeline: blocked on C1.
- ViewCube with click-to-face/edge/corner views and a home view. three.js ViewHelper only draws axes, so a labeled cube is our own work.
- Marking menu: a radial menu on right-click or long press. Item list TBD.
- Inspector/properties panel (Fusion's own docs do not describe an "inspector"; layout TBD) for the selected feature's parameters and numeric fields, in the active units.

## 2. Blender-style operations (mapped to B-rep where possible)
| Operation | B-rep route (OCCT) | Mesh-only? | Notes |
|---|---|---|---|
| Extrude (face/sketch) | BRepPrimAPI_MakePrism (sketch) or BRepFeat_MakePrism (face push/pull) | No | Press-pull style |
| Inset | Offset face outline, then split | Partly | Exact behavior TBD. **Research Digest proposal, needs Erik's sign-off:** feasible as `BRepOffsetAPI_MakeOffset` on the face's outer wire (class present in the OCCT 8.0.1 reference) + `BRepAlgoAPI_Splitter` to split the face, then optional push/pull; edge cases: self-intersecting offsets, faces with holes. Sources: research/gui/README.md [C3], https://dev.opencascade.org/doc/refman/html/class_b_rep_offset_a_p_i___make_offset.html |
| Bevel | BRepFilletAPI_MakeFillet / MakeChamfer | No | Chamfer is test-only (C4) |
| Loop cut | Split by plane (BRepAlgoAPI_Splitter) | Mostly mesh | C2 |
| Knife | Split by a sketch curve (BRepAlgoAPI_Splitter) | Mostly mesh | C2 |
| Grab/rotate/scale gizmo | gp_Trsf on the body, with numeric entry (type a value like Blender's G X 10) | No | Body-level only unless C2 opens sub-element editing |
| Snapping | Vertex, edge midpoint, face center, grid | No | Grid size TBD |
| Selection modes | Vertex, edge, face, body (TopExp exploration) | No | Hotkeys 1-4 proposed, TBD |

## 3. Exploring the model
- Orbit, pan and zoom, with presets (front, top, right, iso) and zoom-to-fit and zoom-to-selection.
- Section planes: one movable clipping plane first, a capped section later.
- Measure: distance, angle, radius, area, volume, in the active units.
- Display modes: shaded, shaded plus edges, wireframe, x-ray.
- An isolate/hide tree from the browser.
- Undo/redo history with a visible list. Its depth is TBD, and it ties into C1.

## 4. Sketch tools and constraints
- Tools: line, rectangle, circle, arc, polygon, fillet, trim, offset, and dimension.
- Constraints: coincident, horizontal, vertical, parallel, perpendicular, equal, tangent, fixed, and dimensional. Proposed solver: PlaneGCS WASM (see C7). **Research Digest proposal, needs Erik's sign-off:** `@salusoft89/planegcs` 1.3.0 is FreeCAD's solver as WASM under LGPL, matching our LICENSE; risk: one small maintainer; SolveSpace is out (GPL-3.0). Sources: research/gui/README.md [S3][S4][S1].
- The mm/inch toggle shows values in the chosen unit. Internally everything stays mm, and export always writes unit="millimeter".

## 5. Input on Chrome (Windows, Android, iPhone)
- Mouse: proposed Fusion-like default bindings (orbit, pan, zoom). Exact mapping TBD. The Blender preset is optional.
- Pointer Events with touch-action: none on the canvas.
- Touch: one finger orbits, two fingers pan and pinch to zoom, and a long press opens the marking menu. Uses Pointer Events.
- Keyboard: shortcuts on desktop only. Touch has an on-screen numeric pad for gizmo entry.
- Performance targets (fps, model size) are TBD and need Erik's numbers.

## 6. Feasibility on OpenCASCADE in WASM
- B-rep operations (extrude, booleans, fillet, transforms, selection by topology) fit the current core.
- Mesh-style operations (loop cut, knife, freeform) have no clean B-rep equivalent. This is C2. Rule: every Blender-style tool gets a version on real faces and edges (push/pull, face inset, bevel as fillet or chamfer). Raw-mesh-only tools go to C2.
- Current state (Pilot, 2026-10-21): the Qt GUI does fillet and cut with project mesh code, not OCCT. Proposed: add OCCT B-rep fillet, chamfer, booleans and extrude alongside the existing mesh code (keep-finished-work rule, AGENTS.md); existing tests stay as they are and OCCT gets its own rows. Loop cut and knife stay mesh-style only if Erik opens C2.
- Proposed browser stack (MIT): three.js (TransformControls for gizmos, clipping planes for sections), camera-controls, three-mesh-bvh for picking. **Research Digest proposal, needs Erik's sign-off:** three.js on WebGL2, all MIT and actively maintained, covers gizmos, sections and fast picking; the labeled ViewCube is custom work. Sources: research/gui/README.md [O1]-[O6].
- WASM is single-threaded, so long OCCT operations run in a Web Worker to keep the UI responsive.
- Open risks: picking B-rep sub-elements from a tessellated view, WASM memory and thread limits on iPhone Safari-engine Chrome, and boolean speed.
- Sourced references: `research/gui/README.md` (Research Digest).

## 7. Phased milestones (each with its own test matrix)
Each phase still passes the watertight and units gate on export.
- P1 Viewer: layout shell, ViewCube, orbit/pan/zoom, display modes, browser tree, isolate/hide. Tests: UX flows such as open a part, orbit, isolate a body, and switch display modes; GUI screenshot tests against baselines.
- P2 Select and inspect: selection modes, measure, section plane, units toggle. Tests: measure a known edge from the test matrix (S1 is 40 mm), with mm and inch readouts both right.
- P3 Sketch: sketch tools and constraints, then extrude. Tests: draw a constrained rectangle, extrude it, export, and open it in Orca.
- P4 Modify: gizmos with numeric entry, snapping, fillet, booleans, undo/redo. Tests: test matrix O-cases driven through the GUI.
- P5 (blocked on C1 and C2): timeline, inset, loop cut, knife.

GUI test conventions: captures go to builds\screenshots\gui-<phase>-<flow>-<step>.png (gitignored). Approved baselines go to tests/gui/baselines/ (tracked, PNG binary). Pilot runs the captures on Z13. Proposed tool: Playwright screenshots on Desktop Chrome, Pixel and iPhone 13 (WebKit). Baselines must be made in the same environment the tests run in. The pixel-diff tolerance is TBD. **Research Digest proposal, needs Erik's sign-off:** Playwright `toHaveScreenshot()` with Desktop Chrome, Pixel and iPhone 13 (WebKit) projects, since it builds and compares baselines natively and emulates all three targets. Sources: research/gui/README.md [T1][T2].

## 8. Workbench tab redesign
Moved to mvp/ui-redesign.md (design only, 2026-10-21).

## Handoff
Grok Build plans and implements each phase once Erik approves its scope. Cursor does the interactive refinement. Erik reviews core diffs.