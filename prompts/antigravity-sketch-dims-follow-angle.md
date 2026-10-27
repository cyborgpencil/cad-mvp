# Antigravity sketch dims follow the angle they represent

Sketch dimension badges follow the angle they represent. On tip `529df18` they stay screen-upright. This file is the Antigravity feed. It does not change the app by itself.

**Gate:** [#208](https://github.com/cyborgpencil/cad-mvp/pull/208) overnight items 1–2 are on main @ `c713ce4`. Pilot holds this item-3 `agy` until **this** brief tip-matches on main. This prompts file does not start an `agy` by itself. Base for this brief is main after #208 @ `c713ce4` (branched from `529df18` / #207). Do not re-spec #208. Do not re-spec the older overnight queue (1) file `prompts/antigravity-sketch-dims.md`. Do not re-spec `prompts/antigravity-sketch-draw-overhaul.md`.

**Hard lock:** Implementation is **Antigravity-only on Z13**. Pilot holds one `agy` until this file tip-matches on main, then owns one `agy`. Do not use Grok Build or Cursor for the handoff into code. Prefer a worktree under `C:\Dev\`; do not invent a new path or create folders from this brief. Do not commit from Antigravity; Pilot/Repo Keeper commit path owns that. Do not invent Erik specs. Stay in `web/` (JS, HTML, CSS). No kernel, C++, `src/`, bindings, or wasm rebuild.

**Source of truth:**

- Erik overnight ~11:55 PM MT 2026-10-26, item **(3) sketch dims follow the angle they represent**, via Chief (room / journal). Team decides. Invent-free.
- `research/overnight-sketch-dims-follow-angle.md` (this docs change; Dig-style tip scan, 2026-10-27 ~1:10 AM MT). Cite that digest. Anything it marks **TBD** stays **TBD**.
- Tip `529df18` `web/index.html`. Quote only the facts below. Do not edit `web/` from this docs PR.
- Sketch draw overhaul park in `mvp/requirements.md` and `prompts/antigravity-sketch-draw-overhaul.md` (brief #185, implementation #189 on main). Live length and angle from the previous segment / last vertex; dims stay while drawing. That overhaul does **not** state badge rotation or parallel-to-edge orientation.
- The digest names `research/sketch-draw-ux-fusion-freecad.md` (Dig, 2026-10-26). That path is **not** in the tree at tip `529df18`. The digest’s claim stands as written: those fetched pages do not document a “rotate dim chip to match segment angle” rule. Do not bake a vendor matrix Dig did not source. Do not go fetch Fusion / FreeCAD / Onshape pages to fill this gap.

Quoted from `web/index.html` at `529df18` (transforms only; no `rotate`):

```css
.line-dim { transform: translate(-50%, -50%); }
.line-dim.angle-dim { transform: translate(-50%, 65%); }
.line-dim.start-callout { transform: translate(-50%, -140%); }
```

Start-callout comment on that tip: “Empty TBD label; keep chip box via existing .line-dim padding.”

`paintLineDimensions()` places badges with `screenOfCad(item.pos)`, then `badge.style.left` and `badge.style.top` only. It sets `data-deg` from `item.deg`. It does **not** set a CSS `rotate` from `seg.angleDeg` or from screen slope. Length items use the segment midpoint (`seg.mid`) and `formatLength(mm)`. Angle items use the segment start (`seg.a`) and `formatAngleDeg(angleDeg)`. The angle value comes from `segmentAngleFromPrevDeg(prev, a, b, frame)`. Badge orientation does not use that value. Badges stay screen-upright.

**Gap (do not invent the fix details):** length and angle chips are axis-aligned to the screen, not oriented along the segment / angle they represent.

## Goal
Implement these sourced behaviors in `web/` (JS, HTML, and CSS). No kernel, C++, `src/`, bindings, or wasm rebuild. Watertight / units are N/A.

Erik: sketch dims **follow the angle they represent**.

Coding bar (only what Erik stated, plus tip facts in the digest):

1. Sketch dimension badges that represent a segment length or an angle must be oriented so they **follow** that represented angle. They must not stay screen-upright only.
2. Reuse existing `#lineDimLayer` / `.line-dim` / `paintLineDimensions` / `lineSegmentsForDimensions` / `seg.angleDeg` (or the screen projection of the segment). Do not invent a second dim system.
3. Preserve overhaul locks already on main: live length and angle from the previous segment / last vertex; dims stay while drawing; the start-callout stays intentional with its visual **TBD**; the very top (tree + filename) and the very bottom (Modify / Create) stay on.

Default invent-free read, not a narrower lock: both kinds that already exist in `paintLineDimensions` (length and angle), excluding the empty start-callout. Whether Dig or Chief need a narrower lock (length only, or angle only) stays **TBD**.

Where a line is **TBD**, leave it TBD. Do not fill flip, offset, control ids, screen-space versus sketch-plane, or the implementation path.

## Workflow
1. Read `research/overnight-sketch-dims-follow-angle.md` and the quotes above. Copy behavior from Erik’s item (3) and those tip facts only.
2. Reuse `#lineDimLayer`, `.line-dim`, `paintLineDimensions`, `lineSegmentsForDimensions`, and `seg.angleDeg` or the screen projection of the segment. Do not add a second dimension layer.
3. Orient badges that represent a segment length or an angle so they follow that represented angle. Screen-upright-only placement is the gap this slice closes.
4. Keep the overhaul locks already on main: live length and angle from the previous segment / last vertex; dimensions stay while drawing; start-callout intentional with visual TBD; top and bottom stay on.
5. Leave the empty start-callout out of the default read. Do not invent its label. Its visual stays **TBD**.
6. Where this file marks a detail **TBD**, leave it TBD. Do not choose a flip rule, an offset, a control id, screen-space versus sketch-plane, or `data-deg` versus CSS `rotate()` versus SVG text. If one of those gaps blocks a concrete formula, record the gap in the implementation PR. Do not guess a stand-in.

## Do not bake / TBD
Do not invent and do not bake any of the following. They stay **TBD**:

- Whether **length** chips, **angle** chips, or **both** must rotate (Erik said “dims” plural — which kinds are in scope is **TBD** if Dig/Chief need a narrower lock; default invent-free read is both kinds that already exist in `paintLineDimensions`, excluding empty start-callout)
- Screen-space rotation vs sketch-plane rotation
- Flip / keep-readable when the segment would put text upside-down
- Offset distance from the segment / vertex (pixels or mm)
- Whether `data-deg` / CSS `rotate()` / SVG text is the implementation path
- Phone vs desktop differences
- Interaction with `#calloutLayer` / Dimension tool focus (older `prompts/antigravity-sketch-dims.md`) beyond orientation
- Vendor Fusion/FreeCAD “parallel dim” matrices Dig did not source for this overnight item
- Any new control ids
- Any new hex
- Any new pixel sizes
- Icon art
- Hotkeys
- Gesture maps
- Themes or Active chrome B
- Panel taxonomy
- New dimension values

## Out of scope
- Overnight items 1–2 (#208 Tool Search exit / hide prior tool UI) — already on main @ `c713ce4`. Do not re-spec them.
- Older overnight queue (1): `prompts/antigravity-sketch-dims.md` (typed mm, callouts, Dimension focus). Do not re-spec it. Interaction with `#calloutLayer` beyond orientation stays **TBD**.
- Sketch draw interaction overhaul (`prompts/antigravity-sketch-draw-overhaul.md`, #185 / #189). Preserve its locks. Do not re-spec it. It does not state badge rotation.
- `prompts/antigravity-view-cube-gizmo-line-dims.md` (#179 / #181). Do not re-spec it. It does not state dim-badge rotation.
- Themes / Active chrome B (`prompts/antigravity-theme-default-modo.md`, #206 @ `e805614`).
- Gesture maps (`prompts/antigravity-ipad-kiwi-gestures-float-dock.md`).
- Constraint solver / PlaneGCS / Trim / Offset.
- Editing `web/` from this docs PR. The later `agy` is `web/` only.
- Editing `research/overnight-sketch-dims-follow-angle.md`, `mvp/requirements.md`, or `UPDATES.md` from the coding `agy`.
- Kernel / C++ / wasm rebuild. Do not commit `.wasm`, `web/cadcam.wasm`, or `web/dist/`. Do not edit a root `PROGRESS.md`.

## Smoke
Manual wake smoke on Pages. No new smoke harness. Reuse `tests/deploy_smoke.py` only if that reuse is clearly required; this brief does not require it. No invented pixel asserts. Because no smoke path is added here, do not print a done marker.

Check sourced behavior only. Do not assert flip, offset distance, screen-space versus sketch-plane, `data-deg` versus CSS `rotate()` versus SVG text, phone versus desktop, a `#calloutLayer` change, a new control id, a hex, or a vendor parallel-dim matrix.

1. A sketch dimension badge that represents a segment length or an angle follows that represented angle. It is not left screen-upright only. Default read: both kinds `paintLineDimensions` already paints, excluding the empty start-callout. A narrower length-only or angle-only lock is still **TBD**; do not treat a guess as the lock.
2. The empty start-callout stays intentional. Its visual stays **TBD**. Do not invent a label.
3. Live length and angle still come from the previous segment / last vertex. Dimensions still stay while drawing.
4. While sketching, the very top (tree + filename) and the very bottom (Modify / Create) stay visible.
5. There is still one dim path: `#lineDimLayer` / `.line-dim` / `paintLineDimensions`. No second dim system.

## Success Criteria
Must PASS at tip-match. Cite Erik overnight item (3) ~11:55 PM MT 2026-10-26 via Chief; `research/overnight-sketch-dims-follow-angle.md`; tip `529df18` `paintLineDimensions` / `.line-dim` facts above. Only that bar is in scope.

1. Cite those sources. Do not cite a vendor matrix Dig did not source.
2. Dim badges that represent length or angle follow the angle they represent (oriented with that geometry). They do not stay screen-upright only. Default invent-free read: both kinds already in `paintLineDimensions`, excluding the empty start-callout. A narrower lock stays **TBD**.
3. Reuse `#lineDimLayer` / `.line-dim` / `paintLineDimensions` / `lineSegmentsForDimensions` / `seg.angleDeg` (or the screen projection of the segment). No second dim system.
4. Overhaul locks already on main still hold: live length/angle from the previous segment / last vertex; dims stay while drawing; start-callout intentional with visual TBD; top and bottom stay on.
5. No invented flip rule, offset, control ids, hex, or vendor bake.
6. This docs PR does not change `web/`.

Outside this hard bar: which of length, angle, or both rotate if a narrower lock is required; screen-space rotation vs sketch-plane rotation; flip / keep-readable; offset distance (pixels or mm); `data-deg` / CSS `rotate()` / SVG text; phone vs desktop; `#calloutLayer` / Dimension tool focus beyond orientation; vendor Fusion/FreeCAD parallel-dim matrices; new control ids; new hex; new pixel sizes; icon art; hotkeys; gesture maps; themes / Active chrome B; panel taxonomy; new dimension values; overnight items 1–2 (#208); `prompts/antigravity-sketch-dims.md`; the sketch draw overhaul brief; `prompts/antigravity-view-cube-gizmo-line-dims.md`; `UPDATES.md`; kernel / C++ / wasm.

## Done
Draft until tip-match: Doc Steward primary (COMMENT), Research Digest second. Author does not self-APPROVE. Repo Keeper undrafts and plain-merges. Pilot holds the coding `agy` for this item until this brief tip-matches (#208 already on main @ `c713ce4`). One Antigravity-only `agy` on Z13, `web/` only. Report the prompt PR link and tip SHA. Pilot reports any implementation PR separately.
