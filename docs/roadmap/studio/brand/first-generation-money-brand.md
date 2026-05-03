# First Generation Money - Brand Bible

**Channel:** First Generation Money
**Locked:** 2026-05-03, Studio M2 build session
**Niche:** First-generation US wealth building - immigrant kids, diaspora professionals, first-gens
**Audience:** 25-45, people who never got the kitchen-table money talk
**Identity:** Zero Boubacar connection. Pure agentic test channel. Stands alone.

---

## Name & Tagline

**Channel name:** First Generation Money
**Show tagline:** *"The money talk your family never had."*
**End-card sign-off:** *"Built for first-gens. Pass it on."*
**YouTube About hook:** "Nobody taught you this. We fix that. Financial literacy for the first generation figuring it out alone."

---

## Color Palette

Vision: the mentor you never had walks into your living room - calm, knows the math, doesn't talk down to you, genuinely wants you to win. Not a Bloomberg terminal (cold, institutional). Not a personal finance hype bro (garish gradients). Something in between: warm confidence, quiet authority, a little unexpected brightness that says "this is actually achievable."

Anchor: deep forest teal-green (not stock-market green - growth that comes from patient tending, like a garden). Seconded by warm cream-gold (the kitchen table warmth this audience never had). Lifted by an unexpected electric violet pop (the surprise of finally understanding money - "wait, THIS is how it works?"). Clean, modern, trustworthy but not boring.

| Role | Name | Hex | Use |
|------|------|-----|-----|
| Primary | Grove Green | `#166B50` | Wordmark, primary CTAs, chart positive bars, anchor color |
| Secondary | First-Gen Cream | `#F7EDD8` | Background warmth, title cards, "kitchen table" feel |
| Accent 1 | Clarity Violet | `#6B3FA0` | Surprise pop for key insights, "aha moment" beats, subscribe button |
| Accent 2 | Warm Gold | `#D4922A` | Numbers, dollar amounts, IRS citations, warmth layer |
| Text | Ink Charcoal | `#1A1F2E` | Body text - slightly blue-shifted black for depth |
| Surface Dark | Deep Grove | `#0D2E20` | Dark mode bg for chart-heavy segments |
| Surface Light | Parchment White | `#FDFAF4` | Default light mode bg - warm, not clinical |
| Neutral | Stone | `#8A9099` | Captions, disclaimers, secondary labels |

**Palette logic:** Grove Green is growth that earns trust - not lottery-ticket green, not envy-green. First-Gen Cream is the kitchen table that should have existed. Clarity Violet is the unexpected "oh, I actually get this now" moment - it hits differently because nothing else on the palette is purple. Warm Gold is every dollar amount, every IRS contribution limit, every compound interest number. Together: warm enough to feel like home, credible enough to trust with your money decisions.

**Hard rules:**
- NO hype gradient backgrounds - ever
- NO red - not even in error/warning contexts (use Stone + Ink Charcoal instead)
- Clarity Violet is precious - use sparingly, for genuine insight moments only
- Light mode is the default (this audience is not dark-mode-native the way tech audiences are)
- Every dollar figure on screen gets Warm Gold treatment

---

## Typography

| Role | Font | Weight | Notes |
|------|------|--------|-------|
| Wordmark / Channel name | Plus Jakarta Sans | ExtraBold (800) | Confident, contemporary, not stuffy - first-gen energy |
| H1 / Episode title | Plus Jakarta Sans | Bold (700) | Same family, consistent authority |
| Body / explanation | Inter | Regular / Medium (400/500) | Maximum readability for financial explanation. Universal, trusted. |
| Numbers / math / citations | IBM Plex Mono | Medium (500) | "Show your work." IRS publication numbers, contribution limits, compound math. Signals rigor. |
| Legal / disclaimer | Inter | Regular, 12px, Stone color | "This is education, not advice." On every long-form. |

**Font pairing logic:** Plus Jakarta Sans is the confident first-gen who figured it out. Inter is the clear explanation. IBM Plex Mono is the receipts - every claim shown in full.

**Google Fonts URLs:**
- Plus Jakarta Sans: `https://fonts.google.com/specimen/Plus+Jakarta+Sans`
- Inter: `https://fonts.google.com/specimen/Inter`
- IBM Plex Mono: `https://fonts.google.com/specimen/IBM+Plex+Mono`

---

## Motion Vocabulary

**Pacing principle:** Content is the star. Motion should feel like a textbook that finally makes sense - clear reveals, satisfying math builds, no tricks. Whiteboard energy: "let me show you the work."

| Element | Spec |
|---------|------|
| Whiteboard draw | Path stroke animation, 1.5s `ease-in-out` - primary visual signature for diagrams |
| Number count-up | 0→final in 1.8s, IBM Plex Mono, Warm Gold `#D4922A`, brief hold at landing value |
| Chart style | Clean line or bar chart only. No 3D ever. Clarity Violet highlight on key inflection point. |
| Slide transition | Wipe right - like turning a page in a workbook. 0.4s. |
| Text reveal | Simple fade-in, 0.3s, no movement - content deserves the attention, not the animation |
| "Aha moment" beat | Clarity Violet `#6B3FA0` background flash (0.2s) on key insight. Used maximum 2× per video. |
| Disclaimer stamp | Inter 12px, Stone, fades in bottom-left on first factual claim, holds for 3s |
| Cold open | No intro sting. Opens directly on the hook statement - respects the viewer's time. |

**Never use:** Flashy intros, glitch effects, money-rain animations, luxury lifestyle B-roll (no Lamborghinis, no champagne - antithetical to the brand), anything that looks like crypto content

---

## Voice Identity

**Persona name:** The Sibling
**Character:** Gender-neutral, warm, calm. The older sibling who figured out money and came back to explain it clearly, without making you feel dumb for not knowing. Never condescending. Never hype. Sounds like a real person who respects your intelligence.
**Gender:** Gender-neutral (neutral ElevenLabs voice - not obviously male or female)
**Vendor:** ElevenLabs (primary)
**Voice ID (locked):** `X4Lh5Ftnso6JSt25plzX` (Hunter - gender-neutral, warm, calm)
**Fallback:** Kai TTS via kie_media, neutral calm voice, pace -5%
**SSML notes:**
- Slight pause before key dollar figures and percentages (`<break time="0.4s"/>`)
- Slow down on math explanations - viewer needs time to follow
- Warm but not cheery - this is serious money, not a game show
- Never rush the disclaimer read - say it clearly, not as a legal-speed blur
**Disclaimer language:** "This is financial education, not personal advice. Always consult a qualified financial professional before making investment decisions." - spoken plainly, not mumbled.

---

## Logo Spec

**Concept:** Clean wordmark-first brand. Optional icon: stacked coins morphing into an upward bar (growth from nothing). Wordmark "First Generation Money" in Plus Jakarta Sans ExtraBold. Optional short-form: "1stGen" monogram for avatar use.

**Primary wordmark layout:**
- "First Generation" in Grove Green `#166B50`, regular weight visible
- "Money" in Plus Jakarta Sans ExtraBold, larger, Warm Gold `#D4922A`
- Optional underline: Grove Green, 3px, under "Money" only

**Icon concept - image generation prompt (kie_media):**
> "Minimalist logo icon, simple upward-pointing bar chart with three ascending bars, clean geometric style, Grove Green (#166B50) bars on white background, slight warmth, no text, no gradients, vector style, square crop, centered"

**1stGen monogram (avatar use):**
> "Square monogram logo, bold letters 1stGen, Plus Jakarta Sans style, Grove Green (#166B50) letters on First-Gen Cream (#F7EDD8) background, clean geometric, no effects, centered"

---

## Avatar (YouTube Channel Icon)

**Size:** 800×800px
**Design:** "1stGen" monogram or bar-chart icon on First-Gen Cream `#F7EDD8` background. Grove Green icon/text. Clean, warm, immediately readable at small size.

**Image generation prompt:**
> "Square YouTube channel avatar, bold monogram letters 1stGen, clean modern sans-serif style, Grove Green (#166B50) on warm cream (#F7EDD8) background, slightly rounded corners on background, professional minimal, no gradients, centered"

---

## Banner (YouTube Channel Art)

**Size:** 2560×1440px - safe zone central 1546×423px
**Layout:**
- Background: Parchment White `#FDFAF4` with subtle Grove Green geometric grid (2% opacity)
- Safe zone: Channel name "First Generation Money" in Plus Jakarta Sans ExtraBold - "First Generation" in Ink Charcoal, "Money" in Warm Gold
- Below name: tagline in Inter Regular, Grove Green - *"The money talk your family never had."*
- Left accent: Clarity Violet vertical bar, 10px, full height - the unexpected pop
- Right accent: subtle IBM Plex Mono financial snippet, very low opacity (8%): `ROI · ROTH IRA · COMPOUND INTEREST · NET WORTH`

---

## End-Card Template

**Duration:** Last 20 seconds of every video
**Layout (16:9):**

```
┌──────────────────────────────────────────────────┐
│ [Grove Green top bar - 6px]                      │
│                                                  │
│  "Built for first-gens."  [Plus Jakarta Bold]   │
│  "Pass it on."            [Plus Jakarta XBold,  │
│                            Clarity Violet]       │
│                                                  │
│  [SUBSCRIBE - Grove Green btn]      [Vid tile]  │
│                                                  │
│  First Generation Money                          │
│  This is education, not advice.  [Inter 12px]   │
│                                                  │
│ [Warm Gold bottom bar - 4px]                     │
└──────────────────────────────────────────────────┘
```

**Background:** Parchment White `#FDFAF4`
**Subscribe CTA text:** "Learn More →"
**Disclaimer:** "Financial education only. Not personal financial advice."

---

## Thumbnail Template Grammar

**Layout:** Light warm bg + large number or bold question dominant + supporting visual or diagram right

**Color zones:**
- Dominant number: IBM Plex Mono, Warm Gold `#D4922A`, very large (100px+)
- Question or topic text: Plus Jakarta Sans ExtraBold, Ink Charcoal, 64px+
- Supporting visual: simple diagram, chart, or icon - never lifestyle stock photography
- Accent bar: Grove Green `#166B50`, left edge, 8px vertical bar

**Text rules:**
- Lead with a number whenever possible ("$0 to $50k" / "3 accounts" / "9 minutes")
- Max 5 words of text outside the number
- YMYL compliance: no specific investment claims in thumbnail text - educational framing only

**Do not:** Hype energy. Lamborghinis. "MAKE MONEY FAST" energy. This channel is the antidote to that.

---

## About Copy (YouTube)

```
Nobody taught you this. We fix that.

First Generation Money is financial education for the first generation figuring it out alone - immigrant kids, diaspora professionals, anyone who never got the money talk other people's families had at the kitchen table.

Credit scores. Retirement accounts. Tax-advantaged investing. Home buying. We show the work, explain the math, and skip the jargon.

New videos every week. Pass it on.

-
This channel provides financial education only. Not personal financial advice. Always consult a qualified financial professional before making investment decisions.
```

**X / Twitter bio (160 chars max):**
`Financial education for first-gens who never got the money talk. We show the math. New videos weekly. Pass it on. 💚`

---

## YMYL Compliance Checklist

Per channel brief and Studio QA Crew check #6 enforcement:

- [ ] "Financial education only, not personal advice" - spoken in every long-form
- [ ] IRS publication numbers cited for contribution limits (format: "IRS Pub. 590-A")
- [ ] Year specified for all dollar amounts and limits ("2026 Roth IRA limit: $7,000")
- [ ] No specific stock picks - ever
- [ ] No guaranteed return language - ever
- [ ] Disclaimer text in YouTube description, every video
- [ ] Studio QA Crew check #8 (YMYL guard) must pass before render

---

## Production Crew Brand Injection

Add this block to every M3 script generation prompt for this channel:

```
CHANNEL: First Generation Money
VOICE: The Sibling - gender-neutral, warm, calm, never condescending
PALETTE: Grove Green (#166B50), First-Gen Cream (#F7EDD8), Clarity Violet (#6B3FA0)
VISUAL STYLE: Whiteboard draw for diagrams, number count-ups in IBM Plex Mono/Warm Gold, wipe-right transitions
IDENTITY: Zero Boubacar connection. No names, no links, no references to other channels.
TONE: Warm authority. Older sibling who figured it out. Never hype, never scary.
YMYL RULE: Every factual money claim cites source. Education framing only. No advice, no picks.
DISCLAIMER: "This is financial education, not personal advice." - spoken plainly in every long-form.
```
