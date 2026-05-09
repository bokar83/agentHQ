# Session Handoff - Sankofa DEAD-PROJECT MODE + RW Daily Nudge - 2026-05-06

## TL;DR

Absorbed the pre-mortem technique from an X post by @itsolelehmann. Full absorb protocol ran (Phase 0-5, Sankofa council, Karpathy audit). Verdict: PROCEED — enhance skills/sankofa. Added DEAD-PROJECT MODE as a retrospective framing trigger (not a 6th voice — preserves odd-number structure). Demonstrated the mode live on the Reserve Works paper trading decision. Surfaced the missing daily trigger as the root failure mode. Fixed it: morning_runner.py Step 7 now sends an RW paper trade nudge via Telegram + email every weekday at 07:00 MT. Commit shipped to main.

## What was built / changed

- `skills/sankofa/SKILL.md` — DEAD-PROJECT MODE section added before Output Rules. Trigger: money/time/hire/launch/irreversible commitment, or explicit "premortem this". Frame shift: 6 months later, plan is dead, all 5 voices speak retrospective. Per-voice mandates defined.
- `signal_works/morning_runner.py` — Step 7 added (lines 261-278). Fires weekdays only. Sends RW nudge via `send_message()` (Telegram) + `send_email()` (bokar83@gmail.com). Non-fatal — logs warning on failure, never crashes runner.
- `skills/boub_voice_mastery/SKILL.md` + `skills/boub_voice_mastery/references/brand-spine-audit.md` — earned-insight gate rule + brand spine audit reference (from earlier today, same commit)
- `skills/ctq-social/SKILL.md` — long-form authority post pattern + 3-diagnostic test check (from earlier today)
- `skills/coordination/references/agent-delegation-pattern.md` — agent delegation pattern reference (from earlier today)
- `docs/reviews/absorb-log.md` — entry appended: `2026-05-06 | https://x.com/itsolelehmann/... | PROCEED | enhance skills/sankofa | continuous-improvement`
- `docs/reviews/absorb-followups.md` — follow-up appended: verify DEAD-PROJECT MODE on first high-stakes /sankofa run by 2026-06-06
- `memory/project_reserve_works_state.md` — DEAD-PROJECT MODE lesson + fix appended

## Decisions made

- **DEAD-PROJECT MODE = mode, not member.** Sankofa stays at 5 voices. Boubacar dislikes even numbers; 6th voice was rejected. Retrospective framing is a trigger that shifts ALL voices, not an additional voice.
- **RW paper trading needs a daily hook, not just a gate.** Gate requirement with no recurring mechanism = dead by week 6. morning_runner Step 7 is the fix. Fires every weekday before Boubacar opens email.
- **Prospective hindsight is real leverage even in LLMs.** Not because Claude has ego (it doesn't), but because retrospective frame forces committed narrative reasoning vs hedged probabilistic reasoning — different output class.

## What is NOT done (explicit)

- morning_runner Steps 4b (Studio Apollo topup) and Step 6 (Studio sequence) still present — marked for removal in a previous session (SW+Studio merged 2026-05-05). Not touched this session; defer to next cleanup pass.
- DEAD-PROJECT MODE not yet verified in production — Karpathy P4 WARN. First high-stakes /sankofa run = verification checkpoint.
- VPS deploy not run this session. Code changes are volume-mounted so they go live on next `git pull + docker compose up -d orchestrator`. RW nudge fires first time at 07:00 MT tomorrow (2026-05-07).

## Open questions

- Steps 4b/6 in morning_runner: when does Boubacar want them removed? Low risk, low urgency — confirm before next morning_runner session.
- DEAD-PROJECT MODE naming: "DEAD-PROJECT MODE" is descriptive but blunt. Boubacar may want to rename it. No action needed unless he asks.

## Next session must start here

1. Deploy to VPS: `ssh root@72.60.209.109 "cd /root/agentsHQ && git pull && docker compose up -d orchestrator"` — activates Step 7 RW nudge.
2. Confirm first RW nudge fired (check Telegram + bokar83@gmail.com) on 2026-05-07 morning.
3. Address any open items from morning_runner Steps 4b/6 removal (SW+Studio merge cleanup).

## Files changed this session

```
skills/sankofa/SKILL.md                          (DEAD-PROJECT MODE added)
signal_works/morning_runner.py                    (Step 7 RW nudge)
skills/boub_voice_mastery/SKILL.md               (earned-insight gate)
skills/boub_voice_mastery/references/brand-spine-audit.md  (new)
skills/ctq-social/SKILL.md                       (long-form authority pattern)
skills/coordination/references/agent-delegation-pattern.md (new)
skills/local_crm/crm_tool.py                     (minor fix)
docs/reviews/absorb-log.md                       (entry appended)
docs/reviews/absorb-followups.md                 (follow-up appended)
memory/project_reserve_works_state.md            (lesson appended)
docs/handoff/2026-05-06-sankofa-dead-project-mode-absorb.md (this file)
```
