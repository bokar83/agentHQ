"""DRAFT for skills/score_request/runner.py.

Pre-staged 2026-04-30. Pipeline:
  validate → score (30-60s) → supabase write → email render → email send/draft
  → return ScoreResult to caller.

Failure modes are captured into ScoreResult.email_status, never raised. The
endpoint always returns a score if scoring succeeded, even if email or
supabase fail. That preserves the visitor's on-screen experience and lets
n8n retry email separately if needed.
"""
from __future__ import annotations
import logging
import os
from typing import Any

from pydantic import ValidationError

# DRAFT imports; these will resolve once files are placed in real locations
# from skills.score_request.schema import (
#     ScoreRequestPayload, ScoreBreakdown, ScoreResult,
# )
# from signal_works.ai_scorer import score_business
# from signal_works.email_builder import render_inbound_report_html
# from signal_works.gmail_draft import create_draft, send_message

logger = logging.getLogger("agentsHQ.score_request.runner")


def _supabase_insert_lead(payload, score_dict: dict) -> str | None:
    """Insert a lead row in Supabase. Returns lead_id or None on failure.

    Reuses the existing Supabase connection pattern from
    signal_works/lead_scraper.py. Source field is the differentiator: the
    cold pipeline uses 'signal_works' or 'apollo_catalyst_works' prefixes;
    the inbound score uses 'geolisted.co - Score Request' so existing
    sequence engines do not pick these up.
    """
    try:
        # DRAFT: actual import + insert in real implementation
        # from orchestrator.db import get_crm_connection_with_fallback
        # conn, _ = get_crm_connection_with_fallback()
        # cur = conn.cursor()
        # cur.execute(
        #     """INSERT INTO leads (name, email, company, city, industry,
        #         website_url, source, ai_score, ai_breakdown, ai_quick_wins,
        #         status, created_at)
        #     VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s::jsonb, %s, %s, NOW())
        #     RETURNING id""",
        #     (payload.name, payload.email, payload.business, payload.city,
        #      payload.niche, payload.website_url, payload.source,
        #      score_dict['score'], json.dumps(score_dict['breakdown']),
        #      score_dict['quick_wins'], 'inbound', datetime.now())
        # )
        # lead_id = cur.fetchone()[0]
        # conn.commit()
        # return str(lead_id)
        return None  # placeholder
    except Exception as exc:
        logger.warning(f"Supabase insert failed: {exc}")
        return None


def run_score_request(payload_dict: dict[str, Any]):
    """Main entry point. Sync. Blocks 30-60s on scoring.

    Called by the FastAPI route POST /score-request after auth check.
    """
    # 1. Validate payload
    try:
        # payload = ScoreRequestPayload(**payload_dict)
        payload = payload_dict  # placeholder for draft
    except ValidationError as exc:
        logger.warning(f"Score request payload validation failed: {exc.errors()[:2]}")
        raise

    logger.info(f"Score request: {payload_dict.get('email')} for {payload_dict.get('business')}")

    # 2. Run the scorer (30-60s blocking call to OpenRouter + SerpAPI + robots.txt)
    try:
        # score_dict = score_business(
        #     business_name=payload.business,
        #     city=payload.city,
        #     niche=payload.niche,
        #     website_url=payload.website_url or "",
        # )
        score_dict = {  # placeholder
            "score": 25,
            "breakdown": {"chatgpt": False, "perplexity": False, "robots_ok": True, "maps_present": False},
            "quick_wins": [
                "Strengthen Google Maps presence",
                "Add structured data to your site",
                "Build topical authority content",
            ],
            "business_name": payload_dict.get("business"),
            "city": payload_dict.get("city"),
            "niche": payload_dict.get("niche"),
        }
    except Exception as exc:
        logger.error(f"Scorer raised: {exc}")
        raise

    # 3. Insert into Supabase
    lead_id = _supabase_insert_lead(payload, score_dict)

    # 4. Render the inbound report email (extension to email_builder.py)
    lead_for_email = {
        "name": payload_dict.get("business"),
        "first_name": payload_dict.get("name", "there").split()[0],
        "email": payload_dict.get("email"),
        "city": payload_dict.get("city"),
        "niche": payload_dict.get("niche"),
        "ai_score": score_dict["score"],
        "ai_breakdown": score_dict["breakdown"],
        "ai_quick_wins": score_dict["quick_wins"],
        "website_url": payload_dict.get("website_url"),
        "source_context": "inbound",  # signal to render_inbound_report_html
    }

    # try:
    #     html_body = render_inbound_report_html(lead_for_email)
    # except Exception as exc:
    #     logger.error(f"Email render failed: {exc}")
    #     html_body = None
    html_body = "<placeholder/>"

    # 5. Send or draft the email based on env gate
    auto_send = os.environ.get("SCORE_AUTO_SEND", "false").lower() == "true"
    email_status = "pending"
    if html_body:
        try:
            subject = (
                f"Your AI visibility score: {score_dict['score']}/100 "
                f"and the 3 things keeping you invisible"
            )
            # if auto_send:
            #     send_message(payload.email, subject, html_body)
            #     email_status = "sent"
            # else:
            #     create_draft(payload.email, subject, html_body)
            #     email_status = "drafted"
            email_status = "sent" if auto_send else "drafted"
        except Exception as exc:
            logger.warning(f"Email send/draft failed: {exc}")
            email_status = f"failed: {type(exc).__name__}"

    # 6. Return ScoreResult to caller (n8n then browser)
    return {
        "score": score_dict["score"],
        "breakdown": score_dict["breakdown"],
        "quick_wins": score_dict["quick_wins"],
        "business": payload_dict.get("business"),
        "city": payload_dict.get("city"),
        "niche": payload_dict.get("niche"),
        "lead_id": lead_id,
        "email_status": email_status,
    }
