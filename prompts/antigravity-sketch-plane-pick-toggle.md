# Antigravity sketch plane-pick toggle

A Multi-like toggle whose only job is to enable or disable the tip’s plane-set paths while Sketch is active and no plane is set. Default is ON, which is current tip behavior. This file is the Antigravity feed. It does not change the app by itself.

**Gate:** Antigravity-only on Z13. Pilot holds until this file tip-matches on main, then owns one `agy` for this brief. This brief is not a float slice. It does not wait on the float 3-way train, and the float train does not wait on it. Chief may run it after or with the float slices. This prompts file does not start the `agy` by itself.

**Hard lock:** Implementation is **Antigravity-only on Z13**. Do not use Grok Build or Cursor for the handoff into code. Prefer worktree `C:\Dev\cadcam-mvp` if Pilot says otherwise; do not invent a new path or create folders from this brief. Do not commit from Antigravity; Pilot/Repo Keeper commit path owns that. Do not invent Erik specs. Stay in `web/` (JS, HTML, CSS). No kernel, C++, `src/`, bindings, or wasm rebuild. Do not edit `UPDATES.md` or a root `PROGRESS.md`. Do not edit this prompt or the float prompt files from the `agy`.

**Source of truth:**

- Chief FINAL LOCK (DEV Chief, 2026-10-27 ~6:45 PM MT), plane-pick:
  - Sole job: enable or disable the tip plane-**set** paths while Sketch is active and no plane is set.
  - Default **ON** (= current tip behavior).
  - OFF = those plane-set paths are **inert** (they do not set `state.sketchPlane`).
  - GAP (2) locked: OFF = **disable hit-testing only**. Do **not** hide `#originPlanes`.
  - GAP (1): control `id` is **TBD**. Placement is the Multi neighborhood only. Do not invent an `id`.
  - `#multiToggle` stays Multi-only. Do not wire plane-pick into it. Do not reuse `state.phoneMulti`.
  - No alternate plane, no auto plane, no hotkey.
  - Re-pick after a plane is already set is **out** of this tip.
  - Phone tappable chrome stays **≥44 CSS px**.
- Tip `5ee57eee269f4f49429d17d150faeaf7b88584f8` (`5ee57ee`, main after #240). Read `web/index.html` from that commit. There is **no** plane-pick control, `data-action`, or state flag on this tip. Do not invent one beyond the locks below.
- Sketch active on this tip is `state.tab === 'sketch'`. No plane set is `!state.sketchPlane`. `paintOriginPicker` uses both: `const show = sketchActive && !state.sketchPlane` and `bar.hidden = !show` for `#originPlanes`. Leave that show/hide rule. OFF must not set `bar.hidden`.
- Plane-set paths on this tip (the only ones this toggle gates):
  1. `#originPlanes` buttons `data-action="originPlane"` (`data-plane` `xz`, `back`, `xy`, `bottom`, `left`, `yz`). `runAction` `action === 'originPlane'` calls `setOriginSketchPlane(which)`, which assigns `state.sketchPlane`.
  2. Planar-face tap while `state.tab === 'sketch'` and no modifier (`shift` / `ctrl` / `meta`), in the pointer-up branch that calls `pickSketchFace(clientX, clientY, pointerType)` and then `setSketchPlane(faceId)` when `faceId && (!state.sketchPlane || faceId !== state.sketchPlane.faceId)`.
- `setOriginSketchPlane` and `setSketchPlane` themselves stay callable. Do not wrap them. `window.__cadcamSketch.tapFace` calls `setSketchPlane` and is not the planar-face tap path above. Leave `tapFace` as on this tip.
- Multi on this tip, the pattern to mirror:
  - Markup in `nav.phone-tabbar`, after `#pickFilter`: `<button type="button" class="tab" id="multiToggle" data-action="multiToggle" data-tool="Multi" title="Multi" aria-pressed="false" aria-label="Multi">Multi</button>`.
  - Class is `tab`, not `tool-btn`. `.tab` is `min-width` / `min-height` / `height: 44px`. Inside the phone media rule, `.phone-tabbar .tab` is `min-width: 44px` and `min-height: 44px`. `.phone-tabbar` is `display: none` until `@media (max-width: 820px), (max-height: 520px)`.
  - `state.phoneMulti` defaults `false`. `runAction` `action === 'multiToggle'` does `state.phoneMulti = state.phoneMulti !== true`, then `paintPhoneChrome()`, which toggles `is-on` and `aria-pressed` on `#multiToggle`.
  - Other `data-action` names on this tip are camelCase (`multiToggle`, `originPlane`, `closeSheet`, `aboutMenu`). `data-action="planePickToggle"` follows that convention. It is the locked action token for this control. It is not on the tip today.
- State flag: this tip has no plane-pick flag. Add `planePickEnabled: true` on the `state` object next to `phoneMulti`. `state.planePickEnabled === false` means OFF (inert). Any other value, including the default `true`, means ON. Do not reuse `phoneMulti`.

Anything these locks do not state stays **TBD**.

## Goal
In `web/` only, add one toggle in the Multi neighborhood that turns the two plane-set paths on or off while Sketch is active and no plane is set. Default ON leaves current tip behavior. OFF makes those paths inert and does not hide `#originPlanes`. No kernel, C++, `src/`, bindings, or wasm rebuild.

Locked behavior:

1. **One control, Multi neighborhood.** Mirror the `#multiToggle` element: `button type="button"` with `class="tab"`, placed in the same `nav.phone-tabbar`, adjacent to `#multiToggle`. Do not add a second copy on the desktop toolbox. Do not use `class="tool-btn"` for this control; `#multiToggle` does not. Do not invent an `id`. Address the control only as `[data-action="planePickToggle"]`. Do not put `data-action="planePickToggle"` on `#multiToggle`.
2. **Action.** `data-action="planePickToggle"` flips `state.planePickEnabled` the way `multiToggle` flips `state.phoneMulti` (`!== true`), then refreshes `is-on` and `aria-pressed` on `[data-action="planePickToggle"]` the way `paintPhoneChrome` does for `#multiToggle`. Default ON: initial `aria-pressed` is `true` and `is-on` is present when `state.planePickEnabled !== false`. Do not write `state.phoneMulti` from this action.
3. **ON (default).** `originPlane` still calls `setOriginSketchPlane`. The planar-face tap still calls `pickSketchFace` and then `setSketchPlane` under the same condition as this tip. `state.sketchPlane` is set the way the tip sets it today.
4. **OFF, and Sketch active, and no plane set.** Those two paths are inert. `originPlane` does not call `setOriginSketchPlane` and does not assign `state.sketchPlane`. The planar-face tap does not call `pickSketchFace` / `setSketchPlane` for the no-plane case and does not assign `state.sketchPlane`. Hit-testing for that set is disabled. `#originPlanes` stays under the existing `paintOriginPicker` rule (`hidden` only when not `sketchActive && !state.sketchPlane`). Do not hide the bar because the toggle is OFF. Do not add a CSS hit-test property.
5. **Plane already set.** Re-pick stays the tip branch (`faceId !== state.sketchPlane.faceId` still calls `setSketchPlane`). This toggle does not change that. Out of this tip.
6. **Not Sketch.** Do not change body pick, `phoneMulti`, or `pickElement` outside the two paths above.

Unchanged:

- `#multiToggle`, `data-action="multiToggle"`, and `state.phoneMulti` stay Multi-only.
- `#originPlanes` markup and `data-plane` values stay.
- Phone floor stays the 44 CSS px already on `.tab` and `.phone-tabbar .tab`. Do not add a px size.

## Workflow
1. Read the locks above. Copy behavior from those locks only.
2. Add `planePickEnabled: true` beside `phoneMulti` on `state`. Do not add a `publishGateState` key and do not add a project-save key. `phoneMulti` is published on this tip; do not copy that publish for this flag.
3. Add the mirrored `tab` button in `nav.phone-tabbar` next to `#multiToggle` with `data-action="planePickToggle"` and no `id`. Wire `runAction` for that action only. Query the button with `[data-action="planePickToggle"]`.
4. Gate only the two call sites named above, and only when `state.planePickEnabled === false` && `state.tab === 'sketch'` && `!state.sketchPlane`. Leave `setOriginSketchPlane`, `setSketchPlane`, and `tapFace` unwapped.
5. Do not set `#originPlanes` hidden from this flag. Do not change `paintOriginPicker`’s `show` rule.
6. Where a string or id is **TBD**, leave it TBD.

## Do not bake / TBD
Do not invent and do not bake any of the following. Park TBDs stay **TBD**, verbatim:

- Control `id`. Do not add an `id`. GAP (1) stays **TBD**.
- Visible label, `data-tool`, `title`, and `aria-label` text. This lock does not name them. Do not copy Multi’s strings (`Multi`). Do not invent a product name such as a plane-pick label. Omit those strings.
- A second control, a desktop `.tool-btn` copy, or placement outside `nav.phone-tabbar`
- Wiring this behavior to `#multiToggle`, `data-action="multiToggle"`, or `state.phoneMulti`
- Hiding `#originPlanes` when OFF, or any change to `paintOriginPicker`’s show rule
- A new CSS hit-test property, `pointer-events` rule, or `disabled` attribute for this toggle
- Wrapping `setOriginSketchPlane` or `setSketchPlane`, or changing `window.__cadcamSketch.tapFace`
- Re-pick after `state.sketchPlane` is already set
- An alternate plane, an auto plane, or a hotkey
- A new `publishGateState` key or a project-save / load key for `planePickEnabled`
- New px sizes (keep the 44 CSS px floor already on `.tab` / `.phone-tabbar .tab`)
- New hex colors, new classes other than the existing `tab` / `is-on` already used by Multi
- Float / drag / Close, snap, persist, z-order, menu-bar shrink

## Out of scope
- Float slices (`prompts/antigravity-offbar-agy-float-register.md`, `prompts/antigravity-offbar-agy-close-chrome.md`, `prompts/antigravity-offbar-agy-regression-smoke.md`) and the monolith `prompts/antigravity-offbar-menus-float-drag-close.md`.
- Snap, persist, z-order, shrink, overflow, collapse.
- Item-7 / flesh / brightness / `#modifyShelf` Delete-in-sketch.
- Theme / Modo tokens / Rust HOLD.
- `UPDATES.md` / root `PROGRESS.md` edits from this brief.
- Kernel / C++ / wasm rebuild. Do not commit `.wasm`, `web/cadcam.wasm`, or `web/dist/`.

## Smoke
Manual wake smoke. No new smoke harness. No invented pixel asserts. Because no smoke path is added here, do not print a done marker.

Check locked behavior only:

1. On load, plane-set still works (default ON): with Sketch active and no plane, `#originPlanes` / `originPlane` calls `setOriginSketchPlane`, and a planar-face tap calls `pickSketchFace` / `setSketchPlane`.
2. After `data-action="planePickToggle"` turns `state.planePickEnabled` false, those two paths do not set `state.sketchPlane` while Sketch is active and no plane is set. `#originPlanes` is still shown under the existing `paintOriginPicker` rule.
3. `#multiToggle` still toggles `state.phoneMulti` only.
4. With a plane already set, the existing re-pick branch is unchanged.
5. The new control is a `tab` in `nav.phone-tabbar` next to `#multiToggle`, found by `[data-action="planePickToggle"]`, with no invented `id`. Tappable size stays the existing 44 CSS px floor.
6. No float, Close, shrink, hotkey, auto plane, or alternate plane from this brief.

## Success Criteria
Must PASS at tip-match. Cite Chief FINAL LOCK plane-pick (2026-10-27 ~6:45 PM MT) and tip `5ee57eee269f4f49429d17d150faeaf7b88584f8` `web/index.html`. Only locked behavior is on this bar.

1. Default `state.planePickEnabled` is `true`. ON matches current tip plane-set behavior.
2. OFF (`state.planePickEnabled === false`) makes `originPlane` → `setOriginSketchPlane` and the planar-face tap → `pickSketchFace` / `setSketchPlane` inert while `state.tab === 'sketch'` and `!state.sketchPlane`. `state.sketchPlane` is not set by those paths.
3. OFF does not hide `#originPlanes`. `paintOriginPicker`’s show rule is unchanged.
4. The control mirrors `#multiToggle` (`button.tab` in `nav.phone-tabbar`, adjacent to `#multiToggle`) and is wired only with `data-action="planePickToggle"`. No invented `id`. Visible label / `data-tool` / `title` / `aria-label` strings stay **TBD** and are not filled with a guessed name.
5. `#multiToggle` and `state.phoneMulti` are unchanged. `phoneMulti` is not the plane-pick flag.
6. Re-pick after a plane is set is unchanged. No alternate plane, auto plane, or hotkey.
7. Tappable chrome stays ≥44 CSS px. No new px threshold.
8. No float-slice edits, no shrink, no item-7, no `UPDATES.md`.

Outside this hard bar: control `id`, visible label strings, re-pick, float/drag/Close, snap, persist, z-order, shrink, item-7, theme, Rust, `UPDATES.md`, `PROGRESS.md`, and `research/`.

## Done
Draft until tip-match. Dig tip-match is COMMENT-only. Doc Steward is second. Repo Keeper undrafts and plain-merges. Author does not self-APPROVE. Doc does not edit `UPDATES.md`. This brief is not in the float merge order. Pilot launches it only after this file tip-matches, after or with the float slices, when Chief has authorized the `agy`. Report the prompt PR link and tip SHA. Pilot reports any implementation PR separately. Control `id` stays TBD; do not open an Erik card for that GAP from this file.
