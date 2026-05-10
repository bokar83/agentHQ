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
