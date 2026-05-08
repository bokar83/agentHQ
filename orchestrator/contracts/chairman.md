# chairman Autonomy Contract

M5 L5 Learning Loop. Weekly oversight crew that reads approval outcomes,
identifies scoring patterns, and proposes SCORING_WEIGHTS mutations to
Boubacar for approval. Applies approved mutations via agent_config.

---

## Gate 1: Silent Corruption

**C1: Output schema**
- Target: Postgres `approval_queue` table
  - Required fields: crew_name="chairman", proposal_type="weight-mutation",
    payload (JSONB with field, current, proposed, rationale, target, note)
  - Valid field values: total_score_weight, next_arc_bonus, topic_overlap_penalty,
    recent_arc_phase_penalty, RECENCY_WINDOW_DAYS, ARC_PHASE_WINDOW_DAYS
  - Nullable: telegram_msg_id (set after send)
- Target: Postgres `agent_config` table (on approved mutation only)
  - Required fields: key (GRIOT_<FIELD>), value (string float), note
  - Written only by apply_mutation() after explicit Boubacar approval

**C2: Dry-run cycles completed**
- [ ] Run 1: date=YYYY-MM-DD, output inspected, no writes executed
- [ ] Run 2: date=YYYY-MM-DD, output inspected, no writes executed
- [ ] Run 3: date=YYYY-MM-DD, output inspected, no writes executed
- [ ] Code-verified: MIN_OUTCOMES=7 guard skips without writing when data is insufficient

**C3: All writes logged to task_outcomes**
- [ ] Confirmed: chairman_weekly_tick does not currently open a task_outcomes row
  (Week 1 observation window only; add episodic_memory tracking in M5.1)

**C4: Schema violation Telegram alert**
- [ ] Confirmed: apply_mutation() returns False and logs error on unknown field
  (no Telegram alert yet; add in M5.1 if mutation error rate warrants it)

---

## Gate 2: Runaway Spend

**C5: Per-crew cost ceiling**
- One Sonnet call per Monday tick, max 1000 tokens output
- Estimated max cost per tick: ~$0.005 (1000 tokens at claude-sonnet-4-6 rates)
- COST_CEILING_USD: 0.02 (4x safety margin over expected cost)

**C6: Max iteration count**
- MAX_TOKENS: 1000 (per Sonnet call, enforced at call_llm level)
- MAX_PROPOSALS: 3 (Sonnet instructed to return at most 3 items)
- Tick fires once per Monday: no iteration loop

### C6a: Canary run ($0.50 cap)
- [ ] Canary date: YYYY-MM-DD
- [ ] Budget cap applied: $0.50
- [ ] llm_calls rows confirmed: one row with crew_name=chairman, model=claude-sonnet-4-6
- [ ] Actual cost per tick: $MEASURED
- [ ] Firing rate verified: once per week

**C7: 7-day dry-run observation**
- Machine-verified at enable time
- At least 2 Monday ticks must fire in dry_run before enabling

---

## Gate 3: Unrecoverable State

**C8: In-progress sentinel**
- chairman writes to approval_queue (append-only). No in-progress flip needed.
- Dedup: _field_already_queued() prevents duplicate pending proposals per field.

**C9: Stale sentinel TTL cleanup**
- Not applicable: approval_queue rows are append-only, never left in transient state.

**C10: Forced failure test**
- [ ] Test scenario: tick killed after Sonnet call, before enqueue
- [ ] Date tested: YYYY-MM-DD
- [ ] Result: next Monday tick re-runs Sonnet, produces same proposals, dedup guard skips already-queued fields

**C11: Idempotency test**
- [ ] Test name: test_chairman_enqueue_dedup_skips_existing_pending
- [ ] Date run: YYYY-MM-DD
- [ ] Result: PASS

---

## Gate 4: Identity Drift

**C12: Output class**
Proposes scoring weight mutations to Boubacar for explicit approval. Never publishes
content. Never modifies griot.py directly. Only writes agent_config after human ack.

**C13: Evergreen/Timely TTL**
- Not applicable: chairman produces weight mutation proposals, not content.

**C14: No generative content**
- [ ] Confirmed: chairman uses Sonnet to reason about weights only, not to produce
  posts, images, or any publishable content.

**C15: Kill switch test**
- [ ] Command tested: `disable chairman` via Telegram
- [ ] Date tested: YYYY-MM-DD
- [ ] Result: next Monday tick skipped (verified in logs)

**C16: set_crew_dry_run gate**
- [ ] Confirmed: ContractNotSatisfiedError raised when attempting to exit dry_run without contract

---

COST_CEILING_USD: 0.02
TIMELY_TTL_DAYS: N/A
OUTPUT_CLASS: Proposes scoring weight mutations to agent_config for human approval. No publishing. No content generation. Applies changes only after explicit Boubacar ack.
SIGNED: pending -- complete dry-run cycles before signing
