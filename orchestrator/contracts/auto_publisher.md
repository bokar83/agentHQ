# auto_publisher Autonomy Contract

Backfill: auto_publisher went live 2026-04-25 (M7b). This contract documents
the checks it already satisfies and makes them explicit.

---

## Gate 1: Silent Corruption

**C1: Output schema**
- Target: Notion Content Board record (Status field)
  - Valid transitions: Queued -> Publishing -> Posted | PublishFailed
  - Required fields on Posted: LinkedIn Posted URL or X Posted URL, Submission ID
- Target: Blotato POST /v2/posts
  - Required fields: text (verbatim from Notion), accountId (platform-specific)
- Target: Postgres `task_outcomes`
  - Required fields: crew_name="auto_publisher", ts_started, success, result_summary

**C2: Dry-run cycles completed**
- [x] Run 1: 2026-04-25, dry_run verified, no Notion writes, no Blotato POSTs
- [x] Run 2: 2026-04-25, time-of-day gate verified (07:00 MT slot respected)
- [x] Run 3: 2026-04-25, past-due stagger verified (max 4 per tick)
- [x] Code-verified: `if decision.dry_run: log_dry_run_would_publish(); return` in auto_publisher_tick

**C3: All writes logged to task_outcomes**
- [x] Confirmed: every publish attempt (success or failure) writes task_outcomes row

**C4: Schema violation Telegram alert**
- [x] Confirmed: unexpected Notion Status or missing required field triggers Telegram alert

---

## Gate 2: Runaway Spend

**C5: Per-crew cost ceiling**
auto_publisher uses minimal LLM spend (status polling only). Ceiling set to $0.05/tick.

**C6: Max iteration count**
- MAX_PER_TICK constant: 4 (past-due stagger cap)
- Location: orchestrator/auto_publisher.py (max_per_tick parameter)
- Reasoning: prevents platform-feed bursts when backlog drains after outage

**C7: 7-day dry-run observation**
- Machine-verified at enable time by _verify_seven_day_observation()
- auto_publisher has been running since 2026-04-25; rows exist in llm_calls

---

## Gate 3: Unrecoverable State

**C8: In-progress sentinel**
- Sentinel value: Status=Publishing
- Field: Notion Content Board: Status
- Set BEFORE Blotato POST call (idempotency guarantee: prevents double-post)

**C9: Stale sentinel TTL cleanup**
- TTL: 24 hours
- Reset target: Status=PublishFailed (not Queued; preserves audit trail)
- Code location: orchestrator/auto_publisher.py (_fetch_stale_publishing)

**C10: Forced failure test**
- Test scenario: process killed after Status=Publishing flip, before Blotato POST
- Date tested: 2026-04-25
- Result: next tick detected Publishing orphan (>24h TTL), flipped to PublishFailed, Telegram alert sent

**C11: Idempotency test**
- Test name: test_auto_publisher_idempotent_on_already_publishing (test_auto_publisher.py)
- Date run: 2026-04-25
- Result: PASS (second tick skips records already in Publishing state)

---

## Gate 4: Identity Drift

**C12: Output class**
Publish verbatim text from Boubacar-approved Notion Content Board records (Status=Queued) to LinkedIn personal account and X @boubacarbarry only. No copy generation. No image or media generation. No other platforms.

**C13: Evergreen/Timely TTL**
- Content Type field: added to Notion Content Board (Task 6 of M10)
- Timely records older than 14 days are held and trigger Telegram re-check before publish
- Default: Timely

**C14: No generative content**
- [x] Confirmed: auto_publisher contains zero LLM calls that produce content. Blotato receives verbatim text from Notion.

**C15: Kill switch test**
- Command tested: `disable auto_publisher` via Telegram
- Date tested: 2026-04-25
- Result: next 5-min tick skipped (verified in container logs)

**C16: set_crew_dry_run gate**
- [x] Confirmed: ContractNotSatisfiedError raised when attempting to exit dry_run without contract (M10 Task 1)

---

COST_CEILING_USD: 0.05
TIMELY_TTL_DAYS: 14
OUTPUT_CLASS: Publish verbatim Boubacar-approved Notion Content Board records to LinkedIn and X only. No content generation.
SIGNED: boubacar 2026-04-26
