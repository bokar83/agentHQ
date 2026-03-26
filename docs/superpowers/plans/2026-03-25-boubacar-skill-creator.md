# boubacar-skill-creator Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Complete, install, and live-test `boubacar-skill-creator` — a personal skill creator that knows Boubacar's voice, learns from every session, and injects identity only where it differentiates.

**Architecture:** Three-layer skill: Identity Layer (loads profile + instincts), Orchestration Layer (SKILL.md workflow with check-ins + voice injection), Mechanics Layer (delegates evals/benchmarking to official skill-creator). Learning persists in two places: `patterns/instincts.json` (portable) + `docs/memory/skill_creator_learnings.md` (fast-load).

**Tech Stack:** Claude Code skills (SKILL.md), JSON data files, Markdown reference files, official skill-creator Python scripts (eval/benchmark/description optimizer), bash for installation.

---

## File Map

| Status | File | Purpose |
|--------|------|---------|
| ✅ Exists (needs polish) | `skills/boubacar-skill-creator/SKILL.md` | Main orchestration skill |
| ✅ Exists | `skills/boubacar-skill-creator/patterns/instincts.json` | Confidence-scored learned behaviors |
| ✅ Exists | `skills/boubacar-skill-creator/patterns/voice-domains.json` | Voice injection rules |
| ✅ Exists | `skills/boubacar-skill-creator/patterns/skill-taxonomy.json` | Boubacar's growing skill map |
| ✅ Exists | `skills/boubacar-skill-creator/agents/reflector.md` | Post-session learning subagent |
| 🔲 Create | `skills/boubacar-skill-creator/patterns/session-tracker.json` | Tracks skills-since-last-reflection |
| 🔲 Create | `skills/boubacar-skill-creator/references/voice-guide.md` | Full leGriot voice rules |
| 🔲 Create | `skills/boubacar-skill-creator/references/check-in-triggers.md` | Complete check-in trigger reference |
| 🔲 Create | `docs/memory/skill_creator_learnings.md` | Mirrored instincts index for fast-load |
| 🔲 Modify | `skills/boubacar-skill-creator/SKILL.md` | Add session counter, CSO polish, voice-guide reference |
| 🔲 Install | `~/.claude/skills/boubacar-skill-creator/` | Live installation |
| 🔲 Optimize | SKILL.md description | Run description optimizer for trigger accuracy |

---

## Task 1: Create `references/voice-guide.md`

**Files:**
- Create: `skills/boubacar-skill-creator/references/voice-guide.md`

- [ ] **Step 1: Write voice-guide.md**

Create `skills/boubacar-skill-creator/references/voice-guide.md` with this exact content:

```markdown
# Boubacar's Voice Guide (leGriot)

Reference this file when voice injection is ON (domain = voice-inject). Apply these rules to skill description, output framing, and examples — not to technical steps.

## Core Identity

Boubacar is the founder of Catalyst Works Consulting. His public voice ("leGriot") is a consulting practitioner who builds daily, thinks in systems, and speaks directly.

## Voice Rules

### What leGriot sounds like
- Direct and diagnostic — names the problem, doesn't dance around it
- One bold diagnosis, then actionable recommendations — not "it depends"
- Uses Theory of Constraints thinking: find the one constraint, don't list 12 problems
- Builds daily — urgency is real, not performative ("deploy this today, not next week")
- Platforms: LinkedIn first, then Instagram, then Twitter (always this order)

### What leGriot never does
- NEVER fabricates stories or invents examples — signals hypotheticals as "Imagine if..."
- NEVER adds a closing call-to-action ("Follow me for more", "Drop a comment below")
- NEVER uses consulting jargon clients have to decode
- NEVER gives wishy-washy multi-answer endings
- NEVER opens with a generic statement — prefers to open with a question or a bold claim

### Preferred opening structures
1. Open with a question: "What if the bottleneck isn't where you think it is?"
2. Open with a bold claim: "Most consulting engagements fail before they start."
3. Never open with "In today's fast-paced world..." or any variant of it

### Output format preferences
- Short over long — if it can be said in half the words, use half
- 2 examples max in any skill — not a library
- One-page deliverables where possible
- Structure: Diagnosis → Evidence → Next Steps (not: Background → Analysis → Conclusion → Appendix)

## Applying Voice in Skills

**In the SKILL.md description:**
Write in Boubacar's direct style. Not "Use when analyzing organizational challenges" — use "Use when diagnosing a client bottleneck and you need a clear answer fast."

**In examples:**
Use his real domains: consulting clients, Catalyst Works, agentsHQ, leGriot content. Not "Acme Corp" or "Company X."

**In output format guidance:**
Frame deliverables the way Boubacar would — "one-page diagnosis," "three moves," "deploy by end of session."

**Technical steps stay clean:**
Voice injection applies to framing and tone. Step-by-step instructions inside a skill remain clear and instructional regardless of domain.
```

- [ ] **Step 2: Verify file exists and content is correct**

```bash
cat "D:\Ai_Sandbox\agentsHQ\skills\boubacar-skill-creator\references\voice-guide.md" | head -5
```

Expected: first line is `# Boubacar's Voice Guide (leGriot)`

- [ ] **Step 3: Commit**

```bash
cd "D:\Ai_Sandbox\agentsHQ" && git add skills/boubacar-skill-creator/references/voice-guide.md && git commit -m "feat: add voice-guide reference for boubacar-skill-creator"
```

---

## Task 2: Create `references/check-in-triggers.md`

**Files:**
- Create: `skills/boubacar-skill-creator/references/check-in-triggers.md`

- [ ] **Step 1: Write check-in-triggers.md**

Create `skills/boubacar-skill-creator/references/check-in-triggers.md` with this exact content:

```markdown
# Check-In Trigger Reference

Full logic for when and how check-ins fire in boubacar-skill-creator.

## Rules

1. Max ONE check-in per step — if multiple triggers fire simultaneously, use the priority order below
2. Check-ins are one question only — wait for response before continuing
3. Never interrupt mid-draft — check-ins fire between steps, not inside them
4. All check-in responses may trigger a learning candidate — note them for the reflector pass

## Trigger Table (Priority Order)

| Priority | Trigger Condition | Check-In Message | When It Fires |
|----------|------------------|-----------------|---------------|
| 1 | Domain = voice-inject AND tone not stated by user | "This skill touches your [domain] domain. Should I write it in your leGriot voice, or keep it technical?" | Step 3 (domain classification) |
| 2 | Stored instinct contradicted by current approach | "You usually [instinct observation]. This skill does [different thing] — intentional?" | Step 4 (during draft) |
| 3 | First draft written | "First draft done. Does this sound like you, or does it feel generic?" | End of Step 4 |
| 4 | session-tracker.json shows skills_since_reflection >= 3 | "Quick check-in — I haven't done a reflection pass in a while. Let me surface what I've learned about how you work. Still accurate?" | Step 1 (pre-session brief) |
| 5 | Before packaging | "Before I package: anything you'd want future-you to know when using this skill?" | Step 8 (before package command) |

## What NOT to Do

- Do not fire check-in #3 if check-in #1 already fired in the same step
- Do not fire check-in #4 if the user just completed a reflection pass this session
- Do not combine check-ins into one message with multiple questions
- Do not use check-ins as a way to stall — if the answer is obvious from context, skip the check-in

## After a Check-In Response

Always process the response before continuing. If the response:
- Confirms current direction → continue
- Redirects → adjust draft accordingly, note as candidate learning for reflector
- Reveals a new preference not in instincts.json → note explicitly for reflector pass
```

- [ ] **Step 2: Verify file**

```bash
cat "D:\Ai_Sandbox\agentsHQ\skills\boubacar-skill-creator\references\check-in-triggers.md" | head -5
```

Expected: first line is `# Check-In Trigger Reference`

- [ ] **Step 3: Commit**

```bash
cd "D:\Ai_Sandbox\agentsHQ" && git add skills/boubacar-skill-creator/references/check-in-triggers.md && git commit -m "feat: add check-in-triggers reference for boubacar-skill-creator"
```

---

## Task 3: Create `patterns/session-tracker.json`

The session tracker tells the skill how many skills have been created since the last reflection pass. This enables check-in trigger #4 (fire at 3+ skills without reflection).

**Files:**
- Create: `skills/boubacar-skill-creator/patterns/session-tracker.json`

- [ ] **Step 1: Write session-tracker.json**

Create `skills/boubacar-skill-creator/patterns/session-tracker.json` with this exact content:

```json
{
  "skills_created_total": 0,
  "skills_since_reflection": 0,
  "last_reflection_date": null,
  "last_skill_created": null
}
```

- [ ] **Step 2: Verify file**

```bash
cat "D:\Ai_Sandbox\agentsHQ\skills\boubacar-skill-creator\patterns\session-tracker.json"
```

Expected: valid JSON with `skills_since_reflection: 0`

- [ ] **Step 3: Commit**

```bash
cd "D:\Ai_Sandbox\agentsHQ" && git add skills/boubacar-skill-creator/patterns/session-tracker.json && git commit -m "feat: add session-tracker for reflection check-in trigger"
```

---

## Task 4: Create `docs/memory/skill_creator_learnings.md`

This is the mirrored fast-load instincts index. It's loaded via MEMORY.md so future sessions see learnings without reading the full instincts.json.

**Files:**
- Create: `docs/memory/skill_creator_learnings.md`
- Modify: `docs/memory/MEMORY.md`

- [ ] **Step 1: Write skill_creator_learnings.md**

Create `docs/memory/skill_creator_learnings.md` with this content:

```markdown
---
name: skill_creator_learnings
description: Active instincts learned by boubacar-skill-creator. Auto-updated after each confirmed reflection pass.
type: project
---

# Skill Creator — Active Learnings

Instincts with confidence ≥ 0.75 (applied automatically in skill creation):

| ID | Domain | Observation | Confidence |
|----|--------|-------------|------------|
| prefers-minimal-first-draft | all | Start lean. Minimal first draft, expand only when asked. | 0.80 |
| build-daily-cadence | all | Skills must be deployable same-session. No multi-day builds. | 0.90 |
| theory-of-constraints-framing | consulting | One bold diagnosis + actionable recommendations. No "it depends" endings. | 0.85 |
| no-fabrication | leGriot | NEVER fabricates stories. Hypotheticals signaled as "Imagine if..." | 1.00 |
| telegram-preferred | personal-agents | Default to Telegram for personal agent outputs, not WhatsApp. | 0.90 |

Instincts with confidence < 0.75 (surface as suggestions, not applied automatically):

*None yet.*

---

*This file is auto-maintained by boubacar-skill-creator's reflector subagent.*
*Full instinct data: `skills/boubacar-skill-creator/patterns/instincts.json`*
```

- [ ] **Step 2: Add pointer to MEMORY.md**

Read `docs/memory/MEMORY.md`, then add this line under the `## Feedback` section:

```markdown
## Skill Creator

- [skill_creator_learnings.md](skill_creator_learnings.md) — active instincts applied during skill creation sessions
```

- [ ] **Step 3: Verify MEMORY.md updated**

```bash
cat "D:\Ai_Sandbox\agentsHQ\docs\memory\MEMORY.md"
```

Expected: contains `skill_creator_learnings.md` entry.

- [ ] **Step 4: Commit**

```bash
cd "D:\Ai_Sandbox\agentsHQ" && git add docs/memory/skill_creator_learnings.md docs/memory/MEMORY.md && git commit -m "feat: add skill_creator_learnings to memory index"
```

---

## Task 5: Polish `SKILL.md`

The draft SKILL.md from simulation is solid but needs three improvements:
1. Description needs CSO polish (third-person, "Use when...", no workflow summary)
2. Step 1 needs to read session-tracker.json and check-in if skills_since_reflection >= 3
3. Step 7 needs to update session-tracker.json after reflection completes
4. Step 8 needs to update session-tracker.json after packaging

**Files:**
- Modify: `skills/boubacar-skill-creator/SKILL.md`

- [ ] **Step 1: Update the YAML frontmatter description**

Replace the current description in the frontmatter:

Old:
```yaml
description: Use when Boubacar wants to create a new Claude Code skill, improve an existing skill, or capture a workflow as a reusable skill. Knows Boubacar's voice, style, and working patterns. Gets smarter with each skill created. Use this instead of the generic skill-creator when working in this project.
```

New:
```yaml
description: Use when creating a new Claude Code skill, improving an existing skill, or capturing a repeatable workflow as a skill — specifically when working in Boubacar's agentsHQ project. Use this instead of the generic skill-creator. Triggers when user says "create a skill", "build a skill", "turn this into a skill", or "I want a skill for X".
```

- [ ] **Step 2: Update Step 1 to read session-tracker and fire check-in**

In SKILL.md, find Step 1 (Pre-Session Brief) and replace it with this version:

```markdown
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
```

- [ ] **Step 3: Update Step 7 to reset session-tracker after reflection**

Find Step 7 (Reflection Pass) and add at the end:

```markdown
After confirmed learnings are stored, update `patterns/session-tracker.json`:
- Set `skills_since_reflection` to 0
- Set `last_reflection_date` to today's date (YYYY-MM-DD)
```

- [ ] **Step 4: Update Step 8 to increment session-tracker after packaging**

Find Step 8 (Package and Taxonomy Update) and add at the end:

```markdown
After packaging, update `patterns/session-tracker.json`:
- Increment `skills_created_total` by 1
- Increment `skills_since_reflection` by 1
- Set `last_skill_created` to the skill name just packaged
```

- [ ] **Step 5: Add reference to voice-guide.md and check-in-triggers.md in the Reference Files section**

The current Reference Files section already lists `references/voice-guide.md`. Verify it also lists `references/check-in-triggers.md`. If not, add it:

```markdown
## Reference Files

- `patterns/instincts.json` — learned behaviors
- `patterns/voice-domains.json` — voice injection rules
- `patterns/skill-taxonomy.json` — skill domain map
- `patterns/session-tracker.json` — skills-since-reflection counter
- `agents/reflector.md` — post-session learning extraction
- `references/voice-guide.md` — Boubacar's voice rules in detail (read when voice injection is ON)
- `references/check-in-triggers.md` — full check-in trigger logic and priority order
```

- [ ] **Step 6: Commit**

```bash
cd "D:\Ai_Sandbox\agentsHQ" && git add skills/boubacar-skill-creator/SKILL.md && git commit -m "feat: polish SKILL.md — CSO description, session tracker, reference files"
```

---

## Task 6: Install to `~/.claude/skills/`

The skill must be installed to Claude Code's skills directory to be active.

**Files:**
- Install: `~/.claude/skills/boubacar-skill-creator/` (copy from project)

- [ ] **Step 1: Check if skills directory exists**

```bash
ls "C:\Users\HUAWEI\.claude\skills" 2>/dev/null || echo "Directory does not exist"
```

If it doesn't exist, create it:
```bash
mkdir -p "C:\Users\HUAWEI\.claude\skills"
```

- [ ] **Step 2: Copy skill to Claude skills directory**

```bash
cp -r "D:\Ai_Sandbox\agentsHQ\skills\boubacar-skill-creator" "C:\Users\HUAWEI\.claude\skills\boubacar-skill-creator"
```

- [ ] **Step 3: Verify installation**

```bash
ls "C:\Users\HUAWEI\.claude\skills\boubacar-skill-creator"
```

Expected output: `SKILL.md  agents/  patterns/  references/`

- [ ] **Step 4: Verify SKILL.md is readable at install location**

```bash
head -5 "C:\Users\HUAWEI\.claude\skills\boubacar-skill-creator\SKILL.md"
```

Expected: YAML frontmatter with `name: boubacar-skill-creator`

---

## Task 7: Run Description Optimizer

The description field controls whether Claude invokes the skill. Use the official skill-creator's `run_loop.py` to optimize it for triggering accuracy.

**Files:**
- Modify: `~/.claude/skills/boubacar-skill-creator/SKILL.md` (description field)

- [ ] **Step 1: Create trigger eval set**

Create `D:\Ai_Sandbox\agentsHQ\skills\boubacar-skill-creator-workspace\trigger-eval.json`:

```json
[
  {"query": "I want to create a skill that helps me run my leGriot content workflow on LinkedIn", "should_trigger": true},
  {"query": "build me a skill for my client diagnostic process — the bottleneck analysis I do at kickoff", "should_trigger": true},
  {"query": "turn this n8n workflow into a reusable skill so I can call it from other agents", "should_trigger": true},
  {"query": "I keep doing this Telegram notification thing manually, let's make it a skill", "should_trigger": true},
  {"query": "create a skill for onboarding new consulting clients into my agentsHQ system", "should_trigger": true},
  {"query": "I want a skill that wraps the Airtable MCP so I don't have to remember all the steps", "should_trigger": true},
  {"query": "make a skill for my weekly review — the one where I check VPS health, n8n status, and git log", "should_trigger": true},
  {"query": "capture what we just did as a reusable skill for future sessions", "should_trigger": true},
  {"query": "how do I improve an existing skill that's not triggering correctly", "should_trigger": true},
  {"query": "can you look at my social-media skill and make it better", "should_trigger": true},
  {"query": "write a python script to parse my n8n export JSON", "should_trigger": false},
  {"query": "what's the git status on this branch", "should_trigger": false},
  {"query": "help me debug why my CrewAI agent is looping", "should_trigger": false},
  {"query": "review the PR I just opened on GitHub", "should_trigger": false},
  {"query": "write a commit message for these changes", "should_trigger": false},
  {"query": "explain how the orchestrator on my VPS works", "should_trigger": false},
  {"query": "I need to add error handling to my n8n webhook", "should_trigger": false},
  {"query": "create a new table in Supabase for tracking client sessions", "should_trigger": false},
  {"query": "what's the best way to structure a CrewAI task for research", "should_trigger": false},
  {"query": "run the existing skill-creator to optimize this skill's description", "should_trigger": false}
]
```

- [ ] **Step 2: Run the description optimizer**

Find the skill-creator path:
```bash
ls "C:\Users\HUAWEI\.claude\plugins\cache\claude-plugins-official\skill-creator\b10b583de281\skills\skill-creator\scripts\"
```

Run the optimizer (replace `<model-id>` with `claude-sonnet-4-6`):
```bash
cd "C:\Users\HUAWEI\.claude\plugins\cache\claude-plugins-official\skill-creator\b10b583de281\skills\skill-creator" && python -m scripts.run_loop \
  --eval-set "D:\Ai_Sandbox\agentsHQ\skills\boubacar-skill-creator-workspace\trigger-eval.json" \
  --skill-path "C:\Users\HUAWEI\.claude\skills\boubacar-skill-creator" \
  --model claude-sonnet-4-6 \
  --max-iterations 5 \
  --verbose
```

This runs in background. Check output periodically with:
```bash
# The script outputs to stdout — run with nohup if needed, or watch terminal
```

- [ ] **Step 3: Apply best description**

When optimizer completes, it returns `best_description` in the JSON output. Apply it to SKILL.md frontmatter in BOTH locations:
- `D:\Ai_Sandbox\agentsHQ\skills\boubacar-skill-creator\SKILL.md`
- `C:\Users\HUAWEI\.claude\skills\boubacar-skill-creator\SKILL.md`

Show before/after to user and report test vs. train scores.

- [ ] **Step 4: Commit optimized description**

```bash
cd "D:\Ai_Sandbox\agentsHQ" && git add skills/boubacar-skill-creator/SKILL.md && git commit -m "feat: apply optimized trigger description from run_loop"
```

---

## Task 8: Live Smoke Test

Create one real skill using the newly installed `boubacar-skill-creator` to confirm it behaves as designed.

- [ ] **Step 1: Start a new session and invoke the skill**

In a fresh Claude Code session, say:
> "I want to create a skill for my weekly VPS health check — it should SSH into 72.60.209.109, check that the orchestrator is running on port 8000, verify n8n is up, and report back via Telegram."

This is a `infrastructure` domain skill (stay_technical). Verify:
- Pre-session brief fires and surfaces instincts
- Domain correctly classified as `infrastructure`
- Voice injection does NOT activate
- Voice check-in does NOT fire
- Draft uses Boubacar's real VPS IP and real port

- [ ] **Step 2: Check session-tracker updated**

After the skill is packaged, verify `session-tracker.json` was incremented:
```bash
cat "C:\Users\HUAWEI\.claude\skills\boubacar-skill-creator\patterns\session-tracker.json"
```

Expected: `skills_created_total: 1`, `skills_since_reflection: 1`

- [ ] **Step 3: Sync installed skill with project copy**

After live test, copy any updated pattern files back to the project:
```bash
cp "C:\Users\HUAWEI\.claude\skills\boubacar-skill-creator\patterns\session-tracker.json" "D:\Ai_Sandbox\agentsHQ\skills\boubacar-skill-creator\patterns\session-tracker.json"
```

- [ ] **Step 4: Final commit and push**

```bash
cd "D:\Ai_Sandbox\agentsHQ" && git add skills/boubacar-skill-creator/ && git commit -m "feat: complete boubacar-skill-creator v1 — installed and live-tested" && git push
```

---

## Self-Review

**Spec coverage check:**

| Spec Requirement | Task |
|-----------------|------|
| Identity layer loads on every session | Task 5 (Step 1 — pre-session brief reads all 4 files) |
| Voice injection for consulting/leGriot domains | Task 1 (voice-guide.md) + Task 5 (SKILL.md Step 4) |
| Voice absent in technical domains | voice-domains.json already seeded; SKILL.md Step 3 |
| 5 check-in triggers | Task 2 (check-in-triggers.md) + Task 5 (SKILL.md Steps 1, 3, 4, 7, 8) |
| Learning loop — reflector extracts instincts | agents/reflector.md already exists |
| Session counter for 3+ skills check-in | Task 3 (session-tracker.json) + Task 5 |
| Dual storage (instincts.json + skill_creator_learnings.md) | Task 4 |
| Install to ~/.claude/skills/ | Task 6 |
| Description optimization | Task 7 |
| Live test | Task 8 |
| Simulations pass | ✅ Already done (18/18) |

**Placeholder scan:** No TBDs or TODOs in any task. All file content is complete and concrete.

**Type consistency:** `skills_since_reflection` used consistently across session-tracker.json (Task 3), SKILL.md Step 1 trigger (Task 5), and reflector reset logic (Task 5 Step 3).
