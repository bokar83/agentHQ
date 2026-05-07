# agentsHQ Cadence Calendar

**Purpose:** Single source of truth for what runs when, and when Boubacar has to be in the loop. Updated whenever a schedule changes.

**Two ringing bells matter:**
- **Background:** runs by itself, no human attention required
- **Human-in-loop:** Boubacar must do something within a window or the pipeline stalls

The goal is to keep the human-in-loop column short and predictable. Anything that creeps onto that list without a real reason should be automated or removed.

Last updated: 2026-05-06

---

## Daily

| Time (MT) | Task | Type | Human in loop? | Source |
|---|---|---|---|---|
| 06:00 | Quote rotation (agentsHQ + The Forge 2.0 Notion) | Background | No | scheduler.py daily cron |
| 06:00 | KPI refresh | Background | No | scheduler.py daily cron |
| 06:00 | Notion lead sync (Supabase -> Notion CRM, ~960 leads) | Background | No | scheduler.py daily cron |
| 06:00 | Daily Lead Harvest (hunter_crew, Utah SMB sweep) | Background | No | scheduler.py daily cron |
| 06:00 | Social Media Engagement Refresh (X & LinkedIn metrics) | Background | No | scheduler.py daily cron |
| 06:00 | NLM registry export (Postgres -> Sheets) | Background | No | VPS crontab |
| 07:00 | heartbeat-morning self-test ping | Background | No | scheduler.py |
| 13:00 | heartbeat-midday self-test ping | Background | No | scheduler.py |
| 19:00 | heartbeat-evening self-test ping | Background | No | scheduler.py |
| 07:00 | Griot morning tick (proposes daily content) Mon-Fri | Background -> Telegram nudge | YES if proposal arrives | griot.py |
| 07:30 | Publish brief Telegram digest | Background -> Telegram nudge | YES if there is content to confirm | publish_brief.py |
| 08:00 | Health sweep (probes all live endpoints) | Background | No (silent unless red) | health_sweep.py |
| 08:30 | NotebookLM digest | Background -> Telegram | Light: scan if anything pending | scheduler.py |
| 13:00 | Weekly model review agent (gates internally on Sunday) | Background | No except Sundays | model_review_agent.py |
| Continuous | griot-scheduler (every 5 min) | Background | No | griot_scheduler.py |
| Continuous | auto-publisher (every 5 min) | Background | No (publishes from queue) | auto_publisher.py |
| Continuous | session-compressor (every 30 min) | Background | No | session_compressor.py |
| Continuous | error_monitor.sh (every 15 min) | Background | YES if alert fires (rare) | VPS crontab |
| Daily | Signal Works morning_runner (20 drafts: 10 SW + 10 CW) | Background | YES Week 1 review; auto-send Week 2+ | signal_works/morning_runner.py |

## Weekly

| Day | Time (MT) | Task | Type | Human in loop? |
|---|---|---|---|---|
| Sunday | 18:00 | Pre-scout Telegram nudge (NEW, planned) | Telegram nudge | YES light: confirms readiness for Monday |
| Sunday | 13:00 | Model review agent (Haiku scorer, 4 candidates, 3 seeds) | Background | No (proposes via approval_queue if change > 3 pts) |
| Monday | 05:30 | Studio Trend Scout fires (9 niches: 6 CW + 3 Studio) | Background -> Telegram | YES: approve/reject candidates within window |
| Monday | 06:00-11:30 | Newsletter anchor approval window | YES | Approve one CW candidate as Weekly Signal anchor |
| Monday | 11:30 | Fallback Telegram nudge if no anchor approved (NEW, planned) | Telegram nudge | YES: reply with topic by 14:00 MT or issue slips |
| Monday | 12:00 | newsletter_crew auto-fires (NEW, planned) | Background -> Telegram | YES: review draft + thumbnail |
| Monday | 12:00-EOB | Newsletter draft review window | YES | Edit if needed, paste into beehiiv |
| Tuesday | varies | Newsletter ships from beehiiv | Background | NO once scheduled |

## Every 3 Days

| Time | Task | Type | Human in loop? |
|---|---|---|---|
| 05:30 (every 3rd day) | NotebookLM auth refresh | Background | YES if alert (rare) |

## Triggered (not scheduled)

| Trigger | Task | Human in loop? |
|---|---|---|
| Approval queue receives item | Telegram message with Approve/Reject buttons | YES: tap within 24h |
| Publish failure on auto-publisher | Telegram alert | YES: investigate |
| Health sweep red probe | Telegram alert | YES: investigate |
| 3+ error monitor alerts in a week | Concierge crew triage (M4, gated until 2026-05-08) | Will become YES once live |

## Gated (not yet running)

| Trigger date | Task | Type when live |
|---|---|---|
| 2026-05-06 | Hunter.io upgrade go/no-go decision | Boubacar decision |
| 2026-05-08 | M5 Chairman Crew (L5 Learning) | Background, weekly proposals via approval_queue |
| 2026-05-08 | M4 Concierge Crew (error triage) | Background |
| 2026-05-12 | M10 Topic Scout Phase 2 | Background |
| 2026-05-15 | M11c Research Engine (triple-hold) + Perplexity prospect-email spike | Boubacar decision |

---

## Human-in-Loop Daily Time Budget (target)

| Window | Task | Target time |
|---|---|---|
| 07:00-07:45 MT | Griot proposal + publish brief responses | 5 min |
| 12:00-12:30 MT (Mon only) | Newsletter draft review | 15 min |
| Throughout day | Approval queue / Telegram nudges | 5 min total |
| Week 1 only | Signal Works morning review | 20 min |

**Total daily ceiling:** ~30 min of attention spread across the day. Anything pushing past 45 min sustained is a signal that something needs to be automated or descoped.

---

## Rules

1. **Anything that requires Boubacar to act inside a window must have a fallback nudge before the window closes.** No silent stalls.
2. **Anything that goes from human-in-loop to background gets celebrated and logged here.** That is the direction we want.
3. **Anything that goes the other way needs justification.** Why did this stop being automatic?
4. **No new recurring human-in-loop task is added without first checking if the existing 30-min budget can absorb it.** If not, something else has to come off.
5. **Scout-to-newsletter must use this Monday's data for this Tuesday's send.** Stale data defeats the point.

---

## Pending Implementation

These are written in the calendar but not yet built. Remove the "(NEW, planned)" tags as they ship.

- Sunday 18:00 MT pre-scout reminder
- Monday 11:30 MT fallback nudge
- Monday 12:00 MT `newsletter_anchor_tick`
- Newsletter Anchor tagging mechanism on scout picks
- CTQ + Sankofa + source verification baked into newsletter_crew

Estimated build: 2-3h. Tracked in `project_task_backlog.md` Active Sprint #2.
