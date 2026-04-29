# Handoff: Style DNA Wire-in HOLDING for Coordinated Deploy (2026-04-29)

**State:** Path A wire-in code shipped + tested green + pushed to origin. NOT deployed to VPS. Holding for "continue" signal from Boubacar to merge alongside parallel-session work.

## What's done

`feature/style-dna-wirein` at tip `16ac664` on origin (https://github.com/bokar83/agentHQ/tree/feature/style-dna-wirein), 14 commits today. Smoke-tested live on 3 real CW leads (Adam Ingersoll @ Shasta Dental, Ben Teerlink @ MMI, Galen Murdock @ ShareMy.Health): all produced personalized openers in voice, written to local CRM Postgres.

26/26 unit tests green:

- `tests/test_lead_scraper_fetch.py` (6): BS4 scraping
- `tests/test_voice_personalizer.py` (7): extract pipeline + derive-website branch
- `tests/test_email_builder_opening.py` (6): short-circuit + scrub
- `tests/test_find_company_website.py` (7): Serper company-name lookup

Decisions baked in:

1. Firecrawl free tier exhausted, swapped `fetch_site_text` to plain `requests` + BeautifulSoup. `beautifulsoup4>=4.12.0` added to `orchestrator/requirements.txt`. Re-evaluate Hobby plan ($16-20/mo) at lift-test verdict on 2026-06-01.
2. Apollo CW leads have no `website_url`. New helper `find_company_website(company, city)` does a Serper search, skips known aggregators, returns plausible company URL. Smoke-tested: 3/3 sites correctly identified.
3. scan_line in voice short-circuit was injecting lead name (read as AI slop for person-named CW leads). De-personalized to generic phrasing.
4. Em-dash hook (`scripts/check_no_em_dashes.py`) is now diff-aware. Default scans only lines added in the staged diff. `--full` flag preserved for ad-hoc cleanup. Council-driven decision (Karpathy + Sankofa unanimous).
5. R7 milestone in `docs/roadmap/harvest.md` with full eval procedure for 2026-06-01. Calendar event also created.
6. Path B (channel-branding-kit, M3.5 sub-skill #3) preserved in plan as "Deferred, do not execute" per Sankofa.

## Why holding

Three feature branches were active in parallel today, all touching `morning_runner.py`, `lead_scraper.py`, or `email_builder.py`:

- `feature/style-dna-wirein` (mine, this branch)
- `feature/10-10-daily-floor` (parallel session: SW topup ladder walk, Hunter.io, Apollo CW_ICP_WIDENED, no_website tagging, hybrid 5-fresh+5-resend)
- `feature/coordination-layer` (parallel session: skills.coordination claim/complete, agent collision tests)

Boubacar chose to wait for parallel sessions to finish, then merge all branches in one deliberate review pass with conflict resolution, then a single VPS deploy. Avoids N separate VPS rebuilds and surfaces conflicts in one place rather than during a deploy emergency.

## What does NOT break by waiting

- VPS systemd timer fires `morning_runner.py` at 07:00 MT. Until VPS pulls new code, it runs the OLD pipeline (no Step 4.5, no voice personalization). Same as today. Zero behavior change. Zero risk.
- Lift-test clock loses one day (~3% of the 30-day window). Statistically irrelevant.
- All branches pushed; no work at risk.

## Resume instructions (when "continue" signal arrives)

1. `git fetch --all` and list open feature branches with unmerged commits relative to main:
   ```bash
   for b in $(git branch -r | grep "feature/" | grep -v HEAD); do
     n=$(git log --oneline main..$b | wc -l)
     [ "$n" -gt 0 ] && echo "$b: $n commits"
   done
   ```
2. **Conflict-shape pre-check** (do this BEFORE any merge):
   ```bash
   git diff "main...feature/style-dna-wirein" signal_works/morning_runner.py signal_works/lead_scraper.py signal_works/email_builder.py
   git diff "main...feature/10-10-daily-floor" signal_works/morning_runner.py signal_works/lead_scraper.py signal_works/email_builder.py
   git diff "main...feature/coordination-layer" signal_works/morning_runner.py
   ```
   Specifically check:
   - **morning_runner.py:** does `feature/coordination-layer`'s `claim/complete` wrap `_main_body()` such that my Step 4.5 lives correctly inside the wrapped body? It should: the collision-control commit refactored `main()` into `main()` + `_main_body()` and Step 4.5 is in `_main_body()`. But verify before merge.
   - **lead_scraper.py:** does `feature/10-10-daily-floor` define its own `find_company_website`? If yes, the two implementations need to be reconciled. The smoke-tested-on-real-leads version is mine on style-dna-wirein commit `7963fa1`.
   - **email_builder.py:** my voice short-circuit at line 253-272. Parallel branches likely did not touch this region (they were focused on subject lines and the no-website branches). Should merge clean.
3. Pick a merge order. Recommendation:
   - `feature/coordination-layer` first (provides infrastructure that style-dna-wirein already depends on: its commit `728ad76` is on style-dna-wirein already as an ancestor).
   - `feature/style-dna-wirein` second (most thoroughly smoke-tested today).
   - `feature/10-10-daily-floor` third (its own scope, builds on style-dna-wirein anyway).
4. After merge to main:
   ```bash
   ssh root@agentshq.boubacarbarry.com "cd /root/agentsHQ && git pull && docker compose up -d --build orchestrator"
   ```
   Per `feedback_container_deploy_protocol_v2.md`. Rebuild required (not docker-cp) because the new code includes a new dependency (`beautifulsoup4`) that needs `pip install` during image build.
5. Verify deploy:
   ```bash
   ssh root@agentshq.boubacarbarry.com "docker exec orc-crewai python -c 'from signal_works.voice_personalizer import _personalize_one; print(\"ok\")'"
   ```
   Expected: `ok` (confirms BS4 import + module load + correct sys.path).
6. Optional: spot-check that tomorrow morning's CW leads will get personalized:
   ```bash
   ssh root@agentshq.boubacarbarry.com "docker exec orc-crewai python -c 'from signal_works.voice_personalizer import personalize_pending_leads; print(personalize_pending_leads(limit=1))'"
   ```
   This actually fires Serper + scrape + LLM extract on one lead. Small cost, high confidence the live pipeline works.

## Reference

- Plan (gitignored, local only): `docs/superpowers/plans/2026-04-29-style-dna-wirein-and-channel-branding-kit.md`
- Memory: `project_style_dna_wirein_state.md`, `project_channel_style_dna_audit.md`, `reference_firecrawl_pricing_2026.md`, `feedback_diff_aware_hook_pattern.md`
- Roadmap: R7 in `docs/roadmap/harvest.md`
- Calendar: 2026-06-01 09:00 MT lift-test eval (Google Calendar, color tomato)
- Skill spec: `skills/transcript-style-dna/SKILL.md` (single-criterion success measure)
