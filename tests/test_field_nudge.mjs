// Field-nudge step math, axis lock, threshold, and clamp. No OCCT, no DOM.
import { pathToFileURL, fileURLToPath } from 'node:url';
import path from 'node:path';

const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..');
const nudge = await import(pathToFileURL(path.join(root, 'web', 'field-nudge.mjs')).href);

const failures = [];

function expect(name, got, want) {
  if (got === want) {
    console.log('PASS ' + name);
    return;
  }
  console.error('FAIL ' + name + ' got ' + JSON.stringify(got) + ' want ' + JSON.stringify(want));
  failures.push(name);
}

expect('STEP_PX is 24', nudge.STEP_PX, 24);
expect('axis is horizontal', nudge.AXIS, 'x');
expect('mm step is 1', nudge.MM_STEP, 1);
expect('deg step is 1', nudge.DEG_STEP, 1);
expect('size floor is 0.1', nudge.MIN_SIZE_MM, 0.1);

const PX = nudge.STEP_PX;

const size = nudge.fieldSpec('boxSx');
const centre = nudge.fieldSpec('primCy');
const rot = nudge.fieldSpec('primRx');
expect('size kind', size && size.kind, 'size');
expect('size unit', size && size.unit, 'mm');
expect('size step', size && size.step, 1);
expect('size min', size && size.min, 0.1);
expect('centre kind', centre && centre.kind, 'centre');
expect('centre unit', centre && centre.unit, 'mm');
expect('rotation kind', rot && rot.kind, 'rotation');
expect('rotation unit', rot && rot.unit, 'deg');
expect('rotation step', rot && rot.step, 1);
expect('bbox is size', nudge.fieldSpec('bboxZ') && nudge.fieldSpec('bboxZ').kind, 'size');
expect('cylinder diameter is size', nudge.fieldSpec('cylD') && nudge.fieldSpec('cylD').kind, 'size');
expect('disc thickness is size', nudge.fieldSpec('discT') && nudge.fieldSpec('discT').kind, 'size');
expect('hole is not a nudge field', nudge.fieldSpec('holeDia'), null);
expect('hole angle is not a nudge field', nudge.fieldSpec('holeCsAng'), null);
expect('empty id', nudge.fieldSpec(''), null);

expect('travel 24', nudge.stepsFromTravel(PX), 1);
expect('travel 23', nudge.stepsFromTravel(PX - 1), 0);
expect('travel 48', nudge.stepsFromTravel(PX * 2), 2);
expect('travel 72', nudge.stepsFromTravel(PX * 3), 3);
expect('travel -24', nudge.stepsFromTravel(-PX), -1);
expect('travel -23', nudge.stepsFromTravel(-(PX - 1)), 0);
expect('travel -72', nudge.stepsFromTravel(-PX * 3), -3);
expect('travel NaN', nudge.stepsFromTravel(NaN), 0);

expect('lock short', nudge.lockAxis(PX - 1, 0), '');
expect('lock right', nudge.lockAxis(PX, 0), 'x');
expect('lock left', nudge.lockAxis(-PX, 4), 'x');
expect('lock tie is horizontal', nudge.lockAxis(PX, PX), 'x');
expect('lock tie left', nudge.lockAxis(-PX, PX), 'x');
expect('lock up', nudge.lockAxis(0, -PX), 'y');
expect('lock down wins', nudge.lockAxis(PX, PX + 1), 'y');
expect('lock vertical wins a long x', nudge.lockAxis(PX, -(PX + 1)), 'y');

expect('clamp size up', nudge.clampValue(20, 1, size), 21);
expect('clamp size down', nudge.clampValue(20, -1, size), 19);
expect('clamp size floor', nudge.clampValue(0.4, -1, size), 0.1);
expect('clamp size at floor', nudge.clampValue(0.1, -1, size), 0.1);
expect('clamp size under floor stays', nudge.clampValue(0.05, -1, size), 0.05);
expect('clamp size under floor can rise', nudge.clampValue(0.05, 1, size), 1.05);
expect('clamp centre negative', nudge.clampValue(-5, -1, centre), -6);
expect('clamp rotation up', nudge.clampValue(0, 1, rot), 1);
expect('clamp rotation down', nudge.clampValue(0, -1, rot), -1);
expect('clamp rotation past 360', nudge.clampValue(359, 1, rot), 360);
expect('clamp bad current', nudge.clampValue('nope', 1, size), 'nope');

function drag(session, dx, dy, focused) {
  session.down(7, 100, 200, focused !== false);
  return session.move(7, 100 + dx, 200 + dy);
}

const one = nudge.createFieldNudgeSession();
expect('session one step', drag(one, PX, 2, true), 1);
expect('session same bucket', one.move(7, 100 + PX + 4, 202), 0);
expect('session second step', one.move(7, 100 + PX * 2, 203), 1);
expect('session third step', one.move(7, 100 + PX * 3, 201), 1);
expect('session up adds nothing', one.up(7), 0);
expect('session after up', one.move(7, 100 + PX * 6, 201), 0);

const jump = nudge.createFieldNudgeSession();
expect('session jump is three steps', drag(jump, PX * 3, 1, true), 3);
expect('session jump not repeated', jump.move(7, 100 + PX * 3, 201), 0);

const back = nudge.createFieldNudgeSession();
expect('session out', drag(back, PX * 2, 0, true), 2);
expect('session back', back.move(7, 100, 200), -2);

const vertical = nudge.createFieldNudgeSession();
expect('session vertical', drag(vertical, 10, PX + 30, true), 0);
expect('session vertical stays locked', vertical.move(7, 100 + PX * 4, 200 + PX + 30), 0);
expect('session vertical axis', vertical.lockedAxis(), 'y');

const tie = nudge.createFieldNudgeSession();
expect('session tie', drag(tie, PX, PX, true), 1);
expect('session tie axis', tie.lockedAxis(), 'x');

const idle = nudge.createFieldNudgeSession();
expect('session unfocused down', idle.down(3, 0, 0, false), false);
expect('session unfocused move', idle.move(3, PX * 3, 0), 0);
expect('session unfocused up', idle.up(3), 0);

const aborted = nudge.createFieldNudgeSession();
expect('session before cancel', drag(aborted, PX * 2, 0, true), 2);
expect('session cancel', aborted.cancel(7), 0);
expect('session cancel move', aborted.move(7, 100 + PX * 5, 0), 0);
expect('session cancel ended', aborted.ended(), true);

const lost = nudge.createFieldNudgeSession();
expect('session before lost', drag(lost, PX, 0, true), 1);
expect('session lostpointercapture', lost.lostCapture(7), 0);
expect('session lost move', lost.move(7, 100 + PX * 4, 0), 0);
expect('session lost ended', lost.ended(), true);

const again = nudge.createFieldNudgeSession();
expect('session first gesture', drag(again, -PX, 0, true), -1);
again.up(7);
expect('session second gesture', drag(again, PX, 0, true), 1);

const other = nudge.createFieldNudgeSession();
other.down(1, 0, 0, true);
expect('session other pointer', other.move(2, PX * 2, 0), 0);
expect('session owner still zero until travel', other.move(1, 4, 0), 0);
expect('session owner step', other.move(1, PX, 0), 1);

if (failures.length) {
  console.error('FAIL field nudge ' + failures.length);
  process.exit(1);
}
console.log('PASS field nudge');
