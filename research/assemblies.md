# Assemblies: parts, instances, placements, combine (2026-10-22, refreshed)

Scope: how CAD apps and formats model assemblies, mapped to OCCT XDE and 3MF, for the MVP (incl. Acceptance B toy truck: PLA wheels + TPU tires). Units: mm, checked on every export.

## How others do it
- **FreeCAD Assembly workbench** (built in since 1.0): parts sit in an Assembly container, positioned with joints; each object has a Placement (position + rotation). https://wiki.freecad.org/Assembly_Workbench
- **FreeCAD App::Link**: a lightweight reference so one shape appears many times, each with its own placement, without copying geometry. https://wiki.freecad.org/App_Link
- **FreeCAD combine**: Part Fuse unites shapes into one new solid. https://wiki.freecad.org/Part_Fuse
- **Onshape**: parts are modeled in a Part Studio; an Assembly holds *instances* of them, positioned by *mates*. https://cad.onshape.com/help/Content/partstudio.htm , https://cad.onshape.com/help/Content/assembly.htm , https://cad.onshape.com/help/Content/instances.htm , https://cad.onshape.com/help/Content/mates.htm
- **Fusion**: components contain bodies; each placement of a component is an occurrence; joints position components. https://help.autodesk.com/view/fusion360/ENU/?guid=ASM-COMPONENTS , https://help.autodesk.com/view/fusion360/ENU/?guid=ASM-JOINTS

Common pattern: shape definition is separate from placement (instance = definition + transform); constraints (mates/joints) are an extra layer on top.

## OCCT (XDE / XCAF)
- XDE stores shapes and located instances separately: "the corresponding shapes (without location) appear at distinct sub-labels. They are referred to by a shape instance, which associates a location". Top-level shapes are either referenced or *free shapes* (roots). https://dev.opencascade.org/doc/overview/html/occt_user_guides__xde.html
- `XCAFDoc_ShapeTool::AddComponent(refLabel, TopLoc_Location)` adds a located reference; `IsReference(label)` + `GetLocation(label)` read it back (same guide). Class ref: https://dev.opencascade.org/doc/refman/html/class_x_c_a_f_doc___shape_tool.html
- Placement types: `gp_Trsf` (rigid transform) wrapped by `TopLoc_Location`; `shape.Located(loc)` / `Moved(loc)` keep geometry shared, while `BRepBuilderAPI_Transform(shape, trsf, copy)` produces transformed geometry. https://dev.opencascade.org/doc/refman/html/class_top_loc___location.html , https://dev.opencascade.org/doc/refman/html/class_b_rep_builder_a_p_i___transform.html
- MVP does not need an XDE document; a plain part list of `TopoDS_Shape` + transform is enough. XDE becomes useful if STEP assembly export is added later (TBD, post-MVP).

## 3MF (core spec 1.4.0)
- `<model unit="millimeter">`; unit default is millimeter; valid units micron..meter. `<resources>` holds `<basematerials>` and `<object>`s (mesh OR `<components>`); `<build>` lists `<item objectid transform>`. https://github.com/3MFConsortium/spec_core/blob/master/3MF%20Core%20Specification.md
- Transform: row-major affine, 12 values "m00 m01 m02 m10 m11 m12 m20 m21 m22 m30 m31 m32"; translation is m30..m32 in model units (mm). Negative-determinant transforms must not flip volume sign (same spec, 3.3).
- `<basematerials>` is in the **core** spec (ch. 5): `<base name displaycolor>`; object gets material via `pid`/`pindex`. Producers MUST NOT put pid/pindex on objects that contain components (4.0). Richer colour/multi-property: Materials extension https://github.com/3MFConsortium/spec_materials/blob/master/3MF%20Materials%20Extension.md
- Overlapping build items/components MUST be united by the device; devices MUST NOT move components relative to each other (3.4.3, 4.2).
- **lib3mf**: `CModel::AddComponentsObject()`, `CComponentsObject::AddComponent(obj, transform)`, `CModel::AddBuildItem(obj, transform)`. https://lib3mf.readthedocs.io/en/stable/source/Cpp/lib3mf_ComponentsObject.html , https://lib3mf.readthedocs.io/en/release-2.3.1/source/Cpp/lib3mf_Model.html
- Note: OrcaSlicer's mapping of 3MF objects/basematerials to filaments and plates is not in these specs; verify in Orca during Acceptance B (TBD, no source).

## Recommendation (MVP, per Chief ruling 02:21 MT in web/PROGRESS.md)
**Flat list of parts; each = one solid + placement (mm) + material tag. No mates/joints. Combine = BRepAlgoAPI_Fuse of the selected parts into a new part. Export = one 3MF object per part with its material.**
Why: matches the definition+placement pattern of all three apps and XDE; maps 1:1 onto 3MF objects/build items/basematerials, which is all Acceptance B needs; constraints are the costliest layer and not needed to print.

## Implementation tips
1. Data model: `Part {id, name, shape, placement(gp_Trsf, mm), material}`; parts panel (select, rename, hide).
2. Move/rotate edits only `placement` (store as `TopLoc_Location(gp_Trsf)`); geometry untouched. Bake (`BRepBuilderAPI_Transform`) only at Combine and at export, so the stored solid stays unmoved and placement round-trips exactly in save/load.
3. Combine: bake each selected part's placement, `BRepAlgoAPI_Fuse`, check `HasErrors()`, then `BRepCheck_Analyzer::IsValid()` + the watertight gate; on fail, roll back and keep originals. New part gets identity placement and the first-selected part's material (TBD: confirm with Erik). Mixed materials in one Combine: block or warn (TBD).
4. Combine is ONE undo step (remove N parts + add 1 part as a single snapshot in web/undo.mjs).
5. Copies: deep copy (new independent solid) for MVP; no shared instances (App::Link/Onshape-style). Reason: simpler undo, save/load and Combine; 3MF components can be added later for size if needed.
6. 3MF export: `unit="millimeter"`, one `<basematerials>` group (one `<base>` per material tag, name = tag e.g. "PLA"/"TPU"), one mesh object per part with `pid`/`pindex`, one build item each with the placement as the 12-value matrix (mm). Mesh objects are separate, not `<components>`, so per-object materials stay legal.
7. Checks on export: units mm; every object watertight; volume compared via `BRepGProp::VolumeProperties` on the exact solid (not mesh) to 0.01 mm3 tolerance. https://dev.opencascade.org/doc/refman/html/class_b_rep_g_prop.html
8. Smoke test: 2 parts, 2 materials, non-identity placements; export, re-read, assert unit, object count, materials and translations.

## Open TBDs (ask Erik via Chief)
- Material tag list (PLA/TPU only, or free text?) and displaycolor per tag.
- Combined part's material when inputs differ.
- Whether export is one 3MF with all parts (assumed) or one file per part.
- Orca filament/plate mapping of basematerials (Acceptance B, Pilot).