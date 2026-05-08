# Session Handoff — Hunter Fix + Email Sig Polish + Email Queue v2 Plan — 2026-05-08

## TL;DR

Started from 2026-05-07 handoff. Three workstreams completed: (1) Hunter `force_fresh` fix merged and validated — CW now hits 15/15 daily regardless of undrafted residue. (2) Email signature polish merged — Studio templates now sign `geolisted.co`, body prose uses "Boubacar" not "Boubacar Barry". (3) Email queue v2 planned — Sankofa Council rejected the 150-cap approach; Boubacar chose Path B (first-principles rewrite: no caps, on-demand drafting, Gmail-as-truth). Plan v2 stub written; full plan + gates + Codex implementation scheduled for 2026-05-09 / Fri-Sat.

## What was built / changed

### Merged to main (both auto-merged by Gate)

- `feature/hunter-force-fresh` → commit `a91e2b0`, merged `2efb37c`
  - `signal_works/topup_cw_leads.py:85` — `force_fresh: bool = False` param added
  - `signal_works/harvest_until_target.py:175` — passes `force_fresh=True`
- `feat/email-signature-polish` → commit `578d66c`, merged `5bb9d8c`
  - `templates/email/studio_t1.py:34` — "Boubacar Barry" → "Boubacar"
  - `templates/email/studio_t1-4.py` footers — `catalystworks.consulting` → `geolisted.co`

### Plans written

- `docs/plans/2026-05-08-phase1-hunter-force-fresh.md` — Karpathy PASS/SHIP
- `docs/plans/2026-05-08-email-signature-polish.md` — Karpathy PASS/SHIP
- `docs/plans/2026-05-09-email-queue-v2-frame.md` — stub, full write tomorrow
- `docs/plans/archive/2026-05-08-hunter-email-queue-v1-superseded.md` — v1 archived
- `docs/plans/codex-prompts/2026-05-08-codex-phase1-hunter.md`
- `docs/plans/codex-prompts/2026-05-08-codex-email-sig-polish.md`

### Skills updated

- `skills/hunter_skill/SKILL.md` — added `force_fresh` pattern + `docker exec -d` harvest rule

### Memory written

- `feedback_codex_sandbox_blocks_git.md`
- `feedback_gate_cron_15min_not_60s.md`
- `feedback_sw_harvest_docker_exec_timeout.md`
- `feedback_studio_templates_sign_geolisted.md`
- `feedback_archive_files_historical_only.md`
- `project_email_queue_v2_state.md` (MEMORY_ARCHIVE)
- `project_harvest_state_2026-05-08.md` (MEMORY_ARCHIVE)

## Decisions made

- **Email queue: Path B (first-principles rewrite).** No 150 soft cap. No `replied` DB column. Drafts on-demand at send time. Send-rate-derived throughput (35 SW + 15 CW + 15 Studio = 65/day). Gmail-as-truth for replies (1h cache at draft time). 4h cron cycle. Multilingual OOO regex (EN + ES + FR). Reply classification Phase 3 (Haiku: interested/objection/OOO/unsubscribe → Telegram + CRM tag).
- **Archive files: historical reference only.** `templates/email/archive/cold_outreach_v1.py` has "Boubacar Barry" — left unfixed per Boubacar's explicit call. Grep rule violations with `| grep -v archive`.
- **Studio templates sign geolisted.co.** CW templates keep catalystworks.consulting. SW templates keep geolisted.co. Rule now locked in memory and SKILL.md.
- **Codex sandbox = edits only, main session = git ops.** Codex cannot write `.git/objects`. Pattern: Codex diffs, Claude commits + pushes.
- **Gate trigger manual when urgent.** Gate runs every 15 min daytime (not 60s). Manual trigger: `cd /root/agentsHQ && set -a && . .env && set +a && GATE_DATA_DIR=... python3 orchestrator/gate_agent.py`.
- **Cron switch deferred.** `scheduler.py` → `harvest_until_target` requires 3 successive days of 50/50. Day 1 in progress.

## What is NOT done (explicit)

- **Email queue v2 (drafter rewrite).** Full Plan v2 not written — stub only at `docs/plans/2026-05-09-email-queue-v2-frame.md`. /sankofa + /karpathy gates required before Codex.
- **Site-wide first-name scrub.** 8 files in `output/websites/catalystworks-site/` and `output/websites/boubacarbarry-site/`. Prompt written (provided in session). Separate branch `feature/first-name-scrub`.
- **SW harvest at 35/35.** Running detached in container at session close. SW=10/35 at last count. Telegram fires ✅ on complete. Check tomorrow AM.
- **Cron switch to harvest_until_target.** Deferred until 3 days of 50/50.
- **Reply scanner Phase 3 (reply classification).** Following week, separate branch after Phase 2 ships.
- **drive_publish audit on VPS.** 401 in sandbox. Run post-merge: `python -m orchestrator.drive_publish audit`.

## Open questions

- SW harvest: did it hit 35/35 tonight? Check Telegram or: `ssh root@72.60.209.109 "docker exec orc-crewai python3 -c 'from signal_works.harvest_until_target import _count_today_sw_with_email; print(_count_today_sw_with_email())'"`
- Plan v2 open questions (documented in stub): send_scheduler.py location, 4h cron extension path, Studio pipeline inclusion in v2, Phase 3 LLM cost, Telegram "interested" routing channel.

## Next session must start here

1. Check SW harvest result: `ssh root@72.60.209.109 "docker exec orc-crewai python3 -c 'from signal_works.harvest_until_target import _count_today_sw_with_email, _count_today_cw_with_email; print(\"SW:\", _count_today_sw_with_email(), \"CW:\", _count_today_cw_with_email())'"`
2. Write full Plan v2 for email queue drafter rewrite (from stub at `docs/plans/2026-05-09-email-queue-v2-frame.md`). Answer the 6 open questions first (grep send_scheduler.py, check cron entries).
3. Run /sankofa + /karpathy on Plan v2.
4. Hand Plan v2 to Codex (or implement directly — Codex sandbox blocked git in this session).
5. After Plan v2 ships + validated: wire cron switch (`scheduler.py` → `harvest_until_target`) as separate small PR.
6. Delegate site-wide first-name scrub to separate session (prompt already written in this session's chat).

## Files changed this session

```
signal_works/topup_cw_leads.py          (force_fresh param)
signal_works/harvest_until_target.py    (force_fresh=True call)
templates/email/studio_t1.py            (Boubacar Barry → Boubacar, geolisted.co)
templates/email/studio_t2.py            (geolisted.co)
templates/email/studio_t3.py            (geolisted.co)
templates/email/studio_t4.py            (geolisted.co)
skills/hunter_skill/SKILL.md            (force_fresh + docker exec -d rules)
docs/plans/2026-05-08-phase1-hunter-force-fresh.md          (NEW)
docs/plans/2026-05-08-email-signature-polish.md             (NEW)
docs/plans/2026-05-09-email-queue-v2-frame.md               (NEW stub)
docs/plans/archive/2026-05-08-hunter-email-queue-v1-superseded.md (NEW archived)
docs/plans/codex-prompts/2026-05-08-codex-phase1-hunter.md (NEW)
docs/plans/codex-prompts/2026-05-08-codex-email-sig-polish.md (NEW)
memory/feedback_codex_sandbox_blocks_git.md                 (NEW)
memory/feedback_gate_cron_15min_not_60s.md                  (NEW)
memory/feedback_sw_harvest_docker_exec_timeout.md           (NEW)
memory/feedback_studio_templates_sign_geolisted.md          (NEW)
memory/feedback_archive_files_historical_only.md            (NEW)
memory/project_email_queue_v2_state.md                      (NEW)
memory/project_harvest_state_2026-05-08.md                  (NEW)
memory/MEMORY.md                                            (4 new pointers)
memory/MEMORY_ARCHIVE.md                                    (2 new pointers)
```

## Session metrics

- Sankofa runs: 1 (plan v1 — drove Path B decision)
- Karpathy runs: 2 (Phase 1 Hunter: PASS, email-sig polish: PASS/SHIP)
- Branches merged: 2
- Commits: a91e2b0 + 578d66c
- CW validated: 15/15 ✅
- All 13 active templates render-check: PASS
