# Switch tool/menu → hide prior tool UI — invent-free digest (overnight item 2)

Status: invent-free digest (MVP Research Digest). Compiled **2026-10-27 ~12:24 AM MT** (America/Denver).
Antigravity feed: `prompts/antigravity-switch-hide-prior-tool-ui.md`. This digest does not start an `agy`.

**Owner draft:** MVP Research Digest (content). Doc Steward primary tip for any `prompts/` PR.
**Date:** 2026-10-27 ~12:24 AM MT (America/Denver)
**Gate tip:** main merge `#206` @ `e805614` (theme tip `9b758b4`). Pilot holds next `agy` until overnight 1–2 tip-match.
**Scope:** When the user switches tools or opens another menu, prior tool UI / panels should hide. UI chrome only. Watertight / units N/A unless an export path is touched (it must not be).
**Hard lock:** Invent-free. Do not invent gesture maps. Active chrome B / themes out of scope unless they collide (they do not).

---

## Source of truth (cite only these)

### Erik / team locks already on main

| Lock | Source | Behavior already stated |
| --- | --- | --- |
| P4 tool-shelf show/hide | `prompts/p4-tool-shelf-show-hide.md` (merged #44/#54) | “A shelf opens only while that tool or edit is active. … **The only open shelf is the active tool's shelf.** Leaving the tool collapses it.” Cluttering shelves listed: Create (`#createMenu`), Modify (`#modifyShelf`), `#dimPanel` / property edit sheet, center `#hudSize` while editing basic shapes. Escape + outside click reuse. |
| Always-visible chrome | `mvp/requirements.md` park + `prompts/antigravity-panel-labels-chrome.md` (#167/#191/#193) | Only **very top** (tree + filename), **tools menu bar**, and **very bottom** (Modify / Create etc.) stay visible 100%. Everything else uses show/hide like other shelves. Mapping TBDs in that brief stay TBD. |
| Sketch chrome minimize | `mvp/requirements.md` park + shipped sketch chrome (#183/#186) | While sketching, minimize non-sketch chrome; top + bottom stay on (overhaul lock). |
| Create → ortho → tools | `mvp/requirements.md` / `prompts/antigravity-sketch-chrome-flow.md` | After plane pick, hide view-selection menu; show only sketch-create tools; keep Finish Sketch. |

### App behavior on tip `e805614` / `web/index.html` (partial mutual exclusion — invent-free)

**Already hides prior chrome in these paths:**

| Trigger | What closes (quoted from code paths) |
| --- | --- |
| Most `runAction` tools | `closePopups()` unless action is file/export/search/toolsMenu/selectionShelf/cameraShelf/createMenu/loadProject/pickFilter/aboutMenu/theme — closes search, tools sheet, create, file/export, about, pick chooser |
| Open Tools menu | `closeSearch`, drawers, file/export, create, selection shelf, camera shelf |
| Open Selection shelf | `closePopups`; closes camera shelf + Modify |
| Open Camera shelf | `closePopups`; closes selection shelf + Modify |
| Open About | `closePopups`; closes selection + camera + Modify |
| Open Create menu | `closePopups`; if sketch tab: `clearSketchGeometry` + `closeSketchSheet`; on open also `setModifyOpen(false)` and clears dim/prop sheet flags |
| Open Modify | `closeCreateMenu`; on open clears dim/prop sheet flags |
| Escape | Closes Modify, selection, camera, dim/prop flags, hudSize collapse when editing basic shape, `closePopups`, drawers |
| `#edgeSheet` | `paintEdgeChrome`: `sheet.hidden = !armed` where armed = `edgeArm === 'fillet' \|\| 'chamfer'` — hides when fillet/chamfer not armed |
| Leave sketch tab / Finish Sketch | `closeSketchSheet()` |
| `openSketchSheet(mode)` | Swaps row visibility inside `#sketchSheet` for the new mode (rect/circle/polygon/line/arc/extrude) |

**Not a single “hide all prior tool UI” gate:**

- Opening a new sketch tool (`sketchLine` / `sketchArc` / …) calls `openSketchSheet(...)` but does **not** universally call `setModifyOpen(false)` / clear `edgeArm` / close unrelated tool panels in one shared helper.
- `closePopups()` does **not** hide `#sketchSheet`, `#edgeSheet`, `#modifyShelf`, or `#dimPanel`.
- Whether every tool↔tool and tool↔menu pair must hide the previous tool’s panel is **Erik overnight intent** but **not** fully enumerated in `mvp/requirements.md` as of tip `e805614`.

### Erik overnight queue

- Journal (Erik overnight ~11:55 PM MT 2026-10-26): item **(2) switch tool/menu → hide prior tool UI**.  
- **Gap:** no dedicated park bullet with that exact name in `mvp/requirements.md` at tip `e805614`. Closest locks are P4 + always-visible chrome + sketch chrome. Doc may park a one-liner citing those. **TBD.**

### Sourced patterns (patterns only — not locks)

| Source | Relevant pattern |
| --- | --- |
| Onshape Search Tools — https://cad.onshape.com/help/Content/Home/search_tools.htm | Search dialog closes when a toolbar tool is selected. |
| Onshape Feature Basics / Dialogs — https://cad.onshape.com/help/Content/PartStudio/feature_basics.htm ; https://cad.onshape.com/help/Content/Home/dialogs.htm | Feature dialog Cancel / Escape closes that feature dialog; Enter commits. (Tool dialog lifecycle — pattern, not our control ids.) |
| Onshape Escape — https://cad.onshape.com/help/Content/Home/keyboard_shortcuts_and_hotkeys.htm | Escape “Exits the command in use”. |
| Shapr3D Accessing tools — https://support.shapr3d.com/hc/en-us/articles/7378907587484-Accessing-tools | Adaptive tools from selection; side menus float. Does **not** publish a universal “switch tool hides previous panel” matrix in the fetched page — do not invent one. |
| FreeCAD Task panel / workbench | Escape can exit Task panel (`General/TasksKeyEsc` in Fine-tuning wiki). FreeCAD #28852 notes task-panel visibility across workbench switches (OSS history) — **not** a lock for our WASM UI; cite only as “OSS apps treat active task UI as modal to the current command.” |
| Prior Dig box digest | `research/ipad-cad-kiwi-modo-gestures-panels.md` — float/dock + gesture maps; **do not** re-bake gesture invents here. |

---

## What exists today (issue scan, invent-free)

**Aligned with Erik intent (partial):**

- P4 + always-visible chrome already state the product rule: non-permanent panels show/hide; only one active tool shelf.
- Several menu openers already mutually exclude (selection ↔ camera ↔ modify; tools ↔ search; create closes modify / sketch sheet when opening).

**Gaps vs “switch tool/menu → hide previous tool UI” (flag, do not invent):**

1. **No single helper** that, on every tool arm or menu open, hides the previous tool’s UI panel set.
2. **Tool→tool** paths (e.g. fillet/chamfer `#edgeSheet` vs sketch `#sketchSheet` vs Modify shelf vs dim/prop) are not uniformly gated in one place — some hide via `paintEdgeChrome` / tab change / create open; others may leave prior UI up. Exact leftover pairs need a tip-time audit during coding, not invented here.
3. Which surfaces count as “prior tool UI” vs permanent chrome is still partly **TBD** under the always-visible chrome brief (region mapping TBD).
4. Whether opening Tool Search must hide `#sketchSheet` / `#edgeSheet` / Modify (today `openSearchDialog` closes tools/create/drawers/file/export, not those tool panels) is **TBD**. *(Superseded by #255 / `8e18de0` — Tool Search removed.)*
5. Themes / Active chrome B must not be reopened.

---

## Recommended invent-free goal (for Doc → `prompts/`)

Implement Erik’s overnight rule by **extending existing P4 / always-visible chrome / mutual-exclusion paths**, not by inventing a new chrome system.

**Allowed (once Doc brief tip-matches + Chief confirms no new TBD bake-ins):**

1. When user **arms a different tool** or **opens a different menu**, hide the prior tool’s non-permanent UI (shelves / tool sheets / search) using the existing show/hide mechanisms.
2. Keep permanent chrome per always-visible lock: very top, tools menu bar, very bottom.
3. Reuse Escape / outside / disclosure patterns already smoke-tested.
4. Keep `#edgeSheet` armed-only rule; keep `closeSketchSheet` on leave-sketch / Finish Sketch / create-open-on-sketch.
5. Audit leftover pairs at tip-time against `web/index.html` — fix only pairs that violate the Erik rule; do not invent new panel taxonomy.

**Do not bake / TBD:**

- Exact enumeration of every panel id that counts as “prior tool UI” (beyond P4 list + always-visible TBD mapping)
- Whether Tool Search open must hide sketch/edge/modify panels *(Superseded by #255 / `8e18de0` — Tool Search removed.)*
- Whether switching tools cancels in-progress tool state (geometry) vs only hides UI — **UI hide only** unless Erik locks cancel semantics
- Phone vs desktop differences beyond existing locks
- New control ids, CSS, pixels, icon art, hotkeys
- Gesture map changes
- Theme / Active chrome B changes

---

## Success Criteria (hard bar — tip-match)

Cite: Erik overnight item (2) ~11:55 PM MT 2026-10-26; P4 `prompts/p4-tool-shelf-show-hide.md`; always-visible chrome park + #191/#193; tip `e805614` `web/index.html` behavior above.

1. Switching to another **tool** hides the previous tool’s non-permanent UI (only one active tool shelf / tool sheet visible), consistent with P4 “only open shelf is the active tool's shelf.”
2. Opening another **menu** (Tools / Create / Selection / Camera / About / Tool Search as applicable; *Tool Search superseded by #255 / `8e18de0`*) hides the prior menu or tool shelf per existing mutual-exclusion patterns, extended only where a tip-time audit shows a leftover prior tool UI still visible.
3. Permanent chrome stays: very top (tree + filename), tools menu bar, very bottom (Modify / Create etc.).
4. No invented panel list, no gesture invents, no theme / Active chrome B work, no kernel / wasm, no export-path edits.

Outside this hard bar (TBD — do not bake): full panel-id taxonomy; Tool Search *(Superseded by #255 / `8e18de0`)* vs sketch/edge/modify hide matrix; cancel-vs-hide for in-progress tools; phone vs desktop extras; control ids / CSS / pixels / icon art / hotkeys; Fusion/Shapr matrices not stated in fetched docs.

## Out of scope

- Overnight item 1 (Tool Search exit) — separate brief.
- Themes / Active chrome B (#206).
- Re-spec of sketch draw overhaul / iPad-Kiwi gestures.
- Kernel / C++ / wasm / `UPDATES.md` from the coding `agy`.

## Done / handoff

- Dig: this invent-free draft on box.  
- **Doc primary:** land `prompts/` brief PR (and park line if needed). Dig seconds tip.  
- Dig does **not** open the prompt PR unless Doc asks. Pilot holds `agy` until tip-match.
