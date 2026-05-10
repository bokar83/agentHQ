# skills/coordination/spawner.py
from __future__ import annotations
import uuid as _uuid
import os as _os

MAX_SPAWN_DEPTH = 5


def build_agent_env(branch: str, parent_id: str = "") -> dict:
    """Build environment dict for a spawned agent subprocess."""
    env = {**_os.environ}
    env["CLAUDE_AGENT_ID"] = _uuid.uuid4().hex
    env["CLAUDE_AGENT_BRANCH"] = branch
    if parent_id:
        env["CLAUDE_PARENT_AGENT_ID"] = parent_id
    return env


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
