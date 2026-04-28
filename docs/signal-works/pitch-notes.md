# Signal Works - Pitch Notes: "Your Agent Learns Your Patterns"

**Source:** Agent-S competitive analysis, 2026-04-28. Council-reviewed (Sankofa + Karpathy). These are positioning artifacts, not engineering milestones. They live here, not in atlas.md.

---

## The Core Narrative

Agent-S's headline: "It comes with its own computer... over time, it learns how you work and gets better at it."

Our version, grounded in what agentsHQ actually does:

> "Your agent gets its own brain. It learns which topics land with your audience, which outreach angles get replies, and when to follow up. Every week it gets a little sharper - without you touching anything."

This is not a promise. It is a description of what Chairman Crew (M5) + Content Scout (M10/Phase 2) actually deliver once live. The narrative should only be used in Signal Works pitches after M5 ships (gate: 2026-05-08).

---

## What Makes It Real (the technical proof points)

| Claim | What backs it |
|---|---|
| "Learns which topics land" | Chairman Crew reads `task_outcomes` weekly, identifies approval/skip patterns, proposes scoring weight mutations |
| "Learns which outreach angles get replies" | M6 Hunter Crew (trigger-gated on 2026-05-06 decision) - tracks reply rates by email angle |
| "Content Scout surfaces what's trending in your niche" | M10 Topic Trend Scout - daily HN/Reddit/YouTube scan, Haiku classifier, fit-scored candidates delivered to Telegram |
| "Every week it gets sharper" | Chairman Crew fires weekly (M5), model review agent fires weekly (M11d) - two independent improvement loops |
| "Without you touching anything" | L1-L4 already live: propose, schedule, publish, reconcile - zero manual Notion work |

---

## The Agent-S Comparison (what to say, what not to say)

**What to say to a prospect:**
"There are hosted agent services coming out now that give every user a managed computer. Ours is different: instead of a general-purpose computer, you get an agent that knows your business - your voice, your audience, your pipeline. It's not trying to do everything; it's trying to be really good at the things that actually drive your revenue."

**What NOT to say:**
- Do not name-drop Agent-S (alpha product, low recognition, may confuse)
- Do not promise "1,000+ integrations" - we have ~15, all deliberate
- Do not claim real-time learning - Chairman Crew is weekly, not continuous

---

## Signal Works Positioning One-Liner

"We set up an AI presence system that publishes your content, scouts new ideas, and gets sharper every week - so you spend your time on clients, not on content."

---

## When to Use This

- Signal Works discovery calls (after diagnosing the prospect's current content process)
- Signal Works proposal decks (the "how it works" slide)
- Cold outreach follow-up emails (after the hook lands)

Do NOT use before M5 ships (2026-05-08). Before that, the "learns" claim is prospective, not live.

---

## Competitive Context

Agent-S (agent-s.app) is targeting the same SMB owner-operator. They are invite-only alpha as of 2026-04-28. Their moat is integration breadth (1,000+ apps, zero setup). Our moat is specificity: we know the content pipeline, the outreach loop, and the client voice. Breadth vs. depth. We win on depth for the specific use case we own.

The race: get Signal Works to first paying client before Agent-S exits alpha and starts SMB marketing at scale. First-mover on "done-for-you AI presence" in the $497-$2,000/mo SMB tier is the window.
