# UI layout review: Fusion, Onshape, FreeCAD, Blender

Research Digest, 2026-10-21. Design input only; takeaways are proposals, not Erik decisions.

## Findings
- **Fusion:** workspace picker (top left) morphs the whole UI. Inside Design, toolbar tabs (Solid, Surface, Mesh, Sheet Metal, Tools) group tools by type of work; panels group tools within a tab. Contextual tabs (e.g. Sketch) appear only while their command is active. 3D Print and Inspect live under Tools. [1][2][3]
- **Onshape:** the top toolbar changes with the current job (Part Studio, Sketch, Assembly). The Feature list with rollback bar stays on the left; undo/redo stay fixed. Tool search (Alt/Opt+C) finds any tool, including ones removed from the toolbar. On small screens, tools collapse into dropdowns. [4][5]
- **FreeCAD:** switching workbenches swaps toolbars and menus but not the scene. 1.0 added an optional TabBar workbench selector. Std Base commands are available in every workbench. PartDesign New Sketch enters Sketcher and returns to PartDesign on close. Mesh is its own workbench. [6][7][8]
- **Blender:** workspace tabs in the Topbar, each a preset window layout (Layout, Modeling, Sculpting...). Ctrl+PageUp/PageDown cycles them. [9]

## Takeaways (proposal)
1. Top tabs: Sketch, Model, Mesh/Repair, Export/Print, with panels inside each tab.
2. Sketch behaves as a contextual mode: entered from Model, returns to Model on finish.
3. Fixed in all tabs: viewport, tree, view cube, undo/redo, select, measure, mm/inch toggle, Export.
4. Tool search; on phones collapse panels into dropdowns.
5. Units check shown in Export/Print before every export (watertight dropped, 02:17 rule).
- TBD for Erik: units/export in top bar vs status bar.

## Tab-switch shortcuts and tool search
- **Blender:** Ctrl+PageUp / Ctrl+PageDown go to the previous / next workspace tab; Ctrl+Tab cycles panel tabs but not workspace tabs. [9][10]
- **FreeCAD:** Std Workbench has no default shortcut; switch via the ComboBox/TabBar or View > Workbench. [7]
- **Onshape:** Search tools (Alt/Opt+C) finds any tool, including ones removed from the toolbar, and can highlight it in the toolbar. On iOS/Android, search sits in the tools menu. The S key opens a customizable shortcut toolbar. [4][5]
- Fusion: no shortcut for switching tabs found in the sources above; not claimed.
- **Chrome reserves (Windows/Linux):** Ctrl+Tab / Ctrl+PgDn (next tab), Ctrl+Shift+Tab / Ctrl+PgUp (previous tab), Ctrl+1..8 (specific tab), Ctrl+9 (last tab); Alt+F / Alt+E open the Chrome menu; Alt+Left/Right go back/forward. Mac: Cmd+1..8, Cmd+Opt+Left/Right. So Blender's Ctrl+PageUp/PageDown clashes in a browser. [11]
- Proposal (keys TBD for Erik): plain **1 / 2 / 3 / 4** = Sketch / Solid / Inspect / Export, active only when no text field has focus. Plain digits are not on Chrome's list [11]. Alt+1..4 is also not on Chrome's Windows list, but Alt+letter combos are browser menu keys there, so keep it as a fallback only. Tool search: one key (e.g. X, as Shapr3D [14]) plus a search button in the phone tools menu, as Onshape [5]. Needs a test in Chrome/Edge/Firefox.

### Mobile / touch
- **Gestures (Onshape iOS/Android):** 1-finger drag = 3D rotate; 2-finger pinch = zoom; 2-finger drag = pan; 2-finger twist = 2D rotate; 2-finger tap = context menu; 2-finger long press = box select; tap = select, double-tap = clear. A 3D Rotate Lock button sits above the View Cube and turns on by default when a sketch entity is selected, so dragging moves the entity, not the view. Tapping the View Cube opens a list: standard views, Zoom to fit, display modes, Section View. [12][13]
- **Precision select (Onshape):** touch and hold shows crosshairs, and releasing selects the highlighted entity. Stylus (e.g. Apple Pencil) works for any one-finger gesture. [13]
- **Gestures (Shapr3D iPad):** 1-finger drag on grid = orbit; 2-finger pan = pan; pinch = zoom; double-tap face = zoom to face; double-tap Orientation Cube = reset view; 3-finger swipe left/right = undo/redo; long-tap and drag = area select; pen draws sketches. [14]
- **Tool search on mobile:** Onshape puts Search tools in the tools menu on iOS/Android [5]. Shapr3D offers command search (X or Cmd/Ctrl+F with a keyboard) [14]. Fusion mobile is a viewer and review app: touch zoom/pan/rotate, and search for parts that highlight in the model; no modeling tools [15][16].
- **Radial / long-press menus:** Fusion desktop's Marking menu (right-click) is radial, with 8 commands that change per tab/workspace, and gestures (drag directions) that pick commands without showing it [17]. On touch, Onshape uses a 2-finger tap for the context menu instead [12].
- **Tab placement and drawers:** none of the official sources above define bottom vs top tabs or drawer layouts for CAD on phones. Gap; not claimed. Onshape notes that tools collapse into dropdowns on small screens [4].
- FreeCAD/Blender: no official touch-navigation docs checked in this pass; not claimed.
- **Proposal 1:** keep the four tabs (Sketch/Solid/Inspect/Export). On phones, put them in a bottom bar (TBD for Erik; no CAD source above), with tree and inspector as drawers (as the mockup already does).
- **Proposal 2:** view controls currently appear 3 times (toolbar, floating viewport bar, radial menu). Put them in one shared spot: a tappable ViewCube menu like Onshape's [12] (views, fit, display modes, section), and drop them from the toolbar and radial menu.
- **Proposal 3:** adopt Onshape-style gestures as defaults (1-finger orbit, 2-finger pan/pinch, 2-finger tap = context/radial menu) and add a rotate-lock toggle in Sketch [12][13].
- **Proposal 4:** the Export tab has no units gate control in the mockup. Add a gate panel (PASS/FAIL, units, volume) that must pass before Export STL/3MF is enabled, which follows the standing rule.

## Repair tab tool list (proposal)
Research Digest, 2026-10-21. Seven tools, in pipeline order (B-rep first, then mesh). It follows the pipeline in `research/healing/README.md` [19]. MVP = in the first build; Later = after MVP. Each tool reports what it changed.
1. **Check shape (MVP):** checks topology, edge parameterization, wire/face orientation and that solid shells are closed, then shows PASS/FAIL. Backed by OCCT `BRepCheck_Analyzer::IsValid`. [19][18]
2. **Find open edges (MVP):** lists free edges (used by one face) and bad edges (used twice with the same orientation), so the user sees where a shell is open or invalid. Backed by OCCT `ShapeAnalysis_Shell` / `ShapeAnalysis_FreeBounds`. [18]
3. **Auto-heal shape (MVP):** one click runs `ShapeFix_Shape`. It fixes missing or deviating curves, wire connections, self-intersecting wires, seams, small edges and shell/solid orientation, then rechecks with BRepCheck. Status flags OK/DONE/FAIL drive the message. Backed by OCCT ShapeFix. [18][19]
4. **Fix face orientation (MVP, part of 3):** makes face orientations in a shell coherent (the B-rep "flipped normals" fix). Backed by OCCT `ShapeFix_Shell`. [18]
5. **Remove small features (Later):** drops small edges (`ShapeFix_Wireframe` with `ModeDropSmallEdges`), spot/strip faces (`ShapeFix_FixSmallFace`) and small holes (`ShapeUpgrade_RemoveInternalWires`). Thresholds are TBD (test-matrix O11). [18][22]
6. **Merge coplanar faces (Later):** unifies same-domain faces and edges (for example after Booleans) with `ShapeUpgrade_UnifySameDomain`. The geometry stays the same. [18]
7. **Mesh repair (MVP, existing code):** our `repair_manifold` welds identical vertices, drops degenerate triangles and flips an inward shell, then re-runs `check_watertight`. A mesh that stays open returns "cannot repair" and writes nothing. Manifold (elalish/manifold, Apache-2.0, WASM) is a TBD candidate for this step. [20][19]
- **Gate to Export (MVP, required):** units only (02:17 rule). `check_watertight` reports but does not block. The B-rep passed BRepCheck after each op. For 3MF, the file reads back through lib3mf and `unit="millimeter"` matches the locked unit. PASS enables Export STL/3MF; FAIL blocks it and names the first failing rule. The result shows on the Repair tab, the Export tab and the status bar. [21][22]
- Not verified in this pass, so not proposed: hole filling on meshes, and ADMesh, MeshFix, PrusaSlicer or Bambu repair features. requirements.md asks for a "small gaps" fix [23]. The only verified gap tool is OCCT's `FixGaps`/`FixWireGaps` (B-rep wire gaps), and OCCT warns that it may change geometry and can fail [18]. TBD for Erik.
## Sources
1. Fusion Help, Workspaces: https://help.autodesk.com/view/fusion360/ENU/?guid=GS-WORKSPACES
2. Fusion API, User-Interface Customization: https://help.autodesk.com/cloudhelp/ENU/Fusion-360-API/files/UserInterface_UM.htm
3. Product Design Online, Fusion 360 new UI (2019): https://productdesignonline.com/fusion-360-tutorials/fusion-360-new-ui-vs-old-ui-august-2019-update/
4. Onshape, User Interface Basics: https://cad.onshape.com/help/Content/Home/user_interface_basics.htm
5. Onshape, Search Tools: https://cad.onshape.com/help/Content/Home/search_tools.htm
6. FreeCAD docs, Workbenches: https://github.com/FreeCAD/FreeCAD-documentation/blob/main/wiki/Workbenches.md
7. FreeCAD wiki, Std Workbench: https://wiki.freecad.org/Std_Workbench
8. FreeCAD wiki, PartDesign NewSketch: https://wiki.freecad.org/PartDesign_NewSketch
9. Blender Manual, Workspaces: https://docs.blender.org/manual/en/latest/interface/window_system/workspaces.html
10. Blender Manual, Tabs & Panels: https://docs.blender.org/manual/en/latest/interface/window_system/tabs_panels.html
11. Google Chrome Help, Chrome keyboard shortcuts: https://support.google.com/chrome/answer/157179
12. Onshape, View Navigation and the View Cube: https://cad.onshape.com/help/Content/View/view_navigation_and_the_view_cube.htm
13. Onshape, Onshape Primer (touch gestures for mobile devices): https://cad.onshape.com/help/Content/Primer/onshape_primer.htm
14. Shapr3D Help, Keyboard shortcuts, gestures, and hotkeys: https://support.shapr3d.com/hc/en-us/articles/7873906073884-Keyboard-shortcuts-gestures-and-hotkeys
15. Autodesk Fusion app, Apple App Store listing (Autodesk): https://apps.apple.com/kh/app/autodesk-fusion/id991074843
16. Fusion Blog, Fusion Mobile: https://www.autodesk.com/products/fusion-360/blog/fusion-360-mobile-ios-android/
17. Fusion Help, Marking menu reference: https://help.autodesk.com/cloudhelp/ENU/Fusion-GetStarted/files/GUID-6514ABC1-CB75-4F0B-AB0E-316FAD36BA93.htm
18. OCCT user guide, Shape Healing: https://dev.opencascade.org/doc/overview/html/occt_user_guides__shape_healing.html
19. Repo: research/healing/README.md (BRepCheck, ShapeFix, BRepMesh, Manifold notes and sources)
20. Repo: mvp/create-export.md (repair_manifold behavior)
21. Repo: research/formats/validation.md (units gate and validity rules)
22. Repo: mvp/test-matrix.md (lib3mf v2.5.0 docs, 3MF Core Spec unit and manifold rules, O11 tolerance TBD)
23. Repo: mvp/requirements.md (Geometry healing and Export validation rows)