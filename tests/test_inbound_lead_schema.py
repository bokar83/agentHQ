from datetime import datetime, timezone
import pytest
from pydantic import ValidationError
from skills.inbound_lead.schema import (
    InboundPayload, ResearchBrief, DraftedEmail, LogResult, InboundRoutineResult
)


def test_inbound_payload_roundtrip():
    payload = InboundPayload(
        name="Jane Smith",
        email="jane@acme.com",
        company="Acme Consulting",
        booking_id="evt_abc123",
        meeting_time=datetime(2026, 5, 1, 14, 0, tzinfo=timezone.utc),
        source="calendly",
        notion_row_id=None,
        raw_company_url=None,
    )
    dumped = payload.model_dump()
    restored = InboundPayload(**dumped)
    assert restored == payload


def test_inbound_payload_rejects_bad_email():
    with pytest.raises(ValidationError):
        InboundPayload(
            name="Jane", email="not-an-email", booking_id="x", source="calendly",
        )


def test_inbound_payload_rejects_bad_source():
    with pytest.raises(ValidationError):
        InboundPayload(
            name="Jane", email="jane@acme.com", booking_id="x", source="webflow",
        )


def test_research_brief_defaults():
    brief = ResearchBrief(
        company_domain="acme.com",
        what_they_do="Boutique consulting firm.",
        industry_signals=[],
        likely_friction=[],
        conversation_hooks=[],
        lens_entry_point="Theory of Constraints",
        sources=[],
        research_confidence="low",
        notes=None,
    )
    assert brief.research_confidence == "low"
    assert brief.industry_signals == []


def test_drafted_email_validates_lengths():
    email = DraftedEmail(
        subject="Got your booking",
        body_markdown="Hi Jane, short note.",
        tone_note=None,
    )
    assert len(email.subject) <= 60
    assert len(email.body_markdown.split()) <= 150


def test_log_result_shape():
    result = LogResult(
        notion_row_url="https://notion.so/abc",
        gmail_draft_id="draft_123",
        gmail_draft_url="https://mail.google.com/mail/u/0/#drafts/draft_123",
        fields_written=["name", "email"],
        fields_skipped=[],
        warnings=[],
    )
    assert result.notion_row_url.startswith("https://")


def test_routine_result_shape():
    payload = InboundPayload(
        name="Jane", email="jane@acme.com", booking_id="x", source="calendly",
    )
    result = InboundRoutineResult(
        status="enriched",
        payload=payload,
        brief=None,
        email=None,
        log=None,
        telegram_sent=True,
        error=None,
    )
    assert result.status == "enriched"
