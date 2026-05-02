# `/agentshq-absorb` Design Spec (v2)

**Date:** 2026-05-02
**Owner:** Boubacar
**Status:** Draft, post Sankofa + Karpathy round 2, awaiting writing-plans

---

## Purpose

Codify the manual workflow Boubacar runs every time he evaluates a GitHub repo, live URL, MCP server, n8n workflow, PDF, raw doc, or local skill for inclusion in agentsHQ. Replaces retyping the protocol every time. Default verdict bias: enhance an existing skill, not build a new one.

## The agentsHQ leverage filter (Phase 0 gate)

Every artifact runs through three questions. **Any yes continues the pipeline. All no = ARCHIVE-AND-NOTE and stop.**

1. **Direct producing-motion strengthening.** Does this strengthen a current producing motion?
   - SW website builds (Signal Works pipeline)
   - CW PDF / deliverable generation (Catalyst Works consulting outputs)
   - Lead-gen (Apollo, Hunter, cold, warm, lead magnets, follow-up sequences)
   - Content board (LinkedIn / X / newsletter / Boubacar voice motion)
   - Atlas autonomy infrastructure (heartbeats, publish loops, learning crews, VPS hardening)
   - Studio / channel cloner pipeline / video production
   - Future producing motions (name them in the verdict)
2. **Founder-time reduction.** Does this remove Boubacar from a process he currently does by hand, or reduce review/approval time on a recurring loop? (Examples: design auto-approval, content auto-publish, review gates that no longer need his eyes.) Anything that multiplies output by removing Boubacar from the loop counts.
3. **Continuous improvement.** Does this measurably enhance one of the existing 74 skills so it does its job better?

If at least one answer is yes, name it explicitly and continue. The named leverage type rides through every later phase and lands in the verdict + registry.

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

If uncertain whether the user wants absorb or install: default to absorb. Surface the install option in the verdict's "Next action" line.

*Why: Boubacar pastes repos constantly to evaluate fit. Auto-installing on a bare URL would pollute the environment with dependencies of things he was just considering. Absorb is read-only and reversible; install is not.*

## Inputs accepted (v1)

| Pattern | Type | Fetcher |
|---|---|---|
| `github.com/owner/repo` | repo | `git clone --depth 1` |
| Repo with `mcp.json` or MCP-mentioning README | mcp-server (clone) | clone + parse manifest |
| Pip package starting with `mcp-server-` or marked MCP in PyPI | mcp-server (pip) | `pip show` metadata + PyPI README, no install |
| URL to a hosted MCP endpoint (`/sse` or `/mcp` path) | mcp-server (remote) | introspect manifest endpoint |
| `*.json` URL or pasted JSON with `"nodes":` and `"connections":` | n8n-workflow | fetch + parse |
| `http(s)://...` ending in `.pdf` | pdf | Read tool with `pages:` |
| `http(s)://...` ending in `.md` / `.txt` | raw-doc | fetch |
| `http(s)://...` (live site) | live-site | Firecrawl scrape |
| Local path containing `SKILL.md` | skill | read in place |
| Local path to `.pdf` / `.md` / `.txt` | raw-doc | Read in place |
| Pasted text > 500 chars | raw-doc | use as-is |
| Else | unknown | ask once, bail |

## Pipeline

### Phase 0: Leverage gate

Apply the three-question leverage filter above. If all three answer no, write ARCHIVE-AND-NOTE verdict (with reason) and stop. Otherwise name the leverage type(s) and continue.

### Phase 1: Detect, fetch, and check registry

Auto-detect input type from the table above. Fetch into `sandbox/.tmp/absorb-<slug>/`. Grep `docs/reviews/absorb-log.md` for the URL/slug. If a prior verdict exists, surface it in chat:

```text
Prior verdict found:
  Date: 2026-04-12
  Verdict: PROCEED
  Placement: enhance skills/website-intelligence
  Leverage: SW website quality

Re-evaluate, or use prior verdict?
```

If user picks prior, stop. Otherwise continue.

(Re-eval drift detection moved to v2 parking lot per Karpathy WARN.)

### Phase 2: Deep artifact analysis

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

**For MCP servers (any flavor):** all of the above + transport (stdio / HTTP / SSE), tools exposed, auth method, manifest contents, install path (clone, pip, remote).

**For n8n workflows:** trigger type, node count, credentials needed, external services touched, error-handling presence.

**For live URLs:** full Firecrawl crawl (not just landing), tech stack detection, what they sell/offer/explain, who runs it, contact surface, freshness signals.

**For raw docs / PDFs:** full read, extract claims, identify what concrete capability or pattern is described.

**For skills:** read `SKILL.md` + every supporting file, understand the full workflow, map every tool/script/agent it invokes.

**Output of Phase 2:** structured artifact dossier:

```text
ARTIFACT DOSSIER : <name>
=========================
What it is: <one paragraph>
What it does: <bullet list of capabilities>
How it works: <high-level mechanism>
Dependencies: <list>
Cost: <license / infra / complexity>
Risks: <list, or "none flagged">
Leverage type (from Phase 0): <direct producing-motion | founder-time-reduction | continuous-improvement>
```

### Phase 3: Placement proposal

Read `docs/SKILLS_INDEX.md` (live ground truth, 74 skills as of 2026-05-02). Cross-reference with `skills/boubacar-skill-creator/patterns/skill-taxonomy.json` for cluster categorization. **If the two disagree, `SKILLS_INDEX.md` wins** (auto-generated, can't drift).

**Decision order. Default toward extension, not new skill:**

1. **Continuous-improvement check.** Does this enhance any of the 74 existing skills' capability or quality? If yes → propose **enhance skill X**. This is the dominant case; new skills are the exception.
2. **Near-duplicate check.** Skill with capability overlap (top 3 trigger phrases share intent, OR description overlaps in core capability)? Propose **extend skill X**.
3. **Cluster check.** Fits a recognized cluster (web-building, lead-gen, content, design, video, autonomy infra, etc.)? Propose extending the strongest skill in that cluster.
4. **Capability gap check.** Real gap none of the 74 skills cover, AND step 1 returned no? Propose **new skill**.
5. **Below-skill check.** Just a tool/script that an existing skill should call? Propose **tool**, lives in the consuming skill's directory or `skills/<skill>/scripts/`.
6. **Satellite check.** Has its own URL, customer, or revenue stream per AGENTS.md? Propose **satellite repo**, referenced from agentsHQ but lives in its own GitHub repo.

Output: chosen placement + named runner-up + one-line reason for runner-up rejection.

**On the 70% threshold from v1:** dropped. Replaced with the procedural test in step 2 (top-3 trigger phrase intent overlap, OR core capability overlap in description). The skill applies the test by reading both descriptions, not by computing a numeric score.

### Phase 4: Sankofa and Karpathy on the proposal

Run both, in sequence, on the placement decision (not on the artifact's internals). Per `feedback_audits_before_implementation.md`: audits run on the plan, not just on shipped code.

**Sankofa Council** uses the leverage-filter lens explicitly:

- Contrarian: "Will this actually reduce Boubacar's time, strengthen the named producing motion, or improve the named skill, or just feel like it does?"
- First Principles: "What is the producing motion, founder-time leak, or skill weakness this strengthens? Name it."
- Expansionist: "What adjacent producing motion or auto-approval loop would this also strengthen that the proposal missed?"
- Outsider: "If a stranger ran agentsHQ a year from now, would they thank us for absorbing this?"
- Executor: "Name the integration date and the metric that proves the leverage materialized."

v1 uses the local in-IDE Sankofa skill (`skills/sankofa/SKILL.md`, single-LLM five-voice prompt), not the orchestrator's parallel-LLM version. v2 may route to the orchestrator for higher-stakes absorb decisions.

**Karpathy audit** on the integration plan: Think Before Coding, Simplicity First, Surgical Changes, Goal-Driven Execution.

Both outputs feed the verdict.

### Phase 5: Verdict, log, and follow-up handoff

Render the structured one-pager (see Output Format below). Then write two lines:

**Append to `docs/reviews/absorb-log.md`** (master registry):

```text
2026-05-02 | https://github.com/owner/repo | PROCEED | enhance skills/website-intelligence | SW website quality
```

Columns: date, source, verdict, placement, leverage type.

**Append to `docs/reviews/absorb-followups.md`** (PROCEED only, lightweight follow-up tracker):

```text
2026-05-02 | enhance skills/website-intelligence | SW website quality | wire <feature> into web-intel scraper | by 2026-05-15
```

Columns: date, placement, leverage type, next action, target date. PROCEED without a written follow-up = PROCEED is incomplete; the skill refuses to finalize the verdict until the next-action and target-date are populated.

## Verdict types (defined)

- **PROCEED** = absorb the artifact. Phase 0 named at least one leverage type. Placement decision made. Follow-up appended.
- **DON'T PROCEED** = artifact is harmful, redundant, or actively conflicts with agentsHQ. Logged with reason. No follow-up. Use rare; this is the "do not absorb, do not save for later" case.
- **ARCHIVE-AND-NOTE** = artifact is interesting but no leverage type names today. Logged so we can grep it later if a producing motion needs it. No follow-up. This is the common "nice but not now" case.

## Placement options (defined)

- **enhance skills/X** = add a feature/capability to X without changing its core scope.
- **extend skills/X** = bigger surface change to X, may affect triggers or core flow.
- **new skill skills/Y** = creates a new SKILL.md folder. Reserved for capability gaps where no existing skill is a reasonable host.
- **new tool** = a script, helper, or reference doc that an existing skill calls. Lives in the consuming skill's directory (`skills/<skill>/scripts/foo.py` or `skills/<skill>/references/foo.md`).
- **new agent** = orchestrator-side CrewAI agent definition. Reserved for runtime autonomy capabilities, not Claude Code workflow capabilities.
- **satellite repo** = product with its own URL/customer/revenue. Lives in its own GitHub repo per AGENTS.md "Platform With Satellites" rule.

## Output format (the one-pager)

Single chat message, top-to-bottom:

```text
ABSORB VERDICT : <artifact name>
================================
<PROCEED | DON'T PROCEED | ARCHIVE-AND-NOTE>

Leverage: <direct producing-motion | founder-time-reduction | continuous-improvement | none>
Motion / target: <SW website builds | CW PDFs | lead-gen | content board | Atlas | Studio | skills/X enhancement | etc.>

Why (3 lines max):
- <reason 1>
- <reason 2>
- <reason 3>

Placement: <enhance skills/X | extend skills/X | new skill skills/Y | new tool | new agent | satellite repo | archive>
Runner-up: <other option>. Rejected because <one line>.

Next action: <one specific concrete next step>
Target date: <YYYY-MM-DD>
```

Below that, four collapsed `<details>` sections:

- **What it is.** Phase 2 dossier.
- **Sankofa Council.** Five voices + chairman.
- **Karpathy audit.** Four principles, PASS/FAIL/WARN per principle.
- **Placement reasoning.** Why chosen home wins, why runner-up loses.

Per `feedback_report_voice_executive_not_designer.md`: exec voice not engineer voice; verdict in 1 sentence; details collapsed.

## v1 also includes: one-time absorb-self bootstrap pass

Before the new-artifact evaluator is considered shipped, v1 includes a one-time pass that runs the absorb protocol against each of the 74 existing skills.

**Goal:** produce a clean, audited skill index. Identify duplicates, drift, conflicts, and skills that should be merged. Every future absorb decision is sharper from day one because the placement rubric is comparing against a known-good taxonomy.

**Scope:**
- Run the absorb protocol on each existing skill (input type = local skill, no fetch needed)
- Skip Phase 0 (already absorbed once; the question is "should it stay")
- Output of each: keep / merge-into-X / archive / split / rename
- Aggregate output: a `docs/reviews/absorb-self-2026-05-02.md` report listing every skill with its verdict and recommended action

**Estimated cost:** ~5 min × 74 skills = ~6 hours of Claude time, parallelizable via subagents to ~1.5 hours wall clock if dispatched in batches of 10.

**Why in v1, not v1.1:** the placement rubric in Phase 3 depends on knowing the current state of the 74 skills. Without the audit, the rubric is guessing. Sankofa Expansionist + Boubacar both endorsed this in round 2.

## File layout

```text
skills/agentshq-absorb/
  SKILL.md                    # the protocol; auto-resolves as /agentshq-absorb
  references/
    placement-rubric.md       # Phase 3 decision rules (only kept if >50 lines)

docs/reviews/
  absorb-log.md               # master registry; one line per evaluation
  absorb-followups.md         # PROCEED follow-ups; one line per actionable verdict
  absorb-self-2026-05-02.md   # one-time bootstrap audit of existing 74 skills
  README.md                   # what this folder is, how to read each file

sandbox/.tmp/absorb-<slug>/   # temp clone/scrape working dir (sweep on 30d)
```

**Karpathy WARN addressed:** v1 uses one reference file (placement-rubric.md), inlined into SKILL.md unless it grows beyond 50 lines during implementation. Detection rules and dossier template stay in SKILL.md.

**No manual edit to `docs/SKILLS_INDEX.md`.** The `scripts/lint_and_index_skills.py` pre-commit hook owns it.
**No manual edit to `AGENTS.md`.** Table was retired; `SKILLS_INDEX.md` is the live source of truth.
**`nsync` skill auto-symlinks** new skill into `.agents/skills/` for Antigravity.

## Architecture decisions

### Codify, don't innovate
This skill is a faithful encoding of the manual workflow Boubacar already runs. Light on novelty, heavy on matching what works today. Per `feedback_existing_stack_first.md`.

### Bias toward enhance, not new
Default verdict for a useful artifact is "enhance skills/X." New skills are the exception. The placement rubric runs the continuous-improvement check first to enforce this.

### Two contexts, one protocol
- **Claude Code shortcut version:** this skill. Interactive, runs in the IDE, used when Boubacar is at the keyboard.
- **Orchestrator runtime version:** the `skill_builder` agent + `skill_build` task type already in `agents.py`. Autonomous, runs on the VPS, triggered by Telegram.

Both share the same protocol. v1 ships only the Claude Code version. Orchestrator integration is a future task.

### Sankofa + Karpathy on the proposal, not the artifact
The artifact's internal code quality matters less than whether absorbing it would help or hurt agentsHQ. That's a placement question. Karpathy fits perfectly for "is this integration surgical?" Sankofa fits perfectly for "is the premise of adopting this even right?" Running them on the artifact itself produces noise.

**Round 1 caveat:** running Sankofa in the same Claude turn as the placement decision produces self-friendly output. v2 should route Sankofa to a different model via the orchestrator. v1 accepts this limitation in exchange for shipping speed; the leverage-filter lens in Phase 4 partially compensates by giving the voices a sharper frame.

### Make the placement call, show the runner-up
Per `feedback_make_educated_decisions.md`: don't paginate three-way verdicts on routine triage. Skill picks one placement, names the runner-up and why it lost. Boubacar overrides if he disagrees.

### Verdict creates follow-on
PROCEED without a follow-up entry is incomplete. The skill refuses to finalize. Without this, verdicts are amnesia.

### Registry prevents re-evaluation churn
Append-only log at `docs/reviews/absorb-log.md`. Cheap. Solves the obvious failure mode. The `leverage` column makes the registry searchable by motion.

## Out of scope (v2 parking lot)

- **Notion templates as input type.** Notion's API for templates is awkward; templates aren't first-class. Real design work needed.
- **Auto-execute the placement decision.** A second skill, not a feature. Needs its own brainstorm: how to extend a skill, write tests, run the writing-skills loop.
- **Bulk mode.** Concurrency, rate limits on Firecrawl/git clone, partial failures, output formatting for N artifacts.
- **Taxonomy-drift re-eval flag.** Auto-flag prior verdicts when `SKILLS_INDEX.md` changes by ≥10 entries or 90+ days pass. Speculative for v1.
- **Sankofa via orchestrator (parallel multi-LLM).** v1 uses the local single-LLM Sankofa for shipping speed; v2 routes to orchestrator for high-stakes absorbs.
- **Recurring absorb-self routine.** v1 runs the bootstrap audit once. v1.1 schedules it quarterly via the routine system.

## Success criteria

1. Pasting a GitHub URL with `/agentshq-absorb` produces a verdict + placement + leverage type + follow-up entry in one chat message.
2. The dossier includes all 7 required fields (what it is, what it does, how it works, deps, cost, risks, leverage type).
3. Sankofa output contains 5 distinct voice sections + chairman synthesis. Karpathy output contains 4 principle verdicts.
4. Both registry files are appended on PROCEED. Only the master log on DON'T PROCEED and ARCHIVE-AND-NOTE.
5. Re-running on a known URL surfaces the prior verdict before re-running the pipeline.
6. Auto-detection correctly classifies all v1 input types. Verified against a fixtures/ folder with one example per type and an expected-classification table.
7. Bootstrap absorb-self pass produces a verdict for each of the 74 existing skills. Aggregate report identifies at least one duplicate, drift, or merge candidate (or formally certifies the index is clean).

## Open implementation questions (for the writing-plans phase)

1. How does the skill invoke Sankofa and Karpathy: direct skill invocation or via the orchestrator's `skill_run` capability?
2. Should the dossier be written to a file in `sandbox/.tmp/absorb-<slug>/dossier.md` so it's grep-able later, or only kept in chat context?
3. Slug generation rule for the registry: `<host>-<owner>-<repo>` for GitHub, `<host>-<path>` for live sites, hash for raw text?
4. For the bootstrap absorb-self pass: parallelize via subagents (faster, harder to review) or sequential (slower, cleaner audit trail)?

These get resolved in the implementation plan, not now.

---

## Pre-implementation gates (per CLAUDE.md / AGENT_SOP.md)

Before any code is written:

1. **This v2 spec is reviewed by Boubacar.** (we are here.)
2. Invoke `superpowers:writing-plans` to produce the implementation plan.
3. Implementation plan also gets Sankofa + Karpathy before any code (per `feedback_audits_before_implementation.md`).
