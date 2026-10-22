#!/usr/bin/env python3
"""Phone smoke for the assembled site in Chromium and WebKit.

Uses Playwright's iPhone 13 device (390x844) and the portrait checks in
deploy_smoke.py: overflow, inert panel, one-row toolbar, Info/Tree row,
Part 1 visible, one search, coverage thresholds, Home, the nav cube, and
the 3-hole plate.

Playwright lives in the gitignored builds/pwvenv. When it cannot be
imported, exit 77. Exit 1 under CI=1 only when a workflow file installs
playwright. This file does not change CI.

WebKit screenshots of the finished plate:
  %USERPROFILE%\\Pictures\\cadmvp-shots\\wasm-webkit-portrait.png
  %USERPROFILE%\\Pictures\\cadmvp-shots\\wasm-webkit-portrait-open.png
"""
from __future__ import annotations

import os
import struct
import sys
import threading
import time
import zlib
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
WORK = ROOT / "builds" / "phone-smoke"
SKIP = 77


def in_ci() -> bool:
    return os.environ.get("CI", "").strip().lower() in {"1", "true", "yes"}


def workflow_installs_playwright() -> bool:
    workflow_dir = ROOT / ".github" / "workflows"
    if not workflow_dir.is_dir():
        return False
    text = ""
    for path in sorted(workflow_dir.glob("*.yml")) + sorted(workflow_dir.glob("*.yaml")):
        text += path.read_text(encoding="utf-8", errors="replace").lower()
    return "playwright" in text


def skip_missing_playwright() -> int:
    if in_ci() and workflow_installs_playwright():
        print(
            "FAIL phone_smoke: playwright is not importable and the CI workflow installs it.",
            flush=True,
        )
        return 1
    print(
        "SKIP phone_smoke: playwright is not importable. "
        "Use builds/pwvenv/Scripts/python.exe (Playwright with WebKit and Chromium).",
        flush=True,
    )
    return SKIP


try:
    from playwright.sync_api import sync_playwright
except ImportError:
    raise SystemExit(skip_missing_playwright())

import deploy_smoke


class PwCdp:
    """Enough of the deploy_smoke CDP surface for the portrait checks."""

    def __init__(self, page: Any) -> None:
        self.page = page
        self.events: list[dict[str, Any]] = []
        self.urls: dict[str, str] = {}
        self._touch: tuple[float, float] | None = None
        self._ids: dict[int, str] = {}
        self._next = 0
        page.on("console", self._on_console)
        page.on("pageerror", self._on_pageerror)
        page.on("request", self._on_request)
        page.on("response", self._on_response)
        page.on("requestfailed", self._on_failed)

    def _request_id(self, request: Any) -> str:
        key = id(request)
        found = self._ids.get(key)
        if found:
            return found
        self._next += 1
        found = str(self._next)
        self._ids[key] = found
        return found

    def _on_console(self, msg: Any) -> None:
        if msg.type not in {"error", "assert"}:
            return
        text = str(msg.text or "")
        # WebKit logs this for the viewport key Chromium needs. The meta tag stays.
        if "interactive-widget" in text and "not recognized" in text:
            return
        args: list[dict[str, Any]] = []
        for arg in msg.args:
            try:
                args.append({"value": arg.json_value()})
            except Exception:
                args.append({"value": msg.text})
                break
        if not args:
            args.append({"value": msg.text})
        self.events.append(
            {"method": "Runtime.consoleAPICalled", "params": {"type": msg.type, "args": args}}
        )

    def _on_pageerror(self, err: Any) -> None:
        self.events.append(
            {
                "method": "Runtime.exceptionThrown",
                "params": {"exceptionDetails": {"text": str(err)}},
            }
        )

    def _on_request(self, request: Any) -> None:
        request_id = self._request_id(request)
        self.urls[request_id] = request.url
        self.events.append(
            {
                "method": "Network.requestWillBeSent",
                "params": {"requestId": request_id, "request": {"url": request.url}},
            }
        )

    def _on_response(self, response: Any) -> None:
        request = response.request
        self.events.append(
            {
                "method": "Network.responseReceived",
                "params": {
                    "requestId": self._request_id(request),
                    "response": {"url": response.url, "status": response.status},
                },
            }
        )

    def _on_failed(self, request: Any) -> None:
        error = str(request.failure or "")
        self.events.append(
            {
                "method": "Network.loadingFailed",
                "params": {
                    "requestId": self._request_id(request),
                    "errorText": error,
                    "canceled": "ERR_ABORTED" in error or "cancelled" in error.lower(),
                },
            }
        )

    def call(self, method: str, params: dict[str, Any] | None = None, timeout: float = 30) -> dict[str, Any]:
        params = params or {}
        if method in {
            "Page.enable",
            "Runtime.enable",
            "Network.enable",
            "Log.enable",
            "Network.setCacheDisabled",
            "Network.clearBrowserCache",
            "Emulation.setDeviceMetricsOverride",
            "Emulation.setTouchEmulationEnabled",
        }:
            return {}
        if method == "Page.addScriptToEvaluateOnNewDocument":
            self.page.add_init_script(params.get("source") or "")
            return {}
        if method == "Page.navigate":
            self.page.goto(
                str(params.get("url") or ""),
                wait_until="domcontentloaded",
                timeout=max(30000, int(timeout * 1000)),
            )
            return {}
        if method == "Runtime.evaluate":
            expression = str(params.get("expression") or "undefined")
            try:
                value = self.page.evaluate(expression)
            except Exception as exc:
                return {"exceptionDetails": {"text": str(exc)}, "result": {}}
            return {"result": {"value": value}}
        if method == "Input.dispatchTouchEvent":
            kind = str(params.get("type") or "")
            points = params.get("touchPoints") or []
            if kind == "touchStart" and points:
                self._touch = (float(points[0]["x"]), float(points[0]["y"]))
            elif kind == "touchEnd" and self._touch is not None:
                x, y = self._touch
                self._touch = None
                self.page.touchscreen.tap(x, y)
            return {}
        return {}

    def drain(self, wait: float) -> None:
        self.page.wait_for_timeout(int(max(0.0, wait) * 1000))

    def close(self) -> None:
        return None


def _paeth(left: int, up: int, up_left: int) -> int:
    estimate = left + up - up_left
    dl = abs(estimate - left)
    du = abs(estimate - up)
    dlu = abs(estimate - up_left)
    if dl <= du and dl <= dlu:
        return left
    if du <= dlu:
        return up
    return up_left


def decode_png_rgb(data: bytes) -> tuple[int, int, bytearray]:
    """Decode an 8-bit RGB or RGBA PNG. Returns width, height, and tightly packed RGB."""
    if data[:8] != b"\x89PNG\r\n\x1a\n":
        raise ValueError("not a png")
    offset = 8
    width = height = 0
    bit_depth = color_type = 0
    compressed = bytearray()
    while offset + 8 <= len(data):
        length = struct.unpack(">I", data[offset : offset + 4])[0]
        kind = data[offset + 4 : offset + 8]
        chunk = data[offset + 8 : offset + 8 + length]
        offset += 12 + length
        if kind == b"IHDR":
            width, height, bit_depth, color_type = struct.unpack(">IIBB", chunk[:10])
        elif kind == b"IDAT":
            compressed.extend(chunk)
        elif kind == b"IEND":
            break
    if bit_depth != 8 or color_type not in {2, 6}:
        raise ValueError(f"png {width}x{height} depth {bit_depth} type {color_type}")
    channels = 3 if color_type == 2 else 4
    raw = zlib.decompress(bytes(compressed))
    stride = width * channels
    expected = (stride + 1) * height
    if len(raw) < expected:
        raise ValueError(f"png inflated {len(raw)} < {expected}")
    rgb = bytearray(width * height * 3)
    prev = bytearray(stride)
    src = 0
    dst = 0
    for _y in range(height):
        filt = raw[src]
        src += 1
        row = bytearray(raw[src : src + stride])
        src += stride
        if filt == 1:
            for i in range(channels, stride):
                row[i] = (row[i] + row[i - channels]) & 255
        elif filt == 2:
            for i in range(stride):
                row[i] = (row[i] + prev[i]) & 255
        elif filt == 3:
            for i in range(stride):
                left = row[i - channels] if i >= channels else 0
                row[i] = (row[i] + ((left + prev[i]) // 2)) & 255
        elif filt == 4:
            for i in range(stride):
                left = row[i - channels] if i >= channels else 0
                up_left = prev[i - channels] if i >= channels else 0
                row[i] = (row[i] + _paeth(left, prev[i], up_left)) & 255
        elif filt != 0:
            raise ValueError(f"png filter {filt}")
        prev = row
        if channels == 3:
            rgb[dst : dst + stride] = row
            dst += stride
        else:
            for x in range(width):
                i = x * 4
                rgb[dst] = row[i]
                rgb[dst + 1] = row[i + 1]
                rgb[dst + 2] = row[i + 2]
                dst += 3
    return width, height, rgb


def canvas_shot_stats(png: bytes) -> dict[str, float]:
    """Sample the canvas bitmap, including the view-cube corner.

    A missing preserveDrawingBuffer flag makes a later readPixels call all zeros.
    This samples the presented screenshot instead. The in-frame sample is logged
    separately from window.__cadcamFrameSample.
    """
    width, height, rgb = decode_png_rgb(png)
    samples: list[tuple[int, int, int]] = []

    def take(x0: float, x1: float, y0: float, y1: float) -> None:
        step_x = max(1, width // 70)
        step_y = max(1, height // 70)
        left = max(0, int(width * x0))
        right = min(width, int(width * x1))
        top = max(0, int(height * y0))
        bottom = min(height, int(height * y1))
        for y in range(top, bottom, step_y):
            row = y * width
            for x in range(left, right, step_x):
                i = (row + x) * 3
                samples.append((rgb[i], rgb[i + 1], rgb[i + 2]))

    take(0.18, 0.72, 0.22, 0.72)
    take(0.70, 0.98, 0.02, 0.30)
    if not samples:
        return {"width": float(width), "height": float(height), "q32": 0.0, "var": 0.0, "n": 0.0}
    buckets = {(r // 32, g // 32, b // 32) for r, g, b in samples}
    lums = [0.2126 * r + 0.7152 * g + 0.0722 * b for r, g, b in samples]
    mean = sum(lums) / len(lums)
    var = sum((value - mean) ** 2 for value in lums) / len(lums)
    return {
        "width": float(width),
        "height": float(height),
        "q32": float(len(buckets)),
        "var": float(var),
        "n": float(len(samples)),
    }


def gl_report(page: Any, engine: str) -> None:
    info = page.evaluate(
        """() => {
          var gl = window.__cadcamGlInfo || {};
          var sample = window.__cadcamFrameSample || {};
          return {
            isWebGL2: gl.isWebGL2 === true,
            contextLost: gl.contextLost || 0,
            lostType: gl.lostType || '',
            afterRender: sample.afterRender === true,
            frameDistinct: sample.distinct32 || 0,
            frameVar: sample.variance || 0,
            colors: sample.colors || [],
            error: sample.error || ''
          };
        }"""
    )
    if not isinstance(info, dict):
        print(f"gl {engine} unreadable {info!r}", flush=True)
        return
    print(
        f"gl {engine} isWebGL2={info.get('isWebGL2')} "
        f"contextLost={info.get('contextLost')} "
        f"lostType={info.get('lostType') or '-'} "
        f"frameAfterRender={info.get('afterRender')} "
        f"frameDistinct32={info.get('frameDistinct')} "
        f"frameVar={float(info.get('frameVar') or 0):.1f} "
        f"frameColors={info.get('colors')} "
        f"frameError={info.get('error') or '-'}",
        flush=True,
    )


def canvas_pixel_problems(page: Any, engine: str) -> list[str]:
    """Fail when the presented 3D canvas is blank or one flat colour."""
    page.evaluate(
        "() => new Promise(function (resolve) {"
        "requestAnimationFrame(function () { requestAnimationFrame(resolve); });"
        "})"
    )
    gl_report(page, engine)
    png = page.locator("#canvas").screenshot(animations="disabled")
    stats = canvas_shot_stats(png)
    q32 = int(stats["q32"])
    variance = float(stats["var"])
    print(
        f"canvas pixels {engine} {int(stats['width'])}x{int(stats['height'])} "
        f"n={int(stats['n'])} q32={q32} var={variance:.1f}",
        flush=True,
    )
    if q32 < 4 or variance < 80:
        return [
            f"{engine} canvas blank or uniform "
            f"q32={q32} var={variance:.1f} (need q32>=4 and var>=80)"
        ]
    return []


def _toast_text(page: Any) -> list[str]:
    value = page.evaluate(
        "() => Array.from(document.querySelectorAll('#toasts .toast')).map(function (node) {"
        "return node.textContent || '';"
        "})"
    )
    if not isinstance(value, list):
        return []
    return [str(item) for item in value]


def _wait_toasts(page: Any, timeout: float = 4.0) -> bool:
    deadline = time.time() + timeout
    while time.time() < deadline:
        if not _toast_text(page):
            return True
        page.wait_for_timeout(100)
    return False


def _is_plate_blue(r: int, g: int, b: int) -> bool:
    return b > 110 and g > 80 and b > r + 25 and r < 170


def _is_label_light(r: int, g: int, b: int) -> bool:
    return r > 170 and g > 180 and b > 180


def _near(r: int, g: int, b: int, rr: int, gg: int, bb: int, tol: int) -> bool:
    return abs(r - rr) <= tol and abs(g - gg) <= tol and abs(b - bb) <= tol


def _frame_pixels(png: bytes, aim: dict[str, Any], cube: dict[str, Any]) -> list[str]:
    """The presented canvas, not the CSS projection, has to hold the plate."""
    width, height, rgb = decode_png_rgb(png)
    plate = aim.get("plate")
    if not isinstance(plate, dict):
        return ["webkit screenshot: no plate bounds"]
    try:
        css_w = float(plate["canvasW"])
        css_h = float(plate["canvasH"])
        min_x = float(plate["minX"])
        min_y = float(plate["minY"])
        max_x = float(plate["maxX"])
        max_y = float(plate["maxY"])
        cube_x = float(cube["x"])
        cube_y = float(cube["y"])
        cube_w = float(cube["w"])
        cube_h = float(cube["h"])
    except (KeyError, TypeError, ValueError):
        return [f"webkit screenshot: plate bounds {plate!r} cube {cube!r}"]
    if css_w < 2 or css_h < 2 or width < 2 or height < 2:
        return [f"webkit screenshot: canvas {css_w}x{css_h} png {width}x{height}"]
    margin = 12.0
    if min_x < margin or min_y < margin or max_x > css_w - margin or max_y > css_h - margin:
        return [
            "webkit screenshot: plate touches the canvas edge "
            f"{min_x:.1f},{min_y:.1f} {max_x:.1f},{max_y:.1f} on {css_w:.0f}x{css_h:.0f}"
        ]
    sx = width / css_w
    sy = height / css_h

    def colors(x0: float, y0: float, x1: float, y1: float) -> list[tuple[int, int, int]]:
        left = max(0, min(width - 1, int(x0 * sx)))
        right = max(left + 1, min(width, int(x1 * sx)))
        top = max(0, min(height - 1, int(y0 * sy)))
        bottom = max(top + 1, min(height, int(y1 * sy)))
        found: list[tuple[int, int, int]] = []
        for y in range(top, bottom):
            row = y * width
            for x in range(left, right):
                i = (row + x) * 3
                found.append((rgb[i], rgb[i + 1], rgb[i + 2]))
        return found

    cx = (min_x + max_x) * 0.5
    cy = (min_y + max_y) * 0.5
    center = colors(cx - 8, cy - 8, cx + 8, cy + 8)
    plate_hits = sum(1 for r, g, b in center if _is_plate_blue(r, g, b))
    if not center or plate_hits * 2 < len(center):
        mid = center[len(center) // 2] if center else None
        return [
            "webkit screenshot: plate centre is not the body "
            f"{plate_hits}/{len(center)} {mid}"
        ]
    corner = colors(4, css_h - 18, 18, css_h - 4)
    if any(_is_plate_blue(r, g, b) for r, g, b in corner):
        return ["webkit screenshot: plate still fills a canvas corner"]
    inset = 0.18
    cube_colors = colors(
        cube_x + cube_w * inset,
        cube_y + cube_h * inset,
        cube_x + cube_w * (1 - inset),
        cube_y + cube_h * (1 - inset),
    )
    lights = sum(1 for r, g, b in cube_colors if _is_label_light(r, g, b))
    blues = sum(1 for r, g, b in cube_colors if _is_plate_blue(r, g, b))
    if lights < 8 or (cube_colors and blues * 2 > len(cube_colors)):
        return [
            "webkit screenshot: view cube not drawn "
            f"lights={lights} blues={blues}/{len(cube_colors)}"
        ]
    grid = 0
    step = 3
    for y in range(0, height, step):
        css_y = y / sy
        if cube_y - 2 <= css_y <= cube_y + cube_h + 2:
            continue
        if min_y - 4 <= css_y <= max_y + 4:
            continue
        row = y * width
        for x in range(0, width, step):
            css_x = x / sx
            if cube_x - 2 <= css_x <= cube_x + cube_w + 2:
                continue
            if min_x - 4 <= css_x <= max_x + 4:
                continue
            i = (row + x) * 3
            r, g, b = rgb[i], rgb[i + 1], rgb[i + 2]
            if _is_plate_blue(r, g, b):
                continue
            if _near(r, g, b, 110, 143, 150, 36) or _near(r, g, b, 30, 74, 82, 16):
                grid += 1
    if grid < 8:
        return [f"webkit screenshot: grid not in frame ({grid} px)"]
    return []


def _frame_plate(page: Any, cdp: PwCdp) -> list[str]:
    """Home, then an empty tap so the plate, grid, and view cube are unobstructed."""
    home = deploy_smoke.tap_selector(cdp, "#vcHome", "webkit home")
    if home:
        return home
    deadline = time.time() + 4
    aim: Any = None
    while time.time() < deadline:
        cdp.drain(0.15)
        aim = page.evaluate("() => window.__cadcamHomeAim ? window.__cadcamHomeAim() : null")
        if isinstance(aim, dict):
            target = aim.get("target") or [9, 9, 9]
            try:
                settled = (
                    abs(float(target[0])) < 0.05
                    and abs(float(target[1])) < 0.05
                    and abs(float(target[2])) < 0.05
                    and aim.get("allInside") is True
                    and int(aim.get("corners") or 0) == 8
                )
            except (TypeError, ValueError, IndexError):
                settled = False
            if settled:
                break
    else:
        return [f"webkit screenshot: home aim {aim!r}"]
    points = page.evaluate(
        """() => {
          const canvas = document.getElementById('canvas').getBoundingClientRect();
          const panel = document.getElementById('dimPanel');
          const pr = panel ? panel.getBoundingClientRect() : null;
          const pts = [];
          for (let i = 0; i < 8; i += 1) {
            const x = canvas.left + 18 + (i % 2) * 22;
            const y = canvas.top + canvas.height * (0.58 + i * 0.04);
            const onPanel = pr && x >= pr.left && x <= pr.right && y >= pr.top && y <= pr.bottom;
            if (!onPanel && y > canvas.top + 8 && y < canvas.bottom - 8) pts.push({x: x, y: y});
          }
          return pts;
        }"""
    )
    if not isinstance(points, list) or not points:
        return ["webkit screenshot: no empty-canvas point"]
    cleared = False
    last: Any = None
    for point in points:
        if not isinstance(point, dict):
            continue
        page.touchscreen.tap(float(point["x"]), float(point["y"]))
        cdp.drain(0.25)
        payload = deploy_smoke.eval_state(cdp)
        state = (payload or {}).get("state") if isinstance(payload, dict) else None
        last = state
        if (
            isinstance(state, dict)
            and int(state.get("selectionCount") or 0) == 0
            and int(state.get("holeCount") or 0) == 3
            and state.get("gateOcct") == "PASS"
        ):
            cleared = True
            break
    if not cleared:
        count = last.get("selectionCount") if isinstance(last, dict) else None
        return [f"webkit screenshot: selection stayed {count!r}"]
    aim = page.evaluate("() => window.__cadcamHomeAim ? window.__cadcamHomeAim() : null")
    if not isinstance(aim, dict) or aim.get("allInside") is not True:
        return [f"webkit screenshot: plate left the frame {aim!r}"]
    plate = aim.get("plate") if isinstance(aim.get("plate"), dict) else {}
    print(
        "webkit home "
        f"target={aim.get('target')} "
        f"plate=({plate.get('minX')},{plate.get('minY')})-({plate.get('maxX')},{plate.get('maxY')}) "
        f"css={plate.get('canvasW')}x{plate.get('canvasH')} "
        f"buf={plate.get('buffer')} dpr-cam={plate.get('cam')}",
        flush=True,
    )
    cube = page.evaluate(
        """() => {
          const el = document.getElementById('viewCube');
          const canvas = document.getElementById('canvas');
          const r = el.getBoundingClientRect();
          const c = canvas.getBoundingClientRect();
          return {x: r.x - c.x, y: r.y - c.y, w: r.width, h: r.height,
            pageX: r.x, pageY: r.y,
            vw: window.innerWidth, vh: window.innerHeight};
        }"""
    )
    if not isinstance(cube, dict):
        return ["webkit screenshot: view cube missing"]
    try:
        inside = (
            float(cube["w"]) >= 32
            and float(cube["h"]) >= 32
            and float(cube["pageX"]) >= -1
            and float(cube["pageY"]) >= -1
            and float(cube["pageX"]) + float(cube["w"]) <= float(cube["vw"]) + 1
            and float(cube["pageY"]) + float(cube["h"]) <= float(cube["vh"]) + 1
        )
    except (KeyError, TypeError, ValueError):
        inside = False
    if not inside:
        return [f"webkit screenshot: view cube {cube!r}"]
    if not _wait_toasts(page):
        return [f"webkit screenshot: toast still up {_toast_text(page)!r}"]
    png = page.locator("#canvas").screenshot(animations="disabled")
    return _frame_pixels(png, aim, cube)


def shoot_plate(page: Any, cdp: PwCdp) -> list[str]:
    """Home and clear the selection, then save the plate collapsed and open."""
    shots = Path.home() / "Pictures" / "cadmvp-shots"
    shots.mkdir(parents=True, exist_ok=True)
    payload = deploy_smoke.eval_state(cdp)
    state = (payload or {}).get("state") if isinstance(payload, dict) else None
    if not isinstance(state, dict) or state.get("dimSheetOpen") is not False:
        return ["webkit screenshot: dimension panel was not collapsed"]
    if int(state.get("holeCount") or 0) != 3 or state.get("gateOcct") != "PASS":
        return [
            "webkit screenshot: plate gate "
            f"{state.get('gateOcct')!r} holes {state.get('holeCount')!r}"
        ]
    framed = _frame_plate(page, cdp)
    if framed:
        return framed
    collapsed = shots / "wasm-webkit-portrait.png"
    page.screenshot(path=str(collapsed))
    print(f"screenshot {collapsed}", flush=True)
    opened = deploy_smoke.tap_selector(cdp, "#dimToggle", "webkit panel")
    if opened:
        return opened
    deadline = time.time() + 5
    while time.time() < deadline:
        cdp.drain(0.2)
        payload = deploy_smoke.eval_state(cdp)
        state = (payload or {}).get("state") if isinstance(payload, dict) else None
        if isinstance(state, dict) and state.get("dimSheetOpen") is True:
            if not _wait_toasts(page):
                return [f"webkit screenshot: open toast {_toast_text(page)!r}"]
            open_path = shots / "wasm-webkit-portrait-open.png"
            page.screenshot(path=str(open_path))
            print(f"screenshot {open_path}", flush=True)
            return []
    return ["webkit screenshot: dimension panel did not open"]


def run_engine(playwright: Any, engine: str, origin: str, shoot: bool) -> list[str]:
    browser = getattr(playwright, engine).launch(headless=True)
    try:
        device = dict(playwright.devices["iPhone 13"])
        device.pop("default_browser_type", None)
        # Playwright 1.64's iPhone 13 layout viewport is 390x664 under Safari chrome.
        # The phone screen, and these portrait checks, are 390x844.
        device["screen"] = {"width": 390, "height": 844}
        device["viewport"] = {"width": 390, "height": 844}
        context = browser.new_context(**device)
        page = context.new_page()
        page.add_init_script(deploy_smoke.HOOK)
        page.set_default_timeout(deploy_smoke.PAGE_TIMEOUT_S * 1000)
        cdp = PwCdp(page)
        print(f"phone {engine} iPhone 13", flush=True)
        portrait = deploy_smoke.run_portrait(cdp, origin)
        if portrait:
            return [f"{engine} portrait", *portrait[:40]]
        nav = deploy_smoke.nav_cube_problems(cdp)
        if nav:
            return [f"{engine} nav cube", *nav[:40]]
        print("NAVCUBE_DONE", flush=True)
        holes = deploy_smoke.run_portrait_holes(cdp, origin)
        if holes:
            return [f"{engine} portrait_holes", *holes[:40]]
        pixels = canvas_pixel_problems(page, engine)
        if pixels:
            return [f"{engine} canvas", *pixels]
        if shoot:
            shots = shoot_plate(page, cdp)
            if shots:
                return [f"{engine} screenshot", *shots]
        print(f"PASS phone_smoke {engine}", flush=True)
        return []
    finally:
        browser.close()


def run_create_desktop(playwright: Any, engine: str, origin: str) -> list[str]:
    """1440x900: the Create menu is a popover, and the bottom sheet is not."""
    browser = getattr(playwright, engine).launch(headless=True)
    try:
        context = browser.new_context(
            viewport={"width": 1440, "height": 900},
            device_scale_factor=1,
            is_mobile=False,
            has_touch=False,
        )
        page = context.new_page()
        page.add_init_script(deploy_smoke.HOOK)
        page.set_default_timeout(deploy_smoke.PAGE_TIMEOUT_S * 1000)
        cdp = PwCdp(page)
        print(f"create shape {engine} 1440x900", flush=True)
        _state, load_problems = deploy_smoke.wait_for_case(
            cdp, origin, origin + "/", deploy_smoke.PAGE_TIMEOUT_S
        )
        if load_problems:
            return [f"{engine} 1440 load", *load_problems[:20]]
        found = deploy_smoke.create_menu_problems(cdp)
        if found:
            return [f"{engine} 1440 create", *found]
        print(f"PASS create popover {engine} 1440x900", flush=True)
        return []
    finally:
        browser.close()


def run() -> int:
    gaps = deploy_smoke.libcascade_gaps()
    if gaps:
        text = "; ".join(gaps)
        if in_ci():
            print(f"FAIL phone_smoke: {text}", flush=True)
            return 1
        print(f"SKIP phone_smoke: {text}", flush=True)
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
    thread = threading.Thread(target=server.serve_forever, name="phone-smoke-http", daemon=True)
    thread.start()
    try:
        with sync_playwright() as playwright:
            for engine, shoot in (("webkit", True), ("chromium", False)):
                problems = run_engine(playwright, engine, origin, shoot)
                if problems:
                    print("FAIL phone_smoke", flush=True)
                    for line in problems:
                        print(line, flush=True)
                    return 1
            for engine in ("webkit", "chromium"):
                problems = run_create_desktop(playwright, engine, origin)
                if problems:
                    print("FAIL phone_smoke", flush=True)
                    for line in problems:
                        print(line, flush=True)
                    return 1
        print("PASS phone_smoke", flush=True)
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
        print(f"FAIL phone_smoke: {exc}", flush=True)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
