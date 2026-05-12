---
name: rca
description: Use when a production system is broken, behaving unexpectedly, or an incident needs investigation. Triggers on: gate agent failures, studio pipeline errors, SW outreach bugs, webchat routing bugs, cost spikes, container crashes, silent failures.
---

**HARD GATE: NO EDITS before root cause is confirmed in writing. Not one line. Not one docker cp. Nothing.**

---

## PHASE 0 -- TRIAGE

If `/rca` was called with a subsystem argument (e.g. `/rca gate`), skip the question below and proceed immediately to the first diagnostic command.

If no argument was given, ask ONE question only:

Which subsystem is broken?

- A) Gate agent (gate_agent.py / VPS cron / /var/log/gate-agent.log)
- B) Studio pipeline (render, ffmpeg, Notion publish, studio_production_crew.py)
- C) Signal Works outreach (morning_runner.py, send_scheduler.py, sequence_engine.py)
- D) Orchestrator / webchat (handlers_chat.py, router.py, crews.py)
- E) Burn guard / cost spike (hooks, OpenRouter balance, provider redirect)
- F) Other -- describe in one sentence

Once the subsystem is known, run the matching diagnostic command immediately. Do not wait for user confirmation.

| Subsystem | First diagnostic command |
|---|---|
| Gate | `ssh root@72.60.209.109 "tail -30 /var/log/gate-agent.log"` |
| Studio | `ssh root@72.60.209.109 "docker logs orc-crewai 2>&1 \| grep -E 'render\|ffmpeg\|studio\|publish' \| tail -30"` |
| Blotato publisher | `ssh root@72.60.209.109 "docker logs orc-crewai 2>&1 \| grep -E 'BLOTATO\|STUDIO PUBLISHER' \| tail -30"` |
| SW outreach | `ssh root@72.60.209.109 "docker logs orc-crewai 2>&1 \| grep -E 'morning\|send_sched\|sequence\|outreach' \| tail -30"` |
| Webchat | `ssh root@72.60.209.109 "docker logs orc-crewai 2>&1 \| grep -E 'chat\|router\|crew\|forward' \| tail -30"` |
| Burn guard | `ssh root@72.60.209.109 "docker logs orc-crewai 2>&1 \| grep -E 'spike\|balance\|openrouter\|provider' \| tail -30"` |
| Baked import (command/handler silently ignored) | `ssh root@72.60.209.109 "docker exec orc-crewai python3 -c \"import <module>; print(<module>.__file__)\""` -- if result is `/app/<file>.py` not `/app/orchestrator/<file>.py`, edit went to wrong copy; fix: `docker exec orc-crewai cp /app/orchestrator/<file>.py /app/<file>.py` + restart |
| Other | `ssh root@72.60.209.109 "docker logs orc-crewai --tail 50"` |

**Phase exit: Run the diagnostic. Do not proceed until the output is in the conversation.**

---

## PHASE 1 -- REPRODUCE

Ask: "What exact symptom triggered this RCA? Paste the error message, log line, or behavior. One sentence minimum."

If file paths appear in the symptom, run:

```bash
ssh root@72.60.209.109 "docker exec orc-crewai find /app -maxdepth 1 -type f | head -20"
```

Read the relevant source file(s) before touching anything.

**Phase exit -- agent must write this exact line before proceeding:**

> **Symptom confirmed:** [exact quote from logs or user description]

---

## PHASE 2 -- ISOLATE ROOT CAUSE

Read the suspect file(s). Grep for the error. Run a targeted diagnostic command.

Three direct actions in sequence. No sub-skill invocations.

1. Read the relevant file at the suspect line.
2. Grep for the error string or function name in the codebase.
3. Run one targeted diagnostic. Example: `docker exec orc-crewai python3 -c "import <module>"` to surface import errors.

No edits. No fixes. Diagnosis only.

**Phase exit -- agent must write this exact line before proceeding:**

> **Root cause:** [one sentence, file:line if known]

---

## PHASE 3 -- SUCCESS CRITERION

Agent proposes the criterion. Do NOT ask the user to write it.

Format: exact command + expected output.

Reference examples by subsystem:

- Gate: `ssh root@72.60.209.109 "tail -5 /var/log/gate-agent.log"` must contain `gate: tick start`
- Studio: `ssh root@72.60.209.109 "docker logs orc-crewai 2>&1 | grep 'render complete' | tail -3"` must return at least one line
- SW outreach: `ssh root@72.60.209.109 "docker logs orc-crewai 2>&1 | grep 'emails sent' | tail -3"` count must be > 0
- Burn guard: `ssh root@72.60.209.109 "docker logs orc-crewai 2>&1 | grep 'spike check' | tail -3"` must contain no ALERT line

After proposing, ask: "Does this success criterion work, or do you want to change it?" Wait for confirmation or edit.

**Phase exit -- agent must write this exact line before proceeding:**

> **Success criterion:** [command] -> [expected output] confirmed

---

## PHASE 4 -- FIX

**Attempt counter starts at 0. After 2 failed self-edit attempts: STOP. Mandatory Codex dispatch. No exceptions. No "one more try."**

Decision rule:

- 1 file, 1-3 lines, first attempt -> agent edits directly.
- Multi-file change OR attempt counter >= 2 -> dispatch `codex:rescue` with this exact template:

```
File: <path>
Line: <line number>
Current: <exact current code>
Replace with: <exact replacement>
Constraint: one file, no new features, no refactor, no style changes
```

After the fix is applied, deploy:

```bash
ssh root@72.60.209.109 "cd /root/agentsHQ && git pull && docker compose up -d orchestrator"
```

Do NOT run `orc_rebuild.sh` or `docker compose build` unless `requirements.txt` changed.

**Phase exit: Fix deployed. Proceed to Phase 5.**

---

## PHASE 5 -- VALIDATE

Run the success criterion command from Phase 3.

- Pass -> write **"Criterion met: [output]"** -> proceed to Phase 6.
- Fail -> increment attempt counter -> return to Phase 4.
- If attempt counter reaches 2 AND Codex has already been dispatched AND validation still fails: STOP. Write a summary of every attempt made. Ask Boubacar for input before continuing.

---

## PHASE 6 -- HANDOFF DOC

Auto-generate `docs/handoff/YYYY-MM-DD-<subsystem>-rca.md` with exactly this structure:

```markdown
# RCA: <subsystem> -- YYYY-MM-DD

**Root cause:** <one sentence>
**Fix applied:** <file:line -- what changed, before -> after>
**Success criterion verified:** <command> -> <actual output>
**Never-again rule:** <one sentence hard rule for AGENT_SOP or memory>
**Memory update:** <yes -- feedback_<subsystem>_<topic>.md> or <no>
```

Commit the handoff doc:

```bash
git add docs/handoff/YYYY-MM-DD-*.md && git commit -m "docs(rca): <subsystem> incident YYYY-MM-DD"
```

If memory update = yes: write or update the memory file immediately after the commit.

---

## Maintenance

Run after any edit to this skill file:

```bash
rsync -av ~/.claude/skills/rca/ root@72.60.209.109:/root/.claude/skills/rca/
```

---

## Self-Improvement

If this RCA uncovered a new subsystem or a diagnostic command that would have saved time, update the Phase 0 triage table in this skill file and re-run the VPS sync.

---

## Known Pitfalls (from past incidents)

### Blotato "Failed to read media metadata"
Drive `webViewLink` passed as `mediaUrls` — private file or wrong URL format. Fix: `ensure_public(file_id)` + convert to `https://drive.usercontent.google.com/download?id={ID}&export=download&confirm=t`. Run `python -m orchestrator.drive_publish audit-videos` to fix all Pipeline DB records. See `feedback_studio_blotato_drive_url.md`.

### TikTok "Unsupported frame rate"
ffmpeg concat produces VFR output (avg_frame_rate ≠ r_frame_rate). Fix: add `-r {fps} -vsync cfr` to `_concat_clips` in `studio_render_publisher.py`. Existing renders must be re-rendered; fix only applies to new renders.

### Deployment: "git pull already up to date" after edit
Push to remote FIRST, then `git pull` on VPS. If you `docker cp` before pushing, the VPS `git pull` will say "already up to date" but the container gets the new file via `docker cp`. Verify the file landed: `docker exec orc-crewai grep -c '<unique_string>' /app/orchestrator/<file>.py`.

### Publisher tick ran before fix deployed
If a heartbeat tick fires between "records reset to scheduled" and "fix deployed", records flip to `publish-failed` again. After deploying a fix, always check `docker logs orc-crewai | grep 'STUDIO PUBLISHER.*tick done'` to confirm the fix-era tick ran before declaring success.
