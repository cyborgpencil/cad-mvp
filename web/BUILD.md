# WASM app build

Single-threaded Emscripten build of the existing mesh checks. No OpenCASCADE in this slice. No `-pthread`, so the page is static files and needs no COOP/COEP headers (`research/occt-wasm/pages-hosting.md`).

`src/solid/watertight.cpp`, `src/units/units.cpp`, and `src/model/repair.cpp` are not edited. The gate in `src/export/gate.cpp` calls `check_watertight` and `export_units`. Volume is the triple sum from `mvp/solid-check.md` divided by 6, computed here so the checker stays the PASS/FAIL source. That is a new readout, not a change to the checker rules.

## Native tests

From a Visual Studio x64 developer shell, at the repo root:

```bat
cmake -S . -B builds\solid-check -G "NMake Makefiles" -DCMAKE_BUILD_TYPE=Release
cmake --build builds\solid-check --target test_watertight test_units test_export test_create test_gate
ctest --test-dir builds\solid-check --output-on-failure
```

`builds\` is gitignored. The `gate` test covers the watertight result, the millimeter lock, the volume, and the export block.

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

## Serve

Static files only. No custom headers and no app server.

```bat
python -m http.server 8765 --directory web
```

Open `http://127.0.0.1:8765/`. Optional query, still behind the same gate: `?fixture=closed_box&tab=export` or `?fixture=open_box&tab=export`. Fixtures are `closed_box`, `open_box`, `box20`, and `flipped_box`.

File → Load closed box / Load open box / Load 20 mm box switches the mesh. The status bar and the Export tab read `gate()` from the wasm module. Export stays disabled until watertight and the millimeter lock both pass, and the button title is the block reason. STL and 3MF then download from the same writers as the native export.

## Pages

GitHub Actions builds this and deploys the static `web/` output plus the generated wasm. Repo Keeper owns that workflow. This session does not add a workflow and does not commit the wasm.
