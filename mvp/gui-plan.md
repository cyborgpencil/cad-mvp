# GUI plan (Fusion-style layout, Blender-style operations)

Status: a draft plan only, with no code yet. Owner: Doc Steward. References: Research Digest (open-source first). Coordinator: Chief.
Watertight and units checks stay a release gate on every export. They are no longer the main test focus.

## 0. Scope conflicts for Erik (unresolved, do not build until answered)
- C1. A parametric timeline reopens parametric history, which was cut from the MVP. Options: (a) cut it, (b) undo history shown as a timeline with no replay, or (c) full parametric replay. Erik decides.
- C2. Blender mesh operations (loop cut, knife, inset on arbitrary mesh, vertex grab) reopen freeform, which was also cut. On B-rep, most of these only have face, edge or body equivalents. Erik decides between a B-rep-only take and a separate mesh mode.
- C3. "Full suite like Fusion" is much bigger than the MVP. Erik needs to say which phases are MVP and which come after.
- C4. Chamfer, sphere, cone and intersect are still test-only until Erik answers (from the test matrix).
- C5. Is iPhone/Android touch MVP or post-MVP? TBD.
- C6. Platform: the GUI targets the browser app (WebGL2 on Chrome for Windows, Android, iPhone). The Qt app is a native test harness only. Should Qt stay a real product? Erik decides.

## 1. Fusion-style layout
- Ribbon/toolbar with tabs per workspace (Sketch, Solid, Inspect, Export). Exact tab list TBD.
- Browser tree: bodies, sketches, construction planes, with visibility and isolate toggles.
- Timeline: blocked on C1.
- ViewCube with click-to-face/edge/corner views and a home view.
- Marking menu: a radial menu on right-click or long press. Item list TBD.
- Inspector/properties panel for the selected feature's parameters and numeric fields, in the active units.

## 2. Blender-style operations (mapped to B-rep where possible)
| Operation | B-rep route (OCCT) | Mesh-only? | Notes |
|---|---|---|---|
| Extrude (face/sketch) | BRepPrimAPI_MakePrism, then fuse or cut | No | Press-pull style |
| Inset | Offset face wire, then imprint | Partly | Feasibility TBD (Research) |
| Bevel | BRepFilletAPI_MakeFillet / MakeChamfer | No | Chamfer is test-only (C4) |
| Loop cut | Face split (BRepFeat_SplitShape) | Mostly mesh | C2 |
| Knife | Section/split by a sketch curve | Mostly mesh | C2 |
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
- Constraints: coincident, horizontal, vertical, parallel, perpendicular, equal, tangent, fixed, and dimensional. The solver choice is TBD (Research, open source first).
- The mm/inch toggle shows values in the chosen unit. Internally everything stays mm, and export always writes unit="millimeter".

## 5. Input on Chrome (Windows, Android, iPhone)
- Mouse: proposed Fusion-like default bindings (orbit, pan, zoom). Exact mapping TBD. The Blender preset is optional.
- Touch: one finger orbits, two fingers pan and pinch to zoom, and a long press opens the marking menu. Uses Pointer Events.
- Keyboard: shortcuts on desktop only. Touch has an on-screen numeric pad for gizmo entry.
- Performance targets (fps, model size) are TBD and need Erik's numbers.

## 6. Feasibility on OpenCASCADE in WASM
- B-rep operations (extrude, booleans, fillet, transforms, selection by topology) fit the current core.
- Mesh-style operations (loop cut, knife, freeform) have no clean B-rep equivalent. This is C2. Rule: every Blender-style tool gets a version on real faces and edges (push/pull, face inset, bevel as fillet or chamfer). Raw-mesh-only tools go to C2.
- Current state (Pilot, 2026-10-21): the Qt GUI does fillet and cut with project mesh code, not OCCT. Proposed: move fillet, chamfer, booleans and extrude to OCCT B-rep. Loop cut and knife stay mesh-style only if Erik opens C2.
- Open risks: rendering stack (three.js or similar, TBD by Research), picking B-rep sub-elements from a tessellated view, WASM memory and thread limits on iPhone Safari-engine Chrome, and boolean speed.
- Sourced references: `research/gui/README.md` (Research Digest).

## 7. Phased milestones (each with its own test matrix)
Each phase still passes the watertight and units gate on export.
- P1 Viewer: layout shell, ViewCube, orbit/pan/zoom, display modes, browser tree, isolate/hide. Tests: UX flows such as open a part, orbit, isolate a body, and switch display modes; GUI screenshot tests against baselines.
- P2 Select and inspect: selection modes, measure, section plane, units toggle. Tests: measure a known edge from the test matrix (S1 is 40 mm), with mm and inch readouts both right.
- P3 Sketch: sketch tools and constraints, then extrude. Tests: draw a constrained rectangle, extrude it, export, and open it in Orca.
- P4 Modify: gizmos with numeric entry, snapping, fillet, booleans, undo/redo. Tests: test matrix O-cases driven through the GUI.
- P5 (blocked on C1 and C2): timeline, inset, loop cut, knife.

GUI test conventions: captures go to builds\screenshots\gui-<phase>-<flow>-<step>.png (gitignored). Approved baselines go to tests/gui/baselines/ (tracked, PNG binary). Pilot runs the captures on Z13. The pixel-diff tolerance is TBD, and so is the screenshot tool (Research).

## Handoff
Grok Build plans and implements each phase once Erik approves its scope. Cursor does the interactive refinement. Erik reviews core diffs.