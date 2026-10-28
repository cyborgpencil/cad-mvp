# Plane-pick toggle INTENT proposal (2026-10-27)

Invent-free Dig - DEV proposal. Compiled **2026-10-27 ~6:45 PM MT** (America/Denver).

**Hard lock:** No invented px, hex, hotkeys, dims, control ids, or alternate plane paths outside sourced digest + tip code. Cite Dig prior pack + Doc invent-free discuss. Flag **GAPS** / **TBD**.

**SoT tip:** `5ee57ee` (after #240). Tip UX facts also verified against `bacb3f7` / `5ee57ee` `web/index.html` on ErmoZ13. **No Z13 CAD coding.**

**Folds:** Dig pack [`second-priority-toolbar-float-sketch-plane-2026-10-27.md`](second-priority-toolbar-float-sketch-plane-2026-10-27.md) §1 + Doc invent-free discuss (Chief steer: propose intent from known UX; no Erik bounce unless true GAP).

---

## Sources

1. Dig prior pack §1: `research/gui/second-priority-toolbar-float-sketch-plane-2026-10-27.md` (MVP tip table + peers; Fusion Selection Filters closest).
2. Tip `5ee57ee` / prior `bacb3f7` `web/index.html` (ErmoZ13 + GitHub): `#originPlanes`, `paintOriginPicker` (`show = sketchActive && !state.sketchPlane`), face path -> `setSketchPlane`, `#multiToggle` / `data-action="multiToggle"` flips `state.phoneMulti` only (toast Multi on/off), **not** plane-pick.
3. Doc invent-free discuss (relayed via Chief ~6:43 PM MT): Multi-like on/off sole job = enable/disable sketch plane/face pick; ON = current tip; OFF = plane-set paths inert; placement Multi neighborhood GAP; default prefer ON; GAP hide vs disable `#originPlanes`.
4. Peer cites remain those in Dig pack §1 Sources only ([F-S1]-[F-S4], [O-S1], [SW-S1][SW-S2], [SH-S1], [M-S1][M-S2]). Do not add new peer claims here.

---

## Proposed intent (for Chief lock / Doc tip-match)

**Name:** Sketch plane-pick enable toggle (Multi-like).

**Sole job:** On/off control whose **only** job is to enable or disable the tip paths that **set** `state.sketchPlane` while Sketch is active and no plane is set yet:

- Ortho chips on `#originPlanes` (`data-action="originPlane"` -> `setOriginSketchPlane`)
- Planar-face tap (`pickSketchFace` / `setSketchPlane`)

**ON (proposed default):** Match current tip behavior at `5ee57ee` / `bacb3f7` - plane pick always available when Sketch tab active and `state.sketchPlane` is null (ortho bar + face tap; status copy already prompts pick).

**OFF:** Those plane-**set** paths are **inert** (do not set `state.sketchPlane`). Do **not** invent: alternate plane, auto-plane, new hotkey, new pick filter mode, or wiring into `#multiToggle` / `state.phoneMulti`.

**Not this control:** `#multiToggle` stays phone multi-select (`state.phoneMulti`) only - Dig pack + tip confirm Multi ≠ plane gate.

**Closest peer pattern (wording only):** Fusion **Selection Filters** can block selecting a plane/face to start a sketch when Body Faces (and related) are off ([F-S3][F-S4] in Dig pack). Peers otherwise require plane/face pick to enter sketch; none publish a Multi-style optional gate (Dig pack §1).

**Placement (not baked):** Phone chrome / Multi neighborhood - **GAP** exact control id, markup, and placement until Chief locks. Do not invent an id.

**Reuse standing floor:** Any new tappable control keeps phone **≥44 CSS px** (Dig pack / `mobile-touch-cad.md`). No new px invented here.

---

## Align Dig + Doc

| Point | Dig pack §1 | Doc discuss | Dig now |
| --- | --- | --- | --- |
| MVP plane pick always on when Sketch + null plane | Yes | Yes | Agree |
| Multi ≠ plane-pick | Yes | Yes | Agree |
| Closest peer Fusion Selection Filters | Yes | Yes | Agree |
| Propose Multi-like on/off for plane/face set paths | Was TBD waiting Erik cut-off | Propose now without waiting | **Adopt Doc intent** (Chief steer) |
| Default ON | Not locked | Prefer ON to match tip | **Propose ON** |
| OFF = plane-set inert; no invent alternate | Implied by invent-free | Explicit | Agree |
| Exact id / placement | TBD | GAP Multi neighborhood | **GAP** |
| OFF hides `#originPlanes` vs only disables hit-testing | TBD | Chief call GAP | **GAP** (true) |

---

## Gaps / TBD (true - Chief call; no invent)

1. **Exact control id + placement** (phone chrome / Multi neighborhood only as neighborhood hint) - **GAP**.
2. **OFF chrome:** hide `#originPlanes` vs keep visible but inert / disable hit-testing only - **GAP** (Chief call).
3. Whether OFF also blocks re-pick after a plane is already set (clear plane / change plane) - **not stated** in Dig pack or Doc discuss -> **GAP / out of first tip** unless Chief expands.
4. Erik cut-off sentence ("currently I am able to…") remains unfinished - **not required** to lock this invent-free intent (Chief steer); bounce Erik **only** if Chief finds a true GAP beyond the rows above.
5. Hotkey, icon glyph, label string beyond "like Multi" - **TBD / do not invent**.
6. Interaction with `#pickFilter` / Body pick - tip keeps pick filter separate; do not invent merge - **out of scope unless Chief expands**.

---

## Next steps (Doc / Chief)

1. **Doc:** tip-match this proposal (invent-free second); prepare prompt draft **only after** Chief lock - no coding slice without lock.
2. **Chief:** lock final intent without Erik bounce unless a row in Gaps is unresolved as true GAP. Suggested lock wording:
   - YES Multi-like toggle; sole job enable/disable ortho + planar-face plane-**set** paths.
   - Default **ON** (= tip).
   - OFF = those paths inert; no alternate plane / auto-plane / hotkey / no reuse of `#multiToggle`.
   - Call GAP (2): hide `#originPlanes` vs disable hits only.
   - Call GAP (1): exact id/placement or park as TBD in prompt.
3. **Pilot / coding:** none until Chief lock + prompt tip-match on main. Track (2) shrink stays LOCK NO. Float track is separate (B).

---

## Related

- Dig pack: `gui/second-priority-toolbar-float-sketch-plane-2026-10-27.md` §1
- Float multi-agy split: `gui/float-multi-agy-split-2026-10-27.md`
- Chief prior lock: (1) was HOLD/TBD; this proposal supersedes wait-on-cut-off per Erik/Chief ~6:41-6:43 PM MT
