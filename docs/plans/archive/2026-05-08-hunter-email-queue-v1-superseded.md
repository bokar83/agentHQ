# Plan: Hunter Fix + Email Queue Rework + Reply Scanner

**Date:** 2026-05-08
**Branch:** `feature/email-queue-and-hunter-fix`
**Author:** Claude (planning) → Codex (implementation)
**Gates:** /sankofa + /karpathy required before Codex handoff

## Context

Two issues bundled into one plan because they touch the same outreach surface:

1. **Hunter / harvest stall** (per `docs/handoff/2026-05-07-enrichment-rebuild-and-thesis-launch.md`): `topup_cw_leads` early-exits when DB has ≥ minimum undrafted CW leads. Today: 41 existing → CW skipped → harvest stalled at 31/50.

2. **Email queue is single global cap, not per-touch.** Today only 50 drafts total were prepared (mix of T1 + T2). Boubacar's mental model: T1 capped at 50 fresh leads/day, T2-T5 auto-fire to every due lead. Currently sequence_engine.py:523-526 burns one shared `daily_limit` across all touches.

Plus: Reply scanner — before drafting T2-T5, scan `boubacar@catalystworks.consulting` inbox for replies. If lead has replied, mark `replied=true` and skip from auto-fire.

## Goals (success criteria)

- **G1.** Hunter manual harvest run hits 50/50 (SW=35, CW=15) end-to-end without stalling.
- **G2.** Daily email drafting prepares: T1 = up to 50 fresh leads (split SW/CW per existing pipeline), T2-T5 = up to 150 leads/touch/pipeline soft cap, oldest-overdue first, REPLIED LEADS EXCLUDED.
- **G3.** Reply scanner runs in container before drafting; queries Gmail for inbound from each lead.email; marks `replied=true` on match (excluding OOO/auto-replies).
- **G4.** Telegram morning digest reports per-touch breakdown: `T1: X / T2: Y / T3: Z / T4: A / T5: B = TOTAL drafts (SW=N, CW=M)`.
- **G5.** Cron at 06:00 MT calls `harvest_until_target` (replacing legacy `_run_daily_harvest`), verified by 1-2 days of stable manual runs first.

## Out of scope

- Site-wide first-name scrub (separate session, separate prompt provided).
- LinkedIn post 1 publish (manual, already done morning of 5/8).
- New paid vendors (Findymail/Anymailfinder/MillionVerifier deferred per handoff).
- Studio pipeline changes.

## Decisions locked

- **Per-touch caps:** T1 = 50 hard cap (split SW=35, CW=15 via existing harvest sub-targets). T2-T5 = 150/touch/pipeline soft cap (Q3 recommendation accepted by Boubacar).
- **Priority within cap:** ORDER BY `last_contacted_at ASC` (oldest-overdue first) — already present in sequence_engine.py:157.
- **Reply scanner backend:** `gws` CLI in container (option b). Runs autonomously, no Claude session dependency.
- **Reply detection:** inbound message + non-bounce + non-OOO/auto-reply (option b). Adds OOO regex filter.
- **Order:** Hunter fix FIRST (~10 lines, low risk). Email queue rework SECOND (bigger surface).
- **Spam math:** SW SEND cap 35/day + CW SEND cap 15/day = ~50/day from `catalystworks.ai@gmail.com`. Drafts can balloon up to ~650/day worst case (50+150*4) but SENDS stay bounded by send_scheduler.py.
- **Touch cadence:** Existing TOUCH_DAYS_SW = {1:0, 2:3, 3:7, 4:12, 5:17}. TOUCH_DAYS_CW = {1:0, 2:6, 3:9, 4:14, 5:19}. Unchanged.

---

## Phase 1 — Hunter / harvest fix

### Files

- `signal_works/topup_cw_leads.py:85-99` — add `force_fresh` param, skip early-exit when True.
- `signal_works/harvest_until_target.py:175` — pass `force_fresh=True`.
- `orchestrator/scheduler.py` — replace `_run_daily_harvest` chain with `harvest_until_target.harvest_until_target()` call (DEFERRED until 1-2 days manual runs prove 50/50 reliable).

### Patch

**`signal_works/topup_cw_leads.py`:**

```python
def topup_cw_leads(minimum: int = DAILY_MINIMUM, dry_run: bool = False, force_fresh: bool = False) -> int:
    """Hybrid CW lead topup: 5 fresh from Apollo (widened ICP) + 5 resends.

    Args:
        minimum: target leads to ensure ready in DB.
        dry_run: walk pipeline without saving.
        force_fresh: skip the ready>=minimum short-circuit. Used by
            harvest_until_target when we want guaranteed daily injection
            even if undrafted residue exists.
    """
    conn = get_crm_connection()
    try:
        ensure_leads_columns(conn)
    except Exception as e:
        logger.warning(f"topup_cw_leads: ensure_leads_columns failed: {e}")
    ready = _count_ready_cw_leads(conn)
    logger.info(f"CW topup: {ready} ready leads (target: {minimum}, force_fresh={force_fresh})")
    if ready >= minimum and not force_fresh:
        return ready
    # ... rest unchanged
```

**`signal_works/harvest_until_target.py:175`:**

```python
saved = topup_cw_leads(minimum=needed, dry_run=dry_run, force_fresh=True)
```

### Manual harvest re-run

```bash
ssh root@72.60.209.109 "docker exec orc-crewai bash -c 'cd /app && python -m signal_works.harvest_until_target --target 50 --sw-target 35 --cw-target 15'"
```

Expected: Telegram fires `✅ Daily harvest complete: 50/50 leads with email (SW=35, CW=15). Passes: N.`

### Cron wire (deferred 1-2 days)

After 2 successive days of 50/50, edit `orchestrator/scheduler.py` to replace the old `_run_daily_harvest` Apollo+enrichment chain with:

```python
from signal_works.harvest_until_target import harvest_until_target as run_daily_harvest
# in the scheduled job:
run_daily_harvest()
```

---

## Phase 2 — Email queue rework (per-touch caps)

### Files

- `skills/outreach/sequence_engine.py:500-580` — `run_sequence` rewrite with per-touch caps.
- `signal_works/morning_runner.py:195` — update `_gap` math + Telegram digest.
- `orchestrator/engine.py:95` — bump or remove hardcoded `daily_limit=10`.

### New constants

```python
# skills/outreach/sequence_engine.py
T1_DAILY_CAP = 50            # hard cap, controls fresh-lead drafting volume
T2_T5_SOFT_CAP_PER_TOUCH = 150  # soft cap per touch per pipeline
```

### `run_sequence` signature change

Old:
```python
def run_sequence(pipeline: str, dry_run: bool = False, daily_limit: int = 10) -> dict:
```

New:
```python
def run_sequence(
    pipeline: str,
    dry_run: bool = False,
    t1_cap: int = T1_DAILY_CAP,
    followup_cap: int = T2_T5_SOFT_CAP_PER_TOUCH,
) -> dict:
```

### `run_sequence` loop rewrite

Replace lines 522-526 (the shared-budget loop) with per-touch cap logic:

```python
max_touch = 5 if pipeline in ("cw", "sw") else 4
total_sent = 0
total_failed = 0
per_touch_counts = {}  # touch -> count drafted

for touch in range(1, max_touch + 1):
    cap = t1_cap if touch == 1 else followup_cap
    leads = _get_due_leads(conn, pipeline, touch, limit=cap)
    if not leads:
        per_touch_counts[touch] = 0
        logger.info(f"[{pipeline.upper()}] T{touch}: no leads due")
        continue

    logger.info(f"[{pipeline.upper()}] T{touch}: {len(leads)} leads due (cap={cap})")
    subject_tpl, body_tpl = _load_template(pipeline, touch)

    drafted = 0
    for lead in leads:
        # ... existing draft logic (lines 534-560) ...
        if result_id:
            _mark_sent(conn, lead["id"], touch, pipeline, subject)
            drafted += 1
            total_sent += 1
        else:
            total_failed += 1
    per_touch_counts[touch] = drafted

return {
    "pipeline": pipeline,
    "total_sent": total_sent,
    "total_failed": total_failed,
    "per_touch": per_touch_counts,
    "results": results,
}
```

### `_get_due_leads` change

T1 cap split: SW pipeline takes T1 from `apollo_signal_works%`-style sources, CW takes from `apollo_catalyst_works%`. Existing source filter handles this. **No change to `_get_due_leads` SQL needed** — pipeline arg already routes correctly.

T1 split per pipeline: SW pipeline call → t1_cap=35, CW pipeline call → t1_cap=15. Caller passes the right cap. Update in `morning_runner.py`:

```python
sw_result = run_sequence("sw", t1_cap=35, followup_cap=150)
cw_result = run_sequence("cw", t1_cap=15, followup_cap=150)
```

This removes the old `_gap = 50 - sw_drafted - cw_drafted` math at line 195. Replace with combined Telegram digest.

### Telegram digest format

```
📧 Outreach drafting complete (2026-05-08)

SW: T1=35 / T2=N / T3=N / T4=N / T5=N = TOTAL drafts
CW: T1=15 / T2=N / T3=N / T4=N / T5=N = TOTAL drafts

Replies skipped (already responded): R leads
Bounces/bad emails skipped: B leads

Total drafts in inbox: G
```

### `engine.py:95` cleanup

```python
# before: result = run_sequence(pipeline, dry_run=False, daily_limit=10)
# after: result = run_sequence(pipeline, dry_run=False)  # use defaults
```

---

## Phase 3 — Reply scanner

### Files

- `skills/outreach/reply_scanner.py` — NEW
- `skills/outreach/sequence_engine.py` — call reply scanner before T2-T5 draft loop
- DB: `leads.replied_at TIMESTAMP NULL`, `leads.replied=BOOLEAN DEFAULT FALSE` columns added via `_ensure_sequence_columns`

### Reply scanner spec

```python
# skills/outreach/reply_scanner.py
"""
Scan boubacar@catalystworks.consulting inbox for replies from leads.
Mark leads.replied=true + leads.replied_at=<message date> when match found.
Excludes:
  - OOO / auto-replies (subject/body regex)
  - Bounce notifications (mailer-daemon, postmaster, bounces@)
  - Already-marked leads (idempotent)

Runs via gws CLI in container:
  gws gmail messages list --query "from:<lead_email> newer_than:30d" --json

Returns:
  {"scanned": N, "matched": M, "skipped_ooo": K}
"""

import subprocess
import json
import re
from datetime import datetime, timezone

OOO_PATTERNS = [
    r"out of (the )?office",
    r"on (vacation|holiday|leave|annual leave|maternity|paternity)",
    r"automatic(ally)? (reply|response)",
    r"away from (the )?office",
    r"i('m| am) (currently )?out",
    r"will (be|return) back",
    r"limited (access|email)",
]
OOO_REGEX = re.compile("|".join(OOO_PATTERNS), re.IGNORECASE)

BOUNCE_SENDERS = {
    "mailer-daemon", "postmaster", "bounces@", "noreply@", "no-reply@",
}


def is_ooo_or_auto(subject: str, snippet: str) -> bool:
    text = f"{subject} {snippet}"
    return bool(OOO_REGEX.search(text))


def is_bounce_sender(from_addr: str) -> bool:
    low = from_addr.lower()
    return any(s in low for s in BOUNCE_SENDERS)


def scan_replies_for_pipeline(pipeline: str, days_back: int = 30) -> dict:
    """Scan Gmail for replies from leads in this pipeline. Mark matches.

    Uses gws CLI in container. Pulls leads where sequence_touch >= 1 AND
    replied IS NOT TRUE AND last_contacted_at >= now - days_back.
    """
    from orchestrator.db import get_crm_connection
    conn = get_crm_connection()
    cur = conn.cursor()
    cur.execute("""
        SELECT id, email, last_contacted_at FROM leads
        WHERE sequence_pipeline = %s
          AND sequence_touch >= 1
          AND (replied IS NULL OR replied = FALSE)
          AND last_contacted_at >= NOW() - INTERVAL '%s days'
    """, (pipeline, days_back))
    leads = cur.fetchall()

    scanned = 0
    matched = 0
    skipped_ooo = 0

    for lead in leads:
        email = lead["email"]
        if not email:
            continue
        scanned += 1
        # Query Gmail via gws (account = boubacar@catalystworks.consulting)
        result = subprocess.run(
            ["gws", "gmail", "messages", "list",
             "--account", "boubacar@catalystworks.consulting",
             "--query", f"from:{email} newer_than:{days_back}d",
             "--json"],
            capture_output=True, text=True, timeout=30,
        )
        if result.returncode != 0:
            continue
        try:
            messages = json.loads(result.stdout).get("messages", [])
        except json.JSONDecodeError:
            continue
        if not messages:
            continue

        # Inspect first match: pull message, check OOO/bounce filters
        msg_id = messages[0]["id"]
        detail = subprocess.run(
            ["gws", "gmail", "messages", "get", msg_id,
             "--account", "boubacar@catalystworks.consulting", "--json"],
            capture_output=True, text=True, timeout=30,
        )
        if detail.returncode != 0:
            continue
        try:
            msg = json.loads(detail.stdout)
        except json.JSONDecodeError:
            continue

        subject = msg.get("subject", "")
        snippet = msg.get("snippet", "")
        from_addr = msg.get("from", "")

        if is_bounce_sender(from_addr):
            continue
        if is_ooo_or_auto(subject, snippet):
            skipped_ooo += 1
            continue

        # Genuine reply. Mark.
        replied_at = msg.get("date") or datetime.now(timezone.utc).isoformat()
        cur.execute("""
            UPDATE leads
            SET replied = TRUE, replied_at = %s, updated_at = NOW()
            WHERE id = %s
        """, (replied_at, lead["id"]))
        matched += 1

    conn.commit()
    cur.close()
    conn.close()
    return {"scanned": scanned, "matched": matched, "skipped_ooo": skipped_ooo}
```

### Schema migration

Add to `_ensure_sequence_columns` in sequence_engine.py:

```python
for col, definition in [
    ("sequence_touch", "INTEGER DEFAULT 0"),
    ("sequence_pipeline", "TEXT"),
    ("opt_out", "BOOLEAN DEFAULT FALSE"),
    ("replied", "BOOLEAN DEFAULT FALSE"),         # NEW
    ("replied_at", "TIMESTAMP WITH TIME ZONE"),   # NEW
]:
    cur.execute(f"ALTER TABLE leads ADD COLUMN IF NOT EXISTS {col} {definition}")
```

### `_get_due_leads` filter update

Both T1 and T2-T5 queries already filter by `(opt_out IS NULL OR opt_out = FALSE)`. Add reply filter:

```sql
AND (replied IS NULL OR replied = FALSE)
```

Append to WHERE clause in both branches at sequence_engine.py:138-145 and 151-159.

### Wire-in

In `morning_runner.py`, before calling `run_sequence`:

```python
from skills.outreach.reply_scanner import scan_replies_for_pipeline

sw_replies = scan_replies_for_pipeline("sw")
cw_replies = scan_replies_for_pipeline("cw")
logger.info(f"Reply scan: SW {sw_replies}, CW {cw_replies}")

sw_result = run_sequence("sw", t1_cap=35, followup_cap=150)
cw_result = run_sequence("cw", t1_cap=15, followup_cap=150)
```

Telegram digest includes `Replies skipped: {sw_replies['matched'] + cw_replies['matched']}`.

---

## Test plan

### Unit-ish

1. `test_topup_cw_force_fresh.py` — call with `force_fresh=True` when ready=100, assert harvest_leads invoked.
2. `test_run_sequence_per_touch_caps.py` — mock `_get_due_leads`, assert T1 capped at 50, T2-T5 each capped at 150.
3. `test_reply_scanner_ooo.py` — feed OOO subject/snippet, assert `is_ooo_or_auto` True; assert lead NOT marked replied.
4. `test_reply_scanner_genuine.py` — feed genuine reply, assert lead marked replied=true.

### Integration (container, manual)

5. After deploy, run dry-run:
   ```bash
   ssh root@72.60.209.109 "docker exec orc-crewai bash -c 'cd /app && python -m skills.outreach.sequence_engine --pipeline sw --dry-run'"
   ```
   Confirm log shows per-touch counts under caps.

6. Run reply scanner solo:
   ```bash
   ssh root@72.60.209.109 "docker exec orc-crewai bash -c 'cd /app && python -c \"from skills.outreach.reply_scanner import scan_replies_for_pipeline; print(scan_replies_for_pipeline(\\\"sw\\\"))\"'"
   ```

7. Re-run harvest manually, confirm 50/50 + Telegram alert.

### Acceptance

- Day 1 after deploy: morning digest shows `T1=N / T2=M ...` per pipeline. M > 0 if any leads have aged past T2 day-gap.
- Day 2: `replied` column populated for any leads who replied in last 30 days.
- Day 7: drafted count grows day-over-day (T2 leads from day 1 hit T2-due on day 4 etc).

## Rollback

- Revert via `git revert <commit>` on `feature/email-queue-and-hunter-fix`.
- DB columns `replied`, `replied_at` are additive — safe to leave even on rollback.
- `topup_cw_leads.force_fresh` default False — existing callers unaffected.

## Risks

| Risk | Likelihood | Mitigation |
|---|---|---|
| Gmail rate-limit on reply scanner (1 req/lead) | Medium | gws CLI batches via `messages list`. Cap days_back=30. ~200 leads/day max scan = under quota. |
| OOO regex too aggressive, marks real replies as OOO | Low | Only SKIPS OOO from being marked replied. Lead stays in queue. Worst case: drafted T2 to someone on vacation — same as today. |
| force_fresh causes Apollo credit burn | Low | Apollo cap already enforced upstream. force_fresh just skips DB short-circuit. |
| Per-touch caps balloon drafts to 650+/day | Low | SENDS still bounded by send_scheduler.py (35 SW + 15 CW = 50/day). Drafts age in inbox. |
| Cron switch to harvest_until_target breaks scheduler | Medium | DEFERRED until 1-2 days manual runs prove stable. |

## Sankofa + Karpathy

This plan is to be reviewed by /sankofa (5 voices stress-test) and /karpathy (4 principles audit) before Codex implements. Update this file with WARN/PASS notes after each gate.

## Codex handoff brief

Once gates pass:
- Branch: `feature/email-queue-and-hunter-fix`
- Phase 1 first (small, ship), test, then Phase 2 + 3 together (interrelated changes to sequence_engine.py).
- File mounts: code is volume-mounted (no rebuild). After local edits, `git pull` on VPS = live.
- BAKED FILE WARNING: `sequence_engine.py` may be in baked image precedence list — check `feedback_baked_image_import_precedence.md`. If yes, `docker cp` after edit too.
- Tests: write the 4 above. Run pre-commit. [READY] commit + push when green.
