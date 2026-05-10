"""Tests for orchestrator/notion_sync_crew.py"""
import pytest
from unittest.mock import MagicMock


def test_extract_page_title_from_notion_page():
    from orchestrator.notion_sync_crew import _extract_title
    page = {"properties": {"Name": {"title": [{"text": {"content": "My Idea"}}]}}}
    assert _extract_title(page) == "My Idea"


def test_extract_page_title_fallback():
    from orchestrator.notion_sync_crew import _extract_title
    page = {"properties": {}}
    assert _extract_title(page) == ""


def test_sync_ideas_returns_count(monkeypatch):
    monkeypatch.setattr(
        "orchestrator.notion_sync_crew._fetch_notion_pages",
        lambda nc, db_id: [
            {"id": "abc123", "properties": {"Name": {"title": [{"text": {"content": "Build roofing page"}}]}}},
        ]
    )
    written = []
    monkeypatch.setattr("orchestrator.notion_sync_crew._write_memory", lambda m: written.append(m) or 99)
    from orchestrator.notion_sync_crew import sync_ideas
    count = sync_ideas(nc=MagicMock(), db_id="test-db")
    assert count == 1
    assert written[0].category == "idea"
    assert "roofing" in written[0].title.lower() or "roofing" in written[0].content.lower()


def test_sync_ideas_skips_empty_titles(monkeypatch):
    monkeypatch.setattr(
        "orchestrator.notion_sync_crew._fetch_notion_pages",
        lambda nc, db_id: [
            {"id": "abc", "properties": {}},  # no title
        ]
    )
    written = []
    monkeypatch.setattr("orchestrator.notion_sync_crew._write_memory", lambda m: written.append(m) or 99)
    from orchestrator.notion_sync_crew import sync_ideas
    count = sync_ideas(nc=MagicMock(), db_id="test-db")
    assert count == 0
    assert len(written) == 0


def test_sync_is_nonfatal_on_exception(monkeypatch):
    monkeypatch.setattr(
        "orchestrator.notion_sync_crew._fetch_notion_pages",
        lambda nc, db_id: (_ for _ in ()).throw(Exception("Notion down"))
    )
    from orchestrator.notion_sync_crew import sync_ideas
    count = sync_ideas(nc=MagicMock(), db_id="test-db")
    assert count == 0
