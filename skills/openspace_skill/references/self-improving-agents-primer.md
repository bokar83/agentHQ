# Self-Improving Agents Primer

**Status: HOLD — activate when Echo metric gate is live in Atlas roadmap**

Absorbed: 2026-05-10 | Verdict: ARCHIVE-AND-NOTE | Source: raw doc (pasted text)

---

## What this is

Survey of three self-improving agent architectures. Read before designing any
skill-quality eval loop or auto-repair mechanism in agentsHQ.

---

## Darwin-Gödel Machine (DGM) — Sakana AI

LLM proposes Python code changes to its own scaffold. Each variant is evaluated
against a fixed benchmark (SWE-bench). Successful variants are archived as
"stepping stones" — the system branches from them in later iterations rather
than restarting from scratch.

Performance gains: SWE-bench 20% → 50%. Polyglot 14.2% → 30.7%.

**Limitation:** Built for coding tasks only. Assumes task-execution skill equals
self-modification skill. Does not generalize across domains.

**Pattern for agentsHQ:** Stepping-stone archive. Do not discard prior skill
versions on failure — archive them as branch candidates. Requires: automated
eval metric per skill.

---

## Hyperagents / DGM-H — Meta

Merges task-agent and meta-agent into one editable program. The improvement
mechanism itself can be rewritten, not just the task logic. Uses same
open-ended evolutionary pool as DGM but allows metacognitive rewriting.

Results across domains:
- Paper review: 0.0 → 0.710 accuracy
- Robotics (quadruped): 0.060 → 0.372, beating human baseline of 0.348

**Key insight:** When the improvement mechanism is fixed (DGM), gains plateau
and are domain-specific. When the mechanism itself is editable (DGM-H), the
system can evolve its own governance.

**Pattern for agentsHQ (future):** The absorb skill and Gate protocol are
themselves candidates for metric-gated improvement — not just the skills they
govern. Do not hardcode the governance loop. Atlas M21+ territory.

---

## Autoresearch — Karpathy

Human writes `program.md` (high-level instructions in markdown). Agent edits
`train.py`. Runs 5-minute eval. Commits if metric improves; `git reset` to last
known good state if not. Loop.

Git = research memory. Discovered: increasing iteration speed beats increasing
batch size in certain contexts. Extended by Shopify for CI pipeline optimization.

**Pattern for agentsHQ (immediate):** This is structurally identical to Echo's
propose/ack loop. The missing piece: a metric that auto-approves without
Boubacar. See Echo metric gate entry in Atlas roadmap (item 15).

---

## Risks (from the article — carry forward into any eval loop design)

- **Reward hacking:** metric gaming without achieving underlying goal. Mitigation:
  multi-criterion rubrics, not single-metric optimization.
- **Local optima:** agents tweak safe hyperparameters, skip bold leaps. Mitigation:
  archive stepping stones + allow branching from non-latest variants.
- **Compute runaway:** infinite improvement loop with no exit condition. Mitigation:
  hard iteration cap + Boubacar notification on ceiling hit.
- **Security:** metric-chasing may produce insecure code or bypass safeguards.
  Mitigation: security scan runs on every proposed skill change before merge.

---

## Activation condition

This reference becomes actionable when Atlas roadmap item 15 (Echo metric gate)
is scoped with: metric name + rubric definition (3+ criteria) + gate_agent
integration point named.

Until then: read-only reference. Do not modify openspace_skill SKILL.md based
on this doc.
