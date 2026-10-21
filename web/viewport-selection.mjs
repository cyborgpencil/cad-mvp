// Move gizmo and selection overlays. Colours come from CSS variables.
// CAD millimetres are Z-up. The viewport is three.js Y-up, so cad (x, y, z)
// is drawn as three (x, z, y). Axis Z is up and uses --axis-z.

export const GIZMO_AXIS_THREE = {
  x: [1, 0, 0],
  y: [0, 0, 1],
  z: [0, 1, 0],
};

export function cadToThree(x, y, z, out) {
  out.set(x, z, y);
  return out;
}

export function threeDeltaToCad(dx, dy, dz) {
  return { x: dx, y: dz, z: dy };
}

export function readCssColor(name) {
  if (typeof document === 'undefined') return '';
  return getComputedStyle(document.documentElement).getPropertyValue(name).trim();
}

function cssThreeColor(THREE, name) {
  const raw = readCssColor(name);
  if (!raw) throw new Error('Missing CSS colour ' + name);
  return new THREE.Color(raw);
}

function addMesh(THREE, group, pickables, geometry, colorName, handle, position) {
  const material = new THREE.MeshBasicMaterial({
    color: cssThreeColor(THREE, colorName),
    depthTest: false,
    depthWrite: false,
    transparent: true,
    opacity: 0.95,
  });
  const mesh = new THREE.Mesh(geometry, material);
  if (position) mesh.position.copy(position);
  // Overlays use renderOrder 5. The gizmo draws after every overlay and the solid.
  mesh.renderOrder = 6;
  mesh.userData.handle = handle;
  mesh.userData.colorName = colorName;
  group.add(mesh);
  pickables.push(mesh);
  return mesh;
}

export function makeGizmo(THREE) {
  const group = new THREE.Group();
  const pickables = [];
  const x = GIZMO_AXIS_THREE.x;
  const y = GIZMO_AXIS_THREE.y;
  const z = GIZMO_AXIS_THREE.z;

  function arrow(dir, colorName, handle) {
    const shaft = new THREE.CylinderGeometry(0.28, 0.28, 12, 8);
    const head = new THREE.ConeGeometry(0.85, 2.4, 10);
    const quat = new THREE.Quaternion().setFromUnitVectors(
      new THREE.Vector3(0, 1, 0),
      new THREE.Vector3(dir[0], dir[1], dir[2])
    );
    const shaftMesh = addMesh(THREE, group, pickables, shaft, colorName, handle);
    shaftMesh.quaternion.copy(quat);
    shaftMesh.position.set(dir[0] * 6, dir[1] * 6, dir[2] * 6);
    const headMesh = addMesh(THREE, group, pickables, head, colorName, handle);
    headMesh.quaternion.copy(quat);
    headMesh.position.set(dir[0] * 13.2, dir[1] * 13.2, dir[2] * 13.2);
  }

  arrow(x, '--axis-x', 'x');
  arrow(y, '--axis-y', 'y');
  arrow(z, '--axis-z', 'z');

  function planeHandle(handle, colorName, geometry, ox, oy, oz) {
    const mesh = addMesh(THREE, group, pickables, geometry, colorName, handle);
    mesh.position.set(ox, oy, oz);
    mesh.material.opacity = 0.45;
  }

  // Planar paddles sit in the positive quadrant of each CAD plane.
  // CAD XY is three XZ (thin in three Y). CAD YZ is thin in three X. CAD ZX is thin in three Z.
  planeHandle('xy', '--axis-z', new THREE.BoxGeometry(4.2, 0.28, 4.2), 5.2, 0.35, 5.2);
  planeHandle('yz', '--axis-x', new THREE.BoxGeometry(0.28, 4.2, 4.2), 0.35, 5.2, 5.2);
  planeHandle('zx', '--axis-y', new THREE.BoxGeometry(4.2, 4.2, 0.28), 5.2, 5.2, 0.35);

  const centre = addMesh(
    THREE,
    group,
    pickables,
    new THREE.SphereGeometry(1.15, 16, 12),
    '--centre-color',
    'view'
  );
  centre.material.opacity = 0.9;

  function paint() {
    for (let i = 0; i < pickables.length; i += 1) {
      const item = pickables[i];
      item.material.color.copy(cssThreeColor(THREE, item.userData.colorName));
    }
  }

  function setHover(handle) {
    paint();
    if (!handle) return;
    const hover = cssThreeColor(THREE, '--handle-hover');
    for (let i = 0; i < pickables.length; i += 1) {
      if (pickables[i].userData.handle === handle) pickables[i].material.color.copy(hover);
    }
  }

  return { group: group, pickables: pickables, paint: paint, setHover: setHover };
}

export function makeOverlays(THREE) {
  function mat(opacity) {
    return new THREE.MeshBasicMaterial({
      transparent: true,
      opacity: opacity,
      depthWrite: false,
      polygonOffset: true,
      polygonOffsetFactor: -2,
      polygonOffsetUnits: -2,
      side: THREE.DoubleSide,
    });
  }
  const selFace = new THREE.Mesh(new THREE.BufferGeometry(), mat(0.72));
  const hoverFace = new THREE.Mesh(new THREE.BufferGeometry(), mat(0.4));
  // Whole-item fill sits under the gizmo. 0.72 washes the cylinder arrows out.
  selFace.userData.faceOpacity = 0.72;
  selFace.userData.itemOpacity = 0.35;
  const selLines = new THREE.LineSegments(
    new THREE.BufferGeometry(),
    new THREE.LineBasicMaterial({ depthTest: false, transparent: true, opacity: 1 })
  );
  const hoverLines = new THREE.LineSegments(
    new THREE.BufferGeometry(),
    new THREE.LineBasicMaterial({ depthTest: false, transparent: true, opacity: 1 })
  );
  const selPoints = new THREE.Points(
    new THREE.BufferGeometry(),
    new THREE.PointsMaterial({ size: 10, sizeAttenuation: false, depthTest: false })
  );
  const hoverPoints = new THREE.Points(
    new THREE.BufferGeometry(),
    new THREE.PointsMaterial({ size: 9, sizeAttenuation: false, depthTest: false })
  );
  const nodes = [selFace, hoverFace, selLines, hoverLines, selPoints, hoverPoints];
  for (let i = 0; i < nodes.length; i += 1) {
    nodes[i].renderOrder = 5;
    nodes[i].frustumCulled = false;
  }
  function syncColors() {
    const sel = cssThreeColor(THREE, '--sel-color');
    const hover = cssThreeColor(THREE, '--hover-color');
    selFace.material.color.copy(sel);
    selLines.material.color.copy(sel);
    selPoints.material.color.copy(sel);
    hoverFace.material.color.copy(hover);
    hoverLines.material.color.copy(hover);
    hoverPoints.material.color.copy(hover);
  }
  function setBuffer(obj, positions, itemSize) {
    obj.geometry.dispose();
    const geo = new THREE.BufferGeometry();
    if (positions && positions.length) {
      geo.setAttribute('position', new THREE.BufferAttribute(positions, itemSize));
    }
    obj.geometry = geo;
    obj.visible = !!(positions && positions.length);
  }
  return {
    selFace: selFace,
    hoverFace: hoverFace,
    selLines: selLines,
    hoverLines: hoverLines,
    selPoints: selPoints,
    hoverPoints: hoverPoints,
    nodes: nodes,
    syncColors: syncColors,
    setBuffer: setBuffer,
  };
}

export function faceVertexArray(vertices, triangles, triList) {
  const out = [];
  for (let i = 0; i < triList.length; i += 1) {
    const tri = triangles[triList[i]];
    if (!tri) continue;
    for (let k = 0; k < 3; k += 1) {
      const p = vertices[tri[k]];
      out.push(p[0], p[2], p[1]);
    }
  }
  return new Float32Array(out);
}

export function polylineArray(polylines) {
  const out = [];
  for (let i = 0; i < polylines.length; i += 1) {
    const pts = polylines[i];
    for (let k = 0; k + 1 < pts.length; k += 1) {
      out.push(pts[k][0], pts[k][2], pts[k][1], pts[k + 1][0], pts[k + 1][2], pts[k + 1][1]);
    }
  }
  return new Float32Array(out);
}

export function pointArray(points) {
  const out = [];
  for (let i = 0; i < points.length; i += 1) {
    out.push(points[i][0], points[i][2], points[i][1]);
  }
  return new Float32Array(out);
}

export function axisVector(kind) {
  const dir = GIZMO_AXIS_THREE[kind];
  return dir ? dir.slice() : null;
}

export function dragPlaneNormal(kind, cameraDir) {
  if (kind === 'xy') return [0, 1, 0];
  if (kind === 'yz') return [1, 0, 0];
  if (kind === 'zx') return [0, 0, 1];
  if (kind === 'view') return [cameraDir[0], cameraDir[1], cameraDir[2]];
  const axis = GIZMO_AXIS_THREE[kind];
  if (!axis) return [0, 1, 0];
  const cx = cameraDir[0];
  const cy = cameraDir[1];
  const cz = cameraDir[2];
  let sx = axis[1] * cz - axis[2] * cy;
  let sy = axis[2] * cx - axis[0] * cz;
  let sz = axis[0] * cy - axis[1] * cx;
  if (sx * sx + sy * sy + sz * sz < 1e-8) {
    sx = axis[1];
    sy = axis[2] - axis[0];
    sz = -axis[1];
  }
  const nx = sy * axis[2] - sz * axis[1];
  const ny = sz * axis[0] - sx * axis[2];
  const nz = sx * axis[1] - sy * axis[0];
  const len = Math.hypot(nx, ny, nz) || 1;
  return [nx / len, ny / len, nz / len];
}
