const test = require('node:test');
const assert = require('node:assert/strict');
const vm = require('node:vm');
const fs = require('node:fs');
const path = require('node:path');
const source = fs.readFileSync(path.join(__dirname, '../static/demo-store.js'), 'utf8');
const storage = () => {
  const data = new Map();
  return { getItem: key => data.get(key) ?? null, setItem: (key, value) => data.set(key, String(value)), removeItem: key => data.delete(key) };
};
function setup(localStorage = storage(), sessionStorage = storage()) {
  const context = { window: {}, localStorage, sessionStorage };
  vm.runInNewContext(source, context);
  return { demo: context.window.RepairDemo, localStorage, sessionStorage };
}
const login = (demo, username) => demo.login(username, 'Practice123!');

test('teacher → admin → technician workflow persists across reload', () => {
  const { demo, localStorage, sessionStorage } = setup();
  assert.throws(() => demo.list(), /กรุณาเข้าสู่ระบบ/);
  assert.throws(() => demo.login('teacher', 'wrong'));
  login(demo, 'teacher');
  const repair = demo.create({ building: 'อาคาร 4', room: '401', type: 'aircon', urgency: 'high', description: 'แอร์ไม่เย็น' });
  assert.equal(repair.status, 'pending');
  assert.equal(demo.list().length, 4);
  demo.update(repair.id, 'comment', { text: 'ขอซ่อมก่อนเปิดเรียน' });
  assert.throws(() => demo.update(repair.id, 'assign', { assigned: 'technician', due: demo.today() }));
  demo.logout();
  assert.equal(demo.user(), undefined);
  login(demo, 'admin');
  assert.throws(() => demo.update(repair.id, 'assign', { assigned: 'teacher', due: demo.today() }));
  assert.throws(() => demo.update(repair.id, 'assign', { assigned: 'technician', due: '2000-01-01' }));
  demo.update(repair.id, 'assign', { assigned: 'technician', due: demo.today() });
  assert.equal(demo.get(repair.id).status, 'accepted');
  demo.logout();
  login(demo, 'technician');
  assert.throws(() => demo.update(repair.id, 'complete', { cost: '100', result: 'ซ่อมแล้ว' }));
  demo.update(repair.id, 'start');
  assert.throws(() => demo.update(repair.id, 'start'));
  assert.throws(() => demo.update(repair.id, 'complete', { cost: '-1', result: 'ซ่อมแล้ว' }));
  assert.throws(() => demo.update(repair.id, 'complete', { cost: '10', result: '  ' }));
  demo.update(repair.id, 'complete', { cost: '125.50', result: 'ล้างแอร์และทดสอบแล้ว' });
  const reloaded = setup(localStorage, sessionStorage).demo;
  assert.equal(reloaded.user().role, 'technician');
  assert.equal(reloaded.get(repair.id).status, 'completed');
  assert.equal(reloaded.get(repair.id).cost, 125.5);
  assert.equal(reloaded.get(repair.id).comments.length, 1);
  reloaded.logout();
  login(reloaded, 'teacher');
  assert.equal(reloaded.get(repair.id).result, 'ล้างแอร์และทดสอบแล้ว');
  assert.throws(() => reloaded.reset());
  login(reloaded, 'admin');
  reloaded.reset();
  assert.equal(reloaded.list().length, 3);
  assert.ok(!localStorage.getItem('repair-system-demo-v1').includes('Practice123!'));
});

test('role restrictions prevent invalid mutations and hidden work access', () => {
  const { demo } = setup();
  login(demo, 'technician');
  assert.throws(() => demo.get(1));
  assert.throws(() => demo.update(1, 'comment', { text: 'ไม่ได้รับมอบหมาย' }));
  assert.throws(() => demo.create({}));
  login(demo, 'admin');
  assert.throws(() => demo.update(2, 'start'));
  assert.throws(() => demo.update(3, 'assign', { assigned: 'technician', due: demo.today() }));
  assert.throws(() => demo.get(999));
});

test('storage errors report failure rather than claiming a save', () => {
  const localStorage = storage();
  const { demo } = setup(localStorage);
  login(demo, 'teacher');
  demo.list();
  localStorage.setItem = () => { throw Error('QuotaExceededError'); };
  assert.throws(() => demo.create({ building: '1', room: '2', type: 'other', urgency: 'low', description: 'test' }), /บันทึกไม่ได้/);
  assert.equal(demo.list().length, 3);
});

test('corrupted data can be reset by an admin', () => {
  const { demo, localStorage } = setup();
  login(demo, 'admin');
  localStorage.setItem('repair-system-demo-v1', '{bad json');
  assert.throws(() => demo.list(), /อ่านข้อมูลไม่ได้/);
  demo.reset();
  assert.equal(demo.list().length, 3);
});
