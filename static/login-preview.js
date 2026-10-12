const previewForm = document.getElementById('login-preview-form');
if (previewForm) {
  previewForm.addEventListener('submit', (event) => {
    event.preventDefault();
    const result = document.getElementById('login-preview-result');
    result.textContent = 'กรอกฟอร์มได้แล้ว แต่ยังไม่ได้เข้าสู่ระบบ: เว็บไซต์นี้ยังไม่เชื่อมต่อเซิร์ฟเวอร์ตรวจบัญชีออนไลน์';
    result.hidden = false;
    document.getElementById('password').value = '';
    result.focus();
  });
}
