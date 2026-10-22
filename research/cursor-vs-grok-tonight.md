# Cursor cloud agents vs Grok Build: overnight 2026-10-21/22

Sources: UPDATES.md (lines 236-260), web/PROGRESS.md (02:17-06:06 MT entries), git log since 2026-10-21 17:00 MT, and figures posted in the team room tonight (marked "room"; reported, not independently verified).

## Grok Build (local on Z13)
| Session | What | Cost | Notes |
|---|---|---|---|
| UI session 1 | one-row tool menu etc. (ca5a38f) | $3.17 | UPDATES 02:22 |
| fix pass | session 2 | $2.31 | UPDATES 02:22 |
| 01a1629d | phone fix (d8d04df) | $3.149 | ~38 min work; watchdog stopped after DONE marker (room) |
| 01a162cd | WebKit blank-view fix (d8d04df) | $3.058 | watchdog stopped (room) |
| 417dfb52 | gizmo + undo batch (fbd0947) | $6.61 | exited cleanly 05:51 (room) |
| **Total** | 5 runs | **~$18.30** | unit 1e10 ticks/$, confirmed (UPDATES 06:05) |

Failures/rework: post-DONE "hang" - background tasks it started kept re-triggering turns; out.json only written on exit; early watchdog kills left two costs provisional until 06:05 (UPDATES 03:40). Launcher fixed (turn_completed + idle then taskkill /T).

## Cursor cloud agents
- PR #1 nav cube: +717/-32, 5 files, no C++; CI green first try; needed 3 overrides mid-run because the prompt file had stale lines; then a rebase onto fbd0947 (UPDATES 04:33/04:49; room).
- PR #2 save/load: CI green; deviated from prompt - libcascade 3.1.0 exports only file-path BRepTools::Write/Read, so a temp file in the Emscripten FS replaces streams (b2f43b1, flagged for Erik) (PROGRESS 05:25).
- Resize and delete agents launched 07:03 MT (room); no result yet.
- Cost: **unknown** - no repo file states Cursor spend.

## Comparison
| | Grok Build | Cursor cloud |
|---|---|---|
| Cost | ~$18.30 for 5 runs (avg ~$3.66) | unknown |
| Runs tonight | 5 (all landed) | 2 PRs green + 2 in flight |
| Rework | process hang/watchdog; no code rework logged | 3 mid-run overrides (stale prompt); 1 spec deviation; rebases |
| Strengths | local Z13 builds, WebKit/Playwright phone harness, deep root-cause debugging (gizmo translateBody) | parallel isolated PRs, CI-gated, no Z13 file conflicts |
| Weak spots | one job at a time on Z13; blocks PR landing while editing | can't run Z13-only checks (WebKit screenshots); cost not visible |

## Lessons
- Make prompt files authoritative before launch (PR #1 needed 3 overrides).
- Fix landing order up front; tonight's order changed 3 times (PROGRESS 04:50, 05:16 x2) before settling: Z13 batch first, then PRs rebased.
- Watchdog: stop on DONE + idle, kill process tree, and read cost via grok usage.

## Recommendation
- Keep Grok Build first for Z13-bound, debugging-heavy or kernel/WASM work (tooling priority).
- Use Cursor second for self-contained, CI-testable features that can run in parallel while Z13 is busy.
- Cheaper-path rule cannot be applied yet: get Cursor's per-agent cost (dashboard, Erik) before choosing on price.
- One Z13 writer at a time; Cursor PRs rebase after it lands.