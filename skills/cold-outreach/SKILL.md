---
name: cold-outreach
description: Proven cold email templates for Catalyst Works Consulting. Two variants — sector-specific (when you know the prospect's industry) and size-based (when you're moving fast or the business type is ambiguous). Reply-first model, no Calendly in the initial email. Triggers on "cold outreach", "cold email", "CW outreach", "send cold email", "outreach template", "T1 template", "outreach copy".
---

# Cold Outreach — Catalyst Works Consulting

---

## Strategy Notes

- **List sources beyond Apollo:** see `skills/hormozi-lead-gen/SKILL.md` Section 4 -- 4 alternative sources + the <1% reply diagnostic.
- **Reply-first model:** Optimize for the micro-commitment (a reply), not the booking. Calendly goes in the follow-up, never the cold email.
- **Sector vs size bracket:** Use the sector version whenever LinkedIn gives you 60 seconds of context. Use the size version when moving fast or business type is ambiguous.
- **Research payoff:** Personalizing the bracket (sector vs generic) can 2x-3x reply rates. The bracket is not decoration.
- **Emoji in subject:** The ninja emoji is intentional and on-brand. Confirm rendering in your email client before bulk send.

---

## HARD RULES (locked 2026-04-30 / 2026-05-01)

### 1. Greeting — drop it when the first name is uncertain

If `first_name_confidence == "low"`, the greeting is OMITTED entirely. The body opens straight to the hook. Do NOT fall back to "Hi there", "Hello", or "Hey".

Why: cold-email research (Lemlist 2024, Apollo 2023, Hunter 2024 on 50M+ emails) shows generic greetings underperform every alternative including no-greeting. "Hi Commercial," / "Hi Utah Plumbing," shipped from us in production = brand damage.

How to apply: every template (CW T1-T5, SW T1-T4) implements `build_body(lead)` returning greeting + hook on HIGH confidence, hook only on LOW confidence. Never hardcode `"Hi {first_name},"` — always go through `build_body(lead)`.

Confidence is set by `skills/outreach/sequence_engine.py:_extract_first_name()`:
- HIGH: `lead.name` from Apollo source, OR email local-part with `.`/`-` separator, OR known prefix (dr/mr/mrs/ms), OR len <= 6 with only single vowel-letter cluster.
- LOW: everything else.

### 2. Signature — first name only, no title, no URL-and-company together

```
Boubacar
catalystworks.consulting
```

That's it. Not "Boubacar Barry". Not "Boubacar Barry, Founder, Catalyst Works". If you list the URL, do not also list the company name spelled out — pick one. Body intro line ("I'm Boubacar Barry, founder of Catalyst Works") stays untouched.

### 3. Send window — weekdays only

Harvest 7 days/week (queue lead inventory). Send Mon-Fri only. `signal_works/morning_runner.py:_main_body()` checks `datetime.now().weekday() >= 5` and skips Steps 3 + 5 on weekends. Apollo budget is monthly; weekend open rates are lower; Saturday/Sunday sends signal "automated blast".

---

## Subject Line

```
Where is your margin actually going? 🥷🏾
```

---

## Template A — Sector-Specific

*Use when: you know the prospect's industry from LinkedIn or a quick search.*

```
Hi [First Name],

I'll keep this simple.

Most [professional services / logistics / ops-heavy] businesses aren't
losing margin to bad strategy. They're losing it to one bottleneck that
hasn't been named yet — a handoff, an approval loop, a pricing gap quietly
taxing everything downstream.

I'm Boubacar Barry, founder of Catalyst Works. I run a constraint
diagnostic — usually 90 minutes — that finds exactly where margin is
leaking and what to fix first. You leave with a specific answer and a
90-day action plan, not a slide deck.

No pitch. Just a direct conversation.

Worth 20 minutes?

Boubacar
catalystworks.consulting
```

**Sector bracket options:**
- `professional services`
- `logistics`
- `ops-heavy`
- Or insert the prospect's specific niche (e.g., `mid-size accounting`, `regional construction`)

---

## Template B — Size-Based

*Use when: moving fast, business type is ambiguous, or company is small enough that sector is unclear.*

```
Hi [First Name],

I'll keep this simple.

Most 20 to 80 person businesses aren't losing margin to bad strategy.
They're losing it to one bottleneck that hasn't been named yet — a handoff,
an approval loop, a pricing gap quietly taxing everything downstream.

I'm Boubacar Barry, founder of Catalyst Works. I run a constraint
diagnostic — usually 90 minutes — that finds exactly where margin is
leaking and what to fix first. You leave with a specific answer and a
90-day action plan, not a slide deck.

No pitch. Just a direct conversation.

Worth 20 minutes?

Boubacar
catalystworks.consulting
```

---

## Follow-Up Sequence

*(Calendly goes here, not in the cold email)*

Follow-up #1 (3 days after no reply): short bump — "Wanted to make sure this didn't get buried."
Follow-up #2 (5 days after that): value add or breakup line.

*Templates TBD — build after first batch results are in.*

---

## Version History

- **v1.0 (2026-04-06):** Initial version. Two templates finalized. Reply-first model confirmed. Calendly removed from cold email. Em dashes removed per house rules.
- **v1.1 (2026-05-01):** Added HARD RULES block. Locked no-greeting rule on low-confidence first names across all 9 templates (CW T1-T5, SW T1-T4) via `build_body(lead)` callable pattern. Locked signature standard (first name + URL only). Locked weekday-only send window. Source-aware first-name extraction in `skills/outreach/sequence_engine.py`. Backed by Lemlist 2024 / Apollo 2023 / Hunter 2024 data — see `feedback_no_greeting_when_unknown.md`.
