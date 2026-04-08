---
name: agentshq-dispatch
description: Dispatches a task to the agentsHQ CrewAI orchestrator via /run-async and returns the job_id. Use when the user asks to run an agent task, start a job, or trigger the orchestrator.
---

# agentshq-dispatch

Sends a task to the agentsHQ CrewAI orchestrator running at `orc-crewai:8000`.

## Setup

Requires:
- `ORCHESTRATOR_API_KEY` — set in agent job secrets
- `CALLBACK_URL` — optional, defaults to thepopebot webhook receiver

## Usage

```bash
skills/library/agentshq-dispatch/dispatch.sh "<task description>" [session_key]
```

### Examples

```bash
# Fire a task
skills/library/agentshq-dispatch/dispatch.sh "Research the top 5 AI tools for solo consultants"

# Fire with session key for conversation continuity
skills/library/agentshq-dispatch/dispatch.sh "Follow up on the research from last session" "session_abc123"
```

## Output

Returns JSON with `job_id`. Poll `/status/{job_id}` or wait for the webhook callback at `/webhook/agent-complete`.
