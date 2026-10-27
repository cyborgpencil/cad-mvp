# Antigravity item 7 → **7-C1 + 7-B1 + 7-E1** (flesh HOLD)

Sketch create clutter stays the tip status quo (**7-C1**). Vert and edge contrast stays on the existing tip materials, with the brightness metric **TBD** (**7-B1**). Edit and delete stay on the existing re-enter / select / Delete / Trim path (**7-E1**). **Flesh** is **HOLD**. Chief final lock (**7-C1 + 7-B1 + 7-E1**, flesh hold, 2026-10-27 ~11:15 AM MT via 3T · Chief) supersedes the overnight all-TBD item-7 prompt as the live must. This file is the Antigravity feed. It does not change the app by itself.

**Gate:** Base tip `507a019` (`507a019255c8b8127c32c5906e396d85b6285c41`, main after [#236](https://github.com/cyborgpencil/cad-mvp/pull/236)). Overnight tip-scan in `research/overnight-sketch-clutter-verts-edit.md` was at `c713ce4`. The facts below were re-read in `web/index.html` at `507a019`. Rust #4 **HOLD**. Triple-tap **HOLD**. No web theme apply. This docs file does not start an `agy`.

**Hard lock:** Invent-free. **Verify-only preferred** where the tip already matches. **No hex invent.** No new control id. No new pixel size. No gesture map. No 7-C2 overflow or dropdown. Flesh stays **HOLD**. Stay in `web/` (JS, HTML, CSS) for the later coding `agy`. No kernel, C++, `src/`, bindings, or wasm rebuild. Watertight / units (mm) only if a solid export path is touched. Do not invent export work. This item does not touch export.

---

## Source of truth (cite)

1. **Chief final lock (7-C1 + 7-B1 + 7-E1, flesh hold):** 3T · Chief final 2026-10-27 ~11:15 AM MT (`/workspace/research/chief-lock-items-6-7-10-2026-10-27.md`). Draw + Modify status quo. Contrast raised on existing tip materials only, no hex. Edit + delete = re-enter sketch + select + Delete/Trim on the existing path. Flesh hold. Brightness target/metric is a true gap.
2. **Dig cite pack (Doc second PASS ~2:45 PM MT):** `/workspace/research/cite-pack-item7-C1-B1-E1-2026-10-27.md`. Dig invent-free second on the retip brief **PASS** ~2:47 PM MT (`/workspace/research/antigravity-item7-C1-B1-E1-brief-2026-10-27.md`).
3. **Overnight scan, superseded as the live must:** `research/overnight-sketch-clutter-verts-edit.md` (Dig, 2026-10-27 ~1:15 AM MT, tip `c713ce4`). Its four-way TBD list is not the live scope. Tip quotes in it were re-read at `507a019`.
4. **Park, do not re-spec:** `prompts/antigravity-sketch-chrome-flow.md` (minimize non-sketch chrome while sketch is active; Create → six ortho planes → sketch-create tools; keep Finish Sketch). `prompts/antigravity-sketch-draw-overhaul.md` (live length and angle; dims stay; #183 strip and Finish stay). Item 8 owns the bottom bar.
5. **Tip facts re-read at `507a019` in `web/index.html`:**
   - Sketch panel `data-panel="sketch"` (`web/index.html:2072-2096`): **Draw** (Line, Rectangle, Circle, Arc, Polygon; each has a `data-action`); **Modify** (Sketch Fillet, Trim, Offset have `data-tool` and no `data-action`; Dimension has `data-action="sketchDimension"`); **Constrain** (third `.group`: Coincident, Horizontal, Vertical, Parallel, Perpendicular, Equal, Tangent, Fixed).
   - Sketch-active CSS (`web/index.html:1737-1748`) includes `html[data-sketch-active] [data-panel="sketch"] .group:nth-child(n+3) { display: none !important; }`. Constrain is that third group. The Draw group and the Modify group are not in that selector. The same block also hides `[data-panel="sketch"] .tool-btn:not([data-action])`, plus the View `vp-bar`, `#selectionShelf`, `#cameraShelf`, `#edgeSheet`, `#pickChooser`, `.hud`, and tools-sheet shelves.
   - `data-sketch-active` is set when `state.tab === 'sketch'` (`paintOriginPicker`, `web/index.html:11120-11122`). The sketch panel is shown when a sketch plane is set (`web/index.html:11124-11125`).
   - Finish Sketch is `#finishBar` / `data-action="finishSketch"` (`web/index.html:2007-2008`). `setTab` shows `#finishBar` on the sketch tab (`web/index.html:12722`). `finishSketch` returns to the Model tab (`web/index.html:13882-13889`).
   - Sketch line material: `THREE.LineBasicMaterial({ color: 0xf0c14e })` on the sketch `LineLoop` and the profile line (`web/index.html:3076-3078`, `3093-3095`). Boot-cube corner points: `PointsMaterial({ color: 0xf2c14e, size: 8, sizeAttenuation: false })`, then `corners.visible = false` (`web/index.html:3050-3054`). Body edge overlay: `edgeMat` `0x10283a` (`web/index.html:3043`); display paths set `0xd7e4f2` / `0x10283a` (`web/index.html:10500`, `10512`, `10517`). These literals are the baseline quote. They are not a brightness target.
   - `#modifyShelf` (`web/index.html:2481`) includes `data-action="delete"` Delete (`web/index.html:2491`). `runAction` sends that action to `deleteSelection()` (`web/index.html:14070-14072`). `deleteSelection` (`web/index.html:7176-7189`) requires `state.selectedIds`, then branches on `state.selection === 'face'`, `'edge'` or `'vertex'`, or bodies. `setTab('sketch')` calls `setModifyOpen(false, true)` (`web/index.html:12686-12687`), which hides `#modifyShelf`. The sketch-active CSS block does not name `#modifyShelf`.
   - Trim is the Modify button `data-tool="Trim"` with no `data-action` (`web/index.html:2083`). A click with an empty `data-action` sets `state.activeTool` from `data-tool` (`web/index.html:14073-14091`). The sketch-active rule `.tool-btn:not([data-action])` includes that button. No new Trim id is in this tip.
   - Modo `--sel-color` `#ffa829` is already set on the modo theme path (`web/index.html:2818`, `10618`). That lock is out of scope here.

---

## Sourced CAD patterns (lean first)

Lock note: these rows support the locked clauses. They are not new MVP chrome. Do not import Onshape overflow, Fusion toggles, a SolidWorks S-bar, or any vendor hex.

### Create clutter (supports **7-C1** status quo)

| App | Pattern | Source |
| --- | --- | --- |
| **Onshape** (lean) | Sketch toolbar only while the sketch is open; tools in dropdowns / overflow | [Sketch Tools](https://cad.onshape.com/help/Content/Sketch/sketch_tools.htm) |
| **Fusion** (check) | Sketch Palette toggles Show Constraints / Dimensions / Points | [Sketch Palette](https://help.autodesk.com/cloudhelp/ENU/Fusion-Sketch/files/GUID-4183A4B7-E002-4396-AD5A-7FF3C8B2F33A.htm) |
| **Shapr3D** (lean) | Adaptive tools; constraints can live aside | [Gestures/hotkeys](https://support.shapr3d.com/hc/en-us/articles/7873906073884-Keyboard-shortcuts-gestures-and-hotkeys) |
| **SolidWorks** (check) | Context **S** shortcut bar in Edit Sketch | [SW shortcuts blog](https://blogs.solidworks.com/products/solidworks/shortcuts-for-solidworks-beginners/) (secondary) |

**7-C1** keeps tip Draw + Modify and Constrain-hidden. Do not invent Onshape overflow, Fusion toggles, or a SolidWorks S-bar. That overflow/dropdown collapse was **7-C2** and is not locked.

### Brighter verts/edges (supports **7-B1** — no hex bake)

| App | Pattern | Source |
| --- | --- | --- |
| **Onshape** | Publishes selection/hover colors. Reference pattern only. Not an MVP lock. | [Colors](https://cad.onshape.com/help/Content/Home/colors.htm) |
| **Shapr3D** | Show Edges / enhanced selection visibility | [Display Modes](https://support.shapr3d.com/hc/en-us/articles/26807298276124-Display-Modes); [Enhanced selection visibility](https://support.shapr3d.com/hc/en-us/articles/19006027312028-5-820-Enhanced-selection-visibility) |
| **Fusion** | Sketch Palette Show Points | Sketch Palette (above) |
| **Modo** | Selected Item Drawing enlarges verts. Chrome lean only. Modo sel `#ffa829` is already product-locked elsewhere. Do not invent a second brightness hex here. | Viewport Properties (prior Dig) |

### Edit + delete (supports **7-E1**)

| App | Pattern | Source |
| --- | --- | --- |
| **Shapr3D** | In sketch: select → Delete; Trim for segments | [Delete (Sketch)](https://support.shapr3d.com/hc/en-us/articles/9310918605980-Delete-Sketch); [Trim](https://support.shapr3d.com/hc/en-us/articles/7874324658204-Trim) |
| **Onshape** | Open sketch; select; Delete / Trim | [Sketch Tools](https://cad.onshape.com/help/Content/Sketch/sketch_tools.htm); [Trim](https://cad.onshape.com/help/Content/Sketch/trim.htm) |
| **Fusion** | Edit Sketch → Delete geometry/constraints | [Unable to modify a sketch](https://www.autodesk.com/support/technical/article/caas/sfdcarticles/sfdcarticles/Unable-to-modify-a-sketch-in-Fusion-360.html) |
| **SolidWorks** | Edit Sketch → select → Delete; Trim PropertyManager | [Trim PropertyManager](https://help.solidworks.com/2022/English/SolidWorks/sldworks/HIDD_TRIM_CHOICES.htm) |

---

## Goal

Lock item 7 to these clauses only:

1. **7-C1.** Keep **Draw + Modify**. **Constrain stays hidden** while sketch-active. That is the tip status quo. Verify it. Do not invent which Draw tools to hide.
2. **7-B1.** Raise contrast on **existing tip materials only** (the gold/dark line and point baselines quoted above). Brightness metric and target are **TBD**. Do not invent a hex. Do not bake the Onshape color table or Modo sel `#ffa829` into this item. Modo sel `#ffa829` is already locked elsewhere and is out of scope here.
3. **7-E1.** Re-enter sketch → select entity → Delete/Trim on the existing path. Whether `#modifyShelf` Delete applies in sketch is **TBD read from tip**. Do not add a control id.
4. **Flesh.** **HOLD.** True gap. Omit it from coding scope.

## Coding bar — verify-only where the tip already matches

Later coding is one Antigravity-only `agy` on Z13, from main, after this file is on main. Prefer a worktree under `C:\Dev\`. Do not invent a new path. Do not commit from Antigravity. This docs PR does not edit `web/`.

1. **7-C1.** Re-verify the sketch-active CSS still hides the third sketch group (Constrain) and still leaves the Draw and Modify groups in place. No tool add or remove. No edit to that CSS for this item when the tip still matches.
2. **7-B1.** If no sourced brightness delta or metric is available, leave the metric **TBD**. Do not invent one. Do not change material colors. Adjust only the existing tip materials if Chief names a metric. No new hex.
3. **7-E1.** Document the existing Delete/Trim path from the tip read above. Reuse existing controls only. The tip read at `507a019` is: sketch tab entry hides `#modifyShelf` via `setModifyOpen(false, true)`; `data-action="delete"` calls `deleteSelection()` (face, edge/vertex, or bodies); Trim is the existing `data-tool="Trim"` button with no `data-action`. Whether `#modifyShelf` Delete applies to a sketch entity while sketch-active stays **TBD**. Do not add a control id. Do not add a `data-action` to unhide Trim.
4. **Flesh.** Omit it.

## MUST NOT

- Invent a hex, a brightness metric, a control id, a pixel size, or which Draw tools to hide.
- Invent **7-C2** overflow or dropdown collapse.
- Implement flesh.
- Bake the Onshape color table, or Modo sel `#ffa829`, as this item’s brightness lock.
- Touch item 6 stretch, item 10 dims, theme tokens, Active chrome B, or Rust #4.
- Create a versioned copy of this prompt.
- Edit `web/` from this docs PR. Edit `UPDATES.md`, `mvp/requirements.md`, or `research/` from the coding `agy`.

## True gap / HOLD (do not bake)

- **Flesh:** **HOLD.** No vendor help page in the cite pack uses “flesh” as a sketch or solid feature. True gap until Erik or Chief defines it. Omit from coding scope.
- **Brightness metric / target:** **TBD.** No sourced delta is in the cite pack or in the tip materials.
- **`#modifyShelf` Delete in sketch:** **TBD read from tip.** The shelf button, the `deleteSelection` branches, and the sketch-tab close of the shelf are recorded above. Do not decide a new delete target.
- **Triple-tap:** Standing **HOLD** (out of scope).
- **Rust #4:** Standing **HOLD** (out of scope).

## Out of scope

- **7-C2** (overflow / dropdown). Not locked.
- Item 6 stretch. Item 10 dims.
- Theme web tokens and Active chrome B. Modo sel `#ffa829` stays where it already is.
- Sketch chrome flow and the sketch draw overhaul, except to avoid re-specifying them. Item 8 owns the bottom bar.
- Constraint solver / PlaneGCS.
- `UPDATES.md` (Repo Keeper).
- Kernel, C++, `src/`, bindings, or `.wasm` rebuild. Do not commit `.wasm`, `web/cadcam.wasm`, or `web/dist/`. Do not edit a root `PROGRESS.md`.

## Smoke

Check sourced behavior only. No invented pixel asserts. No invented hex asserts. Watertight / units only if an export path is touched. This item does not touch export, so do not add that assert.

1. Sketch-active: the Constrain group is hidden; the Draw group and the Modify group are present. No tool was added or removed.
2. Re-enter sketch on the existing Sketch-tab path. Delete and Trim stay on the controls already in the tip (`#modifyShelf` `data-action="delete"`, Modify `data-tool="Trim"`). Do not assert a new sketch-entity delete result while that `#modifyShelf` applicability is TBD.
3. Tip material colors were not replaced with an invented hex. Modo sel `#ffa829` was not copied onto sketch materials.

## Success Criteria

Must PASS at tip-match. Cite 3T · Chief final **7-C1 + 7-B1 + 7-E1** (flesh hold, 2026-10-27 ~11:15 AM MT); Dig cite pack (Doc second PASS); tip re-read at `507a019`.

1. The prompt states **7-C1** (Draw + Modify stay; Constrain stays hidden while sketch-active; verify only; no invented Draw-tool hide list; no **7-C2**).
2. The prompt states **7-B1** (existing tip materials only; brightness metric/target **TBD**; no hex invent; Onshape colors and Modo sel `#ffa829` are not this item’s lock).
3. The prompt states **7-E1** (re-enter sketch → select entity → Delete/Trim on the existing path; `#modifyShelf` Delete in sketch is **TBD read from tip**; no new control id).
4. **Flesh** is **HOLD** and is outside coding scope.
5. This docs change does not edit `web/`.

## Done

Re-read on `507a019`: sketch-active CSS still hides the third sketch group; Draw and Modify groups remain; line/point materials are the quoted baselines; `#modifyShelf` Delete and Modify Trim are the existing controls, with sketch applicability of that Delete left **TBD**. Prompt updated in place. Dig primary tip-match, Doc Steward second. Author does not self-APPROVE. Repo Keeper undrafts and plain-merges. After this file is on main, Pilot runs one Antigravity-only coding `agy` on Z13 from main. This file does not start that `agy`.
