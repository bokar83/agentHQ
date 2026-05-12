# CW Automation Strip — Rationale & Handoff

**Date:** 2026-05-12
**Branch:** `feat/strip-cw-automation`
**Decision driver:** Sankofa Council + parallel CC CLI council premortem (both converged)

## What was stripped

`signal_works/morning_runner.py` Steps 4 / 4.5 / 5 / 5b:

| Step | Did | Removed |
|---|---|---|
| 4   | CW Apollo lead topup (`topup_cw_leads.topup_cw_leads`) | ✅ |
| 4.5 | CW voice personalization (`voice_personalizer.personalize_pending_leads`) | ✅ |
| 5   | CW T1-T5 auto-send (`sequence_engine.run_sequence("cw", ...)`) | ✅ |
| 5b  | CW recycle / T-advance (`recycle_cw.recycle_yesterdays_cw`) | ✅ |

`cw_drafted` / `cw_recycled` locals retained at `0` to keep downstream
delegation payload + atexit alert schema stable. `CW_THRESHOLD` constant left
in place (harmless, removed from health check).

## What was NOT stripped

- **`sequence_engine` itself** — runs from DB queue. Existing CW leads already
  in flight (T2-T5) keep advancing through their cadence via the regular cron.
  This is intentional: we don't abandon prospects mid-sequence.
- **`topup_cw_leads.py`** module still exists in repo — only the morning_runner
  invocation removed. If a future manual CW push is needed, the module is
  callable directly.
- **CW DB tables / lead history** — untouched.

## Evidence backing the decision

Pulled 2026-05-12 by RCA evidence subagent:

- **Replies last 14 days:** 0 across 715 lead_interactions
- **CW messaged all-time:** 142 (0 replies, 0 meetings, $0 revenue)
- **CW Apollo widened-ICP email coverage:** 121/124 = 97.6% → sourcing was
  fine, conversion was the failure
- **Apollo "no org match" rate on SMB trades:** 663:1 (memory:
  `feedback_harvest_per_touch_caps_ship1_ship2c.md`)
- **Hunter Starter utilization:** 100/2000 (5%) — overpaying capacity
- **Today's CW sends (2026-05-12):** 0 (systemd killed mid-Step 2)
- **Premortem all 4 scenarios:** infra-work substituting for recognition-work
  was the consistent failure mode

## Apollo subscription

Boubacar cancelled Apollo Basic plan 2026-05-12. Plan stays active until
**2026-05-28**, then auto-switches to Apollo Free tier.

**Risk after 2026-05-28:** SW pipeline still imports `apollo_client.find_owner_by_company`
in `signal_works/topup_leads.py:35`. Free tier rate limits or auth failures
may cause silent SW degradation. Need to either:

1. Verify Apollo Free tier still works for SW's narrow use case (org-only
   `find_owner_by_company`, not bulk reveal), OR
2. Remove Apollo from SW chain entirely (memory already says Apollo is "dead
   weight for trades-SMBs" — Hunter + Prospeo would be sole enrichment path), OR
3. Downgrade gracefully — wrap Apollo call in try/except returning None to
   keep chain alive.

**Recommendation:** Option 2 before 2026-05-28. Apollo on trades = 663:1
miss anyway. Strip from SW chain too.

## CW pipeline going forward (manual mode)

1. **Permission filter (CC framing):** *If you cannot name the reason the
   prospect already knows who Boubacar is, the name does not go on the list.*
2. Sources that qualify:
   - Warm referrals
   - Completed SW audit clients (SW → CW upsell ladder)
   - Inbound DMs from CW content engagement
   - Specific founders Boubacar has had genuine prior contact with
3. Sources that DO NOT qualify:
   - Cold-scrape lists
   - Apollo/ZoomInfo "looks like ICP" matches
   - LinkedIn search results without prior engagement
4. Add by hand to `data/cw_target_list.csv` (TBD — Boubacar to seed this
   week). Existing `sequence_engine.run_sequence("cw")` will pick them up
   from DB once added via `topup_cw_leads` manual call OR a simpler CSV-
   import script.

## Inbound signal metric (NEW — track weekly)

Per CC council: track weekly count of unsolicited DMs + non-network post
engagement. Leading indicator that CW recognition is compounding. Log
location TBD (Notion or markdown). If 0 in 4 consecutive weeks, recognition
diagnosis is wrong → re-council.

## What still needs to happen this week

| Day | Action | Owner |
|---|---|---|
| Tue (today) | Watch Hunter post-fix pull complete. Log SW yield. | Boubacar + monitoring |
| Tue | Open Prospeo `INVALID_DATAPOINTS` debug ticket (silently poisons SW) | Boubacar / dev session |
| Wed | Answer "10 names" question in writing. Seed `data/cw_target_list.csv`. | Boubacar |
| Wed-Thu | Verify Apollo Free-tier behavior OR strip Apollo from SW chain | Dev session |
| Fri | First CW LinkedIn post drafted for Monday publish. Inbound-signal log stood up. | Boubacar |

## Rollback

If this strip turns out to be wrong (e.g. CW reply rate retroactively
surfaces from already-in-flight T2-T5 cadence and warm-pivot proves harder
than expected):

```bash
git revert <strip-commit-sha>
# OR cherry-pick original Steps 4/4.5/5/5b from main~1
```

CW lead DB + sequence_engine code unchanged → restoration is purely a
morning_runner.py revert.
