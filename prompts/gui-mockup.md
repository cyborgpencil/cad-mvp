# Prompt: clickable GUI mockup (Grok Build)

Working dir: C:\Dev\cadcam-mvp\mockup\ on Z13. Write nothing outside mockup\ except the two screenshots.
Goal: a clickable layout mockup so Erik can give quick feedback. No real geometry and no OCCT.

## Must have
- Fusion-style layout: ribbon/toolbar (Sketch, Solid, Inspect, Export tabs), browser tree on the left, inspector/properties panel on the right, a timeline strip at the bottom (visual only), and a ViewCube in the top-right of the 3D view.
- Blender-style tool set in the ribbon: extrude (push/pull), inset, bevel (fillet/chamfer), loop cut, knife, grab/rotate/scale, snapping toggle, and selection modes (vertex, edge, face, body).
- Exploring: orbit/pan/zoom, view presets, section, measure, display modes, isolate/hide, undo/redo buttons.
- Export panel with STL and 3MF buttons (toast only).
- An mm/inch toggle that only changes the labels.
- 3D view: a three.js placeholder cube with orbit. Clicking ViewCube faces snaps the camera.

## Rules
- Every fake button shows a toast naming the tool.
- No CDN: inline a pinned minified three.js into one <script type="module"> in index.html, keeping its MIT license comment. Chrome blocks separate module files opened from disk (file://). No node_modules.
- Chrome on Windows, Android and iPhone. Pointer Events with touch-action: none on the 3D view. On narrow screens the ribbon collapses, and the tree and inspector become slide-out drawers.
- No network calls and no build step.

## Done when
- mockup\index.html opens by double-click in Chrome.
- Screenshots at desktop width (1440x900) and phone width (390x844) are saved as builds\screenshots\mockup-desktop.png and builds\screenshots\mockup-phone.png.
- Report the files created and their sizes.

The watertight and units gate does not apply, because this mockup exports nothing real. Scope questions C1-C9 in mvp/gui-plan.md are deferred: show the tools, decide nothing.