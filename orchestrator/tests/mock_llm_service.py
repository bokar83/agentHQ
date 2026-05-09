"""
Mock LLM service for offline orchestrator testing.

Intercepts calls to select_by_capability / get_llm so tests never hit
OpenRouter. Drop this fixture into any test file:

    from orchestrator.tests.mock_llm_service import mock_llm

    def test_something(mock_llm):
        ...  # all LLM calls return scripted responses

Scripted scenarios are keyed by the first user message substring.
Add entries to SCENARIOS for new test cases.

Success criterion: one passing test that does not hit OpenRouter.
Verified by: grep for 'openrouter' in outbound HTTP during pytest run.
"""

import pytest
from unittest.mock import MagicMock, patch

# ---------------------------------------------------------------------------
# Scripted response scenarios
# Keyed by substring match on the first user message content.
# ---------------------------------------------------------------------------

SCENARIOS: dict[str, str] = {
    "summarize":        "This is a mock summary of the requested content.",
    "publish":          "Mock publish response: content queued successfully.",
    "scout":            "Mock scout response: 3 trending topics identified.",
    "digest":           "Mock digest response: morning brief compiled.",
    "score":            "Mock score response: quality score 0.82.",
    "outline":          "Mock outline response: 5-section structure drafted.",
    # fallback
    "__default__":      "Mock LLM response: task completed.",
}


def _pick_response(messages: list[dict]) -> str:
    """Match first user message against SCENARIOS, fall back to default."""
    for msg in messages:
        if msg.get("role") == "user":
            content = str(msg.get("content", "")).lower()
            for key, response in SCENARIOS.items():
                if key != "__default__" and key in content:
                    return response
    return SCENARIOS["__default__"]


# ---------------------------------------------------------------------------
# Pytest fixture — drop into any test module
# ---------------------------------------------------------------------------

class _MockLLM:
    """Callable LLM stand-in. Returns scripted responses based on message content."""

    def __init__(self, model_id: str = "anthropic/claude-haiku-4.5", temperature: float = 0.3):
        self.model = model_id
        self.temperature = temperature

    def __call__(self, messages, **kwargs):
        text = _pick_response(messages if isinstance(messages, list) else [])
        response = MagicMock()
        response.content = text
        response.choices = [MagicMock(message=MagicMock(content=text))]
        response.usage = MagicMock(prompt_tokens=10, completion_tokens=20, total_tokens=30)
        return response


@pytest.fixture
def mock_llm():
    """
    Patches select_by_capability and get_llm for the duration of one test.
    No OpenRouter calls are made.
    """
    mock_model_id = "anthropic/claude-haiku-4.5"
    instance = _MockLLM(mock_model_id)

    with (
        patch("agents.select_by_capability", return_value=mock_model_id),
        patch("agents.get_llm", return_value=instance),
    ):
        yield instance


# ---------------------------------------------------------------------------
# Smoke test — verifies the fixture itself works
# Run: pytest orchestrator/tests/mock_llm_service.py -v
# ---------------------------------------------------------------------------

def test_mock_llm_returns_scripted_response(mock_llm):
    """Fixture returns a response without hitting OpenRouter."""
    messages = [{"role": "user", "content": "please summarize this document"}]
    result = mock_llm(messages)
    assert "mock summary" in result.content.lower()
    assert result.usage.total_tokens == 30


def test_mock_llm_fallback_response(mock_llm):
    """Unmatched message returns default response."""
    messages = [{"role": "user", "content": "zyx_unrecognized_prompt_xyz"}]
    result = mock_llm(messages)
    assert "mock llm response" in result.content.lower()


def test_mock_llm_has_model_attribute(mock_llm):
    """LLM object carries model ID."""
    assert mock_llm.model == "anthropic/claude-haiku-4.5"
