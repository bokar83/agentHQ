---
name: cw-automation-engagement
description: Operationalizes the Catalyst Works AI automation delivery engagement. Phase 3 scope: find a free case study client, build their automation, document results, capture testimonial. Triggers on "automation engagement", "case study client", "build automation for", "n8n engagement", or "cw automation".
---

# CW Automation Engagement

**Acceptance criterion (locked before any content below):**
First CW automation engagement scoped and priced using this skill by 2026-07-04.
Success = case study doc exists with: client name, task automated, hours saved/week, testimonial quote.

**v1 scope:** Phase 3 only: acquire and deliver one free case study engagement.
Phases 4-6 (packaging, pricing, acquisition) added only after first paid engagement closes.

**Tool dependency:** n8n-mcp MCP server (installed 2026-05-04 via `npx n8n-mcp`).
Gives Claude expert knowledge of 1,650 n8n nodes + 2,352 templates. Always available in session.

---

## When to Use This Skill

- User says "find a case study client" or "first automation engagement"
- User has an n8n workflow to build for a client
- User wants to scope/price an automation engagement
- Post-engagement: capture results and testimonial

---

## Phase 3: Case Study Acquisition (v1, full scope)

### Step 1: Find the right person

Target profile (all three must be true):
1. In CW's existing network (LinkedIn 1st-degree, BNI, South Valley Chamber, past warm leads)
2. Has a recurring task that is process-driven and takes 3+ hours/week (see qualifying questions below)
3. Willing to give a written testimonial if the automation delivers

Qualifying questions (ask in a 15-min call or DM):
- "What task do you do every week that you hate the most?"
- "If I could eliminate that task entirely, would you be willing to let me try, for free, and give me feedback afterward?"
- "How many hours a week does it take today?"

Disqualify if:
- Task requires human judgment on every instance (not process-driven)
- No clear digital input/output (pure physical work)
- They want full access to their production systems immediately (no sandbox path)

### Step 2: Scope the automation (30 min)

Run a discovery interview. Extract:

| Field | Question to ask |
|---|---|
| Trigger | "What starts this task? An email? A form? A schedule?" |
| Input data | "What information does the task need to run?" |
| Steps | "Walk me through each step you take, in order." |
| Output | "What does done look like? A file? A message? An entry?" |
| Current time | "How long does this take you per run? Per week?" |
| Tools involved | "What apps or systems do you touch during this task?" |

Map to n8n node types after the call. Use n8n-mcp `search_nodes` to confirm coverage.

Minimum viable automation rule: automate the single most painful step first. Not the whole workflow.

### Step 3: Build the automation

Pre-build checklist:
- [ ] Confirm n8n instance available (client's self-hosted, n8n cloud, or agentsHQ VPS)
- [ ] Credentials scoped: never ask for production API keys before sandbox test passes
- [ ] Template search done: `search_templates({query: '<task keyword>'})` - check before building from scratch

**Automation brief (write this before touching n8n-mcp tools):**

```
Goal:    <one sentence — what outcome does the client get?>
Steps:   1. <first atomic action> → 2. <next> → 3. <next> ...
Tools:   <app/service per step, e.g. Gmail → Airtable → Slack>
```

This brief is the contract between discovery and build. If the brief is vague, the n8n workflow will be vague. Write it before any template search. Avoid vague instructions like "process the data" — every step must name a concrete action and a concrete system.

Build protocol:
1. `search_templates` - find closest match (2,352 available)
2. `search_nodes` for each service the client uses
3. `get_node` for every node you'll use - never rely on defaults
4. `validate_node` before wiring
5. Build in sandbox/dev first, never production
6. `validate_workflow` before handing to client
7. Run a live test with real (non-sensitive) data in client's presence

Safety rule (from n8n-mcp README): NEVER edit production workflows directly with AI. Always copy first.

### Step 4: Deliver and document

Delivery session (30-60 min with client):
1. Walk through the workflow in n8n UI - show them what each node does
2. Trigger it live with their real data
3. Show them how to monitor executions
4. Leave a one-page "what this does + how to pause it" doc

Measure immediately after delivery:
- Hours saved per week (client's estimate)
- Before/after time comparison
- Any errors in first week (follow up at day 7)

### Step 5: Capture the case study

Case study template (fill after 2-week run):

```markdown
# Case Study: [Client Name] - [Task Automated]

**Client:** [Name, Role, Company, Industry]
**Task automated:** [one sentence]
**Before:** [X hours/week, manual steps]
**After:** [Y minutes/week, automated]
**Time saved:** [X - Y per week = Z hours/month]
**Stack:** n8n + [nodes used]
**Build time:** [hours from discovery to delivery]

## What they said
"[Testimonial quote, exact words, approved by client]"

## How it works (one paragraph)
[Plain language description of the workflow for prospects to understand]

## Replication complexity
[Simple / Medium / Complex]: [one sentence on what would need to change for another client]
```

Save to: `deliverables/case-studies/[client-slug]-automation-[YYYY-MM].md`

### Step 6: Package for next engagement

After case study is captured:
- Add to CW Signal Session intake: "Do you have recurring tasks taking 3+ hours/week?"
- Add automation delivery as an explicit CW offer (price band: $3K-$5K build + $500-$1K/month)
- Wire case study into cold outreach template as social proof

Trigger for v2 skill expansion (Phases 4-6): first case study doc exists + first paying engagement closed.

---

## n8n-mcp Quick Reference

Most useful tools for client engagements:

| Tool | When to use |
|---|---|
| `search_templates` | Before building anything: check 2,352 templates first |
| `search_nodes` | Find nodes for a specific service (e.g. "gmail", "slack", "airtable") |
| `get_node` | Get exact parameter names: never guess, defaults fail at runtime |
| `validate_node` | Catch missing required fields before wiring |
| `validate_workflow` | Full check before delivery or deploy |
| `n8n_create_workflow` | Deploy directly to client's n8n instance (needs API key) |

Critical rule from n8n-mcp docs: **never trust defaults**. Always explicitly configure ALL parameters. Default values are the #1 source of runtime failures.

---

## Pricing (locked, do not quote below these floors)

| Engagement type | Price |
|---|---|
| Free case study (first one only) | $0, in exchange for testimonial + case study rights |
| Build engagement | $3,000-$5,000 one-time |
| Complex build (multi-agent, custom MCP, cross-platform) | $5,000-$15,000 |
| Monthly maintenance + optimization | $500-$1,000/month |

ROI framing: if automation saves 10 hrs/week at $75/hr billing rate = $3,000/month value. $3K-$5K one-time is a no-brainer.

---

## Cross-References

- Roadmap: `docs/roadmap/harvest.md` milestone R-automation
- n8n-mcp repo: https://github.com/czlonkowski/n8n-mcp
- n8n-mcp dashboard: https://dashboard.n8n-mcp.com (free tier: 100 tool calls/day)
- Source methodology: X-thread @eng_khairallah1 6-phase AI automation agency playbook
- Absorb log: `docs/reviews/absorb-log.md` 2026-05-04 entries
- Case studies output: `deliverables/case-studies/`
