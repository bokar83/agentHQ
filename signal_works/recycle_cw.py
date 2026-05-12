"""
signal_works/recycle_cw.py
==========================
CW queue recycle / fallback. When today's CW T1 lead pool is empty or
under-target, this module picks up leads we contacted in the past 7 days
but have NOT touched today, then issues a re-touch email so the daily
outreach floor of CW_THRESHOLD is maintained.

Why this exists:
  Step 5b in morning_runner. Without this, a thin Apollo harvest morning
  produces 0 CW emails and the pipeline silently underperforms. The old
  cascade fallback (T2 burning when T1 empty) was removed 2026-05-11 because
  it inflated wrong counters. This module replaces it with an explicit,
  bounded, honest recycle.

Contract (per agent spec):
  recycle_yesterdays_cw(min_floor: int) -> list[str]
    - Queries orc-postgres sw_email_log for prior CW 'sent' rows in the
      last 7 days where the lead_email has NOT been logged today.
    - For each (up to min_floor), re-touches via sequence_engine primitives,
      honoring AUTO_SEND_CW env (true => actual send; false => draft).
    - Returns the list of lead_emails that were re-touched (success only).

Hard rules:
  - Never sends without sequence_engine's auto_send rule.
  - Never blocks the runner: every failure is caught, logged, and the next
    candidate is tried.
  - Cap at min_floor regardless of how many candidates exist.
  - Skips leads with no body context (missing lead row in Supabase leads
    table). Those would yield generic emails that hurt deliverability.
"""
from __future__ import annotations

import logging
import os
from typing import List, Optional

logger = logging.getLogger(__name__)


def _orc_conn():
    """Connect to orc-postgres. Caller MUST close."""
    import psycopg2
    return psycopg2.connect(
        host=os.environ.get("POSTGRES_HOST", "orc-postgres"),
        database=os.environ.get("POSTGRES_DB", "postgres"),
        user=os.environ.get("POSTGRES_USER", "postgres"),
        password=os.environ.get("POSTGRES_PASSWORD", ""),
        port=int(os.environ.get("POSTGRES_PORT", 5432)),
    )


def _query_recyclable_emails(min_floor: int) -> List[str]:
    """
    Returns up to `min_floor` lead_emails that were sent CW emails in the
    past 7 days but have NOT been logged at all today. Distinct emails only.
    """
    if min_floor <= 0:
        return []
    try:
        conn = _orc_conn()
        cur = conn.cursor()
        cur.execute(
            """
            SELECT DISTINCT lead_email
            FROM sw_email_log
            WHERE pipeline='cw'
              AND status='sent'
              AND created_at::date >= CURRENT_DATE - INTERVAL '7 days'
              AND lead_email NOT IN (
                  SELECT lead_email
                  FROM sw_email_log
                  WHERE created_at::date = CURRENT_DATE
              )
            LIMIT %s
            """,
            (min_floor,),
        )
        rows = cur.fetchall()
        cur.close()
        conn.close()
        # rows is list of single-element tuples
        return [r[0] for r in rows if r and r[0]]
    except Exception as e:
        logger.warning(f"recycle_cw: query failed (non-fatal): {e}")
        return []


def _crm_conn():
    """Get the Supabase leads connection used by sequence_engine."""
    try:
        from orchestrator.db import get_crm_connection
    except ModuleNotFoundError:
        import sys
        sys.path.insert(0, "/app")
        from db import get_crm_connection  # type: ignore
    return get_crm_connection()


def _load_lead(conn, email: str) -> Optional[dict]:
    """Fetch the lead row from Supabase leads by email. None if missing."""
    cur = conn.cursor()
    try:
        cur.execute(
            """
            SELECT id, name, email, title, company, industry, city,
                   sequence_touch, sequence_pipeline,
                   review_count, has_website, google_rating, niche,
                   gmb_opener
            FROM leads
            WHERE email = %s
            LIMIT 1
            """,
            (email,),
        )
        row = cur.fetchone()
        if row is None:
            return None
        return dict(row)
    finally:
        cur.close()


def recycle_yesterdays_cw(min_floor: int = 10) -> List[str]:
    """
    Pick up CW leads contacted in past 7 days (not today) and issue a re-touch.

    Returns the list of lead_emails that were successfully re-touched. Length
    of the returned list <= min_floor.

    Honors AUTO_SEND_CW env via sequence_engine's _create_draft + auto_send.
    Drafts when AUTO_SEND_CW != 'true'. Caller (morning_runner) calls this
    inside a try/except and never re-raises.
    """
    if min_floor <= 0:
        return []

    candidates = _query_recyclable_emails(min_floor)
    if not candidates:
        logger.info(f"recycle_cw: no recyclable CW emails found (min_floor={min_floor}).")
        return []

    logger.info(
        f"recycle_cw: {len(candidates)} candidates pulled "
        f"(target min_floor={min_floor})."
    )

    # Lazy import to avoid hard dependency at module-load time (the morning
    # runner imports recycle_cw inside a try/except already).
    try:
        from skills.outreach.sequence_engine import (
            _create_draft,
            _load_template,
            _render,
            _mark_sent,
            _log_to_orc_postgres,
        )
    except Exception as e:
        logger.warning(f"recycle_cw: sequence_engine primitives unavailable: {e}")
        return []

    auto_send = os.environ.get("AUTO_SEND_CW", "false").lower() == "true"

    # Re-touch template: use the highest-touch CW template the lead has not
    # yet seen, falling back to T1 if we can't tell. Most recycled leads will
    # already be at T5; for those, re-fire T5 (final touch is the most
    # "earned the right to bump" message in the sequence). This is the safest
    # default that keeps the message contextually consistent.
    # If the lead has no body context, we skip rather than send generic copy.

    crm_conn = _crm_conn()
    touched: List[str] = []
    try:
        for email in candidates:
            try:
                lead = _load_lead(crm_conn, email)
                if not lead:
                    logger.info(f"recycle_cw: skip {email} (no lead row in Supabase)")
                    continue

                # Pick the touch to re-fire. Re-touch the highest touch the lead
                # already completed; default to 1 if we have no signal. Clamp to
                # 5 (CW max). T1 will introduce; T5 will be the final nudge.
                current_touch = int(lead.get("sequence_touch") or 0)
                touch = max(1, min(5, current_touch if current_touch > 0 else 1))

                subject_tpl, body_or_builder = _load_template("cw", touch)
                subject = subject_tpl
                body = _render(body_or_builder, lead)

                result_id = _create_draft(
                    email, subject, body, "cw", auto_send=auto_send,
                )
                if not result_id:
                    _log_to_orc_postgres(
                        lead_id=lead["id"], lead_email=email, touch=touch,
                        pipeline="cw", subject=subject, gmail_id="",
                        status="failed",
                    )
                    logger.info(f"recycle_cw: failed for {email}")
                    continue

                # status mirrors auto_send: 'sent' or 'drafted'.
                # Use 'recycled-sent' / 'recycled-drafted' prefix so downstream
                # spend-tracking can distinguish recycled volume from primary.
                status = "recycled-sent" if auto_send else "recycled-drafted"
                _log_to_orc_postgres(
                    lead_id=lead["id"], lead_email=email, touch=touch,
                    pipeline="cw", subject=subject, gmail_id=result_id,
                    status=status,
                )
                touched.append(email)
                logger.info(f"recycle_cw: re-touched {email} as T{touch} ({status})")

                if len(touched) >= min_floor:
                    break
            except Exception as e:
                logger.warning(f"recycle_cw: candidate {email} failed: {e}")
                continue
    finally:
        try:
            crm_conn.close()
        except Exception:
            pass

    logger.info(
        f"recycle_cw: complete. Re-touched {len(touched)}/{min_floor} "
        f"({'sent' if auto_send else 'drafted'})."
    )
    return touched


if __name__ == "__main__":
    # CLI: python -m signal_works.recycle_cw [N]
    # Prints the would-be recycled emails. Does NOT send.
    import sys

    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    n = int(sys.argv[1]) if len(sys.argv) > 1 else 10
    print(f"DRY-RUN candidates for min_floor={n}:")
    for e in _query_recyclable_emails(n):
        print(f"  {e}")
