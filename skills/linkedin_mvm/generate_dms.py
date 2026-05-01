"""
skills/linkedin_mvm/generate_dms.py
====================================
Reads workspace/linkedin-mvm/target_list.csv and:
  1) Adds each prospect to the lead DB (Supabase + Notion auto-sync via local_crm).
  2) Generates a personalized DM per prospect using templates/linkedin/dm_v1.py.
  3) Writes one Markdown file with all DMs, copy-paste ready.

Run from agentsHQ root:
  python -m skills.linkedin_mvm.generate_dms

CSV columns expected:
  name, company, title, location, linkedin_url, industry, hook

The `hook` column is the per-prospect personalization line (1-2 sentences).
"""
from __future__ import annotations

import csv
import logging
import os
import sys
from datetime import datetime
from pathlib import Path

# Path setup so the script runs from agentsHQ root or via -m.
ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from templates.linkedin.dm_v1 import render_dm, render_connection_note, DEFAULT_CALENDLY_URL  # noqa: E402

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")

CSV_PATH = ROOT / "workspace" / "linkedin-mvm" / "target_list.csv"
OUT_DIR = ROOT / "workspace" / "linkedin-mvm"

CSV_FIELDS_FULL = [
    "name", "company", "title", "location", "linkedin_url",
    "industry", "hook", "connection_note", "dm_text", "lead_db_id", "status",
]


def _first_name(full_name: str) -> str:
    return (full_name or "").strip().split(" ")[0] or "there"


def _ingest_to_crm_via_orchestrator(row: dict) -> int:
    """Add the lead via the orchestrator HTTP API (which runs inside the
    container with full DB access). Returns lead_id or 0 on failure.

    Calls POST /run with task_type that maps to a CRM ingest workflow. If
    the orchestrator is not reachable, falls back silently.
    """
    api_key = (os.environ.get("ORCHESTRATOR_API_KEY") or "").strip()
    api_url = os.environ.get("ORCHESTRATOR_URL", "http://127.0.0.1:8000").strip()
    if not api_key:
        return 0

    payload = {
        "name": row.get("name", "").strip(),
        "company": row.get("company", "").strip() or "Unknown",
        "title": row.get("title", "").strip(),
        "location": row.get("location", "").strip(),
        "linkedin_url": row.get("linkedin_url", "").strip(),
        "industry": row.get("industry", "").strip() or "Other",
        "source": "LinkedIn",
        "notes": row.get("hook", "").strip(),
    }
    try:
        import httpx
        r = httpx.post(
            f"{api_url}/leads/add",
            headers={"X-API-Key": api_key, "Content-Type": "application/json"},
            json=payload,
            timeout=15,
        )
        if r.status_code in (200, 201):
            return int(r.json().get("lead_id", 0))
        # Endpoint may not exist; fall back silently
        logger.debug(f"orchestrator /leads/add not available ({r.status_code}); using direct CRM")
    except Exception as exc:
        logger.debug(f"orchestrator HTTP ingest failed: {exc}")
    return 0


def _ingest_to_crm(row: dict) -> int:
    """Add the lead to Supabase + Notion CRM. Returns lead_id or 0 on failure.

    Two paths tried in order:
      1. orchestrator HTTP API (works from outside the container).
      2. direct local_crm import (works only inside the container).
    """
    # Path 1: orchestrator API (preferred when running on VPS or locally)
    lead_id = _ingest_to_crm_via_orchestrator(row)
    if lead_id:
        return lead_id

    # Path 2: direct import (works only inside the orc-crewai container)
    try:
        from skills.local_crm.crm_tool import add_lead
    except Exception as exc:  # noqa: BLE001
        logger.debug(f"local_crm direct import failed: {exc}")
        return 0

    payload = {
        "name": row.get("name", "").strip(),
        "company": row.get("company", "").strip() or "Unknown",
        "title": row.get("title", "").strip(),
        "location": row.get("location", "").strip(),
        "linkedin_url": row.get("linkedin_url", "").strip(),
        "industry": row.get("industry", "").strip() or "Other",
        "source": "LinkedIn",
        "notes": row.get("hook", "").strip(),
    }
    try:
        return add_lead(payload)
    except Exception as exc:  # noqa: BLE001
        logger.warning(f"add_lead failed for {payload['name']}: {exc}")
        return 0


def main(csv_path: Path = CSV_PATH, calendly_url: str = DEFAULT_CALENDLY_URL, skip_crm: bool = False) -> Path:
    if not csv_path.exists():
        raise FileNotFoundError(
            f"Target list not found at {csv_path}.\n"
            "Create the CSV with columns: name, company, title, location, "
            "linkedin_url, industry, hook"
        )

    today = datetime.now().strftime("%Y-%m-%d")
    out_path = OUT_DIR / f"dms_to_send_{today}.md"
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    rows = []
    with csv_path.open(newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            rows.append({k: (v or "").strip() for k, v in row.items()})

    logger.info(f"Loaded {len(rows)} prospects from {csv_path}")

    sections: list[str] = [
        f"# LinkedIn DMs to send - {today}",
        "",
        f"**Generated:** {datetime.now().isoformat(timespec='seconds')}",
        f"**Source:** {csv_path}",
        f"**Total:** {len(rows)} DMs",
        "",
        "## How to use",
        "",
        "1. Open each LinkedIn URL.",
        "2. If you are connected -> send the DM directly. If not -> send a connection request, paste the DM as the note (LinkedIn caps notes at 300 chars; the DM body fits with the hook trimmed if needed).",
        "3. The DM is also stored in the `dm_text` column of `target_list.csv` for in-CSV reference.",
        "4. After sending, mark the row as `messaged` in the `status` column (or set status via the lead DB).",
        "",
        "---",
        "",
    ]

    ingested = 0
    skipped = 0
    # Augment rows in-place with connection_note + dm_text + lead_db_id + status,
    # then rewrite CSV.
    for i, row in enumerate(rows, start=1):
        name = row.get("name", "").strip()
        if not name:
            skipped += 1
            row["connection_note"] = ""
            row["dm_text"] = ""
            row["lead_db_id"] = ""
            row["status"] = "skipped_no_name"
            continue
        hook = row.get("hook", "").strip() or "Saw your work and wanted to connect."
        first = _first_name(name)
        connection_note = render_connection_note(first, hook)
        dm = render_dm(first, hook, calendly_url=calendly_url)

        if skip_crm:
            # Re-use existing lead_db_id if present; do not re-ingest
            try:
                lead_id = int(row.get("lead_db_id", "") or 0)
            except (TypeError, ValueError):
                lead_id = 0
        else:
            lead_id = _ingest_to_crm(row)
        if lead_id:
            ingested += 1

        # Annotate the row for CSV write-back
        row["connection_note"] = connection_note
        row["dm_text"] = dm
        row["lead_db_id"] = str(lead_id) if lead_id else ""
        if not row.get("status"):
            row["status"] = "new"

        sections.append(f"### {i}. {name} - {row.get('title', '')} @ {row.get('company', '')}")
        sections.append("")
        sections.append(f"**LinkedIn:** {row.get('linkedin_url', '(missing)')}")
        sections.append(f"**Lead DB ID:** {lead_id or 'NOT_INGESTED'}")
        sections.append(f"**Industry:** {row.get('industry', '')}")
        sections.append(f"**Hook used:** {hook}")
        sections.append("")
        sections.append(f"**Step 1 - Connection request note ({len(connection_note)} chars):**")
        sections.append("")
        sections.append("```")
        sections.append(connection_note)
        sections.append("```")
        sections.append("")
        sections.append("**Step 2 - Full DM after they accept:**")
        sections.append("")
        sections.append("```")
        sections.append(dm)
        sections.append("```")
        sections.append("")
        sections.append("---")
        sections.append("")

    sections.append(f"\n_Ingested {ingested} of {len(rows)} into the lead DB. Skipped: {skipped}._\n")
    out_path.write_text("\n".join(sections), encoding="utf-8")

    # Rewrite the CSV with the dm_text + lead_db_id + status columns added.
    with csv_path.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=CSV_FIELDS_FULL, extrasaction="ignore")
        w.writeheader()
        for row in rows:
            w.writerow({k: row.get(k, "") for k in CSV_FIELDS_FULL})

    logger.info(f"Wrote {out_path} ({ingested} ingested, {skipped} skipped, {len(rows)} total)")
    logger.info(f"Updated CSV with connection_note + dm_text columns: {csv_path}")
    print(f"\nDone. Open: {out_path}")
    print(f"      CSV with DMs: {csv_path}\n")
    return out_path


if __name__ == "__main__":
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("--skip-crm", action="store_true",
                    help="Re-use existing lead_db_id from CSV; do not re-ingest")
    args = ap.parse_args()
    main(skip_crm=args.skip_crm)
