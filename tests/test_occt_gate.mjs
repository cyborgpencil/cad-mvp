import { existsSync } from 'node:fs';
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
const selUrl = pathToFileURL(path.join(root, 'web', 'selection.mjs')).href;
const viewUrl = pathToFileURL(path.join(root, 'web', 'viewport-selection.mjs')).href;

const { createInstance } = await import(initUrl);
const { checkOcctGate, closedBoxMesh, openBoxMesh, box20Mesh } = await import(gateUrl);
const { buildBox, buildCylinder, PLACEHOLDER_BOX_MM, PLACEHOLDER_CYLINDER_MM } = await import(primUrl);
const { applyPointerSelection, groupMeshFaces, modeFromHotkey } = await import(selUrl);
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
expect('box tbd defaults', PLACEHOLDER_BOX_MM.tbd === true && box.params.sx === 20 && box.params.sz === 20);

const cyl = buildCylinder(oc, null);
expect('cylinder gate', cyl.gate.pass === true && cyl.gate.freeEdges === 0);
expect('cylinder watertight', cyl.watertight.pass === true);
expect('cylinder units mm', cyl.units === 'mm');
expect('cylinder faces ' + cyl.topology.faces.length, cyl.topology.faces.length === 3);
expect('cylinder vertices ' + cyl.topology.vertices.length, cyl.topology.vertices.length === 2);
expect('cylinder edges ' + cyl.topology.edges.length, cyl.topology.edges.length === 3);
expect('cylinder tbd defaults', PLACEHOLDER_CYLINDER_MM.tbd === true && cyl.params.axis === 'Z');

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
expect('hotkey 5', modeFromHotkey('5') === 'item');
expect('hotkey 4 unused', modeFromHotkey('4') === '');

const cad = threeDeltaToCad(1, 2, 3);
expect('three Y is cad Z', cad.x === 1 && cad.y === 3 && cad.z === 2);
expect('gizmo X', GIZMO_AXIS_THREE.x[0] === 1 && GIZMO_AXIS_THREE.x[1] === 0 && GIZMO_AXIS_THREE.x[2] === 0);
expect('gizmo Y', GIZMO_AXIS_THREE.y[0] === 0 && GIZMO_AXIS_THREE.y[1] === 0 && GIZMO_AXIS_THREE.y[2] === 1);
expect('gizmo Z up', GIZMO_AXIS_THREE.z[0] === 0 && GIZMO_AXIS_THREE.z[1] === 1 && GIZMO_AXIS_THREE.z[2] === 0);

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
