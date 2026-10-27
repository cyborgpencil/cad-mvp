# Antigravity panel labels + always-visible chrome

Label every panel. The only panels that stay visible 100% of the time are the very top (tree + filename), the tools menu bar, and the very bottom (Modify / Create etc.). Everything else must not stay on-screen permanently; use show/hide like other shelves. This file is the Antigravity feed. It does not change the app by itself.

**Gate:** Next coding slice after sketch-draw overhaul tip-merged on main (#189 merge `72b6ef4` / tip `84223f4`). X-ray (#163) stays later. iPad/Kiwi held for Erik OK. Rust #4 HOLD (no `.cadmvp` freeze).

**Hard lock:** Implementation is **Antigravity-only on Z13**. Pilot holds one `agy` until this file tip-matches on main, then owns one `agy`. Do not use Grok Build or Cursor for the handoff into code. Prefer worktree `C:\Dev\cadcam-mvp` if Pilot says otherwise; do not invent a new path or create folders from this brief. Do not commit from Antigravity; Pilot/Repo Keeper commit path owns that. Do not invent Erik specs. No kernel, C++, `src/`, bindings, or wasm rebuild.

**Source of truth:** The two parked bullets in `mvp/requirements.md` under **Queued after current in-flight (discuss / parked)** named exactly **Panel labels** and **Always-visible chrome (permanent panels)**. Merged via PR #167 (tip `9fe9260` / merge `7b56e1a`). Erik via 3T, 2026-10-26 ~10:27 AM MT. Cite those two bullets only. Anything they do not state stays **TBD**.

## Goal
Implement these sourced behaviors in `web/` (JS, HTML, and CSS). No kernel, C++, `src/`, bindings, or wasm rebuild.

Copied from the two park bullets:

- **Panel labels**
  - Every panel must be labeled.
  - **Status: discuss / parked.** Implement only after the current coding queue clears. No Antigravity prompt yet.
  - **TBD:** exact label text per panel, which surfaces count as panels, and phone vs desktop label placement.
- **Always-visible chrome (permanent panels)**
  - The only panels that stay visible 100% of the time are: the **very top** (tree + filename), the **tools menu bar**, and the **very bottom** (Modify / Create etc.).
  - Everything else must not stay on-screen permanently; use show/hide like other shelves.
  - **Status: discuss / parked.** Implement only after the current coding queue clears. No Antigravity prompt yet.
  - **TBD:** which existing UI regions map to “very top / tools menu bar / very bottom”, which other panels currently stay permanent and must become shelves, and any exceptions Erik did not state.

The status lines are the park’s status in `mvp/requirements.md`. This file is the Antigravity feed those lines said was not written yet. Do not edit `mvp/requirements.md` from this brief. Start only when the Gate is met. Where a line is **TBD**, leave it TBD.

## Workflow
1. Read the two park bullets named above. Copy behavior from those bullets only.
2. Label every panel.
3. Keep visible 100% of the time only the **very top** (tree + filename), the **tools menu bar**, and the **very bottom** (Modify / Create etc.).
4. Everything else must not stay on-screen permanently. Use show/hide like other shelves.
5. Where the park marks a detail **TBD**, leave it TBD. Do not fill the gap with a guessed value. Do not choose label text, which surfaces count as panels, or phone vs desktop label placement. Do not map existing UI regions onto “very top / tools menu bar / very bottom”. Do not name which other panels become shelves. Do not add exceptions Erik did not state.

## Do not bake / TBD
Do not invent and do not bake any of the following. Park TBDs stay **TBD**, verbatim:

Panel labels:

- exact label text per panel
- which surfaces count as panels
- phone vs desktop label placement

Always-visible chrome (permanent panels):

- which existing UI regions map to “very top / tools menu bar / very bottom”
- which other panels currently stay permanent and must become shelves
- any exceptions Erik did not state

Do not invent any of the following. Erik did not state them:

- control ids
- CSS selectors
- pixel sizes
- hex colors
- icon art

## Out of scope
- Sketch chrome #183/#186 and sketch draw overhaul #185/#189. Both are already on main. Do not re-spec them. The overhaul already locks that while sketching, the very top (tree + filename) and the very bottom (Modify / Create) stay visible. Do not invent Arc dialog or sketch-strip rules here.
- X-ray select-through (#163 park). It stays later.
- iPad/Kiwi. Held for Erik OK.
- Rust #4 HOLD. No `.cadmvp` freeze.
- This brief does not edit `mvp/requirements.md`.
- Kernel / C++ / wasm rebuild. Do not commit `.wasm`, `web/cadcam.wasm`, or `web/dist/`. Do not edit `UPDATES.md`, `research/`, or a root `PROGRESS.md`.

## Smoke
Manual wake smoke on Pages. No new smoke harness. Reuse `tests/deploy_smoke.py` only if that reuse is clearly required; this brief does not require it. No invented pixel asserts. Because no smoke path is added here, do not print a done marker.

Check Erik-stated behavior only. Do not assert label strings, which surfaces count as panels, phone vs desktop placement, which regions map to very top / tools menu bar / very bottom, which other panels become shelves, or exceptions Erik did not state.

1. Every panel is labeled.
2. The only panels that stay visible 100% of the time are the very top (tree + filename), the tools menu bar, and the very bottom (Modify / Create etc.).
3. Everything else does not stay on-screen permanently. It uses show/hide like other shelves.

## Success Criteria
Must PASS at tip-match. Cite the two park bullets in `mvp/requirements.md` (Erik via 3T, 2026-10-26 ~10:27 AM MT; PR #167 tip `9fe9260` / merge `7b56e1a`). Only Erik-stated behavior is on this bar.

1. Every panel is labeled.
2. The only panels that stay visible 100% of the time are the very top (tree + filename), the tools menu bar, and the very bottom (Modify / Create etc.).
3. Everything else does not stay on-screen permanently. It uses show/hide like other shelves.

Outside this hard bar: exact label text per panel, which surfaces count as panels, phone vs desktop label placement, which existing UI regions map to “very top / tools menu bar / very bottom”, which other panels currently stay permanent and must become shelves, any exceptions Erik did not state, control ids, CSS selectors, pixel sizes, hex colors, icon art, sketch chrome #183/#186, sketch draw overhaul #185/#189, Arc dialog rules, sketch-strip rules, X-ray (#163), iPad/Kiwi, Rust #4, `mvp/requirements.md`, `UPDATES.md`, and `research/`.

## Done
Draft until tip-match: Doc Steward primary (COMMENT), Research Digest second. Author does not self-APPROVE. Repo Keeper undrafts and plain-merges. After this file is on main, Pilot runs one Antigravity-only `agy` from it. Report the prompt PR link and tip SHA. Pilot reports any implementation PR separately.
