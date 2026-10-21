# Development Tooling Priority: Grok Build → Cursor → Grok Bots

**Status**: Draft outline  
**Date**: 2026-10-20  
**Scope**: MVP development only (design-to-print CAD tool). Does not alter feature requirements.  
**General skill**: See `.grok/skills/tooling-priority/SKILL.md` for the reusable version of this workflow.

## Goal
Maximize use of Grok Build tokens first, Cursor tokens second, and Grok Bot tokens last — without compromising geometry correctness, watertight export quality, or development speed.

## Tool Roles

| Priority | Tool | Best Use | Avoid For | Token Efficiency Notes |
|----------|------|----------|-----------|------------------------|
| 1 | **Grok Build** (terminal coding agent) | Large autonomous tasks: implement OCCT kernel wrappers, healing/validation pipeline, tessellation, MCP tool surface, build system, parallel module work via subagents, headless scripts | High-touch UI polish, one-line fixes, visual debugging | Plan mode + approved plans reduce wasted iterations. Batch independent modules with subagents. |
| 2 | **Cursor** (AI IDE) | Interactive refinement, multi-file review, debugging geometry edge cases, integration of Build outputs, tab-complete on complex C++/WASM, using Grok models inside the editor | Long unattended multi-hour autonomous runs | Use after Build produces a working draft. Switch models only when quality justifies the cost. |
| 3 | **Grok Bots** (persistent cloud agents) | Research digests (OCCT/FreeCAD/format updates), documentation maintenance routines, progress summaries, preparing next prompts, standing checks | Primary implementation of geometry kernel or performance-critical code | Keep routines narrow. Use for background work that does not block coding. |

## Recommended Workflow

1. **Architecture & planning** (Grok Build, plan mode)  
   Load `mvp/requirements.md`, `AGENTS.md`, and relevant research notes. Generate a modular plan for the kernel, validation gate, and MCP surface. Review and lock the plan before any code is written.

2. **Core implementation** (Grok Build primary)  
   - Parallel subagents for independent pieces (healing, units handling, STL/3MF export validation, basic sketch→extrude).  
   - Require tests or validation checks in the same task.  
   - Output clean diffs for human review.

3. **Refinement & integration** (Cursor)  
   Open the resulting changes in Cursor. Use agent mode with a Grok model for interactive debugging, edge-case fixes, and WASM/build adjustments. Keep sessions focused.

4. **Background & coordination** (Grok Bots, last)  
   - One bot owns research digests and updates `research/`.  
   - One bot owns documentation consistency (INDEX.md, UPDATES.md, requirements notes).  
   - Bots prepare scoped prompts or checklists for the next Build or Cursor session.  
   - Do not assign primary coding of the geometry kernel to bots.

## Quality Guardrails (non-negotiable)

- Every geometry change must include a manifold/watertight check and units verification.  
- Never invent missing constraints, tolerances, or material data — stop and record the gap.  
- Human review of all diffs that touch export, healing, or tessellation.  
- Keep strict MVP scope; do not expand into full CAM or advanced simulation.  
- Maintain living reference docs (`mvp/requirements.md`, research notes) and log changes in `UPDATES.md`.  
- Prefer incremental, testable commits over large unreviewed dumps.

## Token / Time Optimization Rules

- Start every non-trivial task in Grok Build plan mode and approve before execution.  
- Move work to Cursor only when interactive inspection or fine-grained editing is faster than another Build cycle.  
- Use Grok Bots only for recurring or research tasks that would otherwise interrupt coding.  
- When a task fails quality (e.g., non-watertight output), re-scope it for Grok Build rather than burning Cursor or Bot tokens on repeated failed attempts.  
- Capture successful workflows as Grok Build skills or project notes so later sessions reuse them.

## Open Questions

- Preferred local build environment (OS, compilers, existing OCCT install)?  
- Target browser WASM size/memory limits for the MVP?  
- Any existing prototype or preferred repository structure?  
- Exact SuperGrokPlus / Cursor plan token pools and reset cadence (user-specific)?

## Next Inputs Required

Confirm the above priority and any constraints on the local development machine before beginning implementation sessions.
