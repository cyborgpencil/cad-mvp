# Item 2: Nav cube visible on mobile
Make the nav cube visible and usable on a ~390 px phone. Tap a face, edge or corner to snap the view; it stays at least 44 px per tap zone. It must not overlap the Create bottom bar, the property bottom sheet (open or closed), the top row, or the Home button, and it respects safe-area insets and 100dvh. The viewport-clear rule still holds (>=70% clear with panel collapsed, >=50% open). Print NAVCUBE_DONE.

## Rules for every session
- Work in C:\Dev\cadcam-mvp on Z13 only. Run git pull --ff-only first. Write no C++ kernel code unless the step needs it, and Erik reviews any core diff.
- Touch first: targets at least 44x44 CSS px. Test in portrait at 390x844 in Chromium and WebKit iPhone 13 profile.
- Every default is a team choice recorded in web/PROGRESS.md. Invent no Erik specs.
- The Blink bracket is a test fixture only: never shipped, never pushed.
- Units stay mm. Done means CTest with CI=1 passes (occt_gate Passed), deploy_smoke passes including the new tests, and the secrets/Blink scan is clean. Don't commit; Repo Keeper merges via PR after CI is green.

## Smoke tests (add to deploy_smoke, 390x844, Chromium and WebKit iPhone 13)
- Nav cube is visible and its bounding rect does not intersect the Create bottom bar, the bottom sheet, the top row or Home.
- Tapping Top, Front and one corner changes the camera to that view.
- Visible viewport fraction checks still pass. One screenshot per batch.
