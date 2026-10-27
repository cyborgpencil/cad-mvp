# Antigravity consolidate then remove the bottom bar

Consolidate, then remove the bottom Create/Modify bar. The units bar is the bottommost band. Chief locked Erik’s newer overnight line over the always-on bottom Create/Modify rule. Create/Modify move only if an existing path already fits. Otherwise that home stays TBD. This file is the Antigravity feed. It does not change the app by itself.

**Gate:** This item’s **code** starts only after this file tip-matches on main **and** overnight item 1 Tool Search exit plus related tip-matches have landed. Overnight 1–2 briefs are on main ([#208](https://github.com/cyborgpencil/cad-mvp/pull/208) @ `c713ce4`). Item 3 brief is on main ([#210](https://github.com/cyborgpencil/cad-mvp/pull/210) @ `1b8a57f`; UPDATES [#211](https://github.com/cyborgpencil/cad-mvp/pull/211)). Pilot holds the coding `agy`. This prompts file does not start an `agy` by itself. Docs base is main @ `7214005` (`72140052f516b59d6560133fc4240f13e5d257c7`, tip after #211). Dig’s scan tip for `web/` remains `c713ce4` (`c713ce4479349fe11d56a53921edb7dafe866038`). #209/#210/#211 are docs/UPDATES only relative to that Dig scan for View/chrome facts. Do not re-spec #208. Do not re-spec item 3. Do not re-spec themes / Active chrome B.

**Hard lock:** Implementation is **Antigravity-only on Z13**. Pilot holds one `agy` until this file tip-matches on main and the item-1 hold above has lifted, then owns one `agy`. Do not use Grok Build or Cursor for the handoff into code. Prefer a worktree under `C:\Dev\`; do not invent a new path or create folders from this brief. Do not commit from Antigravity; Pilot/Repo Keeper commit path owns that. Do not invent Erik specs. Stay in `web/` (JS, HTML, CSS). No kernel, C++, `src/`, bindings, or wasm rebuild. No new control ids, hex, pixel sizes, gesture maps, themes, Active chrome B changes, or invented relocation homes.

**Source of truth:**

- Erik overnight ~11:55 PM MT 2026-10-26, item **(8) Consolidate then remove bottom bar; units bar = bottommost**, via CAD Chief. Invent-free.
- Chief lock, 2026-10-27 ~1:17 AM MT via 3T · Chief: **Erik’s newer overnight wins** over the always-on bottom Create/Modify lock. Consolidate, then remove that bottom bar. The units bar is bottommost. Relocate Create/Modify only if an existing path already fits; otherwise the destination stays **TBD**. Do not invent a new home.
- `research/overnight-consolidate-remove-bottom-bar.md` (Dig, 2026-10-27 ~1:15 AM MT), scanned at tip `c713ce4`. Cite that digest. Anything it still marks **TBD** stays **TBD**.
- Always-visible chrome park and `prompts/antigravity-panel-labels-chrome.md`: very top (tree + filename), tools menu bar, and very bottom (Modify / Create) were the permanent panels. This brief supersedes **only** the always-on bottom Create/Modify rule. Very top and the tools menu bar stay as that park states. Do not rewrite the older bullet in `mvp/requirements.md` from the coding `agy`.
- Sketch draw overhaul park and `prompts/antigravity-sketch-draw-overhaul.md`: while sketching, very top and very bottom (Modify / Create) stay visible. Chief’s newer lock wins for **that bottom bar**, including while sketching. Do not re-spec the rest of the overhaul (live length/angle, dims stay, #183 strip, Finish Sketch).

Quoted from Dig’s scan of `web/index.html` at `c713ce4`:

- Units bar: `<footer class="statusbar" aria-label="Units">` with `Units`, `#statusUnits` (mm), `#statusHint`, `#buildStamp`. It is the document footer.
- Desktop bottom: `<div class="desk-bottom" role="toolbar" aria-label="Create and modify">` — Create and Modify. Hidden by default; shown from min-width 821px at height 52px. That height is a tip fact. Do not retune it and do not treat it as a new size spec.
- Phone: `<nav class="phone-tabbar">` — Pick, Multi, Undo, Redo, Create, Modify, and Model/Repair/Export tabs. Hidden at the base rule; phone breakpoints show it.
- `#modifyShelf` holds Move/Rotate/Resize/Fillet/Chamfer/Booleans/Delete and is `hidden` until opened.
- `.vp-bar[aria-label="View"]` is a viewport overlay, not the document footer. Item 4 owns that View popup. Do not move it here.
- DOM order at the bottom of the shell places `#modifyShelf`, then `.desk-bottom`, then `.phone-tabbar`, and the units `footer.statusbar` is the bottommost footer element in the scanned markup.
- Create’s existing action on those bars is `data-action="createMenu"`. Modify’s existing action is `data-action="modifyShelf"`. Those facts are not a decision that either path fits as the new home.

**Gap:** Create/Modify bottom bars are still present beside the units footer. Erik wants them consolidated, then removed, with the units bar bottommost.

## Goal
Implement these sourced behaviors in `web/` (JS, HTML, and CSS). No kernel, C++, `src/`, bindings, or wasm rebuild. Watertight / units gate / export mm lock are unchanged.

Erik + Chief:

1. **Consolidate** the bottom Create/Modify bar, then **remove** it. This replaces the always-on very-bottom Create/Modify rule, including during sketch. Very top and the tools menu bar stay.
2. The **units bar** (`footer.statusbar[aria-label="Units"]`) is the bottommost chrome band.
3. Relocate Create/Modify **only if an existing path already fits**. If none fits, the destination stays **TBD**. Do not add a bar, icon, shelf, or control id to house them. Do not decide that `createMenu` or `#modifyShelf` fits. Record the reachability gap when the bar is removed and no existing path fits. Removal is still the lock. A new home invented to avoid that gap fails.

Where a destination or phone-nav question is **TBD**, leave it **TBD**.

## Workflow
1. Read `research/overnight-consolidate-remove-bottom-bar.md` and the Chief lock. Copy behavior from those sources only.
2. Treat `.desk-bottom` (Create and Modify) as the desktop bottom bar named by the always-visible lock. Remove it after consolidate.
3. Create and Modify on `.phone-tabbar` are part of that same bottom Create/Modify bar. Whether the rest of `.phone-tabbar` (Pick, Multi, Undo, Redo, Model/Repair/Export) goes away stays **TBD**. Do not delete that rest by guess.
4. Keep the units footer bottommost. Do not change units copy, the mm gate, or RustGate.
5. Do not invent a relocation home. Existing actions may be reused only when that path already performs the job without a new control. If it does not, stop and leave TBD.
6. Leave the viewport View `vp-bar` to item 4.
7. Do not add show-hide animation. That treatment is TBD.

## Do not bake / TBD
Do not invent and do not bake any of the following. They stay **TBD**:

- Which existing path fits Create/Modify, if any
- A new home, bar, icon, or control id for Create or Modify
- Phone-tabbar fate beyond the Create/Modify controls (whole nav versus those two)
- Whether the viewport `.vp-bar` is part of this item (it is item 4)
- Show-hide animation during consolidate
- Any new hex
- Any new pixel size (the tip 52px height is not a retune target)
- Icon art
- Hotkeys
- Gesture maps
- Themes or Active chrome B

Resolved, and therefore not TBD: the always-on bottom Create/Modify bar is consolidated and then removed. The units bar is bottommost. Chief, 2026-10-27 ~1:17 AM MT via 3T · Chief. Very top and the tools menu bar are not part of this removal.

## Out of scope
- Units gate, RustGate, export mm lock, STL/3MF checks.
- Item 4 View popup. Item 5 Home placement. Item 6 cube double-tap. Item 7 sketch clauses. Item 9 redundancy punch list (there is none). Item 10 rebuild note (no coding brief).
- Overnight 1–2 (#208) and item 3. Do not re-spec them.
- Modo orange selection hex / triple-tap / Rust #4.
- Editing the older always-visible or overhaul bullets in place. This brief is the override for the bottom bar. The coding `agy` does not edit `mvp/requirements.md`.
- Editing `research/overnight-consolidate-remove-bottom-bar.md` or `UPDATES.md` from the coding `agy`.
- Editing `web/` from this docs PR.
- Kernel / C++ / wasm rebuild. Do not commit `.wasm`, `web/cadcam.wasm`, or `web/dist/`. Do not edit a root `PROGRESS.md`.

## Smoke
Manual wake smoke on Pages. No new smoke harness. Reuse `tests/deploy_smoke.py` only if that reuse is clearly required; this brief does not require it. No invented pixel asserts. Because no smoke path is added here, do not print a done marker.

Check sourced behavior only. Do not assert a new Create/Modify home, a phone-tabbar layout beyond the removed Create/Modify bottom bar, a pixel height, or a units-value change.

1. The bottom Create/Modify bar (desktop `.desk-bottom`, and the Create/Modify controls that were the phone bottom bar) is gone after consolidate.
2. The units footer is the bottommost chrome band.
3. Very top (tree + filename) and the tools menu bar still stay.
4. No new control was added to rehouse Create or Modify. If no existing path fits, the destination is still TBD and no stand-in home exists.
5. Units still read mm. The export gate behavior is unchanged.

## Success Criteria
Must PASS at tip-match. Cite Erik overnight item (8) ~11:55 PM MT 2026-10-26 via CAD Chief; Chief lock 2026-10-27 ~1:17 AM MT via 3T · Chief; `research/overnight-consolidate-remove-bottom-bar.md`; tip `c713ce4`. Only that bar is in scope.

1. The bottom Create/Modify bar is consolidated, then removed. The older always-on rule for that bar does not win, including while sketching.
2. The units bar is bottommost.
3. Create/Modify are relocated only along an existing path that already fits. Otherwise the destination stays TBD. No invented home.
4. Very top and the tools menu bar are unchanged by this item.
5. No invented control id, hex, pixel size, gesture, theme, or Active chrome B change. No units-gate edit.
6. This docs PR does not change `web/`.

Outside this hard bar: which existing path fits; the rest of the phone tabbar; the viewport View bar (item 4); consolidate animation; items 1–7, 9, and 10; `UPDATES.md`; kernel / C++ / wasm.

## Done
Draft until tip-match: Doc Steward primary (COMMENT), Research Digest second. Author does not self-APPROVE. Repo Keeper undrafts and plain-merges. Pilot holds the coding `agy` for this item until overnight item 1 Tool Search exit and related tip-matches have landed **and** this brief tip-matches on main. This file does not start an `agy`. One Antigravity-only `agy` on Z13, `web/` only, after that hold lifts. Report the prompt PR link and tip SHA. Pilot reports any implementation PR separately.
