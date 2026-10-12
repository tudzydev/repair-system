// Optional enhancements; all forms work without JavaScript.
const loginForm = document.getElementById('login-form');
if (loginForm) {
  const csrfInput = loginForm.querySelector('[name="csrf_token"]');
  if (csrfInput && csrfInput.value.includes('{{')) {
    document.getElementById('login-preview-note').hidden = false;
    document.getElementById('login-submit').disabled = true;
    loginForm.addEventListener('submit', (event) => event.preventDefault());
  }
}
document.querySelectorAll('.password-toggle').forEach((button) => {
  const input = document.getElementById(button.getAttribute('aria-controls'));
  if (!input) return;
  button.hidden = false;
  button.addEventListener('click', () => {
    const show = input.type === 'password';
    input.type = show ? 'text' : 'password';
    button.textContent = show ? 'ซ่อน' : 'แสดง';
    button.setAttribute('aria-pressed', String(show));
  });
});
const imageInput = document.querySelector('[data-image-preview]');
if (imageInput) {
  const preview = document.getElementById('image-preview');
  const feedback = document.getElementById('image-feedback');
  let previewUrl;
  imageInput.addEventListener('change', () => {
    if (previewUrl) URL.revokeObjectURL(previewUrl);
    preview.hidden = true;
    preview.removeAttribute('src');
    imageInput.setCustomValidity('');
    feedback.textContent = '';
    const file = imageInput.files[0];
    if (!file) return;
    if (file.size > 5 * 1024 * 1024) {
      const message = 'ภาพมีขนาดเกิน 5 MB กรุณาเลือกภาพที่เล็กลง';
      imageInput.setCustomValidity(message);
      feedback.textContent = message;
      return;
    }
    if (['image/jpeg', 'image/png', 'image/gif'].includes(file.type)) {
      previewUrl = URL.createObjectURL(file);
      preview.src = previewUrl;
      preview.hidden = false;
    }
  });
}
