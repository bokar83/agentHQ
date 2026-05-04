# L5 Learn  -  Curator Pattern Spec

Translated from hermes-agent (NousResearch/hermes-agent, MIT) curator architecture.
Absorb date: 2026-05-03. Implementer may read on 2026-05-08 when L5 data dependency clears.

## Acceptance Checklist

Before this doc is considered complete, an L5 implementer must answer all five from this doc alone:

- [ ] 1. What triggers the idle background pass, and how is "idle" defined?
- [ ] 2. What is the auxiliary LLM call contract (inputs, outputs, model)?
- [ ] 3. What is the `task_outcomes` read path and schema?
- [ ] 4. What is the heuristics output format and where does it land?
- [ ] 5. How is run state persisted and read across sessions?

---

## 1. Idle-Trigger Mechanism

**hermes-agent pattern:** `curator.py` uses inactivity-triggered execution. No cron daemon.
When the agent is idle AND `now - last_run_at > interval_hours` (default 7 days), it spawns
a forked background AIAgent via `maybe_run_curator()`. State lives in `.curator_state` JSON.

**agentsHQ translation:**

- Idle = no active Claude Code session for the VPS orchestrator (orc-crewai)
- Trigger = existing heartbeat wake mechanism (L2 already live). Add a condition check in the
  5-min wake handler: `if hours_since_last_l5_run > 168 and task_outcomes_count >= 14_days_threshold`
- Implementation: check `autonomy_state.json` → `l5_learn.last_run_at` and
  `l5_learn.outcomes_since_last_run` before spawning
- Default interval: 7 days (configurable in autonomy_state.json)
- Minimum idle: 2 hours (no L5 run during active publishing windows)

---

## 2. Auxiliary LLM Call Contract

**hermes-agent pattern:** Curator spawns a `forked AIAgent` using the auxiliary client
(never the main session client  -  preserves prompt cache). The forked agent receives
a task description and the skill inventory, outputs structured JSON decisions
(pin / archive / consolidate / patch).

**agentsHQ translation:**

Inputs to the background L5 subagent:
```json
{
  "task": "analyze_performance_signal",
  "outcomes_path": "data/task_outcomes.json",
  "current_heuristics_path": "griot/config/heuristics.json",
  "min_samples": 14,
  "output_path": "griot/config/heuristics.json",
  "state_path": "autonomy_state.json"
}
```

The subagent prompt instructs it to:
1. Read `task_outcomes` (last N records)
2. Group by content_type, platform, time_of_day
3. Compute engagement signal (impressions / clicks / replies)
4. Identify top-3 and bottom-3 performing patterns
5. Output updated `heuristics.json` with delta commentary

Model: use auxiliary/cheaper model (e.g., haiku)  -  not the main orchestrator model.
Never touch the main session prompt cache.

Strict invariants (from hermes curator):
- Never auto-delete outcomes data  -  only append
- Pinned heuristics bypass auto-update (flag in heuristics.json: `"pinned": true`)
- If subagent errors, log to autonomy_state.json and skip  -  do not retry in same cycle

---

## 3. task_outcomes Read Path and Schema

**Current location (Atlas L4, live):** Notion `task_outcomes` table + local mirror at
`data/task_outcomes.json` (to be confirmed  -  check actual L4 write path in atlas.md).

**Minimum schema L5 needs:**

```json
[
  {
    "post_id": "string",
    "content_type": "linkedin_post | x_post | newsletter",
    "published_at": "ISO8601",
    "platform": "linkedin | x",
    "outcome": "approved | skipped | posted",
    "engagement": {
      "impressions": 0,
      "clicks": 0,
      "replies": 0
    },
    "griot_attributes": {
      "hook_type": "string",
      "topic_cluster": "string",
      "time_slot": "07:00 | 11:00 | 12:00 | 14:00"
    }
  }
]
```

If `engagement` fields are not populated by L4 (L4 currently only sets `outcome`),
L5 first run should default engagement to nulls and set `l5_learn.status = "awaiting_engagement_data"`.
Do not produce heuristics from approval-only signal  -  wait for real engagement data.

---

## 4. Heuristics Output Format

Written to `griot/config/heuristics.json`. This file is read by griot-morning at proposal time.

```json
{
  "updated_at": "ISO8601",
  "generated_by": "l5_learn_v1",
  "sample_size": 42,
  "pinned": false,
  "top_patterns": [
    {
      "content_type": "linkedin_post",
      "hook_type": "contrarian",
      "time_slot": "07:00",
      "avg_engagement_score": 0.84,
      "recommendation": "prioritize"
    }
  ],
  "bottom_patterns": [
    {
      "content_type": "x_post",
      "hook_type": "list",
      "time_slot": "14:00",
      "avg_engagement_score": 0.12,
      "recommendation": "deprioritize"
    }
  ],
  "delta_commentary": "Contrarian hooks on LinkedIn morning slot outperformed list posts by 7x. Recommend reducing list posts to 1/week."
}
```

griot-morning reads `top_patterns` to bias topic/hook selection.
If `heuristics.json` is absent or `pinned: true`, griot-morning uses default weights.

---

## 5. Run State Persistence

**hermes-agent pattern:** `.curator_state` JSON written atomically via `tempfile + os.replace()`.
Fields: `last_run_at`, `last_run_duration_seconds`, `last_run_summary`, `paused`, `run_count`.

**agentsHQ translation  -  add to `autonomy_state.json`:**

```json
{
  "l5_learn": {
    "last_run_at": null,
    "last_run_duration_seconds": null,
    "last_run_summary": null,
    "outcomes_since_last_run": 0,
    "paused": false,
    "run_count": 0,
    "status": "awaiting_data"
  }
}
```

Write atomically: write to `autonomy_state.json.tmp`, then `mv` to `autonomy_state.json`.
Read at heartbeat wake to check trigger condition. Never delete  -  only update.

---

## Future Applications (not specced now)

These two motions also benefit from the same idle-trigger auxiliary LLM pattern.
Spec them when their producing motion is ready.

**Auto-approval loop hardening:**
A curator-style idle pass scans `approval_queue` for items older than 24h with
high-confidence signal (past-similar approved). Auto-approves with Telegram notification.
Removes Boubacar from daily approval decisions on obvious items.

**Skill health monitoring:**
Background agent checks last-used timestamps across 72 skills.
Flags stale skills (>90 days no invocation), runs smoke tests on critical path skills.
Makes the skill library self-maintaining.

---

## Source Reference

Pattern source: `agent/curator.py`, `agent/memory_manager.py`, `cron/scheduler.py`
in [NousResearch/hermes-agent](https://github.com/NousResearch/hermes-agent) (MIT license).
Clone at: `sandbox/.tmp/absorb-nousresearch-hermes-agent/` (read-only, safe to delete after L5 ships).
