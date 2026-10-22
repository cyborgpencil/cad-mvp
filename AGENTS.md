# CAD/CAM Project — Core Rules

## Core Principles
- **Honesty on missing information**: When any required input (specs, constraints, materials, machine details, tolerances, or context) is absent or ambiguous, stop and state exactly what is needed. Do not invent values, assume defaults, or proceed with incomplete data.
- **Update and organize project files**: After any meaningful research, decision, design change, or result, save updates to the correct location under `/workspace/artifacts/` (research/, mvp/, vision/, etc.). Update INDEX.md, ORGANIZATION.md, and UPDATES.md as needed. Create or revise reference documents so later work can check against them. Keep MVP and vision documents strictly separate. Apply the document-upgrader and project-organizer skills for consistency.
- **Reference documents**: Maintain living reference docs for key facts, standards, constraints, and decisions. Consult these before starting work or making choices; update them when new facts appear.

## Workflow
1. Review existing research notes, UPDATES.md, and reference documents.
2. Identify gaps and request missing information.
3. Perform the work.
4. Save outputs to the proper project folders and update related indexes/logs.
5. Note any remaining assumptions and the next required inputs.

## Output Standards
Prefer updates to existing project documents over one-off explanations. Explicitly list assumptions and open questions. Log significant changes in UPDATES.md.

## Push cadence (cyborgpencil/cad-mvp)
Erik approved pushing. The team set this cadence on 2026-10-21; Repo Keeper owns pushes.
- Code: commit and push once at the end of each Grok Build session, only after Grok Build Pilot's re-run passes the build, every CTest case, the STL/3MF export, and the mm checks. Pilot's pass post is the signal.
- Docs: doc-only commits are made locally right away and go up with the next code push. If no code push comes within about a day, push the docs on their own.
- Before every push: check `git status` for build, SDK, or mesh files; scan for keys, tokens, and local user paths; then do a normal `git push` to `main`.
- Never: push a failing build or test, force-push, amend or rebase pushed commits, or push while a Grok Build session is still editing the tree.
- A rejected push, conflict, or login prompt means stop and report in the group.
- After each push, post the commit links and the changed core files so Erik can review them.

## Keep finished work (Erik's rule, 2026-10-21)
- Keep everything Grok Build has already finished (the Qt app, export, units, tests in dfb46b7, and the rest) unless something actually needs to change.
- No rewrites or deletions of finished code. Any change to existing code needs a reason posted in the CAD CAM MVP group first, and the current tests must keep passing.
- The mockup lives only in mockup/. Stack work builds on what is there.
- OpenCASCADE fillet and cut are added next to the existing mesh code, not in place of it. Changing or removing the mesh path later needs a posted reason first.
- Repo Keeper runs git diff --stat before every commit and holds any commit that changes code outside mockup/ or the docs without a posted reason.

## Z13-only execution (Erik's rule, 2026-10-21)
All project work runs through Shell aimed directly at the dev PC (Z13). Nothing runs from ErmoAlly, and nothing goes through a WinRM hop. Grok Build sessions, captures, builds and git all run on Z13.

## Handoff folder for files going to Erik (2026-10-21)
The app's file copy only reads under `%USERPROFILE%`, so it can't copy anything out of `C:\Dev\cadcam-mvp`. Files meant for Erik, such as screenshots or the mockup HTML, get one extra copy in `%USERPROFILE%\Pictures\cadmvp-shots\` on Z13. The working copy stays in `builds\`. This folder holds handoff copies only, never project work. It's an exception to the Z13-dev-folder-only rule, set by 3T; Erik can confirm or change it. Don't delete anything in this folder unless Erik says to (3T, 2026-10-21).
The shared skill `pull-files-from-user-pc` covers this method: stage with Shell, leave the originals untouched, then copy from the staging folder.

## Team rules (Erik, 2026-10-21)
- Flexibility: roles are defaults, not walls. If an owner is busy, stalled or offline, the next best-fit bot takes over. Say so in the room, read the owner's latest status and files first, and hand the work back cleanly when the owner returns. Safety rules still apply.
- Research first: before any task, check the repo, docs, earlier work, skills and memory, plus sourced best practices. Post a short plan with sources, then start.
## Overnight override 2026-10-22 (tonight only, Chief 02:17 MT)
- HYBRID tooling for tonight only: Grok Build and Cursor cloud agents both write code. Cursor cloud agents take repo feature work (nav cube, save/load, assemblies, new tools), each as its own PR with CI, reviewable by Erik in the morning. Grok Build Pilot keeps Z13-bound work: finishing the phone fix, the gizmo/undo/shading/tooltip batch, local C++/WASM rebuilds, and Acceptance A and B in OrcaSlicer, and writes the Cursor launch prompts for steps 2 and 3 with Doc Steward. The normal Grok Build -> Cursor -> Grok Bots priority returns after tonight.
- Merge rules: every change lands through a PR. Repo Keeper merges only after CI (ci.yml on pull_request) is green and the secrets/Blink scan passes. Branch protection requires ci.yml. No force-push. No direct pushes to main while a PR is open.
- Before starting work and before every merge, run git pull --ff-only; if it can't fast-forward, stop and ask Repo Keeper instead of merging or rebasing.
- Unchanged: units in mm and the OCCT shape-validity check after fillet, chamfer, Boolean and delete. No watertight requirement.
## Coding tools (Erik, 2026-10-22)
- Order: Grok Build, then Cursor, then Google Antigravity (third, end of queue, trial). Gemini Code Assist GitHub review app approved; install pending Erik's sign-in. Details: mvp/tooling-priority.md.
