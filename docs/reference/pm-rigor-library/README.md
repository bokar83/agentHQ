# PM Rigor Library

A cherry-picked, distilled set of project management patterns. Source: Ernie Nielsen / BYU Enterprise Project Management methodology, plus our own field-tested practice.

This is **not** a methodology to install wholesale. It is a library of named patterns. You pull from it when a moment calls for more rigor.

## How to use this library

1. **Default pulls per context** are defined in the consuming skill (e.g., `engagement-ops` says: Signal Sessions always get objective-statement + completion-criteria + constraint-matrix-light + parking-lot).
2. **One-off pulls** when you spot the trigger: scope is creeping → pull `constraint-matrix`. Risks are flying around → pull `parking-lot`. Decision gate ahead → pull `stargate-checkpoint`.
3. **Adjacency reuse:** the same patterns work outside client engagements. Constraint Matrix is useful for an internal build that's running long. Parking Lot is useful in any brainstorm. Closeout Meeting is useful at the end of any sprint. Pull where it fits.

## When NOT to pull

- The pattern adds 30 minutes of overhead to a 90-minute engagement.
- The pattern requires roles you don't have (Sponsor, Functional Manager, PMO).
- The pattern is for cross-team coordination but the work is solo.
- The pattern would produce an artifact that nobody will read again.

If two of these are true, skip the pattern.

## The 8 patterns

| Pattern | One-line | Best for | Time to apply |
|---|---|---|---|
| [objective-statement](patterns/objective-statement.md) | 25-word clarity test for the goal | Any engagement, any project, any sprint | 5 min |
| [completion-criteria](patterns/completion-criteria.md) | Define done before you start | Anything with a deliverable | 5-10 min |
| [constraint-matrix](patterns/constraint-matrix.md) | Force-rank scope / schedule / resources | Anything with a deadline or a budget | 10 min (light) / 30 min (full) |
| [parking-lot](patterns/parking-lot.md) | Capture, don't process | Brainstorms, kickoffs, busy sessions | 0 min ongoing |
| [risk-brainstorm](patterns/risk-brainstorm.md) | 3-bucket risk identification | Multi-week engagements, complex builds | 30 min |
| [stargate-checkpoint](patterns/stargate-checkpoint.md) | Go / no-go gate at decision points | Long engagements, before kickoffs, before launches | 15 min |
| [mitar-loop](patterns/mitar-loop.md) | Monitor / Investigate / Take Action / Report | Anything you're managing across time | Ongoing |
| [closeout-meeting](patterns/closeout-meeting.md) | Successes / challenges / lessons learned | End of every engagement, every sprint | 30 min |

See [_index.md](_index.md) for the trigger-to-pattern lookup table.

## Source material

The original BYU PDFs are preserved in [byu-source/](byu-source/) for reference. They are not loaded by any skill :  they are reference-only. If you ever need to go deeper than the patterns capture, those are the source of truth.

The patterns themselves are rewritten in our voice and shape. We kept the names that earn their keep (Constraint Matrix, MITAR, Parking Lot) and renamed the ones that don't (Stargate stayed because it's evocative, not because it's standard).

## Updating this library

When a closeout memo produces a sharp lesson learned, propose either:

1. **Updating an existing pattern** :  add a "field note" section with the date and what was learned, OR
2. **Adding a new pattern** :  only if the lesson is genuinely new and reusable across at least 2 future contexts.

Don't update the library silently. Propose the change in the conversation, then write it.
