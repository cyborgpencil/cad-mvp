# Antigravity Home onto the top-view control

Home moves from the viewport mid-top onto the top-view control. On tip `c713ce4` Home is still `#vcHome` beside the view cube. Which node “top-view control” names is not stated. This file is the Antigravity feed. It does not change the app by itself.

**Gate:** This item’s **code** starts only after this file tip-matches on main **and** overnight item 1 Tool Search exit plus related tip-matches have landed. Overnight 1–2 briefs are on main ([#208](https://github.com/cyborgpencil/cad-mvp/pull/208) @ `c713ce4`). Item 3 brief is on main ([#210](https://github.com/cyborgpencil/cad-mvp/pull/210) @ `1b8a57f`; UPDATES [#211](https://github.com/cyborgpencil/cad-mvp/pull/211)). Pilot holds the coding `agy`. This prompts file does not start an `agy` by itself. Docs base is main @ `7214005` (`72140052f516b59d6560133fc4240f13e5d257c7`, tip after #211). Dig’s scan tip for `web/` remains `c713ce4` (`c713ce4479349fe11d56a53921edb7dafe866038`). #209/#210/#211 are docs/UPDATES only relative to that Dig scan for View/chrome facts. Do not re-spec #208. Do not re-spec item 3. Do not re-spec themes / Active chrome B.

**Hard lock:** Implementation is **Antigravity-only on Z13**. Pilot holds one `agy` until this file tip-matches on main and the item-1 hold above has lifted, then owns one `agy`. Do not use Grok Build or Cursor for the handoff into code. Prefer a worktree under `C:\Dev\`; do not invent a new path or create folders from this brief. Do not commit from Antigravity; Pilot/Repo Keeper commit path owns that. Do not invent Erik specs. Stay in `web/` (JS, HTML, CSS). No kernel, C++, `src/`, bindings, or wasm rebuild. No new control ids, hex, pixel sizes, gesture maps, themes, Active chrome B changes, or invented relocation homes. Do not invent which tip node is the top-view control.

**Source of truth:**

- Erik overnight ~11:55 PM MT 2026-10-26, item **(5) Move Home from viewport mid-top onto top-view control**, via CAD Chief. Invent-free.
- `research/overnight-home-onto-top-view-control.md` (Dig, 2026-10-27 ~1:15 AM MT), scanned at tip `c713ce4`. Cite that digest. Anything it marks **TBD** stays **TBD**.
- View cube / Home park (`mvp/requirements.md`, `prompts/antigravity-view-cube-gizmo-line-dims.md`): Home centers on the selected model when something is selected; otherwise **0,0,0**. Pixel thresholds, hold timing, and the Home key binding stay **TBD** in that park.
- Chief lock, 2026-10-27 ~1:17 AM MT via 3T · Chief (recorded on item 6): Home leaves the view cube and moves to the top-view control (this item). That lock does not name the destination node. Item 6 drops the cube’s Home double-tap. Do not implement the stretch toggle in this brief.
- `prompts/antigravity-view-cube.md` locks adjacent swipe and, until item 6, a double-tap Home iso success cite. This brief does not rewrite swipe. It does not keep Home on the cube.

Quoted from Dig’s scan of `web/index.html` at `c713ce4`:

- Mid-top Home: `<button … class="vc-home" id="vcHome" data-action="view" data-view="home" data-tool="Home view" title="Home view">Home</button>` inside `#viewport`.
- `.vc-home` is `position: absolute; top: 8px; right: 148px;` with 44px minimum box. `layoutChrome()` places it mid-top beside the cube. Those numbers are tip facts. Do not retune them.
- A second Home control sits in `#cameraShelf` Views: `data-view="home"`, `data-tool="Home view"`, title `Iso`, icon `#i-iso`.
- A separate Top control sits in that same cluster: `data-view="top"`, `data-tool="View: Top"`, title `Top`.
- `action === 'view'` calls `goView(...)`. `goView('home')` uses `VIEWS.home` (`theta: Math.PI/4`, `phi: 0.96`, same numbers as `VIEWS.iso`) and `homeTargetAndRadius()` (selection, else origin 0,0,0).
- `layoutDimSheet` / `layoutRects` / phone safe-pad treat `#vcHome` as a reserved mid-top rect.

**Gap (do not invent the destination):** `#vcHome` is still the viewport mid-top Home. Erik’s destination is the words “top-view control”. The Camera-shelf Home/Iso button and the Top button are both on tip. Neither is named as the destination.

## Goal
Implement these sourced behaviors in `web/` (JS, HTML, and CSS). No kernel, C++, `src/`, bindings, or wasm rebuild. Watertight / units are N/A.

Erik: **move Home from viewport mid-top onto top-view control**.

Coding bar:

1. Viewport mid-top `#vcHome` stops being the Home entry once Home is on the top-view control.
2. Home is reachable from the **top-view control**. That phrase is Erik’s. Do not map it onto the Camera-shelf Home/Iso button, the Top button, `.topbar-shelves`, or a new control.
3. Keep Home aim already on tip and in the View cube park: selected model when something is selected; otherwise 0,0,0. Do not invent a Home key.
4. Do not remove `#vcHome` by guessing a destination. A guessed node fails. Until Erik or Chief names the node, leave `#vcHome` where the tip left it and record the gap.

Where the destination is **TBD**, leave it **TBD**.

## Workflow
1. Read `research/overnight-home-onto-top-view-control.md` and the facts above. Copy behavior from those sources only.
2. Treat “top-view control” as unnamed. Do not choose among tip Home, Iso, and Top controls.
3. Do not add a Home button, id, or icon.
4. Preserve `homeTargetAndRadius()` aim (selection, else 0,0,0). Leave the Home key binding TBD.
5. Leave cube double-tap to item 6. Leave adjacent swipe as already locked.
6. Phone layout after `#vcHome` leaves (cube / dim-sheet overlap helpers) stays **TBD**. Do not invent a layout.

## Do not bake / TBD
Do not invent and do not bake any of the following. They stay **TBD**:

- Which tip node is the top-view control
- Whether the Camera-shelf Home stays, merges, or is the destination
- Phone layout after `#vcHome` is no longer mid-top
- Home key binding (already TBD on the View cube park)
- Pixel thresholds and hold timing from that park
- Any new control id
- Any new hex
- Any new pixel size
- Icon art
- Hotkeys
- Gesture maps
- Themes or Active chrome B
- A new home invented for Home

## Out of scope
- Item 6 stretch toggle and dropping `goView('home')` on cube double-tap. Separate brief: `prompts/antigravity-view-cube-double-tap-iso.md`.
- Item 4 View popup move. Items 7–9. Item 10 rebuild note (no coding brief).
- Overnight 1–2 (#208) and item 3. Do not re-spec them.
- Adjacent-face swipe (`prompts/antigravity-view-cube.md`).
- Editing `research/overnight-home-onto-top-view-control.md`, `mvp/requirements.md`, or `UPDATES.md` from the coding `agy`.
- Editing `web/` from this docs PR.
- Kernel / C++ / wasm rebuild. Do not commit `.wasm`, `web/cadcam.wasm`, or `web/dist/`. Do not edit a root `PROGRESS.md`.

## Smoke
Manual wake smoke on Pages. No new smoke harness. Reuse `tests/deploy_smoke.py` only if that reuse is clearly required; this brief does not require it. No invented pixel asserts. Because no smoke path is added here, do not print a done marker.

Check sourced behavior only. Do not assert which button is the top-view control. Do not assert a new id or a pixel position.

1. Home aim is unchanged: selected model when something is selected; otherwise 0,0,0.
2. `#vcHome` is still the mid-top control if the destination node is still unnamed. Moving it onto a guessed control fails.
3. No new Home control was added.

## Success Criteria
Must PASS at tip-match. Cite Erik overnight item (5) ~11:55 PM MT 2026-10-26 via CAD Chief; `research/overnight-home-onto-top-view-control.md`; Chief lock 2026-10-27 ~1:17 AM MT (Home leaves the cube; destination node still unnamed); tip `c713ce4`. Only that bar is in scope.

1. The ask is placement: Home leaves viewport mid-top and is on the top-view control.
2. The destination node stays **TBD**. A guessed Camera-shelf, Top, or new control does not pass.
3. Home aim stays selected-model, else 0,0,0.
4. No invented control id, hex, pixel size, icon, hotkey, gesture, theme, or Active chrome B change.
5. This docs PR does not change `web/`.

Outside this hard bar: the destination node; whether Camera-shelf Home stays or merges; phone overlap layout; Home key binding; item 6’s stretch mechanism; items 1–4 and 7–10; `UPDATES.md`; kernel / C++ / wasm.

## Done
Draft until tip-match: Doc Steward primary (COMMENT), Research Digest second. Author does not self-APPROVE. Repo Keeper undrafts and plain-merges. Pilot holds the coding `agy` for this item until overnight item 1 Tool Search exit and related tip-matches have landed **and** this brief tip-matches on main. This file does not start an `agy`. One Antigravity-only `agy` on Z13, `web/` only, after that hold lifts. Report the prompt PR link and tip SHA. Pilot reports any implementation PR separately.
