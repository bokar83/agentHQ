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

    NOTION_DB_ID = "619a842a0e044cb38d1719ec67c130f0"  # CRM Leads page ID
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
        return s if s in ("new", "contacted", "replied", "meeting", "closed", "disqualified") else "new"

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

        try:
            if email and email in existing:
                # Update existing page
                page_id = existing[email]
                resp = httpx.patch(
                    f"https://api.notion.com/v1/pages/{page_id}",
                    headers=notion_headers,
                    json={"properties": props},
                    timeout=15,
                )
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
