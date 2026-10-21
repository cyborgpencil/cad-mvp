# GUI wire target: Qt app in src/ vs WASM browser page

Updated 2026-10-21 (MT). Research Digest. Informs Erik's choice; does not decide it. No scope change proposed.

## Repo state (read 2026-10-21)
- `src/gui/` is a Qt 6 Widgets app (`solid_view`: main_window, mesh_view on Qt6::OpenGLWidgets), built only if `find_package(Qt6)` succeeds (CMakeLists.txt).
- **No OCCT is linked anywhere yet**: no `vcpkg.json`, and no `BRep*`/`ShapeAnalysis*`/`TopoDS` in `src/`. The current check is the in-house triangle checker (`src/solid/watertight.*`) plus `repair_manifold` (weld, drop degenerates, flip shell) in `src/model/repair.*`.
- `prompts/wasm-occt-core.md` (Erik, 2026-10-20) scopes the browser MVP and lists "Qt desktop GUI work" as **out of scope**. `mvp/requirements.md` says "Browser-portable target (WASM)".
- Approved GUI = `mockup/index.html` (HTML/CSS) + `mvp/ui-redesign.md` (44 px targets, 390 px phone layout, Export only on Export tab behind the gate).

## Comparison
| Item | (A) Qt desktop app in `src/` | (B) WASM browser page |
| --- | --- | --- |
| OCCT 8.0.1 build | Native MSVC via vcpkg `opencascade` port [4]; OCCT ships Qt Widgets samples historically [5] | Emscripten is an official OCCT target; `adm/scripts/wasm_build.bat` [3]; WebGL sample exists [5] |
| Mockup reuse | Must be rebuilt in Qt Widgets/QML; the HTML is reference only | HTML/CSS mockup used directly; C++ core exposed via embind |
| Phone reach (44 px, 390 px) | Desktop only as built. Phone needs Qt for WASM or Android build (proposal, unscoped) | Same page on desktop Chrome, Android, iPhone WebKit [ref occt-wasm] |
| Watertight + units gate on Export | C++ call before `QFileDialog` save; gate lives in C++ | Same C++ gate called through embind; JS enables Export button only on pass |
| Export path | Normal file save to disk | Blob download, `showSaveFilePicker`, or Web Share (iPhone) [ref occt-wasm 19-21] |
| Fit with Erik's prompt | Conflicts: Qt GUI listed out of scope | Matches `prompts/wasm-occt-core.md` |

## Notes
1. **Gate is the same C++ either way.** Today it is the mesh checker + `repair_manifold`. Adding `BRepCheck_Analyzer` (B-rep validity) and `ShapeAnalysis_FreeBounds` (free/open edges) before tessellation is planned work on both targets, not a differentiator. Exact gate order = TBD (Erik/Doc Steward).
2. **Qt on the web is a third path, not free.** Qt for WebAssembly runs on mobile Safari and Android Chrome [1], but: `QOpenGLWidget` is **not supported** on WASM [1] (our `mesh_view` uses Qt6::OpenGLWidgets, so it would need rework); Qt binary WASM builds do **not** include Wasm exceptions or SIMD, so our chosen config (native exceptions, `-msimd128`) needs Qt built from source [1]; Qt 6.12 pins Emscripten 5.0.5 [1]; Qt WASM is GPL-3 or commercial [1] (OCCT is LGPL-2.1 [ref occt-wasm 2]).
3. **Qt WASM size:** Qt Widgets example ~3.2 MB brotli before OCCT [1]. Plain-HTML (B) adds no UI toolkit to the wasm. OCCT size figures: see `research/occt-wasm/README.md`.
4. **Qt WASM saves by download:** `QFileDialog::saveFileContent()` saves "via file download" [1]; no native Web Share path documented.
5. **Effort/risk (proposal, unmeasured):** (A) has a working window today but zero OCCT and no phone path. (B) needs emsdk + OCCT WASM build first (not yet done on Z13), then JS wiring; risks are wasm size and iPhone memory (~300 MB budget, see occt-wasm README). No time estimates sourced.
6. **Touch on (B):** 44 px and 390 px were already measured on the mockup (T1: 63/64 pass, Part name button 30x44; T2 pass). Real touch input (T3/T4) still untested on both.

## Gaps / TBD
- OCCT 8.0.1-specific Qt sample status: OCCT docs say project samples are moving out of the main repo [5]; 8.0.1 Qt sample location not confirmed.
- No sourced effort/time figures for either path.
- iOS per-tab memory ceiling still unsourced (from occt-wasm README).

## Sources
1. Qt 6.12 docs, Qt for WebAssembly: https://doc.qt.io/qt-6/wasm.html
2. Emscripten settings reference: https://emscripten.org/docs/tools_reference/settings_reference.html
3. OCCT build docs (Emscripten target): https://dev.opencascade.org/doc/occt-8.0.0/overview/html/build_upgrade__building_occt.html ; https://github.com/Open-Cascade-SAS/OCCT/blob/0ebbbedb/adm/scripts/wasm_build.bat
4. vcpkg opencascade port: https://vcpkg.io/en/package/opencascade
5. OCCT Tutorials and Samples (Qt Widgets, QtQuick, WebGL): https://dev.opencascade.org/doc/occt-7.9.0/overview/html/samples.html
- [ref occt-wasm N] = numbered sources in `research/occt-wasm/README.md`.
