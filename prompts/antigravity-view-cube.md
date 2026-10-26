# Antigravity view-cube swipe adjacent (overnight queue item 3)

Team-locked overnight order (2)->(4)->(3)->(1) after Rust #1. Lock **(c)** from `mvp/requirements.md` (Chief/3T, 2026-10-26): view cube = **adjacent** face step; map swipe so direction matches "flip with swipe". **Not** opposite-face. Authored by Doc Steward from Research Digest lock-(c) shortlist + Chief T2 keep-L/R lock (2026-10-26 ~5:48 AM MT). This file is the Antigravity feed. It does not change the app by itself.

**Hard lock:** Implementation is **Antigravity-only on ErmoZ13**. Do **not** use Grok Build or Cursor for the handoff into code. Pilot owns the Antigravity run after this brief is on main. Suggested worktree: `C:\Dev\cadcam-antigravity-view-cube` on `feat/antigravity-view-cube`. Keep `C:\Dev\cadcam-mvp` main clean. No (1) until (3) tips.

**Pick:** Align view-cube **swipe** with lock (c): adjacent face only; swipe direction matches "flip with swipe". Face/corner taps, Home, and dominant-axis path stay.

Units: **mm**. Gate: OCCT validity + units (watertight dropped). Do **not** reopen phone T2. Do not remove `#dimPanel`. Do not implement queue (2)(4)(1) here.

Sources: lock (c) + wake smoke #5 in `mvp/requirements.md`; Digest lock-(c) shortlist; Chief T2 keep-L/R (2026-10-26); `web/view-cube.mjs` (`nextCubeFace`, `swipeDirection`); `web/index.html` cube gesture; `tests/view_cube_swipe_smoke.py`; `test_view_cube.mjs`; `prompts/nav-cube-mobile.md`.

## Context
- WASM UI: `web/view-cube.mjs` + cube gesture in `web/index.html`. Keep adjacent-only — no opposite-face jump. Horizontal ring already maps `left` → `FACE_RING[(i+1)%4]` (Front→Right).
- Prefer JS/HTML/CSS + existing view-cube helpers. **No** kernel, C++, `src/`, `web/bindings.cpp`, or `cadcam.wasm` rebuild. Do **not** add a second cube or three.js ViewHelper widget.
- Do not commit `.wasm`, `web/cadcam.wasm`, or `web/dist/`. Do not edit `UPDATES.md`. Do not edit `research/`.
- Commit on a PR branch. Never push to main. Repo Keeper merges after tip-match + `ci.yml` green.

## Team-chosen behaviour

### T1 — Keep adjacent-only + taps / Home / layout
Keep adjacent-only (no opposite jump). Tap / double-tap Home / current phone size / dominant-axis path unchanged. Do not regress face/corner snaps or mm / OCCT-after-ops.

### T2 — Horizontal: keep current L/R (Chief lock)
**Locked:** keep current L/R mapping — `left` → ring +1 (Front→Right). Matches flip-with-swipe. **Do not invert** unless Erik’s wake says otherwise. Vertical stays adjacent-only (see T3).

### T3 — Vertical Top/Bottom stay adjacent
Vertical Top/Bottom and Top/Bottom side exits stay adjacent. Do not invent a new mapping.

### T4 — Existing smokes + optional assert
Existing swipe smokes stay green (`tests/view_cube_swipe_smoke.py`, `test_view_cube.mjs`, and any deploy/phone harness hooks). Optional assert: Front + swipe-left → Right (current ring +1). No new smoke file.

### T5 — Web + tests only
`web/view-cube.mjs` + `web/index.html` gesture + tests only. No kernel / wasm / `#dimPanel` / queue (1)(2)(4).

### T6 — Out of this slice + Antigravity gate
No (1) until (3) tips. Phone T2 reopen. `#dimPanel` remove. Opposite-face toggle. Second nav cube. L/R invert (held unless Erik wake).

## Wake smoke (manual / Pages)
1. Face tap Top / Front / corner still snaps; double-tap Home iso.
2. From Front, swipe left → Right (ring +1); adjacent step, not Back — wake #5 / lock (c).
3. Vertical Top/Bottom stay adjacent.
4. Existing view-cube swipe smokes green.

## Acceptance
- T1. Adjacent-only; taps/Home/layout/dominant-axis/mm/OCCT unchanged.
- T2. Keep current L/R (`left` → ring +1, Front→Right); no invert unless Erik wake.
- T3. Vertical Top/Bottom adjacent; no new mapping.
- T4. Existing swipe smokes green; optional Front+swipe-left→Right assert OK.
- T5. web/view-cube.mjs + gesture + tests only.
- T6. No (1)(2)(4) / phone-T2 / dimPanel-remove / opposite-face / invert / second cube / kernel / wasm.

## Out of scope
- Queue (1)(2)(4); opposite-face toggle; L/R invert; second cube; phone T2; `#dimPanel` remove; kernel/WASM; UPDATES in prompt PR; printer send.

## Done
`ci.yml` green on the **prompt** PR. Tip-match (Doc Steward primary; Digest second). Author does not self-APPROVE. Repo Keeper undrafts and plain-merges. Pilot runs Antigravity-only from this file after tip. Report PR link + tip SHA; Pilot reports the impl PR separately.
