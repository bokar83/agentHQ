# Session Handoff - Signal Works Pipeline Complete - 2026-04-27

## TL;DR
Built the full Signal Works outreach automation from scratch: lead harvesting across 81 Wasatch Front niche/city pairs, personalized HTML email generation, Gmail draft creation from boubacar@catalystworks.consulting, bounce scanning, and a unified daily runner that also triggers the existing Catalyst Works cold outreach. 20 drafts/day, 100 contacts/week. Boubacar reviews and hits Send. Week 1 is validation; Week 2 flips to full auto-send.

## What was built / changed

### New files
- `signal_works/gmail_draft.py` - creates Gmail drafts via CW OAuth (httpx, no gws CLI)
- `signal_works/email_builder.py` - personalized HTML renderer (has-website + no-website variants, colorblind-safe, Vercel play links)
- `signal_works/send_drafts.py` - daily SW draft runner (`--run` real, `--run --test` test, `--count` check)
- `signal_works/topup_leads.py` - harvests 3 niches x 27 Utah cities until 10 email leads exist
- `signal_works/bounce_scanner.py` - scans CW inbox for mailer-daemon, nulls bad emails in Supabase
- `signal_works/morning_runner.py` - unified 4-step daily runner (bounce + SW topup + SW drafts + CW drafts)
- `signal_works/outreach_runner.py` - standalone wrapper for CW cold outreach pipeline
- `signal_works/register_task_admin.ps1` - one-time Windows Task Scheduler setup (run as admin)
- `signal_works/morning.bat` - fallback manual runner (deprecated in favor of morning_runner.py)
- `docs/reference/TOOLS_ACCESS.md` - master reference for all tool access patterns
- `output/websites/signal-works-demo-hvac/play.html` - HVAC autoplay page (amber #E8A020 spinner)

### Modified files
- `signal_works/lead_scraper.py` - added `_is_valid_email()` (rejects ...@domain, noreply, placeholder, platform domains); wired into Firecrawl + CSV loader
- `signal_works/migrate_leads_table.py` - added email_drafted, email_drafted_at, email_sent_at columns
- `orchestrator/db.py` - added `get_leads_for_drafting()` and `mark_email_drafted()`
- `signal_works/templates/preview_roofing.html` - updated to Vercel play URL
- `signal_works/templates/preview_dental.html` - updated to Vercel play URL

### Deployed
- HVAC demo site: https://signal-works-demo-hvac.vercel.app (GitHub: bokar83/signal-works-demo-hvac, created 2026-04-27)
- All 3 sites have /play.html autoplay pages and /pitch-reel.mp4

## Decisions made

**Video in email:** Vercel /play.html pages, not Drive links. `<video>` in email blocked by Gmail/Outlook. Drive doesn't autoplay. Play page: black bg, autoplay muted loop, tap to unmute.

**Gmail auth:** `secrets/gws-oauth-credentials-cw.json` read directly via httpx. gws CLI cannot handle large HTML bodies on Windows (8191-char limit, no stdin support).

**Email routing:** All Signal Works + CW outreach drafts go to boubacar@catalystworks.consulting Drafts. Gmail MCP tool is scoped to bokar83@gmail.com only - do not use it for outreach.

**Test safety:** `--run --test` adds [TEST] prefix and never marks leads as drafted. `--mark-drafted` is blocked if draft_payloads.json contains [TEST] subjects.

**Harvester scope:** 3 niches (roofer, pediatric dentist, hvac) x 27 Wasatch Front cities = 81 pairs. Stops the moment 10 email leads found. SLC core scraped first.

**Week 1/Week 2 plan:** Week 1 = human review before send (training wheels). Week 2 = if 5 days clean, flip to auto-send by changing `drafts.create` to `messages.send`.

**Bounce handling:** bounce_scanner.py reads CW inbox, extracts Final-Recipient headers, nulls emails in Supabase with note. Runs as step 0 daily.

**20 drafts/day target locked:** 10 SW + 10 CW. 100 contacts/week Mon-Fri.

## What is NOT done (explicit)

- **Windows Task Scheduler not registered permanently** - requires admin elevation. `register_task_admin.ps1` is ready; Boubacar must run it once from elevated PowerShell. In-session cron at 07:03 AM is the backup (7-day limit, must re-create each session).
- **Auto-send not enabled** - by design until Week 1 validates. `send_drafts.py` uses `drafts.create`. Flip to `messages.send` in both `gmail_draft.py` and `outreach_tool.py` for Week 2.
- **HVAC email template (preview_hvac.html)** - not built. The live play.html works; the static preview template for review is missing.
- **Notion logging for SW leads** - not wired. SW leads only go to Supabase; no Notion Content Board entry per draft batch.
- **Score rescoring** - ~15 leads in DB have ai_score=0 with breakdown=NULL (scored before scorer was fully wired). They'll rescore on next topup run.

## Open questions

- Should SW drafts include owner name lookup (Google My Business API or manual)? Currently fallback is first word of business name.
- Should HVAC leads get a different pitch since the emergency angle is stronger? Current template is niche-generic.
- Week 2 auto-send: should there be a Telegram confirmation before each batch sends, or fully silent?

## Next session must start here

1. **Verify morning_runner.py ran at 07:03 AM** - check `logs/signal_works_morning.log`. If 20 drafts in boubacar@catalystworks.consulting, pipeline is working.
2. **Run register_task_admin.ps1 as admin** to make the Task Scheduler permanent: `powershell -ExecutionPolicy Bypass -File "D:\Ai_Sandbox\agentsHQ\signal_works\register_task_admin.ps1"`
3. **Review the 5 existing leads' real drafts** - Vault Roofing (Levi), Aspen Roofing, Brady Roofing, Powerful Roofing, Rose Park Pediatric. Delete any duplicate [TEST] drafts from earlier sessions.
4. **Check if topup found new leads** - `python -m signal_works.send_drafts --count` should show 10 if harvest ran.
5. **Signal Works conversations** - Boubacar has 3 calls today (2026-04-28). Goal: lock 1 into a 20-30 min discovery call. Catalyst Works prospect by Friday.

## Files changed this session

```
signal_works/
  gmail_draft.py              NEW
  email_builder.py            NEW (major)
  send_drafts.py              NEW (rewritten twice)
  topup_leads.py              NEW (rewritten for 81 pairs)
  bounce_scanner.py           NEW
  morning_runner.py           NEW
  outreach_runner.py          NEW
  register_task_admin.ps1     NEW
  morning.bat                 UPDATED
  lead_scraper.py             UPDATED (_is_valid_email)
  migrate_leads_table.py      UPDATED (email tracking cols)
  templates/preview_roofing.html  UPDATED (Vercel links)
  templates/preview_dental.html   UPDATED (Vercel links)

orchestrator/
  db.py                       UPDATED (get_leads_for_drafting, mark_email_drafted)

output/websites/signal-works-demo-hvac/
  play.html                   NEW
  pitch-reel.mp4              COMMITTED + DEPLOYED
  pitch-reel-thumbnail.png    COMMITTED + DEPLOYED
  index.html                  COMMITTED + DEPLOYED

docs/reference/
  TOOLS_ACCESS.md             NEW
```
