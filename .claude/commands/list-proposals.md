---
description: Show queued commit proposals (kind=commit-proposal, status=queued).
allowed-tools: Bash
---

Show all currently queued Echo commit proposals. Format as a table with: short id, branch, tests status, files count, suggested message head, age.

## The exact bash to run

```bash
cd d:/Ai_Sandbox/agentsHQ && python -c "
import os
from pathlib import Path
from dotenv import load_dotenv
from datetime import datetime, timezone
load_dotenv(Path('d:/Ai_Sandbox/agentsHQ/.env'))
os.environ.setdefault('POSTGRES_HOST', '127.0.0.1')
os.environ.setdefault('POSTGRES_USER', 'postgres')
os.environ.setdefault('POSTGRES_DB', 'postgres')
from skills.coordination import proposal
rows = proposal.list_pending(limit=20)
if not rows:
    print('No queued proposals.')
else:
    now = datetime.now(timezone.utc)
    for r in rows:
        pid = r['id'][:8]
        p = r['payload']
        age_min = int((now - r['created_at']).total_seconds() / 60)
        head = p.get('suggested_message', '').splitlines()[0]
        print(f\"{pid}  {p.get('branch', '?'):30s}  tests={p.get('tests_status', '?')}  files={len(p.get('files', []))}  {age_min}m  {head[:60]}\")
"
```
