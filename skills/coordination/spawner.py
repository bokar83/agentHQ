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
