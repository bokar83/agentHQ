# Studio M1: Engine First, Two-Channel Batch Second

**Codename:** studio
**Milestone:** M1
**Status:** in-progress
**Started:** 2026-04-25
**Ship target:** engine v0 + channel briefs locked by 2026-05-09
**Owner:** Boubacar Barry

**One-line:** ship the trend-scout + Notion pipeline + QA crew engine first; two channels (Sankofa Stories, AI Displacement) ride downstream as M2-M3 dogfooding.

---

## Why this exists

Two passes of the Sankofa Council reframed M1 from "lock one niche" to "ship the engine, then run two channels through it." The corrected design treats studio as a portfolio engine, not a single-channel build. The channels are the engine's dogfooding.

The build airplane comes first, then test flights.

---

## Scope: what M1 ships

### 1. Studio Trend Scout v0 (the engine)

**What it does.** Scans YouTube, TikTok, and Instagram for viral patterns within configured niches. Identifies trends, hooks, formats, and content shapes that are working in the last 7 to 30 days. Outputs candidates to a Notion Studio Pipeline DB.

**Inputs per run.**
- Niche tag (e.g. "african-folktales-children", "ai-career-displacement")
- Platform set (YouTube long, YouTube Shorts, TikTok, Instagram Reels)
- Time window (default 7d, optional 30d)
- Top-N (default 20 candidates per run)

**Outputs per run.**
- Notion record per candidate with: source URL, title, thumbnail, view count, posting velocity, hook structure, format pattern, suggested clone-with-twist for our brand.
- Daily brief to Telegram with top 5 candidates per active niche.
- Cost ledger entry per run (tokens + Firecrawl credits + Kai credits if used).

**Pattern source.** Adapted from `clone-scout` skill (which scouts websites). The same dual-signal logic (proven traffic + rising buzz) applies to video content.

**Where the code lives.** `orchestrator/studio_trend_scout.py`, mirrored in `skills/studio-trend-scout/`. New module. Reuses `tools.py` Firecrawl bundle and the existing scheduler heartbeat.

**Heartbeat wake.** New wake `studio_trend_scout_daily` fires once per day at 06:00 MT, scans all configured active niches, posts daily brief to Telegram. Uses the Atlas heartbeat substrate (no new infra).

### 2. Studio Pipeline DB (Notion)

A new Notion database that holds: niches (configured), candidates (scout output), drafts (next phase), assets (rendered videos), and publishes (post records). Modeled on the existing Content Board schema, simplified.

**Schema (rough cut, finalized in build):**

| Property | Type | Purpose |
|---|---|---|
| Title | title | Candidate hook or asset name |
| Niche | select | sankofa-stories, ai-displacement, etc. |
| Status | select | scouted, queued, drafted, qa-pending, qa-failed, qa-passed, scheduled, posted, archived |
| Source URL | url | Original video being trend-cloned |
| Source channel | text | Original channel name |
| Source views | number | Views on the source at scout time |
| Hook | rich_text | One-line hook (engine output) |
| Twist | rich_text | How we make it ours (engine output) |
| Format | select | tale, explainer, listicle, reaction, vlog, animation |
| Length target | select | short (<60s), medium (60-180s), long (3-15m) |
| Asset URL | url | Drive link to rendered video |
| Platform | multi_select | youtube-long, youtube-shorts, tiktok, instagram-reels |
| Scheduled at | date | Post time |
| Posted URL | url | Published link |
| QA notes | rich_text | Failed checks, agent flags |
| Cost | number | Token + media cost for this asset |

**DB ID logged to env on creation.** `NOTION_STUDIO_PIPELINE_DB_ID`. No bare ID strings in code.

### 3. Quality Review Crew (the QA layer)

Multi-pass checker that runs on every drafted asset before it is queued for render. The "impeccable QA" bar from Boubacar in Pass 2.

**Checks (M1 v0):**
1. Spellcheck and grammar pass (Sonnet)
2. Named-entity validation (place names, person names, language names cross-checked against a maintained dictionary)
3. Source-citation present if claim is factual
4. No banned-phrase patterns (slurs, platform-banned terms, copyrighted song lyrics, brand trademarks without context)
5. Length within target band (e.g. Shorts must be 60 to 90 seconds)
6. Hook in first 3 seconds
7. CTA present and platform-appropriate
8. No coffee, alcohol, or beverage props in any scene description (Boubacar values rule, applies to Sankofa even though the channel is faceless because the visual brand is associated with him eventually)

**Failures route.** If any check fails, the record flips Status=qa-failed, agent posts a Telegram message with the failure reason, and the asset waits for either an automated retry (e.g. spellcheck fix) or Boubacar's review.

**Pass 1 v0 limitation.** Cultural-mismatch detection (kente over a Bamileke tale, Akan symbol over a Wolof story) is NOT in M1. Slots into M3 as "regional motif library + image-generator prompt enforcement." Workaround in M1: visual generation runs against a single conservative motif set per niche; cultural-tag mismatch is a Boubacar-review item, not an agent-block item.

### 4. Two channel briefs scaffolded (not built)

M1 ships the briefs only, not the channels. The briefs define the niche, brand surface, voice strategy, posting cadence, and revenue model for each. M2 builds the brand identity and creates the channel.

**Channel A: Sankofa Stories** (working name; final lock in M2)
- Niche: African folktales, retellings + original tales, mixing cultures permitted, entertainment-first.
- Audience: African children + diaspora children, parents, Black History Month + bedtime story buyers.
- Format: 8 to 12 min animated tales (long), 60 to 90 sec hook clips (Shorts/Reels/TikTok).
- Voice: faceless, single recurring TTS narrator persona (working concept "the griot under the baobab").
- Languages: English primary, French secondary (M2 decision: launch EN-only, add FR after channel A passes 1k subs).
- Cadence: 2 long/week + 4 shorts/week.
- Revenue: AdSense + sponsor (African diaspora brands) + affiliate (children's books, audiobooks, African home decor) + later merch (Adinkra, kente, baobab prints) + later Spotify podcast feed.
- Brand status: brand-new YouTube channel + IG + TikTok + Spotify podcast. Not riding on any existing channel.

**Channel B: AI Catalyst (reuse existing)** (working name uses existing channel; final lock in M2)
- Niche: AI displacement education for working professionals, "how to thrive alongside AI," HR/workforce transition lens.
- Audience: 30-55 year old professionals scared about AI taking their jobs, especially in HR, ops, finance, marketing, customer service.
- Format: 8 to 12 min explainers (long), 60 sec data-reveal Shorts. Mostly screen + animated diagrams via hyperframes.
- Voice: openly Boubacar Barry, "Director of HR with global experience" framing, faceless visual format (no on-camera).
- Branding: links to boubacarbarry.com (NOT catalystworks.consulting). Pseudonymity dropped per Council Pass 2.
- Languages: English only.
- Cadence: 2 long/week + 3 shorts/week.
- Revenue: AdSense + sponsor (AI tools, course platforms, career tools, LinkedIn Premium) + affiliate (AI tool subscriptions, course platforms, resume tools) + owned products downstream (Tier 1 toolkit $47-97, Tier 2 course $197-297 per existing AI Displacement strategy memo).
- Brand status: reuses existing AI Catalyst YouTube channel as testbed. New IG + TikTok created.

**Why these two and not Wealth Atlas or Studio Logs in M1.**
- Wealth Atlas: deferred. Adds when we have 14 days of trend-scout data to validate the first-gen framing has organic search demand. Channel 3 candidate, queued.
- Studio Logs / Agentic Diary: deferred. Ships when the studio system has 30 days of activity worth showing. Channel 4 candidate, queued.

### 5. Time budget tracking

A simple Notion property in the Studio Pipeline DB or a separate small table that logs Boubacar's actual studio time per week. M1 ships the logging hook, M2-M5 use the data.

**Build phase (M1-M3):** acceptable budget up to 2 hr/day.
**Steady state (M4 onward):** target 3 hr/week.

**Kill rule:** if measured weekly studio time exceeds 4 hours for 2 consecutive weeks AFTER M4 ships, descope the studio to one channel until the system is back under budget.

---

## What M1 does NOT ship

- The two channels themselves (M2 brand identity, M3 production pipeline)
- Auto-publish to platforms (M4, depends on Atlas M7 + Blotato Creator subscription)
- Performance dashboards (M5, needs ≥10 published assets per channel)
- Monetization wiring (M6, needs YPP eligibility on first channel)
- Wealth Atlas, Studio Logs, or any third channel (M7 onward, after data)
- Regional motif library (slots into M3)
- Pronunciation dictionary (slots into M3)

---

## Done definition for M1

M1 is shipped when ALL of these are true:

1. Studio Trend Scout v0 runs daily, scans both configured niches (sankofa-stories, ai-displacement), posts a daily brief to Telegram with top 5 candidates per niche.
2. Studio Pipeline DB exists in Notion with the schema above. DB ID logged to VPS .env as `NOTION_STUDIO_PIPELINE_DB_ID`.
3. Quality Review Crew runs on a sample asset (Boubacar feeds it 1 sample script), all 8 checks fire, failures route to Telegram, passes route to qa-passed status.
4. Both channel briefs (Sankofa Stories, AI Catalyst) are committed to this doc and reviewed.
5. Time-tracking property exists in Studio Pipeline DB, logged for the M1 build session itself as the first entry.
6. M2 (brand identity) is the explicit next milestone, with trigger gate "M1 shipped + Boubacar reviews 14 days of trend-scout daily briefs and confirms the candidates feel right."

---

## Build sequence

| Order | Work | Owner | Hours est. (build budget) |
|---|---|---|---|
| 1 | Notion Studio Pipeline DB scaffolded with schema | agent | 1h |
| 2 | Trend Scout v0 in `orchestrator/studio_trend_scout.py` (Firecrawl + Sonnet pattern-match) | agent | 4-6h |
| 3 | Heartbeat wake `studio_trend_scout_daily` registered | agent | 30min |
| 4 | Telegram daily brief formatter (mirrors `publish_brief.py` pattern) | agent | 1-2h |
| 5 | Quality Review Crew in `orchestrator/studio_qa_crew.py` (8 checks) | agent | 3-4h |
| 6 | Tests for trend scout + QA crew | agent | 2-3h |
| 7 | Boubacar reviews 1 sample run end-to-end | Boubacar | 30min |
| 8 | Three-way nsync, M1 marked shipped, session log | agent | 30min |

Total: 12-18 build hours across 2-3 sessions. Boubacar's hands-on time: ~1 hour total during M1 build.

---

## Cost ceiling for M1 build

| Cost source | Estimate |
|---|---|
| Anthropic tokens (trend scout + QA crew development) | $5-15 |
| Firecrawl credits (scraping YouTube/TikTok/IG metadata) | already in plan; 0/3000 until May 14, flag |
| Kai credits (no media generation in M1) | $0 |
| Blotato Creator subscription | NOT in M1; defers to M4 |
| **M1 build total** | **<$20** |

**Firecrawl flag.** Account is at 0/3000 credits until 2026-05-14 (per existing memory). Trend scout v0 must be built such that it works inside this constraint. Options: (a) wait until 2026-05-14 to ship the live scout; (b) ship the scout against YouTube Data API + TikTok scraping fallback that does not need Firecrawl; (c) ship it dormant against Firecrawl, activate post-2026-05-14. Decision deferred to build session, default to (b).

---

## Risks and kill rules

| Risk | Detection | Kill rule |
|---|---|---|
| Trend scout produces low-signal candidates that all look the same | Boubacar reviews 7 daily briefs in week 1, flags >50% "this is noise" | Refactor pattern-match prompt; if still noisy week 2, descope scout to 3 specific platforms with hand-picked seed accounts |
| Time budget blows past 2 hr/day during build | Weekly self-audit in Notion time-tracking | If build phase exceeds 4 weeks, hard-stop and descope to a single channel manual pipeline until time budget recovers |
| YouTube enforcement flags the AI Catalyst test channel during M2 launch | Watch for any "channel review" notification | Pivot AI Catalyst to brand-new account; archive the existing channel as inactive |
| Sankofa Stories cultural pushback | Any 1+ comment thread accusing misrepresentation | Boubacar reviews and either responds publicly, edits the asset, or pulls the asset; agent flags but does not auto-pull |
| Firecrawl credits not back by May 14 | Check 2026-05-14 | Hot-swap to YouTube Data API + native scrapers; cost rises by ~$10-20/mo |

---

## Open decisions deferred to build session

1. Channel codenames (Sankofa Stories vs Tales of the Baobab vs Griot's Lantern; AI Catalyst stays as is or rebrands).
2. Whether AI Catalyst is the existing channel or a new one (depends on what Boubacar finds when he checks the existing channel state).
3. TTS voice provider for Sankofa Stories (ElevenLabs character voice vs Kai TTS via kie_media). Default ElevenLabs.
4. Whether Studio Pipeline DB lives in The Forge 2.0 or in a new top-level Studio workspace.
5. Whether the trend scout pulls from boubacarbarry.com personal-site analytics for AI Catalyst topic ideas (only if site has GA4 + topic data).

---

## Cross-references

- `docs/roadmap/studio.md` (parent roadmap; this M1 doc supersedes the original M1-M2 description in the roadmap header)
- `docs/roadmap/atlas.md` (sister roadmap; Atlas M7 is the publish dependency for studio M4)
- `skills/clone-scout/SKILL.md` (pattern adapted for trend scout)
- `skills/kie_media/SKILL.md` (M3 production pipeline)
- `skills/hyperframes/SKILL.md` (M3 production pipeline)
- `orchestrator/heartbeat.py` (M1 wake registration)
- `orchestrator/publish_brief.py` (M1 daily brief formatter pattern)
- Memory: `project_ai_displacement_property.md` (Channel B strategy seed)
- Memory: `project_clone_factory_defaults.md` (bilingual default applies to Channel A French expansion)
- Memory: `feedback_no_alcohol_or_coffee_imagery.md` (QA crew check 8)
- Memory: `feedback_always_cite_sources.md` (QA crew check 3)
- Memory: `feedback_n8n_workflow_protocol.md` (if any n8n workflow ships in M3)

---

## Council outputs that shaped this doc

**Pass 1 (single-channel niche selection):** rejected. Forced the path-vs-candidate question.
**Pass 2 (corrected frame, portfolio engine):** accepted. Surfaced "engine first, channels second" as the M1 shape.

Both council passes are referenced in the studio.md session log.
