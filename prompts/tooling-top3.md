# Tooling top 3: launch prompts for Grok Build Pilot

Status: READY, queued (Doc Steward, 2026-10-22). Runs only after Acceptance A and B (mvp/acceptance-a-b.md) are done. Implementer: Grok Build Pilot on Z13. Repo Keeper merges each item as its own PR after CI is green and the diff scan is clean.
Source: built only from research/cursor-and-tooling.md ("Recommended top 3" and section 2). Anything that digest does not verify is marked TBD.

Shared checks for all three:
- Units check required: 3MF must assert `unit="millimeter"` explicitly; STL has no units, so confirm size by bounds (default 20 mm cube = 20 x 20 x 20 within tolerance).
- No watertight gate (Erik, 2026-10-22 02:17 MT). The OCCT shape-validity check after ops is unchanged and does not block Export.
- No printer send. Nothing goes to a printer, ever, from these tools.
- Docs and test tooling only around the app; no geometry kernel changes.

## 1. Playwright MCP
Goal: let agents drive the browser app for acceptance tests A and B and capture canvas screenshots.
Scope: add a project MCP config for Playwright MCP (Apache-2.0, `npx @playwright/mcp@latest`). Per the digest, Grok Build reads `.cursor/mcp.json` and `.mcp.json`, so one config can serve Grok Build and Cursor. Out of scope: capturing the OrcaSlicer desktop window (no sourced MCP tool; TBD).
Steps:
1. Research first: re-read the digest links (github.com/microsoft/playwright-mcp, playwright.dev/mcp/tools/screenshots) and post a short plan.
2. Add the project MCP config (file location: `.mcp.json` vs `.cursor/mcp.json` = TBD, pick one and say why).
3. Use `browser_take_screenshot` on the Pages build at desktop and 390x844 portrait; save PNGs to `builds\screenshots\<ID>-<step>.png`.
4. Drive one acceptance flow end to end and record the steps.
Checks: units readout shows mm; exported file passes the units check; screenshots saved; deploy_smoke still passes.
Report back: config file path and contents, Playwright MCP version used, screenshot paths, any tool that failed, PR link.

## 2. trimesh PR check (GitHub Actions)
Goal: a test-side export check on every PR (MIT, `pip install` in CI).
Scope: a Python check run by CI on exported STL/3MF: bounds and volume for size, plus an explicit `unit="millimeter"` assertion on 3MF. Do not use `is_watertight` as a gate (watertight dropped). Repair helpers: out of scope.
Steps:
1. Research first: trimesh docs (trimesh.org/trimesh.html) and the existing ci.yml; post a plan.
2. Add the script under `tools/` (name TBD) and a step in the existing CI workflow (job placement TBD, Repo Keeper to confirm).
3. Run it against current export fixtures (default 20 mm cube; others TBD).
4. trimesh version pin: TBD.
Checks: units assertion present and failing on a non-mm file; bounds within the matrix tolerance; CI green; no printer send.
Report back: script path, CI run link, fixtures checked with bounds/volume values, trimesh version, PR link.

## 3. OrcaSlicer CLI headless slice
Goal: prove exports slice, using `--slice 0`, `--export-3mf`, `--export-statistics` (per-plate time and filament JSON), `--outputdir`.
Scope: external tool only (AGPL-3.0; never linked into the app). Profiles must be passed with `--load-settings` and `--load-filaments`. Run on Z13 first; CI use = TBD.
Steps:
1. Research first: orcaslicer.com/wiki/cli (cli_actions, cli_misc, cli_mode); post a plan.
2. Locate the installed Orca CLI on Z13 (path TBD) and the profile JSONs matching the acceptance profiles (Ermo X1C, Bambu 0.20 mm Standard, Bambu PLA Basic, stock TPU 95A; export paths TBD).
3. Slice the acceptance exports into `builds\orca\` with `--export-statistics`.
4. Add a wrapper script under `tools/` (name TBD).
Checks: units check on the input files; sliced size matches within 0.05 mm per axis; statistics JSON written; no printer send and no network printer settings.
Report back: exact command lines, Orca version, profile files used, statistics JSON paths with time and filament, any errors, PR link.