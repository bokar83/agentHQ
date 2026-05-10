"""
skills/outreach/sequence_engine.py
===================================
5-touch email sequence engine for CW and SW pipelines.

Touch schedule (SW):
  T1 = Day 0  (first contact)
  T2 = Day 3
  T3 = Day 7
  T4 = Day 12 (breakup)
  T5 = Day 17 (SaaS audit upsell, different angle for non-responders)

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

# SW: 5 touches at Day 0/3/7/12/17 (T5 = SaaS audit upsell for non-responders)
# CW: 5 touches at Day 0/6/9/14/19 (T2 = SaaS PDF value-add)
# Studio: 4 touches at Day 0/5/11/18 (website + AI presence angle)
TOUCH_DAYS_SW = {1: 0, 2: 3, 3: 7, 4: 12, 5: 17}
TOUCH_DAYS_CW = {1: 0, 2: 6, 3: 9, 4: 14, 5: 19}
TOUCH_DAYS_STUDIO = {1: 0, 2: 5, 3: 11, 4: 18}

def _touch_days(pipeline: str) -> dict:
    if pipeline == "cw":
        return TOUCH_DAYS_CW
    if pipeline == "studio":
        return TOUCH_DAYS_STUDIO
    return TOUCH_DAYS_SW

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
        5: "templates.email.sw_t5",
    },
    "studio": {
        1: "templates.email.studio_t1",
        2: "templates.email.studio_t2",
        3: "templates.email.studio_t3",
        4: "templates.email.studio_t4",
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
        ("gmb_opener", "TEXT"),  # which T1 branch fired: no_website|low_reviews|chatgpt|generic
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

    if pipeline == "cw":
        source_filter = "apollo_catalyst_works%"
    elif pipeline == "studio":
        source_filter = "apollo_studio%"
    else:
        source_filter = "signal_works%"
    source_op = "LIKE"

    if touch == 1:
        cur.execute(f"""
            SELECT id, name, email, title, company, industry, city,
                   sequence_touch, sequence_pipeline,
                   review_count, has_website, google_rating, niche,
                   gmb_opener
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
                   sequence_touch, sequence_pipeline,
                   review_count, has_website, google_rating, niche,
                   gmb_opener
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

    # GMB qualification gate: SW T1 only.
    # Blocks unqualified leads (already well-reviewed, have website) from burning
    # sequence credits. Gate uses score_gmb_lead(); leads scoring < 2 are skipped.
    # T2-T5 are not gated — once enrolled, the sequence runs to completion.
    if pipeline == "sw" and touch == 1:
        try:
            from skills.serper_skill.hunter_tool import score_gmb_lead
        except ImportError:
            from serper_skill.hunter_tool import score_gmb_lead
        before = len(rows)
        qualified = []
        for r in rows:
            score, notes = score_gmb_lead(r)
            if score >= 2:
                r["gmb_signal_notes"] = notes
                # Determine which opener branch will fire — stored to DB so T2-T5 use
                # the same thread even if the lead's data changes between touches.
                if notes.get("no_website"):
                    r["gmb_opener"] = "no_website"
                elif notes.get("low_reviews") is not None:
                    r["gmb_opener"] = "low_reviews"
                elif r.get("niche"):
                    r["gmb_opener"] = "chatgpt"
                else:
                    r["gmb_opener"] = "generic"
                qualified.append(r)
        rows = qualified
        filtered = before - len(rows)
        if filtered:
            logger.info(f"[SW] T1 GMB gate: dropped {filtered} unqualified lead(s) (score < 2)")

    elif pipeline == "sw" and touch > 1:
        # Reconstruct gmb_signal_notes from stored gmb_opener for T2-T5.
        # This ensures the same thread fires regardless of data changes since T1.
        for r in rows:
            opener = r.get("gmb_opener") or ""
            if opener == "no_website":
                r["gmb_signal_notes"] = {"no_website": True}
            elif opener == "low_reviews":
                r["gmb_signal_notes"] = {"low_reviews": int(r.get("review_count", 0) or 0)}
            else:
                r["gmb_signal_notes"] = {}

    return rows


def _mark_sent(conn, lead_id: int, touch: int, pipeline: str, subject: str,
               gmb_opener: str = "") -> None:
    now = datetime.now(timezone.utc)
    cur = conn.cursor()
    if gmb_opener and touch == 1:
        cur.execute("""
            UPDATE leads
            SET sequence_touch = %s,
                sequence_pipeline = %s,
                last_contacted_at = %s,
                email_drafted_at = COALESCE(email_drafted_at, %s),
                updated_at = %s,
                gmb_opener = %s
            WHERE id = %s
        """, (touch, pipeline, now, now, now, gmb_opener, lead_id))
    else:
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
    """Return (subject, body_or_builder) for the given pipeline/touch.

    body_or_builder is either:
      - a callable build_body(lead) if the template defines it, or
      - a format-string BODY (legacy templates).
    """
    module_path = TEMPLATES[pipeline][touch]
    mod = importlib.import_module(module_path)
    subject = mod.SUBJECT
    if hasattr(mod, "build_body"):
        return subject, mod.build_body
    return subject, mod.BODY


# Tokens that indicate "name" is actually a business name, not a person.
_BUSINESS_TOKENS = {
    # Niches we target
    "plumbing", "roofing", "hvac", "dental", "chiropractic", "construction",
    "landscaping", "electric", "electrical", "heating", "cooling", "air",
    "pediatric", "medical", "clinic", "wellness", "health", "therapy",
    "automotive", "auto", "law", "legal", "accounting", "insurance",
    # Common business descriptors
    "commercial", "residential", "professional", "premier", "premium",
    "quality", "reliable", "trusted", "expert", "experts", "advanced",
    "complete", "total", "all", "first", "best", "top",
    "family", "local", "national", "american", "emergency",
    # Suffixes / generic words
    "solutions", "services", "service", "company", "co", "llc",
    "inc", "corp", "corporation", "group", "associates", "partners",
    "industries", "enterprises", "systems", "specialists", "specialist",
    "design", "build", "builders", "contractors", "contracting",
    # Articles / connectors
    "the", "and", "of", "for", "&", "a", "an",
    # Generic location/direction words
    "north", "south", "east", "west", "valley", "mountain",
    "hill", "hills", "creek", "river", "lake", "sky", "sun",
}

_LOCATION_TOKENS = {
    "utah", "ut", "salt", "lake", "city", "provo", "ogden", "sandy",
    "lehi", "park", "draper", "murray", "west", "jordan", "saint",
    "george", "logan", "cedar", "bountiful", "heber", "denver", "phoenix",
    "vegas", "boise", "albuquerque", "seattle", "portland", "diego",
    "reno", "tucson",
}


def _looks_like_business(token: str) -> bool:
    """Return True if the token looks like a business word, not a person first name."""
    if not token:
        return True
    low = token.lower().rstrip(",.;:'\"")
    return low in _BUSINESS_TOKENS or low in _LOCATION_TOKENS


# Common 4-7 char first names that begin with two consonants. Used to keep
# these as HIGH confidence even though the consonant-consonant heuristic
# below would otherwise flag them as initial+lastname patterns.
# Source: top US/UK first names from SSA + ONS that match the cons-cons shape.
_COMMON_CC_FIRST_NAMES = {
    "scott", "chris", "brian", "bryan", "glenn", "frank", "frans", "fred",
    "grant", "grace", "blake", "brent", "brett", "brock", "brody", "bruce",
    "clark", "claire", "craig", "drew", "drake", "dwight", "flynn", "ian",
    "jack", "jake", "jared", "jay", "joel", "jon", "kris", "kyle", "lane",
    "lex", "luke", "mason", "max", "miles", "neil", "noah", "owen", "phil",
    "phelps", "quinn", "reed", "reese", "rhett", "rhys", "rich", "rick",
    "ryan", "sean", "seth", "shane", "shawn", "skylar", "stan", "stephan",
    "steve", "stuart", "tate", "todd", "trace", "trent", "trey", "troy",
    "tyler", "vaughn", "wade", "wayne", "wes", "will", "wyatt",
}


def _looks_like_initial_plus_lastname(local: str) -> bool:
    """Detect 'gkirz', 'jsmith', 'mhall' pattern: single first-letter initial
    glued to a surname. These render as 'Hi Gkirz' which is wrong, so the
    caller should drop confidence to 'low' and skip the greeting.

    Heuristic: local-part has no separator, length 4-7, AND
      - first 2 chars are both consonants, AND
      - chars[1:] looks like a standalone surname (>=3 chars with a vowel
        within the first 3 positions).
    Allowlist of common cons-cons first names (Scott, Chris, Brian) escapes
    the rule so we don't over-flag legitimate names.
    """
    if not local or len(local) < 4 or len(local) > 7:
        return False
    if local in _COMMON_CC_FIRST_NAMES:
        return False
    vowels = set("aeiouy")
    if local[0] in vowels or local[1] in vowels:
        return False  # first 2 chars must be consonant-consonant
    rest = local[1:]
    if len(rest) < 3:
        return False
    if not any(c in vowels for c in rest[:3]):
        return False  # rest must look pronounceable (vowel within first 3 chars)
    return True


def _first_name_from_email(email: str) -> tuple[str, str]:
    """Parse a plausible first name from the local-part of an email.

    Returns (name, confidence) where confidence is "high" or "low":
      scott@commroof.com    -> ("Scott", "high")  -- allowlisted cons-cons name
      john.smith@x.com      -> ("John", "high")   -- dotted = clearly first.last
      jeff-campbell@x.com   -> ("Jeff", "high")   -- dashed = clearly first-last
      drmarcus@x.com        -> ("Marcus", "high") -- prefix stripped
      gkirz@x.com           -> ("Gkirz", "low")   -- initial+lastname pattern
      jsmith@x.com          -> ("Jsmith", "low")  -- initial+lastname pattern
      robsnow@x.com         -> ("Robsnow", "low") -- > 6 chars no separator
      lgrow@x.com           -> ("Lgrow", "low")   -- initial+lastname pattern
      j.smith@x.com         -> ("", "low")        -- single letter unreliable
      info@x.com            -> ("", "low")        -- role inbox
      ""                    -> ("", "low")
    """
    if not email or "@" not in email:
        return "", "low"
    local = email.split("@", 1)[0].lower()
    # Reject role inboxes outright
    if local in {"info", "contact", "hello", "hi", "support", "sales", "admin",
                 "office", "team", "service", "help", "owner", "ceo", "founder"}:
        return "", "low"
    # Detect explicit separator (dot or dash) which signals firstname.lastname
    has_separator = "." in local or "-" in local
    # Take the first dot/dash-separated token
    first = local.replace("-", ".").split(".")[0]
    # Strip digits
    first = "".join(c for c in first if c.isalpha())
    # Strip common professional prefixes (drmarcus -> marcus, drsmith -> smith)
    prefix_stripped = False
    for prefix in ("dr", "mr", "mrs", "ms"):
        if first.startswith(prefix) and len(first) >= len(prefix) + 3:
            first = first[len(prefix):]
            prefix_stripped = True
            break
    if len(first) < 2:
        return "", "low"
    name = first.capitalize()
    # Confidence rules:
    # - HIGH if the local-part had a separator (john.smith, jeff-campbell)
    # - HIGH if a prefix was stripped (drmarcus -> Marcus is intentional)
    # - LOW if the local-part looks like initial+lastname (gkirz, jsmith, mhall)
    # - HIGH if the local-part is short and looks like just a first name (scott, paul)
    # - LOW if the local-part is long (>6 chars) with no separator, suggesting
    #   firstinitial+lastname mash (lgrow, robsnow, mjohnson)
    if has_separator or prefix_stripped:
        return name, "high"
    # Initial+lastname catches the gkirz/jsmith/mhall pattern explicitly, even
    # when local is short. Without this guard, "gkirz" passes the <=6 length
    # check below and renders as "Hi Gkirz".
    if _looks_like_initial_plus_lastname(local):
        return name, "low"
    # No-separator locals: a short local (<=6 chars) is usually a clean first
    # name (paul, scott, brian, andrew, jordan, jodd). A longer local is
    # usually firstinitial+lastname mashed together which renders awkwardly
    # in a greeting -- so flag LOW and skip greeting.
    if len(local) <= 6:
        return name, "high"
    return name, "low"


def _extract_first_name(lead: dict) -> tuple[str, str]:
    """Best-effort first-name extraction from a lead dict.

    Returns (name, confidence) where confidence is "high" or "low".
    Templates use confidence to decide whether to render a greeting line:
      - confidence == "high": render "Hi {first_name},"
      - confidence == "low":  skip the greeting; body opens with the hook

    Strategy uses lead.source to decide whether lead.name is reliable:
      - source starts with "apollo_" or "cw_": lead.name is a real Apollo
        person ("Firstname Lastname"). Trust it (HIGH confidence).
      - source starts with "signal_works": lead.name is the business name
        from Google Maps. Never trust it. Parse from email; confidence
        depends on how clean the email parse is.

    Order of preference:
      1. lead["first_name"] if explicitly set (HIGH)
      2. For CW/apollo sources: first token of lead.name if 2+ tokens
         and not a business/location word (HIGH)
      3. Email local-part with confidence per _first_name_from_email
      4. Fallback: ("there", "low")
    """
    explicit = (lead.get("first_name") or "").strip()
    if explicit:
        return explicit, "high"

    source = (lead.get("source") or "").lower()
    is_sw = source.startswith("signal_works")
    is_cw = source.startswith("apollo_") or source.startswith("cw_")
    raw_name = (lead.get("name") or "").strip()

    # CW path: Apollo gives us real person names. Trust lead.name first.
    if is_cw and raw_name:
        tokens = raw_name.split()
        first_token = tokens[0].rstrip(",.;:'\"")
        if (len(tokens) >= 2
            and not _looks_like_business(first_token)
            and len(first_token) >= 2):
            return first_token, "high"

    # SW path OR CW name unusable: parse from email with confidence.
    from_email, email_conf = _first_name_from_email(lead.get("email", ""))
    if from_email:
        return from_email, email_conf

    # Unknown-source last resort: try the name even if single-token.
    if not is_sw and raw_name:
        tokens = raw_name.split()
        first_token = tokens[0].rstrip(",.;:'\"")
        if (not _looks_like_business(first_token)
            and len(first_token) >= 2):
            return first_token, "low"

    return "there", "low"


def _render(body_or_builder, lead: dict) -> str:
    """Render email body from either a build_body callable or a legacy format string.

    Adds first_name + first_name_confidence to the enriched lead so templates
    can decide whether to render a greeting line. See feedback_no_greeting_when_unknown.md
    for the rationale (cold email best-practice: drop greeting > use generic
    "Hi there").
    """
    first_name, confidence = _extract_first_name(lead)
    if callable(body_or_builder):
        enriched = dict(lead)
        if "first_name" not in enriched:
            enriched["first_name"] = first_name
        if "first_name_confidence" not in enriched:
            enriched["first_name_confidence"] = confidence
        if "niche" not in enriched:
            enriched["niche"] = (lead.get("industry") or "business").lower()
        if "city" not in enriched:
            enriched["city"] = lead.get("city") or "your city"
        if "business_name" not in enriched:
            enriched["business_name"] = lead.get("business_display_name") or lead.get("name") or "your business"
        if "review_count" not in enriched:
            enriched["review_count"] = int(lead.get("review_count", 0) or 0)
        if "gmb_signal_notes" not in enriched:
            enriched["gmb_signal_notes"] = lead.get("gmb_signal_notes", {})
        return body_or_builder(enriched)
    niche = (lead.get("industry") or "business").lower()
    city = lead.get("city") or "your city"
    return body_or_builder.format(first_name=first_name, niche=niche, city=city)


# ── Main runner ───────────────────────────────────────────────────────────────

def run_sequence(pipeline: str, dry_run: bool = False, daily_limit: int = 10) -> dict:
    """
    Process all due touches for a pipeline up to daily_limit total emails.
    Auto-send controlled by AUTO_SEND_CW / AUTO_SEND_SW env vars (default: draft).
    Returns summary dict.
    """
    auto_send_cw = os.environ.get("AUTO_SEND_CW", "false").lower() == "true"
    auto_send_sw = os.environ.get("AUTO_SEND_SW", "false").lower() == "true"
    auto_send_studio = os.environ.get("AUTO_SEND_STUDIO", "false").lower() == "true"
    if pipeline == "cw":
        auto_send = auto_send_cw
    elif pipeline == "studio":
        auto_send = auto_send_studio
    else:
        auto_send = auto_send_sw
    conn = _get_conn()
    _ensure_sequence_columns(conn)

    total_sent = 0
    total_failed = 0
    results = []

    max_touch = 5 if pipeline in ("cw", "sw") else 4
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
                _mark_sent(conn, lead["id"], touch, pipeline, subject,
                           gmb_opener=lead.get("gmb_opener", ""))
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
