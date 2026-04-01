"""Tests for get_llm_metaclaw factory — specifically the fallback behavior."""
import os
import pytest
from unittest.mock import patch, MagicMock
from agents import get_llm_metaclaw


def test_get_llm_metaclaw_disabled_by_env(monkeypatch):
    """When USE_METACLAW=false, should call select_llm directly."""
    monkeypatch.setenv("USE_METACLAW", "false")
    monkeypatch.setenv("OPENROUTER_API_KEY", "test-key")

    with patch("agents.select_llm") as mock_select:
        mock_select.return_value = MagicMock()
        get_llm_metaclaw("consultant", "complex")
        mock_select.assert_called_once_with("consultant", "complex", None)


def test_get_llm_metaclaw_correct_temp_consultant(monkeypatch):
    """Consultant role should get temperature 0.3."""
    monkeypatch.setenv("USE_METACLAW", "true")
    monkeypatch.setenv("OPENROUTER_API_KEY", "test-key")

    with patch("agents.LLM") as mock_llm:
        mock_llm.return_value = MagicMock()
        get_llm_metaclaw("consultant")
        call_kwargs = mock_llm.call_args[1]
        assert call_kwargs["temperature"] == 0.3


def test_get_llm_metaclaw_correct_temp_social(monkeypatch):
    """Social role should get temperature 0.8."""
    monkeypatch.setenv("USE_METACLAW", "true")
    monkeypatch.setenv("OPENROUTER_API_KEY", "test-key")

    with patch("agents.LLM") as mock_llm:
        mock_llm.return_value = MagicMock()
        get_llm_metaclaw("social")
        call_kwargs = mock_llm.call_args[1]
        assert call_kwargs["temperature"] == 0.8


def test_get_llm_metaclaw_proxy_url(monkeypatch):
    """MetaClaw LLM should point at http://orc-metaclaw:30000/v1."""
    monkeypatch.setenv("USE_METACLAW", "true")
    monkeypatch.setenv("OPENROUTER_API_KEY", "test-key")

    with patch("agents.LLM") as mock_llm:
        mock_llm.return_value = MagicMock()
        get_llm_metaclaw("researcher")
        call_kwargs = mock_llm.call_args[1]
        assert call_kwargs["base_url"] == "http://orc-metaclaw:30000/v1"


def test_get_llm_metaclaw_fallback_on_exception(monkeypatch):
    """If LLM() raises, should fall back to select_llm."""
    monkeypatch.setenv("USE_METACLAW", "true")
    monkeypatch.setenv("OPENROUTER_API_KEY", "test-key")

    with patch("agents.LLM", side_effect=OSError("connection refused")):
        with patch("agents.select_llm") as mock_select:
            mock_select.return_value = MagicMock()
            get_llm_metaclaw("consultant", "complex")
            mock_select.assert_called_once_with("consultant", "complex", 0.3)


def test_consulting_agent_uses_metaclaw(monkeypatch):
    """build_consulting_agent must use get_llm_metaclaw when USE_METACLAW=true."""
    monkeypatch.setenv("USE_METACLAW", "true")
    monkeypatch.setenv("OPENROUTER_API_KEY", "test-key")

    with patch("agents.LLM") as mock_llm:
        from crewai.llms.base_llm import BaseLLM
        mock_llm.return_value = MagicMock(spec=BaseLLM)
        from agents import build_consulting_agent
        build_consulting_agent()
        call_kwargs = mock_llm.call_args[1]
        assert "orc-metaclaw" in call_kwargs["base_url"]


def test_researcher_agent_uses_metaclaw(monkeypatch):
    """build_researcher_agent must use get_llm_metaclaw when USE_METACLAW=true."""
    monkeypatch.setenv("USE_METACLAW", "true")
    monkeypatch.setenv("OPENROUTER_API_KEY", "test-key")

    with patch("agents.LLM") as mock_llm:
        from crewai.llms.base_llm import BaseLLM
        mock_llm.return_value = MagicMock(spec=BaseLLM)
        from agents import build_researcher_agent
        build_researcher_agent()
        call_kwargs = mock_llm.call_args[1]
        assert "orc-metaclaw" in call_kwargs["base_url"]


def test_social_agent_uses_metaclaw(monkeypatch):
    """build_social_media_agent must use get_llm_metaclaw when USE_METACLAW=true."""
    monkeypatch.setenv("USE_METACLAW", "true")
    monkeypatch.setenv("OPENROUTER_API_KEY", "test-key")

    with patch("agents.LLM") as mock_llm:
        from crewai.llms.base_llm import BaseLLM
        mock_llm.return_value = MagicMock(spec=BaseLLM)
        from agents import build_social_media_agent
        build_social_media_agent()
        call_kwargs = mock_llm.call_args[1]
        assert "orc-metaclaw" in call_kwargs["base_url"]
