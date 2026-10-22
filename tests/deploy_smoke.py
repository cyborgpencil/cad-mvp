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
  portrait 390x844      touch-create box, cylinder, and disc; bottom sheet does not cover Home;
                        move, rotate, and resize a box with taps and typed values;
                        no page-level horizontal scroll; visible buttons and the status
                        line stay inside the width; the sheet and toolbar do not scroll
                        sideways unless marked data-hscroll
  portrait holes        three countersunk holes on a plate; volumes logged; same overflow checks
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
                and state.get("watertight") is True
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
  if (Math.abs(tr.top - ir.top) > 0.5) problems.push('Info top ' + ir.top.toFixed(1) + ' Tree top ' + tr.top.toFixed(1));
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
  if (!(nameMin >= 64) || !(nameMin <= 96)) problems.push('part name min-width ' + ns.minWidth);
  if (ns.overflowX !== 'hidden' && ns.overflowX !== 'clip' && ns.overflow !== 'hidden' && ns.overflow !== 'clip') {
    problems.push('part name overflow ' + ns.overflowX);
  }
  if (ns.textOverflow !== 'ellipsis') problems.push('part name text-overflow ' + ns.textOverflow);
  var savedName = name.value;
  name.value = 'MMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMM';
  if (name.scrollWidth <= name.clientWidth + 1) problems.push('part name did not truncate');
  name.value = savedName;
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


SEARCH_DISCLOSURE_EXPR = r"""
(function(){
  var problems = [];
  function box(el) { return el.getBoundingClientRect(); }
  var btn = document.getElementById('searchBtn');
  var dlg = document.getElementById('searchDlg');
  var input = document.getElementById('searchInput');
  var bar = document.querySelector('.vp-bar');
  if (!btn || !dlg || !input || !bar) return JSON.stringify(['missing search chrome']);
  var searchButtons = [];
  var allBtns = document.querySelectorAll('button');
  for (var s = 0; s < allBtns.length; s++) {
    var candidate = allBtns[s];
    var label = ((candidate.getAttribute('aria-label') || '') + ' ' + (candidate.getAttribute('title') || '') + ' ' + (candidate.getAttribute('data-tool') || '')).toLowerCase();
    var icon = candidate.querySelector('use');
    var href = icon ? (icon.getAttribute('href') || '') : '';
    if (label.indexOf('search') !== -1 || href === '#i-search') searchButtons.push(candidate);
  }
  if (searchButtons.length !== 1) problems.push('search buttons ' + searchButtons.length);
  else if (searchButtons[0] !== btn) problems.push('search button is not the disclosure');
  var searchBox = box(btn);
  var searchStyle = getComputedStyle(btn);
  if (searchStyle.display === 'none' || searchStyle.visibility === 'hidden' || !(searchBox.width > 0) || !(searchBox.height > 0)) {
    problems.push('search button hidden');
  }
  if (searchBox.right <= 0 || searchBox.left >= window.innerWidth || searchBox.bottom <= 0 || searchBox.top >= window.innerHeight) {
    problems.push('search button offscreen');
  }
  var meta = document.querySelector('meta[name="viewport"]');
  if (!meta || String(meta.content).indexOf('interactive-widget=resizes-content') < 0) {
    problems.push('missing interactive-widget');
  }
  if (btn.getAttribute('aria-controls') !== 'searchDlg') problems.push('aria-controls');
  if (btn.getAttribute('aria-expanded') !== 'false') problems.push('aria-expanded start ' + btn.getAttribute('aria-expanded'));
  var br = box(btn);
  if (br.width + 0.5 < 44 || br.height + 0.5 < 44) {
    problems.push('search button ' + br.width.toFixed(1) + 'x' + br.height.toFixed(1));
  }
  if (!dlg.hidden) problems.push('dialog not hidden');
  var dr = box(dlg);
  if (dr.width > 0.5 || dr.height > 0.5) problems.push('collapsed size ' + dr.width.toFixed(1) + 'x' + dr.height.toFixed(1));
  try { input.focus(); } catch (err) {}
  if (document.activeElement === input) problems.push('collapsed input took focus');
  var barTop = box(bar).top;
  btn.click();
  if (dlg.hidden) problems.push('dialog stayed hidden');
  if (btn.getAttribute('aria-expanded') !== 'true') problems.push('aria-expanded open ' + btn.getAttribute('aria-expanded'));
  if (document.activeElement !== input) problems.push('open focus ' + (document.activeElement && (document.activeElement.id || document.activeElement.tagName)));
  var list = document.getElementById('searchList');
  var results = list ? list.querySelectorAll('button') : [];
  if (!results.length) problems.push('no search results');
  var st = getComputedStyle(dlg);
  if (st.position !== 'fixed' && st.position !== 'absolute') problems.push('dialog position ' + st.position);
  var vv = window.visualViewport;
  var viewTop = vv ? vv.offsetTop : 0;
  var viewBottom = vv ? (vv.offsetTop + vv.height) : window.innerHeight;
  var openBox = box(dlg);
  if (openBox.bottom > viewBottom + 1 || openBox.top < viewTop - 1) problems.push('dialog outside visual viewport');
  var visible = 0;
  for (var i = 0; i < results.length; i++) {
    var rr = box(results[i]);
    if (rr.height > 1 && rr.top >= viewTop - 1 && rr.bottom <= viewBottom + 1) visible++;
  }
  if (!visible) problems.push('no result inside visual viewport');
  if (Math.abs(box(bar).top - barTop) > 0.5) problems.push('tool row moved ' + box(bar).top.toFixed(1) + ' vs ' + barTop.toFixed(1));
  document.dispatchEvent(new KeyboardEvent('keydown', {key:'Escape', bubbles:true, cancelable:true}));
  if (!dlg.hidden || btn.getAttribute('aria-expanded') !== 'false') problems.push('esc did not collapse');
  if (document.activeElement !== btn) problems.push('esc focus ' + (document.activeElement && (document.activeElement.id || document.activeElement.tagName)));
  btn.click();
  var canvas = document.getElementById('canvas');
  if (canvas) canvas.click();
  if (!dlg.hidden || btn.getAttribute('aria-expanded') !== 'false') problems.push('outside did not collapse');
  if (document.activeElement !== btn) problems.push('outside focus ' + (document.activeElement && (document.activeElement.id || document.activeElement.tagName)));
  btn.click();
  btn.click();
  if (!dlg.hidden || btn.getAttribute('aria-expanded') !== 'false') problems.push('icon did not collapse');
  if (document.activeElement !== btn) problems.push('icon focus ' + (document.activeElement && (document.activeElement.id || document.activeElement.tagName)));
  var end = box(dlg);
  if (end.width > 0.5 || end.height > 0.5) problems.push('recollapsed size ' + end.width.toFixed(1) + 'x' + end.height.toFixed(1));
  try { input.focus(); } catch (err2) {}
  if (document.activeElement === input) problems.push('recollapsed input took focus');
  if (document.activeElement && document.activeElement.blur) document.activeElement.blur();
  return JSON.stringify(problems);
})()
"""


def search_disclosure_problems(cdp: Cdp) -> list[str]:
    raw, err = eval_expr(cdp, SEARCH_DISCLOSURE_EXPR)
    if err or not isinstance(raw, str):
        return [f"search {raw or err}"]
    try:
        found = json.loads(raw)
    except json.JSONDecodeError:
        return [f"search {raw}"]
    if not isinstance(found, list):
        return [f"search {raw}"]
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
    if any(abs(float(v)) > 1e-6 for v in target):
        return False
    count = int(aim.get("selectionCount") or 0)
    sel_ok = count > 0 if selected else count == 0
    return aim.get("allInside") is True and int(aim.get("corners") or 0) == 8 and sel_ok


def wait_home_aim(cdp: Cdp, label: str, selected: bool) -> list[str]:
    clicked, err = eval_expr(
        cdp,
        "(function(){var b=document.getElementById('vcHome');if(!b)return 'missing';b.click();return 'ok';})()",
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
    return problems


def run_portrait(cdp: Cdp, origin: str) -> list[str]:
    """390x844 touch emulation. Tap primitives, bottom sheet, move/rotate/resize a box."""
    try:
        set_portrait(cdp)
    except (RuntimeError, TimeoutError, OSError) as exc:
        return [f"portrait emulation failed: {exc}"]
    problems: list[str] = []
    inspector_checked = False
    search_checked = False
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
        if not search_checked:
            search_checked = True
            search_found = search_disclosure_problems(cdp)
            if search_found:
                problems.append(f"portrait {kind} search")
                problems.extend(search_found)
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
        fit_problems = portrait_fit_problems(cdp)
        if fit_problems:
            problems.append(f"portrait {kind} overflow")
            problems.extend(fit_problems)
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
        print(
            "portrait_box transforms: move cx 5 stepper 6, rotate z 15, resize sy 22, snap on, gate PASS",
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
    hole_button = tap_selector(cdp, '#touchToolbar [data-action="holeTool"]', "portrait holes tool")
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
                and state.get("watertight") is True
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
    closed = closed_inspector_problems(cdp)
    if closed:
        return ["portrait holes closed inspector", *closed]
    return []


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
            try:
                set_desktop(cdp)
            except (RuntimeError, TimeoutError, OSError) as exc:
                failures.append(f"desktop toolbar metrics {exc}")
            else:
                time.sleep(0.3)
                desktop_bar = toolbar_row_problems(cdp)
                desktop_bar.extend(chrome_row_problems(cdp))
                desktop_bar.extend(search_disclosure_problems(cdp))
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
                    home_found = home_aim_round(cdp, "desktop")
                    if home_found:
                        failures.append("desktop home")
                        failures.extend(home_found[:40])
        if not failures:
            portrait_problems = run_portrait(cdp, origin)
            if portrait_problems:
                failures.append("portrait")
                failures.extend(portrait_problems[:40])
        if not failures:
            hole_problems = run_portrait_holes(cdp, origin)
            if hole_problems:
                failures.append("portrait_holes")
                failures.extend(hole_problems[:40])
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
