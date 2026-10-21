# Prompt: wire the approved GUI into the real app

Status: READY (Doc Steward, 2026-10-21). Target = **WASM only** (Erik, 2026-10-21 01:45 MT): one OCCT WASM app for desktop and mobile; the desktop/Qt path becomes this same WASM app.

## Goal
Connect the approved layout (`mvp/ui-redesign.md`, mockup in `mockup/index.html`) to real geometry so the status bar and Export show real results, not placeholders.

## Scope
- Tools: only those listed in `mvp/ui-redesign.md`. Chamfer is a user tool (Erik, 2026-10-21); sphere, cone and intersect are test-only. Whether the full Model tool set stays or is cut to five is TBD for Erik.
- FixGaps (the small-gaps fix) is OUT. It's TBD for Erik, so add no button or stub for it.
- Strict MVP scope: no features beyond the docs. Mark anything missing as TBD and stop. Don't invent it.

## Hard gates
1. **Real watertight check.** It replaces the placeholder FAIL in the status bar and reports PASS or FAIL from the actual mesh/solid.
2. **Real units check.** Units are locked to mm and the real volume is shown (it replaces the placeholder 8000 mm³).
3. **Export is gated.** STL and 3MF export stays disabled unless both checks pass, and the UI says why when it's disabled.
4. Add CTest cases for both checks and for the gated Export. All tests must pass.

## Working rules
- Work only in the dev folder on the dev PC. Use incremental commits, one per checkpoint. No force-push, reset or deletes.
- Erik reviews core diffs. Leave geometry-kernel changes as reviewable diffs.
- Keep the layout matching the approved design. Keep touch targets at 44×44 px or larger.

## Checkpoints
1. Plan only: list the files to touch and the target-specific approach, then stop for review.
2. Wire the status bar to the real watertight and units results, plus their tests.
3. Gate Export on those checks, plus its test.
4. Wire the tools for the agreed set.
5. Run CTest, then take screenshots: desktop (1440×900), phone portrait (390×844), phone landscape (844×390).

## Cap
Stop at 60 minutes, or at any checkpoint failure, and report what was done, what's left, the test results and the files changed.


## Target: WASM
- The watertight and units checks run in the OCCT WASM build in the browser, not in mockup JS.
- **Responsive:** the layout adapts to desktop width with breakpoints, and to phone rotation (portrait and landscape) using an orientation listener (`matchMedia('(orientation: ...)')` or `screen.orientation` change) plus a resize re-layout. Units stay visible and touch targets stay at 44 px or larger in all three layouts.
- **Hosted link:** it must run from GitHub Pages (static files, no custom headers). Build **single-threaded**: no `-pthread`, so the page needs no COOP/COEP headers (see `research/occt-wasm/pages-hosting.md`). Never commit the `.wasm`, because Actions builds and deploys it. Don't add a server. (Repo Keeper owns the Pages workflow; only green builds deploy.)
- Check against rotation checks R1–R5 in `research/gui/usability-checks.md` before reporting done.
- **OCCT source (Chief, 2026-10-21):** first choice is prebuilt libcascade 3.1.0 (OCCT 8.0.1, single-threaded), loaded as-is, calling `BRepCheck_Analyzer` and `ShapeAnalysis_FreeBounds` from JS. Our core stays its own small WASM. No Docker without Erik's OK. Fallback is OCCT `adm/scripts/wasm_build.bat`. The .wasm is fetched by Actions and never committed.
- **Interim deploy (Chief and 3T, 2026-10-21):** the first Pages build may go live with our own mesh checker, provided the page shows an 'Interim build: OCCT check pending' banner and Export stays disabled until the real OCCT watertight and units gate is green. It still needs Erik's push go-ahead.
