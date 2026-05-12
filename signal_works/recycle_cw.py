"""
signal_works/recycle_cw.py
==========================
CW queue recycle / fallback. When today's CW T1 harvest is thin and the
daily run produces fewer than CW_THRESHOLD drafts/sends, this module finds
leads we contacted recently and ages back their last_contacted_at so the
*next-touch* template fires naturally on the next sequence_engine pass.

Why this exists:
  Step 5b in morning_runner. Without this, a thin Apollo harvest morning
  produces 0 CW emails and the pipeline silently underperforms. The old
  cascade fallback (T2 burning when T1 empty) was removed 2026-05-11 because
  it inflated wrong counters. This replaces it with an explicit, bounded
  T-advance: a lead at T1 yesterday gets T2 today, T2 -> T3, ... T4 -> T5.
  Leads at T5 are skipped (sequence exhausted).

Contract:
  recycle_yesterdays_cw(min_floor: int) -> list[str]
    - Queries orc-postgres sw_email_log for prior CW 'sent' rows in the
      last 7 days where the lead_email has NOT been logged today.
    - For each (up to min_floor), looks up the lead in Supabase, confirms
      it is on the 'cw' sequence at touch 1-4 (skips touch=5 = exhausted),
      and UPDATEs last_contacted_at to age it past the next touch's gap.
    - Returns the list of lead_emails advanced (one per qualified lead).

The actual draft/send happens via the standard sequence_engine.run_sequence
call that the caller (morning_runner Step 5b) makes *after* this function
returns. That preserves all existing template/personalisation/auto-send
logic and avoids duplicating touch-progression code here.

Hard rules:
  - Never sends. Never drafts. Pure DB UPDATE on leads.
  - Never blocks the runner: every failure is caught and logged.
  - Cap at min_floor regardless of how many candidates exist.
  - Skips T5 (sequence_touch=5) -- those leads have completed CW.
  - Skips leads with no Supabase row (orphan sw_email_log entry).
"""
from __future__ import annotations

import logging
import os
from datetime import datetime, timedelta, timezone
from typing import List, Optional

logger = logging.getLogger(__name__)

# CW touch-gap days (mirrors TOUCH_DAYS_CW in skills/outreach/sequence_engine.py).
# When ageing back last_contacted_at, we set it >= TOUCH_DAYS_CW[next_touch] + 1
# day in the past so the lead clears the cutoff in _get_due_leads().
TOUCH_DAYS_CW = {1: 0, 2: 6, 3: 9, 4: 14, 5: 19}


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
    Returns up to `min_floor` * 2 candidate emails (over-fetch buffer to cover
    leads we'll skip downstream for being at T5, missing from leads table, or
    already sequence-exhausted).

    Source: orc-postgres sw_email_log, pipeline='cw', status='sent', last 7
    days, distinct, excluding any email already logged today.
    """
    if min_floor <= 0:
        return []
    # Over-fetch so downstream skips (T5, orphan, etc.) don't starve the cap.
    fetch_n = max(min_floor * 2, min_floor + 5)
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
            (fetch_n,),
        )
        rows = cur.fetchall()
        cur.close()
        conn.close()
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


def _advance_lead(conn, email: str) -> Optional[str]:
    """
    Age back last_contacted_at on a CW lead so it passes the cutoff for
    the *next* touch (sequence_touch + 1). Returns the email on success,
    None on skip.

    Skip cases:
      - lead not in Supabase
      - sequence_pipeline != 'cw'
      - sequence_touch is NULL/0 (lead never contacted -- they belong to T1
        harvest, not recycle)
      - sequence_touch >= 5 (sequence exhausted)
    """
    cur = conn.cursor()
    try:
        cur.execute(
            """
            SELECT id, sequence_touch, sequence_pipeline
            FROM leads
            WHERE email = %s
            LIMIT 1
            """,
            (email,),
        )
        row = cur.fetchone()
        if row is None:
            logger.info(f"recycle_cw: skip {email} (no lead row in Supabase)")
            return None
        lead = dict(row)
        current_touch = int(lead.get("sequence_touch") or 0)
        pipeline = lead.get("sequence_pipeline") or ""
        if pipeline != "cw":
            logger.info(
                f"recycle_cw: skip {email} (sequence_pipeline={pipeline!r}, not cw)"
            )
            return None
        if current_touch < 1:
            logger.info(
                f"recycle_cw: skip {email} (sequence_touch={current_touch}, "
                "belongs to T1 harvest)"
            )
            return None
        if current_touch >= 5:
            logger.info(
                f"recycle_cw: skip {email} (sequence_touch=5, sequence exhausted)"
            )
            return None

        next_touch = current_touch + 1
        # Age past the gap. +1 day buffer ensures we clear the cutoff cleanly
        # even with clock skew or query-time drift.
        gap_days = TOUCH_DAYS_CW[next_touch] + 1
        aged_back = datetime.now(timezone.utc) - timedelta(days=gap_days)

        cur.execute(
            """
            UPDATE leads
            SET last_contacted_at = %s,
                updated_at = %s
            WHERE id = %s
            """,
            (aged_back, datetime.now(timezone.utc), lead["id"]),
        )
        conn.commit()
        logger.info(
            f"recycle_cw: advanced {email} from T{current_touch} -> "
            f"eligible for T{next_touch} (aged back {gap_days}d)"
        )
        return email
    except Exception as e:
        logger.warning(f"recycle_cw: advance failed for {email}: {e}")
        try:
            conn.rollback()
        except Exception:
            pass
        return None
    finally:
        cur.close()


def recycle_yesterdays_cw(min_floor: int = 10) -> List[str]:
    """
    Find CW leads contacted in last 7 days (not today), age-back their
    last_contacted_at so the next touch fires on the very next sequence
    engine pass.

    Returns the list of lead_emails that were advanced. Length <= min_floor.

    Caller pattern (morning_runner Step 5b):
        emails = recycle_yesterdays_cw(min_floor=shortfall)
        if emails:
            run_sequence("cw", t1_cap=0, followup_cap=len(emails))
            # then mark today's sw_email_log rows for these emails as recycle=TRUE
    """
    if min_floor <= 0:
        return []

    candidates = _query_recyclable_emails(min_floor)
    if not candidates:
        logger.info(
            f"recycle_cw: no recyclable CW emails found (min_floor={min_floor})."
        )
        return []

    logger.info(
        f"recycle_cw: {len(candidates)} candidates pulled "
        f"(target min_floor={min_floor})."
    )

    crm_conn = _crm_conn()
    advanced: List[str] = []
    try:
        for email in candidates:
            adv = _advance_lead(crm_conn, email)
            if adv is not None:
                advanced.append(adv)
            if len(advanced) >= min_floor:
                break
    finally:
        try:
            crm_conn.close()
        except Exception:
            pass

    logger.info(
        f"recycle_cw: complete. Advanced {len(advanced)}/{min_floor} CW leads "
        "for next-touch pickup by run_sequence."
    )
    return advanced


def mark_today_recycled(emails: List[str]) -> int:
    """
    Mark today's sw_email_log rows for the given emails as recycle=TRUE.
    Called by morning_runner Step 5b *after* the second run_sequence("cw")
    pass writes draft/sent rows for the advanced cohort.

    Idempotent: re-runs harmlessly. Returns the number of rows updated.
    Never raises.
    """
    if not emails:
        return 0
    try:
        conn = _orc_conn()
        cur = conn.cursor()
        cur.execute(
            """
            UPDATE sw_email_log
            SET recycle = TRUE
            WHERE pipeline='cw'
              AND created_at::date = CURRENT_DATE
              AND lead_email = ANY(%s)
            """,
            (emails,),
        )
        n = cur.rowcount
        conn.commit()
        cur.close()
        conn.close()
        logger.info(f"recycle_cw: marked {n} sw_email_log rows as recycle=TRUE")
        return n
    except Exception as e:
        logger.warning(f"recycle_cw: mark_today_recycled failed (non-fatal): {e}")
        return 0


if __name__ == "__main__":
    # CLI: python -m signal_works.recycle_cw [N]
    # Lists would-be candidates AND shows their advance plan. Does NOT update.
    import sys

    logging.basicConfig(
        level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s"
    )
    n = int(sys.argv[1]) if len(sys.argv) > 1 else 10
    print(f"DRY-RUN candidates for min_floor={n}:")
    cands = _query_recyclable_emails(n)
    if not cands:
        print("  (none)")
        sys.exit(0)
    crm = _crm_conn()
    try:
        cur = crm.cursor()
        for e in cands:
            cur.execute(
                "SELECT sequence_touch, sequence_pipeline FROM leads "
                "WHERE email = %s LIMIT 1",
                (e,),
            )
            r = cur.fetchone()
            if not r:
                print(f"  {e}  [skip: no leads row]")
                continue
            d = dict(r)
            t = int(d.get("sequence_touch") or 0)
            p = d.get("sequence_pipeline") or "?"
            if p != "cw":
                print(f"  {e}  [skip: pipeline={p}]")
            elif t < 1:
                print(f"  {e}  [skip: touch={t}, T1 harvest]")
            elif t >= 5:
                print(f"  {e}  [skip: touch=5, exhausted]")
            else:
                print(f"  {e}  [T{t} -> eligible for T{t + 1}]")
        cur.close()
    finally:
        crm.close()
