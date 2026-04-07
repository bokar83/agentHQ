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
