# Tools Access Reference

Single source of truth for how every agent accesses external tools and services.
Read this before touching any integration. Never rediscover these from scratch.

---

## Gmail / Email

### Send or draft from boubacar@catalystworks.consulting (Signal Works outreach, cold email)

```python
from signal_works.gmail_draft import create_draft

draft_id = create_draft(
    to_email="recipient@example.com",
    subject="Subject line",
    html_body="<p>HTML body</p>",
)
```

**Credentials:** `secrets/gws-oauth-credentials-cw.json`
**Env var override:** `GOOGLE_OAUTH_CREDENTIALS_JSON_CW`
**Pattern:** Reads refresh_token, POSTs to `https://oauth2.googleapis.com/token`, calls Gmail API directly with httpx. No gws CLI needed.

### Send or draft from bokar83@gmail.com (Atlas content pipeline, default account)

Uses `orchestrator/tools.py` `_gws_request()`:

```python
from orchestrator.tools import _gws_request
resp = _gws_request("post", "https://gmail.googleapis.com/gmail/v1/users/me/drafts",
                    account="bokar83@gmail.com", json={"message": {"raw": raw_b64}})
```

**Credentials:** `secrets/gws-oauth-credentials.json`
**Env var override:** `GOOGLE_OAUTH_CREDENTIALS_JSON`

### Send scheduled emails (monkeybiz@catalystworks.consulting)

Uses `GWSMailSendTool` in `orchestrator/skills/doc_routing/gws_cli_tools.py`.
Calls `gws gmail users messages send` via subprocess (plain-text only, short body).
For HTML or large bodies, always use `gmail_draft.create_draft` instead.

### NEVER do this on Windows

- `subprocess.run(['gws', ...], shell=False)` - gws is a .cmd file, not found without shell
- Pass large JSON as `--json` CLI argument - hits Windows 8191-char limit
- Use stdin pipe to gws `--json -` - gws ignores stdin entirely
- Use `gws auth export` credentials with google-auth - refresh token scope mismatch

---

## VPS / SSH

```bash
ssh root@agentshq.boubacarbarry.com
# OR
ssh root@72.60.209.109
```

**App directory:** `/root/agentsHQ`
**Container:** `orc-crewai` (app), `orc-postgres` (DB)
**NEVER ask the user for these - grep docs/handoff or docker-compose.yml first**

### Run commands inside container

```bash
docker exec -it orc-crewai bash
# Or pipe a command:
echo "command" | docker exec -i orc-crewai bash
```

### Postgres (Supabase) via VPS

psql is NOT on the VPS host. Pipe SQL through Docker:

```bash
cat file.sql | docker exec -i orc-postgres psql -U postgres -d postgres
```

From Python (local or VPS), use `orchestrator.db.get_crm_connection()` - returns a psycopg2 connection with RealDictCursor. All fetchone/fetchall results are dicts, not tuples.

---

## Google Drive

### Upload a file

```bash
gws drive +upload --parent FOLDER_ID --name "filename" path/to/file
```

### Set public sharing

```bash
gws drive permissions create --params '{"fileId":"FILE_ID"}' --json '{"role":"reader","type":"anyone"}'
```

**Asset Library folder:** `05_Asset_Library/02_Videos/` ID: `1jvdSp0GggQi6-7o4WkS5Q-Jv3F1tjqE5`

---

## Notion

**Content Board DB:** `FORGE_CONTENT_DB` = `339bcf1a-3029-81d1-8377-dc2f2de13a20`
**Title field:** `Title` (NOT "Name")
**Drive field:** `Drive Link` (type `url`, NOT "Drive URL")
**Platform field:** type `multi_select`
**Status field:** type `select` (NOT `status`)
**Valid Content Types:** `Evergreen`, `Timely` only

Use MCP tool: `mcp__claude_ai_Notion__notion-create-pages`

---

## Vercel

### Demo site URLs (live)

| Site | URL | MP4 direct | Play page |
|---|---|---|---|
| Roofing | https://signal-works-demo-roofing.vercel.app | /pitch-reel.mp4 (live) | /play.html |
| Dental | https://signal-works-demo-dental.vercel.app | /pitch-reel.mp4 (live) | /play.html (live) |
| HVAC | local only - not deployed | - | - |

### Deploy a site

```bash
cd output/websites/signal-works-demo-<niche>
git add -A && git commit -m "deploy: <description>"
git push  # Vercel auto-deploys on push to main
```

If no remote: `vercel --prod` from the site directory.

---

## Calendly

**Discovery call URL:** `https://calendly.com/boubacarbarry/signal-works-discovery-call`
**User URI:** `https://api.calendly.com/users/9acb1142-7c25-4cc0-8bac-f03730fe73d8`
**Webhooks:** agentsHQ receives Calendly webhooks inbound only.

### How to create/manage event types (confirmed working from session logs 2026-04-17 and 2026-04-19)

Use the **claude.ai Calendly MCP tools** - already wired into this Claude Code instance, no separate login needed.

```text
Step 1: ToolSearch("select:mcp__claude_ai_Calendly__users-get_current_user,mcp__claude_ai_Calendly__event_types-create_event_type,mcp__claude_ai_Calendly__event_types-list_event_types")
Step 2: mcp__claude_ai_Calendly__users-get_current_user  --> get user URI
Step 3: mcp__claude_ai_Calendly__event_types-create_event_type with:
  {
    "create_event_type_request": {
      "owner": "https://api.calendly.com/users/9acb1142-7c25-4cc0-8bac-f03730fe73d8",
      "name": "Event Name",
      "duration": 30,
      "description": "...",
      "color": "#D4872A",
      "active": true,
      "locations": [
        {"kind": "zoom_conference"},
        {"kind": "google_conference"},
        {"kind": "ask_invitee"}
      ]
    }
  }
```

**No authentication step required.** The MCP is authenticated through claude.ai's OAuth integration.
**CRITICAL: This works. Previous memory incorrectly said event type creation was UI-only. The MCP can do it.**

### Available Calendly MCP tools (load via ToolSearch)

- `mcp__claude_ai_Calendly__users-get_current_user` - get user URI and timezone
- `mcp__claude_ai_Calendly__event_types-create_event_type` - create new event type
- `mcp__claude_ai_Calendly__event_types-list_event_types` - list all event types
- `mcp__claude_ai_Calendly__event_types-get_event_type` - get one event type
- `mcp__claude_ai_Calendly__event_types-update_event_type` - update event type
- `mcp__claude_ai_Calendly__event_types-list_event_type_available_times` - check availability
- `mcp__claude_ai_Calendly__meetings-list_events` - list scheduled meetings
- `mcp__claude_ai_Calendly__meetings-create_invitee` - book a meeting slot
- `mcp__claude_ai_Calendly__meetings-cancel_event` - cancel a meeting
- `mcp__claude_ai_Calendly__scheduling_links-create_single_use_scheduling_link` - one-time booking link

---

## GWS CLI (gws) - Windows quirks

- Binary is `gws.cmd` (npm global) - requires `shell=True` in subprocess OR call PowerShell
- Works fine when called directly from PowerShell interactive session
- FAILS when spawned as child process from Python via `-File` or `-Command` with JSON args
- **Use `signal_works/gmail_draft.py` instead for any email operation from Python**

---

## Signal Works Pipeline

### Daily sequence

```bash
# 1. Top up leads to 10 email minimum
python -m signal_works.topup_leads

# 2. Create drafts in boubacar@catalystworks.consulting (real run)
python -m signal_works.send_drafts --run

# 2b. Test run (adds [TEST], does NOT mark drafted)
python -m signal_works.send_drafts --run --test

# Check count
python -m signal_works.send_drafts --count
```

### Key files

| File | Purpose |
|---|---|
| `signal_works/email_builder.py` | Renders personalized HTML per lead (has-website + no-website variants) |
| `signal_works/gmail_draft.py` | Creates Gmail drafts from boubacar@catalystworks.consulting |
| `signal_works/send_drafts.py` | Daily runner: render + draft + mark |
| `signal_works/topup_leads.py` | Harvests until >= 10 email leads in DB |
| `signal_works/morning.bat` | One-click morning runner (topup + send_drafts) |

### Lead qualification rule

Only save leads with at minimum a phone number. Discard if no phone, no email, AND no website.

---

## Telegram (notifications)

Bot token: `TELEGRAM_BOT_TOKEN` env var
Chat ID: `TELEGRAM_CHAT_ID` env var

```python
from orchestrator.notifier import send_telegram
send_telegram("message text")
```

---

## Firecrawl (web scraping)

Default tool for any web content. 3 tools: scrape / crawl / search.
3000 credits/month. Resets May 14. Use sparingly for bulk scrapes.

```python
from orchestrator.tools import firecrawl_scrape, firecrawl_search
```

---

## n8n

**HARD RULE:** Never docker stop/restart/cp on n8n. Never edit SQLite directly. Use n8n UI or REST API only.
n8n API key location: `.env` as `N8N_API_KEY`.

---

*Last updated: 2026-04-27. Update this file whenever a new integration is wired or an existing one changes.*
