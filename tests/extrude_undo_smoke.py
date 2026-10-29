#!/usr/bin/env python3
"""Phone Extrude Undo/Redo smoke (390x844, Chromium and WebKit).

Verifies:
- New, Join, Cut: each Undo returns body count and volume to pre-extrude values;
  Redo restores post-extrude values.
- A failed extrude pushes nothing onto the undo stack.
- Hole -> Extrude -> Undo removes only the Extrude.
- Open sketch sheet (extrude and profile), Undo/Redo: sheet closes
  (state.sketchSheetMode falsy, #sketchSheet hidden), prior/redo scene restored,
  and the next Confirm cannot extrude onto the restored scene.
- After Undo and Redo: validity gate passes (watertight) and units stay mm.
- Undo/Redo controls, labels, and Confirm button stay unchanged (>= 44x44 CSS px).

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
WORK = ROOT / "builds" / "extrude-undo-smoke"
SKIP = 77


def in_ci() -> bool:
    return os.environ.get("CI", "").strip().lower() not in {"", "0", "false", "no"}


def skip_missing_playwright() -> int:
    if in_ci():
        print(
            "FAIL extrude_undo_smoke: playwright is not importable; "
            "CI must not skip this test.",
            flush=True,
        )
        return 1
    print(
        "SKIP extrude_undo_smoke: playwright is not importable. "
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


def volume_of(state: dict[str, Any]) -> float:
    try:
        return float(state.get("volumeMm3"))
    except (TypeError, ValueError):
        return float("nan")


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


def check_confirm_btn(page: Any, kind: str, stage: str, problems: list[str]) -> None:
    text = (page.locator("#sketchConfirm").text_content() or "").strip()
    if text != "Confirm":
        problems.append(f"{kind} {stage} confirm label {text!r}")
    size = box_ok(page, "#sketchConfirm")
    if not size or size["w"] + 0.5 < 44 or size["h"] + 0.5 < 44:
        problems.append(f"{kind} {stage} confirm box {size!r}")


def check_gate_and_units(page: Any, kind: str, label: str, problems: list[str]) -> None:
    state = read_state(page)
    if state.get("occtGate") is not True or state.get("gateOcct") != "PASS":
        problems.append(
            f"{kind} {label} occtGate={state.get('occtGate')!r} "
            f"gateOcct={state.get('gateOcct')!r} msg={state.get('occtMessage')!r}"
        )
    if state.get("watertight") is not True:
        problems.append(f"{kind} {label} watertight={state.get('watertight')!r}")
    if state.get("unitsPass") is not True:
        problems.append(f"{kind} {label} unitsPass={state.get('unitsPass')!r}")
    units_text = (page.locator("#statusUnits").text_content() or "").strip()
    if units_text.lower() != "mm":
        problems.append(f"{kind} {label} statusUnits={units_text!r}")


def open_tools_sheet(page: Any) -> None:
    is_open = page.evaluate(
        "() => { const s = document.getElementById('toolsSheet'); return !!(s && s.hidden === false); }"
    )
    if not is_open:
        tap(page, "[data-action='toolsMenu']")
        page.wait_for_function(
            "() => { const s = document.getElementById('toolsSheet'); return !!(s && s.hidden === false); }"
        )


def open_create_menu(page: Any) -> None:
    open_tools_sheet(page)
    tap(page, "#toolsSheet [data-action='createMenu']")
    page.wait_for_function(
        "() => { const m = document.getElementById('createMenu'); return !!(m && m.hidden === false); }"
    )


def sketch_rect_and_open_extrude(page: Any, kind: str, problems: list[str]) -> None:
    open_create_menu(page)
    tap(page, "#createMenu [data-action='newSketch']")
    page.wait_for_function(
        "() => !!(window.__cadcamSketch && window.__cadcamSketch.state().tab === 'sketch')"
    )
    tapped = page.evaluate(
        "() => window.__cadcamSketch.tapFace(window.__cadcamSketch.topFace())"
    )
    if tapped is not True:
        problems.append(f"{kind} tapFace {tapped!r}")
        return
    page.wait_for_function(
        """() => {
          const st = window.__cadcamSketch ? window.__cadcamSketch.state() : null;
          return !!(st && st.plane === true && st.faceId);
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
    check_confirm_btn(page, kind, "rect", problems)
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
          const modeRow = document.getElementById('sketchModeRow');
          return s.sketchSheetOpen === true
            && !!(depthRow && depthRow.hidden === false)
            && !!(modeRow && modeRow.hidden === false);
        }"""
    )
    check_confirm_btn(page, kind, "extrude", problems)


def set_extrude_mode(page: Any, mode: str) -> None:
    tap(page, f"#sketchModeRow [data-mode='{mode}']")
    page.wait_for_function(
        """(want) => {
          const st = window.__cadcamSketch ? window.__cadcamSketch.state() : null;
          return !!(st && st.extrudeMode === want);
        }""",
        arg=mode,
    )


def set_extrude_depth(page: Any, depth_str: str) -> None:
    page.locator("#sketchDepth").fill(depth_str)
    page.wait_for_function(
        """(want) => {
          const el = document.getElementById('sketchDepth');
          return !!(el && el.value === want);
        }""",
        arg=depth_str,
    )


def wait_extrude_state(
    page: Any,
    *,
    undo_depth: int,
    redo_depth: int,
    bodies: int,
    volume: float,
    tol: float = 0.5,
) -> dict[str, Any]:
    page.wait_for_function(
        """(spec) => {
          const s = window.__cadcamExportState || {};
          const vol = Number(s.volumeMm3);
          return s.undoDepth === spec.undo
            && s.redoDepth === spec.redo
            && s.bodyCount === spec.bodies
            && Number.isFinite(vol)
            && Math.abs(vol - spec.vol) <= spec.tol
            && s.occtGate === true
            && s.gateOcct === 'PASS'
            && s.watertight === true
            && s.unitsPass === true;
        }""",
        arg={
            "undo": undo_depth,
            "redo": redo_depth,
            "bodies": bodies,
            "vol": volume,
            "tol": tol,
        },
    )
    return read_state(page)


def run_case(page: Any, kind: str) -> list[str]:
    problems: list[str] = []
    page.wait_for_function(
        """() => {
          const s = window.__cadcamExportState;
          const vol = s ? Number(s.volumeMm3) : NaN;
          return !!(s && s.occtReady === true && window.__cadcamSketch
            && s.bodyCount === 1 && s.undoDepth === 0 && s.redoDepth === 0
            && s.occtGate === true && s.gateOcct === 'PASS'
            && s.watertight === true && s.unitsPass === true
            && Math.abs(vol - 8000) < 0.5);
        }"""
    )
    check_controls(page, kind, problems)
    check_gate_and_units(page, kind, "initial", problems)
    if problems:
        return problems

    # 1. Failed extrude pushes nothing onto the undo stack, then New Extrude -> Undo -> Redo.
    sketch_rect_and_open_extrude(page, kind, problems)
    if problems:
        return problems
    set_extrude_depth(page, "0")
    tap(page, "#sketchConfirm")
    page.wait_for_function(
        """() => {
          const s = window.__cadcamExportState || {};
          return s.undoDepth === 0 && s.redoDepth === 0
            && s.bodyCount === 1 && Math.abs(Number(s.volumeMm3) - 8000) < 0.5
            && String(s.lastError || '').indexOf('Blind distance must be millimetres above 0') >= 0;
        }"""
    )
    check_gate_and_units(page, kind, "after-failed-extrude", problems)

    set_extrude_depth(page, "10")
    set_extrude_mode(page, "new")
    tap(page, "#sketchConfirm")
    wait_extrude_state(page, undo_depth=1, redo_depth=0, bodies=2, volume=9000.0)
    check_gate_and_units(page, kind, "new-extrude", problems)

    tap(page, ".topbar [data-action='undo']")
    wait_extrude_state(page, undo_depth=0, redo_depth=1, bodies=1, volume=8000.0)
    check_gate_and_units(page, kind, "new-undo", problems)

    tap(page, ".topbar [data-action='redo']")
    wait_extrude_state(page, undo_depth=1, redo_depth=0, bodies=2, volume=9000.0)
    check_gate_and_units(page, kind, "new-redo", problems)

    tap(page, ".topbar [data-action='undo']")
    wait_extrude_state(page, undo_depth=0, redo_depth=1, bodies=1, volume=8000.0)

    # 2. Join Extrude -> Undo -> Redo.
    sketch_rect_and_open_extrude(page, kind, problems)
    if problems:
        return problems
    set_extrude_depth(page, "10")
    set_extrude_mode(page, "join")
    tap(page, "#sketchConfirm")
    wait_extrude_state(page, undo_depth=1, redo_depth=0, bodies=1, volume=9000.0)
    check_gate_and_units(page, kind, "join-extrude", problems)

    tap(page, ".topbar [data-action='undo']")
    wait_extrude_state(page, undo_depth=0, redo_depth=1, bodies=1, volume=8000.0)
    check_gate_and_units(page, kind, "join-undo", problems)

    tap(page, ".topbar [data-action='redo']")
    wait_extrude_state(page, undo_depth=1, redo_depth=0, bodies=1, volume=9000.0)
    check_gate_and_units(page, kind, "join-redo", problems)

    tap(page, ".topbar [data-action='undo']")
    wait_extrude_state(page, undo_depth=0, redo_depth=1, bodies=1, volume=8000.0)

    # 3. Cut Extrude -> Undo -> Redo.
    sketch_rect_and_open_extrude(page, kind, problems)
    if problems:
        return problems
    set_extrude_depth(page, "10")
    set_extrude_mode(page, "cut")
    tap(page, "#sketchConfirm")
    wait_extrude_state(page, undo_depth=1, redo_depth=0, bodies=1, volume=7000.0)
    check_gate_and_units(page, kind, "cut-extrude", problems)

    tap(page, ".topbar [data-action='undo']")
    wait_extrude_state(page, undo_depth=0, redo_depth=1, bodies=1, volume=8000.0)
    check_gate_and_units(page, kind, "cut-undo", problems)

    tap(page, ".topbar [data-action='redo']")
    wait_extrude_state(page, undo_depth=1, redo_depth=0, bodies=1, volume=7000.0)
    check_gate_and_units(page, kind, "cut-redo", problems)

    tap(page, ".topbar [data-action='undo']")
    wait_extrude_state(page, undo_depth=0, redo_depth=1, bodies=1, volume=8000.0)

    # 4. Hole -> Extrude -> Undo removes only the Extrude.
    open_create_menu(page)
    tap(page, "#createMenu [data-action='holeTool']")
    page.wait_for_function(
        """() => {
          const s = window.__cadcamExportState || {};
          return s.holeTool === true && s.selectionMode === 'face';
        }"""
    )
    hole_face_ok = page.evaluate(
        "() => window.__cadcamSketch.tapHoleFace(window.__cadcamSketch.topFace())"
    )
    if hole_face_ok is not True:
        problems.append(f"{kind} tapHoleFace {hole_face_ok!r}")
        return problems
    page.wait_for_function(
        "() => (window.__cadcamExportState || {}).holeFaceReady === true"
    )
    dim_open = page.evaluate(
        "() => Boolean(document.getElementById('dimPanel')?.classList.contains('is-open'))"
    )
    if not dim_open:
        tap(page, "#dimToggle")
        page.wait_for_function(
            "() => Boolean(document.getElementById('dimPanel')?.classList.contains('is-open'))"
        )
    page.locator("#holeU").fill("10")
    page.locator("#holeV").fill("10")
    tap(page, "#holeApply")
    page.wait_for_function(
        """() => {
          const s = window.__cadcamExportState || {};
          const vol = Number(s.volumeMm3);
          return s.undoDepth === 1 && s.redoDepth === 0
            && s.holeCount === 1 && s.bodyCount === 1
            && Number.isFinite(vol) && vol < 7900
            && s.occtGate === true && s.gateOcct === 'PASS'
            && s.watertight === true && s.unitsPass === true
            && s.lastError === '';
        }"""
    )
    after_hole = read_state(page)
    hole_vol = volume_of(after_hole)
    check_gate_and_units(page, kind, "after-hole", problems)

    sketch_rect_and_open_extrude(page, kind, problems)
    if problems:
        return problems
    set_extrude_depth(page, "10")
    set_extrude_mode(page, "new")
    tap(page, "#sketchConfirm")
    wait_extrude_state(
        page,
        undo_depth=2,
        redo_depth=0,
        bodies=2,
        volume=hole_vol + 1000.0,
        tol=1.0,
    )
    check_gate_and_units(page, kind, "hole-then-extrude", problems)

    tap(page, ".topbar [data-action='undo']")
    wait_extrude_state(
        page,
        undo_depth=1,
        redo_depth=1,
        bodies=1,
        volume=hole_vol,
        tol=0.5,
    )
    undone_extrude = read_state(page)
    if int(undone_extrude.get("holeCount") or 0) != 1:
        problems.append(f"{kind} holeCount after extrude undo {undone_extrude.get('holeCount')!r}")
    check_gate_and_units(page, kind, "hole-extrude-undo", problems)

    # 5. Open sketch sheet -> Undo/Redo closes the sheet (sketchSheetMode falsy),
    # restores the prior/redo scene, and the next Confirm cannot extrude onto it.
    sketch_rect_and_open_extrude(page, kind, problems)
    if problems:
        return problems
    set_extrude_depth(page, "10")
    set_extrude_mode(page, "new")
    tap(page, ".topbar [data-action='undo']")
    page.wait_for_function(
        """(spec) => {
          const s = window.__cadcamExportState || {};
          const sheet = document.getElementById('sketchSheet');
          const vol = Number(s.volumeMm3);
          return s.sketchSheetOpen === false
            && !!(sheet && sheet.hidden === true)
            && s.undoDepth === spec.undo
            && s.redoDepth === spec.redo
            && s.bodyCount === spec.bodies
            && s.holeCount === 0
            && Number.isFinite(vol)
            && Math.abs(vol - spec.vol) <= spec.tol
            && s.occtGate === true
            && s.gateOcct === 'PASS'
            && s.watertight === true
            && s.unitsPass === true;
        }""",
        arg={"undo": 0, "redo": 2, "bodies": 1, "vol": 8000.0, "tol": 0.5},
    )
    check_gate_and_units(page, kind, "open-sheet-undo", problems)

    page.evaluate("document.getElementById('toasts').replaceChildren()")
    tap(page, "#sketchConfirm")
    page.wait_for_function(
        """(spec) => {
          const s = window.__cadcamExportState || {};
          const sk = window.__cadcamSketch ? window.__cadcamSketch.state() : {};
          const sheet = document.getElementById('sketchSheet');
          const hint = document.getElementById('statusHint');
          const toasts = document.getElementById('toasts');
          const vol = Number(s.volumeMm3);
          return !!(toasts && (toasts.textContent || '').includes('Sketch'))
            && !!(hint && (hint.textContent || '').trim().startsWith('Undo'))
            && sk.closed === true
            && s.sketchSheetOpen === false
            && !!(sheet && sheet.hidden === true)
            && s.undoDepth === spec.undo
            && s.redoDepth === spec.redo
            && s.bodyCount === spec.bodies
            && s.holeCount === 0
            && Number.isFinite(vol)
            && Math.abs(vol - spec.vol) <= spec.tol
            && s.occtGate === true
            && s.gateOcct === 'PASS'
            && s.watertight === true
            && s.unitsPass === true;
        }""",
        arg={"undo": 0, "redo": 2, "bodies": 1, "vol": 8000.0, "tol": 0.5},
    )
    check_gate_and_units(page, kind, "open-sheet-undo-confirm", problems)

    open_tools_sheet(page)
    tap(page, "#sheetTools button:has-text('Extrude (Push/Pull)')")
    page.wait_for_function(
        """() => {
          const s = window.__cadcamExportState || {};
          const depthRow = document.getElementById('sketchDepthRow');
          const modeRow = document.getElementById('sketchModeRow');
          return s.sketchSheetOpen === true
            && !!(depthRow && depthRow.hidden === false)
            && !!(modeRow && modeRow.hidden === false);
        }"""
    )
    set_extrude_depth(page, "10")
    set_extrude_mode(page, "new")
    tap(page, ".topbar [data-action='redo']")
    page.wait_for_function(
        """(spec) => {
          const s = window.__cadcamExportState || {};
          const sheet = document.getElementById('sketchSheet');
          const vol = Number(s.volumeMm3);
          return s.sketchSheetOpen === false
            && !!(sheet && sheet.hidden === true)
            && s.undoDepth === spec.undo
            && s.redoDepth === spec.redo
            && s.bodyCount === spec.bodies
            && s.holeCount === 1
            && Number.isFinite(vol)
            && Math.abs(vol - spec.vol) <= spec.tol
            && s.occtGate === true
            && s.gateOcct === 'PASS'
            && s.watertight === true
            && s.unitsPass === true;
        }""",
        arg={"undo": 1, "redo": 1, "bodies": 1, "vol": hole_vol, "tol": 0.5},
    )
    check_gate_and_units(page, kind, "open-sheet-redo", problems)

    page.evaluate("document.getElementById('toasts').replaceChildren()")
    tap(page, "#sketchConfirm")
    page.wait_for_function(
        """(spec) => {
          const s = window.__cadcamExportState || {};
          const sk = window.__cadcamSketch ? window.__cadcamSketch.state() : {};
          const sheet = document.getElementById('sketchSheet');
          const hint = document.getElementById('statusHint');
          const toasts = document.getElementById('toasts');
          const vol = Number(s.volumeMm3);
          return !!(toasts && (toasts.textContent || '').includes('Sketch'))
            && !!(hint && (hint.textContent || '').trim().startsWith('Redo'))
            && sk.closed === true
            && s.sketchSheetOpen === false
            && !!(sheet && sheet.hidden === true)
            && s.undoDepth === spec.undo
            && s.redoDepth === spec.redo
            && s.bodyCount === spec.bodies
            && s.holeCount === 1
            && Number.isFinite(vol)
            && Math.abs(vol - spec.vol) <= spec.tol
            && s.occtGate === true
            && s.gateOcct === 'PASS'
            && s.watertight === true
            && s.unitsPass === true;
        }""",
        arg={"undo": 1, "redo": 1, "bodies": 1, "vol": hole_vol, "tol": 0.5},
    )
    check_gate_and_units(page, kind, "open-sheet-redo-confirm", problems)

    open_create_menu(page)
    tap(page, "#createMenu [data-action='newSketch']")
    page.wait_for_function(
        "() => !!(window.__cadcamSketch && window.__cadcamSketch.state().tab === 'sketch')"
    )
    tapped = page.evaluate(
        "() => window.__cadcamSketch.tapFace(window.__cadcamSketch.topFace())"
    )
    if tapped is not True:
        problems.append(f"{kind} open-rect tapFace {tapped!r}")
        return problems
    page.wait_for_function(
        """() => {
          const st = window.__cadcamSketch ? window.__cadcamSketch.state() : null;
          return !!(st && st.plane === true && st.faceId);
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
    tap(page, ".topbar [data-action='redo']")
    page.wait_for_function(
        """(spec) => {
          const s = window.__cadcamExportState || {};
          const sheet = document.getElementById('sketchSheet');
          const callouts = window.__cadcamCallouts ? window.__cadcamCallouts.probe() : null;
          const vol = Number(s.volumeMm3);
          return s.sketchSheetOpen === false
            && !!(sheet && sheet.hidden === true)
            && !!(callouts && callouts.hidden === true)
            && s.undoDepth === spec.undo
            && s.redoDepth === spec.redo
            && s.bodyCount === spec.bodies
            && Number.isFinite(vol)
            && Math.abs(vol - spec.vol) <= spec.tol
            && s.occtGate === true
            && s.gateOcct === 'PASS'
            && s.watertight === true
            && s.unitsPass === true;
        }""",
        arg={"undo": 2, "redo": 0, "bodies": 2, "vol": hole_vol + 1000.0, "tol": 1.0},
    )
    check_gate_and_units(page, kind, "open-rect-sheet-redo", problems)

    open_tools_sheet(page)
    tap(page, "#sheetTools button:has-text('Rectangle')")
    page.wait_for_function(
        """() => {
          const s = window.__cadcamExportState || {};
          const row = document.getElementById('sketchRectRow');
          return s.sketchSheetOpen === true && !!(row && row.hidden === false);
        }"""
    )
    tap(page, ".topbar [data-action='undo']")
    page.wait_for_function(
        """(spec) => {
          const s = window.__cadcamExportState || {};
          const sheet = document.getElementById('sketchSheet');
          const callouts = window.__cadcamCallouts ? window.__cadcamCallouts.probe() : null;
          const vol = Number(s.volumeMm3);
          return s.sketchSheetOpen === false
            && !!(sheet && sheet.hidden === true)
            && !!(callouts && callouts.hidden === true)
            && s.undoDepth === spec.undo
            && s.redoDepth === spec.redo
            && s.bodyCount === spec.bodies
            && Number.isFinite(vol)
            && Math.abs(vol - spec.vol) <= spec.tol
            && s.occtGate === true
            && s.gateOcct === 'PASS'
            && s.watertight === true
            && s.unitsPass === true;
        }""",
        arg={"undo": 1, "redo": 1, "bodies": 1, "vol": hole_vol, "tol": 0.5},
    )
    check_gate_and_units(page, kind, "open-rect-sheet-undo", problems)
    check_controls(page, kind, problems)
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
        url = origin + "/?primitive=box&select=item"
        print(f"load {kind} {url}", flush=True)
        page.goto(url, wait_until="domcontentloaded", timeout=deploy_smoke.PAGE_TIMEOUT_S * 1000)
        problems = run_case(page, kind)
        if errors:
            problems = [f"{kind} js: {item}" for item in errors[:8]] + problems
        if problems:
            return [f"{kind} 390x844", *problems]
        print(f"PASS extrude_undo_smoke {kind}", flush=True)
        return []
    finally:
        browser.close()


def run() -> int:
    gaps = deploy_smoke.libcascade_gaps()
    if gaps:
        text = "; ".join(gaps)
        if in_ci():
            print(f"FAIL extrude_undo_smoke: {text}", flush=True)
            print("CI must not skip extrude_undo_smoke.", flush=True)
            return 1
        print("SKIP extrude_undo_smoke: " + text, flush=True)
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
    thread = threading.Thread(target=server.serve_forever, name="extrude-undo-http", daemon=True)
    thread.start()
    try:
        with sync_playwright() as playwright:
            for engine in ("chromium", "webkit"):
                problems = run_engine(playwright, engine, origin)
                if problems:
                    print("FAIL extrude_undo_smoke", flush=True)
                    for line in problems:
                        print(line, flush=True)
                    return 1
        print("PASS extrude_undo_smoke", flush=True)
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
        print(f"FAIL extrude_undo_smoke: {exc}", flush=True)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
