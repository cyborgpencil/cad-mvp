// Flat parts list. Each part owns one solid. Placement is a translation in
// millimetres, stored as a TopLoc_Location and applied only when Combine
// fuses the parts and when a 3MF is written. No mates. No shared instances.
//
// Team choices, 2026-10-22, not Erik measurements:
//   materials PLA, PETG, TPU; missing or "default" reads as PLA
//   display colors below (3MF core <base displaycolor>)
//   export mesh linear deflection 0.01 mm so a placed box stays inside 0.01 mm
//   a fused part keeps the first selected part's name and that shared material
//   the fused solid is already in place, so its placement is identity
// The .cadmvp fields are unchanged. This module does not check watertight.

import { checkOcctShape } from './occt-gate.mjs';
import { copyShape, fuseShapes, optimalBounds, solidVolumeMm3 } from './occt-ops.mjs';

export const MATERIALS = Object.freeze(['PLA', 'PETG', 'TPU']);
export const DEFAULT_PART_MATERIAL = 'PLA';

// Team choice for the core-spec base color. Not a filament measurement.
export const MATERIAL_COLOR = Object.freeze({
  PLA: '#F4F4F4',
  PETG: '#B9D6F2',
  TPU: '#E7C36A',
});

export const EXPORT_MESH_DEFLECTION_MM = 0.01;
export const EXPORT_MESH_ANGLE_RAD = 0.2;
export const VOLUME_TOL_MM3 = 0.01;
export const BOUNDS_TOL_MM = 0.01;
// Weld quantum for 3MF object vertices. Team choice for this export path.
export const VERTEX_WELD_MM = 1e-6;

export const ERR_NEED = 'Select two or more parts. The model was not changed.';
export const ERR_MIXED = 'These parts use different materials. The model was not changed.';
export const ERR_COMBINE = 'Combine failed the shape check. The model was not changed.';
export const ERR_UNITS = 'This export is not in millimetres. The file was not written.';
export const ERR_EXPORT = 'The 3MF could not be written.';

function release(obj) {
  if (!obj || typeof obj.delete !== 'function') return;
  try { obj.delete(); } catch (_err) { /* already released */ }
}

function fail(error) {
  return {
    ok: false,
    error: error,
    shape: null,
    material: '',
    placement: null,
    name: '',
    volumeMm3: 0,
    valid: false,
  };
}

export function placementOf(part) {
  const src = part && part.placement ? part.placement : null;
  const x = src ? Number(src.x) : 0;
  const y = src ? Number(src.y) : 0;
  const z = src ? Number(src.z) : 0;
  return {
    x: Number.isFinite(x) ? x : 0,
    y: Number.isFinite(y) ? y : 0,
    z: Number.isFinite(z) ? z : 0,
  };
}

export function materialTag(part) {
  const raw = part && typeof part.material === 'string' ? part.material : '';
  if (raw === 'PLA' || raw === 'PETG' || raw === 'TPU') return raw;
  if (!raw || raw === 'default') return DEFAULT_PART_MATERIAL;
  return raw;
}

export function makeLocation(oc, placement) {
  const place = placementOf({ placement: placement });
  const vec = new oc.gp_Vec(place.x, place.y, place.z);
  const trsf = new oc.gp_Trsf();
  try {
    trsf.SetTranslation(vec);
    return new oc.TopLoc_Location(trsf);
  } finally {
    release(vec);
    release(trsf);
  }
}

export function locationTranslation(location) {
  if (!location || typeof location.Transformation !== 'function') return null;
  let trsf = null;
  let vec = null;
  try {
    trsf = location.Transformation();
    vec = trsf.TranslationPart();
    return { x: vec.X(), y: vec.Y(), z: vec.Z() };
  } catch (_err) {
    return null;
  } finally {
    release(vec);
    release(trsf);
  }
}

// Deep copy with the placement applied. The caller's solid is not moved.
// Identity placement is still a deep copy, so parts never share a shape.
export function placedCopy(oc, shape, placement) {
  if (!oc || !shape) return { ok: false, shape: null, error: ERR_COMBINE };
  const place = placementOf({ placement: placement });
  let loc = null;
  try {
    loc = makeLocation(oc, place);
    const read = locationTranslation(loc);
    if (!read
      || Math.abs(read.x - place.x) > 1e-9
      || Math.abs(read.y - place.y) > 1e-9
      || Math.abs(read.z - place.z) > 1e-9) {
      return { ok: false, shape: null, error: ERR_COMBINE };
    }
    if (!place.x && !place.y && !place.z) {
      const copied = copyShape(oc, shape);
      if (!copied) return { ok: false, shape: null, error: ERR_COMBINE };
      return { ok: true, shape: copied, error: '' };
    }
    if (typeof shape.Located !== 'function') {
      return { ok: false, shape: null, error: ERR_COMBINE };
    }
    const located = shape.Located(loc);
    if (!located || (typeof located.IsNull === 'function' && located.IsNull())) {
      release(located);
      return { ok: false, shape: null, error: ERR_COMBINE };
    }
    const copied = copyShape(oc, located);
    release(located);
    if (!copied) return { ok: false, shape: null, error: ERR_COMBINE };
    return { ok: true, shape: copied, error: '' };
  } catch (_err) {
    return { ok: false, shape: null, error: ERR_COMBINE };
  } finally {
    release(loc);
  }
}

// A move of a local part changes the placement only. The stored solid is the
// same object, still in its own coordinates.
export function moveLocalPart(part, dx, dy, dz) {
  if (!part || part.shapeLocal !== true || !part.shape) {
    return { ok: false, placement: null, shape: part ? part.shape : null };
  }
  const place = placementOf(part);
  return {
    ok: true,
    placement: {
      x: place.x + (Number(dx) || 0),
      y: place.y + (Number(dy) || 0),
      z: place.z + (Number(dz) || 0),
    },
    shape: part.shape,
  };
}

function placementFor(part) {
  if (part && part.shapeLocal === true) return placementOf(part);
  return { x: 0, y: 0, z: 0 };
}

export function combineParts(oc, parts, options) {
  const list = Array.isArray(parts) ? parts.filter(function (part) { return part && part.shape; }) : [];
  if (options && options.forceFail === true) return fail(ERR_COMBINE);
  if (list.length < 2) return fail(ERR_NEED);
  const tags = list.map(materialTag);
  for (let i = 1; i < tags.length; i += 1) {
    if (tags[i] !== tags[0]) return fail(ERR_MIXED);
  }
  const held = [];
  function dropHeld() {
    while (held.length) release(held.pop());
  }
  try {
    for (let i = 0; i < list.length; i += 1) {
      const copied = placedCopy(oc, list[i].shape, placementFor(list[i]));
      if (!copied.ok || !copied.shape) {
        dropHeld();
        return fail(ERR_COMBINE);
      }
      held.push(copied.shape);
    }
    let acc = held.shift();
    while (held.length) {
      const next = held.shift();
      const fused = fuseShapes(oc, acc, next);
      release(acc);
      release(next);
      acc = null;
      if (!fused || !fused.ok || !fused.shape) {
        if (fused && fused.shape) release(fused.shape);
        dropHeld();
        return fail(ERR_COMBINE);
      }
      acc = fused.shape;
    }
    const gate = checkOcctShape(oc, acc);
    if (!gate || gate.valid !== true) {
      release(acc);
      return fail(ERR_COMBINE);
    }
    return {
      ok: true,
      error: '',
      shape: acc,
      material: tags[0],
      placement: { x: 0, y: 0, z: 0 },
      name: list[0].name ? String(list[0].name) : 'Part',
      volumeMm3: solidVolumeMm3(oc, acc),
      valid: true,
    };
  } catch (_err) {
    dropHeld();
    return fail(ERR_COMBINE);
  }
}

function track(trash, obj) {
  if (obj && typeof obj.delete === 'function') trash.push(obj);
  return obj;
}

function weldKey(x, y, z, quantumMm) {
  const q = quantumMm > 0 ? quantumMm : VERTEX_WELD_MM;
  return Math.round(x / q) + ',' + Math.round(y / q) + ',' + Math.round(z / q);
}

function triangleArea2(a, b, c) {
  const ux = b[0] - a[0];
  const uy = b[1] - a[1];
  const uz = b[2] - a[2];
  const vx = c[0] - a[0];
  const vy = c[1] - a[1];
  const vz = c[2] - a[2];
  const cx = uy * vz - uz * vy;
  const cy = uz * vx - ux * vz;
  const cz = ux * vy - uy * vx;
  return cx * cx + cy * cy + cz * cz;
}

// Weld vertices that round to the same millimetre quantum, remap triangles,
// and drop degenerates. Does not require a watertight mesh.
export function weldMesh(vertices, triangles, quantumMm) {
  const q = quantumMm > 0 ? quantumMm : VERTEX_WELD_MM;
  const list = vertices || [];
  const tris = triangles || [];
  const map = new Map();
  const outV = [];
  const remap = new Array(list.length);
  for (let i = 0; i < list.length; i += 1) {
    const p = list[i];
    const key = weldKey(p[0], p[1], p[2], q);
    if (map.has(key)) {
      remap[i] = map.get(key);
    } else {
      remap[i] = outV.length;
      map.set(key, outV.length);
      outV.push([p[0], p[1], p[2]]);
    }
  }
  const outT = [];
  for (let i = 0; i < tris.length; i += 1) {
    const tri = tris[i];
    const a = remap[tri[0]];
    const b = remap[tri[1]];
    const c = remap[tri[2]];
    if (a === undefined || b === undefined || c === undefined) continue;
    if (a === b || b === c || a === c) continue;
    if (triangleArea2(outV[a], outV[b], outV[c]) <= 0) continue;
    outT.push([a, b, c]);
  }
  return { vertices: outV, triangles: outT };
}

export function meshHasDuplicateVertices(vertices, quantumMm) {
  const q = quantumMm > 0 ? quantumMm : VERTEX_WELD_MM;
  const seen = new Set();
  const list = vertices || [];
  for (let i = 0; i < list.length; i += 1) {
    const p = list[i];
    const key = weldKey(p[0], p[1], p[2], q);
    if (seen.has(key)) return true;
    seen.add(key);
  }
  return false;
}

export function meshSignedVolumeMm3(vertices, triangles) {
  const list = vertices || [];
  const tris = triangles || [];
  let sum = 0;
  for (let i = 0; i < tris.length; i += 1) {
    const tri = tris[i];
    const a = list[tri[0]];
    const b = list[tri[1]];
    const c = list[tri[2]];
    if (!a || !b || !c) continue;
    const cx = b[1] * c[2] - b[2] * c[1];
    const cy = b[2] * c[0] - b[0] * c[2];
    const cz = b[0] * c[1] - b[1] * c[0];
    sum += a[0] * cx + a[1] * cy + a[2] * cz;
  }
  return sum / 6;
}

// True when no directed edge is used twice. Does not require every edge to
// be used twice (that would be a watertight check).
export function meshHasConsistentWinding(vertices, triangles) {
  const tris = triangles || [];
  const directed = new Map();
  for (let i = 0; i < tris.length; i += 1) {
    const tri = tris[i];
    for (let k = 0; k < 3; k += 1) {
      const from = tri[k];
      const to = tri[(k + 1) % 3];
      const key = from + '>' + to;
      if (directed.has(key)) return false;
      directed.set(key, 1);
    }
  }
  return meshSignedVolumeMm3(vertices, triangles) > 0;
}

// Single-body print pose. Same rule as src/export/bed_orient.cpp:
// 24 proper axis-aligned rotations, zmin at 0, lowest part, then the larger
// planar face on the bed, then the longer X extent. Identity stays when it
// already wins. Multi-body exports do not call this.
const BED_NORMAL_DOT = 0.999;
const BED_PLANE_MM = 0.05;

export function axisAlignedRotations() {
  const perms = [
    [0, 1, 2],
    [0, 2, 1],
    [1, 0, 2],
    [1, 2, 0],
    [2, 0, 1],
    [2, 1, 0],
  ];
  const signOrder = [1, -1];
  const out = [];
  for (let sa = 0; sa < 2; sa += 1) {
    for (let sb = 0; sb < 2; sb += 1) {
      for (let sc = 0; sc < 2; sc += 1) {
        const s = [signOrder[sa], signOrder[sb], signOrder[sc]];
        for (let p = 0; p < perms.length; p += 1) {
          const perm = perms[p];
          const m = [0, 0, 0, 0, 0, 0, 0, 0, 0];
          for (let row = 0; row < 3; row += 1) m[row * 3 + perm[row]] = s[row];
          const det = m[0] * (m[4] * m[8] - m[5] * m[7])
            - m[1] * (m[3] * m[8] - m[5] * m[6])
            + m[2] * (m[3] * m[7] - m[4] * m[6]);
          if (det === 1) out.push(m);
        }
      }
    }
  }
  return out;
}

function triGeom(a, b, c) {
  const ux = b[0] - a[0];
  const uy = b[1] - a[1];
  const uz = b[2] - a[2];
  const vx = c[0] - a[0];
  const vy = c[1] - a[1];
  const vz = c[2] - a[2];
  const cx = uy * vz - uz * vy;
  const cy = uz * vx - ux * vz;
  const cz = ux * vy - uy * vx;
  const len = Math.hypot(cx, cy, cz);
  if (!(len > 1e-12)) return null;
  return {
    n: [cx / len, cy / len, cz / len],
    area: len * 0.5,
    offset: (cx * a[0] + cy * a[1] + cz * a[2]) / len,
    zmin: Math.min(a[2], b[2], c[2]),
    zmax: Math.max(a[2], b[2], c[2]),
  };
}

export function meshPlanarFaces(vertices, triangles) {
  const faces = [];
  const verts = vertices || [];
  const tris = triangles || [];
  for (let t = 0; t < tris.length; t += 1) {
    const tri = tris[t];
    const a = verts[tri[0]];
    const b = verts[tri[1]];
    const c = verts[tri[2]];
    if (!a || !b || !c) continue;
    const geom = triGeom(a, b, c);
    if (!geom) continue;
    let found = null;
    for (let i = 0; i < faces.length; i += 1) {
      const face = faces[i];
      const dot = face.normal[0] * geom.n[0] + face.normal[1] * geom.n[1] + face.normal[2] * geom.n[2];
      if (dot >= BED_NORMAL_DOT && Math.abs(face.offset - geom.offset) <= BED_PLANE_MM) {
        found = face;
        break;
      }
    }
    if (!found) {
      found = {
        normal: geom.n,
        offset: geom.offset,
        area: geom.area,
        zMin: geom.zmin,
        zMax: geom.zmax,
      };
      faces.push(found);
    } else {
      found.area += geom.area;
      if (geom.zmin < found.zMin) found.zMin = geom.zmin;
      if (geom.zmax > found.zMax) found.zMax = geom.zmax;
    }
  }
  return faces;
}

function poseScore(vertices, triangles, index, zShift) {
  const bounds = meshBounds(vertices);
  const faces = meshPlanarFaces(vertices, triangles);
  let bed = 0;
  let floating = 0;
  for (let i = 0; i < faces.length; i += 1) {
    const face = faces[i];
    const down = face.normal[2] <= -BED_NORMAL_DOT;
    const onBed = face.zMax <= BED_PLANE_MM && face.zMin <= 1e-4;
    if (down && onBed && face.area > bed) bed = face.area;
    if (down && face.zMin > BED_PLANE_MM) floating += face.area;
  }
  return {
    height: bounds ? bounds.zmax - bounds.zmin : 0,
    bed: bed,
    floating: floating,
    dx: bounds ? bounds.xmax - bounds.xmin : 0,
    index: index,
    zShift: zShift,
  };
}

function poseBetter(candidate, current) {
  if (Math.abs(candidate.height - current.height) > BED_PLANE_MM) return candidate.height < current.height;
  if (Math.abs(candidate.bed - current.bed) > 1e-3) return candidate.bed > current.bed;
  if (Math.abs(candidate.floating - current.floating) > 1e-3) return candidate.floating < current.floating;
  if (Math.abs(candidate.dx - current.dx) > BED_PLANE_MM) return candidate.dx > current.dx;
  return candidate.index < current.index;
}

function applyRotation(vertices, m) {
  const posed = [];
  let zmin = Infinity;
  for (let i = 0; i < vertices.length; i += 1) {
    const p = vertices[i];
    const next = [
      m[0] * p[0] + m[1] * p[1] + m[2] * p[2],
      m[3] * p[0] + m[4] * p[1] + m[5] * p[2],
      m[6] * p[0] + m[7] * p[1] + m[8] * p[2],
    ];
    if (next[2] < zmin) zmin = next[2];
    posed.push(next);
  }
  const shift = Number.isFinite(zmin) ? zmin : 0;
  if (Math.abs(shift) > 1e-12) {
    for (let i = 0; i < posed.length; i += 1) posed[i][2] -= shift;
  }
  return { vertices: posed, zShift: shift };
}

export function orientMeshFlatOnBed(vertices, triangles) {
  const list = vertices || [];
  const tris = triangles || [];
  if (!list.length || !tris.length) {
    return { vertices: list, triangles: tris, turned: false };
  }
  const rotations = axisAlignedRotations();
  let best = null;
  for (let i = 0; i < rotations.length; i += 1) {
    const posed = applyRotation(list, rotations[i]);
    const score = poseScore(posed.vertices, tris, i, posed.zShift);
    if (!best || poseBetter(score, best.score)) {
      best = { score: score, vertices: posed.vertices };
    }
  }
  if (!best || (best.score.index === 0 && Math.abs(best.score.zShift) <= 1e-12)) {
    return { vertices: list, triangles: tris, turned: false };
  }
  return {
    vertices: best.vertices,
    triangles: tris,
    turned: best.score.index !== 0,
  };
}

export function meshBounds(vertices) {
  const list = vertices || [];
  if (!list.length) return null;
  let xmin = Infinity;
  let ymin = Infinity;
  let zmin = Infinity;
  let xmax = -Infinity;
  let ymax = -Infinity;
  let zmax = -Infinity;
  for (let i = 0; i < list.length; i += 1) {
    const p = list[i];
    if (p[0] < xmin) xmin = p[0];
    if (p[1] < ymin) ymin = p[1];
    if (p[2] < zmin) zmin = p[2];
    if (p[0] > xmax) xmax = p[0];
    if (p[1] > ymax) ymax = p[1];
    if (p[2] > zmax) zmax = p[2];
  }
  return { xmin: xmin, ymin: ymin, zmin: zmin, xmax: xmax, ymax: ymax, zmax: zmax };
}

function faceIsReversed(oc, face) {
  if (!face || typeof face.Orientation !== 'function') return false;
  let ori = null;
  try { ori = face.Orientation(); } catch (_err) { ori = null; }
  if (ori === 'TopAbs_REVERSED') return true;
  const table = oc && oc.TopAbs_Orientation ? oc.TopAbs_Orientation : null;
  return !!(table && ori === table.TopAbs_REVERSED);
}

function meshShape(oc, shape) {
  const trash = [];
  try {
    const parameters = track(trash, new oc.IMeshTools_Parameters());
    parameters.Relative = false;
    parameters.Deflection = EXPORT_MESH_DEFLECTION_MM;
    parameters.Angle = EXPORT_MESH_ANGLE_RAD;
    parameters.ControlSurfaceDeflection = true;
    parameters.InParallel = false;
    let mesher = null;
    try {
      mesher = track(trash, new oc.BRepMesh_IncrementalMesh(shape, parameters));
    } catch (_err) {
      mesher = track(trash, new oc.BRepMesh_IncrementalMesh(
        shape,
        EXPORT_MESH_DEFLECTION_MM,
        false,
        EXPORT_MESH_ANGLE_RAD,
        false
      ));
    }
    try {
      if (mesher && typeof mesher.Perform === 'function') mesher.Perform();
    } catch (_err) {
      // This build meshes inside the constructor.
    }
    const vertices = [];
    const triangles = [];
    const explorer = track(trash, new oc.TopExp_Explorer(shape, oc.TopAbs_ShapeEnum.TopAbs_FACE));
    while (explorer.More()) {
      const face = track(trash, oc.TopoDS.Face(explorer.Current()));
      const loc = track(trash, new oc.TopLoc_Location());
      let tri = null;
      try {
        tri = oc.BRep_Tool.Triangulation(face, loc, 0);
      } catch (_err) {
        tri = null;
      }
      if (tri && typeof tri.delete === 'function') trash.push(tri);
      if (tri && !(typeof tri.IsNull === 'function' && tri.IsNull()) && tri.NbNodes && tri.NbNodes() > 0) {
        const trsf = track(trash, loc.Transformation());
        const reversed = faceIsReversed(oc, face);
        const base = vertices.length;
        const nNodes = tri.NbNodes();
        for (let i = 1; i <= nNodes; i += 1) {
          const node = track(trash, tri.Node(i));
          const moved = track(trash, node.Transformed(trsf));
          vertices.push([moved.X(), moved.Y(), moved.Z()]);
        }
        const nTri = tri.NbTriangles();
        for (let i = 1; i <= nTri; i += 1) {
          const poly = track(trash, tri.Triangle(i));
          const v1 = base + poly.Value(1) - 1;
          const v2 = base + poly.Value(2) - 1;
          const v3 = base + poly.Value(3) - 1;
          // TopAbs_REVERSED faces store the triangulation in forward order.
          triangles.push(reversed ? [v1, v3, v2] : [v1, v2, v3]);
        }
      }
      explorer.Next();
    }
    return weldMesh(vertices, triangles);
  } finally {
    for (let i = trash.length - 1; i >= 0; i -= 1) release(trash[i]);
  }
}

function xmlEscape(text) {
  return String(text)
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;');
}

function xmlNum(value) {
  const n = Number(value);
  if (!Number.isFinite(n)) return '0';
  let text = n.toFixed(6);
  if (text.indexOf('.') >= 0) {
    text = text.replace(/0+$/, '').replace(/\.$/, '');
  }
  if (text === '-0') return '0';
  return text;
}

function transformAttr(placement) {
  const place = placementOf({ placement: placement });
  return '1 0 0 0 1 0 0 0 1 ' + xmlNum(place.x) + ' ' + xmlNum(place.y) + ' ' + xmlNum(place.z);
}

export function materialColor(tag) {
  if (Object.prototype.hasOwnProperty.call(MATERIAL_COLOR, tag)) return MATERIAL_COLOR[tag];
  return '#CCCCCC';
}

function colorFor(tag) {
  return materialColor(tag);
}

function modelXml(objects) {
  const tags = [];
  MATERIALS.forEach(function (tag) { tags.push(tag); });
  objects.forEach(function (obj) {
    if (tags.indexOf(obj.material) < 0) tags.push(obj.material);
  });
  let xml = '<?xml version="1.0" encoding="UTF-8"?>\n'
    + '<model unit="millimeter" xml:lang="en-US" '
    + 'xmlns="http://schemas.microsoft.com/3dmanufacturing/core/2015/02">\n'
    + ' <resources>\n'
    + '  <basematerials id="1">\n';
  for (let i = 0; i < tags.length; i += 1) {
    xml += '   <base name="' + xmlEscape(tags[i]) + '" displaycolor="' + colorFor(tags[i]) + '"/>\n';
  }
  xml += '  </basematerials>\n';
  for (let i = 0; i < objects.length; i += 1) {
    const obj = objects[i];
    const id = i + 2;
    const pindex = tags.indexOf(obj.material);
    xml += '  <object id="' + id + '" type="model" name="' + xmlEscape(obj.name) + '" pid="1" pindex="' + pindex + '">\n';
    xml += '   <mesh>\n    <vertices>\n';
    for (let v = 0; v < obj.vertices.length; v += 1) {
      const p = obj.vertices[v];
      xml += '     <vertex x="' + xmlNum(p[0]) + '" y="' + xmlNum(p[1]) + '" z="' + xmlNum(p[2]) + '"/>\n';
    }
    xml += '    </vertices>\n    <triangles>\n';
    for (let t = 0; t < obj.triangles.length; t += 1) {
      const tri = obj.triangles[t];
      xml += '     <triangle v1="' + tri[0] + '" v2="' + tri[1] + '" v3="' + tri[2] + '"/>\n';
    }
    xml += '    </triangles>\n   </mesh>\n  </object>\n';
  }
  xml += ' </resources>\n <build>\n';
  for (let i = 0; i < objects.length; i += 1) {
    xml += '  <item objectid="' + (i + 2) + '" transform="' + transformAttr(objects[i].placement) + '"/>\n';
  }
  xml += ' </build>\n</model>\n';
  return xml;
}

function crc32(text) {
  let crc = 0xffffffff;
  for (let i = 0; i < text.length; i += 1) {
    crc ^= text.charCodeAt(i);
    for (let bit = 0; bit < 8; bit += 1) {
      const mask = -(crc & 1);
      crc = (crc >>> 1) ^ (0xedb88320 & mask);
    }
  }
  return (~crc) >>> 0;
}

function pushU16(bytes, value) {
  bytes.push(value & 0xff, (value >> 8) & 0xff);
}

function pushU32(bytes, value) {
  bytes.push(value & 0xff, (value >> 8) & 0xff, (value >> 16) & 0xff, (value >>> 24) & 0xff);
}

function utf8(text) {
  return unescape(encodeURIComponent(text));
}

function zipStore(items) {
  const dosDate = (46 << 9) | (10 << 5) | 20;
  const local = [];
  const records = [];
  for (let i = 0; i < items.length; i += 1) {
    const name = utf8(items[i].name);
    const data = utf8(items[i].data);
    const crc = crc32(data);
    const offset = local.length;
    records.push({ name: name, data: data, crc: crc, offset: offset });
    pushU32(local, 0x04034b50);
    pushU16(local, 20);
    pushU16(local, 0);
    pushU16(local, 0);
    pushU16(local, 0);
    pushU16(local, dosDate);
    pushU32(local, crc);
    pushU32(local, data.length);
    pushU32(local, data.length);
    pushU16(local, name.length);
    pushU16(local, 0);
    for (let c = 0; c < name.length; c += 1) local.push(name.charCodeAt(c));
    for (let c = 0; c < data.length; c += 1) local.push(data.charCodeAt(c));
  }
  const centralOffset = local.length;
  const central = [];
  for (let i = 0; i < records.length; i += 1) {
    const item = records[i];
    pushU32(central, 0x02014b50);
    pushU16(central, 20);
    pushU16(central, 20);
    pushU16(central, 0);
    pushU16(central, 0);
    pushU16(central, 0);
    pushU16(central, dosDate);
    pushU32(central, item.crc);
    pushU32(central, item.data.length);
    pushU32(central, item.data.length);
    pushU16(central, item.name.length);
    pushU16(central, 0);
    pushU16(central, 0);
    pushU16(central, 0);
    pushU16(central, 0);
    pushU32(central, 0);
    pushU32(central, item.offset);
    for (let c = 0; c < item.name.length; c += 1) central.push(item.name.charCodeAt(c));
  }
  const end = [];
  pushU32(end, 0x06054b50);
  pushU16(end, 0);
  pushU16(end, 0);
  pushU16(end, records.length);
  pushU16(end, records.length);
  pushU32(end, central.length);
  pushU32(end, centralOffset);
  pushU16(end, 0);
  return new Uint8Array(local.concat(central, end));
}

export function exportAssembly3mf(oc, parts, options) {
  const units = options && options.units ? String(options.units) : 'mm';
  if (units !== 'mm' && units !== 'millimeter') {
    return { ok: false, bytes: null, xml: '', error: ERR_UNITS };
  }
  const list = Array.isArray(parts) ? parts : [];
  if (!oc || !list.length) return { ok: false, bytes: null, xml: '', error: ERR_EXPORT };
  const objects = [];
  try {
    for (let i = 0; i < list.length; i += 1) {
      const part = list[i];
      if (!part || !part.shape) return { ok: false, bytes: null, xml: '', error: ERR_EXPORT };
      const mesh = meshShape(oc, part.shape);
      if (!mesh.vertices.length || !mesh.triangles.length) {
        return { ok: false, bytes: null, xml: '', error: ERR_EXPORT };
      }
      let vertices = mesh.vertices;
      let placement = placementFor(part);
      const autoBed = !(options && options.autoBed === false);
      if (autoBed && list.length === 1) {
        const laid = orientMeshFlatOnBed(vertices, mesh.triangles);
        vertices = laid.vertices;
        if (laid.turned) placement = { x: 0, y: 0, z: 0 };
        else placement = { x: placement.x, y: placement.y, z: 0 };
      }
      objects.push({
        name: part.name ? String(part.name) : 'Part',
        material: materialTag(part),
        vertices: vertices,
        triangles: mesh.triangles,
        placement: placement,
      });
    }
    const xml = modelXml(objects);
    if (xml.indexOf('unit="millimeter"') < 0 || xml.indexOf('<components') >= 0) {
      return { ok: false, bytes: null, xml: '', error: ERR_EXPORT };
    }
    const types = '<?xml version="1.0" encoding="UTF-8"?>\n'
      + '<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">\n'
      + ' <Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>\n'
      + ' <Default Extension="model" ContentType="application/vnd.ms-package.3dmanufacturing-3dmodel+xml"/>\n'
      + '</Types>\n';
    const rels = '<?xml version="1.0" encoding="UTF-8"?>\n'
      + '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">\n'
      + ' <Relationship Target="/3D/3dmodel.model" Id="rel0" Type="http://schemas.microsoft.com/3dmanufacturing/2013/01/3dmodel"/>\n'
      + '</Relationships>\n';
    const bytes = zipStore([
      { name: '[Content_Types].xml', data: types },
      { name: '_rels/.rels', data: rels },
      { name: '3D/3dmodel.model', data: xml },
    ]);
    return { ok: true, bytes: bytes, xml: xml, error: '' };
  } catch (_err) {
    return { ok: false, bytes: null, xml: '', error: ERR_EXPORT };
  }
}

export function modelXmlFrom3mf(bytes) {
  if (!bytes || !bytes.length) return '';
  let text = '';
  const chunk = 0x8000;
  for (let i = 0; i < bytes.length; i += chunk) {
    text += String.fromCharCode.apply(null, bytes.subarray(i, Math.min(bytes.length, i + chunk)));
  }
  const start = text.indexOf('<model');
  const end = text.indexOf('</model>');
  if (start < 0 || end < 0) return '';
  return text.slice(start, end + '</model>'.length);
}

export function placedMeshBounds(vertices, placement) {
  const place = placementOf({ placement: placement });
  let xmin = Infinity;
  let ymin = Infinity;
  let zmin = Infinity;
  let xmax = -Infinity;
  let ymax = -Infinity;
  let zmax = -Infinity;
  const list = vertices || [];
  for (let i = 0; i < list.length; i += 1) {
    const p = list[i];
    const x = p[0] + place.x;
    const y = p[1] + place.y;
    const z = p[2] + place.z;
    if (x < xmin) xmin = x;
    if (y < ymin) ymin = y;
    if (z < zmin) zmin = z;
    if (x > xmax) xmax = x;
    if (y > ymax) ymax = y;
    if (z > zmax) zmax = z;
  }
  return { xmin: xmin, ymin: ymin, zmin: zmin, xmax: xmax, ymax: ymax, zmax: zmax };
}

export function exactPlacedBounds(oc, shape, placement) {
  const copied = placedCopy(oc, shape, placement);
  if (!copied.ok || !copied.shape) return null;
  try {
    return optimalBounds(oc, copied.shape);
  } finally {
    release(copied.shape);
  }
}
