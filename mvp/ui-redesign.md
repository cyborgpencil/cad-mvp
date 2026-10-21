# UI redesign: workbench tabs (proposal, design only, 2026-10-21)
Erik asked for a friendlier, less plain UI built around process tabs. This section is design only: no code changes, and the Qt app and mockup stay as they are until Erik approves. It builds on Research Digest's sourced review in research/gui/ui-layout-review.md (Fusion, Onshape, FreeCAD, Blender). Section 2 of mvp/gui-plan.md lists the operations.

## 1 Layout sketch
```
+--------------------------------------------------------------------------------+
| [Logo] File v | Undo Redo | Sketch | Model | Mesh/Repair | Export/Print | mm|in |  <- top bar
+--------------------------------------------------------------------------------+
| Tab toolbar: big icon+label buttons for the active tab only, grouped           |
|  e.g. Model:  [Extrude] [Push/Pull] [Fillet] [Chamfer] | [Union][Cut] | ...    |
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
| Quick export | Top bar shortcut to Export/Print tab | One path to export, always gated |
| Status bar (units, watertight, volume, errors) | Bottom | Watertight and units gate stays visible |

## 3 Tab-by-tool map
| Tab | Tools (MVP candidates from sections 2 to 4) | Notes |
|---|---|---|
| Sketch | Line, rectangle, circle, arc, constraints (coincident, parallel, perpendicular, equal, dimension), trim, finish sketch | PlaneGCS solver (section 4) |
| Model | Extrude, push/pull, fillet, chamfer, shell TBD, union / cut / intersect, loop cut, knife, inset, primitives (box, cylinder; sphere and cone test-only) | B-rep where possible (section 2); chamfer, sphere, cone, intersect stay test-only (C4) |
| Mesh/Repair | Watertight check, fix normals, fill holes, merge vertices, self-intersection report, volume and shell count | Exact repair tool list TBD (C2) |
| Export/Print | STL / 3MF export, units confirm, watertight gate, bounding box and volume readout, open in OrcaSlicer TBD | Export blocked unless the gate passes |

## 4 UI best-practice rules applied
- Only the active tab's tools show, so the toolbar stays short (progressive disclosure).
- Icon plus text label on toolbar buttons; tooltips with the keyboard shortcut.
- Shared tools never move between tabs.
- The inspector shows the active tool's options and live dimensions, instead of pop-up dialogs.
- Clear status: gate PASS/FAIL in color plus text, errors in plain words.
- Touch targets at least 44 px on phone.

## 5 Open questions for Erik (TBD, not decided)
- Is Mesh/Repair its own tab, or part of Export/Print? (relates to C2)
- Should a history timeline appear in the MVP? (C1)
- Exact tool list per tab beyond the MVP candidates above.
- Visual style: light, dark, or both; brand colors are TBD.
- Where units and export sit: the top bar (as sketched), the status bar, or both. TBD.
- Should Sketch be its own tab, or a contextual mode that opens from Model and returns there (as in Fusion and FreeCAD)? Proposal: a contextual mode that still shows as a tab. TBD.

## Research-backed proposals (not Erik's decisions)
- Top tabs work like Blender's workspaces, with each tab's tools grouped into panels like Fusion's toolbar tabs.
- Shared tools stay fixed across tabs, like FreeCAD's Std commands and Onshape's fixed controls.
- Tool search (like Onshape Alt+C) and panels that collapse into dropdowns on phones.
- The watertight and units check is shown inside the Export/Print tab, right before every export, and also in the status bar.
