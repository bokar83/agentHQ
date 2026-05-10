"""Tests for memory_distillation_crew.py"""
from pathlib import Path


def test_read_all_memory_files_excludes_digest_and_index(tmp_path):
    """read_all_memory_files excludes MEMORY.md, MEMORY-DIGEST.md, and .original."""
    (tmp_path / "feedback_foo.md").write_text("some content")
    (tmp_path / "project_bar.md").write_text("project content")
    (tmp_path / "MEMORY.md").write_text("index")
    (tmp_path / "MEMORY-DIGEST.md").write_text("old digest")
    (tmp_path / "MEMORY.original.md").write_text("original")
    from orchestrator.memory_distillation_crew import read_all_memory_files
    results = read_all_memory_files(memory_dir=tmp_path)
    names = [r[0] for r in results]
    assert "feedback_foo.md" in names
    assert "project_bar.md" in names
    assert "MEMORY.md" not in names
    assert "MEMORY-DIGEST.md" not in names
    assert "MEMORY.original.md" not in names


def test_build_distillation_prompt_requests_five_facts():
    """Prompt asks for exactly 5 highest-leverage facts."""
    from orchestrator.memory_distillation_crew import build_distillation_prompt
    prompt = build_distillation_prompt(
        snippets=[("foo.md", "content"), ("bar.md", "more content")],
        today="2026-05-25"
    )
    assert "5" in prompt
    assert "highest" in prompt.lower()
    assert "leverage" in prompt.lower()


def test_build_distillation_prompt_includes_date():
    """Prompt contains today's date."""
    from orchestrator.memory_distillation_crew import build_distillation_prompt
    prompt = build_distillation_prompt(
        snippets=[("foo.md", "content")],
        today="2026-05-25"
    )
    assert "2026-05-25" in prompt


def test_save_to_postgres_calls_execute(monkeypatch):
    """save_to_postgres inserts into memory_distillation with correct params."""
    import orchestrator.memory_distillation_crew as mdc

    executed = []

    class FakeCursor:
        def execute(self, sql, params=None):
            executed.append((sql, params))

    class FakeConn:
        def cursor(self): return FakeCursor()
        def commit(self): pass
        def close(self): pass

    monkeypatch.setattr("psycopg2.connect", lambda **kw: FakeConn())
    mdc.save_to_postgres("## Digest\nfact 1", "2026-05-25")
    assert len(executed) == 1
    sql, params = executed[0]
    assert "memory_distillation" in sql
    assert params[0] == "2026-05-25"
    assert "fact 1" in params[1]
