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
          triangles.push([
            base + poly.Value(1) - 1,
            base + poly.Value(2) - 1,
            base + poly.Value(3) - 1,
          ]);
        }
      }
      explorer.Next();
    }
    return { vertices: vertices, triangles: triangles };
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

function colorFor(tag) {
  if (Object.prototype.hasOwnProperty.call(MATERIAL_COLOR, tag)) return MATERIAL_COLOR[tag];
  return '#CCCCCC';
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
      objects.push({
        name: part.name ? String(part.name) : 'Part',
        material: materialTag(part),
        vertices: mesh.vertices,
        triangles: mesh.triangles,
        placement: placementFor(part),
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
