# MVP wrap-up: debug UI out, default cube, Modify menu

Source: Erik 2026-10-22 08:40 MT via 3T. Items 1-3 of the wrap-up list. The Chief assigns the owner; 3T noted Pilot folds items 1-2 into the next Grok Build batch with the badge and banner fixes.

## Rules
- Web layer only (`web/`). No kernel edits in `src/`. Erik reviews the `index.html` diff.
- Units stay visible and keep gating Export. The OCCT shape-validity check after operations stays, routes to the log, and never blocks Export. Watertight checks are dropped (Erik 02:17 MT).
- Keep the 390x844 phone layout rules: 44 px targets, the single-row tool shelf, and the viewport-clear check.
- Commit incrementally on a branch and open a PR. Never push to main directly.

## 1. Debug and test UI out, info into a log
Remove from the UI:
- The `#occtBanner` interim banner (`Interim build: OCCT check pending`).
- Every Watertight badge: `#statusTight` on the status bar and `#gateTight` in the Export gate panel, plus the gate title and fine-print text that mention watertight.
- The File menu fixture loaders (`loadFixture` buttons for closed, open and 20 mm boxes) and any other test-only readouts, such as op-log or raw-gate text. Query fixtures (`?fixture=`, `?demo=`) can stay for tests but get no UI.

Route that information to a log:
- Every check result (OCCT validity, free-edge count, units, volume, op results and errors) goes to `console.info`/`console.warn` with a `[cadmvp]` prefix, and into an in-memory log.
- Add one Download log action (team-chosen place: File menu) that saves the in-memory log as `cadmvp-log.txt`, plain text, one line per event with an ISO timestamp.
- Keep shown to the user: the Units readout and a clean error message when an operation fails or Export is blocked by units.

## 2. Default model: a 20 x 20 x 20 mm cube
- On first load with no query, the scene holds one solid box primitive, 20 x 20 x 20 mm, through the same path as Create > Box, so it's editable, selectable and saved like any box. It replaces the `open_box` mesh fixture as the default (`web/bindings.cpp` `g_mesh`/`g_fixture` and the page's start-up load).
- Placement: team-chosen, centred on the origin with its base on the ground plane (z 0 to 20).
- Undo starts empty after load (call the undo stack's clear).

## 3. Modify menu on the bottom bar
- Add a Modify button on the bottom bar right after Create, same style, icon team-chosen.
- Tapping or clicking Modify toggles the tool shelf (the modify tools: move, rotate, resize, fillet, chamfer, Boolean, delete as present on main). Shown: one row only. Hidden: the viewport gains the space.
- `aria-expanded` reflects the state. Esc closes it on desktop. Opening Create closes the shelf, and the reverse.
- Team-chosen default: the shelf starts hidden on phones and shown on desktop.

## Tests (CI must stay green)
- Deploy smoke at 390x844 and desktop:
  - There's no banner, no Watertight text anywhere in the DOM, and no fixture loaders.
  - Units shows `mm`.
  - The default scene is one box with volume 8000 mm3 within 0.01 and bounding box 20x20x20 within 0.01.
  - Modify toggles the shelf, which shows as one row, and the viewport-clear rule holds with the shelf hidden.
  - Download log produces a non-empty file with `[cadmvp]`-style lines.
  - No console errors.
- Remove or update the old tests that asserted the banner, the badges or the `open_box` default. The `occt_gate` Node test can keep its fixtures.

## Report
- PR link and head.
- The CTest count, deploy smoke result, and one 390x844 screenshot saved to `C:\Users\cybor\Pictures\cadmvp-shots\` on Z13.
- Files changed.
- Any team-chosen values you changed, so Doc Steward can log them in `web/PROGRESS.md`.