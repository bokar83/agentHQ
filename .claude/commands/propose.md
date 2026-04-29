---
description: Snapshot current work as an async commit proposal. Telegram fires, agent does NOT block.
allowed-tools: Bash
---

You are about to call Echo M1's `/propose` primitive. This is the async-partnership flow: you snapshot the working tree, queue a commit proposal, send a Telegram message to Boubacar, and CONTINUE working. He will `/ack` or `/reject` on his own cadence.

## What to do

1. Run the propose() function via Python. Use the agentsHQ venv if available, otherwise system python.
2. Print the returned short_id and suggested_message head to chat so Boubacar can correlate with his Telegram.
3. State "Proposal queued. Continuing." and move on to the next task.

Optional argument: `$ARGUMENTS` if present is an extra message to append to the suggested commit body (e.g. context the user wants captured).

## The exact bash to run

```bash
cd d:/Ai_Sandbox/agentsHQ && python -c "
import os
from pathlib import Path
from dotenv import load_dotenv
load_dotenv(Path('d:/Ai_Sandbox/agentsHQ/.env'))
os.environ.setdefault('POSTGRES_HOST', '127.0.0.1')
os.environ.setdefault('POSTGRES_USER', 'postgres')
os.environ.setdefault('POSTGRES_DB', 'postgres')
from skills.coordination import proposal
extra = '''$ARGUMENTS''' or None
result = proposal.propose(test_cmd=None, extra_message=extra)
print(f\"Proposal {result['short_id']} queued. Branch: {result['branch']}. Tests: {result['tests_status']}. Files: {len(result['files'])}.\")
print(f\"Suggested: {result['suggested_message'].splitlines()[0]}\")
"
```

After the bash completes, say "Proposal queued. Continuing." in chat and proceed with the next task. Do NOT wait for user acknowledgement. The whole point of /propose is async.
