# Assemblies: parts, instances, placements, combine (2026-10-22)

Scope: how 3 CAD apps model assemblies, mapped to OCCT XCAF and 3MF, for the MVP (incl. Acceptance B toy truck: PLA wheels + TPU tires). Units: mm, checked on every export.

## How others do it
- **FreeCAD Assembly workbench** (built in since 1.0): parts are placed in an Assembly container and positioned with joints; each object has a Placement (position + rotation). https://wiki.freecad.org/Assembly_Workbench
- **FreeCAD App::Link**: a lightweight reference to another object, so one shape appears many times with its own placement (instances) without copying geometry. https://wiki.freecad.org/App_Link
- **FreeCAD combine**: Part Fuse unites shapes into one new solid (Boolean). https://wiki.freecad.org/Part_Fuse
- **Onshape**: parts are designed in a Part Studio; an Assembly holds *instances* of those parts, positioned by *mates*. https://cad.onshape.com/help/Content/partstudio.htm , https://cad.onshape.com/help/Content/assembly.htm , https://cad.onshape.com/help/Content/instances.htm , https://cad.onshape.com/help/Content/mates.htm
- **Fusion**: components hold bodies; each placement of a component is an occurrence; components are positioned with joints. https://help.autodesk.com/view/fusion360/ENU/?guid=ASM-COMPONENTS , https://help.autodesk.com/view/fusion360/ENU/?guid=ASM-JOINTS

Common pattern: shape definition is separate from placement (instance = definition + transform); constraints (mates/joints) are an extra layer on top.

## OCCT mapping (XCAF / XDE)
- XDE "separates shape definitions and their locations"; an assembly's components each reference one shape with a location; an instance is "a replication of another shape with a location". https://dev.opencascade.org/doc/overview/html/occt_user_guides__xde.html
- `XCAFDoc_ShapeTool` provides add-shape, add-component (reference + location), and assembly queries. https://dev.opencascade.org/doc/refman/html/class_x_c_a_f_doc___shape_tool.html
- Locations are `TopLoc_Location` (wrapping a gp_Trsf) on the component label (see XDE guide above).

## 3MF mapping
- Core spec: `<resources>` holds `<object>`s (mesh or `<components>`); `<build>` lists `<item objectid transform>`; a `<component>` references another object with a 3x4 `transform`; model `unit` attribute (set "millimeter"). https://github.com/3MFConsortium/spec_core/blob/master/3MF%20Core%20Specification.md
- Materials extension: `<basematerials>` + per-object/per-triangle `pid`/`pindex` assigns materials (wheel = PLA, tire = TPU as separate objects). https://github.com/3MFConsortium/spec_materials/blob/master/3MF%20Materials%20Extension.md
- Note: how OrcaSlicer maps 3MF objects to filaments/plates is not covered by these specs; verify in Orca during Acceptance B (TBD, no source yet).

## Recommendation (MVP)
**Flat list of parts, each = one solid + placement transform (mm) + material tag; no mates/joints; Combine = Boolean fuse of selected parts into a new part (originals removed, one undo step).**
Reasons: matches the shared definition+placement pattern in all three apps and XDE; maps 1:1 to 3MF build items/components and per-object materials, which is all Acceptance B needs; constraints are the costliest layer and not needed to print. Instances (one definition, many placements, e.g. 4 wheels) are a cheap add: store a shared shape id per part.

## Next steps for Cursor
1. Data model: `Part {id, name, shapeRef, transform(4x4, mm), material}`; parts panel list (select, rename, hide).
2. Move/rotate part edits only its transform; geometry untouched.
3. Combine: BRepAlgoAPI_Fuse on selected (transforms applied), validity check (BRepCheck_Analyzer), roll back on fail.
4. 3MF export: one object per part, build item with transform, basematerials per material, unit="millimeter"; smoke test round-trips 2 parts with 2 materials and checks units.
5. Save/load stores the same part list.
