# View popup → top lower tools bar — invent-free digest (overnight item 4)

Status: invent-free digest. Compiled **2026-10-27 ~1:15 AM MT** (America/Denver).
Antigravity feed: `prompts/antigravity-view-popup-top-tools-bar.md`. This digest does not start an `agy`.

**Owner draft:** MVP Research Digest (tip-scan). Doc Steward primary tip for any `prompts/` PR.
**Date:** 2026-10-27 ~1:15 AM MT (America/Denver)
**Gate tip:** main @ `c713ce4` (`c713ce4479349fe11d56a53921edb7dafe866038`) — [#208](https://github.com/cyborgpencil/cad-mvp/pull/208) merged (overnight 1–2 briefs).
**Scope:** Where View UI lives and whether it has a top-bar show/hide icon. UI chrome only (`web/`). Watertight / units N/A.
**Hard lock:** Invent-free. Do not invent icon art, which tools move, a new control id, or a new panel taxonomy. No new hex, pixel sizes, gesture maps, themes, or Active chrome B changes.

---

## Source of truth (cite only these)

### Erik / team

| Source | Statement |
| --- | --- |
| Erik overnight ~11:55 PM MT 2026-10-26 via CAD Chief (room) | Item **(4) View popup → top lower tools bar, own show/hide icon**. Team decides; invent-free. Do not invent beyond these words. |
| Park: Top-bar shelf icons (`mvp/requirements.md`, `prompts/antigravity-topbar-shelf-icons.md`) | Selection + show/hide **camera** already get top-bar icons to the right of Tools. Does **not** name a View shelf icon. |
| Park: Always-visible chrome (`mvp/requirements.md`, `prompts/antigravity-panel-labels-chrome.md`) | Permanent: very top (tree + filename), tools menu bar, very bottom (Modify / Create). Everything else show/hide. Exact region mapping TBD. |

### App behavior on tip `c713ce4` / `web/index.html` (invent-free tip scan)

| Fact | Quote / location |
| --- | --- |
| View toolbar in viewport | `<div class="vp-bar" role="toolbar" aria-label="View" data-hscroll>` — Analyze (Measure, Section) + Display (Shaded / Shaded+Edges / Wireframe / X-Ray). No `hidden` on the View `vp-bar` itself. |
| View bar CSS | `.vp-bar { position: absolute; left: 10px; bottom: 10px; … }` — viewport overlay, not in `.topbar-shelves`. |
| Top lower tools row | `<div class="topbar-shelves" role="toolbar" aria-label="Tools">` under `<header class="topbar">` — holds Tools menu, `#selectionShelfBtn`, `#cameraShelfBtn`, Info. |
| Selection show/hide | `#selectionShelfBtn` → `#selectionShelf` (`data-action="selectionShelf"`, `aria-controls="selectionShelf"`). |
| Camera show/hide | `#cameraShelfBtn` → `#cameraShelf` (`data-action="cameraShelf"`, title/aria **"Show/hide camera"**). Camera shelf includes Navigate + **Views** (Front/Top/Right/Home) + Visibility. |
| No View show/hide icon | Tip has no `#viewShelfBtn` / `data-action="viewShelf"` / topbar control whose `aria-controls` points at the View `vp-bar`. |
| Sketch hide | `html[data-sketch-active] .vp-bar[aria-label="View"] { display: none !important; }` — View bar is suppressed while sketch-active; that is not a user show/hide icon. |
| Always-visible comment in CSS | `/* Always-visible chrome: topbar (tree + filename), toolbox ribbon (tools menu bar), and bottom bar (Modify / Create etc.). Everything else uses show/hide shelves. */` |

**Gap vs Erik wording (do not invent the fix):** View tools live in a viewport-bottom `.vp-bar` (“View”), not in the top lower tools bar (`.topbar-shelves`), and they have **no** own show/hide icon like Selection / Camera.

---

## Recommended invent-free goal (for `prompts/`)

Erik: **View popup → top lower tools bar, own show/hide icon**.

**Coding bar (only Erik words + tip facts):**

1. The View UI that today is the viewport `.vp-bar[aria-label="View"]` must move into the **top lower tools bar** (tip: `.topbar-shelves` / tools ribbon — exact target label TBD if a narrower lock is required).
2. That View UI must have its **own show/hide icon** (same pattern family as `#selectionShelfBtn` / `#cameraShelfBtn` — do not invent art, hotkeys, or a control id).
3. Do not re-spec Selection / Camera top-bar icons already on tip / in park.

**TBD (do not invent):**

- Whether “View popup” means only Analyze+Display `vp-bar`, or also part of `#cameraShelf` Views cluster.
- Exact control id / icon / label text for the new show/hide control.
- Whether the viewport `.vp-bar` is removed, emptied, or kept as a host.
- Phone vs desktop placement.
- Interaction with sketch-active hide of the View `vp-bar`.
- Whether Measure/Section/Display stay together.

## Out of scope

- Overnight 1–2 (merged #208), item 3 dims-follow-angle, items 5–10.
- Rust #4 / Modo orange sel hex / triple-tap (stay TBD).
- Kernel / C++ / wasm / UPDATES.md.
- Themes / Active chrome B. Gesture maps.

## Done

Dig tip-scan committed for the docs brief. No coding `agy`. Pilot holds coding until overnight item 1 Tool Search exit and related tip-matches land, and until the brief tip-matches.
