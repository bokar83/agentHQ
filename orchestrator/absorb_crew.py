"""
absorb_crew.py -- Phase 1 absorb agent.

Heartbeat tick (absorb_tick) drains pending rows from absorb_queue, fetches
the artifact content, runs an analyst LLM pass using skills/agentshq-absorb
SKILL.md as the system prompt, and persists a verdict. Tier-based routing:

  - PROCEED on enhance/extend/new_tool ........ silent log + Gate watches branch (Phase 3)
  - PROCEED on new_skill/new_agent/satellite/replace ... approval_queue alert w/ buttons
  - ARCHIVE-AND-NOTE / DONT_PROCEED ........... silent log append, no Telegram

Phase 1 ships verdict generation + log append + approval_queue alert path
for big-surface tier. Coding-subagent spawn (auto-PR for enhance/extend)
lands in Phase 3.
"""

from __future__ import annotations

import json
import logging
import os
import re
from datetime import datetime
from typing import Optional

import httpx

logger = logging.getLogger("agentsHQ.absorb_crew")

ABSORB_LOG_PATH = os.environ.get(
    "ABSORB_LOG_PATH",
    "/app/data/absorb-log.md",
)
ABSORB_FOLLOWUPS_PATH = os.environ.get(
    "ABSORB_FOLLOWUPS_PATH",
    "/app/data/absorb-followups.md",
)
SKILL_PATH = os.environ.get(
    "ABSORB_SKILL_PATH",
    "/app/skills/agentshq-absorb/SKILL.md",
)

ANTHROPIC_MODEL = os.environ.get(
    "ABSORB_MODEL",
    "claude-sonnet-4-6",
)
ANALYST_MAX_TOKENS = 4096
BATCH_LIMIT = 5

BIG_SURFACE_PLACEMENTS = (
    "new_skill", "new_agent", "satellite", "replace_existing",
)


def _conn():
    from memory import _pg_conn
    return _pg_conn()


def _pop_pending(limit: int = BATCH_LIMIT) -> list:
    """Select pending rows and flip them to 'processing' atomically."""
    conn = _conn()
    cur = conn.cursor()
    cur.execute(
        """
        WITH next AS (
            SELECT id FROM absorb_queue
             WHERE status = 'pending'
             ORDER BY ts_received ASC
             FOR UPDATE SKIP LOCKED
             LIMIT %s
        )
        UPDATE absorb_queue q
           SET status = 'processing'
          FROM next
         WHERE q.id = next.id
        RETURNING q.id, q.source, q.url, q.submitted_by
        """,
        (limit,),
    )
    rows = cur.fetchall()
    conn.commit()
    cur.close()
    return [dict(id=r[0], source=r[1], url=r[2], submitted_by=r[3]) for r in rows]


def _fetch_content(url: str) -> tuple[str, str]:
    """Return (artifact_kind, raw_text). Routes by URL pattern.

    X posts -> r.jina.ai reader (canonical per memory rule).
    GitHub repos -> README via raw.githubusercontent.com (best-effort default branch).
    Anything else -> straight GET.
    """
    if "x.com/" in url or "twitter.com/" in url:
        kind = "x-post"
        target = f"https://r.jina.ai/{url}"
    elif "github.com/" in url:
        kind = "github-repo"
        m = re.match(r"https?://github\.com/([^/]+)/([^/?#]+)", url)
        if m:
            owner, repo = m.group(1), m.group(2).removesuffix(".git")
            target = f"https://raw.githubusercontent.com/{owner}/{repo}/HEAD/README.md"
        else:
            target = url
    else:
        kind = "url"
        target = url

    try:
        r = httpx.get(target, timeout=30, follow_redirects=True,
                      headers={"User-Agent": "agentsHQ-absorb/1.0"})
        text = r.text if r.status_code == 200 else f"[fetch failed status={r.status_code}] {r.text[:200]}"
    except Exception as e:
        text = f"[fetch error: {e}]"
    return kind, text[:60_000]


def _load_skill_prompt() -> str:
    try:
        with open(SKILL_PATH, "r", encoding="utf-8") as f:
            return f.read()
    except FileNotFoundError:
        logger.error(f"SKILL.md not found at {SKILL_PATH}; analyst running blind")
        return "(SKILL.md unavailable; apply Phases 0-5 from /agentshq-absorb skill from memory)"


_ANALYST_USER_TEMPLATE = """Run /agentshq-absorb on this artifact.

URL: {url}
Artifact kind: {kind}
Source channel: {source}

Fetched content (truncated to 60K chars):
---
{content}
---

Output ONLY a single JSON object with these keys (no prose, no markdown fence):

{{
  "verdict": "PROCEED" | "ARCHIVE-AND-NOTE" | "DONT_PROCEED",
  "leverage": "producing-motion" | "founder-time-reduction" | "continuous-improvement" | "none",
  "motion": "<one short string naming the motion/skill/target, or 'none'>",
  "placement": "enhance" | "extend" | "new_skill" | "new_tool" | "new_agent" | "satellite" | "replace_existing" | "archive",
  "placement_target": "<skills/X path or repo name, blank if archive>",
  "runner_up": "<one short string, or 'n/a'>",
  "runner_up_reason": "<one line, or 'n/a'>",
  "why": ["<reason 1>", "<reason 2>", "<reason 3>"],
  "next_action": "<one specific concrete next step, or 'n/a'>",
  "target_date": "YYYY-MM-DD or 'n/a'",
  "security_status": "STATIC-CLEAN" | "SUSPICIOUS" | "BLOCKED" | "N/A",
  "security_flags": ["<file:line - pattern>", ...],
  "dossier_summary": "<2-3 sentence dossier>",
  "council_run": true | false,
  "fast_path_reason": "<one line if council_run=false, else blank>"
}}

Follow the SKILL.md phase rules exactly. Coverage-check before council. Fast-path is allowed on small-tier obvious cases per the skill's exceptions."""


def _run_analyst(url: str, kind: str, source: str, content: str) -> dict:
    """Call anthropic. Returns parsed verdict dict. Raises on hard failure."""
    from anthropic import Anthropic

    client = Anthropic()
    system = _load_skill_prompt()
    user = _ANALYST_USER_TEMPLATE.format(
        url=url, kind=kind, source=source, content=content,
    )

    resp = client.messages.create(
        model=ANTHROPIC_MODEL,
        max_tokens=ANALYST_MAX_TOKENS,
        system=system,
        messages=[{"role": "user", "content": user}],
    )
    text = "".join(b.text for b in resp.content if getattr(b, "type", None) == "text")
    text = text.strip()
    if text.startswith("```"):
        text = re.sub(r"^```(?:json)?\s*", "", text)
        text = re.sub(r"\s*```\s*$", "", text)
    try:
        verdict = json.loads(text)
    except json.JSONDecodeError as e:
        raise RuntimeError(f"analyst returned non-JSON: {e}; head={text[:300]}")
    return verdict


def _format_log_line(row: dict, v: dict) -> str:
    today = datetime.utcnow().strftime("%Y-%m-%d")
    why = " ".join(f"({w})" for w in (v.get("why") or [])[:3])
    placement = v.get("placement", "archive")
    target = v.get("placement_target", "")
    place_str = f"{placement} {target}".strip()
    motion = v.get("motion", "none")
    leverage = v.get("leverage", "none")
    src = row.get("source", "?")
    return (
        f"{today} | {row['url']} (via {src}) | {v.get('verdict', '?')} | "
        f"{place_str} | {leverage} ({motion}). {why}\n"
    )


def _append_log(path: str, line: str) -> None:
    try:
        with open(path, "a", encoding="utf-8") as f:
            f.write(line)
    except FileNotFoundError:
        logger.error(f"absorb log not found at {path}; verdict orphaned")
    except Exception as e:
        logger.error(f"absorb log append failed: {e}")


def _append_followup(v: dict) -> None:
    today = datetime.utcnow().strftime("%Y-%m-%d")
    placement = v.get("placement", "")
    target = v.get("placement_target", "")
    place_str = f"{placement} {target}".strip()
    line = (
        f"\n{today} | {place_str} | {v.get('leverage', '')} | "
        f"{v.get('next_action', '')} | {v.get('target_date', 'n/a')}\n"
    )
    _append_log(ABSORB_FOLLOWUPS_PATH, line)


def _alert_big_surface(row: dict, v: dict) -> Optional[int]:
    """Push PROCEED + big-surface verdict to approval_queue for ✅/❌ ack."""
    try:
        import approval_queue
        payload = {
            "title": f"Absorb PROCEED -> {v.get('placement')} {v.get('placement_target', '')}".strip(),
            "platform": "absorb",
            "hook_preview": (v.get("dossier_summary") or "")[:200],
            "text": (
                f"URL: {row['url']}\n"
                f"Source: {row.get('source')}\n"
                f"Leverage: {v.get('leverage')} / motion: {v.get('motion')}\n"
                f"Placement: {v.get('placement')} {v.get('placement_target', '')}\n"
                f"Runner-up: {v.get('runner_up')} -- {v.get('runner_up_reason')}\n"
                f"Why: " + "; ".join(v.get("why") or []) + "\n"
                f"Next action: {v.get('next_action')}\n"
                f"Target date: {v.get('target_date')}\n"
                f"Security: {v.get('security_status')} {','.join(v.get('security_flags') or [])}\n"
                f"Council run: {v.get('council_run')}"
            ),
            "absorb_url": row["url"],
            "absorb_verdict": v,
        }
        q = approval_queue.enqueue(
            crew_name="absorb",
            proposal_type="absorb-big-surface",
            payload=payload,
        )
        return q.id
    except Exception as e:
        logger.error(f"absorb: approval_queue alert failed: {e}", exc_info=True)
        return None


def _persist(row: dict, kind: str, raw: str, v: dict) -> None:
    log_line = _format_log_line(row, v)
    _append_log(ABSORB_LOG_PATH, log_line)
    if v.get("verdict") == "PROCEED":
        _append_followup(v)

    aq_id = None
    if v.get("verdict") == "PROCEED" and v.get("placement") in BIG_SURFACE_PLACEMENTS:
        aq_id = _alert_big_surface(row, v)

    conn = _conn()
    cur = conn.cursor()
    cur.execute(
        """
        UPDATE absorb_queue
           SET status = 'done',
               ts_processed = now(),
               artifact_kind = %s,
               verdict = %s,
               leverage = %s,
               placement = %s,
               dossier = %s::jsonb,
               raw_content = %s,
               approval_queue_id = %s
         WHERE id = %s
        """,
        (
            kind,
            v.get("verdict"),
            v.get("leverage"),
            v.get("placement"),
            json.dumps(v),
            raw[:32_000],
            aq_id,
            row["id"],
        ),
    )
    conn.commit()
    cur.close()


def _mark_failed(row_id: int, err: str) -> None:
    conn = _conn()
    cur = conn.cursor()
    cur.execute(
        """
        UPDATE absorb_queue
           SET status = 'failed', ts_processed = now(), error = %s
         WHERE id = %s
        """,
        (err[:4000], row_id),
    )
    conn.commit()
    cur.close()


def absorb_tick() -> dict:
    """Heartbeat entrypoint. Drains up to BATCH_LIMIT pending rows."""
    rows = _pop_pending()
    processed = 0
    failed = 0
    for row in rows:
        try:
            kind, raw = _fetch_content(row["url"])
            v = _run_analyst(row["url"], kind, row["source"], raw)
            _persist(row, kind, raw, v)
            processed += 1
            logger.info(
                f"absorb: #{row['id']} {v.get('verdict')} {v.get('placement')} -- {row['url']}"
            )
        except Exception as e:
            logger.error(f"absorb: #{row['id']} failed: {e}", exc_info=True)
            try:
                _mark_failed(row["id"], str(e))
            except Exception as e2:
                logger.error(f"absorb: mark_failed also failed for #{row['id']}: {e2}")
            failed += 1
    return {"processed": processed, "failed": failed, "polled": len(rows)}
