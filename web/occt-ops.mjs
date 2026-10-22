// Fuse, cut, common, fillet, and chamfer through libcascade 3.1.0.
// Signatures checked in builds/libcascade/pkg/package/dist/types.d.ts, then
// called from Node (2026-10-21):
//   BRepAlgoAPI_Fuse / Cut / Common constructor(S1, S2)
//   BRepAlgoAPI_BuilderAlgo.SimplifyResult(unifyEdges?, unifyFaces?, angularTol?)
//   BRepAlgoAPI_Algo.IsDone(), HasErrors(), Shape()
//   BRepFilletAPI_MakeFillet constructor(S) and Add(radius, edge), Build()
//   BRepFilletAPI_MakeChamfer constructor(S) and Add(distance, edge), Build()
//   BRepBuilderAPI_Copy constructor(S, copyGeom?, copyMesh?)
// Shape() throws StdFail_NotDone when IsDone() is false. This module never
// calls Shape() unless IsDone() is true and HasErrors() is not true.
// delete() in 3.1.0 frees the wrapper. Inputs and the kept shape are not
// deleted while an algorithm still holds them. The copy (copyGeom true) is
// what later steps keep.

import { checkOcctShape } from './occt-gate.mjs';
import { inspectSolid } from './occt-primitives.mjs';

// App defaults. Team choice (Erik 7:00 PM MT), not a sourced spec.
// Overlap equals the 4 mm thickness so the upright is the same stock, the
// two boxes share the corner block, and the inner edge is one line at
// x = corner + overlap, z = corner + thickness. The corner is the origin,
// so the fused solid spans 40 x 20 x 40 mm. The 2 mm fillet stays inside
// that box (radius is below the 4 mm stock). The 0.5 mm chamfer is only
// the two outer edges that run along the width: the base tip's top edge
// and the upright's outer top edge. Those cuts do not move the silhouette
// corners, so the bounding box stays 40 x 20 x 40 mm. Live preview is off:
// the fillet is applied once, when the build runs.
export const LBRACKET_LEG_LENGTH_MM = 40;
export const LBRACKET_LEG_WIDTH_MM = 20;
export const LBRACKET_THICKNESS_MM = 4;
export const LBRACKET_UPRIGHT_HEIGHT_MM = 40;
export const LBRACKET_CORNER_X_MM = 0;
export const LBRACKET_CORNER_Y_MM = 0;
export const LBRACKET_CORNER_Z_MM = 0;
export const LBRACKET_OVERLAP_MM = 4;
export const LBRACKET_INNER_FILLET_RADIUS_MM = 2;
export const LBRACKET_CHAMFER_DISTANCE_MM = 0.5;
export const LBRACKET_INNER_EDGE_MODE = 'auto';
export const LBRACKET_CHAMFER_EDGE_RULE = 'outer-leg-end-edges-along-width';
export const LBRACKET_FILLET_LIVE_PREVIEW = false;

export const LBRACKET_DEFAULTS = Object.freeze({
  legLengthMm: LBRACKET_LEG_LENGTH_MM,
  legWidthMm: LBRACKET_LEG_WIDTH_MM,
  thicknessMm: LBRACKET_THICKNESS_MM,
  uprightHeightMm: LBRACKET_UPRIGHT_HEIGHT_MM,
  cornerXMm: LBRACKET_CORNER_X_MM,
  cornerYMm: LBRACKET_CORNER_Y_MM,
  cornerZMm: LBRACKET_CORNER_Z_MM,
  overlapMm: LBRACKET_OVERLAP_MM,
  filletRadiusMm: LBRACKET_INNER_FILLET_RADIUS_MM,
  chamferDistanceMm: LBRACKET_CHAMFER_DISTANCE_MM,
  innerEdgeMode: LBRACKET_INNER_EDGE_MODE,
  chamferEdgeRule: LBRACKET_CHAMFER_EDGE_RULE,
  filletLivePreview: LBRACKET_FILLET_LIVE_PREVIEW,
});

const EDGE_TOL_MM = 1e-4;
const STL_HEADER = 'cadcam-mvp binary stl, coordinates in millimeters';

function track(trash, obj) {
  if (obj && typeof obj.delete === 'function') trash.push(obj);
  return obj;
}

function dispose(trash) {
  for (let i = trash.length - 1; i >= 0; i -= 1) {
    try {
      trash[i].delete();
    } catch (_err) {
      // already released
    }
  }
  trash.length = 0;
}

function explain(oc, err) {
  try {
    if (oc && typeof oc.getExceptionMessage === 'function' && err) {
      const pair = oc.getExceptionMessage(err);
      if (Array.isArray(pair) && (pair[0] || pair[1])) {
        return pair.filter(function (part) { return part; }).join(': ');
      }
    }
  } catch (_err) {
    // not a wasm exception
  }
  if (err && err.message) return err.message;
  return String(err);
}

function num(value, fallback) {
  const n = Number(value);
  return Number.isFinite(n) ? n : fallback;
}

export function lbracketSpec(overrides) {
  const src = overrides || {};
  return {
    legLengthMm: num(src.legLengthMm, LBRACKET_LEG_LENGTH_MM),
    legWidthMm: num(src.legWidthMm, LBRACKET_LEG_WIDTH_MM),
    thicknessMm: num(src.thicknessMm, LBRACKET_THICKNESS_MM),
    uprightHeightMm: num(src.uprightHeightMm, LBRACKET_UPRIGHT_HEIGHT_MM),
    cornerXMm: num(src.cornerXMm, LBRACKET_CORNER_X_MM),
    cornerYMm: num(src.cornerYMm, LBRACKET_CORNER_Y_MM),
    cornerZMm: num(src.cornerZMm, LBRACKET_CORNER_Z_MM),
    overlapMm: num(src.overlapMm, LBRACKET_OVERLAP_MM),
    filletRadiusMm: num(src.filletRadiusMm, LBRACKET_INNER_FILLET_RADIUS_MM),
    chamferDistanceMm: num(src.chamferDistanceMm, LBRACKET_CHAMFER_DISTANCE_MM),
    innerEdgeMode: src.innerEdgeMode ? String(src.innerEdgeMode) : LBRACKET_INNER_EDGE_MODE,
    chamferEdgeRule: src.chamferEdgeRule ? String(src.chamferEdgeRule) : LBRACKET_CHAMFER_EDGE_RULE,
    filletLivePreview: src.filletLivePreview === undefined
      ? LBRACKET_FILLET_LIVE_PREVIEW
      : src.filletLivePreview === true,
    stopAfter: src.stopAfter ? String(src.stopAfter) : 'chamfer',
  };
}

export function expectedLBracketBounds(spec) {
  const box = spec || lbracketSpec(null);
  return {
    xmin: box.cornerXMm,
    ymin: box.cornerYMm,
    zmin: box.cornerZMm,
    xmax: box.cornerXMm + box.legLengthMm,
    ymax: box.cornerYMm + box.legWidthMm,
    zmax: box.cornerZMm + box.uprightHeightMm,
  };
}

export function unitsLockGate() {
  return {
    pass: true,
    unit: 'mm',
    message: 'PASS: export unit is millimeter.',
  };
}

function takeDoneShape(oc, algo, label) {
  let done = false;
  try {
    done = algo.IsDone() === true;
  } catch (err) {
    return {
      ok: false,
      shape: null,
      error: 'FAIL: ' + label + ' IsDone threw ' + explain(oc, err) + '; Shape() was not called.',
    };
  }
  if (!done) {
    return {
      ok: false,
      shape: null,
      error: 'FAIL: ' + label + ' IsDone is false; Shape() was not called.',
    };
  }
  if (typeof algo.HasErrors === 'function') {
    let errors = false;
    try {
      errors = algo.HasErrors() === true;
    } catch (err) {
      return {
        ok: false,
        shape: null,
        error: 'FAIL: ' + label + ' HasErrors threw ' + explain(oc, err) + '; Shape() was not called.',
      };
    }
    if (errors) {
      return {
        ok: false,
        shape: null,
        error: 'FAIL: ' + label + ' HasErrors is true; Shape() was not called.',
      };
    }
  }
  try {
    return { ok: true, shape: algo.Shape(), error: '' };
  } catch (err) {
    return {
      ok: false,
      shape: null,
      error: 'FAIL: ' + label + ' Shape() threw ' + explain(oc, err),
    };
  }
}

function copyOwned(oc, source, trash) {
  const copier = track(trash, new oc.BRepBuilderAPI_Copy(source, true, false));
  try {
    copier.Build();
  } catch (err) {
    return {
      ok: false,
      shape: null,
      error: 'FAIL: BRepBuilderAPI_Copy Build threw ' + explain(oc, err) + '; Shape() was not called.',
    };
  }
  return takeDoneShape(oc, copier, 'BRepBuilderAPI_Copy');
}

// A shape the caller owns. The copier is disposed here. The copy is not.
export function copyShape(oc, source) {
  if (!source) return null;
  const trash = [];
  try {
    const copied = copyOwned(oc, source, trash);
    if (!copied.ok || !copied.shape) return null;
    return copied.shape;
  } finally {
    dispose(trash);
  }
}

function shapeList(oc, trash, shape) {
  const Ctor = oc.TopTools_ListOfShape || oc.NCollection_List_TopoDS_Shape;
  if (!Ctor) return null;
  const list = track(trash, new Ctor());
  let appended = null;
  try {
    appended = list.Append(shape);
  } catch (_err) {
    return null;
  }
  if (appended && appended !== shape && appended !== list && typeof appended.delete === 'function') track(trash, appended);
  return list;
}

// options.glueShift is the flush disc fuse only. Cuts never set it.
function booleanOp(oc, kind, shapeA, shapeB, options) {
  if (!shapeA || !shapeB) {
    return { ok: false, shape: null, error: 'FAIL: ' + kind + ' needs two shapes.' };
  }
  const glueShift = !!(options && options.glueShift);
  if (glueShift && kind !== 'fuse') {
    return { ok: false, shape: null, error: 'FAIL: SetGlue is only allowed on a flush fuse.' };
  }
  const Ctor = kind === 'cut'
    ? oc.BRepAlgoAPI_Cut
    : kind === 'common'
      ? oc.BRepAlgoAPI_Common
      : oc.BRepAlgoAPI_Fuse;
  const label = kind === 'cut' ? 'BRepAlgoAPI_Cut' : kind === 'common' ? 'BRepAlgoAPI_Common' : 'BRepAlgoAPI_Fuse';
  const trash = [];
  let owned = null;
  try {
    let algo;
    if (glueShift) {
      algo = track(trash, new Ctor());
      const args = shapeList(oc, trash, shapeA);
      const tools = shapeList(oc, trash, shapeB);
      if (!args || !tools) {
        return { ok: false, shape: null, error: 'FAIL: flush fuse could not build the shape lists.' };
      }
      algo.SetArguments(args);
      algo.SetTools(tools);
      if (typeof algo.SetNonDestructive === 'function') algo.SetNonDestructive(true);
      const glue = oc.BOPAlgo_GlueEnum && oc.BOPAlgo_GlueEnum.BOPAlgo_GlueShift;
      if (!glue) {
        return { ok: false, shape: null, error: 'FAIL: BOPAlgo_GlueShift is missing from this libcascade build.' };
      }
      algo.SetGlue(glue);
      try {
        algo.Build();
      } catch (err) {
        return {
          ok: false,
          shape: null,
          error: 'FAIL: flush fuse Build threw ' + explain(oc, err) + '; Shape() was not called.',
        };
      }
    } else {
      algo = track(trash, new Ctor(shapeA, shapeB));
    }
    if (kind === 'fuse') {
      let done = false;
      try {
        done = algo.IsDone() === true;
      } catch (err) {
        return {
          ok: false,
          shape: null,
          error: 'FAIL: fuse IsDone threw ' + explain(oc, err) + '; Shape() was not called.',
        };
      }
      if (done) {
        try {
          algo.SimplifyResult(true, true);
        } catch (err) {
          return {
            ok: false,
            shape: null,
            error: 'FAIL: fuse SimplifyResult threw ' + explain(oc, err) + '; Shape() was not called.',
          };
        }
      }
    }
    const taken = takeDoneShape(oc, algo, label);
    if (!taken.ok) return taken;
    track(trash, taken.shape);
    const copied = copyOwned(oc, taken.shape, trash);
    if (!copied.ok) return copied;
    owned = copied.shape;
    return { ok: true, shape: owned, error: '' };
  } catch (err) {
    if (owned) {
      try { owned.delete(); } catch (_drop) { /* already released */ }
    }
    return { ok: false, shape: null, error: 'FAIL: ' + label + ' threw ' + explain(oc, err) };
  } finally {
    dispose(trash);
  }
}

export function fuseShapes(oc, shapeA, shapeB) {
  return booleanOp(oc, 'fuse', shapeA, shapeB, null);
}

// Flush contact only. The disc on the leg uses this. Hole cuts do not.
export function fuseFlushShapes(oc, shapeA, shapeB) {
  return booleanOp(oc, 'fuse', shapeA, shapeB, { glueShift: true });
}

export function cutShapes(oc, shapeA, shapeB) {
  return booleanOp(oc, 'cut', shapeA, shapeB);
}

export function commonShapes(oc, shapeA, shapeB) {
  return booleanOp(oc, 'common', shapeA, shapeB);
}

function filletFaultText(fillet) {
  try {
    if (!fillet || typeof fillet.NbFaultyContours !== 'function') return '';
    const count = fillet.NbFaultyContours();
    if (!count) return '';
    const index = fillet.FaultyContour(1);
    const status = fillet.StripeStatus(index);
    return ' FaultyContours ' + count + ' StripeStatus ' + status + '.';
  } catch (_err) {
    return '';
  }
}

export function filletEdges(oc, shape, radius, edges) {
  if (!(Number(radius) > 0)) {
    return { ok: false, shape: null, error: 'FAIL: fillet radius must be a positive number of millimetres.' };
  }
  if (!shape || !edges || !edges.length) {
    return { ok: false, shape: null, error: 'FAIL: fillet has no edge.' };
  }
  const trash = [];
  let owned = null;
  try {
    const fillet = track(trash, new oc.BRepFilletAPI_MakeFillet(shape));
    for (let i = 0; i < edges.length; i += 1) fillet.Add(Number(radius), edges[i]);
    try {
      fillet.Build();
    } catch (err) {
      return {
        ok: false,
        shape: null,
        error: 'FAIL: fillet Build threw ' + explain(oc, err) + '; Shape() was not called.',
      };
    }
    const taken = takeDoneShape(oc, fillet, 'fillet');
    if (!taken.ok) {
      taken.error += filletFaultText(fillet);
      return taken;
    }
    track(trash, taken.shape);
    const copied = copyOwned(oc, taken.shape, trash);
    if (!copied.ok) return copied;
    owned = copied.shape;
    return { ok: true, shape: owned, error: '' };
  } catch (err) {
    if (owned) {
      try { owned.delete(); } catch (_drop) { /* already released */ }
    }
    return { ok: false, shape: null, error: 'FAIL: fillet threw ' + explain(oc, err) };
  } finally {
    dispose(trash);
  }
}

export function chamferEdges(oc, shape, distance, edges) {
  if (!(Number(distance) > 0)) {
    return { ok: false, shape: null, error: 'FAIL: chamfer distance must be a positive number of millimetres.' };
  }
  if (!shape || !edges || !edges.length) {
    return { ok: false, shape: null, error: 'FAIL: chamfer has no edge.' };
  }
  const trash = [];
  let owned = null;
  try {
    const chamfer = track(trash, new oc.BRepFilletAPI_MakeChamfer(shape));
    for (let i = 0; i < edges.length; i += 1) chamfer.Add(Number(distance), edges[i]);
    try {
      chamfer.Build();
    } catch (err) {
      return {
        ok: false,
        shape: null,
        error: 'FAIL: chamfer Build threw ' + explain(oc, err) + '; Shape() was not called.',
      };
    }
    const taken = takeDoneShape(oc, chamfer, 'chamfer');
    if (!taken.ok) return taken;
    track(trash, taken.shape);
    const copied = copyOwned(oc, taken.shape, trash);
    if (!copied.ok) return copied;
    owned = copied.shape;
    return { ok: true, shape: owned, error: '' };
  } catch (err) {
    if (owned) {
      try { owned.delete(); } catch (_drop) { /* already released */ }
    }
    return { ok: false, shape: null, error: 'FAIL: chamfer threw ' + explain(oc, err) };
  } finally {
    dispose(trash);
  }
}

function releaseShape(shape) {
  if (!shape || typeof shape.delete !== 'function') return;
  try { shape.delete(); } catch (_err) { /* already released */ }
}

// CAD Euler XYZ: rotate about X, then Y, then Z, around origin, then translate.
// Team choice, 2026-10-21. Angles are degrees in the UI and radians in OCCT.
export const TRANSFORM_EULER = 'XYZ';

export function transformShape(oc, shape, spec) {
  const src = spec || {};
  const dx = num(src.dx, 0);
  const dy = num(src.dy, 0);
  const dz = num(src.dz, 0);
  const rxDeg = num(src.rxDeg, 0);
  const ryDeg = num(src.ryDeg, 0);
  const rzDeg = num(src.rzDeg, 0);
  const origin = Array.isArray(src.origin) ? src.origin : [0, 0, 0];
  if (!shape) {
    return {
      ok: false,
      shape: null,
      error: 'FAIL: transform needs a shape. The last good shape was kept.',
      kept: true,
    };
  }
  if (!dx && !dy && !dz && !rxDeg && !ryDeg && !rzDeg) {
    return { ok: true, shape: null, skipped: true, error: '', kept: true };
  }
  const trash = [];
  let owned = null;
  try {
    const originPnt = track(trash, new oc.gp_Pnt(origin[0], origin[1], origin[2]));
    const trsf = track(trash, new oc.gp_Trsf());
    // Multiply in Z, Y, X so the composed matrix is Rz*Ry*Rx (X first).
    const rotations = [
      [[0, 0, 1], rzDeg],
      [[0, 1, 0], ryDeg],
      [[1, 0, 0], rxDeg],
    ];
    for (let i = 0; i < rotations.length; i += 1) {
      const deg = rotations[i][1];
      if (!deg) continue;
      const dirv = rotations[i][0];
      const dir = track(trash, new oc.gp_Dir(dirv[0], dirv[1], dirv[2]));
      const ax = track(trash, new oc.gp_Ax1(originPnt, dir));
      const part = track(trash, new oc.gp_Trsf());
      part.SetRotation(ax, deg * Math.PI / 180);
      trsf.Multiply(part);
    }
    if (dx || dy || dz) {
      const vec = track(trash, new oc.gp_Vec(dx, dy, dz));
      const move = track(trash, new oc.gp_Trsf());
      move.SetTranslation(vec);
      trsf.PreMultiply(move);
    }
    const xf = track(trash, new oc.BRepBuilderAPI_Transform(shape, trsf, true, false));
    const taken = takeDoneShape(oc, xf, 'BRepBuilderAPI_Transform');
    if (!taken.ok) {
      taken.kept = true;
      taken.error = taken.error || 'FAIL: transform IsDone is false; Shape() was not called.';
      if (taken.error.indexOf('kept') < 0) taken.error += ' The last good shape was kept.';
      return taken;
    }
    track(trash, taken.shape);
    const copied = copyOwned(oc, taken.shape, trash);
    if (!copied.ok) {
      copied.kept = true;
      if (copied.error && copied.error.indexOf('kept') < 0) copied.error += ' The last good shape was kept.';
      return copied;
    }
    owned = copied.shape;
    return { ok: true, shape: owned, error: '', kept: false };
  } catch (err) {
    if (owned) {
      try { owned.delete(); } catch (_drop) { /* already released */ }
    }
    return {
      ok: false,
      shape: null,
      error: 'FAIL: BRepBuilderAPI_Transform threw ' + explain(oc, err) + ' The last good shape was kept.',
      kept: true,
    };
  } finally {
    dispose(trash);
  }
}

// Exact geometry box. useTriangulation false, useShapeTolerance false so the
// box is not padded by the shape tolerance (BRepBndLib.Add does pad).
// libcascade 3.1.0: AddOptimal(shape, box, useTriangulation, useShapeTolerance).
export function optimalBounds(oc, shape) {
  if (!oc || !shape) return null;
  const trash = [];
  try {
    const box = track(trash, new oc.Bnd_Box());
    oc.BRepBndLib.AddOptimal(shape, box, false, false);
    if (typeof box.IsVoid === 'function' && box.IsVoid()) return null;
    const bounds = {
      xmin: box.GetXMin(),
      ymin: box.GetYMin(),
      zmin: box.GetZMin(),
      xmax: box.GetXMax(),
      ymax: box.GetYMax(),
      zmax: box.GetZMax(),
    };
    const values = [bounds.xmin, bounds.ymin, bounds.zmin, bounds.xmax, bounds.ymax, bounds.zmax];
    if (!values.every(function (n) { return Number.isFinite(n); })) return null;
    return bounds;
  } catch (_err) {
    return null;
  } finally {
    dispose(trash);
  }
}

function mulMat(a, b) {
  const out = [[0, 0, 0], [0, 0, 0], [0, 0, 0]];
  for (let r = 0; r < 3; r += 1) {
    for (let c = 0; c < 3; c += 1) {
      out[r][c] = a[r][0] * b[0][c] + a[r][1] * b[1][c] + a[r][2] * b[2][c];
    }
  }
  return out;
}

function transposeMat(m) {
  return [
    [m[0][0], m[1][0], m[2][0]],
    [m[0][1], m[1][1], m[2][1]],
    [m[0][2], m[1][2], m[2][2]],
  ];
}

function matVec(m, v) {
  return [
    m[0][0] * v[0] + m[0][1] * v[1] + m[0][2] * v[2],
    m[1][0] * v[0] + m[1][1] * v[1] + m[1][2] * v[2],
    m[2][0] * v[0] + m[2][1] * v[1] + m[2][2] * v[2],
  ];
}

// Same XYZ order as transformShape: R = Rz * Ry * Rx, degrees.
function eulerMatrixDeg(rxDeg, ryDeg, rzDeg) {
  const rx = (Number(rxDeg) || 0) * Math.PI / 180;
  const ry = (Number(ryDeg) || 0) * Math.PI / 180;
  const rz = (Number(rzDeg) || 0) * Math.PI / 180;
  const cx = Math.cos(rx);
  const sx = Math.sin(rx);
  const cy = Math.cos(ry);
  const sy = Math.sin(ry);
  const cz = Math.cos(rz);
  const sz = Math.sin(rz);
  const rotX = [[1, 0, 0], [0, cx, -sx], [0, sx, cx]];
  const rotY = [[cy, 0, sy], [0, 1, 0], [-sy, 0, cy]];
  const rotZ = [[cz, -sz, 0], [sz, cz, 0], [0, 0, 1]];
  return mulMat(rotZ, mulMat(rotY, rotX));
}

function resizeFail(method, error) {
  const text = error && error.indexOf('kept') >= 0 ? error : (error + ' The last good shape was kept.');
  return {
    ok: false,
    shape: null,
    kept: true,
    rolledBack: true,
    method: method,
    error: text,
    valid: false,
  };
}

// Locked uniform scale uses gp_Trsf.SetScale and BRepBuilderAPI_Transform.
// Unlocked resize uses gp_GTrsf and BRepBuilderAPI_GTransform about origin,
// in the body's local axes (euler is the same XYZ rotation as transformShape).
// factors are multiplicative. The input shape is not modified. A failed
// analyzer or a throw drops the new shape and reports rollback.
export function resizeShape(oc, shape, spec) {
  const src = spec || {};
  const factors = Array.isArray(src.factors) ? src.factors : [1, 1, 1];
  const fx = Number(factors[0]);
  const fy = Number(factors[1]);
  const fz = Number(factors[2]);
  const origin = Array.isArray(src.origin) ? src.origin : [0, 0, 0];
  const euler = Array.isArray(src.euler) ? src.euler : [0, 0, 0];
  const uniform = src.uniform === true;
  const method = uniform ? 'scale' : 'gtransform';
  if (!shape) return resizeFail(method, 'FAIL: resize needs a shape.');
  if (!(fx > 0) || !(fy > 0) || !(fz > 0) || !Number.isFinite(fx) || !Number.isFinite(fy) || !Number.isFinite(fz)) {
    return resizeFail(method, 'FAIL: size must be greater than zero.');
  }
  if (Math.abs(fx - 1) <= 1e-12 && Math.abs(fy - 1) <= 1e-12 && Math.abs(fz - 1) <= 1e-12) {
    return { ok: true, shape: null, skipped: true, kept: true, rolledBack: false, method: method, error: '', valid: true };
  }
  const trash = [];
  let owned = null;
  try {
    let algo = null;
    let label = '';
    if (uniform) {
      const pnt = track(trash, new oc.gp_Pnt(Number(origin[0]) || 0, Number(origin[1]) || 0, Number(origin[2]) || 0));
      const trsf = track(trash, new oc.gp_Trsf());
      trsf.SetScale(pnt, fx);
      algo = track(trash, new oc.BRepBuilderAPI_Transform(shape, trsf, true, false));
      label = 'BRepBuilderAPI_Transform';
    } else {
      const world = eulerMatrixDeg(euler[0], euler[1], euler[2]);
      const local = [[fx, 0, 0], [0, fy, 0], [0, 0, fz]];
      const linear = mulMat(world, mulMat(local, transposeMat(world)));
      const centre = [Number(origin[0]) || 0, Number(origin[1]) || 0, Number(origin[2]) || 0];
      const moved = matVec(linear, centre);
      const shift = [centre[0] - moved[0], centre[1] - moved[1], centre[2] - moved[2]];
      const gtrsf = track(trash, new oc.gp_GTrsf());
      for (let r = 0; r < 3; r += 1) {
        for (let c = 0; c < 3; c += 1) gtrsf.SetValue(r + 1, c + 1, linear[r][c]);
        gtrsf.SetValue(r + 1, 4, shift[r]);
      }
      algo = track(trash, new oc.BRepBuilderAPI_GTransform(shape, gtrsf, true));
      label = 'BRepBuilderAPI_GTransform';
    }
    const taken = takeDoneShape(oc, algo, label);
    if (!taken.ok || !taken.shape) {
      return resizeFail(method, taken.error || ('FAIL: ' + label + ' was rejected.'));
    }
    track(trash, taken.shape);
    const copied = copyOwned(oc, taken.shape, trash);
    if (!copied.ok || !copied.shape) {
      return resizeFail(method, copied.error || 'FAIL: resize copy failed.');
    }
    owned = copied.shape;
    let check = null;
    try {
      check = checkOcctShape(oc, owned);
    } catch (err) {
      releaseShape(owned);
      owned = null;
      return resizeFail(method, 'FAIL: BRepCheck_Analyzer threw ' + explain(oc, err));
    }
    if (src.forceInvalid === true || !check || check.valid !== true || check.pass !== true) {
      releaseShape(owned);
      owned = null;
      const why = src.forceInvalid === true
        ? 'FAIL: OCCT BRepCheck_Analyzer is not valid.'
        : ((check && check.message) || 'FAIL: OCCT BRepCheck_Analyzer is not valid.');
      return resizeFail(method, why);
    }
    const keptShape = owned;
    owned = null;
    return {
      ok: true,
      shape: keptShape,
      kept: false,
      rolledBack: false,
      method: method,
      error: '',
      valid: true,
      check: check,
    };
  } catch (err) {
    releaseShape(owned);
    return resizeFail(method, 'FAIL: ' + (uniform ? 'BRepBuilderAPI_Transform' : 'BRepBuilderAPI_GTransform') + ' threw ' + explain(oc, err));
  } finally {
    dispose(trash);
  }
}

export function makeBoxSolid(oc, dx, dy, dz, origin) {
  if (!(dx > 0) || !(dy > 0) || !(dz > 0)) return null;
  const trash = [];
  let owned = null;
  try {
    const at = origin || [0, 0, 0];
    const corner = track(trash, new oc.gp_Pnt(at[0], at[1], at[2]));
    const maker = track(trash, new oc.BRepPrimAPI_MakeBox(corner, dx, dy, dz));
    try {
      maker.Build();
    } catch (err) {
      return null;
    }
    const taken = takeDoneShape(oc, maker, 'BRepPrimAPI_MakeBox');
    if (!taken.ok) return null;
    track(trash, taken.shape);
    const copied = copyOwned(oc, taken.shape, trash);
    if (!copied.ok) return null;
    owned = copied.shape;
    return owned;
  } catch (_err) {
    releaseShape(owned);
    return null;
  } finally {
    dispose(trash);
  }
}

function near(p, x, y, z) {
  return Math.abs(p[0] - x) <= EDGE_TOL_MM
    && Math.abs(p[1] - y) <= EDGE_TOL_MM
    && Math.abs(p[2] - z) <= EDGE_TOL_MM;
}

function segmentMatch(a, b, x1, y1, z1, x2, y2, z2) {
  return (near(a, x1, y1, z1) && near(b, x2, y2, z2))
    || (near(a, x2, y2, z2) && near(b, x1, y1, z1));
}

function edgeEnds(oc, edge, trash) {
  const first = track(trash, oc.TopExp.FirstVertex(edge, true));
  const last = track(trash, oc.TopExp.LastVertex(edge, true));
  if (!first || !last) return null;
  if (typeof first.IsNull === 'function' && first.IsNull()) return null;
  if (typeof last.IsNull === 'function' && last.IsNull()) return null;
  const p1 = track(trash, oc.BRep_Tool.Pnt(first));
  const p2 = track(trash, oc.BRep_Tool.Pnt(last));
  return {
    a: [p1.X(), p1.Y(), p1.Z()],
    b: [p2.X(), p2.Y(), p2.Z()],
  };
}

function collectEdges(oc, shape, trash) {
  const found = [];
  const seen = new Set();
  const explorer = track(trash, new oc.TopExp_Explorer(shape, oc.TopAbs_ShapeEnum.TopAbs_EDGE));
  while (explorer.More()) {
    const edge = track(trash, oc.TopoDS.Edge(explorer.Current()));
    const ends = edgeEnds(oc, edge, trash);
    if (ends) {
      const ka = ends.a.map(function (n) { return Math.round(n * 1e4); }).join(',');
      const kb = ends.b.map(function (n) { return Math.round(n * 1e4); }).join(',');
      const key = ka < kb ? ka + '|' + kb : kb + '|' + ka;
      if (!seen.has(key)) {
        seen.add(key);
        found.push({ edge: edge, a: ends.a, b: ends.b });
      }
    }
    explorer.Next();
  }
  return found;
}

function emptySolid() {
  return {
    units: 'mm',
    gate: { pass: false, valid: false, freeEdges: -1, message: 'FAIL: no shape.' },
    watertight: { pass: false, message: 'FAIL: mesh has no triangles.' },
    mesh: { vertices: [], triangles: [] },
    topology: { source: 'occt', vertices: [], edges: [], faces: [], triFace: [] },
  };
}

export function buildLBracket(oc, overrides) {
  const spec = lbracketSpec(overrides);
  const log = [];
  let lastError = '';
  let good = null;

  function push(step, fields) {
    const units = unitsLockGate();
    log.push(Object.assign({
      step: step,
      pass: false,
      occt: false,
      occtMessage: '',
      watertight: false,
      watertightMessage: '',
      units: units.unit,
      unitsPass: units.pass === true,
      unitsMessage: units.message,
      error: '',
    }, fields));
  }

  function failStep(step, error) {
    lastError = error;
    push(step, { error: error });
  }

  function remember(step, shape) {
    let inspected;
    try {
      inspected = inspectSolid(oc, shape);
    } catch (err) {
      releaseShape(shape);
      failStep(step, 'FAIL: ' + step + ' gate threw ' + explain(oc, err));
      return false;
    }
    const units = unitsLockGate();
    const occtPass = inspected.gate.pass === true;
    const tightPass = inspected.watertight.pass === true;
    const pass = occtPass && tightPass && units.pass === true;
    let error = '';
    if (!pass) {
      error = !occtPass ? inspected.gate.message : !tightPass ? inspected.watertight.message : units.message;
      lastError = error;
      push(step, {
        pass: false,
        occt: occtPass,
        occtMessage: inspected.gate.message,
        watertight: tightPass,
        watertightMessage: inspected.watertight.message,
        error: error,
      });
      releaseShape(shape);
      return false;
    }
    if (good && good.shape && good.shape !== shape) releaseShape(good.shape);
    good = { step: step, shape: shape, inspected: inspected };
    push(step, {
      pass: true,
      occt: true,
      occtMessage: inspected.gate.message,
      watertight: true,
      watertightMessage: inspected.watertight.message,
      error: '',
    });
    return true;
  }

  const boxTrash = [];
  try {
    const corner = [spec.cornerXMm, spec.cornerYMm, spec.cornerZMm];
    const base = makeBoxSolid(oc, spec.legLengthMm, spec.legWidthMm, spec.thicknessMm, corner);
    const upright = makeBoxSolid(oc, spec.overlapMm, spec.legWidthMm, spec.uprightHeightMm, corner);
    if (!base || !upright) {
      releaseShape(base);
      releaseShape(upright);
      failStep('fuse', 'FAIL: L-bracket box IsDone is false; Shape() was not called.');
    } else {
      const fused = fuseShapes(oc, base, upright);
      releaseShape(base);
      releaseShape(upright);
      if (!fused.ok) {
        failStep('fuse', fused.error);
      } else if (remember('fuse', fused.shape) && spec.stopAfter !== 'fuse') {
        if (spec.filletLivePreview) {
          push('fillet-preview', {
            pass: true,
            error: '',
            occtMessage: 'Live preview is out of scope. The fillet is applied once.',
          });
        }
        if (spec.innerEdgeMode !== 'auto') {
          failStep('fillet', 'FAIL: inner edge mode "' + spec.innerEdgeMode
            + '" is not implemented. App default is ' + LBRACKET_INNER_EDGE_MODE + '.');
        } else if (!(spec.filletRadiusMm > 0)) {
          failStep('fillet', 'FAIL: fillet radius must be a positive number of millimetres.');
        } else {
          const edgeTrash = [];
          let filleted = null;
          try {
            const edges = collectEdges(oc, good.shape, edgeTrash);
            const x = spec.cornerXMm + spec.overlapMm;
            const z = spec.cornerZMm + spec.thicknessMm;
            const y0 = spec.cornerYMm;
            const y1 = spec.cornerYMm + spec.legWidthMm;
            const inner = edges.find(function (edge) {
              return segmentMatch(edge.a, edge.b, x, y0, z, x, y1, z);
            });
            if (!inner) {
              failStep('fillet', 'FAIL: auto-detect found no inner edge at the concave corner.');
            } else {
              filleted = filletEdges(oc, good.shape, spec.filletRadiusMm, [inner.edge]);
            }
          } finally {
            dispose(edgeTrash);
          }
          if (filleted && !filleted.ok) {
            failStep('fillet', filleted.error);
          } else if (filleted && filleted.ok && remember('fillet', filleted.shape) && spec.stopAfter !== 'fillet') {
            if (spec.chamferEdgeRule !== LBRACKET_CHAMFER_EDGE_RULE) {
              failStep('chamfer', 'FAIL: chamfer edge rule "' + spec.chamferEdgeRule
                + '" is not implemented. App default is ' + LBRACKET_CHAMFER_EDGE_RULE + '.');
            } else if (!(spec.chamferDistanceMm > 0)) {
              failStep('chamfer', 'FAIL: chamfer distance must be a positive number of millimetres.');
            } else {
              const edgeTrash = [];
              let chamfered = null;
              try {
                const edges = collectEdges(oc, good.shape, edgeTrash);
                const y0 = spec.cornerYMm;
                const y1 = spec.cornerYMm + spec.legWidthMm;
                const baseTip = edges.find(function (edge) {
                  const xTip = spec.cornerXMm + spec.legLengthMm;
                  const zTip = spec.cornerZMm + spec.thicknessMm;
                  return segmentMatch(edge.a, edge.b, xTip, y0, zTip, xTip, y1, zTip);
                });
                const uprightTop = edges.find(function (edge) {
                  const zTop = spec.cornerZMm + spec.uprightHeightMm;
                  return segmentMatch(edge.a, edge.b, spec.cornerXMm, y0, zTop, spec.cornerXMm, y1, zTop);
                });
                if (!baseTip || !uprightTop) {
                  failStep('chamfer', 'FAIL: chamfer edge rule found '
                    + (baseTip ? 1 : 0) + ' of the base tip and '
                    + (uprightTop ? 1 : 0) + ' of the upright top.');
                } else {
                  chamfered = chamferEdges(oc, good.shape, spec.chamferDistanceMm, [baseTip.edge, uprightTop.edge]);
                }
              } finally {
                dispose(edgeTrash);
              }
              if (chamfered && !chamfered.ok) failStep('chamfer', chamfered.error);
              else if (chamfered && chamfered.ok) remember('chamfer', chamfered.shape);
            }
          }
        }
      }
    }
  } catch (err) {
    failStep(log.length ? log[log.length - 1].step : 'build', 'FAIL: L-bracket threw ' + explain(oc, err));
  } finally {
    dispose(boxTrash);
  }

  const inspected = good ? good.inspected : emptySolid();
  const lastGoodStep = good ? good.step : '';
  if (good && good.shape) releaseShape(good.shape);
  const finished = spec.stopAfter === 'fuse' || spec.stopAfter === 'fillet' || spec.stopAfter === 'chamfer'
    ? spec.stopAfter
    : 'chamfer';
  const finishedEntry = log.filter(function (item) { return item.step === finished; }).pop();
  return {
    pass: !!(finishedEntry && finishedEntry.pass === true) && lastError === '',
    units: 'mm',
    lastGoodStep: lastGoodStep,
    lastError: lastError,
    log: log,
    gate: inspected.gate,
    watertight: inspected.watertight,
    mesh: inspected.mesh,
    topology: inspected.topology,
    params: spec,
    bounds: expectedLBracketBounds(spec),
    meshTimeMs: inspected.meshTimeMs || 0,
    meshSettings: inspected.meshSettings || null,
    meshPath: inspected.meshPath || '',
  };
}

// Interactive Booleans. Team choice, 2026-10-21.
// Two 20 mm boxes. The first uses the box primitive centre (0, 0, 10).
// The second is shifted +10 mm on X, so the overlap is 10 x 20 x 20 mm.
// Cut is the first body minus the second. A 40 mm shift leaves a gap.
// The demo cuts a Z cylinder (diameter 10 mm, height 30 mm, same centre)
// through that box. Volume tolerance for the boxes is 1e-3 mmÂ³.
// The cylinder demo uses 1e-2 mmÂ³. An absolute volume at or below 1e-4 mmÂ³
// is empty. Bounding boxes from BRepBndLib.Add (exact geometry) use 1e-3 mm.
export const BOOLEAN_BOX_EDGE_MM = 20;
export const BOOLEAN_OVERLAP_SHIFT_MM = 10;
export const BOOLEAN_DISJOINT_SHIFT_MM = 40;
export const BOOLEAN_VOLUME_TOL_MM3 = 1e-3;
export const BOOLEAN_CURVE_VOLUME_TOL_MM3 = 1e-2;
export const BOOLEAN_BOUNDS_TOL_MM = 1e-3;
export const BOOLEAN_EMPTY_VOLUME_MM3 = 1e-4;
export const BOOLEAN_DEMO_CYLINDER_DIAMETER_MM = 10;
export const BOOLEAN_DEMO_CYLINDER_HEIGHT_MM = 30;
export const BOOLEAN_DEMO_OP = 'cut';

export function booleanBoxCentre(shiftX) {
  return {
    cx: num(shiftX, 0),
    cy: 0,
    cz: 10,
  };
}

export function booleanBoxOrigin(shiftX) {
  const centre = booleanBoxCentre(shiftX);
  const half = BOOLEAN_BOX_EDGE_MM / 2;
  return [centre.cx - half, centre.cy - half, centre.cz - half];
}

export function expectedOverlapVolumes() {
  const box = BOOLEAN_BOX_EDGE_MM * BOOLEAN_BOX_EDGE_MM * BOOLEAN_BOX_EDGE_MM;
  const overlap = BOOLEAN_OVERLAP_SHIFT_MM * BOOLEAN_BOX_EDGE_MM * BOOLEAN_BOX_EDGE_MM;
  return {
    union: box * 2 - overlap,
    cut: box - overlap,
    intersect: overlap,
  };
}

export function expectedOverlapBounds(op) {
  const half = BOOLEAN_BOX_EDGE_MM / 2;
  const shift = BOOLEAN_OVERLAP_SHIFT_MM;
  const y0 = -half;
  const y1 = half;
  const z0 = 0;
  const z1 = BOOLEAN_BOX_EDGE_MM;
  if (op === 'union') {
    return { xmin: -half, ymin: y0, zmin: z0, xmax: -half + BOOLEAN_BOX_EDGE_MM + shift, ymax: y1, zmax: z1 };
  }
  if (op === 'cut') {
    return { xmin: -half, ymin: y0, zmin: z0, xmax: -half + shift, ymax: y1, zmax: z1 };
  }
  return { xmin: -half + shift, ymin: y0, zmin: z0, xmax: half, ymax: y1, zmax: z1 };
}

export function expectedDemoVolumes() {
  const radius = BOOLEAN_DEMO_CYLINDER_DIAMETER_MM / 2;
  const cylinder = Math.PI * radius * radius * BOOLEAN_DEMO_CYLINDER_HEIGHT_MM;
  const inside = Math.PI * radius * radius * BOOLEAN_BOX_EDGE_MM;
  const box = BOOLEAN_BOX_EDGE_MM * BOOLEAN_BOX_EDGE_MM * BOOLEAN_BOX_EDGE_MM;
  return {
    union: box + cylinder - inside,
    cut: box - inside,
    intersect: inside,
  };
}

export function expectedDemoBounds(op) {
  const half = BOOLEAN_BOX_EDGE_MM / 2;
  const radius = BOOLEAN_DEMO_CYLINDER_DIAMETER_MM / 2;
  const zBox0 = 0;
  const zBox1 = BOOLEAN_BOX_EDGE_MM;
  const zCyl0 = 10 - BOOLEAN_DEMO_CYLINDER_HEIGHT_MM / 2;
  const zCyl1 = 10 + BOOLEAN_DEMO_CYLINDER_HEIGHT_MM / 2;
  if (op === 'union') {
    return { xmin: -half, ymin: -half, zmin: zCyl0, xmax: half, ymax: half, zmax: zCyl1 };
  }
  if (op === 'intersect') {
    return { xmin: -radius, ymin: -radius, zmin: zBox0, xmax: radius, ymax: radius, zmax: zBox1 };
  }
  return { xmin: -half, ymin: -half, zmin: zBox0, xmax: half, ymax: half, zmax: zBox1 };
}

export function normalizeBooleanOp(op) {
  const name = String(op || '').toLowerCase();
  if (name === 'union' || name === 'fuse') return { ui: 'union', kind: 'fuse' };
  if (name === 'cut') return { ui: 'cut', kind: 'cut' };
  if (name === 'intersect' || name === 'common') return { ui: 'intersect', kind: 'common' };
  return null;
}

export function makeCylinderSolid(oc, radius, height, base, direction) {
  if (!(radius > 0) || !(height > 0)) return null;
  const at = base || [0, 0, 0];
  const dir = direction || [0, 0, 1];
  const trash = [];
  let owned = null;
  try {
    const origin = track(trash, new oc.gp_Pnt(at[0], at[1], at[2]));
    const gpDir = track(trash, new oc.gp_Dir(dir[0], dir[1], dir[2]));
    const axes = track(trash, new oc.gp_Ax2(origin, gpDir));
    const maker = track(trash, new oc.BRepPrimAPI_MakeCylinder(axes, radius, height));
    try {
      maker.Build();
    } catch (_err) {
      return null;
    }
    const taken = takeDoneShape(oc, maker, 'BRepPrimAPI_MakeCylinder');
    if (!taken.ok) return null;
    track(trash, taken.shape);
    const copied = copyOwned(oc, taken.shape, trash);
    if (!copied.ok) return null;
    owned = copied.shape;
    return owned;
  } catch (_err) {
    releaseShape(owned);
    return null;
  } finally {
    dispose(trash);
  }
}

export function solidVolumeMm3(oc, shape) {
  const trash = [];
  try {
    const props = track(trash, new oc.GProp_GProps());
    oc.BRepGProp.VolumeProperties(shape, props, true, false, false);
    return props.Mass();
  } finally {
    dispose(trash);
  }
}

export function solidBounds(oc, shape) {
  const trash = [];
  try {
    const box = track(trash, new oc.Bnd_Box());
    oc.BRepBndLib.Add(shape, box, false);
    return {
      xmin: box.GetXMin(),
      ymin: box.GetYMin(),
      zmin: box.GetZMin(),
      xmax: box.GetXMax(),
      ymax: box.GetYMax(),
      zmax: box.GetZMax(),
    };
  } finally {
    dispose(trash);
  }
}

function countSolids(oc, shape) {
  const explorer = new oc.TopExp_Explorer(shape, oc.TopAbs_ShapeEnum.TopAbs_SOLID);
  let count = 0;
  try {
    while (explorer.More()) {
      count += 1;
      explorer.Next();
    }
  } finally {
    explorer.delete();
  }
  return count;
}

function emptyBoolean(error) {
  return {
    ok: false,
    op: '',
    shape: null,
    error: error,
    kept: true,
    inputsKept: true,
    units: 'mm',
    volumeMm3: 0,
    bounds: null,
    gate: { pass: false, valid: false, freeEdges: -1, message: error },
    watertight: { pass: false, message: 'FAIL: mesh has no triangles.' },
    mesh: { vertices: [], triangles: [] },
    topology: { source: 'occt', vertices: [], edges: [], faces: [], triFace: [] },
    meshTimeMs: 0,
  };
}

// One Boolean on exactly two shapes. Reuses fuseShapes, cutShapes, commonShapes.
// Shape() is not called unless IsDone() is true. A failed or empty result is
// deleted here. The caller keeps both inputs.
export function applyBooleanSolids(oc, op, shapeA, shapeB) {
  const which = normalizeBooleanOp(op);
  if (!which) return emptyBoolean('FAIL: Boolean op must be union, cut, or intersect. Both inputs were kept.');
  const made = which.kind === 'cut'
    ? cutShapes(oc, shapeA, shapeB)
    : which.kind === 'common'
      ? commonShapes(oc, shapeA, shapeB)
      : fuseShapes(oc, shapeA, shapeB);
  if (!made.ok || !made.shape) {
    return emptyBoolean((made.error || ('FAIL: ' + which.ui + ' failed.')) + ' Both inputs were kept.');
  }
  let view = null;
  try {
    view = inspectSolid(oc, made.shape);
  } catch (err) {
    releaseShape(made.shape);
    return emptyBoolean('FAIL: ' + which.ui + ' gate threw ' + explain(oc, err) + ' Both inputs were kept.');
  }
  let volume = 0;
  let solids = 0;
  try {
    volume = solidVolumeMm3(oc, made.shape);
    solids = countSolids(oc, made.shape);
  } catch (err) {
    releaseShape(made.shape);
    return emptyBoolean('FAIL: ' + which.ui + ' volume threw ' + explain(oc, err) + ' Both inputs were kept.');
  }
  const units = unitsLockGate();
  const triangles = view.mesh && view.mesh.triangles ? view.mesh.triangles.length : 0;
  const empty = !(volume > BOOLEAN_EMPTY_VOLUME_MM3) || solids < 1 || triangles < 1;
  const pass = !empty && view.gate.pass === true && view.watertight.pass === true && units.pass === true;
  if (!pass) {
    releaseShape(made.shape);
    let error = '';
    if (empty) error = 'FAIL: ' + which.ui + ' result is empty.';
    else if (view.gate.pass !== true) error = view.gate.message || ('FAIL: ' + which.ui + ' failed the OCCT gate.');
    else if (view.watertight.pass !== true) error = view.watertight.message || ('FAIL: ' + which.ui + ' mesh is not watertight.');
    else error = units.message || 'FAIL: units are not millimetres.';
    if (error.indexOf('kept') === -1) error += ' Both inputs were kept.';
    return {
      ok: false,
      op: which.ui,
      shape: null,
      error: error,
      kept: true,
      inputsKept: true,
      units: 'mm',
      volumeMm3: volume,
      bounds: null,
      gate: view.gate,
      watertight: view.watertight,
      mesh: view.mesh,
      topology: view.topology,
      meshTimeMs: view.meshTimeMs || 0,
    };
  }
  let bounds = null;
  try {
    bounds = solidBounds(oc, made.shape);
  } catch (err) {
    releaseShape(made.shape);
    return emptyBoolean('FAIL: ' + which.ui + ' bounds threw ' + explain(oc, err) + ' Both inputs were kept.');
  }
  return {
    ok: true,
    op: which.ui,
    shape: made.shape,
    error: '',
    kept: false,
    inputsKept: true,
    units: 'mm',
    volumeMm3: volume,
    bounds: bounds,
    gate: view.gate,
    watertight: view.watertight,
    mesh: view.mesh,
    topology: view.topology,
    meshTimeMs: view.meshTimeMs || 0,
    meshSettings: view.meshSettings || null,
    meshPath: view.meshPath || '',
  };
}

function releasePair(shapeA, shapeB) {
  releaseShape(shapeA);
  releaseShape(shapeB);
}

export function buildOverlapBoolean(oc, op, shiftX) {
  const which = normalizeBooleanOp(op);
  if (!which) return emptyBoolean('FAIL: Boolean op must be union, cut, or intersect.');
  const move = num(shiftX, BOOLEAN_OVERLAP_SHIFT_MM);
  const shapeA = makeBoxSolid(oc, BOOLEAN_BOX_EDGE_MM, BOOLEAN_BOX_EDGE_MM, BOOLEAN_BOX_EDGE_MM, booleanBoxOrigin(0));
  const shapeB = makeBoxSolid(oc, BOOLEAN_BOX_EDGE_MM, BOOLEAN_BOX_EDGE_MM, BOOLEAN_BOX_EDGE_MM, booleanBoxOrigin(move));
  if (!shapeA || !shapeB) {
    releasePair(shapeA, shapeB);
    return emptyBoolean('FAIL: Boolean boxes were not built.');
  }
  let beforeA = 0;
  let beforeB = 0;
  try {
    beforeA = solidVolumeMm3(oc, shapeA);
    beforeB = solidVolumeMm3(oc, shapeB);
  } catch (_err) {
    beforeA = 0;
    beforeB = 0;
  }
  const applied = applyBooleanSolids(oc, which.ui, shapeA, shapeB);
  if (!applied.ok) {
    let kept = false;
    try {
      const afterA = solidVolumeMm3(oc, shapeA);
      const afterB = solidVolumeMm3(oc, shapeB);
      const viewA = inspectSolid(oc, shapeA);
      const viewB = inspectSolid(oc, shapeB);
      kept = Math.abs(afterA - beforeA) <= BOOLEAN_VOLUME_TOL_MM3
        && Math.abs(afterB - beforeB) <= BOOLEAN_VOLUME_TOL_MM3
        && viewA.gate.pass === true && viewA.watertight.pass === true
        && viewB.gate.pass === true && viewB.watertight.pass === true;
    } catch (_err) {
      kept = false;
    }
    applied.inputsKept = kept;
    releasePair(shapeA, shapeB);
    return applied;
  }
  releasePair(shapeA, shapeB);
  applied.inputsKept = false;
  return applied;
}

export function buildBooleanDemo(oc, op) {
  const which = normalizeBooleanOp(op || BOOLEAN_DEMO_OP);
  if (!which) return emptyBoolean('FAIL: Boolean op must be union, cut, or intersect.');
  const box = makeBoxSolid(oc, BOOLEAN_BOX_EDGE_MM, BOOLEAN_BOX_EDGE_MM, BOOLEAN_BOX_EDGE_MM, booleanBoxOrigin(0));
  const baseZ = 10 - BOOLEAN_DEMO_CYLINDER_HEIGHT_MM / 2;
  const cylinder = makeCylinderSolid(
    oc,
    BOOLEAN_DEMO_CYLINDER_DIAMETER_MM / 2,
    BOOLEAN_DEMO_CYLINDER_HEIGHT_MM,
    [0, 0, baseZ],
    [0, 0, 1]
  );
  if (!box || !cylinder) {
    releasePair(box, cylinder);
    return emptyBoolean('FAIL: Boolean demo solids were not built.');
  }
  const applied = applyBooleanSolids(oc, which.ui, box, cylinder);
  releasePair(box, cylinder);
  return applied;
}

export function binaryStlBytes(mesh) {
  const triangles = mesh && mesh.triangles ? mesh.triangles : [];
  const vertices = mesh && mesh.vertices ? mesh.vertices : [];
  const bytes = new ArrayBuffer(84 + triangles.length * 50);
  const view = new DataView(bytes);
  for (let i = 0; i < 80; i += 1) {
    view.setUint8(i, i < STL_HEADER.length ? STL_HEADER.charCodeAt(i) : 0);
  }
  view.setUint32(80, triangles.length, true);
  let offset = 84;
  for (let t = 0; t < triangles.length; t += 1) {
    const tri = triangles[t];
    const a = vertices[tri[0]];
    const b = vertices[tri[1]];
    const c = vertices[tri[2]];
    const ux = b[0] - a[0];
    const uy = b[1] - a[1];
    const uz = b[2] - a[2];
    const vx = c[0] - a[0];
    const vy = c[1] - a[1];
    const vz = c[2] - a[2];
    let nx = uy * vz - uz * vy;
    let ny = uz * vx - ux * vz;
    let nz = ux * vy - uy * vx;
    const length = Math.hypot(nx, ny, nz) || 1;
    view.setFloat32(offset, nx / length, true);
    view.setFloat32(offset + 4, ny / length, true);
    view.setFloat32(offset + 8, nz / length, true);
    offset += 12;
    const corners = [a, b, c];
    for (let k = 0; k < 3; k += 1) {
      view.setFloat32(offset, corners[k][0], true);
      view.setFloat32(offset + 4, corners[k][1], true);
      view.setFloat32(offset + 8, corners[k][2], true);
      offset += 12;
    }
    view.setUint16(offset, 0, true);
    offset += 2;
  }
  return new Uint8Array(bytes);
}

export function meshBounds(mesh) {
  let xmin = Infinity;
  let ymin = Infinity;
  let zmin = Infinity;
  let xmax = -Infinity;
  let ymax = -Infinity;
  let zmax = -Infinity;
  const vertices = mesh && mesh.vertices ? mesh.vertices : [];
  for (let i = 0; i < vertices.length; i += 1) {
    const p = vertices[i];
    if (p[0] < xmin) xmin = p[0];
    if (p[1] < ymin) ymin = p[1];
    if (p[2] < zmin) zmin = p[2];
    if (p[0] > xmax) xmax = p[0];
    if (p[1] > ymax) ymax = p[1];
    if (p[2] > zmax) zmax = p[2];
  }
  return { xmin: xmin, ymin: ymin, zmin: zmin, xmax: xmax, ymax: ymax, zmax: zmax };
}

export function meshVolumeMm3(mesh) {
  const vertices = mesh && mesh.vertices ? mesh.vertices : [];
  const triangles = mesh && mesh.triangles ? mesh.triangles : [];
  let sum = 0;
  for (let i = 0; i < triangles.length; i += 1) {
    const tri = triangles[i];
    const a = vertices[tri[0]];
    const b = vertices[tri[1]];
    const c = vertices[tri[2]];
    if (!a || !b || !c) continue;
    sum += a[0] * (b[1] * c[2] - b[2] * c[1])
      + a[1] * (b[2] * c[0] - b[0] * c[2])
      + a[2] * (b[0] * c[1] - b[1] * c[0]);
  }
  return Math.abs(sum) / 6;
}


// Confirm sizes. Team choice, 2026-10-21. Same 2 mm and 0.5 mm as the L-bracket defaults.
export const EDGE_FILLET_RADIUS_MM = 2;
export const EDGE_CHAMFER_DISTANCE_MM = 0.5;

// Hole tool. Team choice, 2026-10-21. 4.5 mm and 9.5 mm are a #8 wood screw
// clearance and countersink, tagged unverified fit. 82 degrees is the #8
// flat-head angle. 90 degrees is the metric ISO countersink angle and stays editable.
export const HOLE_DIAMETER_MM = 4.5;
export const HOLE_COUNTERSINK_DIAMETER_MM = 9.5;
export const HOLE_COUNTERSINK_ANGLE_DEG = 82;
export const HOLE_BLIND_DEPTH_MM = 6;
export const HOLE_FIT = 'unverified fit';
// Plate for the portrait hole test. A flat box, not an Erik measurement.
export const PLATE_SX_MM = 80;
export const PLATE_SY_MM = 40;
export const PLATE_SZ_MM = 6;
// Three countersunk holes, millimetres from the face-edge corner. Team choice.
export const PLATE_HOLE_UV_MM = Object.freeze([
  Object.freeze([20, 20]),
  Object.freeze([40, 20]),
  Object.freeze([60, 20]),
]);
// Cutter overlap outside the face so the Boolean crosses it. The section on
// the face is still the countersink diameter, and the included angle is unchanged.
export const HOLE_CUTTER_PAD_MM = 0.05;

function addScaled(point, dir, scale) {
  return [
    point[0] + dir[0] * scale,
    point[1] + dir[1] * scale,
    point[2] + dir[2] * scale,
  ];
}

function makeConeSolid(oc, r1, r2, height, base, direction) {
  if (!(r1 >= 0) || !(r2 >= 0) || !(height > 0) || (r1 === 0 && r2 === 0)) return null;
  const at = base || [0, 0, 0];
  const dir = direction || [0, 0, 1];
  const trash = [];
  let owned = null;
  try {
    const origin = track(trash, new oc.gp_Pnt(at[0], at[1], at[2]));
    const gpDir = track(trash, new oc.gp_Dir(dir[0], dir[1], dir[2]));
    const axes = track(trash, new oc.gp_Ax2(origin, gpDir));
    const maker = track(trash, new oc.BRepPrimAPI_MakeCone(axes, r1, r2, height));
    try {
      maker.Build();
    } catch (_err) {
      return null;
    }
    const taken = takeDoneShape(oc, maker, 'BRepPrimAPI_MakeCone');
    if (!taken.ok) return null;
    track(trash, taken.shape);
    const copied = copyOwned(oc, taken.shape, trash);
    if (!copied.ok) return null;
    owned = copied.shape;
    return owned;
  } catch (_err) {
    releaseShape(owned);
    return null;
  } finally {
    dispose(trash);
  }
}


// Countersunk through-hole. The cone and the drill are fused once.
// face is the outer-face point. dir points into the solid.
// padMm extends the cutter past both faces. The caller cuts with cutShapes, which does not set glue.
export function makeCountersunkThroughHole(oc, options) {
  const src = options || {};
  const holeRadius = Number(src.holeDiameterMm) / 2;
  const countersinkRadius = Number(src.countersinkDiameterMm) / 2;
  const through = Number(src.throughMm);
  const pad = Number(src.padMm);
  const face = src.face;
  const dir = src.dir;
  const halfAngle = (Number(src.countersinkAngleDeg) / 2) * Math.PI / 180;
  if (!(holeRadius > 0) || !(countersinkRadius > holeRadius) || !(through > 0) || !(pad >= 0) || !(halfAngle > 0) || !face || !dir) {
    return null;
  }
  const depth = (countersinkRadius - holeRadius) / Math.tan(halfAngle);
  if (!(depth > 0)) return null;
  const cone = makeConeSolid(
    oc,
    holeRadius + (depth + pad) * Math.tan(halfAngle),
    holeRadius,
    depth + pad,
    addScaled(face, dir, -pad),
    dir
  );
  const cylinder = makeCylinderSolid(
    oc,
    holeRadius,
    through + pad * 2,
    addScaled(face, dir, -pad),
    dir
  );
  if (!cone || !cylinder) {
    releaseShape(cone);
    releaseShape(cylinder);
    return null;
  }
  const fused = fuseShapes(oc, cone, cylinder);
  releaseShape(cone);
  releaseShape(cylinder);
  if (!fused.ok || !fused.shape) {
    if (fused.shape) releaseShape(fused.shape);
    return null;
  }
  return fused.shape;
}

export function countersinkHeightMm(holeDiameterMm, countersinkDiameterMm, angleDeg) {
  const r1 = Number(countersinkDiameterMm) / 2;
  const r2 = Number(holeDiameterMm) / 2;
  const half = (Number(angleDeg) / 2) * Math.PI / 180;
  if (!(r1 > r2) || !(half > 0) || !(half < Math.PI / 2)) return 0;
  const height = (r1 - r2) / Math.tan(half);
  return height > 0 ? height : 0;
}

// Removed volume of one hole. The countersink is the cone frustum
// BRepPrimAPI_MakeCone(R1, R2, H) with H = (R1-R2)/tan(angle/2), plus the
// drill below that frustum. depthMm is the hole depth inside the solid.
export function holeRemovedVolumeMm3(spec) {
  const src = spec || {};
  const radius = Number(src.diameterMm) / 2;
  const depth = Number(src.depthMm);
  if (!(radius > 0) || !(depth > 0)) return 0;
  if (src.countersink !== true) return Math.PI * radius * radius * depth;
  const r1 = Number(src.countersinkDiameterMm) / 2;
  const height = countersinkHeightMm(src.diameterMm, src.countersinkDiameterMm, src.countersinkAngleDeg);
  if (!(r1 > radius) || !(height > 0)) return 0;
  const used = Math.min(height, depth);
  const rAt = r1 + (radius - r1) * (used / height);
  const frustum = (Math.PI * used / 3) * (r1 * r1 + r1 * rAt + rAt * rAt);
  const rest = Math.PI * radius * radius * Math.max(0, depth - used);
  return frustum + rest;
}

function unitDir(dir) {
  if (!dir) return null;
  const len = Math.hypot(Number(dir[0]), Number(dir[1]), Number(dir[2]));
  if (!(len > 1e-12)) return null;
  return [dir[0] / len, dir[1] / len, dir[2] / len];
}

function holeFail(error, volumeBefore) {
  const text = error && error.indexOf('kept') === -1 ? error + ' The solid was kept.' : (error || 'FAIL: hole failed. The solid was kept.');
  return {
    ok: false,
    shape: null,
    kept: true,
    error: text,
    volumeBefore: volumeBefore || 0,
    volumeAfter: volumeBefore || 0,
    depthMm: 0,
    countersinkHeightMm: 0,
    units: 'mm',
  };
}

function ownedCopy(oc, shape) {
  const trash = [];
  const copied = copyOwned(oc, shape, trash);
  const kept = copied.ok ? copied.shape : null;
  const rest = [];
  for (let i = 0; i < trash.length; i += 1) {
    if (trash[i] !== kept) rest.push(trash[i]);
  }
  dispose(rest);
  return kept;
}

// Distance along dir from the face point to the far intersection.
// The line starts 1 mm outside the face. Returns 0 when the solid is not pierced.
function measureThroughMm(oc, shape, face, dir) {
  const back = 1;
  const trash = [];
  try {
    const origin = track(trash, new oc.gp_Pnt(
      face[0] - dir[0] * back,
      face[1] - dir[1] * back,
      face[2] - dir[2] * back
    ));
    const gpDir = track(trash, new oc.gp_Dir(dir[0], dir[1], dir[2]));
    const line = track(trash, new oc.gp_Lin(origin, gpDir));
    const inter = track(trash, new oc.BRepIntCurveSurface_Inter());
    inter.Init(shape, line, 1e-6);
    let maxW = -Infinity;
    let guard = 0;
    while (inter.More() && guard < 64) {
      guard += 1;
      const w = Number(inter.W());
      if (Number.isFinite(w) && w > maxW) maxW = w;
      inter.Next();
    }
    if (!(maxW > back)) return 0;
    return maxW - back;
  } catch (_err) {
    return 0;
  } finally {
    dispose(trash);
  }
}

// One parametric hole. The countersink cone is
// BRepPrimAPI_MakeCone(R1 = countersink dia/2, R2 = hole dia/2, H = (R1-R2)/tan(angle/2)).
// A 0.05 mm start outside the face keeps that angle and that face section.
// The cone is fused with the drill, then one cutShapes runs. A failed or empty
// result is deleted. The caller's shape is not an argument of the Boolean.
export function cutHole(oc, shape, spec) {
  const src = spec || {};
  const face = src.face;
  const dir = unitDir(src.dir);
  const diameter = Number(src.diameterMm);
  const radius = diameter / 2;
  const countersink = src.countersink === true;
  const csDia = Number(src.countersinkDiameterMm);
  const angle = Number(src.countersinkAngleDeg);
  const depthMode = src.depthMode === 'blind' ? 'blind' : 'through';
  if (!shape || !face || face.length < 3 || !dir) {
    return holeFail('FAIL: hole needs one solid and a face point.');
  }
  if (!(radius > 0)) return holeFail('FAIL: hole diameter must be a positive number of millimetres.');
  if (countersink) {
    if (!(csDia / 2 > radius)) return holeFail('FAIL: countersink diameter must be larger than the hole.');
    if (!(angle > 0) || !(angle < 180)) return holeFail('FAIL: countersink angle must be between 0 and 180 degrees.');
  }
  let volumeBefore = 0;
  try {
    volumeBefore = solidVolumeMm3(oc, shape);
  } catch (err) {
    return holeFail('FAIL: hole volume threw ' + explain(oc, err));
  }
  let depth = Number(src.depthMm);
  if (depthMode === 'through') {
    depth = measureThroughMm(oc, shape, face, dir);
    if (!(depth > 0)) return holeFail('FAIL: could not measure a through depth.', volumeBefore);
  } else if (!(depth > 0)) {
    return holeFail('FAIL: blind depth must be a positive number of millimetres.', volumeBefore);
  }
  const csHeight = countersink ? countersinkHeightMm(diameter, csDia, angle) : 0;
  if (countersink && !(csHeight > 0)) return holeFail('FAIL: countersink height is not positive.', volumeBefore);
  if (countersink && depth + 1e-6 < csHeight) {
    return holeFail('FAIL: the hole is shorter than the countersink.', volumeBefore);
  }
  const pad = HOLE_CUTTER_PAD_MM;
  const start = addScaled(face, dir, -pad);
  const cylLen = depth + (depthMode === 'through' ? pad * 2 : pad);
  const cylinder = makeCylinderSolid(oc, radius, cylLen, start, dir);
  if (!cylinder) return holeFail('FAIL: the hole drill was not built.', volumeBefore);
  let tool = cylinder;
  if (countersink) {
    const half = (angle / 2) * Math.PI / 180;
    const r1 = csDia / 2;
    const cone = makeConeSolid(oc, r1 + pad * Math.tan(half), radius, csHeight + pad, start, dir);
    if (!cone) {
      releaseShape(cylinder);
      return holeFail('FAIL: the countersink cone was not built.', volumeBefore);
    }
    const fused = fuseShapes(oc, cone, cylinder);
    releaseShape(cone);
    releaseShape(cylinder);
    if (!fused.ok || !fused.shape) {
      if (fused.shape) releaseShape(fused.shape);
      return holeFail(fused.error || 'FAIL: the countersink fuse failed.', volumeBefore);
    }
    tool = fused.shape;
  }
  const base = ownedCopy(oc, shape);
  if (!base) {
    releaseShape(tool);
    return holeFail('FAIL: the solid could not be copied.', volumeBefore);
  }
  const cut = cutShapes(oc, base, tool);
  releaseShape(base);
  releaseShape(tool);
  if (!cut.ok || !cut.shape) {
    if (cut.shape) releaseShape(cut.shape);
    return holeFail(cut.error || 'FAIL: the hole cut failed.', volumeBefore);
  }
  const gated = checkSolidGate(oc, cut.shape);
  if (!gated.pass || !(gated.volume + 1e-6 < volumeBefore)) {
    releaseShape(cut.shape);
    const why = gated.pass ? 'FAIL: the hole did not remove material.' : (gated.error || 'FAIL: the hole failed the gate.');
    return holeFail(why, volumeBefore);
  }
  return {
    ok: true,
    shape: cut.shape,
    kept: false,
    error: '',
    volumeBefore: volumeBefore,
    volumeAfter: gated.volume,
    depthMm: depth,
    countersinkHeightMm: csHeight,
    units: 'mm',
    gate: gated.view.gate,
    watertight: gated.view.watertight,
    mesh: gated.view.mesh,
    topology: gated.view.topology,
    bounds: gated.bounds,
    solids: gated.solids,
  };
}

export function checkSolidGate(oc, shape) {
  let view;
  try {
    view = inspectSolid(oc, shape);
  } catch (err) {
    return {
      pass: false,
      error: 'FAIL: gate threw ' + explain(oc, err),
      view: emptySolid(),
      solids: 0,
      volume: 0,
      bounds: null,
    };
  }
  let solids = 0;
  let volume = 0;
  let bounds = null;
  try {
    solids = countSolids(oc, shape);
    volume = solidVolumeMm3(oc, shape);
    bounds = solidBounds(oc, shape);
  } catch (err) {
    return {
      pass: false,
      error: 'FAIL: volume threw ' + explain(oc, err),
      view: view,
      solids: solids,
      volume: volume,
      bounds: bounds,
    };
  }
  const units = unitsLockGate();
  const pass = view.gate.pass === true
    && view.watertight.pass === true
    && units.pass === true
    && solids === 1
    && volume > BOOLEAN_EMPTY_VOLUME_MM3;
  let error = '';
  if (!pass) {
    if (view.gate.pass !== true) error = view.gate.message || 'FAIL: OCCT gate failed.';
    else if (view.watertight.pass !== true) error = view.watertight.message || 'FAIL: mesh is not watertight.';
    else if (units.pass !== true) error = units.message;
    else if (solids !== 1) error = 'FAIL: expected one solid, found ' + solids + '.';
    else error = 'FAIL: result is empty.';
  }
  return { pass: pass, error: error, view: view, solids: solids, volume: volume, bounds: bounds };
}

function matchEdges(oc, shape, segments, trash) {
  const found = collectEdges(oc, shape, trash);
  const chosen = [];
  const used = new Set();
  for (let i = 0; i < segments.length; i += 1) {
    const segment = segments[i];
    const hit = found.find(function (edge, index) {
      if (used.has(index)) return false;
      return segmentMatch(edge.a, edge.b, segment.a[0], segment.a[1], segment.a[2], segment.b[0], segment.b[1], segment.b[2]);
    });
    if (!hit) return [];
    used.add(found.indexOf(hit));
    chosen.push(hit.edge);
  }
  return chosen;
}

// Fillet or chamfer on edges the user picked. Failure leaves the caller's shape alone.
export function applyPickedEdgeOp(oc, shape, segments, kind, size) {
  const which = kind === 'chamfer' ? 'chamfer' : 'fillet';
  if (!shape || !segments || !segments.length) {
    return { ok: false, shape: null, error: 'FAIL: ' + which + ' has no picked edge. The last good shape was kept.', kept: true };
  }
  const trash = [];
  let made = null;
  try {
    const edges = matchEdges(oc, shape, segments, trash);
    if (!edges.length) {
      return {
        ok: false,
        shape: null,
        error: 'FAIL: picked edge was not found on the solid. The last good shape was kept.',
        kept: true,
      };
    }
    made = which === 'chamfer'
      ? chamferEdges(oc, shape, size, edges)
      : filletEdges(oc, shape, size, edges);
  } catch (err) {
    return {
      ok: false,
      shape: null,
      error: 'FAIL: ' + which + ' threw ' + explain(oc, err) + ' The last good shape was kept.',
      kept: true,
    };
  } finally {
    dispose(trash);
  }
  if (!made || !made.ok || !made.shape) {
    return {
      ok: false,
      shape: null,
      error: (made && made.error ? made.error : 'FAIL: ' + which + ' was rejected.') + ' The last good shape was kept.',
      kept: true,
    };
  }
  const gated = checkSolidGate(oc, made.shape);
  if (!gated.pass) {
    releaseShape(made.shape);
    return {
      ok: false,
      shape: null,
      error: gated.error + ' The last good shape was kept.',
      kept: true,
    };
  }
  return {
    ok: true,
    shape: made.shape,
    error: '',
    kept: false,
    units: 'mm',
    volumeMm3: gated.volume,
    bounds: gated.bounds,
    solids: gated.solids,
    gate: gated.view.gate,
    watertight: gated.view.watertight,
    mesh: gated.view.mesh,
    topology: gated.view.topology,
    meshTimeMs: gated.view.meshTimeMs || 0,
    meshSettings: gated.view.meshSettings || null,
    meshPath: gated.view.meshPath || '',
  };
}

