# Selection, delete and typed resize (2026-10-22)

Delete UX is already decided by the chief (trash/Del, face delete heals or errors with model unchanged, edges/vertices only via owning feature, validity check + rollback, one undo step). This digest covers selection patterns and the OCCT backing. Units: mm. Watertight checks are dropped (Erik); the shape-validity check after each op stays.

## Selection patterns
- FreeCAD: box selection (Std BoxSelection) and selection methods incl. preselection and selection filters. https://wiki.freecad.org/Std_BoxSelection , https://wiki.freecad.org/Selection_methods
- Onshape: selection filters, box select, and "select other" for overlapped entities. https://cad.onshape.com/help/Content/selections.htm , https://cad.onshape.com/help/Content/select-other.htm
- Onshape mobile: tap to select, touch selection specifics. https://cad.onshape.com/help/Content/MobileHelp/mobile-select.htm
- Shapr3D: help site blocked automated fetch (403) — not cited; verify manually before relying on it.
- Existing in-repo spec: `gui/modo-selection-primitives.md` (V/E/F/Item modes) and `mobile-touch-cad.md` (hit sizes, tap slop).

## OCCT: BRepAlgoAPI_Defeaturing (face delete)
Sources: https://dev.opencascade.org/doc/refman/html/class_b_rep_algo_a_p_i___defeaturing.html , https://occt3d.com/dev/doc/refman/html/class_b_o_p_algo___remove_features.html
- Removes "holes, protrusions, gaps, chamfers, fillets etc."; input must be SOLID, COMPSOLID or COMPOUND of solids; **only FACEs can be removed**. Builds a new shape; input untouched (easy rollback).
- Method: groups faces into connected features, extends adjacent faces to cover the feature, trims, rebuilds the solid. Features removed one by one.
- Limits: adjacent faces must intersect (not tangent) or the feature likely won't be removed; extended adjacent faces must fully cover the feature; INTERNAL parts are dropped.
- Failure detection: `IsDone()` false / `HasErrors()` (AlertTooFewArguments, AlertNoFacesToRemove, AlertRemoveFeaturesFailed); `HasWarnings()` incl. **AlertUnableToRemoveTheFeature** (partial result — treat as fail for our UX). Then run BRepCheck_Analyzer on the result. https://dev.opencascade.org/doc/refman/html/class_b_rep_check___analyzer.html
- History: `SetToFillHistory(true)`; `Modified(s)`, `Generated(s)`, `IsDeleted(s)`, `History()` (BRepTools_History). Use to remap selections/ids after delete and to record which result faces came from which op (edge -> owning fillet/chamfer faces map).
- Inputs must be valid per BRepCheck_Analyzer; invalid shapes can be fixed with ShapeFix/ShapeAnalysis/ShapeUpgrade. https://dev.opencascade.org/doc/overview/html/specification__boolean_operations.html

## Resize by typed values
- Primitives: edit real parameters and rebuild (FreeCAD Part Box Length/Width/Height in the property editor). https://wiki.freecad.org/Part_Box , https://wiki.freecad.org/Property_editor
- Uniform scale: gp_Trsf::SetScale + BRepBuilderAPI_Transform (geometry type preserved). https://dev.opencascade.org/doc/refman/html/class_b_rep_builder_a_p_i___transform.html
- Non-uniform: gp_GTrsf + BRepBuilderAPI_GTransform; refman: underlying curves/surfaces may change, "a circle may be transformed into an ellipse". (B-spline conversion not stated on that page — unverified.) https://dev.opencascade.org/doc/refman/html/class_b_rep_builder_a_p_i___g_transform.html
- UIs: FreeCAD Draft Scale (typed X/Y/Z factors) https://wiki.freecad.org/Draft_Scale ; Onshape Transform (incl. scale) https://cad.onshape.com/help/Content/transform.htm ; Fusion Scale (uniform/non-uniform) https://help.autodesk.com/view/fusion360/ENU/?guid=SLD-SCALE-SOLID
- **Recommend:** primitives keep parameters and resize by typed mm values + rebuild; general bodies get uniform scale only in MVP; non-uniform (GTransform) deferred since it changes geometry types (circle -> ellipse, hurts later fillet/holes).

## Recommendation
Back face delete with BRepAlgoAPI_Defeaturing (history on); treat any error OR AlertUnableToRemoveTheFeature warning OR BRepCheck_Analyzer invalid as failure -> keep original shape. Edge/vertex delete: look up owning feature faces via recorded history and defeature those faces; no owner -> "Can't delete this edge on its own".

## Next steps for Cursor
1. Selection filter toggle (Vertex/Edge/Face/Body) + box select on desktop, tap select on phone.
2. `deleteFaces(shape, faces)` wrapper: Defeaturing -> checks above -> commit or rollback, one undo entry; smoke test removes a hole from a box (valid result) and a failing case leaves model unchanged.
3. Keep per-op history map (fillet/chamfer -> generated faces) for edge delete.
4. Primitive param panel (mm) + uniform scale field; units check in tests.
