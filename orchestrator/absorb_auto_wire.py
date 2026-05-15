"""
absorb_auto_wire.py -- Phase 4 absorb auto-wire crew.

Heartbeat tick (auto_wire_tick) drains absorb_queue rows that meet ALL of:
  - status='done' AND verdict='PROCEED'
  - placement IN ('enhance', 'extend', 'new_tool')
  - dossier.placement_target references one of the 4 opted-in skills
    (ctq-social, client-intake, library, boubacar-prompts)
  - not already wired (no row in hermes_auto_wire_lineage with status
    IN ('pushed', 'pending'))

For each eligible candidate it creates a feature branch, appends a
structured note derived from the dossier to a markdown file inside the
target skill, commits as author Hermes Auto-Wire, and pushes [READY] for
Gate pickup. The boundary script (Compass M7 enforce branch) keys off
the author to constrain writes to the ALLOWED paths only.

Gated on:
  - Sabbath rule (no auto-wires on Sunday America/Denver)
  - Daytime window (06:00-22:00 America/Denver inclusive)
  - 3 auto-wires per day cap via hermes_auto_wire_state

Returns: dict(processed, parked_rate_limit, failed).
"""

from __future__ import annotations

import json
import logging
import os
import re
import subprocess
from datetime import datetime
from typing import Optional

import pytz

logger = logging.getLogger("agentsHQ.absorb_auto_wire")

TIMEZONE = os.environ.get("GENERIC_TIMEZONE", "America/Denver")
DAILY_CAP = int(os.environ.get("AUTO_WIRE_DAILY_CAP", "3"))
ALLOWED_SKILLS = ("ctq-social", "client-intake", "library", "boubacar-prompts")
ALLOWED_PLACEMENTS = ("enhance", "extend", "new_tool")
WORKTREE_ROOT = os.environ.get("AUTO_WIRE_WORKTREE_ROOT", "/tmp")
REPO_ROOT = os.environ.get("AUTO_WIRE_REPO_ROOT", "/app")
AUTHOR_NAME = "Hermes Auto-Wire"
AUTHOR_EMAIL = "hermes@agentshq.local"
TODAY_FMT = "%Y-%m-%d"


def _conn():
    from memory import _pg_conn
    return _pg_conn()


def _now_local() -> datetime:
    return datetime.now(pytz.timezone(TIMEZONE))


def _today_key() -> str:
    return _now_local().strftime(TODAY_FMT)


def _in_window() -> tuple[bool, str]:
    now = _now_local()
    if now.weekday() == 6:
        return False, "sabbath"
    if now.hour < 6 or now.hour >= 22:
        return False, "off-hours"
    return True, "ok"


def _slug(text: str, max_len: int = 30) -> str:
    if not text:
        return "absorb"
    s = re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")[:max_len].rstrip("-")
    return s or "absorb"


def _detect_skill(placement_target: str) -> Optional[str]:
    """Map placement_target to one of the 4 allowed skills, or None."""
    if not placement_target:
        return None
    t = placement_target.lower()
    for skill in ALLOWED_SKILLS:
        if skill in t:
            return skill
    return None


def _resolve_target_path(skill: str) -> str:
    """Append target inside the skill. Always references/auto-wire-notes.md
    so we never touch SKILL.md (the routing trigger spec)."""
    return f"skills/{skill}/references/auto-wire-notes.md"


def _current_count(cur) -> int:
    cur.execute(
        "SELECT count FROM hermes_auto_wire_state WHERE day = %s",
        (_today_key(),),
    )
    row = cur.fetchone()
    return int(row[0]) if row else 0


def _bump_count(cur, branch: str) -> None:
    cur.execute(
        """
        INSERT INTO hermes_auto_wire_state (day, count, last_branch, updated_at)
        VALUES (%s, 1, %s, now())
        ON CONFLICT (day) DO UPDATE
           SET count = hermes_auto_wire_state.count + 1,
               last_branch = EXCLUDED.last_branch,
               updated_at = now()
        """,
        (_today_key(), branch),
    )


def _pop_candidates(cur, max_n: int) -> list:
    """Drain up to max_n eligible absorb_queue rows."""
    cur.execute(
        """
        SELECT id, url, source, dossier
          FROM absorb_queue
         WHERE status = 'done'
           AND verdict = 'PROCEED'
           AND placement = ANY(%s)
           AND id NOT IN (
               SELECT absorb_queue_id FROM hermes_auto_wire_lineage
                WHERE status IN ('pushed', 'pending')
           )
         ORDER BY ts_processed ASC NULLS LAST, id ASC
         FOR UPDATE SKIP LOCKED
         LIMIT %s
        """,
        (list(ALLOWED_PLACEMENTS), max_n * 3),
    )
    out = []
    for r in cur.fetchall():
        dossier = r[3] if isinstance(r[3], dict) else (json.loads(r[3]) if r[3] else {})
        skill = _detect_skill(dossier.get("placement_target") or "")
        if skill is None:
            continue
        out.append({"id": r[0], "url": r[1], "source": r[2], "dossier": dossier, "skill": skill})
        if len(out) >= max_n:
            break
    return out


def _build_content_block(row: dict) -> str:
    d = row["dossier"]
    today = _now_local().strftime(TODAY_FMT)
    summary = (d.get("dossier_summary") or "").strip()
    next_action = (d.get("next_action") or "").strip()
    motion = (d.get("motion") or "").strip()
    leverage = (d.get("leverage") or "").strip()
    why_str = "; ".join(w for w in (d.get("why") or []) if w)
    rationale = (
        f"Leverage: {leverage}. Motion: {motion}. Why this lands here: {why_str}."
        if why_str else f"Leverage: {leverage}. Motion: {motion}."
    )
    return (
        f"\n## From absorb #{row['id']} ({today})\n\n"
        f"Source: {row['url']}\n\n"
        f"{summary}\n\n"
        f"{rationale}\n\n"
        f"Next action: {next_action}\n\n"
        f"See absorb-log row {today} for the full dossier.\n"
    )


def _run(cmd: list, cwd: Optional[str] = None, env: Optional[dict] = None) -> tuple[int, str, str]:
    try:
        p = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True, timeout=120, env=env)
        return p.returncode, p.stdout, p.stderr
    except FileNotFoundError as e:
        return 127, "", f"missing binary: {e}"
    except subprocess.TimeoutExpired as e:
        return 124, "", f"timeout: {e}"


def _record_lineage(cur, aq_id: int, branch: str, target: str,
                    status: str, sha: Optional[str] = None,
                    error: Optional[str] = None) -> int:
    cur.execute(
        """
        INSERT INTO hermes_auto_wire_lineage
            (absorb_queue_id, branch_name, target_path, commit_sha, status, ts_pushed, error)
        VALUES (%s, %s, %s, %s, %s, %s, %s)
        RETURNING id
        """,
        (aq_id, branch, target, sha, status,
         datetime.utcnow() if status == "pushed" else None, error),
    )
    return int(cur.fetchone()[0])


def _mark_aq(cur, aq_id: int, status: str) -> None:
    cur.execute("UPDATE absorb_queue SET status = %s WHERE id = %s", (status, aq_id))


def _wire_one(row: dict) -> tuple[str, Optional[str], Optional[str]]:
    """Branch + commit + push for one candidate.
    Returns (status, commit_sha, error). status in {'pushed','failed','skipped_no_git'}.
    """
    aq_id = row["id"]
    skill = row["skill"]
    today = _now_local().strftime(TODAY_FMT)
    slug = _slug(row["dossier"].get("next_action") or skill)
    branch = f"auto-wire/absorb-{aq_id}-{slug}-{today}"
    worktree_path = f"{WORKTREE_ROOT}/auto-wire-{aq_id}"
    target_rel = _resolve_target_path(skill)

    rc, _, err = _run(["git", "--version"])
    if rc != 0:
        return "skipped_no_git", None, f"git unavailable: {err.strip()}"

    rc, _, err = _run(
        ["git", "worktree", "add", worktree_path, "-b", branch, "origin/main"],
        cwd=REPO_ROOT,
    )
    if rc != 0:
        return "failed", None, f"worktree add: {err.strip()[:400]}"

    try:
        target_abs = f"{worktree_path}/{target_rel}"
        os.makedirs(os.path.dirname(target_abs), exist_ok=True)
        existed = os.path.exists(target_abs)
        with open(target_abs, "a", encoding="utf-8") as f:
            if not existed:
                f.write(
                    f"# Auto-wire notes for {skill}\n\n"
                    "Appended by absorb_auto_wire crew. Each section comes from "
                    "an absorb_queue PROCEED verdict. Boubacar reviews via Gate.\n"
                )
            f.write(_build_content_block(row))

        rc, _, err = _run(["git", "add", target_rel], cwd=worktree_path)
        if rc != 0:
            return "failed", None, f"git add: {err.strip()[:400]}"

        env = os.environ.copy()
        env["GIT_AUTHOR_NAME"] = AUTHOR_NAME
        env["GIT_AUTHOR_EMAIL"] = AUTHOR_EMAIL
        env["GIT_COMMITTER_NAME"] = AUTHOR_NAME
        env["GIT_COMMITTER_EMAIL"] = AUTHOR_EMAIL
        env["SKIP_SESSION_LOG"] = "1"
        commit_msg = (
            f"chore(auto-wire): append absorb #{aq_id} dossier to {target_rel} [READY]\n\n"
            f"Auto-wired from absorb_queue #{aq_id}.\n"
            f"Source: {row['url']}\n"
            f"Skill: {skill}\n"
            f"Placement: {row['dossier'].get('placement')} {row['dossier'].get('placement_target', '')}\n"
            f"Authored by Hermes Auto-Wire under M7 write-boundary scope.\n"
        )
        rc, _, err = _run(["git", "commit", "-m", commit_msg], cwd=worktree_path, env=env)
        if rc != 0:
            return "failed", None, f"git commit: {err.strip()[:400]}"

        rc, sha_out, _ = _run(["git", "rev-parse", "HEAD"], cwd=worktree_path)
        sha = sha_out.strip() if rc == 0 else None

        rc, _, err = _run(["git", "push", "origin", branch], cwd=worktree_path)
        if rc != 0:
            return "failed", sha, f"git push: {err.strip()[:400]}"
        return "pushed", sha, None
    finally:
        _run(["git", "worktree", "remove", worktree_path, "--force"], cwd=REPO_ROOT)


def auto_wire_tick() -> dict:
    """Heartbeat entry. Returns dict(processed, parked_rate_limit, failed)."""
    in_window, why = _in_window()
    if not in_window:
        logger.info(f"auto_wire: skipping tick ({why})")
        return {"processed": 0, "parked_rate_limit": 0, "failed": 0, "skipped": why}

    conn = _conn()
    cur = conn.cursor()
    try:
        used = _current_count(cur)
        remaining = max(0, DAILY_CAP - used)
        processed = parked = failed = 0

        if remaining <= 0:
            cur.execute(
                """
                SELECT id FROM absorb_queue
                 WHERE status = 'done' AND verdict = 'PROCEED'
                   AND placement = ANY(%s)
                   AND id NOT IN (
                       SELECT absorb_queue_id FROM hermes_auto_wire_lineage
                        WHERE status IN ('pushed', 'pending')
                   )
                 ORDER BY ts_processed ASC NULLS LAST, id ASC
                 LIMIT 5
                """,
                (list(ALLOWED_PLACEMENTS),),
            )
            for (aq_id,) in cur.fetchall():
                _mark_aq(cur, aq_id, "parked_rate_limit")
                parked += 1
            conn.commit()
            logger.info(f"auto_wire: daily cap reached ({used}/{DAILY_CAP}); parked={parked}")
            return {"processed": 0, "parked_rate_limit": parked, "failed": 0}

        candidates = _pop_candidates(cur, remaining)
        conn.commit()

        for row in candidates:
            aq_id = row["id"]
            target_rel = _resolve_target_path(row["skill"])
            slug = _slug(row["dossier"].get("next_action") or row["skill"])
            today = _now_local().strftime(TODAY_FMT)
            pending_branch = f"auto-wire/absorb-{aq_id}-{slug}-{today}"
            lin_id = _record_lineage(cur, aq_id, pending_branch, target_rel, "pending")
            conn.commit()

            status, sha, err = _wire_one(row)

            if status == "pushed":
                cur.execute(
                    "UPDATE hermes_auto_wire_lineage SET status='pushed', commit_sha=%s, ts_pushed=now() WHERE id=%s",
                    (sha, lin_id),
                )
                _bump_count(cur, pending_branch)
                conn.commit()
                processed += 1
                logger.info(f"auto_wire: shipped {pending_branch} (sha={sha[:8] if sha else 'unknown'})")
            else:
                cur.execute(
                    "UPDATE hermes_auto_wire_lineage SET status='failed', error=%s WHERE id=%s",
                    (err, lin_id),
                )
                _mark_aq(cur, aq_id, "auto_wire_failed")
                conn.commit()
                failed += 1
                logger.error(f"auto_wire: #{aq_id} failed: {err}")

        return {"processed": processed, "parked_rate_limit": parked, "failed": failed}
    finally:
        try:
            cur.close()
        except Exception:
            pass
