from unittest.mock import MagicMock, patch
from datetime import datetime, timezone

import pytest

from skills.inbound_lead.logger import (
    _build_research_summary, _build_properties, create_gmail_draft,
    gmail_draft_url, log_lead,
)
from skills.inbound_lead.schema import (
    DraftedEmail, InboundPayload, ResearchBrief,
)


def _payload(email="jane@acme.com", company="Acme"):
    return InboundPayload(
        name="Jane Doe", email=email, company=company, booking_id="bk_1",
        meeting_time=datetime(2026, 5, 1, 15, 0, tzinfo=timezone.utc),
        source="calendly", raw_company_url="https://acme.com/",
    )


def _brief():
    return ResearchBrief(
        company_domain="acme.com",
        what_they_do="Boutique mid-market consulting.",
        industry_signals=["Mid-market focus"],
        likely_friction=["Margin pressure"],
        conversation_hooks=["What changed last year?"],
        lens_entry_point="Theory of Constraints",
        sources=["https://acme.com/"],
        research_confidence="medium",
    )


def _draft():
    return DraftedEmail(subject="Saw your booking", body_markdown="Short note?")


def test_build_research_summary_embeds_booking_id_and_confidence():
    s = _build_research_summary(_brief(), "bk_123")
    assert "[booking:bk_123]" in s
    assert "Confidence: medium" in s
    assert "Boutique mid-market consulting." in s


def test_build_research_summary_truncates_to_2000():
    b = _brief()
    b.what_they_do = "x" * 3000
    s = _build_research_summary(b, "bk")
    assert len(s) <= 2000


def test_build_properties_title_is_person_not_company():
    """Addendum decision 1: Lead/Company title = person name."""
    props = _build_properties(_payload(), _brief(), "cta", "notes", "Call Booked")
    assert props["Lead/Company"]["title"][0]["text"]["content"] == "Jane Doe"
    assert props["Contact Name"]["rich_text"][0]["text"]["content"] == "Acme"


def test_build_properties_source_is_always_other():
    """Addendum decision 7: Source=Other until Calendly/Formspree options added."""
    props = _build_properties(_payload(), _brief(), "cta", "notes", None)
    assert props["Source"]["select"]["name"] == "Other"


def test_build_properties_omits_status_when_none():
    props = _build_properties(_payload(), _brief(), "cta", "notes", None)
    assert "Status" not in props


def test_build_properties_rejects_invalid_status():
    props = _build_properties(_payload(), _brief(), "cta", "notes", "BogusStatus")
    assert "Status" not in props


def test_gmail_draft_url_format():
    assert gmail_draft_url("r-123") == "https://mail.google.com/mail/u/0/#drafts?compose=r-123"


def test_create_gmail_draft_returns_none_when_gws_missing():
    with patch("skills.inbound_lead.logger.subprocess.run",
               side_effect=FileNotFoundError):
        assert create_gmail_draft("a@b.com", "A", "s", "b") is None


def test_create_gmail_draft_parses_id_on_success():
    fake = MagicMock(returncode=0, stdout='{"id":"d-42","message":{"id":"m-1"}}', stderr="")
    with patch("skills.inbound_lead.logger.subprocess.run", return_value=fake):
        assert create_gmail_draft("a@b.com", "A", "s", "b") == "d-42"


def test_create_gmail_draft_handles_nonzero_exit():
    fake = MagicMock(returncode=1, stdout="", stderr="auth error")
    with patch("skills.inbound_lead.logger.subprocess.run", return_value=fake):
        assert create_gmail_draft("a@b.com", "A", "s", "b") is None


def test_log_lead_new_row_creates_page_and_draft():
    """Happy path: no existing row, Gmail draft succeeds, Notion create succeeds."""
    with patch("skills.inbound_lead.logger.NotionClient") as NC, \
         patch("skills.inbound_lead.logger.create_gmail_draft", return_value="d-1") as mk:
        client = NC.return_value
        client.query_database.return_value = []
        client.create_page.return_value = {"id": "11111111222233334444555566667777"}
        result = log_lead(
            _payload(), _brief(), _draft(),
            database_id="db1", notion_secret="sk",
        )
    assert result.gmail_draft_id == "d-1"
    assert result.notion_page_id == "11111111222233334444555566667777"
    assert "gmail_draft" in result.fields_written
    assert "Status" in result.fields_written
    assert "booking_id_property" in result.fields_skipped
    mk.assert_called_once()


def test_log_lead_existing_row_updates_and_bumps_new_status():
    """Existing row with Status=New bumps to Call Booked."""
    existing = {
        "id": "aaaa1111bbbb2222cccc3333dddd4444",
        "properties": {"Status": {"select": {"name": "New"}}},
    }
    with patch("skills.inbound_lead.logger.NotionClient") as NC, \
         patch("skills.inbound_lead.logger.create_gmail_draft", return_value="d-9"):
        client = NC.return_value
        client.query_database.return_value = [existing]
        result = log_lead(
            _payload(), _brief(), _draft(),
            database_id="db1", notion_secret="sk",
        )
    assert result.notion_page_id == existing["id"]
    assert "Status" in result.fields_written
    args, kwargs = client.update_page.call_args
    assert args[0] == existing["id"]
    assert args[1]["Status"]["select"]["name"] == "Call Booked"


def test_log_lead_existing_row_does_not_bump_proposal_sent():
    """Existing row with later status (Proposal Sent) must not get demoted."""
    existing = {
        "id": "aaaa1111bbbb2222cccc3333dddd4444",
        "properties": {"Status": {"select": {"name": "Proposal Sent"}}},
    }
    with patch("skills.inbound_lead.logger.NotionClient") as NC, \
         patch("skills.inbound_lead.logger.create_gmail_draft", return_value="d-9"):
        client = NC.return_value
        client.query_database.return_value = [existing]
        log_lead(
            _payload(), _brief(), _draft(),
            database_id="db1", notion_secret="sk",
        )
        args, _ = client.update_page.call_args
    assert "Status" not in args[1]


def test_log_lead_gmail_failure_still_writes_notion():
    """Gmail failure: warning logged, Notion write proceeds, fields_skipped has gmail_draft."""
    with patch("skills.inbound_lead.logger.NotionClient") as NC, \
         patch("skills.inbound_lead.logger.create_gmail_draft", return_value=None):
        client = NC.return_value
        client.query_database.return_value = []
        client.create_page.return_value = {"id": "11111111222233334444555566667777"}
        result = log_lead(
            _payload(), _brief(), _draft(),
            database_id="db1", notion_secret="sk",
        )
    assert result.gmail_draft_id is None
    assert "gmail_draft" in result.fields_skipped
    assert result.notion_page_id is not None


def test_log_lead_without_draft_skips_gmail_entirely():
    """Partial case: no draft passed. Logger must not attempt Gmail call."""
    with patch("skills.inbound_lead.logger.NotionClient") as NC, \
         patch("skills.inbound_lead.logger.create_gmail_draft") as mk:
        client = NC.return_value
        client.query_database.return_value = []
        client.create_page.return_value = {"id": "aaa"}
        result = log_lead(
            _payload(), _brief(), draft=None,
            database_id="db1", notion_secret="sk",
        )
    mk.assert_not_called()
    assert "gmail_draft" in result.fields_skipped


def test_log_lead_warns_about_source_other():
    """The source=Other warning must always appear until user adds options."""
    with patch("skills.inbound_lead.logger.NotionClient") as NC, \
         patch("skills.inbound_lead.logger.create_gmail_draft", return_value=None):
        client = NC.return_value
        client.query_database.return_value = []
        client.create_page.return_value = {"id": "aaa"}
        result = log_lead(
            _payload(), _brief(), draft=None,
            database_id="db1", notion_secret="sk",
        )
    assert any("Source set to Other" in w for w in result.warnings)
