# Antigravity app-wide redundancy pass

An app-wide redundancy pass over tip chrome. Dig inventoried duplicate controls. That inventory is not a punch list, and this brief does not add one. Collapses already named by overnight items 4–8 stay in those briefs. This file is the Antigravity feed. It does not change the app by itself.

**Gate:** This item’s **code** starts only after this file tip-matches on main **and** overnight item 1 Tool Search exit plus related tip-matches have landed. Overnight 1–2 briefs are on main ([#208](https://github.com/cyborgpencil/cad-mvp/pull/208) @ `c713ce4`). Item 3 brief is on main ([#210](https://github.com/cyborgpencil/cad-mvp/pull/210) @ `1b8a57f`; UPDATES [#211](https://github.com/cyborgpencil/cad-mvp/pull/211)). Pilot holds the coding `agy`. This prompts file does not start an `agy` by itself. Docs base is main @ `7214005` (`72140052f516b59d6560133fc4240f13e5d257c7`, tip after #211). Dig’s scan tip for `web/` remains `c713ce4` (`c713ce4479349fe11d56a53921edb7dafe866038`). #209/#210/#211 are docs/UPDATES only relative to that Dig scan for View/chrome facts. Do not re-spec #208. Do not re-spec item 3. Do not re-spec themes / Active chrome B. Do not re-spec items 4–8; cite them.

**Hard lock:** Implementation is **Antigravity-only on Z13**. Pilot holds one `agy` until this file tip-matches on main and the item-1 hold above has lifted, then owns one `agy`. Do not use Grok Build or Cursor for the handoff into code. Prefer a worktree under `C:\Dev\`; do not invent a new path or create folders from this brief. Do not commit from Antigravity; Pilot/Repo Keeper commit path owns that. Do not invent Erik specs. Stay in `web/` (JS, HTML, CSS). No kernel, C++, `src/`, bindings, or wasm rebuild. No new control ids, hex, pixel sizes, gesture maps, themes, Active chrome B changes, or invented relocation homes. No invented punch list.

**Source of truth:**

- Erik overnight ~11:55 PM MT 2026-10-26, item **(9) App-wide redundancy pass**, via CAD Chief. Invent-free. That message has no further detail.
- `research/overnight-app-wide-redundancy-pass.md` (Dig, 2026-10-27 ~1:15 AM MT), scanned at tip `c713ce4`. Cite that digest. The duplicate table is an inventory. It is not an acceptance matrix.
- Items 4–8 are the named anti-redundancy moves from the same overnight message. Their briefs own those moves. This pass does not add a second spec for View placement, Home placement, cube double-tap, sketch clauses, or the bottom bar.
- P4 (`prompts/p4-tool-shelf-show-hide.md`) and hide-prior tool UI (#208, `prompts/antigravity-switch-hide-prior-tool-ui.md`) stay as written. Do not re-spec them.

Dig’s tip inventory at `c713ce4` (facts only; not a removal order):

| Duplicate / overlap | Tip evidence |
| --- | --- |
| Home control ×2 | `#vcHome` mid-top and Camera shelf Views `data-view="home"` (title Iso). Item 5 owns placement. The destination node stays TBD there. |
| Home vs Iso angles | `VIEWS.home` and `VIEWS.iso` share `theta` / `phi`. |
| Create ×2 | `.desk-bottom` Create and `.phone-tabbar` `#createBtn` Create, both `data-action="createMenu"`. Item 8 owns the bottom bar. |
| Modify ×2 | `.desk-bottom` `#modifyDesktop` and phone `#modifyBtn`, both `data-action="modifyShelf"`. Item 8 owns the bottom bar. |
| View tools vs Camera shelf | Viewport View `vp-bar` versus `#cameraShelf`. Different controls. Item 4 owns the View popup move. Whether the Views cluster is included stays TBD there. |
| Isolate ×2 | Camera shelf Isolate and Items browser `#isoBtn`. Not named by Erik. |
| Theme pickers ×2 | About in `.topbar-shelves` and inspector About `data-action="theme"`. Not named by Erik. Active chrome B stays locked. Do not restyle. |
| Selection entry points | `#selectionShelfBtn` / `#selectionShelf` and phone `#pickFilter` / `#pickChooser`. Not named by Erik. |
| Units surfaces | Footer `#statusUnits` and export gate `#gateUnits`. Related, not the same UI. Do not change the units gate. |

**Gap:** Erik named a pass and did not say which duplicate wins.

## Goal
Implement no redundancy removal beyond what items 4–8 already require. No kernel, C++, `src/`, bindings, or wasm rebuild.

Coding bar:

1. The pass is real as a limit: do not add a second copy of a control while doing items 4–8, and do not invent extra collapses in this item.
2. Duplicates that items 4–8 already name are collapsed only by those briefs, under their TBDs and Chief locks.
3. Any other row in the inventory stays until Erik or Chief cites it. Isolate, theme pickers, selection entry points, Home-versus-Iso angles, and the units-gate surface are not a punch list.
4. Phone versus desktop media-split pairs are not declared redundant here. That question stays TBD.

Where the digest says **TBD**, leave it **TBD**.

## Workflow
1. Read `research/overnight-app-wide-redundancy-pass.md`. Use the table as an inventory only.
2. Do not delete, merge, or restyle a row that items 4–8 do not already require.
3. Do not pick a winner for any TBD pair.
4. Do not change themes, Active chrome B, gesture maps, or the units gate while noting those overlaps.
5. Do not write a punch list into code comments, a checklist file, or a smoke assert.

## Do not bake / TBD
Do not invent and do not bake any of the following. They stay **TBD**:

- An ordered punch list
- Which duplicate wins
- Whether phone/desktop media-split pairs count as redundancy
- Whether Isolate, theme, or selection pairs are in scope
- Whether Home and Iso sharing angles is a bug to “fix”
- Screenshots / visual QA (item 10 is a separate note, not this pass)
- Any new control id
- Any new hex
- Any new pixel size
- Icon art
- Hotkeys
- Gesture maps
- Themes or Active chrome B
- A new home for a control removed from a duplicate pair

## Out of scope
- Re-spec of items 4–8. Follow those briefs for the moves they already name.
- Item 10 rebuild / Orca / screenshots. No chrome brief.
- Overnight 1–2 (#208) and item 3.
- A full information-architecture redesign.
- Rust #4 / Modo orange selection hex / triple-tap.
- Kernel / wasm / export path.
- Editing `research/overnight-app-wide-redundancy-pass.md`, `mvp/requirements.md`, or `UPDATES.md` from the coding `agy`.
- Editing `web/` from this docs PR.
- Kernel / C++ / wasm rebuild. Do not commit `.wasm`, `web/cadcam.wasm`, or `web/dist/`. Do not edit a root `PROGRESS.md`.

## Smoke
Manual wake smoke on Pages. No new smoke harness. Reuse `tests/deploy_smoke.py` only if that reuse is clearly required; this brief does not require it. No invented pixel asserts. Because no smoke path is added here, do not print a done marker.

Check sourced behavior only. Do not assert that Isolate, theme, selection, or units-gate duplicates were removed.

1. No punch-list removal landed from the inventory table.
2. Items 4–8, when they land, are not given a second conflicting collapse by this pass.
3. Themes, Active chrome B, and the units gate are unchanged by this pass.

## Success Criteria
Must PASS at tip-match. Cite Erik overnight item (9) ~11:55 PM MT 2026-10-26 via CAD Chief; `research/overnight-app-wide-redundancy-pass.md`; tip `c713ce4`. Only that bar is in scope.

1. The pass does not invent a punch list.
2. Removals beyond items 4–8 do not ship without a later Erik or Chief cite.
3. The Dig table remains an inventory. It is not success criteria for which control survives.
4. No invented control id, hex, pixel size, gesture, theme, Active chrome B change, or relocation home.
5. This docs PR does not change `web/`.

Outside this hard bar: ordered winners; media-split pairs; Isolate / theme / selection scope; Home versus Iso angle equality; item 10 screenshots; items 1–8 as re-specs; `UPDATES.md`; kernel / C++ / wasm.

## Done
Draft until tip-match: Doc Steward primary (COMMENT), Research Digest second. Author does not self-APPROVE. Repo Keeper undrafts and plain-merges. Pilot holds the coding `agy` for this item until overnight item 1 Tool Search exit and related tip-matches have landed **and** this brief tip-matches on main. This file does not start an `agy`. One Antigravity-only `agy` on Z13, `web/` only, after that hold lifts. Report the prompt PR link and tip SHA. Pilot reports any implementation PR separately.
