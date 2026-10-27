# Modo factory hex from media (invent-free)

**Owner:** MVP Research Digest (executor pass)  
**Compiled:** 2026-10-27 ~11:30 AM MT (America/Denver)  
**Product note:** cad-mvp `modo` theme goals remain **orange selection** + **muted teal buttons** + **flat viewport backdrop** (Erik lock 2026-10-27 ~11:24 AM MT). Active chrome stays **lock B** (muted-teal active; orange for selection only). Values below are **Foundry Modo factory reference** from media/docs — not an instruction to copy Modo orange onto active chrome.

## Media inventory (what is / isn’t Modo)

| Path | Shows Foundry Modo? | Notes |
| --- | --- | --- |
| `/workspace/uploads/s1.png`–`s4.png` | **No** | cad-mvp / local `127.0.0.1:8787` CAD/CAM UI (teal/purple) |
| `/workspace/uploads/s5.png`–`s7.png`, `d.png` | **No** | Orca Slicer / Bambu-style slicer dialogs |
| `/workspace/uploads/*.heic` (5 files) | **No** | Outdoor telecom/junction-box photos; converted under `heic/` for check only |
| YouTube `https://youtu.be/HhuccQ20YVM` | **Yes** | Foundry Learn “Modo for Industrial Design: 1. Beginner Introduction”; downloaded via yt-dlp → `video/modo-intro.mp4` (~7:19); frames in `video/frames/`, `video/scan/`, `video/hi/` |
| Official help PNGs under `help-imgs/` | **Yes** | From `learn.foundry.com/modo/current/content/resources/images/...` (selection modes, tabs, buttons, polygon selection, pie menu, tool handles) |

**Tooling:** venv at `tmp/modo-hex/venv` with `pillow` + `pillow-heif`; yt-dlp at `/home/box/.local/bin/yt-dlp`.

## Sampling method

1. Prefer **exact dominant pixel** counts on official lossless/help PNGs over video (H.264 shifts orange).  
2. Video used for GL Background gray stops + panel chrome (empty Perspective viewport).  
3. No invented values. Web-search synthesis claiming `#ff8000` / `1.0,0.5,0.0` was **not** found in Foundry docs body text and is **rejected**.  
4. Docs still only name colors (“orange”, “light blue”); hex comes from media pixels only.

## Factory hex table

| Element | Hex | RGB | Best source | Confidence |
| --- | --- | --- | --- | --- |
| **Active chrome / mode-button fill** (Polygons/Vertices/Edges active) | `#f49c1c` | 244,156,28 | `help-imgs/selection_mode_polygons.png` / `selection_mode_vertices.png` / `selection_mode-icon-buttons.png` — exact pixel count peak | **High** |
| Active vertical tool tab (Basic) | `#fb9909` | 251,153,9 | `help-imgs/buttons.png` peak | High (same family as `#f49c1c`) |
| Active tab **text** (Items list tab name) | `#f49c1c` (also anti-aliased `#da8f32`) | 244,156,28 | `help-imgs/tabs.png`, `select_layer.png` | High |
| **Selection fill** (selected polygons/item solid) | `#ffa829` | 255,168,41 | `help-imgs/shortest_path_poly_2.png` (2837× exact), `selectionmode_polys.png`, `tool_handles_thumb_377_0.png` selected sphere | **High** |
| Selection / pie-menu / HUD orange (same family) | `#fca828` / `#ffa828` | 252,168,40 / 255,168,40 | `help-imgs/piemenu.png` modeQ | High |
| Selected **item-name text** in Items List | `#f49c1c` | 244,156,28 | `help-imgs/select_layer.png` | High |
| Pre-highlight / “light blue” (docs name) | `#8cb4c7` | 140,180,199 | Dominant cool blue in `help-imgs/partial_lasso.gif` mesh/overlay region; also `#96b7cc` in `alternate_buttons.png` | **Medium** — docs say hover pre-highlight is light blue; no dedicated hover still with labeled pre-highlight. Treat as candidate, not locked. |
| Bright cyan UI accent (Action Center–class) | `#4ce7ec` (peak); also `#50cdd1`, `#54abae` | 76,231,236 / 80,205,209 / 84,171,174 | `partial_lasso.gif` | Medium — accent on toggles/icons, **not** primary button fill |
| Muted teal/gray-green icon chrome | `#5a757c` | 90,117,124 | `buttons.png` / `alternate_buttons.png` teal cluster median | Medium — **not** a Modo “teal button” factory system; factory primary accent is orange |
| Panel / toolbox chrome | `#49494b` | 73,73,75 | video `h007.png` left toolbox | Medium (compressed) |
| Modes-bar idle button fill | `#646464` | 100,100,100 | video `h007.png` | Medium |
| Top menu bar | `#464649` | 70,70,73 | video `h007.png` | Medium |
| Axis X / Y / Z (handles) | ~`#e43333` / `#33cc33` / `#3366fa` family | sparse samples | `tool_handles_thumb_377_0.png` | Low–medium (few pixels) |
| Handle hover yellow | **TBD** | — | Docs name yellow; no clean yellow-hover still in this pass | Open |

### GL Background gray-gradient stops — **Modo-factory reference only**

**Not a cad-mvp `modo` theme goal** (Erik lock: flat viewport backdrop only).

From empty Perspective viewport in reference video frame `video/hi/h007.png` (1920×1080):

| Stop | Hex | RGB |
| --- | --- | --- |
| Upper / lighter | `#646b6d` | 100,107,109 |
| Center | `#343a3c` | 52,58,60 |
| Lower / darker | `#333a3c` | 51,58,60 |

Docs: GL Background **Gradient** = gray gradient multiplied over viewport Background color (`3d_viewport_properties`). Exact factory Background preference float still unpublished.

## Recommended candidates for Erik / Doc (selection only)

For replacing cad-mvp freeze `--sel-color` `#ff4fd8` with Modo-factory orange **without inventing**:

1. **Primary pick — selection fill:** `#ffa829` (official help polygon selection + selected sphere).  
2. **Chrome/text orange (if ever needed for reference UI):** `#f49c1c` (active mode button / selected item name).  
3. **Do not** apply factory orange to active tool chrome in product — Chief lock **B** keeps active = muted teal `--accent` `#14756e`.

Hover light-blue: **`#8cb4c7` approved** for `modo` `--hover-color` (Erik ~11:37 AM MT; was medium-confidence candidate).

Muted teal buttons: keep product `#14756e` — **not** claimed as Modo factory button fill (factory accent is orange).

## Erik apply lock (2026-10-27)

- **~11:37 AM MT:** APPROVED web/PR apply — `modo` `--sel-color` `#ffa829`; `--hover-color` may move `#d7f4ff` → `#8cb4c7`; `#f49c1c` chrome/text **ref only** (lock B); GL stops Modo-ref only (flat); teal stay `#14756e`; reject `#ff8000`.
- **~11:38 AM MT:** During this CAD project, Modo/MODO theme changes are **always approved** — do not ask Erik per change; proceed invent-free from sourced Dig/Doc tokens.
- Doc apply brief: `/workspace/research/antigravity-modo-sel-hex-apply-brief-2026-10-27.md` (Pilot one agy **after** flat-bg #229 on main).

## Video download note

Prior box note (2026-10-21) said yt-dlp hit YouTube 429. This pass **succeeded** without cookies: `/home/box/.local/bin/yt-dlp` → `video/modo-intro.mp4`.

## File map on box

```
/workspace/tmp/modo-hex/
  modo-factory-hex-from-media.md   ← this file
  venv/                            pillow + pillow-heif
  heic/*.png                       converted HEICs (not Modo)
  video/modo-intro.mp4
  video/frames/  video/scan/  video/hi/
  help-imgs/                       official Foundry help assets
  annotated/                       region overlays from sampling
```

## Sources

- https://youtu.be/HhuccQ20YVM  
- https://learn.foundry.com/modo/current/content/help/pages/modeling/selection_modes_types.html  
- https://learn.foundry.com/modo/current/content/help/pages/modo_interface/standard_tool_controls.html  
- https://learn.foundry.com/modo/current/content/help/pages/modo_interface/ui_conventions.html  
- https://learn.foundry.com/modo/current/content/help/pages/preferences/pref_display.html  
- https://learn.foundry.com/modo/current/content/help/pages/modo_interface/3d_viewport_properties.html  
- Prior: `/workspace/research/modo-theme-gui-tokens.md`, `/workspace/modo-research-notes.md`
