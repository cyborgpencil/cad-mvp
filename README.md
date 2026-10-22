# CAD/CAM MVP

Design-to-print MVP. Requirements and acceptance criteria are in [mvp/requirements.md](mvp/requirements.md).

Units are millimeters, with a fluid inch switch. The app is one browser WASM build (C++ and OpenCASCADE, WebGL2, hosted on GitHub Pages) for desktop and mobile (Erik, 2026-10-21). The older Qt `solid_view` window is a native test harness only. Export requires the units (mm) check. The OCCT shape-validity check runs after operations and logs failures, but it does not block Export. Watertight checks were dropped (Erik, 2026-10-22).

Licensed under the GNU Lesser General Public License v2.1. See [LICENSE](LICENSE).

## Folder layout
- `src/` - application source code
- `docs/` - project documentation and specs
- `mvp/` - MVP scope, milestones, and acceptance criteria
- `research/` - research notes and references
- `prompts/` - AI prompts used in development
- `tests/` - automated tests
- `builds/` - build output and exports (git-ignored)
- `tools/` - helper scripts and utilities
- `.grok/skills/` - Grok agent skills

## Remote
- https://github.com/cyborgpencil/cad-mvp
- Optional: periodic `git bundle` to another drive, pending Erik's choice of drive and schedule.
