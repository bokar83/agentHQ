# Parking Lot

A capture-don't-process technique. When ideas, risks, or questions emerge faster than you can act on them, you write them down in a designated spot and keep moving. You come back to them when there's time.

## When to pull

- During brainstorms, when ideas exceed processing capacity
- During kickoffs, when risks surface before you can analyze them
- During sessions, when a tangent appears that's worth keeping but not now
- During implementation, when a "we should also..." emerges and would derail the current task

## Why it works

Two failure modes it prevents:

1. **Lost context.** Without a parking lot, good ideas get said once and forgotten. You're in a meeting and someone surfaces a real risk; if you don't capture it, it's gone in 20 minutes.
2. **Derailed flow.** Without a parking lot, every tangent becomes a debate about whether to chase it. The parking lot says: we don't have to decide right now, just write it down and we'll triage later.

The parking lot isn't a productivity hack. It's permission to defer.

## How to apply

Three rules:

### Rule 1: One designated spot

The parking lot has one location. In an engagement, it's a section in the brief or session-notes called "Parking Lot." In a roadmap, it's a section in the session log. In a brainstorm session, it's the bottom of the notes file.

If the parking lot is scattered, it's not a parking lot, it's litter.

### Rule 2: Capture, don't process

When something hits the parking lot:

- Write it down in 1 to 2 sentences
- Don't analyze it
- Don't decide what to do with it
- Don't argue about whether it belongs there
- Move on

The whole technique fails if you stop to evaluate.

### Rule 3: Triage on a schedule

Parking lots accumulate. They have to be triaged or they rot.

- For a single engagement: triage at the end of each session. 5 minutes. Each item gets one of: kill / promote to deliverable / leave for next session / convert to a follow-up task.
- For a roadmap: triage at the end of each session log entry, same rules.
- For a brainstorm: triage at the end of the brainstorm.

If a parking lot has 3+ entries from sessions ago that nobody triaged, the technique has broken down.

## Format

```markdown
## Parking Lot
- [item 1, 1-2 sentences]
- [item 2]
- [item 3]
```

That's it. No fields, no metadata. Plain bullets.

When an item is triaged, either:
- Delete it (killed)
- Move it to the appropriate section (promoted)
- Add a date stamp (still parked, but I noticed it)

## Examples

**During a Signal Session brief:**
```markdown
## Parking Lot
- Spouse / co-founder / COO may be the actual decision-maker and not in the room
- $8M is the cliff zone; ego may resist the real diagnosis
- He may anchor on a symptom (e.g., "we need a new ERP") instead of leverage
```

**During a roadmap session log:**
```markdown
## Parking Lot
- Consider rebranding the dashboard to something less generic than "client portal"
- The closeout-memo template might want a "what would you do differently" section
- Could the engagement-ops skill auto-create a Notion page when the brief is written?
```

## The hard rule

If something is in the parking lot for 3 weeks and hasn't been triaged, it's dead. Delete it. Not every parked thought deserves a second life.

The parking lot is not a backlog. A backlog has commitments. A parking lot has captures.

## Field note

The most common parking-lot failure: people use it to avoid a hard decision. "We'll park that and discuss next week" becomes "we'll never discuss it." Triage discipline is the antidote :  name a triage moment and stick to it.

## Related patterns

- [risk-brainstorm](risk-brainstorm.md) :  a structured way to populate the parking lot for risks specifically
- [closeout-meeting](closeout-meeting.md) :  the closeout is partly a final triage of any remaining parking-lot items

## Source

Adapted from BYU PM Process Guide ("Parking Lot Risks" :  risks identified during planning but not yet assessed). Generalized here from risks-only to any captured-but-deferred thought.
