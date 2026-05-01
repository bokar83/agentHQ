"""
skills/linkedin_mvm/apollo_pull.py
==================================
One-shot script: pulls 50 AI-Governance-ICP prospects from Apollo and writes
them straight into workspace/linkedin-mvm/target_list.csv (appending to
existing rows, deduping by linkedin_url).

ICP per Playbook V3 sec 1.8 + LinkedIn MVM:
  - Job titles: Owner, Founder, CEO, President, Managing Partner, Managing
    Director, Principal, COO, CFO, Director of Operations, VP Operations
  - Industries: Accounting, Legal Services, Management Consulting, Financial
    Services, Insurance, Architecture & Planning, Civil Engineering, Staffing
    & Recruiting, Human Resources, Marketing & Advertising, IT Services
  - Geography: Salt Lake City, Provo, Ogden, Lehi, Sandy, Park City, then
    Mountain West (Boise, Denver, Phoenix)
  - Company size: 11-200 employees

Apollo /mixed_people/api_search costs ZERO credits. Email reveal costs 1
credit per lead - we do NOT reveal here, LinkedIn DM does not need emails.

Run from agentsHQ root:
  python -m skills.linkedin_mvm.apollo_pull

Or with custom params:
  python -m skills.linkedin_mvm.apollo_pull --max 50 --pages 5
"""
from __future__ import annotations

import argparse
import csv
import logging
import os
import sys
from pathlib import Path

import httpx

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")

APOLLO_API_URL = "https://api.apollo.io/v1"
# Strip whitespace + \r - Windows-edited .env files often carry CRLF.
APOLLO_KEY = (os.environ.get("APOLLO_API_KEY") or "").strip()

CSV_PATH = ROOT / "workspace" / "linkedin-mvm" / "target_list.csv"

# AI Governance ICP filters
PERSON_TITLES = [
    "Owner", "Founder", "Co-Founder", "CEO", "Chief Executive Officer",
    "President", "Managing Partner", "Managing Director", "Principal",
    "Chief Operating Officer", "COO", "Chief Financial Officer", "CFO",
    "Director of Operations", "VP Operations", "Vice President Operations",
]

PERSON_LOCATIONS_TIER_1 = [
    "Salt Lake City, Utah", "Provo, Utah", "Orem, Utah", "Lehi, Utah",
    "Ogden, Utah", "Sandy, Utah", "Park City, Utah", "St. George, Utah",
    "Draper, Utah", "South Jordan, Utah", "Logan, Utah", "Murray, Utah",
]

PERSON_LOCATIONS_TIER_2 = [
    "Boise, Idaho", "Meridian, Idaho", "Denver, Colorado", "Boulder, Colorado",
    "Colorado Springs, Colorado", "Phoenix, Arizona", "Scottsdale, Arizona",
    "Tucson, Arizona", "Las Vegas, Nevada", "Reno, Nevada",
]

# Apollo "Value too long" caps queries hard. Run multiple short searches in
# sequence, one industry-keyword per search, and dedupe via linkedin_url.
INDUSTRY_KEYWORD_PASSES = [
    "accounting",
    "law firm",
    "consulting",
    "insurance",
    "architecture",
    "engineering",
    "financial services",
    "wealth management",
    "staffing",
    "marketing agency",
    "IT services",
]

EMPLOYEE_RANGE = ["11,200"]  # 11-200 employees

CSV_FIELDS = ["name", "company", "title", "location", "linkedin_url", "industry", "hook"]


def search_apollo(keyword: str, page: int, per_page: int, tier: int) -> list[dict]:
    """One Apollo page for a single industry keyword. Returns raw person records."""
    if not APOLLO_KEY:
        raise RuntimeError("APOLLO_API_KEY not set in environment.")

    locations = PERSON_LOCATIONS_TIER_1 if tier == 1 else PERSON_LOCATIONS_TIER_1 + PERSON_LOCATIONS_TIER_2

    payload = {
        "q_keywords": keyword,
        "person_titles": PERSON_TITLES,
        "person_locations": locations,
        "organization_num_employees_ranges": EMPLOYEE_RANGE,
        "page": page,
        "per_page": per_page,
    }
    headers = {
        "Content-Type": "application/json",
        "X-Api-Key": APOLLO_KEY,
        "Cache-Control": "no-cache",
    }
    with httpx.Client(timeout=30) as client:
        r = client.post(f"{APOLLO_API_URL}/mixed_people/api_search", json=payload, headers=headers)
    if r.status_code != 200:
        logger.error(f"Apollo {r.status_code} on '{keyword}' p{page}: {r.text[:200]}")
        return []
    return r.json().get("people", [])


def to_row(person: dict) -> dict:
    org = person.get("organization") or {}
    loc = org.get("primary_location") or {}
    industry = org.get("industry") or ""
    location_str = ", ".join(filter(None, [loc.get("city"), loc.get("state")])) or person.get("city", "")
    return {
        "name": person.get("name", "").strip(),
        "company": (org.get("name") or "").strip(),
        "title": (person.get("title") or "").strip(),
        "location": location_str.strip(),
        "linkedin_url": (person.get("linkedin_url") or "").strip(),
        "industry": industry.strip(),
        "hook": "",  # MUST be filled in manually after running -- see SKILL.md
    }


def load_existing_urls(csv_path: Path) -> set[str]:
    """Return set of linkedin_urls already in the CSV, for dedupe."""
    if not csv_path.exists():
        return set()
    urls: set[str] = set()
    with csv_path.open(newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            u = (row.get("linkedin_url") or "").strip()
            if u:
                urls.add(u)
    return urls


def append_rows(csv_path: Path, rows: list[dict]) -> int:
    """Append rows to CSV; create with header if missing. Returns count written."""
    csv_path.parent.mkdir(parents=True, exist_ok=True)
    existed = csv_path.exists() and csv_path.stat().st_size > 0
    with csv_path.open("a", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=CSV_FIELDS)
        if not existed:
            w.writeheader()
        for r in rows:
            w.writerow(r)
    return len(rows)


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--max", type=int, default=50, help="Max new rows to append")
    p.add_argument("--pages", type=int, default=4, help="Apollo pages to scan (25 ppp)")
    p.add_argument("--per-page", type=int, default=25, help="Records per Apollo page (max 25)")
    p.add_argument("--tier", type=int, default=1, choices=[1, 2], help="1=Utah, 2=Utah+Mountain West")
    args = p.parse_args()

    if not APOLLO_KEY:
        print("ERROR: APOLLO_API_KEY missing from env. Run with the agentsHQ venv or source .env.")
        return 2

    seen = load_existing_urls(CSV_PATH)
    logger.info(f"Existing rows in target_list.csv: {len(seen)}")

    new_rows: list[dict] = []
    # Loop industries first, then pages, until we hit args.max
    for keyword in INDUSTRY_KEYWORD_PASSES:
        if len(new_rows) >= args.max:
            break
        for page in range(1, args.pages + 1):
            if len(new_rows) >= args.max:
                break
            logger.info(f"Apollo: kw='{keyword}' page={page}/{args.pages} tier={args.tier}")
            people = search_apollo(keyword=keyword, page=page, per_page=args.per_page, tier=args.tier)
            if not people:
                logger.info(f"  '{keyword}' p{page}: no more results")
                break
            added_this_page = 0
            for person in people:
                row = to_row(person)
                if not row["linkedin_url"] or row["linkedin_url"] in seen:
                    continue
                if not row["name"]:
                    continue
                seen.add(row["linkedin_url"])
                new_rows.append(row)
                added_this_page += 1
                if len(new_rows) >= args.max:
                    break
            logger.info(f"  '{keyword}' p{page}: raw={len(people)} new={added_this_page} total={len(new_rows)}")

    written = append_rows(CSV_PATH, new_rows)
    print(f"\nDone. Appended {written} new rows to {CSV_PATH}")
    print(f"Total unique linkedin_urls now: {len(seen)}")
    print("\nNEXT: open the CSV and fill in the `hook` column for each row (60-90 sec/row).")
    print("      Without hooks the DM falls back to a generic line which performs poorly.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
