# Hermes skill write-boundary expansion (M7) -- status

Companion status file to `hermes-skill-write-boundary-expansion.md`. The
parent decision doc captured the 5 open questions; this file captures
how each one resolved on 2026-05-15 and the migration trail.

## M7 status update (2026-05-15)

All 5 Boubacar decisions resolved with recommended defaults:
  1. Gate-review-only (no per-PR Telegram gate)
  2. Markdown only (data/*.json deferred to Phase 5)
  3. Per-skill allowlist: ctq-social, client-intake, library, boubacar-prompts
  4. Rate limit: 3 auto-wires per 24h America/Denver
  5. ALLOWED rows verbatim approved

Migration plan executed in 3 companion branches landing today:
  - feat/hermes-boundary-expand-2026-05-15 (CLAUDE.md ALLOWED expansion)
  - feat/hermes-boundary-enforce-2026-05-15 (scripts/check_hermes_write_boundary.py + tests + pre-commit wiring)
  - feat/absorb-auto-wire-crew-2026-05-15 (orchestrator/absorb_auto_wire.py + migration 011)

Phase 5 (data/*.json inclusion + per-skill allowlist expansion) re-opens after 30+ shipped auto-wires + zero incidents.
