# Prompt: restyle the GUI in the MODO style

Status: READY for Pilot (Doc Steward, 2026-10-21). Erik's direction (2:05 AM MT): visuals come first; the GUI should look like MODO 3D with its teal overall tone. Reference: [What is Modo](https://learn.foundry.com/modo/content/help/pages/getting_started/what_is_modo.html).

## Scope
- Visual restyle only: colors, typography, panel chrome, icons and spacing. Keep the approved layout, tabs, tools and gates from `mvp/ui-redesign.md`.
- Exact palette hex values are TBD. Sample them from the reference or Research Digest's MODO notes, put them in CSS custom properties in one place (for example `--accent-teal`), and list them in `mockup/PROGRESS.md`. Don't copy MODO icons or other assets; use our own or open-licensed icons.
- Must keep: units always visible, watertight PASS/FAIL readable (contrast at least WCAG AA 4.5:1 for text), touch targets at least 44×44, and the desktop, phone portrait and phone landscape layouts.

## Checkpoints
1. Plan the palette and tokens, then stop.
2. Apply them to the web app (``web/`` if it exists, else the mockup), then run CTest.
3. Screenshots: desktop 1440×900, phone 390×844 portrait, 844×390 landscape. Re-check T1/T2 and R1–R5.

## Cap
30 minutes. Edit files in place, use incremental commits, and leave no versioned copies.