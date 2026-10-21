# Mockup progress

2026-10-21 — Checkpoint 1: layout shell saved (top bar with File, Undo/Redo, Sketch/Model/Repair/Export tabs, mm/in toggle; browser tree; inspector; floating view bar; ViewCube; status bar with units, watertight FAIL, volume). Inlined three.js r160 cube with orbit. Next: Sketch tools.
2026-10-21 — Checkpoint 2: Sketch tools added (Line, Rectangle, Circle, Arc, Polygon, Sketch Fillet, Trim, Offset, Dimension, and constraints Coincident through Fixed). Finish Sketch bar returns to Model. Next: Model tools.
2026-10-21 — Checkpoint 3: Model tools added (New Sketch, Extrude/Push-Pull, Inset, Fillet, Loop Cut, Knife, Grab, Rotate, Scale, Union, Cut, Snapping). Chamfer omitted. Next: Repair tools.
2026-10-21 — Checkpoint 4: Repair tools added (Check shape, Find open edges, Auto-heal, Mesh repair). FixGaps / small-gaps omitted. Next: Export gate.
2026-10-21 — Checkpoint 5: Export gate panel with fake watertight/units PASS/FAIL, one Export button (STL/3MF) disabled on FAIL. Keyboard 1–4 and X, phone bottom tabs and drawers. Mockup opens from disk.
2026-10-21 — Phone layout (<=820px): Info/Inspector stays fully visible at 390px and at least 44x44. Part1 truncates with text-overflow ellipsis; the full name is the title attribute and shows on tap.

## Palette placeholders (web/index.html :root, 2026-10-21)

TBD. Not sampled from a Foundry screenshot. `research/gui/modo-tools.md` records that Foundry publishes no Modo UI hex and shows orange highlights. Erik asked for a teal tone, so these are stand-in values until he names a Modo version or a screenshot. No Modo icons, logos, or screenshots are in the app. One accent variable: `--accent`.

| Token | Value | Role |
|---|---|---|
| --bg | #0e2429 | page background |
| --top | #10262b | top bar and phone tabs |
| --panel | #123038 | side panels |
| --panel-2 | #163840 | menus, drawers |
| --ribbon | #14343c | toolbox tools |
| --field | #0e2429 | inputs, unit switch |
| --status | #10262b | status bar |
| --finish | #123830 | Finish Sketch bar |
| --ink | #f4fbfb | primary text |
| --muted | #d5e4e2 | secondary text |
| --tab-ink | #d5e4e2 | inactive tab text (light gray) |
| --tab-bg | #1a3036 | inactive tab fill (darker gray) |
| --tab-track | #0e2429 | tab strip |
| --tab-active | #1b454c | active tab fill |
| --line | rgba(244, 251, 251, 0.14) | hairline |
| --line-strong | #0a181c | panel borders |
| --accent | #14756e | the only accent |
| --accent-dim | color-mix(in srgb, var(--accent) 32%, transparent) | active tool wash |
| --measure | #fff8e8 | dimension stroke |
| --pass | #c8f5df | PASS text |
| --pass-bg | #0e3d2c | PASS badge |
| --fail | #ffd0d0 | FAIL text and gate reason |
| --fail-bg | #3f1518 | FAIL badge |
| --banner-bg | #12343a | interim banner |
| --banner-ink | #f4fbfb | interim banner text |
| --disabled-bg | #2a454a | disabled Export |
| --disabled-ink | #d5e4e2 | disabled Export label |

Checked pairs are at least WCAG AA 4.5:1 for text. White on `--accent` (#14756e) is about 5.53:1. PASS and FAIL badges are about 10:1. Handle colors in the view (not UI text): X #e15b4a, Y #3cba6a, Z #4c8dff. Those are placeholders too.
