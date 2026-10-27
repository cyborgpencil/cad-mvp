# Sketch clutter, verts, edit — invent-free digest (overnight item 7)

Status: invent-free digest. Compiled **2026-10-27 ~1:15 AM MT** (America/Denver).
Antigravity feed: `prompts/antigravity-sketch-clutter-verts-edit.md`. This digest does not start an `agy`.

**Owner draft:** MVP Research Digest (tip-scan). Doc Steward primary tip for any `prompts/` PR.
**Date:** 2026-10-27 ~1:15 AM MT (America/Denver)
**Gate tip:** main @ `c713ce4` (`c713ce4479349fe11d56a53921edb7dafe866038`) — [#208](https://github.com/cyborgpencil/cad-mvp/pull/208) merged.
**Scope:** Sketch UI / visibility / edit chrome in `web/`. Watertight / units N/A unless a solid export path is touched (do not invent that).
**Hard lock:** Invent-free. This Erik line bundles several asks — tip-scan each; do not invent a punch list. No new control ids, hex, pixel sizes, gesture maps, themes, or Active chrome B changes.

---

## Source of truth (cite only these)

### Erik / team

| Source | Statement |
| --- | --- |
| Erik overnight ~11:55 PM MT 2026-10-26 via CAD Chief | Item **(7) Sketch: less create clutter; brighter verts/edges all components; edit+delete; flesh sketches+solids**. Invent-free; do not expand beyond these clauses. |
| Park: Sketch chrome minimize + Create→ortho (`mvp/requirements.md`, `prompts/antigravity-sketch-chrome-flow.md`) | While sketch active, minimize non-sketch chrome; Create → six ortho planes → sketch-create tools; keep Finish Sketch. |
| Park: Sketch draw overhaul (`mvp/requirements.md`, `prompts/antigravity-sketch-draw-overhaul.md`) | Live length/angle; dims stay; top + **very bottom (Modify/Create) stay on**; #183 strip + Finish stay. |

### App behavior on tip `c713ce4` / `web/index.html`

| Fact | Quote / location |
| --- | --- |
| Sketch panel groups | `data-panel="sketch"`: **Draw** (Line, Rectangle, Circle, Arc, Polygon); **Modify** (Sketch Fillet, Trim, Offset, Dimension); **Constrain** (Coincident, Horizontal, Vertical, Parallel, Perpendicular, Equal, Tangent, Fixed). |
| Create clutter (partial tip mitigation) | `html[data-sketch-active] [data-panel="sketch"] .group:nth-child(n+3) { display: none !important; }` hides Constrain (3rd group) while sketch-active. Draw + Modify groups still present. |
| Other sketch-active hides | View `vp-bar`, `#selectionShelf`, `#cameraShelf`, `#cameraShelfBtn`, selection shelf group, `#edgeSheet`, `#pickChooser`, `.hud`, tools-sheet shelves — see CSS block ~1744+. |
| Finish | `#finishBar` / `data-action="finishSketch"` — Finish Sketch. |
| Sketch line color | `THREE.LineBasicMaterial({ color: 0xf0c14e })` on sketch `LineLoop` / profile line. |
| Corner / point material (boot cube corners) | `PointsMaterial({ color: 0xf2c14e, size: 8, sizeAttenuation: false })` — corners start `visible = false`. |
| Body edge overlay | `edgeMat = LineBasicMaterial({ color: 0x10283a })`; later theme paths set `0xd7e4f2` / `0x10283a`. |
| Delete control | `#modifyShelf` includes `data-action="delete"` **Delete** (body/modify shelf — not a sketch-geometry editor labeled Edit). |
| Side note TBD | Inspector About/side: “TBD. Vertex maps, the tool pipe, and statistics are not in this build.” |
| No tip “Edit sketch” button | Tip scan found Finish Sketch + modify Delete; no dedicated sketch **edit** mode control named Edit in the sketch panel groups above. |

**Gaps vs Erik wording (do not invent fixes):**

1. **less create clutter** — Constrain already hidden when sketch-active; Draw still exposes five create tools + Modify four. What else counts as “create clutter” is TBD.
2. **brighter verts/edges all components** — tip has fixed gold/dark edge colors; no tip pass that brightens verts/edges across **all components**. Target brightness / hex TBD (Modo orange sel hex stays TBD globally).
3. **edit+delete** — Delete exists on modify shelf; sketch-entity edit/delete workflow is not specified on tip beyond Finish / Trim / Offset / Fillet tools.
4. **flesh sketches+solids** — no tip-spec or park bullet that defines “flesh”; treat as Erik TBD content.

---

## Recommended invent-free goal (for `prompts/`)

Split clauses; only bake what Erik said. Do not turn the gaps into a punch list.

1. Reduce sketch **create clutter** (Erik) without inventing which Draw tools leave the strip.
2. Make verts/edges **brighter** for **all components** (Erik). Tip colors above are the baseline quote. Do not invent a hex or treat those literals as the new brightness target.
3. Provide **edit+delete** for sketch context (Erik). Do not invent control ids or whether this reuses `#modifyShelf` Delete.
4. **Flesh sketches+solids** — record as Erik’s ask. Implementation content is **TBD** until Erik/Chief narrows.

**TBD (do not invent):**

- Which create tools stay vs hide/move.
- Brightness metric / hex / shader path; per-component vs sketch-only.
- Edit means: re-enter sketch, drag verts, properties, or something else.
- Delete means: sketch entities, whole sketch, or bodies.
- What “flesh” adds to sketches and solids.
- Collision with Constrain-hide CSS and #183 / overhaul locks.
- Modo orange selection hex (out of scope TBD).

Where a clause is unspecified, leave it TBD. A stand-in tool list, hex, Edit control, or flesh feature fails.

## Out of scope

- Constraint solver / PlaneGCS.
- Items 1–6, 8–10; Rust #4 / triple-tap.
- Kernel / C++ / wasm / UPDATES.md.
- Themes / Active chrome B. Gesture maps. Item 8’s bottom-bar removal (separate brief). The overhaul “very bottom stays on” line is not retargeted here.

## Done

Dig tip-scan committed for the docs brief. No punch list. No coding `agy`. Pilot holds coding until overnight item 1 Tool Search exit and related tip-matches land, and until the brief tip-matches.
