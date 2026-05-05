# Session Handoff - Provider Switching + Atlas Circuit Breaker - 2026-05-02

## TL;DR

Started with a bare URL absorb of cc-switch (farion1231/cc-switch), a Tauri desktop GUI for managing CLI providers. Absorb verdict: PROCEED: not by installing cc-switch, but by building two independent layers it inspired: a local Python provider-switching script (Layer A/B) and an Atlas OpenRouter circuit breaker with Telegram alerting (Layer C). Both shipped, tested, deployed to VPS, and verified live. Also fixed a long-standing VPS .env bug where SMTP_PASS with spaces was silently aborting orc_rebuild.sh.

## What was built / changed

**Layer A/B: local machine:**
- `skills/switch-provider/switch_provider.py`: switches Claude Code (`~/.claude/settings.json`) and Codex (`~/.codex/config.toml`) providers atomically via os.replace(). 9 tests.
- `skills/switch-provider/providers.json`: openrouter, anthropic-official, therouter presets
- `skills/switch-provider/SKILL.md`: trigger phrases + usage
- `tests/test_switch_provider.py`: 9 tests, all passing

**Layer C: VPS orchestrator:**
- `orchestrator/provider_health.py`: provider_health Postgres table, record_failure(), record_recovery(), get_status(). RealDictCursor pattern (dict not tuple).
- `orchestrator/provider_probe.py`: run_probe() heartbeat callback, tests OpenRouter every 5 min, sends Telegram on recovery
- `orchestrator/llm_helpers.py`: circuit breaker wired into call_llm() exception handler. Re-raises after recording. Telegram alert on trip includes manual switch command.
- `orchestrator/app.py`: ensure_table() + register_wake("provider-probe", every="5m") on startup
- `tests/test_provider_probe.py`: 3 tests, all passing

**Docs + logs:**
- `docs/superpowers/specs/2026-05-02-multi-cli-provider-switching-design.md`
- `docs/reviews/absorb-log.md`: cc-switch PROCEED entry appended
- `docs/reviews/absorb-followups.md`: followup entry appended
- `docs/roadmap/atlas.md`: session log entry added (2026-05-02 evening)

**VPS fix:**
- `.env` on VPS: SMTP_PASS was unquoted (`urnh jwyo vyur qurl`), silently aborting orc_rebuild.sh at the "sourcing .env" step. Fixed by quoting: `SMTP_PASS="urnh jwyo vyur qurl"`.

## Decisions made

- **Degrade-and-alert, not auto-failover.** If OpenRouter goes down, Atlas pauses LLM calls and fires Telegram with the exact manual switch command. No silent failover to a second provider (cost risk).
- **No double-counting in probe.** `run_probe()` calls `call_llm()` which already calls `record_failure()` on exception. The probe does NOT call `record_failure()` directly.
- **RealDictCursor = dict access.** `get_local_connection()` uses RealDictCursor. All DB row access must use `row["column_name"]`, never `row[0]`. Positional indexing is unreliable across psycopg2 versions.
- **Provider-switching script has no cc-switch dependency.** providers.json is our own registry. Add new providers by editing that file directly.

## What is NOT done (explicit)

- Gemini CLI switching: OAuth-based, not API-key-based. Deferred.
- Auto-failover to second provider: rejected. Revisit after 30 days of Layer C telemetry.
- M13 (true spend visibility): not touched this session. Target 2026-05-07.
- M8 (Mission Control dashboard): not touched this session.
- Notion task DB entry for provider switching work: skipped (roadmap is the durable artifact).

## Open questions

- None blocking. All decisions made and shipped.

## Next session must start here

1. Read `docs/roadmap/atlas.md` Session Log for 2026-05-02 entry to confirm state.
2. Check provider-probe is firing: `ssh root@agentshq.boubacarbarry.com 'docker logs orc-crewai --since 10m 2>&1 | grep -i "provider.probe"'`
3. Decide: M13 (spend visibility, 2026-05-07 target) or M8 (dashboard): both are ready to start.
4. Health check routine fires automatically on 2026-05-17 at 9am MT (trig_01KHkpRpAk8huaCgNrBBexAA).

## Files changed this session

```
skills/switch-provider/
  providers.json          (new)
  switch_provider.py      (new)
  SKILL.md                (new)
tests/
  test_switch_provider.py (new, 9 tests)
  test_provider_probe.py  (new, 3 tests)
orchestrator/
  provider_health.py      (new)
  provider_probe.py       (new)
  llm_helpers.py          (modified: circuit breaker in call_llm)
  app.py                  (modified: probe registration + ensure_table)
docs/
  superpowers/specs/2026-05-02-multi-cli-provider-switching-design.md (new)
  roadmap/atlas.md        (session log appended)
  handoff/2026-05-02-provider-switching-shipped.md (this file)
  reviews/absorb-log.md   (cc-switch entry)
  reviews/absorb-followups.md (cc-switch followup)
VPS:
  ~/agentsHQ/.env         (SMTP_PASS quoted)
```
