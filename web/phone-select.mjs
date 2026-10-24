// Phone pick filter, tap-vs-drag, Multi add/remove, and the edge touch radius.
// The page wires pointer events and the existing highlight path.
// Tap slop stays in viewport-selection.mjs (TAP_SLOP_PX). Face and body
// touch picks stay on selection.mjs TOUCH_PICK_TOLERANCE_PX. This file
// only widens Edge.

export const PICK_FILTERS = ['body', 'face', 'edge', 'vertex'];

export const FILTER_LABELS = {
  body: 'Body',
  face: 'Face',
  edge: 'Edge',
  vertex: 'Vertex',
};

// Screen-px radius for an Edge tap. Larger than selection.mjs
// TOUCH_PICK_TOLERANCE_PX (20). Face and body stay on that radius.
// Team-chosen, TBD for Erik.
export const EDGE_TOUCH_TOLERANCE_PX = 32;

// Bottom-bar chip and Multi toggle. WCAG 2.5.5 / Apple HIG.
export const CHIP_MIN_PX = 44;

const MODE_BY_FILTER = {
  body: 'item',
  face: 'face',
  edge: 'edge',
  vertex: 'vertex',
};

const FILTER_BY_MODE = {
  item: 'body',
  face: 'face',
  edge: 'edge',
  vertex: 'vertex',
};

export function filterLabel(filter) {
  return FILTER_LABELS[filter] || FILTER_LABELS.body;
}

export function modeForFilter(filter) {
  return MODE_BY_FILTER[filter] || 'item';
}

export function filterForMode(mode) {
  return FILTER_BY_MODE[mode] || 'body';
}

// Body -> Face -> Edge -> Vertex -> Body. Unknown starts at Body.
export function nextFilter(filter) {
  const index = PICK_FILTERS.indexOf(filter);
  if (index < 0) return PICK_FILTERS[0];
  return PICK_FILTERS[(index + 1) % PICK_FILTERS.length];
}

// Edge touch and pen use EDGE_TOUCH_TOLERANCE_PX. Mouse stays on the
// shared mouse radius. Every other filter uses the caller's touch or
// mouse radius (selection.mjs).
export function pickTolerancePx(modeOrFilter, pointerType, touchPx, mousePx) {
  const named = FILTER_BY_MODE[modeOrFilter] || modeOrFilter;
  const filter = PICK_FILTERS.indexOf(named) >= 0 ? named : 'body';
  const touch = pointerType === 'touch' || pointerType === 'pen';
  const baseTouch = Number(touchPx) > 0 ? Number(touchPx) : 20;
  const baseMouse = Number(mousePx) > 0 ? Number(mousePx) : 8;
  if (filter === 'edge' && touch) return EDGE_TOUCH_TOLERANCE_PX;
  return touch ? baseTouch : baseMouse;
}

// 'tap' selects. 'drag' is an orbit and never selects. 'cancel' never selects.
// Movement equal to the slop is a drag, matching tapSlopPx() (>= slop).
export function classifyPointer(dx, dy, slopPx, cancelled) {
  if (cancelled) return 'cancel';
  const limit = Number(slopPx);
  const slop = Number.isFinite(limit) ? limit : 8;
  const x = Number(dx);
  const y = Number(dy);
  if (!Number.isFinite(x) || !Number.isFinite(y)) return 'cancel';
  return Math.hypot(x, y) < slop ? 'tap' : 'drag';
}

export function shouldSelect(dx, dy, slopPx, cancelled) {
  return classifyPointer(dx, dy, slopPx, cancelled) === 'tap';
}

// Multi off: a hit replaces the selection. Multi on: a hit adds, or
// removes when it is already selected. An empty hit clears either way.
// Does not mutate selectedIds. Shift and Ctrl stay on selection.mjs.
export function selectionFromTap(mode, selectedIds, hitId, multi) {
  const ids = Array.isArray(selectedIds) ? selectedIds.slice() : [];
  const empty = hitId == null || hitId === '';
  let action = 'replace';
  if (empty) {
    ids.length = 0;
    action = 'clear';
  } else if (multi) {
    const at = ids.indexOf(hitId);
    if (at >= 0) {
      ids.splice(at, 1);
      action = 'remove';
    } else {
      ids.push(hitId);
      action = 'add';
    }
  } else {
    ids.length = 0;
    ids.push(hitId);
    action = 'replace';
  }
  const filter = filterForMode(mode);
  const all = filter !== 'body' && ids.length === 0;
  return {
    ids: ids,
    count: ids.length,
    action: action,
    all: all,
    highlight: ids.length > 0,
  };
}

export function selectionCount(ids) {
  return Array.isArray(ids) ? ids.length : 0;
}

export function countText(count) {
  const n = Number(count);
  const value = Number.isFinite(n) && n > 0 ? Math.floor(n) : 0;
  return value === 1 ? '1 selected' : value + ' selected';
}

// Screen point `distance` px to the left of the segment direction
// (client y grows downward). Used to aim an Edge tap between the
// 20 px touch radius and EDGE_TOUCH_TOLERANCE_PX.
export function pointBesideSegment(ax, ay, bx, by, distance) {
  const dx = Number(bx) - Number(ax);
  const dy = Number(by) - Number(ay);
  const len = Math.hypot(dx, dy);
  const mx = (Number(ax) + Number(bx)) / 2;
  const my = (Number(ay) + Number(by)) / 2;
  const d = Number(distance);
  const step = Number.isFinite(d) ? d : 0;
  if (!(len > 0)) return { x: mx, y: my };
  return {
    x: mx + (-dy / len) * step,
    y: my + (dx / len) * step,
  };
}
