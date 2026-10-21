# CAD/CAM Project Research Index

Organized knowledge for high-performance custom CAD/CAM combining Autodesk, Adobe, FreeCAD, and Blender features.

## Current Documents

- **MVP**: See `../mvp/requirements.md` (design-to-print scope only).
- **Solid check**: See `../mvp/solid-check.md` (in-memory triangle watertight gate).
- **Mesh view**: See `../mvp/mesh-view.md` (desktop window over the watertight checker).
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
- `formats/`: STL, 3MF, STEP details, plus `validation.md` (watertight and units checks). (MVP)
- `ai-mcp/`: Model Context Protocol for first-class AI tools. (MVP; tool list TBD for Erik)
- `simulations/`: FEA, CAM path, motion types. (post-MVP background)
- `architecture/`: Kernel, components, performance notes. (MVP scope section conflicts with design-to-print scope; pending Erik.)
- `occt-wasm/`: OCCT to WebAssembly build options. (MVP)
- `healing/`: B-Rep and mesh validation and repair. (MVP)
- `gui/`: Fusion-style layout, Blender-style ops mapped to OCCT B-rep, browser input, and GUI screenshot tests (`gui/README.md`). (plan input; scope conflicts pending Erik)

## Notes

Update research here first. Propagate only confirmed changes into MVP or vision docs. Keep documents consistent with the project-organizer skill (`../.grok/skills/project-organizer/`). Note: a "document-upgrader" skill was referenced here but does not exist in the repo.
