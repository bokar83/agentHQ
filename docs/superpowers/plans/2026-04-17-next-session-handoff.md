# Session Handoff — 2026-04-17

## What We Built This Session

Two standalone static unit converter websites, fully built and pushed to GitHub. One task left before they go live: buy the domains.

---

## Unit Converter Sites — Status: DONE except domains

### English site
- Local: `d:/Ai_Sandbox/agentsHQ/output/websites/unit-converter-site/`
- GitHub: `bokar83/unit-converter-site` (branch: master)
- Preview: `http://localhost:3001` (run `npx serve out -p 3001` from the folder)

### French site
- Local: `d:/Ai_Sandbox/agentsHQ/output/websites/convertisseur-en-ligne-site/`
- GitHub: `bokar83/convertisseur-en-ligne-site` (branch: master)
- Locale: `.env.local` has `NEXT_PUBLIC_LOCALE=fr`

### What's built
- Next.js 14, static export (`output: 'export'`), Tailwind CSS, TypeScript
- 10 converter categories, 13 pages each (10 converters + homepage + about + privacy)
- 1:1 From/To converter widget, real-time, swap button, read-only result field
- 7 AdSense zones per converter page (placeholder pub ID `ca-pub-XXXXXXXXXX`)
- Mobile-first: 375px priority, then 1280px desktop, 768px tablet
- NEXT_PUBLIC_LOCALE env var switches all UI strings at build time (en.json / fr.json)
- 32 converter math unit tests — all passing (`npm test`)
- `sitemap.xml`, `robots.txt`, `ads.txt` in `out/` for both sites

### Only step left: buy domains + connect Hostinger

**Domain candidates (check on Namecheap):**
- EN: `unitconvert.com` or `unitconvert.co` (both unverified — check availability)
- FR: `convertisseur-en-ligne.com` (strong SEO match for francophone market)
- `.com` is fine for the FR site — no need for `.fr` TLD

**Hostinger connection (do once per domain after purchase):**
1. Hostinger Control Panel → Hosting → select domain → Git → Connect repository
2. EN: `https://github.com/bokar83/unit-converter-site` | branch: `master` | publish dir: `out`
3. FR: `https://github.com/bokar83/convertisseur-en-ligne-site` | branch: `master` | publish dir: `out`

**After connecting:** every `git push origin master` auto-deploys.

**Before AdSense review:** swap `ca-pub-XXXXXXXXXX` in both sites' `src/app/layout.tsx` with real publisher ID, rebuild, push.

---

## Active Sprint (next session priority order)

1. Buy domains for unit converter sites (Namecheap — see candidates above)
2. Connect Hostinger Git deploy for both sites
3. Submit calculatorz.tools/sitemap.xml to Search Console (55 URLs, not yet resubmitted)
4. Test stale task types in orchestrator: research, consulting, app_build, agent_creation
5. Forge 2.0 pending fixes — add move_block to NotionClient, move 8 loose blocks into Archives toggle

---

## Key Files Reference

| What | Path |
|------|------|
| EN site source | `d:/Ai_Sandbox/agentsHQ/output/websites/unit-converter-site/src/` |
| FR site source | `d:/Ai_Sandbox/agentsHQ/output/websites/convertisseur-en-ligne-site/src/` |
| EN locale strings | `src/locales/en.json` |
| FR locale strings | `src/locales/fr.json` |
| Converter math | `src/lib/converters/*.ts` (10 files) |
| Registry (slug → config) | `src/lib/registry.ts` |
| AdSense zones | `src/components/AdZone.tsx` |
| Converter widget | `src/components/ConverterWidget.tsx` |
| Unit tests | `__tests__/converters.test.ts` |
| Design spec | `docs/superpowers/specs/2026-04-16-unit-converter-sites-design.md` |
| Implementation plan | `docs/superpowers/plans/2026-04-16-unit-converter-sites.md` |
