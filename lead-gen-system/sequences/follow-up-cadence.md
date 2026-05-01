# Follow-Up Cadence - 8-Touch Cross-Channel (Enhancement)

**Type:** Enhancement spec for `skills/outreach/sequence_engine.py`.
**Hormozi alignment:** YES. Brings current 4-touch (SW) / 5-touch (CW) email-only sequences up to Hormozi's 8-touch cross-channel floor.
**Status:** PROPOSED. Do not modify the sequence engine until Boubacar says ship-it.

---

## Why This Spec

Phase 2 audit, artifact #19 (Severity 5): single-channel funnel. Current sequence engine is email-only. Hormozi's follow-up rule: minimum 8 touches across channels. The sequence engine has solid mechanics - what's missing is the LinkedIn DM and phone-call legs interleaved with the email touches.

**This is an enhancement, not a replacement.** The existing day-cadence (Day 0/3/7/12 SW; Day 0/6/9/14/19 CW) stays. We add cross-channel touches in between, plus reactivation logic for non-converters.

---

## The 8-Touch Sequence (Catalyst Works)

| # | Day | Channel | Touch type | Action |
|---|---|---|---|---|
| 1 | 0 | Email | T1 - Hook + Big Fast Value | Send enhanced T1 (per `cold-email-v1.md`) |
| 2 | 3 | LinkedIn DM | Connection + reference T1 | Send connection request with one-line reference to email observation. NO immediate ask. |
| 3 | 6 | Email | T2 - SaaS Audit PDF | Existing `cw_t2.py` (the value-drop). Ship as-is. |
| 4 | 9 | Email | T3 - Pattern observation + new value | Enhanced T3 (per separate diff below) |
| 5 | 13 | LinkedIn engagement | Comment publicly on their recent post | Operator-driven: 30 seconds of real engagement. Not a bot. |
| 6 | 14 | Email | T4 - Pattern recognition + soft proof | Enhanced T4 (per separate diff below) |
| 7 | 19 | Email | T5 - Breakup + final value drop | Enhanced T5 (per separate diff below) |
| 8 | 30 | Phone or voicemail | Pattern interrupt | Operator-driven for HIGHEST-tier leads only. ICP filter applies. |

**Total: 8 touches across 30 days. 5 email + 2 LinkedIn + 1 phone.**

---

## The 8-Touch Sequence (Signal Works)

| # | Day | Channel | Touch type | Action |
|---|---|---|---|---|
| 1 | 0 | Email | T1 - AI Visibility Score email | Existing `email_builder.py` HTML version (per Phase 2 audit, artifact #8) |
| 2 | 2 | LinkedIn DM | Connection + score line | Connection request: "Sent you the AI score breakdown for [biz] earlier. Curious what you found when you ran the test on ChatGPT." NO ask. |
| 3 | 3 | Email | T2 - Re-anchor demo | Existing `sw_t2.py` (or enhance per separate spec) |
| 4 | 6 | LinkedIn engagement | Comment on a recent post | Operator-driven. Niche-specific (rooftop drone shot for roofers; care-team photo for dentists). |
| 5 | 7 | Email | T3 - Niche pattern observation | Existing `sw_t3.py` |
| 6 | 12 | Email | T4 - Final demo CTA | Existing `sw_t4.py` |
| 7 | 14 | Phone | Cold call | Operator-driven. Use script from `signal_works_plan.md` ("Cold Call" section). |
| 8 | 21 | Email | Breakup + value drop | NEW - recommend a Hormozi-style breakup with one final value drop (a specific 4-line robots.txt fix tailored to their actual site). |

**Total: 8 touches across 21 days. 5 email + 2 LinkedIn + 1 phone.**

---

## Implementation Plan

### Phase A: Spec only (this session, COMPLETE)
- Document the 8-touch design.
- No code changes.

### Phase B: Manual cross-channel layer (next 7 days, Boubacar-driven)
- For each new lead added to the queue: Boubacar manually sends LinkedIn touches at Day 2 + Day 6 + Day 13.
- LinkedIn touches do NOT run through the sequence engine. They are operator actions.
- Track in the leads table: `linkedin_touch_1_at` (timestamp), `linkedin_touch_2_at`, `linkedin_touch_3_at`.
- This is the falsifiable test: do LinkedIn touches improve reply rate over email-only? Compare 100-lead batch with vs. without.

### Phase C: Automate (only after Phase B data)
- If LinkedIn touches improve reply rate by ≥30% over the 100-lead batch, automate them via:
  - Phantombuster + LinkedIn (if Boubacar's account permits)
  - OR Playwright + saved session (per memory's `reference_skool_access.md` pattern)
- If LinkedIn touches do NOT improve reply rate, kill the channel and add no automation. Hormozi's "More" axis is data-driven.

---

## Reactivation Logic (the missing piece)

Currently, when a lead hits T5 + no reply → `opt_out = TRUE` → vanishes. Hormozi's rule: keep the list warm.

**Spec (additive):**

```
After T8 (phone or final email):
  - Mark sequence_status = 'completed_no_reply' (NOT opt_out)
  - opt_out remains FALSE (they didn't ask to leave)
  - Move to reactivation queue

Quarterly reactivation:
  - Every 90 days, send Template B (warm reactivation, per warm-reactivation-v1.md)
  - Pure value drop, no ask
  - If they reply: re-enter the 8-touch sequence at T1
  - If 4 consecutive quarterly drops produce no reply (1 year): set sequence_status = 'dormant' and stop
```

**Database changes:**
- `leads.sequence_status` (TEXT) - 'active' | 'completed_no_reply' | 'replied' | 'booked' | 'closed' | 'dormant' | 'opt_out'
- `leads.last_reactivation_at` (TIMESTAMP)
- `leads.reactivation_count` (INTEGER, default 0)

---

## Triggers and Behaviors (the smarter follow-up)

Hormozi's rule: every touch must add new value. Static day-based cadence misses behavioral signal. Layer these triggers on top of the day-based system:

| Trigger | Action |
|---|---|
| Lead opens email but doesn't reply | Pull-in: send next email 1 day earlier than scheduled (interest signal) |
| Lead clicks Calendly but doesn't book | Operator-alert: send a manual 1-line "saw you looked at the calendar - anything I can answer that's holding you up?" within 24 hours |
| Lead replies positively but doesn't book | Operator-alert: switch to manual mode, ACA framework, no automated follow-up |
| Lead replies "not now / not interested" | Move to reactivation queue immediately, skip remaining touches |
| Lead replies "unsubscribe" / "STOP" | Set opt_out = TRUE, halt all touches |
| Lead bounces | `bounce_scanner.py` already handles |

**Implementation note:** the trigger layer requires email-tracking (open + click signals). Existing infrastructure may not have this. Phase C scope; not Phase B.

---

## Success Criteria

| Metric | Target | Floor |
|---|---|---|
| Cross-channel reply lift over email-only | ≥30% over 100-lead batch | ≥10% |
| LinkedIn DM accept rate | ≥60% | ≥40% |
| LinkedIn DM reply rate (after accept) | ≥15% | ≥8% |
| Phone connect rate (HIGHEST-tier only) | ≥30% | ≥15% |
| Reactivation reply rate (Q1 of dormancy) | ≥5% | ≥2% |

If LinkedIn fails the floor: kill the channel, don't automate it.
If phone fails the floor: keep it for HIGHEST-tier only, don't expand.
If reactivation fails the floor: increase the value content; don't increase frequency.

---

## Anti-Patterns Refused

- Automation before data. (Manual run for the first 100 leads. Then evaluate.)
- LinkedIn DM before connection. (Connection requires acceptance; DMs to non-connections are limited and look spammy.)
- Same content across channels. (Each channel needs its own framing. Email pattern ≠ LinkedIn pattern ≠ phone pattern.)
- Phone calls without prior email + LinkedIn. (Phone is touch 7 or 8, never touch 1. Hormozi's activation order applies within the sequence too.)
- Reactivation sends with an ask. (Reactivation is pure value drop. No ask = no resistance.)

---

## Output Contract

- ICP: same as upstream (CW or SW). ✓
- Channel: 3 channels (email + LinkedIn + phone) per sequence. ✓
- Lead magnet: existing per brand. ✓
- Hook: existing (T1 hook applies to whole sequence). ✓
- Offer: existing per brand. ✓
- CTA: per touch (one CTA per touch, never doubled). ✓
- Follow-up plan: 8 touches over 21-30 days. ✓
- Success criteria: explicit floors above. ✓
- Anti-patterns refused: 5 listed above. ✓
