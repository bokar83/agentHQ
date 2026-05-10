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

    async def _run():
        loop = asyncio.get_running_loop()
        await minion_worker._execute(loop, task, handler)

    asyncio.run(_run())

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

    async def _run():
        loop = asyncio.get_running_loop()
        await minion_worker._execute(loop, task, boom)

    asyncio.run(_run())

    assert "t2" in failed
    assert "boom" in failed["t2"]
    assert "t2" not in completed
