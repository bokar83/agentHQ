"""
memory_distillation_crew.py - Atlas M9d-B: Memory Distillation Engine

Reads all flat-file memory/*.md files, calls LLM to surface the 5
highest-leverage facts not already obvious from the MEMORY.md index,
writes result to the memory_distillation Postgres table (UNIQUE on date).

Designed to run via VPS cron: 1st of each month at 06:00 Mountain
  0 12 1 * * root cd /root/agentsHQ && docker exec orc-crewai python3 orchestrator/memory_distillation_crew.py >> /var/log/memory_distillation.log 2>&1

Success criterion: digest contains at least 1 fact not already in the
MEMORY.md one-line index.
"""
from __future__ import annotations

import logging
import os
import sys
from datetime import date
from pathlib import Path

ORCH_DIR = Path(__file__).resolve().parent
ROOT_DIR = ORCH_DIR.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

logger = logging.getLogger("agentsHQ.memory_distillation")

MEMORY_DIR = Path(os.environ.get(
    "MEMORY_DIR",
    str(Path.home() / ".claude" / "projects" / "d--Ai-Sandbox-agentsHQ" / "memory")
))
DISTILLATION_MODEL = "anthropic/claude-sonnet-4-6"

_EXCLUDED = {"MEMORY.md", "MEMORY.original.md", "MEMORY_ARCHIVE.md", "MEMORY-DIGEST.md"}


# ── reader ────────────────────────────────────────────────────────────────────

def read_memory_from_db(limit: int = 200) -> list[tuple[str, str]]:
    """Read all memory rows from Postgres for distillation."""
    import psycopg2
    import psycopg2.extras
    conn = psycopg2.connect(
        host=os.environ.get("POSTGRES_HOST", "agentshq-postgres-1"),
        database=os.environ.get("POSTGRES_DB", "postgres"),
        user=os.environ.get("POSTGRES_USER", "postgres"),
        password=os.environ.get("POSTGRES_PASSWORD", ""),
        port=int(os.environ.get("POSTGRES_PORT", 5432)),
    )
    try:
        cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        cur.execute("""
            SELECT category, title, content, pipeline, source
            FROM memory
            ORDER BY relevance_boost DESC, created_at DESC
            LIMIT %s
        """, (limit,))
        rows: list[dict] = [dict(r) for r in cur.fetchall()]
        return [(f"{r['category']}:{r.get('title') or r['source']}", r['content']) for r in rows]
    finally:
        conn.close()


def read_all_memory_files(memory_dir: Path = MEMORY_DIR) -> list[tuple[str, str]]:
    """Return (filename, content) for all non-index, non-digest memory files (flat-file fallback)."""
    files = sorted(
        [f for f in memory_dir.glob("*.md") if f.name not in _EXCLUDED],
        key=lambda f: f.name,
    )
    return [(f.name, f.read_text(encoding="utf-8", errors="replace")) for f in files]


# ── prompt builder ─────────────────────────────────────────────────────────────

def build_distillation_prompt(snippets: list[tuple[str, str]], today: str) -> str:
    block = "\n\n".join(f"[{name}]\n{content[:500]}" for name, content in snippets)
    return f"""You are the agentsHQ memory distillation agent. Today is {today}.

Below are {len(snippets)} memory files from the agentsHQ project (lessons, feedback, project state, references):

{block}

Surface the 5 highest-leverage facts that:
1. Are NOT already summarized as a one-liner in the MEMORY.md index
2. Would save meaningful time or prevent a repeated mistake if recalled at session start
3. Are concrete and actionable — not general principles

Format your output as:

## Memory Digest — {today}

### Fact 1: [short title]
[1-2 sentences. What it is and why it matters right now.]
Source: [filename]

### Fact 2: [short title]
[1-2 sentences.]
Source: [filename]

### Fact 3: [short title]
[1-2 sentences.]
Source: [filename]

### Fact 4: [short title]
[1-2 sentences.]
Source: [filename]

### Fact 5: [short title]
[1-2 sentences.]
Source: [filename]

Be surgical. Cut anything already obvious from reading MEMORY.md or derivable from the code."""


# ── Postgres writer ────────────────────────────────────────────────────────────

def save_to_postgres(content: str, date_iso: str) -> None:
    """INSERT into memory_distillation table. UNIQUE on date — safe to re-run."""
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
            INSERT INTO memory_distillation (date, content)
            VALUES (%s, %s)
            ON CONFLICT (date) DO UPDATE SET content = EXCLUDED.content, created_at = NOW()
            """,
            (date_iso, content),
        )
        conn.commit()
        logger.info(f"memory_distillation: saved to Postgres (date={date_iso})")
    finally:
        conn.close()


# ── main ───────────────────────────────────────────────────────────────────────

def run(dry_run: bool = False) -> None:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    today = date.today().isoformat()

    logger.info("memory_distillation: reading memory from Postgres")
    try:
        snippets = read_memory_from_db(limit=200)
    except Exception as e:
        logger.warning(f"memory_distillation: DB read failed ({e}), falling back to flat files")
        snippets = []
    if not snippets:
        logger.info("memory_distillation: DB returned 0 rows, falling back to flat files")
        snippets = read_all_memory_files()
    logger.info(f"memory_distillation: {len(snippets)} memory items read")

    from llm_helpers import call_llm
    prompt = build_distillation_prompt(snippets, today)
    logger.info("memory_distillation: calling LLM")
    response = call_llm(
        messages=[{"role": "user", "content": prompt}],
        model=DISTILLATION_MODEL,
        max_tokens=1200,
        temperature=0.3,
    )
    digest = response.choices[0].message.content.strip()
    logger.info(f"memory_distillation: LLM returned {len(digest)} chars")

    if dry_run:
        sys.stdout.buffer.write((digest + "\n").encode("utf-8", errors="replace"))
        sys.stdout.buffer.flush()
        return

    save_to_postgres(digest, today)

    try:
        from notifier import send_message
        chat_id = os.environ.get("TELEGRAM_CHAT_ID", "")
        if chat_id:
            send_message(chat_id, f"Memory digest ready ({today}). Query: SELECT content FROM memory_distillation WHERE date = '{today}'")
    except Exception as e:
        logger.debug(f"Telegram notify skipped: {e}")


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry-run", action="store_true", help="Print output, skip Postgres write")
    args = parser.parse_args()
    run(dry_run=args.dry_run)
