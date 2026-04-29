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

## Telegram (notifications)

**Bot:** `agentsHQ4Bou_bot`
**Env vars:** `ORCHESTRATOR_TELEGRAM_BOT_TOKEN`, `TELEGRAM_CHAT_ID` (Boubacar's private chat: `7792432594`)

### From orchestrator (Python)

```python
from orchestrator.notifier import send_telegram
send_telegram("message text")
```

### Ad-hoc from any Python script

Use `urllib.request.urlopen` directly: **do NOT use curl** (exits 35, SSL failure on this network):

```python
import urllib.request, urllib.parse, json, os

token = os.environ["ORCHESTRATOR_TELEGRAM_BOT_TOKEN"]
chat_id = os.environ["TELEGRAM_CHAT_ID"]
data = urllib.parse.urlencode({"chat_id": chat_id, "text": "your message"}).encode()
urllib.request.urlopen(f"https://api.telegram.org/bot{token}/sendMessage", data, timeout=15)
```

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

## Supabase (hosted CRM database)

**Project ID:** `jscucboftaoaphticqci`
**Single source of truth for all lead/CRM data. Never use Airtable.**

Use the `mcp__claude_ai_Supabase__execute_sql` MCP tool for direct queries (load via ToolSearch).

### Key tables

| Table | Purpose |
|---|---|
| `leads` | All CRM leads: name, company, title, location, phone, linkedin_url, email, industry, source, status, notes, created_at, updated_at, last_contacted_at |

### Pipeline status values

`new` → `messaged` → `replied` → `booked` → `paid`

### Inbound wiring (live via n8n)

- boubacarbarry.com contact form → `source: 'boubacarbarry.com - Contact Form'`
- boubacarbarry.com Calendly → `source: 'boubacarbarry.com - Calendly'`, `status: 'Discovery Booked'`
- catalystworks.consulting contact → `source: 'catalystworks.consulting - Contact Form'`
- Notion mirrors leads for human-readable view (n8n sync workflow live)

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

Also available: `mcp__claude_ai_Google_Drive__*` MCP tools (load via ToolSearch) for search, read, create, share.

---

## Notion

**Content Board DB:** `FORGE_CONTENT_DB` = `339bcf1a-3029-81d1-8377-dc2f2de13a20`
**Title field:** `Title` (NOT "Name")
**Drive field:** `Drive Link` (type `url`, NOT "Drive URL")
**Platform field:** type `multi_select`
**Status field:** type `select` (NOT `status`)
**Valid Content Types:** `Evergreen`, `Timely` only

Use MCP tool: `mcp__claude_ai_Notion__notion-create-pages` (load via ToolSearch)

---

## Calendly

**Discovery call URL:** `https://calendly.com/boubacarbarry/signal-works-discovery-call`
**Signal Session Audit URL:** `https://calendly.com/bokar83/signal-session-ai-data-exposure-audit`
**User URI:** `https://api.calendly.com/users/9acb1142-7c25-4cc0-8bac-f03730fe73d8`
**Webhooks:** agentsHQ receives Calendly webhooks inbound via n8n → `/inbound-lead` endpoint.

### How to create/manage event types (confirmed working 2026-04-17 and 2026-04-19)

Use the **claude.ai Calendly MCP tools** - already wired into Claude Code, no separate login needed.

```text
Step 1: ToolSearch("select:mcp__claude_ai_Calendly__users-get_current_user,mcp__claude_ai_Calendly__event_types-create_event_type,mcp__claude_ai_Calendly__event_types-list_event_types")
Step 2: mcp__claude_ai_Calendly__users-get_current_user : verify user URI
Step 3: mcp__claude_ai_Calendly__event_types-create_event_type
```

```json
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

**No authentication step required.** MCP is authenticated through claude.ai's OAuth.

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

## Hostinger (static and Node.js site deployments)

**Plan:** Cloud Startup ($11.99/mo, 10 Node.js apps). Renews 2027-04-19.

### Static sites (catalystworks-site, humanatwork-site, signal-works demos)

Each site is a **separate GitHub repo**, connected to Hostinger via GitHub native integration:
- Push to `main` = auto-deploy (no FTP, no manual step)
- `dev` branch = staging

```bash
# From the site's local repo directory:
git add -A && git commit -m "deploy: <description>"
git push  # triggers Hostinger auto-deploy
```

**Repo pattern:** `bokar83/<site-name>` (e.g. `bokar83/catalystworks-site`, `bokar83/humanatwork-site`)

### Node.js apps (calculatorz-app and similar)

- Hostinger runs `npm run build` and serves from `.next`: NOT a static export
- Never use `output: 'export'` in next.config.ts (produces `out/` which Hostinger ignores)
- Always push to the correct app repo (e.g. `calculatorz-app`), not any secondary repo

### Tailwind v4 specifics (calculatorz-app)

- Uses `@tailwindcss/postcss`: NO `tailwind.config.ts` (that's v3)
- Content scanning via `@source` directives in `globals.css` for components/, app/, lib/

### Cache / CDN gotchas

- hcdn aggressively caches prerendered routes with `s-maxage=31536000` (1 year)
- Always ship cache-busting middleware with any visual change deploy:

```ts
// middleware.ts
import { NextResponse } from 'next/server'
import type { NextRequest } from 'next/server'
export function middleware(request: NextRequest) {
  const response = NextResponse.next()
  if (request.nextUrl.pathname === '/') {
    response.headers.set('Cache-Control', 'no-store, must-revalidate')
    response.headers.set('CDN-Cache-Control', 'no-store')
  }
  return response
}
export const config = { matcher: ['/'] }
```

- If site still serves stale after deploy: tell Boubacar to open hPanel → Kodee AI → ask to purge hcdn cache. That is the only working purge path for Node.js apps.
- Diagnose stale cache: `curl -sIk https://site/` returns `Age: <large>` + `x-hcdn-cache-status: HIT`

### Default cache headers for Hostinger Next.js apps

```ts
// next.config.ts
async headers() {
  return [{
    source: '/:path*',
    headers: [{ key: 'Cache-Control', value: 'public, max-age=0, s-maxage=60, must-revalidate' }],
  }]
}
```

### Process cap (503s)

If you see `uv_thread_create` assertion + site-wide 503: process cap hit, not code bug. Check hPanel → Resources before debugging code.

---

## Vercel (Signal Works demo sites)

### Demo site URLs (live)

| Site | URL | MP4 direct | Play page |
|---|---|---|---|
| Roofing | https://signal-works-demo-roofing.vercel.app | /pitch-reel.mp4 (live) | /play.html |
| Dental | https://signal-works-demo-dental.vercel.app | /pitch-reel.mp4 (live) | /play.html (live) |
| HVAC | local only - not deployed | - | - |

### Deploy a Vercel site

```bash
cd output/websites/signal-works-demo-<niche>
git add -A && git commit -m "deploy: <description>"
git push  # Vercel auto-deploys on push to main
```

If no remote: `vercel --prod` from the site directory.

---

## NotebookLM

**Tool priority:** CLI first, MCP backup. Never use `mcp__notebooklm-mcp__*` if the CLI works.

### CLI invocation

**Local (Windows, from agentsHQ venv):**

```bash
d:/Ai_Sandbox/agentsHQ/.venv/Scripts/python.exe ~/.claude/skills/notebooklm/scripts/nlm.py <command>
```

**VPS:**

```bash
python3 ~/.claude/skills/notebooklm/scripts/nlm.py <command>
```

Never call `python -m notebooklm` with system Python (`C:\Program Files\Python313`) - notebooklm-py is only in the agentsHQ venv.
In PowerShell, use the full path above - `nlm.exe` is not on PATH.

### Auth

- Cookies: `~/.notebooklm/storage_state.json` (local and VPS)
- Cookies expire every 7-30 days
- Re-login: `.venv/Scripts/python.exe -m notebooklm login` in agentsHQ PowerShell (interactive: press ENTER in terminal after NotebookLM loads, NOT in browser)
- After re-login: `scp C:/Users/HUAWEI/.notebooklm/storage_state.json root@72.60.209.109:~/.notebooklm/storage_state.json`
- VPS auto-refresh cron runs every 3 days at 05:30 UTC (script: `scripts/notebooklm_auth_refresh.py`)
- If `~/.notebooklm/REAUTH_NEEDED` exists on VPS: Google session expired, manual re-login required

### Key notebook IDs (CW_* = Catalyst Works)

| Notebook | ID |
|---|---|
| CW_Catalyst Works Ops | `a5c23cdf-8d26-4849-b204-b98fb3a618f9` |
| CW_Audience Engine | `e246e525-8618-47ef-afd6-e279eed17d37` |
| CW_Learning Lab | `bf152426-3e69-4d99-b7f9-54b3ce372911` |
| CW_Frameworks and IP | `1f88870c-1e40-42ba-9921-964b08a6ef45` |
| CW_Content Studio | `18d8f6a5-276f-4da8-8f61-6c922e846ba8` |
| CW_Client Work | `4975cb22-112a-4a53-b3bb-c7e2f0b543cb` |
| CW_Research | `e6715ad0-f85a-4f9f-a262-9146335b28f3` |
| CW_Ideas | `3325eaf0-33fc-4421-9575-e4ab452da177` |

---

## AutoCLI (web CLI bridge, formerly opencli-rs)

**Binary:** `autocli.exe` (also aliased as `opencli-rs.exe` for back-compat)
**Path:** `C:\Users\HUAWEI\AppData\Local\Microsoft\WindowsApps\`
**Chrome extension:** unpacked at `C:\Users\HUAWEI\autocli-extension\` (do NOT move: Chrome reads it on every startup)

Requires Chrome running + daemon on `127.0.0.1:19825`. Diagnose with `autocli doctor`.

**Sites NOT supported (do not waste time):**
- `skool.com` - use `scripts/skool-harvester/` with saved Playwright session at `~/.claude/playwright-state/skool.json` instead

---

## Firecrawl (web scraping)

Default tool for any web content. 3 tools: scrape / crawl / search.
3000 credits/month. Resets May 14. Use sparingly for bulk scrapes.

```python
from orchestrator.tools import firecrawl_scrape, firecrawl_search
```

---

## Blotato (social publishing)

**API base:** `https://backend.blotato.com/v2`
**Auth:** `BLOTATO_API_KEY` env var (header: `blotato-api-key`)
**Python module:** `orchestrator/blotato_publisher.py` (verified end-to-end 2026-04-25)
**Status:** Active on Atlas (LinkedIn + X). Inactive for Studio (YouTube, IG, TikTok, etc.) until Studio M4.

**Boubacar's effective pricing (30% Skool RoboNuggets discount, lifetime):**

| Tier | Effective/mo | Credits/mo | Accounts | Use |
|---|---|---|---|---|
| Starter | $20.30 | 1,250 | 20 | Atlas (LinkedIn + X only) |
| Creator | $67.90 | 5,000 | 40 | Studio M4 (multi-channel) |

Always quote effective price, not list ($29/$97). WebFetch blotato.com/pricing before any new build.

### Python usage

```python
from orchestrator.blotato_publisher import get_publisher, list_accounts

# List connected accounts to get account IDs
accounts = list_accounts()

# Publish immediately
pub = get_publisher()
result = pub.publish_and_wait(
    text="Post content here",
    account_id="<blotato_account_id>",
    platform="linkedin",  # or "twitter", "youtube", "instagram", "tiktok", "threads", etc.
)
# result.ok, result.public_url, result.status

# Publish with media
result = pub.publish_and_wait(
    text="Post with image",
    account_id="<account_id>",
    platform="twitter",
    media_urls=["https://public-url-to-image.jpg"],
)

# Scheduled post (scheduledTime is ROOT-LEVEL, NOT inside post: misnesting causes silent immediate publish)
post_id = pub.publish(text="...", account_id="...", platform="linkedin",
                      scheduled_time_iso="2026-05-01T09:00:00-06:00")
result = pub.poll_until_terminal(post_id)
```

### Platform name mapping (Notion → Blotato)

`X` → `twitter`, `LinkedIn` → `linkedin`, `YouTube` → `youtube`, `Instagram` → `instagram`,
`TikTok` → `tiktok`, `Threads` → `threads`, `Facebook` → `facebook`, `Pinterest` → `pinterest`

### Account IDs (from Blotato dashboard → Accounts tab)

| Account                       | Platform  | Blotato Account ID      |
| ----------------------------- | --------- | ----------------------- |
| boubacarbarry (personal)      | X/Twitter | `17065`                 |
| boubacarbarry (personal)      | LinkedIn  | `19365`                 |
| Catalyst Works (company page) | LinkedIn  | `114214027` (page ID)   |
| Baobab YouTube                | YouTube   | `34864`                 |
| Catalyst Works YouTube        | YouTube   | `34865`                 |

**To post to X:** `account_id = os.environ["BLOTATO_X_ACCOUNT_ID"]` (= `17065`)
**To post to LinkedIn (personal):** `account_id = "19365"`
**To post to LinkedIn (company page):** `account_id = os.environ["BLOTATO_LINKEDIN_PAGE_ID"]` (= `114214027`)

**NEVER leave BLOTATO_API_KEY as the string `EMPTY` in .env.** Always sync local `.env` to VPS via:

```bash
scp "d:/Ai_Sandbox/agentsHQ/.env" root@72.60.209.109:/root/agentsHQ/.env
```

### Key gotchas (verified 2026-04-25)

- POST returns 201, not 200: use `status_code not in (200, 201)` for error checks
- `scheduledTime` is a root-level field in the request body, sibling of `post`: never nest it inside `post`
- Poll status via `GET /v2/posts/{id}`: states: `in-progress` → `published` or `failed`
- `publicUrl` and `errorMessage` may be top-level OR nested under `"post"` key: check both
- n8n workflow `6XEaB5k7Kz4ubEck` ("RN | Notion Social Media Posting via Blotato") exists but is inactive

---

## YouTube

**No direct API integration today.** YouTube is a Blotato-supported platform (`platform="youtube"`) but not yet wired.

### Current state

- Blotato supports YouTube (verified in `SUPPORTED_PLATFORMS` in `blotato_publisher.py`)
- No YouTube account currently connected in Blotato
- No YouTube Data API v3 credentials in `.env`

### When YouTube upload is needed (Studio M4+)

**Path A: Blotato (simplest):** Connect YouTube account in Blotato dashboard, then use `blotato_publisher.py` with `platform="youtube"`. No separate API creds needed.

**Path B: YouTube Data API v3 (direct):**

```text
1. Create OAuth2 app in Google Cloud Console (same project as gws)
2. Enable YouTube Data API v3
3. Scopes: https://www.googleapis.com/auth/youtube.upload
4. Store credentials in secrets/gws-oauth-credentials-yt.json
5. Upload via: POST https://www.googleapis.com/upload/youtube/v3/videos
   with multipart body (metadata JSON + video binary)
```

**Path C: youtube-10k-lens skill:** The `/youtube-10k-lens` skill is for ANALYZING YouTube videos (transcript + $10K revenue lens), not uploading.

### Downloading/transcribing YouTube content

Use the `transcribe` skill or `yt-dlp`:

```bash
# Download audio only
yt-dlp -x --audio-format mp3 -o "%(title)s.%(ext)s" "https://youtube.com/watch?v=..."

# Get transcript (if captions exist)
yt-dlp --write-auto-sub --skip-download "https://youtube.com/watch?v=..."
```

---

## beehiiv (newsletter)

**Current state:** newsletter_crew drafts content; Boubacar pastes into beehiiv manually.
**Future:** beehiiv REST API for direct draft creation.

```text
POST /publications/{pub_id}/posts
Auth: BEEHIIV_API_KEY env var
Pub ID: BEEHIIV_PUBLICATION_ID env var
```

**NEVER** use n8n Mailgun/SendGrid for newsletter delivery: beehiiv is the platform.

---

## GWS CLI (gws) - Windows quirks

- Binary is `gws.cmd` (npm global) - requires `shell=True` in subprocess OR call PowerShell
- Works fine when called directly from PowerShell interactive session
- FAILS when spawned as child process from Python via `-File` or `-Command` with JSON args
- **Use `signal_works/gmail_draft.py` instead for any email operation from Python**

---

## n8n

**HARD RULE:** Never docker stop/restart/cp on n8n. Never edit SQLite directly. Use n8n UI or REST API only.
n8n API key location: `.env` as `N8N_API_KEY`.

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

*Last updated: 2026-04-27. Update this file whenever a new integration is wired or an existing one changes.*
