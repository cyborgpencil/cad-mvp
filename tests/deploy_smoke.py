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
  ?fixture=open_box     OCCT gate FAIL, Export locked
  ?primitive=box&select=face   OCCT ready, one face selected
  ?demo=lbracket        final L-bracket OCCT gate PASS (app defaults)
  ?demo=booleans        box minus cylinder, OCCT gate PASS
  ?demo=booleans&op=    union, cut, and intersect each PASS
  ?pair=overlap         select two bodies with the 4 key, then Union, Cut, Intersect
  /?fixture=closed_box  plain 4 key selects the whole body
  portrait 390x844      touch-create box, cylinder, and disc, then edit one dimension
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
        "expect": "occtReady and gate FAIL, Export locked",
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
        if state.get("exportAllowed") is not False or state.get("exportDisabled") is not True:
            problems.append(f"{name}: Export is not locked")
    elif name == "box_face":
        if state.get("occtReady") is not True:
            problems.append(f"{name}: occtReady is not true")
        if state.get("selectionMode") != "face" or int(state.get("selectionCount") or 0) < 1:
            problems.append(
                f"{name}: expected one selected face, got mode {state.get('selectionMode')!r} "
                f"count {state.get('selectionCount')!r}"
            )
        if state.get("occtGate") is not True or state.get("gateOcct") != "PASS":
            problems.append(f"{name}: gate is not PASS ({state.get('gateOcct')!r})")
    elif name == "lbracket":
        if state.get("demo") != "lbracket":
            problems.append(f"{name}: demo {state.get('demo')!r}")
        if state.get("occtGate") is not True or state.get("gateOcct") != "PASS":
            problems.append(f"{name}: gate is not PASS ({state.get('gateOcct')!r})")
        if state.get("watertight") is not True:
            problems.append(f"{name}: watertight is not true")
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
        if state.get("watertight") is not True:
            problems.append(f"{name}: watertight is not true")
        if state.get("unitsPass") is not True:
            problems.append(f"{name}: units are not locked")
        if state.get("exportAllowed") is not True:
            problems.append(f"{name}: Export is not enabled")
        if state.get("lastError"):
            problems.append(f"{name}: lastError {state.get('lastError')!r}")
        if state.get("booleanOp") != expected_op:
            problems.append(f"{name}: booleanOp {state.get('booleanOp')!r}, want {expected_op!r}")
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


def eval_expr(cdp: Cdp, expression: str) -> tuple[Any, str]:
    result = cdp.call(
        "Runtime.evaluate",
        {"expression": expression, "returnByValue": True},
        timeout=30,
    )
    if result.get("exceptionDetails"):
        detail = result.get("exceptionDetails") or {}
        return None, str(detail.get("text") or detail.get("exception") or "evaluate failed")
    remote = result.get("result") or {}
    return remote.get("value"), ""


def set_portrait(cdp: Cdp) -> None:
    cdp.call(
        "Emulation.setDeviceMetricsOverride",
        {"width": 390, "height": 844, "deviceScaleFactor": 1, "mobile": True},
    )
    cdp.call("Emulation.setTouchEmulationEnabled", {"enabled": True, "maxTouchPoints": 1})


def touch_tap(cdp: Cdp, x: float, y: float) -> None:
    point = {"x": float(x), "y": float(y), "radiusX": 1.0, "radiusY": 1.0, "force": 1.0, "id": 0}
    cdp.call("Input.dispatchTouchEvent", {"type": "touchStart", "touchPoints": [point]})
    time.sleep(0.05)
    cdp.call("Input.dispatchTouchEvent", {"type": "touchEnd", "touchPoints": []})


def toolbar_point_expr(kind: str) -> str:
    return (
        "(function(){"
        f"var b=document.querySelector('#touchToolbar [data-kind=\"{kind}\"]');"
        "if(!b) return 'missing';"
        "var st=getComputedStyle(b);"
        "if(st.display==='none'||st.visibility==='hidden') return 'hidden';"
        "var r=b.getBoundingClientRect();"
        "if(r.width<1||r.height<1) return 'empty';"
        "return JSON.stringify({x:r.left+r.width/2,y:r.top+r.height/2,w:r.width,h:r.height});"
        "})()"
    )


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
    "var nodes=document.querySelectorAll('#touchToolbar button, #dimPanel button, #dimPanel input');"
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
    key: str,
    want: float,
    timeout: float,
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
            ready = (
                state.get("primitiveKind") == kind
                and state.get("occtGate") is True
                and state.get("gateOcct") == "PASS"
                and state.get("dimPanelOpen") is True
                and state.get("watertight") is True
                and state.get("unitsPass") is True
                and not state.get("lastError")
                and int(state.get("bodyCount") or 0) == 1
                and param_is(state, key, want)
            )
            if ready:
                return state, []
        time.sleep(0.15)
    return last, [f"portrait {kind} timed out waiting for {key}={want}", json.dumps(last)]


def run_portrait(cdp: Cdp, origin: str) -> list[str]:
    """390x844 touch emulation. Tap each primitive, edit one dimension, gate PASS."""
    try:
        set_portrait(cdp)
    except (RuntimeError, TimeoutError, OSError) as exc:
        return [f"portrait emulation failed: {exc}"]
    problems: list[str] = []
    for spec in PORTRAIT:
        kind = str(spec["kind"])
        url = origin + "/"
        print(f"load portrait_{kind} {url}", flush=True)
        _state, load_problems = wait_for_case(cdp, origin, url, PAGE_TIMEOUT_S)
        if load_problems:
            problems.append(f"portrait {kind} load")
            problems.extend(load_problems[:20])
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
            cdp, origin, kind, str(spec["key"]), float(spec["fresh"]), PAGE_TIMEOUT_S
        )
        if wait_problems or not isinstance(created, dict):
            problems.append(f"portrait {kind} create")
            problems.extend(wait_problems[:20])
            return problems
        measured, measure_err = eval_expr(cdp, TARGET_EXPR)
        if measure_err or not isinstance(measured, str):
            problems.append(f"portrait {kind} targets {measured or measure_err}")
            return problems
        sizes = json.loads(measured)
        if int(sizes.get("n") or 0) < 12 or sizes.get("bad"):
            problems.append(f"portrait {kind} targets {measured}")
            return problems
        edited, edit_err = eval_expr(cdp, edit_expr(str(spec["field"]), str(spec["value"])))
        if edit_err or edited != "edited":
            problems.append(f"portrait {kind} edit {edited or edit_err}")
            return problems
        done, edit_problems = wait_portrait(
            cdp, origin, kind, str(spec["key"]), float(spec["want"]), PAGE_TIMEOUT_S
        )
        if edit_problems or not isinstance(done, dict):
            problems.append(f"portrait {kind} edited")
            problems.extend(edit_problems[:20])
            return problems
        print(
            f"portrait_{kind}: gate PASS, {spec['field']} {spec['fresh']} -> {spec['want']}, "
            f"targets {sizes.get('n')}",
            flush=True,
        )
    return problems



def click_boolean(cdp: Cdp, op: str) -> str:
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
        timeout=30,
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
        for case in CASES:
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
        if not failures:
            for op in ("union", "cut", "intersect"):
                url = origin + "/?pair=overlap"
                print(f"load boolean_{op} {url}", flush=True)
                started = time.time()
                state, problems = wait_for_case(cdp, origin, url, PAGE_TIMEOUT_S)
                if problems or not isinstance(state, dict):
                    failures.append(f"boolean_{op} load")
                    failures.extend(problems[:40])
                    break
                press_plain_4(cdp)
                cdp.drain(0.4)
                keyed = eval_state(cdp)
                problems = site_problems(cdp.events, origin, cdp.urls)
                problems.extend(smoke_notes(keyed))
                keyed_state = (keyed or {}).get("state") if keyed else None
                if not isinstance(keyed_state, dict):
                    problems.append(f"boolean_{op}: no state after the 4 key")
                else:
                    state = keyed_state
                    if state.get("selectionMode") != "item" or int(state.get("selectionCount") or 0) < 2:
                        problems.append(
                            f"boolean_{op}: expected two selected bodies after 4, "
                            f"mode {state.get('selectionMode')!r} count {state.get('selectionCount')!r}"
                        )
                    order = state.get("selectionOrder") or []
                    if len(order) < 2:
                        problems.append(f"boolean_{op}: selection order {order!r}")
                if problems:
                    failures.append(f"boolean_{op} select")
                    failures.extend(problems[:40])
                    break
                clicked = click_boolean(cdp, op)
                if clicked != "clicked":
                    failures.append(f"boolean_{op}: button {clicked}")
                    break
                done, problems = wait_boolean(cdp, origin, op, PAGE_TIMEOUT_S)
                elapsed = time.time() - started
                if not isinstance(done, dict):
                    problems.append(f"boolean_{op}: no result state")
                else:
                    print(f"boolean_{op}={json.dumps(done, separators=(',', ':'))}", flush=True)
                    if done.get("occtGate") is not True or done.get("gateOcct") != "PASS":
                        problems.append(f"boolean_{op}: gate {done.get('gateOcct')!r}")
                    if done.get("watertight") is not True or done.get("unitsPass") is not True:
                        problems.append(f"boolean_{op}: watertight or units failed")
                    if done.get("exportAllowed") is not True:
                        problems.append(f"boolean_{op}: Export is not enabled")
                    if int(done.get("bodyCount") or 0) != 1:
                        problems.append(f"boolean_{op}: bodyCount {done.get('bodyCount')!r}")
                    if done.get("booleanOp") != op:
                        problems.append(f"boolean_{op}: op {done.get('booleanOp')!r}")
                if problems:
                    failures.append(f"boolean_{op} ({elapsed:.1f}s)")
                    failures.extend(problems[:40])
                    break
                print(f"boolean_{op}: gate PASS, {elapsed:.1f}s", flush=True)
        if not failures:
            portrait_problems = run_portrait(cdp, origin)
            if portrait_problems:
                failures.append("portrait")
                failures.extend(portrait_problems[:40])
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
