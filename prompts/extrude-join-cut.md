# Extrude Join and Cut

Team-chosen by Doc Steward / 3T, 2026-10-24 (America/Denver). These locks are final. P5c Blind New Body is on main via #70 (`7c83b2a`). Origin-plane empty-doc is on main via #77 (`347888e`). Read `research/gui/sketch-mvp-p5c.md` (Fusion Extrude New Body / Join / Cut; Onshape New / Add / Remove; `BRepPrimAPI_MakePrism`), `research/gui/post-p5c-next.md` (Join/Cut deferred from P5c), `research/occt-wasm/booleans.md` (Fuse/Cut, NonDestructive, SimplifyResult, keep the last valid shape), `prompts/p5c-sketch-extrude.md`, and `prompts/origin-plane-empty-doc.md`. Fusion Extrude solid: https://help.autodesk.com/view/fusion360/ENU/?contextId=SLD-EXTRUDE-SOLID . Onshape Extrude: https://cad.onshape.com/help/Content/PartStudio/extrude.htm . Feed this to Grok Build / Cursor. This file is the spec. It does not change the app.

## Context
- WASM UI in `web/` (mostly `web/index.html`, plus `web/occt-ops.mjs`). Work in the Z13 repo (`C:\Dev\cadcam-mvp`).
- Units stay millimetres.
- After modeling ops, keep the OCCT shape-validity check and the millimetre units check. Watertight was dropped (02:17 rule).
- P5c already runs from Create → Sketch. A face tap stores `state.sketchPlane` as `{ faceId, bodyId, frame }`. Rectangle (corner, L×W mm) and center circle (Ø mm) build a closed profile. Finish Sketch returns to Model and keeps that profile. Blind / Distance opens at **10 mm** (`SKETCH_BLIND_DEPTH_MM`). Commit goes through `makePrismSolid` / `BRepPrimAPI_MakePrism` along `frame.outward` and adds a new body.
- Origin-plane empty-doc shows the picker only when `state.bodies.length === 0`. Picking Top, Front, or Right stores `{ faceId: '', bodyId: '', originPlane, frame }` at the world origin. When any body exists, Create → Sketch still uses the face tap. Top / XY outward is +Z.
- The default session seeds one 20 mm cube, centre (0, 0, 10), from z = 0 to z = 20. Volume is 8000 mm³.
- Interactive body Booleans already exist. Union, Cut, and Intersect call `fuseShapes`, `cutShapes`, and `commonShapes` in `web/occt-ops.mjs`. A failed or empty Boolean keeps the inputs.
- Do not commit `.wasm`, `web/cadcam.wasm`, or `web/dist/`. Do not edit `UPDATES.md`. Do not add or edit a root `PROGRESS.md`. Leave `web/PROGRESS.md` for a separate scrub.
- Prefer JS, CSS, and HTML, plus the existing libcascade 3.1.0 JS bindings. No kernel, C++, `src/`, `web/bindings.cpp`, or `cadcam.wasm` rebuild. If a needed binding is missing, stop and report it. Do not add a second Boolean path.
- Commit on a PR branch. Never push to main. Repo Keeper merges after `ci.yml` is green.

## Team-chosen behaviour
The Extrude sheet gains Join and Cut beside the current New Body path. Blind depth and the prism stay as they are. Join and Cut then Boolean that prism onto one target body.

### Ops
The Extrude sheet offers three modes: **New Body** (the current P5c default), **Join**, and **Cut**. The sheet opens on New Body, so a confirm with no mode change still adds a body. This sketch-extrude slice has no Intersect mode. Body-level Intersect already exists and stays on the Boolean toolbar.

### Labels
The mode labels are New Body, Join, and Cut. Join and Cut use those words. Cut matches the Boolean toolbar. Onshape's Add and Remove are not the labels here.

### Blind depth
Blind / Distance still opens at **10 mm** (`SKETCH_BLIND_DEPTH_MM`). A typed depth in mm overrides that default for New Body, Join, and Cut. The prism vector is `frame.outward` times that depth, the same vector `commitSketchExtrude` uses today. This slice adds no flip, two-sided, or symmetric direction.

### Kernel path
Build the solid from the closed profile with `makePrismSolid` / `BRepPrimAPI_MakePrism`.

- New Body: add the prism as a body, the way P5c does today.
- Join: `fuseShapes(target, prism)`, or the existing fuse wrapper those body Booleans already call.
- Cut: `cutShapes(target, prism)`. The target is the object and the prism is the tool (target minus tool).

Call those wrappers. Leave the shared Boolean helper as it is. It already follows the body-Boolean pattern: NonDestructive so a failed op can leave the inputs alone, IsDone before Shape, and SimplifyResult on fuse.

On failure, keep the prior bodies, show an error, and do not install the result. Failure includes a wrapper that returns not ok, an empty solid, an OCCT validity failure, or a millimetre units failure. A Cut whose tool misses the target is the same kind of failure: the result volume is not lower than the target volume. Release the rejected prism with the existing `delete()` path. It must not remain in the scene.

After a successful Join or Cut, run the same OCCT validity check and millimetre units check the New Body extrude already runs. Watertight stays off.

### Target body
- Face plane (`faceId` set): the Join/Cut target is that face's body. Use `bodyId` when it is set. When `faceId` is set and `bodyId` is blank, use the body that owns that face. Item selection is not required. If no body owns the face, Join and Cut stay disabled.
- Origin plane (no face): Join and Cut stay disabled until exactly one body is selected with Item (hotkey 4). Zero bodies, or any selection other than exactly one body, keeps Join and Cut disabled. New Body stays available with no selection, including on an empty document.
- The origin picker still appears only when `state.bodies.length === 0`. An origin-plane profile kept by Finish Sketch stays in place when a body is added afterwards, so that body can be selected as the target. Adding the body does not turn the plane into a face plane. Start Sketch still clears the profile, and a successful extrude still clears it.

### When Join or Cut succeeds
The result replaces the target. The body count does not increase, and the prism is not left as its own body. New Body still adds a body.

### Phone
Every new op chip is at least 44 CSS px. The chips do not cover the bottom bar. The portrait check is 390×844.

## Acceptance
- Default 20 mm cube, top-face sketch (highest Z, outward +Z), corner rect 10×10 mm, Extrude Blind 10 mm, mode **Join**. One body remains. The boss lies outside the cube, so the volume is 9000 mm³ (8000 plus 10×10×10), within 0.5 mm³. That volume is greater than the cube and greater than the overlapping Cut below. OCCT validity passes and the mm gate passes. The prism is not a second body.
- **Cut** with a prism that overlaps the cube. One body remains, the volume is less than 8000 mm³, OCCT validity passes, and the mm gate passes. Concrete overlap, using the locked outward vector: empty doc, Top / XY, corner rect 10×10 mm (the #77 placement, from the origin along +X and +Y), Finish Sketch, add one 20 mm box at the seeded centre (0, 0, 10), select that body with Item, Extrude Blind 10 mm, mode Cut. The prism occupies x 0..10, y 0..10, z 0..10 and lies inside the box. Volume is 7000 mm³, within 0.5 mm³.
- **New Body** is unchanged. The same top-face sketch, rect 10×10 mm, Blind 10 mm, left on New Body, ends with two bodies.
- Origin-plane empty doc: New Body still commits (rect 10×10 mm and circle Ø10 mm, Blind 10 mm, as #77). Join and Cut stay disabled while no body exists. On an origin plane they stay disabled until exactly one body is selected.
- Failed Cut when the tool misses. Same top-face rect 10×10 mm, Blind 10 mm along the face outward, so the prism sits outside the cube. Mode Cut. The cube remains, the volume stays 8000 mm³ within 0.5 mm³, an error is shown, and no second body appears.
- Portrait 390×844: the New Body, Join, and Cut chips are each at least 44 CSS px and do not cover the bottom bar.

## Tests
Extend the smoke that already exists. Do not add a new smoke file or a new harness.

- `tests/deploy_smoke.py` and `tests/phone_smoke.py`: add a check only where one already fits. Phone smoke already uses the 390×844 viewport.
- Face Join on the default cube (top face, rect 10×10 mm, Blind 10 mm): one body, volume 9000 mm³ within 0.5 mm³, OCCT validity, mm gate.
- Overlapping Cut (Top origin rect 10×10 mm, Finish Sketch, then one 20 mm box at centre (0, 0, 10), one Item selected, Blind 10 mm): one body, volume 7000 mm³ within 0.5 mm³, OCCT validity, mm gate. Do not start a new sketch between Finish Sketch and the Cut, or the profile is cleared.
- New Body regression: two bodies after the top-face extrude. The existing empty-doc New Body rect and circle checks still pass with the sheet opening on New Body.
- Origin plane with no body: Join and Cut cannot commit. After exactly one body is selected, they can.
- Miss Cut on the top-face outward prism: the prior cube is kept, an error is shown, and the volume stays 8000 mm³ within 0.5 mm³.
- Phone: the three op chips are at least 44 CSS px at 390×844, and they do not cover the bottom bar.

## Out of scope
- Intersect from sketch Extrude. Body-level Intersect stays on the Boolean toolbar.
- A constraint solver.
- Revolve, sweep, and loft.
- Changing the body-level Union / Cut / Intersect toolbar, or retuning `fuseShapes` / `cutShapes` / `commonShapes`.
- A kernel or WASM rebuild.
- A watertight gate.
- A new extrude direction control (flip, two-sided, or symmetric).
- Offset or angled construction planes.

## Done
`ci.yml` green on the PR (a docs-only diff may skip the native build; a code diff runs the build). Tip-match reviews. Repo Keeper undrafts and plain-merges. Report the PR link and the tip SHA.
