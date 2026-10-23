// Single-body bed pose. A synthetic L fused from two boxes.
// The profile is the unique largest face. No fixture dimensions.
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
  const message = 'bed_orient: libcascade is missing (' + missingLib.join(', ') + '). Run: python web/fetch-libcascade.py';
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

function parseObjectMeshes(modelXml) {
  const objects = [];
  const blocks = String(modelXml || '').split('<object ').slice(1);
  for (let i = 0; i < blocks.length; i += 1) {
    const vertices = [];
    const triangles = [];
    const vre = /<vertex x="([^"]+)" y="([^"]+)" z="([^"]+)"\/>/g;
    let match = vre.exec(blocks[i]);
    while (match) {
      vertices.push([Number(match[1]), Number(match[2]), Number(match[3])]);
      match = vre.exec(blocks[i]);
    }
    const tre = /<triangle v1="([^"]+)" v2="([^"]+)" v3="([^"]+)"\/>/g;
    match = tre.exec(blocks[i]);
    while (match) {
      triangles.push([Number(match[1]), Number(match[2]), Number(match[3])]);
      match = tre.exec(blocks[i]);
    }
    objects.push({ vertices: vertices, triangles: triangles });
  }
  return objects;
}

const rotations = asm.axisAlignedRotations();
expect('24 axis-aligned rotations', rotations.length === 24);
expect(
  'identity is first',
  !!rotations[0] && rotations[0].join(',') === '1,0,0,0,1,0,0,0,1'
);

// Base 30 x 6 x 10 fused with an upright 10 x 6 x 24. Profile area 440.
// Bottom is 180 and the tall wall is 144, so the profile is the largest face.
const base = ops.makeBoxSolid(oc, 30, 6, 10, [0, 0, 0]);
const upright = ops.makeBoxSolid(oc, 10, 6, 24, [0, 0, 0]);
const fused = ops.fuseShapes(oc, base, upright);
release(base);
release(upright);
expect('L fuse ' + (fused.error || ''), fused.ok === true && !!fused.shape);
const shape = fused.ok ? fused.shape : null;
if (shape) {
  const volume = projectFile.shapeVolumeMm3(oc, shape);
  expect('L volume 2640', near(volume, 2640, 0.05));
}

function exportOne(part, options) {
  return asm.exportAssembly3mf(oc, [part], options);
}

const part = {
  name: 'Bracket',
  material: 'PLA',
  shape: shape,
  placement: { x: 0, y: 0, z: 0 },
  shapeLocal: true,
};

const laid = shape ? exportOne(part, { units: 'mm', autoBed: true }) : { ok: false, bytes: null };
expect('L 3mf written', laid.ok === true);
const laidXml = laid.ok ? asm.modelXmlFrom3mf(laid.bytes) : '';
const laidMeshes = parseObjectMeshes(laidXml);
expect('L 3mf one object', laidMeshes.length === 1);

function bedReport(mesh) {
  const bounds = asm.meshBounds(mesh.vertices);
  const faces = asm.meshPlanarFaces(mesh.vertices, mesh.triangles);
  let largest = 0;
  let bed = 0;
  let floating = false;
  for (let i = 0; i < faces.length; i += 1) {
    const face = faces[i];
    if (face.area > largest) largest = face.area;
    const down = face.normal[2] <= -0.999;
    if (down && face.zMin > 0.05) floating = true;
    if (down && face.zMax <= 0.05 && face.zMin <= 1e-4 && face.area > bed) bed = face.area;
  }
  let xmin = Infinity;
  let xmax = -Infinity;
  let ymin = Infinity;
  let ymax = -Infinity;
  const verts = mesh.vertices;
  for (let i = 0; i < verts.length; i += 1) {
    if (verts[i][2] > 0.05) continue;
    if (verts[i][0] < xmin) xmin = verts[i][0];
    if (verts[i][0] > xmax) xmax = verts[i][0];
    if (verts[i][1] < ymin) ymin = verts[i][1];
    if (verts[i][1] > ymax) ymax = verts[i][1];
  }
  return {
    bounds: bounds,
    largest: largest,
    bed: bed,
    floating: floating,
    footX: xmax - xmin,
    footY: ymax - ymin,
  };
}

if (laidMeshes[0] && laidMeshes[0].vertices.length) {
  const report = bedReport(laidMeshes[0]);
  const height = report.bounds.zmax - report.bounds.zmin;
  const foot = Math.min(report.footX, report.footY);
  expect(
    'largest face on z=0 (bed ' + report.bed.toFixed(2) + ' largest ' + report.largest.toFixed(2) + ')',
    report.bed + 0.05 >= report.largest && report.bed > 400
  );
  expect('L height is the thickness', near(height, 6, 0.05) && Math.abs(report.bounds.zmin) <= 1e-3);
  expect('no downward face above the bed', report.floating === false);
  expect('bed footprint covers the profile', foot >= 20 && Math.max(report.footX, report.footY) >= 29);
  expect('L still wound outward', asm.meshSignedVolumeMm3(laidMeshes[0].vertices, laidMeshes[0].triangles) > 2000);
}

const skipped = shape ? exportOne(part, { units: 'mm', autoBed: false }) : { ok: false };
const skipMeshes = parseObjectMeshes(skipped.ok ? asm.modelXmlFrom3mf(skipped.bytes) : '');
if (skipMeshes[0] && skipMeshes[0].vertices.length) {
  const bounds = asm.meshBounds(skipMeshes[0].vertices);
  expect('autoBed off keeps the arm', (bounds.zmax - bounds.zmin) >= 24 - 0.05);
}

const other = ops.makeBoxSolid(oc, 4, 4, 4, [40, 0, 0]);
const pair = shape ? asm.exportAssembly3mf(oc, [
  part,
  { name: 'Block', material: 'PLA', shape: other, placement: { x: 0, y: 0, z: 0 }, shapeLocal: true },
], { units: 'mm', autoBed: true }) : { ok: false };
const pairMeshes = parseObjectMeshes(pair.ok ? asm.modelXmlFrom3mf(pair.bytes) : '');
expect('two bodies stay two objects', pairMeshes.length === 2);
if (pairMeshes[0] && pairMeshes[0].vertices.length) {
  const bounds = asm.meshBounds(pairMeshes[0].vertices);
  expect('second body skips the bed pose', (bounds.zmax - bounds.zmin) >= 24 - 0.05);
}

const lifted = shape ? exportOne({
  name: 'Bracket',
  material: 'PLA',
  shape: shape,
  placement: { x: 5, y: 0, z: 12 },
  shapeLocal: true,
}, { units: 'mm' }) : { ok: false };
const liftedXml = lifted.ok ? asm.modelXmlFrom3mf(lifted.bytes) : '';
expect('turned part drops the old placement', liftedXml.indexOf('transform="1 0 0 0 1 0 0 0 1 0 0 0"') >= 0);
const liftedMeshes = parseObjectMeshes(liftedXml);
if (liftedMeshes[0] && liftedMeshes[0].vertices.length) {
  const bounds = asm.meshBounds(liftedMeshes[0].vertices);
  expect(
    'lifted L is seated',
    Math.abs(bounds.zmin) <= 1e-3 && near(bounds.zmax - bounds.zmin, 6, 0.05)
  );
}

const page = readFileSync(path.join(root, 'web', 'index.html'), 'utf8');
expect('single-body STL lays on the bed', page.indexOf('Module.exportStl()') >= 0);
expect('multi-body STL stays raw', page.indexOf('Module.exportStlRaw') >= 0);
expect('multi-body 3MF stays raw', page.indexOf('Module.export3mfRaw') >= 0);

release(shape);
release(other);

if (failures.length) {
  console.error(failures.length + ' failed');
  process.exit(1);
}
console.log('ok');
