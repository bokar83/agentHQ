# Email Data Wiring Audit — 2026-05-12

**Auditor:** email-wiring agent (sandbox/parent dispatch)
**Branch:** `feat/email-events-canonical-ledger`
**Scope:** Reconcile "how many emails were sent across all 3 brands (CW, SW, GW) all-time" + per-email visibility (opened / replied / bounced / clicked).

## TL;DR (ground truth)

| Brand | Real sent (Gmail) | Old logger (`sw_email_log`) | Replies (Gmail) | Bounces (Gmail) |
|-------|------------------:|----------------------------:|----------------:|----------------:|
| **CW** (boubacar@catalystworks.consulting) | **446 cold** / 482 total | 15 sent + 67 drafted | **3** | **44** |
| **SW** (same OAuth, no separate inbox) | included in CW total | 35 sent + 47 drafted | (shared thread) | (shared thread) |
| **GW** (bokar83@gmail.com personal) | indistinguishable from personal mail (12 869 lifetime) | — | — | — |

**Reply rate, CW account, cold outreach:** 3 / 446 = **0.67%** (n=446 — solid sample).
**Bounce rate, CW account, lifetime:** 44 / 482 = **9.1%**.

Ground-truth source: `gws-oauth-credentials-cw.json` queried directly against `https://gmail.googleapis.com/gmail/v1/users/me/messages` with paginated counts (not `resultSizeEstimate`).

## What we believed vs what we have

- **Boubacar's belief:** "100+ CW + 100+ SW emails sent historically."
- **Reality:** 446 cold-outreach messages, all sent from `boubacar@catalystworks.consulting` via the cw OAuth. The brand split (CW vs SW) is **lost at the Gmail layer** — both share one inbox + one OAuth identity. Inside `sw_email_log`, the `pipeline` column tracks which template ran, but only from 2026-05-11 onward (last 2 days, 164 rows).
- **The historical 400+ sends (April + May 1-10) have no row in any DB table.** They exist only as Gmail Sent messages.

## Why the existing tables are wrong

| Table | Rows | Problem |
|-------|-----:|---------|
| `leads` | 0 | Empty. Used to hold the source list; truncated or never repopulated after Apollo refresh. Lead-resolution joins fail. |
| `sw_email_log` | 164 | Earliest row 2026-05-11. Status enum only `drafted` / `sent` / `failed` / `dry-run`. No `opened` / `replied` / `bounced` / `clicked` events ever recorded. Missing all historical sends pre-2026-05-11. |
| `email_jobs` | 2 | One-off from 2026-04-27. Never written by current pipeline. |
| `lead_interactions` | 0 | Written by `_mark_sent()` BUT requires `leads.id` FK — and `leads` is empty, so every insert silently no-ops (lead_id orphan). |
| `apollo_revealed` | 0 | Empty. |

## Send-call site inventory (every place email is sent)

| File:Line | Function | Target | Logs to `sw_email_log`? |
|-----------|----------|--------|:----------------------:|
| `skills/outreach/sequence_engine.py:329` | `_create_draft(auto_send=True)` | `users/me/messages/send` | yes (via `_mark_sent`→`_log_to_orc_postgres`) — but only on draft creation, not draft-then-send |
| `skills/outreach/sequence_engine.py:336` | `_create_draft(auto_send=False)` | `users/me/drafts` | yes (status='drafted') |
| `signal_works/send_scheduler.py:152` | `_send_draft` | `users/me/drafts/send` | **NO — gap.** Sends a draft, never inserts a 'sent' row. |
| `signal_works/gmail_draft.py:68` | `create_draft` | `users/me/drafts` | NO — called by ad-hoc code, no logger |
| `orchestrator/tools.py:844` | `GWSGmailSendHTMLMeTool` (`gmail_send_html_me`) | `users/me/messages/send` | NO — internal notification path, not outreach |
| `orchestrator/tools.py:674` | `GWSGmailCreateDraftTool` (`gmail_create_draft`) | `users/me/drafts` | NO |

**The send_scheduler gap is the largest data leak.** `sequence_engine` writes a `drafted` row, `send_scheduler` later promotes the draft to a real send, but no row flips to `sent`. The 164 `sw_email_log` rows are therefore not a sent-log — they are a draft-creation-log.

## Migrations: what shipped, what's pending

Migration directory layout (two separate dirs — historical baggage):

- `migrations/` (top-level): 006 newsletter, 007 sw_email_log, 008 pipeline_metrics — all applied on VPS
- `orchestrator/migrations/`: 0001 video_jobs, 001 llm_calls, … 008 email_jobs — all applied on VPS
- Next free slot in top-level `migrations/`: **009**
- Next free slot in `orchestrator/migrations/`: **009** (same number, different dir)

This migration ships as `migrations/009_email_events.sql` (top-level — sw_email_log is also there, keep them co-located).

## Notion CRM check (severed 2026-05-07)

`feedback_notion_pagination_bug.md` confirms Notion content board was severed. The historical CRM Notion DB still exists but is not re-wired and not authoritative. Per task brief: **do NOT re-wire Notion**. Historical sends are recovered from Gmail Sent directly.

## Gmail OAuth identities

| File | Account | Sent count (lifetime) | Used by |
|------|---------|----------------------:|---------|
| `secrets/gws-oauth-credentials-cw.json` | boubacar@catalystworks.consulting | 482 | All outreach (CW + SW) |
| `secrets/gws-oauth-credentials.json` | bokar83@gmail.com | 12 869 (personal mail) | Internal notifications (`_gws_request` default) |

`signal@catalystworks.consulting` is an alias (mail-forward), not a send-as identity (per `feedback_signal_at_catalystworks_not_send_alias.md`). All outbound to prospects comes out of `boubacar@catalystworks.consulting`.

## Top 3 surprises

1. **Brand split has never existed at the wire level.** CW and SW are template-only labels; Gmail sees one sender. Any "per-brand" count must come from a downstream log (`pipeline` column in `sw_email_log` or new `email_events.brand`), not from From-address.
2. **send_scheduler never logs sent events.** All "sent" rows in `sw_email_log` come from `sequence_engine` running in auto-send mode (15 + 35 = 50 rows). The other 372 cold-outreach sends from the last 14 days went out via send_scheduler → no DB trail.
3. **Reply rate is 0.67% (3 / 446), bounce rate is 9.1% (44 / 482).** Bounce rate is materially above the 2% kill-switch threshold in `send_scheduler._bounce_rate_kill_switch` — the switch never tripped because it queries `sw_email_log` (50 rows window) instead of Gmail (real bounces).

## Phase 2 design — see migration

Proposed schema: `migrations/009_email_events.sql` (in this branch). Append-only, brand+direction+event_type immutable ledger. `v_email_funnel` view answers the dashboard question in one query.

## Phase 3 ship plan (in this branch)

1. `migrations/009_email_events.sql` — schema
2. `scripts/backfill_email_events.py` — backfill from sw_email_log + Gmail Sent
3. Wire `skills/outreach/sequence_engine.py::_mark_sent` and `signal_works/send_scheduler.py::_send_draft` to also write `email_events`
4. `scripts/sync_replies_from_gmail.py` — 15-min cron to detect replies
5. Bounces: classify `from:mailer-daemon` Gmail messages → `email_events.event_type='bounced'`
6. Opens/clicks: **explicit gap, deferred**. Standard Gmail API exposes no open tracking. A pixel-CDN is a separate decision.

## Phase 4 validation — see follow-up audit

`docs/audits/email-data-wiring-2026-05-12-validation.md` (written post-ship after backfill runs on VPS).
