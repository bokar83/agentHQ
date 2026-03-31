# Design Spec: Telegram-Native Delivery Pipeline
**Date:** 2026-03-31
**Project:** agentsHQ
**Status:** Approved

---

## Problem

The current system routes all post-processing (save to GitHub, save to Drive, send Telegram reply) through an n8n sub-workflow. This creates:
- OAuth credential expiry (GitHub broke after n8n update)
- Concurrency timeouts (n8n waits synchronously for async crew work)
- Two systems to maintain instead of one
- Workflow state outside version control

## Goal

From the user's perspective: send a Telegram message, get a Telegram reply. That's it.

The orchestrator owns everything. n8n is reduced to a 2-node webhook receiver.

---

## Architecture

```
Telegram message
      ↓
n8n (2 nodes: Telegram Trigger → HTTP POST /run — fire and forget)
      ↓
POST /run on orchestrator (VPS:8000)
      ↓
┌─────────────────────────────────────────────────┐
│  orchestrator.py                                │
│                                                 │
│  1. Receive request (from_number = chat_id)     │
│  2. Send ack to Telegram immediately (~1s)      │
│  3. Return HTTP 202 to n8n (n8n is done)        │
│  4. Background job:                             │
│     a. Classify + run CrewAI crew               │
│     b. Every 5 min → Simpsons progress ping     │
│     c. Crew finishes → build output             │
│     d. Save .md file to local /app/outputs      │
│     e. Push file to GitHub outputs/{type}/      │
│     f. Upload file to Google Drive outputs/     │
│     g. Send final result + links to Telegram    │
└─────────────────────────────────────────────────┘
```

---

## New Files

### `orchestrator/notifier.py`
Owns all Telegram Bot API calls. No other file sends Telegram messages.

Functions:
- `send_message(chat_id, text)` — raw send, handles Telegram's 4096 char limit
- `send_ack(chat_id, task_type)` — immediate "On it" with task type label
- `send_progress_ping(chat_id)` — random Simpsons quote from 20-quote pool
- `send_result(chat_id, summary, drive_url, github_url)` — final delivery with links

Config (from env): `TELEGRAM_BOT_TOKEN`, `TELEGRAM_CHAT_ID`

### `orchestrator/saver.py`
Owns all save operations. Returns URLs.

Functions:
- `save_to_github(title, task_type, content) → str` — pushes .md to `outputs/{task_type}/{slug}-{timestamp}.md`, returns GitHub blob URL
- `save_to_drive(title, task_type, content) → str` — uploads .md to Drive `outputs/` folder (ID: `1wb2ZdYkLdSy-oWQ3bWZWgRXOIgX59t2N`), returns webViewLink

Config (from env): `GITHUB_TOKEN`, `GITHUB_USERNAME`, `GITHUB_REPO`, `GOOGLE_SERVICE_ACCOUNT_JSON`, `GOOGLE_DRIVE_FOLDER_ID`

Dependencies to add to `requirements.txt`:
- `PyGithub` — GitHub API
- `google-api-python-client` — Drive API
- `google-auth` — Service account auth

---

## Modified Files

### `orchestrator/orchestrator.py`

**`/run` endpoint changes:**
- Accept request
- Detect chat_id from `from_number`
- Send ack via `notifier.send_ack()`
- Return `{"status": "accepted", "job_id": uuid}` immediately (HTTP 202)
- Register background task: `run_background_job(request)`

**New `run_background_job()` function:**
```
1. Start progress ping timer (every 300s → notifier.send_progress_ping)
2. Run crew (existing run_orchestrator logic)
3. Cancel ping timer
4. Save to GitHub → get github_url
5. Save to Drive → get drive_url
6. Build final summary (existing _build_summary)
7. notifier.send_result(chat_id, summary, drive_url, github_url)
8. Save to memory (existing save_to_memory)
```

**`/run` no longer returns `TaskResponse` with result** — it returns accepted immediately. The result is pushed to Telegram directly.

**Backward compatibility:** A new `/run-sync` endpoint preserves the current synchronous behavior (blocks until result, returns `TaskResponse`). Direct HTTP callers (Cursor, Claude Code) that need a synchronous result use `/run-sync`. The existing `/run` becomes async-only.

### `docker-compose.yml`
Add environment variables:
```
TELEGRAM_BOT_TOKEN=<token>
TELEGRAM_CHAT_ID=<your chat id — extracted from first message or set manually>
GOOGLE_SERVICE_ACCOUNT_JSON=/app/secrets/agentshq-service-account.json
GOOGLE_DRIVE_FOLDER_ID=1wb2ZdYkLdSy-oWQ3bWZWgRXOIgX59t2N
```

Add volume mount for service account key:
```
- ./secrets:/app/secrets
```

### `orchestrator/Dockerfile`
No changes needed.

### `infrasctructure/.env`
Add:
```
TELEGRAM_BOT_TOKEN=8777275362:AAE6XBLzEnwufW6m074H2A-8fNZO29rbRTg
TELEGRAM_CHAT_ID=<to be determined from first inbound message>
GOOGLE_DRIVE_FOLDER_ID=1wb2ZdYkLdSy-oWQ3bWZWgRXOIgX59t2N
```

---

## n8n Workflow (rebuilt via REST API)

Replace existing main workflow `a6ciAzyqvnXIC9lw` with a 2-node workflow:

```
[Telegram Trigger] → [HTTP Request: POST http://localhost:8000/run]
```

HTTP Request node config:
- Method: POST
- URL: `http://localhost:8000/run`
- Body: `{ "task": "{{ $json.message.text }}", "from_number": "{{ $json.message.chat.id }}", "session_key": "{{ $json.message.chat.id }}" }`
- Response: ignored (fire and forget)
- Timeout: 10s (just enough to confirm receipt, not wait for result)

Sub-workflow `ppn7iH-oqxOUqdfzIGfDo` is deactivated (not deleted — kept as backup).

---

## Telegram UX (user experience)

```
User:    "Research the top 5 AI tools for consulting firms"

Bot:     "On it — Research Agent is on the case. 🔍"
         [returns in ~1 second]

[5 minutes pass]

Bot:     "Don't have a cow — still chewing on it." — Bart Simpson

[crew finishes at ~8 min]

Bot:     --- Research complete (487s) ---

         [full report content, up to 3700 chars]

         📁 Drive: https://drive.google.com/file/d/...
         📂 GitHub: https://github.com/bokar83/agentHQ/blob/main/outputs/research/...

         [reply 'more' to see the rest]
```

---

## The 20 Simpsons Progress Quotes

Rotated randomly. Never the same one twice in a row.

1. "It's taking forever... or is it just me?" — Homer
2. "I am so smart! S-M-R-T. The agents are proving it right now." — Homer
3. "Mmm... deep research..." — Homer
4. "Trying is the first step towards failure. Good thing your agents don't try — they DO." — Homer
5. "Don't have a cow — still chewing on it." — Bart
6. "Excellent... the plan is proceeding." — Mr. Burns
7. "In this house, we obey the laws of thermodynamics. Processing takes time." — Homer
8. "This is the greatest thing I've ever been asked to do." — Homer
9. "Why do they call it a shortcut when it never is?" — Homer
10. "This better be worth it... it will be." — Homer
11. "I'm not normally a praying man, but if you're up there... speed up the agents." — Homer
12. "The key to happiness is not to ask questions. Also: wait for the ping." — Homer
13. "Remember: an idiot is anyone slower than me. These agents are not idiots." — Homer
14. "I've learned that life is one crushing defeat after another — until the deliverable arrives." — Homer
15. "Every time I try to leave, something pulls me back. Just like this research task." — Homer
16. "Ahhh, the agents are thinking. There's nothing more satisfying... except nachos." — Homer
17. "I can't promise I'll try, but I'll try to try. The agents promised more." — Homer
18. "Facts are meaningless. You can use facts to prove anything that's even remotely true. Like: your task is almost done." — Homer
19. "To alcohol! The cause of, and solution to, all of life's problems. To agents!" — Homer
20. "The problem with being right is that nobody believes you until it's too late. Check back in 5 minutes." — Homer

---

## Concurrency Fix

The current single-threaded FastAPI + crew execution means concurrent requests block each other. Fix: use FastAPI's `BackgroundTasks` (already imported) to run each job in a thread pool. Since `/run` now returns 202 immediately, n8n never times out regardless of how many tasks are in flight.

For the orchestrator itself: Python's GIL means CPU-bound tasks (LLM API calls are I/O-bound) can run truly concurrently via threads. No queue needed at this scale (1-5 concurrent requests).

---

## What is NOT Changing

- CrewAI crews — no changes
- Router — no changes
- Memory (Postgres + Qdrant) — no changes
- Voice polisher — no changes
- "more" command — no changes
- `/run-team` endpoint — no changes
- `/run-sync` endpoint (new, but same logic as current `/run`) — backward compatible

---

## Credentials Summary

| Credential | Where stored | Notes |
|---|---|---|
| Telegram bot token | `.env` → `TELEGRAM_BOT_TOKEN` | Never in n8n again |
| GitHub token | Already in `.env` as `GITHUB_TOKEN` | No change |
| Google Drive folder | `.env` → `GOOGLE_DRIVE_FOLDER_ID` | Updated to outputs subfolder |
| Google service account | `./secrets/agentshq-service-account.json` on VPS | Volume-mounted into container |

---

## Success Criteria

1. Send a Telegram message → receive ack within 2 seconds
2. Every 5 minutes of processing → receive a Simpsons progress ping
3. Task completes → receive full output + Drive link + GitHub link in Telegram
4. Two concurrent tasks → both complete without timeout
5. n8n workflow is 2 nodes, no credentials managed in n8n except Telegram bot token (for the trigger)
6. All save logic is in Python, version-controlled, never needs n8n re-auth
