---
name: tab-shutdown
description: >
  Closes a Claude Code session cleanly. Writes all discoveries, decisions, and
  lessons to memory and skills, updates any affected skills, writes a handoff
  doc to docs/handoff/, and posts the next-session prompt in chat. Trigger on
  "tab shutdown", "close this tab", "end session", "wrap up", "shut it down",
  or "/tab-shutdown".
---

# Tab Shutdown

Closes this Claude Code session cleanly so the next session (same or different
tab) picks up exactly where this one left off with zero context loss.

This skill is for closing a SINGLE TAB (not the full nightly shutdown).
Run it whenever you are done working in this specific Claude Code instance,
even mid-day.

---

## HARD RULES

1. **Never skip a step.** Every step runs every time. A 5-minute session still
   gets a handoff file. A 10-second change still gets a memory update.

2. **Memory first, handoff second.** Write durable facts to memory files BEFORE
   writing the handoff. The handoff is transient; memory is permanent.

3. **Post the prompt in chat.** The handoff file alone is not enough. The next
   session prompt MUST appear as the last message in this conversation so
   Boubacar can copy-paste it into the next tab.

4. **No vague summaries.** Every memory entry names specific files, functions,
   URLs, or decisions. "Updated the skill" is not a memory entry.
   "Added HARD RULES block to skills/kie_media/SKILL.md lines 14-28" is.

5. **Write mid-session checkpoints on long tasks.** Any task with 3+ steps or
   expected duration over 30 minutes gets a checkpoint written to
   `docs/handoff/active-context.md` after each major step completes. Do not
   wait for the session to end. Sessions die without warning.

---

## Mid-Session Checkpoint (run during long tasks)

Trigger: after any major step completes on a task that has 3+ steps or will
take 30+ minutes (deploys, multi-file builds, VPS work, migrations).

Write or overwrite `docs/handoff/active-context.md`:

```markdown
# Active Context - <date> <time MT>

## What is in flight
[1-2 sentences: exact task, what step just completed]

## Files being edited
[Bullet list of files currently open or recently changed]

## Decisions made so far
[Any architectural or product decisions locked in this session]

## Next step
[The exact next action if this session dies right now]

## Blockers / waiting on
[Anything unresolved that would stop progress]
```

Keep it under 30 lines. Overwrite on every checkpoint, do not append.
This file is transient; it gets replaced by the full handoff doc at session end.

---

## Checklist (run in order)

### Step 1: Inventory what changed this session

Look back at the full conversation. List:
- Files created or edited (paths)
- Decisions made (architectural, product, design)
- New patterns or techniques discovered
- Errors encountered and how they were fixed
- Rules Boubacar stated explicitly
- Things that surprised you or went wrong

### Step 2: Update memory files

For each item from Step 1, decide: which memory type fits?

| Type | When to use |
|---|---|
| `feedback` | A rule Boubacar stated, a correction, a confirmed approach |
| `project` | State of in-progress work, decisions, blockers, next steps |
| `user` | New info about Boubacar's preferences, expertise, context |
| `reference` | A DB ID, a URL, a location of a resource |

Write or update the relevant memory file. Then add/update the pointer in
`MEMORY.md`.

**Always check first:** does a relevant memory file already exist? Update it
rather than creating a duplicate.

### Step 3: Update affected skills

For each skill that was used, corrected, or extended this session:
- Does the SKILL.md reflect what was learned?
- If a bug was found in how the skill was followed (like the mix-blend-mode
  cursor issue), add a HARD RULE or Known Pitfalls section.
- If a new pattern was discovered (like the Volta cinematic standard), add it.

Skills that commonly need updates after website/design work:
- `skills/frontend-design/SKILL.md`
- `skills/demo-builder/SKILL.md`
- `skills/site-qualify/SKILL.md`
- `skills/blotato/SKILL.md`
- `skills/kie_media/SKILL.md`

After updating agentsHQ skills, copy to `~/.claude/skills/<name>/SKILL.md`
so the global install stays in sync.

### Step 4: Write the handoff file

Path: `docs/handoff/YYYY-MM-DD-<slug>.md`

Format:
```markdown
# Session Handoff - <title> - <date>

## TL;DR
One paragraph. What was the arc of this session?

## What was built / changed
Bullet list. File paths. Specific. No vague summaries.

## Decisions made
Decisions that affect future sessions. With reasoning.

## What is NOT done (explicit)
Things deliberately left incomplete and why.

## Open questions
Anything unresolved that the next session must address.

## Next session must start here
Numbered list of first actions for the next session, in order.

## Files changed this session
Tree or bullet list of every file touched.
```

### Step 5: Post the next-session prompt in chat

This is the last thing you do. Copy the format below exactly. Post it as
your final message.

Format:
```
---
NEXT SESSION PROMPT - copy this into the new tab:

Continue from [docs/handoff/YYYY-MM-DD-<slug>.md].

Context:
- [2-3 sentences summarizing where things stand]
- [Any blockers or decisions needed from Boubacar]

First actions:
1. [Exact first thing to do]
2. [Second thing]
3. [Third thing if applicable]
---
```

---

## What makes a good vs bad tab shutdown

**Bad:**
- "Memory updated, handoff written, see you next time!"
- Vague memory entries ("improved the design skill")
- Handoff file that just lists what was done with no "next steps"
- No prompt posted in chat

**Good:**
- Memory entries that name specific files, line numbers, and decisions
- Handoff that has a "Next session must start here" section a stranger could follow
- Prompt posted in chat that Boubacar can copy-paste with zero context needed
- Skills that reflect exactly what was learned, so the NEXT build is better
  than this one WITHOUT needing to explain it again

---

## Files

- This skill: `skills/tab-shutdown/SKILL.md`
- Memory dir: `~/.claude/projects/d--Ai-Sandbox-agentsHQ/memory/`
- Memory index: `~/.claude/projects/d--Ai-Sandbox-agentsHQ/memory/MEMORY.md`
- Handoff dir: `docs/handoff/`
- Global skills copy: `~/.claude/skills/tab-shutdown/SKILL.md`
