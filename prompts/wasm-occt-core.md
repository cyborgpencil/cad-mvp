# Grok Build task: OCCT core to WASM (browser MVP)

Status: ready for Grok Build Pilot. Decisions from Erik, 2026-10-20 10:59-11:04 PM MT.

## Goal
Build the MVP core on OpenCASCADE (OCCT), compiled to WebAssembly with Emscripten, with a simple web GUI. Target browser: current Google Chrome on Windows desktop, Android, and iPhone (WebKit).

## Scope (MVP only)
- Sketch to solid: line, rectangle, circle, dimensions, basic constraints, extrude, union/cut, constant-radius fillet.
- Units: model stored in millimeters (locked). The main GUI shows a clearly visible mm/inch toggle (display only, factor 25.4).
- Watertight gate: export is blocked unless the solid passes the watertight/manifold check. Show a clear reason when blocked.
- Export: binary STL and 3MF only (3MF with unit="millimeter").
- Out of scope: STEP import, freeform mesh, feature history, multi-body, revolve, chamfer, MCP, Qt desktop GUI work.

## Environment (ErmoZ13)
- Repo: C:\Dev\cadcam-mvp. Run Grok from this folder.
- SDKs (emsdk, Node, vcpkg tree) go in C:\Dev\sdk\, never inside the repo. Build output and vcpkg_installed go under builds\ (gitignored).
- OCCT 8.0.1 (sources: research\occt-wasm\README.md). Native Z13 build: vcpkg `opencascade` port in manifest mode.
- Browser build: OCCT 8.0.1 compiled with our core via Emscripten. Build config (research\occt-wasm\README.md):
  - Single-threaded (no COOP/COEP headers needed).
  - Basic WASM SIMD on, relaxed SIMD off.
  - Native WASM exceptions (floor: iOS 16.4, Chrome 95).
  - Memory growth on, small initial heap, max 2 GB default. Keep models under about 300 MB. Fallback if iPhone load fails: rebuild with a 512 MB max.
  - Rendering: WebGL2. No WebGPU in MVP.
  - File save: showSaveFilePicker where available (Windows, Android), else Web Share with files (iPhone), else plain download. One build must run on desktop Chrome, Chrome on Android, and Chrome on iPhone, which uses Apple WebKit (see research\occt-wasm\README.md).
- Reuse the existing pure C++ core (units, checker, exporters) where it ports cleanly; do not edit the checker sources without flagging it.

## Required checks (every output)
1. Watertight: exported STL/3MF passes the existing checker (CTest) and a read-back check.
2. Units: a 20 mm test box exports as 20 mm in STL and 3MF; the toggle shows 0.787 in without changing stored values.
3. Chrome on Windows: page loads and exports in current desktop Chrome. Record wasm size, load time, and memory.
4. Chrome on iPhone (WebKit, iOS 16.4+): page loads and exports; record load time and memory if possible. Grok cannot test this from Z13, so mark it unverified for Erik to run.
5. Chrome on Android: page loads and exports (file save works); record load time and memory if possible. Grok cannot test this from Z13, so mark it unverified for Erik to run.
6. Open pocket via OCCT boolean cut: on a 40 x 30 x 20 mm box, cut an 8 x 8 x 6 mm pocket at X 16, Y 12 that breaks through the top face (pocket spans Z 14 to 20), using `BRepAlgoAPI_Cut`, not mesh code. The export must be one closed shell (no interior void), pass the watertight checker and read-back, keep 40 x 30 x 20 mm in STL and 3MF, and have volume 24000 - 384 = 23616 mm3 within tessellation tolerance. Record the measured volume and shell count.
7. Report anything you could not verify as unverifiable; never fake a pass.

## Git
- Grok must not run git commit or git push.
- When all checks pass, report the result and the changed files. Repo Keeper then commits and pushes to origin main. Erik reviews core diffs on GitHub.

## Deliverables
- Source under src/ (web GUI and WASM bindings), build script, short note in mvp/ on how to build and serve locally.
- Log of what was deferred.

## Acceptance
Erik opens an exported file in OrcaSlicer at the correct size with no manifold errors.



