# Float+drag+X multi-Antigravity split proposal (2026-10-27)

Invent-free Dig - DEV proposal. Compiled **2026-10-27 ~6:45 PM MT** (America/Denver).

**Hard lock:** Split boundaries come only from `prompts/antigravity-offbar-menus-float-drag-close.md` sections/tasks + Doc invent-free 3-way discuss. No invented px/hex/hotkeys/ids. Snap / persist / z-order stay **TBD OUT**. Menu-bar shrink **OMIT** (Chief LOCK NO). **No Pilot launch** until Chief locks this split after Dig+Doc tip-match style review.

**Base SoT tip:** `5ee57ee` (merge #240). Prompt landed via #239 @ `adf0a7d` / main `3280162`; file still present at `5ee57ee`.

---

## Sources

1. GitHub `cyborgpencil/cad-mvp` file `prompts/antigravity-offbar-menus-float-drag-close.md` @ ref `5ee57ee` (raw via cursor-github get_file_contents).
2. Dig pack §3 + Chief lock (3): float + drag + explicit Close; snap/persist/z-order TBD - `research/gui/second-priority-toolbar-float-sketch-plane-2026-10-27.md`.
3. Doc invent-free discuss (relayed ~6:43 PM MT): 3-way split `agy-float-register` / `agy-close-chrome` / `agy-regression-smoke`; alt 2-way register+Close with smoke in Success Criteria.
4. Prompt hard lock: Antigravity-only on Z13; Pilot one `agy` after file tip-matches - Erik standing prefer **multi then merge**; this digest proposes how to split that one feed across multiple agy runs then merge.

---

## Prompt structure (cite headings only; invent-free)

From the prompt file at tip `5ee57ee`:

| Prompt block | What it locks |
| --- | --- |
| **Gate / Hard lock / Source of truth** | Chief (3) only; tip ids `#fileMenu`, `#exportMenu`, `#createMenu`, About `.menu` (no id); reuse `setupFloatingPanelDock()`; Close reuse `#toolsSheet` `closeSheet` -> `closePopups()`; ≥44 floor |
| **Goal** locked behaviors 1-4 | Float; Drag (extend `floatPanels`); Explicit Close top chrome; Dismiss via existing path |
| **Workflow** steps 1-6 | Read locks -> register four menus -> `applyPanelPosition` / `position: fixed` -> add Close `.sheet-h` -> leave TBD -> no regress existing `floatPanels` |
| **Do not bake / TBD** | Snap grid beyond edge dock; persist XY; z-order; corner pin; new ids/px/hex/hotkeys; plane-pick; shrink |
| **Out of scope** | (1) plane HOLD; (2) shrink LOCK NO; item-7; `#pickChooser`; UPDATES from brief |
| **Smoke** + **Success Criteria** | Manual wake smoke; 6-7 locked checks; no new harness required |

Menus in brief (full set): `#fileMenu`, `#exportMenu`, `#createMenu`, About `.menu-wrap .menu[aria-label="About"]` (no invented id).

---

## Proposed slices (Dig adopts Doc 3-way; alt noted)

### Slice 1 - `agy-float-register` (Workflow 2-3 / Goal Float+Drag)

**In:**

- Extend existing `setupFloatingPanelDock()` `floatPanels` (or same pointer handlers) to register the four menus named in Goal / Workflow 2.
- Reuse existing `applyPanelPosition` + existing `position: fixed` assignment pattern (prompt: already used for `#browser` / `#inspector`) so bar-anchored menus can leave absolute dropdown anchoring; `#createMenu` already `position: fixed`.
- Keep early-return for `input, textarea, select, a, label.menu-file` and `tapSlopPx()` threshold (Goal Drag).
- Do **not** register `#pickChooser` or `#inspector [aria-label="About"]`.

**Out of slice 1:** Close UI / `.sheet-h` rows; new smoke harness; snap/persist/z-order; shrink; plane-pick.

### Slice 2 - `agy-close-chrome` (Workflow 4 / Goal Explicit Close + Dismiss)

**In:**

- Add reused Close control on each of the four menus: `.sheet-h` row + `button.icon-btn` + `data-action="closeSheet"` + `aria-label="Close"` + `<span>Close</span>` (mirror `#toolsSheet` header; do not copy `data-tool="Close tools menu"` onto File/Export/Create/About).
- Dismiss stays existing `closeSheet` -> `closePopups()` / `setToolsOpen(false)` (Goal Dismiss). Do not invent action names.

**Depends on:** Slice 1 landed (or same merge train **after** slice 1) so Close sits on menus already in the float-dock set. Doc: "Depends on (1) or same merge train after (1)."

**Out:** New drag system; corner pin CSS; snap/persist/z-order; new px.

### Slice 3 - `agy-regression-smoke` (Smoke + Success Criteria; verify-only / tiny fix)

**In:**

- Verify-only (preferred) against prompt Smoke 1-6 / Success Criteria 1-7: four menus float+drag; Close dismisses; existing `#sketchSheet`, `#edgeSheet`, `#toolsSheet`, `.vp-bar`, `#searchDlg`, `#browser`, `#inspector` still float/dock; outside-click `closest` ignore list unchanged; no new px/z/hotkeys; snap/persist/z-order **not** implemented.
- Tiny fix **only** if a slice 1/2 regression against those locked checks is found - no scope expansion.

**Out:** New smoke harness unless clearly required (prompt: does not require new harness); pixel asserts; UPDATES edits from agy.

### Alt 2-way (Doc; Dig OK if Chief prefers fewer merges)

1. **register+fixed all four** (= slice 1)
2. **Close chrome** (= slice 2); fold slice-3 checks into Success Criteria of (2) / Pilot wake smoke

Dig **primary recommendation:** Doc **3-way** - matches Erik multi-then-merge and isolates Close from register (lower conflict surface on HTML chrome vs JS dock list).

---

## Merge order / conflict risk (invent-free)

| Order | Why | Conflict risk (from prompt file touch surface) |
| --- | --- | --- |
| 1 then 2 then 3 | Doc depend rule; register before Close chrome | **Low-med:** slice 1 mostly JS `floatPanels` / `applyPanelPosition` branch; slice 2 mostly HTML headers inside the four menus + shared dismiss already wired. Same file `web/index.html` -> sequential merge train reduces clash. |
| 1+2 same PR train, 3 verify | Fewer tips | **Med:** one large HTML+JS diff; harder tip-match blame. |
| Parallel 1 and 2 without rebase | - | **High:** both touch the four menu nodes / same `web/index.html` - avoid. |

Prompt already says: do not commit from Antigravity; Pilot/Repo Keeper commit path; draft until tip-match; Dig COMMENT-only. Multi-agy ⇒ each slice gets its own prompt file or clearly scoped agy brief derived from the landed monolith - **Doc owns prompt split files after Chief lock**; Dig does not invent filenames beyond the Doc labels above.

**Still OUT for all slices:** snap grid beyond existing edge dock; persist XY; z-order / new `z-index` (prompt: `.menu` 30 / `.create-menu` 40 leave them); plane-pick; shrink; `#pickChooser`.

---

## Align Dig + Doc

| Point | Dig | Doc | Dig now |
| --- | --- | --- | --- |
| Split from prompt Workflow/Goal/Smoke | This digest | 3-way labels | Agree 3-way primary |
| Slice 1 = register + fixed; no Close | - | Yes | Agree |
| Slice 2 = Close reuse; after (1) | - | Yes | Agree |
| Slice 3 = verify-only / tiny fix | - | Yes | Agree |
| Alt 2-way OK | - | Yes | Note for Chief |
| Snap/persist/z TBD out | Dig pack + prompt | Yes | Agree |
| No Pilot until Chief locks split | Prompt Gate + Chief | Yes | Agree |
| Shrink omit | Chief LOCK NO | Yes | Agree |

---

## Gaps / TBD (true)

1. Whether Chief locks **3-way** vs **alt 2-way** - Chief call (not a product GAP).
2. Exact new prompt filenames / how Pilot launches N agy from split files - **Doc after lock**; do not invent path beyond Doc labels `agy-float-register` / `agy-close-chrome` / `agy-regression-smoke`.
3. Snap / persist / z-order - still **GAP / TBD OUT** (unchanged).
4. Close "top-right" visual pin - Dig pack CAUTION; prompt reuses `.sheet-h` without far-edge pin - **do not invent pin** (already locked in prompt).

No Erik bounce required for this track unless Chief rejects multi-agy entirely (product preference already "multi then merge").

---

## Next steps (Doc / Chief)

1. **Doc:** second this split invent-free; if Chief locks 3-way, author split prompt files (or scoped briefs) from the monolith **without** expanding TBD; tip-match each before Pilot.
2. **Chief:** lock 3-way (recommended) or alt 2-way; confirm merge train **1 -> 2 -> 3**; keep snap/persist/z OUT; no Pilot until lock + tip-match.
3. **Pilot:** HOLD until Chief go post-lock.
4. **RK:** sequential undraft/merge per slice tip-match (Dig primary COMMENT, Doc second).

---

## Related

- Landed prompt: `prompts/antigravity-offbar-menus-float-drag-close.md` @ `5ee57ee`
- Dig pack §3: `gui/second-priority-toolbar-float-sketch-plane-2026-10-27.md`
- Plane-pick intent (separate track): `gui/plane-pick-intent-proposal-2026-10-27.md`
