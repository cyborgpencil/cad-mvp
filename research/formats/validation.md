# Validation: units and validity checks (STL and 3MF)

Checked 2026-10-20. Updated 2026-10-22 for Erik's 02:17 MT rule (2026-10-22, see UPDATES.md): watertight checks/tests dropped; Export no longer waits on watertight. Units checks and the OCCT validity check after fillet, chamfer, Boolean and delete stay.

## Units
- In 3MF, the root `<model>` element has a `unit` attribute (default millimeter). Valid values are micron, millimeter, centimeter, inch, foot, and meter. [1][2]
- STL carries no units (see stl-3mf-step.md). The MVP must lock a unit and record it in our own metadata or the export dialog. Which unit: TBD for Erik (mm is the 3MF default).
- The official C++ library for reading and writing 3MF is lib3mf from the 3MF Consortium. [3]

## Export gate (units only)
Export is gated on units. Watertight is not a gate (02:17 rule); `check_watertight` may still report, but it never blocks. Checks that stay:
- the B-Rep source passed BRepCheck after each op (see ../healing/README.md); a failure rolls the op back, it does not gate Export
- export refuses an empty or zero-triangle / zero-volume mesh, or an inside-out one (negative volume, logged as `FAIL: mesh is inside-out (negative volume).`), with a clear log error (3T calls, 2026-10-22, PR #11); that is a sanity check, not a watertight check
- for 3MF: the file re-reads cleanly through lib3mf and `unit` matches the locked unit
- for STL: a re-read bounding box matches the expected size in the locked unit

`src/solid` still has the in-memory triangle checker (edges shared by two triangles, winding, zero-area triangles); since PR #11 it reports only. The contract is `../../mvp/solid-check.md`.

## Next steps
1. Grok Build: one validator in tests\ that runs the units, 3MF re-read and STL bounds checks on every exported file and fails the build on any miss (no watertight assertion).

## Sources
1. https://3mf.io/spec/core-v1-3-0/
2. https://github.com/3MFConsortium/spec_core/blob/master/3MF%20Core%20Specification.md
3. https://github.com/3MFConsortium/lib3mf