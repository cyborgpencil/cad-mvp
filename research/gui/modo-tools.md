# MODO layout, theme and tools: restyle input for our mockup (2026-10-21)

Sources are Foundry Modo docs (learn.foundry.com) unless noted. Hex colors: none are published for the UI theme, so all hex values are TBD.

## Layout (default Model layout)
- Left: Toolbox with rotated sub-tabs that group tools by function. The tool Properties panel sits under the toolbox. It starts empty and fills in when a tool is picked, adding sections when falloffs, action centers or snapping are on. [1][2]
- Center: 3D viewport. [1]
- Right top: Lists viewport tabs (Scenes/Items list, Shading/Shader Tree, Groups, Images). The "+" adds tabs, and tabs can be dragged to reorder. [3]
- Right below: Properties, Channels, Display and Lists (Vertex Maps, Tool Pipe, Statistics, Info). Item Properties adds sub-tabs down the right edge, one per selected item. [1][2]
- Tabs never auto-select; the user clicks to switch. [4]
- Snapping controls are in the menu bar below the layout tabs. [7]

## Color theme: the "teal" premise needs Erik's check
- The docs give Modo's highlight color as orange, not teal. The active tab name turns orange (inactive is light gray, background tabs darker gray) [4], the active tool is highlighted orange [1], the active viewport thumb turns orange [5], and the tab drop marker is an orange line [3].
- Preferences > Display > Colors only edits 3D-viewport schemes (background, grid, work plane, selection, handles, axis X/Y/Z, etc.). The application UI has no documented editable theme. [5]
- I found no official or community teal hex for Modo. Teal could come from a newer release or a custom theme. Ask Erik which build or screenshot he means.
- Hex for background, panel, tab, accent and text: TBD. Sample them from an official Foundry screenshot Erik picks, using an eyedropper on a 1:1 PNG, and record the source URL next to each value.

## MVP-relevant tools (what Modo does)
- Boolean: Union, Intersect, Subtract, Add. Inputs must be watertight with volume, have no coincident (shared-position) verts/edges/faces and no floating verts. It sits in Mesh Edit, or procedurally in Mesh Ops > Edit > Boolean. [6]
- Solid Drill: background mesh drills foreground 2D polygons (Core, Stencil, Tunnel, Slice). [8]
- MeshFusion: non-destructive union/subtract/intersect with real-time update and blends. It wants quads; n-gons hurt strip quality. [9]
- Edge Bevel: turns selected edges into quad strips (Inset/Width, Round Level, Edge Shape). This maps to our Fillet/Chamfer. [10]
- Work Plane: clicks land on it. The Work Plane tool has 3-point handles and a Preview toggle. [7]
- Action Center: sets the tool handle's origin and axis (None, Automatic, Selection, Selection Border, Selection Center Auto Axis, Element...). [11]
- Snapping: snaps the tool handle. The X key holds snapping, and it depends on the Action Center. [12]
- Push/Pull: not looked up this pass, so TBD.
- Our mapping: Fillet and Chamfer go to Edge Bevel (OCCT BRepFilletAPI, not a mesh bevel). Booleans go to the Boolean tool (OCCT, see `../occt-wasm/booleans.md`). Workplane = sketch plane, plus snapping and handles.

## Restyle notes for mockup/index.html (no numbers invented)
1. Layout: Toolbox on the left with vertical tab strip (Sketch/Model/Modify/Repair/Export), tool Properties under it. Viewport in the center. Right side: Items list on top, Properties/Info tabs below.
2. One accent color for active tab, active tool and active viewport border, set by a CSS variable `--accent` (value TBD, teal vs orange per Erik).
3. Inactive tabs light gray, background tabs darker gray (Modo convention [4]). Exact values TBD.
4. Tabs switch only on click. Don't auto-switch panels when the selection changes. [4]
5. Show on-canvas tool handles (axis-colored per Modo's handle scheme [5]) with a live Preview toggle in tool Properties, the way Work Plane works. [7]
6. Keep the 44 px touch targets and the Export gate (watertight + units) unchanged.

## Sources
1. https://learn.foundry.com/modo/current/content/help/pages/modo_interface/exploring_layout.html
2. https://learn.foundry.com/modo/current/content/help/pages/modo_interface/viewports/list_info/properties.html
3. https://learn.foundry.com/modo/essentials/content/essentials/getting-started/lists-viewport.html
4. https://learn.foundry.com/modo/content/help/pages/modo_interface/ui_conventions.html
5. https://learn.foundry.com/modo/current/content/help/pages/preferences/pref_display.html
6. https://learn.foundry.com/modo/current/content/help/pages/modeling/edit_geometry/boolean.html
7. https://learn.foundry.com/modo/current/content/help/pages/modeling/workplane.html
8. https://learn.foundry.com/modo/current/content/help/pages/modeling/edit_geometry/solid_drill.html
9. https://learn.foundry.com/modo/current/content/help/pages/meshfusion/mf_introduction.html
10. https://modosdk.foundry.com/modo/content/help/pages/modeling/vert_edge_poly_comp_tools/edge_bevel.html
11. https://learn.foundry.com/modo/current/content/help/pages/modeling/action_centers.html
12. https://learn.foundry.com/modo/current/content/help/pages/modeling/snapping.html
Start page: https://learn.foundry.com/modo/content/help/pages/getting_started/what_is_modo.html
