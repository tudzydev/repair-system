(() => {
  const demo = window.RepairDemo;
  const content = document.getElementById('demo-content');
  const message = document.getElementById('demo-message');
  let pendingMessage = '';
  const esc = value => String(value ?? '').replace(/[&<>"']/g, char => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[char]));
  const statuses = { pending: 'รอรับเรื่อง', accepted: 'มอบหมายแล้ว', in_progress: 'กำลังซ่อม', completed: 'เสร็จสิ้น' };
  const types = { electrical: 'ไฟฟ้า', furniture: 'เฟอร์นิเจอร์', computer: 'คอมพิวเตอร์', aircon: 'เครื่องปรับอากาศ', other: 'อื่น ๆ' };
  const urgency = { low: 'ต่ำ', medium: 'ปานกลาง', high: 'เร่งด่วน' };
  const roles = { teacher: 'ครู / บุคลากร', admin: 'ผู้ดูแลระบบ', technician: 'เจ้าหน้าที่ซ่อม' };
  const options = obj => Object.entries(obj).map(([key, label]) => `<option value="${key}">${label}</option>`).join('');
  const badge = r => `<span class="demo-status ${esc(r.status)}">${esc(statuses[r.status])}</span>`;
  const notify = (text, error = false) => { message.textContent = text; message.hidden = false; message.className = `alert ${error ? 'alert-danger' : 'alert-success'}`; };
  const values = form => Object.fromEntries(new FormData(form));
  const navigate = hash => { if (location.hash === hash) render(); else location.hash = hash; };
  const act = fn => { try { fn(); } catch (error) { notify(error.message, true); } };
  const bindForm = (id, fn) => document.getElementById(id)?.addEventListener('submit', event => { event.preventDefault(); act(() => fn(values(event.currentTarget))); });
  const table = rows => rows.length ? `<div class="card demo-table"><table><thead><tr><th>เลขใบแจ้งซ่อม</th><th>สถานที่ / ปัญหา</th><th>ความเร่งด่วน</th><th>สถานะ</th></tr></thead><tbody>${rows.map(r => `<tr><td><a href="#repair/${r.id}">${esc(r.number)}</a><br><small>${esc(r.created)}</small></td><td>${esc(r.building)} · ${esc(r.room)}<br>${esc(r.description)}</td><td>${esc(urgency[r.urgency])}</td><td>${badge(r)}</td></tr>`).join('')}</tbody></table></div>` : '<div class="card demo-panel">ยังไม่มีรายการที่ตรงกับเงื่อนไข</div>';

  function dashboard(user) {
    const rows = demo.list();
    content.innerHTML = `<div class="demo-heading"><div><p class="eyebrow">ภาพรวมงานซ่อม</p><h1>สวัสดี ${esc(user.fullname)}</h1></div>${user.role === 'teacher' ? '<a class="btn btn-primary" href="#create">＋ แจ้งซ่อมใหม่</a>' : ''}</div><div class="demo-grid">${Object.entries(statuses).map(([key, label]) => `<a class="card demo-stat" href="#repairs?status=${key}"><span>${label}</span><strong>${rows.filter(r => r.status === key).length}</strong></a>`).join('')}</div><div class="demo-heading"><h2>รายการล่าสุด</h2><a href="#repairs">ดูทั้งหมด →</a></div>${table([...rows].reverse().slice(0, 5))}`;
  }
  function repairs(query) {
    const filters = new URLSearchParams(query);
    content.innerHTML = `<div class="demo-heading"><h1>รายการแจ้งซ่อม</h1>${demo.user().role === 'teacher' ? '<a class="btn btn-primary" href="#create">＋ แจ้งซ่อมใหม่</a>' : ''}</div><form id="filters" class="demo-filters"><label class="sr-only" for="search">ค้นหา</label><input class="form-control" id="search" name="search" placeholder="ค้นหาเลขใบแจ้งซ่อม อาคาร หรือรายละเอียด" value="${esc(filters.get('search') || '')}"><label class="sr-only" for="status">สถานะ</label><select id="status" name="status" class="form-select"><option value="">ทุกสถานะ</option>${options(statuses)}</select><button class="btn btn-primary">ค้นหา</button></form><div id="repair-list"></div>`;
    document.getElementById('status').value = filters.get('status') || '';
    const search = (filters.get('search') || '').toLowerCase();
    const rows = demo.list().filter(r => (!filters.get('status') || r.status === filters.get('status')) && `${r.number} ${r.building} ${r.room} ${r.description}`.toLowerCase().includes(search));
    document.getElementById('repair-list').innerHTML = table([...rows].reverse());
    bindForm('filters', data => navigate(`#repairs?${new URLSearchParams(data)}`));
  }
  function create() {
    if (demo.user().role !== 'teacher') throw Error('เฉพาะครูเท่านั้นที่แจ้งซ่อมได้');
    content.innerHTML = `<div class="demo-heading"><h1>แจ้งซ่อมใหม่</h1><a href="#repairs">กลับไปรายการ</a></div><form id="create-form" class="card demo-panel demo-form"><div><label class="form-label" for="building">อาคาร</label><input class="form-control" id="building" name="building" maxlength="100" required placeholder="เช่น อาคาร 1"></div><div><label class="form-label" for="room">ห้อง / บริเวณ</label><input class="form-control" id="room" name="room" maxlength="50" required placeholder="เช่น 101"></div><div><label class="form-label" for="type">ประเภทปัญหา</label><select class="form-select" id="type" name="type">${options(types)}</select></div><div><label class="form-label" for="urgency">ความเร่งด่วน</label><select class="form-select" id="urgency" name="urgency">${options(urgency)}</select></div><div><label class="form-label" for="description">รายละเอียดปัญหา</label><textarea class="form-control" id="description" name="description" rows="4" maxlength="3000" required></textarea></div><button class="btn btn-primary">ส่งใบแจ้งซ่อม →</button></form>`;
    document.getElementById('urgency').value = 'medium';
    bindForm('create-form', data => { const r = demo.create(data); pendingMessage = `สร้างใบแจ้งซ่อม ${r.number} แล้ว`; navigate(`#repair/${r.id}`); });
  }
  function detail(id, user) {
    const r = demo.get(id);
    const field = (label, value) => `<div><strong>${label}</strong><p class="demo-text">${esc(value || '—')}</p></div>`;
    let action = '';
    if (user.role === 'admin' && r.status === 'pending') {
      action = `<form id="assign-form" class="card demo-panel demo-form"><h2>มอบหมายงาน</h2><div><label class="form-label" for="assigned">เจ้าหน้าที่</label><select class="form-select" id="assigned" name="assigned">${demo.users.filter(u => u.role === 'technician').map(u => `<option value="${u.username}">${esc(u.fullname)}</option>`).join('')}</select></div><div><label class="form-label" for="due">กำหนดเสร็จ</label><input class="form-control" id="due" name="due" type="date" min="${demo.today()}" value="${demo.today()}" required></div><button class="btn btn-primary">มอบหมายงาน</button></form>`;
    } else if (user.role === 'technician' && r.status === 'accepted') {
      action = '<section class="card demo-panel"><h2>งานพร้อมดำเนินการ</h2><button class="btn btn-primary" id="start">เริ่มซ่อม →</button></section>';
    } else if (user.role === 'technician' && r.status === 'in_progress') {
      action = '<form id="complete-form" class="card demo-panel demo-form"><h2>บันทึกผลการซ่อม</h2><div><label class="form-label" for="cost">ค่าใช้จ่าย (บาท)</label><input class="form-control" id="cost" name="cost" type="number" min="0" max="9999999999.99" step="0.01" required value="0"></div><div><label class="form-label" for="result">ผลการซ่อม</label><textarea class="form-control" id="result" name="result" rows="3" maxlength="3000" required></textarea></div><button class="btn btn-primary">บันทึกและปิดงาน ✓</button></form>';
    }
    content.innerHTML = `<div class="demo-heading"><div><p class="eyebrow">รายละเอียดใบแจ้งซ่อม</p><h1>${esc(r.number)}</h1></div><a href="#repairs">กลับไปรายการ →</a></div><section class="card demo-panel"><p>${badge(r)}</p><div class="demo-details">${field('สถานที่', `${r.building} · ${r.room}`)}${field('ประเภท', types[r.type])}${field('ความเร่งด่วน', urgency[r.urgency])}${field('ผู้แจ้ง', demo.users.find(u => u.username === r.owner)?.fullname)}${field('วันที่แจ้ง', r.created)}${field('กำหนดเสร็จ', r.due)}${field('เจ้าหน้าที่', demo.users.find(u => u.username === r.assigned)?.fullname)}</div><h2>รายละเอียดปัญหา</h2><p class="demo-text">${esc(r.description)}</p>${r.status === 'completed' ? `<h2>ผลการซ่อม</h2><p class="demo-text">${esc(r.result)}</p><p>ค่าใช้จ่าย ${Number(r.cost).toLocaleString('th-TH')} บาท · เสร็จเมื่อ ${esc(r.completed)}</p>` : ''}<button class="btn btn-outline-secondary" id="print">พิมพ์ใบแจ้งซ่อม</button></section>${action}<section class="card demo-panel"><h2>ความคิดเห็น (${r.comments.length})</h2>${r.comments.map(c => `<div class="demo-comment"><strong>${esc(c.author)}</strong> · ${esc(c.date)}<p class="demo-text">${esc(c.text)}</p></div>`).join('')}<form id="comment-form" class="demo-form"><label class="form-label" for="comment">เพิ่มความคิดเห็น</label><textarea class="form-control" id="comment" name="text" rows="3" maxlength="2000" required></textarea><button class="btn btn-outline-primary">ส่งความคิดเห็น</button></form></section>`;
    const update = (action, data) => { demo.update(id, action, data); render(); notify('บันทึกข้อมูลแล้ว'); };
    bindForm('assign-form', data => update('assign', data));
    bindForm('complete-form', data => update('complete', data));
    bindForm('comment-form', data => update('comment', data));
    document.getElementById('start')?.addEventListener('click', () => act(() => update('start')));
    document.getElementById('print').addEventListener('click', () => window.print());
  }
  function users(user) {
    if (user.role !== 'admin') throw Error('เฉพาะผู้ดูแลระบบ');
    content.innerHTML = `<div class="demo-heading"><h1>บัญชีทดลอง</h1></div><p>สลับบทบาทด้วยการออกจากระบบ แล้วเข้าสู่ระบบด้วยบัญชีด้านล่าง ทุกบัญชีใช้รหัสผ่าน <code>Practice123!</code></p><div class="card demo-table"><table><thead><tr><th>ชื่อผู้ใช้</th><th>ชื่อ</th><th>บทบาท</th></tr></thead><tbody>${demo.users.map(u => `<tr><td>${u.username}</td><td>${esc(u.fullname)}</td><td>${roles[u.role]}</td></tr>`).join('')}</tbody></table></div><section class="card demo-panel"><h2>เริ่มทดลองใหม่</h2><p>ลบใบแจ้งซ่อมและความคิดเห็นจำลองที่เพิ่มในเบราว์เซอร์นี้ แล้วคืนข้อมูลตัวอย่าง</p><button class="btn btn-outline-secondary" id="reset">รีเซ็ตข้อมูลจำลอง</button></section>`;
    document.getElementById('reset').addEventListener('click', () => {
      if (window.confirm('ลบข้อมูลจำลองในเบราว์เซอร์นี้และคืนข้อมูลตัวอย่าง?')) act(() => { demo.reset(); render(); notify('คืนข้อมูลตัวอย่างแล้ว'); });
    });
  }
  function render() {
    message.hidden = true;
    const user = demo.user();
    if (!user) { location.replace('login.html'); return; }
    document.getElementById('demo-account').innerHTML = `<span><strong>${esc(user.fullname)}</strong><small>${roles[user.role]}</small></span><button id="logout" class="btn btn-outline-secondary btn-sm">ออกจากระบบ</button>`;
    document.getElementById('logout').addEventListener('click', () => { demo.logout(); location.replace('login.html'); });
    const [path, query] = (location.hash.slice(1) || 'dashboard').split('?');
    const nav = [['dashboard', 'ภาพรวม'], ['repairs', 'รายการแจ้งซ่อม'], ...(user.role === 'teacher' ? [['create', '＋ แจ้งซ่อมใหม่']] : []), ...(user.role === 'admin' ? [['users', 'บัญชีทดลอง']] : [])];
    document.getElementById('demo-nav').innerHTML = nav.map(([key, label]) => `<a href="#${key}" ${path === key || (key === 'repairs' && path.startsWith('repair/')) ? 'aria-current="page"' : ''}>${label}</a>`).join('');
    try {
      if (path === 'dashboard') dashboard(user);
      else if (path === 'repairs') repairs(query);
      else if (path === 'create') create();
      else if (path === 'users') users(user);
      else if (/^repair\/\d+$/.test(path)) detail(path.split('/')[1], user);
      else throw Error('ไม่พบหน้าที่ต้องการ');
      if (pendingMessage) { notify(pendingMessage); pendingMessage = ''; }
    } catch (error) {
      content.innerHTML = '<h1>เปิดหน้านี้ไม่ได้</h1><a href="#dashboard">กลับไปภาพรวม</a>';
      if (user.role === 'admin') {
        content.innerHTML += '<p>หากข้อมูลจำลองเสียหาย สามารถคืนข้อมูลตัวอย่างได้</p><button id="recover" class="btn btn-outline-secondary">คืนข้อมูลตัวอย่าง</button>';
        document.getElementById('recover').addEventListener('click', () => { if (window.confirm('คืนข้อมูลจำลองเริ่มต้น?')) act(() => { demo.reset(); navigate('#dashboard'); }); });
      }
      notify(error.message, true);
    }
  }
  window.addEventListener('hashchange', () => { render(); content.focus(); });
  window.addEventListener('storage', render);
  render();
})();
