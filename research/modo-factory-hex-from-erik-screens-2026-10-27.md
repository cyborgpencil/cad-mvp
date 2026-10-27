# Modo factory hex from Erik screens (invent-free)

**Owner:** MVP Research Digest  
**Compiled:** 2026-10-27 ~1:35 PM MT (America/Denver)  
**Product locks (unchanged):**  
- Selection orange stays **`#ffa829`** (Erik: current orange is good).  
- Active chrome stays **lock B** — product muted teal `#14756e`; factory orange active chrome = **ref only**.  
- Flat viewport backdrop still stands — GL/viewport gradient stops below are **Modo-factory reference / source only**, not a cad-mvp apply goal.  
- Reject unsourced `#ff8000`. Never invent hex.

## Screen inventory (Erik PNGs)

Folder: `/workspace/research/modo-erik-screens-2026-10-27/`

| File (sha256 stem) | Size | Role (by looking) |
| --- | --- | --- |
| `9d9f9c9fce7bf45087f434eb678a3c6170b4c4d56d474e0774d5e0baefc24334.png` | 628×1544 | **Left toolbox / bar** — primitives, mode icons, vertical tabs (`Basic` active), Default Layouts header |
| `729eff9015a39e2ba6df57e53fc1c0842a17a03a4c6d6f45c1be6c35b507631a.png` | 1077×1935 | **Right bar** — Shading tree + Properties (Diffuse/Specular); viewport sliver on left |
| `e9c000225bd6bf7ea0f479c898a8809a0e93cad7cba4192852b8ecb09d5daddf.png` | 918×719 | **Viewport** — extruded “Modo” mesh selected; Perspective + top mode tabs |

**Provenance note:** mobile-browser crops (iOS chrome visible on right-bar shot; macupdate.com static host mentioned in capture). Expect mild compression / AA wash vs lossless Foundry help PNGs. Prefer prior [`modo-factory-hex-from-media.md`](modo-factory-hex-from-media.md) for selection/active orange when these screens disagree due to compression.

**Tooling:** Pillow via `/workspace/tmp/modo-hex/venv`; region annotations under `/workspace/tmp/modo-hex/erik-screens-annotated/`.

## Sampling method

1. Identify each PNG by layout (left toolbox vs right Properties vs viewport “Modo” mesh).  
2. Dominant / median RGB on labeled UI regions only (panel bodies, cool chrome, empty viewport columns).  
3. **Exclude** material Diffuse/Specular color swatches and their RGB numeric fields from chrome tokens.  
4. **Exclude** selected-mesh fill when proposing product selection orange — lock stays `#ffa829`.  
5. No invented values. Cross-check vs media digest; cite drift, do not overwrite that file.

## Factory hex table (Erik screens)

| Element | Hex | RGB | Best source region | Confidence |
| --- | --- | --- | --- | --- |
| **Panel gray (primary toolbox / toolbar)** | `#5e5f61` | 94,95,97 | Left toolbox body (dominant exact); also VIEW secondary toolbar | **High** |
| Panel gray (darker chrome / wells) | `#474747` | 71,71,71 | Left dropdown wells; right Properties body; VIEW toolbar | **High** |
| Panel gray (deep / nested) | `#353739` | 53,55,57 | Right Shading tree / deep panel | **High** |
| **Muted cool chrome (blue-gray panel)** | `#5f6367` | 95,99,103 | Right Shading / Add-Layer row / vert-tab strip (cool bias) | **High** |
| Muted cool field / section fill | `#91989e` | 145,152,158 | Right Properties section fills (blue-gray; not material) | **High** |
| Cool chrome neighbor | `#565a5e` | 86,90,94 | Viewport-adjacent cool gray; left vert-tab neighborhood | Medium |
| Factory **active chrome orange** | *(unreliable in these PNGs)* | — | Visually orange Basic / Properties / mode accents, but peaks wash to muddy `#b28c48` / `#cda65e` family | **Low** for hex — keep media digest **`#f49c1c` / `#fb9909` as ref only**; do **not** apply to product active chrome (lock B) |
| Selected mesh fill (viewport “Modo”) | muddy `#b28c48` family (compressed) | 178,140,72 peak | VIEW mesh region — **note only** | **Low** as hex; **product lock stays `#ffa829`** |
| Product hover light-blue | — | — | Not re-sampled as new lock; prior approved `#8cb4c7` stands | n/a this pass |
| Product muted-teal active | — | — | **Not** found as Modo factory button fill (expected); product stays `#14756e` | n/a |

### Material data — **excluded from chrome**

Right-bar Properties shows Diffuse / Specular RGB numbers and warm swatches. Sampled warm peaks (e.g. `#f2d686`, `#c79e58`, `#e9c97c`) are **material / property data**, not UI chrome. Do **not** put them in chrome token tables or apply briefs.

### GL / viewport gray-gradient stops — **Modo-factory reference only**

**Not a cad-mvp `modo` theme goal** (flat-backdrop lock still stands until Erik says otherwise).

From empty columns in the viewport PNG (`e9c000…png`), left/right of the “Modo” mesh:

| Stop | Hex | RGB | Notes |
| --- | --- | --- | --- |
| Top / lighter | `#565a5e` | 86,90,94 | Also near `#5e5f61` at very top chrome edge |
| Mid | `#4a4d50` | 74,77,80 | Clear mid stop (Rcol/Lcol peak) |
| Bot / darker | `#383b3f` | 56,59,63 | Dominant lower viewport (~90%+ in bot bands) |

Right-bar viewport sliver agrees on mid `#505357` / bot `#383b3f`; top of that sliver mixes panel `#353739` (UI overlap) — prefer VIEW empty-column stops above.

## Cross-check vs media digest

Prior: [`modo-factory-hex-from-media.md`](modo-factory-hex-from-media.md) (~11:32 AM MT).

| Topic | Media digest | Erik screens | Drift |
| --- | --- | --- | --- |
| Selection orange | `#ffa829` High (help PNGs) | Compressed muddy browns | **Keep `#ffa829`**; Erik confirmed current orange good |
| Active chrome orange | `#f49c1c` / `#fb9909` High | Visually present, hex washed | Keep media hex as **ref only** |
| Panel gray | `#49494b` Medium (video) | `#5e5f61` / `#474747` / `#353739` High | Erik screens clearer; `#474747` ≈ prior `#49494b` family |
| Muted teal/blue | `#5a757c` icon Medium; hover `#8cb4c7` | Cool panel `#5f6367` + field `#91989e` | No factory teal **button** system; cool blue-gray chrome clarified |
| GL gradient | `#646b6d` → `#343a3c` → `#333a3c` | `#565a5e` → `#4a4d50` → `#383b3f` | Same darkening story; Erik stops slightly cooler/darker top, clearer mid; **source only** both |

## Recommended stance (no new product apply hex)

1. **Orange selection lock unchanged:** `#ffa829`.  
2. **Hover lock unchanged:** `#8cb4c7`.  
3. **Lock B unchanged:** product active = `#14756e`; factory orange chrome = ref only.  
4. **Panel / cool chrome** from this pass may inform a later invent-free Doc brief for `modo` panel tokens — **not** applied this turn.  
5. **Gradient stops** = source-only reference; do not reintroduce viewport gradient.

## Open / low-confidence

1. Exact factory active-chrome orange hex from these three PNGs — **Low** (mobile/compression); defer to media digest.  
2. Distinct “Model” top-tab muted-teal fill — described in capture notes; invent-free peak **not** isolated in top-bar crop (text AA / light glyphs dominate). Leave **TBD**; do not invent.  
3. Handle-hover yellow — still open (unchanged).

## Sources

- `/workspace/research/modo-erik-screens-2026-10-27/*.png` (Erik, 2026-10-27)  
- Prior invent-free: `/workspace/research/modo-factory-hex-from-media.md`  
- Token map: `/workspace/research/modo-theme-gui-tokens.md`  
- Decisions log: `/workspace/research/modo-theme-decisions-log.md`  
- Annotated regions: `/workspace/tmp/modo-hex/erik-screens-annotated/`
