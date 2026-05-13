# Constraints AI capture → 3-email follow-up: integration plan

**Decision:** **VPS-only. Decommission n8n from this pipeline.**

**Date:** 2026-05-12
**Owner:** Boubacar
**Author:** Claude Code (session-collision-fix branch)
**Status:** Plan, not yet implemented

---

## TL;DR

The site's "save your diagnosis" form is currently broken. It POSTs to a
non-existent n8n webhook (`POST .../catalystworks-constraints-ai/capture` →
404 `webhook not registered`). The frontend swallows the error and shows
success. Every capture submission since the 2026-05-11 deploy has been
silently discarded.

The n8n diagnostic endpoint (root `POST .../catalystworks-constraints-ai`)
works correctly and returns valid JSON. Only the `/capture` sub-route is
absent on n8n. Supabase `diagnostic_captures` has 0 rows as of 2026-05-11
not because traffic is zero, but because the wire is cut.

**Recommendation:** rebuild the capture path through the existing Cloudflare
Worker (`_worker.js` already has `handleCapture` written but undeployed) AND
have the Worker double-write to agentsHQ `/inbound-lead` so the follow-up
sequence triggers. Retire the n8n LLM proxy at the same time by deploying
the Worker's LLM-call path (also already written in `_worker.js`).

**Net effect:** one fewer SaaS (n8n), one less authentication surface, code
already written and tested. Same edge-cached latency as today.

---

## Current state of the wire (2026-05-12)

```
Browser
  │  POST https://n8n.srv1040886.hstgr.cloud/webhook/catalystworks-constraints-ai
  │  body: { pain: "..." }
  ▼
n8n (self-hosted on Hostinger srv1040886)
  │  OpenRouter call (gpt-4o-mini → Constraints AI prompt)
  ▼
JSON response
  └── frontend renders diagnosis ✅


Browser
  │  POST https://n8n.srv1040886.hstgr.cloud/webhook/catalystworks-constraints-ai/capture
  │  body: { email, pain, result, source }
  ▼
n8n → 404 "webhook POST catalystworks-constraints-ai/capture is not registered" ❌
  │
  ▼
Frontend swallow (index.html:2222) — UI shows success regardless
Captured leads: lost.
```

`diagnostic_captures` row count today: **0**.

## What I'd build instead (VPS-only path)

```
Browser
  │  POST https://catalystworks-diagnostic.<worker-subdomain>.workers.dev
  │  body: { pain: "..." }
  ▼
Cloudflare Worker (_worker.js, deployed)
  │  OpenRouter call (same Constraints AI prompt — code already in _worker.js)
  │  Logs to Supabase diagnostic_submissions (already in _worker.js)
  ▼
JSON response → browser renders ✅

────────────────────────────────────────────

Browser
  │  POST <same-worker>/capture
  │  body: { email, pain, result, source: "site_demo_capture" }
  ▼
Cloudflare Worker (handleCapture, already in _worker.js:299-346)
  │  ├─→ Supabase INSERT diagnostic_captures (row exists)
  │  └─→ agentsHQ POST /inbound-lead (NEW: 15 lines added to handleCapture)
  ▼
agentsHQ FastAPI orchestrator/app.py:796 (existing endpoint)
  │  background task: run_inbound_lead(payload)
  │    ├─ idempotency check on email
  │    ├─ INSERT into leads with sequence_pipeline='constraints_ai'
  │    │  and sequence_touch=0
  │    └─ first touch will be picked up by sequence_engine within 90 min
  ▼
sequence_engine.run_sequence("constraints_ai")
  │  TOUCH_DAYS_CONSTRAINTS_AI = {1: 0, 2: 2, 3: 4}
  │  T1 fires same-day (Day 0)
  │  T2 at Day 2
  │  T3 at Day 4
  ▼
Gmail Drafts (auto_send=False until Boubacar flips AUTO_SEND_CONSTRAINTS_AI)
```

Everything to the right of the Worker already exists. The Worker code is
already written. Net work: deploy `_worker.js` to Cloudflare Workers, point
the front-end at the worker URL instead of n8n, and add 15 lines to
`handleCapture` for the agentsHQ double-write.

## Decision matrix: n8n vs VPS-only

| Dimension | Keep n8n | VPS-only (recommended) |
|---|---|---|
| Setup effort | Fix broken webhook + add follow-up logic in n8n workflow | Deploy existing `_worker.js`, add 15 lines for double-write |
| Recurring cost | Hostinger n8n license (~$20-50/mo for self-hosted, plus VPS slice) | $0 — Cloudflare Workers free tier covers this trivially |
| Failure surfaces | Browser → Cloudflare DNS → n8n VPS → OpenRouter → Supabase → agentsHQ VPS (5 hops, 4 SaaS) | Browser → Cloudflare Worker → Supabase → agentsHQ VPS (3 hops, 2 SaaS) |
| Authentication surfaces | n8n login + workflow versioning + OpenRouter key in n8n + Supabase service key in n8n + agentsHQ API key in n8n | OpenRouter key + Supabase service key + agentsHQ API key in `wrangler secret` (one place, encrypted at rest, deploy-versioned) |
| Visibility | n8n executions tab — has UI, requires login | Cloudflare Workers logs (`wrangler tail`) — terminal, lower friction |
| Versioning | Manual workflow export to JSON, gitignored by default | `_worker.js` already in git, every change reviewed |
| Latency | Cold-start n8n container 2-8s for first request after idle | Cloudflare edge <100ms |
| Failure mode for the capture path today | Silently 404s, drops every lead | Code-reviewed, tested, single-step deploy |

Only honest argument for keeping n8n: **visual workflow UI lets Boubacar
edit the flow without touching code.** Worth $50/mo + 2 extra failure
surfaces if Boubacar wants self-serve. Otherwise, code wins.

## Webhook payload contract (canonical)

The Worker's POST to `/inbound-lead` uses agentsHQ's existing
`InboundPayload` schema (orchestrator/app.py). To stay compatible without
schema changes, the field mapping is:

```json
{
  "email": "<captured email>",
  "source": "constraints_ai_capture",
  "booking_id": null,
  "name": null,
  "company": null,
  "raw_company_url": null,
  "meeting_time": null,
  "extra": {
    "pain_text": "<what they typed into the demo, ≤1500 chars>",
    "response_constraint": "<diagnosis output>",
    "response_action": "<diagnosis output>",
    "user_agent": "<ua>",
    "geo_country": "<cf-ipcountry>",
    "captured_at": "<ISO8601 UTC>"
  }
}
```

Two-row write strategy:
1. Cloudflare Worker INSERTs into Supabase `diagnostic_captures` (rich
   capture row, fast path, fail-open if agentsHQ unreachable).
2. Cloudflare Worker POSTs `/inbound-lead` with the payload above (triggers
   3-email sequence, idempotency-safe).

The `extra` blob carries Constraints-AI-specific context that
`templates/email/constraints_ai_t{1,2,3}.py` need (pain_text,
response_constraint, response_action). The `run_inbound_lead` runner is
modified to copy these into the `leads` row so sequence_engine's
`_render(lead)` step finds them.

## Required changes (ordered, smallest first)

### Change 1 — Cloudflare Worker double-write (≤30 min)

File: `output/websites/catalystworks-site/_worker.js`, function
`handleCapture` (already exists at line 299).

After the existing Supabase INSERT, add:

```javascript
// Trigger agentsHQ inbound-lead sequence (constraints_ai pipeline)
if (env.AGENTSHQ_INBOUND_URL && env.AGENTSHQ_API_KEY) {
  try {
    await fetch(env.AGENTSHQ_INBOUND_URL, {
      method: 'POST',
      headers: {
        'content-type': 'application/json',
        'x-api-key': env.AGENTSHQ_API_KEY,
      },
      body: JSON.stringify({
        email,
        source: 'constraints_ai_capture',
        extra: {
          pain_text: (body.pain || '').slice(0, 1500),
          response_constraint: body.result?.constraint || null,
          response_action: body.result?.action || null,
          user_agent: userAgent,
          geo_country: country,
          captured_at: new Date().toISOString(),
        },
      }),
    });
  } catch (e) {
    console.error('inbound-lead notify failed:', e);
    // Capture row already saved to Supabase, do not propagate this error.
  }
}
```

Add `wrangler secret put AGENTSHQ_INBOUND_URL` (value:
`https://agentshq.boubacarbarry.com/inbound-lead`) and
`AGENTSHQ_API_KEY` (existing agentsHQ inbound key).

### Change 2 — `skills/inbound_lead/runner.py` constraints_ai branch (≤45 min)

When `payload.source == 'constraints_ai_capture'`:
1. Skip the Apollo/research step (warm inbound — they self-identified).
2. INSERT into `leads` with `sequence_pipeline = 'constraints_ai'`,
   `sequence_touch = 0`.
3. Copy `extra.pain_text`, `extra.response_constraint`,
   `extra.response_action` into `leads` columns (need migration to add
   `pain_text`, `response_constraint`, `response_action` columns).
4. Set `first_name_confidence = 'low'` (capture is email-only by default).

### Change 3 — Migration `migrations/009_constraints_ai_capture_fields.sql`

```sql
ALTER TABLE leads
  ADD COLUMN IF NOT EXISTS pain_text TEXT,
  ADD COLUMN IF NOT EXISTS response_constraint TEXT,
  ADD COLUMN IF NOT EXISTS response_action TEXT;
```

Apply via `migrate.py` on orc-postgres, idempotent.

### Change 4 — Frontend cutover

File: `output/websites/catalystworks-site/index.html:2091`

```javascript
const WORKER_URL = 'https://catalystworks-diagnostic.<sub>.workers.dev';
```

(One-line change after worker is deployed.)

### Change 5 — Decommission n8n workflow

After 7 days of clean capture flow:
1. Disable `catalystworks-constraints-ai` workflow in n8n.
2. Cancel n8n Hostinger plan if no other workflows depend on it.

## Risk + rollback

**Risk 1:** Cloudflare Workers free tier limits (100k requests/day). At
current traffic this is 100x headroom. Mitigation: monitor `wrangler tail`
weekly for first month.

**Risk 2:** agentsHQ `/inbound-lead` rejects payload schema. Mitigation:
Worker logs failure but does NOT propagate to user. Capture is durable in
Supabase; follow-up sequence is best-effort. A scheduled job
(`scripts/replay_failed_captures.py`, future M-something) can reconcile
Supabase rows that lack a matching `leads` entry.

**Risk 3:** Existing `n8n.../webhook/catalystworks-constraints-ai` (the
LLM-diagnostic root) is in production today and working. If the Worker
deploy breaks the diagnostic AS WELL as fixing capture, the front-end loses
both. Mitigation: deploy Worker first, A/B with feature flag
(`WORKER_URL_BETA`) in the front-end, soak for 48h, then cut over.

**Rollback:** revert `output/websites/catalystworks-site/index.html` to
the n8n URL. Diagnostic returns to working state immediately. Capture
returns to silently-broken state (no worse than today).

## Verification (post-deploy)

1. `curl -X POST <worker>/capture -d '{"email":"PROBE@example.invalid","pain":"test","result":{"constraint":"x","action":"y"},"source":"site_demo_capture"}'`
   → 200 `{ok:true,message:"captured"}`.
2. `psql -d ... -c "SELECT COUNT(*) FROM diagnostic_captures WHERE email='PROBE@example.invalid'"`
   → 1.
3. `psql -d ... -c "SELECT * FROM leads WHERE email='PROBE@example.invalid'"`
   → 1 row with `sequence_pipeline='constraints_ai'`, `sequence_touch=0`.
4. Wait 1h, run `python -m skills.outreach.sequence_engine --pipeline constraints_ai --dry-run`.
   → reports 1 due lead for T1.
5. Delete the probe row from both tables before going live.

## Open question

**Q: Should n8n be retired entirely from agentsHQ, or just from this
pipeline?** AGENTS.md line 59 still has n8n in the entry diagram. Other
pipelines (boubacarbarry.com form, Calendly bookings) currently flow
through n8n. This document only argues against n8n for the
Constraints AI capture path. The broader question (does n8n stay in
the architecture at all?) is out of scope here and worth its own Council
session.

---

**Next step from Boubacar:** approve this plan, or ask for changes. No
code shipped yet — design only.
