# GUI usability checks (pass/fail)

Research Digest, 2026-10-21. Test prep only, no app code. These checks verify the built GUI against `mvp/ui-redesign.md` "Team decisions (final)" (D1-D10), `prompts/gui-mockup.md` and `research/gui/ui-layout-review.md` (R). Mark each check PASS or FAIL and note the browser, OS and device.

## 1. Touch targets
Thresholds: WCAG 2.2 SC 2.5.8 (AA) sets at least 24x24 CSS px, with exceptions for spacing, equivalent controls, inline targets, user-agent controls and essential cases [1]. SC 2.5.5 (AAA) sets at least 44x44 CSS px [2]. Apple's HIG gives a hit region of at least 44x44 pt [3]. Material gives at least 48x48 dp [4]. **Our rule is 44 px minimum (D9).** 48 dp is noted only for reference.
Measuring: in Chrome DevTools, open the device toolbar, choose Responsive and enter 390 x 844, with Device type Mobile so touch events fire [5]. Inspect each control and read its width and height in Elements > Computed (box model), or run `getBoundingClientRect()` in the Console.
- **T1:** At 390x844, measure every tab, toolbar button, view-bar button, drawer handle, ViewCube face, mm/in toggle and the Export button. Expected: each is at least 44 x 44 CSS px. Source: D9 [2].
- **T2:** At 1440x900, measure the same controls. Expected: at least 44 px (D9 applies everywhere). Anything under 44 but at least 24 is noted as a fail of the team rule, not of WCAG AA. Source: D9 [1][2].
- **T3:** Any visual icon smaller than 44 px. Expected: its hit area (padding included) is still at least 44 x 44, and neighboring hit areas don't overlap. Source: [1][4].
- **T4:** Tap each control on a real Android phone (Chrome) and an iPhone (Safari). Expected: no accidental neighbor activation in 10 taps per control. Device mode is only an approximation [5].

## 2. Shortcuts (1-4 tabs, X search)
Chrome on Windows/Linux reserves Ctrl+Tab, Ctrl+Shift+Tab, Ctrl+PgUp/PgDn, Ctrl+1..8, Ctrl+9, Ctrl+K/Ctrl+E, Alt+F/Alt+E (Chrome menu) and Alt+Left/Right. On Mac it reserves Cmd+1..9 and Cmd+Opt+Left/Right. Plain digits and plain X are not on the list [6].
- **K1 (Chrome, Windows desktop):** Click the 3D view, then press 1, 2, 3, 4. Expected: the tab switches to Sketch, Model, Repair and Export in turn. Source: D10.
- **K2:** Press X. Expected: the tool search box opens with focus. Typing finds a tool; Esc closes it. Source: D10, R.
- **K3:** Focus a text input (search box, Part1 rename, dimension field), then press 1-4 and X. Expected: the characters go into the field, with no tab switch and no search popup. Repeat inside any contenteditable element. Source: D10.
- **K4:** Press Ctrl+1, Ctrl+Tab, Ctrl+PgDn and Alt+F. Expected: Chrome handles them (browser tab or menu), and the app neither blocks them nor reacts to them. Source: [6].
- **K5 (Android Chrome, no keyboard):** Expected: the tab bar and the search button in the tools menu reach every tab and tool. Source: D10, R.
- **K6 (Android Chrome + hardware keyboard):** Repeat K1-K3. Status: untested; no official source checked for Android web key events.
- **K7 (iPhone Safari, no keyboard):** Same as K5.
- **K8 (iPhone/iPad Safari + hardware keyboard):** Repeat K1-K3. Status: **untested**. Apple documents system shortcuts for external keyboards on iPad [7] but not web-page key events. No official source verified that plain keys reach a web page, so the touch fallback is required.

## 3. Export gate
- **E1:** Load a model whose check shows FAIL. Expected: the one Export button (STL/3MF) is disabled, and no other export path exists (no menu item, no shortcut, no quick export). Source: D7, prompt.
- **E2:** With FAIL. Expected: the gate panel names the failing rule (for example an open edge or a unit mismatch), in the `check_watertight` style of one message per first failing rule. Source: D7, R (Repair section).
- **E3:** Make the check PASS. Expected: Export is enabled, and both STL and 3MF are offered. Source: D7.
- **E4:** On every tab, look at the status bar. Expected: it shows units (read-only), watertight PASS/FAIL and volume at all times. Source: D6.
- **E5:** Toggle mm/in in the top bar. Expected: the labels and readouts change units. The locked export unit is unchanged (3MF stays `unit="millimeter"` unless Erik decides otherwise). The mockup toggle only changes labels. Source: D6, prompt.

## 4. Layout
- **L1 (1440x900):** Expected: the top bar has File, Undo/Redo, the tabs Sketch/Model/Repair/Export and mm/in. The tree is on the left, the inspector on the right, the viewport in the center, and the status bar at the bottom. Source: D1, D6, prompt.
- **L2 (390x844):** Expected: the tabs are in a bottom bar, and the tree and inspector open as drawers and close again. Tool search sits in the tools menu. Source: prompt, R.
- **L3:** On Model, tap New Sketch. Expected: the Sketch tab becomes active, and a Finish Sketch bar is visible. Tapping it returns to Model. Source: D2.
- **L4:** On every tab. Expected: exactly one floating view bar (select modes, Measure, Section, display modes, Orbit/Pan/Zoom/Fit, views, Isolate/Hide) plus the ViewCube, top right. The view controls are not repeated in the toolbar. Clicking a ViewCube face snaps the view. Source: D4, prompt.
- **L5:** Expected: no radial menu (right-click or long-press shows none) and no history timeline. Only the browser tree ships. Source: D5, D8.

## 5. Repair tab
- **P1:** Open Repair. Expected: exactly Check shape, Find open edges, Auto-heal and Mesh repair. Each gives feedback (a toast in the mockup). Source: D3, prompt.
- **P2:** Expected: there is no small-gaps fix, and no Remove small features or Merge coplanar faces (all later or TBD). Source: D3, R (Repair section).
- **P3 (built app, not mockup):** After Auto-heal or Mesh repair, the status-bar PASS/FAIL updates, and the result reports what changed or "cannot repair". Source: R [Repair tool list, items 3 and 7].

## 6. Rotation (portrait and landscape)
Erik, 2026-10-21: one responsive WASM app for desktop and phone, in both orientations. Rotate in Chrome DevTools device mode with the Rotate button in the device toolbar [12]. In app code, `matchMedia('(orientation: portrait)')` [10] and `screen.orientation` `change` [9] are the hooks to test. WCAG 2.1 SC 1.3.4 (AA) says content must not be restricted to one orientation unless that is essential [11].
- **R1:** At 390x844 (portrait) and 844x390 (landscape), visit Sketch, Model, Repair and Export. Expected: all 4 tabs reachable in both, and the Export button reachable without horizontal scroll. Source: D1, [12].
- **R2:** Open a sketch with one entity selected, then rotate; repeat with a dialog or drawer open. Expected: same tab, sketch still open, selection kept, dialog still open with its input values. No reload. Source: [9][10].
- **R3:** Rotate on every tab, and on a real phone with the OS rotation lock off. Expected: no "rotate your device" block, no `screen.orientation.lock()`, and all content works in both. Source: [11].
- **R4:** At 844x390, measure the same controls as T1. Expected: each is at least 44 x 44 CSS px. Source: D9 [2].
- **R5:** In both orientations on every tab. Expected: the status bar shows units, watertight PASS/FAIL and volume, not hidden or clipped. Source: D6, E4.

## Sources
1. W3C, Understanding SC 2.5.8 Target Size (Minimum): https://www.w3.org/WAI/WCAG22/Understanding/target-size-minimum.html
2. W3C, Understanding SC 2.5.5 Target Size (Enhanced): https://www.w3.org/WAI/WCAG22/Understanding/target-size-enhanced.html
3. Apple HIG, Buttons (hit region at least 44x44 pt): https://developer.apple.com/design/human-interface-guidelines/buttons ; also https://developer.apple.com/design/tips/
4. Material Design 3, Density/targets (48x48 dp): https://m3.material.io/foundations/layout/grids-spacing/density
5. Chrome DevTools, Simulate mobile devices with device mode: https://developer.chrome.com/docs/devtools/device-mode
6. Google Chrome Help, Chrome keyboard shortcuts: https://support.google.com/chrome/answer/157179
7. Apple Support, Use shortcuts on an Apple external keyboard with iPad: https://support.apple.com/guide/ipad/use-shortcuts-ipaddf61a0c2/ipados
8. Repo: mvp/ui-redesign.md (Team decisions (final)), prompts/gui-mockup.md, research/gui/ui-layout-review.md
9. MDN, ScreenOrientation: change event: https://developer.mozilla.org/en-US/docs/Web/API/ScreenOrientation/change_event
10. MDN, Window.matchMedia() and the orientation media feature: https://developer.mozilla.org/en-US/docs/Web/API/Window/matchMedia ; https://developer.mozilla.org/en-US/docs/Web/CSS/@media/orientation
11. W3C, Understanding SC 1.3.4 Orientation: https://www.w3.org/WAI/WCAG21/Understanding/orientation.html
12. Chrome DevTools, device mode (Rotate): https://developer.chrome.com/docs/devtools/device-mode#orientation
