# Handoff — Hostinger Migration + Baobab Deploy
**Date:** 2026-04-15
**Session focus:** Upgraded Hostinger to Business plan, migrated calculatorz.tools and Baobab to Node.js hosting

---

## What Was Done

### Hostinger Upgrade
- Upgraded from Premium ($3.99) to Business ($5.99/mo) — paid $0 via Hostinger balance credit through 2027-04-15
- Now have: 50 websites, 5 Node.js app slots, 50GB NVMe, daily backups, 5 mailboxes/site

### calculatorz.tools — Migrated to Node.js
- Deleted static site setup, created Node.js app pointing to `bokar83/calculatorz-app`
- Removed `output: 'export'` and `images: { unoptimized: true }` from next.config.ts
- Removed `--webpack` flag from build script
- Removed PWA plugin (was injecting webpack config incompatible with Next.js 16 Turbopack)
- Added `turbopack: {}` to next.config.ts to satisfy Turbopack requirement
- Env var set: `NEXT_PUBLIC_ADSENSE_PUBLISHER_ID=pub-0698915573244960`
- Status: **deployed and live**

### Baobab — New Deploy at baobab.boubacarbarry.com
- Created Node.js app on Hostinger subdomain `baobab.boubacarbarry.com`
- Repo: `bokar83/baobab-app`, branch `main`, Node 20.x
- Fixed build crash: Supabase client was initializing at module load time — rewrote as `getSupabase()` lazy factory returning null when env vars absent
- Fixed 503 on practice sessions: chat route was using `toTextStreamResponse()` — incompatible with `useChat`/`DefaultChatTransport`. Switched to `toDataStreamResponse()`
- Env vars added: `OPENROUTER_API_KEY`, `NOTION_API_KEY`, `PRACTICE_SESSIONS_DB_ID`, `SUPABASE_URL`, `SUPABASE_SERVICE_KEY`
- Status: **deployed and live**

### Decisions Made
- Baobab does not need a separate marketing website — the app is the product
- Homepage splash screen (was PWA-powered) is intentionally not rebuilt — the silence screen before sessions is the right ceremony moment, homepage splash is just friction
- Node.js slot budget: calculatorz (1) + Baobab (1) = 2 used, 3 remaining

---

## Open Items for Next Session

1. **calculatorz.tools — verify live and AdSense** — confirm the Node.js deploy is serving correctly, check AdSense review status (submitted Apr 15)
2. **Baobab — test full session flow** — run a complete practice session end to end: silence screen, conversation, end session, analysis, results page
3. **Hostinger mailboxes** — set up additional mailboxes on catalystworks.consulting (have 5 free slots now): hello@, outreach@, noreply@
4. **Node.js slot plan** — decide what goes in slots 3-5: Clone Factory outputs? Next revenue app?
5. **Clone Factory sites on Hostinger** — 48 website slots available for AdSense/affiliate clone sites

---

## Prompt to Continue Tomorrow

```
We're continuing the Hostinger migration session from Apr 15.

What was done:
- Upgraded to Business plan (50 sites, 5 Node.js slots)
- calculatorz.tools: migrated from static export to Node.js on Hostinger (bokar83/calculatorz-app). Removed PWA, output:export, added turbopack:{}.
- Baobab: deployed at baobab.boubacarbarry.com. Fixed lazy Supabase init crash, fixed 503 by switching toTextStreamResponse to toDataStreamResponse.

What to do now:
1. Verify calculatorz.tools is fully live and check AdSense review status
2. Test Baobab end-to-end: full practice session through to results page
3. Set up additional mailboxes on catalystworks.consulting (5 free slots on Business plan)
4. Decide what goes in remaining 3 Node.js slots

Hostinger Node.js slots used: calculatorz.tools (1), baobab.boubacarbarry.com (1). 3 slots remaining.
```
