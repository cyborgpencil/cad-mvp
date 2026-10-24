# Post-P5c next-queue candidates (2026-10-24)

MVP Research Digest. P1–P5 parked queue is **closed** once PR [#70](https://github.com/cyborgpencil/cad-mvp/pull/70) (P5c sketch → Blind 10 mm) is on `main` (merge tip `7c83b2a` at write time). This note lists **only** deferred opens already recorded in research plus ready existing digests — for 3T to pick. Invent nothing. Units: **mm**. Gate: OCCT validity + units (watertight dropped, 02:17 rule).

## A — Deferred from locked slices

From [`research/gui/sketch-mvp-p5c.md`](sketch-mvp-p5c.md) **Still open**:

- Origin-plane fallback when no body exists (empty-document first sketch) — not locked.

From P5c recommended slice / PR #70 scope (same digest + #70 body):

- Extrude Join / Cut later if cheap (Blind **New Body** only in P5c).

From [`research/gui/ui-gap-p2.md`](ui-gap-p2.md) **Still open**:

- P1 Select-Other only if cheap; else follow-up.

## B — Ready existing research (one line each)

- [`research/gui/booleans-fillet-chamfer.md`](booleans-fillet-chamfer.md): MODO MeshFusion lessons + OCCT MakeFillet/MakeChamfer/Fuse with BRepCheck gate; L-bracket sequence is a **PROPOSAL** (dims TBD for Erik).
- [`research/occt-wasm/booleans.md`](../occt-wasm/booleans.md): exact OCCT Boolean on release (NonDestructive, Fuzzy TBD, GlueShift for coplanar contact only, SimplifyResult); ghost transform preview by default.
- [`research/project-save-load.md`](../project-save-load.md): end-to-end `.cadmvp` checklist P1–P7 (save → fresh-tab load → compare); undo stops at loaded state (team ruling).
- [`research/assemblies.md`](../assemblies.md): flat part list (placement mm + PLA/PETG/TPU); Combine = Fuse as one undo; one 3MF object per part. **Orca filament mapping still open.**
- [`research/projects/blink-mount.md`](../projects/blink-mount.md): Blink mount / door-casing / wood-screw research for the L-bracket sample path; mount geometry and Erik’s casing still TBD.
- [`research/ai-mcp/`](../ai-mcp/): MCP overview only; **tool list TBD for Erik** (INDEX already says this). See also [`overview.md`](../ai-mcp/overview.md).

## C — Suggested pickup order for 3T (non-binding)

1. Phone/Pages smoke of P5c after #70 deploy (verification on [Pages](https://cyborgpencil.github.io/cad-mvp/), not a research invent).
2. Origin-plane empty-doc (small UX lock needed) **or** Extrude Join/Cut (needs team lock on New/Add/Remove).
3. Boolean/fillet polish from existing digests if Pilot bandwidth.
4. Project save/load e2e checklist from `project-save-load.md`.
5. MCP tool list — wait for Erik (TBD).

## D — Next steps

- **3T:** pick one item and lock any TBD.
- **Doc Steward:** PROGRESS/UPDATES when a new parked/active row is chosen.
- **Pilot:** implement only after lock + prompt.

## Sources

Repo paths (primary):

- `research/gui/sketch-mvp-p5c.md`
- `research/gui/ui-gap-p2.md`
- `research/gui/booleans-fillet-chamfer.md`
- `research/occt-wasm/booleans.md`
- `research/project-save-load.md`
- `research/assemblies.md`
- `research/projects/blink-mount.md`
- `research/ai-mcp/overview.md`
- `research/INDEX.md`
- PR #70: https://github.com/cyborgpencil/cad-mvp/pull/70

Official / already-cited URLs copied from those digests (no new claims):

- OCCT `BRepPrimAPI_MakePrism`: https://dev.opencascade.org/doc/refman/html/class_b_rep_prim_a_p_i___make_prism.html
- OCCT Boolean Operations guide: https://dev.opencascade.org/doc/overview/html/specification__boolean_operations.html
- OCCT `BRepFilletAPI_MakeFillet`: https://dev.opencascade.org/doc/refman/html/class_b_rep_fillet_a_p_i___make_fillet.html
- Onshape Select Other: https://cad.onshape.com/help/Content/select-other.htm
- GitHub Pages deploy: https://cyborgpencil.github.io/cad-mvp/
