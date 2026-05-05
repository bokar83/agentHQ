# Session Handoff - TOOLS_ACCESS.md Overhaul + Calendly Fix - 2026-04-27

## TL;DR

Boubacar corrected a false claim from a previous session (Claude said it couldn't log into Calendly
or create events: it was wrong). We dug through session .jsonl logs to confirm the actual method
(claude.ai Calendly MCP, confirmed working 2026-04-17 and 2026-04-19). Then did a full audit and
overhaul of `docs/reference/TOOLS_ACCESS.md`, which was badly out of date: missing Hostinger,
Supabase, NotebookLM, AutoCLI, Blotato, YouTube, and beehiiv entirely, and had wrong Calendly info.

## What was built / changed

- `docs/reference/TOOLS_ACCESS.md`: MAJOR overhaul. Sections fixed and added:
  - **Fixed:** Calendly (was "UI only, use Playwright": actually MCP works with no auth step)
  - **Fixed:** Telegram (added "use Python urllib NOT curl" rule + working code snippet)
  - **Fixed:** Calendly entry now includes Signal Session Audit URL + User URI
  - **Added:** Supabase section (CRM schema, pipeline values, all inbound wiring sources)
  - **Added:** Hostinger section (static vs Node.js deploy, GitHub auto-deploy, Tailwind v4, hcdn cache gotchas, process cap diagnosis)
  - **Added:** NotebookLM section (CLI invocation local+VPS, auth re-login flow, all 8 CW notebook IDs, REAUTH_NEEDED marker)
  - **Added:** AutoCLI section (binary path, Chrome extension location, skool.com exclusion)
  - **Added:** Blotato section (Python module `orchestrator/blotato_publisher.py`, effective pricing, all API gotchas: 201 not 200, scheduledTime root-level, poll pattern, Notion→Blotato platform name mapping)
  - **Added:** YouTube section (current state: nothing wired; Path A Blotato, Path B Data API v3, Path C = lens skill is analysis only; yt-dlp download pattern)
  - **Added:** beehiiv section (newsletter platform, future API path, hard rule against Mailgun/SendGrid)
  - **Added:** Google Drive MCP note alongside existing gws CLI pattern
  - **Added:** Vercel section correctly updated (Dental pitch reel now live)

- `memory/reference_calendly_api_method.md`: completely rewritten. Old content said "UI only".
  New content documents the confirmed MCP method, user URI, all 10 available Calendly MCP tools.

- `memory/MEMORY.md`: two index entries updated:
  - Tools Access Reference: expanded description to reflect the new scope
  - Calendly API Method: corrected from "UI-only" lie to confirmed MCP method

## Decisions made

- `docs/reference/TOOLS_ACCESS.md` is the canonical single source of truth for ALL tool access.
  Every agent should read it before touching any integration. It now covers all active tools.
- Calendly event type creation via MCP is the standard path going forward. No Playwright needed.
- YouTube: Blotato (Path A) is the lowest-effort path when Studio M4 needs YouTube publishing.
  No new code needed: just connect the account in Blotato dashboard and use existing `blotato_publisher.py`.

## What is NOT done (explicit)

- TOOLS_ACCESS.md still missing: GitHub (gh CLI patterns), Stripe, Supabase MCP tool examples
- No actual Calendly event was created this session: the fix was documentation + memory only
- YouTube is documented but not wired: Studio M4 decision

## Open questions

- Boubacar asked about a shared file "for all agents telling you how to log in and execute things."
  TOOLS_ACCESS.md is that file. But it lives in the repo, not in a shared memory location accessible
  to all Claude Code instances. Consider whether it should also be mirrored to
  `~/.claude/projects/.../memory/` as a reference file, or whether pointing MEMORY.md to it is enough.

## Next session must start here

1. Read `docs/reference/TOOLS_ACCESS.md`: this is now the master integration reference
2. If a Calendly event is needed, use the MCP method documented there (no login, just ToolSearch + 3 steps)
3. If any integration is missing from TOOLS_ACCESS.md, add it before doing the work

## Files changed this session

```
docs/reference/TOOLS_ACCESS.md                             : full overhaul
memory/reference_calendly_api_method.md                    : rewritten (Calendly MCP method)
memory/MEMORY.md                                           : 2 index entries updated
```
