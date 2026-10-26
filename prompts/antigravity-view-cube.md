# Antigravity view-cube swipe adjacent (overnight queue item 3)

Team-locked overnight order (2)->(4)->(3)->(1) after Rust #1. Lock **(c)** from `mvp/requirements.md` (Chief/3T, 2026-10-26): view cube = **adjacent** face step; map swipe so direction matches "flip with swipe" (invert L/R if needed). **Not** opposite-face. Authored by Doc Steward from Research Digest lock-(c) shortlist + existing `#viewCube` / `view-cube.mjs`. This file is the Antigravity feed. It does not change the app by itself.

**Hard lock:** Implementation is **Antigravity-only on ErmoZ13**. Do **not** use Grok Build or Cursor for the handoff into code. Pilot owns the Antigravity run after this brief is on main (or Chief clears). Suggested worktree: `C:\Dev\cadcam-antigravity-view-cube` on `feat/antigravity-view-cube`. Keep `C:\Dev\cadcam-mvp` main clean. No (1) until (3) tips.

**Pick:** Align view-cube **swipe** with lock (c): adjacent face only; swipe direction matches "flip with swipe". Face/corner taps, Home, and dominant-axis path stay. Invert L/R on the ring only if wake #5 still feels wrong after adjacent is correct.

Units: **mm**. Gate: OCCT validity + units (watertight dropped). Do **not** reopen phone T2. Do not remove `#dimPanel`. Do not implement queue (2)(4)(1) here.

Sources: lock (c) + wake smoke #5 in `mvp/requirements.md`; Digest lock-(c) shortlist (2026-10-26 ~5:48 AM MT); `web/view-cube.mjs` (`nextCubeFace`, `swipeDirection`); `web/index.html` cube gesture; `tests/view_cube_swipe_smoke.py`; `test_view_cube.mjs`; `prompts/nav-cube-mobile.md`.

## Context
- WASM UI: `web/view-cube.mjs` + cube gesture in `web/index.html`. Gap: swipe direction / ring step may not match lock (c) "flip with swipe" (wake #5). Keep adjacent-only — no opposite-face jump.
- Prefer JS/HTML/CSS + existing view-cube helpers. **No** kernel, C++, `src/`, `web/bindings.cpp`, or `cadcam.wasm` rebuild. Do **not** add a second cube or three.js ViewHelper widget.
- Do not commit `.wasm`, `web/cadcam.wasm`, or `web/dist/`. Do not edit `UPDATES.md`. Do not edit `research/`.
- Commit on a PR branch. Never push to main. Repo Keeper merges after tip-match + `ci.yml` green.

## Team-chosen behaviour

### T1 — Keep adjacent-only + taps / Home / layout
Keep adjacent-only (no opposite jump). Tap / double-tap Home / 24px (or current phone size) / dominant-axis path unchanged. Do not regress face/corner snaps or mm / OCCT-after-ops.

### T2 — Horizontal swipe = flip-with-swipe (Chief lock c)
Horizontal: swipe direction must match "flip with swipe". Today `left` → `FACE_RING[(i+1)%4]` (Front→Right). Invert L/R on the ring **only** if wake #5 still feels wrong after adjacent step is confirmed.

### T3 — Vertical Top/Bottom stay adjacent
Vertical Top/Bottom and Top/Bottom side exits stay adjacent. Do not invent a new mapping.

### T4 — Existing smokes + optional assert
Existing swipe smokes stay green (`tests/view_cube_swipe_smoke.py`, `test_view_cube.mjs`, and any deploy/phone harness hooks). Optional assert: Front + swipe-left lands the face lock (c) picks (after invert decision). No new smoke file.

### T5 — Web + tests only
`web/view-cube.mjs` + `web/index.html` gesture + tests only. No kernel / wasm / `#dimPanel` / queue (1)(2)(4).

### T6 — Out of this slice + Antigravity gate
No (1) until (3) tips. Phone T2 reopen. `#dimPanel` remove. Opposite-face toggle. Second nav cube.

## Wake smoke (manual / Pages)
1. Face tap Top / Front / corner still snaps; double-tap Home iso.
2. From Front, swipe so the **adjacent** face steps in the swipe direction (not Back) — wake #5 / lock (c).
3. Invert L/R on the ring only if direction still feels wrong after adjacent works.
4. Existing view-cube swipe smokes green.

## Acceptance
- T1. Adjacent-only; taps/Home/layout/dominant-axis/mm/OCCT unchanged.
- T2. Horizontal swipe matches flip-with-swipe; L/R invert only if needed.
- T3. Vertical Top/Bottom adjacent; no new mapping.
- T4. Existing swipe smokes green; optional Front+swipe-left assert OK.
- T5. web/view-cube.mjs + gesture + tests only.
- T6. No (1)(2)(4) / phone-T2 / dimPanel-remove / opposite-face / second cube / kernel / wasm.

## Out of scope
- Queue (1)(2)(4); opposite-face toggle; second cube; phone T2; `#dimPanel` remove; kernel/WASM; UPDATES in prompt PR; printer send.

## Done
`ci.yml` green on the **prompt** PR. Tip-match (Doc Steward primary; Digest second). Author does not self-APPROVE. Repo Keeper undrafts and plain-merges. Pilot runs Antigravity-only from this file after tip. Report PR link + tip SHA; Pilot reports the impl PR separately.
