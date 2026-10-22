# Item 2: Nav cube visible on mobile
Make the nav cube visible and usable on a ~390 px phone. Tap a face, edge or corner to snap the view; it stays at least 44 px per tap zone. It must not overlap the Create bottom bar, the property bottom sheet (open or closed), the top row, or the Home button, and it respects safe-area insets and 100dvh. The viewport-clear rule still holds (>=70% clear with panel collapsed, >=50% open). Print NAVCUBE_DONE.

## Rules for every session
- Work in a fresh clone on a PR branch off main. Never push to main. Any C++ or bindings change goes in its own commit and is flagged for Erik review.
- Touch first: targets at least 44x44 CSS px. Test in portrait at 390x844 in Chromium 390x844 in CI; WebKit per the phone-fix harness if present.
- Every default is a team choice recorded in web/PROGRESS.md. Invent no Erik specs.
- The Blink bracket is a test fixture only: never shipped, never pushed.
- Units stay mm. Done means CTest with CI=1 passes (occt_gate Passed), deploy_smoke passes including the new tests, and the secrets/Blink scan is clean. Don't commit; Repo Keeper merges via PR after CI is green.

## Smoke tests (add to deploy_smoke, 390x844, Chromium in CI; WebKit per phone-fix harness if present)
- Nav cube is visible and its bounding rect does not intersect the Create bottom bar, the bottom sheet, the top row or Home.
- Tapping Top, Front and one corner changes the camera to that view.
- Visible viewport fraction checks still pass. One screenshot per batch.

## Done means
- ci.yml is green on the PR, then Repo Keeper merges. No direct merge by the agent.

## Pilot review fixes (2026-10-22)
- Adapt the existing #viewCube (placeViewCube, syncViewCube, pickViewCube in web/index.html). Do not add a second cube.
- Reuse the overlap selectors from the viewport-fraction checks already in tests/deploy_smoke.py.
- Snap test: after tapping each face, camera view direction matches that axis within 1 degree.
- Chief ruling: phone cube is 88 px visible, top-right, inset by safe area. 6 face taps plus 8 corner taps (iso views); edge taps desktop-only. Corner hit areas extend past the visible cube to at least 44 px each. Double-tap resets to home iso. Snaps animate in 250 ms or less.
- Do not add three.js ViewHelper (one cube only); borrowing its animated camera move is fine. Canvas keeps touch-action: none.
- Camera snap (from three.js r160 ViewHelper method, not the file; repo inlines r160 with no addons): rotate camera around the orbit target at fixed distance, ease over 250 ms or less, ignore taps while animating. Fire on pointerup but skip a tap that ends a drag so orbiting never triggers a snap. Source: https://github.com/mrdoob/three.js/blob/r160/examples/jsm/helpers/ViewHelper.js
