#!/usr/bin/env python3
"""Swipe #viewCube from Front onto the neighbouring face.

Desktop Chromium uses a mouse drag on the cube overlay. WebKit and a
390x844 Chromium context dispatch PointerEvents on #viewCube. Each of
left, right, up, and down is reset through the Front button, then swiped
40 px, including a slow drag longer than 400 ms. The camera direction and
cubeFaceName must match the next face. A 10 px nudge stays on Front.
A tap, then a swipe, then another tap inside one turn must land on the
swiped face, not Home.

Wired into CTest next to gizmo_drag_smoke. Playwright lives in the pwvenv.
Exit 77 when it cannot be imported.
"""
from __future__ import annotations

import math
import sys
import threading
import time
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
WORK = ROOT / "builds" / "view-cube-smoke"
SKIP = 77
SWIPE_PX = 40
NUDGE_PX = 10
SLOW_S = 0.5
FRONT = (0.0, 0.0, 1.0)
RIGHT = (1.0, 0.0, 0.0)
LEFT = (-1.0, 0.0, 0.0)
TOP = (0.0, 1.0, 0.0)
BOTTOM = (0.0, -1.0, 0.0)
# Screen up is negative clientY. Left from Front lands on Right.
PHONE_SWIPES = (
    ("left", -SWIPE_PX, 0.0, RIGHT, "right", "Right"),
    ("right", SWIPE_PX, 0.0, LEFT, "left", "Left"),
    ("up", 0.0, -SWIPE_PX, TOP, "top", "Top"),
    ("down", 0.0, SWIPE_PX, BOTTOM, "bottom", "Bottom"),
)


def skip_missing_playwright() -> int:
    print(
        "SKIP view_cube_swipe_smoke: playwright is not importable. "
        "Use builds/pwvenv/Scripts/python.exe.",
        flush=True,
    )
    return SKIP


try:
    from playwright.sync_api import sync_playwright
except ImportError:
    raise SystemExit(skip_missing_playwright())

import deploy_smoke


READ_NAV = """() => {
  const nav = window.__cadcamNavCube ? window.__cadcamNavCube() : null;
  const s = window.__cadcamExportState || {};
  const hint = document.getElementById('statusHint');
  const label = document.getElementById('viewLabel');
  return {
    nav: nav,
    hint: hint ? hint.textContent : '',
    viewLabel: label ? label.textContent : '',
    selectionCount: s.selectionCount,
    selectionMode: s.selectionMode
  };
}"""

CUBE_SWIPE = """({down, up, phase}) => {
  const el = document.getElementById('viewCube');
  if (!el) return 'missing';
  function fire(type, x, y) {
    const ending = type === 'pointerup' || type === 'pointercancel';
    el.dispatchEvent(new PointerEvent(type, {
      bubbles: true,
      cancelable: true,
      pointerId: 11,
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
  if (phase === 'cancel') {
    fire('pointercancel', up.x, up.y);
    return 'cancel';
  }
  fire('pointerup', up.x, up.y);
  return 'up';
}"""

# Tap, swipe, tap in one turn. Separate CDP calls can miss the 320 ms window.
TAP_SWIPE_TAP = """({x, y, dx, dy, pointerType}) => {
  const el = document.getElementById('viewCube');
  if (!el) return 'missing';
  const kind = pointerType || 'touch';
  function fire(type, px, py) {
    const ending = type === 'pointerup' || type === 'pointercancel';
    el.dispatchEvent(new PointerEvent(type, {
      bubbles: true,
      cancelable: true,
      pointerId: 21,
      pointerType: kind,
      isPrimary: true,
      button: 0,
      buttons: ending ? 0 : 1,
      clientX: px,
      clientY: py,
      width: 24,
      height: 24
    }));
  }
  function tap(px, py) {
    fire('pointerdown', px, py);
    fire('pointerup', px, py);
  }
  function swipe(px, py, ex, ey) {
    fire('pointerdown', px, py);
    fire('pointermove', (px + ex) / 2, (py + ey) / 2);
    fire('pointermove', ex, ey);
    fire('pointerup', ex, ey);
  }
  tap(x, y);
  swipe(x, y, x + dx, y + dy);
  tap(x, y);
  return 'done';
}"""

TAP_AT = """({x, y}) => {
  const el = document.elementFromPoint(x, y) || document.getElementById('viewCube');
  function fire(type) {
    el.dispatchEvent(new PointerEvent(type, {
      bubbles: true,
      cancelable: true,
      pointerId: 14,
      pointerType: 'touch',
      isPrimary: true,
      button: 0,
      buttons: type === 'pointerup' ? 0 : 1,
      clientX: x,
      clientY: y,
      width: 24,
      height: 24
    }));
  }
  fire('pointerdown');
  fire('pointerup');
  if (el.closest && el.closest('button, a, input, textarea, select')) return 'button';
  return el.id || el.tagName;
}"""


def angle_deg(a: list[Any] | tuple[float, ...], b: tuple[float, float, float]) -> float:
    dot = float(a[0]) * b[0] + float(a[1]) * b[1] + float(a[2]) * b[2]
    dot = max(-1.0, min(1.0, dot))
    return math.degrees(math.acos(dot))


def read_nav(page: Any) -> dict[str, Any]:
    value = page.evaluate(READ_NAV)
    if not isinstance(value, dict):
        return {}
    return value


def direction_of(state: dict[str, Any]) -> list[float] | None:
    nav = state.get("nav")
    if not isinstance(nav, dict):
        return None
    direction = nav.get("direction")
    if not isinstance(direction, list) or len(direction) != 3:
        return None
    return [float(direction[0]), float(direction[1]), float(direction[2])]


def wait_face(page: Any, axis: tuple[float, float, float], label: str) -> list[str]:
    last: dict[str, Any] | None = None
    t0 = time.time()
    while time.time() - t0 < 1.5:
        last = read_nav(page)
        nav = last.get("nav") if isinstance(last.get("nav"), dict) else None
        if isinstance(nav, dict) and nav.get("animating") is True:
            time.sleep(0.02)
            continue
        direction = direction_of(last)
        if direction is None:
            time.sleep(0.02)
            continue
        if angle_deg(direction, axis) <= 1.0:
            print(
                f"{label}: {angle_deg(direction, axis):.3f} deg "
                f"face {nav.get('face')!r} hint {last.get('hint')!r}",
                flush=True,
            )
            return []
        time.sleep(0.02)
    direction = direction_of(last or {})
    nav = (last or {}).get("nav") if isinstance((last or {}).get("nav"), dict) else {}
    angle = angle_deg(direction, axis) if direction else 999.0
    return [
        f"{label} off axis {angle:.2f} deg dir {direction!r} "
        f"animating {nav.get('animating')!r} face {nav.get('face')!r}"
    ]


def cube_center(page: Any) -> dict[str, float] | None:
    box = page.locator("#viewCube").bounding_box()
    if not box:
        return None
    return {
        "x": float(box["x"]) + float(box["width"]) / 2,
        "y": float(box["y"]) + float(box["height"]) / 2,
        "w": float(box["width"]),
        "h": float(box["height"]),
    }


def mouse_drag(page: Any, down: dict[str, float], up: dict[str, float]) -> None:
    page.mouse.move(down["x"], down["y"])
    page.mouse.down()
    page.mouse.move((down["x"] + up["x"]) / 2, (down["y"] + up["y"]) / 2)
    page.mouse.move(up["x"], up["y"])
    page.mouse.up()


def touch_drag(page: Any, down: dict[str, float], up: dict[str, float]) -> None:
    page.evaluate(CUBE_SWIPE, {"down": down, "up": up, "phase": "down"})
    page.evaluate(CUBE_SWIPE, {"down": down, "up": up, "phase": "up"})


def pointer_drag(
    page: Any,
    down: dict[str, float],
    up: dict[str, float],
    slow: bool = False,
    cancel: bool = False,
) -> None:
    page.evaluate(CUBE_SWIPE, {"down": down, "up": up, "phase": "down"})
    if slow:
        time.sleep(SLOW_S)
    phase = "cancel" if cancel else "up"
    page.evaluate(CUBE_SWIPE, {"down": down, "up": up, "phase": phase})


def face_problems(page: Any, axis: tuple[float, float, float], face: str, label: str, tag: str) -> list[str]:
    problems = wait_face(page, axis, tag)
    after = read_nav(page)
    nav = after.get("nav") if isinstance(after.get("nav"), dict) else {}
    direction = direction_of(after)
    if nav.get("snapFace") != face:
        problems.append(
            f"{tag} cubeFaceName {nav.get('snapFace')!r} want {face!r} dir {direction!r}"
        )
    if str(after.get("viewLabel") or "") != label:
        problems.append(f"{tag} viewLabel {after.get('viewLabel')!r}")
    hint = str(after.get("hint") or "")
    if "Orbit" in hint:
        problems.append(f"{tag} hint {hint!r}")
    return problems


def outside_face_zone(page: Any, cube: dict[str, float], name: str | None = None) -> dict[str, Any] | None:
    state = read_nav(page)
    nav = state.get("nav") if isinstance(state.get("nav"), dict) else {}
    zones = nav.get("zones") if isinstance(nav.get("zones"), list) else []
    left = cube["x"] - cube["w"] / 2
    top = cube["y"] - cube["h"] / 2
    for zone in zones:
        if not isinstance(zone, dict) or zone.get("kind") != "face":
            continue
        if name and zone.get("name") != name:
            continue
        x = float(zone["x"])
        y = float(zone["y"])
        if left <= x <= left + cube["w"] and top <= y <= top + cube["h"]:
            continue
        hit = page.evaluate(
            """({x, y}) => {
              const el = document.elementFromPoint(x, y);
              if (!el) return '';
              if (el.closest && el.closest('button, a, input, textarea, select')) return 'button';
              return el.id || el.tagName;
            }""",
            {"x": x, "y": y},
        )
        if hit in {"", "button"}:
            continue
        return zone
    return None


def run_phone_swipes(page: Any, kind: str) -> list[str]:
    """Four directions, fast and slow, through pointer events on #viewCube."""
    problems: list[str] = []
    select_n = read_nav(page).get("selectionCount")
    for name, dx, dy, axis, face, label in PHONE_SWIPES:
        for slow in (False, True):
            pace = "slow" if slow else "fast"
            tag = f"{kind} {pace} {name}"
            go_front(page)
            reset = wait_face(page, FRONT, f"{tag} front")
            if reset:
                problems.extend(reset)
                continue
            cube = cube_center(page)
            if not cube:
                problems.append(f"{tag} view cube missing")
                continue
            up = {"x": cube["x"] + dx, "y": cube["y"] + dy}
            pointer_drag(page, cube, up, slow=slow)
            problems.extend(face_problems(page, axis, face, label, tag))
    go_front(page)
    cancel_reset = wait_face(page, FRONT, f"{kind} cancel front")
    problems.extend(cancel_reset)
    cube = cube_center(page)
    if cube and not cancel_reset:
        pointer_drag(
            page,
            cube,
            {"x": cube["x"] - SWIPE_PX, "y": cube["y"]},
            slow=True,
            cancel=True,
        )
        time.sleep(0.35)
        cancelled = read_nav(page)
        direction = direction_of(cancelled)
        nav = cancelled.get("nav") if isinstance(cancelled.get("nav"), dict) else {}
        if direction is None or angle_deg(direction, FRONT) > 1.0 or nav.get("animating") is True:
            problems.append(f"{kind} pointercancel moved {direction!r} face {nav.get('face')!r}")
        else:
            print(f"{kind} pointercancel stayed Front", flush=True)
    zone = outside_face_zone(page, cube, "right") if cube else None
    if not zone:
        problems.append(f"{kind} phone right zone missing")
    else:
        go_front(page)
        zreset = wait_face(page, FRONT, f"{kind} zone tap front")
        problems.extend(zreset)
        if not zreset:
            hit = page.evaluate(TAP_AT, {"x": float(zone["x"]), "y": float(zone["y"])})
            print(f"{kind} tap zone right on {hit}", flush=True)
            problems.extend(face_problems(page, RIGHT, "right", "Right", f"{kind} tap right"))
    after = read_nav(page)
    if after.get("selectionCount") != select_n:
        problems.append(
            f"{kind} phone selection {after.get('selectionCount')!r} was {select_n!r}"
        )
    return problems


def run_tap_swipe_tap(page: Any, kind: str) -> list[str]:
    """Tap, swipe left, tap again. The tap after the swipe must not go Home."""
    go_front(page)
    reset = wait_face(page, FRONT, f"{kind} tap-swipe-tap front")
    if reset:
        return reset
    cube = cube_center(page)
    if not cube:
        return [f"{kind} tap-swipe-tap cube missing"]
    fired = page.evaluate(
        TAP_SWIPE_TAP,
        {
            "x": cube["x"],
            "y": cube["y"],
            "dx": -SWIPE_PX,
            "dy": 0.0,
            "pointerType": "mouse" if kind == "mouse" else "touch",
        },
    )
    if fired != "done":
        return [f"{kind} tap-swipe-tap {fired!r}"]
    problems = face_problems(page, RIGHT, "right", "Right", f"{kind} tap-swipe-tap")
    after = read_nav(page)
    hint = str(after.get("hint") or "")
    if "Home" in hint:
        problems.append(f"{kind} tap-swipe-tap hint {hint!r}")
    return problems


def go_front(page: Any) -> None:
    page.evaluate(
        """() => {
          const btn = document.querySelector('[data-view="front"]');
          if (btn) btn.click();
        }"""
    )


def run_case(page: Any, kind: str) -> list[str]:
    problems: list[str] = []
    page.wait_for_function(
        """() => {
          const s = window.__cadcamExportState;
          return !!(s && s.occtReady === true && typeof window.__cadcamNavCube === 'function');
        }""",
        timeout=deploy_smoke.PAGE_TIMEOUT_S * 1000,
    )
    page.locator("#viewCube").wait_for(state="visible")
    before = read_nav(page)
    select_n = before.get("selectionCount")
    print(f"{kind} start {before.get('viewLabel')!r} sel {select_n}", flush=True)
    go_front(page)
    problems.extend(wait_face(page, FRONT, f"{kind} front"))
    if problems:
        return problems
    cube = cube_center(page)
    if not cube:
        return [f"{kind} view cube missing"]
    print(f"{kind} cube {cube['w']:.0f}x{cube['h']:.0f} at {cube['x']:.1f},{cube['y']:.1f}", flush=True)
    nudge_up = {"x": cube["x"] - NUDGE_PX, "y": cube["y"]}
    if kind == "touch":
        touch_drag(page, cube, nudge_up)
    else:
        mouse_drag(page, cube, nudge_up)
    time.sleep(0.35)
    nudged = read_nav(page)
    nudged_dir = direction_of(nudged)
    if nudged_dir is None or angle_deg(nudged_dir, FRONT) > 1.0:
        problems.append(
            f"{kind} 10px nudge left Front {nudged_dir!r} hint {nudged.get('hint')!r}"
        )
        return problems
    swipe_up = {"x": cube["x"] - SWIPE_PX, "y": cube["y"]}
    if kind == "touch":
        touch_drag(page, cube, swipe_up)
    else:
        mouse_drag(page, cube, swipe_up)
    problems.extend(wait_face(page, RIGHT, f"{kind} swipe left"))
    after = read_nav(page)
    hint = str(after.get("hint") or "")
    if "Orbit" in hint:
        problems.append(f"{kind} hint {hint!r}")
    if after.get("selectionCount") != select_n:
        problems.append(
            f"{kind} selection {after.get('selectionCount')!r} was {select_n!r}"
        )
    nav = after.get("nav") if isinstance(after.get("nav"), dict) else {}
    try:
        budget = float(nav.get("lastSnapBudget") or 0)
        elapsed = float(nav.get("lastSnapMs") or 0)
    except (TypeError, ValueError):
        budget = 0.0
        elapsed = 0.0
    if budget > 250.0:
        problems.append(f"{kind} snap ease {budget:.0f} ms > 250")
    if elapsed >= 500.0:
        problems.append(f"{kind} snap frame {elapsed:.0f} ms")
    if str(after.get("viewLabel") or "") != "Right":
        problems.append(f"{kind} viewLabel {after.get('viewLabel')!r}")
    if kind == "touch":
        problems.extend(run_phone_swipes(page, kind))
    problems.extend(run_tap_swipe_tap(page, kind))
    return problems


def run_engine(playwright: Any, engine: str, origin: str, phone: bool = False) -> list[str]:
    browser = getattr(playwright, engine).launch(headless=True)
    try:
        if phone:
            context = browser.new_context(
                viewport={"width": 390, "height": 844},
                device_scale_factor=1,
                is_mobile=True,
                has_touch=True,
            )
            kind = "touch"
        elif engine == "webkit":
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
        label = "chromium-390" if phone else engine
        if errors:
            problems = [f"{kind} js: {item}" for item in errors[:8]] + problems
        if problems:
            return [f"{label} {kind}", *problems]
        print(f"PASS view_cube_swipe_smoke {label}", flush=True)
        return []
    finally:
        browser.close()


def run() -> int:
    gaps = deploy_smoke.libcascade_gaps()
    if gaps:
        print("SKIP view_cube_swipe_smoke: " + "; ".join(gaps), flush=True)
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
    thread = threading.Thread(target=server.serve_forever, name="view-cube-swipe-http", daemon=True)
    thread.start()
    try:
        with sync_playwright() as playwright:
            for engine, phone in (("chromium", False), ("webkit", False), ("chromium", True)):
                problems = run_engine(playwright, engine, origin, phone)
                if problems:
                    print("FAIL view_cube_swipe_smoke", flush=True)
                    for line in problems:
                        print(line, flush=True)
                    return 1
        print("PASS view_cube_swipe_smoke", flush=True)
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
        print(f"FAIL view_cube_swipe_smoke: {exc}", flush=True)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
