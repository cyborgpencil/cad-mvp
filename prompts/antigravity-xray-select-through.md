# Antigravity X-ray select-through

Select-through-objects (click-through / pick past front faces) is allowed **only when X-ray is on**. When X-ray is **off**, pick must hit the **frontmost surface only** — no click-through to objects behind. This file is the Antigravity feed. It does not change the app by itself.

**Gate:** Next coding slice after panel labels + always-visible chrome tip-merged on main (#193 merge `b99f5f9` / tip `146cb9e`; UPDATES #194 merge `70c522d` / tip `f7b8db6`). iPad/Kiwi held for Erik OK. Rust #4 HOLD (no `.cadmvp` freeze).

**Hard lock:** Implementation is **Antigravity-only on Z13**. Pilot holds one `agy` until this file tip-matches on main, then owns one `agy`. Do not use Grok Build or Cursor for the handoff into code. Prefer worktree `C:\Dev\cadcam-mvp` if Pilot says otherwise; do not invent a new path or create folders from this brief. Do not commit from Antigravity; Pilot/Repo Keeper commit path owns that. Do not invent Erik specs. No kernel, C++, `src/`, bindings, or wasm rebuild unless an existing web pick path clearly requires a tiny JS-only change in `web/` — stay in `web/` (JS, HTML, CSS). Prefer reusing whatever X-ray / pick path already exists; if none exists, implement only the Erik-stated on/off select-through rule without inventing a new control name or location.

**Source of truth:** The parked bullet in `mvp/requirements.md` under **Queued after current in-flight (discuss / parked)** named exactly **X-ray select-through**. Merged via PR #163 (tip `e69494d` / merge `c5ec1a3`). Erik via 3T, 2026-10-26 ~9:44 AM MT. Cite that bullet only. Anything it does not state stays **TBD**.

## Goal
Implement these sourced behaviors in `web/` (JS, HTML, and CSS). No kernel, C++, `src/`, bindings, or wasm rebuild.

Copied from the park bullet:

- **X-ray select-through**
  - Select-through-objects (click-through / pick past front faces) is allowed **only when X-ray is on**.
  - When X-ray is **off**, pick must hit the **frontmost surface only** — no click-through to objects behind.
  - **Status: discuss / parked.** Implement only after L-bracket `agy` and the rest of the current coding queue clear. No Antigravity prompt yet.
  - **TBD:** what the app’s X-ray control is named/where it lives, any pick-tolerance or depth-buffer details not stated by Erik.

The status lines are the park’s status in `mvp/requirements.md`. This file is the Antigravity feed those lines said was not written yet. Do not edit `mvp/requirements.md` from this brief. Start only when the Gate is met. Where a line is **TBD**, leave it TBD.

## Workflow
1. Read the park bullet named above. Copy behavior from that bullet only.
2. When X-ray is **on**, allow select-through-objects (click-through / pick past front faces).
3. When X-ray is **off**, pick hits the **frontmost surface only** — no click-through to objects behind.
4. Where the park marks a detail **TBD**, leave it TBD. Do not fill the gap with a guessed value. Do not invent the X-ray control’s name or where it lives. Do not invent pick-tolerance or depth-buffer numbers. If an X-ray on/off control already exists in `web/`, reuse it; if it does not, do not invent a new named control, placement, hotkey, or icon — leave that TBD and implement only the pick rule gated on whatever existing X-ray state the app already exposes (or document the gap in the PR without inventing UI).

## Do not bake / TBD
Do not invent and do not bake any of the following. Park TBDs stay **TBD**, verbatim:

- what the app’s X-ray control is named
- where the X-ray control lives
- any pick-tolerance not stated by Erik
- any depth-buffer details not stated by Erik

Do not invent any of the following. Erik did not state them:

- control ids
- CSS selectors
- pixel sizes
- hex colors
- icon art
- hotkeys
- new toolbar placement for an X-ray toggle

## Out of scope
- Panel labels + always-visible chrome (#167 park / #191 brief / #193 impl). Already on main. Do not re-spec them.
- Sketch chrome #183/#186 and sketch draw overhaul #185/#189. Already on main. Do not re-spec them.
- iPad/Kiwi. Held for Erik OK.
- Rust #4 HOLD. No `.cadmvp` freeze.
- This brief does not edit `mvp/requirements.md`.
- Kernel / C++ / wasm rebuild. Do not commit `.wasm`, `web/cadcam.wasm`, or `web/dist/`. Do not edit `UPDATES.md`, `research/`, or a root `PROGRESS.md`.

## Smoke
Manual wake smoke on Pages. No new smoke harness. Reuse `tests/deploy_smoke.py` only if that reuse is clearly required; this brief does not require it. No invented pixel asserts. Because no smoke path is added here, do not print a done marker.

Check Erik-stated behavior only. Do not assert control names, control placement, pick-tolerance values, or depth-buffer details.

1. With X-ray **on**, select-through-objects (click-through / pick past front faces) is allowed.
2. With X-ray **off**, pick hits the **frontmost surface only** — no click-through to objects behind.

## Success Criteria
Must PASS at tip-match. Cite the park bullet **X-ray select-through** in `mvp/requirements.md` (Erik via 3T, 2026-10-26 ~9:44 AM MT; PR #163 tip `e69494d` / merge `c5ec1a3`). Only Erik-stated behavior is on this bar.

1. With X-ray **on**, select-through-objects (click-through / pick past front faces) is allowed.
2. With X-ray **off**, pick hits the **frontmost surface only** — no click-through to objects behind.

Outside this hard bar: X-ray control name, where the control lives, pick-tolerance, depth-buffer details, control ids, CSS selectors, pixel sizes, hex colors, icon art, hotkeys, new toolbar placement, panel labels (#167/#191/#193), sketch chrome #183/#186, sketch draw overhaul #185/#189, iPad/Kiwi, Rust #4, `mvp/requirements.md`, `UPDATES.md`, and `research/`.

## Done
Draft until tip-match: Doc Steward primary (COMMENT), Research Digest second. Author does not self-APPROVE. Repo Keeper undrafts and plain-merges. After this file is on main, Pilot runs one Antigravity-only `agy` from it. Report the prompt PR link and tip SHA. Pilot reports any implementation PR separately.
