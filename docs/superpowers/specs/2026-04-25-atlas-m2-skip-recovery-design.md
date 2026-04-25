# Atlas M2: Skip Self-Heal (Same-Day Re-Pick)

**Roadmap:** `docs/roadmap/atlas.md` (codename: atlas)
**Milestone:** M2
**Branch:** `feat/atlas-m2-skip-recovery`
**Save point:** `savepoint-pre-atlas-m2-2026-04-25`
**Date:** 2026-04-25

## Problem

When Boubacar replies `skip` to a publish brief, M1 flips the Notion record's Status to Skipped. The Scheduled Date stays. That slot is now "burned": the date is occupied by a Skipped row that won't publish, and no new pick fills it.

Today's `griot_scheduler` only schedules approvals into the *next open future slot* (tomorrow or later). It does not recognize that a Skipped row's slot is functionally empty and could be backfilled.

Result: a Skip on Tuesday means Wednesday's brief is empty. Cadence breaks silently.

## Goal

`griot_scheduler_tick` (5-minute wake) detects Skipped rows whose Scheduled Date is yesterday or today, treats those slots as empty, and backfills with an approved candidate from the queue. Within 5 minutes of a Skip, a fresh pick takes the slot.

## Non-goals

- Backfilling Skipped slots older than yesterday (the slot is gone; cadence has already moved on)
- Promoting candidates that have not yet been approved by Boubacar (M2 only fills with already-`approved` candidates from `approval_queue`)
- Sending a new approval flow when the candidate pool is empty (just log + Telegram heads-up; griot-morning's empty-backlog signal already covers this)

## Design

### One-line summary

In `griot_scheduler_tick`, before walking forward for the next open slot, scan Notion for Skipped rows in a yesterday-or-today window per platform. For each Skipped row whose date+platform slot is now genuinely empty (no other Queued/Posted post on that exact date+platform), pick the oldest approved unscheduled queue row for that platform and assign it the Skipped row's date.

The Skipped row stays Skipped (it is the audit trail of the skip). The new candidate gets a separate Notion record with Status=Queued + Scheduled Date=that date.

### Data flow

```text
griot_scheduler_tick (every 5 min):
  approvals = _fetch_unscheduled_approvals()  # existing
  notion = open client
  occupied = _fetch_occupancy(notion)         # existing

  # NEW: backfill phase
  skipped_slots = _find_recent_skipped_slots(notion, today, yesterday)
    -> list of (platform, date_iso, source_notion_id) tuples
       where Status=Skipped AND Scheduled Date in {yesterday, today}

  for slot in skipped_slots:
    if (slot.platform, slot.date) is NOT in occupied (genuinely empty):
      candidate = pick oldest approval for slot.platform from approvals list
      if candidate:
        _update_notion_schedule(notion, candidate.notion_id, slot.date)
        occupied[(slot.platform, slot.date)] = True
        _mark_scheduled(queue_id, slot.date)
        _mark_skipped_backfilled(notion, slot.source_notion_id, candidate.notion_id)
        Telegram: "Backfilled <date>: '<title>' (replacing Skipped: '<source title>')"
        approvals.remove(candidate)  # don't reuse for forward scheduling
        backfilled_count += 1

  # Existing: forward-scheduling phase runs on remaining approvals.
  ...
```

The backfill phase runs FIRST. If a Skipped slot is filled, that approval is consumed before the forward-scheduling loop runs, so it's not double-scheduled.

### Backfill rules

1. **Window:** yesterday OR today. Skipped rows whose Scheduled Date is older than yesterday are NOT backfilled (the slot has passed; cadence has moved on).
2. **Slot empty test:** the Skipped row's (platform, date) is "empty" if no other Notion row with Status in {Queued, Ready, Posted} occupies the same (platform, date). Skipped + (Queued or Posted) on the same day = no backfill (slot already taken).
3. **Candidate pick:** oldest `approved` unscheduled candidate from approval_queue **whose payload.platform matches** the Skipped slot's platform. If no candidate matches the platform, skip this slot and log.
4. **Idempotency:** dedupe by Skipped row's `decision_note`. After a successful backfill, the Skipped row's Notion `Status` field stays `Skipped` (never overwrite the audit trail), but we add a `decision_note` entry to the matching `approval_queue.publish_brief` row IF one exists. We do NOT modify the Notion Skipped row itself; instead we track backfill state in the orchestrator's approval_queue layer (see Idempotency section below).
5. **Multi-skip same day same platform:** if two LinkedIn posts both got Skipped on the same date (rare; would require multi-LinkedIn day, which our cadence doesn't currently produce), backfill ONE: the older Skipped row.

### Idempotency

Two layers, mirroring M1's pattern:

1. **Approval-queue consumption.** Once a candidate is picked for backfill, `_mark_scheduled(queue_id, slot_iso)` is called same as forward-scheduling. The candidate's `payload.scheduled_date` is set, so the next tick won't reuse it.
2. **Skipped slot dedup.** On each tick, after `_find_recent_skipped_slots`, filter out any (platform, date) pair that is now occupied by Queued/Posted/Ready (because a previous tick's backfill made it occupied). The "slot empty" test naturally encodes this: if last tick's backfill scheduled a candidate into yesterday's slot, this tick's `_fetch_occupancy` already shows it occupied, and `_find_recent_skipped_slots` rejects it.

So the Skipped row is left untouched in Notion. The audit trail is preserved. The "this slot got backfilled" signal is implicit in the occupancy check.

**Edge case:** if a backfill writes Notion successfully but `_mark_scheduled` fails, the next tick will see the Notion-occupied slot (not empty) AND the approval still unscheduled in approval_queue. The forward-scheduling phase will then reschedule the same candidate to a *different* date. To prevent this, `_mark_scheduled` must run BEFORE the next tick's `_fetch_unscheduled_approvals`. Within a single tick this is guaranteed by sequential code. Across tick boundaries, the worst case is one duplicate scheduling. We accept this; it's a 1-in-1000 race that recovers in one more tick by the human noticing two scheduled posts.

### Files touched

| File | Change |
|---|---|
| `orchestrator/griot_scheduler.py` | Add `_find_recent_skipped_slots(notion, today_iso) -> list[dict]`. Add `_pick_candidate_for_platform(approvals, platform)` returning the matching `(queue_id, payload)` or None. Modify `griot_scheduler_tick` to run backfill phase before forward-scheduling phase. |
| `orchestrator/tests/test_griot_scheduler.py` | Add 5 new tests (see Test plan). Existing tests should pass unchanged because backfill phase is a no-op when there are no Skipped rows. |

No new files. No new tables. No migration. No env vars.

### Backfill algorithm in detail

```python
def _find_recent_skipped_slots(notion, today_iso: str) -> list[dict]:
    """Return list of {platform, date_iso, notion_id, title} for Skipped
    Notion rows whose Scheduled Date is yesterday or today.

    Yesterday is computed in the orchestrator's TIMEZONE (America/Denver).
    """
    yesterday_iso = (date.fromisoformat(today_iso) - timedelta(days=1)).isoformat()
    posts = notion.query_database(CONTENT_DB_ID, filter_obj=None)
    out = []
    for p in posts:
        props = p.get("properties", {})
        if _select(props.get("Status", {})) != "Skipped":
            continue
        sd = _date_start(props.get("Scheduled Date", {}))
        if not sd or sd[:10] not in (yesterday_iso, today_iso):
            continue
        for pf in _multi(props.get("Platform", {})):
            if pf in ("LinkedIn", "X"):
                out.append({
                    "platform": pf,
                    "date_iso": sd[:10],
                    "notion_id": p["id"],
                    "title": _title(props.get("Title", {})),
                })
                break  # one slot per Notion record (matches forward-scheduling pattern)
    # Stable order: by date ascending then platform alphabetically (helpful for tests + logs)
    out.sort(key=lambda s: (s["date_iso"], s["platform"]))
    return out


def _pick_candidate_for_platform(approvals: list, platform: str) -> tuple[int, dict] | None:
    """Return the (queue_id, payload) of the oldest approval matching this
    platform, or None if no candidate matches.
    """
    for queue_id, payload in approvals:
        if payload.get("platform") == platform:
            return (queue_id, payload)
    return None
```

In `griot_scheduler_tick`:

```python
# After approvals + notion + occupied are loaded, BEFORE the forward loop:
tz = pytz.timezone(TIMEZONE)
today_iso = datetime.now(tz).date().isoformat()

skipped_slots = _find_recent_skipped_slots(notion, today_iso)
backfilled_count = 0
for slot in skipped_slots:
    key = (slot["platform"], slot["date_iso"])
    if key in occupied:
        # Slot was already backfilled or otherwise filled. Skip.
        continue
    pick = _pick_candidate_for_platform(approvals, slot["platform"])
    if pick is None:
        logger.info(
            f"griot_scheduler_tick: no candidate available to backfill "
            f"Skipped slot {slot['platform']} {slot['date_iso']}"
        )
        continue
    queue_id, payload = pick
    candidate_notion_id = payload.get("notion_id")
    candidate_title = payload.get("title", "")
    try:
        _update_notion_schedule(notion, candidate_notion_id, slot["date_iso"])
        occupied[key] = True
        _mark_scheduled(queue_id, slot["date_iso"])
        approvals.remove((queue_id, payload))  # consume from forward-scheduling loop
        backfilled_count += 1
        logger.info(
            f"griot_scheduler_tick: backfilled {slot['platform']} {slot['date_iso']} "
            f"with queue #{queue_id} '{candidate_title[:50]}' "
            f"(replacing Skipped '{slot['title'][:50]}')"
        )
        # Telegram notify
        try:
            from notifier import send_message
            chat_id = os.environ.get("OWNER_TELEGRAM_CHAT_ID") or os.environ.get("TELEGRAM_CHAT_ID")
            if chat_id:
                send_message(
                    str(chat_id),
                    f"Backfilled {slot['date_iso']} ({slot['platform']}): "
                    f"'{candidate_title[:60]}' (replacing Skipped: '{slot['title'][:60]}')"
                )
        except Exception as ne:
            logger.warning(f"griot_scheduler_tick: backfill Telegram notify failed: {ne}")
    except Exception as e:
        logger.error(
            f"griot_scheduler_tick: backfill of {slot['platform']} {slot['date_iso']} "
            f"failed: {e}", exc_info=True
        )

if backfilled_count:
    logger.info(f"griot_scheduler_tick: backfilled {backfilled_count} Skipped slot(s)")

# Then existing forward-scheduling loop runs on the remaining approvals.
```

### Test plan

5 unit tests in `tests/test_griot_scheduler.py`:

1. **test_backfill_yesterday_skipped_today_empty.** Yesterday LinkedIn Skipped, today no slots filled, one approved LinkedIn candidate available. After tick: Notion update_page called for the candidate's notion_id with Scheduled Date=yesterday + Status=Queued. Approval row marked scheduled. Telegram fired. Forward-scheduling loop sees zero remaining approvals.

2. **test_no_backfill_if_slot_already_filled.** Yesterday LinkedIn Skipped, but yesterday LinkedIn ALSO has a Queued row (Notion shows two records on same platform-date). Backfill skips this slot. Forward-scheduling proceeds normally.

3. **test_no_backfill_outside_window.** LinkedIn Skipped from 3 days ago, today empty. Backfill phase finds no eligible slots. No-op.

4. **test_backfill_chooses_matching_platform.** Yesterday LinkedIn Skipped, only X candidates in approval queue. Backfill skips this slot (no platform match), logs "no candidate available." Telegram NOT fired.

5. **test_backfill_then_forward_scheduling_independent.** Yesterday X Skipped (one approved X candidate consumed by backfill). Two more approved X candidates remain. Forward-scheduling phase runs on the remaining two and assigns them future slots. Backfilled candidate count = 1, forward-scheduled count = 2.

Plus 1 manual integration check on VPS post-deploy: `/trigger_heartbeat griot-scheduler` (dry-run); confirm the new `_find_recent_skipped_slots` import is reachable.

### Deploy plan

1. Branch `feat/atlas-m2-skip-recovery` off main at `4df7dd1`. ✅ done.
2. Save point tag `savepoint-pre-atlas-m2-2026-04-25`. ✅ done.
3. TDD: write 5 failing tests.
4. Implement the two helpers + tick changes.
5. All tests green. Run full orchestrator suite for regressions.
6. SCP / git pull on VPS, rebuild orc-crewai container.
7. Verify post-deploy: `docker logs orc-crewai | grep griot_scheduler` shows tick firing every 5 min, no errors. Verify import: `python -c "from griot_scheduler import _find_recent_skipped_slots; print('ok')"`.
8. Roadmap update + session log.
9. PR + merge + nsync.

### Rollback

Single commit revert. No DB state. No new env vars.

Save point tag: `savepoint-pre-atlas-m2-2026-04-25`.

### Risks and mitigations

| Risk | Mitigation |
|---|---|
| Backfill double-fires (race between ticks) | Idempotency layer 2: `_fetch_occupancy` shows the slot occupied after first backfill; second tick rejects the slot. Worst case: 1 duplicate within a single 5-min window. Acceptable. |
| `_pick_candidate_for_platform` consumes a candidate that the forward loop would have scheduled differently | Backfill runs first deliberately; the candidate's "lost" forward-slot is just the next open slot, which is what the system would have done anyway. No semantic loss. |
| Skipped row's Scheduled Date in Notion is malformed | `_date_start` returns None → row skipped in `_find_recent_skipped_slots`. Same defensive pattern as `_fetch_occupancy`. |
| Notion query times out | Existing `griot_scheduler_tick` already wraps Notion calls in try/except; backfill phase inherits same protection. |
| The Skipped row stays Skipped forever, cluttering the board | Acceptable; the audit trail is the point. Boubacar can manually move stale Skipped rows to Archived if visual clutter becomes an issue. |
| Multi-platform candidate (e.g., a candidate marked LinkedIn + X) | `payload.platform` for an approval_queue row is set to ONE platform at enqueue (per griot.py logic). If this changes later, `_pick_candidate_for_platform` keeps using single-platform match. Multi-platform candidates would need both to be enqueued separately. |

## Out of scope (for M2)

- Reviving Skipped posts back to Queued (intentional design: Skipped is final)
- Backfilling slots more than 1 day stale (cadence has moved on)
- Notifying Boubacar of long-stale Skipped rows for cleanup (cosmetic; revisit if board pollution becomes real)
- Promoting non-approved candidates (security boundary; only approved content fills slots)

## Cross-references

- Roadmap: `docs/roadmap/atlas.md` § M2
- Phase 3.75 scheduler: `orchestrator/griot_scheduler.py`
- M1 spec (provides the Skipped state this milestone responds to): `docs/superpowers/specs/2026-04-25-atlas-m1-publish-reply-design.md`
- Notion schema reference: memory `reference_notion_content_board_schema.md`
