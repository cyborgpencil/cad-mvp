# Simulations in CAD/CAM

## Types for MVP
- **Structural/FEA**: Stress, deformation, modal frequency, buckling (static/dynamic).
- **Thermal**: Heat transfer, thermal stress.
- **Motion/Kinematic**: Assemblies, joints, collisions.
- **CAM Simulation**: Toolpath verification, stock removal, collision detection, machine simulation.
- **Manufacturability**: Injection molding, sheet metal, additive process sim.

## From Tools
- Fusion: Built-in FEA, generative, cloud solves.
- FreeCAD: FEM workbench (CalculiX etc.), CAM sim.
- Blender: Basic physics, but not engineering-grade.

## Requirements
- Validated solvers. Mesh generation from B-Rep. Result visualization (stress plots, animations).
- High-performance: Multi-core/GPU for large solves. Progressive results.

## MVP Priority
1. Basic CAM path simulation + collision.
2. Simple static stress FEA.
3. Assembly motion.

Source: Autodesk/FreeCAD feature lists.
