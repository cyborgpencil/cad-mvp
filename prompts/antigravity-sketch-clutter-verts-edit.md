# Antigravity sketch clutter, verts, edit

Sketch: less create clutter; brighter verts and edges on all components; edit and delete; flesh sketches and solids. Dig’s tip scan leaves each unspecified clause TBD. This file does not turn those clauses into a punch list. This file is the Antigravity feed. It does not change the app by itself.

**Gate:** This item’s **code** starts only after this file tip-matches on main **and** overnight item 1 Tool Search exit plus related tip-matches have landed. Overnight 1–2 briefs are on main ([#208](https://github.com/cyborgpencil/cad-mvp/pull/208) @ `c713ce4`). Item 3 brief is on main ([#210](https://github.com/cyborgpencil/cad-mvp/pull/210) @ `1b8a57f`; UPDATES [#211](https://github.com/cyborgpencil/cad-mvp/pull/211)). Pilot holds the coding `agy`. This prompts file does not start an `agy` by itself. Docs base is main @ `7214005` (`72140052f516b59d6560133fc4240f13e5d257c7`, tip after #211). Dig’s scan tip for `web/` remains `c713ce4` (`c713ce4479349fe11d56a53921edb7dafe866038`). #209/#210/#211 are docs/UPDATES only relative to that Dig scan for View/chrome facts. Do not re-spec #208. Do not re-spec item 3. Do not re-spec themes / Active chrome B.

**Hard lock:** Implementation is **Antigravity-only on Z13**. Pilot holds one `agy` until this file tip-matches on main and the item-1 hold above has lifted, then owns one `agy`. Do not use Grok Build or Cursor for the handoff into code. Prefer a worktree under `C:\Dev\`; do not invent a new path or create folders from this brief. Do not commit from Antigravity; Pilot/Repo Keeper commit path owns that. Do not invent Erik specs. Stay in `web/` (JS, HTML, CSS). No kernel, C++, `src/`, bindings, or wasm rebuild. No new control ids, hex, pixel sizes, gesture maps, themes, Active chrome B changes, or invented relocation homes. No invented punch list.

**Source of truth:**

- Erik overnight ~11:55 PM MT 2026-10-26, item **(7) Sketch: less create clutter; brighter verts/edges all components; edit+delete; flesh sketches+solids**, via CAD Chief. Invent-free. Do not expand beyond these clauses.
- `research/overnight-sketch-clutter-verts-edit.md` (Dig, 2026-10-27 ~1:15 AM MT), scanned at tip `c713ce4`. Cite that digest. Anything it marks **TBD** stays **TBD**.
- Sketch chrome park and `prompts/antigravity-sketch-chrome-flow.md`: while sketch is active, minimize non-sketch chrome; Create → six ortho planes → sketch-create tools; keep Finish Sketch. Do not re-spec that flow.
- Sketch draw overhaul park and `prompts/antigravity-sketch-draw-overhaul.md`: live length and angle; dims stay; #183 strip and Finish stay. The overhaul’s “very bottom (Modify / Create) stay on” line is not retargeted here (item 8 is the bottom-bar brief). Do not re-spec the overhaul.

Quoted from Dig’s scan of `web/index.html` at `c713ce4` (baseline only; not a new color spec):

- Sketch panel `data-panel="sketch"`: **Draw** (Line, Rectangle, Circle, Arc, Polygon); **Modify** (Sketch Fillet, Trim, Offset, Dimension); **Constrain** (Coincident, Horizontal, Vertical, Parallel, Perpendicular, Equal, Tangent, Fixed).
- While sketch-active, CSS hides the third group (Constrain). Draw and Modify stay.
- Other sketch-active hides include the View `vp-bar`, selection shelf, camera shelf, `#edgeSheet`, `#pickChooser`, `.hud`, and tools-sheet shelves.
- Finish Sketch is `#finishBar` / `data-action="finishSketch"`.
- Sketch line material uses `0xf0c14e`. Boot-cube corner points use `0xf2c14e` at size 8 and start `visible = false`. Body edge overlay uses `0x10283a`, with theme paths `0xd7e4f2` / `0x10283a`. Do not treat these literals as a brightness target. Do not invent a replacement hex.
- `#modifyShelf` has `data-action="delete"` Delete. That is the body/modify shelf, not a sketch editor labeled Edit.
- Inspector copy already says vertex maps, the tool pipe, and statistics are not in this build.
- No sketch-panel control is named Edit.

**Gaps (do not invent fixes):**

1. Less create clutter — Constrain is already hidden while sketch-active. What else is clutter is TBD.
2. Brighter verts/edges for all components — no tip pass does that. Brightness and hex are TBD. Modo orange selection hex stays TBD and out of scope.
3. Edit+delete — sketch-entity edit/delete is not specified beyond Finish / Trim / Offset / Fillet and the modify-shelf Delete.
4. Flesh sketches+solids — “flesh” has no tip spec. Content is TBD.

## Goal
Record Erik’s four clauses in `web/` only where a clause is already specified. No kernel, C++, `src/`, bindings, or wasm rebuild. Watertight / units are N/A. Do not touch export to invent “flesh”.

Erik’s clauses, and only these:

1. Less sketch **create clutter**. Do not invent which Draw tools leave.
2. **Brighter** verts and edges for **all components**. Tip colors are the baseline quote. Do not invent a hex.
3. **Edit+delete** in the sketch context. Do not invent a control id. Do not decide that `#modifyShelf` Delete is or is not the control.
4. **Flesh sketches+solids**. Implementation content is TBD. Do not invent it.

A stand-in tool list, hex, Edit button, delete rule, or flesh feature fails.

## Workflow
1. Read `research/overnight-sketch-clutter-verts-edit.md`. Copy the four clauses and the gaps. Do not add a fifth ask.
2. Leave every Dig TBD as TBD. Do not choose tools to hide, a brightness number, an edit gesture, a delete target, or a flesh feature.
3. Keep Finish Sketch. Do not re-spec the #183 strip, the six-plane Create flow, or the draw overhaul.
4. Do not retune theme colors or Active chrome B while quoting the tip materials.
5. If a clause is still unspecified at coding time, record the gap. Do not ship a partial punch list for that clause.

## Do not bake / TBD
Do not invent and do not bake any of the following. They stay **TBD**:

- Which create tools stay, hide, or move
- Brightness metric, hex, or shader path
- Per-component versus sketch-only brightness
- What “edit” means (re-enter sketch, drag verts, properties, or anything else)
- What “delete” means (sketch entities, whole sketch, or bodies)
- Whether edit+delete reuses `#modifyShelf` Delete
- What “flesh” adds to sketches and solids
- Collision with the Constrain-hide CSS and with #183 / the overhaul locks
- Modo orange selection hex
- Any new control id
- Any new pixel size
- Icon art
- Hotkeys
- Gesture maps
- Themes or Active chrome B
- A punch list assembled from the gaps

## Out of scope
- Constraint solver / PlaneGCS.
- Items 1–6, 8, and 9. Item 8 owns the bottom bar. Item 10 is a rebuild note with no coding brief.
- Sketch chrome flow and the sketch draw overhaul, except to avoid re-specifying them.
- Rust #4 / triple-tap.
- Editing `research/overnight-sketch-clutter-verts-edit.md`, `mvp/requirements.md`, or `UPDATES.md` from the coding `agy`.
- Editing `web/` from this docs PR.
- Kernel / C++ / wasm rebuild. Do not commit `.wasm`, `web/cadcam.wasm`, or `web/dist/`. Do not edit a root `PROGRESS.md`.

## Smoke
Manual wake smoke on Pages. No new smoke harness. Reuse `tests/deploy_smoke.py` only if that reuse is clearly required; this brief does not require it. No invented pixel asserts. No invented color asserts. Because no smoke path is added here, do not print a done marker.

Check sourced behavior only. Do not assert a hidden Draw tool, a new hex, an Edit control, a delete target, or a flesh feature.

1. Finish Sketch is still present.
2. No punch-list change shipped for a clause Dig left unspecified.
3. Tip material colors were not replaced with an invented hex.

## Success Criteria
Must PASS at tip-match. Cite Erik overnight item (7) ~11:55 PM MT 2026-10-26 via CAD Chief; `research/overnight-sketch-clutter-verts-edit.md`; tip `c713ce4`. Only Erik’s four clauses are in scope, and only where they are specified. They are not specified past the words below.

1. The scope is less create clutter, brighter verts/edges on all components, edit+delete, and flesh sketches+solids. No fifth ask.
2. Each unspecified gap stays TBD. No invented punch list.
3. No invented control id, hex, pixel size, icon, hotkey, gesture, theme, or Active chrome B change.
4. This docs PR does not change `web/`.

Outside this hard bar: which create tools move; brightness metric and hex; edit meaning; delete meaning; flesh content; Constrain-hide collisions; Modo orange hex; items 1–6 and 8–10; the sketch overhaul’s bottom-bar line; `UPDATES.md`; kernel / C++ / wasm.

## Done
Draft until tip-match: Doc Steward primary (COMMENT), Research Digest second. Author does not self-APPROVE. Repo Keeper undrafts and plain-merges. Pilot holds the coding `agy` for this item until overnight item 1 Tool Search exit and related tip-matches have landed **and** this brief tip-matches on main. This file does not start an `agy`. One Antigravity-only `agy` on Z13, `web/` only, after that hold lifts. Report the prompt PR link and tip SHA. Pilot reports any implementation PR separately.
