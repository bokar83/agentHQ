# Handoff — Inbound Signal Metric Prototype (saved 2026-05-12, run Wed/Thu)

**Status:** QUEUED — Wed/Thu 2026-05-13 or 14 coding session
**Origin:** Sankofa Council 2026-05-12 (CW pivot session, `outputs/council/2026-05-12-18-37-24.html`) recommended an inbound signal metric. Implementation prompt below.
**Why queued, not run now:** Lead-strategy v4 session (this one) is the master roadmap close-out. The metric is the implementation of a council verdict from earlier today — it's a builder task, not a strategy task. Belongs in a separate session per failure mode #4 (Cognitive Overload from False Symmetry).

## Prompt for the Wed/Thu coding session

```
Proposal for next track after CW pivot lands — inbound signal metric prototype.

CONTEXT
The Sankofa Council that ran today on the CW automation question landed a strong
verdict (full HTML on VPS at /outputs/council/2026-05-12-18-37-24.html). Headline:
stop CW auto-harvest, switch to a permission-filtered target list. But the council
explicitly added a piece my own recommendation missed — an INBOUND SIGNAL METRIC.
This is the leading indicator that the new CW motion is actually working.

Council quote:
> "Simultaneously, instrument one inbound signal metric — unsolicited DMs or content
> engagement per week — so you have a leading indicator that CW legitimacy is
> compounding, not just that the list is growing."

Without this, the new CW list grows but we have no way to tell if the underlying
motion (warm referrals, content engagement, SW audit → CW upsell) is producing fit
demand. The list can grow purely because Boubacar adds names from podcasts every
week, and we'd never know that the inbound side is stagnant.

PROPOSED PROTOTYPE

Goal: one weekly number Boubacar can look at — "did inbound demand compound this
week vs last week?" — derived from real signals, no manual logging.

Three signal sources to instrument:

1. UNSOLICITED LINKEDIN DMs (the strongest signal)
   - Pull recent inbound DMs to Boubacar's LinkedIn profile
   - Filter out outbound thread replies, internal team chats, recruiter spam
   - Output: count + sender list per week
   - Implementation note: LinkedIn doesn't expose a clean API for this. Two paths:
     a. Manual log — Boubacar adds names to a Notion DB during the 09:00 CW Hour
        block. Lowest friction, lowest signal-loss.
     b. Email forwarding — LinkedIn sends DM notifications via email; we already
        have Gmail access; parse those.
   - Recommend starting with (a) for week 1, switch to (b) if it bottlenecks.

2. X (TWITTER) MENTIONS — confirmed today that r.jina.ai works for X reads
   (memory rule feedback_x_reader_jina_works.md added 2026-05-12).
   - Pull @boubacarbarry mentions + bookmarks + replies over the last 7 days via
     `WebFetch https://r.jina.ai/https://x.com/search?q=%40boubacarbarry&f=live`
   - Filter out retweets of own posts; count real conversations.
   - Output: count + permalink list per week.

3. SW AUDIT → CW UPSELL CONVERSIONS — leading indicator from the existing pipeline
   - Query sw_email_log for replies in last 7 days where the reply chain led to a
     CW touch (sequence_pipeline flip from sw → cw, or a manual lead.status='cw_lead'
     promotion).
   - Output: count + lead_email list per week.

DELIVERABLE

A weekly digest section that lands in the existing morning_digest on Mondays only
(or whenever the period rolls over). Format like the other digest sections — pipe-
delimited rows with Owner field. Example:

  📈 Inbound signal — week ending 2026-05-12 (3)
  - LinkedIn DMs (unsolicited) | Boubacar | 4 this week (3 last week)
  - X mentions (real conversations) | Boubacar | 2 this week (0 last week)
  - SW → CW conversions | Boubacar | 1 this week (0 last week)

  ⚠️ Inbound debt: 0 weeks below baseline (5 DMs + 2 mentions + 1 conversion)

WHERE TO HOOK IT IN

The digest builder is in orchestrator/scheduler.py:_run_morning_digest. The existing
4 sections (Yesterday handoffs / Roadmap next-actions / Open [READY] branches /
Owner debt) follow a clean pattern — each is a _collect_*() helper returning a list
of dicts, plus a _render_digest_section() formatter. Mirror that pattern. Add a
_collect_inbound_signal() helper that returns 3 rows (one per signal source).

Three sub-functions, each best-effort, single failure shouldn't break the digest
(existing pattern wraps each in try/except).

SCOPE GUARDRAILS

- This is a metric, not a CRM. Don't auto-log to Notion until the metric is proven
  useful. First 2 weeks = digest-only.
- Don't try to attribute LinkedIn DMs to specific content posts. That's a downstream
  question. First just count.
- X reads via r.jina.ai are rate-limited but not blocked. Cache for 6 hours.

EFFORT ESTIMATE

- LinkedIn manual-log path (a): 30 min — create Notion DB schema + _collect_inbound_signal_linkedin
  that queries it
- X r.jina.ai pull: 1 hour — _collect_inbound_signal_x with WebFetch + regex parse
- SW→CW conversion query: 30 min — single SQL against sw_email_log + leads tables
- Digest splice + render: 30 min — mirror existing _collect_yesterday_handoffs pattern
- Total: ~2.5 hours, single feature branch

KEEP OUT OF SCOPE

- Outreach automation off the inbound list (Council was clear: list is permission
  filter, not lead source; inbound is purely measurement)
- Multi-week trend graphs (digest is one row, not a dashboard)
- Sentiment analysis on the DMs/mentions (out of scope)

OUTPUT

When done, PR titled "feat(digest): inbound signal metric prototype". Boubacar
reviews + decides whether to keep, drop, or evolve after 2 weeks of real data.

Branch suggestion: feat/digest-inbound-signal-metric. Fresh from main.
```

## Cross-references

- Master strategy: `docs/strategy/lead-strategy-2026-05-12.html` (failure mode #2 — No Ritualized First Win — this metric feeds it)
- Memory: `project_lead_strategy_2026-05-12.md` (open follow-up #1)
- Source council: `outputs/council/2026-05-12-18-37-24.html` (CW pivot premortem)
