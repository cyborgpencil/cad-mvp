# Antigravity sketch + dimension viz (overnight queue item 1)

Team-locked overnight order (2)->(4)->(3)->(1) after Rust #1. Lock **(a)** from `mvp/requirements.md` (Chief/3T, 2026-10-26): precise = typed mm + callouts; **no** constraint solver. Authored by Doc Steward from Research Digest draft + Chief locks (T3 ii, T4 focus/show). This file is the Antigravity feed. It does not change the app by itself.

**Hard lock:** Implementation is **Antigravity-only on ErmoZ13**. Do **not** start worktree/`agy` until after (4) and (3) land (or Chief clears). Do **not** use Grok Build or Cursor for the handoff into code. Suggested worktree later: `C:\Dev\cadcam-antigravity-sketch-dims` on `feat/antigravity-sketch-dims`. Keep `C:\Dev\cadcam-mvp` main clean.

**Pick:** Improve sketch dimension / callout viz under lock (a). Keep shipped Create Sketch → Rect/Circle/Line/Arc/Polygon → Extrude path. Do not implement (2)(3)(4) here.

Units: **mm**. Gate: OCCT validity + units (watertight dropped). Do **not** reopen phone T2. Do not remove `#dimPanel`. No PlaneGCS / Trim / Offset / constraint solver.

Sources: lock (a) in `mvp/requirements.md`; Digest overnight-(1) draft; `prompts/antigravity-basic-sketch.md`, `prompts/sketch-line-followup.md`; PRs #70/#77/#83/#98/#108/#116/#118/#123; `sketchCalloutSpecs()` in `web/index.html`. Chief locks 2026-10-26 ~5:16 AM MT: T3 **(ii)**, T4 callout focus/show.

## Context
- WASM UI in `web/` (mostly `web/index.html`). Gap: Dimension/Trim/Offset chrome inert; Line/Arc lack typed mm + callouts; Polygon has typed N/Ø but no `#calloutLayer` rows.
- Prefer JS/HTML/CSS + existing libcascade bindings. **No** kernel, C++, `src/`, `web/bindings.cpp`, or `cadcam.wasm` rebuild. If a needed binding is missing, mark TBD and stop.
- Do not commit `.wasm`, `web/cadcam.wasm`, or `web/dist/`. Do not edit `UPDATES.md`. Do not edit `research/`.
- Commit on a PR branch. Never push to main. Repo Keeper merges after tip-match + `ci.yml` green.

## Team-chosen behaviour

### T1 — Keep shipped sketch / extrude / mm / OCCT
Do not regress Create→Sketch, face/origin plane, Rect/Circle/Line/Arc/Polygon, Finish, Blind Extrude New/Join/Cut, Measure, boot cube, millimetre units, or OCCT-after-ops validity.

### T2 — Polygon callouts on `#calloutLayer`
While the Polygon sheet is open, add Ø (and sides display) rows via `sketchCalloutSpecs` (or equivalent). Hide on close/extrude (same P6 rule as Rect/Circle). Typed N/Ø sheet fields stay authoritative.

### T3 — Line / Arc typed length/radius + callouts (Chief lock)
**Locked (ii):** typed length/radius rewrite + callouts (matches lock **(a)**). Optional typed length/radius fields rewrite the last segment/radius then Confirm; publish matching `#calloutLayer` rows. No PlaneGCS / display-only-only path.

### T4 — Dimension = callout focus/show (Chief lock)
Wire Dimension tool as **callout focus / show dims** only (reuse `#calloutLayer` + sheet fields). Trim/Offset/constraints stay inert. No solver.

### T5 — Phone + smoke
New tappables ≥44 CSS px; do not cover `.phone-tabbar` / `#vcHome` / `#exportBtn` / `#statusUnits`. Respect phone callout-hide for basic shapes + `#dimPanel` keep-lock. Reuse `tests/deploy_smoke.py` only — no new smoke file.

### T6 — Out of this slice
Queue (2) empty-sketch, (3) view-cube swipe, (4) V/E/F gizmo hide. Phone T2 reopen. `#dimPanel` remove. PlaneGCS / Trim / Offset / constraint solver. Kernel / wasm.

## Wake smoke (manual / Pages)
1. Boot cube + typed resize / `#dimPanel` Size still work.
2. Create Sketch → Rect 20×10 callouts → Extrude Blind 10 New → ~2000 mm³, unitsPass, OCCT gate.
3. Circle Ø10 callout → Extrude; Polygon N=6 Ø10 callout (**if T2 lands**) → Extrude.
4. Line triangle (0,0)/(10,0)/(0,10) → Extrude New ~500 mm³ (#108 regression).
5. Measure still reads on the cube.
6. **Not (1):** delete-all → New Sketch empty path (that is overnight **(2)**).

## Acceptance
- T1. Shipped sketch/extrude/mm/OCCT/boot-cube path unchanged.
- T2. Polygon sheet writes Ø (+ sides) to `#calloutLayer`; hide on close/extrude.
- T3. Line/Arc: typed length/radius rewrite + callouts (Chief ii).
- T4. Dimension: callout focus/show; Trim/Offset stay inert.
- T5. Phone ≥44 px; no cover bottom chrome; deploy_smoke green.
- T6. No (2)(3)(4) / phone-T2 / dimPanel-remove / solver / kernel / wasm.

## Out of scope
- Queue (2)(3)(4); constraint solver; `#dimPanel` remove; phone T2; kernel/WASM; UPDATES in prompt PR; printer send.

## Done
`ci.yml` green on the **prompt** PR. Tip-match (Doc Steward primary; Digest second). Author does not self-APPROVE. Repo Keeper undrafts and plain-merges. Pilot runs Antigravity-only from this file **only after (4)→(3)** (or Chief clears).
