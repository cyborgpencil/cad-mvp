# Antigravity empty-sketch / no spawn box (overnight queue item 2)

Team-locked overnight order (2)->(4)->(3)->(1) after Rust #1. Lock **(b)** from `mvp/requirements.md` (Chief/3T, 2026-10-26). Authored by Doc Steward for Pilot Antigravity on Z13. This file is the Antigravity feed. It does not change the app by itself.

**Hard lock:** Implementation is **Antigravity-only on ErmoZ13**. Do **not** use Grok Build or Cursor for the handoff into code. Pilot owns the Antigravity run after this brief is on main. Worktree: `C:\Dev\cadcam-antigravity-empty-sketch` on `feat/antigravity-empty-sketch` (already staged off main). Keep `C:\Dev\cadcam-mvp` main clean.

**Pick:** Fix Create Sketch on an empty document so it **never spawns a solid/box**. Keep the **boot cube** on a fresh session. Empty path must open the origin-plane picker (`#originPlanes`) with `state.bodies.length === 0`.

Units: **mm**. Gate: OCCT validity + units (watertight dropped). Do not reopen phone T2, Arc/Polygon polish, P1-P5, `#dimPanel` remove, or Rust gate rewrite.

Sources: lock (b) in `mvp/requirements.md`; `prompts/origin-plane-empty-doc.md` (T5 empty predicate); `prompts/antigravity-basic-sketch.md` (sketch chrome); shipped origin-plane empty-doc #77.

## Context
- WASM UI in `web/` (mostly `web/index.html`, plus related JS). Antigravity-only on the empty-sketch worktree.
- Fresh load still seeds the default **20 mm boot cube**. That is intentional — **do not remove** the boot cube.
- Create → Sketch is `data-action="newSketch"`. Empty doc path should show `#originPlanes` (Top/Front/Right) when `state.bodies.length === 0` (see `prompts/origin-plane-empty-doc.md` T5). Face-tap path when bodies exist stays unchanged.
- Bug to kill: some Create Sketch / empty path still creates a box (or other solid) so `bodies.length` is no longer 0 and `#originPlanes` never appears (or appears after an unwanted solid).
- Prefer JS/HTML/CSS + existing libcascade bindings. **No** kernel, C++, `src/`, `web/bindings.cpp`, or `cadcam.wasm` rebuild. If a needed binding is missing, mark TBD and stop.
- Do not commit `.wasm`, `web/cadcam.wasm`, or `web/dist/`. Do not edit `UPDATES.md`. Do not add or edit a root `PROGRESS.md`. Do not edit `research/`.
- Commit on a PR branch. Never push to main. Repo Keeper merges after tip-match + `ci.yml` green.

## Team-chosen behaviour

### T1 — Keep boot cube
A normal new session / fresh Pages load still has the default 20 mm cube. Do not delete the seed cube to "fix" the empty path.

### T2 — Empty Create Sketch never spawns a solid
When the document is empty (`state.bodies.length === 0` after delete-all or equivalent), Create → Sketch must:
1. **Not** add a box, cube, or any other body.
2. Show `#originPlanes` (Top / Front / Right) for plane pick.
3. Leave `state.bodies.length === 0` until the user finishes a sketch and extrudes (or otherwise intentionally creates a body).

Find the spawn site (likely a fallback that creates a sketch plane by inserting a temporary solid, or a stale path that re-seeds a cube). Remove or gate that path so empty Create Sketch is picker-only.

### T3 — Body-present path unchanged
With at least one body (including the boot cube), Create → Sketch keeps the planar face-tap path. Origin picker stays off while `bodies.length !== 0`.

### T4 — Smoke hooks
Reuse existing smoke harness only (`tests/deploy_smoke.py`; phone via existing portrait path). No new smoke file.

Primary smoke (must pass):
1. Start from a state with bodies (boot cube or fixture).
2. Delete-all / `ensureEmpty` so `state.bodies.length === 0`.
3. Create → Sketch (`newSketch`).
4. Assert `state.bodies.length === 0`.
5. Assert `#originPlanes` is visible (or equivalent published flag already used by origin-plane smoke).
6. Assert no new body id appeared.

Regression:
- Fresh load still has boot cube (`bodies.length >= 1` before delete-all).
- With boot cube present, Create → Sketch does **not** force origin picker; face tap still works.
- Existing `portrait_origin_plane_problems` / origin-plane extrude cases stay green after a deliberate empty-doc plane pick + rect/circle (or line) extrude.

### T5 — Phone
No new chrome required. If any control is touched, keep ≥ 44 CSS px and do not cover the bottom bar / Home / Export / units. Portrait 390×844.

## Acceptance
- T1. Fresh session still seeds the 20 mm boot cube.
- T2. After delete-all: Create Sketch → `bodies.length === 0` and `#originPlanes` visible; no spawned box.
- T3. With bodies present: face-tap sketch path unchanged; origin picker not forced.
- T4. deploy_smoke (and portrait path if touched) green with the new empty-sketch assert.
- T5. No wasm/kernel diff. No phone-T2 / dimPanel / Rust-gate edits.

## Out of scope
- Queue (1) sketch+dimensioning/viz, (3) view-cube swipe, (4) selection gizmo hide — later in locked order.
- Removing the boot cube.
- Constraint solver / PlaneGCS.
- Kernel / WASM rebuild; `UPDATES.md`; speculative Arc/Polygon retune.
- Printer send.

## Done
`ci.yml` green on the PR. Tip-match reviews (Doc Steward primary on this **prompt** PR; Digest second if needed). Author does not self-APPROVE. Repo Keeper undrafts and plain-merges. After the prompt is on main, Pilot runs Antigravity-only from this file on `C:\Dev\cadcam-antigravity-empty-sketch`. Report the PR link and tip SHA for the prompt; Pilot reports the impl PR separately.
