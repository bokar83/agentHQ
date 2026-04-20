"""End-to-end integration test for the inbound lead routine.

Strategy: patch the three external-I/O seams (Anthropic SDK, Firecrawl search,
Notion HTTP client, gws subprocess, Postgres psycopg2), then call
run_inbound_lead on a realistic payload and assert the shape of the result
plus the side-effect call patterns.

This is a black-box test of the full pipeline: it exercises researcher +
drafter + logger + idempotency + runner all composed. It does NOT hit the
FastAPI endpoint (covered by the unit tests of the runner) and does NOT
touch any real network.
"""
from unittest.mock import MagicMock, patch
from datetime import datetime, timezone

import pytest


VALID_PAYLOAD = {
    "name": "Jane Doe",
    "email": "jane@acme.com",
    "company": "Acme Consulting",
    "booking_id": "bk_abc123",
    "meeting_time": "2026-05-01T15:00:00+00:00",
    "source": "calendly",
    "raw_company_url": "https://acme.com/",
}


CLEAN_DRAFT_JSON = (
    '{"subject": "Saw your booking", '
    '"body_markdown": "Short calm note with a question at the end?", '
    '"tone_note": "calm"}'
)


BRIEF_JSON = (
    '{"company_domain": "acme.com", '
    '"what_they_do": "Boutique mid-market consulting.", '
    '"industry_signals": ["Mid-market focus"], '
    '"likely_friction": ["Margin pressure as they scale delivery"], '
    '"conversation_hooks": ["What shifted in the last year?"], '
    '"lens_entry_point": "Theory of Constraints", '
    '"sources": ["https://acme.com/"], '
    '"research_confidence": "medium", '
    '"notes": null}'
)


def _mock_anthropic_response(text: str) -> MagicMock:
    block = MagicMock()
    block.type = "text"
    block.text = text
    resp = MagicMock()
    resp.content = [block]
    resp.stop_reason = "end_turn"
    return resp


@pytest.fixture
def env(monkeypatch):
    monkeypatch.setenv("NOTION_API_KEY", "sk_fake")
    monkeypatch.setenv("NOTION_FORGE_PIPELINE_DB_ID", "db_fake")
    monkeypatch.setenv("ANTHROPIC_API_KEY", "sk_fake_anthropic")
    monkeypatch.setenv("SUPABASE_DB_URL", "postgresql://fake")


def test_end_to_end_fresh_enrichment_produces_enriched_result(env):
    """Full pipeline, first-time prospect: research + draft + log + mark enriched."""
    with patch("skills.inbound_lead.researcher.run_research") as run_research, \
         patch("skills.inbound_lead.drafter._generate_draft") as gen_draft, \
         patch("skills.inbound_lead.logger.NotionClient") as NC, \
         patch("skills.inbound_lead.logger.create_gmail_draft", return_value="d-42") as gws, \
         patch("skills.inbound_lead.idempotency._get_conn") as get_conn:
        # Researcher stub
        run_research.return_value = {
            "success": True, "answer": BRIEF_JSON, "error": None,
            "tool_calls": 2, "turns": 3,
        }
        # Drafter stub -- returns a DraftedEmail directly, so we patch the
        # internal _generate_draft helper (already tested individually).
        from skills.inbound_lead.schema import DraftedEmail
        gen_draft.return_value = DraftedEmail(
            subject="Saw your booking",
            body_markdown="Short calm note with a question at the end?",
        )

        # Notion stub: no existing row, create succeeds
        client = NC.return_value
        client.query_database.return_value = []
        client.create_page.return_value = {"id": "11111111222233334444555566667777"}

        # Postgres stub: has_been_enriched -> no row; mark_enriched -> OK
        cur = MagicMock()
        cur.fetchone.return_value = None  # no prior enrichment
        conn = MagicMock()
        conn.cursor.return_value.__enter__.return_value = cur
        get_conn.return_value = conn

        from skills.inbound_lead.runner import run_inbound_lead
        result = run_inbound_lead(VALID_PAYLOAD)

    assert result.status == "enriched"
    assert result.payload.email == "jane@acme.com"
    assert result.brief is not None
    assert result.brief.research_confidence == "medium"
    assert result.email is not None
    assert result.email.subject == "Saw your booking"
    assert result.log is not None
    assert result.log.notion_page_id == "11111111222233334444555566667777"
    assert result.log.gmail_draft_id == "d-42"

    run_research.assert_called_once()
    gen_draft.assert_called_once()
    gws.assert_called_once()
    client.create_page.assert_called_once()


def test_end_to_end_rebook_skips_research_and_draft(env):
    """Prior enrichment exists: runner should NOT hit researcher or drafter."""
    with patch("skills.inbound_lead.researcher.run_research") as run_research, \
         patch("skills.inbound_lead.drafter._generate_draft") as gen_draft, \
         patch("skills.inbound_lead.logger.NotionClient") as NC, \
         patch("skills.inbound_lead.logger.create_gmail_draft") as gws, \
         patch("skills.inbound_lead.idempotency._get_conn") as get_conn:
        client = NC.return_value
        client.query_database.return_value = [{
            "id": "aaaa1111bbbb2222cccc3333dddd4444",
            "properties": {"Status": {"select": {"name": "Call Booked"}}},
        }]

        cur = MagicMock()
        # has_been_enriched does tuple indexing: row[0]..row[5]
        cur.fetchone.return_value = (
            "jane@acme.com", "bk_old", datetime(2026, 4, 1, tzinfo=timezone.utc),
            "bk_old", None, "enriched",
        )
        conn = MagicMock()
        conn.cursor.return_value.__enter__.return_value = cur
        get_conn.return_value = conn

        from skills.inbound_lead.runner import run_inbound_lead
        result = run_inbound_lead(VALID_PAYLOAD)

    assert result.status == "rebook_update"
    run_research.assert_not_called()
    gen_draft.assert_not_called()
    gws.assert_not_called()
    client.update_page.assert_called_once()


def test_end_to_end_degrades_to_partial_when_gmail_fails(env):
    """Research OK, Notion OK, Gmail draft fails -> partial."""
    with patch("skills.inbound_lead.researcher.run_research") as run_research, \
         patch("skills.inbound_lead.drafter._generate_draft") as gen_draft, \
         patch("skills.inbound_lead.logger.NotionClient") as NC, \
         patch("skills.inbound_lead.logger.create_gmail_draft", return_value=None), \
         patch("skills.inbound_lead.idempotency._get_conn") as get_conn:
        run_research.return_value = {
            "success": True, "answer": BRIEF_JSON, "error": None,
            "tool_calls": 1, "turns": 2,
        }
        from skills.inbound_lead.schema import DraftedEmail
        gen_draft.return_value = DraftedEmail(
            subject="Hi", body_markdown="Short note?",
        )
        client = NC.return_value
        client.query_database.return_value = []
        client.create_page.return_value = {"id": "ppp"}

        cur = MagicMock()
        cur.fetchone.return_value = None
        conn = MagicMock()
        conn.cursor.return_value.__enter__.return_value = cur
        get_conn.return_value = conn

        from skills.inbound_lead.runner import run_inbound_lead
        result = run_inbound_lead(VALID_PAYLOAD)

    assert result.status == "partial"
    assert result.log.gmail_draft_id is None
    assert "gmail_draft" in result.log.fields_skipped


def test_end_to_end_telegram_message_renders_for_enriched_case(env):
    """After a successful run, the formatter produces a message that contains
    all the key info a human would need from Telegram."""
    from skills.inbound_lead.schema import (
        DraftedEmail, InboundPayload, InboundRoutineResult, LogResult, ResearchBrief,
    )
    from skills.inbound_lead.telegram_notify import format_inbound_telegram_message

    payload = InboundPayload(
        name="Jane Doe", email="jane@acme.com", company="Acme Consulting",
        booking_id="bk_abc123",
        meeting_time=datetime(2026, 5, 1, 15, 0, tzinfo=timezone.utc),
        source="calendly", raw_company_url="https://acme.com/",
    )
    result = InboundRoutineResult(
        status="enriched", payload=payload,
        brief=ResearchBrief(
            company_domain="acme.com", what_they_do="Consulting firm.",
            industry_signals=[], likely_friction=["Margin pressure"],
            conversation_hooks=[], lens_entry_point="Lean", sources=[],
            research_confidence="medium",
        ),
        email=DraftedEmail(subject="Saw your booking", body_markdown="x"),
        log=LogResult(
            notion_page_id="abc", notion_row_url="https://www.notion.so/abc",
            gmail_draft_id="d-1", gmail_draft_url="https://mail.google.com/...=d-1",
            fields_written=["Lead/Company"], fields_skipped=["booking_id_property"],
            warnings=[],
        ),
    )
    msg = format_inbound_telegram_message(result)
    assert "enriched" in msg
    assert "jane@acme.com" in msg
    assert "Acme Consulting" in msg
    assert "2026-05-01" in msg
    assert "Margin pressure" in msg
    assert "Saw your booking" in msg
    assert "notion.so/abc" in msg
    assert "mail.google.com" in msg
