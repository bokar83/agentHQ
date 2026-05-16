# 10-Channel Studio Program: Africa-Themed (5) + Layoff-Wave-Prep (5)

**Status:** SPEC (awaiting Boubacar approval).
**Date:** 2026-05-16.
**Companion to:** `docs/strategy/aic-fr-africa-mande-folk-lofi-channels-2026-05-16.md` (channels 1-3 detailed there; this doc adds channels 4-10 plus master sequencing for all 10).
**Strategic lens:** `reference_layoff_wave_2026_strategic_lens.md` + `feedback_boubacar_synthesis_pattern.md` (memory).

## What this doc covers

This is the master program doc for all 10 Studio sub-channels Boubacar has approved or council-greenlit. The earlier companion spec covers channels 1-3 in detail (AIC-FR-Africa, Mande-folk-instrumental, Lofi-African). This doc adds channels 4-10 and provides the cross-channel sequencing, capacity check, voice-creep tripwire, and reopen/kill rules for the whole program.

## The 10 channels

### Africa-themed cluster (Boubacar moat: heritage + language + geography)

1. **AIC-FR-Africa** — French AI tools + AI news for Francophone African ICP, AI persona host. (Spec'd in companion doc.)
2. **Mande-Folk-Instrumental ambient** — West African focus music (kora + balafon + djembe). (Spec'd in companion doc.)
3. **Lofi-African / afrobeats-lofi** — SEO sibling to channel 2. (Spec'd in companion doc.)
4. **1stGen-FR diaspora money** — French port of 1stGen Money, targeting Francophone African diaspora in France, Belgium, Canada, Quebec.
5. **AI-tools-for-African-SMB** — practical Claude / n8n / AI use cases for small African business operators (salon, construction, retail). Ships AFTER channel 1 validates traction.

### Layoff-wave-prep cluster (Boubacar moat: forward-timing + faceless infra + pipeline conversion)

6. **Boring Business + AI** — per-trade variants (HVAC, roofing, etc.) feeding CW + SW directly. Highest strategic ROI.
7. **AI For HR / AI For Ops** — role-specific AI explainers feeding CW SMB-launch SKU.
8. **The Soft Landing** — career transition, severance math, COBRA, freelance pivot. Feeds 1stGen.
9. **Knowledge Worker AI Toolkit** — faceless screen-recordings of real desk-worker AI workflows. Feeds CW DIY pack.
10. **One Hour Income** — no-code micro-product builds. Feeds 1stGen + clone-builder SKU.

## Channels 4-10 detailed

### Channel 4: 1stGen-FR Diaspora Money

**Thesis:** 1stGen Money's content angle (first-gen immigrant money advice) ports cleanly to the Francophone diaspora in France, Belgium, Canada, Quebec. ICP shares the financial-literacy gap + diaspora-specific concerns (remittances, family-back-home obligations, business-back-home investing) but currently has no major French-language operator on YouTube.

**ICP:** Senegalese, Ivorian, Malian, Guinean, Burkinabe diaspora (and adjacent Francophone African diaspora) in Europe + Canada. 25-45 age band, employed, financially-literate-adjacent but underserved by Anglo-1stGen content.

**Production cadence:** mirrors 1stGen English cadence (whatever that is at scale). French ElevenLabs voice (different persona from AIC-FR-Africa).

**Infra fit:** identical to 1stGen English. New brand_config entry + French voice + trend_scout config for Francophone-diaspora-money keywords.

**Conversion path:** 1stGen-FR audience -> 1stGen money-advice products + future 1stGen-FR Notion templates + remittance-app affiliate (Wise, Remitly, Sendwave).

**DelDuca self-check:** Risk #3 (generic personal finance is too broad). Mitigation: diaspora-specific framing locks the cut (remittances, family obligations, business-back-home). Stay narrow.

**Brand-spine isolation:** runs under 1stGen brand spine (cousin not separate brand). Cross-promotion from 1stGen English allowed since same family.

**Voice:** different persona/voice from AIC-FR-Africa to avoid brand collision. Could be voice-only (no AI face needed for money content).

**Time to ship:** 2 weeks once English 1stGen ops are observed and translated.

### Channel 5: AI-Tools-for-African-SMB

**Thesis:** Distinct from AIC-FR-Africa (which is AI-tools-curious-general-audience). Channel 5 targets operator ICP: small African business owners who want concrete AI use cases for their specific business (salon bookings, construction quoting, retail inventory). Practical not philosophical.

**ICP:** Owner-operators of $50K-$1M/yr revenue African SMBs. WhatsApp-heavy. Mobile-first. Mostly Francophone but could fork to Anglophone or Lusophone later.

**Production cadence:** 2 long-form per week + 4 shorts per week. Long-form = "how to use [tool] for your [business type]" with real workflow walkthroughs.

**Infra fit:** Studio video stack + screen-recording overlay via HyperFrames + French voice. WhatsApp Business API connection for distribution (forward winning shorts to African WhatsApp lists).

**Conversion path:** SMB operator audience -> AIC-FR's AI-tools sponsorships + future "AI Toolkit for African SMBs" Notion guide ($29-$47) + potential white-label deals with African SaaS platforms.

**DelDuca self-check:** All 7 clean. Operator ICP is concrete + narrow.

**Ship timing:** AFTER AIC-FR-Africa shows traction signal (~60-90 days post-launch of channel 1). Boubacar explicit ordering.

### Channel 6: Boring Business + AI (per-trade variants)

**Thesis:** Council flagged this as the strategic crown jewel. Every view potentially a $5K CW deal. SW already has 8+ trade verticals = 8 channel variants on same Studio infra.

**ICP:** US/Canada small-trade business owners (HVAC, roofing, plumbing, salon, restaurant, dental). $500K-$5M annual revenue. Quasi-tech-curious but solo-operating; need AI to save 10hrs/wk.

**Production cadence:** 1 long-form case-study per week + 3 shorts. Case-studies pulled from SW teardowns (even non-closed prospects work as content).

**Infra fit:** scene-segmenter handles case-study beats + HyperFrames overlay + ffmpeg compose + Blotato. Per-trade brand_config swap. SW teardown output in `agent_outputs/` is the content bank.

**Conversion path:** trade operator -> SW website-build lead OR CW consulting lead. Sponsorship overlay possible with trade-software vendors (ServiceTitan, Jobber, Housecall).

**DelDuca self-check:** Risk #3 (saturation). Mitigation = real-receipts moat (actual SW client work) beats generic creator economics. Boubacar earned-authority is the cut.

**Sequencing:** pick ONE trade vertical first (HVAC or roofing — whichever has most case-study material in SW agent_outputs). Prove template, then fan to 2-3 more trades.

### Channel 7: AI For HR / AI For Ops (rename from "Claude For Non-Coders")

**Thesis:** Outsider voice flagged it: "Claude for non-coders" loses laid-off knowledge workers at the title. Search intent is "AI tools for HR" or "AI for ops". Rename + role-cut wins SEO.

**ICP:** HR coordinator / Operations manager / Financial analyst / Marketing manager age 30-50. Mid-career, now AI-curious, partly out of fear (will I get laid off?) partly genuine (how can I keep my job?).

**Production cadence:** 4 shorts per week + 1 long-form per week. Episode bank already seeded by 27+ archived absorbs (Bober + darkzodchi + Zephyr + navtoor + Sprytix + rubenhassid + more).

**Infra fit:** ElevenLabs neutral VO + scene-segmenter for tool-by-tool beats + HyperFrames screen-rec overlay + Blotato. Native voice clone of "AI assistant for HR" persona (no face).

**Conversion path:** HR/Ops audience -> CW SMB-launch SKU (when laid-off they start their own consultancy / agency / coaching biz) + future "AI Stack for [Role]" Notion guide ($47) + lead-magnet to 1stGen for money-side decisions.

**DelDuca self-check:** Risk #3 (saturation). Mitigation = HARD role pivot per channel ("AI For HR Coordinators" not "AI For Non-Coders"). Generic loses; role-specific wins.

**Sequencing:** start with ONE role (recommend HR — highest displaced-population + highest desperation + highest searcher conversion). Prove template, then fan to Operations and Finance.

### Channel 8: The Soft Landing

**Thesis:** Time-locked to the layoff wave. Pure utility channel. Severance math, COBRA vs ACA marketplace cost, 401k rollover decisions, freelance pivot timing, healthcare bridge tactics, first-90-day plan after layoff.

**ICP:** Severance-week to month-3 post-layoff knowledge workers. Marketing director, mid-level engineer, ops manager, finance analyst. Numb, decision-paralyzed, looking for checklists not motivation.

**Production cadence:** 3 utility shorts per week + 1 long-form decision-tree per week.

**Infra fit:** data-viz Shorts (number-driven, fact-cards) via HyperFrames + ElevenLabs neutral VO + scene-segmenter for fact beats.

**Conversion path:** displaced-worker audience -> 1stGen money advice (PRIMARY funnel — CW $5K is wrong for this ICP) + affiliate to job-board / healthcare-marketplace / severance-negotiation tools + future "Layoff Recovery Toolkit" Notion guide.

**DelDuca self-check:** Risk #4 (advertiser flight on "layoff" topics — YouTube demonetizes aggressively). HARD mitigation: frame "career transition" / "next chapter" / "AI-readiness reset" NOT "layoff" / "fired" / "unemployed". TOS distinguishes. Compliance check at every script.

**Time-criticality:** must launch by 2026-07-15 to age into July wave. Ship Wave 2.

### Channel 9: Knowledge Worker AI Toolkit (DEFERRED to Q3)

**Why deferred:** Council flagged Boubacar needs to narrate own workflows = breaks <30min/wk budget. Defer until CW MRR hits a sustainability floor. Episode seeds already exist from Sprytix + navtoor + rubenhassid absorbs (7-layer personal AI system = 7-episode series ready to ship when capacity opens).

**Reopen trigger:** CW MRR exceeds $5K/mo + Boubacar willing to do 30-45min/wk narration recording session.

### Channel 10: One Hour Income (DEFERRED to Q4)

**Why deferred:** High saturation risk + Boubacar real-builds requirement (time leak) + lower 1stGen funnel priority vs Soft Landing. Ship after CW productized SKU lands and 1stGen MRR validates the no-code-micro-product funnel.

**Reopen trigger:** CW productized SKU live + 1stGen MRR > $2K/mo.

## Master sequencing across all 10 channels

### Wave 1 (spec by 2026-06-01, launch by 2026-06-15)

Goal: warm up the 3 highest-strategic-ROI channels first.

- **Channel 6 — Boring Business + AI** (pick 1 trade vertical first: HVAC or roofing based on SW agent_outputs volume)
- **Channel 7 — AI For HR** (single role first, fan after proof)
- **Channel 1 — AIC-FR-Africa** (already spec'd, lowest infra add since persona + brand_config + voice are net-new but no new pipeline)

3 channels. Studio production_tick handles. Boubacar time: ~90min/wk total review + persona approval across the 3.

### Wave 2 (spec by 2026-06-30, launch by 2026-07-15)

Goal: ship time-critical layoff-wave channels + low-overhead music channels. Wave 2 just makes the layoff-window age requirement.

- **Channel 8 — The Soft Landing** (TIME-CRITICAL: must age into July wave)
- **Channel 2 — Mande-Folk-Instrumental** (lowest overhead — Suno + ffmpeg loop)
- **Channel 3 — Lofi-African** (sibling of #2 — same infra + same launch)

3 more channels. Cumulative: 6 channels live by mid-July. Boubacar time: ~120min/wk aggregate.

### Wave 3 (spec by 2026-08-15, launch by 2026-08-30)

Goal: ship validated-after-Wave-1 channels.

- **Channel 4 — 1stGen-FR** (port from 1stGen English ops)
- **Channel 5 — AI-tools-for-African-SMB** (after Channel 1 traction signal)

2 more channels. Cumulative: 8 channels live by end of August. Boubacar time: ~150min/wk aggregate.

### Wave 4 (Q3-Q4 2026, deferred)

- **Channel 9 — Knowledge Worker AI Toolkit** (deferred until CW MRR floor)
- **Channel 10 — One Hour Income** (deferred until CW SKU + 1stGen MRR validates)

Total program at full deploy: 10 channels live by Q4 2026.

## Capacity check

Studio production_tick + Blotato fan-out + Cards v2 pipeline empirically handles ~3-5 channels concurrently today. The Wave 1/2/3 sequencing keeps capacity ahead of demand by adding only 2-3 channels per wave. Studio M5 monetization analytics is the critical missing piece — ships before Wave 1 if possible so revenue signal is measurable from launch.

If Studio capacity strains during Wave 2:
- **Drop first:** Channel 8 Soft Landing (weakest non-layoff fallback if wave does not materialize)
- **Then:** Channels 2 + 3 (music, lowest revenue per minute of attention)
- **Keep at all costs:** Channels 1, 6, 7 (Wave 1 strategic crown jewels)

## Voice-creep tripwire (the killer)

Per council premortem failure mode #3 (HIGH probability). 10 new faceless channels = Studio agents consume ~10 new style references weekly. CTQ has already flagged voice-creep twice in 2026-05.

**Tripwire mechanism:**
1. **Pre-program baseline:** Boubacar's last 50 personal-account posts (LinkedIn + X + newsletter) scored on existing CTQ rubric. Saved as `data/boubacar-voice-baseline-2026-05-16.json`.
2. **Quarterly audit:** CTQ re-scores last 50 personal-account posts vs baseline. Drift threshold: 15% on hook/voice fingerprint scores.
3. **Tripwire fire:** if drift breaches threshold, automatic 1-month "Studio dark" pause. All 10 channels stop new content. Boubacar reviews voice-creep root cause.
4. **Reset:** post 1-month dark, re-baseline + restart with stricter per-channel voice-loading isolation.

This is the single most important guardrail in the program. It costs nothing in setup and protects Boubacar's main asset.

## Reopen / kill conditions

**Program-wide kill:** if (a) layoff wave demonstrably does not materialize by 2026-09-01 AND (b) zero Wave-1 channels have hit Studio-M5 monetization floor by then. Pivot warmed channels to evergreen content.

**Channel-level pause:** any single channel triggers DelDuca 2+ red flags retrospectively OR voice-creep CTQ alarm fires AND that channel is the root cause.

**Add candidates to program:** future absorbs surface market gaps Boubacar can defend (per `boubacar-synthesis-pattern` 4-lens pass), at which point new channel proposed for next-wave inclusion.

## Open questions for Boubacar before Wave 1 launch

1. **AIC-FR-Africa persona name** (Salif / Aminata / other)? (Carried from earlier spec.)
2. **First trade vertical for Channel 6** (HVAC or roofing)? Depends on which has more SW agent_outputs material.
3. **First role for Channel 7** (HR or Operations)? Recommend HR for searcher-conversion density.
4. **Studio M5 monetization analytics:** ship before Wave 1 OR launch pre-analytics + add tracking retro?
5. **Channel handle ownership:** Boubacar registers all 10 sets himself OR delegate to a VA / junior?
6. **Voice-baseline approval:** OK with the proposed tripwire mechanism + 15% drift threshold?

## What this doc does NOT cover

- Per-channel script templates (handled in channel-specific deep specs once Boubacar approves the program)
- Per-channel monetization breakdown beyond high-level (CW vs SW vs 1stGen vs AdSense)
- Studio M5 analytics design (separate doc)
- Channel handle registration sequence (Boubacar's call)
- Pricing for productized SKUs feeding from each channel (separate strategy doc)
- Specific Wave 1 launch timeline beyond 2-week windows
