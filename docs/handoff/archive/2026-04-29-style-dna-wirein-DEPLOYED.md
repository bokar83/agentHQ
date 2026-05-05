# Handoff: Style DNA Wire-in DEPLOYED to production (2026-04-29)

**Status update:** Supersedes `2026-04-29-style-dna-wirein-holding.md`. Path A is no longer holding: it shipped to main, deployed to VPS, smoke-tested live, and tomorrow's 07:00 MT systemd run will be the first scheduled fire.

## What's running tomorrow

VPS systemd timer fires `morning_runner.py` at 07:00 MT. Sequence:

1. STEP 1: Bounce scan
2. STEP 2: SW topup (BROKEN, see below)
3. STEP 3: SW T1-T4 sequence (drafts)
4. STEP 4: CW Apollo topup (working)
5. STEP 4.5: voice personalize today's CW leads (NEW, working)
6. STEP 5: CW T1-T4 sequence (drafts; auto-send is OFF)

Both pipelines: AUTO_SEND_CW=false and AUTO_SEND_SW=false in container env. Confirmed via `docker exec orc-crewai env | grep AUTO_SEND`. So all touches are drafts; nothing auto-sends. Boubacar reviews 07:30-08:00 MT.

## Verified live in production

- Container imports clean: `voice_personalizer`, `lead_scraper`, `bs4`, `skills.coordination` all import.
- `personalize_pending_leads(limit=1)` produced 1 NEW lead live: Wade Millward @ rikor.io. Opener: "Wade, if your subcontractor insurance compliance feels like a full-time job, there is a simpler way to get it done right." Voice in his domain, named him, found a real angle.
- DB has 4 leads with `voice_personalization_line` populated total (3 from local smoke test + 1 from prod).

## What broke during deploy and got fixed

5 separate bugs surfaced during the smoke test on VPS, all fixed and pushed to main:

1. `signal_works/lead_scraper.py:12`: `from orchestrator.db import upsert_signal_works_lead` failed in container because Dockerfile flattens `orchestrator/*` to `/app`. Fixed with try/except fallback. Commit `15a3ad1`.
2. `skills/transcript-style-dna/extract.py:25`: same root cause, `from orchestrator.llm_helpers`. Commit `9f2c322`.
3. `orchestrator/llm_helpers.py:24`: `float(os.environ.get("CHAT_TEMPERATURE", "0.7"))` crashed because the var was set-to-empty (default only applies on unset). Fixed with `or` fallback. Commit `d55996a`.
4. `signal_works/voice_personalizer.py:126`: same flattened-container issue, my own code. Commit `d1fd280`.
5. Defensive: hardened `signal_works/send_drafts.py` and `skills/inbound_lead/researcher.py` proactively (not in tomorrow's hot path but adjacent surfaces). Commit `81aec2f`.

5 more files have unguarded `from orchestrator.X` imports but are scoped to one-shot migrations or non-production paths. Logged in `feedback_flattened_container_imports.md` for future hardening when those code paths get touched.

## CRITICAL FINDING: SW topup is broken in production

During Phase 3 verification (Council Expansionist asked "is SW unblocked too?"), found that SW topup hits a different bug:

```
File "/app/signal_works/topup_leads.py", line 80, in _resolve_email
    apollo = find_owner_by_company(business["business_name"], business.get("city", ""))
KeyError: 'business_name'
```

This is on parallel-session code (commit `14e6a55 feat(sw): rewrite topup with ladder walk + 4-layer email resolution`). NOT mine to fix; the parallel session is actively iterating on this code (most recent commit `184df30 fix(sw): decouple circuit breaker alert from Hunter cap state`).

**Implication for R1 (first contract by 2026-05-02):** the SW funnel has been silently broken since this code shipped. SW T1-T4 sequence is firing on whatever leads exist in DB, but no NEW leads are being added by the morning topup. This bleeds R1 directly. Surfacing here so the parallel session sees it.

## Memory + handoff index (where to find context)

- `project_style_dna_wirein_state.md`: full deployment outcome
- `feedback_flattened_container_imports.md`: the import-class lesson
- `feedback_diff_aware_hook_pattern.md`: the hook lesson from earlier today
- `reference_firecrawl_pricing_2026.md`: why we swapped to BS4
- `project_channel_style_dna_audit.md`: the original Sankofa decision
- `docs/roadmap/harvest.md`: R7 milestone with full eval procedure
- Calendar: 2026-06-01 09:00 MT lift-test verdict (Google Calendar, color tomato)

## Tomorrow morning routine

1. ~07:30 MT: SSH to VPS, `tail logs/signal_works_morning.log` for the run summary
2. Query DB: count `voice_personalization_line IS NOT NULL` since now
3. Spot-check 2-3 openers in the CW drafts folder
4. If openers look generic or weird, that's a "skill confidence is low for this prospect" signal, NOT a bug. Note for the lift-test eval.
5. If the SW topup bug above is resolved by the parallel session, SW pipeline reactivates
6. Decide: flip AUTO_SEND_CW=true (if drafts are good for tomorrow's batch) or hold another day

## Next-after-A bite (post-lift-test)

When R7 fires KEEP on 2026-06-01: wire transcript-style-dna into Catalyst Works pre-discovery prep (R3 territory). ~30 min. Spec already in `skills/transcript-style-dna/SKILL.md` under "Catalyst Works (engagement-ops)."
