# Antigravity View popup → top lower tools bar

The View popup moves into the top lower tools bar and gets its own show/hide icon. On tip `c713ce4` that View UI is the viewport `.vp-bar`, and it has no show/hide icon. This file is the Antigravity feed. It does not change the app by itself.

**Gate:** This item’s **code** starts only after this file tip-matches on main **and** overnight item 1 Tool Search exit plus related tip-matches have landed. Overnight 1–2 briefs are on main ([#208](https://github.com/cyborgpencil/cad-mvp/pull/208) @ `c713ce4`). Item 3 brief is on main ([#210](https://github.com/cyborgpencil/cad-mvp/pull/210) @ `1b8a57f`; UPDATES [#211](https://github.com/cyborgpencil/cad-mvp/pull/211)). Pilot holds the coding `agy`. This prompts file does not start an `agy` by itself. Docs base is main @ `7214005` (`72140052f516b59d6560133fc4240f13e5d257c7`, tip after #211). Dig’s scan tip for `web/` remains `c713ce4` (`c713ce4479349fe11d56a53921edb7dafe866038`). #209/#210/#211 are docs/UPDATES only relative to that Dig scan for View/chrome facts. Do not re-spec #208. Do not re-spec item 3. Do not re-spec themes / Active chrome B.

**Hard lock:** Implementation is **Antigravity-only on Z13**. Pilot holds one `agy` until this file tip-matches on main and the item-1 hold above has lifted, then owns one `agy`. Do not use Grok Build or Cursor for the handoff into code. Prefer a worktree under `C:\Dev\`; do not invent a new path or create folders from this brief. Do not commit from Antigravity; Pilot/Repo Keeper commit path owns that. Do not invent Erik specs. Stay in `web/` (JS, HTML, CSS). No kernel, C++, `src/`, bindings, or wasm rebuild. No new control ids, hex, pixel sizes, gesture maps, themes, Active chrome B changes, or invented relocation homes.

**Source of truth:**

- Erik overnight ~11:55 PM MT 2026-10-26, item **(4) View popup → top lower tools bar, own show/hide icon**, via CAD Chief. Team decides. Invent-free. Do not invent beyond these words.
- `research/overnight-view-popup-top-tools-bar.md` (Dig, 2026-10-27 ~1:15 AM MT), scanned at tip `c713ce4`. Cite that digest. Anything it marks **TBD** stays **TBD**.
- Park: Top-bar shelf icons (`mvp/requirements.md`, `prompts/antigravity-topbar-shelf-icons.md`). Selection and show/hide camera already get top-bar icons to the right of Tools. That park does not name a View shelf icon. Do not re-spec it.
- Park: Always-visible chrome (`mvp/requirements.md`, `prompts/antigravity-panel-labels-chrome.md`). Permanent: very top (tree + filename), tools menu bar, very bottom (Modify / Create). Everything else show/hide. Region mapping in that brief stays **TBD**. Item 8 is a later Chief lock on the bottom bar. Do not re-spec item 8 here.

Quoted from Dig’s scan of `web/index.html` at `c713ce4` (do not edit `web/` from this docs PR):

- View toolbar: `<div class="vp-bar" role="toolbar" aria-label="View" data-hscroll>` — Analyze (Measure, Section) and Display (Shaded / Shaded+Edges / Wireframe / X-Ray). No `hidden` on that View `vp-bar`.
- `.vp-bar { position: absolute; left: 10px; bottom: 10px; … }` — viewport overlay, not in `.topbar-shelves`. Those pixel values are tip facts. Do not retune them and do not treat them as a new size spec.
- Top lower tools row: `<div class="topbar-shelves" role="toolbar" aria-label="Tools">` under `<header class="topbar">` — Tools menu, `#selectionShelfBtn`, `#cameraShelfBtn`, Info.
- `#selectionShelfBtn` → `#selectionShelf`. `#cameraShelfBtn` → `#cameraShelf` (title/aria “Show/hide camera”). Camera shelf includes Navigate, Views (Front/Top/Right/Home), and Visibility.
- Tip has no `#viewShelfBtn`, no `data-action="viewShelf"`, and no topbar control whose `aria-controls` points at the View `vp-bar`. Do not mint those ids from this sentence. They are the negative scan.
- Sketch-active CSS hides `.vp-bar[aria-label="View"]`. That is not a user show/hide icon.

**Gap (do not invent the fix):** View tools live in the viewport-bottom `.vp-bar` (“View”), not in the top lower tools bar, and they have no own show/hide icon like Selection / Camera.

## Goal
Implement these sourced behaviors in `web/` (JS, HTML, and CSS). No kernel, C++, `src/`, bindings, or wasm rebuild. Watertight / units are N/A.

Erik: **View popup → top lower tools bar, own show/hide icon**.

Coding bar (only Erik’s words plus tip facts in the digest):

1. The View UI that today is the viewport `.vp-bar[aria-label="View"]` moves into the **top lower tools bar** (tip name: `.topbar-shelves` / the tools ribbon). A narrower target label than that stays **TBD**.
2. That View UI gets its **own show/hide icon**, in the same pattern family as `#selectionShelfBtn` / `#cameraShelfBtn`. Do not invent art, hotkeys, or a control id.
3. Do not re-spec Selection / Camera top-bar icons already on tip and in the top-bar shelf park.

Where a line is **TBD**, leave it **TBD**. Do not fill it with a guessed icon, id, or tool list.

## Workflow
1. Read `research/overnight-view-popup-top-tools-bar.md` and the facts above. Copy behavior from those sources only.
2. Move the View UI that is `.vp-bar[aria-label="View"]` into the top lower tools bar.
3. Give that View UI its own show/hide icon. Reuse the existing Selection / Camera show/hide pattern family. Do not design a new icon.
4. Leave Selection and Camera shelves as they are.
5. Where the digest marks a detail **TBD**, leave it **TBD**. Do not decide whether “View popup” also includes the Camera shelf Views cluster. Do not decide whether Measure, Section, and Display stay together. Do not decide whether the old `.vp-bar` node is removed, emptied, or kept. Do not decide phone versus desktop placement. Do not decide how sketch-active hide interacts with the moved View UI.

## Do not bake / TBD
Do not invent and do not bake any of the following. They stay **TBD**:

- Whether “View popup” means only the Analyze+Display `vp-bar`, or also part of the `#cameraShelf` Views cluster
- Exact control id, icon, or label text for the show/hide control
- Whether the viewport `.vp-bar` is removed, emptied, or kept as a host
- Phone vs desktop placement
- Interaction with the sketch-active hide of the View `vp-bar`
- Whether Measure, Section, and Display stay together
- Any new control id
- Any new hex
- Any new pixel size (quoted tip offsets stay facts, not a retune)
- Icon art
- Hotkeys
- Gesture maps
- Themes or Active chrome B
- A new home for any control this item does not name

## Out of scope
- Overnight 1–2 (#208). Do not re-spec them.
- Item 3 (sketch dims follow the angle). Separate brief. Do not re-spec it.
- Item 5 (Home placement), item 6 (cube double-tap), item 7 (sketch clutter), item 8 (bottom bar), item 9 (redundancy pass), item 10 (rebuild note; no coding brief).
- Top-bar shelf icons park and `prompts/antigravity-topbar-shelf-icons.md`. Do not re-spec Selection / Camera.
- Always-visible chrome region mapping. Stays TBD in that brief. Item 8’s Chief lock on the bottom bar is not this item.
- Rust #4 / Modo orange selection hex / triple-tap.
- Editing `research/overnight-view-popup-top-tools-bar.md`, `mvp/requirements.md`, or `UPDATES.md` from the coding `agy`.
- Editing `web/` from this docs PR. The later `agy` is `web/` only.
- Kernel / C++ / wasm rebuild. Do not commit `.wasm`, `web/cadcam.wasm`, or `web/dist/`. Do not edit a root `PROGRESS.md`.

## Smoke
Manual wake smoke on Pages. No new smoke harness. Reuse `tests/deploy_smoke.py` only if that reuse is clearly required; this brief does not require it. No invented pixel asserts. Because no smoke path is added here, do not print a done marker.

Check sourced behavior only. Do not assert a control id, icon art, label string, phone placement, whether the Camera Views cluster moved, whether Measure/Section/Display were split, or a new pixel size.

1. The View UI that was `.vp-bar[aria-label="View"]` is in the top lower tools bar (`.topbar-shelves` / tools ribbon). Do not assert a narrower slot.
2. That View UI has its own show/hide icon, in the Selection / Camera pattern family. Do not assert an id or glyph.
3. Selection and Camera top-bar icons still show and hide their existing shelves.

## Success Criteria
Must PASS at tip-match. Cite Erik overnight item (4) ~11:55 PM MT 2026-10-26 via CAD Chief; `research/overnight-view-popup-top-tools-bar.md`; tip `c713ce4`. Only that bar is in scope.

1. The View popup is in the top lower tools bar.
2. It has its own show/hide icon.
3. Selection / Camera top-bar icons are not re-specified.
4. No invented control id, hex, pixel size, icon art, hotkey, gesture map, theme, or Active chrome B change.
5. This docs PR does not change `web/`.

Outside this hard bar: whether “View popup” includes the Camera Views cluster; the show/hide control’s id, icon, and label; whether `.vp-bar` is removed, emptied, or kept; phone vs desktop; sketch-active hide; whether Measure/Section/Display stay together; items 1–3 and 5–10; Rust #4; Modo orange hex; triple-tap; `UPDATES.md`; kernel / C++ / wasm.

## Done
Draft until tip-match: Doc Steward primary (COMMENT), Research Digest second. Author does not self-APPROVE. Repo Keeper undrafts and plain-merges. Pilot holds the coding `agy` for this item until overnight item 1 Tool Search exit and related tip-matches have landed **and** this brief tip-matches on main. This file does not start an `agy`. One Antigravity-only `agy` on Z13, `web/` only, after that hold lifts. Report the prompt PR link and tip SHA. Pilot reports any implementation PR separately.
