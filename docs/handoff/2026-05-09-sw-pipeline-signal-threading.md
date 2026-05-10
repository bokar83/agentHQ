# Session Handoff - SW Pipeline Signal Threading - 2026-05-09

## TL;DR

Absorbed m0h/@exploraX_ Google Maps lead-gen playbook and built the entire SW email pipeline from scratch in one session. Starting point: generic 5-touch sequence with unqualified leads and fabricated scarcity claims. Ending point: qualification gate, signal-threaded T1-T5 openers (each lead gets emails specific to their exact gap), gmb_opener persisted to DB, Calendly in T3/T4, /callsheet Telegram command, monthly decay cron, and a pipeline audit script. All deployed to VPS. Sankofa identified the real bottleneck: the machine is built but calls aren't being made.

## What was built / changed

- `skills/serper_skill/hunter_tool.py` — `score_gmb_lead()` returns `(int, dict)`. Named constants: `GMB_LOW_REVIEW_THRESHOLD=30`, `GMB_LOW_RATING_THRESHOLD=4.0`, `GMB_REQUIRED_FIELDS`.
- `skills/outreach/sequence_engine.py` — T1 SW gate (score < 2 dropped). `gmb_opener` determined + injected at T1. T2-T5 reconstruct `gmb_signal_notes` from stored opener. `_ensure_sequence_columns` adds `gmb_opener` column. `_mark_sent` writes opener to DB. `_get_due_leads` selects `review_count, has_website, google_rating, niche, gmb_opener`.
- `templates/email/sw_t1.py` — 4-branch opener. Subject: "noticed something on your Google listing".
- `templates/email/sw_t2.py` — signal-thread continuity. "One per city" REMOVED. Replaced with AI-compounds-like-Google framing.
- `templates/email/sw_t3.py` — signal thread + social proof + Calendly. Fabricated "12→47 reviews" REMOVED. Replaced with "similar businesses in Utah" framing.
- `templates/email/sw_t4.py` — Calendly link added. "meeting" → "walkthrough".
- `orchestrator/griot.py _ops_digest_text()` — GMB signal breakdown block added after outreach metrics.
- `orchestrator/handlers_commands.py _cmd_callsheet()` — new Telegram command. Today's SW T1 leads with phones + pre-written openers. Registered in `_COMMANDS`.
- `orchestrator/scheduler.py _run_gmb_score_decay()` — monthly decay cron, 1st of month 06:00 MT.
- `scripts/pipeline_audit.py` — `--check gmb_score_gate | sequence_thread | decay_candidates | all`.
- `skills/hormozi-lead-gen/references/cold-call-scripts.md` — 3 objection handlers, "walkthrough" reframe, "tomorrow at 10" close, offer menu with price anchors.
- `skills/hormozi-lead-gen/references/review-request-product.md` — n8n+Twilio build spec, $297-497 sellable add-on.
- `docs/roadmap/atlas.md` — Atlas item #11 added (GATED: scorer → website-teardown auto-audit). Cheat block updated. Session log appended.

## Decisions made

- **gmb_opener persisted to DB** — branch frozen at T1 enrollment. Even if a lead gets a website between T1 and T2, T2 still uses the no_website thread. Prevents broken continuity from data changes.
- **"One per city" permanently removed** — fabricated scarcity. If two prospects compare emails, credibility gone. Real scarcity = enforce it or don't say it.
- **T3 social proof = "similar businesses in Utah"** — no fabricated numbers until real SW client data exists.
- **ai_quick_wins field skipped** — 433/2051 SW leads have it but all generic ("build topical authority content"). Not specific enough to use in email openers.
- **/callsheet = on-demand only** — not auto-included in morning digest. Stale by afternoon; Boubacar should pull it when ready to call.
- **Mid-sequence leads never opted out by decay** — never interrupt an active thread. Flag only.
- **Review-request product = build after first client** — spec done, no clients yet to deliver to.

## What is NOT done (explicit)

- **Calls not being made** — Sankofa identified this as the real bottleneck. The pipeline is built. Revenue gates on Boubacar dialing leads.
- **Review-request n8n workflow** — spec at `skills/hormozi-lead-gen/references/review-request-product.md`. Build after first SW client.
- **Score decay not tested** — fires 1st of month. First real run: 2026-06-01. No manual test.
- **Pipeline audit not run** — scheduled for 2026-05-28. Run: `docker exec orc-crewai python3 /app/scripts/pipeline_audit.py --check all`
- **Atlas #11 gated** — auto-audit (scorer → website-teardown warm opener). Trigger: 2026-05-28 baseline.
- **AUTO_SEND_SW status unknown** — if it's still "false", sequences are drafting not sending. Check: `docker exec orc-crewai env | grep AUTO_SEND`

## Open questions

- Is AUTO_SEND_SW=true on VPS? If not, emails are drafting to Gmail, not sending. Check before assuming pipeline is live.
- What is actual SW T1 volume per week? If <20, volume is the first bottleneck.
- When does first SW client close? That unlocks: review-request workflow build, real social proof for T3, Atlas #11.

## Next session must start here

1. Send `/callsheet` to @CCagentsHQ_bot after 07:30 MT morning runner fires. Get the list. Dial within the hour.
2. Check `docker exec orc-crewai env | grep AUTO_SEND` — confirm AUTO_SEND_SW=true.
3. Check morning digest for GMB signal breakdown line (no-website/low-reviews/chatgpt split).
4. `docker logs orc-crewai --tail 50` — confirm `[SW] T1 GMB gate: dropped N` present.
5. On 2026-05-28: `docker exec orc-crewai python3 /app/scripts/pipeline_audit.py --check all`

## Files changed this session

```
skills/serper_skill/hunter_tool.py          score_gmb_lead() returns (int, dict)
skills/outreach/sequence_engine.py          gate, opener persistence, T2-T5 reconstruction
templates/email/sw_t1.py                    4-branch signal opener
templates/email/sw_t2.py                    signal thread, scarcity removed
templates/email/sw_t3.py                    signal thread, fake numbers removed, Calendly
templates/email/sw_t4.py                    Calendly added
orchestrator/griot.py                       GMB signal breakdown in digest
orchestrator/handlers_commands.py           /callsheet command
orchestrator/scheduler.py                   _run_gmb_score_decay() monthly cron
scripts/pipeline_audit.py                   new file — 3 health checks
skills/hormozi-lead-gen/references/
  cold-call-scripts.md                      objection handlers, price anchors
  review-request-product.md                 n8n+Twilio product spec
docs/roadmap/atlas.md                       item #11, cheat block, session log
docs/reviews/absorb-log.md                  verdict logged
docs/reviews/absorb-followups.md            follow-up DONE marked
```
