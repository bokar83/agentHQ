#!/usr/bin/env bash
# scripts/orc_rebuild.sh
# ======================
# Coordination-aware rebuild for the orc-crewai orchestrator container.
#
# Why this exists: bare `docker compose build orchestrator && docker compose
# up -d orchestrator` recreates orc-crewai, which kills any in-flight Python
# process inside it -- including a long-running morning_runner. On 2026-04-29
# this collision happened repeatedly between two parallel Claude Code sessions
# and burned API credits + lost work.
#
# What this does:
#   1. Refuse to rebuild if `task:morning-runner` is currently held.
#   2. Claim `task:orc-rebuild` so two simultaneous rebuilds cannot stomp.
#   3. Source .env (so docker-compose interpolation works).
#   4. Run `docker compose build orchestrator && docker compose up -d orchestrator`.
#   5. Release the rebuild lock.
#
# Override: pass --force to bypass the morning-runner check (still claims the
# rebuild lock). Use only when you genuinely know what you are doing.
#
# Usage:
#   ./scripts/orc_rebuild.sh
#   ./scripts/orc_rebuild.sh --force
#
# Exit codes:
#   0   rebuild + restart succeeded
#   1   build or up failed
#   2   morning_runner currently in flight (lock held), refused
#   3   another rebuild already running (lock held), refused
#   75  (EX_TEMPFAIL) lock acquisition failed for unknown reason

set -euo pipefail

REPO_ROOT="${REPO_ROOT:-/root/agentsHQ}"
RUNNER_LOCK_RESOURCE="task:morning-runner"
REBUILD_LOCK_RESOURCE="task:orc-rebuild"
REBUILD_LOCK_TTL_SECONDS=600  # 10 minutes max for a rebuild + restart

# ANSI color (only if stdout is a TTY)
if [ -t 1 ]; then
  RED='\033[0;31m'
  YEL='\033[0;33m'
  GRN='\033[0;32m'
  RST='\033[0m'
else
  RED=''; YEL=''; GRN=''; RST=''
fi

log() { printf "%b[orc_rebuild]%b %s\n" "$YEL" "$RST" "$*"; }
err() { printf "%b[orc_rebuild]%b %s\n" "$RED" "$RST" "$*" >&2; }
ok()  { printf "%b[orc_rebuild]%b %s\n" "$GRN" "$RST" "$*"; }

FORCE=0
for arg in "$@"; do
  case "$arg" in
    --force) FORCE=1 ;;
    -h|--help)
      grep '^# ' "$0" | sed 's/^# \?//'
      exit 0
      ;;
    *) err "unknown arg: $arg"; exit 2 ;;
  esac
done

cd "$REPO_ROOT"

# Step 1: refuse if morning-runner is in flight (unless --force)
# Runs inside orc-crewai container because that is where psycopg2 lives.
# If orc-crewai is not running, no morning_runner can be in flight, so skip.
ORC_RUNNING=$(docker ps --filter name=orc-crewai --format '{{.Names}}' | head -1)

if [ "$FORCE" -eq 0 ] && [ -n "$ORC_RUNNING" ]; then
  log "checking $RUNNER_LOCK_RESOURCE before rebuild..."
  RUNNING_JSON=$(docker exec orc-crewai python3 -c "
import json
try:
    from skills.coordination import list_running
    rows = list_running()
    held = [
        {k: (v.isoformat() if hasattr(v, 'isoformat') else v) for k, v in r.items()}
        for r in rows if r.get('resource') == '$RUNNER_LOCK_RESOURCE'
    ]
    print(json.dumps(held))
except Exception as e:
    import sys; sys.stderr.write(f'coordination check failed: {e}\n')
    print('[]')
" 2>&1) || true

  if [ -n "$RUNNING_JSON" ] && [ "$RUNNING_JSON" != "[]" ]; then
    err "$RUNNER_LOCK_RESOURCE is currently held:"
    err "  $RUNNING_JSON"
    err ""
    err "Refusing to rebuild while morning_runner is in flight."
    err "Wait for it to finish, or pass --force to override."
    exit 2
  fi
  log "$RUNNER_LOCK_RESOURCE is free"
elif [ -z "$ORC_RUNNING" ]; then
  log "orc-crewai is not running; skipping runner-lock check"
fi

# Step 2: claim the rebuild lock so two simultaneous rebuilds cannot collide
# Same constraint: only available if orc-crewai is up. If down, we are first.
HOLDER="$(hostname)/pid=$$/orc_rebuild.sh"
TASK_ID=""
if [ -n "$ORC_RUNNING" ]; then
  log "claiming $REBUILD_LOCK_RESOURCE..."
  TASK_ID=$(docker exec orc-crewai python3 -c "
from skills.coordination import claim
task = claim(resource='$REBUILD_LOCK_RESOURCE', holder='$HOLDER', ttl_seconds=$REBUILD_LOCK_TTL_SECONDS)
if task is None:
    raise SystemExit(3)
print(task['id'])
" 2>&1) || {
    rc=$?
    if [ "$rc" -eq 3 ]; then
      err "$REBUILD_LOCK_RESOURCE already held by another rebuild. Refusing."
      exit 3
    fi
    err "could not claim rebuild lock (rc=$rc)"
    exit 75
  }
  log "got rebuild lock: task_id=$TASK_ID"
else
  log "orc-crewai is not running; skipping rebuild-lock claim"
fi

# Always release on exit (success or fail). Note: after rebuild, orc-crewai is
# the NEW container. The lock row in DB persists across container restarts
# because the DB lives in orc-postgres. Use the new container to release.
release_lock() {
  if [ -z "$TASK_ID" ]; then
    return 0
  fi
  # Wait briefly for new container to be exec-able
  for _ in 1 2 3 4 5; do
    if docker exec orc-crewai python3 -c "
from skills.coordination import complete
try:
    complete('$TASK_ID')
    print('[orc_rebuild] released $REBUILD_LOCK_RESOURCE')
except Exception as e:
    print(f'[orc_rebuild] WARN: release failed: {e}')
" 2>&1; then
      return 0
    fi
    sleep 2
  done
  err "WARN: could not release rebuild lock $TASK_ID (will expire after TTL of ${REBUILD_LOCK_TTL_SECONDS}s)"
}
trap release_lock EXIT

# Step 3: source .env so docker-compose ${VAR} interpolation resolves
if [ ! -f "$REPO_ROOT/.env" ]; then
  err ".env not found at $REPO_ROOT/.env"
  exit 1
fi
log "sourcing .env"
set -a
. "$REPO_ROOT/.env"
set +a

# Step 4: build + up
log "docker compose build orchestrator..."
if ! docker compose build orchestrator; then
  err "docker compose build failed"
  exit 1
fi

log "docker compose up -d orchestrator..."
if ! docker compose up -d orchestrator; then
  err "docker compose up failed"
  exit 1
fi

# Step 5: wait healthy
log "waiting for orc-crewai to be healthy..."
for _ in $(seq 1 60); do
  if docker ps --filter name=orc-crewai --format '{{.Status}}' | grep -q 'healthy'; then
    ok "orc-crewai healthy"
    exit 0
  fi
  sleep 3
done

err "orc-crewai did not become healthy within 180s"
exit 1
