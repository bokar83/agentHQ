# RCA: gate -- 2026-05-11 (gate_poll telegram spam + gate_agent prefix gap)

**Root cause:** gate_agent.py:229 prefix filter only matched `feature/`, `feat/`, `fix/` while gate_poll.py:49 scans 7 prefixes (those + `docs/`, `chore/`, `refactor/`, `test/`). docs/+chore/ branches with `[READY]` tip were detected and Telegram-alerted by gate_poll but never entered gate_agent's review queue, so the 3 stuck branches (`docs/atlas-session-log-2026-05-08`, `docs/roadmap-studio-2026-05-11`, `chore/gitignore-tmp-screenshots`) re-spammed every 5-min cron tick.

**Fix applied:**
- `orchestrator/gate_agent.py:229` — replaced 3-prefix `startswith` chain with `any(branch.startswith(p) for p in ("feature/", "feat/", "fix/", "docs/", "chore/", "refactor/", "test/"))`. Matches gate_poll scope exactly. docs/+chore/ branches now route through `AUTO_APPROVE_PREFIXES` (line 84) for silent merge on docs-only diffs — no Telegram.
- `scripts/gate_poll.py` — added `/tmp/gate_poll_alerted.json` dedup sentinel keyed on `branch:tip_sha`. Suppresses re-alerts at same SHA across cron ticks. Stops bleeding even if gate_agent merge fails. Pre-populated on VPS for the 3 stuck branches before deploy.

**Success criterion verified:**
`ssh root@72.60.209.109 "GATE_DATA_DIR=/root/agentsHQ/data REPO_ROOT=/root/agentsHQ python3 /root/agentsHQ/orchestrator/gate_agent.py 2>&1 | tail -3"` →
`gate: tick done. merged=['chore/gitignore-tmp-screenshots', 'docs/atlas-session-log-2026-05-08', 'docs/roadmap-studio-2026-05-11'], failed=['fix/gate-agent-prefix-coverage'], blocked=[], held_high_risk=[]`. All 3 spam-source branches merged + deleted from origin. `fix/gate-agent-prefix-coverage` failed due to VPS scp'd files colliding with git merge — expected, fix already live on VPS, resolves on PR merge.

**Never-again rule:** When changing prefix-coverage rules in any gate component, change ALL gate components in the same PR. gate_poll + gate_agent must agree on what counts as a reviewable branch. Asymmetry = infinite loop.

**Memory update:** yes — `feedback_gate_poll_gate_agent_prefix_parity.md`
