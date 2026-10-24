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
// Confirm sizes. Each tool writes its own default when it is picked.
// Team-chosen (3T, 2026-10-23). Same millimetres as EDGE_FILLET_RADIUS_MM
// and EDGE_CHAMFER_DISTANCE_MM in occt-ops.mjs.
export const FILLET_DEFAULT_MM = 2;
export const CHAMFER_DEFAULT_MM = 0.5;

// Shown when picked edges belong to more than one body. Confirm stays off.
export const CROSS_BODY_MESSAGE = 'pick edges on one body';

// OCCT rejected the fillet or chamfer (size too big, or a re-fillet that
// does not fit). The last shape stays. Team-chosen (3T, 2026-10-23).
export const SMALLER_SIZE_MESSAGE = 'Try a smaller size.';

// Tapping Fillet or Chamfer arms that op and switches the chip to Edge.
export function armEdgeTool(op) {
  const kind = op === 'chamfer' ? 'chamfer' : 'fillet';
  return {
    op: kind,
    filter: 'edge',
    mode: 'edge',
    sizeMm: kind === 'chamfer' ? CHAMFER_DEFAULT_MM : FILLET_DEFAULT_MM,
  };
}

// Blank, zero, and negative sizes are rejected before OCCT runs.
// A size OCCT cannot build is not decided here.
export function parseEdgeSize(text) {
  if (text == null) return { ok: false, size: NaN };
  const raw = String(text).trim().replace(',', '.');
  if (!raw) return { ok: false, size: NaN };
  const n = Number(raw);
  if (!Number.isFinite(n) || !(n > 0)) return { ok: false, size: n };
  return { ok: true, size: n };
}

// One body keeps the edge id (e0). Several bodies prefix the body id
// so e0 on two solids does not collide.
export function edgePickId(bodyId, edgeId, bodyCount) {
  const edge = edgeId == null ? '' : String(edgeId);
  if (!(Number(bodyCount) > 1)) return edge;
  return String(bodyId) + ':' + edge;
}

export function splitEdgePick(id, singleBodyId) {
  const text = id == null ? '' : String(id);
  const cut = text.indexOf(':');
  if (cut > 0) {
    return { bodyId: text.slice(0, cut), edgeId: text.slice(cut + 1) };
  }
  return { bodyId: singleBodyId ? String(singleBodyId) : '', edgeId: text };
}

// picks are selected ids ("b1:e0" or "e0") or { bodyId } rows.
export function edgeBodyIds(picks, singleBodyId) {
  const ids = [];
  const list = Array.isArray(picks) ? picks : [];
  for (let i = 0; i < list.length; i += 1) {
    const item = list[i];
    let bodyId = '';
    if (item && typeof item === 'object') {
      if (item.bodyId) bodyId = String(item.bodyId);
      else if (item.id) bodyId = splitEdgePick(item.id, singleBodyId).bodyId;
    } else {
      bodyId = splitEdgePick(item, singleBodyId).bodyId;
    }
    if (bodyId && ids.indexOf(bodyId) < 0) ids.push(bodyId);
  }
  return ids;
}

// Confirm is on only for a positive size and edges of one body.
export function confirmEdgeDecision(picks, sizeText, singleBodyId) {
  const size = parseEdgeSize(sizeText);
  const bodies = edgeBodyIds(picks, singleBodyId);
  if (bodies.length > 1) {
    return {
      enabled: false,
      message: CROSS_BODY_MESSAGE,
      bodyId: '',
      sizeOk: size.ok,
      size: size.size,
    };
  }
  const bodyId = bodies.length === 1 ? bodies[0] : '';
  const hasEdge = Array.isArray(picks) && picks.length > 0 && bodyId !== '';
  if (!hasEdge || !size.ok) {
    return {
      enabled: false,
      message: '',
      bodyId: bodyId,
      sizeOk: size.ok,
      size: size.size,
    };
  }
  return {
    enabled: true,
    message: '',
    bodyId: bodyId,
    sizeOk: true,
    size: size.size,
  };
}

// A second fillet on an edge that already carries one is allowed.
// If OCCT rejects it, the page uses SMALLER_SIZE_MESSAGE and keeps the shape.
export function repeatEdgeOpAllowed() {
  return true;
}

// True when the failure is the modeller rejecting the size, including a
// re-fillet that does not fit. Missing picks and a blank size are not.
export function occtSizeFailure(message) {
  const text = String(message || '');
  if (!text) return false;
  if (text === CROSS_BODY_MESSAGE) return false;
  if (text.indexOf('no picked') >= 0) return false;
  if (text.indexOf('not found') >= 0) return false;
  if (text.indexOf('no edge') >= 0) return false;
  if (text.indexOf('no solid') >= 0) return false;
  if (text.indexOf('not loaded') >= 0) return false;
  if (text.indexOf('choose Fillet') >= 0) return false;
  if (text.indexOf('positive number') >= 0) return false;
  if (text.indexOf('pick an edge') >= 0) return false;
  if (text.indexOf('mesh was rejected') >= 0) return false;
  return true;
}

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
