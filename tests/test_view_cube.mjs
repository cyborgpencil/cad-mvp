// View-cube swipe face table and tap threshold. No OCCT, no DOM.
import { pathToFileURL, fileURLToPath } from 'node:url';
import path from 'node:path';

const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..');
const cube = await import(pathToFileURL(path.join(root, 'web', 'view-cube.mjs')).href);

const failures = [];

function expect(name, got, want) {
  if (got === want) {
    console.log('PASS ' + name);
    return;
  }
  console.error('FAIL ' + name + ' got ' + JSON.stringify(got) + ' want ' + JSON.stringify(want));
  failures.push(name);
}

const TABLE = {
  front: { left: 'right', right: 'left', up: 'top', down: 'bottom' },
  right: { left: 'back', right: 'front', up: 'top', down: 'bottom' },
  back: { left: 'left', right: 'right', up: 'top', down: 'bottom' },
  left: { left: 'front', right: 'back', up: 'top', down: 'bottom' },
  top: { left: 'left', right: 'right', up: 'back', down: 'front' },
  bottom: { left: 'left', right: 'right', up: 'front', down: 'back' }
};

const DIRS = ['left', 'right', 'up', 'down'];

expect('SWIPE_PX is 24', cube.SWIPE_PX, 24);
expect('SWIPE_MS is 400', cube.SWIPE_MS, 400);

for (const face of Object.keys(TABLE)) {
  for (const dir of DIRS) {
    expect(face + ' + ' + dir, cube.nextCubeFace(face, dir), TABLE[face][dir]);
  }
}

expect('Front mixed case', cube.nextCubeFace('Front', 'LEFT'), 'right');
expect('unknown face', cube.nextCubeFace('iso', 'left'), null);
expect('unknown dir', cube.nextCubeFace('front', 'in'), null);
expect('empty face', cube.nextCubeFace('', 'left'), null);
expect('empty dir', cube.nextCubeFace('front', ''), null);

let ring = 'front';
for (let i = 0; i < 4; i += 1) ring = cube.nextCubeFace(ring, 'left');
expect('left ring returns to front', ring, 'front');

ring = 'front';
for (let i = 0; i < 4; i += 1) ring = cube.nextCubeFace(ring, 'right');
expect('right ring returns to front', ring, 'front');

expect('top down then down is bottom', cube.nextCubeFace(cube.nextCubeFace('top', 'down'), 'down'), 'bottom');
expect('bottom up then up is top', cube.nextCubeFace(cube.nextCubeFace('bottom', 'up'), 'up'), 'top');

expect('tap 0 px', cube.swipeDirection(0, 0, 100), null);
expect('tap 23 px right', cube.swipeDirection(23, 0, 100), null);
expect('tap 23 px up', cube.swipeDirection(0, -23, 100), null);
expect('swipe 24 px right', cube.swipeDirection(24, 0, 100), 'right');
expect('swipe 24 px left', cube.swipeDirection(-24, 0, 100), 'left');
expect('swipe 24 px up', cube.swipeDirection(0, -24, 100), 'up');
expect('swipe 24 px down', cube.swipeDirection(0, 24, 100), 'down');
expect('swipe at 400 ms', cube.swipeDirection(24, 0, 400), 'right');
expect('too slow 401 ms', cube.swipeDirection(24, 0, 401), null);
expect('negative dt', cube.swipeDirection(24, 0, -1), null);
expect('dominant x', cube.swipeDirection(30, 10, 80), 'right');
expect('dominant y', cube.swipeDirection(10, -30, 80), 'up');
expect('diagonal hypot tap', cube.swipeDirection(16, 16, 80), null);
expect('diagonal hypot swipe', cube.swipeDirection(18, 18, 80), 'right');

if (failures.length) {
  console.error('FAIL view_cube ' + failures.length);
  process.exit(1);
}
console.log('PASS view_cube');
