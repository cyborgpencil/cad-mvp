# Antigravity selection V/E/F hide whole-body gizmo (overnight queue item 4)

Team-locked overnight order (2)->(4)->(3)->(1) after Rust #1. Lock **(d)** from `mvp/requirements.md` (Chief/3T, 2026-10-26). Authored by Doc Steward from Research Digest shortlist for Pilot Antigravity on Z13. This file is the Antigravity feed. It does not change the app by itself.

**Hard lock:** Implementation is **Antigravity-only on ErmoZ13**. Do **not** use Grok Build or Cursor for the handoff into code. Pilot owns the Antigravity run after this brief is on main (or Chief clears branch start). Suggested worktree: `C:\Dev\cadcam-antigravity-selection-gizmo` on `feat/antigravity-selection-gizmo-hide` (create off main after (2) lands or in parallel if Independent). Keep `C:\Dev\cadcam-mvp` main clean.

**Pick:** Hide the **whole-body** move/resize gizmo when selection is vertex, edge, or face. Keep the gizmo for Item / body selection. Typed-resize (#112) and existing Item gizmo behaviour stay.

Units: **mm**. Gate: OCCT validity + units (watertight dropped). Do **not** reopen phone T2. Do not remove `#dimPanel`. Do not implement queue (2)(3)(1) here.

Sources: lock (d) in `mvp/requirements.md`; Digest (4) shortlist (2026-10-26); Item gizmo hide-on-multi via #16; typed-resize #112; `gizmoShouldShow()` in `web/index.html`.

## Context
- WASM UI in `web/` (mostly `web/index.html`). Gap: `gizmoShouldShow()` falls through to `return true` on single-body V/E/F, so the whole-body gizmo still shows; multi-body already hides via Item (#16).
- Prefer JS/HTML/CSS + existing libcascade bindings. **No** kernel, C++, `src/`, `web/bindings.cpp`, or `cadcam.wasm` rebuild. If a needed binding is missing, mark TBD and stop.
- Do not commit `.wasm`, `web/cadcam.wasm`, or `web/dist/`. Do not edit `UPDATES.md`. Do not add or edit a root `PROGRESS.md`. Do not edit `research/`.
- Commit on a PR branch. Never push to main. Repo Keeper merges after tip-match + `ci.yml` green.

## Team-chosen behaviour

### T1 — Keep move / resize / stack / mm / OCCT
Do not regress body Item move, resize handles, stack order, millimetre units, or OCCT-after-ops validity. Typed-resize (#112) stays.

### T2 — Hide gizmo when selection is vertex / edge / face
When the active selection kind is `vertex`, `edge`, or `face` (including single-body V/E/F), `gizmoShouldShow()` (or equivalent) must return false so the whole-body gizmo is hidden. Fix the fall-through `return true` on single-body V/E/F.

### T3 — Item / body still shows + smoke green
Item (body) selection still shows the whole-body gizmo. Existing `gizmo_drag_smoke` (or current name) stays green: Item gizmo visible and a 10 mm drag still works.

### T4 — Clear-on-mode-switch + hide after V/E/F pick
Keep clear-on-mode-switch behaviour. After the user picks a V/E/F chip (or equivalent) and a sub-shape, the gizmo must hide. Returning to Item restores the gizmo.

### T5 — Touch zone + optional assert
No `GIZMO_TOUCH_ZONE` change. Optional smoke: after V/E/F pick, assert `gizmoVisible === false` (or the published flag already used by gizmo smoke). Reuse `tests/deploy_smoke.py` / existing harness only — no new smoke file.

### T6 — Out of this slice
Queue (2) empty-sketch, (3) view-cube swipe, (1) sketch+dims. Phone T2 reopen. `#dimPanel` remove. Sub-shape-specific gizmos (new vertex/edge/face manipulators).

**TBD (do not invent):** Whether dim-panel Move/Rotate/Resize chrome should also hide vs viewport handles only. Leave as-is unless already gated by `gizmoShouldShow()`; if unclear, mark TBD in the PR and stop expanding scope.

## Wake smoke (manual / Pages)
1. Item selection → whole-body gizmo on.
2. V/E/F chip + pick → gizmo off.
3. Back to Item → gizmo restore.
4. 10 mm Item drag still works.

## Acceptance
- T1. Item move/resize/typed-resize/mm/OCCT path unchanged.
- T2. Single-body V/E/F selection hides whole-body gizmo (`gizmoShouldShow` false).
- T3. Item selection shows gizmo; `gizmo_drag_smoke` green.
- T4. Mode switch + V/E/F pick hide; Item restores.
- T5. No `GIZMO_TOUCH_ZONE` change; optional `gizmoVisible===false` assert OK.
- T6. No phone-T2 / dimPanel-remove / (2)(3)(1) / kernel / wasm edits.

## Out of scope
- Queue (2)(3)(1); phone T2 reopen; `#dimPanel` remove; sub-shape gizmos.
- Kernel / WASM rebuild; `UPDATES.md`; constraint solver.
- Printer send.

## Done
`ci.yml` green on the PR. Tip-match reviews (Doc Steward primary on this **prompt** PR; Digest second if needed). Author does not self-APPROVE. Repo Keeper undrafts and plain-merges. After the prompt is on main (or Chief clears), Pilot runs Antigravity-only from this file. Report the PR link and tip SHA for the prompt; Pilot reports the impl PR separately.
