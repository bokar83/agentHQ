# Handoff — 2026-04-19 — calculatorz.tools cache fix + hosting upgrade

## Summary

Two cascading issues on calculatorz.tools resolved tonight:
1. **Stale hcdn cache** serving 2.9-day-old "Go Pro" prerender despite fresh deploys
2. **Site-wide 503s** from Hostinger process cap (120) being hit across 12 websites

Site is now healthy. AdSense resubmission was already in flight; nothing to undo.

## Actions Taken

### Cache fix (calculatorz-app)
- Added global `headers()` in `next.config.ts`: `public, max-age=0, s-maxage=60, must-revalidate`
- Added `export const revalidate = 60` to `app/page.tsx`
- Shipped temporary no-store middleware on `/` to force hcdn eviction
- Boubacar triggered **Kodee AI** (hPanel) to force-purge hcdn
- Verified homepage served new code (no "Go Pro" nav)

### Dead repo cleanup
- Archived `bokar83/calculatorz-site` on GitHub (isArchived: true)
- Renamed local `output/websites/calculatorz-site/` → `calculatorz-site.ARCHIVED`
- Only `calculatorz-app` is the live deploy target

### 503 outage diagnosis
- stderr showed `uv_thread_create` assertion failures in `node_platform.cc:68`
- console.log showed 28+ "Ready in 0ms" (Node respawning)
- `curl localhost:3000` inside SSH returned "Connection refused"
- Manual `node server.js` worked → confirmed not a code bug
- Root cause: **Max Processes cap 88/120**, Resources Usage 97%
- Fix: `pkill -u u507946419 -f 'node|lsnode'` + redeploy + Boost Now (24h Cloud Professional, 400 processes)
- All URLs returned 200 after boost

### AdSense final E-E-A-T audit
- `/about/` — real content, MBAs, 20+ yrs
- `/editorial-standards/` — 8 substantive sections
- `/contact/` — 3 working emails
- `/finance/tip-calculator/` — 8 FAQs, April 2026 date
- `/health/bmi/` — medical disclaimer, WHO/CDC/Harvard citations

### Hostinger upgrade decision
- User confirmed intent to upgrade to **Cloud Startup** ($11.99/mo, 12-month, $36.88 net after $107 balance credit)
- Renews 2027-04-19 at $25.99/mo
- Unlocks 10 Node.js apps, 100 PHP workers, dedicated IP, 100 MySQL connections

## Lessons Learned (saved to memory)

1. **[feedback_hostinger_hcdn_cache_purge.md]** — Always ship no-store middleware on `/` with code changes; hcdn has no purge UI for Node.js apps
2. **[feedback_hostinger_process_cap.md]** — 503 + `uv_thread_create` = process cap, NOT code. Check Resources panel before editing anything
3. **[feedback_dead_repo_archive_workflow.md]** — GitHub archive + `.ARCHIVED` folder rename, always both
4. **[project_hostinger_plan_upgrade.md]** — Cloud Startup upgrade record for 30-day money-back window tracking

## Remaining — For Next Session

### Do first (billing)
- [ ] Confirm Cloud Startup upgrade completed in hPanel
- [ ] Verify Max Processes cap rose permanently above 120 (not the 400 boost-temp number)
- [ ] Note: Boost Now expires ~2026-04-20; watch for sustained-cap behavior after boost ends

### Cleanup
- [ ] Remove the temporary no-store middleware once hcdn eviction is confirmed stable (currently at `output/apps/calculatorz-app/middleware.ts` — may have been deleted already; verify)
- [ ] Restore normal caching by keeping `s-maxage=60, must-revalidate` from `next.config.ts` + `revalidate=60` on pages

### Optional
- [ ] Consider consolidating/archiving unused sites out of 12 total to reduce baseline process usage even after upgrade
- [ ] AdSense re-crawl happens 1-14 days — no action needed, just monitor
- [ ] If user wants to push E-E-A-T further: add individual reviewer names to articles, affiliate disclosure on tip-calculator if it links to affiliates

## Key Files Touched

- `d:/Ai_Sandbox/agentsHQ/output/apps/calculatorz-app/next.config.ts`
- `d:/Ai_Sandbox/agentsHQ/output/apps/calculatorz-app/app/page.tsx`
- `d:/Ai_Sandbox/agentsHQ/output/apps/calculatorz-app/middleware.ts` (temp)
- `d:/Ai_Sandbox/agentsHQ/output/websites/calculatorz-site.ARCHIVED/` (renamed)

## Tripwires

- 30-day money-back window on Cloud Startup upgrade closes **2026-05-19**
- If process issues recur after upgrade: consolidation is the next lever, not another upgrade
- If hcdn serves stale again: Kodee purge works; don't waste time on code alone
