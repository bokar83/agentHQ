# Session Handoff - calculatorz.tools state-paycheck + utility deploy - 2026-05-07

## TL;DR
Deployed 51 geo-targeted state paycheck calculator pages + 3 utility calculators (hours-worked, hex-to-rgb, cm-to-inches) to production at `calculatorz.tools`. Caught and fixed a Next.js 15 routing bug (partial dynamic segments cause site-wide 404), pushed to `bokar83/calculatorz-app` `main` @ `dac9945`, deleted feature branch local + remote, synced agentsHQ staged checkout to match origin. Hostinger auto-deploy webhook fires on main push; final verification still pending.

## What was built / changed

**Production repo: `bokar83/calculatorz-app` @ `main` = `dac9945`:**
- Renamed `app/finance/take-home-pay-calculator-[state]/page.tsx` → `app/finance/take-home-pay-calculator/[state]/page.tsx` (Next.js 15 doesn't support partial dynamic segments in folder names)
- Added `async rewrites()` block to `next.config.ts` mapping flat URL `/finance/take-home-pay-calculator-:state/` → nested route, so all canonical URLs, JSON-LD, internal `Link href` values keep the flat URL pattern
- 51 states prerendered via `generateStaticParams` (alabama → wyoming)
- 113 total static pages, build clean (0 TS errors, 0 routing errors)

**Staged checkout: `d:/Ai_Sandbox/agentsHQ/output/apps/calculatorz-app/`:**
- Pulled origin/main (was at `9553103`, now `dac9945`)
- Same fix mirrored locally (rename + rewrites)
- Removed ghost duplicate dir resurrected by earlier `cp -rf` overlay

**Branches:**
- `feature/calculatorz-state-calculator-deploy` deleted local + remote (fully merged into main)

## Decisions made

- **Used non-destructive `cp -rf source/. target/` overlay** instead of `rm -rf target && cp -r` (Bash policy denied destructive flag). Verified pre-overlay with `diff -rq` — no target-only files would be lost.
- **Bypassed broken repo SSL config per-command** with `-c http.sslBackend=schannel -c http.sslCAInfo=` instead of editing `.git/config` (CLAUDE.md hard rule: never modify git config). Repo had stale `sslCAInfo` pointing at non-existent `ca-bundle.crt`.
- **Pulled staged checkout from origin** rather than committing-from-staged. The staged checkout is its own independent git checkout of `bokar83/calculatorz-app`, sharing the remote with the production repo. Pulling avoids dual-source-of-truth and keeps production repo as canonical source.
- **Pushed straight to main per Boubacar's explicit instruction** (this session was direct, not gate-mediated). Normal CLAUDE.md hard rule "no push without gate" was overridden in-conversation.
- **Did NOT touch unrelated agentsHQ dirty state** (14 files + 6 commits ahead on `feature/social-media-daily-analytics`) per Boubacar's explicit "leave alone".

## What is NOT done (explicit)

- **Hostinger production verification not run.** Build webhook fires on main push, but didn't check `https://calculatorz.tools/finance/take-home-pay-calculator-california/` returns 200 after the auto-deploy window. Should be checked next session.
- **Hostinger `.htaccess` rewrite not added.** Open question whether Hostinger static hosting honors Next.js server-side `rewrites()`. If not, the flat URLs (e.g. `/finance/take-home-pay-calculator-california/`) will 404 on prod even though the nested URLs work. The skill (`hostinger-deploy/SKILL.md`) was updated with this question — need to test.
- **Sitemap regeneration not verified.** `app/sitemap.ts` is dynamic and should pick up the 51 state pages, but didn't confirm the rendered sitemap.xml lists them with the correct URL pattern (flat or nested?).
- **Search Console submission not done.** Should ping Search Console with new sitemap to accelerate indexing of 51 state pages.
- **agentsHQ feature branch (`feature/social-media-daily-analytics`) untouched** — 14 dirty files + 6 commits ahead, all unrelated to calculatorz. Per Boubacar's "leave alone".

## Open questions

1. ~~**Does Hostinger static hosting honor Next.js `rewrites()`?**~~ **RESOLVED 2026-05-07.** Yes, Hostinger Git auto-deploy honors Next.js server-side `rewrites()`. Production verified: both flat and nested URLs return 200 (california, texas, florida, wyoming spot-checked).
2. ~~**Sitemap URL format:** does `app/sitemap.ts` emit flat or nested?~~ **RESOLVED 2026-05-07.** Sitemap emits flat URLs matching page canonicals. 51 state entries, all flat pattern. Clean for SEO indexing.
3. **Repo SSL config fix:** `d:/Ai_Sandbox/calculatorz-app/.git/config` has `http.sslCAInfo` pointing at non-existent path. Same issue likely in `output/apps/calculatorz-app/.git/config`. Currently bypassing per-command. Permanent fix is `git config --unset http.sslCAInfo` — needs Boubacar approval before running (CLAUDE.md "never update git config").

## Production verification (2026-05-07)

All 9 spot-checks returned 200:
- `/finance/take-home-pay-calculator-california/` (flat canonical)
- `/finance/take-home-pay-calculator/california/` (nested actual route)
- `/finance/take-home-pay-calculator-texas/`, `-florida/`, `-wyoming/` (3 more states)
- `/sitemap.xml` (51 state entries, flat URL pattern)
- `/finance/hours-worked-calculator/`, `/finance/hex-to-rgb/`, `/finance/cm-to-inches/` (3 utility calcs — note: live under `/finance/`, not `/utility/` as I'd guessed in earlier draft)

## Next session must start here

1. **Verify Hostinger deploy.** Hit these in browser:
   - `https://calculatorz.tools/finance/take-home-pay-calculator-california/` (flat — what canonicals point to)
   - `https://calculatorz.tools/finance/take-home-pay-calculator/california/` (nested — Next.js's actual route)
   - `https://calculatorz.tools/finance/take-home-pay-calculator-texas/`
   - `https://calculatorz.tools/utility/hours-worked/` (or wherever the 3 utilities landed)

   Both flat and nested should return 200. If only nested returns 200 (flat 404s), Hostinger isn't honoring `rewrites()` — proceed to step 2.

2. **If flat URLs 404:** add Apache rewrite to `public/.htaccess` in calculatorz-app:
   ```apache
   RewriteEngine On
   RewriteRule ^finance/take-home-pay-calculator-([a-z-]+)/?$ /finance/take-home-pay-calculator/$1/ [L]
   ```
   Commit + push to main with SSL bypass:
   ```bash
   cd d:/Ai_Sandbox/calculatorz-app
   git add public/.htaccess
   git commit -m "fix(routing): add Apache rewrite for flat state URLs"
   git -c http.sslBackend=schannel -c http.sslCAInfo= push origin main
   ```

3. **Verify sitemap.xml lists all 51 state pages** with the canonical URL pattern. Hit `https://calculatorz.tools/sitemap.xml`.

4. **Submit sitemap to Google Search Console** (calculatorz.tools property) for accelerated indexing.

5. **Check Hostinger deploy logs** if anything looks off — webhook should have fired ~2-5 min after push at 2026-05-07.

## Files changed this session

**`bokar83/calculatorz-app` repo:**
- `app/finance/take-home-pay-calculator/[state]/page.tsx` (renamed from `take-home-pay-calculator-[state]/page.tsx`)
- `next.config.ts` (+8 lines, added `rewrites()` block)

**`agentsHQ/output/apps/calculatorz-app/` (staged checkout, pulled to match origin):**
- Same files as above, pulled via `git pull origin main`

**`agentsHQ` repo (memory + skills + handoff):**
- `C:/Users/HUAWEI/.claude/projects/d--Ai-Sandbox-agentsHQ/memory/feedback_nextjs15_partial_dynamic_segments.md` (new)
- `C:/Users/HUAWEI/.claude/projects/d--Ai-Sandbox-agentsHQ/memory/feedback_git_ssl_bypass_one_shot.md` (new)
- `C:/Users/HUAWEI/.claude/projects/d--Ai-Sandbox-agentsHQ/memory/feedback_staged_checkout_is_independent_repo.md` (new)
- `C:/Users/HUAWEI/.claude/projects/d--Ai-Sandbox-agentsHQ/memory/feedback_cp_overlay_does_not_delete.md` (new)
- `C:/Users/HUAWEI/.claude/projects/d--Ai-Sandbox-agentsHQ/memory/project_calculatorz_state_paycheck_deploy.md` (new)
- `C:/Users/HUAWEI/.claude/projects/d--Ai-Sandbox-agentsHQ/memory/MEMORY.md` (4 new pointers in Workflow/SOP section)
- `C:/Users/HUAWEI/.claude/projects/d--Ai-Sandbox-agentsHQ/memory/MEMORY_ARCHIVE.md` (1 new project pointer)
- `C:/Users/HUAWEI/.claude/skills/hostinger-deploy/SKILL.md` (3 new HARD RULES: Next.js 15 partial segments, Hostinger+rewrites compatibility, SSL bypass)
- `docs/handoff/2026-05-07-calculatorz-state-paycheck-deploy.md` (this file)
