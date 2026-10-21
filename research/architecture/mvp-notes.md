# Architecture Notes for High-Performance CAD/CAM MVP

## Core Components
1. **Geometry Kernel**: OpenCASCADE (OCCT) for B-Rep, NURBS, booleans, STEP. Proven, free, used by FreeCAD.
2. **Parametric Engine**: History tree, constraints (sketcher solver), property system.
3. **Visualization**: High-perf viewport (OpenGL/Vulkan). Mesh tessellation on demand.
4. **CAM Engine**: Toolpath generation (2.5D first), post-processors, G-code.
5. **Simulation**: Integrate lightweight FEA or external.
6. **AI Layer**: MCP server + internal agent for natural language ops.
7. **UI**: 2D/3D tools unified. Sketch on planes, extrude, freeform mesh hybrid.
8. **Data**: Native parametric format + export STEP/STL/3MF.

## Performance Goals
- Single-thread heavy for modeling (high clock CPU).
- Multi-core for CAM/sim/mesh.
- GPU for viz/render.
- Low latency interactive edits.

## MVP Scope
- 2D sketch + 3D extrude/revolve/boolean/fillet.
- Export STL/3MF/STEP.
- Basic CAM (2.5D) + sim.
- MCP AI tools for design ops.
- Hybrid mesh (Blender-like freeform).

## Tech Stack Ideas
- Kernel: OCCT + custom parametric layer.
- UI: Qt or web (WASM OCCT).
- Scripting: Python or Rust bindings.
- AI: MCP + local LLM integration.

Sources: Spatial components, FreeCAD architecture, workstation guides.
