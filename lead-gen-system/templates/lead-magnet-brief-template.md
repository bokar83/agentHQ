# Catalyst Works Lead Magnet Brief - "Margin Bottleneck Diagnostic"

**Type:** New artifact (Priority 2; clears the bar because no CW lead magnet exists today).
**Hormozi alignment:** YES. Type = Reveal Problem (Diagnosis). Mirrors what SW already has (AI Visibility Score), now built for CW.
**Status:** PROPOSED. Do not build the PDF until Boubacar says ship-it.

---

## Why This Is Necessary

Phase 2 audit, artifact #20: CW has no lead magnet. SW has the AI Visibility Score (Hormozi-grade). CW has cold-email + SaaS Audit value-drop, but no public-facing magnet that would let a stranger find Boubacar, opt-in, and become an engaged lead without a cold touch first.

This brief is a 7-step Hormozi compliance check for a "Margin Bottleneck Diagnostic" - a 5-question scorecard that surfaces a services-firm operator's hidden constraint. It serves three purposes:

1. **Pre-cold lead magnet:** placed on catalystworks.consulting as the primary CTA. Strangers take it; Boubacar gets emails.
2. **Cold-email upgrade:** linked at T2 as a richer Big Fast Value than the current SaaS Audit PDF.
3. **Discovery call seed:** the diagnostic results become the first paragraph of the engagement brief in `skills/engagement-ops/SKILL.md`.

---

## The 7-Step Hormozi Compliance Check

### Step 1: Figure out the problem (narrow AND meaningful)

**The problem:** services-firm operators ($5M-50M) cannot name the specific operational bottleneck eating their margin. They feel it. They don't have language for it.

**Why it's narrow:** ONE problem (constraint identification). Not "your business is broken."

**Why it's meaningful:** Hormozi's "feels obligated to pay" test - an operator with a $30M services firm who walks away with one specific named bottleneck would happily pay $497 for the same insight in person.

---

### Step 2: Figure out how to solve it (Reveal Problem type)

**Type:** Reveal Problem (Diagnosis).

**Mechanic:** 5-question scorecard. Each question maps to one of the 8 Catalyst Works diagnostic lenses (Theory of Constraints, Lean, etc.). The output is:
- A 0-100 score (overall margin-leak risk)
- The single highest-leakage lens out of the 8
- One specific named bottleneck pattern that lens predicts

**The 5 questions (draft):**

1. "What was the last quarter where you missed a margin target you'd planned for? Open-ended."
2. "When a project goes over budget, what's the most common reason? (Pick one: scope creep / approval bottleneck / resource conflict / pricing decision / delivery handoff)"
3. "How many people sign off on a customer pricing exception?" (Number input)
4. "When a senior leader leaves or joins, how long until the team's cadence stabilizes?" (Pick one: <2 weeks / 2-8 weeks / 2-6 months / 6+ months / never tracked)
5. "What's the one bottleneck you've been meaning to fix but haven't?" (Open-ended)

**Scoring logic:** Each answer maps to lens-specific risk weights. Highest-weighted lens = primary diagnostic. Output is a one-paragraph diagnosis + one specific named pattern + one CTA to book a Signal Session for the full diagnostic.

---

### Step 3: Figure out how to deliver it (Software type)

**Delivery:** Web tool. Not a PDF. Not an email questionnaire.

**Why software:** Hormozi's effort-and-sacrifice rule. A PDF requires download + manual scoring + interpretation. A web tool delivers a result in 90 seconds.

**Tech:** Static HTML + JS form on catalystworks.consulting/diagnostic. Email capture gates the result. Submits to Supabase `lead_magnet_responses` table. Email auto-fires within 60 seconds with the full report.

**Build effort:** 1-2 days for v1 (no design system; ship ugly first). Use existing `skills/inbound_lead/drafter.py` for the email template.

---

### Step 4: Test the name (name the SOLUTION, not the format)

**NOT:** "Free Bottleneck Diagnostic" (names the format)
**NOT:** "5-Question Margin Scorecard" (names the format)

**TRY:**
- "The Margin Leak Locator"
- "Where's Your 6-8% Going?"
- "The 90-Second Operations Diagnostic"
- "The One Bottleneck That's Costing You This Quarter"

**Test:** put 4 names into a 1-day LinkedIn poll on Boubacar's profile. Highest engagement wins. Hormozi's "Better" axis: data over taste.

**Default for v1:** "The 90-Second Operations Diagnostic." Safe, specific, time-bound. Replace after the test.

---

### Step 5: Make it easy to consume (under 5 minutes)

**Target:** 90 seconds to complete. 60 seconds for the email to arrive. ~3 minutes to read the report.

**Friction reductions:**
- 5 questions only. Not 10. Not 20.
- 4 of 5 are multiple-choice or numeric. One open-ended.
- No login. No download. Email gate at submit.
- Mobile-first. Half of LinkedIn traffic is mobile.

---

### Step 6: Make it darn good (overdeliver)

**The report (auto-generated email) must include:**

- **The score:** 0-100, with breakdown by lens.
- **The primary diagnostic:** one specific named pattern (e.g., "Hidden Approval Loop in Pricing Exceptions"). Written in the operator's domain language, not consultant jargon.
- **The leak estimate:** "Operators with this pattern typically lose 5-9% margin in Q4." Cite the source if real; mark "general benchmark" if not.
- **The next 3 questions:** what to investigate first to verify the diagnosis. Not "book a call." Actual investigation steps.
- **The 1-week experiment:** one tactical thing the operator can try without you. Hormozi's "feels obligated to pay" - if they can solve it with the experiment, they don't need you. If they can't, they want the full diagnostic.
- **The Signal Session CTA:** anchored at $497, time-bound to "this month."

**Pass test:** would an operator forward this report to their COO? If yes, it's overdelivering. If no, it's a brochure.

---

### Step 7: Make it easy for them to ask for more (clear CTA)

**The report ends with this CTA block:**

```
If the diagnosis named the right pattern and the experiment didn't fully fix it,
the next step is the 90-minute Signal Session.

You leave with:
- One named bottleneck (more specific than this report)
- The mechanism behind it (why it persists)
- A 90-day plan to remove it (executable without me in the room)

$497. 3 sessions per month. Confirmation within 24 hours.

[Book Signal Session]
```

**Anchored. Time-bound. Specific. One action.**

---

## Value Equation Self-Score

| Lever | Score | Reasoning |
|---|---|---|
| Dream Outcome | 8/10 | "Find the bottleneck eating 6-8% of your margin" - specific, in operator language |
| Perceived Likelihood | 6/10 | Diagnostic logic is real (8 lenses); proof improves once first paid client closes |
| Time Delay | 9/10 | 90 seconds to score, 60 seconds to email, 3 minutes to read |
| Effort & Sacrifice | 9/10 | 5 questions, no signup, mobile-friendly |
| **Total** | **32/40 = 8.0** | **PASS. Production-grade.** |

---

## Anti-Patterns Refused

- Multi-problem magnet (would solve "all margin leaks" - too broad). NO.
- Format-named magnet ("PDF Audit"). NO.
- Email-gated download with no immediate value (the score must show on-screen before the email gate completes). NO.
- "Book a call to learn more" instead of a substantive report. NO.
- Mock client quotes ("Sarah from XYZ Corp said..."). NO. Use real or no quote.

---

## Output Contract

- ICP: services-firm founder/COO, $5M-$50M revenue, currently feeling margin pressure. ✓
- Channel: catalystworks.consulting/diagnostic + cold email T2 link + LinkedIn post CTA. ✓
- Lead magnet: Reveal Problem type, Software delivery, 7-step compliance verified above. ✓
- Hook: contrarian + specificity ("Where's your 6-8% going?"). ✓
- Offer (anchored at end of report): $497 Signal Session. Scarcity hook: 3 sessions per month. ✓
- CTA: one button, "Book Signal Session." ✓
- Follow-up plan: email-capture triggers a 4-touch nurture sequence (separate spec). ✓
- Success criteria: 30% completion rate (start to email), 10% Calendly book rate from the report. ✓
- Anti-patterns refused: multi-problem, format-named, mock quotes. ✓

---

## When to Build

- v1 ships AFTER warm-DM falsifier test (per Phase 6 review-gate).
- v1 build time: 1-2 days (one Boubacar focus session OR one /schedule agent run).
- v1 lives at catalystworks.consulting/diagnostic, gated by simple email field.
- v2 (the polished version with the 8-lens-specific outputs) only after v1 produces 50 completed scores.

**Do not build the diagnostic in this session.** This brief is the spec; the build is a separate session.
