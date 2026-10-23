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
- [gui/ui-layout-review.md](gui/ui-layout-review.md): Fusion, Onshape, FreeCAD and Blender UI layout review with tab-layout takeaways (2026-10-21).
- [gui/usability-checks.md](gui/usability-checks.md): pass/fail GUI checklist for touch targets, shortcuts, the Export gate, layout, the Repair tab and rotation (2026-10-21).
- [gui/wire-target.md](gui/wire-target.md): Qt app in src/ vs WASM browser page as the GUI wiring target, for Erik's choice (2026-10-21).
- [occt-wasm/pages-hosting.md](occt-wasm/pages-hosting.md): does the single-threaded OCCT WASM build fit GitHub Pages (limits, MIME, headers) (2026-10-21).
- [occt-wasm/prebuilt-options.md](occt-wasm/prebuilt-options.md): prebuilt OCCT WASM options (libcascade, opencascade.js, occt-import-js, official build) and reuse-vs-build verdict (2026-10-21).
- [projects/blink-mount.md](projects/blink-mount.md): Blink XT/XT2/Indoor/Outdoor mount specs (official vs measured), US door casing sizes, wood screw pilot/clearance holes for the L-bracket (2026-10-21).
- [gui/modo-tools.md](gui/modo-tools.md): Modo layout, theme (docs say orange accent; teal hex TBD) and MVP tools (Boolean, Edge Bevel, Work Plane, Action Center, snapping) with mockup restyle notes (2026-10-21).
- [gui/modo-selection-primitives.md](gui/modo-selection-primitives.md): MVP spec for selection modes (V/E/F/Item), hover vs selected CSS vars (colours TBD; orange vs teal pending Erik), Move gizmo, Box/Cylinder primitives mapped to BRepPrimAPI with the units gate and OCCT validity check (2026-10-21; watertight dropped 2026-10-22).
- [occt-wasm/booleans.md](occt-wasm/booleans.md): why Modo mesh Booleans fail, OCCT 8.0.1 Fuzzy/Glue/NonDestructive/SimplifyResult with libcascade 3.1.0 bindings, live-drag preview (ghost or manifold-3d) and exact OCCT on release (2026-10-21).
- [gui/booleans-fillet-chamfer.md](gui/booleans-fillet-chamfer.md): MODO MeshFusion strengths/limits (no source says it "failed"; Modo discontinued after 17.1), OCCT MakeFillet/MakeChamfer/Fuse + BRepCheck/FreeBounds gate, libcascade 3.1.0 bindings verified, L-bracket PROPOSAL with dims TBD (2026-10-21).
- [mobile-touch-cad.md](mobile-touch-cad.md): mobile touch patterns for the CAD viewport: hit sizes (WCAG 24/44 px, HIG 44 pt, Material 48 dp), tap vs drag (Android 8 dp slop), decimal entry in mm, next steps for step 2 gizmo (2026-10-21).
- [assemblies.md](assemblies.md): FreeCAD/Onshape/Fusion assembly models mapped to OCCT XCAF and 3MF build items/materials; XDE located instances, 3MF core transforms/basematerials; MVP flat part list (placement mm + PLA/PETG/TPU), Combine = BRepAlgoAPI_Fuse as one undo step, one 3MF object per part. Orca filament mapping still open (2026-10-22).
- [selection-and-delete.md](selection-and-delete.md): selection patterns, OCCT BRepAlgoAPI_Defeaturing limits/history/failure checks for delete, typed resize (params vs uniform/non-uniform scale) (2026-10-22).
- [cursor-vs-grok-tonight.md](cursor-vs-grok-tonight.md): overnight Grok Build (5 runs, ~$18.30) vs Cursor cloud agents (PR #1/#2, cost unknown): runs, rework, strengths, lessons, recommendation (2026-10-22).
- [cursor-and-tooling.md](cursor-and-tooling.md): Cursor vs Grok Build (cloud agents, Bugbot, rules/skills, MCP) plus tools to add (Playwright MCP, GitHub Actions + trimesh, OrcaSlicer CLI, lib3mf); top 3 recommended, sourced.
- [project-save-load.md](project-save-load.md): wrap-up item 4, end-to-end .cadmvp save, fresh-tab reload and compare checklist (P1-P7); undo stops at the loaded state (team ruling).
- [touch-gestures.md](touch-gestures.md): swipe gestures for the phone app: repo touch map, Onshape/Shapr3D/Nomad orbit, pan, undo and view-cube patterns, touch-action and pointercancel; 3T build order view-cube swipe, 3-finger undo/redo, value nudge (2026-10-22).
