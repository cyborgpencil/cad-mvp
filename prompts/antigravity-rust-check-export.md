# Antigravity Rust CLI port of tools/check_export.py (slice #2)

Authored by Doc Steward, 2026-10-26 (America/Denver), from the Rust track on main tip `d371162` (PR #146). Digest sources welcome. This file is the Antigravity feed. It does not change the app by itself.

**Hard lock:** Implementation is **Antigravity-only on ErmoZ13**. Do **not** use Grok Build or Cursor for the handoff into code. Pilot owns the Antigravity run after this brief is on main. Worktree `C:\Dev\cadcam-antigravity-*`. Keep `C:\Dev\cadcam-mvp` main clean. No phone UI, no `#dimPanel`, no watertight reopen, no replacement of C++ `Module.gate()`.

**Pick (requirements Rust track, Independent slice #2):** Native Rust CLI that checks exported STL/3MF against a typed size and volume. Same contract as `tools/check_export.py`, so CI can run it first as a shadow / dual-run. Python stays. A later slice may prefer the Rust CLI only after dual-run has stayed green; that switch is not this slice.

Crate: standalone binary package `rust/cadcam_check_export/` (`src/main.rs`, bin name `cadcam_check_export`). Host target only. **Not** the wasm `rust/cadcam_gate` cdylib. No `wasm32` target for #2. No Cargo workspace that pulls this bin into the wasm crate build.

Mesh load (open-source, pure Rust, no Python, no trimesh, no OCCT):

- STL: [`stl_io` 0.11](https://crates.io/crates/stl_io) (MIT). Reads ASCII and binary STL. MSRV 1.85; CI stable from rustup is enough. If that exact minor refuses the runner, pin the newest `stl_io` that builds there and still reads both STL kinds.
- 3MF: [`zip`](https://crates.io/crates/zip) + [`quick-xml`](https://crates.io/crates/quick-xml) (both MIT). Read `3D/3dmodel.model` the way `read_3mf_unit` does (path compare is case-insensitive; XML local names, so a default xmlns still yields `model` and `unit`). Triangles come from that same model XML.
- Leave `lib3mf` / `lib3mf-core` and the C++ lib3mf unused. They are a second stack, and the Rust `lib3mf` line can pull parry/nalgebra.
- Volume: signed triple-product / 6, same helper as `mesh_volume_mm3` in `rust/cadcam_gate/src/lib.rs`. Duplicate that short helper in this crate. A tiny pure `rlib` shared with #1 is allowed only when it stays free of `wasm-bindgen` and does not change `cadcam_gate` wasm exports. Prefer the duplicate so #1 and `web/` stay put.
- Extents: axis-aligned bbox size on each axis (max − min), millimeters, same role as trimesh `extents`.
- Commit `Cargo.lock`. Do not commit `target/` (already covered by `rust/**/target/` in `.gitignore`).

Units: **mm**. Watertight (Erik, 2026-10-22 02:17 MT): dropped as an Export gate. `is_watertight` is **INFO only** and never decides the exit code. Do not reopen watertight. Do not reopen phone T2 / Arc–Polygon polish / P1–P5 / `#dimPanel` remove. Do not pull OCCT / libcascade / AGPL bindings.

Sources: `mvp/requirements.md` Rust conversion (“Next Independent: **#2** Rust CLI port of `tools/check_export.py` (CI-first)”; then #4 only if the schema stays frozen; skip #3 and #5/#6) on main `d371162`. `tools/check_export.py` (contract below). `.github/workflows/ci.yml` step `Export check (trimesh)` (the `export_box` + Python invocation). `prompts/antigravity-rust-units-gate.md` (slice #1 feed; wasm crate stays the shadow gate). Erik watertight drop: `mvp/export.md` and the 2026-10-22 02:17 MT rule. Loader crates: stl_io, zip, quick-xml (links above). Python pin today: `tools/requirements.txt` (`trimesh==5.1.1`); the Rust CLI does not install it.

## Context
- CI today, after Native CTest, when `steps.changes.outputs.code == 'true'`:

  `./builds/native/export_box`

  then

  `python tools/check_export.py builds/export/box.stl builds/export/box.3mf --expect-size 20 20 20 --expect-volume 8000`

  `export_box` writes `builds/export/box.stl` and `builds/export/box.3mf` from the repo root (20 mm cube, volume 8000 mm3). Those two files and those args are the dual-run pair.
- Slice #1 already lives in `rust/cadcam_gate` (`cdylib` + `rlib`, `wasm32-unknown-unknown`, `web/rust-gate.mjs`). C++ `Module.gate()` is still the Export boss. This slice does not touch that path.
- `ci.yml` already installs stable rustup (with the wasm32 target) in the Rust gate step when cargo is missing. The #2 CLI builds for the host. It does not need `wasm32-unknown-unknown`.
- Coding stays Antigravity-only on Z13 after this brief is on main. Parallel with overnight UI slices (1)–(4) is allowed because this slice is Independent. This brief does not schedule those UI slices.
- Do not edit `UPDATES.md` (Repo Keeper only), in this prompt PR or in the impl PR. Do not edit `research/`.

## Team-chosen behaviour

### T1 — CLI parity with tools/check_export.py
One or more positional `.stl` / `.3mf` paths.

Required:

- `--expect-size X Y Z` — bbox extents in mm, three finite floats.
- `--expect-volume` — mm3, one finite float (the app volume the Python checker calls the BRepGProp volume).

Optional:

- `--size-tol` — absolute mm per axis. Default `0.1`. Finite, and `>= 0`.
- `--volume-rel-tol` — `|actual − expected| / |expected|`. Default `0.01`. Finite, and `>= 0`.

Exit, after every path is attempted:

- **0** — every file passed (no FAIL line).
- **1** — any FAIL, and no usage/load error.
- **2** — usage or load error. A load error on any path wins over FAIL on another path (same as the Python `load_error` flag).

Usage that exits **2** prints `ERROR:` on stderr: missing required flag, bad flag arity, non-finite number, negative `--size-tol` or `--volume-rel-tol`.

Load errors exit **2** and print `ERROR:` on stderr. Cover bad path, suffix other than `.stl`/`.3mf`, unreadable file, bad zip, missing `3D/3dmodel.model`, bad XML, no `model` element, and a file that does not yield a triangle mesh. Do not shell out to Python or trimesh. An empty triangle list is a successful load that **FAIL**s (exit 1), not a load error.

Stdout lines, in Python order, for each file that loads:

1. The path argument, as typed, on its own line (no PASS/FAIL prefix).
2. 3MF only: unit check. STL has no unit-attribute check and prints no unit line.
3. Triangle / extents / volume checks.
4. One watertight INFO line. Always, after a successful load, including when earlier lines are FAIL.

3MF unit (exact strings):

- missing attribute → `FAIL: export unit attribute is missing.`
- present and not `millimeter` → `FAIL: export unit is not millimeter.`
- `millimeter` → `PASS: export unit is millimeter.`

Mesh:

- no triangles → `FAIL: mesh has no triangles.` (do not also grade extents or volume).
- extents missing or not three finite numbers → `FAIL: bbox extents are missing.`
- any axis with `abs(got − want) > size_tol` (boundary equal to the tol still passes) → `FAIL: bbox extents are {got} mm, expected {want} mm.`
- else → `PASS: bbox extents are {got} mm.`
- volume non-finite or `<= 0` → `FAIL: volume is not positive ({vol} mm3).`
- else relative error `> volume_rel_tol` (boundary equal to the tol still passes; expected `0` uses the Python rule: relative `0` only when actual equals expected, otherwise non-finite relative and FAIL) → `FAIL: volume is {vol} mm3, expected {exp} mm3.`
- else → `PASS: volume is {vol} mm3.`

`{got}` is three numbers joined by spaces. Format each float the way `fmt` does in `tools/check_export.py`: six digits after the decimal, strip trailing zeros and a dangling decimal point; non-finite stays the default rendering; blank / `-` / `-0` print as `0`.

Watertight INFO, exact shape:

- `INFO: is_watertight is true.` or `INFO: is_watertight is false.`
- or `INFO: is_watertight could not be read ({reason}).`

Use a small in-crate closed-shell check (each triangle edge shared by two triangles) so the exported 20 mm box can print `true`. Do not import a manifold or OCCT crate for it. The boolean never selects the exit code. Dual-run does not fail when this boolean differs from trimesh.

CI box, default tols, both files in one process, exit 0. STL stdout has the path, `PASS: bbox extents are 20 20 20 mm.`, `PASS: volume is 8000 mm3.`, and an INFO line. 3MF stdout adds `PASS: export unit is millimeter.` before the extents line. Match closely enough that those PASS lines hold; do not tighten the CI tolerances.

### T2 — CI dual-run on the same artifacts
In `.github/workflows/ci.yml`, keep the step `Export check (trimesh)` as it is, including the Python command and `--expect-size 20 20 20 --expect-volume 8000`.

Add a following step, same `if: steps.changes.outputs.code == 'true'`, that:

1. Puts `$HOME/.cargo/bin` on `PATH`. If `cargo` is missing, install stable rustup for the host only (no `--target wasm32-unknown-unknown` on this step).
2. `cargo test --manifest-path rust/cadcam_check_export/Cargo.toml`
3. `cargo build --release --manifest-path rust/cadcam_check_export/Cargo.toml`
4. Runs `cadcam_check_export` on `builds/export/box.stl` and `builds/export/box.3mf` with the **same** `--expect-size 20 20 20 --expect-volume 8000`. Defaults for both tols. Do not point it at a different mesh.

Shadow rule: both processes exit 0. Python stays in the workflow in this slice even when they agree. If they disagree, fix the Rust CLI (or stop and report). Do not delete `tools/check_export.py`. Do not flip CI over to Rust-only.

### T3 — Tests inside the Rust crate
`cargo test` on `rust/cadcam_check_export` covers at least:

- Good STL and good 3MF (20³, volume 8000, 3MF unit `millimeter`) → exit 0 and the PASS lines from T1.
- Size outside `--size-tol` → exit 1 and a FAIL bbox line.
- 3MF with triangles and no `unit` attribute → exit 1 and `FAIL: export unit attribute is missing.`
- 3MF `unit` other than `millimeter` → exit 1.
- STL path does not print an export-unit line.
- Zero triangles → exit 1 and `FAIL: mesh has no triangles.`
- Missing path, bad zip, bad XML → exit 2 and stderr `ERROR:`.
- Size and volume pass while watertight is false → exit 0, with an INFO line.
- Non-finite or negative tol, or a missing required flag → exit 2.

Fixtures may be generated in the crate tests or stored under `rust/cadcam_check_export/`. Do not add them under `web/` or `tests/` Python smoke.

### T4 — No web / wasm / assemble work
This slice does not require changes to `web/`, `web/assemble_site.py`, Pages, `rust/cadcam_gate` wasm exports, `window.__cadcamRustGate`, or `#statusRustGate`. Do not add a `wasm32` job. `pages.yml` can keep testing `cadcam_gate` only.

### T5 — Tip-match path
Impl PR is a branch. Never push to main. Author posts a tip-match COMMENT and does not self-APPROVE. Research Digest primary, Doc Steward second. Repo Keeper undrafts and plain-merges after `ci.yml` is green (crate tests, Python export check exit 0, Rust CLI exit 0 on the same box args). No phone preview (no UI in this slice).

In that same impl PR, one short bullet on the Rust track in `mvp/requirements.md`: #2 `cadcam_check_export` dual-runs in CI beside `tools/check_export.py` on `box.stl` / `box.3mf` (`--expect-size 20 20 20 --expect-volume 8000`); Python stays; watertight stays INFO-only. Same weight as the slice #1 bullet. Do not edit `UPDATES.md` there; Repo Keeper cascades after merge. Leaving the line for that cascade is acceptable only if the impl PR would otherwise be code-only — prefer the one requirements bullet, as #1 did.

## Acceptance
- T1. Flags, exits 0 / 1 / 2, and PASS / FAIL / INFO / path lines match the Python contract above. `is_watertight` never selects the exit.
- T2. CI builds the host CLI and runs it on `builds/export/box.stl` and `builds/export/box.3mf` with the same expect-size and expect-volume as the Python step. Python step still present. Both exit 0.
- T3. Crate tests cover good size, bad size, 3MF missing unit, and load error → 2.
- T4. No web, wasm, or assemble change is required for the slice to land.
- T5. Impl tip-match path above, plus the one `mvp/requirements.md` line (preferred).

## Out of scope
- Editing `rust/cadcam_gate` wasm exports, `web/`, or `assemble_site.py` for this slice.
- Replacing C++ `Module.gate()` or the Export button enablement.
- Watertight as a FAIL or as an exit-code input. Reopening watertight.
- OCCT, libcascade, truck, AGPL bindings, `opencascade-rs`.
- Slice #4 `.cadmvp` schema validate.
- Overnight UI queue (1)–(4), phone T2, `#dimPanel`, Arc/Polygon polish, P1–P5.
- Deleting `tools/check_export.py` or dropping the Python CI step in this first landing.
- `UPDATES.md` (Repo Keeper). A wasm32 target for this CLI.

## Prove (agent / CI — not Erik checklist)
After the impl PR is up: `ci.yml` green; `cargo test` for `rust/cadcam_check_export` green; Python `check_export.py` and `cadcam_check_export` both exit 0 on `box.stl` and `box.3mf` with `--expect-size 20 20 20 --expect-volume 8000`. Author tip-match COMMENT (no self-APPROVE). Research Digest primary tip-match; Doc Steward second. Repo Keeper undrafts and plain-merges. Repo Keeper writes `UPDATES.md` after merge. No phone preview for this slice.

## Done
This **prompt PR** stays draft until Doc Steward tip-matches (primary) and Research Digest tip-matches (second). Author does not self-APPROVE. Repo Keeper undrafts and plain-merges. After this file is on main, Repo Keeper opens the worktree (`C:\Dev\cadcam-antigravity-*`, `C:\Dev\cadcam-mvp` main left clean) and Pilot runs Antigravity-only on ErmoZ13 from this file. Report the prompt PR link and tip SHA; Pilot reports the impl PR separately.
