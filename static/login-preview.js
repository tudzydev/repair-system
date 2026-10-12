const previewForm = document.getElementById('login-preview-form');
if (previewForm) {
  previewForm.addEventListener('submit', event => {
    event.preventDefault();
    const result = document.getElementById('login-preview-result');
    const password = document.getElementById('password');
    try {
      window.RepairDemo.login(document.getElementById('username').value, password.value);
      password.value = '';
      const path = location.pathname;
      location.href = path.endsWith('/login/') || path.endsWith('/login/index.html') ? '../pages/mock.html' : 'mock.html';
    } catch (error) {
      result.textContent = error.message;
      result.className = 'alert alert-danger mt-3';
      result.hidden = false;
      result.focus();
      password.value = '';
    }
  });
}
