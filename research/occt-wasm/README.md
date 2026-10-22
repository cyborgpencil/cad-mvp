# OCCT for WASM (iOS Safari + Windows) and native MSVC on Z13

Updated 2026-10-20 (MT). Kernel = OpenCASCADE (Erik, 2026-10-20 11:00 PM MT). Target = current Chrome on Windows, Android, and iPhone (WebKit) (Erik, 2026-10-20 11:04 PM MT).

## Recommendation
- **Pin OCCT 8.0.1 on both sides** (latest official release, 2026-07-30; LGPL-2.1). [1][2]
- **Native (Z13, MSVC):** vcpkg port `opencascade` 8.0.1 (x64-windows), manifest mode, project-local. No system-wide install needed. Official docs: VS 2019+ (2022 preferred), C++17, CMake 3.10+ (3.16+ recommended). [3][4]
- **WASM:** build *our C++ core + OCCT 8.0.1* with Emscripten (officially supported target: Emscripten SDK 3.0+; repo ships `adm/scripts/wasm_build.bat`). Export a small embind API to the web GUI. [3][5]
- **Reference / fallback:** `libcascade` 3.1.0 (taucad fork of opencascade.js; OCCT 8.0.1, Emscripten 6.0.5). Good for a quick JS-side spike and as proof the toolchain works; not our core, since our core is C++. [6][7]

## Constraints that matter for iPhone
- **Chrome on iPhone runs on Apple WebKit, not Blink** (App Store Review Guideline 2.5.6 requires WebKit for iOS browsers; an EU-only exception exists, unconfirmed whether Chrome uses it). So Safari/WebKit limits below still apply to "Chrome on iPhone". [11]
- Native WASM exceptions require **Safari 16.4+**; keep relaxed SIMD **off** (Safari 26.x cannot parse it). [7][8]
- Size: opencascade.js full build 48.9 MB wasm, ~9.1 MB brotli; a custom build was 7.1 MB JS+WASM (2.4 MB compressed). v3 benchmark binary ~38 MB. Custom (module-trimmed) builds are required. [9][10]
- Start **single-threaded**: v3 benchmark shows multi-thread only 1.24x total gain with +39% init time. [10]
- TBD (unsourced yet): per-tab memory ceiling on iOS Safari, and COOP/COEP headers if threads are ever enabled. Measure on Erik's iPhone in the spike.

## Chosen build config (one build, all three targets) - 2026-10-20 11:05 PM MT
| Item | Choice | Why |
| --- | --- | --- |
| Threads | **Single-threaded. No COOP/COEP headers needed.** | Threads need SharedArrayBuffer, which needs cross-origin isolation (COOP same-origin + COEP require-corp) on all three. MT gain was only 1.24x with +39% init. [12][13][10] |
| SIMD | Baseline `-msimd128` on, **relaxed SIMD off** | Safari/WebKit 26.x cannot parse relaxed SIMD; iPhone Chrome is WebKit. [7][11] |
| Exceptions | Native wasm exceptions | Floor = iOS 16.4; Chrome 95+. [8] |
| Memory | `ALLOW_MEMORY_GROWTH`, small initial heap, default 2 GB max | Android Chrome reliably got 4 GB; iPhone WebKit only ~300-500 MB reliably and may reload the tab. **Budget the working set under ~300 MB.** Emscripten default max is 2 GB. [14][15][16] |
| Rendering | **WebGL2** baseline (WebGPU later, optional) | WebGL2 is on Chrome 56+, Chrome Android, iOS 15+. WebGPU is on iOS 26 and Chrome 113+, but on Android only on some GPUs. [17][18] |
| File save | `showSaveFilePicker` if present, else Web Share with files (`navigator.canShare`), else `<a download>` Blob | Picker: Chrome desktop + Android yes, iOS no. Web Share files: Android Chrome + iOS yes. [19][20][21] |

Fallback: if the iPhone load fails when the module starts, rebuild with a lower `MAXIMUM_MEMORY` (for example 512 MB), or use `IMPORTED_MEMORY` to set the max at runtime. [15] Phone checks Grok can't run are marked unverified for Erik.

## BREP text in libcascade 3.1.0 (2026-10-22)

The prebuilt single-threaded module exports file-path `BRepTools.Write` and `BRepTools.Read`. A runtime probe wrote a box to MEMFS and read it back. The `std::ostream` and `std::istream` overloads are not in `opencascade_single.js.symbols`. `web/project-file.mjs` uses the file-path calls, copies the BREP text into the `.cadmvp` JSON, and deletes the temporary file. `cadcam.wasm` still does not link OCCT.

## Next steps (Grok Build first)
1. Native: add `vcpkg.json` with `opencascade` 8.0.1; CMake `find_package(OpenCASCADE)`; spike = box -> BRepCheck -> BRepMesh -> STL, ctest passes on Z13.
2. WASM: install emsdk (user-level, no removals), build OCCT 8.0.1 static with only ModelingData/ModelingAlgorithms/Mesh modules, link the same core, record wasm size raw + brotli.
3. Load on iPhone Safari + Windows browser; record load time and memory. Watertight + units (mm) checks required on every exported file.

## Sources
1. https://github.com/Open-Cascade-SAS/OCCT/releases
2. https://occt3d.com/open-cascade-technology/
3. https://dev.opencascade.org/doc/occt-8.0.0/overview/html/build_upgrade__building_occt.html
4. https://vcpkg.io/en/package/opencascade ; https://vcpkg.link/ports/opencascade/versions
5. https://github.com/Open-Cascade-SAS/OCCT/blob/0ebbbedb/adm/scripts/wasm_build.bat
6. https://www.npmjs.com/package/libcascade
7. https://github.com/taucad/opencascade.js/blob/main/CHANGELOG.md
8. https://github.com/taucad/opencascade.js/blob/main/BREAKING_CHANGES.md
9. https://ocjs.org/docs/getting-started/file-size
10. https://github.com/taucad/opencascade.js/blob/main/BENCHMARKS.md
11. https://developer.apple.com/app-store/review/guidelines/ (section 2.5.6)
12. https://web.dev/articles/cross-origin-isolation-guide
13. https://caniuse.com/sharedarraybuffer
14. https://bugs.webkit.org/show_bug.cgi?id=269777
15. https://github.com/emscripten-core/emscripten/issues/24078
16. https://emscripten.org/docs/tools_reference/settings_reference.html
17. https://caniuse.com/webgl2
18. https://github.com/gpuweb/gpuweb/wiki/Implementation-Status
19. https://caniuse.com/mdn-api_window_showsavefilepicker
20. https://caniuse.com/web-share
21. https://web.dev/patterns/files/save-a-file