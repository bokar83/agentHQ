# RCA: studio pipeline (qa-failed pile + production_tick silence) -- 2026-05-14

**Subsystem:** studio production pipeline
**Reporter:** Boubacar (asked: how is studio doing this week)
**Severity:** silent rot. Pipeline appeared to publish 5 posts/wk but production_tick had returned `0 qa-passed candidates queued` for 22+ hours and 13 records sat at qa-failed with no automated recovery.

## Root cause

Three coupled defects, each individually masked the others:

1. **studio_script_generator._post_process** stripped only em-dash (U+2014) and `" -- "` (spaced double-hyphen). The QA regex `studio_qa_crew.EM_DASH_PATTERN` (`[—–]|(?:(?<=\w)--| -- )`) ALSO catches en-dash (U+2013) and `word--word` (no surrounding spaces). LLM occasionally emitted those variants. They survived `_post_process`. `check_personal_rules` rejected. Records flipped to qa-failed.

2. **studio_production_crew._fetch_qa_passed_candidates** filtered for Status=qa-passed OR Ready only. `studio_trend_scout` creates records at Status=scouted. Nothing in the codebase advanced scouted -> Ready/qa-passed automatically. Result: production_tick logged `0 qa-passed candidates queued` indefinitely. Historical 21 published records came from manual Status flips or pre-restart container memory.

3. **No silence watchdog.** production_tick reporting 0 candidates for 22+ hours produced no alert. Pipeline death would have been invisible until Boubacar noticed missing posts (estimate: 3-4 weeks given current cadence).

## Why audits missed it

- Per-record qa-failed reasons in Notion (`source_citation: factual claim without citation`) were stale. They reflected an earlier code path before commit `fa96435` (2026-05-04) added shorts-skip-citation. Re-running QA today on those drafts passes citation. Surface-level reading of QA notes pointed at the wrong bug.
- dry_run path in script_generator returns a stub `[STUB SCRIPT] {title}` that bypasses `_post_process` entirely. Initial dry-run probe falsely showed em-dash failures from the title alone, suggesting bug location at output post-processing rather than pattern coverage.
- production_tick logged silence as INFO not WARN, so daily log scanning surfaced no signal.

## Fix applied (PR fix/studio-emdash-spine, gate-merged 2026-05-14)

- `orchestrator/studio_script_generator.py:367` extended to strip all 4 dash variants (em-dash, en-dash, spaced `--`, word--word via regex).
- `orchestrator/studio_production_crew.py:_fetch_qa_passed_candidates` filter extended to include Status=scouted. Comment documents the one-pass invariant (run_production updates Status to scheduled or qa-failed on completion, so a scouted record is processed exactly once unless a human flips it back).
- `orchestrator/studio_production_crew.py:studio_production_tick` now persists pulse state to `/app/workspace/studio_pipeline_pulse.json` and posts a Telegram alert (action-required buttons per `feedback_telegram_alerts_actionable_buttons_only.md`) if candidates=0 for >90 min and no alert in last 6h.
- `orchestrator/tests/test_studio_script_generator_emdash.py` regression test covers all 4 dash variants. 5/5 pass pre-deploy.

## Operational recovery

Bulk-reset 13 qa-failed -> Ready. Production_tick triggered manually (2026-05-14 23:31 UTC). Records flowed through script -> QA pass -> voice -> scenes -> render -> Drive upload. ~2.5 min per record. UTB folktale on retry path: cta_present soft-failure, regenerated, second pass green.

## Verification

| Check | Method | Result |
|---|---|---|
| em-dash stripped | regression test (5 cases) | 5/5 PASS |
| scouted records advance | trigger production_tick, observe log | scouted records processed live, status flipped to scheduled |
| QA passed (no em-dash trip) | live log inspection | "QA passed" + "renders done" sequence on processed records |
| Silence alert wired | code review + state file path | _alert_silence wired; first fire scheduled if next 90 min returns 0 candidates |

## Success criterion (per RCA Phase 3)

`qa-failed` count drops from 13 toward 0 within next 2 hours AND `published`/`scheduled` count for 2026-05-14 + 2026-05-15 increases by >= 3.

## Engagement scraper bug (deferred)

VPS curl on 3 published YouTube videos returned views in Indonesian locale ("X tontonan"): AIC 5-12 = 14 views (Notion stored 0), AIC 5-13 = 24 views (Notion stored 24, correct), UTB Penguin = 57 views (Notion stored 0). Scraper parser misses the locale variant. Real engagement is 14-57 views per post (cold channels, week 1, no warm-up). Not blocking this RCA. Separate ticket.

## Council + Karpathy review trail

- Council premortem on initial proposal (Option E) flagged "patching debris while the pipe is broken." Killed Option E in favor of fixing the spine (scouted advancement + silence alert) alongside the dash strip.
- Karpathy audit on Option E2 identified that proposed code change duplicated existing _post_process strip and missed the actual gap. Forced re-investigation of EM_DASH_PATTERN coverage. Discovered en-dash + word--word gap. Corrected Option E2 -> single-site fix with regression test.

## Never-again rule

Any check function with a regex pattern (`EM_DASH_PATTERN`, banned-phrase pattern, etc.) MUST have a paired sanitizer that covers the same pattern set, OR the asymmetry must be documented inline as deliberate. Add a regression test asserting the sanitizer kills every input the check rejects.

## Memory updates

- `feedback_studio_pipeline_spine_dependencies.md` (new) -- spine wiring (scouted -> Ready handler implicit via filter, production_tick silence alert) is load-bearing infra that must be preserved across refactors.
- `feedback_qa_check_paired_sanitizer.md` (new) -- regex-based check in module A must have paired sanitizer in module B covering same set, or asymmetry documented.
