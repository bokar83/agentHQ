# Plan v2 Frame: Email Queue First-Principles Rewrite

**Date:** 2026-05-09 (write tomorrow)
**Branch:** TBD `feat/email-queue-v2`
**Author:** Claude → Codex
**Status:** STUB. Full plan written tomorrow. Reviewed by /sankofa + /karpathy before code.

## Why this exists separately from v1

Sankofa Council on v1 (2026-05-08) surfaced the 150-soft-cap as a band-aid that introduces draft-aging debt. First-Principles voice argued caps are an engineering smell — the right primitive is send-rate-derived flow control, not invented per-touch ceilings. Boubacar picked Path B (this rewrite) over Path A (ship v1 with patches).

## Locked design decisions (going into Plan v2 write)

1. **No draft cap.** Drafts are created on-demand at send time, not pre-staged.
2. **Send-rate-derived throughput.** Daily budget = `send_scheduler.py` per-pipeline caps (35 SW + 15 CW + 15 Studio = 65/day max sends). Drafter pulls exactly available capacity from due-queue, oldest-overdue first, drafts + sends in same window.
3. **Replied = Gmail-fetched at draft time, 1h cache.** No `replied` column added to `leads`. Skip lead if Gmail shows inbound from that address since `last_contacted_at`.
4. **Reply classification = Phase 3.** Cheap LLM call (Haiku) tags reply: `interested` / `objection` / `ooo` / `unsubscribe` → Telegram alert (interested) + CRM tag (objection) + defer 14d (ooo) + opt_out=true (unsubscribe). ~50 lines added.
5. **4h cron, not 06:00 only.** Drafter runs every 4h (06:00, 10:00, 14:00, 18:00 MT). Cycle compresses 25%.
6. **Multilingual OOO regex.** EN + ES + FR baseline.
7. **Hard 90s budget on reply scan.** Never blocks drafting. Fire-and-forget pattern.

## Goals (success criteria)

- **G1.** Coverage: P(any due lead gets touched within their cadence window) ≥ 95%.
- **G2.** Throughput: Daily sends ≤ send_scheduler caps (35 SW + 15 CW + 15 Studio = 65/day).
- **G3.** Hygiene: Zero T2-T5 sends to leads who have replied (verified via Gmail at draft time).
- **G4.** Latency: Lead due at Day 3 09:00 MT gets touched by 14:00 MT same day (next 4h slot).
- **G5.** Visibility: Telegram digest shows touched/skipped-for-reply/skipped-for-OOO/bounce per pipeline per slot.

## Out of scope for v2

- New paid vendors.
- Studio template content changes (separate `feat/email-signature-polish` branch handles).
- Site first-name scrub (separate session).

## Phase split

- **Phase 2a:** Drafter rewrite (no caps, on-demand, send-rate-derived). Ship Fri-Sat.
- **Phase 2b:** Reply scanner (Gmail-as-truth, 1h cache, multilingual OOO, fire-and-forget). Same branch.
- **Phase 3:** Reply classification + Telegram routing. Following week, separate branch.

## Open questions for tomorrow's write

1. Where is `send_scheduler.py` exactly? (Phase 2 needs to coordinate with it cleanly.)
2. Existing 06:00 MT cron entry path? (Need to extend to 4 slots, not replace.)
3. Reply cache TTL = 1h confirmed? Or longer (e.g., 4h matching cron cycle)?
4. Studio pipeline: is it part of this rewrite or held? (Sankofa plan implied yes, confirm with Boubacar.)
5. Phase 3 LLM choice: Haiku 4.5 or cheaper? Cost per classification?
6. Telegram routing: which chat for "interested" alert? Same as morning digest or separate "hot lead" channel?

## Action

Write full Plan v2 tomorrow 2026-05-09 morning. Run /sankofa + /karpathy. Codex implements Fri-Sat 2026-05-09 / 2026-05-10.
