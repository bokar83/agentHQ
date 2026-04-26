import os
os.environ.setdefault("NOTION_SECRET", "fake")  # pragma: allowlist secret
os.environ.setdefault("OPENROUTER_API_KEY", "fake")  # pragma: allowlist secret


def test_save_memory_tool_in_chat_tools():
    """run_chat() tool list must include save_memory function."""
    orch_path = "d:/Ai_Sandbox/agentsHQ/orchestrator/handlers_chat.py"
    with open(orch_path, "r", encoding="utf-8") as f:
        src = f.read()
    assert "save_memory" in src, "save_memory tool not found in run_chat tool definitions"


def test_shortcut_classify_notion_capture():
    import sys
    sys.path.insert(0, "d:/Ai_Sandbox/agentsHQ/orchestrator")
    from handlers import _shortcut_classify
    result = _shortcut_classify("Add to my ideas list: build a voice coach")
    assert result == "notion_capture"


def test_shortcut_classify_gws_short_message():
    import sys
    sys.path.insert(0, "d:/Ai_Sandbox/agentsHQ/orchestrator")
    from handlers import _shortcut_classify
    result = _shortcut_classify("what's on my calendar")
    assert result == "gws_task"


def test_shortcut_classify_returns_none_for_chat():
    import sys
    sys.path.insert(0, "d:/Ai_Sandbox/agentsHQ/orchestrator")
    from handlers import _shortcut_classify
    result = _shortcut_classify("hey how are you")
    assert result is None


def test_has_email_followup_metadata_extraction():
    import sys
    sys.path.insert(0, "d:/Ai_Sandbox/agentsHQ/orchestrator")
    from router import extract_metadata
    meta = extract_metadata("Research AI trends and send me an email about it")
    assert meta["has_email_followup"] is True


def test_no_email_followup_for_plain_task():
    import sys
    sys.path.insert(0, "d:/Ai_Sandbox/agentsHQ/orchestrator")
    from router import extract_metadata
    meta = extract_metadata("Research AI trends")
    assert meta["has_email_followup"] is False
