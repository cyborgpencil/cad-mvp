# UI redesign: workbench tabs (approved by Erik 2026-10-21; implementation in progress)

> Rule update (Erik, 2026-10-22 02:17 MT): watertight checks and tests are dropped. Units (mm) checks stay and gate Export. The OCCT shape-validity check after operations stays, but a failure is a clean error/revert and never blocks Export. Any watertight gate or watertight test below is superseded by this rule.
Erik asked for a friendlier, less plain UI built around process tabs. Erik approved the wireframes on 2026-10-21 and asked for the GUI to be built into the current project; Grok Build is implementing it. It builds on Research Digest's sourced review in research/gui/ui-layout-review.md (Fusion, Onshape, FreeCAD, Blender). Section 2 of mvp/gui-plan.md lists the operations.

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
| Model | Extrude, push/pull, fillet, chamfer, shell TBD, union / cut / intersect, loop cut, knife, inset, primitives (box, cylinder; sphere and cone test-only) | B-rep where possible (section 2); sphere, cone, intersect stay test-only (C4); chamfer is a user tool (Erik, 2026-10-21) |
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
| Model | Solid | Extrude (Push/Pull), Inset, Fillet, Chamfer, Loop Cut, Knife, Grab, Rotate, Scale, Snapping |
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

## Touch swipe gestures (approved by 3T 2026-10-23; build order 1 to 3)
All web-only, in the pointer handler in `web/index.html`; no C++. Sources: [Onshape view navigation](https://cad.onshape.com/help/Content/View/view_navigation_and_the_view_cube.htm), [Shapr3D gestures](https://support.shapr3d.com/hc/en-us/articles/7873906073884-Keyboard-shortcuts-gestures-and-hotkeys), [Shapr3D forum on 3-finger undo](https://discourse.shapr3d.com/t/2-finger-undo-3-finger-redo/19784), [Nomad history](https://nomadsculpt.com/manual/history), [Nomad interface](https://nomadsculpt.com/manual/interface), [MDN touch-action](https://developer.mozilla.org/en-US/docs/Web/CSS/Reference/Properties/touch-action), [MDN pointer events](https://developer.mozilla.org/en-US/docs/Web/API/Pointer_events).
1. **View-cube swipe to the next face (build first).** A swipe on the cube turns the view 90 degrees to the neighbouring face (front to right, etc.); a tap still picks a face. None of the three apps has this; Onshape's 90-degree arrow step is the closest model. Needs its own swipe threshold, separate from `tapSlopPx()`, and must end on `pointercancel`. A swipe must start on the cube and counts once the finger moves 24 px or more, at any speed; once the finger has moved, no face is picked on release, and anything shorter is a tap (24 px team-chosen by 3T, 2026-10-23; the original 400 ms limit was dropped in the #21 fix because slow swipes fell through to a corner tap; Erik may change after phone testing). Swiping left from Front goes to Right, right to Left, up to Top, down to Bottom; a second finger hands off to pinch/pan. Logic in `web/view-cube.mjs`. Draft PR #21.
2. **Three-finger swipe to undo/redo (Shapr3D).** Left undoes, right redoes, with a setting to turn it off. Three fingers avoid the two-finger pinch/pan conflict. Risk: the iOS system three-finger gesture; needs a real-phone test.
3. **Swipe a focused value field to nudge it (like Nomad's swipe slider).** Snaps to mm steps, one undo step per nudge, focused fields only (keeps the item 8 hotkey fix). Step size: 1 mm per nudge on size and centre fields, in the locked units, and 1 degree per nudge on rotation fields (both team-chosen by 3T, 2026-10-23; Erik may change after phone testing).
4. **Dropped: edge swipe for the tool shelf.** Clashes with iOS/Safari edge gestures, no source found; the Modify shelf toggle covers it.
5. **No change: two-finger orbit/pan lock.** Current one-finger orbit and two-finger pinch/pan match Onshape and Shapr3D; revisit only if Erik's phone testing finds a problem.

## Phone selection (team-chosen by the Chief 2026-10-23; Erik reviews afterward)
Needed for Erik's phone acceptance test (picked edges for fillet and chamfer, and Booleans). JS only, on `feat/phone-selection`.
- Tapping a body selects it; tapping empty space clears the selection.
- Edge pick mode: tap an edge to pick it for fillet or chamfer, with a larger touch tolerance. The tolerance value is recorded in `PROGRESS.md` (TBD until set).
- A Multi toggle adds or removes items from the selection, for Booleans.
- The selection has a clear highlight, and the panel shows the selected count.
