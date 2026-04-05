import pytest
from unittest.mock import patch, MagicMock
from skills.forge_cli.forge import build_parser, run_command


def test_log_command_parses():
    parser = build_parser()
    args = parser.parse_args(["log", "Built homepage", "--agent", "Designer", "--status", "Success"])
    assert args.command == "log"
    assert args.message == "Built homepage"
    assert args.agent == "Designer"
    assert args.status == "Success"


def test_task_add_parses():
    parser = build_parser()
    args = parser.parse_args(["task", "add", "Wire Hunter", "--priority", "P1", "--due", "2026-04-12"])
    assert args.task_command == "add"
    assert args.title == "Wire Hunter"
    assert args.priority == "P1"
    assert args.due == "2026-04-12"


def test_pipeline_add_parses():
    parser = build_parser()
    args = parser.parse_args(["pipeline", "add", "Acme Corp", "--value", "5000", "--status", "New"])
    assert args.pipeline_command == "add"
    assert args.company == "Acme Corp"
    assert args.value == 5000
    assert args.status == "New"


def test_revenue_parses():
    parser = build_parser()
    args = parser.parse_args(["revenue", "2500", "--source", "Consulting", "--buyer", "Acme Corp"])
    assert args.command == "revenue"
    assert args.amount == 2500.0
    assert args.source == "Consulting"
    assert args.buyer == "Acme Corp"


def test_content_idea_parses():
    parser = build_parser()
    args = parser.parse_args(["content", "idea", "AI leadership post", "--platform", "LinkedIn,X", "--topic", "AI,Leadership"])
    assert args.content_command == "idea"
    assert args.title == "AI leadership post"
    assert args.platform == "LinkedIn,X"
    assert args.topic == "AI,Leadership"
