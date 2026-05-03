"""Tests for skills/switch-provider/switch_provider.py"""
import json
import os
import sys
import tempfile
from pathlib import Path

import pytest

# Add skills/switch-provider to path so we can import the script
sys.path.insert(0, str(Path(__file__).parent.parent / "skills" / "switch-provider"))
import switch_provider


@pytest.fixture
def tmp_settings(tmp_path):
    """A temp ~/.claude/settings.json with an existing env block."""
    settings = tmp_path / "settings.json"
    settings.write_text(json.dumps({
        "env": {
            "EXISTING_KEY": "existing_value",
            "ANTHROPIC_BASE_URL": "https://old.provider.com/api",
            "ANTHROPIC_AUTH_TOKEN": "old_token"
        },
        "permissions": {"allow": ["Bash(*)"]}
    }, indent=2))
    return settings


@pytest.fixture
def providers_json(tmp_path):
    """A temp providers.json."""
    p = tmp_path / "providers.json"
    p.write_text(json.dumps({
        "openrouter": {
            "label": "OpenRouter",
            "claude": {
                "ANTHROPIC_BASE_URL": "https://openrouter.ai/api",
                "ANTHROPIC_AUTH_TOKEN": "$OPENROUTER_API_KEY"
            }
        },
        "anthropic-official": {
            "label": "Anthropic Official",
            "claude": {}
        }
    }))
    return p


def test_switch_claude_to_openrouter(tmp_settings, providers_json, monkeypatch):
    monkeypatch.setenv("OPENROUTER_API_KEY", "sk-or-test-123")
    switch_provider.switch_claude(
        provider_key="openrouter",
        providers_path=str(providers_json),
        settings_path=str(tmp_settings),
    )
    result = json.loads(tmp_settings.read_text())
    assert result["env"]["ANTHROPIC_BASE_URL"] == "https://openrouter.ai/api"
    assert result["env"]["ANTHROPIC_AUTH_TOKEN"] == "sk-or-test-123"
    assert result["env"]["EXISTING_KEY"] == "existing_value"
    assert result["permissions"]["allow"] == ["Bash(*)"]


def test_switch_claude_to_official_removes_base_url(tmp_settings, providers_json, monkeypatch):
    switch_provider.switch_claude(
        provider_key="anthropic-official",
        providers_path=str(providers_json),
        settings_path=str(tmp_settings),
    )
    result = json.loads(tmp_settings.read_text())
    assert "ANTHROPIC_BASE_URL" not in result["env"]
    assert "ANTHROPIC_AUTH_TOKEN" not in result["env"]
    assert result["env"]["EXISTING_KEY"] == "existing_value"


def test_switch_is_idempotent(tmp_settings, providers_json, monkeypatch):
    monkeypatch.setenv("OPENROUTER_API_KEY", "sk-or-test-123")
    switch_provider.switch_claude("openrouter", str(providers_json), str(tmp_settings))
    switch_provider.switch_claude("openrouter", str(providers_json), str(tmp_settings))
    result = json.loads(tmp_settings.read_text())
    assert result["env"]["ANTHROPIC_BASE_URL"] == "https://openrouter.ai/api"


def test_missing_settings_file_creates_minimal_config(tmp_path, providers_json, monkeypatch):
    monkeypatch.setenv("OPENROUTER_API_KEY", "sk-or-test-123")
    settings = tmp_path / "settings.json"
    assert not settings.exists()
    switch_provider.switch_claude("openrouter", str(providers_json), str(settings))
    result = json.loads(settings.read_text())
    assert result["env"]["ANTHROPIC_BASE_URL"] == "https://openrouter.ai/api"


def test_corrupted_settings_file_creates_minimal_config(tmp_path, providers_json, monkeypatch):
    monkeypatch.setenv("OPENROUTER_API_KEY", "sk-or-test-123")
    settings = tmp_path / "settings.json"
    settings.write_text("{{not valid json}}")
    switch_provider.switch_claude("openrouter", str(providers_json), str(settings))
    result = json.loads(settings.read_text())
    assert result["env"]["ANTHROPIC_BASE_URL"] == "https://openrouter.ai/api"


def test_unknown_provider_raises(tmp_settings, providers_json):
    with pytest.raises(SystemExit):
        switch_provider.switch_claude("nonexistent", str(providers_json), str(tmp_settings))
