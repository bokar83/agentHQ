# video_crew Autonomy Contract

---

## Gate 1: Silent Corruption

**C1: Output schema**

- Target: Postgres local DB, video_jobs table
  - Required fields: id, job_type, status, priority, prompt, params_json, created_at, requested_by
  - Valid status values: pending, dispatched, running, done, failed, cancelled
  - Valid job_type values: batch, ugc, cameo, narrative, ads, watermark_remove
  - Nullable fields: result_json, error_msg, dispatched_at, completed_at, linked_content_id

- Target: Supabase media_generations table (written by kie_media, not dispatcher directly)
  - Written on every successful Kie API call
  - No additional writes by video_crew.py

**C2: Dry-run cycles completed**
- [ ] Run 1: date=PENDING, output inspected, no Kie calls executed
- [ ] Run 2: date=PENDING, output inspected, no Kie calls executed
- [ ] Run 3: date=PENDING, output inspected, no Kie calls executed
- [x] Code-verified: `if not decision.allowed: return` branch exists in run_video_tick()

**C3: All writes logged to task_outcomes**
- [x] Confirmed: run_video_tick() writes episodic_memory outcome row via start_task/complete_task pattern

**C4: Schema violation Telegram alert**
- [x] Confirmed: invalid job_type raises ValueError before any DB write; enqueue() returns error string

---

## Gate 2: Runaway Spend

**C5: Per-crew cost ceiling**
$2.00 per job (Kie AI video generation ceiling). Guard enforces per tick.

**C6: Max iteration count**
- MAX_JOBS_PER_TICK constant value: 3
- Location in code: orchestrator/video_crew.py (module-level constant)
- Reasoning: 3 jobs x $2.00 ceiling = $6.00 max spend per 5-min tick. Prevents burst spend.

**C7: 7-day dry-run observation**
Machine-verified at enable time. Guard queries llm_calls automatically.

---

## Gate 3: Unrecoverable State

**C8: In-progress sentinel**
- Sentinel value: status='dispatched'
- Field: video_jobs.status
- Set before: Kie API createTask call (atomic UPDATE in _claim_job)

**C9: Stale sentinel TTL cleanup**
- TTL: 30 minutes
- Reset target state: status='pending' (with attempts increment)
- Code location: video_crew.py:VideoJobDispatcher._cleanup_stale_dispatched()

**C10: Forced failure test**
- Test scenario: job claimed (status=dispatched), process killed before Kie call completes
- Date tested: PENDING (required before live enable)
- Result: PENDING: next tick _cleanup_stale_dispatched() should reset to pending within 30 min

**C11: Idempotency test**
- Test name: test_claim_job_is_atomic (concurrent claim: only one succeeds)
- Date run: PENDING
- Result: PENDING

---

## Gate 4: Identity Drift

**C12: Output class**
Video generation jobs only, dispatched from explicit user requests (Telegram or /run command). No AI-generated copy. Crew enqueues and dispatches Kie API calls; all media stored to Google Drive and logged to Supabase. No Notion writes, no social publishing.

**C13: Evergreen/Timely TTL**
- Not applicable: video_crew does not post to Content Board or publish content
- Video assets stored to Drive with standard MEDIA_* naming convention

**C14: No generative content**
- [ ] Note: UGC and ads job types DO call claude-haiku inline for scene splitting / brief structuring. This is prompt engineering (input structuring), not copy generation for publication. Output is structured params, not publishable content.
- [x] Confirmed: no crew LLM call produces copy, images, or media for direct publication

**C15: Kill switch test**
- Command tested: set VIDEO_CREW_ENABLED= (blank) and restart container
- Date tested: PENDING
- Result: PENDING: heartbeat wake not registered when env var absent

**C16: set_crew_dry_run gate**
- [x] Confirmed: autonomy_guard enforces dry_run check; crew starts enabled=false, dry_run=true in autonomy_state.json

---

COST_CEILING_USD: 2.00
TIMELY_TTL_DAYS: 14
OUTPUT_CLASS: Video generation jobs dispatched to Kie AI, results stored to Google Drive and local Postgres. No content publication. No Notion writes.
SIGNED: UNSIGNED
