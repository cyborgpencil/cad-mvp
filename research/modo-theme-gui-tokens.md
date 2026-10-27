# Modo → cad-mvp GUI token map (theme prep)

Status: invent-free digest (MVP Research Digest). Compiled **2026-10-26 ~8:48 PM MT**.  
**Fold (2026-10-27):** flat viewport only (Erik ~11:24 AM MT revoke); modo sel/hover `#ffa829` / `#8cb4c7` shipped on main via [#231](https://github.com/cyborgpencil/cad-mvp/pull/231); panel/cool chrome from Erik-screen digest = **reference / later apply**, not product locks this tip; GL gradient stops = **source only**.

Builds on prior Modo GUI pass (box path `/workspace/modo-research-notes.md` has no in-repo counterpart; [gui/modo-tools.md](gui/modo-tools.md), [gui/modo-selection-primitives.md](gui/modo-selection-primitives.md), [prompts/modo-restyle.md](../prompts/modo-restyle.md)).  
Themes named **`default`** / **`modo`** — theme code on main via #206 + flat #229 + sel/hover #231. This file maps tokens invent-free.

## Erik likes (Chief, 2026-10-26 — theme feature; revised 2026-10-27)

Capture for the `modo` theme (no hex invented here beyond shipped locks):

1. **High-contrast orange selection** — shipped `#ffa829` (#231; Erik ~11:37 AM MT)
2. **Flat viewport backdrop only** — Erik ~11:24 AM MT (was "viewport background gradient"; revoked)
3. **Muted teal buttons** — product `--accent` `#14756e` (chrome B)

Note: Foundry docs describe Modo **active chrome** (tabs/tools/viewport thumb) as **orange**, not teal. Erik's muted-teal **buttons** + orange **selection** is an intentional product preference for `modo`, not a claim that Modo factory chrome is teal. Prior restyle prompt already flagged docs-orange vs Erik-teal ([modo-restyle.md](../prompts/modo-restyle.md)). Chief lock **B**: muted-teal active; orange for selection only (2026-10-26 ~10:36 PM MT).

## Sources

### Prior box research
- Box path `/workspace/modo-research-notes.md` (2026-10-21) — selection orange; hover light blue; hex TBD. No in-repo counterpart; link dropped.
- [gui/modo-selection-primitives.md](gui/modo-selection-primitives.md) — `--sel-color` / `--hover-color` named
- [gui/modo-tools.md](gui/modo-tools.md) — orange active tab/tool; no teal hex published
- [prompts/modo-restyle.md](../prompts/modo-restyle.md) — Erik teal-tone direction
- [modo-factory-hex-from-media.md](modo-factory-hex-from-media.md) — invent-free media hex (2026-10-27 ~11:30 AM MT)
- [modo-factory-hex-from-erik-screens-2026-10-27.md](modo-factory-hex-from-erik-screens-2026-10-27.md) — invent-free Erik-screen panel/cool + GL stops (2026-10-27 ~1:35 PM MT)

### Foundry Modo (official help)
- Selection modes (selected = orange): https://learn.foundry.com/modo/current/content/help/pages/modeling/selection_modes_types.html
- Tool controls (pre-highlight = light blue → selected orange): https://learn.foundry.com/modo/current/content/help/pages/modo_interface/standard_tool_controls.html  
  (also: https://modosdk.foundry.com/modo/14.2/content/help/pages/modo_interface/standard_tool_controls.html)
- Display prefs Colors (Selection, Selection Fill, Background, Handles, Axis X/Y/Z; app chrome not editable here): https://learn.foundry.com/modo/current/content/help/pages/preferences/pref_display.html
- 3D Viewport Properties — GL Background **Gradient** = "gray gradient shading that is multiplied over the viewport color": https://learn.foundry.com/modo/content/help/pages/modo_interface/3d_viewport_properties.html
- UI conventions (active tab name orange; active button orange; inactive tabs light gray / darker gray background tabs; viewport thumb orange when active): https://learn.foundry.com/modo/current/content/help/pages/modo_interface/ui_conventions.html
- Community confirm Gradient is default GL Background on most viewports: https://community.foundry.com/discuss/topic/130700/changing-background-color-in-modo-10-2-ver-2

### cad-mvp repo
- `web/index.html` `:root` tokens; flat viewport via #229; modo sel/hover via #231
- Raw path: https://github.com/cyborgpencil/cad-mvp/blob/main/web/index.html

## Current cad-mvp tokens (quoted / shipped)

From `web/index.html` `:root` freeze archaeology (comment in-file: "Erik asked for a teal tone. Docs show orange highlights. One accent: --accent.") — default snapshot:

| Token | Current value (`default`) |
| --- | --- |
| `--bg` | `#0e2429` |
| `--top` | `#10262b` |
| `--panel` | `#123038` |
| `--panel-2` | `#163840` |
| `--ribbon` | `#14343c` |
| `--field` | `#0e2429` |
| `--status` | `#10262b` |
| `--ink` | `#f4fbfb` |
| `--muted` | `#d5e4e2` |
| `--tab-bg` | `#1a3036` |
| `--tab-active` | `#1b454c` |
| `--accent` | `#14756e` |
| `--hover-color` | `#d7f4ff` (`default`); **`modo` shipped `#8cb4c7`** (#231) |
| `--sel-color` | `#ff4fd8` (`default`); **`modo` shipped `#ffa829`** (#231) |
| `--axis-x` | `#ff2d2d` |
| `--axis-y` | `#2ee66b` |
| `--axis-z` | `#3d7eff` |
| `--handle-hover` | `#efe07a` |
| `--active-fill` | `#5b3cc4` (`default`); `modo` active uses `--accent` `#14756e` (lock B) |
| `--active-border` | `#ffffff` |

**Viewport background — flat only (product).** Erik ~11:24 AM MT; #229 on main uses `var(--bg)` / clear. Do not reintroduce CSS/WebGL viewport gradient.

**Superseded freeze archaeology** (not a product goal). At earlier tip `#viewport` once quoted:

```css
background: radial-gradient(1200px 700px at 50% 42%, #1a454c 0%, #123038 55%, #0e2429 100%);
```

JS reads `--sel-color` via `getComputedStyle(document.documentElement)` for canvas selection paint.

## Modo-sourced colors (hex / gradient)

| Element | Named in docs | Hex / stops | Notes |
| --- | --- | --- | --- |
| Selection (component/item) | **orange** | **`#ffa829` shipped** (`modo`) | Media digest High; Erik ~11:37 APPROVED; #231 on main |
| Pre-highlight / hover | **light blue** | **`#8cb4c7` shipped** (`modo`) | Erik ~11:37 APPROVED; #231 on main |
| Active tab / active tool button / active viewport thumb | **orange** | `#f49c1c` / `#fb9909` **ref only** | Product active stays lock B `#14756e`; do not apply factory orange to active chrome |
| Inactive tab name | light gray | **TBD** | ui_conventions |
| Background tabs | darker gray | **TBD** | ui_conventions |
| GL Background Gradient | gray gradient × viewport Background color | **source only** (see digests) | **Not** a cad-mvp product goal (flat lock) |
| Axis X / Y / Z | red / green / blue | **TBD** | pref_display + prior notes |
| Handle hover | yellow | **TBD** | prior notes / transform docs |
| App UI chrome teal | — | product `#14756e` | cad-mvp; not Foundry-published Modo factory button fill |

### Panel / cool chrome — research reference / later apply (not product locks this tip)

From [modo-factory-hex-from-erik-screens-2026-10-27.md](modo-factory-hex-from-erik-screens-2026-10-27.md) (High confidence samples):

| Element | Hex | Role |
| --- | --- | --- |
| Panel gray (primary) | `#5e5f61` | toolbox / toolbar body |
| Panel gray (darker) | `#474747` | wells / Properties body |
| Panel gray (deep) | `#353739` | nested / Shading tree |
| Muted cool chrome | `#5f6367` | blue-gray panel |
| Cool field / section | `#91989e` | Properties section fills |

Do **not** apply these to `web/` from this fold. Later invent-free Doc brief if Chief orders.

### GL / viewport gray-gradient stops — **Modo-factory reference / source only**

**Not a cad-mvp `modo` theme goal.** Flat backdrop stands.

Media digest (video): `#646b6d` → `#343a3c` → `#333a3c`.  
Erik screens: `#565a5e` → `#4a4d50` → `#383b3f`.

## Mapping table (token/element → current → modo → source)

| Token / element | Current (`default` snapshot) | `modo` | Source / status |
| --- | --- | --- | --- |
| `--sel-color` (selection) | `#ff4fd8` (magenta) | **`#ffa829`** | Shipped #231; Erik ~11:37 |
| `--hover-color` | `#d7f4ff` | **`#8cb4c7`** | Shipped #231; Erik ~11:37 |
| Viewport background | flat `#229` (`--bg` / clear) | **flat** | Erik ~11:24; gradient revoked |
| Buttons / chrome fill (idle) | `--tab-bg` `#1a3036`, panels teal family | **Muted teal** buttons | `--accent` `#14756e` (cad-mvp) |
| Active tool / units / `.is-on` | `--active-fill` `#5b3cc4` (purple) | **muted teal `--accent` `#14756e`** | Chief lock **B** |
| `--accent` | `#14756e` | muted-teal button + active | cad-mvp; lock B |
| Axis / handle hover | `#ff2d2d` / `#2ee66b` / `#3d7eff` / `#efe07a` | keep unless later brief | Names sourced; exact Modo-match hex TBD if Doc wants |
| Panel / top / ribbon | dark teal stack | panel/cool from Erik screens = **research only** | later apply TBD |

### Conflict closed (not invent)

- **Modo docs:** orange = selection **and** active UI chrome.
- **Erik / Chief for this theme:** orange = selection (`#ffa829`); buttons + active = muted teal (`#14756e`); viewport = **flat**. Lock **B**.

## Open / later (not this fold)

1. Panel / cool chrome product apply from Erik-screen hex table (reference only now).
2. Modo factory active-button orange hex as product (unused under lock B; `#f49c1c` ref only).
3. Handle-hover yellow exact factory hex.
4. Distinct "Model" top-tab muted-teal fill (Erik screens TBD; do not invent).

## Sources (fold)

- [modo-factory-hex-from-media.md](modo-factory-hex-from-media.md)
- [modo-factory-hex-from-erik-screens-2026-10-27.md](modo-factory-hex-from-erik-screens-2026-10-27.md)
- [prompts/antigravity-theme-default-modo.md](../prompts/antigravity-theme-default-modo.md)
