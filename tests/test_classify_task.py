"""Tests for skills/switch-provider/classify_task.py"""
import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent / "skills" / "switch-provider"))
import classify_task


def _msg(text: str) -> dict:
    """Build a minimal UserPromptSubmit hook payload."""
    return {"prompt": text}


# --- Manual override detection ---

def test_override_switch_to_openrouter():
    assert classify_task.detect_override("switch to openrouter") == "openrouter"

def test_override_use_anthropic():
    assert classify_task.detect_override("use anthropic") == "anthropic-official"

def test_override_change_to_gemini():
    assert classify_task.detect_override("change to gemini") == "openrouter"

def test_override_switch_codex():
    assert classify_task.detect_override("switch to codex") == "codex-suggest"

def test_override_none_when_no_match():
    assert classify_task.detect_override("help me design a banner") is None


# --- Keyword classification ---

def test_classify_design_returns_anthropic():
    assert classify_task.classify("help me design a landing page") == "anthropic-official"

def test_classify_creative_returns_anthropic():
    assert classify_task.classify("write brand copy for my startup") == "anthropic-official"

def test_classify_frontend_returns_anthropic():
    assert classify_task.classify("build a UI component with tailwind") == "anthropic-official"

def test_classify_wireframe_returns_anthropic():
    assert classify_task.classify("create a wireframe for the homepage") == "anthropic-official"

def test_classify_backend_returns_openrouter():
    assert classify_task.classify("fix this bug in my Python function") == "openrouter"

def test_classify_refactor_returns_openrouter():
    assert classify_task.classify("refactor the database module") == "openrouter"

def test_classify_research_returns_openrouter():
    assert classify_task.classify("research the best vector database options") == "openrouter"

def test_classify_analyze_returns_openrouter():
    assert classify_task.classify("analyze this dataset and summarize it") == "openrouter"

def test_classify_default_returns_openrouter():
    assert classify_task.classify("what time is it in Denver") == "openrouter"

def test_classify_case_insensitive():
    assert classify_task.classify("DESIGN a Logo for me") == "anthropic-official"

def test_classify_override_wins_over_keyword():
    assert classify_task.classify("switch to openrouter for this design task") == "openrouter"


# --- Hook payload parsing ---

def test_parse_prompt_from_hook_payload():
    payload = json.dumps({"prompt": "help me design a banner"})
    text = classify_task.parse_prompt(payload)
    assert text == "help me design a banner"

def test_parse_prompt_missing_key_returns_empty():
    payload = json.dumps({"other": "data"})
    text = classify_task.parse_prompt(payload)
    assert text == ""

def test_parse_prompt_invalid_json_returns_empty():
    text = classify_task.parse_prompt("not json at all")
    assert text == ""
