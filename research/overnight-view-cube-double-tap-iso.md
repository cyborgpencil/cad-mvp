# View-cube double-tap stretch iso↔non-iso — invent-free digest (overnight item 6)

Status: invent-free digest. Compiled **2026-10-27 ~1:15 AM MT** (America/Denver). Chief lock added **2026-10-27 ~1:17 AM MT**.
Antigravity feed: `prompts/antigravity-view-cube-double-tap-iso.md`. This digest does not start an `agy`.

**Owner draft:** MVP Research Digest (tip-scan). Doc Steward primary tip for any `prompts/` PR.
**Date:** 2026-10-27 ~1:15 AM MT (America/Denver)
**Gate tip:** main @ `c713ce4` (`c713ce4479349fe11d56a53921edb7dafe866038`) — [#208](https://github.com/cyborgpencil/cad-mvp/pull/208) merged.
**Scope:** View-cube double-tap behavior. UI / camera chrome only. Watertight / units N/A.
**Hard lock:** Invent-free. No new control ids, hex, pixel sizes, gesture maps, themes, or Active chrome B changes. Do not invent stretch timing or a stretch mechanism.

---

## Source of truth (cite only these)

### Erik / team

| Source | Statement |
| --- | --- |
| Erik overnight ~11:55 PM MT 2026-10-26 via CAD Chief | Item **(6) View-cube double-tap stretch iso↔non-iso**. Invent-free. |
| Overnight lock (c) / `prompts/antigravity-view-cube.md` | Adjacent-face swipe only. Success cite includes “Face tap … still snaps; **double-tap Home iso**.” |
| iPad gestures brief (`prompts/antigravity-ipad-kiwi-gestures-float-dock.md`) | Viewport double-tap → `goView('fit')`. Explicitly: **View-cube double-tap Home is unchanged** / do not retarget view-cube double-tap Home. |
| Triple-tap | Stays **TBD** (Chief/Erik standing). Out of this item’s invent-free scope. |
| Chief lock, 2026-10-27 ~1:17 AM MT via 3T · Chief | **Erik wins.** View-cube double-tap = iso↔non-iso stretch. Home leaves the cube and moves to the top-view control (item 5). Drop the cube’s current Home double-tap binding. No invent on stretch timing or pixel sizes. What “stretch” means and what “non-iso” means stay **TBD** where this digest left them. |

### App behavior on tip `c713ce4`

| Fact | Quote / location |
| --- | --- |
| Cube element | `<div id="viewCube" class="view-cube" aria-hidden="true"></div>` |
| Double-tap window | `const CUBE_DOUBLE_MS = 320;` + `cubeTapMs` timestamp |
| Double-tap action | On cube pointer release (no swipe, no hold, within slop): if `(now - cubeTapMs) <= CUBE_DOUBLE_MS` → `goView('home'); toast('View: Home');` else single-tap `pickViewCube` snap |
| Swipe vs double-tap | Committed swipe or hold clears `cubeTapMs` so a follow-up tap does not go Home |
| `VIEWS.home` / `VIEWS.iso` | Same spherical angles (`theta: Math.PI/4`, `phi: 0.96`). `goView('home')` also recenters via `homeTargetAndRadius()`. |
| Main camera | `THREE.PerspectiveCamera(40, …)` — no tip code that toggles perspective stretch / ortho “non-iso” on cube double-tap |
| `view-cube.mjs` | Adjacent swipe helpers only; no double-tap / iso-stretch logic in that module |
| HUD caption | `#viewLabel` via `viewCaption()` returns a primary face name if dominant else `'Iso'` — display label, not a stretch toggle |

**Gap vs Erik wording:** Cube double-tap today always runs **Home** (`goView('home')`), not a **stretch toggle between iso and non-iso**. No tip function implements “stretch iso↔non-iso”.

**Prior-lock tension (Dig flagged; Chief resolved):** Existing briefs lock cube double-tap as **Home iso**. Erik’s overnight line asks for **stretch iso↔non-iso**. Dig did not pick a winner. Chief lock above picks Erik and drops the cube Home double-tap binding. That resolution does not define stretch or non-iso.

---

## Recommended invent-free goal (for `prompts/`)

Erik + Chief: view-cube **double-tap** is a **stretch** that toggles **iso ↔ non-iso**. It is not Home.

**Coding bar (only what Erik stated, what Chief locked, and tip facts):**

1. View-cube double-tap must perform a **stretch** transition that toggles **iso ↔ non-iso** (Erik’s words). Chief: Erik wins over the prior Home-iso double-tap cite for this gesture.
2. Drop the cube’s current Home double-tap binding (`goView('home')` / `toast('View: Home')` on that gesture). Home leaves the cube and is item 5’s placement ask. Do not move `#vcHome` in this item.
3. Do not invent a second gesture channel. The existing detector (`CUBE_DOUBLE_MS` / `cubeTapMs`, existing slop) is the tip fact. Do not change its timing or pixel slop. Do not invent a stretch duration.
4. Do not invent triple-tap. Keep it out of scope.
5. Do not ship a stand-in stretch. If “stretch” or “non-iso” is still TBD, record the gap. A guessed FOV, dolly, ortho toggle, or face choice fails.

**TBD (do not invent) — still open after the Chief lock:**

- What “stretch” means (FOV, dolly, ortho↔perspective, animateSpherical only, or anything else).
- What “non-iso” means (last ortho face, nearest face, Front, current `#viewLabel` face, or anything else).
- Phone vs desktop differences.

**Closed by Chief (do not reopen):**

- Cube double-tap is not Home iso. Drop that binding.
- Home placement is item 5 (top-view control). This gesture does not keep `homeTargetAndRadius()` as the double-tap action.
- Prior “double-tap Home iso” success cites and the iPad brief’s “view-cube double-tap Home is unchanged” line are superseded for **this cube gesture only**. Adjacent swipe and viewport (non-cube) double-tap fit stay as already locked.
- Stretch timing and pixel sizes: do not invent. Do not retune `CUBE_DOUBLE_MS` or the existing slop.

## Out of scope

- Adjacent swipe remapping (already shipped / locked).
- Viewport (non-cube) double-tap fit.
- Item 5’s choice of which node is the top-view control.
- Items 4, 7–10; Rust #4 / Modo orange / triple-tap.
- Kernel / C++ / wasm / UPDATES.md.
- Themes / Active chrome B.

## Done

Dig tip-scan committed for the docs brief, with the Chief lock baked. No coding `agy`. Pilot holds coding until overnight item 1 Tool Search exit and related tip-matches land, and until the brief tip-matches.
