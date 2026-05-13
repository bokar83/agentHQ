"""skills/constraints_ai_capture/runner.py

Background persistence path for POST /api/constraints-capture.

Two writes, ordered:

1. Supabase REST → diagnostic_captures (durable artifact). Best-effort —
   if Supabase env is missing or the call fails, log and continue.
2. orc-postgres leads table → INSERT with sequence_pipeline='constraints_ai',
   sequence_touch=0, capture_idempotency_key set. Unique index makes a
   duplicate submit a silent no-op.

Why a separate module: keeps app.py thin, lets sequence_engine import it
without an app.py circular dependency.
"""

from __future__ import annotations

import json
import logging
import os
import sys
from typing import Optional

import httpx

logger = logging.getLogger("agentsHQ.constraints_capture")


def _supabase_log_capture(payload: dict) -> None:
    """POST to Supabase diagnostic_captures table. Fire-and-forget."""
    url = os.environ.get("SUPABASE_URL")
    key = os.environ.get("SUPABASE_SERVICE_KEY")
    if not url or not key:
        logger.warning(
            "constraints_capture: SUPABASE_URL/SUPABASE_SERVICE_KEY unset; "
            "skipping Supabase log"
        )
        return
    try:
        resp = httpx.post(
            f"{url}/rest/v1/diagnostic_captures",
            headers={
                "content-type": "application/json",
                "apikey": key,
                "authorization": f"Bearer {key}",
                "prefer": "return=minimal",
            },
            json={
                "email": payload["email"],
                "pain_text": payload.get("pain_text", ""),
                "response_json": {
                    "constraint": payload.get("response_constraint", ""),
                    "action": payload.get("response_action", ""),
                },
                "source": payload.get("source", "site_demo_capture"),
                "user_agent": payload.get("user_agent", ""),
                "geo_country": payload.get("geo_country", ""),
            },
            timeout=15,
        )
        if resp.status_code >= 400:
            logger.warning(
                f"constraints_capture: supabase non-2xx {resp.status_code} "
                f"body={resp.text[:200]}"
            )
    except Exception as exc:
        logger.error(f"constraints_capture: supabase POST failed: {exc}")


def _insert_lead(payload: dict) -> Optional[int]:
    """Insert lead row with sequence_pipeline=constraints_ai. Returns row id
    or None on uniqueness conflict (duplicate submit)."""
    try:
        from db import get_crm_connection_with_fallback
    except ModuleNotFoundError:
        from orchestrator.db import get_crm_connection_with_fallback

    conn, _ = get_crm_connection_with_fallback()
    # leads.name is NOT NULL on Supabase. Capture form is email-only — no real
    # name attached. Use email prefix as the placeholder. Most CRM UIs render
    # exactly this when name is empty, so the operator-visible behaviour is
    # unchanged. Reversible — a later touch (paid call, form follow-up) can
    # overwrite name when a real one becomes known.
    email = payload["email"]
    name_placeholder = email.split("@", 1)[0] if "@" in email else email
    try:
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO leads (
                    name,
                    email,
                    source,
                    sequence_pipeline,
                    sequence_touch,
                    pain_text,
                    response_constraint,
                    response_action,
                    capture_idempotency_key
                )
                VALUES (%s, %s, %s, 'constraints_ai', 0, %s, %s, %s, %s)
                ON CONFLICT (capture_idempotency_key)
                  WHERE capture_idempotency_key IS NOT NULL
                  DO NOTHING
                RETURNING id
                """,
                (
                    name_placeholder,
                    email,
                    payload.get("source", "site_demo_capture"),
                    payload.get("pain_text", ""),
                    payload.get("response_constraint", ""),
                    payload.get("response_action", ""),
                    payload["idempotency_key"],
                ),
            )
            row = cur.fetchone()
            conn.commit()
            return row[0] if row else None
    except Exception as exc:
        logger.error(f"constraints_capture: lead insert failed: {exc}")
        conn.rollback()
        return None
    finally:
        conn.close()


def persist_constraints_capture(payload: dict) -> None:
    """Public entry point. Called by app.py background task."""
    _supabase_log_capture(payload)
    lead_id = _insert_lead(payload)
    if lead_id is None:
        logger.info(
            f"constraints_capture: duplicate idempotency_key "
            f"{payload['idempotency_key'][:8]}... or insert failed (already-logged)"
        )
    else:
        logger.info(
            f"constraints_capture: lead {lead_id} inserted for "
            f"{payload['email']} (constraints_ai pipeline, T0)"
        )
