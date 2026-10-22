// Move / rotate / scale gizmo and selection overlays. Colours come from CSS variables.
// CAD millimetres are Z-up. The viewport is three.js Y-up, so cad (x, y, z)
// is drawn as three (x, z, y). Axis Z is up and uses --axis-z.

export const GIZMO_AXIS_THREE = {
  x: [1, 0, 0],
  y: [0, 0, 1],
  z: [0, 1, 0],
};

export const GIZMO_MODES = ['move', 'rotate', 'scale'];

// Tap vs drag. Under 8 CSS px of movement is a tap. Team choice, 2026-10-21
// (Android touch slop 8 dp). Source: research/mobile-touch-cad.md.
export const TAP_SLOP_PX = 8;

// Finger gizmo pick zone. At least 44 CSS px square (WCAG 2.5.5 / Apple HIG).
// Team choice, 2026-10-21. Mesh picking stays on PICK_TOLERANCE_PX / TOUCH_PICK_TOLERANCE_PX.
export const GIZMO_TOUCH_ZONE_PX = 44;

// Snap and steppers. Team choice (Chief, 2026-10-21 20:48 MT).
export const SNAP_MM = 1;
export const SNAP_DEG = 15;
export const STEPPER_MM = 1;
export const STEPPER_FINE_MM = 0.1;
export const STEPPER_DEG = 15;
export const STEPPER_FINE_DEG = 1;
export const LONG_PRESS_MS = 400;
export const MIN_SIZE_MM = 0.1;

export function snapNumber(value, step, on) {
  const n = Number(value);
  if (!on || !(Number(step) > 0) || !Number.isFinite(n)) return n;
  return Math.round(n / step) * step;
}

export function isTapMove(dx, dy, slop) {
  const limit = slop == null ? TAP_SLOP_PX : slop;
  return Math.hypot(dx, dy) < limit;
}

export function cadEulerToThreeQuaternion(THREE, rxDeg, ryDeg, rzDeg) {
  const qx = new THREE.Quaternion().setFromAxisAngle(
    new THREE.Vector3(GIZMO_AXIS_THREE.x[0], GIZMO_AXIS_THREE.x[1], GIZMO_AXIS_THREE.x[2]),
    (Number(rxDeg) || 0) * Math.PI / 180
  );
  const qy = new THREE.Quaternion().setFromAxisAngle(
    new THREE.Vector3(GIZMO_AXIS_THREE.y[0], GIZMO_AXIS_THREE.y[1], GIZMO_AXIS_THREE.y[2]),
    (Number(ryDeg) || 0) * Math.PI / 180
  );
  const qz = new THREE.Quaternion().setFromAxisAngle(
    new THREE.Vector3(GIZMO_AXIS_THREE.z[0], GIZMO_AXIS_THREE.z[1], GIZMO_AXIS_THREE.z[2]),
    (Number(rzDeg) || 0) * Math.PI / 180
  );
  return new THREE.Quaternion().multiply(qz).multiply(qy).multiply(qx);
}

export function handleKind(handle) {
  if (handle === 'x' || handle === 'y' || handle === 'z' || handle === 'xy' || handle === 'yz' || handle === 'zx' || handle === 'view') {
    return 'move';
  }
  if (handle === 'rx' || handle === 'ry' || handle === 'rz') return 'rotate';
  if (handle === 'sx' || handle === 'sy' || handle === 'sz') return 'scale';
  return '';
}

export function handleAxis(handle) {
  if (!handle) return '';
  if (handle === 'x' || handle === 'rx' || handle === 'sx') return 'x';
  if (handle === 'y' || handle === 'ry' || handle === 'sy') return 'y';
  if (handle === 'z' || handle === 'rz' || handle === 'sz') return 'z';
  return '';
}

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

function localAxisPoints(THREE, dir, from, to, count) {
  const pts = [];
  for (let i = 0; i < count; i += 1) {
    const t = from + (to - from) * (i / Math.max(count - 1, 1));
    pts.push(new THREE.Vector3(dir[0] * t, dir[1] * t, dir[2] * t));
  }
  return pts;
}

function localRingPoints(THREE, radius, count) {
  const pts = [];
  for (let i = 0; i < count; i += 1) {
    const a = (i / count) * Math.PI * 2;
    pts.push(new THREE.Vector3(Math.cos(a) * radius, Math.sin(a) * radius, 0));
  }
  return pts;
}

export function makeGizmo(THREE) {
  const group = new THREE.Group();
  const move = new THREE.Group();
  const rotate = new THREE.Group();
  const scale = new THREE.Group();
  group.add(move);
  group.add(rotate);
  group.add(scale);
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
    const shaftMesh = addMesh(THREE, move, pickables, shaft, colorName, handle);
    shaftMesh.quaternion.copy(quat);
    shaftMesh.position.set(dir[0] * 6, dir[1] * 6, dir[2] * 6);
    shaftMesh.userData.pickLocal = localAxisPoints(THREE, [0, 1, 0], -6, 6, 8);
    const headMesh = addMesh(THREE, move, pickables, head, colorName, handle);
    headMesh.quaternion.copy(quat);
    headMesh.position.set(dir[0] * 13.2, dir[1] * 13.2, dir[2] * 13.2);
    headMesh.userData.pickLocal = [new THREE.Vector3(0, 0, 0)];
  }

  arrow(x, '--axis-x', 'x');
  arrow(y, '--axis-y', 'y');
  arrow(z, '--axis-z', 'z');

  function planeHandle(handle, colorName, geometry, ox, oy, oz) {
    const mesh = addMesh(THREE, move, pickables, geometry, colorName, handle);
    mesh.position.set(ox, oy, oz);
    mesh.material.opacity = 0.45;
    mesh.userData.pickLocal = [new THREE.Vector3(0, 0, 0)];
  }

  // Planar paddles sit in the positive quadrant of each CAD plane.
  // CAD XY is three XZ (thin in three Y). CAD YZ is thin in three X. CAD ZX is thin in three Z.
  planeHandle('xy', '--axis-z', new THREE.BoxGeometry(4.2, 0.28, 4.2), 5.2, 0.35, 5.2);
  planeHandle('yz', '--axis-x', new THREE.BoxGeometry(0.28, 4.2, 4.2), 0.35, 5.2, 5.2);
  planeHandle('zx', '--axis-y', new THREE.BoxGeometry(4.2, 4.2, 0.28), 5.2, 5.2, 0.35);

  const centre = addMesh(
    THREE,
    move,
    pickables,
    new THREE.SphereGeometry(1.15, 16, 12),
    '--centre-color',
    'view'
  );
  centre.material.opacity = 0.9;
  centre.userData.pickLocal = [new THREE.Vector3(0, 0, 0)];

  function ring(dir, colorName, handle) {
    const torus = new THREE.TorusGeometry(9.5, 0.32, 12, 48);
    const mesh = addMesh(THREE, rotate, pickables, torus, colorName, handle);
    mesh.quaternion.setFromUnitVectors(
      new THREE.Vector3(0, 0, 1),
      new THREE.Vector3(dir[0], dir[1], dir[2])
    );
    mesh.material.opacity = 0.92;
    mesh.userData.pickLocal = localRingPoints(THREE, 9.5, 32);
  }

  ring(x, '--axis-x', 'rx');
  ring(y, '--axis-y', 'ry');
  ring(z, '--axis-z', 'rz');

  function scaleHandle(dir, colorName, handle) {
    const cube = addMesh(THREE, scale, pickables, new THREE.BoxGeometry(2.2, 2.2, 2.2), colorName, handle);
    cube.position.set(dir[0] * 13.2, dir[1] * 13.2, dir[2] * 13.2);
    cube.userData.pickLocal = [new THREE.Vector3(0, 0, 0)];
    const shaft = addMesh(THREE, scale, pickables, new THREE.CylinderGeometry(0.22, 0.22, 11, 8), colorName, handle);
    const quat = new THREE.Quaternion().setFromUnitVectors(
      new THREE.Vector3(0, 1, 0),
      new THREE.Vector3(dir[0], dir[1], dir[2])
    );
    shaft.quaternion.copy(quat);
    shaft.position.set(dir[0] * 6, dir[1] * 6, dir[2] * 6);
    shaft.material.opacity = 0.7;
    shaft.userData.pickLocal = localAxisPoints(THREE, [0, 1, 0], -5.5, 5.5, 8);
  }

  scaleHandle(x, '--axis-x', 'sx');
  scaleHandle(y, '--axis-y', 'sy');
  scaleHandle(z, '--axis-z', 'sz');

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

  function setMode(mode) {
    const next = mode === 'rotate' || mode === 'scale' ? mode : 'move';
    move.visible = next === 'move';
    rotate.visible = next === 'rotate';
    scale.visible = next === 'scale';
    return next;
  }

  setMode('move');

  return {
    group: group,
    pickables: pickables,
    paint: paint,
    setHover: setHover,
    setMode: setMode,
    modes: { move: move, rotate: rotate, scale: scale },
  };
}

function meshAncestryVisible(mesh) {
  let node = mesh;
  while (node) {
    if (node.visible === false) return false;
    node = node.parent;
  }
  return true;
}

export function pickGizmoHandle(pickables, camera, px, py, width, height, zonePx) {
  const zone = zonePx == null ? GIZMO_TOUCH_ZONE_PX : zonePx;
  const half = zone / 2;
  let best = '';
  let bestD = half + 1e-6;
  let Vector3 = null;
  for (let i = 0; i < pickables.length; i += 1) {
    const mesh = pickables[i];
    if (!meshAncestryVisible(mesh)) continue;
    if (!Vector3 && mesh.position && mesh.position.constructor) Vector3 = mesh.position.constructor;
    if (!Vector3) continue;
    const samples = mesh.userData.pickLocal && mesh.userData.pickLocal.length
      ? mesh.userData.pickLocal
      : [mesh.position.clone ? new Vector3(0, 0, 0) : { x: 0, y: 0, z: 0 }];
    for (let s = 0; s < samples.length; s += 1) {
      const local = samples[s];
      const ndc = local.clone ? local.clone() : new Vector3(local.x, local.y, local.z);
      mesh.localToWorld(ndc);
      ndc.project(camera);
      if (ndc.z < -1 || ndc.z > 1) continue;
      const sx = (ndc.x * 0.5 + 0.5) * width;
      const sy = (-ndc.y * 0.5 + 0.5) * height;
      const d = Math.max(Math.abs(sx - px), Math.abs(sy - py));
      if (d <= bestD) {
        bestD = d;
        best = mesh.userData.handle || '';
      }
    }
  }
  return best;
}

export function gizmoHandleZones(pickables, camera, width, height, zonePx) {
  const zone = zonePx == null ? GIZMO_TOUCH_ZONE_PX : zonePx;
  const zones = [];
  let Vector3 = null;
  for (let i = 0; i < pickables.length; i += 1) {
    const mesh = pickables[i];
    if (!meshAncestryVisible(mesh)) continue;
    if (!Vector3 && mesh.position && mesh.position.constructor) Vector3 = mesh.position.constructor;
    if (!Vector3) continue;
    const samples = mesh.userData.pickLocal && mesh.userData.pickLocal.length
      ? mesh.userData.pickLocal
      : [new Vector3(0, 0, 0)];
    let minX = Infinity;
    let minY = Infinity;
    let maxX = -Infinity;
    let maxY = -Infinity;
    let any = false;
    for (let s = 0; s < samples.length; s += 1) {
      const ndc = samples[s].clone ? samples[s].clone() : new Vector3(samples[s].x, samples[s].y, samples[s].z);
      mesh.localToWorld(ndc);
      ndc.project(camera);
      if (ndc.z < -1 || ndc.z > 1) continue;
      const sx = (ndc.x * 0.5 + 0.5) * width;
      const sy = (-ndc.y * 0.5 + 0.5) * height;
      any = true;
      if (sx < minX) minX = sx;
      if (sy < minY) minY = sy;
      if (sx > maxX) maxX = sx;
      if (sy > maxY) maxY = sy;
    }
    if (!any) continue;
    const pad = zone / 2;
    const w = Math.max(zone, (maxX - minX) + zone);
    const h = Math.max(zone, (maxY - minY) + zone);
    zones.push({
      handle: mesh.userData.handle || '',
      x: (minX + maxX) / 2,
      y: (minY + maxY) / 2,
      w: w,
      h: h,
      minX: minX - pad,
      minY: minY - pad,
      maxX: maxX + pad,
      maxY: maxY + pad,
    });
  }
  let minPx = zones.length ? Infinity : 0;
  for (let i = 0; i < zones.length; i += 1) {
    const m = Math.min(zones[i].w, zones[i].h);
    if (m < minPx) minPx = m;
  }
  if (!Number.isFinite(minPx)) minPx = 0;
  return { minPx: minPx, zones: zones };
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
  const axis = handleAxis(kind) || kind;
  const dir = GIZMO_AXIS_THREE[axis];
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
