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
