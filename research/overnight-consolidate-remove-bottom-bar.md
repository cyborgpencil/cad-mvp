# Consolidate then remove the bottom bar — invent-free digest (overnight item 8)

Status: invent-free digest. Compiled **2026-10-27 ~1:15 AM MT** (America/Denver). Chief lock added **2026-10-27 ~1:17 AM MT**.
Antigravity feed: `prompts/antigravity-consolidate-remove-bottom-bar.md`. This digest does not start an `agy`.

**Owner draft:** MVP Research Digest (tip-scan). Doc Steward primary tip for any `prompts/` PR.
**Date:** 2026-10-27 ~1:15 AM MT (America/Denver)
**Gate tip:** main @ `c713ce4` (`c713ce4479349fe11d56a53921edb7dafe866038`) — [#208](https://github.com/cyborgpencil/cad-mvp/pull/208) merged.
**Scope:** Bottom chrome stack vs units status bar. UI only.
**Hard lock:** Invent-free. No new control ids, hex, pixel sizes, gesture maps, themes, or Active chrome B changes. Do not invent a new home for Create/Modify.

---

## Source of truth (cite only these)

### Erik / team

| Source | Statement |
| --- | --- |
| Erik overnight ~11:55 PM MT 2026-10-26 via CAD Chief | Item **(8) Consolidate then remove bottom bar; units bar = bottommost**. Invent-free. |
| Always-visible chrome park | Permanent panels: very top, tools menu bar, **very bottom (Modify / Create etc.)**. Everything else show/hide. Region mapping TBD. |
| Sketch draw overhaul park / prompt | While sketching, very top and **very bottom (Modify / Create) stay visible**. |
| Chief lock, 2026-10-27 ~1:17 AM MT via 3T · Chief | **Erik’s newer overnight wins** over the always-on bottom Create/Modify lock. Consolidate, then remove that bottom bar. The units bar is bottommost. Relocate Create/Modify only if an existing path already fits; otherwise the destination stays **TBD**. Do not invent a new home. |

### App behavior on tip `c713ce4`

| Fact | Quote / location |
| --- | --- |
| Units bar | `<footer class="statusbar" aria-label="Units">` with `Units <b id="statusUnits">mm</b>`, `#statusHint`, `#buildStamp`. |
| Status CSS | `.statusbar { … border-top: 1px solid …; flex: none; }` — document footer. |
| Desktop bottom Create/Modify | `<div class="desk-bottom" role="toolbar" aria-label="Create and modify">` — Create + Modify. Default CSS `.desk-bottom { display: none }`; `@media (min-width: 821px) { .desk-bottom { display: flex; … height: 52px; … } }`. |
| Phone bottom workbench | `<nav class="phone-tabbar" …>` — Pick, Multi, Undo, Redo, Create, Modify, Model/Repair/Export tabs. Shown in phone media rules (base `.phone-tabbar { display: none }` then phone breakpoints show it). |
| Modify shelf | `#modifyShelf.modify-shelf` — Move/Rotate/Resize/Fillet/Chamfer/Booleans/Delete; `hidden` until opened; sits above desk-bottom / phone chrome in the DOM stack. |
| Viewport bottom View bar | `.vp-bar[aria-label="View"]` absolute inside `#viewport` (not the document footer) — separate from units footer. |
| CSS always-visible comment | Names **bottom bar (Modify / Create etc.)** as permanent chrome. |

**DOM order (bottom of app shell, invent-free):** `#modifyShelf` → `.desk-bottom` → `.phone-tabbar` → … → `<footer class="statusbar" aria-label="Units">` is the document’s units footer (bottommost footer element in the scanned markup).

**Gap vs Erik wording:** Tip still has Create/Modify **bottom bar(s)** (desk-bottom and/or phone-tabbar) in addition to the units `footer.statusbar`. Erik wants: **consolidate**, then **remove** the bottom bar, and make the **units bar bottommost**.

**Prior-lock tension (Dig flagged; Chief resolved):** Always-visible chrome and the sketch draw overhaul say the very bottom (Modify / Create) stays on. Chief lock above: the newer overnight line wins for **that bottom bar**. Very top and the tools menu bar are not retargeted by this lock. Dig did not choose a new home for Create/Modify. Chief: relocate only if an existing path already fits; else TBD.

---

## Recommended invent-free goal (for `prompts/`)

1. **Consolidate** the bottom Create/Modify bar (Erik + Chief). Do not invent the merge target.
2. **Remove** that bottom bar after consolidate (Erik + Chief). This supersedes the always-on very-bottom Create/Modify rule, including while sketching, for that bar only.
3. **Units bar = bottommost** (Erik). Tip: `footer.statusbar[aria-label="Units"]` remains the bottommost chrome band. Do not invent a new status height.
4. **Create/Modify relocation:** only if an existing path already fits. Tip already has `data-action="createMenu"` and `#modifyShelf` / `data-action="modifyShelf"`. Those are facts, not a decision that they fit. If no existing path fits, the destination stays **TBD**. Do not add a bar, icon, or control id.

**TBD (do not invent) — still open after the Chief lock:**

- Which existing path fits Create/Modify, if any.
- Phone-tabbar fate (whole nav vs Create/Modify only). The rest of that nav (Pick, Multi, Undo, Redo, Model/Repair/Export) is not named by Erik’s line.
- Whether viewport `.vp-bar` is in scope (item 4 owns the View popup move). Erik said bottom bar + units bar.
- How consolidate is performed (which controls fold where) beyond “existing path or TBD”.
- Show-hide animation during consolidate.

## Out of scope

- Changing the units gate / RustGate / export mm lock.
- Items 4–7, 9–10; Modo hex / triple-tap / Rust #4.
- Kernel / C++ / wasm / UPDATES.md.
- Themes / Active chrome B. Gesture maps. A new home for Create/Modify.

## Done

Dig tip-scan committed for the docs brief, with the Chief lock baked. No coding `agy`. Pilot holds coding until overnight item 1 Tool Search exit and related tip-matches land, and until the brief tip-matches.
