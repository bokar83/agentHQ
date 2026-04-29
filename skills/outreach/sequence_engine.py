"""
skills/outreach/sequence_engine.py
===================================
4-touch email sequence engine for CW and SW pipelines.

Touch schedule:
  T1 = Day 0  (first contact)
  T2 = Day 3
  T3 = Day 7
  T4 = Day 12

Rules:
  - AUTO_SEND_CW / AUTO_SEND_SW env vars control send vs draft
  - Default: BOTH are draft-only until Boubacar flips the switch
  - Set AUTO_SEND_CW=true or AUTO_SEND_SW=true in .env to enable
  - Opted-out leads (opt_out = TRUE) are never contacted
  - A lead with no sequence_touch is eligible for T1
  - Touches advance only when the gap since last_contacted_at is met
  - niche and city pulled from leads.industry / leads.city for SW templates

Usage:
  python -m skills.outreach.sequence_engine --pipeline cw
  python -m skills.outreach.sequence_engine --pipeline sw
  python -m skills.outreach.sequence_engine --pipeline cw --dry-run
"""

import os
import sys
import json
import base64
import logging
import argparse
import importlib.util
from datetime import datetime, timezone, timedelta
from email.mime.text import MIMEText
from pathlib import Path
from typing import Optional

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

logger = logging.getLogger(__name__)

# SW: 4 touches at Day 0/3/7/12
# CW: 5 touches at Day 0/6/9/14/19 (T2 = SaaS PDF value-add)
TOUCH_DAYS_SW = {1: 0, 2: 3, 3: 7, 4: 12}
TOUCH_DAYS_CW = {1: 0, 2: 6, 3: 9, 4: 14, 5: 19}

def _touch_days(pipeline: str) -> dict:
    return TOUCH_DAYS_CW if pipeline == "cw" else TOUCH_DAYS_SW

CW_ACCOUNT = "catalystworks.ai@gmail.com"
SW_ACCOUNT = "catalystworks.ai@gmail.com"

TEMPLATES = {
    "cw": {
        1: "templates.email.cold_outreach",
        2: "templates.email.cw_t2",
        3: "templates.email.cw_t3",
        4: "templates.email.cw_t4",
        5: "templates.email.cw_t5",
    },
    "sw": {
        1: "templates.email.sw_t1",
        2: "templates.email.sw_t2",
        3: "templates.email.sw_t3",
        4: "templates.email.sw_t4",
    },
}


# ── DB ────────────────────────────────────────────────────────────────────────

def _get_conn():
    try:
        from orchestrator.db import get_crm_connection_with_fallback
    except ModuleNotFoundError:
        # VPS container: orchestrator/ is mounted as /app directly
        sys.path.insert(0, "/app")
        from db import get_crm_connection_with_fallback
    conn, is_fallback = get_crm_connection_with_fallback()
    if is_fallback:
        logger.warning("sequence_engine: using local Postgres fallback.")
    return conn


def _ensure_sequence_columns(conn) -> None:
    """Add sequence tracking columns to leads if not present."""
    cur = conn.cursor()
    for col, definition in [
        ("sequence_touch", "INTEGER DEFAULT 0"),
        ("sequence_pipeline", "TEXT"),
        ("opt_out", "BOOLEAN DEFAULT FALSE"),
    ]:
        cur.execute(f"""
            ALTER TABLE leads ADD COLUMN IF NOT EXISTS {col} {definition}
        """)
    conn.commit()
    cur.close()


def _get_due_leads(conn, pipeline: str, touch: int, limit: int = 10) -> list[dict]:
    """
    Fetch leads due for a specific touch.
    T1: sequence_touch IS NULL or 0, last_contacted_at IS NULL
    T2-T4: sequence_touch = touch-1, last_contacted_at <= now - required_days
    """
    cur = conn.cursor()
    min_gap = timedelta(days=_touch_days(pipeline)[touch])
    cutoff = datetime.now(timezone.utc) - min_gap

    source_filter = "apollo_catalyst_works" if pipeline == "cw" else "apollo_signal_works%"
    source_op = "=" if pipeline == "cw" else "LIKE"

    if touch == 1:
        cur.execute(f"""
            SELECT id, name, email, title, company, industry, city,
                   sequence_touch, sequence_pipeline
            FROM leads
            WHERE email IS NOT NULL AND email != ''
              AND (opt_out IS NULL OR opt_out = FALSE)
              AND (sequence_touch IS NULL OR sequence_touch = 0)
              AND last_contacted_at IS NULL
              AND source {source_op} %s
            ORDER BY created_at ASC
            LIMIT %s
        """, (source_filter, limit))
    else:
        cur.execute(f"""
            SELECT id, name, email, title, company, industry, city,
                   sequence_touch, sequence_pipeline
            FROM leads
            WHERE email IS NOT NULL AND email != ''
              AND (opt_out IS NULL OR opt_out = FALSE)
              AND sequence_touch = %s
              AND sequence_pipeline = %s
              AND last_contacted_at <= %s
              AND source {source_op} %s
            ORDER BY last_contacted_at ASC
            LIMIT %s
        """, (touch - 1, pipeline, cutoff, source_filter, limit))

    rows = [dict(r) for r in cur.fetchall()]
    cur.close()
    return rows


def _mark_sent(conn, lead_id: int, touch: int, pipeline: str, subject: str) -> None:
    now = datetime.now(timezone.utc)
    cur = conn.cursor()
    cur.execute("""
        UPDATE leads
        SET sequence_touch = %s,
            sequence_pipeline = %s,
            last_contacted_at = %s,
            email_drafted_at = COALESCE(email_drafted_at, %s),
            updated_at = %s
        WHERE id = %s
    """, (touch, pipeline, now, now, now, lead_id))
    cur.execute("""
        INSERT INTO lead_interactions (lead_id, interaction_type, content)
        VALUES (%s, %s, %s)
    """, (lead_id, f"sequence_{pipeline}_t{touch}", subject))
    conn.commit()
    cur.close()


# ── Gmail ─────────────────────────────────────────────────────────────────────

def _get_access_token(pipeline: str) -> str:
    import httpx
    env_var = "GOOGLE_OAUTH_CREDENTIALS_JSON_CW"
    env_path = os.environ.get(env_var, "")
    local_path = Path(__file__).resolve().parents[2] / "secrets" / "gws-oauth-credentials-cw.json"
    docker_path = "/app/secrets/gws-oauth-credentials-cw.json"
    creds_path = (
        env_path if (env_path and Path(env_path).exists())
        else str(local_path) if local_path.exists()
        else docker_path
    )
    with open(creds_path) as f:
        creds = json.load(f)
    resp = httpx.post(
        "https://oauth2.googleapis.com/token",
        data={
            "client_id": creds["client_id"],
            "client_secret": creds["client_secret"],
            "refresh_token": creds["refresh_token"],
            "grant_type": "refresh_token",
        },
        timeout=15,
    )
    resp.raise_for_status()
    return resp.json()["access_token"]


def _create_draft(to_email: str, subject: str, body: str,
                  pipeline: str, auto_send: bool = False) -> Optional[str]:
    import httpx
    try:
        token = _get_access_token(pipeline)
        from_addr = CW_ACCOUNT if pipeline == "cw" else SW_ACCOUNT
        msg = MIMEText(body, "plain")
        msg["to"] = to_email
        msg["from"] = from_addr
        msg["subject"] = subject
        raw = base64.urlsafe_b64encode(msg.as_bytes()).decode()

        if auto_send:
            resp = httpx.post(
                "https://gmail.googleapis.com/gmail/v1/users/me/messages/send",
                headers={"Authorization": f"Bearer {token}"},
                json={"raw": raw},
                timeout=20,
            )
        else:
            resp = httpx.post(
                "https://gmail.googleapis.com/gmail/v1/users/me/drafts",
                headers={"Authorization": f"Bearer {token}"},
                json={"message": {"raw": raw}},
                timeout=20,
            )
        resp.raise_for_status()
        result_id = resp.json().get("id")
        action = "sent" if auto_send else "drafted"
        logger.info(f"  Email {action} to {to_email} (id: {result_id})")
        return result_id
    except Exception as e:
        logger.error(f"  Gmail failed for {to_email}: {e}")
        return None


# ── Template loading ──────────────────────────────────────────────────────────

def _load_template(pipeline: str, touch: int):
    module_path = TEMPLATES[pipeline][touch]
    mod = importlib.import_module(module_path)
    return mod.SUBJECT, mod.BODY


def _render(body: str, lead: dict) -> str:
    first_name = (lead.get("name") or "there").split()[0]
    niche = (lead.get("industry") or "business").lower()
    city = lead.get("city") or "your city"
    return body.format(first_name=first_name, niche=niche, city=city)


# ── Main runner ───────────────────────────────────────────────────────────────

def run_sequence(pipeline: str, dry_run: bool = False, daily_limit: int = 10) -> dict:
    """
    Process all due touches for a pipeline up to daily_limit total emails.
    Auto-send controlled by AUTO_SEND_CW / AUTO_SEND_SW env vars (default: draft).
    Returns summary dict.
    """
    auto_send_cw = os.environ.get("AUTO_SEND_CW", "false").lower() == "true"
    auto_send_sw = os.environ.get("AUTO_SEND_SW", "false").lower() == "true"
    auto_send = auto_send_cw if pipeline == "cw" else auto_send_sw
    conn = _get_conn()
    _ensure_sequence_columns(conn)

    total_sent = 0
    total_failed = 0
    results = []

    max_touch = 5 if pipeline == "cw" else 4
    for touch in range(1, max_touch + 1):
        if total_sent + total_failed >= daily_limit:
            break
        leads = _get_due_leads(conn, pipeline, touch, limit=daily_limit - total_sent - total_failed)
        if not leads:
            logger.info(f"[{pipeline.upper()}] T{touch}: no leads due")
            continue

        logger.info(f"[{pipeline.upper()}] T{touch}: {len(leads)} leads due")
        subject_tpl, body_tpl = _load_template(pipeline, touch)

        for lead in leads:
            name = lead.get("name", "")
            email = lead.get("email", "")
            subject = subject_tpl
            body = _render(body_tpl, lead)

            if dry_run:
                logger.info(f"  [DRY-RUN] Would {'send' if auto_send else 'draft'}: {name} <{email}> | {subject}")
                results.append({"name": name, "email": email, "touch": touch, "status": "dry-run"})
                continue

            result_id = _create_draft(email, subject, body, pipeline, auto_send=auto_send)
            if result_id:
                _mark_sent(conn, lead["id"], touch, pipeline, subject)
                total_sent += 1
                results.append({"name": name, "email": email, "touch": touch,
                                 "status": "sent" if auto_send else "drafted"})
            else:
                total_failed += 1
                results.append({"name": name, "email": email, "touch": touch, "status": "failed"})

    conn.close()
    action = "sent" if auto_send else "drafted"
    logger.info(f"[{pipeline.upper()}] Sequence done: {total_sent} {action}, {total_failed} failed")
    return {"pipeline": pipeline, action: total_sent, "failed": total_failed, "results": results}


# ── CLI ───────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    parser = argparse.ArgumentParser(description="Run email sequence for a pipeline")
    parser.add_argument("--pipeline", choices=["cw", "sw"], required=True)
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    from dotenv import load_dotenv
    load_dotenv(override=True)

    summary = run_sequence(args.pipeline, dry_run=args.dry_run)
    print(json.dumps(summary, indent=2))
