# Antigravity top-bar shelf icons (selection + show/hide camera)

Move the selection sliding toolbar and the show/hide camera sliding toolbar into icons on the top bar. This file is the Antigravity feed. It does not change the app by itself.

**Gate:** Next coding slice after truck MVP Acceptance B on main (#171 `d8988d7` / UPDATES #172 `295cdca`). First parked UI slice per Chief.

**Hard lock:** Implementation is **Antigravity-only on Z13**. Pilot owns one `agy` after this file is on main. Do not use Grok Build or Cursor for the handoff into code. Suggested Pilot worktree already exists: `C:\Dev\cadcam-antigravity-topbar` on `feat/antigravity-topbar-shelf-icons`. Work there, or in `C:\Dev\cadcam-mvp` if Pilot says otherwise. Do not create folders from this brief. Do not commit; Repo Keeper commits. Do not invent Erik specs.

**Source of truth:** Parked bullet **Top-bar shelf icons (selection + show/hide camera)** in `mvp/requirements.md`, under **Queued after current in-flight (discuss / parked)**. Merged via PR #157 (tip `4397534` / merge `b0a5808`). Erik via 3T, 2026-10-26 ~8:31 AM MT. Cite that bullet only. Anything it does not state stays **TBD**.

## Goal
Implement these three sourced bullets in `web/` (JS, HTML, and CSS):

- Move the **selection** sliding toolbar and the **show/hide camera** sliding toolbar into **icons on the top bar, to the right of the tools menu**.
- Separate by tool type. Selection gets its own icon group. Any further tool-type groups are **TBD**.
- Same behavior as the tools menu: press the icon to show or hide that shelf.

Prefer the existing shelf show/hide pattern used by the tools menu. No kernel, C++, `src/`, bindings, or wasm rebuild.

## Workflow
1. Read the park bullet named above. Copy behavior from that bullet only.
2. In `web/`, add icons on the top bar, to the right of the tools menu, for the selection shelf and the show/hide-camera shelf.
3. Keep selection as its own icon group. Leave any further tool-type groups **TBD**.
4. Pressing an icon shows or hides that shelf, the same way the tools menu shows or hides its shelf.
5. Where the park marks a detail **TBD**, leave it TBD. Do not fill the gap with a guessed value.

## Do not bake / TBD
Do not invent and do not bake any of the following. They stay **TBD**, verbatim from the park:

- icon art
- pixel sizes
- hotkeys
- which existing controls are the selection shelf and which are the show/hide camera shelf
- which bar is the top bar (header or the ribbon that holds the Tools menu)
- phone and desktop placement
- whether any shelf besides those two moves

Any further tool-type groups are **TBD**.

## Out of scope
- Other parked UI: view cube, gizmo fix, dimensions, X-ray select-through, panel labels, always-visible chrome.
- Truck TBD parts.
- Rust #4.
- Printer send.
- Inventing icon art, pixel sizes, or hotkeys.
- Kernel / C++ / wasm rebuild. Do not commit `.wasm`, `web/cadcam.wasm`, or `web/dist/`. Do not edit `UPDATES.md`, `research/`, or a root `PROGRESS.md`.

## Smoke
Manual wake smoke on Pages. No new smoke harness. Reuse `tests/deploy_smoke.py` only if that reuse is clearly required; this brief does not require it. No invented pixel asserts. Because no smoke path is added here, do not print a done marker. (`TOPBAR_SHELF_ICONS_DONE` would apply only if a later smoke path is added.)

1. Top-bar icons appear to the right of the tools menu for the selection shelf and the show/hide-camera shelf.
2. Pressing an icon toggles that shelf show/hide the same way the tools menu does.
3. Selection is its own icon group.

## Done
Draft until tip-match: Doc Steward primary (COMMENT), Research Digest second. Author does not self-APPROVE. Repo Keeper undrafts and plain-merges. After this file is on main, Pilot runs one Antigravity-only `agy` from it. Report the prompt PR link and tip SHA. Pilot reports any implementation PR separately.
