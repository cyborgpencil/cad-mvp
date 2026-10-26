# Antigravity Rust WASM units + volume Export-gate mirror (slice #1)

Team-locked by 3T in CAD CAM MVP room, 2026-10-26 (America/Denver). Authored by Doc Steward from Digest shortlist #1. This file is the Antigravity feed. It does not change the app by itself.

**Hard lock:** Implementation is **Antigravity-only on ErmoZ13**. Do **not** use Grok Build or Cursor for the handoff into code. Pilot owns the Antigravity run after this brief is on main. Same worktree style as prior Antigravity jobs (`C:\Dev\cadcam-antigravity-*` pattern); keep `C:\Dev\cadcam-mvp` main clean.

**Pick (3T locked):** Rust WASM mirror of **units + mesh volume** Export-gate path. Dual-run vs C++ `Module.gate()`. **C++ stays authoritative** — Rust is a shadow check until Erik says replace. **No OCCT / libcascade / kernel** in this slice.

Units: **mm**. Gate rule (Erik 2026-10-22 02:17 MT): units (mm) gates Export; OCCT shape-validity after ops does **not** block Export; watertight is **dropped** as an Export gate. Do not reopen watertight. Do not reopen phone T2 / Arc–Polygon polish / P1–P5 / dimPanel remove.

Sources: Digest note (room, 2026-10-26) + `src/units/units.hpp`, `src/units/units.cpp`, `src/export/gate.cpp`, `mvp/units.md`, `mvp/export.md`, `web/BUILD.md`, `web/assemble_site.py`, wasm-bindgen https://wasm-bindgen.github.io/wasm-bindgen/ , wasm-pack https://rustwasm.github.io/wasm-pack/ . WASM coexistence: separate `wasm32-unknown-unknown` module (do **not** link into Emscripten OCCT; see wasm-bindgen Emscripten note).

## Context
- App already loads two WASMs: Emscripten `cadcam.wasm` + libcascade `opencascade_single.wasm` (`web/BUILD.md`). Add a **third** module only.
- C++ Export gate today (`evaluate_export_gate` in `src/export/gate.cpp`): `export_allowed = units_pass && mesh_pass`. Units via `export_units_pass` (storage / 3MF / STL all `"millimeter"`). Mesh via signed `mesh_volume_mm3` (triple sum / 6); empty triangles → no triangles; volume `< -1e-9` → inside-out; `|volume| <= 1e-9` → zero volume. Watertight is reported but **not** in `export_allowed` / `export_block_reason` decision (units then mesh only).
- Units lock (`UnitLock`): stored lengths always mm; `kMmPerInch = 25.4`; `to_display` / `to_millimeters`; `ExportUnitRecord` storage/threemf/stl are always `"millimeter"`.
- Pages assemble: `web/assemble_site.py` `REQUIRED` + globs — any new site file **must** be listed there or assemble fails. Do not invent a second file list in the workflow.
- Prefer `wasm-pack` / `wasm-bindgen` crate under something like `rust/cadcam_gate/` (or `web/rust-gate/` — pick one tree and stick to it). Target `wasm32-unknown-unknown`. Commit source + build script; do **not** commit huge intermediate `target/` (gitignore). Built `.wasm` / glue for Pages: follow existing pattern (CI/Pages build emits artifacts; do not commit `web/cadcam.wasm`).
- Do not edit `UPDATES.md` (Repo Keeper only). Do not edit `research/` except if Digest already owns a follow-up. Do not edit phone UI / `#calloutLayer` / `#dimPanel`.
- Commit on a PR branch. Never push to main. Repo Keeper merges after tip-match + `ci.yml` green.

## Team-chosen behaviour

### T1 — Rust crate mirrors units + volume only
Ship a small Rust library that exports (via wasm-bindgen) functions whose results match C++ for the same inputs:

1. `to_display(mm, display_is_inch) -> f64` — divide by 25.4 only when inch.
2. `to_millimeters(displayed, display_is_inch) -> f64` — multiply by 25.4 only when inch.
3. `export_units_pass(storage, threemf, stl) -> bool` — all three equal `"millimeter"`.
4. `mesh_volume_mm3(vertices_xyz flat f64, triangles_ijk flat u32) -> f64` — same triple-product / 6 as `gate.cpp`.
5. `evaluate_rust_gate(...)` (or equivalent) → `{ units_pass, mesh_pass, export_allowed, block_reason, units_message, mesh_message, volume_mm3 }` using the **same** message strings as C++:
   - units pass: `PASS: export unit is millimeter.`
   - units fail: `FAIL: export unit is not millimeter.`
   - no triangles: `FAIL: mesh has no triangles.`
   - inside-out: `FAIL: mesh is inside-out (negative volume).`
   - zero: `FAIL: mesh has zero volume.`
   - mesh pass: `PASS: mesh has volume.`
   - `export_allowed = units_pass && mesh_pass`
   - `block_reason`: units message if !units_pass, else mesh message if !mesh_pass, else empty. **Ignore watertight** for allow/block (mirror current `export_block_reason`).

Round-trip: `0` and `25.4` mm exact; 1 mm → inch display → store again within one double ulp of `1` (see `mvp/units.md`).

### T2 — Load as third WASM; dual-run on Export tab
- Build / stage glue so the page can `import` / init the Rust module beside existing WASMs.
- On Export tab (and wherever `Module.gate()` / `__cadcamExportState` is published), also run the Rust gate on the **same** mesh + unit strings the C++ path uses.
- Show a clear readout, e.g. `RustGate: PASS` / `RustGate: FAIL` (+ short reason). Prefer a dedicated status id (e.g. `#statusRustGate` or Export-tab line) that does **not** replace `#statusUnits` / C++ gate UI.
- Publish for smoke: e.g. `window.__cadcamRustGate = { exportAllowed, blockReason, volumeMm3, unitsPass, meshPass, matchesCpp }` where `matchesCpp` is true when Rust `export_allowed` and `block_reason` agree with C++ for the current mesh (compare against existing published C++ state).
- **C++ still decides** Export button enablement. Rust must not gate the download by itself in this slice.

### T3 — Assemble + CI
- Extend `web/assemble_site.py` `REQUIRED` (and globs if needed) for every new site-relative file the page loads (glue `.js` / `.mjs`, `.wasm`, init helper). Missing → assemble must fail.
- Wire Pages / `ci.yml` so the Rust WASM is built in CI (or a documented `web/` script that Pages already invokes). Prefer adding a step next to existing wasm build; do not require Erik to install Rust on the phone.
- If Z13 local prove needs `rustup` / `wasm-pack`, install under a gitignored path or document the one-time toolchain; do not commit toolchains.

### T4 — Smoke dual-run asserts
Extend existing `tests/deploy_smoke.py` only (no new smoke file).

On at least these fixtures (reuse existing navigations):
- `?fixture=closed_box` (or default 20 mm box): C++ export allowed; Rust `exportAllowed === true`; `matchesCpp === true`; volume agrees with C++ within a tight epsilon (prefer exact same f64 path; allow ≤ 1e-9 relative if needed and document).
- `?fixture=flipped_box` (or equivalent inside-out): both block with inside-out / negative-volume messaging; `matchesCpp === true`.
- Empty / no-triangle case if already reachable in smoke; else a tiny hook that feeds zero triangles to Rust only is OK **only** if it does not break the live mesh — prefer a published test helper `window.__cadcamRustGate.eval(meshLike)` for the empty case.

Do **not** assert Rust replaces C++. Do **not** reintroduce watertight as a smoke Export requirement.

### T5 — Docs touch (minimal, this PR ok)
- One short note in `mvp/requirements.md` or a tiny `mvp/rust-gate.md` linked from requirements: slice #1 dual-run shadow; C++ boss; no OCCT. Doc Steward will tip-match; keep TBD for “replace C++?” until Erik decides.
- Do **not** write `UPDATES.md` in the impl PR (Repo Keeper cascade after merge).

## Acceptance
- T1. Rust exports match C++ messages and allow/block for units + volume cases above.
- T2. Pages (or local assemble) loads three WASMs; Export tab shows RustGate PASS/FAIL; C++ still owns Export enable.
- T3. `assemble_site.py` lists new files; CI builds the Rust wasm; `ci.yml` green on the PR.
- T4. `deploy_smoke` dual-run asserts green for closed + flipped (and empty if hooked).
- T5. Brief note on dual-run / C++ authority lands with the impl (or a docs hop RK opens — prefer in-impl one paragraph).

## Out of scope
- OCCT / libcascade / `web/occt-*.mjs` / B-Rep ops / `opencascade-rs` / truck / kernel rewrite.
- Linking Rust into the Emscripten module (`wasm32-unknown-emscripten`).
- Re-enabling watertight as Export gate.
- Replacing C++ `Module.gate()` (shadow only).
- Phone T2, `#calloutLayer`, `#dimPanel` remove, Arc/Polygon polish, P1–P5.
- Editing `UPDATES.md`, speculative UI polish, new smoke harness file.

## Prove (agent / CI — not Erik checklist)
After impl PR is up: `ci.yml` green; smoke dual-run asserts pass; Pages (or assembled `web/`) shows `RustGate` next to Export for closed_box PASS and flipped_box FAIL with `matchesCpp`. Author tip-match COMMENT (no self-APPROVE). Research Digest primary tip-match; Doc Steward second. Repo Keeper undrafts and plain-merges. Repo Keeper writes `UPDATES.md` after merge.

## Done
This **prompt PR** stays draft until Research Digest tip-matches (primary). Doc Steward is second if needed. Author does not self-APPROVE. Repo Keeper undrafts and plain-merges. After the prompt is on main, Pilot runs Antigravity-only on Z13 from this file (worktree off main). Report the PR link and tip SHA for the prompt; Pilot reports the impl PR separately.
