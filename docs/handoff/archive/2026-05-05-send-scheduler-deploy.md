# Session Handoff - Send Scheduler + 50 Drafts/Day Deploy - 2026-05-05

## TL;DR

Built send_scheduler.py (batched email sender, 35 SW + 15 CW + 15 Studio/day),
updated morning_runner to 50 drafts/day target with SW gap fill. Ran Sankofa Council
on volume/deliverability. All code committed and merged by gate. Docker build running
on VPS at shutdown -- container still has old code. Morning run at 13:00 UTC.

## What was built / changed

- `signal_works/send_scheduler.py` (NEW) -- batched sender, DAILY_CAPS SW=35/CW=15/Studio=15,
  BATCH_SIZES SW=6/CW=3/Studio=3, 3-8 min random delay, 6 runs/day via systemd timer
- `scripts/systemd/send-scheduler.service` + `.timer` (NEW) -- 09:00-16:30 MT Mon-Fri
- `signal_works/morning_runner.py` -- SW topup min=35, SW seq limit=35, CW seq limit=15,
  Step 5b gap fill (SW fills CW shortfall to hit 50), Step 6 Studio seq limit=15
- `skills/outreach/sequence_engine.py` -- Studio pipeline: TOUCH_DAYS_STUDIO, TEMPLATES studio,
  source_filter apollo_studio%, AUTO_SEND_STUDIO, _subject(lead) hook
- `templates/email/sw_t1.py` -- _resolve_niche(), _INDUSTRY_TO_NICHE, generic hook fallback
- `templates/email/studio_t1.py` -- _subject() niche-aware, _TRADES set
- `templates/email/studio_t3.py` + `studio_t4.py` -- Calendly URL fixed

## Decisions made

- 35 SW + 15 CW = 50 drafts/day. SW gap fill covers CW shortfall.
- Auto-send stays OFF until Boubacar reviews 2026-05-05 morning run. CW ready first.
- send_scheduler timer NOT installed yet -- do it after verifying build landed.
- Hormozi ramp: 50/day now, prove reply rate, scale to 100 after 2 booked calls.
- Docker code is image-baked (not volume). Every change = full rebuild (15-25 min).
- CW resend NOT needed -- 57 leads already at touch=1, working through T2-T5 normally.

## What is NOT done (explicit)

- Docker build still running at shutdown -- container has old code (minimum=10)
- send-scheduler.timer NOT installed on VPS yet
- Auto-send all OFF -- intentional
- sender identity mismatch (Gmail vs .consulting domain) -- flagged by Sankofa, not fixed
- Google Postmaster Tools not set up -- needed before scaling past 50/day

## Open questions

- Did 2026-05-05 morning run (13:00 UTC) fire with new code? Check log.
- Did Studio harvest find leads (Step 4b)? First run ever.
- Did SW niche resolution work? No more "best small business in X"?

## Next session must start here

1. Verify build landed: `ssh root@72.60.209.109 "docker exec orc-crewai grep -c 'minimum=35' /app/signal_works/morning_runner.py"` -- expect 1
2. If build done, install timer: `ssh root@72.60.209.109 "cp /root/agentsHQ/scripts/systemd/send-scheduler.* /etc/systemd/system/ && systemctl daemon-reload && systemctl enable send-scheduler.timer && systemctl start send-scheduler.timer"`
3. Check morning run log: `ssh root@72.60.209.109 "tail -100 /var/log/signal_works_morning.log"` -- verify 35 SW + 15 CW + Studio Step 4b/6
4. Check Drafts in boubacar@catalystworks.consulting -- confirm niche labels correct, no "small business"
5. If CW drafts look good: flip `AUTO_SEND_CW=true` in VPS .env + rebuild

## Files changed this session

```
signal_works/send_scheduler.py             (NEW)
signal_works/morning_runner.py             (50 drafts target + gap fill)
scripts/systemd/send-scheduler.service    (NEW)
scripts/systemd/send-scheduler.timer      (NEW)
skills/outreach/sequence_engine.py        (Studio pipeline wiring)
templates/email/sw_t1.py                  (niche fix)
templates/email/studio_t1.py             (niche-aware subject)
templates/email/studio_t3.py             (Calendly fix)
templates/email/studio_t4.py             (Calendly fix)
```
