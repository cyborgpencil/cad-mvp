# Extrude Join and Cut

Team-chosen by Doc Steward, 2026-10-24 (America/Denver), from Digest #79 T1–T5. 3T Chief refined T1 the same day. Locks are final. Research on main: `research/gui/extrude-join-cut.md` (#79 @ `23aee4c`). Boolean Fuse/Cut, NonDestructive, SimplifyResult, and keep-last-valid: `research/occt-wasm/booleans.md`. P5c Blind New Body is on main via #70 (`7c83b2a`). Origin-plane empty-doc is on main via #77 (`347888e`). Also read `prompts/p5c-sketch-extrude.md` and `prompts/origin-plane-empty-doc.md`. Feed this to Grok Build / Cursor. This file is the spec. It does not change the app.

## Context
- WASM UI in `web/` (mostly `web/index.html`, plus `web/occt-ops.mjs`). Work in the Z13 repo (`C:\Dev\cadcam-mvp`).
- Units stay millimetres.
- After modeling ops, keep the OCCT shape-validity check and the millimetre units check. Watertight was dropped (02:17 rule).
- P5c already runs from Create → Sketch. A face tap stores `state.sketchPlane` as `{ faceId, bodyId, frame }`. Rectangle (corner, L×W mm) and center circle (Ø mm) build a closed profile. Finish Sketch returns to Model and keeps that profile. Blind / Distance opens at **10 mm** (`SKETCH_BLIND_DEPTH_MM`). Today `commitSketchExtrude` always pushes a new body. This slice adds the mode switch inside that same function.
- Origin-plane empty-doc shows the picker only when `state.bodies.length === 0`. Picking Top, Front, or Right stores `{ faceId: '', bodyId: '', originPlane, frame }` at the world origin. When any body exists, Create → Sketch still uses the face tap. Top / XY outward is +Z.
- The default session seeds one 20 mm cube, centre (0, 0, 10), from z = 0 to z = 20. Volume is 8000 mm³.
- Interactive body Booleans already exist. Union, Cut, and Intersect call `fuseShapes`, `cutShapes`, and `commonShapes` in `web/occt-ops.mjs`. A failed or empty Boolean keeps the inputs. This slice reuses `fuseShapes` and `cutShapes`. It does not call `commonShapes`.
- Do not commit `.wasm`, `web/cadcam.wasm`, or `web/dist/`. Do not edit `UPDATES.md`. Do not add or edit a root `PROGRESS.md`. Leave `web/PROGRESS.md` for a separate scrub.
- Prefer JS, CSS, and HTML, plus the existing libcascade 3.1.0 JS bindings in `web/occt-ops.mjs`. No kernel, C++, `src/`, `web/bindings.cpp`, or `cadcam.wasm` rebuild. If a needed binding is missing, stop and report it. Do not add a second Boolean path.
- Commit on a PR branch. Never push to main. Repo Keeper merges after `ci.yml` is green.

## Team-chosen behaviour
Extrude keeps Blind 10 mm and `makePrismSolid`. The sheet then offers New, Join, and Cut. Join and Cut Boolean the prism into one target through the same `commitSketchExtrude`. Do not always open the sheet on New.

### T1 — Target body
Resolve the Join/Cut target in this order. Do not invent a body picker.

1. If exactly one body is Item-selected (Item, hotkey 4), that body is the target.
2. Else if the sketch is a face path (`faceId` set), the target is the face-owning body (`bodyId` when set, otherwise the body that owns `faceId`).
3. Else the target is the newest body, the last entry in `state.bodies`.

Origin-plane path (no face): Join and Cut require exactly one Item-selected body. If none is selected, or more than one is selected, reject the commit with a clear toast. Do not fall through to the newest body. Do not invent a picker. New still commits with no Item selection.

### T2 — Default mode after Finish Sketch
The Extrude sheet does not always open on New. After Finish Sketch, set the chip from the profile:

- If `state.bodies.length === 0`, open Extrude on **New** (New Body).
- Else if the sketch profile is on a body face (`faceId` set / face path), open Extrude on **Join**.
- Else open Extrude on **New**.

The user can override that default with the New, Join, and Cut chips before Confirm. A face sketch on the default 20 mm cube therefore opens on Join. An empty document opens on New. An origin-plane profile opens on New, because that plane has no `faceId`, even when a body already exists.

### T3 — Cut that empties the whole body
If Cut would remove the entire target body, or leave an empty solid, reject the commit. Keep the prior body. Show a clear toast, for example "Cut removed the whole body". Do not leave an empty body entry in `state.bodies`. Do not install the empty result. Release the rejected prism with the existing `delete()` path.

A Cut that fails in the wrapper (`ok` false), fails OCCT validity, or fails the millimetre units check also keeps the prior bodies and shows an error. T3 is the extra rule for a cut that would delete the whole target even when the Boolean itself returns a shape.

### T4 — Chips
The Extrude sheet has three chips: **New**, **Join**, and **Cut**. Each chip is at least 44 CSS px. Use the same pattern as the origin-plane Top / Front / Right chips. The chips do not cover the bottom bar. The portrait check is 390×844. New means a new body. There is no Intersect chip on this sheet.

### T5 — One commit path
Face sketches and origin-plane sketches both Join and Cut through one `commitSketchExtrude` mode switch. Empty-doc stays on New until a body exists (`bodies.length === 0` follows T2). Join or Cut on that empty document has no target, so the commit is rejected and the document stays empty.

### Blind depth and kernel
Blind / Distance still opens at **10 mm** (`SKETCH_BLIND_DEPTH_MM`). A typed depth in mm overrides that default for New, Join, and Cut. The prism vector is `frame.outward` times that depth, the same vector `commitSketchExtrude` uses today.

- **New:** `makePrismSolid` / `BRepPrimAPI_MakePrism`, then push a body, as P5c does today.
- **Join:** prism, then `fuseShapes(target, prism)` into the target.
- **Cut:** prism, then `cutShapes(target, prism)` into the target (target minus tool).

Call those libcascade helpers in `web/occt-ops.mjs`. Leave the shared Boolean helper as it is. It already uses NonDestructive so a failed op can leave the inputs alone, checks IsDone before Shape, and runs SimplifyResult on fuse. After a successful Join or Cut, run the same OCCT validity check and millimetre units check the New extrude already runs. Watertight stays off.

When Join or Cut succeeds, the result replaces the target. The body count does not increase, and the prism is not a second body. New still adds a body.

The origin picker still appears only when `state.bodies.length === 0`. Finish Sketch keeps an origin-plane profile. Adding a body afterwards leaves that profile in place so the user can Item-select that body and Confirm Join or Cut. Start Sketch still clears the profile. A successful extrude still clears it.

## Acceptance
- T2, face path. Default 20 mm cube (`bodies.length === 1`), top-face sketch (`faceId` set), corner rect 10×10 mm, Finish Sketch, open Extrude. The sheet opens on **Join** without a chip tap. Blind 10 mm Confirm leaves one body. The boss lies outside the cube, so the volume is 9000 mm³ (8000 plus 10×10×10), within 0.5 mm³. OCCT validity passes and the mm gate passes. The prism is not a second body.
- T2, override. The same face profile, chip override to **New**, Blind 10 mm, ends with two bodies. The sheet must not have opened on New by itself.
- T2, empty doc. `bodies.length === 0`, origin plane, open Extrude: the sheet opens on **New**. Rect 10×10 mm and circle Ø10 mm, Blind 10 mm, New, each add a body as #77 does.
- T2, origin plane with a body. The profile has no `faceId`, so Extrude opens on **New** even though a body exists. The user can tap Join or Cut.
- T1, origin plane. Join or Cut with no Item selection, or with more than one body selected, rejects with a clear toast. Prior bodies stay. No body picker appears. New still commits with no Item selection. With exactly one Item-selected body, Join or Cut uses that body.
- Overlapping Cut. Empty doc, Top / XY, corner rect 10×10 mm, Finish Sketch, add one 20 mm box at centre (0, 0, 10), Item-select that body, Extrude opens on New, override to Cut, Blind 10 mm. The prism occupies x 0..10, y 0..10, z 0..10 inside the box. One body remains. Volume is 7000 mm³, within 0.5 mm³. OCCT validity passes and the mm gate passes.
- T3. A Cut whose prism contains the whole target rejects the commit. Concrete case: Top / XY circle Ø40 mm, Finish Sketch, add the 20 mm box at centre (0, 0, 10), Item-select it, Cut, typed Blind **30 mm**. That cylinder contains the cube. The commit does not land. The prior box remains, volume stays 8000 mm³ within 0.5 mm³, the toast is clear (wording such as "Cut removed the whole body"), and `state.bodies` has no empty entry.
- T4. Portrait 390×844: the New, Join, and Cut chips are each at least 44 CSS px and do not cover the bottom bar.

## Tests
Extend the smoke that already exists. Do not add a new smoke file or a new harness.

- `tests/deploy_smoke.py` and `tests/phone_smoke.py`: add a check only where one already fits. Phone smoke already uses the 390×844 viewport.
- T2: empty doc opens Extrude on New (existing origin-plane New rect and circle still pass). A face profile on the default cube opens Extrude on Join. An origin-plane profile with a body present opens on New. A chip tap overrides the default.
- Face Join (top face, rect 10×10 mm, Blind 10 mm, default Join): one body, volume 9000 mm³ within 0.5 mm³, OCCT validity, mm gate.
- New override on that same face profile: two bodies.
- Origin-plane Join/Cut: reject toast when Item selection is not exactly one body; commit when it is. Do not start a new sketch between Finish Sketch and the Cut, or the profile is cleared.
- Overlapping Cut (Top rect 10×10 mm, one 20 mm box, one Item selected, Blind 10 mm): one body, volume 7000 mm³ within 0.5 mm³, OCCT validity, mm gate.
- T3: containing Cut (Top circle Ø40 mm, Blind 30 mm, one Item-selected 20 mm box) does not commit. Prior body kept, volume 8000 mm³ within 0.5 mm³, clear toast, no empty `state.bodies` entry.
- Phone: the three chips are at least 44 CSS px at 390×844, and they do not cover the bottom bar.

## Out of scope
- Intersect on the sketch Extrude sheet. Body-level Intersect stays on the Modify Boolean toolbar.
- A body picker.
- Redesigning Modify Union / Cut / Intersect, or retuning `fuseShapes` / `cutShapes` / `commonShapes`.
- A constraint solver.
- Revolve, sweep, and loft.
- A kernel or WASM rebuild.
- A watertight gate.
- A new extrude direction control (flip, two-sided, or symmetric).
- Offset or angled construction planes.

## Done
`ci.yml` green on the PR (a docs-only diff may skip the native build; a code diff runs the build). Tip-match reviews. This PR stays draft until Digest tip-matches. Repo Keeper undrafts and plain-merges. Report the PR link and the tip SHA.
