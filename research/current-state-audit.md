# Current State Audit: CW + SW Lead-Gen Artifacts

**Audit date:** 2026-04-30
**Scope:** Every lead-gen artifact currently live or recently launched across Catalyst Works (CW) and Signal Works (SW).
**Method:** Filesystem walk, source-code read, Hormozi-framework comparison from research/hormozi-research-notes.md.
**Severity scale:** 1 (cosmetic) → 5 (load-bearing failure).

---

## Inventory

| # | Artifact | Path | Status | Severity |
|---|---|---|---|---|
| 1 | CW Cold Outreach T1 ("Where is your margin actually going?") | `templates/email/cold_outreach.py` | LIVE, sending | 2 |
| 2 | CW Cold T2 - SaaS audit PDF value-add | `templates/email/cw_t2.py` | LIVE | 1 |
| 3 | CW Cold T3 - bottleneck bump | `templates/email/cw_t3.py` | LIVE | 3 |
| 4 | CW Cold T4 - pattern-recognition | `templates/email/cw_t4.py` | LIVE | 2 |
| 5 | CW Cold T5 - breakup | `templates/email/cw_t5.py` | LIVE | 2 |
| 6 | SW Cold T1 - "Invisible on ChatGPT" | `templates/email/sw_t1.py` | LIVE (Drafts mode) | 2 |
| 7 | SW Cold T2-T4 - sequence | `templates/email/sw_t2-4.py` | LIVE (Drafts mode) | 3 |
| 8 | SW long-form HTML cold email (score-based) | `signal_works/email_builder.py` + `templates/cold_email.txt` | LIVE | 4 |
| 9 | SW score-engine lead magnet (AI Visibility Score) | `signal_works/ai_scorer.py` | LIVE | 1 |
| 10 | SW demo sites (dental, roofing, HVAC) | Vercel: signal-works-demo-* | LIVE | 1 |
| 11 | SW autoplay video pages (per niche) | Vercel `/play.html` per demo | LIVE | 1 |
| 12 | Sequence engine - 4-touch (SW) / 5-touch (CW) | `skills/outreach/sequence_engine.py` | LIVE | 1 |
| 13 | Morning runner - daily 20 drafts | `signal_works/morning_runner.py` | LIVE on VPS systemd timer | 1 |
| 14 | CW Discovery Call OS v2.0 | `docs/roadmap/harvest.md` references; not located as standalone file | EXISTS in roadmap | 3 |
| 15 | Inbound lead drafter (lints for blocked frameworks/sales phrases) | `skills/inbound_lead/drafter.py` | LIVE | 1 |
| 16 | Engagement Ops skill | `skills/engagement-ops/SKILL.md` | LIVE | 1 |
| 17 | Voice-DNA personalizer | `signal_works/voice_personalizer.py` | LIVE (CW only) | 2 |
| 18 | A/B test infrastructure (variant A vs B framing) | `signal_works/email_builder.py` | PAUSED 2026-04-28 | 2 |
| 19 | Channel = Cold email only (today) | - | Single-channel | 5 |
| 20 | Lead magnet for CW | - | DOES NOT EXIST | 5 |
| 21 | Warm outreach system | - | DOES NOT EXIST | 5 |
| 22 | Posting / Content channel | LinkedIn intermittent; no system | NEAR-ZERO | 4 |
| 23 | Paid ads | - | DOES NOT EXIST | 1 |
| 24 | Follow-up reactivation for opens-but-no-replies | - | DOES NOT EXIST | 3 |
| 25 | Lead getters (referrals / employees / agencies / affiliates) | - | DOES NOT EXIST | 2 |

---

## Per-Artifact Audit

### 1. CW Cold Outreach T1 - "Where is your margin actually going?"

**File:** `templates/email/cold_outreach.py`

**What it is:** The 145-word seed cold email that launched yesterday (2026-04-29) to Apollo-sourced ICP leads. Sends from `boubacar@catalystworks.consulting`.

**What it does well by Hormozi standards:**
- **Hook is contrarian + specific.** "Most businesses aren't losing margin to bad strategy. They're losing it to one bottleneck." This inverts conventional wisdom and creates a curiosity loop. Strong Hook by H-R-R.
- **Soft CTA is one yes/no question** ("Is there a place... where work slows down or disappears?"). Low friction. Hormozi-compliant.
- **No sales phrases.** The drafter lints out "circle back," "leverage your," "transform your business," etc.
- **Personal authority is named** ("15 years working with leadership teams across three continents"). Matches Hormozi's Big Fast Value criterion: prove the sender has earned the prospect's attention.
- **Closes with a direct ask, not a meeting link dump.** "If yes, worth a reply." This is healthier than "book a Calendly" because it tests interest before consuming the prospect's calendar slot.

**What it's missing by Hormozi standards:**
- **No Big Fast Value upfront.** Hormozi's cold rule: give first, ask second. The email asks ("Is there a place...") before delivering anything the prospect can take and use. The SaaS audit PDF arrives at T2, six days later. By Hormozi math, T1 should already carry a tangible micro-value (a one-line observation, a specific stat, a relevant micro-finding) before the question.
- **Personalization is structural-only.** First name token. No reference to anything specific about THE prospect's business. Hormozi rejects this as "send-or-don't-send" territory.
- **No proof.** "15 years across three continents" is biographical, not proof of result. Hormozi's Perceived Likelihood lever is empty here.
- **Value Equation score:**
  - Dream Outcome: 6/10 (margin recovery is the implicit promise; not named in prospect's words)
  - Perceived Likelihood: 3/10 (no case study, no number, no client name)
  - Time Delay: 5/10 (a Signal Session is 90 min; not stated in T1)
  - Effort: 7/10 (one reply; very low effort)
  - **Total: 21/40 → 5.25/10 average. Below Hormozi's 7/10 floor.**

**Verdict:** **MODIFY.** The structure is already Hormozi-flavored (contrarian hook, low-friction CTA, no sales sludge). The fixes are surgical: add one line of Big Fast Value before the question, add one proof point, sharpen the dream outcome to a number/timeframe.

**Severity:** 2 (good bones, two missing levers)

---

### 2. CW Cold T2 - SaaS Audit PDF Value-Add

**File:** `templates/email/cw_t2.py`

**What it is:** Day-6 follow-up. Opens with "no worries if the timing was off," delivers a one-page SaaS audit PDF link, names a specific number ($9,660/year average bleed), offers $500 flat audit upgrade.

**Hormozi alignment:**
- **THIS is Big Fast Value.** A free, useful, immediately-consumable artifact. Hormozi-compliant lead magnet adjacent.
- **The number ($9,660/year) is specific.** Strong Perceived Likelihood booster.
- **The upsell is priced and time-bound** ("$500 flat. Delivered in 5 business days. No retainer."). Time Delay clear, Effort clear, Sacrifice (price) clear.

**What it's missing:**
- **PDF is a flat artifact, not a Hormozi-grade lead magnet.** It tells a story but does not generate engagement signal. By Hormozi's 7-step lead magnet rule, it should: (a) solve a narrow problem completely, (b) reveal another problem your core offer solves, (c) end with a clear CTA back to the next step. T2 is closer to "value drop" than "lead magnet."
- **Sequence misorder.** In Hormozi's Cold Outreach 3-Problem framework, Big Fast Value should land in T1, not T2. By T2 the prospect has already decided whether to engage.

**Verdict:** **KEEP, with minor tightening.** Push some of T2's value into T1; keep T2 as the PDF delivery + audit upsell.

**Severity:** 1

---

### 3. CW Cold T3 - Bottleneck Bump

**File:** `templates/email/cw_t3.py`

**What it is:** 3-sentence Day-9 bump. "Most owners I talk to already know where the friction is. They just haven't had time to name it precisely... That's the 90 minutes. Still worth it?"

**Hormozi alignment:**
- **Short, low-pressure.** Good.
- **One named offer** (90 min Signal Session implied).

**What it's missing:**
- **No new value.** Hormozi's follow-up rule: every touch must add something. T3 just bumps. He'd reject this as "just bumping."
- **Self-referential.** "I talk to" is operator-perspective, not prospect-perspective.
- **No proof angle.** Could carry one micro-case at this stage and double in weight.

**Verdict:** **MODIFY.** Add one new value angle (a one-line case study, a one-line stat, or a one-line specific finding from the SaaS doc) so the touch isn't a bump.

**Severity:** 3

---

### 4. CW Cold T4 - Pattern-Recognition

**File:** `templates/email/cw_t4.py`

**What it is:** Day-14 social-proof-via-pattern. "Most businesses I work with have the same pattern: one decision point, one approval loop, or one pricing gap..."

**Hormozi alignment:**
- **Specificity is good** (decision point / approval loop / pricing gap).
- **Diagnostic positioning** maintained from T1.

**What it's missing:**
- **Same "I work with" but no actual client.** Hormozi's hard rule: never imply social proof you can't show. Per Boubacar's hard rule (memory: "Never Fabricate Client Stories"), the "businesses I work with" framing is borderline.
- **No client name or anonymized number.** A real Signal Works prospect would assume "I work with" means CW has paid clients. CW does not yet (per harvest.md, "Zero paid engagements as of 2026-04-28").

**Verdict:** **MODIFY URGENTLY.** Reframe from "businesses I work with" to "businesses I've spent 15 years inside" - same authority, no implied client roster. This is on the edge of the No-Fabricated-Stories rule.

**Severity:** 2

---

### 5. CW Cold T5 - Breakup

**File:** `templates/email/cw_t5.py`

**What it is:** Day-19 final. "I won't follow up after this." Names both offers (Signal Session + SaaS audit) one last time.

**Hormozi alignment:**
- **Implicit scarcity** (deadline created by sender stopping).
- **Re-anchors offers** with prices.
- **Doesn't beg.**

**What it's missing:**
- **No final value drop.** Hormozi-style breakups often ship one last useful thing (a benchmark, a stat, a parting observation) so even non-converters keep CW in mind.

**Verdict:** **MODIFY.** Add one final value drop. Otherwise solid.

**Severity:** 2

---

### 6-7. SW Cold T1 + T2-T4

**Files:** `templates/email/sw_t1.py`, `sw_t2.py`, `sw_t3.py`, `sw_t4.py`

**What it is:** Plain-text 4-touch SW sequence (Day 0/3/7/12). T1 has two openers (no-website variant + default ChatGPT-search variant). Sends from `geolisted.co` brand, marked "Reply STOP to opt out."

**Hormozi alignment:**
- **Hook is concrete and falsifiable.** "Open ChatGPT and type: 'who is the best [niche] in [city]?' If your business is not in the answer, someone ready to hire just called your competitor instead." This is Hormozi-grade. The prospect can verify in 10 seconds.
- **Specificity** is high (niche + city + AI tool names).
- **Time-bound stake** ("That window closes fast once one business in your category claims it"). Implicit urgency, Hormozi-compliant.
- **Two-week build, free demo** sets Time Delay and Sacrifice clearly.
- **CTA is low-friction** ("Worth a look?").

**What it's missing:**
- **No proof.** No client name, no before/after, no case study. Per harvest.md, no paying SW client yet. Per memory's no-fabrication rule, this is correct - but the lever is empty.
- **The HTML version (artifact #8) and the plain-text T1 are competing.** Two cold-email systems for the same prospect.

**Verdict:** **KEEP**, with proof-add when SW client #1 ships.

**Severity:** 2 (T1) → 3 (T2-T4 inherits the "every touch must add value" Hormozi rule; sample T2-T4 sequence not read in this audit, flagged for review)

---

### 8. SW Long-Form HTML Cold Email (score-based)

**File:** `signal_works/email_builder.py` + `signal_works/templates/cold_email.txt`

**What it is:** A second SW cold-email system. Pre-computes an AI visibility score (0-100), embeds it in subject + score-bar visual, lists 3 quick wins, links a niche-specific autoplay video, links Calendly. Plain-text fallback in `cold_email.txt`.

**Hormozi alignment:**
- **THE SCORE IS A LEAD MAGNET.** This is Hormozi's "Reveal Problem (Diagnosis)" lead magnet type, executed inline. Strong.
- **Specificity is exceptional.** Score, breakdown, niche-tailored quick wins, niche-tailored video, competitor reference.
- **Big Fast Value is in the email itself.** The score and the 3 quick wins are takeaway value the prospect can use even if they never reply.
- **Visual proof.** Color-coded score bar, platform indicators (ChatGPT/Perplexity/Bing/Crawlers), accessibility-aware (color + symbol).
- **CTA is clear.** "Book a Free Visibility Check" + Calendly link.

**What it's missing:**
- **The two SW cold systems collide.** Plain-text T1 (`sw_t1.py`) lives in the sequence engine; the HTML email lives in `email_builder.py`. Which one runs in production? Per `morning_runner.py` step 3, the sequence engine fires SW T1-T4. Per `signal_works/AGENTS.md`, `gmail_draft.py` is preferred over GWS CLI. Reading `email_builder.py`, the HTML version exists and creates Gmail drafts but is not called from the sequence engine. **This is unclear and a real risk.**
- **A/B test was paused.** Variant B ("competitors got a 20-person AI team") is preserved but disabled until 2026-05-12.

**Verdict:** **CLARIFY which version runs in prod.** If the HTML version is the live SW T1, it's a 9/10 by Hormozi standards. If it's dead code and `sw_t1.py` is the live one, the HTML version is wasted (and `sw_t1.py` should pull more from it). **Boubacar must clarify.**

**Severity:** 4 (active production ambiguity)

---

### 9. SW AI Visibility Score Engine

**File:** `signal_works/ai_scorer.py`

**What it is:** A scoring engine that produces 0-100 for any lead based on (a) ChatGPT mention, (b) Perplexity mention, (c) robots.txt allowlist for AI crawlers, (d) Bing Places claimed.

**Hormozi alignment:**
- **Pure Reveal-Problem lead magnet.** This is best-in-class Hormozi.
- **Scales.** Score generated automatically for every lead before any outreach.
- **Falsifiable + defensible.** All 4 criteria are real, fixable things.

**What it's missing:**
- **Not productized as a public tool yet.** Per signal_works_plan.md Phase 2: "AI Visibility Score as Viral Web App (Month 6+)." The score is currently a private prospecting input. Hormozi would say: ship this as a free web tool tomorrow, gate the full report on email capture, and let it become a content-channel acquisition asset.

**Verdict:** **KEEP, productize sooner.** Severity flag is 1 because the artifact itself is excellent; the under-utilization is a strategic note for Phase 5.

**Severity:** 1

---

### 10-11. SW Demo Sites + Autoplay Video Pages

**Paths:** Vercel `signal-works-demo-{dental,roofing,hvac}.vercel.app/`, with `/play.html` autoplay pages.

**What it is:** Per-niche static demo sites. The URL is dropped into every cold email so the prospect can see the work.

**Hormozi alignment:**
- **THE DEMO IS A LEAD MAGNET.** "Sample of the Service" type. Hormozi-grade.
- **Niche-specific.** Roofers see roofing demo; dentists see dental demo. Conversion-friendly.
- **Time-to-value is seconds.** Click the link, watch the video.

**Verdict:** **KEEP.** Best-in-class.

**Severity:** 1

---

### 12. Sequence Engine

**File:** `skills/outreach/sequence_engine.py`

**What it is:** Drives the 4-touch (SW) / 5-touch (CW) cadence. Tracks `sequence_touch` per lead in Postgres, advances on day-gap satisfied, writes Gmail drafts (or auto-sends if the env var is on).

**Hormozi alignment:**
- **Mechanically correct cadence.** Day 0 / 3 / 7 / 12 (SW) and 0 / 6 / 9 / 14 / 19 (CW). Both inside Hormozi's "min 8 touches across channels" rule when combined with reactivation.
- **Opt-out tracked.** Compliance baked in.
- **Account discipline** (CW + SW from same Gmail).

**What it's missing:**
- **Single-channel.** Email only. Hormozi's 8-touchpoint rule explicitly assumes cross-channel (email → LinkedIn → call → email). SW + CW today have no LinkedIn, no DM, no call leg.
- **No reactivation loop.** A lead who hits T5 with no reply goes opt_out. Hormozi's "Keep your list warm" rule says quarterly value drops to dormant contacts. Not implemented.

**Verdict:** **EXTEND.** The mechanics are solid. The next layer is multi-channel (LinkedIn DM is the obvious add) and quarterly reactivation.

**Severity:** 1 (engine), but cross-references **#19 (single-channel)** as Severity 5

---

### 13. Morning Runner

**File:** `signal_works/morning_runner.py`

**What it is:** Daily 07:00 MT job on VPS systemd timer. 5 steps: bounce scan, SW topup, SW sequence, CW topup, voice personalize, CW sequence. 20 drafts/day target.

**Hormozi alignment:**
- **Daily volume hits the Rule of 100 spirit.** 20 drafts/day across two pipelines = 600/month combined. Below Hormozi's "100 cold/day" but realistic for a one-person op.
- **Sundays + Saturdays skipped on send (gating).** Compliance and deliverability-friendly.
- **Telegram alert on zero drafts.** Failure-aware.

**What it's missing:**
- **20/day is below Hormozi's velocity floor for cold.** He'd push for 100 cold + 100 warm + 100 minutes content + 100 minutes paid. Boubacar is at ~20 cold and zero of the others.

**Verdict:** **KEEP, scale up only after channel diversification.** Severity 1 in itself. The volume gap is captured in **#19**.

**Severity:** 1

---

### 14. Discovery Call OS v2.0

**Status:** Referenced in `harvest.md` but no standalone discovery-call-system file located in this audit. It may be embedded inside engagement-ops or live as a workspace doc.

**Hormozi alignment:** TBD - cannot audit without reading the doc.

**Verdict:** **LOCATE + AUDIT in next session.**

**Severity:** 3 (load-bearing for the close, but invisible until found)

---

### 15. Inbound Lead Drafter

**File:** `skills/inbound_lead/drafter.py`

**What it is:** A linter that scrubs em dashes, sales phrases, and blocked frameworks from any drafted email. Re-generates once on lint failure.

**Hormozi alignment:**
- **Voice consistency at scale.** Critical for Hormozi-grade outreach (avoids "circle back" / "transform your business" / etc.).
- **Belt-and-suspenders for the brand.**

**Verdict:** **KEEP.** Best-in-class.

**Severity:** 1

---

### 16. Engagement Ops Skill

**File:** `skills/engagement-ops/SKILL.md`

**What it is:** The post-conversion engagement runner. Engagement brief, session notes, deliverable tracker, closeout memo. Pulls from PM rigor library.

**Hormozi alignment:**
- **Hormozi doesn't cover this layer in $100M Leads** - it's the delivery side. But: clean post-sale ops feed referrals, which is one of Hormozi's 4 lead getters.

**Verdict:** **KEEP.** Adjacent but supports the lead-getter system.

**Severity:** 1

---

### 17. Voice-DNA Personalizer

**File:** `signal_works/voice_personalizer.py`

**What it is:** Pulls a prospect's writing voice from public sources (LinkedIn posts, About page, transcripts) via `transcript-style-dna`, generates one personalized opener line per CW lead. Used in CW sequence T1 only.

**Hormozi alignment:**
- **TRUE personalization.** Not first-name-token; actual voice mirroring. Hormozi's Cold Outreach 3-Problem rule says "personalize," and this is the highest grade of it.
- **Limited to 10 leads/day** (matches CW daily_limit).

**What it's missing:**
- **CW only.** SW leads do not get voice personalization. This is a deliberate trade-off (SW prospects are local SMB owners who often don't have public voice signal), but worth documenting.

**Verdict:** **KEEP, expand if SW LinkedIn presence detection is added.**

**Severity:** 2 (great, but underused on SW side)

---

### 18. A/B Test Infrastructure

**File:** `signal_works/email_builder.py` (`AB_TEST_ACTIVE = False`)

**What it is:** Variant B ("competitors got a 20-person AI team") preserved but disabled until 2026-05-12.

**Hormozi alignment:**
- **More-Better-New axis 2 ("Better").** Hormozi's "one test per week per platform" rule. Critical for finding the better hook.

**What it's missing:**
- **Currently dormant.** Hormozi: launch → run Rule of 100 → test one variable per week. Boubacar is at the launch stage so the dormancy is appropriate. Re-enabling 2026-05-12 is the right call, but only if a measurable criterion (reply rate over a 20-email batch, 5 business days) is locked in beforehand. Per harvest.md, this is the plan.

**Verdict:** **REACTIVATE on schedule.** Lock the criterion before flipping.

**Severity:** 2

---

### 19. CHANNEL = COLD EMAIL ONLY (today)

**Status:** Single-channel.

**Hormozi alignment:**
- **CRITICAL FAILURE BY HORMOZI STANDARDS.** The Core Four is a portfolio. Boubacar is running ONE of the four. By Hormozi's activation order, Warm Outreach should have been first. By the 8-touchpoint follow-up rule, every prospect should be hit across email + LinkedIn + phone, not just email.

**Verdict:** **REPLACE the single-channel assumption.** This is the load-bearing strategic gap. Severity 5.

**Severity:** 5

---

### 20. CW LEAD MAGNET - DOES NOT EXIST

**Status:** Missing.

**Hormozi alignment:**
- **CRITICAL FAILURE.** CW has the SaaS audit PDF as a value-drop, but no lead magnet that would let a stranger find Boubacar, opt in, and become an engaged lead without a cold-email touch first. SW has the AI Visibility Score (excellent). CW has nothing equivalent.

**Verdict:** **BUILD.** This is a Phase 5 deliverable. The natural Hormozi-grade CW lead magnet is a "Margin Bottleneck Diagnostic" - Reveal-Problem type, 5-question scorecard, surfaces the prospect's hidden constraint.

**Severity:** 5

---

### 21. WARM OUTREACH SYSTEM - DOES NOT EXIST

**Status:** Missing.

**Hormozi alignment:**
- **CRITICAL FAILURE.** Hormozi's activation-order rule: Warm first. Boubacar has 15 years of contacts (GE, three continents, prior employers, alumni). None of those are in a structured warm-outreach pipeline.

**Verdict:** **BUILD.** Phase 5 deliverable: a warm-reactivation template + a 10-step warm process derived from Hormozi.

**Severity:** 5

---

### 22. POSTING / CONTENT - NEAR ZERO

**Status:** LinkedIn posting is intermittent (per memory's `feedback_newsletter_*` and `ctq-social` skill, content discipline exists in skill form but not in cadence). No system that produces 100 minutes/day of content output for the lead-gen funnel specifically.

**Hormozi alignment:**
- **LARGE FAILURE.** Posting is a Core Four channel. Hormozi treats audience as the compounding asset. Boubacar's audience is small and not growing on a system.

**Verdict:** **DEFER, but design.** Phase 5 should produce the rules; the cadence happens in `harvest.md`.

**Severity:** 4

---

### 23. PAID ADS - DOES NOT EXIST

**Status:** Missing.

**Hormozi alignment:**
- **APPROPRIATE GAP.** Hormozi's activation order: paid ads come 4th. Boubacar has not yet completed channels 1-3, so paid is correctly skipped. Don't add now.

**Verdict:** **NO ACTION.** Skip until $5K MRR floor.

**Severity:** 1

---

### 24. FOLLOW-UP REACTIVATION - DOES NOT EXIST

**Status:** Missing.

**Hormozi alignment:**
- **MODERATE FAILURE.** Once a prospect hits T5 and is opted out (per `sequence_engine.py`), they vanish from the system. Hormozi's rule: keep your list warm with quarterly value drops.

**Verdict:** **BUILD a quarterly reactivation drop.** Phase 5 template.

**Severity:** 3

---

### 25. LEAD GETTERS (Referrals / Employees / Agencies / Affiliates) - DO NOT EXIST

**Status:** Missing.

**Hormozi alignment:**
- **APPROPRIATE GAP for now.** Hormozi's Lead Getters require either paying clients (referrals) or revenue (to hire). Boubacar has zero of either today.

**Verdict:** **DEFER.** First Signal Works contract triggers the referral-ask design.

**Severity:** 2 (correct timing)

---

## Summary Tables

### What CW/SW Has That Hormozi Would Endorse

| Artifact | Why it earns the keep |
|---|---|
| AI Visibility Score (`ai_scorer.py`) | Reveal-Problem lead magnet, automated, scaled |
| SW HTML cold email | Big Fast Value embedded inline (score + quick wins + niche video) |
| Voice-DNA personalizer | True personalization on CW T1 |
| Sequence engine | Day 0/3/7/12 cadence + opt-out tracking |
| Inbound drafter linter | Voice consistency at scale |
| Niche demo sites | Sample-of-Service lead magnet |
| Morning runner discipline | Daily-volume cadence in production |
| Hook structure on CW T1 | Contrarian + specific + low-friction CTA |
| Hook structure on SW T1 | Falsifiable + concrete + time-bound stake |

### What Hormozi Would Force Onto the Roadmap

| Gap | Severity | Why |
|---|---|---|
| Single-channel (email only) | 5 | Core Four is a portfolio, not a menu |
| No CW lead magnet | 5 | No engaged-lead funnel that bypasses cold email |
| No warm outreach system | 5 | Activation-order rule violated; Boubacar has 15 yrs of contacts unmined |
| Two SW cold systems collide | 4 | Production ambiguity between `sw_t1.py` and `email_builder.py` |
| Content channel near-zero | 4 | Audience is the compounding asset; not compounding |
| CW T1 has no Big Fast Value | 2 | Asks before giving; Hormozi reverses this |
| CW T4 social-proof framing | 2 | "Businesses I work with" implies clients CW does not yet have |
| Reactivation loop missing | 3 | Dormant list decays without quarterly value drops |
| Discovery Call OS v2.0 missing from filesystem | 3 | Cannot audit; cannot Hormozi-align without reading |

### Severity Histogram

| Severity | Count | Items |
|---|---|---|
| 5 (load-bearing failure) | 3 | Single-channel; missing CW lead magnet; missing warm outreach |
| 4 | 2 | SW cold-system ambiguity; content channel near-zero |
| 3 | 3 | CW T3 bump w/o new value; reactivation missing; Discovery OS unfindable |
| 2 | 6 | CW T1, T4, T5, voice-personalizer scope, A/B paused, lead getters |
| 1 | 11 | All best-in-class artifacts |

---

## Diagnostic Read

**The system is well-built but narrow.**

Boubacar has built more sophisticated single-channel cold-email infrastructure than 95% of consultants will ever ship. The score engine, voice personalizer, sequence engine, and demo sites are all genuinely Hormozi-grade in *what they do*.

The failure is *coverage*. Hormozi's Core Four is a portfolio - Boubacar is running one of the four. The Rule of 100 and the activation-order rule are both being violated, not by sloppiness but by *strategic narrowing* (cold email + Apollo-sourced ICPs).

**Two interpretations:**
1. **System-design problem.** The skill / template stack should grow to cover Warm + Content + (eventually) Paid.
2. **Volume-of-execution problem.** The system is fine; what's missing is a human who shows up daily across multiple channels.

Phase 6 (review-gate.md) must answer this explicitly. My current read is **65% system, 35% volume**: the missing channels (Warm, Content) are real gaps the skill can fix, but the cold-email channel is already strong enough that adding daily reps (Boubacar's hands on warm DMs + posting) is the immediate highest-leverage move, not more skill-building.

---

## Verdict Inputs for Phase 3

The Phase 3 decision matrix needs to score this current state on the 5 axes (1-10):

1. **Buyer trigger clarity** - current state has strong triggers (CW: bottleneck/margin; SW: AI score) but no validated dream-outcome language from real conversations. **6/10.**
2. **Channel coverage** - 1 of 4 Core channels active. **2/10.**
3. **Hook strength** - both CW and SW T1 hooks are strong (contrarian, specific, falsifiable). **8/10.**
4. **Offer specificity** - CW: $497 Signal Session, $500 SaaS Audit, both clear. SW: $500 setup + $497-$997/mo tiered, very clear. **8/10.**
5. **Follow-up depth** - 4-5 touches single-channel, no reactivation. Hormozi standard is 8 touches cross-channel + quarterly drops. **5/10.**

**Predicted Phase 3 total: ~29/50.** This is "MODIFY, don't replace" territory. The system is solid; the gap is breadth, not foundation.

The seed emails launched yesterday (CW T1 going to Apollo leads): they are Hormozi-grade by structure but missing one Big Fast Value line and one proof point. Severity 2 = ship-as-is OK for now, modify on next batch.

(Phase 3 will lock the call.)
