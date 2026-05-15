---
name: agentshq-absorb
description: Use when evaluating any GitHub repo, live URL, MCP server, n8n workflow, PDF, raw doc, or local skill for inclusion in agentsHQ. Auto-fires on bare GitHub URLs (read-only analysis, never installs). Outputs PROCEED / DON'T PROCEED / ARCHIVE-AND-NOTE verdict with placement (enhance/extend/new skill/new tool/new agent/satellite) and leverage type (producing-motion/founder-time-reduction/continuous-improvement). Triggers on "absorb", "should we absorb", "evaluate this for agentshq", "is this worth adding", "review this repo for agentshq", "/agentshq-absorb", or a bare github.com URL with no other context.
---

# /agentshq-absorb

Codify Boubacar's manual workflow for evaluating any artifact (GitHub repo, live URL, MCP server, n8n workflow, PDF, raw doc, or local skill) against agentsHQ. Output: structured one-pager verdict + placement + leverage type + follow-up handoff. Default placement bias: enhance an existing skill, not build a new one.

## Self-Audit Mode

Run this when the user says "audit my config", "scan our own setup", "check agentsHQ for secrets", or at any Compass-scheduled monthly interval. Turns the Security Scan Gate inward against agentsHQ's own Claude Code configuration — not an external artifact being absorbed.

**Four checks. Run all four. Each is a grep, no external tools.**

### Check 1 — Hardcoded secrets in CLAUDE.md and handoff docs (v2-6)

Pattern: `(password|secret|token|api_key|private_key)\s*=\s*['"][^'"]{8,}['"]`

Grep targets:
- `CLAUDE.md`
- `docs/handoff/**/*.md`
- `docs/memory/**/*.md`
- `C:\Users\HUAWEI\.claude\projects\d--Ai-Sandbox-agentsHQ\memory\**/*.md`

Verdict: any match = BLOCKED (secrets committed). Fix: move value to `.env` or remove from doc.

### Check 2 — Shell-out patterns in hooks (v1-1)

Pattern: any of `curl`, `wget`, `fetch`, `sh -c`, `bash -c` inside hook scripts.

Grep targets:
- `~/.claude/hooks/**/*.js`
- `~/.claude/hooks/**/*.sh`
- `~/.claude/settings.json` (hook command fields)

Verdict: match = SUSPICIOUS. Hooks executing remote downloads = supply chain vector. Review intent; replace with local scripts.

### Check 3 — Overly-broad permissions in settings.json

Read `~/.claude/settings.json` and `d:\Ai_Sandbox\agentsHQ\.claude\settings.json`.

Flag if any `allow` permission entry uses `*` glob without path restriction, or grants `Bash` to a command with no argument constraints.

Verdict: match = WARN. Tighten to specific patterns.

### Check 4 — Known-bad MCP transport patterns

Read all `~/.claude/mcp*.json` or MCP entries in settings.json.

Flag if:
- Any MCP server uses `http://` (non-TLS) transport to a non-localhost endpoint
- Any MCP server entry has `env` fields containing raw API keys (not `$ENV_VAR` references)

Verdict: non-TLS external = SUSPICIOUS. Raw key in env = BLOCKED.

**Output format:**

```text
SELF-AUDIT RESULTS : agentsHQ config
=====================================
Check 1 (secrets in docs):    CLEAN | <file:line — matched value>
Check 2 (hook shell-outs):    CLEAN | <file:line — matched pattern>
Check 3 (broad permissions):  CLEAN | <entry — exact permission string>
Check 4 (MCP transport):      CLEAN | <server — issue>

Overall: CLEAN | FINDINGS PRESENT
Action required: <list fixes, or "none">
```

**Cadence:** monthly, governed by Compass M6. Also run any time a new hook, MCP server, or settings.json entry is added.

---

## Hard rule: bare URL = absorb, never install

A bare GitHub URL with no other context **always** triggers absorb. Never install. The shallow clone in Phase 1 lives in `sandbox/.tmp/absorb-<slug>/` and is read-only. Install only fires on explicit "install this repo / install <name> / add this to agentsHQ / wire this up" + URL, and is handled by other skills.

## Hard rule: security scan before any clone or install

Before any `git clone`, pip install, or execution of external code: run the **Security Scan Gate** (see below). No exceptions. BLOCKED = halt immediately, notify Boubacar. SUSPICIOUS = flag prominently, Boubacar decides. STATIC-CLEAN = continue.

This scan is a **shared primitive** - invoke it from any agentsHQ ingestion path (absorb, Dockerfiles, pip requirements, n8n workflow URLs, MCP installs), not only here.

### Security Scan Gate

Runs entirely via static analysis: Claude reads file tree and manifests and scripts. No external tools. No new dependencies.

**Step 1 - Fetch file tree and key files (read-only, no clone needed for this step):**

For GitHub repos: use the GitHub MCP or fetch raw file list via the GitHub API trees endpoint. Read these specific files if present:

- `package.json` (postinstall / preinstall / prepare scripts)
- `setup.py`, `setup.cfg`, `pyproject.toml` (entry_points, install_requires)
- Any `*.sh`, `Makefile`, `.github/workflows/*.yml`, `Dockerfile`
- `requirements.txt`, `go.mod`, `Cargo.toml`
- Top-level `.js`, `.py`, `.ts` entry points

**Step 2 - Apply v1 pattern checklist (two mandatory, rest v2):**

| Priority | Pattern | Signal |
| -------- | ------- | ------ |
| **v1-1** | `postinstall`, `preinstall`, or `prepare` script containing `curl`, `wget`, `fetch`, `sh`, `bash`, or shell invocation | Install-time shell-out - highest-risk supply chain vector |
| **v1-2** | `base64.*eval`, `atob(`, `Buffer.from.*base64`, or decode-then-run chains in any `.js`, `.py`, `.ts` file | Runtime decode-plus-run chain - obfuscated payload delivery |
| **v2-3** | Package name in `requirements.txt` or `package.json` that differs by exactly 1 character (insert/delete/substitute) from any name in the Popular Package Reference below | Typosquatting / dependency confusion |
| **v2-4** | Hardcoded IPv4 address (`\b\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}\b`) or non-localhost domain in a `requests.post`, `fetch(`, `http.request`, `axios.post`, or `urllib.request` call in any script | Exfil endpoint - data leaving the machine |
| **v2-5** | `os.environ`, `process.env`, or `System.getenv` read into a variable that is then passed to an HTTP call or written to a file at an external path | Credential/env var harvesting |
| **v2-6** | Hardcoded credential assignment matching the v2-6 regex (see below table) in any tracked file not covered by `.gitignore` | Secret committed to history |
| **v3-7** | Repo age < 30 days AND stargazer count ≥ 50 (see v3-7 procedure below) | Astroturfed trust signal - fabricated popularity used to lend legitimacy |

**v2-6 regex:** `(password|secret|token|api_key|private_key)\s*=\s*['"][^'"]{8,}['"]`
Apply against any `.py`, `.js`, `.ts`, `.env`, `.yml`, `.yaml`, `.json` file that is tracked (not in `.gitignore`).

**v3-7 procedure (GitHub repos only):**

Use the GitHub MCP `get_repository` tool (or fetch `https://api.github.com/repos/<owner>/<repo>`) and read:

- `created_at` - repo creation date
- `stargazers_count` - current star count
- `forks_count` - current fork count

Compute repo age in days from `created_at` to today.

Flag **SUSPICIOUS** if ALL of:

1. Age ≤ 30 days
2. Stars ≥ 50

Flag **SUSPICIOUS** (lower confidence) if:

1. Age ≤ 30 days AND forks ≥ 20 (fork spike without stars)

Note: stars alone are not suspicious (legitimate viral repos exist). The combination of very new + already popular is the signal. Always include the exact numbers in the flag: `created_at: <date> (<N> days old), stars: <N>, forks: <N>`.

---

**Popular Package Reference (typosquatting baseline - v2-3):**

Check each dependency name against this list using 1-char edit distance (Levenshtein). A match that is NOT on this list but is 1 edit away from one that is = SUSPICIOUS.

```text
Python (requirements.txt / pyproject.toml):
requests, numpy, pandas, flask, django, fastapi, sqlalchemy, boto3, pydantic,
pillow, scipy, matplotlib, tensorflow, torch, scikit-learn, celery, redis,
pytest, black, mypy, uvicorn, aiohttp, httpx, click, typer, rich, loguru,
cryptography, paramiko, fabric, invoke, ansible, setuptools, wheel, pip,
six, urllib3, certifi, charset-normalizer, idna, packaging, attrs, PyYAML

npm / package.json:
react, express, lodash, axios, moment, webpack, babel, eslint, prettier,
typescript, next, vue, angular, svelte, tailwindcss, vite, rollup, esbuild,
dotenv, chalk, commander, inquirer, jest, mocha, chai, sinon, nodemon,
socket.io, mongoose, sequelize, knex, pg, mysql2, redis, bull, winston,
cors, helmet, morgan, passport, jsonwebtoken, bcrypt, uuid, dayjs, zod,
openai, anthropic, langchain, cheerio, puppeteer, playwright
```

Flag: if a dependency name is within 1 edit of ANY item on this list AND is not itself on this list → **SUSPICIOUS** with note "possible typosquat of `<matched-name>`".

**Step 3 - Build security verdict block:**

```text
SECURITY SCAN : <repo-slug>
============================
Status: STATIC-CLEAN | SUSPICIOUS | BLOCKED
  (STATIC-CLEAN = no patterns matched. Runtime payloads not checked - dynamic execution is out of scope.)

Flags:
  - <file>:<line> - <exact matched pattern> - <threat description>
  (or "none" if STATIC-CLEAN)

Recommendation: PROCEED | PROCEED-WITH-CAUTION | HALT

Override (SUSPICIOUS only): [ ] Boubacar annotated: "<reason>" on <date>
  (BLOCKED is a hard stop - no override path)
```

**Verdict rules:**

- Any v1-1 or v1-2 match → **BLOCKED**. Halt. No clone. No install. Surface the exact file:line and matched pattern to Boubacar.
- Any v2-3, v2-4, v2-5, v2-6, or v3-7 match → **SUSPICIOUS**. Continue but prominently flag. Boubacar must annotate the Override field before absorb proceeds.
- No matches → **STATIC-CLEAN**. Disclaimer always shown: "Runtime payloads not checked."
- SUSPICIOUS with Override annotated → treated as PROCEED-WITH-CAUTION in the log.

**Where this gate fires in each ingestion path:**

| Path | When to run |
| ---- | ----------- |
| absorb (GitHub repo) | After detection, before Phase 0 leverage gate |
| absorb (MCP server clone) | Same - before clone |
| Any `orc_rebuild.sh` Dockerfile with external pip install or npm install | Before rebuild |
| n8n workflow with external URL fetch nodes | Before import |
| Any "install this" explicit command | Before install |

**Log the scan result** in the dossier under `SECURITY SCAN` section. Always. Even STATIC-CLEAN results are logged so the audit trail exists.

**Acceptance test fixtures:** `skills/agentshq-absorb/fixtures/security-scan/` - clean samples (must produce zero flags) and malicious samples (one per pattern, must trigger their labeled pattern). Use these to calibrate false-positive rate before flagging a real repo.

---

## Hard rule: read the README first, every time

Before any analysis, scoring, or placement work: read the README. No exceptions. The README defines what the artifact actually is. Many placement mistakes happen because this step is skipped and the agent infers from the repo name or description alone.

## Hard rule: tool vs skill detection (runs before Phase 0)

Before the leverage gate, classify the artifact:

**External tool / binary / CLI:** anything that installs as a standalone executable, CLI, plugin, or binary (e.g. rtk, caveman, context-mode, markitdown, ffmpeg, wsl-distro).

→ Route to **Tool Fit Check** (see below). Skip Phase 3 placement taxonomy entirely.

**Skill / workflow / pattern / knowledge artifact:** anything that adds capabilities to how Claude Code or agentsHQ operates (prompts, SKILL.md, agent definitions, n8n workflows, MCP servers, docs/patterns).

→ Continue to Phase 0 leverage gate, then Phase 3 placement taxonomy.

### Tool Fit Check (for external tools/binaries only)

Answer three questions. Output the answers directly. No placement taxonomy.

1. **Does it work on our stack?** (Windows 11 native + WSL2 Ubuntu + VPS Linux). Name which environment it works in and any limitations.
2. **Does it make our work measurably better?** (faster, cheaper, fewer manual steps, less context burn). Quantify if possible.
3. **Is there already something doing this?** Check installed tools + existing skills + MCP connections.

Then run **Sankofa and Karpathy**, but reframe the question for tools:

**Sankofa framing for tools:**
> Council, stress-test whether we should add this tool to agentsHQ's stack.
>
> Tool: `<name>`
> What it does: `<one line>`
> Stack fit: `<which environments it works in, any limitations>`
> Proposed verdict: `<INSTALL IT | SKIP IT | REVISIT WHEN>`
> Already on stack: `<what currently covers this need, if anything>`
>
> Apply the tool-bloat lens:
> - Contrarian: Does this actually solve a real pain, or does it just feel useful?
> - First Principles: What specific recurring cost or friction does this eliminate? Name it exactly.
> - Expansionist: What else on the stack does this interact with, positively or negatively?
> - Outsider: A year from now, is this tool still pulling its weight or has it become dead weight?
> - Executor: Name the install command, the environment, and the metric that proves it earned its place.

**Karpathy framing for tools:**
> Karpathy, audit whether adding this tool is the minimum change that solves the problem.
>
> Tool: `<name>`
> Problem it solves: `<one sentence>`
> Install plan: `<what gets added, where, what it touches>`
>
> 1. Think Before Coding: is the problem real and clearly stated?
> 2. Simplicity First: is this tool the minimum solution, or is there a simpler path?
> 3. Surgical Changes: does installing this touch only what must change?
> 4. Goal-Driven Execution: is there a verifiable metric that proves the tool earned its place?

Verdict: **INSTALL IT** / **SKIP IT** / **REVISIT WHEN** (name the condition).

If INSTALL IT: provide the exact install command(s) for the applicable environment. Log to absorb-log.md and absorb-followups.md. Done.

If SKIP IT or REVISIT WHEN: one sentence why. Log to absorb-log.md. Done.

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

## Phase 1.5: Batch + Cluster modes

When Boubacar sends more than one artifact in a single message, route as follows BEFORE Phase 2:

### Batch mode (parallel-independent items)

Trigger: 2+ URLs/repos/links pasted with no stated topical relationship.

Behavior: spawn N background subagents in a SINGLE response (`Agent` tool, `run_in_background: true`), one per artifact. Each subagent runs Phases 2-5 independently and returns its own verdict block. Main thread aggregates verdicts after all complete, optionally surfaces cross-cutting follow-ups.

Per concurrency rule: never serially spawn — one message, N parallel tool calls.

### Cluster mode (same-topic items)

Trigger: 2+ artifacts on the same subject (e.g. five different planning-skill repos, three articles on the same framework). Boubacar usually flags this explicitly ("these are all on X").

Behavior: ONE subagent holds all artifacts in context, returns a single synthesized verdict comparing them. Output: per-artifact mini-dossier + cross-artifact comparison table + ONE combined PROCEED / ARCHIVE-AND-NOTE for the cluster. Reject placeholder duplicates; if any artifact wholesale supersedes the others, declare it the cluster winner.

When ambiguous between batch and cluster: default cluster if artifacts share a noun in the user prompt; default batch otherwise.

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

SECURITY SCAN : <repo-slug>
============================
Status: STATIC-CLEAN | SUSPICIOUS | BLOCKED
  (STATIC-CLEAN = no patterns matched. Runtime payloads not checked - dynamic execution is out of scope.)
Flags:
  - <file>:<line> - <exact matched pattern> - <threat description>
  (or "none" if STATIC-CLEAN)
Recommendation: PROCEED | PROCEED-WITH-CAUTION | HALT
Override (SUSPICIOUS only): [ ] Boubacar annotated: "<reason>" on <date>
```

### Coverage check (runs after dossier, before Phase 3)

**Hard rule: grep our stack before any council work.**

Extract 2-3 core capability keywords from the dossier. Then grep all four:

1. `docs/AGENT_SOP.md`
2. `CLAUDE.md`
3. `docs/SKILLS_INDEX.md`
4. `skills/<closest-match>/SKILL.md`

If matches found that cover the artifact's core capability: **stop**. Surface the matching file + line number. Verdict is ARCHIVE-AND-NOTE immediately. Do not continue to Phase 3 or Phase 4.

If no coverage found: continue to Phase 3.

**Why this rule exists:** 2026-05-03: absorbed `forrestchang/andrej-karpathy-skills`, ran full Sankofa council, council argued persuasively to PROCEED. But AGENT_SOP.md line 65-70 already had all 4 Karpathy principles verbatim. Council was run on a duplicate. Full council review wasted on noise that a 10-second grep would have caught.

## Phase 3: Placement proposal

Read `docs/SKILLS_INDEX.md` (live ground truth). Cross-reference with `skills/boubacar-skill-creator/patterns/skill-taxonomy.json` for clusters. **If they disagree, SKILLS_INDEX.md wins.**

Default toward extension, not new skill. Run all six checks in order; the first match decides:

1. **Continuous-improvement check (runs first).** Does this enhance any of the 74 existing skills' capability or quality? Yes, propose **enhance skills/X**. This is the dominant case.
2. **Near-duplicate check.** Skill with capability overlap (top 3 trigger phrases share intent OR description overlaps in core capability)? Propose **extend skills/X**.
3. **Cluster check.** Fits a recognized cluster (web-building, lead-gen, content, design, video, autonomy infra, etc.)? Propose extending the strongest skill in that cluster.
4. **Capability gap check.** Real gap none of the 74 skills cover, AND step 1 returned no? Propose **new skill skills/Y**.
5. **Below-skill check.** Just a tool/script that an existing skill should call? Propose **new tool**, lives in the consuming skill's directory.
6. **Satellite check.** Has its own URL, customer, or revenue stream per AGENTS.md? Propose **satellite repo**, referenced from agentsHQ but lives in its own GitHub repo.
7. **Wholesale-better check.** Does the artifact materially outperform an existing skill on the SAME capability (better algorithm, better DX, better safety model, better cost), not just a feature add? Propose **replace existing skills/X**. Triggers mandatory Karpathy audit, mandatory Sankofa (no fast-path), and a documented migration plan in the verdict's "Placement reasoning" details (current skill stays in place until the replacement ships + passes a parity test).

Output: chosen placement + named runner-up + one-line reason for runner-up rejection.

## Phase 4: Sankofa and Karpathy on the proposal

Run both, in sequence, on the placement decision (not on the artifact's internals). Per `feedback_audits_before_implementation.md`.

### Council mandatory vs optional (threshold)

Sankofa + Karpathy are MANDATORY when the chosen placement is one of:

- `new skill skills/Y`
- `new agent`
- `satellite repo`
- `replace existing skills/X`

Council is OPTIONAL (fast-path PROCEED allowed) when placement is:

- `enhance skills/X` (additive, in-scope)
- `extend skills/X` (when surface change is small + reversible)
- `new tool` (single helper, single consumer)

If council is skipped, the verdict footer MUST state: `Fast-pathed. Justification: <one line>`. Skipping council on a mandatory-tier placement = incomplete verdict.

### Premortem mode toggle

Trigger: Boubacar appends `--premortem` to the invocation, OR the placement is `new agent` / `satellite repo` / `replace existing`, OR the artifact touches send-email / push-to-main / VPS deploy / billing surfaces.

When triggered, invoke Sankofa via the `council` skill with `premortem this` appended to the framing. Council retroactively imagines the absorb failed 6 months from now and works backward to the cause. Capture the top-3 failure modes + a tripwire metric per mode. Append them to the verdict's "Placement reasoning" details. Failing to attach tripwires on a premortem-triggered absorb = incomplete verdict.

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

Placement: <enhance skills/X | extend skills/X | new skill skills/Y | new tool | new agent | satellite repo | replace existing skills/X | archive>
Runner-up: <other option>. Rejected because <one line>.

Next action: <one specific concrete next step>
Target date: <YYYY-MM-DD on PROCEED; "n/a" on ARCHIVE-AND-NOTE or DON'T PROCEED>
```

**Target date rule:** On PROCEED, a real YYYY-MM-DD target date is required (matches the follow-up entry). On ARCHIVE-AND-NOTE or DON'T PROCEED, the field still appears with value `n/a` to keep the verdict block schema-stable for the verification harness.

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
- **replace existing skills/X** = artifact wholesale outperforms an existing skill on the same capability. Build the replacement in a separate path (e.g. `skills/X-v2/`), keep `skills/X/` live until the replacement passes a documented parity test, then atomic-swap and archive the old one to `zzzArchive/skills/X-<date>/`. Mandatory: Karpathy audit + Sankofa premortem + migration plan in the verdict.

## Common mistakes

| Mistake | Fix |
| --- | --- |
| Skipping Phase 0 because "obviously useful" | Run the gate every time. The leverage type is required output. |
| Defaulting to "new skill" | Run Phase 3 step 1 (continuous-improvement) FIRST. New skill is the exception. |
| Sankofa output is vague | Pass the exact framing block above (with leverage type and motion filled in). |
| PROCEED logged without follow-up | Refuse to finalize. Ask Boubacar for next-action + target-date if unknown. |
| Bare URL triggered an install | Hard rule violated. Absorb is read-only. Install needs explicit phrasing. |
| Capability looks "missing" but is already wired via an existing MCP | In Phase 2, also check MCP connections + descriptions of all 75 skills. Example: `firecrawl-mcp-server` looked like a PROCEED candidate but was ARCHIVE-AND-NOTE because Firecrawl MCP is already used by skills/website-intelligence. Verdict: ARCHIVE-AND-NOTE = correct; accept it. |
| Sankofa shifts the placement mid-review | Accept the shift. Write the original proposal in "Placement reasoning" details, then the revised placement in the verdict. Example: markitdown started as "enhance skills/agentshq-absorb"; Sankofa First Principles correctly downgraded to "shared helper" because binding a general utility to one consumer was suboptimal. |
| target_date forgotten on ARCHIVE-AND-NOTE / DON'T PROCEED | Field is still required for harness compatibility. Use literal `n/a`. PROCEED requires real YYYY-MM-DD. |
| Running full Sankofa + Karpathy on obvious infrastructure install | Phase 0 passes + install = one CLI command → fast-path PROCEED + install commands. Skip taxonomy debate. Example: context-mode was a `/plugin install`; full council review wasted more tokens than the install. Reserve Sankofa/Karpathy for genuinely ambiguous placements only. |
| Running skill placement taxonomy on an external tool | Tools (CLIs, binaries, plugins) go through Tool Fit Check + Sankofa/Karpathy with tool-bloat framing, not Phase 3. "Where does this live in our skills?" is the wrong question for rtk, ffmpeg, or caveman. The right question is "does it work on our stack, make our work better, and earn its place?" |
| Skipping the README | README defines what the artifact is. Skipping it causes misclassification. Read it before any analysis, every time. |
| Running council before checking our own stack | Grep AGENT_SOP.md + CLAUDE.md + SKILLS_INDEX.md for core capability keywords BEFORE Phase 3 or Phase 4. If coverage exists, ARCHIVE-AND-NOTE immediately. Council is for genuinely ambiguous placements, not rubber-stamping duplicates. Example: forrestchang/andrej-karpathy-skills: full Sankofa council run; AGENT_SOP.md line 65-70 already had all 4 principles verbatim. |
| Skipping security scan because "I trust this repo" | Hard rule - scan runs on every external artifact before clone/install. Trust is not a bypass. STATIC-CLEAN is a 30-second check; skipping it is how supply chain injections land. |
| Reporting STATIC-CLEAN as "safe" | Always show the disclaimer: "Runtime payloads not checked." STATIC-CLEAN means no obvious static patterns found, not that the code is trustworthy. |
| SUSPICIOUS verdict with no pattern attribution | Every SUSPICIOUS or BLOCKED verdict must show exact `file:line - matched pattern`. Opaque status labels create friction without protection. |
| Bypassing BLOCKED via workaround | BLOCKED is a hard stop. No clone. No install. No override path. Surface the finding to Boubacar and stop. |
| Executing implausible numbers without checking | Any numeric input that looks like a typo (498 hours, 4800 lines, $9999) — push back and confirm before executing. Example: "498 hours" was meant to be "48 hours". Rule: if a number is >10x the reasonable range for the request, ask once before acting. |
| Proposing wiring for a framework the orchestrator doesn't use | Before writing any "wire X into the coding agent" follow-up, grep orchestrator/ for the framework. If zero matches, the task is GATED (pre-condition: framework must first be adopted). Example: TradingAgents absorb proposed LangGraph checkpoint wiring; `grep -r "langgraph" orchestrator/` returned zero — orchestrator is 100% CrewAI. Correct outcome: ARCHIVE-AND-NOTE + GATED atlas task. |
