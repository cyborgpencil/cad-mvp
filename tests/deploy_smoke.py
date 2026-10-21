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
)


def check_case(name: str, state: dict[str, Any]) -> list[str]:
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


def response_count(events: list[dict[str, Any]], origin: str) -> int:
    count = 0
    for event in events:
        if event.get("method") != "Network.responseReceived":
            continue
        response = (event.get("params") or {}).get("response") or {}
        if str(response.get("url") or "").startswith(origin):
            count += 1
    return count


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

    server = ThreadingHTTPServer(("127.0.0.1", http_port), handler)
    thread = threading.Thread(target=server.serve_forever, name="deploy-smoke-http", daemon=True)
    thread.start()

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
            case_problems = check_case(case["name"], state)
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
