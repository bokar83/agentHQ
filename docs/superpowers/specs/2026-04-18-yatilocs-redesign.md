# Yati Locs Website Redesign — Design Spec
**Date:** 2026-04-18  
**Repo:** bokar83/yatilocs-site  
**Live URLs:** yatilocs.com / yatifirecutz.com  
**Branch strategy:** `dev` (shared build base), `main` (Version A — Cinematic Warmth), `culture` (Version B — Bold Culture-First)

---

## 1. Brief

Yati is Dubai's premier locs specialist serving the Black and African diaspora across income levels. The site must feel cinematic and premium while also warm, rooted, and culturally specific. The gap in the Dubai market: every competitor (XHair, Barber Republic, Chaps & Co) uses cold luxury — dark backgrounds, gold accents, no cultural identity. Yati owns the cultural identity lane. That is the differentiator.

Two builds will split-test on the existing dual-URL setup:
- `yatilocs.com` → `main` branch → **Version A: Cinematic Warmth**
- `yatifirecutz.com` → `culture` branch → **Version B: Bold Culture-First**

Both share identical structure, copy, and assets. Only palette, typography, and texture layer differ.

---

## 2. Shared Structure (Both Versions)

### Sections (in order)
1. **Nav** — Sticky, minimal. Logo left. "Book Now" CTA right (WhatsApp deep link). Transparent over hero, solid on scroll.
2. **Hero** — Full-viewport. Video background (YatiVideo_01.mp4 as primary, fallback to hero image). Cinematic overlay. H1 + tagline + two CTAs.
3. **Social Proof Strip** — Thin bar below hero. Google/Instagram review count placeholder + "Dubai's #1 Locs Specialist" positioning line.
4. **Art in Action (Gallery)** — Masonry grid. All 18 photos + 7 videos. Lightbox on click. Lazy loaded.
5. **Our Craft (Services)** — 6 service cards. Elegant, no emoji. Price range optional.
6. **The Locsmith's Legacy** — Full-width cinematic split. Logo/brand mark left, copy right. Improved copy (see section 5).
7. **Secrets of the Locsmith (Tips)** — 5 tips, styled as editorial pull-quotes or numbered list.
8. **Footer** — Social links, WhatsApp CTA, email signup (Formspree wired), copyright.

### Fixed Elements
- Floating WhatsApp button (bottom-right, always visible on mobile)
- `prefers-reduced-motion` respected on all animations

---

## 3. Version A — Cinematic Warmth (`main` branch)

### Palette
```
--color-bg:        #0D0B08   (near-black, warm)
--color-surface:   #1A1612   (card backgrounds)
--color-gold:      #C9A84C   (primary accent)
--color-cream:     #F5EDD6   (text on dark)
--color-terracotta:#B85C38   (secondary accent, CTAs)
--color-muted:     #7A6E62   (secondary text)
```

### Typography
- **Display/H1:** Cormorant Garamond (serif, editorial weight 700) — cinematic, literary
- **Headings H2/H3:** Cormorant Garamond 600
- **Body:** DM Sans 400/500 — clean, readable, warm
- **Accent/labels:** DM Sans 600 uppercase letterspaced

### Animations
- Hero: Ken Burns slow zoom on video/image, text fades in with staggered delay
- Scroll reveals: fade-up on all section entries (Intersection Observer, 60px offset)
- Gallery: hover scale 1.03 + overlay text reveal
- Service cards: subtle border glow on hover
- Nav: smooth background transition on scroll
- Floating WhatsApp: pulse ring animation

### Hero copy (Version A)
```
H1: Your Crown Deserves a Master
Subhead: Dubai's premier locs & Black hair specialist.
        Culture. Care. Craft.
CTA1: See the Work  CTA2: Book with Yati →
```

---

## 4. Version B — Bold Culture-First (`culture` branch)

### Palette
```
--color-bg:        #1A0F2E   (deep indigo/night)
--color-surface:   #251840   (card backgrounds)
--color-gold:      #F4A925   (vivid amber/kente gold)
--color-cream:     #FDF6E3   (warm white)
--color-accent:    #E8563A   (burnt orange)
--color-pattern:   rgba(244,169,37,0.06) (Kente texture overlay)
```

### Typography
- **Display/H1:** Bebas Neue — bold, loud, commanding (all-caps display)
- **Headings H2/H3:** Outfit 700
- **Body:** Outfit 400
- **Accent:** Outfit 600 uppercase

### Visual Texture
- Subtle Kente-inspired geometric SVG pattern as repeating background overlay (low opacity, CSS background-image)
- Section dividers use diagonal cut angles (clip-path) instead of straight lines
- Service cards have a thin gold border-left accent

### Hero copy (Version B)
```
H1: THE LOCSMITH IS IN DUBAI
Subhead: Black hair. World class hands. Book your crown today.
CTA1: See the Work  CTA2: Book Now →
```

---

## 5. Copy Improvements

### Legacy Section (both versions)
**Current (weak):** "With years of hands-on experience, Yati has lived the loc journey..."

**Revised:**
> Yati didn't just learn locs. He lived them.  
>  
> From his first set of starter locs to the flourishing crowns he tends today, every technique he uses is something he has worn, tested, and refined on himself. That is what sets him apart in Dubai — not just the skill, but the lived understanding of what your hair needs at every stage of the journey.  
>  
> Whether you are starting fresh or maintaining a crown you have carried for years, you are in hands that know the path. Because Yati has walked it too.

### Services (rename from emoji to clean headings)
- Loc Creation — Starter Locs
- Maintenance and Retwist
- Loc Styling — Barrel Rolls, Updos, Twists
- Wash and Deep Conditioning
- Scalp Detox and Hydration
- Beard Grooming and Lining

### Gallery intro (both versions)
**Revised:** "Every photo is a real transformation. Every video is a real moment from the chair. This is what Yati does — not just hair, but craft."

---

## 6. SEO Fixes (Critical — Both Versions)

### Missing elements to add
- **H1 tag** on hero (currently missing entirely)
- **robots.txt** — allow all, sitemap pointer
- **sitemap.xml** — single-page, manual
- **OG meta tags** — og:title, og:description, og:image (use Yati_01.jpg)
- **Twitter/X card meta**
- **LocalBusiness schema** (JSON-LD): name, address (Dubai), phone, url, openingHours, sameAs (Instagram, TikTok)
- **Service schema** for each of the 6 services
- **Canonical tag**
- **Image alt text** — keyword-rich rewrites for all 18 photos (e.g., "Yati Locs Dubai starter locs transformation")

### Target keywords (primary)
- "locs specialist Dubai"
- "Black hair Dubai"
- "dreadlocks Dubai"
- "locs barber Dubai"

### Target keywords (secondary)
- "starter locs Dubai"
- "loc retwist Dubai"
- "African hair Dubai"
- "loc maintenance Dubai"

### Meta tags
```
Title: Yati Locs — Dubai's Premier Locs & Black Hair Specialist
Description: Expert locs creation, maintenance, styling and Black hair care in Dubai. 
             Book with Yati — the go-to locs specialist for Dubai's African diaspora. 
             WhatsApp +971558487022.
```

---

## 7. Technical Requirements

- Pure HTML/CSS/JS — no build tooling, matches current repo pattern
- Google Fonts via `<link rel="preconnect">` + `display=swap`
- Formspree for email signup (free tier, POST action)
- All videos: `autoplay muted loop playsinline` — critical for iOS
- `loading="lazy"` on all below-fold images
- Explicit `width` and `height` on all `<img>` tags (prevent CLS)
- `touch-action: manipulation` on all buttons
- Floating WhatsApp button: `position: fixed`, z-index 9999
- `prefers-reduced-motion` media query wrapping all keyframe animations
- No `transition: all` anywhere
- All icon buttons get `aria-label`
- Form inputs get `autocomplete`, `name`, correct `type`
- `text-wrap: balance` on all headings

### Files to rename
- `hero-placeholder.png` → `yati-hero-bg.jpg` (or keep if AI-generated image, just rename)
- `yati-placeholder.png` → `yati-locs-logo.png`

### New files to create
- `robots.txt`
- `sitemap.xml`
- `CNAME` (if needed for Hostinger)

---

## 8. Branch + Deploy Strategy

```
main   → yatilocs.com       → Version A (Cinematic Warmth)
culture → yatifirecutz.com  → Version B (Bold Culture-First)
dev    → local development  → shared base, branch from here
```

Build order:
1. Build Version A on `dev`, test on localhost
2. Push `dev` → merge to `main` → yatilocs.com live
3. Branch `culture` from `main`
4. Apply Version B palette/typography/texture changes on `culture`
5. Push `culture` → yatifirecutz.com points to `culture` branch

---

## 9. Out of Scope (This Build)

- Online booking system beyond WhatsApp (Phase 2)
- Pricing page
- Blog/content section
- Testimonials carousel (needs real reviews collected first)
- GA4 tracking (add in Phase 2 once Yati confirms analytics access)
