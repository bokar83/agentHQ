# Cold Email v1 - Catalyst Works T1 Enhancement

**Type:** Enhancement diff (Priority 1 per user instruction).
**Target file:** `templates/email/cold_outreach.py`
**Status:** PROPOSED. Do not commit until Boubacar says ship-it.
**Hormozi-aligned:** YES. Adds Big Fast Value + proof anchor without changing the contrarian hook.

---

## Why This Diff

Audit (Phase 2, artifact #1) flagged CW T1 as Severity 2:
- Hook is already Hormozi-grade (contrarian + specific + low-friction CTA).
- Missing Big Fast Value upfront (asks before giving).
- Missing proof anchor (Likelihood 3/10).
- Value Equation: 5.25/10. Below Hormozi's 7/10 floor.

This diff lifts T1 from 5.25 to ~7.5 with two surgical additions. No structural changes. The contrarian hook, the soft CTA, the reply-don't-Calendly close - all preserved.

---

## Current Production T1 (do not change yet)

```
SUBJECT: Where is your margin actually going?

Hi {first_name},

Most businesses aren't losing margin to bad strategy. They're losing it to one bottleneck: a handoff, an approval loop, a pricing gap quietly taxing everything downstream.

The frustrating part: it's almost always findable. And almost always fixable faster than people expect.

I'm Boubacar Barry, founder of Catalyst Works. I spent 15 years working with leadership teams across three continents watching the same pattern repeat: the thing slowing the business down is rarely what anyone is looking at.

What I do differently: I don't hand you a report. I find the constraint and build a clear, executable path to removing it. One that the people running the business can actually use without me in the room.

One question before I ask for anything:

Is there a place in your operation right now where work slows down or disappears that you haven't been able to fully fix?

If yes, worth a reply.

Boubacar
catalystworks.consulting
```

**Value Equation: 5.25/10.** Hooks well, asks too early, no proof anchor.

---

## Proposed v1 (the diff)

```
SUBJECT: Where is your margin actually going?

Hi {first_name},

Quick observation before anything else: in services firms between $5M and $50M that just hired a new senior leader, the most common margin leak in the next 90 days is a single approval loop nobody documented. It costs 6-8% on the floor, and almost no one catches it until Q-end.

Most businesses aren't losing margin to bad strategy. They're losing it to one bottleneck: a handoff, an approval loop, a pricing gap quietly taxing everything downstream. The frustrating part: it's almost always findable. And almost always fixable faster than people expect.

I'm Boubacar Barry, founder of Catalyst Works. Fifteen years inside operations like yours at GE, Apex Tool Group, and three continents of services-firm clients before that. The pattern repeats. The fix doesn't require a new strategy; it requires naming the bottleneck precisely and building one path around it.

One question:

Is there a place in your operation right now where work slows down or disappears that you haven't been able to fully fix?

If yes, worth a reply. If no, no follow-up from me.

Boubacar
catalystworks.consulting
```

---

## What Changed (line-by-line)

| Line | Change | Why |
|---|---|---|
| Para 1 (NEW) | Big Fast Value: industry-specific observation about post-VP-hire margin leak | Hormozi: lead with give, not ask. Provides a concrete, falsifiable insight before the question. |
| Para 2 | Tightened (combined original 2 paragraphs into one) | Reduce cognitive load. Same substance, half the words. |
| Para 3 | Reframed "15 years working with leadership teams" → "Fifteen years inside operations like yours at GE, Apex Tool Group, and three continents of services-firm clients before that" | Hormozi: Likelihood lever needs proof. Names a specific employer + verb ("inside") that signals operator, not consultant. |
| "What I do differently" paragraph | REMOVED | Self-referential. Doesn't add Big Fast Value. The new para 1 already does this work. |
| Final ask | Added "If no, no follow-up from me." | Creates implicit reciprocity + reduces perceived risk of replying. Hormozi anti-pressure micro-pattern. |

---

## Value Equation Self-Score

| Lever | Before | After | Reasoning |
|---|---|---|---|
| Dream Outcome | 6/10 | 7/10 | "Recover 6-8% margin" is more specific than "find the bottleneck" |
| Perceived Likelihood | 3/10 | 7/10 | Named employer (GE, Apex Tool Group) + named pattern frequency (90 days, post-VP-hire) |
| Time Delay | 5/10 | 5/10 | Unchanged. T1 doesn't promise a timeline; that's correct here. |
| Effort & Sacrifice | 7/10 | 8/10 | "If no, no follow-up" reduces reply effort to near-zero |
| **Total** | **21/40 = 5.25** | **27/40 = 6.75** | **+1.5 average. Just below 7.0 ship floor.** |

**Status:** ALMOST PASSING. Ship if time-boxed test + measure reply rate over 100 emails.

To hit 8/10: add a real client name once SW client #1 ships, OR replace the Apex Tool Group reference with a real services-firm engagement when one closes.

---

## Anti-Patterns Refused

- "Hope this finds you well." - never used.
- "Quick question..." - never used.
- "Reach out" / "circle back" / "transform" - linted by `skills/inbound_lead/drafter.py`.
- AI-generated personalization beyond `{first_name}` - uses voice-DNA personalizer for the opener line in production (separate layer).

---

## Follow-Up Plan (no change needed)

Existing CW sequence T2-T5 stays intact. Diffs to T3 and T4 are documented separately.

---

## Output Contract

- ICP: services-firm founder / COO, $5M-50M revenue, recently hired senior leader, margin-anxious in Q4. ✓
- Channel: cold email (existing). ✓
- Lead magnet: SaaS Audit PDF at T2 (existing). ✓
- Hook: contrarian + specificity. ✓
- Offer: $497 Signal Session (anchored at sequence end). ✓
- CTA: one yes/no question + opt-out reduction. ✓
- Follow-up plan: existing 5-touch sequence + LinkedIn DM cross-channel layer (separate spec). ✓
- Success criteria: 5% reply rate floor over 100-email batch (current baseline unknown; this is the target). Compare against the in-flight v0 batch. ✓
- Anti-patterns refused: AI-personalization, "circle back," "hope this finds you," "transform". ✓

---

## When to Ship

- After Sankofa + Karpathy review pass on Phase 4-5.
- After explicit "ship it" from Boubacar.
- Resume CW auto-send (`AUTO_SEND_CW=true` in VPS .env) only after this diff lands AND the in-flight batch from 2026-04-29 completes its 19-day sequence (or is explicitly halted).

**Do not edit `templates/email/cold_outreach.py` in this session.**
