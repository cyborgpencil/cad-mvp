# Antigravity view cube, gizmo, and line dimensions

Implement the parked view-cube swipe, gizmo placement, and per-line length dimensions. This file is the Antigravity feed. It does not change the app by itself.

**Gate:** Next coding slice after top-bar shelf icons on main (#177 / UPDATES #178 @ `94001ae`). First of the remaining parked UI trio (view cube + gizmo + line dims) per Chief lock 2026-10-26 ~2:01 PM MT. X-ray (#163 park) and panel chrome (#167 park) stay queued after this.

**Hard lock:** Implementation is **Antigravity-only on Z13**. Pilot owns one `agy` after this file is on main. If `agy` exits with dirty tree and no commit (same as truck/topbar), Pilot commits + drafts the impl PR — no second `agy`. Do not use Grok Build or Cursor for the handoff into code. Suggested Pilot worktree: create or reuse a dedicated worktree under `C:\Dev\` only if Pilot already has one; do not invent a path or create folders from this brief. Prefer `C:\Dev\cadcam-mvp` if Pilot says otherwise. Do not commit from Antigravity; Repo Keeper / Pilot commit path owns commits. Do not invent Erik specs.

**Source of truth:** The three parked bullets in `mvp/requirements.md` under **Queued after current in-flight (discuss / parked)** named exactly **View cube**, **Gizmo fix**, and **Dimensions**. Parked via PR #160 (merge `4c1a7c2`). Erik via 3T, 2026-10-26 ~8:46 AM MT. Cite those three bullets for the new behavior. Overnight locks **(c)** and **(d)** stay as written in that file; this brief implements the three park bullets, not a rewrite of those locks. Chief lock (CAD CAM MVP) scopes the gizmo park bullets to **body/item** selection so lock **(d)** still wins in vertex / edge / face. Anything the park does not state stays **TBD**.

## Goal
Implement these sourced behaviors in `web/` (JS, HTML, CSS as needed). No kernel, C++, `src/`, bindings, or wasm rebuild.

### View cube
Copied from park #160:

- More predictable swipe: each swipe up, down, left, or right rotates the view cube and the camera in that direction. The direction is screen-relative and independent of the model orientation.
- **Press-and-hold** for a slow continuous view-cube and camera adjust.
- **Home** shortcut: center on the selected model when something is selected; otherwise center on **0,0,0**.
- **TBD:** pixel thresholds, hold timing, and the Home key binding.

Overnight lock **(c)** stays as written in `mvp/requirements.md`: view cube = **adjacent** face step; map swipe so direction matches “flip with swipe” (invert L/R if needed). Not opposite-face. This slice does not rewrite that lock. Success criterion 8 is the adjacent-face bar for this feed.

### Gizmo fix
**Chief lock (body/item vs V/E/F):**

- Lock **(d)** wins in V/E/F: **whole-body / move gizmo stays hidden** in vertex, edge, and face modes. It stays for body/item.
- Park #160 gizmo bullets (center / empty hide / non-multi retap move) apply to **body/item** selection only.
- Do **not** invent a V/E/F / vertex-mode selection gizmo. Tip FAIL if this brief or the implementation invents a V/E/F fill.

Park #160 wording, then the scope that applies:

- The gizmo centers on the selection (one selection, or a multi-component / multi-object selection). Apply that to one body/item, or a multi body/item selection.
- Tap empty space hides the gizmo or moves it off.
- With multi-select off, park #160 said: tap vertex 1, then vertex 2, and the gizmo moves from vertex 1 to vertex 2. Chief lock: do **not** invent a vertex-mode gizmo. Apply that retap move at **body/item** level only: successive body/item taps move the gizmo between bodies/items.
- **TBD:** any tap or pixel threshold not stated in the gizmo park bullet.

### Dimensions
Copied from park #160:

- Show a dimension on **each line**, with that line's length, as in other CAD apps.
- **TBD:** which dimension style.

## Workflow
1. Read the three park bullets named above, plus overnight locks **(c)** and **(d)**. Copy behavior from those sources only. Chief lock scopes gizmo center, empty-space hide, and non-multi retap to body/item.
2. Implement view-cube swipe (screen-relative, adjacent-face per lock **(c)**), press-hold continuous adjust, and Home center (selected model when something is selected; otherwise **0,0,0**).
3. Implement gizmo center-on-selection for body/item (single or multi), empty-space hide or move off, and non-multi retap move between bodies/items. Keep the whole-body gizmo hidden in V/E/F (lock **(d)**).
4. Implement a length dimension on each line.
5. Where the park marks a detail **TBD**, leave it TBD. Do not fill the gap with a guessed value.

## Do not bake / TBD
Do not invent and do not bake any of the following. They stay **TBD**, verbatim from the park:

- pixel thresholds
- hold timing
- the Home key binding
- any tap or pixel threshold not stated in the gizmo park bullet
- which dimension style

## Out of scope
- Other parked UI: top-bar shelf icons (already shipped), X-ray select-through, panel labels, always-visible chrome.
- Truck TBD parts / printer send.
- Rust #4.
- Inventing pixel thresholds, hold timings, the Home key binding, or dimension style.
- Inventing OCCT, watertight, or Export behavior for this UI slice.
- Kernel / C++ / wasm rebuild. Do not commit `.wasm`, `web/cadcam.wasm`, or `web/dist/`. Do not edit `UPDATES.md`, `research/`, or a root `PROGRESS.md`.

## Smoke
Manual wake smoke on Pages. No new smoke harness. Reuse `tests/deploy_smoke.py` only if clearly required; this brief does not require it. No invented pixel asserts. Because no smoke path is added here, do not print a done marker.

1. Swipe up, down, left, or right rotates the view cube and the camera in that screen direction, independent of model orientation.
2. Press-and-hold slowly and continuously adjusts the view cube and the camera.
3. Home centers on the selected model when something is selected; otherwise it centers on **0,0,0**.
4. On body/item selection, the gizmo centers on a single selection and on a multi body/item selection.
5. Tap empty space hides the gizmo or moves it off.
6. With multi-select off, successive body/item taps move the gizmo between bodies/items. No vertex-mode gizmo.
7. Each line shows a dimension with that line's length.
8. View-cube steps stay adjacent-face (overnight lock **(c)**). Not opposite-face.
9. The whole-body gizmo stays hidden in vertex / edge / face, and stays available for body/item (overnight lock **(d)**).

## Success Criteria
Must PASS at tip-match. Cite park #160 plus overnight locks **(c)** and **(d)**. Items 4–6 apply to **body/item** selection only.

1. Swipe up/down/left/right rotates the view cube **and** the camera; direction is **screen-relative**, independent of model orientation.
2. **Press-and-hold** = slow continuous view-cube + camera adjust.
3. **Home** centers on the **selected model** when something is selected; else **0,0,0**.
4. Gizmo **centers on the selection** (single or multi body/item).
5. Tap **empty space** hides the gizmo or moves it off.
6. With **multi-select off**: successive body/item taps move the gizmo between bodies/items. Park wording said vertex 1→2. Chief lock: do **not** invent a vertex-mode gizmo — apply the retap move at **body/item** level only.
7. A dimension on **each line**, with **that line's length** (line-by-line).
8. View cube stays **adjacent-face** step (overnight lock **c**). Not opposite-face.
9. Whole-body gizmo stays **hidden in V/E/F**; kept for body/item (overnight lock **d**).

Outside this hard bar: pixel thresholds, hold timing, the Home key binding, dimension style, the X-ray and panel-chrome parks, and any OCCT / watertight / Export change.

## Done
Draft until tip-match: Doc Steward primary (COMMENT), Research Digest second. Author does not self-APPROVE. Repo Keeper undrafts and plain-merges. After this file is on main, Pilot runs one Antigravity-only `agy` from it. If that `agy` exits with a dirty tree and no commit, Pilot commits and drafts the implementation PR — no second `agy`. Report the prompt PR link and tip SHA. Pilot reports any implementation PR separately.
