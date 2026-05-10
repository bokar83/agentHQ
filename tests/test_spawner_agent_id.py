from __future__ import annotations
import os, uuid
from unittest.mock import patch, MagicMock
from skills.coordination.spawner import build_agent_env

def test_build_agent_env_injects_agent_id():
    env = build_agent_env(branch="feat/test-branch", parent_id="parent-abc")
    assert "CLAUDE_AGENT_ID" in env
    assert env["CLAUDE_AGENT_ID"]
    assert "feat/test-branch" in env.get("CLAUDE_AGENT_BRANCH", "")

def test_build_agent_env_unique_ids():
    env1 = build_agent_env(branch="feat/a", parent_id="p1")
    env2 = build_agent_env(branch="feat/b", parent_id="p1")
    assert env1["CLAUDE_AGENT_ID"] != env2["CLAUDE_AGENT_ID"]

def test_build_agent_env_inherits_parent():
    env = build_agent_env(branch="feat/x", parent_id="parent-xyz")
    assert env.get("CLAUDE_PARENT_AGENT_ID") == "parent-xyz"
