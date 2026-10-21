// Selection rules from research/gui/modo-selection-primitives.md.
// Colours are not in this file. The page reads --hover-color and --sel-color.

export const SELECTION_MODES = ['vertex', 'edge', 'face', 'item'];

// Hotkeys: Vertex 1, Edge 2, Face 3, Item 5. Keys 4, 6 and 7 are out of scope.
export const SELECTION_HOTKEYS = {
  '1': 'vertex',
  '2': 'edge',
  '3': 'face',
  '5': 'item',
};

// Screen-space radius for vertex and edge picking when the hit is a mesh.
// TBD placeholder. The spec leaves the WASM pick tolerance undocumented.
export const PICK_TOLERANCE_PX = 8;

// Coplanar test for mesh-face grouping when no OCCT solid is loaded.
// TBD placeholder. Not a MODO value.
export const MESH_COPLANAR_DOT = 0.999;

export function modeFromHotkey(key) {
  return SELECTION_HOTKEYS[key] || '';
}

export function occtShapeType(mode) {
  if (mode === 'vertex') return 'TopAbs_VERTEX';
  if (mode === 'edge') return 'TopAbs_EDGE';
  if (mode === 'face') return 'TopAbs_FACE';
  return 'SHAPE';
}

// Click replaces. Shift+click adds. Ctrl+click removes.
// Empty Vertex/Edge/Face means the operation applies to all, with no highlight.
// Item mode stays empty until something is selected.
export function applyPointerSelection(mode, selectedIds, hitId, modifiers) {
  const shift = !!(modifiers && modifiers.shift);
  const ctrl = !!(modifiers && modifiers.ctrl);
  const ids = Array.isArray(selectedIds) ? selectedIds.slice() : [];
  if (ctrl) {
    if (hitId != null) {
      const at = ids.indexOf(hitId);
      if (at >= 0) ids.splice(at, 1);
    }
  } else if (shift) {
    if (hitId != null && ids.indexOf(hitId) < 0) ids.push(hitId);
  } else if (hitId == null) {
    ids.length = 0;
  } else {
    ids.length = 0;
    ids.push(hitId);
  }
  const all = mode !== 'item' && ids.length === 0;
  return {
    ids: ids,
    all: all,
    highlight: ids.length > 0,
  };
}

function triNormal(vertices, tri) {
  const a = vertices[tri[0]];
  const b = vertices[tri[1]];
  const c = vertices[tri[2]];
  const ux = b[0] - a[0];
  const uy = b[1] - a[1];
  const uz = b[2] - a[2];
  const vx = c[0] - a[0];
  const vy = c[1] - a[1];
  const vz = c[2] - a[2];
  let nx = uy * vz - uz * vy;
  let ny = uz * vx - ux * vz;
  let nz = ux * vy - uy * vx;
  const len = Math.hypot(nx, ny, nz) || 1;
  return [nx / len, ny / len, nz / len];
}

function edgeKey(a, b) {
  return a < b ? a + ',' + b : b + ',' + a;
}

// Mesh fallback when libcascade has no solid. Faces are coplanar triangle groups.
// Edges are the borders between those groups (a box diagonal stays inside its face).
export function groupMeshFaces(vertices, triangles) {
  const count = triangles.length;
  const parent = [];
  for (let i = 0; i < count; i += 1) parent.push(i);
  function find(a) {
    let x = a;
    while (parent[x] !== x) {
      parent[x] = parent[parent[x]];
      x = parent[x];
    }
    return x;
  }
  function unite(a, b) {
    const pa = find(a);
    const pb = find(b);
    if (pa !== pb) parent[pa] = pb;
  }
  const normals = [];
  for (let t = 0; t < count; t += 1) normals.push(triNormal(vertices, triangles[t]));
  const edgeMap = new Map();
  for (let t = 0; t < count; t += 1) {
    const tri = triangles[t];
    for (let k = 0; k < 3; k += 1) {
      const key = edgeKey(tri[k], tri[(k + 1) % 3]);
      if (!edgeMap.has(key)) edgeMap.set(key, []);
      edgeMap.get(key).push(t);
    }
  }
  for (const tris of edgeMap.values()) {
    for (let i = 0; i < tris.length; i += 1) {
      for (let j = i + 1; j < tris.length; j += 1) {
        const ni = normals[tris[i]];
        const nj = normals[tris[j]];
        const dot = ni[0] * nj[0] + ni[1] * nj[1] + ni[2] * nj[2];
        if (dot >= MESH_COPLANAR_DOT) unite(tris[i], tris[j]);
      }
    }
  }
  const groups = new Map();
  for (let t = 0; t < count; t += 1) {
    const g = find(t);
    if (!groups.has(g)) groups.set(g, []);
    groups.get(g).push(t);
  }
  const triFace = new Array(count);
  const faces = [];
  let faceIndex = 0;
  for (const tris of groups.values()) {
    const id = 'f' + faceIndex;
    faceIndex += 1;
    let sx = 0;
    let sy = 0;
    let sz = 0;
    let n = 0;
    for (let i = 0; i < tris.length; i += 1) {
      triFace[tris[i]] = id;
      const tri = triangles[tris[i]];
      for (let k = 0; k < 3; k += 1) {
        const p = vertices[tri[k]];
        sx += p[0];
        sy += p[1];
        sz += p[2];
        n += 1;
      }
    }
    faces.push({
      id: id,
      tris: tris,
      centroid: n ? [sx / n, sy / n, sz / n] : [0, 0, 0],
    });
  }
  const edges = [];
  const used = new Set();
  let edgeIndex = 0;
  for (const entry of edgeMap.entries()) {
    const key = entry[0];
    const tris = entry[1];
    const faceIds = new Set();
    for (let i = 0; i < tris.length; i += 1) faceIds.add(triFace[tris[i]]);
    if (faceIds.size < 2 && tris.length !== 1) continue;
    const parts = key.split(',');
    const ia = Number(parts[0]);
    const ib = Number(parts[1]);
    edges.push({ id: 'e' + edgeIndex, pts: [vertices[ia], vertices[ib]] });
    edgeIndex += 1;
    used.add(ia);
    used.add(ib);
  }
  const topoVerts = [];
  let vertexIndex = 0;
  for (const index of used) {
    topoVerts.push({ id: 'v' + vertexIndex, index: index, p: vertices[index] });
    vertexIndex += 1;
  }
  return {
    source: 'mesh',
    vertices: topoVerts,
    edges: edges,
    faces: faces,
    triFace: triFace,
  };
}
