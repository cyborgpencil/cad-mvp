# OCCT WASM on GitHub Pages: does it fit?

Research Digest, 2026-10-21 (MT). Erik chose WASM only, hosted on GitHub Pages.

## Verdict: not blocking (with one size item TBD)
The planned build is single-threaded, so it needs no COOP/COEP headers, which Pages can't send. Size can't be confirmed: no project `.wasm` exists yet.

## Our build settings (from repo)
- `prompts/wasm-occt-core.md` and `research/occt-wasm/README.md`: single-threaded, `-msimd128` on, relaxed SIMD off, native wasm exceptions, `ALLOW_MEMORY_GROWTH`, default 2 GB max, WebGL2.
- No Emscripten CMake toolchain, preset or emcmake script in the repo yet. The root `CMakeLists.txt` has no `EMSCRIPTEN` branch.
- Built size: **TBD.** The only `.wasm` files under `builds/` are a browser extension's (`builds/edge-cdp/.../ink.wasm`), not ours.

## GitHub Pages limits [1]
| Limit | Value | Fit |
| --- | --- | --- |
| Published site | max 1 GB | Fine unless wasm is far larger than any figure in occt-wasm README (TBD) |
| Source repo | 1 GB recommended | Don't commit build output; deploy via Actions artifact |
| Single file in repo | Git blocks files over 100 MiB [2] | Only applies if wasm is committed; Actions deploy avoids it. Per-file limit for Actions artifacts: not documented (TBD) |
| Bandwidth | soft 100 GB/month | Usage-dependent; at ~10 MB/load that is ~10,000 loads (arithmetic only, size TBD) |
| Deploy | times out after 10 min; 10 builds/hour soft limit does not apply to custom Actions workflows [1] | Use the custom Actions workflow [3] |
| Use | Not for commercial SaaS [1] | Flag for Erik if the tool is ever sold |

## Headers and MIME
- **Custom headers:** Pages has no setting for response headers; not in its docs [1][3]. Third-party guides confirm COOP/COEP can't be set [6]. Treated as no headers.
- **`.wasm` MIME:** Pages uses mime-db, where `.wasm` was registered as `application/wasm` in 2017 [4], so `WebAssembly.instantiateStreaming` should work. Not live-tested on our site: verify with `curl -I` after first deploy.
- **Threads:** Emscripten pthreads are off unless `-pthread` is passed; pthreads need SharedArrayBuffer, which browsers gate behind COOP/COEP [5]. Our single-threaded build doesn't use them, so no isolation is needed.
- **Fallback only if threads are ever enabled:** `coi-serviceworker` adds COOP/COEP via a service worker; it reloads the page once on first visit, must be same-origin, and needs HTTPS [7]. Not needed now.

## Blocking?
- Nothing blocking found. Open items: real wasm size (first Emscripten build), live MIME check, and the commercial-use clause if the product is ever sold.

## Sources
1. GitHub Docs, GitHub Pages limits: https://docs.github.com/en/pages/getting-started-with-github-pages/github-pages-limits
2. GitHub Docs, About large files on GitHub: https://docs.github.com/en/repositories/working-with-files/managing-large-files/about-large-files-on-github
3. GitHub Docs, Using custom workflows with GitHub Pages: https://docs.github.com/en/pages/getting-started-with-github-pages/using-custom-workflows-with-github-pages
4. WebAssembly spec issue #573 (mime-db, used by GitHub Pages, registers .wasm): https://github.com/WebAssembly/spec/issues/573
5. Emscripten docs, Pthreads support: https://emscripten.org/docs/porting/pthreads.html
6. webrarian deployment guide (host header table): https://coatless-wasm.github.io/webrarian/articles/deployment.html
7. coi-serviceworker: https://github.com/gzuidhof/coi-serviceworker
