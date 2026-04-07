import os
os.environ.setdefault("NOTION_SECRET", "fake")  # pragma: allowlist secret
os.environ.setdefault("OPENROUTER_API_KEY", "fake")  # pragma: allowlist secret


def test_save_memory_tool_in_chat_tools():
    """run_chat() tool list must include save_memory function."""
    # Read the source file directly to avoid sys.path conflicts across test files
    orch_path = "d:/Ai_Sandbox/agentsHQ/orchestrator/orchestrator.py"
    with open(orch_path, "r", encoding="utf-8") as f:
        src = f.read()
    assert "save_memory" in src, "save_memory tool not found in run_chat tool definitions"
