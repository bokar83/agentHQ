# agentsHQ Autonomous Crew Contract
# Design Spec: 2026-04-26

## Status
Approved. Ready to implement.

## Problem
agentsHQ has 30+ crews. A growing subset run on a heartbeat with no human in the loop
to start them. Today, the only gate before flipping a crew live is a manual flag flip in
autonomy_state.json. No written standard exists for what a crew must demonstrate before
that flip is allowed. This means every new autonomous crew is a judgment call, and the
judgment has no memory across sessions.

Four failure modes are unaddressed:
1. Silent corruption: crew writes bad data, appears to succeed, no alert
2. Runaway spend: crew burns $5 in one tick before the daily cap catches it
3. Unrecoverable state: crew fails mid-execution, leaves records half-written, next tick makes it worse
4. Identity drift: something is posted that is not Boubacar's voice, not his intent, at the wrong moment

## Scope
Heartbeat crews only: `griot`, `auto_publisher`, `concierge`, `chairman`, `studio`.
On-demand crews (30+ in CREW_REGISTRY, triggered by Telegram message) are out of scope.

## Design

### Enforcement Architecture

Two functions in `orchestrator/autonomy_guard.py` become hard gates:

```python
def set_crew_enabled(crew_name: str, enabled: bool) -> None:
    if enabled:
        _assert_contract_satisfied(crew_name)  # raises ContractNotSatisfiedError
    ...

def set_crew_dry_run(crew_name: str, dry_run: bool) -> None:
    if not dry_run:
        _assert_contract_satisfied(crew_name)  # raises ContractNotSatisfiedError
    ...
```

`set_crew_dry_run(..., False)` is the actual live-fire transition: a crew can be
`enabled=True, dry_run=True` (safe) without issue, but exiting dry_run requires the
same contract check. Both transitions are gated.

`_assert_contract_satisfied(crew_name)` does two things:
1. Reads `orchestrator/contracts/<crew_name>.md`: raises if file missing or unsigned
2. Runs machine-verifiable checks (C5, C7) inline: raises if they fail

### Contract File Format

Each heartbeat crew gets `orchestrator/contracts/<crew_name>.md`. The file is a filled-in
checklist. The enforcement function looks for a `SIGNED:` block at the bottom:

```
SIGNED: <approver> <YYYY-MM-DD>
COST_CEILING_USD: 0.10
TIMELY_TTL_DAYS: 14
OUTPUT_CLASS: <one-line description of exactly what this crew can create or publish>
```

Missing file = `ContractNotSatisfiedError`. Missing `SIGNED:` block = same.
Missing `COST_CEILING_USD` = same (required for C5 enforcement).

### The 16 Checks

#### Gate 1: Silent Corruption

**C1: Output schema documented**
Every object the crew writes (Notion record, Postgres row, Blotato post, Telegram message)
has a documented schema in the contract file: required fields, valid values, nullable fields.
Any write the crew makes that is not covered by this schema is a bug.

**C2: Dry-run cycles completed and code-verified**
The crew has been run with `dry_run=True` at least 3 times and output was inspected manually
each time. Additionally, code-verified that no writes execute when `guard().dry_run == True`.
The dry_run path must be a branch in the crew's tick handler, not just a guard at the top.

**C3: All writes logged to task_outcomes**
Every write the crew makes is logged to `task_outcomes` with: `crew_name`, `target`
(e.g., "notion:Content Board:record_id"), `payload_summary`, `success` (bool), `error_message`.
Writes that are not logged are invisible to debugging and the Chairman learning loop.

**C4: Schema violation triggers Telegram alert**
If the crew attempts to write a value outside the documented schema (wrong Status value,
null where required, unexpected field), it surfaces a Telegram alert to Boubacar and
does NOT continue silently. Alert format: crew name, field, expected, actual.

---

#### Gate 2: Runaway Spend

**C5: Per-crew cost ceiling in autonomy_state.json, enforced by guard()**
`autonomy_state.json` carries a `cost_ceiling_usd` field per crew. `guard()` enforces it
per tick alongside the global daily cap: whichever is lower wins. The ceiling is also
declared in the contract file's `SIGNED:` block so it is human-readable.

Example state schema addition:
```json
"crews": {
  "griot": {
    "enabled": true,
    "dry_run": false,
    "cost_ceiling_usd": 0.05
  }
}
```

**C6: Hard max iteration count per tick**
If the crew iterates over records, retries, or loops for any reason, there is a hard
`MAX_ITERATIONS` constant declared in the crew module that cannot be exceeded regardless
of input size. The contract file documents the value and the reasoning.

**C7: Machine-verified 7-day dry-run observation**
`_assert_contract_satisfied()` queries `llm_calls` for this crew over the past 7 days.
It confirms: (a) at least 1 autonomous row exists (crew has actually run), (b) no single
tick's spend exceeded `cost_ceiling_usd`. This is not a checkbox: it is a live query
at enable time. If the crew has not run for 7 days or has breached the ceiling on any
tick, the enable call fails.

---

#### Gate 3: Unrecoverable State

**C8: In-progress status flip before any external write**
Before the crew touches any external record, it flips a sentinel status
(e.g., `Status=Publishing`, `status=processing`). This is the idempotency marker.
If the crew crashes after the flip, the next tick sees the sentinel and knows a
prior run was interrupted. The contract file documents what the sentinel value is
and which field it lives in.

**C9: Stale in-progress TTL cleanup**
The crew's tick handler checks for records stuck in the in-progress sentinel status
for longer than a declared TTL (e.g., 30 minutes). Stale records are reset to a
recoverable state (not deleted, not ignored). The TTL and reset target state are
documented in the contract file.

**C10: Forced failure tested, self-recovered**
At least one deliberate failure has been tested: process killed mid-write, exception
raised after status flip, Notion API timeout. The next tick recovered cleanly without
human intervention. The test scenario and result are documented in the contract file.

**C11: Idempotency verified via test harness**
Running the crew twice in the same tick window produces the same result as running it
once. Verified via a deliberate test harness that bypasses heartbeat tick deduplication
and calls the callback twice. Not assumed from tick deduplication: that is a separate
guarantee. Test name and date documented in the contract file.

---

#### Gate 4: Identity Drift

**C12: Output class bounded**
The contract file's `OUTPUT_CLASS` line specifies exactly what the crew can create or
publish. Example: "LinkedIn and X posts only, from pre-approved Notion Content Board
records with Status=Queued, verbatim text passthrough, no AI-generated copy."
Any output outside this class is a bug, not a feature. The crew's code must make
it structurally impossible to produce output outside this class (not just
a runtime check).

**C13: Approved records carry Evergreen/Timely flag; Timely records expire**
The Notion Content Board gets a new `Content Type` select property: `Evergreen` / `Timely`.
Set by Boubacar at approval time. Default: `Timely`.

`auto_publisher` behavior:
- `Evergreen` records: publish whenever scheduled. No expiry.
- `Timely` records: if `Scheduled Date` is more than `TIMELY_TTL_DAYS` days past the
  approval date, hold the record and send a Telegram re-check:
  "This post was approved N days ago. Still good? [Publish] [Skip] [Edit]"
  One tap resets the clock.

`TIMELY_TTL_DAYS` default: 14. Declared in the contract file's `SIGNED:` block.

**C14: No generative content in flight**
The crew formats, schedules, and publishes. It does not generate new copy, images,
or media autonomously. Griot picks from existing approved records: it does not
draft new ones. If a crew needs generative capability in the future, that requires
a new contract review, not a flag flip.

**C15: Kill switch tested on this crew specifically**
The Telegram `disable <crew_name>` command has been tested on this specific crew.
After the command, the next heartbeat tick did NOT fire the crew (verified in logs
within 5 minutes). Test date documented in the contract file.

**C16: set_crew_dry_run(..., False) is also gated**
Explicitly called out as its own check because it is the actual live-fire transition.
A crew that passed `set_crew_enabled` but then has `set_crew_dry_run(..., False)` called
without a contract re-check would exit dry_run silently. The enforcement in
`set_crew_dry_run` closes this gap.

---

### New Postgres Table: content_approvals

Tracks first-try approval rate as a clean signal for the Chairman learning loop (M5).
No joins, no archeology: one query answers "what % of posts did Boubacar approve
on the first try?"

```sql
CREATE TABLE content_approvals (
    id               SERIAL PRIMARY KEY,
    notion_page_id   TEXT NOT NULL,       : Content Board record ID
    attempt_number   INTEGER NOT NULL,    : 1 = first try, 2+ = revised and resubmitted
    submitted_at     TIMESTAMPTZ NOT NULL,
    decided_at       TIMESTAMPTZ,
    decision         TEXT NOT NULL,       : approved / rejected / skipped / edited
    evergreen        BOOLEAN NOT NULL,    : mirrors Notion Content Type at decision time
    platform         TEXT NOT NULL,       : linkedin / x
    griot_score      FLOAT,              : score griot assigned at pick time
    chairman_score   FLOAT               : null until M5, filled retrospectively
);
```

New row per attempt. Rejected + revised = row 1 (rejected) + row 2 (approved).
This preserves full history for pattern analysis.

Chairman's learning signal query:
```sql
SELECT
    COUNT(*) FILTER (WHERE attempt_number = 1 AND decision = 'approved') AS first_try_approved,
    COUNT(*) AS total,
    ROUND(
        100.0 * COUNT(*) FILTER (WHERE attempt_number = 1 AND decision = 'approved') / COUNT(*),
        1
    ) AS first_try_pct
FROM content_approvals
WHERE submitted_at > NOW() - INTERVAL '30 days';
```

When `first_try_pct` consistently exceeds ~90% over 4+ weeks, the crew has learned
Boubacar well enough to propose going fully autonomous on that content class.
This is the trigger for L5 Chairman to recommend removing the approval step.

---

### Notion Schema Change

New field on Content Board: `Content Type` (select)
- `Evergreen`: always publish when scheduled, no expiry
- `Timely`: expires after `TIMELY_TTL_DAYS` days, requires re-check

Set at approval time. Default: `Timely`. Griot's approval Telegram message
gets updated to include the flag as a third button: `[Approve Evergreen]` vs
default approve = Timely.

---

### Backfill: griot and auto_publisher

Both crews already satisfy most checks implicitly. Their contract files get written
and signed as part of this milestone to make the implicit explicit.

Code changes required for backfill:
- Add `cost_ceiling_usd` to `autonomy_state.json` for both crews
- Add `content_approvals` write to griot's approval handler
- Add Evergreen/Timely check to auto_publisher's tick handler
- Add `Content Type` Notion field to Content Board

No behavioral changes to existing flows.

---

### Contract Files to Create

| File | Status |
|---|---|
| `orchestrator/contracts/griot.md` | Write + sign this session (backfill) |
| `orchestrator/contracts/auto_publisher.md` | Write + sign this session (backfill) |
| `orchestrator/contracts/concierge.md` | Write at M4 build time |
| `orchestrator/contracts/chairman.md` | Write at M5 build time |
| `orchestrator/contracts/studio.md` | Write at Studio M4 build time |

---

### Files to Create or Modify

| File | Change |
|---|---|
| `orchestrator/autonomy_guard.py` | Add `_assert_contract_satisfied()`, gate `set_crew_enabled` + `set_crew_dry_run` |
| `orchestrator/contracts/griot.md` | NEW: backfill contract |
| `orchestrator/contracts/auto_publisher.md` | NEW: backfill contract |
| `orchestrator/autonomy_state.json` (VPS) | Add `cost_ceiling_usd` per crew |
| `supabase/migrations/` or `orchestrator/db.py` | Add `content_approvals` table |
| `orchestrator/griot.py` | Write to `content_approvals` on each approval decision |
| `orchestrator/auto_publisher.py` | Evergreen/Timely check + Timely TTL hold logic |
| Notion Content Board (live via API) | Add `Content Type` select field |

---

### The Learning Arc

This contract is the floor. The Chairman learning loop (M5) is how the floor rises.

1. Today: Boubacar approves everything manually. Every tap is a data point in `content_approvals`.
2. M5 (Chairman, ~2026-05-08): Chairman reads `content_approvals`, identifies patterns
   (rejected reasons, griot_score correlation, topic/platform patterns), proposes scoring
   weight mutations to griot, enqueues proposals to `approval_queue`.
3. The signal: first-try approval rate climbs toward ~90% sustained over 4+ weeks.
4. The gate: that rate, not a calendar date, is the trigger to propose removing the
   approval step for that content class. Chairman recommends. Boubacar decides.

Fully autonomous content posting is earned, not assumed. The contract makes the earning
measurable.

---

### Open Questions (resolved)

| Question | Decision |
|---|---|
| Evergreen/Timely flag location | Notion Content Board (queryable by Chairman) |
| Re-attestation mechanism | Timely TTL + Telegram re-check, not periodic manual review |
| New row vs update on re-submission | New row: preserves full attempt history |
| Enforcement point | Both `set_crew_enabled` AND `set_crew_dry_run` |
| C7 verification | Machine query at enable time, not signed checkbox |

---

## Build Sequence

This spec produces one implementation milestone: **M10: Autonomous Crew Contract**.

Suggested branch: `feat/atlas-m10-crew-contract`

Block 1 (1h): `autonomy_guard.py`: `_assert_contract_satisfied()`, gate both functions, `ContractNotSatisfiedError`, `cost_ceiling_usd` in state schema + `guard()` enforcement
Block 2 (1h): `content_approvals` table migration + write calls in `griot.py`
Block 3 (1h): Evergreen/Timely in `auto_publisher.py` + Notion `Content Type` field
Block 4 (30min): Write + sign `contracts/griot.md` + `contracts/auto_publisher.md`
Block 5 (30min): Tests + deploy + verify both existing crews still pass the contract gate

Total: ~4h
