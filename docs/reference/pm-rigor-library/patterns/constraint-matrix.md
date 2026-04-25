# Constraint Matrix

A 3x3 force-rank of scope, schedule, and resources. Each gets exactly one of "most constrained," "moderately constrained," or "least constrained." No two parameters can share a level. The matrix is the rule book for what to flex when reality intrudes.

## When to pull

- At the start of any engagement or project that has a deadline or a budget
- The moment scope creeps, the schedule slips, or a resource becomes unavailable
- Before any "should we add this?" or "should we cut this?" decision

## Why it works

Without a matrix, every tradeoff is re-litigated. With a matrix, the answer is pre-decided.

The constraint matrix forces an explicit conversation about which parameter is sacred and which is flexible. It is the antidote to "we want all three" :  a wish, not a plan.

## How to apply

Three steps. Total time: 10 minutes (light) or 30 minutes (full with team).

### Step 1: Rank

Force-rank scope, schedule, and resources from most constrained to least. No ties. If two feel equally tight, pick anyway :  the act of picking surfaces the real priority.

### Step 2: Justify

For each ranking, write one sentence finishing this stem:

- "Scope is most constrained because..."
- "Schedule is moderately constrained because..."
- "Resources are least constrained because..."

If you can't finish the sentence, the ranking is wrong.

### Step 3: Document the implication

Write one sentence per parameter that says what this means in practice:

- Most constrained → "We will not flex this. Anything that pushes against it gets cut elsewhere."
- Moderately constrained → "We will flex this only if we have to, and only with a documented reason."
- Least constrained → "This is where we absorb pressure first."

## Format

```markdown
## Constraint Matrix
| Parameter | Constraint | Why |
|---|---|---|
| Scope | Most | [one sentence] |
| Schedule | Moderately | [one sentence] |
| Resources | Least | [one sentence] |

**Implication:** [one paragraph that says what we'll flex first when reality hits]
```

## Light version (Signal Session, advisory)

For a 90-minute session, the matrix is two lines:

```markdown
- Most constrained: Schedule (90 min, immovable)
- Moderately: Scope (lots could come up, only a few will surface)
- Least: Resources (just us)
> Implication: cut early, name what we're NOT covering.
```

That's it. Three minutes. No table needed.

## Full version (SHIELD, multi-week build)

For longer engagements, expand each parameter with its sub-considerations:

**Scope:**
- Most constrained: well-defined requirements, hard list from client, mandated by contract
- Moderately: some "want-to-haves" articulated, phased delivery possible
- Least: requirements adjustable, minimum is much less than the ask

**Schedule:**
- Most constrained: immovable deadline, tight window, another commitment depends on it
- Moderately: range of dates, multiple possible deadlines, all immovable
- Least: no driving date, wide range relative to project duration

**Resources:**
- Most constrained: specialized non-transferable skills required, tight budget, narrow team
- Moderately: skills exist in multiple places, budget enhancement discouraged but possible
- Least: general skills, high familiarity in org, comfortable budget

## Examples

**Signal Session with $8M-revenue logistics CEO:**
| Parameter | Constraint | Why |
|---|---|---|
| Schedule | Most | 90 minutes, fixed Tuesday slot, he's flying out Wednesday |
| Scope | Moderately | 8 lenses available, only 3 will surface; "$8M and breaking" is broad |
| Resources | Least | Just BB, prep time available |

**Implication:** time is sacred. If we run long on lens 1, we cut lenses 2 and 3 short rather than overrun. Name what we're NOT covering at minute 60.

**Internal client portal build, 3-week ship:**
| Parameter | Constraint | Why |
|---|---|---|
| Schedule | Most | Promised to two clients for early-May demo |
| Scope | Moderately | 8 features in mind, 4 will ship in v1 |
| Resources | Least | Solo build, no external dependencies |

**Implication:** if we can't hit the date, we cut features 5-8 entirely from v1. We don't move the date, we don't add resources, we ship what's done.

## The re-read

The matrix isn't a one-time exercise. Re-read it every time you're tempted to flex something. If you flex the most-constrained parameter, the matrix is wrong :  fix it explicitly with a note.

For multi-week engagements, re-read at every session-notes entry. A constraint shift mid-engagement is the single most important signal you'll get; the matrix makes it visible.

## Field note

Most teams discover their matrix is wrong the first time they hit pressure. That's the point. The matrix being wrong-then-corrected is more useful than the matrix being unwritten.

The hardest case: when the client says "all three are most constrained." That's a refusal to plan. Push back. "If something has to give, what gives first?" If they still won't pick, the engagement isn't ready for a kickoff.

## Related patterns

- [objective-statement](objective-statement.md) :  the goal is fixed; the matrix is what gets flexed in service of it
- [stargate-checkpoint](stargate-checkpoint.md) :  every checkpoint includes a matrix re-read

## Source

Adapted from BYU PM Process Guide, section 1.2.2 ("Establish the Project Governance Framework :  Create the Constraint Matrix"). The original used checkmarks in a table; we use written rankings because they survive the trip into a Markdown file better.
