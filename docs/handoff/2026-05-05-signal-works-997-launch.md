# Session Handoff - Signal Works 997 Launch - 2026-05-05

## TL;DR
Built and launched the Signal Works $997 close page at geolisted.co/997. Full session: SW+CW sprint planning (Sankofa reviewed), spec sheet built and Sankofa reviewed, cinematic 997.html page built with AI search preloader + scramble headline + live missed-call counter + signal wave canvas, deployed to Hostinger via geolisted-site repo with .htaccess clean URL rewrite.

## What was built / changed

- `d:/Ai_Sandbox/agentsHQ/output/websites/geolisted-site/997.html` — full close page, live at geolisted.co/997
- `d:/Ai_Sandbox/agentsHQ/output/websites/geolisted-site/.htaccess` — clean URL rewrite (/997 → /997.html)
- `d:/Ai_Sandbox/agentsHQ/output/websites/geolisted-site/` — committed, pushed, auto-deployed to Hostinger
- `d:/Ai_Sandbox/agentsHQ/output/websites/signal-works-site.ARCHIVED/` — local folder archived
- `bokar83/signal-works-site` GitHub repo — archived (read-only)
- `d:/Ai_Sandbox/agentsHQ/deliverables/signal-works/spec-997.html` — draft spec sheet (superseded by 997.html)
- Memory: 6 new files written this session

## Decisions made

- **geolisted.co = SW production domain.** 997.html lives in `geolisted-site` repo, not a new repo.
- **Canvas animation > video background.** Pitch reels have burned-in text that bleeds through any overlay. Canvas stays.
- **Reels (roofing, HVAC, dental) = proof/outreach assets only.** Not hero backgrounds.
- **Cold SMS axed.** Warm only — prospects already have TN from the call.
- **SW outreach = phone-first.** Email is background noise for trades. Dial is the lever.
- **signal-works-site repo archived.** Was created in error; geolisted-site is canonical.
- **Sprint is Tue-Sat only.** Sunday = Sabbath (no work, no contact). Saturday = light trades only.

## What is NOT done (explicit)

- **Phone number in SMS CTA is wired** (801-888-1963) but nav "Book a Call" still goes to Calendly only — no SMS fallback in nav.
- **Hero video:** commented-out video block removed. If real footage-only reel is created, wire it with opacity .12-.18 + rgba overlay .82+.
- **Custom pitch reel for 997 page:** reels exist for roofing/HVAC/dental but none purpose-built for the /997 page itself.
- **Sprint execution:** page is live, plan emailed, but no dials placed yet. Sprint starts Tue 2026-05-06.
- **Apollo:** deferred until Wed pickup gate confirms phone outreach viability.
- **CW warm reactivation:** 5 dormant Utah/MW contacts identified but messages not sent yet.

## Open questions

- Which Hostinger subdomain/path will index.html and 997.html share for nav linking? Currently nav links back to `index.html` (relative). Fine for same domain.
- Should `/997` link appear in geolisted.co nav? Currently not wired.
- Spec page says "May build slots: 3 of 5 remaining" — needs manual update as slots fill.

## Next session must start here

1. **Sprint day 1 (if Tue):** Pull 30 GMB-only leads (landscapers, Phoenix metro). Open Google Maps, filter: GMB exists, website field empty, 10+ reviews. Log to Leads DB sheet.
2. **Add /997 link to geolisted.co nav** — single line edit in `geolisted-site/index.html`, push, done.
3. **CW warm messages:** pick 5 dormant Utah/MW contacts from LinkedIn, one specific signal each, send reactivation message using template from sprint plan email.
4. **Wed gate:** after 10 dials, log pickup rate. <15% = pivot to SMS + supply house.

## Files changed this session

```
output/websites/geolisted-site/
  997.html          ← new, live
  .htaccess         ← new, live
output/websites/signal-works-site.ARCHIVED/
  (archived, not touched)
deliverables/signal-works/
  spec-997.html     ← superseded draft
memory/
  feedback_sabbath_no_work_sunday.md    ← new
  feedback_boubacar_phone.md            ← new
  feedback_local_sandbox_before_push.md ← new
  feedback_hostinger_clean_urls.md      ← new
  feedback_video_bg_bleed.md            ← new
  project_sw_hero_video.md             ← new
  reference_signal_works_site.md       ← updated (geolisted.co facts)
  reference_boubacar_phone.md          ← new
  MEMORY.md                            ← updated (8 new pointers)
skills/hostinger-deploy/SKILL.md       ← updated (HARD RULES block added)
```
