// Phone selection: tap vs drag, filter cycle, edge radius, Multi, count.
// No OCCT and no DOM.
import { pathToFileURL, fileURLToPath } from 'node:url';
import path from 'node:path';

const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..');
const phone = await import(pathToFileURL(path.join(root, 'web', 'phone-select.mjs')).href);
const selection = await import(pathToFileURL(path.join(root, 'web', 'selection.mjs')).href);
const view = await import(pathToFileURL(path.join(root, 'web', 'viewport-selection.mjs')).href);

const failures = [];

function expect(name, got, want) {
  const same = JSON.stringify(got) === JSON.stringify(want);
  if (same) {
    console.log('PASS ' + name);
    return;
  }
  console.error('FAIL ' + name + ' got ' + JSON.stringify(got) + ' want ' + JSON.stringify(want));
  failures.push(name);
}

function expectOk(name, ok) {
  if (ok) {
    console.log('PASS ' + name);
    return;
  }
  console.error('FAIL ' + name);
  failures.push(name);
}

const SLOP = view.TAP_SLOP_PX;
const TOUCH = selection.TOUCH_PICK_TOLERANCE_PX;
const MOUSE = selection.PICK_TOLERANCE_PX;

expect('filters', phone.PICK_FILTERS, ['body', 'face', 'edge', 'vertex']);
expect('chip min', phone.CHIP_MIN_PX, 44);
expect('edge radius', phone.EDGE_TOUCH_TOLERANCE_PX, 32);
expectOk('edge radius is larger than touch pick', phone.EDGE_TOUCH_TOLERANCE_PX > TOUCH);
expect('touch pick stays 20', TOUCH, 20);
expect('mouse pick stays 8', MOUSE, 8);
expect('tap slop stays 8', SLOP, 8);

expect('label body', phone.filterLabel('body'), 'Body');
expect('label face', phone.filterLabel('face'), 'Face');
expect('label edge', phone.filterLabel('edge'), 'Edge');
expect('label vertex', phone.filterLabel('vertex'), 'Vertex');
expect('label unknown', phone.filterLabel('nope'), 'Body');

expect('mode body', phone.modeForFilter('body'), 'item');
expect('mode face', phone.modeForFilter('face'), 'face');
expect('mode edge', phone.modeForFilter('edge'), 'edge');
expect('mode vertex', phone.modeForFilter('vertex'), 'vertex');
expect('mode unknown', phone.modeForFilter(''), 'item');

expect('filter item', phone.filterForMode('item'), 'body');
expect('filter face', phone.filterForMode('face'), 'face');
expect('filter edge', phone.filterForMode('edge'), 'edge');
expect('filter vertex', phone.filterForMode('vertex'), 'vertex');

expect('next body', phone.nextFilter('body'), 'face');
expect('next face', phone.nextFilter('face'), 'edge');
expect('next edge', phone.nextFilter('edge'), 'vertex');
expect('next vertex', phone.nextFilter('vertex'), 'body');
expect('next unknown', phone.nextFilter('nope'), 'body');
let cycle = 'body';
for (let i = 0; i < 4; i += 1) cycle = phone.nextFilter(cycle);
expect('cycle returns', cycle, 'body');

expect('edge touch', phone.pickTolerancePx('edge', 'touch', TOUCH, MOUSE), 32);
expect('edge pen', phone.pickTolerancePx('edge', 'pen', TOUCH, MOUSE), 32);
expect('edge mode touch', phone.pickTolerancePx('edge', 'touch', TOUCH, MOUSE), phone.EDGE_TOUCH_TOLERANCE_PX);
expect('edge mouse stays shared', phone.pickTolerancePx('edge', 'mouse', TOUCH, MOUSE), MOUSE);
expect('face touch stays 20', phone.pickTolerancePx('face', 'touch', TOUCH, MOUSE), TOUCH);
expect('body touch stays 20', phone.pickTolerancePx('body', 'touch', TOUCH, MOUSE), TOUCH);
expect('item touch stays 20', phone.pickTolerancePx('item', 'touch', TOUCH, MOUSE), TOUCH);
expect('vertex touch stays 20', phone.pickTolerancePx('vertex', 'touch', TOUCH, MOUSE), TOUCH);
expect('vertex mouse', phone.pickTolerancePx('vertex', 'mouse', TOUCH, MOUSE), MOUSE);
expect('face mouse', phone.pickTolerancePx('face', '', TOUCH, MOUSE), MOUSE);

expect('class tap', phone.classifyPointer(0, 0, SLOP, false), 'tap');
expect('class under slop', phone.classifyPointer(SLOP - 0.1, 0, SLOP, false), 'tap');
expect('class at slop is drag', phone.classifyPointer(SLOP, 0, SLOP, false), 'drag');
expect('class past slop', phone.classifyPointer(0, SLOP + 4, SLOP, false), 'drag');
expect('class diagonal under', phone.classifyPointer(3, 3, SLOP, false), 'tap');
expect('class cancel', phone.classifyPointer(0, 0, SLOP, true), 'cancel');
expect('class bad', phone.classifyPointer('x', 0, SLOP, false), 'cancel');
expect('should tap', phone.shouldSelect(1, 1, SLOP, false), true);
expect('should drag', phone.shouldSelect(SLOP, 0, SLOP, false), false);
expect('should cancel', phone.shouldSelect(0, 0, SLOP, true), false);

const none = [];
const cleared = phone.selectionFromTap('item', none, null, false);
expect('empty clears', cleared.ids, []);
expect('empty count', cleared.count, 0);
expect('empty action', cleared.action, 'clear');
expect('empty no highlight', cleared.highlight, false);
expect('body empty is not all', cleared.all, false);

const replaced = phone.selectionFromTap('item', ['old'], 'item', false);
expect('replace ids', replaced.ids, ['item']);
expect('replace count', replaced.count, 1);
expect('replace action', replaced.action, 'replace');
expect('replace highlight', replaced.highlight, true);

const faceClear = phone.selectionFromTap('face', ['f0'], null, false);
expect('face clear all', faceClear.all, true);
expect('face clear count', faceClear.count, 0);

const start = ['b1'];
const added = phone.selectionFromTap('item', start, 'b2', true);
expect('multi add', added.ids, ['b1', 'b2']);
expect('multi add count', added.count, 2);
expect('multi add action', added.action, 'add');
expect('multi does not mutate', start, ['b1']);

const removed = phone.selectionFromTap('item', added.ids, 'b2', true);
expect('multi remove', removed.ids, ['b1']);
expect('multi remove count', removed.count, 1);
expect('multi remove action', removed.action, 'remove');

const multiClear = phone.selectionFromTap('item', ['b1', 'b2'], null, true);
expect('multi empty clears', multiClear.ids, []);
expect('multi empty action', multiClear.action, 'clear');

const off = phone.selectionFromTap('face', ['f0', 'f1'], 'f2', false);
expect('multi off replaces', off.ids, ['f2']);
expect('multi off count', off.count, 1);

expect('count none', phone.selectionCount(null), 0);
expect('count two', phone.selectionCount(['a', 'b']), 2);
expect('text zero', phone.countText(0), '0 selected');
expect('text one', phone.countText(1), '1 selected');
expect('text two', phone.countText(2), '2 selected');
expect('text bad', phone.countText('nope'), '0 selected');

const beside = phone.pointBesideSegment(0, 0, 10, 0, 24);
expect('beside x', beside.x, 5);
expect('beside y', beside.y, 24);
const other = phone.pointBesideSegment(0, 0, 10, 0, -24);
expect('beside other', other, { x: 5, y: -24 });
const gap = (TOUCH + phone.EDGE_TOUCH_TOLERANCE_PX) / 2;
const mid = phone.pointBesideSegment(10, 20, 40, 20, gap);
const along = Math.hypot(mid.x - 25, mid.y - 20);
expectOk('beside sits between 20 and 32', along > TOUCH && along < phone.EDGE_TOUCH_TOLERANCE_PX);
expect('degenerate segment', phone.pointBesideSegment(3, 4, 3, 4, 24), { x: 3, y: 4 });

const filletArm = phone.armEdgeTool('fillet');
expect('fillet arms edge', filletArm.filter, 'edge');
expect('fillet mode', filletArm.mode, 'edge');
expect('fillet op', filletArm.op, 'fillet');
expect('fillet default', filletArm.sizeMm, 2);
expect('fillet default constant', phone.FILLET_DEFAULT_MM, 2);

const chamferArm = phone.armEdgeTool('chamfer');
expect('chamfer arms edge', chamferArm.filter, 'edge');
expect('chamfer mode', chamferArm.mode, 'edge');
expect('chamfer op', chamferArm.op, 'chamfer');
expect('chamfer default', chamferArm.sizeMm, 0.5);
expect('chamfer default constant', phone.CHAMFER_DEFAULT_MM, 0.5);
expect('unknown tool is fillet', phone.armEdgeTool('nope').op, 'fillet');
expect('unknown tool default', phone.armEdgeTool('').sizeMm, phone.FILLET_DEFAULT_MM);
expectOk('tools set different defaults', filletArm.sizeMm !== chamferArm.sizeMm);

expect('size 2', phone.parseEdgeSize('2'), { ok: true, size: 2 });
expect('size 0.5', phone.parseEdgeSize('0.5'), { ok: true, size: 0.5 });
expect('size spaced', phone.parseEdgeSize(' 2 '), { ok: true, size: 2 });
expect('size blank', phone.parseEdgeSize(''), { ok: false, size: NaN });
expect('size spaces', phone.parseEdgeSize('   '), { ok: false, size: NaN });
expect('size null', phone.parseEdgeSize(null), { ok: false, size: NaN });
expect('size zero', phone.parseEdgeSize('0'), { ok: false, size: 0 });
expect('size negative', phone.parseEdgeSize('-1'), { ok: false, size: -1 });
expect('size word', phone.parseEdgeSize('big'), { ok: false, size: NaN });

expect('one body id', phone.edgePickId('b1', 'e0', 1), 'e0');
expect('multi body id', phone.edgePickId('b1', 'e0', 2), 'b1:e0');
expect('split single', phone.splitEdgePick('e3', 'b1'), { bodyId: 'b1', edgeId: 'e3' });
expect('split multi', phone.splitEdgePick('b2:e4', 'b1'), { bodyId: 'b2', edgeId: 'e4' });

const oneEdge = phone.confirmEdgeDecision(['e0'], '2', 'b1');
expect('one edge enabled', oneEdge.enabled, true);
expect('one edge body', oneEdge.bodyId, 'b1');
expect('one edge quiet', oneEdge.message, '');

const twoEdges = phone.confirmEdgeDecision(['b1:e0', 'b1:e3'], '2', '');
expect('multi same body', twoEdges.enabled, true);
expect('multi same body id', twoEdges.bodyId, 'b1');
expect('multi same quiet', twoEdges.message, '');

const crossed = phone.confirmEdgeDecision(['b1:e0', 'b2:e1'], '2', '');
expect('cross body off', crossed.enabled, false);
expect('cross body message', crossed.message, 'pick edges on one body');
expect('cross body constant', phone.CROSS_BODY_MESSAGE, 'pick edges on one body');
expect('cross body no target', crossed.bodyId, '');

const crossObjects = phone.confirmEdgeDecision(
  [{ bodyId: 'b1', edgeId: 'e0' }, { bodyId: 'b9', edgeId: 'e2' }],
  '0.5',
  ''
);
expect('cross objects off', crossObjects.enabled, false);
expect('cross objects message', crossObjects.message, phone.CROSS_BODY_MESSAGE);

const badSize = phone.confirmEdgeDecision(['e0'], '', 'b1');
expect('blank size blocks', badSize.enabled, false);
expect('blank size is not cross body', badSize.message, '');
expect('blank size flag', badSize.sizeOk, false);

const zeroSize = phone.confirmEdgeDecision(['b1:e0'], '0', '');
expect('zero size blocks', zeroSize.enabled, false);
expect('zero size flag', zeroSize.sizeOk, false);

const negativeSize = phone.confirmEdgeDecision(['b1:e0', 'b1:e1'], '-2', '');
expect('negative size blocks', negativeSize.enabled, false);

const noEdge = phone.confirmEdgeDecision([], '2', 'b1');
expect('no edge blocks', noEdge.enabled, false);
expect('no edge quiet', noEdge.message, '');

expect('refillet allowed', phone.repeatEdgeOpAllowed(), true);
expect('smaller message', phone.SMALLER_SIZE_MESSAGE, 'Try a smaller size.');
expect('occt isdone is size', phone.occtSizeFailure('FAIL: fillet IsDone is false; Shape() was not called.'), true);
expect('occt invalid is size', phone.occtSizeFailure('FAIL: OCCT BRepCheck_Analyzer is not valid.'), true);
expect('occt throw is size', phone.occtSizeFailure('FAIL: fillet Build threw boom; Shape() was not called.'), true);
expect('missing edge is not size', phone.occtSizeFailure('FAIL: fillet has no edge.'), false);
expect('not found is not size', phone.occtSizeFailure('FAIL: picked edge was not found on the solid. The last good shape was kept.'), false);
expect('blank is not size', phone.occtSizeFailure(''), false);
expect('cross text is not size', phone.occtSizeFailure(phone.CROSS_BODY_MESSAGE), false);
expect('mesh reject is not size', phone.occtSizeFailure('FAIL: the new mesh was rejected. The last good shape was kept.'), false);

expect('sel point size', view.SEL_POINT_SIZE, 18);
expect('hover point size', view.HOVER_POINT_SIZE, 14);
expectOk('points thicker than the old 10 and 9', view.SEL_POINT_SIZE > 10 && view.HOVER_POINT_SIZE > 9);
expectOk('hover point is smaller', view.HOVER_POINT_SIZE < view.SEL_POINT_SIZE);
expect('sel edge px', view.SEL_EDGE_PX, 6);
expect('hover edge px', view.HOVER_EDGE_PX, 4);
expectOk('edges thicker than a 1px webgl line', view.SEL_EDGE_PX > 1 && view.HOVER_EDGE_PX > 1);
expectOk('hover edge is thinner', view.HOVER_EDGE_PX < view.SEL_EDGE_PX);

const ribbon = view.expandEdgeOverlay([1, 2, 3, 4, 5, 6]);
expect('ribbon count', ribbon.count, 1);
expect('ribbon position length', ribbon.position.length, 18);
expect('ribbon side', Array.from(ribbon.side), [-1, 1, 1, -1, 1, -1]);
expect('ribbon end', Array.from(ribbon.end), [-1, -1, 1, -1, 1, 1]);
expect('ribbon start', [ribbon.position[0], ribbon.position[1], ribbon.position[2]], [1, 2, 3]);
expect('ribbon far', [ribbon.position[6], ribbon.position[7], ribbon.position[8]], [4, 5, 6]);
expect('fatA stays start', [ribbon.fatA[6], ribbon.fatA[7], ribbon.fatA[8]], [1, 2, 3]);
expect('fatB stays end', [ribbon.fatB[0], ribbon.fatB[1], ribbon.fatB[2]], [4, 5, 6]);
expect('empty ribbon', view.expandEdgeOverlay([]).count, 0);
expect('two ribbons', view.expandEdgeOverlay([0, 0, 0, 1, 0, 0, 1, 0, 0, 1, 1, 0]).count, 2);

function StubColor() {
  this.r = 1;
  this.g = 1;
  this.b = 1;
  this.copy = function (c) {
    this.r = c.r;
    this.g = c.g;
    this.b = c.b;
    return this;
  };
}
function StubVector2(x, y) {
  this.x = x || 0;
  this.y = y || 0;
  this.set = function (nx, ny) {
    this.x = nx;
    this.y = ny;
    return this;
  };
}
function StubGeometry() {
  this.attributes = {};
  this.setAttribute = function (name, attr) {
    this.attributes[name] = attr;
    return this;
  };
  this.dispose = function () {};
}
function StubAttr(array, itemSize) {
  this.array = array;
  this.itemSize = itemSize;
}
function StubBasic(params) {
  this.opacity = params.opacity;
  this.depthTest = params.depthTest;
  this.depthWrite = params.depthWrite;
  this.transparent = params.transparent;
  this.side = params.side;
  this.color = new StubColor();
  this.userData = {};
  this.isMeshBasicMaterial = true;
}
function StubPoints(params) {
  this.size = params.size;
  this.sizeAttenuation = params.sizeAttenuation;
  this.depthTest = params.depthTest;
  this.color = new StubColor();
}
function StubObject(geo, mat) {
  this.geometry = geo;
  this.material = mat;
  this.userData = {};
  this.visible = true;
  this.renderOrder = 0;
  this.frustumCulled = true;
}
const stubThree = {
  DoubleSide: 2,
  Vector2: StubVector2,
  BufferGeometry: StubGeometry,
  BufferAttribute: StubAttr,
  MeshBasicMaterial: StubBasic,
  PointsMaterial: StubPoints,
  Mesh: StubObject,
  Points: StubObject,
};
const overlays = view.makeOverlays(stubThree);
expect('sel point material', overlays.selPoints.material.size, view.SEL_POINT_SIZE);
expect('hover point material', overlays.hoverPoints.material.size, view.HOVER_POINT_SIZE);
expect('sel edge material', overlays.selLines.material.userData.edgePx, view.SEL_EDGE_PX);
expect('hover edge material', overlays.hoverLines.material.userData.edgePx, view.HOVER_EDGE_PX);
expect('item opacity stays', overlays.selFace.userData.itemOpacity, 0.35);
expect('face opacity stays', overlays.selFace.userData.faceOpacity, 0.72);
expectOk('edge overlay is a fat mesh', overlays.selLines.userData.fatEdge === true && overlays.selLines.material.isMeshBasicMaterial === true);
expect('fat cache key', overlays.selLines.material.customProgramCacheKey(), 'fat-edge-overlay');
expectOk('hover cache matches', overlays.hoverLines.material.customProgramCacheKey() === overlays.selLines.material.customProgramCacheKey());

overlays.setBuffer(overlays.selFace, new Float32Array([0, 0, 0, 1, 0, 0, 0, 1, 0]), 3);
expect('face buffer length', overlays.selFace.geometry.attributes.position.array.length, 9);
expectOk('face is not a ribbon', overlays.selFace.geometry.attributes.fatA == null);
expect('face visible', overlays.selFace.visible, true);

overlays.setBuffer(overlays.selLines, new Float32Array([0, 0, 0, 10, 0, 0]), 3);
expect('edge visible', overlays.selLines.visible, true);
expect('edge expanded', overlays.selLines.geometry.attributes.position.array.length, 18);
expect('edge fatSide', overlays.selLines.geometry.attributes.fatSide.array.length, 6);
overlays.setBuffer(overlays.hoverLines, new Float32Array(0), 3);
expect('hover edge hidden', overlays.hoverLines.visible, false);
overlays.setBuffer(overlays.selLines, new Float32Array(0), 3);
expect('sel edge hidden', overlays.selLines.visible, false);
expectOk('cleared edge has no position', overlays.selLines.geometry.attributes.position == null);

const shader = {
  uniforms: {},
  vertexShader: 'void main(){\n#include <project_vertex>\n}\n',
};
overlays.selLines.material.onBeforeCompile(shader, {
  getDrawingBufferSize: function (target) { return target.set(200, 100); },
  domElement: { clientWidth: 100, width: 200, height: 100 },
});
expect('thickness tracks device pixels', shader.uniforms.edgeThickness.value, view.SEL_EDGE_PX * 2);
expect('resolution width', shader.uniforms.edgeResolution.value.x, 200);
expectOk('project include stays', shader.vertexShader.indexOf('#include <project_vertex>') >= 0);
expectOk('ribbon shader injected', shader.vertexShader.indexOf('fatClipA') >= 0 && shader.vertexShader.indexOf('fatA') >= 0);
expectOk('shader has no colour literal', shader.vertexShader.indexOf('#ff4fd8') < 0 && shader.vertexShader.indexOf('linewidth') < 0);
const injected = shader.vertexShader;
overlays.selLines.material.onBeforeCompile(shader, null);
expect('shader injects once', shader.vertexShader, injected);
overlays.selLines.onBeforeRender({
  getDrawingBufferSize: function (target) { return target.set(300, 150); },
  domElement: { clientWidth: 100 },
});
expect('resize keeps css width', overlays.selLines.material.userData.edgeThickness.value, view.SEL_EDGE_PX * 3);

const vertexClick = selection.applyPointerSelection('vertex', ['v0', 'v1'], 'v2', {});
expect('vertex click replaces', vertexClick.ids, ['v2']);
expect('vertex click highlight', vertexClick.highlight, true);
expect('vertex click not all', vertexClick.all, false);
const edgeClick = selection.applyPointerSelection('edge', ['e0'], 'e4', {});
expect('edge click replaces', edgeClick.ids, ['e4']);
expect('edge click highlight', edgeClick.highlight, true);
expect('edge click not all', edgeClick.all, false);
const faceClick = selection.applyPointerSelection('face', ['f0', 'f4'], 'f1', {});
expect('face click replaces', faceClick.ids, ['f1']);
expect('face click highlight', faceClick.highlight, true);
expect('face click not all', faceClick.all, false);
const shiftEdge = selection.applyPointerSelection('edge', ['e0'], 'e1', { shift: true });
expect('shift still adds', shiftEdge.ids, ['e0', 'e1']);
expect('shift highlight', shiftEdge.highlight, true);
const emptyVertex = selection.applyPointerSelection('vertex', ['v0'], null, {});
expect('empty vertex ids', emptyVertex.ids, []);
expect('empty vertex all', emptyVertex.all, true);
expect('empty vertex highlight', emptyVertex.highlight, false);
const emptyEdge = selection.applyPointerSelection('edge', ['e0', 'e1'], null, {});
expect('empty edge ids', emptyEdge.ids, []);
expect('empty edge all', emptyEdge.all, true);
expect('empty edge highlight', emptyEdge.highlight, false);
const emptyFace = selection.applyPointerSelection('face', ['f0'], null, {});
expect('empty face ids', emptyFace.ids, []);
expect('empty face all', emptyFace.all, true);
expect('empty face highlight', emptyFace.highlight, false);

if (failures.length) {
  console.error('FAIL ' + failures.length);
  process.exit(1);
}
console.log('ok');
