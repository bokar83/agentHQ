# `/agentshq-absorb` Design Spec

**Date:** 2026-05-02
**Owner:** Boubacar
**Status:** Draft, awaiting Sankofa + Karpathy review before implementation

---

## Purpose

Codify the manual workflow Boubacar runs every time he evaluates a GitHub repo, live URL, or other artifact for inclusion in agentsHQ. Output is a structured one-pager verdict (PROCEED / DON'T PROCEED / ARCHIVE-AND-NOTE) with placement recommendation and runner-up. Replaces retyping the protocol every time.

## Trigger surface

- User says "absorb", "should we absorb", "evaluate this for agentsHQ", "is this worth adding", "review this repo for agentsHQ"
- User invokes `/agentshq-absorb <input>`
- **User pastes a bare GitHub URL with no other context.** Auto-fires `/agentshq-absorb`. Does NOT install.

The skill name `agentshq-absorb` auto-resolves as the slash command. No separate file in `.claude/commands/` (matches `nsync`, `tab-shutdown` pattern).

### Hard rule: bare URL = absorb, never install

A bare GitHub URL with no other context **always** triggers this skill. It never triggers an install, clone-and-run, dependency install, or any other action that touches the agentsHQ environment. The shallow clone in Phase 1 lives in `sandbox/.tmp/absorb-<slug>/` and is read-only analysis.

**Install only fires when the user explicitly says so.** Trigger phrases for install (handled by other skills, NOT this one):

- "install this repo" + URL
- "install <name>" + URL
- "add this to agentsHQ" + URL (after a prior absorb verdict)
- "wire this up" + URL

If the user pastes a bare URL and the agent is uncertain whether they want absorb or install: default to absorb. Surface the install option in the verdict's "Next action" line.

*Why: Boubacar pastes repos constantly to evaluate fit. Auto-installing on a bare URL would pollute the environment with dependencies of things he was just considering. Absorb is read-only and reversible; install is not.*

## Inputs accepted (v1)

| Pattern | Type | Fetcher |
|---|---|---|
| `github.com/owner/repo` | repo | `git clone --depth 1` |
| Repo with `mcp.json` or MCP-mentioning README | mcp-server | clone + parse manifest |
| `*.json` URL or pasted JSON with `"nodes":` and `"connections":` | n8n-workflow | fetch + parse |
| `http(s)://...` ending in `.pdf` | pdf | Read tool with `pages:` |
| `http(s)://...` ending in `.md` / `.txt` | raw-doc | fetch |
| `http(s)://...` (live site) | live-site | Firecrawl scrape |
| Local path containing `SKILL.md` | skill | read in place |
| Local path to `.pdf` / `.md` / `.txt` | raw-doc | Read in place |
| Pasted text > 500 chars | raw-doc | use as-is |
| Else | unknown | ask once, bail |

## Pipeline (six phases)

### Phase 1: Detect and Fetch

Auto-detect from input pattern (table above). Fetch into `sandbox/.tmp/absorb-<slug>/`. If detection ambiguous, ask one clarifying question, then bail if no answer.

### Phase 2: Registry check

Grep `docs/reviews/absorb-log.md` for the URL/slug. If found, surface prior verdict in chat:

```
Prior verdict found:
  Date: 2026-04-12
  Verdict: DON'T PROCEED
  Placement: archive-and-note
  Reason: 80% overlap with clone-builder

Re-evaluate, or use prior verdict?
```

If user picks prior, skip the rest. Otherwise continue.

**Re-eval flag:** if prior verdict is older than 90 days OR `docs/SKILLS_INDEX.md` has changed by ≥10 skill entries since prior eval, prepend a "TAXONOMY DRIFT, re-eval recommended" line to the prior verdict surface.

### Phase 3: Deep artifact analysis

No shortcuts. Read everything that defines what the artifact is and what it does.

**For repos:**
- README, all top-level docs, `SKILL.md` if present
- Manifests: `package.json`, `pyproject.toml`, `requirements.txt`, `Cargo.toml`, `go.mod`
- Every entrypoint file
- Directory tree
- `.env.example`
- Dependency surface
- License
- Last commit date, open issues count
- Walk actual code paths: what does it do, how, what does it depend on, what does it expose
- Red flags: abandonware (>12mo no commits), sketchy deps, unclear license, secrets in repo

**For MCP servers:** all of the above + transport (stdio/HTTP), tools exposed, auth method, manifest contents.

**For n8n workflows:** trigger type, node count, credentials needed, external services touched, error-handling presence.

**For live URLs:** full Firecrawl crawl (not just landing), tech stack detection, what they sell/offer/explain, who runs it, contact surface, freshness signals.

**For raw docs / PDFs:** full read, extract claims, identify what concrete capability or pattern is described.

**For skills:** read `SKILL.md` + every supporting file, understand the full workflow, map every tool/script/agent it invokes.

**Output of Phase 3:** structured "artifact dossier":

```
ARTIFACT DOSSIER : <name>
=========================
What it is: <one paragraph>
What it does: <bullet list of capabilities>
How it works: <high-level mechanism>
Dependencies: <list>
Cost: <license / infra / complexity>
Risks: <list, or "none flagged">
```

### Phase 4: Placement proposal

Read `docs/SKILLS_INDEX.md` (live ground truth, 74 skills as of 2026-05-02). Cross-reference with `skills/boubacar-skill-creator/patterns/skill-taxonomy.json` for cluster categorization.

**Decision order (run all four before recommending):**

1. **Near-duplicate check.** Is there a skill with ≥70% capability overlap? → propose **extension**, not new skill.
2. **Cluster check.** Which existing skill cluster does this fit (web-building, lead-gen, content, design, video, etc.)? → name the cluster and propose extending the strongest skill in it.
3. **Capability gap check.** Does this fill a real gap none of the 74 skills cover? → propose **new skill**.
4. **Below-skill check.** Is this just a tool/script that an existing skill should call? → propose **tool**, not skill.

Output: chosen placement + named runner-up + one-line reason for runner-up rejection.

### Phase 5: Sankofa and Karpathy on the proposal

Run both, in sequence, on the placement decision (not on the artifact's internals). Per `feedback_audits_before_implementation.md`: audits run on the plan, not just on shipped code.

- **Sankofa Council:** five voices stress-test "is this the right home for this thing?" (Contrarian challenges the premise of adopting it at all; First Principles asks if the question is even right; Expansionist hunts for missed leverage; Outsider reads cold; Executor names the next concrete move). v1 uses the local in-IDE Sankofa skill (`skills/sankofa/SKILL.md`, single-LLM five-voice prompt), not the orchestrator's parallel-LLM version. v2 may route to the orchestrator for higher-stakes absorb decisions.
- **Karpathy audit:** four principles applied to the integration plan. Think Before Coding (intent stated?), Simplicity First (minimum integration?), Surgical Changes (touches only what must change?), Goal-Driven Execution (verifiable success criteria?).

Both outputs feed the verdict.

### Phase 6: Verdict and log

Render structured one-pager (see Output Format below). Append one line to `docs/reviews/absorb-log.md`:

```
2026-05-02 | https://github.com/owner/repo | PROCEED | extend skills/clone-builder
```

## Output format (the one-pager)

Single chat message, top-to-bottom:

```
ABSORB VERDICT : <artifact name>
================================
<PROCEED | DON'T PROCEED | ARCHIVE-AND-NOTE>

Why (3 lines max):
- <reason 1>
- <reason 2>
- <reason 3>

Placement: <extend skills/X | new skill skills/Y | new tool | new agent | archive>
Runner-up: <other option>. Rejected because <one line>.

Next action: <one specific concrete next step>
```

Below that, four collapsed `<details>` sections:

- **What it is.** Phase 3 dossier.
- **Sankofa Council.** Five voices + chairman.
- **Karpathy audit.** Four principles, PASS/FAIL/WARN per principle.
- **Placement reasoning.** Why chosen home wins, why runner-up loses.

Per `feedback_report_voice_executive_not_designer.md`: exec voice not engineer voice; verdict in 1 sentence; details collapsed.

## File layout

```
skills/agentshq-absorb/
  SKILL.md                    # the protocol; auto-resolves as /agentshq-absorb
  references/
    detect-fetch.md           # Phase 1 detection rules + fetch commands
    dossier-template.md       # Phase 3 dossier structure
    placement-rubric.md       # Phase 4 decision rules
    output-template.md        # Phase 6 one-pager template

docs/reviews/
  absorb-log.md               # registry; one line per evaluation
  README.md                   # what this folder is, how to read the log

sandbox/.tmp/absorb-<slug>/   # temp clone/scrape working dir (sweep on 30d)
```

**No manual edit to `docs/SKILLS_INDEX.md`.** The `scripts/lint_and_index_skills.py` pre-commit hook owns it.
**No manual edit to `AGENTS.md`.** Table was retired; `SKILLS_INDEX.md` is the live source of truth.
**`nsync` skill auto-symlinks** new skill into `.agents/skills/` for Antigravity.

## Architecture decisions

### Codify, don't innovate
This skill is a faithful encoding of the manual workflow Boubacar already runs. Light on novelty, heavy on matching what works today. Per `feedback_existing_stack_first.md`.

### Two contexts, one protocol
- **Claude Code shortcut version:** this skill. Interactive, runs in the IDE, used when Boubacar is at the keyboard.
- **Orchestrator runtime version:** the `skill_builder` agent + `skill_build` task type already in `agents.py`. Autonomous, runs on the VPS, triggered by Telegram.

Both share the same protocol. v1 ships only the Claude Code version. Orchestrator integration is a future task.

### Sankofa + Karpathy on the proposal, not the artifact
The artifact's internal code quality matters less than whether absorbing it would help or hurt agentsHQ. That's a placement question. Karpathy fits perfectly for "is this integration surgical?" Sankofa fits perfectly for "is the premise of adopting this even right?" Running them on the artifact itself produces noise (every random repo has style issues that don't matter to us).

### Make the placement call, show the runner-up
Per `feedback_make_educated_decisions.md`: don't paginate three-way verdicts on routine triage. Skill picks one placement, names the runner-up and why it lost. Boubacar overrides if he disagrees. One-line audit trail makes wrong calls easy to catch.

### Registry prevents re-evaluation churn
Append-only log at `docs/reviews/absorb-log.md`. Cheap. Solves the obvious failure mode (re-evaluating the same repo). No separate "rejected ideas" file. The registry already captures rejection reason in one column.

## Out of scope (v2 parking lot)

- **Notion templates.** Notion's API for templates is awkward; templates aren't first-class. Real design work needed.
- **Auto-execute the placement decision.** A second skill, not a feature. Needs its own brainstorm: how to extend a skill, write tests, run the writing-skills loop.
- **Bulk mode.** Concurrency, rate limits on Firecrawl/git clone, partial failures, output formatting for N artifacts. v1 doesn't need it (manual one-at-a-time today).

## Success criteria

1. Pasting a GitHub URL with `/agentshq-absorb` produces a verdict + placement in one chat message.
2. The dossier is accurate enough that Boubacar doesn't need to open the repo himself to sanity-check.
3. Sankofa and Karpathy outputs are real reviews, not boilerplate.
4. Registry entry is appended on every run.
5. Re-running on a known URL surfaces the prior verdict.
6. Auto-detection correctly classifies all v1 input types (repo, MCP, n8n, PDF, raw doc, live site, local skill).

## Open implementation questions (for the writing-plans phase)

1. How does the skill invoke Sankofa and Karpathy: direct skill invocation or via the orchestrator's `skill_run` capability?
2. Should the dossier be written to a file in `sandbox/.tmp/absorb-<slug>/dossier.md` so it's grep-able later, or only kept in chat context?
3. Slug generation rule for the registry: `<host>-<owner>-<repo>` for GitHub, `<host>-<path>` for live sites, hash for raw text?
4. What's the exact threshold for the "taxonomy drift" re-eval flag: count of skills changed, or also dates of changes?

These get resolved in the implementation plan, not now.

---

## Pre-implementation gates (per CLAUDE.md / AGENT_SOP.md)

Before any code is written:

1. **This spec is reviewed by Boubacar.** (we are here.)
2. **Sankofa Council runs on this spec.** Five voices, full output, no softening.
3. **Karpathy audit runs on this spec.** Four principles, PASS/FAIL/WARN per principle.
4. **Boubacar reviews Sankofa + Karpathy output.** Approve, revise, or kill.
5. Only then: invoke `superpowers:writing-plans` to produce the implementation plan.
6. Implementation plan also gets Sankofa + Karpathy before any code (per `feedback_audits_before_implementation.md`).
