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
