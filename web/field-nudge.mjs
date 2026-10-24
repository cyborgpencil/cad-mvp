// Focused-field nudge for size, centre, and rotation values.
// Axis is horizontal (clientX). Right increases. Left decreases.
// Up and down are not a nudge axis. Once vertical travel dominates,
// the gesture locks to scroll and never changes the value. A tie
// (|dx| === |dy|) locks horizontal. Team choice, 2026-10-23.
// 24 CSS px is one step. Size and centre step 1 mm. Rotation steps
// 1 degree. Erik may change either value after phone testing.
// Size clamps at MIN_SIZE_MM (0.1), the same floor as the gizmo.
// A step that cannot move the value is not a change.
// Each returned step is one undo step for the caller. A pointermove
// that does not cross a new step returns 0. pointercancel and
// lostpointercapture end the gesture and return no further steps.

export const STEP_PX = 24;
export const AXIS = 'x';
export const MM_STEP = 1;
export const DEG_STEP = 1;
export const MIN_SIZE_MM = 0.1;

const SIZE_IDS = {
  boxSx: true,
  boxSy: true,
  boxSz: true,
  cylD: true,
  cylH: true,
  discD: true,
  discT: true,
  bboxX: true,
  bboxY: true,
  bboxZ: true
};

const CENTRE_IDS = {
  primCx: true,
  primCy: true,
  primCz: true
};

const ROT_IDS = {
  primRx: true,
  primRy: true,
  primRz: true
};

export function fieldSpec(id) {
  const name = String(id || '');
  if (SIZE_IDS[name]) {
    return { id: name, unit: 'mm', kind: 'size', step: MM_STEP, min: MIN_SIZE_MM };
  }
  if (CENTRE_IDS[name]) {
    return { id: name, unit: 'mm', kind: 'centre', step: MM_STEP, min: null };
  }
  if (ROT_IDS[name]) {
    return { id: name, unit: 'deg', kind: 'rotation', step: DEG_STEP, min: null };
  }
  return null;
}

// Signed step count for horizontal travel. Right is positive.
export function stepsFromTravel(dx, stepPx) {
  const px = Number(stepPx) > 0 ? Number(stepPx) : STEP_PX;
  const x = Number(dx);
  if (!Number.isFinite(x)) return 0;
  return Math.trunc(x / px);
}

// '' until travel reaches one step on either axis, then 'x' or 'y'.
export function lockAxis(dx, dy, stepPx) {
  const px = Number(stepPx) > 0 ? Number(stepPx) : STEP_PX;
  const x = Number(dx);
  const y = Number(dy);
  if (!Number.isFinite(x) || !Number.isFinite(y)) return '';
  if (Math.abs(x) < px && Math.abs(y) < px) return '';
  return Math.abs(x) >= Math.abs(y) ? 'x' : 'y';
}

// Size never goes below its floor, and a negative step does not raise
// a value that is already on or under that floor. Centre and rotation
// are not clamped.
export function clampValue(current, delta, spec) {
  const value = Number(current);
  const step = Number(delta);
  if (!Number.isFinite(value) || !Number.isFinite(step)) {
    return Number.isFinite(value) ? value : current;
  }
  if (!spec || spec.kind !== 'size') return value + step;
  const floor = Number(spec.min);
  const min = Number.isFinite(floor) ? floor : MIN_SIZE_MM;
  let next = value + step;
  if (next < min) {
    if (value <= min) return value;
    next = min;
  }
  if (!(next > 0)) return value;
  return next;
}

// One gesture. down() arms only when focused is true.
// move() returns the new horizontal steps since the previous move.
// cancel() and lostCapture() end it; later moves return 0.
export function createFieldNudgeSession() {
  let pointerId = null;
  let originX = 0;
  let originY = 0;
  let axis = '';
  let emitted = 0;
  let ended = false;
  let armed = false;

  function finish() {
    ended = true;
    armed = false;
  }

  return {
    down(id, x, y, focused) {
      if (armed && !ended && pointerId !== id) return false;
      pointerId = id;
      originX = Number(x);
      originY = Number(y);
      axis = '';
      emitted = 0;
      ended = false;
      armed = focused === true && Number.isFinite(originX) && Number.isFinite(originY);
      return armed;
    },
    move(id, x, y) {
      if (!armed || ended || id !== pointerId) return 0;
      const dx = Number(x) - originX;
      const dy = Number(y) - originY;
      if (!Number.isFinite(dx) || !Number.isFinite(dy)) return 0;
      if (!axis) {
        axis = lockAxis(dx, dy, STEP_PX);
        if (!axis) return 0;
      }
      if (axis !== 'x') return 0;
      const total = stepsFromTravel(dx, STEP_PX);
      const fresh = total - emitted;
      emitted = total;
      return fresh;
    },
    cancel(id) {
      if (pointerId != null && id != null && id !== pointerId) return 0;
      finish();
      return 0;
    },
    lostCapture(id) {
      if (pointerId != null && id != null && id !== pointerId) return 0;
      finish();
      return 0;
    },
    up(id) {
      if (pointerId != null && id != null && id !== pointerId) return 0;
      finish();
      return 0;
    },
    lockedAxis() {
      return axis;
    },
    ended() {
      return ended;
    },
    pointerId() {
      return pointerId;
    }
  };
}
