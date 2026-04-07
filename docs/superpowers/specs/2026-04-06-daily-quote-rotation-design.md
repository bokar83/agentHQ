# Daily Quote Rotation — Design Spec
**Date:** 2026-04-06  
**Status:** Approved  
**Author:** Boubacar Barry / Claude Code

---

## What We're Building

A daily motivational quote rotation that:
1. Runs at 6:00 AM MT on the VPS (inside the orchestrator Docker container)
2. Updates the quote callout on two Notion pages: agentsHQ landing + The Forge 2.0
3. Sends a Telegram message to Boubacar with the quote of the day
4. Is fully independent of his local machine -- runs whether his computer is on or not

---

## Architecture

### Where It Lives
`orchestrator/scheduler.py` -- new function `_run_quote_rotation()` called at 6am alongside the existing `_run_kpi_refresh()` and `_run_daily_harvest()`.

### Quote Bank
`docs/quote_bank.json` -- 100 quotes curated to match Boubacar's character:
- Stoics (Marcus Aurelius, Seneca, Epictetus)
- Builders/founders (Reid Hoffman, Mark Cuban, Bezos, Buffett)
- HR/OD/leadership (Peter Drucker, Simon Sinek, Brene Brown)
- War generals and strategists (Sun Tzu, Patton, Churchill)
- African/Guinean/diaspora voices (where verified)
- Sales and revenue truth-tellers
- Funny but true (Homer Simpson, movie quotes that land)
- Athletes (Gretzky, Ali, Jordan, Kobe)

**Rotation formula:** `index = day_of_year % len(quotes)` (deterministic, no randomness, same quote all day on all devices)

### Notion Updates (Direct REST API)
The VPS scheduler calls the Notion REST API directly (no MCP -- MCP is only available in Claude Code sessions).

Two pages to update:
- `agentsHQ`: `327bcf1a-3029-80b7-9b1e-d77f94c9c61c`
- `The Forge 2.0`: `249bcf1a-3029-807f-86e8-fb97e2671154`

**Strategy:** The quote lives in a specific callout block. We store the block IDs on first run (or hardcode after discovery), then use `PATCH /v1/blocks/{block_id}` to update the callout text in place. No full page replacement.

Block IDs are discovered once via `GET /v1/blocks/{page_id}/children` and stored in `docs/quote_block_ids.json`.

### Telegram Notification
Calls `_send_telegram_alert()` (already in scheduler.py) with a formatted message:

```
💬 Quote of the Day

"[quote text]"

-- [author]

Have a sharp one. agentsHQ
```

---

## Implementation Plan

### 1. Expand quote bank to 100 quotes
File: `docs/quote_bank.json`

### 2. Create `docs/quote_block_ids.json`
Stores the discovered block IDs for the two quote callouts so we don't search every run.

```json
{
  "agentsHQ_quote_block_id": "...",
  "forge_quote_block_id": "..."
}
```

### 3. Add `_run_quote_rotation()` to `orchestrator/scheduler.py`
```python
def _run_quote_rotation():
    """Update daily quote on agentsHQ + The Forge 2.0, then send to Telegram."""
    # 1. Load quote bank
    # 2. Pick quote by day_of_year % len(quotes)
    # 3. Load block IDs (or discover + save them)
    # 4. PATCH both Notion callout blocks via REST API
    # 5. Send Telegram message
```

### 4. Hook into `_scheduler_loop()` at 6am
Call `_run_quote_rotation()` first (before harvest) so the quote is set before the morning report lands.

### 5. Test flag in `__main__`
`python scheduler.py --test-quotes` fires quote rotation immediately without waiting for 6am.

---

## Environment Variables Required
- `NOTION_API_KEY` -- already in .env for the forge KPI refresh
- `ORCHESTRATOR_TELEGRAM_BOT_TOKEN` -- already in scheduler.py
- `TELEGRAM_CHAT_ID` -- already in scheduler.py

No new secrets needed.

---

## Error Handling
- Notion API failure: log error, send Telegram alert, do NOT crash scheduler
- Quote bank file missing: fall back to hardcoded emergency quote, log warning
- Block ID not found: re-discover via page children API, update `quote_block_ids.json`
- All failures are non-blocking -- harvest still runs

---

## Files Changed
- `docs/quote_bank.json` -- expanded to 100 quotes
- `docs/quote_block_ids.json` -- new, created on first run
- `orchestrator/scheduler.py` -- add `_run_quote_rotation()`, hook into loop

---

## Out of Scope
- n8n workflow (Option B, rejected)
- Claude Code cron (Option C, rejected)
- Randomization (deterministic rotation preferred -- same quote all day)
- Quote submission UI (manual edit of quote_bank.json is sufficient)
