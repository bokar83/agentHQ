# Lighthouse · 1-Page LinkedIn Audit · Operating Playbook

**Purpose:** when a V1/V2/V3/V4 recipient replies yes, deliver the audit in 30 min, not 3 hours. This playbook is the speed tool.

**Template:** `data/lighthouse-audit-template.html`. Open, fill in 6 slots, send. That's the whole motion.

**SLA:** 5 PM same day the yes lands. Late yes (after 4 PM) means deliver next day. Honor the promise or skip the audit and apologize. Half-baked work is worse than a delay.

**Voice rules (non-negotiable):**
- Zero em-dashes. Use hyphens, commas, colons, periods.
- No throat-clearing. No "I noticed an interesting opportunity". Lead with the finding.
- Direct. Opinionated. Pick one rewrite, not three.
- Specifics, never generics. Quote their actual text. Name the actual pattern.
- Vary sentence length. Short. Then long. Then short.
- No buzzword soup. No "leverage", "synergy", "tapestry", "delve", "complexities".

---

## The 7-Minute Diagnostic

Pull up their LinkedIn in one tab, this playbook in another. Walk the 3 buckets in order.

### Bucket 1 · Headline (the line under their name)

Read it once. Then ask:
- Does it name a RESULT they help buyers get? Or just a FUNCTION (CEO, Founder, Consultant)?
- Does it tell me who the buyer is? (target audience present or absent)
- Is it under 220 chars? (LinkedIn limit, longer truncates)
- Is the first word a hook or a title? (Title first = skipped)

**Failure flags:** "Founder | CEO | Consultant" lists. "Helping businesses..." (vague verb + vague object). Job-board copy. Anything that could belong to 1,000 people.

**Strong pattern:** `[Role action verb] [Specific buyer] [Specific result] in [Timeframe or condition].`
Example: "Cut 30+ hours of weekly ops time for SMB founders building their first AI workflow."

### Bucket 2 · Latest Post Hook (line 1 of their most recent original post)

Read just the first line. Don't read line 2 or 3.

- Did you want to read line 2? If no, the hook failed.
- Is the first word boring (The, In, Today, So)?
- Does it set up a frame everyone agrees with? (No tension = no hook)
- Does it telegraph the whole post in line 1? (Spoiler kills the scroll-stop)

**Failure flags:** "In today's fast-paced world..." "I've been thinking about..." "Last week I attended..." (with no payoff in line 1).

**Strong patterns (Cole swipe file, applied):**
- Big Number: `In [Timeframe], my [Niche] generated [$X / Y Results].`
- The Crazy Part: `In [Timeframe], I [Result]. The crazy part? [Twist].`
- Belief Flip: `I used to think [Common belief]. But [Now I've achieved X].`
- The Secret: `Over [Timeframe], I've [Achieved Result]. The secret? [Open loop].`
- The Struggle: `I struggled for [Time] to [Overcome Y]. But now, I [Achieved Z].`
- Most Powerful: `The most powerful [Habit / Idea] for [Outcome]:`

Match the right format to their actual story. Don't force a Big Number if they have no numbers.

### Bucket 3 · About Section CTA (last paragraph, the ask)

Scroll to the bottom of their About. What does the last paragraph DO?

- Is there a clear next step a reader can take? (DM, calendar link, free resource)
- Does it tell the reader who it's for? (target buyer named or implied)
- Is it written for a HUMAN, or for ATS / SEO?
- Does it close with a soft yes/no, or with a real reason to act?

**Failure flags:** "Open to opportunities." "Let's connect." "Reach out if interested." (All zero specificity, zero urgency, zero buyer-name.)

**Strong pattern:** Name the buyer + name the result + name the easy first step.
Example: `If you're a SaaS founder spending more than $5K/mo on tools that don't talk to each other, DM me "AUDIT" and I'll send you the 1-page rewrite. No pitch.`

---

## Pick the One

After the 7-min walk, pick the WORST of the 3. That's your audit subject.

If all 3 are roughly equal, pick the **headline** (highest leverage; gets read most often, by the most kinds of readers).

If all 3 are strong, pick the one that's closest to "good but missing one thing", that gives the recipient a clear win. Don't tear down work that's already pulling weight; sharpen it.

---

## Filling in the Template

The HTML template has 9 [SLOTS]. Fill them in this order:

1. `[PROSPECT_NAME]`, first name only. ("Chad", not "Chad Burdette".)
2. `[DATE_DELIVERED]`, `Wednesday May 13, 2026` style.
3. `[WITNESS_ANCHOR]`, one sentence of personal observation tied to this recipient. Examples:
   - "I have been watching your work since [event/year] and one line kept stopping me."
   - "Pulled up your profile this morning and one section stopped me cold."
   - "Saw your post on [topic] last week. Then came back to your profile and noticed something."

   30 seconds to write per recipient. Required. Council added this slot 2026-05-13 to convert the document from system output to human gesture.
4. `[HOOK | HEADLINE | ABOUT_CTA]` (3 mentions), pick one, replace everywhere.
5. `[VERBATIM_CURRENT_TEXT]`, paste their actual line word for word. No paraphrasing.
6. `[ONE_SENTENCE_DIAGNOSIS]`, name the pattern. Avoid generic.
7. `[REWRITE_FINAL]`, one version, committed. Use their real specifics (their company, their service, their numbers if known).
8. `[ONE_SENTENCE_REASONING]`, cite the principle, not the buzzword.
9. `[OTHER_TWO_OF: ...]`, list the two buckets you didn't audit, lowercase comma-separated.

## Strategic Bridge (do NOT edit)

The template footnote names the $250 Signal Session as the explicit next step. Council mandate 2026-05-13: the audit is a sample of the method, not the conclusion. Do not strip or soften the Bridge. Do not remove the price. Do not change the trigger word ("Signal"). If you want to swap pricing or scheduling logic, that is a separate decision tracked in `docs/roadmap/lighthouse.md`, not an in-flight edit.

---

## CTQ Self-Check (5 items, 90 seconds before send)

Run this every time. No exceptions.

1. **Zero em-dashes?** Ctrl-F the doc. Both `-` and `-` must return zero matches.
2. **Witness anchor present and specific?** The opening sentence must reference the recipient by name + a real observation. Generic openers fail. ("Pulled up your profile this morning..." is OK because it is honest; "I have been watching your great work for years" is NOT OK because it is generic-flattery.)
3. **Specific everywhere?** Did you name the actual text from their profile, or did you write "your hook"? Names beat pronouns.
4. **One rewrite, not three?** If you offered options, pick one and delete the rest. Conviction earns the second reply.
5. **Strategic Bridge intact?** The footnote names the $250 Signal Session, the 7 sections, the "Signal" reply trigger, and "by Friday" scheduling. All 4 elements must be present. Council 2026-05-13.

Fail any of three = rewrite that section. Don't send.

---

## Send Path

Email to recipient. From `boubacar@catalystworks.consulting` via the canonical CW OAuth path (per `feedback_cw_send_canonical_path.md`). NEVER via `gws gmail` CLI (silently rewrites From).

Subject: `[NAME], here's the audit.` (lowercase the comma fragment, keep it short, no exclamation point.)

Body: paste the HTML as Gmail HTML body (Gmail compose, Ctrl-Shift-V the rendered version, or use the canonical Python send path with `MIMEText(body, "html", "utf-8")`).

After send: verify From-header by fetching the sent message metadata. Per HARD RULE 0.

---

## Log to inbound-signal-log

Append a `DELIVERED` event:

```
[YYYY-MM-DD HH:MM] DELIVERED audit to [NAME] - focus: [hook|headline|about-cta]
```

Then mark the warm-list row with `audit delivered YYYY-MM-DD`.

---

## Thursday Check-In

Two days after delivery, ping the recipient:

> [NAME], following up on the audit I sent Wednesday. Did the rewrite feel accurate? I'd rather hear "no, here's why" than silence. Either way, no pitch.

Pre-write this Wednesday night during the 21:00 ritual so Thursday morning is press-send.

---

## Common Failure Modes (do not repeat)

| Failure | Fix |
|---|---|
| Audit reads like a generic LinkedIn coaching post | Quote their literal text. Cite their literal company. |
| 3 rewrite options instead of 1 | Pick one. Delete the rest. Conviction > optionality. |
| Reasoning section uses buzzwords | Cite the specific tactic. "Pre-commit the brain" beats "engage the reader". |
| Audit ships at 5:47 PM | Promise was 5 PM. Send a 4:55 PM holding note: "Audit lands at 5:30 today. Tightening it." Honor the new time. |
| You audited 2 buckets to "give more value" | Promise was 1. Hold the line. Offer the other 2 in section 05 of the template. They reply yes, you do round 2 free. Now you have a real conversation, not a one-shot. |
| Em-dash slips into the rewrite | Ctrl-F before send. Every time. |

---

## When This Playbook Stops Working

If Week 1 ends with ≥10 audits sent and ≤3 yes-replies to a second touch, the audit format itself is the problem. Triggers Saturday M5 Conversion Scorecard rewrite. Don't iterate on this playbook mid-W1.

---

**Cross-ref:**
- `docs/roadmap/lighthouse.md`, master sprint
- `docs/strategy/lead-strategy-2026-05-12.html`, v8 with V1/V2/V3/V4 templates
- `skills/library/cole-templates/templates-linkedin-hooks.md`, 15 hook formats
- `skills/boub_voice_mastery/SKILL.md`, voice rules
- `skills/ctq-social/references/linkedin-craft.md`. LinkedIn-specific craft notes
- `data/lighthouse-warm-list.md`, the 10 names
- `data/inbound-signal-log.md`, the log
