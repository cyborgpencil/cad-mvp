import { pathToFileURL, fileURLToPath } from 'node:url';
import path from 'node:path';

const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..');
const initUrl = pathToFileURL(path.join(root, 'builds', 'libcascade', 'dist', 'init.single.js')).href;
const gateUrl = pathToFileURL(path.join(root, 'web', 'occt-gate.mjs')).href;

const { createInstance } = await import(initUrl);
const { checkOcctGate, closedBoxMesh, openBoxMesh, box20Mesh } = await import(gateUrl);

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
