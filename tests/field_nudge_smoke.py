#!/usr/bin/env python3
"""Focused field swipe nudges one step per threshold, and each step is one undo.

Synthetic PointerEvents on the size and rotation fields. A focused Size X
swipe of three horizontal steps adds 3 mm and three undo steps. One rotation
step adds 1 degree and one undo step. An unfocused field ignores the gesture.
pointercancel stops any further change. Vertical travel does not nudge, and
the camera does not orbit.

Wired into CTest next to three_finger_smoke. Playwright lives in the pwvenv.
Exit 77 when it cannot be imported.
"""
from __future__ import annotations

import math
import sys
import threading
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
WORK = ROOT / "builds" / "field-nudge-smoke"
SKIP = 77


def skip_missing_playwright() -> int:
    print(
        "SKIP field_nudge_smoke: playwright is not importable. "
        "Use builds/pwvenv/Scripts/python.exe.",
        flush=True,
    )
    return SKIP


try:
    from playwright.sync_api import sync_playwright
except ImportError:
    raise SystemExit(skip_missing_playwright())

import deploy_smoke


# steps > 0 moves right. A sub-step move is included so a pointermove that
# does not cross a new 24 px step must not push another undo.
# cancelAfter applies that many steps, then pointercancel, then extra moves.
SWIPE = """(spec) => {
  const el = document.getElementById(spec.id);
  const box = el.getBoundingClientRect();
  const y = box.top + Math.max(1, box.height / 2);
  const x0 = box.left + Math.max(1, box.width / 2);
  const step = spec.stepPx;
  const steps = spec.steps || 0;
  const vertical = spec.vertical === true;
  function fire(type, x, yv) {
    const ending = type === 'pointerup' || type === 'pointercancel';
    el.dispatchEvent(new PointerEvent(type, {
      bubbles: true,
      cancelable: true,
      pointerId: spec.pointerId || 41,
      pointerType: 'touch',
      isPrimary: true,
      button: 0,
      buttons: ending ? 0 : 1,
      clientX: x,
      clientY: yv
    }));
  }
  function cam() {
    const nav = window.__cadcamNavCube ? window.__cadcamNavCube() : null;
    if (!nav) return null;
    return { direction: nav.direction, target: nav.target, distance: nav.distance };
  }
  const before = window.__cadcamExportState || {};
  const beforeCam = cam();
  const beforeSx = before.primitiveParams ? before.primitiveParams.sx : null;
  const beforeRx = before.primitiveParams ? before.primitiveParams.rx : null;
  fire('pointerdown', x0, y);
  if (vertical) {
    fire('pointermove', x0 + Math.min(8, step - 1), y + step * 3);
    fire('pointerup', x0 + Math.min(8, step - 1), y + step * 3);
  } else if (spec.cancelAfter != null) {
    const n = spec.cancelAfter;
    fire('pointermove', x0 + step * 0.4, y);
    for (let i = 1; i <= n; i += 1) fire('pointermove', x0 + step * i, y + 2);
    fire('pointercancel', x0 + step * n, y);
    fire('pointermove', x0 + step * (n + 3), y);
    fire('pointerup', x0 + step * (n + 3), y);
  } else {
    fire('pointermove', x0 + step * 0.4, y);
    for (let i = 1; i <= steps; i += 1) fire('pointermove', x0 + step * i, y + 1);
    fire('pointerup', x0 + step * steps, y);
  }
  const after = window.__cadcamExportState || {};
  const params = after.primitiveParams || {};
  const stored = el.getAttribute('data-mm');
  return {
    beforeUndo: before.undoDepth,
    undo: after.undoDepth,
    redo: after.redoDepth,
    beforeSx: beforeSx,
    sx: params.sx,
    rx: params.rx,
    beforeRx: beforeRx,
    value: el.value,
    stored: stored,
    active: document.activeElement ? document.activeElement.id : '',
    selection: after.selectionMode || '',
    beforeCam: beforeCam,
    afterCam: cam()
  };
}"""


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


def wait_ready(page: Any) -> None:
    page.wait_for_function(
        """() => {
          const s = window.__cadcamExportState;
          return !!(s && s.occtReady === true && window.__cadcamFieldNudge && s.primitiveKind === 'box');
        }""",
        timeout=deploy_smoke.PAGE_TIMEOUT_S * 1000,
    )


def open_sheet(page: Any) -> None:
    page.locator("#dimToggle").click()
    page.wait_for_function(
        """() => {
          const s = window.__cadcamExportState || {};
          const el = document.getElementById('boxSx');
          if (!el || s.dimSheetOpen !== true) return false;
          const r = el.getBoundingClientRect();
          return r.width > 20 && r.height > 20;
        }""",
        timeout=deploy_smoke.PAGE_TIMEOUT_S * 1000,
    )


def near(got: Any, want: float) -> bool:
    try:
        return abs(float(got) - want) <= 1e-4
    except (TypeError, ValueError):
        return False


def run_case(page: Any, kind: str) -> list[str]:
    problems: list[str] = []
    wait_ready(page)
    hook = page.evaluate("() => window.__cadcamFieldNudge")
    if not isinstance(hook, dict) or hook.get("axis") != "x" or hook.get("mm") != 1 or hook.get("deg") != 1:
        return [f"{kind} field nudge hook {hook!r}"]
    px = hook.get("px")
    if not isinstance(px, (int, float)) or int(px) != 24:
        return [f"{kind} step px {px!r}"]
    step_px = int(px)

    touch = page.evaluate(
        """() => {
          const field = getComputedStyle(document.getElementById('boxSx')).touchAction;
          const rot = getComputedStyle(document.getElementById('primRx')).touchAction;
          const panel = getComputedStyle(document.getElementById('dimPanel')).touchAction;
          const viewport = getComputedStyle(document.getElementById('viewport')).touchAction;
          return { field: field, rot: rot, panel: panel, viewport: viewport };
        }"""
    )
    print(f"{kind} touch-action {touch}", flush=True)
    if not isinstance(touch, dict) or touch.get("field") != "pan-y" or touch.get("rot") != "pan-y":
        problems.append(f"{kind} field touch-action {touch!r}")
    if isinstance(touch, dict) and touch.get("panel") == "none":
        problems.append(f"{kind} panel touch-action stole scroll {touch!r}")

    open_sheet(page)
    page.locator("#boxSx").focus()
    page.keyboard.press("1")
    digit = page.evaluate(
        """() => {
          const el = document.getElementById('boxSx');
          const s = window.__cadcamExportState || {};
          const stored = el.getAttribute('data-mm');
          const typed = el.value;
          if (stored != null) el.value = stored;
          return {
            active: document.activeElement ? document.activeElement.id : '',
            selection: s.selectionMode || '',
            typed: typed,
            stored: stored
          };
        }"""
    )
    print(f"{kind} digit {digit}", flush=True)
    if not isinstance(digit, dict) or digit.get("active") != "boxSx" or digit.get("selection") != "item":
        problems.append(f"{kind} digit hotkey left the field {digit!r}")

    size = page.evaluate(SWIPE, {"id": "boxSx", "stepPx": step_px, "steps": 3, "pointerId": 41})
    print(f"{kind} size {size}", flush=True)
    if not isinstance(size, dict):
        problems.append(f"{kind} size swipe failed")
    else:
        moved = cam_delta(size.get("beforeCam"), size.get("afterCam"))
        if moved:
            problems.append(f"{kind} size swipe orbited {moved}")
        if not near(size.get("sx"), float(size.get("beforeSx") or 0) + 3):
            problems.append(f"{kind} size not +3 mm {size!r}")
        if size.get("undo") != (size.get("beforeUndo") or 0) + 3:
            problems.append(f"{kind} size undoDepth {size!r}")
        if size.get("active") != "boxSx":
            problems.append(f"{kind} size blur {size!r}")

    page.locator("#primRx").focus()
    rot = page.evaluate(SWIPE, {"id": "primRx", "stepPx": step_px, "steps": 1, "pointerId": 42})
    print(f"{kind} rotation {rot}", flush=True)
    if not isinstance(rot, dict):
        problems.append(f"{kind} rotation swipe failed")
    else:
        moved = cam_delta(rot.get("beforeCam"), rot.get("afterCam"))
        if moved:
            problems.append(f"{kind} rotation swipe orbited {moved}")
        if not near(rot.get("rx"), float(rot.get("beforeRx") or 0) + 1):
            problems.append(f"{kind} rotation not +1 deg {rot!r}")
        if rot.get("undo") != (rot.get("beforeUndo") or 0) + 1:
            problems.append(f"{kind} rotation undoDepth {rot!r}")

    page.evaluate(
        """() => {
          const el = document.getElementById('boxSx');
          if (el && el.blur) el.blur();
          const vp = document.getElementById('viewport');
          if (vp && vp.focus) vp.focus();
        }"""
    )
    idle = page.evaluate(SWIPE, {"id": "boxSx", "stepPx": step_px, "steps": 3, "pointerId": 43})
    print(f"{kind} unfocused {idle}", flush=True)
    if not isinstance(idle, dict):
        problems.append(f"{kind} unfocused swipe failed")
    elif idle.get("undo") != idle.get("beforeUndo") or not near(idle.get("sx"), idle.get("beforeSx")):
        problems.append(f"{kind} unfocused changed the field {idle!r}")

    page.locator("#boxSx").focus()
    up = page.evaluate(
        SWIPE,
        {"id": "boxSx", "stepPx": step_px, "steps": 0, "vertical": True, "pointerId": 44},
    )
    print(f"{kind} vertical {up}", flush=True)
    if not isinstance(up, dict):
        problems.append(f"{kind} vertical swipe failed")
    elif up.get("undo") != up.get("beforeUndo") or not near(up.get("sx"), up.get("beforeSx")):
        problems.append(f"{kind} vertical nudge {up!r}")

    cancelled = page.evaluate(
        SWIPE,
        {"id": "boxSx", "stepPx": step_px, "steps": 0, "cancelAfter": 1, "pointerId": 45},
    )
    print(f"{kind} cancel {cancelled}", flush=True)
    if not isinstance(cancelled, dict):
        problems.append(f"{kind} cancel swipe failed")
    else:
        if cancelled.get("undo") != (cancelled.get("beforeUndo") or 0) + 1:
            problems.append(f"{kind} cancel did not stop {cancelled!r}")
        if not near(cancelled.get("sx"), float(cancelled.get("beforeSx") or 0) + 1):
            problems.append(f"{kind} cancel size {cancelled!r}")
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
        print(f"PASS field_nudge_smoke {engine}", flush=True)
        return []
    finally:
        browser.close()


def run() -> int:
    gaps = deploy_smoke.libcascade_gaps()
    if gaps:
        print("SKIP field_nudge_smoke: " + "; ".join(gaps), flush=True)
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
    thread = threading.Thread(target=server.serve_forever, name="field-nudge-http", daemon=True)
    thread.start()
    try:
        with sync_playwright() as playwright:
            for engine in ("chromium", "webkit"):
                problems = run_engine(playwright, engine, origin)
                if problems:
                    print("FAIL field_nudge_smoke", flush=True)
                    for line in problems:
                        print(line, flush=True)
                    return 1
        print("PASS field_nudge_smoke", flush=True)
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
        print(f"FAIL field_nudge_smoke: {exc}", flush=True)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
