# Session Handoff — CW Strip Shipped + Lead Strategy Review Queued — 2026-05-12

## TL;DR

Boubacar invoked /council on the question of whether to cancel Apollo + Hunter subscriptions and pivot away from auto-harvest for Catalyst Works. Sankofa Council ran 4-scenario premortem. Verdict: strip CW automation, cancel Apollo, keep Hunter for SW. Boubacar cancelled Apollo (plan ends 2026-05-28). Stripped CW Steps 4/4.5/5/5b from `signal_works/morning_runner.py`, pushed `[READY]` for Gate. Added `mode="premortem"` to the Sankofa Council Python engine + skill docs. Two X-sourced lead-gen links queued for absorb in next session as part of the lead-strategy review (moved up from Wed to tonight, in a separate tab).

## What was built / changed

**Code shipped (both pushed `[READY]` for Gate):**

- `feat/strip-cw-automation` (commit `53b25f1`):
  - `signal_works/morning_runner.py` — Steps 4 / 4.5 / 5 / 5b removed (CW Apollo topup, voice personalize, T1-T5 auto-send, recycle). Health-check threshold SW-only. Header doc updated.
  - `docs/handoff/2026-05-12-cw-strip-rationale.md` — full rationale + rollback plan + Apollo Free-tier risk callout for SW chain post-2026-05-28.

- `feat/council-premortem-mode` (commit `a102698`):
  - `orchestrator/council.py` — `SankofaCouncil.run(mode="standard"|"premortem")` kwarg + auto-detect on "premortem this" phrase. Per-voice retrospective mandates injected when premortem. Default behavior preserved.
  - `skills/council/council.md` — invoke doc + full PREMORTEM MODE section mirroring Sankofa.
  - `skills/council/SKILL.md` — description updated.
  - Mirrored to `C:\Users\HUAWEI\.claude\skills\council\` (canon).

**Docs / roadmap:**

- `docs/roadmap/harvest.md` — added H1j (Lead-strategy review). Session log entry for 2026-05-12.
- Memory: `C:\Users\HUAWEI\.claude\projects\d--Ai-Sandbox-agentsHQ\memory\project_cw_automation_stripped_2026-05-12.md` + MEMORY.md pointer.

## Decisions made

1. **Cancel Apollo subscription.** Boubacar already did this in the Apollo UI — plan ends 2026-05-28, auto-switches to Free tier after.
2. **Keep Hunter Starter ($49/mo).** SW-load-bearing per `feedback_hunter_apollo_paid_required.md`. Today's "zero email morning run" proved SW dies one Hunter wobble away. Re-evaluate after current post-fix pull yield is logged.
3. **NO paid-leads pivot.** Every B2B vendor pulls from same Apollo/ZoomInfo SMB index. CW Apollo already at 97.6% email coverage. Sourcing wasn't the failure. Recognition was.
4. **CW = manual only.** New CW prospects enter `data/cw_target_list.csv` ONLY if they pass the permission filter (already know who Boubacar is). Cold-scrape sources do NOT qualify.
5. **CW T2-T5 in-flight cadence preserved.** Stripping morning_runner does not kill `sequence_engine` cron — existing CW leads keep advancing through follow-ups.
6. **Premortem mode added to Council** so future high-stakes decisions can be reviewed from 6-months-future retrospective lens (mirrors Sankofa DEAD-PROJECT MODE).

## What is NOT done (explicit)

- **Lead-strategy review itself.** Originally scheduled Wed 2026-05-13. Boubacar moved it up — wants it run NOW in a separate session. Prompt posted at end of this handoff. Includes absorb of 2 X-sourced lead-gen links.
- **Apollo Free-tier behavior in SW chain.** `topup_leads.py:35` still imports `apollo_client.find_owner_by_company`. After 2026-05-28 either verify graceful Free-tier degradation OR strip Apollo from SW chain. Memory already says Apollo = dead weight on trades (663:1 miss).
- **Prospeo `INVALID_DATAPOINTS` ticket.** Silently poisoning SW per Council. Not opened yet — needs separate session.
- **Hunter post-fix pull yield logged.** New pull running this evening. Yield numbers feed Hunter keep/downgrade decision later this week.
- **Inbound-signal metric baseline.** Weekly count of unsolicited DMs + non-network engagement. Not yet stood up. Wed/Thu session.
- **CSV scaffold `data/cw_target_list.csv`.** Not created. Lead-strategy review will define schema + seed.
- **10-names question** — Boubacar has not answered in writing yet. Lead-strategy review prompts for it.

## Open questions

- Apollo Free-tier — does `find_owner_by_company` org-only call still work, or hit auth/rate limit?
- Should `topup_cw_leads.py` module be deleted from repo or kept for future manual CW push? (Currently retained.)
- Inbound-signal metric storage — Notion DB vs markdown log vs Supabase table?
- Content cadence — what's the realistic weekly publish target now that CW Hour is reclaimed (was being eaten by morning_runner triage)?

## Next session must start here

**Boubacar opens a separate tab and runs the prompt at the bottom of this file.** That session does NOT continue this work — it runs the H1j lead-strategy review independently with fresh head + absorbs the 2 X-sourced links.

This session is closing. After Boubacar pastes the prompt and confirms the new tab is moving:

1. Watch this evening's Hunter post-fix pull. Log yield to a memory entry by morning.
2. Confirm Gate merged both `[READY]` branches (`feat/strip-cw-automation` + `feat/council-premortem-mode`).
3. Verify VPS has the strip live: `ssh root@72.60.209.109 "cd /root/agentsHQ && git pull && grep -n 'CW automation REMOVED' /root/agentsHQ/signal_works/morning_runner.py"`.

## Files changed this session

```
signal_works/morning_runner.py
orchestrator/council.py
skills/council/SKILL.md
skills/council/council.md
docs/handoff/2026-05-12-cw-strip-rationale.md (new)
docs/handoff/2026-05-12-cw-strip-shipped-lead-strategy-queued.md (this file)
docs/roadmap/harvest.md
~/.claude/skills/council/SKILL.md (canon mirror)
~/.claude/skills/council/council.md (canon mirror)
~/.claude/projects/d--Ai-Sandbox-agentsHQ/memory/project_cw_automation_stripped_2026-05-12.md (new)
~/.claude/projects/d--Ai-Sandbox-agentsHQ/memory/MEMORY.md (pointer added)
```
