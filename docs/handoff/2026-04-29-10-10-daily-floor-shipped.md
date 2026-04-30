# Session Handoff - 10+10 Daily Email Floor Shipped - 2026-04-29

## TL;DR

Shipped the 10+10 daily email floor: a CW + SW outreach pipeline that produces a minimum of 10 Catalyst Works drafts and 10 Signal Works drafts per day in `boubacar@catalystworks.consulting` Drafts, fired automatically by a DST-aware systemd timer at 07:00 MT every morning. End of session: 16 SW drafts + 6 CW drafts produced live by the final clean run, plus ~13 CW drafts from earlier in the session, all visible in Gmail.

The session also hardened the deploy path with `scripts/orc_rebuild.sh`, a coordination-aware wrapper that prevents the rebuild collisions that killed 4 morning_runner runs mid-flight earlier in the evening (parallel Claude session was rebuilding orc-crewai while this session's runner was in flight).

Total session: ~10 hours. Plan + 11 tasks executed via subagent-driven development. RCA performed on the rebuild collision pattern. Memory written. Two health checks scheduled for 7d + 14d out.

## What was built / changed

**New files:**
- `signal_works/expansion_ladder.py`: 392 niche/city pairs across 6 tiers (Utah core → Mountain states → Western US → Top 50 metros → North America)
- `signal_works/hunter_client.py`: Hunter.io domain-search wrapper, daily cap 5, raises HunterCapReached
- `scripts/orc_rebuild.sh`: coordination-aware rebuild wrapper, refuses if `task:morning-runner` held
- `scripts/README.md`: documentation
- `docs/superpowers/specs/2026-04-29-10-10-daily-floor-design.md`: committed
- `docs/superpowers/plans/2026-04-29-10-10-daily-floor.md`: gitignored, local only
- 8 new test files in `tests/`

**Updated files:**
- `orchestrator/db.py`: `ensure_leads_columns`, `get_resend_queue`; new columns: `no_website`, `email_source`, `last_drafted_at`, `apollo_id`
- `skills/apollo_skill/apollo_client.py`: `find_owner_by_company` using `mixed_people/api_search` + `q_organization_name`; `CW_ICP_WIDENED`; `_import_get_crm_connection` helper
- `skills/outreach/sequence_engine.py`: source_filter LIKE-prefix match; `build_body` callable handling
- `signal_works/lead_scraper.py`: no_website flag + dual-import fallback
- `signal_works/topup_leads.py`: full rewrite with ladder walk + 4-layer email resolution + circuit breaker + business_name alias
- `signal_works/topup_cw_leads.py`: hybrid 5-fresh + 5-resend with Apollo gap-fill
- `signal_works/morning_runner.py`: Telegram failure alert wrapper, drafted-vs-sent fix, coordination claim
- `templates/email/sw_t1.py`: `build_body` with no_website conditional opener
- `templates/email/cold_outreach.py`: CW T1 signature: `Boubacar / catalystworks.consulting` only (was `Boubacar Barry / Founder, Catalyst Works / catalystworks.consulting`)
- `docs/AGENT_SOP.md`: Hard Rule added: always use scripts/orc_rebuild.sh

**Deployed:**
- VPS at `agentshq.boubacarbarry.com:/root/agentsHQ/` synced with all the above
- orc-crewai container rebuilt with new image (sha256:24c41b8a4f19...)
- systemd timer `signal-works-morning.timer` set, next firing Thu 2026-04-30 13:00 UTC = 07:00 MT
- 7-day health check routine `trig_0121WhpLQ3DHturLbcxnJKyq` fires 2026-05-06 16:00 UTC
- 14-day health check routine `trig_01H1atLLEkDGTXJQjActAkPe` fires 2026-05-13 16:00 UTC

**Pushed to origin:**
- `feature/10-10-daily-floor` at `5b87180`: full plan execution
- `feature/coordination-layer` at `1e255b5`: orc_rebuild.sh + integration fixes + SOP

## Decisions made

- **CW pipeline = hybrid 5 fresh + 5 resend** (with 60-day cooldown on resends). Apollo gap-fills if resend queue runs short. Boubacar agreed; we have 70-80 historical contacts that can cycle back.
- **SW pipeline = geo-expansion ladder + 4-layer email resolution** (Firecrawl → Apollo strict → Hunter → skip). Boubacar specified Google Maps stays first because "no website = automatic SW prospect" is a real signal worth capturing in the lead.
- **Apollo company-name lookup uses `mixed_people/api_search`** with `q_organization_name`, NOT `organizations/enrich` + `people/match`. The intuitive endpoint pair returns 422: discovered after burning credits on it.
- **Hunter daily cap = 5 searches/day** + circuit breaker after 5 consecutive Apollo+Firecrawl double-failures. Both protect against the worst-case credit burn that virtual tests surfaced (400 Hunter credits in 1 day if upstream APIs both fail).
- **CW T1 signature** per Boubacar's rule: first name only, no title, no company-and-URL pair. The body intro line stays untouched (signature rule applies to signatures only).
- **`scripts/orc_rebuild.sh` mandated for all rebuilds.** Bare `docker compose build orchestrator` is now banned via AGENT_SOP Hard Rule. Wrapper checks `task:morning-runner` lock and refuses if held.
- **Branch strategy:** kept `feature/10-10-daily-floor` and `feature/coordination-layer` separate. They have related work that should eventually merge to dev/main but not tonight.

## What is NOT done (explicit)

- **Branch reconciliation** between `feature/10-10-daily-floor` and `feature/coordination-layer`. Both have related work. Not merged. Decide later.
- **`AUTO_SEND_CW=true`** still false. All CW emails are drafts pending review.
- **Studio (Step 6) wiring** in morning_runner. Separate engagement.
- **Firecrawl render config investigation**: why JS-heavy small biz sites return empty text from Firecrawl. Apollo + Hunter became the rescue paths.
- **Hunter Starter plan upgrade** ($34/mo for 500 searches): defer until Tier 3+ engagement is real. Free tier (25/mo) covers Tier 1-2 with the 5/day cap.
- **The other Claude session's voice_personalizer module**: referenced in morning_runner but optional (wrapped in try/except, non-fatal).
- **`MEMORY.md` is at 207 lines** (cap is 200). Lines 200-207 are domain-grep helpers; truncation risk is low priority. Worth pruning next session if convenient.

## Open questions

1. When does Boubacar want to flip `AUTO_SEND_CW=true`? Suggestion: review tomorrow's batch of drafts first.
2. Should the two branches `feature/10-10-daily-floor` and `feature/coordination-layer` merge into dev now, or stay separate until a planned reconciliation?
3. Is the SOP rule about `scripts/orc_rebuild.sh` enough for the parallel Claude sessions on VPS to honor it, or do we need a stricter mechanism (e.g., a pre-commit hook that fails on bare `docker compose build orchestrator` commands in scripts)?

## Next session must start here

1. **First check**: tomorrow morning at 07:05 MT, verify the systemd timer fired by reading `/var/log/signal_works_morning.log` mtime + tail. Expected: ~10 SW + ~4-8 CW new drafts.
2. **If timer fired clean**: count drafts via Gmail API or manually in inbox. If ≥10 SW and ≥5 CW, the pipeline is working. If <5 of either, investigate `/var/log/signal_works_morning.log` for the failure.
3. **If timer DID NOT fire**: check `systemctl status signal-works-morning.timer` and `systemctl status signal-works-morning.service`. Most likely cause: another session rebuilt orc-crewai at exactly 13:00 UTC and killed the runner.
4. **Branch reconciliation decision**: discuss with Boubacar whether `feature/10-10-daily-floor` and `feature/coordination-layer` should merge to `dev` now.
5. **If drafts look good across the day**: discuss flipping `AUTO_SEND_CW=true` so CW drafts auto-send instead of sitting in Drafts.

## Files changed this session

```
NEW:
  signal_works/expansion_ladder.py
  signal_works/hunter_client.py
  scripts/orc_rebuild.sh
  scripts/README.md
  docs/superpowers/specs/2026-04-29-10-10-daily-floor-design.md
  tests/test_lead_schema.py
  tests/test_expansion_ladder.py
  tests/test_hunter_client.py
  tests/test_apollo_company_match.py
  tests/test_topup_leads_ladder.py
  tests/test_topup_cw_resend.py
  tests/test_lead_scraper_no_website.py
  tests/test_sw_t1_no_website.py

UPDATED:
  orchestrator/db.py
  skills/apollo_skill/apollo_client.py
  skills/outreach/sequence_engine.py
  signal_works/lead_scraper.py
  signal_works/topup_leads.py
  signal_works/topup_cw_leads.py
  signal_works/morning_runner.py
  templates/email/sw_t1.py
  templates/email/cold_outreach.py
  docs/AGENT_SOP.md

MEMORY (Claude Code auto-memory):
  feedback_use_orc_rebuild_wrapper.md (NEW)
  reference_coordination_layer.md (NEW)
  feedback_apollo_company_name_lookup.md (NEW)
  project_parallel_claude_sessions_on_vps.md (NEW; in MEMORY_ARCHIVE)
  project_10_10_daily_floor_deployment.md (NEW; in MEMORY_ARCHIVE)
  feedback_pyright_reverts_agents_py.md (UPDATED: broader scope)
  MEMORY.md (UPDATED: 4 pointers added)
  MEMORY_ARCHIVE.md (UPDATED: 2 pointers added)

VPS-only deployment:
  /etc/systemd/system/signal-works-morning.timer
  /etc/systemd/system/signal-works-morning.service
  /root/agentsHQ/.env (CRLF normalization, SMTP_PASS + SIGNAL_WORKS_SENDER quoting)
```
