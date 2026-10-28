# Antigravity off-bar menus float + drag + Close

Active multi-agy feed (Chief FINAL LOCK 2026-10-27, merge order 1→2→3): `prompts/antigravity-offbar-agy-float-register.md`, then `prompts/antigravity-offbar-agy-close-chrome.md`, then `prompts/antigravity-offbar-agy-regression-smoke.md`. This file stays.

Off-bar menus float over the viewport, drag with the existing float-dock path, and show an explicit Close control. This file is the combined lock. It does not change the app by itself.

**Gate:** Chief lock piece (3) only, on main tip `bacb3f78a5de3b72872d5a44d81b4c3f0c2bd18a` (merge #238). Item-7 attempt3 is already DONE VALID on this tip (7-C1+B1+E1 @ `91369e1`, merge #237). No coding PR for item-7. This tip is unblocked. This prompts file does not start the `agy` by itself.

**Hard lock:** Implementation is **Antigravity-only on Z13**. Pilot holds one `agy` until this file tip-matches on main, then owns one `agy`. Do not use Grok Build or Cursor for the handoff into code. Prefer worktree `C:\Dev\cadcam-mvp` if Pilot says otherwise; do not invent a new path or create folders from this brief. Do not commit from Antigravity; Pilot/Repo Keeper commit path owns that. Do not invent Erik specs. Stay in `web/` (JS, HTML, CSS). No kernel, C++, `src/`, bindings, or wasm rebuild. Do not edit `UPDATES.md` or a root `PROGRESS.md`.

**Source of truth:**

- Chief (3T Chief - CAD CAM MVP · DEV), after Dig pack + Doc second, locked second-priority piece **(3) YES**: off-bar menus **float + draggable + explicit X/close top-right**. Snap / persist / z-order = **TBD** (out of this tip).
- Tip `bacb3f7` `web/index.html` (read from that commit; do not invent ids):
  - `#fileMenu` (`.menu`, `role="menu"`, `aria-label="File"`), opened by `#fileBtn` / `data-action="fileMenu"`, inside `.menu-wrap`.
  - `#exportMenu` (`.menu`, `role="menu"`, `aria-label="Export"`), opened by `#exportBtn` / `data-action="exportMenu"`, inside `.export-wrap` (`position: relative`).
  - `#createMenu` (`.create-menu`, `role="menu"`, `aria-label="Create"`). Openers: `#createDesktop` and the tools-sheet Create button, both `data-action="createMenu"`.
  - About chrome: `.menu-wrap` > button `data-action="aboutMenu"` (`aria-label="Info"`) and a `.menu` with `role="region"` `aria-label="About"`. That `.menu` has **no id** on this tip. Do not invent one. The inspector block `#inspector [aria-label="About"]` is a `.prop`, not a `.menu`. It is not an off-bar menu for this brief.
  - `.menu` is `position: absolute; top: calc(100% + 4px); left: 0` (anchored dropdown). `#createMenu` is already `position: fixed`. `placeCreateMenu()` writes inline `left` / `top` / `right` / `bottom` / `width` from the visible opener, and on the narrow layout clears those inline styles.
  - `closePopups()` sets `#fileMenu` hidden and `#fileBtn` `aria-expanded="false"`, hides `#exportMenu` when present, hides `#searchDlg`, calls `setToolsOpen(false)`, `setAboutOpen(false)`, and `closeCreateMenu()`, and hides `#pickChooser`. It does not, on this tip, set `#exportBtn` `aria-expanded`.
  - `runAction` calls `closePopups()` unless `action` is `fileMenu`, `exportMenu`, `search`, `toolsMenu`, `selectionShelf`, `cameraShelf`, the view-bar toggle, `createMenu`, `loadProject`, `pickFilter`, `aboutMenu`, or `theme`. `closeSheet` is **not** in that exclusion list, so a `data-action="closeSheet"` control already runs `closePopups()` and then the `action === 'closeSheet'` branch (`setToolsOpen(false); return`).
  - Outside click already ignores `.menu-wrap`, `.export-wrap`, `.search-dlg`, `.sheet`, `.create-menu`, `.pick-chooser`, and `#sketchSheet` (`closest` at the pointer path). Do not replace that list.
- Float-dock already on tip (PR #204 / `setupFloatingPanelDock()`):
  - `floatPanels` = `#sketchSheet, #edgeSheet, #toolsSheet, .vp-bar, #searchDlg, #browser, #inspector`.
  - Pointer drag on the panel. `onPanelPointerDown` returns early for `input, textarea, select, a, label.menu-file`. Movement past existing `tapSlopPx()` drags. `applyPanelPosition` docks `left` when `rawLeft <= 0`, `right` when `rawLeft >= maxLeft`, otherwise `float`. `position: fixed` is set only for `#browser` and `#inspector`. `floatingPanelStates()` publishes `panelDockState` for the gate.
  - Those selectors do **not** include `#fileMenu`, `#exportMenu`, `#createMenu`, or the About `.menu`. That gap is this brief.
- Close control already on tip, `#toolsSheet` header `.sheet-h`:
  - `button.icon-btn` with `data-action="closeSheet"`, `data-tool="Close tools menu"`, `aria-label="Close"`, and `<span>Close</span>`.
  - `.sheet-h` is `display: flex; gap: 8px; align-items: center`. `.sheet-h .icon-btn` sets `background: var(--panel-2)`. `.icon-btn` is already `min-width` / `min-height` / `height: 44px`.
- Tappable chrome floor already in the tree: **≥44 CSS px**. `.menu button` and `.create-menu button` already use that floor. Do not invent a new px threshold.
- Dig pack `research/gui/second-priority-toolbar-float-sketch-plane-2026-10-27.md` is **not** on tip `bacb3f7`. External research label only (do not invent file contents). The only §3 summary this brief carries: pattern OK for float + drag + explicit dismiss; CAUTION locking an X corner (Modo pin upper-right is the sourced “upper right” prose); GAP snap / persist / z-order.

Anything these locks do not state stays **TBD**.

## Goal
In `web/` only, make the off-bar menus float, drag, and close. No kernel, C++, `src/`, bindings, or wasm rebuild.

Menus in this brief (the full set on tip — do not add others):

1. `#fileMenu`
2. `#exportMenu`
3. `#createMenu`
4. The About `.menu` inside `.menu-wrap` (`aria-label="About"`, no id). Do not invent an id.

`#pickChooser` (`class="pick-chooser"`, `role="menu"`) is not `.menu` or `.create-menu`. Do not retarget it.

Locked behavior:

1. **Float.** Once opened, each menu above is a panel over the viewport, not stuck only as the anchored `.menu` dropdown (`position: absolute` under the opener) or only as the `placeCreateMenu()` anchor. Reuse the positioning the dock path already applies. `applyPanelPosition` already sets `position: fixed` for `#browser` and `#inspector`. Reuse that existing `fixed` assignment for these menus so they can leave `.menu-wrap` / `.export-wrap` / the create anchor. Do not invent a new positioning scheme, a new offset, or a new px value. Existing `.menu` `top: calc(100% + 4px)` stays the pre-drag anchor rule; do not add another number.
2. **Drag.** Extend the existing `setupFloatingPanelDock()` `floatPanels` list (or the same pointer handlers) to include these menus. Do not add a second drag system. Do not invent a tear-off affordance id. Drag-from-chrome is the existing panel `pointerdown` path; mirror that. Keep the existing early-return for `input, textarea, select, a, label.menu-file`, and keep `tapSlopPx()` as the move threshold. `#fileMenu` contains `label.menu-file` (Load); that early-return stays.
3. **Explicit Close, top-right of the menu chrome.** Reuse the `#toolsSheet` control: `button.icon-btn`, `data-action="closeSheet"`, `aria-label="Close"`, child `<span>Close</span>`, inside a `.sheet-h` row at the top of the menu (the tools header puts this button after `h2.panel-h`). Do not invent an SVG or other glyph. Do not copy `data-tool="Close tools menu"` onto File, Export, Create, or About. Do not invent a replacement `data-tool` string. Do not invent a heading where the menu has none. Do not invent a margin, inset, or corner coordinate. Dig’s CAUTION stands: do not add a separate X-corner lock. `.sheet-h` has no far-edge pin rule on this tip; do not add one.
4. **Dismiss** through the existing path. `data-action="closeSheet"` already calls `closePopups()` (it is not excluded) and then `setToolsOpen(false)`. That is the wire. Do not add a new action name or a parallel dismiss function. Do not remove these menus from the existing outside-click `closest` list.

Unchanged:

- Existing float-dock on `#sketchSheet`, `#edgeSheet`, `#toolsSheet`, `.vp-bar`, `#searchDlg`, `#browser`, `#inspector` keeps working, including edge dock left / right and mid = float.
- Phone tappable chrome stays **≥44 CSS px**. The reused `.icon-btn` already meets that floor. Do not add a px size.

## Workflow
1. Read the locks above. Copy behavior from those locks only.
2. Register `#fileMenu`, `#exportMenu`, `#createMenu`, and the About `.menu` (`.menu-wrap .menu[aria-label="About"]`) on the existing `setupFloatingPanelDock()` list. Do not register `#pickChooser` or `#inspector [aria-label="About"]`.
3. When a registered menu is open, let `applyPanelPosition` move it. Reuse the existing `position: fixed` assignment so `#fileMenu`, `#exportMenu`, and the About `.menu` are not left `position: absolute` inside the bar. `#createMenu` is already `position: fixed`. Do not add a third placer beside `placeCreateMenu()` and `applyPanelPosition`. Open-time placement may still run; drag after open uses the dock path. Do not invent session persist to reconcile them.
4. Add the reused Close control in a `.sheet-h` row at the top of each of those four menus. Dismiss stays `data-action="closeSheet"` → existing `closePopups()` / `setToolsOpen(false)`.
5. Where a detail is **TBD**, leave it TBD.
6. Do not regress the panels already in `floatPanels`.

## Do not bake / TBD
Do not invent and do not bake any of the following. Park TBDs stay **TBD**, verbatim:

- Snap grid, or any snap beyond the edge dock `applyPanelPosition` already implements (`left` / `right` / `float`)
- Persist XY across sessions
- Z-order stacking rules (do not invent a new `z-index`; `.menu` is `30` and `.create-menu` is `40` on this tip — leave them)
- A corner coordinate or pin mode for the Close control
- New hotkeys
- New hex colors
- New px sizes or a new tap threshold (keep `tapSlopPx()` and the 44 CSS px floor already on `.icon-btn` / `.menu button` / `.create-menu button`)
- New control ids, new action names, new classes, new icon glyphs
- A tear-off affordance id
- A second drag system
- `data-tool` text other than the existing `#toolsSheet` value `Close tools menu`, which stays on that sheet’s button only
- Plane-pick toggle
- Menu-bar shrink, overflow, or collapse

## Out of scope
- (1) Sketch plane-pick toggle. HOLD. Not this tip.
- (2) Numeric few-px shrink of the menu bar. LOCK NO. The ≥44 CSS px phone floor stays. Optional overflow / collapse is omitted.
- Item-7 / flesh / brightness / `#modifyShelf` Delete-in-sketch. Item-7 attempt3 already matches 7-C1+B1+E1 @ `91369e1`. Gaps stay flag-only elsewhere. Do not code them from this brief.
- Theme / Modo tokens / Rust HOLD.
- `#pickChooser` and the inspector `.prop` About region.
- `UPDATES.md` / root `PROGRESS.md` edits from this brief.
- Kernel / C++ / wasm rebuild. Do not commit `.wasm`, `web/cadcam.wasm`, or `web/dist/`.

## Smoke
Manual wake smoke. No new smoke harness. Reuse `tests/deploy_smoke.py` only if that reuse is clearly required; this brief does not require it. No invented pixel asserts. Because no smoke path is added here, do not print a done marker.

Check locked behavior only:

1. Opening `#fileMenu`, `#exportMenu`, and `#createMenu` yields a panel that can float and be dragged with the existing dock/float machinery (the `floatPanels` extension).
2. The About `.menu` (no id) does the same.
3. Each of those floating menus shows a Close control in the top header row (`.sheet-h` + `.icon-btn` + `aria-label="Close"` + `<span>Close</span>`) that dismisses through `closePopups()` / the existing `closeSheet` branch.
4. `#sketchSheet`, `#edgeSheet`, `#toolsSheet`, `.vp-bar`, `#searchDlg`, `#browser`, and `#inspector` still float and dock as before.
5. Snap grid, persist, and z-order are not implemented (**TBD**).
6. No plane-pick toggle, no menu-bar shrink, no overflow/collapse, no new ids, px, hex, or hotkeys.

## Success Criteria
Must PASS at tip-match. Cite Chief lock piece (3) and tip `bacb3f78a5de3b72872d5a44d81b4c3f0c2bd18a` `web/index.html`. Only locked behavior is on this bar.

1. `#fileMenu`, `#exportMenu`, and `#createMenu` open as panels that float and drag via `setupFloatingPanelDock` / `applyPanelPosition` (extended registration). Not stuck only as the anchored dropdown or only as the `placeCreateMenu()` anchor.
2. The About `.menu` inside `.menu-wrap` is in that same set. No invented id.
3. Each of those menus shows the reused Close control (`icon-btn`, `data-action="closeSheet"`, `aria-label="Close"`, `<span>Close</span>`) in a top `.sheet-h` row, and that control dismisses through existing `closePopups()` / `action === 'closeSheet'`.
4. Existing float-dock panels still dock left / right and float in the middle. No regression.
5. Snap / persist / z-order stay **TBD**.
6. No plane-pick toggle, no few-px shrink, no overflow/collapse, no invented ids, px, hex, hotkeys, glyphs, or a second drag system.
7. Tappable chrome stays ≥44 CSS px. No new px threshold.

Outside this hard bar: snap grid, persist, z-order, corner pin, plane-pick, menu-bar shrink, overflow/collapse, item-7, theme, Rust, `UPDATES.md`, `PROGRESS.md`, and `research/`.

## Done
Draft until tip-match. Dig tip-match is COMMENT-only. Repo Keeper undrafts and plain-merges. Author does not self-APPROVE. Doc does not edit `UPDATES.md`. After this file is on main, Pilot runs one Antigravity-only `agy` from it. Report the prompt PR link and tip SHA. Pilot reports any implementation PR separately.
