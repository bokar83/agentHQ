"""Tests for the CrewAI-bypass research engine."""
import os
import sys
from unittest.mock import MagicMock, patch

# Add orchestrator to path so 'import research_engine' works the same way
# as production (handlers.py uses flat imports inside the container).
ORCH_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if ORCH_DIR not in sys.path:
    sys.path.insert(0, ORCH_DIR)


def _mock_anthropic_response(stop_reason, content_blocks):
    resp = MagicMock()
    resp.stop_reason = stop_reason
    resp.content = content_blocks
    return resp


def _text_block(text):
    b = MagicMock()
    b.type = "text"
    b.text = text
    return b


def _tool_use_block(tool_id, name, input_dict):
    b = MagicMock()
    b.type = "tool_use"
    b.id = tool_id
    b.name = name
    b.input = input_dict
    return b


@patch("research_engine.anthropic.Anthropic")
def test_single_turn_no_tool_calls(mock_anthropic_cls):
    """Claude answers directly without using any tool -- loop exits on end_turn."""
    import research_engine

    mock_client = MagicMock()
    mock_anthropic_cls.return_value = mock_client
    mock_client.messages.create.return_value = _mock_anthropic_response(
        stop_reason="end_turn",
        content_blocks=[_text_block("Here is the direct answer.")],
    )

    result = research_engine.run_research(
        user_prompt="What is 2+2?",
        anthropic_api_key="sk-test",  # pragma: allowlist secret
        firecrawl_api_key="fc-test",  # pragma: allowlist secret
    )

    assert result["success"] is True
    assert "direct answer" in result["answer"].lower()
    assert result["tool_calls"] == 0
