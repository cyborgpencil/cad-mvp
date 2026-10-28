# Antigravity off-bar menus — slice 1 — float register

Slice 1 of the Chief 3-way merge train. Register the four off-bar menus on the existing float dock so they can leave the anchored dropdown and be dragged. No Close control in this slice. This file is the Antigravity feed for slice 1. It does not change the app by itself.

**Gate:** Antigravity-only on Z13. Pilot holds until this file tip-matches on main, then launches **this slice only**. Chief authorizes multi-agy only after all three float files tip-match. Merge order is 1 before 2 before 3. This prompts file does not start the `agy` by itself.

**Hard lock:** Implementation is **Antigravity-only on Z13**. Do not use Grok Build or Cursor for the handoff into code. Prefer worktree `C:\Dev\cadcam-mvp` if Pilot says otherwise; do not invent a new path or create folders from this brief. Do not commit from Antigravity; Pilot/Repo Keeper commit path owns that. Do not invent Erik specs. Stay in `web/` (JS, HTML, CSS). No kernel, C++, `src/`, bindings, or wasm rebuild. Do not edit `UPDATES.md` or a root `PROGRESS.md`. Do not edit this prompt, the monolith, or the other slice files from the `agy`.

**Source of truth:**

- Chief FINAL LOCK (DEV Chief, 2026-10-27 ~6:45 PM MT): float is a **3-way** merge train. This file is slice **1** (float register, no Close).
- Combined lock, left in place: `prompts/antigravity-offbar-menus-float-drag-close.md`. Do not contradict it. Do not delete it. Where this slice is narrower, this file wins for the `agy`: Close, snap, persist, and z-order are not this slice.
- Tip `5ee57eee269f4f49429d17d150faeaf7b88584f8` (`5ee57ee`, main after #240). Read `web/index.html` from that commit; do not invent ids:
  - `#fileMenu` (`.menu`, `role="menu"`, `aria-label="File"`), opened by `#fileBtn` / `data-action="fileMenu"`, inside `.menu-wrap`.
  - `#exportMenu` (`.menu`, `role="menu"`, `aria-label="Export"`), opened by `#exportBtn` / `data-action="exportMenu"`, inside `.export-wrap` (`position: relative`).
  - `#createMenu` (`.create-menu`, `role="menu"`, `aria-label="Create"`). Openers: `#createDesktop` and the tools-sheet Create button, both `data-action="createMenu"`.
  - About chrome: `.menu-wrap` > button `data-action="aboutMenu"` (`aria-label="Info"`) and a `.menu` with `role="region"` `aria-label="About"`. That `.menu` has **no id** on this tip. Do not invent one. The inspector block `#inspector [aria-label="About"]` is a `.prop`, not a `.menu`. It is not an off-bar menu for this brief.
  - `.menu` is `position: absolute; top: calc(100% + 4px); left: 0` (anchored dropdown). `#createMenu` is already `position: fixed` (`.create-menu`). `placeCreateMenu()` writes inline `left` / `top` / `right` / `bottom` / `width` from the visible opener, and on the narrow layout clears those inline styles.
  - `.menu` `z-index` is `30`. `.create-menu` `z-index` is `40`. Leave both.
  - Outside click already ignores `.menu-wrap`, `.export-wrap`, `.search-dlg`, `.sheet`, `.create-menu`, `.pick-chooser`, and `#sketchSheet` (`closest` at the pointer path). Do not replace that list.
- Float-dock already on tip (`setupFloatingPanelDock()`):
  - `floatPanels` = `#sketchSheet, #edgeSheet, #toolsSheet, .vp-bar, #searchDlg, #browser, #inspector`.
  - Pointer drag on the panel. `onPanelPointerDown` returns early for `input, textarea, select, a, label.menu-file`. Movement past existing `tapSlopPx()` drags. `applyPanelPosition` docks `left` when `rawLeft <= 0`, `right` when `rawLeft >= maxLeft`, otherwise `float`. `position: fixed` is set only for `#browser` and `#inspector` (`panel.style.position = 'fixed'` on that drawer branch). `floatingPanelStates()` publishes `panelDockState` for the gate.
  - Those selectors do **not** include `#fileMenu`, `#exportMenu`, `#createMenu`, or the About `.menu`. That gap is this slice.

Anything these locks do not state stays **TBD**.

## Goal
In `web/` only, register the four off-bar menus on the existing float dock and let `applyPanelPosition` move them. No Close chrome in this slice. No kernel, C++, `src/`, bindings, or wasm rebuild.

Menus in this brief (the full set on tip — do not add others):

1. `#fileMenu`
2. `#exportMenu`
3. `#createMenu`
4. The About `.menu` inside `.menu-wrap` (`aria-label="About"`, no id). Do not invent an id.

`#pickChooser` (`class="pick-chooser"`, `role="menu"`) is not `.menu` or `.create-menu`. Do not retarget it.

Locked behavior for this slice:

1. **Float.** Once opened, each menu above is a panel over the viewport, not stuck only as the anchored `.menu` dropdown (`position: absolute` under the opener) or only as the `placeCreateMenu()` anchor. Reuse `applyPanelPosition`. Reuse the existing `position: fixed` assignment (`#browser` / `#inspector`) so `#fileMenu`, `#exportMenu`, and the About `.menu` can leave `position: absolute`. `#createMenu` is already `position: fixed`. Do not invent a new positioning scheme, a new offset, or a new px value. Existing `.menu` `top: calc(100% + 4px)` stays the pre-drag anchor rule; do not add another number.
2. **Drag.** Extend `setupFloatingPanelDock()` `floatPanels` (or the same pointer handlers) to include these menus. Do not add a second drag system. Do not invent a tear-off affordance id. Drag-from-chrome is the existing panel `pointerdown` path; mirror that. Keep the existing early-return for `input, textarea, select, a, label.menu-file`, and keep `tapSlopPx()` as the move threshold. `#fileMenu` contains `label.menu-file` (Load); that early-return stays.

Unchanged:

- Existing float-dock on `#sketchSheet`, `#edgeSheet`, `#toolsSheet`, `.vp-bar`, `#searchDlg`, `#browser`, `#inspector` keeps working, including edge dock left / right and mid = float.
- Outside-click `closest` list stays as on this tip.
- Phone tappable chrome stays **≥44 CSS px**. Do not add a px size.

## Workflow
1. Read the locks above. Copy behavior from those locks only.
2. Register `#fileMenu`, `#exportMenu`, `#createMenu`, and the About `.menu` (`.menu-wrap .menu[aria-label="About"]`) on the existing `setupFloatingPanelDock()` list. Do not register `#pickChooser` or `#inspector [aria-label="About"]`.
3. When a registered menu is open, let `applyPanelPosition` move it. Reuse the existing `position: fixed` assignment so `#fileMenu`, `#exportMenu`, and the About `.menu` are not left `position: absolute` inside the bar. `#createMenu` is already `position: fixed`. Do not add a third placer beside `placeCreateMenu()` and `applyPanelPosition`. Open-time placement may still run; drag after open uses the dock path. Do not invent session persist to reconcile them.
4. Where a detail is **TBD**, leave it TBD.
5. Do not regress the panels already in `floatPanels`.
6. Do not add Close UI. Slice 2 owns `.sheet-h` after this slice is on main.

## Do not bake / TBD
Do not invent and do not bake any of the following. Park TBDs stay **TBD**, verbatim:

- Close UI, `.sheet-h`, `button.icon-btn` Close, `data-action="closeSheet"` on these menus, `aria-label="Close"`, or `<span>Close</span>`
- Snap grid, or any snap beyond the edge dock `applyPanelPosition` already implements (`left` / `right` / `float`)
- Persist XY across sessions
- Z-order stacking rules (do not invent a new `z-index`; `.menu` is `30` and `.create-menu` is `40` on this tip — leave them)
- New hotkeys
- New hex colors
- New px sizes or a new tap threshold (keep `tapSlopPx()` and the 44 CSS px floor already on `.menu button` / `.create-menu button`)
- New control ids, new action names, new classes, new icon glyphs
- A tear-off affordance id
- A second drag system
- A new smoke harness
- Plane-pick toggle
- Menu-bar shrink, overflow, or collapse

## Out of scope
- Slice 2 Close chrome and slice 3 regression smoke. Do not implement them from this file.
- Snap grid beyond the edge dock; persist XY; z-order / a new `z-index`.
- Shrink. Plane-pick. `#pickChooser`. `#inspector [aria-label="About"]`.
- Item-7 / flesh / brightness / `#modifyShelf` Delete-in-sketch. Do not code them from this brief.
- Theme / Modo tokens / Rust HOLD.
- `UPDATES.md` / root `PROGRESS.md` edits from this brief.
- Kernel / C++ / wasm rebuild. Do not commit `.wasm`, `web/cadcam.wasm`, or `web/dist/`.

## Smoke
Manual wake smoke. No new smoke harness. Reuse `tests/deploy_smoke.py` only if that reuse is clearly required; this brief does not require it. No invented pixel asserts. Because no smoke path is added here, do not print a done marker.

Check locked behavior for this slice only:

1. Opening `#fileMenu`, `#exportMenu`, and `#createMenu` yields a panel that can float and be dragged with the existing dock/float machinery (the `floatPanels` extension).
2. The About `.menu` (no id) does the same.
3. `#sketchSheet`, `#edgeSheet`, `#toolsSheet`, `.vp-bar`, `#searchDlg`, `#browser`, and `#inspector` still float and dock as before.
4. The outside-click ignore list is unchanged.
5. Snap grid, persist, and z-order are not implemented (**TBD**).
6. No Close control was added. No plane-pick toggle, no menu-bar shrink, no overflow/collapse, no new ids, px, hex, or hotkeys.

## Success Criteria
Must PASS at tip-match. Cite Chief FINAL LOCK 3-way slice 1, the monolith `prompts/antigravity-offbar-menus-float-drag-close.md`, and tip `5ee57eee269f4f49429d17d150faeaf7b88584f8` `web/index.html`. Only locked behavior is on this bar.

1. `#fileMenu`, `#exportMenu`, and `#createMenu` open as panels that float and drag via `setupFloatingPanelDock` / `applyPanelPosition` (extended registration). Not stuck only as the anchored dropdown or only as the `placeCreateMenu()` anchor.
2. The About `.menu` inside `.menu-wrap` (`.menu-wrap .menu[aria-label="About"]`) is in that same set. No invented id.
3. `applyPanelPosition`’s existing `position: fixed` assignment is reused so those menus can leave `position: absolute`. `#createMenu` was already `position: fixed`.
4. Early-return `input, textarea, select, a, label.menu-file` and `tapSlopPx()` stay.
5. `#pickChooser` and `#inspector [aria-label="About"]` are not registered.
6. Existing float-dock panels still dock left / right and float in the middle. No regression.
7. Snap / persist / z-order stay **TBD**. `.menu` stays `30`. `.create-menu` stays `40`.
8. No Close UI, no plane-pick toggle, no few-px shrink, no overflow/collapse, no invented ids, px, hex, hotkeys, glyphs, or a second drag system.
9. Tappable chrome stays ≥44 CSS px. No new px threshold.

Outside this hard bar: Close chrome, snap grid, persist, z-order, plane-pick, menu-bar shrink, overflow/collapse, item-7, theme, Rust, `UPDATES.md`, `PROGRESS.md`, and `research/`.

## Done
Draft until tip-match. Dig tip-match is COMMENT-only. Doc Steward is second. Repo Keeper undrafts and plain-merges. Author does not self-APPROVE. Doc does not edit `UPDATES.md`. Pilot runs multi-agy only after Chief authorizes it, and only after all three float files tip-match. Merge order is 1 → 2 → 3. This file is slice 1; Pilot launches this slice only from this file. Report the prompt PR link and tip SHA. Pilot reports any implementation PR separately.
