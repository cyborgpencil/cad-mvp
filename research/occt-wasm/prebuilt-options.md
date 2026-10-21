# Prebuilt OCCT -> WASM options (reuse vs build ourselves)

Research Digest, 2026-10-21 (MT). Target: OCCT 8.0.1, single-threaded, native wasm exceptions (`prompts/wasm-occt-core.md`).

| Option | Latest / OCCT | Activity | License | Threads | Size | Our 4 classes |
| --- | --- | --- | --- | --- | --- | --- |
| **libcascade** (taucad fork of opencascade.js) [1][2] | 3.1.0, 2026-10-13; OCCT 8.0.1, Emscripten 6.0.5 [1] | 13 releases 2026-07-29 to 2026-10-13 [1] | LGPL-2.1-only WITH Open-CASCADE-Exception-1.0 [1] | Ships both `opencascade_single.wasm` and `_multi.wasm`; single needs no COOP/COEP [1] | single 42,751,732 B raw (~42.8 MB), multi 42,731,431 B [3]; brotli TBD | `BRepCheck_Analyzer`, `ShapeAnalysis_FreeBounds`, `BRepMesh_IncrementalMesh`, `StlAPI_Writer` all present in the 3.1.0 `api-reference.json` [3] |
| **opencascade.js** (original, npm `opencascade.js`) [4] | 1.1.1 on npm, OCCT V7_4_0p1 [4] | npm release ~6 years old [4] | LGPL-2.1 (TBD exact SPDX) | TBD | full build 48.9 MB wasm, ~9.1 MB brotli (older ocjs docs, in occt-wasm README [9]) | TBD for 1.1.1 |
| **occt-import-js** [5] | 0.0.23, 2024-12-03 [5] | No npm release since 2024-12 [5] | LGPL-2.1 [5] | TBD | TBD | Import only (STEP/IGES/BREP to mesh JSON); no modeling, check, or STL export API [5]. Not a fit |
| **Official OCCT** [6][7] | No prebuilt WASM published; Emscripten is a supported build target, with `adm/scripts/wasm_build.bat` [6][7] | n/a | LGPL-2.1 + exception [8] | our choice | TBD (custom trim; occt-wasm README cites 7.1 MB JS+WASM for a trimmed ocjs build [9]) | All, since we build them |

## Notes
- **libcascade custom builds:** `@libcascade/toolchain` builds a trimmed symbol set, adds "your own C++ wrappers", and sets Emscripten flags (`exceptions: 'wasm'`, `simd`, `ALLOW_MEMORY_GROWTH`, single variant) through pinned Docker images [1]. So our C++ core (units, checker, exporters) could be linked in as custom bindings instead of maintaining our own OCCT Emscripten build. Needs Docker (or Podman) on Z13: install status TBD.
- **Size:** the stock 42.8 MB single wasm is untrimmed. The iPhone budget (~300 MB working set) and load time make a trimmed build the expected path either way. Trimmed size for our class set: TBD until built.
- **Build-ourselves cost:** 8.0.x build docs cover Emscripten [6], but we'd own toolchain pinning, module trimming and embind glue. libcascade says clean builds take "10-30 minute[s]" with a cache hit in seconds [1] (their figure, not measured here).
- **License fit:** OCCT and libcascade are both LGPL-2.1 with the OCCT exception [1][8]. Static wasm linking under LGPL needs us to let users relink (publish our objects or source); our repo is already public on GitHub, so this is likely fine. Legal reading is a TBD for Erik, not advice.
- **Not checked:** opencascade.js upstream (donalffons) GitHub activity and its v2 beta line; whether libcascade single build uses native wasm exceptions in the prebuilt binary (README says v3 does [1]; confirm in `opencascade_single.provenance.json`).

- **Phase 2 (2026-10-21):** libcascade 3.1.0 prebuilt confirmed working (single-threaded, 42.8 MB .wasm uncompressed). Served gzipped by GitHub Pages: content-encoding gzip, 12,359,983 bytes (~12.4 MB) transfer, measured by Repo Keeper via curl -I after deploy 644affb, 2026-10-21.

## Verdict (for Erik / Chief)
**Reuse libcascade 3.x via its toolchain (custom single-threaded build + our C++ as custom bindings) rather than building OCCT 8.0.1 ourselves.** It already ships OCCT 8.0.1, matches our config (single variant, wasm exceptions, SIMD), exposes all four classes we need, and has the right license. Fallback: the official OCCT Emscripten build [6] if the toolchain can't link our C++ core or Docker isn't allowed on Z13. Old opencascade.js (OCCT 7.4) and occt-import-js (import only) are not fits.

## Sources
1. libcascade on npm (README, versions, license): https://www.npmjs.com/package/libcascade ; repo https://github.com/taucad/opencascade.js
2. libcascade changelog: https://github.com/taucad/opencascade.js/blob/main/CHANGELOG.md
3. libcascade 3.1.0 package file listing and api-reference.json (checked 2026-10-21): https://unpkg.com/libcascade@3.1.0/?meta ; https://unpkg.com/libcascade@3.1.0/dist/api-reference.json
4. opencascade.js on npm: https://www.npmjs.com/package/opencascade.js
5. occt-import-js on npm: https://www.npmjs.com/package/occt-import-js
6. OCCT build docs (Emscripten): https://dev.opencascade.org/doc/occt-8.0.0/overview/html/build_upgrade__building_occt.html
7. OCCT wasm_build.bat: https://github.com/Open-Cascade-SAS/OCCT/blob/0ebbbedb/adm/scripts/wasm_build.bat
8. OCCT license: https://github.com/Open-Cascade-SAS/OCCT/blob/master/LICENSE_LGPL_21.txt ; https://dev.opencascade.org/resources/licensing
9. research/occt-wasm/README.md (sources 9, 10 there)
