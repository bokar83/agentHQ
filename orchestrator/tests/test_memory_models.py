"""Tests for memory_models.py — write contract validation."""
import pytest
from pydantic import ValidationError


def test_agent_lesson_valid():
    from orchestrator.memory_models import AgentLesson
    m = AgentLesson(
        what_happened="Studio VFR bug caused Blotato rejections",
        outcome="FAILED",
        rule="Always encode CFR before uploading to Drive",
        pipeline="studio",
        cost_estimate="$12 wasted",
    )
    assert m.category == "agent_lesson"
    assert m.relevance_boost == 1.5


def test_agent_lesson_invalid_outcome():
    from orchestrator.memory_models import AgentLesson
    with pytest.raises(ValidationError):
        AgentLesson(
            what_happened="x", outcome="WRONG", rule="y", pipeline="studio"
        )


def test_hard_rule_valid():
    from orchestrator.memory_models import HardRule
    m = HardRule(
        rule="Never say FGM — always 1stGen or 1stGen Money",
        reason="Boubacar explicit brand naming rule",
        applies_to="all",
    )
    assert m.category == "hard_rule"
    assert m.relevance_boost == 2.0


def test_lead_record_valid():
    from orchestrator.memory_models import LeadRecord
    m = LeadRecord(
        company="Elevate Roofing",
        contact="Rod",
        gmb_score=3,
        sequence="T1",
        last_touch="Sent audit 2026-05-07",
        response="",
        audit_url="https://geolisted.co/audits/elevate",
    )
    assert m.entity_ref == "sw:elevate-roofing"
    assert m.pipeline == "sw"


def test_lead_record_invalid_sequence():
    from orchestrator.memory_models import LeadRecord
    with pytest.raises(ValidationError):
        LeadRecord(
            company="X", contact="Y", gmb_score=1,
            sequence="T9", last_touch="", response="", audit_url=""
        )


def test_client_record_entity_ref():
    from orchestrator.memory_models import ClientRecord
    m = ClientRecord(
        company="Acme Corp",
        contact="Jane Smith",
        offer="Signal Session",
        stage="discovery",
        last_touch="Call 2026-05-01",
        mrr="",
        notes="",
    )
    assert m.entity_ref == "cw:acme-corp"


def test_project_state_valid():
    from orchestrator.memory_models import ProjectState
    m = ProjectState(
        codename="atlas",
        milestone="M9d-A",
        status="on-track",
        last_action="Deployed gate cron",
        next_action="Wire session start injection",
        blockers="",
    )
    assert m.pipeline == "atlas"
    assert m.category == "project_state"


def test_idea_valid():
    from orchestrator.memory_models import Idea
    m = Idea(
        title="Build roofing landing page",
        context="Came up during SW sprint",
        pipeline="sw",
        priority="soon",
    )
    assert m.category == "idea"
    assert m.relevance_boost == 0.9


def test_asset_valid():
    from orchestrator.memory_models import Asset
    m = Asset(
        title="Elevate Roofing Audit",
        asset_type="report",
        url="https://geolisted.co/audits/elevate",
        pipeline="sw",
        notes="Canonical SW audit template",
    )
    assert m.category == "asset"
    assert m.relevance_boost == 0.8


def test_session_log_valid():
    from orchestrator.memory_models import SessionLog
    m = SessionLog(
        codename="atlas",
        summary="Shipped weekly synthesis crew. 4 tests pass.",
        date="2026-05-10",
    )
    assert m.category == "session_log"
    assert m.relevance_boost == 1.2


def test_to_db_row_has_required_keys():
    from orchestrator.memory_models import HardRule
    m = HardRule(
        rule="Never say FGM",
        reason="Brand rule",
        applies_to="all",
    )
    row = m.to_db_row()
    for key in ("source", "category", "content", "relevance_boost",
                "pipeline", "entity_ref", "tags", "agent_id", "external_id"):
        assert key in row, f"Missing key: {key}"
