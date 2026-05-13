# agentsHQ: Claude Code SOP

**Read `docs/AGENT_SOP.md` first, every session. No exceptions.** Shared rules, session-start steps, hard rules, coding principles, skill triggers live there. File = Claude-Code-specific additions only.

---

## 🚨 HARD RULE: EMAIL SENDING (read every session, no exceptions)

**Boubacar's standing instruction (2026-05-11):** You may NEVER send an email until Boubacar explicitly says "send this email" (or equivalent: "ship it", "go ahead and send", "fire it"). Drafting, queueing, building the script, verifying the From-line — all allowed. Pressing send — only after explicit go-ahead, IN THIS SESSION, for THIS specific email batch. Approval for one batch does NOT carry to the next.

**If a prior agent or memory says "send", but the current session's user has not said it, you do NOT send.** Memories of past authorizations expire at the session boundary.

**If a send fails or doesn't appear to land:** DEBUG by reading the API response, fetching the sent message metadata, checking server-side logs. Do NOT re-send to "verify it went out". A duplicate-send to a cold prospect is unrecoverable and damages the relationship.

**Channel-specific send rules:**

| Outbound | From-line | Path | Why |
|---|---|---|---|
| Cold outreach (Catalyst Works + Signal Works) | `boubacar@catalystworks.consulting` | cw OAuth + direct Gmail API (see below) | OAuth identity matches From, no rewrite |
| Internal/notifications to Boubacar | `boubacar@catalystworks.consulting` | Same | Already wired in `tools.py` |
| Signal Works inbound replies | (sender writes to) `signal@catalystworks.consulting` | alias routes to boubacar@ inbox | optics on SW website |

**The canonical send path (use this, nothing else):**

```python
# Inside orc-crewai container, OR via SSH+docker exec
import json, base64, httpx
from email.mime.text import MIMEText

with open("/app/secrets/gws-oauth-credentials-cw.json") as f:
    c = json.load(f)
token = httpx.post("https://oauth2.googleapis.com/token", data={
    "client_id": c["client_id"], "client_secret": c["client_secret"],
    "refresh_token": c["refresh_token"], "grant_type": "refresh_token",
}, timeout=15).json()["access_token"]

msg = MIMEText(body, "plain", "utf-8")
msg["From"] = "boubacar@catalystworks.consulting"   # Honored. OAuth identity matches.
msg["To"] = to_addr
msg["Subject"] = subject
raw = base64.urlsafe_b64encode(msg.as_bytes()).decode("ascii").rstrip("=")

resp = httpx.post(
    "https://gmail.googleapis.com/gmail/v1/users/me/messages/send",
    headers={"Authorization": f"Bearer {token}"},
    json={"raw": raw}, timeout=30,
)
msg_id = resp.json()["id"]

# MANDATORY verify-after-send. labelIds:[SENT] alone is NOT proof.
v = httpx.get(
    f"https://gmail.googleapis.com/gmail/v1/users/me/messages/{msg_id}",
    headers={"Authorization": f"Bearer {token}"},
    params={"format": "metadata"}, timeout=20,
).json()
from_hdr = next(h["value"] for h in v["payload"]["headers"] if h["name"].lower() == "from")
assert from_hdr.endswith("boubacar@catalystworks.consulting"), f"From rewritten: {from_hdr}"
```

**DO NOT use:**
- `gws gmail users messages send` CLI from `orc-crewai` (authed as bokar83@gmail.com → silently rewrites From to bokar83, prospects see personal Gmail). Verified broken 2026-05-11.
- Gmail MCP `create_draft` and calling it done (creates a draft, never sends).
- Any path that lacks a verify-after-send step.

**Wired Python tools that already do this correctly:**
- `orchestrator/tools.py::_gws_request(account="boubacar@catalystworks.consulting", ...)` — POST to `gmail/v1/users/me/messages/send`
- `signal_works/gmail_draft.py` — draft variant of the same pattern
- `skills/outreach/sequence_engine.py::_create_draft(..., auto_send=True)` — production send path used by SW T1-T5 outreach

**Why this rule exists:** 2026-05-11 incident. Agent sent batch 1 of cold-teardown outreach without final explicit go-ahead the second time (interpreted "verify it went out" as "re-send to verify"). Result: 3 prospects each received 2 emails with mismatched From-lines. Unrecoverable. Boubacar had to write this rule because the same gws-vs-cw + send-permission question keeps reappearing across sessions.

See: `~/.claude/projects/d--Ai-Sandbox-agentsHQ/memory/feedback_cw_send_canonical_path.md` for the full context.

---

## Active Roadmaps

Multi-session projects tracked in `docs/roadmap/<codename>.md`. `roadmap` skill manages them (list / show / next / log / new / archive). Read at session start, log at session end.

| Codename | One-line |
|---|---|
| `atlas` | agentsHQ true agentic work (autonomy layer) |
| `compass` | governance model: rules live, enforce, retire, anti-sprawl |
| `echo` | async substrate: agent proposes commits, human acks asynchronously |
| `harvest` | Catalyst Works revenue pipeline (stub) |
| `studio` | faceless agency: branded channels as adjacent revenue to CW |

Full registry: `docs/roadmap/README.md`.

## Audit Registry (2026-05-11)

Before starting any `/audit`, `/rca`, "find bugs", or adversarial code review:

1. Read `docs/audits/REGISTRY.md` — chronological ledger of audits run, what shipped, what was skipped + why, what's still deferred
2. Read `docs/decisions/INTENTIONAL.md` — greppable index of patterns that look like bugs but are deliberate design
3. Memory rule: `feedback_audit_read_handoffs_first.md` — read handoffs + routing-architecture.md before flagging severity

Every audit MUST add an entry to `docs/audits/REGISTRY.md` as part of close-out. Incomplete audit otherwise.

## Claude-Code-Only

**Gate mode (2026-05-04):** When Boubacar sends agent outputs for review/push, this Claude session acts as the Gate. Gate has ONE job: arbitrate writes to shared state (GitHub, VPS, main). Refuse all other work until queue is clear. See AGENTS.md Gate section for full rules.

**No push/deploy without gate review.** Never `git push`, `ssh ... orc_rebuild.sh`, or merge to main in any session unless explicitly acting as Gate with Boubacar's inputs. Other Claude sessions = coding agents only.

**Container deploys (2026-05-05): NO REBUILD for code changes.** Code dirs are volume-mounted in `docker-compose.yml`. Deploy = `ssh root@72.60.209.109 "cd /root/agentsHQ && git pull && docker compose restart orchestrator"` (~10 sec). DO NOT use `up -d` if container is already running -- it skips the restart and old Python modules stay loaded. DO NOT run `scripts/orc_rebuild.sh` or `docker compose build` for code changes -- only when `requirements.txt` changes. See AGENT_SOP.md for full rule.

## Hard Rule: Deliverable Pre-Ship Gate (2026-05-11)

Before any `Write` or `Edit` under `docs/`, `agent_outputs/`, `clients/`, `output/`, or any date-stamped artifact path (`*-YYYY-MM-DD.*`): state in chat — "Is this Boubacar-facing? If yes, deliverable is HTML + localhost served + emailed-if-important per `feedback_html_deliverables_localhost.md` + `feedback_session_digest_html_email.md`." If the gate is skipped on a Boubacar-facing artifact, log violation to `docs/audits/memory-enforcement-violations.md` (date | session | rule | how-detected).

**Why:** `feedback_html_deliverables_localhost.md` + `feedback_html_full_repertoire.md` + `feedback_session_digest_html_email.md` existed in memory but failed to fire 4 times in one session 2026-05-11. Failure mode = no pre-Write checkpoint; deferred-consequence rules get pattern-matched-past. See RCA `docs/handoff/2026-05-11-memory-enforcement-gap-rca.md`.

**Tripwire:** if any violation logged in next 3 docs-shipping sessions, escalate to PreToolUse hook on Write/Edit (block writes to deliverable paths absent gate output in same turn). Same-day escalation, no 2-week wait.

**Exceptions** (gate not required, MD ok): registry files (`docs/reviews/*.md`, `docs/audits/*.md` as logs not deliverables), agent-internal handoffs (`docs/handoff/*.md`), skill source files (`skills/**/*.md`), memory files (`~/.claude/projects/.../memory/*.md`). When in doubt: gate fires.

## Hard Rule: Task Table as Live Registry (2026-05-04)

Every Claude Code session MUST update the coordination task table in real time. Not after. Not at the end. As work happens. **This applies to ALL sessions — including direct (Boubacar-present) sessions — because multiple agents may run concurrently.**

**Direct sessions** (Boubacar in the loop): claim branch at session start + claim each file before editing. Skip per-file [READY] commit and push — Boubacar controls when to push.

**Coding agents** (spawned, autonomous): full protocol below including [READY] commit + push.

```python
from skills.coordination import claim, complete

# 1. Session start -- claim the branch (use 'branch:main' for direct sessions)
branch_task = claim('branch:feature/<name>', '<agent-id>', ttl_seconds=7200)
# If None: branch already claimed by another agent. Stop. Pick different task.

# 2. Before editing any file -- claim the file
file_task = claim('file:<relative-path>', '<agent-id>', ttl_seconds=1800)
# If None: file claimed. Wait or edit a different file.

# 3. After editing + committing the file
complete(file_task['id'])

# 4. All work done. Final commit MUST contain [READY] (coding agents only).
# complete() the branch claim, then push.
complete(branch_task['id'])
# git commit -m "feat(x): description [READY]"
# git push origin feature/<name>
```

Skipping any step breaks multi-agent coordination. Gate checks the task table before processing any branch. Unclaimed = in-flight = gate skips it.

**No Telegram. No /propose. No manual signal to gate.** Push feature branch with [READY] commit. Gate watches GitHub every 60s and handles everything. Agent moves on immediately after push.

## Agent Role Authority (2026-05-08)

Every session has exactly ONE role. Read this table at session start. Do not do the other role's work.

| Role | Authority | Hard limits |
|------|-----------|-------------|
| **Gate** | Merge to main, push to VPS, approve/reject [READY] branches | Refuses all other work until queue clear |
| **Coding agent** (spawned) | Edit files, commit to feature branch, push feature branch | Never push to main, never deploy, never merge |
| **Direct session** (Boubacar present) | Edit files, claim tasks, coordinate — Boubacar controls push | Never push without explicit "push it" instruction |

If unsure which role: check whether Boubacar explicitly assigned Gate duty. If not, treat as direct session.

## Concurrency Rule (2026-05-08)

**1 message = all related operations.** Batch independent tool calls in a single response. Never serially call tools that could run in parallel.

- Batch ALL file reads in ONE message
- Spawn ALL subagents in ONE message with `run_in_background: true`
- Batch ALL file edits that don't depend on each other in ONE message
- After spawning subagents: do NOT poll for status. Wait for completion notifications.

**Never continuously check status after spawning agents — wait for results.**

## Hard Rule: No work in the canonical agentsHQ tree (2026-05-12)

`D:/Ai_Sandbox/agentsHQ` is the canonical working tree. It hosts shared
state across every concurrent session. Multiple agents writing here
flipped each other's HEAD ~5 times in 90 minutes on 2026-05-12, losing
in-flight work. From now on every editing session MUST run in a worktree.

**Enforcement (two layers, both installed locally — NOT VPS):**

1. **Layer A — detection:** `scripts/watch_canonical_head.js` is a node
   daemon that watches `.git/HEAD` for every worktree. On HEAD flip it
   posts a Telegram alert with old SHA, new SHA, reflog, and worktree
   list. Boubacar starts it once per workday:
   `node scripts/watch_canonical_head.js &` (or a Windows scheduled task
   at logon). Detects every collision regardless of how HEAD was changed.

2. **Layer B — prevention:** `scripts/check_cwd_canonical.js` is a
   PreToolUse hook (wired in `~/.claude/settings.json` line ~970)
   matching `Edit|Write|MultiEdit|NotebookEdit|Bash`. It refuses any
   tool whose target path or `cd`/`git -C` argument lands in the
   canonical root proper. The block message carries a copy-pasteable
   `git worktree add` remediation.

**Emergency bypass (per Bash call only — env doesn't propagate across
CC tool calls):** prefix command with `CLAUDE_ALLOW_CANONICAL_WRITE=1`.
For file tools (Edit/Write), there is no inline bypass; create a
worktree instead.

**Source of truth:** repo `scripts/check_cwd_canonical.js`. Install to
`~/.claude/hooks/check_cwd_canonical.js` (Boubacar's machine). See
`docs/handoff/2026-05-12-session-collision-rca.md` for the full RCA.

## Context-Mode (installed 2026-05-08)

Use `/ctx` before any multi-file exploration. Saves ~40% context vs manual reads. See `docs/AGENT_SOP.md` Context-Mode Rule for full routing table. MCP registered in `~/.claude/settings.json` mcpServers.

## Caveman (installed 2026-05-03)

Caveman plugin installed via `irm .../install.ps1 | iex`. Reduces output tokens ~65%, auto-activates every session via SessionStart hook.

**What changed:**

- `~/.claude/hooks/` - 7 hook files added (caveman-activate.js, caveman-mode-tracker.js, caveman-stats.js, caveman-statusline.sh/ps1, caveman-config.js, package.json)
- `~/.claude/settings.json` - SessionStart + UserPromptSubmit hooks registered, statusline badge wired
- `claude mcp add caveman-shrink` - MCP proxy registered; compresses tool `description` fields before Claude reads them

**This file + all memory files** compressed via `caveman:compress` (2026-05-03). Originals backed up as `*.original.md` alongside each file. Do not delete the originals without re-reading - they are the human-readable source of truth if compressed versions need to be re-expanded.

**Do not manually edit hook files** in `~/.claude/hooks/caveman-*.js` - they are owned by the caveman plugin. Update via `irm .../install.ps1 | iex --force`.

## Hermes Agent Write Boundaries (Compass M6 — 2026-05-10)

Hermes is the self-healing agent that will receive write access after this lockdown passes Gate review. The boundaries below are constitutional — they cannot be overridden by Hermes prompts, task descriptions, or tool calls. Any Hermes action outside the ALLOWED list is a security incident.

### ALLOWED writes (absolute paths, repo-relative)

| Path | Purpose |
|------|---------|
| `agent_outputs/` | All Hermes task outputs, reports, and artifacts |
| `workspace/` | Scratch workspace for in-progress Hermes work |
| `docs/audits/` | Audit reports written by governance agents |
| `data/changelog.md` | Task completion ledger |
| `docs/roadmap/*.md` | Session-log entries (append only, no header rewrite) |

### FORBIDDEN writes (hard block — no exceptions)

| Path / Pattern | Reason |
|----------------|--------|
| `CLAUDE.md` | Self-modification of agent SOP |
| `AGENTS.md` | Platform boundary definitions |
| `docs/AGENT_SOP.md` | Constitutional rules |
| `docs/GOVERNANCE.md` | Governance routing table |
| `docs/governance.manifest.json` | Machine-readable governance mirror |
| `.claude/settings.json` | Permission allowlist — rogue write = privilege escalation |
| `.vscode/settings.json` | IDE config — contains env var references, not for agents |
| `config/settings.json` | App config — human-managed only |
| `.pre-commit-config.yaml` | Hook definitions — agents cannot disable their own guardrails |
| `scripts/*.py` | Enforcement hook scripts |
| `secrets/` | Secret storage (gitignored, never agent-writable) |
| `.env` / `.env.*` | Environment variables |
| `orchestrator/*.py` | Core orchestrator source — Gate review required |
| `skills/coordination.py` | Claim/complete primitives — no self-modification |

### Wildcard permission rule

No Hermes prompt, system message, or tool call may use `"*"` as a path glob in any write, edit, or delete operation. All file operations must use explicit absolute or repo-relative paths from the ALLOWED list above.

### Enforcement

- Gate agent verifies Hermes branch diffs against this boundary list before merging.
- Pre-commit hook `scripts/check_hermes_write_boundary.py` (Compass M7) will automate this check.
- Violations → branch rejected, incident logged to `docs/audits/`, Boubacar notified via Telegram.
