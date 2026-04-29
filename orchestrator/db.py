"""
db.py — Database connection utilities for agentsHQ
===================================================
Supabase is the primary CRM database.
Local Postgres is the fallback -- used only when Supabase is unreachable.
A background sync job moves any local fallback data to Supabase when it recovers.

Rule: Local Postgres leads table should always be empty.
      If it has rows, Supabase was unreachable and a sync is needed.
"""

import os
import logging

logger = logging.getLogger(__name__)


CREATE_CONTENT_APPROVALS = """
CREATE TABLE IF NOT EXISTS content_approvals (
    id               SERIAL PRIMARY KEY,
    notion_page_id   TEXT NOT NULL,
    attempt_number   INTEGER NOT NULL DEFAULT 1,
    submitted_at     TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    decided_at       TIMESTAMPTZ,
    decision         TEXT NOT NULL,
    evergreen        BOOLEAN NOT NULL DEFAULT FALSE,
    platform         TEXT NOT NULL,
    griot_score      FLOAT,
    chairman_score   FLOAT
);
"""


CREATE_CHAT_ARTIFACTS = """
CREATE TABLE IF NOT EXISTS chat_artifacts (
    artifact_id   TEXT PRIMARY KEY,
    session_id    TEXT NOT NULL,
    turn_number   INTEGER NOT NULL,
    artifact_type TEXT NOT NULL,
    content       TEXT NOT NULL,
    created_at    TIMESTAMPTZ DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS chat_artifacts_session_turn
    ON chat_artifacts (session_id, turn_number);
"""


CREATE_EMAIL_JOBS = """
CREATE TABLE IF NOT EXISTS email_jobs (
    id         SERIAL PRIMARY KEY,
    to_addr    TEXT NOT NULL,
    subject    TEXT NOT NULL,
    body_text  TEXT NOT NULL,
    send_at    TIMESTAMPTZ NOT NULL,
    status     TEXT NOT NULL DEFAULT 'pending',
    created_at TIMESTAMPTZ DEFAULT now(),
    sent_at    TIMESTAMPTZ,
    error_msg  TEXT
);
"""


def ensure_chat_artifacts_table() -> None:
    """Create chat_artifacts table if it does not exist (idempotent)."""
    conn = get_local_connection()
    try:
        cur = conn.cursor()
        cur.execute(CREATE_CHAT_ARTIFACTS)
        conn.commit()
        cur.close()
    except Exception as e:
        logger.warning(f"ensure_chat_artifacts_table failed: {e}")
    finally:
        conn.close()


def save_chat_artifact(artifact_id: str, session_id: str, turn_number: int,
                       artifact_type: str, content: str) -> None:
    conn = get_local_connection()
    try:
        cur = conn.cursor()
        cur.execute(
            """INSERT INTO chat_artifacts (artifact_id, session_id, turn_number, artifact_type, content)
               VALUES (%s, %s, %s, %s, %s)
               ON CONFLICT (artifact_id) DO UPDATE SET content = EXCLUDED.content""",
            (artifact_id, session_id, turn_number, artifact_type, content),
        )
        conn.commit()
        cur.close()
    except Exception as e:
        logger.warning(f"save_chat_artifact failed: {e}")
    finally:
        conn.close()


def get_chat_artifact(artifact_id: str) -> dict | None:
    conn = get_local_connection()
    try:
        cur = conn.cursor()
        cur.execute("SELECT * FROM chat_artifacts WHERE artifact_id = %s", (artifact_id,))
        row = cur.fetchone()
        cur.close()
        return dict(row) if row else None
    except Exception as e:
        logger.warning(f"get_chat_artifact failed: {e}")
        return None
    finally:
        conn.close()


CREATE_VIDEO_JOBS = """
CREATE TABLE IF NOT EXISTS video_jobs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    job_type TEXT NOT NULL,
    status TEXT DEFAULT 'pending',
    priority INT DEFAULT 5,
    prompt TEXT,
    params_json JSONB DEFAULT '{}'::jsonb,
    result_json JSONB,
    error_msg TEXT,
    attempts INT DEFAULT 0,
    max_attempts INT DEFAULT 3,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    dispatched_at TIMESTAMPTZ,
    completed_at TIMESTAMPTZ,
    linked_content_id TEXT,
    requested_by TEXT DEFAULT 'system',
    feature_flag TEXT DEFAULT 'video_crew_v1'
);

CREATE INDEX IF NOT EXISTS idx_video_jobs_status
    ON video_jobs (status, priority, created_at);

CREATE INDEX IF NOT EXISTS idx_video_jobs_job_type
    ON video_jobs (job_type, status);
"""


def ensure_content_approvals_table() -> None:
    """Create content_approvals table if it does not exist (idempotent).

    Called by app startup and griot module init. Safe to call multiple times.
    """
    conn = get_local_connection()
    try:
        cur = conn.cursor()
        cur.execute(CREATE_CONTENT_APPROVALS)
        conn.commit()
        cur.close()
    except Exception as e:
        logger.warning(f"ensure_content_approvals_table failed: {e}")
    finally:
        conn.close()


def ensure_video_jobs_table() -> None:
    """Create video_jobs table if it does not exist (idempotent).

    Called by app startup and video crew module init. Safe to call multiple times.
    """
    conn = get_local_connection()
    try:
        cur = conn.cursor()
        cur.execute(CREATE_VIDEO_JOBS)
        conn.commit()
        cur.close()
    except Exception as e:
        logger.warning(f"ensure_video_jobs_table failed: {e}")
    finally:
        conn.close()


def get_crm_connection():
    """
    Return a psycopg2 connection to the Supabase CRM database.
    Builds connection from SUPABASE_HOST, SUPABASE_USER, SUPABASE_PASSWORD, SUPABASE_DB
    to avoid shell escaping issues with special characters in the password.
    """
    import psycopg2
    import psycopg2.extras

    import base64
    host = os.environ.get("SUPABASE_HOST")
    user = os.environ.get("SUPABASE_USER")
    # Password stored as base64 to survive Docker/shell variable interpolation of special chars
    password_b64 = os.environ.get("SUPABASE_PASSWORD_B64")
    password = base64.b64decode(password_b64).decode("utf-8") if password_b64 else None
    dbname = os.environ.get("SUPABASE_DB", "postgres")
    port = int(os.environ.get("SUPABASE_PORT", 6543))

    if not all([host, user, password]):
        raise RuntimeError("Supabase connection vars not set (SUPABASE_HOST, SUPABASE_USER, SUPABASE_PASSWORD_B64).")

    conn = psycopg2.connect(
        host=host,
        port=port,
        dbname=dbname,
        user=user,
        password=password,
        connect_timeout=5,
        cursor_factory=psycopg2.extras.RealDictCursor,
        sslmode="require",
    )
    return conn


def get_local_connection():
    """
    Return a psycopg2 connection to the local Postgres database.
    Used as fallback when Supabase is unreachable, and for task queue / chat history.
    """
    import psycopg2
    import psycopg2.extras

    conn = psycopg2.connect(
        host=os.environ.get("POSTGRES_HOST", "postgres"),
        port=int(os.environ.get("POSTGRES_PORT", 5432)),
        dbname=os.environ.get("POSTGRES_DB", "postgres"),
        user=os.environ.get("POSTGRES_USER", "postgres"),
        password=os.environ.get("POSTGRES_PASSWORD", ""),
        cursor_factory=psycopg2.extras.RealDictCursor,
    )
    return conn


def get_crm_connection_with_fallback() -> tuple:
    """
    Try Supabase first. If unavailable, fall back to local Postgres.
    Returns (conn, is_fallback) tuple.
    Callers should log a warning if is_fallback is True.
    """
    try:
        conn = get_crm_connection()
        return conn, False
    except Exception as e:
        logger.warning(f"Supabase unavailable ({e}), falling back to local Postgres.")
        conn = get_local_connection()
        return conn, True


def sync_supabase_to_notion() -> int:
    """
    Read all leads from Supabase and upsert them into the Notion CRM Leads database.
    Matches on email (unique identifier). Creates new pages for new leads, updates
    existing pages for changed leads.
    Returns number of leads synced.
    """
    import httpx

    NOTION_DB_ID = os.environ.get("NOTION_CRM_LEADS_DB_ID", "619a842a0e044cb38d1719ec67c130f0")
    notion_token = (
        os.environ.get("NOTION_API_KEY")
        or os.environ.get("NOTION_TOKEN")
        or os.environ.get("NOTION_SECRET")
    )
    if not notion_token:
        logger.error("NOTION SYNC: No Notion token found -- skipping.")
        return 0

    notion_headers = {
        "Authorization": f"Bearer {notion_token}",
        "Notion-Version": "2022-06-28",
        "Content-Type": "application/json",
    }

    def _notion_status(s: str) -> str:
        """Map Supabase status values to Notion select options."""
        mapping = {
            "new": "new",
            "messaged": "contacted",
            "contacted": "contacted",
            "replied": "replied",
            "meeting": "meeting",
            "booked": "meeting",
            "closed": "closed",
            "paid": "closed",
            "disqualified": "disqualified",
        }
        return mapping.get(s, "new") if s else "new"

    def _notion_priority(p) -> str:
        """Map Supabase priority (int) to Notion select option."""
        mapping = {1: "🥇 P1", 2: "🥈 P2", 3: "🥉 P3", 4: "P4", 5: "P5"}
        try:
            return mapping.get(int(p), "P4")
        except (TypeError, ValueError):
            return "P4"

    def _notion_industry(i: str) -> str:
        valid = ("Legal", "Accounting", "Marketing Agency", "HVAC", "Plumbing", "Roofing", "Other")
        if not i:
            return "Other"
        for v in valid:
            if v.lower() in i.lower():
                return v
        return "Other"

    def _notion_source(s: str) -> str:
        if not s:
            return "Manual"
        s_lower = s.lower()
        if "hunter" in s_lower:
            return "Hunter"
        if "apollo" in s_lower:
            return "Apollo"
        if "serper_linkedin" in s_lower or "linkedin" in s_lower:
            return "LinkedIn"
        if "serper" in s_lower:
            return "Serper"
        if "boubacarbarry" in s_lower:
            return "boubacarbarry.com"
        if "catalystworks" in s_lower:
            return "catalystworks.consulting"
        return "Manual"

    # Build email -> page_id map from existing Notion CRM pages
    existing = {}
    try:
        cursor = None
        while True:
            body = {"page_size": 100}
            if cursor:
                body["start_cursor"] = cursor
            resp = httpx.post(
                f"https://api.notion.com/v1/databases/{NOTION_DB_ID}/query",
                headers=notion_headers,
                json=body,
                timeout=20,
            )
            if resp.status_code != 200:
                logger.error(f"NOTION SYNC: Failed to query CRM Leads DB: {resp.status_code} {resp.text[:200]}")
                return 0
            data = resp.json()
            for page in data.get("results", []):
                email_prop = page.get("properties", {}).get("Email", {})
                email = email_prop.get("email") or ""
                if email:
                    existing[email.lower()] = page["id"]
            if not data.get("has_more"):
                break
            cursor = data.get("next_cursor")
    except Exception as e:
        logger.error(f"NOTION SYNC: Error fetching existing Notion pages: {e}")
        return 0

    # Fetch all leads from Supabase
    try:
        conn = get_crm_connection()
        cur = conn.cursor()
        cur.execute("SELECT * FROM leads ORDER BY created_at DESC")
        leads = cur.fetchall()
        cur.close()
        conn.close()
    except Exception as e:
        logger.error(f"NOTION SYNC: Failed to fetch leads from Supabase: {e}")
        return 0

    synced = 0
    for lead in leads:
        email = (lead.get("email") or "").lower()
        name = lead.get("name") or "Unknown"

        props = {
            "Name": {"title": [{"text": {"content": name}}]},
        }
        if lead.get("company"):
            props["Company"] = {"rich_text": [{"text": {"content": lead["company"]}}]}
        if lead.get("title"):
            props["Title"] = {"rich_text": [{"text": {"content": lead["title"]}}]}
        if lead.get("location"):
            props["Location"] = {"rich_text": [{"text": {"content": lead["location"]}}]}
        if email:
            props["Email"] = {"email": email}
        if lead.get("phone"):
            props["Phone"] = {"phone_number": lead["phone"]}
        if lead.get("linkedin_url"):
            props["LinkedIn"] = {"url": lead["linkedin_url"]}
        if lead.get("industry"):
            props["Industry"] = {"select": {"name": _notion_industry(lead["industry"])}}
        if lead.get("source"):
            props["Source"] = {"select": {"name": _notion_source(lead["source"])}}
        if lead.get("status"):
            props["Status"] = {"select": {"name": _notion_status(lead["status"])}}
        if lead.get("created_at"):
            props["Lead Date"] = {"date": {"start": str(lead["created_at"])[:10]}}
        if lead.get("last_contacted_at"):
            props["Last Contacted"] = {"date": {"start": str(lead["last_contacted_at"])[:10]}}
        if lead.get("notes"):
            props["Notes"] = {"rich_text": [{"text": {"content": str(lead["notes"])[:2000]}}]}
        if lead.get("priority") is not None:
            props["Priority"] = {"select": {"name": _notion_priority(lead["priority"])}}

        try:
            if email and email in existing:
                # Update existing page matched by email
                page_id = existing[email]
                resp = httpx.patch(
                    f"https://api.notion.com/v1/pages/{page_id}",
                    headers=notion_headers,
                    json={"properties": props},
                    timeout=15,
                )
            # NOTE: _id_map lookup removed — existing{} is keyed by email only.
            # No-email leads always create a new Notion page (acceptable: rare case).
            else:
                # Create new page
                resp = httpx.post(
                    "https://api.notion.com/v1/pages",
                    headers=notion_headers,
                    json={
                        "parent": {"database_id": NOTION_DB_ID},
                        "properties": props,
                    },
                    timeout=15,
                )
            if resp.status_code in (200, 201):
                synced += 1
            else:
                logger.error(f"NOTION SYNC: Failed for {name}: {resp.status_code} {resp.text[:200]}")
        except Exception as e:
            logger.error(f"NOTION SYNC: Exception for lead {name}: {e}")

    logger.info(f"NOTION SYNC: {synced}/{len(leads)} leads synced to Notion CRM.")
    return synced


def sync_fallback_to_supabase() -> int:
    """
    Move any leads written to local Postgres fallback back to Supabase.
    Called on orchestrator startup and periodically by the scheduler.
    Returns number of rows synced.
    """
    import psycopg2.extras

    try:
        local_conn = get_local_connection()
        local_cur = local_conn.cursor()

        # Check for any leads in local fallback
        local_cur.execute("SELECT * FROM leads ORDER BY created_at ASC")
        rows = local_cur.fetchall()

        if not rows:
            local_cur.close()
            local_conn.close()
            return 0

        logger.info(f"Sync: found {len(rows)} fallback lead(s) to sync to Supabase.")

        supabase_conn = get_crm_connection()
        supabase_cur = supabase_conn.cursor()

        synced = 0
        for row in rows:
            try:
                supabase_cur.execute("""
                    INSERT INTO leads
                        (name, company, title, location, phone, linkedin_url, email,
                         industry, source, status, last_contacted_at, created_at, updated_at)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    ON CONFLICT DO NOTHING
                """, (
                    row['name'], row['company'], row['title'], row['location'],
                    row['phone'], row['linkedin_url'], row['email'],
                    row['industry'], row['source'], row['status'],
                    row.get('last_contacted_at'), row['created_at'], row['updated_at'],
                ))
                synced += 1
            except Exception as e:
                logger.error(f"Sync: failed to insert lead {row.get('name')}: {e}")

        supabase_conn.commit()
        supabase_cur.close()
        supabase_conn.close()

        # Clear local fallback rows that were synced
        local_cur.execute("DELETE FROM leads WHERE id = ANY(%s)", ([r['id'] for r in rows],))
        local_conn.commit()
        local_cur.close()
        local_conn.close()

        logger.info(f"Sync: {synced} lead(s) moved from local Postgres to Supabase.")
        return synced

    except Exception as e:
        logger.error(f"sync_fallback_to_supabase failed: {e}")
        return 0


def upsert_signal_works_lead(lead: dict) -> None:
    """Insert or update a Signal Works lead in Supabase leads table.

    Strategy:
    - If email is present: upsert on email (unique constraint).
    - If no email: check for existing row by (name, city) to avoid duplicates, then insert.
    All rows get source='signal_works' and lead_type from the lead dict (default 'website_prospect').
    Baseline (review_count + rating) is captured on first insert only -- never overwritten.
    Uses dedicated columns -- no JSON blobs for filterable fields.
    """
    import json
    from datetime import date
    conn = get_crm_connection()
    email = lead.get("email", "").strip()
    name = lead.get("name", "")
    city = lead.get("city", "")
    ai_breakdown = lead.get("ai_breakdown")
    breakdown_json = json.dumps(ai_breakdown) if ai_breakdown else None
    review_count = int(lead.get("review_count", 0) or 0)
    ai_score = int(lead.get("ai_score", 0) or 0)
    google_rating = lead.get("google_rating") or None
    has_website = bool(lead.get("has_website", bool(lead.get("website_url", ""))))
    google_address = lead.get("google_address", "") or ""
    today = date.today().isoformat()

    # 12 mutable non-identity fields: website_url onward.
    # Phone is always passed explicitly as the first arg before this tuple in UPDATE,
    # and as position 3 in INSERT (after name, email).
    def _vals():
        return (
            lead.get("website_url", ""),
            has_website,
            review_count,
            ai_score,
            google_rating,
            google_address,
            lead.get("google_maps_url", ""),
            lead.get("niche", ""),
            city,
            lead.get("lead_type", "website_prospect"),
            breakdown_json,
            lead.get("ai_quick_wins", ""),
        )

    _UPDATE_COLS = """
        phone=%s, website_url=%s, has_website=%s,
        review_count=%s, ai_score=%s, google_rating=%s,
        google_address=%s, google_maps_url=%s, niche=%s,
        city=%s, lead_type=%s, ai_breakdown=%s, ai_quick_wins=%s
    """

    try:
        with conn.cursor() as cur:
            # Dedup: look up by email (if present) or name+city. No ON CONFLICT needed.
            if email:
                cur.execute(
                    "SELECT id, baseline_reviews FROM leads WHERE email=%s AND source='signal_works'",
                    (email,),
                )
            else:
                cur.execute(
                    "SELECT id, baseline_reviews FROM leads WHERE name=%s AND city=%s AND source='signal_works'",
                    (name, city),
                )
            existing = cur.fetchone()

            if existing:
                row_id = existing['id']
                has_baseline = existing['baseline_reviews'] is not None
                if has_baseline:
                    cur.execute(
                        f"UPDATE leads SET email=%s, {_UPDATE_COLS}, updated_at=NOW() WHERE id=%s",
                        (email, lead.get("phone", ""), *_vals(), row_id),
                    )
                else:
                    cur.execute(
                        f"""UPDATE leads SET email=%s, {_UPDATE_COLS},
                            baseline_reviews=%s, baseline_rating=%s, baseline_date=%s,
                            updated_at=NOW() WHERE id=%s""",
                        (email, lead.get("phone", ""), *_vals(), review_count, google_rating, today, row_id),
                    )
            else:
                cur.execute(
                    """
                    INSERT INTO leads (
                        name, email, phone, company, location, source, status,
                        website_url, has_website, review_count, ai_score,
                        google_rating, google_address, google_maps_url,
                        niche, city, lead_type, ai_breakdown, ai_quick_wins,
                        baseline_reviews, baseline_rating, baseline_date,
                        created_at, updated_at
                    )
                    VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,NOW(),NOW())
                    """,
                    (
                        name, email, lead.get("phone", ""),
                        name, city, "signal_works", "new",
                        *_vals(),
                        review_count, google_rating, today,
                    ),
                )
        conn.commit()
    except Exception as exc:
        logger.warning(f"upsert_signal_works_lead failed: {exc}")
        try:
            conn.rollback()
        except Exception:
            pass
    finally:
        conn.close()


def ensure_leads_columns(conn) -> None:
    """Add no_website, email_source, last_drafted_at, apollo_id columns if not present.

    Idempotent. Safe to call from morning_runner each run.
    """
    cur = conn.cursor()
    for col, definition in [
        ("no_website", "BOOLEAN DEFAULT FALSE"),
        ("email_source", "TEXT"),
        ("last_drafted_at", "TIMESTAMPTZ"),
        ("apollo_id", "TEXT"),
    ]:
        try:
            cur.execute(f"ALTER TABLE leads ADD COLUMN IF NOT EXISTS {col} {definition}")
        except Exception as e:
            logger.warning(f"ensure_leads_columns: {col} alter failed: {e}")
    try:
        conn.commit()
    except Exception as e:
        logger.warning(f"ensure_leads_columns: commit failed: {e}")


def get_resend_queue(limit: int = 5, days_back: int = 60) -> list[dict]:
    """Return oldest-revealed Apollo contacts NOT touched in `days_back` days.

    Used by CW topup as the resend pool. Pairs with the apollo_revealed dedup
    table (apollo_id, revealed_at, email, name).
    """
    conn = get_crm_connection_with_fallback()[0]
    cur = conn.cursor()
    cur.execute(
        """
        SELECT apollo_id, email, name, revealed_at
        FROM apollo_revealed
        WHERE email IS NOT NULL
          AND revealed_at < NOW() - (%s || ' days')::interval
          AND apollo_id NOT IN (
              SELECT apollo_id FROM leads
              WHERE last_drafted_at > NOW() - (%s || ' days')::interval
                AND apollo_id IS NOT NULL
          )
        ORDER BY revealed_at ASC
        LIMIT %s
        """,
        (str(days_back), str(days_back), limit),
    )
    rows = [dict(r) for r in cur.fetchall()]
    conn.close()
    return rows


def ensure_email_jobs_table() -> None:
    """Create email_jobs table if it does not exist (idempotent)."""
    conn = get_local_connection()
    try:
        cur = conn.cursor()
        cur.execute(CREATE_EMAIL_JOBS)
        conn.commit()
        cur.close()
    except Exception as e:
        logger.warning(f"ensure_email_jobs_table failed: {e}")
    finally:
        conn.close()


CREATE_SESSION_SUMMARIES = """
CREATE TABLE IF NOT EXISTS session_summaries (
    id            SERIAL PRIMARY KEY,
    session_id    TEXT NOT NULL,
    summary       TEXT NOT NULL,
    turn_count    INTEGER NOT NULL,
    created_at    TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    window_end_at TIMESTAMPTZ NOT NULL,
    tags          TEXT[]
);
CREATE INDEX IF NOT EXISTS idx_session_summaries_session
    ON session_summaries (session_id, created_at DESC);
"""


def ensure_session_summaries_table() -> None:
    """Create session_summaries table if it does not exist (idempotent)."""
    conn = get_local_connection()
    try:
        cur = conn.cursor()
        cur.execute(CREATE_SESSION_SUMMARIES)
        conn.commit()
        cur.close()
    except Exception as e:
        logger.warning(f"ensure_session_summaries_table failed: {e}")
    finally:
        conn.close()


def save_session_summary(session_id: str, summary: str, turn_count: int,
                         window_end_at: str) -> None:
    """Persist a compressed session summary."""
    conn = get_local_connection()
    try:
        cur = conn.cursor()
        cur.execute(
            """INSERT INTO session_summaries (session_id, summary, turn_count, window_end_at)
               VALUES (%s, %s, %s, %s)""",
            (session_id, summary, turn_count, window_end_at),
        )
        conn.commit()
        cur.close()
    except Exception as e:
        logger.warning(f"save_session_summary failed: {e}")
    finally:
        conn.close()


def get_latest_session_summary(session_id: str, max_age_hours: int = 24) -> dict | None:
    """Return the most recent summary for a session, within max_age_hours. None if none found."""
    conn = get_local_connection()
    try:
        cur = conn.cursor()
        cur.execute(
            """SELECT summary, turn_count, created_at, window_end_at
               FROM session_summaries
               WHERE session_id = %s
                 AND created_at > NOW() - INTERVAL '%s hours'
               ORDER BY created_at DESC
               LIMIT 1""",
            (session_id, max_age_hours),
        )
        row = cur.fetchone()
        cur.close()
        if not row:
            return None
        return {
            "summary": row[0],
            "turn_count": row[1],
            "created_at": row[2],
            "window_end_at": row[3],
        }
    except Exception as e:
        logger.warning(f"get_latest_session_summary failed: {e}")
        return None
    finally:
        conn.close()


def fetch_pending_email_jobs() -> list[dict]:
    conn = get_local_connection()
    try:
        cur = conn.cursor()
        cur.execute(
            """
            SELECT * FROM email_jobs
            WHERE status = 'pending' AND send_at <= now()
            ORDER BY send_at
            """
        )
        rows = cur.fetchall()
        cur.close()
        return [dict(row) for row in rows]
    except Exception as e:
        logger.warning(f"fetch_pending_email_jobs failed: {e}")
        return []
    finally:
        conn.close()


def mark_email_job_sent(job_id: int) -> None:
    conn = get_local_connection()
    try:
        cur = conn.cursor()
        cur.execute(
            """
            UPDATE email_jobs
            SET status = 'sent', sent_at = now()
            WHERE id = %s
            """,
            (job_id,),
        )
        conn.commit()
        cur.close()
    except Exception as e:
        logger.warning(f"mark_email_job_sent failed for {job_id}: {e}")
    finally:
        conn.close()


def mark_email_job_failed(job_id: int, error: str) -> None:
    conn = get_local_connection()
    try:
        cur = conn.cursor()
        cur.execute(
            """
            UPDATE email_jobs
            SET status = 'failed', error_msg = %s
            WHERE id = %s
            """,
            (error, job_id),
        )
        conn.commit()
        cur.close()
    except Exception as e:
        logger.warning(f"mark_email_job_failed failed for {job_id}: {e}")
    finally:
        conn.close()


def insert_email_job(to_addr, subject, body_text, send_at) -> int | None:
    conn = get_local_connection()
    try:
        cur = conn.cursor()
        cur.execute(
            """
            INSERT INTO email_jobs (to_addr, subject, body_text, send_at)
            VALUES (%s, %s, %s, %s)
            RETURNING id
            """,
            (to_addr, subject, body_text, send_at),
        )
        row = cur.fetchone()
        conn.commit()
        cur.close()
        if not row:
            return None
        return int(row["id"])
    except Exception as e:
        logger.warning(f"insert_email_job failed: {e}")
        return None
    finally:
        conn.close()


def get_leads_for_drafting(limit: int = 10) -> list[dict]:
    """Return up to `limit` Signal Works leads that have an email but no draft yet.
    Ordered by ai_score ASC (lowest score = most urgent pitch goes first)."""
    conn = get_crm_connection()
    try:
        cur = conn.cursor()
        cur.execute(
            """
            SELECT id, name, email, niche, city, ai_score, ai_breakdown, ai_quick_wins,
                   website_url, google_rating, review_count
            FROM leads
            WHERE lead_type = 'website_prospect'
              AND email IS NOT NULL AND email != ''
              AND (email_drafted IS NULL OR email_drafted = FALSE)
            ORDER BY ai_score ASC NULLS LAST
            LIMIT %s
            """,
            (limit,),
        )
        rows = cur.fetchall()
        return [dict(r) for r in rows]
    except Exception as e:
        logger.warning(f"get_leads_for_drafting failed: {e}")
        return []
    finally:
        conn.close()


def mark_email_drafted(lead_id: int, draft_id: str = "") -> None:
    """Mark a lead as having a Gmail draft created."""
    conn = get_crm_connection()
    try:
        cur = conn.cursor()
        cur.execute(
            """
            UPDATE leads
            SET email_drafted = TRUE,
                email_drafted_at = NOW()
            WHERE id = %s
            """,
            (lead_id,),
        )
        conn.commit()
        cur.close()
    except Exception as e:
        logger.warning(f"mark_email_drafted failed for lead {lead_id}: {e}")
        conn.rollback()
    finally:
        conn.close()
