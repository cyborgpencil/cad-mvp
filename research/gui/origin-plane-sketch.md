# Origin-plane empty-doc sketch (2026-10-24)

MVP Research Digest. Implementation prep for the next GB slice after P5c (3T lock, 2026-10-24 America/Denver): **sketch when the document has no body** by picking an origin / construction plane, then reusing the existing P5c rect/circle → Blind 10 mm path. Units: **mm**. Gate: OCCT validity + units (watertight dropped, 02:17 rule). Invent nothing; **TBD** marks need 3T or Erik.

Context: P5c is on `main` via [#70](https://github.com/cyborgpencil/cad-mvp/pull/70) (merge `7c83b2a`). Authoritative face path: [`research/gui/sketch-mvp-p5c.md`](sketch-mvp-p5c.md) + [`prompts/p5c-sketch-extrude.md`](../../prompts/p5c-sketch-extrude.md). That note’s **Still open**: origin-plane fallback when no body exists (empty-document first sketch) — not locked. Related queue note: [`research/gui/post-p5c-next.md`](post-p5c-next.md) (PR #72; may still be open at write time).

## 1. Context (P5c on main)

P5c behaviour (locked / shipped):

- Create → Sketch; **tap a planar face** sets the sketch plane (exclusive with V/E/F highlight; phone ≥44 CSS px).
- Tools: corner rectangle (L×W mm) + center circle (Ø mm); Finish Sketch keeps a closed profile.
- Extrude: Blind / Distance only; default depth **10 mm**; result = **new body**; kernel `BRepPrimAPI_MakePrism` via `makePrismSolid`; after commit OCCT validity + mm gate.
- **Out of P5c:** Join/Cut, constraints, origin-plane empty-doc.

Empty document = no body → **no planar face to tap**. Face-only P5c cannot start the first solid from a blank scene.

## 2. Typical CAD: first sketch on origin / construction planes (sourced)

| Product | Empty / no solid path | Planes | Sources |
|---|---|---|---|
| **Fusion** | Create Sketch → select initial plane or face. Valid selections include **origin planes**, work planes, and planar faces. | Document origin planes (XY / XZ / YZ naming in product UI; Autodesk also describes XY as default active plane in the 3D Sketch Manipulator). | Fusion Help, Create a sketch [1]; Autodesk Fusion blog sketches guide (first sketch on default origin planes) [2] |
| **Onshape** | New Sketch → **select the plane** to sketch on. Can also use a part face or Mate connector when geometry exists. Empty Part Studio still has default planes + Origin. | Default **Top, Front, Right** planes (+ Origin as reference). | Onshape Sketch Basics [3]; Onshape Part Studios (planes and Origin) [4] |
| **FreeCAD PartDesign** | **New Sketch** opens a Select-feature / attachment dialog to pick a plane; if no Body exists, New Sketch **creates a Body**. Body **Origin** exposes standard **XY, XZ, YZ** planes. | XY / XZ / YZ (Body Origin). | FreeCAD-documentation PartDesign NewSketch [5]; PartDesign Body Origin [6] |

Shared pattern: with no solid, the user still has **fixed world (or body) origin planes** to attach the first sketch — not only a face pick.

## 3. Gap vs MVP today (repo facts on `main` @ `7c83b2a`)

Facts from `web/index.html` / `web/occt-ops.mjs` (no invented behaviour):

- `action === 'newSketch'`: clears sketch geometry, switches to Sketch tab, sets hint **“Tap a planar face”**. No origin-plane branch.
- `setSketchPlane(faceId)` requires `state.meshCad`, `state.topology`, and a face id from topology; builds a frame via `viewApi.faceFrameFromTriangles`. Fail → hint **“Tap a planar face”** / non-planar toast.
- Sketch tab pointer pick calls `pickSketchFace` → `setSketchPlane` only (face path).
- Rectangle / Circle Confirm stay **disabled** until `state.sketchPlane` is set; sheet copy says **“Tap a planar face”**.
- `paintSketchVisuals` draws the plane fill from the **picked face’s triangles** — no origin-plane mesh path.
- Extrude already uses `plane.frame.outward` + `makePrismSolid` + `inspectSolid` gate (mm) — reusable once a frame exists without a face.
- Default session seeds a **20 mm cube** (`makeBoxSolid(oc, 20, 20, 20, …)`); blank / cleared scenes use `projectBlank` / `sceneCleared` when there are no bodies. Origin fallback is for the **no-body** case (delete-all / blank project), not the cube acceptance path.
- Prompt on main already states origin-plane fallback is **not locked** and out of P5c scope. [`prompts/p5c-sketch-extrude.md`](../../prompts/p5c-sketch-extrude.md)

| Area | Typical (above) | MVP today | Gap |
|---|---|---|---|
| Empty-doc plane | Origin XY/XZ/YZ (or Top/Front/Right) | Face pick only | Need origin / construction plane when `bodies.length === 0` (or no pickable faces) |
| UX | Plane dialog / picker | Hint “Tap a planar face” only | Plane picker or default + override (**TBD lock**) |
| After plane | Sketch tools → extrude | P5c rect/circle → Blind 10 mm already on main | Reuse; do not re-spec Extrude |
| Join/Cut | Often later | Not in P5c | Still later (3T: after this slice) |

## 4. Recommended MVP slice (propose — locks TBD for 3T)

Aligned with 3T’s next-slice lock: **origin-plane empty-doc first**, Extrude Join/Cut **later**. Prefer reusing P5c JS + libcascade bindings; no kernel rebuild unless a binding is missing (then stop and mark TBD).

1. **When:** Create → Sketch (or New Sketch) while there is **no body** / no pickable planar face (same empty-doc idea as `projectBlank` / zero bodies — exact predicate **TBD** with Pilot reading current state flags).
2. **Planes (propose):** offer at least **world XY**; preferably also **XZ** and **YZ** to match Fusion origin planes + FreeCAD Body Origin + Onshape’s three default planes [1][4][5][6]. **Team lock TBD:** XY-only vs all three.
3. **UX (propose, pick one — TBD):**
   - **A:** Plane picker sheet/chips (≥ **44 CSS px**, do not cover bottom bar) listing XY / XZ / YZ (names TBD: world vs Top/Front/Right labels).
   - **B:** Default **XY** immediately, with an override control to switch plane before Confirm on the first profile.
4. **Frame:** build a sketch frame at the world origin with orthonormal u/v and an outward normal consistent with Blind extrude (normal convention **TBD** — e.g. +Z for XY). Store on `state.sketchPlane` without requiring `faceId` from topology (schema detail for Pilot; keep face path unchanged when a face exists).
5. **After plane set:** **reuse P5c** — rect + circle (mm), Finish Sketch, Blind default **10 mm**, `makePrismSolid`, OCCT validity + mm gate, new body only.
6. **Phone:** all new plane controls ≥ 44 CSS px; portrait 390×844 smoke.
7. **Out of scope this slice:** Extrude Join/Cut; constraint solver; offset / angled construction planes with invented dimensions; Mate-connector / FreeCAD Body container invent; watertight gate; WASM rebuild.

### TBD locks for 3T / Erik

| # | Question | Propose (non-binding) |
|---|---|---|
| T1 | Which planes? | XY + XZ + YZ |
| T2 | Picker (A) vs default XY + override (B)? | A (explicit picker, clearer empty-doc) |
| T3 | Plane labels in UI? | World XY / XZ / YZ (mm) — or Onshape-style Top/Front/Right (**TBD**) |
| T4 | Extrude normal sense on origin planes? | Right-hand outward matching current face `outward` usage |
| T5 | Exact empty-doc predicate? | `state.bodies.length === 0` (and/or `projectBlank`) — Pilot confirms against code |

## 5. Next steps

1. **3T:** lock T1–T5 (or mark which stay Pilot-discretion).
2. **Doc Steward:** PROGRESS/UPDATES row + `prompts/` for this slice after locks; tip-match this research PR.
3. **Pilot / GB:** implement origin-plane path; keep face path regression; unit/smoke: empty doc → XY (or locked set) → rect 10×10 × Blind 10 mm new body, OCCT+mm; phone ≥44 px.
4. **Later (already queued):** Extrude Join/Cut; P1 Select-Other if still open ([`ui-gap-p2.md`](ui-gap-p2.md)).

## 6. Sources

Repo:

1. `research/gui/sketch-mvp-p5c.md` (Still open: origin-plane fallback)
2. `prompts/p5c-sketch-extrude.md` (origin-plane out of scope / not locked)
3. `research/gui/post-p5c-next.md` / PR #72 (next-queue; 3T picked origin-plane)
4. `web/index.html` on `main` @ `7c83b2a` (`newSketch`, `setSketchPlane`, `pickSketchFace`, sketch sheet gating, extrude commit)
5. `web/occt-ops.mjs` (`makePrismSolid` / `BRepPrimAPI_MakePrism`, `SKETCH_BLIND_DEPTH_MM`)
6. PR #70: https://github.com/cyborgpencil/cad-mvp/pull/70

Official / docs (no new product claims beyond cited pages):

7. Fusion Help, Create a sketch (origin planes / work planes / planar faces): https://help.autodesk.com/view/fusion360/ENU/?contextId=SKT-CREATE-3D-SKETCH  
8. Autodesk Fusion blog, How to Create Sketches (first sketch on default origin planes): https://www.autodesk.com/products/fusion-360/blog/sketches-in-fusion/  
9. Onshape Help, Sketch Basics (select plane; face or Mate connector when available): https://cad.onshape.com/help/Content/Sketch/sketch_basics.htm  
10. Onshape Help, Part Studios (default Top/Front/Right planes + Origin): https://cad.onshape.com/help/Content/PartStudio/part_studios.htm  
11. FreeCAD-documentation, PartDesign NewSketch: https://github.com/FreeCAD/FreeCAD-documentation/blob/main/wiki/PartDesign_NewSketch.md  
12. FreeCAD-documentation, PartDesign Body (Origin XY/XZ/YZ): https://github.com/FreeCAD/FreeCAD-documentation/blob/main/wiki/PartDesign_Body.md  
13. OCCT `BRepPrimAPI_MakePrism` (already used by P5c): https://dev.opencascade.org/doc/refman/html/class_b_rep_prim_a_p_i___make_prism.html  
14. Repo touch targets: `research/mobile-touch-cad.md` (44 px)
