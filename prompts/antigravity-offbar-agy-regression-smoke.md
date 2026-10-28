# Antigravity off-bar menus — slice 3 — regression smoke

Slice 3 of the Chief 3-way merge train. Verify-only against the combined lock, after slices 1 and 2 are on main. A tiny fix is allowed only when a locked check regresses. This file is the Antigravity feed for slice 3. It does not change the app by itself.

**Gate:** Antigravity-only on Z13. Do not start until slice 1 (`prompts/antigravity-offbar-agy-float-register.md`) and slice 2 (`prompts/antigravity-offbar-agy-close-chrome.md`) have both merged to main. Pilot holds until this file tip-matches on main, then launches **this slice only**, and only after slices 1 and 2 are on main. Chief authorizes multi-agy only after all three float files tip-match. Merge order is 1 before 2 before 3. This prompts file does not start the `agy` by itself.

**Hard lock:** Implementation is **Antigravity-only on Z13**. Do not use Grok Build or Cursor for the handoff into code. Prefer worktree `C:\Dev\cadcam-mvp` if Pilot says otherwise; do not invent a new path or create folders from this brief. Do not commit from Antigravity; Pilot/Repo Keeper commit path owns that. Do not invent Erik specs. Stay in `web/` (JS, HTML, CSS) and only if a tiny fix is required. No kernel, C++, `src/`, bindings, or wasm rebuild. Do not edit `UPDATES.md` or a root `PROGRESS.md`. Do not edit this prompt, the monolith, or the other slice files from the `agy`. Preferred result is **no code change**.

**Source of truth:**

- Chief FINAL LOCK (DEV Chief, 2026-10-27 ~6:45 PM MT): float is a **3-way** merge train. This file is slice **3** (verify-only / tiny fix).
- Combined lock, left in place: `prompts/antigravity-offbar-menus-float-drag-close.md`. Its Smoke and Success Criteria are the check list, narrowed to what slices 1 and 2 were allowed to land. Do not contradict that file. Do not delete it.
- Authoring tip `5ee57eee269f4f49429d17d150faeaf7b88584f8` (`5ee57ee`, main after #240) is the pre-slice fact base. Verify against main **after** slices 1 and 2 have merged, not against this authoring tip alone. If either slice is missing, stop and report. Do not implement slice 1 or slice 2 from this file.
- Checks that are locked (from the monolith Smoke / Success, split across slices 1 and 2):
  1. `#fileMenu`, `#exportMenu`, `#createMenu`, and the About `.menu` (`.menu-wrap .menu[aria-label="About"]`, no id) float and drag via `setupFloatingPanelDock` / `applyPanelPosition`.
  2. Each of those four shows Close (`.sheet-h` + `button.icon-btn` + `data-action="closeSheet"` + `aria-label="Close"` + `<span>Close</span>`) and that control dismisses through existing `closePopups()` / `action === 'closeSheet'` (`setToolsOpen(false)`).
  3. `data-tool="Close tools menu"` stays on `#toolsSheet` only.
  4. Existing `floatPanels` entries `#sketchSheet`, `#edgeSheet`, `#toolsSheet`, `.vp-bar`, `#searchDlg`, `#browser`, `#inspector` still float and dock (`left` / `right` / `float`).
  5. Outside-click ignore list stays `.menu-wrap, .export-wrap, .search-dlg, .sheet, .create-menu, .pick-chooser, #sketchSheet`.
  6. Early-return `input, textarea, select, a, label.menu-file` and `tapSlopPx()` stay.
  7. No new px, no new `z-index`, no new hotkeys. `.menu` stays `30`. `.create-menu` stays `40`.
  8. Snap grid, persist XY, and z-order stacking are **not** implemented.
- `#pickChooser` and `#inspector [aria-label="About"]` stay unregistered.

Anything these locks do not state stays **TBD**.

## Goal
Verify the locked float, drag, and Close behavior after slices 1 and 2. If a locked check fails, make the smallest edit that restores that check. Do not expand scope. No kernel, C++, `src/`, bindings, or wasm rebuild.

## Workflow
1. Confirm slices 1 and 2 are on main. If not, stop.
2. Walk the Smoke list below. Prefer no code change.
3. A tiny fix is allowed only when a check in Smoke fails against the locked behavior. The fix restores that check and nothing else.
4. If a check fails because slice 1 or slice 2 never landed, stop and report. Do not build the missing slice from this file.
5. Do not add a smoke harness. The monolith does not require one.

## Do not bake / TBD
Do not invent and do not bake any of the following. Park TBDs stay **TBD**, verbatim:

- Snap grid, or any snap beyond the edge dock `applyPanelPosition` already implements (`left` / `right` / `float`)
- Persist XY across sessions
- Z-order stacking rules or a new `z-index` (`.menu` `30`, `.create-menu` `40`)
- A new smoke harness, pixel assert, or done marker
- New hotkeys, hex colors, px sizes, control ids, action names, classes, or glyphs
- A second drag system
- Plane-pick toggle
- Menu-bar shrink, overflow, or collapse
- Scope that slices 1 and 2 left out

## Out of scope
- Implementing slice 1 or slice 2 when they are absent.
- Snap grid beyond the edge dock; persist XY; z-order / a new `z-index`.
- Shrink. Plane-pick. `#pickChooser`.
- Item-7 / flesh / brightness / `#modifyShelf` Delete-in-sketch.
- Theme / Modo tokens / Rust HOLD.
- `UPDATES.md` / root `PROGRESS.md` edits from this brief. Antigravity does not edit `UPDATES.md`.
- Kernel / C++ / wasm rebuild. Do not commit `.wasm`, `web/cadcam.wasm`, or `web/dist/`.

## Smoke
Manual wake smoke. No new smoke harness. Reuse `tests/deploy_smoke.py` only if that reuse is clearly required; the monolith does not require it, and this slice does not either. No invented pixel asserts. Because no smoke path is added here, do not print a done marker.

Verify:

1. `#fileMenu`, `#exportMenu`, `#createMenu`, and the About `.menu` (no id) float and drag with the existing dock/float machinery.
2. Each of those four shows Close (`.sheet-h` + `.icon-btn` + `aria-label="Close"` + `<span>Close</span>`) and Close dismisses through `closePopups()` / the existing `closeSheet` branch.
3. `#sketchSheet`, `#edgeSheet`, `#toolsSheet`, `.vp-bar`, `#searchDlg`, `#browser`, and `#inspector` still float and dock as before.
4. The outside-click ignore list is unchanged.
5. No new px, `z-index`, or hotkeys.
6. Snap grid, persist, and z-order are not implemented (**TBD**).
7. No plane-pick toggle, no menu-bar shrink, no overflow/collapse, no new ids.

## Success Criteria
Must PASS at tip-match. Cite Chief FINAL LOCK 3-way slice 3, the monolith Smoke / Success, and slices 1 and 2. Authoring tip for the pre-slice facts is `5ee57eee269f4f49429d17d150faeaf7b88584f8`.

1. The four menus float and drag. Close dismisses. Existing `floatPanels` panels still work.
2. Outside-click ignore list unchanged. No new px, z, or hotkeys.
3. Snap / persist / z-order are not implemented.
4. Any code change is a tiny restoration of a failed check above. No scope expansion.
5. No new smoke harness.
6. No plane-pick, no shrink, no `#pickChooser` registration, no invented ids.

Outside this hard bar: snap grid, persist, z-order, corner pin, plane-pick, menu-bar shrink, overflow/collapse, item-7, theme, Rust, `UPDATES.md`, `PROGRESS.md`, and `research/`.

## Done
Draft until tip-match. Dig tip-match is COMMENT-only. Doc Steward is second. Repo Keeper undrafts and plain-merges. Author does not self-APPROVE. Doc does not edit `UPDATES.md`. Pilot runs multi-agy only after Chief authorizes it, and only after all three float files tip-match. Merge order is 1 → 2 → 3. This file is slice 3; do not launch it before slices 1 and 2 are on main. Report the prompt PR link and tip SHA. Pilot reports any implementation PR separately. A verify-only pass with no code change meets this slice.
