import os, sys
sys.path.insert(0, "d:/Ai_Sandbox/agentsHQ/orchestrator")
os.environ.setdefault("NOTION_SECRET", "fake")  # pragma: allowlist secret
os.environ.setdefault("OPENROUTER_API_KEY", "fake")  # pragma: allowlist secret

import inspect


def test_save_memory_tool_in_chat_tools():
    """run_chat() tool list must include save_memory function."""
    import orchestrator.orchestrator as orch
    src = inspect.getsource(orch.run_chat)
    assert "save_memory" in src, "save_memory tool not found in run_chat tool definitions"
