// Three-finger undo/redo classifier and gesture session. No OCCT, no DOM.
import { pathToFileURL, fileURLToPath } from 'node:url';
import path from 'node:path';

const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..');
const finger = await import(pathToFileURL(path.join(root, 'web', 'three-finger.mjs')).href);

const failures = [];

function expect(name, got, want) {
  if (got === want) {
    console.log('PASS ' + name);
    return;
  }
  console.error('FAIL ' + name + ' got ' + JSON.stringify(got) + ' want ' + JSON.stringify(want));
  failures.push(name);
}

expect('SWIPE_PX is 40', finger.SWIPE_PX, 40);
expect('SWIPE_MS is 400', finger.SWIPE_MS, 400);
expect('storage key', finger.STORAGE_KEY, 'cadcam.threeFingerUndo');

const PX = finger.SWIPE_PX;
const MS = finger.SWIPE_MS;

function sample(over) {
  return Object.assign({
    enabled: true,
    cancelled: false,
    pointers: 3,
    dx: -PX,
    dy: 0,
    dt: 100
  }, over);
}

expect('classify left', finger.classifyThreeFinger(sample({ dx: -PX })), 'undo');
expect('classify right', finger.classifyThreeFinger(sample({ dx: PX })), 'redo');
expect('classify short', finger.classifyThreeFinger(sample({ dx: -(PX - 1) })), null);
expect('classify short right', finger.classifyThreeFinger(sample({ dx: PX - 1 })), null);
expect('classify vertical', finger.classifyThreeFinger(sample({ dx: 10, dy: PX + 30 })), null);
expect('classify vertical dominates a long x', finger.classifyThreeFinger(sample({ dx: -PX, dy: -(PX + 1) })), null);
expect('classify tie is horizontal', finger.classifyThreeFinger(sample({ dx: PX, dy: PX })), 'redo');
expect('classify 2-finger', finger.classifyThreeFinger(sample({ pointers: 2 })), null);
expect('classify 1-finger', finger.classifyThreeFinger(sample({ pointers: 1 })), null);
expect('classify 4-finger', finger.classifyThreeFinger(sample({ pointers: 4 })), null);
expect('classify toggle off', finger.classifyThreeFinger(sample({ enabled: false })), null);
expect('classify cancel', finger.classifyThreeFinger(sample({ cancelled: true })), null);
expect('classify at window', finger.classifyThreeFinger(sample({ dt: MS })), 'undo');
expect('classify past window', finger.classifyThreeFinger(sample({ dt: MS + 1 })), null);
expect('classify negative dt', finger.classifyThreeFinger(sample({ dt: -1 })), null);
expect('classify empty', finger.classifyThreeFinger(null), null);

const mem = new Map();
const store = {
  getItem(key) { return mem.has(key) ? mem.get(key) : null; },
  setItem(key, value) { mem.set(key, String(value)); }
};
expect('toggle defaults on', finger.readEnabled(store), true);
expect('toggle write off', finger.writeEnabled(store, false), true);
expect('toggle reads off', finger.readEnabled(store), false);
expect('toggle write on', finger.writeEnabled(store, true), true);
expect('toggle reads on', finger.readEnabled(store), true);
expect('stored on is 1', store.getItem(finger.STORAGE_KEY), '1');
finger.writeEnabled(store, false);
expect('stored off is 0', store.getItem(finger.STORAGE_KEY), '0');
expect('word off', finger.readEnabled({ getItem() { return 'off'; } }), false);
expect('word false', finger.readEnabled({ getItem() { return 'false'; } }), false);
expect('blank is on', finger.readEnabled({ getItem() { return ''; } }), true);
expect('missing store is on', finger.readEnabled(null), true);

function swipe(dx, dy, enabled, tEnd) {
  const s = finger.createThreeFingerSession();
  s.down(1, 0, 0, 0);
  s.down(2, 30, 4, 0);
  s.down(3, 60, -4, 0);
  s.move(1, dx, dy);
  s.move(2, 30 + dx, 4 + dy);
  s.move(3, 60 + dx, -4 + dy);
  const first = s.up(1, dx, dy, tEnd == null ? 120 : tEnd, enabled);
  const second = s.up(2, 30 + dx, 4 + dy, tEnd == null ? 120 : tEnd, enabled);
  const third = s.up(3, 60 + dx, -4 + dy, tEnd == null ? 130 : tEnd, enabled);
  return { first: first, second: second, third: third, session: s };
}

let left = swipe(-PX, 0, true);
expect('session left', left.first, 'undo');
expect('session left once', left.second, null);
expect('session left third', left.third, null);

let right = swipe(PX, 2, true);
expect('session right', right.first, 'redo');
expect('session right once', right.second, null);

let short = swipe(-(PX - 1), 0, true);
expect('session short', short.first, null);

let vertical = swipe(12, PX + 20, true);
expect('session vertical', vertical.first, null);

const two = finger.createThreeFingerSession();
two.down(1, 0, 0, 0);
two.down(2, 20, 0, 0);
two.move(1, -PX - 10, 0);
two.move(2, 20 - PX - 10, 0);
expect('session 2-finger', two.up(1, -PX - 10, 0, 80, true), null);
expect('session 2-finger other', two.up(2, 20 - PX - 10, 0, 90, true), null);

let off = swipe(-PX - 8, 0, false);
expect('session toggle off', off.first, null);
expect('session toggle off second', off.second, null);

const aborted = finger.createThreeFingerSession();
aborted.down(1, 0, 0, 0);
aborted.down(2, 10, 0, 0);
aborted.down(3, 20, 0, 0);
aborted.move(1, -PX - 5, 0);
aborted.move(2, 10 - PX - 5, 0);
aborted.move(3, 20 - PX - 5, 0);
expect('session cancel', aborted.cancel(2), null);
expect('session cancel up', aborted.up(1, -PX - 5, 0, 100, true), null);
expect('session cancel last', aborted.up(3, 20 - PX - 5, 0, 110, true), null);

const lost = finger.createThreeFingerSession();
lost.down(1, 0, 0, 0);
lost.down(2, 10, 0, 10);
lost.down(3, 20, 0, 20);
lost.move(1, PX + 6, 0);
lost.move(2, 10 + PX + 6, 0);
lost.move(3, 20 + PX + 6, 0);
expect('session lostpointercapture', lost.lostCapture(1), null);
expect('session lost up', lost.up(1, PX + 6, 0, 90, true), null);
expect('session lost other', lost.up(2, 10 + PX + 6, 0, 100, true), null);

const slow = swipe(-PX - 4, 0, true, MS + 5);
expect('session past window', slow.first, null);

const again = finger.createThreeFingerSession();
again.down(1, 0, 0, 0);
again.down(2, 10, 0, 0);
again.down(3, 20, 0, 0);
again.move(1, -PX, 0);
again.move(2, 10 - PX, 0);
again.move(3, 20 - PX, 0);
expect('session first gesture', again.up(1, -PX, 0, 50, true), 'undo');
again.up(2, 10 - PX, 0, 60, true);
again.up(3, 20 - PX, 0, 70, true);
again.down(4, 0, 0, 200);
again.down(5, 12, 0, 200);
again.down(6, 24, 0, 200);
again.move(4, PX, 0);
again.move(5, 12 + PX, 0);
again.move(6, 24 + PX, 0);
expect('session next gesture', again.up(4, PX, 0, 240, true), 'redo');

const extra = finger.createThreeFingerSession();
extra.down(1, 0, 0, 0);
extra.down(2, 10, 0, 0);
extra.down(3, 20, 0, 0);
extra.down(4, 30, 0, 0);
extra.move(1, -PX - 10, 0);
expect('session fourth finger', extra.up(1, -PX - 10, 0, 80, true), null);

if (failures.length) {
  console.error('FAIL three_finger ' + failures.length);
  process.exit(1);
}
console.log('PASS three_finger');
