#!/usr/bin/env python3
"""Phone Auto-heal / Mesh repair Undo/Redo smoke (390x844, Chromium and WebKit).

Verifies:
- Repair a broken mesh (Auto-heal and Mesh repair), Undo: mesh and validity
  status match pre-repair; Redo restores the repaired mesh.
- Repair on a clean mesh (or unrepairable/cleared scene) pushes no undo step
  and leaves g_mesh untouched (including open_box with a duplicate vertex).
- Extrude, then repair, then Undo removes only the repair.
- Covers the sceneCleared snapshot path in installSnapshot (L6580-6585).
- Watertight and mm hold after Undo and Redo at phone width (390x844).

State waits only (no sleep, skip, xfail, or timeout bump). Exit 77 when
Playwright or libcascade is missing locally; fail hard when CI is set.
"""
from __future__ import annotations

import os
import sys
import threading
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
WORK = ROOT / "builds" / "repair-undo-smoke"
SKIP = 77

CAPTURE_MODULE_SCRIPT = """
(() => {
  let orig = null;
  Object.defineProperty(window, 'createCadcam', {
    configurable: true,
    enumerable: true,
    get() {
      return orig;
    },
    set(fn) {
      if (typeof fn !== 'function') {
        orig = fn;
        return;
      }
      orig = async function (...args) {
        const mod = await fn.apply(this, args);
        window.__cadcamTestModule = mod;
        return mod;
      };
    }
  });
})();
"""


def in_ci() -> bool:
    return os.environ.get("CI", "").strip().lower() not in {"", "0", "false", "no"}


def skip_missing_playwright() -> int:
    if in_ci():
        print(
            "FAIL repair_undo_smoke: playwright is not importable; "
            "CI must not skip this test.",
            flush=True,
        )
        return 1
    print(
        "SKIP repair_undo_smoke: playwright is not importable. "
        "Use builds/pwvenv/Scripts/python.exe.",
        flush=True,
    )
    return SKIP


try:
    from playwright.sync_api import sync_playwright
except ImportError:
    raise SystemExit(skip_missing_playwright())

import deploy_smoke


def read_state(page: Any) -> dict[str, Any]:
    state = page.evaluate("() => window.__cadcamExportState || null")
    return state if isinstance(state, dict) else {}


def read_mesh_and_validity(page: Any) -> dict[str, Any]:
    snap = page.evaluate(
        """() => {
          const s = window.__cadcamExportState || {};
          const mod = window.__cadcamTestModule || null;
          const pos = mod && typeof mod.meshPositions === 'function'
            ? Array.from(mod.meshPositions())
            : [];
          const idx = mod && typeof mod.meshIndices === 'function'
            ? Array.from(mod.meshIndices())
            : [];
          const unitsEl = document.getElementById('statusUnits');
          const hintEl = document.getElementById('statusHint');
          return {
            positions: pos,
            indices: idx,
            watertight: s.watertight,
            meshPass: s.meshPass,
            meshMessage: s.meshMessage,
            exportAllowed: s.exportAllowed,
            blockReason: s.blockReason,
            occtGate: s.occtGate,
            gateOcct: s.gateOcct,
            unitsPass: s.unitsPass,
            statusUnits: unitsEl ? String(unitsEl.textContent || '').trim() : '',
            statusHint: hintEl ? String(hintEl.textContent || '').trim() : '',
            volumeMm3: Number(s.volumeMm3),
            cppVolumeMm3: Number(s.cppVolumeMm3),
            bodyCount: Number(s.bodyCount),
            sceneCleared: s.sceneCleared === true,
            undoDepth: Number(s.undoDepth),
            redoDepth: Number(s.redoDepth)
          };
        }"""
    )
    return snap if isinstance(snap, dict) else {}


def tap(page: Any, selector: str) -> None:
    loc = page.locator(selector).first
    if loc.is_visible():
        loc.tap()
    else:
        loc.dispatch_event("click")


def box_ok(page: Any, selector: str) -> dict[str, float] | None:
    box = page.locator(selector).first.bounding_box()
    if not box:
        return None
    return {"w": float(box["width"]), "h": float(box["height"])}


def check_controls(page: Any, kind: str, problems: list[str]) -> None:
    meta = page.evaluate(
        """() => {
          const u = document.querySelector('.topbar [data-action="undo"]');
          const r = document.querySelector('.topbar [data-action="redo"]');
          return {
            undoAria: u ? u.getAttribute('aria-label') : '',
            undoTitle: u ? (u.getAttribute('title') || u.getAttribute('data-parked-title') || '') : '',
            redoAria: r ? r.getAttribute('aria-label') : '',
            redoTitle: r ? (r.getAttribute('title') || r.getAttribute('data-parked-title') || '') : ''
          };
        }"""
    )
    if not isinstance(meta, dict):
        problems.append(f"{kind} controls meta {meta!r}")
        return
    if meta.get("undoAria") != "Undo" or meta.get("undoTitle") != "Undo":
        problems.append(f"{kind} undo attrs {meta!r}")
    if meta.get("redoAria") != "Redo" or meta.get("redoTitle") != "Redo":
        problems.append(f"{kind} redo attrs {meta!r}")
    for sel, name in (
        (".topbar [data-action='undo']", "undo"),
        (".topbar [data-action='redo']", "redo"),
    ):
        size = box_ok(page, sel)
        if not size or size["w"] + 0.5 < 44 or size["h"] + 0.5 < 44:
            problems.append(f"{kind} {name} box {size!r}")


def check_watertight_and_mm(page: Any, kind: str, label: str, problems: list[str]) -> None:
    snap = read_mesh_and_validity(page)
    if snap.get("watertight") is not True:
        problems.append(f"{kind} {label} watertight={snap.get('watertight')!r}")
    if snap.get("meshPass") is not True:
        problems.append(f"{kind} {label} meshPass={snap.get('meshPass')!r}")
    if snap.get("occtGate") is not True or snap.get("gateOcct") != "PASS":
        problems.append(
            f"{kind} {label} occtGate={snap.get('occtGate')!r} gateOcct={snap.get('gateOcct')!r}"
        )
    if snap.get("unitsPass") is not True:
        problems.append(f"{kind} {label} unitsPass={snap.get('unitsPass')!r}")
    if str(snap.get("statusUnits") or "").lower() != "mm":
        problems.append(f"{kind} {label} statusUnits={snap.get('statusUnits')!r}")


def open_tools_sheet(page: Any) -> None:
    is_open = page.evaluate(
        "() => { const s = document.getElementById('toolsSheet'); return !!(s && s.hidden === false); }"
    )
    if not is_open:
        tap(page, "[data-action='toolsMenu']")
        page.wait_for_function(
            "() => { const s = document.getElementById('toolsSheet'); return !!(s && s.hidden === false); }"
        )


def tap_repair_tool(page: Any, tool_label: str) -> None:
    tab_now = page.evaluate("() => (window.__cadcamExportState || {}).tab || ''")
    if tab_now == "repair":
        open_tools_sheet(page)
        tap(page, f"#sheetTools button:has-text('{tool_label}')")
    else:
        action = "autoHeal" if tool_label == "Auto-heal" else "meshRepair"
        tap(page, f"[data-action='{action}']")


def check_mesh_match(
    got: dict[str, Any],
    want: dict[str, Any],
    kind: str,
    stage: str,
    problems: list[str],
) -> None:
    if got.get("positions") != want.get("positions") or not got.get("positions"):
        problems.append(
            f"{kind} {stage} positions len={len(got.get('positions') or [])} "
            f"want len={len(want.get('positions') or [])}"
        )
    if got.get("indices") != want.get("indices") or not got.get("indices"):
        problems.append(
            f"{kind} {stage} indices={got.get('indices')!r} want={want.get('indices')!r}"
        )
    for key in ("watertight", "meshPass", "exportAllowed", "blockReason", "unitsPass"):
        if got.get(key) != want.get(key):
            problems.append(f"{kind} {stage} {key}={got.get(key)!r} want={want.get(key)!r}")
    if abs(float(got.get("volumeMm3") or 0.0) - float(want.get("volumeMm3") or 0.0)) > 1e-5:
        problems.append(
            f"{kind} {stage} volumeMm3={got.get('volumeMm3')!r} want={want.get('volumeMm3')!r}"
        )
    if abs(float(got.get("cppVolumeMm3") or 0.0) - float(want.get("cppVolumeMm3") or 0.0)) > 1e-5:
        problems.append(
            f"{kind} {stage} cppVolumeMm3={got.get('cppVolumeMm3')!r} want={want.get('cppVolumeMm3')!r}"
        )
    if str(got.get("statusUnits") or "").lower() != "mm":
        problems.append(f"{kind} {stage} statusUnits={got.get('statusUnits')!r}")


def run_flipped_box_case(page: Any, kind: str, origin: str) -> list[str]:
    problems: list[str] = []
    url = origin + "/?fixture=flipped_box&tab=repair"
    print(f"load {kind} {url}", flush=True)
    page.goto(url, wait_until="domcontentloaded", timeout=deploy_smoke.PAGE_TIMEOUT_S * 1000)
    page.wait_for_function(
        """() => {
          const s = window.__cadcamExportState;
          const mod = window.__cadcamTestModule;
          return !!(s && mod && s.occtReady === true
            && s.fixture === 'flipped_box'
            && s.sceneCleared === false
            && s.undoDepth === 0 && s.redoDepth === 0
            && s.watertight === false && s.meshPass === false
            && s.exportAllowed === false && s.unitsPass === true
            && Math.abs(Number(s.volumeMm3) + 1.0) < 1e-6);
        }"""
    )
    check_controls(page, kind, problems)
    pre_snap = read_mesh_and_validity(page)
    if pre_snap.get("statusUnits", "").lower() != "mm":
        problems.append(f"{kind} flipped_box initial units {pre_snap.get('statusUnits')!r}")
    if problems:
        return problems

    # 1. Auto-heal repairs the broken mesh and pushes 1 undo step.
    tap_repair_tool(page, "Auto-heal")
    page.wait_for_function(
        """() => {
          const s = window.__cadcamExportState || {};
          const hint = document.getElementById('statusHint');
          const text = hint ? String(hint.textContent || '') : '';
          return s.undoDepth === 1 && s.redoDepth === 0
            && s.sceneCleared === false
            && s.watertight === true && s.meshPass === true
            && s.occtGate === true && s.gateOcct === 'PASS'
            && s.exportAllowed === true && s.unitsPass === true
            && Math.abs(Number(s.volumeMm3) - 1.0) < 1e-6
            && text.indexOf('Repaired. ') === 0;
        }"""
    )
    repaired_snap = read_mesh_and_validity(page)
    check_watertight_and_mm(page, kind, "after-auto-heal", problems)
    if repaired_snap.get("indices") == pre_snap.get("indices"):
        problems.append(f"{kind} auto-heal did not change triangle winding indices")

    # 2. Repair on a clean mesh pushes no undo step.
    tap_repair_tool(page, "Auto-heal")
    page.wait_for_function(
        """() => {
          const s = window.__cadcamExportState || {};
          const hint = document.getElementById('statusHint');
          const text = hint ? String(hint.textContent || '') : '';
          return s.undoDepth === 1 && s.redoDepth === 0
            && s.watertight === true && s.unitsPass === true
            && text.indexOf('PASS: ') === 0;
        }"""
    )
    tap_repair_tool(page, "Mesh repair")
    page.wait_for_function(
        """() => {
          const s = window.__cadcamExportState || {};
          const hint = document.getElementById('statusHint');
          const text = hint ? String(hint.textContent || '') : '';
          return s.undoDepth === 1 && s.redoDepth === 0
            && s.watertight === true && s.unitsPass === true
            && text.indexOf('PASS: ') === 0;
        }"""
    )

    # 3. Undo Auto-heal: mesh and validity status match pre-repair (via !sceneCleared L6581 path).
    tap(page, ".topbar [data-action='undo']")
    page.wait_for_function(
        """() => {
          const s = window.__cadcamExportState || {};
          const hint = document.getElementById('statusHint');
          return s.undoDepth === 0 && s.redoDepth === 1
            && s.sceneCleared === false
            && s.watertight === false && s.meshPass === false
            && s.exportAllowed === false && s.unitsPass === true
            && Math.abs(Number(s.volumeMm3) + 1.0) < 1e-6
            && hint && String(hint.textContent || '').trim() === 'Undo Auto-heal';
        }"""
    )
    undo_snap = read_mesh_and_validity(page)
    check_mesh_match(undo_snap, pre_snap, kind, "undo-auto-heal", problems)

    # 4. Redo Auto-heal: restores the repaired mesh, watertight and mm hold.
    tap(page, ".topbar [data-action='redo']")
    page.wait_for_function(
        """() => {
          const s = window.__cadcamExportState || {};
          const hint = document.getElementById('statusHint');
          return s.undoDepth === 1 && s.redoDepth === 0
            && s.sceneCleared === false
            && s.watertight === true && s.meshPass === true
            && s.occtGate === true && s.gateOcct === 'PASS'
            && s.exportAllowed === true && s.unitsPass === true
            && Math.abs(Number(s.volumeMm3) - 1.0) < 1e-6
            && hint && String(hint.textContent || '').trim() === 'Redo Auto-heal';
        }"""
    )
    redo_snap = read_mesh_and_validity(page)
    check_mesh_match(redo_snap, repaired_snap, kind, "redo-auto-heal", problems)
    check_watertight_and_mm(page, kind, "redo-auto-heal-gate", problems)

    # 5. Undo back to broken, then repair with 'Mesh repair' button to verify its label.
    tap(page, ".topbar [data-action='undo']")
    page.wait_for_function(
        """() => {
          const s = window.__cadcamExportState || {};
          return s.undoDepth === 0 && s.redoDepth === 1 && s.watertight === false;
        }"""
    )
    tap(page, "[data-action='meshRepair']")
    page.wait_for_function(
        """() => {
          const s = window.__cadcamExportState || {};
          const hint = document.getElementById('statusHint');
          const text = hint ? String(hint.textContent || '') : '';
          return s.undoDepth === 1 && s.redoDepth === 0
            && s.watertight === true && s.meshPass === true
            && Math.abs(Number(s.volumeMm3) - 1.0) < 1e-6
            && text.indexOf('Repaired. ') === 0;
        }"""
    )
    tap(page, ".topbar [data-action='undo']")
    page.wait_for_function(
        """() => {
          const s = window.__cadcamExportState || {};
          const hint = document.getElementById('statusHint');
          return s.undoDepth === 0 && s.redoDepth === 1
            && s.watertight === false && s.meshPass === false
            && hint && String(hint.textContent || '').trim() === 'Undo Mesh repair';
        }"""
    )
    check_mesh_match(read_mesh_and_validity(page), pre_snap, kind, "undo-mesh-repair", problems)

    tap(page, ".topbar [data-action='redo']")
    page.wait_for_function(
        """() => {
          const s = window.__cadcamExportState || {};
          const hint = document.getElementById('statusHint');
          return s.undoDepth === 1 && s.redoDepth === 0
            && s.watertight === true && s.meshPass === true
            && hint && String(hint.textContent || '').trim() === 'Redo Mesh repair';
        }"""
    )
    check_mesh_match(read_mesh_and_validity(page), repaired_snap, kind, "redo-mesh-repair", problems)
    check_watertight_and_mm(page, kind, "redo-mesh-repair-gate", problems)
    return problems


def run_extrude_and_scene_cleared_case(page: Any, kind: str, origin: str) -> list[str]:
    problems: list[str] = []
    url = origin + "/"
    print(f"load {kind} {url}", flush=True)
    page.goto(url, wait_until="domcontentloaded", timeout=deploy_smoke.PAGE_TIMEOUT_S * 1000)
    page.wait_for_function(
        """() => {
          const s = window.__cadcamExportState;
          const mod = window.__cadcamTestModule;
          return !!(s && mod && s.occtReady === true && window.__cadcamSketch
            && s.sceneCleared === true && s.bodyCount === 0
            && s.undoDepth === 0 && s.redoDepth === 0
            && Number(s.volumeMm3) === 0);
        }"""
    )

    # 1. Repair on cleared scene pushes no undo step and stays sceneCleared.
    tap_repair_tool(page, "Auto-heal")
    page.wait_for_function(
        """() => {
          const s = window.__cadcamExportState || {};
          return s.sceneCleared === true && s.bodyCount === 0
            && s.undoDepth === 0 && s.redoDepth === 0;
        }"""
    )

    # 2. Sketch a 10x10 rectangle on the Top (XY) origin plane and Extrude 10 mm New.
    open_tools_sheet(page)
    tap(page, "#toolsSheet [data-action='createMenu']")
    page.wait_for_function(
        "() => { const m = document.getElementById('createMenu'); return !!(m && m.hidden === false); }"
    )
    tap(page, "#createMenu [data-action='newSketch']")
    page.wait_for_function(
        "() => !!(window.__cadcamSketch && window.__cadcamSketch.state().tab === 'sketch')"
    )
    tap(page, "#originPlanes [data-action='originPlane'][data-plane='xy']")
    page.wait_for_function(
        """() => {
          const st = window.__cadcamSketch ? window.__cadcamSketch.state() : null;
          return !!(st && st.plane === true && st.originPlane === 'xy');
        }"""
    )
    open_tools_sheet(page)
    tap(page, "#sheetTools button:has-text('Rectangle')")
    page.wait_for_function(
        """() => {
          const s = window.__cadcamExportState || {};
          const row = document.getElementById('sketchRectRow');
          return s.sketchSheetOpen === true && !!(row && row.hidden === false);
        }"""
    )
    page.locator("#sketchL").fill("10")
    page.locator("#sketchW").fill("10")
    page.wait_for_function(
        """() => {
          const l = document.getElementById('sketchL');
          const w = document.getElementById('sketchW');
          return !!(l && w && l.value === '10' && w.value === '10');
        }"""
    )
    tap(page, "#sketchConfirm")
    page.wait_for_function(
        """() => {
          const st = window.__cadcamSketch ? window.__cadcamSketch.state() : null;
          return !!(st && st.closed === true && st.profile === 'rect');
        }"""
    )
    tap(page, "#finishBar [data-action='finishSketch']")
    page.wait_for_function(
        """() => {
          const st = window.__cadcamSketch ? window.__cadcamSketch.state() : null;
          return !!(st && st.tab === 'model' && st.closed === true);
        }"""
    )
    open_tools_sheet(page)
    tap(page, "#sheetTools button:has-text('Extrude (Push/Pull)')")
    page.wait_for_function(
        """() => {
          const s = window.__cadcamExportState || {};
          const depthRow = document.getElementById('sketchDepthRow');
          return s.sketchSheetOpen === true && !!(depthRow && depthRow.hidden === false);
        }"""
    )
    page.locator("#sketchDepth").fill("10")
    page.wait_for_function(
        "() => { const el = document.getElementById('sketchDepth'); return !!(el && el.value === '10'); }"
    )
    tap(page, "#sketchModeRow [data-mode='new']")
    page.wait_for_function(
        "() => !!(window.__cadcamSketch && window.__cadcamSketch.state().extrudeMode === 'new')"
    )
    tap(page, "#sketchConfirm")
    page.wait_for_function(
        """() => {
          const s = window.__cadcamExportState || {};
          return s.undoDepth === 1 && s.redoDepth === 0
            && s.sceneCleared === false && s.bodyCount === 1
            && Math.abs(Number(s.volumeMm3) - 1000) < 0.5
            && s.watertight === true && s.meshPass === true
            && s.occtGate === true && s.gateOcct === 'PASS'
            && s.unitsPass === true;
        }"""
    )
    check_watertight_and_mm(page, kind, "after-extrude", problems)

    # 3. Repair on the clean extruded mesh pushes no undo step.
    tap_repair_tool(page, "Auto-heal")
    page.wait_for_function(
        """() => {
          const s = window.__cadcamExportState || {};
          const hint = document.getElementById('statusHint');
          const text = hint ? String(hint.textContent || '') : '';
          return s.undoDepth === 1 && s.redoDepth === 0
            && s.bodyCount === 1 && s.sceneCleared === false
            && text.indexOf('PASS: ') === 0;
        }"""
    )

    # 4. Break the kernel mesh (flip winding of the extruded prism), then repair -> Undo removes only the repair.
    page.evaluate(
        """() => {
          const mod = window.__cadcamTestModule;
          const pos = mod.meshPositions();
          const idx = mod.meshIndices();
          const flipped = new Uint32Array(idx.length);
          for (let i = 0; i + 2 < idx.length; i += 3) {
            flipped[i] = idx[i];
            flipped[i + 1] = idx[i + 2];
            flipped[i + 2] = idx[i + 1];
          }
          mod.replaceMesh(pos, flipped, mod.fixtureName());
          const checkBtn = document.querySelector('[data-action="checkShape"]');
          if (checkBtn) checkBtn.click();
        }"""
    )
    page.wait_for_function(
        """() => {
          const s = window.__cadcamExportState || {};
          return s.undoDepth === 1 && s.redoDepth === 0
            && s.bodyCount === 1 && s.sceneCleared === false
            && s.watertight === false && s.meshPass === false
            && s.exportAllowed === false
            && Math.abs(Number(s.volumeMm3) - 1000) < 0.5
            && Math.abs(Number(s.cppVolumeMm3) + 1000) < 0.5;
        }"""
    )
    extrude_broken_snap = read_mesh_and_validity(page)

    tap_repair_tool(page, "Auto-heal")
    page.wait_for_function(
        """() => {
          const s = window.__cadcamExportState || {};
          const hint = document.getElementById('statusHint');
          const text = hint ? String(hint.textContent || '') : '';
          return s.undoDepth === 2 && s.redoDepth === 0
            && s.bodyCount === 1 && s.sceneCleared === false
            && s.watertight === true && s.meshPass === true
            && s.occtGate === true && s.gateOcct === 'PASS'
            && s.exportAllowed === true && s.unitsPass === true
            && Math.abs(Number(s.volumeMm3) - 1000) < 0.5
            && Math.abs(Number(s.cppVolumeMm3) - 1000) < 0.5
            && text.indexOf('Repaired. ') === 0;
        }"""
    )
    extrude_repaired_snap = read_mesh_and_validity(page)
    check_watertight_and_mm(page, kind, "extrude-then-repair", problems)

    # First Undo removes ONLY the repair (bodyCount stays 1, mesh returns to pre-repair broken state via L6581).
    tap(page, ".topbar [data-action='undo']")
    page.wait_for_function(
        """() => {
          const s = window.__cadcamExportState || {};
          const hint = document.getElementById('statusHint');
          return s.undoDepth === 1 && s.redoDepth === 1
            && s.bodyCount === 1 && s.sceneCleared === false
            && s.watertight === false && s.meshPass === false
            && s.exportAllowed === false && s.unitsPass === true
            && Math.abs(Number(s.volumeMm3) - 1000) < 0.5
            && Math.abs(Number(s.cppVolumeMm3) + 1000) < 0.5
            && hint && String(hint.textContent || '').trim() === 'Undo Auto-heal';
        }"""
    )
    after_first_undo = read_mesh_and_validity(page)
    if after_first_undo.get("bodyCount") != 1:
        problems.append(f"{kind} first undo removed extrude body: {after_first_undo.get('bodyCount')!r}")
    check_mesh_match(after_first_undo, extrude_broken_snap, kind, "extrude-repair-undo", problems)

    # Second Undo removes the Extrude and restores the sceneCleared=true snapshot path.
    tap(page, ".topbar [data-action='undo']")
    page.wait_for_function(
        """() => {
          const s = window.__cadcamExportState || {};
          const hint = document.getElementById('statusHint');
          return s.undoDepth === 0 && s.redoDepth === 2
            && s.bodyCount === 0 && s.sceneCleared === true
            && Number(s.volumeMm3) === 0
            && hint && String(hint.textContent || '').trim() === 'Undo Extrude';
        }"""
    )

    # First Redo restores the Extrude (sceneCleared=false -> L6581 path), watertight and mm hold.
    tap(page, ".topbar [data-action='redo']")
    page.wait_for_function(
        """() => {
          const s = window.__cadcamExportState || {};
          const hint = document.getElementById('statusHint');
          return s.undoDepth === 1 && s.redoDepth === 1
            && s.bodyCount === 1 && s.sceneCleared === false
            && s.watertight === true && s.meshPass === true
            && s.occtGate === true && s.gateOcct === 'PASS'
            && s.unitsPass === true
            && Math.abs(Number(s.volumeMm3) - 1000) < 0.5
            && hint && String(hint.textContent || '').trim() === 'Redo Extrude';
        }"""
    )
    check_watertight_and_mm(page, kind, "redo-extrude-from-cleared", problems)

    # Second Redo restores the repair, watertight and mm hold.
    tap(page, ".topbar [data-action='redo']")
    page.wait_for_function(
        """() => {
          const s = window.__cadcamExportState || {};
          const hint = document.getElementById('statusHint');
          return s.undoDepth === 2 && s.redoDepth === 0
            && s.bodyCount === 1 && s.sceneCleared === false
            && s.watertight === true && s.meshPass === true
            && s.occtGate === true && s.gateOcct === 'PASS'
            && s.exportAllowed === true && s.unitsPass === true
            && Math.abs(Number(s.volumeMm3) - 1000) < 0.5
            && hint && String(hint.textContent || '').trim() === 'Redo Auto-heal';
        }"""
    )
    check_mesh_match(
        read_mesh_and_validity(page),
        extrude_repaired_snap,
        kind,
        "extrude-repair-redo",
        problems,
    )
    check_watertight_and_mm(page, kind, "redo-repair-after-extrude", problems)
    check_controls(page, kind, problems)
    return problems


def check_failed_repair_step(
    got: dict[str, Any],
    want: dict[str, Any],
    want_v: int,
    want_t: int,
    want_hint: str,
    kind: str,
    stage: str,
    problems: list[str],
    check_hint: bool = True,
) -> None:
    got_v = len(got.get("positions") or []) // 3
    got_t = len(got.get("indices") or []) // 3
    if got_v != want_v or got_t != want_t:
        problems.append(
            f"{kind} {stage} counts v={got_v} (want {want_v}) t={got_t} (want {want_t})"
        )
    check_mesh_match(got, want, kind, stage, problems)
    if got.get("undoDepth") != 0 or got.get("redoDepth") != 0:
        problems.append(
            f"{kind} {stage} undo={got.get('undoDepth')!r} redo={got.get('redoDepth')!r}"
        )
    if got.get("watertight") is not False:
        problems.append(f"{kind} {stage} watertight={got.get('watertight')!r}")
    if got.get("unitsPass") is not True or str(got.get("statusUnits") or "").lower() != "mm":
        problems.append(
            f"{kind} {stage} units={got.get('statusUnits')!r} unitsPass={got.get('unitsPass')!r}"
        )
    if check_hint and got.get("statusHint") != want_hint:
        problems.append(
            f"{kind} {stage} statusHint={got.get('statusHint')!r} want={want_hint!r}"
        )


def run_open_box_probe_case(page: Any, kind: str, origin: str) -> list[str]:
    problems: list[str] = []
    url = origin + "/?fixture=open_box&tab=repair"
    print(f"load {kind} {url}", flush=True)
    page.goto(url, wait_until="domcontentloaded", timeout=deploy_smoke.PAGE_TIMEOUT_S * 1000)
    page.wait_for_function(
        """() => {
          const s = window.__cadcamExportState;
          const mod = window.__cadcamTestModule;
          return !!(s && mod && s.occtReady === true
            && s.fixture === 'open_box'
            && s.sceneCleared === false
            && s.undoDepth === 0 && s.redoDepth === 0
            && s.watertight === false
            && s.unitsPass === true);
        }"""
    )
    pre_open = read_mesh_and_validity(page)
    if str(pre_open.get("statusUnits") or "").lower() != "mm" or pre_open.get("unitsPass") is not True:
        problems.append(
            f"{kind} open_box initial units {pre_open.get('statusUnits')!r} unitsPass={pre_open.get('unitsPass')!r}"
        )
        return problems

    open_check_msg = str(
        page.evaluate("() => String(window.__cadcamTestModule.checkShape() || '')") or ""
    )
    if not open_check_msg.startswith("FAIL: "):
        problems.append(f"{kind} open_box checkShape={open_check_msg!r}")
        return problems
    want_hint = f"cannot repair: {open_check_msg}"

    pre_v = len(pre_open.get("positions") or []) // 3
    pre_t = len(pre_open.get("indices") or []) // 3
    if pre_v != 8 or pre_t != 10:
        problems.append(f"{kind} open_box initial counts v={pre_v} t={pre_t}")
        return problems

    # 1. Plain open_box: Module.repairMesh(), Auto-heal, and Mesh repair leave g_mesh and undo stack untouched.
    direct_msg = page.evaluate("() => String(window.__cadcamTestModule.repairMesh() || '')")
    if direct_msg != want_hint:
        problems.append(f"{kind} open_box Module.repairMesh msg={direct_msg!r} want={want_hint!r}")
    after_direct = read_mesh_and_validity(page)
    check_failed_repair_step(
        after_direct,
        pre_open,
        8,
        10,
        want_hint,
        kind,
        "open_box-direct",
        problems,
        check_hint=False,
    )

    page.evaluate("() => { const h = document.getElementById('statusHint'); if (h) h.textContent = ''; }")
    tap_repair_tool(page, "Auto-heal")
    page.wait_for_function(
        """() => {
          const s = window.__cadcamExportState || {};
          const hint = document.getElementById('statusHint');
          const text = hint ? String(hint.textContent || '') : '';
          return s.undoDepth === 0 && s.redoDepth === 0
            && s.watertight === false && s.unitsPass === true
            && text.indexOf('cannot repair: ') === 0;
        }"""
    )
    after_autoheal = read_mesh_and_validity(page)
    check_failed_repair_step(
        after_autoheal,
        pre_open,
        8,
        10,
        want_hint,
        kind,
        "open_box-auto-heal",
        problems,
    )

    page.evaluate("() => { const h = document.getElementById('statusHint'); if (h) h.textContent = ''; }")
    tap(page, "[data-action='meshRepair']")
    page.wait_for_function(
        """() => {
          const s = window.__cadcamExportState || {};
          const hint = document.getElementById('statusHint');
          const text = hint ? String(hint.textContent || '') : '';
          return s.undoDepth === 0 && s.redoDepth === 0
            && s.watertight === false && s.unitsPass === true
            && text.indexOf('cannot repair: ') === 0;
        }"""
    )
    post_open = read_mesh_and_validity(page)
    check_failed_repair_step(
        post_open,
        pre_open,
        8,
        10,
        want_hint,
        kind,
        "open_box-mesh-repair",
        problems,
    )
    post_v = len(post_open.get("positions") or []) // 3
    post_t = len(post_open.get("indices") or []) // 3
    print(
        f"GATE {kind} g_mesh open_box (clean vertices): "
        f"vertices {pre_v}->{post_v}, triangles {pre_t}->{post_t}, "
        f"undoDepth={post_open.get('undoDepth')}, redoDepth={post_open.get('redoDepth')}",
        flush=True,
    )

    # 2. Open box with 1 duplicate vertex (9 vertices, 10 triangles):
    # weld_exact runs inside repair_manifold before check_watertight fails,
    # and bindings.cpp repair_mesh() assigns g_mesh = result.mesh only when
    # result.pass is true, leaving g_mesh untouched on failed repair.
    def seed_open_box_with_dup_vertex() -> dict[str, Any]:
        page.evaluate(
            """() => {
              const mod = window.__cadcamTestModule;
              mod.loadFixture('open_box');
              const pos = Array.from(mod.meshPositions());
              const idx = Array.from(mod.meshIndices());
              const dupIndex = pos.length / 3;
              pos.push(pos[0], pos[1], pos[2]);
              idx[0] = dupIndex;
              mod.replaceMesh(new Float64Array(pos), new Uint32Array(idx), 'open_box');
              const checkBtn = document.querySelector('[data-action="checkShape"]');
              if (checkBtn) checkBtn.click();
            }"""
        )
        page.wait_for_function(
            """() => {
              const s = window.__cadcamExportState || {};
              const mod = window.__cadcamTestModule;
              const hint = document.getElementById('statusHint');
              const text = hint ? String(hint.textContent || '') : '';
              return !!(mod && mod.meshPositions().length === 27
                && mod.meshIndices().length === 30
                && s.undoDepth === 0 && s.redoDepth === 0
                && s.watertight === false && s.unitsPass === true
                && text.indexOf('FAIL: ') === 0);
            }"""
        )
        return read_mesh_and_validity(page)

    pre_dup_direct = seed_open_box_with_dup_vertex()
    dup_msg = page.evaluate("() => String(window.__cadcamTestModule.repairMesh() || '')")
    if dup_msg != want_hint:
        problems.append(
            f"{kind} open_box+dup Module.repairMesh msg={dup_msg!r} want={want_hint!r}"
        )
    post_dup_direct = read_mesh_and_validity(page)
    check_failed_repair_step(
        post_dup_direct,
        pre_dup_direct,
        9,
        10,
        want_hint,
        kind,
        "open_box_dup-direct",
        problems,
        check_hint=False,
    )

    pre_dup_auto = seed_open_box_with_dup_vertex()
    tap_repair_tool(page, "Auto-heal")
    page.wait_for_function(
        """() => {
          const s = window.__cadcamExportState || {};
          const hint = document.getElementById('statusHint');
          const text = hint ? String(hint.textContent || '') : '';
          return s.undoDepth === 0 && s.redoDepth === 0
            && s.watertight === false && s.unitsPass === true
            && text.indexOf('cannot repair: ') === 0;
        }"""
    )
    post_dup_auto = read_mesh_and_validity(page)
    check_failed_repair_step(
        post_dup_auto,
        pre_dup_auto,
        9,
        10,
        want_hint,
        kind,
        "open_box_dup-auto-heal",
        problems,
    )

    pre_dup_mesh = seed_open_box_with_dup_vertex()
    tap(page, "[data-action='meshRepair']")
    page.wait_for_function(
        """() => {
          const s = window.__cadcamExportState || {};
          const hint = document.getElementById('statusHint');
          const text = hint ? String(hint.textContent || '') : '';
          return s.undoDepth === 0 && s.redoDepth === 0
            && s.watertight === false && s.unitsPass === true
            && text.indexOf('cannot repair: ') === 0;
        }"""
    )
    post_dup_mesh = read_mesh_and_validity(page)
    check_failed_repair_step(
        post_dup_mesh,
        pre_dup_mesh,
        9,
        10,
        want_hint,
        kind,
        "open_box_dup-mesh-repair",
        problems,
    )

    dup_pre_v = len(pre_dup_mesh.get("positions") or []) // 3
    dup_pre_t = len(pre_dup_mesh.get("indices") or []) // 3
    dup_post_v = len(post_dup_mesh.get("positions") or []) // 3
    dup_post_t = len(post_dup_mesh.get("indices") or []) // 3
    print(
        f"GATE {kind} g_mesh open_box+dup_vertices (Module.repairMesh / Auto-heal / Mesh repair): "
        f"vertices {dup_pre_v}->{dup_post_v}, triangles {dup_pre_t}->{dup_post_t}, "
        f"undoDepth={post_dup_mesh.get('undoDepth')}, redoDepth={post_dup_mesh.get('redoDepth')}",
        flush=True,
    )
    return problems


def run_engine(playwright: Any, engine: str, origin: str) -> list[str]:
    browser = getattr(playwright, engine).launch(headless=True)
    try:
        if engine == "webkit":
            device = dict(playwright.devices["iPhone 13"])
            device.pop("default_browser_type", None)
            device["screen"] = {"width": 390, "height": 844}
            device["viewport"] = {"width": 390, "height": 844}
            device["device_scale_factor"] = 1
            context = browser.new_context(**device)
        else:
            context = browser.new_context(
                viewport={"width": 390, "height": 844},
                device_scale_factor=1,
                is_mobile=True,
                has_touch=True,
            )
        context.add_init_script(CAPTURE_MODULE_SCRIPT)
        kind = "webkit" if engine == "webkit" else "chromium"
        page = context.new_page()
        errors: list[str] = []

        def on_pageerror(err: Any) -> None:
            errors.append(str(err))

        def on_console(msg: Any) -> None:
            if msg.type not in {"error", "assert"}:
                return
            text = str(msg.text or "")
            if "interactive-widget" in text and "not recognized" in text:
                return
            errors.append(text)

        page.on("pageerror", on_pageerror)
        page.on("console", on_console)
        page.set_default_timeout(deploy_smoke.PAGE_TIMEOUT_S * 1000)
        problems = run_flipped_box_case(page, kind, origin)
        if not problems:
            problems = run_open_box_probe_case(page, kind, origin)
        if not problems:
            problems = run_extrude_and_scene_cleared_case(page, kind, origin)
        if errors:
            problems = [f"{kind} js: {item}" for item in errors[:8]] + problems
        if problems:
            return [f"{kind} 390x844", *problems]
        print(f"PASS repair_undo_smoke {kind}", flush=True)
        return []
    finally:
        browser.close()


def run() -> int:
    gaps = deploy_smoke.libcascade_gaps()
    if gaps:
        text = "; ".join(gaps)
        if in_ci():
            print(f"FAIL repair_undo_smoke: {text}", flush=True)
            print("CI must not skip repair_undo_smoke.", flush=True)
            return 1
        print("SKIP repair_undo_smoke: " + text, flush=True)
        return SKIP
    assembler = deploy_smoke.load_assembler()
    site = WORK / "_site"
    WORK.mkdir(parents=True, exist_ok=True)
    assembler.assemble(site, [])
    print(f"assembled {site}", flush=True)
    http_port = deploy_smoke.free_port()
    origin = f"http://127.0.0.1:{http_port}"

    def handler(*args: Any, **kwargs: Any) -> deploy_smoke.SiteHandler:
        return deploy_smoke.SiteHandler(*args, directory=str(site), **kwargs)

    server = deploy_smoke.ThreadingHTTPServer(("127.0.0.1", http_port), handler)
    thread = threading.Thread(target=server.serve_forever, name="repair-undo-http", daemon=True)
    thread.start()
    try:
        with sync_playwright() as playwright:
            for engine in ("chromium", "webkit"):
                problems = run_engine(playwright, engine, origin)
                if problems:
                    print("FAIL repair_undo_smoke", flush=True)
                    for line in problems:
                        print(line, flush=True)
                    return 1
        print("PASS repair_undo_smoke", flush=True)
        return 0
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=5)


def main() -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    try:
        return run()
    except SystemExit as exc:
        if isinstance(exc.code, int):
            return exc.code
        print(f"FAIL repair_undo_smoke: {exc}", flush=True)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
