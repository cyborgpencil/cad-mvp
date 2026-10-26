# WASM app build

Single-threaded Emscripten build of the existing mesh checks, plus the libcascade 3.1.0 OCCT gate loaded as a second WASM. No `-pthread`, so the page is static files and needs no COOP/COEP headers (`research/occt-wasm/pages-hosting.md`).

`src/solid/watertight.cpp`, `src/units/units.cpp`, and `src/model/repair.cpp` are not edited. The gate in `src/export/gate.cpp` calls `export_units` (units lock); its older `check_watertight` call is legacy and is no longer an Export requirement. Volume is the triple sum from `mvp/solid-check.md` divided by 6, shown as a readout only.

Current rule (Erik, 2026-10-22 02:17 MT): watertight checks and tests are dropped. The units (mm) check stays and gates Export. The OCCT shape-validity check after operations stays, but it does not block Export. Code status (dd22dce): pending. `src/export/gate.cpp:93` still requires `watertight_pass && units_pass`, `src/export/export_files.cpp` still writes only after `check_watertight`, and `tests/deploy_smoke.py` still asserts watertight; removal is a separate C++ commit for Erik to review.

## Native tests

From a Visual Studio x64 developer shell, at the repo root:

```bat
cmake -S . -B builds\solid-check -G "NMake Makefiles" -DCMAKE_BUILD_TYPE=Release
cmake --build builds\solid-check --target test_watertight test_units test_export test_create test_gate
ctest --test-dir builds\solid-check --output-on-failure
```

`builds\` is gitignored. The `gate` test covers the millimeter lock, the volume, and the export block. `test_watertight` is a legacy test and not a required check. After `python web\fetch-libcascade.py`, CTest also runs `occt_gate` (Node, libcascade `BRepCheck_Analyzer` shape-validity check).

## Emscripten (this machine)

SDK lives only under `builds\emsdk` (gitignored). Nothing is installed system-wide.

```bat
git clone --depth 1 https://github.com/emscripten-core/emsdk.git builds\emsdk
builds\emsdk\emsdk.bat install latest
builds\emsdk\emsdk.bat activate latest --embedded
```

`--embedded` writes `.emscripten` inside `builds\emsdk`. Do not pass `--permanent`.

Build and emit `web/cadcam.js` plus `web/cadcam.wasm` (both gitignored). `emcmake` needs Ninja on `PATH` (Visual Studio ships it under `Common7\IDE\CommonExtensions\Microsoft\CMake\Ninja`). CMake 4.3.1 warns that it cannot build Emscripten shared libraries. This target is one executable, so that warning does not apply.

```bat
call builds\emsdk\emsdk_env.bat
emcmake cmake -S web -B builds\wasm -G Ninja -DCMAKE_BUILD_TYPE=Release
cmake --build builds\wasm
```

Do not add `-pthread`. Do not commit `web/cadcam.wasm` or `web/cadcam.js`.

## libcascade 3.1.0 (OCCT gate)

Prebuilt taucad `libcascade` 3.1.0, single-threaded (`opencascade_single.wasm`, no `-pthread`, no SharedArrayBuffer, no COOP/COEP). Canonical copy lives only under gitignored `builds/libcascade/`. The page loads a staged copy from gitignored `web/dist/`.

```bat
python web\fetch-libcascade.py
```

Source: `https://registry.npmjs.org/libcascade/-/libcascade-3.1.0.tgz` (OCCT V8_0_1, Emscripten 6.0.5). The OCCT check is `web/occt-gate.mjs`: `BRepCheck_Analyzer.IsValid()` after operations. A failed operation becomes a clean error and reverts; the check does not block Export. Free-edge (watertight) counting is no longer a requirement.

## Rust units + volume gate mirror (slice #1)

`rust/cadcam_gate` compiles to `wasm32-unknown-unknown` and is loaded as a third WASM (`web/rust-gate.mjs` + staged `web/dist/cadcam_rust_gate.js` and `web/dist/cadcam_rust_gate_bg.wasm`). It runs in dual-run shadow mode alongside C++ `Module.gate()`; C++ stays authoritative for Export enablement and there is no OCCT dependency in the Rust crate.

```bat
python web\build-rust-gate.py
```

`web/build-rust-gate.py` builds the release `wasm32-unknown-unknown` crate (adding the target via `rustup` when present), caches the matching `wasm-bindgen` CLI under gitignored `builds/wasm-bindgen/`, and stages the glue and `.wasm` into gitignored `web/dist/`. Do not commit `rust/cadcam_gate/target/` or `web/dist/`.

## Serve

Static files only. No custom headers and no app server.

```bat
python -m http.server 8765 --directory web
```

Open `http://127.0.0.1:8765/`. Optional query, still behind the same gate: `?fixture=closed_box&tab=export` or `?fixture=open_box&tab=export`. Fixtures are `closed_box`, `open_box`, `box20`, and `flipped_box`.

File → Load closed box / Load open box / Load 20 mm box switches the mesh. The status bar and the Export tab read `gate()` from the wasm module. Export is gated by the millimeter (units) lock, and the button title is the block reason. Watertight is not a gate, and the OCCT validity result goes to the log without blocking Export. STL and 3MF then download from the same writers as the native export.

## Pages

GitHub Actions builds this and deploys the static `web/` output plus the generated wasm and the libcascade 3.1.0 single-threaded files (fetched at build time, never committed). Repo Keeper owns that workflow.
