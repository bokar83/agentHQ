# Session Handoff - GMaps Lead-Gen Absorb + SW T1 Gate - 2026-05-09

## TL;DR

Absorbed m0h/@exploraX_ Google Maps lead-gen playbook (pasted X thread). Verdict: PROCEED. Extracted three pieces of real value from a manual workflow and wired them directly into the SW pipeline: a 4-signal GMB qualification scorer gating T1 sequence enrollment, and a cold-call reference card with objection scripts. Both shipped same session. Pipeline audit due 2026-05-28.

## What was built / changed

- `skills/serper_skill/hunter_tool.py` — `score_gmb_lead(lead: dict) -> int` added with 4 named constants (`GMB_LOW_REVIEW_THRESHOLD=30`, `GMB_LOW_RATING_THRESHOLD=4.0`, `GMB_REQUIRED_FIELDS={"phone","website_url","google_address"}`). Scores 0-4 on: review count, has_website, google_rating, missing fields.
- `skills/outreach/sequence_engine.py` — T1 SW gate in `_get_due_leads()`: leads scoring < 2 via `score_gmb_lead()` are dropped before sequence enrollment. SW T1 only — CW and Studio paths untouched. Dual import path for VPS + local.
- `skills/hormozi-lead-gen/references/cold-call-scripts.md` — new file: 3 objection counters, "walkthrough not meeting" reframe, "tomorrow at 10" close, offer menu (website / review automation / missed-call text-back).
- `docs/roadmap/atlas.md` — Atlas item #11 added (GATED: scorer output → website-teardown warm T1 opener, trigger 2026-05-28). Cheat block + session log updated.
- `docs/reviews/absorb-log.md` — verdict logged.
- `docs/reviews/absorb-followups.md` — follow-up logged + marked DONE (shipped same session).

## Decisions made

- **SQL vs Python gate:** Gate wired as Python-side post-fetch filter (not SQL WHERE clause) because `has_website`, `review_count`, `google_rating` are already stored columns but adding SQL conditions would require reading enrollment SQL more carefully. Python filter is auditable and zero blast-radius change.
- **T1 only, not T2-T5:** Once a lead enrolls (T1 sent), the sequence runs to completion. Gate only applies at enrollment. Karpathy P3 preserved.
- **Reference doc, not skill trigger:** Cold-call scripts are Boubacar-operated (not agent-executed). Placed in `hormozi-lead-gen/references/` not wired into any agent workflow.
- **Phase 2 deferred to Atlas #11:** Auto-audit (scorer output → website-teardown one-pager as warm T1 opener) gated until 2026-05-28 baseline established.

## What is NOT done (explicit)

- **Pipeline audit (2026-05-28):** Run query against active SW sequence to confirm zero leads with >100 reviews or `has_website=True` in `sequence_touch=1` rows. No audit command exists yet — needs thin wrapper or manual SQL.
- **VPS deploy:** Code changes not yet deployed. Requires `git pull && docker compose up -d orchestrator` on VPS.
- **Atlas #11 (auto-audit opener):** Gated until 2026-05-28. Do not start before baseline.

## Open questions

- Should `score_gmb_lead` return signal labels (for logging which signals fired) in addition to the integer score? Currently silent — gate log only says "dropped N leads". Could add `signal_notes` dict return for future email personalization matching the article's approach.
- `GMB_REQUIRED_FIELDS` currently gates on `phone/website_url/google_address`. Should `google_maps_url` be included? Currently excluded — presence varies by source.

## Next session must start here

1. Deploy to VPS: `ssh root@72.60.209.109 "cd /root/agentsHQ && git pull && docker compose up -d orchestrator"` — confirm gate is live in container.
2. Verify gate fires: `docker logs orc-crewai --tail 50` after next morning runner tick — look for `"[SW] T1 GMB gate: dropped N"` line.
3. If no morning runner today: run manually `python -m skills.outreach.sequence_engine --pipeline sw --dry-run` on VPS to confirm gate logic executes without error.
4. On 2026-05-28: run SW sequence audit — confirm no unqualified leads in active T1 sequence. Start Atlas #11 planning if baseline looks good.

## Files changed this session

```
skills/serper_skill/hunter_tool.py        (score_gmb_lead + constants added)
skills/outreach/sequence_engine.py        (T1 SW gate added)
skills/hormozi-lead-gen/references/
  cold-call-scripts.md                    (new file)
docs/roadmap/atlas.md                     (item #11, cheat block, session log)
docs/reviews/absorb-log.md               (verdict)
docs/reviews/absorb-followups.md         (follow-up + DONE mark)
```
