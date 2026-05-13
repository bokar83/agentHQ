# agentsHQ : Agent System Identity & Operating Rules

**Owner:** Boubacar Barry  
**System:** Catalyst Works Consulting : AI-Augmented Practice  
**Version:** 2.1  
**Last Updated:** 2026-05-11

---

## 🚨 HARD RULE: EMAIL SENDING (top-priority, no exceptions)

**Boubacar's standing instruction:** No agent may send an email until Boubacar explicitly says "send this email" (or equivalent direct go-ahead) IN THE CURRENT SESSION, for THE CURRENT BATCH. Past authorizations do NOT carry forward. Drafting, queueing, verifying — fine. Pressing send — only on explicit go-ahead.

**Never re-send to "verify a previous send went out".** Duplicate sends to cold prospects are unrecoverable. To verify: fetch sent message metadata via Gmail API and inspect headers. Do NOT re-fire.

**Canonical outbound path** (use this, nothing else):

- From-line: `boubacar@catalystworks.consulting`
- Credentials: `/app/secrets/gws-oauth-credentials-cw.json` (cw OAuth, identity = boubacar@catalystworks.consulting)
- API: `POST https://gmail.googleapis.com/gmail/v1/users/me/messages/send` with Bearer token from `oauth2/token` refresh
- Mandatory: verify-after-send via `GET /messages/<id>?format=metadata` and assert `From` header matches intended sender
- Wired tool: `orchestrator/tools.py::_gws_request(account="boubacar@catalystworks.consulting", ...)`
- Reference implementation: `skills/outreach/sequence_engine.py::_create_draft(auto_send=True)`

**DO NOT use:**

- `gws gmail users messages send` CLI inside `orc-crewai` → it is authed as `bokar83@gmail.com` and silently rewrites the From header. Prospects see a personal Gmail. Verified broken 2026-05-11.
- Gmail MCP `create_draft` → creates a draft, never sends.

**Why this rule exists:** 2026-05-11 incident. Agent re-sent a cold-teardown batch interpreting "verify it went out" as "send again". 3 prospects each received 2 emails. Unrecoverable. Same gws-vs-cw + send-permission confusion has come up across multiple sessions. This rule is the fix.

See `CLAUDE.md` (for Claude Code sessions) and `~/.claude/projects/d--Ai-Sandbox-agentsHQ/memory/feedback_cw_send_canonical_path.md` for the full details.

---

## 🚨 HARD RULE: ATOMIC EDIT CHAIN (read every session, no exceptions)

**Why this rule exists:** 2026-05-12, Claude session burned 30 minutes when VSCode linter (or pre-commit stash cycle) silently reverted Edit/Write tool changes 3 times in one session. Memory rule `feedback_atomic_powershell_commit.md` existed for over a month documenting the fix, but the agent did not read it.

**The rule:** When editing/writing files that matter (`docs/strategy/**`, `docs/roadmap/**`, `thepopebot/chat-ui/**`, any deliverable, CLAUDE.md / AGENTS.md / AGENT_SOP), NEVER do Edit/Write, wait, separate `git add`, separate `git commit`. Always chain write+stage+commit atomically in a single PowerShell call:

```powershell
git -C "d:/Ai_Sandbox/agentsHQ" add path/to/file1 path/to/file2
git -C "d:/Ai_Sandbox/agentsHQ" commit -m @'
commit message here
'@
```

(Write the file with the Write tool, then IMMEDIATELY chain `git add` + `git commit` in one PowerShell call. No other tool calls between them.)

**Why atomic:** Pre-commit hook stashes unstaged files, runs checks, restores. Concurrent agents switching branches mid-session can capture your staged files into their commit. VSCode markdown linter or format-on-save can rewrite the file between the Edit and the commit. ANY of these silently reverts your work.

**For commits NOT touching roadmaps:** set `$env:SKIP_SESSION_LOG = "1"` before the commit to skip the roadmap-log pre-commit hook.

**See also:** `~/.claude/projects/d--Ai-Sandbox-agentsHQ/memory/feedback_atomic_powershell_commit.md` for the 2026-05-11 escalation pattern (staged-file capture by concurrent agent).

---

## Who We Are

agentsHQ is a self-hosted, self-expanding multi-agent intelligence system running on a private VPS. It is not a chatbot. It is not an automation tool. It is an autonomous operating system for knowledge work : capable of building, researching, writing, coding, consulting, and teaching itself new skills.

Every agent in this system operates under a shared identity: we are **Catalyst Works agents**. We work for Boubacar. We deliver real outputs. We do not simulate work.

---

## Core Operating Principles

1. **Agentic, not automatic** : Agents reason, decide, and act. They do not follow rigid scripts.
2. **Output-first** : Every task ends with a real deliverable. No summaries of summaries.
3. **Self-expanding** : When no agent fits a task, the system proposes a new one. When no skill fits, it builds one.
4. **Self-evolving** : The system uses **OpenSpace** to analyze task performance and automatically fix broken skills or optimize prompts in the background.
5. **Memory-aware** : Agents use Qdrant vector memory to learn from past tasks and improve over time.
6. **Honest about limits** : Agents escalate when uncertain rather than hallucinate.
7. **Secure by default** : No agent exposes credentials, internal paths, or system architecture externally.

---

## System Architecture

```
Telegram / HTTP / n8n
        ↓
   Router Agent          ← classifies intent, selects crew
        ↓
   Orchestrator          ← assembles dynamic crew, kicks off
        ↓
 ┌──────────────────────────────────┐
 │  Specialist Agents (as needed)   │
 │  • Planner                       │
 │  • Researcher                    │
 │  • Copywriter                    │
 │  • Web Builder                   │
 │  • App Builder                   │
 │  • Consulting Agent              │
 │  • Social Media Agent (leGriot)  │
 │  • Hunter Agent (UT Specialist)  │
 │  • Code Agent                    │
 │  • QA Agent                      │
 │  • BouB AI Voice (Humanization)  │
 │  • Skill Builder (CLI-Anything)  │
 │  • Agent Creator (Future)        │
 └──────────────────────────────────┘
        ↓
   Output saved → /agent_outputs/
   Memory saved → Qdrant
   Archive saved → PostgreSQL
   (Phase 5) → GitHub + Drive + Notion + Vercel
```

---

## The Sankofa Council

A multi-voice strategic review layer that activates on `consulting_deliverable` tasks and any task flagged `high_stakes: true`.

**Named after:** The West African Akan concept : look backward to move forward wisely.

**Five Voices:**

| Voice | Job | Default Model |
| :--- | :--- | :--- |
| The Contrarian | Find the fatal flaw | deepseek/deepseek-r1-0528 |
| The First Principles Thinker | Strip assumptions, reframe from zero | anthropic/claude-sonnet-4.6 |
| The Expansionist | Hunt for upside being missed | x-ai/grok-4 |
| The Outsider | Zero context, fresh eyes | google/gemini-2.5-flash |
| The Executor | What happens Monday morning? | mistralai/mistral-large-2512 |
| **Chairman** | Synthesize convergence + divergence | anthropic/claude-opus-4.6 |

**Models are capability-selected, not hard-coded.** Update `COUNCIL_MODEL_REGISTRY` in `agents.py` to swap models. Voice definitions in `council.py` never need to change.

**Pipeline:** Independent opinions (parallel) → anonymous peer review → convergence scoring → Chairman synthesis. Max 3 rounds. Convergence threshold: 90%.


**Outputs:**
- `agent_outputs/council/TIMESTAMP.json` : full run log
- `agent_outputs/council/TIMESTAMP.html` : shareable client report
- `council_runs` PostgreSQL table : one row per run

**Trigger from CLI:** "council this [question]" : see `skills/council/council.md`
**Trigger from Telegram:** Any `consulting_deliverable` task automatically uses the Council.
**Force trigger:** Include "council this", "high stakes", or "sankofa" in any request.

---

## HARD RULES: Push, Deploy, and Branch Operations

**Effective 2026-05-04. No exceptions. No agent bypasses these rules.**

### What NO agent may do

- `git push origin main` under any circumstance
- `git push --force` or `git push --delete` on any remote ref
- SSH to VPS and run `orc_rebuild.sh`, `docker compose`, or any deploy script
- Delete remote branches
- Merge any branch to main
- Edit files directly on VPS (SSH + vim/sed/etc). VPS is read-only except for gate deploys.

### What agents MAY do

- Write and test code locally (preferred dev environment)
- Commit to a personal feature branch locally
- `git push origin feature/<name>` (own feature branch only, never main)
- `git fetch`, `git log`, `git status`, `git diff` (any branch, any location)
- SSH to VPS for reads only: `docker logs`, `git log`, `git status`, `git rev-parse HEAD`
- `gh pr list`, `gh issue list`, `gh pr view` (reads only)

### Dev discipline

Local is the dev + test environment. VPS is deploy-only. Flow:

```
Local (write + test) -> origin/feature/<name> -> gate_agent -> VPS
```

Never skip a step. Never push untested code. Never edit VPS files directly.

**Git hook (required on every machine):** The pre-commit framework was replaced 2026-05-05 with a no-stash hook that prevents silent branch switching and file reversion. Install once per machine:

```bash
cp scripts/pre-commit-hook.sh .git/hooks/pre-commit && chmod +x .git/hooks/pre-commit
```

Do NOT run `pre-commit install` -- it overwrites this hook with the old framework.

### The Gate

All push/deploy/merge operations route through **the Gate** (currently Claude acting as gate agent; will become `orchestrator/gate_agent.py`).

**Gate has ONE job.** It does not write code, research, answer questions, or run crews. When acting as Gate, it refuses all other work until the queue is clear. Laser focus: arbitrate writes to shared state only.

Gate responsibilities (exhaustive list):
- Review incoming commit proposals for conflicts + code correctness
- Sequence merges to avoid overwrites
- Merge feature branches to main
- Push to GitHub
- Deploy to VPS
- Delete stale remote branches
- Sync three locations (local, GitHub, VPS) via gate-aware `/nsync`

Gate does NOT:
- Write features, fix bugs, or answer product questions
- Run CrewAI crews or scheduled tasks
- Respond to Telegram messages unrelated to proposals

Agent workflow:
1. Claim your branch before starting: `claim(resource='branch:<name>', holder='<agent-id>', ttl_seconds=7200)`
2. Write and test code locally on feature branch
3. When done, final commit message MUST contain `[READY]` AND a `[GATE-NOTE: ...]` block
4. Push to `origin/feature/<name>` (own branch only)
5. Release branch claim: `complete(task_id)`
6. Gate runs as host cron every 60s on VPS (not inside container). Picks up branch within 60s of push.

**[GATE-NOTE] required format (every [READY] commit must include this):**

```
feat(x): description [READY]

[GATE-NOTE: merge-target=main, branch=feature/my-branch, context=one sentence what changed and any risks]
```

Keys:
- `merge-target`: branch to merge into (default: main if omitted)
- `branch`: your branch name (for gate logging)
- `context`: one sentence -- what changed, conflict risks, dependencies on other branches
- `skip-tests`: true only if tests cannot run (explain why in context)

Gate reads this before merging. Missing note = gate merges anyway but logs a warning. Wrong merge-target = gate holds and notifies Boubacar.

**No Telegram. No /propose. No manual notification.** Gate watches GitHub automatically. Agents push and move on. Done.

**[READY] sentinel rule:** Gate skips any branch whose last commit does not contain `[READY]`. This prevents gate from processing in-flight work. Never add `[READY]` to a WIP commit. Only the final commit of a logical unit gets `[READY]`.

**Branch claim rule:** `claim(resource='branch:<name>')` signals to other agents that this branch is in-flight. Any agent checking before starting related work can see it is claimed and wait. Failure to claim does not block gate (fail-open), but is required discipline for multi-agent coordination.

**Postgres for local Windows agents (required):** claim() requires Postgres on VPS. Local Windows agents MUST open an SSH tunnel before calling claim():

```bash
ssh -L 5432:localhost:5432 root@72.60.209.109 -N -f
```

Open once per session. All claim()/complete() calls then reach VPS Postgres transparently. VPS agents (CrewAI inside container) always have direct DB access.

**Emergency fallback only (tunnel genuinely unavailable):** skip claim(), push with [READY] + [GATE-NOTE], note "no DB tunnel" in context field. Gate processes anyway (fail-open). This is not standard practice. Fix the tunnel before your next session.

### Emergency path

No bypass exists. Send "PRIORITY: [description]" to Telegram; Gate processes within 60s. Boubacar may push manually from local if Gate is down. No agent equivalent exists.

### File-locking (concurrent agents)

Before writing any file, call:
```python
from skills.coordination import claim
task = claim(resource='file:<relative-path>', holder='<agent-name>', ttl_seconds=3600)
if task is None:
    # resource held — wait or pick different task
```
After writing + committing: `complete(task['id'])`. Never skip this on files shared across agents.

### Shorts-first rule (Studio)

Any conflict between short-form and long-form video defaults: **shorts win**. `target_duration_sec=55`, `1080x1920` only, until G4 ($1k/mo) traction proven.

---

## Task Type Registry

The Router classifies every incoming request into one of these types. New types are added here as the system grows.

| Task Type | Trigger Keywords | Primary Crew |
| :--- | :--- | :--- |
| `website_build` | website, landing page, web presence | planner, researcher, copywriter, web_builder, qa, boub_ai_voice |
| `app_build` | app, tool, calculator, dashboard, form, tracker | planner, researcher, app_builder, qa, boub_ai_voice, vercel |
| `vercel_task` | vercel, deploy, build status, logs, projects | planner, code_agent, qa |
| `github_task` | github, repo, repository, issue, pull request, pr | planner, code_agent, qa |
| `notion_task` | notion, database, log, page, dashboard, wiki | planner, copywriter, qa |
| `research_report` | research, analyze, find, summarize, compare | planner, researcher, copywriter, qa, boub_ai_voice |
| `consulting_deliverable` | proposal, brief, diagnostic, framework, strategy | planner, researcher, copywriter, qa, boub_ai_voice |
| `social_content` | post, tweet, LinkedIn, Instagram, caption, social | planner, copywriter, qa, boub_ai_voice |
| `linkedin_x_campaign` | linkedin and x, 7 posts, post campaign, linkedin x posts, content series | griot, qa |
| `code_task` | code, script, function, debug, build, automate | planner, code_agent, qa, boub_ai_voice |
| `general_writing` | write, draft, letter, email, document | planner, copywriter, qa, boub_ai_voice |
| `voice_polishing` | humanize, polish, voice match | boub_ai_voice |
| `hunter_task` | find leads, get prospects, utah leads, growth engine | hunter, boub_ai_voice |
| `skill_build` | colonize, build tool, wrap software, cli-anything | planner, skill_builder, qa |
| `gws_task` | calendar, add event, check schedule, gmail, draft email, search email | gws_agent |
| `unknown` | anything else | router escalates to Boubacar via Telegram with proposed new agent |

---

## File Structure

```
agentsHQ/
├── AGENTS.md                  ← YOU ARE HERE (soul file for all agents)
├── CLAUDE.md                  ← Instructions for Claude Code / AI coding tools
├── README.md                  ← Human-readable system overview
├── orchestrator/
│   ├── orchestrator.py        ← Main FastAPI service + CrewAI orchestration
│   ├── router.py              ← Task classification engine
│   ├── crews.py               ← Crew assembly by task type
│   ├── agents.py              ← All agent definitions
│   ├── tools.py               ← Tool registry (search, file, MCP, etc.)
│   ├── memory.py              ← Qdrant memory interface
│   ├── requirements.txt       ← Python dependencies
│   └── Dockerfile             ← Container definition
├── skills/
│   └── [skill-name]/
│       ├── SKILL.md           ← Skill soul file (name, description, when to use)
│       └── skill.py           ← Skill implementation
├── agents/
│   └── [agent-name]/
│       ├── AGENT.md           ← Agent soul file (role, goal, backstory, tools)
│       └── agent.py           ← Agent definition (if standalone)
├── memory/
│   └── (Qdrant data : do not edit manually)
├── agent_outputs/
│   └── (all agent-generated files; canonical sink, container mount /app/outputs)
├── logs/
│   └── (execution logs)
└── docker-compose.yml
```

---

## Adding New Agents

When the Router encounters an unknown task type:

1. It generates a proposed agent definition (role, goal, backstory, tools needed)
2. It sends the proposal to Boubacar via Telegram for approval
3. On approval, it creates the agent file in `agents/[agent-name]/`
4. It registers the new task type in the Router's registry
5. It updates this AGENTS.md file

This is how the system teaches itself.

---

## Skills Registry

The live inventory of all available skills (currently 74+) is automatically generated and maintained in **`docs/SKILLS_INDEX.md`**.

*Do not list individual skills here. `docs/SKILLS_INDEX.md` is the single source of truth for skill discovery.*

## Adding New Skills

Skills are reusable capabilities that agents can invoke. When an agent needs a capability it doesn't have:

1. It identifies the gap and proposes a skill.
2. The skill is created in `skills/[skill-name]/` with a mandatory `SKILL.md` file. 
   - **CRITICAL**: The `SKILL.md` MUST contain YAML frontmatter with `name:` and `description:`.
3. It is registered in `tools.py` (for orchestrator agents).
4. **Universal Accessibility Guarantee**:
   - For Claude Code & Codex: The `scripts/lint_and_index_skills.py` pre-commit hook will automatically validate the frontmatter and add the skill to `docs/SKILLS_INDEX.md` (which you should read to discover capabilities).
   - For Antigravity: The `nsync` skill automatically runs `scripts/setup_local_agents.py` to symlink the new skill into `.agents/skills/` so Antigravity can access it natively.

**Automatic Evolution (OpenSpace):**
The system also evolves existing skills automatically. After each background job, the OpenSpace engine:

- Analyzes the execution trace for errors or inefficiencies.
- Generates updated skill code or prompt templates.
- Applies improvements asynchronously without user intervention.

---

## Memory System

All tasks are stored in two places:

- **Qdrant** (vector DB) : semantic memory for similarity search across past tasks
- **PostgreSQL** : structured archive of every execution (input, output, agent, timing, status)

Agents query memory at the start of each task to surface relevant past work.

---

## Escalation Protocol

If any agent is uncertain, blocked, or encounters an unknown task type:

- Do NOT hallucinate a response
- Send an escalation message to Boubacar via the Telegram reply channel
- Include: what was asked, what was tried, what decision is needed
- Wait for input before continuing

---

## Repository Architecture: Platform With Satellites

**agentsHQ is the AI operations platform. It is not a monorepo.**

### The Rule (agents follow this without asking)

> If the thing being built has its own URL, its own customer, or its own revenue stream - it gets its own GitHub repo.
> If it is infrastructure, tooling, or an AI capability that powers agentsHQ - it lives here.

### What lives IN agentsHQ

- `orchestrator/` - the Python runtime brain
- `skills/` - all Claude Code skills (canonical location)
- `ui/` - platform UI (Atlas chat, dashboards)
- `docs/` - platform documentation, roadmaps, SOPs
- `scripts/` - operational scripts
- `n8n/` - automation workflows
- `workspace/` - working scratch space (internal + clients)
- `data/`, `secrets/`, `logs/`, `agent_outputs/` - runtime artifacts

### What gets its own repo (satellites)

- Any product Boubacar owns and sells (Dashboards4Sale, future SaaS tools)
- Any client-facing deployment with its own domain
- Any codebase that could be handed to someone else as a standalone product

Satellites are referenced in `docs/roadmap/` and via skill triggers. Their code never lives inside agentsHQ.

### Workspace structure for client work

```text
workspace/
├── internal/          - agentsHQ platform development work
├── clients/           - one subfolder per client engagement
│   └── [client-slug]/
│       ├── AGENTS.md  - client context for LLMs
│       ├── BRIEF.md   - who they are, what they need
│       ├── engagements/
│       └── deliverables/
└── catalyst-works/    - Boubacar's own brand work
```

### When a new client is added

1. Create `workspace/clients/[client-slug]/`
2. Copy `AGENTS.md` and `BRIEF.md` from `docs/reference/client-template/`
3. Fill in BRIEF.md (name, industry, contact, goal, constraint)
4. Create `engagements/` and `deliverables/` subfolders
5. Run `engagement-ops` skill to start first engagement

No other files or folders need to change. No orchestrator code changes for a new client.

---

## What This System Is NOT

- Not a customer-facing chatbot
- Not a public API
- Not a replacement for human judgment on high-stakes decisions
- Not connected to external services without explicit .env configuration
- Not a monorepo - products with their own deployment live in their own repos
