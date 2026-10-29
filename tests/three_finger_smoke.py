#!/usr/bin/env python3
"""Three-finger swipe undoes, then redoes, and the setting survives reload.

Synthetic PointerEvents on #viewport. Left drops undoDepth by one. Right
puts it back. Turning the File-menu toggle off stores the choice, and a
reload keeps it off so the same swipe does nothing.

Wired into CTest next to view_cube_swipe_smoke. Playwright lives in the
pwvenv. Exit 77 when it cannot be imported.
"""
from __future__ import annotations

import math
import os
import sys
import threading
import time
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
WORK = ROOT / "builds" / "three-finger-smoke"
SKIP = 77


def in_ci() -> bool:
    return os.environ.get("CI", "").strip().lower() not in {"", "0", "false", "no"}


def skip_missing_playwright() -> int:
    if in_ci():
        print(
            "FAIL three_finger_smoke: playwright is not importable; "
            "CI must not skip this test.",
            flush=True,
        )
        return 1
    print(
        "SKIP three_finger_smoke: playwright is not importable. "
        "Use builds/pwvenv/Scripts/python.exe.",
        flush=True,
    )
    return SKIP


try:
    from playwright.sync_api import sync_playwright
except ImportError:
    raise SystemExit(skip_missing_playwright())

import deploy_smoke


SWIPE = """(dx) => {
  const el = document.getElementById('viewport');
  const box = el.getBoundingClientRect();
  const y = box.top + box.height * 0.78;
  const x0 = box.left + Math.min(box.width * 0.28, Math.max(24, box.width - 160));
  const pts = [
    { id: 21, x: x0, y: y },
    { id: 22, x: x0 + 28, y: y + 12 },
    { id: 23, x: x0 + 56, y: y - 10 }
  ];
  function fire(type, p, x, yv) {
    const ending = type === 'pointerup' || type === 'pointercancel';
    el.dispatchEvent(new PointerEvent(type, {
      bubbles: true,
      cancelable: true,
      pointerId: p.id,
      pointerType: 'touch',
      isPrimary: p.id === 21,
      button: 0,
      buttons: ending ? 0 : 1,
      clientX: x,
      clientY: yv,
      width: 22,
      height: 22
    }));
  }
  for (let i = 0; i < pts.length; i += 1) fire('pointerdown', pts[i], pts[i].x, pts[i].y);
  for (let i = 0; i < pts.length; i += 1) {
    fire('pointermove', pts[i], pts[i].x + dx * 0.5, pts[i].y);
  }
  for (let i = 0; i < pts.length; i += 1) {
    fire('pointermove', pts[i], pts[i].x + dx, pts[i].y);
  }
  for (let i = 0; i < pts.length; i += 1) {
    fire('pointerup', pts[i], pts[i].x + dx, pts[i].y);
  }
  const s = window.__cadcamExportState || {};
  const hint = document.getElementById('statusHint');
  return { undo: s.undoDepth, redo: s.redoDepth, hint: hint ? hint.textContent : '' };
}"""

PINCH_THEN_THIRD = """() => {
  const el = document.getElementById('viewport');
  const box = el.getBoundingClientRect();
  const y = box.top + box.height * 0.72;
  const x0 = box.left + Math.min(box.width * 0.34, Math.max(30, box.width - 180));
  function fire(type, id, x, yv) {
    const ending = type === 'pointerup' || type === 'pointercancel';
    el.dispatchEvent(new PointerEvent(type, {
      bubbles: true,
      cancelable: true,
      pointerId: id,
      pointerType: 'touch',
      isPrimary: id === 31,
      button: 0,
      buttons: ending ? 0 : 1,
      clientX: x,
      clientY: yv,
      width: 22,
      height: 22
    }));
  }
  function cam() {
    const nav = window.__cadcamNavCube ? window.__cadcamNavCube() : null;
    if (!nav) return null;
    return {
      direction: nav.direction,
      target: nav.target,
      distance: nav.distance
    };
  }
  fire('pointerdown', 31, x0, y);
  fire('pointerdown', 32, x0 + 40, y);
  fire('pointermove', 31, x0 - 24, y + 16);
  fire('pointermove', 32, x0 + 70, y - 12);
  const before = cam();
  fire('pointerdown', 33, x0 + 18, y + 28);
  const after = cam();
  fire('pointerup', 33, x0 + 18, y + 28);
  fire('pointerup', 31, x0 - 24, y + 16);
  fire('pointerup', 32, x0 + 70, y - 12);
  return { before: before, after: after };
}"""

READ_TOGGLE = """() => {
  const btn = document.getElementById('threeFingerUndo');
  const hook = window.__cadcamThreeFinger || {};
  const key = hook.key || 'cadcam.threeFingerUndo';
  let stored = null;
  try { stored = localStorage.getItem(key); } catch (err) { stored = 'throw'; }
  return {
    pressed: btn ? btn.getAttribute('aria-pressed') : '',
    label: btn ? btn.textContent : '',
    stored: stored,
    enabled: typeof hook.enabled === 'function' ? hook.enabled() : null,
    key: key
  };
}"""


def read_toggle(page: Any) -> dict[str, Any]:
    value = page.evaluate(READ_TOGGLE)
    if not isinstance(value, dict):
        return {}
    return value


def wait_ready(page: Any) -> None:
    page.wait_for_function(
        """() => {
          const s = window.__cadcamExportState;
          return !!(s && s.occtReady === true && window.__cadcamThreeFinger && s.primitiveKind === 'box');
        }""",
        timeout=deploy_smoke.PAGE_TIMEOUT_S * 1000,
    )


def stack_resize(page: Any) -> dict[str, Any]:
    value = page.evaluate(
        """() => {
          const before = (window.__cadcamExportState || {}).undoDepth;
          const status = window.__cadcamResize({ sx: 40, sy: 20, sz: 20 });
          return {
            before: before,
            undo: status ? status.undoDepth : null,
            redo: status ? status.redoDepth : null,
            ok: status ? status.ok : false,
            error: status ? status.error : 'missing'
          };
        }"""
    )
    if not isinstance(value, dict):
        return {}
    return value


def cam_delta(before: dict[str, Any] | None, after: dict[str, Any] | None) -> str:
    if not isinstance(before, dict) or not isinstance(after, dict):
        return "missing camera"
    bd = before.get("direction")
    ad = after.get("direction")
    bt = before.get("target")
    at = after.get("target")
    if not isinstance(bd, list) or not isinstance(ad, list) or len(bd) != 3 or len(ad) != 3:
        return "missing direction"
    if not isinstance(bt, list) or not isinstance(at, list) or len(bt) != 3 or len(at) != 3:
        return "missing target"
    dot = float(bd[0]) * float(ad[0]) + float(bd[1]) * float(ad[1]) + float(bd[2]) * float(ad[2])
    dot = max(-1.0, min(1.0, dot))
    angle = math.degrees(math.acos(dot))
    shift = math.dist(
        (float(bt[0]), float(bt[1]), float(bt[2])),
        (float(at[0]), float(at[1]), float(at[2])),
    )
    try:
        dist = abs(float(after.get("distance")) - float(before.get("distance")))
    except (TypeError, ValueError):
        return "missing distance"
    if angle > 0.05 or shift > 1e-4 or dist > 1e-4:
        return f"angle {angle:.4f} deg shift {shift:.6f} dist {dist:.6f}"
    return ""


def run_case(page: Any, kind: str) -> list[str]:
    problems: list[str] = []
    wait_ready(page)
    toggle = read_toggle(page)
    label = str(toggle.get("label") or "")
    if "Three-finger undo/redo" not in label:
        problems.append(f"{kind} toggle label {label!r}")
    if toggle.get("pressed") != "true" or toggle.get("enabled") is not True:
        problems.append(f"{kind} default toggle {toggle!r}")
    if problems:
        return problems

    made = stack_resize(page)
    print(f"{kind} resize {made}", flush=True)
    if made.get("ok") is not True or made.get("undo") != 1 or made.get("before") != 0:
        return [f"{kind} resize did not push one undo step {made!r}"]

    info = page.evaluate("() => window.__cadcamThreeFinger")
    px = 40
    if isinstance(info, dict) and isinstance(info.get("px"), (int, float)):
        px = int(info["px"])
    left = page.evaluate(SWIPE, -(px + 16))
    print(f"{kind} swipe left {left}", flush=True)
    if not isinstance(left, dict) or left.get("undo") != 0 or left.get("redo") != 1:
        problems.append(f"{kind} undo swipe {left!r}")
    right = page.evaluate(SWIPE, px + 16)
    print(f"{kind} swipe right {right}", flush=True)
    if not isinstance(right, dict) or right.get("undo") != 1 or right.get("redo") != 0:
        problems.append(f"{kind} redo swipe {right!r}")

    jump = page.evaluate(PINCH_THEN_THIRD)
    moved = ""
    if isinstance(jump, dict):
        moved = cam_delta(jump.get("before"), jump.get("after"))
    else:
        moved = "pinch script failed"
    if moved:
        problems.append(f"{kind} third finger camera jump {moved}")
    else:
        print(f"{kind} third finger did not move the camera", flush=True)

    page.locator("#fileBtn").click()
    page.locator("#threeFingerUndo").click()
    off = read_toggle(page)
    if off.get("pressed") != "false" or off.get("stored") != "0" or off.get("enabled") is not False:
        problems.append(f"{kind} toggle off {off!r}")
    held = page.evaluate(SWIPE, -(px + 16))
    if not isinstance(held, dict) or held.get("undo") != 1 or held.get("redo") != 0:
        problems.append(f"{kind} swipe while off {held!r}")

    page.reload(wait_until="domcontentloaded", timeout=deploy_smoke.PAGE_TIMEOUT_S * 1000)
    wait_ready(page)
    kept = read_toggle(page)
    print(f"{kind} reload off {kept}", flush=True)
    if kept.get("pressed") != "false" or kept.get("stored") != "0" or kept.get("enabled") is not False:
        problems.append(f"{kind} toggle did not persist off {kept!r}")
    made_off = stack_resize(page)
    if made_off.get("ok") is not True or made_off.get("undo") != 1:
        problems.append(f"{kind} resize while off {made_off!r}")
    ignored = page.evaluate(SWIPE, -(px + 16))
    if not isinstance(ignored, dict) or ignored.get("undo") != 1:
        problems.append(f"{kind} swipe after reload off {ignored!r}")

    page.locator("#fileBtn").click()
    page.locator("#threeFingerUndo").click()
    page.reload(wait_until="domcontentloaded", timeout=deploy_smoke.PAGE_TIMEOUT_S * 1000)
    wait_ready(page)
    back = read_toggle(page)
    print(f"{kind} reload on {back}", flush=True)
    if back.get("pressed") != "true" or back.get("stored") != "1" or back.get("enabled") is not True:
        problems.append(f"{kind} toggle did not persist on {back!r}")
    if "Three-finger undo/redo" not in str(back.get("label") or ""):
        problems.append(f"{kind} label after reload {back.get('label')!r}")
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
        print(f"PASS three_finger_smoke {engine}", flush=True)
        return []
    finally:
        browser.close()


def run() -> int:
    gaps = deploy_smoke.libcascade_gaps()
    if gaps:
        text = "; ".join(gaps)
        if in_ci():
            print(f"FAIL three_finger_smoke: {text}", flush=True)
            print("CI must not skip three_finger_smoke.", flush=True)
            return 1
        print("SKIP three_finger_smoke: " + text, flush=True)
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
    thread = threading.Thread(target=server.serve_forever, name="three-finger-http", daemon=True)
    thread.start()
    try:
        with sync_playwright() as playwright:
            for engine in ("chromium", "webkit"):
                problems = run_engine(playwright, engine, origin)
                if problems:
                    print("FAIL three_finger_smoke", flush=True)
                    for line in problems:
                        print(line, flush=True)
                    return 1
        print("PASS three_finger_smoke", flush=True)
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
        print(f"FAIL three_finger_smoke: {exc}", flush=True)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
