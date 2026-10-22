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
const { buildBox, buildCylinder, PLACEHOLDER_BOX_MM, PLACEHOLDER_CYLINDER_MM, BOX_EDGE_MM, CYLINDER_DIAMETER_MM, CYLINDER_HEIGHT_MM, SPHERE_DIAMETER_MM, inspectSolid, checkMeshWatertight, TESSELLATION_DEFLECTION_MM, TESSELLATION_ANGULAR, TESSELLATION_RELATIVE, TESSELLATION_CONTROL_SURFACE, TESSELLATION_IN_PARALLEL } = await import(primUrl);
const ops = await import(opsUrl);
const { applyPointerSelection, groupMeshFaces, modeFromHotkey, PICK_TOLERANCE_PX } = await import(selUrl);
const { threeDeltaToCad, GIZMO_AXIS_THREE } = await import(viewUrl);

let failures = 0;

function expect(name, ok) {
  if (ok) {
    return;
  }
  console.error(name + ' failed');
  failures += 1;
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
expect('pick tolerance 8', PICK_TOLERANCE_PX === 8);

const cad = threeDeltaToCad(1, 2, 3);
expect('three Y is cad Z', cad.x === 1 && cad.y === 3 && cad.z === 2);
expect('gizmo X', GIZMO_AXIS_THREE.x[0] === 1 && GIZMO_AXIS_THREE.x[1] === 0 && GIZMO_AXIS_THREE.x[2] === 0);
expect('gizmo Y', GIZMO_AXIS_THREE.y[0] === 0 && GIZMO_AXIS_THREE.y[1] === 0 && GIZMO_AXIS_THREE.y[2] === 1);
expect('gizmo Z up', GIZMO_AXIS_THREE.z[0] === 0 && GIZMO_AXIS_THREE.z[1] === 1 && GIZMO_AXIS_THREE.z[2] === 0);

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

console.log('lbracket triangles', bracket.mesh.triangles.length);
console.log('lbracket stl bytes', stlBytes.length);
console.log('lbracket mesh ms', bracket.meshTimeMs);
console.log('lbracket mesh settings', JSON.stringify(bracket.meshSettings));
console.log('overlap volumes', JSON.stringify(overlapVolumes));
console.log('demo volumes', JSON.stringify(demoVolumes));

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
