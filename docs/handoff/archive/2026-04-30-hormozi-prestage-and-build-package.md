# Session Handoff: Hormozi Pre-Stage + Friday Build Package - 2026-04-30 (continuation)

## TL;DR

Continuation of the Hormozi lead-gen session. Boubacar sent 3 warm DMs by hand (Brody Horton, Rod Lambourne, Rich Hoopes via LinkedIn) and named the meta-constraint: "I don't have any truly warm connections in the States." Pivoted to building the geolisted.co AI Visibility Score web tool as the inbound channel that compounds while the warm network rebuilds. Pre-staged the entire build package (8 files in `lead-gen-system/build-staging/`), validated the n8n workflow via MCP, ran Karpathy + Sankofa twice each. Both audits returned SHIP. Friday 2026-05-01 8am MT execution window with a halt-condition gate on the warm-DM outcome.

## What was built / changed

### Files created (all in `lead-gen-system/`)

**Sent log (3 warm DMs, one folder per batch):**
- `sent/2026-04-30-warm-reactivation-batch-1/README.md`
- `sent/2026-04-30-warm-reactivation-batch-1/01-brody-horton.md`
- `sent/2026-04-30-warm-reactivation-batch-1/02-rod-lambourne.md`
- `sent/2026-04-30-warm-reactivation-batch-1/03-rich-hoopes.md`
- `sent/2026-04-30-warm-reactivation-batch-1/outcomes.md` (template, awaiting reply data)

**Build staging (8 drafts; nothing committed to production):**
- `build-staging/BUILD-PLAN-v2.md` (locked, 7 + 4 binding revisions applied)
- `build-staging/schema_score_request.py` (Pydantic ScoreRequestPayload + ScoreResult)
- `build-staging/runner_score_request.py` (orchestration pipeline ~120 LOC)
- `build-staging/route_score_request.py` (`POST /score-request` route, X-API-Key gated, append to `orchestrator/app.py`)
- `build-staging/email_builder_extension.py` (`render_inbound_report_html()` append to `signal_works/email_builder.py`)
- `build-staging/gmail_draft_send_extension.py` (`send_message()` append to `signal_works/gmail_draft.py`, env-gated)
- `build-staging/geolisted_form_handler.html` (form + scanner + safe-DOM result render; XSS purged via security hook flag)
- `build-staging/n8n_workflow_geolisted_score.ts` (VALIDATED via mcp__claude_ai_n8n__validate_workflow → 4 nodes valid)

### Files updated

- `lead-gen-system/README.md` - added `sent/` folder navigation, em-dashes purged
- `deliverables/hormozi-lead-gen/previews/geolisted-score-flow.html` - corrected `/api/score` → `/score-request`, added pre-stage notes
- `docs/handoff/2026-04-30-hormozi-lead-gen-skill-build.md` - earlier handoff updated mid-session with falsifier-test status

### Memory written

**MEMORY.md (4 new pointers, 1 consolidation to stay under 200 lines):**
- `feedback_agentshq_self_build_first.md` - execution model
- `feedback_read_before_asking.md` - read-first rule
- `feedback_audits_before_implementation.md` - Karpathy + Sankofa BEFORE code
- `reference_n8n_sdk_shape.md` - canonical n8n SDK shape

**Project memory updated:**
- `project_hormozi_lead_gen_2026_04_30.md` - added pre-stage section, build-package inventory, A/A/A architectural decisions, Friday halt-condition

### n8n verification (read-only)

- 4 active form-pattern workflows already exist on the VPS n8n (`IeSWirZ2W5DW1qvH`, `jGksZgH3Xp8TBBXY`, `VmikWwt8kIR3rXoy`, plus HR Exposed). Pulled details via `mcp__claude_ai_n8n__get_workflow_details` to use as templates.
- Webhook base URL: `https://n8n.srv1040886.hstgr.cloud/`
- Existing X-API-Key credential reusable: `agentsHQ Orchestrator API Key`

## Decisions made

### Architecture (operator-confirmed A/A/A)

1. **New `/score-request` route, NOT reuse of `/inbound-lead`.** Existing `InboundPayload` schema requires `booking_id` and the source enum is `Literal["calendly", "formspree"]` - both incompatible with score requests.
2. **Sync webhook with `responseMode: 'responseNode'`.** Browser holds the connection 30-60 seconds while the score computes. n8n responds with the full score JSON. Async polling rejected as over-engineered for unproven channel.
3. **`SCORE_AUTO_SEND` env gate.** Default false → drafts created via existing `gmail_draft.create_draft()`. Flip to true after first 5 manual verifications pass a 5-point quality checklist. Test-before-live rule honored.

### Plan revisions locked

- Email render: extend `signal_works/email_builder.py` with `render_inbound_report_html()`, do NOT create `score_report_sender.py` (Karpathy WARN closed)
- Email CTA URL: `SIGNAL_WORKS_CALENDLY` env var (NOT `SIGNAL_WORKS_CALENDLY_AUDIT`)
- Email CTA text: "Book a 20-minute Signal Works call" (mirrors cold-email T1-T5 wording)
- v2 generalization trigger: score runs > 100 OR a 2nd Boubacar-owned site needs inbound capture
- Phase 1.5 (post-50-runs): Supabase aggregator fires Telegram with auto-generated stats per niche+city when N >= 10
- Formspree fallback preserved for 7 days post-launch via `data-fallback-url` attribute
- 5-point quality checklist gates the auto-send flip

### Friday halt-condition (binding)

Step 1 of execution order: read `lead-gen-system/sent/2026-04-30-warm-reactivation-batch-1/outcomes.md`. If 0 replies AND 0 sends from Boubacar, the build does NOT proceed. Pivot to network-rebuild routines per Sankofa First Principles.

## What is NOT done (explicit)

- **No production files modified.** Zero touches to `orchestrator/app.py`, `signal_works/*`, `templates/email/*`, `bokar83/geolisted-site/index.html`, or any n8n workflow. All 8 staged drafts are in `build-staging/` only.
- **n8n workflow created? NO.** Validated via MCP, not yet created via `create_workflow_from_code`. That's a Friday step.
- **CW auto-send still ON.** In-flight cold batch from 2026-04-29 continues its 19-day sequence per the earlier session decision.
- **3 warm DMs sent, replies not yet checked.** That's the Friday-morning halt-condition input.
- **Margin Bottleneck Diagnostic web tool** still NOT built. Was deferred earlier; remains deferred in BUILD-PLAN-v2.
- **CW T1-T5 enhancement diffs** still PROPOSED only, not committed. Earlier session output, unchanged.

## Open questions

1. Friday outcome of the 3 warm DMs (Brody, Rod, Rich) determines whether the build proceeds.
2. Apex Tool Group reference in CW T4 enhancement diff - fact-check whether to keep or replace with a different employer name (low-confidence item from earlier review-gate).
3. SW T1 production ambiguity (`sw_t1.py` plain-text vs `email_builder.py` HTML) - earlier review-gate question still open. Doesn't block this build but blocks any SW change.

## Next session must start here

1. **Read `lead-gen-system/sent/2026-04-30-warm-reactivation-batch-1/outcomes.md` first.** Update with whatever replies came in (or didn't).
2. **Apply the halt-condition decision tree:**
   - 0 replies AND 0 new sends → execution-only mode, do NOT build, pivot to network-rebuild routines
   - 3 sent / 0 replies → build proceeds with caveat that warm channel is weaker than expected; consider personalization audit before sending more
   - 1+ reply → build proceeds; respond to the reply using ACA framework first (Acknowledge / Compliment / Ask)
   - 1+ booked call → run Discovery Call OS v2.0; build queue waits behind the close
3. **If build proceeds: read `lead-gen-system/build-staging/BUILD-PLAN-v2.md` execution order top to bottom.** It is the canonical artifact. 15 steps. ~90 min.
4. **Step 8 of execution order:** call `mcp__claude_ai_n8n__validate_workflow` once more on `n8n_workflow_geolisted_score.ts` (sanity check), then `mcp__claude_ai_n8n__create_workflow_from_code` to deploy.
5. **Step 13 of execution order:** verify all 5 first drafts pass the 5-point quality checklist BEFORE flipping `SCORE_AUTO_SEND=true`.

## Files changed this session

``
lead-gen-system/
├── README.md                                     (UPDATED: sent/ navigation + em-dash purge)
├── sent/                                         (NEW folder)
│   └── 2026-04-30-warm-reactivation-batch-1/
│       ├── README.md
│       ├── 01-brody-horton.md
│       ├── 02-rod-lambourne.md
│       ├── 03-rich-hoopes.md
│       └── outcomes.md
└── build-staging/                                (NEW folder)
    ├── BUILD-PLAN-v2.md
    ├── schema_score_request.py
    ├── runner_score_request.py
    ├── route_score_request.py
    ├── email_builder_extension.py
    ├── gmail_draft_send_extension.py
    ├── geolisted_form_handler.html
    └── n8n_workflow_geolisted_score.ts             (VALIDATED 4 nodes)

deliverables/hormozi-lead-gen/previews/
└── geolisted-score-flow.html                     (UPDATED: /api/score → /score-request)

docs/handoff/
├── 2026-04-30-hormozi-lead-gen-skill-build.md    (UPDATED mid-session)
└── 2026-04-30-hormozi-prestage-and-build-package.md (NEW: this file)

MEMORY `(C:/Users/HUAWEI/.claude/projects/d--Ai-Sandbox-agentsHQ/memory/):`
├── feedback_agentshq_self_build_first.md         (NEW)
├── feedback_read_before_asking.md                (NEW)
├── feedback_audits_before_implementation.md      (NEW)
├── reference_n8n_sdk_shape.md                    (NEW)
├── project_hormozi_lead_gen_2026_04_30.md        (UPDATED: pre-stage section + Friday gate)
└── MEMORY.md                                     (UPDATED, 199/200 lines)

UNCHANGED (production):
- orchestrator/app.py (no /score-request route yet)
- signal_works/email_builder.py (no render_inbound_report_html yet)
- signal_works/gmail_draft.py (no send_message yet)
- signal_works/ai_scorer.py (UNCHANGED, no edits needed)
- All templates/email/*.py
- bokar83/geolisted-site/index.html (form still posts to Formspree)
- VPS .env (SCORE_AUTO_SEND not yet added)
- All n8n workflows (no geolisted-score workflow created yet)
``
