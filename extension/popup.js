const API = 'http://localhost:8000/api';
function showView(id) {
  document.querySelectorAll('.view').forEach(v => v.style.display = 'none');
  document.getElementById(id).style.display = 'block';
}
function showError(elId, msg) {
  const el = document.getElementById(elId);
  el.textContent = msg;
  el.style.display = 'block';
}
function hideError(elId) {
  document.getElementById(elId).style.display = 'none';
}
async function apiPost(path, body) {
  const res = await fetch(API + path, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
  });
  const data = await res.json();
  if (!res.ok) throw new Error(data.detail || 'Server error');
  return data;
}
function saveAuth(token, email) {
  chrome.storage.local.set({ pw_token: token, pw_email: email });
}
function clearAuth() {
  chrome.storage.local.remove(['pw_token', 'pw_email']);
}
chrome.storage.local.get(['pw_token', 'pw_email'], ({ pw_token, pw_email }) => {
  if (pw_token && pw_email) {
    document.getElementById('loggedin-email').textContent = pw_email;
    showView('view-loggedin');
  } else {
    showView('view-login');
  }
});
document.getElementById('btn-login').addEventListener('click', async () => {
  const email = document.getElementById('login-email').value.trim();
  const password = document.getElementById('login-password').value;
  hideError('login-error');
  const btn = document.getElementById('btn-login');
  btn.disabled = true;
  btn.textContent = 'Signing in…';
  try {
    const data = await apiPost('/auth/login', { email, password });
    saveAuth(data.access_token, data.email);
    document.getElementById('loggedin-email').textContent = data.email;
    showView('view-loggedin');
  } catch (e) {
    showError('login-error', e.message);
  } finally {
    btn.disabled = false;
    btn.textContent = 'Log In';
  }
});
document.getElementById('btn-register').addEventListener('click', async () => {
  const email = document.getElementById('reg-email').value.trim();
  const password = document.getElementById('reg-password').value;
  hideError('register-error');
  const btn = document.getElementById('btn-register');
  btn.disabled = true;
  btn.textContent = 'Creating account…';
  try {
    const data = await apiPost('/auth/register', { email, password });
    saveAuth(data.access_token, data.email);
    document.getElementById('loggedin-email').textContent = data.email;
    showView('view-loggedin');
  } catch (e) {
    showError('register-error', e.message);
  } finally {
    btn.disabled = false;
    btn.textContent = 'Create Account';
  }
});
document.getElementById('btn-logout').addEventListener('click', () => {
  clearAuth();
  document.getElementById('login-email').value = '';
  document.getElementById('login-password').value = '';
  showView('view-login');
});
document.getElementById('go-register').addEventListener('click', e => {
  e.preventDefault();
  hideError('login-error');
  showView('view-register');
});
document.getElementById('go-login').addEventListener('click', e => {
  e.preventDefault();
  hideError('register-error');
  showView('view-login');
});