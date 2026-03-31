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
