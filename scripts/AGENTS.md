---
owner: production
status: active
---

# scripts/ - Operational Scripts

One-off and recurring operational scripts. Not imported by orchestrator.

## What lives here

- `check_no_em_dashes.py` - pre-commit hook (referenced by `.pre-commit-config.yaml` - DO NOT MOVE)
- `skool-harvester/` - Skool.com harvest scripts
- Miscellaneous utility scripts (MakeShortcut.ps1, Run-Local-SecureWatch.bat, etc.)

## Rules for LLMs working here

- **Do not move `scripts/check_no_em_dashes.py`** - the pre-commit hook path is hardcoded in `.pre-commit-config.yaml`.
- New operational scripts go here, not at repo root.
- Scripts here are for human/operator use, not for agent import.

## Cross-references

- Constitution: [`docs/GOVERNANCE.md`](../docs/GOVERNANCE.md)
- Folder Governance: [`docs/AGENT_SOP.md`](../docs/AGENT_SOP.md)
