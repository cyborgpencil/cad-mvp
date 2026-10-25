#!/usr/bin/env python3
"""Phone selection in a 390x844 frame: tap, filter, Multi, delete, undo, redo.

Real pointer events. Screenshots land in builds/logs/phone-select-shots/.
Exit 77 when Playwright or libcascade is missing.
"""
from __future__ import annotations

import math
import sys
import threading
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
WORK = ROOT / "builds" / "phone-select-smoke"
SHOTS = ROOT / "builds" / "logs" / "phone-select-shots"
SKIP = 77

FILTERS = ("body", "face", "edge", "vertex")


def skip_missing_playwright() -> int:
    print(
        "SKIP phone_select_smoke: playwright is not importable. "
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
      pointerId: spec.pointerId || 51,
      pointerType: 'touch',
      isPrimary: true,
      button: 0,
      buttons: ending ? 0 : 1,
      clientX: x,
      clientY: y
    }));
  }
  const x0 = Number(spec.x);
  const y0 = Number(spec.y);
  fire('pointerdown', x0, y0);
  if (spec.drag) {
    const dx = Number(spec.dx) || 0;
    const dy = Number(spec.dy) || 0;
    const steps = 4;
    for (let i = 1; i <= steps; i += 1) {
      fire('pointermove', x0 + dx * i / steps, y0 + dy * i / steps);
    }
    fire('pointerup', x0 + dx, y0 + dy);
  } else {
    fire('pointerup', x0, y0);
  }
  return window.__cadcamExportState || {};
}"""


def cam_angle(before: dict[str, Any] | None, after: dict[str, Any] | None) -> float:
    if not isinstance(before, dict) or not isinstance(after, dict):
        return 0.0
    bd = before.get("direction")
    ad = after.get("direction")
    if not isinstance(bd, list) or not isinstance(ad, list) or len(bd) != 3 or len(ad) != 3:
        return 0.0
    dot = float(bd[0]) * float(ad[0]) + float(bd[1]) * float(ad[1]) + float(bd[2]) * float(ad[2])
    dot = max(-1.0, min(1.0, dot))
    return math.degrees(math.acos(dot))


def read_nav(page: Any) -> dict[str, Any]:
    nav = page.evaluate("() => window.__cadcamNavCube ? window.__cadcamNavCube() : null")
    return nav if isinstance(nav, dict) else {}


def read_state(page: Any) -> dict[str, Any]:
    state = page.evaluate("() => window.__cadcamExportState || null")
    return state if isinstance(state, dict) else {}


def aims(page: Any) -> dict[str, Any]:
    found = page.evaluate("() => window.__cadcamPhoneSelect.aims()")
    return found if isinstance(found, dict) else {}


def shot(page: Any, kind: str, name: str) -> None:
    SHOTS.mkdir(parents=True, exist_ok=True)
    page.screenshot(path=str(SHOTS / f"{kind}-{name}.png"))


def pointer(page: Any, spec: dict[str, Any]) -> dict[str, Any]:
    state = page.evaluate(POINTER, spec)
    return state if isinstance(state, dict) else {}


def count_text(page: Any) -> str:
    return page.locator("#selectionCount").inner_text().strip()


def box_ok(page: Any, selector: str) -> dict[str, float] | None:
    box = page.locator(selector).bounding_box()
    if not box:
        return None
    return {"w": float(box["width"]), "h": float(box["height"])}


def choose_filter(page: Any, name: str) -> None:
    page.locator("#pickFilter").click()
    page.locator(f"#pickChooser [data-filter='{name}']").click()
    page.wait_for_function(
        """(name) => {
          const state = window.__cadcamExportState || {};
          const chooser = document.getElementById('pickChooser');
          return state.phoneFilter === name
            && state.selectionCount === 0
            && !!(chooser && chooser.hidden);
        }""",
        arg=name,
    )


def wait_field(page: Any, script: str, arg: Any = None) -> None:
    page.wait_for_function(script, arg=arg)


def near(got: Any, want: float, tol: float = 0.01) -> bool:
    try:
        return abs(float(got) - want) <= tol
    except (TypeError, ValueError):
        return False


def run_case(page: Any, kind: str) -> list[str]:
    problems: list[str] = []
    page.wait_for_function(
        """() => {
          const state = window.__cadcamExportState;
          return !!(state && state.occtReady === true && window.__cadcamPhoneSelect
            && state.primitiveKind === 'box' && state.bodyCount === 1);
        }"""
    )
    hook = page.evaluate("() => window.__cadcamPhoneSelect")
    if not isinstance(hook, dict) or hook.get("edgePx") != 32 or hook.get("vertexPx") != 32 or hook.get("touchPx") != 20:
        return [f"{kind} hook {hook!r}"]
    if hook.get("chipMin") != 44 or hook.get("filters") != ["body", "face", "edge", "vertex"]:
        return [f"{kind} hook filters {hook!r}"]
    if hook.get("slopPx") != 8:
        problems.append(f"{kind} slop {hook.get('slopPx')!r}")

    chip = box_ok(page, "#pickFilter")
    multi = box_ok(page, "#multiToggle")
    print(f"{kind} chip {chip} multi {multi}", flush=True)
    if not chip or chip["w"] + 0.5 < 44 or chip["h"] + 0.5 < 44:
        problems.append(f"{kind} chip size {chip!r}")
    if not multi or multi["w"] + 0.5 < 44 or multi["h"] + 0.5 < 44:
        problems.append(f"{kind} multi size {multi!r}")
    shot(page, kind, "01-ready")

    page.locator("#pickFilter").click()
    page.wait_for_function("() => document.getElementById('pickChooser').hidden === false")
    for name in FILTERS:
        size = box_ok(page, f"#pickChooser [data-filter='{name}']")
        if not size or size["h"] + 0.5 < 44:
            problems.append(f"{kind} chooser {name} {size!r}")
    page.locator("#pickFilter").click()
    page.wait_for_function(
        """() => {
          const state = window.__cadcamExportState || {};
          const chooser = document.getElementById('pickChooser');
          return state.selectionCount === 1 && state.phoneFilter === 'body' && !!(chooser && chooser.hidden);
        }"""
    )

    found = aims(page)
    empty = found.get("empty") if isinstance(found.get("empty"), dict) else None
    body = found.get("body") if isinstance(found.get("body"), dict) else None
    print(f"{kind} aims empty {empty} body {body}", flush=True)
    if not empty or not body:
        problems.append(f"{kind} missing empty/body aim { {k: found.get(k) for k in ('empty', 'body')} }")
        return problems

    cleared = pointer(page, {"x": empty["x"], "y": empty["y"], "pointerId": 51})
    shot(page, kind, "02-cleared")
    if cleared.get("selectionCount") != 0 or cleared.get("selectedIds") not in ([], None):
        problems.append(f"{kind} empty tap {cleared.get('selectionCount')!r} {cleared.get('selectedIds')!r}")
    if cleared.get("selectionHighlight") is not False:
        problems.append(f"{kind} empty highlight {cleared.get('selectionHighlight')!r}")
    if count_text(page) != "0 selected":
        problems.append(f"{kind} empty count text {count_text(page)!r}")

    before_cam = read_nav(page)
    dragged = pointer(page, {
        "x": empty["x"],
        "y": empty["y"],
        "drag": True,
        "dx": 36,
        "dy": 12,
        "pointerId": 52,
    })
    after_cam = read_nav(page)
    angle = cam_angle(before_cam, after_cam)
    print(f"{kind} drag angle {angle:.3f} count {dragged.get('selectionCount')}", flush=True)
    shot(page, kind, "03-drag")
    if dragged.get("selectionCount") != 0:
        problems.append(f"{kind} drag selected {dragged.get('selectedIds')!r}")
    if angle < 0.5:
        problems.append(f"{kind} drag did not orbit ({angle:.3f} deg)")

    found = aims(page)
    body = found.get("body") if isinstance(found.get("body"), dict) else None
    if not body or not body.get("id"):
        problems.append(f"{kind} body aim after drag {body!r}")
        return problems
    picked = pointer(page, {"x": body["x"], "y": body["y"], "pointerId": 53})
    shot(page, kind, "04-body")
    ids = picked.get("selectedIds")
    if picked.get("selectionCount") != 1 or not isinstance(ids, list) or body["id"] not in ids:
        problems.append(f"{kind} body pick {picked.get('selectionCount')!r} {ids!r} want {body.get('id')!r}")
    if picked.get("phoneFilter") != "body" or picked.get("selectionHighlight") is not True:
        problems.append(f"{kind} body chrome {picked.get('phoneFilter')!r} {picked.get('selectionHighlight')!r}")
    if count_text(page) != "1 selected":
        problems.append(f"{kind} body count text {count_text(page)!r}")

    for name, step in (("face", "05-face"), ("edge", "06-edge"), ("vertex", "07-vertex")):
        choose_filter(page, name)
        found = aims(page)
        aim = found.get(name) if isinstance(found.get(name), dict) else None
        print(f"{kind} {name} aim {aim}", flush=True)
        if not aim or not aim.get("id"):
            problems.append(f"{kind} {name} aim missing {aim!r}")
            continue
        if name in ("edge", "vertex"):
            gap = aim.get("gap")
            touch_px = found.get("touchPx")
            edge_px = found.get("edgePx" if name == "edge" else "vertexPx")
            try:
                gap_n = float(gap)
                touch_n = float(touch_px)
                edge_n = float(edge_px)
            except (TypeError, ValueError):
                problems.append(f"{kind} {name} gap {gap!r} touch {touch_px!r} limit {edge_px!r}")
                gap_n = touch_n = edge_n = 0.0
            if not (touch_n < gap_n < edge_n):
                problems.append(f"{kind} {name} gap {gap_n} not between {touch_n} and {edge_n}")
        picked = pointer(page, {"x": aim["x"], "y": aim["y"], "pointerId": 54})
        shot(page, kind, step)
        ids = picked.get("selectedIds")
        if picked.get("selectionCount") != 1 or picked.get("phoneFilter") != name or not isinstance(ids, list) or aim["id"] not in ids:
            problems.append(f"{kind} {name} pick {picked.get('phoneFilter')!r} {picked.get('selectionCount')!r} {ids!r} want {aim.get('id')!r}")
        if picked.get("selectionHighlight") is not True:
            problems.append(f"{kind} {name} highlight off")
        if count_text(page) != "1 selected":
            problems.append(f"{kind} {name} count text {count_text(page)!r}")

    choose_filter(page, "body")
    found = aims(page)
    body = found.get("body") if isinstance(found.get("body"), dict) else None
    if not body:
        problems.append(f"{kind} body aim before delete missing")
        return problems
    pointer(page, {"x": body["x"], "y": body["y"], "pointerId": 55})
    before_delete = read_state(page)
    if before_delete.get("selectionCount") != 1 or before_delete.get("bodyCount") != 1:
        problems.append(f"{kind} solid not selected {before_delete.get('selectionCount')!r}")
    depth = int(before_delete.get("undoDepth") or 0)
    page.locator("#deleteBtn").click()
    wait_field(
        page,
        """() => {
          const state = window.__cadcamExportState || {};
          return state.bodyCount === 0 && state.sceneCleared === true;
        }""",
    )
    shot(page, kind, "08-solid-delete")
    deleted = read_state(page)
    if int(deleted.get("undoDepth") or 0) != depth + 1:
        problems.append(f"{kind} solid undo depth {deleted.get('undoDepth')!r} was {depth}")

    page.locator(".phone-tabbar [data-action='undo']").click()
    wait_field(
        page,
        """() => {
          const state = window.__cadcamExportState || {};
          return state.bodyCount === 1 && state.sceneCleared === false;
        }""",
    )
    shot(page, kind, "09-solid-undo")
    page.locator(".phone-tabbar [data-action='redo']").click()
    wait_field(
        page,
        """() => {
          const state = window.__cadcamExportState || {};
          return state.bodyCount === 0 && state.sceneCleared === true;
        }""",
    )
    shot(page, kind, "10-solid-redo")
    page.locator(".phone-tabbar [data-action='undo']").click()
    wait_field(
        page,
        """() => {
          const state = window.__cadcamExportState || {};
          return state.bodyCount === 1 && state.sceneCleared === false;
        }""",
    )

    page.locator("#multiToggle").click()
    wait_field(page, "() => (window.__cadcamExportState || {}).phoneMulti === true")
    page.locator("#createBtn").click()
    page.locator("#createMenu [data-kind='box']").click()
    wait_field(page, "() => (window.__cadcamExportState || {}).bodyCount === 2")
    shot(page, kind, "11-two-bodies")
    found = aims(page)
    bodies = found.get("bodies") if isinstance(found.get("bodies"), list) else []
    print(f"{kind} multi bodies {bodies}", flush=True)
    if len(bodies) < 2:
        problems.append(f"{kind} multi aims {bodies!r}")
        return problems
    first = bodies[0]
    second = bodies[1]
    pointer(page, {"x": first["x"], "y": first["y"], "pointerId": 56})
    one = read_state(page)
    if one.get("selectionCount") != 1 or first.get("id") not in (one.get("selectedIds") or []):
        problems.append(f"{kind} multi first {one.get('selectedIds')!r}")
    found = aims(page)
    bodies = found.get("bodies") if isinstance(found.get("bodies"), list) else []
    second = next((item for item in bodies if item.get("id") == second.get("id")), None)
    if not isinstance(second, dict):
        problems.append(f"{kind} multi second aim lost {bodies!r}")
        return problems
    pointer(page, {"x": second["x"], "y": second["y"], "pointerId": 57})
    both = read_state(page)
    shot(page, kind, "12-multi-add")
    both_ids = both.get("selectedIds") if isinstance(both.get("selectedIds"), list) else []
    if both.get("selectionCount") != 2 or first.get("id") not in both_ids or second.get("id") not in both_ids:
        problems.append(f"{kind} multi add {both_ids!r}")
    if count_text(page) != "2 selected":
        problems.append(f"{kind} multi count text {count_text(page)!r}")
    if both.get("selectionHighlight") is not True:
        problems.append(f"{kind} multi highlight off")
    pointer(page, {"x": second["x"], "y": second["y"], "pointerId": 58})
    removed = read_state(page)
    shot(page, kind, "13-multi-remove")
    removed_ids = removed.get("selectedIds") if isinstance(removed.get("selectedIds"), list) else []
    if removed.get("selectionCount") != 1 or second.get("id") in removed_ids or first.get("id") not in removed_ids:
        problems.append(f"{kind} multi remove {removed_ids!r}")

    hole = page.evaluate("() => window.__cadcamPhoneSelect.installHole()")
    print(f"{kind} hole {hole}", flush=True)
    if not isinstance(hole, dict) or hole.get("ok") is not True or not hole.get("faceId"):
        problems.append(f"{kind} hole fixture {hole!r}")
        return problems
    try:
        plain = float(hole.get("plain"))
        holed = float(hole.get("volume"))
    except (TypeError, ValueError):
        problems.append(f"{kind} hole volumes {hole!r}")
        return problems
    choose_filter(page, "face")
    found = aims(page)
    cyl = found.get("cylinder") if isinstance(found.get("cylinder"), dict) else None
    print(f"{kind} cylinder {cyl}", flush=True)
    if not cyl or cyl.get("id") != hole.get("faceId"):
        problems.append(f"{kind} cylinder aim {cyl!r} want {hole.get('faceId')!r}")
        return problems
    pointer(page, {"x": cyl["x"], "y": cyl["y"], "pointerId": 59})
    faced = read_state(page)
    shot(page, kind, "14-cylinder-face")
    if faced.get("selectionCount") != 1 or hole.get("faceId") not in (faced.get("selectedIds") or []):
        problems.append(f"{kind} cylinder pick {faced.get('selectedIds')!r}")
        return problems
    face_depth = int(faced.get("undoDepth") or 0)
    page.locator("#deleteBtn").click()
    wait_field(
        page,
        """(spec) => {
          const state = window.__cadcamExportState || {};
          return state.bodyCount === 1
            && state.sceneCleared === false
            && Math.abs(Number(state.volumeMm3) - spec.plain) <= spec.tol;
        }""",
        arg={"plain": plain, "tol": 0.01},
    )
    shot(page, kind, "15-face-delete")
    after_face = read_state(page)
    if int(after_face.get("undoDepth") or 0) != face_depth + 1:
        problems.append(f"{kind} face undo depth {after_face.get('undoDepth')!r} was {face_depth}")
    page.locator(".phone-tabbar [data-action='undo']").click()
    wait_field(
        page,
        """(spec) => {
          const state = window.__cadcamExportState || {};
          return state.bodyCount === 1 && Math.abs(Number(state.volumeMm3) - spec.holed) <= spec.tol;
        }""",
        arg={"holed": holed, "tol": 0.01},
    )
    shot(page, kind, "16-face-undo")
    page.locator(".phone-tabbar [data-action='redo']").click()
    wait_field(
        page,
        """(spec) => {
          const state = window.__cadcamExportState || {};
          return state.bodyCount === 1 && Math.abs(Number(state.volumeMm3) - spec.plain) <= spec.tol;
        }""",
        arg={"plain": plain, "tol": 0.01},
    )
    shot(page, kind, "17-face-redo")
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
        url = origin + "/?primitive=box&select=item"
        print(f"load {kind} {url}", flush=True)
        page.goto(url, wait_until="domcontentloaded", timeout=deploy_smoke.PAGE_TIMEOUT_S * 1000)
        problems = run_case(page, kind)
        if errors:
            problems = [f"{kind} js: {item}" for item in errors[:8]] + problems
        if problems:
            return [f"{kind} 390x844", *problems]
        print(f"PASS phone_select_smoke {kind}", flush=True)
        return []
    finally:
        browser.close()


def run() -> int:
    gaps = deploy_smoke.libcascade_gaps()
    if gaps:
        print("SKIP phone_select_smoke: " + "; ".join(gaps), flush=True)
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
    thread = threading.Thread(target=server.serve_forever, name="phone-select-http", daemon=True)
    thread.start()
    try:
        with sync_playwright() as playwright:
            for engine in ("chromium", "webkit"):
                problems = run_engine(playwright, engine, origin)
                if problems:
                    print("FAIL phone_select_smoke", flush=True)
                    for line in problems:
                        print(line, flush=True)
                    return 1
        print("PASS phone_select_smoke", flush=True)
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
        print(f"FAIL phone_select_smoke: {exc}", flush=True)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
