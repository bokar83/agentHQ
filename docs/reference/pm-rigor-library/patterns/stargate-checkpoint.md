# Stargate Checkpoint

A formal go / no-go gate at a key decision point. The work pauses. The objective, the constraint matrix, and the current status get re-read. Then a decision: continue as planned, change course, or stop.

The name comes from the BYU methodology :  a Stargate is a controlled passage from one phase to another. We kept the name because it's evocative and it earned its keep.

## When to pull

- Before kickoff (gate between proposal and engagement start)
- At the midpoint of a multi-week engagement (gate between phase 1 and phase 2)
- Before a major deliverable ships (gate between draft and send)
- Whenever someone says "I'm not sure we're on the right track"
- Before any decision that's expensive to reverse

## Why it works

Without checkpoints, work continues by inertia. The original objective drifts, the constraint matrix goes stale, and you find out at the closeout that you've delivered the wrong thing.

The Stargate forces a deliberate moment of "should we keep going as planned." Most of the time the answer is yes. The few times the answer is no, the checkpoint just saved an engagement.

## How to apply

Three questions, in order. Answer each in writing.

### Question 1: Is the objective still right?

Re-read the [objective statement](objective-statement.md). Is it still what we're trying to do?

- If yes → proceed to Q2
- If no → write the new objective. The checkpoint is now also a re-scoping moment. The client (or sponsor) needs to see and approve the new objective before any further work.

### Question 2: Is the constraint matrix still accurate?

Re-read the [constraint matrix](constraint-matrix.md). Has anything shifted?

- If unchanged → proceed to Q3
- If shifted → update the matrix. If the most-constrained parameter changed, this is a major event :  pause work, update the plan, re-confirm with the client.

### Question 3: What's the call?

Pick one:

- **Continue** :  plan is sound, keep going
- **Adjust** :  plan needs a defined change (cut feature X, extend deadline by 1 week, swap deliverable Y for Z)
- **Pivot** :  the work is fundamentally off; restart the planning step
- **Stop** :  the engagement no longer makes sense; close it cleanly

For "adjust" and "pivot," the change must be documented and (if external) confirmed with the client before continuing.

## Format

```markdown
## Stargate Checkpoint — [date]

**Trigger:** [why we're holding this checkpoint — milestone reached / client request / time-based]

### Q1: Objective still right?
[Yes / No + new objective if No]

### Q2: Constraint matrix still accurate?
[Yes / No + what shifted]

### Q3: The call
[Continue / Adjust / Pivot / Stop]

**Decision rationale:** [1 paragraph]
**Action items:** [if any, who owns and by when]
**Confirmed with:** [client name and date, or "internal only"]
```

## Examples

**Mid-engagement Stargate, week 3 of 6 SHIELD:**

```markdown
## Stargate Checkpoint — 2026-05-15

**Trigger:** End of phase 1 (diagnostic complete), entering phase 2 (recommendation design)

### Q1: Objective still right?
Yes. Help [Client] reduce ops chaos at $12M revenue. Diagnostic surfaced ops, not finance, as the binding constraint — that matches the engagement objective.

### Q2: Constraint matrix still accurate?
Shifted. Schedule was "moderately constrained" at kickoff. Client now wants the readout 1 week earlier (May 29 instead of June 5) for a board meeting. New matrix: schedule most, scope moderately, resources least.

### Q3: The call
Adjust. Cut the "implementation roadmap" deliverable from phase 2 — too much for the new timeline. Replace with a "first 30 days" memo that's leaner.

**Decision rationale:** Client's board moment is the real deadline. Pruning scope buys us the schedule. Implementation roadmap can be a follow-up engagement.

**Action items:**
- BB: send revised scope memo to client today, get explicit confirmation
- BB: update engagement-brief.md with new scope and matrix

**Confirmed with:** [client name], 2026-05-15 via email
```

**Pre-launch Stargate, before sending a SHIELD proposal:**

```markdown
## Stargate Checkpoint — Pre-send proposal

### Q1: Is the objective still right?
Yes. Help [client] turn $8M ops chaos into a 12-week reset.

### Q2: Constraint matrix still accurate?
Yes. Same as Signal Session matrix.

### Q3: The call
Continue. But first: run /sankofa on the proposal before sending. Specific question for council: is the price ($28K) defensible given what we surfaced in the Signal Session?
```

## The hard rules

1. **Stargates aren't status meetings.** A status meeting is "where are we." A Stargate is "should we keep going." Different question, different posture.
2. **The decision must be in writing.** A verbal "yeah we're good" doesn't count. The artifact is the proof.
3. **If the client is the sponsor, the client must be in the loop.** Stargates that adjust scope or schedule require explicit client confirmation before continuing.

## Field note

The discomfort of holding a Stargate is the signal that you need one. If it feels awkward to pause and ask "should we keep going," that's exactly the moment when momentum is masking a problem.

The cheapest Stargate is one held early. The most expensive one is the closeout meeting where you realize you should have held one in week 2.

## Related patterns

- [objective-statement](objective-statement.md) :  Q1 of every Stargate
- [constraint-matrix](constraint-matrix.md) :  Q2 of every Stargate
- [mitar-loop](mitar-loop.md) :  MITAR is the ongoing monitor; Stargate is the formal pause

## Source

Adapted from BYU PM Process Guide. Original Stargates were tied to specific named phases (1.1.2, 2.1.3, 2.3.2, 2.3.4, 2.3.6); we generalized to "any major decision point" because solopreneur engagements don't have the same enterprise phase structure.
