# thepopebot Integration — Design Spec

**Date:** 2026-04-08
**Author:** Boubacar Barry (Catalyst Works Consulting)
**Status:** Approved for implementation planning

---

## Problem Statement

agentsHQ runs on a VPS and is only accessible via SSH from a desktop. There is no way to:
- Run or monitor a Claude Code session from a phone or laptop browser
- Fire a coding task and let it run headlessly while away from the desk
- Inspect running sessions or session output without opening a terminal

The goal is to add these capabilities without breaking the existing stack.

---

## What We Are Building

A **thepopebot sidecar**: the `event-handler` container from the thepopebot project deployed
alongside the existing agentsHQ Docker stack, exposed at `agentsHQ.boubacarbarry.com`, connected
to the existing orchestrator via internal Docker network webhooks.

This is additive only. No existing services are modified.

---

## Architecture Overview

```
Internet
  |
  v
Traefik (ports 80/443) [root-traefik-1 — already running]
  |
  |-- Host: agentsHQ.boubacarbarry.com --> thepopebot event-handler (port 3001 internal)
  |-- Host: n8n.srv1040886.hstgr.cloud --> root-n8n-1 (already wired)
  |
  v
Docker orc-net (internal)
  |
  |-- orc-crewai (port 8000) — CrewAI orchestrator
  |-- orc-postgres (port 5432)
  |-- orc-qdrant (port 6333)
  |-- orc-metaclaw

thepopebot event-handler talks to orc-crewai via:
  POST http://orc-crewai:8000/run-async  (fire task)
  GET  http://orc-crewai:8000/status/{job_id}  (poll)
  callback_url: http://thepopebot-event-handler:3001/webhook/agent-complete
```

---

## Component Inventory

### Existing (untouched)
| Component | Location | Role |
|---|---|---|
| root-traefik-1 | /root/docker-compose.yml | Reverse proxy, TLS |
| root-n8n-1 | /root/docker-compose.yml | Workflow automation |
| orc-crewai | /root/agentsHQ/docker-compose.yml | CrewAI orchestrator, port 8000 |
| orc-postgres | /root/agentsHQ/docker-compose.yml | PostgreSQL |
| orc-qdrant | /root/agentsHQ/docker-compose.yml | Vector memory |
| orc-metaclaw | /root/agentsHQ/docker-compose.yml | Meta-learning proxy |
| @agentsHQ4Bou_bot | Telegram | Primary notification + task input channel |

### New (thepopebot sidecar)
| Component | Location | Role |
|---|---|---|
| thepopebot-event-handler | /root/agentsHQ/thepopebot/ | Next.js UI + agent runner, port 3001 internal |
| thepopebot-litellm | /root/agentsHQ/thepopebot/ | OpenAI→Anthropic API translation (internal only) |
| thepopebot-runner | /root/agentsHQ/thepopebot/ | Self-hosted GitHub Actions runner |
| docker-compose.thepopebot.yml | /root/agentsHQ/ | Isolated compose file, independent of existing stack |

### New (agent containers — ephemeral)
Spun up on demand by thepopebot event-handler via Docker socket. Clones `bokar83/agentsHQ`
repo, runs Claude Code in the specified branch, commits and opens PR. Torn down after job completes.

---

## Port Map (Locked)

| Port | Service | Exposure |
|---|---|---|
| 80 | Traefik | Public (HTTP → redirect to HTTPS) |
| 443 | Traefik | Public (HTTPS) |
| 3001 | thepopebot event-handler | Internal Docker only |
| 4000 | thepopebot LiteLLM | Internal Docker only |
| 7681 | ttyd (per agent container) | Internal, proxied via WS through event-handler |
| 8000 | orc-crewai | Internal Docker + existing external (0.0.0.0) |
| 5432 | orc-postgres | Internal Docker + existing external (0.0.0.0) |
| 5678 | root-n8n-1 | Internal (127.0.0.1 only) |
| 6333 | orc-qdrant | Internal (127.0.0.1 only) |
| 22 | SSH | Public |

No port conflicts. All new ports are either internal-only or unused.

---

## Authentication

### thepopebot UI
- `next-auth` v5 JWT cookie sessions
- Single admin user created during `npm run setup`
- No public registration; personal use only
- HTTPS enforced by Traefik

### Claude Code auth (inside agent containers)
- **Method:** `ANTHROPIC_API_KEY` environment variable
- **Key type:** `sk-ant-api03-*` (Console API key — already in `/root/agentsHQ/.env`)
- **NOT using:** `sk-ant-oat01-*` OAuth tokens (deprecated for external use ~Feb 20 2026)
- thepopebot's `auth.sh` falls back to `ANTHROPIC_API_KEY` natively; no config changes needed

### Orchestrator API calls (thepopebot → orc-crewai)
- `X-Api-Key` header using `ORCHESTRATOR_API_KEY` from `.env`
- Internal Docker network call; not exposed publicly

---

## Telegram Strategy

thepopebot's own Telegram bot is **disabled** by leaving `TELEGRAM_BOT_TOKEN` unset in its config.

Notifications flow:

1. thepopebot receives job completion (via callback_url from `/run-async`, or GitHub Actions webhook in Phase 4)
2. orc-crewai orchestrator sends Telegram notification via existing `@agentsHQ4Bou_bot` as part of job completion
3. Result also appears in thepopebot browser UI (via polling or callback)

One bot. One inbox. No conflicts.

---

## GitHub Integration

**Repo:** `bokar83/agentsHQ`
**Feature branch for this build:** `feature/thepopebot-sidecar`
**Agent job branches:** `agent-job/{uuid}` (created per headless job, auto-deleted after merge)

**GitHub Actions required (thepopebot-managed):**
- `auto-merge.yml` — squash-merges agent-job/* PRs when `AUTO_MERGE=true`
- `notify-pr-complete.yml` — fires webhook to thepopebot on PR merge
- `rebuild-event-handler.yml` — rebuilds Next.js on push to main
- `upgrade-event-handler.yml` — manual upgrade workflow

**GitHub PAT required scopes:**
- Actions (R/W), Administration (R/W), Contents (R/W), Metadata (R)
- Pull requests (R/W), Secrets (R/W), Workflows (R/W)

**`RUNS_ON`:** `self-hosted` (using thepopebot's `runner` container on VPS)

---

## DNS

**Record to add:**
```
Type:  A
Host:  agentsHQ
Value: 72.60.209.109
TTL:   300
```
Registrar: wherever `boubacarbarry.com` is registered (nameservers: ns1/ns2.dns-parking.com).
Manual action required — no programmatic DNS access configured.

**Staging subdomain (Phase 1 only):**
```
Type:  A
Host:  agentsHQ-dev
Value: 72.60.209.109
TTL:   300
```
Remove after Phase 2 promotion.

---

## Save Point Strategy

Before any VPS changes:
1. Tag current main: `git tag pre-thepopebot && git push origin pre-thepopebot`
2. Work on branch: `feature/thepopebot-sidecar` (local + pushed to origin)
3. All thepopebot files go in `/root/agentsHQ/thepopebot/` with own compose file
4. Rollback: `docker-compose -f docker-compose.thepopebot.yml down` — zero impact on existing stack
5. Existing stack compose files (`/root/docker-compose.yml`, `/root/agentsHQ/docker-compose.yml`) are never modified

---

## Phased Implementation

### Phase 0 — Save Point and Prep (zero risk)
- Tag `pre-thepopebot` on current main
- Create `feature/thepopebot-sidecar` branch
- Add DNS A records for `agentsHQ.boubacarbarry.com` and `agentsHQ-dev.boubacarbarry.com`
- Verify DNS propagates to 72.60.209.109
- Confirm GitHub PAT has required scopes

### Phase 1 — Deploy Sidecar (isolated, dev subdomain)
- `npx thepopebot init` in `/root/agentsHQ/thepopebot/` on VPS
- Strip thepopebot's bundled Traefik from its compose
- Add Traefik Docker labels using dev subdomain
- Set `TELEGRAM_BOT_TOKEN` = unset (disable thepopebot Telegram)
- Set `ANTHROPIC_API_KEY` = existing key from `.env`
- Assign internal port 3001
- Join `orc-net` Docker network (so it can reach orc-crewai)
- Validate: browser login at agentsHQ-dev.boubacarbarry.com
- Validate: interactive Claude Code terminal opens from mobile browser
- Validate: existing stack (orchestrator, n8n, Telegram) unaffected

### Phase 2 — Promote to Production
- Update Traefik label to `agentsHQ.boubacarbarry.com`
- Remove dev subdomain DNS record
- Merge `feature/thepopebot-sidecar` → main, push to origin and VPS

### Phase 3 — Connect to agentsHQ Orchestrator
- Add thepopebot skill: calls `POST http://orc-crewai:8000/run-async` with `X-Api-Key` header
- Webhook receiver in thepopebot at `/webhook/agent-complete` receives callback payloads
- On completion: orchestrator notifies `@agentsHQ4Bou_bot` via existing notifier.py
- Test: type task in browser → CrewAI executes → result in browser + Telegram notification
- Validate via `/run-async` + `callback_url` pattern (already supported in orchestrator)

### Phase 4 — Headless Agent Job Runner
- Configure `agent-job/CRONS.json` and GitHub Actions workflows in `bokar83/agentsHQ` repo
- Register self-hosted GitHub Actions runner (`runner` container)
- Configure `AUTO_MERGE=true`, `ALLOWED_PATHS=/logs,/outputs,/agent_outputs`
- Test: fire headless Claude Code job from mobile → GitHub PR created → auto-merged → Telegram notified
- Pin thepopebot NPM version after confirming all workflows function

### Phase 5 — Bidirectional Session Sync (Future)
See: [docs/roadmap/future-enhancements.md](../roadmap/future-enhancements.md)

---

## Risk Register

| Risk | Severity | Mitigation |
|---|---|---|
| Port conflict on 80/443 | RESOLVED | Existing Traefik uses Docker label routing; labels added, no binding conflict |
| Claude Code OAuth deprecated | RESOLVED | Using ANTHROPIC_API_KEY (Console key, already in .env) |
| Breaking existing stack | RESOLVED | Separate compose file; `docker-compose down` reverts instantly |
| Docker socket access | MEDIUM | thepopebot mounts /var/run/docker.sock; can see all containers. Acceptable for personal VPS. |
| thepopebot NPM version drift | MEDIUM | Pin version during init; disable auto-upgrade workflow until manually reviewed |
| GitHub PAT scope gaps | MEDIUM | Verify PAT has all 7 required scopes before Phase 1; create new PAT if needed |
| Self-hosted runner registration | MEDIUM | Runner container requires GitHub token and registration step; confirm runner appears in repo settings before Phase 4 |
| LiteLLM unpinned image | LOW | thepopebot uses `litellm:main-latest`; pin to specific tag after Phase 1 |
| n8n | NONE | Hard rule: never touch n8n Docker or VPS infrastructure |

---

## What This Does NOT Do

- Does not replace agentsHQ orchestrator or CrewAI
- Does not add a second Telegram bot
- Does not touch n8n
- Does not modify `/root/docker-compose.yml` or `/root/agentsHQ/docker-compose.yml`
- Does not use OAuth tokens (deprecated)
- Does not sync browser and Telegram conversation history (Phase 5, future)

---

## Success Criteria

- [ ] `agentsHQ.boubacarbarry.com` loads in mobile browser with HTTPS
- [ ] Interactive Claude Code terminal opens and accepts input from phone
- [ ] Session persists when switching from phone to desktop browser
- [ ] Typing a task in browser chat triggers a CrewAI job via `/run-async`
- [ ] Job completion sends Telegram notification via `@agentsHQ4Bou_bot`
- [ ] Headless Claude Code job fires, creates PR, auto-merges, notifies Telegram
- [ ] `docker-compose -f docker-compose.thepopebot.yml down` reverts everything cleanly
- [ ] All existing services (orchestrator, n8n, Telegram bot, Qdrant) continue functioning
