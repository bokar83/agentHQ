# Studio: Faceless Agency on agentsHQ

**Codename:** studio
**Status:** active
**Lifespan:** open-ended
**Started:** 2026-04-25
**Owner:** Boubacar Barry
**One-line:** a faceless content agency that runs multiple branded channels on agentsHQ infrastructure as an adjacent revenue stream to Catalyst Works

**Project:** Build and operate a portfolio of faceless brand channels (no Boubacar on camera, no founder voice) that produce, schedule, and publish content with minimal daily input. Revenue comes from AdSense, sponsorship, and affiliate, not from consulting. Studio leverages the same orchestrator, crews, n8n workflows, Notion content boards, and Drive asset library that Atlas operates; it does not build a parallel infrastructure.

**Active session log:** see bottom of this file

---

## Done Definition

Studio is "done" when **three faceless channels run a fully automated content pipeline that produces a stable monthly net revenue floor without daily Boubacar input**.

Concretely, all of the following are true:

| # | Gate | Threshold |
|---|---|---|
| G1 | Channel count | 3 faceless channels live, each with its own brand surface, niche, and posting cadence |
| G2 | Production autonomy | Script, visuals, voiceover, composition, and caption are produced end-to-end by agentsHQ crews. Boubacar reviews, never authors. |
| G3 | Publishing autonomy | Posts hit each channel on schedule via Atlas M7 (Blotato or platform OAuth). No manual upload step. |
| G4 | Revenue floor | $1,000+/month net (after asset and tool costs) sustained for 90 consecutive days, summed across all channels |
| G5 | Operations cost | Boubacar's weekly studio time is ≤2 hours (review + steering only). Anything more says the system is not done. |

**Done = G1 through G5 all true at the same time.**

Anything outside these gates is descoped or future enhancement. If a gate stops being true after it was hit, that triggers a re-scope, not a silent slide.

---

## Status Snapshot

*Last updated: 2026-04-25 (Saturday)*

| Gate | Status | Notes |
|---|---|---|
| G1 Channels live | ❌ 0 of 3 | No studio-branded channels exist yet. Brief locked today; selection is M1. |
| G2 Production autonomy | 🟡 INFRA-READY | All component skills exist (kie_media, hyperframes, image-generator, clone-builder pattern). Pipeline not wired into a studio crew yet. |
| G3 Publishing autonomy | ❌ BLOCKED | Depends on Atlas M7 (auto-publish path resolved). Today's Atlas pipeline still requires Boubacar's tap. |
| G4 Revenue floor | ❌ $0 | No channels live, no monetization wired. |
| G5 Ops cost | N/A | Cannot measure until G1 is partially true. |

**Leverageable infrastructure (already shipped on agentsHQ):**
- Atlas autonomy layer: griot crew, scheduler, publish brief, error monitor, three-way nsync (active and stable)
- `kie_media` skill: text-to-image, image-to-image, text-to-video, image-to-video with model fallback, Drive upload, Supabase logging
- `hyperframes` + `hyperframes-cli` skills: code-driven video composition; HTML to MP4 with GSAP timelines, captions, TTS, transitions
- `image-generator` skill: prompt design for scroll-stop and deconstruction shots
- `clone-builder` and `clone-scout` skills: research-driven build pipeline pattern (Notion record in, deployed asset out); reusable shape for studio channel builds
- `boub_voice_mastery` skill (only as a negative reference; studio voices are explicitly NOT Boubacar's)
- n8n: ~50 workflows Boubacar has flagged as available for upload; framework for posting-agency automation
- Notion: existing Content Board pattern, schema verified 2026-04-24, ready to fork into a Studio Content Board per channel
- Drive: `05_Asset_Library/` already in use by kie_media; folder taxonomy in `reference_drive_folder_structure.md` supports per-channel subfolders
- Telegram one-tap publish (Path 3 today; bridge until Atlas M7 closes)

**Not yet built (studio-specific):**
- Channel brand identities (no faceless brand exists yet)
- Niche selection and channel theses
- Faceless voice strategies (text-to-speech voice, narration vs. on-screen-only, music-only)
- Studio Content Boards (per channel)
- Studio-side scheduler and publishing (will likely fork Atlas's heartbeat pattern)
- Monetization wiring (AdSense channel approval, affiliate program signups, sponsor scaffolding)
- Performance dashboards (per-channel views, subs, RPM, sponsor leads)

---

## Milestones

### M1: Channel and Niche Selection ⏳ QUEUED

**What:** Run a research-driven scout (clone-scout pattern, adapted) to identify 3 candidate niches for faceless channels. Each candidate gets: niche thesis, primary platform (YouTube vs. TikTok vs. Instagram vs. podcast), competitor density, monetization shape (AdSense-led vs. affiliate-led vs. sponsor-led), audience growth ceiling, production cost per asset, language target.

Lock the first channel (M2 input). Park the other two as M7 candidates.

**Why this is M1:** Everything downstream depends on niche. Building a brand or a pipeline before niche is locked is wasted motion. The clone-scout skill already encodes this discipline for tools; studio adapts it for channels.

**Trigger:** When Boubacar says "let's pick the niche" in a future session.
**Blockers:** None for the research; choice itself is a Boubacar decision.
**Branch:** `feat/studio-m1-niche-scout`
**ETA:** One scouting session (2-3 hr) + one decision session.

**Deliverable:** A locked brief in Notion for one channel, structured like a clone-scout record: niche, platform, monetization model, posting cadence, language target, voice strategy, success metric for first 90 days.

---

### M2: Brand Identity for Channel 1 ⏳ QUEUED

**What:** Lock the faceless brand identity for the first channel: name, logo, color palette, typography, motion vocabulary, voice identity (TTS voice or stock narration), end-card template, thumbnail template. Create the channel on the chosen platform with full brand assets uploaded (avatar, banner, about copy, links).

**Why:** Production cannot ship without a consistent surface. The brand is the moat against the next AI-content channel.

**Trigger:** M1 complete (channel picked).
**Blockers:** M1.
**Branch:** `feat/studio-m2-brand`
**ETA:** 3-5 hr build, plus channel approval wait time on platforms that gate (YouTube monetization, etc.).

**Leverages:** `design`, `brand`, `banner-design`, `image-generator` for thumbnails, `kie_media` for cover art generation.

---

### M3: Content Production Pipeline ⏳ QUEUED

**What:** Wire a studio-side crew that takes a topic in and produces a publish-ready asset out. Pipeline shape:

1. Topic queue entry (Notion Studio Content Board, channel = Channel 1)
2. Research and outline crew (Sonnet) builds script
3. Voice generation (TTS via hyperframes or kie_media route)
4. Visual asset generation (kie_media for images and b-roll, image-generator for prompts where Midjourney quality is needed)
5. Composition (hyperframes) assembles voiceover + visuals + captions + branded intro/outro
6. Render to platform-spec MP4 (16:9, 9:16, 1:1 per channel)
7. Asset lands in Drive `05_Asset_Library/<channel>/<date>/`
8. Notion record updates with asset URL, ready for scheduling

**Why:** Production is the content engine. Without this, studio is just a deck.

**Trigger:** M2 complete; first 3-5 manually-scripted topics queued in Notion.
**Blockers:** M2; also requires confirming faceless voice path (TTS vs. paid voice talent). Default to TTS.
**Branch:** `feat/studio-m3-production`
**ETA:** 8-12 hr build across 2-3 sessions; the pieces exist, the orchestration is new.

**Leverages:** `kie_media`, `hyperframes`, `hyperframes-cli`, `image-generator`, `boubacar-prompts` (for prompt engineering of the production crew, not for voice).

---

### M4: Multi-Channel Publish Pipeline ⏳ DECISION-GATED

**What:** Auto-publish from Notion Studio Content Board to the platform on Scheduled Date. Same shape as Atlas M7 but applied to studio channels.

**Why:** Without auto-publish, G3 is impossible and Boubacar's daily tap-to-publish does not scale to 3 channels.

**Trigger gate:** Atlas M7 resolved (Blotato live OR OAuth apps approved). Studio rides whichever path Atlas picked.
**Blockers:**
- Atlas M7
- Per-platform credentials per channel (each channel needs its own LinkedIn/X/YouTube/TikTok account, not Boubacar's personal)

**Branch:** `feat/studio-m4-publish`
**ETA:** 2-4 hr once Atlas M7 path is live (mostly per-channel credential plumbing).

---

### M5: Performance Tracking and Analytics Ingestion ⏳ QUEUED

**What:** Pull per-channel and per-asset metrics into a Studio dashboard (or Notion view). Daily ingestion of: views, watch time, subs gained, click-through, RPM, top-performing assets, drop-off curves where the platform exposes them.

**Why:** G4 (revenue) and G5 (ops cost) cannot be measured without this. Also, M6 monetization decisions and M8 niche pivots both feed off performance data.

**Trigger:** M3 has shipped at least 10 published assets per channel (enough data to be worth ingesting).
**Blockers:** M3 + M4. Per-platform analytics access (YouTube Data API, TikTok analytics, Meta Graph API) each have onboarding paperwork.
**Branch:** `feat/studio-m5-analytics`
**ETA:** 6-10 hr; per-platform API onboarding is the long pole.

---

### M6: Monetization Wiring ⏳ TRIGGER-GATED

**What:** Connect the revenue rails for Channel 1: AdSense application (YouTube) or platform fund (TikTok), affiliate program signups (Amazon Associates, Impact, ShareASale, niche-specific), sponsor outreach scaffolding (media kit auto-generated from M5 metrics).

**Why:** G4 (revenue floor) only starts counting once these rails are live. Most platforms gate monetization on subscriber/view thresholds, so M6 cannot be M2.

**Trigger gate:** Channel 1 hits the platform's monetization eligibility threshold (YouTube: 1,000 subs + 4,000 watch hours, or 500 subs + Shorts views per the alt path; TikTok and Meta have their own).
**Blockers:** M3 + M5; also gated by external platform approval (days to weeks).
**Branch:** `feat/studio-m6-monetize`
**ETA:** 4-6 hr active build, plus wall-clock approval wait.

---

### M7: Scale to Channel 2 ⏳ TRIGGER-GATED

**What:** Repeat M2 through M6 for the second-ranked candidate from M1. Reuse the production pipeline (M3) with channel-specific brand identity, voice, and niche.

**Why:** Single-channel studio is a side project, not an agency. The second channel proves the pipeline is reusable, not bespoke.

**Trigger gate:** Channel 1 has cleared M6 (monetization live) AND ops cost is tracking ≤2 hr/week on Channel 1 alone. Adding a second channel before the first is stable doubles the failure modes.
**Blockers:** M6 on Channel 1.
**Branch:** `feat/studio-m7-channel2`
**ETA:** 60-70% of M2 through M6 effort because the pipeline already exists.

---

### M8: Channel 3 + Operations Layer ⏳ TRIGGER-GATED

**What:** Add Channel 3 and lock the operations layer that lets the system run with Boubacar reviewing rather than authoring. Includes:

- Weekly review brief auto-generated from M5 dashboard, delivered to Telegram
- Topic backlog auto-replenished by a research crew when the queue drops below threshold
- Failure paths (asset rejected by platform, monetization revoked, RPM crashes) routed to a Studio Concierge crew (mirrors Atlas M4 Concierge pattern)
- Decision protocol for "kill a channel and reuse its slot" if a channel underperforms for 90 days

**Why:** This is where studio stops being a content factory and starts being an agency. Operations layer is the difference between G5 (≤2 hr/week) and Boubacar firefighting daily.

**Trigger gate:** M7 stable for 60 days with both channels above their monetization floor.
**Blockers:** M7.
**Branch:** `feat/studio-m8-ops`
**ETA:** 8-15 hr across multiple sessions.

---

## Descoped Items

These are explicit "do not build" decisions with reasons, so we do not relitigate.

| Item | Reason | Date decided | Revisit when |
|---|---|---|---|
| **Boubacar on camera** | The whole brand thesis is faceless. On-camera content goes on Catalyst Works channels, not studio. | 2026-04-25 | Never under the studio codename. A face-led brand would get its own roadmap. |
| **Direct competition with Catalyst Works** | Studio is adjacent revenue (ads, affiliate, sponsorship), not consulting. Same audience would dilute both brands. | 2026-04-25 | Never. If a studio channel grows into consulting, it routes to Catalyst Works as a lead source, not a competitor. |
| **Multi-channel from day one** | Three channels at once with no proven pipeline triples the failure modes. M1 picks one channel; M7 adds the second only after the first is monetized and stable. | 2026-04-25 | M7 trigger gate. |
| **Custom infrastructure** | Studio runs on agentsHQ. No new orchestrator, no new database, no new heartbeat layer. Forks the patterns Atlas built. | 2026-04-25 | Only if a channel has a constraint (live streaming, real-time chat, etc.) that the existing infra physically cannot serve. |
| **Paid voice talent for narration (Phase 1)** | TTS quality (ElevenLabs, Kai voices) is good enough for ad-revenue scale. Paid talent is a fixed-cost burden before revenue exists. | 2026-04-25 | Channel 1 hits $2k/month and a specific channel's metrics show TTS as a measurable conversion ceiling. |
| **LinkedIn-as-faceless** | LinkedIn rewards founder voice and face. Faceless LinkedIn underperforms. Boubacar's personal LinkedIn stays on Catalyst Works rails. | 2026-04-25 | Never under studio. |

---

## Cross-References

- **Sibling roadmaps:**
  - `atlas.md` (autonomy layer; studio depends on Atlas M7 for G3, and reuses Atlas heartbeat patterns)
  - `harvest.md` (Catalyst Works revenue; studio is the adjacency, harvest is the core)
  - `future-enhancements.md` (any studio idea that does not belong in M1 through M8 lands here)
- **Skills (existing capabilities studio leverages):**
  - `skills/kie_media/SKILL.md` (image and video generation with model fallback)
  - `skills/hyperframes/SKILL.md` and `skills/hyperframes-cli/SKILL.md` (video composition)
  - `skills/image-generator/SKILL.md` (prompt design for scroll-stop visuals)
  - `skills/clone-builder/SKILL.md` and `skills/clone-scout/SKILL.md` (research-and-build pattern adapted for channel selection)
  - `skills/design/SKILL.md`, `skills/brand/SKILL.md`, `skills/banner-design/SKILL.md` (M2 brand identity)
  - `skills/seo-strategy/SKILL.md` (M1 niche research and M3 metadata)
- **Memory:**
  - `project_clone_targets_db.md` (Notion DB pattern adapted for Studio Channels DB)
  - `project_clone_factory_defaults.md` (bilingual default and US revenue rails apply to faceless sites/landing pages where studio includes them)
  - `reference_publisher_options.md` (Path 1 Blotato vs. Path 2 OAuth for M4 publishing)
  - `reference_drive_folder_structure.md` (per-channel asset subfolders under `05_Asset_Library/`)
  - `reference_notion_content_board_schema.md` (schema to fork for Studio Content Boards)
- **Modules and infra to reuse (not build new):**
  - `orchestrator/heartbeat.py` (heartbeat scheduler; add studio wakes alongside griot)
  - `orchestrator/scheduler.py` and `orchestrator/publish_brief.py` (forkable patterns)
  - n8n workflows on `https://n8n.srv1040886.hstgr.cloud/` (Boubacar's ~50 staged workflows)

---

## Session Log

Append-only. Newest entry at the bottom. Each entry: date, what changed, what's next.

### 2026-04-25: Studio roadmap created

Boubacar locked the faceless agency vision: multiple branded channels, no founder face, runs on agentsHQ infrastructure, adjacent revenue stream to Catalyst Works (ads, affiliate, sponsorship; not consulting). Earlier in the same conversation he flagged ~50 n8n workflows already available to him that frame an ad agency or posting agency, and explicitly named the goal as "fully automate it, takes nothing away from my revenue work yet at the same time will help me to generate revenue."

Created this roadmap as a sibling to atlas (autonomy) and harvest (Catalyst Works revenue). Locked Done Definition (G1-G5: three channels, full production autonomy, full publishing autonomy, $1k/month net floor sustained 90 days, ops cost ≤2 hr/week). Mapped M1 through M8 with explicit dependency on Atlas M7 for auto-publish (G3) and on Atlas heartbeat patterns for studio scheduling. Documented six descoped items including the hard "no Boubacar on camera" rule that defines the brand.

Status snapshot is honest: zero studio-specific work shipped; full leverage available from Atlas, kie_media, hyperframes, image-generator, clone-builder/scout, n8n, Notion, Drive.

**Next:** lock down channel and niche selection (M1) in a future session. That session should run a clone-scout-style research pass adapted for channels (not tools), pick one niche, and lock the brief that feeds M2.

---
