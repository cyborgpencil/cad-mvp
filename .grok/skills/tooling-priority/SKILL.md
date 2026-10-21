---
name: tooling-priority
description: "Prioritize Grok Build for heavy autonomous coding, Cursor for interactive refinement, and Grok Bots for background work. Use when planning development workflow, assigning tasks across these tools, or optimizing token use without lowering quality."
type: workflow
lifecycle: active
---

# Tooling Priority — Grok Build → Cursor → Grok Bots

General workflow for any project. Maximize Grok Build tokens first, Cursor second, Grok Bots last. Protect quality and avoid wasted cycles.

## Core Priority

| Priority | Tool | Use for | Move to next when |
|----------|------|---------|-------------------|
| 1 | Grok Build | Large autonomous tasks, planning, parallel subagents, headless runs, multi-file generation | Interactive debugging or fine edits are faster |
| 2 | Cursor | Review, multi-file refinement, debugging edge cases, integration, daily editing | Task is recurring, research, or coordination only |
| 3 | Grok Bots | Research digests, documentation routines, progress summaries, preparing prompts, standing checks | Never for primary implementation of core logic |

## Workflow

1. Start non-trivial work in Grok Build plan mode. Load project rules (AGENTS.md or equivalent) and requirements. Approve the plan before code is written.
2. Execute in Grok Build. Prefer parallel subagents for independent modules. Require tests or validation in the same task. Produce clean diffs.
3. Move to Cursor only for interactive inspection, debugging, or polishing that would take more Build cycles.
4. Assign Grok Bots only to narrow, recurring, or research tasks that do not block coding.

## Quality Guardrails

- Always review diffs that touch core logic, validation, or export paths.
- Do not invent missing requirements or constraints. Stop and record the gap.
- Keep scope tight. Prefer incremental, testable commits.
- Re-scope failed tasks back to Grok Build instead of repeating them in Cursor or Bots.
- Capture successful patterns as skills or project notes for reuse.

## Token and Time Rules

- Use plan mode for anything larger than a small fix.
- Batch independent work in Grok Build.
- Switch to Cursor only when the interactive loop is clearly faster.
- Keep Bot routines narrow and non-blocking.
- Log decisions in project UPDATES.md or equivalent.

## Triggers

"tooling priority", "Grok Build first", "use Build then Cursor", "token priority for tools", "workflow across Build Cursor Bots"
