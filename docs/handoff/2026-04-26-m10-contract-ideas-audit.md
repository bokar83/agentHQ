# Session Handoff: M10 Crew Contract + Ideas DB Audit
# 2026-04-26

## TL;DR

Long session. Started by resolving a merge conflict and rebasing the M10 branch.
Shipped M10 (autonomous crew contract gate) across 7 tasks: ContractNotSatisfiedError
enforcement in autonomy_guard.py, per-crew cost ceiling, signed contracts for griot
and auto_publisher, content_approvals Postgres table, Evergreen/Timely TTL in
auto_publisher, Content Type Notion field, VPS deploy. Then ran R55-R51 RoboNuggets
harvest batch (Council approved R57 only). Closed with a full Ideas DB audit:
updated 20+ records, added Domain field, ran two Council passes on relevance,
corrected n8n framing in memory, locked in the Ideas-as-parking-lot principle.

---

## What was built / changed

### M10: Autonomous Crew Contract (SHIPPED, live on VPS)

- `orchestrator/autonomy_guard.py`: ContractNotSatisfiedError, _assert_contract_satisfied(),
  _verify_seven_day_observation() (C7 machine check via llm_calls), per-crew
  cost_ceiling_usd in state schema, guard() enforces per-crew ceiling alongside global cap,
  set_crew_enabled(True) and set_crew_dry_run(False) both gated
- `orchestrator/contracts/__init__.py`: new (package)
- `orchestrator/contracts/TEMPLATE.md`: template for future crews
- `orchestrator/contracts/griot.md`: signed backfill contract, ceiling=$0.01
- `orchestrator/contracts/auto_publisher.md`: signed backfill contract, ceiling=$0.05
- `orchestrator/db.py`: content_approvals table (id, notion_page_id, attempt_number,
  submitted_at, decided_at, decision, evergreen, platform, griot_score, chairman_score)
- `orchestrator/griot.py`: record_content_approval(): writes to content_approvals
  on every approval decision (non-fatal on DB error)
- `orchestrator/auto_publisher.py`: _should_hold_for_timely_check(), _send_timely_recheck_telegram(),
  C13 TTL gate wired before Status=Publishing flip, TIMELY_TTL_DAYS=14
- `orchestrator/tests/test_autonomy_guard.py`: 5 new tests (21 total in file)
- `orchestrator/tests/test_crew_contracts.py`: new, 6 tests
- `orchestrator/tests/test_content_approvals.py`: new, 2 tests
- `docs/roadmap/atlas.md`: M10 session log added
- `docs/superpowers/specs/2026-04-26-autonomous-crew-contract-design.md`: spec
- Notion Content Board: Content Type select field (Evergreen=green, Timely=yellow)
- 112/113 tests pass (1 pre-existing failure unrelated to M10)
- Merged to main, pushed to origin, VPS deploy confirmed healthy

### workspace/outreach deleted

- Screenshots migrated to workspace/demo-sites/screenshots/
- No skill files referenced workspace/outreach/ (already clean)

### R55-R51 Harvest Batch

- Ran: `python orchestrator/harvest_reviewer.py robonuggets --max 5`
- Council ran 3 rounds, converged at 0.82
- R57: TAKE (Queued in Ideas DB). First gate: Blotato MCP connection test
- R56: SKIP (reversed from Take: anti-pattern blueprint)
- R59: Reference Only (downgraded: covered by existing stack)
- R60: Hold (unblocks after R57 validates MCP layer)
- R58: Reference Only (confirmed)
- Council JSON: outputs/council/2026-04-26-19-53-40.json
- Notion Harvested Recommendations DB updated with Pass 3 verdicts for all 5

### Ideas DB Audit

- 10 items marked Done (shipped and verified live)
- Practice Runner marked Done (= Baobab at baobab.boubacarbarry.com: was missed)
- N8N Workflow Adapter: rescoped to "Workflow Triage and Hybrid Orchestration" (was
  incorrectly killed; un-killed after Boubacar clarified n8n framing)
- R57 POC entry killed (duplicate merged into full R57 entry)
- 3 items corrected from Done to Reviewed (ports that were planned but not executed:
  blotato skill, prompt-best-practices, BRAND.md format)
- Google Drive Agent rescoped to conversational UX layer over gws CLI
- Domain field added to Ideas DB: agentsHQ / Catalyst Works / Studio / Personal
- 23+ records tagged with Domain
- n8n framing corrected in memory (two-step evaluation, not hard ban)
- Ideas-as-parking-lot principle locked in memory

---

## Decisions made

1. **M10 enforcement point**: ContractNotSatisfiedError in BOTH set_crew_enabled(True)
   AND set_crew_dry_run(False). The dry_run exit is the actual live-fire transition.

2. **content_approvals new row per attempt**: rejected + revised = row 1 (rejected)
   + row 2 (approved). Preserves full history for Chairman first-try rate calculation.

3. **Evergreen/Timely default**: Timely. Records without Content Type field also
   treated as Timely (safe default). Evergreen = never expires.

4. **n8n is a tool, not a ban**: Two-step evaluation: can agentsHQ do it natively?
   If yes, build there. If no, or if n8n is genuinely superior, n8n is fine.
   Reversed prior "hard rule" framing in memory.

5. **Ideas DB is a parking lot**: Never kill ideas without explicit instruction.
   Domain field scopes future Council reviews. Ideas span all of Boubacar's work,
   not just agentsHQ.

6. **Scholarship Discovery Website**: Separate future business from Baobab. Ad/subscription
   model for scholarship applicants. Not yet built. Keep as idea.

---

## What is NOT done (explicit)

- M9a VPS smoke test (Telegram approval buttons): pending Boubacar confirmation
- M9b web chat (full SSE streaming): blocked on M9a smoke test pass
- leGriot A/B test script: rubric done, models wired, script not written (~45 min)
- R57 Blotato MCP connection test: Council's first gate before any build
- Port blotato_best_practices to skills/blotato/: still in workspace/skool-harvest only
- Port prompt-best-practices.md to docs/reference/: not yet created
- Codify [entity]_BRAND.md format: not yet in docs/reference/
- Domain tags on remaining Ideas DB records not fetched in this session
- VPS orphan archive sunset: /root/_archive_20260421/: check 2026-04-28, delete if clean
- M11c (research engine rewrite): after M11b stable
- M11d (weekly model review agent): after A/B test

---

## Open questions

1. Has any prospect seen a demo site and expressed interest in the outreach
   pipeline output? (Council's standing question: answer determines R59 priority)
2. M9a smoke test: want to verify Telegram approval buttons are working live?
3. Scholarship Discovery Website: just an idea, correct? (confirmed yes, nothing built)

---

## Next session must start here

1. Check VPS orphan archive: `ssh root@72.60.209.109 "ls /root/_archive_20260421/"`
   Delete if past 2026-04-28 and nothing has broken.
2. Run M9a smoke test (optional, Boubacar decides): send a test approval via Telegram,
   verify [Approve] / [Reject] buttons work on a real approval_queue item.
3. Build the leGriot A/B test script (~45 min):
   - Run leGriot on 3 seed ideas, each against Grok-4 and Sonnet
   - Save raw outputs side-by-side, no model labels
   - Boubacar scores blind using docs/reference/legriot-quality-rubric.md
4. If A/B test validates Grok-4: proceed to M11d (weekly model review agent)
5. If A/B test says Sonnet wins: update ROLE_CAPABILITY for writer/social roles

---

## Files changed this session

```
d:/Ai_Sandbox/agentsHQ/
  orchestrator/
    autonomy_guard.py                          MODIFIED (M10 contract gate)
    db.py                                      MODIFIED (content_approvals table)
    griot.py                                   MODIFIED (record_content_approval)
    auto_publisher.py                          MODIFIED (Evergreen/Timely TTL)
    contracts/
      __init__.py                              NEW
      TEMPLATE.md                              NEW
      griot.md                                 NEW (signed)
      auto_publisher.md                        NEW (signed)
    tests/
      test_autonomy_guard.py                   MODIFIED (+5 tests)
      test_crew_contracts.py                   NEW (6 tests)
      test_content_approvals.py                NEW (2 tests)
  docs/
    roadmap/atlas.md                           MODIFIED (M10 session log)
    superpowers/specs/
      2026-04-26-autonomous-crew-contract-design.md  NEW
    handoff/
      2026-04-26-m10-contract-ideas-audit.md   NEW (this file)
  workspace/
    outreach/                                  DELETED (migrated to demo-sites/)
    demo-sites/screenshots/                    NEW (migrated screenshots)

~/.claude/projects/d-Ai-Sandbox-agentsHQ/memory/
  MEMORY.md                                    MODIFIED (pointers updated)
  project_atlas_m9_m11_state.md               MODIFIED (M10 added)
  project_harvest_loop_complete.md            MODIFIED (R55-R51 batch results)
  feedback_n8n_last_resort.md                 MODIFIED (framing corrected)
  feedback_ideas_list_purpose.md              NEW

Notion (live changes):
  Content Board: Content Type field added (Evergreen/Timely)
  Ideas DB: Domain field added; 23+ records updated (Status + Domain)
  Harvested Recommendations DB: 5 rows updated with R55-R51 Council verdicts
```

---

## Notion state

- Ideas DB (33bbcf1a): Domain field live, 23+ records tagged
- Harvested Recommendations (0e60ae9d-dc77): R60-R56 all updated with Pass 3 verdicts
- Content Board (339bcf1a): Content Type field live
- R57 Ideas entry (34ebcf1a-3029-81d6): Status=Queued, Council-approved
