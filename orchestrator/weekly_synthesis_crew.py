"""
weekly_synthesis_crew.py - Atlas M9d-A: Weekly Synthesis

Reads last N memory files + roadmap log entries, calls LLM to synthesize
a weekly retrospective, writes result as a new Notion page in the
Retrospectives database (FORGE_RETROSPECTIVES_DB env var).

Designed to run via VPS cron: Sunday 20:00 Mountain
  0 20 * * 0 root cd /root/agentsHQ && set -a && . .env && set +a && python3 orchestrator/weekly_synthesis_crew.py >> /var/log/weekly_synthesis.log 2>&1

Success criterion: Boubacar reads the page and names 1 insight he would
not have surfaced manually.
"""
from __future__ import annotations

import logging
import os
import re
import sys
from datetime import date, timedelta
from pathlib import Path

ORCH_DIR = Path(__file__).resolve().parent
ROOT_DIR = ORCH_DIR.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

logger = logging.getLogger("agentsHQ.weekly_synthesis")

MEMORY_DIR = Path(os.environ.get(
    "MEMORY_DIR",
    str(Path.home() / ".claude" / "projects" / "d--Ai-Sandbox-agentsHQ" / "memory")
))
ROADMAP_DIR = ROOT_DIR / "docs" / "roadmap"
SYNTHESIS_MODEL = "anthropic/claude-sonnet-4-6"
MEMORY_LIMIT = 30
ROADMAP_DAYS = 7

_EXCLUDED_MEMORY = {"MEMORY.md", "MEMORY.original.md", "MEMORY_ARCHIVE.md"}


# ── readers ───────────────────────────────────────────────────────────────────

def read_memory_files(
    memory_dir: Path = MEMORY_DIR,
    limit: int = MEMORY_LIMIT,
) -> list[tuple[str, str]]:
    """Return list of (filename, content) for recent non-index memory files."""
    files = sorted(
        [f for f in memory_dir.glob("*.md") if f.name not in _EXCLUDED_MEMORY],
        key=lambda f: f.stat().st_mtime,
        reverse=True,
    )[:limit]
    return [(f.name, f.read_text(encoding="utf-8", errors="replace")) for f in files]


def read_roadmap_logs(
    roadmap_dir: Path = ROADMAP_DIR,
    days: int = ROADMAP_DAYS,
) -> str:
    """Extract dated session log entries from all roadmap files within `days`."""
    cutoff_iso = (date.today() - timedelta(days=days)).isoformat()
    sections: list[str] = []
    for roadmap_file in sorted(roadmap_dir.glob("*.md")):
        text = roadmap_file.read_text(encoding="utf-8", errors="replace")
        for match in re.finditer(r"### (\d{4}-\d{2}-\d{2}):(.*?)(?=\n###|\Z)", text, re.DOTALL):
            if match.group(1) >= cutoff_iso:
                sections.append(
                    f"[{roadmap_file.stem}] {match.group(1)}:\n{match.group(2).strip()}"
                )
    return "\n\n".join(sections) if sections else "(no roadmap log entries in last 7 days)"


# ── prompt builder ─────────────────────────────────────────────────────────────

def build_synthesis_prompt(
    memory_snippets: list[tuple[str, str]],
    roadmap_text: str,
    today: str,
) -> str:
    snippets_block = "\n\n".join(
        f"[{name}]\n{content[:600]}" for name, content in memory_snippets
    )
    return f"""You are the agentsHQ weekly synthesis agent. Today is {today}.

Below are the most recently updated memory files (lessons, feedback, project state):

{snippets_block}

Recent roadmap session logs (last 7 days):

{roadmap_text}

Write a structured weekly retrospective with EXACTLY these four sections:

## PROJECT STATUS
2-3 sentences on where each active project stands based on the evidence above.

## OPEN LOOPS
Unresolved items, pending decisions, or threads that appeared but were not closed.

## EMERGING PATTERNS
Themes appearing across multiple memory files or log entries that point to something worth paying attention to.

## SUGGESTED FOCUS
One specific thing to work on next, with a one-sentence reason grounded in the evidence above. Be direct. No hedging.

Write in Boubacar's voice: direct, earned, no filler. Smart Brevity rules apply."""


# ── Postgres writer ────────────────────────────────────────────────────────────

def save_to_postgres(content: str, date_iso: str) -> None:
    """INSERT into weekly_synthesis table. UNIQUE on date — safe to re-run."""
    import psycopg2
    conn = psycopg2.connect(
        host=os.environ.get("POSTGRES_HOST", "agentshq-postgres-1"),
        database=os.environ.get("POSTGRES_DB", "postgres"),
        user=os.environ.get("POSTGRES_USER", "postgres"),
        password=os.environ.get("POSTGRES_PASSWORD", ""),
        port=int(os.environ.get("POSTGRES_PORT", 5432)),
    )
    try:
        cur = conn.cursor()
        cur.execute(
            """
            INSERT INTO weekly_synthesis (date, content)
            VALUES (%s, %s)
            ON CONFLICT (date) DO UPDATE SET content = EXCLUDED.content, created_at = NOW()
            """,
            (date_iso, content),
        )
        conn.commit()
        logger.info(f"weekly_synthesis: saved to Postgres (date={date_iso})")
    finally:
        conn.close()


# ── main ───────────────────────────────────────────────────────────────────────

def run(dry_run: bool = False) -> None:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    today = date.today().isoformat()

    logger.info("weekly_synthesis: reading memory files")
    snippets = read_memory_files()
    logger.info(f"weekly_synthesis: {len(snippets)} memory files read")

    logger.info("weekly_synthesis: reading roadmap logs")
    roadmap_text = read_roadmap_logs()

    logger.info("weekly_synthesis: calling LLM")
    from llm_helpers import call_llm
    prompt = build_synthesis_prompt(snippets, roadmap_text, today)
    response = call_llm(
        messages=[{"role": "user", "content": prompt}],
        model=SYNTHESIS_MODEL,
        max_tokens=1500,
        temperature=0.4,
    )
    synthesis = response.choices[0].message.content.strip()
    logger.info(f"weekly_synthesis: LLM returned {len(synthesis)} chars")

    if dry_run:
        sys.stdout.buffer.write((synthesis + "\n").encode("utf-8", errors="replace"))
        sys.stdout.buffer.flush()
        return

    save_to_postgres(synthesis, today)

    try:
        from notifier import send_message
        chat_id = os.environ.get("TELEGRAM_CHAT_ID", "")
        if chat_id:
            send_message(chat_id, f"Weekly synthesis ready ({today}). Query: SELECT content FROM weekly_synthesis WHERE date = '{today}'")
    except Exception as e:
        logger.debug(f"Telegram notify skipped: {e}")


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry-run", action="store_true", help="Print output, skip Notion write")
    args = parser.parse_args()
    run(dry_run=args.dry_run)
