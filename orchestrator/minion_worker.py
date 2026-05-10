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
