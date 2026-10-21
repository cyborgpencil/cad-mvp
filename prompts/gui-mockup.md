# Prompt: clickable GUI mockup (Grok Build)

Working dir: C:\Dev\cadcam-mvp\mockup\ on Z13. Write nothing outside mockup\.
Goal: a clickable layout mockup that follows the final decisions in mvp/ui-redesign.md ("Team decisions (final)"), so Erik can give quick feedback. No real geometry and no OCCT. Replace mockup\index.html in place, with no versioned copies.
Only run this after Erik approves the design.

## Must have
- Top bar: File, Undo/Redo, the four tabs Sketch, Model, Repair and Export, and an mm/in toggle that only changes the labels.
- Sketch is a mode. "New Sketch" on the Model tab switches to the Sketch tab, and a "Finish Sketch" bar returns you to Model. Sketch tools: Line, Rectangle, Circle, Arc, Polygon, Sketch Fillet, Trim, Offset, Dimension, plus the constraints Coincident, Horizontal, Vertical, Parallel, Perpendicular, Equal, Tangent and Fixed.
- Model tools: Extrude (Push/Pull), Inset, Bevel (Fillet/Chamfer), Loop Cut, Knife, Grab, Rotate, Scale, Snapping.
- Repair tab: Check shape, Find open edges, Auto-heal and Mesh repair (toast only). Add nothing else.
- Export tab: a watertight and units check panel showing PASS/FAIL (fake), then the one Export button with STL and 3MF choices. The button stays disabled while the check shows FAIL. There's no other export path.
- Shared on every tab: a browser tree on the left (Bodies, Sketches, Construction planes), an inspector on the right, one floating view bar (Select modes Vertex/Edge/Face/Body, Measure, Section, display modes, Orbit/Pan/Zoom/Fit, view presets, Isolate/Hide), the ViewCube top right, and a status bar showing units, watertight PASS/FAIL and volume (fake values).
- Not included: the history timeline and the radial menu.
- Keys: 1 to 4 switch tabs only when no text field has focus, and X opens a tool search box. Do not use Ctrl+K, Ctrl+1 to 8, Ctrl+Tab, Ctrl+PgUp/PgDn or Alt+letter.
- Style: dark neutral (the earlier Slate theme) with one accent color, and touch targets of at least 44 px.
- Phones: the tabs move to a bottom bar, the tree and inspector become drawers, and tool search sits in the tools menu.
- 3D view: a three.js placeholder cube with orbit. Clicking ViewCube faces snaps the camera.

## Rules
- Every fake button shows a toast naming the tool.
- No CDN: inline a pinned minified three.js (r160) into one <script type="module"> in index.html, keeping its MIT license comment. Chrome blocks separate module files opened from disk (file://). No node_modules.
- Chrome on Windows, Android and iPhone. Pointer Events with touch-action: none on the 3D view.
- No network calls and no build step.

## Checkpoints (save partial work)
1. First write a working index.html with the layout shell (top bar, tabs, tree, inspector, view bar, status bar) and the inlined three.js cube. Save it before anything else.
2. Then add one tab's tools at a time (Sketch, Model, Repair, Export), saving index.html after each so it always opens.
3. After each save, append one line to mockup\PROGRESS.md naming what is done.
If the run stops early, the last saved index.html must still open in Chrome.

## Done when
- mockup\index.html opens by double-click in Chrome.
- Do not take screenshots. Grok Build Pilot captures them afterward with headless Edge at 1440x900 and 390x844, saved as builds\screenshots\mockup-desktop.png and builds\screenshots\mockup-phone.png.
- Report the files created and their sizes.

The mockup exports nothing real, so the real watertight and units check does not run. The fake check panel on the Export tab must still be shown, because the gate is a must-have in the design.