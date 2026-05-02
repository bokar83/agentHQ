# Fixtures for /agentshq-absorb

One row per v1 input type. Columns: `input` (literal string the user pastes) | `expected_type` (one of the types in the detection table).

## How to verify

Run `tests/verify_verdict.py --fixtures fixtures.tsv` to confirm the detection rules in SKILL.md classify each fixture correctly.

## Schema

| Column | Description |
| --- | --- |
| input | The literal input. URL, path, or pasted string. |
| expected_type | One of: repo, mcp-server, n8n-workflow, pdf, raw-doc, live-site, skill, unknown |
