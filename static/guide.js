document.querySelectorAll('.guide-content table').forEach((table) => {
  const wrapper = document.createElement('div');
  wrapper.className = 'table-scroll';
  wrapper.tabIndex = 0;
  wrapper.setAttribute('role', 'region');
  wrapper.setAttribute('aria-label', 'ตารางคู่มือ เลื่อนเพื่ออ่านคอลัมน์เพิ่มเติม');
  table.before(wrapper);
  wrapper.append(table);
});

if (navigator.clipboard && window.isSecureContext) {
  document.querySelectorAll('.guide-content pre').forEach((pre) => {
    const wrapper = document.createElement('div');
    wrapper.className = 'code-block';
    pre.before(wrapper);
    wrapper.append(pre);
    const button = document.createElement('button');
    button.type = 'button';
    button.className = 'copy-button';
    button.textContent = 'คัดลอก';
    button.setAttribute('aria-label', 'คัดลอกโค้ดในบล็อกนี้');
    wrapper.append(button);
    button.addEventListener('click', async () => {
      const status = document.getElementById('copy-status');
      try {
        await navigator.clipboard.writeText(pre.textContent);
        button.textContent = 'คัดลอกแล้ว ✓';
        status.textContent = 'คัดลอกโค้ดแล้ว';
        setTimeout(() => { button.textContent = 'คัดลอก'; }, 2000);
      } catch {
        status.textContent = 'คัดลอกไม่ได้ กรุณาเลือกข้อความแล้วคัดลอกด้วยตนเอง';
      }
    });
  });
}
