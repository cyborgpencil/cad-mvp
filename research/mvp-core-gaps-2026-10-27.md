# MVP core research gaps (invent-free)

Checked 2026-10-27 ~5:55 PM MT on ErmoZ13. Home tree: `C:\dev\cadcam-mvp\research\` (repo `cyborgpencil/cad-mvp`, tip `507a019` / main). Do **not** treat `C:\dev\cadcam-mvp-research\research\INDEX.md` as live — that INDEX stops at 2026-10-23 and misses overnight + Modo hex notes.

Standing digest topics vs file state:

| Topic | Path | Last touch (local) | State |
| --- | --- | --- | --- |
| OCCT → WASM | `occt-wasm/` (README, prebuilt-options, pages-hosting, booleans) | 2026-10-21–22 | Strongest MVP core set; reuse-vs-build verdict already written. |
| Healing / validation | `healing/README.md` | 2026-10-22 | Sourced BRepCheck / ShapeFix / BRepMesh / Manifold notes. Open TBDs: tessellation deflections; Manifold vs in-house edge check. Pipeline text still mentions "export blocked or repaired" in Next steps while Export gate is units-only (02:17 rule in `formats/validation.md`). |
| STL / 3MF / units | `formats/validation.md`, `formats/stl-3mf-step.md` | 2026-10-22 | `validation.md` is the contract (units gate; watertight not a gate). `stl-3mf-step.md` is short and cites only "Multiple 3D printing guides" — needs proper sources if kept. |
| MCP AI tools | `ai-mcp/overview.md` | 2026-10-22 | Thin overview; INDEX still says **tool list TBD for Erik**. No per-tool schema digest yet. |
| Architecture | `architecture/mvp-notes.md` | 2026-10-22 | INDEX: scope conflicts pending Erik. |

GUI overnight + Modo hex digests (2026-10-27) are indexed; core kernel/export folders were not refreshed in that wave.

## Next steps (for Grok Build / Cursor once Erik picks a topic)

1. **If MCP:** draft invent-free MVP tool list from existing app ops (sketch, extrude, boolean, fillet/chamfer, units, export STL/3MF) + cite MCP spec; leave product choices as TBD until Erik locks.
2. **If healing:** align Next steps with 02:17 (report-only mesh checks; BRepCheck rolls ops back; Export = units); source current Manifold + ShapeFix docs; no invented deflection numbers.
3. **If formats:** replace weak STL/3MF/STEP sources with Consortium / ISO / lib3mf / OCCT docs; keep units gate as written.
4. **If occt-wasm:** re-verify prebuilt options against current libcascade / OCCT 8.x pages (versions only from live sources).

## Sources (this gap note)

- Local files under `C:\dev\cadcam-mvp\research\` and `research\INDEX.md` (mtime 2026-10-27 3:18 PM MT).
- `formats/validation.md` (02:17 rule pointers).
- `C:\dev\cadcam-mvp-research\research\INDEX.md` compared as stale mirror (mtime 2026-10-23).
