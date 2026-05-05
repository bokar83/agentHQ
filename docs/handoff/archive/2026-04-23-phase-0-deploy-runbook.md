# Phase 0 VPS Deploy Runbook

**Date:** 2026-04-23
**Branch:** `feat/autonomy-safety-rails`
**Head commit:** `a707470`
**PR:** https://github.com/bokar83/agentHQ/pull/9
**Save point (rollback target):** `savepoint-pre-autonomy-20260423`

## Pre-flight (already done)

- [x] 10 commits on branch, pushed to origin
- [x] 35/35 pytest pass locally (15 autonomy + 20 orchestrator)
- [x] E2E integration test pass (guard + ledger + cap + kill persistence)
- [x] Static analysis, security audit, behavioral probes clean
- [x] Two review-found bugs fixed + regression tests added
- [x] SecureWatch CI check green
- [ ] Ultrareview cleared (WAITING)
- [ ] PR merged to main

## Deploy order (execute on the VPS after PR merges)

### Step 1: Pull main into VPS checkout

```bash
cd /root/agentsHQ                # confirm path if different
git fetch origin
git checkout main
git pull origin main
```

Expected: fast-forward, HEAD now at the merge commit.

### Step 2: Apply migration 004 to live Postgres

```bash
docker exec -i orc-postgres psql -U postgres -d postgres \
  < orchestrator/migrations/004_autonomous_flag.sql
```

Expected output: `ALTER TABLE` x2 (one per column).

### Step 3: Verify migration landed

```bash
docker exec orc-postgres psql -U postgres -d postgres \
  -c "\d llm_calls" | grep -E "autonomous|guard_decision"
```

Expected: two rows showing `autonomous | boolean` and `guard_decision | text`.

### Step 4: Add autonomy env vars to VPS .env

Edit `/root/agentsHQ/.env` (or wherever the active `.env` lives for the orc container). Append:

```
AUTONOMY_ENABLED=true
AUTONOMY_DAILY_USD_CAP=1.00
AUTONOMY_STATE_FILE=data/autonomy_state.json
```

### Step 5: Rebuild the orc container

```bash
cd /root/agentsHQ
docker compose up -d --build orc
```

Expected: orc rebuilds and restarts. `docker ps` shows `orc` healthy within 60 seconds.

### Step 6: Confirm new volume mount took effect

```bash
docker inspect orc --format '{{range .Mounts}}{{.Source}} -> {{.Destination}}{{"\n"}}{{end}}' \
  | grep data
```

Expected: a line containing `/root/agentsHQ/data -> /app/data` (or equivalent).

### Step 7: Tail logs for startup errors

```bash
docker logs -f orc 2>&1 | head -50
```

Look for:
- `DIGEST: thread started (07:00 America/Denver)`
- `DIGEST: morning digest thread registered`
- No tracebacks
- No `ImportError: No module named autonomy_guard`

Press Ctrl-C when confirmed clean.

### Step 8: Verify state file got created with safe defaults

```bash
cat /root/agentsHQ/data/autonomy_state.json
```

Expected:

```json
{
  "killed": false,
  "killed_at": null,
  "killed_reason": null,
  "crews": {
    "griot":     {"enabled": false, "dry_run": true},
    "hunter":    {"enabled": false, "dry_run": true},
    "concierge": {"enabled": false, "dry_run": true},
    "chairman":  {"enabled": false, "dry_run": true}
  }
}
```

### Step 9: Boubacar Telegram smoke test (your phone)

Send to the agentsHQ bot:

1. `/autonomy_status`
   - Expect: "Autonomy live", `$0.0000 / $1.00`, all 4 crews `off (dry-run)`.

2. `/pause_autonomy`
   - Expect: "Autonomy KILLED. All autonomous crews blocked."

3. `/autonomy_status`
   - Expect: first line `KILLED: telegram /pause_autonomy`.

4. `/resume_autonomy`
   - Expect: "Autonomy resumed. $0.0000 / $1.00 spent today."

5. `/spend`
   - Expect: "Autonomous spend today: $0.0000 / $1.00" + "(no autonomous calls yet today)".

### Step 10: Kill-switch persistence check

```bash
# Flip kill via Telegram first: send /pause_autonomy
# Then on VPS:
cat /root/agentsHQ/data/autonomy_state.json | python -c "import sys, json; print(json.load(sys.stdin)['killed'])"
# Should print: True

docker compose restart orc
sleep 15
cat /root/agentsHQ/data/autonomy_state.json | python -c "import sys, json; print(json.load(sys.stdin)['killed'])"
# Should still print: True
```

Then send `/resume_autonomy` from Telegram to clear it.

### Step 11: Morning digest sanity (optional : fires at 07:00 MT)

The digest will fire on its own tomorrow morning. If you want to test early without waiting:

```bash
docker exec orc python -c "from scheduler import _run_morning_digest; _run_morning_digest()"
```

Expected: Telegram message titled "agentsHQ morning digest, <day>", with "Autonomy live" + $0 spend.

## Rollback (if anything breaks)

```bash
cd /root/agentsHQ
git reset --hard savepoint-pre-autonomy-20260423
docker compose up -d --build orc
```

Migration is additive with defaults, so rollback does not need a migration reversal : the new columns just sit there unused. No data loss.

## Post-deploy

- Mark todo "VPS deploy + Telegram smoke test" complete
- Close PR #9 (or let the merge close it)
- Log the deploy in the save points memory file
- Kick off Phase 1 design (episodic memory + approval queue)

## What's next (not Phase 0)

- **Phase 1:** `feat/episodic-memory-and-queue` : Supabase tables for `task_outcomes`, `approval_queue`, `crew_lessons`. Enables the learning loop and human-in-the-loop approval substrate. Still no autonomous work running.
- **Phase 2:** `feat/heartbeat` : smart scheduler that wakes 3x/day plus event triggers.
- **Phase 3:** `feat/griot-autonomous` : first autonomous crew (content). L1 only, no publishing without approval.
