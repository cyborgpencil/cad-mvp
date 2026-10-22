# Cursor and tooling for the CAD/CAM MVP

_Research digest, 2026-10-22. Sources are linked inline. Anything I couldn't confirm from an official doc or repo is marked **not verified**._

## 1. What Cursor does well here, compared with Grok Build

**Cloud agents (formerly Background Agents).** Each one runs in an isolated cloud VM with the repo, dependencies, secrets and network access. You can run "as many agents as you want in parallel", they don't need your machine to be online, they can build and test their own changes and drive a browser or desktop, and they open PRs ([Cursor docs](https://cursor.com/docs/cloud-agent)). Automations can start them on a schedule or from GitHub events ([Cursor help](https://cursor.com/help/ai-features/cloud-agents)).
- **Cost:** they draw on plan usage at the selected model's rate, with no separate VM charge ([Cursor forum, staff answer](https://forum.cursor.com/t/what-is-the-pricing-structure-for-using-cloud-agents/156843)). They need an eligible paid plan (Premium and up on the X Subscription) ([Cursor help](https://cursor.com/help/ai-features/cloud-agents)).
- **Grok Build:** it runs locally (TUI, headless `grok -p`, or ACP) ([xAI docs](https://docs.x.ai/build/overview)). Its parallel work comes from subagents, each with its own context, optionally in isolated git worktrees (`grok -w`, `isolation: worktree`) ([worktrees](https://docs.x.ai/build/features/worktrees), [subagents](https://github.com/xai-org/grok-build/blob/main/crates/codegen/xai-grok-pager/docs/user-guide/16-subagents.md)). A hosted cloud-VM agent equivalent: **not verified**.
- **For us:** cloud agents fit long, self-contained PRs (assemblies is already running this way). Grok Build fits local Z13 runs that need the WASM build and the Orca toolchain.

**Bugbot (PR review).** It reviews every PR and supports rules and effort levels (Low, Default, High, Smart). Autofix runs on Cloud Agent credits ([Bugbot docs](https://cursor.com/docs/bugbot)).
- **Cost:** usage-based billing, averaging $1.00–$1.50 per review. On individual plans it uses included usage first ([Cursor help](https://cursor.com/help/account-and-billing/bugbot-usage-based-billing)).
- **Grok Build:** lists "Code review: line-by-line feedback before opening a PR" ([x.ai/build](https://x.ai/build)). That is local review before a PR exists. An automatic GitHub PR-review bot: **not verified**.

**Rules and skills.** Rules are `.cursor/rules/*.mdc` files controlled by `alwaysApply`, `description` or `globs` ([Rules](https://cursor.com/docs/rules)). Skills are `SKILL.md` folders in `.cursor/skills/` or `.agents/skills/` ([Skills](https://cursor.com/docs/skills)).
- **Grok Build:** has Skills, Hooks, per-directory AGENTS.md and Memory ([x.ai/build](https://x.ai/build)), so it's roughly at parity. Our repo already uses AGENTS.md and `.grok/skills`.

**MCP support.** Cloud agents support MCP servers ([Cursor docs](https://cursor.com/docs/cloud-agent)).
- **Grok Build:** `grok mcp add` supports stdio or HTTP servers, with project scope in `.grok/config.toml`. It also reads `.cursor/mcp.json` and `.mcp.json` ([xAI MCP docs](https://docs.x.ai/build/features/mcp-servers)), so one project MCP config can serve both tools. Subagents inherit the parent's MCP servers ([subagents](https://github.com/xai-org/grok-build/blob/main/crates/codegen/xai-grok-pager/docs/user-guide/16-subagents.md)).

**Pricing and open source for Grok Build.** The harness is Apache-2.0 according to the [grok-build LICENSE](https://github.com/grok-build/grok-build/blob/main/LICENSE). That repo path differs from xai-org, so whether it's official is **not verified**. A "Plus $8/month" figure comes only from a third-party site ([grokmag](https://grokmag.com/grok-build/)), so it's **not verified**.

## 2. Connectors, MCP servers and tools to add

| Tool | Benefit for us | Cost | Open source (license) | Setup |
|---|---|---|---|---|
| GitHub Actions CI | Runs the tests (shape validity, units, size) on every PR | Standard runners are free on public repos; private repos use included minutes, then overage ([GitHub docs](https://docs.github.com/en/actions/how-tos/write-workflows/choose-where-workflows-run/choose-the-runner-for-a-job#standard-github-hosted-runners-for-public-repositories), [billing](https://docs.github.com/billing/managing-billing-for-github-actions/about-billing-for-github-actions)). Whether cad-mvp is public: **not verified** | Service, not OSS | Low to medium: one workflow YAML; an emsdk/OCCT WASM build in CI is more work |
| GitHub MCP server | Agents read PRs, issues and CI status | Free; uses a PAT ([install guide](https://github.com/github/github-mcp-server/blob/main/docs/installation-guides/install-cursor.md)) | Yes, MIT ([repo](https://github.com/github/github-mcp-server)) | Low |
| Playwright MCP | Drives the browser app for agent-run acceptance tests A and B; screenshots of the canvas | Free | Yes, Apache-2.0 ([repo](https://github.com/microsoft/playwright-mcp/)) | Low: `npx @playwright/mcp@latest` ([repo](https://github.com/microsoft/playwright-mcp/)) |
| Playwright screenshots (also covers screenshot capture) | `browser_take_screenshot` captures viewport, element or full page as PNG/JPEG/WebP to a file ([docs](https://playwright.dev/mcp/tools/screenshots)); the docs recommend screenshots for canvas content | Free | Yes, Apache-2.0 | Low. Capturing the Orca desktop window itself: no sourced MCP tool, **not verified** |
| lib3mf (3MF Consortium) | Official C++ read, write and validation of 3MF; could sit in our C++ core | Free | Yes, BSD-2-Clause ([repo](https://github.com/3mfconsortium/lib3mf)) | Medium: C++ dependency, and WASM build feasibility is **not verified** |
| 3MF Consortium online/standalone validator | Spec-conformance check | **not verified** (I found no official source) | **not verified** | **not verified** |
| trimesh (Python) | Test-side STL/3MF checks: `is_watertight`, bounds and volume for size checks, plus repair helpers ([docs](https://trimesh.org/trimesh.html), [repair](https://trimesh.org/trimesh.repair.html)) | Free | Yes, MIT ([license](https://github.com/mikedh/trimesh/blob/main/LICENSE.md)) | Low: `pip install` in CI |
| admesh | CLI STL check and repair | Free | Yes, GPL-2 ([COPYING](https://github.com/admesh/admesh/blob/docs/COPYING)), so keep it as an external test tool and don't link it into the app | Low |
| OrcaSlicer CLI | Headless slicing in CI or on Z13: `--slice 0`, `--export-3mf`, `--export-statistics` (per-plate time and filament as JSON), `--outputdir` ([CLI actions](https://www.orcaslicer.com/wiki/cli/cli_actions), [misc](https://www.orcaslicer.com/wiki/cli/cli_misc)). Proves our exports slice | Free | Yes, AGPL-3.0 ([repo](https://github.com/OrcaSlicer/orcaslicer)) | Medium: profile JSONs must be supplied with `--load-settings` and `--load-filaments` ([CLI mode](https://www.orcaslicer.com/wiki/cli/cli_mode)) |

**Units (mm) check for validators.** In 3MF, `<model unit>` defaults to millimeter, and micron, centimeter, inch, foot and meter are also allowed ([3MF Core spec](https://github.com/3MFConsortium/spec_core/blob/master/3MF%20Core%20Specification.md)). Validators should assert `unit="millimeter"` explicitly rather than rely on the default. STL stores no units at all (STL as "triangle soup": [trimesh formats](https://trimesh.org/formats.html)). So STL checks have to confirm size instead: the bounds of the default 20 mm cube must equal 20 x 20 x 20 within tolerance.

## 3. Google AI Ultra: Antigravity and Gemini CLI for this repo

**Coverage.** Google AI Ultra (consumer plan) covers Google Antigravity, which includes the app, `agy` CLI, IDE and SDK. Ultra gets "the highest usage limits" and priority access to new models ([Google One Help](https://support.google.com/googleone/answer/16286513?hl=en)). Third-party models are also included ([Antigravity Plans](https://antigravity.google/docs/plans/)). For Gemini CLI, the notice reads: "Unpaid tier and Google One users: Gemini CLI was replaced by Antigravity CLI on June 18th, 2026". The CLI is also "not optimized for Gemini 4 Argon" ([gemini-cli repo](https://github.com/google-gemini/gemini-cli), [geminicli.com](https://geminicli.com/docs/resources/quota-and-pricing/)). For a Google One Ultra account, the practical path is therefore Antigravity CLI rather than Gemini CLI. Whether Gemini CLI still works at all with a Google One Ultra login: **not verified**.

**Limits.**
- **Antigravity.** Google publishes relative limits, not absolute ones:
  - Free: a weekly quota.
  - Pro: a quota refreshed every 5 hours, with a weekly cap.
  - Ultra: the highest quota, refreshed every 5 hours, plus the highest weekly limits ([Plans](https://antigravity.google/docs/plans/)).
  - Ultra $100/mo is 5x the tokens of Pro $20/mo, and Ultra $200/mo is 20x. Gemini models share one pool, and non-Gemini models have a separate fixed limit ([Antigravity blog, 2026-05-19](https://antigravity.google/blog/changes-to-antigravity-plans/)).
  - Overages are billed through purchased AI credits ([Plans](https://antigravity.google/docs/plans/)).
  - Absolute token or prompt counts: **not verified** (not published; "subject to modification").
- **Gemini CLI.** The quota table lists requests per user per day: Code Assist Individual 1,000, AI Pro 1,500, AI Ultra 2,000, and API-key free tier 250 ([geminicli.com quotas](https://geminicli.com/docs/resources/quota-and-pricing/)). The same page carries the replacement notice above, so whether these numbers still apply to Google One accounts is **not verified**.

**Windows (relevant to Z13).**
- **Antigravity:** the app needs Windows 10 64-bit or later, on x64 or ARM64 ([download](https://antigravity.google/download/)). The CLI installs with `irm https://antigravity.google/cli/install.ps1 | iex` ([getting started](https://antigravity.google/docs/getting-started/)).
- **Gemini CLI:** needs Windows 11 24H2+ and Node.js 20+ ([installation](https://geminicli.com/docs/get-started/installation/)).

**GitHub PR integration.**
- **Gemini Code Assist on GitHub** is a GitHub app. It auto-summarizes and reviews PRs, responds to `/gemini` comments, and supports a style guide in `.gemini/styleguide.md`. The consumer version is limited to 33 PRs/day, and it skips `.github/workflows` files ([Google for Developers](https://developers.google.com/gemini-code-assist/docs/review-repo-code), [Google blog](https://blog.google/innovation-and-ai/technology/developers-tools/gemini-code-assist-free/)). Google's blog calls it free. Whether that is still current: **not verified**.
- **`google-github-actions/run-gemini-cli`** runs PR review (auto, or `@gemini-cli /review`) and issue triage. It authenticates with a `GEMINI_API_KEY` secret, Vertex or Code Assist ([repo](https://github.com/google-github-actions/run-gemini-cli/)).
  - Whether it accepts a Google One Ultra login: **not verified**.
  - The license: **not verified**.
  - It depends on Gemini CLI, so the replacement notice above may affect it: **not verified**.
- **Antigravity PR integration:** I found no official GitHub PR-review integration, so it's **not verified**.

**For us.** Ultra is worth considering for Antigravity on Z13 as a third agent alongside Grok Build and Cursor. The consumer Code Assist GitHub app is the lowest-effort way to get a second PR reviewer, at 33 PRs/day. Neither one replaces the units/size checks in CI.

## Recommended top 3
1. **Playwright MCP.** It's free, Apache-2.0 and low-setup. It covers browser testing for acceptance A and B and screenshot capture, and it works in Cursor and in Grok Build, which reads `.cursor/mcp.json`.
2. **GitHub Actions running a trimesh-based (MIT) export check.** It runs validity, units/size and bounds checks on every PR. The units check is required, and it should also assert `unit="millimeter"` in 3MF.
3. **OrcaSlicer CLI.** It gives us a headless slice of the exported STL/3MF, with `--export-statistics` JSON as proof that the file prints. Note that Orca is AGPL-3.0, so use it as an external tool only.

Bugbot is worth a trial on a few PRs, at about $1–1.50 each ([source](https://cursor.com/help/account-and-billing/bugbot-usage-based-billing)), but it isn't in the top 3 because it costs money for each review.

## Settled TBDs for prompts/tooling-top3.md (Research Digest, 2026-10-22)
- **Playwright MCP config location: `.cursor/mcp.json`** at the repo root. Cursor documents `.cursor/mcp.json` as the project-level MCP file (global is `~/.cursor/mcp.json`) ([Cursor MCP docs](https://cursor.com/docs/context/mcp)), and section 2 above notes Grok Build reads it too, so one file serves both. Contents: the README's standard config, `{"mcpServers":{"playwright":{"command":"npx","args":["@playwright/mcp@latest"]}}}` ([playwright-mcp README](https://github.com/microsoft/playwright-mcp)). Neither `.mcp.json` nor `.cursor/mcp.json` exists on main `03cd6ea` yet.
- **trimesh script: `tools/check_export.py`**, pinned `trimesh==5.1.1` (latest on [PyPI](https://pypi.org/project/trimesh/), needs Python 3.10+; checked 2026-10-22). It loads each exported STL/3MF, asserts bounds and volume in mm (default 20 mm cube: bounds 20 mm per axis, volume 8000 mm3), asserts `unit="millimeter"` in 3MF, and refuses an empty mesh. Per the 02:17 rule it does not assert `is_watertight`; it may print it as information.
- **CI placement:** a new step at the end of the existing `build` job in `.github/workflows/ci.yml`, after "Native CTest", because that job already has Python 3 and produces the build outputs; no new job or workflow. Repo Keeper to confirm.
