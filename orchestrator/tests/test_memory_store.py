"""Tests for memory_store.py."""
import pytest
from unittest.mock import MagicMock, patch


def test_write_executes_insert(monkeypatch):
    """write() calls cursor.execute with INSERT INTO memory."""
    executed = []

    class FakeCursor:
        def execute(self, sql, params=None):
            executed.append((sql, params))
        def fetchone(self):
            return {"id": 42}

    class FakeConn:
        def cursor(self): return FakeCursor()
        def commit(self): pass
        def close(self): pass

    monkeypatch.setattr("psycopg2.connect", lambda **kw: FakeConn())

    from orchestrator.memory_models import HardRule
    from orchestrator.memory_store import write
    row_id = write(HardRule(
        rule="Never say FGM",
        reason="Brand rule",
        applies_to="all",
    ))
    assert len(executed) == 1
    assert "INSERT INTO memory" in executed[0][0]
    assert row_id == 42


def test_write_rejects_invalid_model():
    """write() raises TypeError if passed a raw dict instead of a memory model."""
    from orchestrator.memory_store import write
    with pytest.raises(TypeError):
        write({"category": "hard_rule", "content": "raw dict"})


def test_query_text_returns_list(monkeypatch):
    """query_text() runs tsvector search and returns list of dicts."""
    fake_rows = [
        {"id": 1, "category": "hard_rule", "title": None,
         "content": "Rule: Never say FGM", "entity_ref": None,
         "pipeline": "general", "source": "claude-code", "created_at": "2026-05-10"},
    ]

    class FakeCursor:
        def execute(self, sql, params=None): pass
        def fetchall(self): return fake_rows

    class FakeConn:
        def cursor(self): return FakeCursor()
        def close(self): pass

    monkeypatch.setattr("psycopg2.connect", lambda **kw: FakeConn())

    from orchestrator.memory_store import query_text
    results = query_text("FGM brand rule")
    assert isinstance(results, list)
    assert len(results) == 1
    assert results[0]["category"] == "hard_rule"


def test_query_filter_by_category(monkeypatch):
    """query_filter() runs WHERE category filter and returns list."""
    fake_rows = [
        {"id": 2, "category": "lead_record", "title": "Elevate Roofing",
         "content": "Company: Elevate Roofing", "entity_ref": "sw:elevate-roofing",
         "pipeline": "sw", "source": "telegram", "created_at": "2026-05-10"},
    ]

    class FakeCursor:
        def execute(self, sql, params=None): pass
        def fetchall(self): return fake_rows

    class FakeConn:
        def cursor(self): return FakeCursor()
        def close(self): pass

    monkeypatch.setattr("psycopg2.connect", lambda **kw: FakeConn())

    from orchestrator.memory_store import query_filter
    results = query_filter(category="lead_record")
    assert len(results) == 1
    assert results[0]["entity_ref"] == "sw:elevate-roofing"


def test_query_text_graceful_empty(monkeypatch):
    """query_text() returns empty list when no rows match."""
    class FakeCursor:
        def execute(self, sql, params=None): pass
        def fetchall(self): return []

    class FakeConn:
        def cursor(self): return FakeCursor()
        def close(self): pass

    monkeypatch.setattr("psycopg2.connect", lambda **kw: FakeConn())

    from orchestrator.memory_store import query_text
    results = query_text("xyzzy nonexistent topic")
    assert results == []
