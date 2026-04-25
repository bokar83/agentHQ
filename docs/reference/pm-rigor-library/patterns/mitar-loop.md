# MITAR Loop

Monitor / Investigate / Take Action / Report. A four-step status loop applied on a cadence (weekly, per-session, monthly :  depending on engagement size). Lightweight enough to run in 15 minutes. Disciplined enough to catch problems before they cost you.

We kept the acronym from BYU because it's specific, memorable, and the four verbs are exactly the right four verbs.

## When to pull

- For any engagement longer than 1 week
- For multi-week internal builds with the roadmap skill
- Whenever you realize you've been heads-down and don't know your status anymore

Skip for: Signal Sessions, single-day work. The constraint matrix and parking lot do enough at that scale.

## Why it works

Two failure modes it prevents:

1. **Quiet rot.** Engagements that go a week without a status check tend to surface problems late. MITAR makes status check a forced ritual.
2. **All-talk-no-action status.** "Status meetings" without the Investigate and Take Action verbs are theatre. MITAR forces the loop: noticing leads to digging leads to doing leads to communicating.

## How to apply

Four verbs. In order. Each gets a short answer. Total time: 15 minutes.

### M :  Monitor

What is actually happening vs. what was planned?

Three quick checks:

- **Schedule:** are we on the planned timeline? Pull from deliverable tracker.
- **Scope:** has anything been added, cut, or changed?
- **Resources:** is anyone unavailable, blocked, or stretched?

Output: a one-sentence status per parameter.

### I :  Investigate

For anything that's off-plan, ask why. Don't accept the surface explanation.

- "We're behind because the client was slow" → Why was the client slow? What can we do about it?
- "Scope grew" → Who added it, and why was it accepted without a Stargate?
- "Resource stretched" → Is this a one-time hit or a structural issue?

Output: 1 to 3 sentences per off-plan item.

### T :  Take Action

Pick one or more:

- **Adjust the plan** :  update the constraint matrix, cut scope, extend timeline (with confirmation)
- **Mitigate** :  add a deliverable-tracker item to address the cause
- **Escalate** :  pull a Stargate checkpoint if the variance is significant
- **Accept** :  sometimes the answer is "this is fine, monitor next week"

Output: action items in the deliverable tracker, with owners and dates.

### R :  Report

Communicate the status to whoever needs it.

- For client engagements: a short status note to the client (1 paragraph: where we are, any changes, what's next)
- For internal builds: a session-log entry in the roadmap
- For solo work: a note to yourself in the relevant file

Reporting is not optional. The loop without R is incomplete; problems noticed and acted on but not communicated still surprise stakeholders.

## Cadence

| Engagement type | Cadence |
|---|---|
| Signal Session | N/A (single session) |
| SHIELD multi-week | Weekly |
| Advisory retainer | Monthly (after each touchpoint) |
| Internal build (roadmap) | Per session, in the session log |
| Solo deep-work sprint | Daily for short sprints, weekly for longer |

## Format

```markdown
## MITAR — [date]

**M:** [schedule status]. [scope status]. [resource status].
**I:** [why anything is off, 1-3 sentences]
**T:** [actions taken or to be taken]
**R:** [where this was reported, to whom, when]
```

## Examples

**Mid-engagement, week 3 of 6 SHIELD:**

```markdown
## MITAR — 2026-05-12

**M:** Schedule on track. Scope: client added a request to include a competitor benchmark slide — accepted with no scope reduction (red flag). Resources: BB heads-down all week, no issues.

**I:** Why was scope expanded without a tradeoff? Because the client framed it as "small ask" and BB didn't push back. The competitor benchmark is actually 6-8 hours of work.

**T:** Two actions:
- Email client today: name the addition, propose either a $1,500 add-on OR cut the "first 30 days" memo to make room
- Update engagement-brief.md to reflect this
- Watch for similar small-asks-that-aren't in week 4

**R:** This MITAR + the client email = the report. Logged in session-notes.md.
```

**Internal roadmap, weekly check:**

```markdown
## MITAR — 2026-05-08 (concierge week 2)

**M:** Schedule: ahead by 1 day. Scope: still 4 features for v1, no creep. Resources: solo, no blockers.

**I:** Ahead because feature 1 was simpler than estimated. Don't trust this — feature 3 will likely eat the buffer.

**T:** No action. Continue. Re-check at end of week 3.

**R:** Logged in concierge.md session log.
```

## The hard rules

1. **All four verbs every time.** A monitor without an investigate is just looking. An investigate without a take action is just thinking. A take action without a report is just doing.
2. **Variance gets a why.** If schedule slipped, scope grew, or a resource got blocked, the I step must produce a real explanation, not a hand-wave.
3. **If three MITARs in a row report "all green, no action," cadence is wrong.** Either you're not looking hard enough or the engagement doesn't need MITAR. Decide which.

## Field note

The most useful MITAR is the one where you catch yourself rationalizing variance. "We're a little behind but it's fine" → no, run the I step. Why? What's the action? The discipline is in resisting "we'll catch up next week."

When client engagements have multiple stakeholders, the R step doubles as a trust-builder. Clients who get a clean weekly status note feel calm. Clients who don't hear anything for 10 days start to worry, and a worried client is a fragile client.

## Related patterns

- [stargate-checkpoint](stargate-checkpoint.md) :  when MITAR keeps surfacing the same problem, escalate to a Stargate
- [constraint-matrix](constraint-matrix.md) :  Monitor reads against the matrix; Take Action updates it
- [risk-brainstorm](risk-brainstorm.md) :  MITAR is the ongoing watch on identified risks

## Source

Acronym and concept from BYU PM Process Guide, section 3.1.2 ("Monitor, Investigate, Take Action, and Report on Project Performance"). Scaled here from enterprise weekly status meetings to solopreneur cadences.
