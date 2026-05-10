---
name: boubacar-prompts
description: Use when improving, rewriting, or optimizing any AI prompt — agent backstories, task descriptions, system prompts, or one-off queries. Triggers on "improve this prompt", "rewrite this prompt", "make this prompt better", "optimize this prompt", or /prompt-engineer.
---

# Prompt Engineer — Catalyst Prompt OS

Rewrite any prompt using the 8-step Catalyst Prompt OS algorithm. Works on agent backstories, task descriptions, system prompts, and one-off queries.

## How to Use

If the user has not yet provided a prompt, ask: "Paste the prompt you'd like me to improve."

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

[write one concrete example that matches the desired tone, length, and structure — use realistic content, not placeholder text]
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

---

---

## Named Template: viral-postmortem

**Trigger:** invoke as `/viral-postmortem` or "run viral postmortem on this draft"

**Purpose:** Forces exact-line citations before final approval. Cannot hide behind generic praise ("strong hook", "great insight"). If the model cannot point at a line, that is the row to fix.

**When to use:** After ctq-social Pass 2, before final ship decision. Also useful after a post performs well -- run it retroactively to extract what actually worked for the hook bank.

```
ROLE
You are reading a post that already crossed 1M views and 10K bookmarks one week from now.
You are not writing it. You are explaining, after the fact, why it landed.

INPUT
[paste draft here]

PROCESS
1. Read the draft.
2. Point at specific lines that did the work.
3. Name the hook move.
4. Name the proof that made it credible.
5. Name the line a reader would screenshot.
6. Name the line that made it save-worthy.
7. Name the line that would make someone reply or send it to a friend.

OUTPUT FORMAT
- hook move: [exact line] (why it works)
- credibility: [exact line] (why a reader believes it)
- screenshottable line: [exact line]
- save-worthy line: [exact line]
- reply or share trigger: [exact line]
- weakest part: [exact line] (what to fix before shipping)

RULES
- Do not say "great post". Do not say "strong hook". Point at specific lines or admit you cannot.
- If you cannot point at a line for any category above, say so plainly. That is the row to fix.
- The model cannot hide behind generic praise. Force it to point at mechanics.
```

**What to do with the output:** Any category where the model writes "cannot identify a line" = that is a gap in the draft. Fix that gap before shipping. The weakest part line is always the edit target.

---

## Applying This to agentsHQ Agent Files

When improving an agent's `backstory` or `goal` field in `orchestrator/agents.py`:

1. The `role` field is the behavior: make it a behavior, not a title
2. The `goal` field is the task instruction: use action verbs, tie to output
3. The `backstory` field is the context + step-back anchoring: what separates exceptional work for this agent?

Ask to write the improved text directly into the file once you've shown the rewrite.
