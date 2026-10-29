/* ═══════════════════════════════════════════════════
   PeopleDesk — Application JavaScript
   ═══════════════════════════════════════════════════ */

'use strict';

// ── State ──────────────────────────────────────────
let currentView      = 'chat';
let editingId        = null;
let deletingId       = null;
let heroVisible      = true;
let allEmployees     = [];
let toastTimer       = null;

// ── Init ───────────────────────────────────────────
document.addEventListener('DOMContentLoaded', () => {
  refreshGlobalStats();
  switchView('chat');
});

// ── View switching ─────────────────────────────────
function switchView(view) {
  currentView = view;

  document.querySelectorAll('.view').forEach(v => v.classList.add('hidden'));
  document.getElementById(`view-${view}`).classList.remove('hidden');

  document.querySelectorAll('.nav-item').forEach(n => {
    n.classList.toggle('active', n.dataset.view === view);
  });

  const titles = { chat: 'Employee Assistant', directory: 'Directory', analytics: 'Analytics' };
  document.getElementById('topbarTitle').textContent = titles[view] || 'PeopleDesk';

  if (view === 'directory')  loadDirectory();
  if (view === 'analytics')  loadAnalytics();
}

function toggleSidebar() {
  const sb = document.getElementById('sidebar');
  sb.classList.toggle('open');
}

document.getElementById('sidebarToggle').addEventListener('click', () => {
  document.getElementById('sidebar').classList.remove('open');
});

// ── Global stats (topbar badge) ────────────────────
async function refreshGlobalStats() {
  try {
    const r = await fetch('/api/stats');
    const s = await r.json();
    document.getElementById('empCount').textContent =
      `${s.total} employee${s.total !== 1 ? 's' : ''}`;
  } catch {}
}

// ═══════════════════════════════════════════════════
//  CHAT
// ═══════════════════════════════════════════════════

function sendSuggestion(text) {
  document.getElementById('chatInput').value = text;
  sendMessage();
}

async function sendMessage() {
  const input  = document.getElementById('chatInput');
  const text   = input.value.trim();
  if (!text) return;

  input.value = '';
  hideHero();

  appendUserMessage(text);
  const typingId = appendTyping();

  document.getElementById('sendBtn').disabled = true;

  try {
    const resp = await fetch('/api/chat', {
      method:  'POST',
      headers: { 'Content-Type': 'application/json' },
      body:    JSON.stringify({ message: text }),
    });
    const data = await resp.json();
    removeTyping(typingId);
    appendBotReply(data);
  } catch {
    removeTyping(typingId);
    appendBotReply({ type: 'text', message: '⚠️ Connection error. Is the server running?' });
  } finally {
    document.getElementById('sendBtn').disabled = false;
    input.focus();
  }
}

function hideHero() {
  if (!heroVisible) return;
  heroVisible = false;
  const hero = document.getElementById('chatHero');
  if (hero) {
    hero.style.transition = 'opacity 0.3s, max-height 0.4s';
    hero.style.overflow   = 'hidden';
    hero.style.opacity    = '0';
    hero.style.maxHeight  = '0';
    hero.style.padding    = '0';
    setTimeout(() => hero.remove(), 420);
  }
}

function appendUserMessage(text) {
  const msgs = document.getElementById('chatMessages');
  msgs.insertAdjacentHTML('beforeend', `
    <div class="msg-row user">
      <div class="msg-avatar user-av">${getInitials('You')}</div>
      <div class="msg-bubble">${escHtml(text)}</div>
    </div>
  `);
  msgs.scrollTop = msgs.scrollHeight;
}

function appendTyping() {
  const id   = `typing-${Date.now()}`;
  const msgs = document.getElementById('chatMessages');
  msgs.insertAdjacentHTML('beforeend', `
    <div class="msg-row typing-indicator" id="${id}">
      <div class="msg-avatar bot">AI</div>
      <div class="msg-bubble">
        <div class="dot"></div><div class="dot"></div><div class="dot"></div>
      </div>
    </div>
  `);
  msgs.scrollTop = msgs.scrollHeight;
  return id;
}

function removeTyping(id) {
  document.getElementById(id)?.remove();
}

function appendBotReply(data) {
  const msgs    = document.getElementById('chatMessages');
  let   content = '';

  const md = renderMarkdown(data.message || '');

  if (data.type === 'employee_list' && data.employees?.length) {
    const cards = data.employees.map(e => empChatCard(e)).join('');
    content = `${md}<div class="chat-emp-list">${cards}</div>`;
  } else if (data.type === 'payroll' && data.stats) {
    const s   = data.stats;
    const fmt = n => `₹${Number(n).toLocaleString('en-IN', { maximumFractionDigits: 0 })}`;
    content = `
      ${md}
      <div class="payroll-card">
        <div class="payroll-stat">
          <div class="payroll-stat-label">Total Employees</div>
          <div class="payroll-stat-value" style="color:var(--clr-accent-2)">${s.total_employees}</div>
        </div>
        <div class="payroll-stat">
          <div class="payroll-stat-label">Total Payroll</div>
          <div class="payroll-stat-value" style="color:var(--clr-green)">${fmt(s.total_payroll)}</div>
        </div>
        <div class="payroll-stat">
          <div class="payroll-stat-label">Average Salary</div>
          <div class="payroll-stat-value" style="color:var(--clr-amber)">${fmt(s.average_salary)}</div>
        </div>
        <div class="payroll-stat">
          <div class="payroll-stat-label">Top Earner</div>
          <div class="payroll-stat-value" style="color:var(--clr-blue);font-size:0.9rem">${s.highest_paid.name}</div>
        </div>
      </div>
    `;
  } else {
    content = md;
  }

  msgs.insertAdjacentHTML('beforeend', `
    <div class="msg-row">
      <div class="msg-avatar bot">AI</div>
      <div class="msg-bubble">${content}</div>
    </div>
  `);
  msgs.scrollTop = msgs.scrollHeight;
}

function empChatCard(e) {
  const fmt = n => `₹${Number(n).toLocaleString('en-IN', { maximumFractionDigits: 0 })}`;
  return `
    <div class="chat-emp-card">
      <div class="chat-emp-avatar">${getInitials(e.name)}</div>
      <div class="chat-emp-info">
        <div class="chat-emp-name">${escHtml(e.name)}</div>
        <div class="chat-emp-role">${escHtml(e.position)} · ID #${e.id}</div>
      </div>
      <div class="chat-emp-salary">${fmt(e.salary)}</div>
    </div>
  `;
}

// ═══════════════════════════════════════════════════
//  DIRECTORY
// ═══════════════════════════════════════════════════

async function loadDirectory() {
  const grid = document.getElementById('employeeGrid');
  grid.innerHTML = '<div class="loading-state"><div class="spinner"></div><span>Loading employees…</span></div>';

  try {
    const r = await fetch('/api/employees');
    allEmployees = await r.json();
    renderDirectory(allEmployees);
  } catch {
    grid.innerHTML = '<div class="empty-state"><p>Failed to load employees.</p></div>';
  }
}

function renderDirectory(employees) {
  const grid = document.getElementById('employeeGrid');
  if (!employees.length) {
    grid.innerHTML = `
      <div class="empty-state">
        <svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"><path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"/><circle cx="9" cy="7" r="4"/></svg>
        <p>No employees found. Add your first team member!</p>
      </div>`;
    return;
  }

  grid.innerHTML = employees.map(e => empCard(e)).join('');
}

function empCard(e) {
  const fmt = n => `₹${Number(n).toLocaleString('en-IN', { maximumFractionDigits: 0 })}`;
  return `
    <div class="emp-card" id="card-${e.id}">
      <div class="emp-card-top">
        <div class="emp-avatar">${getInitials(e.name)}</div>
        <div class="emp-info">
          <div class="emp-name">${escHtml(e.name)}</div>
          <div class="emp-id">ID #${e.id}</div>
        </div>
      </div>
      <div class="emp-badge">${escHtml(e.position)}</div>
      <div>
        <div class="emp-salary">${fmt(e.salary)}</div>
        <div class="emp-salary-label">Annual Salary</div>
      </div>
      <div class="emp-actions">
        <button class="emp-btn" onclick="openEditModal(${e.id})">
          <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7"/><path d="M18.5 2.5a2.121 2.121 0 0 1 3 3L12 15l-4 1 1-4 9.5-9.5z"/></svg>
          Edit
        </button>
        <button class="emp-btn del" onclick="openDeleteModal(${e.id}, '${escHtml(e.name)}')">
          <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polyline points="3 6 5 6 21 6"/><path d="M19 6l-1 14a2 2 0 0 1-2 2H8a2 2 0 0 1-2-2L5 6"/><path d="M10 11v6"/><path d="M14 11v6"/><path d="M9 6V4a1 1 0 0 1 1-1h4a1 1 0 0 1 1 1v2"/></svg>
          Delete
        </button>
      </div>
    </div>
  `;
}

function filterDirectory() {
  const q = document.getElementById('dirSearch').value.toLowerCase();
  const filtered = allEmployees.filter(e =>
    e.name.toLowerCase().includes(q) ||
    e.position.toLowerCase().includes(q) ||
    String(e.id).includes(q)
  );
  renderDirectory(filtered);
}

// ── Add employee ────────────────────────────────────
function openAddModal() {
  editingId = null;
  document.getElementById('modalTitle').textContent     = 'Add Employee';
  document.getElementById('formSubmitBtn').textContent  = 'Add Employee';
  document.getElementById('fId').disabled               = false;
  document.getElementById('employeeForm').reset();
  document.getElementById('employeeModal').classList.remove('hidden');
}

// ── Edit employee ───────────────────────────────────
function openEditModal(id) {
  const emp = allEmployees.find(e => e.id === id);
  if (!emp) return;

  editingId = id;
  document.getElementById('modalTitle').textContent    = 'Edit Employee';
  document.getElementById('formSubmitBtn').textContent = 'Save Changes';
  document.getElementById('fId').value                 = emp.id;
  document.getElementById('fId').disabled              = true;
  document.getElementById('fName').value               = emp.name;
  document.getElementById('fPosition').value           = emp.position;
  document.getElementById('fSalary').value             = emp.salary;
  document.getElementById('employeeModal').classList.remove('hidden');
}

function closeModal() {
  document.getElementById('employeeModal').classList.add('hidden');
  editingId = null;
}

async function submitEmployee(e) {
  e.preventDefault();
  const btn = document.getElementById('formSubmitBtn');
  btn.disabled    = true;
  btn.textContent = 'Saving…';

  const payload = {
    id:       parseInt(document.getElementById('fId').value),
    name:     document.getElementById('fName').value.trim(),
    position: document.getElementById('fPosition').value.trim(),
    salary:   parseFloat(document.getElementById('fSalary').value),
  };

  try {
    let r;
    if (editingId !== null) {
      r = await fetch(`/api/employees/${editingId}`, {
        method:  'PUT',
        headers: { 'Content-Type': 'application/json' },
        body:    JSON.stringify(payload),
      });
    } else {
      r = await fetch('/api/employees', {
        method:  'POST',
        headers: { 'Content-Type': 'application/json' },
        body:    JSON.stringify(payload),
      });
    }

    const data = await r.json();
    if (!r.ok) throw new Error(data.error || 'Request failed');

    closeModal();
    await loadDirectory();
    refreshGlobalStats();
    showToast(editingId !== null ? '✅ Employee updated!' : '✅ Employee added!', 'success');
  } catch (err) {
    showToast(`❌ ${err.message}`, 'error');
  } finally {
    btn.disabled    = false;
    btn.textContent = editingId !== null ? 'Save Changes' : 'Add Employee';
  }
}

// ── Delete employee ─────────────────────────────────
function openDeleteModal(id, name) {
  deletingId = id;
  document.getElementById('deleteMsg').textContent =
    `Are you sure you want to remove ${name} (ID #${id}) from the system? This cannot be undone.`;
  document.getElementById('deleteModal').classList.remove('hidden');
}

function closeDeleteModal() {
  document.getElementById('deleteModal').classList.add('hidden');
  deletingId = null;
}

async function confirmDelete() {
  if (deletingId === null) return;
  try {
    const r = await fetch(`/api/employees/${deletingId}`, { method: 'DELETE' });
    if (!r.ok) throw new Error('Delete failed');

    closeDeleteModal();
    await loadDirectory();
    refreshGlobalStats();
    showToast('🗑️ Employee removed.', 'success');
  } catch (err) {
    showToast(`❌ ${err.message}`, 'error');
  }
}

// ═══════════════════════════════════════════════════
//  ANALYTICS
// ═══════════════════════════════════════════════════

async function loadAnalytics() {
  const grid = document.getElementById('analyticsGrid');
  grid.innerHTML = '<div class="loading-state"><div class="spinner"></div><span>Loading analytics…</span></div>';

  try {
    const r = await fetch('/api/stats');
    const s = await r.json();
    renderAnalytics(s);
  } catch {
    grid.innerHTML = '<div class="empty-state"><p>Failed to load analytics.</p></div>';
  }
}

function renderAnalytics(s) {
  const fmt = n => `₹${Number(n).toLocaleString('en-IN', { maximumFractionDigits: 0 })}`;
  const grid = document.getElementById('analyticsGrid');

  if (!s.total) {
    grid.innerHTML = '<div class="empty-state"><p>No data yet. Add employees first.</p></div>';
    return;
  }

  const positions = s.positions || {};
  const maxCount  = Math.max(...Object.values(positions), 1);
  const rolesHtml = Object.entries(positions).map(([role, count]) => `
    <div class="role-row">
      <div class="role-label">${escHtml(role)}</div>
      <div class="role-bar-wrap">
        <div class="role-bar" style="width:${Math.round((count / maxCount) * 100)}%"></div>
      </div>
      <div class="role-count">${count}</div>
    </div>
  `).join('');

  grid.innerHTML = `
    <div class="stat-card purple">
      <div class="stat-card-label">
        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"/><circle cx="9" cy="7" r="4"/></svg>
        Total Employees
      </div>
      <div class="stat-card-value">${s.total}</div>
      <div class="stat-card-sub">Active team members</div>
    </div>

    <div class="stat-card green">
      <div class="stat-card-label">
        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><line x1="12" y1="1" x2="12" y2="23"/><path d="M17 5H9.5a3.5 3.5 0 0 0 0 7h5a3.5 3.5 0 0 1 0 7H6"/></svg>
        Total Payroll
      </div>
      <div class="stat-card-value">${fmt(s.payroll)}</div>
      <div class="stat-card-sub">Annual salary budget</div>
    </div>

    <div class="stat-card amber">
      <div class="stat-card-label">
        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><line x1="18" y1="20" x2="18" y2="10"/><line x1="12" y1="20" x2="12" y2="4"/><line x1="6" y1="20" x2="6" y2="14"/></svg>
        Avg Salary
      </div>
      <div class="stat-card-value">${fmt(s.average)}</div>
      <div class="stat-card-sub">Per employee / year</div>
    </div>

    <div class="stat-card blue">
      <div class="stat-card-label">
        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polyline points="23 6 13.5 15.5 8.5 10.5 1 18"/></svg>
        Top Earner
      </div>
      <div class="stat-card-value" style="font-size:1.2rem">${escHtml(s.top?.name || '—')}</div>
      <div class="stat-card-sub">${fmt(s.top?.salary || 0)} · ${escHtml(s.top?.position || '')}</div>
    </div>

    <div class="stat-card stat-card-wide">
      <div class="stat-card-label">
        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"/><path d="M12 6v6l4 2"/></svg>
        Roles Breakdown
      </div>
      <div class="roles-grid">${rolesHtml}</div>
    </div>
  `;
}

// ═══════════════════════════════════════════════════
//  Utilities
// ═══════════════════════════════════════════════════

function getInitials(name) {
  return (name || '?')
    .split(' ')
    .filter(Boolean)
    .slice(0, 2)
    .map(w => w[0].toUpperCase())
    .join('');
}

function escHtml(s) {
  return String(s)
    .replace(/&/g,'&amp;')
    .replace(/</g,'&lt;')
    .replace(/>/g,'&gt;')
    .replace(/"/g,'&quot;');
}

function renderMarkdown(text) {
  // Bold **text**
  text = text.replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>');
  // Italic *text*
  text = text.replace(/\*([^*]+)\*/g, '<em>$1</em>');
  // Bullet points
  text = text.replace(/^• (.+)$/gm, '<li>$1</li>');
  text = text.replace(/(<li>.*<\/li>\n?)+/gs, match => `<ul>${match}</ul>`);
  // Newlines
  text = text.replace(/\n/g, '<br>');
  return text;
}

function showToast(msg, type = '') {
  const toast = document.getElementById('toast');
  toast.textContent = msg;
  toast.className   = `toast ${type} show`;
  clearTimeout(toastTimer);
  toastTimer = setTimeout(() => { toast.classList.remove('show'); }, 3500);
}

// Close modals on overlay click
document.getElementById('employeeModal').addEventListener('click', e => {
  if (e.target === e.currentTarget) closeModal();
});
document.getElementById('deleteModal').addEventListener('click', e => {
  if (e.target === e.currentTarget) closeDeleteModal();
});
