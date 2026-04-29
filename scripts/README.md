# scripts/

Operational scripts for the agentsHQ deploy + runtime.

## orc_rebuild.sh

Coordination-aware wrapper around `docker compose build orchestrator && docker compose up -d orchestrator`.

**Always use this instead of bare `docker compose build orchestrator`.**

### Why

Bare `docker compose build orchestrator` followed by `docker compose up -d orchestrator` recreates the orc-crewai container, which kills any in-flight Python process inside it. On 2026-04-29, two parallel Claude Code sessions on the same VPS rebuilt the orchestrator simultaneously while morning_runner was running. Result: 4 morning_runner runs were killed mid-flight, ~30 Apollo credits burned redundantly, and SW pipeline never completed.

### What it does

1. Checks whether `task:morning-runner` is held in the coordination table. If yes, refuses to rebuild and exits with code 2. The runner finishes naturally; rebuild can retry afterwards.
2. Claims `task:orc-rebuild` so two simultaneous rebuilds cannot collide. If already held by another rebuild, exits with code 3.
3. Sources `.env` so `docker-compose` `${VAR}` interpolation works.
4. Runs `docker compose build orchestrator && docker compose up -d orchestrator`.
5. Waits up to 180s for orc-crewai to be healthy.
6. Releases the rebuild lock on exit (success or failure).

### Usage

```bash
# Standard: refuses if morning_runner is running
./scripts/orc_rebuild.sh

# Override the runner-in-flight check (still claims the rebuild lock)
./scripts/orc_rebuild.sh --force

# Print this help
./scripts/orc_rebuild.sh --help
```

### Exit codes

| Code | Meaning |
|------|---------|
| 0 | Rebuild + restart succeeded; orc-crewai is healthy |
| 1 | Build or up command failed |
| 2 | morning_runner is in flight; refused (use `--force` to override) |
| 3 | Another rebuild is already running; refused |
| 75 | Lock acquisition failed for an unknown reason |

### What is NOT blocked

This wrapper only gates the `docker compose build` + `docker compose up` deploy step. It does not block:

- Editing any source file (no docker involvement)
- Editing the Dockerfile (only the deploy step is gated)
- `docker exec`, `docker logs`, `docker inspect` (read-only, unaffected)
- Adding new services, env vars, mounts (those land on the next legitimate rebuild)

### Total restriction window

The morning_runner takes 5-10 minutes per run (1-2 times per day max). Outside that window, this wrapper behaves identically to a bare `docker compose build`.

### Bypass

If you genuinely need to rebuild while the runner is in flight (e.g., the runner is stuck and you need to kill it to roll forward a fix), pass `--force`. The rebuild lock is still claimed, so two `--force` calls cannot collide either.
