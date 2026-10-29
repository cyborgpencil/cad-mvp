# Tool Search exit — invent-free digest (overnight item 1)

Status: invent-free digest (MVP Research Digest). Compiled **2026-10-27 ~12:24 AM MT** (America/Denver). **Superseded by #255 (`8e18de0`):** Tool Search chrome (`#searchBtn`, `#searchDlg`, `X` hotkey) was removed on main.
Antigravity feed: `prompts/antigravity-tool-search-exit.md`. This digest does not start an `agy`.

**Owner draft:** MVP Research Digest (content). Doc Steward primary tip for any `prompts/` PR.
**Date:** 2026-10-27 ~12:24 AM MT (America/Denver)
**Gate tip:** main merge `#206` @ `e805614` (theme tip `9b758b4`). Pilot holds next `agy` until overnight 1–2 tip-match.
**Scope:** How the user exits / closes Tool Search UI cleanly. UI chrome only. Watertight / units N/A (no export-path touch).
**Hard lock:** Invent-free. Do not invent gesture maps beyond Chief-locked maps. Active chrome B / themes stay out of scope unless they collide (they do not here).

---

## Source of truth (cite only these)

### App behavior on tip `e805614` / `web/index.html`

| Fact | Quote / location |
| --- | --- |
| Control | `#searchBtn` — `data-action="search"`, `data-tool="Tool search"`, `title="Tool search (X)"`, `aria-label="Tool search"`, `aria-expanded`, `aria-controls="searchDlg"` |
| Dialog | `#searchDlg` `role="dialog"` `aria-label="Tool search"` — children: `<h2 class="panel-h">Tool search</h2>`, `#searchInput` placeholder `"Search tools"`, `#searchList` |
| **No in-dialog Close / Cancel / X button** | Markup has only heading + input + list (no close control inside `#searchDlg`) |
| Toggle via button | `toggleSearch()` → open if hidden else `closeSearch(true)` |
| Hotkey `X` / `x` | Calls **`openSearchDialog()` only** (does **not** toggle closed). Toast `"Tool search"`. |
| Escape | `keydown` Escape → `closePopups()` (sets `searchDlg.hidden = true`, `aria-expanded="false"`) among other chrome closes; restores focus to `#searchBtn` if search was open |
| Outside click | Click outside `.search-dlg` (and listed chrome) → `closePopups()`; focus back to `#searchBtn` if search was open |
| Pick result | `pickCatalogItem` → `closePopups()` then `runAction` |
| Open side-effects | `openSearchDialog()` closes file/export menus, tools sheet, create menu, drawers; clears input; focuses `#searchInput` |
| Tools menu | `openToolsMenu()` calls `closeSearch(false)` |
| Smoke | `tests/deploy_smoke.py` `SEARCH_DISCLOSURE_EXPR`: Escape + outside click collapse, `aria-expanded` / `aria-controls`, 44×44 `#searchBtn`, dialog in visual viewport |

### Team docs already on main

- `prompts/p4-tool-shelf-show-hide.md`: Escape + outside click are the existing disclosure pattern to reuse (`CREATE_MENU_EXPR` / `SEARCH_DISCLOSURE_EXPR`).
- UPDATES (2026-10-21): ui-redesign locked “keys 1 to 4 plus **X for tool search** (untested)” — open hotkey only; exit path not specified there.
- Always-visible chrome / panel labels (`prompts/antigravity-panel-labels-chrome.md`, #191/#193): Tool Search is **not** permanent chrome; it is show/hide.

### Erik overnight queue

- Journal (Erik overnight ~11:55 PM MT 2026-10-26 via Chief): after `#206`, item **(1) Tool Search exit**. Team decides; invent-free scan + briefs owned by Dig.  
- **Gap:** as of tip `e805614`, `mvp/requirements.md` has **no** parked bullet named “Tool Search exit”. Doc may need a park line before / with the prompt PR. **TBD for Doc/Erik** whether this brief alone is enough or a requirements park is required.

### Sourced CAD / iPad patterns (patterns only — not locks)

| Source | Exit / dismiss behavior stated |
| --- | --- |
| Onshape Search Tools — https://cad.onshape.com/help/Content/Home/search_tools.htm | Close Search tools dialog with the dialog close control **or Escape**. Dialog also closes when a toolbar tool is selected. Mobile: tap **Cancel** to remove the search bar. Clear typed query with **x** in the field (clear ≠ close). |
| Shapr3D Accessing tools — https://support.shapr3d.com/hc/en-us/articles/7378907587484-Accessing-tools | Command Search via **`X`** or Ctrl/Cmd+F / toolbar / help (open path). Page does **not** spell Escape/close affordances in the fetched text — exit details **TBD** if we need Shapr-specific close. |
| Fusion Design Shortcuts / Command Search | Official shortcuts table lists **Model Toolbox = S** (https://help.autodesk.com/view/fusion360/ENU/?guid=GUID-F0491540-0324-470A-B651-2238D0EFAC30). Blog describes typing + Enter/Space to invoke (https://www.autodesk.com/products/fusion-360/blog/new-ways-to-access-commands-in-fusion-360/). **Escape-to-dismiss for Fusion Command Search is not confirmed from official pages fetched this turn** — leave Fusion Escape **TBD**, do not bake. |

---

## What exists today (issue scan, invent-free)

**Working exits already in code:**

1. Press `#searchBtn` again (`toggleSearch` → `closeSearch`).
2. Escape (via `closePopups`).
3. Outside click (via `closePopups`).
4. Pick a search result (`pickCatalogItem` → `closePopups`).
5. Opening Tools menu (`openToolsMenu` → `closeSearch`).

**Friction / gaps (do not invent fixes):**

1. Hotkey **`X` opens only** — pressing `X` again while open **re-opens / resets** search; it does not close. Toggle-close exists only on the button.
2. **No Cancel / Close control inside** `#searchDlg` (Onshape mobile Cancel / desktop close control are sourced patterns; whether we add one is **Erik/Chief TBD**).
3. Escape today also collapses Modify / selection / camera / dim / prop sheets / drawers — not search-only. Whether exit should be search-scoped is **TBD**.
4. Phone vs desktop exit affordance (beyond Escape / outside / button) is **TBD**.
5. No requirements park bullet yet for this overnight item.

---

## Recommended invent-free goal (for Doc → `prompts/`)

Keep behavior that already exists and is smoke-tested. Close any Erik-stated gap **only** after Erik/Chief lock. Until then, implementation must not invent a new close control, must not change `X` into a toggle, and must not invent phone Cancel copy.

**Minimal safe coding slice (only if Chief locks “keep existing exits; document + smoke”):**

- Preserve Escape, outside click, `#searchBtn` toggle, pick-to-close, tools-menu-to-close.
- Preserve `SEARCH_DISCLOSURE_EXPR` bar.
- Do **not** add in-dialog Close/Cancel unless Erik locks it.
- Do **not** make `X` toggle unless Erik locks it.
- Do **not** retarget Escape to search-only unless Erik locks it.

If Erik wants an Onshape-like in-dialog Cancel / close control, that is a **separate lock** — do not bake from this draft alone.

---

## Success Criteria (hard bar — tip-match)

Only sourced / already-shipped behavior:

1. User can exit Tool Search via **Escape**, with `#searchDlg` hidden and `#searchBtn` `aria-expanded="false"` (existing).
2. User can exit via **outside click** (existing; smoke).
3. User can exit via **`#searchBtn` toggle** (existing).
4. Picking a catalog item closes Tool Search (existing).
5. No invented in-dialog Cancel/Close, no invented `X`-toggle, no theme / Active chrome B work, no kernel / wasm.

Outside this bar (TBD — do not bake):

- Whether `X` should toggle closed
- In-dialog Close / Cancel control and its label
- Escape scoped only to search vs current broad `closePopups` / shelf collapse
- Phone-specific Cancel copy / placement
- Fusion Escape confirmation
- Shapr Command Search close details beyond open shortcut
- Park wording in `mvp/requirements.md`
- Control ids / CSS / pixels / icon art beyond existing `#searchBtn` / `#searchDlg`

## Out of scope

- Overnight item 2 (switch → hide prior tool UI) — separate brief.
- Themes / Active chrome B (`prompts/antigravity-theme-default-modo.md`, #206).
- iPad/Kiwi gesture map invents (`prompts/antigravity-ipad-kiwi-gestures-float-dock.md`).
- Kernel / C++ / wasm / `UPDATES.md` from the coding `agy`.

## Done / handoff

- Dig: this invent-free draft on box.  
- **Doc primary:** land `prompts/` brief PR (park in `mvp/requirements.md` if team pattern requires). Dig seconds tip.  
- Dig does **not** open the prompt PR unless Doc asks. Pilot holds `agy` until tip-match.
