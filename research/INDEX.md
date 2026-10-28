# CAD/CAM Project Research Index

Organized knowledge for high-performance custom CAD/CAM combining Autodesk, Adobe, FreeCAD, and Blender features.

## Current Documents

- **MVP**: See `../mvp/requirements.md` (design-to-print scope only).
- **Solid check**: See `../mvp/solid-check.md` (in-memory triangle checker; reports only since the 02:17 rule).
- **Mesh view**: See `../mvp/mesh-view.md` (desktop window over the triangle checker).
- **Tooling priority**: See `../mvp/tooling-priority.md` (Grok Build, then Cursor, then Grok Bots).
- **Get started**: See `../mvp/get-started-with-grok-build.md` (simple first steps).
- **Tooling skill**: See `../.grok/skills/tooling-priority/SKILL.md` (reusable across projects).
- **Full Vision**: See `../vision/full-project.md` (post-MVP, independent).
- **Organization**: See `../ORGANIZATION.md`.

## Research Folders

- `autodesk/`: Fusion 360 CAD/CAM/CAE features. (post-MVP background)
- `freecad/`: Open-source parametric CAD with OCCT kernel, CAM, FEM.
- `blender/`: Mesh/freeform strengths + STEP addons. (post-MVP background)
- `adobe/`: 2D vector excellence, textures, 2D-3D bridges. (post-MVP background)
- `formats/`: STL, 3MF, STEP details, plus `validation.md` (units gate and validity checks; watertight dropped, 02:17 rule). (MVP)
- `ai-mcp/`: Model Context Protocol for first-class AI tools. (MVP; tool list TBD for Erik)
- `simulations/`: FEA, CAM path, motion types. (post-MVP background)
- `architecture/`: Kernel, components, performance notes. (MVP scope section conflicts with design-to-print scope; pending Erik.)
- `occt-wasm/`: OCCT to WebAssembly build options. (MVP)
- `healing/`: B-Rep and mesh validation and repair. (MVP)
- `gui/`: Fusion-style layout, Blender-style ops mapped to OCCT B-rep, browser input, and GUI screenshot tests (`gui/README.md`). (plan input; scope conflicts pending Erik)

## Notes

Update research here first. Propagate only confirmed changes into MVP or vision docs. Keep documents consistent with the project-organizer skill (`../.grok/skills/project-organizer/`). Note: a "document-upgrader" skill was referenced here but does not exist in the repo.
- [gui/plane-pick-intent-proposal-2026-10-27.md](gui/plane-pick-intent-proposal-2026-10-27.md): Dig+Doc invent-free plane-pick INTENT - Multi-like on/off sole job enable/disable ortho+#originPlanes + planar-face set paths; default ON=tip; Multi!=plane; Fusion filters closest; GAP exact id/placement + OFF hide vs disable hits; Chief lock next (2026-10-27 ~6:45 PM MT).
- [gui/float-multi-agy-split-2026-10-27.md](gui/float-multi-agy-split-2026-10-27.md): Dig+Doc invent-free float+drag+X multi-agy split @ tip 5ee57ee of offbar prompt - 3-way agy-float-register / agy-close-chrome / agy-regression-smoke (alt 2-way); snap/persist/z TBD out; no Pilot until Chief lock (2026-10-27 ~6:45 PM MT).
- [gui/second-priority-toolbar-float-sketch-plane-2026-10-27.md](gui/second-priority-toolbar-float-sketch-plane-2026-10-27.md): second-priority invent-free pack  -  (1) sketch plane-pick toggle TBD vs Multi/Fusion filters; (2) toolbar density CAUTION few-px; (3) float/drag OK, X-corner CAUTION, snap/persist/z-order GAP; coding tip only after Chief lock AND item-7 exit (2026-10-27 ~6:25 PM MT).
- [mvp-core-gaps-2026-10-27.md](mvp-core-gaps-2026-10-27.md): invent-free status of OCCT/WASM, healing, STL/3MF validation, and MCP folders vs live INDEX; home tree is cad-mvp not cadcam-mvp-research (2026-10-27 ~5:55 PM MT).
- [overnight-10-rebuild-screenshots-note.md](overnight-10-rebuild-screenshots-note.md): overnight item 10  -  rebuild L-bracket + truck with latest tools, Orca plates, morning screenshots; note only; no `prompts/` chrome brief (2026-10-27 ~1:15 AM MT).
- [overnight-app-wide-redundancy-pass.md](overnight-app-wide-redundancy-pass.md): overnight item 9  -  app-wide redundancy pass; tip `c713ce4` duplicate inventory only; no punch list (2026-10-27 ~1:15 AM MT).
- [overnight-consolidate-remove-bottom-bar.md](overnight-consolidate-remove-bottom-bar.md): overnight item 8  -  consolidate then remove the bottom Create/Modify bar; units bar bottommost; Chief lock 2026-10-27 ~1:17 AM MT; relocate only if an existing path fits, else TBD (2026-10-27 ~1:15 AM MT).
- [overnight-sketch-clutter-verts-edit.md](overnight-sketch-clutter-verts-edit.md): overnight item 7  -  less sketch create clutter, brighter verts/edges, edit+delete, flesh sketches+solids; unspecified clauses stay TBD; no punch list (2026-10-27 ~1:15 AM MT).
- [overnight-view-cube-double-tap-iso.md](overnight-view-cube-double-tap-iso.md): overnight item 6  -  view-cube double-tap iso<->non-iso stretch; Chief lock drops the Home double-tap; stretch and non-iso meanings stay TBD (2026-10-27 ~1:15 AM MT).
- [overnight-home-onto-top-view-control.md](overnight-home-onto-top-view-control.md): overnight item 5  -  move Home off viewport mid-top `#vcHome` onto the top-view control; destination node unnamed on tip `c713ce4` (2026-10-27 ~1:15 AM MT).
- [overnight-view-popup-top-tools-bar.md](overnight-view-popup-top-tools-bar.md): overnight item 4  -  View popup into the top lower tools bar with its own show/hide icon; tip `c713ce4` View UI is `.vp-bar`, not `.topbar-shelves` (2026-10-27 ~1:15 AM MT).
- [overnight-sketch-dims-follow-angle.md](overnight-sketch-dims-follow-angle.md): overnight item 3  -  sketch dims follow the angle they represent; tip `529df18` `.line-dim` badges stay screen-upright (CSS translate only, no rotate); flip, offset, chip kinds, and the implementation path stay TBD (2026-10-27 ~1:10 AM MT).
- [gui/ui-layout-review.md](gui/ui-layout-review.md): Fusion, Onshape, FreeCAD and Blender UI layout review with tab-layout takeaways (2026-10-21).
- [gui/usability-checks.md](gui/usability-checks.md): pass/fail GUI checklist for touch targets, shortcuts, the Export gate, layout, the Repair tab and rotation (2026-10-21).
- [gui/wire-target.md](gui/wire-target.md): Qt app in src/ vs WASM browser page as the GUI wiring target, for Erik's choice (2026-10-21).
- [occt-wasm/pages-hosting.md](occt-wasm/pages-hosting.md): does the single-threaded OCCT WASM build fit GitHub Pages (limits, MIME, headers) (2026-10-21).
- [occt-wasm/prebuilt-options.md](occt-wasm/prebuilt-options.md): prebuilt OCCT WASM options (libcascade, opencascade.js, occt-import-js, official build) and reuse-vs-build verdict (2026-10-21).
- [projects/blink-mount.md](projects/blink-mount.md): Blink XT/XT2/Indoor/Outdoor mount specs (official vs measured), US door casing sizes, wood screw pilot/clearance holes for the L-bracket (2026-10-21).
- [gui/modo-tools.md](gui/modo-tools.md): Modo layout, theme (docs say orange accent; teal hex TBD) and MVP tools (Boolean, Edge Bevel, Work Plane, Action Center, snapping) with mockup restyle notes (2026-10-21).
- [gui/modo-selection-primitives.md](gui/modo-selection-primitives.md): MVP spec for selection modes (V/E/F/Item), hover vs selected CSS vars (colours TBD; orange vs teal pending Erik), Move gizmo, Box/Cylinder primitives mapped to BRepPrimAPI with the units gate and OCCT validity check (2026-10-21; watertight dropped 2026-10-22).
- [gui/ui-gap-p2.md](gui/ui-gap-p2.md): P2 UI gap analysis vs Fusion/Onshape/FreeCAD  -  selection, measure/callouts, shaders, shelf show/hide, sketch; feeds parked P1/P3/P4/P5 (2026-10-24).
- [gui/measure-callouts-p5.md](gui/measure-callouts-p5.md): P5a/P5b Measure + live callouts implementation prep  -  two-point distance, edge length, volume (mm); viewport L×W×H / Ø×H while editing; before P5c sketch (2026-10-24).
- [gui/sketch-mvp-p5c.md](gui/sketch-mvp-p5c.md): P5c minimal sketch→extrude follow-on after P2  -  rect/circle on face, Blind extrude mm, no constraint solver; phone 44 px; OCCT MakePrism + validity/units (2026-10-24).
- [gui/post-p5c-next.md](gui/post-p5c-next.md): post-P5c next-queue candidates after P1-P5 close (#70) - deferred opens + ready digests for 3T pickup (2026-10-24).
- [gui/origin-plane-sketch.md](gui/origin-plane-sketch.md): origin-plane empty-doc sketch prep after P5c - world XY/XZ/YZ picker TBD, reuse Blind 10 mm MakePrism + OCCT/mm (2026-10-24).
- [gui/extrude-join-cut.md](gui/extrude-join-cut.md): Extrude Join/Cut prep after origin-plane (#77)  -  Fusion New/Join/Cut, Onshape New/Add/Remove, FreeCAD Pad/Pocket; reuse makePrismSolid + fuseShapes/cutShapes; TBD locks T1 - T5 (2026-10-24).
- [gui/touch-booleans-fillet.md](gui/touch-booleans-fillet.md): touch body Booleans + edge fillet/chamfer prep after Extrude Join/Cut (#83)  -  reuse fuseShapes/cutShapes/commonShapes and filletEdges/chamferEdges; phone ≥44 px; save/load deferred; TBD locks T1 - T7 (2026-10-24).
- [gui/measure-sketch-next.md](gui/measure-sketch-next.md): P6 measure/callouts delta after P5a - c  -  angle (degrees) + one-face area (mm²); sketch L×W/Ø callouts on the P5b pattern; T1 - T6 locked 2026-10-24 (2026-10-24).
- [gui/save-load-roundtrip.md](gui/save-load-roundtrip.md): save/load BREP-only round-trip prep after P6 (#98)  -  v1 .cadmvp, Union/Cut and sketch→extrude reload with null primitive, material tags; T1 - T6 locked 2026-10-24 (2026-10-24).
- [occt-wasm/booleans.md](occt-wasm/booleans.md): why Modo mesh Booleans fail, OCCT 8.0.1 Fuzzy/Glue/NonDestructive/SimplifyResult with libcascade 3.1.0 bindings, live-drag preview (ghost or manifold-3d) and exact OCCT on release (2026-10-21).
- [gui/booleans-fillet-chamfer.md](gui/booleans-fillet-chamfer.md): MODO MeshFusion strengths/limits (no source says it "failed"; Modo discontinued after 17.1), OCCT MakeFillet/MakeChamfer/Fuse + BRepCheck/FreeBounds gate, libcascade 3.1.0 bindings verified, L-bracket PROPOSAL with dims TBD (2026-10-21).
- [mobile-touch-cad.md](mobile-touch-cad.md): mobile touch patterns for the CAD viewport: hit sizes (WCAG 24/44 px, HIG 44 pt, Material 48 dp), tap vs drag (Android 8 dp slop), decimal entry in mm, next steps for step 2 gizmo (2026-10-21).
- [assemblies.md](assemblies.md): FreeCAD/Onshape/Fusion assembly models mapped to OCCT XCAF and 3MF build items/materials; XDE located instances, 3MF core transforms/basematerials; MVP flat part list (placement mm + PLA/PETG/TPU), Combine = BRepAlgoAPI_Fuse as one undo step, one 3MF object per part. Orca filament mapping still open (2026-10-22).
- [selection-and-delete.md](selection-and-delete.md): selection patterns, OCCT BRepAlgoAPI_Defeaturing limits/history/failure checks for delete, typed resize (params vs uniform/non-uniform scale) (2026-10-22).
- [cursor-vs-grok-tonight.md](cursor-vs-grok-tonight.md): overnight Grok Build (5 runs, ~$18.30) vs Cursor cloud agents (PR #1/#2, cost unknown): runs, rework, strengths, lessons, recommendation (2026-10-22).
- [cursor-and-tooling.md](cursor-and-tooling.md): Cursor vs Grok Build (cloud agents, Bugbot, rules/skills, MCP) plus tools to add (Playwright MCP, GitHub Actions + trimesh, OrcaSlicer CLI, lib3mf); top 3 recommended, sourced.
- [project-save-load.md](project-save-load.md): wrap-up item 4, end-to-end .cadmvp save, fresh-tab reload and compare checklist (P1-P7); undo stops at the loaded state (team ruling).
- [touch-gestures.md](touch-gestures.md): swipe gestures for the phone app: repo touch map, Onshape/Shapr3D/Nomad orbit, pan, undo and view-cube patterns, touch-action and pointercancel; 3T build order view-cube swipe, 3-finger undo/redo, value nudge (2026-10-23).
- [modo-theme-gui-tokens.md](modo-theme-gui-tokens.md): Modo to cad-mvp GUI token map; flat viewport (gradient revoked Erik ~11:24 AM MT); modo sel/hover #ffa829/#8cb4c7 shipped #231; panel/cool chrome + GL stops research/source only (2026-10-27 fold).
- [modo-factory-hex-from-media.md](modo-factory-hex-from-media.md): invent-free Modo factory hex from Foundry help PNGs + intro video; sel #ffa829 / hover #8cb4c7; GL stops source only; flat viewport stands (2026-10-27 ~11:30 AM MT).
- [modo-factory-hex-from-erik-screens-2026-10-27.md](modo-factory-hex-from-erik-screens-2026-10-27.md): invent-free Modo factory hex from Erik screens; panel/cool chrome reference only; GL stops source only; orange lock #ffa829 (2026-10-27 ~1:35 PM MT).
- [overnight-tool-search-exit.md](overnight-tool-search-exit.md): overnight item 1  -  Tool Search exit invent-free digest; Escape, outside click, `#searchBtn` toggle, and pick-to-close already exist; no in-dialog Cancel; `X` opens only; exit TBDs unbaked (2026-10-27 ~12:24 AM MT).
- [overnight-switch-hide-prior-tool-ui.md](overnight-switch-hide-prior-tool-ui.md): overnight item 2  -  switch tool/menu hides prior tool UI; extends P4 and always-visible chrome; panel-id taxonomy, Tool Search vs sketch/edge/modify, and cancel-vs-hide stay TBD (2026-10-27 ~12:24 AM MT).
