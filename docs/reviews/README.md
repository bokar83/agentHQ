# docs/reviews/

Append-only registries for the `/agentshq-absorb` skill.

## Files

- `absorb-log.md`: master registry. One line per evaluation. Columns: date | source | verdict | placement | leverage type.
- `absorb-followups.md`: PROCEED follow-up tracker. One line per actionable PROCEED verdict. Columns: date | placement | leverage type | next action | target date.
- `absorb-self-YYYY-MM-DD.md`: one-time bootstrap audit reports of the existing skill index (created by a separate plan, not /agentshq-absorb itself).

## Rules

- Append only. Never edit a prior line.
- If a verdict is reversed, append a new line with the reversal and a back-reference to the original date.
- The registry is the audit trail. PROCEED without a corresponding follow-up entry means the skill bailed before completing.
