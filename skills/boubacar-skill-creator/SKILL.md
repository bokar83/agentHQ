---
name: boubacar-skill-creator
description: Use when creating a new Claude Code skill, improving an existing skill, or capturing a repeatable workflow as a skill — specifically when working in Boubacar's agentsHQ project. Use this instead of the generic skill-creator. Triggers when user says "create a skill", "build a skill", "turn this into a skill", or "I want a skill for X".
---

# Boubacar Skill Creator

A personal, intelligent skill creator built for Boubacar Diallo (Catalyst Works). Not a generic tool — knows who you are, how you think, and when your voice should be in the skill.

## Step 1 — Pre-Session Brief

Before anything else, load identity context:

1. Read `docs/memory/user_boubacar.md` — working style, voice, tech stack
2. Read `skills/boubacar-skill-creator/patterns/instincts.json` — learned behaviors (apply any with confidence ≥ 0.75 automatically)
3. Read `skills/boubacar-skill-creator/patterns/voice-domains.json` — which domains get voice injection
4. Read `skills/boubacar-skill-creator/patterns/skill-taxonomy.json` — Boubacar's growing skill map
5. Read `skills/boubacar-skill-creator/patterns/session-tracker.json` — check `skills_since_reflection`

Greet with a brief: "I know you. Here's what I remember about how we work..." (1-3 bullet summary of top instincts, confidence ≥ 0.75 only). Keep it short.

**CHECK-IN TRIGGER:** If `skills_since_reflection` >= 3:
> "Quick check-in — I haven't done a reflection pass in [skills_since_reflection] skills. Let me surface what I've learned about how you work. Still accurate?"
> Show the top 3 instincts by confidence. Ask if they still hold.

## Step 2 — Understand Intent

Ask: what should this skill enable? If the user is already mid-workflow, extract intent from conversation history first.

Capture:
- What does it do?
- When should it trigger?
- Is this for Boubacar personally, his consulting practice, a client workflow, or a technical utility?

## Step 3 — Classify Domain

Classify into one of these domains using `voice-domains.json`:

**Voice-inject domains** (Boubacar's tone goes in):
- `consulting` — client work, frameworks, diagnostics
- `leGriot` — content, social media, storytelling
- `social-media` — LinkedIn, Instagram, Twitter workflows
- `client-facing` — anything a client sees or touches
- `personal-agents` — journal, ideas, personal ops

**Stay-technical domains** (clean, generic, no voice):
- `infrastructure` — Docker, SSH, VPS, servers
- `scripts` — Python/bash utilities
- `api-wrappers` — MCP, API integrations
- `git` — version control workflows
- `data-processing` — data transforms, ETL

**CHECK-IN TRIGGER:** If domain = voice-inject AND user hasn't explicitly mentioned tone preference:
> "This skill touches your [domain] domain. Should I write it in your leGriot voice, or keep it technical?"

## Step 4 — Draft the Skill

Write a first draft following the standard SKILL.md format:
- YAML frontmatter: `name`, `description` (use writing-skills CSO rules — description = triggering conditions only, "Use when...")
- Clear overview
- Step-by-step instructions
- Examples relevant to Boubacar's actual context (not generic)

**Apply active instincts** (confidence ≥ 0.75) automatically. Examples:
- If instinct says "prefers minimal-first-draft" → write lean, no gold-plating
- If instinct says "values Theory of Constraints framing" → structure outputs as one diagnosis + recommendations

**Voice injection** (if domain = voice-inject):
- Description: write in Boubacar's direct, diagnostic style
- Examples: use his actual domains (consulting, leGriot, agentsHQ)
- Output framing: use his language ("one bold diagnosis", "actionable recs", "build daily")
- Keep technical steps clean — voice goes in framing and tone, not mechanics

**CHECK-IN TRIGGER:** After draft is written:
> "First draft done. Does this sound like you, or does it feel generic?"

## Step 5 — Test with skill-creator

Delegate testing mechanics to the official skill-creator. Invoke it:
- Use its eval infrastructure: write 2-3 test prompts, spawn with-skill and baseline subagents
- Run benchmarking
- Launch eval viewer for review

Do NOT reinvent the wheel. The official skill-creator handles evals well. Your job is to frame the test cases in Boubacar's context — use realistic prompts from his actual domains.

## Step 6 — Iterate

Read feedback. Improve. Apply instincts to guide improvements:
- If feedback says "too verbose" → check if instinct exists; if not, note as candidate learning
- If feedback says "wrong tone" → adjust voice injection rules
- Repeat until user is satisfied

## Step 7 — Reflection Pass

After the skill is approved, spawn the reflector subagent:
Read `agents/reflector.md` for instructions.

The reflector will:
1. Analyze the session
2. Surface 1-3 candidate instincts
3. Ask user: "I noticed X. Should I remember this?"

Only store confirmed learnings. Update `instincts.json` + mirror to `docs/memory/skill_creator_learnings.md`.

After confirmed learnings are stored, update `patterns/session-tracker.json`:
- Set `skills_since_reflection` to 0
- Set `last_reflection_date` to today's date (YYYY-MM-DD)

**CHECK-IN TRIGGER (standing):** If this is the 3rd+ skill created without a reflection pass:
> "Quick check-in — I haven't done a reflection pass in a while. Let me surface what I've learned about how you work. Still accurate?"

## Step 8 — Package and Taxonomy Update

Package the skill:
```bash
python -m scripts.package_skill <path/to/skill>
```

Update `patterns/skill-taxonomy.json` — add new skill to its domain bucket.

After packaging, update `patterns/session-tracker.json`:
- Increment `skills_created_total` by 1
- Increment `skills_since_reflection` by 1
- Set `last_skill_created` to the skill name just packaged

**CHECK-IN TRIGGER:** Before packaging:
> "Before I package: anything you'd want future-you to know when using this skill?"

---

## Check-In Rules

Check-ins are short, direct, never interrupt momentum. Max one question. Wait for response before continuing.

Never fire more than one check-in per step. If multiple triggers fire at once, pick the most important one.

---

## Reference Files

- `patterns/instincts.json` — learned behaviors
- `patterns/voice-domains.json` — voice injection rules
- `patterns/skill-taxonomy.json` — skill domain map
- `patterns/session-tracker.json` — skills-since-reflection counter
- `agents/reflector.md` — post-session learning extraction
- `references/voice-guide.md` — Boubacar's voice rules in detail (read when voice injection is ON)
- `references/check-in-triggers.md` — full check-in trigger logic and priority order
