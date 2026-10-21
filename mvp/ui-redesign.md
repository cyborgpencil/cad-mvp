# UI redesign: workbench tabs (proposal, design only, 2026-10-21)
Erik asked for a friendlier, less plain UI built around process tabs. This section is design only: no code changes, and the Qt app and mockup stay as they are until Erik approves. It builds on Research Digest's sourced review in research/gui/ui-layout-review.md (Fusion, Onshape, FreeCAD, Blender). Section 2 of mvp/gui-plan.md lists the operations.

## 1 Layout sketch
```
+--------------------------------------------------------------------------------+
| [Logo] File v | Undo Redo | Sketch | Model | Mesh/Repair | Export | mm|in |  <- top bar
+--------------------------------------------------------------------------------+
| Tab toolbar: big icon+label buttons for the active tab only, grouped           |
|  e.g. Model:  [Extrude] [Push/Pull] [Fillet]           | [Union][Cut] | ...    |
+-----------+----------------------------------------------------+---------------+
| Browser   |                                                    | Properties /  |
| (parts,   |                 3D viewport                        | Inspector     |
| sketches, |                                                    | (active tool  |
| bodies)   |                                          [ViewCube]| options, dims)|
|           |  [Select v] [Measure] [Section]   (floating, left) |               |
+-----------+----------------------------------------------------+---------------+
| Status bar: units locked (mm) | Watertight: PASS/FAIL | Volume | Hints / errors |
+--------------------------------------------------------------------------------+
| (optional later) History timeline -- depends on C1, not in MVP until Erik says |
+--------------------------------------------------------------------------------+
```
Phone (narrow) layout: tabs become a bottom tab bar, the tab toolbar becomes a horizontal scroll strip above it, and the browser and inspector become slide-in drawers (same as section 1).

## 2 Tools shared across all tabs (always in the same place)
| Tool | Where | Why fixed |
|---|---|---|
| Undo / Redo | Top bar, left | Used in every workflow |
| File (new, open, save, import STL) | Top bar menu | Import STL is TBD scope |
| Units toggle (mm / inch) | Top bar, right | Units must always be visible; mm locked for export |
| Select (click, box, face/edge/body filter) | Floating viewport strip | Every tab selects geometry |
| View (ViewCube, fit, ortho/persp, standard views) | Viewport corner | Same navigation everywhere |
| Measure | Floating viewport strip | Needed when sketching, modeling and checking prints |
| Section view | Floating viewport strip | Shows internal voids such as O5 |
| Quick export | Top bar shortcut to Export tab | One path to export, always gated |
| Status bar (units, watertight, volume, errors) | Bottom | Watertight and units gate stays visible |

## 3 Tab-by-tool map
| Tab | Tools (MVP candidates from sections 2 to 4) | Notes |
|---|---|---|
| Sketch | Line, rectangle, circle, arc, constraints (coincident, parallel, perpendicular, equal, dimension), trim, finish sketch | PlaneGCS solver (section 4) |
| Model | Extrude, push/pull, fillet, chamfer, shell TBD, union / cut / intersect, loop cut, knife, inset, primitives (box, cylinder; sphere and cone test-only) | B-rep where possible (section 2); chamfer, sphere, cone, intersect stay test-only (C4) |
| Mesh/Repair | Watertight check, fix normals, fill holes, merge vertices, self-intersection report, volume and shell count | Exact repair tool list TBD (C2) |
| Export | STL / 3MF export, units confirm, watertight gate, bounding box and volume readout, open in OrcaSlicer TBD | Export blocked unless the gate passes |

## 4 UI best-practice rules applied
- Only the active tab's tools show, so the toolbar stays short (progressive disclosure).
- Icon plus text label on toolbar buttons; tooltips with the keyboard shortcut.
- Shared tools never move between tabs.
- The inspector shows the active tool's options and live dimensions, instead of pop-up dialogs.
- Clear status: gate PASS/FAIL in color plus text, errors in plain words.
- Touch targets at least 44 px on phone.

## 5 Open questions for Erik (TBD, not decided)
- Is Mesh/Repair its own tab, or part of Export? (relates to C2)
- Should a history timeline appear in the MVP? (C1)
- Exact tool list per tab beyond the MVP candidates above.
- Visual style: light, dark, or both; brand colors are TBD.
- Where units and export sit: the top bar (as sketched), the status bar, or both. TBD.
- Should Sketch be its own tab, or a contextual mode that opens from Model and returns there (as in Fusion and FreeCAD)? Proposal: a contextual mode that still shows as a tab. TBD.

## Research-backed proposals (not Erik's decisions)
- Top tabs work like Blender's workspaces, with each tab's tools grouped into panels like Fusion's toolbar tabs.
- Shared tools stay fixed across tabs, like FreeCAD's Std commands and Onshape's fixed controls.
- Tool search (like Onshape Alt+C) and panels that collapse into dropdowns on phones.
- The watertight and units check is shown inside the Export tab, right before every export, and also in the status bar.

## Current mockup controls mapped to tabs (from Repo Keeper's read-only inventory of mockup/index.html, 2026-10-21)
| Proposed tab | Mockup tab | Mockup controls |
|---|---|---|
| Sketch | Sketch | Line, Rectangle, Circle, Arc, Polygon, Sketch Fillet, Trim, Offset, Dimension; constraints Coincident, Horizontal, Vertical, Parallel, Perpendicular, Equal, Tangent, Fixed |
| Model | Solid | Extrude (Push/Pull), Inset, Fillet (Chamfer test-only), Loop Cut, Knife, Grab, Rotate, Scale, Snapping |
| Mesh/Repair | Inspect | Section, Measure, display modes (Shaded, Shaded + Edges, Wireframe, X-Ray), Isolate, Hide |
| Export | Export | Export STL, Export 3MF |
| Shared (all tabs) | top bar, view bar, radial menu | Undo/Redo, mm/in, selection (Vertex, Edge, Face, Body), navigation (Orbit, Pan, Zoom, Fit, Front, Top, Right, Iso/Home), ViewCube, browser tree (Bodies, Sketches, Construction planes) |

Findings:
- Tab names differ: the mockup says Solid and Inspect, the proposal says Model and Mesh/Repair. TBD for Erik.
- MUST-HAVE gap: the mockup has no watertight or units check before Export STL/3MF. Export must show and enforce it before every export.
- Navigation and view controls appear in three places (toolbar, floating view bar, radial menu). Proposal: keep one shared spot. The radial menu's fate is TBD.
- The mockup has no mesh repair tools yet, so the Mesh/Repair tool list is TBD.
- The timeline (Origin, Sketch1, Extrude1, Fillet1) is visual only, which ties to the open timeline TBD.
- Appearance swatches (Steel, Orange, Green, Slate): placement TBD.
- Tab-switch keys and tool search keys are TBD. Research notes Blender uses Ctrl+PageUp/PageDown, which Chrome on Windows reserves for its own tabs (per 3T), so it is ruled out, and Onshape uses Alt+C for tool search. See research/gui/ui-layout-review.md.

## Team decisions (final) (2026-10-21, at Erik's request; Erik reviews afterward)
These replace the TBDs above where they conflict.
1. Tabs are Sketch, Model, Repair and Export (settled by Chief). Plain words beat Solid and Inspect, and short labels fit a phone's bottom tab bar.
2. Sketch is a mode that shows as a tab. Model opens it, and a "Finish Sketch" bar returns you to Model, as in Fusion and FreeCAD.
3. Repair is its own tab for hole fill, normals and the other healing tools. Healing is a core MVP job, and FreeCAD keeps Mesh as its own workbench. Proposed MVP tools (Research Digest, research/gui/ui-layout-review.md sources 18 to 23): Check shape, Find open edges, Auto-heal and Mesh repair. Remove small features and Merge coplanar faces come later. The small-gaps fix is TBD for Erik, because OCCT FixGaps can change geometry.
4. Measure, Section, display modes and navigation live in one shared floating view bar plus the ViewCube. The mockup repeated them in three places.
5. There's no radial menu in the MVP, because it only duplicated the shared view bar.
6. The mm/in toggle is in the top bar. The status bar shows units (read-only) and the watertight PASS/FAIL result and volume at all times, because units are locked and the check is a hard gate.
7. There's one Export button, and it lives only on the Export tab, behind the watertight and units check. There's no quick export, so nothing can skip the check.
8. The history timeline is out of the MVP, and only the browser tree ships. The mockup labels the timeline visual only, and nothing behind it supports history yet.
9. The visual style is dark neutral with one accent color, based on the mockup's Slate theme, with touch targets of at least 44 px and no other new style work in the MVP.
10. Plain keys 1 to 4 switch between Sketch, Model, Repair and Export, active only when no text field has focus, and X opens tool search. Chrome reserves Ctrl+1 to 8, Ctrl+Tab, Ctrl+PgUp/PgDn and Ctrl+K, and Alt+letter opens its menus (research/gui/ui-layout-review.md, sources 11 to 17). On phones, search sits in the tools menu. The keys still need a browser test.
