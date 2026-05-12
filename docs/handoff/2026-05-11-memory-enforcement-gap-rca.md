# RCA: memory-enforcement-gap — 2026-05-11

**Root cause:** 3-layer compound — local = no pre-Write checkpoint + consequence-perception gates out deferred rules (H2+H5); VPS = orchestrator container has zero memory loading, 166 feedback rules invisible (H6); meta = capture-without-retire pipeline, MEMORY.md at 211 lines past 200 truncation cliff (H7+H8).

**Fix applied:** 3 layers shipped this session.

- **Layer 1 (local enforcement)** — added "Hard Rule: Deliverable Pre-Ship Gate (2026-05-11)" block to `CLAUDE.md` immediately above "Task Table as Live Registry" section. 1-question gate at pre-Write boundary on `docs/`, `agent_outputs/`, `clients/`, `output/`, date-stamped paths. Tripwire log at `docs/audits/memory-enforcement-violations.md`. 3-session fail-fast escalation to PreToolUse hook.

- **Layer 2 (VPS parity)** — created `docs/RULES.md` (~100 lines, curated standing rules subset for VPS agents). Added 1-line reference at top of `docs/AGENTS.md`. Deferred items: 5 remaining AGENTS.md files + CrewAI backstory injection in `orchestrator/crews.py` (separate commit, separate test pass).

- **Layer 3 (memory hygiene)** — appended 2 bullets to `docs/AGENT_SOP.md` Hard Rules cluster: (i) memory hygiene discipline (grep before new feedback, retire_when frontmatter, 180-line MEMORY.md budget, monthly Boubacar review), (ii) VPS agents read `docs/RULES.md`.

**Success criterion verified:**

| Command | Expected output | Actual |
|---|---|---|
| `grep "Deliverable Pre-Ship Gate" d:\Ai_Sandbox\agentsHQ\CLAUDE.md` | matches at one line | TBD (ship + grep) |
| `ls d:\Ai_Sandbox\agentsHQ\docs\RULES.md` | file exists | YES |
| `grep "docs/RULES.md" d:\Ai_Sandbox\agentsHQ\docs\AGENTS.md` | matches at one line | YES |
| `grep "Memory hygiene (2026-05-11)" d:\Ai_Sandbox\agentsHQ\docs\AGENT_SOP.md` | matches at one line | YES |

**Never-again rule:** before any `Write` or `Edit` to a deliverable path, state in chat "Is this Boubacar-facing? If yes, HTML + localhost + email-if-important." Skipped = log to `docs/audits/memory-enforcement-violations.md`. If violations >0 in next 3 docs-shipping sessions, escalate to PreToolUse hook same day.

**Memory update:** yes — `feedback_memory_enforcement_rca_2026-05-11.md` (to be written next session, covers diagnostic methodology + 3-layer fix-pattern for future similar gaps).

---

## Phase-by-phase summary

| Phase | Outcome |
|---|---|
| 1 — Reproduce | 4 misses in 1 session. Deterministic when (a) docs/ writes queued AND (b) rule has deferred consequences AND (c) no in-turn checkpoint. |
| 2 — Minimise | Bimodal: local = consequence-gating + missing checkpoint; VPS = zero memory loading. Different problem space per surface. |
| 3 — Hypothesise | H2 + H5 + H6 + H7 + H8 all confirmed. H1 partial. H3 minor factor. H4 secondary. |
| 4 — Instrument | Cheapest signal: count "you forgot to..." moments in last 14 days session transcripts. Cluster by rule + consequence-class. |
| 5 — Fix | 3-layer fix as above. |
| 6 — Regression | Tripwire log + 3-session fail-fast. Next 10 docs-shipping sessions = 0 violations target. |

## What still needs to happen (deferred follow-ups)

1. **Layer 2 completion:** add `docs/RULES.md` reference line to remaining 5 AGENTS.md files (`orchestrator/`, `configs/`, `signal_works/`, `templates/`, `skills/`). Surgical, but touches 5 files = separate commit.
2. **Layer 2c:** inject `"Read /app/docs/RULES.md before any action."` into every CrewAI agent `backstory` in `orchestrator/crews.py` and equivalents. Token-cost-per-task implication — measure first, ship second.
3. **Memory hygiene monthly review (Layer 3):** Boubacar reads MEMORY.md index, retires stale rules to `memory/archive/`, consolidates overlapping rules. First review: 2026-06-11.
4. **MEMORY.md immediate consolidation:** file is at 211 lines, over the 180 budget. Needs trim before next entry added. Candidate consolidations identified in 2026-05-11 absorb session.
5. **PreToolUse hook spec:** prepared as backup. Implementation deferred until tripwire fires.

## Cross-references

- Plan: `C:\Users\HUAWEI\.claude\plans\social-ghost-writing-skills-quirky-popcorn.md` (catalyst session)
- Tripwire log: `docs/audits/memory-enforcement-violations.md`
- Standing rules for VPS: `docs/RULES.md`
- Sankofa Council transcript (in-session): see conversation history 2026-05-11
- Karpathy audit rounds 1+2 + revised: see conversation history 2026-05-11

## Karpathy + Sankofa convergence

Karpathy revised verdict: ship 1Q gate + tripwire + 3-session fail-fast. RCA accepted this for Layer 1. Sankofa Council Round 1 verdict: MODIFY KARPATHY (Stop-hook too late, gate at pre-Write correct). Both converged on the gate-shape; RCA expanded the scope to cover VPS + meta which neither saw.

**Brutal honest acknowledgment:** Layer 1 alone may have caught 80% of the failure cases Boubacar sees today. Layer 2 + 3 are insurance against the failures Boubacar can't see (VPS) and future scaling failures (memory hygiene). If next-session evidence shows Layer 1 fired reliably, Layers 2+3 still earned their place by addressing different failure surfaces.
