// Face delete builds its fixture here: a 40x20x10 mm box with a 6 mm
// through-hole. Volume is BRepGProp.VolumeProperties. No Blink file.
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
  const message = 'delete: libcascade is missing (' + missingLib.join(', ') + '). Run: python web/fetch-libcascade.py';
  if (envSet('CI') || envSet('GITHUB_ACTIONS')) {
    console.error('FAIL ' + message);
    process.exit(1);
  }
  console.error('SKIP ' + message);
  process.exit(77);
}

const { createInstance } = await import(pathToFileURL(path.join(libDir, 'init.single.js')).href);
const ops = await import(pathToFileURL(path.join(root, 'web', 'occt-ops.mjs')).href);
const { inspectSolid } = await import(pathToFileURL(path.join(root, 'web', 'occt-primitives.mjs')).href);
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

expect('BRepAlgoAPI_Defeaturing exported', typeof oc.BRepAlgoAPI_Defeaturing === 'function');
expect('indexed map exported', typeof oc.NCollection_IndexedMap_TopoDS_Shape_TopTools_ShapeMapHasher === 'function'
  || typeof oc.TopTools_IndexedMapOfShape === 'function');

const fixture = ops.buildHoleDeleteFixture(oc);
expect('hole fixture built', !!(fixture && fixture.ok && fixture.shape));
if (fixture && fixture.ok) {
  const plain = fixture.plainVolumeMm3;
  const holed = fixture.volumeMm3;
  expect('plain box volume is BRepGProp', Number.isFinite(plain) && plain > 7000);
  expect('hole removes material', holed < plain - 1);
  const view = inspectSolid(oc, fixture.shape);
  const wall = (view.topology.faces || []).find(function (face) { return face.surface === 'GeomAbs_Cylinder'; });
  expect('hole wall is a cylinder face', !!(wall && wall.occtIndex > 0));
  const before = ops.solidVolumeMm3(oc, fixture.shape);
  const healed = wall ? ops.defeatureFaceOrdinals(oc, fixture.shape, [wall.occtIndex - 1]) : null;
  const afterInput = ops.solidVolumeMm3(oc, fixture.shape);
  expect('failed path is not this one', !!(healed && healed.ok && healed.shape));
  if (healed && healed.ok) {
    const after = ops.solidVolumeMm3(oc, healed.shape);
    const valid = new oc.BRepCheck_Analyzer(healed.shape);
    expect(
      'hole wall delete volume within 0.01 (' + after + ' vs ' + plain + ')',
      Math.abs(after - plain) <= ops.DELETE_VOLUME_TOL_MM3
    );
    expect('hole wall delete is valid', valid.IsValid() === true);
    valid.delete();
    const healedView = inspectSolid(oc, healed.shape);
    expect('hole wall delete drops a face', healedView.topology.faces.length < view.topology.faces.length);
    release(healed.shape);
  }
  expect('input shape unchanged by defeaturing', Math.abs(afterInput - before) <= 1e-6);
  release(fixture.shape);
}

const box = ops.makeBoxSolid(oc, 40, 20, 10, [0, 0, 0]);
expect('plain box built', !!box);
if (box) {
  const before = ops.solidVolumeMm3(oc, box);
  const view = inspectSolid(oc, box);
  const plane = (view.topology.faces || []).find(function (face) { return face.surface === 'GeomAbs_Plane'; });
  const failed = plane ? ops.defeatureFaceOrdinals(oc, box, [plane.occtIndex - 1]) : null;
  const after = ops.solidVolumeMm3(oc, box);
  expect('box face delete fails', !!(failed && failed.ok === false && !failed.shape));
  expect('box face delete error', !!(failed && failed.error && failed.error.indexOf('DELETE_DONE') < 0));
  expect('box face delete keeps volume', Math.abs(after - before) <= 1e-6);
  const still = new oc.BRepCheck_Analyzer(box);
  expect('box face delete keeps a valid solid', still.IsValid() === true);
  still.delete();

  const edge = view.topology.edges[0];
  const alone = ops.deleteOwningFeature(oc, box, [], {
    kind: 'edge',
    a: edge.pts[0],
    b: edge.pts[edge.pts.length - 1],
  });
  expect('edge without a feature is refused', !!(alone && alone.ok === false && alone.error === ops.DELETE_EDGE_ALONE));
  expect('refused edge keeps volume', Math.abs(ops.solidVolumeMm3(oc, box) - before) <= 1e-6);
  release(box);
}

// Fillet one real edge, then delete that feature.
const stock = ops.makeBoxSolid(oc, 40, 20, 10, [0, 0, 0]);
if (stock) {
  const plain = ops.solidVolumeMm3(oc, stock);
  const stockView = inspectSolid(oc, stock);
  const edge = stockView.topology.edges[0];
  const segment = { a: edge.pts[0], b: edge.pts[edge.pts.length - 1] };
  const filleted = ops.applyPickedEdgeOp(oc, stock, [segment], 'fillet', 2);
  expect('fillet built', !!(filleted && filleted.ok && filleted.featureFaces && filleted.featureFaces.length));
  if (filleted && filleted.ok) {
    const features = [{ kind: 'fillet', faces: filleted.featureFaces }];
    const filletedView = inspectSolid(oc, filleted.shape);
    let onEdge = null;
    for (let i = 0; i < filletedView.topology.edges.length; i += 1) {
      const candidate = filletedView.topology.edges[i];
      const mid = candidate.pts[Math.floor((candidate.pts.length - 1) / 2)];
      const attempt = ops.deleteOwningFeature(oc, filleted.shape, features, {
        kind: 'edge',
        a: candidate.pts[0],
        b: candidate.pts[candidate.pts.length - 1],
      });
      if (attempt && attempt.ok) {
        onEdge = { mid: mid, result: attempt };
        break;
      }
    }
    expect('fillet edge delete succeeds', !!(onEdge && onEdge.result && onEdge.result.ok));
    if (onEdge && onEdge.result && onEdge.result.ok) {
      const valid = new oc.BRepCheck_Analyzer(onEdge.result.shape);
      const healed = inspectSolid(oc, onEdge.result.shape);
      const cylinders = (healed.topology.faces || []).filter(function (face) {
        return face.surface === 'GeomAbs_Cylinder';
      }).length;
      expect('fillet delete is valid', valid.IsValid() === true);
      expect('fillet face is gone', cylinders === 0);
      expect(
        'fillet delete volume back within 0.01',
        Math.abs(ops.solidVolumeMm3(oc, onEdge.result.shape) - plain) <= ops.DELETE_VOLUME_TOL_MM3
      );
      valid.delete();
      release(onEdge.result.shape);
    }
    expect(
      'fillet input kept until replaced',
      Math.abs(ops.solidVolumeMm3(oc, filleted.shape) - filleted.volumeMm3) <= 1e-4
    );
    release(filleted.shape);
  }
  release(stock);
}

if (failures.length) {
  console.error('FAIL delete ' + failures.length);
  process.exit(1);
}
console.log('PASS delete');
