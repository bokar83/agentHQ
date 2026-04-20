from unittest.mock import patch
from datetime import datetime, timezone

import pytest

from skills.inbound_lead.runner import run_inbound_lead
from skills.inbound_lead.schema import DraftedEmail, LogResult, ResearchBrief
from skills.inbound_lead.drafter import DraftResult


def _valid_payload():
    return {
        "name": "Jane Doe",
        "email": "jane@acme.com",
        "company": "Acme",
        "booking_id": "bk_1",
        "meeting_time": "2026-05-01T15:00:00+00:00",
        "source": "calendly",
    }


def _brief():
    return ResearchBrief(
        company_domain="acme.com",
        what_they_do="Consulting.",
        industry_signals=[], likely_friction=[], conversation_hooks=[],
        lens_entry_point="Lean", sources=[], research_confidence="medium",
    )


def _clean_draft_result():
    return DraftResult(
        email=DraftedEmail(subject="Hi", body_markdown="Short note?"),
        status="clean", lint_errors=[],
    )


def _success_log(notion_id="page-1", gmail_id="d-1"):
    return LogResult(
        notion_page_id=notion_id,
        notion_row_url=f"https://www.notion.so/{notion_id}",
        gmail_draft_id=gmail_id,
        gmail_draft_url=f"https://mail.google.com/.../compose={gmail_id}",
        fields_written=["Lead/Company", "Email"],
        fields_skipped=["booking_id_property"],
        warnings=[],
    )


@pytest.fixture
def env(monkeypatch):
    monkeypatch.setenv("NOTION_API_KEY", "sk_fake")
    monkeypatch.setenv("NOTION_FORGE_PIPELINE_DB_ID", "db_fake")


def test_invalid_payload_returns_failed_without_side_effects(env):
    """Missing required field (booking_id): failed status, no research attempted."""
    bad = {"name": "J", "email": "x@y.com", "source": "calendly"}
    with patch("skills.inbound_lead.researcher.research") as r, \
         patch("skills.inbound_lead.idempotency.has_been_enriched") as h:
        result = run_inbound_lead(bad)
    r.assert_not_called()
    h.assert_not_called()
    assert result.status == "failed"
    assert "Invalid payload" in (result.error or "")


def test_missing_env_returns_failed(monkeypatch):
    """No NOTION_API_KEY or NOTION_FORGE_PIPELINE_DB_ID: abort with failed status."""
    monkeypatch.delenv("NOTION_API_KEY", raising=False)
    monkeypatch.delenv("NOTION_SECRET", raising=False)
    monkeypatch.delenv("NOTION_TOKEN", raising=False)
    monkeypatch.delenv("NOTION_FORGE_PIPELINE_DB_ID", raising=False)
    result = run_inbound_lead(_valid_payload())
    assert result.status == "failed"
    assert "NOTION" in (result.error or "")


def test_happy_path_fresh_enrichment(env):
    """No prior row: research, draft, log, mark_enriched. Status=enriched."""
    with patch("skills.inbound_lead.idempotency.has_been_enriched", return_value=None), \
         patch("skills.inbound_lead.researcher.research", return_value=_brief()) as r, \
         patch("skills.inbound_lead.drafter.draft_email", return_value=_clean_draft_result()) as d, \
         patch("skills.inbound_lead.logger.log_lead", return_value=_success_log()) as lg, \
         patch("skills.inbound_lead.idempotency.mark_enriched") as me:
        result = run_inbound_lead(_valid_payload())
    assert result.status == "enriched"
    assert result.brief.research_confidence == "medium"
    assert result.email.subject == "Hi"
    assert result.log.gmail_draft_id == "d-1"
    r.assert_called_once()
    d.assert_called_once()
    lg.assert_called_once()
    me.assert_called_once()


def test_rebook_path_skips_research_and_draft(env):
    """Prior enrichment exists: skip research + draft, log with fallback brief."""
    prior = {"email": "jane@acme.com", "first_booking": "bk_0", "status": "enriched"}
    with patch("skills.inbound_lead.idempotency.has_been_enriched", return_value=prior), \
         patch("skills.inbound_lead.researcher.research") as r, \
         patch("skills.inbound_lead.drafter.draft_email") as d, \
         patch("skills.inbound_lead.logger.log_lead", return_value=_success_log(gmail_id=None)) as lg, \
         patch("skills.inbound_lead.idempotency.mark_rebook") as mr:
        result = run_inbound_lead(_valid_payload())
    assert result.status == "rebook_update"
    r.assert_not_called()
    d.assert_not_called()
    lg.assert_called_once()
    mr.assert_called_once()


def test_partial_when_draft_lints_dirty_but_notion_succeeds(env):
    """Drafter returns status=partial: runner marks overall partial."""
    partial_draft = DraftResult(
        email=DraftedEmail(subject="Hi", body_markdown="circle back?"),
        status="partial", lint_errors=["sales_phrase:circle back"],
    )
    with patch("skills.inbound_lead.idempotency.has_been_enriched", return_value=None), \
         patch("skills.inbound_lead.researcher.research", return_value=_brief()), \
         patch("skills.inbound_lead.drafter.draft_email", return_value=partial_draft), \
         patch("skills.inbound_lead.logger.log_lead", return_value=_success_log()), \
         patch("skills.inbound_lead.idempotency.mark_enriched"):
        result = run_inbound_lead(_valid_payload())
    assert result.status == "partial"


def test_partial_when_gmail_fails(env):
    """Notion write succeeds, Gmail fails: partial."""
    log_no_gmail = LogResult(
        notion_page_id="p-1", notion_row_url="u",
        gmail_draft_id=None, gmail_draft_url=None,
        fields_written=["Lead/Company"], fields_skipped=["gmail_draft"],
        warnings=["Gmail draft creation failed; Notion row still written."],
    )
    with patch("skills.inbound_lead.idempotency.has_been_enriched", return_value=None), \
         patch("skills.inbound_lead.researcher.research", return_value=_brief()), \
         patch("skills.inbound_lead.drafter.draft_email", return_value=_clean_draft_result()), \
         patch("skills.inbound_lead.logger.log_lead", return_value=log_no_gmail), \
         patch("skills.inbound_lead.idempotency.mark_enriched"):
        result = run_inbound_lead(_valid_payload())
    assert result.status == "partial"


def test_researcher_exception_degrades_to_fallback_brief_and_continues(env):
    """If researcher raises, runner uses fallback brief and still drafts + logs."""
    with patch("skills.inbound_lead.idempotency.has_been_enriched", return_value=None), \
         patch("skills.inbound_lead.researcher.research", side_effect=RuntimeError("firecrawl dead")), \
         patch("skills.inbound_lead.drafter.draft_email", return_value=_clean_draft_result()) as d, \
         patch("skills.inbound_lead.logger.log_lead", return_value=_success_log()), \
         patch("skills.inbound_lead.idempotency.mark_enriched"):
        result = run_inbound_lead(_valid_payload())
    d.assert_called_once()
    assert result.brief.research_confidence == "none"
    assert result.status == "enriched"  # still enriched because draft+log ok


def test_notion_create_failure_marks_failed(env):
    """Notion didn't write (no page_id) and no draft: failed."""
    empty_log = LogResult(
        notion_page_id=None, notion_row_url=None,
        gmail_draft_id=None, gmail_draft_url=None,
        fields_written=[], fields_skipped=["gmail_draft"],
        warnings=["Notion create failed: 500"],
    )
    with patch("skills.inbound_lead.idempotency.has_been_enriched", return_value=None), \
         patch("skills.inbound_lead.researcher.research", return_value=_brief()), \
         patch("skills.inbound_lead.drafter.draft_email", return_value=_clean_draft_result()), \
         patch("skills.inbound_lead.logger.log_lead", return_value=empty_log), \
         patch("skills.inbound_lead.idempotency.mark_enriched") as me:
        result = run_inbound_lead(_valid_payload())
    me.assert_not_called()
    assert result.status in ("failed", "partial")
