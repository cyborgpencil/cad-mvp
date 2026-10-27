# Antigravity iPad/Kiwi gestures + float-dock

Touch-first gesture family and a dockable-or-draggable floating panel so the viewport stays clear. This file is the Antigravity feed. It does not change the app by itself.

**Gate:** Next coding slice after X-ray select-through tip-merges on main (#197 tip `d0514a4` / brief #195 merge `aa635b6`). Theme feature stays after this. Rust #4 HOLD (no `.cadmvp` freeze).

**Hard lock:** Implementation is **Antigravity-only on Z13**. Pilot holds one `agy` until this file tip-matches on main, then owns one `agy`. Do not use Grok Build or Cursor for the handoff into code. Prefer worktree `C:\Dev\cadcam-mvp` if Pilot says otherwise; do not invent a new path or create folders from this brief. Do not commit from Antigravity; Pilot/Repo Keeper commit path owns that. Do not invent Erik specs. No kernel, C++, `src/`, bindings, or wasm rebuild — stay in `web/` (JS, HTML, CSS). Prefer reusing existing floating panels / touch handlers; if none fit, implement only the Erik-stated behaviors without inventing control names, placement, hotkeys, or icons beyond what this brief states.

**Source of truth (Erik locks only):**

- Erik via 3T, 2026-10-26 ~6:31 PM MT (research) and ~8:47 PM MT (OK to implement after X-ray): prefer **tap / long-press / double / triple-tap**; **dockable-or-draggable floating panel** so the viewport stays clear; **keep live dims**.
- Pattern sources for invent-free summary (Doc/Dig; Erik OK): **Shapr3D** + **Onshape Mobile** for touch gesture family; **Foundry Modo** for float/dock (Thumb tear-off → float; drag-to-edge → dock). Chief relay 2026-10-26 ~9:49 PM MT: Modo dock **L/R**; **triple-tap TBD**.
- Dig research: box `research/ipad-cad-kiwi-modo-gestures-panels.md` (not a second source of locks).

Anything these locks do not state stays **TBD**.

## Goal
Implement these sourced behaviors in `web/` (JS, HTML, and CSS). No kernel, C++, `src/`, bindings, or wasm rebuild.

Copied from Erik locks / Chief relay:

- Prefer the gesture family **tap**, **long-press**, **double-tap**, and **triple-tap** for touch interaction where the app already handles pointer/touch (do not invent a full secret gesture language).
- Provide a **floating panel** that can **float (drag)** or **dock left or right** (Modo-style dock L/R) so the **viewport stays clear**.
- **Keep live dims** — do not regress dims-stay while drawing (already on main from sketch-draw overhaul). This brief does not re-spec dim confirm model.
- **Triple-tap** mapping is **TBD** — do not invent an action for triple-tap.
- Exact per-gesture action map (what tap vs long-press vs double-tap does for select / context / clear / zoom) is **TBD** where Erik did not lock an action — do not bake Shapr-only or Onshape-only mappings as if Erik locked them. Prefer wiring the gesture *family* and the float/dock panel; leave unmapped actions TBD in the PR.

## Workflow
1. Read the Erik locks above. Copy behavior from those locks only.
2. Ensure touch input can recognize tap / long-press / double-tap / triple-tap as distinct events where touch is already handled. Do not invent pixel thresholds or timings Erik did not state — reuse existing touch timing/tolerance if present; otherwise leave thresholds **TBD** and do not invent numbers.
3. Implement a floating panel that the user can drag and dock to the **left or right** edge (Modo dock L/R pattern). Viewport must remain usable (panel does not permanently eat the work area).
4. Where a detail is **TBD**, leave it TBD. Do not invent control ids, CSS selectors, pixel sizes, hex colors, icon art, hotkeys, or new toolbar placements beyond “float + dock L/R”.
5. Do not regress live dims while drawing.

## Do not bake / TBD
Do not invent and do not bake any of the following. Park TBDs stay **TBD**, verbatim:

- triple-tap action mapping
- exact action for tap vs long-press vs double-tap (select / context / clear / zoom / etc.) unless already present in the app
- touch timing / pixel thresholds Erik did not state
- dock snap pixel sizes; top/bottom dock (brief locks L/R only)
- control ids, CSS selectors, hex colors, icon art, hotkeys
- phone vs desktop layout exceptions Erik did not state
- “Kiwi Modo” as a different product than Foundry Modo (name gap — Foundry Modo is the float/dock pattern source)

## Out of scope
- X-ray select-through (#163 / #195 / #197). Do not re-spec.
- Theme Default + Modo (next after this brief). Do not implement theme tokens here.
- Panel labels + always-visible chrome already on main. Do not re-spec.
- Sketch chrome / sketch-draw overhaul already on main. Do not re-spec dims beyond “do not regress”.
- Rust #4 HOLD. No `.cadmvp` freeze.
- This brief does not edit `mvp/requirements.md` unless Doc separately parks a bullet.
- Kernel / C++ / wasm rebuild. Do not commit `.wasm`, `web/cadcam.wasm`, or `web/dist/`. Do not edit `UPDATES.md` or a root `PROGRESS.md`.

## Smoke
Manual wake smoke on Pages. No new smoke harness. Reuse `tests/deploy_smoke.py` only if that reuse is clearly required; this brief does not require it. No invented pixel asserts. Because no smoke path is added here, do not print a done marker.

Check Erik-stated behavior only:

1. Touch path exposes tap / long-press / double-tap / triple-tap as distinct events (triple-tap may be recognized with **no action** — TBD).
2. A floating panel can be dragged and docked to the **left or right** so the viewport stays clear.
3. Live dims while drawing are not regressed.

## Success Criteria
Must PASS at tip-match. Cite Erik via 3T 2026-10-26 ~6:31 PM MT / ~8:47 PM MT and Chief Modo dock L/R + triple-tap TBD. Only Erik-stated behavior is on this bar.

1. Touch gesture family tap / long-press / double-tap / triple-tap is recognized (triple-tap action stays TBD — no invented binding).
2. Floating panel can float (drag) and dock **left or right**; viewport stays clear.
3. Live dims while drawing are not regressed.

Outside this hard bar: exact gesture→action map, touch timings/px, control ids, CSS selectors, hex colors, icon art, hotkeys, top/bottom dock, theme tokens, X-ray, Rust #4, `mvp/requirements.md`, `UPDATES.md`, and `research/`.

## Done
Draft until tip-match: Doc Steward primary (COMMENT), Research Digest second. Author does not self-APPROVE. Repo Keeper undrafts and plain-merges. After this file is on main, Pilot runs one Antigravity-only `agy` from it. Report the prompt PR link and tip SHA. Pilot reports any implementation PR separately. Theme invent-free brief follows this merge.
