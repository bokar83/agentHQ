# Studio Channel Expansion: AIC-FR-Africa + Mande-Folk + Lofi-African

**Status:** SPEC (awaiting Boubacar approval).
**Date:** 2026-05-16.
**Author:** agentsHQ (this session).
**Trigger:** absorb-session 2026-05-15/16 surfaced 3 channel candidates that fit Studio infra. Boubacar approved all 3 to spec. Companion deep-review of all session URLs through the layoff-wave-prep lens is running in parallel and will land separately.

## Strategic frame (read this first)

A lay-off wave is anticipated in July-August 2026 driven by AI displacement narratives and broader economy. Knowledge workers will search en masse for: upskilling in AI, career transition help, new-economy preparation, starting a new business. Studio's existing channels (UTB anthropology / AIC AI+HR / 1stGen money) are positioned for adjacent audiences but not for this acute search demand at scale.

The 3 channels in this spec are deliberately faceless, low-Boubacar-time, and Studio-infra-native so they can be warmed up + aged + indexed BEFORE the July search wave hits. Conversion path is the same as existing channels: feed audience into SW website-build leads + CW consulting leads + 1stGen money advice + future product offers.

**Hard rule for all 3:** automation first. If a channel needs more than ~30min of Boubacar-time per week to maintain, it gets killed before launch, not after.

---

## Channel 1: AIC-FR-Africa (AI tools and AI news in French for African ICP)

### One-line thesis

There is nobody producing structured French-language AI tools and AI news content targeted at Francophone African operators today. Boubacar (Guinean operator with French fluency and existing Guinea+Conakry coding in personal brand) sits alone in this lane. The Studio Trend Scout already pulls Anthropic/OpenAI/Google release data; routing it through an AI persona narrating in French at an African audience is a 0-to-1 lane.

### ICP

- Francophone African knowledge workers (Senegal, Cote d'Ivoire, Mali, Guinea, Burkina, DRC) curious about AI tools but locked out of mostly-English explainer content
- Francophone diaspora in France, Belgium, Canada, Quebec who are AI-curious but want content from a French-African voice rather than a Paris-French or Quebecois-French voice
- Bonus tier: small-business operators in Francophone Africa looking for practical AI use cases (where this can later spawn an AI-tools-for-African-SMB sub-channel)

### Production cadence

- 3 to 5 short-form (60-90s) per week + 1 long-form (8-12min) per week
- Long-form covers a weekly AI-tools-or-news theme
- Shorts cut down from the long-form into 3-5 hook-driven clips per week
- All faceless via AI persona (Higgsfield or kie_media generated avatar, French ElevenLabs voice)

### Voice and persona

- Single recurring AI persona named in-channel (e.g. "Salif" or "Aminata" - placeholder pending Boubacar pick)
- Persona is HONEST about being AI: opening intro line every video establishes "AI assistant, here to translate the latest AI tools into something useful for you"
- Boubacar-narrative undertone (Guinean operator, first-gen, builds things) but persona is the named host
- Brand-spine isolation: this is NOT Boubacar's personal voice; this is an AIC sub-brand. The "I" in scripts is the persona, not Boubacar.

### Studio infra fit

- kie_media: avatar generation, image gen, video gen (Higgsfield + GPT Image 2 + Seedance routes)
- ElevenLabs voice registry: French voice clone for persona
- HyperFrames: short composition w/ overlays, captions, hooks
- scene-segmenter: script to beat structure
- ffmpeg compose: final render
- Blotato: cross-platform fan-out (YouTube + TikTok + Reels + LinkedIn-FR + Threads)
- studio_brand_config: new brand entry needed for AIC-FR-Africa (color palette, font, intro/outro plate, channel-name graphics) - small new file
- studio_trend_scout: needs a new niche config entry for Francophone-Africa-AI-tools

Net infra additions: 1 brand_config entry + 1 trend_scout niche config + 1 French voice in ElevenLabs registry + 1 channel handle creation across platforms. No new orchestrator module.

### Monetization stack

- YouTube AdSense (eligible after subs + watch-hours threshold; Francophone-Africa CPM is lower than US but the volume potential is real)
- Lead-magnet to SW website-build: each long-form ends with "if you run a French-African business and want a website that does this, here's our 5-min audit form" (signal-works-pitch-reel style)
- Future: paid AI-tools-for-African-SMB Notion guide ($19-$47) once audience hits ~5k subs

### First-90d KPIs

- Channel published, branded, first 30 shorts + 12 long-form shipped
- ~500-1500 subs on YouTube (organic Francophone-Africa AI niche is underserved, this is realistic)
- 1-3 lead-magnet form fills per month by day 90
- Boubacar time: under 30min/week reviewing scripts and approving publishes (Studio production tick handles the rest)

### AdamDelDuca anti-pattern self-check (7 patterns)

1. Speech-clip channels (rights/RPM weak): NO. Original AI persona + original scripts. Clean.
2. Kids-yoga (brutal RPM): NO. Adult B2B-adjacent audience.
3. Generic personal finance (too broad): NO. AI-tools vertical, not finance.
4. War/news (advertiser flight + accuracy load): PARTIAL RISK. AI-NEWS angle could drift into politics-of-AI or Africa-policy-of-AI. Mitigation: stay tools-focused; treat news only as "what shipped this week + how to use it". No commentary on African political AI policy.
5. High-production documentaries (capital-heavy): NO. Studio faceless infra is exactly the low-prod path.
6. Police/dashcam: NO.
7. Lofi music (saturated): NO. AI-tools vertical.

Net: 1 partial risk (#4 if news angle creeps), 6 clean. Mitigation written into script-generator prompt before launch.

### Brand-spine isolation

- New channel handle (not under any existing UTB/AIC/1stGen account)
- New brand_config entry in `studio_brand_config.py` distinct color palette + intro/outro plate
- Cross-promotion from existing channels only AFTER first 30 days and only if AIC-FR-Africa hits early traction (avoid burning UTB/AIC/1stGen on an unproven cousin)
- Boubacar personal accounts: zero direct cross-post (separate audience, separate trust posture)

### Launch checklist (handed off to Studio production_tick)

1. Boubacar picks persona name (Salif vs Aminata vs other)
2. Studio brand_config entry created
3. ElevenLabs French voice cloned/selected
4. Channel handles created across YouTube + TikTok + Reels + Threads + LinkedIn-FR
5. studio_trend_scout niche config added (Francophone-Africa-AI keyword set)
6. First 3 long-form scripts approved by Boubacar (set the voice baseline)
7. Studio production_tick takes over from week 2

---

## Channel 2: Mande-Folk-Instrumental Ambient (focus music with West African roots)

### One-line thesis

Lofi music is saturated. Mande-folk-instrumental ambient (kora + balafon + djembe + ngoni in slow ambient arrangements) is not. Boubacar's Guinean heritage is a defensible cultural moat: someone who actually grew up adjacent to this music tradition produces credibly-arranged content, where a generic Spotify lofi producer cannot.

### ICP

- Knowledge workers globally who want non-English non-anglo focus music for deep work
- African diaspora (any region) looking for ambient music that connects to roots
- Yoga + meditation + study communities outside the lofi-saturated lane

### Production cadence

- 1 to 2 new 1-2 hour focus mixes per week, uploaded as YouTube videos with a static-or-slow-motion visual loop
- Optional: 1 livestream channel doing 24/7 ambient (gated on the @0x_fokki absorb $40 setup spike landing first)
- All audio generated via Suno or similar music-gen model with Mande instrumentation prompts; light human curation step

### Voice and persona

- No voice. Pure instrumental + ambient.
- Channel branding evokes West African landscape (savanna sunrise, kora close-ups, Conakry skyline) - generated via image-gen + Ken Burns motion through ffmpeg pipeline (Studio standard pivot per `feedback_studio_pipeline_ffmpeg_pivot.md`)

### Studio infra fit

- Suno (external): instrumental music gen with Mande/West African prompts
- kie_media: image gen for video loop visuals
- ffmpeg: Ken Burns motion + slow zoom on static visuals + audio overlay
- Blotato: YouTube + (TikTok cut-downs as audio teasers + Reels for cover-art reveals)
- studio_brand_config: new entry for Mande-Folk channel
- studio_trend_scout: not applicable (music channel, not news-driven)
- HyperFrames: not needed for the long-form (single visual loop)

Net infra additions: external Suno account + brand_config entry + channel handles. Lightest infra footprint of the 3 channels.

### Monetization stack

- YouTube AdSense (focus-music CPM is low but watch-time is extreme: 1-2 hour mixes earn well per video)
- Optional Sponsorships: meditation apps, focus tools, productivity SaaS (small but recurring)
- Distribution to Spotify + Apple Music + DistroKid (passive streaming royalty stream)
- Future: paid "Boubacar's focus playlists" Patreon-style tier once audience builds

### First-90d KPIs

- 24 long-form mixes shipped (2/week)
- 500-2000 YouTube subs (focus-music niches can compound fast once the first viral mix lands)
- Spotify monthly listeners >= 100 after distribution
- Boubacar time: under 15min/week (mostly choosing which generated mixes to release)

### AdamDelDuca anti-pattern self-check

1. Speech-clip: NO. Original instrumental.
2. Kids-yoga: NO. Adult focus-music audience.
3. Generic personal finance: NO.
4. War/news: NO.
5. High-production docs: NO. Low-prod by design.
6. Police/dashcam: NO.
7. **Lofi music (SATURATED, only at massive scale): HIT.** Mitigation = West African cultural moat is the bet. Mande-folk-instrumental is structurally different from typical lofi (real West African instrumentation, slower tempo, different harmonic vocabulary). Boubacar's heritage is the defensible angle.

Net: 1 hard hit on lofi-saturation, mitigated by heritage cut. Worth the bet because the cost to test is so low.

### Brand-spine isolation

- Completely separate from any AI-tools channel
- Optional Boubacar-personal cross-promotion (this is heritage content, personal voice can endorse without brand collision)

### Launch checklist

1. Boubacar picks channel name (placeholder: "Conakry Calm" or "Sahel Focus" or other)
2. Suno account configured w/ instrumental-only Mande/Susu/Mandingo prompts
3. brand_config entry created
4. YouTube + Spotify + Apple Music + Bandcamp handles created
5. First 4 mixes published in week 1 to establish channel character

---

## Channel 3: Lofi-African / Afrobeats-Lofi (closer-to-lofi sibling of Channel 2)

### One-line thesis

If Channel 2 (Mande-Folk) is the heritage moat play, Channel 3 (Lofi-African) is the SEO play. Afrobeats-lofi and amapiano-lofi are emerging search terms with low competition right now. Sister channel to Channel 2, identical infra, different musical vocabulary.

### Why ship BOTH music channels

Two music channels at zero marginal cost (same infra) doubles the surface area for discovery. They target different listeners (heritage-curious vs lofi-search-volume), don't cannibalize each other, and the one that traction-wins earlier gets the priority production slot.

### ICP

- Global lofi listeners searching adjacent to amapiano / afrobeats / African-fusion focus music
- Crossover audience from existing lofi channels who want variety

### Production cadence + infra + monetization

Same as Channel 2. Same Suno + kie_media + ffmpeg + Blotato stack. Different prompt template (afrobeats-lofi instead of Mande-folk).

### AdamDelDuca anti-pattern self-check

Same as Channel 2: 1 hit on lofi-saturation, mitigated by African-fusion cut. The bet is that "afrobeats-lofi" and "amapiano-lofi" are still small enough searches to win SEO position before they saturate.

### Launch checklist

Same as Channel 2 + share infra. Single Suno account + brand_config entry covers both.

---

## Cross-channel: shared infra additions needed before launch

- `studio_brand_config.py`: 3 new entries (AIC-FR-Africa + Mande-Folk + Lofi-African)
- `studio_trend_scout` niche config: 1 new entry (Francophone-Africa-AI keyword set)
- ElevenLabs voice registry: 1 new French voice for AIC-FR-Africa persona
- Suno account: external (Boubacar provisions)
- Channel handles: 3 sets across YouTube + platform-by-channel-fit

No new orchestrator module needed. No new skill needed. No CrewAI crew needed. All 3 channels run on existing Studio production_tick + Blotato fan-out.

## Sequencing recommendation

**Week 1:** Boubacar approves spec + picks persona name + provisions Suno + creates channel handles.
**Week 2:** AIC-FR-Africa first 3 long-forms (Boubacar reviews to set voice baseline).
**Week 3:** Mande-Folk + Lofi-African first 4 mixes each (low-touch, Suno-generated).
**Week 4:** Studio production_tick takes over all 3 channels. Boubacar time drops to <30min/week aggregate.

## Open questions for Boubacar before launch

1. AIC-FR-Africa persona name (Salif / Aminata / Boubacar-picks-other)?
2. Comfortable with AI-persona-as-honest framing or want a different voice posture (e.g. "we built this AI to help Francophone Africans")?
3. Studio M5 monetization analytics is not yet shipped: are you OK launching pre-analytics and adding tracking retroactively, or want M5 to land first?
4. Brand handles: pick all-3 names + Boubacar registers, or assign to a junior to register?
5. Which channel ships FIRST if we have to stagger (recommend AIC-FR-Africa for July-wave urgency; music channels can follow 2 weeks later)?

## What this spec does NOT cover

- Pricing or specific lead-magnet copy for SW/CW conversion
- Specific Notion guide product spec (only flagged as a future revenue layer)
- AIC-FR-Africa's news vs tools split percentage (start 70% tools + 30% news, adjust based on engagement)
- Music distribution contracts (DistroKid vs CD Baby vs other) - Boubacar's call
- Reopen conditions for the layoff-wave assumption (handled in the parallel /council deep-review)
