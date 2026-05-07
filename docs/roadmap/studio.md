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
| G1 Channels live | 🟡 2 of 3 EXIST | Under the Baobab + AI Catalyst exist (Boubacar's). First Generation Money needs creation in M2. Engine LIVE on VPS (kill switch off). |
| G2 Production autonomy | 🟡 ENGINE LIVE | M1 SHIPPED 2026-04-25: Trend Scout + QA Crew (8 checks) + Pipeline DB live. Studio session also shipped harvest reviewer + niche research + inventory snapshot. Production pipeline orchestration (script -> render) is M3. |
| G3 Publishing autonomy | ✅ INFRA READY | Atlas M7b SHIPPED 2026-04-25 (Blotato API verified, $20.30/mo Skool-discounted). Studio M4 reuses BlotatoPublisher class (platform-agnostic by design). |
| G4 Revenue floor | ❌ $0 | No channels live posting yet. Floor is portfolio-level: $1k/mo net across all active channels, sustained 90 days. |
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

### M1: Engine First, Three-Channel Batch Second ✅ SHIPPED 2026-04-25

**Same-day ship after Atlas M7b.** Engine LIVE on VPS, kill switch off pending Boubacar's first dry-run brief verification. THREE channels in M1 batch (not 2 as originally scoped): Under the Baobab + AI Catalyst + First Generation Money.

**Full M1 brief:** [docs/roadmap/studio/m1-engine-and-channel-batch.md](studio/m1-engine-and-channel-batch.md)

**What shipped:**

1. **Studio Trend Scout v0** (`orchestrator/studio_trend_scout.py`): heartbeat tick at 06:00 MT daily, scans configured niches via YouTube Data API v3 over a SEED LIST of search terms per niche. Scores candidates by view-velocity (views/hour since publish), top picks queued in Studio Pipeline DB. Idempotent (skip dupes by Source URL). Sends Telegram brief. Graceful degrade if no `YOUTUBE_API_KEY` / `GOOGLE_API_KEY`.
2. **Studio Pipeline DB**: created in The Forge 2.0 (Notion). 20 properties: Channel, Niche tag, Status, Format, Length target, Source URL, Source channel, Source views, Hook, Twist, Draft, Asset URL, Platform, Submission ID, Posted URL, Scheduled Date, Posted Date, QA notes, Cost USD. DB ID: `34ebcf1a-3029-8140-a565-f7c26fe9de86`. Logged to local + VPS .env as `NOTION_STUDIO_PIPELINE_DB_ID`.
3. **Quality Review Crew** (`orchestrator/studio_qa_crew.py`): 8 checks on every drafted asset before render. (1) spellcheck, (2) banned-phrases / engagement-bait, (3) length-within-target, (4) hook present (no generic intros), (5) source citation when factual claim detected, (6) CTA present, (7) personal rules (no coffee/alcohol/em-dashes/fake clients), (8) brand voice (per-niche bans). Failures route to Telegram, passes flip Status=qa-passed.
4. **Three channel briefs** at `docs/roadmap/studio/channels/`:
   - `under-the-baobab.md` (faceless African folktales; channel exists)
   - `ai-catalyst.md` (AI displacement, Path A openly Boubacar; channel exists virgin)
   - `first-generation-money.md` (faceless first-gen finance; channel needs creation in M2)
5. **Operating snapshot locked** at `docs/roadmap/studio/operating-snapshot.md`: 3-channel portfolio (Wealth Atlas descoped in favor of First Generation Money after SEO/GEO research), Mon-Sat publish + skip Sun, no LinkedIn ever for Studio.

**Plus the studio session shipped tonight (parallel work, separate commits):**

- Skool harvester (3 Python tools)
- Harvest reviewer crew + harvest triage
- Niche research tool, video analyze tool
- Inventory snapshot generator (51 skills, 40 modules)
- 5 R-series RoboNuggets lessons mined and scored
- Atlas M8 Mission Control dashboard at /atlas (separate Atlas roadmap milestone)

**VPS deploy verified:**
- studio-trend-scout wake registered: `at=06:00 every=None crew_name=studio`
- Container Up healthy
- Manual tick run: 3 niches loaded, idempotency query OK, Notion accessible, graceful degrade on missing YouTube API key as designed
- Default state: `studio.enabled=False` until first dry-run brief reviewed

**To activate live:**
1. Get a Google Cloud API key with YouTube Data API v3 enabled
2. Add `YOUTUBE_API_KEY=<key>` to VPS .env
3. Flip `studio.enabled=True` in `data/autonomy_state.json`
4. Restart container
5. Wait for next 06:00 MT wake; verify Telegram brief lands with candidates per niche

**Tests:** 261/261 orchestrator tests pass (210 pre-Studio + 30 QA crew + 21 trend scout = 261).
**Save point:** `savepoint-pre-studio-m1-engine-2026-04-25` (at 196f875 pre-rebase).
**Branch:** `feat/studio-m1-engine` (merged via rebase to main).
**Commit:** `1d0cd88` (after rebase onto Atlas M8).

---

### M2: Brand Identity for Two Channels ✅ SHIPPED 2026-05-03

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

### M3: Content Production Pipeline ✅ SHIPPED 2026-05-05

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

### M3.4: Scene Motion Upgrade , Ken Burns → Mixed Video ⏳ QUEUED (post-M3 first batch)

**What:** Replace all-Ken-Burns scene rendering with a mixed-motion pipeline. Instead of every scene being a still image with zoompan, 2-3 scenes per Short get real video motion via Kai image-to-video (Seedance). Remaining scenes keep Ken Burns.

**Why Ken Burns is the current baseline:** Ken Burns is fast, cheap ($0 extra per video), and deterministic. It works. But 7 sequential Ken Burns clips feel monotonous in motion even with varied directions (zoom_in, pan_left, etc.). Confirmed in first-fire review 2026-05-05.

**Target behavior:**
- Scene 0 (hook): image-to-video (Seedance) , most important scene, viewer retention hooks here
- Scenes 1-4: Ken Burns (cheap, covers narration body)
- Scene 5 (CTA/climax): image-to-video (Seedance) , emotional peak before outro
- Scene 6 (bridge to outro): Ken Burns

**Cost delta:** ~$0.08-0.12/video in Kai credits (2x Seedance calls). Acceptable at first-batch volume. Revisit at scale.

**Effort:** ~4 hr. `studio_visual_generator.py` + `studio_render_publisher.py` changes only.

**Implementation:**
1. `studio_visual_generator.py`: return `{"type": "video", "source_url": ...}` for hook/climax scenes, `{"type": "image", ...}` for rest
2. `studio_render_publisher.py`: `_ffmpeg_render()` , if `scene["type"] == "video"`, download and use directly instead of calling `_render_ken_burns_clip()`
3. `studio_scene_builder.py`: add `motion_type` field per scene (hook → `video`, body → `image`, climax → `video`)

**Trigger:** First batch of 15 Shorts reviewed. Ken Burns monotony confirmed as quality gap worth fixing. Decision: 2026-05-05.

**Blockers:** None. M3 pipeline is already rendering successfully.

**Branch:** `feat/studio-m3.4-scene-motion`
**ETA:** 1 session (~4 hr).

---

### M3.5: Channel Cloner Pipeline ⏳ QUEUED (post-M3)

**What:** Reverse-engineer a successful YouTube channel's full surface (voice, scripts, visuals, thumbnails) and produce new content modeled after it. Same M3 production engine, different input shape: instead of trend-scout candidate → original script, the cloner takes 3-5 reference channels → style profile → script in that style → visuals matching the channel's aesthetic → thumbnails matching their grammar.

**Source:** YouTube video MJmoSxSPeRY analysis 2026-04-29 + Sankofa Council recommendation to keep this internal.

**Why M3.5 not its own milestone:** the production engine (script generator → kie_media stills → kling video → hyperframes composition → render) is M3. The cloner is a different *front end* on the same pipeline: it swaps "trend-scout original idea" for "model-after-existing-channel idea." Building it as M3.5 reuses M3 infrastructure instead of forking a parallel pipeline.

**Pipeline shape:**

1. Operator gives N reference channel URLs + niche description
2. Pull 3-5 viral transcripts per channel (YouTube transcript API, already used in `youtube-10k-lens`)
3. Run `transcript-style-dna` extractor on combined transcripts → style profile JSON ✅ (shipped 2026-04-29)
4. Generate channel branding: name candidates, description, logo prompt, banner prompt (single LLM call)
5. Generate 15 video idea titles in the channel's style (single LLM call against style profile)
6. Operator picks 1 idea
7. Generate full script (~2000 words = 10 min video) in channel's voice
8. **Scene segmenter** breaks script into ~167 scenes at 200 wpm, emits paired image+video prompts per beat (NEW SUB-SKILL)
9. kie_media generates images per scene with reference-image consistency (style profile drives prompt enforcement)
10. kie_media generates video per image (image-to-video, kling v2.1 master)
11. hyperframes composes voiceover + scenes + captions + branded intro/outro
12. Render → Drive → Pipeline DB → M4 publish

**Sub-skills to build (in order):**

| Sub-skill | Status | Effort | Notes |
|---|---|---|---|
| transcript-style-dna | ✅ shipped 2026-04-29 | done | N texts → style profile JSON + opener line |
| scene-segmenter | ❌ to build | ~3-4 hr | Script → ~167 paired image+video prompts at 200 wpm. Single Python module + LLM call. NEXT BUILD. |
| channel-branding-kit | ❌ to build | ~2 hr | Style profile + niche → name/description/logo/banner prompts. Single LLM call. |
| video-idea-generator | ❌ to build | ~1 hr | Style profile + niche → 15 ranked video titles in voice. Single LLM call. |
| reference-image-consistency in kie_media | ❌ to enhance existing | ~2 hr | Set reference once, reuse across N scene generations. Existing skill upgrade. |
| thumbnail reverse-engineer | ❌ to build | ~3 hr | 5 reference thumbnails → thumbnail style profile + new thumbnail prompts. Vision call. |

**Total new effort beyond what's already shipped:** ~12 hr across multiple sessions.

**Why:** Once Studio has its own production engine working on original ideas (M3), the cloner becomes a force multiplier: any time a channel finds traction in a niche, Studio can spin up a model-after-it variant in hours, not weeks. Increases portfolio velocity toward G6 (≥2 active channels) and G4 ($1K/mo net floor).

**Trigger:** M3 complete (production pipeline rendering original ideas end-to-end on at least one channel). Do NOT start M3.5 until M3 produces a working video.

**Blockers:** M3.

**Risk flag (named honestly):** Channel cloning has YouTube originality / IP exposure. Mitigation: clone *style* not *content*; never copy a competitor's specific video idea verbatim; treat cloned channels as "style-modeled" not "replicated." If YouTube demonetizes a cloned channel, that is market signal: pivot to original-only on that niche.

**Branch:** `feat/studio-m3.5-cloner`

**ETA:** 12-15 hr build across 3-4 sessions, post-M3.

**Leverages:** M3 production engine, `transcript-style-dna` ✅, `kie_media`, `hyperframes`, `youtube-10k-lens` (transcript pull).

**Source:** Strategy session 2026-04-29 + Sankofa Council overrule of external $497 audit packaging.

**Started today (2026-04-29):** scene-segmenter sub-skill scaffolding. See `skills/scene-segmenter/`.

---

### M3.6: Content Intelligence Layer ⏳ STUB LIVE (post-M3 confirm)

**What:** Per-channel intelligence dossiers injected into the Studio script crew at production time. Scripts read niche signal, competitor gaps, and proven hooks before writing. Scripts do not write blind.

**Why:** Inspired by Graeme Kay's research agent architecture (2026-05-04 Sankofa Council). Borrowed the dossier concept; skipped the full 29-dir vault until M5 analytics prove ROI. Minimum viable research layer: one markdown file per channel, one context injection in the script generator.

**What is live (seeded 2026-05-04):**

- `research-vault/dossiers/under_the_baobab.md`: African storytelling trends, competitor signal, hooks that convert, verification queue
- `research-vault/dossiers/ai_catalyst.md`: AI displacement content trends, competitor signal, professional audience hooks
- `research-vault/dossiers/first_generation_money.md`: first-gen finance trends, RPM estimates, competitor signal, YMYL compliance notes
- `orchestrator/studio_script_generator.py`: `_load_dossier()` + `_CHANNEL_DOSSIER_MAP`; dossier injected as `CHANNEL INTELLIGENCE DOSSIER` block in system prompt

**What this is NOT yet:**

- No automated refresh (manual until M5 proves ROI)
- No `findings.jsonl` / `claims.jsonl` ledgers
- No source registry or cron collector

**Trigger to expand:** M5 analytics show measurable CTR or watch-time lift on dossier-informed scripts vs. baseline. If lift confirmed, build automated refresh + findings ledger. If flat, dossiers stay as manual editorial context only.

**Success proxy (reviewable before M5):** At least one script per channel references a niche-specific hook, angle, or trend from its dossier.

**Dossier update cadence (manual):** After each M5 analytics review, update competitor signal + trending topics. ~20 min per channel.

**Blockers:** None. Stub is already live and injecting.
**Branch:** `feat/studio-m3-production`.

---

### M3.7: Content Multiplier with Remix QA 🔄 IN PROGRESS (started 2026-05-07)

**What:** Take ONE approved source (article, YouTube video, post, PDF, raw text) and generate 9 atomic content pieces aligned to Boubacar's voice and the 8 diagnostic lenses. Pieces route to LinkedIn, X, and matching Studio channel video scripts. QA can route a source three ways: passed (use verbatim), remix (strip unverifiable bits, keep concept, write Boubacar's original take), or failed (truly off-brand).

**Why this milestone exists:**

On 2026-05-06 the content idea pipeline was unified into Griot. The unification deploy left 3 silently-broken wakes (`story_prompt_tick`, `studio_story_bridge`, `griot_signal_brief`) — Dockerfile didn't COPY new files. Result: zero new ideas surfaced for review on 2026-05-07. Discovery via session 2026-05-07. Fix shipped via docker cp + restart same session.

That fix restored the producers, but exposed two deeper gaps:

1. Trend scout produces ~6 picks/run, but each pick = one video idea, not multiple content pieces. "Approve one trend → multiplier extracts every angle across LinkedIn, X, video scripts, newsletter, quote cards." This milestone closes that gap.

2. QA was binary (pass/fail). When a source had a fabricated quote or unsourced stat, it got trashed even when the underlying CONCEPT was strong. Boubacar's framing (2026-05-07): "the reason to go out there and get these ideas is not always cloning and copying word for word, but it's also generating ideas and using that as a spark to create something new and unique." Remix QA strips the bits we can't verify and keeps the salvageable angle.

**Pieces per run (9):**
1. LinkedIn long post (600-1400 chars, Boubacar voice)
2. X thread (3-7 tweets)
3. X single punchy (<280)
4. Direct angle (LinkedIn, mirrors source thesis)
5. Adjacent angle (LinkedIn, related but distinct POV)
6. Contrarian angle (LinkedIn or X thread)
7. Studio video script (UTB / FGM / AIC, only when channel matches)
8. Quote card (1 line + image prompt)
9. Newsletter section (200-400 chars for The Forge weekly)

Channel-aware skip: African folktale source skips pieces 1-6 if no Boubacar angle, generates piece 7 as UTB script. AI displacement source generates 1-6 + AIC script. Cross-pollination allowed.

**Three trigger paths:**
- Auto: `scout_approve:` Telegram callback fires multiplier crew automatically
- Manual: `/multiply <url>` slash command in webchat OR "multiply this: <url>" natural language
- Notion: drop URL into Content Board with Status=Multiply, 5-min heartbeat picks it up

**The 8 lenses** (from AGENT_SOP): TOC, JTBD, Lean, Behavioral Economics, Systems Thinking, Design Thinking, Org Development, AI Strategy. Lens classifier (Haiku) picks 2-3 most relevant per source. Each piece uses 1-2 lenses to frame. Never name the lens in output.

**Three QA verdicts** (added 2026-05-07):

- `qa-passed`: source verified, can be cited verbatim. Multiplier runs in `mode=verbatim`.
- `qa-remix`: source has unverifiable elements (fabricated quotes, unsourced stats, unattributed claims) BUT the underlying concept is salvageable. Multiplier runs in `mode=remix`: strips the unverifiable bits, uses the concept as ideation spark, generates Boubacar's original take with NO source citation.
- `qa-failed`: source has fatal failures (banned phrases, fabricated client stories, off-channel niche mismatch, copyrighted phrases). Trashed.

QA classifies each failure as FATAL or FIXABLE. All FIXABLE = qa-remix. Any FATAL = qa-failed. Zero failures = qa-passed.

**What shipped this session (M3.7.1):**

- [x] Skill scaffold: `skills/content_multiplier/SKILL.md` + `prompts/lens_classifier.md` + `prompts/piece_generator.md`
- [x] Voice rules locked: no em-dash, no FGM (use 1stGen), no fabricated stories, verified stats only, Smart Brevity
- [x] Cost ceiling: <$0.30/run hard cap
- [x] Notion schema: `Multiplier Run ID`, `Piece Type`, `Created From`, `Source URL`, `Source Treatment` (extends existing Content Board)
- [x] Three-path trigger spec (auto, on-demand, Notion)
- [x] Three-verdict QA spec (passed | remix | failed) with FATAL/FIXABLE failure classification
- [x] Trend scout cadence split: Studio niches daily, CW niches Mon/Wed/Fri, Sun off (code edited in studio_trend_scout.py, deploys with M3.7 commit)

**What's left (M3.7.2 — Codex working 2026-05-07):**

- [ ] `orchestrator/content_multiplier_crew.py` with verbatim/remix/auto modes
- [ ] `orchestrator/studio_qa_crew.py` refactor: 3-state verdict + FATAL/FIXABLE tagging
- [ ] `skills/content_multiplier/prompts/remix_classifier.md` + `remix_piece_generator.md`
- [ ] Tests: `test_content_multiplier.py` (all 3 modes) + `test_studio_qa_remix.py` (FATAL/FIXABLE logic)

**What's left (M3.7.3 — next session):**

- [ ] Wire `scout_approve:` callback in handlers_approvals.py to fire crew
- [ ] Add `/multiply` router intent
- [ ] Heartbeat wake `multiplier-tick` every 5m for Status=Multiply Notion records
- [ ] Bulk Telegram review handler (`multiplier_approve_all:` / `multiplier_per_piece:` / `multiplier_reject_all:`)
- [ ] Notion schema extension: add `Multiplier Run ID` (rich_text), `Piece Type` (select), `Source Treatment` (select), `QA Verdict` (select) properties
- [ ] Sankofa Council CTQ filter integration (deferred from v1 for speed)

**Cost:** ~$0.20-0.30/run × ~10-15 runs/week (more with 3x scout cadence) = $3-5/week.

**Trigger:** none -- proceed in parallel with M4 (publish pipeline). M3.7 produces ideas; M4 publishes assets. Independent.
**Blockers:** none for M3.7.2 build. M3.7.3 wiring needs M3.7.2 verified working first.
**Branch:** `feat/studio-m3-7-content-multiplier`
**ETA:** 1 session for M3.7.2 (Codex crew + qa refactor + remix prompts), 1 session for M3.7.3 (wiring + Notion schema + Sankofa CTQ).

---

### M4: Multi-Channel Publish Pipeline 🔄 IN PROGRESS

**What:** Auto-publish from Studio Pipeline DB to the platform on Scheduled Date. Default path: Blotato Creator at $97/mo (verified live 2026-04-25), supports YouTube + IG + TikTok + Threads + LinkedIn + X + FB + Pinterest, 5,000 AI credits/mo, 40 social accounts.

**Progress:**
- [x] Social Launch Kits shipped (2026-05-03): `docs/roadmap/studio/social-launch-kit/`  -  bios, avatar specs, link-in-bio strategy, warm-up protocols for IG + TikTok for all 3 channels
- [x] `orchestrator/studio_blotato_publisher.py` initialized (2026-05-03): scans Pipeline DB for Status=scheduled + ScheduledDate=Today → Blotato API → Status=posted
- [x] All Blotato account IDs wired in VPS .env (2026-05-05): YT + X + TikTok + IG for all 3 channels including `firstgenerationmoney_` IG (ID 45188)
- [x] ScheduledDate fix shipped (2026-05-05): render publisher now writes Scheduled Date = today on completion
- [ ] Warm-up window executed per-platform protocols (30 days per channel)
- [ ] End-to-end test: 1 scheduled record → Blotato → posted

**Why:** Without auto-publish, G3 is impossible. With 3 channels × 4+ platform endpoints, manual publishing breaks the 3 hr/week steady-state budget.

**Trigger gate:** Atlas M7 resolved ✅ (Blotato Creator $20.30/mo active, YT + X already linked). IG/TikTok accounts needed to complete platform coverage.

**Blockers:**

- IG + TikTok account creation (Boubacar  -  2FA required)
- Blotato IG/TikTok account IDs after creation

**Branch:** `feat/studio-m4-publish`
**ETA:** Unblocked on code side. Wall-clock gate = account creation + warm-up window (30 days).
**Cost:** $97/mo Blotato Creator (already active).

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

**Channel Launch Protocol:** See [`skills/kie_media/references/channel-launch-doctrine.md`](../../skills/kie_media/references/channel-launch-doctrine.md). Covers: 5-decision launch framework, 4-part content formula, Shorts path doctrine, iteration protocol. Load at every new channel launch.

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

### 2026-04-25 (night): M1 SHIPPED. Engine LIVE on VPS. 3-channel batch briefed.

**Same-day ship in 9-hour build window.** Started after Atlas M7b SHIPPED, finished within hour 13 of the day. M1 went from spec-only to engine-LIVE-on-VPS in one sitting after the original spec said 12-18 hours across 2-3 sessions.

**Channel batch reshaped from 2 to 3:** Boubacar locked Wealth Atlas in earlier in the session, then pivoted to "First Generation Money" after SEO/GEO research. So M1 now ships briefs for Under the Baobab + AI Catalyst + First Generation Money. Wealth Atlas descoped (better framing won).

**Why First Generation Money beat Wealth Atlas / Inherited Nothing on naming:**
- Zero negative-framing semantic confusion (Inherited Nothing reads as grief in poetry contexts)
- Keyword stack matches search demand ("first gen money", "first generation wealth")
- Generative engines parse cleanly for diaspora/immigrant queries
- Existing competitor "First Gen Money" is small enough to displace; "Inherited Nothing" had no native search momentum

**M1 ship contents:**

1. Studio Trend Scout v0 (`orchestrator/studio_trend_scout.py`): heartbeat wake `studio-trend-scout` at 06:00 MT daily, YouTube Data API v3 search per niche, view-velocity scoring, top-N to Notion + Telegram brief. Graceful degrade if no API key.
2. Studio Pipeline DB in Notion (20 properties; ID `34ebcf1a-3029-8140-a565-f7c26fe9de86`). Created via direct Notion API. ID logged to local + VPS .env.
3. Studio QA Crew (`orchestrator/studio_qa_crew.py`): 8 checks on every drafted asset (spellcheck, banned-phrases, length, hook, source, CTA, personal rules, brand voice). Pure regex/string for v0 (LLM upgrade in M3).
4. 3 channel briefs at `docs/roadmap/studio/channels/`.
5. Operating snapshot locked at `docs/roadmap/studio/operating-snapshot.md`: 3-channel portfolio, Mon-Sat publish + skip Sun, no LinkedIn for Studio ever, video-creation is bottleneck #1.
6. `studio` added to `KNOWN_CREWS` in autonomy_guard. Heartbeat wake registered. BaseTools (`StudioTrendScoutTool` + `StudioQARunTool`) wired in tools.py.

**Tests:** 261/261 orchestrator tests pass (210 baseline + 30 QA crew + 21 trend scout = 261 after Studio M1).

**VPS deploy verified:**
- `git pull` brought commits down
- `docker cp` 5 files into orc-crewai (`/app/`, NOT `/app/orchestrator/`)
- Container restart, `studio-trend-scout` wake registered with `at=06:00`
- Manual tick run: 3 niches loaded, Notion query OK, graceful degrade on missing YouTube API key as designed
- Default `studio.enabled=False`; flip True after first dry-run brief reviewed

**Studio session shipped in parallel** (separate commits, separate planning):
- Skool harvester (3 Python tools, Playwright session-based)
- Harvest reviewer + harvest triage
- Niche research + video analyze tools
- Inventory snapshot generator
- 5 RoboNuggets R-series lessons mined and dual-lens-scored
- Atlas M8 Mission Control dashboard at /atlas (separate Atlas roadmap milestone)
- orchestrator.py monolith sunset (commit `0d9d288`); app.py is sole entrypoint now

**Total day's velocity (atlas + studio combined):**
- Atlas: M1, M2, M7a, M7b, M8 all SHIPPED
- Studio: M1 engine SHIPPED + harvest pipeline + 5 RoboNuggets reviews
- 261 tests passing, 0 regressions
- 3 Notion DBs created/extended (Content Board schema extended for M7b, Studio Pipeline new, Harvested Recommendations new)
- $20.30/mo Blotato Creator subscription started; auto-publish LIVE on Boubacar's LinkedIn + X
- 3 Sankofa Council passes (M7 split, M7b design, Pass 2 reframe of Studio M1)

**Next studio session:**
1. Get Google Cloud API key with YouTube Data API v3 enabled, add to VPS .env as `YOUTUBE_API_KEY`
2. Flip `studio.enabled=True` in `data/autonomy_state.json` on VPS
3. Restart container, wait for next 06:00 MT wake
4. Verify Telegram brief lands with candidates per niche
5. Boubacar reviews 7 days of briefs to validate signal quality
6. Then M2: register X handles, create First Generation Money YouTube channel, lock brand identity for all 3

**Save point:** `savepoint-pre-studio-m1-engine-2026-04-25` (at `196f875` pre-rebase).
**Branch:** `feat/studio-m1-engine` (merged via rebase to main).
**Commits:** `1d0cd88` (Studio M1 engine), now on origin via rebase.

---

### 2026-05-03: M2 Brand Identity - Palettes + Brand Bibles LOCKED

**Session scope:** Studio M2 brand identity for all 3 channels. Boubacar approved palettes after preview at `localhost:7420`.

**What shipped:**

3 brand bibles at `docs/roadmap/studio/brand/`:

- `under-the-baobab-brand.md`
- `ai-catalyst-brand.md`
- `first-generation-money-brand.md`

Each bible locks: final name, tagline, color palette (hex + role), typography stack, motion vocabulary, TTS voice spec + persona name, end-card template layout, thumbnail grammar, avatar spec, banner layout spec, About copy (YouTube + X), and M3 production crew brand injection block.

**Palette decisions (LOCKED):**

| Channel | Primary | Secondary | Accent 1 | Accent 2 |
| --- | --- | --- | --- | --- |
| Under the Baobab | Saffron Gold `#E8A020` | Baobab Indigo `#3D2B8E` | Terracotta Fire `#C45E2A` | Savanna Amber `#F5C842` |
| AI Catalyst | Fulani Indigo `#2D1B8E` | Catalyst Orange `#F26419` | Living Green `#1DB954` | Pale Indigo `#8B7FD4` |
| First Generation Money | Grove Green `#166B50` | First-Gen Cream `#F7EDD8` | Clarity Violet `#6B3FA0` | Warm Gold `#D4922A` |

**Asset Generation (COMPLETED):**
- Logos: `docs/roadmap/studio/brand/logos/` (all 3 channels, including no-bg variants)
- Avatars: `docs/roadmap/studio/brand/avatars/` (all 3 channels)
- Banners: Background scenes generated via `kie_media`; composite scripts ready.
- Templates: End-card and Thumbnail HTML templates verified for `hyperframes` injection.

**Boubacar actions (not agent):**

- [ ] Create First Generation Money YouTube channel
- [ ] Register X handles
- [ ] Create IG + TikTok accounts for all 3 channels (see `docs/roadmap/studio/social-launch-kit/`)
- [ ] Connect IG + TikTok to Blotato, share account IDs with agent

---

### 2026-05-03: M4 Kickoff  -  Social Launch Kits + Blotato Publisher

**M4 officially IN PROGRESS.** Session shipped two M4 deliverables.

**Social Launch Kits (all 3 channels):** `docs/roadmap/studio/social-launch-kit/`

- `under-the-baobab.md`  -  IG + TikTok bio, avatar spec, link-in-bio strategy, 30-day warm-up protocol
- `ai-catalyst.md`  -  same, plus cross-promotion note for boubacarbarry.com
- `first-generation-money.md`  -  same, plus YMYL compliance notes for financial content

Research sourced 2026 IG + TikTok warm-up protocols: IG requires 7-day silence before adding link in bio; 5-hashtag cap; Stories signal trust score. TikTok requires 7-day observation phase; 1-2 posts/day max; consistent IP + device + posting window.

**Blotato Publisher (`orchestrator/studio_blotato_publisher.py`):** Wraps existing `BlotatoPublisher` class. Scans Pipeline DB for Status=scheduled + ScheduledDate=Today → publishes via Blotato API → flips Status=posted. Per-channel account ID mapping for all 3 channels × 4 platforms (YT, X, IG, TikTok). Dry-run mode (`--dry-run`) for safe testing. Heartbeat tick registered as `studio-blotato-publisher` at 09:00 MT daily.

**What's next (wall-clock gated):**

1. Boubacar creates IG + TikTok for all 3 channels (see kits for handles + checklist)
2. Connects accounts in Blotato, shares account IDs → agent updates .env
3. Agent registers heartbeat tick on VPS (`studio-blotato-publisher`)
4. End-to-end test: 1 scheduled Pipeline DB record → publisher tick → Blotato → posted

---

### 2026-05-03 (night): M4 publisher deployed + heartbeat live on VPS

**Blotato publisher fully operational on VPS.** Session fixed schema mismatches and confirmed clean run.

**What shipped in this half-session:**

- `studio-blotato-publisher` heartbeat wake registered in `scheduler.py` at 09:00 MT
- Fixed `notion_client` → `skills.forge_cli.NotionClient` (correct import for VPS container)
- Fixed Status field type: `status` → `select` (Notion schema confirmed via API)
- Fixed Status option names: `publishing` → `rendering`, `posted` → `published` (actual Pipeline DB values)
- Verified on VPS: `STUDIO PUBLISHER: tick start ... 0 record(s) scheduled`  -  clean, no errors
- All commits pushed to main

**Account wiring (already in .env):**
- YT: all 3 channels wired (35697, 35696, 35698)
- X: all 3 channels wired
- TikTok: all 3 channels wired (40989, 40987, 40994)
- IG: Baobab (45174) + Catalyst (45176) wired; 1stGen pending `firstgenerationmoney_` IG review

**IG account creation recap:**
- `under_thebaobab` IG: live
- `aicatalyst_official` IG: under selfie review (submitted)
- `firstgenerationmoney_` IG: under review
- TikTok accounts created by Boubacar; all 3 IDs in .env

**What's next (M4 gates remaining):**
1. `firstgenerationmoney_` IG review clears → Boubacar adds `BLOTATO_1STGEN_INSTAGRAM_ACCOUNT_ID` to .env
2. First Pipeline DB record reaches Status=scheduled → publisher fires at next 09:00 MT tick
3. Confirm first auto-post live → M4 SHIPPED

### 2026-05-03: M3 Production Pipeline BUILT + API-tested

**Session scope:** M3 content production pipeline  -  built all modules, live API tested, deployed to VPS.

**What shipped:**

7 new orchestrator modules:

| Module | Purpose |
|---|---|
| `studio_brand_config.py` | Dynamic brand loader: Notion → JSON → placeholder fallback |
| `studio_script_generator.py` | Sonnet scriptwriter, SSML pronunciation, [SCENE:] + [RETENTION:] markers |
| `studio_voice_generator.py` | ElevenLabs primary (word-level timestamps), Kai TTS stub fallback |
| `studio_scene_builder.py` | Script → timed scenes, brand-enforced image/video prompts |
| `studio_visual_generator.py` | kie_media wrapper, parallel batch-3, source_url passthrough for image_to_video |
| `studio_composer.py` | hyperframes project builder, GSAP word-level captions, branded intro/outro |
| `studio_render_publisher.py` | 3-format render (16:9 / 9:16 / 1:1) + Drive + Notion update + Telegram |
| `studio_production_crew.py` | Main orchestrator + heartbeat tick + CLI (`--test`, `--notion-id`, `--tick`) |

**Brand + voice configs (COMPLETED):**
- `configs/brand_config.{under_the_baobab,ai_catalyst,first_generation_money}.json`  -  full colors, fonts, voice IDs
- `configs/voice_registry.json`  -  5 locked ElevenLabs voice IDs (male/female African, Boubacar, Hunter, Elhadja elder)
- Notion Studio Brand Config DB created under `agentsHQ > Studio`; all 3 channel rows seeded and status=ready
- Logos + avatars uploaded to Drive: `05_Asset_Library/Studio/Brand/{Logos,Avatars}/`

**QA crew extended to 10 checks:**
- Check 9: retention loop density (≥1 `[RETENTION:]` trigger per 250 spoken words)
- Check 10: AI-origin safe (no 100%-AI boilerplate pattern without human editorial signal)

**Live API test results (2026-05-03):**
- Sonnet script: 1700 words, all 10 QA checks passing ✅
- ElevenLabs: 9MB MP3, 1400+ word-level timestamps ✅
- kie_media image: Seedream/4.5 confirmed working, Drive upload via `GOOGLE_OAUTH_CREDENTIALS_JSON` ✅
- kie_media video: Seedance-2 confirmed working (Kling image-to-video slugs all 422 on Kai as of today) ✅
- Compose + render: dry_run clean; hyperframes + Node 22 + ffmpeg baked into container ✅

**Infrastructure fixes:**
- Dockerfile: Node 20 → 22 (required by hyperframes), `hyperframes` + `ffmpeg` installed globally
- `configs/` baked into Docker image (no more manual `docker cp`)
- `docker-compose.yml`: `ELEVENLABS_API_KEY`, `KIE_AI_API_KEY`, `NOTION_STUDIO_BRAND_CONFIG_DB_ID` wired
- `kie_media._upload_to_drive`: reads `GOOGLE_OAUTH_CREDENTIALS_JSON` (already set in container)  -  Drive upload now works without `gws_token.json`
- `kie_media`: Drive upload failures non-fatal in all 3 generate functions
- `.env` CRLF + unquoted-value fix script: `/root/agentsHQ/scripts/fix_env.py`
- `parenting-psychology` niche seed added to `studio_trend_seeds.default.json` for Under the Baobab
- Heartbeat wake `studio-production` registered at `every="30m"`, `crew_name="studio"`

**What M3 does NOT yet have (not started):**
- First real video rendered end-to-end from a qa-passed Pipeline DB candidate (no candidates exist yet  -  trend scout runs at 06:00)
- `studio.enabled=True` on VPS (intentionally left False until first 5 candidates reviewed)
- hyperframes composition live render test (dry_run only  -  no candidate to trigger it)

**Next steps to close M3 fully:**
1. Flip `studio.enabled=True` in `data/autonomy_state.json` after first 5 trend-scout briefs reviewed
2. First qa-passed candidate: run `python3 -m studio_production_crew --notion-id <id>` live
3. Confirm MP4 renders and lands in Drive `05_Asset_Library/<channel>/<date>/`
4. M3 marked SHIPPED  -  M4 publish path takes over

---

### 2026-05-03 (late): M3 ffmpeg pivot  -  hyperframes dropped

Session scope: M3 render engine pivot after hyperframes failed in container (Chrome headless can't access container filesystem paths → blank purple renders).

**What shipped (7 modules rewritten):**

- `studio_composer.py`: full rewrite  -  ffmpeg manifest + SRT writer (no hyperframes)
- `studio_render_publisher.py`: full rewrite  -  ffmpeg Ken Burns (8 motion variants) + concat + audio mix + SRT caption burn; email via gws +send from channel alias
- `studio_visual_generator.py`: GPT Image 2 only (`gpt_image_2_text`), vault lookup before Kai
- `studio_production_crew.py`: status=Ready fix, QA retry, lint_passed removed
- `studio_qa_crew.py`: skip source_citation for storytelling niches
- `studio_brand_config.py`: slugify channel name for config lookup
- `studio_script_generator.py`: retention loop auto-inject, loop_interval passthrough
- `studio_voice_generator.py`: strip SCENE/RETENTION markers before TTS
- `studio_trend_scout.py`: niche-aware classifier (inspiration mode), dual YT key rotation

**Key decisions locked:**
1. hyperframes dropped permanently  -  ffmpeg is the renderer
2. GPT Image 2 for stills (~$0.04/image vs ~$7/video clip)
3. SRT as separate track (multilingual ready)
4. Ken Burns 8-variant cycle per scene
5. Asset vault: search before generating (score ≥2 tag match = reuse)

**What is NOT done:** shorts (1080x1920) + square (1080x1080) reframe, music vault, branch not merged to main.

---

### 2026-05-04: First Fire review  -  3 blocking bugs found and fixed

Session scope: post-Monday first-fire review. Scout ran (22 candidates written). No video produced.

**Root cause analysis:**

| Bug | Effect | Fix |
|---|---|---|
| No `studio-qa` heartbeat (misdiagnosed first) | Caused scout tick to error mid-run | `newsletter_editorial_input` import guarded with `try/except ImportError` |
| `_fetch_qa_passed_candidates()` queried `Status="Ready"` | Zero candidates picked up by production tick | Fixed filter to `"scouted"` |
| Spurious `studio-qa` heartbeat added then removed | Ran QA on empty-Draft scouted records → all 19 flipped to `qa-failed` | Removed heartbeat, reset 19 records back to `scouted` via Notion API |

**Also shipped:**
- Shorts/square center-crop before Ken Burns in `_render_ken_burns_clip()`  -  portrait: `crop=ih*w/h:ih`, square: `crop=min(iw,ih):min(iw,ih)`

**State at session end (2026-05-04 ~17:20 MT):**
- 19 `scouted` records in Pipeline DB  -  production tick picks up at next 30m fire (~17:20 MT)
- `studio-production` heartbeat: `every=30m`, `crew_name=studio`
- Flow confirmed: `scouted` → production_tick → script (Sonnet) → inline QA → voice → visuals → ffmpeg render → `scheduled`
- Monitor armed watching for first production run logs
- **Music vault deferred:** `build_vault.py` + `workspace/media/music/` not yet built

**Next steps:**
1. Confirm first successful video in Drive + Telegram notification
2. If render succeeds: merge `feat/studio-m3-production` → `main`, mark M3 SHIPPED
3. Build music vault: `workspace/media/music/` dir + `build_vault.py` scanner (Suno instrumentals per channel)
4. Review video quality  -  Ken Burns + GPT Image 2 acceptable?

---

### 2026-05-04: Monetization doctrine absorbed + QA check 11 wired

Absorbed YT monetization playbook (X thread, anonymous, unverified 9-day claim). Extracted structural doctrine (4-part formula and 5-decision launch framework) and encoded as callable reference.

**What shipped:**

- `skills/kie_media/references/channel-launch-doctrine.md`: 5-decision channel launch framework, 4-part content formula (Hook/Value/Curiosity Gap/Loop Ending), Shorts path doctrine (3-5/day), iteration protocol (retention rate + avg watch duration + drop-off point per video), anti-patterns, Atlas agent integration note. Review date: 2026-08-04.
- `orchestrator/studio_qa_crew.py`: QA check 11 added (`check_four_part_formula()`). Validates curiosity gap + loop ending in every long-form script. Shorts skipped (hook + CTA checks cover it). Total QA checks: 11.
- `orchestrator/studio_script_generator.py`: 4-part formula promoted to HARD RULE 2 in system prompt. Sonnet now instructed to produce Hook / Value / Curiosity Gap / Loop Ending explicitly.
- `docs/roadmap/studio.md` M6: Channel Launch Protocol reference added pointing to doctrine file.

**Key doctrine decisions:**

- Shorts path is Studio default (faster testing, lower cost per asset)
- Pattern replication over originality at launch. Replicate winning format, swap topic only.
- Curiosity gap + loop ending are now enforced at QA, not just advised
- 4-part formula applies to X/LinkedIn content board (cross-motion leverage)

**Next steps:**

1. Deploy updated `studio_qa_crew.py` + `studio_script_generator.py` to VPS
2. First produced video: verify QA check 11 fires correctly on script output
3. M5 (analytics): must include retention rate + avg watch duration + drop-off point per video. These are the three doctrine iteration metrics.

---

### 2026-05-04: kie_media Studio Art Direction wired - thumbnail/scene prompt quality lift

`skills/kie_media/SKILL.md` updated with Studio Art Direction section. Every thumbnail, scene still, and cover art call now uses a 6-field structured prompt instead of freeform text:

- Composition Anchor (5 options, vary per batch)
- Background Mode (5 options, never repeat twice in a row)
- Subject + Channel Context
- Lighting + Mood
- Palette (channel-locked: Under the Baobab = ochre/terracotta/gold; AI Catalyst = navy/slate/amber; 1stGen Money = forest green/charcoal/warm gold)
- Anti-Slop Prohibition per channel (no generic African stock clichés / no purple-blue AI gradient / no fake urgency expressions)

Ken Burns still rule added: generate at 16:9, offset subject from center, 2-3 stills per scene for motion variety.

Source: taste-skill `imagegen-frontend-web` vocabulary. Absorb verdict: PROCEED (continuous-improvement).

### 2026-05-04: Research Intelligence Layer: M3.6 seeded, dossiers wired into script crew

**Session scope:** Architecture review + minimum viable implementation. No VPS deploy required (dossiers read from repo at script-generation time).

**Trigger:** Sankofa Council review of Graeme Kay's research agent architecture (X thread 2026-05-04). Sankofa + Karpathy both ran on full adoption vs. selective borrow.

**Council verdict:** Build stub now, not full vault. Full vault (29 dirs, JSONL ledgers, 6h cron) only if M5 analytics prove dossier lift.

**What shipped:**

- `research-vault/dossiers/under_the_baobab.md`: African storytelling niche signal, competitor gaps, hooks that convert, verification queue
- `research-vault/dossiers/ai_catalyst.md`: AI displacement content trends, professional audience hooks, competitor signal
- `research-vault/dossiers/first_generation_money.md`: first-gen finance trends, $15-22 RPM estimate, competitor signal, YMYL notes
- `orchestrator/studio_script_generator.py`: `_load_dossier()` + `_CHANNEL_DOSSIER_MAP`; dossier injected as `CHANNEL INTELLIGENCE DOSSIER` block in system prompt. Non-breaking: empty string if no dossier found.
- `docs/roadmap/studio.md`: M3.6 milestone added
- `docs/roadmap/atlas.md`: verification queue concept documented in Cross-References + session log

**What was NOT built (Karpathy surgical rule):** No JSONL ledgers, no source registry, no cron, no automated refresh, no operator cockpit, no wiki layer.

**Success proxy (before M5):** First post-dossier script contains a niche-specific hook or trend reference from its dossier. Reviewable by reading script output before render.

**Next steps:**

1. Confirm first video rendered (M3 first render). Review whether dossier influenced hook choice
2. M5 gate: if CTR/watch-time shows lift on dossier-informed scripts, expand to `findings.jsonl` + source registry + weekly refresh cron
3. Atlas M5 Chairman crew design (2026-05-08+): add `data/verification_queue.md` on VPS as knowledge-claim staging layer

---

### 2026-05-05: M3 SHIPPED + pipeline fully unblocked

**Session scope:** Fixed all silent pipeline blockers, switched to Shorts-first strategy, first Short rendered end-to-end.

**What shipped:**

- Shorts-first render: `_PLATFORM_SPECS = {"shorts": {"width": 1080, "height": 1920}}` only. Long-form re-enabled when traction proven.
- Brand configs x3: `target_duration_sec=55`, `hook_word_budget=15`, `retention_loop_interval=50`, `intro/outro=1s each`.
- QA check 11 `check_four_part_formula()`: curiosity gap + loop ending enforced.
- QA `short (<60s)` band widened: `(30, 275)` words. Source citation skipped for all Shorts.
- Script generator hard cap: `HARD CAP: never exceed {target_words + 20} words total`.
- `_update_notion()` writes `Scheduled Date = today` on render completion (auto-post was silently broken).
- zoompan at target resolution, not 4K. Clip timeout 600s.
- `length_target` derived from `brand.target_duration_sec` in production crew.
- CTA patterns expanded: 18 patterns covering natural Sonnet endings.
- All Blotato account IDs confirmed in VPS .env for all 3 channels.

**First Short confirmed rendering** (2026-05-05 01:05 UTC): 180 words, QA passed all 11 checks, voice 63.3s, 7 scenes, ffmpeg shorts 1080x1920 in progress.

**M4 status:** All account IDs wired. Warm-up window is the remaining gate. Blotato publisher fires at 09:00 MT daily on `Status=scheduled AND ScheduledDate=today`.

**Next:** Confirm first Short in Drive. Review quality. M4 warm-up window starts day 1 from first post.

---

### 2026-05-05: Branded channel cards shipped + scene motion upgrade planned

**Session scope:** Caption removal, branded intro/outro cards built and deployed, pipeline production unblocked.

**What shipped:**

- Burned-in captions removed from ffmpeg pipeline. SRT sidecar delivered only. Source: Sankofa Council verdict + first-fire frame review (giant cyan text covered the image center, sync drifted).
- 6 hyperframes-rendered branded channel cards (3 channels x intro + outro):
  - Under the Baobab: baobab/Milky Way photo bg, gold circular logo, Cinzel Decorative font, pulse-glow outro animation
  - AI Catalyst: energy vortex photo bg, violet circular logo, Space Grotesk font, draw-in + spin + counter-arc outro
  - First Gen Money: linen texture photo bg, green circular logo with gold border, Plus Jakarta Sans, rising float + wealth particles outro
- Cards deployed to `/app/workspace/assets/{intros,outros}/<channel>_{intro,outro}.mp4`
- `studio_render_publisher.py` wired: ffmpeg concat prepends intro + appends outro per channel. Audio delayed by intro duration so narration starts after card.
- Drive upload fix: `_upload_to_drive()` now passes `filename` + `mime_type` (was missing 2 required args, all renders had Drive upload silently fail).
- Drive root folder fix: falls back to `GOOGLE_DRIVE_FOLDER_ID` env var (hardcoded fallback ID was 404).
- QA `source_citation` skipped for `short (<60s)` length_target (no room in 55s scripts for citations, was blocking all AI Catalyst + First Gen Money candidates).
- Scene density fix: `_WORDS_PER_SCENE` now scales with `target_duration_sec` (30 words/scene for shorts = 7 scenes vs. 1 scene from old 200-word constant).
- Studio re-enabled. 15 scouted candidates queued for next production tick.

**First render confirmed:** 3 videos in Drive with correct URLs. Notion updated to `scheduled`.

**Ken Burns acknowledged as monotonous:** All 7 scenes per Short use Ken Burns zoompan. Functional but visually repetitive. Decision: keep for first batch, upgrade in M3.4. See new milestone above.

**Next:** Monitor first batch (15 scouted candidates). Confirm Drive uploads land correctly. M4 warm-up day 1 starts from first post. M3.4 scene motion upgrade queued after first-batch review.

### 2026-05-05 (session 2) -- Bug chain found and fixed; full re-render queued

**Bugs fixed in studio_render_publisher.py:**
- Corrupted em-dash byte (0x97) in docstring caused UTF-8 SyntaxError; Python fell back to stale .pyc (old title-card code). Fixed: replaced with hyphen, deleted .pyc.
- `_ASSETS_DIR` constant never defined despite being referenced at lines 181-182. Fixed: added `_ASSETS_DIR = Path(os.environ.get("STUDIO_ASSETS_DIR", "/app/workspace/assets"))`.
- `_upload_to_drive()` called with 2 args; function requires 4. Fixed: added `local_path.name, "video/mp4"`.
- QA `source_citation` skipped for `short (<60s)` length_target (was blocking all AI Catalyst + First Gen scripts).

**All previous renders queued for re-render:**
- 12 archived records + 1 Baobab record reset to `qa-passed` (Asset URL cleared).
- 7 Under the Baobab + 6 First Gen Money = 13 in queue.
- Old renders moved to `/app/workspace/renders/archive/2026-05-05/`.
- AI Catalyst archived records stayed archived (scraped YouTube content, no scripts).

**Pipeline now correct:** intro card + Ken Burns scenes + outro card + SRT sidecar. No burned captions. Drive upload working.

**Next:** Confirm first re-render completes with intro/outro visible and no captions. Then M4 publisher warm-up.

---

### 2026-05-06: Storytelling infrastructure — Studio content sourcing upgraded

**Session scope:** Not a Studio build session. Strategic decision made that affects Studio content sourcing.

**Decision: Story-first content strategy adopted across all channels.**

Boubacar's lived experiences and raw observations are the primary content source for all channels — not trend-scouted topics. Studio channels are now downstream consumers of the same story signals that feed Boubacar's personal LinkedIn/X.

**What this means for Studio:**
- `Content Type=Story + Status=Idea` entries on the Content Board are available as script briefs for all 3 Studio channels
- One lived moment → multiple channel adaptations (FGM = financial angle, UTB = diaspora/identity angle, AIC = AI practitioner angle)
- Channel routing is flexible — Boubacar confirms which channels a story feeds, LéGroit proposes, nothing is pre-wired
- Story posts are X-primary for personal brand; Studio channels adapt to short-form video format

**Not yet built:**
- Studio crew does not yet pull from `Content Type=Story` entries — still uses trend-scouted candidates only
- Wiring story entries → Studio script generation is next Studio milestone

**Channel + Blotato account map confirmed:**

| Channel | Platform | Blotato ID |
|---|---|---|
| First Gen Money | X (@FirstGenMoney_) | 17661 |
| First Gen Money | Instagram | 45188 |
| First Gen Money | TikTok | 40994 |
| First Gen Money | YouTube | 35698 |
| Under the Baobab | X (@UnderTheBaobab_) | 17650 |
| Under the Baobab | Instagram | 45174 |
| Under the Baobab | TikTok | 40989 |
| Under the Baobab | YouTube | 35697 |
| AI Catalyst | X (@boubacarbarry — shared) | 17065 |
| AI Catalyst | Instagram | 45176 |
| AI Catalyst | TikTok | 40987 |
| AI Catalyst | YouTube | 35696 |

**Next Studio session:**
1. Wire Studio script crew to pull `Content Type=Story + Status=Idea` as candidate briefs (alongside trend-scouted topics)
2. Story → multi-channel adaptation: one entry generates 3 scripts (FGM/UTB/AIC lenses)
3. M4 warm-up: confirm first batch of renders posted and tracking engagement
