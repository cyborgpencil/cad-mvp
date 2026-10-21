# Blender Relevant Features for CAD/CAM

## Core Strengths
- Mesh modeling, sculpting, freeform. High-performance viewport (Eevee/Cycles).
- Python API for scripting/addons.
- 3D Print Toolbox: manifold checks, repair.
- Built-in: MeasureIt (dimensions), CAD Transform (precise snaps).

## CAD Interoperability (via addons)
- STEP/IGES import/export: Angel STEP, StepXpert, Import CAD Model, Seamless CAD (OCCT-based feature tree in Blender).
- Preserve hierarchy, materials, colors. Some support parametric re-export.
- DXF/SVG native.

## Export
Native: STL, OBJ, FBX, glTF. Mesh-focused. STEP via addons (tessellated or hybrid).

## Limitations for CAD
Primarily mesh, not true B-Rep solids. Precision CAD needs kernels like OCCT. Good for organic/sculpting + mesh export.

## Strengths to Emulate
Intuitive freeform/sculpting. Excellent rendering/visualization. Strong Python ecosystem. Real-time performance.

Source: Blender docs, addon marketplaces, StackExchange.
