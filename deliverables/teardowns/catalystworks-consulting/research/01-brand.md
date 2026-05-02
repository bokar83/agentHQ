# Phase 1: Brand & Media Extraction

**Target:** https://catalystworks.consulting/
**Captured:** 2026-05-01
**Mode:** URL (live site)

---

## Identity

- **Name:** Catalyst Works
- **Title tag:** "AI Risk and Diagnostic Consulting for SMBs | Catalyst Works"
- **Meta description:** "AI governance and business diagnostic consulting for SMB owner-operators. 90-minute Signal Session: one named constraint in writing, within 24 hours. $497."
- **Twitter handle:** @catalystworks
- **Founder (named on site):** Boubacar Barry
- **Positioning words on site:** "diagnostic consulting", "AI governance", "constraint", "friction", "Signal Session"

## Visual Identity (extracted from `:root` CSS variables)

| Token | Hex | Role |
|---|---|---|
| `--navy` | `#071A2E` | Primary background |
| `--carbon` | `#1E222A` | Secondary surface |
| `--cyan` | `#00B7C2` | Primary accent (links, brand mark) |
| `--cyan-hover` | `#008F99` | Hover state |
| `--orange` | `#FF7A00` | CTA color (button bg) |
| `--orange-hover` | `#E06900` | CTA hover |
| `--clay` | `#B47C57` | Apricot accent (italic emphasis text) |
| `--mist` | `#F3F6F9` | Light surface (none seen on hero) |
| `--white` | `#FFFFFF` | Headline text |

**Palette character:** dark navy ground, two warm-cool accents (cyan + orange), one earthen italic (clay). Clear, intentional, distinctive. Not a default Bootstrap palette.

## Typography

- **Body:** Public Sans (Google Font)
- **Display / serif emphasis:** Spectral (Google Font, serif). Used for H1 ("You know something is wrong. You just can't name it.") with italic clay emphasis on "name it"

This pairing is doing the brand work. Spectral italic is the visual signature.

## Logo Asset

**File on server:** `https://catalystworks.consulting/CatalystWorks_logo.jpg` (52KB, 200 OK)

**What it looks like:** circular navy mark with a cyan arc above, a clay arc below, and "CW" wordmark in white inside a navy plate, with an orange dot accent on the C. Distinctive, brand-coded, premium.

**FINDING:** the actual logo PNG is **NOT used in the rendered site**. The header logo is HTML text (`Catalyst` + `Works` in cyan). The logo file exists at the URL only because it's the favicon. This is exactly the failure mode codified in `website-intelligence` HARD RULE #2: text-logotype substituted for the real mark. This is a Phase 2 craft-gap finding.

## Photography

- **Founder photo:** `https://catalystworks.consulting/Boubacar.JPG` (170KB, 200 OK), used on the "Not a vendor. A diagnostic partner." section
- **Hero image:** none. Hero is text-only on a navy ground with subtle grid texture.
- **Project photos:** none. Service business, not portfolio-driven.
- **OG image:** `og-image.jpg` (63KB, 1200x630), exists for social shares

## Voice Fingerprint (verbatim copy patterns)

The voice is unmistakable. Six samples that capture the pattern:

1. **"You know something is wrong. You just can't name it."** (H1)
2. **"No pitch. No proposal. Just your constraint, named."**
3. **"Structured. Not intuitive. One named constraint."**
4. **"AI didn't create your constraint. It just made it impossible to hide."**
5. **"Most consultants want a six-week discovery before they tell you anything. Catalyst Works starts differently: one conversation, one named constraint, one action."**
6. **"There is no sales pitch inside the session. The work is the pitch."**

**Pattern characteristics:**
- Short declarative sentences. Periods over conjunctions.
- Negation-then-affirmation rhythm ("Not a vendor. A diagnostic partner.")
- Concrete deliverable language ("named in writing", "in 90 minutes", "one page", "$497")
- Anti-jargon stance, calls out "discovery theatre" and "six-week discovery"
- Spectral-italic emphasis on the gut-punch phrase ("name it", written as italic clay)

## Offer Architecture (what's being sold)

| Tier | Name | Price | Promise |
|---|---|---|---|
| Free entry | Friction Audit Starter | Free | 10-signal self-diagnostic, instant score |
| Lead magnet | The Weekly Signal | Free | Newsletter: one constraint / friction pattern / insight per week |
| Paid 1 | Executive Signal Session | $497 | 90-min diagnostic, one named constraint in writing, 1-page summary in 24h. **3 sessions/month.** |
| Implied next | Diagnostic Sprint | unstated | Mentioned as "if the session reveals a constraint worth a full Diagnostic Sprint" |

**CTA stack:** every section ends in "Book a Signal Session". Single-ask discipline. The page does not try to sell the Diagnostic Sprint directly. Funnel-clean.

**Scarcity tag visible above the fold:** "3 Signal Session slots available this month".

## Information Architecture (section flow)

1. Hero, "You know something is wrong. You just can't name it." + offer card
2. The Friction Audit Starter (free 10-signal diagnostic)
3. "No pitch. No proposal. Just your constraint, named." (Signal Session intro)
4. "What you experience in 90 minutes" (3-step: interview / constraint named / written summary)
5. "Structured. Not intuitive. One named constraint." (multi-lens diagnostic explainer)
6. "You recognize at least one of these" (3 pain quotes: revenue/margin, recurring problem, key person leaving)
7. CTA section, "Ready to name your constraint?"
8. "Named in 90 minutes." (testimonial slot)
9. "Not a vendor. A diagnostic partner." (Boubacar bio)
10. "Not a gut feeling. The right way of reading a system." (methodology)
11. "AI didn't create your constraint. It just made it impossible to hide." (AI angle)
12. Final CTA, "Name your constraint. Then remove it."
13. The Weekly Signal (newsletter signup)
14. AI / customer data section (secondary lead magnet on AI risk)

## Tech Fingerprint

- **Framework:** static HTML (no React/Vue/Next bundle visible). One stylesheet (Google Fonts), one external script (GSAP 3.12.5 from cdnjs), one analytics script (GA4: G-TBW90RVMM1).
- **Hosting clue (IP):** 77.37.57.178 (Hostinger, consistent with project memory).
- **No CMS:** no WordPress, no Webflow signature.
- **Animation library:** GSAP loaded but rendered viewport shows only static text. Animation usage is minimal or scroll-triggered below the fold.

## Em-dash audit on source content

The site copy contains em-dashes in at least two confirmed paragraphs:
- "...one named constraint, written, specific, and cross-functional, plus three friction signals..."
- The FAQ JSON-LD answers contain em-dashes that will leak into Google rich snippets.

This violates the project hard rule "no em-dashes anywhere." Phase 2 finding.

## What's Already Working (carry forward to mockup, do NOT replace)

- The H1 voice ("You know something is wrong. You just can't name it.")
- The italic clay accent on emphasis words ("name it")
- The navy + cyan + orange + clay palette (do not introduce new colors)
- The single-CTA discipline ("Book a Signal Session")
- The scarcity tag ("3 slots this month")
- The $497 price stated above the fold
- Spectral italic + Public Sans pairing

## What's Missing or Broken (gaps the redesign must close)

1. **Real CW logo not used in header**, text logotype substituted for the actual brand mark. **Mockup must use the real logo PNG.**
2. **No founder photograph above the fold**, Boubacar's photo is buried in the bio section. Trust-building visual element is hidden.
3. **No hero imagery**, the hero is 100% text on a navy background. Distinctive choice, but visually thinner than peers.
4. **Em-dashes in body copy** violate stated brand rule.
5. **Logo file is favicon-only**, opportunity to use it in header, footer, and OG card.

---

## Asset inventory (downloaded to `mockups/source-media/`)

| File | Size | Use |
|---|---|---|
| `logo.jpg` | 52KB | Real CW logo mark, must appear in proposed mockup header |
| `boubacar.jpg` | 170KB | Founder photo, candidate for hero or trust-band placement |
| `og-image.jpg` | 63KB | Existing social card, reference for current visual treatment |
| `(none)` | | No project photos exist (service business, not portfolio) |
| `(none)` | | No hero photo / video exists |

End of Phase 1.
