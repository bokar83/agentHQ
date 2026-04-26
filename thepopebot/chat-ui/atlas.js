// atlas.js -- Atlas Mission Control client
// DOM is built with createElement/textContent throughout.
// No user-sourced data is ever injected via innerHTML.

const ORC_BASE = '/api/orc';
const TOKEN_TTL_MS = 8 * 60 * 60 * 1000;

let _token = null;

// Safe DOM element builder
function el(tag, attrs, ...children) {
  const node = document.createElement(tag);
  if (attrs) {
    Object.entries(attrs).forEach(([k, v]) => {
      if (k === 'class') node.className = v;
      else if (k === 'dataset') Object.entries(v).forEach(([dk, dv]) => (node.dataset[dk] = dv));
      else node.setAttribute(k, v);
    });
  }
  children.forEach(c => {
    if (c == null) return;
    node.appendChild(typeof c === 'string' ? document.createTextNode(c) : c);
  });
  return node;
}

// Bootstrap
(function init() {
  const stored = sessionStorage.getItem('chat_token');
  const storedTs = sessionStorage.getItem('chat_token_ts');
  if (stored && storedTs && (Date.now() - parseInt(storedTs, 10)) < TOKEN_TTL_MS) {
    _token = stored;
    showDashboard();
  }
  document.getElementById('pin-form').addEventListener('submit', submitPin);
})();

// PIN flow
async function submitPin(e) {
  e.preventDefault();
  const pin = document.getElementById('pin-input').value.trim();
  const btn = document.getElementById('pin-submit');
  const errEl = document.getElementById('pin-error');

  if (!pin) return;
  btn.disabled = true;
  btn.textContent = 'Connecting...';
  errEl.textContent = '';

  try {
    const res = await fetch(ORC_BASE + '/chat-token', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ pin }),
    });
    const data = await res.json();
    if (!res.ok) {
      errEl.textContent = data.detail || 'Connection failed.';
      return;
    }
    _token = data.token;
    sessionStorage.setItem('chat_token', _token);
    sessionStorage.setItem('chat_token_ts', String(Date.now()));
    showDashboard();
  } catch (_) {
    errEl.textContent = 'Network error. Is the VPS reachable?';
  } finally {
    btn.disabled = false;
    btn.textContent = 'Connect';
  }
}

function showDashboard() {
  document.getElementById('pin-screen').style.display = 'none';
  const dash = document.getElementById('dashboard');
  dash.hidden = false;
  startPolling();
}

// Fetch helper
async function apiFetch(path, opts) {
  opts = opts || {};
  const res = await fetch(ORC_BASE + path, {
    method: opts.method || 'GET',
    headers: Object.assign(
      { 'Content-Type': 'application/json', 'Authorization': 'Bearer ' + _token },
      opts.headers || {}
    ),
    body: opts.body || undefined,
  });
  if (res.status === 401) {
    sessionStorage.removeItem('chat_token');
    sessionStorage.removeItem('chat_token_ts');
    location.reload();
    throw new Error('TOKEN_EXPIRED');
  }
  return res.json();
}

// Hero strip
async function refreshHero() {
  const badge = document.getElementById('sync-badge');
  try {
    badge.textContent = 'Syncing...';
    badge.className = 'badge badge-dim';
    const d = await apiFetch('/atlas/hero');
    const status = d.system_status || 'green';

    const statusEl = document.getElementById('hero-status-val');
    statusEl.textContent = status.charAt(0).toUpperCase() + status.slice(1);
    statusEl.className = 'hero-value ' + status;

    const lastEl = document.getElementById('hero-last-action-val');
    const la = d.last_action || {};
    lastEl.textContent = la.description || 'None yet';

    const nextEl = document.getElementById('hero-next-fire-val');
    const nf = d.next_fire || {};
    nextEl.textContent = nf.at ? (nf.at + ' (' + nf.in_minutes + ' min)') : 'None scheduled';

    const spendEl = document.getElementById('hero-spend-val');
    const sp = d.spend_pacing || {};
    spendEl.textContent = sp.pct != null ? sp.pct.toFixed(1) + '%' : '--';

    badge.textContent = 'Live';
    badge.className = 'badge badge-green';
    const hb = document.getElementById('health-badge');
    hb.textContent = d.killed ? 'Killed' : 'Online';
    hb.className = d.killed ? 'badge badge-red' : 'badge badge-green';
  } catch (err) {
    if (err.message !== 'TOKEN_EXPIRED') {
      badge.textContent = 'Offline';
      badge.className = 'badge badge-red';
    }
  }
}

// State card
function renderState(d) {
  const body = document.getElementById('card-state-body');
  const actions = document.getElementById('card-state-actions');
  body.replaceChildren();
  actions.replaceChildren();

  const crews = d.crews || {};
  const griot = crews.griot || {};
  const rows = [
    ['Kill Switch', d.killed ? 'ACTIVE' : 'Off', d.killed ? 'red' : 'green'],
    ['Griot Enabled', griot.enabled ? 'On' : 'Off', griot.enabled ? 'green' : 'amber'],
    ['Griot Dry-Run', griot.dry_run ? 'On' : 'Off', griot.dry_run ? 'amber' : ''],
    ['Daily Cap', '$' + (d.cap_usd || 0).toFixed(2), ''],
  ];
  rows.forEach(function(row) {
    body.appendChild(el('div', { class: 'data-row' },
      el('span', { class: 'data-label' }, row[0]),
      el('span', { class: 'data-value ' + row[2] }, row[1]),
    ));
  });

  const griotEnabled = !!griot.enabled;
  const toggleBtn = el('button', { class: 'btn btn-toggle' + (griotEnabled ? ' active' : '') },
    griotEnabled ? 'Disable Griot' : 'Enable Griot'
  );
  toggleBtn.addEventListener('click', function() { actionToggleGriot(!griotEnabled, toggleBtn); });

  const griotDryRun = !!griot.dry_run;
  const dryBtn = el('button', { class: 'btn btn-toggle' + (griotDryRun ? ' active' : '') },
    griotDryRun ? 'Live Mode' : 'Dry-Run'
  );
  dryBtn.addEventListener('click', function() { actionToggleDryRun(!griotDryRun, dryBtn); });

  actions.appendChild(toggleBtn);
  actions.appendChild(dryBtn);
}

async function refreshState() {
  try { renderState(await apiFetch('/atlas/state')); } catch (_) {}
}

// Queue card
function renderQueue(d) {
  const body = document.getElementById('card-queue-body');
  body.replaceChildren();
  const items = d.items || [];
  if (!items.length) {
    body.appendChild(el('p', { class: 'empty-state' }, 'No pending items'));
    return;
  }
  items.forEach(function(item) {
    const crew = el('div', { class: 'queue-crew' });
    crew.textContent = item.crew_name || '';
    const preview = el('div', { class: 'queue-preview' });
    preview.textContent = item.preview || '';

    const approveBtn = el('button', { class: 'btn btn-approve' }, 'Approve');
    const rejectBtn = el('button', { class: 'btn btn-reject' }, 'Reject');
    approveBtn.addEventListener('click', function() { actionQueueApprove(item.id, approveBtn, rejectBtn); });
    rejectBtn.addEventListener('click', function() { actionQueueReject(item.id, approveBtn, rejectBtn); });

    body.appendChild(el('div', { class: 'queue-item' },
      crew, preview,
      el('div', { class: 'queue-actions' }, approveBtn, rejectBtn)
    ));
  });
}

async function refreshQueue() {
  try { renderQueue(await apiFetch('/atlas/queue')); } catch (_) {}
}

// Content card
function renderContent(d) {
  const body = document.getElementById('card-content-body');
  body.replaceChildren();
  const items = d.items || [];
  if (!items.length) {
    body.appendChild(el('p', { class: 'empty-state' }, 'No posts scheduled this week'));
    return;
  }
  items.forEach(function(item) {
    const platform = el('span', { class: 'content-platform' });
    platform.textContent = (item.platform || '').slice(0, 2);
    const title = el('span', { class: 'content-title' });
    title.textContent = item.title || '';
    const rawStatus = (item.status || '').toLowerCase();
    const sCls = rawStatus === 'queued' ? 'content-status queued'
               : rawStatus === 'posted' ? 'content-status posted'
               : rawStatus === 'skipped' ? 'content-status skipped'
               : 'content-status';
    const status = el('span', { class: sCls });
    status.textContent = item.status || '';
    body.appendChild(el('div', { class: 'content-item' }, platform, title, status));
  });
}

async function refreshContent() {
  try { renderContent(await apiFetch('/atlas/content')); } catch (_) {}
}

// Spend card
function renderSpend(d) {
  const body = document.getElementById('card-spend-body');
  body.replaceChildren();
  const today = d.today || {};
  const spent = today.spent_usd || 0;
  const cap = today.cap_usd || 1;
  const pct = Math.min(100, (spent / cap) * 100);
  const barCls = pct > 90 ? 'spend-bar-fill red' : pct > 70 ? 'spend-bar-fill amber' : 'spend-bar-fill';

  body.appendChild(el('div', { class: 'data-row' },
    el('span', { class: 'data-label' }, 'Today Spent'),
    el('span', { class: 'data-value' }, '$' + spent.toFixed(4)),
  ));
  body.appendChild(el('div', { class: 'data-row' },
    el('span', { class: 'data-label' }, 'Daily Cap'),
    el('span', { class: 'data-value' }, '$' + cap.toFixed(2)),
  ));

  const track = el('div', { class: 'spend-bar-track' });
  const fill = el('div', { class: barCls });
  fill.style.width = pct.toFixed(1) + '%';
  track.appendChild(fill);
  body.appendChild(track);

  const pctLabel = el('div', { class: 'data-label' });
  pctLabel.textContent = pct.toFixed(1) + '% of cap used';
  body.appendChild(pctLabel);

  const perCrew = today.per_crew || {};
  Object.entries(perCrew).forEach(function([crew, usd]) {
    if (usd > 0) {
      body.appendChild(el('div', { class: 'data-row' },
        el('span', { class: 'data-label' }, crew),
        el('span', { class: 'data-value' }, '$' + usd.toFixed(4)),
      ));
    }
  });
}

async function refreshSpend() {
  try { renderSpend(await apiFetch('/atlas/spend')); } catch (_) {}
}

// Heartbeats card
function renderHeartbeats(d) {
  const body = document.getElementById('card-heartbeats-body');
  body.replaceChildren();
  const wakes = d.wakes || [];
  if (!wakes.length) {
    body.appendChild(el('p', { class: 'empty-state' }, 'No wakes registered'));
    return;
  }
  wakes.forEach(function(w) {
    const timeStr = w.at_hour != null
      ? String(w.at_hour).padStart(2, '0') + ':' + String(w.at_minute || 0).padStart(2, '0')
      : (w.every_seconds ? 'every ' + w.every_seconds + 's' : '--');
    const lastStr = w.last_fired ? w.last_fired.slice(0, 16).replace('T', ' ') : 'never';
    const name = el('span', { class: 'hb-name' });
    name.textContent = w.name || '';
    const last = el('span', { class: 'hb-last' });
    last.textContent = timeStr + ' / last: ' + lastStr;
    body.appendChild(el('div', { class: 'hb-row' }, name, last));
  });
}

async function refreshHeartbeats() {
  try { renderHeartbeats(await apiFetch('/atlas/heartbeats')); } catch (_) {}
}

// Errors card
function renderErrors(d) {
  const body = document.getElementById('card-errors-body');
  body.replaceChildren();
  const fallbacks = d.fallbacks || [];
  const logLines = d.log_lines || [];
  if (!fallbacks.length && !logLines.length) {
    body.appendChild(el('p', { class: 'empty-state' }, 'No errors in last 24h'));
    return;
  }
  fallbacks.forEach(function(f) {
    const row = el('div', { class: 'error-row' });
    const ts = el('span', { class: 'data-label' });
    ts.textContent = (f.ts || '').slice(0, 16).replace('T', ' ') + ' ';
    const task = document.createTextNode(f.task_type || '');
    row.appendChild(ts);
    row.appendChild(task);
    body.appendChild(row);
  });
}

async function refreshErrors() {
  try { renderErrors(await apiFetch('/atlas/errors')); } catch (_) {}
}

// Ideas card
function renderIdeas(d) {
  const body = document.getElementById('card-ideas-body');
  body.replaceChildren();
  const items = d.items || [];
  if (!items.length) {
    body.appendChild(el('p', { class: 'empty-state' }, 'No active ideas'));
    return;
  }
  items.forEach(function(item, idx) {
    const rank = el('span', { class: 'data-label' });
    rank.textContent = String(idx + 1) + '.';
    const title = el('span', { class: 'content-title' });
    title.textContent = item.title || '';
    const impact = el('span', { class: 'data-label' });
    impact.textContent = (item.impact || '') + ' / ' + (item.effort || '');
    body.appendChild(el('div', { class: 'content-item' }, rank, title, impact));
  });
}

async function refreshIdeas() {
  try { renderIdeas(await apiFetch('/atlas/ideas')); } catch (_) {}
}

// Action stubs (wired fully in Task 17)
async function actionToggleGriot(enabled, btn) {
  btn.disabled = true;
  try {
    const d = await apiFetch('/atlas/toggle/griot', {
      method: 'POST',
      body: JSON.stringify({ enabled }),
    });
    renderState(d);
  } catch (_) { btn.disabled = false; }
}

async function actionToggleDryRun(dry_run, btn) {
  btn.disabled = true;
  try {
    const d = await apiFetch('/atlas/toggle/dry_run', {
      method: 'POST',
      body: JSON.stringify({ dry_run }),
    });
    renderState(d);
  } catch (_) { btn.disabled = false; }
}

async function actionQueueApprove(id, approveBtn, rejectBtn) {
  approveBtn.disabled = true;
  rejectBtn.disabled = true;
  try {
    const d = await apiFetch('/atlas/queue/' + id + '/approve', { method: 'POST', body: '{}' });
    renderQueue(d);
  } catch (_) { approveBtn.disabled = false; rejectBtn.disabled = false; }
}

async function actionQueueReject(id, approveBtn, rejectBtn) {
  approveBtn.disabled = true;
  rejectBtn.disabled = true;
  try {
    const d = await apiFetch('/atlas/queue/' + id + '/reject', {
      method: 'POST',
      body: JSON.stringify({ note: '' }),
    });
    renderQueue(d);
  } catch (_) { approveBtn.disabled = false; rejectBtn.disabled = false; }
}

// Polling
function refreshAll() {
  refreshHero();
  refreshState();
  refreshQueue();
  refreshContent();
  refreshSpend();
  refreshHeartbeats();
  refreshErrors();
  refreshIdeas();
}

function startPolling() {
  refreshAll();
  setInterval(refreshAll, 30000);
  document.addEventListener('visibilitychange', function() {
    if (document.visibilityState === 'visible') refreshAll();
  });
}
