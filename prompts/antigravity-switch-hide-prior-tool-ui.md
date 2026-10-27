# Antigravity switch tool/menu → hide prior tool UI

When the user switches tools or opens another menu, prior tool UI hides. Extend P4 and always-visible chrome. This file is the Antigravity feed. It does not change the app by itself.

**Gate:** This **code** starts only after this file tip-matches on main. Base is main merge `#206` @ `e805614` (theme tip `9b758b4`). Pilot holds the next `agy` until overnight items 1 and 2 both tip-match. This prompts file does not start the `agy` by itself. P4 and always-visible chrome are already on main. Do not re-spec them. Do not re-spec `#206`.

**Hard lock:** Implementation is **Antigravity-only on Z13**. Pilot holds one `agy` until this file tip-matches on main, then owns one `agy`. Do not use Grok Build or Cursor for the handoff into code. Prefer a worktree under `C:\Dev\`; do not invent a new path or create folders from this brief. Do not commit from Antigravity; Pilot/Repo Keeper commit path owns that. Do not invent Erik specs. Stay in `web/` (JS, HTML, CSS). No kernel, C++, `src/`, bindings, or wasm rebuild.

**Source of truth:**

- Erik overnight ~11:55 PM MT 2026-10-26, item **(2) switch tool/menu → hide prior tool UI**.
- `research/overnight-switch-hide-prior-tool-ui.md` (Dig, 2026-10-27 ~12:24 AM MT), scanned at tip `e805614`. Cite that digest. Anything it marks **TBD** stays **TBD**.
- P4, `prompts/p4-tool-shelf-show-hide.md` (merged #44 / #54): “A shelf opens only while that tool or edit is active. … **The only open shelf is the active tool's shelf.** Leaving the tool collapses it.” Shelves named there: Create (`#createMenu`), Modify (`#modifyShelf`), `#dimPanel` / the property edit sheet, and center `#hudSize` while editing a basic shape. Escape and outside click are the disclosure pattern to reuse.
- Always-visible chrome: the park bullet in `mvp/requirements.md` and `prompts/antigravity-panel-labels-chrome.md` (#167 / #191 / #193). Only the **very top** (tree + filename), the **tools menu bar**, and the **very bottom** (Modify / Create etc.) stay visible 100% of the time. Everything else uses show/hide like other shelves. Mapping TBDs in that brief stay **TBD**.
- Sketch chrome minimize: park plus shipped sketch chrome (#183 / #186). While sketching, minimize non-sketch chrome; top and bottom stay on (overhaul lock).
- Create → ortho → tools: `mvp/requirements.md` and `prompts/antigravity-sketch-chrome-flow.md`. After the plane pick, hide the view-selection menu, show only sketch-create tools, and keep Finish Sketch.
- Park bullet **Switch tool/menu → hide prior tool UI** in `mvp/requirements.md` (this docs PR). It cites those locks. It does not add a panel taxonomy.

Partial mutual exclusion already on tip `e805614` `web/index.html` (Dig scan; not a full pair list):

| Trigger | What that path already closes |
| --- | --- |
| Most `runAction` tools | `closePopups()` unless `action` is `fileMenu`, `exportMenu`, `search`, `toolsMenu`, `selectionShelf`, `cameraShelf`, `createMenu`, `loadProject`, `pickFilter`, `aboutMenu`, or `theme`. That call closes search, the tools sheet, create, file/export, about, and the pick chooser. |
| Open Tools menu | `closeSearch`, drawers, file/export, create, the selection shelf, the camera shelf |
| Open Selection shelf | `closePopups`; closes the camera shelf and Modify |
| Open Camera shelf | `closePopups`; closes the selection shelf and Modify |
| Open About | `closePopups`; closes selection, camera, and Modify |
| Open Create menu | `closePopups`; on the sketch tab, `clearSketchGeometry` and `closeSketchSheet`; on open, `setModifyOpen(false)` and clears dim/prop sheet flags |
| Open Modify | `closeCreateMenu`; on open, clears dim/prop sheet flags |
| Escape | Closes Modify, selection, camera, dim/prop flags, collapses `#hudSize` while editing a basic shape, `closePopups`, drawers |
| `#edgeSheet` | `paintEdgeChrome`: hidden unless `edgeArm` is `fillet` or `chamfer` |
| Leave sketch tab / Finish Sketch | `closeSketchSheet()` |
| `openSketchSheet(mode)` | Swaps row visibility inside `#sketchSheet` for the new mode (rect, circle, polygon, line, arc, extrude) |

Dig also records what is not a single gate on that tip:

- Opening a new sketch tool calls `openSketchSheet(...)`. It does not universally call `setModifyOpen(false)`, clear `edgeArm`, or close unrelated tool panels in one shared helper.
- `closePopups()` does not hide `#sketchSheet`, `#edgeSheet`, `#modifyShelf`, or `#dimPanel`.
- `openSearchDialog()` closes the tools sheet, create, drawers, and file/export. It does not hide `#sketchSheet`, `#edgeSheet`, or Modify. Whether it must is **TBD**.
- Whether every tool-to-tool and tool-to-menu pair must hide the previous tool’s panel is Erik’s overnight intent. It is not fully enumerated in `mvp/requirements.md` as of tip `e805614`.

Sourced patterns in the digest are patterns only. They are not locks.

- Onshape Search Tools (https://cad.onshape.com/help/Content/Home/search_tools.htm): the search dialog closes when a toolbar tool is selected.
- Onshape feature dialogs (https://cad.onshape.com/help/Content/PartStudio/feature_basics.htm ; https://cad.onshape.com/help/Content/Home/dialogs.htm): Cancel or Escape closes that feature dialog. Enter commits. That is a tool-dialog lifecycle pattern, not a control id for this app.
- Onshape Escape (https://cad.onshape.com/help/Content/Home/keyboard_shortcuts_and_hotkeys.htm): Escape “Exits the command in use”.
- Shapr3D Accessing tools (https://support.shapr3d.com/hc/en-us/articles/7378907587484-Accessing-tools): adaptive tools from selection; side menus float. The fetched page does not publish a universal “switch tool hides previous panel” matrix. Do not invent one.
- FreeCAD: Escape can exit the Task panel (`General/TasksKeyEsc` in the Fine-tuning wiki). FreeCAD #28852 notes task-panel visibility across workbench switches. That is OSS history, not a lock for this WASM UI. Dig’s cite line is only that OSS apps treat active task UI as modal to the current command.
- Prior Dig box digest `research/ipad-cad-kiwi-modo-gestures-panels.md` covers float/dock and gesture maps. Do not re-bake gesture invents here. That file is not in this repo’s `research/` tree at tip `e805614`.

## Goal
Implement Erik’s overnight rule by extending the P4, always-visible chrome, and mutual-exclusion paths already cited above. UI chrome only. Do not invent a new chrome system.

When this file has tip-matched, the coding slice may do only the following. Dig allowed this list only when it does not bake a **TBD**. This brief does not close those TBDs.

1. When the user arms a different tool, or opens a different menu, hide the prior tool’s non-permanent UI (shelves, tool sheets, search) with the show/hide mechanisms that already exist.
2. Keep permanent chrome as the always-visible lock states it: very top (tree + filename), tools menu bar, very bottom (Modify / Create etc.).
3. Reuse Escape, outside click, and the disclosure pattern already smoke-tested (`CREATE_MENU_EXPR`, `SEARCH_DISCLOSURE_EXPR`, and the Modify disclosure checks).
4. Keep the `#edgeSheet` armed-only rule. Keep `closeSketchSheet` on leave-sketch, Finish Sketch, and create-open on the sketch tab.
5. Audit leftover pairs at tip time against `web/index.html`. Fix only a pair that still shows prior non-permanent tool UI after the user has switched tool or menu. Do not publish a new panel taxonomy from that audit.

Hide UI only. Do not cancel in-progress tool geometry unless Erik locks cancel semantics. That cancel-versus-hide choice stays **TBD**.

Where a line is **TBD**, leave it **TBD**. Do not map existing regions onto “very top / tools menu bar / very bottom” beyond the words already in the always-visible park. Do not decide which surfaces count as panels.

## Workflow
1. Read `research/overnight-switch-hide-prior-tool-ui.md`, P4, and the always-visible chrome park and brief. Copy behavior from those sources and from the partial paths quoted above.
2. On a tool arm or a menu open, hide the prior tool’s non-permanent UI using an existing show/hide path.
3. Leave permanent chrome visible: very top (tree + filename), tools menu bar, very bottom (Modify / Create etc.).
4. Keep `#edgeSheet` visible only while fillet or chamfer is armed. Keep sketch-sheet close on leave-sketch, Finish Sketch, and create-open on the sketch tab.
5. At tip time, compare `web/index.html` with the rule “the only open shelf is the active tool's shelf.” Change a pair only when prior non-permanent tool UI is still visible after the switch. The Tool Search versus `#sketchSheet` / `#edgeSheet` / Modify question is **TBD**. That audit does not answer it.
6. Where the digest or the always-visible brief marks a detail **TBD**, leave it **TBD**. Do not fill cancel-versus-hide. Do not name a new panel list.

## Do not bake / TBD
Do not invent and do not bake any of the following. They stay **TBD**:

- The exact list of every panel id that counts as “prior tool UI”, beyond the P4 shelf list and the always-visible mapping TBD
- Whether opening Tool Search must hide `#sketchSheet`, `#edgeSheet`, or Modify
- Whether switching tools cancels in-progress tool state (geometry) or only hides UI
- Phone versus desktop differences beyond existing locks
- New control ids, CSS, pixels, icon art, or hotkeys
- Gesture map changes
- Theme or Active chrome B changes
- A Fusion or Shapr hide matrix those fetched pages do not state

The always-visible TBDs stay **TBD** as well: which existing UI regions map to “very top / tools menu bar / very bottom”; which other panels currently stay permanent and must become shelves; any exceptions Erik did not state.

## Out of scope
- Overnight item 1 (Tool Search exit). Separate brief: `prompts/antigravity-tool-search-exit.md`.
- Themes / Active chrome B (`prompts/antigravity-theme-default-modo.md`, #206).
- Re-spec of sketch draw overhaul or iPad/Kiwi gestures. Sketch chrome #183 / #186 and the Create → ortho flow stay as already locked. Do not re-spec them.
- Editing `research/overnight-switch-hide-prior-tool-ui.md`, `mvp/requirements.md`, or `UPDATES.md` from the coding `agy`.
- Export-path edits. Watertight and units stay untouched.
- Kernel / C++ / wasm rebuild. Do not commit `.wasm`, `web/cadcam.wasm`, or `web/dist/`. Do not edit a root `PROGRESS.md`.

## Smoke
Manual wake smoke on Pages. No new smoke harness. Reuse `tests/deploy_smoke.py` disclosure checks that already exist (`CREATE_MENU_EXPR`, `SEARCH_DISCLOSURE_EXPR`, Modify `aria-expanded` / `aria-controls`). This brief does not add a smoke expression. No invented pixel asserts. Because no new smoke path is added here, do not print a done marker.

Check Erik-stated and P4-stated behavior only. Do not assert a panel-id taxonomy, a Tool Search versus sketch/edge/modify matrix, cancel-versus-hide, phone versus desktop extras, new control ids, CSS, pixels, icon art, or hotkeys.

1. Switching to another tool hides the previous tool’s non-permanent UI, so only the active tool’s shelf or tool sheet stays open (P4).
2. Opening another menu hides the prior menu or tool shelf where an existing mutual-exclusion path already does that, and where a tip-time audit shows prior non-permanent tool UI still visible.
3. Very top (tree + filename), the tools menu bar, and very bottom (Modify / Create etc.) stay visible.

## Success Criteria
Must PASS at tip-match. Cite Erik overnight item (2) ~11:55 PM MT 2026-10-26; P4 `prompts/p4-tool-shelf-show-hide.md`; the always-visible chrome park and #191 / #193; Dig’s scan of tip `e805614` `web/index.html` in `research/overnight-switch-hide-prior-tool-ui.md`. Only that sourced behavior is on this bar.

1. Switching to another tool hides the previous tool’s non-permanent UI. Only one active tool shelf or tool sheet is visible, consistent with P4: “The only open shelf is the active tool's shelf.”
2. Opening another menu (Tools, Create, Selection, Camera, About, or Tool Search as applicable) hides the prior menu or tool shelf along the existing mutual-exclusion paths, extended only where a tip-time audit shows leftover prior tool UI still visible.
3. Permanent chrome stays: very top (tree + filename), tools menu bar, very bottom (Modify / Create etc.).
4. No invented panel list, no gesture invents, no theme or Active chrome B work, no kernel or wasm, no export-path edits.

Outside this hard bar: full panel-id taxonomy; the Tool Search versus sketch/edge/modify hide matrix; cancel-versus-hide for in-progress tools; phone versus desktop extras; control ids, CSS, pixels, icon art, and hotkeys; Fusion or Shapr matrices the fetched docs do not state; the always-visible region-mapping TBDs; overnight item 1; themes #206; sketch-draw re-spec; iPad/Kiwi gestures; `research/overnight-switch-hide-prior-tool-ui.md`; `mvp/requirements.md`; `UPDATES.md`; kernel / C++ / wasm.

## Done
Draft until tip-match: Doc Steward primary (COMMENT), Research Digest second. Author does not self-APPROVE. Repo Keeper undrafts and plain-merges. After this file is on main, Pilot runs one Antigravity-only `agy` from it. Pilot holds that `agy` until overnight items 1 and 2 have both tip-matched. This brief does not lock which item’s `agy` runs first. Report the prompt PR link and tip SHA. Pilot reports any implementation PR separately.
