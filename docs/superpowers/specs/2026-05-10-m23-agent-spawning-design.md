# M23: Agent-to-Agent Spawning & Delegation

**Date:** 2026-05-10
**Branch:** `feat/atlas-m23-agent-spawning`
**Status:** Approved for implementation

---

## What We Are Building

A lightweight spawning framework that lets any orchestrator crew dispatch a focused sub-agent (Minion) to run a targeted task asynchronously inside the existing `orc-crewai` container. The parent gets a `task_id` back immediately. The Minion runs in a thread pool, writes its result to the `tasks` table, and optionally pings Telegram on completion. A new `/atlas/agents` endpoint feeds a Live Agent Graph panel on the Atlas dashboard.

This is M23 and M8b combined into one branch. M8b backend + frontend ship alongside M23 because the graph has real data the moment the first Minion spawns.

---

## Architecture

### Components

| File | Role |
|---|---|
| `skills/coordination/spawner.py` | `spawn()` — validates depth cap, enqueues Minion task |
| `orchestrator/minion_worker.py` | Background worker loop — `claim_next` → `run_in_executor` → `complete/fail` |
| `orchestrator/app.py` | Startup: `asyncio.create_task(minion_worker.run())` (~3 lines) |
| `orchestrator/atlas_dashboard.py` | `get_agents()` — wraps `list_running()` + `recent_completed()` |
| `orchestrator/app.py` | `/atlas/agents` GET endpoint |
| `agentsHQ-echo/thepopebot/chat-ui/atlas.js` | `renderAgents()` card function |
| `agentsHQ-echo/thepopebot/chat-ui/atlas.html` | Agents card HTML |

No new dependencies. No new containers. No new DB tables (uses existing `tasks` table).

### Data Flow

```
Parent crew calls spawn(kind, payload, parent_id, depth)
  → spawner.py validates depth < 5
  → enqueue(kind, payload_with_meta) writes row to tasks table
  → returns task_id immediately (non-blocking)

minion_worker.run() loop (background thread, started at app startup)
  → claim_next("minion:*") atomically pops oldest queued Minion task
  → loop.run_in_executor(None, handler) runs handler in thread pool
  → complete(task_id, result) or fail(task_id, error)
  → optional Telegram ping on completion

/atlas/agents endpoint
  → atlas_dashboard.get_agents()
  → list_running() + recent_completed(since=3600)
  → returns JSON {running: [...], recent: [...]}

Atlas panel polls /atlas/agents every 30s
  → renderAgents() renders table of active + recent Minions
```

---

## spawner.py

```python
# skills/coordination/spawner.py

MAX_SPAWN_DEPTH = 5

class SpawnDepthExceeded(RuntimeError):
    pass

def spawn(kind: str, payload: dict, parent_id: str | None = None, depth: int = 0) -> str:
    """Enqueue a Minion task. Returns task_id. Non-blocking.

    kind must be prefixed "minion:" (e.g., "minion:triage", "minion:research").
    depth is the current nesting level — callers pass their own depth + 1.
    Raises SpawnDepthExceeded if depth >= MAX_SPAWN_DEPTH.
    """
    if depth >= MAX_SPAWN_DEPTH:
        raise SpawnDepthExceeded(f"spawn depth {depth} exceeds cap {MAX_SPAWN_DEPTH}")
    if not kind.startswith("minion:"):
        raise ValueError(f"Minion kind must start with 'minion:' — got '{kind}'")
    full_payload = {"_parent_id": parent_id, "_depth": depth, **payload}
    from skills.coordination import enqueue
    return enqueue(kind, full_payload)
```

---

## minion_worker.py

```python
# orchestrator/minion_worker.py

import asyncio
import logging
from skills.coordination import claim_next, complete, fail

logger = logging.getLogger("agentsHQ.minion_worker")

# Handler registry: kind -> callable(payload) -> dict
# Add new Minion types here. Plain dict, no dynamic loading.
_HANDLERS: dict[str, callable] = {}

def register(kind: str, handler) -> None:
    _HANDLERS[kind] = handler

async def run() -> None:
    """Background loop. Runs for the lifetime of the app."""
    loop = asyncio.get_running_loop()
    while True:
        for kind, handler in list(_HANDLERS.items()):
            task = claim_next(kind, holder="minion_worker", ttl_seconds=300)
            if task:
                logger.info("minion_worker: claimed %s task_id=%s", kind, task["id"])
                asyncio.create_task(_execute(loop, task, handler))
        await asyncio.sleep(2)

async def _execute(loop, task: dict, handler) -> None:
    try:
        result = await loop.run_in_executor(None, lambda: handler(task["payload"]))
        complete(task["id"], result or {})
        logger.info("minion_worker: completed task_id=%s", task["id"])
    except Exception as exc:
        fail(task["id"], str(exc))
        logger.error("minion_worker: failed task_id=%s error=%s", task["id"], exc)
```

---

## app.py changes (startup only)

```python
# In lifespan startup block, after existing heartbeat registration:
import minion_worker as _mw
asyncio.create_task(_mw.run())
```

---

## skills/coordination/__init__.py addition

One new helper (prefix query — `recent_completed` requires exact kind match):

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

## atlas_dashboard.py addition

```python
def get_agents() -> dict:
    """Live Agent Graph: running + recently completed Minion tasks."""
    from skills.coordination import list_running, recent_completed_prefix
    running = list_running()
    recent = recent_completed_prefix("minion:", since_seconds=3600, limit=50)
    return {"running": running, "recent": recent}
```

---

## /atlas/agents endpoint

```python
@app.get("/atlas/agents")
async def atlas_agents(_auth=Depends(verify_chat_token)):
    return JSONResponse(_atd.get_agents())
```

---

## Atlas Frontend (atlas.js + atlas.html)

New card added to the main grid. Same pattern as every existing card.

`atlas.html` addition inside `#cards-col`:
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

`atlas.js` addition in the `refreshAll()` or equivalent polling function:
```javascript
try { renderAgents(await apiFetch('/atlas/agents')); } catch (_) {}
```

`renderAgents(d)` renders a simple table: kind / claimed_by / status / lease_expires_at for running rows, plus a "recent completions" sub-list.

Poll interval: 30s (same as other cards).

---

## Depth Cap

- Default: 5 levels
- Enforced in `spawn()` before any DB write
- `SpawnDepthExceeded` is a `RuntimeError` — callers catch and log, do not retry

---

## Error Handling

- `spawn()` raises on bad input — callers must handle
- `minion_worker._execute()` catches all exceptions, calls `fail()`, logs — never crashes the worker loop
- `/atlas/agents` returns empty lists on DB error (same `try/except` as other dashboard endpoints)

---

## Success Criteria (all must pass before claiming shipped)

1. `spawn("minion:test", {"msg": "hello"})` returns a task_id string. Row appears in `tasks` table with `status='queued'` within 1 second.
2. `minion_worker` picks up the task, runs registered handler, marks `status='done'` within 5 seconds of enqueue.
3. `GET /atlas/agents` (with valid token) returns JSON with the completed row in `recent`.
4. Atlas dashboard at agentshq.boubacarbarry.com/atlas shows the Agents card with no console errors.
5. `spawn("minion:test", {}, depth=5)` raises `SpawnDepthExceeded` before writing any DB row (verify via `SELECT COUNT(*) FROM tasks` before and after — count unchanged).

---

## What This Unlocks

- M8b Live Agent Graph: satisfied (backend endpoint + frontend panel ship in this branch)
- M23 trigger gates: all met after this ships
- M24 Hermes Self-Healing: gates 1+2 met. M24 adds worktree sandbox isolation as its own deliverable.

---

## Out of Scope (M23)

- Worktree / sandbox isolation per Minion (M24)
- Event-driven message bus / Postgres LISTEN-NOTIFY (M25)
- Minion-to-Minion communication (M25)
- Dynamic handler loading / plugin system (explicitly rejected — registry stays a plain dict)
