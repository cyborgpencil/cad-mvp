# MODO-style selection, gizmo and primitives: MVP implementation spec

Status: draft (MVP Research Digest, 2026-10-21 MT). This spec doesn't invent values. Anything undocumented is marked TBD. All colours are TBD hex.

## Sources
- Reference video: "Modo for Industrial Design: 1. Beginner Introduction", Foundry Learn, https://youtu.be/HhuccQ20YVM. The download was blocked by YouTube's bot check, so no frames have been reviewed and the duration is TBD.
- Selection modes: https://learn.foundry.com/modo/current/content/help/pages/modeling/selection_modes_types.html
- Tool controls, selection and handles: https://learn.foundry.com/modo/current/content/help/pages/modo_interface/standard_tool_controls.html
- Display prefs (selection colour): https://learn.foundry.com/modo/current/content/help/pages/preferences/pref_display.html
- Viewport properties: https://learn.foundry.com/modo/content/help/pages/modo_interface/3d_viewport_properties.html
- Transform tool: https://learn.foundry.com/modo/current/content/help/pages/layout/transforms/transform.html
- Move tool handles: https://learn.foundry.com/modo/essentials/content/essentials/getting-started/tools.html
- Tool Pipe: https://learn.foundry.com/modo/current/content/help/pages/modo_interface/viewports/utility/tool_pipe.html
- Primitives: https://learn.foundry.com/modo/current/content/help/pages/modeling/creating_geometry.html, .../create_geometry/cube.html, .../cylinder.html, .../sphere.html, .../cone.html
- OCCT: https://occt3d.com/dev/doc/refman/html/class_b_rep_prim_a_p_i___make_box.html, .../class_b_rep_prim_a_p_i___make_cylinder.html, .../class_b_rep_prim_a_p_i___make_sphere.html, .../class_b_rep_prim_a_p_i___make_cone.html, https://dev.opencascade.org/doc/occt-8.0.0/refman/html/_b_rep_prim_a_p_i___make_cone_8hxx.html

## Selection modes for MVP
- Modes and hotkeys: Vertex 1, Edge 2, Face 3, Item 5. Keys 4, 6 and 7 (Materials, Pivot, Center) are out of scope.
- Two distinct highlight states:
  - Hover (pre-highlight). MODO's default is light blue. Hex TBD.
  - Selected. MODO's default is orange. Hex TBD.
  - The two states must never look the same.
- Colours must be named CSS variables, with values TBD: `--hover-color` and `--sel-color`. Don't hardcode orange, teal or any other literal colour.
- Conflict for Erik to decide: MODO's docs use orange for selection, but Erik asked for a teal palette.
- Modifiers: click selects (replaces the selection), Shift+click adds, Ctrl+click removes.
- Empty-selection rule: in Vertex, Edge or Face mode with nothing selected, an operation applies to all elements, with no highlight drawn. In Item mode, an explicit selection is required.
- Mapping to OCCT topology: TopAbs_VERTEX / TopAbs_EDGE / TopAbs_FACE / the whole shape. Picking implementation is TBD and owned by Grok Build.

## Active-button contrast
- MODO's actual active-button style: TBD. It isn't documented and needs a review of the video frames.
- PROPOSAL ONLY (not from MODO docs): the active or selected state must differ from the inactive state by both fill and border, not by colour alone. Fill and border hex values are TBD and need Erik's approval.

## Gizmo (Tool Handles)
- Axis colours: X red, Y green, Z blue (exact hex TBD).
- A handle changes to a hover highlight colour before dragging. MODO uses yellow; hex TBD.
- MVP Move gizmo: 3 axis arrows (single-axis move), 3 planar paddles (two-axis move), and a centre handle that moves in the view plane.
- Scale (boxes) and rotate (circles) come later and are not in the MVP.
- Each move gets numeric Position XYZ fields in mm.

## Primitives (MVP: Box and Cylinder)
Parameters can be edited after creation, and each edit rebuilds the solid.
- Box: center position (X, Y, Z mm) and size X/Y/Z (mm).
  - Mapped to `BRepPrimAPI_MakeBox(gp_Pnt(cx - sx/2, cy - sy/2, cz - sz/2), sx, sy, sz)`.
  - Corner-offset note: OCCT's MakeBox is corner-based, while MODO's Position is the centre, so the half-size offset is required.
- Cylinder: center (X, Y, Z mm), radius (mm), height (mm) and axis (X/Y/Z).
  - Mapped to `BRepPrimAPI_MakeCylinder(gp_Ax2(base, dir), R, H)`.
  - OCCT builds from the base along the axis, so base = center - dir*H/2.
  - Partial angle (the Angle overload) is not in the MVP.
- Sides/Segments: in MODO these control mesh tessellation, which an exact B-rep doesn't have. Whether to expose them as tessellation or deflection settings is TBD (Erik decides).
- Validation: every primitive result must pass the watertight and units gates.
- Export gate and interim banner: unchanged. Export stays enabled only when watertight, units and the OCCT gate all pass.
- Sphere and Cone (MakeSphere, MakeCone) come after the MVP.

## Open TBDs
1. Selection colour: MODO orange or Erik's teal palette (Erik decides). It is set via `--sel-color` / `--hover-color`.
1. All colour hex values: hover, selected, axes, handle hover, active-button fill and border.
2. MODO's active-button style, from video frames. This is blocked until the video can be downloaded with cookies or frames are supplied manually.
3. Video duration.
4. Picking implementation and tolerance for vertices and edges in WASM.
5. Whether Sides/Segments map to tessellation deflection.
6. Default sizes for the Box and Cylinder primitives in mm. The MODO defaults are in metres and aren't adopted.
7. Partial-angle and elliptical (Radius XYZ) support. Out of MVP scope unless Erik says otherwise.
8. A check of the BRepPrimAPI signatures against the libcascade (OCCT 8.0.1) headers.
