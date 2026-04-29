---
description: Reject a queued commit proposal. Marks it failed, no commit happens.
allowed-tools: Bash
---

The user wants to reject proposal `$ARGUMENTS`. The argument is `<proposal_id>` optionally followed by a reason (free text after the id). The reason is captured in the `tasks.error` column for forensics.

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
    print('ERROR: pass a proposal id (and optional reason)')
    sys.exit(1)
parts = arg.split(None, 1)
pid = parts[0]
reason = parts[1] if len(parts) > 1 else None
result = proposal.reject(pid, reason=reason)
if result.get('ok'):
    print(f\"Rejected {result['id'][:8]}\" + (f\" ({reason})\" if reason else ''))
else:
    print(f\"FAILED: {result.get('error')}\")
    sys.exit(2)
"
```

After successful reject, state the reason captured (if any) and continue with the next task.
