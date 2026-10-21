# Validation: watertight and units checks (STL and 3MF)

Checked 2026-10-20.

## Units
- In 3MF, the root `<model>` element has a `unit` attribute (default millimeter). Valid values are micron, millimeter, centimeter, inch, foot, and meter. [1][2]
- STL carries no units (see stl-3mf-step.md). The MVP must lock a unit and record it in our own metadata or the export dialog. Which unit: TBD for Erik (mm is the 3MF default).
- The official C++ library for reading and writing 3MF is lib3mf from the 3MF Consortium. [3]

## Watertight (required on every output)
Minimum checks before writing a file:
- every edge is shared by exactly two triangles (closed, edge-manifold)
- consistent outward winding, with no degenerate or zero-area triangles
- the B-Rep source passed BRepCheck (see ../healing/README.md)
- for 3MF: the file re-reads cleanly through lib3mf and `unit` matches the locked unit
- for STL: a re-read bounding box matches the expected size in the locked unit

`src/solid` checks an in-memory triangle mesh for the first two bullets (every edge shared by two triangles, consistent outward winding, no zero-area triangles). It does not run BRepCheck, lib3mf, or the STL bounding-box re-read. The contract is `../../mvp/solid-check.md`.

## Next steps
1. Grok Build: one validator in tests\ that runs these checks on every exported STL and 3MF and fails the build on any miss.

## Sources
1. https://3mf.io/spec/core-v1-3-0/
2. https://github.com/3MFConsortium/spec_core/blob/master/3MF%20Core%20Specification.md
3. https://github.com/3MFConsortium/lib3mf