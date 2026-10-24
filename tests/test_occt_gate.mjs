import { existsSync, mkdirSync, readFileSync, writeFileSync } from 'node:fs';
import { pathToFileURL, fileURLToPath } from 'node:url';
import path from 'node:path';

const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..');
const libDir = path.join(root, 'builds', 'libcascade', 'dist');
const libFiles = ['init.single.js', 'opencascade_single.js', 'opencascade_single.wasm'];
const missingLib = libFiles.filter((name) => !existsSync(path.join(libDir, name)));

function envSet(name) {
  const value = process.env[name];
  return value !== undefined && String(value).trim() !== '';
}

if (missingLib.length) {
  const message =
    'occt_gate: libcascade is missing (' +
    missingLib.join(', ') +
    ') under builds/libcascade/dist. Run: python web/fetch-libcascade.py';
  if (envSet('CI') || envSet('GITHUB_ACTIONS')) {
    console.error('FAIL ' + message);
    console.error('CI must not skip occt_gate when libcascade is missing.');
    process.exit(1);
  }
  console.error('SKIP ' + message);
  process.exit(77);
}

const initUrl = pathToFileURL(path.join(libDir, 'init.single.js')).href;
const gateUrl = pathToFileURL(path.join(root, 'web', 'occt-gate.mjs')).href;

const primUrl = pathToFileURL(path.join(root, 'web', 'occt-primitives.mjs')).href;
const opsUrl = pathToFileURL(path.join(root, 'web', 'occt-ops.mjs')).href;
const selUrl = pathToFileURL(path.join(root, 'web', 'selection.mjs')).href;
const viewUrl = pathToFileURL(path.join(root, 'web', 'viewport-selection.mjs')).href;

const { createInstance } = await import(initUrl);
const { checkOcctGate, closedBoxMesh, openBoxMesh, box20Mesh } = await import(gateUrl);
const { buildBox, buildCylinder, buildDisc, PLACEHOLDER_BOX_MM, PLACEHOLDER_CYLINDER_MM, PLACEHOLDER_DISC_MM, BOX_EDGE_MM, CYLINDER_DIAMETER_MM, CYLINDER_HEIGHT_MM, DISC_DIAMETER_MM, DISC_THICKNESS_MM, SPHERE_DIAMETER_MM, inspectSolid, checkMeshWatertight, TESSELLATION_DEFLECTION_MM, TESSELLATION_ANGULAR, TESSELLATION_RELATIVE, TESSELLATION_CONTROL_SURFACE, TESSELLATION_IN_PARALLEL } = await import(primUrl);
const ops = await import(opsUrl);
const projectUrl = pathToFileURL(path.join(root, 'web', 'project-file.mjs')).href;
const projectFile = await import(projectUrl);
const { normalizeBox, normalizeCylinder, normalizeDisc } = await import(primUrl);
const blinkPath = path.join(root, 'tests', 'fixtures', 'blink.mjs');
const blinkUrl = pathToFileURL(blinkPath).href;
let blinkMod = null;
if (existsSync(blinkPath)) {
  try { blinkMod = await import(blinkUrl); } catch (e) { blinkMod = null; }
}
const { applyPointerSelection, groupMeshFaces, modeFromHotkey, isTypingTarget, isViewportHotkeyTarget, selectionHotkeyAllowed, PICK_TOLERANCE_PX, TOUCH_PICK_TOLERANCE_PX } = await import(selUrl);
const { threeDeltaToCad, GIZMO_AXIS_THREE, TAP_SLOP_PX, GIZMO_TOUCH_ZONE_PX, SNAP_MM, SNAP_DEG, STEPPER_MM, STEPPER_FINE_MM, STEPPER_DEG, STEPPER_FINE_DEG, LONG_PRESS_MS, snapNumber, isTapMove, handleKind, GIZMO_MODES, faceFrameFromTriangles, viewerBuffersFromCad, viewerVertexNormals } = await import(viewUrl);
const blinkJsonPath = path.join(root, 'tests', 'fixtures', 'blink.json');
let blinkFile = null;
if (existsSync(blinkJsonPath)) {
  try { blinkFile = JSON.parse(readFileSync(blinkJsonPath, 'utf8')); } catch (_err) { blinkFile = null; }
}

let failures = 0;

function expect(name, ok) {
  if (ok) {
    return;
  }
  console.error(name + ' failed');
  failures += 1;
}

// Viewer mesh of a countersunk hole. Normals must point out of the material
// (toward the hole axis) and agree with the triangle winding.
function viewerCutNormalReport(mesh, holePoints, plateSz, csRadius) {
  const built = viewerBuffersFromCad(mesh.vertices, mesh.triangles);
  const normals = viewerVertexNormals(built.positions, built.indices);
  const positions = built.positions;
  const indices = built.indices;
  let walls = 0;
  let into = 0;
  let disagree = 0;
  let topUp = 0;
  let topDown = 0;
  function xyz(i) {
    return [positions[i * 3], positions[i * 3 + 1], positions[i * 3 + 2]];
  }
  for (let t = 0; t + 2 < indices.length; t += 3) {
    const ia = indices[t];
    const ib = indices[t + 1];
    const ic = indices[t + 2];
    const a = xyz(ia);
    const b = xyz(ib);
    const c = xyz(ic);
    const cx = (a[0] + b[0] + c[0]) / 3;
    const cy = (a[1] + b[1] + c[1]) / 3;
    const cz = (a[2] + b[2] + c[2]) / 3;
    const ux = b[0] - a[0];
    const uy = b[1] - a[1];
    const uz = b[2] - a[2];
    const vx = c[0] - a[0];
    const vy = c[1] - a[1];
    const vz = c[2] - a[2];
    let fnx = uy * vz - uz * vy;
    let fny = uz * vx - ux * vz;
    let fnz = ux * vy - uy * vx;
    const fl = Math.hypot(fnx, fny, fnz) || 1;
    fnx /= fl;
    fny /= fl;
    fnz /= fl;
    let nearest = 1e9;
    let radial = [0, 0];
    for (let h = 0; h < holePoints.length; h += 1) {
      const hole = holePoints[h];
      const dx = cx - hole[0];
      const dz = cz - hole[1];
      const dist = Math.hypot(dx, dz);
      if (dist < nearest) {
        nearest = dist;
        radial = [dx, dz];
      }
    }
    const rl = Math.hypot(radial[0], radial[1]) || 1;
    const faceRadial = (fnx * radial[0] + fnz * radial[1]) / rl;
    if (cy > plateSz - 0.3 && nearest > csRadius + 1 && fny > 0.9) topUp += 1;
    if (cy > plateSz - 0.3 && nearest > csRadius + 1 && fny < -0.9) topDown += 1;
    if (!(nearest < csRadius + 0.35) || !(nearest > 0.4)) continue;
    if (!(cy > 0.25) || !(cy < plateSz - 0.15)) continue;
    if (Math.abs(faceRadial) < 0.2) continue;
    walls += 1;
    const ids = [ia, ib, ic];
    for (let k = 0; k < 3; k += 1) {
      const p = xyz(ids[k]);
      const nx = normals[ids[k] * 3];
      const ny = normals[ids[k] * 3 + 1];
      const nz = normals[ids[k] * 3 + 2];
      let best = 1e9;
      let rv = [0, 0];
      for (let h = 0; h < holePoints.length; h += 1) {
        const hole = holePoints[h];
        const dx = p[0] - hole[0];
        const dz = p[2] - hole[1];
        const dist = Math.hypot(dx, dz);
        if (dist < best) {
          best = dist;
          rv = [dx, dz];
        }
      }
      const rlen = Math.hypot(rv[0], rv[1]);
      if (rlen < 0.2) continue;
      if ((nx * rv[0] + nz * rv[1]) / rlen > 1e-3) into += 1;
      if (nx * fnx + ny * fny + nz * fnz <= 0) disagree += 1;
    }
  }
  if (!walls) return 'no cut-face triangles';
  if (!topUp || topDown) return 'top face normal up ' + topUp + ' down ' + topDown;
  if (into) return into + ' vertex normals point into the solid';
  if (disagree) return disagree + ' vertex normals disagree with winding';
  return '';
}

// Countersink mouths on the plate top. A seam may split one circle into two arcs.
function topCountersinkCircles(oc, shape, zTop, diameterMm) {
  const trash = [];
  function track(obj) {
    if (obj) trash.push(obj);
    return obj;
  }
  const groups = new Map();
  const seen = new Set();
  let ok = true;
  try {
    const explorer = track(new oc.TopExp_Explorer(shape, oc.TopAbs_ShapeEnum.TopAbs_EDGE));
    while (explorer.More()) {
      const edge = track(oc.TopoDS.Edge(explorer.Current()));
      const adaptor = track(new oc.BRepAdaptor_Curve(edge));
      if (adaptor.GetType() === oc.GeomAbs_CurveType.GeomAbs_Circle) {
        const circ = track(adaptor.Circle());
        const radius = circ.Radius();
        const loc = track(circ.Location());
        const axis = track(circ.Axis());
        const dir = track(axis.Direction());
        const atTop = Math.abs(loc.Z() - zTop) <= 1e-6 && Math.abs(Math.abs(dir.Z()) - 1) <= 1e-6;
        if (atTop) {
          const diaOk = Math.abs(2 * radius - diameterMm) <= 1e-6;
          if (!diaOk) ok = false;
          const u0 = adaptor.FirstParameter();
          const u1 = adaptor.LastParameter();
          const mid = track(adaptor.Value((u0 + u1) * 0.5));
          const edgeKey = [mid.X(), mid.Y(), mid.Z(), u0, u1].map(function (n) { return Math.round(n * 1e6); }).join(',');
          if (!seen.has(edgeKey)) {
            seen.add(edgeKey);
            const ckey = [loc.X(), loc.Y(), loc.Z()].map(function (n) { return Math.round(n * 1e6); }).join(',');
            const group = groups.get(ckey) || { arcs: 0, diaOk: true };
            group.arcs += 1;
            group.diaOk = group.diaOk && diaOk;
            groups.set(ckey, group);
          }
        }
      }
      explorer.Next();
    }
  } catch (err) {
    console.error('top countersink circles ' + (err && err.message ? err.message : String(err)));
    ok = false;
  } finally {
    for (let i = trash.length - 1; i >= 0; i -= 1) {
      try {
        if (trash[i] && typeof trash[i].delete === 'function') trash[i].delete();
      } catch (_err) {
        // Already released.
      }
    }
  }
  groups.forEach(function (group) {
    if (group.arcs < 1 || group.arcs > 2 || !group.diaOk) ok = false;
  });
  return { ok: ok, circles: groups.size };
}

const oc = await createInstance();

const closed = checkOcctGate(oc, closedBoxMesh());
expect('closed_box pass', closed.pass === true);
expect('closed_box valid', closed.valid === true);
expect('closed_box free edges', closed.freeEdges === 0);
expect('closed_box pass sentence', typeof closed.message === 'string' && closed.message.startsWith('PASS:'));

const open = checkOcctGate(oc, openBoxMesh());
expect('open_box fail', open.pass === false);
expect('open_box has free edges', open.freeEdges > 0);
expect('open_box fail sentence', typeof open.message === 'string' && open.message.startsWith('FAIL:'));
expect('open_box names FreeBounds', open.message.includes('ShapeAnalysis_FreeBounds'));

const box20 = checkOcctGate(oc, box20Mesh());
expect('box20 pass', box20.pass === true && box20.freeEdges === 0);

const empty = checkOcctGate(oc, { vertices: [], triangles: [] });
expect('empty fail', empty.pass === false);

const box = buildBox(oc, null);
expect('box gate', box.gate.pass === true && box.gate.freeEdges === 0);
expect('box watertight', box.watertight.pass === true);
expect('box units mm', box.units === 'mm');
expect('box faces ' + box.topology.faces.length, box.topology.faces.length === 6);
expect('box vertices ' + box.topology.vertices.length, box.topology.vertices.length === 8);
expect('box edges ' + box.topology.edges.length, box.topology.edges.length === 12);
expect('box defaults', BOX_EDGE_MM === 20 && PLACEHOLDER_BOX_MM.sx === 20 && PLACEHOLDER_BOX_MM.sy === 20 && PLACEHOLDER_BOX_MM.sz === 20 && box.params.sx === 20 && box.params.sy === 20 && box.params.sz === 20 && PLACEHOLDER_BOX_MM.tbd === undefined);

const cyl = buildCylinder(oc, null);
expect('cylinder gate', cyl.gate.pass === true && cyl.gate.freeEdges === 0);
expect('cylinder watertight', cyl.watertight.pass === true);
expect('cylinder units mm', cyl.units === 'mm');
expect('cylinder faces ' + cyl.topology.faces.length, cyl.topology.faces.length === 3);
expect('cylinder vertices ' + cyl.topology.vertices.length, cyl.topology.vertices.length === 2);
expect('cylinder edges ' + cyl.topology.edges.length, cyl.topology.edges.length === 3);
expect('cylinder defaults', CYLINDER_DIAMETER_MM === 20 && CYLINDER_HEIGHT_MM === 20 && PLACEHOLDER_CYLINDER_MM.radius === 10 && PLACEHOLDER_CYLINDER_MM.height === 20 && cyl.params.radius === 10 && cyl.params.height === 20 && cyl.params.axis === 'Z' && PLACEHOLDER_CYLINDER_MM.tbd === undefined);
expect('sphere default only', SPHERE_DIAMETER_MM === 20);

const disc = buildDisc(oc, null);
expect('disc gate', disc.gate.pass === true && disc.gate.freeEdges === 0);
expect('disc watertight', disc.watertight.pass === true && disc.units === 'mm');
expect('disc kind', disc.kind === 'disc');
expect('disc defaults', DISC_DIAMETER_MM === 18 && DISC_THICKNESS_MM === 4 && PLACEHOLDER_DISC_MM.diameter === 18 && PLACEHOLDER_DISC_MM.thickness === 4 && PLACEHOLDER_DISC_MM.cz === 2 && disc.params.diameter === 18 && disc.params.thickness === 4 && disc.params.axis === 'Z');
expect('disc faces ' + disc.topology.faces.length, disc.topology.faces.length === 3);

const cylX = buildCylinder(oc, { axis: 'X' });
expect('cylinder X gate', cylX.gate.pass === true && cylX.watertight.pass === true && cylX.units === 'mm');

const bad = buildBox(oc, { sx: 0, sy: 20, sz: 20 });
expect('non-positive box fails', bad.gate.pass === false && bad.mesh.triangles.length === 0);

const grouped = groupMeshFaces(closedBoxMesh().vertices, closedBoxMesh().triangles);
expect('mesh faces ' + grouped.faces.length, grouped.faces.length === 6);
expect('mesh edges ' + grouped.edges.length, grouped.edges.length === 12);
expect('mesh vertices ' + grouped.vertices.length, grouped.vertices.length === 8);

const replaced = applyPointerSelection('face', ['f0'], 'f1', {});
expect('click replaces', replaced.ids.length === 1 && replaced.ids[0] === 'f1' && replaced.all === false);
const added = applyPointerSelection('face', ['f0'], 'f1', { shift: true });
expect('shift adds', added.ids.length === 2 && added.ids[0] === 'f0' && added.ids[1] === 'f1');
const removed = applyPointerSelection('face', ['f0', 'f1'], 'f0', { ctrl: true });
expect('ctrl removes', removed.ids.length === 1 && removed.ids[0] === 'f1');
const allFaces = applyPointerSelection('face', ['f0'], null, {});
expect('empty face is all', allFaces.ids.length === 0 && allFaces.all === true && allFaces.highlight === false);
const clearedItem = applyPointerSelection('item', ['item'], null, {});
expect('empty item is not all', clearedItem.ids.length === 0 && clearedItem.all === false && clearedItem.highlight === false);

expect('hotkey 1', modeFromHotkey('1') === 'vertex');
expect('hotkey 2', modeFromHotkey('2') === 'edge');
expect('hotkey 3', modeFromHotkey('3') === 'face');
expect('hotkey 4 item', modeFromHotkey('4') === 'item');
expect('hotkey 5', modeFromHotkey('5') === 'item');

function fakeEl(tag, extra) {
  const el = Object.assign({
    tagName: tag,
    nodeType: 1,
    id: '',
    isContentEditable: false,
    parentElement: null,
    getAttribute: function (name) {
      if (name === 'contenteditable') {
        if (extra && Object.prototype.hasOwnProperty.call(extra, 'contentEditableAttr')) {
          return extra.contentEditableAttr;
        }
        return null;
      }
      return null;
    }
  }, extra || {});
  return el;
}
const bodyEl = fakeEl('BODY');
const inputEl = fakeEl('INPUT');
const textareaEl = fakeEl('TEXTAREA');
const selectEl = fakeEl('SELECT');
const editEl = fakeEl('DIV', { isContentEditable: true, contentEditableAttr: 'true' });
const editChild = fakeEl('SPAN');
editChild.parentElement = editEl;
const canvasEl = fakeEl('CANVAS', { id: 'canvas' });
const viewportEl = fakeEl('MAIN', { id: 'viewport' });
expect('typing input', isTypingTarget(inputEl) === true);
expect('typing textarea', isTypingTarget(textareaEl) === true);
expect('typing select', isTypingTarget(selectEl) === true);
expect('typing contenteditable', isTypingTarget(editEl) === true);
expect('typing contenteditable child', isTypingTarget(editChild) === true);
expect('body is not typing', isTypingTarget(bodyEl) === false);
expect('viewport is not typing', isTypingTarget(viewportEl) === false);
expect('canvas hotkey target', isViewportHotkeyTarget(canvasEl) === true);
expect('viewport hotkey target', isViewportHotkeyTarget(viewportEl) === true);
expect('body is not viewport hotkey', isViewportHotkeyTarget(bodyEl) === false);
expect('input blocks digit hotkey', selectionHotkeyAllowed('1', inputEl, inputEl) === false);
expect('textarea blocks digit hotkey', selectionHotkeyAllowed('4', textareaEl, textareaEl) === false);
expect('select blocks digit hotkey', selectionHotkeyAllowed('2', selectEl, selectEl) === false);
expect('contenteditable blocks digit hotkey', selectionHotkeyAllowed('3', editEl, editChild) === false);
expect('unfocused digit does not change selection', selectionHotkeyAllowed('1', bodyEl, bodyEl) === false);
expect('unfocused 4 does not change selection', selectionHotkeyAllowed('4', bodyEl, bodyEl) === false);
expect('viewport digit 4 allowed', selectionHotkeyAllowed('4', viewportEl, canvasEl) === true);
expect('canvas digit 1 allowed', selectionHotkeyAllowed('1', canvasEl, canvasEl) === true);
expect('pick tolerance 8', PICK_TOLERANCE_PX === 8);
expect('touch pick tolerance 20', TOUCH_PICK_TOLERANCE_PX === 20);

const cad = threeDeltaToCad(1, 2, 3);
expect('three Y is cad Z', cad.x === 1 && cad.y === 3 && cad.z === 2);
expect('gizmo X', GIZMO_AXIS_THREE.x[0] === 1 && GIZMO_AXIS_THREE.x[1] === 0 && GIZMO_AXIS_THREE.x[2] === 0);
expect('gizmo Y', GIZMO_AXIS_THREE.y[0] === 0 && GIZMO_AXIS_THREE.y[1] === 0 && GIZMO_AXIS_THREE.y[2] === 1);
expect('gizmo Z up', GIZMO_AXIS_THREE.z[0] === 0 && GIZMO_AXIS_THREE.z[1] === 1 && GIZMO_AXIS_THREE.z[2] === 0);
expect('tap slop 8', TAP_SLOP_PX === 8 && isTapMove(5, 5, 8) === true && isTapMove(8, 0, 8) === false);
expect('gizmo zone 44', GIZMO_TOUCH_ZONE_PX === 44);
expect('snap 1mm 15deg', SNAP_MM === 1 && SNAP_DEG === 15 && snapNumber(5.4, 1, true) === 5 && snapNumber(22, 15, true) === 15);
expect('steppers', STEPPER_MM === 1 && STEPPER_FINE_MM === 0.1 && STEPPER_DEG === 15 && STEPPER_FINE_DEG === 1 && LONG_PRESS_MS === 400);
expect('gizmo modes', GIZMO_MODES.join(',') === 'move,rotate,scale' && handleKind('rx') === 'rotate' && handleKind('sx') === 'scale' && handleKind('x') === 'move');
expect('transform euler XYZ', ops.TRANSFORM_EULER === 'XYZ');

const fixture = JSON.parse(readFileSync(path.join(root, 'tests', 'fixtures', 'lbracket.json'), 'utf8'));
const defaults = ops.lbracketSpec(null);
const specFields = [
  'legLengthMm', 'legWidthMm', 'thicknessMm', 'uprightHeightMm',
  'cornerXMm', 'cornerYMm', 'cornerZMm', 'overlapMm',
  'filletRadiusMm', 'chamferDistanceMm', 'innerEdgeMode',
  'chamferEdgeRule', 'filletLivePreview',
];
expect('fixture thickness 4', fixture.thicknessMm === 4);
expect('no tbd constant', ops.LBRACKET_TBD_THICKNESS_MM === undefined && ops.LBRACKET_THICKNESS_MM === 4);
for (let fi = 0; fi < specFields.length; fi += 1) {
  const field = specFields[fi];
  expect('default ' + field, defaults[field] === fixture[field] && defaults[field] === ops.LBRACKET_DEFAULTS[field]);
}
expect('defaults bbox size', fixture.bboxMm[0] === 40 && fixture.bboxMm[1] === 20 && fixture.bboxMm[2] === 40);

const bracket = ops.buildLBracket(oc, null);
expect('lbracket pass', bracket.pass === true);
expect('lbracket units mm', bracket.units === 'mm');
expect('lbracket gate', bracket.gate.pass === true && bracket.gate.freeEdges === 0);
expect('lbracket watertight', bracket.watertight.pass === true);
expect('lbracket last error empty', bracket.lastError === '');
expect('lbracket steps', bracket.log.filter(function (item) { return item.pass; }).map(function (item) { return item.step; }).join(',') === 'fuse,fillet,chamfer');
expect('lbracket from defaults', bracket.params.thicknessMm === defaults.thicknessMm && bracket.params.filletRadiusMm === ops.LBRACKET_INNER_FILLET_RADIUS_MM && bracket.params.chamferDistanceMm === 0.5 && bracket.params.filletLivePreview === false && bracket.params.innerEdgeMode === 'auto');
const bounds = ops.meshBounds(bracket.mesh);
const want = ops.expectedLBracketBounds(bracket.params);
const boundTol = 1e-3;
expect('lbracket xmin ' + bounds.xmin, Math.abs(bounds.xmin - want.xmin) <= boundTol);
expect('lbracket ymin ' + bounds.ymin, Math.abs(bounds.ymin - want.ymin) <= boundTol);
expect('lbracket zmin ' + bounds.zmin, Math.abs(bounds.zmin - want.zmin) <= boundTol);
expect('lbracket xmax ' + bounds.xmax, Math.abs(bounds.xmax - want.xmax) <= boundTol);
expect('lbracket ymax ' + bounds.ymax, Math.abs(bounds.ymax - want.ymax) <= boundTol);
expect('lbracket zmax ' + bounds.zmax, Math.abs(bounds.zmax - want.zmax) <= boundTol);
expect('lbracket bbox 40', Math.abs((bounds.xmax - bounds.xmin) - fixture.bboxMm[0]) <= boundTol);
expect('lbracket bbox 20', Math.abs((bounds.ymax - bounds.ymin) - fixture.bboxMm[1]) <= boundTol);
expect('lbracket bbox 40z', Math.abs((bounds.zmax - bounds.zmin) - fixture.bboxMm[2]) <= boundTol);

const fuseOnly = ops.buildLBracket(oc, { stopAfter: 'fuse' });
expect('fuse-only pass', fuseOnly.pass === true && fuseOnly.lastGoodStep === 'fuse' && fuseOnly.watertight.pass === true);

const tooLarge = ops.buildLBracket(oc, { filletRadiusMm: 100 });
expect('fillet too large fails', tooLarge.pass === false);
expect('fillet too large keeps fuse', tooLarge.lastGoodStep === 'fuse');
expect('fillet too large caught', typeof tooLarge.lastError === 'string'
  && tooLarge.lastError.indexOf('IsDone is false') !== -1
  && tooLarge.lastError.indexOf('Shape() was not called') !== -1);
expect('fillet too large still watertight', tooLarge.gate.pass === true && tooLarge.watertight.pass === true);
expect('fillet too large mesh kept', tooLarge.mesh.triangles.length === fuseOnly.mesh.triangles.length && tooLarge.mesh.triangles.length > 0);

const boxA = ops.makeBoxSolid(oc, 40, 20, 10, [0, 0, 0]);
const boxB = ops.makeBoxSolid(oc, 10, 20, 40, [0, 0, 0]);
const fused = ops.fuseShapes(oc, boxA, boxB);
expect('fuse wrapper', fused.ok === true && fused.shape);
const edgeExp = new oc.TopExp_Explorer(fused.shape, oc.TopAbs_ShapeEnum.TopAbs_EDGE);
const oneEdge = oc.TopoDS.Edge(edgeExp.Current());
const bigFillet = ops.filletEdges(oc, fused.shape, 100, [oneEdge]);
expect('filletEdges too large', bigFillet.ok === false && bigFillet.shape === null
  && bigFillet.error.indexOf('Shape() was not called') !== -1);
const kept = inspectSolid(oc, fused.shape);
expect('caller shape kept after failed fillet', kept.gate.pass === true && kept.watertight.pass === true && kept.units === 'mm');
oneEdge.delete();
edgeExp.delete();
const cut = ops.cutShapes(oc, boxA, boxB);
expect('cut wrapper', cut.ok === true && cut.shape);
const cutView = inspectSolid(oc, cut.shape);
expect('cut gate', cutView.gate.pass === true && cutView.watertight.pass === true && cutView.units === 'mm');
const common = ops.commonShapes(oc, boxA, boxB);
expect('common wrapper', common.ok === true && common.shape);
const commonView = inspectSolid(oc, common.shape);
expect('common gate', commonView.gate.pass === true && commonView.watertight.pass === true && commonView.units === 'mm');
fused.shape.delete();
cut.shape.delete();
common.shape.delete();
boxA.delete();
boxB.delete();

const stlDir = path.join(root, 'builds', 'export');
mkdirSync(stlDir, { recursive: true });
const stlPath = path.join(stlDir, 'lbracket.stl');
writeFileSync(stlPath, ops.binaryStlBytes(bracket.mesh));
const stlBytes = readFileSync(stlPath);
const stlHeader = stlBytes.subarray(0, 80).toString('latin1');
expect('stl header millimeters', stlHeader.indexOf('millimeter') !== -1 && stlHeader.indexOf('solid') !== 0);
const stlCount = stlBytes.readUInt32LE(80);
expect('stl size', stlBytes.length === 84 + stlCount * 50 && stlCount === bracket.mesh.triangles.length);
const stlVertices = [];
const stlTriangles = [];
let stlOffset = 84;
for (let tri = 0; tri < stlCount; tri += 1) {
  stlOffset += 12;
  const corners = [];
  for (let k = 0; k < 3; k += 1) {
    corners.push(stlVertices.length);
    stlVertices.push([
      stlBytes.readFloatLE(stlOffset),
      stlBytes.readFloatLE(stlOffset + 4),
      stlBytes.readFloatLE(stlOffset + 8),
    ]);
    stlOffset += 12;
  }
  stlOffset += 2;
  stlTriangles.push(corners);
}
const weldScale = 1e4;
const weldMap = new Map();
const weldedVertices = [];
function weldId(p) {
  const key = Math.round(p[0] * weldScale) + '|' + Math.round(p[1] * weldScale) + '|' + Math.round(p[2] * weldScale);
  const found = weldMap.get(key);
  if (found !== undefined) return found;
  const id = weldedVertices.length;
  weldedVertices.push(p);
  weldMap.set(key, id);
  return id;
}
const weldedTriangles = stlTriangles.map(function (tri) {
  return [weldId(stlVertices[tri[0]]), weldId(stlVertices[tri[1]]), weldId(stlVertices[tri[2]])];
});
const stlMesh = { vertices: weldedVertices, triangles: weldedTriangles };
const stlTight = checkMeshWatertight(stlMesh);
expect('stl closed mesh', stlTight.pass === true);
const stlBounds = ops.meshBounds(stlMesh);
expect('stl xmin', Math.abs(stlBounds.xmin - want.xmin) <= boundTol);
expect('stl ymin', Math.abs(stlBounds.ymin - want.ymin) <= boundTol);
expect('stl zmin', Math.abs(stlBounds.zmin - want.zmin) <= boundTol);
expect('stl xmax', Math.abs(stlBounds.xmax - want.xmax) <= boundTol);
expect('stl ymax', Math.abs(stlBounds.ymax - want.ymax) <= boundTol);
expect('stl zmax', Math.abs(stlBounds.zmax - want.zmax) <= boundTol);
expect('stl bbox 40x20x40', Math.abs((stlBounds.xmax - stlBounds.xmin) - 40) <= boundTol
  && Math.abs((stlBounds.ymax - stlBounds.ymin) - 20) <= boundTol
  && Math.abs((stlBounds.zmax - stlBounds.zmin) - 40) <= boundTol);

expect('mesh deflection 0.05', TESSELLATION_DEFLECTION_MM === 0.05);
expect('mesh angle 0.2', TESSELLATION_ANGULAR === 0.2);
expect('mesh relative false', TESSELLATION_RELATIVE === false);
expect('mesh control surface', TESSELLATION_CONTROL_SURFACE === true);
expect('mesh not parallel', TESSELLATION_IN_PARALLEL === false);
expect('box mesh path', box.meshPath === 'IMeshTools_Parameters');
expect('box mesh deflection readback', box.meshSettings && Math.abs(box.meshSettings.Deflection - 0.05) < 1e-9);
expect('box mesh angle readback', box.meshSettings && Math.abs(box.meshSettings.Angle - 0.2) < 1e-9);
expect('box mesh relative readback', box.meshSettings && box.meshSettings.Relative === false);
expect('box mesh control readback', box.meshSettings && box.meshSettings.ControlSurfaceDeflection === true);
expect('box mesh parallel readback', box.meshSettings && box.meshSettings.InParallel === false);

function nearBounds(name, got, want, tol) {
  const keys = ['xmin', 'ymin', 'zmin', 'xmax', 'ymax', 'zmax'];
  for (let i = 0; i < keys.length; i += 1) {
    const key = keys[i];
    expect(name + ' ' + key + ' ' + (got ? got[key] : 'none'), !!got && Math.abs(got[key] - want[key]) <= tol);
  }
}

function writeCheckedStl(fileName, mesh, wantBounds, boundsTol) {
  const filePath = path.join(stlDir, fileName);
  writeFileSync(filePath, ops.binaryStlBytes(mesh));
  const bytes = readFileSync(filePath);
  const header = bytes.subarray(0, 80).toString('latin1');
  expect(fileName + ' millimeters', header.indexOf('millimeter') !== -1 && header.indexOf('solid') !== 0);
  const count = bytes.readUInt32LE(80);
  expect(fileName + ' size', bytes.length === 84 + count * 50 && count === mesh.triangles.length && count > 0);
  const vertices = [];
  const triangles = [];
  let offset = 84;
  for (let tri = 0; tri < count; tri += 1) {
    offset += 12;
    const corners = [];
    for (let k = 0; k < 3; k += 1) {
      corners.push(vertices.length);
      vertices.push([
        bytes.readFloatLE(offset),
        bytes.readFloatLE(offset + 4),
        bytes.readFloatLE(offset + 8),
      ]);
      offset += 12;
    }
    offset += 2;
    triangles.push(corners);
  }
  const map = new Map();
  const welded = [];
  function wid(p) {
    const key = Math.round(p[0] * 1e4) + '|' + Math.round(p[1] * 1e4) + '|' + Math.round(p[2] * 1e4);
    const found = map.get(key);
    if (found !== undefined) return found;
    const id = welded.length;
    welded.push(p);
    map.set(key, id);
    return id;
  }
  const weldedTris = triangles.map(function (tri) {
    return [wid(vertices[tri[0]]), wid(vertices[tri[1]]), wid(vertices[tri[2]])];
  });
  const tight = checkMeshWatertight({ vertices: welded, triangles: weldedTris });
  expect(fileName + ' watertight ' + tight.message, tight.pass === true);
  nearBounds(fileName, ops.meshBounds({ vertices: welded, triangles: weldedTris }), wantBounds, boundsTol);
  return { triangles: count, bytes: bytes.length };
}

const overlapVolumes = ops.expectedOverlapVolumes();
const overlapOps = ['union', 'cut', 'intersect'];
const overlapFiles = {
  union: 'boolean-union.stl',
  cut: 'boolean-cut.stl',
  intersect: 'boolean-intersect.stl',
};
for (let oi = 0; oi < overlapOps.length; oi += 1) {
  const opName = overlapOps[oi];
  const made = ops.buildOverlapBoolean(oc, opName, ops.BOOLEAN_OVERLAP_SHIFT_MM);
  expect(opName + ' ok', made.ok === true && made.shape);
  expect(opName + ' gate', made.gate.pass === true && made.watertight.pass === true && made.units === 'mm');
  expect(opName + ' volume ' + made.volumeMm3, Math.abs(made.volumeMm3 - overlapVolumes[opName]) <= ops.BOOLEAN_VOLUME_TOL_MM3);
  nearBounds(opName + ' bounds', made.bounds, ops.expectedOverlapBounds(opName), ops.BOOLEAN_BOUNDS_TOL_MM);
  if (made.ok && made.mesh) writeCheckedStl(overlapFiles[opName], made.mesh, ops.expectedOverlapBounds(opName), 0.05);
  if (made.shape) made.shape.delete();
}

for (let repeat = 0; repeat < 3; repeat += 1) {
  const again = ops.buildOverlapBoolean(oc, 'union', ops.BOOLEAN_OVERLAP_SHIFT_MM);
  expect('repeat union ' + repeat, again.ok === true && Math.abs(again.volumeMm3 - overlapVolumes.union) <= ops.BOOLEAN_VOLUME_TOL_MM3);
  if (again.shape) again.shape.delete();
}

const disjoint = ops.buildOverlapBoolean(oc, 'intersect', ops.BOOLEAN_DISJOINT_SHIFT_MM);
expect('disjoint intersect fails', disjoint.ok === false && disjoint.shape === null);
expect('disjoint message', typeof disjoint.error === 'string' && disjoint.error.indexOf('empty') !== -1 && disjoint.error.indexOf('kept') !== -1);
expect('disjoint inputs kept', disjoint.inputsKept === true);

const demoVolumes = ops.expectedDemoVolumes();
const demoOps = ['union', 'cut', 'intersect'];
for (let di = 0; di < demoOps.length; di += 1) {
  const opName = demoOps[di];
  const demo = ops.buildBooleanDemo(oc, opName);
  expect('demo ' + opName + ' ok', demo.ok === true && demo.op === opName);
  expect('demo ' + opName + ' gate', demo.gate.pass === true && demo.watertight.pass === true && demo.units === 'mm');
  expect('demo ' + opName + ' volume ' + demo.volumeMm3, Math.abs(demo.volumeMm3 - demoVolumes[opName]) <= ops.BOOLEAN_CURVE_VOLUME_TOL_MM3);
  nearBounds('demo ' + opName, demo.bounds, ops.expectedDemoBounds(opName), ops.BOOLEAN_BOUNDS_TOL_MM);
  if (opName === 'cut' && demo.mesh) {
    const demoStl = writeCheckedStl('boolean-demo.stl', demo.mesh, ops.expectedDemoBounds('cut'), 0.05);
    console.log('boolean-demo triangles', demoStl.triangles, 'bytes', demoStl.bytes);
  }
  if (demo.shape) demo.shape.delete();
}

const opsSrc = readFileSync(path.join(root, 'web', 'occt-ops.mjs'), 'utf8');
const glueCalls = opsSrc.split('algo.SetGlue(').length - 1;
expect('SetGlue once', glueCalls === 1);
expect('flush fuse helper', opsSrc.indexOf('export function fuseFlushShapes') !== -1);
expect('plain fuse stays glue-free', opsSrc.indexOf("booleanOp(oc, 'fuse', shapeA, shapeB, null)") !== -1);

const primBoxBounds = { xmin: -10, ymin: -10, zmin: 0, xmax: 10, ymax: 10, zmax: 20 };
const primCylBounds = { xmin: -10, ymin: -10, zmin: 0, xmax: 10, ymax: 10, zmax: 20 };
const primDiscBounds = { xmin: -9, ymin: -9, zmin: 0, xmax: 9, ymax: 9, zmax: 4 };
const primBoxStl = writeCheckedStl('prim-box.stl', box.mesh, primBoxBounds, 0.05);
const primCylStl = writeCheckedStl('prim-cylinder.stl', cyl.mesh, primCylBounds, 0.05);
const primDiscStl = writeCheckedStl('prim-disc.stl', disc.mesh, primDiscBounds, 0.05);
console.log('prim-box triangles', primBoxStl.triangles, 'bytes', primBoxStl.bytes);
console.log('prim-cylinder triangles', primCylStl.triangles, 'bytes', primCylStl.bytes);
console.log('prim-disc triangles', primDiscStl.triangles, 'bytes', primDiscStl.bytes);

const boxSolid = ops.makeBoxSolid(oc, 20, 20, 20, [-10, -10, 0]);
expect('transform source', !!boxSolid);
const skipped = ops.transformShape(oc, boxSolid, { dx: 0, dy: 0, dz: 0, rxDeg: 0, ryDeg: 0, rzDeg: 0 });
expect('identity transform skipped', skipped.ok === true && skipped.skipped === true && skipped.shape === null);
const missing = ops.transformShape(oc, null, { dx: 5 });
expect('null transform kept', missing.ok === false && missing.shape === null && missing.kept === true && missing.error.indexOf('kept') !== -1);
const moved = ops.transformShape(oc, boxSolid, { dx: 5, dy: 0, dz: 0 });
expect('move ok', moved.ok === true && !!moved.shape);
const movedView = inspectSolid(oc, moved.shape);
expect('move gate', movedView.gate.pass === true && movedView.watertight.pass === true && movedView.units === 'mm');
const movedBounds = ops.solidBounds(oc, moved.shape);
nearBounds('moved box', movedBounds, { xmin: -5, ymin: -10, zmin: 0, xmax: 15, ymax: 10, zmax: 20 }, 0.05);
expect('move volume', Math.abs(ops.solidVolumeMm3(oc, moved.shape) - 8000) <= 1e-3);
const movedStl = writeCheckedStl('prim-box-moved.stl', movedView.mesh, { xmin: -5, ymin: -10, zmin: 0, xmax: 15, ymax: 10, zmax: 20 }, 0.05);
console.log('prim-box-moved triangles', movedStl.triangles, 'bytes', movedStl.bytes);
const rotated = ops.transformShape(oc, boxSolid, { rzDeg: 15, origin: [0, 0, 10] });
expect('rotate ok', rotated.ok === true && !!rotated.shape);
const rotatedView = inspectSolid(oc, rotated.shape);
expect('rotate gate', rotatedView.gate.pass === true && rotatedView.watertight.pass === true && rotatedView.units === 'mm');
expect('rotate volume', Math.abs(ops.solidVolumeMm3(oc, rotated.shape) - 8000) <= 1e-3);
const rotatedBounds = ops.solidBounds(oc, rotated.shape);
const rotExtent = 10 * (Math.cos(15 * Math.PI / 180) + Math.sin(15 * Math.PI / 180));
nearBounds('rotated box', rotatedBounds, {
  xmin: -rotExtent,
  ymin: -rotExtent,
  zmin: 0,
  xmax: rotExtent,
  ymax: rotExtent,
  zmax: 20,
}, 0.2);
const rotatedStl = writeCheckedStl('prim-box-rotated.stl', rotatedView.mesh, {
  xmin: -rotExtent,
  ymin: -rotExtent,
  zmin: 0,
  xmax: rotExtent,
  ymax: rotExtent,
  zmax: 20,
}, 0.2);
console.log('prim-box-rotated triangles', rotatedStl.triangles, 'bytes', rotatedStl.bytes);
expect('input kept after transform', Math.abs(ops.solidVolumeMm3(oc, boxSolid) - 8000) <= 1e-3);
if (moved.shape) moved.shape.delete();
if (rotated.shape) rotated.shape.delete();
if (boxSolid) boxSolid.delete();
const resized = buildBox(oc, { sx: 24, sy: 20, sz: 20, cx: 0, cy: 0, cz: 10 });
expect('resize gate', resized.gate.pass === true && resized.watertight.pass === true && resized.units === 'mm');
expect('resize volume ' + (resized.params.sx * resized.params.sy * resized.params.sz), Math.abs((resized.params.sx * resized.params.sy * resized.params.sz) - 9600) < 1e-9);
const resizedStl = writeCheckedStl('prim-box-resized.stl', resized.mesh, { xmin: -12, ymin: -10, zmin: 0, xmax: 12, ymax: 10, zmax: 20 }, 0.05);
console.log('prim-box-resized triangles', resizedStl.triangles, 'bytes', resizedStl.bytes);

const plateSx = ops.PLATE_SX_MM;
const plateSy = ops.PLATE_SY_MM;
const plateSz = ops.PLATE_SZ_MM;
const plateShape = ops.makeBoxSolid(oc, plateSx, plateSy, plateSz, [-plateSx / 2, -plateSy / 2, 0]);
expect('plate solid', !!plateShape);
const plateView = plateShape ? inspectSolid(oc, plateShape) : null;
expect('plate gate', !!plateView && plateView.gate.pass === true && plateView.watertight.pass === true && plateView.units === 'mm');
let plateFace = null;
let plateFaceZ = -Infinity;
const plateFaces = plateView && plateView.topology ? plateView.topology.faces : [];
expect('plate faces ' + plateFaces.length, plateFaces.length === 6);
for (let fi = 0; fi < plateFaces.length; fi += 1) {
  const centroid = plateFaces[fi].centroid;
  if (centroid && centroid[2] > plateFaceZ) {
    plateFaceZ = centroid[2];
    plateFace = plateFaces[fi];
  }
}
const plateFrame = plateFace
  ? faceFrameFromTriangles(plateView.mesh.vertices, plateView.mesh.triangles, plateFace.tris, [0, 0, plateSz / 2])
  : null;
expect('plate frame', !!plateFrame);
if (plateFrame) {
  expect('plate frame origin', Math.abs(plateFrame.origin[0] + plateSx / 2) <= 0.2
    && Math.abs(plateFrame.origin[1] + plateSy / 2) <= 0.2
    && Math.abs(plateFrame.origin[2] - plateSz) <= 0.2);
  expect('plate inward', Math.abs(plateFrame.inward[0]) <= 1e-6 && Math.abs(plateFrame.inward[1]) <= 1e-6 && plateFrame.inward[2] < -0.9);
  const plateSpots = ops.PLATE_HOLE_UV_MM;
  for (let pi = 0; pi < plateSpots.length; pi += 1) {
    const at = plateFrame.point(plateSpots[pi][0], plateSpots[pi][1]);
    expect('plate spot ' + pi, Math.abs(at[0] - (-plateSx / 2 + plateSpots[pi][0])) <= 0.2
      && Math.abs(at[1] - (-plateSy / 2 + plateSpots[pi][1])) <= 0.2
      && Math.abs(at[2] - plateSz) <= 0.2);
  }
}
const plateVolume = plateSx * plateSy * plateSz;
const badHole = plateShape && plateFrame ? ops.cutHole(oc, plateShape, {
  face: plateFrame.point(ops.PLATE_HOLE_UV_MM[0][0], ops.PLATE_HOLE_UV_MM[0][1]),
  dir: plateFrame.inward,
  diameterMm: 0,
  depthMode: 'through',
  countersink: true,
  countersinkDiameterMm: ops.HOLE_COUNTERSINK_DIAMETER_MM,
  countersinkAngleDeg: ops.HOLE_COUNTERSINK_ANGLE_DEG,
}) : { ok: true, kept: false, shape: {}, error: 'missing' };
expect('bad diameter kept', badHole.ok === false && badHole.kept === true && badHole.shape === null && String(badHole.error).indexOf('kept') !== -1);
expect('bad diameter volume', !!plateShape && Math.abs(ops.solidVolumeMm3(oc, plateShape) - plateVolume) <= 1e-3);
let holedShape = plateShape;
let plateBefore = 0;
let plateAfter = 0;
if (plateFrame && plateShape) {
  for (let hi = 0; hi < ops.PLATE_HOLE_UV_MM.length; hi += 1) {
    const uv = ops.PLATE_HOLE_UV_MM[hi];
    const cut = ops.cutHole(oc, holedShape, {
      face: plateFrame.point(uv[0], uv[1]),
      dir: plateFrame.inward,
      diameterMm: ops.HOLE_DIAMETER_MM,
      depthMode: 'through',
      depthMm: 0,
      countersink: true,
      countersinkDiameterMm: ops.HOLE_COUNTERSINK_DIAMETER_MM,
      countersinkAngleDeg: ops.HOLE_COUNTERSINK_ANGLE_DEG,
    });
    expect('plate hole ' + (hi + 1) + ' ' + (cut.error || ''), cut.ok === true && !!cut.shape && cut.units === 'mm');
    expect('plate hole ' + (hi + 1) + ' gate', cut.ok === true && cut.gate && cut.gate.pass === true && cut.watertight && cut.watertight.pass === true);
    expect('plate hole ' + (hi + 1) + ' depth', cut.ok === true && Math.abs(cut.depthMm - plateSz) <= 0.05);
    const faceCount = cut.topology && cut.topology.faces ? cut.topology.faces.length : 0;
    expect('plate hole ' + (hi + 1) + ' faces ' + faceCount, cut.ok === true && faceCount === 6 + (hi + 1) * 2);
    const tops = cut.ok && cut.shape
      ? topCountersinkCircles(oc, cut.shape, plateSz, ops.HOLE_COUNTERSINK_DIAMETER_MM)
      : { ok: false, circles: 0 };
    expect('plate hole ' + (hi + 1) + ' countersink tops ' + tops.circles, tops.ok === true && tops.circles === hi + 1);
    if (!cut.ok || !cut.shape) break;
    if (hi === 0) plateBefore = cut.volumeBefore;
    plateAfter = cut.volumeAfter;
    console.log('plate hole', hi + 1, 'volume', cut.volumeBefore, '->', cut.volumeAfter, 'depth', cut.depthMm, 'countersink height', cut.countersinkHeightMm);
    if (holedShape !== plateShape) holedShape.delete();
    holedShape = cut.shape;
  }
}
const oneHole = ops.holeRemovedVolumeMm3({
  diameterMm: ops.HOLE_DIAMETER_MM,
  depthMm: plateSz,
  countersink: true,
  countersinkDiameterMm: ops.HOLE_COUNTERSINK_DIAMETER_MM,
  countersinkAngleDeg: ops.HOLE_COUNTERSINK_ANGLE_DEG,
});
const plateWant = plateVolume - oneHole * ops.PLATE_HOLE_UV_MM.length;
expect('plate volume ' + plateAfter + ' want ' + plateWant, plateBefore > 0 && Math.abs(plateBefore - plateVolume) <= 1e-3 && Math.abs(plateAfter - plateWant) <= 0.5);
expect('plate input kept', !!plateShape && Math.abs(ops.solidVolumeMm3(oc, plateShape) - plateVolume) <= 1e-3);
const plateBounds = {
  xmin: -plateSx / 2,
  ymin: -plateSy / 2,
  zmin: 0,
  xmax: plateSx / 2,
  ymax: plateSy / 2,
  zmax: plateSz,
};
if (holedShape && holedShape !== plateShape) {
  const holedView = inspectSolid(oc, holedShape);
  const plateStl = writeCheckedStl('prim-plate-holes.stl', holedView.mesh, plateBounds, 0.2);
  console.log('prim-plate-holes triangles', plateStl.triangles, 'bytes', plateStl.bytes);
  if (plateFrame) {
    const holePoints = [];
    for (let hi = 0; hi < ops.PLATE_HOLE_UV_MM.length; hi += 1) {
      const uv = ops.PLATE_HOLE_UV_MM[hi];
      holePoints.push(plateFrame.point(uv[0], uv[1]));
    }
    const normalReport = viewerCutNormalReport(
      holedView.mesh,
      holePoints,
      plateSz,
      ops.HOLE_COUNTERSINK_DIAMETER_MM / 2
    );
    expect('viewer cut normals ' + normalReport, normalReport === '');
  }
}
console.log(
  'plate holes diameter', ops.HOLE_DIAMETER_MM,
  'countersink', ops.HOLE_COUNTERSINK_DIAMETER_MM,
  'angle', ops.HOLE_COUNTERSINK_ANGLE_DEG,
  'plate', plateSx, plateSy, plateSz,
  'volume', plateBefore, '->', plateAfter,
  'fit', ops.HOLE_FIT
);
const blindBox = ops.makeBoxSolid(oc, 20, 20, 10, [-10, -10, 0]);
const blindCut = blindBox ? ops.cutHole(oc, blindBox, {
  face: [0, 0, 10],
  dir: [0, 0, -1],
  diameterMm: ops.HOLE_DIAMETER_MM,
  depthMode: 'blind',
  depthMm: ops.HOLE_BLIND_DEPTH_MM,
  countersink: false,
}) : { ok: false, error: 'missing', volumeAfter: 0 };
const blindWant = 20 * 20 * 10 - ops.holeRemovedVolumeMm3({
  diameterMm: ops.HOLE_DIAMETER_MM,
  depthMm: ops.HOLE_BLIND_DEPTH_MM,
  countersink: false,
});
expect('blind hole ' + (blindCut.error || ''), blindCut.ok === true && Math.abs(blindCut.volumeAfter - blindWant) <= 0.5);
expect('blind input kept', !!blindBox && Math.abs(ops.solidVolumeMm3(oc, blindBox) - 4000) <= 1e-3);
if (blindCut.shape) blindCut.shape.delete();
if (blindBox) blindBox.delete();
if (holedShape && holedShape !== plateShape) holedShape.delete();
if (plateShape) plateShape.delete();

const pageSrc = readFileSync(path.join(root, 'web', 'index.html'), 'utf8');
expect('no bracket demo in the page', pageSrc.indexOf('demo=blink') === -1 && pageSrc.indexOf('buildBlink') === -1);
expect('disc hook', pageSrc.indexOf("primKind === 'disc'") !== -1);
expect('create menu', pageSrc.indexOf('id="createMenu"') !== -1 && pageSrc.indexOf('data-action="createMenu"') !== -1);
expect('decimal keypad', pageSrc.indexOf('inputmode="decimal"') !== -1);
expect('gizmo switch', pageSrc.indexOf('id="gizmoSwitch"') !== -1 && pageSrc.indexOf('data-mode="rotate"') !== -1 && pageSrc.indexOf('data-mode="scale"') !== -1);
expect('portrait sheet', pageSrc.indexOf('id="dimToggle"') !== -1 && pageSrc.indexOf('id="dimBody"') !== -1 && pageSrc.indexOf('primRz') !== -1);
expect('hole tool', pageSrc.indexOf('id="holeApply"') !== -1 && pageSrc.indexOf('id="holeDia"') !== -1 && pageSrc.indexOf('data-action="holeTool"') !== -1);
expect('hole defaults on the page', pageSrc.indexOf('value="4.5"') !== -1 && pageSrc.indexOf('value="9.5"') !== -1 && pageSrc.indexOf('value="90"') !== -1);
expect('closed inspector hidden', pageSrc.indexOf('.inspector:not(.open)') !== -1 && pageSrc.indexOf('visibility: hidden') !== -1);
expect('tap slop in page', pageSrc.indexOf('tapSlopPx()') !== -1);
expect('no layout constants in web ops', opsSrc.indexOf('BLINK_') === -1 && opsSrc.indexOf('buildBlink') === -1);

if (blinkMod && blinkFile) {
  const blinkPlan = blinkMod.blinkHolePlan(null);
  const blinkSpec = blinkMod.blinkSpec(null);
  const legCount = Number(blinkFile.legHoleCount);
  const discCount = Number(blinkFile.discHoleCount);
  const specKeys = ['legLengthMm', 'uprightHeightMm', 'legWidthMm', 'thicknessMm', 'discAlongMm', 'discAcrossMm', 'discDiameterMm', 'discThicknessMm'];
  let specMatch = Number.isFinite(legCount) && Number.isFinite(discCount);
  for (let si = 0; si < specKeys.length; si += 1) {
    if (Number(blinkSpec[specKeys[si]]) !== Number(blinkFile[specKeys[si]])) specMatch = false;
  }
  const specOffsets = blinkSpec.legHoleOffsetsMm || [];
  const fileOffsets = Array.isArray(blinkFile.legHoleOffsetsMm) ? blinkFile.legHoleOffsetsMm : [];
  const offsetMatch = specOffsets.length === fileOffsets.length && specOffsets.every(function (value, index) {
    return Number(value) === Number(fileOffsets[index]);
  });
  expect('fixture sizes match the local file', specMatch && offsetMatch);
  expect('drop log empty', blinkPlan.dropped.length === 0);
  const keptCountersink = blinkPlan.kept.filter(function (hole) { return hole.kind === 'countersink'; });
  expect('countersink count', keptCountersink.length === legCount * 2);
  expect('horizontal countersinks', blinkPlan.kept.filter(function (hole) { return hole.leg === 'horizontal'; }).length === legCount);
  expect('vertical countersinks', blinkPlan.kept.filter(function (hole) { return hole.leg === 'vertical' && hole.kind === 'countersink'; }).length === legCount);
  expect('disc screws', blinkPlan.discHoles.length === discCount && blinkPlan.discHoles[0].fit.indexOf('Erik to measure') !== -1);
  expect('through-holes planned', keptCountersink.length + blinkPlan.discHoles.length === legCount * 2 + discCount);
  const clearance = blinkMod.countersinkClearance(null);
  expect('countersink clearance ' + clearance.failures.join('; '), clearance.pass === true);
  expect('edge defaults', ops.EDGE_FILLET_RADIUS_MM === blinkSpec.userFilletRadiusMm && ops.EDGE_CHAMFER_DISTANCE_MM === blinkSpec.userChamferMm);

  const blinkWant = blinkMod.expectedBlinkVolume(null);
  const blinkBounds = blinkMod.expectedBlinkBounds(null);
  const blink = blinkMod.buildBlink(oc, null);
  expect('blink pass ' + (blink.lastError || ''), blink.pass === true && blink.lastError === '');
  expect('blink units', blink.units === 'mm' && blink.fit === 'unverified fit');
  expect('blink gate', blink.gate.pass === true && blink.watertight.pass === true && blink.solids === 1);
  expect('blink volume ' + blink.volumeMm3 + ' want ' + blinkWant, Math.abs(blink.volumeMm3 - blinkWant) <= blinkSpec.volumeTolMm3);
  expect('blink analytic field', Math.abs(blink.analyticVolumeMm3 - blinkWant) <= 1e-9);
  nearBounds('blink bounds', blink.bounds, blinkBounds, blinkSpec.boundsTolMm);
  const blinkSteps = blink.log.filter(function (item) { return item.pass; }).map(function (item) { return item.step; });
  expect('blink steps ' + blinkSteps.join(','), blinkSteps[0] === 'fuse' && blinkSteps[1] === 'fillet' && blinkSteps[2] === 'disc' && blinkSteps[blinkSteps.length - 1] === 'hole');
  expect('blink fuse glue off', blink.log[0].glue === false);
  expect('blink disc glue on', blink.log[2].glue === true && blink.log[2].step === 'disc');
  expect('blink holes glue off', blink.log.filter(function (item) { return item.step === 'hole'; }).every(function (item) { return item.glue === false && item.pass === true; }));
  expect('blink hole steps', blink.log.filter(function (item) { return item.step === 'hole' && item.pass; }).length === legCount * 2 + discCount);
  expect('blink through count', blink.throughHoles === legCount * 2 + discCount && blink.droppedHoles.length === 0);
  const blinkClass = blinkMod.classifyBlinkHoles(oc, blink.shape, null);
  expect('blink holes through ' + blinkClass.message, blinkClass.pass === true);
  if (!blinkClass.pass) console.error(blinkClass.failures.join('\n'));
  const blinkMeshVol = ops.meshVolumeMm3(blink.mesh);
  expect('blink mesh volume ' + blinkMeshVol, Math.abs(blinkMeshVol - blinkWant) <= blinkSpec.meshVolumeTolMm3);
  if (blink.mesh) {
    const blinkStl = writeCheckedStl('blink.stl', blink.mesh, blinkBounds, 0.05);
    console.log('blink triangles', blinkStl.triangles, 'bytes', blinkStl.bytes);
  }
  expect('blink mesh settings', blink.meshSettings && Math.abs(blink.meshSettings.Deflection - 0.05) < 1e-9 && blink.meshSettings.Relative === false && Math.abs(blink.meshSettings.Angle - 0.2) < 1e-9);

  const huge = ops.applyPickedEdgeOp(oc, blink.shape, [blinkMod.blinkPickSegments(null)[0]], 'fillet', 100);
  expect('oversized fillet rejected', huge.ok === false && huge.shape === null && huge.kept === true);
  expect('oversized keeps shape', Math.abs(ops.solidVolumeMm3(oc, blink.shape) - blink.volumeMm3) <= 1e-6);
  const tipped = ops.applyPickedEdgeOp(oc, blink.shape, [blinkMod.blinkPickSegments(null)[0]], 'fillet', ops.EDGE_FILLET_RADIUS_MM);
  expect('picked fillet ' + (tipped.error || ''), tipped.ok === true && !!tipped.shape && tipped.volumeMm3 < blink.volumeMm3);
  const chamfered = tipped.ok && tipped.shape
    ? ops.applyPickedEdgeOp(oc, tipped.shape, [blinkMod.blinkPickSegments(null)[1]], 'chamfer', ops.EDGE_CHAMFER_DISTANCE_MM)
    : { ok: false, shape: null, error: 'fillet did not run' };
  expect('picked chamfer ' + (chamfered.error || ''), chamfered.ok === true && !!chamfered.shape);
  if (blink.shape) blink.shape.delete();
  if (tipped.shape) tipped.shape.delete();
  if (chamfered.shape) chamfered.shape.delete();
  console.log('blink volume', blink.volumeMm3, 'analytic', blinkWant, 'mesh', blinkMeshVol);
  console.log('blink dropped', blink.droppedHoles.length);
} else {
  console.log('skipped, local fixture');
}

console.log('lbracket triangles', bracket.mesh.triangles.length);
console.log('lbracket stl bytes', stlBytes.length);
console.log('lbracket mesh ms', bracket.meshTimeMs);
console.log('lbracket mesh settings', JSON.stringify(bracket.meshSettings));
console.log('overlap volumes', JSON.stringify(overlapVolumes));
console.log('demo volumes', JSON.stringify(demoVolumes));

function shapeMapCount(oc, shape, typeName) {
  const Ctor = oc.TopTools_IndexedMapOfShape
    || oc.NCollection_IndexedMap_TopoDS_Shape_TopTools_ShapeMapHasher;
  const map = new Ctor();
  let count = -1;
  try {
    oc.TopExp.MapShapes(shape, oc.TopAbs_ShapeEnum[typeName], map);
    count = map.Extent();
  } finally {
    try { map.delete(); } catch (_err) { /* already released */ }
  }
  return count;
}

function segmentOf(edge) {
  const pts = edge && edge.pts ? edge.pts : [];
  if (pts.length < 2) return null;
  return { a: pts[0].slice(), b: pts[pts.length - 1].slice() };
}

function edgeLen(edge) {
  const seg = segmentOf(edge);
  if (!seg) return 0;
  const dx = seg.a[0] - seg.b[0];
  const dy = seg.a[1] - seg.b[1];
  const dz = seg.a[2] - seg.b[2];
  return Math.sqrt(dx * dx + dy * dy + dz * dz);
}

// 20 mm cube, one edge, r = d = 2 mm. Volumes are the straight-edge formulas
// (fillet removes r^2*(1-pi/4)*L, chamfer removes d^2/2*L). Tolerance 0.1%.
// Free edges are a topology assert on the result, not an export gate.
const cubeOrigin = [-10, -10, 0];
const cubeFilletWant = 7982.832;
const cubeChamferWant = 7960;
const cube = ops.makeBoxSolid(oc, 20, 20, 20, cubeOrigin);
expect('cube built', !!cube && Math.abs(ops.solidVolumeMm3(oc, cube) - 8000) <= 1e-6);
const cubeView = cube ? inspectSolid(oc, cube) : null;
const cubeEdge = cubeView
  ? cubeView.topology.edges.filter(function (edge) { return Math.abs(edgeLen(edge) - 20) < 0.05; })[0]
  : null;
const cubeSeg = segmentOf(cubeEdge);
const cubeHuge = cube && cubeSeg
  ? ops.applyPickedEdgeOp(oc, cube, [cubeSeg], 'fillet', 100)
  : { ok: true, kept: false, shape: {} };
expect('cube oversized rejected', cubeHuge.ok === false && cubeHuge.shape === null && cubeHuge.kept === true);
expect('cube oversized keeps 8000', !!cube && Math.abs(ops.solidVolumeMm3(oc, cube) - 8000) <= 1e-6);
const cubeFillet = cube && cubeSeg
  ? ops.applyPickedEdgeOp(oc, cube, [cubeSeg], 'fillet', 2)
  : { ok: false, error: 'no edge', topology: { faces: [], edges: [], vertices: [] }, gate: {} };
const cubeFilletTol = cubeFilletWant * 0.001;
expect(
  'cube fillet volume ' + (cubeFillet.volumeMm3 || '') + ' ' + (cubeFillet.error || ''),
  cubeFillet.ok === true && Math.abs(cubeFillet.volumeMm3 - cubeFilletWant) <= cubeFilletTol
);
expect('cube fillet faces', cubeFillet.ok === true && shapeMapCount(oc, cubeFillet.shape, 'TopAbs_FACE') === 7);
expect('cube fillet edges', cubeFillet.ok === true && shapeMapCount(oc, cubeFillet.shape, 'TopAbs_EDGE') === 15);
expect('cube fillet vertices', cubeFillet.ok === true && shapeMapCount(oc, cubeFillet.shape, 'TopAbs_VERTEX') === 10);
expect('cube fillet free edges', cubeFillet.gate && cubeFillet.gate.freeEdges === 0);
expect('cube fillet units', cubeFillet.units === 'mm');
const cubeAgainEdge = cubeFillet.ok && cubeFillet.topology
  ? cubeFillet.topology.edges.filter(function (edge) { return edgeLen(edge) > 1; })[0]
  : null;
const cubeAgain = cubeFillet.ok && cubeAgainEdge
  ? ops.applyPickedEdgeOp(oc, cubeFillet.shape, [segmentOf(cubeAgainEdge)], 'fillet', 50)
  : { ok: false, kept: false, shape: {} };
if (cubeAgain.ok) {
  expect('cube refillet allowed', !!cubeAgain.shape);
  if (cubeAgain.shape) cubeAgain.shape.delete();
} else {
  expect('cube refillet kept', cubeAgain.kept === true && cubeAgain.shape === null);
  expect(
    'cube refillet volume',
    Math.abs(ops.solidVolumeMm3(oc, cubeFillet.shape) - cubeFillet.volumeMm3) <= 1e-4
  );
}
const cubeB = ops.makeBoxSolid(oc, 20, 20, 20, cubeOrigin);
const cubeBView = cubeB ? inspectSolid(oc, cubeB) : null;
const cubeBEdge = cubeBView
  ? cubeBView.topology.edges.filter(function (edge) { return Math.abs(edgeLen(edge) - 20) < 0.05; })[0]
  : null;
const cubeChamfer = cubeB && cubeBEdge
  ? ops.applyPickedEdgeOp(oc, cubeB, [segmentOf(cubeBEdge)], 'chamfer', 2)
  : { ok: false, error: 'no edge', gate: {} };
const cubeChamferTol = cubeChamferWant * 0.001;
expect(
  'cube chamfer volume ' + (cubeChamfer.volumeMm3 || '') + ' ' + (cubeChamfer.error || ''),
  cubeChamfer.ok === true && Math.abs(cubeChamfer.volumeMm3 - cubeChamferWant) <= cubeChamferTol
);
expect('cube chamfer faces', cubeChamfer.ok === true && shapeMapCount(oc, cubeChamfer.shape, 'TopAbs_FACE') === 7);
expect('cube chamfer edges', cubeChamfer.ok === true && shapeMapCount(oc, cubeChamfer.shape, 'TopAbs_EDGE') === 15);
expect('cube chamfer vertices', cubeChamfer.ok === true && shapeMapCount(oc, cubeChamfer.shape, 'TopAbs_VERTEX') === 10);
expect('cube chamfer free edges', cubeChamfer.gate && cubeChamfer.gate.freeEdges === 0);
expect('cube input kept', !!cube && Math.abs(ops.solidVolumeMm3(oc, cube) - 8000) <= 1e-6);
if (cubeFillet.shape) cubeFillet.shape.delete();
if (cubeChamfer.shape) cubeChamfer.shape.delete();
if (cube) cube.delete();
if (cubeB) cubeB.delete();

function projectNear(a, b) {
  return typeof a === 'number' && typeof b === 'number' && Math.abs(a - b) <= 0.01;
}

function releaseProjectShape(shape) {
  if (shape && typeof shape.delete === 'function') {
    try { shape.delete(); } catch (_err) { /* already released */ }
  }
}

const projectBoxParams = normalizeBox(null);
const projectCylParams = normalizeCylinder({ cx: 10, cy: 0, cz: 10, radius: 10, height: 20, axis: 'Z' });
const projectBox = ops.makeBoxSolid(oc, projectBoxParams.sx, projectBoxParams.sy, projectBoxParams.sz, [
  projectBoxParams.cx - projectBoxParams.sx / 2,
  projectBoxParams.cy - projectBoxParams.sy / 2,
  projectBoxParams.cz - projectBoxParams.sz / 2,
]);
const projectDir = projectCylParams.axis === 'X' ? [1, 0, 0] : projectCylParams.axis === 'Y' ? [0, 1, 0] : [0, 0, 1];
const projectCyl = ops.makeCylinderSolid(oc, projectCylParams.radius, projectCylParams.height, [
  projectCylParams.cx - projectDir[0] * projectCylParams.height / 2,
  projectCylParams.cy - projectDir[1] * projectCylParams.height / 2,
  projectCylParams.cz - projectDir[2] * projectCylParams.height / 2,
], projectDir);
const projectBodies = [
  { name: 'Box', kind: 'box', params: projectBoxParams, shape: projectBox, material: 'default', features: [] },
  { name: 'Cylinder', kind: 'cylinder', params: projectCylParams, shape: projectCyl, material: 'default', features: [] },
];
const projectWritten = projectBox && projectCyl ? projectFile.documentFromBodies(oc, projectBodies) : { ok: false, error: 'shape' };
expect('project save', projectWritten.ok === true && typeof projectWritten.text === 'string');
if (projectWritten.ok) {
  const projectDoc = JSON.parse(projectWritten.text);
  expect('project units mm', projectDoc.units === 'mm' && projectDoc.version === 1 && projectDoc.parts.length === 2);
  const projectParsed = projectFile.parseProject(projectWritten.text);
  expect('project parse', projectParsed.ok === true);
  const projectLoaded = projectParsed.ok ? projectFile.loadShapes(oc, projectParsed.doc, { normalizeBox, normalizeCylinder, normalizeDisc }, ops) : { ok: false, parts: [] };
  expect('project load ' + (projectLoaded.error || ''), projectLoaded.ok === true && projectLoaded.parts.length === 2);
  if (projectLoaded.ok) {
    const originals = [projectBox, projectCyl];
    for (let pi = 0; pi < projectLoaded.parts.length; pi += 1) {
      const part = projectLoaded.parts[pi];
      expect('project source ' + part.name, part.source === 'parameters');
      const before = projectFile.measureShape(oc, originals[pi]);
      const after = projectFile.measureShape(oc, part.shape);
      expect('project volume ' + part.name + ' ' + after.volumeMm3, projectNear(before.volumeMm3, after.volumeMm3));
      ['xmin', 'ymin', 'zmin', 'xmax', 'ymax', 'zmax'].forEach(function (key) {
        expect('project bound ' + part.name + ' ' + key, projectNear(before.bounds[key], after.bounds[key]));
      });
      releaseProjectShape(part.shape);
    }
    expect('project box volume', projectNear(projectFile.measureShape(oc, projectBox).volumeMm3, 8000));
  }
  const featured = JSON.parse(projectWritten.text);
  featured.parts[0].features = ['fillet'];
  const featuredLoaded = projectFile.loadShapes(oc, projectFile.parseProject(JSON.stringify(featured)).doc, { normalizeBox, normalizeCylinder }, ops);
  expect('project feature fallback', featuredLoaded.ok === true && featuredLoaded.parts[0].source === 'brep');
  if (featuredLoaded.ok) {
    featuredLoaded.parts.forEach(function (part) { releaseProjectShape(part.shape); });
  }
}
expect('project empty', projectFile.parseProject('').ok === false && projectFile.parseProject('   ').error === projectFile.ERR_EMPTY);
expect('project corrupt', projectFile.parseProject('{not json').error === projectFile.ERR_READ);
const projectInches = projectWritten.ok ? JSON.parse(projectWritten.text) : { units: 'mm', version: 1, parts: [] };
projectInches.units = 'in';
expect('project wrong units', projectFile.parseProject(JSON.stringify(projectInches)).error === projectFile.ERR_UNITS);
delete projectInches.units;
expect('project missing units', projectFile.parseProject(JSON.stringify(projectInches)).error === projectFile.ERR_UNITS);
releaseProjectShape(projectBox);
releaseProjectShape(projectCyl);

if (failures !== 0) {
  console.error(failures + ' failed');
  console.error('closed', closed);
  console.error('open', open);
  process.exit(1);
}

console.log('ok');
console.log('closed_box', closed.message);
console.log('open_box', open.message);
process.exit(0);
