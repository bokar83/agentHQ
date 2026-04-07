"""Tests for memory architecture — cross-session learning system."""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'orchestrator'))

import pytest
from unittest.mock import patch, MagicMock


def test_query_memory_uses_default_collection():
    """query_memory with no collection param uses agentshq_memory."""
    mock_client = MagicMock()
    mock_result = MagicMock()
    mock_result.payload = {"task_type": "research_report", "summary": "Test summary", "date": "2026-04-07"}
    mock_client.search.return_value = [mock_result]

    with patch("memory.get_qdrant_client", return_value=mock_client), \
         patch("memory.get_embedding", return_value=[0.1] * 1536):
        from memory import query_memory
        results = query_memory("test query")
        call_kwargs = mock_client.search.call_args[1]
        assert call_kwargs["collection_name"] == "agentshq_memory"
        assert len(results) == 1


def test_query_memory_uses_custom_collection():
    """query_memory with collection param uses the specified collection."""
    mock_client = MagicMock()
    mock_client.search.return_value = []

    with patch("memory.get_qdrant_client", return_value=mock_client), \
         patch("memory.get_embedding", return_value=[0.1] * 1536):
        from memory import query_memory
        query_memory("test query", collection="agentshq_learnings")
        call_kwargs = mock_client.search.call_args[1]
        assert call_kwargs["collection_name"] == "agentshq_learnings"


def test_extract_and_save_learnings_returns_true_on_success():
    """extract_and_save_learnings saves to Qdrant and Postgres without error."""
    import os
    mock_client = MagicMock()
    mock_client.get_collection.return_value = True

    mock_openai_instance = MagicMock()
    mock_choice = MagicMock()
    mock_choice.message.content = "Pattern: Use 3-section structure with context, findings, recommendations."
    mock_openai_instance.chat.completions.create.return_value = MagicMock(choices=[mock_choice])

    mock_conn = MagicMock()
    mock_cur = MagicMock()
    mock_conn.cursor.return_value = mock_cur

    test_env = {"MEMORY_LEARNING_ENABLED": "true", "OPENROUTER_API_KEY": "test-key"}  # pragma: allowlist secret
    with patch.dict(os.environ, test_env), \
         patch("memory.get_qdrant_client", return_value=mock_client), \
         patch("memory.get_embedding", return_value=[0.1] * 1536), \
         patch("memory._pg_conn", return_value=mock_conn):
        import importlib
        import memory as mem_module
        with patch.object(mem_module, "_call_extraction_llm", return_value="Pattern: Use 3-section structure."):
            from memory import extract_and_save_learnings
            result = extract_and_save_learnings(
                task_request="Write a research report on AI trends",
                task_type="research_report",
                result_summary="The report covered 5 key trends...",
                learning_type="pattern"
            )
            assert result is True
            assert mock_client.upsert.called


def test_extract_and_save_learnings_returns_false_when_disabled():
    """extract_and_save_learnings returns False when MEMORY_LEARNING_ENABLED is not set."""
    import os
    with patch.dict(os.environ, {"MEMORY_LEARNING_ENABLED": "false"}):
        from memory import extract_and_save_learnings
        result = extract_and_save_learnings(
            task_request="test",
            task_type="research_report",
            result_summary="test output",
        )
        assert result is False


def test_extract_negative_lesson_saves_with_negative_type():
    """extract_negative_lesson saves a lesson with lesson_type=negative."""
    import os
    mock_client = MagicMock()
    mock_client.get_collection.return_value = True

    mock_conn = MagicMock()
    mock_cur = MagicMock()
    mock_conn.cursor.return_value = mock_cur

    with patch.dict(os.environ, {"MEMORY_LEARNING_ENABLED": "true"}), \
         patch("memory.get_qdrant_client", return_value=mock_client), \
         patch("memory.get_embedding", return_value=[0.1] * 1536), \
         patch("memory._pg_conn", return_value=mock_conn):
        import memory as mem_module
        with patch.object(mem_module, "_call_extraction_llm", return_value="Avoid using complex tables; use bullet lists instead."):
            from memory import extract_negative_lesson
            result = extract_negative_lesson(
                feedback="The table wasn't done well, too hard to read",
                task_type="research_report",
                original_output="Here is the research with a complex table...",
            )
            assert result is True
            upsert_call = mock_client.upsert.call_args
            point = upsert_call[1]["points"][0]
            assert point.payload["lesson_type"] == "negative"
            assert point.payload["source"] == "user_critique"


def test_memory_gated_task_types_constant_exists():
    """MEMORY_GATED_TASK_TYPES contains expected task types and excludes simple ones."""
    import sys, os
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'orchestrator'))
    from orchestrator import MEMORY_GATED_TASK_TYPES
    assert "research_report" in MEMORY_GATED_TASK_TYPES
    assert "consulting_deliverable" in MEMORY_GATED_TASK_TYPES
    assert "copywriting" in MEMORY_GATED_TASK_TYPES
    assert "gws_task" not in MEMORY_GATED_TASK_TYPES
    assert "hunter_task" not in MEMORY_GATED_TASK_TYPES
    assert "chat" not in MEMORY_GATED_TASK_TYPES


def test_is_praise_detects_explicit_praise():
    """_is_praise returns True for short explicit praise messages."""
    import sys, os
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'orchestrator'))
    from orchestrator import _is_praise
    assert _is_praise("good job") is True
    assert _is_praise("Great work!") is True
    assert _is_praise("well done") is True
    assert _is_praise("perfect") is True
    assert _is_praise("I want a research report on AI trends") is False
    assert _is_praise("") is False


def test_is_feedback_on_prior_job_within_window():
    """_is_feedback_on_prior_job returns True when critique signals present and job is recent."""
    import sys, os
    from datetime import datetime, timedelta
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'orchestrator'))
    from orchestrator import _is_feedback_on_prior_job, _last_completed_job

    _last_completed_job["12345"] = {
        "job_id": "abc",
        "task_type": "research_report",
        "task_request": "research AI trends",
        "result_summary": "found 5 trends",
        "delivered_at": datetime.utcnow() - timedelta(minutes=5),
    }
    assert _is_feedback_on_prior_job("the table wasn't done well", "12345") is True
    assert _is_feedback_on_prior_job("I want a new report on fintech", "12345") is False


def test_list_lessons_returns_rows():
    """list_lessons() returns lesson rows from Postgres agent_learnings."""
    with patch("memory._pg_conn") as mock_pg:
        mock_conn = MagicMock()
        mock_cur = MagicMock()
        mock_cur.fetchall.return_value = [
            (1, "research_report", "pattern", "Use 3-section structure.", "auto", "2026-04-07")
        ]
        mock_conn.cursor.return_value = mock_cur
        mock_pg.return_value = mock_conn
        from memory import list_lessons
        rows = list_lessons(task_type="research_report")
        assert len(rows) == 1
        assert rows[0]["task_type"] == "research_report"
        assert rows[0]["id"] == 1


def test_purge_lesson_sets_status():
    """purge_lesson() updates lesson_status to purged."""
    with patch("memory._pg_conn") as mock_pg:
        mock_conn = MagicMock()
        mock_cur = MagicMock()
        mock_cur.rowcount = 1
        mock_conn.cursor.return_value = mock_cur
        mock_pg.return_value = mock_conn
        from memory import purge_lesson
        result = purge_lesson(lesson_id=42)
        assert result is True
