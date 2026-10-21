# File Formats: STL, 3MF, STEP

## STL (Stereolithography)
- Mesh of triangles. No units, no color, no metadata.
- Universal for 3D printing. Simple, large files for curves.
- Best: Max compatibility. Worst: Faceting, scale issues, non-editable.

## 3MF (3D Manufacturing Format)
- ZIP+XML. Mesh + units, colors, materials, multi-parts, assemblies, print settings/profiles.
- Modern replacement for STL. Smaller, validated.
- Best: Slicer workflows, multi-color/material, context. ISO/IEC 25422:2025.

## STEP (ISO 10303)
- Exact B-Rep solids: NURBS, curves, surfaces, assemblies, units, PMI possible.
- Neutral CAD exchange (Fusion, SolidWorks, FreeCAD, etc.).
- Best: Editable, precise for CAM/CNC, manufacturing. Requires tessellation for printing.

## MVP Recommendations
- Native: Parametric B-Rep (STEP-like).
- Export: STEP (master), STL (print), 3MF (print+metadata).
- Support import of all three.

Source: Multiple 3D printing guides (2025-2026).
