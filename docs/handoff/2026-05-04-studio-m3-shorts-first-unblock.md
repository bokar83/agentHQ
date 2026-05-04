# Session Handoff: Studio M3 Shorts-First Unblock - 2026-05-04

## TL;DR
Absorbed a YT monetization playbook, encoded it as doctrine, then fixed three
silent pipeline bugs that were blocking every video from rendering and auto-posting.
Switched the entire Studio strategy from long-form to Shorts-first (55s scripts,
1080x1920 render). Pipeline is live and should produce the first Short within
the next 30-minute tick.

## What was built / changed

- `skills/kie_media/references/channel-launch-doctrine.md` (NEW): 5-decision
  channel launch framework, 4-part formula (Hook/Value/Curiosity Gap/Loop Ending),
  Shorts path doctrine, iteration protocol. Review date 2026-08-04.
- `orchestrator/studio_qa_crew.py`: check 11 `check_four_part_formula()` added.
  `_LOOP_ENDING_PATTERNS` expanded with 11 real Sonnet phrases. Total: 11 checks.
- `orchestrator/studio_script_generator.py`: 4-part formula as HARD RULE 2.
  11 rules total in system prompt.
- `orchestrator/studio_render_publisher.py`:
  - Shorts (1080x1920) only in `_PLATFORM_SPECS`
  - `_update_notion()` now writes `Scheduled Date = today` (was missing - nothing auto-posted)
  - zoompan at target resolution, not 4K (was timing out at 120s)
  - Clip timeout raised to 600s
  - `primary_asset_url` falls back to shorts key
- `orchestrator/studio_production_crew.py`: `length_target` derived from
  `brand.target_duration_sec` - overrides stale `long (3-15m)` on queued records.
- `configs/brand_config.*.json` (x3): `target_duration_sec=55`,
  `hook_word_budget=15`, `retention_loop_interval=50`, `intro/outro=1s each`.
- `research-vault/AGENTS.md` (NEW): governance doc, was failing pre-commit hook.
- `docs/roadmap/studio.md`: M6 Channel Launch Protocol ref + session log.

## Decisions made

- **Shorts-first is the strategy.** 10M Shorts views/90 days path faster than
  4K watch hours. Long-form re-enabled only when Shorts traction proven.
- **One render format at POC.** Cost and speed. Add formats when G4 in sight.
- **4-part formula enforced at two layers**: prompt (Sonnet instruction) +
  QA gate (check 11). Not just documentation.
- **QA regex patterns must be broad**: Sonnet writes naturally, not keyword-exactly.
  Narrow patterns = silent mass failure.
- **`ScheduledDate` is required for auto-post**: Blotato publisher needs both
  `Status=scheduled` AND `Scheduled Date=today`. Never write one without the other.

## What is NOT done (explicit)

- Music vault not built (`workspace/media/music/` missing, `build_vault.py` unwritten).
- `feat/studio-m3-production` NOT merged to main. Waiting for first confirmed render.
- Long-form format disabled intentionally.
- `firstgenerationmoney_` IG account still under review (Boubacar action needed).
- Shorts/square reframe tested at render level but not validated on actual output.

## Open questions

- Does the first rendered Short look acceptable (Ken Burns + GPT Image 2 at 55s)?
- Is the ElevenLabs voice appropriate for 55s scripts vs 10min scripts?
- Should 3-5 Shorts/day cadence be enforced by heartbeat frequency or manually scheduled?

## Next session must start here

1. Check Telegram for first Short render notification (fired within 30min of session close).
2. If notification received: review Drive link, assess video quality.
3. If quality acceptable: merge `feat/studio-m3-production` to main, mark M3 SHIPPED in studio.md.
4. If no notification: `docker logs orc-crewai -tail 50 | grep -E "studio|render|error"` to diagnose.
5. After merge: M4 unblocked. Check `firstgenerationmoney_` IG review status, wire account ID to .env.

## Files changed this session

```
orchestrator/studio_qa_crew.py
orchestrator/studio_script_generator.py
orchestrator/studio_render_publisher.py
orchestrator/studio_production_crew.py
configs/brand_config.under_the_baobab.json
configs/brand_config.ai_catalyst.json
configs/brand_config.first_generation_money.json
skills/kie_media/references/channel-launch-doctrine.md  (NEW)
research-vault/AGENTS.md  (NEW)
docs/roadmap/studio.md
docs/reviews/absorb-log.md
docs/reviews/absorb-followups.md
docs/handoff/2026-05-04-absorb-security-scan-shipped.md  (prior session, staged)
docs/handoff/2026-05-04-n8n-mcp-absorb-and-automation-agency.md  (prior session, staged)
scripts/markitdown_helper.py  (prior session, staged)
skills/agentshq-absorb/fixtures/security-scan/  (prior session, staged)
skills/frontend-design/references/design-audit.md  (prior session, staged)
```

Branch: `feat/studio-m3-production` - pushed, NOT merged.
