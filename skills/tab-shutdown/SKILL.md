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

0. **Do work now — only defer if genuinely blocked.** Before writing anything to "Next session must start here", ask: is this actually blocked right now by another agent, timing, or an external dependency? If not, do it before closing. Items deferred with no real blocker are a failure mode. (2026-05-10: 4 unblocked items were deferred unnecessarily — all done same session once Boubacar asked "what's blocking you?")

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

### Step 1b: Close open followups touched this session

**HARD RULE: Before writing the handoff, grep `docs/reviews/absorb-followups.md` for any entry whose target date is today or that was directly touched this session. For each one:**
- If work completed → mark `| DONE` at end of line
- If work was superseded (direction changed mid-session) → mark `| SUPERSEDED YYYY-MM-DD: <one line why>`
- If still open → leave as-is

**Why:** 2026-05-08 incident — `telegram_inbound.py` followup was written, then the session discovered the inbound loop already existed and the plan changed. Handoff doc was not updated. Next session was handed a stale "build this" prompt for something already resolved. A 30-second grep + mark would have caught it.

Same rule applies to any mid-session handoff docs written before work was complete: if the work changed direction, update the doc before closing.

### Step 1c: Update roadmaps and active tasks

**HARD RULE: Every session that touches a roadmap milestone, ships a feature, or makes a product decision MUST log it before closing.**

For each active roadmap touched this session (`docs/roadmap/<codename>.md`):
1. Add a session log entry at the bottom of the file with date + what shipped/decided/deferred
2. Update the "Session-Start Cheat Block" at the top — change "Last session ended" date, update default next moves
3. If a milestone flipped status (QUEUED → SHIPPED, RESEARCH-GATED → QUEUED, etc.) — update the milestone header

For Notion Execution Cycle tasks: if any tasks were completed or new ones created this session, note them in the handoff "What is NOT done" section so next session can update Notion.

Run `git -C "d:/Ai_Sandbox/agentsHQ" add docs/roadmap/ && git commit` to capture roadmap updates before closing.

### Step 2: Update memory files

For each item from Step 1, decide: which memory type fits?

| Type | When to use |
|---|---|
| `feedback` | A rule Boubacar stated, a correction, a confirmed approach |
| `project` | State of in-progress work, decisions, blockers, next steps |
| `user` | New info about Boubacar's preferences, expertise, context |
| `reference` | A DB ID, a URL, a location of a resource |

Write or update the relevant memory file. Then add/update the pointer in
the correct index — see the routing rule below.

**Always check first:** does a relevant memory file already exist? Update it
rather than creating a duplicate.

#### MEMORY.md routing rule (added 2026-04-29)

`MEMORY.md` has a hard cap of 200 lines because the harness truncates past
that. Capability rules live at lines 1-25 in the always-loaded zone. Discipline:

- **`project_*.md`** entries -> add the pointer to **`MEMORY_ARCHIVE.md`**, not
  `MEMORY.md`. Project state is on-demand, not always-loaded.
- **`feedback_*.md`** and **`reference_*.md`** entries -> add the pointer to
  `MEMORY.md` under the matching section.
- **A new always-true capability** (a thing Claude can do without asking, like
  VPS SSH, gws drive upload, telegram send) -> also add a one-line bullet to
  the "Always-true capability shortlist" block at the top of `MEMORY.md`
  (lines 9-20). This is the always-loaded zone; only put things here that
  every session should know.
- **Always run `wc -l MEMORY.md` after editing.** If the file is over 195
  lines, move the oldest `project_*` pointer from MEMORY.md to MEMORY_ARCHIVE.md
  before closing the session. Hard cap: 200 lines.
- **Why:** capability amnesia diagnosed 2026-04-29 was caused by MEMORY.md
  growing past 285 lines and getting truncated. Index discipline prevents
  recurrence. See `feedback_placement_before_architecture.md`.

### Step 2b: Write session lessons to Postgres memory table

**HARD RULE: Every session writes 3-5 lessons + 1 project_state to the VPS Postgres `memory` table. This is separate from flat-file memory. It feeds the second brain and the weekly synthesis crew.**

Run this Python snippet from d:/Ai_Sandbox/agentsHQ:

```python
# Run: cd d:/Ai_Sandbox/agentsHQ && python -c "<paste snippet>"
import sys; sys.path.insert(0, '.')
from orchestrator.memory_models import AgentLesson, ProjectState, SessionLog
from orchestrator.memory_store import write

# Write 3-5 agent lessons from this session (fill in real values):
write(AgentLesson(
    what_happened="<what happened>",
    outcome="SUCCEEDED",  # or FAILED or PARTIAL
    rule="<the rule to remember>",
    pipeline="<atlas|sw|cw|studio|general>",
    cost_estimate="",
    source="claude-code",
    agent_id="tab-shutdown",
))

# Write 1 project state for the primary codename touched:
write(ProjectState(
    codename="<atlas|harvest|studio|compass|echo|general>",
    milestone="<M9d-A or blank>",
    status="on-track",  # or blocked, shipped, paused
    last_action="<what just shipped>",
    next_action="<exact next move>",
    blockers="",
    source="claude-code",
    agent_id="tab-shutdown",
))

# Write 1 session log:
write(SessionLog(
    codename="<codename>",
    summary="<2-3 sentences: what shipped, what changed, what's next>",
    date="<YYYY-MM-DD>",
    source="claude-code",
    agent_id="tab-shutdown",
))
```

**If the VPS Postgres is unreachable** (e.g. laptop is offline), skip this step and note it in the handoff doc. The flat-file memory from Step 2 is the fallback.

**Why this matters:** The memory table feeds /query in Telegram, the weekly synthesis crew, and session-start context injection. Without writes at session end, the second brain stays empty.

### Step 3: Update affected skills (ALWAYS — never defer to memory alone)

**HARD RULE: every lesson learned this session that belongs in a skill MUST be written to the skill file. Memory is for runtime context. Skills are for durable how-to. Do NOT leave skill-relevant lessons sitting only in memory and call this step done.**

The user clarified this rule explicitly on 2026-04-30: *"When it comes to the tab shutdown, you ALWAYS write what needs to be written to the skills files to update them. Don't leave that in memory."*

For each skill that was used, corrected, or extended this session:

- Does the SKILL.md reflect what was learned?
- If a bug was found in how the skill was followed (like the mix-blend-mode cursor issue, or the GSAP split-line invisible-headline bug), add a HARD RULE or Known Pitfalls section.
- If a new pattern was discovered (like the Volta cinematic standard, or the "20-50% redesign" rule, or "use the real client logo"), add it as a top-level HARD RULE near the top of the skill.
- If a phase of a multi-phase skill was extended (like the website-intelligence Phase 1 media inventory + Phase 5 hand-off rule), edit those phases directly.

Skills that commonly need updates after website/design work:

- `~/.claude/skills/frontend-design/SKILL.md`
- `~/.claude/skills/website-intelligence/SKILL.md`
- `~/.claude/skills/demo-builder/SKILL.md`
- `~/.claude/skills/site-qualify/SKILL.md`
- `~/.claude/skills/blotato/SKILL.md`
- `~/.claude/skills/kie_media/SKILL.md`

The global `~/.claude/skills/` versions are the active ones the harness loads. If an agentsHQ project copy exists at `d:/Ai_Sandbox/agentsHQ/skills/<name>/SKILL.md`, sync it too — but the global is canonical.

**Markdown lint warnings on skill edits (MD031 fence blank-lines, MD034 bare-urls, MD060 table-pipe-spacing) are cosmetic. Content lands clean. Do NOT let them stop the edit.**

**If your editor blocks the skill edit:** retry once. If the user explicitly tells you to stop editing the skill, save the rule to memory AND surface the deferred edit in the handoff under "Open questions" so the next session catches it. Never silently skip a skill update because an earlier edit was rejected — the rejection might have been about scope, not content. Check before declaring Step 3 complete.

### Step 3b: Commit all work and push to main

**HARD RULE: No tab closes with uncommitted changes or unpushed commits. Everything ships to main before the session ends.**

1. `git status` — check for uncommitted changes
2. Stage all session files: `git add <files>` (never `git add -A` — avoid accidental secrets)
3. Commit with a clear message summarizing the session work
4. `git push origin main` — push to remote
5. If push rejected (non-fast-forward): `git pull --rebase origin main && git push origin main`

### Step 3c: Verify changes are live on VPS

**HARD RULE (added 2026-05-10): After pushing to main, verify the VPS has the changes and they are active in the running system. Do not close the tab until this is confirmed.**

```bash
ssh root@72.60.209.109 "cd /root/agentsHQ && git pull && git log --oneline -3"
```

Then spot-check at least one key file changed this session:
```bash
ssh root@72.60.209.109 "grep -n '<key_pattern>' /root/agentsHQ/<changed_file>"
```

If VPS is behind: `git pull` on VPS. If container needs restart for code to take effect: `docker compose up -d orchestrator` (code is volume-mounted — no rebuild needed unless `requirements.txt` changed).

**Why:** Committing and pushing to GitHub does NOT automatically update the VPS. The VPS pulls on deploy commands only. Without this step, changes may sit in GitHub but be dead in production.

**Gate notification (if applicable):**
If this session produced code changes that need Gate review (new features, infra changes, anything that touches shared state):
- Verify commits are on `main` with `[READY]` tag if a feature branch was used
- Gate watches GitHub every 5 min — no manual signal needed
- If there are open Blotato/Notion/VPS changes that Gate needs to know about, add a note to `docs/handoff/active-context.md` with "GATE: [what needs review]"

**No pending branches:** If any feature branches were created this session and not merged, either:
- Push with `[READY]` so Gate processes them, OR
- Document them explicitly in the handoff "What is NOT done" section with reason for deferral

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

**If any first action references a handoff doc written mid-session:** add this warning inline — `(verify this is still current before starting — direction may have changed after it was written)`.

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
