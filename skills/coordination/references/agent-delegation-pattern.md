# Agent-to-Agent Delegation Pattern

**Unlock condition:** This doc earns its place when one Atlas agent cites it as the
design reference for its first `enqueue`→`claim_next` handoff. Delete if unused after
2 sessions.

---

## The Pattern

When an agent needs work done that it cannot or should not do itself:

1. **Decompose** — break the goal into typed work items (one concern per item)
2. **Enqueue** — write each item to the coordination ledger with a `kind` label
3. **Move on** — the dispatching agent does not wait; it completes its own claim
4. **Claim** — a downstream agent (same or different process) calls `claim_next(kind)`
5. **Complete** — downstream agent calls `complete(task_id, result)` when done

This is the agentsHQ answer to "respawn and give each other tasks."

---

## Concrete API (skills/coordination/__init__.py)

```python
from skills.coordination import claim, complete, enqueue, claim_next, fail

# Dispatching agent — e.g. morning_runner deciding a script needs a render
job = enqueue(
    kind="studio:render",                  # typed — downstream knows what this is
    payload={"script_id": "abc123", "channel": "griot"},
    priority=0,                            # optional; lower = higher priority
)
# morning_runner moves on immediately — no blocking

# Rendering agent — separate process or next heartbeat cycle
task = claim_next(kind="studio:render", holder="studio-render-agent", ttl_seconds=600)
if task is None:
    return  # nothing queued, skip cycle

try:
    result = render_video(task["payload"])
    complete(task["id"], result={"drive_url": result})
except Exception as e:
    fail(task["id"])   # returns to queue for retry if TTL expires
```

---

## Kind naming convention

```
<domain>:<verb>          # studio:render, sw:outreach, atlas:verify
<domain>:<noun>-<verb>   # griot:post-approve, cw:pdf-generate
```

Keep kinds stable — they are the contract between the dispatching and consuming agent.

---

## When to use vs. direct call

| Situation | Use |
|-----------|-----|
| Same agent, same process, blocking is fine | Direct function call |
| Different heartbeat cycles or processes | `enqueue` / `claim_next` |
| Agent needs to hand off and forget | `enqueue` / `claim_next` |
| Human must approve before downstream acts | `approval_queue` (separate) |
| Knowledge claim another agent will act on | `data/verification_queue.md` (Atlas M5+) |

---

## Atlas milestone gate

Full agent-to-agent respawn (M-delegation) is gated on M5 Chairman crew.
Until then, use this pattern for one-way handoffs only (dispatch + forget).
Two-way (agent A waits on agent B's result) requires the async job API in atlas.md.
