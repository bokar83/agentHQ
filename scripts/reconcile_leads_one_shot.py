"""
reconcile_leads_one_shot.py
============================
One-shot parity audit between Notion CRM Leads DB and Supabase `leads` table.

Run inside the `orc-crewai` container (Supabase env vars set there):
    docker exec orc-crewai python /app/scripts/reconcile_leads_one_shot.py

Outputs `docs/audits/notion_sever_parity_<YYYY-MM-DD>.md`.

Match strategy:
  1. Primary: lower(email)
  2. Fallback: (lower(name), lower(company))

Categories:
  - matched
  - notion_only (page exists in Notion, no row in Supabase) -- requires backfill
  - supabase_only (row in Supabase, no Notion page) -- safe (Supabase = SOR)
  - status_drift (matched but Notion.Status != Supabase.status)
"""

from __future__ import annotations

import datetime as _dt
import os
import sys
from collections import defaultdict
from pathlib import Path

import httpx

# Ensure we can import db.py from /app or repo root
for candidate in ("/app", str(Path(__file__).resolve().parent.parent / "orchestrator")):
    if candidate not in sys.path:
        sys.path.insert(0, candidate)

from db import get_crm_connection  # type: ignore

NOTION_DB_ID = os.environ.get("NOTION_CRM_LEADS_DB_ID", "619a842a0e044cb38d1719ec67c130f0")
NOTION_TOKEN = (
    os.environ.get("NOTION_API_KEY")
    or os.environ.get("NOTION_TOKEN")
    or os.environ.get("NOTION_SECRET")
)

REPO_ROOT = Path(__file__).resolve().parent.parent
AUDIT_DIR = REPO_ROOT / "docs" / "audits"


# Notion -> Supabase status mapping (mirror of legacy sync logic)
NOTION_TO_SUPABASE_STATUS = {
    "new": {"new"},
    "contacted": {"messaged", "contacted"},
    "replied": {"replied"},
    "meeting": {"meeting", "booked"},
    "closed": {"closed", "paid"},
    "disqualified": {"disqualified"},
}


def _fetch_notion_pages() -> list[dict]:
    if not NOTION_TOKEN:
        raise RuntimeError("No Notion token in env (NOTION_API_KEY / NOTION_TOKEN / NOTION_SECRET).")

    headers = {
        "Authorization": f"Bearer {NOTION_TOKEN}",
        "Notion-Version": "2022-06-28",
        "Content-Type": "application/json",
    }
    pages: list[dict] = []
    cursor = None
    while True:
        body: dict = {"page_size": 100}
        if cursor:
            body["start_cursor"] = cursor
        resp = httpx.post(
            f"https://api.notion.com/v1/databases/{NOTION_DB_ID}/query",
            headers=headers,
            json=body,
            timeout=30,
        )
        if resp.status_code != 200:
            raise RuntimeError(
                f"Notion query failed: {resp.status_code} {resp.text[:300]}"
            )
        data = resp.json()
        pages.extend(data.get("results", []))
        if not data.get("has_more"):
            break
        cursor = data.get("next_cursor")
    return pages


def _flatten_notion_page(page: dict) -> dict:
    """Pull commonly-used CRM fields out of a Notion page object."""
    props = page.get("properties", {})

    def _title(prop: dict) -> str:
        items = prop.get("title", [])
        return "".join(item.get("plain_text", "") for item in items).strip()

    def _rich_text(prop: dict) -> str:
        items = prop.get("rich_text", [])
        return "".join(item.get("plain_text", "") for item in items).strip()

    def _email(prop: dict) -> str:
        return (prop.get("email") or "").strip().lower()

    def _select(prop: dict) -> str:
        sel = prop.get("select") or {}
        return (sel.get("name") or "").strip()

    return {
        "page_id": page["id"],
        "name": _title(props.get("Name", {})),
        "company": _rich_text(props.get("Company", {})),
        "email": _email(props.get("Email", {})),
        "status": _select(props.get("Status", {})),
        "url": page.get("url", ""),
    }


def _fetch_supabase_leads() -> list[dict]:
    conn = get_crm_connection()
    try:
        cur = conn.cursor()
        cur.execute(
            "SELECT id, name, company, email, status FROM leads ORDER BY id ASC"
        )
        rows = [dict(r) for r in cur.fetchall()]
        cur.close()
        return rows
    finally:
        conn.close()


def _email_key(record: dict) -> str:
    return (record.get("email") or "").strip().lower()


def _name_company_key(record: dict) -> tuple[str, str]:
    return (
        (record.get("name") or "").strip().lower(),
        (record.get("company") or "").strip().lower(),
    )


def _is_status_compatible(notion_status: str, supabase_status: str) -> bool:
    if not notion_status or not supabase_status:
        return False
    accepted = NOTION_TO_SUPABASE_STATUS.get(notion_status.lower(), set())
    return supabase_status.lower() in accepted


def _build_supabase_indexes(rows: list[dict]):
    by_email: dict[str, dict] = {}
    by_name_company: dict[tuple[str, str], list[dict]] = defaultdict(list)
    for r in rows:
        email = _email_key(r)
        if email:
            by_email[email] = r
        nc = _name_company_key(r)
        if nc != ("", ""):
            by_name_company[nc].append(r)
    return by_email, by_name_company


def reconcile() -> dict:
    notion_pages_raw = _fetch_notion_pages()
    notion_records = [_flatten_notion_page(p) for p in notion_pages_raw]
    supabase_rows = _fetch_supabase_leads()

    sb_by_email, sb_by_nc = _build_supabase_indexes(supabase_rows)
    matched_supabase_ids: set = set()

    matched: list[dict] = []
    notion_only: list[dict] = []
    status_drift: list[dict] = []

    for n in notion_records:
        sb = None
        match_kind = None
        email = n["email"]
        if email and email in sb_by_email:
            sb = sb_by_email[email]
            match_kind = "email"
        else:
            nc = _name_company_key(n)
            if nc != ("", "") and sb_by_nc.get(nc):
                sb = sb_by_nc[nc][0]
                match_kind = "name+company"

        if sb is None:
            notion_only.append(n)
            continue

        matched_supabase_ids.add(sb["id"])
        matched.append({"notion": n, "supabase": sb, "match_kind": match_kind})

        if not _is_status_compatible(n["status"], sb.get("status") or ""):
            status_drift.append(
                {
                    "notion_page_id": n["page_id"],
                    "name": n["name"],
                    "email": n["email"],
                    "notion_status": n["status"],
                    "supabase_status": sb.get("status"),
                    "supabase_id": sb["id"],
                }
            )

    supabase_only = [r for r in supabase_rows if r["id"] not in matched_supabase_ids]

    return {
        "totals": {
            "notion": len(notion_records),
            "supabase": len(supabase_rows),
            "matched": len(matched),
            "notion_only": len(notion_only),
            "supabase_only": len(supabase_only),
            "status_drift": len(status_drift),
        },
        "matched": matched,
        "notion_only": notion_only,
        "supabase_only": supabase_only,
        "status_drift": status_drift,
    }


def write_report(result: dict, run_date: _dt.date) -> Path:
    AUDIT_DIR.mkdir(parents=True, exist_ok=True)
    out_path = AUDIT_DIR / f"notion_sever_parity_{run_date.isoformat()}.md"
    t = result["totals"]

    lines: list[str] = []
    lines.append(f"# Notion ↔ Supabase Lead Parity Audit ({run_date.isoformat()})")
    lines.append("")
    lines.append(
        "One-shot reconciliation run after severing Notion CRM Leads sync. "
        "Supabase is the sole system of record going forward."
    )
    lines.append("")
    lines.append("## Totals")
    lines.append("")
    lines.append(f"- Notion CRM pages: **{t['notion']}**")
    lines.append(f"- Supabase leads:   **{t['supabase']}**")
    lines.append(f"- Matched:          **{t['matched']}**")
    lines.append(f"- Notion-only orphans (need backfill into Supabase): **{t['notion_only']}**")
    lines.append(f"- Supabase-only (expected post-sever, OK):           **{t['supabase_only']}**")
    lines.append(f"- Status drift (Notion vs Supabase mismatch):        **{t['status_drift']}**")
    lines.append("")

    lines.append("## Notion-only orphans")
    lines.append("")
    if not result["notion_only"]:
        lines.append("_None._")
    else:
        lines.append("| Name | Company | Email | Notion Status | Page |")
        lines.append("|---|---|---|---|---|")
        for n in result["notion_only"]:
            lines.append(
                f"| {n['name']} | {n['company']} | {n['email']} | {n['status']} | "
                f"[{n['page_id'][:8]}]({n['url']}) |"
            )
    lines.append("")

    lines.append("## Status drift")
    lines.append("")
    if not result["status_drift"]:
        lines.append("_None._")
    else:
        lines.append("| Name | Email | Notion Status | Supabase Status | Supabase ID |")
        lines.append("|---|---|---|---|---|")
        for d in result["status_drift"]:
            lines.append(
                f"| {d['name']} | {d['email']} | {d['notion_status']} | "
                f"{d['supabase_status']} | {d['supabase_id']} |"
            )
    lines.append("")

    lines.append("## Supabase-only leads")
    lines.append("")
    lines.append(
        f"_{t['supabase_only']} rows in Supabase have no Notion counterpart. "
        "Expected: leads added after Notion sync was bypassed. No action needed._"
    )
    lines.append("")

    out_path.write_text("\n".join(lines), encoding="utf-8")
    return out_path


def main() -> int:
    run_date = _dt.date.today()
    print(f"[reconcile] running for {run_date.isoformat()}")
    result = reconcile()
    out = write_report(result, run_date)
    t = result["totals"]
    print(f"[reconcile] notion={t['notion']} supabase={t['supabase']} "
          f"matched={t['matched']} notion_only={t['notion_only']} "
          f"supabase_only={t['supabase_only']} drift={t['status_drift']}")
    print(f"[reconcile] report written: {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
