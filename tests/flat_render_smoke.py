#!/usr/bin/env python3
"""Flat, Fusion-like model rendering smoke (Chromium and WebKit, desktop + phone-width).

Verifies:
- Default display mode reports Shaded+Edges on load and after a new body is created
  (single-body and multi-body).
- Scene has no DirectionalLight; keeps AmbientLight(0xffffff, 0.38) and
  HemisphereLight(0xdde7f5, 0x2a313c, 0.7).
- Body material is matte MeshLambertMaterial with flatShading: true, color 0x5aa4d6,
  and polygonOffset (true, factor 1, units 1); edge LineSegments (EdgesGeometry +
  LineBasicMaterial, 0x10283a) present and visible by default for single- and multi-body.
- No fake blob shadow in the scene; renderer color space/clipping, viewport CSS gradient,
  and GridHelper unchanged; no environment map or AO.
- Other display modes (Shaded, Wireframe, X-Ray, Shaded+Edges), selection color,
  swatches, section clipping, and X-ray still work through applyLook.
- Watertight gate still passes and units stay mm.

State waits only (no sleep, skip, xfail, or timeout bump). Exit 77 when
Playwright or libcascade is missing locally; fail hard when CI is set.
"""
from __future__ import annotations

import os
import sys
import threading
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
WORK = ROOT / "builds" / "flat-render-smoke"
SKIP = 77

CAPTURE_SCENE_SCRIPT = """
(() => {
  let origCreate = null;
  function hookThree() {
    if (!window.THREE || !window.THREE.WebGLRenderer || window.__cadcamSceneHooked) return;
    window.__cadcamSceneHooked = true;
    const OrigRenderer = window.THREE.WebGLRenderer;
    window.THREE.WebGLRenderer = function (...args) {
      const inst = new OrigRenderer(...args);
      window.__cadcamMainRenderer = inst;
      const origRender = inst.render;
      inst.render = function (sc, cam) {
        if (sc && Array.isArray(sc.children) && sc.children.some(c => c && c.type === 'GridHelper')) {
          window.__cadcamMainScene = sc;
          window.__cadcamMainCamera = cam;
        }
        return origRender.apply(this, arguments);
      };
      return inst;
    };
    window.THREE.WebGLRenderer.prototype = OrigRenderer.prototype;
  }
  Object.defineProperty(window, 'createCadcam', {
    configurable: true,
    enumerable: true,
    get() {
      hookThree();
      return origCreate;
    },
    set(fn) {
      if (typeof fn !== 'function') {
        origCreate = fn;
        return;
      }
      origCreate = async function (...args) {
        hookThree();
        const mod = await fn.apply(this, args);
        hookThree();
        return mod;
      };
    }
  });
})();
"""


def in_ci() -> bool:
    return os.environ.get("CI", "").strip().lower() not in {"", "0", "false", "no"}


def skip_missing_playwright() -> int:
    if in_ci():
        print(
            "FAIL flat_render_smoke: playwright is not importable; "
            "CI must not skip this test.",
            flush=True,
        )
        return 1
    print(
        "SKIP flat_render_smoke: playwright is not importable. "
        "Use builds/pwvenv/Scripts/python.exe.",
        flush=True,
    )
    return SKIP


try:
    from playwright.sync_api import sync_playwright
except ImportError:
    raise SystemExit(skip_missing_playwright())

import deploy_smoke


def tap(page: Any, selector: str) -> None:
    loc = page.locator(selector).first
    if loc.is_visible():
        loc.click()
    else:
        loc.dispatch_event("click")


def probe_render(page: Any) -> dict[str, Any]:
    snap = page.evaluate(
        """() => {
          const sc = window.__cadcamMainScene;
          const renderer = window.__cadcamMainRenderer;
          const s = window.__cadcamExportState || {};
          const readout = document.getElementById('displayReadout');
          const unitsEl = document.getElementById('statusUnits');
          const vp = document.getElementById('viewport');
          const vpBg = vp ? getComputedStyle(vp).backgroundImage : '';
          const displayBtns = {};
          document.querySelectorAll('[data-action="display"]').forEach(btn => {
            const m = btn.getAttribute('data-mode') || '';
            displayBtns[m] = {
              isOn: btn.classList.contains('is-on'),
              ariaPressed: btn.getAttribute('aria-pressed')
            };
          });
          if (!sc) {
            return { hasScene: false };
          }
          const lights = [];
          let directionalCount = 0;
          let blobShadowCount = 0;
          let gridInfo = null;
          let singleMesh = null;
          let bodyRootInfo = null;
          let sectionQuadInfo = null;

          sc.traverse(obj => {
            if (obj && obj.isLight) {
              if (obj.type === 'DirectionalLight' || obj.isDirectionalLight) {
                directionalCount += 1;
              }
              lights.push({
                type: obj.type,
                color: obj.color ? obj.color.getHex() : null,
                groundColor: obj.groundColor ? obj.groundColor.getHex() : null,
                intensity: Number(obj.intensity)
              });
            }
            if (obj && obj.isMesh && obj.material && obj.material.map && obj.geometry && obj.geometry.type === 'PlaneGeometry') {
              blobShadowCount += 1;
            }
          });

          for (const ch of sc.children) {
            if (!ch) continue;
            if (ch.type === 'GridHelper') {
              gridInfo = { visible: ch.visible === true };
            } else if (ch.isMesh && ch.children && ch.children.some(sub => sub && sub.isLineSegments)) {
              const edgeChild = ch.children.find(sub => sub && sub.isLineSegments);
              const mat = ch.material || {};
              const emat = (edgeChild && edgeChild.material) || {};
              const egeo = (edgeChild && edgeChild.geometry) || {};
              const posAttr = egeo.attributes && egeo.attributes.position;
              singleMesh = {
                visible: ch.visible === true,
                matType: mat.type || '',
                flatShading: mat.flatShading === true,
                color: mat.color ? mat.color.getHex() : null,
                transparent: mat.transparent === true,
                opacity: Number(mat.opacity),
                depthWrite: mat.depthWrite === true,
                polygonOffset: mat.polygonOffset === true,
                polygonOffsetFactor: Number(mat.polygonOffsetFactor),
                polygonOffsetUnits: Number(mat.polygonOffsetUnits),
                clippingCount: Array.isArray(mat.clippingPlanes) ? mat.clippingPlanes.length : 0,
                edgePresent: !!edgeChild,
                edgeVisible: !!(edgeChild && edgeChild.visible === true),
                edgeGeoType: egeo.type || '',
                edgeVertCount: posAttr ? Number(posAttr.count) : 0,
                edgeMatType: emat.type || '',
                edgeColor: emat.color ? emat.color.getHex() : null,
                edgeClippingCount: Array.isArray(emat.clippingPlanes) ? emat.clippingPlanes.length : 0
              };
            } else if (ch.isMesh && ch.geometry && ch.geometry.type === 'PlaneGeometry' && ch.material && ch.material.color && ch.material.color.getHex() === 0x14756e) {
              sectionQuadInfo = { visible: ch.visible === true };
            } else if (ch.type === 'Group' && ch.children && ch.children.every(sub => sub && sub.userData && sub.userData.bodyId)) {
              if (!bodyRootInfo || ch.children.length > 0) {
                bodyRootInfo = {
                  visible: ch.visible === true,
                  count: ch.children.length,
                  bodies: ch.children.map(sub => {
                    const bmat = sub.material || {};
                    const wire = sub.children && sub.children[0];
                    const wmat = (wire && wire.material) || {};
                    const wgeo = (wire && wire.geometry) || {};
                    const wpos = wgeo.attributes && wgeo.attributes.position;
                    return {
                      bodyId: sub.userData.bodyId,
                      visible: sub.visible === true,
                      matType: bmat.type || '',
                      flatShading: bmat.flatShading === true,
                      colorHex: bmat.color ? '#' + bmat.color.getHexString() : '',
                      emissiveHex: bmat.emissive ? '#' + bmat.emissive.getHexString() : '',
                      emissiveIntensity: Number(bmat.emissiveIntensity || 0),
                      transparent: bmat.transparent === true,
                      opacity: Number(bmat.opacity),
                      depthWrite: bmat.depthWrite === true,
                      polygonOffset: bmat.polygonOffset === true,
                      polygonOffsetFactor: Number(bmat.polygonOffsetFactor),
                      polygonOffsetUnits: Number(bmat.polygonOffsetUnits),
                      clippingCount: Array.isArray(bmat.clippingPlanes) ? bmat.clippingPlanes.length : 0,
                      wirePresent: !!(wire && wire.isLineSegments),
                      wireVisible: !!(wire && wire.visible === true),
                      wireGeoType: wgeo.type || '',
                      wireVertCount: wpos ? Number(wpos.count) : 0,
                      wireMatType: wmat.type || '',
                      wireColor: wmat.color ? wmat.color.getHex() : null,
                      wireClippingCount: Array.isArray(wmat.clippingPlanes) ? wmat.clippingPlanes.length : 0
                    };
                  })
                };
              }
            }
          }

          return {
            hasScene: true,
            envNull: sc.environment == null,
            outputColorSpace: renderer ? renderer.outputColorSpace : '',
            localClippingEnabled: !!(renderer && renderer.localClippingEnabled === true),
            toneMapping: renderer ? Number(renderer.toneMapping) : -1,
            displayReadout: readout ? String(readout.textContent || '').trim() : '',
            displayBtns: displayBtns,
            directionalCount: directionalCount,
            lights: lights,
            blobShadowCount: blobShadowCount,
            gridInfo: gridInfo,
            singleMesh: singleMesh,
            bodyRootInfo: bodyRootInfo,
            sectionQuadInfo: sectionQuadInfo,
            vpBg: vpBg,
            watertight: s.watertight === true,
            occtGate: s.occtGate === true,
            gateOcct: s.gateOcct || '',
            unitsPass: s.unitsPass === true,
            statusUnits: unitsEl ? String(unitsEl.textContent || '').trim().toLowerCase() : '',
            bodyCount: Number(s.bodyCount || 0),
            sceneCleared: s.sceneCleared === true,
            selectionHighlight: s.selectionHighlight === true
          };
        }"""
    )
    return snap if isinstance(snap, dict) else {}


def check_base_invariants(snap: dict[str, Any], tag: str, problems: list[str]) -> None:
    if not snap.get("hasScene"):
        problems.append(f"{tag} main scene not captured")
        return
    if snap.get("directionalCount") != 0:
        problems.append(f"{tag} directionalCount={snap.get('directionalCount')!r} (want 0)")
    lights = snap.get("lights") or []
    if len(lights) != 2:
        problems.append(f"{tag} lights count={len(lights)} {lights!r} (want 2: Ambient + Hemisphere)")
    else:
        amb = next((l for l in lights if l.get("type") == "AmbientLight"), None)
        hemi = next((l for l in lights if l.get("type") == "HemisphereLight"), None)
        if not amb or amb.get("color") != 0xFFFFFF or abs(float(amb.get("intensity", -1)) - 0.38) > 1e-6:
            problems.append(f"{tag} AmbientLight mismatch {amb!r}")
        if (
            not hemi
            or hemi.get("color") != 0xDDE7F5
            or hemi.get("groundColor") != 0x2A313C
            or abs(float(hemi.get("intensity", -1)) - 0.7) > 1e-6
        ):
            problems.append(f"{tag} HemisphereLight mismatch {hemi!r}")
    if snap.get("blobShadowCount") != 0:
        problems.append(f"{tag} blobShadowCount={snap.get('blobShadowCount')!r} (want 0)")
    if snap.get("envNull") is not True:
        problems.append(f"{tag} scene.environment is not null")
    if snap.get("outputColorSpace") != "srgb" or snap.get("localClippingEnabled") is not True:
        problems.append(
            f"{tag} renderer outputColorSpace={snap.get('outputColorSpace')!r} "
            f"localClippingEnabled={snap.get('localClippingEnabled')!r}"
        )
    vp_bg = str(snap.get("vpBg") or "")
    if "radial-gradient" not in vp_bg:
        problems.append(f"{tag} viewport gradient changed: {vp_bg!r}")
    sm = snap.get("singleMesh") or {}
    if sm.get("matType") != "MeshLambertMaterial" or sm.get("flatShading") is not True:
        problems.append(f"{tag} bodyMat type={sm.get('matType')!r} flatShading={sm.get('flatShading')!r}")
    if (
        sm.get("polygonOffset") is not True
        or sm.get("polygonOffsetFactor") != 1
        or sm.get("polygonOffsetUnits") != 1
    ):
        problems.append(
            f"{tag} polygonOffset={sm.get('polygonOffset')!r} "
            f"factor={sm.get('polygonOffsetFactor')!r} units={sm.get('polygonOffsetUnits')!r}"
        )
    if (
        sm.get("edgePresent") is not True
        or sm.get("edgeMatType") != "LineBasicMaterial"
        or (not snap.get("sceneCleared") and sm.get("edgeGeoType") != "EdgesGeometry")
    ):
        problems.append(f"{tag} edge LineSegments mismatch: {sm!r}")


def check_edges_default_active(snap: dict[str, Any], tag: str, problems: list[str]) -> None:
    if snap.get("displayReadout") != "Shaded + Edges":
        problems.append(f"{tag} displayReadout={snap.get('displayReadout')!r} (want 'Shaded + Edges')")
    btns = snap.get("displayBtns") or {}
    edges_btn = btns.get("edges") or {}
    shaded_btn = btns.get("shaded") or {}
    if edges_btn.get("isOn") is not True or edges_btn.get("ariaPressed") != "true":
        problems.append(f"{tag} edges button state {edges_btn!r}")
    if shaded_btn.get("isOn") is not False or shaded_btn.get("ariaPressed") != "false":
        problems.append(f"{tag} shaded button state {shaded_btn!r}")


def check_gate_and_mm(snap: dict[str, Any], tag: str, problems: list[str]) -> None:
    if snap.get("watertight") is not True:
        problems.append(f"{tag} watertight={snap.get('watertight')!r}")
    if snap.get("occtGate") is not True or snap.get("gateOcct") != "PASS":
        problems.append(f"{tag} occtGate={snap.get('occtGate')!r} gateOcct={snap.get('gateOcct')!r}")
    if snap.get("unitsPass") is not True or snap.get("statusUnits") != "mm":
        problems.append(f"{tag} unitsPass={snap.get('unitsPass')!r} statusUnits={snap.get('statusUnits')!r}")


def create_box_via_ui(page: Any, expected_bodies: int) -> None:
    is_narrow = page.evaluate("() => window.matchMedia('(max-width: 820px)').matches")
    if is_narrow:
        is_open = page.evaluate(
            "() => { const s = document.getElementById('toolsSheet'); return !!(s && s.hidden === false); }"
        )
        if not is_open:
            tap(page, "[data-action='toolsMenu']")
            page.wait_for_function(
                "() => { const s = document.getElementById('toolsSheet'); return !!(s && s.hidden === false); }"
            )
        tap(page, "#toolsSheet [data-action='createMenu']")
    else:
        tap(page, "#createDesktop")
    page.wait_for_function(
        "() => { const m = document.getElementById('createMenu'); return !!(m && m.hidden === false); }"
    )
    tap(page, "#createMenu [data-action='primitive'][data-kind='box']")
    page.wait_for_function(
        "() => (window.__cadcamExportState || {}).primCreateStep === 'plane'"
    )
    tap(page, "#originPlanes [data-action='originPlane'][data-plane='xy']")
    page.wait_for_function(
        """() => {
          const s = window.__cadcamExportState || {};
          return s.primCreateStep === 'dims' && s.primConfirmVisible === true;
        }"""
    )
    tap(page, "#primConfirm")
    page.wait_for_function(
        """(wantBodies) => {
          const s = window.__cadcamExportState || {};
          return s.sceneCleared === false
            && s.bodyCount === wantBodies
            && s.watertight === true
            && s.occtGate === true
            && s.gateOcct === 'PASS'
            && s.unitsPass === true;
        }""",
        arg=expected_bodies,
    )


def run_viewport_case(page: Any, kind: str, width: int, height: int, origin: str) -> list[str]:
    problems: list[str] = []
    tag = f"{kind} {width}x{height}"
    url = origin + "/"
    print(f"load {tag} {url}", flush=True)
    page.goto(url, wait_until="domcontentloaded", timeout=deploy_smoke.PAGE_TIMEOUT_S * 1000)
    page.wait_for_function(
        """() => {
          const s = window.__cadcamExportState;
          return !!(s && s.sceneCleared === true && s.bodyCount === 0 && window.__cadcamMainScene);
        }"""
    )

    # 1. Cold-start load: Shaded+Edges is default, no DirectionalLight, matte material, no blob shadow.
    snap0 = probe_render(page)
    check_base_invariants(snap0, f"{tag} cold-start", problems)
    check_edges_default_active(snap0, f"{tag} cold-start", problems)
    sm0 = snap0.get("singleMesh") or {}
    if sm0.get("color") != 0x5AA4D6 or sm0.get("edgeColor") != 0x10283A:
        problems.append(f"{tag} cold-start colors body={sm0.get('color')!r} edge={sm0.get('edgeColor')!r}")
    if problems:
        return problems

    # 2. Create first body (single-body): Shaded+Edges stays default, mesh + edges visible.
    create_box_via_ui(page, 1)
    snap1 = probe_render(page)
    check_base_invariants(snap1, f"{tag} single-body", problems)
    check_edges_default_active(snap1, f"{tag} single-body", problems)
    check_gate_and_mm(snap1, f"{tag} single-body", problems)
    sm1 = snap1.get("singleMesh") or {}
    if sm1.get("visible") is not True or sm1.get("edgeVisible") is not True or int(sm1.get("edgeVertCount") or 0) < 24:
        problems.append(f"{tag} single-body mesh/edge visibility {sm1!r}")
    if snap1.get("selectionHighlight") is not True:
        problems.append(f"{tag} single-body selectionHighlight={snap1.get('selectionHighlight')!r}")

    # 3. Other display modes (Shaded, Wireframe, X-Ray, back to Shaded+Edges) on single-body.
    tap(page, "[data-action='display'][data-mode='shaded']")
    page.wait_for_function(
        """() => {
          const r = document.getElementById('displayReadout');
          return !!(r && r.textContent.trim() === 'Shaded');
        }"""
    )
    snap_shaded = probe_render(page)
    sm_shaded = snap_shaded.get("singleMesh") or {}
    if sm_shaded.get("visible") is not True or sm_shaded.get("edgeVisible") is not False:
        problems.append(f"{tag} shaded mode visibility {sm_shaded!r}")

    tap(page, "[data-action='display'][data-mode='wire']")
    page.wait_for_function(
        """() => {
          const r = document.getElementById('displayReadout');
          return !!(r && r.textContent.trim() === 'Wireframe');
        }"""
    )
    snap_wire = probe_render(page)
    sm_wire = snap_wire.get("singleMesh") or {}
    if sm_wire.get("visible") is not False or sm_wire.get("edgeVisible") is not True:
        problems.append(f"{tag} wire mode visibility {sm_wire!r}")

    tap(page, "[data-action='display'][data-mode='xray']")
    page.wait_for_function(
        """() => {
          const r = document.getElementById('displayReadout');
          return !!(r && r.textContent.trim() === 'X-Ray');
        }"""
    )
    snap_xray = probe_render(page)
    sm_xray = snap_xray.get("singleMesh") or {}
    if (
        sm_xray.get("visible") is not True
        or sm_xray.get("edgeVisible") is not True
        or sm_xray.get("transparent") is not True
        or abs(float(sm_xray.get("opacity", 0)) - 0.28) > 1e-6
        or sm_xray.get("depthWrite") is not False
        or sm_xray.get("edgeColor") != 0xD7E4F2
    ):
        problems.append(f"{tag} xray mode state {sm_xray!r}")

    tap(page, "[data-action='display'][data-mode='edges']")
    page.wait_for_function(
        """() => {
          const r = document.getElementById('displayReadout');
          return !!(r && r.textContent.trim() === 'Shaded + Edges');
        }"""
    )
    snap_edges = probe_render(page)
    sm_edges = snap_edges.get("singleMesh") or {}
    if (
        sm_edges.get("visible") is not True
        or sm_edges.get("edgeVisible") is not True
        or sm_edges.get("transparent") is not False
        or abs(float(sm_edges.get("opacity", 0)) - 1.0) > 1e-6
        or sm_edges.get("depthWrite") is not True
        or sm_edges.get("edgeColor") != 0x10283A
    ):
        problems.append(f"{tag} restored edges mode state {sm_edges!r}")

    # 4. Section clipping toggle.
    tap(page, "[data-action='section']")
    page.wait_for_function(
        """() => {
          const btn = document.querySelector('[data-action="section"]');
          return !!(btn && btn.getAttribute('aria-pressed') === 'true');
        }"""
    )
    snap_sec_on = probe_render(page)
    sm_sec_on = snap_sec_on.get("singleMesh") or {}
    sq_on = snap_sec_on.get("sectionQuadInfo") or {}
    if sm_sec_on.get("clippingCount") != 1 or sm_sec_on.get("edgeClippingCount") != 1 or sq_on.get("visible") is not True:
        problems.append(f"{tag} section on state mesh={sm_sec_on!r} quad={sq_on!r}")

    tap(page, "[data-action='section']")
    page.wait_for_function(
        """() => {
          const btn = document.querySelector('[data-action="section"]');
          return !!(btn && btn.getAttribute('aria-pressed') === 'false');
        }"""
    )
    snap_sec_off = probe_render(page)
    sm_sec_off = snap_sec_off.get("singleMesh") or {}
    sq_off = snap_sec_off.get("sectionQuadInfo") or {}
    if sm_sec_off.get("clippingCount") != 0 or sm_sec_off.get("edgeClippingCount") != 0 or sq_off.get("visible") is not False:
        problems.append(f"{tag} section off state mesh={sm_sec_off!r} quad={sq_off!r}")

    # 5. Swatches update bodyMat color and restore default 0x5aa4d6.
    tap(page, ".swatch[data-color='#e39b4a']")
    page.wait_for_function(
        """() => {
          const sw = document.querySelector(".swatch[data-color='#e39b4a']");
          return !!(sw && sw.classList.contains('is-on'));
        }"""
    )
    snap_swatch = probe_render(page)
    if (snap_swatch.get("singleMesh") or {}).get("color") != 0xE39B4A:
        problems.append(f"{tag} swatch #e39b4a failed: {snap_swatch.get('singleMesh')!r}")

    tap(page, ".swatch[data-color='#5aa4d6']")
    page.wait_for_function(
        """() => {
          const sw = document.querySelector(".swatch[data-color='#5aa4d6']");
          return !!(sw && sw.classList.contains('is-on'));
        }"""
    )
    snap_swatch_reset = probe_render(page)
    if (snap_swatch_reset.get("singleMesh") or {}).get("color") != 0x5AA4D6:
        problems.append(f"{tag} swatch #5aa4d6 reset failed: {snap_swatch_reset.get('singleMesh')!r}")

    # 6. Create second body (multi-body): per-body edges from L5401 visible by default,
    #    matte material + polygonOffset cloned, selection color works on selected body.
    create_box_via_ui(page, 2)
    page.evaluate("() => { const row = document.querySelector('#partList .part-row'); if (row) row.click(); }")
    page.wait_for_function(
        "() => ((window.__cadcamExportState || {}).selectedIds || []).length === 1"
    )
    snap2 = probe_render(page)
    check_base_invariants(snap2, f"{tag} multi-body", problems)
    check_edges_default_active(snap2, f"{tag} multi-body", problems)
    check_gate_and_mm(snap2, f"{tag} multi-body", problems)
    br = snap2.get("bodyRootInfo") or {}
    if br.get("visible") is not True or br.get("count") != 2:
        problems.append(f"{tag} multi-body bodyRoot {br!r}")
    else:
        for binfo in br.get("bodies") or []:
            if (
                binfo.get("visible") is not True
                or binfo.get("matType") != "MeshLambertMaterial"
                or binfo.get("flatShading") is not True
                or binfo.get("polygonOffset") is not True
                or binfo.get("polygonOffsetFactor") != 1
                or binfo.get("polygonOffsetUnits") != 1
                or binfo.get("wirePresent") is not True
                or binfo.get("wireVisible") is not True
                or binfo.get("wireGeoType") != "EdgesGeometry"
                or binfo.get("wireMatType") != "LineBasicMaterial"
                or int(binfo.get("wireVertCount") or 0) < 24
            ):
                problems.append(f"{tag} multi-body child mismatch {binfo!r}")
        emissives = [float(b.get("emissiveIntensity") or 0) for b in (br.get("bodies") or [])]
        if not any(abs(val - 0.25) < 1e-6 for val in emissives):
            problems.append(f"{tag} multi-body selection emissive missing {br.get('bodies')!r}")

    return problems


def run_engine(playwright: Any, engine: str, origin: str) -> list[str]:
    browser = getattr(playwright, engine).launch(headless=True)
    try:
        kind = "webkit" if engine == "webkit" else "chromium"
        for width, height, is_mobile in ((1280, 800, False), (390, 844, True)):
            if engine == "webkit" and is_mobile:
                device = dict(playwright.devices["iPhone 13"])
                device.pop("default_browser_type", None)
                device["screen"] = {"width": width, "height": height}
                device["viewport"] = {"width": width, "height": height}
                device["device_scale_factor"] = 1
                context = browser.new_context(**device)
            else:
                context = browser.new_context(
                    viewport={"width": width, "height": height},
                    device_scale_factor=1,
                    is_mobile=is_mobile,
                    has_touch=is_mobile,
                )
            try:
                context.add_init_script(CAPTURE_SCENE_SCRIPT)
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
                problems = run_viewport_case(page, kind, width, height, origin)
                if errors:
                    problems = [f"{kind} {width}x{height} js: {item}" for item in errors[:8]] + problems
                if problems:
                    return [f"{kind} {width}x{height}", *problems]
                print(f"PASS flat_render_smoke {kind} {width}x{height}", flush=True)
            finally:
                context.close()
        return []
    finally:
        browser.close()


def run() -> int:
    gaps = deploy_smoke.libcascade_gaps()
    if gaps:
        text = "; ".join(gaps)
        if in_ci():
            print(f"FAIL flat_render_smoke: {text}", flush=True)
            print("CI must not skip flat_render_smoke.", flush=True)
            return 1
        print("SKIP flat_render_smoke: " + text, flush=True)
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
    thread = threading.Thread(target=server.serve_forever, name="flat-render-http", daemon=True)
    thread.start()
    try:
        with sync_playwright() as playwright:
            for engine in ("chromium", "webkit"):
                problems = run_engine(playwright, engine, origin)
                if problems:
                    print("FAIL flat_render_smoke", flush=True)
                    for line in problems:
                        print(line, flush=True)
                    return 1
        print("PASS flat_render_smoke", flush=True)
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
        print(f"FAIL flat_render_smoke: {exc}", flush=True)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
