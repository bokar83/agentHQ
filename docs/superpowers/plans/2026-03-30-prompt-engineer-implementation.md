# Prompt Engineer Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a prompt rewriting system as both a Claude Code skill (`skills/boubacar-prompts/SKILL.md`) and a Telegram-accessible orchestrator agent, both powered by the 8-step Catalyst Prompt OS algorithm.

**Architecture:** The skill is a pure markdown instruction file that Claude Code reads and follows. The orchestrator changes are three additions to existing Python files — one agent definition, one crew builder, one router entry — with no new infrastructure or tools required.

**Tech Stack:** Markdown (skill), Python 3.x, CrewAI, FastAPI (orchestrator already running)

---

## File Map

| Action | File | What it does |
| --- | --- | --- |
| Create | `skills/boubacar-prompts/SKILL.md` | Claude Code skill — full 8-step rewriting algorithm |
| Modify | `orchestrator/agents.py` | Add `build_prompt_engineer_agent()` at end of agent definitions |
| Modify | `orchestrator/crews.py` | Add `build_prompt_engineer_crew()` before `CREW_REGISTRY`, add entry to registry |
| Modify | `orchestrator/router.py` | Add `prompt_engineering` entry to `TASK_TYPES` dict |

---

## Task 1: Create the Claude Code Skill

**Files:**
- Create: `skills/boubacar-prompts/SKILL.md`

- [ ] **Step 1: Create the skill file**

Create `d:\Ai_Sandbox\agentsHQ\skills\boubacar-prompts\SKILL.md` with this exact content:

```markdown
---
name: boubacar-prompts
description: Use when improving, rewriting, or optimizing any AI prompt — agent backstories, task descriptions, system prompts, or one-off queries. Triggers on "improve this prompt", "rewrite this prompt", "make this better", "optimize this prompt", or /prompt-engineer.
---

# Prompt Engineer — Catalyst Prompt OS

Rewrite any prompt using the 8-step Catalyst Prompt OS algorithm. Works on agent backstories, task descriptions, system prompts, and one-off queries.

## How to Use

When the user provides a prompt to improve:
1. Run all 8 steps of the algorithm below on the raw prompt
2. Output the improved prompt in a copy-pasteable code block
3. Follow with a Change Summary

## The 8-Step Rewriting Algorithm

### Step 1 — Define Objective
Before rewriting, identify:
- What exact outcome must this prompt produce?
- What decision, asset, or action does it create?

This anchors every decision in the rewrite.

### Step 2 — Step-Back Thinking
Answer these three questions internally before touching a word:
1. What are the key principles of a high-quality output for this task?
2. What separates average from exceptional for this specific use case?
3. What common mistakes does this type of prompt usually produce?

Use these answers to guide the rewrite — don't just answer them, apply them.

### Step 3 — Behavior-First Role (replaces "expert")
"Expert" is a title. It tells the AI what to know, not how to show up.

Replace any "expert" role — or any role that describes knowledge without behavior — with a behavior-first role:

**Format:** `"You are a [behavior] who specializes in [domain] explaining this to [audience]."`

Behavior examples (pick the one that fits the task):
- `storyteller` — when the goal is understanding, not just information
- `diagnostician` — when the goal is identifying a root cause or constraint
- `coach` — when the goal is behavioral change or skill development
- `challenger` — when the goal is stress-testing ideas or assumptions
- `precision editor` — when the goal is structured transformation of text
- `translator` — when the goal is making complex things accessible
- `strategist` — when the goal is sequencing decisions under constraint
- `skeptic` — when the goal is finding what's wrong before it ships
- `systems thinker` — when the goal is mapping interdependencies

If an audience is not specified in the original prompt, infer it from context or omit it.

### Step 4 — Few-Shot Examples (when applicable)
If the prompt targets creative or structured output, add one ideal example inline.

Rules:
- The example must match the desired tone, length, and structure exactly
- Use a real-looking example, not a placeholder
- Skip for conversational or open-ended prompts — examples constrain too much

Format:
```
Here is an example of the output format I want:

[example]
```

### Step 5 — Task Instructions
Rewrite the task using action verbs:
- Analyze, Build, Evaluate, Recommend, Compare, Generate, Diagnose, Identify, Synthesize

Tie the output to real-world impact where possible:
- Revenue or cost saved
- Time saved
- Risk reduced or avoided

Be specific about what to produce. Avoid "don't do X" framing — state what to do instead.

### Step 6 — Output Format
Add explicit structure so the model knows exactly what to return:

Default structure:
```
1. Direct Answer
2. Reasoning (concise, structured)
3. Alternatives + Trade-offs
4. Practical Next Action
```

Override when the task calls for it:
- Technical tasks → code block + inline comments
- Comparison tasks → table
- Data tasks → JSON or structured list
- Consulting tasks → diagnosis → recommendation → next question

### Step 7 — Multi-Output + Selection Gate
Add this instruction to the prompt:

```
Generate 2–3 variations of your response. For each variation, score it on:
- Clarity (1-5)
- Depth (1-5)
- Usefulness (1-5)
- Actionability (1-5)

Select the highest-scoring variation. Then improve it once more before delivering the final output.
```

### Step 8 — Iteration Gate
End every rewritten prompt with this line:

```
After completing your output, ask yourself: what would make this response 10x more useful? Refine once before delivering.
```

---

## Output Format

After running all 8 steps, output:

**IMPROVED PROMPT:**
```
[full rewritten prompt — copy-pasteable, no truncation]
```

**CHANGE SUMMARY:**
- Role: [what changed — e.g., "expert → diagnostician who specializes in..."]
- Step-back added: [the 3 anchoring questions applied]
- Output format: [what structure was added]
- Multi-output gate: added
- Iteration gate: added
- Few-shot example: [added / not applicable]
- Other: [any other meaningful change]

---

## Example: Before and After

**Before (weak):**
```
You are an expert in marketing strategy.
Help me write a go-to-market plan for a new B2B SaaS product.
```

**After (strong):**
```
You are a strategist who specializes in B2B SaaS go-to-market execution, explaining this to a founder who has built the product but has never led a GTM motion.

STEP-BACK CONTEXT:
A strong GTM plan identifies the single ICP (ideal customer profile) constraint first — not channels, not messaging. Average plans list tactics. Exceptional plans sequence decisions: who first, why them, how to reach them, what to say, what success looks like in 90 days.

Common mistake: starting with channels instead of customer clarity.

YOUR TASK:
Build a 90-day GTM plan for a new B2B SaaS product. Structure it as:
1. ICP definition — one primary persona with job title, company size, pain trigger
2. Value proposition — one sentence that connects the pain to the outcome
3. Channel selection — top 2 channels with reasoning tied to ICP behavior
4. Outreach sequence — 3-touch sequence with actual message templates
5. Success metric — one number that defines "working" by day 90

OUTPUT FORMAT:
1. Direct Answer: the 90-day GTM plan (structured as above)
2. Reasoning: why this ICP, why these channels
3. Alternatives: what changes if ICP shifts to enterprise vs SMB
4. Next Action: the one thing to do in the next 48 hours

Generate 2–3 variations of this GTM plan. Score each on Clarity, Depth, Usefulness, Actionability (1-5 each). Select the best. Improve it once more before delivering.

After completing your output, ask yourself: what would make this response 10x more useful? Refine once before delivering.
```
```

---

## Applying This to agentsHQ Agent Files

When improving an agent's `backstory` or `goal` field in `orchestrator/agents.py`:

1. The `role` field is the behavior: make it a behavior, not a title
2. The `goal` field is the task instruction: use action verbs, tie to output
3. The `backstory` field is the context + step-back anchoring: what separates exceptional work for this agent?

Ask to write the improved text directly into the file once you've shown the rewrite.
```

- [ ] **Step 2: Verify the file was created**

```bash
ls d:/Ai_Sandbox/agentsHQ/skills/boubacar-prompts/
```

Expected output: `SKILL.md`

- [ ] **Step 3: Commit**

```bash
cd d:/Ai_Sandbox/agentsHQ
git add skills/boubacar-prompts/SKILL.md
git commit -m "feat: add boubacar-prompts skill — 8-step Catalyst Prompt OS rewriter"
```

---

## Task 2: Add Prompt Engineer Agent to agents.py

**Files:**
- Modify: `orchestrator/agents.py` (append after `build_hunter_agent()`, before end of file)

- [ ] **Step 1: Open agents.py and locate the end of agent definitions**

The last agent defined is `build_hunter_agent()` ending around line 428. The new function goes immediately after it.

- [ ] **Step 2: Add the agent function**

Append this block after `build_hunter_agent()` in `orchestrator/agents.py`:

```python
def build_prompt_engineer_agent() -> Agent:
    """Builds the Prompt Engineer agent — rewrites any prompt using Catalyst Prompt OS."""
    return Agent(
        role="Prompt Engineer — Catalyst Prompt OS",
        goal="""Take any raw prompt and rewrite it using the 8-step Catalyst Prompt OS algorithm.
        Replace title-based roles ('expert') with behavior-first roles that describe how the AI
        should show up. Add step-back thinking, explicit output format, multi-output selection gate,
        and iteration gate. Return the improved prompt with a clear change summary.""",
        backstory="""You are a precision editor who specializes in prompt architecture,
        transforming vague or underperforming instructions into high-performance prompts
        that produce monetizable outputs. You have studied thousands of AI prompts and
        know exactly what separates a prompt that produces slop from one that produces
        a deliverable worth money. You don't add fluff — you add architecture. Every rewrite
        you produce makes the AI smarter about how to show up, not just what to know.
        You apply the Catalyst Prompt OS: behavior-first roles, step-back anchoring,
        action-verb task instructions tied to real-world impact, explicit output format,
        multi-output selection gate, and an iteration gate.""",
        verbose=False,
        allow_delegation=False,
        tools=[],
        llm=get_llm("claude-sonnet", 0.4),
        max_iter=3
    )
```

- [ ] **Step 3: Add the import to the top of crews.py (preview — actual edit in Task 3)**

Note: `build_prompt_engineer_agent` must also be imported in `crews.py`. This is handled in Task 3 Step 1.

- [ ] **Step 4: Verify Python syntax**

```bash
cd d:/Ai_Sandbox/agentsHQ
python -c "from orchestrator.agents import build_prompt_engineer_agent; print('OK')"
```

If running inside Docker context on VPS, syntax check locally:
```bash
python -c "
import ast, sys
with open('orchestrator/agents.py') as f:
    ast.parse(f.read())
print('agents.py syntax OK')
"
```

Expected: `agents.py syntax OK`

- [ ] **Step 5: Commit**

```bash
git add orchestrator/agents.py
git commit -m "feat: add build_prompt_engineer_agent to agents.py"
```

---

## Task 3: Add Prompt Engineer Crew to crews.py

**Files:**
- Modify: `orchestrator/crews.py` (two changes: import + crew function + registry entry)

- [ ] **Step 1: Add import at top of crews.py**

Find this import block near the top of `orchestrator/crews.py`:

```python
from agents import (
    build_planner_agent,
    build_researcher_agent,
    build_copywriter_agent,
    build_web_builder_agent,
    build_app_builder_agent,
    build_code_agent,
    build_consulting_agent,
    build_social_media_agent,
    build_qa_agent,
    build_orchestrator_agent,
    build_agent_creator_agent,
    build_boub_ai_voice_agent,
    build_hunter_agent,
)
```

Add `build_prompt_engineer_agent,` at the end of the import list:

```python
from agents import (
    build_planner_agent,
    build_researcher_agent,
    build_copywriter_agent,
    build_web_builder_agent,
    build_app_builder_agent,
    build_code_agent,
    build_consulting_agent,
    build_social_media_agent,
    build_qa_agent,
    build_orchestrator_agent,
    build_agent_creator_agent,
    build_boub_ai_voice_agent,
    build_hunter_agent,
    build_prompt_engineer_agent,
)
```

- [ ] **Step 2: Add the crew builder function**

Find `build_voice_polisher_crew()` in `crews.py` (the function just before `CREW_REGISTRY`). Add the new crew function immediately after `build_voice_polisher_crew()` and before `CREW_REGISTRY`:

```python
def build_prompt_engineer_crew(user_request: str) -> Crew:
    """
    Crew for: prompt_engineering
    Rewrites any prompt using the 8-step Catalyst Prompt OS algorithm.
    Single-agent, no QA — the multi-output gate in the task IS the self-QA.
    """
    agent = build_prompt_engineer_agent()

    task_rewrite = Task(
        description=f"""
        Rewrite the following prompt using the Catalyst Prompt OS algorithm:

        ORIGINAL PROMPT:
        {user_request}

        Follow ALL 8 steps in sequence:

        STEP 1 — DEFINE OBJECTIVE
        Identify: what exact outcome must this prompt produce? What decision, asset, or action?

        STEP 2 — STEP-BACK THINKING
        Answer internally before rewriting:
        - What are the key principles of a high-quality output for this task?
        - What separates average from exceptional for this specific use case?
        - What common mistakes does this type of prompt usually produce?

        STEP 3 — BEHAVIOR-FIRST ROLE
        Replace any "expert" title (or knowledge-only role) with a behavior-first role:
        "You are a [behavior] who specializes in [domain] explaining this to [audience]."
        Choose behavior from: storyteller, diagnostician, coach, challenger, precision editor,
        translator, strategist, skeptic, systems thinker — whichever fits the task.

        STEP 4 — FEW-SHOT EXAMPLE (if applicable)
        If the prompt targets structured or creative output, add one ideal output example.
        Skip for conversational or open-ended prompts.

        STEP 5 — TASK INSTRUCTIONS
        Rewrite task instructions using action verbs (Analyze, Build, Evaluate, Recommend,
        Compare, Generate, Diagnose). Tie output to real-world impact: revenue, time saved,
        or risk reduced.

        STEP 6 — OUTPUT FORMAT
        Add explicit structure:
        1. Direct Answer
        2. Reasoning (concise, structured)
        3. Alternatives + Trade-offs
        4. Practical Next Action
        Override with tables, JSON, or code blocks when the task requires it.

        STEP 7 — MULTI-OUTPUT + SELECTION GATE
        Add this instruction to the prompt:
        "Generate 2-3 variations. Score each on Clarity, Depth, Usefulness, Actionability (1-5).
        Select the best. Improve it once more before final output."

        STEP 8 — ITERATION GATE
        End the rewritten prompt with:
        "After completing your output, ask yourself: what would make this 10x more useful?
        Refine once before delivering."

        YOUR OUTPUT FORMAT (mandatory, every time):

        ORIGINAL PROMPT:
        [first 200 characters of the original for reference]

        WHAT WAS IMPROVED:
        • Role: [what changed — e.g., "expert in marketing → strategist who specializes in B2B GTM"]
        • Step-back thinking: [the 3 principles applied]
        • Output format: [what structure was added]
        • Multi-output gate: added
        • Iteration gate: added
        • Few-shot example: [added / not applicable — reason]
        • Other: [any other meaningful change]

        IMPROVED PROMPT:
        [full rewritten prompt — complete, copy-pasteable, no truncation]
        """,
        expected_output=(
            "Structured response with: ORIGINAL PROMPT summary, WHAT WAS IMPROVED bullets, "
            "and IMPROVED PROMPT as a complete copy-pasteable block."
        ),
        agent=agent
    )

    return Crew(
        agents=[agent],
        tasks=[task_rewrite],
        process=Process.sequential,
        verbose=False,
        memory=False,
    )
```

- [ ] **Step 3: Add entry to CREW_REGISTRY**

Find `CREW_REGISTRY` at the bottom of `crews.py`:

```python
CREW_REGISTRY = {
    "website_crew":        build_website_crew,
    "app_crew":            build_app_crew,
    "research_crew":       build_research_crew,
    "consulting_crew":     build_consulting_crew,
    "social_crew":         build_social_crew,
    "code_crew":           build_code_crew,
    "writing_crew":        build_writing_crew,
    "agent_creator_crew":  build_agent_creator_crew,
    "voice_polisher_crew": build_voice_polisher_crew,
    "hunter_crew":         build_hunter_crew,
    "unknown_crew":        build_unknown_crew,
}
```

Add the new entry:

```python
CREW_REGISTRY = {
    "website_crew":           build_website_crew,
    "app_crew":               build_app_crew,
    "research_crew":          build_research_crew,
    "consulting_crew":        build_consulting_crew,
    "social_crew":            build_social_crew,
    "code_crew":              build_code_crew,
    "writing_crew":           build_writing_crew,
    "agent_creator_crew":     build_agent_creator_crew,
    "voice_polisher_crew":    build_voice_polisher_crew,
    "hunter_crew":            build_hunter_crew,
    "prompt_engineer_crew":   build_prompt_engineer_crew,
    "unknown_crew":           build_unknown_crew,
}
```

- [ ] **Step 4: Verify Python syntax**

```bash
python -c "
import ast
with open('orchestrator/crews.py') as f:
    ast.parse(f.read())
print('crews.py syntax OK')
"
```

Expected: `crews.py syntax OK`

- [ ] **Step 5: Commit**

```bash
git add orchestrator/crews.py
git commit -m "feat: add build_prompt_engineer_crew to crews.py"
```

---

## Task 4: Register Task Type in router.py

**Files:**
- Modify: `orchestrator/router.py` — add one entry to `TASK_TYPES` dict

- [ ] **Step 1: Add task type to TASK_TYPES**

In `orchestrator/router.py`, find `TASK_TYPES`. It ends with the `hunter_task` entry:

```python
    "hunter_task": {
        "description": "Proactive growth engine: find Utah service SMB leads, add to CRM, and draft discovery messages",
        "keywords": ["find leads", "get prospects", "utah leads", "smb prospects", "growth engine", "hunting", "outreach", "daily leads", "fill pipeline"],
        "crew": "hunter_crew",
    },
}
```

Add the new entry before the closing `}`:

```python
    "hunter_task": {
        "description": "Proactive growth engine: find Utah service SMB leads, add to CRM, and draft discovery messages",
        "keywords": ["find leads", "get prospects", "utah leads", "smb prospects", "growth engine", "hunting", "outreach", "daily leads", "fill pipeline"],
        "crew": "hunter_crew",
    },
    "prompt_engineering": {
        "description": "Rewrite, improve, or optimize an AI prompt or instruction — not general writing tasks like emails or articles",
        "keywords": ["improve this prompt", "rewrite prompt", "better prompt", "fix my prompt",
                     "prompt engineer", "make this prompt", "optimize prompt", "prompt for",
                     "write me a prompt", "improve prompt", "rewrite this prompt", "make this better"],
        "crew": "prompt_engineer_crew",
    },
}
```

- [ ] **Step 2: Verify Python syntax**

```bash
python -c "
import ast
with open('orchestrator/router.py') as f:
    ast.parse(f.read())
print('router.py syntax OK')
"
```

Expected: `router.py syntax OK`

- [ ] **Step 3: Verify router classification works for a test input**

```bash
python -c "
import sys
sys.path.insert(0, 'orchestrator')
from router import classify_task
result = classify_task('improve this prompt: you are an expert at marketing')
print(result)
"
```

Expected: `task_type` should be `prompt_engineering` with confidence > 0.75

- [ ] **Step 4: Commit**

```bash
git add orchestrator/router.py
git commit -m "feat: add prompt_engineering task type to router"
```

---

## Task 5: Deploy to VPS and Smoke Test

**Files:** None — deploy only

- [ ] **Step 1: Push to GitHub**

```bash
cd d:/Ai_Sandbox/agentsHQ
git push origin main
```

- [ ] **Step 2: Pull and rebuild on VPS**

```bash
ssh root@72.60.209.109 "cd /root/agentsHQ && git pull origin main && docker compose build orchestrator && docker compose up -d orchestrator"
```

- [ ] **Step 3: Verify orchestrator is running**

```bash
ssh root@72.60.209.109 "docker compose ps"
```

Expected: `orchestrator` status = `Up`

- [ ] **Step 4: Smoke test via curl on VPS**

```bash
ssh root@72.60.209.109 "curl -s -X POST http://localhost:8000/run \
  -H 'Content-Type: application/json' \
  -d '{\"task\": \"improve this prompt: you are an expert at marketing strategy. help me with my go to market plan.\", \"from_number\": \"test\"}' | python3 -m json.tool"
```

Expected: JSON response with `success: true`, `task_type: prompt_engineering`, and result containing `ORIGINAL PROMPT:`, `WHAT WAS IMPROVED:`, `IMPROVED PROMPT:` sections.

- [ ] **Step 5: Test via Telegram**

Send to `@agentsHQ4Bou_bot`:
```
improve this prompt: you are an expert at business consulting. analyze my company.
```

Expected Telegram reply contains all three output sections and the role has been changed from "expert" to a behavior-first role.

- [ ] **Step 6: Final commit if any hotfixes were needed**

```bash
git add -A
git commit -m "fix: prompt engineer smoke test corrections [if any]"
git push origin main
```

---

## Self-Review Against Spec

**Spec coverage check:**

| Spec requirement | Covered by |
| --- | --- |
| Skill file at `skills/boubacar-prompts/SKILL.md` | Task 1 |
| Skill runs 8-step algorithm | Task 1 Step 1 (full algorithm in SKILL.md) |
| Skill outputs improved prompt + change summary | Task 1 Step 1 (output format section) |
| `build_prompt_engineer_agent()` with behavior-first backstory | Task 2 Step 2 |
| LLM = `get_llm("claude-sonnet", 0.4)` | Task 2 Step 2 |
| No tools on agent | Task 2 Step 2 (`tools=[]`) |
| `build_prompt_engineer_crew()` single-agent crew | Task 3 Step 2 |
| Task description runs all 8 steps | Task 3 Step 2 |
| Mandatory output format (ORIGINAL / WHAT WAS IMPROVED / IMPROVED) | Task 3 Step 2 |
| `CREW_REGISTRY` updated with `prompt_engineer_crew` | Task 3 Step 3 |
| `TASK_TYPES` entry with description distinguishing from general_writing | Task 4 Step 1 |
| Keywords include all expected trigger phrases | Task 4 Step 1 |
| VPS deploy + smoke test | Task 5 |
| Zero regression (no changes to existing crews/agents) | Tasks 2-4 only add, never modify existing code |

**Placeholder scan:** No TBDs, no TODOs, no "similar to Task N" references. All code blocks are complete.

**Type consistency:** `build_prompt_engineer_agent` is the exact function name used in both `agents.py` (definition) and `crews.py` (import + call). `prompt_engineer_crew` is the exact key used in both `CREW_REGISTRY` and `router.py`.
