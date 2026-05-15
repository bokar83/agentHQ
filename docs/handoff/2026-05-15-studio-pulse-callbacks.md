# Studio pipeline pulse callbacks wired (2026-05-15)

**Branch:** `fix/studio-pulse-callbacks`
**Worktree:** `D:/tmp/wt-studio-pulse-callbacks`

## Context

The 2026-05-14 silence-watchdog RCA shipped `_alert_silence` in `orchestrator/studio_production_crew.py` posting a Telegram alert with two inline-keyboard buttons (`studio_pulse:ack`, `studio_pulse:snooze`) when `production_tick` reports zero candidates for >90 minutes. The buttons rendered, but no dispatcher branch matched their `callback_data` — pressing them silently no-oped.

## What landed

Three surgical edits, no refactors, per Karpathy P3:

1. `orchestrator/handlers_approvals.py` — new `elif cb_data.startswith("studio_pulse:")` branch in `handle_callback_query`, inserted before the `canon_restore`/`canon_dismiss` block. Loads pulse JSON, applies `ack` (zero `last_alert_sent`, re-arming) or `snooze` (set `snoozed_until = now + 6h`), writes back, calls `answer_callback_query` for the toast, then best-effort POSTs `editMessageText` so the buttons disappear and the chat shows the action that was taken. Honors `STUDIO_PULSE_STATE_PATH` env var so tests can point at a tmp file.
2. `orchestrator/studio_production_crew.py` — `studio_production_tick` now reads `snoozed_until` from pulse state and short-circuits the alert (with an `INFO` log line) while it is in the future. `_alert_silence` itself is unchanged.
3. `orchestrator/tests/test_studio_pulse_callbacks.py` — five regression tests: ack zeros `last_alert_sent` and edits the message, snooze sets `snoozed_until` ~6h out without touching `last_alert_sent`, snooze creates the state file when missing, watchdog skips alert while snoozed, watchdog re-alerts once snooze has expired.

## Verification

```
python -m pytest orchestrator/tests/test_studio_pulse_callbacks.py -v
# 5 passed in 0.41s
```

`test_studio_trend_scout.py` shows three pre-existing failures (`Ready` vs `Multiply`) on a clean `origin/main` checkout — unrelated to this branch.

## Followups

- Once VPS picks up the deploy (`git pull && docker compose restart orchestrator`), the next 0-candidates alert will have working buttons. No manual reset needed; existing `last_alert_sent: 1778808334` in `/app/workspace/studio_pipeline_pulse.json` will keep the cooldown intact, and the next ack/snooze press writes through.
- Consider promoting the `editMessageText` shim into `notifier.py` if a third callback handler ever needs it (gate_approve and canon_restore currently send a fresh confirmation message instead — pick one pattern across the codebase next time we touch this area).

## Reference memories

- `feedback_telegram_alerts_actionable_buttons_only.md` — buttons must be wired both ways
- `feedback_telegram_mcp_bun_cjs.md` — bot/notifier wiring details
