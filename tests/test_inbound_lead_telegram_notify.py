from datetime import datetime, timezone

from skills.inbound_lead.schema import (
    DraftedEmail, InboundPayload, InboundRoutineResult, LogResult, ResearchBrief,
)
from skills.inbound_lead.telegram_notify import format_inbound_telegram_message


def _payload():
    return InboundPayload(
        name="Jane Doe", email="jane@acme.com", company="Acme", booking_id="bk_1",
        meeting_time=datetime(2026, 5, 1, 15, 0, tzinfo=timezone.utc),
        source="calendly", raw_company_url="https://acme.com/",
    )


def _brief(confidence="medium"):
    return ResearchBrief(
        company_domain="acme.com", what_they_do="Consulting.",
        industry_signals=[], likely_friction=["Margin pressure", "Scaling"],
        conversation_hooks=[], lens_entry_point="Lean", sources=[],
        research_confidence=confidence,
    )


def _log_ok():
    return LogResult(
        notion_page_id="abc",
        notion_row_url="https://www.notion.so/abc",
        gmail_draft_id="d-1",
        gmail_draft_url="https://mail.google.com/.../compose=d-1",
        fields_written=["Lead/Company"], fields_skipped=["booking_id_property"],
        warnings=[],
    )


def test_message_contains_status_and_contact_info():
    result = InboundRoutineResult(
        status="enriched", payload=_payload(), brief=_brief(),
        email=DraftedEmail(subject="Saw your booking", body_markdown="short"),
        log=_log_ok(),
    )
    msg = format_inbound_telegram_message(result)
    assert "enriched" in msg
    assert "Jane Doe" in msg and "jane@acme.com" in msg
    assert "Acme" in msg
    assert "Research: medium" in msg
    assert "Notion:" in msg and "abc" in msg
    assert "Gmail draft:" in msg
    assert "Saw your booking" in msg


def test_message_includes_meeting_time():
    result = InboundRoutineResult(
        status="enriched", payload=_payload(), brief=_brief(),
        email=None, log=_log_ok(),
    )
    msg = format_inbound_telegram_message(result)
    assert "2026-05-01" in msg


def test_failed_status_includes_error_and_no_brief():
    result = InboundRoutineResult(
        status="failed", payload=_payload(),
        error="Missing NOTION_API_KEY or NOTION_FORGE_PIPELINE_DB_ID in environment.",
    )
    msg = format_inbound_telegram_message(result)
    assert "failed" in msg
    assert "NOTION_API_KEY" in msg


def test_partial_status_surfaces_skipped_and_warnings():
    log = LogResult(
        notion_page_id="abc", notion_row_url="https://www.notion.so/abc",
        gmail_draft_id=None, gmail_draft_url=None,
        fields_written=["Lead/Company"],
        fields_skipped=["gmail_draft", "booking_id_property"],
        warnings=["Source set to Other; add Calendly + Formspree options."],
    )
    result = InboundRoutineResult(
        status="partial", payload=_payload(), brief=_brief(),
        email=DraftedEmail(subject="Hi", body_markdown="short"),
        log=log,
    )
    msg = format_inbound_telegram_message(result)
    assert "partial" in msg
    assert "gmail_draft" in msg
    assert "Source set to Other" in msg


def test_rebook_update_with_no_brief_still_renders():
    result = InboundRoutineResult(
        status="rebook_update", payload=_payload(),
        brief=None, email=None, log=_log_ok(),
    )
    msg = format_inbound_telegram_message(result)
    assert "rebook_update" in msg
    assert "jane@acme.com" in msg


def test_message_under_telegram_length_limit():
    """Telegram hard-limits at 4096 chars; our truncator caps at 1500."""
    long_friction = ["x" * 500 for _ in range(3)]
    brief = _brief()
    brief.likely_friction = long_friction
    result = InboundRoutineResult(
        status="enriched", payload=_payload(), brief=brief,
        email=DraftedEmail(subject="y" * 60, body_markdown="short"),
        log=_log_ok(),
    )
    msg = format_inbound_telegram_message(result)
    assert len(msg) <= 1500
