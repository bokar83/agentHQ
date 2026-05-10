"""Tests for /remember and /query Telegram command handlers."""
import pytest
from unittest.mock import patch, MagicMock


def test_remember_ignores_non_matching_command():
    from orchestrator.handlers_commands import _cmd_remember
    result = _cmd_remember("/digest", "chat123")
    assert result is False


def test_remember_without_args_sends_usage():
    sent = []
    with patch("orchestrator.handlers_commands._send_memory", side_effect=lambda cid, msg: sent.append(msg)):
        from orchestrator.handlers_commands import _cmd_remember
        result = _cmd_remember("/remember", "chat123")
    assert result is True
    assert any("Usage" in m for m in sent)


def test_remember_writes_idea_row(monkeypatch):
    written = []
    monkeypatch.setattr("orchestrator.handlers_commands._memory_write", lambda m: written.append(m) or 99)
    sent = []
    monkeypatch.setattr("orchestrator.handlers_commands._send_memory", lambda cid, msg: sent.append(msg))
    from orchestrator.handlers_commands import _cmd_remember
    result = _cmd_remember("/remember Build a roofing page for SW", "chat123")
    assert result is True
    assert len(written) == 1
    assert written[0].category == "idea"
    assert "roofing" in written[0].title.lower() or "roofing" in written[0].content.lower()
    assert any("Saved" in m or "saved" in m for m in sent)


def test_query_ignores_non_matching_command():
    from orchestrator.handlers_commands import _cmd_query
    result = _cmd_query("/digest", "chat123")
    assert result is False


def test_query_without_args_sends_usage():
    sent = []
    with patch("orchestrator.handlers_commands._send_memory", side_effect=lambda cid, msg: sent.append(msg)):
        from orchestrator.handlers_commands import _cmd_query
        result = _cmd_query("/query", "chat123")
    assert result is True
    assert any("Usage" in m for m in sent)


def test_query_text_returns_synthesis(monkeypatch):
    monkeypatch.setattr(
        "orchestrator.handlers_commands._memory_query_text",
        lambda text, **kw: [{"category": "hard_rule", "title": None,
                              "content": "Rule: Never say FGM", "entity_ref": None,
                              "pipeline": "general", "source": "seed", "created_at": "2026-05-10"}]
    )
    monkeypatch.setattr(
        "orchestrator.handlers_commands._memory_synthesize",
        lambda rows, question: "Never say FGM — use 1stGen instead."
    )
    sent = []
    monkeypatch.setattr("orchestrator.handlers_commands._send_memory", lambda cid, msg: sent.append(msg))
    from orchestrator.handlers_commands import _cmd_query
    result = _cmd_query("/query what are my FGM rules", "chat123")
    assert result is True
    assert any("1stGen" in m or "FGM" in m for m in sent)


def test_query_filter_syntax(monkeypatch):
    monkeypatch.setattr(
        "orchestrator.handlers_commands._memory_query_filter",
        lambda **kw: [{"category": "lead_record", "title": "Elevate Roofing",
                        "content": "Company: Elevate Roofing\nContact: Rod",
                        "entity_ref": "sw:elevate-roofing", "pipeline": "sw",
                        "source": "telegram", "created_at": "2026-05-10"}]
    )
    sent = []
    monkeypatch.setattr("orchestrator.handlers_commands._send_memory", lambda cid, msg: sent.append(msg))
    from orchestrator.handlers_commands import _cmd_query
    result = _cmd_query("/query --filter category=lead_record", "chat123")
    assert result is True
    assert any("Elevate" in m for m in sent)


def test_query_llm_failure_returns_raw_rows(monkeypatch):
    monkeypatch.setattr(
        "orchestrator.handlers_commands._memory_query_text",
        lambda text, **kw: [{"category": "hard_rule", "title": None,
                              "content": "Rule: Never say FGM", "entity_ref": None,
                              "pipeline": "general", "source": "seed", "created_at": "2026-05-10"}]
    )
    def _raise(*a, **kw):
        raise RuntimeError("LLM unavailable")
    monkeypatch.setattr("orchestrator.handlers_commands._memory_synthesize", _raise)
    sent = []
    monkeypatch.setattr("orchestrator.handlers_commands._send_memory", lambda cid, msg: sent.append(msg))
    from orchestrator.handlers_commands import _cmd_query
    result = _cmd_query("/query FGM rules", "chat123")
    assert result is True
    assert len(sent) >= 1


def test_query_synthesis_flag(monkeypatch):
    """--synthesis flag returns weekly synthesis."""
    sent = []
    monkeypatch.setattr("orchestrator.handlers_commands._send_memory", lambda cid, msg: sent.append(msg))

    import psycopg2
    class FakeCursor:
        def execute(self, sql, params=None): pass
        def fetchone(self): return ("2026-05-10", "## PROJECT STATUS\nAtlas is on track.")
    class FakeConn:
        def cursor(self): return FakeCursor()
        def close(self): pass
    monkeypatch.setattr("psycopg2.connect", lambda **kw: FakeConn())

    from orchestrator.handlers_commands import _cmd_query
    result = _cmd_query("/query --synthesis", "chat123")
    assert result is True
    assert any("synthesis" in m.lower() or "PROJECT STATUS" in m for m in sent)
