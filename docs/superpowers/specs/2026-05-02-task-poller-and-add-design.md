# Notion State Poller + /task add Design

**Spec date:** 2026-05-02
**Author:** Boubacar Barry + Claude Code
**Status:** approved for implementation
**Codename:** task-poller

---

## 1. Goal

Make Notion-side task edits propagate to a permanent agentsHQ event log without operator behavior change. Plus one fast-capture Telegram verb for phone-side new-task creation.

> Boubacar clicks Status, P0, Sprint, etc. in Notion the way he always does. Within 5 minutes, agentsHQ has logged what changed. The log unlocks past-due alerts, daily standups, and bi-weekly Golden Gem reviews as future read-only consumers.

This replaces the original `/task done`, `/task p0`, `/task sprint` (etc.) command-surface design that Sankofa Council rejected. Reason: a Telegram command surface forces operator discipline that fails in practice; a passive poller catches Notion clicks without requiring it.

---

## 2. Architecture

```
        Boubacar clicks in Notion (mobile, web, anywhere)
                              |
                              v
                    Notion Tasks DB (truth)
                              |
                              | every 5 min (heartbeat tick)
                              v
        orchestrator/notion_state_poller.py (NEW)
          - query rows changed in last 6 min
          - diff vs notion_state_cache.json
          - emit changelog entries
                              |
              +---------------+---------------+
              v                               v
       data/notion_state_cache.json    docs/audits/changelog.md
       (state mirror, gitignored)      (event log, committed)


        Boubacar from phone:  /task add "Reply to Adam"
                              |
                              v
                  thepopebot-event-handler (existing)
                              |
                              v
        orc-crewai handlers_commands.py
          - handle_task_add()
          - assigns next T-26xxxx
          - writes to Notion
          - poller catches new row next tick
```

**Two components:**

1. `orchestrator/notion_state_poller.py` (NEW). Heartbeat-driven. Every 5 minutes, queries Notion Tasks DB for rows updated in the last 6 minutes, diffs each row against the cached state, and writes one changelog line per detected change. Updates cache atomically. No Telegram. No operator discipline.

2. `/task add "<title>" [--owner=X] [--sprint=Y] [--p0]`. Single Telegram verb in `orchestrator/handlers_commands.py`. Assigns next T-26xxxx, creates a Notion row, echoes back the new ID + top 3 Boubacar tasks. Poller catches the new row next tick.

Webhooks not used. Notion's webhook API is paid-tier-only and historically flaky; polling is simpler and 5-min latency is acceptable.

---

## 3. Poller behavior

### 3.1 Trigger

Heartbeat tick. Register a wake `notion-state-poller` with `every=5m` in `orchestrator/scheduler.py`. Same pattern as `auto_publisher` and `griot_scheduler_tick`.

### 3.2 Per-tick sequence

1. Acquire coordination lock via `skills.coordination.claim('task:notion-state-poller')`. If held, log and skip the tick.
2. Query Notion for rows where `last_edited_time >= now - 6min`. Paginate if >100 rows.
3. Load `data/notion_state_cache.json`. If missing, treat as empty and trigger backfill mode (3.6).
4. For each row, compare tracked properties against cache. Emit one changelog line per differing property.
5. Atomic cache write: write `data/notion_state_cache.json.tmp`, fsync, rename. Release lock.

Total wall-clock per tick: ≤10 seconds under normal load.

### 3.3 Tracked properties

| Property | Reason tracked |
|---|---|
| Status | Done / In Progress / Not Started transitions are the most-asked events |
| P0 | Single-row dictator; flips matter |
| Sprint | Multi-select; sprint moves are the planning signal |
| Owner | Reassignments need an audit trail |
| Due Date | Past-due automation needs date changes |
| Blocked By | Dependency edits show what unblocked or got newly gated |
| Task (title) | Renames are rare but should be logged |
| Notes | Golden Gem prefix flips matter |
| Outcome | Set when something ships; captures the "what shipped" event |

NOT tracked: Source, Completion Criteria, Category, Priority, Task ID. Rarely change after creation. Adding tracked props later is non-breaking.

### 3.4 Diff equality rules

- Strings (Task, Notes, Outcome): byte-exact. Whitespace counts.
- Selects (Status): name equality. Null vs name counts.
- Multi-selects (Sprint, Owner): set equality, order-independent.
- Dates (Due Date): ISO string equality on `start` field.
- Checkboxes (P0): bool equality.
- Relations (Blocked By): set equality on related page IDs.

A single Notion edit that changes multiple properties produces multiple changelog lines, all with the same timestamp.

### 3.5 Changelog line format (locked contract)

```
<ISO_UTC_TIMESTAMP> | <TASK_ID> | <VERB> | "<TITLE>" | <CHANGE_DESC>
```

- Timestamp: ISO 8601 UTC, `2026-05-02T14:30:21Z`. No fractional seconds.
- Task ID: `T-YYxxxx` or literal `system` for poller meta-events.
- Verb: lowercase, single word from the closed list (3.7).
- Title: double-quoted, max 60 chars, truncated with `...` if longer. Internal `"` escaped as `\"`.
- Change desc: verb-specific (3.7).

Pipe character in title or desc replaced with U+2503 Heavy Vertical Bar so the field separator stays unambiguous.

### 3.6 First-run backfill

If `data/notion_state_cache.json` is missing on first tick:
1. Query ALL active rows (paginated).
2. Write all rows to cache.
3. Emit one line: `<timestamp> | system | backfill | n=<count> active rows`.
4. Subsequent ticks behave normally.

Without this rule, the first tick would emit thousands of `created` lines.

### 3.7 Verb list and change descriptions

| Verb | Change desc format | Example |
|---|---|---|
| status | `<old> -> <new>` | `Not Started -> Done` |
| p0 | `<old> -> <new>` | `false -> true` |
| sprint | `[<csv>] -> [<csv>]` | `[Week 3] -> [Week 4]` |
| owner | `[<csv>] -> [<csv>]` | `[Boubacar] -> [Coding]` |
| due | `<iso> -> <iso>` (use `none` for null) | `none -> 2026-05-08` |
| blocked | `added: <ID>, ...` | `added: T-26045, T-26102` |
| unblocked | `removed: <ID>, ...` | `removed: T-26045` |
| renamed | `"<old>" -> "<new>"` | `"Follow up" -> "Reply to Rod"` |
| notes | `prefix: <new prefix up to first colon>` OR `notes changed (no detail)` | `prefix: Golden Gem` |
| outcome | `set: "<truncated>"` | `set: "shipped 2026-05-02"` |
| created | `Owner=<csv> Sprint=<csv> Source="<src>"` | `Owner=Boubacar Sprint=Backlog Source="Manual: 2026-05-02"` |
| archived | `Sprint moved to Archive` | (literal) |
| deleted | (empty) | (the line itself is the event) |
| backfill | `n=<count> active rows` | `n=638 active rows` |
| rotated | `previous file: <filename>` | `previous file: changelog-2026-04.md` |

### 3.8 Edge cases

| Case | Behavior |
|---|---|
| Notion API 429 | Catch, sleep with backoff, retry once. If still 429: log, release lock, exit tick. Next tick catches up via 6-min window with 1-min overlap. |
| Notion API 5xx | Same retry-once-then-skip pattern. Don't crash heartbeat. |
| Cache file corrupted | Rename to `notion_state_cache.json.broken-<timestamp>`, treat as missing, triggers backfill. |
| Row deleted in Notion | API doesn't return deleted rows in change-window queries. Detect via cache-vs-current set diff once per day at 06:00 MT (special tick). Emit `deleted` line. |
| Two ticks overlap | Coordination lock prevents. Second tick logs and skips. |
| `/task add` row appears in same tick | Poller treats it like any other new row. Emits one `created` line. |
| `last_edited_time` not advanced (Notion bug, rare) | Compare cache vs current on properties anyway. Property diff catches it. |

### 3.9 Cache file shape

`data/notion_state_cache.json`. Same dir as `autonomy_state.json`. Already gitignored via `data/`.

```json
{
  "_meta": {
    "version": 1,
    "last_tick": "2026-05-02T14:30:00Z",
    "last_full_scan": "2026-05-02T06:00:00Z"
  },
  "<notion_page_id>": {
    "task_id": "T-26045",
    "title": "Follow up on inbox replies",
    "status": "Not Started",
    "p0": true,
    "sprint": ["Week 3"],
    "owner": ["Boubacar"],
    "due_date": null,
    "blocked_by": [],
    "notes": "",
    "outcome": ""
  }
}
```

Task ID and title denormalized so diff function does not need a second Notion query for human-readable changelog lines.

### 3.10 Hard caps

- Max 200 rows processed per tick. If exceeded, log warning and continue next tick.
- Max 10 seconds wall-clock per tick.
- Max changelog file size before rotation: 5 MB. Rotate to `changelog-YYYY-MM.md`, start fresh, emit one `rotated` line in the new file.

---

## 4. Changelog as public contract

The changelog format (3.5 + 3.7) is locked once shipped. Downstream consumers will rely on it.

### 4.1 Stability rules

- Never reorder columns. Adding new columns at the end is OK.
- Never change verb names. Can add new verbs. Can never repurpose existing verbs.
- Never edit historical lines. Even to fix a typo. Write a NEW line correcting it: `<timestamp> | T-XXXXX | correction | "..." | see prior line YYYY-MM-DDTHH:MM:SS`.
- File rotation: when current file >5 MB, rename and start fresh.

### 4.2 Downstream consumers (read-only, NOT in this spec)

These will read `changelog.md` going forward. Listed to verify the format supports them.

| Consumer | Query |
|---|---|
| 3-day past-due Telegram digest | Lines with `verb=status` AND new value `In Progress`, where same task_id has no later `status -> Done` AND the In Progress line is >3 days old. |
| Daily standup digest | Group lines from last 24h by verb, count. |
| Bi-weekly Golden Gem nudge | Lines with `verb=notes` AND `prefix: Golden Gem` AND no later notes line removing the prefix, where original line is >14 days old. |
| Audit harvester re-runs | Task IDs where last status change is `Done` since last harvester run. |
| What-shipped-this-week generator | Lines with `verb=outcome` since last Monday. |

Each is a 30-line Python grep/awk over the file. None are built today. Their existence validates the format.

### 4.3 What the changelog is NOT

- Not a state mirror. It's an event stream. To know "current state of T-26045," query Notion or the cache.
- Not a conflict resolver. Records what happened, not what should have happened.
- Not human narrative. Just facts.

### 4.4 Privacy

The changelog will contain task titles, some with client names (e.g., "Reply to Rod (Elevate)"). Committed to private GitHub repo, same exposure as existing `docs/handoff/*.md`. Acceptable risk for one-person repo.

---

## 5. /task add (the only Telegram verb)

### 5.1 Command shape

```
/task add "<title>" [--owner=<owner>] [--sprint=<week>] [--p0]
```

Required: `add` keyword + quoted title.
Optional flags:
- `--owner=Boubacar | Coding | agentsHQ | Decision` (default: Boubacar)
- `--sprint=Backlog | "Week 1" | ... | "Week 12" | Archive` (default: Backlog)
- `--p0` (flips P0=true on the new row AND clears P0 from any other row in same atomic write)

Examples:
```
/task add "Reply to Adam at Shasta Dental"
/task add "Audit Hunter trial decision" --owner=Decision --sprint="Week 2"
/task add "Reply to Rod by Monday" --p0
```

### 5.2 Behavior

1. Parse: text -> `{title, owner, sprint, p0}`. On parse fail, reply with usage hint and stop.
2. Validate: `owner` must be one of four taxonomy values; `sprint` must be one of 14 options. Invalid -> reject with closest-match suggestion.
3. Acquire next Task ID: query Notion for max existing `T-26xxxx`, increment by 1. When 2027 starts, IDs auto-roll to `T-27001`.
4. If `--p0`: clear existing P0 first (single-P0 invariant).
5. Create the Notion row with: Task=title, Status=Not Started, Owner=[parsed], Sprint=[parsed], Task ID=new, P0=parsed flag, Source=`Manual: <YYYY-MM-DD>`.
6. Echo reply (B+C from Q1):
   ```
   Added T-26618: "Reply to Adam at Shasta Dental"
   Top 3:
     T-26045  P0  Follow up on inbox replies
     T-26200       Reply to Rod cover-note response
     T-26101       Send Tier 2 SaaS audit drafts
   ```
   Top 3 query: `Owner contains Boubacar AND Status != Done AND Notes does not start with Golden Gem`, sorted P0 desc -> Priority desc -> Task ID asc, limit 3.
7. Return. Single Telegram message. Poller catches the new row on next tick.

### 5.3 Failure modes

| Failure | Reply |
|---|---|
| Missing/unquoted title | `Missing title. Usage: /task add "<title>" [--owner=X] [--sprint=Y] [--p0]` |
| Bad flag | `Unknown flag --foo. Valid: --owner, --sprint, --p0` |
| Invalid owner | `Owner "boubcar" not found. Did you mean "Boubacar"?` |
| Invalid sprint | `Sprint "Week 13" not found. Valid: Backlog, Week 1-12, Archive.` |
| Notion API down | `Notion API error. Try again in 1 min.` (No row created.) |
| Title duplicate of existing active row | Create anyway, but warn: `Added T-26618 (note: similar title to T-26045 "...")`. Sometimes you want two similar tasks. |

### 5.4 Where it lives

- New function `handle_task_add(text, chat_id) -> str` in `orchestrator/handlers_commands.py`.
- Calls into existing `skills/notion_skill/notion_tool.py`. May add small helper `create_task(title, owner, sprint, task_id, p0)`.
- ~80 lines total. No new file.

No `tasks_writer.py` module: single caller, single sink. YAGNI on abstraction. If a second caller emerges, promote then.

### 5.5 What `/task add` does NOT do

- Doesn't write to changelog directly. Poller does.
- Doesn't dedupe titles strictly.
- Doesn't validate `--sprint` against current 12-week-year cycle.
- Doesn't auto-assign Category, Priority, Due Date, Completion Criteria, Blocked By. Set in Notion if needed.
- Doesn't echo a confirmation step. The reply IS the confirmation.

---

## 6. Verifiable success criteria

Ship is complete when ALL four pass on the live VPS deploy.

**C1: Poller catches Notion clicks.** Click any active task's Status from `Not Started` to `In Progress` in Notion. Within 5 min, a line appears in `docs/audits/changelog.md` matching:
```
<timestamp> | T-XXXXX | status | "<title>" | Not Started -> In Progress
```

**C2: Poller catches /task add.** Fire `/task add "Test from spec verification"` from Telegram. Within 30 seconds: one Telegram echo reply with new T-26xxxx + top 3. Within 5 minutes: one `created` line in changelog. Notion row exists with correct defaults (Owner=Boubacar, Sprint=Backlog, Source=`Manual: <today>`).

**C3: Failure modes return clean errors.**
- `/task add` (no title) -> reply contains usage hint, no Notion write.
- `/task add "x" --owner=NotARealOwner` -> reply names closest valid owner, no write.
- Edit a task's `Source` field in Notion (NOT tracked) -> poller does NOT emit a changelog line.

**C4: Coordination locking works.** Manually trigger two pollers within 1 second. Second logs `lock held by task:notion-state-poller, skipping` and exits cleanly. No duplicate lines, no race condition.

---

## 7. Out of scope (deferred)

| Item | Why deferred | Revisit trigger |
|---|---|---|
| `/task done`, p0, sprint, etc. | Notion clicks + poller solves it. | Operator names a friction a verb would solve. |
| WriteResult dataclass | Single caller; tuples/dicts work. | Second consumer of writer logic. |
| 3-day past-due Telegram digest | Reads the changelog. Separate work. | After 1 week of clean poller. |
| Daily standup digest | Same. | Operator asks for it. |
| Bi-weekly Golden Gem nudge | Same. | After Gems live 14 days. |
| Roadmap markdown auto-edit | Sankofa: too fragile. | A real downstream consumer needs synced markdown state. |
| Notion webhooks (vs polling) | Paid-tier-only, flaky. | Notion ships free webhooks AND latency becomes a felt issue. |
| `--due` flag on /task add | YAGNI. | Operator wants to set due dates from phone. |
| File rotation automation | 5MB cap unlikely week one. | Changelog hits 4 MB. |
| Auto-restart of poller on failure | Heartbeat already retries every 5min. | Poller crashes >2x/week. |

---

## 8. Run plan

Six phases. Build poller before `/task add` so the verb relies on the poller already running.

**Phase 1: Poller skeleton + state cache** (~45 min)
- Create `orchestrator/notion_state_poller.py` with `tick()` function.
- Cache schema + atomic write helpers.
- Backfill mode (first run).
- Unit tests for diff logic (8-10 tests, no Notion API).

**Phase 2: Wire poller to heartbeat + first deploy** (~15 min)
- Register wake in `orchestrator/scheduler.py`.
- Add `task:notion-state-poller` to known coordination locks.
- Deploy via `scripts/orc_rebuild.sh`.
- Verify backfill line appears in changelog.
- Click a Notion row, verify changelog updates within 5 min.

**Phase 3: /task add handler** (~30 min)
- Add `handle_task_add()` in `orchestrator/handlers_commands.py`.
- Wire into command dispatcher.
- Unit tests for parser (10-12 tests, no Notion API).

**Phase 4: Wire /task add + redeploy** (~10 min)
- Deploy via `scripts/orc_rebuild.sh`.
- Smoke test: `/task add "spec verification test"`.
- Verify echo + Notion row + changelog line within 5 min.

**Phase 5: Verification of C1-C4** (~15 min, with Boubacar)
- Walk through C1, C2, C3, C4 against live system.
- If any fail: stop, fix, re-verify before moving on.

**Phase 6: Cleanup** (~10 min)
- Update `docs/roadmap/atlas.md`: add new milestone (Notion state poller, status SHIPPED).
- Open follow-up tasks in Notion as `Owner=Coding` for the deferred items in section 7.

Total estimated build time: ~2 hours of focused work + verification.

---

## 9. Failure modes + rollback

| Failure | Recovery |
|---|---|
| Poller spams duplicate lines | Stop wake (`autonomy_state.json` toggle). Inspect cache. Fix diff logic. Redeploy. |
| Poller misses changes (window too small) | Bump `WINDOW_MIN` from 6 to 10. Env-driven, no code redeploy. |
| Notion 429s sustained | Coordination lock + retry-once handles it. Else: reduce frequency from 5min to 10min. |
| `/task add` wrong Task ID | Manual fix in Notion. Update assignment logic. |
| Cache file disappears | Backfill mode handles it. One `backfill` line, no spam. |
| Heartbeat itself dies | Pre-existing infra issue. Not introduced by this work. |

**Rollback:** disable wake in `autonomy_state.json` -> poller stops. `/task add` handler reverts via git. Notion data untouched.

---

## 10. Council record

**Karpathy v1 verdict:** HOLD. Required cuts before ship: drop WriteResult dataclass, cut 10 verbs to 4, simplify changelog format, define C1-C4. All applied. The 4-verb cut became 0-verb after Sankofa.

**Sankofa v1 verdict:** REWRITE. Original `/task done`, `/task p0` etc. surface was the wrong solution. Right solution: passive Notion poller catches operator clicks without requiring discipline. `/task add` is the only verb that earns its keep (faster than Notion mobile UX for fast capture). Section 2 + 4 + 5 reflect Sankofa's reframe.

**User decisions locked:**
- Q1: B+C echo (confirmation + top 3) on `/task add` reply.
- Q2: C strict ID match + best-guess suggestion on miss.
- Q3: B `/task add` allowed for ad-hoc creation.
- Q4: B single changelog file, no markdown edits.
- Q5: C originally; revised after Sankofa to "no separate writer module" since all state-mutation verbs cut.
- Council reframe: hybrid C (poller + `/task add`).

---

## 11. Cross-references

- Plan: `docs/superpowers/plans/2026-05-02-task-poller-and-add.md` (next, after spec approval)
- Notion Tasks DB: `https://app.notion.com/p/249bcf1a302980739c26c61cad212477`
- Coordination skill: `skills/coordination/__init__.py`
- Scheduler: `orchestrator/scheduler.py`
- Handlers: `orchestrator/handlers_commands.py`
- Notion helper: `skills/notion_skill/notion_tool.py`
- Prior audit spec: `docs/superpowers/specs/2026-05-01-notion-task-audit-design.md`
- Prior audit plan: `docs/superpowers/plans/2026-05-01-notion-task-audit.md`
