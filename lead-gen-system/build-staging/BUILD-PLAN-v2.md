# geolisted.co AI Visibility Score: Build Plan v2 (post pre-stage)

**Date:** 2026-04-30 late-night pre-stage. Build window: Friday 2026-05-01, 8am MT.
**Status:** PRE-STAGED. No code committed. No deploys. No live changes.
**Authoritative supersede of:** the verbal plan in chat earlier this session.

---

## Decisions locked (operator confirmation 2026-04-30)

1. **A/A/A on the three forks:**
   - New `/score-request` route (NOT reuse `/inbound-lead`).
   - Sync webhook with response node (browser holds connection 30-60s).
   - Build `gmail_draft.send_message()` gated behind `SCORE_AUTO_SEND` env var (default false = drafts; flip to true after first 5 verified manually).

2. **Email render: extend `signal_works/email_builder.py`, do NOT create a new file.** Add `render_inbound_report_html(lead)`. Karpathy WARN closed.

3. **Defer build execution to Friday 2026-05-01, 8am MT** per Sankofa Council Pass 2.

---

## Architecture (final)

```
Visitor on geolisted.co
   │
   ▼
[Submit form: name, business, email, city, niche]
   │
   ▼
POST https://n8n.srv1040886.hstgr.cloud/webhook/geolisted-score
   │  (sync mode, response node returns when last node finishes)
   ▼
n8n workflow "geolisted.co Score Request":
   1. Webhook (POST, sync response mode)
   2. Set node: shape payload as ScoreRequestPayload
   3. HTTP Request: POST http://orc-crewai:8000/score-request
      headers: X-API-Key (Header Auth credential, existing)
   4. Respond to Webhook: pass through {score, breakdown, quick_wins}
   │
   ▼
agentsHQ FastAPI POST /score-request (NEW route, X-API-Key gated):
   1. Validate ScoreRequestPayload (NEW pydantic schema)
   2. Call signal_works.ai_scorer.score_business(name, city, niche, website?)
      → returns {score, breakdown, quick_wins} in 30-60s
   3. Write Supabase leads row (source='geolisted.co - Score Request')
   4. Render HTML report via email_builder.render_inbound_report_html(lead)
   5. If SCORE_AUTO_SEND=true → gmail_draft.send_message(); else create_draft()
   6. Return {score, breakdown, quick_wins} to n8n
   │
   ▼
n8n returns score JSON back through open connection to browser
   │
   ▼
Browser renders score on-screen. Full report email lands in inbox in parallel.
```

---

## Files touched (4 production files + 1 new file + 1 n8n workflow)

| # | File | Type | Purpose | Owner | LOC est |
|---|---|---|---|---|---|
| 1 | `skills/score_request/__init__.py` | NEW | Module init | I author | 1 |
| 2 | `skills/score_request/schema.py` | NEW | Pydantic ScoreRequestPayload, ScoreResult | I author | 30 |
| 3 | `skills/score_request/runner.py` | NEW | Orchestrate scorer + supabase + email | I author | 80 |
| 4 | `signal_works/email_builder.py` | EXTEND | Add `render_inbound_report_html()` | I author | +40 |
| 5 | `signal_works/gmail_draft.py` | EXTEND | Add `send_message()` companion to `create_draft()` | I author | +30 |
| 6 | `orchestrator/app.py` | EXTEND | Add `POST /score-request` route | I author | +30 |
| 7 | n8n workflow `geolisted.co Score Request` | NEW | Webhook → shape → /score-request → response | agentsHQ via MCP | n/a |
| 8 | `bokar83/geolisted-site/index.html` | EDIT | Form action + button text + scanner-card JS + result rendering | I author | ~+100 |

**Total LOC: ~310 added, ~5 modified.**

**Why I author all the Python and not agentsHQ:** agentsHQ does not have a "self-author Python and redeploy the orchestrator container" crew. The boubacar-skill-creator skill writes SKILL.md files, not orchestrator routes. agentsHQ DOES have the n8n MCP, so the n8n workflow is the only piece agentsHQ creates. Per the rule from the operator: "Step in for things they cannot do." This is one of those.

---

## Execution order (Friday 2026-05-01 8am MT)

1. **Verify warm-DM outcomes first.** Read `lead-gen-system/sent/2026-04-30-warm-reactivation-batch-1/outcomes.md`. If 0 replies, halt the build and pivot per Sankofa.
2. Branch `feature/ai-score-flow` off main.
3. Author files 1-6 (Python). Run `pytest -q` if any test exists for inbound_lead schema (guards against regressions).
4. Test locally:
   - `python -c "from signal_works.ai_scorer import score_business; print(score_business('Bright Smiles', 'Provo', 'pediatric dentist'))"` → confirm score returns in 30-60s.
   - `python -c "from signal_works.email_builder import render_inbound_report_html; ..."` → confirm HTML renders.
   - Run `gmail_draft.send_message()` to my own email with a test payload. Verify it lands as a real send (not draft).
5. Commit + push to feature branch. Open PR.
6. Deploy to VPS via `scripts/orc_rebuild.sh` (per memory's `feedback_use_orc_rebuild_wrapper.md`). Set `SCORE_AUTO_SEND=false` in VPS .env.
7. Hit the new `/score-request` endpoint via curl with X-API-Key header from outside the container. Verify it works end-to-end including Supabase row + Notion mirror.
8. Use `mcp__claude_ai_n8n__validate_workflow` on the staged n8n code.
9. Use `mcp__claude_ai_n8n__create_workflow_from_code` to deploy the n8n workflow.
10. Test n8n workflow with a sample webhook POST.
11. Branch `feature/ai-score-flow` off `bokar83/geolisted-site` main. Update `index.html`. Push. Hostinger auto-deploys.
12. End-to-end test on geolisted.co live: submit form, watch scanner UI, see score on screen, verify email lands as draft, verify Supabase row, verify Notion mirror.
13. Manually click Send on first 5 drafts. Each draft MUST pass this 5-point checklist before flipping `SCORE_AUTO_SEND=true`:
    1. Renders correctly in Gmail web AND Apple Mail iOS preview
    2. Score number on screen == score number in email body (no drift)
    3. All 3 quick wins are score-derived for that specific lead, not boilerplate
    4. Zero em dashes (verify with `grep "-|-"` on the rendered HTML)
    5. The Calendly link returns HTTP 200 on click
    If any draft fails any check, halt the flip and fix the rendering pipeline before proceeding.
14. Merge feature branches to main.
15. Update memory: `reference_website_registry.md` (flip status to LIVE), `project_hormozi_lead_gen_2026_04_30.md` (mark score path shipped), `feedback_calendly_over_forms.md` (note geolisted migration done).

---

## Three Outsider guardrails (binding)

### Guardrail 1: Scanner timeout + skip option

The browser-side JS that displays the scanner card MUST:
- Show an elapsed-time counter (`Scanning... 23s / max 60s`)
- After 45 seconds, show a "This is taking longer than expected. Email me the result instead?" button
- If clicked, the browser closes the form, shows a success message, and the score arrives via email only
- Hard-fail at 90 seconds: show error, suggest retry, log the failure

### Guardrail 2: Form-flip rollback step

The geolisted-site form change ships with **dual endpoint support**:
- The `<form>` action points to the new n8n webhook
- A `data-fallback-url="https://formspree.io/f/boubacar"` attribute is preserved
- The submit handler attempts the n8n endpoint first; on network error or 5xx, falls back to Formspree
- After 7 days of clean operation, the Formspree fallback is removed in a separate PR

### Guardrail 3: X-API-Key rotation rule

In `reference_website_registry.md`:
- Document `ORCHESTRATOR_API_KEY` rotation cadence: every 90 days
- Document the rotation procedure: rotate VPS .env → update n8n credential `agentsHQ Orchestrator API Key` → restart container → verify
- Document the break-glass: if key is compromised, rotate immediately and audit Supabase `leads` for any rows in last 24h that look bot-generated

---

## Score-result data capture (Expansionist concern)

Every call to `/score-request` writes the full result to Supabase. Schema additions to `leads`:
- `ai_score` (existing column from cold pipeline, reuse)
- `ai_breakdown` (existing JSONB column, reuse)
- `ai_quick_wins` (existing column, reuse)

This means after 50 score runs, the data is already structured for content reuse:
```sql
SELECT industry, AVG(ai_score), COUNT(*)
FROM leads
WHERE source = 'geolisted.co - Score Request'
GROUP BY industry HAVING COUNT(*) > 10;
```

→ "Pediatric dentists in Salt Lake City average 22/100 on AI visibility (n=18)" → LinkedIn carousel material. **No new schema work needed; the existing pipeline already captures this.**

---

## What is NOT in this build (deferred, with explicit triggers)

- **Generalized inbound capture pattern across Calculatorz / Convertisseur / Unit Converter / humanatwork.ai / boubacarbarry.com.** Sankofa Expansionist flagged as 3x leverage. **Trigger condition for v2 generalization:** score runs > 100 OR a second Boubacar-owned site needs inbound capture, whichever comes first.
- **Public AI Visibility Score widget for embedding on third-party sites.** Defer until the geolisted.co flow proves demand (>50 completed score runs / month).
- **Score-result content engine (Phase 1.5).** AFTER 50 score runs total: add a Supabase aggregator that fires daily and Telegrams Boubacar when any niche+city pair crosses N=10 score runs, with an auto-generated stat in the form "X niche in Y city averages Z/100 on AI visibility (n=N)". ~30 LOC. Becomes LinkedIn carousel material. Post-launch task.
- **Deeper-audit upsell (Phase 2).** Email CTA could become "I want the full audit" → triggers a 10-minute deeper scoring run with competitor comparison. Self-segments high-intent visitors. Defer until first 50 score runs prove the funnel.
- **Multi-language support (French Africa, MENA).** Per memory's `signal_works_plan.md`, defer until $5K MRR.

---

## Success criteria (binding)

This build is done when ALL of these are true:

| # | Check | Verification command |
|---|---|---|
| 1 | Visitor can submit the geolisted.co form | Manual visit to geolisted.co, submit, see scanner |
| 2 | Score appears on screen within 90s | Manual test |
| 3 | Score email lands in visitor's inbox | Manual test, check inbox |
| 4 | Lead appears in Supabase with correct source | `SELECT * FROM leads WHERE source LIKE 'geolisted.co%' ORDER BY created_at DESC LIMIT 1` |
| 5 | Lead mirrors to Notion CRM | Visual check in Notion Leads view |
| 6 | Telegram notification fires | Check Telegram on test |
| 7 | Formspree fallback works if n8n endpoint is down | curl with bad endpoint, verify form falls through |
| 8 | The form change is reverted by a single git revert if needed | dry-run `git revert` on the feature commit |

If any of 1-7 fails on the first run, fix before merging. If 8 is broken, the rollback path is broken; fix it first.

---

## Rejected alternatives

| Approach | Why rejected |
|---|---|
| Reuse `/inbound-lead` route | Schema mismatch (booking_id required, source enum). Forces two intents into one runner. |
| Async webhook + browser polling | Over-engineered for unproven inbound channel. Sync wait is acceptable for "scan my site" UX. |
| Always send email (no env gate) | Violates `feedback_test_before_live.md`. Need first 5 manual verifications. |
| Direct browser → VPS API (no n8n) | Inconsistent with the n8n-everywhere pattern. Loses Supabase + Notion + Telegram fan-out. |
| Vercel serverless function | New infra. The VPS already runs FastAPI. Boubacar's rule: "Existing stack first." |
| New `score_report_sender.py` file | `email_builder.py` already does score+breakdown+quick-wins HTML. Karpathy WARN: extend not create. |

---

## Open questions for Friday morning

These can be answered without code, but I want them on the record:

1. **Visitor email validation:** if the visitor enters a fake email, the score still computes (cost = real OpenRouter + SerpAPI calls). Add a basic regex check + maybe a Have-I-Been-Pwned-style "is this a real domain" check? Or accept the abuse risk for v1?
2. **Rate limit:** what stops a script kiddie from running the score 100x in 10 min? Recommend basic rate limit (5/min per IP) on the VPS route.
3. ~~**Score-result CTA in the email:** should the CTA be "Book a Signal Works call" (Calendly), "Buy a custom audit ($X)", or "Read the FAQ"?~~ **LOCKED 2026-04-30 (Sankofa Pass 3 Outsider revision):** CTA URL = `SIGNAL_WORKS_CALENDLY` env var (NOT `SIGNAL_WORKS_CALENDLY_AUDIT`). CTA text = "Book a 20-minute Signal Works call." Mirrors cold-email T1-T5 wording for consistency across all geolisted.co touchpoints.

These are not blockers for Friday's build but should be answered by the time we ship to live traffic.
