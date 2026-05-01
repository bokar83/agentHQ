"""Structural tests for newsletter crew Task 6 enhancements."""
from __future__ import annotations

import ast
from pathlib import Path


CREWS_PATH = Path(__file__).resolve().parents[1] / "crews.py"


def _newsletter_function() -> ast.FunctionDef:
    module = ast.parse(CREWS_PATH.read_text(encoding="utf-8", errors="replace"))
    for node in module.body:
        if isinstance(node, ast.FunctionDef) and node.name == "build_newsletter_crew":
            return node
    raise AssertionError("build_newsletter_crew not found")


def _assigned_names(function_node: ast.FunctionDef) -> list[str]:
    names: list[str] = []
    for node in function_node.body:
        if isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name):
                    names.append(target.id)
    return names


def _return_nodes(function_node: ast.FunctionDef) -> list[ast.Return]:
    returns: list[ast.Return] = []
    for node in function_node.body:
        if isinstance(node, ast.If):
            for nested in node.body:
                if isinstance(nested, ast.Return):
                    returns.append(nested)
        elif isinstance(node, ast.Return):
            returns.append(node)
    return returns


def _crew_list_names(return_node: ast.Return, keyword_name: str) -> list[str]:
    assert isinstance(return_node.value, ast.Call)
    for keyword in return_node.value.keywords:
        if keyword.arg == keyword_name:
            assert isinstance(keyword.value, ast.List)
            return [elt.id for elt in keyword.value.elts if isinstance(elt, ast.Name)]
    raise AssertionError(f"{keyword_name} keyword not found")


def test_build_newsletter_crew_accepts_metadata_param():
    function_node = _newsletter_function()

    assert [arg.arg for arg in function_node.args.args] == ["user_request", "metadata"]
    assert len(function_node.args.defaults) == 1
    default = function_node.args.defaults[0]
    assert isinstance(default, ast.Constant)
    assert default.value is None


def test_newsletter_crew_inserts_research_verification_before_qa():
    function_node = _newsletter_function()

    assigned_names = _assigned_names(function_node)
    assert "researcher" in assigned_names
    assert "task_verify_sources" in assigned_names
    assert assigned_names.index("task_write") < assigned_names.index("task_verify_sources")
    assert assigned_names.index("task_verify_sources") < assigned_names.index("task_qa")

    task_qa_assign = next(
        node for node in function_node.body
        if isinstance(node, ast.Assign)
        and any(isinstance(target, ast.Name) and target.id == "task_qa" for target in node.targets)
    )
    assert isinstance(task_qa_assign.value, ast.Call)
    qa_context = next(keyword.value for keyword in task_qa_assign.value.keywords if keyword.arg == "context")
    assert isinstance(qa_context, ast.List)
    assert [elt.id for elt in qa_context.elts if isinstance(elt, ast.Name)] == ["task_verify_sources"]


def test_newsletter_crew_adds_researcher_and_verify_task_to_both_branches():
    function_node = _newsletter_function()

    returns = _return_nodes(function_node)
    assert len(returns) == 2
    for return_node in returns:
        agents = _crew_list_names(return_node, "agents")
        tasks = _crew_list_names(return_node, "tasks")
        assert "researcher" in agents
        assert "task_verify_sources" in tasks
