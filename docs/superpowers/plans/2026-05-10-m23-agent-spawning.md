# M23: Agent-to-Agent Spawning & Delegation — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Ship a lightweight Minion spawning framework inside `orc-crewai` so any crew can dispatch async sub-tasks, plus the Live Agent Graph panel on the Atlas dashboard (M8b absorbed).

**Architecture:** `spawn()` in `skills/coordination/spawner.py` enqueues Minion tasks into the existing `tasks` table. `orchestrator/minion_worker.py` runs a background async loop that claims and executes them in a thread pool. A new `/atlas/agents` endpoint feeds a new dashboard card at agentshq.boubacarbarry.com/atlas.

**Tech Stack:** Python 3.13, FastAPI, psycopg2, asyncio/ThreadPoolExecutor, vanilla JS (Atlas frontend in `agentsHQ-echo/thepopebot/chat-ui/`).

---

## File Map

| Action | File | What it does |
|---|---|---|
| Create | `skills/coordination/spawner.py` | `spawn()`, `SpawnDepthExceeded` |
| Modify | `skills/coordination/__init__.py` | Add `recent_completed_prefix()` |
| Create | `orchestrator/minion_worker.py` | Background claim/execute loop + handler registry |
| Modify | `orchestrator/app.py` | Wire `minion_worker.run()` at startup |
| Modify | `orchestrator/atlas_dashboard.py` | Add `get_agents()` |
| Modify | `orchestrator/app.py` | Add `GET /atlas/agents` endpoint |
| Create | `tests/test_minion_spawner.py` | Unit tests for spawner.py (no DB needed) |
| Create | `tests/test_minion_worker.py` | Unit tests for worker (mocked coordination) |
| Create | `tests/test_minion_integration.py` | Integration tests (requires VPS tunnel) |
| Modify | `agentsHQ-echo/thepopebot/chat-ui/atlas.html` | Agents card HTML |
| Modify | `agentsHQ-echo/thepopebot/chat-ui/atlas.js` | `renderAgents()` + poll wire-in |

---

## Pre-flight

Before starting, confirm VPS Postgres is reachable (needed for integration tests):

```bash
ssh root@72.60.209.109 "docker exec orc-postgres psql -U postgres -d postgres -c 'SELECT 1;'"
```

Expected output: ` ?column? \n----------\n        1`

SSH tunnel for integration tests (open once per session):
```bash
ssh -L 55432:localhost:5432 root@72.60.209.109 -N -f -o ExitOnForwardFailure=yes
export TEST_COORD_DSN="host=127.0.0.1 port=55432 user=postgres password=postgres dbname=postgres"
```

---

## Task 1: `spawn()` + `recent_completed_prefix()`

**Files:**
- Create: `skills/coordination/spawner.py`
- Modify: `skills/coordination/__init__.py`
- Create: `tests/test_minion_spawner.py`

- [ ] **Step 1: Write the failing tests**

```python
# tests/test_minion_spawner.py
"""Tests for spawner.py — no DB required."""
from __future__ import annotations
import sys, os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import pytest
from skills.coordination.spawner import spawn, SpawnDepthExceeded, MAX_SPAWN_DEPTH


def test_spawn_depth_exceeded_raises_before_db(monkeypatch):
    """spawn() at max depth must raise without touching DB."""
    calls = []
    monkeypatch.setattr("skills.coordination.enqueue", lambda k, p: calls.append((k, p)) or "fake-id")
    with pytest.raises(SpawnDepthExceeded):
        spawn("minion:test", {}, depth=MAX_SPAWN_DEPTH)
    assert len(calls) == 0


def test_spawn_bad_kind_raises(monkeypatch):
    monkeypatch.setattr("skills.coordination.enqueue", lambda k, p: "fake-id")
    with pytest.raises(ValueError, match="minion:"):
        spawn("notaminion:test", {})


def test_spawn_returns_task_id(monkeypatch):
    monkeypatch.setattr("skills.coordination.enqueue", lambda k, p: "abc123")
    result = spawn("minion:test", {"msg": "hello"})
    assert result == "abc123"


def test_spawn_injects_meta(monkeypatch):
    captured = {}
    def fake_enqueue(kind, payload):
        captured["kind"] = kind
        captured["payload"] = payload
        return "id1"
    monkeypatch.setattr("skills.coordination.enqueue", fake_enqueue)
    spawn("minion:test", {"x": 1}, parent_id="p99", depth=2)
    assert captured["payload"]["_parent_id"] == "p99"
    assert captured["payload"]["_depth"] == 2
    assert captured["payload"]["x"] == 1
```

- [ ] **Step 2: Run — expect ImportError**

```bash
cd d:/Ai_Sandbox/agentsHQ
python -m pytest tests/test_minion_spawner.py -v 2>&1 | head -10
```

Expected: `ModuleNotFoundError: No module named 'skills.coordination.spawner'`

- [ ] **Step 3: Create `skills/coordination/spawner.py`**

```python
# skills/coordination/spawner.py
from __future__ import annotations

MAX_SPAWN_DEPTH = 5


class SpawnDepthExceeded(RuntimeError):
    pass


def spawn(kind: str, payload: dict, parent_id: str | None = None, depth: int = 0) -> str:
    """Enqueue a Minion task. Returns task_id. Non-blocking.

    kind must start with 'minion:' (e.g. 'minion:triage', 'minion:research').
    depth is the current nesting level — callers pass their own depth + 1.
    Raises SpawnDepthExceeded if depth >= MAX_SPAWN_DEPTH (default 5).
    Raises ValueError if kind does not start with 'minion:'.
    """
    if depth >= MAX_SPAWN_DEPTH:
        raise SpawnDepthExceeded(
            f"spawn depth {depth} exceeds cap {MAX_SPAWN_DEPTH}"
        )
    if not kind.startswith("minion:"):
        raise ValueError(
            f"Minion kind must start with 'minion:' -- got '{kind}'"
        )
    full_payload = {"_parent_id": parent_id, "_depth": depth, **payload}
    from skills.coordination import enqueue
    return enqueue(kind, full_payload)
```

- [ ] **Step 4: Run spawner tests — expect 4 passed**

```bash
python -m pytest tests/test_minion_spawner.py -v
```

Expected:
```
tests/test_minion_spawner.py::test_spawn_depth_exceeded_raises_before_db PASSED
tests/test_minion_spawner.py::test_spawn_bad_kind_raises PASSED
tests/test_minion_spawner.py::test_spawn_returns_task_id PASSED
tests/test_minion_spawner.py::test_spawn_injects_meta PASSED
4 passed
```

- [ ] **Step 5: Add `recent_completed_prefix()` to `skills/coordination/__init__.py`**

Append after the `recent_completed` function (around line 275):

```python
def recent_completed_prefix(prefix: str, since_seconds: int = 3600, limit: int = 50) -> list[dict]:
    """Recent finished work items whose kind starts with prefix."""
    with _connect() as c, c.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
        cur.execute(
            """
            SELECT id, kind, status, payload, result, claimed_by, claimed_at
            FROM tasks
            WHERE kind LIKE %s AND status IN ('done', 'failed')
              AND claimed_at > now() - make_interval(secs => %s)
            ORDER BY claimed_at DESC
            LIMIT %s
            """,
            (prefix.rstrip("%") + "%", since_seconds, limit),
        )
        return [dict(r) for r in cur.fetchall()]
```

- [ ] **Step 6: Commit**

```bash
git checkout -b feat/atlas-m23-agent-spawning
git add skills/coordination/spawner.py skills/coordination/__init__.py tests/test_minion_spawner.py
git commit -m "feat(m23): spawner.py + SpawnDepthExceeded + recent_completed_prefix"
```

---

## Task 2: `minion_worker.py`

**Files:**
- Create: `orchestrator/minion_worker.py`
- Create: `tests/test_minion_worker.py`

- [ ] **Step 1: Create `orchestrator/minion_worker.py`**

```python
# orchestrator/minion_worker.py
"""Minion worker: background loop that claims and executes Minion tasks.

Handler registry maps kind -> callable(payload: dict) -> dict.
Register handlers at app startup via minion_worker.register().
"""
from __future__ import annotations

import asyncio
import logging
from typing import Callable

from skills.coordination import claim_next, complete, fail

logger = logging.getLogger("agentsHQ.minion_worker")

# Handler registry: kind -> callable(payload) -> dict
# Plain dict. No dynamic loading. Add new Minion types here at app startup.
_HANDLERS: dict[str, Callable[[dict], dict]] = {}


def register(kind: str, handler: Callable[[dict], dict]) -> None:
    """Register a handler for a Minion kind. Call at app startup."""
    _HANDLERS[kind] = handler


async def run() -> None:
    """Background loop. Runs for the lifetime of the app.

    Polls every 2 seconds. For each registered kind, claims the oldest
    queued task and dispatches it to a thread pool executor.
    Never crashes on handler errors -- logs and marks failed.
    """
    loop = asyncio.get_running_loop()
    while True:
        for kind, handler in list(_HANDLERS.items()):
            task = claim_next(kind, holder="minion_worker", ttl_seconds=300)
            if task:
                logger.info(
                    "minion_worker: claimed kind=%s task_id=%s", kind, task["id"]
                )
                asyncio.create_task(_execute(loop, task, handler))
        await asyncio.sleep(2)


async def _execute(
    loop: asyncio.AbstractEventLoop,
    task: dict,
    handler: Callable[[dict], dict],
) -> None:
    """Run handler in thread pool. Mark complete or failed."""
    try:
        result = await loop.run_in_executor(
            None, lambda: handler(task["payload"])
        )
        complete(task["id"], result or {})
        logger.info("minion_worker: completed task_id=%s", task["id"])
    except Exception as exc:
        fail(task["id"], str(exc))
        logger.error(
            "minion_worker: failed task_id=%s error=%s", task["id"], exc
        )
```

- [ ] **Step 2: Write worker unit tests**

```python
# tests/test_minion_worker.py
"""Unit tests for minion_worker -- mocks coordination layer."""
from __future__ import annotations
import asyncio
import sys, os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../orchestrator")))

import pytest


def test_register_and_handler_callable():
    import minion_worker
    minion_worker._HANDLERS.clear()
    minion_worker.register("minion:test", lambda p: {"ok": True})
    assert "minion:test" in minion_worker._HANDLERS
    result = minion_worker._HANDLERS["minion:test"]({"x": 1})
    assert result == {"ok": True}


def test_execute_calls_complete_on_success(monkeypatch):
    import minion_worker
    completed = {}
    failed = {}
    monkeypatch.setattr(minion_worker, "complete", lambda tid, r: completed.update({tid: r}))
    monkeypatch.setattr(minion_worker, "fail", lambda tid, e: failed.update({tid: e}))

    task = {"id": "t1", "payload": {"msg": "hi"}}
    handler = lambda p: {"echo": p["msg"]}
    asyncio.run(minion_worker._execute(asyncio.get_event_loop(), task, handler))

    assert "t1" in completed
    assert completed["t1"]["echo"] == "hi"
    assert "t1" not in failed


def test_execute_calls_fail_on_exception(monkeypatch):
    import minion_worker
    completed = {}
    failed = {}
    monkeypatch.setattr(minion_worker, "complete", lambda tid, r: completed.update({tid: r}))
    monkeypatch.setattr(minion_worker, "fail", lambda tid, e: failed.update({tid: e}))

    task = {"id": "t2", "payload": {}}

    def boom(p):
        raise ValueError("boom")

    asyncio.run(minion_worker._execute(asyncio.get_event_loop(), task, boom))

    assert "t2" in failed
    assert "boom" in failed["t2"]
    assert "t2" not in completed
```

- [ ] **Step 3: Run worker unit tests**

```bash
python -m pytest tests/test_minion_worker.py -v
```

Expected: 3 passed.

- [ ] **Step 4: Commit**

```bash
git add orchestrator/minion_worker.py tests/test_minion_worker.py
git commit -m "feat(m23): minion_worker background loop + unit tests"
```

---

## Task 3: Wire worker into `app.py` startup

**Files:**
- Modify: `orchestrator/app.py` (startup_event around line 210)

- [ ] **Step 1: Add minion_worker startup block**

In `startup_event()`, after the last `except` block (around line 210), append:

```python
    # M23: Minion worker -- background loop for agent-to-agent spawning.
    try:
        import minion_worker as _mw
        asyncio.create_task(_mw.run())
        logger.info("minion_worker started.")
    except Exception as e:
        logger.warning(f"minion_worker startup failed (non-fatal): {e}")
```

- [ ] **Step 2: Verify app imports cleanly**

```bash
cd d:/Ai_Sandbox/agentsHQ/orchestrator
python -c "import app; print('app import OK')" 2>&1 | tail -3
```

Expected: `app import OK`

- [ ] **Step 3: Commit**

```bash
git add orchestrator/app.py
git commit -m "feat(m23): wire minion_worker.run() at app startup"
```

---

## Task 4: Integration tests (spawn + worker end-to-end)

**Files:**
- Create: `tests/test_minion_integration.py`

- [ ] **Step 1: Open SSH tunnel (if not already open)**

```bash
ssh -L 55432:localhost:5432 root@72.60.209.109 -N -f -o ExitOnForwardFailure=yes
export TEST_COORD_DSN="host=127.0.0.1 port=55432 user=postgres password=postgres dbname=postgres"
```

- [ ] **Step 2: Create `tests/test_minion_integration.py`**

```python
# tests/test_minion_integration.py
"""Integration tests: spawn -> worker claims -> result in DB.

Requires SSH tunnel to VPS Postgres (see Pre-flight). Skipped if unreachable.
"""
from __future__ import annotations
import asyncio
import os
import sys

import psycopg2
import pytest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../orchestrator")))

DSN = os.environ.get(
    "TEST_COORD_DSN",
    "host=127.0.0.1 port=55432 user=postgres password=postgres dbname=postgres",
)


def _can_connect() -> bool:
    try:
        psycopg2.connect(DSN, connect_timeout=2).close()
        return True
    except Exception:
        return False


pytestmark = pytest.mark.skipif(
    not _can_connect(), reason="VPS Postgres tunnel not reachable at TEST_COORD_DSN"
)


@pytest.fixture(autouse=True)
def _set_dsn(monkeypatch):
    monkeypatch.setenv("TEST_COORD_DSN", DSN)
    yield


def test_spawn_creates_queued_row():
    """spawn() must write a queued row to tasks within 1 second."""
    from skills.coordination import init_schema
    from skills.coordination.spawner import spawn
    init_schema()

    task_id = spawn("minion:test", {"msg": "hello"})
    assert isinstance(task_id, str) and len(task_id) > 0

    conn = psycopg2.connect(DSN)
    with conn.cursor() as cur:
        cur.execute("SELECT status, kind FROM tasks WHERE id = %s", (task_id,))
        row = cur.fetchone()
    conn.close()

    assert row is not None, "row not found in tasks table"
    assert row[0] == "queued"
    assert row[1] == "minion:test"


def test_spawn_depth_exceeded_no_db_write():
    """spawn() at max depth must not write any row."""
    from skills.coordination.spawner import spawn, SpawnDepthExceeded, MAX_SPAWN_DEPTH

    conn = psycopg2.connect(DSN)
    with conn.cursor() as cur:
        cur.execute("SELECT COUNT(*) FROM tasks")
        before = cur.fetchone()[0]
    conn.close()

    with pytest.raises(SpawnDepthExceeded):
        spawn("minion:test", {}, depth=MAX_SPAWN_DEPTH)

    conn = psycopg2.connect(DSN)
    with conn.cursor() as cur:
        cur.execute("SELECT COUNT(*) FROM tasks")
        after = cur.fetchone()[0]
    conn.close()

    assert before == after


def test_worker_picks_up_and_completes_task():
    """Worker loop must claim queued task and mark done within 5 seconds."""
    import minion_worker
    from skills.coordination import init_schema
    from skills.coordination.spawner import spawn
    init_schema()

    minion_worker._HANDLERS.clear()
    minion_worker.register("minion:test", lambda p: {"echoed": p.get("msg")})

    task_id = spawn("minion:test", {"msg": "world"})

    async def run_worker_briefly():
        try:
            await asyncio.wait_for(minion_worker.run(), timeout=5.0)
        except asyncio.TimeoutError:
            pass

    asyncio.run(run_worker_briefly())

    conn = psycopg2.connect(DSN)
    with conn.cursor() as cur:
        cur.execute("SELECT status, result FROM tasks WHERE id = %s", (task_id,))
        row = cur.fetchone()
    conn.close()

    assert row is not None
    assert row[0] == "done", f"expected done, got {row[0]}"
    assert row[1]["echoed"] == "world"
```

- [ ] **Step 3: Run integration tests**

```bash
python -m pytest tests/test_minion_integration.py -v
```

Expected: 3 passed (or skipped if tunnel not open).

- [ ] **Step 4: Commit**

```bash
git add tests/test_minion_integration.py
git commit -m "test(m23): integration tests for spawn + worker end-to-end"
```

---

## Task 5: `/atlas/agents` backend endpoint

**Files:**
- Modify: `orchestrator/atlas_dashboard.py`
- Modify: `orchestrator/app.py`
- Modify: `orchestrator/tests/test_atlas_dashboard.py`

- [ ] **Step 1: Write the failing test**

Append to `orchestrator/tests/test_atlas_dashboard.py`:

```python
def test_get_agents_returns_shape():
    """get_agents() must return dict with 'running' and 'recent' lists."""
    from unittest.mock import patch
    mock_running = [{"id": "r1", "resource": "minion:test", "claimed_by": "minion_worker"}]
    mock_recent = [{"id": "d1", "kind": "minion:test", "status": "done"}]

    with patch("skills.coordination.list_running", return_value=mock_running), \
         patch("skills.coordination.recent_completed_prefix", return_value=mock_recent):
        result = atlas_dashboard.get_agents()

    assert "running" in result
    assert "recent" in result
    assert result["running"][0]["id"] == "r1"
    assert result["recent"][0]["kind"] == "minion:test"
```

- [ ] **Step 2: Run — expect AttributeError**

```bash
python -m pytest orchestrator/tests/test_atlas_dashboard.py::test_get_agents_returns_shape -v
```

Expected: `AttributeError: module 'atlas_dashboard' has no attribute 'get_agents'`

- [ ] **Step 3: Append `get_agents()` to `orchestrator/atlas_dashboard.py`**

```python
def get_agents() -> dict:
    """Live Agent Graph: running tasks + recently completed Minion tasks."""
    try:
        from skills.coordination import list_running, recent_completed_prefix
        running = list_running()
        recent = recent_completed_prefix("minion:", since_seconds=3600, limit=50)
        return {"running": running, "recent": recent}
    except Exception:
        return {"running": [], "recent": []}
```

- [ ] **Step 4: Run test — expect PASS**

```bash
python -m pytest orchestrator/tests/test_atlas_dashboard.py::test_get_agents_returns_shape -v
```

Expected: PASSED.

- [ ] **Step 5: Add route to `app.py`**

Find the `/atlas/ledger` GET route (around line 1045). Add immediately after it:

```python
@app.get("/atlas/agents")
async def atlas_agents(_auth=Depends(verify_chat_token)):
    return JSONResponse(_atd.get_agents())
```

- [ ] **Step 6: Commit**

```bash
git add orchestrator/atlas_dashboard.py orchestrator/app.py orchestrator/tests/test_atlas_dashboard.py
git commit -m "feat(m23/m8b): get_agents() + /atlas/agents endpoint"
```

---

## Task 6: Atlas frontend — Agents card

**Files:**
- Modify: `agentsHQ-echo/thepopebot/chat-ui/atlas.html`
- Modify: `agentsHQ-echo/thepopebot/chat-ui/atlas.js`

Work in the `agentsHQ-echo` repo for this task.

- [ ] **Step 1: Add the Agents card to `atlas.html`**

In `agentsHQ-echo/thepopebot/chat-ui/atlas.html`, find the `#cards-col` div. Add after the last `<section class="card"...>` block before `</div><!-- /cards-col -->` (or equivalent closing tag):

```html
<section class="card" data-card="agents" data-color="teal">
  <div class="card-header">
    <h2>Active <span class="accent-word">Agents</span></h2>
  </div>
  <div class="card-body" id="agents-body">
    <p class="dim">Loading...</p>
  </div>
</section>
```

- [ ] **Step 2: Add `renderAgents()` to `atlas.js`**

Find the block of `render*` functions. Append after the last one. Note: builds DOM nodes with `textContent` (not `innerHTML`) to prevent XSS from tasks table values.

```javascript
function renderAgents(d) {
  const el = document.getElementById('agents-body');
  if (!el) return;
  const running = d.running || [];
  const recent = d.recent || [];

  while (el.firstChild) el.removeChild(el.firstChild);

  if (running.length === 0 && recent.length === 0) {
    const p = document.createElement('p');
    p.className = 'dim';
    p.textContent = 'No active agents.';
    el.appendChild(p);
    return;
  }

  function makeTable(rows, cols) {
    const tbl = document.createElement('table');
    tbl.className = 'mini-table';
    const thead = tbl.createTHead();
    const hrow = thead.insertRow();
    cols.forEach(function(c) {
      const th = document.createElement('th');
      th.textContent = c.label;
      hrow.appendChild(th);
    });
    const tbody = tbl.createTBody();
    rows.forEach(function(r) {
      const tr = tbody.insertRow();
      cols.forEach(function(c) {
        const td = tr.insertCell();
        td.textContent = c.get(r) || '--';
      });
    });
    return tbl;
  }

  if (running.length > 0) {
    const lbl = document.createElement('p');
    lbl.className = 'card-label';
    lbl.textContent = 'Running';
    el.appendChild(lbl);
    el.appendChild(makeTable(running, [
      { label: 'Kind', get: function(r) { return r.resource || r.kind; } },
      { label: 'Holder', get: function(r) { return r.claimed_by; } },
      { label: 'Expires', get: function(r) { return r.lease_expires_at ? new Date(r.lease_expires_at).toLocaleTimeString() : null; } }
    ]));
  }

  if (recent.length > 0) {
    const lbl2 = document.createElement('p');
    lbl2.className = 'card-label';
    lbl2.style.marginTop = '0.75rem';
    lbl2.textContent = 'Recent (1h)';
    el.appendChild(lbl2);
    el.appendChild(makeTable(recent, [
      { label: 'Kind', get: function(r) { return r.kind; } },
      { label: 'Status', get: function(r) { return r.status; } },
      { label: 'Claimed By', get: function(r) { return r.claimed_by; } }
    ]));
  }
}
```

- [ ] **Step 3: Wire into the poll loop**

Find the function that calls all other `apiFetch` calls (search for `renderState` and `renderQueue` called together). Add:

```javascript
try { renderAgents(await apiFetch('/atlas/agents')); } catch (_) {}
```

alongside the other fetch calls.

- [ ] **Step 4: Verify locally (no console errors)**

```bash
cd d:/Ai_Sandbox/agentsHQ-echo/thepopebot/chat-ui
python -m http.server 8080
```

Open `http://localhost:8080/atlas.html` in browser. Open DevTools console. Log in with PIN. Confirm Agents card renders with "No active agents." and no JS errors.

- [ ] **Step 5: Commit in agentsHQ-echo repo**

```bash
cd d:/Ai_Sandbox/agentsHQ-echo
git add thepopebot/chat-ui/atlas.html thepopebot/chat-ui/atlas.js
git commit -m "feat(m8b): Active Agents card on Atlas dashboard (XSS-safe DOM construction)"
```

---

## Task 7: Deploy + verify all 5 success criteria

- [ ] **Step 1: Deploy backend to VPS**

```bash
ssh root@72.60.209.109 "cd /root/agentsHQ && git pull && docker compose up -d orchestrator"
```

Wait 15 seconds, then confirm minion_worker started:

```bash
ssh root@72.60.209.109 "docker logs orc-crewai --tail 30 2>&1 | grep -i minion"
```

Expected: `minion_worker started.`

- [ ] **Step 2: Register a smoke-test handler temporarily**

Add to `app.py` startup (after `_mw` import, inside the try block):

```python
        _mw.register("minion:test", lambda p: {"ok": True, "echo": p.get("msg", "")})
```

Redeploy:
```bash
ssh root@72.60.209.109 "cd /root/agentsHQ && git pull && docker compose up -d orchestrator"
```

- [ ] **Step 3: Verify criterion 1 -- spawn creates queued row**

```bash
ssh root@72.60.209.109 "docker exec orc-crewai python3 -c \"
import sys; sys.path.insert(0, '/app')
from skills.coordination.spawner import spawn
tid = spawn('minion:test', {'msg': 'hello'})
print('task_id:', tid)
\""
```

Then:
```bash
ssh root@72.60.209.109 "docker exec orc-postgres psql -U postgres -d postgres -c \"SELECT id, status, kind FROM tasks WHERE kind='minion:test' ORDER BY created_at DESC LIMIT 1;\""
```

Expected: `status=queued`, `kind=minion:test`.

- [ ] **Step 4: Verify criterion 2 -- worker marks done within 5s**

Wait 5 seconds, then:

```bash
ssh root@72.60.209.109 "docker exec orc-postgres psql -U postgres -d postgres -c \"SELECT id, status, result FROM tasks WHERE kind='minion:test' ORDER BY created_at DESC LIMIT 1;\""
```

Expected: `status=done`, `result={"ok": true, "echo": "hello"}`.

- [ ] **Step 5: Verify criterion 3 -- /atlas/agents returns completed row**

Get a token via the Atlas PIN screen (use browser DevTools Network tab to copy the token), then:

```bash
curl -s -H "Authorization: Bearer <TOKEN>" \
  https://agentshq.boubacarbarry.com/atlas/agents | python3 -m json.tool
```

Expected: `recent` array contains `minion:test` row with `status: done`.

- [ ] **Step 6: Deploy frontend + verify criterion 4**

```bash
cd d:/Ai_Sandbox/agentsHQ-echo
git push origin main
```

Wait ~60s for GH Actions. Open agentshq.boubacarbarry.com/atlas. Confirm Agents card visible, no console errors.

- [ ] **Step 7: Verify criterion 5 -- depth cap blocks DB write**

```bash
ssh root@72.60.209.109 "docker exec orc-postgres psql -U postgres -d postgres -c 'SELECT COUNT(*) FROM tasks;'"
```

Note the count. Then:

```bash
ssh root@72.60.209.109 "docker exec orc-crewai python3 -c \"
import sys; sys.path.insert(0, '/app')
from skills.coordination.spawner import spawn, SpawnDepthExceeded, MAX_SPAWN_DEPTH
try:
    spawn('minion:test', {}, depth=MAX_SPAWN_DEPTH)
    print('ERROR: no exception raised')
except SpawnDepthExceeded as e:
    print('OK: SpawnDepthExceeded raised:', e)
\""
```

Expected output: `OK: SpawnDepthExceeded raised: spawn depth 5 exceeds cap 5`

Run count again — must be unchanged.

- [ ] **Step 8: Clean up smoke-test handler + update roadmap**

Remove the `_mw.register("minion:test", ...)` line from `app.py` startup.

Update `docs/roadmap/atlas.md`:
- M8b: change header to `✅ SHIPPED 2026-05-10`, add note: "Absorbed into M23 branch. Backend `/atlas/agents` + Active Agents card on Atlas dashboard. Polls `tasks` table directly."
- M23: change header to `✅ SHIPPED 2026-05-10`, add shipped summary.

```bash
cd d:/Ai_Sandbox/agentsHQ
git add orchestrator/app.py docs/roadmap/atlas.md
git commit -m "feat(m23/m8b): ship agent spawning framework + Live Agent Graph [READY]"
git push origin feat/atlas-m23-agent-spawning
```

---

## Self-Review

**Spec coverage:**

| Spec requirement | Task |
|---|---|
| `spawn()` depth cap + kind validation | Task 1 |
| `SpawnDepthExceeded` raises before DB write | Task 1 unit + Task 4 integration |
| `_parent_id` + `_depth` injected into payload | Task 1 (`test_spawn_injects_meta`) |
| `recent_completed_prefix()` | Task 1 Step 5 |
| `minion_worker.run()` background loop | Task 2 |
| `register()` handler registry | Task 2 |
| `_execute` complete on success | Task 2 |
| `_execute` fail on exception | Task 2 |
| Wire `run()` at app startup | Task 3 |
| End-to-end spawn + worker integration | Task 4 |
| `get_agents()` in atlas_dashboard | Task 5 |
| `/atlas/agents` endpoint | Task 5 |
| Atlas HTML Agents card | Task 6 |
| `renderAgents()` JS (XSS-safe) | Task 6 |
| Poll wire-in | Task 6 |
| All 5 success criteria verified on VPS | Task 7 |
| Roadmap M8b + M23 marked shipped | Task 7 Step 8 |

No gaps. Type consistency verified: `spawn()` returns `str`, `claim_next()` returns `dict | None`, `complete(str, dict)` and `fail(str, str)` used consistently throughout.
