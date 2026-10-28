# Second-priority pack: sketch plane-pick toggle + toolbar density + floating panels (2026-10-27)

Invent-free Dig · DEV research. Compiled **2026-10-27 ~6:25 PM MT** (America/Denver).

**Pack label (Chief/Erik):** second priority task — research **1 + 2 + 3** in one invent-free pack. Hand Doc only when all three ready.

**Hard lock:** No invented px, hex, sizes, dims, hotkeys, snap/persist/z-order behaviors, or claims. Cite every source. Flag **GAPS** / **TBD**.

**Context:** SoT tip `bacb3f7`; Pilot item-7 base still `91369e1`. **No Z13 CAD coding.** Item-7 stays LIVE uninterrupted. **Coding tip only after Chief lock AND item-7 exits.**

**Related (do not contradict):** [`ui-layout-review.md`](ui-layout-review.md), [`modo-tools.md`](modo-tools.md), [`origin-plane-sketch.md`](origin-plane-sketch.md), [`../mobile-touch-cad.md`](../mobile-touch-cad.md), overnight chrome digests under `research/overnight-*.md`.

---

## 1) TOP — Sketch-create plane-pick toggle (like Multi)

### Erik ask (incomplete — TBD)

Erik (via Chief ~6:18 PM MT): when creating a sketch, a **toggle (like multi-select)** to turn **on/off** the ability to **select a plane**. Note cut off at **"currently I am able to…"** — remaining intent **TBD**. Do not invent the missing clause, dims, or hotkeys.

### MVP current UX at tip `bacb3f7` (READ ONLY)

Source: `git show bacb3f7:web/index.html` on ErmoZ13 (`C:\Dev\cadcam-mvp`), tip `bacb3f78a5de3b72872d5a44d81b4c3f0c2bd18a`.

| Fact | Evidence on tip |
| --- | --- |
| Enter Sketch workbench via toolbox tab `data-tab="sketch"`. | `#i-tab-sketch` / `data-tab="sketch"` |
| Until a plane is set, `#originPlanes` shows ortho chips: Front, Back, Top, Bottom, Left, Right (`data-action="originPlane"`). | `paintOriginPicker`: `show = sketchActive && !state.sketchPlane` |
| Status copy when bodies exist: **"Pick an ortho plane or tap a planar face — returns to Model"**. Empty doc: pick Front/Back/Top/Bottom/Left/Right. | `paintSketchStatus` |
| Face pick: `pickSketchFace` temporarily forces `state.selection = 'face'`, ray + phone 44 CSS px miss ring (radius 22). Non-planar → toast **"That face is not planar."** | `pickSketchFace`, `setSketchPlane` |
| Origin chip → `setOriginSketchPlane` sets `state.sketchPlane.originPlane` + view. Face → `setSketchPlane` sets face/body frame. | functions above |
| After plane set, origin bar hides; sketch tool panel shows (`data-sketch-plane`). | `paintOriginPicker` |
| **Multi** toggle (`#multiToggle`, `data-action="multiToggle"`) flips `state.phoneMulti` only — **not** wired to plane-pick enable/disable. | action handler + `paintPhoneChrome` |
| **Pick filter** (`#pickFilter` / `pickChooser`) exists for Body (etc.) — separate from sketch plane-pick. | phone tabbar markup |
| **No** control on tip that toggles "ability to select a plane" on/off during sketch create. | tip scan: no `selectPlane` / plane-pick toggle id |

### Peers (sourced only)

| Product | How sketch plane / face is chosen | Toggle that enables/disables plane-or-face pick? |
| --- | --- | --- |
| **Fusion** | Create Sketch → select origin plane, work plane, or planar face. [F-S1][F-S2] | **Selection Filters** can block pick: if Body Faces (and related) are off, user **cannot** select plane/surface to start a sketch. [F-S3][F-S4] Closest sourced parallel to "toggle ability to select." Not labeled as a sketch-only Multi-like chip. |
| **Onshape** | Sketch dialog → select **one** plane at a time; or part face / Mate connector. Sketch first or plane/face first. [O-S1] | **GAP:** no published "toggle off plane select" control like Multi. One-plane-at-a-time is the documented limit. [O-S1] |
| **SolidWorks** | Sketch or sketch tool → prompted to select plane; or pre-select plane/face then Sketch. [SW-S1][SW-S2] | **GAP:** no published Multi-like toggle to disable plane selection during New Sketch in pages fetched. |
| **Shapr3D** | Select plane before sketch; or planar face / construction plane; origin rectangles near origin; Space on hover; touch double-tap. [SH-S1] | **GAP:** no published on/off toggle for "ability to select a plane" in pages fetched. |
| **Modo** | Mesh **Sketch** tool draws on **Work Plane**; align Work Plane to selection (incl. polygon). Different paradigm from B-rep sketch-on-plane. [M-S1][M-S2] | Work Plane on/off / align — **not** the same as CAD "select sketch plane" toggle. **GAP** for B-rep plane-pick toggle. |

### §1 invent-free recommendation

**Verdict: TBD pending Erik's cut-off sentence + Chief lock.**

- MVP today: plane pick is **always on** while Sketch tab is active and `state.sketchPlane` is null (ortho chips + face tap). Multi does **not** gate it. [tip `bacb3f7`]
- Peer **closest** sourced pattern for enabling/disabling what can be picked: **Fusion Selection Filters** (Body Faces / work geometry). [F-S3][F-S4]
- Peers otherwise: **required** plane/face pick to enter sketch, not a Multi-style optional gate. [O-S1][SW-S1][SH-S1]
- Do **not** invent: default on vs off, whether toggle also disables face tap vs only origin chips, hotkey, or chip placement.

**Erik TBD to resolve:** finish "currently I am able to…" — able to select faces when unwanted? able to pick planes after sketch started? something else?

---

## 2) Menu-bar text / icons — shrink a few px?

### Per product (sourced)

| Product | Density / size facts | User compact control? | Published px |
| --- | --- | --- | --- |
| **Modo** | Form View Options (O): Icon Size **Extra small / Small / Large** (or Normal = form default). [M1] | Yes | SDK: command/tool **20×20** small, **32×32** large; tree **13×13**. [M3] **GAP:** Extra-small exact px |
| **Shapr3D** | Main menu **icons only** by default; labels on hover via setting. [S1][S3] | Icon-only / labels-on-hover — not "shrink N px" | **GAP:** no icon/font px |
| **Onshape** | Lower res / higher browser zoom → toolbar **more compact**, tools collapse into dropdown groups. [O1] Forum: use browser zoom. [O3] | Collapse + zoom, not icon-size pref | **GAP:** no icon px |
| **Fusion** | Small **16×16** (toolbars/dropdowns), large **32×32** (panels); HiDPI 32/64 assets. [F1] Toolbar single-row; **hides** overflow commands. [F2] Apparent size via **OS scaling**. [F3] Space: show/hide, minimize, dock — not icon shrink. [F4] | No in-app few-px shrink found | 16 / 32 (HiDPI 32 / 64) [F1] |
| **SolidWorks** | Customize → Toolbars: text + button sizes; **Small / Medium / Large** icon choices (reseller). [SW1][SW2] | Yes | **GAP:** S/M/L px not published in fetched official text |

### Standing phone floor (already in tree)

Tappable targets: WCAG / HIG / Material → standing phone rule **≥44 CSS px** in [`../mobile-touch-cad.md`](../mobile-touch-cad.md). [T1]

### §2 invent-free recommendation

**Verdict: CAUTION — insufficient evidence to lock "shrink a few pixels."**

- Density **modes** / icon-only / collapse are sourced; a numeric **"few px"** delta is **not** published by any of the five. [M1][S1][O1][F1][SW2]
- Fusion explicitly keeps fixed icon roles and hides overflow rather than shrinking. [F1][F2]
- Phone: do not shrink tappable chrome below **≥44 CSS px** without Chief re-lock. [T1]

---

## 3) Off-bar menus — float, drag, X/close (esp. top-right)

### Per product (sourced)

| Product | Float / drag | Close / dismiss | Persist / snap / z-order |
| --- | --- | --- | --- |
| **Modo** | Thumb-drag detaches viewport to floating window; dock via yellow line. [M4][M5] Alt+click toolbar → popover; Ctrl/Cmd+click → palette. [M2] | Palette: **single close** in thin header. [M5] Popover: dismiss on mouse leave; **pin = small circle upper-right**. [M4] | Floating windows **persist** sessions; pinned popovers **persist**. [M4] **GAP:** snap grid; z-order |
| **Shapr3D** | Menus **float over canvas** (left main / right constraints). [S2] | **GAP:** X placement for floating main menus not documented (persistent chrome). | **GAP:** persist XY, snap, z-order |
| **Onshape** | Feature dialogs **move/resize** with mouse. [O4][O5] | Check accept; **X** / Escape cancel. [O5] Mobile: check / X. [O4] | Mobile remembers manual expand height. [O4] **GAP:** desktop XY persist, snap, z-order; **GAP:** desktop X corner not locked by a prose sentence in fetched text |
| **Fusion** | Undock by pull-away; dock at **green** edge bar. [F5] Minimize: double-arrow (docked) / minus (undocked) on dialog title bar upper right or left. [F4] | Minimize per [F4]; command OK/Cancel lifecycle. **GAP:** universal floater X corner | **GAP:** free-float XY persist; z-order; snap beyond green bar |
| **SolidWorks** | CommandManager **floats** (drag / double-click); redock via docking arrows; double-click float → last dock. [SW3] | OK/Cancel on PropertyManager (re-open SW help before coding cites). [SW5] | Last-dock restore. [SW3] **GAP:** snap grid; z-order; free XY persist |

### §3 invent-free recommendation

**Verdict: OK as a product pattern to support float + drag + explicit dismiss; CAUTION on locking "X always top-right"; GAPS on snap / persist / z-order — do not invent.**

- Only Modo popover **pin** is explicitly **"upper right"** in fetched prose. [M4]
- Flag for Chief: snap, persist position, z-order = **TBD / GAP** unless new sources appear.

---

## Combined Dig recommendation (for Chief / Doc)

| # | Topic | Dig call | Notes |
| --- | --- | --- | --- |
| 1 | Sketch plane-pick toggle | **TBD** | Erik sentence incomplete. Closest peer: Fusion Selection Filters. MVP has no such toggle; Multi ≠ plane gate. |
| 2 | Shrink menu-bar few px | **CAUTION / insufficient evidence** | Prefer density mode, icon-only, or collapse; keep phone ≥44. |
| 3 | Float + drag + X | **OK pattern; CAUTION on X corner; GAP snap/persist/z-order** | Source Modo/Onshape/Fusion/SW/Shapr float behaviors; do not invent snap/persist/z-order. |

---

## GAPS / TBD (explicit)

1. Erik cut-off: **"currently I am able to…"** — intent **TBD**.
2. Whether plane-pick toggle means origin chips only, face tap only, or both — **TBD**.
3. Numeric **"few px"** shrink delta — unpublished.
4. SolidWorks S/M/L and Modo Extra-small **exact px** — unpublished / incomplete.
5. Shapr3D / Onshape icon + label **font px** — unpublished in pages fetched.
6. Floating **snap**, **XY persist** (except Modo float/pin persist), **z-order** — **GAP**.
7. Universal **"X top-right"** lock — only Modo pin corner is prose-explicit; others **GAP**.
8. Current cad-mvp menu-bar computed CSS px at `bacb3f7` — **not measured in this digest** (follow-on Dig after Chief asks).
9. Peer-product screenshot measurements in `research/` — none this turn.

---

## Next steps (prompt-ready — Grok Build / Cursor)

**Coding tip ONLY after Chief lock AND Pilot item-7 exits.** Do not start chrome or sketch-plane coding from this digest alone. Item-7 attempt3 stays LIVE.

1. **Doc:** tip-match when this lands on a research PR; no `web/` edits from Dig.
2. **Chief / Erik:** finish the plane-pick sentence; lock §1 (toggle yes/no, what it gates, default). Prefer Fusion-filter-style wording only if Erik confirms that intent.
3. **Chief:** lock §2 path (no shrink / density enum / icon-only / collapse). Keep phone ≥44 unless re-locked.
4. **Chief:** lock §3 which surfaces float; dismiss control; leave snap/persist/z-order TBD.
5. **Dig later (invent-free):** measure tip menu-bar icon/text CSS px before any shrink coding.
6. **Pilot / GB / Cursor:** implement only after locks + item-7 exit; no invented px/hotkeys.

---

## Sources

Accessed 2026-10-27 ~6:25 PM MT (America/Denver) unless a page carries its own date.

### §1 MVP tip
- Z13: `git show bacb3f7:web/index.html` in `C:\Dev\cadcam-mvp` (commit `bacb3f78a5de3b72872d5a44d81b4c3f0c2bd18a`). Functions/IDs: `paintOriginPicker`, `paintSketchStatus`, `pickSketchFace`, `setSketchPlane`, `setOriginSketchPlane`, `#originPlanes`, `#multiToggle`, `state.phoneMulti`.

### §1 peers
- [F-S1] Fusion Create a sketch: https://help.autodesk.com/view/fusion360/ENU/?contextId=SKT-CREATE-3D-SKETCH
- [F-S2] Start a sketch on a plane or face: https://help.autodesk.com/cloudhelp/ENU/Fusion-Sketch/files/GUID-88CC0E51-AD05-4028-BF59-FACA5EC0FA2B.htm
- [F-S3] Cannot select plane/surface — Selection Filters: https://www.autodesk.com/support/technical/article/caas/sfdcarticles/sfdcarticles/Cannot-select-plane-or-face-to-start-a-sketch-in-Fusion-360.html
- [F-S4] Use selection filters: https://help.autodesk.com/cloudhelp/ENU/Fusion-Model/files/SLD-SELECTION-FILTERS.htm
- [O-S1] Onshape Sketch Basics: https://cad.onshape.com/help/Content/Sketch/sketch_basics.htm
- [SW-S1] MySolidWorks — Creating New Sketches: https://my.solidworks.com/reader/onlinehelp/2021%252Fenglish%252Fsolidworks%252Fsldworks%252Ft_creating_new_sketches_with_existing_sketches.htm/creating-new-sketches-with-existing-sketches
- [SW-S2] Edit Sketch Message PropertyManager (prompt to select plane): https://my.solidworks.com/reader/onlinehelp/2021%252Fenglish%252Fsolidworks%252Fsldworks%252Fhidd_dve_sketch_message_dlg.htm/edit-sketch-message-propertymanager
- [SH-S1] Shapr3D Using sketch planes: https://support.shapr3d.com/hc/en-us/articles/7874240047388-Using-sketch-planes
- [M-S1] Modo Work Plane: https://learn.foundry.com/modo/current/content/help/pages/modeling/workplane.html
- [M-S2] Modo Sketch tool: https://learn.foundry.com/modo/current/content/help/pages/modeling/create_geometry/sketch.html

### §2 / §3 (shared)
- [M1] Modo Form View Options: https://learn.foundry.com/modo/current/content/help/pages/modo_interface/viewports/list_info/properties.html
- [M2] Modo Exploring the Layout: https://learn.foundry.com/modo/current/content/help/pages/modo_interface/exploring_layout.html
- [M3] Modo SDK Icon Resources: https://learn.foundry.com/modo/developers/latest/sdk/pages/ui/Icon%20Resources.html
- [M4] Modo UI Conventions: https://learn.foundry.com/modo/content/help/pages/modo_interface/ui_conventions.html
- [M5] Modo Layout Controls: https://learn.foundry.com/modo/current/content/help/pages/modo_interface/layout_controls.html
- [S1] Shapr3D modeling space: https://support.shapr3d.com/hc/en-us/articles/7873880676508-Shapr3D-modeling-space
- [S2] Shapr3D Accessing tools: https://support.shapr3d.com/hc/en-us/articles/7378907587484-Accessing-tools
- [S3] Shapr3D 5.440 UI Refresh: https://support.shapr3d.com/hc/en-us/articles/9971839217436-5-440-User-Interface-Refresh
- [O1] Onshape UI Basics: https://cad.onshape.com/help/Content/Home/user_interface_basics.htm
- [O3] Onshape forum toolbar/UI size: https://forum.onshape.com/discussion/2328/is-it-possible-to-resize-the-toolbars ; https://forum.onshape.com/discussion/25346/how-do-i-adjust-the-size-of-the-user-interface
- [O4] Onshape Dialogs: https://cad.onshape.com/help/Content/Home/dialogs.htm
- [O5] Onshape Feature Basics: https://cad.onshape.com/help/Content/PartStudio/feature_basics.htm
- [F1] Fusion API UI icons: https://help.autodesk.com/cloudhelp/ENU/Fusion-360-API/files/UserInterface_UM.htm
- [F2] Fusion forum toolbar resize (Brian Ekins): https://forums.autodesk.com/t5/fusion-api-and-scripts-forum/resizing-fusion-360-toolbars/td-p/6240736
- [F3] Fusion icon size via Windows scaling: https://www.autodesk.com/support/technical/article/caas/sfdcarticles/sfdcarticles/How-to-increase-icon-size-in-Fusion-360-on-Windows-OS.html
- [F4] Fusion UI screen space: https://www.autodesk.com/support/technical/article/caas/sfdcarticles/sfdcarticles/UI-elements-take-up-too-much-screen-space-in-Fusion-360.html
- [F5] Fusion dock/undock: https://www.autodesk.com/support/technical/article/caas/sfdcarticles/sfdcarticles/How-to-dock-undock-toolbars-and-dialog-boxes-in-Fusion-360.html
- [SW1] SolidWorks Text and Button Sizes: https://help.solidworks.com/2025/english/SolidWorks/sldworks/c_user_interface_tablets.htm?format=P&value=
- [SW2] Javelin Scaling SOLIDWORKS UI: https://www.javelin-tech.com/blog/2025/08/scaling-the-solidworks-user-interface/
- [SW3] CATI CommandManager float/dock: https://www.cati.com/blog/exploring-the-solidworks-commandmanager/
- [SW5] SolidWorks PropertyManager Overview: https://help.solidworks.com/2022/english/SolidWorks/sldworks/r_pm_overview.htm?format=P&value=
- [T1] `research/mobile-touch-cad.md`
