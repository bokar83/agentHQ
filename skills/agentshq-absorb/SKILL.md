---
name: agentshq-absorb
description: Use when evaluating any GitHub repo, live URL, MCP server, n8n workflow, PDF, raw doc, or local skill for inclusion in agentsHQ. Auto-fires on bare GitHub URLs (read-only analysis, never installs). Outputs PROCEED / DON'T PROCEED / ARCHIVE-AND-NOTE verdict with placement (enhance/extend/new skill/new tool/new agent/satellite) and leverage type (producing-motion/founder-time-reduction/continuous-improvement). Triggers on "absorb", "should we absorb", "evaluate this for agentsHQ", "is this worth adding", "review this repo for agentsHQ", "/agentshq-absorb", or a bare github.com URL with no other context.
---

# /agentshq-absorb

Codify Boubacar's manual workflow for evaluating any artifact (GitHub repo, live URL, MCP server, n8n workflow, PDF, raw doc, or local skill) against agentsHQ. Output: structured one-pager verdict + placement + leverage type + follow-up handoff. Default placement bias: enhance an existing skill, not build a new one.

## Hard rule: bare URL = absorb, never install

A bare GitHub URL with no other context **always** triggers absorb. Never install. The shallow clone in Phase 1 lives in `sandbox/.tmp/absorb-<slug>/` and is read-only. Install only fires on explicit "install this repo / install <name> / add this to agentsHQ / wire this up" + URL, and is handled by other skills.

## Phase 0: Leverage gate

Apply three questions. **Any yes continues. All no = ARCHIVE-AND-NOTE and stop.**

1. **Direct producing-motion strengthening.** Does this strengthen a current producing motion?
   - SW website builds (Signal Works pipeline)
   - CW PDF / deliverable generation
   - Lead-gen (Apollo, Hunter, cold, warm, lead magnets, follow-up sequences)
   - Content board (LinkedIn / X / newsletter / Boubacar voice motion)
   - Atlas autonomy infrastructure (heartbeats, publish loops, learning crews, VPS hardening)
   - Studio / channel cloner pipeline / video production
   - Other named producing motion (name it explicitly)
2. **Founder-time reduction.** Does this remove Boubacar from a process he currently does by hand, or reduce review/approval time on a recurring loop?
3. **Continuous improvement.** Does this measurably enhance one of the 74 existing skills?

Name the leverage type explicitly. It rides through every later phase.

## Phase 1: Detect, fetch, and check registry

### Detection table

| Pattern | Type | Fetcher |
| --- | --- | --- |
| `github.com/owner/repo` | repo | `git clone --depth 1 <url> sandbox/.tmp/absorb-<slug>/` |
| Repo with `mcp.json` or MCP-mentioning README | mcp-server (clone) | clone + parse manifest |
| Pip package `mcp-server-*` or marked MCP in PyPI | mcp-server (pip) | `pip show` metadata + PyPI README, no install |
| URL to hosted MCP endpoint (`/sse` or `/mcp` path) | mcp-server (remote) | introspect manifest endpoint |
| `*.json` URL or pasted JSON with `"nodes":` and `"connections":` | n8n-workflow | fetch + parse |
| `http(s)://...` ending in `.pdf` | pdf | Read tool with `pages:` |
| `http(s)://...` ending in `.md` / `.txt` | raw-doc | fetch |
| `http(s)://...` (live site) | live-site | Firecrawl scrape |
| Local path containing `SKILL.md` | skill | read in place |
| Local path to `.pdf` / `.md` / `.txt` | raw-doc | Read in place |
| Pasted text > 500 chars | raw-doc | use as-is |
| Else | unknown | ask once, bail |

### Slug rule

- GitHub: `<owner>-<repo>` (lowercase, hyphenate)
- Live URL: `<host>-<top-path>` (lowercase, strip protocol, replace `/` with `-`, truncate at 60 chars)
- Pasted text: `text-<sha1[:8]>`
- Local skill: skill folder name

### Registry check

Grep `docs/reviews/absorb-log.md` for the source URL or slug. If a prior verdict exists, surface it:

```text
Prior verdict found:
  Date: <date>
  Verdict: <verdict>
  Placement: <placement>
  Leverage: <leverage type>

Re-evaluate, or use prior verdict?
```

If the user picks prior, stop. Otherwise continue.

## Phase 2: Deep artifact analysis

Read everything that defines what the artifact is and what it does. No shortcuts.

**Repos:** README, all top-level docs, SKILL.md if present, manifests (package.json, pyproject.toml, requirements.txt, Cargo.toml, go.mod), every entrypoint file, directory tree, .env.example, dependency surface, license, last commit date, open issues count. Walk actual code paths. Flag red flags: abandonware (>12mo no commits), sketchy deps, unclear license, secrets in repo.

**MCP servers (any flavor):** above + transport (stdio / HTTP / SSE), tools exposed, auth method, manifest contents, install path (clone / pip / remote).

**n8n workflows:** trigger type, node count, credentials needed, external services touched, error-handling presence.

**Live URLs:** full Firecrawl crawl (not just landing), tech stack, what they sell/offer/explain, who runs it, contact surface, freshness signals.

**Raw docs / PDFs:** full read, extract claims, identify the concrete capability or pattern described.

**Skills:** read SKILL.md + every supporting file, understand the full workflow, map every tool/script/agent it invokes.

### Dossier template

```text
ARTIFACT DOSSIER : <name>
=========================
What it is: <one paragraph>
What it does:
- <bullet capability 1>
- <bullet capability 2>
How it works: <high-level mechanism>
Dependencies: <list>
Cost: <license / infra / complexity>
Risks: <list, or "none flagged">
Leverage type (from Phase 0): <producing-motion | founder-time-reduction | continuous-improvement>
```

## Phase 3: Placement proposal

Read `docs/SKILLS_INDEX.md` (live ground truth). Cross-reference with `skills/boubacar-skill-creator/patterns/skill-taxonomy.json` for clusters. **If they disagree, SKILLS_INDEX.md wins.**

Default toward extension, not new skill. Run all six checks in order; the first match decides:

1. **Continuous-improvement check (runs first).** Does this enhance any of the 74 existing skills' capability or quality? Yes, propose **enhance skills/X**. This is the dominant case.
2. **Near-duplicate check.** Skill with capability overlap (top 3 trigger phrases share intent OR description overlaps in core capability)? Propose **extend skills/X**.
3. **Cluster check.** Fits a recognized cluster (web-building, lead-gen, content, design, video, autonomy infra, etc.)? Propose extending the strongest skill in that cluster.
4. **Capability gap check.** Real gap none of the 74 skills cover, AND step 1 returned no? Propose **new skill skills/Y**.
5. **Below-skill check.** Just a tool/script that an existing skill should call? Propose **new tool**, lives in the consuming skill's directory.
6. **Satellite check.** Has its own URL, customer, or revenue stream per AGENTS.md? Propose **satellite repo**, referenced from agentsHQ but lives in its own GitHub repo.

Output: chosen placement + named runner-up + one-line reason for runner-up rejection.

## Phase 4: Sankofa and Karpathy on the proposal

Run both, in sequence, on the placement decision (not on the artifact's internals). Per `feedback_audits_before_implementation.md`.

### Sankofa Council on the placement

Invoke the local `sankofa` skill via the Skill tool with skill name `sankofa`. Pass this exact framing as the input:

> Council, stress-test this absorb proposal.
>
> Artifact: `<artifact name>`
> Proposed placement: `<placement decision from Phase 3>`
> Runner-up rejected: `<runner-up + reason>`
> Leverage type: `<Phase 0 leverage>`
> Producing motion or skill being strengthened: `<Phase 0 motion>`
>
> Apply the leverage-filter lens explicitly:
>
> - Contrarian: Will this actually reduce Boubacar's time, strengthen the named producing motion, or improve the named skill, or just feel like it does?
> - First Principles: What is the producing motion, founder-time leak, or skill weakness this strengthens? Name it.
> - Expansionist: What adjacent producing motion or auto-approval loop would this also strengthen that the proposal missed?
> - Outsider: If a stranger ran agentsHQ a year from now, would they thank us for absorbing this?
> - Executor: Name the integration date and the metric that proves the leverage materialized.

The Sankofa skill returns five voice sections + chairman synthesis. Capture the chairman verdict; it informs the final PROCEED / DON'T PROCEED call.

**v1 limitation acknowledged in the verdict footer:** Sankofa runs in the same model turn as the placement decision (in-IDE, single-LLM). v2 will route via the orchestrator for adversarial review. Add this disclaimer to the collapsed Sankofa details section: `(Sankofa: in-IDE single-LLM v1. v2: route via orchestrator for adversarial review.)`

### Karpathy audit on the placement

Invoke the local `karpathy` skill via the Skill tool with skill name `karpathy`. Pass this exact framing as the input:

> Karpathy, audit the integration plan for this absorb proposal.
>
> Artifact: `<artifact name>`
> Proposed placement: `<placement>`
> Integration plan: `<one paragraph: what files get touched, what changes, what ships>`
>
> Apply the four principles to the integration plan, not the artifact's internal code:
>
> 1. Think Before Coding: is the absorb intent stated and unambiguous?
> 2. Simplicity First: is the proposed integration the minimum that achieves the leverage?
> 3. Surgical Changes: does the integration touch only what must change?
> 4. Goal-Driven Execution: are there verifiable success criteria for the integration?

The Karpathy skill returns four principle verdicts (PASS/FAIL/WARN). A single FAIL = HOLD on the absorb verdict. WARN does not block but logs to the verdict.

## Phase 5: Verdict, log, and follow-up handoff

### Verdict types

- **PROCEED** = absorb. Phase 0 named at least one leverage type. Placement decided. Follow-up appended.
- **DON'T PROCEED** = harmful, redundant, or actively conflicts with agentsHQ. Logged with reason. No follow-up.
- **ARCHIVE-AND-NOTE** = interesting but no leverage type names today. Logged so we can grep it later. No follow-up.

### Output format (single chat message)

```text
ABSORB VERDICT : <artifact name>
================================
<PROCEED | DON'T PROCEED | ARCHIVE-AND-NOTE>

Leverage: <producing-motion | founder-time-reduction | continuous-improvement | none>
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

Below that, four collapsed `<details>` sections: **What it is** (Phase 2 dossier), **Sankofa Council** (five voices + chairman + the v1 disclaimer), **Karpathy audit** (four principle verdicts), **Placement reasoning** (why chosen home wins, why runner-up loses).

### Registry appends

**Always append to `docs/reviews/absorb-log.md`:**

```text
2026-05-02 | https://github.com/owner/repo | PROCEED | enhance skills/website-intelligence | producing-motion
```

**On PROCEED only, also append to `docs/reviews/absorb-followups.md`:**

```text
2026-05-02 | enhance skills/website-intelligence | producing-motion | wire <feature> into web-intel scraper | 2026-05-15
```

**Hard rule: PROCEED without a follow-up append is incomplete.** The skill must not finalize the verdict until next-action and target-date are written. If the agent cannot determine a next action, it asks Boubacar before logging.

## Placement options (defined)

- **enhance skills/X** = add a feature/capability to X without changing its core scope.
- **extend skills/X** = bigger surface change to X, may affect triggers or core flow.
- **new skill skills/Y** = creates a new SKILL.md folder. Reserved for capability gaps where no existing skill is a reasonable host.
- **new tool** = a script, helper, or reference doc that an existing skill calls. Lives in the consuming skill's directory (`skills/<skill>/scripts/foo.py` or `skills/<skill>/references/foo.md`).
- **new agent** = orchestrator-side CrewAI agent definition. Reserved for runtime autonomy capabilities, not Claude Code workflow capabilities.
- **satellite repo** = product with its own URL/customer/revenue. Lives in its own GitHub repo per AGENTS.md "Platform With Satellites" rule.

## Common mistakes

| Mistake | Fix |
| --- | --- |
| Skipping Phase 0 because "obviously useful" | Run the gate every time. The leverage type is required output. |
| Defaulting to "new skill" | Run Phase 3 step 1 (continuous-improvement) FIRST. New skill is the exception. |
| Sankofa output is vague | Pass the exact framing block above (with leverage type and motion filled in). |
| PROCEED logged without follow-up | Refuse to finalize. Ask Boubacar for next-action + target-date if unknown. |
| Bare URL triggered an install | Hard rule violated. Absorb is read-only. Install needs explicit phrasing. |
