# Codex prompt — Phase 1 Hunter `force_fresh`

You are implementing a surgical 2-file fix in the agentsHQ repo (`d:\Ai_Sandbox\agentsHQ`).

## Goal

`harvest_until_target` must hit 50/50 (SW=35, CW=15) without short-circuiting CW when the DB already has ≥15 undrafted CW leads.

Today CW pull was skipped (41 existing undrafted leads triggered an early-return), causing harvest to stall at 31/50. Fix is to add a `force_fresh` parameter that bypasses the short-circuit when called from the daily-target runner.

## Context

- Plan: `docs/plans/2026-05-08-phase1-hunter-force-fresh.md`
- Sankofa + Karpathy: PASS / SHIP
- Originating handoff: `docs/handoff/2026-05-07-enrichment-rebuild-and-thesis-launch.md` lines 82-95

## Branch

`feature/hunter-force-fresh` off `main`.

## Edits

### 1. `signal_works/topup_cw_leads.py:85-99`

Add `force_fresh: bool = False` to the signature. Skip the `ready >= minimum` early-return when `force_fresh=True`. Keep all other logic identical.

```python
def topup_cw_leads(minimum: int = DAILY_MINIMUM, dry_run: bool = False, force_fresh: bool = False) -> int:
    """Hybrid CW lead topup: 5 fresh from Apollo (widened ICP) + 5 resends.

    Args:
        minimum: target leads to ensure ready in DB.
        dry_run: walk pipeline without saving.
        force_fresh: skip the ready>=minimum short-circuit. Used by
            harvest_until_target when we want guaranteed daily injection
            even if undrafted residue exists.
    """
    conn = get_crm_connection()
    try:
        ensure_leads_columns(conn)
    except Exception as e:
        logger.warning(f"topup_cw_leads: ensure_leads_columns failed: {e}")
    ready = _count_ready_cw_leads(conn)
    logger.info(f"CW topup: {ready} ready leads (target: {minimum}, force_fresh={force_fresh})")
    if ready >= minimum and not force_fresh:
        return ready
    # ... rest of function UNCHANGED ...
```

### 2. `signal_works/harvest_until_target.py:175`

Pass `force_fresh=True`:

```python
saved = topup_cw_leads(minimum=needed, dry_run=dry_run, force_fresh=True)
```

## Constraints

- Default `force_fresh=False` preserves all existing callers.
- Do not refactor adjacent code (`harvest_leads`, `_save_cw_lead`, `_count_ready_cw_leads`, etc.).
- Do not bundle the cron switch (`scheduler.py`) into this PR — that's a separate PR after 3 days of stable manual runs.
- No new tests required (test plan = manual harvest re-run on VPS).

## Verification

After edits, run pre-commit hooks. They should pass clean. Do not skip with `--no-verify`.

The post-deploy manual test (Boubacar runs, not Codex):

```bash
ssh root@72.60.209.109 "docker exec orc-crewai bash -c 'cd /app && python -m signal_works.harvest_until_target --target 50 --sw-target 35 --cw-target 15'"
```

Expected Telegram alert: `✅ Daily harvest complete: 50/50 leads with email (SW=35, CW=15). Passes: N.`

## Coordination protocol (REQUIRED)

This is agentsHQ. Per `CLAUDE.md` Hard Rule:

```python
from skills.coordination import claim, complete

branch_task = claim('branch:feature/hunter-force-fresh', '<your-agent-id>', ttl_seconds=7200)
# If None: branch already claimed. Stop.

# Before editing each file:
file_task1 = claim('file:signal_works/topup_cw_leads.py', '<your-agent-id>', ttl_seconds=1800)
# edit, commit
complete(file_task1['id'])

file_task2 = claim('file:signal_works/harvest_until_target.py', '<your-agent-id>', ttl_seconds=1800)
# edit, commit
complete(file_task2['id'])

complete(branch_task['id'])
```

## Final commit + push

Final commit message MUST contain `[READY]` so the Gate picks it up:

```
git commit -m "feat(harvest): add force_fresh to topup_cw_leads, bypass DB short-circuit [READY]"
git push origin feature/hunter-force-fresh
```

Gate watches GitHub every 60s. After push, Codex is done. No Telegram, no manual signal.

## Output

Reply with: branch pushed + final commit hash + the diff for both files.
