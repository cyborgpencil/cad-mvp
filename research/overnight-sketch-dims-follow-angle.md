# Sketch dims follow the angle they represent — invent-free digest (overnight item 3)

Status: invent-free digest. Compiled **2026-10-27 ~1:10 AM MT** (America/Denver).
Antigravity feed: `prompts/antigravity-sketch-dims-follow-angle.md`. This digest does not start an `agy`.

**Owner draft:** MVP Doc Steward (Chief idle-fill while Dig seconds #208). Dig may second or amend invent-free.  
**Date:** 2026-10-27 ~1:10 AM MT (America/Denver)  
**Gate tip:** main @ `529df18` (#207 UPDATES; theme #206 @ `e805614`). Overnight 1–2 briefs still draft [#208](https://github.com/cyborgpencil/cad-mvp/pull/208) @ `389e33f` — Pilot starts item-1 agy first after #208 tip-matches; this item-3 brief does **not** start an agy ahead of 1–2.  
**Scope:** Sketch dimension / length / angle **badge orientation** so dims follow the angle of the geometry they represent. UI chrome only (`web/`). Watertight / units N/A.  
**Hard lock:** Invent-free. Do not invent gesture maps, themes, Active chrome B, panel taxonomy, or new dim values.

---

## Source of truth (cite only these)

### Erik / team

| Source | Statement |
| --- | --- |
| Erik overnight ~11:55 PM MT 2026-10-26 via Chief (room / journal) | After `#206`, overnight queue includes item **(3) sketch dims follow the angle they represent**. Team decides; invent-free. |
| Sketch draw overhaul park + `prompts/antigravity-sketch-draw-overhaul.md` | Live length and angle from previous segment / last vertex; dims stay while drawing. Does **not** state badge rotation / parallel-to-edge orientation. |
| `research/sketch-draw-ux-fusion-freecad.md` (Dig, 2026-10-26) | Fusion / FreeCAD / Onshape draw-time UX. **Does not** document a “rotate dim chip to match segment angle” rule on the fetched pages — pattern gap; do not bake a vendor matrix Dig did not source. |

### App behavior on tip `529df18` / `web/index.html` (invent-free tip scan)

| Fact | Quote / location |
| --- | --- |
| Layer | `#lineDimLayer.line-dim-layer` |
| Length chip CSS | `.line-dim { transform: translate(-50%, -50%); … }` — **no rotate** |
| Angle chip CSS | `.line-dim.angle-dim { transform: translate(-50%, 65%); … }` — **no rotate** |
| Start callout CSS | `.line-dim.start-callout { transform: translate(-50%, -140%); }` — empty TBD label |
| Placement | `paintLineDimensions()` sets `badge.style.left` / `badge.style.top` from `screenOfCad(item.pos)` only. Does **not** set a CSS `rotate` from `seg.angleDeg` / screen slope. |
| Length item | Midpoint of segment; `text: formatLength(mm)`; `deg` stored on `data-deg` but unused for orientation |
| Angle item | Positioned at segment start `seg.a`; `text: formatAngleDeg(angleDeg)` |
| Angle value | `segmentAngleFromPrevDeg(prev, a, b, frame)` — value exists; orientation of the badge does not use it |
| Screen-axis text | Badges stay screen-upright (CSS translate only) |

**Gap vs Erik wording (do not invent the fix details):** length and angle chips are axis-aligned to the screen, not oriented along the segment / angle they represent.

---

## Recommended invent-free goal (for `prompts/`)

Erik: sketch dims **follow the angle they represent**.

**Coding bar (only what Erik stated + tip facts):**

1. Sketch dimension badges that represent a segment length or an angle must be oriented so they **follow** that represented angle (not stay screen-upright only).
2. Reuse existing `#lineDimLayer` / `.line-dim` / `paintLineDimensions` / `lineSegmentsForDimensions` / `seg.angleDeg` (or the screen projection of the segment) — do not invent a second dim system.
3. Preserve overhaul locks already on main: live length/angle from previous segment / last vertex; dims stay while drawing; start-callout intentional with visual TBD; top/bottom stay on.

**TBD (do not invent):**

- Whether **length** chips, **angle** chips, or **both** must rotate (Erik said “dims” plural — which kinds are in scope is **TBD** if Dig/Chief need a narrower lock; default invent-free read is both kinds that already exist in `paintLineDimensions`, excluding empty start-callout).
- Screen-space rotation vs sketch-plane rotation.
- Flip / keep-readable when the segment would put text upside-down.
- Offset distance from the segment / vertex (pixels or mm).
- Whether `data-deg` / CSS `rotate()` / SVG text is the implementation path.
- Phone vs desktop differences.
- Interaction with `#calloutLayer` / Dimension tool focus (older `prompts/antigravity-sketch-dims.md`) beyond orientation.
- Vendor Fusion/FreeCAD “parallel dim” matrices Dig did not source for this overnight item.

---

## Out of scope

- Overnight items 1–2 (#208 Tool Search exit / hide prior tool UI) — do not re-spec; Pilot runs those first after tip-match.
- Themes / Active chrome B / gestures.
- Constraint solver / PlaneGCS / Trim / Offset.
- Kernel / C++ / wasm / UPDATES.md.

## Success criteria (tip-match bar)

1. Cite Erik overnight item (3) ~11:55 PM MT 2026-10-26; tip `529df18` `paintLineDimensions` / `.line-dim` facts above.
2. Dim badges that represent length or angle follow the angle they represent (oriented with that geometry), invent-free vs tip scan.
3. No invented flip rule, offset, control ids, hex, or vendor bake Dig did not source.
4. No `web/` change in the docs PR itself.

## Done

Draft until tip-match: Doc Steward primary (COMMENT), Research Digest second. Author does not self-APPROVE. Repo Keeper undrafts and plain-merges. Pilot holds coding `agy` for this item until overnight 1–2 are on main **and** this brief tip-matches; one Antigravity-only `agy` on Z13, `web/` only.
