#!/usr/bin/env python3
"""Phone smoke for the assembled site in Chromium and WebKit.

Uses Playwright's iPhone 13 device (390x844) and the portrait checks in
deploy_smoke.py: overflow, inert panel, one-row toolbar, Info/Tree row,
Part 1 visible, one search, coverage thresholds, Home, and the 3-hole plate.

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


def shoot_plate(page: Any, cdp: PwCdp) -> list[str]:
    """Save the WebKit plate collapsed, then with the dimension panel open."""
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
