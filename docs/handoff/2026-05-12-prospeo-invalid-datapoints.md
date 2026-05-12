# Handoff Stub — Prospeo INVALID_DATAPOINTS Silent Poisoning of SW Chain

**Date:** 2026-05-12
**Status:** OPEN — separate session required
**Priority:** Medium (silent quality killer, not infra-down)
**Owner:** dev session, Wed/Thu before 2026-05-28

## What this is

Prospeo enrichment is silently returning `INVALID_DATAPOINTS` errors that poison the SW lead pipeline. Identified by Sankofa Council 2026-05-12 as one of the silent failure chains. Not yet ticketed.

## Why it matters

- SW chain depends on Prospeo for enrichment after Hunter handoff
- Silent failures mean leads with bad data still get queued for send
- Likely contributing to the **9.4% delivery failure rate** discovered today via the canonical email_events ledger backfill
- Sender reputation damage compounds: 47 of 500 sends bouncing → Gmail throttles → cold lane dies before strategy lane lands

## What to investigate

1. `signal_works/sequence_engine.py` + `signal_works/topup_leads.py` — find every Prospeo API call
2. Search Prospeo response payloads for `INVALID_DATAPOINTS` error code
3. Determine: how many leads in `leads` table were enriched with INVALID_DATAPOINTS responses but still got queued
4. Cross-reference with the 44 hard-bounced sends in `email_events` table (orc-postgres) — are they correlated with Prospeo-flagged leads?

## What to fix

- Reject Prospeo INVALID_DATAPOINTS responses at enrichment time, do not queue for send
- Surface count in morning digest (silent failures → visible failures)
- Add Hunter re-verification as a hard gate before send queue, regardless of Prospeo state

## Hard deadline

Before 2026-05-28 (Apollo Free-tier cutover). If Apollo SW chain breaks AND Prospeo continues poisoning AND list hygiene gate not built → cold lane dies completely.

## Cross-references

- Master strategy: `docs/strategy/lead-strategy-2026-05-12.html` (M8 — List Hygiene Gate)
- Memory: `project_lead_strategy_2026-05-12.md`
- Council premortem: `outputs/council/2026-05-12-20-20-24.html` (failure mode #8 — Sender Reputation Cliff)
- Email events ledger: `migrations/009_email_events.sql`, branch `feat/email-events-canonical-ledger`
