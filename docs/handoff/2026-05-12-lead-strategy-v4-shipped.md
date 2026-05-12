# Session Handoff — Lead Strategy v4 Shipped — 2026-05-12

## TL;DR

Shipped Lead Strategy v4 as the ONE master roadmap until 2026-08-04. All other roadmaps feed into this. Sankofa Council premortem killed the 8-lane v3 plan as the failure mode itself — v4 = ONE lane (Daily Fast-Feedback Sprint, M-F 09:00 MDT, warm Utah contacts, reply-dependent) for Weeks 1-3. Data-wiring subagent shipped canonical `email_events` ledger on branch `feat/email-events-canonical-ledger` [READY] and surfaced two corrections: (1) 500 cold sends all-time, not the 100+/100+ Boubacar remembered; (2) 0 real human replies — the 3 the new ledger flagged were all mailer-daemon bounces (classifier bug). 9.4% delivery failure rate above Gmail throttle threshold. Brandon = accountability partner candidate, daily 09:05 MDT text, 4-week commitment to be confirmed Mon 2026-05-13 before 09:00.

## What was built / changed

**Strategy doc (master roadmap, the only artifact that matters):**
- `docs/strategy/lead-strategy-2026-05-12.html` — full v4 HTML with TL;DR card, 8 ground-truth numbers, 7 failure modes table, 7 prevention mechanics (M1-M7) + M8 list-hygiene gate, 12-week ramp, Brandon accountability spec, Monday 2026-05-13 09:00 MDT non-negotiable action card. Served on `http://127.0.0.1:8801/lead-strategy-2026-05-12.html`.

**Roadmap update:**
- `docs/roadmap/harvest.md` — added H1j section with SHIPPED ✅ status, full decision summary, cross-refs.

**Handoff stubs (queued separately):**
- `docs/handoff/2026-05-12-prospeo-invalid-datapoints.md` — Prospeo INVALID_DATAPOINTS silent poisoning of SW chain. Hard deadline before 2026-05-28 (Apollo Free-tier cutover).
- `docs/handoff/2026-05-13-inbound-signal-metric-prompt.md` — inbound-signal-metric prototype prompt (2.5 hr coding session, ~Wed/Thu).

**Memory (saved this session):**
- `~/.claude/projects/d--Ai-Sandbox-agentsHQ/memory/project_lead_strategy_2026-05-12.md` — the master plan summary, all mechanics, all decisions, all open follow-ups.
- `~/.claude/projects/d--Ai-Sandbox-agentsHQ/memory/feedback_agent_time_perception_broken.md` — new rule: agent has no reliable internal clock, stop volunteering duration claims.
- `MEMORY.md` — two new pointers added.

**Email sent (verified per HARD RULE 0):**
- Lead Strategy v4 session digest sent to `bokar83@gmail.com` + `boubacar@catalystworks.consulting`. Msg ID `19e1de601c8dd0c4`. From-header verified as `Boubacar Barry <boubacar@catalystworks.consulting>`. HTML body = full strategy doc. Plain-text body = TL;DR.
- Script saved at `d:/tmp/send_lead_strategy_digest.py` for re-send if needed.

**Subagent work (already merged into main earlier via gate auto-merge):**
- `feat/email-events-canonical-ledger` branch (tip `ed5ebe0`) — canonical `email_events` ledger on orc-postgres, backfill from `sw_email_log` + Gmail Sent metadata, reply-detection cron, list hygiene gate. KNOWN BUG: reply detector flags `from:mailer-daemon@*` and `from:postmaster@*` as event_type='replied'. Fix is part of M8 in v4. Two-DB drift: migration applied to orc-postgres, NOT Supabase — Supabase still holds the canonical `leads` table.

**Sankofa Council premortem (run this session):**
- `outputs/council/2026-05-12-20-20-24.html` — 5 voices speaking from 2026-08-04 retrospectively. Named 7 failure modes + 7 calendar-level preventions. Chairman synthesis: ONE lane W1-3, Brandon as accountability partner, paid $250 Signal Session trial (not free).

## Decisions made

1. **Lead Strategy v4 = master roadmap.** All other roadmaps (harvest, ghost, atlas, compass, studio) feed into this. The only plan Boubacar follows until 2026-08-04.

2. **Weeks 1-3 = ONE lane only.** Daily Fast-Feedback Sprint. NO other lanes until W4+, gated on ≥10 replies + ≥1 paid call.

3. **8-lane v3 plan rejected** as the failure mode itself per Sankofa premortem. Re-entry possible W4-11, but the architecture is sequenced, not parallel.

4. **Brandon = accountability partner candidate.** Daily 09:05 MDT text from Boubacar, 4-week commitment. Confirmation due before 09:00 Mon 2026-05-13. If Brandon declines, list-building shifts to find backup before sprint Day 1.

5. **Signal Session pricing = $250 paid trial** (lower than $1500 full). Free reserved for select strategic accounts. Rejects "free" as default per Council failure mode #6 (Avoidance of Closure by Design Contradiction).

6. **Goalpost = 3 paying clients (1 each in SW + GW + CW) by 2026-08-04.** Single 12WY 90-day decision. Mid-cycle review 2026-06-30 = forced inflection.

7. **Reddit + LinkedIn + X only.** Drop Facebook from all watering-hole plays. Reddit subs locked: r/sweatystartup (CW + SW), r/HVAC (SW), r/Substack (GW), r/SaltLakeCity (local).

8. **Utah-local positioning explicit in copy.** "Boubacar — South Jordan, UT" in cold sign-offs. Memory rule `feedback_social_pipeline_strategy_refill.md` about Guinea+Conakry is for content-geography only, NOT physical location.

9. **Idea Vault Lock policy.** New ideas during the cycle → text Telegram "Vault: [idea]" → bot replies "Stored. Unlocks after 3 paying clients." Targets Council failure mode #7 (Shiny-Drift).

10. **Time-perception rule logged.** Agent will not volunteer duration claims or "X hours into session" framing. Memory rule live.

## What is NOT done (explicit)

- **Brandon has not been asked yet.** Boubacar to confirm before Mon 2026-05-13 09:00 MDT.
- **Google Calendar overlay not built.** Strategy doc has the spec for M1-M8 timings but no .ics file or Calendar MCP write happened. Boubacar can manually set up the recurring blocks tomorrow, OR a separate session can build the .ics.
- **Reply-classifier fix (M8) not shipped yet.** The 3 mailer-daemon-as-replied rows are still in `email_events` on orc-postgres. Fix queued in `docs/handoff/2026-05-12-prospeo-invalid-datapoints.md` Wed/Thu session.
- **First Win Ceremony script not built.** `scripts/first_win_ceremony.py` spec'd in v4 but not coded. Queued for W1.
- **orc-postgres → Supabase reconciliation NOT done.** Two-DB drift on `email_events` remains. Probably acceptable for now (orc-postgres = audit ledger, Supabase = lead state). Document the architecture in a separate session.
- **Inbound-signal-metric prototype NOT built.** Prompt saved at `docs/handoff/2026-05-13-inbound-signal-metric-prompt.md` for separate coding session.
- **Apollo Free-tier verification for SW chain NOT done.** Hard deadline 2026-05-28. Documented in Prospeo handoff stub.
- **Notion calendar / execution-cycle update NOT done** this session. Boubacar can transcribe M1-M8 into his Notion calendar Wed morning if useful.

## Open questions

1. **Will Brandon accept?** (load-bearing — the daily 09:05 text is the prevention layer for failure modes 1-5)
2. **Does Boubacar have 3 warm Utah contacts ready by Mon 09:00?** If not, W1 pivots to building the warm list.
3. **Free Signal Sessions for which "key accounts" specifically?** Strategy doc says "select strategic accounts" — Boubacar to name them as opportunities arise.
4. **Google Calendar overlay built in-session next time, or hand-set by Boubacar?** Decision can wait until first M1 sprint runs.
5. **Reply-classifier fix priority** — ship in standalone session, or fold into next cold-send prep work?

## Next session must start here

Three possible openers depending on Boubacar's state Mon morning:

**Opener A — Brandon said yes + Boubacar has 3 contacts:**
1. Verify Brandon accountability text channel works (test ping at 08:45)
2. Send Fast-Feedback Sprint template to 3 warm Utah contacts at 09:00 MDT
3. Text Brandon at 09:05 "Sent 3. Day 1 done."
4. Log Day 1 to `data/inbound-signal-log.md` (create the file in this session)
5. Watch for replies, fire First Win Ceremony manually if any land

**Opener B — Brandon said yes + Boubacar doesn't have 3 contacts:**
1. 08:30-09:00 = list-building. Use any of: LinkedIn 1st-degree Utah connections, past clients/collaborators, neighbors who own businesses, anyone who already follows the work
2. Send to 3 at 09:00 (even if not "warm-warm" — proximity counts)
3. Same Brandon text at 09:05

**Opener C — Brandon declined or unreachable:**
1. Sprint Day 1 still runs at 09:00 — non-negotiable
2. Backup accountability: pick 1 other candidate (close friend, sibling, family member who'll text back). Ask immediately.
3. If genuinely no one available: text accountability to Telegram bot. Lower fidelity but not zero.

**ALL openers:**
- Read this handoff file first
- Open `http://127.0.0.1:8801/lead-strategy-2026-05-12.html` (server may need restart — `cd docs/strategy && python -m http.server 8801 --bind 127.0.0.1`)
- Then start opener A/B/C

## Files changed this session

```
docs/strategy/lead-strategy-2026-05-12.html (new, master deliverable)
docs/handoff/2026-05-12-prospeo-invalid-datapoints.md (new stub)
docs/handoff/2026-05-13-inbound-signal-metric-prompt.md (new queued prompt)
docs/handoff/2026-05-12-lead-strategy-v4-shipped.md (this file)
docs/roadmap/harvest.md (H1j section added, SHIPPED)
outputs/council/2026-05-12-20-20-24.html (Sankofa premortem report)
d:/tmp/send_lead_strategy_digest.py (session-digest sender, msg id 19e1de601c8dd0c4)
~/.claude/projects/d--Ai-Sandbox-agentsHQ/memory/project_lead_strategy_2026-05-12.md (new)
~/.claude/projects/d--Ai-Sandbox-agentsHQ/memory/feedback_agent_time_perception_broken.md (new)
~/.claude/projects/d--Ai-Sandbox-agentsHQ/memory/MEMORY.md (2 pointers added)
```

Plus (already on `feat/email-events-canonical-ledger` branch, ready for Gate):
```
migrations/009_email_events.sql
scripts/backfill_email_events.py
scripts/sync_replies_from_gmail.py
signal_works/email_events.py
signal_works/send_scheduler.py (wired)
skills/outreach/sequence_engine.py (wired)
docs/audits/email-data-wiring-2026-05-12.md
docs/audits/email-data-wiring-2026-05-12-validation.md
```
