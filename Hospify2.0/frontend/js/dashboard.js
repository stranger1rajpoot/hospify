/**
 * Hospify - Shared Dashboard JS
 * Handles auth, sidebar, API calls, toasts, and utilities
 */

const API_BASE = (typeof HOSPIFY_CONFIG !== 'undefined') ? HOSPIFY_CONFIG.API_BASE_URL : 'http://localhost:5000/api';

// ── AUTH ──────────────────────────────────────────
const Auth = {
  getToken: () => localStorage.getItem('access_token') || sessionStorage.getItem('access_token'),
  getUser: () => {
    try {
      return JSON.parse(localStorage.getItem('user') || sessionStorage.getItem('user') || 'null');
    } catch { return null; }
  },
  logout: () => {
    localStorage.clear(); sessionStorage.clear();
    window.location.href = '../../login.html';
  },
  require: () => {
    const token = Auth.getToken();
    const user = Auth.getUser();
    if (!token || !user) { window.location.href = '../../login.html'; return null; }
    return user;
  }
};

// ── API ───────────────────────────────────────────
const API = {
  async request(method, endpoint, body = null) {
    const token = Auth.getToken();
    const opts = {
      method,
      headers: { 'Content-Type': 'application/json', ...(token ? { Authorization: `Bearer ${token}` } : {}) }
    };
    if (body) opts.body = JSON.stringify(body);
    try {
      const res = await fetch(`${API_BASE}${endpoint}`, opts);
      if (res.status === 401) { Auth.logout(); return null; }
      return await res.json();
    } catch {
      return null;
    }
  },
  get: (endpoint) => API.request('GET', endpoint),
  post: (endpoint, body) => API.request('POST', endpoint, body),
  put: (endpoint, body) => API.request('PUT', endpoint, body),
  delete: (endpoint) => API.request('DELETE', endpoint),
};

// ── TOAST ─────────────────────────────────────────
const Toast = {
  container: null,
  init() {
    this.container = document.getElementById('toastContainer');
    if (!this.container) {
      this.container = document.createElement('div');
      this.container.id = 'toastContainer';
      this.container.className = 'toast-container';
      document.body.appendChild(this.container);
    }
  },
  show(message, type = 'info', duration = 3500) {
    if (!this.container) this.init();
    const icons = { success: 'fa-circle-check', error: 'fa-circle-xmark', warning: 'fa-triangle-exclamation', info: 'fa-circle-info' };
    const toast = document.createElement('div');
    toast.className = `toast ${type}`;
    toast.innerHTML = `<i class="fas ${icons[type] || icons.info}"></i><span>${message}</span>`;
    this.container.appendChild(toast);
    setTimeout(() => { toast.style.animation = 'fadeOut .3s forwards'; setTimeout(() => toast.remove(), 300); }, duration);
  },
  success: (msg) => Toast.show(msg, 'success'),
  error: (msg) => Toast.show(msg, 'error'),
  warning: (msg) => Toast.show(msg, 'warning'),
  info: (msg) => Toast.show(msg, 'info'),
};

// ── SIDEBAR ───────────────────────────────────────
const Sidebar = {
  collapsed: false,
  init() {
    this.collapsed = localStorage.getItem('sidebarCollapsed') === 'true';
    if (this.collapsed) this.applyCollapsed();
    this.setActive();
  },
  toggle() {
    this.collapsed = !this.collapsed;
    localStorage.setItem('sidebarCollapsed', this.collapsed);
    this.applyCollapsed();
  },
  applyCollapsed() {
    const sidebar = document.getElementById('sidebar');
    const mainContent = document.getElementById('mainContent');
    const header = document.getElementById('header');
    if (sidebar) sidebar.classList.toggle('collapsed', this.collapsed);
    if (mainContent) mainContent.classList.toggle('sidebar-collapsed', this.collapsed);
    if (header) header.classList.toggle('sidebar-collapsed', this.collapsed);
  },
  setActive() {
    const current = window.location.pathname;
    document.querySelectorAll('.nav-item[data-page]').forEach(item => {
      item.classList.toggle('active', item.dataset.page && current.includes(item.dataset.page));
    });
  },
  mobilToggle() {
    const sidebar = document.getElementById('sidebar');
    if (sidebar) sidebar.classList.toggle('mobile-open');
  }
};

// ── DARK MODE ─────────────────────────────────────
const Theme = {
  init() {
    const dark = localStorage.getItem('darkMode') === 'true';
    if (dark) document.documentElement.setAttribute('data-theme', 'dark');
    const btn = document.getElementById('themeToggle');
    if (btn) btn.innerHTML = dark ? '<i class="fas fa-sun"></i>' : '<i class="fas fa-moon"></i>';
  },
  toggle() {
    const isDark = document.documentElement.getAttribute('data-theme') === 'dark';
    if (isDark) {
      document.documentElement.removeAttribute('data-theme');
      localStorage.setItem('darkMode', 'false');
    } else {
      document.documentElement.setAttribute('data-theme', 'dark');
      localStorage.setItem('darkMode', 'true');
    }
    const btn = document.getElementById('themeToggle');
    if (btn) btn.innerHTML = !isDark ? '<i class="fas fa-sun"></i>' : '<i class="fas fa-moon"></i>';
  }
};

// ── USER RENDER ───────────────────────────────────
function renderUserInfo() {
  const user = Auth.getUser();
  if (!user) return;

  const nameEl = document.getElementById('userFullName');
  const roleEl = document.getElementById('userRole');
  const avatarEls = document.querySelectorAll('.user-initials');
  const headerNameEl = document.getElementById('headerName');
  const headerRoleEl = document.getElementById('headerRole');

  const initials = `${(user.first_name || '')[0] || ''}${(user.last_name || '')[0] || ''}`.toUpperCase();

  if (nameEl) nameEl.textContent = `${user.first_name} ${user.last_name}`;
  if (roleEl) roleEl.textContent = user.role_display || user.role;
  if (headerNameEl) headerNameEl.textContent = `${user.first_name} ${user.last_name}`;
  if (headerRoleEl) headerRoleEl.textContent = user.role_display || user.role;
  avatarEls.forEach(el => el.textContent = initials);
}

// ── FORMAT ────────────────────────────────────────
const Format = {
  currency: (amount, currency = 'PKR') => `${currency} ${Number(amount || 0).toLocaleString('en-PK', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`,
  date: (dateStr) => {
    if (!dateStr) return '—';
    return new Date(dateStr).toLocaleDateString('en-PK', { day: '2-digit', month: 'short', year: 'numeric' });
  },
  time: (timeStr) => {
    if (!timeStr) return '—';
    const [h, m] = timeStr.split(':');
    const hour = parseInt(h);
    return `${hour > 12 ? hour - 12 : hour || 12}:${m} ${hour >= 12 ? 'PM' : 'AM'}`;
  },
  datetime: (str) => {
    if (!str) return '—';
    return new Date(str).toLocaleString('en-PK', { day: '2-digit', month: 'short', year: 'numeric', hour: '2-digit', minute: '2-digit' });
  },
  number: (n) => Number(n || 0).toLocaleString('en-PK'),
  badge: (status) => {
    const map = {
      active: 'success', inactive: 'gray', scheduled: 'primary', confirmed: 'info',
      completed: 'success', cancelled: 'danger', in_progress: 'warning', no_show: 'gray',
      paid: 'success', pending: 'warning', partial: 'info', overdue: 'danger',
      available: 'success', out_of_stock: 'danger', expired: 'gray', normal: 'success',
      abnormal: 'warning', critical: 'danger', requested: 'primary',
    };
    const cls = map[status] || 'gray';
    return `<span class="badge badge-${cls}">${status?.replace(/_/g, ' ') || '—'}</span>`;
  }
};

// ── MODAL ─────────────────────────────────────────
const Modal = {
  open: (id) => {
    const overlay = document.getElementById(id);
    if (overlay) overlay.classList.add('active');
  },
  close: (id) => {
    const overlay = document.getElementById(id);
    if (overlay) overlay.classList.remove('active');
  },
  closeAll: () => {
    document.querySelectorAll('.modal-overlay.active').forEach(m => m.classList.remove('active'));
  }
};

// Close modal on overlay click
document.addEventListener('click', (e) => {
  if (e.target.classList.contains('modal-overlay')) Modal.closeAll();
});

// ── PAGINATION ────────────────────────────────────
function renderPagination(containerId, total, pages, currentPage, onPageChange) {
  const container = document.getElementById(containerId);
  if (!container) return;
  if (pages <= 1) { container.innerHTML = ''; return; }

  let html = `<div style="display:flex;align-items:center;gap:8px;justify-content:flex-end;padding:16px 22px;border-top:1px solid var(--light-3)">
    <span style="font-size:.82rem;color:var(--text-muted)">${total} total</span>
    <div style="display:flex;gap:6px;margin-left:auto">`;

  for (let i = 1; i <= pages; i++) {
    if (pages > 7 && Math.abs(i - currentPage) > 2 && i !== 1 && i !== pages) {
      if (Math.abs(i - currentPage) === 3) html += `<span style="padding:6px 4px;color:var(--text-muted)">...</span>`;
      continue;
    }
    html += `<button onclick="${onPageChange}(${i})" style="width:32px;height:32px;border-radius:8px;border:1.5px solid ${i === currentPage ? 'var(--primary)' : 'var(--light-3)'};background:${i === currentPage ? 'var(--primary)' : 'transparent'};color:${i === currentPage ? '#fff' : 'var(--text-muted)'};font-size:.82rem;font-weight:600;cursor:pointer">${i}</button>`;
  }

  html += `</div></div>`;
  container.innerHTML = html;
}

// ── SEARCH DEBOUNCE ───────────────────────────────
function debounce(fn, delay = 400) {
  let timer;
  return (...args) => { clearTimeout(timer); timer = setTimeout(() => fn(...args), delay); };
}

// ── CONFIRM DIALOG ────────────────────────────────
function confirmAction(message, onConfirm) {
  if (confirm(message)) onConfirm();
}

// ── LOADING STATE ─────────────────────────────────
function setTableLoading(tbodyId, cols = 5) {
  const tbody = document.getElementById(tbodyId);
  if (!tbody) return;
  tbody.innerHTML = `<tr><td colspan="${cols}" style="text-align:center;padding:48px">
    <div class="spinner"></div>
    <p style="margin-top:12px;color:var(--text-muted);font-size:.875rem">Loading...</p>
  </td></tr>`;
}

function setTableEmpty(tbodyId, message = 'No records found', cols = 5) {
  const tbody = document.getElementById(tbodyId);
  if (!tbody) return;
  tbody.innerHTML = `<tr><td colspan="${cols}">
    <div class="empty-state">
      <i class="fas fa-inbox"></i>
      <h3>${message}</h3>
      <p>No data available yet.</p>
    </div>
  </td></tr>`;
}

// ── INIT ──────────────────────────────────────────
document.addEventListener('DOMContentLoaded', () => {
  Toast.init();
  Theme.init();
  Sidebar.init();
  renderUserInfo();
});
