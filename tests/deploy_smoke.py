#!/usr/bin/env python3
"""Deploy smoke test for the GitHub Pages tree.

Assembles the site with web/assemble_site.py into gitignored
builds/deploy-smoke/_site, serves that directory over HTTP, and loads it
in headless Edge or Chromium through the Chrome DevTools Protocol with
the HTTP cache disabled.

Fails when any same-origin response is not 2xx, or when the page reports
a JavaScript exception, an unhandled rejection, or a console error.

Asserts window.__cadcamExportState.occtReady for:
  ?fixture=closed_box   OCCT gate PASS, Export enabled
  ?fixture=open_box     OCCT gate FAIL, units pass, Export enabled
  ?primitive=box&select=face   OCCT ready, one face selected
  ?demo=lbracket        final L-bracket OCCT gate PASS (app defaults)
  ?demo=booleans        box minus cylinder, OCCT gate PASS
  ?demo=booleans&op=    union, cut, and intersect each PASS
  ?pair=overlap         select two bodies with the 4 key, then Union, Cut, Intersect.
                        Union undo restores both boxes. ?pair=disjoint Intersect
                        keeps both and does not push undo. Disjoint Cut follows
                        the same keep-both rule when the gate rejects it.
  /?fixture=closed_box  plain 4 key selects the whole body when the viewport is focused
  Create Box/Cylinder/Disc is one undo/redo step; digits do not change selection
                        unless the viewport is focused, and inputs ignore hotkeys
  portrait 390x844      Create menu (Box, Cylinder, Disc, Hole, Sketch; no primitive
                        buttons left outside it), then box, cylinder, and disc;
                        #calloutLayer stays hidden on phone while editing a basic shape
                        (box, cylinder, disc) while Properties Size fields (boxSx/boxSy/boxSz,
                        cylD/cylH, discD/discT) stay present and editable and update after
                        the sheet edit; desktop callouts stay visible and off Home/Export/units;
                        uncovered viewport >= 70% with the dimension panel collapsed
                        and >= 50% with it open; the panel stays shut until a tap;
                        build stamp is visible and matches the script ?v= param;
                        bottom sheet does not cover Home; move, rotate, and resize
                        a box with taps and typed values;
                        no page-level horizontal scroll; visible buttons and the status
                        line stay inside the width; the sheet and toolbar do not scroll
                        sideways unless marked data-hscroll; Part 1 is fully visible,
                        min-width 96px;
                        before those primitive taps, sketch on the default cube:
                        Finish Sketch, Tools-sheet Rectangle and Circle, L×W / Ø /
                        Blind inputs, and Extrude Confirm are at least 44 px; the
                        sketch sheet does not cover the status bar
                        or view bar; the top face becomes the plane with no V/E/F
                        highlight; the origin-plane picker stays off; Extrude on
                        that face opens on Join, and New / Join / Cut are each at
                        least 44 px; a 10×10 top-face rect Blind 10 mm Join leaves
                        one body at 9000 mm³; the same profile overridden to New
                        leaves two bodies; the page is restored to the 20 mm box
  portrait origin plane empty doc (bodies.length === 0, not projectBlank):
                        Top / Front / Right chips are at least 44 px and do not
                        cover the status bar or view bar; Top is
                        XY with +Z outward; rectangle 10×10 and circle Ø10 each
                        open Extrude on New and Blind 10 mm add a new body that
                        passes OCCT and mm; Join or Cut with no body, or without
                        exactly one Item-selected body, rejects; one Item-selected
                        20 mm box Cut by that 10×10 prism is 7000 mm³; a Ø40
                        circle Blind 30 mm that contains the box is rejected and
                        the 8000 mm³ box stays
  portrait holes        three countersunk holes on a plate; volumes logged; same overflow
                        and coverage checks
  measure tool          default 20 mm cube: one edge polyline ~20 mm, volume ~8000 mm³,
                        opposite-corner distance ~sqrt(3)*20; Measure control >= 44 px
  portrait nav cube     88 px cube, 6 face and 8 corner taps, each face within 1 degree,
                        clear-view fraction held; prints NAVCUBE_DONE
  portrait inspector    closed right panel is inert, not rendered, not tappable, and not focusable
  /tests/fixtures/lbracket.json, /fixtures/lbracket.json,
  /tests/fixtures/blink.json, and /fixtures/blink.json return 404

Exit 77 (CTest skip) only when the browser or libcascade is missing and
CI is not set. In CI those gaps fail the run.
"""
from __future__ import annotations

import argparse
import base64
import importlib.util
import json
import math
import os
import shutil
import socket
import struct
import subprocess
import sys
import threading
import time
import urllib.error
import urllib.request
import zlib
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
WORK = ROOT / "builds" / "deploy-smoke"
PAGE_TIMEOUT_S = 180
SKIP = 77

HOOK = """
(() => {
  if (window.__cadcamSmoke) return;
  window.__cadcamSmoke = { errors: [], rejects: [] };
  window.addEventListener('error', (ev) => {
    const msg = ev && ev.message ? String(ev.message) : 'error';
    window.__cadcamSmoke.errors.push(msg);
  });
  window.addEventListener('unhandledrejection', (ev) => {
    const reason = ev && ev.reason;
    const msg = reason && reason.message ? String(reason.message) : String(reason);
    window.__cadcamSmoke.rejects.push(msg);
  });
})();
"""

PROBE = (
    "JSON.stringify({"
    "state: window.__cadcamExportState || null,"
    "smoke: window.__cadcamSmoke || null"
    "})"
)


def in_ci() -> bool:
    return os.environ.get("CI", "").strip().lower() in {"1", "true", "yes"}


def load_assembler():
    path = ROOT / "web" / "assemble_site.py"
    spec = importlib.util.spec_from_file_location("assemble_site", path)
    if spec is None or spec.loader is None:
        raise SystemExit(f"cannot load {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def find_browser() -> str | None:
    env = os.environ.get("CADCAM_BROWSER", "").strip()
    if env:
        candidate = Path(env)
        if candidate.is_file():
            return str(candidate)
        found = shutil.which(env)
        return found
    if sys.platform == "win32":
        candidates = [
            r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
            r"C:\Program Files\Microsoft\Edge\Application\msedge.exe",
            r"C:\Program Files\Google\Chrome\Application\chrome.exe",
            r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
        ]
        for candidate in candidates:
            if Path(candidate).is_file():
                return candidate
        for name in ("msedge", "chrome", "chromium"):
            found = shutil.which(name)
            if found:
                return found
        return None
    for name in (
        "google-chrome",
        "google-chrome-stable",
        "chromium",
        "chromium-browser",
        "microsoft-edge",
        "microsoft-edge-stable",
    ):
        found = shutil.which(name)
        if found:
            return found
    return None


def libcascade_gaps() -> list[str]:
    needed = [
        ROOT / "web" / "dist" / "init.single.js",
        ROOT / "web" / "dist" / "opencascade_single.js",
        ROOT / "web" / "dist" / "opencascade_single.wasm",
        ROOT / "web" / "dist" / "cadcam_rust_gate.js",
        ROOT / "web" / "dist" / "cadcam_rust_gate_bg.wasm",
    ]
    missing = [str(path.relative_to(ROOT)) for path in needed if not path.is_file()]
    if not missing:
        return []
    return [
        "libcascade is not staged ("
        + ", ".join(missing)
        + "). Run: python web/fetch-libcascade.py"
    ]


def skip_or_fail(reasons: list[str]) -> int:
    text = "; ".join(reasons)
    if in_ci():
        print(f"FAIL deploy_smoke: {text}", flush=True)
        print("CI must not skip the deploy smoke test.", flush=True)
        return 1
    print(f"SKIP deploy_smoke: {text}", flush=True)
    return SKIP


def free_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.bind(("127.0.0.1", 0))
        return int(sock.getsockname()[1])


class SiteHandler(SimpleHTTPRequestHandler):
    extensions_map = {
        **SimpleHTTPRequestHandler.extensions_map,
        ".js": "text/javascript",
        ".mjs": "text/javascript",
        ".wasm": "application/wasm",
        ".html": "text/html; charset=utf-8",
    }

    def end_headers(self) -> None:
        self.send_header("Cache-Control", "no-store")
        super().end_headers()

    def log_message(self, fmt: str, *args: Any) -> None:
        return


class WsClient:
    """Minimal WebSocket client for one CDP target. No extensions."""

    def __init__(self, url: str) -> None:
        if not url.startswith("ws://"):
            raise SystemExit(f"unsupported debugger url {url}")
        rest = url[len("ws://") :]
        hostport, _, path = rest.partition("/")
        _host, _, port_text = hostport.partition(":")
        self.host = "127.0.0.1"
        self.port = int(port_text or "80")
        self.path = "/" + path
        self.sock = socket.create_connection((self.host, self.port), timeout=10)
        self.sock.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
        # No Origin header. Current Edge/Chromium reject the debugger
        # socket with 403 unless that origin is listed in --remote-allow-origins.
        # A non-browser client omits Origin. Host is the address we connected to.
        key = base64.b64encode(os.urandom(16)).decode("ascii")
        request = (
            f"GET {self.path} HTTP/1.1\r\n"
            f"Host: {self.host}:{self.port}\r\n"
            "Upgrade: websocket\r\n"
            "Connection: Upgrade\r\n"
            f"Sec-WebSocket-Key: {key}\r\n"
            "Sec-WebSocket-Version: 13\r\n"
            "\r\n"
        )
        self.sock.sendall(request.encode("ascii"))
        buffer = b""
        while b"\r\n\r\n" not in buffer:
            chunk = self.sock.recv(4096)
            if not chunk:
                raise SystemExit("CDP websocket closed during handshake")
            buffer += chunk
        head, self.buffer = buffer.split(b"\r\n\r\n", 1)
        status = head.split(b"\r\n", 1)[0]
        if b" 101 " not in status:
            raise SystemExit(f"CDP websocket handshake failed: {status.decode('ascii', 'replace')}")

    def send_text(self, text: str) -> None:
        payload = text.encode("utf-8")
        mask = os.urandom(4)
        header = bytearray([0x81])
        length = len(payload)
        if length < 126:
            header.append(0x80 | length)
        elif length < 65536:
            header.append(0x80 | 126)
            header += struct.pack("!H", length)
        else:
            header.append(0x80 | 127)
            header += struct.pack("!Q", length)
        header += mask
        masked = bytes(byte ^ mask[index % 4] for index, byte in enumerate(payload))
        self.sock.sendall(bytes(header) + masked)

    def _read_exact(self, size: int, deadline: float) -> bytes | None:
        while len(self.buffer) < size:
            remaining = deadline - time.time()
            if remaining <= 0:
                return None
            self.sock.settimeout(remaining)
            try:
                chunk = self.sock.recv(65536)
            except (TimeoutError, socket.timeout):
                return None
            if not chunk:
                raise SystemExit("CDP websocket closed")
            self.buffer += chunk
        data = self.buffer[:size]
        self.buffer = self.buffer[size:]
        return data

    def recv_text(self, timeout: float) -> str | None:
        deadline = time.time() + timeout
        fragments: list[bytes] = []
        while True:
            # Once a frame has started, finish it. A short poll timeout must
            # not split a frame across two reads or the next header is garbage.
            frame_deadline = deadline if not fragments else max(deadline, time.time() + 5)
            header = self._read_exact(2, frame_deadline)
            if header is None:
                if fragments:
                    raise SystemExit("truncated CDP frame")
                return None
            first, second = header[0], header[1]
            opcode = first & 0x0F
            masked = (second & 0x80) != 0
            length = second & 0x7F
            if length == 126:
                extra = self._read_exact(2, frame_deadline)
                if extra is None:
                    raise SystemExit("truncated CDP frame")
                length = struct.unpack("!H", extra)[0]
            elif length == 127:
                extra = self._read_exact(8, frame_deadline)
                if extra is None:
                    raise SystemExit("truncated CDP frame")
                length = struct.unpack("!Q", extra)[0]
            mask = b""
            if masked:
                got = self._read_exact(4, frame_deadline)
                if got is None:
                    raise SystemExit("truncated CDP frame")
                mask = got
            payload = self._read_exact(length, frame_deadline)
            if payload is None:
                raise SystemExit("truncated CDP frame")
            if masked:
                payload = bytes(byte ^ mask[index % 4] for index, byte in enumerate(payload))
            if opcode == 0x9:
                self._send_control(0xA, payload)
                continue
            if opcode == 0x8:
                raise SystemExit("CDP websocket closed by the browser")
            if opcode == 0xA:
                continue
            fragments.append(payload)
            if first & 0x80:
                return b"".join(fragments).decode("utf-8", "replace")

    def _send_control(self, opcode: int, payload: bytes) -> None:
        mask = os.urandom(4)
        header = bytearray([0x80 | opcode, 0x80 | len(payload)])
        header += mask
        masked = bytes(byte ^ mask[index % 4] for index, byte in enumerate(payload))
        self.sock.sendall(bytes(header) + masked)

    def close(self) -> None:
        try:
            self.sock.close()
        except OSError:
            pass


class Cdp:
    def __init__(self, ws_url: str) -> None:
        self.ws = WsClient(ws_url)
        self.next_id = 0
        self.events: list[dict[str, Any]] = []
        self.urls: dict[str, str] = {}

    def call(self, method: str, params: dict[str, Any] | None = None, timeout: float = 30) -> dict[str, Any]:
        self.next_id += 1
        message_id = self.next_id
        self.ws.send_text(json.dumps({"id": message_id, "method": method, "params": params or {}}))
        deadline = time.time() + timeout
        while time.time() < deadline:
            raw = self.ws.recv_text(min(1.0, max(0.05, deadline - time.time())))
            if raw is None:
                continue
            message = json.loads(raw)
            if message.get("id") == message_id:
                if "error" in message:
                    raise RuntimeError(f"{method} {message['error']}")
                return message.get("result") or {}
            if "method" in message:
                self.events.append(message)
        raise TimeoutError(method)

    def drain(self, wait: float) -> None:
        deadline = time.time() + wait
        while time.time() < deadline:
            raw = self.ws.recv_text(max(0.05, deadline - time.time()))
            if raw is None:
                continue
            message = json.loads(raw)
            if "method" in message:
                self.events.append(message)

    def close(self) -> None:
        self.ws.close()


def console_text(params: dict[str, Any]) -> str:
    parts: list[str] = []
    for arg in params.get("args") or []:
        if "value" in arg:
            parts.append(str(arg["value"]))
        elif arg.get("description"):
            parts.append(str(arg["description"]))
        else:
            parts.append(json.dumps(arg)[:240])
    return " ".join(parts)[:800]


def site_problems(events: list[dict[str, Any]], origin: str, urls: dict[str, str]) -> list[str]:
    problems: list[str] = []
    seen: set[str] = set()

    def add(text: str) -> None:
        if text not in seen:
            seen.add(text)
            problems.append(text)

    for event in events:
        method = event.get("method")
        params = event.get("params") or {}
        if method == "Network.requestWillBeSent":
            request = params.get("request") or {}
            request_id = str(params.get("requestId") or "")
            url = str(request.get("url") or "")
            if request_id:
                urls[request_id] = url
        elif method == "Network.responseReceived":
            response = params.get("response") or {}
            url = str(response.get("url") or "")
            if not url.startswith(origin):
                continue
            status = int(response.get("status") or 0)
            if response.get("fromDiskCache") or response.get("fromPrefetchCache"):
                add(f"cached response {url}")
            if status < 200 or status >= 300:
                add(f"HTTP {status} {url}")
        elif method == "Network.requestServedFromCache":
            url = urls.get(str(params.get("requestId") or ""), "")
            if url.startswith(origin):
                add(f"cached response {url}")
        elif method == "Network.loadingFailed":
            if params.get("canceled"):
                continue
            error = str(params.get("errorText") or "")
            if "ERR_ABORTED" in error:
                continue
            url = urls.get(str(params.get("requestId") or ""), "")
            if url.startswith(origin):
                add(f"load failed {error} {url}")
        elif method == "Runtime.consoleAPICalled" and params.get("type") in {"error", "assert"}:
            add(f"console.{params.get('type')}: {console_text(params)}")
        elif method == "Runtime.exceptionThrown":
            details = params.get("exceptionDetails") or {}
            exception = details.get("exception") or {}
            text = details.get("text") or exception.get("description") or "exception"
            add(f"exception: {text}")
        elif method == "Log.entryAdded":
            entry = params.get("entry") or {}
            if entry.get("level") == "error":
                url = str(entry.get("url") or "")
                if url and not url.startswith(origin):
                    continue
                add(f"console error: {entry.get('text')}")
    return problems


def eval_state(cdp: Cdp) -> dict[str, Any] | None:
    try:
        result = cdp.call(
            "Runtime.evaluate",
            {"expression": PROBE, "returnByValue": True},
            timeout=15,
        )
    except (RuntimeError, TimeoutError):
        return None
    remote = result.get("result") or {}
    value = remote.get("value")
    if not isinstance(value, str) or not value.startswith("{"):
        return None
    try:
        return json.loads(value)
    except json.JSONDecodeError:
        return None


def smoke_notes(payload: dict[str, Any] | None) -> list[str]:
    if not payload:
        return []
    smoke = payload.get("smoke") or {}
    notes: list[str] = []
    for item in smoke.get("errors") or []:
        notes.append(f"page error: {item}")
    for item in smoke.get("rejects") or []:
        notes.append(f"unhandled rejection: {item}")
    return notes


CASES = (
    {
        "name": "closed_box",
        "query": "/?fixture=closed_box&tab=export",
        "expect": "occtReady and gate PASS, Export enabled",
    },
    {
        "name": "open_box",
        "query": "/?fixture=open_box&tab=export",
        "expect": "occtReady and gate FAIL, units pass, Export enabled",
    },
    {
        "name": "flipped_box",
        "query": "/?fixture=flipped_box&tab=export",
        "expect": "occtReady, inside-out negative volume blocked by C++ and Rust",
    },
    {
        "name": "box_face",
        "query": "/?primitive=box&select=face",
        "expect": "occtReady, face selected",
    },
    {
        "name": "lbracket",
        "query": "/?demo=lbracket",
        "expect": "occtReady, gate PASS on the final bracket",
    },
    {
        "name": "booleans",
        "query": "/?demo=booleans",
        "expect": "box minus cylinder, gate PASS",
        "op": "cut",
    },
    {
        "name": "booleans_union",
        "query": "/?demo=booleans&op=union",
        "expect": "box union cylinder, gate PASS",
        "op": "union",
    },
    {
        "name": "booleans_intersect",
        "query": "/?demo=booleans&op=intersect",
        "expect": "box intersect cylinder, gate PASS",
        "op": "intersect",
    },
    {
        "name": "hotkey4",
        "query": "/?fixture=closed_box",
        "expect": "plain 4 selects the whole body",
        "hotkey": True,
    },
)


def check_case(name: str, state: dict[str, Any], expected_op: str = "") -> list[str]:
    problems: list[str] = []
    if state.get("dimSheetOpen") is True:
        problems.append(f"{name}: dimension panel opened without a tap")
    if state.get("occtReady") is not True:
        problems.append(f"{name}: occtReady is not true")
    if name == "closed_box":
        if state.get("fixture") != "closed_box":
            problems.append(f"{name}: fixture {state.get('fixture')!r}")
        if state.get("occtGate") is not True or state.get("gateOcct") != "PASS":
            problems.append(f"{name}: gate is not PASS ({state.get('gateOcct')!r})")
        if state.get("exportAllowed") is not True or state.get("exportDisabled") is not False:
            problems.append(f"{name}: Export is not enabled")
    elif name == "open_box":
        if state.get("fixture") != "open_box":
            problems.append(f"{name}: fixture {state.get('fixture')!r}")
        if state.get("occtGate") is not False or state.get("gateOcct") != "FAIL":
            problems.append(f"{name}: gate is not FAIL ({state.get('gateOcct')!r})")
        if state.get("unitsPass") is not True:
            problems.append(f"{name}: units are not locked")
        if state.get("exportAllowed") is not True or state.get("exportDisabled") is not False:
            problems.append(f"{name}: Export is not enabled")
    elif name == "box_face":
        if state.get("occtReady") is not True:
            problems.append(f"{name}: occtReady is not true")
        if state.get("selectionMode") != "face" or int(state.get("selectionCount") or 0) < 1:
            problems.append(
                f"{name}: expected one selected face, got mode {state.get('selectionMode')!r} "
                f"count {state.get('selectionCount')!r}"
            )
        if state.get("gizmoVisible") is not False:
            problems.append(
                f"{name}: expected gizmoVisible false on face selection, got {state.get('gizmoVisible')!r}"
            )
        if state.get("occtGate") is not True or state.get("gateOcct") != "PASS":
            problems.append(f"{name}: gate is not PASS ({state.get('gateOcct')!r})")
    elif name == "lbracket":
        if state.get("demo") != "lbracket":
            problems.append(f"{name}: demo {state.get('demo')!r}")
        if state.get("occtGate") is not True or state.get("gateOcct") != "PASS":
            problems.append(f"{name}: gate is not PASS ({state.get('gateOcct')!r})")
        if state.get("unitsPass") is not True:
            problems.append(f"{name}: units are not locked")
        if state.get("lastError"):
            problems.append(f"{name}: lastError {state.get('lastError')!r}")
        steps = [item.get("step") for item in (state.get("opLog") or []) if item.get("pass")]
        if steps != ["fuse", "fillet", "chamfer"]:
            problems.append(f"{name}: op log {steps!r}")
    elif name.startswith("booleans"):
        if state.get("demo") != "booleans":
            problems.append(f"{name}: demo {state.get('demo')!r}")
        if state.get("occtGate") is not True or state.get("gateOcct") != "PASS":
            problems.append(f"{name}: gate is not PASS ({state.get('gateOcct')!r})")
        if state.get("unitsPass") is not True:
            problems.append(f"{name}: units are not locked")
        if state.get("exportAllowed") is not True:
            problems.append(f"{name}: Export is not enabled")
        if state.get("lastError"):
            problems.append(f"{name}: lastError {state.get('lastError')!r}")
        if state.get("booleanOp") != expected_op:
            problems.append(f"{name}: booleanOp {state.get('booleanOp')!r}, want {expected_op!r}")
    elif name == "flipped_box":
        if state.get("fixture") != "flipped_box":
            problems.append(f"{name}: fixture {state.get('fixture')!r}")
        if state.get("exportAllowed") is not False or state.get("exportDisabled") is not True:
            problems.append(f"{name}: inside-out mesh did not block Export ({state.get('exportAllowed')!r})")
        inside_out_msg = "FAIL: mesh is inside-out (negative volume)."
        if state.get("blockReason") != inside_out_msg:
            problems.append(f"{name}: C++ blockReason {state.get('blockReason')!r}")
    rust = state.get("rustGate") if isinstance(state.get("rustGate"), dict) else {}
    if name in ("closed_box", "open_box"):
        if (
            rust.get("ready") is not True
            or rust.get("exportAllowed") is not True
            or rust.get("unitsPass") is not True
            or rust.get("meshPass") is not True
            or rust.get("matchesCpp") is not True
            or str(rust.get("blockReason") or "") != ""
            or not str(rust.get("statusText") or "").startswith("RustGate: PASS")
        ):
            problems.append(f"{name}: rustGate {rust!r}")
        try:
            rust_vol = float(rust.get("volumeMm3"))
            cpp_vol = float(state.get("cppVolumeMm3"))
        except (TypeError, ValueError):
            rust_vol = float("nan")
            cpp_vol = float("nan")
        if not math.isfinite(rust_vol) or not math.isfinite(cpp_vol) or abs(rust_vol - cpp_vol) > 1e-9:
            problems.append(f"{name}: volume mismatch rust={rust.get('volumeMm3')!r} cpp={state.get('cppVolumeMm3')!r}")
        if name == "closed_box" and abs(rust_vol - 1.0) > 1e-9:
            problems.append(f"{name}: expected 1.0 mm3 volume, got {rust_vol!r}")
    elif name == "flipped_box":
        inside_out_msg = "FAIL: mesh is inside-out (negative volume)."
        if (
            rust.get("ready") is not True
            or rust.get("exportAllowed") is not False
            or rust.get("unitsPass") is not True
            or rust.get("meshPass") is not False
            or rust.get("matchesCpp") is not True
            or rust.get("blockReason") != inside_out_msg
            or not str(rust.get("statusText") or "").startswith("RustGate: FAIL")
        ):
            problems.append(f"{name}: rustGate {rust!r}")
        try:
            rust_vol = float(rust.get("volumeMm3"))
            cpp_vol = float(state.get("cppVolumeMm3"))
        except (TypeError, ValueError):
            rust_vol = float("nan")
            cpp_vol = float("nan")
        if not math.isfinite(rust_vol) or not math.isfinite(cpp_vol) or abs(rust_vol - cpp_vol) > 1e-9 or abs(rust_vol + 1.0) > 1e-9:
            problems.append(f"{name}: inside-out volume rust={rust.get('volumeMm3')!r} cpp={state.get('cppVolumeMm3')!r}")
    return problems


def rust_gate_probe_problems(cdp: Cdp, case_name: str) -> list[str]:
    expr = (
        "(function(){"
        "var rg=window.__cadcamRustGate||null;"
        "var st=window.__cadcamExportState||null;"
        "var dom=document.getElementById('statusRustGate');"
        "var badge=document.getElementById('gateRust');"
        "var empty=rg&&typeof rg.eval==='function'?rg.eval({vertices:[],triangles:[]}):null;"
        "var unitsBad=rg&&typeof rg.eval==='function'?rg.eval({vertices:[],triangles:[],storage:'inch'}):null;"
        "var d254=rg&&typeof rg.toDisplay==='function'?rg.toDisplay(25.4,true):null;"
        "var m254=rg&&typeof rg.toMillimeters==='function'?rg.toMillimeters(1.0,true):null;"
        "var rt1=rg&&typeof rg.toDisplay==='function'&&typeof rg.toMillimeters==='function'?rg.toMillimeters(rg.toDisplay(1.0,true),true):null;"
        "return JSON.stringify({"
        "rg:rg?{ready:rg.ready,exportAllowed:rg.exportAllowed,blockReason:rg.blockReason,volumeMm3:rg.volumeMm3,unitsPass:rg.unitsPass,meshPass:rg.meshPass,matchesCpp:rg.matchesCpp}:null,"
        "domText:dom?String(dom.textContent||''):'',"
        "badgeText:badge?String(badge.textContent||''):'',"
        "empty:empty,"
        "unitsBad:unitsBad,"
        "d254:d254,m254:m254,rt1:rt1,"
        "liveAllowedAfter:st?st.exportAllowed:null"
        "});"
        "})()"
    )
    raw, err = eval_expr(cdp, expr)
    if err or not isinstance(raw, str) or not raw.startswith("{"):
        return [f"{case_name}: rust_gate_probe {raw or err}"]
    try:
        data = json.loads(raw)
    except json.JSONDecodeError:
        return [f"{case_name}: rust_gate_probe json {raw}"]
    problems: list[str] = []
    rg = data.get("rg") if isinstance(data.get("rg"), dict) else {}
    dom_text = str(data.get("domText") or "")
    badge_text = str(data.get("badgeText") or "")
    if case_name == "closed_box":
        if (
            rg.get("ready") is not True
            or rg.get("exportAllowed") is not True
            or rg.get("matchesCpp") is not True
            or badge_text != "PASS"
            or not dom_text.startswith("RustGate: PASS")
            or data.get("liveAllowedAfter") is not True
        ):
            problems.append(f"{case_name}: window.__cadcamRustGate/DOM {data!r}")
    elif case_name == "flipped_box":
        inside_out = "FAIL: mesh is inside-out (negative volume)."
        if (
            rg.get("ready") is not True
            or rg.get("exportAllowed") is not False
            or rg.get("blockReason") != inside_out
            or rg.get("matchesCpp") is not True
            or badge_text != "FAIL"
            or not dom_text.startswith("RustGate: FAIL")
            or inside_out not in dom_text
            or data.get("liveAllowedAfter") is not False
        ):
            problems.append(f"{case_name}: window.__cadcamRustGate/DOM {data!r}")
    empty = data.get("empty") if isinstance(data.get("empty"), dict) else {}
    if (
        empty.get("exportAllowed") is not False
        or empty.get("unitsPass") is not True
        or empty.get("meshPass") is not False
        or empty.get("blockReason") != "FAIL: mesh has no triangles."
        or empty.get("matchesCpp") is not True
    ):
        problems.append(f"{case_name}: empty eval {empty!r}")
    units_bad = data.get("unitsBad") if isinstance(data.get("unitsBad"), dict) else {}
    if (
        units_bad.get("exportAllowed") is not False
        or units_bad.get("unitsPass") is not False
        or units_bad.get("blockReason") != "FAIL: export unit is not millimeter."
    ):
        problems.append(f"{case_name}: unitsBad eval {units_bad!r}")
    if data.get("d254") != 1.0 or data.get("m254") != 25.4:
        problems.append(f"{case_name}: unit conversion 25.4 -> {data.get('d254')!r}, 1.0 -> {data.get('m254')!r}")
    try:
        rt1 = float(data.get("rt1"))
    except (TypeError, ValueError):
        rt1 = float("nan")
    if not math.isfinite(rt1) or abs(rt1 - 1.0) > 2.3e-16:
        problems.append(f"{case_name}: 1 mm round-trip {data.get('rt1')!r}")
    return problems


def wait_for_case(cdp: Cdp, origin: str, url: str, timeout: float) -> tuple[dict[str, Any] | None, list[str]]:
    cdp.events.clear()
    cdp.urls.clear()
    cdp.call("Page.navigate", {"url": url})
    deadline = time.time() + timeout
    last: dict[str, Any] | None = None
    while time.time() < deadline:
        cdp.drain(0.5)
        problems = site_problems(cdp.events, origin, cdp.urls)
        payload = eval_state(cdp)
        problems.extend(smoke_notes(payload))
        if problems:
            time.sleep(0.8)
            cdp.drain(0.4)
            problems = site_problems(cdp.events, origin, cdp.urls)
            if payload:
                latest = eval_state(cdp)
                if latest:
                    payload = latest
            problems.extend(smoke_notes(payload))
            return (payload or {}).get("state") if payload else last, problems
        state = (payload or {}).get("state") if payload else None
        if isinstance(state, dict):
            last = state
            if state.get("occtReady") is True:
                cdp.drain(1.0)
                problems = site_problems(cdp.events, origin, cdp.urls)
                latest = eval_state(cdp)
                if latest and isinstance(latest.get("state"), dict):
                    state = latest["state"]
                problems.extend(smoke_notes(latest))
                return state, problems
    return last, [f"timed out waiting for occtReady at {url}", json.dumps(last)]


def browser_args(browser: str, port: int, profile: Path) -> list[str]:
    args = [
        browser,
        "--headless=new",
        f"--remote-debugging-port={port}",
        "--remote-debugging-address=127.0.0.1",
        "--remote-allow-origins=*",
        f"--user-data-dir={profile}",
        "--no-first-run",
        "--no-default-browser-check",
        "--disable-extensions",
        "--disable-background-networking",
        "--disable-sync",
        "--disable-component-update",
        "--disable-features=Translate,MediaRouter,OptimizationHints",
        "about:blank",
    ]
    if sys.platform == "win32":
        args.insert(2, "--disable-gpu")
    else:
        args[2:2] = [
            "--no-sandbox",
            "--disable-dev-shm-usage",
            "--use-gl=angle",
            "--use-angle=swiftshader",
            "--enable-unsafe-swiftshader",
        ]
    return args


def stop_browser(proc: subprocess.Popen[Any] | None, profile: Path) -> None:
    if proc is not None and proc.poll() is None:
        if sys.platform == "win32":
            subprocess.run(
                ["taskkill", "/F", "/T", "/PID", str(proc.pid)],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                check=False,
            )
        else:
            try:
                os.killpg(proc.pid, 15)
            except OSError:
                proc.terminate()
    if sys.platform == "win32":
        needle = str(profile).replace("'", "''")
        command = (
            "Get-CimInstance Win32_Process | "
            f"Where-Object {{ $_.CommandLine -and $_.CommandLine.Contains('{needle}') }} | "
            "ForEach-Object { Stop-Process -Id $_.ProcessId -Force -ErrorAction SilentlyContinue }"
        )
        subprocess.run(
            ["powershell", "-NoProfile", "-Command", command],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            check=False,
        )
    elif proc is not None:
        try:
            os.killpg(proc.pid, 9)
        except OSError:
            pass


def wait_for_page(port: int) -> str:
    deadline = time.time() + 30
    url = f"http://127.0.0.1:{port}/json/list"
    while time.time() < deadline:
        try:
            with urllib.request.urlopen(url, timeout=1) as response:
                pages = json.loads(response.read().decode("utf-8"))
        except (urllib.error.URLError, TimeoutError, json.JSONDecodeError, OSError):
            time.sleep(0.2)
            continue
        for page in pages:
            if page.get("type") == "page" and page.get("webSocketDebuggerUrl"):
                return str(page["webSocketDebuggerUrl"])
        time.sleep(0.2)
    raise SystemExit("CDP did not expose a page target")


def press_digit(cdp: Cdp, digit: str) -> None:
    """Press a plain digit key. Alt is not held, so 4 stays Item select."""
    cdp.call(
        "Runtime.evaluate",
        {
            "expression": (
                "(function(){"
                "var el=document.activeElement;"
                "if(el&&el.blur) el.blur();"
                "var vp=document.getElementById('viewport');"
                "if(vp&&vp.focus) vp.focus();"
                "return document.activeElement?document.activeElement.tagName:'';"
                "})()"
            ),
            "returnByValue": True,
        },
    )
    code = ord(digit)
    for kind in ("keyDown", "keyUp"):
        cdp.call(
            "Input.dispatchKeyEvent",
            {
                "type": kind,
                "key": digit,
                "code": "Digit" + digit,
                "windowsVirtualKeyCode": code,
                "nativeVirtualKeyCode": code,
                "text": digit if kind == "keyDown" else "",
                "modifiers": 0,
            },
        )


def press_plain_4(cdp: Cdp) -> None:
    """Press the plain 4 key. Alt is not held, so this is Item select, not Export."""
    press_digit(cdp, "4")



PORTRAIT = (
    {"kind": "box", "field": "boxSx", "value": "30", "key": "sx", "fresh": 20.0, "want": 30.0},
    {"kind": "cylinder", "field": "cylH", "value": "24", "key": "height", "fresh": 20.0, "want": 24.0},
    {"kind": "disc", "field": "discD", "value": "22", "key": "diameter", "fresh": 18.0, "want": 22.0},
)


def eval_expr(cdp: Cdp, expression: str, timeout: float = 30) -> tuple[Any, str]:
    result = cdp.call(
        "Runtime.evaluate",
        {"expression": expression, "returnByValue": True},
        timeout=timeout,
    )
    if result.get("exceptionDetails"):
        detail = result.get("exceptionDetails") or {}
        return None, str(detail.get("text") or detail.get("exception") or "evaluate failed")
    remote = result.get("result") or {}
    return remote.get("value"), ""


def set_portrait(cdp: Cdp) -> None:
    cdp.call(
        "Emulation.setDeviceMetricsOverride",
        {
            "width": 390,
            "height": 844,
            "deviceScaleFactor": 1,
            "mobile": True,
            "screenOrientation": {"type": "portraitPrimary", "angle": 0},
        },
    )
    cdp.call("Emulation.setTouchEmulationEnabled", {"enabled": True, "maxTouchPoints": 1})


def touch_tap(cdp: Cdp, x: float, y: float) -> None:
    point = {"x": float(x), "y": float(y), "radiusX": 1.0, "radiusY": 1.0, "force": 1.0, "id": 0}
    cdp.call("Input.dispatchTouchEvent", {"type": "touchStart", "touchPoints": [point]})
    time.sleep(0.05)
    cdp.call("Input.dispatchTouchEvent", {"type": "touchEnd", "touchPoints": []})


def create_point_expr(selector: str) -> str:
    return (
        "(function(){"
        "var menu=document.getElementById('createMenu');"
        "if(!menu) return 'missing menu';"
        "if(menu.hidden){"
        "var openers=document.querySelectorAll('[data-action=\"createMenu\"]');"
        "var opener=null;"
        "for(var i=0;i<openers.length;i++){"
        "if(openers[i].closest&&openers[i].closest('[hidden]')) continue;"
        "var st=getComputedStyle(openers[i]);"
        "var r=openers[i].getBoundingClientRect();"
        "if(st.display==='none'||st.visibility==='hidden'||r.width<1||r.height<1) continue;"
        "opener=openers[i];break;"
        "}"
        "if(!opener){"
        "var sheet=document.getElementById('toolsSheet');"
        "if(!sheet||sheet.hidden){"
        "var tm=document.querySelector('[data-action=\"toolsMenu\"]');"
        "if(tm)tm.click();"
        "}"
        "var sc=document.querySelector('#toolsSheet [data-action=\"createMenu\"]');"
        "if(sc&&sheet&&!sheet.hidden) opener=sc;"
        "}"
        "if(!opener) return 'missing create';"
        "opener.click();"
        "}"
        f"var b=menu.querySelector('{selector}');"
        "if(!b) return 'missing';"
        "var st=getComputedStyle(b);"
        "if(st.display==='none'||st.visibility==='hidden') return 'hidden';"
        "var r=b.getBoundingClientRect();"
        "if(r.width<1||r.height<1) return 'empty';"
        "return JSON.stringify({x:r.left+r.width/2,y:r.top+r.height/2,w:r.width,h:r.height});"
        "})()"
    )


def toolbar_point_expr(kind: str) -> str:
    return create_point_expr(f'[data-kind="{kind}"]')


TARGET_EXPR = (
    "(function(){"
    "function shown(el){"
    "if(!el||el.closest('[hidden]')) return null;"
    "var st=getComputedStyle(el);"
    "if(st.display==='none'||st.visibility==='hidden') return null;"
    "var r=el.getBoundingClientRect();"
    "if(r.width<1||r.height<1) return null;"
    "var label=(el.id||el.getAttribute('aria-label')||el.textContent||'').replace(/\\s+/g,' ').trim();"
    "return {w:r.width,h:r.height,label:label};"
    "}"
    "var nodes=document.querySelectorAll('#touchToolbar button, #dimPanel button, #dimPanel input, #gizmoSwitch button');"
    "var bad=[];"
    "var n=0;"
    "for(var i=0;i<nodes.length;i++){"
    "var box=shown(nodes[i]);"
    "if(!box) continue;"
    "n++;"
    "if(box.w<44||box.h<44) bad.push(box.label+' '+box.w.toFixed(1)+'x'+box.h.toFixed(1));"
    "}"
    "return JSON.stringify({n:n,bad:bad});"
    "})()"
)


def point_expr(selector: str) -> str:
    return (
        "(function(){"
        f"var b=document.querySelector('{selector}');"
        "if(!b) return 'missing';"
        "var st=getComputedStyle(b);"
        "if(st.display==='none'||st.visibility==='hidden') return 'hidden';"
        "var r=b.getBoundingClientRect();"
        "if(r.width<1||r.height<1) return 'empty';"
        "return JSON.stringify({x:r.left+r.width/2,y:r.top+r.height/2,w:r.width,h:r.height});"
        "})()"
    )


def resize_call(cdp: Cdp, spec: dict[str, Any], timeout: float = 30) -> tuple[dict[str, Any] | None, str]:
    payload = json.dumps(spec)
    raw, err = eval_expr(
        cdp,
        "(function(){"
        f"if(typeof window.__cadcamResize!=='function') return 'missing';"
        f"return JSON.stringify(window.__cadcamResize({payload}));"
        "})()",
        timeout=timeout,
    )
    if err or not isinstance(raw, str) or not raw.startswith("{"):
        return None, err or str(raw)
    try:
        data = json.loads(raw)
    except json.JSONDecodeError:
        return None, raw
    if not isinstance(data, dict):
        return None, raw
    return data, ""


def _near(value: Any, want: float, tol: float = 0.01) -> bool:
    try:
        return abs(float(value) - want) < tol
    except (TypeError, ValueError):
        return False


UNLOCK_EXPR = (
    "(function(){"
    "var b=document.getElementById('lockProportions');"
    "if(!b) return 'missing';"
    "if(b.getAttribute('aria-pressed')==='true') b.click();"
    "return b.getAttribute('aria-pressed')==='false' ? 'off' : 'on';"
    "})()"
)


def edit_expr(field: str, value: str) -> str:
    return (
        "(function(){"
        f"var el=document.getElementById('{field}');"
        "if(!el) return 'missing';"
        "if(el.getAttribute('inputmode')!=='decimal') return 'inputmode='+String(el.getAttribute('inputmode'));"
        f"el.value='{value}';"
        "el.dispatchEvent(new Event('change',{bubbles:true}));"
        "return 'edited';"
        "})()"
    )


def param_is(state: dict[str, Any], key: str, want: float) -> bool:
    params = state.get("primitiveParams") or {}
    if not isinstance(params, dict) or key not in params:
        return False
    try:
        return abs(float(params.get(key)) - want) < 1e-6
    except (TypeError, ValueError):
        return False


def wait_portrait(
    cdp: Cdp,
    origin: str,
    kind: str,
    params: dict[str, float],
    timeout: float,
    extra: dict[str, Any] | None = None,
) -> tuple[dict[str, Any] | None, list[str]]:
    deadline = time.time() + timeout
    last: dict[str, Any] | None = None
    extra = extra or {}
    while time.time() < deadline:
        cdp.drain(0.3)
        problems = site_problems(cdp.events, origin, cdp.urls)
        payload = eval_state(cdp)
        problems.extend(smoke_notes(payload))
        if problems:
            return last, problems
        state = (payload or {}).get("state") if payload else None
        if isinstance(state, dict):
            last = state
            ready = (
                state.get("primitiveKind") == kind
                and state.get("occtGate") is True
                and state.get("gateOcct") == "PASS"
                and state.get("dimPanelOpen") is True
                and state.get("unitsPass") is True
                and not state.get("lastError")
                and int(state.get("bodyCount") or 0) == 1
                and all(param_is(state, key, want) for key, want in params.items())
            )
            for key, want in extra.items():
                if state.get(key) != want:
                    ready = False
                    break
            if ready:
                return state, []
        time.sleep(0.15)
    return last, [f"portrait {kind} timed out waiting for {params} {extra}", json.dumps(last)]


def tap_selector(cdp: Cdp, selector: str, label: str) -> list[str]:
    raw, err = eval_expr(cdp, point_expr(selector))
    if err or not isinstance(raw, str) or not raw.startswith("{"):
        return [f"{label} {raw or err}"]
    box = json.loads(raw)
    if float(box["w"]) < 44 or float(box["h"]) < 44:
        return [f"{label} {box['w']}x{box['h']}"]
    touch_tap(cdp, float(box["x"]), float(box["y"]))
    return []


def tap_point(cdp: Cdp, expression: str, label: str) -> list[str]:
    raw, err = eval_expr(cdp, expression)
    if err or not isinstance(raw, str) or not raw.startswith("{"):
        return [f"{label} {raw or err}"]
    box = json.loads(raw)
    if float(box["w"]) < 44 or float(box["h"]) < 44:
        return [f"{label} {box['w']}x{box['h']}"]
    touch_tap(cdp, float(box["x"]), float(box["y"]))
    return []


CREATE_MENU_EXPR = r"""
(function(){
  var problems = [];
  var menu = document.getElementById('createMenu');
  if (!menu) return JSON.stringify(['missing create menu']);
  var stray = document.querySelectorAll('[data-action="primitive"], [data-action="holeTool"]');
  for (var i = 0; i < stray.length; i++) {
    if (!menu.contains(stray[i])) {
      var strayLabel = stray[i].getAttribute('data-tool') || stray[i].getAttribute('data-kind') || 'button';
      problems.push('primitive outside menu ' + strayLabel);
    }
  }
  function visibleOpener() {
    var openers = document.querySelectorAll('[data-action="createMenu"]');
    for (var n = 0; n < openers.length; n++) {
      if (openers[n].closest && openers[n].closest('[hidden]')) continue;
      var st = getComputedStyle(openers[n]);
      var r = openers[n].getBoundingClientRect();
      if (st.display === 'none' || st.visibility === 'hidden' || r.width < 1 || r.height < 1) continue;
      return openers[n];
    }
    var sheet = document.getElementById('toolsSheet');
    if (!sheet || sheet.hidden) {
      var tm = document.querySelector('[data-action="toolsMenu"]');
      if (tm) tm.click();
    }
    var sc = document.querySelector('#toolsSheet [data-action="createMenu"]');
    if (sc && sheet && !sheet.hidden) return sc;
    return null;
  }
  var opener = visibleOpener();
  if (!opener) problems.push('missing create opener');
  else {
    var openerBox = opener.getBoundingClientRect();
    if (openerBox.width + 0.5 < 44 || openerBox.height + 0.5 < 44) {
      problems.push('create opener ' + openerBox.width.toFixed(1) + 'x' + openerBox.height.toFixed(1));
    }
    if (menu.hidden) opener.click();
  }
  if (menu.hidden) problems.push('menu stayed hidden');
  var want = ['Box', 'Cylinder', 'Disc', 'Hole', 'Sketch'];
  var items = menu.querySelectorAll('button:not([data-action="closeSheet"])');
  if (items.length !== want.length) problems.push('create items ' + items.length);
  var iw = window.innerWidth;
  var ih = window.innerHeight;
  for (var j = 0; j < want.length; j++) {
    var item = items[j];
    if (!item) continue;
    var text = (item.textContent || '').replace(/\s+/g, ' ').trim();
    if (text !== want[j]) problems.push('create item ' + j + ' ' + text);
    var itemBox = item.getBoundingClientRect();
    var itemStyle = getComputedStyle(item);
    if (itemStyle.display === 'none' || itemStyle.visibility === 'hidden' || itemBox.width < 1 || itemBox.height < 1) {
      problems.push(want[j] + ' hidden');
      continue;
    }
    if (itemBox.width + 0.5 < 44 || itemBox.height + 0.5 < 44) {
      problems.push(want[j] + ' ' + itemBox.width.toFixed(1) + 'x' + itemBox.height.toFixed(1));
    }
    if (itemBox.left < -1 || itemBox.top < -1 || itemBox.right > iw + 1 || itemBox.bottom > ih + 1) {
      problems.push(want[j] + ' offscreen ' + itemBox.left.toFixed(0) + ',' + itemBox.top.toFixed(0));
    }
  }
  var menuBox = menu.getBoundingClientRect();
  var gapBelow = ih - menuBox.bottom;
  var sheetWide = menuBox.width + 1 >= Math.min(iw - 4, Math.max(iw * 0.85, iw - 24));
  var sheet = sheetWide && menuBox.left <= 4 && gapBelow >= 36 && gapBelow <= 140;
  var popover = menuBox.width < Math.min(420, iw * 0.5) && menuBox.left > 2 && !sheet;
  var shape = 'w=' + menuBox.width.toFixed(0) + ' left=' + menuBox.left.toFixed(0) + ' gap=' + gapBelow.toFixed(0);
  if (iw >= 900) {
    if (!popover) problems.push('create popover missing ' + shape);
    if (sheet) problems.push('create sheet visible on desktop ' + shape);
  } else if (iw <= 820) {
    if (!sheet) problems.push('create sheet missing ' + shape);
    if (popover) problems.push('create popover visible at ' + Math.round(iw) + ' ' + shape);
  }
  document.dispatchEvent(new KeyboardEvent('keydown', {key:'Escape', bubbles:true, cancelable:true}));
  if (!menu.hidden) problems.push('esc did not close create');
  var expanded = document.querySelectorAll('[data-action="createMenu"]');
  for (var k = 0; k < expanded.length; k++) {
    if (expanded[k].getAttribute('aria-expanded') !== 'false') problems.push('esc aria-expanded');
  }
  opener = visibleOpener();
  if (opener) opener.click();
  if (menu.hidden) problems.push('create did not reopen');
  var canvas = document.getElementById('canvas');
  if (canvas) canvas.click();
  if (!menu.hidden) problems.push('outside did not close create');
  return JSON.stringify(problems);
})()
"""


def create_menu_problems(cdp: Cdp) -> list[str]:
    raw, err = eval_expr(cdp, CREATE_MENU_EXPR)
    if err or not isinstance(raw, str):
        return [f"create menu {raw or err}"]
    try:
        found = json.loads(raw)
    except json.JSONDecodeError:
        return [f"create menu {raw}"]
    if not isinstance(found, list):
        return [f"create menu {raw}"]
    return [str(item) for item in found]


# Portrait sketch chrome only. Does not confirm a profile or extrude, so the
# default 20 mm box is still the only body when this returns.
SKETCH_PORTRAIT_EXPR = r"""
(function(){
  var problems = [];
  function boxOf(el) {
    if (!el || el.closest('[hidden]')) return null;
    var st = getComputedStyle(el);
    if (st.display === 'none' || st.visibility === 'hidden') return null;
    var r = el.getBoundingClientRect();
    if (r.width < 1 || r.height < 1) return null;
    return r;
  }
  function need(el, label) {
    var r = boxOf(el);
    if (!r) { problems.push(label + ' hidden'); return; }
    if (r.width + 0.5 < 44 || r.height + 0.5 < 44) {
      problems.push(label + ' ' + r.width.toFixed(1) + 'x' + r.height.toFixed(1));
    }
  }
  function sheetBtn(name) {
    var buttons = document.querySelectorAll('#sheetTools button');
    for (var i = 0; i < buttons.length; i++) {
      var span = buttons[i].querySelector('span');
      if (span && span.textContent === name) return buttons[i];
    }
    return null;
  }
  function visibleClick(selector) {
    var nodes = document.querySelectorAll(selector);
    for (var i = 0; i < nodes.length; i++) {
      if (boxOf(nodes[i])) { nodes[i].click(); return true; }
    }
    if (selector === '[data-action="createMenu"]') {
      var sheet = document.getElementById('toolsSheet');
      if (!sheet || sheet.hidden) {
        var tm = document.querySelector('[data-action="toolsMenu"]');
        if (tm && boxOf(tm)) tm.click();
      }
      var sc = document.querySelector('#toolsSheet [data-action="createMenu"]');
      if (sc && (boxOf(sc) || (sheet && !sheet.hidden))) {
        sc.click();
        return true;
      }
    }
    return false;
  }
  function overlaps(a, b) {
    if (!a || !b) return false;
    return a.left < b.right - 1 && a.right > b.left + 1 && a.top < b.bottom - 1 && a.bottom > b.top + 1;
  }
  function scrollOk(label) {
    if (document.documentElement.scrollWidth > window.innerWidth + 0.5) {
      problems.push(label + ' scrollWidth ' + document.documentElement.scrollWidth);
    }
  }
  function decimal(id, label) {
    var el = document.getElementById(id);
    need(el, label);
    if (!el) return;
    if (el.getAttribute('inputmode') !== 'decimal') problems.push(label + ' inputmode');
    if (String(el.value).trim() !== '10') problems.push(label + ' value ' + el.value);
  }
  function calloutRows() {
    var rows = [];
    var layer = document.getElementById('calloutLayer');
    if (!layer || layer.hidden) return rows;
    for (var i = 0; i < 3; i++) {
      var row = document.getElementById('calloutRow' + i);
      if (!row || row.hidden) continue;
      var value = document.getElementById('calloutValue' + i);
      var tag = document.getElementById('calloutTag' + i);
      rows.push({
        tag: tag ? String(tag.textContent || '').trim() : '',
        dim: value ? (value.getAttribute('data-dim') || '') : '',
        text: value ? String(value.textContent || '').trim() : '',
        value: value,
        minus: document.getElementById('calloutMinus' + i),
        plus: document.getElementById('calloutPlus' + i)
      });
    }
    return rows;
  }
  function assertSketchCallouts(label, expected) {
    var rows = calloutRows();
    if (rows.length !== expected.length) problems.push(label + ' rows ' + rows.length);
    for (var i = 0; i < expected.length; i++) {
      var row = rows[i];
      if (!row) continue;
      if (row.tag !== expected[i].tag) problems.push(label + ' tag ' + row.tag);
      if (row.dim !== expected[i].dim) problems.push(label + ' dim ' + row.dim);
      if (row.text !== expected[i].text) problems.push(label + ' text ' + row.text);
      need(row.value, label + ' ' + expected[i].tag);
      need(row.minus, label + ' ' + expected[i].tag + ' minus');
      need(row.plus, label + ' ' + expected[i].tag + ' plus');
    }
    var layerBox = boxOf(document.getElementById('calloutLayer'));
    var vpBox = boxOf(document.getElementById('viewport'));
    var hudBox = boxOf(document.querySelector('.hud'));
    var homeBox = boxOf(document.querySelector('#cameraShelf [data-action="view"][data-view="top"]'));
    if (layerBox && vpBox) {
      var expectTop = vpBox.top + 8;
      if (hudBox) expectTop = Math.max(expectTop, hudBox.bottom + 8);
      if (homeBox && homeBox.bottom <= vpBox.top + vpBox.height / 2) expectTop = Math.max(expectTop, homeBox.bottom + 8);
      if (Math.abs((layerBox.left - vpBox.left) - 8) > 2 || Math.abs(layerBox.top - Math.round(expectTop)) > 2) {
        problems.push(label + ' not docked under hud');
      }
      var vpCx = vpBox.left + vpBox.width / 2;
      var vpCy = vpBox.top + vpBox.height / 2;
      if (vpCx >= layerBox.left - 0.5 && vpCx <= layerBox.right + 0.5 && vpCy >= layerBox.top - 0.5 && vpCy <= layerBox.bottom + 0.5) {
        problems.push(label + ' centered over viewport');
      }
    }
    if (overlaps(layerBox, homeBox)) problems.push(label + ' covers home');
    if (overlaps(layerBox, boxOf(document.getElementById('exportBtn')))) problems.push(label + ' covers export');
    if (overlaps(layerBox, boxOf(document.getElementById('statusUnits')))) problems.push(label + ' covers units');
  }
  function noSketchDims(label) {
    var rows = calloutRows();
    for (var i = 0; i < rows.length; i++) {
      if (rows[i].dim === 'sketchL' || rows[i].dim === 'sketchW' || rows[i].dim === 'sketchD' || rows[i].dim === 'sketchPolyD' || rows[i].dim === 'sketchPolySides' || rows[i].dim === 'sketchLineL' || rows[i].dim === 'sketchArcR') {
        problems.push(label + ' sketch callout ' + rows[i].dim);
      }
    }
  }
  function cover(label) {
    var sheet = document.getElementById('sketchSheet');
    var sheetBox = boxOf(sheet);
    if (!sheetBox) { problems.push(label + ' sheet hidden'); return; }
    var bars = ['.statusbar', '.vp-bar'];
    for (var i = 0; i < bars.length; i++) {
      var bar = document.querySelector(bars[i]);
      var barBox = boxOf(bar);
      if (!barBox) {
        if (bars[i] === '.vp-bar' && document.documentElement.hasAttribute('data-sketch-active')) continue;
        problems.push(label + ' missing ' + bars[i]);
        continue;
      }
      if (overlaps(sheetBox, barBox)) problems.push(label + ' covers ' + bars[i]);
    }
  }
  function assertExtrudeChips(label, mode) {
    var row = document.getElementById('sketchModeRow');
    if (!row || row.hidden) { problems.push(label + ' mode row hidden'); return; }
    var chips = row.querySelectorAll('[data-action="sketchExtrudeMode"]');
    if (chips.length !== 3) problems.push(label + ' chip count ' + chips.length);
    var names = [];
    var on = '';
    var bars = ['.statusbar', '.vp-bar'];
    for (var i = 0; i < chips.length; i++) {
      var text = (chips[i].textContent || '').replace(/\s+/g, '');
      names.push(text);
      if (/intersect/i.test(text)) problems.push(label + ' intersect chip');
      var r = boxOf(chips[i]);
      if (!r) { problems.push(label + ' ' + text + ' hidden'); continue; }
      if (r.width + 0.5 < 44 || r.height + 0.5 < 44) {
        problems.push(label + ' ' + text + ' ' + r.width.toFixed(1) + 'x' + r.height.toFixed(1));
      }
      if (r.left < -0.5 || r.right > window.innerWidth + 0.5) problems.push(label + ' ' + text + ' offscreen');
      for (var b = 0; b < bars.length; b++) {
        var bar = document.querySelector(bars[b]);
        var barBox = boxOf(bar);
        if (barBox && overlaps(r, barBox)) problems.push(label + ' ' + text + ' covers ' + bars[b]);
      }
      if (chips[i].classList.contains('is-on')) on = chips[i].getAttribute('data-mode') || '';
    }
    if (names.join(',') !== 'New,Join,Cut') problems.push(label + ' chips ' + names.join(','));
    if (on !== mode) problems.push(label + ' mode ' + on + ' wanted ' + mode);
    var chipState = hook.state();
    if (!chipState || chipState.extrudeMode !== mode) {
      problems.push(label + ' state mode ' + (chipState && chipState.extrudeMode));
    }
  }
  function tapExtrudeMode(mode) {
    var btn = document.querySelector('#sketchModeRow [data-mode="' + mode + '"]');
    if (!btn) { problems.push('missing mode ' + mode); return; }
    btn.click();
    if (!btn.classList.contains('is-on')) problems.push(mode + ' not on');
  }
  function openCreate() {
    var menu = document.getElementById('createMenu');
    if (menu && menu.hidden !== true) return true;
    return visibleClick('[data-action="createMenu"]');
  }
  var hook = window.__cadcamSketch;
  if (!hook || typeof hook.tapFace !== 'function' || typeof hook.state !== 'function') {
    problems.push('missing sketch hook');
    return JSON.stringify(problems);
  }
  if (!visibleClick('[data-action="createMenu"]')) problems.push('create opener hidden');
  var menu = document.getElementById('createMenu');
  var sketchItem = menu ? menu.querySelector('[data-action="newSketch"]') : null;
  need(sketchItem, 'Create Sketch');
  if (sketchItem) sketchItem.click();
  var st = hook.state();
  if (!st || st.tab !== 'sketch') problems.push('tab after Sketch ' + (st && st.tab));
  if (!st || st.picker !== true) problems.push('origin picker hidden before plane');
  var originBar = document.getElementById('originPlanes');
  if (!originBar || originBar.hidden !== false) problems.push('origin picker bar hidden before plane');
  need(document.querySelector('#finishBar [data-action="finishSketch"]'), 'Finish Sketch');
  scrollOk('sketch shell');
  if (!visibleClick('[data-action="toolsMenu"]')) problems.push('tools opener hidden');
  var tools = document.getElementById('toolsSheet');
  if (!tools || tools.hidden) problems.push('tools sheet hidden');
  var rectBtn = sheetBtn('Rectangle');
  var circBtn = sheetBtn('Circle');
  var lineBtn = sheetBtn('Line');
  var arcBtn = sheetBtn('Arc');
  var polyBtn = sheetBtn('Polygon');
  need(rectBtn, 'Rectangle');
  need(circBtn, 'Circle');
  need(lineBtn, 'Line');
  need(arcBtn, 'Arc');
  need(polyBtn, 'Polygon');
  var face = hook.topFace();
  if (!face) problems.push('no top face');
  var tapped = face ? hook.tapFace(face) : false;
  if (tapped !== true) problems.push('tapFace ' + String(tapped));
  st = hook.state();
  if (!st.plane) problems.push('plane not set');
  if (face && st.faceId !== face) problems.push('face ' + st.faceId);
  if (st.originPlane) problems.push('origin plane ' + st.originPlane);
  if (st.picker !== false) problems.push('picker after face');
  if (!st.selectedIds || st.selectedIds.length !== 0) problems.push('selected ' + JSON.stringify(st.selectedIds));
  if (st.highlight !== false) problems.push('highlight on');
  if (st.bodies !== 1) problems.push('bodies ' + st.bodies);
  if (st.tab !== 'sketch') problems.push('tab during plane ' + st.tab);
  var itemBtn = document.querySelector('[data-action="select"][data-mode="item"]');
  if (itemBtn) itemBtn.click();
  if (!rectBtn || !boxOf(rectBtn)) {
    visibleClick('[data-action="toolsMenu"]');
    rectBtn = sheetBtn('Rectangle');
  }
  if (rectBtn) rectBtn.click();
  else problems.push('Rectangle click missing');
  decimal('sketchL', 'Length');
  decimal('sketchW', 'Width');
  assertSketchCallouts('rect callout', [
    { tag: 'L', dim: 'sketchL', text: '10 mm' },
    { tag: 'W', dim: 'sketchW', text: '10 mm' }
  ]);
  var sketchLEl = document.getElementById('sketchL');
  var sketchWEl = document.getElementById('sketchW');
  var volBeforeCallout = window.__cadcamExportState ? Number(window.__cadcamExportState.volumeMm3) : null;
  var bodiesBeforeCallout = hook.state() ? hook.state().bodies : null;
  if (sketchLEl) {
    sketchLEl.value = '12';
    sketchLEl.dispatchEvent(new Event('input', { bubbles: true }));
  }
  var editedRows = calloutRows();
  var lengthRow = null;
  for (var ri = 0; ri < editedRows.length; ri++) if (editedRows[ri].dim === 'sketchL') lengthRow = editedRows[ri];
  if (!lengthRow || lengthRow.text !== '12 mm') problems.push('rect edit ' + (lengthRow && lengthRow.text));
  var plusBtn = document.getElementById('calloutPlus0');
  if (plusBtn) plusBtn.click();
  else problems.push('rect plus missing');
  editedRows = calloutRows();
  lengthRow = null;
  for (var rj = 0; rj < editedRows.length; rj++) if (editedRows[rj].dim === 'sketchL') lengthRow = editedRows[rj];
  if (!lengthRow || lengthRow.text !== '13 mm') problems.push('rect plus ' + (lengthRow && lengthRow.text));
  var afterPlus = hook.state();
  if (!afterPlus || afterPlus.closed !== false) problems.push('rect plus closed ' + (afterPlus && afterPlus.closed));
  if (!afterPlus || afterPlus.profile) problems.push('rect plus profile ' + (afterPlus && afterPlus.profile));
  if (!afterPlus || afterPlus.bodies !== bodiesBeforeCallout) problems.push('rect plus bodies ' + (afterPlus && afterPlus.bodies));
  var volAfterCallout = window.__cadcamExportState ? Number(window.__cadcamExportState.volumeMm3) : null;
  if (!(Math.abs(Number(volAfterCallout) - Number(volBeforeCallout)) < 0.5)) problems.push('rect plus volume ' + volAfterCallout);
  if (sketchLEl) {
    sketchLEl.value = '10';
    sketchLEl.dispatchEvent(new Event('input', { bubbles: true }));
  }
  if (sketchWEl && String(sketchWEl.value).trim() !== '10') {
    sketchWEl.value = '10';
    sketchWEl.dispatchEvent(new Event('input', { bubbles: true }));
  }
  need(document.getElementById('sketchConfirm'), 'Rectangle confirm');
  cover('rectangle');
  scrollOk('rectangle sheet');
  if (!visibleClick('[data-action="toolsMenu"]')) problems.push('tools opener for circle hidden');
  circBtn = sheetBtn('Circle');
  if (circBtn) circBtn.click();
  else problems.push('Circle click missing');
  decimal('sketchD', 'Diameter');
  assertSketchCallouts('circle callout', [
    { tag: 'Ø', dim: 'sketchD', text: '10 mm' }
  ]);
  var sketchDEl = document.getElementById('sketchD');
  if (sketchDEl) {
    sketchDEl.value = '14';
    sketchDEl.dispatchEvent(new Event('input', { bubbles: true }));
  }
  var circleRows = calloutRows();
  if (!circleRows.length || circleRows[0].dim !== 'sketchD' || circleRows[0].text !== '14 mm') {
    problems.push('circle edit ' + (circleRows[0] && circleRows[0].text));
  }
  if (sketchDEl) {
    sketchDEl.value = '10';
    sketchDEl.dispatchEvent(new Event('input', { bubbles: true }));
  }
  need(document.getElementById('sketchConfirm'), 'Circle confirm');
  cover('circle');
  scrollOk('circle sheet');
  var finish = document.querySelector('#finishBar [data-action="finishSketch"]');
  if (finish) finish.click();
  else problems.push('Finish Sketch missing');
  st = hook.state();
  if (st.tab !== 'model') problems.push('finish tab ' + st.tab);
  noSketchDims('finish');
  if (st.closed) problems.push('profile committed');
  if (st.bodies !== 1) problems.push('bodies after finish ' + st.bodies);
  if (!visibleClick('[data-action="toolsMenu"]')) problems.push('tools opener for extrude hidden');
  var ext = sheetBtn('Extrude (Push/Pull)');
  need(ext, 'Extrude');
  if (ext) ext.click();
  decimal('sketchDepth', 'Blind');
  noSketchDims('extrude');
  var confirmBtn = document.getElementById('sketchConfirm');
  need(confirmBtn, 'Extrude confirm');
  if (confirmBtn && confirmBtn.disabled !== true) problems.push('Extrude confirm enabled without a profile');
  var published = window.__cadcamExportState || {};
  if (published.sketchDepthDefault !== 10) problems.push('depth default ' + published.sketchDepthDefault);
  cover('extrude');
  assertExtrudeChips('extrude', 'join');
  scrollOk('extrude sheet');
  if (!visibleClick('[data-action="createMenu"]')) problems.push('create opener for cleanup hidden');
  menu = document.getElementById('createMenu');
  sketchItem = menu ? menu.querySelector('[data-action="newSketch"]') : null;
  if (sketchItem) sketchItem.click();
  finish = document.querySelector('#finishBar [data-action="finishSketch"]');
  if (finish) finish.click();
  st = hook.state();
  published = window.__cadcamExportState || {};
  if (st.tab !== 'model') problems.push('cleanup tab ' + st.tab);
  if (st.plane) problems.push('plane left set');
  if (st.profile) problems.push('profile left ' + st.profile);
  if (st.bodies !== 1) problems.push('cleanup bodies ' + st.bodies);
  if (published.primitiveKind !== 'box' || published.bodyCount !== 1) {
    problems.push('model ' + published.primitiveKind + ' bodies ' + published.bodyCount);
  }
  if (published.tab !== 'model') problems.push('published tab ' + published.tab);
  if (published.sketchSheetOpen) problems.push('sketch sheet left open');
  if (published.sketchPlane) problems.push('published plane left set');
  var toolsLeft = document.getElementById('toolsSheet');
  if (toolsLeft && toolsLeft.hidden !== true) problems.push('tools sheet left open');
  var menuLeft = document.getElementById('createMenu');
  if (menuLeft && menuLeft.hidden !== true) problems.push('create menu left open');
  scrollOk('cleanup');
  if (!openCreate()) problems.push('face join create hidden');
  menu = document.getElementById('createMenu');
  sketchItem = menu ? menu.querySelector('[data-action="newSketch"]') : null;
  if (sketchItem) sketchItem.click();
  else problems.push('face join sketch missing');
  var faceJoin = hook.topFace();
  if (!faceJoin) problems.push('face join no top');
  var tappedJoin = faceJoin ? hook.tapFace(faceJoin) : false;
  if (tappedJoin !== true) problems.push('face join tap ' + String(tappedJoin));
  st = hook.state();
  if (!st || !st.faceId) problems.push('face join faceId ' + (st && st.faceId));
  if (!visibleClick('[data-action="toolsMenu"]')) problems.push('face join tools hidden');
  rectBtn = sheetBtn('Rectangle');
  if (rectBtn) rectBtn.click();
  else problems.push('face join rectangle missing');
  var joinL = document.getElementById('sketchL');
  var joinW = document.getElementById('sketchW');
  if (joinL) joinL.value = '10';
  if (joinW) joinW.value = '10';
  confirmBtn = document.getElementById('sketchConfirm');
  if (confirmBtn && confirmBtn.disabled !== true) confirmBtn.click();
  else problems.push('face join rect confirm');
  finish = document.querySelector('#finishBar [data-action="finishSketch"]');
  if (finish) finish.click();
  else problems.push('face join finish missing');
  st = hook.state();
  if (!st || st.tab !== 'model' || st.profile !== 'rect' || st.closed !== true) {
    problems.push('face join profile ' + (st && st.profile) + ' tab ' + (st && st.tab));
  }
  if (!visibleClick('[data-action="toolsMenu"]')) problems.push('face join extrude tools');
  ext = sheetBtn('Extrude (Push/Pull)');
  if (ext) ext.click();
  else problems.push('face join extrude missing');
  var joinDepth = document.getElementById('sketchDepth');
  if (joinDepth) joinDepth.value = '10';
  assertExtrudeChips('face join', 'join');
  confirmBtn = document.getElementById('sketchConfirm');
  if (confirmBtn && confirmBtn.disabled !== true) confirmBtn.click();
  else problems.push('face join confirm disabled');
  st = hook.state();
  published = window.__cadcamExportState || {};
  if (!st || st.bodies !== 1) problems.push('face join bodies ' + (st && st.bodies));
  if (!st || st.emptyBodies !== 0) problems.push('face join empty ' + (st && st.emptyBodies));
  if (st && st.closed) problems.push('face join profile kept');
  if (published.bodyCount !== 1) problems.push('face join count ' + published.bodyCount);
  if (published.occtGate !== true || published.gateOcct !== 'PASS') {
    problems.push('face join occt ' + published.gateOcct + ' ' + (published.occtMessage || ''));
  }
  if (published.unitsPass !== true) problems.push('face join units');
  if (published.lastError) problems.push('face join error ' + published.lastError);
  var joinHintEl = document.getElementById('statusHint');
  var joinHint = joinHintEl ? String(joinHintEl.textContent || '') : '';
  if (joinHint.indexOf('OCCT valid') < 0 || joinHint.indexOf('mm') < 0 || joinHint.indexOf('Join') < 0) {
    problems.push('face join hint ' + joinHint);
  }
  var joinVol = Number(published.volumeMm3);
  if (!(Math.abs(joinVol - 9000) < 0.5)) problems.push('face join volume ' + joinVol);
  if (!st || !st.bounds) problems.push('face join no bounds');
  else {
    if (Math.abs(st.bounds.min[2]) > 0.25) problems.push('face join zmin ' + st.bounds.min[2]);
    if (Math.abs(st.bounds.max[2] - 30) > 0.25) problems.push('face join zmax ' + st.bounds.max[2]);
  }
  var joinDel = document.getElementById('deleteBtn');
  if (joinDel) joinDel.click();
  else problems.push('face join delete missing');
  st = hook.state();
  if (!st || st.bodies !== 0) problems.push('face reset bodies ' + (st && st.bodies));
  if (!openCreate()) problems.push('face new create hidden');
  menu = document.getElementById('createMenu');
  var faceBox = menu ? menu.querySelector('[data-action="primitive"][data-kind="box"]') : null;
  if (faceBox) faceBox.click();
  else problems.push('face new box missing');
  st = hook.state();
  if (!st || st.bodies !== 1) problems.push('face new box bodies ' + (st && st.bodies));
  if (!openCreate()) problems.push('face new sketch create');
  menu = document.getElementById('createMenu');
  sketchItem = menu ? menu.querySelector('[data-action="newSketch"]') : null;
  if (sketchItem) sketchItem.click();
  var faceNew = hook.topFace();
  var tappedNew = faceNew ? hook.tapFace(faceNew) : false;
  if (tappedNew !== true) problems.push('face new tap ' + String(tappedNew));
  if (!visibleClick('[data-action="toolsMenu"]')) problems.push('face new tools');
  rectBtn = sheetBtn('Rectangle');
  if (rectBtn) rectBtn.click();
  else problems.push('face new rectangle missing');
  if (joinL) joinL.value = '10';
  if (joinW) joinW.value = '10';
  confirmBtn = document.getElementById('sketchConfirm');
  if (confirmBtn && confirmBtn.disabled !== true) confirmBtn.click();
  else problems.push('face new rect confirm');
  finish = document.querySelector('#finishBar [data-action="finishSketch"]');
  if (finish) finish.click();
  if (!visibleClick('[data-action="toolsMenu"]')) problems.push('face new extrude tools');
  ext = sheetBtn('Extrude (Push/Pull)');
  if (ext) ext.click();
  if (joinDepth) joinDepth.value = '10';
  assertExtrudeChips('face new', 'join');
  tapExtrudeMode('new');
  confirmBtn = document.getElementById('sketchConfirm');
  if (confirmBtn && confirmBtn.disabled !== true) confirmBtn.click();
  else problems.push('face new confirm disabled');
  st = hook.state();
  published = window.__cadcamExportState || {};
  if (!st || st.bodies !== 2) problems.push('face new bodies ' + (st && st.bodies));
  if (!st || st.emptyBodies !== 0) problems.push('face new empty ' + (st && st.emptyBodies));
  if (published.bodyCount !== 2) problems.push('face new count ' + published.bodyCount);
  if (published.occtGate !== true || published.gateOcct !== 'PASS') {
    problems.push('face new occt ' + published.gateOcct + ' ' + (published.occtMessage || ''));
  }
  if (published.unitsPass !== true) problems.push('face new units');
  if (published.lastError) problems.push('face new error ' + published.lastError);
  var newHintEl = document.getElementById('statusHint');
  var newHint = newHintEl ? String(newHintEl.textContent || '') : '';
  if (newHint.indexOf('New body') < 0 || newHint.indexOf('OCCT valid') < 0) problems.push('face new hint ' + newHint);
  var itemBtnRestore = document.querySelector('[data-action="select"][data-mode="item"]');
  var restoreDel = document.getElementById('deleteBtn');
  var restoreGuard = 0;
  while (hook.state() && hook.state().bodies > 0 && restoreGuard < 4) {
    if (itemBtnRestore) itemBtnRestore.click();
    var beforeBodies = hook.state().bodies;
    if (restoreDel) restoreDel.click();
    var afterState = hook.state();
    if (!afterState || afterState.bodies >= beforeBodies) break;
    restoreGuard += 1;
  }
  st = hook.state();
  if (!st || st.bodies !== 0) problems.push('restore empty ' + (st && st.bodies));
  var emptySeqBefore = st ? st.bodySeq : null;
  if (!openCreate()) problems.push('empty sketch create hidden');
  menu = document.getElementById('createMenu');
  var emptyNewSketch = menu ? menu.querySelector('[data-action="newSketch"]') : null;
  if (emptyNewSketch) emptyNewSketch.click();
  else problems.push('empty newSketch missing');
  st = hook.state();
  published = window.__cadcamExportState || {};
  var emptyOriginBar = document.getElementById('originPlanes');
  if (!st || st.tab !== 'sketch' || st.bodies !== 0 || st.picker !== true) {
    problems.push('empty newSketch state ' + JSON.stringify(st));
  }
  if (!st || !Array.isArray(st.bodyIds) || st.bodyIds.length !== 0 || st.bodySeq !== emptySeqBefore) {
    problems.push('empty newSketch bodyIds ' + JSON.stringify(st && st.bodyIds) + ' seq ' + (st && st.bodySeq) + '/' + emptySeqBefore);
  }
  if (published.bodyCount !== 0 || (Array.isArray(published.bodyIds) && published.bodyIds.length !== 0) || published.primitiveKind) {
    problems.push('empty newSketch published ' + published.bodyCount + ' ' + published.primitiveKind);
  }
  if (!emptyOriginBar || emptyOriginBar.hidden === true || !boxOf(emptyOriginBar)) {
    problems.push('empty newSketch originPlanes hidden');
  }
  var emptyFinish = document.querySelector('#finishBar [data-action="finishSketch"]');
  if (emptyFinish) emptyFinish.click();
  else problems.push('empty finishSketch missing');
  if (!openCreate()) problems.push('restore create hidden');
  menu = document.getElementById('createMenu');
  var restoreBox = menu ? menu.querySelector('[data-action="primitive"][data-kind="box"]') : null;
  if (restoreBox) restoreBox.click();
  else problems.push('restore box missing');
  st = hook.state();
  published = window.__cadcamExportState || {};
  if (!st || st.bodies !== 1 || st.tab !== 'model' || st.plane || st.profile) {
    problems.push('restore model bodies ' + (st && st.bodies) + ' tab ' + (st && st.tab));
  }
  if (published.primitiveKind !== 'box' || published.bodyCount !== 1) {
    problems.push('restore ' + published.primitiveKind + ' bodies ' + published.bodyCount);
  }
  if (published.sketchSheetOpen) problems.push('restore sheet open');
  if (published.sketchPlane) problems.push('restore plane set');
  if (published.lastError) problems.push('restore error ' + published.lastError);
  var toolsRestore = document.getElementById('toolsSheet');
  if (toolsRestore && toolsRestore.hidden !== true) problems.push('restore tools open');
  var menuRestore = document.getElementById('createMenu');
  if (menuRestore && menuRestore.hidden !== true) problems.push('restore menu open');
  scrollOk('restore');
  return JSON.stringify(problems);
})()
"""


ORIGIN_PLANE_EXPR = r"""
(function(){
  var problems = [];
  function boxOf(el) {
    if (!el || el.closest('[hidden]')) return null;
    var st = getComputedStyle(el);
    if (st.display === 'none' || st.visibility === 'hidden') return null;
    var r = el.getBoundingClientRect();
    if (r.width < 1 || r.height < 1) return null;
    return r;
  }
  function need(el, label) {
    var r = boxOf(el);
    if (!r) { problems.push(label + ' hidden'); return; }
    if (r.width + 0.5 < 44 || r.height + 0.5 < 44) {
      problems.push(label + ' ' + r.width.toFixed(1) + 'x' + r.height.toFixed(1));
    }
  }
  function overlaps(a, b) {
    if (!a || !b) return false;
    return a.left < b.right - 1 && a.right > b.left + 1 && a.top < b.bottom - 1 && a.bottom > b.top + 1;
  }
  function near(a, b, eps) {
    if (!a || !b || a.length < 3 || b.length < 3) return false;
    return Math.abs(a[0] - b[0]) <= eps && Math.abs(a[1] - b[1]) <= eps && Math.abs(a[2] - b[2]) <= eps;
  }
  function cross(a, b) {
    return [
      a[1] * b[2] - a[2] * b[1],
      a[2] * b[0] - a[0] * b[2],
      a[0] * b[1] - a[1] * b[0]
    ];
  }
  function sheetBtn(name) {
    var buttons = document.querySelectorAll('#sheetTools button');
    for (var i = 0; i < buttons.length; i++) {
      var span = buttons[i].querySelector('span');
      if (span && span.textContent === name) return buttons[i];
    }
    return null;
  }
  function visibleClick(selector) {
    var nodes = document.querySelectorAll(selector);
    for (var i = 0; i < nodes.length; i++) {
      if (boxOf(nodes[i])) { nodes[i].click(); return true; }
    }
    if (selector === '[data-action="createMenu"]') {
      var sheet = document.getElementById('toolsSheet');
      if (!sheet || sheet.hidden) {
        var tm = document.querySelector('[data-action="toolsMenu"]');
        if (tm && boxOf(tm)) tm.click();
      }
      var sc = document.querySelector('#toolsSheet [data-action="createMenu"]');
      if (sc && (boxOf(sc) || (sheet && !sheet.hidden))) {
        sc.click();
        return true;
      }
    }
    return false;
  }
  function openTools() {
    if (!visibleClick('[data-action="toolsMenu"]')) {
      problems.push('tools opener hidden');
      return false;
    }
    var tools = document.getElementById('toolsSheet');
    if (!tools || tools.hidden) {
      problems.push('tools sheet hidden');
      return false;
    }
    return true;
  }
  function coverChips(label) {
    var barEl = document.getElementById('originPlanes');
    if (barEl && barEl.hidden) return;
    var chips = document.querySelectorAll('#originPlanes [data-action="originPlane"]');
    var bars = ['.statusbar', '.vp-bar'];
    for (var c = 0; c < chips.length; c++) {
      var chip = chips[c];
      var text = (chip.textContent || '').replace(/\s+/g, ' ').trim();
      var r = boxOf(chip);
      need(chip, label + ' ' + text);
      if (!r) continue;
      if (r.left < -0.5 || r.right > window.innerWidth + 0.5) problems.push(label + ' ' + text + ' offscreen');
      for (var i = 0; i < bars.length; i++) {
        var bar = document.querySelector(bars[i]);
        var barBox = boxOf(bar);
        if (!barBox) {
          if (bars[i] === '.vp-bar' && document.documentElement.hasAttribute('data-sketch-active')) continue;
          problems.push(label + ' missing ' + bars[i]);
          continue;
        }
        if (overlaps(r, barBox)) problems.push(label + ' ' + text + ' covers ' + bars[i]);
      }
    }
  }
  function pickPlane(plane, label, outward, u, v) {
    var barEl = document.getElementById('originPlanes');
    if (barEl && barEl.hidden) startSketch();
    var chip = document.querySelector('#originPlanes [data-plane="' + plane + '"]');
    if (!chip) { problems.push('missing ' + label); return; }
    chip.click();
    var st = hook.state();
    if (!st || st.originPlane !== plane) {
      problems.push(label + ' plane ' + (st && st.originPlane));
      return;
    }
    if (st.faceId) problems.push(label + ' faceId ' + st.faceId);
    if (!near(st.origin, [0, 0, 0], 1e-6)) problems.push(label + ' origin ' + JSON.stringify(st.origin));
    if (!near(st.outward, outward, 1e-6)) problems.push(label + ' outward ' + JSON.stringify(st.outward));
    if (!near(st.u, u, 1e-6)) problems.push(label + ' u ' + JSON.stringify(st.u));
    if (!near(st.v, v, 1e-6)) problems.push(label + ' v ' + JSON.stringify(st.v));
    if (!near(cross(st.u, st.v), st.outward, 1e-6)) problems.push(label + ' right-hand');
    if (!chip.classList.contains('is-on')) problems.push(label + ' not selected');
    if (st.picker !== false) problems.push(label + ' picker stayed visible');
    if (st.bodies !== 0) problems.push(label + ' bodies ' + st.bodies);
  }
  function setMm(id, value) {
    var el = document.getElementById(id);
    if (!el) { problems.push('missing ' + id); return; }
    el.value = value;
    if (el.getAttribute('inputmode') !== 'decimal') problems.push(id + ' inputmode');
  }
  function confirmSketch(label) {
    var btn = document.getElementById('sketchConfirm');
    need(btn, label + ' confirm');
    if (!btn) return;
    if (btn.disabled) {
      var note = document.getElementById('sketchNote');
      problems.push(label + ' confirm disabled ' + (note ? note.textContent : ''));
      return;
    }
    btn.click();
  }
  function assertExtrudeChips(label, mode) {
    var row = document.getElementById('sketchModeRow');
    if (!row || row.hidden) { problems.push(label + ' mode row hidden'); return; }
    var chips = row.querySelectorAll('[data-action="sketchExtrudeMode"]');
    if (chips.length !== 3) problems.push(label + ' chip count ' + chips.length);
    var names = [];
    var on = '';
    var bars = ['.statusbar', '.vp-bar'];
    for (var i = 0; i < chips.length; i++) {
      var text = (chips[i].textContent || '').replace(/\s+/g, '');
      names.push(text);
      if (/intersect/i.test(text)) problems.push(label + ' intersect chip');
      var r = boxOf(chips[i]);
      if (!r) { problems.push(label + ' ' + text + ' hidden'); continue; }
      if (r.width + 0.5 < 44 || r.height + 0.5 < 44) {
        problems.push(label + ' ' + text + ' ' + r.width.toFixed(1) + 'x' + r.height.toFixed(1));
      }
      if (r.left < -0.5 || r.right > window.innerWidth + 0.5) problems.push(label + ' ' + text + ' offscreen');
      for (var b = 0; b < bars.length; b++) {
        var bar = document.querySelector(bars[b]);
        var barBox = boxOf(bar);
        if (barBox && overlaps(r, barBox)) problems.push(label + ' ' + text + ' covers ' + bars[b]);
      }
      if (chips[i].classList.contains('is-on')) on = chips[i].getAttribute('data-mode') || '';
    }
    if (names.join(',') !== 'New,Join,Cut') problems.push(label + ' chips ' + names.join(','));
    if (on !== mode) problems.push(label + ' mode ' + on + ' wanted ' + mode);
    var chipState = hook.state();
    if (!chipState || chipState.extrudeMode !== mode) {
      problems.push(label + ' state mode ' + (chipState && chipState.extrudeMode));
    }
  }
  function tapExtrudeMode(mode) {
    var btn = document.querySelector('#sketchModeRow [data-mode="' + mode + '"]');
    if (!btn) { problems.push('missing mode ' + mode); return; }
    btn.click();
    if (!btn.classList.contains('is-on')) problems.push(mode + ' not on');
  }
  function hintText() {
    var hint = document.getElementById('statusHint');
    return hint ? String(hint.textContent || '') : '';
  }
  function addBox(label) {
    if (!visibleClick('[data-action="createMenu"]')) { problems.push(label + ' create hidden'); return false; }
    var menu = document.getElementById('createMenu');
    var boxBtn = menu ? menu.querySelector('[data-action="primitive"][data-kind="box"]') : null;
    if (!boxBtn) { problems.push(label + ' box missing'); return false; }
    boxBtn.click();
    return true;
  }
  function selectItem(label) {
    var itemBtn = document.querySelector('[data-action="select"][data-mode="item"]');
    if (!itemBtn) { problems.push(label + ' item missing'); return false; }
    itemBtn.click();
    return true;
  }
  function deleteAll(label) {
    var guard = 0;
    while (hook.state() && hook.state().bodies > 0 && guard < 6) {
      if (!selectItem(label)) return false;
      var del = document.getElementById('deleteBtn');
      if (!del) { problems.push(label + ' delete missing'); return false; }
      var before = hook.state().bodies;
      del.click();
      var after = hook.state();
      if (!after || after.bodies >= before) {
        problems.push(label + ' delete stuck ' + (after && after.bodies));
        return false;
      }
      guard += 1;
    }
    return !!(hook.state() && hook.state().bodies === 0);
  }
  function openExtrude(label) {
    if (!openTools()) return false;
    var ext = sheetBtn('Extrude (Push/Pull)');
    if (!ext) { problems.push(label + ' extrude missing'); return false; }
    ext.click();
    return true;
  }
  function extrude(kind) {
    var finish = document.querySelector('#finishBar [data-action="finishSketch"]');
    if (finish) finish.click();
    else problems.push(kind + ' finish missing');
    var st = hook.state();
    if (!st || st.tab !== 'model') problems.push(kind + ' finish tab ' + (st && st.tab));
    if (!st || st.closed !== true) problems.push(kind + ' profile not closed');
    if (!openTools()) return;
    var ext = sheetBtn('Extrude (Push/Pull)');
    if (!ext) { problems.push(kind + ' extrude missing'); return; }
    ext.click();
    setMm('sketchDepth', '10');
    var depth = document.getElementById('sketchDepth');
    if (depth && String(depth.value).trim() !== '10') problems.push(kind + ' depth ' + (depth && depth.value));
    assertExtrudeChips(kind, 'new');
    confirmSketch(kind + ' extrude');
  }
  function assertSolid(kind, expectVol, checkBounds) {
    var st = hook.state();
    var published = window.__cadcamExportState || {};
    if (!st || st.bodies !== 1) problems.push(kind + ' bodies ' + (st && st.bodies));
    if (!st || st.picker !== false) problems.push(kind + ' picker still on');
    if (!st || !st.bounds) problems.push(kind + ' no bounds');
    else {
      if (st.bounds.kind !== 'extrude') problems.push(kind + ' kind ' + st.bounds.kind);
      checkBounds(st.bounds);
    }
    if (published.bodyCount !== 1) problems.push(kind + ' bodyCount ' + published.bodyCount);
    if (published.occtGate !== true || published.gateOcct !== 'PASS') {
      problems.push(kind + ' occt ' + published.gateOcct + ' ' + (published.occtMessage || ''));
    }
    if (published.unitsPass !== true) problems.push(kind + ' unitsPass');
    var units = document.getElementById('statusUnits');
    if (!units || !/mm/i.test(units.textContent || '')) problems.push(kind + ' units ' + (units ? units.textContent : 'missing'));
    if (published.lastError) problems.push(kind + ' error ' + published.lastError);
    var hint = document.getElementById('statusHint');
    var hintText = hint ? String(hint.textContent || '') : '';
    if (hintText.indexOf('OCCT valid') < 0 || hintText.indexOf('mm') < 0) problems.push(kind + ' hint ' + hintText);
    if (published.primitiveKind) problems.push(kind + ' primitive ' + published.primitiveKind);
    var vol = Number(published.volumeMm3);
    if (!(Math.abs(vol - expectVol) < 0.5)) problems.push(kind + ' volume ' + vol);
  }
  function ensureEmpty(label) {
    var st0 = hook.state();
    if (st0 && st0.bodies === 0) return st0;
    if (!st0 || st0.bodies !== 1) {
      problems.push(label + ' bodies ' + (st0 && st0.bodies));
      return null;
    }
    var del = document.getElementById('deleteBtn');
    if (!del) { problems.push(label + ' delete missing'); return null; }
    del.click();
    var st = hook.state();
    var published = window.__cadcamExportState || {};
    if (!st || st.bodies !== 0) {
      problems.push(label + ' left ' + (st && st.bodies) + ' ' + (published.lastError || ''));
      return null;
    }
    if (!Array.isArray(st.bodyIds) || st.bodyIds.length !== 0) {
      problems.push(label + ' bodyIds ' + JSON.stringify(st.bodyIds));
    }
    if (published.bodyCount !== 0 || (Array.isArray(published.bodyIds) && published.bodyIds.length !== 0)) {
      problems.push(label + ' published bodyCount ' + published.bodyCount);
    }
    if (published.projectBlank === true || st.projectBlank === true) problems.push(label + ' projectBlank');
    return st;
  }
  function startSketch() {
    var stBefore = hook.state();
    var seqBefore = stBefore ? stBefore.bodySeq : null;
    if (!visibleClick('[data-action="createMenu"]')) problems.push('create opener hidden');
    var menu = document.getElementById('createMenu');
    var sketchItem = menu ? menu.querySelector('[data-action="newSketch"]') : null;
    if (!sketchItem) { problems.push('Create Sketch missing'); return null; }
    sketchItem.click();
    var st = hook.state();
    var published = window.__cadcamExportState || {};
    var originBarNow = document.getElementById('originPlanes');
    if (!st || st.tab !== 'sketch') problems.push('tab ' + (st && st.tab));
    if (!st || st.bodies !== 0 || published.bodyCount !== 0) problems.push('sketch bodies ' + (st && st.bodies) + '/' + published.bodyCount);
    if (!st || st.picker !== true) problems.push('picker off on empty doc');
    if (!originBarNow || originBarNow.hidden === true || !boxOf(originBarNow)) problems.push('originPlanes hidden on empty newSketch');
    if (!st || !Array.isArray(st.bodyIds) || st.bodyIds.length !== 0) {
      problems.push('newSketch spawned bodyIds ' + JSON.stringify(st && st.bodyIds));
    }
    if (Array.isArray(published.bodyIds) && published.bodyIds.length !== 0) {
      problems.push('newSketch published bodyIds ' + JSON.stringify(published.bodyIds));
    }
    if (seqBefore !== null && st && st.bodySeq !== seqBefore) {
      problems.push('newSketch advanced bodySeq ' + seqBefore + ' -> ' + st.bodySeq);
    }
    if (published.primitiveKind) {
      problems.push('newSketch spawned primitive ' + published.primitiveKind);
    }
    if (st && st.projectBlank === true) problems.push('empty doc required projectBlank');
    return st;
  }
  if (Math.abs(window.innerWidth - 390) > 0.5 || Math.abs(window.innerHeight - 844) > 0.5) {
    problems.push('viewport ' + window.innerWidth + 'x' + window.innerHeight);
  }
  var hook = window.__cadcamSketch;
  if (!hook || typeof hook.state !== 'function') {
    problems.push('missing sketch hook');
    return JSON.stringify(problems);
  }
  var before = hook.state();
  var beforePub = window.__cadcamExportState || {};
  if (!before || before.bodies !== 1 || before.picker !== false || !Array.isArray(before.bodyIds) || before.bodyIds.length !== 1) {
    problems.push('cube start bodies ' + (before && before.bodies) + ' picker ' + (before && before.picker));
  }
  if (beforePub.primitiveKind !== 'box' || !(Math.abs(Number(beforePub.volumeMm3) - 8000) < 0.5)) {
    problems.push('boot cube ' + beforePub.primitiveKind + ' vol ' + beforePub.volumeMm3);
  }
  if (!visibleClick('[data-action="createMenu"]')) problems.push('create opener hidden');
  var menu0 = document.getElementById('createMenu');
  var sketch0 = menu0 ? menu0.querySelector('[data-action="newSketch"]') : null;
  if (sketch0) sketch0.click();
  else problems.push('Create Sketch missing');
  var cube = hook.state();
  var originBarCube = document.getElementById('originPlanes');
  if (!cube || cube.tab !== 'sketch' || cube.picker !== true || cube.bodies !== 1 || !originBarCube || originBarCube.hidden) {
    problems.push('cube sketch picker ' + (cube && cube.picker) + ' tab ' + (cube && cube.tab) + ' bodies ' + (cube && cube.bodies));
  }
  var cubeFace = typeof hook.topFace === 'function' ? hook.topFace() : null;
  if (!cubeFace || typeof hook.tapFace !== 'function' || !hook.tapFace(cubeFace)) {
    problems.push('cube face tap failed ' + cubeFace);
  }
  cube = hook.state();
  if (!cube || !cube.plane || cube.faceId !== cubeFace || cube.originPlane !== '' || cube.picker !== false) {
    problems.push('cube face plane ' + JSON.stringify(cube));
  }
  var finish0 = document.querySelector('#finishBar [data-action="finishSketch"]');
  if (finish0) finish0.click();
  else problems.push('cube finish missing');
  cube = hook.state();
  if (!cube || cube.tab !== 'model' || cube.picker !== false) problems.push('cube finish ' + (cube && cube.tab));
  if (!ensureEmpty('clear cube')) return JSON.stringify(problems);
  if (!startSketch()) return JSON.stringify(problems);
  var originBar = document.getElementById('originPlanes');
  if (!originBar || originBar.hidden === true) problems.push('origin picker hidden');
  var chips = originBar ? originBar.querySelectorAll('[data-action="originPlane"]') : [];
  if (chips.length !== 6) problems.push('chip count ' + chips.length);
  var labels = [];
  for (var i = 0; i < chips.length; i++) {
    labels.push(((chips[i].textContent || '').replace(/\s+/g, '') ) + ':' + chips[i].getAttribute('data-plane'));
  }
  if (labels.join(',') !== 'Front:xz,Back:back,Top:xy,Bottom:bottom,Left:left,Right:yz') problems.push('chips ' + labels.join(','));
  coverChips('planes');
  if (document.documentElement.scrollWidth > window.innerWidth + 0.5) {
    problems.push('chip scrollWidth ' + document.documentElement.scrollWidth);
  }
  pickPlane('xz', 'Front', [0, 1, 0], [1, 0, 0], [0, 0, -1]);
  pickPlane('back', 'Back', [0, -1, 0], [1, 0, 0], [0, 0, 1]);
  pickPlane('bottom', 'Bottom', [0, 0, -1], [1, 0, 0], [0, -1, 0]);
  pickPlane('left', 'Left', [-1, 0, 0], [0, 1, 0], [0, 0, -1]);
  pickPlane('yz', 'Right', [1, 0, 0], [0, 1, 0], [0, 0, 1]);
  pickPlane('xy', 'Top', [0, 0, 1], [1, 0, 0], [0, 1, 0]);
  if (openTools()) {
    var rectBtn = sheetBtn('Rectangle');
    if (!rectBtn) problems.push('Rectangle missing');
    else rectBtn.click();
    setMm('sketchL', '10');
    setMm('sketchW', '10');
    coverChips('rect sheet');
    confirmSketch('rect');
    var drawn = hook.state();
    if (!drawn || drawn.profile !== 'rect' || drawn.closed !== true) problems.push('rect profile ' + (drawn && drawn.profile));
    extrude('rect');
    assertSolid('rect', 1000, function (bounds) {
      var min = bounds.min;
      var max = bounds.max;
      for (var k = 0; k < 3; k++) {
        if (Math.abs(min[k]) > 0.05) problems.push('rect min ' + k + ' ' + min[k]);
        if (Math.abs(max[k] - 10) > 0.05) problems.push('rect max ' + k + ' ' + max[k]);
      }
    });
  }
  if (!ensureEmpty('clear rect')) return JSON.stringify(problems);
  if (!startSketch()) return JSON.stringify(problems);
  pickPlane('xy', 'Top circle', [0, 0, 1], [1, 0, 0], [0, 1, 0]);
  if (openTools()) {
    var circBtn = sheetBtn('Circle');
    if (!circBtn) problems.push('Circle missing');
    else circBtn.click();
    setMm('sketchD', '10');
    confirmSketch('circle');
    var circled = hook.state();
    if (!circled || circled.profile !== 'circle' || circled.closed !== true) problems.push('circle profile ' + (circled && circled.profile));
    extrude('circle');
    assertSolid('circle', Math.PI * 25 * 10, function (bounds) {
      var min = bounds.min;
      var max = bounds.max;
      if (Math.abs(min[2]) > 0.2) problems.push('circle zmin ' + min[2]);
      if (Math.abs(max[2] - 10) > 0.2) problems.push('circle zmax ' + max[2]);
      if (!(min[0] < -4 && max[0] > 4 && min[1] < -4 && max[1] > 4)) {
        problems.push('circle xy ' + JSON.stringify(min) + ' ' + JSON.stringify(max));
      }
      var reach = Math.max(Math.abs(min[0]), Math.abs(max[0]), Math.abs(min[1]), Math.abs(max[1]));
      if (reach < 4.5 || reach > 5.2) problems.push('circle radius ' + reach);
    });
  }
  if (!ensureEmpty('join empty')) return JSON.stringify(problems);
  if (startSketch()) {
    pickPlane('xy', 'Join empty', [0, 0, 1], [1, 0, 0], [0, 1, 0]);
    if (openTools()) {
      var emptyRect = sheetBtn('Rectangle');
      if (!emptyRect) problems.push('join empty rectangle missing');
      else emptyRect.click();
      setMm('sketchL', '10');
      setMm('sketchW', '10');
      confirmSketch('join empty rect');
      var emptyFinish = document.querySelector('#finishBar [data-action="finishSketch"]');
      if (emptyFinish) emptyFinish.click();
      else problems.push('join empty finish missing');
      var emptySt = hook.state();
      if (!emptySt || emptySt.bodies !== 0 || emptySt.profile !== 'rect' || emptySt.faceId) {
        problems.push('join empty profile ' + (emptySt && emptySt.profile) + ' bodies ' + (emptySt && emptySt.bodies) + ' face ' + (emptySt && emptySt.faceId));
      }
      if (openExtrude('join empty')) {
        assertExtrudeChips('join empty', 'new');
        tapExtrudeMode('join');
        confirmSketch('join empty');
        emptySt = hook.state();
        var emptyHint = hintText();
        if (!emptySt || emptySt.bodies !== 0) problems.push('join empty bodies ' + (emptySt && emptySt.bodies));
        if (!emptySt || emptySt.profile !== 'rect') problems.push('join empty kept ' + (emptySt && emptySt.profile));
        if (emptyHint.indexOf('need a body') < 0) problems.push('join empty hint ' + emptyHint);
        tapExtrudeMode('cut');
        confirmSketch('cut empty');
        emptySt = hook.state();
        emptyHint = hintText();
        if (!emptySt || emptySt.bodies !== 0) problems.push('cut empty bodies ' + (emptySt && emptySt.bodies));
        if (!emptySt || emptySt.profile !== 'rect') problems.push('cut empty kept ' + (emptySt && emptySt.profile));
        if (emptyHint.indexOf('need a body') < 0) problems.push('cut empty hint ' + emptyHint);
      }
    }
  }
  if (addBox('origin box')) {
    var boxSt = hook.state();
    var boxPub = window.__cadcamExportState || {};
    if (!boxSt || boxSt.bodies !== 1) problems.push('origin box bodies ' + (boxSt && boxSt.bodies));
    if (!boxSt || boxSt.picker !== false) problems.push('origin box picker');
    if (!boxSt || boxSt.faceId) problems.push('origin box face ' + (boxSt && boxSt.faceId));
    if (!boxSt || (boxSt.selectedIds && boxSt.selectedIds.length !== 0)) {
      problems.push('origin box selected ' + JSON.stringify(boxSt && boxSt.selectedIds));
    }
    if (!(Math.abs(Number(boxPub.volumeMm3) - 8000) < 0.5)) problems.push('origin box volume ' + boxPub.volumeMm3);
    if (boxSt && boxSt.profile !== 'rect') problems.push('origin box profile ' + (boxSt && boxSt.profile));
    if (openExtrude('origin none')) {
      assertExtrudeChips('origin none', 'new');
      tapExtrudeMode('join');
      confirmSketch('origin none');
      boxSt = hook.state();
      boxPub = window.__cadcamExportState || {};
      if (!boxSt || boxSt.bodies !== 1) problems.push('origin none bodies ' + (boxSt && boxSt.bodies));
      if (!(Math.abs(Number(boxPub.volumeMm3) - 8000) < 0.5)) problems.push('origin none volume ' + boxPub.volumeMm3);
      if (!boxSt || boxSt.profile !== 'rect') problems.push('origin none profile ' + (boxSt && boxSt.profile));
      if (hintText().indexOf('exactly one') < 0) problems.push('origin none hint ' + hintText());
      if (boxPub.occtGate !== true) problems.push('origin none occt ' + boxPub.gateOcct);
    }
  }
  if (addBox('origin second')) {
    var twoSt = hook.state();
    if (!twoSt || twoSt.bodies !== 2) problems.push('origin second bodies ' + (twoSt && twoSt.bodies));
    if (selectItem('origin two') && openExtrude('origin two')) {
      assertExtrudeChips('origin two', 'new');
      tapExtrudeMode('cut');
      confirmSketch('origin two');
      twoSt = hook.state();
      if (!twoSt || twoSt.bodies !== 2) problems.push('origin two after ' + (twoSt && twoSt.bodies));
      if (!twoSt || twoSt.profile !== 'rect') problems.push('origin two profile ' + (twoSt && twoSt.profile));
      if (hintText().indexOf('exactly one') < 0) problems.push('origin two hint ' + hintText());
    }
  }
  if (deleteAll('origin clear') && addBox('overlap box')) {
    var cutSt = hook.state();
    var cutPub = window.__cadcamExportState || {};
    if (!cutSt || cutSt.bodies !== 1 || cutSt.profile !== 'rect') {
      problems.push('overlap setup bodies ' + (cutSt && cutSt.bodies) + ' profile ' + (cutSt && cutSt.profile));
    }
    if (!(Math.abs(Number(cutPub.volumeMm3) - 8000) < 0.5)) problems.push('overlap box volume ' + cutPub.volumeMm3);
    if (selectItem('overlap') && openExtrude('overlap')) {
      assertExtrudeChips('overlap', 'new');
      setMm('sketchDepth', '10');
      tapExtrudeMode('cut');
      confirmSketch('overlap cut');
      cutSt = hook.state();
      cutPub = window.__cadcamExportState || {};
      if (!cutSt || cutSt.bodies !== 1) problems.push('overlap bodies ' + (cutSt && cutSt.bodies));
      if (!cutSt || cutSt.emptyBodies !== 0) problems.push('overlap empty ' + (cutSt && cutSt.emptyBodies));
      if (cutPub.bodyCount !== 1) problems.push('overlap count ' + cutPub.bodyCount);
      if (!(Math.abs(Number(cutPub.volumeMm3) - 7000) < 0.5)) problems.push('overlap volume ' + cutPub.volumeMm3);
      if (cutPub.occtGate !== true || cutPub.gateOcct !== 'PASS') {
        problems.push('overlap occt ' + cutPub.gateOcct + ' ' + (cutPub.occtMessage || ''));
      }
      if (cutPub.unitsPass !== true) problems.push('overlap units');
      if (cutPub.lastError) problems.push('overlap error ' + cutPub.lastError);
      var overlapHint = hintText();
      if (overlapHint.indexOf('OCCT valid') < 0 || overlapHint.indexOf('mm') < 0) problems.push('overlap hint ' + overlapHint);
    }
  }
  if (!ensureEmpty('contain clear')) return JSON.stringify(problems);
  if (startSketch()) {
    pickPlane('xy', 'Contain', [0, 0, 1], [1, 0, 0], [0, 1, 0]);
    if (openTools()) {
      var containCirc = sheetBtn('Circle');
      if (!containCirc) problems.push('contain circle missing');
      else containCirc.click();
      setMm('sketchD', '40');
      confirmSketch('contain circle');
      var containFinish = document.querySelector('#finishBar [data-action="finishSketch"]');
      if (containFinish) containFinish.click();
      var containSt = hook.state();
      if (!containSt || containSt.profile !== 'circle' || containSt.bodies !== 0) {
        problems.push('contain profile ' + (containSt && containSt.profile) + ' bodies ' + (containSt && containSt.bodies));
      }
      if (addBox('contain box') && selectItem('contain') && openExtrude('contain')) {
        assertExtrudeChips('contain', 'new');
        tapExtrudeMode('cut');
        setMm('sketchDepth', '30');
        confirmSketch('contain cut');
        containSt = hook.state();
        var containPub = window.__cadcamExportState || {};
        if (!containSt || containSt.bodies !== 1) problems.push('contain bodies ' + (containSt && containSt.bodies));
        if (!containSt || containSt.emptyBodies !== 0) problems.push('contain empty ' + (containSt && containSt.emptyBodies));
        if (containPub.bodyCount !== 1) problems.push('contain count ' + containPub.bodyCount);
        if (!(Math.abs(Number(containPub.volumeMm3) - 8000) < 0.5)) problems.push('contain volume ' + containPub.volumeMm3);
        if (hintText().indexOf('Cut removed the whole body') < 0) problems.push('contain hint ' + hintText());
        if (!containSt || containSt.profile !== 'circle') problems.push('contain profile kept ' + (containSt && containSt.profile));
        if (containSt && containSt.picker !== false) problems.push('contain picker');
      }
    }
  }
  if (!ensureEmpty('line clear')) return JSON.stringify(problems);
  if (!startSketch()) return JSON.stringify(problems);
  pickPlane('xy', 'Line top', [0, 0, 1], [1, 0, 0], [0, 1, 0]);
  var lineSheet = document.getElementById('sketchSheet');
  if (!lineSheet || lineSheet.hidden !== true) problems.push('line start sheet open');
  var trimRibbon = document.querySelector('.tool-btn[data-tool="Trim"]');
  if (!trimRibbon) problems.push('Trim button missing');
  else if (trimRibbon.getAttribute('data-action')) problems.push('Trim data-action ' + trimRibbon.getAttribute('data-action'));
  if (openTools()) {
    var trimBtn = sheetBtn('Trim');
    if (trimBtn) problems.push('Trim sheet visible during sketch');
    var lineTool = sheetBtn('Line');
    need(lineTool, 'Line');
    if (!lineTool) problems.push('Line missing');
    else lineTool.click();
    var lineNote = document.getElementById('sketchNote');
    if (!lineNote || lineNote.textContent !== 'Line') problems.push('line note ' + (lineNote && lineNote.textContent));
    var lineRect = document.getElementById('sketchRectRow');
    var lineCirc = document.getElementById('sketchCircRow');
    var lineRow = document.getElementById('sketchLineRow');
    var lineDepth = document.getElementById('sketchDepthRow');
    if (!lineRect || lineRect.hidden !== true) problems.push('line shows length');
    if (!lineCirc || lineCirc.hidden !== true) problems.push('line shows diameter');
    if (!lineRow || lineRow.hidden !== false) problems.push('line row hidden');
    if (!lineDepth || lineDepth.hidden !== true) problems.push('line shows depth');
    if (boxOf(document.getElementById('sketchL'))) problems.push('line shows sketchL');
    if (boxOf(document.getElementById('sketchW'))) problems.push('line shows sketchW');
    if (boxOf(document.getElementById('sketchD'))) problems.push('line shows sketchD');
    var lineLEl = document.getElementById('sketchLineL');
    need(lineLEl, 'Line length');
    if (!lineLEl || lineLEl.getAttribute('inputmode') !== 'decimal') problems.push('line length inputmode');
    var lineCallout0 = document.getElementById('calloutValue0');
    if (!lineCallout0 || !boxOf(lineCallout0) || lineCallout0.getAttribute('data-dim') !== 'sketchLineL') {
      problems.push('line callout missing');
    }
    need(document.getElementById('calloutMinus0'), 'Line callout minus');
    need(lineCallout0, 'Line callout value');
    need(document.getElementById('calloutPlus0'), 'Line callout plus');
    var lineSheetBox = boxOf(document.getElementById('sketchSheet'));
    if (!lineSheetBox) problems.push('line sheet hidden');
    var lineKeep = ['#exportBtn', '#statusUnits'];
    for (var lk = 0; lk < lineKeep.length; lk++) {
      var keepEl = document.querySelector(lineKeep[lk]);
      var keepBox = boxOf(keepEl);
      if (keepBox && overlaps(lineSheetBox, keepBox)) problems.push('line covers ' + lineKeep[lk]);
    }
    var beforeLine = hook.state();
    var beforeBodies = beforeLine ? beforeLine.bodies : -1;
    if (typeof hook.placeLineVertex !== 'function') problems.push('placeLineVertex missing');
    else {
      if (hook.placeLineVertex(0, 0) !== true) problems.push('line vertex 1');
      if (hook.placeLineVertex(10, 0) !== true) problems.push('line vertex 2');
    }
    if (!lineCallout0 || String(lineCallout0.textContent || '').trim() !== '10 mm') {
      problems.push('line callout at 2 ' + (lineCallout0 && lineCallout0.textContent));
    }
    var two = hook.state();
    if (!two || two.lineVertices !== 2) problems.push('lineVertices 2 ' + (two && two.lineVertices));
    if (!two || two.closed !== false) problems.push('line closed at 2');
    if (!two || two.bodies !== beforeBodies) problems.push('line bodies ' + (two && two.bodies));
    var twoBtn = document.getElementById('sketchConfirm');
    need(twoBtn, 'Line confirm');
    if (!twoBtn || twoBtn.disabled !== true || twoBtn.getAttribute('aria-disabled') !== 'true') {
      problems.push('line confirm enabled at 2');
    }
    if (typeof hook.placeLineVertex === 'function' && hook.placeLineVertex(0, 10) !== true) problems.push('line vertex 3');
    if (!lineCallout0 || String(lineCallout0.textContent || '').trim() !== '14.142 mm') {
      problems.push('line callout at 3 ' + (lineCallout0 && lineCallout0.textContent));
    }
    var three = hook.state();
    if (!three || three.lineVertices !== 3 || three.closed !== false) {
      problems.push('line before confirm n ' + (three && three.lineVertices) + ' closed ' + (three && three.closed));
    }
    confirmSketch('line');
    if (boxOf(document.getElementById('calloutRow0'))) problems.push('line callout stayed after confirm');
    var drawnLine = hook.state();
    if (!drawnLine || drawnLine.profile !== 'line' || drawnLine.closed !== true || drawnLine.lineVertices !== 3) {
      problems.push('line profile ' + (drawnLine && drawnLine.profile) + ' closed ' + (drawnLine && drawnLine.closed) + ' n ' + (drawnLine && drawnLine.lineVertices));
    }
    extrude('line');
    assertSolid('line', 500, function (bounds) {
      var min = bounds.min;
      var max = bounds.max;
      for (var axis = 0; axis < 3; axis++) {
        if (Math.abs(min[axis]) > 0.05) problems.push('line min ' + axis + ' ' + min[axis]);
        if (Math.abs(max[axis] - 10) > 0.05) problems.push('line max ' + axis + ' ' + max[axis]);
      }
    });
  }
  if (!ensureEmpty('line typed clear')) return JSON.stringify(problems);
  if (!startSketch()) return JSON.stringify(problems);
  pickPlane('xy', 'Line typed top', [0, 0, 1], [1, 0, 0], [0, 1, 0]);
  if (openTools()) {
    var lineTypedTool = sheetBtn('Line');
    if (!lineTypedTool) problems.push('Line typed missing');
    else lineTypedTool.click();
    hook.placeLineVertex(0, 0);
    hook.placeLineVertex(10, 0);
    hook.placeLineVertex(10, 5);
    var lineTypedEl = document.getElementById('sketchLineL');
    if (!lineTypedEl || String(lineTypedEl.value).trim() !== '5') {
      problems.push('line typed initial ' + (lineTypedEl && lineTypedEl.value));
    }
    if (lineTypedEl) {
      lineTypedEl.value = '10';
      lineTypedEl.dispatchEvent(new Event('input', { bubbles: true }));
    }
    var lineTypedVal0 = document.getElementById('calloutValue0');
    if (!lineTypedVal0 || String(lineTypedVal0.textContent || '').trim() !== '10 mm') {
      problems.push('line typed callout ' + (lineTypedVal0 && lineTypedVal0.textContent));
    }
    confirmSketch('line typed');
    extrude('line typed');
    assertSolid('line typed', 500, function (bounds) {
      if (Math.abs(bounds.max[0] - 10) > 0.05 || Math.abs(bounds.max[1] - 10) > 0.05) {
        problems.push('line typed bounds ' + JSON.stringify(bounds));
      }
    });
  }
  if (!ensureEmpty('arc clear')) return JSON.stringify(problems);
  if (!startSketch()) return JSON.stringify(problems);
  pickPlane('xy', 'Arc top', [0, 0, 1], [1, 0, 0], [0, 1, 0]);
  var arcRibbon = document.querySelector('.tool-btn[data-tool="Arc"]');
  if (!arcRibbon) problems.push('Arc button missing');
  else if (arcRibbon.getAttribute('data-action') !== 'sketchArc') problems.push('Arc data-action ' + arcRibbon.getAttribute('data-action'));
  if (openTools()) {
    var arcTool = sheetBtn('Arc');
    need(arcTool, 'Arc');
    if (!arcTool) problems.push('Arc missing');
    else arcTool.click();
    var arcNote = document.getElementById('sketchNote');
    if (!arcNote || arcNote.textContent !== 'Arc') problems.push('arc note ' + (arcNote && arcNote.textContent));
    var arcRect = document.getElementById('sketchRectRow');
    var arcCirc = document.getElementById('sketchCircRow');
    var arcPoly = document.getElementById('sketchPolyRow');
    var arcRow = document.getElementById('sketchArcRow');
    var arcDepth = document.getElementById('sketchDepthRow');
    if (!arcRect || arcRect.hidden !== true) problems.push('arc shows length');
    if (!arcCirc || arcCirc.hidden !== true) problems.push('arc shows diameter');
    if (!arcPoly || arcPoly.hidden !== true) problems.push('arc shows polygon');
    if (!arcRow || arcRow.hidden !== false) problems.push('arc row hidden');
    if (!arcDepth || arcDepth.hidden !== true) problems.push('arc shows depth');
    if (boxOf(document.getElementById('sketchL'))) problems.push('arc shows sketchL');
    if (boxOf(document.getElementById('sketchW'))) problems.push('arc shows sketchW');
    if (boxOf(document.getElementById('sketchD'))) problems.push('arc shows sketchD');
    var arcREl = document.getElementById('sketchArcR');
    need(arcREl, 'Arc radius');
    if (!arcREl || arcREl.getAttribute('inputmode') !== 'decimal') problems.push('arc radius inputmode');
    var arcCallout0 = document.getElementById('calloutValue0');
    if (!arcCallout0 || !boxOf(arcCallout0) || arcCallout0.getAttribute('data-dim') !== 'sketchArcR') {
      problems.push('arc callout missing');
    }
    need(document.getElementById('calloutMinus0'), 'Arc callout minus');
    need(arcCallout0, 'Arc callout value');
    need(document.getElementById('calloutPlus0'), 'Arc callout plus');
    var arcSheetBox = boxOf(document.getElementById('sketchSheet'));
    if (!arcSheetBox) problems.push('arc sheet hidden');
    var arcKeep = ['#exportBtn', '#statusUnits'];
    for (var ak = 0; ak < arcKeep.length; ak++) {
      var arcKeepBox = boxOf(document.querySelector(arcKeep[ak]));
      if (arcKeepBox && overlaps(arcSheetBox, arcKeepBox)) problems.push('arc covers ' + arcKeep[ak]);
    }
    if (typeof hook.placeArcPoint !== 'function') problems.push('placeArcPoint missing');
    else {
      if (hook.placeArcPoint(0, 0) !== true) problems.push('arc colinear 1');
      if (hook.placeArcPoint(5, 0) !== true) problems.push('arc colinear 2');
      var arcTwo = hook.state();
      var arcBtn = document.getElementById('sketchConfirm');
      need(arcBtn, 'Arc confirm');
      if (!arcTwo || arcTwo.arcPoints !== 2 || arcTwo.closed !== false) {
        problems.push('arc at 2 ' + (arcTwo && arcTwo.arcPoints));
      }
      if (!arcBtn || arcBtn.disabled !== true || arcBtn.getAttribute('aria-disabled') !== 'true') {
        problems.push('arc confirm enabled at 2');
      }
      if (hook.placeArcPoint(10, 0) !== true) problems.push('arc colinear 3');
      if (arcBtn) arcBtn.click();
      var afterColinear = hook.state();
      if (!afterColinear || afterColinear.closed !== false || afterColinear.profile) {
        problems.push('arc colinear accepted ' + (afterColinear && afterColinear.profile) + ' closed ' + (afterColinear && afterColinear.closed));
      }
      if (hook.placeArcPoint(0, 0) !== true) problems.push('arc point 1');
      if (hook.placeArcPoint(10, 5) !== true) problems.push('arc point 2');
      if (hook.placeArcPoint(10, 0) !== true) problems.push('arc point 3');
    }
    if (!arcCallout0 || String(arcCallout0.textContent || '').trim() !== '5.590 mm') {
      problems.push('arc callout at 3 ' + (arcCallout0 && arcCallout0.textContent));
    }
    var arcThree = hook.state();
    if (!arcThree || arcThree.arcPoints !== 3 || arcThree.closed !== false) {
      problems.push('arc before confirm n ' + (arcThree && arcThree.arcPoints) + ' closed ' + (arcThree && arcThree.closed));
    }
    confirmSketch('arc');
    if (boxOf(document.getElementById('calloutRow0'))) problems.push('arc callout stayed after confirm');
    var drawnArc = hook.state();
    if (!drawnArc || drawnArc.profile !== 'arc' || drawnArc.closed !== true || drawnArc.arcPoints !== 3) {
      problems.push('arc profile ' + (drawnArc && drawnArc.profile) + ' closed ' + (drawnArc && drawnArc.closed) + ' n ' + (drawnArc && drawnArc.arcPoints));
    }
    extrude('arc');
    var arcExpectedVol = 0.5 * 31.25 * (2 * Math.PI - Math.acos(-0.6) + 0.8) * 10;
    assertSolid('arc', arcExpectedVol, function (bounds) {
      var min = bounds.min;
      var max = bounds.max;
      if (Math.abs(min[2]) > 0.05) problems.push('arc min z ' + min[2]);
      if (Math.abs(max[2] - 10) > 0.05) problems.push('arc max z ' + max[2]);
    });
  }
  if (!ensureEmpty('arc typed clear')) return JSON.stringify(problems);
  if (!startSketch()) return JSON.stringify(problems);
  pickPlane('xy', 'Arc typed top', [0, 0, 1], [1, 0, 0], [0, 1, 0]);
  if (openTools()) {
    var arcTypedTool = sheetBtn('Arc');
    if (!arcTypedTool) problems.push('Arc typed missing');
    else arcTypedTool.click();
    hook.placeArcPoint(0, 0);
    hook.placeArcPoint(5, 5);
    hook.placeArcPoint(10, 0);
    var arcTypedEl = document.getElementById('sketchArcR');
    if (!arcTypedEl || String(arcTypedEl.value).trim() !== '5') {
      problems.push('arc typed initial ' + (arcTypedEl && arcTypedEl.value));
    }
    if (arcTypedEl) {
      arcTypedEl.value = '10';
      arcTypedEl.dispatchEvent(new Event('input', { bubbles: true }));
    }
    var arcTypedVal0 = document.getElementById('calloutValue0');
    if (!arcTypedVal0 || String(arcTypedVal0.textContent || '').trim() !== '10 mm') {
      problems.push('arc typed callout ' + (arcTypedVal0 && arcTypedVal0.textContent));
    }
    confirmSketch('arc typed');
    extrude('arc typed');
    var semiExpectedVol = 0.5 * Math.PI * 100 * 10;
    assertSolid('arc typed', semiExpectedVol, function (bounds) {
      if (Math.abs(bounds.min[2]) > 0.05 || Math.abs(bounds.max[2] - 10) > 0.05) {
        problems.push('arc typed z ' + JSON.stringify(bounds));
      }
    });
  }
  if (!ensureEmpty('polygon clear')) return JSON.stringify(problems);
  if (!startSketch()) return JSON.stringify(problems);
  pickPlane('xy', 'Polygon top', [0, 0, 1], [1, 0, 0], [0, 1, 0]);
  var polyRibbon = document.querySelector('.tool-btn[data-tool="Polygon"]');
  if (!polyRibbon) problems.push('Polygon button missing');
  else if (polyRibbon.getAttribute('data-action') !== 'sketchPolygon') problems.push('Polygon data-action ' + polyRibbon.getAttribute('data-action'));
  var dimRibbon = document.querySelector('.tool-btn[data-tool="Dimension"]');
  if (!dimRibbon) problems.push('Dimension button missing');
  else if (dimRibbon.getAttribute('data-action') !== 'sketchDimension') problems.push('Dimension data-action ' + dimRibbon.getAttribute('data-action'));
  var offsetRibbon = document.querySelector('.tool-btn[data-tool="Offset"]');
  if (!offsetRibbon) problems.push('Offset button missing');
  else if (offsetRibbon.getAttribute('data-action')) problems.push('Offset data-action ' + offsetRibbon.getAttribute('data-action'));
  if (openTools()) {
    var offsetBtn = sheetBtn('Offset');
    if (offsetBtn) problems.push('Offset sheet visible during sketch');
    var polyTool = sheetBtn('Polygon');
    need(polyTool, 'Polygon');
    if (!polyTool) problems.push('Polygon missing');
    else polyTool.click();
    var polyNote = document.getElementById('sketchNote');
    if (!polyNote || polyNote.textContent !== 'Polygon') problems.push('polygon note ' + (polyNote && polyNote.textContent));
    var polyRect = document.getElementById('sketchRectRow');
    var polyCirc = document.getElementById('sketchCircRow');
    var polyRow = document.getElementById('sketchPolyRow');
    var polyDepth = document.getElementById('sketchDepthRow');
    if (!polyRect || polyRect.hidden !== true) problems.push('polygon shows length');
    if (!polyCirc || polyCirc.hidden !== true) problems.push('polygon shows circle diameter');
    if (!polyRow || polyRow.hidden !== false) problems.push('polygon row hidden');
    if (!polyDepth || polyDepth.hidden !== true) problems.push('polygon shows depth');
    var sidesEl = document.getElementById('sketchPolySides');
    var polyDEl = document.getElementById('sketchPolyD');
    need(sidesEl, 'Polygon sides');
    need(polyDEl, 'Polygon diameter');
    if (!sidesEl || String(sidesEl.value).trim() !== '6' || sidesEl.getAttribute('inputmode') !== 'decimal') {
      problems.push('polygon sides default ' + (sidesEl && sidesEl.value));
    }
    if (!polyDEl || String(polyDEl.value).trim() !== '10' || polyDEl.getAttribute('inputmode') !== 'decimal') {
      problems.push('polygon diameter default ' + (polyDEl && polyDEl.value));
    }
    var polyCallout0 = document.getElementById('calloutValue0');
    var polyCallout1 = document.getElementById('calloutValue1');
    if (!polyCallout0 || !boxOf(polyCallout0) || polyCallout0.getAttribute('data-dim') !== 'sketchPolyD' || String(polyCallout0.textContent || '').trim() !== '10 mm') {
      problems.push('polygon callout 0 ' + (polyCallout0 && polyCallout0.textContent));
    }
    if (!polyCallout1 || !boxOf(polyCallout1) || polyCallout1.getAttribute('data-dim') !== 'sketchPolySides' || String(polyCallout1.textContent || '').trim() !== '6') {
      problems.push('polygon callout 1 ' + (polyCallout1 && polyCallout1.textContent));
    }
    need(document.getElementById('calloutMinus0'), 'Polygon D minus');
    need(polyCallout0, 'Polygon D value');
    need(document.getElementById('calloutPlus0'), 'Polygon D plus');
    need(document.getElementById('calloutMinus1'), 'Polygon N minus');
    need(polyCallout1, 'Polygon N value');
    need(document.getElementById('calloutPlus1'), 'Polygon N plus');
    var polySheetBox = boxOf(document.getElementById('sketchSheet'));
    if (!polySheetBox) problems.push('polygon sheet hidden');
    var polyKeep = ['#exportBtn', '#statusUnits'];
    for (var pk = 0; pk < polyKeep.length; pk++) {
      var polyKeepBox = boxOf(document.querySelector(polyKeep[pk]));
      if (polyKeepBox && overlaps(polySheetBox, polyKeepBox)) problems.push('polygon covers ' + polyKeep[pk]);
    }
    if (openTools()) {
      var dimTool = sheetBtn('Dimension');
      need(dimTool, 'Dimension');
      if (!dimTool) {
        problems.push('Dimension sheet missing');
      } else {
        dimTool.click();
        if (!boxOf(document.getElementById('sketchSheet')) || !boxOf(polyCallout0)) {
          problems.push('Dimension hid sheet or callout');
        }
      }
    }
    var polyConfirm = document.getElementById('sketchConfirm');
    need(polyConfirm, 'Polygon confirm');
    if (sidesEl) {
      sidesEl.value = '2';
      sidesEl.dispatchEvent(new Event('input', { bubbles: true }));
    }
    if (!polyConfirm || polyConfirm.disabled !== true) {
      if (polyConfirm) polyConfirm.click();
      var badTwo = hook.state();
      if (badTwo && (badTwo.closed || badTwo.bodies !== 0)) problems.push('polygon N=2 accepted');
    }
    if (sidesEl && polyDEl) {
      sidesEl.value = '6';
      polyDEl.value = '';
      polyDEl.dispatchEvent(new Event('input', { bubbles: true }));
    }
    if (!polyConfirm || polyConfirm.disabled !== true) {
      if (polyConfirm) polyConfirm.click();
      var badBlank = hook.state();
      if (badBlank && (badBlank.closed || badBlank.bodies !== 0)) problems.push('polygon blank diameter accepted');
    }
    if (sidesEl && polyDEl) {
      sidesEl.value = '6';
      polyDEl.value = '10';
      sidesEl.dispatchEvent(new Event('input', { bubbles: true }));
      polyDEl.dispatchEvent(new Event('input', { bubbles: true }));
    }
    confirmSketch('polygon');
    if (boxOf(document.getElementById('calloutRow0')) || boxOf(document.getElementById('calloutRow1'))) {
      problems.push('polygon callout stayed after confirm');
    }
    var drawnPoly = hook.state();
    if (!drawnPoly || drawnPoly.profile !== 'polygon' || drawnPoly.closed !== true || drawnPoly.polygonSides !== 6) {
      problems.push('polygon profile ' + (drawnPoly && drawnPoly.profile) + ' closed ' + (drawnPoly && drawnPoly.closed) + ' sides ' + (drawnPoly && drawnPoly.polygonSides));
    }
    extrude('polygon');
    var hexExpectedVol = (3 * Math.sqrt(3) / 2) * 25 * 10;
    assertSolid('polygon', hexExpectedVol, function (bounds) {
      var min = bounds.min;
      var max = bounds.max;
      if (Math.abs(min[2]) > 0.05) problems.push('polygon min z ' + min[2]);
      if (Math.abs(max[2] - 10) > 0.05) problems.push('polygon max z ' + max[2]);
    });
  }
  return JSON.stringify(problems);
})()
"""


def portrait_origin_plane_problems(cdp: Cdp) -> list[str]:
    """390x844 empty doc: Top/Front/Right, rect and circle Blind 10 mm, then a line triangle."""
    raw, err = eval_expr(cdp, ORIGIN_PLANE_EXPR, timeout=300)
    if err or not isinstance(raw, str):
        return [f"origin plane {raw or err}"]
    try:
        found = json.loads(raw)
    except json.JSONDecodeError:
        return [f"origin plane {raw}"]
    if not isinstance(found, list):
        return [f"origin plane {raw}"]
    return [str(item) for item in found]


def portrait_sketch_problems(cdp: Cdp) -> list[str]:
    raw, err = eval_expr(cdp, SKETCH_PORTRAIT_EXPR, timeout=180)
    if err or not isinstance(raw, str):
        return [f"portrait sketch {raw or err}"]
    try:
        found = json.loads(raw)
    except json.JSONDecodeError:
        return [f"portrait sketch {raw}"]
    if not isinstance(found, list):
        return [f"portrait sketch {raw}"]
    problems = [str(item) for item in found]
    if problems:
        return problems
    return portrait_fit_problems(cdp)


COVERAGE_EXPR = r"""
(function(){
  var wantOpen = __WANT_OPEN__;
  var problems = [];
  var canvas = document.getElementById('canvas');
  var panel = document.getElementById('dimPanel');
  var cube = document.getElementById('viewCube');
  var menu = document.getElementById('createMenu');
  if (!canvas) return JSON.stringify({ratio:0, problems:['missing canvas']});
  var canvasBox = canvas.getBoundingClientRect();
  if (canvasBox.width < 1 || canvasBox.height < 1) problems.push('canvas empty');
  if (!panel || panel.hidden) problems.push('dimension panel hidden');
  var open = !!(panel && panel.classList.contains('is-open'));
  if (wantOpen && !open) problems.push('panel not open');
  if (!wantOpen && open) problems.push('panel opened without a tap');
  if (menu && !menu.hidden) problems.push('create menu open during coverage');
  function shown(el) {
    if (!el || el.hidden || (el.closest && el.closest('[hidden]'))) return null;
    var st = getComputedStyle(el);
    if (st.display === 'none' || st.visibility === 'hidden') return null;
    var r = el.getBoundingClientRect();
    if (r.width < 1 || r.height < 1) return null;
    return r;
  }
  var cubeBox = shown(cube);
  if (!cube || !cubeBox) problems.push('view cube missing');
  var selectors = ['.vp-bar', '#dimPanel', '#cameraShelf [data-action="view"][data-view="top"]', '#viewCube', '.statusbar'];
  var rects = [];
  var cubeOnCanvas = false;
  for (var s = 0; s < selectors.length; s++) {
    var el = document.querySelector(selectors[s]);
    var box = shown(el);
    if (!box) continue;
    var left = Math.max(canvasBox.left, box.left);
    var top = Math.max(canvasBox.top, box.top);
    var right = Math.min(canvasBox.right, box.right);
    var bottom = Math.min(canvasBox.bottom, box.bottom);
    if (right - left < 0.5 || bottom - top < 0.5) continue;
    if (selectors[s] === '#viewCube') cubeOnCanvas = true;
    rects.push({l:left, t:top, r:right, b:bottom});
  }
  if (cubeBox && !cubeOnCanvas) problems.push('view cube off the canvas');
  var gridW = Math.ceil(canvasBox.width);
  var gridH = Math.ceil(canvasBox.height);
  var area = gridW * gridH;
  var covered = 0;
  if (area > 0 && area <= 4000000) {
    var grid = new Uint8Array(area);
    for (var i = 0; i < rects.length; i++) {
      var rect = rects[i];
      var x0 = Math.max(0, Math.floor(rect.l - canvasBox.left));
      var y0 = Math.max(0, Math.floor(rect.t - canvasBox.top));
      var x1 = Math.min(gridW, Math.ceil(rect.r - canvasBox.left));
      var y1 = Math.min(gridH, Math.ceil(rect.b - canvasBox.top));
      for (var y = y0; y < y1; y++) {
        var row = y * gridW;
        for (var x = x0; x < x1; x++) {
          var idx = row + x;
          if (!grid[idx]) { grid[idx] = 1; covered++; }
        }
      }
    }
  } else if (area > 4000000) {
    problems.push('canvas grid ' + gridW + 'x' + gridH);
  }
  var ratio = area ? (area - covered) / area : 0;
  var need = wantOpen ? 0.5 : 0.7;
  if (ratio + 1e-9 < need) problems.push('uncovered ' + ratio.toFixed(3) + ' < ' + need.toFixed(2));
  return JSON.stringify({ratio:ratio, need:need, covered:covered, area:area, problems:problems});
})()
"""


def coverage_problems(cdp: Cdp, want_open: bool) -> list[str]:
    expression = COVERAGE_EXPR.replace("__WANT_OPEN__", "true" if want_open else "false")
    raw, err = eval_expr(cdp, expression)
    label = "open" if want_open else "collapsed"
    if err or not isinstance(raw, str):
        return [f"coverage {label} {raw or err}"]
    try:
        found = json.loads(raw)
    except json.JSONDecodeError:
        return [f"coverage {label} {raw}"]
    if not isinstance(found, dict):
        return [f"coverage {label} {raw}"]
    ratio = found.get("ratio")
    try:
        ratio_text = f"{float(ratio):.1%}"
    except (TypeError, ValueError):
        ratio_text = str(ratio)
    print(f"viewport uncovered {ratio_text} ({label})", flush=True)
    problems = found.get("problems") if isinstance(found.get("problems"), list) else [raw]
    return [f"coverage {label}: {item}" for item in problems]


FACE_AXES = (
    ("right", (1.0, 0.0, 0.0)),
    ("left", (-1.0, 0.0, 0.0)),
    ("top", (0.0, 1.0, 0.0)),
    ("bottom", (0.0, -1.0, 0.0)),
    ("front", (0.0, 0.0, 1.0)),
    ("back", (0.0, 0.0, -1.0)),
)


def _angle_deg(a: list[float] | tuple[float, ...], b: list[float] | tuple[float, ...]) -> float:
    dot = float(a[0]) * float(b[0]) + float(a[1]) * float(b[1]) + float(a[2]) * float(b[2])
    dot = max(-1.0, min(1.0, dot))
    return math.degrees(math.acos(dot))


NAV_OVERLAP_EXPR = r"""
(function(){
  function shown(el) {
    if (!el || el.hidden || (el.closest && el.closest('[hidden]'))) return null;
    var st = getComputedStyle(el);
    if (st.display === 'none' || st.visibility === 'hidden') return null;
    var r = el.getBoundingClientRect();
    if (r.width < 1 || r.height < 1) return null;
    return {left:r.left, top:r.top, right:r.right, bottom:r.bottom, width:r.width, height:r.height};
  }
  function hit(a, b) {
    return a.left < b.right - 0.5 && a.right > b.left + 0.5 && a.top < b.bottom - 0.5 && a.bottom > b.top + 0.5;
  }
  var problems = [];
  var cube = shown(document.getElementById('viewCube'));
  var names = ['.vp-bar', '#dimPanel', '.topbar'];
  var topHome = document.querySelector('#cameraShelf [data-action="view"][data-view="top"]');
  if (!topHome) problems.push('missing #cameraShelf [data-action="view"][data-view="top"]');
  else if (cube) {
    var topHomeBox = shown(topHome);
    if (topHomeBox && hit(cube, topHomeBox)) problems.push('overlaps #cameraShelf [data-action="view"][data-view="top"]');
  }
  if (!cube) problems.push('view cube missing');
  else {
    if (Math.abs(cube.width - 88) > 1 || Math.abs(cube.height - 88) > 1) {
      problems.push('cube size ' + cube.width.toFixed(1) + 'x' + cube.height.toFixed(1));
    }
    for (var i = 0; i < names.length; i++) {
      var box = shown(document.querySelector(names[i]));
      if (!box) {
        problems.push('missing ' + names[i]);
        continue;
      }
      if (hit(cube, box)) problems.push('overlaps ' + names[i]);
    }
  }
  var nav = window.__cadcamNavCube ? window.__cadcamNavCube() : null;
  if (!nav) problems.push('nav cube api missing');
  return JSON.stringify({problems:problems, nav:nav});
})()
"""


def read_nav(cdp: Cdp) -> tuple[dict[str, Any] | None, list[str]]:
    raw, err = eval_expr(cdp, NAV_OVERLAP_EXPR)
    if err or not isinstance(raw, str):
        return None, [f"nav cube {raw or err}"]
    try:
        found = json.loads(raw)
    except json.JSONDecodeError:
        return None, [f"nav cube {raw}"]
    if not isinstance(found, dict):
        return None, [f"nav cube {raw}"]
    problems = found.get("problems") if isinstance(found.get("problems"), list) else [raw]
    nav = found.get("nav")
    if not isinstance(nav, dict):
        return None, [str(item) for item in problems] or ["nav cube api missing"]
    return nav, [str(item) for item in problems]


def nav_zone(nav: dict[str, Any], name: str, kind: str) -> dict[str, Any] | None:
    zones = nav.get("zones")
    if not isinstance(zones, list):
        return None
    for zone in zones:
        if isinstance(zone, dict) and zone.get("name") == name and zone.get("kind") == kind:
            return zone
    return None


def nav_zone_problems(nav: dict[str, Any]) -> list[str]:
    problems: list[str] = []
    if nav.get("phone") is not True:
        problems.append(f"phone cube flag {nav.get('phone')!r}")
    try:
        size = float(nav.get("size"))
    except (TypeError, ValueError):
        size = 0.0
    if abs(size - 88.0) > 0.5:
        problems.append(f"cube css {size}")
    visible = nav.get("visible") if isinstance(nav.get("visible"), dict) else {}
    try:
        if abs(float(visible.get("w")) - 88.0) > 1.5 or abs(float(visible.get("h")) - 88.0) > 1.5:
            problems.append(f"visible cube {visible.get('w')}x{visible.get('h')}")
    except (TypeError, ValueError):
        problems.append(f"visible cube {visible!r}")
    zones = nav.get("zones") if isinstance(nav.get("zones"), list) else []
    faces = [z for z in zones if isinstance(z, dict) and z.get("kind") == "face"]
    corners = [z for z in zones if isinstance(z, dict) and z.get("kind") == "corner"]
    edges = [z for z in zones if isinstance(z, dict) and z.get("kind") == "edge"]
    if len(faces) != 6:
        problems.append(f"face zones {len(faces)}")
    if len(corners) != 8:
        problems.append(f"corner zones {len(corners)}")
    if edges:
        problems.append(f"phone edge zones {len(edges)}")
    for zone in faces + corners:
        try:
            w = float(zone.get("w"))
            h = float(zone.get("h"))
        except (TypeError, ValueError):
            problems.append(f"zone size {zone.get('name')}")
            continue
        if w < 44 or h < 44:
            problems.append(f"{zone.get('name')} hit {w}x{h}")
        if zone.get("extendsPast") is not True:
            problems.append(f"{zone.get('name')} hit stays inside the cube")
    return problems


def _sheet_open(cdp: Cdp) -> bool | None:
    raw, err = eval_expr(
        cdp,
        "(function(){var p=document.getElementById('dimPanel');"
        "return !!(p && !p.hidden && p.classList.contains('is-open'));})()",
    )
    if err:
        return None
    return raw is True


def _set_sheet(cdp: Cdp, want_open: bool) -> list[str]:
    current = _sheet_open(cdp)
    if current is want_open:
        return []
    toggled, err = eval_expr(cdp, CLICK_DIM_EXPR)
    if err or toggled != "clicked":
        return [f"dim toggle {toggled or err}"]
    deadline = time.time() + 2.0
    while time.time() < deadline:
        cdp.drain(0.05)
        if _sheet_open(cdp) is want_open:
            return []
        time.sleep(0.05)
    return [f"dim sheet did not become {'open' if want_open else 'collapsed'}"]


def _wait_snap(
    cdp: Cdp,
    axis: tuple[float, float, float],
    distance: float | None,
    label: str,
    *,
    check_snap_timing: bool = True,
) -> list[str]:
    # Home uses goView/animateSpherical (320 ms, may refit radius) — not cube face snap (250 ms).
    deadline = time.time() + (1.6 if not check_snap_timing else 1.2)
    last: dict[str, Any] | None = None
    while time.time() < deadline:
        cdp.drain(0.03)
        nav, problems = read_nav(cdp)
        if problems and nav is None:
            return [f"{label} {problems[0]}"]
        if not isinstance(nav, dict):
            time.sleep(0.03)
            continue
        last = nav
        if nav.get("animating") is True:
            time.sleep(0.02)
            continue
        direction = nav.get("direction")
        if not isinstance(direction, list) or len(direction) != 3:
            return [f"{label} direction {direction!r}"]
        angle = _angle_deg(direction, axis)
        try:
            dist_ok = True
            if distance is not None:
                dist_ok = abs(float(nav.get("distance")) - distance) <= 0.05
            elapsed = float(nav.get("lastSnapMs") or 0)
            budget = float(nav.get("lastSnapBudget") or 0)
        except (TypeError, ValueError):
            return [f"{label} distance {nav.get('distance')!r}"]
        if not check_snap_timing:
            if angle <= 1.0 and dist_ok:
                print(
                    f"nav {label}: {angle:.3f} deg, distance {float(nav.get('distance')):.2f}",
                    flush=True,
                )
                return []
            time.sleep(0.02)
            continue
        # The ease is 250 ms. Headless frames can land later; that lateness is not a longer ease.
        if angle <= 1.0 and dist_ok and 0 < budget <= 250.0 and elapsed < 500.0:
            print(
                f"nav {label}: {angle:.3f} deg, ease {budget:.0f} ms, frame {elapsed:.0f} ms, "
                f"distance {float(nav.get('distance')):.2f}",
                flush=True,
            )
            return []
        if budget > 250.0:
            return [f"{label} snap ease {budget:.0f} ms > 250"]
        if elapsed >= 500.0:
            return [f"{label} snap frame {elapsed:.0f} ms"]
        time.sleep(0.02)
    direction = (last or {}).get("direction")
    angle = _angle_deg(direction, axis) if isinstance(direction, list) and len(direction) == 3 else 999.0
    return [
        f"{label} off axis {angle:.2f} deg dir {direction!r} "
        f"animating {(last or {}).get('animating')!r} snap {(last or {}).get('lastSnapMs')!r}"
    ]


def _zone_point(zone: dict[str, Any]) -> tuple[float, float] | list[str]:
    try:
        return float(zone["x"]), float(zone["y"])
    except (KeyError, TypeError, ValueError):
        return [f"zone point {zone!r}"]


def _zone_clear(cdp: Cdp, zone: dict[str, Any], x: float, y: float) -> list[str]:
    raw, err = eval_expr(
        cdp,
        "(function(){"
        f"var el=document.elementFromPoint({x}, {y});"
        "if(!el || !el.closest('#viewport')) return 'outside';"
        "var block=el.closest('button, a, input, .vp-bar, .dim-panel, .topbar, .statusbar');"
        "return block ? (block.id || block.className || block.tagName) : 'ok';"
        "})()",
    )
    if err or raw != "ok":
        return [f"{zone.get('name')} tap lands on {raw or err}"]
    return []


def _tap_zone(cdp: Cdp, zone: dict[str, Any]) -> list[str]:
    point = _zone_point(zone)
    if isinstance(point, list):
        return point
    x, y = point
    blocked = _zone_clear(cdp, zone, x, y)
    if blocked:
        return blocked
    touch_tap(cdp, x, y)
    return []


def _double_tap_zone(cdp: Cdp, zone: dict[str, Any]) -> list[str]:
    """Two cube pointer-ups 80 ms apart on the page clock.

    A CDP round trip between taps can pass the 320 ms double-tap window, so
    the second tap becomes another face snap. Both ups stay in one evaluate.
    """
    point = _zone_point(zone)
    if isinstance(point, list):
        return point
    x, y = point
    blocked = _zone_clear(cdp, zone, x, y)
    if blocked:
        return blocked
    fired, err = eval_expr(
        cdp,
        "(function(){"
        "var vp=document.getElementById('viewport');"
        "if(!vp) return 'missing';"
        "function fire(type, px, py, buttons){"
        "vp.dispatchEvent(new PointerEvent(type, {bubbles:true, cancelable:true,"
        "clientX:px, clientY:py, pointerId:9, pointerType:'touch', button:0,"
        "buttons:buttons, isPrimary:true}));"
        "}"
        f"fire('pointerdown', {x}, {y}, 1);"
        f"fire('pointerup', {x}, {y}, 0);"
        "var t0=performance.now();"
        "while(performance.now()-t0<80){}"
        f"fire('pointerdown', {x}, {y}, 1);"
        f"fire('pointerup', {x}, {y}, 0);"
        "return 'double';"
        "})()",
    )
    if err or fired != "double":
        return [f"{zone.get('name')} double-tap {fired or err}"]
    return []


def nav_cube_problems(cdp: Cdp) -> list[str]:
    """390x844. Face snaps land on-axis, corner and home snaps match, clear-view holds."""
    problems: list[str] = []
    for want_open in (False, True):
        sheet_problems = _set_sheet(cdp, want_open)
        if sheet_problems:
            return [f"nav sheet {'open' if want_open else 'collapsed'}", *sheet_problems]
        cdp.drain(0.1)
        nav, overlap = read_nav(cdp)
        label = "open" if want_open else "collapsed"
        if overlap:
            problems.append(f"nav overlap {label}")
            problems.extend(overlap)
            return problems
        if not isinstance(nav, dict):
            return ["nav cube missing"]
        if not want_open:
            zone_problems = nav_zone_problems(nav)
            if zone_problems:
                return zone_problems
        covered = coverage_problems(cdp, want_open)
        if covered:
            return covered
    home_sheet = _set_sheet(cdp, False)
    if home_sheet:
        return home_sheet
    time.sleep(0.4)
    nav, overlap = read_nav(cdp)
    if overlap or not isinstance(nav, dict):
        return overlap or ["nav cube missing before snaps"]
    try:
        distance = float(nav.get("distance"))
    except (TypeError, ValueError):
        return [f"nav distance {nav.get('distance')!r}"]
    if not math.isfinite(distance) or distance < 1e-3:
        return [f"nav distance {distance}"]
    for name, axis in FACE_AXES:
        time.sleep(0.4)
        fresh, fresh_problems = read_nav(cdp)
        if fresh_problems or not isinstance(fresh, dict):
            return [f"{name} zone", *(fresh_problems or ["missing"])]
        zone = nav_zone(fresh, name, "face")
        if zone is None:
            return [f"{name} zone missing"]
        tapped = _tap_zone(cdp, zone)
        if tapped:
            return tapped
        snapped = _wait_snap(cdp, axis, distance, name)
        if snapped:
            return snapped
    time.sleep(0.4)
    fresh, fresh_problems = read_nav(cdp)
    if fresh_problems or not isinstance(fresh, dict):
        return ["corner zone", *(fresh_problems or ["missing"])]
    corner = nav_zone(fresh, "trf", "corner")
    front_zone = nav_zone(fresh, "front", "face")
    if not isinstance(front_zone, dict):
        return ["front swipe zone missing"]
    tapped_front = _tap_zone(cdp, front_zone)
    if tapped_front:
        return tapped_front
    snapped_front = _wait_snap(cdp, (0.0, 0.0, 1.0), distance, "front-before-swipe")
    if snapped_front:
        return snapped_front
    swiped_left, swipe_err = eval_expr(
        cdp,
        "(function(){"
        "var el=document.getElementById('viewCube');"
        "if(!el) return 'missing';"
        "var r=el.getBoundingClientRect();"
        "var cx=r.left+r.width/2, cy=r.top+r.height/2;"
        "function fire(type, x, y, buttons){"
        "el.dispatchEvent(new PointerEvent(type, {bubbles:true, cancelable:true, clientX:x, clientY:y,"
        "pointerId:11, pointerType:'touch', button:0, buttons:buttons, isPrimary:true, width:24, height:24}));"
        "}"
        "fire('pointerdown', cx, cy, 1);"
        "fire('pointermove', cx-20, cy, 1);"
        "fire('pointermove', cx-40, cy, 1);"
        "fire('pointerup', cx-40, cy, 0);"
        "return 'swiped';"
        "})()",
    )
    if swipe_err or swiped_left != "swiped":
        return [f"swipe left {swiped_left or swipe_err}"]
    snapped_right = _wait_snap(cdp, (1.0, 0.0, 0.0), distance, "swipe-left-right")
    if snapped_right:
        return snapped_right
    swiped_nav, swiped_problems = read_nav(cdp)
    if swiped_problems or not isinstance(swiped_nav, dict):
        return ["swipe left read", *(swiped_problems or ["missing"])]
    if swiped_nav.get("face") != "right" or swiped_nav.get("snapFace") != "right":
        return [
            f"swipe left face {swiped_nav.get('face')!r} snapFace {swiped_nav.get('snapFace')!r} want 'right'"
        ]
    time.sleep(0.4)
    fresh, fresh_problems = read_nav(cdp)
    if fresh_problems or not isinstance(fresh, dict):
        return ["corner zone after swipe", *(fresh_problems or ["missing"])]
    corner = nav_zone(fresh, "trf", "corner")
    if corner is None:
        zones = fresh.get("zones") if isinstance(fresh.get("zones"), list) else []
        corner = next((z for z in zones if isinstance(z, dict) and z.get("kind") == "corner"), None)
    if not isinstance(corner, dict):
        return ["corner zone missing"]
    corner_dir = corner.get("dir")
    if not isinstance(corner_dir, list) or len(corner_dir) != 3:
        return [f"corner dir {corner_dir!r}"]
    tapped = _tap_zone(cdp, corner)
    if tapped:
        return tapped
    corner_axis = (float(corner_dir[0]), float(corner_dir[1]), float(corner_dir[2]))
    snapped = _wait_snap(cdp, corner_axis, distance, str(corner.get("name") or "corner"))
    if snapped:
        return snapped
    time.sleep(0.4)
    fresh, fresh_problems = read_nav(cdp)
    if fresh_problems or not isinstance(fresh, dict):
        return ["home zone", *(fresh_problems or ["missing"])]
    home_zone = nav_zone(fresh, "front", "face") or corner
    if not isinstance(home_zone, dict):
        return ["home tap zone missing"]
    home = fresh.get("home")
    if not isinstance(home, list) or len(home) != 3:
        return [f"home dir {home!r}"]
    doubled = _double_tap_zone(cdp, home_zone)
    if doubled:
        return doubled
    # Double-tap Home: goView/animateSpherical refits selection (SC3); not cube snap timing/distance.
    snapped = _wait_snap(
        cdp,
        (float(home[0]), float(home[1]), float(home[2])),
        None,
        "home",
        check_snap_timing=False,
    )
    if snapped:
        return snapped
    time.sleep(0.4)
    fresh, fresh_problems = read_nav(cdp)
    if fresh_problems or not isinstance(fresh, dict):
        return ["drag", *(fresh_problems or ["missing"])]
    before = fresh.get("direction")
    drag_zone = nav_zone(fresh, "front", "face")
    if not isinstance(before, list) or not isinstance(drag_zone, dict):
        return ["drag zone missing"]
    x = float(drag_zone["x"])
    y = float(drag_zone["y"])
    # On-cube: past tap slop (8) but under swipe (24) must not commit a face snap (SC1).
    dragged, drag_err = eval_expr(
        cdp,
        "(function(){"
        "var vp=document.getElementById('viewport');"
        "if(!vp) return 'missing';"
        "function fire(type, x, y, buttons){"
        "vp.dispatchEvent(new PointerEvent(type, {bubbles:true, cancelable:true, clientX:x, clientY:y,"
        "pointerId:7, pointerType:'touch', button:0, buttons:buttons, isPrimary:true}));"
        "}"
        f"fire('pointerdown', {x}, {y}, 1);"
        f"fire('pointermove', {x + 16}, {y}, 1);"
        f"fire('pointerup', {x + 16}, {y}, 0);"
        "return 'dragged';"
        "})()",
    )
    if drag_err or dragged != "dragged":
        return [f"drag {dragged or drag_err}"]
    cdp.drain(0.2)
    after_nav, after_problems = read_nav(cdp)
    if after_problems or not isinstance(after_nav, dict):
        return ["drag read", *(after_problems or ["missing"])]
    after = after_nav.get("direction")
    if not isinstance(after, list) or _angle_deg(before, after) > 0.5:
        return [f"drag snapped the view {before!r} -> {after!r}"]
    if after_nav.get("animating") is True:
        return ["drag started a snap"]
    return []


STAMP_EXPR = r"""
(function(){
  var problems = [];
  var el = document.getElementById('buildStamp');
  if (!el) return JSON.stringify({stamp:'', problems:['missing stamp']});
  var text = (el.textContent || '').replace(/\s+/g, '');
  var st = getComputedStyle(el);
  var box = el.getBoundingClientRect();
  if (!text) problems.push('empty stamp');
  if (st.display === 'none' || st.visibility === 'hidden' || box.width < 1 || box.height < 1) problems.push('stamp hidden');
  if (box.right <= 0 || box.bottom <= 0 || box.left >= window.innerWidth || box.top >= window.innerHeight) {
    problems.push('stamp offscreen');
  }
  var scripts = document.querySelectorAll('script[src]');
  if (!scripts.length) problems.push('no script src');
  for (var i = 0; i < scripts.length; i++) {
    try {
      var srcUrl = new URL(scripts[i].src, location.href);
      if (srcUrl.searchParams.get('v') !== text) problems.push('script v ' + scripts[i].getAttribute('src'));
    } catch (err) {
      problems.push('script url');
    }
  }
  var names = ['init.single.js', 'occt-gate.mjs', 'occt-primitives.mjs', 'occt-ops.mjs', 'project-file.mjs', 'undo.mjs', 'selection.mjs', 'viewport-selection.mjs', 'assemblies.mjs', 'view-cube.mjs', 'three-finger.mjs', 'field-nudge.mjs', 'phone-select.mjs'];
  var found = {};
  var entries = performance.getEntriesByType('resource');
  for (var e = 0; e < entries.length; e++) {
    var url = entries[e].name || '';
    for (var n = 0; n < names.length; n++) {
      if (url.indexOf('/' + names[n]) !== -1) found[names[n]] = url;
    }
  }
  for (var m = 0; m < names.length; m++) {
    if (!found[names[m]]) {
      problems.push('missing module ' + names[m]);
      continue;
    }
    try {
      var modUrl = new URL(found[names[m]], location.href);
      if (modUrl.searchParams.get('v') !== text) problems.push('module v ' + names[m]);
    } catch (err2) {
      problems.push('module url ' + names[m]);
    }
  }
  return JSON.stringify({stamp:text, problems:problems});
})()
"""


def stamp_problems(cdp: Cdp) -> list[str]:
    raw, err = eval_expr(cdp, STAMP_EXPR)
    if err or not isinstance(raw, str):
        return [f"build stamp {raw or err}"]
    try:
        found = json.loads(raw)
    except json.JSONDecodeError:
        return [f"build stamp {raw}"]
    if not isinstance(found, dict):
        return [f"build stamp {raw}"]
    stamp = str(found.get("stamp") or "")
    problems = found.get("problems") if isinstance(found.get("problems"), list) else [raw]
    if problems:
        return [f"build stamp: {item}" for item in problems]
    print(f"build stamp {stamp} matches script urls", flush=True)
    return []


CLICK_DIM_EXPR = (
    "(function(){var b=document.getElementById('dimToggle');"
    "if(!b)return 'missing';b.click();return 'clicked';})()"
)


PORTRAIT_FIT_EXPR = r"""
(function(){
  var iw = window.innerWidth;
  var ih = window.innerHeight;
  var problems = [];
  if (document.documentElement.scrollWidth > iw + 0.5) {
    problems.push('page scrollWidth ' + document.documentElement.scrollWidth + ' > ' + iw);
  }
  function shown(el) {
    if (!el || el.closest('[hidden]')) return null;
    var st = getComputedStyle(el);
    if (st.display === 'none' || st.visibility === 'hidden') return null;
    var r = el.getBoundingClientRect();
    if (r.width < 1 || r.height < 1) return null;
    if (r.bottom <= 0 || r.top >= ih || r.right <= 0 || r.left >= iw) return null;
    return r;
  }
  var nodes = document.querySelectorAll('button, #statusHint, .statusbar');
  for (var i = 0; i < nodes.length; i++) {
    var el = nodes[i];
    var r = shown(el);
    if (!r) continue;
    if (el.closest && el.closest('[data-hscroll]')) continue;
    if (r.right > iw + 0.5) {
      var label = (el.id || el.getAttribute('aria-label') || el.getAttribute('data-tool') || el.className || '')
        .toString().replace(/\s+/g, ' ').trim().slice(0, 48);
      problems.push(label + ' right ' + r.right.toFixed(1));
    }
  }
  var hosts = document.querySelectorAll('#dimPanel, #touchToolbar, .vp-bar');
  for (var j = 0; j < hosts.length; j++) {
    var host = hosts[j];
    if (!shown(host)) continue;
    if (host.hasAttribute('data-hscroll')) continue;
    if (host.scrollWidth > host.clientWidth + 1) {
      problems.push((host.id || 'host') + ' scrollWidth ' + host.scrollWidth + ' > ' + host.clientWidth);
    }
  }
  return JSON.stringify(problems);
})()
"""


def portrait_fit_problems(cdp: Cdp) -> list[str]:
    raw, err = eval_expr(cdp, PORTRAIT_FIT_EXPR)
    if err or not isinstance(raw, str):
        return [f"portrait fit {raw or err}"]
    try:
        found = json.loads(raw)
    except json.JSONDecodeError:
        return [f"portrait fit {raw}"]
    if not isinstance(found, list):
        return [f"portrait fit {raw}"]
    found_text = [str(item) for item in found]
    found_text.extend(toolbar_row_problems(cdp))
    found_text.extend(chrome_row_problems(cdp))
    return found_text


TOOLBAR_ROW_EXPR = r"""
(function(){
  var problems = [];
  var iw = window.innerWidth;
  if (document.documentElement.scrollWidth > iw + 0.5) {
    problems.push('page scrollWidth ' + document.documentElement.scrollWidth + ' > ' + iw);
  }
  var bar = document.querySelector('.vp-bar');
  if (!bar) return JSON.stringify(['missing toolbar']);
  if (!bar.hasAttribute('data-hscroll')) problems.push('toolbar missing data-hscroll');
  var st = getComputedStyle(bar);
  if (st.flexWrap !== 'nowrap') problems.push('toolbar wrap ' + st.flexWrap);
  if (st.overflowX !== 'auto' && st.overflowX !== 'scroll') problems.push('toolbar overflow-x ' + st.overflowX);
  if (st.scrollSnapType.indexOf('x') < 0 || st.scrollSnapType.indexOf('mandatory') < 0) {
    problems.push('toolbar snap ' + st.scrollSnapType);
  }
  var buttons = bar.querySelectorAll('button');
  if (!buttons.length) problems.push('toolbar has no buttons');
  var measureBtn = bar.querySelector('[data-action="measure"]');
  if (!measureBtn) problems.push('missing Measure');
  var top = null;
  var btnH = 0;
  for (var i = 0; i < buttons.length; i++) {
    var b = buttons[i];
    var r = b.getBoundingClientRect();
    var bst = getComputedStyle(b);
    if (r.width + 0.5 < 44 || r.height + 0.5 < 44) {
      problems.push('toolbar button ' + r.width.toFixed(1) + 'x' + r.height.toFixed(1));
    }
    if (bst.flexGrow !== '0' || bst.flexShrink !== '0') {
      problems.push('toolbar button flex ' + bst.flexGrow + ' ' + bst.flexShrink);
    }
    if (top === null) {
      top = r.top;
      btnH = r.height;
    } else if (Math.abs(r.top - top) > 0.5) {
      problems.push('toolbar button top ' + r.top.toFixed(1) + ' vs ' + top.toFixed(1));
    }
  }
  var br = bar.getBoundingClientRect();
  var pad = parseFloat(st.paddingTop) + parseFloat(st.paddingBottom);
  var border = parseFloat(st.borderTopWidth) + parseFloat(st.borderBottomWidth);
  var limit = btnH + pad + border + 0.5;
  if (br.height > limit) problems.push('toolbar height ' + br.height.toFixed(1) + ' > ' + limit.toFixed(1));
  return JSON.stringify(problems);
})()
"""


def toolbar_row_problems(cdp: Cdp) -> list[str]:
    raw, err = eval_expr(cdp, TOOLBAR_ROW_EXPR)
    if err or not isinstance(raw, str):
        return [f"toolbar row {raw or err}"]
    try:
        found = json.loads(raw)
    except json.JSONDecodeError:
        return [f"toolbar row {raw}"]
    if not isinstance(found, list):
        return [f"toolbar row {raw}"]
    return [str(item) for item in found]


CHROME_ROW_EXPR = r"""
(function(){
  var problems = [];
  var tree = document.querySelector('[data-drawer="browser"]');
  var info = document.querySelector('[data-drawer="inspector"]');
  var name = document.getElementById('docName');
  if (!tree || !info || !name) return JSON.stringify(['missing tree, info, or part name']);
  function box(el) { return el.getBoundingClientRect(); }
  var tr = box(tree);
  var ir = box(info);
  var nr = box(name);
  if (tr.width + 0.5 < 44 || tr.height + 0.5 < 44) problems.push('Tree ' + tr.width.toFixed(1) + 'x' + tr.height.toFixed(1));
  if (ir.width + 0.5 < 44 || ir.height + 0.5 < 44) problems.push('Info ' + ir.width.toFixed(1) + 'x' + ir.height.toFixed(1));
  var shelves = document.querySelector('.topbar-shelves');
  var browser = document.getElementById('browser');
  if (!shelves || shelves.firstElementChild !== tree) problems.push('Tree is not first in topbar-shelves');
  if (tree.closest('.topbar')) problems.push('Tree still in topbar');
  if (!(tr.top > ir.top + 0.5)) problems.push('Info top ' + ir.top.toFixed(1) + ' Tree top ' + tr.top.toFixed(1));
  if (!browser) {
    problems.push('missing browser drawer');
  } else if (!browser.classList.contains('open')) {
    tree.click();
    if (!browser.classList.contains('open') || tree.getAttribute('aria-expanded') !== 'true') {
      problems.push('Tree did not open browser');
    }
    tree.click();
    if (browser.classList.contains('open') || tree.getAttribute('aria-expanded') !== 'false') {
      problems.push('Tree did not close browser');
    }
  }
  if (ir.right > nr.left + 0.5) problems.push('Info is not left of the part name');
  var buttons = document.querySelectorAll('.topbar button');
  for (var i = 0; i < buttons.length; i++) {
    var b = buttons[i];
    if (b.closest('[hidden]')) continue;
    var st = getComputedStyle(b);
    if (st.display === 'none' || st.visibility === 'hidden') continue;
    var r = b.getBoundingClientRect();
    if (r.width < 1 || r.height < 1) continue;
    if (r.width + 0.5 < 44 || r.height + 0.5 < 44) {
      var label = b.getAttribute('aria-label') || b.getAttribute('data-tool') || b.textContent || '';
      problems.push(String(label).trim().slice(0, 24) + ' ' + r.width.toFixed(1) + 'x' + r.height.toFixed(1));
    }
  }
  var nrBox = box(name);
  if (!(nrBox.width > 0) || !(nrBox.height > 0)) {
    problems.push('part name box ' + nrBox.width.toFixed(1) + 'x' + nrBox.height.toFixed(1));
  }
  if (nrBox.right <= 0 || nrBox.left >= window.innerWidth || nrBox.bottom <= 0 || nrBox.top >= window.innerHeight) {
    problems.push('part name offscreen ' + nrBox.left.toFixed(1) + ',' + nrBox.top.toFixed(1));
  }
  var ns = getComputedStyle(name);
  var nameMin = parseFloat(ns.minWidth);
  if (!(nameMin >= 96)) problems.push('part name min-width ' + ns.minWidth);
  if (window.innerWidth <= 820 && !(parseFloat(ns.flexGrow) >= 1)) problems.push('part name flex ' + ns.flexGrow);
  if (ns.overflowX !== 'hidden' && ns.overflowX !== 'clip' && ns.overflow !== 'hidden' && ns.overflow !== 'clip') {
    problems.push('part name overflow ' + ns.overflowX);
  }
  if (ns.textOverflow !== 'ellipsis') problems.push('part name text-overflow ' + ns.textOverflow);
  var savedName = name.value;
  if (savedName !== 'Part 1') problems.push('part name value ' + savedName);
  if (name.scrollWidth > name.clientWidth + 1) problems.push('part name clipped ' + name.scrollWidth + '>' + name.clientWidth);
  name.value = 'MMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMM';
  if (name.scrollWidth <= name.clientWidth + 1) problems.push('part name did not truncate');
  name.value = savedName;
  var meta = document.querySelector('meta[name="viewport"]');
  if (!meta || String(meta.content).indexOf('interactive-widget=resizes-content') < 0) {
    problems.push('missing interactive-widget');
  }
  return JSON.stringify(problems);
})()
"""


def chrome_row_problems(cdp: Cdp) -> list[str]:
    raw, err = eval_expr(cdp, CHROME_ROW_EXPR)
    if err or not isinstance(raw, str):
        return [f"chrome row {raw or err}"]
    try:
        found = json.loads(raw)
    except json.JSONDecodeError:
        return [f"chrome row {raw}"]
    if not isinstance(found, list):
        return [f"chrome row {raw}"]
    return [str(item) for item in found]


def read_home_aim(cdp: Cdp) -> tuple[dict[str, Any] | None, str]:
    raw, err = eval_expr(
        cdp,
        "(function(){var a=window.__cadcamHomeAim&&window.__cadcamHomeAim();return a?JSON.stringify(a):'';})()",
    )
    if err or not isinstance(raw, str) or not raw.startswith("{"):
        return None, str(raw or err or "no home aim")
    try:
        aim = json.loads(raw)
    except json.JSONDecodeError:
        return None, raw
    if not isinstance(aim, dict):
        return None, raw
    return aim, ""


def home_target_ready(aim: dict[str, Any], selected: bool) -> bool:
    target = aim.get("target")
    if not isinstance(target, list) or len(target) != 3:
        return False
    # SC: Home centers selected model else 0,0,0. Only require origin when cleared.
    if not selected and any(abs(float(v)) > 1e-6 for v in target):
        return False
    count = int(aim.get("selectionCount") or 0)
    sel_ok = count > 0 if selected else count == 0
    return aim.get("allInside") is True and int(aim.get("corners") or 0) == 8 and sel_ok


def wait_home_aim(cdp: Cdp, label: str, selected: bool) -> list[str]:
    clicked, err = eval_expr(
        cdp,
        "(function(){var s=document.getElementById('cameraShelf');if(!s)return 'missing';var wasHidden=s.hidden===true;var t=document.getElementById('cameraShelfBtn')||document.querySelector('[data-action=\"cameraShelf\"]');if(wasHidden){if(!t)return 'missing';t.click();}if(s.hidden)return 'missing';var b=s.querySelector('[data-action=\"view\"][data-view=\"top\"]');if(!b)return 'missing';b.click();if(wasHidden&&t&&!s.hidden)t.click();return 'ok';})()",
    )
    if clicked != "ok":
        return [f"{label} home click {clicked or err}"]
    last: dict[str, Any] | None = None
    deadline = time.time() + 2.5
    while time.time() < deadline:
        aim, _why = read_home_aim(cdp)
        if aim is None:
            time.sleep(0.1)
            continue
        last = aim
        if home_target_ready(aim, selected):
            return []
        time.sleep(0.1)
    return [f"{label} home {json.dumps(last)}"]


def home_aim_round(cdp: Cdp, label: str) -> list[str]:
    problems = wait_home_aim(cdp, label + " selected", True)
    if problems:
        return problems
    raw, err = eval_expr(
        cdp,
        "(function(){var b=document.querySelector('[data-action=\"select\"][data-mode=\"vertex\"]');"
        "if(!b)return 'missing';b.click();var a=window.__cadcamHomeAim?window.__cadcamHomeAim():{};"
        "return String(a.selectionCount);})()",
    )
    if str(raw) != "0":
        return [f"{label} vertex selection {raw or err}"]
    return wait_home_aim(cdp, label + " clear", False)


def set_desktop(cdp: Cdp) -> None:
    cdp.call(
        "Emulation.setDeviceMetricsOverride",
        {
            "width": 1280,
            "height": 800,
            "deviceScaleFactor": 1,
            "mobile": False,
        },
    )


SHEET_HIT_EXPR = r"""
(function(){
  var vp = document.getElementById('viewport');
  var panel = document.getElementById('dimPanel');
  if (!window.__holeTapProbe && vp) {
    window.__holeTapProbe = [];
    function note(ev) {
      var list = window.__holeTapProbe;
      if (!list || list.length > 30) return;
      var t = ev.target;
      list.push(ev.type + ' btn=' + ev.button + ' pt=' + ev.pointerType + ' ' + Math.round(ev.clientX) + ',' + Math.round(ev.clientY) + ' ' + (t ? (t.id || t.tagName) : ''));
    }
    vp.addEventListener('pointerdown', note, true);
    vp.addEventListener('pointerup', note, true);
  }
  if (window.__holeTapProbe) window.__holeTapProbe.length = 0;
  if (panel) {
    panel.style.visibility = 'hidden';
    panel.style.pointerEvents = 'none';
  }
  var face = (window.__cadcamExportState || {}).facePick;
  if (!face || !vp) return JSON.stringify({pts:[]});
  var pts = [];
  function add(x, y) {
    x = Math.round(Number(x));
    y = Math.round(Number(y));
    if (!isFinite(x) || !isFinite(y)) return;
    var el = document.elementFromPoint(x, y);
    var blocked = !!(el && el.closest && el.closest('button, a, input, textarea, .vp-bar, .sheet, .hud, .dim-panel, .touch-toolbar, .vc-home'));
    var onView = !!(el && (el.id === 'canvas' || el.id === 'viewport' || (vp.contains(el) && !blocked)));
    pts.push({x:x, y:y, onView:onView, id: el ? (el.id || el.tagName) : 'none'});
  }
  add(face.x, face.y);
  add(Number(face.x) - 64, face.y);
  add(Number(face.x) + 64, face.y);
  add(face.x, Number(face.y) - 28);
  return JSON.stringify({pts:pts, faceId:face.id, z:face.z});
})()
"""


RESTORE_SHEET_EXPR = r"""
(function(){
  var panel = document.getElementById('dimPanel');
  if (panel) {
    panel.style.visibility = '';
    panel.style.pointerEvents = '';
  }
  return 'restored';
})()
"""


def synth_tap_expr(x: float, y: float) -> str:
    return (
        "(function(){"
        "var vp=document.getElementById('viewport');"
        "if(!vp) return 'missing';"
        f"var x={float(x):.2f}, y={float(y):.2f};"
        "var down={bubbles:true,cancelable:true,clientX:x,clientY:y,button:0,buttons:1,pointerId:1,pointerType:'touch',isPrimary:true};"
        "vp.dispatchEvent(new PointerEvent('pointerdown', down));"
        "var up={bubbles:true,cancelable:true,clientX:x,clientY:y,button:0,buttons:0,pointerId:1,pointerType:'touch',isPrimary:true};"
        "vp.dispatchEvent(new PointerEvent('pointerup', up));"
        "return 'sent';"
        "})()"
    )


INSPECTOR_CLOSED_EXPR = r"""
(function(){
  var inspector = document.getElementById('inspector');
  var problems = [];
  if (!inspector) return JSON.stringify(['missing inspector']);
  if (inspector.classList.contains('open')) problems.push('inspector open');
  if (!inspector.hasAttribute('inert')) problems.push('missing inert');
  var st = getComputedStyle(inspector);
  if (st.visibility !== 'hidden') problems.push('visibility ' + st.visibility);
  var buttons = inspector.querySelectorAll('button, input, a, select, textarea');
  if (!buttons.length) problems.push('no inspector controls');
  var iw = window.innerWidth;
  var ih = window.innerHeight;
  for (var i = 0; i < buttons.length; i++) {
    var b = buttons[i];
    var r = b.getBoundingClientRect();
    var bst = getComputedStyle(b);
    var notRendered = bst.visibility === 'hidden' || bst.display === 'none' || (r.width < 0.5 && r.height < 0.5);
    if (!notRendered) {
      var name = b.id || b.getAttribute('data-action') || String(i);
      problems.push('rendered ' + name + ' ' + r.width.toFixed(1) + 'x' + r.height.toFixed(1));
    }
    var cx = Math.min(iw - 2, Math.max(2, r.left + Math.max(r.width, 0) / 2));
    var cy = Math.min(ih - 2, Math.max(2, r.top + Math.min(Math.max(r.height, 0) / 2, 24)));
    var hit = document.elementFromPoint(cx, cy);
    if (hit && inspector.contains(hit)) problems.push('tap ' + (b.id || b.getAttribute('data-action') || i));
    try { b.focus(); } catch (err) {}
    if (document.activeElement === b) problems.push('focused ' + (b.id || b.getAttribute('data-action') || i));
  }
  for (var y = 4; y < ih; y += 36) {
    var edge = document.elementFromPoint(iw - 2, y);
    if (edge && inspector.contains(edge)) problems.push('edge ' + y);
  }
  if (document.activeElement && document.activeElement.blur) document.activeElement.blur();
  return JSON.stringify(problems);
})()
"""


def closed_inspector_problems(cdp: Cdp) -> list[str]:
    raw, err = eval_expr(cdp, INSPECTOR_CLOSED_EXPR)
    if err or not isinstance(raw, str):
        return [f"closed inspector {raw or err}"]
    try:
        found = json.loads(raw)
    except json.JSONDecodeError:
        return [f"closed inspector {raw}"]
    if not isinstance(found, list):
        return [f"closed inspector {raw}"]
    return [str(item) for item in found]


def num_text(value: float) -> str:
    text = f"{float(value):.6f}".rstrip("0").rstrip(".")
    return text or "0"


def reveal_expr(selector: str) -> str:
    return (
        "(function(){"
        f"var el=document.querySelector('{selector}');"
        "if(!el) return 'missing';"
        "el.scrollIntoView({block:'center',inline:'nearest'});"
        "return 'shown';"
        "})()"
    )


def field_text(cdp: Cdp, field: str) -> tuple[str, str]:
    return eval_expr(
        cdp,
        "(function(){"
        f"var el=document.getElementById('{field}');"
        "return el?String(el.value):'missing';"
        "})()",
    )


def wait_hole_state(
    cdp: Cdp,
    origin: str,
    ready_fn,
    timeout: float,
    label: str,
) -> tuple[dict[str, Any] | None, list[str]]:
    deadline = time.time() + timeout
    last: dict[str, Any] | None = None
    while time.time() < deadline:
        cdp.drain(0.3)
        problems = site_problems(cdp.events, origin, cdp.urls)
        payload = eval_state(cdp)
        problems.extend(smoke_notes(payload))
        if problems:
            return last, problems
        state = (payload or {}).get("state") if payload else None
        if isinstance(state, dict):
            last = state
            if state.get("lastError"):
                return state, [str(state.get("lastError"))]
            if ready_fn(state):
                return state, []
        time.sleep(0.15)
    return last, [f"{label} timed out", json.dumps(last)]


def portrait_layout_ok(state: dict[str, Any], expanded: bool) -> list[str]:
    layout = state.get("layout") or {}
    problems: list[str] = []
    if layout.get("portrait") is not True:
        problems.append(f"portrait layout flag {layout.get('portrait')!r}")
    if layout.get("sheet") is not True:
        problems.append("portrait sheet missing")
    if layout.get("homeOverlap") is True:
        problems.append("Home overlaps the dimension sheet")
    view_clear = float(layout.get("viewClearPx") or 0)
    if view_clear < 80:
        problems.append(f"view covered, clear {view_clear}px")
    if expanded and layout.get("sheetOpen") is not True:
        problems.append("sheet not expanded")
    if not expanded and layout.get("sheetOpen") is True:
        problems.append("sheet started expanded")
    home = layout.get("home") or {}
    panel = layout.get("panel") or {}
    if home and panel and float(panel.get("y") or 0) < float(home.get("bottom") or 0) + 4:
        if layout.get("homeOverlap") is True:
            problems.append("sheet top meets Home")
    if expanded and panel:
        panel_h = float(panel.get("h") or 0)
        viewport_h = float(layout.get("viewportH") or 0)
        if viewport_h <= 0:
            problems.append("viewport height missing")
        elif panel_h > viewport_h * 0.4 + 1.5:
            problems.append(f"sheet {panel_h:.1f}px over 40% of {viewport_h:.1f}px")
    return problems


def _is_default_box(state: dict[str, Any] | None) -> bool:
    """True when the page already holds the Create > Box 20 mm solid."""
    if not isinstance(state, dict):
        return False
    params = state.get("primitiveParams") or {}
    if not isinstance(params, dict):
        return False
    try:
        sx = float(params.get("sx"))
        sy = float(params.get("sy"))
        sz = float(params.get("sz"))
    except (TypeError, ValueError):
        return False
    return (
        state.get("primitiveKind") == "box"
        and abs(sx - 20.0) < 1e-6
        and abs(sy - 20.0) < 1e-6
        and abs(sz - 20.0) < 1e-6
        and int(state.get("bodyCount") or 0) == 1
    )


def _wait_body_count(cdp: Cdp, origin: str, count: int, timeout: float = 30) -> list[str]:
    deadline = time.time() + timeout
    last: dict[str, Any] | None = None
    while time.time() < deadline:
        cdp.drain(0.2)
        problems = site_problems(cdp.events, origin, cdp.urls)
        if problems:
            return problems[:12]
        payload = eval_state(cdp)
        state = (payload or {}).get("state") if payload else None
        if isinstance(state, dict):
            last = state
            if int(state.get("bodyCount") or 0) == count:
                return []
        time.sleep(0.1)
    return [f"bodyCount did not become {count}", json.dumps(last)]


def _delete_default_body(cdp: Cdp, origin: str) -> list[str]:
    tapped = tap_selector(cdp, "#deleteBtn", "clear default box")
    if tapped:
        return tapped
    return _wait_body_count(cdp, origin, 0)


WRAPUP_PHONE_EXPR = r"""
(function(){
  var problems = [];
  function shown(el) {
    if (!el) return null;
    var st = getComputedStyle(el);
    var r = el.getBoundingClientRect();
    if (st.display === 'none' || st.visibility === 'hidden' || r.width < 1 || r.height < 1) return null;
    return r;
  }
  if (document.getElementById('occtBanner')) problems.push('occtBanner present');
  if (document.getElementById('statusTight')) problems.push('statusTight present');
  if (document.getElementById('gateTight')) problems.push('gateTight present');
  if (document.querySelectorAll('#fileMenu [data-action="loadFixture"]').length) problems.push('fixture loaders remain');
  if (!document.querySelector('#fileMenu [data-action="downloadLog"]')) problems.push('missing download log');
  var units = document.getElementById('statusUnits');
  if (!units || !/mm/i.test(units.textContent || '')) problems.push('units readout ' + (units ? units.textContent : 'missing'));
  var hits = [];
  function walk(node) {
    if (!node) return;
    if (node.nodeType === 3) {
      if (/watertight/i.test(node.nodeValue || '')) hits.push(String(node.nodeValue).trim().slice(0, 40));
      return;
    }
    if (node.nodeType !== 1) return;
    var tag = node.tagName;
    if (tag === 'SCRIPT' || tag === 'STYLE') return;
    ['title', 'aria-label', 'data-tool', 'placeholder'].forEach(function (name) {
      var value = node.getAttribute(name);
      if (value && /watertight/i.test(value)) hits.push(name + ':' + value.slice(0, 40));
    });
    for (var child = node.firstChild; child; child = child.nextSibling) walk(child);
  }
  walk(document.body);
  if (hits.length) problems.push('watertight text ' + hits.slice(0, 4).join(' | '));
  var st = window.__cadcamExportState || {};
  var params = st.primitiveParams || {};
  if (st.primitiveKind !== 'box' || st.bodyCount !== 1) problems.push('model ' + st.primitiveKind + ' bodies ' + st.bodyCount);
  if (st.undoDepth !== 0) problems.push('undo ' + st.undoDepth);
  if (st.projectDirty === true) problems.push('dirty');
  if (st.exactVolume !== true) problems.push('exactVolume ' + st.exactVolume);
  if (!(Math.abs(Number(st.volumeMm3) - 8000) < 0.01)) problems.push('volume ' + st.volumeMm3);
  var bb = st.bboxMm || {};
  ['dx', 'dy', 'dz'].forEach(function (key) {
    if (!(Math.abs(Number(bb[key]) - 20) < 0.01)) problems.push('bbox ' + key + ' ' + bb[key]);
  });
  [['cx', 0], ['cy', 0], ['cz', 10], ['sx', 20], ['sy', 20], ['sz', 20]].forEach(function (pair) {
    if (!(Math.abs(Number(params[pair[0]]) - pair[1]) < 0.01)) problems.push(pair[0] + ' ' + params[pair[0]]);
  });
  if (st.unitsPass !== true) problems.push('unitsPass');
  if (st.occtGate !== true || st.gateOcct !== 'PASS') problems.push('gate ' + st.gateOcct);
  if (st.exportAllowed !== true || st.exportDisabled !== false) problems.push('export');
  if (st.bannerHidden !== true) problems.push('bannerHidden');
  var lines = String(st.logText || '').split('\n').filter(Boolean);
  var iso = /^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d+)?Z \[cadmvp\] /;
  if (!lines.length) problems.push('empty log');
  lines.forEach(function (line) {
    if (!iso.test(line)) problems.push('log line ' + line.slice(0, 80));
  });
  function lastMsg(prefix) {
    var found = '';
    lines.forEach(function (line) {
      var at = line.indexOf('[cadmvp] ');
      if (at < 0) return;
      var msg = line.slice(at + 9);
      if (msg.indexOf(prefix) === 0) found = msg;
    });
    return found;
  }
  var vol = parseFloat(lastMsg('volume ').replace('volume ', ''));
  if (!(Math.abs(vol - 8000) < 0.01)) problems.push('log volume ' + lastMsg('volume '));
  var boxParts = lastMsg('bbox ').replace('bbox ', '').split(' x ').map(parseFloat);
  if (boxParts.length !== 3 || boxParts.some(function (n) { return !(Math.abs(n - 20) < 0.01); })) {
    problems.push('log bbox ' + lastMsg('bbox '));
  }
  function tab(action) {
    var nodes = document.querySelectorAll('.topbar [data-action="' + action + '"]');
    for (var i = 0; i < nodes.length; i++) {
      var rect = shown(nodes[i]);
      if (rect) return {el: nodes[i], r: rect};
    }
    return null;
  }
  var undo = tab('undo');
  var redo = tab('redo');
  [['undo', undo], ['redo', redo]].forEach(function (pair) {
    if (!pair[1]) problems.push(pair[0] + ' missing');
    else if (pair[1].r.width + 0.5 < 44 || pair[1].r.height + 0.5 < 44) {
      problems.push(pair[0] + ' ' + pair[1].r.width.toFixed(1) + 'x' + pair[1].r.height.toFixed(1));
    } else if (pair[1].r.left < -0.5 || pair[1].r.right > window.innerWidth + 0.5) {
      problems.push(pair[0] + ' outside ' + window.innerWidth);
    }
  });
  var shelf = document.getElementById('modifyShelf');
  if (!shelf || shelf.hidden !== true) problems.push('shelf not hidden on phone');
  if (st.modifyOpen === true) problems.push('modifyOpen on phone');
  return JSON.stringify(problems);
})()
"""


WRAPUP_DESK_EXPR = r"""
(function(){
  var problems = [];
  var shelf = document.getElementById('modifyShelf');
  if (!shelf || shelf.hidden !== true) problems.push('shelf not collapsed at load');
  var btn = document.getElementById('modifyDesktop');
  if (btn) problems.push('modifyDesktop still present');
  if (shelf) {
    shelf.hidden = false;
    var cs = getComputedStyle(shelf);
    if (cs.flexWrap !== 'nowrap') problems.push('wrap ' + cs.flexWrap);
    var top = null;
    var buttons = shelf.querySelectorAll('button');
    for (var i = 0; i < buttons.length; i++) {
      var br = buttons[i].getBoundingClientRect();
      if (br.width < 1) continue;
      if (br.width + 0.5 < 44 || br.height + 0.5 < 44) {
        problems.push('shelf button ' + br.width.toFixed(1) + 'x' + br.height.toFixed(1));
      }
      if (top === null) top = br.top;
      else if (Math.abs(br.top - top) > 0.5) problems.push('shelf top ' + br.top.toFixed(1) + ' vs ' + top.toFixed(1));
    }
    var sr = shelf.getBoundingClientRect();
    if (sr.height < 44 || sr.height > 64) problems.push('shelf height ' + sr.height.toFixed(1));
    shelf.hidden = true;
  }
  var desk = document.querySelector('.desk-bottom');
  if (desk) problems.push('desk-bottom still present');
  var menu = document.getElementById('createMenu');
  if (menu && menu.hidden !== true) problems.push('create menu open at start');
  return JSON.stringify(problems);
})()
"""


VIEWPORT_GRADIENT_EXPR = r"""
(function(){
  var problems = [];
  var rootBg = getComputedStyle(document.documentElement).getPropertyValue('--bg').trim().toLowerCase();
  if (rootBg !== '#0e2429') problems.push('root --bg ' + rootBg);
  var vp = document.getElementById('viewport');
  var canvas = document.getElementById('canvas');
  if (!vp || !canvas) return JSON.stringify(['missing viewport or canvas']);
  var vpStyle = getComputedStyle(vp);
  var bgImg = String(vpStyle.backgroundImage || '').toLowerCase();
  var wantBg = 'radial-gradient(1200px 700px at 50% 42%, rgb(26, 69, 76) 0%, rgb(18, 48, 56) 55%, rgb(14, 36, 41) 100%)';
  if (bgImg !== wantBg) problems.push('viewport backgroundImage ' + bgImg);
  var csStyle = getComputedStyle(canvas);
  if (csStyle.backgroundColor !== 'rgba(0, 0, 0, 0)' || csStyle.backgroundImage !== 'none') {
    problems.push('canvas css bg ' + csStyle.backgroundColor + ' ' + csStyle.backgroundImage);
  }
  var gl = canvas.getContext('webgl2') || canvas.getContext('webgl');
  if (!gl) {
    problems.push('missing webgl context');
  } else {
    var attrs = gl.getContextAttributes ? gl.getContextAttributes() : null;
    if (!attrs || attrs.alpha !== true) problems.push('webgl alpha ' + (attrs ? attrs.alpha : 'missing'));
    var cc = gl.getParameter(gl.COLOR_CLEAR_VALUE);
    if (!cc || Math.abs(Number(cc[3])) > 1e-6) {
      problems.push('webgl clearAlpha ' + (cc ? cc[3] : 'missing'));
    }
  }
  var sample = window.__cadcamFrameSample || {};
  var corner = sample.colors && sample.colors[4];
  if (!corner || corner[3] !== 0) {
    problems.push('canvas corner clear not transparent ' + JSON.stringify(corner));
  }
  var r = vp.getBoundingClientRect();
  return JSON.stringify({
    problems: problems,
    inner: {x: Math.round(r.left + r.width * 0.45), y: Math.round(r.top + 12)},
    outer: {x: Math.round(r.left + 6), y: Math.round(r.bottom - 6)}
  });
})()
"""


def _png_1x1_rgb(b64: str) -> tuple[int, int, int] | None:
    raw = base64.b64decode(b64)
    if len(raw) < 24 or raw[:8] != b"\x89PNG\r\n\x1a\n":
        return None
    pos = 8
    idat = bytearray()
    while pos + 8 <= len(raw):
        length = struct.unpack(">I", raw[pos : pos + 4])[0]
        kind = raw[pos + 4 : pos + 8]
        if kind == b"IDAT":
            idat.extend(raw[pos + 8 : pos + 8 + length])
        pos += 12 + length
    if not idat:
        return None
    row = zlib.decompress(bytes(idat))
    if len(row) < 4:
        return None
    return (int(row[1]), int(row[2]), int(row[3]))


def viewport_gradient_problems(cdp: Cdp, label: str) -> list[str]:
    raw, err = eval_expr(cdp, VIEWPORT_GRADIENT_EXPR)
    if err or not isinstance(raw, str):
        return [f"{label} {raw or err}"]
    try:
        payload = json.loads(raw)
    except json.JSONDecodeError:
        return [f"{label} {raw[:500]}"]
    if not isinstance(payload, dict):
        return [f"{label} {raw[:500]}"]
    problems = [str(item) for item in (payload.get("problems") or [])]
    if problems:
        return [f"{label}: {item}" for item in problems]
    inner_pt = payload.get("inner") or {}
    outer_pt = payload.get("outer") or {}
    try:
        in_shot = cdp.call(
            "Page.captureScreenshot",
            {
                "format": "png",
                "clip": {
                    "x": int(inner_pt["x"]),
                    "y": int(inner_pt["y"]),
                    "width": 1,
                    "height": 1,
                    "scale": 1,
                },
            },
        )
        out_shot = cdp.call(
            "Page.captureScreenshot",
            {
                "format": "png",
                "clip": {
                    "x": int(outer_pt["x"]),
                    "y": int(outer_pt["y"]),
                    "width": 1,
                    "height": 1,
                    "scale": 1,
                },
            },
        )
        inner_rgb = _png_1x1_rgb(str(in_shot.get("data") or ""))
        outer_rgb = _png_1x1_rgb(str(out_shot.get("data") or ""))
    except Exception as exc:
        return [f"{label} screenshot {exc}"]
    if inner_rgb is None or outer_rgb is None:
        return [f"{label} screenshot decode inner={inner_rgb!r} outer={outer_rgb!r}"]
    if inner_rgb == (14, 36, 41):
        return [f"{label} canvas inner background is flat #0e2429 {inner_rgb!r}"]
    if inner_rgb == outer_rgb or sum(inner_rgb) <= sum(outer_rgb) + 10:
        return [
            f"{label} canvas gradient not visible inner={inner_rgb!r} outer={outer_rgb!r}"
        ]
    return []


def _json_problems(raw: Any, err: str, label: str) -> list[str]:
    if err or not isinstance(raw, str):
        return [f"{label} {raw or err}"]
    try:
        found = json.loads(raw)
    except json.JSONDecodeError:
        return [f"{label} {raw[:500]}"]
    if not isinstance(found, list):
        return [f"{label} {raw[:500]}"]
    return [str(item) for item in found]


def run_wrapup(cdp: Cdp, origin: str) -> list[str]:
    """Default 20 mm box, [cadmvp] log, header Undo/Redo, desktop shelf."""
    try:
        set_portrait(cdp)
    except (RuntimeError, TimeoutError, OSError) as exc:
        return [f"wrapup portrait {exc}"]
    url = origin + "/"
    print(f"load wrapup phone {url}", flush=True)
    state, load_problems = wait_for_case(cdp, origin, url, PAGE_TIMEOUT_S)
    if load_problems:
        return ["wrapup phone load", *load_problems[:20]]
    if not isinstance(state, dict):
        return ["wrapup phone returned no state"]
    raw, err = eval_expr(cdp, WRAPUP_PHONE_EXPR)
    problems = _json_problems(raw, err, "wrapup phone")
    if problems:
        return problems
    problems = viewport_gradient_problems(cdp, "wrapup phone gradient")
    if problems:
        return problems
    clicked, click_err = eval_expr(
        cdp,
        "(function(){var b=document.querySelector('.topbar [data-action=\"undo\"]');"
        "if(!b)return 'missing';b.click();"
        "var r=document.querySelector('.topbar [data-action=\"redo\"]');"
        "if(!r)return 'missing redo';r.click();return 'clicked';})()",
    )
    if click_err or clicked != "clicked":
        return [f"wrapup undo click {clicked or click_err}"]
    time.sleep(0.2)
    cdp.drain(0.3)
    quiet = site_problems(cdp.events, origin, cdp.urls)
    if quiet:
        return ["wrapup undo click", *quiet[:12]]
    after = eval_state(cdp)
    after_state = (after or {}).get("state") if after else None
    if not isinstance(after_state, dict) or int(after_state.get("undoDepth") or 0) != 0:
        return [f"wrapup undo depth {after_state!r}"[:400]]
    if int(after_state.get("bodyCount") or 0) != 1:
        return [f"wrapup undo changed the model {after_state.get('bodyCount')!r}"]
    covered = coverage_problems(cdp, False)
    if covered:
        return ["wrapup phone coverage", *covered[:20]]
    fit = portrait_fit_problems(cdp)
    if fit:
        return ["wrapup phone fit", *fit[:20]]
    try:
        set_desktop(cdp)
    except (RuntimeError, TimeoutError, OSError) as exc:
        return [f"wrapup desktop {exc}"]
    print(f"load wrapup desktop {url}", flush=True)
    state, load_problems = wait_for_case(cdp, origin, url, PAGE_TIMEOUT_S)
    if load_problems:
        return ["wrapup desktop load", *load_problems[:20]]
    raw, err = eval_expr(cdp, WRAPUP_DESK_EXPR)
    problems = _json_problems(raw, err, "wrapup desktop")
    if problems:
        return problems
    problems = viewport_gradient_problems(cdp, "wrapup desktop gradient")
    if problems:
        return problems
    desk_callouts = callout_problems(cdp, "box", {"boxSx": 20.0, "boxSy": 20.0, "boxSz": 20.0})
    if desk_callouts:
        return ["wrapup desktop callouts", *desk_callouts]
    escaped, esc_err = eval_expr(
        cdp,
        "(function(){document.dispatchEvent(new KeyboardEvent('keydown',{key:'Escape',bubbles:true}));"
        "var shelf=document.getElementById('modifyShelf');"
        "return JSON.stringify({hidden:!!(shelf&&shelf.hidden)});})()",
    )
    if esc_err or not isinstance(escaped, str):
        return [f"wrapup esc {escaped or esc_err}"]
    try:
        esc_state = json.loads(escaped)
    except json.JSONDecodeError:
        return [f"wrapup esc {escaped}"]
    if esc_state.get("hidden") is not True:
        return [f"wrapup esc left the shelf open {esc_state}"]
    created, create_err = eval_expr(
        cdp,
        "(function(){var tm=document.querySelector('[data-action=\"toolsMenu\"]');if(tm)tm.click();"
        "var shelf=document.getElementById('modifyShelf');if(shelf)shelf.hidden=false;"
        "var b=document.querySelector('#toolsSheet [data-action=\"createMenu\"]');"
        "if(!b)return 'missing';b.click();"
        "var menu=document.getElementById('createMenu');"
        "return JSON.stringify({shelf:!!(shelf&&shelf.hidden!==true),menu:!!(menu&&menu.hidden!==true)});})()",
    )
    if create_err or not isinstance(created, str):
        return [f"wrapup create {created or create_err}"]
    try:
        created_state = json.loads(created)
    except json.JSONDecodeError:
        return [f"wrapup create {created}"]
    if created_state.get("shelf") is not False or created_state.get("menu") is not True:
        return [f"wrapup create did not close the shelf {created_state}"]
    eval_expr(
        cdp,
        "(function(){document.dispatchEvent(new KeyboardEvent('keydown',{key:'Escape',bubbles:true}));return 'ok';})()",
    )
    downloaded, down_err = eval_expr(
        cdp,
        "(function(){var file=document.getElementById('fileBtn');if(!file)return 'missing file';file.click();"
        "var log=document.querySelector('#fileMenu [data-action=\"downloadLog\"]');"
        "if(!log)return 'missing log';log.click();"
        "var last=window.__cadcamLastDownload||{};"
        "return JSON.stringify({name:last.name||'',text:last.text||''});})()",
    )
    if down_err or not isinstance(downloaded, str) or not downloaded.startswith("{"):
        return [f"wrapup download {downloaded or down_err}"]
    try:
        saved = json.loads(downloaded)
    except json.JSONDecodeError:
        return [f"wrapup download {downloaded[:300]}"]
    if saved.get("name") != "cadmvp-log.txt":
        return [f"wrapup download name {saved.get('name')!r}"]
    text = str(saved.get("text") or "")
    lines = [line for line in text.splitlines() if line]
    if not lines:
        return ["wrapup download empty"]
    import re
    stamp = re.compile(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d+)?Z \[cadmvp\] ")
    bad = [line for line in lines if not stamp.match(line)]
    if bad:
        return [f"wrapup download line {bad[0][:120]}"]
    if not any("volume " in line and "8000" in line for line in lines):
        return ["wrapup download missing volume 8000"]
    print("wrapup pass", flush=True)
    return []


CALLOUT_PROBE_EXPR = (
    "(function(){"
    "var hook=window.__cadcamCallouts;"
    "if(!hook||typeof hook.probe!=='function') return 'missing';"
    "return JSON.stringify(hook.probe());"
    "})()"
)

CALLOUT_FIELDS = {
    "box": (("L", "boxSx"), ("W", "boxSy"), ("H", "boxSz")),
    "cylinder": (("Ø", "cylD"), ("H", "cylH")),
    "disc": (("Ø", "discD"), ("T", "discT")),
}


def _callout_probe(cdp: Cdp) -> tuple[dict[str, Any] | None, list[str]]:
    raw, err = eval_expr(cdp, CALLOUT_PROBE_EXPR)
    if err or not isinstance(raw, str) or not raw.startswith("{"):
        return None, [f"callout probe {raw or err}"]
    try:
        data = json.loads(raw)
    except json.JSONDecodeError:
        return None, [f"callout probe {raw}"]
    if not isinstance(data, dict):
        return None, [f"callout probe {raw}"]
    return data, []


def callout_problems(
    cdp: Cdp,
    kind: str,
    expect_mm: dict[str, float] | None = None,
) -> list[str]:
    """Phone hides basic-shape #calloutLayer and keeps Size fields editable; desktop shows callouts."""
    data, problems = _callout_probe(cdp)
    if problems or not isinstance(data, dict):
        return problems
    if data.get("editing") is not True:
        problems.append(f"callouts editing flag {data.get('editing')!r}")
    if data.get("kind") != kind:
        problems.append(f"callouts kind {data.get('kind')!r}")
    for name, key in (("Home", "coversHome"), ("Export", "coversExport"), ("units", "coversUnits")):
        if data.get(key) is True:
            problems.append(f"callouts cover {name}")
    expect = CALLOUT_FIELDS.get(kind)
    if expect is None:
        problems.append(f"callout kind {kind!r}")
        return problems
    if data.get("dimPanelHidden") is True:
        problems.append(f"dimPanel hidden during {kind} edit")
    size_fields = data.get("sizeFields")
    if not isinstance(size_fields, list) or len(size_fields) != len(expect):
        problems.append(f"size fields {size_fields!r}")
        return problems
    for index, (tag, dim) in enumerate(expect):
        field = size_fields[index] if index < len(size_fields) and isinstance(size_fields[index], dict) else {}
        if field.get("tag") != tag:
            problems.append(f"size field tag {field.get('tag')!r} != {tag}")
        if field.get("dim") != dim:
            problems.append(f"size field dim {field.get('dim')!r} != {dim}")
        if field.get("present") is not True or field.get("editable") is not True:
            problems.append(f"size field {dim} not editable {field!r}")
        if field.get("groupHidden") is True:
            problems.append(f"size field {dim} group hidden")
        if not str(field.get("value") or "").strip():
            problems.append(f"size field {dim} value {field.get('value')!r}")
        if expect_mm and dim in expect_mm:
            try:
                mm = float(field.get("mm"))
            except (TypeError, ValueError):
                mm = float("nan")
            if abs(mm - float(expect_mm[dim])) > 0.02:
                problems.append(f"size field {dim} mm {field.get('mm')!r}")
    rows = data.get("rows")
    if data.get("phone") is True:
        if data.get("hidden") is not True:
            problems.append(f"phone callouts visible during {kind} edit")
        if isinstance(rows, list) and rows:
            problems.append(f"phone callout rows {len(rows)}")
        if data.get("coversVpCenter") is True or data.get("coversBodyCenter") is True:
            problems.append("phone callouts centered over body")
        return problems
    if data.get("hidden") is not False:
        problems.append(f"callouts hidden during {kind} edit")
    if data.get("inside") is not True:
        problems.append("callouts outside the viewport")
    if not isinstance(rows, list):
        problems.append(f"callout rows {rows!r}")
        return problems
    if len(rows) != len(expect):
        problems.append(f"callout rows {len(rows)} != {len(expect)}")
    for index, (tag, dim) in enumerate(expect):
        if index >= len(rows) or not isinstance(rows[index], dict):
            break
        row = rows[index]
        if row.get("tag") != tag:
            problems.append(f"callout tag {row.get('tag')!r} != {tag}")
        if row.get("dim") != dim:
            problems.append(f"callout dim {row.get('dim')!r} != {dim}")
        text = str(row.get("text") or "")
        formatted = str(row.get("formatted") or "")
        if not text or text != formatted:
            problems.append(f"callout {dim} text {text!r} formatted {formatted!r}")
        if not text.endswith(" mm"):
            problems.append(f"callout {dim} units {text!r}")
        if expect_mm and dim in expect_mm:
            try:
                mm = float(row.get("mm"))
            except (TypeError, ValueError):
                mm = float("nan")
            if abs(mm - float(expect_mm[dim])) > 0.02:
                problems.append(f"callout {dim} mm {row.get('mm')!r}")
        try:
            font_px = float(row.get("fontPx") or 0)
        except (TypeError, ValueError):
            font_px = 0.0
        if font_px + 0.5 < 13:
            problems.append(f"callout {dim} font {font_px}")
        for part in ("value", "minus", "plus"):
            try:
                width = float(row.get(part + "W") or 0)
                height = float(row.get(part + "H") or 0)
            except (TypeError, ValueError):
                width = 0.0
                height = 0.0
            if width + 0.5 < 44 or height + 0.5 < 44:
                problems.append(f"callout {dim} {part} {width:.1f}x{height:.1f}")
    return problems


def callout_hidden_problems(cdp: Cdp) -> list[str]:
    """Callouts leave when the basic-shape edit ends."""
    data, problems = _callout_probe(cdp)
    if problems or not isinstance(data, dict):
        return problems
    if data.get("hidden") is not True:
        problems.append(f"callouts still visible {data.get('hidden')!r}")
    if data.get("editing") is not False:
        problems.append(f"editing flag {data.get('editing')!r}")
    rows = data.get("rows")
    if isinstance(rows, list) and rows:
        problems.append(f"callout rows left {len(rows)}")
    return problems


def run_portrait(cdp: Cdp, origin: str) -> list[str]:
    """390x844 touch emulation. Tap primitives, bottom sheet, move/rotate/resize a box."""
    try:
        set_portrait(cdp)
    except (RuntimeError, TimeoutError, OSError) as exc:
        return [f"portrait emulation failed: {exc}"]
    print(f"load portrait_origin_plane {origin}/", flush=True)
    _origin_state, origin_load = wait_for_case(cdp, origin, origin + "/", PAGE_TIMEOUT_S)
    if origin_load:
        return ["portrait origin plane load", *origin_load[:20]]
    origin_found = portrait_origin_plane_problems(cdp)
    if origin_found:
        return ["portrait origin plane", *origin_found]
    problems: list[str] = []
    inspector_checked = False
    stamp_checked = False
    create_checked = False
    sketch_checked = False
    for spec in PORTRAIT:
        kind = str(spec["kind"])
        url = origin + "/"
        print(f"load portrait_{kind} {url}", flush=True)
        _state, load_problems = wait_for_case(cdp, origin, url, PAGE_TIMEOUT_S)
        if load_problems:
            problems.append(f"portrait {kind} load")
            problems.extend(load_problems[:20])
            return problems
        if not inspector_checked:
            inspector_checked = True
            closed = closed_inspector_problems(cdp)
            if closed:
                problems.append(f"portrait {kind} closed inspector")
                problems.extend(closed)
                return problems
        if not stamp_checked:
            stamp_checked = True
            stamp_found = stamp_problems(cdp)
            if stamp_found:
                problems.append(f"portrait {kind} stamp")
                problems.extend(stamp_found)
                return problems
        if not create_checked:
            create_checked = True
            menu_found = create_menu_problems(cdp)
            if menu_found:
                problems.append(f"portrait {kind} create menu")
                problems.extend(menu_found)
                return problems
        if not sketch_checked:
            sketch_checked = True
            sketch_found = portrait_sketch_problems(cdp)
            if sketch_found:
                problems.append(f"portrait {kind} sketch")
                problems.extend(sketch_found)
                return problems
        # The default page is already the 20 mm box. Another Box tap adds a body.
        if not (kind == "box" and _is_default_box(_state)):
            if kind in ("cylinder", "disc"):
                cleared = _delete_default_body(cdp, origin)
                if cleared:
                    problems.append(f"portrait {kind} clear")
                    problems.extend(cleared[:12])
                    return problems
                hidden = callout_hidden_problems(cdp)
                if hidden:
                    problems.append(f"portrait {kind} callouts hidden")
                    problems.extend(hidden)
                    return problems
            raw, err = eval_expr(cdp, toolbar_point_expr(kind))
            if err or not isinstance(raw, str) or not raw.startswith("{"):
                problems.append(f"portrait {kind} toolbar {raw or err}")
                return problems
            box = json.loads(raw)
            if float(box["w"]) < 44 or float(box["h"]) < 44:
                problems.append(f"portrait {kind} button {box['w']}x{box['h']}")
                return problems
            touch_tap(cdp, float(box["x"]), float(box["y"]))
        created, wait_problems = wait_portrait(
            cdp, origin, kind, {str(spec["key"]): float(spec["fresh"])}, PAGE_TIMEOUT_S
        )
        if wait_problems or not isinstance(created, dict):
            problems.append(f"portrait {kind} create")
            problems.extend(wait_problems[:20])
            return problems
        layout_problems = portrait_layout_ok(created, expanded=False)
        if layout_problems:
            problems.append(f"portrait {kind} layout")
            problems.extend(layout_problems)
            return problems
        covered = coverage_problems(cdp, False)
        if covered:
            problems.append(f"portrait {kind} coverage")
            problems.extend(covered)
            return problems
        fit_problems = portrait_fit_problems(cdp)
        if fit_problems:
            problems.append(f"portrait {kind} overflow")
            problems.extend(fit_problems)
            return problems
        fresh_mm = {
            "box": {"boxSx": 20.0, "boxSy": 20.0, "boxSz": 20.0},
            "cylinder": {"cylD": 20.0, "cylH": 20.0},
            "disc": {"discD": 18.0, "discT": 4.0},
        }[kind]
        shown = callout_problems(cdp, kind, fresh_mm)
        if shown:
            problems.append(f"portrait {kind} callouts")
            problems.extend(shown)
            return problems
        if kind == "box":
            home_found = home_aim_round(cdp, "portrait")
            if home_found:
                problems.append("portrait home")
                problems.extend(home_found)
                return problems
            eval_expr(
                cdp,
                "(function(){var b=document.querySelector('[data-action=\"select\"][data-mode=\"item\"]');"
                "if(b)b.click();return 'ok';})()",
            )
        expand_problems = tap_selector(cdp, "#dimToggle", f"portrait {kind} expand")
        if expand_problems:
            problems.extend(expand_problems)
            return problems
        opened, open_problems = wait_portrait(
            cdp,
            origin,
            kind,
            {str(spec["key"]): float(spec["fresh"])},
            PAGE_TIMEOUT_S,
            extra={"dimSheetOpen": True},
        )
        if open_problems or not isinstance(opened, dict):
            problems.append(f"portrait {kind} expand wait")
            problems.extend(open_problems[:20])
            return problems
        open_layout = portrait_layout_ok(opened, expanded=True)
        if open_layout:
            problems.append(f"portrait {kind} expanded layout")
            problems.extend(open_layout)
            return problems
        open_covered = coverage_problems(cdp, True)
        if open_covered:
            problems.append(f"portrait {kind} open coverage")
            problems.extend(open_covered)
            return problems
        open_fit = portrait_fit_problems(cdp)
        if open_fit:
            problems.append(f"portrait {kind} expanded overflow")
            problems.extend(open_fit)
            return problems
        measured, measure_err = eval_expr(cdp, TARGET_EXPR)
        if measure_err or not isinstance(measured, str):
            problems.append(f"portrait {kind} targets {measured or measure_err}")
            return problems
        sizes = json.loads(measured)
        if int(sizes.get("n") or 0) < 12 or sizes.get("bad"):
            problems.append(f"portrait {kind} targets {measured}")
            return problems
        handles = opened.get("gizmoHandles") or {}
        if float(handles.get("minPx") or 0) < 44:
            problems.append(f"portrait {kind} gizmo handles {handles}")
            return problems
        edited, edit_err = eval_expr(cdp, edit_expr(str(spec["field"]), str(spec["value"])))
        if edit_err or edited != "edited":
            problems.append(f"portrait {kind} edit {edited or edit_err}")
            return problems
        done, edit_problems = wait_portrait(
            cdp, origin, kind, {str(spec["key"]): float(spec["want"])}, PAGE_TIMEOUT_S
        )
        if edit_problems or not isinstance(done, dict):
            problems.append(f"portrait {kind} edited")
            problems.extend(edit_problems[:20])
            return problems
        live_mm = {
            "box": {"boxSx": 30.0},
            "cylinder": {"cylH": 24.0},
            "disc": {"discD": 22.0},
        }[kind]
        live = callout_problems(cdp, kind, live_mm)
        if live:
            problems.append(f"portrait {kind} callouts live")
            problems.extend(live)
            return problems
        print(
            f"portrait_{kind}: gate PASS, {spec['field']} {spec['fresh']} -> {spec['want']}, "
            f"targets {sizes.get('n')}, handles {handles.get('minPx')}",
            flush=True,
        )
        if kind != "box":
            continue
        typed, type_err = eval_expr(cdp, edit_expr("primCx", "5"))
        if type_err or typed != "edited":
            problems.append(f"portrait box move type {typed or type_err}")
            return problems
        moved, move_problems = wait_portrait(cdp, origin, "box", {"cx": 5.0, "sx": 30.0}, PAGE_TIMEOUT_S)
        if move_problems or not isinstance(moved, dict):
            problems.append("portrait box move")
            problems.extend(move_problems[:20])
            return problems
        mode_problems = tap_selector(cdp, '#gizmoSwitch [data-mode="rotate"]', "portrait box rotate mode")
        if mode_problems:
            problems.extend(mode_problems)
            return problems
        rotated_mode, mode_wait = wait_portrait(
            cdp, origin, "box", {"cx": 5.0}, PAGE_TIMEOUT_S, extra={"gizmoMode": "rotate"}
        )
        if mode_wait or not isinstance(rotated_mode, dict):
            problems.append("portrait box rotate mode wait")
            problems.extend(mode_wait[:20])
            return problems
        rot_typed, rot_err = eval_expr(cdp, edit_expr("primRz", "15"))
        if rot_err or rot_typed != "edited":
            problems.append(f"portrait box rotate type {rot_typed or rot_err}")
            return problems
        rotated, rot_problems = wait_portrait(
            cdp, origin, "box", {"cx": 5.0, "rz": 15.0, "sx": 30.0}, PAGE_TIMEOUT_S
        )
        if rot_problems or not isinstance(rotated, dict):
            problems.append("portrait box rotate")
            problems.extend(rot_problems[:20])
            return problems
        scale_mode = tap_selector(cdp, '#gizmoSwitch [data-mode="scale"]', "portrait box scale mode")
        if scale_mode:
            problems.extend(scale_mode)
            return problems
        scaled_mode, scale_wait = wait_portrait(
            cdp, origin, "box", {"rz": 15.0}, PAGE_TIMEOUT_S, extra={"gizmoMode": "scale"}
        )
        if scale_wait or not isinstance(scaled_mode, dict):
            problems.append("portrait box scale mode wait")
            problems.extend(scale_wait[:20])
            return problems
        unlocked, unlock_err = eval_expr(cdp, UNLOCK_EXPR)
        if unlock_err or unlocked != "off":
            problems.append(f"portrait box unlock {unlocked or unlock_err}")
            return problems
        size_typed, size_err = eval_expr(cdp, edit_expr("boxSy", "22"))
        if size_err or size_typed != "edited":
            problems.append(f"portrait box scale type {size_typed or size_err}")
            return problems
        scaled, scale_problems = wait_portrait(
            cdp, origin, "box", {"cx": 5.0, "rz": 15.0, "sx": 30.0, "sy": 22.0}, PAGE_TIMEOUT_S
        )
        if scale_problems or not isinstance(scaled, dict):
            problems.append("portrait box scale")
            problems.extend(scale_problems[:20])
            return problems
        step_problems = tap_selector(
            cdp, '#dimPanel button[data-dim="primCx"][data-delta="1"]', "portrait box stepper"
        )
        if step_problems:
            problems.extend(step_problems)
            return problems
        stepped, step_wait = wait_portrait(
            cdp, origin, "box", {"cx": 6.0, "rz": 15.0, "sy": 22.0, "sx": 30.0}, PAGE_TIMEOUT_S
        )
        if step_wait or not isinstance(stepped, dict):
            problems.append("portrait box stepper")
            problems.extend(step_wait[:20])
            return problems
        if stepped.get("snap") is not True:
            problems.append(f"portrait box snap {stepped.get('snap')!r}")
            return problems
        stepped_callouts = callout_problems(
            cdp, "box", {"boxSx": 30.0, "boxSy": 22.0, "boxSz": 30.0}
        )
        if stepped_callouts:
            problems.append("portrait callout check")
            problems.extend(stepped_callouts)
            return problems
        print(
            "portrait_box transforms: move cx 5 stepper 6, rotate z 15, resize sy 22, "
            "callouts hidden, snap on, gate PASS",
            flush=True,
        )
    return problems


def run_portrait_holes(cdp: Cdp, origin: str) -> list[str]:
    """390x844. Resize a box into the plate, tap its top face, cut three countersunk holes."""
    try:
        set_portrait(cdp)
    except (RuntimeError, TimeoutError, OSError) as exc:
        return [f"portrait holes emulation failed: {exc}"]
    url = origin + "/"
    print(f"load portrait_holes {url}", flush=True)
    _loaded, load_problems = wait_for_case(cdp, origin, url, PAGE_TIMEOUT_S)
    if load_problems:
        return ["portrait holes load", *load_problems[:20]]
    if not _is_default_box(_loaded):
        raw, err = eval_expr(cdp, toolbar_point_expr("box"))
        if err or not isinstance(raw, str) or not raw.startswith("{"):
            return [f"portrait holes toolbar {raw or err}"]
        box = json.loads(raw)
        touch_tap(cdp, float(box["x"]), float(box["y"]))
    created, wait_problems = wait_portrait(cdp, origin, "box", {"sx": 20.0}, PAGE_TIMEOUT_S)
    if wait_problems or not isinstance(created, dict):
        return ["portrait holes create", *wait_problems[:20]]
    defaults = created.get("holeDefaults") or {}
    try:
        plate_sx = float(defaults["plateSx"])
        plate_sy = float(defaults["plateSy"])
        plate_sz = float(defaults["plateSz"])
        diameter = float(defaults["diameterMm"])
        cs_diameter = float(defaults["countersinkDiameterMm"])
        angle = float(defaults["countersinkAngleDeg"])
    except (KeyError, TypeError, ValueError):
        return [f"portrait holes defaults {defaults!r}"]
    positions = defaults.get("positions")
    if not isinstance(positions, list) or len(positions) != 3:
        return [f"portrait holes positions {positions!r}"]
    expand_problems = tap_selector(cdp, "#dimToggle", "portrait holes expand")
    if expand_problems:
        return expand_problems
    unlocked, unlock_err = eval_expr(cdp, UNLOCK_EXPR)
    if unlock_err or unlocked != "off":
        return [f"portrait holes unlock {unlocked or unlock_err}"]
    edits = (
        ("boxSx", plate_sx),
        ("boxSy", plate_sy),
        ("boxSz", plate_sz),
        ("primCz", plate_sz / 2),
    )
    for field, value in edits:
        edited, edit_err = eval_expr(cdp, edit_expr(field, num_text(value)))
        if edit_err or edited != "edited":
            return [f"portrait holes {field} {edited or edit_err}"]
    plate, plate_problems = wait_portrait(
        cdp,
        origin,
        "box",
        {"sx": plate_sx, "sy": plate_sy, "sz": plate_sz, "cz": plate_sz / 2},
        PAGE_TIMEOUT_S,
        extra={"dimSheetOpen": True},
    )
    if plate_problems or not isinstance(plate, dict):
        return ["portrait holes plate", *plate_problems[:20]]
    open_fit = portrait_fit_problems(cdp)
    if open_fit:
        return ["portrait holes expanded overflow", *open_fit]
    open_covered = coverage_problems(cdp, True)
    if open_covered:
        return ["portrait holes open coverage", *open_covered]
    collapse = tap_selector(cdp, "#dimToggle", "portrait holes collapse")
    if collapse:
        return collapse
    collapsed, collapse_problems = wait_portrait(
        cdp,
        origin,
        "box",
        {"sx": plate_sx, "sy": plate_sy, "sz": plate_sz},
        PAGE_TIMEOUT_S,
        extra={"dimSheetOpen": False},
    )
    if collapse_problems or not isinstance(collapsed, dict):
        return ["portrait holes collapse wait", *collapse_problems[:20]]
    shut_fit = portrait_fit_problems(cdp)
    if shut_fit:
        return ["portrait holes collapsed overflow", *shut_fit]
    shut_covered = coverage_problems(cdp, False)
    if shut_covered:
        return ["portrait holes collapsed coverage", *shut_covered]
    topped, top_err = eval_expr(
        cdp,
        "(function(){var b=document.querySelector('[data-action=\"view\"][data-view=\"top\"]');"
        "if(!b)return 'missing';b.click();return 'clicked';})()",
    )
    if top_err or topped != "clicked":
        return [f"portrait holes top view {topped or top_err}"]
    time.sleep(0.7)
    for _zoom in range(5):
        zoomed, zoom_err = eval_expr(
            cdp,
            "(function(){var b=document.querySelector('[data-action=\"zoomstep\"]');"
            "if(!b)return 'missing';b.click();return 'clicked';})()",
        )
        if zoom_err or zoomed != "clicked":
            return [f"portrait holes zoom {zoomed or zoom_err}"]
    time.sleep(0.2)
    hole_button = tap_point(cdp, create_point_expr('[data-action="holeTool"]'), "portrait holes tool")
    if hole_button:
        return hole_button
    armed, arm_problems = wait_hole_state(
        cdp,
        origin,
        lambda state: state.get("holeTool") is True and state.get("selectionMode") == "face",
        15,
        "portrait holes arm",
    )
    if arm_problems or not isinstance(armed, dict):
        return ["portrait holes arm", *arm_problems[:20]]
    points_raw, points_err = eval_expr(cdp, SHEET_HIT_EXPR)
    try:
        if points_err or not isinstance(points_raw, str) or not points_raw.startswith("{"):
            return [f"portrait holes face points {points_raw or points_err}"]
        try:
            hit_plan = json.loads(points_raw)
        except json.JSONDecodeError:
            return [f"portrait holes face points {points_raw}"]
        face_points = hit_plan.get("pts") if isinstance(hit_plan, dict) else None
        if not isinstance(face_points, list) or not face_points:
            return [f"portrait holes face points {points_raw}"]
        faced: dict[str, Any] | None = None
        face_problems: list[str] = []

        def accept_face(point: dict[str, Any]) -> bool:
            nonlocal faced, face_problems
            faced, face_problems = wait_hole_state(
                cdp,
                origin,
                lambda state: state.get("holeFaceReady") is True,
                1.2,
                "portrait holes face",
            )
            if isinstance(faced, dict) and faced.get("holeFaceReady") is True and not face_problems:
                return True
            faced = None
            return False

        for point in face_points:
            if not isinstance(point, dict) or point.get("onView") is not True:
                continue
            touch_tap(cdp, float(point["x"]), float(point["y"]))
            if accept_face(point):
                break
        if not isinstance(faced, dict):
            for point in face_points:
                if not isinstance(point, dict) or point.get("onView") is not True:
                    continue
                sent, sent_err = eval_expr(cdp, synth_tap_expr(float(point["x"]), float(point["y"])))
                if sent_err or sent != "sent":
                    face_problems = [f"portrait holes synth {sent or sent_err}", *face_problems]
                    break
                if accept_face(point):
                    break
        if not isinstance(faced, dict):
            probe, _probe_err = eval_expr(cdp, "JSON.stringify(window.__holeTapProbe||[])")
            return ["portrait holes face", *face_problems[:8], points_raw, str(probe or "")]
    finally:
        eval_expr(cdp, RESTORE_SHEET_EXPR)
    reopen = tap_selector(cdp, "#dimToggle", "portrait holes sheet")
    if reopen:
        return reopen
    shown, shown_err = eval_expr(cdp, reveal_expr("#holeApply"))
    if shown_err or shown != "shown":
        return [f"portrait holes reveal {shown or shown_err}"]
    for field, want in (("holeDia", diameter), ("holeCsDia", cs_diameter), ("holeCsAng", angle)):
        text, text_err = field_text(cdp, field)
        if text_err or not text:
            return [f"portrait holes {field} {text or text_err}"]
        try:
            got = float(text)
        except ValueError:
            return [f"portrait holes {field} {text}"]
        if abs(got - want) > 1e-6:
            return [f"portrait holes {field} {got} want {want}"]
    if faced.get("holeDepthMode") != "through" or faced.get("holeCountersink") is not True:
        return [f"portrait holes mode {faced.get('holeDepthMode')!r} countersink {faced.get('holeCountersink')!r}"]
    done: dict[str, Any] | None = None
    for index, uv in enumerate(positions):
        if not isinstance(uv, (list, tuple)) or len(uv) < 2:
            return [f"portrait holes uv {uv!r}"]
        for field, value in (("holeU", float(uv[0])), ("holeV", float(uv[1]))):
            edited, edit_err = eval_expr(cdp, edit_expr(field, num_text(value)))
            if edit_err or edited != "edited":
                return [f"portrait holes {field} {edited or edit_err}"]
        shown, shown_err = eval_expr(cdp, reveal_expr("#holeApply"))
        if shown_err or shown != "shown":
            return [f"portrait holes reveal {shown or shown_err}"]
        cut = tap_selector(cdp, "#holeApply", "portrait holes cut")
        if cut:
            return cut
        want_count = index + 1
        done, cut_problems = wait_hole_state(
            cdp,
            origin,
            lambda state, count=want_count: (
                int(state.get("holeCount") or 0) == count
                and state.get("occtGate") is True
                and state.get("gateOcct") == "PASS"
                and state.get("unitsPass") is True
                and int(state.get("bodyCount") or 0) == 1
            ),
            PAGE_TIMEOUT_S,
            f"portrait holes cut {want_count}",
        )
        if cut_problems or not isinstance(done, dict):
            return [f"portrait holes cut {want_count}", *cut_problems[:20]]
    if not isinstance(done, dict):
        return ["portrait holes no result"]
    hole_log = done.get("holeLog") or []
    if not isinstance(hole_log, list) or len(hole_log) != 3:
        return [f"portrait holes log {hole_log!r}"]
    try:
        volume_before = float(hole_log[0]["volumeBefore"])
        volume_after = float(hole_log[-1]["volumeAfter"])
    except (KeyError, TypeError, ValueError):
        return [f"portrait holes volumes {hole_log!r}"]
    if not volume_after < volume_before:
        return [f"portrait holes volume {volume_before} -> {volume_after}"]
    for index, entry in enumerate(hole_log):
        if not isinstance(entry, dict):
            return [f"portrait holes entry {index}"]
        if entry.get("countersink") is not True or entry.get("depthMode") != "through":
            return [f"portrait holes entry {index} {entry!r}"]
        if abs(float(entry.get("diameterMm") or 0) - diameter) > 1e-6:
            return [f"portrait holes diameter {entry.get('diameterMm')!r}"]
        if abs(float(entry.get("countersinkDiameterMm") or 0) - cs_diameter) > 1e-6:
            return [f"portrait holes countersink {entry.get('countersinkDiameterMm')!r}"]
        if abs(float(entry.get("countersinkAngleDeg") or 0) - angle) > 1e-6:
            return [f"portrait holes angle {entry.get('countersinkAngleDeg')!r}"]
        if abs(float(entry.get("u") or 0) - float(positions[index][0])) > 1e-6:
            return [f"portrait holes u {entry.get('u')!r}"]
        if abs(float(entry.get("v") or 0) - float(positions[index][1])) > 1e-6:
            return [f"portrait holes v {entry.get('v')!r}"]
        if abs(float(entry.get("depthMm") or 0) - plate_sz) > 0.2:
            return [f"portrait holes depth {entry.get('depthMm')!r}"]
        if not float(entry.get("volumeAfter") or 0) < float(entry.get("volumeBefore") or 0):
            return [f"portrait holes step volume {entry!r}"]
    print(
        "portrait_holes: plate "
        f"{plate_sx:g}x{plate_sy:g}x{plate_sz:g} mm, "
        f"diameter {diameter:g} mm, countersink {cs_diameter:g} mm, angle {angle:g} deg, "
        f"volume {volume_before:.3f} -> {volume_after:.3f} mm3, "
        f"fit {defaults.get('fit')!r}",
        flush=True,
    )
    hole_fit = portrait_fit_problems(cdp)
    if hole_fit:
        return ["portrait holes open overflow", *hole_fit]
    measured, measure_err = eval_expr(cdp, TARGET_EXPR)
    if measure_err or not isinstance(measured, str):
        return [f"portrait holes targets {measured or measure_err}"]
    sizes = json.loads(measured)
    if int(sizes.get("n") or 0) < 12 or sizes.get("bad"):
        return [f"portrait holes targets {measured}"]
    scrolled, scroll_err = eval_expr(
        cdp,
        "(function(){var panel=document.getElementById('dimPanel');"
        "if(panel) panel.scrollTop=0;"
        "var toggle=document.getElementById('dimToggle');"
        "if(toggle&&toggle.scrollIntoView) toggle.scrollIntoView({block:'nearest',inline:'nearest'});"
        "return toggle?'top':'missing';})()",
    )
    if scroll_err or scrolled != "top":
        return [f"portrait holes hide scroll {scrolled or scroll_err}"]
    close_sheet = tap_selector(cdp, "#dimToggle", "portrait holes hide")
    if close_sheet:
        return close_sheet
    hidden, hide_problems = wait_hole_state(
        cdp,
        origin,
        lambda state: state.get("dimSheetOpen") is False and int(state.get("holeCount") or 0) == 3,
        PAGE_TIMEOUT_S,
        "portrait holes hide",
    )
    if hide_problems or not isinstance(hidden, dict):
        return ["portrait holes hide", *hide_problems[:12]]
    hidden_fit = portrait_fit_problems(cdp)
    if hidden_fit:
        return ["portrait holes hidden overflow", *hidden_fit]
    hidden_covered = coverage_problems(cdp, False)
    if hidden_covered:
        return ["portrait holes hidden coverage", *hidden_covered]
    closed = closed_inspector_problems(cdp)
    if closed:
        return ["portrait holes closed inspector", *closed]
    return []


def _q5_tools_point_expr(tool_name: str) -> str:
    return (
        "(function(){"
        "var sheet=document.getElementById('toolsSheet');"
        "if(!sheet) return 'missing toolsSheet';"
        "if(sheet.hidden){"
        "var openers=document.querySelectorAll('[data-action=\"toolsMenu\"]');"
        "var opener=null;"
        "for(var i=0;i<openers.length;i++){"
        "var st=getComputedStyle(openers[i]);"
        "var r=openers[i].getBoundingClientRect();"
        "if(st.display==='none'||st.visibility==='hidden'||r.width<1||r.height<1) continue;"
        "opener=openers[i];break;"
        "}"
        "if(!opener) return 'missing toolsMenu';"
        "opener.click();"
        "}"
        "var buttons=document.querySelectorAll('#sheetTools button');"
        "var b=null;"
        "for(var j=0;j<buttons.length;j++){"
        "var span=buttons[j].querySelector('span');"
        f"if(span&&span.textContent==={json.dumps(tool_name)}){{b=buttons[j];break;}}"
        "}"
        "if(!b) return 'missing';"
        "var st=getComputedStyle(b);"
        "if(st.display==='none'||st.visibility==='hidden') return 'hidden';"
        "var r=b.getBoundingClientRect();"
        "if(r.width<1||r.height<1) return 'empty';"
        "return JSON.stringify({x:r.left+r.width/2,y:r.top+r.height/2,w:r.width,h:r.height});"
        "})()"
    )


def _q5_sketch_l_profile_and_extrude(
    cdp: Cdp,
    origin: str,
    leg_a_mm: float,
    leg_b_mm: float,
    wall_mm: float,
    extrude_depth_mm: float,
) -> tuple[dict[str, Any] | None, list[str]]:
    """Sketch 6-vertex 90° L-profile with 4 mm wall thickness on XY and Blind Extrude."""
    problems = _delete_default_body(cdp, origin)
    if problems:
        return None, ["q5 clear body", *problems]
    problems = tap_point(cdp, create_point_expr('[data-action="newSketch"]'), "q5 newSketch")
    if problems:
        return None, ["q5 newSketch", *problems]
    problems = tap_selector(cdp, '#originPlanes [data-plane="xy"]', "q5 pick Top XY")
    if problems:
        return None, ["q5 pick xy", *problems]
    problems = tap_point(cdp, _q5_tools_point_expr("Line"), "q5 sketchLine")
    if problems:
        return None, ["q5 sketchLine", *problems]
    loop_uv = (
        (0.0, 0.0),
        (leg_a_mm, 0.0),
        (leg_a_mm, wall_mm),
        (wall_mm, wall_mm),
        (wall_mm, leg_b_mm),
        (0.0, leg_b_mm),
    )
    for u_val, v_val in loop_uv:
        placed, place_err = eval_expr(
            cdp,
            f"Boolean(window.__cadcamSketch && window.__cadcamSketch.placeLineVertex({u_val}, {v_val}))",
        )
        if place_err or placed is not True:
            return None, [f"q5 placeLineVertex({u_val},{v_val}) {placed or place_err}"]
    problems = tap_selector(cdp, "#sketchConfirm", "q5 line confirm")
    if problems:
        return None, ["q5 line confirm", *problems]
    problems = tap_selector(cdp, '#finishBar [data-action="finishSketch"]', "q5 finishSketch")
    if problems:
        return None, ["q5 finishSketch", *problems]
    problems = tap_point(cdp, _q5_tools_point_expr("Extrude (Push/Pull)"), "q5 sketchExtrude")
    if problems:
        return None, ["q5 sketchExtrude", *problems]
    edited, edit_err = eval_expr(cdp, edit_expr("sketchDepth", num_text(extrude_depth_mm)))
    if edit_err or edited != "edited":
        return None, [f"q5 sketchDepth {edited or edit_err}"]
    problems = tap_selector(cdp, "#sketchConfirm", "q5 extrude confirm")
    if problems:
        return None, ["q5 extrude confirm", *problems]
    state, wait_problems = wait_hole_state(
        cdp,
        origin,
        lambda s: (
            int(s.get("bodyCount") or 0) == 1
            and s.get("occtGate") is True
            and s.get("gateOcct") == "PASS"
            and s.get("unitsPass") is True
        ),
        PAGE_TIMEOUT_S,
        f"q5 extrude {extrude_depth_mm}mm",
    )
    if wait_problems or not isinstance(state, dict):
        return None, [f"q5 extrude {extrude_depth_mm}mm", *wait_problems[:12]]
    return state, []


def _q5_find_planar_face(
    cdp: Cdp, want_outward: tuple[float, float, float], body_id: str | None = None
) -> tuple[str, list[str]]:
    arg = json.dumps(body_id) if body_id else ""
    raw, err = eval_expr(
        cdp,
        f"JSON.stringify(window.__cadcamSketch && typeof window.__cadcamSketch.faces==='function' ? window.__cadcamSketch.faces({arg}) : [])",
    )
    if err or not isinstance(raw, str) or not raw.startswith("["):
        return "", [f"q5 faces {raw or err}"]
    try:
        faces = json.loads(raw)
    except json.JSONDecodeError:
        return "", [f"q5 faces json {raw[:200]}"]
    best_id = ""
    best_area = -1.0
    wx, wy, wz = want_outward
    for face in faces:
        if not isinstance(face, dict):
            continue
        out = face.get("outward")
        if not isinstance(out, list) or len(out) < 3:
            continue
        dot = float(out[0]) * wx + float(out[1]) * wy + float(out[2]) * wz
        area = float(face.get("uSpan") or 0.0) * float(face.get("vSpan") or 0.0)
        if dot > 0.99 and area > best_area:
            best_area = area
            best_id = str(face.get("id") or "")
    if not best_id:
        return "", [f"q5 face not found for outward {want_outward} in {raw[:240]}"]
    return best_id, []


def run_portrait_q5_lbracket(cdp: Cdp, origin: str) -> list[str]:
    """390x844 Q5 phone acceptance L-bracket rebuild: sketch -> Blind Extrude -> Union/Cut -> STL/3MF."""
    try:
        set_portrait(cdp)
    except (RuntimeError, TimeoutError, OSError) as exc:
        return [f"q5 portrait emulation failed: {exc}"]
    url = origin + "/"
    print(f"load portrait_q5_lbracket {url}", flush=True)
    _loaded, load_problems = wait_for_case(cdp, origin, url, PAGE_TIMEOUT_S)
    if load_problems:
        return ["q5 load", *load_problems[:20]]

    # Locked by Q5 (mvp/requirements.md #150 @ a38d89d & prompts/antigravity-l-bracket-rebuild.md):
    wall_mm = 4.0
    disc_thickness_mm = 4.0
    # TBD test-only parameters (non-Blink values; not baked into app):
    leg_a_mm = 44.0  # TBD leg A length
    leg_b_mm = 36.0  # TBD leg B length
    leg_w_mm = 28.0  # TBD leg width
    disc_dia_mm = 12.0  # TBD disc diameter
    disc_u_mm = 34.0  # TBD off-centre U on Leg A (centre is 22)
    disc_v_mm = 8.0   # TBD off-centre V on Leg A (centre is 14)
    hole_dia_mm = 4.0  # TBD hole diameter
    cs_dia_mm = 7.0    # TBD countersink diameter
    cs_ang_deg = 90.0  # TBD countersink angle
    leg_a_holes_uv = ((12.0, 20.0), (22.0, 20.0), (34.0, 21.0))  # 3 CSK holes on Leg A
    leg_b_holes_uv = ((12.0, 14.0), (20.0, 14.0), (28.0, 14.0))  # 3 CSK holes on Leg B

    l_area_mm2 = leg_a_mm * wall_mm + (leg_b_mm - wall_mm) * wall_mm

    # Step 1 & 2A: Sketch 90° L-profile on XY and Blind Extrude to locked 4 mm depth.
    flat4_state, problems = _q5_sketch_l_profile_and_extrude(
        cdp, origin, leg_a_mm, leg_b_mm, wall_mm, wall_mm
    )
    if problems or not isinstance(flat4_state, dict):
        return ["q5 4mm blind extrude", *problems]
    if not _near(flat4_state.get("volumeMm3"), l_area_mm2 * wall_mm, 0.5):
        return [f"q5 4mm extrude volume {flat4_state.get('volumeMm3')!r} want {l_area_mm2 * wall_mm}"]

    # Step 1 & 2B: Sketch 90° L-profile (4 mm wall thickness on both legs) on XY and Blind Extrude to leg_w_mm.
    base_state, problems = _q5_sketch_l_profile_and_extrude(
        cdp, origin, leg_a_mm, leg_b_mm, wall_mm, leg_w_mm
    )
    if problems or not isinstance(base_state, dict):
        return ["q5 base lbracket extrude", *problems]
    base_vol = l_area_mm2 * leg_w_mm
    if not _near(base_state.get("volumeMm3"), base_vol, 0.5):
        return [f"q5 base volume {base_state.get('volumeMm3')!r} want {base_vol}"]

    # Step 3: Disc — sketch a circle off-centre on Leg A, Blind Extrude 4 mm, Union onto Leg A.
    leg_a_face, problems = _q5_find_planar_face(cdp, (0.0, -1.0, 0.0))
    if problems:
        return problems
    problems = tap_point(cdp, create_point_expr('[data-action="newSketch"]'), "q5 disc newSketch")
    if problems:
        return ["q5 disc newSketch", *problems]
    tapped_face, tap_err = eval_expr(
        cdp,
        f"Boolean(window.__cadcamSketch && window.__cadcamSketch.tapFace({json.dumps(leg_a_face)}))",
    )
    if tap_err or tapped_face is not True:
        return [f"q5 disc tapFace {tapped_face or tap_err}"]
    problems = tap_point(cdp, _q5_tools_point_expr("Circle"), "q5 sketchCircle")
    if problems:
        return ["q5 sketchCircle", *problems]
    placed_center, center_err = eval_expr(
        cdp,
        f"Boolean(window.__cadcamSketch && window.__cadcamSketch.placeCircleCenter({disc_u_mm}, {disc_v_mm}))",
    )
    if center_err or placed_center is not True:
        return [f"q5 placeCircleCenter {placed_center or center_err}"]
    edited, edit_err = eval_expr(cdp, edit_expr("sketchD", num_text(disc_dia_mm)))
    if edit_err or edited != "edited":
        return [f"q5 sketchD {edited or edit_err}"]
    problems = tap_selector(cdp, "#sketchConfirm", "q5 circle confirm")
    if problems:
        return ["q5 circle confirm", *problems]
    problems = tap_selector(cdp, '#finishBar [data-action="finishSketch"]', "q5 disc finishSketch")
    if problems:
        return ["q5 disc finishSketch", *problems]
    problems = tap_point(cdp, _q5_tools_point_expr("Extrude (Push/Pull)"), "q5 disc sketchExtrude")
    if problems:
        return ["q5 disc sketchExtrude", *problems]
    edited, edit_err = eval_expr(cdp, edit_expr("sketchDepth", num_text(disc_thickness_mm)))
    if edit_err or edited != "edited":
        return [f"q5 disc sketchDepth {edited or edit_err}"]
    problems = tap_selector(
        cdp, '[data-action="sketchExtrudeMode"][data-mode="new"]', "q5 disc mode new"
    )
    if problems:
        return ["q5 disc mode new", *problems]
    problems = tap_selector(cdp, "#sketchConfirm", "q5 disc extrude confirm")
    if problems:
        return ["q5 disc extrude confirm", *problems]
    disc_extruded, wait_problems = wait_hole_state(
        cdp,
        origin,
        lambda s: (
            int(s.get("bodyCount") or 0) == 2
            and s.get("occtGate") is True
            and s.get("gateOcct") == "PASS"
            and s.get("unitsPass") is True
        ),
        PAGE_TIMEOUT_S,
        "q5 disc extrude 4mm",
    )
    if wait_problems or not isinstance(disc_extruded, dict):
        return ["q5 disc extrude 4mm", *wait_problems[:12]]
    body_ids = disc_extruded.get("bodyIds") or []
    if not isinstance(body_ids, list) or len(body_ids) != 2:
        return [f"q5 disc bodyIds {body_ids!r}"]
    picked_pair, pick_err = eval_expr(
        cdp,
        "(function(){"
        "var item=document.querySelector('[data-action=\"select\"][data-mode=\"item\"]');"
        "if(item) item.click();"
        "var buttons=document.querySelectorAll('[data-action=\"boolean\"][data-op=\"union\"]');"
        "var picked=null;"
        "for(var i=0;i<buttons.length;i++){if(!buttons[i].disabled){picked=buttons[i];break;}}"
        "if(!picked) return 'disabled';"
        "picked.click();"
        "return 'clicked';"
        "})()",
    )
    if pick_err or picked_pair != "clicked":
        return [f"q5 disc union click {picked_pair or pick_err}"]
    unioned, union_problems = wait_boolean(cdp, origin, "union", PAGE_TIMEOUT_S)
    if union_problems or not isinstance(unioned, dict):
        return ["q5 disc union", *union_problems[:12]]
    want_union_vol = base_vol + math.pi * (disc_dia_mm / 2.0) ** 2 * disc_thickness_mm
    if (
        int(unioned.get("bodyCount") or 0) != 1
        or unioned.get("unitsPass") is not True
        or unioned.get("occtGate") is not True
        or not _near(unioned.get("volumeMm3"), want_union_vol, 1.5)
    ):
        return [
            f"q5 union state bodyCount={unioned.get('bodyCount')!r} "
            f"vol={unioned.get('volumeMm3')!r} want={want_union_vol:.3f}"
        ]

    # Step 4: Cut 3 CSK holes on Leg A and 3 CSK holes on Leg B (6 CSK holes total).
    problems = tap_point(cdp, create_point_expr('[data-action="holeTool"]'), "q5 holeTool")
    if problems:
        return ["q5 holeTool", *problems]
    problems = tap_selector(cdp, "#dimToggle", "q5 open dim sheet")
    if problems:
        return ["q5 open dim sheet", *problems]
    for field, val in (
        ("holeDia", hole_dia_mm),
        ("holeCsDia", cs_dia_mm),
        ("holeCsAng", cs_ang_deg),
    ):
        edited, edit_err = eval_expr(cdp, edit_expr(field, num_text(val)))
        if edit_err or edited != "edited":
            return [f"q5 {field} {edited or edit_err}"]

    hole_specs = [
        *(("A", (0.0, -1.0, 0.0), uv) for uv in leg_a_holes_uv),
        *(("B", (-1.0, 0.0, 0.0), uv) for uv in leg_b_holes_uv),
    ]
    after_holes: dict[str, Any] | None = None
    for index, (leg_label, outward, (u_val, v_val)) in enumerate(hole_specs):
        face_id, face_problems = _q5_find_planar_face(cdp, outward)
        if face_problems:
            return [f"q5 hole {index + 1} leg {leg_label}", *face_problems]
        selected_face, sel_err = eval_expr(
            cdp,
            f"Boolean(window.__cadcamSketch && window.__cadcamSketch.tapHoleFace({json.dumps(face_id)}))",
        )
        if sel_err or selected_face is not True:
            return [f"q5 hole {index + 1} tapHoleFace {selected_face or sel_err}"]
        for field, val in (("holeU", u_val), ("holeV", v_val)):
            edited, edit_err = eval_expr(cdp, edit_expr(field, num_text(val)))
            if edit_err or edited != "edited":
                return [f"q5 hole {index + 1} {field} {edited or edit_err}"]
        shown, shown_err = eval_expr(cdp, reveal_expr("#holeApply"))
        if shown_err or shown != "shown":
            return [f"q5 hole {index + 1} reveal {shown or shown_err}"]
        problems = tap_selector(cdp, "#holeApply", f"q5 hole {index + 1} cut")
        if problems:
            return problems
        want_count = index + 1
        after_holes, cut_problems = wait_hole_state(
            cdp,
            origin,
            lambda s, c=want_count: (
                int(s.get("holeCount") or 0) == c
                and s.get("occtGate") is True
                and s.get("gateOcct") == "PASS"
                and s.get("unitsPass") is True
                and int(s.get("bodyCount") or 0) == 1
            ),
            PAGE_TIMEOUT_S,
            f"q5 hole {want_count} leg {leg_label}",
        )
        if cut_problems or not isinstance(after_holes, dict):
            return [f"q5 hole {want_count} leg {leg_label}", *cut_problems[:12]]
        hole_log = after_holes.get("holeLog") or []
        if not isinstance(hole_log, list) or len(hole_log) != want_count:
            return [f"q5 holeLog len {len(hole_log) if isinstance(hole_log, list) else hole_log!r}"]
        entry = hole_log[-1] if isinstance(hole_log[-1], dict) else {}
        if (
            entry.get("countersink") is not True
            or entry.get("depthMode") != "through"
            or abs(float(entry.get("depthMm") or 0.0) - wall_mm) > 0.25
            or not (float(entry.get("volumeAfter") or 0.0) < float(entry.get("volumeBefore") or 0.0))
        ):
            return [f"q5 hole {want_count} entry {entry!r}"]

    if not isinstance(after_holes, dict):
        return ["q5 holes missing final state"]
    if after_holes.get("exportAllowed") is not True or after_holes.get("exportDisabled") is True:
        return [f"q5 export blocked {after_holes!r}"]

    # Step 6: Export STL and 3MF when Module.gate() allows. Units stay mm. No printer send.
    for fmt, ext in (("STL", ".stl"), ("3MF", ".3mf")):
        exported, exp_err = eval_expr(
            cdp,
            "(function(){"
            "window.__cadcamLastDownload=null;"
            f"var b=document.querySelector('[data-action=\"exportFmt\"][data-fmt=\"{fmt}\"]');"
            "if(!b) return 'missing';"
            "b.click();"
            "return JSON.stringify(window.__cadcamLastDownload||null);"
            "})()",
        )
        if exp_err or not isinstance(exported, str) or not exported.startswith("{"):
            return [f"q5 export {fmt} {exported or exp_err}"]
        info = json.loads(exported)
        if not str(info.get("name") or "").endswith(ext):
            return [f"q5 export {fmt} name {info!r}"]
        if int(info.get("byteLength") or 0) <= 84:
            return [f"q5 export {fmt} bytes {info!r}"]
        if fmt == "3MF":
            head = info.get("head") or []
            if not isinstance(head, list) or len(head) < 2 or head[0] != 80 or head[1] != 75:
                return [f"q5 export 3MF header {head!r}"]
    units_text, units_err = eval_expr(
        cdp,
        "(function(){var u=document.getElementById('statusUnits');return u?u.textContent.trim():'';})()",
    )
    if units_err or units_text != "mm":
        return [f"q5 statusUnits {units_text or units_err!r}"]
    print(
        f"portrait_q5_lbracket: 90deg L ({leg_a_mm:g}x{leg_b_mm:g}x{leg_w_mm:g} mm, wall {wall_mm:g} mm), "
        f"off-centre disc D={disc_dia_mm:g}x{disc_thickness_mm:g} mm Union, "
        f"6 CSK holes Cut (3/leg), volume {after_holes.get('volumeMm3'):.3f} mm3, STL+3MF exported, units mm",
        flush=True,
    )
    return []


def run_portrait_q5_truck(cdp: Cdp, origin: str) -> list[str]:
    """390x844 Q5 11-part toy-truck MVP: sketch -> Blind Extrude (New/Join/Cut) -> Union/Cut -> STL/3MF."""
    try:
        set_portrait(cdp)
    except (RuntimeError, TimeoutError, OSError) as exc:
        return [f"truck portrait emulation failed: {exc}"]
    url = origin + "/"
    print(f"load portrait_q5_truck {url}", flush=True)
    _loaded, load_problems = wait_for_case(cdp, origin, url, PAGE_TIMEOUT_S)
    if load_problems:
        return ["truck load", *load_problems[:20]]

    problems = _delete_default_body(cdp, origin)
    if problems:
        return ["truck clear default body", *problems]

    def check_op(label: str, want_bodies: int) -> tuple[dict[str, Any] | None, list[str]]:
        st, wait_probs = wait_hole_state(
            cdp,
            origin,
            lambda s, n=want_bodies: (
                int(s.get("bodyCount") or 0) == n
                and s.get("occtGate") is True
                and s.get("gateOcct") == "PASS"
                and s.get("unitsPass") is True
                and not s.get("lastError")
            ),
            PAGE_TIMEOUT_S,
            f"truck {label}",
        )
        if wait_probs or not isinstance(st, dict):
            return None, [f"truck {label}", *wait_probs[:12]]
        units_txt, u_err = eval_expr(
            cdp,
            "(function(){var u=document.getElementById('statusUnits');return u?u.textContent.trim():'';})()",
        )
        if u_err or units_txt != "mm":
            return None, [f"truck {label} units {units_txt or u_err!r}"]
        return st, []

    def sketch_circle_and_extrude(
        label: str,
        face_id: str,
        diameter_mm: float,
        depth_mm: float,
        mode: str,
        want_bodies: int,
        uv_center: tuple[float, float] | None = None,
    ) -> tuple[dict[str, Any] | None, list[str]]:
        probs = tap_point(cdp, create_point_expr('[data-action="newSketch"]'), f"truck {label} newSketch")
        if probs:
            return None, [f"truck {label} newSketch", *probs]
        tapped, tap_err = eval_expr(
            cdp,
            f"Boolean(window.__cadcamSketch && window.__cadcamSketch.tapFace({json.dumps(face_id)}))",
        )
        if tap_err or tapped is not True:
            return None, [f"truck {label} tapFace({face_id}) {tapped or tap_err}"]
        probs = tap_point(cdp, _q5_tools_point_expr("Circle"), f"truck {label} Circle")
        if probs:
            return None, [f"truck {label} Circle", *probs]
        if uv_center is not None:
            placed, place_err = eval_expr(
                cdp,
                f"Boolean(window.__cadcamSketch && window.__cadcamSketch.placeCircleCenter({uv_center[0]}, {uv_center[1]}))",
            )
            if place_err or placed is not True:
                return None, [f"truck {label} placeCircleCenter {placed or place_err}"]
        edited, edit_err = eval_expr(cdp, edit_expr("sketchD", num_text(diameter_mm)))
        if edit_err or edited != "edited":
            return None, [f"truck {label} sketchD {edited or edit_err}"]
        probs = tap_selector(cdp, "#sketchConfirm", f"truck {label} circle confirm")
        if probs:
            return None, [f"truck {label} circle confirm", *probs]
        probs = tap_selector(cdp, '#finishBar [data-action="finishSketch"]', f"truck {label} finishSketch")
        if probs:
            return None, [f"truck {label} finishSketch", *probs]
        probs = tap_point(cdp, _q5_tools_point_expr("Extrude (Push/Pull)"), f"truck {label} Extrude")
        if probs:
            return None, [f"truck {label} Extrude", *probs]
        edited, edit_err = eval_expr(cdp, edit_expr("sketchDepth", num_text(depth_mm)))
        if edit_err or edited != "edited":
            return None, [f"truck {label} sketchDepth {edited or edit_err}"]
        probs = tap_selector(
            cdp, f'[data-action="sketchExtrudeMode"][data-mode="{mode}"]', f"truck {label} mode {mode}"
        )
        if probs:
            return None, [f"truck {label} mode {mode}", *probs]
        probs = tap_selector(cdp, "#sketchConfirm", f"truck {label} extrude confirm")
        if probs:
            return None, [f"truck {label} extrude confirm", *probs]
        return check_op(label, want_bodies)

    # 1. Chassis/body (PLA): sketch 80x30 mm on Top XY, Blind Extrude 6 mm.
    problems = tap_point(cdp, create_point_expr('[data-action="newSketch"]'), "truck chassis newSketch")
    if problems:
        return ["truck chassis newSketch", *problems]
    problems = tap_selector(cdp, '#originPlanes [data-plane="xy"]', "truck chassis pick xy")
    if problems:
        return ["truck chassis pick xy", *problems]
    problems = tap_point(cdp, _q5_tools_point_expr("Rectangle"), "truck chassis Rectangle")
    if problems:
        return ["truck chassis Rectangle", *problems]
    for field, val in (("sketchL", 80.0), ("sketchW", 30.0)):
        edited, edit_err = eval_expr(cdp, edit_expr(field, num_text(val)))
        if edit_err or edited != "edited":
            return [f"truck chassis {field} {edited or edit_err}"]
    problems = tap_selector(cdp, "#sketchConfirm", "truck chassis rect confirm")
    if problems:
        return ["truck chassis rect confirm", *problems]
    problems = tap_selector(cdp, '#finishBar [data-action="finishSketch"]', "truck chassis finishSketch")
    if problems:
        return ["truck chassis finishSketch", *problems]
    problems = tap_point(cdp, _q5_tools_point_expr("Extrude (Push/Pull)"), "truck chassis Extrude")
    if problems:
        return ["truck chassis Extrude", *problems]
    edited, edit_err = eval_expr(cdp, edit_expr("sketchDepth", num_text(6.0)))
    if edit_err or edited != "edited":
        return [f"truck chassis sketchDepth {edited or edit_err}"]
    problems = tap_selector(cdp, "#sketchConfirm", "truck chassis extrude confirm")
    if problems:
        return ["truck chassis extrude confirm", *problems]
    chassis_state, problems = check_op("chassis 80x30x6", 1)
    if problems or not isinstance(chassis_state, dict):
        return problems
    if not _near(chassis_state.get("volumeMm3"), 80.0 * 30.0 * 6.0, 1.0):
        return [f"truck chassis volume {chassis_state.get('volumeMm3')!r}"]

    # Two Ø4.4 through-holes across the 30 mm width, 10 mm in from each end, 3 mm up, via Cut.
    xz_face, problems = _q5_find_planar_face(cdp, (0.0, -1.0, 0.0))
    if problems:
        return ["truck chassis xz face", *problems]
    for hole_idx, u_mm in enumerate((10.0, 70.0), start=1):
        _st, problems = sketch_circle_and_extrude(
            f"chassis hole {hole_idx}", xz_face, 4.4, 30.0, "cut", 1, uv_center=(u_mm, 3.0)
        )
        if problems:
            return problems
        xz_face, problems = _q5_find_planar_face(cdp, (0.0, -1.0, 0.0))
        if problems:
            return [f"truck chassis xz face after hole {hole_idx}", *problems]

    # 2. Cab (PLA): sketch 30x30 mm on chassis top at front, Blind Extrude 25 mm, Union into chassis.
    top_face, problems = _q5_find_planar_face(cdp, (0.0, 0.0, 1.0))
    if problems:
        return ["truck chassis top face", *problems]
    problems = tap_point(cdp, create_point_expr('[data-action="newSketch"]'), "truck cab newSketch")
    if problems:
        return ["truck cab newSketch", *problems]
    tapped_top, tap_err = eval_expr(
        cdp,
        f"Boolean(window.__cadcamSketch && window.__cadcamSketch.tapFace({json.dumps(top_face)}))",
    )
    if tap_err or tapped_top is not True:
        return [f"truck cab tapFace {tapped_top or tap_err}"]
    problems = tap_point(cdp, _q5_tools_point_expr("Rectangle"), "truck cab Rectangle")
    if problems:
        return ["truck cab Rectangle", *problems]
    for field, val in (("sketchL", 30.0), ("sketchW", 30.0)):
        edited, edit_err = eval_expr(cdp, edit_expr(field, num_text(val)))
        if edit_err or edited != "edited":
            return [f"truck cab {field} {edited or edit_err}"]
    problems = tap_selector(cdp, "#sketchConfirm", "truck cab rect confirm")
    if problems:
        return ["truck cab rect confirm", *problems]
    problems = tap_selector(cdp, '#finishBar [data-action="finishSketch"]', "truck cab finishSketch")
    if problems:
        return ["truck cab finishSketch", *problems]
    problems = tap_point(cdp, _q5_tools_point_expr("Extrude (Push/Pull)"), "truck cab Extrude")
    if problems:
        return ["truck cab Extrude", *problems]
    edited, edit_err = eval_expr(cdp, edit_expr("sketchDepth", num_text(25.0)))
    if edit_err or edited != "edited":
        return [f"truck cab sketchDepth {edited or edit_err}"]
    problems = tap_selector(
        cdp, '[data-action="sketchExtrudeMode"][data-mode="new"]', "truck cab mode new"
    )
    if problems:
        return ["truck cab mode new", *problems]
    problems = tap_selector(cdp, "#sketchConfirm", "truck cab extrude confirm")
    if problems:
        return ["truck cab extrude confirm", *problems]
    _cab_new, problems = check_op("cab extrude 25mm", 2)
    if problems:
        return problems
    unioned_click, u_click_err = eval_expr(
        cdp,
        "(function(){"
        "var item=document.querySelector('[data-action=\"select\"][data-mode=\"item\"]');"
        "if(item) item.click();"
        "var buttons=document.querySelectorAll('[data-action=\"boolean\"][data-op=\"union\"]');"
        "var picked=null;"
        "for(var i=0;i<buttons.length;i++){if(!buttons[i].disabled){picked=buttons[i];break;}}"
        "if(!picked) return 'disabled';"
        "picked.click();"
        "return 'clicked';"
        "})()",
    )
    if u_click_err or unioned_click != "clicked":
        return [f"truck cab union click {unioned_click or u_click_err}"]
    _unioned_bool, union_probs = wait_boolean(cdp, origin, "union", PAGE_TIMEOUT_S)
    if union_probs:
        return ["truck cab union wait", *union_probs[:12]]
    body_state, problems = check_op("cab union into chassis", 1)
    if problems or not isinstance(body_state, dict):
        return problems
    want_body_vol = 80.0 * 30.0 * 6.0 - 2.0 * (math.pi * 2.2 * 2.2 * 30.0) + 30.0 * 30.0 * 25.0
    if not _near(body_state.get("volumeMm3"), want_body_vol, 2.5):
        return [f"truck body volume {body_state.get('volumeMm3')!r} want {want_body_vol:.3f}"]
    chassis_id = str((body_state.get("bodyIds") or ["b1"])[0])
    horiz_face, problems = _q5_find_planar_face(cdp, (0.0, 0.0, 1.0), body_id=chassis_id)
    if problems:
        return ["truck chassis horiz face", *problems]

    # 3. Axles x2 (PLA): sketch a Ø4 circle, Blind Extrude 44 mm (New).
    for axle_idx, u_mm in enumerate((10.0, 40.0), start=1):
        _ax_st, problems = sketch_circle_and_extrude(
            f"axle {axle_idx}",
            horiz_face,
            4.0,
            44.0,
            "new",
            1 + axle_idx,
            uv_center=(u_mm, 15.0),
        )
        if problems:
            return problems

    # 4. Wheel hubs x4 (PLA): sketch a Ø16 circle, Blind Extrude 8 mm. Bore Ø4.2 via Cut.
    for hub_idx in range(1, 5):
        want_count = 3 + hub_idx
        u_mm = float(hub_idx * 22)
        v_mm = 50.0
        hub_st, problems = sketch_circle_and_extrude(
            f"hub {hub_idx} outer",
            horiz_face,
            16.0,
            8.0,
            "new",
            want_count,
            uv_center=(u_mm, v_mm),
        )
        if problems or not isinstance(hub_st, dict):
            return problems
        hub_ids = hub_st.get("bodyIds") or []
        if not isinstance(hub_ids, list) or len(hub_ids) != want_count:
            return [f"truck hub {hub_idx} bodyIds {hub_ids!r}"]
        hub_id = str(hub_ids[-1])
        hub_top, problems = _q5_find_planar_face(cdp, (0.0, 0.0, 1.0), body_id=hub_id)
        if problems:
            return [f"truck hub {hub_idx} top face", *problems]
        _bore_st, problems = sketch_circle_and_extrude(
            f"hub {hub_idx} bore",
            hub_top,
            4.2,
            8.0,
            "cut",
            want_count,
        )
        if problems:
            return problems

    # 5. Tires x4 (TPU): ring OD 24 / ID 15.6 / width 8. ID via Cut. 0.2 stretch on the hub.
    for tire_idx in range(1, 5):
        want_count = 7 + tire_idx
        u_mm = float(tire_idx * 30)
        v_mm = 85.0
        tire_st, problems = sketch_circle_and_extrude(
            f"tire {tire_idx} outer",
            horiz_face,
            24.0,
            8.0,
            "new",
            want_count,
            uv_center=(u_mm, v_mm),
        )
        if problems or not isinstance(tire_st, dict):
            return problems
        tire_ids = tire_st.get("bodyIds") or []
        if not isinstance(tire_ids, list) or len(tire_ids) != want_count:
            return [f"truck tire {tire_idx} bodyIds {tire_ids!r}"]
        tire_id = str(tire_ids[-1])
        tire_top, problems = _q5_find_planar_face(cdp, (0.0, 0.0, 1.0), body_id=tire_id)
        if problems:
            return [f"truck tire {tire_idx} top face", *problems]
        _id_st, problems = sketch_circle_and_extrude(
            f"tire {tire_idx} id",
            tire_top,
            15.6,
            8.0,
            "cut",
            want_count,
        )
        if problems:
            return problems
        tagged, tag_err = eval_expr(
            cdp,
            "(function(){"
            "while(document.querySelector('#partList .part-row.is-on')){"
            "document.querySelector('#partList .part-row.is-on').click();"
            "}"
            f"var row=document.querySelector('#partList [data-part-id={json.dumps(tire_id)}]');"
            "if(!row) return 'missing row';"
            "row.click();"
            "var m=document.getElementById('partMaterial');"
            "if(!m) return 'missing select';"
            "m.value='TPU';"
            "m.dispatchEvent(new Event('change',{bubbles:true}));"
            f"var fresh=document.querySelector('#partList [data-part-id={json.dumps(tire_id)}]');"
            "return fresh&&fresh.querySelector('.part-mat')?fresh.querySelector('.part-mat').textContent.trim():'';"
            "})()",
        )
        if tag_err or tagged != "TPU":
            return [f"truck tire {tire_idx} TPU tag {tagged or tag_err!r}"]

    # Verify 11 parts (1 body + 2 axles + 4 hubs + 4 tires; 7 PLA + 4 TPU) and mixed-material Combine refusal.
    parts_raw, parts_err = eval_expr(
        cdp,
        "JSON.stringify(window.__cadcamSketch && window.__cadcamSketch.state ? window.__cadcamSketch.state().parts : [])",
    )
    if parts_err or not isinstance(parts_raw, str) or not parts_raw.startswith("["):
        return [f"truck parts state {parts_raw or parts_err!r}"]
    parts = json.loads(parts_raw)
    if len(parts) != 11:
        return [f"truck part count {len(parts)} != 11: {parts!r}"]
    pla_parts = [p for p in parts if isinstance(p, dict) and p.get("material") == "PLA"]
    tpu_parts = [p for p in parts if isinstance(p, dict) and p.get("material") == "TPU"]
    if len(pla_parts) != 7 or len(tpu_parts) != 4:
        return [f"truck materials PLA={len(pla_parts)} TPU={len(tpu_parts)} parts={parts!r}"]

    # Do not Combine a hub with a tire (mixed materials; sourced in mvp/acceptance-a-b.md).
    hub_part_id = str(parts[3].get("id") or "")
    tire_part_id = str(parts[7].get("id") or "")
    mixed_note, mixed_err = eval_expr(
        cdp,
        "(function(){"
        "while(document.querySelector('#partList .part-row.is-on')){"
        "document.querySelector('#partList .part-row.is-on').click();"
        "}"
        f"var r1=document.querySelector('#partList [data-part-id={json.dumps(hub_part_id)}]');"
        "if(!r1) return 'missing r1';"
        "r1.click();"
        f"var r2=document.querySelector('#partList [data-part-id={json.dumps(tire_part_id)}]');"
        "if(!r2) return 'missing r2';"
        "r2.click();"
        "var btn=document.getElementById('combineBtn');"
        "if(!btn||btn.disabled) return 'combine disabled';"
        "btn.click();"
        "var note=document.getElementById('assemblyNote');"
        "return note?note.textContent.trim():'';"
        "})()",
    )
    if mixed_err or "different materials" not in str(mixed_note or ""):
        return [f"truck mixed hub+tire combine note {mixed_note or mixed_err!r}"]

    final_state, problems = check_op("final 11-part truck", 11)
    if problems or not isinstance(final_state, dict):
        return problems
    if final_state.get("exportAllowed") is not True or final_state.get("exportDisabled") is True:
        return [f"truck export blocked {final_state!r}"]

    # 7. Export STL and 3MF when C++ Module.gate() passes. Units stay mm.
    # Skip numeric --expect-size / --expect-volume on the truck files.
    for fmt, ext in (("STL", ".stl"), ("3MF", ".3mf")):
        exported, exp_err = eval_expr(
            cdp,
            "(function(){"
            "window.__cadcamLastDownload=null;"
            f"var b=document.querySelector('[data-action=\"exportFmt\"][data-fmt=\"{fmt}\"]');"
            "if(!b) return 'missing';"
            "b.click();"
            "return JSON.stringify(window.__cadcamLastDownload||null);"
            "})()",
        )
        if exp_err or not isinstance(exported, str) or not exported.startswith("{"):
            return [f"truck export {fmt} {exported or exp_err}"]
        info = json.loads(exported)
        if not str(info.get("name") or "").endswith(ext):
            return [f"truck export {fmt} name {info!r}"]
        if int(info.get("byteLength") or 0) <= 84:
            return [f"truck export {fmt} bytes {info!r}"]
        if fmt == "3MF":
            head = info.get("head") or []
            if not isinstance(head, list) or len(head) < 2 or head[0] != 80 or head[1] != 75:
                return [f"truck export 3MF header {head!r}"]
    units_text, units_err = eval_expr(
        cdp,
        "(function(){var u=document.getElementById('statusUnits');return u?u.textContent.trim():'';})()",
    )
    if units_err or units_text != "mm":
        return [f"truck statusUnits {units_text or units_err!r}"]
    print(
        f"portrait_q5_truck: 11 parts (1 body PLA + 2 axles PLA + 4 hubs PLA + 4 tires TPU), "
        f"volume {final_state.get('volumeMm3'):.3f} mm3, STL+3MF exported, units mm",
        flush=True,
    )
    print("TRUCK_MVP_DONE", flush=True)
    return []


def click_boolean(cdp: Cdp, op: str, timeout: float = 30) -> str:
    expression = (
        "(function(){"
        f"var b=document.querySelector('[data-action=\"boolean\"][data-op=\"{op}\"]');"
        "if(!b) return 'missing';"
        "if(b.disabled) return 'disabled';"
        "b.click();"
        "return 'clicked';"
        "})()"
    )
    result = cdp.call(
        "Runtime.evaluate",
        {"expression": expression, "returnByValue": True},
        timeout=timeout,
    )
    remote = result.get("result") or {}
    value = remote.get("value")
    return str(value) if value is not None else ""


def wait_boolean(
    cdp: Cdp, origin: str, op: str, timeout: float
) -> tuple[dict[str, Any] | None, list[str]]:
    deadline = time.time() + timeout
    last: dict[str, Any] | None = None
    while time.time() < deadline:
        cdp.drain(0.5)
        problems = site_problems(cdp.events, origin, cdp.urls)
        payload = eval_state(cdp)
        problems.extend(smoke_notes(payload))
        state = (payload or {}).get("state") if payload else None
        if isinstance(state, dict):
            last = state
            ready = (
                state.get("booleanOp") == op
                and state.get("occtGate") is True
                and not state.get("lastError")
            )
            if ready or state.get("lastError"):
                if state.get("lastError"):
                    problems.append(str(state.get("lastError")))
                return state, problems
        elif problems:
            return last, problems
    return last, [f"timed out waiting for boolean {op}", json.dumps(last)]


BOOLEAN_MM3_TOL = 1e-3

BOOL_PART_EXPR = r"""
(function(){
  var asm = window.__cadcamAssembly ? window.__cadcamAssembly() : null;
  var s = window.__cadcamExportState || {};
  var hintEl = document.getElementById('statusHint');
  var vols = [];
  var parts = asm && asm.parts ? asm.parts : [];
  for (var i = 0; i < parts.length; i++) vols.push(parts[i] && parts[i].volumeMm3);
  return JSON.stringify({
    body: s.bodyCount,
    undo: s.undoDepth,
    op: s.booleanOp || '',
    err: s.lastError || '',
    vol: s.volumeMm3,
    gate: s.occtGate === true,
    units: s.unitsPass === true,
    vols: vols,
    hint: hintEl ? String(hintEl.textContent || '') : ''
  });
})()
"""


def _within_mm3(value: Any, want: float) -> bool:
    try:
        return abs(float(value) - want) <= BOOLEAN_MM3_TOL
    except (TypeError, ValueError):
        return False


def _bool_part_snap(cdp: Cdp) -> tuple[dict[str, Any] | None, str]:
    return _json_eval(cdp, BOOL_PART_EXPR)


def _pair_volume_problems(snap: dict[str, Any], label: str) -> list[str]:
    problems: list[str] = []
    vols = snap.get("vols")
    if not isinstance(vols, list) or len(vols) != 2:
        problems.append(f"{label} volumes {vols!r}")
        return problems
    for vol in vols:
        if not _within_mm3(vol, 8000):
            problems.append(f"{label} box volume {vol!r}")
    if snap.get("gate") is not True or snap.get("units") is not True:
        problems.append(f"{label} gate {snap.get('gate')!r} units {snap.get('units')!r}")
    if int(snap.get("body") or 0) != 2:
        problems.append(f"{label} bodyCount {snap.get('body')!r}")
    return problems


def _undo_restores_pair(cdp: Cdp, before_depth: int, label: str) -> list[str]:
    raw, err = eval_expr(cdp, UNDO_KEY_EXPR)
    parsed, parse_err = _key_state(raw, err)
    if parse_err or not parsed:
        return [f"boolean undo {label} {parse_err or raw!r}"]
    problems: list[str] = []
    if int(parsed.get("body") or 0) != 2:
        problems.append(f"boolean undo {label} bodyCount {parsed.get('body')!r}")
    if int(parsed.get("undo") or 0) != before_depth:
        problems.append(f"boolean undo {label} depth {parsed.get('undo')!r} want {before_depth}")
    snap, snap_err = _bool_part_snap(cdp)
    if snap_err or not snap:
        problems.append(f"boolean undo {label} parts {snap_err or snap!r}")
        return problems
    hint = str(snap.get("hint") or "")
    if hint != "Undo " + label:
        problems.append(f"boolean undo {label} hint {hint!r}")
    problems.extend(_pair_volume_problems(snap, f"boolean undo {label}"))
    if not _within_mm3(snap.get("vol"), 16000):
        problems.append(f"boolean undo {label} scene volume {snap.get('vol')!r}")
    return problems


def union_undo_problems(cdp: Cdp, before_depth: int, done: dict[str, Any]) -> list[str]:
    """Overlap Union is one undo step. Undo restores both 8000 mm3 boxes."""
    problems: list[str] = []
    depth = int(done.get("undoDepth") or 0)
    if depth != before_depth + 1:
        problems.append(f"boolean_union undo depth {depth} want {before_depth + 1}")
    if not _within_mm3(done.get("volumeMm3"), 12000):
        problems.append(f"boolean_union volume {done.get('volumeMm3')!r} want 12000")
    if problems:
        return problems
    return _undo_restores_pair(cdp, before_depth, "Union")


def _select_pair(cdp: Cdp, origin: str, label: str) -> tuple[dict[str, Any] | None, list[str]]:
    press_plain_4(cdp)
    cdp.drain(0.4)
    keyed = eval_state(cdp)
    problems = site_problems(cdp.events, origin, cdp.urls)
    problems.extend(smoke_notes(keyed))
    keyed_state = (keyed or {}).get("state") if keyed else None
    if not isinstance(keyed_state, dict):
        problems.append(f"{label}: no state after the 4 key")
        return None, problems
    if keyed_state.get("selectionMode") != "item" or int(keyed_state.get("selectionCount") or 0) < 2:
        problems.append(
            f"{label}: expected two selected bodies after 4, "
            f"mode {keyed_state.get('selectionMode')!r} count {keyed_state.get('selectionCount')!r}"
        )
    order = keyed_state.get("selectionOrder") or []
    if len(order) < 2:
        problems.append(f"{label}: selection order {order!r}")
    return keyed_state, problems


def overlap_boolean_problems(cdp: Cdp, origin: str) -> list[str]:
    """Union, Cut, and Intersect on the overlap pair. Union undo restores both boxes."""
    for op in ("union", "cut", "intersect"):
        url = origin + "/?pair=overlap"
        print(f"load boolean_{op} {url}", flush=True)
        started = time.time()
        state, problems = wait_for_case(cdp, origin, url, PAGE_TIMEOUT_S)
        if problems or not isinstance(state, dict):
            return [f"boolean_{op} load", *problems[:40]]
        state, problems = _select_pair(cdp, origin, f"boolean_{op}")
        if problems or not isinstance(state, dict):
            return [f"boolean_{op} select", *problems[:40]]
        before_depth = int(state.get("undoDepth") or 0)
        clicked = click_boolean(cdp, op, PAGE_TIMEOUT_S)
        if clicked != "clicked":
            return [f"boolean_{op}: button {clicked}"]
        done, problems = wait_boolean(cdp, origin, op, PAGE_TIMEOUT_S)
        elapsed = time.time() - started
        if not isinstance(done, dict):
            problems.append(f"boolean_{op}: no result state")
        else:
            print(f"boolean_{op}={json.dumps(done, separators=(',', ':'))}", flush=True)
            if done.get("occtGate") is not True or done.get("gateOcct") != "PASS":
                problems.append(f"boolean_{op}: gate {done.get('gateOcct')!r}")
            if done.get("unitsPass") is not True:
                problems.append(f"boolean_{op}: units failed")
            if done.get("exportAllowed") is not True:
                problems.append(f"boolean_{op}: Export is not enabled")
            if int(done.get("bodyCount") or 0) != 1:
                problems.append(f"boolean_{op}: bodyCount {done.get('bodyCount')!r}")
            if done.get("booleanOp") != op:
                problems.append(f"boolean_{op}: op {done.get('booleanOp')!r}")
            if op == "union" and not problems:
                problems.extend(union_undo_problems(cdp, before_depth, done))
        if problems:
            return [f"boolean_{op} ({elapsed:.1f}s)", *problems[:40]]
        print(f"boolean_{op}: gate PASS, {elapsed:.1f}s", flush=True)
    return []


def _boolean_outcome(cdp: Cdp, timeout: float) -> tuple[dict[str, Any] | None, list[str]]:
    """Poll until the op records a result or a kept-inputs error. An error is not a failure by itself."""
    deadline = time.time() + timeout
    last: dict[str, Any] | None = None
    while time.time() < deadline:
        cdp.drain(0.4)
        snap, err = _bool_part_snap(cdp)
        if err or not snap:
            last = None
            continue
        last = snap
        if snap.get("err") or snap.get("op"):
            return snap, []
    return last, ["timed out waiting for boolean outcome", json.dumps(last)]


def disjoint_boolean_problems(cdp: Cdp, origin: str) -> list[str]:
    """Disjoint Intersect stays an empty reject. Cut is a success only when OCCT accepts it."""
    for op in ("intersect", "cut"):
        label = f"boolean_disjoint_{op}"
        url = origin + "/?pair=disjoint"
        print(f"load {label} {url}", flush=True)
        state, problems = wait_for_case(cdp, origin, url, PAGE_TIMEOUT_S)
        if problems or not isinstance(state, dict):
            return [f"{label} load", *problems[:40]]
        state, problems = _select_pair(cdp, origin, label)
        if problems or not isinstance(state, dict):
            return [f"{label} select", *problems[:40]]
        before_depth = int(state.get("undoDepth") or 0)
        if int(state.get("bodyCount") or 0) != 2:
            return [f"{label} bodyCount before {state.get('bodyCount')!r}"]
        clicked = click_boolean(cdp, op, PAGE_TIMEOUT_S)
        if clicked != "clicked":
            return [f"{label}: button {clicked}"]
        done, problems = _boolean_outcome(cdp, PAGE_TIMEOUT_S)
        if problems or not isinstance(done, dict):
            return [f"{label} outcome", *problems[:20]]
        print(f"{label}={json.dumps(done, separators=(',', ':'))}", flush=True)
        err = str(done.get("err") or "")
        if op == "intersect" or err:
            if op == "intersect" and ("empty" not in err or "kept" not in err):
                problems.append(f"{label} message {err!r}")
            elif op == "cut" and "kept" not in err:
                problems.append(f"{label} message {err!r}")
            if int(done.get("body") or 0) != 2:
                problems.append(f"{label} bodyCount {done.get('body')!r}")
            if int(done.get("undo") or 0) != before_depth:
                problems.append(f"{label} undo {done.get('undo')!r} want {before_depth}")
            if done.get("op"):
                problems.append(f"{label} pushed op {done.get('op')!r}")
            problems.extend(_pair_volume_problems(done, label))
        elif done.get("op") == "cut" and int(done.get("body") or 0) == 1:
            if int(done.get("undo") or 0) != before_depth + 1:
                problems.append(f"{label} undo {done.get('undo')!r} want {before_depth + 1}")
            if done.get("gate") is not True or done.get("units") is not True:
                problems.append(f"{label} gate {done.get('gate')!r} units {done.get('units')!r}")
            if not problems:
                problems.extend(_undo_restores_pair(cdp, before_depth, "Cut"))
        else:
            problems.append(f"{label} unsettled {done!r}")
        site = site_problems(cdp.events, origin, cdp.urls)
        if site:
            problems.extend(site[:10])
        if problems:
            return [label, *problems[:40]]
        print(f"{label}: pass", flush=True)
    return []


def response_count(events: list[dict[str, Any]], origin: str) -> int:
    count = 0
    for event in events:
        if event.get("method") != "Network.responseReceived":
            continue
        response = (event.get("params") or {}).get("response") or {}
        if str(response.get("url") or "").startswith(origin):
            count += 1
    return count


def assert_fixture_urls_404(origin: str) -> list[str]:
    """Acceptance fixtures stay in tests/ and are not part of the served site."""
    paths = (
        "/tests/fixtures/lbracket.json",
        "/fixtures/lbracket.json",
        "/tests/fixtures/blink.json",
        "/fixtures/blink.json",
    )
    problems: list[str] = []
    for path in paths:
        url = origin + path
        deadline = time.time() + 5
        while True:
            try:
                with urllib.request.urlopen(url, timeout=5) as response:
                    problems.append(f"{path} returned {response.status}, expected 404")
                break
            except urllib.error.HTTPError as exc:
                if exc.code != 404:
                    problems.append(f"{path} returned {exc.code}, expected 404")
                else:
                    print(f"404 {path}", flush=True)
                break
            except urllib.error.URLError as exc:
                if time.time() < deadline:
                    time.sleep(0.1)
                    continue
                problems.append(f"{path} request failed: {exc}")
                break
    return problems


def run_type_in_resize(cdp: Cdp, origin: str) -> list[str]:
    """Typed mm resize: one undo step, inch display, lock, ellipse note, rollback."""
    try:
        set_portrait(cdp)
    except (RuntimeError, TimeoutError, OSError) as exc:
        return [f"resize emulation failed: {exc}"]
    url = origin + "/?primitive=box"
    print(f"load type_in_resize {url}", flush=True)
    loaded, load_problems = wait_for_case(cdp, origin, url, PAGE_TIMEOUT_S)
    if load_problems or not isinstance(loaded, dict):
        return ["resize load", *load_problems[:20]]
    opened, open_err = eval_expr(cdp, CLICK_DIM_EXPR)
    if open_err or opened != "clicked":
        return [f"resize dim sheet {opened or open_err}"]
    measured, measure_err = eval_expr(
        cdp,
        "(function(){"
        "var b=document.getElementById('lockProportions');"
        "if(!b) return 'missing';"
        "var st=getComputedStyle(b);"
        "var r=b.getBoundingClientRect();"
        "return JSON.stringify({w:r.width,h:r.height,display:st.display,visibility:st.visibility});"
        "})()",
    )
    if measure_err or not isinstance(measured, str) or not measured.startswith("{"):
        return [f"resize lock target {measured or measure_err}"]
    box = json.loads(measured)
    if box.get("display") == "none" or box.get("visibility") == "hidden":
        return [f"resize lock hidden {measured}"]
    if float(box.get("w") or 0) < 44 or float(box.get("h") or 0) < 44:
        return [f"resize lock target {box.get('w')}x{box.get('h')}"]
    fresh, fresh_err = resize_call(cdp, {})
    if fresh_err or not fresh:
        return [f"resize status {fresh_err}"]
    if fresh.get("lock") is not True or fresh.get("ellipse") is not False:
        return [f"resize lock default {fresh.get('lock')!r} ellipse {fresh.get('ellipse')!r}"]
    if int(fresh.get("undoDepth") or 0) != 0 or not _near(fresh.get("dx"), 20.0):
        return [f"resize fresh {fresh.get('dx')!r} undo {fresh.get('undoDepth')!r}"]
    unlocked, unlock_err = resize_call(cdp, {"lock": False})
    if unlock_err or not unlocked:
        return [f"resize unlock {unlock_err}"]
    if unlocked.get("ellipse") is not True or unlocked.get("ellipseText") != "Circles may become ellipses.":
        return [f"resize ellipse {unlocked.get('ellipseText')!r} shown {unlocked.get('ellipse')!r}"]
    if int(unlocked.get("undoDepth") or 0) != 0 or not _near((unlocked.get("params") or {}).get("sx"), 20.0, 1e-6):
        return [f"resize unlock changed the solid {unlocked}"]
    one, one_err = resize_call(cdp, {"sx": 30, "lock": False})
    if one_err or not one:
        return [f"resize 30 {one_err}"]
    if one.get("done") != "RESIZE_DONE" or one.get("method") != "gtransform" or one.get("valid") is not True:
        return [f"resize 30 result {one.get('done')!r} {one.get('method')!r} valid {one.get('valid')!r} {one.get('error')!r}"]
    if int(one.get("undoDepth") or 0) != 1:
        return [f"resize 30 undo depth {one.get('undoDepth')!r}"]
    if not _near(one.get("dx"), 30.0) or not _near(one.get("dy"), 20.0) or not _near(one.get("dz"), 20.0):
        return [f"resize 30 bbox {one.get('dx')!r} {one.get('dy')!r} {one.get('dz')!r}"]
    if not _near((one.get("params") or {}).get("sx"), 30.0, 1e-6):
        return [f"resize 30 stored sx {(one.get('params') or {}).get('sx')!r}"]
    back, back_err = resize_call(cdp, {"undo": True})
    if back_err or not back:
        return [f"resize undo {back_err}"]
    if int(back.get("undoDepth") or 0) != 0 or not _near(back.get("dx"), 20.0):
        return [f"resize undo restored {back.get('dx')!r} depth {back.get('undoDepth')!r}"]
    if not _near((back.get("params") or {}).get("sx"), 20.0, 1e-6):
        return [f"resize undo stored {(back.get('params') or {}).get('sx')!r}"]
    locked, locked_err = resize_call(cdp, {"lock": True, "sx": 30})
    if locked_err or not locked:
        return [f"resize lock on {locked_err}"]
    if locked.get("method") != "rebuild" or locked.get("done") != "RESIZE_DONE":
        return [f"resize lock method {locked.get('method')!r} {locked.get('done')!r} {locked.get('error')!r}"]
    params = locked.get("params") or {}
    if not _near(locked.get("dx"), 30.0) or not _near(locked.get("dy"), 30.0) or not _near(locked.get("dz"), 30.0):
        return [f"resize lock bbox {locked.get('dx')!r} {locked.get('dy')!r} {locked.get('dz')!r}"]
    if not _near(params.get("sx"), 30.0, 1e-6) or not _near(params.get("sy"), 30.0, 1e-6) or not _near(params.get("sz"), 30.0, 1e-6):
        return [f"resize lock params {params!r}"]
    restored, restored_err = resize_call(cdp, {"undo": True})
    if restored_err or not restored or int(restored.get("undoDepth") or 0) != 0:
        return [f"resize lock undo {restored_err or restored}"]
    inches, inch_err = resize_call(cdp, {"unit": "in", "lock": False})
    if inch_err or not inches:
        return [f"resize inches {inch_err}"]
    if inches.get("unit") != "in" or int(inches.get("undoDepth") or 0) != 0:
        return [f"resize inches unit {inches.get('unit')!r} depth {inches.get('undoDepth')!r}"]
    if not _near((inches.get("params") or {}).get("sx"), 20.0, 1e-9):
        return [f"resize inches stored {(inches.get('params') or {}).get('sx')!r}"]
    typed, typed_err = resize_call(cdp, {"field": "boxSx", "text": "1"})
    if typed_err or not typed:
        return [f"resize inch type {typed_err}"]
    stored = (typed.get("params") or {}).get("sx")
    try:
        stored_mm = float(stored)
    except (TypeError, ValueError):
        return [f"resize inch stored {stored!r}"]
    if abs(stored_mm - 25.4) >= 1e-9 or abs(stored_mm - 508.0) < 1 or abs(stored_mm - 645.16) < 1:
        return [f"resize inch stored {stored_mm}"]
    if typed.get("method") != "gtransform" or int(typed.get("undoDepth") or 0) != 1:
        return [f"resize inch method {typed.get('method')!r} depth {typed.get('undoDepth')!r}"]
    millimetres, mm_err = resize_call(cdp, {"unit": "mm"})
    if mm_err or not millimetres:
        return [f"resize back to mm {mm_err}"]
    if millimetres.get("unit") != "mm" or abs(float((millimetres.get("params") or {}).get("sx")) - stored_mm) >= 1e-9:
        return [f"resize mm drift {millimetres.get('unit')!r} {(millimetres.get('params') or {}).get('sx')!r}"]
    if int(millimetres.get("undoDepth") or 0) != 1:
        return [f"resize mm switch depth {millimetres.get('undoDepth')!r}"]
    cleared, clear_err = resize_call(cdp, {"undo": True})
    if clear_err or not cleared or int(cleared.get("undoDepth") or 0) != 0:
        return [f"resize inch undo {clear_err or cleared}"]
    depth = 0
    for spec, label in (
        ({"sx": 0, "lock": False}, "zero"),
        ({"sx": -4, "lock": False}, "negative"),
        ({"field": "boxSx", "text": ""}, "blank"),
        ({"sx": 30, "lock": False, "forceInvalid": True}, "invalid-gtransform"),
        ({"sx": 30, "lock": True, "forceInvalid": True}, "invalid-rebuild"),
    ):
        failed, fail_err = resize_call(cdp, spec)
        if fail_err or not failed:
            return [f"resize {label} {fail_err}"]
        if failed.get("rolledBack") is not True or int(failed.get("undoDepth") or 0) != depth:
            return [f"resize {label} rollback {failed.get('rolledBack')!r} depth {failed.get('undoDepth')!r}"]
        if "kept" not in str(failed.get("error") or ""):
            return [f"resize {label} error {failed.get('error')!r}"]
        if not _near((failed.get("params") or {}).get("sx"), 20.0, 1e-6) or not _near(failed.get("dx"), 20.0):
            return [f"resize {label} changed {failed.get('dx')!r} {(failed.get('params') or {}).get('sx')!r}"]
        if label == "blank" and "Enter a number" not in str(failed.get("error")):
            return [f"resize blank error {failed.get('error')!r}"]
        if label in {"zero", "negative"} and "greater than zero" not in str(failed.get("error")):
            return [f"resize {label} error {failed.get('error')!r}"]
    cut_url = origin + "/?demo=booleans&op=cut"
    print(f"load type_in_resize_cut {cut_url}", flush=True)
    cut, cut_problems = wait_for_case(cdp, origin, cut_url, PAGE_TIMEOUT_S)
    if cut_problems or not isinstance(cut, dict):
        return ["resize cut load", *cut_problems[:20]]
    before, before_err = resize_call(cdp, {"lock": True})
    if before_err or not before:
        return [f"resize cut status {before_err}"]
    if before.get("kind") != "boolean" or before.get("primitiveKind"):
        return [f"resize cut kind {before.get('kind')!r} primitive {before.get('primitiveKind')!r}"]
    try:
        dx0 = float(before["dx"])
        dy0 = float(before["dy"])
        dz0 = float(before["dz"])
    except (KeyError, TypeError, ValueError):
        return [f"resize cut bbox {before.get('dx')!r} {before.get('dy')!r} {before.get('dz')!r}"]
    if dx0 <= 0 or dy0 <= 0 or dz0 <= 0:
        return [f"resize cut bbox {dx0} {dy0} {dz0}"]
    scaled, scale_err = resize_call(cdp, {"lock": True, "sx": float(dx0) * 1.5})
    if scale_err or not scaled:
        return [f"resize cut scale {scale_err}"]
    if scaled.get("method") != "scale" or scaled.get("done") != "RESIZE_DONE" or scaled.get("valid") is not True:
        return [f"resize cut scale result {scaled.get('method')!r} {scaled.get('done')!r} {scaled.get('error')!r}"]
    if not _near(scaled.get("dx"), float(dx0) * 1.5) or not _near(scaled.get("dy"), float(dy0) * 1.5) or not _near(scaled.get("dz"), float(dz0) * 1.5):
        return [f"resize cut scaled bbox {scaled.get('dx')!r} {scaled.get('dy')!r} {scaled.get('dz')!r}"]
    widened, wide_err = resize_call(cdp, {"undo": True, "lock": False})
    if wide_err or not widened:
        return [f"resize cut undo {wide_err}"]
    if int(widened.get("undoDepth") or 0) != 0 or widened.get("ellipse") is not True:
        return [f"resize cut unlocked {widened.get('undoDepth')!r} ellipse {widened.get('ellipse')!r}"]
    try:
        base_x = float(widened["dx"])
        base_y = float(widened["dy"])
        base_z = float(widened["dz"])
    except (KeyError, TypeError, ValueError):
        return [f"resize cut restored bbox {widened.get('dx')!r} {widened.get('dy')!r} {widened.get('dz')!r}"]
    stretched, stretch_err = resize_call(cdp, {"lock": False, "sx": base_x * 1.25})
    if stretch_err or not stretched:
        return [f"resize cut gtransform {stretch_err}"]
    if stretched.get("method") != "gtransform" or stretched.get("ellipse") is not True or stretched.get("valid") is not True:
        return [f"resize cut gtransform result {stretched.get('method')!r} ellipse {stretched.get('ellipse')!r} {stretched.get('error')!r}"]
    if not _near(stretched.get("dx"), base_x * 1.25) or not _near(stretched.get("dy"), base_y) or not _near(stretched.get("dz"), base_z):
        return [f"resize cut stretched {stretched.get('dx')!r} {stretched.get('dy')!r} {stretched.get('dz')!r}"]
    print(
        "type_in_resize: 30 mm bbox, one undo, inch 25.4, lock, ellipse note, rollback, cut scale",
        flush=True,
    )
    return []


SAVELOAD_BUTTONS_EXPR = r"""
(function () {
  var problems = [];
  function closeMenu() {
    var menu = document.getElementById('fileMenu');
    var btn = document.getElementById('fileBtn');
    if (menu && !menu.hidden && btn) btn.click();
  }
  try {
    var menu = document.getElementById('fileMenu');
    var fileBtn = document.getElementById('fileBtn');
    if (!menu || !fileBtn) problems.push('file menu missing');
    else {
      fileBtn.click();
      if (menu.hidden) problems.push('file menu stayed closed');
      ['saveProjectBtn', 'loadProjectBtn'].forEach(function (id) {
        var el = document.getElementById(id);
        if (!el) { problems.push('missing ' + id); return; }
        var r = el.getBoundingClientRect();
        if (r.width < 44 || r.height < 44) problems.push(id + ' size ' + r.width.toFixed(1) + 'x' + r.height.toFixed(1));
        if (r.left < -0.5 || r.top < -0.5 || r.right > window.innerWidth + 0.5 || r.bottom > window.innerHeight + 0.5) {
          problems.push(id + ' offscreen ' + r.left.toFixed(1) + ',' + r.top.toFixed(1) + ' ' + r.right.toFixed(1) + ',' + r.bottom.toFixed(1) + ' view ' + window.innerWidth + 'x' + window.innerHeight);
        }
      });
      var input = document.getElementById('projectFile');
      if (!input || input.type !== 'file') problems.push('file input missing');
      else if (getComputedStyle(input).display === 'none') problems.push('file input display none');
      closeMenu();
      if (!menu.hidden) problems.push('file menu stayed open');
    }
  } catch (err) {
    problems.push('buttons ' + (err && err.message ? err.message : String(err)));
    closeMenu();
  }
  return JSON.stringify({ problems: problems });
})()
"""


SAVELOAD_EXPR = r"""
(function () {
  var problems = [];
  var clears = 0;
  function near(a, b) {
    return typeof a === 'number' && typeof b === 'number' && isFinite(a) && isFinite(b) && Math.abs(a - b) <= 0.01;
  }
  var hook = window.__cadcamProject;
  if (!hook || typeof hook.preparePair !== 'function') {
    problems.push('missing project hook');
    return JSON.stringify({ problems: problems, clears: clears });
  }
  try {
    var pair = hook.preparePair();
    if (!pair || pair.ok !== true) {
      problems.push('pair ' + (pair && pair.error ? pair.error : 'failed'));
      return JSON.stringify({ problems: problems, clears: clears });
    }
    var before = hook.measures();
    if (!before || before.length !== pair.count) problems.push('measure count ' + (before && before.length));
    var box = null;
    for (var i = 0; i < before.length; i += 1) {
      if (before[i].name.indexOf('Box') === 0) box = before[i];
    }
    if (!box || !near(box.volumeMm3, 8000)) problems.push('box volume ' + (box && box.volumeMm3));
    var saved = hook.saveText();
    if (!saved || saved.ok !== true) {
      problems.push('save ' + (saved && saved.error ? saved.error : 'failed'));
      return JSON.stringify({ problems: problems, clears: clears });
    }
    var doc = JSON.parse(saved.text);
    if (doc.units !== 'mm') problems.push('file units ' + doc.units);
    if (doc.version !== 1) problems.push('file version ' + doc.version);
    if (!doc.parts || doc.parts.length !== before.length) problems.push('file parts');
    var prevClear = window.__cadcamClearUndo;
    var clearOk = true;
    window.__cadcamClearUndo = function () {
      clears += 1;
      var result = typeof prevClear === 'function' ? prevClear() : false;
      if (result !== true) clearOk = false;
      return result;
    };
    var loaded = hook.loadText(saved.text, true);
    if (!loaded || loaded.ok !== true) problems.push('load ' + (loaded && loaded.error ? loaded.error : 'failed'));
    if (clears !== 1) problems.push('clearUndo after load ' + clears);
    if (!clearOk) problems.push('clearUndo did not reset the undo stack');
    var published = window.__cadcamExportState || {};
    if (published.undoDepth !== 0 || published.redoDepth !== 0) problems.push('undo depth ' + published.undoDepth + '/' + published.redoDepth);
    var after = hook.measures();
    if (!after || after.length !== before.length) problems.push('reload count');
    else {
      for (var n = 0; n < before.length; n += 1) {
        if (after[n].name !== before[n].name) problems.push('name ' + before[n].name + ' vs ' + after[n].name);
        if (after[n].source !== 'parameters') problems.push('source ' + after[n].name + ' ' + after[n].source);
        if (!after[n].params || typeof after[n].params !== 'object') problems.push('params ' + after[n].name);
        if (!near(after[n].volumeMm3, before[n].volumeMm3)) problems.push('volume ' + after[n].name + ' ' + after[n].volumeMm3);
        var keys = ['xmin', 'ymin', 'zmin', 'xmax', 'ymax', 'zmax'];
        for (var k = 0; k < keys.length; k += 1) {
          var key = keys[k];
          if (!after[n].bounds || !near(after[n].bounds[key], before[n].bounds[key])) {
            problems.push('bound ' + after[n].name + ' ' + key);
          }
        }
      }
    }
    var inchBtn = document.querySelector('[data-action="units"][data-unit="in"]');
    if (!inchBtn) problems.push('inch button missing');
    else inchBtn.click();
    if (hook.unit() !== 'in') problems.push('display unit ' + hook.unit());
    var inchSaved = hook.saveText();
    if (!inchSaved || inchSaved.ok !== true) problems.push('inch save');
    else {
      var inchDoc = JSON.parse(inchSaved.text);
      if (inchDoc.units !== 'mm') problems.push('inch file units ' + inchDoc.units);
      var inchLoaded = hook.loadText(inchSaved.text, true);
      if (!inchLoaded || inchLoaded.ok !== true) problems.push('inch load');
      if (hook.unit() !== 'in') problems.push('unit changed on load ' + hook.unit());
      var inchAfter = hook.measures();
      if (!inchAfter || inchAfter.length !== before.length) problems.push('inch count');
      else {
        for (var m = 0; m < before.length; m += 1) {
          if (!near(inchAfter[m].volumeMm3, before[m].volumeMm3)) problems.push('inch drift ' + inchAfter[m].name + ' ' + inchAfter[m].volumeMm3);
        }
      }
    }
    if (clears !== 2) problems.push('clearUndo after inch load ' + clears);
    var names = hook.measures().map(function (row) { return row.name; });
    var volumes = hook.measures().map(function (row) { return row.volumeMm3; });
    hook.setDirty(true);
    function unchanged(label, result) {
      if (!result || result.unchanged !== true || result.ok !== false) problems.push(label + ' result');
      var now = hook.measures();
      if (now.length !== names.length) problems.push(label + ' count');
      for (var u = 0; u < names.length; u += 1) {
        if (!now[u] || now[u].name !== names[u] || !near(now[u].volumeMm3, volumes[u])) problems.push(label + ' model');
      }
      if (hook.dirty() !== true) problems.push(label + ' dirty');
    }
    unchanged('corrupt', hook.loadText('{not json', true));
    unchanged('empty', hook.loadText('', true));
    unchanged('blank', hook.loadText('   ', true));
    var badUnits = JSON.parse(saved.text);
    badUnits.units = 'in';
    unchanged('units', hook.loadText(JSON.stringify(badUnits), true));
    var missingUnits = JSON.parse(saved.text);
    delete missingUnits.units;
    unchanged('missing units', hook.loadText(JSON.stringify(missingUnits), true));
    var badVersion = JSON.parse(saved.text);
    badVersion.version = 2;
    var beforeVersion = clears;
    var versionResult = hook.loadText(JSON.stringify(badVersion), true);
    unchanged('version', versionResult);
    if (!versionResult || versionResult.error !== 'This file version is not supported. The model was not changed.') {
      problems.push('version error ' + (versionResult && versionResult.error));
    }
    if (clears !== beforeVersion) problems.push('version cleared undo');
    var beforeCancel = clears;
    unchanged('cancel', hook.loadText(saved.text, false));
    if (clears !== beforeCancel) problems.push('cancel cleared undo');
    if (clears !== 2) problems.push('clearUndo final ' + clears);
    if (!clearOk) problems.push('clearUndo final did not reset the undo stack');
    var endState = window.__cadcamExportState || {};
    if (endState.undoDepth !== 0 || endState.redoDepth !== 0) problems.push('undo depth final ' + endState.undoDepth + '/' + endState.redoDepth);
    var mmBtn = document.querySelector('[data-action="units"][data-unit="mm"]');
    if (mmBtn) mmBtn.click();
    function bodyCount() {
      var st = window.__cadcamSketch && window.__cadcamSketch.state ? window.__cadcamSketch.state() : null;
      return st ? st.bodies : -1;
    }
    function hintText() {
      var hint = document.getElementById('statusHint');
      return hint ? String(hint.textContent || '') : '';
    }
    function rowNamed(name) {
      var rows = document.querySelectorAll('#partList .part-row');
      for (var i = 0; i < rows.length; i++) {
        var label = rows[i].querySelector('.part-name');
        if (label && label.textContent === name) return rows[i];
      }
      return null;
    }
    function clearParts() {
      var guard = 0;
      while (guard < 12) {
        var on = document.querySelector('#partList .part-row.is-on');
        if (!on) break;
        on.click();
        guard += 1;
      }
    }
    function setMaterial(name, value) {
      clearParts();
      var row = rowNamed(name);
      if (!row) { problems.push('material row ' + name); return false; }
      row.click();
      var sel = document.getElementById('partMaterial');
      if (!sel) { problems.push('partMaterial missing'); return false; }
      sel.value = value;
      sel.dispatchEvent(new Event('change', { bubbles: true }));
      return true;
    }
    function tagOf(name) {
      var row = rowNamed(name);
      if (!row || typeof window.__cadcamPartColor !== 'function') return '';
      var color = window.__cadcamPartColor(row.getAttribute('data-part-id'));
      return color && color.tag ? color.tag : '';
    }
    function storedMaterial(name) {
      var pub = window.__cadcamExportState || {};
      var names = pub.projectNames || [];
      var materials = pub.assemblyMaterials || [];
      for (var i = 0; i < names.length; i++) if (names[i] === name) return materials[i];
      return '';
    }
    function deleteAll(label) {
      var guard = 0;
      while (guard < 6) {
        var count = bodyCount();
        if (!count) return true;
        var item = document.querySelector('[data-action="select"][data-mode="item"]');
        if (!item) { problems.push(label + ' item missing'); return false; }
        item.click();
        var del = document.getElementById('deleteBtn');
        if (!del) { problems.push(label + ' delete missing'); return false; }
        del.click();
        if (bodyCount() >= count) {
          problems.push(label + ' stuck ' + bodyCount() + ' ' + hintText());
          return false;
        }
        guard += 1;
      }
      if (bodyCount()) problems.push(label + ' left ' + bodyCount());
      return bodyCount() === 0;
    }
    function clickCreate(kind) {
      var menu = document.getElementById('createMenu');
      if (!menu || menu.hidden) {
        if (!visibleClick('[data-action="createMenu"]')) {
          problems.push('create opener hidden');
          return false;
        }
      }
      menu = document.getElementById('createMenu');
      var button = menu ? menu.querySelector('[data-action="primitive"][data-kind="' + kind + '"]') : null;
      if (!button) { problems.push('missing create ' + kind); return false; }
      button.click();
      return true;
    }
    function visibleClick(selector) {
      var nodes = document.querySelectorAll(selector);
      for (var i = 0; i < nodes.length; i++) {
        var el = nodes[i];
        if (!el || (el.closest && el.closest('[hidden]'))) continue;
        var st = getComputedStyle(el);
        if (st.display === 'none' || st.visibility === 'hidden') continue;
        var r = el.getBoundingClientRect();
        if (r.width < 1 || r.height < 1) continue;
        el.click();
        return true;
      }
      if (selector === '[data-action="createMenu"]') {
        var sheet = document.getElementById('toolsSheet');
        if (!sheet || sheet.hidden) {
          var tm = document.querySelector('[data-action="toolsMenu"]');
          if (tm) tm.click();
        }
        var sc = document.querySelector('#toolsSheet [data-action="createMenu"]');
        if (sc && sheet && !sheet.hidden) {
          sc.click();
          return true;
        }
      }
      return false;
    }
    function openTools() {
      if (!visibleClick('[data-action="toolsMenu"]')) { problems.push('tools opener hidden'); return false; }
      var tools = document.getElementById('toolsSheet');
      if (!tools || tools.hidden) { problems.push('tools sheet hidden'); return false; }
      return true;
    }
    function sheetBtn(name) {
      var buttons = document.querySelectorAll('#sheetTools button');
      for (var i = 0; i < buttons.length; i++) {
        var span = buttons[i].querySelector('span');
        if (span && span.textContent === name) return buttons[i];
      }
      return null;
    }
    function setMm(id, value) {
      var el = document.getElementById(id);
      if (!el) { problems.push('missing ' + id); return; }
      el.value = value;
    }
    function boundKeys() { return ['xmin', 'ymin', 'zmin', 'xmax', 'ymax', 'zmax']; }
    function roundTrip(label, expectName, expectVolume) {
      var before = hook.measures();
      if (!before || before.length !== 1) { problems.push(label + ' count ' + (before && before.length)); return; }
      if (before[0].name !== expectName) problems.push(label + ' name ' + before[0].name);
      if (!near(before[0].volumeMm3, expectVolume)) problems.push(label + ' volume ' + before[0].volumeMm3);
      var savedOp = hook.saveText();
      if (!savedOp || savedOp.ok !== true) { problems.push(label + ' save ' + (savedOp && savedOp.error)); return; }
      var opDoc = JSON.parse(savedOp.text);
      if (opDoc.units !== 'mm' || opDoc.version !== 1) problems.push(label + ' header');
      if (!opDoc.parts || opDoc.parts.length !== 1) { problems.push(label + ' parts'); return; }
      if (opDoc.parts[0].primitive !== null) problems.push(label + ' primitive');
      if (opDoc.parts[0].name !== expectName) problems.push(label + ' part name ' + opDoc.parts[0].name);
      var loadedOp = hook.loadText(savedOp.text, true);
      if (!loadedOp || loadedOp.ok !== true) { problems.push(label + ' load ' + (loadedOp && loadedOp.error)); return; }
      var afterOp = hook.measures();
      if (!afterOp || afterOp.length !== 1) { problems.push(label + ' reload count'); return; }
      if (afterOp[0].name !== before[0].name) problems.push(label + ' reload name ' + afterOp[0].name);
      if (afterOp[0].source !== 'brep') problems.push(label + ' source ' + afterOp[0].source);
      if (afterOp[0].params !== null) problems.push(label + ' params');
      if (!near(afterOp[0].volumeMm3, before[0].volumeMm3)) problems.push(label + ' drift ' + afterOp[0].volumeMm3);
      var keys = boundKeys();
      for (var k = 0; k < keys.length; k++) {
        var key = keys[k];
        if (!afterOp[0].bounds || !before[0].bounds || !near(afterOp[0].bounds[key], before[0].bounds[key])) {
          problems.push(label + ' bound ' + key);
        }
      }
    }
    function makeOverlapPair(label) {
      if (!deleteAll(label + ' clear')) return false;
      if (!clickCreate('box') || !clickCreate('box')) return false;
      if (bodyCount() !== 2) { problems.push(label + ' bodies ' + bodyCount()); return false; }
      return true;
    }
    function clickBoolean(op) {
      var item = document.querySelector('[data-action="select"][data-mode="item"]');
      if (!item) { problems.push(op + ' item missing'); return false; }
      item.click();
      var buttons = document.querySelectorAll('[data-action="boolean"][data-op="' + op + '"]');
      var picked = null;
      for (var i = 0; i < buttons.length; i++) if (!buttons[i].disabled) { picked = buttons[i]; break; }
      if (!picked) {
        var pub = window.__cadcamExportState || {};
        problems.push(op + ' disabled sel ' + pub.selectionMode + ' ' + pub.selectionCount);
        return false;
      }
      picked.click();
      if (bodyCount() !== 1) { problems.push(op + ' result ' + bodyCount() + ' ' + hintText()); return false; }
      return true;
    }
    var matRows = hook.measures() || [];
    var boxName = '';
    var cylName = '';
    for (var mi = 0; mi < matRows.length; mi++) {
      if (!boxName && matRows[mi].name.indexOf('Box') === 0) boxName = matRows[mi].name;
      if (!cylName && matRows[mi].name.indexOf('Cylinder') === 0) cylName = matRows[mi].name;
    }
    if (!boxName || !cylName) problems.push('material names ' + boxName + ' ' + cylName);
    else if (setMaterial(boxName, 'PETG') && setMaterial(cylName, 'TPU')) {
      var namesBeforePla = ((window.__cadcamExportState || {}).projectNames || []).slice();
      if (!clickCreate('box')) problems.push('pla create');
      else {
        var namesAfterPla = (window.__cadcamExportState || {}).projectNames || [];
        var plaName = '';
        for (var pi = 0; pi < namesAfterPla.length; pi++) {
          if (namesBeforePla.indexOf(namesAfterPla[pi]) < 0) plaName = namesAfterPla[pi];
        }
        if (!plaName) problems.push('pla name ' + namesAfterPla.join(','));
        else if (storedMaterial(boxName) !== 'PETG' || storedMaterial(cylName) !== 'TPU' || storedMaterial(plaName) !== 'PLA') {
          problems.push('material live ' + storedMaterial(boxName) + ' ' + storedMaterial(cylName) + ' ' + storedMaterial(plaName));
        } else {
          var matSaved = hook.saveText();
          if (!matSaved || matSaved.ok !== true) problems.push('material save');
          else {
            var matDoc = JSON.parse(matSaved.text);
            var matByName = {};
            for (var mp = 0; mp < matDoc.parts.length; mp++) matByName[matDoc.parts[mp].name] = matDoc.parts[mp].material;
            if (matByName[boxName] !== 'PETG' || matByName[cylName] !== 'TPU' || matByName[plaName] !== 'PLA') {
              problems.push('material file ' + JSON.stringify(matByName));
            }
            hook.setDirty(true);
            var missingMat = JSON.parse(matSaved.text);
            delete missingMat.parts[0].material;
            var missingMatResult = hook.loadText(JSON.stringify(missingMat), true);
            if (!missingMatResult || missingMatResult.unchanged !== true || missingMatResult.ok !== false) problems.push('missing material result');
            if (!missingMatResult || missingMatResult.error !== 'This file could not be read. The model was not changed.') {
              problems.push('missing material error ' + (missingMatResult && missingMatResult.error));
            }
            if (hook.dirty() !== true) problems.push('missing material dirty');
            if (storedMaterial(boxName) !== 'PETG' || storedMaterial(plaName) !== 'PLA') problems.push('missing material changed model');
            var matLoaded = hook.loadText(matSaved.text, true);
            if (!matLoaded || matLoaded.ok !== true) problems.push('material load ' + (matLoaded && matLoaded.error));
            else if (storedMaterial(boxName) !== 'PETG' || storedMaterial(cylName) !== 'TPU' || storedMaterial(plaName) !== 'PLA') {
              problems.push('material reload ' + storedMaterial(boxName) + ' ' + storedMaterial(cylName) + ' ' + storedMaterial(plaName));
            } else if (tagOf(boxName) !== 'PETG' || tagOf(cylName) !== 'TPU' || tagOf(plaName) !== 'PLA') {
              problems.push('material tag ' + tagOf(boxName) + ' ' + tagOf(cylName) + ' ' + tagOf(plaName));
            } else {
              var matAfter = hook.measures() || [];
              for (var mr = 0; mr < matAfter.length; mr++) {
                if (matAfter[mr].source !== 'parameters' || !matAfter[mr].params) problems.push('material source ' + matAfter[mr].name + ' ' + matAfter[mr].source);
              }
              var defaultDoc = JSON.parse(matSaved.text);
              for (var md = 0; md < defaultDoc.parts.length; md++) {
                if (defaultDoc.parts[md].name === plaName) defaultDoc.parts[md].material = 'default';
              }
              var defaultLoaded = hook.loadText(JSON.stringify(defaultDoc), true);
              if (!defaultLoaded || defaultLoaded.ok !== true) problems.push('default material load');
              else if (storedMaterial(plaName) !== 'default' || tagOf(plaName) !== 'PLA') {
                problems.push('default material ' + storedMaterial(plaName) + ' tag ' + tagOf(plaName));
              } else if (storedMaterial(boxName) !== 'PETG' || tagOf(boxName) !== 'PETG' || storedMaterial(cylName) !== 'TPU' || tagOf(cylName) !== 'TPU') {
                problems.push('default siblings ' + storedMaterial(boxName) + ' ' + storedMaterial(cylName));
              }
            }
          }
        }
      }
    }
    if (makeOverlapPair('union') && clickBoolean('union')) roundTrip('union', 'Union 1', 12000);
    if (makeOverlapPair('cut') && clickBoolean('cut')) roundTrip('cut', 'Cut 1', 4000);
    if (!deleteAll('extrude clear')) {
      /* deleteAll already recorded why the scene was not empty */
    } else if (!visibleClick('[data-action="createMenu"]')) {
      problems.push('extrude create hidden');
    } else {
      var sketchMenu = document.getElementById('createMenu');
      var sketchItem = sketchMenu ? sketchMenu.querySelector('[data-action="newSketch"]') : null;
      if (!sketchItem) problems.push('extrude sketch missing');
      else {
        sketchItem.click();
        var sketchState = window.__cadcamSketch.state();
        if (!sketchState || sketchState.bodies !== 0 || sketchState.tab !== 'sketch') {
          problems.push('extrude sketch start ' + (sketchState && sketchState.tab) + ' ' + (sketchState && sketchState.bodies));
        } else {
          var topPlane = document.querySelector('#originPlanes [data-plane="xy"]');
          if (!topPlane) problems.push('extrude top missing');
          else {
            topPlane.click();
            sketchState = window.__cadcamSketch.state();
            if (!sketchState || sketchState.originPlane !== 'xy') problems.push('extrude plane ' + (sketchState && sketchState.originPlane));
            else if (openTools()) {
              var rectBtn = sheetBtn('Rectangle');
              if (!rectBtn) problems.push('extrude rectangle missing');
              else {
                rectBtn.click();
                setMm('sketchL', '10');
                setMm('sketchW', '10');
                var confirmBtn = document.getElementById('sketchConfirm');
                if (!confirmBtn || confirmBtn.disabled) problems.push('extrude rect confirm ' + hintText());
                else {
                  confirmBtn.click();
                  sketchState = window.__cadcamSketch.state();
                  if (!sketchState || sketchState.profile !== 'rect' || sketchState.closed !== true) {
                    problems.push('extrude profile ' + (sketchState && sketchState.profile));
                  } else {
                    var finishBtn = document.querySelector('#finishBar [data-action="finishSketch"]');
                    if (finishBtn) finishBtn.click();
                    else problems.push('extrude finish missing');
                    if (openTools()) {
                      var extBtn = sheetBtn('Extrude (Push/Pull)');
                      if (!extBtn) problems.push('extrude tool missing');
                      else {
                        extBtn.click();
                        setMm('sketchDepth', '10');
                        var newMode = document.querySelector('#sketchModeRow [data-mode="new"]');
                        if (newMode && !newMode.classList.contains('is-on')) newMode.click();
                        confirmBtn = document.getElementById('sketchConfirm');
                        if (!confirmBtn || confirmBtn.disabled) problems.push('extrude confirm ' + hintText());
                        else {
                          confirmBtn.click();
                          sketchState = window.__cadcamSketch.state();
                          if (!sketchState || sketchState.bodies !== 1 || !sketchState.bounds || sketchState.bounds.kind !== 'extrude') {
                            problems.push('extrude kind ' + (sketchState && sketchState.bounds && sketchState.bounds.kind) + ' bodies ' + (sketchState && sketchState.bodies) + ' ' + hintText());
                          } else roundTrip('extrude', 'Extrude 1', 1000);
                        }
                      }
                    }
                  }
                }
              }
            }
          }
        }
      }
    }
  } catch (err2) {
    problems.push(err2 && err2.message ? err2.message : String(err2));
  }
  return JSON.stringify({ problems: problems, clears: clears });
})()
"""


ASSEMBLY_LAYOUT_EXPR = r"""
(function(){
  var problems = [];
  var w = window.innerWidth;
  var h = window.innerHeight;
  if (w < 380 || w > 420) problems.push('width ' + w);
  var info = document.querySelector('[data-drawer="inspector"]');
  var inspector = document.getElementById('inspector');
  if (!info || !inspector) return JSON.stringify({problems:['missing inspector'], w:w, h:h});
  if (!inspector.classList.contains('open')) info.click();
  inspector.classList.add('open');
  inspector.removeAttribute('inert');
  function measure(el, name) {
    if (!el) { problems.push(name + ' missing'); return; }
    el.scrollIntoView({block:'center', inline:'nearest'});
    var r = el.getBoundingClientRect();
    var cx = r.left + r.width / 2;
    var cy = r.top + r.height / 2;
    var top = document.elementFromPoint(cx, cy);
    var hit = top === el || (el.contains && el.contains(top));
    var on = r.width >= 44 && r.height >= 44 && r.bottom > 0 && r.right > 0 && r.left < w && r.top < h;
    if (!on || !hit) problems.push(name + ' ' + Math.round(r.width) + 'x' + Math.round(r.height) + ' hit=' + hit + ' on=' + on + ' at ' + (top ? (top.id || top.className || top.tagName) : 'none'));
  }
  var rows = document.querySelectorAll('#partList .part-row');
  if (rows.length < 2) problems.push('rows ' + rows.length);
  for (var i = 0; i < rows.length; i++) measure(rows[i], 'part ' + i);
  measure(document.getElementById('combineBtn'), 'combine');
  measure(document.getElementById('partMaterial'), 'material');
  return JSON.stringify({problems:problems, w:w, h:h, rows:rows.length, open:inspector.classList.contains('open')});
})()
"""


def assembly_problems(cdp: Cdp, origin: str) -> list[str]:
    """Portrait 390x844: parts list and Combine are 44 px, and the probe rolls back."""
    try:
        try:
            set_portrait(cdp)
        except (RuntimeError, TimeoutError, OSError) as exc:
            return [f"assembly portrait {exc}"]
        url = origin + "/?demo=assembly"
        cdp.events.clear()
        cdp.urls.clear()
        cdp.call("Page.navigate", {"url": url})
        deadline = time.time() + PAGE_TIMEOUT_S
        last: dict[str, Any] | None = None
        ready = False
        while time.time() < deadline:
            cdp.drain(0.5)
            payload = eval_state(cdp)
            notes = smoke_notes(payload)
            if notes:
                return [f"assembly {item}" for item in notes[:20]]
            state = (payload or {}).get("state") if payload else None
            if not isinstance(state, dict):
                continue
            last = state
            if state.get("demo") == "assembly" and state.get("lastError"):
                return [f"assembly demo {state.get('lastError')}"]
            if (
                state.get("occtReady") is True
                and state.get("demo") == "assembly"
                and int(state.get("bodyCount") or 0) >= 2
            ):
                cdp.drain(0.4)
                site = site_problems(cdp.events, origin, cdp.urls)
                if site:
                    return [f"assembly {item}" for item in site[:20]]
                ready = True
                break
        if not ready:
            return [f"assembly timed out {json.dumps(last)[:500]}"]
        layout_raw, layout_err = eval_expr(cdp, ASSEMBLY_LAYOUT_EXPR)
        if layout_err or not isinstance(layout_raw, str):
            return [f"assembly layout {layout_raw or layout_err}"]
        try:
            layout = json.loads(layout_raw)
        except json.JSONDecodeError:
            return [f"assembly layout {layout_raw[:500]}"]
        layout_problems = layout.get("problems") if isinstance(layout, dict) else [str(layout_raw)]
        if not isinstance(layout_problems, list):
            return [f"assembly layout {layout_raw[:500]}"]
        if layout_problems:
            return [f"assembly {item}" for item in layout_problems]
        raw, err = eval_expr(
            cdp,
            "JSON.stringify(window.__cadcamAssembly({probe:true}))",
            timeout=120,
        )
        if err or not isinstance(raw, str):
            return [f"assembly probe {raw or err}"]
        try:
            found = json.loads(raw)
        except json.JSONDecodeError:
            return [f"assembly probe {raw[:500]}"]
        if not isinstance(found, dict):
            return [f"assembly probe {raw[:500]}"]
        problems: list[str] = []
        if found.get("error"):
            problems.append(f"error {found.get('error')}")
        if found.get("mixedUnchanged") is not True:
            problems.append(f"mixed changed {found.get('mixedUnchanged')!r}")
        if found.get("mixedError") != "These parts use different materials. The model was not changed.":
            problems.append(f"mixed error {found.get('mixedError')!r}")
        if found.get("failUnchanged") is not True:
            problems.append(f"force fail changed {found.get('failUnchanged')!r}")
        if found.get("failError") != "Combine failed the shape check. The model was not changed.":
            problems.append(f"force fail error {found.get('failError')!r}")
        if found.get("combined") is not True:
            problems.append(f"combined {found.get('combined')!r}")
        if found.get("combinedMaterial") != "PLA":
            problems.append(f"material {found.get('combinedMaterial')!r}")
        if found.get("combinedValid") is not True:
            problems.append(f"valid {found.get('combinedValid')!r}")
        if found.get("undoRestored") is not True:
            problems.append(f"undo {found.get('undoRestored')!r}")
        if found.get("undoStep") is not True:
            problems.append("undo step")
        if problems:
            return [f"assembly {item}" for item in problems]
        print("ASSEMBLIES_DONE", flush=True)
        return []
    finally:
        try:
            set_desktop(cdp)
        except (RuntimeError, TimeoutError, OSError):
            pass


def run_saveload(cdp: Cdp, origin: str) -> list[str]:
    """Round-trip a box and a cylinder through the project-file hook."""
    url = origin + "/?primitive=box"
    _state, load_problems = wait_for_case(cdp, origin, url, PAGE_TIMEOUT_S)
    if load_problems:
        return ["saveload load", *load_problems[:20]]
    try:
        set_portrait(cdp)
    except (RuntimeError, TimeoutError, OSError) as exc:
        return [f"saveload portrait {exc}"]
    time.sleep(0.3)
    button_raw, button_err = eval_expr(cdp, SAVELOAD_BUTTONS_EXPR)
    if button_err or not isinstance(button_raw, str):
        return [f"saveload buttons {button_raw or button_err}"]
    try:
        button_found = json.loads(button_raw)
    except json.JSONDecodeError:
        return [f"saveload buttons {button_raw[:500]}"]
    button_problems = button_found.get("problems") if isinstance(button_found, dict) else [str(button_raw)]
    if not isinstance(button_problems, list):
        return [f"saveload buttons {button_raw[:500]}"]
    if button_problems:
        return [f"saveload {item}" for item in button_problems]
    cover = coverage_problems(cdp, False)
    if cover:
        return [f"saveload {item}" for item in cover]
    raw, err = eval_expr(cdp, SAVELOAD_EXPR, timeout=300)
    if err or not isinstance(raw, str):
        return [f"saveload eval {raw or err}"]
    try:
        found = json.loads(raw)
    except json.JSONDecodeError:
        return [f"saveload json {raw[:500]}"]
    problems = found.get("problems") if isinstance(found, dict) else [str(raw)]
    if not isinstance(problems, list):
        return [f"saveload {raw[:500]}"]
    if problems:
        return [f"saveload {item}" for item in problems]
    print("saveload pass", flush=True)
    return []


SIZE_GROUP_EXPR = r"""
(function(){
  function group(id) {
    var el = document.getElementById(id);
    if (!el) return {missing:true, hidden:true, display:'none'};
    var st = getComputedStyle(el);
    return {missing:false, hidden: el.hidden === true, display: st.display};
  }
  var sheet = document.getElementById('dimPanel');
  return JSON.stringify({
    open: !!(sheet && sheet.classList.contains('is-open')),
    box: group('primBox'),
    cyl: group('primCyl'),
    disc: group('primDisc'),
    bbox: group('primBbox'),
    cylD: (document.getElementById('cylD') || {}).value || '',
    cylH: (document.getElementById('cylH') || {}).value || '',
    sx: (document.getElementById('boxSx') || {}).value || '',
    sy: (document.getElementById('boxSy') || {}).value || '',
    sz: (document.getElementById('boxSz') || {}).value || '',
    bx: (document.getElementById('bboxX') || {}).value || '',
    by: (document.getElementById('bboxY') || {}).value || '',
    bz: (document.getElementById('bboxZ') || {}).value || ''
  });
})()
"""


def _json_eval(cdp: Cdp, expression: str, timeout: float = 30) -> tuple[dict[str, Any] | None, str]:
    raw, err = eval_expr(cdp, expression, timeout=timeout)
    if err or not isinstance(raw, str) or not raw.startswith("{"):
        return None, err or str(raw)
    try:
        data = json.loads(raw)
    except json.JSONDecodeError:
        return None, raw
    return data if isinstance(data, dict) else None, ""


def _part_row_id(cdp: Cdp, name: str) -> tuple[str, str]:
    raw, err = eval_expr(
        cdp,
        "(function(){"
        f"var name={json.dumps(name)};"
        "var rows=document.querySelectorAll('#partList .part-row');"
        "for(var i=0;i<rows.length;i++){"
        "var label=rows[i].querySelector('.part-name');"
        "if(label&&label.textContent===name) return rows[i].getAttribute('data-part-id')||'';"
        "}"
        "return '';"
        "})()",
    )
    if err or not isinstance(raw, str):
        return "", err or str(raw)
    return raw, ""


def _click_part(cdp: Cdp, name: str) -> tuple[str, str]:
    raw, err = eval_expr(
        cdp,
        "(function(){"
        f"var name={json.dumps(name)};"
        "var rows=document.querySelectorAll('#partList .part-row');"
        "for(var i=0;i<rows.length;i++){"
        "var label=rows[i].querySelector('.part-name');"
        "if(label&&label.textContent===name){rows[i].click();return rows[i].getAttribute('data-part-id')||'';}"
        "}"
        "return '';"
        "})()",
    )
    if err or not isinstance(raw, str) or not raw:
        return "", err or raw or f"missing part {name}"
    return raw, ""


def _field_open(group: Any) -> bool:
    return isinstance(group, dict) and group.get("hidden") is False and group.get("display") != "none"


def _named_part(status: dict[str, Any], name: str) -> dict[str, Any] | None:
    parts = status.get("parts")
    if not isinstance(parts, list):
        return None
    for item in parts:
        if isinstance(item, dict) and item.get("name") == name:
            return item
    return None


def multi_body_size_problems(cdp: Cdp, origin: str) -> list[str]:
    """Several bodies: the size sheet follows the selected part, and undo covers the resize.

    Repro before the fix: with Box and Cylinder both in the model, selecting either
    part and opening the size sheet left diameter, height, and Size X/Y/Z hidden.
    """
    try:
        set_desktop(cdp)
    except (RuntimeError, TimeoutError, OSError) as exc:
        return [f"multi size desktop {exc}"]
    url = origin + "/?demo=assembly"
    print(f"load multi_body_size {url}", flush=True)
    loaded, load_problems = wait_for_case(cdp, origin, url, PAGE_TIMEOUT_S)
    if load_problems or not isinstance(loaded, dict):
        return ["multi size load", *load_problems[:20]]
    if loaded.get("demo") != "assembly" or int(loaded.get("bodyCount") or 0) != 2:
        return [f"multi size scene {loaded.get('demo')!r} bodies {loaded.get('bodyCount')!r}"]
    opened, open_err = eval_expr(cdp, CLICK_DIM_EXPR)
    if open_err or opened != "clicked":
        return [f"multi size sheet {opened or open_err}"]
    both, both_err = _json_eval(cdp, SIZE_GROUP_EXPR)
    if both_err or not both:
        return [f"multi size groups {both_err}"]
    if both.get("open") is not True:
        return ["multi size sheet stayed closed"]
    for key in ("box", "cyl", "disc", "bbox"):
        if _field_open(both.get(key)):
            return [f"multi size {key} visible while both parts are selected {both.get(key)}"]

    box_click, box_err = _click_part(cdp, "Cylinder")
    if box_err:
        return [f"multi size deselect cylinder {box_err}"]
    listed, listed_err = _json_eval(cdp, SIZE_GROUP_EXPR)
    if listed_err or not listed:
        return [f"multi size box groups {listed_err}"]
    if not _field_open(listed.get("box")) or _field_open(listed.get("cyl")) or _field_open(listed.get("bbox")):
        return [f"multi size parts-list box fields {listed}"]
    if listed.get("sx") != "20" or listed.get("sy") != "20" or listed.get("sz") != "20":
        return [f"multi size box values {listed.get('sx')!r} {listed.get('sy')!r} {listed.get('sz')!r}"]

    cyl_id, cyl_err = _part_row_id(cdp, "Cylinder")
    if cyl_err or not cyl_id:
        return [f"multi size cylinder id {cyl_err or cyl_id!r}"]
    picked, pick_err = _json_eval(
        cdp,
        "(function(){"
        f"if(typeof window.__cadcamPickPart!=='function') return 'missing';"
        f"return JSON.stringify(window.__cadcamPickPart({json.dumps(cyl_id)}));"
        "})()",
    )
    if pick_err or not picked:
        return [f"multi size viewport pick {pick_err}"]
    if picked.get("cyl") is not True or picked.get("box") is not False or picked.get("kind") != "cylinder":
        return [f"multi size viewport fields {picked}"]
    shown, shown_err = _json_eval(cdp, SIZE_GROUP_EXPR)
    if shown_err or not shown:
        return [f"multi size cyl groups {shown_err}"]
    if not _field_open(shown.get("cyl")) or _field_open(shown.get("box")):
        return [f"multi size cylinder fields {shown}"]
    if shown.get("cylD") != "20" or shown.get("cylH") != "20":
        return [f"multi size cylinder values {shown.get('cylD')!r} {shown.get('cylH')!r}"]

    locked, lock_err = resize_call(cdp, {"lock": True, "diameter": 30}, timeout=120)
    if lock_err or not locked:
        return [f"multi size lock resize {lock_err}"]
    if locked.get("done") != "RESIZE_DONE" or locked.get("method") != "rebuild" or locked.get("valid") is not True:
        return [f"multi size lock result {locked.get('done')!r} {locked.get('method')!r} {locked.get('error')!r}"]
    if int(locked.get("undoDepth") or 0) != 1:
        return [f"multi size lock depth {locked.get('undoDepth')!r}"]
    cyl = _named_part(locked, "Cylinder") or {}
    box = _named_part(locked, "Box") or {}
    if not _near(cyl.get("radius"), 15.0, 1e-6) or not _near(cyl.get("height"), 30.0, 1e-6):
        return [f"multi size lock cylinder {cyl!r}"]
    if not _near(locked.get("dx"), 30.0) or not _near(locked.get("dy"), 30.0) or not _near(locked.get("dz"), 30.0):
        return [f"multi size lock bounds {locked.get('dx')!r} {locked.get('dy')!r} {locked.get('dz')!r}"]
    if not _near(box.get("sx"), 20.0, 1e-6) or not _near(box.get("sy"), 20.0, 1e-6) or not _near(box.get("sz"), 20.0, 1e-6):
        return [f"multi size lock box changed {box!r}"]
    undone, undo_err = resize_call(cdp, {"undo": True}, timeout=120)
    if undo_err or not undone or int(undone.get("undoDepth") or 0) != 0 or int(undone.get("redoDepth") or 0) != 1:
        return [f"multi size undo {undo_err or undone}"]
    cyl = _named_part(undone, "Cylinder") or {}
    if not _near(cyl.get("radius"), 10.0, 1e-6) or not _near(cyl.get("height"), 20.0, 1e-6):
        return [f"multi size undo cylinder {cyl!r}"]
    if not _near(undone.get("dx"), 20.0) or not _near(undone.get("dy"), 20.0) or not _near(undone.get("dz"), 20.0):
        return [f"multi size undo bounds {undone.get('dx')!r} {undone.get('dy')!r} {undone.get('dz')!r}"]
    redone, redo_err = resize_call(cdp, {"redo": True}, timeout=120)
    if redo_err or not redone or int(redone.get("undoDepth") or 0) != 1 or int(redone.get("redoDepth") or 0) != 0:
        return [f"multi size redo {redo_err or redone}"]
    cyl = _named_part(redone, "Cylinder") or {}
    if not _near(cyl.get("radius"), 15.0, 1e-6) or not _near(cyl.get("height"), 30.0, 1e-6):
        return [f"multi size redo cylinder {cyl!r}"]
    if not _near(redone.get("dx"), 30.0) or not _near(redone.get("dy"), 30.0) or not _near(redone.get("dz"), 30.0):
        return [f"multi size redo bounds {redone.get('dx')!r} {redone.get('dy')!r} {redone.get('dz')!r}"]
    cleared, clear_err = resize_call(cdp, {"undo": True}, timeout=120)
    if clear_err or not cleared or int(cleared.get("undoDepth") or 0) != 0:
        return [f"multi size clear {clear_err or cleared}"]

    unlocked, unlock_err = resize_call(cdp, {"lock": False, "diameter": 30}, timeout=120)
    if unlock_err or not unlocked:
        return [f"multi size unlock resize {unlock_err}"]
    if unlocked.get("method") != "rebuild" or unlocked.get("done") != "RESIZE_DONE" or unlocked.get("ellipse") is not True:
        return [f"multi size unlock result {unlocked.get('method')!r} {unlocked.get('done')!r} ellipse {unlocked.get('ellipse')!r} {unlocked.get('error')!r}"]
    cyl = _named_part(unlocked, "Cylinder") or {}
    box = _named_part(unlocked, "Box") or {}
    if not _near(cyl.get("radius"), 15.0, 1e-6) or not _near(cyl.get("height"), 20.0, 1e-6):
        return [f"multi size unlock cylinder {cyl!r}"]
    if not _near(unlocked.get("dx"), 30.0) or not _near(unlocked.get("dy"), 30.0) or not _near(unlocked.get("dz"), 20.0):
        return [f"multi size unlock bounds {unlocked.get('dx')!r} {unlocked.get('dy')!r} {unlocked.get('dz')!r}"]
    if not _near(box.get("sx"), 20.0, 1e-6):
        return [f"multi size unlock box {box!r}"]
    restored, restore_err = resize_call(cdp, {"undo": True, "lock": True}, timeout=120)
    if restore_err or not restored or int(restored.get("undoDepth") or 0) != 0:
        return [f"multi size unlock undo {restore_err or restored}"]

    off, off_err = _click_part(cdp, "Cylinder")
    if off_err:
        return [f"multi size clear cylinder {off_err}"]
    on, on_err = _click_part(cdp, "Box")
    if on_err:
        return [f"multi size select box {on_err}"]
    box_fields, box_fields_err = _json_eval(cdp, SIZE_GROUP_EXPR)
    if box_fields_err or not box_fields or not _field_open(box_fields.get("box")) or _field_open(box_fields.get("cyl")):
        return [f"multi size box again {box_fields_err or box_fields}"]
    widened, wide_err = resize_call(cdp, {"lock": True, "sx": 30}, timeout=120)
    if wide_err or not widened:
        return [f"multi size box resize {wide_err}"]
    if widened.get("method") != "rebuild" or widened.get("done") != "RESIZE_DONE":
        return [f"multi size box result {widened.get('method')!r} {widened.get('done')!r} {widened.get('error')!r}"]
    box = _named_part(widened, "Box") or {}
    cyl = _named_part(widened, "Cylinder") or {}
    if not _near(box.get("sx"), 30.0, 1e-6) or not _near(box.get("sy"), 30.0, 1e-6) or not _near(box.get("sz"), 30.0, 1e-6):
        return [f"multi size box lock {box!r}"]
    if not _near(widened.get("dx"), 30.0) or not _near(widened.get("dy"), 30.0) or not _near(widened.get("dz"), 30.0):
        return [f"multi size box bounds {widened.get('dx')!r} {widened.get('dy')!r} {widened.get('dz')!r}"]
    if not _near(cyl.get("radius"), 10.0, 1e-6) or not _near(cyl.get("height"), 20.0, 1e-6):
        return [f"multi size box touched cylinder {cyl!r}"]
    box_undo, box_undo_err = resize_call(cdp, {"undo": True}, timeout=120)
    if box_undo_err or not box_undo or int(box_undo.get("undoDepth") or 0) != 0:
        return [f"multi size box undo {box_undo_err or box_undo}"]
    box = _named_part(box_undo, "Box") or {}
    if not _near(box.get("sx"), 20.0, 1e-6) or not _near(box.get("sy"), 20.0, 1e-6) or not _near(box.get("sz"), 20.0, 1e-6):
        return [f"multi size box undo values {box!r}"]
    if not _near(box_undo.get("dx"), 20.0) or not _near(box_undo.get("dy"), 20.0) or not _near(box_undo.get("dz"), 20.0):
        return [f"multi size box undo bounds {box_undo.get('dx')!r} {box_undo.get('dy')!r} {box_undo.get('dz')!r}"]
    box_redo, box_redo_err = resize_call(cdp, {"redo": True}, timeout=120)
    if box_redo_err or not box_redo or int(box_redo.get("undoDepth") or 0) != 1:
        return [f"multi size box redo {box_redo_err or box_redo}"]
    box = _named_part(box_redo, "Box") or {}
    if not _near(box.get("sx"), 30.0, 1e-6) or not _near(box.get("sy"), 30.0, 1e-6) or not _near(box.get("sz"), 30.0, 1e-6):
        return [f"multi size box redo values {box!r}"]
    if not _near(box_redo.get("dx"), 30.0) or not _near(box_redo.get("dy"), 30.0) or not _near(box_redo.get("dz"), 30.0):
        return [f"multi size box redo bounds {box_redo.get('dx')!r} {box_redo.get('dy')!r} {box_redo.get('dz')!r}"]

    added, add_err = eval_expr(
        cdp,
        "(function(){var b=document.querySelector('[data-action=\"primitive\"][data-kind=\"cylinder\"]');"
        "if(!b) return 'missing'; b.click(); return 'added';})()",
        timeout=120,
    )
    if add_err or added != "added":
        return [f"multi size add cylinder {added or add_err}"]
    # Union the box and the original cylinder. The added cylinder stays, so the
    # Boolean result is resized beside another body.
    for name in ("Box", "Cylinder"):
        _clicked, click_err = _click_part(cdp, name)
        if click_err:
            return [f"multi size union select {name} {click_err}"]
    union, union_err = eval_expr(
        cdp,
        "(function(){var b=document.querySelector('[data-action=\"boolean\"][data-op=\"union\"]');"
        "if(!b) return 'missing'; if(b.disabled) return 'disabled'; b.click();"
        "var s=window.__cadcamExportState||{};"
        "return JSON.stringify({bodies:s.bodyCount, error:s.lastError||''});})()",
        timeout=120,
    )
    if union_err or not isinstance(union, str) or not union.startswith("{"):
        return [f"multi size union {union or union_err}"]
    try:
        union_state = json.loads(union)
    except json.JSONDecodeError:
        return [f"multi size union {union}"]
    if int(union_state.get("bodies") or 0) != 2 or union_state.get("error"):
        return [f"multi size union result {union_state}"]
    bbox, bbox_err = _json_eval(cdp, SIZE_GROUP_EXPR)
    if bbox_err or not bbox:
        return [f"multi size bbox groups {bbox_err}"]
    if not _field_open(bbox.get("bbox")) or _field_open(bbox.get("box")) or _field_open(bbox.get("cyl")):
        return [f"multi size union fields {bbox}"]
    try:
        base_x = float(bbox.get("bx"))
    except (TypeError, ValueError):
        return [f"multi size union x {bbox.get('bx')!r}"]
    scaled, scale_err = resize_call(cdp, {"lock": True, "sx": base_x * 1.5}, timeout=120)
    if scale_err or not scaled:
        return [f"multi size union resize {scale_err}"]
    if scaled.get("method") != "scale" or scaled.get("done") != "RESIZE_DONE" or scaled.get("kind") != "boolean":
        return [f"multi size union resize result {scaled.get('method')!r} {scaled.get('kind')!r} {scaled.get('error')!r}"]
    started = {
        "dx": base_x,
        "dy": float(bbox.get("by")),
        "dz": float(bbox.get("bz")),
    }
    if not _near(scaled.get("dx"), started["dx"] * 1.5) or not _near(scaled.get("dy"), started["dy"] * 1.5) or not _near(scaled.get("dz"), started["dz"] * 1.5):
        return [f"multi size union scaled {scaled.get('dx')!r} {scaled.get('dy')!r} {scaled.get('dz')!r} from {started}"]
    extra = _named_part(scaled, "Cylinder 3") or {}
    if extra.get("kind") != "cylinder" or not _near(extra.get("radius"), 10.0, 1e-6):
        return [f"multi size union extra {extra!r}"]
    union_undo, union_undo_err = resize_call(cdp, {"undo": True}, timeout=120)
    if union_undo_err or not union_undo or int(union_undo.get("undoDepth") or 0) != int(scaled.get("undoDepth") or 1) - 1:
        return [f"multi size union undo {union_undo_err or union_undo}"]
    if not _near(union_undo.get("dx"), started["dx"]) or not _near(union_undo.get("dy"), started["dy"]) or not _near(union_undo.get("dz"), started["dz"]):
        return [f"multi size union undo size {union_undo.get('dx')!r} {union_undo.get('dy')!r} {union_undo.get('dz')!r}"]
    union_redo, union_redo_err = resize_call(cdp, {"redo": True}, timeout=120)
    if union_redo_err or not union_redo or int(union_redo.get("undoDepth") or 0) != int(scaled.get("undoDepth") or 0):
        return [f"multi size union redo {union_redo_err or union_redo}"]
    if not _near(union_redo.get("dx"), started["dx"] * 1.5):
        return [f"multi size union redo size {union_redo.get('dx')!r}"]
    print("multi body size pass", flush=True)
    return []


MOVE_POS_EXPR = (
    "(function(){"
    "var x=document.getElementById('posX');"
    "var s=window.__cadcamExportState||{};"
    "return JSON.stringify({"
    "disabled:!!(x&&x.disabled),"
    "title:x?x.title:'',"
    "mm:x&&x.getAttribute('data-mm')!=null?Number(x.getAttribute('data-mm')):null,"
    "gizmo:s.gizmoVisible===true,"
    "undo:s.undoDepth||0,"
    "redo:s.redoDepth||0,"
    "lastMove:s.lastMove||null,"
    "error:s.lastError||''"
    "});})()"
)

MOVE_DRAG_EXPR = (
    "(function(){"
    "if(typeof window.__cadcamGizmoDrag!=='function') return 'missing-drag';"
    "var plan=window.__cadcamGizmoDrag('x',10);"
    "if(!plan||!plan.down||!plan.up) return JSON.stringify({error:'no-plan',handle:plan&&plan.handle});"
    "if(plan.handle!=='x') return JSON.stringify({error:'handle',handle:plan.handle});"
    "var el=document.getElementById('viewport');"
    "function fire(type,x,y){"
    "var ending=type==='pointerup'||type==='pointercancel';"
    "el.dispatchEvent(new PointerEvent(type,{"
    "bubbles:true,cancelable:true,pointerId:7,pointerType:'mouse',isPrimary:true,"
    "button:0,buttons:ending?0:1,clientX:x,clientY:y}));}"
    "fire('pointerdown',plan.down.x,plan.down.y);"
    "fire('pointermove',(plan.down.x+plan.up.x)/2,(plan.down.y+plan.up.y)/2);"
    "fire('pointermove',plan.up.x,plan.up.y);"
    "fire('pointerup',plan.up.x,plan.up.y);"
    "var s=window.__cadcamExportState||{};"
    "var hint=document.getElementById('statusHint');"
    "return JSON.stringify({handle:plan.handle,"
    "span:Math.hypot(plan.up.x-plan.down.x,plan.up.y-plan.down.y),"
    "lastMove:s.lastMove||null,gizmo:s.gizmoVisible===true,"
    "undo:s.undoDepth||0,redo:s.redoDepth||0,"
    "hint:hint?hint.textContent:'',error:s.lastError||''});"
    "})()"
)

MOVE_FIELD_EXPR = (
    "(function(){"
    "var el=document.getElementById('posX');"
    "if(!el) return JSON.stringify({error:'missing'});"
    "if(el.disabled) return JSON.stringify({error:'disabled',title:el.title||''});"
    "var before=Number(el.getAttribute('data-mm'));"
    "el.value=String(before+10);"
    "el.dispatchEvent(new Event('change',{bubbles:true}));"
    "var s=window.__cadcamExportState||{};"
    "var hint=document.getElementById('statusHint');"
    "return JSON.stringify({before:before,after:Number(el.getAttribute('data-mm')),"
    "lastMove:s.lastMove||null,undo:s.undoDepth||0,redo:s.redoDepth||0,"
    "disabled:!!el.disabled,title:el.title||'',"
    "hint:hint?hint.textContent:'',error:s.lastError||''});"
    "})()"
)


def _assembly_doc(cdp: Cdp) -> tuple[dict[str, Any] | None, str]:
    return _json_eval(
        cdp,
        "(function(){var a=window.__cadcamAssembly?window.__cadcamAssembly():null;"
        "return a?JSON.stringify(a):'';})()",
        timeout=60,
    )


def _asm_part(doc: dict[str, Any] | None, name: str) -> dict[str, Any]:
    if not doc:
        return {}
    return _named_part(doc, name) or {}


def multi_body_move_problems(cdp: Cdp, origin: str) -> list[str]:
    """Several bodies: body/item selection shows the move gizmo (SC4 multi OK).

    Park SC4: gizmo centers on single or multi body/item. Then pick one part
    and drag; a plain primitive must update its placement. A Boolean result
    may bake the translation.
    """
    try:
        set_desktop(cdp)
    except (RuntimeError, TimeoutError, OSError) as exc:
        return [f"multi move desktop {exc}"]
    url = origin + "/?demo=assembly"
    print(f"load multi_body_move {url}", flush=True)
    loaded, load_problems = wait_for_case(cdp, origin, url, PAGE_TIMEOUT_S)
    if load_problems or not isinstance(loaded, dict):
        return ["multi move load", *load_problems[:20]]
    if loaded.get("demo") != "assembly" or int(loaded.get("bodyCount") or 0) != 2:
        return [f"multi move scene {loaded.get('demo')!r} bodies {loaded.get('bodyCount')!r}"]
    # SC4 / park: gizmo centers on multi body/item selection (not hidden).
    if loaded.get("gizmoVisible") is not True or loaded.get("posDisabled") is not False:
        return [f"multi move both selected gizmo {loaded.get('gizmoVisible')!r} disabled {loaded.get('posDisabled')!r}"]
    both, both_err = _json_eval(cdp, MOVE_POS_EXPR)
    if both_err or not both:
        return [f"multi move both fields {both_err}"]
    if both.get("disabled") is not False or both.get("gizmo") is not True:
        return [f"multi move both fields state {both}"]
    if "Select one part" in str(both.get("title") or ""):
        return [f"multi move both blocked {both.get('title')!r}"]

    cyl_id, cyl_err = _part_row_id(cdp, "Cylinder")
    if cyl_err or not cyl_id:
        return [f"multi move cylinder id {cyl_err or cyl_id!r}"]
    picked, pick_err = _json_eval(
        cdp,
        "(function(){"
        f"if(typeof window.__cadcamPickPart!=='function') return 'missing';"
        f"return JSON.stringify(window.__cadcamPickPart({json.dumps(cyl_id)}));"
        "})()",
    )
    if pick_err or not picked or picked.get("kind") != "cylinder":
        return [f"multi move pick {pick_err or picked}"]
    shown, shown_err = _json_eval(cdp, MOVE_POS_EXPR)
    if shown_err or not shown:
        return [f"multi move shown {shown_err}"]
    if shown.get("gizmo") is not True or shown.get("disabled") is not False or shown.get("title"):
        return [f"multi move cylinder fields {shown}"]
    if not _near(shown.get("mm"), 10.0, 0.05):
        return [f"multi move cylinder x {shown.get('mm')!r}"]

    marked, mark_err = _json_eval(
        cdp,
        "(function(){"
        f"var m=window.__cadcamShapeMark?window.__cadcamShapeMark({json.dumps(cyl_id)},'keep'):null;"
        "return m?JSON.stringify(m):'missing';})()",
    )
    if mark_err or not marked or marked.get("mark") != "keep":
        return [f"multi move mark {mark_err or marked}"]
    dragged, drag_err = _json_eval(cdp, MOVE_DRAG_EXPR, timeout=120)
    if drag_err or not dragged:
        return [f"multi move drag {drag_err}"]
    if dragged.get("error") or dragged.get("handle") != "x":
        return [f"multi move drag plan {dragged}"]
    try:
        span = float(dragged.get("span"))
    except (TypeError, ValueError):
        span = 0.0
    if span < 8:
        return [f"multi move drag span {dragged.get('span')!r}"]
    move = dragged.get("lastMove") if isinstance(dragged.get("lastMove"), dict) else {}
    if move.get("baked") is not False or move.get("shapeSame") is not True:
        return [f"multi move primitive bake {dragged}"]
    if int(dragged.get("undo") or 0) != 1:
        return [f"multi move drag depth {dragged}"]
    if not _near((move.get("placement") or {}).get("x"), 20.0, 0.05):
        return [f"multi move placement {move}"]
    kept, kept_err = _json_eval(
        cdp,
        "(function(){"
        f"var m=window.__cadcamShapeMark?window.__cadcamShapeMark({json.dumps(cyl_id)}):null;"
        "return m?JSON.stringify(m):'missing';})()",
    )
    if kept_err or not kept or kept.get("mark") != "keep":
        return [f"multi move mark lost {kept_err or kept}"]
    doc, doc_err = _assembly_doc(cdp)
    if doc_err or not doc:
        return [f"multi move assembly {doc_err}"]
    cyl = _asm_part(doc, "Cylinder")
    box = _asm_part(doc, "Box")
    if cyl.get("shapeLocal") is not True or not _near((cyl.get("placement") or {}).get("x"), 20.0, 0.05):
        return [f"multi move cylinder placed {cyl}"]
    box_place = box.get("placement") or {}
    if not _near(box_place.get("x"), 0.0, 0.05) or not _near(box_place.get("z"), 10.0, 0.05):
        return [f"multi move box moved {box}"]

    undone, undo_err = resize_call(cdp, {"undo": True}, timeout=120)
    if undo_err or not undone or int(undone.get("undoDepth") or 0) != 0 or int(undone.get("redoDepth") or 0) != 1:
        return [f"multi move undo {undo_err or undone}"]
    doc, doc_err = _assembly_doc(cdp)
    cyl = _asm_part(doc, "Cylinder")
    if doc_err or not _near((cyl.get("placement") or {}).get("x"), 10.0, 0.05):
        return [f"multi move undo placement {doc_err or cyl}"]
    redone, redo_err = resize_call(cdp, {"redo": True}, timeout=120)
    if redo_err or not redone or int(redone.get("undoDepth") or 0) != 1 or int(redone.get("redoDepth") or 0) != 0:
        return [f"multi move redo {redo_err or redone}"]
    doc, doc_err = _assembly_doc(cdp)
    cyl = _asm_part(doc, "Cylinder")
    if doc_err or not _near((cyl.get("placement") or {}).get("x"), 20.0, 0.05):
        return [f"multi move redo placement {doc_err or cyl}"]
    cleared, clear_err = resize_call(cdp, {"undo": True}, timeout=120)
    if clear_err or not cleared or int(cleared.get("undoDepth") or 0) != 0:
        return [f"multi move clear {clear_err or cleared}"]

    added, add_err = eval_expr(
        cdp,
        "(function(){var b=document.querySelector('[data-action=\"primitive\"][data-kind=\"cylinder\"]');"
        "if(!b) return 'missing'; b.click(); return 'added';})()",
        timeout=120,
    )
    if add_err or added != "added":
        return [f"multi move add {added or add_err}"]
    for name in ("Box", "Cylinder"):
        _clicked, click_err = _click_part(cdp, name)
        if click_err:
            return [f"multi move union select {name} {click_err}"]
    union, union_err = eval_expr(
        cdp,
        "(function(){var b=document.querySelector('[data-action=\"boolean\"][data-op=\"union\"]');"
        "if(!b) return 'missing'; if(b.disabled) return 'disabled'; b.click();"
        "var s=window.__cadcamExportState||{};"
        "return JSON.stringify({bodies:s.bodyCount,gizmo:s.gizmoVisible===true,"
        "disabled:s.posDisabled===true,error:s.lastError||''});})()",
        timeout=120,
    )
    if union_err or not isinstance(union, str) or not union.startswith("{"):
        return [f"multi move union {union or union_err}"]
    try:
        union_state = json.loads(union)
    except json.JSONDecodeError:
        return [f"multi move union {union}"]
    if int(union_state.get("bodies") or 0) != 2 or union_state.get("error"):
        return [f"multi move union result {union_state}"]
    if union_state.get("gizmo") is not True or union_state.get("disabled") is not False:
        return [f"multi move union gizmo {union_state}"]
    union_id, union_id_err = _part_row_id(cdp, "Union 1")
    if union_id_err or not union_id:
        return [f"multi move union id {union_id_err or union_id!r}"]
    planned, plan_err = _json_eval(
        cdp,
        "(function(){var p=window.__cadcamGizmoDrag?window.__cadcamGizmoDrag('x',10):null;"
        "return p?JSON.stringify({handle:p.handle}):'missing';})()",
    )
    if plan_err or not planned or planned.get("handle") != "x":
        return [f"multi move union handle {plan_err or planned}"]
    stamped, stamp_err = _json_eval(
        cdp,
        "(function(){"
        f"var m=window.__cadcamShapeMark?window.__cadcamShapeMark({json.dumps(union_id)},'bake'):null;"
        "return m?JSON.stringify(m):'missing';})()",
    )
    if stamp_err or not stamped or stamped.get("mark") != "bake":
        return [f"multi move union mark {stamp_err or stamped}"]
    before_doc, before_err = _assembly_doc(cdp)
    extra_before = _asm_part(before_doc, "Cylinder 3")
    if before_err or extra_before.get("shapeLocal") is not True:
        return [f"multi move extra before {before_err or extra_before}"]
    baked, bake_err = _json_eval(cdp, MOVE_FIELD_EXPR, timeout=120)
    if bake_err or not baked:
        return [f"multi move union field {bake_err}"]
    if baked.get("error") and baked.get("error") != "disabled":
        return [f"multi move union field error {baked}"]
    baked_move = baked.get("lastMove") if isinstance(baked.get("lastMove"), dict) else {}
    if baked_move.get("baked") is not True or baked_move.get("shapeSame") is not False:
        return [f"multi move union baked {baked}"]
    if not _near(baked.get("after"), float(baked.get("before") or 0) + 10.0, 0.05):
        return [f"multi move union x {baked.get('before')!r} -> {baked.get('after')!r}"]
    gone, gone_err = _json_eval(
        cdp,
        "(function(){"
        f"var m=window.__cadcamShapeMark?window.__cadcamShapeMark({json.dumps(union_id)}):null;"
        "return m?JSON.stringify(m):'missing';})()",
    )
    if gone_err or not gone or gone.get("mark"):
        return [f"multi move union mark kept {gone_err or gone}"]
    after_doc, after_err = _assembly_doc(cdp)
    extra_after = _asm_part(after_doc, "Cylinder 3")
    if after_err or not _near((extra_after.get("placement") or {}).get("x"), (extra_before.get("placement") or {}).get("x"), 0.05):
        return [f"multi move extra shifted {after_err or extra_after}"]
    union_depth = int(baked.get("undo") or 0)

    extra_id, extra_id_err = _part_row_id(cdp, "Cylinder 3")
    if extra_id_err or not extra_id:
        return [f"multi move extra id {extra_id_err or extra_id!r}"]
    picked_extra, extra_pick_err = _json_eval(
        cdp,
        "(function(){"
        f"return JSON.stringify(window.__cadcamPickPart({json.dumps(extra_id)}));"
        "})()",
    )
    if extra_pick_err or not picked_extra or picked_extra.get("kind") != "cylinder":
        return [f"multi move pick extra {extra_pick_err or picked_extra}"]
    slid, slide_err = _json_eval(cdp, MOVE_FIELD_EXPR, timeout=120)
    if slide_err or not slid:
        return [f"multi move extra field {slide_err}"]
    slid_move = slid.get("lastMove") if isinstance(slid.get("lastMove"), dict) else {}
    if slid_move.get("baked") is not False or slid_move.get("shapeSame") is not True:
        return [f"multi move extra bake {slid}"]
    if not _near((slid_move.get("placement") or {}).get("x"), float((extra_before.get("placement") or {}).get("x") or 0) + 10.0, 0.05):
        return [f"multi move extra placement {slid_move}"]
    extra_depth = int(slid.get("undo") or 0)
    if extra_depth != union_depth + 1:
        return [f"multi move extra depth {extra_depth} after {union_depth}"]

    back, back_err = resize_call(cdp, {"undo": True}, timeout=120)
    if back_err or not back or int(back.get("undoDepth") or 0) != union_depth:
        return [f"multi move extra undo {back_err or back}"]
    doc, doc_err = _assembly_doc(cdp)
    extra = _asm_part(doc, "Cylinder 3")
    if doc_err or not _near((extra.get("placement") or {}).get("x"), (extra_before.get("placement") or {}).get("x"), 0.05):
        return [f"multi move extra undo placement {doc_err or extra}"]
    again, again_err = resize_call(cdp, {"redo": True}, timeout=120)
    if again_err or not again or int(again.get("undoDepth") or 0) != extra_depth:
        return [f"multi move extra redo {again_err or again}"]
    doc, doc_err = _assembly_doc(cdp)
    extra = _asm_part(doc, "Cylinder 3")
    if doc_err or not _near((extra.get("placement") or {}).get("x"), float((extra_before.get("placement") or {}).get("x") or 0) + 10.0, 0.05):
        return [f"multi move extra redo placement {doc_err or extra}"]
    back, back_err = resize_call(cdp, {"undo": True}, timeout=120)
    if back_err or not back or int(back.get("undoDepth") or 0) != union_depth:
        return [f"multi move extra undo again {back_err or back}"]
    union_back, union_back_err = resize_call(cdp, {"undo": True}, timeout=120)
    if union_back_err or not union_back or int(union_back.get("undoDepth") or 0) != union_depth - 1:
        return [f"multi move union undo {union_back_err or union_back}"]
    restored, restored_err = _json_eval(cdp, MOVE_POS_EXPR)
    if restored_err or not restored or not _near(restored.get("mm"), baked.get("before"), 0.05):
        return [f"multi move union undo x {restored_err or restored}"]
    union_fwd, union_fwd_err = resize_call(cdp, {"redo": True}, timeout=120)
    if union_fwd_err or not union_fwd or int(union_fwd.get("undoDepth") or 0) != union_depth:
        return [f"multi move union redo {union_fwd_err or union_fwd}"]
    forwarded, forwarded_err = _json_eval(cdp, MOVE_POS_EXPR)
    if forwarded_err or not forwarded or not _near(forwarded.get("mm"), float(baked.get("before") or 0) + 10.0, 0.05):
        return [f"multi move union redo x {forwarded_err or forwarded}"]
    print("multi body move pass", flush=True)
    return []


def _css_rgb(hex_color: str) -> str:
    n = int(hex_color[1:], 16)
    return f"rgb({(n >> 16) & 255}, {(n >> 8) & 255}, {n & 255})"


PART_CHIPS_EXPR = (
    "(function(){"
    "function chip(name){"
    "var rows=document.querySelectorAll('#partList .part-row');"
    "for(var i=0;i<rows.length;i++){"
    "var label=rows[i].querySelector('.part-name');"
    "if(!label||label.textContent!==name) continue;"
    "var el=rows[i].querySelector('.part-chip');"
    "if(!el) return null;"
    "return {material:el.getAttribute('data-material')||'',color:el.getAttribute('data-color')||'',"
    "bg:getComputedStyle(el).backgroundColor||'',title:el.title||'',"
    "h:rows[i].getBoundingClientRect().height};}"
    "return null;}"
    "var mat=document.getElementById('materialChip');"
    "return JSON.stringify({box:chip('Box'),cyl:chip('Cylinder'),"
    "swatch:mat?{hidden:mat.hidden===true,material:mat.getAttribute('data-material')||'',"
    "color:mat.getAttribute('data-color')||'',bg:getComputedStyle(mat).backgroundColor||''}:null});"
    "})()"
)


def _chip_ok(chip: Any, tag: str, hex_color: str) -> bool:
    if not isinstance(chip, dict):
        return False
    bg = str(chip.get("bg") or "").replace(" ", "")
    want = _css_rgb(hex_color).replace(" ", "")
    return (
        chip.get("material") == tag
        and str(chip.get("color") or "").upper() == hex_color.upper()
        and (bg == want or bg == want.replace("rgb(", "rgba(").replace(")", ",1)"))
        and chip.get("title") == tag
    )


def multi_body_color_problems(cdp: Cdp, origin: str) -> list[str]:
    """PETG and TPU use their own colours in the parts list and on unselected meshes.

    Repro before the fix: the parts list showed the material name only, and every
    unselected body used the same blue. PLA, PETG, and TPU already had canonical colours.
    """
    try:
        set_desktop(cdp)
    except (RuntimeError, TimeoutError, OSError) as exc:
        return [f"multi color desktop {exc}"]
    url = origin + "/?demo=assembly"
    print(f"load multi_body_color {url}", flush=True)
    loaded, load_problems = wait_for_case(cdp, origin, url, PAGE_TIMEOUT_S)
    if load_problems or not isinstance(loaded, dict):
        return ["multi color load", *load_problems[:20]]
    chips, chip_err = _json_eval(cdp, PART_CHIPS_EXPR)
    if chip_err or not chips:
        return [f"multi color chips {chip_err}"]
    if not _chip_ok(chips.get("box"), "PLA", "#F4F4F4"):
        return [f"multi color pla {chips.get('box')}"]
    if not _chip_ok(chips.get("cyl"), "PETG", "#B9D6F2"):
        return [f"multi color petg {chips.get('cyl')}"]
    if chips["box"].get("color") == chips["cyl"].get("color"):
        return ["multi color pla and petg match"]
    box_h = float((chips.get("box") or {}).get("h") or 0)
    if abs(box_h - 44) > 1:
        return [f"multi color row height {box_h}"]
    swatch = chips.get("swatch") if isinstance(chips.get("swatch"), dict) else {}
    if swatch.get("hidden") is not True:
        return [f"multi color mixed swatch {swatch}"]

    cyl_id, cyl_err = _part_row_id(cdp, "Cylinder")
    box_id, box_err = _part_row_id(cdp, "Box")
    if cyl_err or box_err or not cyl_id or not box_id:
        return [f"multi color ids {cyl_err or box_err}"]
    picked, pick_err = _json_eval(
        cdp,
        "(function(){"
        f"return JSON.stringify(window.__cadcamPickPart({json.dumps(cyl_id)}));"
        "})()",
    )
    if pick_err or not picked:
        return [f"multi color pick {pick_err or picked}"]
    changed, change_err = eval_expr(
        cdp,
        "(function(){var sel=document.getElementById('partMaterial');"
        "if(!sel) return 'missing'; sel.value='TPU';"
        "sel.dispatchEvent(new Event('change',{bubbles:true}));"
        "return sel.value;})()",
    )
    if change_err or changed != "TPU":
        return [f"multi color set tpu {changed or change_err}"]
    painted, paint_err = _json_eval(cdp, PART_CHIPS_EXPR)
    if paint_err or not painted:
        return [f"multi color after {paint_err}"]
    if not _chip_ok(painted.get("cyl"), "TPU", "#E7C36A"):
        return [f"multi color tpu chip {painted.get('cyl')}"]
    if not _chip_ok(painted.get("box"), "PLA", "#F4F4F4"):
        return [f"multi color box changed {painted.get('box')}"]
    one = painted.get("swatch") if isinstance(painted.get("swatch"), dict) else {}
    if one.get("hidden") is not False or str(one.get("color") or "").upper() != "#E7C36A":
        return [f"multi color material chip {one}"]

    # Leave the cylinder unselected so its viewport colour is the material, not the selection.
    picked_box, box_pick_err = _json_eval(
        cdp,
        "(function(){"
        f"return JSON.stringify(window.__cadcamPickPart({json.dumps(box_id)}));"
        "})()",
    )
    if box_pick_err or not picked_box:
        return [f"multi color pick box {box_pick_err or picked_box}"]
    colors, color_err = _json_eval(
        cdp,
        "(function(){"
        "function one(id){return window.__cadcamPartColor?window.__cadcamPartColor(id):null;}"
        f"return JSON.stringify({{cyl:one({json.dumps(cyl_id)}),box:one({json.dumps(box_id)})}});"
        "})()",
    )
    if color_err or not colors:
        return [f"multi color meshes {color_err}"]
    cyl_color = colors.get("cyl") if isinstance(colors.get("cyl"), dict) else {}
    box_color = colors.get("box") if isinstance(colors.get("box"), dict) else {}
    if cyl_color.get("selected") is not False or str(cyl_color.get("mesh") or "").upper() != "#E7C36A":
        return [f"multi color cylinder mesh {cyl_color}"]
    if str(cyl_color.get("color") or "").upper() != "#E7C36A" or cyl_color.get("tag") != "TPU":
        return [f"multi color cylinder tag {cyl_color}"]
    if box_color.get("selected") is not True or str(box_color.get("mesh") or "").upper() != "#FF4FD8":
        return [f"multi color selected box {box_color}"]
    if str(box_color.get("color") or "").upper() != "#F4F4F4":
        return [f"multi color box tag {box_color}"]
    print("multi body color pass", flush=True)
    return []


def cylinder_live_volume_problems(cdp: Cdp, origin: str) -> list[str]:
    """Typed cylinder resize among other bodies must match the reloaded BRep volume."""
    try:
        set_desktop(cdp)
    except (RuntimeError, TimeoutError, OSError) as exc:
        return [f"cyl volume desktop {exc}"]
    url = origin + "/?demo=assembly"
    print(f"load cyl_volume {url}", flush=True)
    loaded, load_problems = wait_for_case(cdp, origin, url, PAGE_TIMEOUT_S)
    if load_problems or not isinstance(loaded, dict):
        return ["cyl volume load", *load_problems[:20]]
    cyl_id, cyl_err = _part_row_id(cdp, "Cylinder")
    if cyl_err or not cyl_id:
        return [f"cyl volume id {cyl_err or cyl_id!r}"]
    picked, pick_err = _json_eval(
        cdp,
        "(function(){"
        f"return JSON.stringify(window.__cadcamPickPart({json.dumps(cyl_id)}));"
        "})()",
    )
    if pick_err or not picked:
        return [f"cyl volume pick {pick_err or picked}"]
    resized, resize_err = resize_call(
        cdp, {"lock": False, "diameter": 14, "height": 22}, timeout=120
    )
    if resize_err or not resized:
        return [f"cyl volume resize {resize_err}"]
    if resized.get("done") != "RESIZE_DONE":
        return [f"cyl volume result {resized.get('done')!r} {resized.get('error')!r}"]
    if not _near(resized.get("dx"), 14.0) or not _near(resized.get("dy"), 14.0) or not _near(resized.get("dz"), 22.0):
        return [f"cyl volume bounds {resized.get('dx')!r} {resized.get('dy')!r} {resized.get('dz')!r}"]
    want = math.pi * 7.0 * 7.0 * 22.0
    live = resized.get("volumeMm3")
    if not _near(live, want, 0.01):
        return [f"cyl volume live {live!r} want {want}"]
    hook, hook_err = _json_eval(
        cdp,
        "(function(){"
        "var h=window.__cadcamProject;"
        "if(!h||typeof h.saveText!=='function'||typeof h.loadText!=='function') return JSON.stringify({error:'missing'});"
        "var saved=h.saveText();"
        "if(!saved||saved.ok!==true) return JSON.stringify({error:saved&&saved.error||'save'});"
        "var loaded=h.loadText(saved.text,true);"
        "if(!loaded||loaded.ok!==true) return JSON.stringify({error:loaded&&loaded.error||'load'});"
        "var rows=h.measures()||[];"
        "var cyl=null;"
        "for(var i=0;i<rows.length;i++){if(rows[i].name==='Cylinder') cyl=rows[i];}"
        "return JSON.stringify({count:rows.length,volume:cyl&&cyl.volumeMm3});"
        "})()",
        timeout=180,
    )
    if hook_err or not hook or hook.get("error"):
        return [f"cyl volume reload {hook_err or hook}"]
    if not _near(hook.get("volume"), want, 0.01):
        return [f"cyl volume reloaded {hook.get('volume')!r} want {want}"]
    if not _near(hook.get("volume"), live, 0.01):
        return [f"cyl volume live vs reload {live!r} {hook.get('volume')!r}"]
    print("cyl live volume pass", flush=True)
    return []


def unlocked_centre_resize_problems(cdp: Cdp, origin: str) -> list[str]:
    """Unlocked single-body resize must keep the typed centre."""
    try:
        set_desktop(cdp)
    except (RuntimeError, TimeoutError, OSError) as exc:
        return [f"centre resize desktop {exc}"]
    url = origin + "/?primitive=box"
    print(f"load centre_resize {url}", flush=True)
    loaded, load_problems = wait_for_case(cdp, origin, url, PAGE_TIMEOUT_S)
    if load_problems or not isinstance(loaded, dict):
        return ["centre resize load", *load_problems[:20]]
    moved, move_err = resize_call(
        cdp, {"lock": False, "field": "primCx", "text": "40"}, timeout=120
    )
    if move_err or not moved:
        return [f"centre resize cx {move_err}"]
    moved, move_err = resize_call(cdp, {"lock": False, "field": "primCy", "text": "15"}, timeout=120)
    if move_err or not moved:
        return [f"centre resize cy {move_err}"]
    moved, move_err = resize_call(cdp, {"lock": False, "field": "primCz", "text": "3"}, timeout=120)
    if move_err or not moved:
        return [f"centre resize cz {move_err}"]
    sized, size_err = resize_call(
        cdp, {"lock": False, "sx": 80, "sy": 30, "sz": 6}, timeout=120
    )
    if size_err or not sized:
        return [f"centre resize size {size_err}"]
    if sized.get("done") != "RESIZE_DONE":
        return [f"centre resize result {sized.get('done')!r} {sized.get('error')!r}"]
    params = sized.get("params") or {}
    place = sized.get("placement") or {}
    if not _near(params.get("cx"), 40.0, 1e-6) or not _near(params.get("cy"), 15.0, 1e-6) or not _near(params.get("cz"), 3.0, 1e-6):
        return [f"centre resize params {params}"]
    if not _near(place.get("x"), 40.0, 1e-6) or not _near(place.get("y"), 15.0, 1e-6) or not _near(place.get("z"), 3.0, 1e-6):
        return [f"centre resize placement {place}"]
    if not _near(sized.get("dx"), 80.0, 1e-4) or not _near(sized.get("dy"), 30.0, 1e-4) or not _near(sized.get("dz"), 6.0, 1e-4):
        return [f"centre resize size {sized.get('dx')!r} {sized.get('dy')!r} {sized.get('dz')!r}"]
    if sized.get("shapeLocal") is True and (
        not _near(sized.get("cx"), 0.0, 1e-3) or not _near(sized.get("cy"), 0.0, 1e-3) or not _near(sized.get("cz"), 0.0, 1e-3)
    ):
        return [f"centre resize local centre {sized.get('cx')!r} {sized.get('cy')!r} {sized.get('cz')!r}"]
    print("unlocked centre resize pass", flush=True)
    return []


def combine_gizmo_x_problems(cdp: Cdp, origin: str) -> list[str]:
    """Combine must not cover the gizmo X handle; the handle point hits the canvas."""
    try:
        set_desktop(cdp)
    except (RuntimeError, TimeoutError, OSError) as exc:
        return [f"gizmo x desktop {exc}"]
    url = origin + "/?demo=assembly"
    print(f"load combine_gizmo {url}", flush=True)
    loaded, load_problems = wait_for_case(cdp, origin, url, PAGE_TIMEOUT_S)
    if load_problems or not isinstance(loaded, dict):
        return ["combine gizmo load", *load_problems[:20]]
    cyl_id, cyl_err = _part_row_id(cdp, "Cylinder")
    if cyl_err or not cyl_id:
        return [f"combine gizmo id {cyl_err or cyl_id!r}"]
    picked, pick_err = _json_eval(
        cdp,
        "(function(){"
        f"return JSON.stringify(window.__cadcamPickPart({json.dumps(cyl_id)}));"
        "})()",
    )
    if pick_err or not picked:
        return [f"combine gizmo pick {pick_err or picked}"]
    hit, hit_err = _json_eval(
        cdp,
        "(function(){"
        "var s=window.__cadcamExportState||{};"
        "var g=s.gizmoHandles||{};"
        "var plan=window.__cadcamGizmoDrag?window.__cadcamGizmoDrag('x',10):null;"
        "var pt=plan&&plan.down?plan.down:g.xPage;"
        "if(!pt) return JSON.stringify({error:'no-handle',gizmo:s.gizmoVisible===true,g:g});"
        "var el=document.elementFromPoint(pt.x,pt.y);"
        "var id=el?(el.id||el.getAttribute('data-action')||el.tagName):'none';"
        "var canvas=document.getElementById('canvas');"
        "var vp=document.getElementById('viewport');"
        "var combine=document.getElementById('combineBtn');"
        "var onCanvas=!!(el&&(el.id==='canvas'||el.id==='viewport'||(vp&&vp.contains(el)&&!(combine&&combine.contains(el)))));"
        "return JSON.stringify({id:id,onCanvas:onCanvas,gizmo:s.gizmoVisible===true,xHits:g.xHitsCanvas===true,pt:pt});"
        "})()",
    )
    if hit_err or not hit:
        return [f"combine gizmo hit {hit_err}"]
    if hit.get("gizmo") is not True:
        return [f"combine gizmo hidden {hit}"]
    if hit.get("id") == "combineBtn" or hit.get("onCanvas") is not True:
        return [f"combine covers gizmo x {hit}"]
    print("combine gizmo x pass", flush=True)
    return []


def boolean_unique_names_problems(cdp: Cdp, origin: str) -> list[str]:
    """Boolean results are Cut 1, Cut 2, ... and survive save/load."""
    try:
        set_desktop(cdp)
    except (RuntimeError, TimeoutError, OSError) as exc:
        return [f"bool names desktop {exc}"]
    url = origin + "/?pair=overlap"
    print(f"load bool_names {url}", flush=True)
    loaded, load_problems = wait_for_case(cdp, origin, url, PAGE_TIMEOUT_S)
    if load_problems or not isinstance(loaded, dict):
        return ["bool names load", *load_problems[:20]]
    named, named_err = _json_eval(
        cdp,
        "(function(){"
        "function names(){return (window.__cadcamExportState||{}).projectNames||[];}"
        "function rows(){return document.querySelectorAll('#partList .part-row');}"
        "function clearSel(){var guard=0;while(guard<12){var on=document.querySelector('#partList .part-row.is-on');if(!on) break;on.click();guard++;}}"
        "function selectAll(){clearSel();var n=rows().length;for(var i=0;i<n;i++){var list=rows();if(i<list.length) list[i].click();}}"
        "function selectLastTwo(){clearSel();var list=rows();if(list.length<2) return;list[list.length-2].click();list=rows();list[list.length-1].click();}"
        "function clickCut(){"
        "var tab=document.querySelector('[data-action=\"tab\"][data-tab=\"model\"]');"
        "if(tab) tab.click();"
        "var buttons=document.querySelectorAll('[data-action=\"boolean\"][data-op=\"cut\"]');"
        "var b=null;"
        "for(var i=0;i<buttons.length;i++){"
        "if(buttons[i].disabled) continue;"
        "var st=getComputedStyle(buttons[i]);"
        "if(st.display==='none'||st.visibility==='hidden') continue;"
        "b=buttons[i]; break;}"
        "if(!b) b=document.getElementById('boolCut')||buttons[0];"
        "if(!b) return 'missing'; if(b.disabled) return 'disabled sel='+((window.__cadcamExportState||{}).selectionCount); b.click(); return 'cut';"
        "}"
        "selectAll();"
        "var first=clickCut();"
        "if(first!=='cut') return JSON.stringify({error:first,names:names()});"
        "var afterFirst=names().slice();"
        "var add=document.querySelector('[data-action=\"primitive\"][data-kind=\"box\"]');"
        "if(!add) return JSON.stringify({error:'add missing',names:afterFirst});"
        "add.click(); add.click();"
        "if(rows().length<3) return JSON.stringify({error:'need three',names:names(),rows:rows().length});"
        "selectLastTwo();"
        "var second=clickCut();"
        "if(second!=='cut') return JSON.stringify({error:second,names:names()});"
        "var afterSecond=names().slice();"
        "var h=window.__cadcamProject;"
        "var before=h&&h.measures?h.measures():[];"
        "var saved=h&&h.saveText?h.saveText():null;"
        "if(!saved||saved.ok!==true) return JSON.stringify({error:saved&&saved.error||'save',names:afterSecond});"
        "var doc=null; try { doc=JSON.parse(saved.text); } catch (e) { doc=null; }"
        "var prims=[];"
        "if(doc&&doc.parts){for(var p=0;p<doc.parts.length;p++) prims.push(doc.parts[p].primitive);}"
        "var loaded=h.loadText(saved.text,true);"
        "if(!loaded||loaded.ok!==true) return JSON.stringify({error:loaded&&loaded.error||'load',names:afterSecond});"
        "var after=h.measures?h.measures():[];"
        "return JSON.stringify({first:afterFirst,second:afterSecond,reloaded:(window.__cadcamExportState||{}).projectNames||[],before:before,after:after,prims:prims});"
        "})()",
        timeout=180,
    )
    if named_err or not named:
        return [f"bool names eval {named_err}"]
    if named.get("error"):
        return [f"bool names {named}"]
    first = named.get("first") if isinstance(named.get("first"), list) else []
    second = named.get("second") if isinstance(named.get("second"), list) else []
    reloaded = named.get("reloaded") if isinstance(named.get("reloaded"), list) else []
    if "Cut 1" not in first:
        return [f"bool names first {first}"]
    if "Cut 1" not in second or "Cut 2" not in second:
        return [f"bool names second {second}"]
    if second.count("Cut 1") != 1 or second.count("Cut 2") != 1:
        return [f"bool names duplicate {second}"]
    if reloaded != second:
        return [f"bool names reload {reloaded} vs {second}"]
    before_rows = named.get("before") if isinstance(named.get("before"), list) else []
    after_rows = named.get("after") if isinstance(named.get("after"), list) else []
    prims = named.get("prims") if isinstance(named.get("prims"), list) else []
    if len(before_rows) != len(second) or len(after_rows) != len(second) or len(prims) != len(second):
        return [f"bool names measures {len(before_rows)} {len(after_rows)} {len(prims)}"]
    bound_keys = ("xmin", "ymin", "zmin", "xmax", "ymax", "zmax")
    for index, (before_row, after_row) in enumerate(zip(before_rows, after_rows)):
        if not isinstance(before_row, dict) or not isinstance(after_row, dict):
            return [f"bool names row {index}"]
        if before_row.get("name") != second[index] or after_row.get("name") != second[index]:
            return [f"bool names measure {before_row.get('name')!r} {after_row.get('name')!r}"]
        try:
            same_volume = abs(float(after_row.get("volumeMm3")) - float(before_row.get("volumeMm3"))) <= 0.01
        except (TypeError, ValueError):
            same_volume = False
        if not same_volume:
            return [f"bool names volume {after_row.get('name')} {after_row.get('volumeMm3')!r} {before_row.get('volumeMm3')!r}"]
        before_bounds = before_row.get("bounds") if isinstance(before_row.get("bounds"), dict) else {}
        after_bounds = after_row.get("bounds") if isinstance(after_row.get("bounds"), dict) else {}
        for key in bound_keys:
            try:
                same_bound = abs(float(after_bounds.get(key)) - float(before_bounds.get(key))) <= 0.01
            except (TypeError, ValueError):
                same_bound = False
            if not same_bound:
                return [f"bool names bound {after_row.get('name')} {key}"]
        if prims[index] is not None:
            return [f"bool names primitive {before_row.get('name')!r}"]
        if after_row.get("source") != "brep" or after_row.get("params") is not None:
            return [f"bool names brep {after_row.get('name')!r} {after_row.get('source')!r} {after_row.get('params')!r}"]
    print("boolean unique names pass", flush=True)
    return []


CREATE_STACK_JS = """
  var s=window.__cadcamExportState||{};
  var hint=document.getElementById('statusHint');
  var names=[];
  document.querySelectorAll('#partList .part-name').forEach(function(el){
    names.push((el.textContent||'').trim());
  });
  return JSON.stringify({
    body:s.bodyCount,
    undo:s.undoDepth,
    redo:s.redoDepth,
    kind:s.primitiveKind||'',
    hint:hint?hint.textContent:'',
    names:names,
    cleared:!!s.sceneCleared
  });
"""
CREATE_STACK_EXPR = "(function(){" + CREATE_STACK_JS + "})()"
REDO_KEY_EXPR = (
    "(function(){"
    "var el=document.activeElement;"
    "if(el&&el.blur) el.blur();"
    "document.dispatchEvent(new KeyboardEvent('keydown',{key:'y',ctrlKey:true,bubbles:true,cancelable:true}));"
    + CREATE_STACK_JS
    + "})()"
)
CREATE_EXTRA_UNDO_EXPR = (
    "(function(){"
    "var el=document.activeElement;if(el&&el.blur)el.blur();"
    "document.dispatchEvent(new KeyboardEvent('keydown',{key:'z',ctrlKey:true,bubbles:true,cancelable:true}));"
    + CREATE_STACK_JS
    + "})()"
)


def _create_stack(cdp: Cdp) -> tuple[dict[str, Any] | None, str]:
    return _json_eval(cdp, CREATE_STACK_EXPR)


def _click_create_kind(cdp: Cdp, kind: str) -> tuple[dict[str, Any] | None, str]:
    return _json_eval(
        cdp,
        "(function(){"
        "var menu=document.getElementById('createMenu');"
        "if(!menu) return JSON.stringify({error:'missing menu'});"
        "if(menu.hidden){"
        "var openers=document.querySelectorAll('[data-action=\"createMenu\"]');"
        "var opener=null;"
        "for(var i=0;i<openers.length;i++){"
        "if(openers[i].closest&&openers[i].closest('[hidden]')) continue;"
        "var st=getComputedStyle(openers[i]);"
        "var r=openers[i].getBoundingClientRect();"
        "if(st.display==='none'||st.visibility==='hidden'||r.width<1||r.height<1) continue;"
        "opener=openers[i];break;"
        "}"
        "if(!opener){"
        "var sheet=document.getElementById('toolsSheet');"
        "if(!sheet||sheet.hidden){"
        "var tm=document.querySelector('[data-action=\"toolsMenu\"]');"
        "if(tm)tm.click();"
        "}"
        "var sc=document.querySelector('#toolsSheet [data-action=\"createMenu\"]');"
        "if(sc&&sheet&&!sheet.hidden) opener=sc;"
        "}"
        "if(!opener) return JSON.stringify({error:'missing create'});"
        "opener.click();"
        "}"
        f"var b=menu.querySelector('[data-kind={json.dumps(kind)}]');"
        "if(!b) return JSON.stringify({error:'missing kind'});"
        "b.click();"
        + CREATE_STACK_JS
        + "})()",
    )


def create_undo_problems(cdp: Cdp, origin: str) -> list[str]:
    """Create Box/Cylinder/Disc each push one undo step, and redo restores them."""
    try:
        set_desktop(cdp)
    except (RuntimeError, TimeoutError, OSError) as exc:
        return [f"create undo desktop {exc}"]
    url = origin + "/?primitive=box"
    print(f"load create_undo {url}", flush=True)
    loaded, load_problems = wait_for_case(cdp, origin, url, PAGE_TIMEOUT_S)
    if load_problems or not isinstance(loaded, dict):
        return ["create undo load", *load_problems[:20]]
    start, start_err = _create_stack(cdp)
    if start_err or not start or int(start.get("body") or 0) != 1 or int(start.get("undo") or 0) != 0:
        return [f"create undo start {start_err or start}"]
    added, add_err = _click_create_kind(cdp, "cylinder")
    if add_err or not added or added.get("error"):
        return [f"create cylinder click {add_err or added}"]
    names = [str(n) for n in (added.get("names") or [])]
    if int(added.get("body") or 0) != 2 or int(added.get("undo") or 0) != 1 or int(added.get("redo") or 0) != 0:
        return [f"create cylinder stack {added}"]
    if not any("Cylinder" in n for n in names):
        return [f"create cylinder names {names}"]
    raw, err = eval_expr(cdp, UNDO_KEY_EXPR)
    undone, undo_err = _key_state(raw, err)
    if undo_err or not undone or int(undone.get("body") or 0) != 1 or int(undone.get("undo") or 0) != 0:
        return [f"create cylinder undo {undo_err or undone}"]
    stack, stack_err = _create_stack(cdp)
    if stack_err or not stack or int(stack.get("redo") or 0) != 1:
        return [f"create cylinder redo depth {stack_err or stack}"]
    if "Nothing to undo" in str(stack.get("hint") or ""):
        return [f"create cylinder hint {stack.get('hint')!r}"]
    if not str(stack.get("hint") or "").startswith("Undo Create"):
        return [f"create cylinder undo hint {stack.get('hint')!r}"]
    redone, redo_err = _json_eval(cdp, REDO_KEY_EXPR)
    if redo_err or not redone or int(redone.get("body") or 0) != 2 or int(redone.get("undo") or 0) != 1:
        return [f"create cylinder redo {redo_err or redone}"]
    raw, err = eval_expr(cdp, UNDO_KEY_EXPR)
    back, back_err = _key_state(raw, err)
    if back_err or not back or int(back.get("body") or 0) != 1:
        return [f"create cylinder undo again {back_err or back}"]
    cleared = _delete_default_body(cdp, origin)
    if cleared:
        return ["create undo clear", *cleared[:12]]
    reset, reset_err = eval_expr(cdp, "window.__cadcamClearUndo()")
    if reset_err or reset is not True:
        return [f"create undo reset {reset or reset_err}"]
    empty, empty_err = _create_stack(cdp)
    if empty_err or not empty or int(empty.get("body") or 0) != 0 or int(empty.get("undo") or 0) != 0:
        return [f"create undo empty {empty_err or empty}"]
    for kind, label in (("disc", "Disc"), ("box", "Box"), ("cylinder", "Cylinder")):
        made, made_err = _click_create_kind(cdp, kind)
        if made_err or not made or made.get("error"):
            return [f"create {kind} empty click {made_err or made}"]
        names = [str(n) for n in (made.get("names") or [])]
        if int(made.get("body") or 0) != 1 or int(made.get("undo") or 0) != 1 or int(made.get("redo") or 0) != 0:
            return [f"create {kind} empty stack {made}"]
        if not any(label in n for n in names):
            return [f"create {kind} empty names {names}"]
        raw, err = eval_expr(cdp, UNDO_KEY_EXPR)
        gone, gone_err = _key_state(raw, err)
        if gone_err or not gone or int(gone.get("body") or 0) != 0 or int(gone.get("undo") or 0) != 0:
            return [f"create {kind} empty undo {gone_err or gone}"]
        stack, stack_err = _create_stack(cdp)
        if stack_err or not stack or int(stack.get("redo") or 0) != 1:
            return [f"create {kind} empty redo depth {stack_err or stack}"]
        if "Nothing to undo" in str(stack.get("hint") or ""):
            return [f"create {kind} empty hint {stack.get('hint')!r}"]
        redone, redo_err = _json_eval(cdp, REDO_KEY_EXPR)
        if redo_err or not redone or int(redone.get("body") or 0) != 1 or int(redone.get("undo") or 0) != 1:
            return [f"create {kind} empty redo {redo_err or redone}"]
        raw, err = eval_expr(cdp, UNDO_KEY_EXPR)
        gone, gone_err = _key_state(raw, err)
        if gone_err or not gone or int(gone.get("body") or 0) != 0:
            return [f"create {kind} empty undo 2 {gone_err or gone}"]
    extra, extra_err = _json_eval(cdp, CREATE_EXTRA_UNDO_EXPR)
    if extra_err or not extra or "Nothing to undo" not in str(extra.get("hint") or ""):
        return [f"create extra undo {extra_err or extra}"]
    print("create undo pass", flush=True)
    return []


def digit_hotkey_guard_problems(cdp: Cdp, origin: str) -> list[str]:
    """Desktop digits ignore selection hotkeys unless the viewport is focused."""
    try:
        set_desktop(cdp)
    except (RuntimeError, TimeoutError, OSError) as exc:
        return [f"digit hotkey desktop {exc}"]
    url = origin + "/?primitive=box"
    print(f"load digit_hotkeys {url}", flush=True)
    loaded, load_problems = wait_for_case(cdp, origin, url, PAGE_TIMEOUT_S)
    if load_problems or not isinstance(loaded, dict):
        return ["digit hotkey load", *load_problems[:20]]
    if loaded.get("selectionMode") != "item" or int(loaded.get("selectionCount") or 0) < 1:
        return [f"digit hotkey start {loaded.get('selectionMode')!r} {loaded.get('selectionCount')!r}"]

    def keyed(expr: str) -> tuple[dict[str, Any] | None, str]:
        return _json_eval(cdp, expr)

    unfocused, un_err = keyed(
        "(function(){"
        "var el=document.activeElement;if(el&&el.blur)el.blur();"
        "var before=window.__cadcamExportState||{};"
        "document.dispatchEvent(new KeyboardEvent('keydown',{key:'1',code:'Digit1',bubbles:true,cancelable:true}));"
        "var s=window.__cadcamExportState||{};"
        "return JSON.stringify({mode:s.selectionMode,count:s.selectionCount,"
        "before:before.selectionMode,active:document.activeElement?(document.activeElement.id||document.activeElement.tagName):''});"
        "})()"
    )
    if un_err or not unfocused:
        return [f"digit unfocused {un_err or unfocused}"]
    if unfocused.get("mode") != "item" or int(unfocused.get("count") or 0) < 1:
        return [f"digit unfocused changed selection {unfocused}"]
    typed, typed_err = keyed(
        "(function(){"
        "var el=document.getElementById('docName');"
        "if(!el) return JSON.stringify({error:'missing docName'});"
        "el.focus();"
        "document.dispatchEvent(new KeyboardEvent('keydown',{key:'4',code:'Digit4',bubbles:true,cancelable:true}));"
        "var s=window.__cadcamExportState||{};"
        "return JSON.stringify({mode:s.selectionMode,count:s.selectionCount,active:document.activeElement?document.activeElement.id:''});"
        "})()"
    )
    if typed_err or not typed or typed.get("error"):
        return [f"digit input {typed_err or typed}"]
    if typed.get("mode") != "item" or typed.get("active") != "docName" or int(typed.get("count") or 0) < 1:
        return [f"digit input changed selection {typed}"]
    select_hit, select_err = keyed(
        "(function(){"
        "var el=document.getElementById('partMaterial');"
        "if(!el){el=document.createElement('select');el.id='hotkeyProbeSelect';document.body.appendChild(el);}"
        "el.focus();"
        "document.dispatchEvent(new KeyboardEvent('keydown',{key:'2',code:'Digit2',bubbles:true,cancelable:true}));"
        "var s=window.__cadcamExportState||{};"
        "return JSON.stringify({mode:s.selectionMode,count:s.selectionCount,"
        "tag:document.activeElement?document.activeElement.tagName:''});"
        "})()"
    )
    if select_err or not select_hit:
        return [f"digit select {select_err or select_hit}"]
    if select_hit.get("mode") != "item" or select_hit.get("tag") != "SELECT":
        return [f"digit select changed selection {select_hit}"]
    area_hit, area_err = keyed(
        "(function(){"
        "var el=document.getElementById('hotkeyProbeArea');"
        "if(!el){el=document.createElement('textarea');el.id='hotkeyProbeArea';document.body.appendChild(el);}"
        "el.focus();"
        "document.dispatchEvent(new KeyboardEvent('keydown',{key:'3',code:'Digit3',bubbles:true,cancelable:true}));"
        "var s=window.__cadcamExportState||{};"
        "return JSON.stringify({mode:s.selectionMode,count:s.selectionCount,"
        "tag:document.activeElement?document.activeElement.tagName:''});"
        "})()"
    )
    if area_err or not area_hit:
        return [f"digit textarea {area_err or area_hit}"]
    if area_hit.get("mode") != "item" or area_hit.get("tag") != "TEXTAREA":
        return [f"digit textarea changed selection {area_hit}"]
    edit_hit, edit_err = keyed(
        "(function(){"
        "var el=document.getElementById('hotkeyProbeEdit');"
        "if(!el){el=document.createElement('div');el.id='hotkeyProbeEdit';el.contentEditable='true';document.body.appendChild(el);}"
        "el.focus();"
        "document.dispatchEvent(new KeyboardEvent('keydown',{key:'1',code:'Digit1',bubbles:true,cancelable:true}));"
        "var s=window.__cadcamExportState||{};"
        "return JSON.stringify({mode:s.selectionMode,count:s.selectionCount,"
        "edit:!!(document.activeElement&&document.activeElement.isContentEditable)});"
        "})()"
    )
    if edit_err or not edit_hit:
        return [f"digit contenteditable {edit_err or edit_hit}"]
    if edit_hit.get("mode") != "item" or edit_hit.get("edit") is not True:
        return [f"digit contenteditable changed selection {edit_hit}"]
    intended, intended_err = keyed(
        "(function(){"
        "var vp=document.getElementById('viewport');"
        "if(!vp) return JSON.stringify({error:'missing viewport'});"
        "if(vp.focus) vp.focus();"
        "document.dispatchEvent(new KeyboardEvent('keydown',{key:'1',code:'Digit1',bubbles:true,cancelable:true}));"
        "var s=window.__cadcamExportState||{};"
        "return JSON.stringify({mode:s.selectionMode,count:s.selectionCount,gizmo:s.gizmoVisible,"
        "active:document.activeElement?document.activeElement.id:''});"
        "})()"
    )
    if intended_err or not intended or intended.get("error"):
        return [f"digit viewport {intended_err or intended}"]
    if intended.get("mode") != "vertex" or intended.get("active") != "viewport" or intended.get("gizmo") is not False:
        return [f"digit viewport intended {intended}"]
    press_plain_4(cdp)
    cdp.drain(0.3)
    restored = _export_state(cdp)
    if (
        restored.get("selectionMode") != "item"
        or int(restored.get("selectionCount") or 0) < 1
        or restored.get("gizmoVisible") is not True
    ):
        return [
            "digit viewport 4 "
            f"{restored.get('selectionMode')!r} {restored.get('selectionCount')!r} gizmo={restored.get('gizmoVisible')!r}"
        ]
    vef_check, vef_err = keyed(
        "(function(){"
        "var aims=window.__cadcamPhoneSelect&&window.__cadcamPhoneSelect.aims?window.__cadcamPhoneSelect.aims():null;"
        "if(!aims) return JSON.stringify({error:'missing aims'});"
        "var canvas=document.getElementById('canvas');"
        "function tap(pt){"
        "  canvas.dispatchEvent(new PointerEvent('pointerdown',{bubbles:true,cancelable:true,pointerId:61,pointerType:'touch',isPrimary:true,button:0,buttons:1,clientX:pt.x,clientY:pt.y}));"
        "  canvas.dispatchEvent(new PointerEvent('pointerup',{bubbles:true,cancelable:true,pointerId:61,pointerType:'touch',isPrimary:true,button:0,buttons:0,clientX:pt.x,clientY:pt.y}));"
        "}"
        "var out={};"
        "var modes=['vertex','edge','face'];"
        "for(var i=0;i<modes.length;i++){"
        "  var m=modes[i];"
        "  var btn=document.querySelector('[data-action=\"select\"][data-mode=\"'+m+'\"]');"
        "  if(!btn) return JSON.stringify({error:'missing '+m});"
        "  btn.click();"
        "  var s0=window.__cadcamExportState||{};"
        "  var aim=aims[m];"
        "  if(!aim||!aim.id) return JSON.stringify({error:'missing aim '+m});"
        "  tap(aim);"
        "  var s1=window.__cadcamExportState||{};"
        "  out[m]={mode0:s0.selectionMode,count0:s0.selectionCount,gizmo0:s0.gizmoVisible,mode1:s1.selectionMode,count1:s1.selectionCount,gizmo1:s1.gizmoVisible};"
        "}"
        "var itemBtn=document.querySelector('[data-action=\"select\"][data-mode=\"item\"]');"
        "if(itemBtn) itemBtn.click();"
        "var sf=window.__cadcamExportState||{};"
        "out.item={mode:sf.selectionMode,count:sf.selectionCount,gizmo:sf.gizmoVisible};"
        "return JSON.stringify(out);"
        "})()"
    )
    if vef_err or not vef_check or vef_check.get("error"):
        return [f"vef gizmo hide {vef_err or vef_check}"]
    for mode_name in ("vertex", "edge", "face"):
        step = vef_check.get(mode_name) if isinstance(vef_check.get(mode_name), dict) else {}
        if (
            step.get("mode0") != mode_name
            or int(step.get("count0") or 0) != 0
            or step.get("gizmo0") is not False
            or step.get("mode1") != mode_name
            or int(step.get("count1") or 0) != 1
            or step.get("gizmo1") is not False
        ):
            return [f"vef gizmo hide {mode_name} {step}"]
    item_step = vef_check.get("item") if isinstance(vef_check.get("item"), dict) else {}
    if (
        item_step.get("mode") != "item"
        or int(item_step.get("count") or 0) != 1
        or item_step.get("gizmo") is not True
    ):
        return [f"vef gizmo restore item {item_step}"]
    print("digit hotkey guard pass", flush=True)
    return []


MEASURE_PROBE_EXPR = (
    "(function(){"
    "var hook=window.__cadcamMeasure;"
    "if(!hook||typeof hook.probe!=='function') return 'missing';"
    "return JSON.stringify(hook.probe());"
    "})()"
)


def _measure_degrees(label: str) -> float | None:
    text = str(label or "").strip()
    if not text.endswith("°") or "mm" in text.lower():
        return None
    try:
        return float(text[:-1])
    except ValueError:
        return None


def measure_tool_problems(cdp: Cdp) -> list[str]:
    """Default 20 mm cube. Measure is read-only: edge polyline, two-point, volume."""
    raw, err = eval_expr(cdp, MEASURE_PROBE_EXPR, timeout=60)
    if err or not isinstance(raw, str) or not raw.startswith("{"):
        return [f"measure probe {raw or err}"]
    try:
        data = json.loads(raw)
    except json.JSONDecodeError:
        return [f"measure probe {raw}"]
    if not isinstance(data, dict):
        return [f"measure probe {raw}"]
    problems: list[str] = []
    button_w = float(data.get("buttonW") or 0)
    button_h = float(data.get("buttonH") or 0)
    if button_w < 44 or button_h < 44:
        problems.append(f"Measure control {button_w:.1f}x{button_h:.1f}")
    if data.get("hiddenOff") is not True or data.get("readoutOff") is not True:
        problems.append(f"measure off hidden {data.get('hiddenOff')!r} readout {data.get('readoutOff')!r}")
    if data.get("hiddenOn") is not True or data.get("readoutOn") is not True:
        problems.append(f"measure on hidden {data.get('hiddenOn')!r} readout {data.get('readoutOn')!r}")
    idle = str(data.get("idleText") or "")
    if idle:
        problems.append(f"idle dimension {idle!r}")
    if data.get("idleSpanHidden") is not True:
        problems.append("idle span still drawn")
    if not _near(data.get("edgeMm"), 20, 0.05):
        problems.append(f"edge length {data.get('edgeMm')!r}")
    if int(data.get("edgePts") or 0) < 3:
        problems.append(f"edge samples {data.get('edgePts')!r}")
    edge_text = str(data.get("edgeText") or "")
    edge_formatted = str(data.get("edgeFormatted") or "")
    if not edge_text or edge_text != edge_formatted:
        problems.append(f"edge text {edge_text!r} formatted {edge_formatted!r}")
    if str(data.get("edgeLabel") or "") != "Length " + edge_text:
        problems.append(f"edge label {data.get('edgeLabel')!r}")
    diagonal = 20 * math.sqrt(3)
    if not _near(data.get("vertexMm"), diagonal, 0.05):
        problems.append(f"vertex distance {data.get('vertexMm')!r}")
    vertex_text = str(data.get("vertexText") or "")
    if not vertex_text or vertex_text != str(data.get("vertexFormatted") or ""):
        problems.append(f"vertex text {vertex_text!r} formatted {data.get('vertexFormatted')!r}")
    if data.get("pickPath") != "tap" or int(data.get("pickCount") or 0) != 2:
        problems.append(f"picks {data.get('pickPath')!r} {data.get('pickCount')!r}")
    if not _near(data.get("pickMm"), diagonal, 0.05):
        problems.append(f"pick distance {data.get('pickMm')!r}")
    if str(data.get("pickText") or "") != vertex_text:
        problems.append(f"pick text {data.get('pickText')!r} vertex {vertex_text!r}")
    if not _near(data.get("volumeMm3"), 8000, 0.01):
        problems.append(f"volume {data.get('volumeMm3')!r}")
    if not _near(data.get("volumeBefore"), data.get("volumeMm3"), 0.01):
        problems.append(f"volume changed {data.get('volumeBefore')!r} -> {data.get('volumeMm3')!r}")
    volume_text = str(data.get("volumeText") or "")
    volume_formatted = str(data.get("volumeFormatted") or "")
    if volume_text != "Volume " + volume_formatted:
        problems.append(f"volume text {volume_text!r} formatted {volume_formatted!r}")
    if "8000" not in volume_formatted:
        problems.append(f"volume format {volume_formatted!r}")
    if data.get("propsHasVolume") is not True:
        problems.append("properties volume missing")
    inch_text = str(data.get("inchText") or "")
    inch_volume = str(data.get("inchVolume") or "")
    if not inch_text.endswith(" in") or "in" not in inch_volume:
        problems.append(f"inch display {inch_text!r} {inch_volume!r}")
    if data.get("angleEdgeError"):
        problems.append(f"angle binding {data.get('angleEdgeError')}")
    else:
        edge_deg = _measure_degrees(str(data.get("angleEdgeLabel") or ""))
        try:
            edge_rad = float(data.get("angleEdgeRad"))
        except (TypeError, ValueError):
            edge_rad = float("nan")
        if edge_deg is None or not _near(edge_deg, math.degrees(edge_rad), 0.05):
            problems.append(
                f"edge angle {data.get('angleEdgeLabel')!r} rad {data.get('angleEdgeRad')!r}"
            )
        elif not _near(edge_deg, 90, 0.5):
            problems.append(f"edge angle not right {edge_deg}")
        if str(data.get("angleVolumeText") or "") != "Volume " + volume_formatted:
            problems.append(f"angle volume {data.get('angleVolumeText')!r}")
    if data.get("angleEdgeFaceError"):
        problems.append(f"edge-face binding {data.get('angleEdgeFaceError')}")
    else:
        face_deg = _measure_degrees(str(data.get("angleEdgeFaceLabel") or ""))
        try:
            face_rad = float(data.get("angleEdgeFaceRad"))
        except (TypeError, ValueError):
            face_rad = float("nan")
        face_label = str(data.get("angleEdgeFaceLabel") or "")
        if (
            face_deg is None
            or face_deg < -0.05
            or face_deg > 180.05
            or not _near(face_deg, math.degrees(face_rad), 0.05)
            or "mm" in face_label.lower()
        ):
            problems.append(
                f"edge-face angle {face_label!r} rad {data.get('angleEdgeFaceRad')!r}"
            )
    if data.get("faceAreaError"):
        problems.append(f"area binding {data.get('faceAreaError')}")
    else:
        if not _near(data.get("faceAreaMm2"), 400, 0.5):
            problems.append(f"face area {data.get('faceAreaMm2')!r}")
        area_label = str(data.get("faceAreaLabel") or "")
        area_formatted = str(data.get("faceAreaFormatted") or "")
        if area_label != area_formatted or "400" not in area_label or "mm²" not in area_label:
            problems.append(f"face area label {area_label!r} formatted {area_formatted!r}")
        if area_label.startswith("Length") or area_label.startswith("Distance"):
            problems.append(f"face area looked like a length {area_label!r}")
        if str(data.get("faceVolumeText") or "") != "Volume " + volume_formatted:
            problems.append(f"area volume {data.get('faceVolumeText')!r}")
        edge_face_label = str(data.get("angleEdgeFaceLabel") or "")
        if edge_face_label and edge_face_label == area_label:
            problems.append(f"edge-face showed area {edge_face_label!r}")
    if int(data.get("shapesAfter") or 0) != 0:
        problems.append(f"shapes left {data.get('shapesAfter')!r}")
    if data.get("hiddenAfter") is not True or data.get("readoutAfter") is not True:
        problems.append(f"measure cleared hidden {data.get('hiddenAfter')!r} readout {data.get('readoutAfter')!r}")
    if int(data.get("picksAfter") or 0) != 0:
        problems.append(f"picks left {data.get('picksAfter')!r}")
    if data.get("exportBefore") is not True or data.get("exportAfter") is not True:
        problems.append(f"export {data.get('exportBefore')!r} -> {data.get('exportAfter')!r}")
    if int(data.get("bodiesBefore") or 0) != 1 or int(data.get("bodiesAfter") or 0) != 1:
        problems.append(f"bodies {data.get('bodiesBefore')!r} -> {data.get('bodiesAfter')!r}")
    if data.get("shelfBefore") != data.get("shelfAfter"):
        problems.append(f"shelf {data.get('shelfBefore')!r} -> {data.get('shelfAfter')!r}")
    return problems


def run(omit: list[str]) -> int:
    browser = find_browser()
    reasons: list[str] = []
    if not browser:
        reasons.append(
            "browser not found (Edge or Chromium). Set CADCAM_BROWSER to the executable."
        )
    reasons.extend(libcascade_gaps())
    if reasons:
        return skip_or_fail(reasons)

    assembler = load_assembler()
    site = WORK / "_site"
    profile = WORK / f"profile-{os.getpid()}"
    WORK.mkdir(parents=True, exist_ok=True)
    copied = assembler.assemble(site, omit)
    print(f"assembled {site}", flush=True)
    for rel in copied:
        print(f"  {rel}", flush=True)

    http_port = free_port()
    origin = f"http://127.0.0.1:{http_port}"

    def handler(*args: Any, **kwargs: Any) -> SiteHandler:
        return SiteHandler(*args, directory=str(site), **kwargs)

    banned = (
        site / "tests" / "fixtures" / "lbracket.json",
        site / "fixtures" / "lbracket.json",
        site / "tests" / "fixtures" / "blink.json",
        site / "fixtures" / "blink.json",
    )
    for banned_path in banned:
        if banned_path.exists():
            print(f"FAIL site contains {banned_path}", flush=True)
            return 1

    server = ThreadingHTTPServer(("127.0.0.1", http_port), handler)
    thread = threading.Thread(target=server.serve_forever, name="deploy-smoke-http", daemon=True)
    thread.start()
    missing = assert_fixture_urls_404(origin)
    if missing:
        print("FAIL deploy_smoke", flush=True)
        for line in missing:
            print(line, flush=True)
        server.shutdown()
        server.server_close()
        thread.join(timeout=5)
        return 1

    cdp_port = free_port()
    if profile.exists():
        shutil.rmtree(profile, ignore_errors=True)
    profile.mkdir(parents=True, exist_ok=True)
    log_path = WORK / "browser.log"
    log_file = log_path.open("w", encoding="utf-8", errors="replace")
    popen_kwargs: dict[str, Any] = {}
    if sys.platform != "win32":
        popen_kwargs["start_new_session"] = True
    proc: subprocess.Popen[Any] | None = None
    cdp: Cdp | None = None
    try:
        proc = subprocess.Popen(
            browser_args(browser, cdp_port, profile),
            stdout=log_file,
            stderr=subprocess.STDOUT,
            **popen_kwargs,
        )
        ws_url = wait_for_page(cdp_port)
        cdp = Cdp(ws_url)
        cdp.call("Page.enable")
        cdp.call("Runtime.enable")
        cdp.call("Network.enable")
        cdp.call("Log.enable")
        cdp.call("Network.setCacheDisabled", {"cacheDisabled": True})
        cdp.call("Network.clearBrowserCache")
        cdp.call("Page.addScriptToEvaluateOnNewDocument", {"source": HOOK})
        print(f"browser {browser}", flush=True)
        print(f"serving {origin} cacheDisabled=true", flush=True)

        failures: list[str] = []
        wrap = run_wrapup(cdp, origin)
        if wrap:
            failures.append("wrapup")
            failures.extend(wrap[:60])
        stamped = False
        for case in CASES:
            if failures:
                break
            url = origin + case["query"]
            print(f"load {case['name']} {url}", flush=True)
            started = time.time()
            state, problems = wait_for_case(cdp, origin, url, PAGE_TIMEOUT_S)
            elapsed = time.time() - started
            if problems:
                failures.append(f"{case['name']} ({elapsed:.1f}s)")
                failures.extend(problems[:40])
                if len(problems) > 40:
                    failures.append(f"... {len(problems) - 40} more")
                break
            assert state is not None
            if case.get("hotkey"):
                press_plain_4(cdp)
                cdp.drain(0.4)
                keyed = eval_state(cdp)
                if keyed and isinstance(keyed.get("state"), dict):
                    state = keyed["state"]
                problems = site_problems(cdp.events, origin, cdp.urls)
                problems.extend(smoke_notes(keyed))
                if state.get("selectionMode") != "item" or int(state.get("selectionCount") or 0) < 1:
                    problems.append(
                        f"hotkey4: expected Item mode and a selected body, "
                        f"got mode {state.get('selectionMode')!r} count {state.get('selectionCount')!r}"
                    )
                if problems:
                    failures.append(f"{case['name']} ({elapsed:.1f}s)")
                    failures.extend(problems[:40])
                    break
            case_problems = check_case(case["name"], state, str(case.get("op") or ""))
            if case["name"] in ("closed_box", "flipped_box") and not case_problems:
                case_problems.extend(rust_gate_probe_problems(cdp, case["name"]))
            shown = json.dumps(state, separators=(",", ":"))
            print(f"{case['name']}={shown}", flush=True)
            print(
                f"{case['name']}: {response_count(cdp.events, origin)} site responses, "
                f"{elapsed:.1f}s, {case['expect']}",
                flush=True,
            )
            if case_problems:
                failures.extend(case_problems)
                failures.append(shown)
                break
            if not stamped:
                stamped = True
                stamp_found = stamp_problems(cdp)
                if stamp_found:
                    failures.append(f"{case['name']} stamp")
                    failures.extend(stamp_found)
                    break
        if not failures:
            failures.extend(overlap_boolean_problems(cdp, origin))
        if not failures:
            failures.extend(disjoint_boolean_problems(cdp, origin))
        if not failures:
            try:
                set_desktop(cdp)
            except (RuntimeError, TimeoutError, OSError) as exc:
                failures.append(f"desktop toolbar metrics {exc}")
            else:
                time.sleep(0.3)
                desktop_bar = toolbar_row_problems(cdp)
                desktop_bar.extend(chrome_row_problems(cdp))
                desktop_bar.extend(create_menu_problems(cdp))
                if desktop_bar:
                    failures.append("desktop toolbar")
                    failures.extend(desktop_bar[:40])
        if not failures:
            home_url = origin + "/?primitive=box"
            print(f"load home {home_url}", flush=True)
            _home_state, home_load = wait_for_case(cdp, origin, home_url, PAGE_TIMEOUT_S)
            if home_load:
                failures.append("home load")
                failures.extend(home_load[:40])
            else:
                try:
                    set_desktop(cdp)
                except (RuntimeError, TimeoutError, OSError) as exc:
                    failures.append(f"home desktop metrics {exc}")
                else:
                    time.sleep(0.3)
                    cover_steps = coverage_problems(cdp, False)
                    if not cover_steps:
                        toggled, toggle_err = eval_expr(cdp, CLICK_DIM_EXPR)
                        if toggle_err or toggled != "clicked":
                            cover_steps = [f"desktop dim toggle {toggled or toggle_err}"]
                    if not cover_steps:
                        cover_steps = coverage_problems(cdp, True)
                    if not cover_steps:
                        toggled, toggle_err = eval_expr(cdp, CLICK_DIM_EXPR)
                        if toggle_err or toggled != "clicked":
                            cover_steps = [f"desktop dim close {toggled or toggle_err}"]
                    if not cover_steps:
                        cover_steps = coverage_problems(cdp, False)
                    if cover_steps:
                        failures.append("desktop coverage")
                        failures.extend(cover_steps[:40])
                    else:
                        home_found = home_aim_round(cdp, "desktop")
                        if home_found:
                            failures.append("desktop home")
                            failures.extend(home_found[:40])
        if not failures:
            try:
                set_portrait(cdp)
            except (RuntimeError, TimeoutError, OSError) as exc:
                failures.append(f"measure portrait {exc}")
            else:
                time.sleep(0.3)
                measure_found = measure_tool_problems(cdp)
                if measure_found:
                    failures.append("measure")
                    failures.extend(measure_found[:40])
                else:
                    print("MEASURE_DONE", flush=True)
        if not failures:
            portrait_problems = run_portrait(cdp, origin)
            if portrait_problems:
                failures.append("portrait")
                failures.extend(portrait_problems[:40])
        if not failures:
            nav_problems = nav_cube_problems(cdp)
            if nav_problems:
                failures.append("nav cube")
                failures.extend(nav_problems[:40])
            else:
                print("NAVCUBE_DONE", flush=True)
        if not failures:
            hole_problems = run_portrait_holes(cdp, origin)
            if hole_problems:
                failures.append("portrait_holes")
                failures.extend(hole_problems[:40])
        if not failures:
            q5_problems = run_portrait_q5_lbracket(cdp, origin)
            if q5_problems:
                failures.append("portrait_q5_lbracket")
                failures.extend(q5_problems[:40])
        if not failures:
            truck_problems = run_portrait_q5_truck(cdp, origin)
            if truck_problems:
                failures.append("portrait_q5_truck")
                failures.extend(truck_problems[:40])
        if not failures:
            delete_found = delete_problems(cdp, origin, desktop=True)
            if delete_found:
                failures.append("delete")
                failures.extend(delete_found[:40])
        if not failures:
            resize_problems = run_type_in_resize(cdp, origin)
            if resize_problems:
                failures.append("type_in_resize")
                failures.extend(resize_problems[:40])
        if not failures:
            saveload_problems = run_saveload(cdp, origin)
            if saveload_problems:
                failures.append("saveload")
                failures.extend(saveload_problems[:40])
        if not failures:
            assembly_found = assembly_problems(cdp, origin)
            if assembly_found:
                failures.append("assembly")
                failures.extend(assembly_found[:40])
        if not failures:
            size_found = multi_body_size_problems(cdp, origin)
            if size_found:
                failures.append("multi_body_size")
                failures.extend(size_found[:40])
        if not failures:
            move_found = multi_body_move_problems(cdp, origin)
            if move_found:
                failures.append("multi_body_move")
                failures.extend(move_found[:40])
        if not failures:
            color_found = multi_body_color_problems(cdp, origin)
            if color_found:
                failures.append("multi_body_color")
                failures.extend(color_found[:40])
        if not failures:
            vol_found = cylinder_live_volume_problems(cdp, origin)
            if vol_found:
                failures.append("cyl_volume")
                failures.extend(vol_found[:40])
        if not failures:
            centre_found = unlocked_centre_resize_problems(cdp, origin)
            if centre_found:
                failures.append("centre_resize")
                failures.extend(centre_found[:40])
        if not failures:
            gizmo_found = combine_gizmo_x_problems(cdp, origin)
            if gizmo_found:
                failures.append("combine_gizmo_x")
                failures.extend(gizmo_found[:40])
        if not failures:
            names_found = boolean_unique_names_problems(cdp, origin)
            if names_found:
                failures.append("boolean_names")
                failures.extend(names_found[:40])
        if not failures:
            create_undo_found = create_undo_problems(cdp, origin)
            if create_undo_found:
                failures.append("create_undo")
                failures.extend(create_undo_found[:40])
        if not failures:
            hotkey_found = digit_hotkey_guard_problems(cdp, origin)
            if hotkey_found:
                failures.append("digit_hotkeys")
                failures.extend(hotkey_found[:40])
        if failures:
            print("FAIL deploy_smoke", flush=True)
            for line in failures:
                print(line, flush=True)
            return 1
        print("PASS deploy_smoke", flush=True)
        return 0
    finally:
        if cdp is not None:
            cdp.close()
        stop_browser(proc, profile)
        log_file.close()
        server.shutdown()
        server.server_close()
        thread.join(timeout=5)
        shutil.rmtree(profile, ignore_errors=True)


DELETE_KEY_EXPR = r"""
(function(){
  var el=document.activeElement;
  if(el&&el.blur) el.blur();
  document.dispatchEvent(new KeyboardEvent('keydown',{key:'Delete',bubbles:true,cancelable:true}));
  var s=window.__cadcamExportState||{};
  return JSON.stringify({body:s.bodyCount,undo:s.undoDepth,cleared:!!s.sceneCleared,w:window.innerWidth});
})()
"""

UNDO_KEY_EXPR = r"""
(function(){
  var el=document.activeElement;
  if(el&&el.blur) el.blur();
  document.dispatchEvent(new KeyboardEvent('keydown',{key:'z',ctrlKey:true,bubbles:true,cancelable:true}));
  var s=window.__cadcamExportState||{};
  return JSON.stringify({body:s.bodyCount,undo:s.undoDepth,cleared:!!s.sceneCleared});
})()
"""

FOCUSED_DELETE_EXPR = r"""
(function(){
  var el=document.getElementById('docName');
  if(!el) return 'missing';
  el.focus();
  document.dispatchEvent(new KeyboardEvent('keydown',{key:'Delete',bubbles:true,cancelable:true}));
  var s=window.__cadcamExportState||{};
  return JSON.stringify({body:s.bodyCount,undo:s.undoDepth,active:document.activeElement?document.activeElement.id:''});
})()
"""

EDGE_ALONE = "Can't delete this edge on its own."
FACE_KEPT = "Can't remove this face. The model was not changed."


def _export_state(cdp: Cdp) -> dict[str, Any]:
    payload = eval_state(cdp)
    state = (payload or {}).get("state") if isinstance(payload, dict) else None
    return state if isinstance(state, dict) else {}


def _key_state(raw: Any, err: str) -> tuple[dict[str, Any] | None, str]:
    if err or not isinstance(raw, str) or not raw.startswith("{"):
        return None, err or str(raw)
    try:
        parsed = json.loads(raw)
    except json.JSONDecodeError:
        return None, raw
    return parsed if isinstance(parsed, dict) else None, ""


def _trash_problems(state: dict[str, Any], want_hidden: bool) -> list[str]:
    btn = state.get("deleteButton") if isinstance(state.get("deleteButton"), dict) else {}
    hidden = btn.get("hidden") is True
    if want_hidden:
        return [] if hidden else ["trash visible with nothing selected"]
    problems: list[str] = []
    if hidden:
        problems.append("trash hidden while something is selected")
    width = float(btn.get("w") or 0)
    height = float(btn.get("h") or 0)
    if width < 44 or height < 44:
        problems.append(f"trash {width:.1f}x{height:.1f}")
    return problems


def delete_problems(cdp: Cdp, origin: str, *, desktop: bool, probe: bool = True) -> list[str]:
    """Trash deletes a selected box. Desktop Del does too, unless an input is focused."""
    problems: list[str] = []
    if desktop:
        try:
            set_desktop(cdp)
        except (RuntimeError, TimeoutError, OSError) as exc:
            return [f"delete desktop metrics {exc}"]
        time.sleep(0.2)
    state, load_problems = wait_for_case(cdp, origin, origin + "/?primitive=box", PAGE_TIMEOUT_S)
    if load_problems:
        return ["delete load", *load_problems[:12]]
    if not isinstance(state, dict):
        return ["delete load returned no state"]
    if int(state.get("bodyCount") or 0) != 1 or int(state.get("undoDepth") or 0) != 0:
        problems.append(f"delete start body {state.get('bodyCount')!r} undo {state.get('undoDepth')!r}")
    problems.extend(_trash_problems(state, False))
    cleared, clear_err = eval_expr(cdp, "window.__cadcamClearSelection()")
    if clear_err or cleared is not True:
        problems.append(f"clear selection {cleared or clear_err}")
    else:
        time.sleep(0.1)
        problems.extend(_trash_problems(_export_state(cdp), True))
    selected, select_err = eval_expr(cdp, "window.__cadcamSelectItem()")
    if select_err or selected is not True:
        problems.append(f"select item {selected or select_err}")
    else:
        time.sleep(0.1)
        problems.extend(_trash_problems(_export_state(cdp), False))
    if not desktop:
        raw, err = eval_expr(cdp, DELETE_KEY_EXPR)
        parsed, perr = _key_state(raw, err)
        if perr or not parsed or int(parsed.get("body") or 0) != 1 or int(parsed.get("undo") or 0) != 0:
            problems.append(f"phone Del deleted the body {perr or parsed}")
    if problems:
        return problems
    problems.extend(tap_selector(cdp, "#deleteBtn", "delete trash"))
    if problems:
        return problems
    time.sleep(0.3)
    state = _export_state(cdp)
    if int(state.get("bodyCount") or 0) != 0 or int(state.get("undoDepth") or 0) != 1 or state.get("sceneCleared") is not True:
        return [
            "trash delete "
            + json.dumps(
                {
                    "body": state.get("bodyCount"),
                    "undo": state.get("undoDepth"),
                    "cleared": state.get("sceneCleared"),
                    "error": state.get("lastError"),
                }
            )
        ]
    raw, err = eval_expr(cdp, UNDO_KEY_EXPR)
    parsed, perr = _key_state(raw, err)
    if perr or not parsed or int(parsed.get("body") or 0) != 1 or int(parsed.get("undo") or 0) != 0 or parsed.get("cleared") is True:
        return [f"undo trash {perr or parsed}"]
    if desktop:
        raw, err = eval_expr(cdp, DELETE_KEY_EXPR)
        parsed, perr = _key_state(raw, err)
        if perr or not parsed or int(parsed.get("body") or 0) != 0 or int(parsed.get("undo") or 0) != 1:
            return [f"desktop Del {perr or parsed}"]
        raw, err = eval_expr(cdp, UNDO_KEY_EXPR)
        parsed, perr = _key_state(raw, err)
        if perr or not parsed or int(parsed.get("body") or 0) != 1 or int(parsed.get("undo") or 0) != 0:
            return [f"undo Del {perr or parsed}"]
        raw, err = eval_expr(cdp, FOCUSED_DELETE_EXPR)
        parsed, perr = _key_state(raw, err)
        if perr or not parsed or int(parsed.get("body") or 0) != 1 or int(parsed.get("undo") or 0) != 0 or parsed.get("active") != "docName":
            return [f"focused Del changed the model {perr or parsed}"]
    if not probe:
        return []
    try:
        result = cdp.call(
            "Runtime.evaluate",
            {
                "expression": "window.__cadcamDeleteProbe()",
                "returnByValue": True,
                "timeout": 120000,
            },
            timeout=130,
        )
    except (RuntimeError, TimeoutError, OSError) as exc:
        return [f"delete probe {exc}"]
    if result.get("exceptionDetails"):
        detail = result.get("exceptionDetails") or {}
        return [f"delete probe {detail.get('text') or detail}"]
    value = (result.get("result") or {}).get("value")
    if not isinstance(value, dict):
        return [f"delete probe returned {value!r}"]
    if value.get("error"):
        problems.append(f"delete probe threw {value.get('error')}")
    hole = value.get("hole") if isinstance(value.get("hole"), dict) else {}
    try:
        delta = abs(float(hole.get("delta")))
    except (TypeError, ValueError):
        delta = 999.0
    if (
        hole.get("ok") is not True
        or delta > 0.01
        or hole.get("valid") is not True
        or hole.get("undoRestored") is not True
        or hole.get("facesDropped") is not True
        or hole.get("undoStep") is not True
    ):
        problems.append("hole face delete " + json.dumps(hole))
    box = value.get("boxFace") if isinstance(value.get("boxFace"), dict) else {}
    if (
        box.get("unchanged") is not True
        or box.get("undoSame") is not True
        or box.get("error") != FACE_KEPT
    ):
        problems.append("box face delete " + json.dumps(box))
    edge = value.get("edge") if isinstance(value.get("edge"), dict) else {}
    if edge.get("error") != EDGE_ALONE or edge.get("unchanged") is not True:
        problems.append("edge delete " + json.dumps(edge))
    fillet = value.get("fillet") if isinstance(value.get("fillet"), dict) else {}
    if (
        fillet.get("ok") is not True
        or fillet.get("valid") is not True
        or fillet.get("cylinderFaces") != 0
        or fillet.get("undoStep") is not True
        or int(fillet.get("featureFaces") or 0) < 1
    ):
        problems.append("fillet delete " + json.dumps(fillet))
    return problems


def main(argv: list[str]) -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    parser = argparse.ArgumentParser(description="Smoke-test the GitHub Pages file set.")
    parser.add_argument(
        "--omit",
        action="append",
        default=[],
        help="Site-relative file to leave out of the temp _site (negative check).",
    )
    args = parser.parse_args(argv)
    try:
        return run(args.omit)
    except SystemExit as exc:
        if isinstance(exc.code, int):
            if exc.code == 0:
                return 0
            print(f"FAIL deploy_smoke: {exc.code}", flush=True)
            return exc.code if exc.code != SKIP else 1
        print(f"FAIL deploy_smoke: {exc}", flush=True)
        return 1


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
