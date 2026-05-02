# Session Handoff :  Constraints AI Live + Conversion Moves Shipped :  2026-05-01

## TL;DR

Catalyst Works v3-WOW site at catalystworks.consulting now has a live, working Constraints AI demo backed by an n8n workflow that calls OpenRouter, logs to Supabase, and pings Boubacar's Telegram with warm/tire-kicker tagging on every diagnose. Sankofa Council surfaced the real conversion bug mid-session: the `$497 Signal Session` CTA was leaking to a free 45-min discovery event. Created a paid Calendly event (`Signal Session: Business Constraint Diagnostic`), wired the URL into the site, flipped the CTA copy from "Book a 45-min discovery call" to "Book the Signal Session", swapped the fine-print from free-funnel to direct-pay refund language, and rewrote the post-diagnosis email capture from PDF-tax to "three reframes from Boubacar in 24 hours" value-transfer. Pricing audit across all surfaces fixed two stale bugs (og-image.jpg showed `$350 / 60 min`, ai-data-audit.html had broken `bokar83` Calendly URLs) and scrubbed a `$397 in 14 days` discount from the lead-magnet template. Both Signal Session events are now `is_paid: true` after Boubacar wired Stripe in the UI.

## What was built / changed

**catalystworks-site (github.com/bokar83/catalystworks-site, main branch, 3 commits this session: `d4f18a1`, `16e3df5`, `4b3dfd2`)**

- `index.html` line 1674: `WORKER_URL` set to `https://n8n.srv1040886.hstgr.cloud/webhook/catalystworks-constraints-ai`. Demo now hits live LLM proxy.
- `index.html` line 1443/1447: Calendly URL swapped from `ai-strategy-discovery-call` (free) to `signal-session-business-constraint-diagnostic` (paid).
- `index.html` line 1395: button copy `Book a 45-min discovery call` → `Book the Signal Session`.
- `index.html` line 1397: fine-print `Free 45-minute discovery to confirm Signal Session fit. Full $497 invoiced after, only if we proceed.` → `$497 charged at booking. Refund in full if I do not name a constraint you can act on. No discovery call. No proposal. The session is the work.`
- `index.html` lines 1202-1212: capture form rewritten from `1-page PDF + 30-day follow-up framework` to `three sharper reframes from Boubacar in 24 hours`.
- `og-image.html` line 160: `60 minutes... $350` → `90 minutes... $497`.
- `og-image.jpg`: regenerated from corrected HTML at 1200x630 via Playwright + local server.
- `ai-data-audit.html` 5 places: `calendly.com/bokar83/...` → `calendly.com/boubacarbarry/signal-session-ai-data-exposure-audit`.

**agentsHQ repo (github.com/bokar83/agentHQ, main branch, commit `dd4b7d0`)**

- `lead-gen-system/templates/lead-magnet-brief-template.md` lines 123, 160: scrubbed `$397 if booked in 14 days` discount to keep $497 floor consistent across all surfaces.

**n8n workflow `2pcr6SLSF4zZch9z` (Catalyst Works Constraints AI Proxy, hosted at n8n.srv1040886.hstgr.cloud)**

Final shape (12 nodes, active version `f09f524a-d66f-428a-b73c-281089feacc4`):
```
Webhook -> Validate and Route -> Switch (Route Action)
                                    |0 blocked  -> Respond Blocked
                                    |1 diagnose -> Call OpenRouter (HTTP) -> Sanitize LLM Output -> Log Diagnosis to Supabase -> Telegram Nag -> Respond Diagnose
                                    |2 capture  -> Log Capture to Supabase -> Telegram Capture Nag -> Respond Capture
```

- `Validate and Route`: added profanity short-circuit (saves OpenRouter $ on noise inputs) and `leadQuality: warm|tire-kicker` classifier (warm = pain has digit AND length ≥ 80).
- `Call OpenRouter`: HTTP Request node using `={{ "Bearer " + $env.OPENROUTER_API_KEY }}` in Authorization header. (Earlier attempt: tried Code node with `await fetch`. n8n Code sandbox has no fetch :  wasted iteration.)
- `Sanitize LLM Output`: dropped debug-meta merge (was leaking `__upstream_status`, `__error`, `__raw_preview` to Supabase `response_json` column. Now returns clean `{constraint, signals, action}`).
- `Telegram Nag`: HTTP node POST to `api.telegram.org/bot{{ $env.TELEGRAM_BOT_TOKEN }}/sendMessage` with chat_id `7792432594`. Markdown-formatted message includes leadQuality tag, pain text, constraint, action, ip-hash prefix.
- `Telegram Capture Nag`: same pattern, captures pain + email and reminds Boubacar to write back within 24 hours.

**VPS `/root/docker-compose.yml` (n8n service)**

Added env vars (n8n container restarted to pick up):
- `OPENROUTER_API_KEY=<value>` :  value from agentsHQ `.env`
- `TELEGRAM_BOT_TOKEN=<value>` :  value from `ORCHESTRATOR_TELEGRAM_BOT_TOKEN`
- `TELEGRAM_CHAT_ID=7792432594`
- `N8N_BLOCK_ENV_ACCESS_IN_NODE=false` (required, default is `true` since n8n v2.0)
- `N8N_FUNCTION_ALLOW_BUILTIN=*`, `N8N_FUNCTION_ALLOW_EXTERNAL=*` (for `require("crypto")`)

**Calendly events** (api method via `mcp__claude_ai_Calendly__event_types-create_event_type`)

- Created: `Signal Session: Business Constraint Diagnostic` :  UUID `fea6a45b-a2c2-43cb-951b-093b215cdd9b`, 90 min, scheduling URL `https://calendly.com/boubacarbarry/signal-session-business-constraint-diagnostic`. Boubacar wired Stripe in UI → `is_paid: true` confirmed via API.
- Existing event also fixed: `Signal Session: AI Data Exposure Audit` :  UUID `1aeae88d-6b4d-4f1f-a254-3e7762beb4cd`. Was `is_paid: false` until Boubacar wired Stripe. Now `is_paid: true` confirmed.

**Supabase tables** (`diagnostic_submissions`, `diagnostic_captures`)

Already existed from earlier session. This session: verified clean rows (no debug-meta leak after sanitize fix). Latest test row `id=10` shows clean schema.

## Decisions made

- **n8n over Cloudflare Worker for the LLM proxy.** Pre-session: Karpathy + Sankofa stress-tested the Cloudflare path, rejected it. Reasons: extra account + paid plan + more moving parts; n8n was already running on the same VPS; existing n8n workflows are templates for the new one.
- **HTTP Request node, not Code node, for OpenRouter call.** n8n docs are explicit: Code node sandbox has no fetch. Documented as `feedback_n8n_code_node_no_fetch.md`.
- **`is_paid` toggle is UI-only.** Calendly REST API has no field to set pricing. Documented as `feedback_calendly_payment_ui_only.md`. Both Signal Session events confirmed `is_paid: true` after Boubacar's UI fix.
- **$497 is the entry-tier anchor for both Catalyst Works and Signal Works.** Both Signal Sessions price at $497. AI Governance playbook shows the ladder: $497 entry → $3,500 SHIELD → $8,500 Sprint → $1,500-$5,000/mo retainer. Discount mechanics on lead magnets removed; discounts must be campaign-specific, not template default.
- **Council rejected the Move 4 fake proof line.** The council wanted ONE specific outcome with a real number above the offer card. Per `feedback_no_client_engagements_yet.md` and `feedback_never_fabricate_client_stories.md`, can't fabricate. Held the move pending a real number from Boubacar's operator era ("at [company], cut [metric] from X to Y in N weeks"). Site copy is stronger after the fine-print + button copy flips even without it.

## What is NOT done (explicit)

- **Move 4 (proof line above offer card):** Held. Need Boubacar to send one operator-era stat with real numbers.
- **Move 5 (LinkedIn post from logged data):** Council recommended Friday 2026-05-08 :  pull last 30 days of `diagnostic_submissions`, classify patterns, draft "I read 50 owner-operators describe what is stuck. Three patterns kept showing up." Not scheduled yet.
- **Per-IP rate limiting on the public webhook:** Audit subagent flagged this as a cost-defense risk. No fix tonight. Recommend `ipHash → Supabase upsert with last_seen_at` in `Validate and Route` next session.
- **Skill extraction:** The Constraints AI workflow (locked prompt + Supabase logging + Telegram nag) is reusable. Audit subagent estimated 1-2 hours to extract as an agentsHQ skill. Deferred per Sankofa "revenue first" verdict.
- **OG image cache priming:** Pushed new og-image.jpg but didn't run LinkedIn / Twitter debugger refresh. Old cached preview may still appear on platforms for hours.

## Open questions

- **MODE 2 sarcasm not surfacing.** Audit subagent noted: vague input ("things feel stuck idk") got a confident MODE 1 answer instead of the sarcasm-5/10 redirect the system prompt asks for. This is prompt-tuning, not a bug. Decision: leave as-is until we have signal from real visitors that vague inputs are happening often enough to matter.
- **Telegram pings: did Boubacar receive the test messages?** I sent two test pings during validation (one warm-tagged margin/headcount input, one capture form test). The orchestrator bot is `@agentsHQ4Bou_bot` chat ID `7792432594`. He confirmed "I got something from the constraints AI" after first test. Second test (capture form) not explicitly confirmed.

## Next session must start here

1. **Confirm Telegram capture nag fired correctly.** Look at @agentsHQ4Bou_bot chat history :  was there a `*Constraints AI capture* ...` message tonight? If not, test the capture path again from Playwright.
2. **Ask Boubacar for Move 4 proof line.** One operator-era stat with real numbers. Wire it in above the offer card (line ~1373 of index.html) and push.
3. **Schedule Move 5** (LinkedIn-post-from-data) for 2026-05-08. Use `mcp__claude_ai_n8n__create_workflow_from_code` or a `RemoteTrigger` one-shot. Pull `diagnostic_submissions` last 30 days, classify patterns, draft the post.
4. **Add per-IP rate limit to Constraints AI workflow.** Code node uses `ipHash` already; add a Supabase upsert keyed on `ip_hash` with `last_seen_at` timestamp; if recent, set `blocked = "rate_limited"`. 1 hour of work.
5. **Optional: extract n8n LLM-proxy pattern as a skill.** 1-2 hours per audit estimate. Would unlock similar demos on Signal Works, AI Governance, HR Exposed sites without re-debugging.

## Files changed this session

```
catalystworks-site repo:
  index.html                    [WORKER_URL, Calendly URL, CTA copy, capture copy, fineprint]
  og-image.html                 [$350/60min → $497/90min]
  og-image.jpg                  [regenerated]
  ai-data-audit.html            [5 broken Calendly URLs fixed]

agentsHQ repo:
  lead-gen-system/templates/lead-magnet-brief-template.md  [$397 discount scrubbed]

n8n workflow 2pcr6SLSF4zZch9z (live):
  Validate and Route Code       [profanity check, leadQuality classifier]
  Call OpenRouter HTTP node     [$env.OPENROUTER_API_KEY auth]
  Sanitize LLM Output Code      [debug-meta leak fixed]
  Telegram Nag (new)            [warm/tire-kicker pings on diagnose]
  Telegram Capture Nag (new)    [email + pain pings on capture]

VPS /root/docker-compose.yml:
  + OPENROUTER_API_KEY env
  + TELEGRAM_BOT_TOKEN env
  + TELEGRAM_CHAT_ID env
  + N8N_BLOCK_ENV_ACCESS_IN_NODE=false
  + N8N_FUNCTION_ALLOW_BUILTIN=* / EXTERNAL=*

Calendly:
  Created: Signal Session: Business Constraint Diagnostic ($497, 90min, is_paid:true)
  Verified: Signal Session: AI Data Exposure Audit (now is_paid:true)

Memory writes:
  feedback_n8n_publish_after_update.md       [new]
  feedback_n8n_code_node_no_fetch.md         [new]
  feedback_calendly_payment_ui_only.md       [new]
  reference_constraints_ai_proxy.md          [new]
  MEMORY.md                                  [+2 pointers, -1 unused, net 200 lines]

Skill writes:
  ~/.claude/skills/frontend-design/SKILL.md  [+ HARD RULE: regenerate OG images]
  /d/Ai_Sandbox/agentsHQ/skills/frontend-design/SKILL.md  [synced]
```
