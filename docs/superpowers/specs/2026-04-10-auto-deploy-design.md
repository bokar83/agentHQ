# Auto-Deploy Stack Design Spec

**Date:** 2026-04-10
**Status:** Approved

---

## Problem

The VPS filesystem at `/root/agentsHQ` is never automatically updated when commits land on GitHub. Three containers need updating after a push to main:

| Container | Update mechanism needed |
|---|---|
| `orc-crewai` | Rebuild Docker image + force-recreate |
| `thepopebot-chat-ui` | nginx reload (bind-mounted, instant after git pull) |
| `thepopebot-event-handler` | Already handled by `rebuild-event-handler.yml` |

The existing `rebuild-event-handler.yml` only syncs inside the event-handler container, not the host filesystem. `deploy.sh` exists but is manual and Windows git push is broken.

---

## Solution: Option A -- Runner Direct Mount + Deploy Script

Add a bind mount of `/root/agentsHQ` into the existing `thepopebot-runner` container so it can git pull directly on the host filesystem. A versioned deploy script handles change detection, rebuilds, and reloads. A new GitHub Actions workflow triggers it on every push to main.

---

## Architecture

### Three file changes + one network addition

**1. `docker-compose.thepopebot.yml`**
- Add volume `- /root/agentsHQ:/root/agentsHQ` to the runner service
- Add `orc-net` network to the runner service so it can reach `orc-crewai:8000` for health checks

**2. `scripts/deploy-stack.sh`** (new)
- Git pull with explicit credential setup from `GH_TOKEN`
- SHA-based change detection with bootstrap and force-push guards
- Independent deploy paths for orchestrator and chat-ui (both attempt regardless of the other's result)
- Rollback: tag previous image before build; restore on health check failure
- Health check via `docker exec orc-crewai curl http://localhost:8000/health`
- Atomic `.deploy-sha` write via tmp file + mv

**3. `.github/workflows/deploy-agentshq.yml`** (new)
- Triggers on push to `main` with path filter: `orchestrator/**`, `thepopebot/chat-ui/**`, `scripts/**`, `docker-compose*.yml`
- Runs on `self-hosted` runner
- Shares concurrency group `event-handler-deploy` with `cancel-in-progress: false`
- Single step: `docker exec thepopebot-runner bash /root/agentsHQ/scripts/deploy-stack.sh`
- `timeout-minutes: 20`

---

## Change Detection

```
On script start:
  if .deploy-sha missing OR git cat-file -e $sha fails:
    CHANGED_PATHS = "all"  # full deploy
  else:
    CHANGED_PATHS = git diff --name-only $sha HEAD

Orchestrator deploy if: CHANGED_PATHS == "all" OR any path matches orchestrator/**
Chat-UI reload if: CHANGED_PATHS == "all" OR any path matches thepopebot/chat-ui/**
Thepopebot compose redeploy if: CHANGED_PATHS == "all" OR any path matches docker-compose.thepopebot.yml
```

---

## Rollback Behavior

Before any orchestrator rebuild:
1. Tag current image: `docker tag agentshq-orchestrator:latest agentshq-orchestrator:previous`
2. Build new image
3. Force-recreate container
4. Poll `docker exec orc-crewai curl http://localhost:8000/health` up to 10x at 10s intervals
5. If healthy: success, update `.deploy-sha`
6. If not healthy: restore `:previous` tag and force-recreate, exit 1

---

## Failure Behavior

- Orchestrator build fails: rollback to previous, exit 1, GitHub run goes red
- Chat-UI nginx reload fails: exit 1, GitHub run goes red
- Git pull fails: exit immediately, nothing rebuilt
- Runner container down: workflow step fails immediately
- Both paths run independently -- chat-ui reload is not blocked by orchestrator failure

---

## Implementation Order (Critical)

1. **Push Change 1 + 2** (compose file + deploy script) -- no workflow yet, safe to push
2. **SSH manual step**: get fresh runner registration token from GitHub Actions settings, then `docker compose -f docker-compose.thepopebot.yml up -d --force-recreate runner`, verify `/root/agentsHQ` is mounted and runner re-registers
3. **Push Change 3** (workflow file) -- now fires against a ready runner

---

## Known Constraints

- Container name `thepopebot-runner` must stay stable -- renaming it breaks the workflow
- `.deploy-sha` is gitignored (runtime state, not source)
- `docker-compose.thepopebot.yml` changes trigger a redeploy of affected thepopebot services
- No env var drift check in v1 -- documented as manual responsibility
- docker.sock exposure is accepted for single-operator VPS

---

## Out of Scope (v1)

- Env var drift detection
- Slack/Telegram deploy notifications
- Blue/green or zero-downtime orchestrator deploys
- Automated testing before deploy
