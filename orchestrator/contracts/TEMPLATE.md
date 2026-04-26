# <crew_name> Autonomy Contract

Fill in every section. All 16 checks must be satisfied before signing.
Replace <...> placeholders. Delete this line when done.

---

## Gate 1: Silent Corruption

**C1: Output schema**
List every object this crew writes and the required fields:

- Target: <e.g. Notion Content Board record>
  - Required fields: <Status, Platform, ...>
  - Valid Status values: <Queued, Publishing, Posted, PublishFailed>
  - Nullable fields: <Source Note>

**C2: Dry-run cycles completed**
- [ ] Run 1: date=<YYYY-MM-DD>, output inspected, no writes executed
- [ ] Run 2: date=<YYYY-MM-DD>, output inspected, no writes executed
- [ ] Run 3: date=<YYYY-MM-DD>, output inspected, no writes executed
- [ ] Code-verified: `if decision.dry_run: return` branch exists in tick handler

**C3: All writes logged to task_outcomes**
- [ ] Confirmed: every write produces a task_outcomes row with crew_name, target, payload_summary, success

**C4: Schema violation Telegram alert**
- [ ] Confirmed: out-of-schema write triggers `send_telegram_alert()` and returns without writing

---

## Gate 2: Runaway Spend

**C5: Per-crew cost ceiling**
Declared below in SIGNED block. Guard enforces it per tick.

**C6: Max iteration count**
- MAX_ITERATIONS constant value: <e.g. 10>
- Location in code: <e.g. orchestrator/auto_publisher.py:42>
- Reasoning: <e.g. max records per tick to prevent feed bursts>

**C7: 7-day dry-run observation**
Machine-verified at enable time. The guard queries llm_calls automatically.

---

## Gate 3: Unrecoverable State

**C8: In-progress sentinel**
- Sentinel value: <e.g. Status=Publishing>
- Field: <e.g. Notion Content Board: Status>
- Set before: <which API call>

**C9: Stale sentinel TTL cleanup**
- TTL: <e.g. 30 minutes>
- Reset target state: <e.g. Status=Queued>
- Code location: <e.g. auto_publisher.py:_fetch_stale_publishing()>

**C10: Forced failure test**
- Test scenario: <e.g. killed process after Notion flip, before Blotato POST>
- Date tested: <YYYY-MM-DD>
- Result: <e.g. next tick detected Publishing orphan, reset to Queued within 35 min>

**C11: Idempotency test**
- Test name: <e.g. test_auto_publisher_idempotent_double_tick>
- Date run: <YYYY-MM-DD>
- Result: PASS

---

## Gate 4: Identity Drift

**C12: Output class**
<One sentence. E.g. "LinkedIn and X posts only, from pre-approved Notion Content Board records with Status=Queued, verbatim text passthrough, no AI-generated copy.">

**C13: Evergreen/Timely TTL**
- Content Type field live on Notion Content Board: YES
- Default for new records: Timely
- Timely TTL: declared in SIGNED block

**C14: No generative content**
- [ ] Confirmed: crew contains no LLM call that produces new copy, images, or media

**C15: Kill switch test**
- Command tested: `disable <crew_name>`
- Date tested: <YYYY-MM-DD>
- Result: next tick skipped within 5 min (verified in logs at <timestamp>)

**C16: set_crew_dry_run gate**
- [ ] Confirmed: ContractNotSatisfiedError raised when attempting to exit dry_run without contract

---

COST_CEILING_USD: <float, e.g. 0.05>
TIMELY_TTL_DAYS: 14
OUTPUT_CLASS: <one sentence>
SIGNED: <approver> <YYYY-MM-DD>
