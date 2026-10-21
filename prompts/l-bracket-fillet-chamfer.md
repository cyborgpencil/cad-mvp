# Grok Build prompt: L-bracket fuse, fillet, chamfer (queued after CI session)

Source digest: research/gui/booleans-fillet-chamfer.md. Tooling: Grok Build first; Cursor second (edge pick to fillet panel wiring).

## Scope (strict MVP)
1. Wrap libcascade 3.1.0 fuse, cut, common, fillet, chamfer in web/ bindings (confirm exact method signatures from the 3.1.0 type definitions first; do not guess).
2. After EVERY op run the gate: OCCT validity + watertight + units (mm locked). On failure keep the last good shape, show the error, never call Shape() when IsDone() is false (catch the throw).
3. Handle lifetime: from 3.1.0 delete() really frees; never delete a handle still referenced.
4. L-bracket demo: fuse two boxes, fillet inner edge, chamfer chosen edges, gate after each step.
5. Tests: CTest/node cases for success, fillet-too-large failure (expect caught error, last good shape kept), and watertight PASS on the final bracket. Deploy smoke test must still pass.

## TBD (Erik) - do not hardcode guesses; use named constants marked TBD
- L-bracket dimensions
- Inner fillet radius
- Chamfer edges and distance
- Inner edge: user-picked or auto-detected
- Fillet live preview yes/no
- Hotkey 4 (still TBD)

## Out of scope
MeshFusion-style live Booleans, preview modes, kernel changes beyond the wrappers.

## Review
Erik reviews core diffs (bindings.cpp). Incremental commits; Repo Keeper scans and pushes.
