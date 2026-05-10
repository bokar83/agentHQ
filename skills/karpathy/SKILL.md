---
name: karpathy
description: Apply the four Karpathy coding principles (from AGENT_SOP.md) as a structured audit of code that was just written, proposed, or reviewed. Use on-demand via /karpathy or as a gate before shipping. Outputs a scored pass/fail per principle with specific line-level callouts. Triggers on "karpathy", "karpathy audit", "four principles", "audit this code", "/karpathy".
---

# Karpathy Principles Audit

Four principles from `docs/AGENT_SOP.md`. Every piece of code must pass all four before shipping.

---

## The Four Principles

1. **Think before coding** - State assumptions. Ask when ambiguous. No code before intent is clear.
2. **Simplicity first** - Minimum code that solves the problem. No premature abstraction. No features added speculatively.
3. **Surgical changes** - Touch only what must change. Do not refactor adjacent code while fixing a bug. Do not clean up what was not broken.
4. **Goal-driven execution** - Verifiable success criteria. Checkpoints. Loop back when the result does not match the goal.

---

## Audit Protocol

For each principle, produce:

- **Status**: PASS / FAIL / WARN
- **Evidence**: Specific file, function, or line that supports the verdict
- **Action**: If FAIL or WARN, the exact change required before shipping

Run this for every piece of code proposed or reviewed in the session.

---

## Principle 1: Think Before Coding

**PASS if:**
- The intent was stated before the first edit
- Ambiguous requirements were surfaced and resolved before writing
- No code was written speculatively ("just in case")

**FAIL if:**
- Code was written before the goal was confirmed
- Assumptions were embedded silently (undeclared magic values, implicit behavior)
- The implementation answers a different question than the one asked

---

## Principle 2: Simplicity First

**PASS if:**
- The solution is the minimum code that achieves the stated goal
- No helper functions, classes, or abstractions were added beyond what the task requires
- Three similar lines were left as three lines, not collapsed into a premature abstraction

**FAIL if:**
- New abstractions were introduced for hypothetical future use
- Error handling was added for scenarios that cannot happen
- The diff is longer than the problem requires

**WARN if:**
- A second similar pattern now exists - note it, but do not abstract yet

---

## Principle 3: Surgical Changes

**PASS if:**
- Only the files and functions required by the task were touched
- Adjacent code that was "messy but working" was left alone
- No refactors, renames, or cleanups were bundled into the PR

**FAIL if:**
- Files unrelated to the task were modified
- A bug fix also included a style change, import reorder, or variable rename
- The diff contains changes that do not trace back to the stated goal

---

## Principle 4: Goal-Driven Execution

**PASS if:**
- A verifiable success criterion was defined before coding started
- The criterion was checked after the work was done (not assumed)
- If the check failed, the loop continued rather than shipping anyway

**FAIL if:**
- No explicit success criterion was stated
- Completion was claimed before running verification
- "It should work" was treated as evidence

---

## Output Format

```
KARPATHY AUDIT
==============

Principle 1 - Think Before Coding: [PASS/FAIL/WARN]
  Evidence: [specific callout]
  Action: [if FAIL/WARN]

Principle 2 - Simplicity First: [PASS/FAIL/WARN]
  Evidence: [specific callout]
  Action: [if FAIL/WARN]

Principle 3 - Surgical Changes: [PASS/FAIL/WARN]
  Evidence: [specific callout]
  Action: [if FAIL/WARN]

Principle 4 - Goal-Driven Execution: [PASS/FAIL/WARN]
  Evidence: [specific callout]
  Action: [if FAIL/WARN]

VERDICT: [SHIP / HOLD]
  If HOLD: list the specific actions required before shipping, in order.
```

---

## Rules

- SHIP requires all four principles at PASS or WARN
- A single FAIL = HOLD, no exceptions
- WARN does not block shipping but must be logged for the next session
- Do not soften a FAIL to a WARN to avoid blocking a ship
- If the code has not been reviewed yet, read it before auditing - do not audit from memory
