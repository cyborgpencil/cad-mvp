# Antigravity off-bar menus — slice 2 — Close chrome

Slice 2 of the Chief 3-way merge train. After slice 1 is on main, add the reused Tools Close control to the four floating menus. This file is the Antigravity feed for slice 2. It does not change the app by itself.

**Gate:** Antigravity-only on Z13. Do not start until slice 1 (`prompts/antigravity-offbar-agy-float-register.md`) has merged to main and the four menus are already in `floatPanels`. Pilot holds until this file tip-matches on main, then launches **this slice only**, and only after slice 1 is on main. Chief authorizes multi-agy only after all three float files tip-match. Merge order is 1 before 2 before 3. This prompts file does not start the `agy` by itself.

**Hard lock:** Implementation is **Antigravity-only on Z13**. Do not use Grok Build or Cursor for the handoff into code. Prefer worktree `C:\Dev\cadcam-mvp` if Pilot says otherwise; do not invent a new path or create folders from this brief. Do not commit from Antigravity; Pilot/Repo Keeper commit path owns that. Do not invent Erik specs. Stay in `web/` (JS, HTML, CSS). No kernel, C++, `src/`, bindings, or wasm rebuild. Do not edit `UPDATES.md` or a root `PROGRESS.md`. Do not edit this prompt, the monolith, or the other slice files from the `agy`.

**Source of truth:**

- Chief FINAL LOCK (DEV Chief, 2026-10-27 ~6:45 PM MT): float is a **3-way** merge train. This file is slice **2** (Close chrome). It depends on slice 1 merged.
- Combined lock, left in place: `prompts/antigravity-offbar-menus-float-drag-close.md`. Do not contradict it. Do not delete it. Slice 1 owns registration. This slice owns Close only.
- Authoring tip `5ee57eee269f4f49429d17d150faeaf7b88584f8` (`5ee57ee`, main after #240) is the fact base below. On that tip the four menus are **not** yet in `floatPanels`. After slice 1 merges, they are. Do not re-register them here. If slice 1 is not on the tree you are editing, stop.
- Menus (the full set — do not add others):
  1. `#fileMenu` (`.menu`, `role="menu"`, `aria-label="File"`). No heading on the authoring tip.
  2. `#exportMenu` (`.menu`, `role="menu"`, `aria-label="Export"`). No heading on the authoring tip.
  3. `#createMenu` (`.create-menu`, `role="menu"`, `aria-label="Create"`). No heading on the authoring tip.
  4. About `.menu` inside `.menu-wrap` (`role="region"`, `aria-label="About"`, no id). It already has `<h2 class="panel-h">About</h2>`. Do not invent an id. `#inspector [aria-label="About"]` is a `.prop`. It is not this menu.
- Close control already on the authoring tip, `#toolsSheet` header `.sheet-h`:
  - `button.icon-btn` with `data-action="closeSheet"`, `data-tool="Close tools menu"`, `aria-label="Close"`, and `<span>Close</span>`.
  - The tools header puts that button after `h2.panel-h`.
  - `.sheet-h` is `display: flex; gap: 8px; align-items: center`. `.sheet-h .icon-btn` sets `background: var(--panel-2)`. `.icon-btn` is already `min-width` / `min-height` / `height: 44px`.
- Dismiss already on the authoring tip: `runAction` calls `closePopups()` unless `action` is `fileMenu`, `exportMenu`, `search`, `toolsMenu`, `selectionShelf`, `cameraShelf`, the view-bar toggle, `createMenu`, `loadProject`, `pickFilter`, `aboutMenu`, or `theme`. `closeSheet` is **not** in that exclusion list, so a `data-action="closeSheet"` control already runs `closePopups()` and then the `action === 'closeSheet'` branch (`setToolsOpen(false); return`).
- `closePopups()` sets `#fileMenu` hidden and `#fileBtn` `aria-expanded="false"`, hides `#exportMenu` when present, hides `#searchDlg`, calls `setToolsOpen(false)`, `setAboutOpen(false)`, and `closeCreateMenu()`, and hides `#pickChooser`. Do not replace it.
- Outside click already ignores `.menu-wrap`, `.export-wrap`, `.search-dlg`, `.sheet`, `.create-menu`, `.pick-chooser`, and `#sketchSheet`. Do not replace that list.
- `.menu` `z-index` is `30`. `.create-menu` `z-index` is `40`. Leave both.

Anything these locks do not state stays **TBD**.

## Goal
In `web/` only, add the reused `#toolsSheet` Close control to each of the four menus that slice 1 already registered. Dismiss stays on the existing `closeSheet` path. No kernel, C++, `src/`, bindings, or wasm rebuild.

Locked behavior for this slice:

1. **Explicit Close on each of the four menus.** Reuse the `#toolsSheet` control: `button.icon-btn`, `data-action="closeSheet"`, `aria-label="Close"`, child `<span>Close</span>`, inside a `.sheet-h` row at the top of the menu. Do not copy `data-tool="Close tools menu"` onto File, Export, Create, or About. Do not invent a replacement `data-tool` string. Do not invent an SVG or other glyph. Do not invent a heading where the menu has none. About already has `h2.panel-h`; that heading may sit in the `.sheet-h` row the way the Tools `h2.panel-h` does. Do not invent a second About heading. Do not invent a margin, inset, or corner coordinate. `.sheet-h` has no far-edge pin rule on the authoring tip; do not add one.
2. **Dismiss** through the existing path. `data-action="closeSheet"` already calls `closePopups()` (it is not excluded) and then `setToolsOpen(false)`. That is the wire. Do not add a new action name or a parallel dismiss function. Do not remove these menus from the existing outside-click `closest` list.

Unchanged:

- Slice 1 registration and drag stay. Do not add a drag system.
- Existing float-dock on `#sketchSheet`, `#edgeSheet`, `#toolsSheet`, `.vp-bar`, `#searchDlg`, `#browser`, `#inspector` keeps working.
- `#toolsSheet` keeps `data-tool="Close tools menu"` on its own Close button.
- Phone tappable chrome stays **≥44 CSS px**. The reused `.icon-btn` already meets that floor. Do not add a px size.

## Workflow
1. Confirm slice 1 is on the tree: `#fileMenu`, `#exportMenu`, `#createMenu`, and `.menu-wrap .menu[aria-label="About"]` are already in `setupFloatingPanelDock()` `floatPanels` (or the same pointer handlers). If they are not, stop.
2. Add the reused Close control in a `.sheet-h` row at the top of each of those four menus. Markup to copy, minus `data-tool`: `button.icon-btn` + `data-action="closeSheet"` + `aria-label="Close"` + `<span>Close</span>`.
3. Dismiss stays `data-action="closeSheet"` → existing `closePopups()` / `setToolsOpen(false)`. Do not add an action name.
4. Where a detail is **TBD**, leave it TBD.
5. Do not regress slice 1 float/drag or the panels that were already in `floatPanels` before slice 1.

## Do not bake / TBD
Do not invent and do not bake any of the following. Park TBDs stay **TBD**, verbatim:

- A new drag system, or a second registration pass over `floatPanels`
- Snap grid, or any snap beyond the edge dock `applyPanelPosition` already implements (`left` / `right` / `float`)
- Persist XY across sessions
- Z-order stacking rules (do not invent a new `z-index`; `.menu` is `30` and `.create-menu` is `40` — leave them)
- A corner coordinate or pin mode for the Close control
- An SVG, glyph, or other icon on the Close control
- `data-tool="Close tools menu"` on File, Export, Create, or About (that string stays on the `#toolsSheet` button only)
- A replacement `data-tool` string
- A heading on File, Export, or Create
- New hotkeys
- New hex colors
- New px sizes or a new tap threshold (keep `tapSlopPx()` and the 44 CSS px floor already on `.icon-btn` / `.menu button` / `.create-menu button`)
- New control ids, new action names, new classes
- A new smoke harness
- Plane-pick toggle
- Menu-bar shrink, overflow, or collapse

## Out of scope
- Slice 1 registration (already required on main) and slice 3 verify. Do not re-implement slice 1 from this file.
- Snap grid beyond the edge dock; persist XY; z-order / a new `z-index`.
- Shrink. Plane-pick. `#pickChooser`. `#inspector [aria-label="About"]`.
- Item-7 / flesh / brightness / `#modifyShelf` Delete-in-sketch.
- Theme / Modo tokens / Rust HOLD.
- `UPDATES.md` / root `PROGRESS.md` edits from this brief.
- Kernel / C++ / wasm rebuild. Do not commit `.wasm`, `web/cadcam.wasm`, or `web/dist/`.

## Smoke
Manual wake smoke. No new smoke harness. Reuse `tests/deploy_smoke.py` only if that reuse is clearly required; this brief does not require it. No invented pixel asserts. Because no smoke path is added here, do not print a done marker.

Check locked behavior for this slice only:

1. Each of `#fileMenu`, `#exportMenu`, `#createMenu`, and the About `.menu` (no id) shows a Close control in the top header row (`.sheet-h` + `.icon-btn` + `aria-label="Close"` + `<span>Close</span>`).
2. That control dismisses through `closePopups()` / the existing `closeSheet` branch (`setToolsOpen(false)`).
3. File, Export, Create, and About do not carry `data-tool="Close tools menu"`. `#toolsSheet` still does.
4. The four menus still float and drag from slice 1. `#sketchSheet`, `#edgeSheet`, `#toolsSheet`, `.vp-bar`, `#searchDlg`, `#browser`, and `#inspector` still float and dock as before.
5. The outside-click ignore list is unchanged.
6. Snap grid, persist, and z-order are not implemented (**TBD**).
7. No plane-pick toggle, no menu-bar shrink, no overflow/collapse, no new ids, px, hex, hotkeys, or glyphs.

## Success Criteria
Must PASS at tip-match. Cite Chief FINAL LOCK 3-way slice 2, the monolith `prompts/antigravity-offbar-menus-float-drag-close.md`, slice 1, and authoring tip `5ee57eee269f4f49429d17d150faeaf7b88584f8` `web/index.html` for the Close control that was copied. Only locked behavior is on this bar.

1. Slice 1 is already on main. This slice does not re-do registration.
2. Each of the four menus shows the reused Close control (`icon-btn`, `data-action="closeSheet"`, `aria-label="Close"`, `<span>Close</span>`) in a top `.sheet-h` row.
3. That control dismisses through existing `closePopups()` / `action === 'closeSheet'`. No new action name.
4. `data-tool="Close tools menu"` stays on `#toolsSheet` only.
5. No invented SVG, glyph, heading (except the About `h2.panel-h` already on the tip), id, or corner pin.
6. Existing float-dock panels, including the four menus, still dock left / right and float in the middle. No regression.
7. Snap / persist / z-order stay **TBD**. `.menu` stays `30`. `.create-menu` stays `40`.
8. No plane-pick toggle, no few-px shrink, no overflow/collapse, no invented ids, px, hex, hotkeys, or a second drag system.
9. Tappable chrome stays ≥44 CSS px. No new px threshold.

Outside this hard bar: snap grid, persist, z-order, corner pin, plane-pick, menu-bar shrink, overflow/collapse, item-7, theme, Rust, `UPDATES.md`, `PROGRESS.md`, and `research/`.

## Done
Draft until tip-match. Dig tip-match is COMMENT-only. Doc Steward is second. Repo Keeper undrafts and plain-merges. Author does not self-APPROVE. Doc does not edit `UPDATES.md`. Pilot runs multi-agy only after Chief authorizes it, and only after all three float files tip-match. Merge order is 1 → 2 → 3. This file is slice 2; do not launch it before slice 1 is on main. Report the prompt PR link and tip SHA. Pilot reports any implementation PR separately.
