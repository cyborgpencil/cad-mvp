# Extrude Join / Cut (after origin-plane) — 2026-10-24

MVP Research Digest. Implementation prep for the next GB slice after origin-plane empty-doc ([#77](https://github.com/cyborgpencil/cad-mvp/pull/77) on `main` at merge `347888e`; latest `main` at write includes UPDATES [#78](https://github.com/cyborgpencil/cad-mvp/pull/78) tip `92c2ab0`). Units: **mm**. Gate: OCCT validity + units (watertight dropped, 02:17 rule). Invent nothing; **TBD** marks need 3T or Erik. Research only — no `web/`, prompts, UPDATES, PROGRESS, kernel, or WASM edits in this PR.

Related (reuse; do not contradict): [`post-p5c-next.md`](post-p5c-next.md) (Join/Cut deferred), [`sketch-mvp-p5c.md`](sketch-mvp-p5c.md), [`origin-plane-sketch.md`](origin-plane-sketch.md), [`prompts/p5c-sketch-extrude.md`](../../prompts/p5c-sketch-extrude.md), [`prompts/origin-plane-empty-doc.md`](../../prompts/origin-plane-empty-doc.md), [`../occt-wasm/booleans.md`](../occt-wasm/booleans.md), [`booleans-fillet-chamfer.md`](booleans-fillet-chamfer.md).

## 1. Context (repo facts on `main`)

P5c Blind **New Body** is on `main` via [#70](https://github.com/cyborgpencil/cad-mvp/pull/70). Origin-plane empty-doc is on `main` via [#77](https://github.com/cyborgpencil/cad-mvp/pull/77). Face tap and origin Top/Front/Right both set `state.sketchPlane`; Extrude is Blind/Distance default **10 mm** (`SKETCH_BLIND_DEPTH_MM`) → new body.

Facts from `web/index.html` + `web/occt-ops.mjs` on `main` @ `92c2ab0` (parent of tip includes `347888e`):

- `commitSketchExtrude()`: reads Blind depth → `makePrismSolid(oc, profile.shape, n*depth)` → `inspectSolid` OCCT+mm gate → **always** `state.bodies.push(body)` with `kind: 'extrude'`. Toast: “New body.” No Join/Cut branch.
- Extrude sheet: Blind depth field + Confirm only. `TOOL_INSP['Extrude (Push/Pull)']` subtitle is **“Blind distance. New body.”** No mode chips/radios for Join/Cut on that sheet.
- Separate Modify Boolean chrome already exists: Union / Cut / Intersect (`data-action="boolean"`, `data-op` union|cut|intersect) — body-vs-body, not Extrude-into-body. Do not confuse Extrude Cut with that tool.
- Body list: `state.bodies[]` with `id`, `name`, selection helpers (`findBody`, multi-body item select). No Extrude “target body” picker today.
- libcascade boolean helpers already in `web/occt-ops.mjs`: `fuseShapes` / `cutShapes` / `commonShapes` wrapping `BRepAlgoAPI_Fuse` / `Cut` / `Common` (NonDestructive pattern, SimplifyResult on fuse, gate via existing checkers). Documented earlier in [`../occt-wasm/booleans.md`](../occt-wasm/booleans.md) and [`booleans-fillet-chamfer.md`](booleans-fillet-chamfer.md).
- Prompts already mark Join/Cut **out of scope** for P5c and origin-plane.

3T (2026-10-24 ~6:40 AM America/Denver): next GB slice is **Extrude Join/Cut** (locked after origin-plane). P1–P5 queue closed — do not restart.

## 2. Typical CAD Extrude modes (sourced)

| Product | New / separate | Join / add | Cut / remove | Intersect / common | Notes | Sources |
|---|---|---|---|---|---|---|
| **Fusion Extrude** | **New Body** | **Join** | **Cut** | **Intersect** | Operation controls how the extruded solid affects the design. New Component is Hybrid-only (out of MVP). | Fusion Extrude reference [1]; Solids from sketches [2] |
| **Onshape Extrude** | **New** | **Add** | **Remove** | **Intersect** | Solid Extrude result types; Merge scope picks which parts Add/Remove/Intersect affect. First Extrude must be New when no parts exist. | Onshape Extrude [3]; Boolean Options lesson [4] |
| **FreeCAD PartDesign** | New Body + Pad starts a solid | **Pad** (additive on active Body) | **Pocket** (subtractive on active Body) | PartDesign Boolean **Common** (separate tool) | Pad/Pocket are cumulative on one Body; Fuse/Cut/Common across Bodies via PartDesign Boolean. | FreeCAD wiki PartDesign Pad [5]; Pocket [6]; Boolean [7]; Workbench overview [8] |

OCCT mapping already used in-repo: prism = `BRepPrimAPI_MakePrism` / `makePrismSolid` [9]; Join ≈ `BRepAlgoAPI_Fuse` / `fuseShapes`; Cut ≈ `BRepAlgoAPI_Cut` / `cutShapes` [10][11].

## 3. Gap vs MVP today

| Area | Typical (above) | MVP today | Gap |
|---|---|---|---|
| Extrude result mode | New / Join(Add) / Cut(Remove) [/ Intersect] | New body only | Mode UI + commit path for Join and Cut |
| Target body | Merge scope / affected bodies | Always push new `state.bodies` entry | Pick or default target when `bodies.length > 1` (**TBD**) |
| Kernel | Prism then boolean | Prism only in Extrude path | After prism: Fuse or Cut into target; keep Blind New Body |
| Booleans elsewhere | Dedicated Boolean tools | Union/Cut/Intersect already in Modify | Reuse `fuseShapes`/`cutShapes`; do not re-invent Modify Boolean |
| Phone | ≥44 px controls | Sketch Confirm / origin chips already 44 px | New mode controls ≥44 CSS px; no bottom-bar cover |

## 4. Recommended MVP slice (propose — locks TBD)

Prefer JS + existing libcascade 3.1.0 bindings in `web/occt-ops.mjs`. No kernel / WASM rebuild. No invent of multi-body pick UX beyond a simple default until 3T locks T1.

1. **Keep** Blind / Distance default **10 mm**, typed override, OCCT validity + mm gate, phone ≥44 px.
2. **Keep** Blind **New Body** path as today (`makePrismSolid` → push body).
3. **Add Join:** prism tool solid → `fuseShapes(target, prism)` (or order matching existing boolean demos) → replace target body shape; drop/discard standalone prism body. On failure: keep last good shapes (standing boolean UX from booleans digests).
4. **Add Cut:** prism → `cutShapes(target, prism)` → replace target; same failure keep-last-good rule. Empty / fully-removed result handling = **TBD** (T3).
5. **UI (propose):** Extrude sheet mode control — **New / Join / Cut** (chips or sheet radios — **TBD** T4). Subtitle today says “New body.” only; extend after lock.
6. **Paths:** apply Join/Cut on **both** face-plane and origin-plane Extrude commits (same `commitSketchExtrude`) unless 3T locks otherwise (**TBD** T5). Join/Cut when `bodies.length === 0` is invalid — keep New only (matches Onshape “first Extrude must be New” [4]).
7. **Out of scope this slice:** Intersect unless already cheap via `commonShapes` and 3T asks; invent multi-body picker beyond default; Up-to / Through-all extents; Modify Boolean redesign; constraint solver; watertight gate; kernel rebuild.

## 5. TBD locks for 3T / Erik (non-binding proposes)

| # | Question | Propose (non-binding) |
|---|---|---|
| T1 | Target body when multiple bodies? | Selected item body if exactly one body selected; else the sketch-plane’s owning body when face path; else newest body — **Pilot confirms against selection helpers; no invent of a full body picker this slice** |
| T2 | Default mode after Finish Sketch? | **New** when `bodies.length === 0`; **Join** when a body exists and the profile is on a face of that body; else **New**. User can override. |
| T3 | Cut that removes entire body / empty result? | Reject commit; keep prior body; toast clear “Cut removed the whole body” (or similar). Do not leave an empty body entry. Exact copy **TBD**. |
| T4 | UI: mode chips vs sheet radio? | Chips on Extrude sheet (≥44 CSS px), same pattern as origin Top/Front/Right. |
| T5 | Origin-plane + face paths both get Join/Cut? | **Yes** — one `commitSketchExtrude` mode switch; origin empty-doc still defaults New until a body exists. |

## 6. Next steps

1. **3T:** lock T1–T5 (or mark Pilot-discretion).
2. **Doc Steward:** tip-match this research PR; write Extrude Join/Cut prompt after locks; PROGRESS/UPDATES when implementation opens.
3. **Pilot / GB:** implement after prompt tips — mode UI + Join Fuse + Cut; keep Blind New Body; smoke: cube face rect → Join; circle → Cut pocket; empty-doc origin still New; phone ≥44 px; regression primitives + origin picker.
4. **Repo Keeper:** plain-merge this research PR (Digest is author — do not self-APPROVE).

## 7. Sources

Repo:

1. `web/index.html` — `commitSketchExtrude`, Extrude sheet (`sketchDepth`), `TOOL_INSP` Extrude “New body.”, Modify boolean Union/Cut/Intersect, `state.bodies`, origin Top/Front/Right chips
2. `web/occt-ops.mjs` — `SKETCH_BLIND_DEPTH_MM`, `makePrismSolid` / `BRepPrimAPI_MakePrism`, `fuseShapes`, `cutShapes`, `commonShapes`
3. `research/gui/post-p5c-next.md` — Join/Cut deferred after P5c
4. `research/gui/sketch-mvp-p5c.md` — Blind New Body; Join/Cut later
5. `research/gui/origin-plane-sketch.md` — Join/Cut later after origin-plane
6. `prompts/p5c-sketch-extrude.md` — Join/Cut out of scope
7. `prompts/origin-plane-empty-doc.md` — Join/Cut out of scope
8. `research/occt-wasm/booleans.md` — Fuse/Cut options + failure UX
9. `research/gui/booleans-fillet-chamfer.md` — libcascade Fuse/Cut bindings verified
10. PR #70: https://github.com/cyborgpencil/cad-mvp/pull/70
11. PR #77: https://github.com/cyborgpencil/cad-mvp/pull/77
12. Team lock (3T / CAD CAM MVP room, 2026-10-24 ~6:40 AM America/Denver): next GB slice Extrude Join/Cut after origin-plane on main.

Official / docs:

13. Fusion Help, Extrude reference (Operation Join / Cut / Intersect / New Body): https://help.autodesk.com/cloudhelp/ENU/Fusion-Model/files/SLD-REF-EXTRUDE.htm
14. Fusion Help, Solids from sketches (same Operation table): https://help.autodesk.com/cloudhelp/ENU/Fusion-Model/files/SLD-CREATE-SOLID-FROM-SKETCH.htm
15. Onshape Help, Extrude (New / Add / Remove / Intersect; Merge scope): https://cad.onshape.com/help/Content/PartStudio/extrude.htm
16. Onshape Learning, Boolean Options (first Extrude New; Merge scope): https://learn.onshape.com/learn/video/boolean-options
17. FreeCAD documentation, PartDesign Pad: https://wiki.freecad.org/PartDesign_Pad (also https://github.com/FreeCAD/FreeCAD-documentation/blob/main/wiki/PartDesign_Pad.md)
18. FreeCAD documentation, PartDesign Pocket: https://wiki.freecad.org/PartDesign_Pocket (also https://github.com/FreeCAD/FreeCAD-documentation/blob/main/wiki/PartDesign_Pocket.md)
19. FreeCAD documentation, PartDesign Boolean (Fuse / Cut / Common): https://wiki.freecad.org/PartDesign_Boolean
20. FreeCAD documentation, PartDesign Workbench (Pad additive / Pocket subtractive): https://wiki.freecad.org/PartDesign_Workbench/en
21. OCCT `BRepPrimAPI_MakePrism`: https://dev.opencascade.org/doc/refman/html/class_b_rep_prim_a_p_i___make_prism.html
22. OCCT Boolean Operations guide: https://dev.opencascade.org/doc/overview/html/specification__boolean_operations.html
23. Repo touch targets: `research/mobile-touch-cad.md` (≥44 CSS px)
