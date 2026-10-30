#!/usr/bin/env python3
"""Adaptive solid-editing context bar & dimension workflow smoke test.

Tests the adaptive lifecycle across Chromium and WebKit (390x844 mobile viewport):
  1. Pre-Selection (Filter State): Filter chips >= 44x44 px, mode switching.
  2. Selection Isolation: Switching filter drops previous entity highlights.
  3. Post-Selection (Action State): Dynamic actions for Face, Edge, Body.
  4. Ergonomics: Stepper buttons, decimal inputmode, no Safari auto-zoom/spinners.
  5. Shortcut Safeguards: Hotkeys 1-4 suspended while typing in dimension inputs.
  6. Keep-Last-Good Pattern: Invalid fillet size rejected, original solid preserved.
  7. Unified Undo Stack: Fillet commit via runUndoable, undo reverts and redo restores.

Exit 77 when Playwright or libcascade is missing.
"""
from __future__ import annotations

import os
import sys
import threading
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
WORK = ROOT / "builds" / "context-bar-smoke"
SKIP = 77


def in_ci() -> bool:
    return os.environ.get("CI", "").strip().lower() not in {"", "0", "false", "no"}


def skip_missing_playwright() -> int:
    if in_ci():
        print(
            "FAIL context_bar_smoke: playwright is not importable; CI must not skip.",
            flush=True,
        )
        return 1
    print("SKIP context_bar_smoke: playwright is not importable.", flush=True)
    return SKIP


try:
    from playwright.sync_api import sync_playwright
except ImportError:
    raise SystemExit(skip_missing_playwright())

import deploy_smoke


POINTER = """(spec) => {
  const el = document.getElementById('canvas');
  function fire(type, x, y) {
    const ending = type === 'pointerup' || type === 'pointercancel';
    el.dispatchEvent(new PointerEvent(type, {
      bubbles: true,
      cancelable: true,
      pointerId: spec.pointerId || 71,
      pointerType: 'touch',
      isPrimary: true,
      button: 0,
      buttons: ending ? 0 : 1,
      clientX: x,
      clientY: y
    }));
  }
  fire('pointerdown', Number(spec.x), Number(spec.y));
  fire('pointerup', Number(spec.x), Number(spec.y));
  return window.__cadcamExportState || {};
}"""


def read_state(page: Any) -> dict[str, Any]:
    state = page.evaluate("() => window.__cadcamExportState || null")
    return state if isinstance(state, dict) else {}


def aims(page: Any) -> dict[str, Any]:
    found = page.evaluate("() => window.__cadcamPhoneSelect ? window.__cadcamPhoneSelect.aims() : null")
    return found if isinstance(found, dict) else {}


def tap(page: Any, selector: str) -> None:
    loc = page.locator(selector).first
    if loc.is_visible():
        loc.tap()
    else:
        loc.dispatch_event("click")


def run_engine(playwright: Any, engine_name: str, origin: str) -> list[str]:
    problems: list[str] = []
    browser_type = getattr(playwright, engine_name)
    browser = browser_type.launch(headless=True)
    try:
        context = browser.new_context(
            viewport={"width": 390, "height": 844},
            is_mobile=True,
            has_touch=True,
            device_scale_factor=3,
        )
        page = context.new_page()
        page_errors: list[str] = []
        page.on("pageerror", lambda exc: page_errors.append(str(exc)))
        def on_console(msg: Any) -> None:
            if msg.type not in {"error", "assert"}:
                return
            text = str(msg.text or "")
            if "interactive-widget" in text and "not recognized" in text:
                return
            page_errors.append(text)

        page.on("console", on_console)

        url = f"{origin}/?part=l"
        print(f"load {engine_name} {url}", flush=True)
        page.goto(url, wait_until="domcontentloaded")
        page.wait_for_function("() => window.__cadcamExportState && window.__cadcamExportState.occtReady === true", timeout=30000)

        initial_state = read_state(page)
        base_volume = float(initial_state.get("volumeMm3") or initial_state.get("volume") or 0.0)
        if not (base_volume > 0):
            problems.append(f"{engine_name} missing initial solid volume")

        # 1. Open Selection Shelf and Verify Tap Targets (Apple HIG >= 44x44 px)
        if page.evaluate("() => document.getElementById('selectionShelf').hidden === true"):
            page.locator("[data-action='selectionShelf']").click()
            page.wait_for_function("() => document.getElementById('selectionShelf').hidden === false")

        for mode in ("vertex", "edge", "face", "item"):
            box = page.locator(f"#selectionShelf [data-action='select'][data-mode='{mode}']").bounding_box()
            if not box or box["width"] < 43.5 or box["height"] < 43.5:
                problems.append(f"{engine_name} select mode {mode} target under 44px: {box}")

        # 2. Verify Selection Isolation
        # Tap Face mode
        tap(page, "#selectionShelf [data-action='select'][data-mode='face']")
        st = read_state(page)
        if (st.get("selection") or st.get("selectionMode")) != "face":
            problems.append(f"{engine_name} expected face mode, got {st.get('selection')}")

        # Pick face f1
        aim_map = aims(page)
        face_aim = aim_map.get("face") if isinstance(aim_map, dict) else None
        if face_aim and "x" in face_aim and "y" in face_aim:
            page.evaluate(POINTER, {"x": face_aim["x"], "y": face_aim["y"]})
            # When face is selected, actions should be visible
            has_face_sel = page.evaluate("() => document.getElementById('selectionActions').hidden === false")
            if not has_face_sel:
                problems.append(f"{engine_name} selectionActions should be visible with face selected")
            push_visible = page.evaluate("() => !document.querySelector('[data-action=\"contextFaceOp\"][data-op=\"pushPull\"]').hidden")
            if not push_visible:
                problems.append(f"{engine_name} push/pull action should be visible for face")

        # Now switch to Edge filter mode -> Selection Isolation must clear previous face highlights
        tap(page, "#selectionShelf [data-action='select'][data-mode='edge']")
        edge_mode_state = read_state(page)
        if (edge_mode_state.get("selection") or edge_mode_state.get("selectionMode")) != "edge":
            problems.append(f"{engine_name} expected edge mode, got {edge_mode_state.get('selection')}")
        sel_count = int(read_state(page).get("selectionCount") or 0)
        if sel_count != 0:
            problems.append(f"{engine_name} selection isolation failed: selectionCount not 0 after mode switch ({sel_count})")
        actions_hidden = page.evaluate("() => document.getElementById('selectionActions').hidden === true")
        if not actions_hidden:
            problems.append(f"{engine_name} selectionActions should be hidden after switching to unselected filter")

        # 3. Post-Selection (Action State) for Edge
        aim_map = aims(page)
        edge_aim = aim_map.get("edge") if isinstance(aim_map, dict) else None
        if not edge_aim or "x" not in edge_aim:
            problems.append(f"{engine_name} could not locate edge aim target")
        else:
            page.evaluate(POINTER, {"x": edge_aim["x"], "y": edge_aim["y"]})
            actions_on = page.evaluate("() => document.getElementById('selectionActions').hidden === false")
            if not actions_on:
                problems.append(f"{engine_name} selectionActions should unhide on edge pick")
            fillet_visible = page.evaluate("() => !document.querySelector('[data-action=\"armEdge\"][data-op=\"fillet\"]').hidden")
            if not fillet_visible:
                problems.append(f"{engine_name} fillet action should be visible on edge pick")

            # 4. Arm Fillet Tool and Verify Parameter Ergonomics
            tap(page, "#selectionActions [data-action='armEdge'][data-op='fillet']")
            page.wait_for_function("() => document.getElementById('edgeSheet').hidden === false")

            sheet_title = page.evaluate("() => (document.getElementById('edgeSheetTitle') || {}).textContent")
            if sheet_title != "Fillet":
                problems.append(f"{engine_name} expected Fillet title, got {sheet_title!r}")

            input_info = page.evaluate("""() => {
                const el = document.getElementById('edgeSize');
                return {
                    type: el.getAttribute('type'),
                    inputmode: el.getAttribute('inputmode'),
                    value: el.value,
                    fontSize: getComputedStyle(el).fontSize
                };
            }""")
            if input_info.get("type") != "text" or input_info.get("inputmode") != "decimal":
                problems.append(f"{engine_name} invalid input attributes: {input_info}")
            if input_info.get("fontSize") != "16px":
                problems.append(f"{engine_name} font size should be 16px to prevent iOS zoom: {input_info.get('fontSize')}")

            # Verify Stepper Buttons (>= 44x44 px)
            minus_box = page.locator("[data-action='edgeStep'][data-delta='-0.5']").bounding_box()
            plus_box = page.locator("[data-action='edgeStep'][data-delta='0.5']").bounding_box()
            if not minus_box or minus_box["width"] < 43.5 or minus_box["height"] < 43.5:
                problems.append(f"{engine_name} minus stepper target under 44px: {minus_box}")
            if not plus_box or plus_box["width"] < 43.5 or plus_box["height"] < 43.5:
                problems.append(f"{engine_name} plus stepper target under 44px: {plus_box}")

            # Test Steppers
            tap(page, "[data-action='edgeStep'][data-delta='0.5']")
            stepped_val = page.evaluate("() => document.getElementById('edgeSize').value")
            if stepped_val != "2.5":
                problems.append(f"{engine_name} expected stepper increment to 2.5, got {stepped_val}")
            tap(page, "[data-action='edgeStep'][data-delta='-0.5']")

            # 5. Desktop Shortcut Safeguards While Typing
            page.locator("#edgeSize").focus()
            page.keyboard.type("1")
            active_mode = read_state(page).get("selection") or read_state(page).get("selectionMode")
            if active_mode != "edge":
                problems.append(f"{engine_name} hotkey 1 leaked through while typing in input! Selection changed to {active_mode}")

            # 6. Keep-Last-Good Pattern (Invalid Size Rejection)
            page.evaluate("() => { const el = document.getElementById('edgeSize'); el.value = '80'; el.dispatchEvent(new Event('input', {bubbles: true})); }")
            page.wait_for_timeout(100)
            tap(page, "#edgeConfirm")
            page.wait_for_timeout(300)

            # Solid volume must remain identical to baseline
            preserved_vol = float(read_state(page).get("volumeMm3") or read_state(page).get("volume") or 0.0)
            if abs(preserved_vol - base_volume) > 1e-4:
                problems.append(f"{engine_name} keep-last-good failed: volume mutated on rejected op ({preserved_vol} vs {base_volume})")

            # Sheet must remain open so user can adjust
            sheet_still_open = page.evaluate("() => document.getElementById('edgeSheet').hidden === false")
            if not sheet_still_open:
                problems.append(f"{engine_name} edgeSheet should stay open after rejected op")

            # 7. Unified Undo Stack (Successful Fillet -> Undo -> Redo)
            page.evaluate("() => { const el = document.getElementById('edgeSize'); el.value = '2'; el.dispatchEvent(new Event('input', {bubbles: true})); }")
            tap(page, "#edgeConfirm")
            page.wait_for_function(f"() => window.__cadcamExportState && Math.abs(Number(window.__cadcamExportState.volumeMm3) - {base_volume}) > 0.1", timeout=10000)

            filleted_vol = float(read_state(page).get("volumeMm3") or read_state(page).get("volume") or 0.0)
            if abs(filleted_vol - base_volume) < 1.0:
                problems.append(f"{engine_name} filleted volume did not change from baseline: {filleted_vol}")

            # Undo reverts solid
            tap(page, ".topbar [data-action='undo']")
            page.wait_for_function(f"() => window.__cadcamExportState && Math.abs(Number(window.__cadcamExportState.volumeMm3) - {base_volume}) < 1e-4", timeout=5000)
            undone_vol = float(read_state(page).get("volumeMm3") or read_state(page).get("volume") or 0.0)
            if abs(undone_vol - base_volume) > 1e-4:
                problems.append(f"{engine_name} undo did not restore baseline volume: {undone_vol} vs {base_volume}")

            # Redo restores fillet
            tap(page, ".topbar [data-action='redo']")
            page.wait_for_function(f"() => window.__cadcamExportState && Math.abs(Number(window.__cadcamExportState.volumeMm3) - {filleted_vol}) < 1e-4", timeout=5000)
            redone_vol = float(read_state(page).get("volumeMm3") or read_state(page).get("volume") or 0.0)
            if abs(redone_vol - filleted_vol) > 1e-4:
                problems.append(f"{engine_name} redo did not restore filleted volume: {redone_vol} vs {filleted_vol}")

        if page_errors:
            problems.extend([f"{engine_name} page error: {err}" for err in page_errors])

        if problems:
            return problems

        print(f"PASS context_bar_smoke {engine_name}", flush=True)
        return []
    finally:
        browser.close()


def run() -> int:
    gaps = deploy_smoke.libcascade_gaps()
    if gaps:
        text = "; ".join(gaps)
        if in_ci():
            print(f"FAIL context_bar_smoke: {text}", flush=True)
            return 1
        print("SKIP context_bar_smoke: " + text, flush=True)
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
    thread = threading.Thread(target=server.serve_forever, name="context-bar-http", daemon=True)
    thread.start()
    try:
        with sync_playwright() as playwright:
            for engine in ("chromium", "webkit"):
                problems = run_engine(playwright, engine, origin)
                if problems:
                    print("FAIL context_bar_smoke", flush=True)
                    for line in problems:
                        print(line, flush=True)
                    return 1
        print("PASS context_bar_smoke", flush=True)
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
        print(f"FAIL context_bar_smoke: {exc}", flush=True)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
