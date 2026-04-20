"""Inbound lead routine runner: idempotency -> research -> draft -> log.

Entry point is `run_inbound_lead(payload_dict)`. Returns an
`InboundRoutineResult` whose status is one of:

- "enriched"      : first time we see this email; research + draft + Notion write all went through.
- "rebook_update" : email already enriched; we only refreshed meeting_time and Notion row.
- "partial"       : first-time enrichment but something degraded (draft lint failed,
                    Notion write failed, Gmail draft failed).
- "failed"        : payload invalid or an unrecoverable error before we could write anything.

The runner never raises: every exception is captured into the result so the
orchestrator can surface a diagnostic to the user instead of a 500.
"""
from __future__ import annotations
import logging
import os
from typing import Any

from pydantic import ValidationError

from skills.inbound_lead.schema import (
    DraftedEmail, InboundPayload, InboundRoutineResult, LogResult, ResearchBrief,
)

logger = logging.getLogger("agentsHQ.inbound_lead.runner")


def _make_fallback_brief(email_domain: str | None) -> ResearchBrief:
    """Used when research is skipped (rebook path) or fully fails."""
    return ResearchBrief(
        company_domain=email_domain,
        what_they_do="No research brief (skipped or failed).",
        industry_signals=[],
        likely_friction=[],
        conversation_hooks=[],
        lens_entry_point="AI Strategy",
        sources=[],
        research_confidence="none",
        notes="Runner fallback brief.",
    )


def _resolve_secrets() -> tuple[str | None, str | None]:
    """Return (notion_secret, pipeline_db_id). Either may be None on misconfig."""
    notion_secret = (
        os.environ.get("NOTION_API_KEY")
        or os.environ.get("NOTION_SECRET")
        or os.environ.get("NOTION_TOKEN")
    )
    pipeline_db = os.environ.get("NOTION_FORGE_PIPELINE_DB_ID")
    return notion_secret, pipeline_db


def run_inbound_lead(payload_dict: dict[str, Any]) -> InboundRoutineResult:
    """Main entry point. Takes raw dict, returns InboundRoutineResult."""
    # Parse payload -----------------------------------------------------------
    try:
        payload = InboundPayload(**payload_dict)
    except ValidationError as exc:
        logger.warning(f"Inbound payload validation failed: {exc.errors()[:2]}")
        # Build a minimal stand-in so the result still validates.
        stub = InboundPayload(
            name=str(payload_dict.get("name") or "(unknown)"),
            email=str(payload_dict.get("email") or "invalid@example.com"),
            booking_id=str(payload_dict.get("booking_id") or "unknown"),
            source=payload_dict.get("source") if payload_dict.get("source") in ("calendly", "formspree") else "calendly",
        )
        return InboundRoutineResult(
            status="failed", payload=stub,
            error=f"Invalid payload: {exc.errors()[:1]}",
        )

    notion_secret, pipeline_db = _resolve_secrets()
    if not notion_secret or not pipeline_db:
        return InboundRoutineResult(
            status="failed", payload=payload,
            error="Missing NOTION_API_KEY or NOTION_FORGE_PIPELINE_DB_ID in environment.",
        )

    # Idempotency check -------------------------------------------------------
    # Imported lazily so tests can patch, and so an environment without
    # Postgres still allows the module to import.
    from skills.inbound_lead.idempotency import (
        has_been_enriched, mark_enriched, mark_rebook,
    )
    from skills.inbound_lead.researcher import research
    from skills.inbound_lead.drafter import draft_email
    from skills.inbound_lead.logger import log_lead

    try:
        prior = has_been_enriched(payload.email)
    except Exception as exc:
        logger.warning(f"Idempotency lookup failed: {exc}. Proceeding as fresh.")
        prior = None

    # Rebook path: update Notion only, skip research + draft -----------------
    if prior:
        fallback = _make_fallback_brief(
            payload.email.split("@", 1)[1] if "@" in payload.email else None
        )
        try:
            log = log_lead(
                payload=payload, brief=fallback, draft=None,
                database_id=pipeline_db, notion_secret=notion_secret,
            )
        except Exception as exc:
            logger.warning(f"Rebook log_lead raised: {exc}")
            log = LogResult(warnings=[f"Rebook log failed: {exc}"])
        try:
            mark_rebook(payload.email, payload.booking_id, payload.meeting_time)
        except Exception as exc:
            logger.warning(f"mark_rebook failed: {exc}")
        return InboundRoutineResult(
            status="rebook_update", payload=payload, log=log,
        )

    # Fresh enrichment path --------------------------------------------------
    try:
        brief = research(
            name=payload.name, email=payload.email,
            company=payload.company, raw_company_url=payload.raw_company_url,
        )
    except Exception as exc:
        logger.warning(f"Researcher raised: {exc}")
        brief = _make_fallback_brief(
            payload.email.split("@", 1)[1] if "@" in payload.email else None
        )

    draft_status = "clean"
    drafted: DraftedEmail | None = None
    try:
        drafted_result = draft_email(
            name=payload.name, brief=brief, meeting_time=payload.meeting_time,
        )
        drafted = drafted_result.email
        draft_status = drafted_result.status
    except Exception as exc:
        logger.warning(f"Drafter raised: {exc}")
        drafted = None
        draft_status = "failed"

    try:
        log = log_lead(
            payload=payload, brief=brief, draft=drafted,
            database_id=pipeline_db, notion_secret=notion_secret,
        )
    except Exception as exc:
        logger.warning(f"Logger raised: {exc}")
        log = LogResult(warnings=[f"Logger raised: {exc}"])

    notion_ok = bool(log.notion_page_id)
    gmail_ok = bool(log.gmail_draft_id) if drafted else True
    overall = (
        "enriched" if notion_ok and gmail_ok and draft_status == "clean"
        else "partial"
    )

    if notion_ok:
        try:
            mark_enriched(
                email=payload.email, booking_id=payload.booking_id,
                meeting_time=payload.meeting_time, status=overall,
            )
        except Exception as exc:
            logger.warning(f"mark_enriched failed: {exc}")
    else:
        overall = "failed" if not log.warnings else "partial"

    return InboundRoutineResult(
        status=overall, payload=payload, brief=brief,
        email=drafted, log=log,
    )
