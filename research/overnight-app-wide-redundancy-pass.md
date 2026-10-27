# App-wide redundancy pass — invent-free digest (overnight item 9)

Status: invent-free digest. Compiled **2026-10-27 ~1:15 AM MT** (America/Denver).
Antigravity feed: `prompts/antigravity-app-wide-redundancy-pass.md`. This digest does not start an `agy`.

**Owner draft:** MVP Research Digest (tip-scan). Doc Steward primary tip for any `prompts/` PR.
**Date:** 2026-10-27 ~1:15 AM MT (America/Denver)
**Gate tip:** main @ `c713ce4` (`c713ce4479349fe11d56a53921edb7dafe866038`) — [#208](https://github.com/cyborgpencil/cad-mvp/pull/208) merged.
**Scope:** Inventory tip redundancies that a pass might touch. UI chrome.
**Hard lock:** Invent-free. Erik asked for an **app-wide redundancy pass**. This digest lists tip duplicates only. It does **not** invent the acceptance matrix or which duplicate wins. No punch list. No new control ids, hex, pixel sizes, gesture maps, themes, or Active chrome B changes.

---

## Source of truth (cite only these)

### Erik / team

| Source | Statement |
| --- | --- |
| Erik overnight ~11:55 PM MT 2026-10-26 via CAD Chief | Item **(9) App-wide redundancy pass**. Invent-free; no further detail in that message. |
| Related overnight lines (same message) | Items 4–8 already name specific chrome moves that are themselves anti-redundancy (View show/hide, Home move, bottom-bar remove). Item 9 is the wider pass. |
| Always-visible / P4 / hide-prior parks | Show/hide shelves; hide prior tool UI (#208 brief). Cite as related locks — do not re-spec. |

### Tip redundancies observed on `c713ce4` (facts only)

| Duplicate / overlap | Tip evidence |
| --- | --- |
| Home control ×2 | `#vcHome` mid-top **and** Camera shelf Views `data-view="home"` (title Iso). |
| Home vs Iso angles | `VIEWS.home` and `VIEWS.iso` share identical `theta`/`phi`. |
| Create ×2 (desktop vs phone) | `.desk-bottom` Create **and** `.phone-tabbar` `#createBtn` Create (media-split, same `data-action="createMenu"`). |
| Modify ×2 | `.desk-bottom` `#modifyDesktop` **and** phone `#modifyBtn` — both `data-action="modifyShelf"`. |
| View tools vs Camera shelf | Viewport View `vp-bar` (Measure/Section/Display) vs `#cameraShelf` (Orbit/Pan/Zoom/Fit + Views + Isolate/Hide) — overlapping “viewing” concerns; different controls. |
| Isolate ×2 | Camera shelf Isolate **and** Items browser `#isoBtn` Isolate. |
| Theme pickers ×2 | About menu in `.topbar-shelves` **and** inspector About `data-action="theme"` group. |
| Selection entry points | Topbar `#selectionShelfBtn` + `#selectionShelf` modes **and** phone `#pickFilter` / `#pickChooser` (Body/Face/Edge/Vertex). |
| Units display ×2 surfaces | Footer `#statusUnits` **and** Export gate `#gateUnits` / unit lock copy (related, not identical UI). |

This table is an invent-free tip inventory. It is **not** Erik’s ordered punch list.

**Gap vs Erik wording:** Erik named a pass but did not list which redundancies to remove, which copy to keep, or success criteria. Do not invent that list beyond tip facts and the other overnight lines (4–8).

---

## Recommended invent-free goal (for `prompts/`)

1. Run an **app-wide redundancy pass** (Erik) on tip chrome after / alongside items 4–8 where they already remove named duplicates.
2. Prefer collapsing tip duplicates that items 4–8 already name (View placement, Home placement, bottom bar) before any other collapse. Do not re-spec those briefs here.
3. Any removal beyond 4–8 needs an invent-free cite (Erik/Chief) or stays TBD. Do not invent a punch list from the table above.

**TBD (do not invent):**

- Ordered punch list and which duplicate wins.
- Whether phone/desktop media-split pairs count as redundancy.
- Whether Isolate / Theme / Selection pairs are in scope.
- Visual QA bar / screenshots (item 10 is a separate note, not a chrome brief).
- Kernel / wasm / docs churn.

## Out of scope

- Inventing a full IA redesign.
- Rust #4 / Modo orange sel hex / triple-tap.
- Themes / Active chrome B changes. Gesture maps. New homes for relocated controls.
- Coding from this digest alone.

## Done

Dig tip-scan committed for the docs brief. No punch list. No coding `agy`. Pilot holds coding until overnight item 1 Tool Search exit and related tip-matches land, and until the brief tip-matches.
