"""
skills/linkedin_mvm/serper_pull.py
==================================
Pulls LinkedIn profiles for the AI Governance ICP via Serper (Google search,
site:linkedin.com/in/). Each result is a real LinkedIn URL with the page's
title parsed for name + title + company.

Why Serper instead of Apollo: Apollo's free /mixed_people/api_search returns
obfuscated rows ("Co***o") with no linkedin_url - the actual data is gated
behind credits. Serper's Google search returns real public LinkedIn URLs at
~$0.001/query. Far cheaper for our volume.

Run from agentsHQ root (locally or on VPS):
  python -m skills.linkedin_mvm.serper_pull --max 50
"""
from __future__ import annotations

import argparse
import csv
import json
import logging
import os
import re
import sys
import time
from pathlib import Path

import httpx

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")

SERPER_KEY = (os.environ.get("SERPER_API_KEY") or "").strip()
SERPER_URL = "https://google.serper.dev/search"

CSV_PATH = ROOT / "workspace" / "linkedin-mvm" / "target_list.csv"
STATE_PATH = ROOT / "workspace" / "linkedin-mvm" / ".serper_pull_state.json"
CSV_FIELDS = ["name", "company", "title", "location", "linkedin_url", "industry", "hook"]

# Each search query targets a specific (industry, role, region) slice.
# Serper returns up to 100 organic results per query; we take 10 each by
# default. site:linkedin.com/in/ ensures we only get profile pages.
#
# Strategy for 500-lead funnel:
#   ~75 queries x ~10 results = ~750 raw, ~500 unique after dedupe.
#   Run as 5-7 queries/day x 10 days. Stays under any rate limit.
#
# Geographic columns: Utah (cities), Mountain West states, "remote-headquartered"
# variants, mid-market trigger phrases.
SEARCH_QUERIES = [
    # === UTAH PRIMARY (29 queries) ===
    ('site:linkedin.com/in/ ("Managing Partner" OR "Owner" OR "Founder" OR "CEO") (CPA OR accounting) Utah', "Accounting"),
    ('site:linkedin.com/in/ ("Partner" OR "Director") accounting "Salt Lake"', "Accounting"),
    ('site:linkedin.com/in/ ("Owner" OR "Founder") "tax firm" Utah', "Accounting"),
    ('site:linkedin.com/in/ ("Managing Partner" OR "Owner" OR "Founder") (law OR attorney) Utah', "Legal Services"),
    ('site:linkedin.com/in/ ("Founding Partner" OR "Senior Partner") "law firm" Utah', "Legal Services"),
    ('site:linkedin.com/in/ ("General Counsel" OR "Chief Legal Officer") Utah', "Legal Services"),
    ('site:linkedin.com/in/ ("Managing Partner" OR "Founder" OR "Principal") consulting Utah', "Management Consulting"),
    ('site:linkedin.com/in/ ("Founder" OR "CEO") "consulting firm" Utah', "Management Consulting"),
    ('site:linkedin.com/in/ ("Principal Consultant" OR "Senior Partner") strategy Utah', "Management Consulting"),
    ('site:linkedin.com/in/ ("CFO" OR "Chief Financial Officer" OR "President") "financial services" Utah', "Financial Services"),
    ('site:linkedin.com/in/ ("Founder" OR "CEO") "wealth management" Utah', "Financial Services"),
    ('site:linkedin.com/in/ ("Managing Director" OR "Partner") "investment" Utah', "Financial Services"),
    ('site:linkedin.com/in/ ("Owner" OR "Founder" OR "President") insurance Utah', "Insurance"),
    ('site:linkedin.com/in/ ("Agency Owner" OR "Principal Agent") insurance Utah', "Insurance"),
    ('site:linkedin.com/in/ ("Founder" OR "Managing Director") "insurance brokerage" Utah', "Insurance"),
    ('site:linkedin.com/in/ ("Principal" OR "Owner" OR "Founder") (architecture OR architect) Utah', "Architecture & Planning"),
    ('site:linkedin.com/in/ ("Founding Principal" OR "Managing Principal") architecture Utah', "Architecture & Planning"),
    ('site:linkedin.com/in/ ("Principal" OR "Owner" OR "Founder") engineering Utah', "Civil Engineering"),
    ('site:linkedin.com/in/ ("CEO" OR "President") "engineering firm" Utah', "Civil Engineering"),
    ('site:linkedin.com/in/ ("Owner" OR "Founder" OR "CEO") staffing Utah', "Staffing & Recruiting"),
    ('site:linkedin.com/in/ ("Founder" OR "President") recruiting Utah', "Staffing & Recruiting"),
    ('site:linkedin.com/in/ ("Owner" OR "Founder" OR "CEO") "marketing agency" Utah', "Marketing & Advertising"),
    ('site:linkedin.com/in/ ("Managing Director" OR "Founder") "creative agency" Utah', "Marketing & Advertising"),
    ('site:linkedin.com/in/ ("CEO" OR "Founder") "digital agency" Utah', "Marketing & Advertising"),
    ('site:linkedin.com/in/ ("Founder" OR "President") "PR firm" Utah', "Marketing & Advertising"),
    ('site:linkedin.com/in/ ("COO" OR "Chief Operating Officer" OR "VP Operations") Utah', "Operations leaders"),
    ('site:linkedin.com/in/ ("Director of Operations" OR "Head of Operations") Utah', "Operations leaders"),
    ('site:linkedin.com/in/ ("Owner" OR "Founder") "HR consulting" Utah', "Human Resources Services"),
    ('site:linkedin.com/in/ ("Founder" OR "CEO") "IT services" Utah', "IT Services & IT Consulting"),

    # === IDAHO + BOISE METRO (8 queries) ===
    ('site:linkedin.com/in/ ("Managing Partner" OR "Founder") accounting (Idaho OR Boise)', "Accounting"),
    ('site:linkedin.com/in/ ("Owner" OR "Founder") "law firm" (Idaho OR Boise)', "Legal Services"),
    ('site:linkedin.com/in/ ("Founder" OR "Principal") consulting (Idaho OR Boise)', "Management Consulting"),
    ('site:linkedin.com/in/ ("CFO" OR "President") "financial services" (Idaho OR Boise)', "Financial Services"),
    ('site:linkedin.com/in/ ("Owner" OR "Founder") insurance (Idaho OR Boise)', "Insurance"),
    ('site:linkedin.com/in/ ("Principal" OR "Founder") architecture (Idaho OR Boise)', "Architecture & Planning"),
    ('site:linkedin.com/in/ ("CEO" OR "Founder") "marketing agency" (Idaho OR Boise)', "Marketing & Advertising"),
    ('site:linkedin.com/in/ ("COO" OR "Director of Operations") (Idaho OR Boise)', "Operations leaders"),

    # === COLORADO + DENVER METRO (10 queries) ===
    ('site:linkedin.com/in/ ("Managing Partner" OR "Founder") accounting (Colorado OR Denver)', "Accounting"),
    ('site:linkedin.com/in/ ("Founder" OR "Owner") "law firm" (Colorado OR Denver OR Boulder)', "Legal Services"),
    ('site:linkedin.com/in/ ("Founder" OR "Principal") consulting (Colorado OR Denver)', "Management Consulting"),
    ('site:linkedin.com/in/ ("Founder" OR "CEO") "wealth management" (Colorado OR Denver)', "Financial Services"),
    ('site:linkedin.com/in/ ("CFO" OR "Chief Financial Officer") (Colorado OR Denver) "professional services"', "Financial Services"),
    ('site:linkedin.com/in/ ("Owner" OR "Founder") insurance (Colorado OR Denver)', "Insurance"),
    ('site:linkedin.com/in/ ("Principal" OR "Founding Principal") architecture (Colorado OR Denver)', "Architecture & Planning"),
    ('site:linkedin.com/in/ ("Owner" OR "CEO") "staffing firm" (Colorado OR Denver)', "Staffing & Recruiting"),
    ('site:linkedin.com/in/ ("Founder" OR "Managing Director") "marketing agency" (Colorado OR Denver)', "Marketing & Advertising"),
    ('site:linkedin.com/in/ ("COO" OR "Director of Operations") (Colorado OR Denver)', "Operations leaders"),

    # === ARIZONA + PHOENIX METRO (8 queries) ===
    ('site:linkedin.com/in/ ("Managing Partner" OR "Founder") accounting (Arizona OR Phoenix OR Scottsdale)', "Accounting"),
    ('site:linkedin.com/in/ ("Owner" OR "Founder") "law firm" (Arizona OR Phoenix)', "Legal Services"),
    ('site:linkedin.com/in/ ("Founder" OR "Principal") consulting (Arizona OR Phoenix)', "Management Consulting"),
    ('site:linkedin.com/in/ ("Founder" OR "CEO") "financial services" (Arizona OR Phoenix)', "Financial Services"),
    ('site:linkedin.com/in/ ("Owner" OR "Founder") insurance (Arizona OR Phoenix)', "Insurance"),
    ('site:linkedin.com/in/ ("Principal" OR "Founder") architecture (Arizona OR Phoenix OR Scottsdale)', "Architecture & Planning"),
    ('site:linkedin.com/in/ ("Owner" OR "Founder") "marketing agency" (Arizona OR Phoenix OR Scottsdale)', "Marketing & Advertising"),
    ('site:linkedin.com/in/ ("COO" OR "Director of Operations") (Arizona OR Phoenix OR Scottsdale) "professional services"', "Operations leaders"),

    # === NEVADA + LAS VEGAS / RENO (4 queries) ===
    ('site:linkedin.com/in/ ("Managing Partner" OR "Founder") accounting (Nevada OR "Las Vegas" OR Reno)', "Accounting"),
    ('site:linkedin.com/in/ ("Owner" OR "Founder") "law firm" (Nevada OR "Las Vegas")', "Legal Services"),
    ('site:linkedin.com/in/ ("Founder" OR "Principal") consulting (Nevada OR "Las Vegas")', "Management Consulting"),
    ('site:linkedin.com/in/ ("Owner" OR "Founder" OR "CEO") "marketing agency" (Nevada OR "Las Vegas")', "Marketing & Advertising"),

    # === TRIGGER-EVENT QUERIES (high-intent leads, 8 queries) ===
    ('site:linkedin.com/in/ ("AI policy" OR "AI governance") (CEO OR Founder OR Partner) Utah', "AI-mention trigger"),
    ('site:linkedin.com/in/ "AI governance" CEO (Colorado OR Arizona OR Idaho)', "AI-mention trigger"),
    ('site:linkedin.com/in/ "AI strategy" "professional services" (Utah OR Colorado)', "AI-mention trigger"),
    ('site:linkedin.com/in/ ("ChatGPT" OR "Claude") accounting partner Utah', "AI-mention trigger"),
    ('site:linkedin.com/in/ "AI policy" "law firm" Utah', "AI-mention trigger"),
    ('site:linkedin.com/in/ "data privacy" CEO Utah', "AI-mention trigger"),
    ('site:linkedin.com/in/ "compliance officer" "professional services" (Utah OR Colorado)', "AI-mention trigger"),
    ('site:linkedin.com/in/ "vCISO" OR "fractional CISO" (Utah OR Colorado OR Arizona OR Idaho)', "AI-mention trigger"),

    # === EXPANSION TIER (broader Mountain West, 8 queries) ===
    ('site:linkedin.com/in/ "Managing Partner" "professional services" "Mountain West"', "Mixed pro services"),
    ('site:linkedin.com/in/ ("Owner" OR "Founder") "Salt Lake City" "professional services"', "Mixed pro services"),
    ('site:linkedin.com/in/ ("CEO" OR "President") "Park City"', "Mixed pro services"),
    ('site:linkedin.com/in/ ("CEO" OR "Founder") "St. George" Utah', "Mixed pro services"),
    ('site:linkedin.com/in/ ("Founder" OR "President") "Provo" OR "Lehi" "professional services"', "Mixed pro services"),
    ('site:linkedin.com/in/ ("Founder" OR "Owner") consulting "Wyoming"', "Management Consulting"),
    ('site:linkedin.com/in/ ("Founder" OR "Managing Director") "boutique firm" Utah', "Mixed pro services"),
    ('site:linkedin.com/in/ ("Founder" OR "President") "advisory firm" (Utah OR Colorado)', "Management Consulting"),
]


def parse_linkedin_title(title: str) -> tuple[str, str, str]:
    """LinkedIn search-result title is usually:
      'Firstname Lastname - Title - Company | LinkedIn'
    or
      'Firstname Lastname - Title at Company | LinkedIn'
    Returns (name, title, company). Robust to missing parts.
    """
    if not title:
        return ("", "", "")
    # Strip the trailing "| LinkedIn" or similar.
    t = re.sub(r"\s*[\|·-]\s*LinkedIn.*$", "", title, flags=re.IGNORECASE).strip()
    # Try " - " split first.
    parts = [p.strip() for p in t.split(" - ")]
    if len(parts) >= 3:
        return (parts[0], parts[1], parts[2])
    if len(parts) == 2:
        # Could be "Name - Title at Company"
        m = re.match(r"^(.*?)\s+at\s+(.+)$", parts[1], flags=re.IGNORECASE)
        if m:
            return (parts[0], m.group(1).strip(), m.group(2).strip())
        return (parts[0], parts[1], "")
    return (t, "", "")


def serper_search(query: str, num: int = 10) -> list[dict]:
    if not SERPER_KEY:
        raise RuntimeError("SERPER_API_KEY not set in environment.")
    headers = {"X-API-KEY": SERPER_KEY, "Content-Type": "application/json"}
    payload = {"q": query, "num": num}
    with httpx.Client(timeout=30) as c:
        r = c.post(SERPER_URL, json=payload, headers=headers)
    if r.status_code != 200:
        logger.error(f"Serper {r.status_code}: {r.text[:300]}")
        return []
    return r.json().get("organic", [])


def normalize_url(url: str) -> str:
    """Strip query/fragment, ensure trailing slash off, lowercase host."""
    if not url:
        return ""
    url = url.split("?")[0].split("#")[0].rstrip("/")
    return url


def to_row(result: dict, industry_label: str) -> dict | None:
    url = normalize_url(result.get("link", ""))
    if not url or "/in/" not in url:
        return None
    name, title, company = parse_linkedin_title(result.get("title", ""))
    snippet = result.get("snippet", "") or ""
    # Try to extract location from snippet (often appears as ", State")
    location = ""
    m = re.search(r"\b(Utah|Idaho|Colorado|Arizona|Nevada|Wyoming|Montana|New Mexico|United States)\b", snippet)
    if m:
        location = m.group(1)
    return {
        "name": name,
        "company": company,
        "title": title,
        "location": location,
        "linkedin_url": url,
        "industry": industry_label,
        "hook": "",  # auto-filled in a later enrichment pass
    }


def load_existing_urls(csv_path: Path) -> set[str]:
    if not csv_path.exists():
        return set()
    urls: set[str] = set()
    with csv_path.open(newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            u = normalize_url(row.get("linkedin_url") or "")
            if u:
                urls.add(u)
    return urls


def append_rows(csv_path: Path, rows: list[dict]) -> int:
    csv_path.parent.mkdir(parents=True, exist_ok=True)
    existed = csv_path.exists() and csv_path.stat().st_size > 0
    with csv_path.open("a", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=CSV_FIELDS)
        if not existed:
            w.writeheader()
        for r in rows:
            w.writerow(r)
    return len(rows)


def load_state() -> dict:
    """State file tracks which query indices have already been run, so daily
    cron picks up where the last run stopped."""
    if STATE_PATH.exists():
        try:
            return json.loads(STATE_PATH.read_text())
        except Exception:
            pass
    return {"next_query_index": 0, "runs": []}


def save_state(state: dict) -> None:
    STATE_PATH.parent.mkdir(parents=True, exist_ok=True)
    STATE_PATH.write_text(json.dumps(state, indent=2))


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--max", type=int, default=75, help="Max new rows to append per run")
    p.add_argument("--per-query", type=int, default=10, help="Results per Serper query (max 100)")
    p.add_argument("--max-queries", type=int, default=10, help="Max queries to run this invocation (rate-limit cushion)")
    p.add_argument("--reset-state", action="store_true", help="Reset query index to 0 before running")
    args = p.parse_args()

    if not SERPER_KEY:
        print("ERROR: SERPER_API_KEY missing. Run with VPS env or sourced local .env.")
        return 2

    state = load_state()
    if args.reset_state:
        state = {"next_query_index": 0, "runs": []}

    start_idx = state.get("next_query_index", 0) % len(SEARCH_QUERIES)
    seen = load_existing_urls(CSV_PATH)
    logger.info(f"Existing rows in target_list.csv: {len(seen)}")
    logger.info(f"Starting at query index {start_idx}, will run up to {args.max_queries} queries")

    new_rows: list[dict] = []
    queries_run = 0
    last_idx = start_idx
    for offset in range(args.max_queries):
        if len(new_rows) >= args.max:
            break
        idx = (start_idx + offset) % len(SEARCH_QUERIES)
        query, industry_label = SEARCH_QUERIES[idx]
        last_idx = idx
        logger.info(f"Serper [{idx}]: {query[:80]}...")
        results = serper_search(query, num=args.per_query)
        added = 0
        for res in results:
            row = to_row(res, industry_label)
            if not row:
                continue
            if row["linkedin_url"] in seen:
                continue
            if not row["name"]:
                continue
            seen.add(row["linkedin_url"])
            new_rows.append(row)
            added += 1
            if len(new_rows) >= args.max:
                break
        logger.info(f"  -> {len(results)} raw, {added} new, total={len(new_rows)}")
        queries_run += 1
        # Small jitter between queries so we don't hammer Serper / Google.
        time.sleep(2.0)

    written = append_rows(CSV_PATH, new_rows)
    state["next_query_index"] = (last_idx + 1) % len(SEARCH_QUERIES)
    state["runs"].append({
        "ts": time.strftime("%Y-%m-%dT%H:%M:%S"),
        "queries_run": queries_run,
        "rows_added": written,
        "total_unique": len(seen),
    })
    state["runs"] = state["runs"][-20:]
    save_state(state)

    print(f"\nDone. Appended {written} new rows. Queries run: {queries_run}.")
    print(f"Total unique linkedin_urls: {len(seen)} / target 500")
    print(f"Next run will start at query index {state['next_query_index']}.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
