# Prompt: interactive Booleans (union, cut, intersect) on selected bodies

Source digest: research/gui/booleans-fillet-chamfer.md. Values: web/PROGRESS.md (team-chosen 2026-10-21).

## Goal
In the WASM app, the user selects two bodies (hotkey 4 = whole-body select) and applies Union, Cut (first minus second, by selection order) or Intersect. The result replaces both inputs in the scene.

## Requirements
- Reuse the fuse/cut/common wrappers in web/occt-ops.mjs. Do not add a second Boolean path.
- Check IsDone() before calling Shape(). On failure, keep the last good shape, show a clear message and keep both inputs unchanged.
- Run the gate (OCCT validity, watertight, units mm) on every result. If the result fails the gate or is empty (e.g. Intersect of disjoint bodies), revert and show a message. Export stays locked unless the current scene passes.
- Free OCCT handles with delete(); no leaks across repeated ops.
- Selection order must be visible, since Cut depends on it.
- Strict MVP scope: no undo stack, no history tree, no multi-body (3+) Booleans.

## Tests (must pass before reporting done)
- Node gate test: union, cut and intersect of two overlapping 20 mm boxes each pass the gate with expected volumes; intersect of disjoint boxes is reported and reverted.
- Browser smoke test: select two bodies, apply each op, verify the gate passes and no page errors; plus a hotkey 4 key-press test.
- CTest with CI=1 stays 7/7 (or more), occt_gate Passed (not Skipped); deploy_smoke stays green; fixtures still 404.
- Pilot's own STL check on one result: watertight, mm, expected bounds.

## Rules
Do not commit. No src/ kernel changes unless required; flag any for Erik's review. Print BOOLEANS_DONE at the end.
