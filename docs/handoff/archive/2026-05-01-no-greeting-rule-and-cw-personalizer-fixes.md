# Session Handoff :  No-Greeting Rule + CW Voice Personalizer Fixes :  2026-05-01

## TL;DR

Locked the no-greeting-on-low-confidence rule across all 9 cold-email templates (CW T1-T5, SW T1-T4) via `build_body(lead)` callable pattern. Source-aware first-name extraction in `skills/outreach/sequence_engine.py` with HIGH/LOW confidence. Fixed 3 bugs in CW path that were quiet-failing voice personalization on the 9 leads SW pulled today: `voice_personalizer.py` source filter (apollo_catalyst_works → LIKE 'apollo_catalyst_works%%' with %% escape for psycopg2), `topup_cw_leads.py` now persists `website_url` at INSERT (saves Serper credit + ~1s/lead), `apollo_client.py:reveal_emails` captures `organization.website_url`. Did NOT backfill the 9 stranded leads to preserve lift-test data integrity. Weekday-only send window already in production.

## What was built / changed

**Templates (9 files) :  confidence-aware greeting**

- `templates/email/cold_outreach.py` (CW T1) :  uses `build_body(lead)`
- `templates/email/sw_t1.py` :  uses `build_body(lead)`
- `templates/email/cw_t2.py` through `cw_t5.py` :  refactored from static `BODY` to `build_body(lead)` (handwritten, Path B per Karpathy audit)
- `templates/email/sw_t2.py` through `sw_t4.py` :  same refactor

Pattern in each:
```python
_GREETING_HIGH = "Hi {first_name},\n\n"
_BODY_HOOK = """[hook content]"""
BODY = _GREETING_HIGH + _BODY_HOOK  # legacy export

def build_body(lead: dict) -> str:
    confidence = lead.get("first_name_confidence", "low")
    greeting = _GREETING_HIGH if confidence == "high" else ""
    return (greeting + _BODY_HOOK).format(first_name=..., niche=..., city=...)
```

**Sequence engine :  source-aware extraction**

- `skills/outreach/sequence_engine.py:_extract_first_name()` :  source-aware. Trusts `lead.name` ONLY on `apollo_*` source. Falls through to email parsing on `signal_works*`.
- `_first_name_from_email()` :  returns `(name, confidence)`. HIGH if has `.`/`-` separator, OR known prefix (dr/mr/mrs/ms), OR `len(local) <= 6`. LOW otherwise.
- `_render()` :  passes `first_name_confidence` into the enriched lead dict.

**Voice personalizer :  source filter fix**

- `signal_works/voice_personalizer.py:144` :  `AND source = 'apollo_catalyst_works'` → `AND source LIKE 'apollo_catalyst_works%%'`. The `%%` is required because the same SQL has `LIMIT %s` and psycopg2 paramstyle="format" treats raw `%` as a placeholder marker. Symptom of the bug if you forget: `IndexError: tuple index out of range` from inside `cursor.execute`.

**Apollo + topup :  website_url at insert**

- `skills/apollo_skill/apollo_client.py:314` :  `reveal_emails()` adds `"website_url": (match.get("organization") or {}).get("website_url", "")` to its return dict.
- `signal_works/topup_cw_leads.py` :  `_save_cw_lead` INSERT now includes `website_url` column.

**Skill files updated (HARD RULE per /tab-shutdown :  never defer to memory)**

- `~/.claude/skills/cold-outreach/SKILL.md` :  added HARD RULES block: no-greeting-on-low-confidence, signature standard (first name + URL only), weekday-only send. Bumped to v1.1.
- `~/.claude/skills/apollo_skill/SKILL.md` :  added HARD RULES block: company-name lookup uses `mixed_people/api_search` (not `organizations/enrich`), website_url at insert, psycopg2 %% escape, mandatory `scripts/orc_rebuild.sh`. Bumped to v1.1.

**Memory files saved this session (running list)**

- `feedback_use_orc_rebuild_wrapper.md` (HARD RULE: never bare `docker compose build orchestrator`)
- `reference_coordination_layer.md` (claim/complete/list_running task locks)
- `feedback_apollo_company_name_lookup.md` (mixed_people/api_search not organizations/enrich)
- `feedback_pyright_reverts_agents_py.md` (UPDATED :  broader scope across signal_works, skills, templates)
- `feedback_no_greeting_when_unknown.md` (the rule + research backing)
- `feedback_psycopg2_like_escape.md` (the %% escape, fresh today)

**AGENT_SOP additions**

- "Always use scripts/orc_rebuild.sh, never bare `docker compose build orchestrator`" :  Hard Rule
- "Cold email greeting: drop entirely when first_name_confidence is low; never use 'Hi there'" :  Hard Rule

## Decisions made

- **Path B (handwrite the 7 templates) over Path A (regex codegen)** :  per Karpathy + reviewer audit. Surgical, predictable, no template-engine introduction.
- **Don't backfill the 9 stranded leads (1763-1771)** :  preserves the lift-test data integrity. Reviewer's explicit rule. New leads going forward will hit the corrected source filter and personalize cleanly.
- **Weekday gate at the runner level, not the cron level** :  `signal_works/morning_runner.py:_main_body()` checks `datetime.now().weekday() >= 5` and skips Steps 3 + 5. Harvest still runs 7 days/week (queue inventory). Send only Mon-Fri.
- **No-greeting research-backed (Lemlist 2024, Apollo 2023, Hunter 2024 on 50M+ emails)** :  generic greetings underperform every alternative including no-greeting. Production damage already shipped: "Hi Commercial," / "Hi Utah Plumbing,". Locked across all 9 templates.

## What is NOT done (explicit)

- 9 stranded leads (1763-1771) NOT backfilled :  by design.
- AUTO_SEND_CW=true NOT flipped :  deferred until Boubacar reviews drafts.
- Hunter Starter plan upgrade NOT decided :  deferred until Tier 3+ engagement.
- Branch reconciliation across `feature/coordination-layer`, `feature/notion-task-audit`, `main` :  deferred. No data loss; just lineage to track.

## Open questions

- None blocking. The CW personalizer fixes are merged into `feature/notion-task-audit` (commits ca00b2f + 9aa1aa1). Confirm tomorrow morning's run produces 10 CW + 10 SW with personalized voice on every CW lead with website_url present.

## Next session must start here

1. Read `docs/roadmap/harvest.md` for current state of CW + SW pipelines.
2. Check tomorrow morning's runner output: did 10 CW + 10 SW drafts ship? Did `voice_personalizer` successfully process the new leads (look for `voice_lead` source records, not just stranded `apollo_catalyst_works` records)? Are CW drafts opening with greetings only on lead.name from Apollo source?
3. If runner produced expected output: consider AUTO_SEND_CW=true flip after Boubacar reviews drafts.
4. If runner failed: check `task:morning-runner` lock state, check container health, check `voice_personalizer.py:144` is the `%%`-escaped version on VPS.
5. Branch reconciliation: `feature/coordination-layer` (10+10 + rebuild wrapper + 9 templates) and `feature/notion-task-audit` (CW personalizer fixes) both have important work. Plan the merge into main.

## Files changed this session

```
templates/email/cold_outreach.py     (CW T1 build_body)
templates/email/sw_t1.py             (SW T1 build_body)
templates/email/cw_t2.py             (CW T2 build_body)
templates/email/cw_t3.py             (CW T3 build_body)
templates/email/cw_t4.py             (CW T4 build_body)
templates/email/cw_t5.py             (CW T5 build_body)
templates/email/sw_t2.py             (SW T2 build_body)
templates/email/sw_t3.py             (SW T3 build_body)
templates/email/sw_t4.py             (SW T4 build_body)
skills/outreach/sequence_engine.py   (source-aware first-name extraction)
signal_works/voice_personalizer.py   (source filter + %% escape)
signal_works/topup_cw_leads.py       (website_url at INSERT)
skills/apollo_skill/apollo_client.py (website_url in reveal_emails return)
signal_works/morning_runner.py       (weekday gate, from earlier)
scripts/orc_rebuild.sh               (coordination wrapper, from earlier)
docs/AGENT_SOP.md                    (2 Hard Rules added)
~/.claude/skills/cold-outreach/SKILL.md  (HARD RULES block + v1.1)
~/.claude/skills/apollo_skill/SKILL.md   (HARD RULES block + v1.1)
~/.claude/projects/.../memory/feedback_psycopg2_like_escape.md (NEW)
~/.claude/projects/.../memory/feedback_no_greeting_when_unknown.md (NEW)
~/.claude/projects/.../memory/feedback_use_orc_rebuild_wrapper.md (NEW)
~/.claude/projects/.../memory/feedback_apollo_company_name_lookup.md (NEW)
~/.claude/projects/.../memory/reference_coordination_layer.md (NEW)
~/.claude/projects/.../memory/feedback_pyright_reverts_agents_py.md (UPDATED)
```

## Session state at shutdown

- VPS image rebuilt with all fixes baked in (orc-crewai healthy)
- origin/feature/coordination-layer @ 8e86745 (10+10 + rebuild wrapper + 9 templates with confidence-aware greeting)
- origin/feature/notion-task-audit @ 940e1b8 (contains my ca00b2f voice_personalizer fix + 9aa1aa1 website_url-at-insert fix)
- 2 health-check routines scheduled (7d + 14d Telegram reports)
