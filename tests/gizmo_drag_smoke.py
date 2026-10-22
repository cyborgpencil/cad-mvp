#!/usr/bin/env python3
"""Drag the box along X and check the one-step undo stack.

Desktop Chromium uses a mouse drag. WebKit uses Playwright's iPhone 13
profile and a pointerType 'touch' drag. The page listens to Pointer Events.
Playwright WebKit has no touch-drag CDP, so the touch drag is dispatched
on #viewport.

Wired into CTest next to deploy_smoke. Playwright lives in the pwvenv.
Exit 77 when it cannot be imported. The visible undo and redo controls
are the ones on screen: the top bar on desktop, the phone tab bar at 390.
"""
from __future__ import annotations

import math
import os
import sys
import threading
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
WORK = ROOT / "builds" / "gizmo-smoke"
SKIP = 77
MOVE_MM = 10.0


def skip_missing_playwright() -> int:
    print(
        "SKIP gizmo_drag_smoke: playwright is not importable. "
        "Use builds/pwvenv/Scripts/python.exe.",
        flush=True,
    )
    return SKIP


try:
    from playwright.sync_api import sync_playwright
except ImportError:
    raise SystemExit(skip_missing_playwright())

import deploy_smoke


READ_STATE = """() => {
  const s = window.__cadcamExportState || {};
  const p = s.primitiveParams || {};
  const aim = window.__cadcamHomeAim ? window.__cadcamHomeAim() : null;
  const hint = document.getElementById('statusHint');
  const pos = document.getElementById('posX');
  return {
    cx: p.cx, cy: p.cy, cz: p.cz,
    undoDepth: s.undoDepth, redoDepth: s.redoDepth,
    gateOcct: s.gateOcct, gizmoVisible: s.gizmoVisible,
    bodyCount: s.bodyCount, hint: hint ? hint.textContent : '',
    target: aim ? aim.target : null,
    posX: pos ? pos.value : ''
  };
}"""

TOUCH = """({down, up, phase}) => {
  const el = document.getElementById('viewport');
  function fire(type, x, y) {
    const ending = type === 'pointerup' || type === 'pointercancel';
    el.dispatchEvent(new PointerEvent(type, {
      bubbles: true,
      cancelable: true,
      pointerId: 7,
      pointerType: 'touch',
      isPrimary: true,
      button: 0,
      buttons: ending ? 0 : 1,
      clientX: x,
      clientY: y,
      width: 24,
      height: 24
    }));
  }
  if (phase === 'down') {
    fire('pointerdown', down.x, down.y);
    fire('pointermove', (down.x + up.x) / 2, (down.y + up.y) / 2);
    return 'down';
  }
  fire('pointermove', up.x, up.y);
  fire('pointerup', up.x, up.y);
  return 'up';
}"""


def near(problems: list[str], label: str, got: Any, want: float, tol: float) -> None:
    try:
        value = float(got)
    except (TypeError, ValueError):
        problems.append(f"{label}: {got!r} want {want} ±{tol}")
        return
    if abs(value - want) > tol:
        problems.append(f"{label}: {value} want {want} ±{tol}")


def read_state(page: Any) -> dict[str, Any]:
    value = page.evaluate(READ_STATE)
    if not isinstance(value, dict):
        return {}
    return value


def drag_plan(page: Any) -> dict[str, Any] | None:
    value = page.evaluate(
        "(mm) => window.__cadcamGizmoDrag ? window.__cadcamGizmoDrag('x', mm) : null",
        MOVE_MM,
    )
    if not isinstance(value, dict):
        return None
    return value


def mouse_drag(page: Any, down: dict[str, Any], up: dict[str, Any]) -> dict[str, Any]:
    page.mouse.move(float(down["x"]), float(down["y"]))
    page.mouse.down()
    page.mouse.move(
        (float(down["x"]) + float(up["x"])) / 2,
        (float(down["y"]) + float(up["y"])) / 2,
    )
    mid = read_state(page)
    page.mouse.move(float(up["x"]), float(up["y"]))
    page.mouse.up()
    return mid


def touch_drag(page: Any, down: dict[str, Any], up: dict[str, Any]) -> dict[str, Any]:
    page.evaluate(TOUCH, {"down": down, "up": up, "phase": "down"})
    mid = read_state(page)
    page.evaluate(TOUCH, {"down": down, "up": up, "phase": "up"})
    return mid


def undo(page: Any, how: str) -> None:
    if how == "button":
        page.locator('[data-action="undo"]:visible').click()
    else:
        page.keyboard.press("Control+z")


def redo(page: Any, how: str) -> None:
    if how == "button":
        page.locator('[data-action="redo"]:visible').click()
    else:
        page.keyboard.press("Control+y")


def check_move(problems: list[str], label: str, state: dict[str, Any], origin: dict[str, Any], tol: float) -> None:
    near(problems, f"{label} cx", state.get("cx"), float(origin["cx"]) + MOVE_MM, tol)
    near(problems, f"{label} cy", state.get("cy"), float(origin["cy"]), tol)
    near(problems, f"{label} cz", state.get("cz"), float(origin["cz"]), tol)
    target = state.get("target") or [None, None, None]
    origin_target = origin.get("target") or [0, 0, 0]
    near(problems, f"{label} mesh x", target[0], float(origin_target[0]) + MOVE_MM, tol)
    near(problems, f"{label} mesh y", target[1], float(origin_target[1]), tol)
    near(problems, f"{label} mesh z", target[2], float(origin_target[2]), tol)


def check_home(problems: list[str], label: str, state: dict[str, Any], origin: dict[str, Any], tol: float) -> None:
    near(problems, f"{label} cx", state.get("cx"), float(origin["cx"]), tol)
    near(problems, f"{label} cy", state.get("cy"), float(origin["cy"]), tol)
    near(problems, f"{label} cz", state.get("cz"), float(origin["cz"]), tol)
    target = state.get("target") or [None, None, None]
    origin_target = origin.get("target") or [0, 0, 0]
    near(problems, f"{label} mesh x", target[0], float(origin_target[0]), tol)
    near(problems, f"{label} mesh y", target[1], float(origin_target[1]), tol)
    near(problems, f"{label} mesh z", target[2], float(origin_target[2]), tol)


def run_case(page: Any, kind: str) -> list[str]:
    problems: list[str] = []
    page.wait_for_function(
        """() => {
          const s = window.__cadcamExportState;
          return !!(s && s.occtReady === true && s.primitiveKind === 'box'
            && s.gizmoVisible === true && s.undoDepth === 0 && s.primitiveParams);
        }""",
        timeout=deploy_smoke.PAGE_TIMEOUT_S * 1000,
    )
    origin = read_state(page)
    print(f"{kind} origin {origin}", flush=True)
    if origin.get("gateOcct") != "PASS":
        problems.append(f"{kind} gate before drag {origin.get('gateOcct')!r}")
    plan = drag_plan(page)
    print(f"{kind} plan {plan}", flush=True)
    if not plan or not isinstance(plan.get("down"), dict) or not isinstance(plan.get("up"), dict):
        return problems + [f"{kind} no drag plan"]
    if plan.get("handle") != "x":
        return problems + [f"{kind} handle {plan.get('handle')!r}"]
    down = plan["down"]
    up = plan["up"]
    span = math.hypot(float(up["x"]) - float(down["x"]), float(up["y"]) - float(down["y"]))
    print(f"{kind} span {span:.1f}px", flush=True)
    if span < 12:
        problems.append(f"{kind} screen span {span:.1f}px")
    if kind == "touch":
        mid = touch_drag(page, down, up)
    else:
        mid = mouse_drag(page, down, up)
    print(f"{kind} mid {mid}", flush=True)
    hint = str(mid.get("hint") or "")
    if "Orbit" in hint or "stays put" in hint:
        problems.append(f"{kind} mid hint {hint!r}")
    try:
        if abs(float(mid.get("posX")) - float(origin.get("cx"))) < 0.5:
            problems.append(f"{kind} preview posX stayed {mid.get('posX')!r}")
    except (TypeError, ValueError):
        problems.append(f"{kind} preview posX {mid.get('posX')!r}")
    moved = read_state(page)
    print(f"{kind} moved {moved}", flush=True)
    check_move(problems, f"{kind} drag", moved, origin, 0.1)
    if moved.get("undoDepth") != 1 or moved.get("redoDepth") != 0:
        problems.append(f"{kind} stack after drag {moved.get('undoDepth')}/{moved.get('redoDepth')}")
    if moved.get("gateOcct") != "PASS":
        problems.append(f"{kind} gate after drag {moved.get('gateOcct')!r}")

    undo(page, "key")
    undone = read_state(page)
    print(f"{kind} undo {undone}", flush=True)
    check_home(problems, f"{kind} undo", undone, origin, 0.01)
    if undone.get("undoDepth") != 0 or undone.get("redoDepth") != 1:
        problems.append(f"{kind} stack after undo {undone.get('undoDepth')}/{undone.get('redoDepth')}")

    undo(page, "key")
    again = read_state(page)
    print(f"{kind} second undo {again}", flush=True)
    check_home(problems, f"{kind} second undo", again, origin, 0.01)
    if again.get("undoDepth") != 0:
        problems.append(f"{kind} second undo depth {again.get('undoDepth')}")
    if "Nothing to undo" not in str(again.get("hint") or ""):
        problems.append(f"{kind} second undo hint {again.get('hint')!r}")

    redo(page, "key")
    redone = read_state(page)
    print(f"{kind} redo {redone}", flush=True)
    check_home(problems, f"{kind} redo", redone, moved, 0.01)
    if redone.get("undoDepth") != 1 or redone.get("redoDepth") != 0:
        problems.append(f"{kind} stack after redo {redone.get('undoDepth')}/{redone.get('redoDepth')}")

    if kind == "mouse":
        undo(page, "button")
        button_undo = read_state(page)
        print(f"{kind} button undo {button_undo}", flush=True)
        check_home(problems, f"{kind} button undo", button_undo, origin, 0.01)
        redo(page, "button")
        button_redo = read_state(page)
        print(f"{kind} button redo {button_redo}", flush=True)
        check_home(problems, f"{kind} button redo", button_redo, moved, 0.01)
    return problems


def run_engine(playwright: Any, engine: str, origin: str) -> list[str]:
    browser = getattr(playwright, engine).launch(headless=True)
    try:
        if engine == "webkit":
            device = dict(playwright.devices["iPhone 13"])
            device.pop("default_browser_type", None)
            device["screen"] = {"width": 390, "height": 844}
            device["viewport"] = {"width": 390, "height": 844}
            context = browser.new_context(**device)
            kind = "touch"
        else:
            context = browser.new_context(
                viewport={"width": 1440, "height": 900},
                device_scale_factor=1,
                is_mobile=False,
                has_touch=False,
            )
            kind = "mouse"
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
            return [f"{engine} {kind}", *problems]
        print(f"PASS gizmo_drag_smoke {engine}", flush=True)
        return []
    finally:
        browser.close()


def run() -> int:
    gaps = deploy_smoke.libcascade_gaps()
    if gaps:
        print("SKIP gizmo_drag_smoke: " + "; ".join(gaps), flush=True)
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
    thread = threading.Thread(target=server.serve_forever, name="gizmo-drag-http", daemon=True)
    thread.start()
    try:
        with sync_playwright() as playwright:
            for engine in ("chromium", "webkit"):
                problems = run_engine(playwright, engine, origin)
                if problems:
                    print("FAIL gizmo_drag_smoke", flush=True)
                    for line in problems:
                        print(line, flush=True)
                    return 1
        print("PASS gizmo_drag_smoke", flush=True)
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
        print(f"FAIL gizmo_drag_smoke: {exc}", flush=True)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
