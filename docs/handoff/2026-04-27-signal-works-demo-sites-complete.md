# Session Handoff - Signal Works Demo Sites - 2026-04-27

## TL;DR
Built, iterated, and shipped two Signal Works demo sites to Vercel: Bright Smiles Pediatric Dentistry (dental) and Summit Roofing Utah (roofing). Required ~10 build iterations due to template-level first passes, wrong photos (Monster Energy, chef, caulk gun), and a broken horizontal scroll. Both sites are now locked, live, and the frontend-design skill has been updated to prevent all of these failures on the first pass next time.

## What was built / changed

### Demo sites (both live on Vercel)
- `output/websites/signal-works-demo-dental/index.html` :  Storybook immersive archetype. Fraunces + Nunito. Navy #0B1F3A + sky blue + coral + gold. Floating pill nav, morphing blob hero, 4-col services grid with hover glow + stagger, Kie-generated B&W child before/after portraits, full schema.
- `output/websites/signal-works-demo-dental/img/dental-before.png` :  Kie gpt4o-image, B&W child shy smile
- `output/websites/signal-works-demo-dental/img/dental-after.png` :  Kie gpt4o-image, B&W child big bright smile
- `output/websites/signal-works-demo-roofing/index.html` :  Bold editorial archetype. Unbounded + DM Sans. Dark #0D0D0D + orange #F4600C. Top-left logo, full-viewport typography hero (ROOFING 11rem + UTAH outline), Volta noise texture, editorial numbered service rows, 3-panel photo strip, Kie before/after aerials.
- `output/websites/signal-works-demo-roofing/img/roof-before.png` :  Kie gpt4o-image, worn aerial roof
- `output/websites/signal-works-demo-roofing/img/roof-after.png` :  Kie gpt4o-image, new charcoal roof aerial
- `output/websites/signal-works-demo-roofing/img/roof-house.png` :  Kie gpt4o-image, suburban home with new roof
- `workspace/demo-sites/build-log.md` :  3 new rows added (dental, roofing, HVAC from other session)

### Skill updates
- `skills/frontend-design/SKILL.md` and `~/.claude/skills/frontend-design/SKILL.md` :  Major additions:
  - Check F (photo plan mandatory before first img tag)
  - 2 new failure modes: The Emoji Icon, The Hotlink Gamble
  - Real photos item added to cinematic baseline checklist
  - Full IMAGE RULES section (6 rules, Kie direct API pattern, content verification rule)
  - MANDATORY live competitive research section (website-intelligence first, Firecrawl search, competitive brief, category-by-category table)
  - 2 new font pairings: Fraunces + Nunito, Unbounded + DM Sans
  - 2 new color stories: Cinematic dark + orange, Navy + sky blue + coral + gold

## Decisions made
- **Roofing site locked as template archetype**: The typography-only hero (word fills viewport, outline text) is a strong pattern worth reusing for other trade contractors. Do not change it.
- **Kie direct API is the working local method**: `orchestrator/kie_media.py` import fails locally (missing firecrawl_tools). Use direct HTTP to `https://api.kie.ai/api/v1/gpt4o-image/generate` with `dotenv load_dotenv()` for the key.
- **GSAP pinned horizontal scroll banned for services**: Breaks silently when CSS widths change. Static 4-col grid with GSAP stagger is the correct pattern.
- **Unsplash content verification**: HTTP 200 is not sufficient. Must describe image content before embedding.
- **frontend-design skill**: additions only, no deletions. Original text preserved exactly.

## What is NOT done
- Neither site has a real contact form wired (Formspree not added)
- No GA4 wired on either site
- No OG images generated (the Vercel meta tags use placeholder)
- No sitemap.xml or robots.txt in either site folder
- Dental site hero animations (SplitText) were not verified on mobile
- HVAC demo site (signal-works-demo-hvac) was added to build log but not built in this session :  another session handled it

## Open questions
- Should Signal Works demo sites eventually move to a custom domain (e.g. demos.signalworks.ai)?
- The roofing site `reviews-feature-q` has an `&mdash;` that should be an em-dash rule violation :  already fixed in session but worth double-checking

## Next session must start here
1. Run `/nsync` to confirm all three machines (laptop, VPS, GitHub) are at the same commit
2. If building a third Signal Works demo (e.g. HVAC, plumber, landscaper), read the updated `frontend-design` skill in full :  specifically the live competitive research section and photo plan check F before writing any HTML
3. If presenting demos to a Signal Works prospect, the two live URLs are:
   - Dental: https://signal-works-demo-dental.vercel.app
   - Roofing: https://signal-works-demo-roofing.vercel.app

## Files changed this session
```
output/websites/signal-works-demo-dental/
  index.html
  img/dental-before.png (new)
  img/dental-after.png (new)

output/websites/signal-works-demo-roofing/
  index.html
  img/roof-before.png (new)
  img/roof-after.png (new)
  img/roof-house.png (new)

workspace/demo-sites/build-log.md

skills/frontend-design/SKILL.md
~/.claude/skills/frontend-design/SKILL.md

~/.claude/projects/d:Ai-Sandbox-agentsHQ/memory/
  project_signal_works_demos.md (new)
  feedback_horizontal_scroll_services.md (new)
  feedback_unsplash_content_verification.md (new)
  MEMORY.md (updated)

docs/handoff/2026-04-27-signal-works-demo-sites-complete.md (this file)
```
