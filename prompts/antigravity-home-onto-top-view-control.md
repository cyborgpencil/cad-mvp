# Antigravity Home onto the top-view control

Home moves from the viewport mid-top onto the Camera-shelf **Top** control. Chief named that destination. On main `e27957f` the Home entry is still `#vcHome` beside the view cube. This file is the Antigravity feed. It does not change the app by itself.

**Gate:** This item’s **code** starts only after this file tip-matches on main **and** overnight item 1 Tool Search exit plus related tip-matches have landed. Overnight 1–2 briefs are on main ([#208](https://github.com/cyborgpencil/cad-mvp/pull/208) @ `c713ce4`). Item 3 brief is on main ([#210](https://github.com/cyborgpencil/cad-mvp/pull/210) @ `1b8a57f`; UPDATES [#211](https://github.com/cyborgpencil/cad-mvp/pull/211)). Item 4 code is on main ([#217](https://github.com/cyborgpencil/cad-mvp/pull/217) @ `0ce3ba1`; UPDATES [#218](https://github.com/cyborgpencil/cad-mvp/pull/218)). Pilot holds the coding `agy`. This prompts file does not start an `agy` by itself. Docs base for this retip is main @ `e27957f` (`e27957f7b39c44175734e6a8bff129eb0f5c9b8c`, tip after #218). Dig’s View scan tip remains `c713ce4` (`c713ce4479349fe11d56a53921edb7dafe866038`). #217/#218 do not change the Home or Camera-shelf Top/Iso attributes Dig quoted. Do not re-spec #208. Do not re-spec item 3. Do not re-spec item 4. Do not re-spec themes / Active chrome B.

**Hard lock:** Implementation is **Antigravity-only on Z13**. Pilot holds one `agy` until this file tip-matches on main and the item-1 hold above has lifted, then owns one `agy`. Do not use Grok Build or Cursor for the handoff into code. Prefer a worktree under `C:\Dev\`; do not invent a new path or create folders from this brief. Do not commit from Antigravity; Pilot/Repo Keeper commit path owns that. Do not invent Erik specs. Stay in `web/` (JS, HTML, CSS). No kernel, C++, `src/`, bindings, or wasm rebuild. No new control ids, hex, pixel sizes, gesture maps, themes, Active chrome B changes, or invented relocation homes. The destination node is named below. Do not substitute another node. Do not invent an element id for Top.

**Source of truth:**

- Erik overnight ~11:55 PM MT 2026-10-26, item **(5) Move Home from viewport mid-top onto top-view control**, via CAD Chief. Invent-free.
- `research/overnight-home-onto-top-view-control.md` (Dig, 2026-10-27 ~1:15 AM MT), scanned at tip `c713ce4`. Cite that digest. Anything it marks **TBD** stays **TBD**, except the destination node Chief later named.
- View cube / Home park (`mvp/requirements.md`, `prompts/antigravity-view-cube-gizmo-line-dims.md`): Home centers on the selected model when something is selected; otherwise **0,0,0**. Pixel thresholds, hold timing, and the Home key binding stay **TBD** in that park.
- Chief lock, 2026-10-27 ~1:17 AM MT via 3T · Chief (recorded on item 6): Home leaves the view cube and moves to the top-view control (this item). That lock does not name the destination node. Item 6 drops the cube’s Home double-tap. Do not implement the stretch toggle in this brief.
- Chief lock, 2026-10-27 ~3:55 AM MT, CAD CAM MVP room: Home destination = the Camera-shelf **Top** control. That is Dig candidate **#2** below. Not the cube (`#viewCube`). Not Camera-shelf Home/Iso (`data-view="home"`, title `Iso`). Not a new control.
- `prompts/antigravity-view-cube.md` locks adjacent swipe and, until item 6, a double-tap Home iso success cite. This brief does not rewrite swipe. It does not keep Home on the cube.

Dig’s invent-free list from the View scan at `c713ce4`. Candidates 1–4 have the same control attributes on main `e27957f`. Cite this list. Do not re-pick.

1. `#vcHome` mid-top · `data-view="home"` · title `Home view`
2. Camera-shelf Top · no element id · `data-view="top"` · `data-tool="View: Top"` · title `Top` ← **named destination**
3. Camera-shelf Home/Iso · no element id · `data-view="home"` · title `Iso`
4. `#viewCube` cube div only
5. View bar Measure / Section / Display — no Top or Home view buttons

Quoted from Dig’s scan of `web/index.html` at `c713ce4`, and still the control markup on main `e27957f`:

- Mid-top Home: `<button … class="vc-home" id="vcHome" data-action="view" data-view="home" data-tool="Home view" title="Home view">Home</button>` inside `#viewport`.
- `.vc-home` is `position: absolute; top: 8px; right: 148px;` with 44px minimum box. `layoutChrome()` places it mid-top beside the cube. Those numbers are tip facts. Do not retune them.
- Camera-shelf Home/Iso sits in `#cameraShelf` Views (`aria-label="Views"`): `data-view="home"`, `data-tool="Home view"`, title `Iso`, icon `#i-iso`. No element id. This button is not the destination.
- Camera-shelf Top sits in that same Views cluster: `<button type="button" data-action="view" data-view="top" data-tool="View: Top" title="Top">` with icon `#i-top`. No element id. Select it by `data-view="top"` under `#cameraShelf`. Do not add an id.
- `action === 'view'` calls `goView(...)`. `goView('home')` uses `VIEWS.home` (`theta: Math.PI/4`, `phi: 0.96`, same numbers as `VIEWS.iso`) and `homeTargetAndRadius()` (selection, else origin 0,0,0).
- `layoutDimSheet` / `layoutRects` / phone safe-pad treat `#vcHome` as a reserved mid-top rect.
- Candidate 5: at `c713ce4` the View bar is the viewport `.vp-bar[aria-label="View"]` (Measure, Section, Display). On main `e27957f` ([#217](https://github.com/cyborgpencil/cad-mvp/pull/217)) that bar sits in `.topbar-shelves` and still has Measure, Section, and Display only. Those buttons have no `data-view="top"` and no `data-view="home"`. Do not re-spec item 4. Do not place Home on that bar.

**Gap:** `#vcHome` is still the viewport mid-top Home entry on `e27957f`. The destination is no longer unnamed. Chief named Dig candidate #2: the existing Camera-shelf Top control (`#cameraShelf` Views, no element id, `data-view="top"`, `data-tool="View: Top"`, title `Top`). Home has not moved onto that control yet.

## Goal
Implement these sourced behaviors in `web/` (JS, HTML, and CSS). No kernel, C++, `src/`, bindings, or wasm rebuild. Watertight / units are N/A.

Erik: **move Home from viewport mid-top onto top-view control**.

Coding bar:

1. Viewport mid-top `#vcHome` stops being the Home entry once Home is on the Camera-shelf Top control. Move it off mid-top. Do not leave it in place as the Home button. Do not add a mid-top substitute.
2. Home is reachable from that existing Top control. It is under `#cameraShelf`, in the Views cluster. Select it by `data-view="top"`. Tip facts on that same button: `data-tool="View: Top"`, title `Top`, no element id. Do not add an id. Do not add a sibling Home button next to it.
3. Do not place Home on `#viewCube`, on the Camera-shelf Home/Iso button (`data-view="home"`, title `Iso`), on the View bar (Measure / Section / Display), or on a new control.
4. Keep Home aim already on tip and in the View cube park: selected model when something is selected; otherwise 0,0,0. That is the aim of today’s `goView('home')` / `homeTargetAndRadius()`. Do not invent a Home key.
5. Activating the named Top control is the Home entry after the move. Do not keep `#vcHome` as that entry.

Where a remaining line is **TBD**, leave it **TBD**. The destination node is not TBD.

## Workflow
1. Read `research/overnight-home-onto-top-view-control.md` and the facts above. Copy behavior from those sources and from the ~3:55 AM MT Chief lock only.
2. Find the destination under `#cameraShelf` with `data-view="top"`. Check the tip facts `data-tool="View: Top"` and title `Top`. Do not invent an element id. Do not choose the Iso button, `#viewCube`, or a new control.
3. Place the Home entry on that Top control. Do not add a Home button, id, or icon.
4. Stop using mid-top `#vcHome` as the Home entry. Do not assign `id="vcHome"` to the Top control.
5. Preserve `homeTargetAndRadius()` aim (selection, else 0,0,0). Leave the Home key binding TBD.
6. Leave cube double-tap to item 6. Leave adjacent swipe as already locked. Do not put Home on the cube.
7. Phone layout after `#vcHome` leaves mid-top (cube / dim-sheet overlap helpers) stays **TBD**. Do not invent a layout.

## Do not bake / TBD
Do not invent and do not bake any of the following. They stay **TBD**:

- Phone layout after `#vcHome` is no longer mid-top
- Whether the Camera-shelf Home/Iso button stays or merges (it is not the destination)
- Whether the Top control’s visible title, icon, `data-tool` string, or `data-view` attribute string changes
- Whether the previous Top view (`goView('top')`) stays reachable on some other existing control
- Whether the `#vcHome` node is removed from the DOM after it stops being the Home entry
- Home key binding (already TBD on the View cube park)
- Pixel thresholds and hold timing from that park
- Any new control id, including an id on the Top control
- Any new hex
- Any new pixel size
- Icon art
- Hotkeys
- Gesture maps
- Themes or Active chrome B
- A new home invented for Home

The destination node is not on this list. It is the Camera-shelf Top control named above.

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

Check sourced behavior only. Do not assert a new id, a pixel position, a retitle, an icon change, or phone layout.

1. Home aim is unchanged: selected model when something is selected; otherwise 0,0,0.
2. The Home entry is the Camera-shelf Top control named above (the `#cameraShelf` Views button that on this tip has no element id, `data-view="top"`, `data-tool="View: Top"`, and title `Top`). Mid-top `#vcHome` is not the Home entry. Do not assert that the title, icon, `data-tool`, or `data-view` string was rewritten or kept.
3. Home is not on `#viewCube`, not on the Camera-shelf Home/Iso button (`data-view="home"`, title `Iso`), and not on a new control.
4. No new Home control and no new element id were added.

## Success Criteria
Must PASS at tip-match. Cite Erik overnight item (5) ~11:55 PM MT 2026-10-26 via CAD Chief; `research/overnight-home-onto-top-view-control.md` (Dig scan tip `c713ce4`); Chief lock 2026-10-27 ~1:17 AM MT (Home leaves the cube; that lock did not name the node); Chief lock 2026-10-27 ~3:55 AM MT (destination = Camera-shelf Top, Dig candidate #2); main control attributes at `e27957f`. Only that bar is in scope.

1. The ask is placement: Home leaves viewport mid-top and is on the Camera-shelf Top control.
2. That control is Dig candidate #2, the existing `#cameraShelf` Views button identified on this tip by no element id, `data-view="top"`, `data-tool="View: Top"`, and title `Top`. A guessed id fails. The cube, the Camera-shelf Home/Iso button, the View bar, and a new control do not pass.
3. After the move, mid-top `#vcHome` is not the Home entry.
4. Home aim stays selected-model, else 0,0,0.
5. No invented control id, hex, pixel size, icon, hotkey, gesture, theme, or Active chrome B change.
6. This docs PR does not change `web/`.

Outside this hard bar: phone overlap layout; whether Camera-shelf Home/Iso stays or merges; whether the previous Top view stays reachable; whether the Top control’s title, icon, `data-tool`, or `data-view` string changes; whether the `#vcHome` node is removed; Home key binding; item 6’s stretch mechanism; items 1–4 and 7–10; `UPDATES.md`; kernel / C++ / wasm.

## Done
Draft until tip-match: Doc Steward primary (COMMENT), Research Digest second tip-match COMMENT. Author does not self-APPROVE. Repo Keeper undrafts and plain-merges. Pilot holds the coding `agy` for this item until overnight item 1 Tool Search exit and related tip-matches have landed **and** this brief tip-matches on main. This file does not start an `agy`. One Antigravity-only `agy` on Z13, `web/` only, after that hold lifts. Report the prompt PR link and tip SHA. Pilot reports any implementation PR separately.
