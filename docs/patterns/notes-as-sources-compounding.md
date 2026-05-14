# Notes-as-Sources Compounding Loop

Pattern extracted from @hooeem "you should be NotebookLM maxxing" (https://x.com/i/status/2054652562867896520), absorbed 2026-05-13. Generalized beyond NotebookLM.

## What it is

A staged knowledge-building loop where a synthesized answer becomes the input for the next layer of synthesis. Instead of asking the system one question and treating the answer as final, you:

1. Ask a narrow extraction question (inventory, framework map, claim audit).
2. Save the answer as a Note (capture layer).
3. Convert the Note into a Source (the synthesis becomes new ground truth).
4. Ask the next question grounded in your own previous synthesis plus the originals.

Each pass compresses information into structured outputs that the next pass can build on. The original sources stay available for evidence; the Notes-turned-Sources steer the structure.

## Why it matters for agentsHQ

This is the same compounding pattern that powers self-improving agent loops. It is not a NotebookLM trick.

- Atlas learning crews: a crew's output is saved, audited, then fed back as a constraint for the next crew. Same shape.
- Hermes write-loop (Compass M6 onward): Hermes proposes, Gate audits, the audit becomes a write-boundary refinement that constrains the next proposal. Same shape.
- Boubacar's absorbed-content learning loop: a raw article (this one) gets distilled to 3 patterns, the pattern doc becomes a reference, the reference shapes the next absorb decision. Same shape.
- Memory pruning: MEMORY.md entries are individual answers; the topic-file detail is the Note; the always-load zone is the Notes-as-Sources compression. Already in production.

The named pattern lets future absorbs route to existing infrastructure instead of inventing a new place for it each time.

## Three places where this pattern is already half-live

- `skills/memory/` flat-file auto-memory plus MemPalace semantic search: input layer plus reasoning layer; the capture-and-convert step is manual today.
- `skills/openspace_skill/` self-improving agent loops: explicitly modeled as recursive synthesis with an Echo-metric gate.
- `skills/notebooklm/` Notes plus Sources primitives: the actual NotebookLM mechanism that exposed the pattern.

## The Source Audit pre-step (paired pattern)

Before any synthesis run that compounds Notes back into Sources, audit the source set. Otherwise compression of weak sources produces compressed weak sources. The audit prompt that earns its place (from @hooeem UC15):

```
Conduct a rigorous Source Audit.

Create a table with:
1. Source name
2. Source type
3. Publication date if available
4. Author or organisation if available
5. Core thesis
6. Usefulness rating
7. Potential bias or weakness
8. What this source is best used for
9. Whether it should be kept, removed or used cautiously

Then identify any contradictions between sources.
```

Use against NotebookLM source sets, against MEMORY.md before a major prune, against Atlas learning-crew input bundles before a synthesis pass.

## Bridge Summary (deferred sub-pattern)

When a knowledge corpus exceeds a single context window or notebook source limit, export a dense, portable summary that can stand in for the original corpus elsewhere. Becomes relevant when Atlas memory exceeds Hermes context budget. Not active yet; named here so the pattern is findable when the limit hits.

## When NOT to use this

- Single-question lookups. Compounding adds latency. If one prompt answers the question, do not stage.
- Sources that have not passed the Source Audit. Compression of garbage equals compressed garbage.
- Producing-motion artifacts on a deadline. Use this for learning loops and memory work, not for SW audits or CW PDFs where speed beats depth.

## Review gate

If this pattern is not invoked on a real session (memory prune OR absorbed-content learning loop OR Atlas crew refactor) by 2026-06-13, archive this file to `zzzArchive/patterns-unused-2026-06/`. The pattern was theoretical, not real.
