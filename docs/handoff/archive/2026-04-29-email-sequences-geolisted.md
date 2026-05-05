# Session Handoff - Email Sequences + GeoListed Site - 2026-04-29

## TL;DR

Marathon session. Built the full CW + SW 4/5-touch email sequence engine from scratch, launched the Signal Works landing page at geolisted.co, registered the domain, created the GitHub repo, wired everything into the morning runner, killed all legacy one-shot email senders, and verified the full pipeline dry-runs clean on both local and VPS.

---

## What was built / changed

### Email Sequence Engine
- `skills/outreach/sequence_engine.py` - NEW. Single source of truth for all outreach. CW 5-touch (Day 0/6/9/14/19), SW 4-touch (Day 0/3/7/12). Draft-only by default. AUTO_SEND_CW / AUTO_SEND_SW env flags control live send. 10/day limit per pipeline.
- `templates/email/sw_t1.py` through `sw_t4.py` - SW sequence templates. Signature: geolisted.co
- `templates/email/cw_t2.py` through `cw_t5.py` - CW T2-T5 (T1 = existing cold_outreach.py). T2 = SaaS PDF at Day 6.
- `orchestrator/engine.py` - crm_outreach dispatch now routes to sequence_engine, not dormant outreach_tool
- `signal_works/morning_runner.py` - Steps 3+5 now call sequence_engine

### Dormant (not deleted, nothing calls them automatically)
- `signal_works/email_builder.py`
- `signal_works/send_drafts.py`
- `skills/outreach/outreach_tool.py`

### GeoListed Landing Page
- `output/websites/signal-works-landing/index.html` - LLM chat preloader + particle network hero combined, nav links, favicon, gold cursor on hover, 3-line punchy hero subhead
- `output/websites/geolisted-site/` - Production copy, GitHub repo bokar83/geolisted-site, branch main
- Domain: geolisted.co (Namecheap, ~$13/yr), DNS pointed to Hostinger
- Favicon: signal pulse rings on navy SVG

### Apollo Integration
- `skills/apollo_skill/apollo_client.py` - CW_ICP, SW_ICP, STUDIO_ICP with contact_email_status=verified, seniority filter, apollo_revealed dedup table

### VPS
- All containers healthy. Sequence engine dry-run verified clean on VPS.
- VPS import fix: sequence_engine falls back to `from db import` when /app is the orchestrator root

---

## Decisions made

- geolisted.co chosen - GEO-forward brand, $13/yr .co
- Sequence engine replaces ALL one-shot senders - single dispatch path
- CW = 5 touches, T2 = SaaS audit PDF (Day 6, value-add not pitch)
- SW = 4 touches, geolisted.co signature
- Draft-only by default - flip AUTO_SEND_CW=true / AUTO_SEND_SW=true in VPS .env when ready
- git branch = always main (hard rule, corrected on geolisted-site)
- Hostinger not Vercel for new sites

---

## What is NOT done

- Auto-send NOT enabled - both pipelines draft-only. Boubacar reviews first.
- Studio not wired into morning_runner
- geolisted.co Hostinger Git connection not yet confirmed live (DNS propagating)
- Website registry gaps (renewal dates, hosting for several sites)
- Reply detection / opt-out automation (opt_out column exists but nothing reads STOP replies)

---

## Open questions

1. When to flip AUTO_SEND_CW=true? (review first batch of drafts first)
2. Is Hostinger Git connection wired for geolisted-site?
3. AdSense status on calculatorz / convertisseur / unit-converter?
4. Renewal dates for catalystworks.consulting, humanatwork.ai, boubacarbarry.com?

---

## Next session must start here

1. Check boubacar@catalystworks.consulting Drafts - confirm morning runner fired and 10+ drafts landed
2. If drafts look good, add AUTO_SEND_CW=true to VPS .env and restart orc-crewai
3. Wire Studio into morning_runner.py as Step 6
4. Confirm geolisted.co is live at Hostinger
5. Fill website registry gaps

---

## Files changed this session

- skills/outreach/sequence_engine.py       NEW
- templates/email/sw_t1-t4.py             NEW (4 files)
- templates/email/cw_t2-t5.py             NEW (4 files)
- skills/apollo_skill/apollo_client.py     UPDATED
- signal_works/morning_runner.py           UPDATED
- signal_works/topup_cw_leads.py          NEW
- orchestrator/engine.py                   UPDATED
- output/websites/signal-works-landing/index.html  UPDATED
- output/websites/geolisted-site/          NEW REPO
- output/websites/geolisted-site/favicon.svg  NEW
