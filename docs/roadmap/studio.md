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

**Reshaped 2026-04-25 after Council Pass 2.** Studio is a portfolio engine, not a fixed-channel-count build.

Studio is "done" when **the engine runs an open-ended portfolio of faceless channels that produces a stable monthly net revenue floor without daily Boubacar input**.

Concretely, all of the following are true:

| # | Gate | Threshold |
|---|---|---|
| G1 | Engine running | Studio Trend Scout daily, Pipeline DB live, QA crew gating every asset, production crew rendering, publish crew posting. End-to-end without manual intervention except review. |
| G2 | Production autonomy | Script, visuals, voiceover, composition, caption produced end-to-end by agentsHQ crews. Boubacar reviews, never authors. |
| G3 | Publishing autonomy | Posts hit each channel on schedule via Atlas M7 path (Blotato Creator $97/mo OR OAuth). No manual upload step. |
| G4 | Revenue floor | $1,000+/month net (after asset and tool costs and Blotato subscription) sustained for 90 consecutive days, summed across all active channels in the portfolio. |
| G5 | Operations cost | Boubacar's weekly studio time at steady state ≤3 hours (target). Hard ceiling 4 hours/week for 2 consecutive weeks triggers descope. Build phase budget is separate (up to 2 hr/day acceptable during M1-M3). |
| G6 | Channel count | At least 2 active channels in the portfolio at the time G4 is met. Open-ended above 2; agents continue spinning up new channels via M7-M8 as the trend scout finds opportunities. |

**Done = G1 through G6 all true at the same time.**

Anything outside these gates is descoped or future enhancement. If a gate stops being true after it was hit, that triggers a re-scope, not a silent slide.

---

## Status Snapshot

*Last updated: 2026-04-25 (Saturday evening)*

| Gate | Status | Notes |
|---|---|---|
| G1 Channels live | ❌ 0 of 3 | M1 reshaped: ENGINE first, channels second. Two-channel batch (Sankofa Stories + AI Catalyst) scaffolded as briefs in M1; brand identity ships in M2. |
| G2 Production autonomy | 🟡 INFRA-READY | All component skills exist (kie_media, hyperframes, image-generator, clone-builder pattern). Trend scout + QA crew + Pipeline DB are M1; production pipeline orchestration is M3. |
| G3 Publishing autonomy | ❌ BLOCKED | Depends on Atlas M7 (Blotato Creator $97/mo verified live 2026-04-25 OR OAuth path). Studio M4 rides whichever path Atlas picks. |
| G4 Revenue floor | ❌ $0 | No channels live, no monetization wired. Floor is portfolio-level: $1k/mo net across all active channels, sustained 90 days. |
| G5 Ops cost | N/A | Build phase budget: up to 2 hr/day. Steady-state target: 3 hr/week. Time-tracking ships in M1 Pipeline DB. |

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

### M1: Engine First, Two-Channel Batch Second 🟡 IN PROGRESS

**Reshaped 2026-04-25 after two Sankofa Council passes.** Original M1 was "lock one niche." Council Pass 2 reframed: studio is a portfolio engine, not a single-channel build. Engine ships first; channels ride downstream as dogfooding.

**Full M1 brief:** [docs/roadmap/studio/m1-engine-and-channel-batch.md](studio/m1-engine-and-channel-batch.md)

**What M1 ships:**

1. **Studio Trend Scout v0**: agent that scans YouTube/TikTok/IG for viral patterns within configured niches, posts daily Telegram brief with top 5 candidates per niche. Adapted from `clone-scout` pattern.
2. **Studio Pipeline DB**: Notion DB for niches, candidates, drafts, assets, publishes. Schema mirrors Content Board, simplified.
3. **Quality Review Crew**: 8-check QA layer that runs on every drafted asset before render. Fails route to Telegram, passes to qa-passed status.
4. **Two channel briefs scaffolded**: Sankofa Stories (faceless African folktales, retellings + originals, mixed cultures permitted, brand-new channel) and AI Catalyst (AI displacement education, openly Boubacar with HR-director framing, links to boubacarbarry.com, reuses existing AI Catalyst YouTube channel as testbed).
5. **Time-tracking property**: logs Boubacar's actual studio time per week. Build phase budget up to 2 hr/day. Steady-state target 3 hr/week.

**Why this shape:** the build airplane comes first, then test flights. Lock the engine, validate it against two niches, expand to channels 3-5 after data.

**Channels deferred (not killed):**
- Wealth Atlas (channel 3 candidate, queued behind 14 days of trend-scout data)
- Studio Logs / Agentic Diary (channel 4 candidate, queued behind 30 days of system activity)

**Trigger:** Now (2026-04-25 evening, M1 brief committed).
**Blockers:** None for engine build. Firecrawl 0/3000 credits flagged; default to YouTube Data API + native scrapers if credits not back by 2026-05-14.
**Branch:** `feat/studio-m1-engine` (to create at first code commit)
**ETA:** 12-18 build hours across 2-3 sessions. Ship target 2026-05-09.
**Save point:** create `savepoint-pre-studio-m1-engine-2026-04-25` before first code change.

**Done definition:** trend scout fires daily, Pipeline DB live in Notion with `NOTION_STUDIO_PIPELINE_DB_ID` in VPS .env, QA crew runs on a sample asset with all 8 checks firing, both channel briefs committed, time-tracking logged for the M1 build session itself.

---

### M2: Brand Identity for Two Channels ⏳ QUEUED

**What:** Lock brand identity for BOTH M1 channels in parallel. Each channel gets: name (final), logo, color palette, typography, motion vocabulary, voice identity (TTS voice or stock narration), end-card template, thumbnail template, channel-page assets (avatar, banner, about copy, links).

- **Sankofa Stories** (working name): faceless storytelling brand, warm/earthy palette tied to African textile motifs, single recurring TTS narrator, brand-new YouTube channel + IG + TikTok + Spotify podcast feed.
- **AI Catalyst** (existing channel reused): faceless explainer brand under Boubacar's name, "Director of HR with global experience" framing, modern/minimal palette, links to boubacarbarry.com, reuses existing YouTube channel + new IG + TikTok.

**Why:** Production cannot ship without consistent brand surfaces. Two channels in parallel is the M1 batch shape, so M2 builds both.

**Trigger:** M1 complete (engine running, briefs reviewed, 7+ days of trend-scout daily briefs reviewed by Boubacar).
**Blockers:** M1.
**Branch:** `feat/studio-m2-brand`
**ETA:** 5-8 hr build across 1-2 sessions, plus platform approval wait time on YouTube monetization for the new Sankofa channel.

**Leverages:** `design`, `brand`, `banner-design`, `image-generator` for thumbnails, `kie_media` for cover art generation.

---

### M3: Content Production Pipeline ⏳ QUEUED

**What:** Wire the studio production crew that takes a Pipeline DB candidate (qa-passed) and produces a publish-ready asset. Pipeline shape:

1. Pipeline DB candidate flips to Status=drafted (Sonnet builds script from trend-scout candidate hook + twist)
2. QA crew runs on script (M1 dependency), passes to Status=qa-passed
3. Voice generation (ElevenLabs default; Kai TTS via kie_media as fallback)
4. Visual asset generation (kie_media seedream/4.5 for stills, kling v2.1 master for hero morphs)
5. Composition (hyperframes) assembles voiceover + visuals + captions + branded intro/outro per channel brand
6. Render to platform specs (16:9 long-form, 9:16 shorts, 1:1 IG square)
7. Asset lands in Drive `05_Asset_Library/<channel>/<YYYY-MM-DD>/`
8. Pipeline DB record updates with Asset URL, flips to Status=scheduled (M4 picks up)

**Adds in M3 (beyond M1 engine):**
- Regional motif library (image-generator prompt enforcement per niche tag, addresses Sankofa visual cultural-mismatch risk)
- Pronunciation dictionary (ElevenLabs SSML phonetic tags for African names, AI/HR jargon)
- Per-channel brand bible loaded into production crew prompts

**Why:** M1 builds the trend scout and QA crew; M2 locks brand identities; M3 is where candidates become rendered videos. Without M3, the engine outputs ideas with nowhere to go.

**Trigger:** M2 complete; first 5 trend-scout-approved candidates queued in Pipeline DB for each of the two channels.
**Blockers:** M2; faceless voice path confirmed (default ElevenLabs).
**Branch:** `feat/studio-m3-production`
**ETA:** 10-15 hr build across 2-3 sessions.

**Leverages:** `kie_media`, `hyperframes`, `hyperframes-cli`, `image-generator`.

---

### M4: Multi-Channel Publish Pipeline ⏳ DECISION-GATED

**What:** Auto-publish from Studio Pipeline DB to the platform on Scheduled Date. Default path: Blotato Creator at $97/mo (verified live 2026-04-25), supports YouTube + IG + TikTok + Threads + LinkedIn + X + FB + Pinterest, 5,000 AI credits/mo, 40 social accounts (covers all M1+M7+M8 channels). Atlas's M7a Blotato spike outcome determines whether studio rides Blotato or pivots to OAuth.

**Why:** Without auto-publish, G3 is impossible. With two channels in the M1 batch and 4-6 platform endpoints per channel, manual publishing alone breaks the 3 hr/week steady-state budget.

**Trigger gate:** Atlas M7 resolved (Blotato Creator subscription active OR OAuth apps approved). Studio rides whichever path Atlas picked.
**Blockers:**
- Atlas M7
- Per-channel platform accounts (Sankofa Stories needs new YouTube + IG + TikTok + Spotify; AI Catalyst reuses existing YouTube but needs new IG + TikTok)

**Branch:** `feat/studio-m4-publish`
**ETA:** 3-5 hr once Atlas M7 path is live (mostly per-channel credential plumbing in Blotato).
**Cost:** $97/mo Blotato Creator. Triggers when M4 starts. Adds to studio operating cost ledger.

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

### M7: Channel 3 (Wealth Atlas or Trend-Scout Pick) ⏳ TRIGGER-GATED

**What:** Add a third channel to the portfolio. Default candidate: Wealth Atlas (faceless first-gen personal finance, $15-22 RPM, deferred from M1). Alternative: whichever niche the trend scout has produced strongest signal on after 14+ days of daily briefs. Reuses M3 production pipeline with channel-specific brand and niche.

**Why:** M1 ships two channels and the engine. Channel 3 proves the engine scales beyond a hand-picked batch and that the trend scout's niche-finding capability works. Studio's "find new niches" job becomes self-driving here.

**Trigger gate:**
- Sankofa Stories OR AI Catalyst has cleared M6 (monetization live)
- AND ops cost is tracking at or below 3 hr/week steady state for at least 30 days
- AND trend scout has output 14+ days of daily briefs that Boubacar reviewed and judged useful

**Blockers:** M6 on at least one M1 channel; trend scout signal track record.
**Branch:** `feat/studio-m7-channel3`
**ETA:** 50-60% of M2 through M6 effort because the engine and pipeline exist; only brand identity + per-niche production tuning is new.

---

### M8: Channel 4 + Operations Layer + Portfolio Engine Maturation ⏳ TRIGGER-GATED

**What:** Add Channel 4 (likely Studio Logs / Agentic Diary, the meta-content channel that is the proof point for AI Catalyst and CW) AND lock the operations layer that lets the system run open-endedly. Includes:

- Studio Logs channel: faceless meta-content showing the studio system itself running (dashboards, cost ledger, trend-scout output, win/fail patterns). Cheapest to produce; rides on the system's own activity logs.
- Weekly review brief auto-generated from M5 dashboard, delivered to Telegram
- Topic backlog auto-replenished by trend scout when any channel's queue drops below threshold
- Failure paths (asset rejected by platform, monetization revoked, RPM crashes) routed to a Studio Concierge crew (mirrors Atlas M4 Concierge pattern)
- Channel-kill protocol: if a channel underperforms for 90 days (revenue below niche floor, engagement decay), the engine reallocates that slot to a fresh trend-scout pick
- Channel-spawn protocol: when trend scout flags a niche with strong signal AND no overlap with active channels, propose a new channel via Telegram for Boubacar's one-tap approve

**Why:** This is where studio stops being a fixed-channel build and becomes a true open-ended portfolio engine. Operations layer is the difference between G5 (≤3 hr/week steady state) and Boubacar firefighting weekly.

**Trigger gate:** M7 stable for 60 days with all three channels above their per-channel revenue floor.
**Blockers:** M7.
**Branch:** `feat/studio-m8-ops`
**ETA:** 12-18 hr across multiple sessions.

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
| **Pseudonymous AI Displacement channel** | Council Pass 2: pseudonymity is a fuse not a fix. AI Catalyst channel ships openly under Boubacar's name with HR-director framing, links to boubacarbarry.com. The "this is built by an AI strategist" angle is the moat, not anonymity. | 2026-04-25 | Only if a specific platform demands an anonymous handle for legal reasons. |
| **Single-channel build for M1** | Council Pass 2 reframed M1 as portfolio engine first, two-channel batch second. A single-channel-locked-and-built M1 misses the leverage of the trend scout. | 2026-04-25 | Never under studio. M2+ may build channels one at a time, but M1 ships the engine + 2 channel briefs. |
| **Hard cap of 3 channels** | Original Done Definition fixed the channel count at 3. Boubacar's stated direction is portfolio open-ended ("unlimited testable channels"), with the trend scout finding new niches and the engine spawning channels. New floor is 2, no ceiling, gated on G4 revenue floor and G5 ops cost. | 2026-04-25 | If portfolio rot becomes a real failure mode (e.g. >5 channels with declining quality), descope back to a hard cap with explicit revisit. |
| **Catalog-purist Sankofa redesign** | Council Pass 1 proposed a "faithful retelling of public-domain sources only" redesign for Sankofa Stories. Boubacar rejected: he is African, has standing to remix and create original tales, and Sankofa Stories is entertainment for African children + diaspora, not academic ethnography. Creative freedom retained. | 2026-04-25 | Never. Sourcing remains a quality input, not a constraint. |

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

### 2026-04-25 (evening): M1 reshaped from "lock one niche" to "engine first, two-channel batch"

Studio session opened M1. Read clone-scout skill, AI displacement strategy memo, no-coffee-or-alcohol rule, kie_media operational facts, hyperframes capability. Generated 3 candidates: Sankofa Stories (faceless African folktales, $5-9 RPM, slow burn), AI Displacement Survivor (faceless career-AI, $10-22 RPM, ties to existing pseudonymous strategy memo), Wealth Atlas (faceless first-gen finance, $15-22 RPM). Verified 2026 YouTube Partner Program thresholds, faceless-niche RPM ranges, and the January 2026 inauthentic-content enforcement wave (16 channels with 4.7B views terminated).

**Sankofa Council Pass 1.** Ran the 5-voice Council on the 3 candidates. Verdict: do not pick a candidate today, pick a path first. The Council surfaced that all three candidates had research moats but the roadmap promised 100% agent autonomy, which is a contradiction. Two paths offered: (a) redesign Sankofa around catalog-purist sourcing, or (b) rewrite the Done Definition to admit Boubacar reviews each video.

**Boubacar's correction.** Rejected the catalog-purist redesign (he is African, has standing to remix, Sankofa is entertainment not ethnography). Reframed "research" as trend-spotting and content-direction, not academic verification. AI Displacement reframed as a Catalyst Works PROOF POINT, not a competitor; pseudonymity dropped, channel ships openly under his name with HR-director framing, links to boubacarbarry.com. Channel count opened to "unlimited testable channels." Errors are okay; flag-early-and-iterate is the bar.

**Sankofa Council Pass 2.** Re-ran with corrections. Pass 2 verdict: studio is a portfolio engine, not a fixed-channel build. Engine ships first; channels ride downstream. AI Catalyst becomes the load-bearing channel because the meta-story (this channel is built BY the AI strategy it teaches) is the moat. Sankofa Stories stays as the creative testbed where the system can fail loudly without consequence. Wealth Atlas defers to channel 3, Studio Logs defers to channel 4. Riskiest assumption: the time budget. Build phase up to 2 hr/day acceptable; steady state target 3 hr/week; hard ceiling 4 hr/week for 2 consecutive weeks triggers descope.

**M1 reshape locked.** Built `docs/roadmap/studio/m1-engine-and-channel-batch.md` (full brief). M1 ships:

1. Studio Trend Scout v0 (orchestrator/studio_trend_scout.py + heartbeat wake)
2. Studio Pipeline DB (Notion, schema mirroring Content Board)
3. Quality Review Crew (8-check QA layer, fails route to Telegram)
4. Two channel briefs scaffolded (Sankofa Stories new channel; AI Catalyst reuses existing YouTube channel)
5. Time-tracking property in Pipeline DB

Studio.md updates:
- Status Snapshot reflects M1 IN PROGRESS, build budget split, Blotato Creator $97/mo (verified live today, not the $9/mo memory rot from earlier sessions; matches Atlas M7a finding) flagged for M4
- Done Definition rewritten: 6 gates not 5. G6 added (≥2 channels at G4 met, open-ended above 2). G5 split into build-phase budget vs steady-state budget. Channel count is no longer fixed at 3.
- M1 milestone block rewritten with engine-first scope
- M2 expanded to ship brand identity for BOTH channels in parallel
- M3 specifies regional motif library + pronunciation dictionary as M3 adds (deferred from M1)
- M4 names Blotato Creator $97/mo as default publish path
- M7 reshaped to "channel 3 (Wealth Atlas or trend-scout pick)"
- M8 reshaped to "channel 4 (Studio Logs) + ops layer + portfolio engine maturation"
- Descoped Items table grew by 4: pseudonymous AI Displacement, single-channel M1, hard cap of 3 channels, catalog-purist Sankofa redesign

Cost ceiling for M1 build: <$20 in tokens. Firecrawl 0/3000 until 2026-05-14 flagged; default fallback to YouTube Data API + native scrapers if credits not back.

**Next session:**

1. Create save point `savepoint-pre-studio-m1-engine-2026-04-25` before any code change.
2. Open `feat/studio-m1-engine` branch.
3. Build sequence (12-18 hr across 2-3 sessions): Notion Studio Pipeline DB → Trend Scout v0 → heartbeat wake → Telegram daily brief formatter → Quality Review Crew → tests → Boubacar reviews 1 sample run end-to-end.
4. Three-way nsync, M1 marked shipped, M2 (brand identity for both channels) becomes next move.

**State at session pause:** local clean on main, 1 new doc (`docs/roadmap/studio/m1-engine-and-channel-batch.md`), 1 modified doc (`docs/roadmap/studio.md`), 1 untracked scratch dir (`scripts/skool-harvester/`, unrelated). About to commit, push to origin, three-way nsync.

---
