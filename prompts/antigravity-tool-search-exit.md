# Antigravity Tool Search exit

How the user exits Tool Search. Exits already on tip `e805614` stay as they are. This file is the Antigravity feed. It does not change the app by itself.

**Gate:** Tool Search exit **code** starts only after this file tip-matches on main. Base is main merge `#206` @ `e805614` (theme tip `9b758b4`). Pilot holds the next `agy` until overnight items 1 and 2 both tip-match. This prompts file does not start the `agy` by itself. Do not re-spec `#206`.

**Hard lock:** Implementation is **Antigravity-only on Z13**. Pilot holds one `agy` until this file tip-matches on main, then owns one `agy`. Do not use Grok Build or Cursor for the handoff into code. Prefer a worktree under `C:\Dev\`; do not invent a new path or create folders from this brief. Do not commit from Antigravity; Pilot/Repo Keeper commit path owns that. Do not invent Erik specs. Stay in `web/` (JS, HTML, CSS). No kernel, C++, `src/`, bindings, or wasm rebuild.

**Source of truth:**

- Erik overnight ~11:55 PM MT 2026-10-26, item **(1) Tool Search exit**, via Chief. Team decides. Invent-free scan and the content draft are Dig’s.
- `research/overnight-tool-search-exit.md` (Dig, 2026-10-27 ~12:24 AM MT), scanned at tip `e805614`. Cite that digest. Anything it marks **TBD** stays **TBD**.
- Tip `e805614` `web/index.html` and `tests/deploy_smoke.py` `SEARCH_DISCLOSURE_EXPR`. Quote only the facts below.
- `prompts/p4-tool-shelf-show-hide.md`: Escape and outside click are the existing disclosure pattern (`CREATE_MENU_EXPR` / `SEARCH_DISCLOSURE_EXPR`).
- UPDATES (2026-10-21): ui-redesign locked “keys 1 to 4 plus **X for tool search** (untested)”. That line is the open hotkey. It does not specify an exit path.
- Always-visible chrome / panel labels (`prompts/antigravity-panel-labels-chrome.md`, #191 / #193): Tool Search is show/hide. It is not permanent chrome.
- Park bullet **Tool Search exit** in `mvp/requirements.md` (this docs PR). Dig left “requirements park vs brief-only” **TBD**. This brief does not close that TBD.

Sourced CAD patterns in the digest are patterns only. They are not locks.

- Onshape Search Tools (https://cad.onshape.com/help/Content/Home/search_tools.htm): close the Search tools dialog with the dialog close control or Escape. The dialog also closes when a toolbar tool is selected. Mobile: tap Cancel to remove the search bar. Clear a typed query with **x** in the field (clear is not close).
- Shapr3D Accessing tools (https://support.shapr3d.com/hc/en-us/articles/7378907587484-Accessing-tools): Command Search opens via **`X`** or Ctrl/Cmd+F / toolbar / help. The fetched page does not spell Escape or close affordances. Shapr close details stay **TBD**.
- Fusion: the official shortcuts table lists Model Toolbox = **S** (https://help.autodesk.com/view/fusion360/ENU/?guid=GUID-F0491540-0324-470A-B651-2238D0EFAC30). A blog describes typing plus Enter/Space to invoke (https://www.autodesk.com/products/fusion-360/blog/new-ways-to-access-commands-in-fusion-360/). Escape-to-dismiss for Fusion Command Search is not confirmed from those pages. Fusion Escape stays **TBD**.

## Goal
Preserve the Tool Search exits already on tip `e805614`. Close an Erik-stated gap only after Erik or Chief locks that gap. Until then, do not add a close control, do not change `X` into a toggle, and do not invent phone Cancel copy.

Working exits (Dig scan of `web/index.html` at `e805614`):

1. Press `#searchBtn` again. `toggleSearch()` opens when the dialog is hidden, and otherwise calls `closeSearch(true)`.
2. Escape. `keydown` Escape calls `closePopups()`, which sets `searchDlg.hidden = true` and `#searchBtn` `aria-expanded="false"`, and restores focus to `#searchBtn` when search was open. The same key also collapses Modify, selection, camera, dim and prop sheet flags, the basic-shape `#hudSize` collapse, and drawers. That broader close is the current path.
3. Outside click. When the click is not on a `[data-tool]` control and not inside `.menu-wrap, .export-wrap, .search-dlg, .sheet, .create-menu, .pick-chooser, #sketchSheet`, the listener calls `closePopups()`, and focus returns to `#searchBtn` when search was open.
4. Pick a result. `pickCatalogItem` calls `closePopups()` and then `runAction`.
5. Open the Tools menu. `openToolsMenu()` calls `closeSearch(false)`.

Markup on that tip:

- `#searchBtn` — `data-action="search"`, `data-tool="Tool search"`, `title="Tool search (X)"`, `aria-label="Tool search"`, `aria-expanded`, `aria-controls="searchDlg"`.
- `#searchDlg` — `role="dialog"` `aria-label="Tool search"`. Children: `<h2 class="panel-h">Tool search</h2>`, `#searchInput` placeholder `"Search tools"`, `#searchList`. No Close, Cancel, or X control inside the dialog.
- Hotkey `X` / `x` calls `openSearchDialog()` only and toasts `"Tool search"`. It does not toggle closed. Pressing `X` while search is open runs `openSearchDialog()` again (clears the input, focuses `#searchInput`).

`openSearchDialog()` closes the file menu, the export menu, the tools sheet, the create menu, and drawers, then clears the input and focuses `#searchInput`.

`SEARCH_DISCLOSURE_EXPR` already checks Escape, outside click, and the icon toggle: dialog hidden, `aria-expanded="false"`, `aria-controls`, a 44×44 `#searchBtn`, and the open dialog inside the visual viewport.

Where a line is **TBD**, leave it **TBD**. An Onshape-like in-dialog Cancel or close control is a separate lock. Do not bake it from this brief.

## Workflow
1. Read `research/overnight-tool-search-exit.md` and the facts above. Copy behavior from those sources only.
2. Keep Escape, outside click, the `#searchBtn` toggle, pick-to-close, and tools-menu-to-close.
3. Keep `SEARCH_DISCLOSURE_EXPR`. Do not weaken those checks.
4. Leave `X` / `x` as open-only: `openSearchDialog()` and toast `"Tool search"`.
5. Leave `#searchDlg` without an in-dialog Close, Cancel, or X control.
6. Leave Escape on the current path (`closePopups()` plus the other chrome that key already collapses). Do not retarget it to search only.
7. Where the digest marks a detail **TBD**, leave it **TBD**. Do not fill the gap with a guessed control, label, or scope.

Dig’s minimal slice — preserve the exits above and the existing smoke — is the whole coding bar until Erik or Chief locks something on the TBD list. This brief is not that lock for a new control.

## Do not bake / TBD
Do not invent and do not bake any of the following. They stay **TBD**:

- Whether `X` should toggle closed
- An in-dialog Close or Cancel control, and its label
- Escape scoped only to search, versus the current broad `closePopups` and shelf collapse
- Phone-specific Cancel copy or placement
- Phone versus desktop exit affordance beyond Escape, outside click, and `#searchBtn`
- Fusion Escape confirmation
- Shapr Command Search close details beyond the open shortcut
- Whether the requirements park is required or this brief alone is enough (the park bullet records the same TBD; it does not close it)
- Control ids, CSS, pixels, or icon art beyond existing `#searchBtn` and `#searchDlg`
- Any new hotkey
- Themes or Active chrome B
- Gesture maps

## Out of scope
- Overnight item 2 (switch tool/menu → hide prior tool UI). Separate brief: `prompts/antigravity-switch-hide-prior-tool-ui.md`.
- Themes / Active chrome B (`prompts/antigravity-theme-default-modo.md`, #206, theme tip `9b758b4`).
- iPad/Kiwi gesture maps (`prompts/antigravity-ipad-kiwi-gestures-float-dock.md`).
- Editing `research/overnight-tool-search-exit.md`, `mvp/requirements.md`, or `UPDATES.md` from the coding `agy`.
- Kernel / C++ / wasm rebuild. Do not commit `.wasm`, `web/cadcam.wasm`, or `web/dist/`. Do not edit a root `PROGRESS.md`.

## Smoke
Reuse `tests/deploy_smoke.py` `SEARCH_DISCLOSURE_EXPR`. No new smoke harness. No new pixel asserts. The 44×44 `#searchBtn` check already in that expression stays. Because no new smoke path is added here, do not print a done marker.

Check sourced behavior only. Do not assert an in-dialog Cancel, an `X` toggle, search-only Escape, phone Cancel copy, or any other TBD.

1. Escape collapses `#searchDlg` and sets `#searchBtn` `aria-expanded="false"` (existing smoke).
2. Outside click collapses the same way (existing smoke).
3. A second `#searchBtn` click collapses the dialog (existing smoke).
4. Picking a catalog item still closes Tool Search through `pickCatalogItem` → `closePopups()`. `SEARCH_DISCLOSURE_EXPR` does not assert that path. Do not add a new expression for it.
5. Opening the Tools menu still calls `closeSearch(false)`. Do not add a new expression for it.

## Success Criteria
Must PASS at tip-match. Cite Erik overnight item (1) ~11:55 PM MT 2026-10-26 via Chief; `research/overnight-tool-search-exit.md` (Dig, 2026-10-27 ~12:24 AM MT); tip `e805614` `web/index.html` and `SEARCH_DISCLOSURE_EXPR`. Only sourced, already-shipped behavior is on this bar.

1. The user can exit Tool Search with Escape. `#searchDlg` is hidden and `#searchBtn` `aria-expanded` is `"false"` (existing).
2. The user can exit with an outside click (existing; smoke).
3. The user can exit with the `#searchBtn` toggle (existing).
4. Picking a catalog item closes Tool Search (existing).
5. No invented in-dialog Cancel or Close, no invented `X` toggle, no theme or Active chrome B work, no kernel or wasm.

Outside this hard bar: whether `X` should toggle closed; an in-dialog Close or Cancel control and its label; Escape scoped only to search versus the current broad `closePopups`; phone-specific Cancel copy or placement; phone versus desktop extras; Fusion Escape confirmation; Shapr Command Search close details beyond the open shortcut; requirements park versus brief-only; control ids, CSS, pixels, or icon art beyond existing `#searchBtn` and `#searchDlg`; new hotkeys; overnight item 2; themes #206; gesture maps; `research/overnight-tool-search-exit.md`; `mvp/requirements.md`; `UPDATES.md`; kernel / C++ / wasm.

## Done
Draft until tip-match: Doc Steward primary (COMMENT), Research Digest second. Author does not self-APPROVE. Repo Keeper undrafts and plain-merges. After this file is on main, Pilot runs one Antigravity-only `agy` from it. Pilot holds that `agy` until overnight items 1 and 2 have both tip-matched. This brief does not lock which item’s `agy` runs first. Report the prompt PR link and tip SHA. Pilot reports any implementation PR separately.
