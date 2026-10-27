# Antigravity item 6 → **6-D**: view-cube double-tap = Home iso

View-cube **double-tap** is **Home iso** (recenter + iso spherical angles via `goView('home')` and `toast('View: Home')`, matching current tip behavior). Chief final lock (**6-D**, 2026-10-27 ~11:15 AM MT via 3T · Chief) **supersedes** the overnight ~1:17 AM MT stretch lock as a live must. Stretch iso↔non-iso is a **true gap** until Erik or Chief names the mechanism (FOV, dolly, ortho↔perspective, or aim — none chosen). Triple-tap remains on **HOLD**. This file is the Antigravity feed and tip-verification record.

**Gate:** Base tip `de0d89d` (`de0d89db83852944a61a6d728367747faa915a58`, main after [#233](https://github.com/cyborgpencil/cad-mvp/pull/233); prior brief gate `62c2feb` after [#232](https://github.com/cyborgpencil/cad-mvp/pull/232), Dig scan `c713ce4`). Triple-tap **HOLD**. Rust #4 **HOLD**. Items 7 and 10 out of scope. No web theme apply.

**Hard lock:** Invent-free. **Verify-only preferred** when tip already matches **6-D**. No stretch meaning, no second gesture channel, no new hotkey or control id, no timing other than tip `CUBE_DOUBLE_MS` (`320` ms). Stay out of kernel, C++, `src/`, bindings, and wasm rebuild. Watertight / units are **N/A** (camera chrome only).

---

## Source of truth (cite)

1. **Chief final lock (6-D):** 3T · Chief final 2026-10-27 ~11:15 AM MT (`/workspace/research/chief-lock-items-6-7-10-2026-10-27.md`, gather `erik-noreply-gather-items-6-7-10.md`). View-cube double-tap = **Home iso** (**6-D**). The earlier overnight Chief lock (2026-10-27 ~1:17 AM MT in `research/overnight-view-cube-double-tap-iso.md`) is **superseded** and struck as a live must.
2. **Dig cite pack (Doc second PASS):** `/workspace/research/cite-pack-item6-6D-2026-10-27.md` and brief `/workspace/research/antigravity-item6-6D-home-iso-brief-2026-10-27.md` (`item6-6d-brief.md` / `item6-6d-cite-pack.md`).
3. **Prior briefs aligned with 6-D:**
   - `prompts/antigravity-view-cube.md`: adjacent-face swipe only; success cite preserves “Face tap … still snaps; **double-tap Home iso**.”
   - `prompts/antigravity-ipad-kiwi-gestures-float-dock.md`: viewport (non-cube) double-tap → `goView('fit')`; view-cube double-tap Home is unchanged.
4. **Tip facts (scanned at `c713ce4`, re-verified unchanged at `de0d89d` in `web/index.html`):**
   - Cube DOM: `<div id="viewCube" class="view-cube" aria-hidden="true"></div>` (`web/index.html:2198`).
   - Detector constants/state: `const CUBE_DOUBLE_MS = 320;` (`web/index.html:2697`) and `let cubeTapMs = 0;` (`web/index.html:3180`).
   - Pointer release on cube (`onPointerDone`, `web/index.html:15544-15586`):
     - Committed adjacent swipe or hold clears `cubeTapMs = 0` (`web/index.html:15565`).
     - With no swipe, no hold, `ev.type !== 'pointercancel'`, and `!pastSlop` (`web/index.html:15568-15574`): if `cubeTapMs > 0 && (now - cubeTapMs) <= CUBE_DOUBLE_MS`, sets `cubeTapMs = 0; goView('home'); toast('View: Home');` else records `cubeTapMs = now` and runs single-tap `pickViewCube` + `snapToDirection` (`web/index.html:15578-15583`).
   - `VIEWS.home` and `VIEWS.iso` share `theta: Math.PI / 4`, `phi: 0.96` (`web/index.html:2681-2682`). `goView('home')` (`web/index.html:9138-9155`) recenters and fits distance via `homeTargetAndRadius()` and `animateSpherical(view.theta, view.phi, fitDistance(aim.radius), aim.center)` with hint `'Home view'`.
   - Main camera is `THREE.PerspectiveCamera(40, …)` (`web/index.html:3000`). No tip path toggles a perspective stretch or ortho “non-iso” on cube double-tap.
   - `web/view-cube.mjs` contains adjacent-swipe helpers only.
   - `#viewLabel` / `viewCaption()` displays a dominant face name or `'Iso'` (`web/index.html:15199`).

---

## Sourced CAD patterns (lean first)

| App | Pattern used for **6-D** | Not used | Source |
| --- | --- | --- | --- |
| **Shapr3D** (lean) | Orientation Cube **double-click / double-tap → reset to default view** (help + video: default isometric). Closest match to Home iso. | Appearance ortho/perspective (not cube double-tap) | [Orientation Cube](https://support.shapr3d.com/hc/en-us/articles/7873937480604-Orientation-Cube); [Gestures](https://support.shapr3d.com/hc/en-us/articles/7873906073884-Keyboard-shortcuts-gestures-and-hotkeys); [Control the view](https://support.shapr3d.com/hc/en-us/articles/13079128172956-Control-the-view-of-your-modeling-environment) |
| **Foundry Modo** (chrome lean / Kiwi stand-in) | **No ViewCube.** Fixed views + pie menu; **A** = fit. Chrome lean only — do **not** invent a Modo cube gesture. | N/A | [3D Viewport](https://learn.foundry.com/modo/current/content/help/pages/modo_interface/3d_viewport.html); `research/ipad-cad-kiwi-modo-gestures-panels.md` |
| **Kiwi!3D** | Rhino/Grasshopper IGA plug-in — **no** public view-cube docs. True gap for cube gestures. | — | [Kiwi!3D](https://www.kiwi3d.com/) |
| **Onshape** (lean check) | View cube face/corner; Isometric/Dimetric/Trimetric + Perspective in **menu**. Mobile double-tap = clear selection, **not** Home. | Do not retarget cube double-tap to perspective toggle | [View Navigation and the View Cube](https://cad.onshape.com/help/Content/View/view_navigation_and_the_view_cube.htm); [Isometric/Dimetric/Trimetric](https://cad.onshape.com/help/Content/View/isometric_dimetric_trimetric_projections.htm) |
| **Fusion 360** (check) | ViewCube face→ortho / corner→iso; **Home icon** separate; Camera projection in RMB menu | Do not invent Home-icon remapping | [ViewCube reference](https://help.autodesk.com/cloudhelp/ENU/Fusion-GetStarted/files/GS-VIEWCUBE.htm) |
| **SolidWorks** (check) | View Selector cube; Ctrl+7 Isometric — named orientation, not double-tap stretch | — | [View Selector](https://help.solidworks.com/2014/English/SolidWorks/sldworks/c_view_selector.htm) |

---

## Goal

Lock item 6 to **6-D**: view-cube **double-tap** = **Home iso** (`goView('home')` + `toast('View: Home')`, recenter + iso angles as on tip today). Strike the overnight stretch lock (~1:17 AM MT) as a live must; **stretch iso↔non-iso** is a **true gap** until Erik or Chief names FOV, dolly, ortho↔perspective, or aim (none chosen).

## Coding bar — **verify-only preferred**

1. Re-verify on current tip (`de0d89d`) that view-cube double-tap still runs `goView('home')` + `toast('View: Home')` via the existing `CUBE_DOUBLE_MS` / `cubeTapMs` detector in `web/index.html` (no alternate detector invent).
2. Because tip already matches **6-D** (`web/index.html:15570-15574`), make **no code change** in `web/` — prompt/docs update only.
3. If tip ever drifts away from `goView('home')` + `toast('View: Home')`, restore that tip-known behavior only (no stretch invent, no second gesture channel, no timing change beyond `CUBE_DOUBLE_MS`).
4. Do **not** implement stretch, FOV, dolly, ortho↔perspective toggle, or triple-tap.
5. Adjacent-face swipe (`web/index.html:15548-15562`) and viewport (non-cube) double-tap fit (`goView('fit')`, `web/index.html:15677-15698`) **stay as-is** (out of scope).

## MUST NOT

- Invent a stretch meaning or a second gesture channel for stretch.
- Invent control ids, hotkeys, pixel slop, timings other than tip `CUBE_DOUBLE_MS` (`320` ms), or triple-tap behavior.
- Create a versioned copy of this prompt.
- Touch items 7 or 10, theme hex / web theme apply, Rust #4, `UPDATES.md`, kernel / C++ / `src/` / wasm.

## True gap / HOLD (do not bake)

- **Stretch iso↔non-iso:** **True gap.** No listed CAD reference documents view-cube double-tap as stretch. No stretch work until Erik/Chief names FOV, dolly, ortho↔perspective, or aim.
- **Triple-tap:** Standing **HOLD** (out of scope).
- **Rust #4:** Standing **HOLD** (out of scope).

## Out of scope

- Adjacent-face swipe remapping (stays as locked in `prompts/antigravity-view-cube.md`).
- Viewport (non-cube) double-tap fit (`goView('fit')`, `prompts/antigravity-ipad-kiwi-gestures-float-dock.md`).
- Item 5 (`#vcHome` / top-view control placement), items 7 and 10, theme web apply, Rust #4, triple-tap.
- `UPDATES.md` (Repo Keeper cascade).
- Kernel, C++, `src/`, bindings, or `.wasm` rebuild.

## Smoke

Check sourced behavior only (no invented pixel or angle asserts):

1. Double-tap `#viewCube` within `CUBE_DOUBLE_MS` (`320` ms) → `goView('home')` (Home iso recenter + `VIEWS.home` angles) and `toast('View: Home')`.
2. Single face/zone tap on `#viewCube` still snaps via `pickViewCube` + `snapToDirection`.
3. Adjacent-face swipe on `#viewCube` still snaps to the adjacent face and clears `cubeTapMs`.
4. Viewport (non-cube) double-tap still runs `goView('fit')`.

## Success Criteria

Must PASS at tip-match. Cite 3T · Chief final **6-D** lock (2026-10-27 ~11:15 AM MT); Dig cite pack (`cite-pack-item6-6D-2026-10-27.md`, Doc second PASS); Shapr3D Orientation Cube default-view double-tap cite; tip scan `c713ce4` re-verified at `de0d89d`.

1. Prompt states **6-D**: view-cube double-tap = **Home iso** (`goView('home')` + `toast('View: Home')`).
2. Overnight stretch lock (~1:17 AM MT) is marked superseded; stretch iso↔non-iso is recorded as a **true gap** until Erik/Chief names FOV / dolly / ortho↔persp / aim.
3. Shapr3D Orientation Cube cite for double-tap reset to default view is preserved alongside the CAD check table.
4. Triple-tap remains **HOLD**; adjacent-face swipe and viewport double-tap fit remain as-is out of scope.
5. Tip `web/index.html` is verified to match **6-D** with **no `web/` code changes**.

## Done

Verified on `de0d89d`: `web/index.html` already matches **6-D** (`CUBE_DOUBLE_MS` / `cubeTapMs` → `goView('home')` + `toast('View: Home')`). Prompt updated in place on `feat/antigravity-item6-6d-home-iso`. Dig primary tip-match, Doc Steward second, Repo Keeper merge.
