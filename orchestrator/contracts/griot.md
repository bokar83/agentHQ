# griot Autonomy Contract

Backfill: griot has been live since 2026-04-24. This contract documents the checks
it already satisfies implicitly and makes them explicit.

---

## Gate 1: Silent Corruption

**C1: Output schema**
- Target: Postgres `approval_queue` table
  - Required fields: crew_name, proposal_type, payload (JSONB with notion_id/title/platform/total_score/hook_preview/why_chosen/score), ts_created
  - Nullable: telegram_msg_id (set after send), ts_decided, decision_note
- Target: Postgres `task_outcomes` table
  - Required fields: crew_name, ts_started, success, result_summary
- Target: Telegram message (preview card to Boubacar)
  - Required fields: hook_preview, platform, scheduled_date, approve/reject buttons

**C2: Dry-run cycles completed**
- [x] Run 1: 2026-04-24, output inspected, no writes executed in dry_run
- [x] Run 2: 2026-04-24, weekend gate verified (griot correctly skipped Saturday)
- [x] Run 3: 2026-04-25, dry_run path verified in griot_morning_tick
- [x] Code-verified: `if decision.dry_run: log and return` in griot_morning_tick

**C3: All writes logged to task_outcomes**
- [x] Confirmed: griot_morning_tick calls episodic_memory.complete_task() on every path

**C4: Schema violation Telegram alert**
- [x] Confirmed: malformed candidate triggers early return with Telegram error message

---

## Gate 2: Runaway Spend

**C5: Per-crew cost ceiling**
griot uses 0 LLM spend (deterministic scorer, no LLM calls). Ceiling set to $0.01
as a safety sentinel: any LLM call from griot would be unexpected.

**C6: Max iteration count**
- MAX_CANDIDATES constant: 5 (top-N scored candidates considered per tick)
- Location: orchestrator/griot.py (_split_pool function)
- Reasoning: griot picks 1 candidate per tick; scanning more is unnecessary overhead

**C7: 7-day dry-run observation**
- Machine-verified at enable time by _verify_seven_day_observation()
- griot has been running since 2026-04-24; rows exist in llm_calls (0-cost rows)

---

## Gate 3: Unrecoverable State

**C8: In-progress sentinel**
- griot writes to approval_queue (append-only). No in-progress flip needed.
- Idempotency handled by _candidate_already_proposed() 7-day dedup check.

**C9: Stale sentinel TTL cleanup**
- Not applicable: approval_queue rows are append-only, never left in a transient state.

**C10: Forced failure test**
- Test scenario: griot tick killed after approval_queue insert, before Telegram send
- Date tested: 2026-04-25
- Result: next tick detected existing pending proposal via _candidate_already_proposed(), skipped re-insert. Telegram re-send handled by heartbeat retry.

**C11: Idempotency test**
- Test name: test_griot_double_fire_deduplicates (in test_griot_scheduler.py)
- Date run: 2026-04-25
- Result: PASS (double-fire produces one approval_queue row, not two)

---

## Gate 4: Identity Drift

**C12: Output class**
Proposal of a single LinkedIn or X post candidate to Boubacar for approval only. griot never publishes. It selects from pre-existing Notion Content Board records (Status=Ready). No copy generation.

**C13: Evergreen/Timely TTL**
- Content Type field: added to Notion Content Board (Task 6 of M10)
- Default: Timely
- Timely TTL: 14 days

**C14: No generative content**
- [x] Confirmed: griot contains zero LLM calls. Scorer is deterministic (rule-based).

**C15: Kill switch test**
- Command tested: `disable griot` via Telegram
- Date tested: 2026-04-25
- Result: next tick skipped (verified in container logs)

**C16: set_crew_dry_run gate**
- [x] Confirmed: ContractNotSatisfiedError raised when attempting to exit dry_run without contract (M10 Task 1)

---

COST_CEILING_USD: 0.01
TIMELY_TTL_DAYS: 14
OUTPUT_CLASS: Propose a single pre-approved Notion Content Board candidate to Boubacar for human approval. No publishing. No copy generation.
SIGNED: boubacar 2026-04-26
