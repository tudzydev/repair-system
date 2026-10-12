/* Browser-only demonstration data. These accounts are public sample accounts. */
(() => {
  const key = 'repair-system-demo-v1';
  const sessionKey = 'repair-system-demo-user';
  const users = [
    { username: 'teacher', fullname: 'ครูสมใจ', role: 'teacher' },
    { username: 'admin', fullname: 'ผู้ดูแลระบบ', role: 'admin' },
    { username: 'technician', fullname: 'ช่างสมชาย', role: 'technician' },
  ];
  const today = () => {
    const now = new Date();
    return `${now.getFullYear()}-${String(now.getMonth() + 1).padStart(2, '0')}-${String(now.getDate()).padStart(2, '0')}`;
  };
  const seed = () => [
    { id: 1, number: 'DEMO-001', owner: 'teacher', building: 'อาคาร 1', room: '101', type: 'aircon', description: 'แอร์ไม่เย็น มีเสียงดังขณะเปิดใช้งาน', urgency: 'high', status: 'pending', assigned: '', due: '', created: today(), comments: [] },
    { id: 2, number: 'DEMO-002', owner: 'teacher', building: 'อาคาร 2', room: 'ห้องคอมพิวเตอร์', type: 'computer', description: 'คอมพิวเตอร์เครื่องที่ 5 เปิดไม่ติด', urgency: 'medium', status: 'accepted', assigned: 'technician', due: today(), created: today(), comments: [] },
    { id: 3, number: 'DEMO-003', owner: 'teacher', building: 'อาคาร 3', room: '302', type: 'electrical', description: 'หลอดไฟหน้าห้องดับ', urgency: 'low', status: 'completed', assigned: 'technician', due: today(), created: today(), completed: today(), cost: 180, result: 'เปลี่ยนหลอดไฟและตรวจสอบการทำงานเรียบร้อย', comments: [] },
  ];
  const read = () => {
    try {
      const raw = localStorage.getItem(key);
      if (!raw) { const data = seed(); localStorage.setItem(key, JSON.stringify(data)); return data; }
      const data = JSON.parse(raw);
      if (!Array.isArray(data) || data.some(r => !Number.isInteger(r.id) || !Array.isArray(r.comments))) throw Error();
      return data;
    } catch { throw Error('อ่านข้อมูลไม่ได้ กรุณาอนุญาตการเก็บข้อมูลในเบราว์เซอร์ หรือรีเซ็ตข้อมูลจำลอง'); }
  };
  const save = data => {
    try { localStorage.setItem(key, JSON.stringify(data)); }
    catch { throw Error('บันทึกไม่ได้ พื้นที่เบราว์เซอร์เต็มหรือไม่อนุญาตให้เก็บข้อมูล'); }
  };
  const user = () => {
    try { return users.find(u => u.username === sessionStorage.getItem(sessionKey)); }
    catch { return undefined; }
  };
  const allowed = (u, r) => u && (u.role === 'admin' || (u.role === 'teacher' ? r.owner === u.username : r.assigned === u.username));
  const required = () => { const u = user(); if (!u) throw Error('กรุณาเข้าสู่ระบบ'); return u; };
  window.RepairDemo = {
    users, today,
    login(username, password) {
      const u = users.find(item => item.username === username.trim());
      if (!u || password !== 'Practice123!') throw Error('ชื่อผู้ใช้หรือรหัสผ่านไม่ถูกต้อง');
      sessionStorage.setItem(sessionKey, u.username);
      return u;
    },
    user,
    logout() { sessionStorage.removeItem(sessionKey); },
    list() { const u = required(); return read().filter(r => allowed(u, r)); },
    get(id) { const r = read().find(r => r.id === Number(id)); if (!r || !allowed(required(), r)) throw Error('ไม่พบงานหรือไม่มีสิทธิ์ดูงานนี้'); return r; },
    create(values) {
      const u = required();
      if (u.role !== 'teacher') throw Error('เฉพาะครูเท่านั้นที่แจ้งซ่อมได้');
      for (const field of ['building', 'room', 'description']) if (!values[field]?.trim()) throw Error('กรุณากรอกข้อมูลให้ครบ');
      if (!['electrical', 'furniture', 'computer', 'aircon', 'other'].includes(values.type) || !['low', 'medium', 'high'].includes(values.urgency)) throw Error('ประเภทหรือความเร่งด่วนไม่ถูกต้อง');
      const data = read();
      const id = Math.max(0, ...data.map(r => r.id)) + 1;
      const r = { id, number: `DEMO-${String(id).padStart(3, '0')}`, owner: u.username, building: values.building.trim(), room: values.room.trim(), description: values.description.trim(), type: values.type, urgency: values.urgency, status: 'pending', assigned: '', due: '', created: today(), comments: [] };
      data.push(r); save(data); return r;
    },
    update(id, action, values = {}) {
      const u = required();
      const data = read();
      const r = data.find(item => item.id === Number(id));
      if (!r || !allowed(u, r)) throw Error('ไม่พบงานหรือไม่มีสิทธิ์');
      if (action === 'assign') {
        if (u.role !== 'admin' || r.status !== 'pending') throw Error('ไม่สามารถมอบหมายงานนี้ได้');
        if (!users.some(t => t.role === 'technician' && t.username === values.assigned) || !/^\d{4}-\d{2}-\d{2}$/.test(values.due) || values.due < today()) throw Error('เลือกช่างและวันกำหนดเสร็จตั้งแต่วันนี้');
        r.assigned = values.assigned; r.due = values.due; r.status = 'accepted';
      } else if (action === 'start') {
        if (u.role !== 'technician' || r.assigned !== u.username || r.status !== 'accepted') throw Error('ไม่สามารถเริ่มงานนี้ได้');
        r.status = 'in_progress';
      } else if (action === 'complete') {
        if (u.role !== 'technician' || r.assigned !== u.username || r.status !== 'in_progress') throw Error('ไม่สามารถปิดงานนี้ได้');
        const cost = Number(values.cost);
        if (values.cost === '' || !Number.isFinite(cost) || cost < 0 || cost > 9999999999.99 || !values.result?.trim()) throw Error('กรอกค่าใช้จ่ายและผลการซ่อมให้ถูกต้อง');
        r.cost = cost; r.result = values.result.trim(); r.completed = today(); r.status = 'completed';
      } else if (action === 'comment') {
        if (!values.text?.trim()) throw Error('กรุณากรอกความคิดเห็น');
        r.comments.push({ author: u.fullname, text: values.text.trim(), date: today() });
      } else throw Error('คำสั่งไม่ถูกต้อง');
      save(data); return r;
    },
    reset() { if (required().role !== 'admin') throw Error('เฉพาะผู้ดูแลเท่านั้นที่รีเซ็ตข้อมูลได้'); save(seed()); },
  };
})();
