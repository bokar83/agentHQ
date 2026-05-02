---
owner: production
status: active
---

# tests/ - Repo-Level Test Suite

Pytest test suite for everything that lives at the repo root or spans multiple modules. Module-internal tests live in `orchestrator/tests/`.

## What lives here

| Subfolder / file | Purpose |
| --- | --- |
| `test_*.py` (root of tests/) | Unit + integration tests for repo-level concerns |
| `integration/` | End-to-end integration tests (graduated from `tmp/` 2026-05-02; e.g. test_phase1_e2e.py, test_autonomy_e2e.py) |
| `pytest_tmp2/`, `pytest_tmp/` | Pytest temp dirs (regenerable, gitignored) |

## What does NOT live here

- Module-internal tests (those go in `orchestrator/tests/`)
- Throwaway probes (those go in `sandbox/.tmp/`)
- One-off smoke tests for a deploy (those go in `scripts/` if reusable, `sandbox/` if not)
- Test data (gitignored runtime data: `data/`)

## Rules

- New e2e tests go in `tests/integration/`. Unit and module tests go flat at `tests/`.
- Tests must be runnable via `python -m pytest tests/` with no extra setup beyond `.env`.
- Permission-locked pytest temp dirs on Windows (`pytest_tmp/`, `pytest_tmp_work/`) are expected; the folder-purpose hook exempts them.

## Cross-references

- Constitution: [`docs/GOVERNANCE.md`](../docs/GOVERNANCE.md)
- Folder Governance: [`docs/AGENT_SOP.md`](../docs/AGENT_SOP.md)
- Module-internal tests: [`orchestrator/tests/`](../orchestrator/tests/)
