# Antigravity iPad/Kiwi gestures + float-dock

Touch-first gesture family and a dockable-or-draggable floating panel so the viewport stays clear. This file is the Antigravity feed. It does not change the app by itself.

**Gate:** Next coding slice after X-ray select-through tip-merges on main (#197 tip `d0514a4` / brief #195 merge `aa635b6`). Theme feature stays after this. Rust #4 HOLD (no `.cadmvp` freeze).

**Hard lock:** Implementation is **Antigravity-only on Z13**. Pilot holds one `agy` until this file tip-matches on main, then owns one `agy`. Do not use Grok Build or Cursor for the handoff into code. Prefer worktree `C:\Dev\cadcam-mvp` if Pilot says otherwise; do not invent a new path or create folders from this brief. Do not commit from Antigravity; Pilot/Repo Keeper commit path owns that. Do not invent Erik specs. No kernel, C++, `src/`, bindings, or wasm rebuild — stay in `web/` (JS, HTML, CSS). Prefer reusing existing floating panels / touch handlers; if none fit, implement only the locked behaviors without inventing control names, placement, hotkeys, or icons beyond what this brief states. No new UI for a gesture action this brief marks **TBD**.

**Source of truth:**

- Erik via 3T, 2026-10-26 ~6:31 PM MT (research) and ~8:47 PM MT (OK to implement after X-ray): prefer **tap / long-press / double / triple-tap**; **dockable-or-draggable floating panel** so the viewport stays clear; **keep live dims**.
- Pattern sources for invent-free summary (Doc/Dig; Erik OK): **Shapr3D** + **Onshape Mobile** for touch gesture family; **Foundry Modo** for float/dock (Thumb tear-off → float; drag-to-edge → dock). Chief relay 2026-10-26 ~9:49 PM MT: Modo dock **L/R**; **triple-tap TBD**.
- Chief + 3T lock, 2026-10-26 ~10:24 PM MT, for the gesture binds (this replaces the earlier park that the exact per-gesture action map is TBD):
  1. **tap** = **select**
  2. **long-hold** (long-press) = **precision/area** if that path already exists in the app; else **TBD** (do not invent precision/area UI)
  3. **double-tap** = **clear-selection** or **zoom-to**, whichever already exists; else **TBD** (do not invent both or pick inventively — map invent-free to existing tools)
  4. **2-finger tap** = **context menu** only if a context menu already exists; else **TBD**
  5. **triple-tap** = **TBD** (recognize only, no action)
- Paths present on main (name a function only when it exists; otherwise the action stays the conditional **TBD** above):
  - Select exists. Wire tap to `selectionFromTap` in `web/phone-select.mjs` and to `applyPointerSelection` in `web/selection.mjs` on the branch the viewport pointer-up in `web/index.html` already uses. Do not add a second select tool.
  - Precision/area select does not exist in `web/`. `LONG_PRESS_MS` in `web/viewport-selection.mjs` is the view-cube / field-nudge hold clock, not a precision or area select. Long-hold action stays **TBD**.
  - Zoom to Fit exists: `goView('fit')` in `web/index.html`, toolbar `data-action="fit"` (`data-tool="Zoom to Fit"`). No clear-selection command exists. Empty-hit clear inside `selectionFromTap` / `applyPointerSelection` stays on the tap path. Double-tap binds to Zoom to Fit only.
  - No viewport context menu exists. The viewport `contextmenu` listener in `web/index.html` only calls `preventDefault()`. `#fileMenu`, `#exportMenu`, `#createMenu`, and `#pickChooser` are chrome menus, not a 2-finger context menu. 2-finger tap action stays **TBD**.
- Dig research: box `research/ipad-cad-kiwi-modo-gestures-panels.md` (not a second source of locks).

Anything these locks do not state stays **TBD**.

## Goal
Implement these sourced behaviors in `web/` (JS, HTML, and CSS). No kernel, C++, `src/`, bindings, or wasm rebuild. Bind each gesture to an existing app path, or leave the action **TBD**. No new UI for a TBD action.

Locked gesture → action map (Chief + 3T, 2026-10-26 ~10:24 PM MT):

1. **tap → select.** Use the existing viewport pointer-up branch in `web/index.html`: `selectionFromTap` (`web/phone-select.mjs`) or `applyPointerSelection` (`web/selection.mjs`). Do not add a second select tool.
2. **long-hold (long-press) → precision/area only if that path already exists; else TBD.** It does not exist. Recognize long-hold. Do not invent precision or area UI. Do not bind long-hold to `LONG_PRESS_MS`.
3. **double-tap → clear-selection or zoom-to, whichever already exists; else TBD.** Zoom to Fit already exists (`goView('fit')`, `data-action="fit"`). A clear-selection command does not. Bind double-tap to Zoom to Fit only. Do not invent a clear-selection command, and do not call both. Do not retarget view-cube double-tap Home.
4. **2-finger tap → context menu only if a context menu already exists; else TBD.** None exists. Recognize the gesture and take no menu action. Do not invent a context menu. Do not open `#fileMenu`, `#exportMenu`, `#createMenu`, or `#pickChooser` as a substitute. Two fingers still pinch/pan (`gesture.type === 'pinch'` in `web/index.html`); do not replace that path.
5. **triple-tap → TBD.** Recognize the gesture. No action.

Unchanged locks:

- **Floating panel** that can **float (drag)** or **dock left or right** (Modo tear-off → float; drag-to-edge → dock L/R) so the **viewport stays clear**. No tear-off or dock-left/right handler was found in `web/`. Do not invent a control id, CSS selector, hex color, icon, or hotkey for it, and do not retarget `#dimPanel` or the live-dim callouts.
- **Keep live dims** — do not regress dims-stay while drawing (already on main from sketch-draw overhaul). This brief does not re-spec the dim confirm model.

## Workflow
1. Read the locks above. Copy behavior from those locks only.
2. Where touch is already handled, recognize **tap**, **long-press** (long-hold), **double-tap**, **2-finger tap**, and **triple-tap** as distinct events. Reuse a timing or tolerance constant the current touch path already has. Do not invent pixel thresholds, timings, or new numbers. Do not copy the view-cube double-tap window onto this family.
3. Bind actions from the map, and nowhere else:
   - tap → existing select path (`selectionFromTap` / `applyPointerSelection`)
   - long-hold → no action (precision/area **TBD**; no new UI)
   - double-tap → existing `goView('fit')` only
   - 2-finger tap → no action (context menu **TBD**; no new UI); leave pinch/pan as it is
   - triple-tap → no action
4. Implement a floating panel the user can drag and dock to the **left or right** edge (Modo dock L/R). Viewport must remain usable (the panel does not permanently eat the work area). Do not invent control ids, CSS selectors, pixel sizes, hex colors, icon art, hotkeys, or a new toolbar placement. No top or bottom dock.
5. Where a detail is **TBD**, leave it TBD.
6. Do not regress live dims while drawing.

## Do not bake / TBD
Do not invent and do not bake any of the following. Park TBDs stay **TBD**, verbatim:

- triple-tap action
- long-hold precision/area action, and any precision or area UI
- 2-finger context menu, and any new menu
- a clear-selection command (not found; do not add one beside Zoom to Fit)
- touch timing / pixel thresholds this brief does not already name as an existing constant (do not invent numbers)
- dock snap pixel sizes; top/bottom dock (brief locks L/R only)
- control ids, CSS selectors, hex colors, icon art, hotkeys
- phone vs desktop layout exceptions Erik did not state
- “Kiwi Modo” as a different product than Foundry Modo (name gap — Foundry Modo is the float/dock pattern source)
- retargeting view-cube double-tap Home
- treating `LONG_PRESS_MS` as precision/area

## Out of scope
- X-ray select-through (#163 / #195 / #197). Do not re-spec.
- Theme Default + Modo (next after this brief). Do not implement theme tokens here.
- Panel labels + always-visible chrome already on main. Do not re-spec.
- Sketch chrome / sketch-draw overhaul already on main. Do not re-spec dims beyond “do not regress”.
- Rust #4 HOLD. No `.cadmvp` freeze.
- This brief does not edit `mvp/requirements.md` unless Doc separately parks a bullet.
- Kernel / C++ / wasm rebuild. Do not commit `.wasm`, `web/cadcam.wasm`, or `web/dist/`. Do not edit `UPDATES.md` or a root `PROGRESS.md`.

## Smoke
Manual wake smoke on Pages. No new smoke harness. Reuse `tests/deploy_smoke.py` only if that reuse is clearly required; this brief does not require it. No invented pixel asserts. Because no smoke path is added here, do not print a done marker.

Check locked behavior only:

1. **tap** selects through the existing path (`selectionFromTap` / `applyPointerSelection`). No second select tool.
2. **long-hold** is a distinct event and does not open precision or area UI (action **TBD**).
3. **double-tap** runs existing Zoom to Fit (`goView('fit')`) and does not also clear the selection. View-cube double-tap Home is unchanged.
4. **2-finger tap** is a distinct event, opens no context menu (action **TBD**), and does not replace two-finger pinch/pan.
5. **triple-tap** is recognized with **no action** (**TBD**).
6. A floating panel can be dragged and docked to the **left or right** so the viewport stays clear.
7. Live dims while drawing are not regressed.

## Success Criteria
Must PASS at tip-match. Cite Erik via 3T 2026-10-26 ~6:31 PM MT / ~8:47 PM MT, Chief Modo dock L/R (2026-10-26 ~9:49 PM MT), and the Chief + 3T gesture binds (2026-10-26 ~10:24 PM MT). Only locked behavior is on this bar.

1. **tap** selects via the existing select path. No second select tool.
2. **long-hold** is recognized; precision/area stays **TBD** (no invented UI).
3. **double-tap** calls existing Zoom to Fit (`goView('fit')`) only. No invented clear-selection.
4. **2-finger tap** is recognized; context menu stays **TBD** (no invented menu). Existing pinch/pan stays.
5. **triple-tap** is recognized with no action (**TBD**).
6. Floating panel can float (drag) and dock **left or right**; viewport stays clear.
7. Live dims while drawing are not regressed.

Outside this hard bar: triple-tap action, long-hold precision/area, 2-finger context menu, a clear-selection command, touch timings/px, control ids, CSS selectors, hex colors, icon art, hotkeys, top/bottom dock, theme tokens, X-ray, Rust #4, `mvp/requirements.md`, `UPDATES.md`, and `research/`.

## Done
Draft until tip-match: Doc Steward primary (COMMENT), Research Digest second. Author does not self-APPROVE. Repo Keeper undrafts and plain-merges. After this file is on main, Pilot runs one Antigravity-only `agy` from it. Report the prompt PR link and tip SHA. Pilot reports any implementation PR separately. Theme invent-free brief follows this merge.
