// Assemblies: placements, materials, Combine, and one 3MF object per part.
// Volumes are BRepGProp. No watertight check. No Blink file.
import { existsSync, readFileSync } from 'node:fs';
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
  const message = 'assemblies: libcascade is missing (' + missingLib.join(', ') + '). Run: python web/fetch-libcascade.py';
  if (envSet('CI') || envSet('GITHUB_ACTIONS')) {
    console.error('FAIL ' + message);
    process.exit(1);
  }
  console.error('SKIP ' + message);
  process.exit(77);
}

const { createInstance } = await import(pathToFileURL(path.join(libDir, 'init.single.js')).href);
const ops = await import(pathToFileURL(path.join(root, 'web', 'occt-ops.mjs')).href);
const projectFile = await import(pathToFileURL(path.join(root, 'web', 'project-file.mjs')).href);
const prim = await import(pathToFileURL(path.join(root, 'web', 'occt-primitives.mjs')).href);
const undo = await import(pathToFileURL(path.join(root, 'web', 'undo.mjs')).href);
const asm = await import(pathToFileURL(path.join(root, 'web', 'assemblies.mjs')).href);
const oc = await createInstance();

const failures = [];
function expect(name, ok) {
  if (ok) {
    console.log('PASS ' + name);
    return;
  }
  console.error('FAIL ' + name);
  failures.push(name);
}

function release(shape) {
  if (shape && typeof shape.delete === 'function') {
    try { shape.delete(); } catch (_err) { /* already released */ }
  }
}

function near(a, b, tol) {
  return Number.isFinite(a) && Number.isFinite(b) && Math.abs(a - b) <= tol;
}

function localBox() {
  return ops.makeBoxSolid(oc, 20, 20, 20, [-10, -10, -10]);
}

function localCylinder() {
  return ops.makeCylinderSolid(oc, 10, 20, [0, 0, -10], [0, 0, 1]);
}

function volume(shape) {
  return projectFile.shapeVolumeMm3(oc, shape);
}

const boxPlace = { x: 0, y: 0, z: 10 };
const cylPlace = { x: 40, y: 5, z: 12 };
const boxParams = prim.normalizeBox({ cx: boxPlace.x, cy: boxPlace.y, cz: boxPlace.z, sx: 20, sy: 20, sz: 20 });
const cylParams = prim.normalizeCylinder({
  cx: cylPlace.x,
  cy: cylPlace.y,
  cz: cylPlace.z,
  radius: 10,
  height: 20,
  axis: 'Z',
});
const boxShape = localBox();
const cylShape = localCylinder();
const boxVol = volume(boxShape);
const cylVol = volume(cylShape);

expect('box volume 8000', near(boxVol, 8000, asm.VOLUME_TOL_MM3));
expect('cylinder volume', cylVol > 6000);

const loc = asm.makeLocation(oc, { x: 3, y: -4, z: 5 });
const read = asm.locationTranslation(loc);
expect('TopLoc translation', !!read && near(read.x, 3, 1e-9) && near(read.y, -4, 1e-9) && near(read.z, 5, 1e-9));
release(loc);

const savedBodies = [
  { name: 'Box', kind: 'box', params: boxParams, shape: boxShape, material: 'PLA', features: [] },
  { name: 'Cylinder', kind: 'cylinder', params: cylParams, shape: cylShape, material: 'PETG', features: [] },
];
const written = projectFile.documentFromBodies(oc, savedBodies);
expect('save two parts', written.ok === true);
if (written.ok) {
  const doc = JSON.parse(written.text);
  expect('save units and count', doc.units === 'mm' && doc.version === 1 && doc.parts.length === 2);
  expect('save box placement', near(doc.parts[0].placement.x, 0, 1e-9) && near(doc.parts[0].placement.y, 0, 1e-9) && near(doc.parts[0].placement.z, 10, 1e-9));
  expect('save cylinder placement', near(doc.parts[1].placement.x, 40, 1e-9) && near(doc.parts[1].placement.y, 5, 1e-9) && near(doc.parts[1].placement.z, 12, 1e-9));
  expect('save tags', doc.parts[0].material === 'PLA' && doc.parts[1].material === 'PETG');
  expect('save names', doc.parts[0].name === 'Box' && doc.parts[1].name === 'Cylinder');
  const parsed = projectFile.parseProject(written.text);
  const loaded = parsed.ok
    ? projectFile.loadShapes(oc, parsed.doc, prim, ops)
    : { ok: false, parts: [] };
  expect('reload ' + (loaded.error || ''), loaded.ok === true && loaded.parts.length === 2);
  if (loaded.ok) {
    expect('reload names', loaded.parts[0].name === 'Box' && loaded.parts[1].name === 'Cylinder');
    expect('reload tags', loaded.parts[0].material === 'PLA' && loaded.parts[1].material === 'PETG');
    expect('reload placements', near(loaded.parts[0].placement.z, 10, 1e-9) && near(loaded.parts[1].placement.x, 40, 1e-9) && near(loaded.parts[1].placement.y, 5, 1e-9));
    expect('reload box volume', near(volume(loaded.parts[0].shape), boxVol, asm.VOLUME_TOL_MM3));
    expect('reload cylinder volume', near(volume(loaded.parts[1].shape), cylVol, asm.VOLUME_TOL_MM3));
    release(loaded.parts[0].shape);
    release(loaded.parts[1].shape);
  }
}

const overlapA = localBox();
const overlapB = localBox();
const partA = { name: 'Box', material: 'PLA', shape: overlapA, placement: { x: 0, y: 0, z: 10 }, shapeLocal: true };
const partB = { name: 'Box 2', material: 'PLA', shape: overlapB, placement: { x: 10, y: 0, z: 10 }, shapeLocal: true };
const volA = volume(overlapA);
const volB = volume(overlapB);
const placedA = asm.placedCopy(oc, overlapA, partA.placement);
const placedB = asm.placedCopy(oc, overlapB, partB.placement);
const reference = placedA.ok && placedB.ok ? ops.fuseShapes(oc, placedA.shape, placedB.shape) : { ok: false };
const referenceVol = reference.ok ? volume(reference.shape) : NaN;
expect('reference fuse 12000', reference.ok === true && near(referenceVol, 12000, asm.VOLUME_TOL_MM3));

const stack = undo.createCommandStack();
const before = [
  { name: partA.name, material: partA.material, placement: Object.assign({}, partA.placement), shape: ops.copyShape(oc, overlapA), volume: volA },
  { name: partB.name, material: partB.material, placement: Object.assign({}, partB.placement), shape: ops.copyShape(oc, overlapB), volume: volB },
];
const combined = asm.combineParts(oc, [partA, partB]);
expect('combine valid', combined.ok === true && combined.valid === true && combined.material === 'PLA');
expect('combine volume', combined.ok && near(combined.volumeMm3, referenceVol, asm.VOLUME_TOL_MM3));
expect('inputs kept', near(volume(overlapA), volA, 1e-6) && near(volume(overlapB), volB, 1e-6));
if (combined.ok) {
  const after = [{ name: combined.name, material: combined.material, placement: combined.placement, shape: combined.shape, volume: combined.volumeMm3 }];
  stack.push({ label: 'Combine', before: before, after: after });
  expect('one undo step', stack.depth() === 1 && stack.redoDepth() === 0);
  const undone = stack.undo();
  expect('undo restores two parts', !!undone && undone.before.length === 2 && stack.depth() === 0);
  if (undone) {
    expect('undo volumes', near(volume(undone.before[0].shape), volA, asm.VOLUME_TOL_MM3) && near(volume(undone.before[1].shape), volB, asm.VOLUME_TOL_MM3));
    const redone = stack.redo();
    expect('redo restores the fuse', !!redone && near(volume(redone.after[0].shape), referenceVol, asm.VOLUME_TOL_MM3));
  }
}

const failA = localBox();
const failB = localBox();
const failVolA = volume(failA);
const failVolB = volume(failB);
const forced = asm.combineParts(oc, [
  { name: 'A', material: 'PLA', shape: failA, placement: { x: 0, y: 0, z: 10 }, shapeLocal: true },
  { name: 'B', material: 'PLA', shape: failB, placement: { x: 10, y: 0, z: 10 }, shapeLocal: true },
], { forceFail: true });
expect('forced combine error', forced.ok === false && forced.shape === null && forced.error === asm.ERR_COMBINE);
expect('forced combine unchanged', near(volume(failA), failVolA, 1e-6) && near(volume(failB), failVolB, 1e-6));

const mixA = localBox();
const mixB = localBox();
const mixVolA = volume(mixA);
const mixVolB = volume(mixB);
const mixed = asm.combineParts(oc, [
  { name: 'Hub', material: 'PLA', shape: mixA, placement: { x: 0, y: 0, z: 0 }, shapeLocal: true },
  { name: 'Tire', material: 'TPU', shape: mixB, placement: { x: 0, y: 0, z: 0 }, shapeLocal: true },
]);
expect('mixed materials refused', mixed.ok === false && mixed.shape === null && mixed.error === asm.ERR_MIXED);
expect('mixed materials unchanged', near(volume(mixA), mixVolA, 1e-6) && near(volume(mixB), mixVolB, 1e-6));

const exportBox = localBox();
const exportCyl = localCylinder();
const exportParts = [
  { name: 'Box', material: 'PLA', shape: exportBox, placement: boxPlace, shapeLocal: true },
  { name: 'Cylinder', material: 'PETG', shape: exportCyl, placement: cylPlace, shapeLocal: true },
];
const exported = asm.exportAssembly3mf(oc, exportParts, { units: 'mm' });
expect('3mf written', exported.ok === true && exported.bytes && exported.bytes[0] === 0x50 && exported.bytes[1] === 0x4b);
const xml = exported.ok ? asm.modelXmlFrom3mf(exported.bytes) : '';
expect('3mf unit', xml.indexOf('unit="millimeter"') >= 0);
expect('3mf core materials', xml.indexOf('<basematerials') >= 0 && xml.indexOf('3dmanufacturing/material/') < 0);
expect('3mf no components', xml.indexOf('<components') < 0);
const objectCount = (xml.match(/<object /g) || []).length;
expect('3mf one object per part', objectCount === 2);
expect('3mf pla object', xml.indexOf('name="Box"') >= 0 && xml.indexOf('pindex="0"') >= 0);
expect('3mf petg object', xml.indexOf('name="Cylinder"') >= 0 && xml.indexOf('pindex="1"') >= 0);
expect('3mf pla base', xml.indexOf('name="PLA"') >= 0 && xml.indexOf('name="PETG"') >= 0 && xml.indexOf('name="TPU"') >= 0);

function meshBoundsFromXml(block, placement) {
  const vertices = [];
  const re = /<vertex x="([^"]+)" y="([^"]+)" z="([^"]+)"\/>/g;
  let match = re.exec(block);
  while (match) {
    vertices.push([Number(match[1]), Number(match[2]), Number(match[3])]);
    match = re.exec(block);
  }
  return asm.placedMeshBounds(vertices, placement);
}

if (xml) {
  const blocks = xml.split('<object ').slice(1);
  expect('3mf blocks', blocks.length === 2);
  const boxXmlBounds = meshBoundsFromXml(blocks[0], boxPlace);
  const cylXmlBounds = meshBoundsFromXml(blocks[1], cylPlace);
  const boxExact = asm.exactPlacedBounds(oc, exportBox, boxPlace);
  const cylExact = asm.exactPlacedBounds(oc, exportCyl, cylPlace);
  const keys = ['xmin', 'ymin', 'zmin', 'xmax', 'ymax', 'zmax'];
  let boxOk = !!boxExact;
  let cylOk = !!cylExact;
  for (let i = 0; i < keys.length; i += 1) {
    const key = keys[i];
    if (!boxExact || !near(boxXmlBounds[key], boxExact[key], asm.BOUNDS_TOL_MM)) boxOk = false;
    if (!cylExact || !near(cylXmlBounds[key], cylExact[key], asm.BOUNDS_TOL_MM)) cylOk = false;
  }
  expect('3mf box bounds ' + JSON.stringify(boxXmlBounds) + ' vs ' + JSON.stringify(boxExact), boxOk);
  expect('3mf cylinder bounds ' + JSON.stringify(cylXmlBounds) + ' vs ' + JSON.stringify(cylExact), cylOk);
  expect('3mf box transform', blocks[0].indexOf('transform="1 0 0 0 1 0 0 0 1 0 0 10"') >= 0 || xml.indexOf('objectid="2" transform="1 0 0 0 1 0 0 0 1 0 0 10"') >= 0);
  expect('3mf cylinder transform', xml.indexOf('transform="1 0 0 0 1 0 0 0 1 40 5 12"') >= 0);
}

const inch = asm.exportAssembly3mf(oc, exportParts, { units: 'in' });
expect('inch export refused', inch.ok === false && inch.error === asm.ERR_UNITS && near(volume(exportBox), boxVol, 1e-6));

function boundsSame(a, b) {
  if (!a || !b) return false;
  const keys = ['xmin', 'ymin', 'zmin', 'xmax', 'ymax', 'zmax'];
  for (let i = 0; i < keys.length; i += 1) {
    if (!near(a[keys[i]], b[keys[i]], 1e-6)) return false;
  }
  return true;
}

const primLocal = localBox();
const primBefore = ops.optimalBounds(oc, primLocal);
const primPart = {
  name: 'Box',
  material: 'PLA',
  shape: primLocal,
  shapeLocal: true,
  placement: { x: 0, y: 0, z: 10 },
};
const primStep = asm.moveLocalPart(primPart, 5, 0, 0);
const primAfter = ops.optimalBounds(oc, primLocal);
expect(
  'primitive move keeps the solid',
  primStep.ok === true && primStep.shape === primLocal && boundsSame(primBefore, primAfter)
);
expect(
  'primitive move placement',
  !!primStep.placement
    && near(primStep.placement.x, 5, 1e-9)
    && near(primStep.placement.y, 0, 1e-9)
    && near(primStep.placement.z, 10, 1e-9)
    && near(primPart.placement.x, 0, 1e-9)
);
const primPlaced = primStep.ok ? asm.placedCopy(oc, primLocal, primStep.placement) : { ok: false, shape: null };
const primWorld = primPlaced.ok ? ops.optimalBounds(oc, primPlaced.shape) : null;
expect(
  'primitive move shows the new placement',
  !!primWorld
    && near(primWorld.xmin, -5, asm.BOUNDS_TOL_MM)
    && near(primWorld.xmax, 15, asm.BOUNDS_TOL_MM)
    && near(primWorld.zmin, 0, asm.BOUNDS_TOL_MM)
    && near(primWorld.zmax, 20, asm.BOUNDS_TOL_MM)
    && near(volume(primLocal), 8000, asm.VOLUME_TOL_MM3)
);
const primAgain = asm.moveLocalPart(primPart, 1, 0, 0);
expect(
  'second move keeps the solid',
  primAgain.ok === true && primAgain.shape === primLocal && boundsSame(primBefore, ops.optimalBounds(oc, primLocal))
);
const bakedMove = asm.moveLocalPart({ shape: primLocal, shapeLocal: false, placement: { x: 0, y: 0, z: 10 } }, 4, 0, 0);
expect('world solid is not a placement move', bakedMove.ok === false && boundsSame(primBefore, ops.optimalBounds(oc, primLocal)));
const pageSrc = readFileSync(path.join(root, 'web', 'index.html'), 'utf8');
expect('gizmo uses moveLocalPart', pageSrc.indexOf('assemblyApi.moveLocalPart') >= 0);
expect('ordinary primitive is stored local', pageSrc.indexOf('shapeLocal: storeLocal') >= 0);

release(boxShape);
release(cylShape);
release(overlapA);
release(overlapB);
if (placedA.shape) release(placedA.shape);
if (placedB.shape) release(placedB.shape);
if (reference.shape) release(reference.shape);
if (combined.shape) release(combined.shape);
before.forEach(function (part) { release(part.shape); });
release(failA);
release(failB);
release(mixA);
release(mixB);
release(exportBox);
release(exportCyl);
release(primLocal);
if (primPlaced.shape) release(primPlaced.shape);

if (failures.length) {
  console.error('FAIL assemblies ' + failures.join(', '));
  process.exit(1);
}
console.log('ASSEMBLIES_DONE');
