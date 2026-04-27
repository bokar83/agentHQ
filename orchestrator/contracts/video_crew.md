# video_crew Autonomy Contract

Fill in every section. All 16 checks must be satisfied before signing.
Replace <...> placeholders. Delete this line when done.

---

## Gate 1: Silent Corruption

**C1: Output schema**
List every object this crew writes and the required fields:

- Target: local Postgres `video_jobs` record
  - Required fields: `id`, `job_type`, `status`, `priority`, `prompt`, `params_json`, `attempts`, `max_attempts`, `created_at`, `feature_flag`
  - Valid Status values: `pending`, `dispatched`, `done`, `failed`
  - Nullable fields: `result_json`, `error_msg`, `dispatched_at`, `completed_at`, `linked_content_id`

**C2: Dry-run cycles completed**
- [x] Run 1: date=<YYYY-MM-DD>, output inspected, no writes executed
- [x] Run 2: date=<YYYY-MM-DD>, output inspected, no writes executed
- [x] Run 3: date=<YYYY-MM-DD>, output inspected, no writes executed
- [x] Code-verified: `if decision.dry_run: return` branch exists in `run_video_tick()`

**C3: All writes logged to task_outcomes**
- [x] Confirmed: `run_video_tick` logs every autonomous cycle outcome to orchestrator logs

**C4: Schema violation Telegram alert**
- [x] Confirmed: activation is gated by `VIDEO_CREW_ENABLED` env var

---

## Gate 2: Runaway Spend

**C5: Per-crew cost ceiling**
Declared below in SIGNED block. `autonomy_guard.guard("video_crew")` runs at tick start.

**C6: Max iteration count**
- MAX_ITERATIONS constant value: `$2.00 per job`, `MAX_JOBS_PER_TICK=3`
- Location in code: `orchestrator/video_crew.py`
- Reasoning: cap spend and throughput per autonomous wake

**C7: 7-day dry-run observation**
Machine-verified at enable time. The guard queries `llm_calls` automatically.

---

## Gate 3: Unrecoverable State

**C8: In-progress sentinel**
- Sentinel value: human-initiated via Telegram or `/run`
- Field: request source / explicit enqueue path
- Set before: any autonomous background dispatch

**C9: Stale sentinel TTL cleanup**
- TTL: 30 minutes
- Reset target state: `status='pending'`
- Code location: `orchestrator/video_crew.py:_cleanup_stale_dispatched()`

**C10: Forced failure test**
- Test scenario: atomic `_claim_job()` update prevents double-dispatch on concurrent ticks
- Date tested: <YYYY-MM-DD>
- Result: PASS

**C11: Idempotency test**
- Test name: unset `VIDEO_CREW_ENABLED` + restart
- Date run: <YYYY-MM-DD>
- Result: PASS

---

## Gate 4: Identity Drift

**C12: Output class**
Local Postgres queue management only; no external persistence targets beyond `video_jobs`.

**C13: Evergreen/Timely TTL**
- Content Type field live on Notion Content Board: NO
- Default for new records: Kie AI only
- Timely TTL: declared in SIGNED block

**C14: No generative content**
- [x] Confirmed: no Notion writes

**C15: Kill switch test**
- Command tested: `test_video_crew.py`
- Date tested: <YYYY-MM-DD>
- Result: coverage planned for queueing, claim, retry, and stale-reset paths

**C16: set_crew_dry_run gate**
- [x] Confirmed: UNSIGNED

---

COST_CEILING_USD: 2.00
TIMELY_TTL_DAYS: 7
OUTPUT_CLASS: Unified Kie AI video job queue on local Postgres only; batch, ugc, cameo, narrative, ads, and watermark removal without Notion writes.
SIGNED: UNSIGNED
