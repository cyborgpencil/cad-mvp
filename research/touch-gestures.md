# Touch swipe gestures (2026-10-23)

Sourced notes for the swipe shortlist. 3T signed off the build order on 2026-10-23: the view-cube swipe first, then the three-finger undo/redo swipe, then the value-field nudge. Tool-shelf edge swipe is out, and orbit/pan stay as they are.

## Repo today (main)
- One pointer-event state machine on the viewport, with gesture types orbit, pan, gizmo, pinch and cube. One finger orbits; two fingers pinch-zoom and pan together.
- `#canvas` has `touch-action: none`; the view cube is tap-only (`pickViewCube`).

## Planned (open PRs, not on main)
- PR #21: view-cube swipe to the next face, 24 px at any speed, starting on the cube, separate from `tapSlopPx()`, `pointercancel` ends it (team-chosen values; Erik may change them after phone tests).
- PR #22: three-finger swipe left undoes, right redoes, with an off switch.
- PR #24: swipe a focused value field to nudge it 1 mm (1 deg on rotation) per step, one undo step each.
## Other apps (sourced)
| App | Orbit / pan / zoom | Undo / redo | View cube on touch |
|---|---|---|---|
| Onshape mobile [1] | 1-finger drag orbits, 2-finger drag pans, pinch zooms, 2-finger twist rotates 2D | not a gesture | tap opens a view menu; no swipe. Arrows step 15 deg, Shift 90 deg. 3D Rotate Lock stops orbit while dragging a selection |
| Shapr3D [2][3][4] | 1 finger orbits, 2 fingers pan, pinch zooms; double-tap a face zooms to it | 3-finger swipe left undoes, right redoes; chosen over 2-finger tap because 2 fingers already pan | face/edge/corner tap, arrows, double-tap for iso |
| Nomad Sculpt [5][6] | drag empty space orbits, 2 fingers pan, pinch zooms | 2-finger tap undoes, 3-finger tap redoes; long press repeats; can be turned off | n/a; toolbar buttons use swipe-up to show a slider |

## Web platform [7][8]
- Browsers own panning and pinch unless `touch-action` says otherwise; when the browser takes a gesture the page gets `pointercancel`, which must end any custom gesture.
- Any new swipe area (cube, value field) needs its own `touch-action` value. `touch-action: none` also blocks page zoom, an accessibility cost.

## Takeaways
- No source app has a swipe on the view cube; Erik's idea is new. Onshape's 90 deg arrow step is the closest model.
- Three fingers for undo/redo avoids the two-finger pan clash (Shapr3D's stated reason). iOS also has a system three-finger undo gesture; test on a real phone.
- Value-field nudge follows Nomad's swipe-to-slider idea: 1 mm per step (team-chosen), one undo step per swipe, focused field only (item 8 fix).
- Edge swipe for the shelf: no source found, and it competes with iOS and Safari edge gestures. Dropped.

## Next steps
- Pilot / Grok Build: PRs #21, #22 and #24 cover the three items; #21 passed the Front-left-to-Right rerun (8 of 8, all four directions, fast and slow).
- Tests: smoke-test each swipe in a 390x844 frame and on a real phone; units still read mm after each.

## Sources
1. Onshape, View Navigation and the View Cube: https://cad.onshape.com/help/Content/View/view_navigation_and_the_view_cube.htm
2. Shapr3D, Keyboard shortcuts, gestures, and hotkeys: https://support.shapr3d.com/hc/en-us/articles/7873906073884-Keyboard-shortcuts-gestures-and-hotkeys
3. Shapr3D forum, 2 finger undo - 3 finger redo: https://discourse.shapr3d.com/t/2-finger-undo-3-finger-redo/19784
4. Shapr3D, Control the view of your modeling environment: https://support.shapr3d.com/hc/en-us/articles/13079128172956-Control-the-view-of-your-modeling-environment
5. Nomad manual, History: https://nomadsculpt.com/manual/history
6. Nomad manual, Interface (Gesture): https://nomadsculpt.com/manual/interface
7. MDN, touch-action: https://developer.mozilla.org/en-US/docs/Web/CSS/Reference/Properties/touch-action
8. MDN, Pointer events: https://developer.mozilla.org/en-US/docs/Web/API/Pointer_events