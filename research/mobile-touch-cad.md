# Mobile touch patterns for the browser CAD viewport (2026-10-21)

Scope: WASM + OpenCASCADE app, Three.js-style viewport, portrait phone. Every figure has a source; anything else is marked **team proposal**.

## 1. Gizmo / handle hit sizes
- WCAG 2.5.8 (AA): targets at least **24x24 CSS px**, or 24 px spacing circles. https://www.w3.org/WAI/WCAG22/Understanding/target-size-minimum
- WCAG 2.5.5 (AAA): **44x44 CSS px**. https://www.w3.org/WAI/WCAG21/Understanding/target-size.html
- Apple HIG: **44x44 pt**. https://developer.apple.com/design/human-interface-guidelines/accessibility
- Material: **48x48 dp**. https://m3.material.io/foundations/designing/structure
- three.js TransformControls: `size` (default **1**) scales the helper UI; `translationSnap`/`rotationSnap`/`scaleSnap` default null; one class handles mouse and touch. https://threejs.org/docs/pages/TransformControls.html
- Onshape/Shapr3D mobile docs: no published hit-size figures found. Gap.
- **Team proposal:** handle pick zones of 44 CSS px or more (invisible pick meshes larger than the drawn handle); raise `size` on `(pointer: coarse)`.

## 2. Tap vs drag picking
- Android touch slop fallback: **8 dp** ("distance a touch can wander before we think the user is scrolling"); paging slop = 2x. https://android.googlesource.com/platform/frameworks/base/+/refs/heads/main/core/java/android/view/ViewConfiguration.java
- Android long-press default: **400 ms** (same file).
- Pointer Events: one event model for mouse, pen and touch; `touch-action: none` on the canvas stops the browser from panning or zooming. https://www.w3.org/TR/pointerevents3/ , https://developer.mozilla.org/en-US/docs/Web/CSS/touch-action
- `(pointer: coarse)` detects finger input. https://developer.mozilla.org/en-US/docs/Web/CSS/@media/pointer
- **Team proposal:** a movement of 8 CSS px or less is a tap (pick), more than that is a drag (orbit/gizmo); touch edge pick radius about 20 px (mouse stays 8 px). When an edge and a face both hit, the edge wins inside the radius, with a "Face / Edge" filter chip and a tap again to cycle candidates.

## 3. Number entry on phones
- `inputmode="decimal"` shows a numeric keypad with a decimal separator. https://developer.mozilla.org/en-US/docs/Web/HTML/Global_attributes/inputmode
- `type=number` pitfalls: invalid text yields an empty `value`, and the wheel or arrow keys change the value. MDN recommends `inputmode` + `pattern` for many cases. https://developer.mozilla.org/en-US/docs/Web/HTML/Element/input/number
- **Team proposal:** `type="text" inputmode="decimal"`, parse with a `,` or `.` separator, a fixed "mm" suffix label (units locked), 44 px or larger -/+ steppers (step TBD, ask Erik), commit on blur or Enter, then re-run the gate.

## Next steps (Grok Build, step 2: transforms gizmo)
1. Add `touch-action: none` to the viewport canvas; route all input through Pointer Events.
2. Add an 8 px tap/drag classifier; count only taps as picks.
3. Detect `(pointer: coarse)`; scale TransformControls `size` and the pick zones to 44 px or more.
4. Use one-axis-at-a-time handles plus a Move / Rotate / Scale segmented control (44 px buttons).
5. Add a numeric panel (`inputmode=decimal`, mm suffix) that stays in sync with the gizmo and writes back to the parametric feature.
6. Snaps: translation in mm, rotation in degrees. Values TBD; ask Erik.
7. After every transform commit: OCCT rebuild, watertight + mm gate, then a CTest and a portrait-viewport smoke tap test.