# Memory Enforcement Violations Log

Append-only. One line per violation. Reviewed weekly. Tripwire for Deliverable Pre-Ship Gate (CLAUDE.md 2026-05-11).

Schema: `YYYY-MM-DD | session-id-or-name | rule-violated | how-detected | remediation`

Tripwire rule: if any violation logged in next 3 docs-shipping sessions after 2026-05-11, escalate to PreToolUse hook on Write/Edit blocking deliverable-path writes without gate output in same turn.

---

## Violations

2026-05-11 | PGA-absorb-session | feedback_html_deliverables_localhost.md + feedback_session_digest_html_email.md | Boubacar manually: "I no longer look at .md files. MD is for the agents." | Tripwire incident #0 — catalyst for the gate rule itself. Counted as historical baseline, not gate-failure.

2026-05-11 | PGA-absorb-session | (memory hygiene gap, pre-existing rule absent) | Built duplicate feedback_html_localhost_and_email_for_humans.md when 3 rules already covered | Deleted duplicate; triggered Layer 3 memory hygiene rule
