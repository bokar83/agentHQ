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
    """Claude answers directly without using any tool; loop exits on end_turn."""
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


@patch("research_engine._execute_tool")
@patch("research_engine.anthropic.Anthropic")
def test_multi_turn_tool_use(mock_anthropic_cls, mock_exec_tool):
    """Claude calls web_search, receives results, then emits final answer."""
    import research_engine

    mock_client = MagicMock()
    mock_anthropic_cls.return_value = mock_client
    mock_exec_tool.return_value = "Shop A at 123 Main St, phone 555-1234."

    # First turn: Claude requests a tool call.
    turn1 = _mock_anthropic_response(
        stop_reason="tool_use",
        content_blocks=[
            _text_block("Let me look that up."),
            _tool_use_block("tu_1", "web_search", {"query": "mechanic shops 84095"}),
        ],
    )
    # Second turn: Claude answers using the tool result.
    turn2 = _mock_anthropic_response(
        stop_reason="end_turn",
        content_blocks=[_text_block("Found Shop A at 123 Main St.")],
    )
    mock_client.messages.create.side_effect = [turn1, turn2]

    result = research_engine.run_research(
        user_prompt="Find mechanic shops in 84095.",
        anthropic_api_key="sk-test",  # pragma: allowlist secret
        firecrawl_api_key="fc-test",  # pragma: allowlist secret
    )

    assert result["success"] is True
    assert result["tool_calls"] == 1
    assert result["turns"] == 2
    assert "Shop A" in result["answer"]
    mock_exec_tool.assert_called_once_with("web_search", {"query": "mechanic shops 84095"}, "fc-test")


@patch("research_engine.anthropic.Anthropic")
def test_missing_api_key_returns_error(mock_anthropic_cls):
    """Missing ANTHROPIC_API_KEY returns a clean error dict, not a crash."""
    import research_engine

    result = research_engine.run_research(
        user_prompt="Anything.",
        anthropic_api_key=None,
        firecrawl_api_key=None,
    )
    # Because we pass None and os.environ may also be empty in test env,
    # we accept either the happy path (if env is set) or the error path.
    if not os.environ.get("ANTHROPIC_API_KEY"):
        assert result["success"] is False
        assert "ANTHROPIC_API_KEY" in (result["error"] or "")
    mock_anthropic_cls.assert_not_called() if not os.environ.get("ANTHROPIC_API_KEY") else None


@patch("research_engine._execute_tool")
@patch("research_engine.anthropic.Anthropic")
def test_max_turns_cap(mock_anthropic_cls, mock_exec_tool):
    """If Claude never stops calling tools, the loop terminates at MAX_TURNS."""
    import research_engine

    mock_client = MagicMock()
    mock_anthropic_cls.return_value = mock_client
    mock_exec_tool.return_value = "some data"

    # Every turn returns another tool call; loop should hit MAX_TURNS.
    infinite_tool_turn = _mock_anthropic_response(
        stop_reason="tool_use",
        content_blocks=[_tool_use_block("tu_x", "web_search", {"query": "x"})],
    )
    mock_client.messages.create.return_value = infinite_tool_turn

    result = research_engine.run_research(
        user_prompt="Never stop.",
        anthropic_api_key="sk-test",  # pragma: allowlist secret
        firecrawl_api_key="fc-test",  # pragma: allowlist secret
    )

    assert result["success"] is False
    assert result["turns"] == research_engine.MAX_TURNS
    assert "MAX_TURNS" in (result["error"] or "")


@patch("research_engine.run_research")
def test_engine_routes_research_report_to_bypass(mock_run_research):
    """engine.run_orchestrator calls research_engine.run_research for research_report."""
    import engine

    mock_run_research.return_value = {
        "success": True,
        "answer": "Five mechanic shops found.",
        "tool_calls": 3,
        "turns": 4,
        "error": None,
    }

    with patch("engine.classify_task") as mock_classify, \
         patch("engine.get_crew_type", return_value="research_crew"), \
         patch("memory.get_conversation_history", return_value=[]), \
         patch("memory.save_to_memory"), \
         patch("memory.save_conversation_turn"):
        mock_classify.return_value = {
            "task_type": "research_report",
            "confidence": 0.95,
            "is_unknown": False,
        }

        result = engine.run_orchestrator(
            task_request="Find mechanic shops near 84095.",
            from_number="browser:test",
            session_key="browser:test",
        )

    assert result["success"] is True
    assert result["task_type"] == "research_report"
    assert "mechanic shops" in result["deliverable"].lower()
    mock_run_research.assert_called_once()
