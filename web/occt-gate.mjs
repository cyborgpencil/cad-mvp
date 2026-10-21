// OCCT export gate for the WASM page.
// Builds a sewn B-Rep from the current triangle mesh, then requires
// BRepCheck_Analyzer.IsValid() and ShapeAnalysis_FreeBounds with zero free edges.

export function closedBoxMesh() {
  return {
    vertices: [
      [0, 0, 0], [1, 0, 0], [1, 1, 0], [0, 1, 0],
      [0, 0, 1], [1, 0, 1], [1, 1, 1], [0, 1, 1],
    ],
    triangles: [
      [0, 2, 1], [0, 3, 2],
      [4, 5, 6], [4, 6, 7],
      [0, 5, 4], [0, 1, 5],
      [3, 6, 2], [3, 7, 6],
      [0, 7, 3], [0, 4, 7],
      [1, 2, 6], [1, 6, 5],
    ],
  };
}

export function openBoxMesh() {
  const mesh = closedBoxMesh();
  mesh.triangles = mesh.triangles.filter((tri) => {
    const a = mesh.vertices[tri[0]];
    const b = mesh.vertices[tri[1]];
    const c = mesh.vertices[tri[2]];
    return !(a[2] === 1 && b[2] === 1 && c[2] === 1);
  });
  return mesh;
}

export function box20Mesh() {
  const mesh = closedBoxMesh();
  mesh.vertices = mesh.vertices.map((p) => [p[0] * 20, p[1] * 20, p[2] * 20]);
  return mesh;
}

export function meshFromFlat(positions, indices) {
  const vertices = [];
  for (let i = 0; i + 2 < positions.length; i += 3) {
    vertices.push([positions[i], positions[i + 1], positions[i + 2]]);
  }
  const triangles = [];
  for (let i = 0; i + 2 < indices.length; i += 3) {
    triangles.push([indices[i], indices[i + 1], indices[i + 2]]);
  }
  return { vertices, triangles };
}

function countShapes(oc, shape, type) {
  if (!shape || (typeof shape.IsNull === 'function' && shape.IsNull())) {
    return 0;
  }
  const explorer = new oc.TopExp_Explorer(shape, type);
  let count = 0;
  while (explorer.More()) {
    count += 1;
    explorer.Next();
  }
  explorer.delete();
  return count;
}

function failResult(message, extra) {
  return Object.assign({
    pass: false,
    valid: false,
    freeEdges: -1,
    message,
  }, extra || {});
}

// BRepCheck_Analyzer + ShapeAnalysis_FreeBounds on a B-rep (a primitive solid).
// The mesh sew path in checkOcctGate stays the gate for fixtures that have no solid.
export function checkOcctShape(oc, shape) {
  if (!oc) {
    return failResult('FAIL: OCCT module is not loaded.');
  }
  if (!shape || (typeof shape.IsNull === 'function' && shape.IsNull())) {
    return failResult('FAIL: OCCT gate has no shape to check.');
  }
  const trash = [];
  const track = (obj) => {
    if (obj && typeof obj.delete === 'function') {
      trash.push(obj);
    }
    return obj;
  };
  try {
    const analyzer = track(new oc.BRepCheck_Analyzer(shape));
    const valid = !!analyzer.IsValid();
    const bounds = track(new oc.ShapeAnalysis_FreeBounds(shape, false, true, false));
    const closedWires = track(bounds.GetClosedWires());
    const openWires = track(bounds.GetOpenWires());
    const edgeType = oc.TopAbs_ShapeEnum.TopAbs_EDGE;
    const freeEdges = countShapes(oc, closedWires, edgeType) + countShapes(oc, openWires, edgeType);
    const closed = freeEdges === 0;
    const pass = valid && closed;
    let message;
    if (pass) {
      message = 'PASS: OCCT BRepCheck_Analyzer is valid and ShapeAnalysis_FreeBounds found 0 free edges.';
    } else if (!valid && !closed) {
      message = 'FAIL: OCCT BRepCheck_Analyzer is not valid and ShapeAnalysis_FreeBounds found '
        + freeEdges + ' free edges.';
    } else if (!valid) {
      message = 'FAIL: OCCT BRepCheck_Analyzer is not valid.';
    } else {
      message = 'FAIL: OCCT ShapeAnalysis_FreeBounds found ' + freeEdges + ' free edges.';
    }
    return { pass, valid, freeEdges, message };
  } catch (err) {
    return failResult('FAIL: OCCT gate error: ' + (err && err.message ? err.message : String(err)));
  } finally {
    for (let i = trash.length - 1; i >= 0; i -= 1) {
      try {
        trash[i].delete();
      } catch (_err) {
        // already released
      }
    }
  }
}

export function checkOcctGate(oc, mesh) {
  if (!oc) {
    return failResult('FAIL: OCCT module is not loaded.');
  }
  if (!mesh || !mesh.triangles || mesh.triangles.length === 0 || !mesh.vertices) {
    return failResult('FAIL: OCCT gate has no triangles to check.');
  }

  const trash = [];
  const track = (obj) => {
    if (obj && typeof obj.delete === 'function') {
      trash.push(obj);
    }
    return obj;
  };

  try {
    const sewer = track(new oc.BRepBuilderAPI_Sewing(1e-6, true, true, true, false));
    let added = 0;
    for (let t = 0; t < mesh.triangles.length; t += 1) {
      const tri = mesh.triangles[t];
      const a = mesh.vertices[tri[0]];
      const b = mesh.vertices[tri[1]];
      const c = mesh.vertices[tri[2]];
      if (!a || !b || !c) {
        continue;
      }
      const p1 = track(new oc.gp_Pnt(a[0], a[1], a[2]));
      const p2 = track(new oc.gp_Pnt(b[0], b[1], b[2]));
      const p3 = track(new oc.gp_Pnt(c[0], c[1], c[2]));
      const poly = track(new oc.BRepBuilderAPI_MakePolygon(p1, p2, p3, true));
      if (!poly.IsDone()) {
        continue;
      }
      const wire = track(poly.Wire());
      const faceMaker = track(new oc.BRepBuilderAPI_MakeFace(wire, true));
      if (!faceMaker.IsDone()) {
        continue;
      }
      const face = track(faceMaker.Face());
      sewer.Add(face);
      added += 1;
    }
    if (added === 0) {
      return failResult('FAIL: OCCT could not build faces from the mesh.');
    }
    sewer.Perform();
    const sewn = track(sewer.SewedShape());
    if (!sewn || (typeof sewn.IsNull === 'function' && sewn.IsNull())) {
      return failResult('FAIL: OCCT sewing produced no shape.');
    }

    const analyzer = track(new oc.BRepCheck_Analyzer(sewn));
    const valid = !!analyzer.IsValid();

    const bounds = track(new oc.ShapeAnalysis_FreeBounds(sewn, false, true, false));
    const closedWires = track(bounds.GetClosedWires());
    const openWires = track(bounds.GetOpenWires());
    const edgeType = oc.TopAbs_ShapeEnum.TopAbs_EDGE;
    const freeEdges = countShapes(oc, closedWires, edgeType) + countShapes(oc, openWires, edgeType);
    const closed = freeEdges === 0;
    const pass = valid && closed;

    let message;
    if (pass) {
      message = 'PASS: OCCT BRepCheck_Analyzer is valid and ShapeAnalysis_FreeBounds found 0 free edges.';
    } else if (!valid && !closed) {
      message = 'FAIL: OCCT BRepCheck_Analyzer is not valid and ShapeAnalysis_FreeBounds found '
        + freeEdges + ' free edges.';
    } else if (!valid) {
      message = 'FAIL: OCCT BRepCheck_Analyzer is not valid.';
    } else {
      message = 'FAIL: OCCT ShapeAnalysis_FreeBounds found ' + freeEdges + ' free edges.';
    }

    return { pass, valid, freeEdges, message };
  } catch (err) {
    return failResult('FAIL: OCCT gate error: ' + (err && err.message ? err.message : String(err)));
  } finally {
    for (let i = trash.length - 1; i >= 0; i -= 1) {
      try {
        trash[i].delete();
      } catch (_err) {
        // already released
      }
    }
  }
}
