---
description: Approve a queued commit proposal. Stages files and commits with the suggested message.
allowed-tools: Bash
---

The user wants to approve proposal `$ARGUMENTS`. Pass that id (full or 8-char prefix) to `proposal.ack()`. If `$ARGUMENTS` is empty, fail loudly and tell the user to run `/list-proposals` first.

## The exact bash to run

```bash
cd d:/Ai_Sandbox/agentsHQ && python -c "
import os, sys
from pathlib import Path
from dotenv import load_dotenv
load_dotenv(Path('d:/Ai_Sandbox/agentsHQ/.env'))
os.environ.setdefault('POSTGRES_HOST', '127.0.0.1')
os.environ.setdefault('POSTGRES_USER', 'postgres')
os.environ.setdefault('POSTGRES_DB', 'postgres')
from skills.coordination import proposal
arg = '''$ARGUMENTS'''.strip()
if not arg:
    print('ERROR: pass a proposal id (run /list-proposals to see queued ones)')
    sys.exit(1)
result = proposal.ack(arg)
if result.get('ok'):
    print(f\"Acked. Commit: {result['commit_sha'][:8] if result.get('commit_sha') else '?'}\")
    print(f\"Message: {result['message'].splitlines()[0]}\")
    print(f\"Files: {len(result['files'])}\")
else:
    print(f\"FAILED: {result.get('error')}\")
    sys.exit(2)
"
```

If the command exits non-zero, surface the error to the user and offer to either retry, fix the underlying issue, or `/reject` the proposal instead.
