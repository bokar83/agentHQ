# LangGraph Checkpoint-SQLite Pattern

**Source:** TauricResearch/TradingAgents (71k stars, v0.2.4)
**Absorbed:** 2026-05-08
**Status:** REFERENCE DRAFT — not deployed. Atlas task required before this is DONE.
**Atlas task:** "Add LangGraph checkpoint-sqlite to coding agent pipeline so state survives container restarts" — not DONE until VPS test run passes.

---

## What this solves

LangGraph graphs that run inside a container lose all intermediate state if the container crashes or is restarted mid-graph. `SqliteSaver` persists every node's output to disk. On next run with the same `thread_id`, the graph resumes from the last completed node — not from START.

agentsHQ gap: if a coding agent dies mid-task (crash, OOM, restart), the work is lost. This pattern closes that gap.

---

## Core pattern (~50 lines, extracted from TradingAgents)

### 1. State schema — inherit `MessagesState`, add typed fields

```python
from typing import Annotated, TypedDict
from langgraph.graph import MessagesState

class AgentState(MessagesState):
    # MessagesState provides: messages: list[BaseMessage]
    task_id: Annotated[str, "Unique task identifier"]
    branch: Annotated[str, "Git branch being worked on"]
    current_file: Annotated[str, "File being edited right now"]
    result: Annotated[str, "Final output"]
    # Add domain-specific fields here
```

### 2. Checkpointer — per-task SQLite DB, deterministic thread_id

```python
import hashlib
import sqlite3
from contextlib import contextmanager
from pathlib import Path
from langgraph.checkpoint.sqlite import SqliteSaver

DATA_DIR = Path.home() / ".agentshq" / "cache" / "checkpoints"

def _db_path(task_id: str) -> Path:
    safe = "".join(c if c.isalnum() else "_" for c in task_id)
    return DATA_DIR / f"{safe}.db"

def thread_id(task_id: str, run_date: str) -> str:
    """Deterministic ID — same task+date always resumes same checkpoint."""
    raw = f"{task_id}:{run_date}"
    return hashlib.sha256(raw.encode()).hexdigest()[:16]

@contextmanager
def get_checkpointer(task_id: str):
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(_db_path(task_id)), check_same_thread=False)
    saver = SqliteSaver(conn)
    saver.setup()  # creates tables if not exist
    try:
        yield saver
    finally:
        conn.close()

def clear_checkpoint(task_id: str, run_date: str) -> None:
    """Call after successful completion to avoid stale resumption."""
    db = _db_path(task_id)
    if not db.exists():
        return
    tid = thread_id(task_id, run_date)
    conn = sqlite3.connect(str(db))
    conn.execute("DELETE FROM checkpoints WHERE thread_id = ?", (tid,))
    conn.execute("DELETE FROM writes WHERE thread_id = ?", (tid,))
    conn.commit()
    conn.close()
```

### 3. Graph compilation — recompile with saver per run

```python
from langgraph.graph import StateGraph

workflow = StateGraph(AgentState)
# ... add_node, add_edge calls here ...

def run_graph(task_id: str, run_date: str, init_state: dict, checkpoint_enabled: bool = False):
    if checkpoint_enabled:
        with get_checkpointer(task_id) as saver:
            graph = workflow.compile(checkpointer=saver)
            config = {
                "recursion_limit": 100,
                "configurable": {"thread_id": thread_id(task_id, run_date)}
            }
            final_state = graph.invoke(init_state, config=config, stream_mode="values")
        clear_checkpoint(task_id, run_date)  # clean up on success
    else:
        graph = workflow.compile()
        final_state = graph.invoke(init_state)
    return final_state
```

### 4. Conditional routing — read last message's tool_calls

```python
def should_continue(state: AgentState) -> str:
    last = state["messages"][-1]
    if hasattr(last, "tool_calls") and last.tool_calls:
        return "tools"       # loop back: agent requested a tool
    return "next_node"       # move forward: agent finished this step
```

### 5. Debate loop — count-gated alternation

```python
class DebateState(TypedDict):
    bull_history: str
    bear_history: str
    count: int
    current_speaker: str  # "bull" | "bear"

MAX_ROUNDS = 2  # each side speaks MAX_ROUNDS times

def route_debate(state: AgentState) -> str:
    ds = state["debate_state"]
    if ds["count"] >= 2 * MAX_ROUNDS:
        return "judge"
    return "bear" if ds["current_speaker"] == "bull" else "bull"
```

---

## Key invariants from TradingAgents source

1. **Per-task DB, not shared DB.** One SQLite file per task/ticker. Avoids write contention when tasks run concurrently.
2. **Clear on success, not on start.** `clear_checkpoint` fires AFTER successful completion. On failure, the checkpoint survives for the next retry.
3. **Recompile for each run.** Don't cache the compiled graph across runs when using a checkpointer — the saver context must be live during invoke.
4. **`stream_mode="values"` for full state.** Each stream chunk is the full current state dict, not just the delta. Cheaper to read `final_state` than to reassemble from deltas.
5. **`thread_id` is deterministic.** Same task+date = same thread_id = resume. Different date = different thread_id = fresh run. This is the restart-vs-fresh control knob.

---

## Atlas integration point

Target: coding agent pipeline (`orchestrator/gate_agent.py` or future `orchestrator/coding_agent.py`).

The coding agent runs multi-step: claim branch → edit files → run tests → commit. If it crashes after edits but before commit, work is lost. With this pattern, it resumes at the last completed node.

Steps to wire:
1. Add `langgraph-checkpoint-sqlite` to `requirements.txt`.
2. Implement `checkpointer.py` in `orchestrator/` using the pattern above.
3. Wrap coding agent graph's `invoke` call with `get_checkpointer(branch_name)`.
4. Set `checkpoint_enabled=True` for long-running tasks (>3 nodes).
5. Verify: crash a coding agent mid-graph, restart container, confirm it resumes from checkpoint.

**Acceptance gate:** task is not DONE until one full crash-resume cycle is verified on VPS.
