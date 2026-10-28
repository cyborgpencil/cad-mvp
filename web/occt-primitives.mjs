// Box, cylinder, and disc solids through libcascade 3.1.0 (OCCT 8.0.1).
// Signatures checked against builds/libcascade/pkg/package/dist/types.d.ts:
//   BRepPrimAPI_MakeBox(gp_Pnt, dx, dy, dz)
//   BRepPrimAPI_MakeCylinder(gp_Ax2, R, H)
//   gp_Ax2(gp_Pnt, gp_Dir)
// Partial-angle MakeCylinder is not used. Sides/Segments is not a parameter.

import { checkOcctShape } from './occt-gate.mjs';

// App defaults. Team choice (Erik 7:00 PM MT), not a sourced spec.
// Box edge is 20 mm. Cylinder diameter is 20 mm (radius 10) and height is 20 mm.
// Centre (0, 0, 10) places that 20 mm solid from z = 0 to z = 20.
// SPHERE_DIAMETER_MM is recorded only. There is no sphere primitive.
export const BOX_EDGE_MM = 20;
export const CYLINDER_DIAMETER_MM = 20;
export const CYLINDER_HEIGHT_MM = 20;
export const SPHERE_DIAMETER_MM = 20;
// Disc. Team choice, 2026-10-21. Diameter 18 mm, thickness 4 mm.
// Centre z is thickness/2 so the disc sits on z = 0, the same bottom rule as the 20 mm solids.
export const DISC_DIAMETER_MM = 18;
export const DISC_THICKNESS_MM = 4;

export const PLACEHOLDER_BOX_MM = Object.freeze({
  cx: 0,
  cy: 0,
  cz: 10,
  sx: BOX_EDGE_MM,
  sy: BOX_EDGE_MM,
  sz: BOX_EDGE_MM,
  rx: 0,
  ry: 0,
  rz: 0,
});

export const PLACEHOLDER_CYLINDER_MM = Object.freeze({
  cx: 0,
  cy: 0,
  cz: 10,
  radius: CYLINDER_DIAMETER_MM / 2,
  height: CYLINDER_HEIGHT_MM,
  axis: 'Z',
  rx: 0,
  ry: 0,
  rz: 0,
});

export const PLACEHOLDER_DISC_MM = Object.freeze({
  cx: 0,
  cy: 0,
  cz: DISC_THICKNESS_MM / 2,
  diameter: DISC_DIAMETER_MM,
  thickness: DISC_THICKNESS_MM,
  axis: 'Z',
  rx: 0,
  ry: 0,
  rz: 0,
});

// Mesh defaults. Team proposal, sourced from the OCCT Mesh user guide
// (https://dev.opencascade.org/doc/overview/html/occt_user_guides__mesh.html).
// Team choice, 2026-10-21. Confirmed on IMeshTools_Parameters in
// libcascade 3.1.0 types.d.ts: Deflection, Relative, Angle,
// ControlSurfaceDeflection, InParallel. The same object is passed to
// BRepMesh_IncrementalMesh(shape, parameters). Display and export both
// use tessellate(), so they share these values. Not a Sides control.
export const TESSELLATION_DEFLECTION_MM = 0.01;
export const TESSELLATION_ANGULAR = 0.2;
export const TESSELLATION_RELATIVE = false;
export const TESSELLATION_CONTROL_SURFACE = true;
export const TESSELLATION_IN_PARALLEL = false;

// Weld grid for tessellation vertices that the mesher emits twice, once per face.
// Same order as the sewing tolerance in occt-gate.mjs. Not a picked MODO value.
const WELD_MM = 1e-4;

const EDGE_SAMPLES = 16;

function track(trash, obj) {
  if (obj && typeof obj.delete === 'function') trash.push(obj);
  return obj;
}

function dispose(trash) {
  for (let i = trash.length - 1; i >= 0; i -= 1) {
    try {
      trash[i].delete();
    } catch (_err) {
      // already released
    }
  }
}

function num(value, fallback) {
  const n = Number(value);
  return Number.isFinite(n) ? n : fallback;
}

export function normalizeBox(params) {
  const src = params || {};
  return {
    cx: num(src.cx, PLACEHOLDER_BOX_MM.cx),
    cy: num(src.cy, PLACEHOLDER_BOX_MM.cy),
    cz: num(src.cz, PLACEHOLDER_BOX_MM.cz),
    sx: num(src.sx, PLACEHOLDER_BOX_MM.sx),
    sy: num(src.sy, PLACEHOLDER_BOX_MM.sy),
    sz: num(src.sz, PLACEHOLDER_BOX_MM.sz),
    rx: num(src.rx, PLACEHOLDER_BOX_MM.rx),
    ry: num(src.ry, PLACEHOLDER_BOX_MM.ry),
    rz: num(src.rz, PLACEHOLDER_BOX_MM.rz),
  };
}

export function normalizeCylinder(params) {
  const src = params || {};
  let axis = String(src.axis || PLACEHOLDER_CYLINDER_MM.axis).toUpperCase();
  if (axis !== 'X' && axis !== 'Y' && axis !== 'Z') axis = 'Z';
  return {
    cx: num(src.cx, PLACEHOLDER_CYLINDER_MM.cx),
    cy: num(src.cy, PLACEHOLDER_CYLINDER_MM.cy),
    cz: num(src.cz, PLACEHOLDER_CYLINDER_MM.cz),
    radius: num(src.radius, PLACEHOLDER_CYLINDER_MM.radius),
    height: num(src.height, PLACEHOLDER_CYLINDER_MM.height),
    axis: axis,
    rx: num(src.rx, PLACEHOLDER_CYLINDER_MM.rx),
    ry: num(src.ry, PLACEHOLDER_CYLINDER_MM.ry),
    rz: num(src.rz, PLACEHOLDER_CYLINDER_MM.rz),
  };
}

export function normalizeDisc(params) {
  const src = params || {};
  let axis = String(src.axis || PLACEHOLDER_DISC_MM.axis).toUpperCase();
  if (axis !== 'X' && axis !== 'Y' && axis !== 'Z') axis = 'Z';
  const diameter = src.diameter === undefined && src.radius !== undefined
    ? num(src.radius, PLACEHOLDER_DISC_MM.diameter / 2) * 2
    : num(src.diameter, PLACEHOLDER_DISC_MM.diameter);
  const thickness = src.thickness === undefined && src.height !== undefined
    ? num(src.height, PLACEHOLDER_DISC_MM.thickness)
    : num(src.thickness, PLACEHOLDER_DISC_MM.thickness);
  return {
    cx: num(src.cx, PLACEHOLDER_DISC_MM.cx),
    cy: num(src.cy, PLACEHOLDER_DISC_MM.cy),
    cz: num(src.cz, PLACEHOLDER_DISC_MM.cz),
    diameter: diameter,
    thickness: thickness,
    axis: axis,
    rx: num(src.rx, PLACEHOLDER_DISC_MM.rx),
    ry: num(src.ry, PLACEHOLDER_DISC_MM.ry),
    rz: num(src.rz, PLACEHOLDER_DISC_MM.rz),
  };
}

function axisVector(axis) {
  if (axis === 'X') return [1, 0, 0];
  if (axis === 'Y') return [0, 1, 0];
  return [0, 0, 1];
}

function isReversed(shape) {
  let name = '';
  try {
    const orient = shape.Orientation();
    name = typeof orient === 'string' ? orient : String(orient);
  } catch (_err) {
    name = '';
  }
  return name.indexOf('REVERSED') !== -1;
}

function xyzOf(point) {
  return [point.X(), point.Y(), point.Z()];
}

function weldMesh(rawVertices, rawTriangles) {
  const vertices = [];
  const map = new Map();
  const scale = 1 / WELD_MM;
  function add(p) {
    const key = Math.round(p[0] * scale) + '|' + Math.round(p[1] * scale) + '|' + Math.round(p[2] * scale);
    const found = map.get(key);
    if (found !== undefined) return found;
    const id = vertices.length;
    vertices.push([p[0], p[1], p[2]]);
    map.set(key, id);
    return id;
  }
  const triangles = [];
  const faceTris = rawTriangles.faceTris.map(function () { return []; });
  for (let t = 0; t < rawTriangles.tris.length; t += 1) {
    const src = rawTriangles.tris[t];
    const a = add(rawVertices[src[0]]);
    const b = add(rawVertices[src[1]]);
    const c = add(rawVertices[src[2]]);
    if (a === b || b === c || a === c) continue;
    const id = triangles.length;
    triangles.push([a, b, c]);
    faceTris[src[3]].push(id);
  }
  return { vertices: vertices, triangles: triangles, faceTris: faceTris };
}

function signedVolume(vertices, triangles) {
  let sum = 0;
  for (let i = 0; i < triangles.length; i += 1) {
    const tri = triangles[i];
    const a = vertices[tri[0]];
    const b = vertices[tri[1]];
    const c = vertices[tri[2]];
    const cx = b[1] * c[2] - b[2] * c[1];
    const cy = b[2] * c[0] - b[0] * c[2];
    const cz = b[0] * c[1] - b[1] * c[0];
    sum += a[0] * cx + a[1] * cy + a[2] * cz;
  }
  return sum;
}

function flipTriangles(triangles) {
  for (let i = 0; i < triangles.length; i += 1) {
    const tri = triangles[i];
    const tmp = tri[1];
    tri[1] = tri[2];
    tri[2] = tmp;
  }
}

// Same rules as src/solid/watertight.cpp. The page still runs the wasm checker
// after replaceMesh. This copy lets the node test see a mesh failure without wasm.
export function checkMeshWatertight(mesh) {
  if (!mesh || !mesh.triangles || mesh.triangles.length === 0) {
    return { pass: false, message: 'FAIL: mesh has no triangles.' };
  }
  const vertexCount = mesh.vertices.length;
  for (let i = 0; i < mesh.triangles.length; i += 1) {
    const tri = mesh.triangles[i];
    for (let k = 0; k < 3; k += 1) {
      if (tri[k] < 0 || tri[k] >= vertexCount) {
        return { pass: false, message: 'FAIL: triangle ' + i + ' uses vertex index ' + tri[k] + ', which is outside the ' + vertexCount + '-vertex mesh.' };
      }
    }
    if (tri[0] === tri[1] || tri[1] === tri[2] || tri[0] === tri[2]) {
      return { pass: false, message: 'FAIL: triangle ' + i + ' has a repeated vertex index.' };
    }
    const a = mesh.vertices[tri[0]];
    const b = mesh.vertices[tri[1]];
    const c = mesh.vertices[tri[2]];
    const ux = b[0] - a[0];
    const uy = b[1] - a[1];
    const uz = b[2] - a[2];
    const vx = c[0] - a[0];
    const vy = c[1] - a[1];
    const vz = c[2] - a[2];
    const cx = uy * vz - uz * vy;
    const cy = uz * vx - ux * vz;
    const cz = ux * vy - uy * vx;
    if (cx === 0 && cy === 0 && cz === 0) {
      return { pass: false, message: 'FAIL: triangle ' + i + ' has zero area.' };
    }
  }
  const undirected = new Map();
  const directed = new Map();
  for (let i = 0; i < mesh.triangles.length; i += 1) {
    const tri = mesh.triangles[i];
    for (let k = 0; k < 3; k += 1) {
      const from = tri[k];
      const to = tri[(k + 1) % 3];
      const dkey = from + ',' + to;
      directed.set(dkey, (directed.get(dkey) || 0) + 1);
      const lo = from < to ? from : to;
      const hi = from < to ? to : from;
      const ukey = lo + ',' + hi;
      undirected.set(ukey, (undirected.get(ukey) || 0) + 1);
    }
  }
  for (const entry of undirected.entries()) {
    if (entry[1] !== 2) {
      return { pass: false, message: 'FAIL: edge (' + entry[0] + ') is shared by ' + entry[1] + ' triangle' + (entry[1] === 1 ? '' : 's') + ' (need 2).' };
    }
  }
  for (const entry of directed.entries()) {
    if (entry[1] !== 1) {
      return { pass: false, message: 'FAIL: edge (' + entry[0] + ') is wound the same way by two triangles.' };
    }
  }
  const sum = signedVolume(mesh.vertices, mesh.triangles);
  if (sum === 0) return { pass: false, message: 'FAIL: signed volume is zero.' };
  if (sum < 0) return { pass: false, message: 'FAIL: winding is inward (signed volume is negative).' };
  return {
    pass: true,
    message: 'PASS: closed triangle mesh, every edge shared by two triangles, outward winding, no zero-area triangles.',
  };
}

function nowMs() {
  if (typeof performance !== 'undefined' && typeof performance.now === 'function') return performance.now();
  return Date.now();
}

function tessellate(oc, shape, trash) {
  const started = nowMs();
  let mesher = null;
  let meshPath = 'IMeshTools_Parameters';
  const parameters = track(trash, new oc.IMeshTools_Parameters());
  parameters.Relative = TESSELLATION_RELATIVE;
  parameters.Deflection = TESSELLATION_DEFLECTION_MM;
  parameters.Angle = TESSELLATION_ANGULAR;
  parameters.ControlSurfaceDeflection = TESSELLATION_CONTROL_SURFACE;
  parameters.InParallel = TESSELLATION_IN_PARALLEL;
  try {
    mesher = track(trash, new oc.BRepMesh_IncrementalMesh(shape, parameters));
  } catch (_err) {
    // Closest constructor if the parameters object is rejected:
    // (shape, linear deflection, isRelative, angular deflection, isInParallel).
    meshPath = 'constructor(linDeflection, isRelative, angDeflection, isInParallel)';
    mesher = track(trash, new oc.BRepMesh_IncrementalMesh(
      shape,
      TESSELLATION_DEFLECTION_MM,
      TESSELLATION_RELATIVE,
      TESSELLATION_ANGULAR,
      TESSELLATION_IN_PARALLEL
    ));
  }
  try {
    if (typeof mesher.Perform === 'function') mesher.Perform();
  } catch (_err) {
    // The constructor already meshes on this build.
  }
  let meshSettings = {
    Relative: TESSELLATION_RELATIVE,
    Deflection: TESSELLATION_DEFLECTION_MM,
    Angle: TESSELLATION_ANGULAR,
    ControlSurfaceDeflection: TESSELLATION_CONTROL_SURFACE,
    InParallel: TESSELLATION_IN_PARALLEL,
    path: meshPath,
  };
  try {
    if (mesher && typeof mesher.Parameters === 'function') {
      const echoed = mesher.Parameters();
      if (echoed) {
        meshSettings = {
          Relative: echoed.Relative,
          Deflection: echoed.Deflection,
          Angle: echoed.Angle,
          ControlSurfaceDeflection: echoed.ControlSurfaceDeflection,
          InParallel: echoed.InParallel,
          path: meshPath,
        };
        if (echoed !== parameters && typeof echoed.delete === 'function') {
          try { echoed.delete(); } catch (_drop) { /* already released */ }
        }
      }
    }
  } catch (_err) {
    // The values passed in are still the ones the constructor received.
  }
  const rawVertices = [];
  const rawTris = [];
  const faceCount = { n: 0 };
  const explorer = track(trash, new oc.TopExp_Explorer(shape, oc.TopAbs_ShapeEnum.TopAbs_FACE));
  while (explorer.More()) {
    const faceIndex = faceCount.n;
    faceCount.n += 1;
    const face = track(trash, oc.TopoDS.Face(explorer.Current()));
    const loc = track(trash, new oc.TopLoc_Location());
    let tri = null;
    try {
      tri = oc.BRep_Tool.Triangulation(face, loc, 0);
    } catch (_err) {
      tri = null;
    }
    if (tri && typeof tri.delete === 'function') trash.push(tri);
    const reversed = isReversed(face);
    if (tri && !(typeof tri.IsNull === 'function' && tri.IsNull()) && tri.NbNodes && tri.NbNodes() > 0) {
      const trsf = track(trash, loc.Transformation());
      const base = rawVertices.length;
      const nNodes = tri.NbNodes();
      for (let i = 1; i <= nNodes; i += 1) {
        const p = track(trash, tri.Node(i));
        const tp = track(trash, p.Transformed(trsf));
        rawVertices.push(xyzOf(tp));
      }
      const nTri = tri.NbTriangles();
      for (let i = 1; i <= nTri; i += 1) {
        const poly = track(trash, tri.Triangle(i));
        let a = base + poly.Value(1) - 1;
        let b = base + poly.Value(2) - 1;
        let c = base + poly.Value(3) - 1;
        if (reversed) {
          const tmp = b;
          b = c;
          c = tmp;
        }
        rawTris.push([a, b, c, faceIndex]);
      }
    }
    explorer.Next();
  }
  const welded = weldMesh(rawVertices, { tris: rawTris, faceTris: Array.from({ length: faceCount.n }, function () { return []; }) });
  if (signedVolume(welded.vertices, welded.triangles) < 0) flipTriangles(welded.triangles);
  welded.meshTimeMs = nowMs() - started;
  welded.meshSettings = meshSettings;
  welded.meshPath = meshPath;
  return welded;
}

function sampleEdge(oc, edge, trash) {
  try {
    const env = oc.BRep_Tool.Curve(edge);
    const curve = env && env.returnValue;
    if (curve && !(typeof curve.IsNull === 'function' && curve.IsNull()) && typeof curve.Value === 'function') {
      const pts = [];
      const first = Number(env.First);
      const last = Number(env.Last);
      const steps = EDGE_SAMPLES;
      for (let i = 0; i <= steps; i += 1) {
        const u = first + (last - first) * (i / steps);
        const p = track(trash, curve.Value(u));
        pts.push(xyzOf(p));
      }
      if (typeof env[Symbol.dispose] === 'function') env[Symbol.dispose]();
      else if (curve && typeof curve.delete === 'function') trash.push(curve);
      if (pts.length >= 2) return pts;
    } else if (env && typeof env[Symbol.dispose] === 'function') {
      env[Symbol.dispose]();
    }
  } catch (_err) {
    // Fall through to the edge vertices.
  }
  const pts = [];
  try {
    const first = track(trash, oc.TopExp.FirstVertex(edge, true));
    const last = track(trash, oc.TopExp.LastVertex(edge, true));
    if (first && !(typeof first.IsNull === 'function' && first.IsNull())) {
      const p = track(trash, oc.BRep_Tool.Pnt(first));
      pts.push(xyzOf(p));
    }
    if (last && !(typeof last.IsNull === 'function' && last.IsNull())) {
      const p = track(trash, oc.BRep_Tool.Pnt(last));
      const q = xyzOf(p);
      const prev = pts[pts.length - 1];
      if (!prev || prev[0] !== q[0] || prev[1] !== q[1] || prev[2] !== q[2]) pts.push(q);
    }
  } catch (_err) {
    // No vertex pair.
  }
  return pts;
}

function topologyFromShape(oc, shape, mesh, trash) {
  const vertices = [];
  const seenV = new Set();
  const vExp = track(trash, new oc.TopExp_Explorer(shape, oc.TopAbs_ShapeEnum.TopAbs_VERTEX));
  while (vExp.More()) {
    const vertex = track(trash, oc.TopoDS.Vertex(vExp.Current()));
    const p = track(trash, oc.BRep_Tool.Pnt(vertex));
    const at = xyzOf(p);
    const key = Math.round(at[0] * 1e6) + '|' + Math.round(at[1] * 1e6) + '|' + Math.round(at[2] * 1e6);
    if (!seenV.has(key)) {
      seenV.add(key);
      vertices.push({ id: 'v' + vertices.length, p: at });
    }
    vExp.Next();
  }
  const edges = [];
  const seenE = new Set();
  const eExp = track(trash, new oc.TopExp_Explorer(shape, oc.TopAbs_ShapeEnum.TopAbs_EDGE));
  while (eExp.More()) {
    const edge = track(trash, oc.TopoDS.Edge(eExp.Current()));
    const pts = sampleEdge(oc, edge, trash);
    if (pts.length >= 2) {
      const a = pts[0];
      const b = pts[pts.length - 1];
      const ka = Math.round(a[0] * 1e4) + ',' + Math.round(a[1] * 1e4) + ',' + Math.round(a[2] * 1e4);
      const kb = Math.round(b[0] * 1e4) + ',' + Math.round(b[1] * 1e4) + ',' + Math.round(b[2] * 1e4);
      const key = ka < kb ? ka + '|' + kb : kb + '|' + ka;
      if (!seenE.has(key)) {
        seenE.add(key);
        edges.push({ id: 'e' + edges.length, pts: pts });
      }
    }
    eExp.Next();
  }
  const faces = [];
  for (let i = 0; i < mesh.faceTris.length; i += 1) {
    const tris = mesh.faceTris[i];
    let sx = 0;
    let sy = 0;
    let sz = 0;
    let n = 0;
    for (let t = 0; t < tris.length; t += 1) {
      const tri = mesh.triangles[tris[t]];
      for (let k = 0; k < 3; k += 1) {
        const p = mesh.vertices[tri[k]];
        sx += p[0];
        sy += p[1];
        sz += p[2];
        n += 1;
      }
    }
    faces.push({
      id: 'f' + i,
      tris: tris.slice(),
      centroid: n ? [sx / n, sy / n, sz / n] : [0, 0, 0],
    });
  }
  const triFace = new Array(mesh.triangles.length);
  for (let i = 0; i < faces.length; i += 1) {
    const tris = faces[i].tris;
    for (let t = 0; t < tris.length; t += 1) triFace[tris[t]] = faces[i].id;
  }
  const topology = {
    source: 'occt',
    vertices: vertices,
    edges: edges,
    faces: faces,
    triFace: triFace,
  };
  stampOcctIndexes(oc, shape, topology, trash);
  return topology;
}

// Face ids stay in TopExp.MapShapes order (the same order as the mesh faces).
// occtIndex is the 1-based map index. TopTools_IndexedMapOfShape is the
// libcascade alias NCollection_IndexedMap_TopoDS_Shape_TopTools_ShapeMapHasher.
function stampOcctIndexes(oc, shape, topology, trash) {
  const Ctor = oc.TopTools_IndexedMapOfShape
    || oc.NCollection_IndexedMap_TopoDS_Shape_TopTools_ShapeMapHasher;
  if (!Ctor || !oc.TopExp || typeof oc.TopExp.MapShapes !== 'function' || !oc.TopoDS) return;
  try {
    const faces = track(trash, new Ctor());
    oc.TopExp.MapShapes(shape, oc.TopAbs_ShapeEnum.TopAbs_FACE, faces);
    if (faces.Extent() === topology.faces.length) {
      for (let i = 0; i < topology.faces.length; i += 1) {
        topology.faces[i].occtIndex = i + 1;
        const face = track(trash, oc.TopoDS.Face(faces.FindKey(i + 1)));
        try {
          const adapt = track(trash, new oc.BRepAdaptor_Surface(face, true));
          topology.faces[i].surface = String(adapt.GetType());
        } catch (_err) {
          topology.faces[i].surface = '';
        }
      }
    }
    const edges = track(trash, new Ctor());
    oc.TopExp.MapShapes(shape, oc.TopAbs_ShapeEnum.TopAbs_EDGE, edges);
    for (let i = 1; i <= edges.Extent(); i += 1) {
      const edge = track(trash, oc.TopoDS.Edge(edges.FindKey(i)));
      const pts = sampleEdge(oc, edge, trash);
      if (pts.length < 2) continue;
      const a = pts[0];
      const b = pts[pts.length - 1];
      for (let k = 0; k < topology.edges.length; k += 1) {
        const topo = topology.edges[k];
        if (topo.occtIndex || !topo.pts || topo.pts.length < 2) continue;
        const pa = topo.pts[0];
        const pb = topo.pts[topo.pts.length - 1];
        const same = (nearPoint(pa, a) && nearPoint(pb, b)) || (nearPoint(pa, b) && nearPoint(pb, a));
        if (same) topo.occtIndex = i;
      }
    }
    const vertices = track(trash, new Ctor());
    oc.TopExp.MapShapes(shape, oc.TopAbs_ShapeEnum.TopAbs_VERTEX, vertices);
    for (let i = 1; i <= vertices.Extent(); i += 1) {
      const vertex = track(trash, oc.TopoDS.Vertex(vertices.FindKey(i)));
      const point = track(trash, oc.BRep_Tool.Pnt(vertex));
      const at = [point.X(), point.Y(), point.Z()];
      for (let k = 0; k < topology.vertices.length; k += 1) {
        const topo = topology.vertices[k];
        if (!topo.occtIndex && nearPoint(topo.p, at)) topo.occtIndex = i;
      }
    }
  } catch (_err) {
    // The mesh ids still select a sub-shape when the map is unavailable.
  }
}

function nearPoint(a, b) {
  return !!a && !!b
    && Math.abs(a[0] - b[0]) <= 1e-4
    && Math.abs(a[1] - b[1]) <= 1e-4
    && Math.abs(a[2] - b[2]) <= 1e-4;
}

// Gate plus mesh for a shape the caller still owns. Does not delete `shape`.
export function inspectSolid(oc, shape) {
  const trash = [];
  try {
    const gate = checkOcctShape(oc, shape);
    const mesh = tessellate(oc, shape, trash);
    const topology = topologyFromShape(oc, shape, mesh, trash);
    const watertight = checkMeshWatertight(mesh);
    return {
      units: 'mm',
      gate: gate,
      watertight: watertight,
      mesh: { vertices: mesh.vertices, triangles: mesh.triangles },
      topology: topology,
      meshTimeMs: mesh.meshTimeMs || 0,
      meshSettings: mesh.meshSettings || null,
      meshPath: mesh.meshPath || '',
    };
  } finally {
    dispose(trash);
  }
}

function finish(oc, shape, trash, kind, params) {
  const gate = checkOcctShape(oc, shape);
  const mesh = tessellate(oc, shape, trash);
  const topology = topologyFromShape(oc, shape, mesh, trash);
  const watertight = checkMeshWatertight(mesh);
  return {
    kind: kind,
    params: params,
    units: 'mm',
    gate: gate,
    watertight: watertight,
    mesh: { vertices: mesh.vertices, triangles: mesh.triangles },
    topology: topology,
    meshTimeMs: mesh.meshTimeMs || 0,
    meshSettings: mesh.meshSettings || null,
    meshPath: mesh.meshPath || '',
  };
}

export function buildBox(oc, params) {
  const box = normalizeBox(params);
  if (!(box.sx > 0) || !(box.sy > 0) || !(box.sz > 0)) {
    return {
      kind: 'box',
      params: box,
      units: 'mm',
      gate: { pass: false, valid: false, freeEdges: -1, message: 'FAIL: box size must be positive millimetres.' },
      watertight: { pass: false, message: 'FAIL: mesh has no triangles.' },
      mesh: { vertices: [], triangles: [] },
      topology: { source: 'occt', vertices: [], edges: [], faces: [], triFace: [] },
    };
  }
  const trash = [];
  try {
    const corner = track(trash, new oc.gp_Pnt(
      box.cx - box.sx / 2,
      box.cy - box.sy / 2,
      box.cz - box.sz / 2
    ));
    const maker = track(trash, new oc.BRepPrimAPI_MakeBox(corner, box.sx, box.sy, box.sz));
    maker.Build();
    if (!maker.IsDone()) {
      return {
        kind: 'box',
        params: box,
        units: 'mm',
        gate: { pass: false, valid: false, freeEdges: -1, message: 'FAIL: BRepPrimAPI_MakeBox is not done.' },
        watertight: { pass: false, message: 'FAIL: mesh has no triangles.' },
        mesh: { vertices: [], triangles: [] },
        topology: { source: 'occt', vertices: [], edges: [], faces: [], triFace: [] },
      };
    }
    const shape = track(trash, maker.Shape());
    return finish(oc, shape, trash, 'box', box);
  } catch (err) {
    return {
      kind: 'box',
      params: box,
      units: 'mm',
      gate: { pass: false, valid: false, freeEdges: -1, message: 'FAIL: OCCT gate error: ' + (err && err.message ? err.message : String(err)) },
      watertight: { pass: false, message: 'FAIL: mesh has no triangles.' },
      mesh: { vertices: [], triangles: [] },
      topology: { source: 'occt', vertices: [], edges: [], faces: [], triFace: [] },
    };
  } finally {
    dispose(trash);
  }
}

export function buildCylinder(oc, params) {
  const cyl = normalizeCylinder(params);
  if (!(cyl.radius > 0) || !(cyl.height > 0)) {
    return {
      kind: 'cylinder',
      params: cyl,
      units: 'mm',
      gate: { pass: false, valid: false, freeEdges: -1, message: 'FAIL: cylinder radius and height must be positive millimetres.' },
      watertight: { pass: false, message: 'FAIL: mesh has no triangles.' },
      mesh: { vertices: [], triangles: [] },
      topology: { source: 'occt', vertices: [], edges: [], faces: [], triFace: [] },
    };
  }
  const trash = [];
  try {
    const dir = axisVector(cyl.axis);
    const base = track(trash, new oc.gp_Pnt(
      cyl.cx - dir[0] * cyl.height / 2,
      cyl.cy - dir[1] * cyl.height / 2,
      cyl.cz - dir[2] * cyl.height / 2
    ));
    const gpDir = track(trash, new oc.gp_Dir(dir[0], dir[1], dir[2]));
    const axes = track(trash, new oc.gp_Ax2(base, gpDir));
    const maker = track(trash, new oc.BRepPrimAPI_MakeCylinder(axes, cyl.radius, cyl.height));
    maker.Build();
    if (!maker.IsDone()) {
      return {
        kind: 'cylinder',
        params: cyl,
        units: 'mm',
        gate: { pass: false, valid: false, freeEdges: -1, message: 'FAIL: BRepPrimAPI_MakeCylinder is not done.' },
        watertight: { pass: false, message: 'FAIL: mesh has no triangles.' },
        mesh: { vertices: [], triangles: [] },
        topology: { source: 'occt', vertices: [], edges: [], faces: [], triFace: [] },
      };
    }
    const shape = track(trash, maker.Shape());
    return finish(oc, shape, trash, 'cylinder', cyl);
  } catch (err) {
    return {
      kind: 'cylinder',
      params: cyl,
      units: 'mm',
      gate: { pass: false, valid: false, freeEdges: -1, message: 'FAIL: OCCT gate error: ' + (err && err.message ? err.message : String(err)) },
      watertight: { pass: false, message: 'FAIL: mesh has no triangles.' },
      mesh: { vertices: [], triangles: [] },
      topology: { source: 'occt', vertices: [], edges: [], faces: [], triFace: [] },
    };
  } finally {
    dispose(trash);
  }
}

function emptyDisc(disc, message) {
  return {
    kind: 'disc',
    params: disc,
    units: 'mm',
    gate: { pass: false, valid: false, freeEdges: -1, message: message },
    watertight: { pass: false, message: 'FAIL: mesh has no triangles.' },
    mesh: { vertices: [], triangles: [] },
    topology: { source: 'occt', vertices: [], edges: [], faces: [], triFace: [] },
  };
}

// A disc is a short cylinder. Display and export use the same mesh path as the cylinder.
export function buildDisc(oc, params) {
  const disc = normalizeDisc(params);
  if (!(disc.diameter > 0) || !(disc.thickness > 0)) {
    return emptyDisc(disc, 'FAIL: disc diameter and thickness must be positive millimetres.');
  }
  const built = buildCylinder(oc, {
    cx: disc.cx,
    cy: disc.cy,
    cz: disc.cz,
    radius: disc.diameter / 2,
    height: disc.thickness,
    axis: disc.axis,
  });
  built.kind = 'disc';
  built.params = disc;
  return built;
}

export function flattenMesh(mesh) {
  const positions = new Float64Array(mesh.vertices.length * 3);
  for (let i = 0; i < mesh.vertices.length; i += 1) {
    positions[i * 3] = mesh.vertices[i][0];
    positions[i * 3 + 1] = mesh.vertices[i][1];
    positions[i * 3 + 2] = mesh.vertices[i][2];
  }
  const indices = new Uint32Array(mesh.triangles.length * 3);
  for (let i = 0; i < mesh.triangles.length; i += 1) {
    indices[i * 3] = mesh.triangles[i][0];
    indices[i * 3 + 1] = mesh.triangles[i][1];
    indices[i * 3 + 2] = mesh.triangles[i][2];
  }
  return { positions: positions, indices: indices };
}
