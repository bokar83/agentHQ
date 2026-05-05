# Session Handoff - Studio + CW Outreach Pipeline Full Build - 2026-05-04

## TL;DR

Massive outreach expansion session. Went from 0 Studio emails to a fully wired pipeline (harvest + score + sequence + 4 templates). Fixed the SW T1 niche bug that was sending "best small business in Seattle" to real prospects. Fixed Calendly 404. All deployed and verified on VPS. First full Studio run fires tomorrow 07:00 MT.

## What was built / changed

- `skills/apollo_skill/apollo_client.py` : STUDIO_ICP expanded to full US+Canada (50+ cities, all industries, 1-1000 employees); STUDIO_ICP_TARGETED added (trades/solo pros: roofers, barbers, photographers, wedding planners, architects, etc.); CW_ICP_WIDENED expanded to full US; email filter loosened to verified+likely_to_engage; web scorer hook pre-reveal for Studio
- `signal_works/studio_web_scorer.py` : NEW. Scores website quality before spending Apollo credits. +3 no site, +2 broken/builder, +1 slow/old/no-contact, -1 schema.org. `filter_studio_candidates()` sorts highest-need first.
- `signal_works/topup_studio_leads.py` : DAILY_MINIMUM 10→25, max_pages 5→15, dual ICP daily alternation with gap-fill fallback
- `signal_works/topup_cw_leads.py` : DAILY_MINIMUM 10→20, max_pages 6→12
- `signal_works/morning_runner.py` : Step 4b (Studio harvest min=25), Step 6 (Studio sequence limit=15), studio_drafted in total, CW target 20
- `skills/outreach/sequence_engine.py` : TOUCH_DAYS_STUDIO {1:0,2:5,3:11,4:18}, TEMPLATES['studio'] t1-t4, source_filter apollo_studio%, AUTO_SEND_STUDIO, `_subject(lead)` hook for niche-aware subjects
- `templates/email/studio_t1.py` : NEW. AI search angle. `_subject(lead)` niche-aware (trades="Can customers find X online?", pros=AI angle). `_TRADES` set.
- `templates/email/studio_t2.py` : NEW. Free website audit value-add.
- `templates/email/studio_t3.py` : NEW. Pricing + Calendly CTA (boubacarbarry/signal-works-discovery-call)
- `templates/email/studio_t4.py` : NEW. Break-up + referral ask + Calendly
- `templates/email/sw_t1.py` : niche bug fixed. `_resolve_niche()` maps Apollo `industry`→human label. `_INDUSTRY_TO_NICHE` dict (30 mappings). Generic hook when niche=None. `{niche_or_type}` in no-website hook.

## Decisions made

- Studio ICP = any business needing web presence. No niche ceiling. Geography = full US+Canada. Volume play.
- Auto-send stays OFF for all pipelines. Boubacar reviews tomorrow's run (2026-05-05) first. CW ready to flip after review.
- Calendly URL = `calendly.com/boubacarbarry/signal-works-discovery-call`. Never `catalystworks` (404).
- Linter revert fix = permanent: always write files via `python <<'PYEOF'` + `git add` + `git commit` in one Bash chain. Edit tool banned for committed files.
- SW T1 niche bug: use `_resolve_niche()` everywhere, never raw `lead.get("niche","small business")`.
- The 10 broken SW drafts that fired this morning : Boubacar manually fixed and sent them. Do NOT resend or delete.

## What is NOT done (explicit)

- Auto-send switches not flipped (intentional : waiting for tomorrow's run review)
- Studio M4 publish pipeline not started
- Website teardown skill : started by separate agent (feature/website-teardown)
- SaaS audit PDF upsell : started by separate agent (feature/saas-audit-upsell)
- Studio M3 render verification : tracked by separate agent

## Open questions

- Tomorrow's run: does Studio harvest actually find 25 leads? Apollo pool may be thin on first pass with new ICP.
- CW auto-send: flip after reviewing tomorrow's 10 CW drafts.
- Studio sequence will produce 0 emails tomorrow (no apollo_studio leads in DB yet : first harvest happens tomorrow). First Studio emails fire on Day 1 after.

## Next session must start here

1. Check VPS log after 13:00 UTC tomorrow: `ssh root@72.60.209.109 "tail -100 /var/log/signal_works_morning.log"`
2. Verify Studio harvest found leads: look for "STEP 4b" and "Studio topup complete: N leads"
3. Check Drafts folder for SW + CW emails : confirm niche is rendering correctly (should see real niche labels like "roofer", "landscaper", not "small business")
4. If CW drafts look good → flip `AUTO_SEND_CW=true` in VPS .env → run `bash scripts/orc_rebuild.sh`
5. Check if website-teardown (feature/website-teardown) and saas-audit (feature/saas-audit-upsell) branches have [READY] commits ready for gate

## Files changed this session

```
skills/apollo_skill/apollo_client.py       (STUDIO_ICP full US, STUDIO_ICP_TARGETED, web scorer hook)
signal_works/studio_web_scorer.py          (NEW)
signal_works/topup_studio_leads.py         (min=25, max_pages=15, dual ICP)
signal_works/topup_cw_leads.py             (min=20, max_pages=12)
signal_works/morning_runner.py             (Step 4b + Step 6 + studio_drafted)
skills/outreach/sequence_engine.py         (Studio pipeline full wiring)
templates/email/studio_t1.py               (NEW)
templates/email/studio_t2.py               (NEW)
templates/email/studio_t3.py               (NEW + Calendly fix)
templates/email/studio_t4.py               (NEW + Calendly fix)
templates/email/sw_t1.py                   (niche bug fix)
```
