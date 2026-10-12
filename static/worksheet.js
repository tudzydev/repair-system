// The Flask deployment serves /worksheet and /login on the same host.
const loginLink = document.getElementById('worksheet-login-link');
const loginHelp = document.getElementById('worksheet-login-help');
if (loginLink && loginHelp) {
  const localPreview = location.protocol === 'file:' ||
    (['localhost', '127.0.0.1', '::1', '[::1]'].includes(location.hostname) && location.port === '5500');
  if (localPreview) {
    loginLink.href = 'http://127.0.0.1:5001/login';
    loginHelp.textContent = 'รัน ./start.command ก่อนเข้าสู่ระบบ';
  } else if (location.hostname.endsWith('.github.io')) {
    loginLink.href = 'pages/login.html';
    loginLink.textContent = 'ดูตัวอย่างหน้าเข้าสู่ระบบ →';
    loginHelp.textContent = 'เว็บใบงานและตัวอย่างบน GitHub Pages · ระบบบันทึกข้อมูลใช้ Flask';
  }
}
