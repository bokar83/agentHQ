# Plan: Phase 1 — Hunter force_fresh fix (standalone)

**Date:** 2026-05-08
**Branch:** `feature/hunter-force-fresh` (off `main`)
**Author:** Claude → Codex
**Status:** Sankofa-passed (Phase 1 portion). Awaiting /karpathy.

## Why standalone

Originally bundled with email-queue rework. Sankofa surfaced disagreement on cap strategy (150 soft cap = invented number, draft-aging risk). Boubacar picked Path B = first-principles rewrite, written tomorrow.

Phase 1 = 12 lines, zero coupling to cap debate. Ships today regardless of Plan v2 direction.

## Goal

`harvest_until_target` hits 50/50 (SW=35, CW=15) without short-circuiting CW when ≥15 undrafted CW leads exist in DB.

## Files

- `signal_works/topup_cw_leads.py:85-99` — add `force_fresh` param.
- `signal_works/harvest_until_target.py:175` — pass `force_fresh=True`.

## Patch 1 — `topup_cw_leads.py`

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
    # ... rest unchanged
```

## Patch 2 — `harvest_until_target.py:175`

```python
saved = topup_cw_leads(minimum=needed, dry_run=dry_run, force_fresh=True)
```

## Test plan

1. Manual harvest re-run after deploy:
   ```bash
   ssh root@72.60.209.109 "docker exec orc-crewai bash -c 'cd /app && python -m signal_works.harvest_until_target --target 50 --sw-target 35 --cw-target 15'"
   ```
2. Expect Telegram alert: `✅ Daily harvest complete: 50/50 leads with email (SW=35, CW=15). Passes: N.`
3. If 50/50 holds for 3 successive days, wire to scheduler.py 06:00 MT cron in a separate small PR.

## Rollback

`git revert <commit>`. Default `force_fresh=False` keeps existing callers unchanged.

## Risks

| Risk | Likelihood | Mitigation |
|---|---|---|
| force_fresh causes Apollo credit burn | Low | Apollo daily cap enforced upstream; force_fresh just skips DB short-circuit. |
| Cron wire breaks scheduler | N/A | Out of scope. Deferred to post-validation PR. |

## Cron switch criteria (deferred to next PR)

- N=3 successive days of 50/50 manual runs.
- No Telegram stall alerts during those 3 days.
- Boubacar OK to cut over.

## Codex handoff

Branch: `feature/hunter-force-fresh`. Two-file edit. After /karpathy passes, Codex implements + ships [READY].
