# GUI research note: Fusion-style layout, Blender-style ops, browser target

Research Digest, 2026-10-21. Plan input only, no code. Feeds `mvp/gui-plan.md` (owned by Doc Steward). The GUI target is the **browser app only** (C++ + OpenCASCADE 8.0.1 -> Emscripten WASM, single-threaded, WebGL2; Chrome on Windows, Android, iPhone, where iPhone Chrome uses WebKit). The Qt `solid_view` is a native test harness only. Watertight + `unit="millimeter"` checks stay as an export gate. License and activity data checked 2026-10-21 via the GitHub API.

## 1. Fusion layout reference [A1-A5]

- **Toolbar**: workspace menu + tabs of grouped tools; contextual tabs (e.g. Sketch) and contextual environments (e.g. Form) swap tabs while active [A1].
- **Browser**: tree of components, bodies, sketches, origins, joints, construction geometry, with visibility toggles [A1][A2].
- **Timeline**: lists operations; play/step, right-click to edit, drag to reorder (Parametric Modeling mode only) [A1][A3].
- **ViewCube**: drag to orbit, click face for ortho view, corner for iso, Home; right-click for ortho/perspective and size [A4].
- **Marking menu**: right-click radial menu; Design default ring is Repeat, PressPull, Redo, Hole, Sketch, Move/Copy, Undo, Delete; second ring of 8 sketch tools; context menu with Isolate/Unisolate and navigation [A5].
- **Inspector/properties**: Fusion uses per-command dialogs; no single Autodesk page fetched names an "inspector" panel, so treat it as our design choice (TBD).

Open-source browser parts (all checked 2026-10-21):

| Part | Use | License | Activity |
|---|---|---|---|
| three.js [O1] | WebGL2 renderer, OrbitControls/TrackballControls, `TransformControls` (mode translate/rotate/scale) [O2], `ViewHelper` axes helper [O3], clipping planes [O4] | MIT | last push 2026-10-20 MT, ~116.7k stars |
| camera-controls [O5] | CAD-like orbit/dolly/pan with transitions | MIT | push 2026-10-20 MT, ~2.4k stars |
| three-mesh-bvh [O6] | fast raycast picking of faces/edges on big meshes | MIT | push 2026-10-18 MT, ~3.5k stars |
| drei [O7] | GizmoHelper/GizmoViewcube (React-only; use only if UI is React) | MIT | push 2026-10-20 MT, ~10k stars |

Note: `ViewHelper` is an axes helper, not a Fusion-style labeled cube; a clickable labeled cube is a small custom component or drei's GizmoViewcube.

## 2. Blender operations reference, with a B-rep version for each [B1-B9]

| Blender tool | Manual | B-rep equivalent (works on real faces/edges) | OCCT API |
|---|---|---|---|
| Extrude region | [B1] | Push/pull a planar face or extrude a sketch profile | `BRepPrimAPI_MakePrism`, `BRepFeat_MakePrism` [C2] |
| Inset faces | [B2] | Offset the face's boundary wire inward and imprint it, then push/pull | wire offset + split (`BRepAlgoAPI_Splitter` [C3]); exact UX TBD |
| Bevel (edge) | [B3] | Edge fillet or chamfer | `BRepFilletAPI_MakeFillet`, `BRepFilletAPI_MakeChamfer` [C2] |
| Loop cut | [B4] | Split a face/body with a plane (no edge-loop topology on B-rep) | `BRepAlgoAPI_Splitter` [C3], `BRepAlgoAPI_Section` [C2] |
| Knife | [B5] | Imprint a sketch curve onto a face (split face) | `BRepAlgoAPI_Splitter` [C3] |
| Grab/rotate/scale + numeric entry | [B6] | Move/rotate a body or face; type exact mm/deg values | gp_Trsf transforms; face-move via `BRepFeat_MakePrism` |
| Snapping | [B7] | Snap to vertex, edge midpoint, face, grid | app-side, over BVH picking [O6] |
| Select modes vertex/edge/face | [B8] | Vertex/edge/face/body picking on B-rep sub-shapes | TopExp map index -> triangle IDs |
| Shell / thickness (related) | — | Hollow a body | `BRepOffsetAPI_MakeThickSolid` [C2] |

**Mesh-only (scope conflict for Erik)**: free vertex dragging, edge-loop slide, subdivision, sculpt, per-vertex Blender bevel/inset on triangle meshes. These need the freeform editing cut from the MVP.

## 3. Exploring the model

- Orbit/pan/zoom + presets: OrbitControls/camera-controls [O1][O5]; ViewCube behaviour per [A4].
- Section planes: three.js `material.clippingPlanes` / `renderer.localClippingEnabled` example [O4]. Display-only; a true OCCT section curve is `BRepAlgoAPI_Section` [C2].
- Measure: distance/angle from picked B-rep vertices/edges (BVH pick [O6]); OCCT computes exact values.
- Display modes: shaded, shaded+edges, wireframe, transparent (three.js materials; Fusion's Navigation Bar has display settings [A1]).
- Isolate/hide: browser-tree visibility [A2] and Isolate in marking-menu context [A5].
- Undo/redo: OCAF offers multi-level undo/redo via transactions [C1]; alternative is an app command stack. Choice TBD.

## 4. Sketching and constraints

| Solver | License | WASM/JS | Notes |
|---|---|---|---|
| SolveSpace `slvs` library [S1][S2] | GPL-3.0 (website says GPLv3; commercial licensing on request) | repo has `src/slvs/jslib.cpp` (Emscripten bindings); npm `slvs` 3.1.0-dev.14 | **GPL conflicts with the repo's LGPL-2.1 LICENSE** — flag |
| FreeCAD PlaneGCS via `@salusoft89/planegcs` [S3][S4] | LGPL-2.1 (npm says LGPL-2.0-or-later) | WASM build + wrapper, npm 1.3.0; push 2026-10-05 MT, ~108 stars | License-compatible; small single maintainer |

Existing Qt sketch tools: line, rectangle, circle, distance, radius, horizontal, vertical, coincident. mm/inch toggle: keep stored mm, display x25.4 (matches `mvp/units.md`).

## 5. Touch and mouse on Chrome

- Use Pointer Events (one model for mouse, pen, touch) with `setPointerCapture()` for drags [W1].
- Set `touch-action: none` on the canvas so the browser does not pan/zoom it; `manipulation`/`pinch-zoom` values exist for UI areas [W2].
- Multi-touch gesture tracking (pinch, two-finger pan) via pointer caches [W3].
- If touch events are used, calling `preventDefault()` suppresses emulated mouse events [W4].
- Proposed map (TBD with Erik): 1 finger orbit, 2 finger pan + pinch zoom, long-press = marking menu (touch has no right-click).
- iOS: iPhone Chrome runs WebKit, so test on WebKit too (Playwright `iPhone 13` device runs WebKit [T2]). No specific WebKit quirk list was fetched; verify on device.

## 6. Feasibility on OpenCASCADE (WASM)

- Every row in section 2's B-rep column is a documented OCCT algorithm [C2][C3]. These are B-rep ops, so the watertight gate runs on the tessellated result.
- **Move to OCCT B-rep**: today's Qt fillet (`fillet_box_edge`) and cut are the team's own mesh code. Recommend fillet/chamfer -> `BRepFilletAPI_*`, cut/union -> `BRepAlgoAPI_*`, extrude -> `BRepPrimAPI_MakePrism`, then tessellate for display and STL/3MF.
- **History**: OCCT has OCAF; `TNaming_NamedShape` stores old/new shape pairs (shape evolution) and supports topological naming, plus transaction undo/redo [C1]. This is the building block for a timeline but is not a ready Fusion-style timeline.
- WASM: single-threaded build means long fillets/booleans block the UI unless run in a Worker (Worker use is TBD; not measured).

## 7. Scope conflicts for Erik (flagged, not resolved)

1. Timeline with edit/reorder reopens **parametric history** (cut from MVP).
2. Blender mesh-only ops (free vertex drag, loop slide, subdivision, sculpt) reopen **freeform editing** (cut from MVP).
3. Full Fusion suite (workspaces, Form, Sheet Metal, CAM, Simulation) far exceeds design-to-print.
4. SolveSpace solver is GPL-3.0 vs repo LGPL-2.1.
5. OCAF/TNaming adoption is an architecture change for undo and naming.
6. Moving fillet/cut from mesh code to OCCT changes the existing test-matrix expectations (e.g. O5b).
7. Touch gesture map and long-press marking menu are new UX specs only Erik can set.

## 8. GUI screenshot and UX test tools

- Playwright `expect(page).toHaveScreenshot()` makes baselines on first run, compares later; rendering varies by OS/GPU/headless, so generate baselines in the same environment [T1].
- Device emulation: `devices['Desktop Chrome']`, `devices['iPhone 13']` (WebKit), and Pixel devices for Android-sized Chromium [T2].
- Layout: baselines in `tests/gui/baselines/` (git-tracked), new captures in `builds/screenshots/`. Use fixed viewport, deterministic camera, disabled animations.
- UX flows to script: sketch rectangle -> extrude -> fillet edge -> section -> measure -> toggle inch -> export, asserting the watertight gate line passes.

## Sources (fetched 2026-10-21)

- [A1] Fusion interface (desktop): https://help.autodesk.com/cloudhelp/ENU/Fusion-GetStarted/files/GS-THE-FUSION-INTERFACE.htm
- [A2] Perform basic tasks: https://help.autodesk.com/cloudhelp/ENU/Fusion-GetStarted/files/GS-BASIC-OPERATIONS.htm
- [A3] Use the Timeline: https://help.autodesk.com/view/fusion360/ENU/?contextId=LP-STEPS-P13N-SNP-GS-OTH-CRD-2
- [A4] ViewCube reference (PT-BR page): https://help.autodesk.com/cloudhelp/PTB/Fusion-GetStarted/files/GS-VIEWCUBE.htm
- [A5] Marking menu reference: https://help.autodesk.com/cloudhelp/ENU/Fusion-GetStarted/files/GUID-6514ABC1-CB75-4F0B-AB0E-316FAD36BA93.htm
- [B1] https://docs.blender.org/manual/en/latest/modeling/meshes/tools/extrude_region.html
- [B2] https://docs.blender.org/manual/en/latest/modeling/meshes/editing/face/inset_faces.html
- [B3] https://docs.blender.org/manual/en/latest/modeling/meshes/editing/edge/bevel.html
- [B4] https://docs.blender.org/manual/en/latest/modeling/meshes/tools/loop.html
- [B5] https://docs.blender.org/manual/en/latest/modeling/meshes/editing/mesh/knife_topology_tool.html
- [B6] https://docs.blender.org/manual/en/latest/scene_layout/object/editing/transform/introduction.html
- [B7] https://docs.blender.org/manual/en/latest/editors/3dview/controls/snapping.html
- [B8] https://docs.blender.org/manual/en/latest/modeling/meshes/selecting/introduction.html
- [O1] https://github.com/mrdoob/three.js
- [O2] https://threejs.org/docs/pages/TransformControls.html
- [O3] https://threejs.org/docs/pages/ViewHelper.html
- [O4] https://threejs.org/examples/webgl_clipping.html
- [O5] https://github.com/yomotsu/camera-controls
- [O6] https://github.com/gkjohnson/three-mesh-bvh
- [O7] https://github.com/pmndrs/drei
- [S1] https://solvespace.com/library.pl
- [S2] https://github.com/solvespace/solvespace (src/slvs)
- [S3] https://github.com/Salusoft89/planegcs
- [S4] https://registry.npmjs.org/@salusoft89/planegcs
- [W1] https://developer.mozilla.org/en-US/docs/Web/API/Pointer_events
- [W2] https://developer.mozilla.org/en-US/docs/Web/CSS/touch-action
- [W3] https://developer.mozilla.org/en-US/docs/Web/API/Touch_events/Multi-touch_interaction
- [W4] https://web.dev/articles/mobile-touchandmouse
- [C1] OCAF user guide: https://dev.opencascade.org/doc/overview/html/occt_user_guides__ocaf.html
- [C2] Modeling algorithms: https://dev.opencascade.org/doc/overview/html/occt_user_guides__modeling_algos.html
- [C3] Boolean operations spec (Splitter): https://dev.opencascade.org/doc/overview/html/specification__boolean_operations.html
- [T1] https://playwright.dev/docs/test-snapshots
- [T2] https://playwright.dev/docs/emulation

## Next steps for Grok Build

1. Plan-mode spike: replace mesh fillet/cut with `BRepFilletAPI_MakeFillet` + `BRepAlgoAPI_Cut` in the WASM core; rerun the test matrix and watertight/units gate.
2. Prototype a three.js viewer shell (OrbitControls or camera-controls, ViewHelper, TransformControls, three-mesh-bvh face/edge picking) that maps picks to B-rep face/edge IDs.
3. Build a PlaneGCS (`@salusoft89/planegcs`) sketch spike reproducing the current 8 sketch tools/constraints.
4. Add a Playwright harness with Desktop Chrome, Pixel, and iPhone 13 projects; baselines to `tests/gui/baselines/`, captures to `builds/screenshots/`.
5. Wait for Erik on section 7 before any timeline or mesh-edit work.
