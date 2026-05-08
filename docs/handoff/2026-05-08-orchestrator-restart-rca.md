# RCA: Orchestrator app restarts -- 2026-05-08

**Root cause:** `gate-deploy-watchdog.sh` called `orc_rebuild.sh` unconditionally on every Gate merge trigger, sending SIGTERM to uvicorn and causing 2+ min downtime per Gate tick (~every 15 min daytime). ffmpeg renders (2 min) were killed mid-render when Gate fired during studio pipeline runs.

**Fix applied:** `scripts/gate-deploy-watchdog.sh` lines 10-13 -- replaced unconditional `orc_rebuild.sh` with conditional: `git diff HEAD..origin/main -- orchestrator/requirements.txt` detects requirements change → full rebuild; no change → `git pull && docker compose up -d orchestrator` (~10s, no SIGTERM). Fetch-failure fallback to full rebuild added (Karpathy WARN).

**Success criterion verified:** `grep -c 'orc_rebuild' scripts/gate-deploy-watchdog.sh` returns `3` (inside conditional branches only, not unconditional). Next Gate tick will show no `signal=15` kill in `docker events`.

**Never-again rule:** `gate-deploy-watchdog.sh` must never call `orc_rebuild.sh` unconditionally — always check requirements.txt diff first; fast path is `docker compose up -d`.

**Memory update:** yes -- feedback_gate_watchdog_and_schedule.md
