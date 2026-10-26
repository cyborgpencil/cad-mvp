# Antigravity truck MVP (Q5, after L-bracket)

Q5 truck rebuild on the live app. This file is the Antigravity feed. It does not change the app by itself.

**Gate:** L-bracket accepted via merged #165 @ `8248749`. The truck rebuild gate is open.

**Hard lock:** Implementation is **Antigravity-only on Z13**. Pilot stages the worktree and owns the one `agy` run after this brief is on main. Do not use Grok Build or Cursor for the handoff into code. Work only in `C:\Dev\cadcam-mvp`. Do not commit; Repo Keeper commits. Do not invent Erik specs.

**Source of truth:** Toy truck feature list in `mvp/requirements.md` (PR #156 @ `47d2312`) and truck parts in `mvp/acceptance-a-b.md`. Also `prompts/mobile-5-booleans.md` (Union/Cut; Intersect may stay in the UI) and `prompts/assemblies.md` (flat parts, mm, per-part 3MF). Sizes below are **sourced team-chosen Acceptance B baselines**. They are not new Q5 locks. Anything not listed stays **TBD**.

## Goal
Build the 11-part toy-truck MVP. Path: sketch → Blind Extrude (New/Join/Cut) → Union/Cut. Prefer the sketch path over primitives-only. Units **mm**. No printer send. Prefer the **11-part** assembly (PLA hubs + TPU tires).

## Workflow
1. Chassis/body (PLA): sketch the plate **80×30 mm**, Blind Extrude **6 mm**. Two **Ø4.4** through-holes across the 30 mm width, **10 mm** in from each end, **3 mm** up. Holes via **Cut**.
2. Cab (PLA): sketch **30×30 mm** on the chassis top at the front, Blind Extrude **25 mm**. **Union** into the chassis. That combine leaves **11 parts** (1 body + 2 axles + 4 hubs + 4 tires).
3. Axles ×2 (PLA): sketch a **Ø4** circle, Blind Extrude **44 mm** (New). They are the axle parts for the sourced chassis holes. Do not add an unsourced offset.
4. Wheel hubs ×4 (PLA): sketch a **Ø16** circle, Blind Extrude **8 mm**. Bore **Ø4.2** via **Cut**.
5. Tires ×4 (TPU): ring **OD 24 / ID 15.6 / width 8**. ID via **Cut**. **0.2** stretch on the hub.
6. After each op: units check (**mm**) and OCCT shape-validity. OCCT validity does not block Export. Watertight and free-edge count are INFO-only.
7. Export STL and 3MF when C++ `Module.gate()` passes. Units stay mm.

**Union/Cut only.** Intersect is not required (it may remain in the UI). Do not Combine a hub with a tire (mixed materials; sourced in `mvp/acceptance-a-b.md`).

## Do not bake
Do not implement, and do not invent dimensions for: bed/cargo box, wheel spokes, tire tread, interior, separate doors. Fillet and chamfer stay non-blocking until a value is sourced. Do not invent defaults. Multi-plate Orca (PLA + stock TPU 95A) stays later. No printer send.

## Smoke
Build the 11 MVP parts on the path above. Export STL and 3MF in mm when `Module.gate()` passes. Skip numeric `--expect-size` / `--expect-volume` on the truck files. No locked total volume is sourced (volume is **TBD**). Both checkers require those flags, so do not invoke them on the truck files. Print `TRUCK_MVP_DONE`.

## Done
Draft until Doc Steward tip-matches (primary COMMENT) and Research Digest tip-matches (second). Author does not self-APPROVE. Repo Keeper undrafts and plain-merges. After this file is on main, Pilot runs one Antigravity-only `agy` session from it. Report the prompt PR link and tip SHA; Pilot reports any impl PR separately.
