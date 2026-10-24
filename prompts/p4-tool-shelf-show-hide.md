# P4: show/hide on every tool shelf

Team-chosen by Doc Steward / 3T map, 2026-10-24. Erik parked the item on 2026-10-23 (center shape perimeter/size box toggles, open only when editing a basic shape). Feed this to Grok Build after P1. This file is the spec. It does not change the app.

Recorded in `web/PROGRESS.md` (parked queue). Status there: spec ready / waiting Pilot after P1.

## Context
- WASM UI in `web/` (mostly `web/index.html`). Work in the Z13 repo (`C:\Dev\cadcam-mvp`).
- Units stay millimetres. The inch control is display-only.
- Do not commit `.wasm`, `web/cadcam.wasm`, or `web/dist/`. Do not edit `UPDATES.md`. Do not add or edit a root `PROGRESS.md`.
- No kernel, C++, `src/`, `web/bindings.cpp`, or WASM rebuild. JS, CSS, and HTML only.
- Commit on a PR branch. Never push to main. Repo Keeper merges after `ci.yml` is green.

## Team-chosen behaviour
One show/hide (collapse) control per cluttering shelf. A shelf opens only while that tool or edit is active. Collapse clears viewport clutter. No shelf stays open on its own. The only open shelf is the active tool's shelf.

Cluttering shelves:
- Create menu/panel (`#createMenu`, openers `[data-action="createMenu"]`).
- Modify tools (`#modifyShelf`).
- Property and dimension panels (`#dimPanel`, and the inspector property block when it is the editing sheet).
- The center perimeter/size box for a basic shape.

Rules:
- Shelves start collapsed. Opening a tool or starting that edit opens its shelf. Leaving the tool collapses it.
- The show/hide affordance stays in the Tools sheet (`#toolsSheet`, opened by `data-action="toolsMenu"`). On a narrow layout the tool strip is already hidden and those actions live in this sheet. Do not add another always-on row of toggles.
- Reuse disclosure that already exists: `aria-expanded`, `aria-controls`, Escape to close, and a click outside to close. Touch targets at least 44×44 CSS px.
- Portrait sheet still respects the phone rule: an open sheet is at most about 40% of the view and never covers Home (`#vcHome`). `layoutDimSheet()` already caps `#dimPanel` at `min(space below Home, 40% of the viewport height)`, and the portrait CSS sets `.dim-panel.is-open { max-height: 40%; }`. Keep that.
- Modify already toggles (`#modifyBtn` on the phone bar, `#modifyDesktop` on the desktop bar, both `data-action="modifyShelf"`, `aria-controls="modifyShelf"`). Extend that pattern. Do not add a second Modify toggle.
- Export and the units status stay visible. They are status chrome, not shelves (`#exportBtn`, `#statusUnits` in the status bar). Do not hide them. Do not invent any other always-on shelf.

Center perimeter/size box:
- Visible only while editing a basic shape (box, cylinder, or disc). Hidden otherwise.
- On main the persistent viewport size line is `.hud` `#hudSize` (with `#hudName` and `#viewLabel`). Primitive sizes also live in `#dimPanel` (`#primBox`, `#primCyl`, `#primDisc`, centres in `#primCentres`). There is no separate perimeter widget.
- Apply this rule to the viewport perimeter/size readout (`#hudSize`). Leave the part name and the view label in place. Do not add a new Three.js helper, and do not hide Export or units to meet this rule.

## Acceptance
- Each cluttering shelf has a visible show/hide control, at least 44×44 CSS px, with `aria-expanded` matching open or collapsed.
- At load, those shelves are collapsed. The shelf opens when its tool or edit is active, and collapses when that tool is no longer active.
- The center perimeter/size box (`#hudSize`) shows only while a basic shape is being edited.
- Create still closes on Escape and on an outside click, and `aria-expanded` returns to `false` (the check already in `CREATE_MENU_EXPR`).
- Portrait: open dimension sheet stays at or under about 40% of the view and does not cover `#vcHome`.
- With every shelf collapsed, Export and the units status are still visible.
- The show/hide control is reached from the Tools sheet. No new always-on shelf.

## Tests
Extend the disclosure checks that already exist. Do not add a new smoke file or a new harness.

- `tests/deploy_smoke.py`: `CREATE_MENU_EXPR` (Create, `aria-expanded`, Escape, outside click, 44 px), `SEARCH_DISCLOSURE_EXPR` (Search pattern to copy), and the wrap-up Modify asserts. On main the desktop wrap-up expects `#modifyShelf` shown and the phone wrap-up expects it hidden. After this slice both start collapsed unless Modify is active, so update the desktop assert to collapsed-at-load. Keep the 44 px and `aria-expanded` / `aria-controls` checks.
- `tests/phone_smoke.py` already reads `#dimPanel`. Extend that check for the portrait 40% cap and Home clearance if the function is already asserting layout. Do not start a second phone suite.

## Out of scope
- P1 selection clarity (exclusive vertex / edge / face highlight).
- P3 shaders (flatter default material).
- P5 measure, live callouts, and sketch.
- Kernel, OpenCASCADE, and any WASM rebuild.

## Done
`ci.yml` green on the PR, then Repo Keeper merges. Report the PR link, the head SHA, and any team-chosen value that changed so Doc Steward can log it in `web/PROGRESS.md`.
