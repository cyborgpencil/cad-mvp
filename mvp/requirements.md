# MVP Requirements: Design-to-Print CAD Tool

**Status**: Confirmed  
**Date**: 2026-10-20  
**Scope**: Single-part 2D/3D design → STL/3MF for any slicer. Browser-portable target (WASM). C++ kernel preferred.

## Overview

Tool for creating precise or freeform 3D parts from 2D sketches or direct modeling, then exporting clean, slicer-ready files. Priority is reliable print output over full CAM or advanced simulation.

> [!IMPORTANT]
> Units must be locked and carried into the file.

## Goals

- 2D sketch (constraints) → 3D solid or mesh (extrude, revolve, boolean, fillet, freeform).
- Parametric history + direct edits.
- High-quality tessellation to STL and 3MF.
- MCP AI for natural-language design and validation ops.
- Basic measurements, healing, and export validation.

## Non-Goals (MVP)

- Full CAM toolpaths or machine simulation.
- 5-axis, generative design, advanced FEA, thermal, or motion studies.
- Multi-user collaboration, version control, or cloud features.
- PCB, sheet metal, or complex assemblies.
- Photorealistic rendering.

## Must-Have Features

| Feature | Acceptance Criteria |
|---------|---------------------|
| Units lock | Explicit mm/inch toggle; export includes correct units |
| Geometry healing | One-click or automatic fix for non-manifold edges, flipped normals, small gaps |
| Measurements | Viewport readouts for distance, angle, radius, and volume |
| Import | Baseline STL and STEP import |
| Export validation | Units pass/fail + recommended tessellation quality before download; free-edge count shown as information only |
| 3MF support | Units, single material/color, multi-body packing |
| Undo/redo + autosave | Reliable session history so modeling is not fragile |
| Selection & snapping | Face/edge/vertex selection + basic grid and vertex snapping |

## Core User Flow

```mermaid
flowchart LR
    A[2D Sketch or Import] --> B[Parametric Solid / Mesh]
    B --> C[Heal & Measure]
    C --> D[Validation Gate]
    D --> E[Export STL / 3MF]
    D --> F[MCP AI Ops]
```

> [!TIP]
> Default tessellation to “slicer-safe” (consistent normals, no holes). Allow user override for higher resolution.

## AI / MCP

- Built-in MCP server exposing: create sketch, extrude, fillet, boolean, heal, measure, validate, export.
- Agent can execute “add 2 mm fillet, check printability, and export 3MF”.

## Technical Notes

- Preferred: C++ + OpenCASCADE (OCCT) for B-Rep precision and STEP support.
- Browser path: Emscripten/WASM possible; watch binary size, boolean performance, and memory limits.
- Desktop fallback recommended for heavy operations.
- Hybrid: B-Rep for engineering features + mesh for organic shapes.
- **Rust WASM slice #1 (dual-run shadow)**: `rust/cadcam_gate` (`wasm32-unknown-unknown`, loaded via `web/rust-gate.mjs`) mirrors the millimeter units lock (`to_display`, `to_millimeters`, `export_units_pass`) and signed mesh volume (`mesh_volume_mm3`, `evaluate_rust_gate`) alongside C++ `Module.gate()`, publishing `#statusRustGate` and `window.__cadcamRustGate` (`matchesCpp`). C++ `Module.gate()` remains authoritative for Export button enablement; no OCCT / `libcascade` in Rust; watertight remains dropped as an Export gate. TBD: whether Rust replaces C++ `Module.gate()` is deferred until Erik decides.
- **Rust CLI slice #2 (CI dual-run shadow)**: `rust/cadcam_check_export` (`cadcam_check_export`, pure-Rust host CLI using `stl_io`, `zip`, and `quick-xml`) dual-runs in CI beside `tools/check_export.py` on `builds/export/box.stl` and `builds/export/box.3mf` (`--expect-size 20 20 20 --expect-volume 8000`); Python stays; `is_watertight` stays INFO-only and never decides the exit code.

## Phone UI (main, team-locked)

- **Callout hide (accepted 2026-10-26, Erik retest)**: On phone, while editing a basic shape (box / cylinder / disc, no sketch specs), `#calloutLayer` stays hidden. Size stays editable on `#dimPanel` / Properties (`boxSx`/`boxSy`/`boxSz`, cyl/disc Size). Shipped PR #123 merge `907402c` (tip `202a737`).
- **`#dimPanel` keep-lock (Chief, 2026-10-26 ~1:09 AM MT)**: Keep the dim body (Size / Centre / Rot / axis / bbox / hole). No full remove until those fields migrate into Properties and phone typed resize is confirmed. Later safe cut only: drop gizmo row / thin selection bar. No `#dimPanel` remove code until then.

## Overnight queue + wake acceptance (team-locked 2026-10-26 ~3:07–3:13 AM MT)

Erik hands-off overnight; final tool tests on wake. Stuck/help check every **20 minutes**. Coding stays **Antigravity-only on Z13**. Open questions: team discuss → 3T / Chief final call (no wait on Erik). Ping Erik only for irreversible or out-of-scope.

### Finish current first
1. **Rust #1** — Antigravity units + volume Export-gate mirror (`prompts/antigravity-rust-units-gate.md`): dual-run vs `Module.gate()`, C++ authoritative, no OCCT. Cascade: tip-match → merge → UPDATES (Repo Keeper) → Pages.

### Overnight locks (Chief/3T final, 2026-10-26)
- **(a)** Precise sketch = typed mm + callouts; **no** constraint solver.
- **(b)** **Keep boot cube**; Create Sketch empty path must never spawn a box (smoke: delete-all → New Sketch → `bodies.length===0` + `#originPlanes`).
- **(c)** View cube = **adjacent** face step; map swipe so direction matches “flip with swipe” (invert L/R if needed). Not opposite-face.
- **(d)** **Hide gizmo** in vertex/edge/face; keep for body/item.
- **(e)** E2E tonight = **STL + 3MF** only; STEP later.
- **(f)** Q5 discuss locked 2026-10-26 ~7:37 AM MT (below). Truck still TBD.

### Q5 discuss (team-locked 2026-10-26 ~7:37 AM MT)

Chief Q5, after overnight (1)–(4). No invented sizes; every missing dimension is **TBD**.

- **Primary rebuild** = phone L-bracket acceptance: 3 countersunk holes per leg + off-centre disc, via **sketch → Blind Extrude (New/Join/Cut) + Union/Cut**. Prefer the sketch path over primitives-only (`prompts/mobile-5-booleans.md`).
- `mvp/projects/blink-l-bracket.md` is **reference only**. Do not bake Blink layout or dimensions into the app or scene.
- **Truck** = discuss/spec only until sizes exist. **No invent**; flag **TBD**. Rebuild after L-bracket acceptance, or when Erik supplies sizes.
- **Union/Cut enough** for this rebuild. Intersect is not required (Intersect may remain in the UI).
- **No printer** send for Q5.
- **Dims TBD** (do not invent): leg A/B length×width; fit/clearance to frame casing; leg screw hole size, countersink, and spacing; Blink boss diameter/height; disc diameter and placement; disc screw count/size/pattern; Blink model; fillet/chamfer defaults; casing profile; screw gauge; printed hole oversize; material/printer.
- **Locked** (restated from `mvp/projects/blink-l-bracket.md` only): wall thickness **4 mm**, disc thickness **4 mm**, corner **90°**, units **mm**. Everything else TBD.

### After Rust #1 tip — Antigravity order
1. (2) Empty-sketch / no-solid Create Sketch never spawns box.
2. (4) Selection V/E/F: hide whole-body gizmo.
3. (3) View-cube swipe direction (adjacent).
4. (1) Sketch + dimensioning/visualization (typed + callouts; no solver).

### Rust conversion (continues; parallel when Independent)
- After #1: keep **dual-run shadow**, C++ boss, until smokes stay green.
- Next Independent: **#2** Rust CLI port of `tools/check_export.py` (CI-first).
- Then **#4** `.cadmvp` schema validate only if schema stays frozen.
- Skip #3 (watertight reopen), #5/#6 (OCCT/truck / AGPL bindings) for now.
- Parallelize Independent Rust with overnight UI slices when not blocked.

### Holds
- Phone T2 (move-gizmo) still held unless (4) requires related work.
- Watertight stays dropped as Export gate; units + OCCT-after-ops rules stay.
- `#dimPanel` keep-lock still applies.
- No printer send unless Erik said otherwise.

### Wake acceptance (Erik final tests when awake)
Leave smokes and Pages ready. **Human gate** = Erik runs this on [Pages](https://cyborgpencil.github.io/cad-mvp/) (or live main) after overnight lands. CI smoke + Pages green on main is the overnight bar.

#### Wake smoke checklist
1. **Empty sketch / boot cube (lock b)** — Delete-all → Create Sketch (no solid) → confirm odies.length===0 and #originPlanes visible; boot cube still present on fresh load (not removed).
2. **Sketch typed + callouts (lock a / queue 1)** — New Sketch on Top → draw closed profile → typed mm sizes via Properties/#dimPanel → callouts show matching values (no constraint solver expected).
3. **Boolean** — Two bodies → Union or Cut → result solid; undo restores prior.
4. **Selection V/E/F (lock d / queue 4)** — Switch vertex / edge / face: whole-body gizmo **hidden** in those modes; body/item mode still shows gizmo.
5. **View-cube swipe (lock c / queue 3)** — Swipe so the **adjacent** face steps in the swipe direction (not opposite-face flip). Invert L/R only if direction feels wrong.
6. **Export STL + 3MF (lock e)** — Box or boolean result → Export STL and 3MF → units mm; Export enabled only when C++ Module.gate() passes (Rust dual-run may show #statusRustGate / window.__cadcamRustGate.matchesCpp===true when loaded — informational).
7. **Phone sanity (if testing phone)** — Basic-shape edit: #calloutLayer hidden; Size still editable on #dimPanel. No printer send.

Pass = all seven feel right; fail notes go to the room (team discuss → Chief/3T call).

## Queued after current in-flight (discuss / parked)

End of queue (Erik via 3T, 2026-10-26 ~8:31 AM MT). **Status: discuss / parked.** Start only after the L-bracket Antigravity brief and tipped docs #155, #154, and #156 have cleared. Leave Pilot's in-flight L-bracket work uninterrupted. No Antigravity prompt for this item yet.

- **Top-bar shelf icons (selection + show/hide camera)**
  - Move the **selection** sliding toolbar and the **show/hide camera** sliding toolbar into **icons on the top bar, to the right of the tools menu**.
  - Separate by tool type. Selection gets its own icon group. Any further tool-type groups are **TBD**.
  - Same behavior as the tools menu: press the icon to show or hide that shelf.
  - **TBD:** icon art, pixel sizes, hotkeys, which existing controls are the selection shelf and which are the show/hide camera shelf, which bar is the top bar (header or the ribbon that holds the Tools menu), phone and desktop placement, and whether any shelf besides those two moves.

## Success Criteria

- User can go from blank sketch to validated, slicer-ready 3MF in a few minutes.
- Files open correctly in common slicers (PrusaSlicer, Orca, Bambu Studio, Cura) without scale or manifold errors.
- MCP commands reliably modify the model and trigger validation.

> [!NOTE]
> This document covers only the MVP. See `/vision/full-project.md` for post-MVP goals. Changes here do not affect the vision document.
