---
name: engagement-ops
description: Run client engagements with consistent rigor. Use when starting, prepping, journaling, tracking, or closing any Catalyst Works client engagement (Signal Session, SHIELD, advisory, paid call). Triggers on "engagement", "client kickoff", "session prep", "Signal Session prep", "SHIELD kickoff", "session notes", "deliverable tracker", "client closeout", "wrap up the engagement", or when a real client name is mentioned in a planning context. Pulls selectively from the PM rigor library at docs/reference/pm-rigor-library/. Internal projects use the roadmap skill instead, but can still pull rigor patterns the same way.
---

# Engagement Ops

The operator for client work. Four artifacts per engagement. Each artifact pulls only the rigor patterns that earn their keep at the engagement's scale. Skip the rest.

## When this fires

| Phrase | What I do |
|---|---|
| "Signal Session with [name]", "I have [X] booked", "client kickoff" | Create or open the engagement folder, draft the brief |
| "session prep", "prep for [client]", "before the call" | Open existing brief, check prework list, refresh context |
| "session notes", "wrapped [client]", "log the session" | Append to session-notes.md, surface follow-ups |
| "deliverable tracker", "what's owed", "what's late" | Open tracker, status each deliverable |
| "close out [client]", "wrap up the engagement", "closeout memo" | Pull closeout-meeting pattern, draft memo, propose next-engagement candidate |

If the user is talking about an internal build (no external client), say so and route to the roadmap skill. Patterns can still be pulled either way.

## Where artifacts live

```
docs/engagements/<client-shortname>/
├── engagement-brief.md       (created at kickoff)
├── session-notes.md          (append-only journal)
├── deliverable-tracker.md    (updated as commitments are made)
└── closeout-memo.md          (created at end)
```

**Client shortname rule:** lowercase, hyphenated, recognizable. Use the client company name, not a codename. Examples: `westridge-logistics`, `acme-trucking`, `forge-partners`. If the engagement is with a person not tied to a company, use first-last (`mike-jensen`).

Internal projects use `docs/roadmap/<codename>.md` via the roadmap skill instead. Codenames are evocative one-word names (`atlas`, `harvest`, `concierge`).

## The four artifacts

### 1. Engagement Brief (`engagement-brief.md`)

Created the moment a paid engagement is booked. Written before the kickoff session.

Required sections:

- **Header:** type (Signal Session / SHIELD / Advisory / Custom), client name + role + company, booked date, session date, status
- **Objective Statement** :  pull `objective-statement` pattern. 25 words or fewer.
- **Completion criteria** :  pull `completion-criteria` pattern. What "money well spent" looks like in their words.
- **Constraint snapshot** :  pull `constraint-matrix` (light version). Which of scope / schedule / resources is most constrained, moderately, least, and the implication.
- **Prework checklist** :  concrete items to do before the session. Always include: pull public footprint, run pre-session diagnostic, send pre-session email, Honest Mirror prep.
- **In-session structure** :  time-boxed agenda. For Signal Session, default to OS v2.0 scaled to the booking length. For SHIELD, default to AMPLIFY-anchored kickoff.
- **Risks (parking lot)** :  pull `parking-lot` pattern. Capture, don't process.
- **After-session deliverable** :  what's owed, by when.
- **Patterns pulled / deliberately not pulled** :  log the decision. This is how we learn what rigor earns its keep at each scale.

### 2. Session Notes (`session-notes.md`)

Append-only journal. One entry per session.

Each entry has:

- **Date + duration**
- **What they said in their own words** (the real signal :  quotes if possible)
- **What was decided**
- **What surprised you**
- **Follow-ups generated** (each one goes to the tracker)

For SHIELD-style multi-session engagements, also append: **constraint-matrix re-read** :  has any of scope/schedule/resources shifted? Triggers a tracker update if yes.

### 3. Deliverable Tracker (`deliverable-tracker.md`)

Simple table. Updated whenever a commitment is made or fulfilled.

| Deliverable | Owner | Owed by | Status | Notes |
|---|---|---|---|---|
| 1-page Signal Memo | BB | YYYY-MM-DD | not started / drafting / shipped | |
| SHIELD proposal decision | BB | YYYY-MM-DD | open / sent / declined | |

Status values are tight: `not started`, `drafting`, `in review`, `shipped`, `late`, `cancelled`. No improvising.

When something goes `late`, the next session-notes entry must include a one-line reason. This is the lightweight version of MITAR :  Monitor, Investigate, Take Action, Report :  without the enterprise weight.

### 4. Closeout Memo (`closeout-memo.md`)

Created within 5 days of last session. Pull `closeout-meeting` pattern.

Three sections only:

- **Successes** :  what worked, in their words and yours
- **Challenges** :  what didn't, what you'd change next time
- **Lessons learned** :  things to bake into future engagements (these can graduate into pattern library updates)

Plus one decision section:

- **Next-engagement candidate?** Yes / No / Maybe + reason. If yes, what shape (SHIELD / advisory / referral introduction)?

If a closeout memo produces a lesson worth keeping, propose adding it to either the relevant pattern in the rigor library or to MEMORY.md as a feedback entry. Don't auto-write :  propose, then ask.

## Pulling from the rigor library

The library lives at `docs/reference/pm-rigor-library/`. See `_index.md` there for the full catalog.

**Default pulls** for each engagement type (always pulled unless the user says otherwise):

| Engagement type | Default patterns |
|---|---|
| Signal Session ($497, 90 min) | objective-statement, completion-criteria, constraint-matrix (light), parking-lot |
| SHIELD kickoff (multi-week, $20K+) | objective-statement, completion-criteria, constraint-matrix (full), risk-brainstorm, stargate-checkpoint, mitar-loop (light), parking-lot |
| Advisory retainer (recurring) | objective-statement, completion-criteria, mitar-loop (light) |
| Custom / TBD | ask which patterns the user wants pulled |

**Always at closeout:** `closeout-meeting` pattern, regardless of engagement type.

**Never auto-pulled** (only on explicit request): WBS-style task decomposition (use superpowers:writing-plans for software builds instead), full Risk Management Plan with quantitative scoring (overkill for any engagement < $50K).

When pulling a pattern, name it explicitly in the artifact under "Patterns pulled" so future you knows what was used and what was skipped.

## Composition with other skills

| Skill | Handoff |
|---|---|
| **discovery-call-system** | Discovery call ends → engagement-ops takes the booking signal. The discovery call output (the diagnostic seed) becomes the first paragraph of the engagement brief. |
| **roadmap** | Long engagements (SHIELD multi-week) can ALSO have a roadmap entry. Codename = client shortname. Roadmap tracks living state, engagement folder holds the artifacts. |
| **superpowers:writing-plans** | If an engagement requires a software-style build (e.g., custom dashboard for the client), use writing-plans for the implementation plan and link it from the engagement brief. |
| **superpowers:brainstorming** | Use before drafting an engagement brief if the engagement shape is ambiguous. The brainstorming output seeds the brief. |
| **sankofa** | Use to pressure-test a SHIELD proposal before sending. Use to pressure-test a tough closeout decision. |

## What this skill is NOT

- Not a CRM. Lead pipeline lives in Notion + Supabase.
- Not a methodology library. The library is a separate folder. This skill consumes it; it does not own it.
- Not a substitute for the discovery call. The first conversation about whether to engage is its own skill.
- Not for internal builds. Use the roadmap skill for those.

## Failure modes to watch for

- **Process LARP at small scale.** A Constraint Matrix on a $497 Signal Session takes 3 minutes. A full Risk Management Plan on a $497 Signal Session is theatre. Pull the light version, skip the heavy one.
- **Artifact drift.** If the brief and the session-notes contradict each other (e.g., the brief says "scope most constrained," the notes say "we expanded scope mid-session"), update the brief or note the contradiction explicitly. Don't let the file rot.
- **Closeout skipped.** The closeout memo is where lessons compound. If it gets skipped for 3 engagements in a row, the rigor library never gets sharper. Always do the 5-day closeout, even if it's 200 words.
