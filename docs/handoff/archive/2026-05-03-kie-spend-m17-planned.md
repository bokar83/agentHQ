# Session Handoff - M17 Kie.ai Spend Tracking Planned - 2026-05-03

## TL;DR

Planning-only session. Boubacar proposed adding Kie.ai spend tracking to the Atlas
dashboard. Sankofa Council and Karpathy audit both returned HOLD. Root problem: credit
unit unknown, delta approach breaks on top-ups, original plan would silently store
wrong units in `usd_today`. M17 milestone added to atlas roadmap, gate-blocked on a
10-minute API probe that must run before any code is written.

## What was built / changed

- `docs/roadmap/atlas.md`: M17 milestone added (QUEUED, gate-blocked). Session log
  appended (2026-05-03 Saturday late entry).

## Decisions made

1. **Do not implement the original plan.** Delta approach is conditionally sound only
   with a confirmed fixed credit-to-USD rate. That rate is unknown.

2. **API probe is the gate.** Run the bash command in M17 before writing any code.
   Two questions must be answered: (a) does Kie expose a transaction/usage endpoint?
   (b) what is the credit-to-USD rate?

3. **If transaction endpoint exists:** mirror OpenRouter pattern exactly. Delta approach
   is obsolete.

4. **If balance-only (delta approach):**
   - Keep `take_snapshot()` signature unchanged. Add `take_kie_snapshot()` as standalone.
   - Add `_fetch_kie_live()` as standalone in `atlas_dashboard.py` (not merged into
     `_fetch_provider_spend()`).
   - Store confirmed USD only. Add `KIE_CREDITS_PER_USD` constant.
   - If rate is per-model-variable: use separate `kie_balance_log` table, not
     `provider_billing` (no unit contamination).
   - Day-1 sentinel: write NULL for `usd_today`, not 0.
   - Top-up detection: write NULL, not 0 (zero implies confirmed zero spend).
   - Audit `_get_historical_comparisons()` with synthetic row before modifying -- may
     need zero code changes.

5. **M17 number confirmed.** M9 and M16 were already taken. M17 is correct.

## What is NOT done (explicit)

- No code written. Zero files in orchestrator/ were touched.
- API probe not yet run. This is the mandatory first step.
- Credit-to-USD rate unknown.

## Open questions

- Does `GET /api/v1/chat/credit` return integer credits or USD directly?
- Does Kie expose `/api/v1/usage` or `/api/v1/transactions`?
- What is the credit-to-USD conversion rate? Fixed or per-model?

## Next session must start here

1. Run the API probe on VPS (command is in M17 milestone):
   ```bash
   docker exec orc-crewai python3 -c "
   import requests, os
   h = {'Authorization': f'Bearer {os.environ[\"KIE_AI_API_KEY\"]}'}
   r = requests.get('https://api.kie.ai/api/v1/chat/credit', headers=h)
   print('credit:', r.status_code, r.json())
   r2 = requests.get('https://api.kie.ai/api/v1/usage', headers=h)
   print('usage:', r2.status_code, r2.text[:500])
   r3 = requests.get('https://api.kie.ai/api/v1/transactions', headers=h)
   print('txns:', r3.status_code, r3.text[:500])
   "
   ```
2. Share probe output. Based on result: implement transaction-endpoint pattern OR
   balance-delta with confirmed rate constant.
3. Build M17 per the plan in `docs/roadmap/atlas.md`.

## Files changed this session

- `docs/roadmap/atlas.md` (M17 milestone + session log entry)
- `docs/handoff/2026-05-03-kie-spend-m17-planned.md` (this file)
