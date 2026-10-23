// View-cube swipe: adjacent face and tap-vs-swipe threshold.
// Team choice (3T, 2026-10-23): 24 CSS px, dominant axis. SWIPE_MS (400) is
// the old flick window. Travel that has already reached SWIPE_PX is still a
// swipe when the finger is slower than that, so a slow drag is not handed
// back to the face picker. The pixel threshold stays separate from tap slop.
// Horizontal swipes walk Front > Right > Back > Left. Vertical swipes go
// Top / Bottom. From Top / Bottom, up/down go Back/Front (Top) or Front/Back
// (Bottom); left/right go Left/Right.

export const SWIPE_PX = 24;
export const SWIPE_MS = 400;

export const FACE_RING = ['front', 'right', 'back', 'left'];

const DIRS = { left: true, right: true, up: true, down: true };

export function swipeDirection(dx, dy, dt) {
  const x = Number(dx);
  const y = Number(dy);
  const t = Number(dt);
  if (!Number.isFinite(x) || !Number.isFinite(y) || !Number.isFinite(t)) return null;
  if (t < 0) return null;
  // A qualified travel is a swipe even when it takes longer than SWIPE_MS.
  if (Math.hypot(x, y) < SWIPE_PX) return null;
  if (Math.abs(x) >= Math.abs(y)) return x < 0 ? 'left' : 'right';
  return y < 0 ? 'up' : 'down';
}

export function nextCubeFace(face, dir) {
  const f = String(face || '').toLowerCase();
  const d = String(dir || '').toLowerCase();
  if (!DIRS[d]) return null;
  if (f === 'top') {
    if (d === 'up') return 'back';
    if (d === 'down') return 'front';
    if (d === 'left') return 'left';
    return 'right';
  }
  if (f === 'bottom') {
    if (d === 'up') return 'front';
    if (d === 'down') return 'back';
    if (d === 'left') return 'left';
    return 'right';
  }
  const i = FACE_RING.indexOf(f);
  if (i < 0) return null;
  if (d === 'up') return 'top';
  if (d === 'down') return 'bottom';
  if (d === 'left') return FACE_RING[(i + 1) % 4];
  return FACE_RING[(i + 3) % 4];
}
