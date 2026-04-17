# SKILL: hyperframes

## What This Skill Does
Generates HeyGen Hyperframes HTML compositions that render to MP4 or WebM video
files via the Hyperframes CLI. This is a code-driven video production skill.
Output is always a video file. This skill does NOT produce live websites or
browser-rendered pages. Do not confuse it with the website_build skill.

## Relationship to website_build Skill
These are sibling skills, not the same skill. Both write HTML. The outputs are
completely different execution contexts:
- website_build: HTML runs live in a browser. Served over HTTP. Users interact with it.
- hyperframes: HTML is a video source file. Rendered headless by Chrome. Encoded
  to MP4 by FFmpeg. Never served to a user directly.
When a task brief calls for both a website and a companion video, invoke both
skills independently. Do not merge their outputs.

## When to Use This Skill
- leGriot requests a video output for a social post (9:16, 15-30 seconds)
- A consulting deliverable requires an animated findings brief (16:9, 30-60 seconds)
- Any task brief specifies "video", "MP4", "animated video", or "Hyperframes"
- A content brief includes duration, aspect ratio, and scene structure

## When NOT to Use This Skill
- The request is for a live website or landing page (use website_build skill)
- The request is for a site animation or scroll effect (use CSS/GSAP on the live site)
- The request is text-only social content (leGriot handles without video)
- Phase 0 is active (no video builds during Phase 0 -- knowledge only)
- No complete brief is supplied (stop and request missing fields before proceeding)

## Phase Gate
- Phase 0: Knowledge only. Do not install, scaffold, or render.
- Phase 1: Install on VPS. Build leGriot video layer. Test one real post.
- Phase 2: Add consulting findings brief format. Automate render pipeline.

## Required Inputs (Brief Template)
Every invocation requires all of these. Stop and ask if any are missing.
- purpose: what this video is for and where it will be published
- duration: e.g. 15s, 30s, 45s
- aspect_ratio: 16:9 | 9:16 | 1:1
- mood_style: e.g. minimal Swiss grid, warm analog, high-energy social
- brand_palette: hex values with usage caps
- typography: body font, heading font
- scenes: key scenes and elements (title card, lower third, captions, etc.)
- audio: none | music at assets/path.mp3 | TTS with voice preference
- caption_tone: Hype | Corporate | Tutorial | Storytelling | Social
- transitions: energy level or mood description
- asset_paths: exact file paths for all media -- never invent paths

## Output Format (Required Every Time)
1. Complete HTML composition in a fenced code block. Nothing elided.
2. Exact CLI render command in a second fenced code block.
3. Two sentences explaining motion and transition choices.
4. If brief is incomplete: stop and ask. Do not guess.

## Hard Rules (All 7 Must Be Honored -- No Exceptions)
1. Register every GSAP timeline on window.__timelines
2. All <video> elements must be muted -- audio via separate <audio> elements
3. No Math.random() -- use seeded PRNG (mulberry32) if needed
4. Timeline construction is synchronous -- no async/await or fetch() during setup
5. Every timed element needs class="clip" + data-start + data-duration + data-track-index
6. Every scene gets an entrance animation -- nothing appears un-animated
7. Every scene boundary gets a transition -- no unintentional jump cuts

## Anti-Patterns (Never Do These)
- Do not output React or Vue components
- Do not request 4K or 60fps unless explicitly instructed
- Do not skip /hyperframes slash command in Claude Code sessions
- Do not invent asset paths
- Do not auto-render without brief review
- Do not auto-publish -- human approval via Telegram required before any post

## LLM Routing
- Primary: Claude Sonnet (cost-efficient for HTML composition generation)
- Escalate to Claude Opus: complex multi-scene consulting deliverable with TTS
  narration and brand-specific motion design

## Full Knowledge Reference
Local: D:\Ai_Sandbox\agentsHQ\agentsHQ-hyperframes-knowledge-update.md
VPS:   ~/agentsHQ/docs/agentsHQ-hyperframes-knowledge-update.md

## External Resources
- Docs: https://hyperframes.heygen.com/introduction
- Prompt guide: https://hyperframes.heygen.com/guides/prompting
- GSAP: https://hyperframes.heygen.com/guides/gsap-animation
- Catalog: https://hyperframes.heygen.com/catalog
- GitHub: https://github.com/heygen-com/hyperframes

## Related Skills
- 3d-website-building / website_build: Use when the brief requires a live browser page.
  Both skills write HTML. Different output context entirely. Do not merge their outputs.
