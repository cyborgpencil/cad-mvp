---
name: project-organizer
description: "Keep CAD/CAM project files organized, correctly saved, and consistently structured. Use when creating or updating any project document, research note, requirement, or prompt."
type: workflow
lifecycle: active
---

# Project Organizer — Save and Structure Files Correctly

## Rules
- Save all new work under `/workspace/artifacts/`.
- Place research in `research/` (with subfolders), MVP items in `mvp/`, long-term vision in `vision/`.
- Never mix MVP scope into vision documents or vice versa.
- After any meaningful change, update:
  - `research/INDEX.md` (if research structure changes)
  - `UPDATES.md` (newest entry at top)
  - `ORGANIZATION.md` only if folder rules change
- Use `document-upgrader` for content consistency; use this skill for location and structure.
- Prefer living reference documents over one-off notes.

## Workflow
1. Confirm correct folder for the content.
2. Write or update the file.
3. Update INDEX.md and UPDATES.md.
4. Note the change in project memory if durable.

## Triggers
"Save this", "organize the docs", "update the project files", "where should this go".
