---
name: boubacar-skill-creator
description: Use when creating a new Claude Code skill, improving an existing skill, or capturing a repeatable workflow as a skill — specifically when working in Boubacar's agentsHQ project. Use this instead of the generic skill-creator. Triggers when user says "create a skill", "build a skill", "turn this into a skill", "I want a skill for X", "improve this skill", "audit this skill", or "make this a skill".
---

# Boubacar Skill Creator

A personal, intelligent skill creator built for Boubacar Barry (Catalyst Works). Not a generic tool — knows who you are, how you think, and when your voice should be in the skill.

This is the **canonical spec** for every skill in agentsHQ — both local (`~/.claude/skills/`) and repo (`agentsHQ/skills/`). All skills must conform to the architecture defined here. The `agentshq-absorb` skill's Phase 2.5 architecture audit scores skills against this file.

---

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

### Atomic section contract (mandatory — every skill, no exceptions)

Every SKILL.md must include all five sections below. A draft missing any section is incomplete and must not be handed off.

| Section | What it must contain |
|---------|----------------------|
| **Trigger** | Exact phrases or conditions that activate the skill. No vague "use when helpful." |
| **Inputs** | What the agent needs before starting (URLs, file paths, user-stated context). |
| **Procedure** | Numbered steps. Each step is one atomic action. No compound steps. |
| **Output Contract** | Exact format of what gets produced (file path, structure, length limits). |
| **Failure Modes** | Named anti-patterns this skill must not produce. At least two. |

### YAML frontmatter (required fields)

- `name`: kebab-case only, no spaces, no capitals, matches folder name
- `description`: WHAT it does + WHEN to use it. Trigger phrases users would actually say. Under 1024 chars. No XML angle brackets. The LAST sentence must enumerate explicit triggers (`Triggers on "X", "Y", "Z"`).

### YAML frontmatter (optional fields, add when relevant)

- `allowed-tools`: restrict which tools the skill may invoke (e.g. `"Bash(python:*) WebFetch"`). Add when the skill should not use all available tools.
- `compatibility`: environment requirements (product, system packages, network needs). 1-500 chars.
- `license`: MIT, Apache-2.0, etc. — only for open-source skills.
- `metadata`: custom key-value pairs — suggest `author`, `version`, `mcp-server`.

### Progressive disclosure — three levels (folder structure rule)

Always prefer files-in-folders over inlining content:

1. **YAML frontmatter** → always loaded in system prompt (keep it minimal, just enough to trigger)
2. **SKILL.md body** → loaded when skill is relevant (procedure here, not detail)
3. **`references/<topic>.md`** → linked but loaded only on demand (detailed docs, API specs, examples)

Keep SKILL.md under 5,000 words. Move detailed reference material to `references/`. This minimizes token usage while preserving depth.

### Canonical folder structure (every skill, both local + repo)

```
skill-name/
├── SKILL.md          # required — the entry point
├── references/       # optional — markdown docs loaded on demand
├── scripts/          # optional — Python/Bash executables (chmod +x)
├── agents/           # optional — sub-agent definitions (.md files for spawning)
├── patterns/         # optional — JSON state, taxonomies, learned data
├── templates/        # optional — reusable file templates
├── assets/           # optional — fonts, icons, images
└── routing-eval.jsonl  # required if skill has triggers — see Step 4.7
```

**No README.md inside the skill folder.** All docs go in SKILL.md or `references/`. README.md at the skill level is reserved for the parent `skills/` registry.

### Folder Governance (per docs/AGENT_SOP.md)

Every folder in agentsHQ has a purpose. The `skills/` tree inherits this rule:

- Every top-level skill folder MUST have a `SKILL.md` (the skill's purpose document)
- A skill folder without a working SKILL.md is a **candidate for `zzzArchive/`**
- Pre-commit hook `scripts/check_folder_purpose.py` enforces this at the repo level

A skill folder with placeholder content (e.g., `description: "indexed entrypoint"` and no procedure) violates this rule and must be deleted or rewritten.

### Apply active instincts (confidence ≥ 0.75) automatically

- If instinct says "prefers minimal-first-draft" → write lean, no gold-plating
- If instinct says "values Theory of Constraints framing" → structure outputs as one diagnosis + recommendations

### Voice injection (if domain = voice-inject)

- Description: write in Boubacar's direct, diagnostic style
- Examples: use his actual domains (consulting, leGriot, agentsHQ)
- Output framing: use his language ("one bold diagnosis", "actionable recs", "build daily")
- Keep technical steps clean — voice goes in framing and tone, not mechanics

### Writing the file

Use the Write tool directly. Do NOT dispatch Codex to write skill files — Codex runs in a sandboxed read-only environment and will fail the write. Codex is for code fixes only. Skill files = Write tool directly.

**If skill spawns subagents or has review loops:** apply `references/gates-taxonomy.md` — name every checkpoint as pre-flight / revision / escalation / abort, answer trigger/behavior/recovery for each. Never leave checkpoints implicit.

**CHECK-IN TRIGGER:** After draft is written:
> "First draft done. Does this sound like you, or does it feel generic?"

## Step 4.5 — check_resolvable (resolver validation before registration)

Before the skill is registered in `SKILLS_INDEX.md`, verify its trigger phrases don't conflict with or duplicate existing skills.

**Run this check:**

1. Read `docs/SKILLS_INDEX.md` — extract every trigger phrase already registered.
2. For each trigger phrase in the new skill draft: check if it overlaps (exact match or near-synonym) with any existing skill's triggers.
3. Check for **dead zones**: trigger phrases so vague ("use when needed", "help with X") that the LLM won't reliably route to this skill over another.

**Output — one of three verdicts:**

| Verdict | Condition | Action |
| ------- | --------- | ------ |
| **CLEAN** | No overlaps, no dead zones | Proceed to Step 4.6 |
| **CONFLICT** | ≥1 trigger phrase matches an existing skill | Rewrite the conflicting phrase to be more specific. Name the conflicting skill. |
| **DEAD ZONE** | ≥1 trigger phrase is too vague to route reliably | Replace with a more precise phrase. |

**After any CONFLICT or DEAD ZONE fix:** re-run check before proceeding.

**Why this matters:** Skills with ambiguous triggers silently fail — the LLM routes to the wrong skill or no skill. A 2-minute check here prevents weeks of wondering why a skill never fires.

## Step 4.6 — gbrain conformance audit (11-item quality gate)

Run after check_resolvable passes, before Step 5. Adapted from gbrain's `skillify check` — converts subjective "looks good" into an objective pass/fail score.

**Checklist (mark each ✅ PASS or ❌ FAIL):**

| # | Item | What to check |
|---|------|---------------|
| 1 | SKILL.md exists | File present with valid YAML frontmatter (`name`, `description`) |
| 2 | Trigger phrases real | Each trigger is a phrase a human would actually say — no vague "use when helpful" |
| 3 | Procedure numbered | Steps are numbered, each is one atomic action, no compound "and" steps |
| 4 | Output contract stated | Exact format of what gets produced (file path, structure, length limits) |
| 5 | Failure modes named | At least two anti-patterns the skill must not produce |
| 6 | SKILLS_INDEX.md entry | Skill registered with real trigger phrases, not a stub |
| 7 | No duplicate coverage | check_resolvable returned CLEAN (Step 4.5 passed) |
| 8 | Domain classified | voice-inject or stay-technical declared (Step 3 done) |
| 9 | No sentinel stubs | No placeholder text like "replace this" or "TODO" in final SKILL.md |
| 10 | Instincts applied | All instincts with confidence ≥ 0.75 reflected in the draft |
| 11 | Gates named (if spawns subagents) | Every checkpoint labeled as pre-flight / revision / escalation / abort |

**Scoring:**

- 11/11 → SHIP
- 9-10/11 → SHIP with logged WARNs (note the fails, fix next session)
- ≤8/11 → HOLD — fix fails before proceeding to Step 5

**Hard fails (auto-HOLD regardless of score):** items 1, 2, 6, 7 — a skill with no SKILL.md, vague triggers, no index entry, or duplicate coverage is broken by definition.

**Log result:** one line in the session — `gbrain-conformance: 11/11 SHIP` or list the fails.

## Step 4.7 — routing-eval.jsonl (skill quality gate)

Every skill with triggers must ship a `routing-eval.jsonl` file in its root directory. This is what `scripts/skill_eval.py` (gate) reads to decide whether the skill's description triggers reliably.

**Format** (one JSON object per line):

```jsonl
{"intent": "phrase a user would actually type", "expected": "skill-name"}
{"intent": "another likely user phrase", "expected": "skill-name"}
{"intent": "unrelated phrase", "expected": "other-skill-or-none"}
```

**Minimum:** 10 true positives (should match) + 5 true negatives (should NOT match).

**Pass threshold:** ≥80% intent → expected matches via the skill's description trigger phrases. Default in `scripts/skill_eval.py`.

**Wired enforcement:** `scripts/gate_poll.py` runs `skill_eval.py` on any READY branch touching `skills/`. Fails auto-reject the branch via Telegram. No LLM session opens on rejection.

**Verify locally before shipping:**

```bash
python scripts/skill_eval.py skills/<your-skill> --threshold 0.8
# Exit 0 = pass; exit 1 = below threshold; exit 2 = malformed/missing
```

## Step 5 — Test with skill-creator

Delegate testing mechanics to the official skill-creator. Invoke it:
- Use its eval infrastructure: write 2-3 test prompts, spawn with-skill and baseline subagents
- Run benchmarking
- Launch eval viewer for review

Do NOT reinvent the wheel. The official skill-creator handles evals well. Your job is to frame the test cases in Boubacar's context — use realistic prompts from his actual domains.

**Before packaging, report acceptance criteria across all three test types:**

1. **Trigger tests** — run 10+ queries that should trigger the skill + 5 that should not. Target: skill loads on ≥90% of relevant queries and does NOT load on unrelated ones. Report the hit rate.

2. **Functional tests** — verify the skill produces correct output end-to-end. For each use case: given input → skill executes → expected output matches. Report pass/fail per use case.

3. **Performance comparison** — run the same task with skill enabled vs. without. Compare: number of back-and-forth messages, tool calls, and tokens consumed. Report the delta.

Do not mark the skill ready for packaging until all three test types are reported. "It seemed to work" is not a passing grade.

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

## Step 8 — Package, Optimize, and Mirror

### 8a — Description optimization

The description field is the primary trigger mechanism — undertriggering is the most common failure mode. Use the official skill-creator eval machinery:

```bash
# Requires: /plugin install example-skills@anthropic-agent-skills (run once in Claude Code)
# Generate 20 trigger/no-trigger eval queries, then:
python -m scripts.run_loop \
  --eval-set <path-to-trigger-eval.json> \
  --skill-path <path-to-skill> \
  --model claude-sonnet-4-6 \
  --max-iterations 5
# Returns best_description — update SKILL.md frontmatter with it before packaging.
```

If the skill-creator plugin is not installed: run `/plugin install example-skills@anthropic-agent-skills` in Claude Code first. One-time install, persists across sessions.

### 8b — Package the skill

```bash
python -m scripts.package_skill <path/to/skill>
```

### 8c — Mirror local ↔ repo (mandatory)

Every skill must exist in BOTH `~/.claude/skills/` (local Claude Code authoring) AND `agentsHQ/skills/` (VPS-deployed CrewAI runtime). Skipping the mirror means VPS agents cannot call the skill. Skipping the local copy means Claude Code can't author updates against the same canon.

**Mirror procedure:**

```bash
# After packaging, copy the entire skill folder to the other side
cp -r ~/.claude/skills/<name>/        d:/Ai_Sandbox/agentsHQ/skills/<name>/
# Or repo → local if the canonical version lives in repo
cp -r d:/Ai_Sandbox/agentsHQ/skills/<name>/  ~/.claude/skills/<name>/

# Then commit + push
cd d:/Ai_Sandbox/agentsHQ
git add skills/<name>/
git commit -m "feat(<name>): mirror <name> skill to repo"
git push origin main

# VPS auto-pulls via gate; or manual:
ssh root@72.60.209.109 "cd /root/agentsHQ && git pull && wc -l skills/<name>/SKILL.md"
```

**Exceptions** (do NOT mirror):
- Plugin-namespaced skills (`superpowers:*`, `caveman:*`, `codex:*`) — they live under `~/.claude/plugins/`
- Skills with `description: "Agent-internal only"` — they live in repo only (Python tools, no SKILL.md procedure for Boubacar)
- Empty placeholder dirs (no SKILL.md content) — fix or delete first

### 8d — Update taxonomy + tracker

Update `patterns/skill-taxonomy.json` — add new skill to its domain bucket.

After packaging, update `patterns/session-tracker.json`:
- Increment `skills_created_total` by 1
- Increment `skills_since_reflection` by 1
- Set `last_skill_created` to the skill name just packaged

**CHECK-IN TRIGGER:** Before packaging:
> "Before I package: anything you'd want future-you to know when using this skill?"

---

## Architecture Compliance — the 6-criterion audit

When auditing existing skills (or before mirroring a skill to repo), score against these six criteria. This is what `agentshq-absorb` Phase 2.5 uses.

| # | Criterion | Method |
|---|-----------|--------|
| 1 | YAML frontmatter present (`name`, `description`) | grep `^---` block + `^name:` + `^description:` |
| 2 | Description optimized — explicit triggers as last sentence | grep `Triggers on / use when / when user says` in description |
| 3 | Progressive disclosure — sub-folders for refs/scripts/agents | dir-listing for `references/`, `scripts/`, `agents/`, `templates/` |
| 4 | Hard rules / gates marked | grep `HARD GATE / Hard rule / HARD-GATE` if applicable |
| 5 | Output / verify / failure-mode section | grep `Output Contract / Verify / Failure mode / Acceptance` |
| 6 | No going-rogue patterns | manual read — no placeholder, generic, or unstructured content |

**Aggregate scoring:**

| Bucket | Score | Action |
|--------|-------|--------|
| **CANONICAL** | 5-6/6 pass | Ship as-is |
| **MINOR DRIFT** | 3-4/6 — intentional design (e.g., agent-internal Python tools) | Acceptable; document why criterion N/A |
| **ROGUE** | ≤2/6 OR structural violation | BLOCKING — rewrite to canonical or delete |

ROGUE skills must NOT be mirrored to VPS — that propagates the drift. Fix or delete first.

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
- `references/gates-taxonomy.md` — checkpoint types for orchestration skills (pre-flight / revision / escalation / abort)
- `references/context-budget-discipline.md` — 4-tier context degradation model for multi-agent skills
