# Move Home onto the top-view control — invent-free digest (overnight item 5)

Status: invent-free digest. Compiled **2026-10-27 ~1:15 AM MT** (America/Denver).
Antigravity feed: `prompts/antigravity-home-onto-top-view-control.md`. This digest does not start an `agy`.

**Owner draft:** MVP Research Digest (tip-scan). Doc Steward primary tip for any `prompts/` PR.
**Date:** 2026-10-27 ~1:15 AM MT (America/Denver)
**Gate tip:** main @ `c713ce4` (`c713ce4479349fe11d56a53921edb7dafe866038`) — [#208](https://github.com/cyborgpencil/cad-mvp/pull/208) merged.
**Scope:** Home control placement. UI chrome only. Watertight / units N/A.
**Hard lock:** Invent-free. Do not invent a new Home behavior beyond existing tip + prior Home park. Do not invent which node is the top-view control. No new control ids, hex, pixel sizes, gesture maps, themes, or Active chrome B changes.

---

## Source of truth (cite only these)

### Erik / team

| Source | Statement |
| --- | --- |
| Erik overnight ~11:55 PM MT 2026-10-26 via CAD Chief | Item **(5) Move Home from viewport mid-top onto top-view control**. Invent-free. |
| Park: View cube / Home (`mvp/requirements.md`, `prompts/antigravity-view-cube-gizmo-line-dims.md`) | **Home** centers on selected model when something is selected; else **0,0,0**. TBD: pixel thresholds, hold timing, Home **key** binding. |
| Prior view-cube brief (`prompts/antigravity-view-cube.md`) | Face/corner taps + **double-tap Home iso** stay (adjacent swipe work). Placement of the Home **button** is not that brief’s move target. |
| Chief lock, 2026-10-27 ~1:17 AM MT via 3T · Chief (item 6) | Home **leaves the cube** and moves to the top-view control (this item). The cube’s current Home double-tap binding is dropped in item 6. This lock does **not** name which tip node “top-view control” is. |

### App behavior on tip `c713ce4` / `web/index.html`

| Fact | Quote / location |
| --- | --- |
| Mid-top Home button | `<button … class="vc-home" id="vcHome" data-action="view" data-view="home" data-tool="Home view" title="Home view">Home</button>` inside `#viewport`. |
| CSS placement | `.vc-home { position: absolute; top: 8px; right: 148px; z-index: 6; min-width/min-height: 44px; … }` |
| Runtime placement | `layoutChrome()` sets `home.style.top = marginTop + 'px'` and `home.style.right = (marginRight + cubeCss + pad + 8) + 'px'` — sits mid-top beside the view cube. |
| Second Home control | Inside `#cameraShelf` Views cluster: `<button … data-action="view" data-view="home" data-tool="Home view" title="Iso">` with `#i-iso` icon. |
| Top view control (separate) | Same Views cluster: `data-view="top"` / `data-tool="View: Top"` / title `Top`. |
| Action path | `action === 'view'` → `goView(btn.getAttribute('data-view') \|\| 'home')`. |
| `goView('home')` | Uses `VIEWS.home` (`theta: Math.PI/4`, `phi: 0.96` — same numbers as `VIEWS.iso`) + `homeTargetAndRadius()` (selection → fit that; else origin `0,0,0`). |
| Overlap logic | `layoutDimSheet` / `layoutRects` / phone safe-pad treat `#vcHome` as a reserved mid-top rect (e.g. `coversHome`). |

**Gap vs Erik wording:** Home is still a floating viewport mid-top control (`#vcHome`). Erik wants it **moved onto top-view control**. Tip already has a Home/Iso control inside the Camera shelf Views group and a separate **Top** view button — which of those (or another “top-view control”) is the destination is **not** stated; do not invent.

---

## Recommended invent-free goal (for `prompts/`)

1. Remove / stop using viewport mid-top `#vcHome` as the Home entry (Erik: move **from** viewport mid-top). Do not do that by guessing a destination.
2. Home must be reachable from the **top-view control** (Erik’s words only). Do not invent which tip node that is.
3. Preserve existing Home aim behavior already on tip / in park (selected model else 0,0,0) unless Erik says otherwise — this overnight line is a **placement** ask.
4. Item 6 drops the cube double-tap Home binding. This item is the placement of Home after it leaves the cube. Do not implement the stretch toggle here.

**TBD (do not invent):**

- Exact destination: Camera shelf Iso/Home button, the Top view button, a new control on `.topbar-shelves`, or something else named “top-view control”.
- Whether the duplicate Camera-shelf Home stays, merges, or is the destination.
- Phone layout after `#vcHome` removal (cube / dim-sheet overlap helpers).
- Home key binding (already TBD in the View cube park).

A guessed destination does not pass. Until Erik or Chief names the node, do not add a Home control and do not pick among the tip Home / Iso / Top controls.

## Out of scope

- View-cube double-tap stretch (item 6). Adjacent swipe.
- Items 4, 7–10; Rust #4 / Modo orange / triple-tap.
- Kernel / C++ / wasm / UPDATES.md.
- Themes / Active chrome B. Gesture maps. New pixel sizes.

## Done

Dig tip-scan committed for the docs brief. No coding `agy`. Pilot holds coding until overnight item 1 Tool Search exit and related tip-matches land, and until the brief tip-matches.
