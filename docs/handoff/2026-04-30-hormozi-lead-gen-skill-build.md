# Session Handoff: Hormozi Lead-Gen Skill Build (2026-04-30)

## TL;DR

Built the `hormozi-lead-gen` skill end-to-end across 6 phases: research, current-state audit, decision matrix (29/50, MERGE verdict), the skill itself (455 lines, brand-agnostic), 7 Phase-5 enhancement specs, and the review-gate hand-off. Two Sankofa Council passes plus a Karpathy audit gated the work. Boubacar reviewed Template A on localhost preview, caught dash and ICP-bracket issues, accepted the 24-hour falsifier test (3 warm DMs by hand) as the actual next move, and is running with that now. No production files modified, no commits, no live sequences halted.

## What was built / changed

### New files (created this session)

**Skill:**
- [skills/hormozi-lead-gen/SKILL.md](../../skills/hormozi-lead-gen/SKILL.md) - 455 lines, brand-agnostic Hormozi procedure

**Research (Phases 1-3):**
- [research/hormozi-research-notes.md](../../research/hormozi-research-notes.md) - 606 lines, source-anchored Hormozi reference
- [research/current-state-audit.md](../../research/current-state-audit.md) - 523 lines, 25-artifact audit
- [research/decision-matrix.md](../../research/decision-matrix.md) - 233 lines, MERGE verdict locked

**Lead-gen system (Phase 5 specs, all PROPOSED, no commits):**
- [lead-gen-system/README.md](../../lead-gen-system/README.md) - START HERE navigation
- [lead-gen-system/templates/cold-email-v1.md](../../lead-gen-system/templates/cold-email-v1.md) - CW T1 enhancement DIFF (VE 5.25 → 6.75)
- [lead-gen-system/templates/cw-t3-t4-t5-diffs.md](../../lead-gen-system/templates/cw-t3-t4-t5-diffs.md) - 3 surgical CW diffs
- [lead-gen-system/templates/warm-reactivation-v1.md](../../lead-gen-system/templates/warm-reactivation-v1.md) - NEW warm channel kit (Template A + Template B + 10-step process)
- [lead-gen-system/templates/lead-magnet-brief-template.md](../../lead-gen-system/templates/lead-magnet-brief-template.md) - Margin Bottleneck Diagnostic spec (build separately)
- [lead-gen-system/sequences/follow-up-cadence.md](../../lead-gen-system/sequences/follow-up-cadence.md) - 8-touch cross-channel design
- [lead-gen-system/scripts/objection-handling.md](../../lead-gen-system/scripts/objection-handling.md) - CW + SW Hormozi-aligned objection bank
- [lead-gen-system/metrics/success-criteria.md](../../lead-gen-system/metrics/success-criteria.md) - floors + LTGP/CAC math

**Hand-off:**
- [review-gate.md](../../review-gate.md) - Phase 6 review gate, 7 open questions, 24-hour falsifier locked

**Visual preview (permanent):**
- [deliverables/hormozi-lead-gen/previews/warm-reactivation-template-a.html](../../deliverables/hormozi-lead-gen/previews/warm-reactivation-template-a.html) - Template A rendered as recipient view + side-rail explainer

### Memory written

**MEMORY.md (operational rules, indexed):**
- Em-dash rules consolidated: [never anywhere · grep before claiming done · LLM JSON scrub] - single line
- Warm outreach rules consolidated: [channel #1 before cold · drop firm-size brackets · "by hand" = type individually] - single line
- Reference: [Hormozi lead-gen skill location and scope](reference_hormozi_lead_gen_skill.md)

**MEMORY_ARCHIVE.md (project state):**
- [Hormozi Lead-Gen Skill Build (2026-04-30)](project_hormozi_lead_gen_2026_04_30.md) - full session state under Active Projects

**Memory files (full content):**
- `reference_hormozi_lead_gen_skill.md`
- `feedback_warm_outreach_first_hormozi_activation_order.md`
- `feedback_drop_icp_brackets_in_warm_outreach.md`
- `feedback_by_hand_means_typing_individually.md`
- `feedback_em_dash_first_pass_audit_required.md`
- `project_hormozi_lead_gen_2026_04_30.md`

### Production state (UNCHANGED)

- `templates/email/cold_outreach.py` - UNCHANGED (CW T1 in production)
- `templates/email/cw_t2.py`, `cw_t3.py`, `cw_t4.py`, `cw_t5.py` - UNCHANGED
- `templates/email/sw_t1.py`, `sw_t2.py`, `sw_t3.py`, `sw_t4.py` - UNCHANGED
- `signal_works/email_builder.py` - UNCHANGED
- `signal_works/morning_runner.py` - UNCHANGED (still running daily at 07:00 MT)
- `skills/outreach/sequence_engine.py` - UNCHANGED
- VPS systemd timer - UNCHANGED, CW auto-send still ON

## Decisions made

1. **Verdict: MERGE not REPLACE.** Score 29/50. CW/SW cold-email infrastructure is Hormozi-grade structurally; gap is breadth (no warm channel, no CW lead magnet, single-channel funnel). HIGH confidence.
2. **Seed-email handling: keep in-flight.** CW T1 batch launched 2026-04-29 rides out its 19-day sequence. Phase 5 enhancement diffs apply to leads added 2026-05-12+. Reasoning: sender-reputation cost of halt-and-relaunch > brand cost of finishing a 6/10 sequence.
3. **Skill scope: 455 lines, 2 worked examples (CW, SW).** Sankofa Pass 1 cut original 1200-line spec by 60%. Hypothetical-future-venture worked example dropped as premature abstraction.
4. **Phase 5 = 3 enhancement diffs + 2 new files (warm kit + CW magnet brief), per Boubacar's "enhance > create new" rule.** Greenfield only when no equivalent exists.
5. **CW T1 diff ships at VE 6.75/10 (under 7.0 floor)** with explicit retest-gate justification. Path to 7.0: real client name once first paid client closes.
6. **Drop firm-size brackets ($5M-$50M) from warm reach-out copy.** Reads as cold-email screening; widens addressable response. Rule applies to warm only; cold/Apollo can keep brackets.
7. **24-hour warm-DM falsifier is the binding test.** 3 messages, by hand, on whatever channel matches the prior relationship. Outcome shapes whether next session is execution-only, system+execution, or pivot to cold lift test.

## What is NOT done (explicit)

- **No CW T1/T3/T4/T5 production edits** - diffs are spec'd in markdown, awaiting Boubacar's "ship it" before any commit.
- **No CW auto-send halt** - auto-send still ON, in-flight batch ongoing.
- **Margin Bottleneck Diagnostic web tool NOT BUILT** - only the brief exists. Build is a separate 1-2 day focused session, gated on warm-DM falsifier outcome.
- **AI Visibility Score NOT shipped as public web tool** - Sankofa Expansionist flagged as missed leverage; not scoped here.
- **8-touch cross-channel sequence engine code NOT modified** - design spec only; manual LinkedIn layer is Boubacar-driven first.
- **Reactivation logic (`leads.sequence_status` + quarterly drops) NOT implemented** - design only.
- **NotebookLM never auth-refreshed** - manual `nlm login` still required.
- **`workspace/warm-reactivation-preview/` folder still exists as duplicate.** Tried to `rm -rf` it; permission was denied. Canonical preview is at `deliverables/hormozi-lead-gen/previews/`. Workspace copy is harmless but redundant; clean up next session if desired.
- **AI Governance Field Guide work** Boubacar showed at the end is a SEPARATE project I didn't touch - has its own build pipeline at `workspace/articles/2026-04-30-ai-governance-field-guide-assets/`.

## Open questions

From [review-gate.md](../../review-gate.md), 7 items still need Boubacar's answer before any production change ships:

1. MERGE verdict: confirm or override (default: confirm)
2. Seed-email call: keep in-flight + swap on 2026-05-12 vs halt-and-swap-now
3. CW T1 diff at 6.75/10: ship with retest-gate vs hold for 7.0+ with real client name
4. Phase 5 file count: keep all 7 vs consolidate `success-criteria.md` + `objection-handling.md`
5. **CRITICAL: SW HTML email vs `sw_t1.py` ambiguity** - which is the live SW T1 in production? Audit Severity 4. Cannot ship SW changes without clarity.
6. AI Visibility Score productization: ship as public web tool at signal-works.com/score within 7 days?
7. Margin Bottleneck Diagnostic v1: schedule a focused build session?

**6 low-confidence items** also flagged in review-gate (Apollo CW ICP filter alignment, 8 CW lenses location, Discovery Call OS v2.0 location, in-flight batch reply data, LinkedIn DM accept rate floor, AI Visibility Score licensability).

## Falsifier test status (UPDATED end of session)

**3 of 3 warm DMs sent on 2026-04-30 via LinkedIn DM.** Full log at [lead-gen-system/sent/2026-04-30-warm-reactivation-batch-1/](../../lead-gen-system/sent/2026-04-30-warm-reactivation-batch-1/).

| # | Recipient | LinkedIn |
|---|---|---|
| 1 | Brody Horton | https://www.linkedin.com/in/brodyhorton/ |
| 2 | Rod Lambourne | https://www.linkedin.com/in/rod-lambourne-21574133/ |
| 3 | Rich Hoopes | https://www.linkedin.com/in/rich-hoopes/ |

All 3 messages used real, specific personalization anchors (not template fill). Replies pending. Outcome diagnostic to be applied at 2026-05-01 EOD per the table in review-gate.md.

## Next session must start here

1. **Ask Boubacar what came back.** "Any replies from Brody, Rod, or Rich?" Update `lead-gen-system/sent/2026-04-30-warm-reactivation-batch-1/outcomes.md` with whatever did or didn't happen.
2. **Read `[project_hormozi_lead_gen_2026_04_30.md](../../../../C:/Users/HUAWEI/.claude/projects/d--Ai-Sandbox-agentsHQ/memory/project_hormozi_lead_gen_2026_04_30.md)**` in memory to recover full state.
3. **Per the outcome:**
   - 0 replies: do NOT build more skill scaffolding. Audit personalization depth + list quality. Either pivot to cold lift test or expand warm to 10 more by-hand sends.
   - 1+ reply (no books): scale warm to 100 names + start building Margin Bottleneck Diagnostic v1.
   - 1+ booked call: run Discovery Call OS v2.0, capture the close. The build queue waits.
4. **If still no answer on the 7 open questions:** ask question #5 first (SW production ambiguity), it's the only one blocking Phase 5 ship.

## Files changed this session

``
NEW:
├── skills/hormozi-lead-gen/SKILL.md
├── research/
│   ├── hormozi-research-notes.md
│   ├── current-state-audit.md
│   └── decision-matrix.md
├── lead-gen-system/
│   ├── README.md
│   ├── templates/
│   │   ├── cold-email-v1.md
│   │   ├── cw-t3-t4-t5-diffs.md
│   │   ├── warm-reactivation-v1.md
│   │   └── lead-magnet-brief-template.md
│   ├── sequences/follow-up-cadence.md
│   ├── scripts/objection-handling.md
│   └── metrics/success-criteria.md
├── deliverables/hormozi-lead-gen/previews/warm-reactivation-template-a.html
├── review-gate.md
└── docs/handoff/2026-04-30-hormozi-lead-gen-skill-build.md  (this file)

MEMORY `(C:/Users/HUAWEI/.claude/projects/d--Ai-Sandbox-agentsHQ/memory/):`
├── reference_hormozi_lead_gen_skill.md             (NEW)
├── feedback_warm_outreach_first_hormozi_activation_order.md  (NEW)
├── feedback_drop_icp_brackets_in_warm_outreach.md  (NEW)
├── feedback_by_hand_means_typing_individually.md   (NEW)
├── feedback_em_dash_first_pass_audit_required.md   (NEW)
├── project_hormozi_lead_gen_2026_04_30.md          (NEW)
├── MEMORY.md                                        (UPDATED, 199/200 lines)
└── MEMORY_ARCHIVE.md                                (UPDATED, +1 active project)

WORKSPACE (transient, can be cleaned next session):
└── workspace/warm-reactivation-preview/             (duplicate of deliverables copy; tried to rm, permission denied)

UNCHANGED (production):
- All templates/email/*.py
- signal_works/* (including morning_runner.py)
- skills/outreach/sequence_engine.py
- VPS systemd timer + .env
``

---

NEXT SESSION PROMPT - copy this into the new tab:

Continue from `docs/handoff/2026-04-30-hormozi-lead-gen-skill-build.md`.

Context:
- 6-phase Hormozi lead-gen skill build shipped 2026-04-30. Skill at `skills/hormozi-lead-gen/SKILL.md`. 7 Phase-5 enhancement specs at `lead-gen-system/`. No production files touched. No commits. CW auto-send still ON, in-flight batch from 2026-04-29 ongoing.
- Boubacar accepted the 24-hour warm-DM falsifier test: 3 messages from his 1st-degree network, by hand. Outcome gates everything else (execution-only vs system+execution vs cold lift test vs Discovery Call run).
- 7 open questions in `review-gate.md` blocking Phase 5 ship. Most critical: which SW T1 is in prod - `sw_t1.py` plain-text or `email_builder.py` HTML version?

First actions:
1. Ask Boubacar: "Did you send the 3 warm DMs? What happened?" Read `project_hormozi_lead_gen_2026_04_30.md` for full state.
2. Match the outcome to the table in `review-gate.md` to set session priority.
3. If 1+ reply came back: ask whether to scale warm to 100 names OR build the Margin Bottleneck Diagnostic v1 web tool (1-2 days) OR ship AI Visibility Score as public web tool first.
4. If 0 replies or 0 sent: do NOT build more skill scaffolding. Diagnose volume vs personalization first.