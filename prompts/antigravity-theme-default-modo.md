# Antigravity Default + Modo themes

The app exposes two themes named exactly **`default`** and **`modo`**. `default` is the frozen `:root` snapshot plus a **flat** viewport backdrop (`--bg` / clear). `modo` is high-contrast orange selection, a **flat** viewport backdrop, and muted teal buttons, with active chrome locked to **B** (muted-teal active; orange for selection only). A top-bar **info** icon opens About (app version) and the theme switcher. Placement stays **TBD**. This file is the Antigravity feed. It does not change the app by itself.

**Docs correction (2026-10-27):** Erik ~11:24 AM MT revoked the viewport-gradient goal. Live theme musts are **flat viewport backdrop only**. The historical freeze quote of `radial-gradient(...)` below is **superseded freeze archaeology** — not a restore, smoke, or success must. Flat landed on main via [#229](https://github.com/cyborgpencil/cad-mvp/pull/229). Modo factory sel/hover hex landed on main via [#231](https://github.com/cyborgpencil/cad-mvp/pull/231) (`--sel-color` `#ffa829` / `--hover-color` `#8cb4c7`). This tip is **docs-only** — no `web/` edits.

**Gate:** Theme **code** for the original Default+Modo slice already shipped (see #206 / #229 / #231 on main). This prompts file remains the invent-free theme brief for tip-match of docs. Do not re-spec gestures #199.

**Hard lock:** Prefer a worktree under `C:\Dev\`; do not invent a new path or create folders from this brief. Do not invent Erik specs. Theme **product** apply for panel/cool chrome from Erik-screen digests stays out of this file's live musts (research fold only). Do not reintroduce a CSS/WebGL viewport gradient. Chrome B stays `#14756e`. Orange product sel stays `#ffa829`; `#f49c1c` is chrome ref only; reject `#ff8000`.

**Source of truth:**

- Erik via 3T, Chief, 2026-10-26 ~8:47 PM MT. End-of-queue theme feature: themes **Default** and **Modo**, a switcher, and an About/version icon.
- Erik revoke, 2026-10-27 ~11:24 AM MT: **flat viewport backdrop only**; gradient goal revoked.
- Erik APPROVED, 2026-10-27 ~11:37 AM MT: Modo `--sel-color` `#ffa829`; `--hover-color` `#8cb4c7`. Standing Modo-theme always-approved ~11:38 AM MT.
- `research/modo-theme-gui-tokens.md` (PR #200, merge `b0dd4df`; later flat + sel/hover fold). Cite that digest for the token map. Panel/cool chrome from `research/modo-factory-hex-from-erik-screens-2026-10-27.md` = research reference / later apply — **not** product locks in this brief.
- Chief lock, 2026-10-26 ~10:36 PM MT: **Active chrome = B** (muted-teal active; orange for selection only). This replaces the digest's "leave A vs B TBD". Erik has no separate later pick. A (orange active chrome, as in the Modo docs) is not the lock.
- Freeze snapshot of `web/index.html` `:root` on main `b0dd4df` (default tokens). Quote only those `:root` values for archaeology. Do not invent hex.
- Code on main: #229 flat `var(--bg)` / clear; #231 modo `--sel-color` `#ffa829` / `--hover-color` `#8cb4c7`; chrome B `#14756e`.

Erik likes (updated invent-free; no hex invented beyond shipped #231):

1. High-contrast orange selection
2. **Flat viewport backdrop only** (Erik ~11:24 AM MT; was "viewport background gradient")
3. Muted teal buttons

## Goal
Describe these sourced behaviors for invent-free tip-match. Themes are named exactly **`default`** and **`modo`**.

- **`default`** is the snapshot of freeze `:root` at `b0dd4df` plus a **flat** viewport backdrop (`--bg` / clear). Do not restore the superseded freeze radial as a live must.
- **`modo`** maps from the digest + Erik locks: high-contrast orange selection (shipped `--sel-color` `#ffa829` via #231); **flat** viewport backdrop; muted teal buttons. Muted teal uses existing cad-mvp `--accent` `#14756e`. Hover on `modo` is shipped `--hover-color` `#8cb4c7` via #231. Default freeze still keeps `--sel-color` `#ff4fd8` / `--hover-color` `#d7f4ff`.
- **Active chrome = B.** On `modo`, active chrome is muted teal. Orange is selection only. Reuse `--accent` `#14756e`. Do not paint active chrome orange. Do not invent a new teal hex. Do not keep `default`'s `--active-fill` `#5b3cc4` as the `modo` active color.
- Theme switcher, and a top-bar **info** icon that opens About (app version) together with the theme switcher. **Placement TBD.**

Where a line is **TBD**, leave it TBD. The B lock is not TBD. Flat viewport is not TBD.

### `default` snapshot (freeze `b0dd4df`)

Digest table (every value matches the file):

| Token | Value |
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

The same `:root` block also contains these properties. They are part of the `default` snapshot. The digest table did not list them. Do not drop them. Do not treat the layout lengths as new switcher sizes.

```css
--finish: #123830;
--tab-ink: #d5e4e2;
--tab-track: #0e2429;
--line: rgba(244, 251, 251, 0.14);
--line-strong: #0a181c;
--accent-dim: color-mix(in srgb, var(--accent) 32%, transparent);
--centre-color: #d8dde6;
--measure: #fff8e8;
--pass: #c8f5df;
--pass-bg: #0e3d2c;
--fail: #ffd0d0;
--fail-bg: #3f1518;
--banner-bg: #12343a;
--banner-ink: #f4fbfb;
--disabled-bg: #2a454a;
--disabled-ink: #d5e4e2;
--shadow: 0 10px 28px rgba(0, 0, 0, 0.45);
--top-h: calc(48px + env(safe-area-inset-top, 0px));
--status-h: 44px;
--phone-tabs-h: calc(56px + env(safe-area-inset-bottom, 0px));
```

**Superseded freeze archaeology** (not a live restore / smoke / success must). At freeze `b0dd4df`, `#viewport` in `web/index.html` quoted:

```css
background: radial-gradient(1200px 700px at 50% 42%, #1a454c 0%, #123038 55%, #0e2429 100%);
```

Erik ~11:24 AM MT revoked the gradient goal. Live product is **flat** via `#229` (`var(--bg)` / clear). Keep the radial quote only as history. Do not restore it. Do not reintroduce CSS/WebGL viewport gradient.

In-file `:root` comment, quoted so it is not rewritten: "Erik asked for a teal tone. Docs show orange highlights. One accent: --accent."

### `modo` shipped selection / hover (main #231)

| Token | `modo` (shipped) | `default` freeze |
| --- | --- | --- |
| `--sel-color` | `#ffa829` | `#ff4fd8` |
| `--hover-color` | `#8cb4c7` | `#d7f4ff` |

`#f49c1c` remains factory active-chrome orange **ref only** (lock B). Reject `#ff8000`.

## Workflow
1. Read `research/modo-theme-gui-tokens.md` and the freeze snapshot above. Copy behavior from those sources, the Chief B lock, Erik ~11:24 flat revoke, and shipped #229 / #231 only.
2. Expose themes named exactly `default` and `modo`, switchable by the user.
3. `default` restores the freeze `:root` snapshot (every quoted `:root` value). Viewport backdrop is **flat** (`--bg` / clear) — **not** the superseded freeze radial.
4. `modo` selection is high-contrast orange via shipped `--sel-color` `#ffa829` (#231). Canvas paint already reads `--sel-color`. Do not invent a new selection hex. Default freeze keeps `#ff4fd8`.
5. `modo` viewport backdrop is **flat** only (Erik like #2 as revised ~11:24). Do not keep, author, or assert a viewport background gradient. Modo GL gray-gradient stops in research digests are **factory reference / source only** — not a product TBD to choose teal-vs-gray gradient.
6. `modo` buttons are muted teal (Erik like #3). Use existing `--accent` `#14756e`. Do not invent a teal hex. The digest states this value is cad-mvp, not a Foundry-published Modo factory hex.
7. `modo` active chrome is **B**: muted-teal active; orange for selection only. Point the active tool / units / `.is-on` treatment at existing `--accent` `#14756e`. Do not use orange for active chrome. Do not invent an active-button orange hex. Modo factory active-button / active-tab orange stays unpublished and is unused under this lock.
8. Add the theme switcher and a top-bar info icon that opens About (app version) and the theme switcher. Placement is **TBD**. Do not choose a slot, alignment, or pixel position. Reuse an existing info / About control if one is already in `web/`.
9. About shows the app version. Do not invent a version string. `PROJECT_VERSION` in `web/project-file.mjs` (`1`) is the file-format version. Do not relabel it as the app version. If no app version string exists, leave that string **TBD**.
10. Tokens the digest leaves **TBD** (panel/cool chrome apply, etc.) stay research-only until a later invent-free apply brief. That hold is not a claim those snapshot values are Modo factory colors. Do not retune axis, handle, panel, ribbon, or top chrome to a new hex from this brief.

## Do not bake / TBD
Do not invent and do not bake any of the following. They stay **TBD** (or research-only):

- Exact placement of the info icon, About, and the theme switcher
- The app version string
- Any new control ids
- Any new CSS selectors
- Any new pixel sizes
- Any invented hex
- Icon art
- Hotkeys
- Panel / cool chrome product apply from Erik-screen digests (`#5e5f61` / `#474747` / `#353739` / `#5f6367` / `#91989e` = research reference only this wave)
- Modo factory active-button / active-tab orange hex (unused under lock B; still unpublished; `#f49c1c` ref only)

Resolved, and therefore not TBD:

- Active chrome is **B** (muted-teal active; orange for selection only). Chief, 2026-10-26 ~10:36 PM MT.
- Viewport backdrop is **flat only**. Erik ~11:24 AM MT; #229 on main.
- Modo `--sel-color` `#ffa829` and `--hover-color` `#8cb4c7` shipped via #231 (Erik ~11:37 AM MT). Default freeze still `#ff4fd8` / `#d7f4ff`.
- Gray-gradient / teal-vs-gray viewport gradient choice is **struck as product TBD**. Modo GL gray stops = factory reference only.

## Out of scope
- Gestures + float/dock brief #199 (merge `d167e21` / tip `be0d5f3`). Already on main. Do not re-spec it.
- X-ray select-through (#195 brief / #197 impl). Already on main. Do not re-spec it.
- Panel labels + always-visible chrome (#191 brief / #193 impl). Already on main. Do not re-spec them.
- `prompts/modo-restyle.md`. Prior direction the digest cites. This slice is the two named themes, not that restyle.
- Editing `mvp/` or `UPDATES.md` from this brief (RK owns UPDATES at merge).
- Kernel / C++ / wasm rebuild. Do not commit `.wasm`, `web/cadcam.wasm`, or `web/dist/`. Do not edit a root `PROGRESS.md`.
- Reintroducing CSS/WebGL viewport gradient. Gradient never visually shipped as a product goal after Erik ~11:24.
- Items 6 / 7 / 10; B3 / B5; Rust #4.

## Smoke
Manual wake smoke on Pages. No new smoke harness. Reuse `tests/deploy_smoke.py` only if that reuse is clearly required; this brief does not require it. No invented pixel asserts. Because no smoke path is added here, do not print a done marker.

Check sourced behavior only. Do not assert placement, control ids, CSS selectors, pixel sizes, icon art, hotkeys, a guessed app version, or any TBD hex.

1. The user can switch a theme named `default` and a theme named `modo`.
2. `default` matches the freeze `:root` snapshot (quoted `:root` values, including `--sel-color` `#ff4fd8` and `--active-fill` `#5b3cc4`) and a **flat** viewport backdrop (`--bg` / clear). Do **not** assert the superseded freeze radial.
3. `modo` selection is high-contrast orange via shipped `--sel-color` `#ffa829` (#231), and orange is selection only (lock B). Hover uses shipped `--hover-color` `#8cb4c7`. An invented selection hex fails.
4. `modo` (and `default`) show a **flat** viewport backdrop. Do **not** assert a viewport background gradient, gray stops, or the superseded teal radial.
5. `modo` buttons are muted teal via existing `--accent` `#14756e`. `modo` active chrome (active tool / units / `.is-on`) is muted teal via that same `--accent`. Active chrome is not orange. Lock B.
6. Top-bar info opens About. About shows the app version and the theme switcher. Do not assert where they sit.

## Success Criteria
Must PASS at tip-match. Cite Erik via 3T, Chief, 2026-10-26 ~8:47 PM MT; Erik flat revoke ~11:24 AM MT; Erik sel/hover APPROVED ~11:37 AM MT; `research/modo-theme-gui-tokens.md` (PR #200 / later fold); Chief lock B, 2026-10-26 ~10:36 PM MT; freeze `:root` on main `b0dd4df`; shipped #229 / #231. Only sourced behavior is on this bar.

1. The app exposes themes named exactly `default` and `modo`, switchable by the user. Reuse existing CSS variables where they already exist. Do not invent chrome beyond the stated themes and the info / About + switcher concept.
2. `modo` applies high-contrast orange selection (shipped `#ffa829`), a **flat** viewport backdrop, and muted teal buttons (Erik likes as revised). Muted teal buttons use existing `--accent` `#14756e`. Do not invent a Modo factory hex. Do not require a viewport gradient.
3. `modo` active chrome is **B**: muted-teal active, using existing `--accent` `#14756e` for the active tool / units / `.is-on` treatment. Orange is selection only.
4. Top-bar info opens About. About shows the app version and provides theme switching. Placement stays TBD when the app does not already place that control.
5. No invented TBD hex and no invented placement. Active chrome is B. Flat viewport stands. Zero live must-PASS requiring a viewport gradient.

Outside this hard bar: panel/cool chrome product apply, Modo GL Background gray-gradient stops (source only), factory active-button orange hex (`#f49c1c` ref only), the app version string, placement of info / About / the switcher, new control ids, new CSS selectors, new pixel sizes, icon art, hotkeys, gestures #199, X-ray #195/#197, panel labels #191/#193, `prompts/modo-restyle.md`, `mvp/`, `UPDATES.md`, kernel / C++ / wasm.

## Done
Draft until tip-match: Dig primary (research fold COMMENT), Doc Steward second (brief/prompt COMMENT). Author does not self-APPROVE. Repo Keeper undrafts and plain-merges. UPDATES cascade is RK-owned after merge. Report the prompt PR link and tip SHA.
