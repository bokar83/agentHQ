# Prompt Engineer — Design Spec
**Date:** 2026-03-30
**Status:** Approved

---

## Overview

Build a prompt rewriting system in two forms:
1. **Claude Code skill** — used during local development to improve agent backstories, task descriptions, and any prompt before deployment
2. **Orchestrator agent** — deployed on VPS, accessible via Telegram to rewrite any prompt on demand

Both share the same rewriting algorithm. The skill is the canonical definition; the agent is the deployed runtime version.

---

## The Rewriting Algorithm (Shared Core)

Source: Craig's video (behavior-first roles) + Catalyst Prompt OS v1.0

Every prompt run through this system follows 8 steps:

### Step 1 — Define Objective
- What exact outcome must this prompt produce?
- What decision, asset, or action does it create?

### Step 2 — Step-Back Thinking
Before rewriting, answer:
- What are the key principles of a high-quality output for this task?
- What separates average from exceptional?
- What common mistakes must be avoided?
Use these answers to anchor the rewrite.

### Step 3 — Behavior-First Role (replaces "expert")
- Identify the *behavior* the model should embody, not just what it knows
- Format: `"You are a [behavior] who specializes in [domain] explaining this to [audience]."`
- Behavior examples: storyteller, diagnostician, coach, challenger, precision editor, translator, strategist, skeptic, systems thinker
- If an audience is not specified, infer from context or omit
- "Expert" is a title. Behaviors are operating modes. Always use a behavior.

### Step 4 — Few-Shot Examples (when applicable)
- If the prompt targets creative or structured output, add 1 ideal example
- Example must match the desired tone, length, and structure
- Skip for conversational or open-ended prompts

### Step 5 — Task Instructions
- Rewrite task instructions using action verbs: Analyze, Build, Evaluate, Recommend, Compare, Generate, Diagnose
- Tie the output to real-world impact where possible: revenue, time saved, risk reduced
- Be specific about what to produce, not what to avoid

### Step 6 — Output Format
Add explicit structure to the prompt:
```
1. Direct Answer
2. Reasoning (concise, structured)
3. Alternatives + Trade-offs
4. Practical Next Action
```
Override with tables, JSON, or code blocks when the use case requires it.

### Step 7 — Multi-Output + Selection Gate
Instruct the model to:
1. Generate 2–3 variations of the answer
2. Evaluate each on: Clarity, Depth, Usefulness, Actionability
3. Select the best version
4. Improve it further before final output

### Step 8 — Iteration Gate
End every rewritten prompt with:
> "After your output, ask yourself: what would make this 10x better? Refine once."

---

## Part 1: Claude Code Skill

### Location
`skills/boubacar-prompts/SKILL.md`

This is a new local skill directory. Not in the community or superpowers repos — this is Boubacar's personal skill. Follows the same naming convention as `skills/boubacar-skill-creator/SKILL.md`.

### Trigger Conditions
- User pastes a prompt and says "improve this", "rewrite this prompt", "make this better", "optimize this prompt"
- User invokes `/prompt-engineer` directly

### Skill Behavior
1. Read the raw prompt provided
2. Run Steps 1–8 of the rewriting algorithm
3. Output the improved prompt in a clean, copy-pasteable code block
4. Follow with a **Change Summary** — a brief diff of what changed and why:
   - Role type changed (e.g., "expert → diagnostician")
   - Step-back thinking added
   - Output format added
   - Multi-output gate added
   - Few-shot example added (if applicable)
5. Offer to write the improved prompt directly into a specified agent file (optional, only if user asks)

### Scope
Works on any prompt type:
- Agent `backstory` and `goal` fields in `agents.py`
- Task `description` fields in `crews.py`
- System prompts for any AI tool
- One-off queries the user is about to send to Claude or another model

### Skill File Structure
```markdown
---
name: boubacar-prompts
description: Use when improving, rewriting, or optimizing any AI prompt — agent backstories, task descriptions, system prompts, or one-off queries. Triggers on "improve this prompt", "rewrite this prompt", "make this better", "optimize this prompt", or /prompt-engineer.
---

[Skill content: full 8-step algorithm + output format instructions]
```

---

## Part 2: Orchestrator Agent

### New Files Modified
| File | Change |
|---|---|
| `orchestrator/agents.py` | Add `build_prompt_engineer_agent()` |
| `orchestrator/crews.py` | Add `build_prompt_engineer_crew()`, register in `CREW_REGISTRY` |
| `orchestrator/router.py` | Add `prompt_engineering` task type + keywords |

### Agent Definition

**Function:** `build_prompt_engineer_agent()`

**Role:** `Prompt Engineer — Catalyst Prompt OS`

**Behavior-first role (applying its own algorithm):**
> "You are a precision editor who specializes in prompt architecture, transforming vague or underperforming instructions into high-performance prompts that produce monetizable outputs."

**Goal:**
Take any raw prompt and rewrite it using the 8-step Catalyst Prompt OS algorithm. Replace "expert" titles with behavior-first roles. Add step-back thinking, output format specification, multi-output gate, and iteration gate. Return the improved prompt with a change summary.

**Backstory:**
You have studied thousands of AI prompts and know exactly what separates a prompt that produces slop from one that produces a deliverable worth money. You don't add fluff — you add architecture. Every rewrite you produce makes the AI smarter about *how to show up*, not just what to know.

**LLM:** `get_llm("claude-sonnet", 0.4)` — temp 0.4 balances structured algorithm-following with fluid rewriting. Avoids 0.7+ which produces creative drift away from the 8-step structure.

**Tools:** None — prompt rewriting is pure LLM reasoning. No file saving (output goes directly to Telegram/terminal), no voice polishing (the improved prompt is a technical artifact, not content).

**max_iter:** 3

### Crew Definition

**Function:** `build_prompt_engineer_crew()`

**Structure:** Single-agent crew (no planner, no QA — prompt rewriting is self-contained and fast)

**Task description:**
```
Rewrite the following prompt using the Catalyst Prompt OS algorithm:

ORIGINAL PROMPT: {user_request}

Follow these steps:
1. Identify the objective — what must this prompt produce?
2. Step-back — what separates average from exceptional for this task?
3. Replace any "expert" role with a behavior-first role: "You are a [behavior] who specializes in [domain]..."
4. Add few-shot example if applicable
5. Rewrite task instructions with action verbs tied to real-world impact
6. Add explicit output format: Direct Answer → Reasoning → Alternatives → Next Action
7. Add multi-output gate: generate 2-3 variations, evaluate, select best, improve it
8. Add iteration gate: "After output, ask: what would make this 10x better? Refine once."

OUTPUT FORMAT (mandatory):
ORIGINAL PROMPT:
[first 200 chars of original for context]

WHAT WAS IMPROVED:
• [bullet list of specific changes made]

IMPROVED PROMPT:
[full rewritten prompt, copy-pasteable]
```

**Expected output:** Structured response with original summary, change bullets, and full improved prompt.

### Router Entry

**Task type key:** `prompt_engineering`

**Description:** `"Rewrite, improve, or optimize an AI prompt or instruction — not general writing tasks like emails or articles"`

**Keywords:**
```python
["improve this prompt", "rewrite prompt", "better prompt", "fix my prompt",
 "prompt engineer", "make this prompt", "optimize prompt", "prompt for",
 "write me a prompt", "improve prompt", "rewrite this", "make this better"]
```

**Crew:** `prompt_engineer_crew`

---

## Telegram Output Format

```
ORIGINAL PROMPT:
[first 200 chars...]

WHAT WAS IMPROVED:
• Role: "expert" → [behavior] who specializes in [domain]
• Added: step-back thinking (principles + common mistakes)
• Added: output format (Direct Answer → Reasoning → Alternatives → Next Action)
• Added: multi-output + selection gate
• Added: iteration gate ("10x better?" refinement)

IMPROVED PROMPT:
[full rewritten prompt]
```

---

## What Is NOT Built

- No memory integration (prompt rewriting is stateless — each request is independent)
- No file saving (output goes to Telegram/terminal directly, not `agent_outputs/`)
- No research step (no web search needed)
- No voice polisher pass (the improved prompt is a technical artifact, not content for Boubacar's voice)

---

## Success Criteria

1. **Skill:** Paste any prompt in the IDE → get back a rewritten version with change summary in under 30 seconds
2. **Agent:** Send "improve this prompt: [paste]" via Telegram → get structured rewrite within the normal crew timeout
3. **Quality gate:** Every rewrite must include all 8 steps applied — behavior-first role, step-back, output format, multi-output gate, iteration gate
4. **Zero regression:** All existing crews and task types unchanged

---

## Virtual Test Results (Pre-Build)

Issues found and resolved before implementation:

| # | Issue | Fix Applied |
| --- | --- | --- |
| 1 | Skill file named `prompt-engineer.md` — doesn't match `boubacar-skill-creator` convention | Renamed to `SKILL.md` in `skills/boubacar-prompts/` |
| 2 | Agent assigned `WRITING_TOOLS` — includes `SaveOutputTool` and `voice_polisher`, neither needed | Removed all tools — pure LLM reasoning task |
| 3 | Router description "Rewrite, improve, or optimize a prompt" could match `general_writing` | Added "AI prompt or instruction — not general writing" to description |
| 4 | Temperature `0.7` (creative writing) causes drift from the 8-step algorithm | Changed to `get_llm("claude-sonnet", 0.4)` |

---

## File Creation Checklist

- [ ] `skills/boubacar-prompts/SKILL.md` — skill file
- [ ] `orchestrator/agents.py` — `build_prompt_engineer_agent()` added
- [ ] `orchestrator/crews.py` — `build_prompt_engineer_crew()` added + `CREW_REGISTRY` updated
- [ ] `orchestrator/router.py` — `prompt_engineering` task type added to `TASK_TYPES`
