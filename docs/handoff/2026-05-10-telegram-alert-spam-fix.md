# Session Handoff - Telegram Alert Spam Fix - 2026-05-10

## TL;DR
Diagnosed and fixed Telegram notification spam. Root cause: session_logger.py fired on every Claude Code session close — including zero-turn aborted sessions. Added turns>0 guard and 5-min per-project cooldown. Drive watch empty-scan also silenced. Audited auto_publisher and griot_scheduler — both already self-deduplicate via state machine, no changes needed. All changes deployed to VPS.

## What was built / changed

- `scripts/session_logger.py` — added `turns > 0` guard before Telegram send; added 5-min per-project cooldown sentinel at `/tmp/session_logger_last_alert.txt`
- `orchestrator/scheduler.py:1248` — removed "Scan complete -- no new files found in Drive inbox." notification (empty scan = not actionable)
- `orchestrator/handlers_commands.py` — `_cmd_shipped` and `_cmd_milestones` added by another session; pulled into same commit via pre-commit hook scanning all modified files

## Decisions made

- **auto_publisher.py is clean** — `_alert_failed` / `_alert_posted` always called after state flip to `PublishFailed`/`Posted`. Row gone from next fetch. No dedup sentinel needed.
- **griot_scheduler.py is clean** — fetch query filters `scheduled_date IS NULL`. `_mark_scheduled` writes the date. Items fire exactly once. No fix needed.
- Pattern: before writing dedup sentinels, read the fetch query filter. State-machine code self-deduplicates.

## What is NOT done

Nothing open. This was a self-contained fix session.

## Open questions

None.

## Next session must start here

No specific continuation needed. Monitor Telegram over next 24h to confirm zero-turn spam is gone.

If spam returns: check `output/session_log.jsonl` — are sessions with turns=0 still appearing? If yes, the hook may not be picking up the updated script (VPS entrypoint sync issue).

## Files changed this session

- `scripts/session_logger.py`
- `orchestrator/scheduler.py`
- `orchestrator/handlers_commands.py` (co-committed, from another session)
