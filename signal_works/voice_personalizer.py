"""
signal_works/voice_personalizer.py

Per-lead voice personalization. Scrapes the lead's website, extracts a voice
fingerprint via skills.transcript-style-dna.extract, returns the opener line.

Best-effort. Never raises. Returns None on any failure (lead falls back to
template-only opener in email_builder._opening).
"""
import importlib.util
import logging
import sys
from pathlib import Path
from typing import Optional

# Ensure repo root is importable
_REPO_ROOT = Path(__file__).resolve().parents[1]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from signal_works.lead_scraper import fetch_site_text, find_company_website  # noqa: E402

# transcript-style-dna lives in a hyphenated dir, which Python cannot
# import normally. Load via importlib.
_EXTRACT_PATH = _REPO_ROOT / "skills" / "transcript-style-dna" / "extract.py"
_spec = importlib.util.spec_from_file_location("transcript_style_dna_extract", _EXTRACT_PATH)
_extract_mod = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_extract_mod)
extract = _extract_mod.extract

logger = logging.getLogger(__name__)

# Refuse to call the LLM on near-empty pages: noise in, noise out.
# 200 chars is roughly a hero section + tagline. Below that, extract has
# insufficient signal to produce a non-generic opener. Tune after lift-test
# data is in.
MIN_TEXT_CHARS = 200

# Hard cap on refs we send. 8000 chars is roughly 2k tokens; one decent
# homepage is enough signal for a voice fingerprint, and more text dilutes
# the opener with boilerplate. Tune after lift-test data is in.
MAX_REF_CHARS = 8000


def _strip_dashes(s: str) -> str:
    """Belt-and-suspenders em/en-dash scrub. Mirrors extract.py."""
    if not isinstance(s, str):
        return s
    return s.replace("\u2014", ", ").replace("\u2013", ", ")


def _personalize_one(lead: dict) -> Optional[str]:
    """
    Compute the voice line for one lead. Returns None on any miss.

    Private to this module. The only public surface is personalize_pending_leads.
    Exposed (with leading underscore) so unit tests can pin the contract directly
    without spinning up a DB.
    """
    url = (lead.get("website_url") or "").strip()
    if not url:
        # CW Apollo leads ship without website_url; derive from company name + city
        company = (lead.get("company") or lead.get("name") or "").strip()
        city = (lead.get("city") or "").strip()
        url = find_company_website(company, city)
        if not url:
            logger.info(
                f"voice_personalizer: skip lead={lead.get('id')} name={lead.get('name')!r} "
                f"reason=no_website company={company!r}"
            )
            return None
        logger.info(
            f"voice_personalizer: derived website lead={lead.get('id')} url={url}"
        )

    text = fetch_site_text(url)
    text_len = len(text or "")
    if not text or text_len < MIN_TEXT_CHARS:
        # Instrumentation tag: lift-test eval distinguishes thin-input from bad-skill
        logger.info(
            f"voice_personalizer: skip lead={lead.get('id')} name={lead.get('name')!r} "
            f"reason=thin_text chars={text_len} url={url}"
        )
        return None

    refs = [text[:MAX_REF_CHARS]]
    target_context = (
        f"prospect runs a {lead.get('niche') or 'local business'} "
        f"named {lead.get('name') or 'the business'} in "
        f"{lead.get('city') or 'their city'}. "
        f"This opener is the first line of a cold email from us, written in their voice."
    )

    try:
        profile = extract(refs, target_context)
    except Exception as exc:
        logger.warning(
            f"voice_personalizer: skip lead={lead.get('id')} reason=extract_error err={exc}"
        )
        return None

    line = (profile or {}).get("opener_line") or ""
    line = _strip_dashes(line).strip()
    confidence = (profile or {}).get("confidence", "unknown")
    if not line:
        logger.info(
            f"voice_personalizer: skip lead={lead.get('id')} reason=empty_opener confidence={confidence}"
        )
        return None

    # Success path instrumentation
    logger.info(
        f"voice_personalizer: ok lead={lead.get('id')} name={lead.get('name')!r} "
        f"chars={text_len} confidence={confidence}"
    )
    return line


def personalize_pending_leads(limit: int = 10) -> int:
    """
    Find up to `limit` un-personalized CW leads with a website + email,
    populate voice_personalization_line for each. Returns count populated.

    Called by morning_runner Step 4.5.
    """
    # Container vs dev: orchestrator/* is flattened to /app in orc-crewai.
    try:
        from orchestrator.db import get_crm_connection
    except ModuleNotFoundError:
        sys.path.insert(0, "/app")
        from db import get_crm_connection

    conn = get_crm_connection()
    populated = 0
    try:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT id, name, company, niche, city, website_url
                FROM leads
                WHERE voice_personalization_line IS NULL
                  AND COALESCE(email, '') <> ''
                  AND (sequence_touch IS NULL OR sequence_touch = 0)
                  AND source = 'apollo_catalyst_works'
                ORDER BY created_at DESC
                LIMIT %s
                """,
                (limit,),
            )
            rows = cur.fetchall()
            cols = [d[0] for d in cur.description]

        for row in rows:
            # rows from psycopg2 RealDictCursor are dict-like; otherwise zip with cols
            if isinstance(row, dict):
                lead = dict(row)
            else:
                lead = dict(zip(cols, row))
            line = _personalize_one(lead)
            if line is None:
                continue
            with conn.cursor() as cur:
                cur.execute(
                    """
                    UPDATE leads
                    SET voice_personalization_line = %s
                    WHERE id = %s
                    """,
                    (line, lead["id"]),
                )
            conn.commit()
            populated += 1
            logger.info(
                f"voice_personalizer: lead {lead['id']} {lead['name']!r} -> {line[:80]!r}"
            )
    finally:
        conn.close()

    return populated


if __name__ == "__main__":
    import argparse
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    ap = argparse.ArgumentParser()
    ap.add_argument("--limit", type=int, default=10, help="max leads to personalize this run")
    args = ap.parse_args()
    n = personalize_pending_leads(limit=args.limit)
    print(f"Populated voice_personalization_line for {n} leads.")
