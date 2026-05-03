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


def test_switch_codex_model(tmp_path):
    """Codex config.toml model key is updated, other keys preserved."""
    config = tmp_path / "config.toml"
    config.write_text('model = "gpt-5.5"\npersonality = "pragmatic"\n')

    providers_with_codex = tmp_path / "providers_codex.json"
    providers_with_codex.write_text(json.dumps({
        "openrouter": {
            "label": "OpenRouter",
            "claude": {},
            "codex": {"model": "openai/gpt-4o"}
        }
    }))

    switch_provider.switch_codex(
        provider_key="openrouter",
        providers_path=str(providers_with_codex),
        config_path=str(config),
    )
    content = config.read_text()
    assert 'model = "openai/gpt-4o"' in content
    assert 'personality = "pragmatic"' in content
    assert 'model = "gpt-5.5"' not in content


def test_switch_codex_missing_config_creates_file(tmp_path):
    config = tmp_path / "config.toml"
    providers_with_codex = tmp_path / "providers_codex.json"
    providers_with_codex.write_text(json.dumps({
        "openrouter": {
            "label": "OpenRouter",
            "codex": {"model": "openai/gpt-4o"}
        }
    }))
    switch_provider.switch_codex("openrouter", str(providers_with_codex), str(config))
    content = config.read_text()
    assert 'model = "openai/gpt-4o"' in content


def test_unresolved_env_var_raises(tmp_settings, providers_json, monkeypatch):
    monkeypatch.delenv("OPENROUTER_API_KEY", raising=False)
    with pytest.raises(SystemExit):
        switch_provider.switch_claude("openrouter", str(providers_json), str(tmp_settings))
