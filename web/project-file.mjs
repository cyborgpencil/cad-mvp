// Project file (.cadmvp) and the BREP text binding.
//
// libcascade 3.1.0 exports BRepTools.Write and BRepTools.Read.
// The linked Write symbol is the file-path overload
// (TopoDS_Shape, const char*, withTriangles, withNormals, version, progress).
// The std::ostream / std::istream overloads are not in the symbol map, and
// cadcam.wasm does not link OCCT, so a std::stringstream wrapper cannot be
// compiled here. This module calls the exported file-path methods, copies
// the BREP text out, and deletes the temporary file. Erik review: this is
// the binding the prebuild can actually call.

import { checkOcctShape } from './occt-gate.mjs';

// Team choices, 2026-10-22. Not Erik measurements.
export const PROJECT_VERSION = 1;
export const PROJECT_UNITS = 'mm';
export const PROJECT_EXTENSION = '.cadmvp';
export const DEFAULT_MATERIAL = 'default';
export const BREP_WITH_TRIANGLES = true;
export const BREP_WITH_NORMALS = false;

export const ERR_EMPTY = 'This file is empty. The model was not changed.';
export const ERR_READ = 'This file could not be read. The model was not changed.';
export const ERR_UNITS = 'This file is not in millimetres. The model was not changed.';
export const ERR_VERSION = 'This file version is not supported. The model was not changed.';
export const ERR_SHAPE = 'A part failed the shape check. The model was not changed.';
export const ERR_SAVE = 'The project could not be saved.';

let tempSeq = 0;

function tempPath() {
  tempSeq += 1;
  return '/cadmvp-brep-' + String(tempSeq) + '.brep';
}

function unlinkQuiet(oc, path) {
  try {
    if (oc && oc.FS && typeof oc.FS.unlink === 'function') oc.FS.unlink(path);
  } catch (_err) {
    // The temporary file is already gone.
  }
}

function release(shape) {
  if (!shape || typeof shape.delete !== 'function') return;
  try { shape.delete(); } catch (_err) { /* already released */ }
}

function axisDir(axis) {
  if (axis === 'X') return [1, 0, 0];
  if (axis === 'Y') return [0, 1, 0];
  return [0, 0, 1];
}

function finiteNumber(value) {
  const n = Number(value);
  return Number.isFinite(n) ? n : null;
}

function cloneData(value) {
  if (value === null || value === undefined) return null;
  return JSON.parse(JSON.stringify(value));
}

export function writeBrepText(oc, shape) {
  if (!oc || !oc.BRepTools || typeof oc.BRepTools.Write !== 'function' || !oc.FS) {
    return { ok: false, text: '', error: ERR_SAVE };
  }
  if (!shape || (typeof shape.IsNull === 'function' && shape.IsNull())) {
    return { ok: false, text: '', error: ERR_SAVE };
  }
  const path = tempPath();
  let progress = null;
  try {
    progress = new oc.Message_ProgressRange();
    const version = oc.TopTools_FormatVersion.TopTools_FormatVersion_CURRENT;
    const wrote = oc.BRepTools.Write(
      shape,
      path,
      BREP_WITH_TRIANGLES,
      BREP_WITH_NORMALS,
      version,
      progress
    );
    if (!wrote) return { ok: false, text: '', error: ERR_SAVE };
    const text = oc.FS.readFile(path, { encoding: 'utf8' });
    if (typeof text !== 'string' || text.indexOf('CASCADE Topology') === -1) {
      return { ok: false, text: '', error: ERR_SAVE };
    }
    return { ok: true, text: text, error: '' };
  } catch (_err) {
    return { ok: false, text: '', error: ERR_SAVE };
  } finally {
    if (progress) release(progress);
    unlinkQuiet(oc, path);
  }
}

export function readBrepText(oc, text) {
  if (!oc || !oc.BRepTools || typeof oc.BRepTools.Read !== 'function' || !oc.FS) {
    return { ok: false, shape: null, error: ERR_SHAPE };
  }
  if (typeof text !== 'string' || text.trim() === '') {
    return { ok: false, shape: null, error: ERR_SHAPE };
  }
  const path = tempPath();
  let progress = null;
  let builder = null;
  let shape = null;
  try {
    oc.FS.writeFile(path, text);
    progress = new oc.Message_ProgressRange();
    builder = new oc.BRep_Builder();
    shape = new oc.TopoDS_Shape();
    const read = oc.BRepTools.Read(shape, path, builder, progress);
    if (!read || (typeof shape.IsNull === 'function' && shape.IsNull())) {
      release(shape);
      return { ok: false, shape: null, error: ERR_SHAPE };
    }
    const owned = shape;
    shape = null;
    return { ok: true, shape: owned, error: '' };
  } catch (_err) {
    release(shape);
    return { ok: false, shape: null, error: ERR_SHAPE };
  } finally {
    release(progress);
    release(builder);
    unlinkQuiet(oc, path);
  }
}

export function shapeVolumeMm3(oc, shape) {
  const props = new oc.GProp_GProps();
  try {
    oc.BRepGProp.VolumeProperties(shape, props, true, false, false);
    return props.Mass();
  } finally {
    release(props);
  }
}

// BRepBndLib::AddOptimal, useTriangulation false, useShapeTolerance false.
// Team choice, 2026-10-22: the box is the exact geometry, not the mesh pad.
export function optimalBounds(oc, shape) {
  const box = new oc.Bnd_Box();
  try {
    oc.BRepBndLib.AddOptimal(shape, box, false, false);
    return {
      xmin: box.GetXMin(),
      ymin: box.GetYMin(),
      zmin: box.GetZMin(),
      xmax: box.GetXMax(),
      ymax: box.GetYMax(),
      zmax: box.GetZMax(),
    };
  } finally {
    release(box);
  }
}

export function measureShape(oc, shape) {
  return {
    volumeMm3: shapeVolumeMm3(oc, shape),
    bounds: optimalBounds(oc, shape),
  };
}

function placementFromParams(params) {
  const src = params || {};
  return {
    x: finiteNumber(src.cx) === null ? 0 : finiteNumber(src.cx),
    y: finiteNumber(src.cy) === null ? 0 : finiteNumber(src.cy),
    z: finiteNumber(src.cz) === null ? 0 : finiteNumber(src.cz),
  };
}

export function partFromBody(oc, body) {
  const params = body && body.params ? body.params : null;
  const written = writeBrepText(oc, body && body.shape);
  if (!written.ok) return { ok: false, error: written.error, part: null };
  const kind = body && body.kind ? String(body.kind) : '';
  const primitive = kind && params
    ? { kind: kind, parameters: cloneData(params) }
    : null;
  let features = [];
  if (body && Array.isArray(body.features)) {
    try {
      features = cloneData(body.features) || [];
    } catch (_err) {
      return { ok: false, error: ERR_SAVE, part: null };
    }
  }
  const material = body && typeof body.material === 'string' && body.material
    ? body.material
    : DEFAULT_MATERIAL;
  return {
    ok: true,
    error: '',
    part: {
      name: body && body.name ? String(body.name) : 'Part',
      placement: placementFromParams(params),
      material: material,
      primitive: primitive,
      features: features,
      shape: written.text,
    },
  };
}

export function documentFromBodies(oc, bodies) {
  const list = Array.isArray(bodies) ? bodies : [];
  const parts = [];
  for (let i = 0; i < list.length; i += 1) {
    const made = partFromBody(oc, list[i]);
    if (!made.ok) return { ok: false, error: made.error, doc: null, text: '' };
    parts.push(made.part);
  }
  const doc = {
    units: PROJECT_UNITS,
    version: PROJECT_VERSION,
    parts: parts,
  };
  return { ok: true, error: '', doc: doc, text: JSON.stringify(doc) };
}

function checkPart(raw) {
  if (!raw || typeof raw !== 'object' || Array.isArray(raw)) return null;
  if (typeof raw.name !== 'string' || !raw.name) return null;
  const place = raw.placement;
  if (!place || typeof place !== 'object') return null;
  if (finiteNumber(place.x) === null || finiteNumber(place.y) === null || finiteNumber(place.z) === null) {
    return null;
  }
  if (typeof raw.material !== 'string') return null;
  if (!Array.isArray(raw.features)) return null;
  if (typeof raw.shape !== 'string' || raw.shape.indexOf('CASCADE Topology') === -1) return null;
  let primitive = null;
  if (raw.primitive !== null && raw.primitive !== undefined) {
    if (!raw.primitive || typeof raw.primitive !== 'object' || Array.isArray(raw.primitive)) return null;
    if (typeof raw.primitive.kind !== 'string' || !raw.primitive.kind) return null;
    if (!raw.primitive.parameters || typeof raw.primitive.parameters !== 'object') return null;
    primitive = {
      kind: raw.primitive.kind,
      parameters: cloneData(raw.primitive.parameters),
    };
  }
  return {
    name: raw.name,
    placement: {
      x: finiteNumber(place.x),
      y: finiteNumber(place.y),
      z: finiteNumber(place.z),
    },
    material: raw.material,
    primitive: primitive,
    features: cloneData(raw.features) || [],
    shape: raw.shape,
  };
}

export function parseProject(text) {
  if (typeof text !== 'string' || text.trim() === '') {
    return { ok: false, error: ERR_EMPTY, doc: null };
  }
  let data = null;
  try {
    data = JSON.parse(text);
  } catch (_err) {
    return { ok: false, error: ERR_READ, doc: null };
  }
  if (!data || typeof data !== 'object' || Array.isArray(data)) {
    return { ok: false, error: ERR_READ, doc: null };
  }
  if (!Object.prototype.hasOwnProperty.call(data, 'units') || data.units !== PROJECT_UNITS) {
    return { ok: false, error: ERR_UNITS, doc: null };
  }
  if (data.version !== PROJECT_VERSION) {
    return { ok: false, error: ERR_VERSION, doc: null };
  }
  if (!Array.isArray(data.parts)) {
    return { ok: false, error: ERR_READ, doc: null };
  }
  const parts = [];
  for (let i = 0; i < data.parts.length; i += 1) {
    const part = checkPart(data.parts[i]);
    if (!part) return { ok: false, error: ERR_READ, doc: null };
    parts.push(part);
  }
  return {
    ok: true,
    error: '',
    doc: { units: PROJECT_UNITS, version: PROJECT_VERSION, parts: parts },
  };
}

export function rebuildShape(oc, part, primApi, opsApi) {
  const prim = part && part.primitive;
  if (!prim || !prim.parameters || !primApi || !opsApi) return null;
  if (Array.isArray(part.features) && part.features.length) return null;
  const kind = prim.kind;
  const placed = Object.assign({}, prim.parameters, {
    cx: part.placement.x,
    cy: part.placement.y,
    cz: part.placement.z,
  });
  let shape = null;
  let params = null;
  try {
    if (kind === 'cylinder') {
      params = primApi.normalizeCylinder(placed);
      const dir = axisDir(params.axis);
      shape = opsApi.makeCylinderSolid(oc, params.radius, params.height, [
        params.cx - dir[0] * params.height / 2,
        params.cy - dir[1] * params.height / 2,
        params.cz - dir[2] * params.height / 2,
      ], dir);
    } else if (kind === 'disc') {
      params = primApi.normalizeDisc(placed);
      const dir = axisDir(params.axis);
      const height = params.thickness;
      shape = opsApi.makeCylinderSolid(oc, params.diameter / 2, height, [
        params.cx - dir[0] * height / 2,
        params.cy - dir[1] * height / 2,
        params.cz - dir[2] * height / 2,
      ], dir);
    } else if (kind === 'box') {
      params = primApi.normalizeBox(placed);
      shape = opsApi.makeBoxSolid(oc, params.sx, params.sy, params.sz, [
        params.cx - params.sx / 2,
        params.cy - params.sy / 2,
        params.cz - params.sz / 2,
      ]);
    } else {
      return null;
    }
    if (!shape || !params) return null;
    const rot = {
      rxDeg: params.rx || 0,
      ryDeg: params.ry || 0,
      rzDeg: params.rz || 0,
      origin: [params.cx, params.cy, params.cz],
    };
    if (rot.rxDeg || rot.ryDeg || rot.rzDeg) {
      const rotated = opsApi.transformShape(oc, shape, rot);
      if (!rotated.ok || !rotated.shape) {
        release(shape);
        return null;
      }
      release(shape);
      shape = rotated.shape;
    }
    return { shape: shape, kind: kind, params: params };
  } catch (_err) {
    release(shape);
    return null;
  }
}

function dropParts(parts) {
  for (let i = 0; i < parts.length; i += 1) release(parts[i].shape);
}

export function loadShapes(oc, doc, primApi, opsApi) {
  const built = [];
  function fail(error) {
    dropParts(built);
    return { ok: false, error: error, parts: [] };
  }
  const list = doc && Array.isArray(doc.parts) ? doc.parts : null;
  if (!list) return fail(ERR_READ);
  for (let i = 0; i < list.length; i += 1) {
    const part = list[i];
    let shape = null;
    let kind = part.primitive && part.primitive.kind ? part.primitive.kind : 'brep';
    let params = part.primitive ? part.primitive.parameters : null;
    let source = '';
    const rebuilt = rebuildShape(oc, part, primApi, opsApi);
    if (rebuilt && rebuilt.shape) {
      const gate = checkOcctShape(oc, rebuilt.shape);
      if (gate.pass === true) {
        shape = rebuilt.shape;
        kind = rebuilt.kind;
        params = rebuilt.params;
        source = 'parameters';
      } else {
        release(rebuilt.shape);
      }
    }
    if (!shape) {
      const read = readBrepText(oc, part.shape);
      if (!read.ok || !read.shape) return fail(ERR_SHAPE);
      const gate = checkOcctShape(oc, read.shape);
      if (gate.pass !== true) {
        release(read.shape);
        return fail(ERR_SHAPE);
      }
      shape = read.shape;
      source = 'brep';
    }
    built.push({
      shape: shape,
      kind: kind,
      params: params,
      source: source,
      name: part.name,
      material: part.material,
      features: part.features,
      placement: part.placement,
    });
  }
  return { ok: true, error: '', parts: built };
}
