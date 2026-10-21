# Project Organization

**Date**: 2026-10-20

## Folder Structure

```
artifacts/
├── .grok/skills/      # Project skills
│   ├── project-organizer/
│   └── tooling-priority/   # General Build → Cursor → Bots workflow
├── ORGANIZATION.md    # This file
├── research/          # Background knowledge (Autodesk, FreeCAD, Blender, formats, MCP, etc.)
│   └── INDEX.md       # Entry point for research
├── mvp/               # MVP-only documents (scope, requirements, acceptance)
│   ├── requirements.md
│   ├── tooling-priority.md
│   └── get-started-with-grok-build.md
└── vision/            # Full project vision (post-MVP, independent)
    └── full-project.md
```

## Rules

- Keep MVP and vision documents strictly separate.
- Log meaningful changes in `UPDATES.md` (newest first).
- Use the `document-upgrader` skill when updating research or requirements so changes stay consistent.
- New research findings go under `research/` first, then get summarized into the relevant MVP or vision doc only if they change scope or goals.
- Diagrams use Mermaid where possible so they stay version-controllable and easy to update.

> [!TIP]
> When returning after time away, start at `UPDATES.md`, then `research/INDEX.md`, then `mvp/requirements.md`.
