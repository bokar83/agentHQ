# Lead-Gen System: Start Here

**Purpose:** Brand-specific lead-generation artifacts that plug into the existing CW + SW infrastructure. Hormozi-aligned.

**Companion skill:** [skills/hormozi-lead-gen/SKILL.md](../skills/hormozi-lead-gen/SKILL.md), the brand-agnostic procedure.

**Status:** All artifacts under `templates/`, `sequences/`, `scripts/`, `metrics/` are PROPOSED. Nothing has been committed to production templates. See [../review-gate.md](../review-gate.md) for ship status. The `sent/` folder is a real-action log (LIVE, append-only).

---

## File Map

```
lead-gen-system/
├── README.md                                    (this file, start here)
├── templates/
│   ├── cold-email-v1.md                         CW T1 enhancement DIFF
│   ├── cw-t3-t4-t5-diffs.md                     CW T3 + T4 + T5 enhancement DIFFS
│   ├── warm-reactivation-v1.md                  NEW: missing warm-outreach kit (Template A + B)
│   └── lead-magnet-brief-template.md            NEW: Margin Bottleneck Diagnostic spec (build separately)
├── sequences/
│   └── follow-up-cadence.md                     8-touch cross-channel design (extends sequence_engine.py)
├── scripts/
│   └── objection-handling.md                    CW + SW objection bank (Hormozi-aligned)
├── metrics/
│   └── success-criteria.md                      Floors before ship: LTGP/CAC math, per-artifact gates
└── sent/                                        LIVE log of real outreach (append-only, never overwrite)
    └── 2026-04-30-warm-reactivation-batch-1/    First Template A test (3 LinkedIn DMs)
        ├── README.md                            Batch summary + status table
        ├── 01-brody-horton.md                   Recipient + message text + status
        ├── 02-rod-lambourne.md                  Recipient + message text + status
        ├── 03-rich-hoopes.md                    Recipient + message text + status
        └── outcomes.md                          Reply log + 24-hour verdict
```

---

## Read in This Order

1. **[../research/decision-matrix.md](../research/decision-matrix.md)**: the verdict (MERGE) and why.
2. **[../review-gate.md](../review-gate.md)**: what to review before deploying.
3. **[metrics/success-criteria.md](metrics/success-criteria.md)**: the floors that govern everything below.
4. **[templates/cold-email-v1.md](templates/cold-email-v1.md)**: the most actionable diff. Read this if you want to see "what does Hormozi-alignment actually look like for our T1?"
5. **[templates/warm-reactivation-v1.md](templates/warm-reactivation-v1.md)**: the missing channel. Read this if you want the falsifier-test artifact.
6. **[sent/2026-04-30-warm-reactivation-batch-1/](sent/2026-04-30-warm-reactivation-batch-1/)**: the live test. 3 LinkedIn DMs sent 2026-04-30, awaiting reply data.
7. **[templates/cw-t3-t4-t5-diffs.md](templates/cw-t3-t4-t5-diffs.md)**: the rest of the CW sequence enhancements.
8. **[templates/lead-magnet-brief-template.md](templates/lead-magnet-brief-template.md)**: the CW magnet that doesn't exist yet (build separately).
9. **[sequences/follow-up-cadence.md](sequences/follow-up-cadence.md)**: the cross-channel design.
10. **[scripts/objection-handling.md](scripts/objection-handling.md)**: discovery-call objection bank.

---

## Operating Rules

- **Enhance before creating new.** Every artifact here that has a corresponding production file is a DIFF, not a replacement.
- **Score before ship.** Every output runs through the Value Equation self-check. Below 7.0/10 = hold (or ship with explicit retest gate).
- **Floors are floors.** Don't soften the success-criteria after the fact.
- **Refuse anti-patterns.** See SKILL.md Section 10.
- **`sent/` is append-only.** Never overwrite. Each batch gets its own dated subfolder. Outcomes are logged as they come in.

---

## What This Is NOT

- NOT a replacement for the existing CW/SW infrastructure.
- NOT a runnable system on its own. These are specs, templates, and logs that plug into existing tooling.
- NOT committed (proposals only). The `sent/` log is the exception: it documents real, by-hand outreach.
