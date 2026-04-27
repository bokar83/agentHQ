# Signal Works :  Design Spec
**Date:** 2026-04-27
**Status:** APPROVED FOR BUILD :  Monday April 27
**Goal:** First signed contract by Friday May 2. First automated email Tuesday April 28.

---

## What Signal Works Is

An AI Presence Agency that makes local businesses findable when people ask AI tools for recommendations. Not a web design agency. Not an SEO agency. The positioning sentence:

**"We make your business the one AI recommends."**

Signal Works is an adjacency to Catalyst Works. Same founder, adjacent problem, different entry product. Catalyst Works transforms businesses strategically. Signal Works makes them visible to AI-powered discovery.

---

## The Problem It Solves (Honest and Defensible)

60%+ of local businesses have outdated or no websites. More critically, almost none of them appear when potential customers ask ChatGPT, Perplexity, Google AI Overviews, or Gemini for recommendations in their niche and city. This is measurable, demonstrable, and fixable.

**What we can prove before the first call:**
- Run their business through the Semrush AI Visibility Checker (free): shows 0-100 score
- Query ChatGPT/Perplexity with "[niche] in [city]": show screenshot of who appears (not them)
- Check their robots.txt: GPTBot/PerplexityBot often blocked (automatic invisibility)
- Check Bing Places: most local businesses are unclaimed (ChatGPT uses Bing heavily)

---

## The Service Stack

### Tier 1 :  AI Presence Starter: $500 setup + $497/month
For simple businesses: no existing site or basic single-service operation.

**What's included:**
- Fast mobile-optimized site built and hosted on Boubacar's infrastructure
- LocalBusiness + FAQ + Service schema markup implemented
- Bing Places claimed and fully optimized (the overlooked ChatGPT key)
- NAP audit across 10 directories, inconsistencies corrected
- robots.txt fixed to allow GPTBot, PerplexityBot, ClaudeBot
- Automated review collection (SMS post-service)
- Monthly AI Visibility Report (ChatGPT, Perplexity, Google AI Overviews, Gemini)

### Tier 2 :  AI Presence Pro: $1,000 setup + $797/month
For established businesses with existing site, higher review counts, competitive niche.

**Everything in Tier 1 plus:**
- Full site rebuild or deep optimization of existing site
- 20-directory citation audit and correction
- Monthly answer-format content (2 pieces targeting niche + city queries)
- Competitor gap analysis in AI Visibility Report
- Missed-call AI text-back bot (GHL or n8n based)

### Tier 3 :  AI Presence Complete: $2,500 setup + $997/month
For multi-location, complex businesses, or any client requiring database/booking integration.

**Everything in Tier 2 plus:**
- Custom site with booking system, intake forms, database
- Full AI agent (Base44) for lead qualification + appointment booking
- Weekly content updates
- Monthly strategy call (30 min)
- First-mover vertical lock-in: Boubacar will not take a competing client in same niche + city

---

## What We Guarantee (Contractually Safe)

**We guarantee the inputs, not the outputs.**

Specific deliverables guaranteed per month:
- Site uptime 99.9% (monitored via UptimeRobot)
- Schema markup maintained and updated
- Bing Places kept current
- Review bot active and firing
- Monthly AI Visibility Report delivered by the 5th of each month
- 2 content pieces published (Tier 2+)

**We do not guarantee:**
- Specific appearance in any AI tool for any query
- Number of leads or calls generated
- Google ranking position

**The honest framing for clients:**
"AI search algorithms are controlled by Google, OpenAI, and others. What I control is making sure you have the best possible infrastructure so that when those algorithms surface businesses, yours is set up to be found. Think of it like making sure you're in the phone book and the business directory and the chamber listing :  except for the AI era."

---

## Target Niches (First 90 Days)

Two niches only. Pick depth over breadth.

**Niche A :  Healthcare/Professional Services (Highest AI visibility potential):**
- Pediatric dentists
- Chiropractors
- Physical therapists
- Mental health counselors

**Niche B :  Home Services (Harder AI visibility but massive market):**
- Roofers
- Landscapers/lawn care
- HVAC (if running paid ads = confirmed budget)
- Painters

**Geographic focus:** Salt Lake City + greater Utah first. Then expand nationally in these two verticals.

**Lead qualifier (all must pass):**
- 20-100 Google reviews (established and can pay)
- Website that is outdated OR no website
- Running Google/Facebook ads OR 50+ reviews (indicates budget)
- NOT a brand new business (under 6 months, under 20 reviews = skip)

---

## The Monday Build Plan (April 27)

### Hard constraint: 8 hours. Everything not done by 6 PM ships as-is.

**Block 1: 8 AM - 12 PM :  Lead Pipeline (4 hours)**

1. Wire Google Maps scraper in agentsHQ for Signal Works:
   - Input: niche keyword + city
   - Filter: no website OR outdated site + 20-100 reviews
   - Output: Supabase leads table with tag `signal_works`, fields: name, phone, email, website_url, review_count, google_maps_url
2. Firecrawl integration: for each lead with a site, scrape homepage for quick content audit
3. AI Visibility Score script (Python):
   - Input: business name + city + category
   - Queries: ChatGPT API "best [category] in [city]" + Perplexity same query
   - Parse response for business name mention
   - Score: 0/25 per tool (ChatGPT, Perplexity, Google AI Overviews manual, Gemini manual) = 0-100
   - Output: score per lead added to Supabase
4. Run pipeline on first target: 25 leads, Salt Lake City, dentists + roofers

**Block 2: 12 PM - 3 PM :  Demo Assets (3 hours)**

1. Build ONE Volta-standard demo site for dentist niche (uses existing frontend-design skill)
   - Business name: "Valley Family Dental" (generic placeholder)
   - Deploy to Vercel: demo-dental.vercel.app or similar
   - Full schema markup implemented
2. Build ONE demo site for roofer niche
   - Deploy to Vercel: demo-roofing.vercel.app
3. Record one 90-second Loom per niche:
   - Show real business AI Visibility Score vs competitor
   - Show demo site
   - "Here is what yours could look like"

**Block 3: 3 PM - 5 PM :  Outreach Infrastructure (2 hours)**

1. Cold email template finalized (Signal Works version, NOT Catalyst Works):
   - Subject: "ChatGPT doesn't know [Business] exists :  your AI score: [X]/100"
   - Body: Loom link, one observation, Calendly CTA
   - Personalization fields: business_name, owner_name, score, loom_url
2. 10 emails queued with personalization filled from lead list
3. Send time: Tuesday April 28, 8:00 AM MT
4. Instagram DM script written (text + voice message version)
5. Calendly: "Signal Works Discovery Call" :  30 min, Tuesday-Friday slots
6. Stripe: three payment links at $497/mo, $797/mo, $997/mo (monthly recurring)
7. Setup fee Stripe links: $500, $1,000, $2,500

**Block 4: 5 PM - 6 PM :  Contract and Close (1 hour)**

1. One-page Signal Works Service Agreement:
   - What we deliver (inputs list)
   - What we do not guarantee (outputs)
   - Monthly fee and setup fee
   - 30-day cancellation clause
   - Hosting ownership clause (Boubacar owns infrastructure)
   - Signature block
2. Upload to HelloSign or DocuSign
3. Test the full end-to-end: email receives -> books call -> demo shared -> contract sent -> paid via Stripe

---

## Tuesday April 28 :  Launch Day

- 8:00 AM: 10 cold emails send automatically
- 9:00 AM - 9:20 AM: 10 Instagram DMs sent manually (dentists and landscapers with visual portfolios)
- Check for opens/replies at noon
- Any reply within 2 hours gets a personal follow-up the same day
- Goal: 2-3 calls booked by end of Tuesday

---

## Wednesday-Friday May 1 :  Close Week

**Every call follows this structure (30 minutes):**

- Min 0-8: Discovery :  "How do new customers find you?" / "Do you know where you show up when someone asks AI for [service]?"
- Min 9-18: Demo :  Share screen. Show their AI score. Show the demo site. Show Bing Places unclaimed. "Here is what we fix."
- Min 19-25: Close :  "This is $[tier] setup and $[tier]/month. First month I will deliver [specific quick wins] and we will measure your score before and after. Want to move forward?"
- Min 26-30: If yes: send contract link + setup fee payment link before they hang up

**Target by Friday May 2:**
- 5-10 calls completed
- 2-3 contracts sent
- 1 signed + paid

---

## The AI Visibility Score Tool (Spec)

**Input:** business_name, city, category (e.g. "Valley Dental", "Salt Lake City", "pediatric dentist")

**Process:**
```python
# For each of 4 queries:
queries = [
    f"best {category} in {city}",
    f"top {category} near {city}",
    f"recommend a {category} in {city}",
    f"who is the best {category} in {city}"
]
# Query ChatGPT API (gpt-4o with web browsing disabled for speed)
# Query Perplexity API
# Check robots.txt for GPTBot/PerplexityBot blocks
# Check if Bing Places listing exists and is claimed
```

**Scoring:**
- ChatGPT mentions business: +25
- Perplexity mentions business: +25
- Bing Places claimed and complete: +25
- robots.txt allows AI crawlers: +25
- Total: 0-100

**Output:** JSON with score, breakdown, and three quick wins (what to fix first)

**This is honest:** The score measures infrastructure readiness and known citation sources. It does not claim to predict all AI behavior. It is defensible and useful.

---

## Tech Stack

| Component | Tool | Status | Cost |
|---|---|---|---|
| Lead scraper | agentsHQ Google Maps scraper | EXISTS | $0 |
| Lead storage | Supabase | EXISTS | $0 |
| Site builder | agentsHQ frontend-design skill | EXISTS | $0 |
| Site hosting | Vercel | EXISTS | $0 (free tier for demos) |
| Site scraping | Firecrawl | EXISTS | $0 (credits available) |
| AI Visibility Score | Build Monday | BUILD | ~$2-5/100 leads (API cost) |
| Email outreach | Gmail sequences or existing tool | EXISTS | $0 |
| Booking | Calendly | EXISTS | $0 |
| Payment | Stripe | EXISTS | 2.9% + $0.30/transaction |
| Contract | HelloSign (3 free/month) or DocuSign | NEED | $0-15 |
| Client site hosting | Vercel Pro or Hostinger | NEED | $20/month at client 1 |
| Uptime monitoring | UptimeRobot | NEED | $0 (free tier) |
| AI Visibility monitoring | Semrush free checker + OtterlyAI | NEED | $0 free / $50+ paid |
| Screen recording | Loom | EXISTS | $0 (free tier) |
| CRM | Supabase + Notion (existing) | EXISTS | $0 |

**Total new cost Monday: $0 for launch. $20-50/month at first client.**

---

## The 10-Day Contract Clock

| Day | Action | Goal |
|---|---|---|
| Mon Apr 28 | Full build day | Pipeline + demo sites + contract ready |
| Tue Apr 29 | 10 emails auto-sent + 10 Instagram DMs | 2-3 call bookings |
| Wed Apr 30 | Follow-up calls, first Discovery calls | 1-2 calls completed |
| Thu May 1 | More calls, contract sends | 2-3 contracts out |
| Fri May 2 | Close week ends | 1 signed contract |
| Mon May 5 | Second email batch (10 new leads) | Pipeline growing |
| Tue May 6 | More calls | |
| Wed May 7 | Target: 2nd signed contract | $1K-$2K MRR |
| Thu May 8 | Deliver client 1 first deliverables | Quick wins visible |
| Fri May 9 | **Day 11: Review state** | 1-3 clients, MRR established |

---

## Personal Guardrails (Boubacar-Specific)

Based on documented patterns in memory:

1. **No new ideas on Monday.** Build only what is in this spec. Every new idea goes in a parking lot doc. Nothing added to Monday's build.

2. **Hard stop at 6 PM Monday.** Whatever is built ships. Imperfect pipeline beats perfect pipeline that never launches.

3. **One revenue action per day, logged.** Before any agentsHQ work, the daily revenue action happens first: one email sent, one follow-up made, one call booked, one contract sent, one invoice paid.

4. **Signal Works work is logged separately from agentsHQ atlas work.** They do not bleed into each other. Different Calendly. Different Supabase tag. Different focus window.

5. **The YouTube channel does not exist until client 1 result is in hand.** This is a hard gate. No channel, no videos, no thumbnails, no channel name decisions until after May 2.

6. **If a call results in "I need to think about it":** Send the contract link anyway. Say "I will leave this open for 48 hours. The demo site I built for you will stay live until then." Creates urgency without pressure.

---

## Signal Works Notion Ideas DB Entry

To be added to the Ideas DB:

**Title:** Signal Works :  AI Presence Agency
**Status:** Active Sprint
**Domain:** Signal Works (new)
**Description:** AI Presence Agency adjacent to Catalyst Works. Makes local businesses visible to AI search tools (ChatGPT, Perplexity, Google AI Overviews, Gemini). Entry product: AI-optimized website + GEO infrastructure + monthly AI Visibility Report. Unique differentiator: GEO optimization + multilingual global reach + Catalyst Works diagnostic methodology. First niche: dentists + roofers, Salt Lake City. Price: $500 setup + $497-997/month. Target: 3 signed clients by May 9.
**Revenue path:** Website biz + Recurring service
**Effort:** Low-Medium
**Upfront capital:** $0
**Time to first dollar:** 10 days

---

## Name and Brand

**Agency name:** Signal Works
**Tagline:** We make your business the one AI recommends.
**Relationship to Catalyst Works:** Adjacent brand, same founder. Catalyst Works = strategic transformation. Signal Works = AI visibility execution.
**Visual identity:** TBD after first client. Use Boubacar's existing personal brand for credibility until then.
**Domain:** Check availability: signalworks.ai / signalworks.co / signalworks.agency

---

## What NOT to Build Monday

- White-label platform for other agencies
- YouTube channel or any video content
- French Africa or MENA materials
- Signal Works website (use a simple one-pager or nothing :  client credibility comes from Boubacar's LinkedIn and Catalyst Works, not Signal Works' own site)
- Any new agentsHQ infrastructure beyond what is needed for the pipeline
- Any branding beyond a name and tagline
