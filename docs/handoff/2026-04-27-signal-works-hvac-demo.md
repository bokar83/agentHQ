# Session Handoff - Signal Works HVAC Demo - 2026-04-27

## TL;DR
Built and deployed the third Signal Works prospect demo site :  Summit Comfort Systems (HVAC, Salt Lake City). Full competitive research, Kie-generated images, 1,956-line immersive full-bleed site with kinetic services list, parallax comfort section, stat counters, reviews marquee, and FAQ accordion. Spent significant time diagnosing a critical GSAP bug (SplitText CDN 404 killed all JS silently). Fixed and documented. Site is live and working.

## What was built / changed

- `output/websites/signal-works-demo-hvac/index.html` :  1,956-line HVAC demo site
- `output/websites/signal-works-demo-hvac/img/hero_bg.png` :  Kie-generated nighttime SLC aerial (2.4MB)
- `output/websites/signal-works-demo-hvac/img/comfort_section.png` :  Kie-generated cozy fireplace interior (2.2MB)
- `output/websites/signal-works-demo-hvac/img/technician.png` :  Kie-generated HVAC tech in uniform (2.0MB)
- `output/websites/signal-works-demo-hvac/.vercel/project.json` :  Vercel project config (old project, superseded)
- `workspace/demo-sites/build-log.md` :  Updated with HVAC entry
- `skills/frontend-design/SKILL.md` :  Critical GSAP Club plugin warning added, splitChars() DOM helper added
- `~/.claude/skills/frontend-design/SKILL.md` :  Synced
- `~/.claude/projects/d:Ai-Sandbox-agentsHQ/memory/feedback_gsap_splittext_cdn.md` :  New memory file
- `~/.claude/projects/d:Ai-Sandbox-agentsHQ/memory/MEMORY.md` :  Updated with GSAP entry + HVAC demo URL
- `~/.claude/projects/d:Ai-Sandbox-agentsHQ/memory/project_signal_works.md` :  Updated with HVAC demo URL and HVAC niche

## Decisions made

- **HVAC demo Vercel project name:** `summit-comfort-hvac` (NOT `signal-works-demo-hvac` :  old project had stale CDN state). Live at https://summit-comfort-hvac.vercel.app
- **Archetype:** Immersive full-bleed / emergency urgency :  midnight navy `#0F1E35` + ice blue `#A8D4F5` + urgent amber `#F5A623`
- **Fonts:** Cormorant Garamond + Space Grotesk (not repeated from dental/roofing)
- **SplitText permanently banned from public CDN** :  use `splitChars()` DOM helper going forward
- **Cursor pattern locked:** `element.style.left/top` on every mousemove/rAF tick; CSS `transform: translate(-50%,-50%)` for centering only; no GSAP touching the cursor transform

## What is NOT done

- Signal Works cold email campaign not started this session (separate task)
- Old Vercel project `signal-works-demo-hvac` still exists :  can be deleted manually in Vercel dashboard if desired
- Build log has bare URL lint warnings (MD034) :  cosmetic, not functional

## Open questions

- Is the 10-day contract clock (2026-05-02) still the target? Session ran long on the HVAC demo debug
- Should the HVAC demo URL `summit-comfort-hvac.vercel.app` be renamed to match the dental/roofing pattern? Requires a new project name or domain alias

## Next session must start here

1. Check Signal Works timeline :  is the 2026-05-02 contract target still live?
2. If cold email campaign not yet started: run `cold-outreach` skill targeting SLC HVAC companies using `signal_works/email_queue_pediatric_dentist_Salt_Lake_City.csv` as the model
3. Build HVAC lead list: scrape Google Maps for SLC HVAC companies, tag `signal_works` in Supabase, qualify with 20-100 reviews + outdated website filter
4. Demo suite is now complete (dental + roofing + HVAC) :  ready to use in outreach

## Files changed this session

```
output/websites/signal-works-demo-hvac/
  index.html
  img/hero_bg.png
  img/comfort_section.png
  img/technician.png
  .vercel/project.json

workspace/demo-sites/build-log.md

skills/frontend-design/SKILL.md
~/.claude/skills/frontend-design/SKILL.md

~/.claude/projects/d:Ai-Sandbox-agentsHQ/memory/
  feedback_gsap_splittext_cdn.md  (NEW)
  MEMORY.md  (updated)
  project_signal_works.md  (updated)

docs/handoff/2026-04-27-signal-works-hvac-demo.md  (this file)
```
