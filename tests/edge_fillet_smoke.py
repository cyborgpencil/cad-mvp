#!/usr/bin/env python3
"""Phone fillet and chamfer on a plain L, 390x844, Chromium and WebKit.

Real touch taps. The part is fused in the page (?part=l), not the Blink
fixture and not ?demo=lbracket. Screenshots use CADMVP_SHOTS_DIR when set,
otherwise the Pictures folder under the home directory, and the file name
starts with fillet-. Exit 77 when Playwright or libcascade is missing.
"""
from __future__ import annotations

import os
import sys
import threading
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
WORK = ROOT / "builds" / "edge-fillet-smoke"
SKIP = 77
CROSS = "pick edges on one body"
SMALLER = "Try a smaller size."


def shots_dir() -> Path:
    raw = os.environ.get("CADMVP_SHOTS_DIR", "").strip()
    if raw:
        return Path(raw)
    return Path.home() / "Pictures" / "cadmvp-shots"


def in_ci() -> bool:
    return os.environ.get("CI", "").strip().lower() not in {"", "0", "false", "no"}


def skip_missing_playwright() -> int:
    if in_ci():
        print(
            "FAIL edge_fillet_smoke: playwright is not importable; "
            "CI must not skip this test.",
            flush=True,
        )
        return 1
    print(
        "SKIP edge_fillet_smoke: playwright is not importable. "
        "Use builds/pwvenv/Scripts/python.exe.",
        flush=True,
    )
    return SKIP


try:
    from playwright.sync_api import sync_playwright
except ImportError:
    raise SystemExit(skip_missing_playwright())

import deploy_smoke


POINTER = """(spec) => {
  const el = document.getElementById('canvas');
  function fire(type, x, y) {
    const ending = type === 'pointerup' || type === 'pointercancel';
    el.dispatchEvent(new PointerEvent(type, {
      bubbles: true,
      cancelable: true,
      pointerId: spec.pointerId || 61,
      pointerType: 'touch',
      isPrimary: true,
      button: 0,
      buttons: ending ? 0 : 1,
      clientX: x,
      clientY: y
    }));
  }
  fire('pointerdown', Number(spec.x), Number(spec.y));
  fire('pointerup', Number(spec.x), Number(spec.y));
  return window.__cadcamExportState || {};
}"""


def read_state(page: Any) -> dict[str, Any]:
    state = page.evaluate("() => window.__cadcamExportState || null")
    return state if isinstance(state, dict) else {}


def aims(page: Any) -> dict[str, Any]:
    found = page.evaluate("() => window.__cadcamPhoneSelect ? window.__cadcamPhoneSelect.aims() : null")
    return found if isinstance(found, dict) else {}


def shot(page: Any, kind: str, name: str) -> None:
    folder = shots_dir()
    folder.mkdir(parents=True, exist_ok=True)
    page.screenshot(path=str(folder / f"fillet-{kind}-{name}.png"))


def pointer(page: Any, point: dict[str, Any], pointer_id: int) -> dict[str, Any]:
    state = page.evaluate(POINTER, {"x": point["x"], "y": point["y"], "pointerId": pointer_id})
    return state if isinstance(state, dict) else {}


def tap(page: Any, selector: str) -> None:
    loc = page.locator(selector).first
    if loc.is_visible():
        loc.tap()
    else:
        loc.dispatch_event("click")


def edge_sheet_problems(page: Any, kind: str) -> list[str]:
    info = page.evaluate(
        """() => {
          function shown(el) {
            if (!el || (el.closest && el.closest('[hidden]'))) return false;
            const st = getComputedStyle(el);
            if (st.display === 'none' || st.visibility === 'hidden') return false;
            const r = el.getBoundingClientRect();
            return r.width >= 1 && r.height >= 1;
          }
          function boxOf(el) {
            if (!shown(el)) return null;
            const r = el.getBoundingClientRect();
            return {left: r.left, top: r.top, right: r.right, bottom: r.bottom, width: r.width, height: r.height};
          }
          function overlaps(a, b) {
            if (!a || !b) return false;
            return a.left < b.right - 1 && a.right > b.left + 1 && a.top < b.bottom - 1 && a.bottom > b.top + 1;
          }
          const input = document.getElementById('edgeSize');
          const sheet = document.getElementById('edgeSheet');
          const span = sheet ? sheet.querySelector('.edge-size span') : null;
          const sheetBox = boxOf(sheet);
          const covers = [];
          for (const sel of ['.vp-bar']) {
            const bar = boxOf(document.querySelector(sel));
            if (!bar) covers.push('missing ' + sel);
            else if (sheetBox && overlaps(sheetBox, bar)) covers.push(sel);
          }
          return {
            type: input ? input.getAttribute('type') : '',
            inputmode: input ? input.getAttribute('inputmode') : '',
            autocomplete: input ? input.getAttribute('autocomplete') : '',
            spellcheck: input ? input.getAttribute('spellcheck') : '',
            min: !!(input && input.hasAttribute('min')),
            step: !!(input && input.hasAttribute('step')),
            mm: span ? String(span.textContent || '').trim() : '',
            covers: covers,
            sheet: !!sheetBox
          };
        }"""
    )
    if not isinstance(info, dict):
        return [f"{kind} edge sheet {info!r}"]
    problems: list[str] = []
    if info.get("type") != "text" or info.get("inputmode") != "decimal":
        problems.append(f"{kind} edge field {info.get('type')!r} {info.get('inputmode')!r}")
    if info.get("autocomplete") != "off" or info.get("spellcheck") != "false":
        problems.append(f"{kind} edge field attrs {info.get('autocomplete')!r} {info.get('spellcheck')!r}")
    if info.get("min") is True or info.get("step") is True:
        problems.append(f"{kind} edge field stepper {info!r}")
    if info.get("mm") != "mm":
        problems.append(f"{kind} edge suffix {info.get('mm')!r}")
    if info.get("sheet") is not True or info.get("covers"):
        problems.append(f"{kind} edge sheet clearance {info.get('covers')!r}")
    return problems


def box_ok(page: Any, selector: str) -> dict[str, float] | None:
    box = page.locator(selector).first.bounding_box()
    if not box:
        return None
    return {"w": float(box["width"]), "h": float(box["height"])}


def volume_of(state: dict[str, Any]) -> float:
    try:
        return float(state.get("volumeMm3"))
    except (TypeError, ValueError):
        return float("nan")


def wait_volume(page: Any, want: float, tol: float) -> dict[str, Any]:
    page.wait_for_function(
        """(spec) => {
          const state = window.__cadcamExportState || {};
          const vol = Number(state.volumeMm3);
          return Number.isFinite(vol) && Math.abs(vol - spec.want) <= spec.tol;
        }""",
        arg={"want": want, "tol": tol},
    )
    return read_state(page)


def hint_text(page: Any) -> str:
    return page.locator("#statusHint").inner_text().strip()


def show_view(page: Any, name: str) -> None:
    tap(page, f"[data-action='view'][data-view='{name}']")
    page.wait_for_timeout(450)


def pick_named(page: Any, key: str, problems: list[str], kind: str) -> dict[str, Any] | None:
    views = ("", "top", "right", "front", "home")
    last = aims(page)
    for view in views:
        if view:
            show_view(page, view)
        found = aims(page)
        last = found
        point = found.get(key) if isinstance(found.get(key), dict) else None
        if point and point.get("x") is not None:
            return point
    ends = page.evaluate(
        "() => window.__cadcamPhoneSelect && window.__cadcamPhoneSelect.edges ? window.__cadcamPhoneSelect.edges() : []"
    )
    problems.append(f"{kind} no {key} aim ends {ends!r}")
    return None


def run_case(page: Any, kind: str) -> list[str]:
    problems: list[str] = []
    page.wait_for_function(
        """() => {
          const state = window.__cadcamExportState;
          const vol = state ? Number(state.volumeMm3) : NaN;
          return !!(state && state.occtReady === true && window.__cadcamPhoneSelect
            && state.bodyCount === 1 && state.demo === '' && state.primitiveKind === ''
            && state.exactVolume === true && Math.abs(vol - 6080) < 5);
        }"""
    )
    start = read_state(page)
    start_vol = volume_of(start)
    print(f"{kind} plain L volume {start_vol}", flush=True)
    if start.get("opLog"):
        problems.append(f"{kind} plain L opLog {start.get('opLog')!r}")
    shot(page, kind, "01-ready")

    tap(page, '[data-action="armEdge"][data-op="fillet"]')
    page.wait_for_function(
        """() => {
          const state = window.__cadcamExportState || {};
          return state.phoneFilter === 'edge' && state.edgeArm === 'fillet'
            && state.edgeSize === '2' && state.edgeSheetOpen === true;
        }"""
    )
    chip = (page.locator("#pickFilter").text_content() or "").strip()
    if chip != "Edge":
        problems.append(f"{kind} fillet chip {chip!r}")
    size_box = box_ok(page, "#edgeSize")
    confirm_box = box_ok(page, "#edgeConfirm")
    print(f"{kind} size {size_box} confirm {confirm_box}", flush=True)
    if not size_box or size_box["w"] + 0.5 < 44 or size_box["h"] + 0.5 < 44:
        problems.append(f"{kind} edge size target {size_box!r}")
    if not confirm_box or confirm_box["w"] + 0.5 < 44 or confirm_box["h"] + 0.5 < 44:
        problems.append(f"{kind} confirm target {confirm_box!r}")
    problems.extend(edge_sheet_problems(page, kind))
    shot(page, kind, "02-fillet-armed")

    inner = pick_named(page, "inner", problems, kind)
    if not inner:
        return problems
    pointer(page, inner, 61)
    page.wait_for_function(
        """() => {
          const state = window.__cadcamExportState || {};
          return state.selectionCount === 1 && state.edgeConfirmEnabled === true;
        }"""
    )
    depth = int(read_state(page).get("undoDepth") or 0)
    page.locator("#edgeSize").fill("1,5")
    try:
        page.wait_for_function(
            """() => {
              const state = window.__cadcamExportState || {};
              return state.edgeSize === '1,5' && state.edgeConfirmEnabled === true;
            }""",
            timeout=8000,
        )
    except Exception as exc:
        problems.append(f"{kind} comma size {exc}")
    page.locator("#edgeSize").fill("80")
    page.wait_for_function("() => (window.__cadcamExportState || {}).edgeSize === '80'")
    tap(page, "#edgeConfirm")
    page.wait_for_function(
        """(depth) => {
          const state = window.__cadcamExportState || {};
          return state.undoDepth === depth && String(state.lastError || '').indexOf('Try a smaller size') >= 0;
        }""",
        arg=depth,
    )
    held = read_state(page)
    if abs(volume_of(held) - start_vol) > 0.5:
        problems.append(f"{kind} oversized volume {volume_of(held)} from {start_vol}")
    if SMALLER not in hint_text(page) and SMALLER not in str(held.get("lastError") or ""):
        problems.append(f"{kind} smaller message {held.get('lastError')!r} hint {hint_text(page)!r}")
    if held.get("exportAllowed") is not True:
        problems.append(f"{kind} export after reject {held.get('exportAllowed')!r}")
    shot(page, kind, "03-smaller")

    tap(page, '[data-action="armEdge"][data-op="fillet"]')
    page.wait_for_function("() => (window.__cadcamExportState || {}).edgeSize === '2'")
    inner = pick_named(page, "inner", problems, kind)
    if not inner:
        return problems
    pointer(page, inner, 62)
    page.wait_for_function("() => (window.__cadcamExportState || {}).edgeConfirmEnabled === true")
    before_fillet = int(read_state(page).get("undoDepth") or 0)
    tap(page, "#edgeConfirm")
    page.wait_for_function(
        """(spec) => {
          const state = window.__cadcamExportState || {};
          const vol = Number(state.volumeMm3);
          return state.undoDepth === spec.depth + 1 && Number.isFinite(vol) && Math.abs(vol - spec.start) > 5;
        }""",
        arg={"depth": before_fillet, "start": start_vol},
    )
    filleted = read_state(page)
    fillet_vol = volume_of(filleted)
    print(f"{kind} fillet volume {fillet_vol}", flush=True)
    if filleted.get("exportAllowed") is not True:
        problems.append(f"{kind} export after fillet {filleted.get('exportAllowed')!r}")
    shot(page, kind, "04-filleted")

    tap(page, ".topbar [data-action='undo']")
    undone = wait_volume(page, start_vol, 0.5)
    if int(undone.get("redoDepth") or 0) < 1:
        problems.append(f"{kind} fillet undo redoDepth {undone.get('redoDepth')!r}")
    shot(page, kind, "05-undo")
    tap(page, ".topbar [data-action='redo']")
    redone = wait_volume(page, fillet_vol, 0.5)
    shot(page, kind, "06-redo")
    if abs(volume_of(redone) - fillet_vol) > 0.5:
        problems.append(f"{kind} fillet redo {volume_of(redone)} want {fillet_vol}")

    tap(page, '[data-action="armEdge"][data-op="chamfer"]')
    page.wait_for_function(
        """() => {
          const state = window.__cadcamExportState || {};
          return state.edgeArm === 'chamfer' && state.edgeSize === '0.5' && state.phoneFilter === 'edge';
        }"""
    )
    tip = pick_named(page, "tip", problems, kind)
    if not tip:
        return problems
    pointer(page, tip, 63)
    page.wait_for_function("() => (window.__cadcamExportState || {}).edgeConfirmEnabled === true")
    before_chamfer = volume_of(read_state(page))
    chamfer_depth = int(read_state(page).get("undoDepth") or 0)
    tap(page, "#edgeConfirm")
    page.wait_for_function(
        """(spec) => {
          const state = window.__cadcamExportState || {};
          const vol = Number(state.volumeMm3);
          return state.undoDepth === spec.depth + 1 && Number.isFinite(vol) && Math.abs(vol - spec.before) > 0.5;
        }""",
        arg={"depth": chamfer_depth, "before": before_chamfer},
    )
    chamfered = read_state(page)
    chamfer_vol = volume_of(chamfered)
    print(f"{kind} chamfer volume {chamfer_vol}", flush=True)
    shot(page, kind, "07-chamfer")
    tap(page, ".topbar [data-action='undo']")
    wait_volume(page, before_chamfer, 0.5)
    tap(page, ".topbar [data-action='redo']")
    wait_volume(page, chamfer_vol, 0.5)
    shot(page, kind, "08-chamfer-redo")

    tap(page, "[data-action='toolsMenu']")
    tap(page, "#toolsSheet [data-action='createMenu']")
    page.wait_for_function("() => document.getElementById('createMenu').hidden === false")
    tap(page, "#createMenu [data-kind='box']")
    tap(page, "#originPlanes [data-plane='xy']")
    tap(page, "#primConfirm")
    page.wait_for_function("() => (window.__cadcamExportState || {}).bodyCount === 2")
    tap(page, '[data-action="armEdge"][data-op="fillet"]')
    page.wait_for_function(
        """() => {
          const state = window.__cadcamExportState || {};
          return state.phoneFilter === 'edge' && state.edgeArm === 'fillet' && state.selectionCount === 0;
        }"""
    )
    if read_state(page).get("phoneMulti") is not True:
        tap(page, "#multiToggle")
    page.wait_for_function("() => (window.__cadcamExportState || {}).phoneMulti === true")

    picked: list[dict[str, Any]] = []
    for view in ("", "top", "right", "front", "home"):
        if view:
            show_view(page, view)
        found = aims(page)
        rows = found.get("bodyEdges") if isinstance(found.get("bodyEdges"), list) else []
        bodies = []
        for row in rows:
            if isinstance(row, dict) and row.get("bodyId") and row.get("x") is not None:
                if row["bodyId"] not in bodies:
                    bodies.append(row["bodyId"])
        if len(bodies) >= 2:
            picked = [row for row in rows if isinstance(row, dict)]
            break
    if len({row.get("bodyId") for row in picked}) < 2:
        problems.append(f"{kind} cross-body aims {picked!r}")
        return problems
    seen: set[str] = set()
    pointer_id = 70
    for row in picked:
        body_id = str(row.get("bodyId") or "")
        if not body_id or body_id in seen:
            continue
        seen.add(body_id)
        pointer(page, row, pointer_id)
        pointer_id += 1
        if len(seen) >= 2:
            break
    page.wait_for_function(
        """(message) => {
          const state = window.__cadcamExportState || {};
          return state.selectionCount >= 2 && state.edgeConfirmEnabled === false
            && state.edgeNote === message;
        }""",
        arg=CROSS,
    )
    blocked = read_state(page)
    if blocked.get("edgeNote") != CROSS:
        problems.append(f"{kind} cross note {blocked.get('edgeNote')!r}")
    if blocked.get("edgeConfirmEnabled") is not False:
        problems.append(f"{kind} cross confirm {blocked.get('edgeConfirmEnabled')!r}")
    if blocked.get("exportAllowed") is not True:
        problems.append(f"{kind} export during cross {blocked.get('exportAllowed')!r}")
    shot(page, kind, "09-cross")
    return problems


def run_engine(playwright: Any, engine: str, origin: str) -> list[str]:
    browser = getattr(playwright, engine).launch(headless=True)
    try:
        if engine == "webkit":
            device = dict(playwright.devices["iPhone 13"])
            device.pop("default_browser_type", None)
            device["screen"] = {"width": 390, "height": 844}
            device["viewport"] = {"width": 390, "height": 844}
            device["device_scale_factor"] = 1
            context = browser.new_context(**device)
        else:
            context = browser.new_context(
                viewport={"width": 390, "height": 844},
                device_scale_factor=1,
                is_mobile=True,
                has_touch=True,
            )
        kind = "webkit" if engine == "webkit" else "chromium"
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
        url = origin + "/?part=l"
        print(f"load {kind} {url}", flush=True)
        page.goto(url, wait_until="domcontentloaded", timeout=deploy_smoke.PAGE_TIMEOUT_S * 1000)
        problems = run_case(page, kind)
        if errors:
            problems = [f"{kind} js: {item}" for item in errors[:8]] + problems
        if problems:
            return [f"{kind} 390x844", *problems]
        print(f"PASS edge_fillet_smoke {kind}", flush=True)
        return []
    finally:
        browser.close()


def run() -> int:
    gaps = deploy_smoke.libcascade_gaps()
    if gaps:
        text = "; ".join(gaps)
        if in_ci():
            print(f"FAIL edge_fillet_smoke: {text}", flush=True)
            print("CI must not skip edge_fillet_smoke.", flush=True)
            return 1
        print("SKIP edge_fillet_smoke: " + text, flush=True)
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
    thread = threading.Thread(target=server.serve_forever, name="edge-fillet-http", daemon=True)
    thread.start()
    try:
        with sync_playwright() as playwright:
            for engine in ("chromium", "webkit"):
                problems = run_engine(playwright, engine, origin)
                if problems:
                    print("FAIL edge_fillet_smoke", flush=True)
                    for line in problems:
                        print(line, flush=True)
                    return 1
        print("PASS edge_fillet_smoke", flush=True)
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
        print(f"FAIL edge_fillet_smoke: {exc}", flush=True)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
