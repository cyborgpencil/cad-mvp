# Modo → cad-mvp GUI token map (theme prep)

Status: invent-free digest (MVP Research Digest). Compiled **2026-10-26 ~8:48 PM MT**.
Builds on prior Modo GUI pass (box path `/workspace/modo-research-notes.md` has no in-repo counterpart; [gui/modo-tools.md](gui/modo-tools.md), [gui/modo-selection-primitives.md](gui/modo-selection-primitives.md), [prompts/modo-restyle.md](../prompts/modo-restyle.md)).
Themes named **`default`** / **`modo`** are for a later Doc invent-free brief (after X-ray). This file only maps tokens.

## Erik likes (Chief, 2026-10-26 — theme feature)

Capture for the future `modo` theme (no hex invented here):

1. **High-contrast orange selection**
2. **Viewport background gradient**
3. **Muted teal buttons**

Note: Foundry docs describe Modo **active chrome** (tabs/tools/viewport thumb) as **orange**, not teal. Erik’s muted-teal **buttons** + orange **selection** is an intentional product preference for `modo`, not a claim that Modo factory chrome is teal. Prior restyle prompt already flagged docs-orange vs Erik-teal ([modo-restyle.md](../prompts/modo-restyle.md)).

## Sources

### Prior box research
- Box path `/workspace/modo-research-notes.md` (2026-10-21) — selection orange; hover light blue; hex TBD. No in-repo counterpart; link dropped.
- [gui/modo-selection-primitives.md](gui/modo-selection-primitives.md) — `--sel-color` / `--hover-color` named; hex TBD
- [gui/modo-tools.md](gui/modo-tools.md) — orange active tab/tool; no teal hex published
- [prompts/modo-restyle.md](../prompts/modo-restyle.md) — Erik teal-tone direction; palette TBD

### Foundry Modo (official help)
- Selection modes (selected = orange): https://learn.foundry.com/modo/current/content/help/pages/modeling/selection_modes_types.html
- Tool controls (pre-highlight = light blue → selected orange): https://learn.foundry.com/modo/current/content/help/pages/modo_interface/standard_tool_controls.html  
  (also: https://modosdk.foundry.com/modo/14.2/content/help/pages/modo_interface/standard_tool_controls.html)
- Display prefs Colors (Selection, Selection Fill, Background, Handles, Axis X/Y/Z; app chrome not editable here): https://learn.foundry.com/modo/current/content/help/pages/preferences/pref_display.html
- 3D Viewport Properties — GL Background **Gradient** = “gray gradient shading that is multiplied over the viewport color”: https://learn.foundry.com/modo/content/help/pages/modo_interface/3d_viewport_properties.html
- UI conventions (active tab name orange; active button orange; inactive tabs light gray / darker gray background tabs; viewport thumb orange when active): https://learn.foundry.com/modo/current/content/help/pages/modo_interface/ui_conventions.html
- Community confirm Gradient is default GL Background on most viewports: https://community.foundry.com/discuss/topic/130700/changing-background-color-in-modo-10-2-ver-2

### cad-mvp repo
- `web/index.html` `:root` tokens on **main** (file last touched `146cb9e597a8b872776d1d4ac34fd61724e33740`; main HEAD at fetch `70c522d441acf8741ec9438ce6fc252b5f474860`)
- Raw path: https://github.com/cyborgpencil/cad-mvp/blob/main/web/index.html

## Current cad-mvp tokens (quoted)

From `web/index.html` `:root` (comment in-file: “Erik asked for a teal tone. Docs show orange highlights. One accent: --accent.”):

| Token | Current value |
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
| `--hover-color` | `#d7f4ff` |
| `--sel-color` | `#ff4fd8` |
| `--axis-x` | `#ff2d2d` |
| `--axis-y` | `#2ee66b` |
| `--axis-z` | `#3d7eff` |
| `--handle-hover` | `#efe07a` |
| `--active-fill` | `#5b3cc4` |
| `--active-border` | `#ffffff` |

Viewport background (CSS class on viewport chrome; not a `:root` var today):

```css
background: radial-gradient(1200px 700px at 50% 42%, #1a454c 0%, #123038 55%, #0e2429 100%);
```

JS reads `--sel-color` via `getComputedStyle(document.documentElement)` for canvas selection paint (`web/index.html` ~line using `--sel-color`).

## Modo-sourced colors (hex / gradient)

| Element | Named in docs | Hex / stops | Notes |
| --- | --- | --- | --- |
| Selection (component/item) | **orange** | **TBD** | Docs name only; Preferences > Display > Colors > Selection |
| Pre-highlight / hover | **light blue** | **TBD** | standard_tool_controls |
| Active tab / active tool button / active viewport thumb | **orange** | **TBD** | ui_conventions |
| Inactive tab name | light gray | **TBD** | ui_conventions |
| Background tabs | darker gray | **TBD** | ui_conventions |
| GL Background Gradient | gray gradient × viewport Background color | **TBD** stops | 3d_viewport_properties; factory Background hex unpublished |
| Axis X / Y / Z | red / green / blue | **TBD** | pref_display + prior notes |
| Handle hover | yellow | **TBD** | prior notes / transform docs |
| App UI chrome teal | — | **TBD / not published** | No official teal hex; app chrome not in Display > Colors |

**No factory Modo hex values found** in official help or reputable community posts searched this pass. Any concrete hex for `modo` must come from Erik-approved eyedropper of a named screenshot / build, or Erik-picked values — not invented here.

## Mapping table (token/element → current → modo candidate → source/TBD)

| Token / element | Current (`default` snapshot) | `modo` candidate | Source / TBD |
| --- | --- | --- | --- |
| `--sel-color` (selection) | `#ff4fd8` (magenta) | High-contrast **orange** | Docs: orange. **Hex TBD** (Erik like #1) |
| `--hover-color` | `#d7f4ff` | Light blue (keep or adjust) | Docs: light blue. Current hex is **cad-mvp**, not Modo-factory-sourced → **confirm / TBD** |
| Viewport background | Teal radial `#1a454c → #123038 → #0e2429` | Keep a **gradient** (Erik like #2); Modo factory = gray gradient × bg | Pattern sourced; **stop hex TBD** if aiming at Modo-gray vs keep current teal gradient |
| Buttons / chrome fill (idle) | `--tab-bg` `#1a3036`, panels teal family | **Muted teal** buttons (Erik like #3) | Current `--accent` `#14756e` is already muted teal (**cad-mvp**). Modo docs use orange for *active* chrome — conflict flagged below |
| Active tool / units / `.is-on` | `--active-fill` `#5b3cc4` (purple) | **TBD** | Modo docs → orange active. Erik muted-teal buttons may prefer muted-teal active + orange only on selection. **Erik decide** |
| `--accent` | `#14756e` | Candidate for muted-teal button accent in `modo` | cad-mvp current; not Foundry-published |
| Axis / handle hover | `#ff2d2d` / `#2ee66b` / `#3d7eff` / `#efe07a` | Align with Modo RGB + yellow hover naming | Names sourced; **exact hex TBD** if Doc wants Modo-match |
| Panel / top / ribbon | dark teal stack | Snapshot into `default`; `modo` panel chrome **TBD** | No Modo app-chrome hex published |

### Conflict to flag (not invent)

- **Modo docs:** orange = selection **and** active UI chrome.
- **Erik likes for this theme:** orange = selection; buttons = muted teal; viewport = gradient.
- Doc brief must leave active-button treatment **TBD** unless Erik picks: (A) orange active like Modo, or (B) muted-teal active with orange reserved for selection only.

## Next steps (Doc brief — after X-ray lands)

Invent-free brief only; Dig does not tip PRs:

1. Themes named **`default`** (= snapshot of current `:root` + viewport gradient as of brief freeze SHA) and **`modo`** (= map above; orange selection + gradient + muted teal buttons; all unsourced hex left TBD).
2. Theme switch + top-bar **info** icon → About (app version) + theme switcher — **placement TBD**.
3. Do **not** invent orange / gray-gradient / teal-button hex; ask Erik for eyedropper source or approve candidates.
4. One agy for Pilot only after that brief is on main (Chief queue).

## Open TBDs

1. Modo factory selection orange hex / Selection Fill hex.
2. Modo factory hover light-blue hex.
3. Modo GL Background gray-gradient stop hex (and base Background hex).
4. Modo active-button / active-tab orange hex.
5. Whether `modo` active chrome follows Modo orange or Erik muted-teal (conflict above).
6. Whether viewport gradient in `modo` keeps current teal radial or switches to Modo-style gray×bg.
