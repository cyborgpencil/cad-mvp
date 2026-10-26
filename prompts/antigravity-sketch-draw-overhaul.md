# Antigravity sketch draw interaction overhaul

Overhaul sketching interaction on top of Create→ortho→sketch tools. This file is the Antigravity feed. It does not change the app by itself.

**Gate:** After the sketch-chrome implementation tip-merges on main. The chrome brief is `prompts/antigravity-sketch-chrome-flow.md` (#183 park is already on main: Create→six ortho→sketch tools + Finish Sketch). Pilot holds this overhaul `agy` until this file is tip-matched on main **and** that chrome implementation has tip-merged. X-ray (#163 park) and panel chrome (#167 park) stay queued after this overhaul.

**Hard lock:** Implementation is **Antigravity-only on Z13**. Pilot holds coding until this file is tip-matched on main and the chrome implementation has tip-merged, then owns one `agy`. If `agy` exits with a dirty tree and no commit, Pilot commits and drafts the implementation PR — no second `agy`. Do not use Grok Build or Cursor for the handoff into code. Suggested Pilot worktree: create or reuse a dedicated worktree under `C:\Dev\` only if Pilot already has one; do not invent a path or create folders from this brief. Prefer `C:\Dev\cadcam-mvp` if Pilot says otherwise. Do not commit from Antigravity; the Pilot commit path owns that commit. Do not invent Erik specs. No kernel, C++, `src/`, bindings, or wasm rebuild.

**Source of truth:** The parked bullet in `mvp/requirements.md` under **Queued after current in-flight (discuss / parked)** named exactly **Sketch draw interaction overhaul**. Parked in the same change as this brief. Erik via 3T, 2026-10-26 ~5:18 PM MT. Chief lock (invent-free) is in that bullet. Cite that bullet for the new behavior. Overnight locks **(c)** and **(d)**, the Q5 discuss locks, and the export acceptance checks stay as written in that file. Anything the park does not state stays **TBD**.

## Goal
Implement these sourced behaviors in `web/` (JS, HTML, CSS as needed). No kernel, C++, `src/`, bindings, or wasm rebuild. Pattern notes from Digest (Fusion / FreeCAD / Onshape) are flags only. This slice implements Erik’s bullets.

Copied from the park in this change:

- **Start-point callout (Erik).** When the user taps or places the start of a draw, make the start point obvious with a callout. The callout is **intentional** (Erik; Chief). **TBD:** callout visual only (badge / ring / label / etc.).
- **Floating end adjust (Erik).** After the start tap, open a floating window/panel so the user can set or adjust the end with typed values. The panel **opens on the start tap** (Erik: after that tap; Chief). **TBD:** whole polyline vs per segment. **TBD:** typed-vs-driving, and preview HUD vs committed dims on Enter/confirm.
- **Polygon snap, on that panel (Erik).** For polygons and specials: snap to tapped vertices and edges, with the snap on/off control **on that floating panel**. **Snap targets v1 (Chief):** vertices and edges of the **current draw chain only**. **TBD:** prior sketch geometry and projected model edges. **TBD:** snap default on or off. **TBD:** tool identity, tool list, and polygon close.
- **Live length and angle (Erik).** While drawing, show live length and angle measured **from the previous segment / last vertex**. FreeCAD sketch-X is not the datum. **TBD:** a switchable datum later.
- **Dims stay while drawing (Erik).** Keep angles and dimensions on the sketch as drawn. They are not only a temporary preview that vanishes. Confirm model stays **TBD**.
- **Top and bottom stay on (Erik).** While sketching, the very top (tree + filename) and the very bottom (Modify / Create) stay visible.
- **#183 stays under this overhaul (Chief).** Create→ortho→sketch tool strip and **Finish Sketch** stay. Do not rework that strip or Finish Sketch.

## Workflow
1. Read the park bullet named above. Copy behavior from that bullet only.
2. Leave the #183 Create→ortho→sketch tool strip and **Finish Sketch** in place. Build this overhaul on that flow.
3. When the user taps or places the start of a draw, make that start point obvious with a callout. Leave the callout visual TBD.
4. On that start tap, open a floating window/panel so the user can set or adjust the end with typed values.
5. For polygons and specials, snap to tapped vertices and edges of the current draw chain. Put snap on/off on that floating panel.
6. While drawing, show live length and angle measured from the previous segment / last vertex.
7. Keep angles and dimensions on the sketch as drawn.
8. While sketching, keep the very top (tree + filename) and the very bottom (Modify / Create) visible.
9. Where the park marks a detail **TBD**, leave it TBD. Do not fill the gap with a guessed value.

## Do not bake / TBD
Do not invent and do not bake any of the following. They stay **TBD**, or they are closed locks, as written in the park:

- callout visual (badge / ring / label / etc.) — the callout itself is intentional
- whole polyline vs per segment for the floating panel — the panel opens on the start tap
- typed-vs-driving, and preview HUD vs committed driving dims on Enter/confirm — Erik said dims stay; the confirm model is still TBD
- snap targets beyond the current draw chain (prior sketch geometry, projected model edges) — v1 is the current draw chain only
- snap default on or off — the on/off control is on the floating panel
- polygon/specials tool identity (separate regular-polygon tool vs tap-vertex polyline), the tool list, and polygon close
- a switchable angle datum — the datum is the previous segment / last vertex; FreeCAD sketch-X is not our datum
- a second, global snap toggle — the snap on/off control is on the floating panel
- control ids
- pixel sizes
- hex colors
- icon art
- phone vs desktop layout
- touch vs pointer layout

## Out of scope
- Reworking the #183 sketch tool strip or **Finish Sketch**. That Create→ortho→strip stays under this overhaul.
- Hiding the very top (tree + filename) or the very bottom (Modify / Create) during sketch.
- The sketch-chrome slice (`prompts/antigravity-sketch-chrome-flow.md`). It stays a separate slice. Do not amend that brief, its strip, or its Finish Sketch from this file.
- Tools-menu-bar visibility during sketch. This overhaul does not decide it.
- Arc-specific behavior. The chrome park’s Arc-dialog TBD is superseded by this overhaul. Do not invent an Arc redesign.
- X-ray select-through (#163 park) and panel chrome (#167 park: panel labels and always-visible chrome). Those stay queued after this slice.
- Truck TBD parts / printer send.
- Rust #4. `.cadmvp` freeze stays TBD.
- Overnight locks **(c)** and **(d)**, the Q5 discuss locks, and the export acceptance checks. Do not rewrite them.
- Inventing dimensions, hex colors, control ids, CSS selectors, pixel sizes, or icon art.
- Kernel / C++ / wasm rebuild. Do not commit `.wasm`, `web/cadcam.wasm`, or `web/dist/`. Do not edit `UPDATES.md`, `research/`, or a root `PROGRESS.md`.

## Smoke
Manual wake smoke on Pages. No new smoke harness. Reuse `tests/deploy_smoke.py` only if clearly required; this brief does not require it. No invented pixel asserts. Because no smoke path is added here, do not print a done marker. Check Erik-stated behavior only.

1. Tapping or placing the start of a draw makes that start point obvious with a callout.
2. That start tap opens a floating window/panel for typed end adjust.
3. For polygons and specials, snap hits vertices and edges of the current draw chain, and the snap on/off control is on that floating panel.
4. While drawing, live length and angle are shown from the previous segment / last vertex.
5. Angles and dimensions stay on the sketch as drawn.
6. While sketching, the very top (tree + filename) and the very bottom (Modify / Create) stay visible.
7. Create→ortho→sketch tools and **Finish Sketch** from the chrome slice are still there.

## Success Criteria
Must PASS at tip-match. Cite the park bullet in `mvp/requirements.md` (Erik via 3T, 2026-10-26 ~5:18 PM MT; Chief invent-free locks in that bullet). Only Erik-stated behavior, plus the Chief locks folded into that bullet, is on this bar.

1. When the user taps or places the start of a draw, the start point is obvious with a callout. The callout is intentional.
2. After that start tap, a floating window/panel is open so the user can set or adjust the end with typed values. It opens on the start tap.
3. For polygons and specials, snap applies to tapped vertices and edges of the current draw chain, and snap on/off is on that floating panel.
4. While drawing, live length and angle are shown, measured from the previous segment / last vertex.
5. Angles and dimensions stay on the sketch as drawn.
6. While sketching, the very top (tree + filename) and the very bottom (Modify / Create) stay visible.
7. Create→ortho→sketch tool strip and **Finish Sketch** from #183 stay. This overhaul does not rework them.

Outside this hard bar: callout visual, whole polyline vs per segment, typed-vs-driving and preview HUD vs committed dims, snap default, prior-sketch and model-edge snap, tool list, polygon close, switchable angle axes, a second global snap toggle, control ids, pixel sizes, hex/colors, icon art, phone vs desktop layout, touch vs pointer layout, tools-menu-bar visibility, Arc-specific redesign, the X-ray and panel-chrome parks, Rust #4, `UPDATES.md`, and `research/`.

## Done
Draft until tip-match: Doc Steward primary (COMMENT), Research Digest second. Author does not self-APPROVE. Repo Keeper undrafts and plain-merges. After this file is on main **and** the sketch-chrome implementation has tip-merged, Pilot runs one Antigravity-only `agy` from it. Pilot holds that overhaul `agy` until both are true. If that `agy` exits with a dirty tree and no commit, Pilot commits and drafts the implementation PR — no second `agy`. Report the prompt PR link and tip SHA. Pilot reports any implementation PR separately.
