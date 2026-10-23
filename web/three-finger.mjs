// Three-finger undo/redo on the viewport.
// Own threshold, separate from the view-cube swipe (24 px / hypot).
// The centroid must travel at least SWIPE_PX horizontally, horizontal
// travel must be at least the vertical travel, and the gesture must end
// within SWIPE_MS of the third pointer landing. One action per gesture.
// 40 CSS px / 400 ms. Erik may change this after phone testing.
// Assumption: a tie between the axes counts as horizontal.
// Left is negative clientX (undo). Right is positive clientX (redo).

export const SWIPE_PX = 40;
export const SWIPE_MS = 400;
export const STORAGE_KEY = 'cadcam.threeFingerUndo';

export function readEnabled(store) {
  try {
    if (!store || typeof store.getItem !== 'function') return true;
    const raw = store.getItem(STORAGE_KEY);
    if (raw == null || raw === '') return true;
    const text = String(raw).trim().toLowerCase();
    if (text === '0' || text === 'false' || text === 'off') return false;
    return true;
  } catch (err) {
    return true;
  }
}

export function writeEnabled(store, enabled) {
  if (!store || typeof store.setItem !== 'function') return false;
  try {
    store.setItem(STORAGE_KEY, enabled ? '1' : '0');
    return true;
  } catch (err) {
    return false;
  }
}

// Returns 'undo', 'redo', or null.
// sample: { enabled, cancelled, pointers, dx, dy, dt }
export function classifyThreeFinger(sample) {
  const src = sample || {};
  if (src.enabled === false) return null;
  if (src.cancelled === true) return null;
  const n = Number(src.pointers);
  if (n !== 3) return null;
  const x = Number(src.dx);
  const y = Number(src.dy);
  const t = Number(src.dt);
  if (!Number.isFinite(x) || !Number.isFinite(y) || !Number.isFinite(t)) return null;
  if (t < 0 || t > SWIPE_MS) return null;
  if (Math.abs(x) < SWIPE_PX) return null;
  if (Math.abs(x) < Math.abs(y)) return null;
  if (x < 0) return 'undo';
  if (x > 0) return 'redo';
  return null;
}

function centroid(map, ids) {
  let sx = 0;
  let sy = 0;
  let n = 0;
  for (let i = 0; i < ids.length; i += 1) {
    const p = map.get(ids[i]);
    if (!p) continue;
    sx += p.x;
    sy += p.y;
    n += 1;
  }
  if (!n) return null;
  return { x: sx / n, y: sy / n };
}

// Pointer state machine. down/move/up/cancel/lostCapture.
// up() returns 'undo', 'redo', or null. A gesture fires at most once,
// when the first of the three pointers lifts, if classify allows it.
// cancel() and lostCapture() end the gesture with no action.
export function createThreeFingerSession() {
  const pointers = new Map();
  let origin = null;
  let armedIds = null;
  let cancelled = false;
  let consumed = false;
  let sawExtra = false;

  function reset() {
    origin = null;
    armedIds = null;
    cancelled = false;
    consumed = false;
    sawExtra = false;
  }

  function arm(now) {
    if (origin || cancelled || consumed || sawExtra) return;
    if (pointers.size !== 3) return;
    armedIds = Array.from(pointers.keys());
    const c = centroid(pointers, armedIds);
    if (!c) return;
    origin = { x: c.x, y: c.y, t: now };
  }

  function endIfIdle() {
    if (pointers.size === 0) reset();
  }

  return {
    down(id, x, y, now) {
      pointers.set(id, { x: Number(x), y: Number(y) });
      if (pointers.size > 3) sawExtra = true;
      arm(Number(now));
      return pointers.size;
    },
    move(id, x, y) {
      if (!pointers.has(id)) return;
      pointers.set(id, { x: Number(x), y: Number(y) });
    },
    up(id, x, y, now, enabled) {
      if (pointers.has(id)) pointers.set(id, { x: Number(x), y: Number(y) });
      let action = null;
      const member = !!(armedIds && armedIds.indexOf(id) !== -1 && pointers.has(id));
      if (!consumed && !cancelled && !sawExtra && member && pointers.size === 3 && origin) {
        const c = centroid(pointers, armedIds);
        consumed = true;
        if (c) {
          action = classifyThreeFinger({
            enabled: enabled !== false,
            cancelled: false,
            pointers: 3,
            dx: c.x - origin.x,
            dy: c.y - origin.y,
            dt: Number(now) - origin.t
          });
        }
      }
      pointers.delete(id);
      endIfIdle();
      return action;
    },
    cancel(id) {
      cancelled = true;
      consumed = true;
      pointers.delete(id);
      endIfIdle();
      return null;
    },
    lostCapture() {
      if (!origin || consumed) return null;
      cancelled = true;
      consumed = true;
      return null;
    }
  };
}
