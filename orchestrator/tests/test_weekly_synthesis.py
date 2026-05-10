"""Tests for weekly_synthesis_crew.py"""
import pytest
from unittest.mock import patch, MagicMock
from pathlib import Path


def test_read_memory_files_returns_list(tmp_path):
    """read_memory_files returns a list of (filename, content) tuples."""
    (tmp_path / "feedback_foo.md").write_text("---\nname: foo\n---\nsome content")
    (tmp_path / "MEMORY.md").write_text("index file")
    from orchestrator.weekly_synthesis_crew import read_memory_files
    results = read_memory_files(memory_dir=tmp_path, limit=10)
    assert isinstance(results, list)
    # MEMORY.md index excluded, feedback_foo.md included
    names = [r[0] for r in results]
    assert "feedback_foo.md" in names
    assert "MEMORY.md" not in names


def test_read_roadmap_logs_returns_text(tmp_path):
    """read_roadmap_logs extracts dated log entries from roadmap files."""
    roadmap = tmp_path / "atlas.md"
    roadmap.write_text("# Atlas\n\n### 2026-05-08:\nShipped thing.\n\n### 2026-04-01:\nOld thing.")
    from orchestrator.weekly_synthesis_crew import read_roadmap_logs
    text = read_roadmap_logs(roadmap_dir=tmp_path, days=10)
    assert "2026-05-08" in text
    assert "Shipped thing" in text


def test_build_synthesis_prompt_contains_required_sections():
    """Prompt includes all 4 required section headers."""
    from orchestrator.weekly_synthesis_crew import build_synthesis_prompt
    prompt = build_synthesis_prompt(
        memory_snippets=[("foo.md", "some content")],
        roadmap_text="log entry",
        today="2026-05-11"
    )
    for section in ["PROJECT STATUS", "OPEN LOOPS", "EMERGING PATTERNS", "SUGGESTED FOCUS"]:
        assert section in prompt


def test_format_notion_page_properties():
    """format_notion_page returns properties dict with Name and Date."""
    from orchestrator.weekly_synthesis_crew import format_notion_page
    props, children = format_notion_page(content="## Test\nSome text.", date_iso="2026-05-11")
    assert "Name" in props
    assert "Date" in props
    assert isinstance(children, list)
    assert len(children) > 0
