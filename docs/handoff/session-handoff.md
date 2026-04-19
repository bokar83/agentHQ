# Session Handoff — 2026-03-31

## What Was Done This Session

### 1. Voice Polisher — DONE
- Removed `build_humanization_task()` from all crews (code, app, writing, research, consulting, social, hunter)
- Moved `polish_voice()` to global post-processing in `orchestrator.py` after `crew.kickoff()`
- All 4 agent types tested and confirmed working

### 2. Title + Deliverable Extraction — DONE
- Added `title` and `deliverable` fields to `TaskResponse` in `orchestrator.py`
- `deliverable` = everything after `DELIVERABLE:` marker in crew output
- `title` = first 80 chars of the task request
- Both fields flow through `Format Result` to `Always Save Sub`

### 3. Always Save Sub Pipeline — DONE (full rewrite)
- **Main workflow** `a6ciAzyqvnXIC9lw`:
  - Removed `Has Files?` IF node (was causing routing bugs)
  - Removed `Send Files via Telegram` node entirely
  - `Send Result to Telegram bot` now connects directly to `Archive to DB` + `Always Save Sub` (unconditional)
  - `Always Save Sub` uses explicit `workflowInputs` referencing `$('Format Result')` by name
- **Sub-workflow** `ppn7iH-oqxOUqdfzIGfDo`:
  - `Prepare Save Payload` builds title, slug, github_path (`outputs/{type}/{slug}-{Date.now()}.md`), markdown_content
  - Fans out to: `Save to GitHub` + `Convert to File` + `Log to Notion` (disabled)
  - `Convert to File` → `Save to Google Drive` → `Send Drive Link` (Telegram sendMessage back to user)
  - `Send Drive Link` sends: `"Saved to Drive: {webViewLink}"` to `from_number` (chat ID)
  - All branches converge at `Collect Save Results`

### 4. Git — DONE
- Pushed to GitHub: commit `12f2f15`
- VPS not manually synced (orchestrator runs from Docker image, not git pull)

---

## What Still Needs Testing

### Priority 1 — End-to-End Test (NEW SESSION FIRST TASK)
Send a task via Telegram and verify:
1. Text reply received in Telegram ✓ (was working before this session)
2. `Always Save Sub` fires: check n8n execution log
3. `Save to GitHub` creates file in `agentHQ/outputs/{type}/` — needs GitHub credential re-auth first (see below)
4. `Save to Google Drive` uploads file to folder `1LWRslgiBwvLEbdh8Th9bKgVsHwFBFd1s`
5. Telegram sends back `"Saved to Drive: https://drive.google.com/..."` message

### Priority 2 — GitHub Credential Re-Auth (MANUAL in n8n UI)
The GitHub credential (`rY6J2xTXEwYt281i`) expired after an n8n update.
- Go to: n8n UI → Credentials → GitHub account → re-authenticate with OAuth
- This is blocking `Save to GitHub` node in sub-workflow

### Priority 3 — Concurrent Request Timeout
- Not addressed this session
- Original issue: n8n times out waiting for orchestrator when 2 requests come in simultaneously
- Fix options: increase n8n timeout (already 900s), or add async job queue on orchestrator side

### Priority 4 — Google Drive Auth
- Credential `dsY5XMdyJ0eFDEux` may need re-auth if Drive upload fails
- Test in sub-workflow execution log

---

## Architecture State (Current)

```
Telegram → Parse Message → Real Message? → Check Agent → [Ack + Run Agent Crew]
                                                              ↓
                                                       Format Result
                                                              ↓
                                              Send Result to Telegram bot
                                                              ↓
                                         ┌────────────────────┴──────────────────┐
                                    Archive to DB                         Always Save Sub
                                                                                  ↓
                                                                     Prepare Save Payload
                                                                   ↙        ↓          ↘
                                                           Save to      Convert to   Log to Notion
                                                           GitHub        File        (disabled)
                                                                           ↓
                                                                    Save to Drive
                                                                           ↓
                                                                    Send Drive Link
                                                                    (Telegram msg)
                                                                           ↓
                                                                  Collect Save Results
```

---

## Key IDs & Credentials

| Item | Value |
|------|-------|
| Main workflow | `a6ciAzyqvnXIC9lw` |
| Sub-workflow | `ppn7iH-oqxOUqdfzIGfDo` |
| VPS | `72.60.209.109` |
| Orchestrator port | `8000` |
| n8n URL | `https://n8n.srv1040886.hstgr.cloud` |
| n8n API key | In VPS SQLite: `docker run root-n8n-1` → sqlite on host at `/var/lib/docker/volumes/n8n_data/_data/database.sqlite` |
| GitHub repo | `bokar83/agentHQ` |
| Drive folder | `1LWRslgiBwvLEbdh8Th9bKgVsHwFBFd1s` |
| Telegram bot | `@agentsHQ4Bou_bot` |

---

## Files Changed This Session

- `orchestrator/orchestrator.py` — voice polish global, title/deliverable extraction, TaskResponse model
- `orchestrator/crews.py` — removed humanization task from all crews
- n8n main workflow `a6ciAzyqvnXIC9lw` — via REST API (not in git)
- n8n sub-workflow `ppn7iH-oqxOUqdfzIGfDo` — via REST API (not in git)
- Saved JSON snapshots: `d:/tmp/main_wf.json`, `d:/tmp/sub_wf.json`

## 2026-03-31 — Firecrawl MCP Added
- `~/.claude/mcp.json` updated to include `firecrawl-mcp` server
- API key: fc-479eab4... (stored in mcp.json env block)
- Restart Claude Code to activate
