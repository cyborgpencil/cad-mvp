// Rust WASM shadow mirror of the units + mesh volume Export gate (slice #1).
// C++ Module.gate() remains authoritative for Export button enablement.

import initRustWasm, {
  to_display,
  to_millimeters,
  export_units_pass,
  mesh_volume_mm3,
  evaluate_rust_gate,
} from './dist/cadcam_rust_gate.js';

let rustReady = false;
let initPromise = null;

export async function initRustGate(wasmInput) {
  if (rustReady) {
    return true;
  }
  if (!initPromise) {
    initPromise = (async () => {
      let target = wasmInput;
      if (!target) {
        const metaUrl = new URL(import.meta.url);
        target = new URL('./dist/cadcam_rust_gate_bg.wasm' + (metaUrl.search || ''), metaUrl);
      }
      if (target instanceof URL && target.protocol === 'file:') {
        const fs = await import('node:fs/promises');
        target = await fs.readFile(target);
      }
      await initRustWasm({ module_or_path: target });
      rustReady = true;
      return true;
    })();
  }
  return initPromise;
}

export function isRustGateReady() {
  return rustReady;
}

export {
  to_display,
  to_millimeters,
  export_units_pass,
  mesh_volume_mm3,
  evaluate_rust_gate,
};

export const toDisplay = to_display;
export const toMillimeters = to_millimeters;
export const exportUnitsPass = export_units_pass;
export const meshVolumeMm3 = mesh_volume_mm3;
export const evaluateRustGate = evaluate_rust_gate;

export function flattenVertices(input) {
  if (!input) {
    return new Float64Array(0);
  }
  if (input instanceof Float64Array) {
    return input;
  }
  if (ArrayBuffer.isView(input)) {
    return Float64Array.from(input);
  }
  if (Array.isArray(input)) {
    if (input.length === 0) {
      return new Float64Array(0);
    }
    if (Array.isArray(input[0])) {
      const out = new Float64Array(input.length * 3);
      for (let i = 0; i < input.length; i += 1) {
        const v = input[i] || [0, 0, 0];
        out[i * 3] = Number(v[0]) || 0;
        out[i * 3 + 1] = Number(v[1]) || 0;
        out[i * 3 + 2] = Number(v[2]) || 0;
      }
      return out;
    }
    return Float64Array.from(input, (n) => Number(n) || 0);
  }
  return new Float64Array(0);
}

export function flattenTriangles(input) {
  if (!input) {
    return new Uint32Array(0);
  }
  if (input instanceof Uint32Array) {
    return input;
  }
  if (ArrayBuffer.isView(input)) {
    return Uint32Array.from(input);
  }
  if (Array.isArray(input)) {
    if (input.length === 0) {
      return new Uint32Array(0);
    }
    if (Array.isArray(input[0])) {
      const out = new Uint32Array(input.length * 3);
      for (let i = 0; i < input.length; i += 1) {
        const tri = input[i] || [0, 0, 0];
        out[i * 3] = Number(tri[0]) >>> 0;
        out[i * 3 + 1] = Number(tri[1]) >>> 0;
        out[i * 3 + 2] = Number(tri[2]) >>> 0;
      }
      return out;
    }
    return Uint32Array.from(input, (n) => Number(n) >>> 0);
  }
  return new Uint32Array(0);
}

export function evalRustGateMesh(meshLike, cppReport) {
  const spec = meshLike || {};
  const rawVerts = spec.positions !== undefined
    ? spec.positions
    : (spec.vertices_xyz !== undefined ? spec.vertices_xyz : spec.vertices);
  const rawTris = spec.indices !== undefined
    ? spec.indices
    : (spec.triangles_ijk !== undefined ? spec.triangles_ijk : spec.triangles);

  const vertices = flattenVertices(rawVerts);
  const triangles = flattenTriangles(rawTris);
  const storage = typeof spec.storage === 'string'
    ? spec.storage
    : (typeof spec.exportUnit === 'string' ? spec.exportUnit : 'millimeter');
  const threemf = typeof spec.threemf === 'string' ? spec.threemf : storage;
  const stl = typeof spec.stl === 'string' ? spec.stl : storage;

  if (!rustReady) {
    return {
      ready: false,
      units_pass: false,
      mesh_pass: false,
      export_allowed: false,
      block_reason: 'Rust gate WASM not initialized.',
      units_message: '',
      mesh_message: '',
      volume_mm3: 0,
      unitsPass: false,
      meshPass: false,
      exportAllowed: false,
      blockReason: 'Rust gate WASM not initialized.',
      unitsMessage: '',
      meshMessage: '',
      volumeMm3: 0,
      matchesCpp: false,
      statusText: 'RustGate: PENDING',
    };
  }

  const res = evaluate_rust_gate(vertices, triangles, storage, threemf, stl);
  const unitsPass = !!res.units_pass;
  const meshPass = !!res.mesh_pass;
  const exportAllowed = !!res.export_allowed;
  const blockReason = String(res.block_reason || '');
  const unitsMessage = String(res.units_message || '');
  const meshMessage = String(res.mesh_message || '');
  const volumeMm3 = Number(res.volume_mm3);

  let matchesCpp = true;
  if (cppReport && typeof cppReport === 'object') {
    const cppAllowed = !!cppReport.exportAllowed;
    const cppReason = String(cppReport.blockReason || '');
    matchesCpp = (exportAllowed === cppAllowed) && (blockReason === cppReason);
  }

  const shortReason = blockReason || meshMessage || unitsMessage;
  const statusText = (exportAllowed ? 'RustGate: PASS' : 'RustGate: FAIL')
    + (shortReason ? ' — ' + shortReason : '');

  return {
    ready: true,
    units_pass: unitsPass,
    mesh_pass: meshPass,
    export_allowed: exportAllowed,
    block_reason: blockReason,
    units_message: unitsMessage,
    mesh_message: meshMessage,
    volume_mm3: volumeMm3,
    unitsPass,
    meshPass,
    exportAllowed,
    blockReason,
    unitsMessage,
    meshMessage,
    volumeMm3,
    matchesCpp,
    statusText,
  };
}
