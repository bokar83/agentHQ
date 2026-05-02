# Session Handoff - Elevate Roofing Signal Works Pilot - 2026-04-30

## TL;DR

Full website-intelligence run on elevatebuiltoregon.com (Rod, Medford OR roofer, Boubacar's first Signal Works pitch and a warm reconnect). Built and shipped a complete demo (17 pages, Industrial Editorial scroll-driven, Rod's actual drone video + photos + voice preserved), an audit one-pager (reusable Signal Works template), and a 3-version outreach message script. Outreach is ON HOLD until Tue May 6 9am MT. Reminders armed across 4 channels (Telegram cron + standalone Python + Google Calendar + Gmail draft).

Three new memory rules locked in that change how website-intelligence runs from here forward.

## What was built / changed

**Project deliverables (all under `d:/Ai_Sandbox/agentsHQ/projects/elevate-built-oregon/`):**
- `research/01-client-brand.md` - brand snapshot, palette decoded from Elementor CSS, voice tells, site state
- `research/02-competitor-analysis.md` - 10 Southern Oregon roofers scored, top 5 deep-profiled (JAM, Pressure Point, Rogue Valley, Renaissance, Eric Preston), patterns, SEO landscape, 3 whitespace plays
- `research/03-build-brief.md` - design + content + tech brief
- `research/04-quality-audit.md` - KEPT/ENHANCED/NEW matrix + audit results
- `competitive-analysis.html` - long-form printable PDF report (warm paper + Instrument Serif), internal-only for Rod
- `audit-one-pager.html` - single-page Catalyst Works/Signal Works branded brief, sharable to ANY prospect, prints to A4 PDF. **THIS IS THE REUSABLE SW TEMPLATE.**
- `_archive/v1-boring-template/` - rejected v1 site, archived as warning artifact
- `site/index.html` + 16 sub-pages - Industrial Editorial v2 build (Fraunces + Geist + Geist Mono, off-black + bone + signal-orange #FF5E1A, kept Rod's navy in tokens). Cinematic scroll-driven. Rod's 44 MB drone video as full-bleed hero. Real wordmark logo PNG inserted via `<img class="brand-logo">` with `filter: brightness(0) invert(1)` for dark surfaces.
- `site/css/elevate.css` - 39 KB design system
- `site/js/elevate.js` - ~7 KB GSAP scroll choreography (header scroll-state, mobile nav, hero parallax, fade-up reveals, marquee speed-on-hover, count-up, mouse-tracking founder glow, cost-band tool, sticky mobile CTA visibility)
- `site/assets/media/` - Rod's actual hero-fox-dental.mp4 (44MB drone), 4 project photos, 2 logos (wordmark + mark)
- `site/assets/favicon.svg`, `og-image.svg`
- `site/sitemap.xml`, `robots.txt`, `vercel.json` (with 4 legacy WP slug redirects)
- `_build/generate_pages.py` - page generator with shared header/footer
- `_build/send_tuesday_reminder.py` - standalone Telegram reminder fallback (zero deps)
- `MESSAGE_TO_ROD.md` - 3 outreach versions (text, email, DM) + 15-min call agenda + price-question script
- `TO_SHARE_WITH_ROD/` - clean package folder (README, audit brief, internal message)
- `REMINDER_TUESDAY_MAY_6.md` - project-folder safety net
- `README.md`

**Memory files created (three new feedback files, one new project file, one new reference file):**
- `feedback_website_intelligence_as_sw_sales_weapon.md` - tier the SW asset (PDF / PDF+hero / full build) by lead temperature; first 5 SW clients get full free build, after that only above $5K threshold
- `feedback_website_intelligence_must_use_frontend_design.md` - Phase 5 of the website-intelligence skill must hand off to frontend-design, NEVER use the warm-paper static template; bar is Apple/Stripe/Linear cinematic
- `feedback_redesign_familiar_not_foreign.md` - 20-50% different not 100%, scrape & reuse existing media first, USE THE REAL LOGO (don't improvise text-based logotype), brief must mark KEPT vs ENHANCED vs NEW, default to keep when uncertain
- `project_elevate_roofing_signal_works_pilot.md` - full project state pointer
- `reference_signal_works_audit_one_pager_template.md` - how to reuse the one-pager for next SW prospect

**Memory index updates:**
- MEMORY.md line 74 - extended the website-intelligence rules pointer to include the audit-one-pager reference
- MEMORY_ARCHIVE.md - added Elevate Roofing project pointer under "Active projects"

**Reminder system armed (Tuesday May 6 9am MT):**
- Telegram cron job ID `1b5683dd` (in-session, dies if Claude session ends)
- Standalone Python script at `_build/send_tuesday_reminder.py` (works anytime, zero deps)
- Google Calendar event (https://www.google.com/calendar/event?eid=cnQ5dDVvdmNnbjZlZzZmcTcwMWNhMTNscTAgYm9rYXI4M0Bt) with email reminder 60 min before + popup 15 min before
- Gmail draft `r-6447362763212794298` in bokar83@gmail.com Drafts (subject "[Reminder] Tuesday May 6 - Send Rod the Elevate Roofing demo")

## Decisions made

**Strategic:**
- Elevate Roofing is the first Signal Works pilot. Win or lose, deliverable becomes the case study + template.
- Doing this build for free on grounds that first 5 SW reference clients warrant it (per the new SW sales weapon rule).
- Outreach to Rod is warm reconnect - known him for years. Not cold. Tone: "saw your site, played with it, want to see?"
- NO price mention in first touch. NEVER lead with "free" if asked - three-option script in MESSAGE_TO_ROD.md ($1,500 + referral, or trade for roof inspection).

**Aesthetic:**
- Industrial Editorial direction (Fraunces variable serif at opsz 144 + Geist humanist sans + Geist Mono numerics). Off-black ink + bone paper + signal-orange #FF5E1A accent. Rod's navy #1C4DA0 retained in tokens for familiarity.
- Hero video transforms scale + Y on scroll (cinematic Stripe move, never seen on contractor sites)
- Editorial 12-col grid with intentional asymmetry, hairline section rules, margin-set vertical section numerals
- Section rhythm balanced after first attempt was too dark: dark hero → orange marquee → light Stack → dark Services → light Portfolio → dark Founder → light Areas → light Reviews → light Cost → dark CTA → dark footer

**Skill / process:**
- Phase 5 of website-intelligence MUST hand off to frontend-design (or 3d-website-building). The skill's default static template was rejected and is now archived as warning.
- Real client logo MUST be used - text-based logotype is a violation of the redesign rule.
- Every SW redesign deliverable must contain at minimum: real logo, real video/photo, real project photos, voice fingerprint preserved verbatim in 3+ visible places.
- Audit one-pager (warm-paper editorial) is the standard SW client deliverable design language.

**Technical:**
- All H2s use direct `.section-h2` class; NEVER use split-line `<span><span>` wrappers (they caused invisible-headline bug when GSAP misfired)
- Cache-bust pattern: `?v=<unix_timestamp>` on every CSS/JS link, bumped via Python regex sweep across all 18 pages
- Em-dash scrubbing site-wide is mandatory before declaring done (caught 12-166 instances per scrub on this build)

## What is NOT done (explicit)

- **Not deployed** - Vercel deploy intentionally deferred. `cd site && vercel --prod` is the first action of the next session.
- **Hero video not compressed** - still 44 MB. Needs `ffmpeg -c:v libx264 -crf 28 -preset slow -an -movflags +faststart` to ~6-8 MB before launch. Not a blocker for showing Rod.
- **Form endpoint placeholder** - `REPLACE_ME` Formspree action still in /get-a-quote/ + final-CTA callback form. Will configure post-Rod-yes.
- **Calendar embed** - no Cal.com / Calendly wired. Form is the v1 fallback.
- **Founder portrait** - placeholder "ROD" letterform on home + about. Real photo needed from Rod post-yes.
- **Manufacturer cert badges** - none. Wait until GAF Master Elite or Owens Corning lands.
- **Sankofa kill list partially deferred** - three open council disagreements left for Boubacar to decide:
  1. Whether the "Stack / one builder beats four" pitch should remain the homepage anchor (Contrarian + First Principles say no, Expansionist says reorder)
  2. Whether to rename "Other Cool Stuff" (Outsider says confusing, Contrarian says it's the personality)
  3. CCB# spell-out - should go from "CCB# 257092" to "Oregon licensed (CCB# 257092)" first time, then bare CCB# afterward (deferred for global pass)
- **Outreach is ON HOLD** - message not sent. Tuesday May 6 9am MT is send-day.

## Open questions

- Will Rod actually deploy his real founder photo + real Formspree key + real calendar after the demo? (Affects how much swap-in work falls back on Boubacar in week 2.)
- Should the audit one-pager template be moved out of the elevate-built-oregon project folder into a more findable location (e.g. `templates/signal-works/`) for easier reuse on next prospect? Currently in `projects/elevate-built-oregon/audit-one-pager.html` which makes it discoverable only if you know the project name.
- Vercel preview vs production for first share with Rod? Recommendation: production (preview URLs change and break shared links). But this is Boubacar's call.

## Next session must start here

**If next session is BEFORE Tuesday May 6:** Project is on hold. Don't touch the Elevate site. Work on something else.

**If next session is ON Tuesday May 6 (the reminder fired):**

1. **Deploy demo to Vercel:**
   ``bash
   cd d:/Ai_Sandbox/agentsHQ/projects/elevate-built-oregon/site
   vercel --prod
   ``
   Copy the production URL.
2. **Open `MESSAGE_TO_ROD.md`** - pick Version B (email) unless Boubacar wants to text, then Version A.
3. **Replace `[LINK]`** with the Vercel URL in whichever version he picked.
4. **(Email path only)** Print `audit-one-pager.html` to PDF in Chrome (`Ctrl+P` → Save as PDF, check Background graphics) → attach as `Elevate-Website-Audit-Brief.pdf`.
5. **Send.**
6. **Don't follow up for 7 days minimum.** One light bump max if no reply by Tue May 13. Then drop it.

**If next session is AFTER Tuesday May 6 and Rod has replied yes:** Open project file `project_elevate_roofing_signal_works_pilot.md`, look at the "Pre-launch TODOs" section, work through swap-ins.

**If next session is on a different prospect entirely:** Start with `reference_signal_works_audit_one_pager_template.md` for the audit one-pager structure, and `feedback_redesign_familiar_not_foreign.md` for the build rules. The Elevate project folder is a complete reference build - copy patterns from it.

## Files changed this session

``
d:/Ai_Sandbox/agentsHQ/projects/elevate-built-oregon/
├── README.md                                    [created]
├── MESSAGE_TO_ROD.md                            [created]
├── REMINDER_TUESDAY_MAY_6.md                    [created]
├── audit-one-pager.html                         [created - REUSABLE TEMPLATE]
├── competitive-analysis.html                    [created]
├── _archive/v1-boring-template/                 [archived rejected v1]
├── _build/
│   ├── generate_pages.py                        [created]
│   └── send_tuesday_reminder.py                 [created]
├── research/
│   ├── 01-client-brand.md                       [created]
│   ├── 02-competitor-analysis.md                [created]
│   ├── 03-build-brief.md                        [created]
│   └── 04-quality-audit.md                      [created]
├── site/
│   ├── index.html                               [created - homepage]
│   ├── 404/index.html                           [created]
│   ├── about/index.html                         [created]
│   ├── contact/index.html                       [created]
│   ├── get-a-quote/index.html                   [created]
│   ├── portfolio/index.html                     [created]
│   ├── service-areas/index.html                 [created hub]
│   ├── service-areas/{6 city pages}/index.html  [created]
│   ├── services/index.html                      [created hub]
│   ├── services/{4 service pages}/index.html    [created]
│   ├── css/elevate.css                          [created - 39KB design system]
│   ├── js/elevate.js                            [created - ~7KB scroll choreography]
│   ├── assets/favicon.svg                       [created]
│   ├── assets/og-image.svg                      [created]
│   ├── assets/media/                            [scraped from Rod's site]
│   │   ├── hero-fox-dental.mp4                  (44MB drone)
│   │   ├── project-{2016,2017,2025,2026}*.jpg   (4 real photos)
│   │   ├── logo-mark.png                        (E mark)
│   │   └── logo-wordmark.png                    (full wordmark)
│   ├── sitemap.xml                              [created]
│   ├── robots.txt                               [created]
│   └── vercel.json                              [created with 4 legacy redirects]
└── TO_SHARE_WITH_ROD/                           [deliverable package]
    ├── README.md
    ├── 00-OUTREACH-MESSAGE-internal.md
    └── 01-Quick-Audit-Brief.html

`C:/Users/HUAWEI/.claude/projects/d--Ai-Sandbox-agentsHQ/memory/`
├── MEMORY.md                                    [edited - extended website-intelligence pointer + tab-shutdown rule]
├── MEMORY_ARCHIVE.md                            [edited - added project pointer]
├── feedback_website_intelligence_as_sw_sales_weapon.md          [created]
├── feedback_website_intelligence_must_use_frontend_design.md    [created]
├── feedback_redesign_familiar_not_foreign.md                    [created]
├── feedback_tab_shutdown_always_writes_to_skills.md             [created in addendum]
├── feedback_sw_report_runs_both_skills.md                       [created in addendum]
├── project_elevate_roofing_signal_works_pilot.md                [created]
└── reference_signal_works_audit_one_pager_template.md           [created]
``

---

## ADDENDUM (2026-04-30 23:35 MT) :  skill-file edits + SW report enhancement

After the initial handoff was written, Boubacar clarified two rules that triggered additional work in the same session:

### Rule 1: tab-shutdown ALWAYS writes lessons to skill files

Boubacar's words: *"I don't want you to stop editing the skills files. I told you to stop before because we were doing multiple things at the same time. When it comes to the tab shutdown, you ALWAYS write what needs to be written to the skills files to update them. Don't leave that in memory."*

The earlier "Step 3: Skills update (deferred per earlier user signal :  rules live in memory)" was wrong. Mid-session "stop editing the skill" signals do NOT carry over to tab-shutdown. Tab-shutdown is the explicit moment to lock in skill-relevant lessons.

**Skill files updated as a result:**

- `~/.claude/skills/website-intelligence/SKILL.md` :  added top-level HARD RULES block (6 rules), Phase 1 expanded with mandatory media inventory + logo-capture pattern + Elementor data-settings JSON extraction technique, NEW Phase 1.5 (run web-design-guidelines), Phase 4 expanded with mandatory KEPT/ENHANCED/NEW matrix template, Phase 5 fully rewritten with the hand-off rule (do NOT use the static template, hand to frontend-design or 3d-website-building) + Known pitfalls + cache-bust pattern.
- `~/.claude/skills/frontend-design/SKILL.md` :  added Known Pitfalls section (7 lessons): GSAP split-line invisible-headline bug + the `.js-ready` gating fix, cache-bust during iteration, no-meta-commentary copy rule, em-dash scrub, mobile hero crowding fix, real-logo rule, mix-blend-mode scoping.
- `~/.claude/skills/tab-shutdown/SKILL.md` :  Step 3 rewritten with explicit HARD RULE: "every lesson learned that belongs in a skill MUST be written to the skill file. Do not silently skip Step 3 because an earlier mid-session edit was rejected."

### Rule 2: SW reports run BOTH website-intelligence AND web-design-guidelines

Boubacar's words: *"Add somewhere, maybe as an enhancement or to the ideas queue at minimum (prefer as an enhancement) that we want both the 'website-intelligence' skill and the 'web-design-guidelines' to run on the initial design and be a part of the report that we give to customers (or at least that I get...tbd) for SW. The two skills are needed, the one to see what is out there in the market and the other to show how the design can be improved and do better with SEO and GEO."*

**Implementation:** Added Phase 1.5 to website-intelligence SKILL.md (run web-design-guidelines on the client's existing site, save scorecard to `research/01b-design-audit.md`, weave findings into Phase 3 audit one-pager and Phase 4 build brief).

**Saved to memory:** `feedback_sw_report_runs_both_skills.md` (not yet pointed to from MEMORY.md :  file at line cap, see below).

### MEMORY.md is at the 200-line cap

Adding the tab-shutdown rule pushed MEMORY.md to exactly 200 lines (the truncation cap). The new `feedback_sw_report_runs_both_skills.md` rule was created as a standalone file but its pointer could not be added to MEMORY.md without first trimming. **Next session should:**

1. Move one project_* or low-traffic feedback pointer from MEMORY.md to MEMORY_ARCHIVE.md
2. Add the `feedback_sw_report_runs_both_skills.md` pointer to MEMORY.md
3. Re-verify `wc -l MEMORY.md` returns ≤199

### What this means for the next session prompt

The next-session prompt at the bottom of this handoff is still correct :  Tuesday May 6 send-day procedure unchanged. But add ONE first-action: trim MEMORY.md from 200 → ≤199 and index the new feedback file.

---

## ADDENDUM 2 (2026-04-30 23:50 MT) :  final sweep + 2 more codified rules

Final pre-shutdown sweep caught 4 things stated in conversation that hadn't been codified outside the Rod-specific MESSAGE_TO_ROD.md. Three were one cluster (general SW outreach posture); one was its own pattern (layered reminders).

### Two new feedback files created

- **`feedback_sw_outreach_posture.md`** :  three rules for EVERY SW first-touch message regardless of prospect:
  1. Show, don't tell. Demo IS the pitch.
  2. Never say "free" out loud. Use the three-option counter ($1,500 / referral / trade) even when willing to do free work.
  3. Wait 7 days before any follow-up. One light bump max.

- **`reference_layered_reminders_pattern.md`** :  the 4-channel reminder pattern (in-session cron + standalone Python + Google Calendar + Gmail draft) for any future-dated task that genuinely matters. Documents the exact Rod-reminder setup as the reference implementation.

### MEMORY.md indexed (still at 200-line cap)

Both new files indexed by extending the existing website-intelligence rules pointer line on MEMORY.md line 74. The line is now long but readable. MEMORY.md still hits exactly 200 lines :  the cap warning from Addendum 1 still applies for the next session.

### Final sweep summary :  8 memory artifacts from this session

| File | Type | What it captures |
|---|---|---|
| `feedback_website_intelligence_as_sw_sales_weapon.md` | feedback | Tier the asset by lead temperature |
| `feedback_website_intelligence_must_use_frontend_design.md` | feedback | Phase 5 hand-off rule |
| `feedback_redesign_familiar_not_foreign.md` | feedback | 20-50% rule + real logo + media inventory |
| `feedback_sw_report_runs_both_skills.md` | feedback | Run BOTH website-intelligence + web-design-guidelines |
| `feedback_sw_outreach_posture.md` | feedback | Show don't tell · never say free · 7-day wait |
| `feedback_tab_shutdown_always_writes_to_skills.md` | feedback | Tab-shutdown writes to skills, not just memory |
| `project_elevate_roofing_signal_works_pilot.md` | project | Full project state pointer (in MEMORY_ARCHIVE) |
| `reference_signal_works_audit_one_pager_template.md` | reference | One-pager structure + how to reuse for next prospect |
| `reference_layered_reminders_pattern.md` | reference | 4-channel reminder pattern |

### Skill files updated this session

| File | What changed |
|---|---|
| `~/.claude/skills/website-intelligence/SKILL.md` | Top-level HARD RULES + Phase 1 media inventory + Phase 1.5 web-design-guidelines + Phase 4 KEPT/ENHANCED/NEW matrix + Phase 5 hand-off + Known Pitfalls |
| `~/.claude/skills/frontend-design/SKILL.md` | Known Pitfalls section (7 lessons including GSAP split-line bug + cache-bust + meta-commentary ban + em-dash scrub + mobile hero + real logo + mix-blend scope) |
| `~/.claude/skills/tab-shutdown/SKILL.md` | Step 3 rewritten with explicit HARD RULE: always write to skill files, never silently skip |

The session is fully closed. No known uncodified rules remain.

