# Save/load — BREP-only round-trip after P6 (prep)

MVP Research Digest prep for the next slice after P6. Invent nothing. Units: **mm**. Volume: **mm³**. Gate: OCCT validity + units (watertight dropped, 02:17 rule). Research only — no `web/`, `tests/`, prompts, UPDATES, PROGRESS, kernel, or WASM edits in this PR.

Product slices P1–P6 stay closed. P6 measure/callouts is on `main` via [#98](https://github.com/cyborgpencil/cad-mvp/pull/98) (merge `56c2528`). UPDATES for #98 is [#99](https://github.com/cyborgpencil/cad-mvp/pull/99) (merge `4163538`). Tip at write: `4163538`. 3T stuck-check 2026-10-24 ~12:39–12:41 PM MT (America/Denver): next queue is save/load, then view-cube swipe. **3T final lock the same day:** Boolean, fillet, and sketch→extrude bodies reload as solids with null `primitive` and no feature rebuild. This note does not reopen P1–P6. Swipe stays after this slice.

The older checklist in [`../project-save-load.md`](../project-save-load.md) is also labeled P1–P7. That list is the 2026-10-22 save/load check, not product slices P1–P6.

## 1. What already ships (tip `4163538`)

`.cadmvp` is on `main` via [#2](https://github.com/cyborgpencil/cad-mvp/pull/2) (merge `c08ef3d`), module `web/project-file.mjs`. The original prompt [`../../prompts/project-save-load.md`](../../prompts/project-save-load.md) said Booleans were not built yet and to add a Boolean case later (Tests, first bullet). The checklist is [`../project-save-load.md`](../project-save-load.md).

| Fact | Where |
|---|---|
| Format is version **1**, units **`mm`**, extension `.cadmvp` | `PROJECT_VERSION`, `PROJECT_UNITS`, `PROJECT_EXTENSION` in `web/project-file.mjs` |
| Shape text is `BRepTools.Write` / `BRepTools.Read` through the Emscripten FS path. The file comment says the `std::ostream` / `std::istream` overloads are not in the symbol map, and a `std::stringstream` wrapper cannot be compiled here | `web/project-file.mjs` header; `writeBrepText`; `readBrepText` |
| Wrong or missing units, a non-1 version, empty text, unreadable JSON, or a failed shape check returns an error that says the model was not changed | `ERR_EMPTY`, `ERR_READ`, `ERR_UNITS`, `ERR_VERSION`, `ERR_SHAPE`; `parseProject` |
| Volume is `BRepGProp.VolumeProperties` → `Mass()`. Bounds are `BRepBndLib.AddOptimal` | `shapeVolumeMm3`, `optimalBounds`, `measureShape` |
| Materials the file can carry are the part `material` string. The tag list is PLA, PETG, TPU. Missing or `"default"` reads as PLA | `web/assemblies.mjs` `MATERIALS`, `DEFAULT_PART_MATERIAL`, `materialTag` (PR [#8](https://github.com/cyborgpencil/cad-mvp/pull/8), merge `dd22dce`). `partFromBody` stores `body.material`, or `DEFAULT_MATERIAL` (`'default'`) when that string is empty |
| New box / cylinder / disc bodies are stored with `material: 'PLA'` | `makeOwned` in `web/index.html` |
| The material menu writes `PLA`, `PETG`, or `TPU` onto the selected bodies | `#partMaterial` change listener in `web/index.html` |

Live smoke is `run_saveload` in `tests/deploy_smoke.py`. Its docstring is a box and a cylinder through `window.__cadcamProject`. `SAVELOAD_EXPR` does all of the following:

- `preparePair` (box + cylinder), save, `units === 'mm'`, `version === 1`.
- Reload, and for each of those parts `source === 'parameters'`, volume and `xmin/ymin/zmin/xmax/ymax/zmax` within 0.01 (`Math.abs(a - b) <= 0.01`). The box volume check is 8000.
- Display switched to inches, save again, file `units` still `mm`, load, display unit still `in`, volumes still within 0.01.
- `clearUndo` once per accepted load; undo and redo depth 0 after load.
- Corrupt JSON, empty, blank, `"units": "in"`, missing `units`, and cancel (`loadText(..., false)`) leave the model and the dirty flag untouched. Cancel does not call clear.

`parseProject` rejects a version other than 1 with `ERR_VERSION`. That version case is in the checklist (P7) and in `parseProject`. It is not one of the `SAVELOAD_EXPR` strings above.

## 2. Reload path today (file:line on tip `4163538`)

`partFromBody` writes `primitive: { kind, parameters }` only when `body.kind` and `body.params` are both set (`web/project-file.mjs` 183–185). Otherwise the part field is `null`.

`rebuildShape` (`web/project-file.mjs` 297–357) returns null when there is no primitive (298–299), when `part.features` is non-empty (300), or when `kind` is not `box`, `cylinder`, or `disc` (334–335).

`loadShapes` (`web/project-file.mjs` 364–412) keeps a parameter rebuild only when `rebuildShape` returns a shape and `checkOcctShape(...).pass === true` (378–385, `source: 'parameters'`). Otherwise it reads the BREP text, requires the same `pass === true`, and sets `source: 'brep'` (390–399). A failed read or a failed check aborts the load (`ERR_SHAPE`) after dropping shapes already built. On the BREP path, `kind` stays `part.primitive.kind` when that field exists, and is `'brep'` when `primitive` is null (375). `params` stays `part.primitive.parameters` when the primitive object exists (376).

`checkOcctShape` sets `pass` from `BRepCheck_Analyzer.IsValid()` and zero free edges (`web/occt-gate.mjs` 91–99). This slice does not change that function. The standing gate name remains OCCT validity + units. Watertight stays dropped as an export gate (02:17 rule, [`../formats/validation.md`](../formats/validation.md)).

Successful `applyLoadedProject` replaces the scene, sets `state.primitive` to null (`web/index.html` 8851), then calls `clearProjectUndo` (8884). `state.primitive` is the edit sheet. The lock’s “null primitive” is the part field and the reloaded body’s `params`.

| Body today | Saved `primitive` | What `loadShapes` does |
|---|---|---|
| Scene Union or Cut (`applySceneBoolean`, `web/index.html` 5762–5767): `kind: 'boolean'`, `params: null`, material copied from the first selected body | `null` (no params) | `rebuildShape` returns null. Shape is BREP, `source: 'brep'`, `kind` becomes `'brep'`, `params` stays null |
| Sketch→extrude New body (`web/index.html` 10238–10258) and Join/Cut extrude (`installExtrudeOnBody`, 9783–9787): `kind: 'extrude'`, params object set, `features: []` | `{ kind: 'extrude', parameters: … }` | `rebuildShape` returns null (`kind` is not box/cylinder/disc). Shape is BREP, `source: 'brep'`. Kind stays `'extrude'` and those params stay on the body |
| Fillet / chamfer (`web/index.html` 5648–5680): kind and params are not cleared. Feature faces are appended onto `body.features` when `result.featureFaces` is non-empty (5679–5680) | Primitive object present when kind and params were already set | Non-empty `features` makes `rebuildShape` return null, then BREP fallback, but kind and params of the old primitive stay. If no feature faces were stored, `rebuildShape` can still rebuild the box, cylinder, or disc from parameters |

## 3. Gap this slice closes

The prompt parked a Boolean round-trip. Those solids exist now, and the smoke does not save them.

| Landed since the prompt | Merge | What the smoke still does not round-trip |
|---|---|---|
| Sketch → Blind extrude [#70](https://github.com/cyborgpencil/cad-mvp/pull/70) | `7c83b2a` | An extruded solid. File still stores an `extrude` primitive; reload keeps that params object with `source: 'brep'` |
| Extrude Join/Cut [#83](https://github.com/cyborgpencil/cad-mvp/pull/83) | `99063c9` | Same `kind: 'extrude'` path as the New body |
| Touch Booleans + fillet [#91](https://github.com/cyborgpencil/cad-mvp/pull/91) | `73408c4` | Union and Cut already save `primitive: null`. Fillet can still rebuild from the old primitive when `features` is empty |
| P6 measure/callouts [#98](https://github.com/cyborgpencil/cad-mvp/pull/98) | `56c2528` | Not a save/load case. Closed |

Material tags are specified in the checklist (PETG, TPU, untagged reads as PLA) and are not asserted in `SAVELOAD_EXPR`.

## 4. Typical CAD (sourced)

Fetched 2026-10-24. Claims below are only what those pages state. They are not extra MVP requirements.

| Product | What the page states | URL fetched |
|---|---|---|
| **Onshape document** | Documents contain the project data and work is recorded automatically. A version is the state of a whole document at a point in time; its geometric data is unchangeable. History can restore a workspace to an earlier point. | https://cad.onshape.com/help/Content/Document/document_management.htm |
| **Onshape export** | Export writes a Part Studio, part, or Assembly to another CAD format and downloads it. “The downloaded data will not contain features or parametric history.” | https://cad.onshape.com/help/Content/File/exporting_files.htm |
| **Fusion archive** | `.f3d` is an archive of a single design workspace. `.f3z` is an archive of a distributed design and includes external references; an F3Z is a ZIP that contains one or more F3D files. A design with xrefs exports as F3Z. Export can go to the cloud or the computer. A second Autodesk page says an `.f3d` encapsulates the design, including design history and metadata, and an `.f3z` is a compressed package of one or more `.f3d` files plus related resources. | https://www.autodesk.com/support/technical/article/caas/sfdcarticles/sfdcarticles/How-to-make-a-local-archive-back-up-file-in-Fusion-360.html and https://www.autodesk.com/support/technical/article/caas/sfdcarticles/sfdcarticles/The-differences-between-an-f3z-and-f3d-file-in-Fusion.html |
| **FreeCAD FCStd** | `.FCStd` is the main FreeCAD file and is a zip. `Document.xml` holds the geometric and parametric definition. Each object that has a Part shape, even a parametric one, also stores that shape as its own `.brep` file so it can be used without recalculating the shape. The typical layout lists those shape files as `.brp`. | https://raw.githubusercontent.com/FreeCAD/FreeCAD-documentation/main/wiki/File_Format_FCStd.md (wiki page https://wiki.freecad.org/File_Format_FCStd is the same article; this fetch used the documentation source) |

Onshape’s cloud history, Fusion’s `.f3d` history, and FreeCAD’s parametric `Document.xml` plus a stored shape are product behavior. T1–T6 say what this slice includes.

## 5. Slice locks (3T final, 2026-10-24, America/Denver)

Numbering is 3T’s list. These are locks, not proposals. Shared reload rule from that lock: Boolean, fillet, and sketch→extrude bodies come back as solids with **null `primitive`** and **no feature rebuild**. The cases to script are T2, T3, and T4. Fillet is the same reload rule; T1–T6 do not add a separate fillet case.

“Null `primitive`” means the `.cadmvp` part’s `primitive` is null and the reloaded body’s `params` is null, so `rebuildShape` does not rebuild that solid. `source` on that solid is `'brep'`.

### T1 — Format

Keep version **1**, units **`mm`**, and the existing FS `BRepTools.Write` / `BRepTools.Read` path in `web/project-file.mjs`. No WASM rebuild. No format v2.

### T2 — Boolean

Union and Cut results round-trip as BREP-only (null `primitive`). Volume and `BRepBndLib.AddOptimal` bounds match within **0.01** (mm³ and mm). Same helpers as `measureShape`.

### T3 — Materials

PETG, TPU, and PLA-default tags survive. `MATERIALS` is `PLA`, `PETG`, `TPU`. `materialTag` maps a missing tag or `"default"` to PLA. PETG and TPU stay those strings.

### T4 — Sketch→extrude

One extruded solid round-trips BREP-only (null `primitive`, same shared rule). Volume and AddOptimal bounds within **0.01**.

### T5 — Keep

Keep the current `SAVELOAD_EXPR` behaviour: bad files listed in section 1, cancel, `clearUndo` on accepted load only, and inch display with the file still `mm` and no volume drift. The box + cylinder pair stays `source: 'parameters'`.

### T6 — Out

Feature rebuild, view-cube swipe, reopening P1–P6, format v2, a `std::stringstream` binding, and any kernel or WASM change. Swipe stays next ([`../touch-gestures.md`](../touch-gestures.md)).

No open TBD inside T1–T6.

## 6. Team locks

| # | Lock |
|---|---|
| T1 | Format — v1, units mm, existing FS `BRepTools.Write` / `Read`. No WASM. No v2. |
| T2 | Boolean — Union and Cut round-trip BREP-only (null `primitive`). Volume and AddOptimal bounds within 0.01. |
| T3 | Materials — PETG, TPU, and PLA-default tags survive (`MATERIALS` / `materialTag` in `web/assemblies.mjs`). |
| T4 | Sketch→extrude — one extruded solid round-trips BREP-only (null `primitive`). Volume and bounds within 0.01. |
| T5 | Keep — current bad-file, cancel, `clearUndo`, and inch-display / file-still-mm behaviour. Box + cylinder stay `source: 'parameters'`. |
| T6 | Out — feature rebuild, swipe, reopening P1–P6, format v2, stringstream binding, kernel/WASM. |

## 7. Tests

Extend `tests/deploy_smoke.py` on the existing SAVELOAD path (`run_saveload`, `SAVELOAD_EXPR`, `SAVELOAD_BUTTONS_EXPR`) and `window.__cadcamProject` only. No new harness and no new smoke file. New Union/Cut, material, and sketch→extrude checks sit beside the current pair. They must not replace the `source === 'parameters'` check on that pair.

## 8. Next steps

1. **Doc Steward:** tip-match this research PR, then draft the Grok Build prompt from T1–T6. Locks are final. Do not edit `UPDATES.md` or `web/PROGRESS.md` in the research PR.
2. **Pilot / Grok Build:** implement only after that prompt. Reuse `documentFromBodies` / `loadShapes` and the FS Write/Read path. Union, Cut, and the extruded solid reload with null `primitive` and `source: 'brep'`. Measure with `measureShape` (volume and AddOptimal) within 0.01. Material tags as T3. Leave the current bad-file, cancel, clearUndo, and inch-display checks in place.
3. **Repo Keeper:** plain-merge this research PR when review is in. Research Digest is the author and does not self-APPROVE. Primary review is Research Digest tip-match.

## 9. Sources

Repo (this tip `4163538` unless a merge SHA is named):

1. `web/project-file.mjs` — version 1, units mm, FS `BRepTools.Write` / `Read`, `partFromBody`, `rebuildShape`, `loadShapes` (`source: 'parameters'` / `source: 'brep'`), `measureShape`, `parseProject`.
2. `web/index.html` — `applySceneBoolean` (Union/Cut, `params: null`), `commitSketchExtrude` / `installExtrudeOnBody` (`kind: 'extrude'`), fillet `features` append, `applyLoadedProject`, `clearProjectUndo`, `window.__cadcamProject`, `makeOwned` material `'PLA'`, `#partMaterial`.
3. `web/assemblies.mjs` — `MATERIALS`, `materialTag`, `DEFAULT_PART_MATERIAL` (PR #8, `dd22dce`).
4. `web/occt-gate.mjs` — `checkOcctShape` (`pass` is valid and zero free edges). Called by `loadShapes`. Not changed in this slice.
5. `tests/deploy_smoke.py` — `SAVELOAD_EXPR`, `run_saveload`.
6. `prompts/project-save-load.md` — Boolean case later; Chief format ruling.
7. `research/project-save-load.md` — checklist P1–P7; undo cleared on load.
8. `research/formats/validation.md` — units gate; watertight dropped (02:17).
9. `research/touch-gestures.md` — view-cube swipe stays after this slice (T6).
10. `research/gui/measure-sketch-next.md` — P6 prep. P6 is on main via #98 (`56c2528`); UPDATES #99 (`4163538`).
11. Merges: #2 (`c08ef3d`), #8 (`dd22dce`), #70 (`7c83b2a`), #83 (`99063c9`), #91 (`73408c4`), #98 (`56c2528`), #99 (`4163538`).

Official pages fetched for section 4:

12. Onshape Document Management: https://cad.onshape.com/help/Content/Document/document_management.htm
13. Onshape Exporting Files: https://cad.onshape.com/help/Content/File/exporting_files.htm
14. Autodesk, local Fusion archive: https://www.autodesk.com/support/technical/article/caas/sfdcarticles/sfdcarticles/How-to-make-a-local-archive-back-up-file-in-Fusion-360.html
15. Autodesk, `.f3d` vs `.f3z`: https://www.autodesk.com/support/technical/article/caas/sfdcarticles/sfdcarticles/The-differences-between-an-f3z-and-f3d-file-in-Fusion.html
16. FreeCAD File Format FCStd (documentation source): https://raw.githubusercontent.com/FreeCAD/FreeCAD-documentation/main/wiki/File_Format_FCStd.md

Team lock: 3T, CAD CAM MVP, 2026-10-24 (America/Denver), after the ~12:39–12:41 PM MT stuck-check. T1–T6 in section 6.
