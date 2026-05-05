# Session Handoff - SW Pipeline Rebuild + Studio Merge - 2026-05-05

## TL;DR

Daily report showed 12 emails instead of target 50. Diagnosed 11 distinct failure modes spanning docker (stale container), hunter (quota exhausted, narrow filter), apollo (no SMB coverage), circuit breaker (5-miss threshold), ICP (Utah-only), Studio/SW pipeline duplication. Shipped 15 commits across the day. Boubacar upgraded Hunter to Starter ($49/mo). Manual run hit 34/35 SW saves in 12 minutes after fixes. Studio outreach merged into SW conceptually (one offer, full US, 1-50 EE). Pipeline metrics + Apollo daily budget instrumentation shipped. SW_ICP expansion shipped but morning_runner Steps 4b/6 still firing -- next session task.

## What was built / changed

**Docker / deploy:**
- `docker-compose.yml` -- volume-mount code dirs (signal_works, skills, templates, orchestrator) -- code changes deploy in 10 sec, no rebuild
- `scripts/session_start_audit.sh` (NEW) -- read-only audit fired by SessionStart hook
- `.gitignore` -- root PNG/HTML scratch patterns
- `.git/hooks/pre-commit` + `scripts/pre-commit-hook.sh` -- check #6 docker doc-drift guard
- `docs/AGENT_SOP.md` -- two old container-deploy rules replaced

**Hunter / Apollo / SW:**
- `signal_works/hunter_client.py` -- cap 5 -> 200, 3-tier seniority fallback (owner -> manager -> any), confidence >= 50
- `signal_works/topup_leads.py` -- circuit breaker 5 -> 50, Hunter domain extract from website when Apollo None
- `signal_works/topup_studio_leads.py` -- /app sys.path fallback for Docker
- `skills/serper_skill/hunter_tool.py` -- confidence 70 -> 50, Apollo fallback in Step 5 (was disabled)
- `skills/apollo_skill/apollo_client.py` -- find_owner_by_company filter loosened (likely_to_engage), SW_ICP expanded to full US 1-50 EE, log credits to apollo_credits, apollo_check_budget guard
- `orchestrator/db.py` -- get_resend_queue revealed_at column fix
- `orchestrator/agents.py` + `orchestrator/crews.py` + `orchestrator/tools.py` -- Hunter agent crew uses Apollo as primary (harvest_apollo_leads tool), discover_leads as fallback

**Metrics + observability:**
- `signal_works/pipeline_metrics.py` (NEW) -- log_step, log_apollo_credits, apollo_check_budget. pipeline_metrics + apollo_credits tables auto-create.
- `signal_works/morning_runner.py` -- log_step calls in Steps 1, 2, 3, 4, 4b, 4.5, 5, 5b, 6. Harvest health check (Telegram alert when SW < 30 or CW < 10). Apollo credits used today summary at end.
- `orchestrator/notifier.py` -- boubacar@catalystworks.consulting added to daily report recipients

**Reserve Works (separate scope):**
- `agents/reserve_works/` (NEW) -- staged research agent, RW_ENABLED=false default
- `reports/reserve_works/` (NEW) -- 14 docs decision package (Sankofa council + capital plan)

**Hygiene:**
- `zzzArchive/sw-997-iterations-2026-05-05/` -- 20 root PNGs archived from $997 page work + GeoListed iterations

## Decisions made

1. **SW absorbs Studio outreach.** Same offer ($997 build + $497/mo). Full US, industry-agnostic, 1-50 EE. T1 routes by has_website: audit (sw_t1) vs build (formerly studio_t1). Studio codename now = faceless YouTube agency only.
2. **EE range = 1,50 (was 1,30).** Step up to 1,200 only if pool exhausts. Sub-50 = best email-find rate + best conversion.
3. **Hunter Starter REQUIRED.** Free 50/mo cap kills SW pipeline. ~$49/mo is non-negotiable for the offer to ship daily.
4. **Apollo daily budget = 500 credits/day default** (env override `APOLLO_DAILY_BUDGET`). `apollo_check_budget` aborts mid-run if would exceed.
5. **Volume-mount over rebuild.** Code changes deploy in 10 sec. Rebuild ONLY for requirements.txt changes.
6. **Pipeline metrics over log-tailing.** Per-step logged to `pipeline_metrics` table. Future "why did CW only produce 7?" answered via SQL not grep.

## What is NOT done (explicit)

- **morning_runner Step 4b (Studio harvest) + Step 6 (Studio sequence) STILL FIRE.** SW_ICP merge is half-done. Need to drop these steps next session.
- **send_scheduler.DAILY_CAPS still has Studio=15.** SW=35 needs to become 50, Studio=0 (or removed key).
- **SW T1 router (has_website -> audit vs build template) NOT IMPLEMENTED.** Currently only audit template fires.
- **CW thin_text fallback NOT shipped.** Voice personalizer drops 50% of CW leads silently. Boubacar said "instrument first" -- now that pipeline_metrics is live, we can measure it but the fallback (template-only when personalization fails) isn't coded.
- **AUTO_SEND still OFF for SW + CW + Studio.** Drafts only. Per Boubacar's "watch 3 days" direction.
- **Reply rate measurement loop not built.** Hormozi ramp 50 -> 100 has no trigger. User said "I'll tell you on first reply."
- **The 19:53 manual run was killed mid-execution.** Lock cleared. The 20:24 run completed and produced ~34 SW saves but the watcher background process was killed before logging the final TOTAL line -- check VPS log for actual final count.

## Open questions

- Does the existing SessionStart audit hook fire correctly on next session start? (Wired today, untested.)
- Does Apollo daily budget guard trip cleanly at 500 credits? (Code reviewed, untested in production run.)
- Will tomorrow's 13:00 UTC scheduled morning_runner pick up new code (volume mount) and produce 35+ SW + 15 CW = 50 drafts as expected? (High confidence, validation tomorrow.)
- Is `topup_studio_leads.py` safe to remove now or wait until SW T1 router is built? (Wait -- still imported by morning_runner Step 4b.)

## Next session must start here

1. **Verify tomorrow's 13:00 UTC run.** SSH `tail -200 /var/log/signal_works_morning.log` -- expect 35+ SW saves, 10+ CW, total drafts 50+.
2. **Query pipeline_metrics for first time:** `docker exec orc-postgres psql -U postgres -d agentshq -c "SELECT * FROM pipeline_metrics WHERE run_date = CURRENT_DATE;"` -- this is the new instrumentation, first real data.
3. **Check Apollo credits used:** same query against `apollo_credits` table.
4. **If results good, drop Studio steps from morning_runner.** Edit signal_works/morning_runner.py: remove Step 4b, Step 6, related logger lines. Edit signal_works/send_scheduler.py: DAILY_CAPS sw=50, drop studio key.
5. **Build SW T1 router:** in skills/outreach/sequence_engine.py, when pipeline=='sw', check `lead.has_website`. If True -> sw_t1 audit template. If False -> use former studio_t1 (rename to sw_t1_nosite.py).
6. **Tab-shutdown next time.**

## Files changed this session

```
# Today's commits (15 total):
4e2d081  feat(notifier): boubacar@catalystworks.consulting in daily report
361ec95  fix: topup_studio /app path + db.py revealed_at
d7cddfb  fix(docker): volume-mount code dirs
42c5cbf  docs: code dirs volume-mounted
4d674f2  chore: SW $997 spec + handoff + hunter SKILL.md docker fix
1732500  chore(infra): 4 hygiene rails (gitignore, session audit, doc-drift hook)
e86aa3b  fix(hunter): loosen email filters
dc44792  feat(hunter): Apollo as primary, discover_leads as fallback
2343c06  fix(sw): unblock Hunter.io fallback for trades-SMBs
0e518b5  fix(sw): Hunter cap 5 -> 200 + 3-tier seniority filter
66c2bf9  feat(sw): merge Studio into SW -- full US, 1-50 EE
f28dcfd  feat(morning_runner): harvest health check
443c1ef  feat(metrics+budget): pipeline metrics + Apollo daily budget
adbb27e  feat(reserve_works): RW research agent v1 staged
76c0c85  docs(reserve_works): decision package
```

All deployed via volume mount on VPS. No rebuild required.
