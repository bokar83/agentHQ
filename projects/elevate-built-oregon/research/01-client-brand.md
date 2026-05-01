# 01 - Client Brand Extraction

## Brand Snapshot

- **Company:** Elevate Roofing & Construction LLC
- **URL:** https://elevatebuiltoregon.com/
- **Location:** Medford, OR (serving Southern Oregon)
- **Primary Color:** `#1C4DA0` (royal blue, used in headers and primary buttons)
- **Secondary Color:** `#16163F` (deep navy, dark backgrounds)
- **Accent Color:** `#F06B32` (terracotta/orange, used sparingly)
- **Highlight Color:** `#F8F812` (bright yellow, used 10x in CSS - likely CTA badges or callouts)
- **Warm Neutral:** `#D3B574` (tan/khaki)
- **Body Text:** `#54595F` (warm gray, default Elementor)
- **Fonts:** Montserrat (headings, 18 references) / Archivo (body, 13 references) - both also Roboto + Roboto Slab loaded but unused in rendered CSS
- **Tone:** Plain-spoken, lightly self-aware, confident-but-warm ("We got you covered (literally).")
- **Core Message:** "We handle the construction so you can focus on what matters most - protecting the people and things that matter to you."

---

## 1. Identity

- **Legal name:** Elevate Roofing & Construction LLC
- **Tagline:** *Elevate Your Expectations*
- **License:** CCB# 257092 (Oregon Construction Contractors Board)
- **Status:** Licensed, Bonded & Insured
- **Founder (inferred from testimonials):** "Rod" - referenced by name in all three reviews; not yet introduced on the site itself
- **Years in business:** 20+ years of experience claimed (likely combined founder experience, not company age - the LLC and CCB# look recent, and copyright reads `2025`)

## 2. Contact

- **Phone:** 458-488-3710
- **Email:** obfuscated as `[email protected]` (likely Cloudflare-style email protection)
- **Form fields:** First Name · Phone · Email · "How can we help you?"
- **Service Area:** Southern Oregon (Medford-based)
- **Business hours:** not published
- **Social media:** none listed

## 3. Site Architecture (current)

| URL | Status |
|---|---|
| `/` (Home) | **Live** - full hero, services teaser, testimonials, contact form |
| `/services/` | "Coming soon..." placeholder |
| `/roofing/` | "Coming soon..." placeholder |
| `/remodels-custom-homes/` | (not verified, in nav) |
| `/decks-fences/` (labeled "New Home Construction") | (in nav, naming mismatch) |
| `/other-cool-stuff/` (labeled "Custom Projects") | (in nav, naming mismatch - humorous slug) |
| `/gallery/` | "Coming soon..." placeholder |
| `/about/` | "Coming soon..." placeholder |
| `/contact-us/` | **Live** - minimal form + license footer |

> **Critical finding:** **5 of 9 pages are placeholders.** The site is functionally a one-pager. About, gallery, and individual service pages all show "Coming soon..." - the entire credibility/portfolio layer is missing. Slugs `decks-fences` and `other-cool-stuff` don't match the nav labels they sit under, suggesting the IA is mid-edit.

## 4. Tech Stack

- **CMS:** WordPress 6.9.4
- **Theme:** Hello Elementor (the bare-bones starter theme)
- **Page builder:** Elementor 4.0.5
- **Analytics:** Site Kit by Google 1.177.0 (so GA4 is wired)
- **Font loader:** Google Fonts (Archivo, Montserrat, Roboto Slab, Roboto - *all four families are loaded, only two are used*; that's a measurable performance hit)
- **Email obfuscation:** Cloudflare-style `[email protected]`
- **No** custom theme, no Yoast/RankMath visible, no schema markup, no Open Graph tags

## 5. Brand Assets

| Asset | URL |
|---|---|
| Primary "E" logomark | https://elevatebuiltoregon.com/wp-content/uploads/2026/01/E-Logo-Picsart-BackgroundRemover.png |
| Wordmark (black, transparent) | https://elevatebuiltoregon.com/wp-content/uploads/2026/01/Simple-Black-Logo-No-Background-768x212.png |
| Footer logo (300x84) | https://elevatebuiltoregon.com/wp-content/uploads/2026/01/Main-Logo-background-removed-Picsart-BackgroundRemover-300x84.png |
| Favicon (32) | https://elevatebuiltoregon.com/wp-content/uploads/2026/01/cropped-E-Logo-Picsart-BackgroundRemover-32x32.png |
| Favicon (192) | https://elevatebuiltoregon.com/wp-content/uploads/2026/01/cropped-E-Logo-Picsart-BackgroundRemover-192x192.png |
| Hero/section background photo | https://elevatebuiltoregon.com/wp-content/uploads/2026/02/2160-1-2048x767.jpg |
| Secondary background photo | https://elevatebuiltoregon.com/wp-content/uploads/2025/11/20250913_155234-1536x1152.jpg |

> Logos appear to be processed through Picsart's free background remover - visible in filenames. That's a tell that the brand assets are DIY, not from a designer.

## 6. Verbatim Copy (homepage)

### Hero
> **ELEVATE YOUR EXPECTATIONS**
> At Elevate, we understand that maintaining, remodeling or building your home or roof is about protecting the people and things that matter most.
> We do what we do best, so you can focus on what matters most.
>
> [Request a Quote]

### Services grid

- **Roofing** - Residential and Commercial. New, reroof and repair. We got you covered (literally).
- **Remodels & ADU** - Bring your own plans and ideas or design + build.
- **New Homes** - Bring us your finished plans or your big ideas. We partner with engineers and architects for a streamlined design build experience.
- **Custom Projects** - Unique ideas require expertise and experience. Fortunately, we have both.

### Differentiators

- **Expertise** - Specialists in premium roofing, custom homes, remodels, and unique, one of a kind projects.
- **Experience** - 20+ years navigating both the complexities of multi-million dollar commercial sites as well as the details of residential projects.

### Testimonials section
> **Don't just take our word for it**

- **Elana** ★★★★★ - *"Elevate did a great job. Rod listened to our ideas and brought them to reality. I couldn't be happier! They are professional, respectful and tidy."*
- **Michael** ★★★★★ - *"Rod and his crew were very professional, timely, communicative, and attentive to details. We know we got quality for a great price."*
- **Susan** ★★★★★ - *"Rod was so wonderful to work with. He paid attention to every little detail. He helped us recognize what needed to be done to maintain our home. We will definitely hire him again!"*

### Footer
> Licensed, Bonded & Insured. CCB# 257092
> © 2025 Elevate Roofing & Construction LLC

## 7. Voice & Tone

- **Register:** Professional but plain-spoken. No jargon. No corporate puffery.
- **Tells of the founder's voice:**
  - *"We got you covered (literally)."* - slight wink, contractor humor
  - *"Bring your own plans and ideas or design + build."* - addresses the customer directly
  - *"Unique ideas require expertise and experience. Fortunately, we have both."* - confident but light
  - *"Other Cool Stuff"* (URL slug) - playful, low-corporate
- **Voice descriptors:** confident, warm, plainspoken, lightly humorous, partnership-oriented
- **Avoids:** "trusted partner," "passionate about," "industry-leading," "your vision is our mission" - the standard contractor cliches

## 8. SEO/Conversion Posture (current)

| Element | Present? |
|---|---|
| `<title>` set | ❌ Empty |
| Meta description | ❌ Missing |
| Open Graph tags | ❌ Missing |
| Twitter cards | ❌ Missing |
| Canonical URL | ✅ Set |
| Favicon (16/32/192) | ✅ Set |
| Schema.org markup (LocalBusiness, RoofingContractor) | ❌ Missing |
| H1 hierarchy | ⚠️ Unverified - Elementor often emits multiple H1s |
| Alt text on images | ⚠️ Unverified |
| Sitemap.xml | ⚠️ Unverified |
| GA4 (Site Kit) | ✅ Loaded |
| Google Reviews integration | ❌ Hardcoded testimonials, no live review pull |
| Lead capture beyond contact form | ❌ Single CTA, no quote calculator, no lead magnet |
| Phone CTA tap-to-call on mobile | ⚠️ Unverified |
| Trust badges (BBB, Angi, GAF, Owens Corning) | ❌ Only the CCB# license number, no logos |

## 9. Homepage Build Quality

- Built in Elementor with mostly default block colors leaking into the markup (the `#ff6900`, `#fcb900`, `#cf2e2e` hex values are Gutenberg block defaults, not used visually)
- Four full Google Font families loaded - only two rendered. Roughly 200KB+ of unused font CSS.
- No hero video, no scroll animation, no parallax, no interactive elements
- Hero is a static photo overlay
- The Hello Elementor theme is intentionally minimal - there's no design system on top of it

## 10. What This Tells Us About the Build Brief

1. **The site is a placeholder, not a finished site.** Treat the rebuild as the *first real site*, not a redesign.
2. **There is no portfolio.** A roofing/construction company without a project gallery is missing the single highest-converting asset in the trade. This is the #1 fix.
3. **There is no "About Rod" page.** A solo-founder GC's biggest differentiator is the founder. The site hides him.
4. **The voice is good - keep it.** "We got you covered (literally)" and "Other Cool Stuff" are the brand. Don't sand them off.
5. **The palette is loud.** Royal blue + bright yellow + terracotta + khaki + sky blue is five competing accents. Tighten to navy + one warm accent + neutrals.
6. **No SEO foundation.** Empty `<title>`, no meta description, no OG, no schema. Easy wins.
7. **No social proof beyond 3 testimonials.** Need: project count, years in business, CCB# prominently displayed, manufacturer certs (GAF Master Elite, Owens Corning Preferred, etc. - verify which they hold), Google Reviews live pull.
