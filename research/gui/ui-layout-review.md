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
5. Watertight and units check shown in Export/Print before every export.
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
- **Proposal 4:** the Export tab has no watertight/units gate control in the mockup. Add a gate panel (PASS/FAIL, units, volume) that must pass before Export STL/3MF is enabled, which follows the standing rule.
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
