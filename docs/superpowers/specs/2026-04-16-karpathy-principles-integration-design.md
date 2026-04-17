---
title: Karpathy Coding Principles — CLAUDE.md Integration
date: 2026-04-16
status: approved
---

## Summary

Integrate four behavioral coding principles from the Karpathy Skills CLAUDE.md
(https://raw.githubusercontent.com/forrestchang/andrej-karpathy-skills/main/CLAUDE.md)
into the agentsHQ project CLAUDE.md as a new section. These principles apply
globally: every session, every task type, every target environment (local,
orchestrator, VPS).

## Sankofa Council Verdict

All four principles pass the gate: agents need them now, they reinforce existing
rules, none conflict with current setup. No kills.

## Principles Being Added

1. **Think Before Coding** — State assumptions explicitly. If uncertain, ask.
   Present multiple interpretations rather than guessing. Clarifying questions
   come before mistakes, not after.

2. **Simplicity First** — Minimum code that solves the problem. Nothing
   speculative. No unrequested features, no premature abstractions, no
   speculative error handling. If a senior engineer would call it overcomplicated,
   it is.

3. **Surgical Changes** — Touch only what must be touched. Preserve existing
   style. Clean up only your own mess. Do not refactor pre-existing dead code or
   rename things unrelated to the current task.

4. **Goal-Driven Execution** — Convert every task into verifiable success
   criteria with an explicit plan. Use checkpoints throughout. Loop back to
   verify each checkpoint before moving on.

## Placement in CLAUDE.md

New section inserted between "Writing Style" and "Permissions":

```
## Writing Style — Hard Rules
   (existing content, untouched)

## Coding Principles (Karpathy)      <-- NEW
   (four principles)

## Permissions
   (existing content, untouched)
```

No existing section is modified, reordered, or removed.

## Scope of Effect

CLAUDE.md is loaded as project instructions into every session. These principles
therefore apply to:

- All orchestrator code changes
- All skill builds and rewrites
- All VPS deploys and SCP operations
- All UI/frontend work
- All agent crew builds
- All Notion, Drive, and integration work

They are session-wide behavioral constraints, not workflow-specific hooks.

## Delivery Steps

1. Write spec doc (this file) and commit.
2. Edit local CLAUDE.md: insert new section, nothing else.
3. SCP updated CLAUDE.md to VPS at 72.60.209.109.
4. Git push from VPS to keep repo in sync.
5. Read back final CLAUDE.md and confirm all four principles are active.

## Spec Self-Review

- No placeholders or TBDs.
- No internal contradictions.
- Scope is tight: one new section, no other changes.
- All requirements are unambiguous.
