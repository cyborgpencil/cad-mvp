# Antigravity sketch chrome minimize + Create→ortho plane flow

Minimize non-sketch chrome while a sketch is active, and start a sketch by pressing Create, picking one of the six orthographic planes, then showing only sketch-create tools. This file is the Antigravity feed. It does not change the app by itself.

**Gate:** Next coding slice after #181 on main (merge `77696ec` / tip was `10d9b9d`). First of the remaining UI after view-cube. X-ray (#163 park) and panel chrome (#167 park) stay queued after this.

**Hard lock:** Implementation is **Antigravity-only on Z13**. Pilot holds coding until this file is tip-matched on main, then owns one `agy`. If `agy` exits with a dirty tree and no commit, Pilot commits and drafts the implementation PR — no second `agy`. Do not use Grok Build or Cursor for the handoff into code. Suggested Pilot worktree: create or reuse a dedicated worktree under `C:\Dev\` only if Pilot already has one; do not invent a path or create folders from this brief. Prefer `C:\Dev\cadcam-mvp` if Pilot says otherwise. Do not commit from Antigravity; the Pilot commit path owns that commit. Do not invent Erik specs. No kernel, C++, `src/`, bindings, or wasm rebuild.

**Source of truth:** The two parked bullets in `mvp/requirements.md` under **Queued after current in-flight (discuss / parked)** named exactly **Sketch chrome minimize (active sketch)** and **Sketch Create → ortho plane → sketch tools flow**. Parked in the same change as this brief. Erik via 3T, 2026-10-26 ~4:40 PM MT. Cite those two bullets for the new behavior. Overnight locks **(c)** and **(d)**, the Q5 discuss locks, and the export acceptance checks stay as written in that file. Anything the park does not state stays **TBD**.

## Goal
Implement these sourced behaviors in `web/` (JS, HTML, CSS as needed). No kernel, C++, `src/`, bindings, or wasm rebuild.

**Problem (Erik):** Arc+polygon hard to test — Arc dialog + floating toolbars eat the viewport.

### Sketch chrome minimize (active sketch)
Copied from the park in this change:

- While a sketch process is active, **minimize / hide non-sketch chrome** — only sketching tools stay visible. Erik referred to the blue-circled sketch tool strip in his phone screenshot; do not invent which control ids that strip maps to. Hide the other floating shelves that crowd the view.
- **TBD:** which existing shelves/panels count as non-sketch chrome vs the sketch tool strip; phone vs desktop placement; whether always-visible chrome from the prior park (very top / tools menu bar / very bottom) stays visible during sketch; Arc dialog placement beyond “don’t eat the viewport”.

### Sketch Create → ortho plane → sketch tools flow
Copied from the park in this change:

- Press Create.
- Pick any of the **six** orthographic views/planes: Front, Back, Top, Bottom, Left, Right.
- Once a plane/view is chosen, hide that view-selection menu and show **only** sketch-create tools.
- Keep **Finish Sketch**.
- **TBD:** Create vs New Sketch naming if the UI differs; whether this replaces the current face-tap sketch plane path or is additive; control ids; layout of the six-plane picker.

## Workflow
1. Read the two park bullets named above. Copy behavior from those bullets only.
2. While a sketch process is active, minimize or hide non-sketch floating shelves that crowd the view. Only sketching tools stay visible.
3. Sketch start: Press Create, then let the user pick any of the six orthographic views/planes (Front, Back, Top, Bottom, Left, Right).
4. Once a plane/view is chosen, hide that view-selection menu and show only sketch-create tools. Keep **Finish Sketch**.
5. Where the park marks a detail **TBD**, leave it TBD. Do not fill the gap with a guessed value.

## Do not bake / TBD
Do not invent and do not bake any of the following. They stay **TBD**, verbatim from the park and from Erik's locks:

- control ids
- pixel sizes
- hex colors
- icon art
- which exact DOM nodes map to the “sketch tool strip” vs “non-sketch chrome” (including which control ids the blue-circled phone strip maps to)
- phone vs desktop placement
- whether always-visible chrome from the prior park (very top / tools menu bar / very bottom) stays visible during sketch
- Arc dialog placement or redesign beyond “don’t eat the viewport”
- Create vs New Sketch naming if the UI differs
- whether the Create → ortho plane path replaces the current face-tap sketch plane path or is additive
- layout of the six-plane picker

## Out of scope
- X-ray select-through (#163 park) and panel chrome (#167 park: panel labels and always-visible chrome). Those stay queued after this slice.
- Truck TBD parts / printer send.
- Rust #4. `.cadmvp` freeze stays TBD.
- Overnight locks **(c)** and **(d)**, the Q5 discuss locks, and the export acceptance checks. Do not rewrite them.
- Inventing dimensions, hex colors, control ids, CSS selectors, pixel sizes, or icon art.
- Kernel / C++ / wasm rebuild. Do not commit `.wasm`, `web/cadcam.wasm`, or `web/dist/`. Do not edit `UPDATES.md`, `research/`, or a root `PROGRESS.md`.

## Smoke
Manual wake smoke on Pages. No new smoke harness. Reuse `tests/deploy_smoke.py` only if clearly required; this brief does not require it. No invented pixel asserts. Because no smoke path is added here, do not print a done marker.

1. While a sketch process is active, non-sketch floating shelves that crowd the view are minimized or hidden.
2. While a sketch process is active, only sketching tools stay visible (the sketch tool strip).
3. Press Create, then pick any of Front, Back, Top, Bottom, Left, Right.
4. After a plane/view is chosen, the view-selection menu is hidden.
5. After a plane/view is chosen, only sketch-create tools are shown.
6. **Finish Sketch** remains available.

## Success Criteria
Must PASS at tip-match. Cite the two park bullets in `mvp/requirements.md` (Erik via 3T, 2026-10-26 ~4:40 PM MT). Only Erik-stated behavior is on this bar.

1. While a sketch process is active, non-sketch floating shelves that crowd the view are minimized/hidden.
2. While a sketch process is active, only sketching tools stay visible (the sketch tool strip).
3. Sketch start: Press Create → user can pick any of the six orthographic views/planes: Front, Back, Top, Bottom, Left, Right.
4. After a plane/view is chosen, the view-selection menu is hidden.
5. After a plane/view is chosen, only sketch-create tools are shown.
6. **Finish Sketch** remains available.

Outside this hard bar: control ids, pixel sizes, hex/colors, which exact DOM nodes map to “sketch tool strip” vs “non-sketch chrome”, whether always-visible chrome (top / tools / bottom park) stays during sketch, Arc dialog redesign beyond viewport crowding, Create vs New Sketch label if they differ, face-tap plane path interaction, the X-ray and panel-chrome parks, Rust #4, `UPDATES.md`, and `research/`.

## Done
Draft until tip-match: Doc Steward primary (COMMENT), Research Digest second. Author does not self-APPROVE. Repo Keeper undrafts and plain-merges. After this file is on main, Pilot runs one Antigravity-only `agy` from it. If that `agy` exits with a dirty tree and no commit, Pilot commits and drafts the implementation PR — no second `agy`. Report the prompt PR link and tip SHA. Pilot reports any implementation PR separately.
