// ============================================================
// Atlas M8 — Mission Control Javascript
// Handles PIN auth, polling, and DOM updates
// ============================================================

let authToken = localStorage.getItem("chat_auth_token");

// Check if we have a token on load
document.addEventListener("DOMContentLoaded", () => {
  if (!authToken) {
    document.getElementById("pin-gate").style.display = "flex";
  } else {
    document.getElementById("pin-gate").style.display = "none";
    initApp();
  }
});

// Auth Flow
document.getElementById("pin-submit").addEventListener("click", async () => {
  const pin = document.getElementById("pin-input").value;
  if (!pin) return;
  
  try {
    const res = await fetch("/api/orc/chat-token", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ pin })
    });
    const data = await res.json();
    if (data.token) {
      authToken = data.token;
      localStorage.setItem("chat_auth_token", authToken);
      document.getElementById("pin-gate").style.display = "none";
      initApp();
    } else {
      document.getElementById("pin-error").innerText = "Invalid PIN";
    }
  } catch (err) {
    document.getElementById("pin-error").innerText = "Server Error";
  }
});

document.getElementById("pin-input").addEventListener("keydown", (e) => {
  if (e.key === "Enter") {
    document.getElementById("pin-submit").click();
  }
});

// App Initialization
function initApp() {
  document.getElementById("app").style.display = "block";
  // Setup iframe
  document.getElementById("chat-iframe").src = "/chat?embedded=1&token=" + authToken;
  
  // Initial Fetch
  fetchAll();
  
  // Setup SSE
  initSSE();
  
  // Setup 30s Polling respecting visibility
  setInterval(() => {
    if (document.visibilityState === "visible") {
      fetchAll();
    }
  }, 30000);
}

let eventSource = null;

function initSSE() {
  if (eventSource) eventSource.close();
  eventSource = new EventSource("/atlas/feed?token=" + encodeURIComponent(authToken));
  
  eventSource.onmessage = (e) => {
    try {
      const data = JSON.parse(e.data);
      if (data.ping) return; // Keepalive
    } catch (err) {}
  };
  
  eventSource.addEventListener("intent", (e) => {
    try {
      const payload = JSON.parse(e.data);
      renderIntent(payload);
    } catch (err) {
      console.error("Failed to parse intent", err);
    }
  });
  
  eventSource.addEventListener("intent_resolved", (e) => {
    try {
      const payload = JSON.parse(e.data);
      removeIntent(payload.id);
    } catch (err) {
      console.error("Failed to parse intent_resolved", err);
    }
  });

  eventSource.onerror = (e) => {
    console.error("SSE Error", e);
    eventSource.close();
    // Reconnect after 5s
    setTimeout(initSSE, 5000);
  };
}

async function handleIntentAction(id, action) {
  try {
    const res = await fetch(`/atlas/intent/${id}/${action}`, {
      method: "POST",
      headers: { "Authorization": `Bearer ${authToken}` }
    });
    if (res.ok) {
      removeIntent(id);
    } else {
      console.error(`Failed to ${action} intent ${id}`);
    }
  } catch (err) {
    console.error("Action error", err);
  }
}

function renderIntent(payload) {
  const container = document.getElementById("intent-feed");
  // Check if already exists
  if (document.getElementById(`intent-${payload.id}`)) return;
  
  const div = document.createElement("div");
  div.id = `intent-${payload.id}`;
  div.className = "row-item";
  div.style.border = "1px solid var(--accent)";
  div.style.background = "rgba(186, 104, 73, 0.1)"; // faint accent
  div.style.padding = "8px";
  
  div.innerHTML = `
    <div style="display:flex; justify-content:space-between; align-items:center;">
      <div>
        <div class="title" style="color:var(--accent);">${payload.crew} Requesting Action</div>
        <div class="meta" style="color:var(--bone); margin-top:4px;">${payload.message}</div>
      </div>
      <div style="display:flex; gap:8px;">
        <button class="btn-action" style="color:var(--green); border-color:var(--green);" onclick="handleIntentAction('${payload.id}', 'approve')">Approve</button>
        <button class="btn-action" style="color:var(--red); border-color:var(--red);" onclick="handleIntentAction('${payload.id}', 'reject')">Reject</button>
      </div>
    </div>
  `;
  container.prepend(div);
}

function removeIntent(id) {
  const el = document.getElementById(`intent-${id}`);
  if (el) el.remove();
}

// Global fetcher
async function fetchAll() {
  try {
    const [state, queue, content, spend, heartbeats, errors, hero] = await Promise.all([
      fetchAPI("/atlas/state"),
      fetchAPI("/atlas/queue"),
      fetchAPI("/atlas/content"),
      fetchAPI("/atlas/spend"),
      fetchAPI("/atlas/heartbeats"),
      fetchAPI("/atlas/errors"),
      fetchAPI("/atlas/hero")
    ]);
    
    renderHero(hero);
    renderState(state);
    renderQueue(queue);
    renderContent(content);
    renderSpend(spend);
    renderHeartbeats(heartbeats);
    renderErrors(errors);
  } catch (err) {
    console.error("Fetch failed", err);
  }
}

// Authenticated Fetch wrapper
async function fetchAPI(endpoint) {
  const res = await fetch(endpoint, {
    headers: { "Authorization": `Bearer ${authToken}` }
  });
  if (res.status === 401 || res.status === 403) {
    localStorage.removeItem("chat_auth_token");
    window.location.reload();
  }
  return res.json();
}

// Render Functions
function renderHero(data) {
  if (!data) return;
  // Status
  const txtSys = document.getElementById("txt-system");
  const ledSys = document.getElementById("led-system");
  txtSys.innerText = "SYSTEM: " + data.status;
  if (data.status === "OPERATIONAL") ledSys.style.background = "var(--green)";
  
  // Spend
  document.getElementById("hero-spend-val").innerHTML = `${data.total_spend_7d.toFixed(2)}<span class="small">USD</span>`;
  
  // Last Action
  document.getElementById("hero-action-type").innerText = "Active";
  
  // Next Fire
  document.getElementById("hero-fire-val").innerText = data.next_fire;
}

function renderState(data) {
  const box = document.getElementById("state-body");
  if (!data) return;
  let html = `<div style="font-family:'IBM Plex Mono',monospace; font-size:13px; color:var(--ink-2)">`;
  html += `Killed: ${data.killed ? 'YES' : 'NO'}<br/>`;
  html += `Cap: $${data.cap_usd}<br/><br/>`;
  html += `<strong>Crews:</strong><br/>`;
  if (data.crews) {
    for (const [crew, settings] of Object.entries(data.crews)) {
      html += `- ${crew}: enabled=${settings.enabled}, dry_run=${settings.dry_run}<br/>`;
    }
  }
  html += `</div>`;
  box.innerHTML = html;
}

function renderQueue(data) {
  const box = document.getElementById("queue-body");
  if (!data || data.length === 0) {
    box.innerHTML = `<div class="loading" style="animation:none;">No pending approvals</div>`;
    return;
  }
  let html = "";
  data.forEach(item => {
    html += `
      <div class="row-item">
        <div class="title">${item.crew_name} / ${item.proposal_type}</div>
        <div class="meta">${new Date(item.ts_created).toLocaleDateString()}</div>
      </div>
    `;
  });
  box.innerHTML = html;
}

function renderContent(data) {
  const box = document.getElementById("content-body");
  box.innerHTML = `<div class="loading" style="animation:none;">Content sync downgraded (Free Plan)</div>`;
}

function renderSpend(data) {
  const box = document.getElementById("spend-body");
  if (!data) return;
  box.innerHTML = `
    <div style="font-family:'Atkinson Hyperlegible',sans-serif; font-size:32px; color:var(--bone); font-weight:bold;">
      $${data.total_7d.toFixed(2)}
    </div>
    <div style="font-family:'IBM Plex Mono',monospace; font-size:12px; color:var(--ink-3); margin-top:8px;">
      Total spend last 7 days
    </div>
  `;
}

function renderHeartbeats(data) {
  const box = document.getElementById("heartbeats-body");
  if (!data || data.length === 0) {
    box.innerHTML = `<div class="loading" style="animation:none;">No active heartbeats</div>`;
    return;
  }
  let html = "";
  data.forEach(item => {
    html += `
      <div class="row-item">
        <div class="title">${item.name}</div>
        <div class="meta">in ${item.seconds_until_fire}s</div>
      </div>
    `;
  });
  box.innerHTML = html;
}

function renderErrors(data) {
  const box = document.getElementById("errors-body");
  box.innerHTML = `<div class="loading" style="animation:none;">Log monitor standing by...</div>`;
}
