# Objective Statement

A 25-word-or-fewer sentence that says what this engagement, project, or sprint is trying to accomplish. Written in plain language. No jargon. No technical terms. Anyone associated with the work should be able to read it once and understand it.

## When to pull

- At the start of any engagement, project, or non-trivial sprint
- Whenever the team feels lost in the weeds
- Whenever the user asks "what are we even doing here"

## Why it works

Three failure modes it prevents:

1. **Drift.** Without a stated objective, the work expands to fill the time. Two weeks later you're solving a different problem and don't know it.
2. **Misalignment.** Two people on the same call leave with two different versions of "what we're doing." The objective statement makes that disagreement visible at minute 5 instead of week 5.
3. **Bad scoping.** You can't decide what's in or out of scope without knowing the goal. Once the objective exists, scope decisions become almost mechanical.

## How to apply

Three checks. The statement passes only if all three are true.

### 1. Clear

- No jargon, no acronyms, no technical terms
- A person not in the room could read it once and explain it back
- Remove any word that needs a definition

### 2. Concise

- 25 words or fewer
- One sentence
- If you need a comma, fine. If you need a semicolon, you're cheating.

### 3. Complete

- Includes what success looks like in their language
- Includes the relevant boundary (timeline, scope, resource) without listing all three
- Stops short of how :  that's not the objective, that's the plan

## Format

```markdown
## Objective Statement
> [the sentence]
```

Always use a blockquote. It signals that this sentence is load-bearing and not to be edited casually.

## Examples

**Good:**
> Help Mike identify the top three operating leverage points at $8M revenue and leave with a concrete first move on the highest-leverage one.

(22 words, no jargon, success criterion baked in, scope clear.)

**Good:**
> Ship a Catalyst Works client portal that consolidates engagement materials for current clients within three weeks.

(17 words, plain language, deliverable + deadline + audience.)

**Bad:**
> Optimize the customer-facing engagement workflow leveraging cross-functional best practices to drive measurable ROI.

(Jargon, no audience, no boundary, untestable.)

**Bad:**
> Build the thing we talked about last week so the team can move forward.

(Vague, no success criterion, no boundary.)

## Field note

The 25-word limit is the killer move. If you can't say it in 25 words, you don't know what you're doing yet. Spend the next hour making it 25 words instead of starting the work :  every hour spent here saves three later.

When someone resists the 25-word limit ("but it's complicated"), that resistance is itself the signal. Complicated objectives are unfinished objectives.

## Related patterns

- [completion-criteria](completion-criteria.md) :  the objective is the goal; completion criteria is what "good" looks like at the end
- [constraint-matrix](constraint-matrix.md) :  the objective is the goal; the matrix tells you what to flex when reality intrudes

## Source

Adapted from BYU PM Process Guide, section 1.2.2 ("Establish the Project Governance Framework :  Create the Objective Statement"). Original was for enterprise projects with a Sponsor; this version is scaled for solopreneur and small-team work.
