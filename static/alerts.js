// Flask flash → SweetAlert2; อ่าน JSON แทนการต่อข้อความเข้า JavaScript
(async function () {
  const element = document.getElementById('notifications');
  if (!element || typeof Swal === 'undefined') return;
  const messages = JSON.parse(element.dataset.messages);
  element.hidden = true;
  for (const [category, message] of messages) {
    const icon = ['success', 'error', 'warning', 'info', 'question'].includes(category) ? category : 'info';
    await Swal.fire({ title: icon === 'success' ? 'สำเร็จ' : 'แจ้งเตือน', text: message, icon, confirmButtonText: 'ตกลง' });
  }
})();
