# Antigravity Default + Modo themes

The app exposes two themes named exactly **`default`** and **`modo`**. `default` is the frozen `:root` snapshot plus the current viewport gradient. `modo` is high-contrast orange selection, a viewport background gradient, and muted teal buttons, with active chrome locked to **B** (muted-teal active; orange for selection only). A top-bar **info** icon opens About (app version) and the theme switcher. Placement stays **TBD**. This file is the Antigravity feed. It does not change the app by itself.

**Gate:** Theme **code** starts only after this file tip-matches on main **and** gestures brief #199 is already on main. #199 is on main (merge `d167e21` / tip `be0d5f3`). This prompts file is idle-fill prep and does not start the theme `agy` by itself. Do not re-spec #199.

**Hard lock:** Implementation is **Antigravity-only on Z13**. Pilot holds one `agy` until this file tip-matches on main, then owns one `agy`. Do not use Grok Build or Cursor for the handoff into code. Prefer a worktree under `C:\Dev\`; do not invent a new path or create folders from this brief. Do not commit from Antigravity; Pilot/Repo Keeper commit path owns that. Do not invent Erik specs. Stay in `web/` (JS, HTML, CSS). No kernel, C++, `src/`, bindings, or wasm rebuild.

**Source of truth:**

- Erik via 3T, Chief, 2026-10-26 ~8:47 PM MT. End-of-queue theme feature: themes **Default** and **Modo**, a switcher, and an About/version icon.
- `research/modo-theme-gui-tokens.md` at tip `f38aa66` (PR #200, merge `b0dd4df`). Doc Steward primary PASS on that research tip. Cite that digest for the token map. Anything it does not state stays **TBD**, except the active-chrome conflict below, which Chief closed after the digest was written.
- Chief lock, 2026-10-26 ~10:36 PM MT: **Active chrome = B** (muted-teal active; orange for selection only). This replaces the digest’s “leave A vs B TBD”. Erik has no separate later pick. A (orange active chrome, as in the Modo docs) is not the lock.
- Freeze snapshot of `web/index.html` `:root` and the `#viewport` background on main `b0dd4df`. Those values match the digest (digest file touch `146cb9e`; unchanged through `b0dd4df`). Quote only these. Do not invent hex.

Erik likes from the digest (no hex invented there):

1. High-contrast orange selection
2. Viewport background gradient
3. Muted teal buttons

## Goal
Implement these sourced behaviors in `web/` (JS, HTML, and CSS). No kernel, C++, `src/`, bindings, or wasm rebuild.

Themes are named exactly **`default`** and **`modo`**.

- **`default`** is the snapshot of current `:root` plus the viewport gradient at brief freeze `b0dd4df`. Quote below. Do not retune it.
- **`modo`** maps from the digest: high-contrast orange selection; a viewport background gradient; muted teal buttons. Muted teal uses the existing cad-mvp `--accent` `#14756e` the digest quotes. Do not invent a Modo factory hex.
- **Active chrome = B.** On `modo`, active chrome is muted teal. Orange is selection only. Reuse `--accent` `#14756e` for that muted-teal active treatment (the digest row “Active tool / units / `.is-on`”, which today paints from `--active-fill`). Do not paint active chrome orange. Do not invent a new teal hex. Do not keep `default`’s `--active-fill` `#5b3cc4` as the `modo` active color.
- Theme switcher, and a top-bar **info** icon that opens About (app version) together with the theme switcher. **Placement TBD.**

`web/` at `b0dd4df` has no theme switcher and no `default` / `modo` wiring. Reuse the existing custom properties, the `#viewport` background, and the existing `getComputedStyle(document.documentElement)` read of `--sel-color` for canvas selection paint. `.is-on` already uses `--active-fill`. Button chrome already uses `--accent`. If a path is missing, implement only the Erik/Chief behaviors in this Goal. Do not invent UI chrome beyond the two named themes and the info / About + switcher concept.

Where a line is **TBD**, leave it TBD. The B lock is not TBD.

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

Viewport background (not a `:root` variable today). Quote from `#viewport` in `web/index.html`:

```css
background: radial-gradient(1200px 700px at 50% 42%, #1a454c 0%, #123038 55%, #0e2429 100%);
```

In-file `:root` comment, quoted so it is not rewritten: “Erik asked for a teal tone. Docs show orange highlights. One accent: --accent.”

## Workflow
1. Read `research/modo-theme-gui-tokens.md` at `f38aa66` and the freeze snapshot above. Copy behavior from those sources and from the Chief B lock only.
2. Expose themes named exactly `default` and `modo`, switchable by the user.
3. `default` restores the freeze snapshot: every quoted `:root` value and the quoted viewport gradient.
4. `modo` selection role is high-contrast orange. The existing selection channel is `--sel-color`. Canvas paint already reads it. No factory orange hex is in the digest or in `web/index.html`. Do not add one. Do not override `--sel-color` with a new literal, the CSS keyword `orange`, or `#ff4fd8` labeled as orange. Leave the number **TBD** and say so in the implementation PR. That gap stays open until Erik supplies a hex. It does not drop the rest of `modo`.
5. `modo` keeps a viewport background gradient (Erik like #2). Whether that gradient stays the quoted teal radial or switches to a Modo-style gray gradient multiplied over the viewport color is **TBD**. Do not author new stops. Do not remove the gradient.
6. `modo` buttons are muted teal (Erik like #3). Use existing `--accent` `#14756e`. Do not invent a teal hex. The digest states this value is cad-mvp, not a Foundry-published Modo factory hex.
7. `modo` active chrome is **B**: muted-teal active; orange for selection only. Point the active tool / units / `.is-on` treatment at existing `--accent` `#14756e`. Do not use orange for active chrome. Do not invent an active-button orange hex. Modo factory active-button / active-tab orange stays unpublished and is unused under this lock.
8. Add the theme switcher and a top-bar info icon that opens About (app version) and the theme switcher. Placement is **TBD**. Do not choose a slot, alignment, or pixel position. Reuse an existing info / About control if one is already in `web/`. None is present at `b0dd4df`.
9. About shows the app version. Do not invent a version string. `PROJECT_VERSION` in `web/project-file.mjs` (`1`) is the file-format version. Do not relabel it as the app version. If no app version string exists, leave that string **TBD**.
10. Tokens the digest leaves **TBD** stay on the `default` snapshot for `modo`. That hold is not a claim that those snapshot values are Modo factory colors. Do not retune hover, axis, handle, panel, ribbon, or top chrome to a new hex.

## Do not bake / TBD
Do not invent and do not bake any of the following. They stay **TBD**:

- Modo factory selection orange hex
- Modo factory Selection Fill hex
- Modo factory hover light-blue hex (`--hover-color` `#d7f4ff` is cad-mvp, not factory-sourced)
- Modo GL Background gray-gradient stop hex, and the base Background hex
- Modo factory active-button / active-tab orange hex (unused under lock B; still unpublished)
- Whether the `modo` viewport gradient keeps the quoted teal radial or switches to Modo-style gray × background
- Exact placement of the info icon, About, and the theme switcher
- The app version string
- Any new control ids
- Any new CSS selectors
- Any new pixel sizes
- Any invented hex
- Icon art
- Hotkeys

Resolved, and therefore not TBD: active chrome is **B** (muted-teal active; orange for selection only). Chief, 2026-10-26 ~10:36 PM MT.

## Out of scope
- Gestures + float/dock brief #199 (merge `d167e21` / tip `be0d5f3`). Already on main. Do not re-spec it.
- X-ray select-through (#195 brief / #197 impl). Already on main. Do not re-spec it.
- Panel labels + always-visible chrome (#191 brief / #193 impl). Already on main. Do not re-spec them.
- `prompts/modo-restyle.md`. Prior direction the digest cites. This slice is the two named themes, not that restyle.
- Editing `research/modo-theme-gui-tokens.md`, `mvp/`, or `UPDATES.md` from this brief or from the theme `agy`.
- Kernel / C++ / wasm rebuild. Do not commit `.wasm`, `web/cadcam.wasm`, or `web/dist/`. Do not edit a root `PROGRESS.md`.

## Smoke
Manual wake smoke on Pages. No new smoke harness. Reuse `tests/deploy_smoke.py` only if that reuse is clearly required; this brief does not require it. No invented pixel asserts. Because no smoke path is added here, do not print a done marker.

Check sourced behavior only. Do not assert placement, control ids, CSS selectors, pixel sizes, icon art, hotkeys, a guessed app version, or any TBD hex.

1. The user can switch a theme named `default` and a theme named `modo`.
2. `default` matches the freeze snapshot (quoted `:root` values, including `--sel-color` `#ff4fd8` and `--active-fill` `#5b3cc4`, and the quoted viewport gradient).
3. `modo` selection is the high-contrast orange role, and orange is selection only (lock B). Do not assert a hex. An invented selection hex fails. If the factory hex is still TBD, record that gap and do not paint a stand-in.
4. `modo` still shows a viewport background gradient. Do not assert gray stops versus the quoted teal radial.
5. `modo` buttons are muted teal via existing `--accent` `#14756e`. `modo` active chrome (active tool / units / `.is-on`) is muted teal via that same `--accent`. Active chrome is not orange. Lock B.
6. Top-bar info opens About. About shows the app version and the theme switcher. Do not assert where they sit.

## Success Criteria
Must PASS at tip-match. Cite Erik via 3T, Chief, 2026-10-26 ~8:47 PM MT; `research/modo-theme-gui-tokens.md` at `f38aa66` (PR #200, merge `b0dd4df`; Doc Steward primary PASS on that tip); Chief lock B, 2026-10-26 ~10:36 PM MT; freeze snapshot of `web/index.html` on main `b0dd4df`. Only sourced behavior is on this bar.

1. The app exposes themes named exactly `default` and `modo`, switchable by the user. Reuse existing CSS variables where they already exist. Do not invent chrome beyond the stated themes and the info / About + switcher concept.
2. `modo` applies high-contrast orange selection, a viewport background gradient, and muted teal buttons (Erik likes). Muted teal buttons use existing `--accent` `#14756e`. Do not invent a Modo factory hex. The orange number is outside this bar (it stays TBD). A stand-in hex does not pass.
3. `modo` active chrome is **B**: muted-teal active, using existing `--accent` `#14756e` for the active tool / units / `.is-on` treatment. Orange is selection only.
4. Top-bar info opens About. About shows the app version and provides theme switching. Placement stays TBD when the app does not already place that control.
5. No invented TBD hex and no invented placement. Active chrome is B, so A versus B is not an open choice.

Outside this hard bar: Modo factory selection orange hex, Selection Fill hex, hover light-blue hex, GL Background gray-gradient stops, factory active-button orange hex, whether `modo` keeps the teal radial or switches to gray × background, the app version string, placement of info / About / the switcher, new control ids, new CSS selectors, new pixel sizes, icon art, hotkeys, gestures #199, X-ray #195/#197, panel labels #191/#193, `prompts/modo-restyle.md`, `research/modo-theme-gui-tokens.md`, `mvp/`, `UPDATES.md`, kernel / C++ / wasm.

## Done
Draft until tip-match: Doc Steward primary (COMMENT), Research Digest second. Author does not self-APPROVE. Repo Keeper undrafts and plain-merges. After this file is on main, Pilot runs one Antigravity-only `agy` from it. That `agy` also requires gestures brief #199 already on main (met: `d167e21`). Report the prompt PR link and tip SHA. Pilot reports any implementation PR separately.
