# Risk Brainstorm

A structured 30-minute exercise that identifies what could go wrong, sorted into three buckets: scope, schedule, and resources. Each risk is captured, assessed (high/medium/low), and either accepted, mitigated, or watched.

## When to pull

- At the start of any multi-week engagement (SHIELD, advisory retainer kickoff, internal build > 1 month)
- Whenever the constraint matrix shifts (a parameter that was "least constrained" becomes "moderately")
- After a near-miss :  capture it now while the lesson is fresh

Skip for: Signal Sessions, single-day work, content projects. Use [parking-lot](parking-lot.md) for those instead.

## Why it works

Two failure modes it prevents:

1. **Surprise as a category.** Most "surprises" in engagements were predictable. Risk brainstorm forces you to see them at hour 1 instead of week 4.
2. **All-or-nothing risk thinking.** Without buckets, every risk feels equally heavy. The 3-bucket structure makes it obvious that "the client's ERP migration might delay our work" (schedule) is a different shape of problem from "the client's CFO might quietly veto" (scope).

## How to apply

Four steps. 30 minutes total.

### Step 1: Brainstorm by bucket (15 min)

Set a 5-minute timer per bucket. List every risk that comes to mind. Don't process. Don't discuss. Just list.

**Scope risks** :  things that could change what we have to deliver:
- Requirements unclear or shifting
- Hidden stakeholder we don't know about
- "Want-to-have" creeping into "must-have"
- Quality bar higher than we estimated
- Regulatory or contractual constraint we haven't seen yet

**Schedule risks** :  things that could delay us:
- External dependency late (vendor, client team, integration)
- Estimate was wrong
- Critical path has too many tasks (no buffer)
- Client unresponsive
- Resource availability shifts
- Holidays / vacation / illness

**Resource risks** :  things that could leave us under-resourced:
- Key person unavailable when needed
- Skill gap we didn't notice
- Tool or system fails
- Budget cut mid-engagement
- Tooling cost spikes (API, model, cloud)

### Step 2: Assess (10 min)

For each risk, two ratings:

- **Likelihood:** high / medium / low :  how likely is this to happen?
- **Impact:** high / medium / low :  if it happens, how bad?

Combined rating is the higher of the two. Don't average.

### Step 3: Decide (5 min per high-rated risk, max 30 min)

For every high-rated risk, pick one:

- **Accept** :  we're aware, we're not doing anything, we accept the cost if it hits
- **Mitigate** :  we will take action to reduce likelihood or impact (and what action, by when)
- **Transfer** :  somebody else owns this risk now (insurance, contract clause, vendor agreement)
- **Avoid** :  we will change the plan to remove this risk entirely

Mitigate actions go into the deliverable tracker as items with owners and dates. This is the bridge from brainstorm to ongoing work.

### Step 4: Park the rest

Medium and low risks go to the parking lot. Re-read at every checkpoint. If a parked risk's likelihood goes up, it gets promoted.

## Format

```markdown
## Risk Register

### Scope
| Risk | Likelihood | Impact | Decision | Action |
|---|---|---|---|---|
| Hidden stakeholder may veto mid-engagement | M | H | Mitigate | Confirm decision-maker structure with client by [date] |
| Want-to-haves creeping into must-haves | H | M | Mitigate | Re-read constraint matrix at session 3 |

### Schedule
| Risk | Likelihood | Impact | Decision | Action |
|---|---|---|---|---|
| Client team late on prework | H | M | Accept | (built buffer into week 2) |

### Resources
| Risk | Likelihood | Impact | Decision | Action |
|---|---|---|---|---|
| API rate-limit hit during analysis | L | H | Mitigate | Batch requests, cache locally |

### Parking lot (medium/low, watch)
- Vacation week 3 of engagement may slow turnaround
- New tool we haven't used before for the diagnostic step
```

## The hard rules

1. **No risk is "everything could go wrong."** That's not a risk, that's anxiety. Risks are specific.
2. **A risk without a decision is just a worry.** Every high-rated risk gets one of accept / mitigate / transfer / avoid. No exceptions.
3. **Mitigation actions go into the tracker.** A mitigation that lives only in the risk register is a mitigation that won't happen.

## Field note

The most useful brainstorm is the one where you find a risk you'd missed. If the exercise produces only "things you already knew," you didn't push hard enough. Five minutes per bucket is the floor :  you can keep going if real new risks are still emerging.

The other useful output: risks you decided to **accept**. Documenting the acceptance is what turns "we got blindsided" into "we knew, we accepted, we moved on." Big difference for the closeout memo.

## Related patterns

- [parking-lot](parking-lot.md) :  medium/low risks live here; promote when likelihood rises
- [constraint-matrix](constraint-matrix.md) :  risks against the most-constrained parameter need the strongest mitigations
- [mitar-loop](mitar-loop.md) :  ongoing monitoring of identified risks happens through MITAR

## Source

Adapted from BYU PM Process Guide, section 2.3.3 ("Create the Risk Management Plan"). Original distinguished a longer list of categories; we collapsed to scope/schedule/resources to align with the constraint matrix and stay legible at small scale.
