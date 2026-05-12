---
name: council
description: >
  Invoke the Sankofa Council on any strategic question. Five independent
  analytical voices (Contrarian, First Principles, Expansionist, Outsider,
  Executor) examine the question in parallel, review each other anonymously,
  and iterate until a Chairman synthesizes a final recommendation.
  Trigger: "council this [your question]"
---

# The Sankofa Council

Use when: you need a decision stress-tested, not validated.
Avoid when: you already know the answer and want confirmation.

## How to invoke

```
council this [your question + as much context as you can provide]
```

The more context you provide, the sharper the output.

**Premortem mode:** append `premortem this` to the query, or pass `mode="premortem"` to `SankofaCouncil.run()`. Voices speak from 6 months in the future, treating the decision as already dead. See PREMORTEM MODE section below.

## What happens

1. Five voices analyze your question independently (in parallel)
2. All outputs are anonymized and shuffled
3. Each voice reviews all five responses and answers: strongest, biggest blind spot, what all five missed
4. A Chairman synthesizes: convergence points (act on these), divergence points (name the tension), final recommendation, Monday morning next step, one open question only you can answer
5. If convergence score < 90%, voices revise and Chairman re-scores (max 3 rounds)
6. HTML report saved to outputs/council/ — shareable with clients as "Sankofa Council Review"

## When to use it

- Pricing decisions where you keep going back and forth
- Client deliverables where one wrong assumption = wrong recommendation
- Any fork in the road where the cost of being wrong is high
- Before presenting a strategy you've been living inside for too long

## What it is NOT

- Not a way to get validation — the Contrarian will find the flaw
- Not a summarizer — it produces sharper analysis than any single model
- Not a chatbot — it produces a structured verdict with a next step

## PREMORTEM MODE

**Trigger:** Append `premortem this` to the query, OR pass `mode="premortem"` to `SankofaCouncil.run()`. Engine auto-detects the trigger phrase.

**Frame shift:** It is 6 months from now. The decision is dead. Every voice speaks in retrospective past tense — not "this could fail" but "this failed, here is why."

**Per-voice retrospective mandate:**

- THE CONTRARIAN: name the chain of events that killed it. Start from the moment it became unfixable.
- THE FIRST PRINCIPLES THINKER: name the single assumption that was wrong from the start. The one nobody wrote down.
- THE OUTSIDER: describe what an outside observer saw coming that insiders ignored.
- THE EXPANSIONIST: name what was never tried that would have saved it.
- THE EXECUTOR: name the earliest warning sign that was visible but ignored, and the exact week it appeared.

**When to use:** any decision involving money, time commitment, hiring, launching, or irreversible resource allocation. Mirrors Sankofa skill's DEAD-PROJECT MODE.

## Running it in this session

To invoke the council directly from this Claude Code session:

```python
import sys
sys.path.insert(0, 'd:/Ai_Sandbox/agentsHQ/orchestrator')

from dotenv import load_dotenv
load_dotenv('d:/Ai_Sandbox/agentsHQ/infrastructure/.env')

from council import SankofaCouncil

council = SankofaCouncil()
result = council.run(
    query="YOUR QUESTION HERE",
    context="RELEVANT CONTEXT HERE",
    task_type="consulting_deliverable"
)

print(result["chairman_synthesis"])
print("\nNext step:", result["next_step"])
print("\nOpen question:", result["open_question"])
print("\nHTML report:", result["html_file_path"])
```
