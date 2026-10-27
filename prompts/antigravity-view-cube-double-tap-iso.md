# Antigravity view-cube double-tap iso↔non-iso

View-cube double-tap is a stretch that toggles iso and non-iso. Chief locked Erik’s overnight line over the older double-tap Home cite. Home leaves the cube (item 5). What “stretch” means and what “non-iso” means stay TBD. This file is the Antigravity feed. It does not change the app by itself.

**Gate:** This item’s **code** starts only after this file tip-matches on main **and** overnight item 1 Tool Search exit plus related tip-matches have landed. Overnight 1–2 briefs are on main ([#208](https://github.com/cyborgpencil/cad-mvp/pull/208) @ `c713ce4`). Item 3 brief is on main ([#210](https://github.com/cyborgpencil/cad-mvp/pull/210) @ `1b8a57f`; UPDATES [#211](https://github.com/cyborgpencil/cad-mvp/pull/211)). Pilot holds the coding `agy`. This prompts file does not start an `agy` by itself. Docs base is main @ `7214005` (`72140052f516b59d6560133fc4240f13e5d257c7`, tip after #211). Dig’s scan tip for `web/` remains `c713ce4` (`c713ce4479349fe11d56a53921edb7dafe866038`). #209/#210/#211 are docs/UPDATES only relative to that Dig scan for View/chrome facts. Do not re-spec #208. Do not re-spec item 3. Do not re-spec themes / Active chrome B.

**Hard lock:** Implementation is **Antigravity-only on Z13**. Pilot holds one `agy` until this file tip-matches on main and the item-1 hold above has lifted, then owns one `agy`. Do not use Grok Build or Cursor for the handoff into code. Prefer a worktree under `C:\Dev\`; do not invent a new path or create folders from this brief. Do not commit from Antigravity; Pilot/Repo Keeper commit path owns that. Do not invent Erik specs. Stay in `web/` (JS, HTML, CSS). No kernel, C++, `src/`, bindings, or wasm rebuild. No new control ids, hex, pixel sizes, gesture maps, themes, Active chrome B changes, or invented relocation homes. Do not invent stretch timing, stretch pixels, or a stretch mechanism.

**Source of truth:**

- Erik overnight ~11:55 PM MT 2026-10-26, item **(6) View-cube double-tap stretch iso↔non-iso**, via CAD Chief. Invent-free.
- Chief lock, 2026-10-27 ~1:17 AM MT via 3T · Chief: **Erik wins.** View-cube double-tap = iso↔non-iso stretch. Home leaves the cube and moves to the top-view control (item 5, `prompts/antigravity-home-onto-top-view-control.md`). Drop the cube’s current Home double-tap binding. No invent on stretch timing or pixel sizes. Stretch meaning and non-iso meaning stay **TBD** where Dig left them.
- `research/overnight-view-cube-double-tap-iso.md` (Dig, 2026-10-27 ~1:15 AM MT), scanned at tip `c713ce4`. Cite that digest. Anything it still marks **TBD** stays **TBD**.
- Overnight lock (c) / `prompts/antigravity-view-cube.md`: adjacent-face swipe only. Its success cite “double-tap Home iso” is superseded **for this cube gesture only**. Do not re-spec adjacent swipe.
- iPad / Kiwi brief (`prompts/antigravity-ipad-kiwi-gestures-float-dock.md`): viewport double-tap → `goView('fit')`. Its line that view-cube double-tap Home is unchanged is superseded **for this cube gesture only**. Do not retarget viewport double-tap fit. Do not re-spec the rest of that brief.
- Triple-tap stays **TBD** and out of this item.

Quoted from Dig’s scan at `c713ce4`:

- Cube: `<div id="viewCube" class="view-cube" aria-hidden="true"></div>`.
- `const CUBE_DOUBLE_MS = 320` and `cubeTapMs`. On pointer release with no swipe, no hold, and within slop: if `(now - cubeTapMs) <= CUBE_DOUBLE_MS` then `goView('home'); toast('View: Home');` else single-tap `pickViewCube`.
- A committed swipe or hold clears `cubeTapMs`.
- `VIEWS.home` and `VIEWS.iso` share `theta: Math.PI/4`, `phi: 0.96`. `goView('home')` also recenters via `homeTargetAndRadius()`.
- Camera is `THREE.PerspectiveCamera(40, …)`. No tip path toggles a perspective stretch or an ortho “non-iso” on cube double-tap.
- `view-cube.mjs` has adjacent swipe helpers only. No double-tap or iso-stretch logic there.
- `#viewLabel` / `viewCaption()` shows a dominant face name or `'Iso'`. That caption is not a stretch toggle.

**Gap:** Cube double-tap runs Home. It does not stretch iso↔non-iso. No tip function defines that stretch.

## Goal
Implement these sourced behaviors in `web/` (JS, HTML, and CSS). The double-tap Dig scanned is the cube pointer path in `web/index.html`. `web/view-cube.mjs` has adjacent-swipe helpers only. Do not add double-tap or stretch logic to that module. No kernel, C++, `src/`, bindings, or wasm rebuild. Watertight / units are N/A.

Erik + Chief: view-cube **double-tap** is **stretch iso↔non-iso**. It is not Home.

Coding bar:

1. The cube double-tap binding to `goView('home')` / `toast('View: Home')` is dropped. That is the Chief lock. Home’s button moves in item 5. Do not move `#vcHome` here.
2. The same gesture is the iso↔non-iso stretch once “stretch” and “non-iso” are defined. They are **not** defined. Do not ship a stand-in (FOV, dolly, ortho↔perspective, `animateSpherical` only, last face, nearest face, Front, or `#viewLabel`).
3. Reuse the existing detector. Do not add a second gesture channel. Do not change `CUBE_DOUBLE_MS`, the slop, or any pixel threshold. Do not invent a stretch duration.
4. Adjacent swipe stays. Viewport (non-cube) double-tap fit stays. Triple-tap stays out.
5. If stretch and non-iso are still TBD at coding time, record the gap and do not edit the double-tap branch into a guessed effect. Dropping Home without a sourced stretch is not a pass. Leaving the Home binding in place is also not a pass once the meanings exist. Until those meanings exist, do not pretend either half is finished by a stand-in.

Where stretch or non-iso is **TBD**, leave it **TBD**.

## Workflow
1. Read `research/overnight-view-cube-double-tap-iso.md`, the Chief lock, and the tip facts above. Copy behavior from those sources only.
2. Treat the prior “double-tap Home iso” success cite as superseded for cube double-tap only.
3. Do not define stretch. Do not define non-iso. Do not pick a camera mode.
4. Do not change double-tap timing or pixel slop.
5. Do not add triple-tap. Do not retarget viewport double-tap fit. Do not remap adjacent swipe.
6. Do not move Home. Item 5 owns placement, and its destination node is still TBD.

## Do not bake / TBD
Do not invent and do not bake any of the following. They stay **TBD**:

- What “stretch” means
- What “non-iso” means
- Phone vs desktop differences for this gesture
- Triple-tap
- Any new timing or pixel size, including a stretch duration and any change to `CUBE_DOUBLE_MS` or slop
- Any new control id
- Any new hex
- Icon art
- Hotkeys
- A new gesture map
- Themes or Active chrome B
- A destination node for Home (item 5)

Resolved, and therefore not TBD: cube double-tap is not Home. Home leaves the cube (placement is item 5). Chief, 2026-10-27 ~1:17 AM MT via 3T · Chief.

## Out of scope
- Item 5 destination choice and `#vcHome` placement. Separate brief.
- Adjacent swipe remapping.
- Viewport double-tap fit (`goView('fit')`).
- Items 4, 7–9. Item 10 rebuild note (no coding brief).
- Overnight 1–2 (#208) and item 3. Do not re-spec them.
- Rust #4 / Modo orange selection hex / triple-tap.
- Editing `research/overnight-view-cube-double-tap-iso.md`, `mvp/requirements.md`, or `UPDATES.md` from the coding `agy`.
- Editing `web/` from this docs PR.
- Kernel / C++ / wasm rebuild. Do not commit `.wasm`, `web/cadcam.wasm`, or `web/dist/`. Do not edit a root `PROGRESS.md`.

## Smoke
Manual wake smoke on Pages. No new smoke harness. Reuse `tests/deploy_smoke.py` or `tests/view_cube_swipe_smoke.py` only if that reuse is clearly required; this brief does not require a new assert. No invented pixel asserts. Because no smoke path is added here, do not print a done marker.

Check sourced behavior only. Do not assert FOV, ortho, dolly, a face name, a millisecond value other than the existing detector, or a pixel slop.

1. Cube double-tap is not a Home action (`goView('home')` / “View: Home”) once a sourced stretch exists. A Home double-tap does not pass.
2. A stand-in stretch does not pass while stretch and non-iso are TBD. Record the gap instead of shipping one.
3. `CUBE_DOUBLE_MS` and the existing slop are unchanged.
4. Adjacent-face swipe still matches lock (c). Viewport double-tap still fits. There is no triple-tap.

## Success Criteria
Must PASS at tip-match. Cite Erik overnight item (6) ~11:55 PM MT 2026-10-26 via CAD Chief; Chief lock 2026-10-27 ~1:17 AM MT via 3T · Chief; `research/overnight-view-cube-double-tap-iso.md`; tip `c713ce4`. Only that bar is in scope.

1. The spec for view-cube double-tap is iso↔non-iso stretch, not Home. That supersedes the Home-iso cite for this gesture only.
2. The cube’s Home double-tap binding is not the spec. Drop it when a sourced stretch exists. Do not replace it with a stand-in while stretch and non-iso are still TBD. Placement of Home is item 5.
3. Stretch meaning and non-iso meaning stay TBD. A guessed mechanism fails. No stand-in ships from this brief while those words are undefined.
4. No invented stretch timing or pixel size. The existing 320 ms detector and slop are not a new spec and are not retuned.
5. No new gesture channel, no triple-tap, no theme or Active chrome B work, no kernel or wasm.
6. This docs PR does not change `web/`.

Outside this hard bar: the meaning of stretch; the meaning of non-iso; phone vs desktop; triple-tap; item 5’s destination node; adjacent swipe; viewport double-tap fit; items 1–4 and 7–10; `UPDATES.md`; kernel / C++ / wasm.

## Done
Draft until tip-match: Doc Steward primary (COMMENT), Research Digest second. Author does not self-APPROVE. Repo Keeper undrafts and plain-merges. Pilot holds the coding `agy` for this item until overnight item 1 Tool Search exit and related tip-matches have landed **and** this brief tip-matches on main. This file does not start an `agy`. One Antigravity-only `agy` on Z13, `web/` only, after that hold lifts. Report the prompt PR link and tip SHA. Pilot reports any implementation PR separately.
