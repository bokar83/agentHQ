---
version: alpha
name: Under the Baobab
description: Faceless African storytelling channel. Griot voice, earthy warmth, West African textile soul.
colors:
  primary: "#C4622D"
  primary-dark: "#A04E22"
  primary-light: "#F5E6DC"
  gold: "#D4A017"
  gold-light: "#F9EEC4"
  indigo-night: "#1B1F4A"
  indigo-mid: "#2D3270"
  baobab-brown: "#6B3E26"
  ochre: "#E8A838"
  terracotta: "#B85C38"
  cream: "#FAF3E8"
  surface: "#FFF8F0"
  text-primary: "#2C1810"
  text-secondary: "#5C3D2E"
  text-muted: "#8B6555"
  border: "#DCC4B0"
typography:
  display:
    fontFamily: "Fraunces"
    fontSize: "52px"
    fontWeight: 700
    lineHeight: 1.1
    letterSpacing: "-0.02em"
  heading:
    fontFamily: "Fraunces"
    fontSize: "32px"
    fontWeight: 600
    lineHeight: 1.25
    letterSpacing: "-0.01em"
  body:
    fontFamily: "Source Serif 4"
    fontSize: "17px"
    fontWeight: 400
    lineHeight: 1.7
    letterSpacing: "0"
  caption:
    fontFamily: "Public Sans"
    fontSize: "13px"
    fontWeight: 500
    lineHeight: 1.4
    letterSpacing: "0.04em"
  eyebrow:
    fontFamily: "Public Sans"
    fontSize: "11px"
    fontWeight: 600
    lineHeight: 1.4
    letterSpacing: "0.12em"
rounded:
  sm: "4px"
  md: "8px"
  lg: "16px"
  xl: "24px"
  full: "9999px"
spacing:
  xs: "4px"
  sm: "8px"
  md: "16px"
  lg: "24px"
  xl: "40px"
  "2xl": "64px"
  "3xl": "96px"
components:
  button-primary:
    backgroundColor: "{colors.primary}"
    textColor: "{colors.cream}"
    typography: "{typography.caption}"
    rounded: "{rounded.sm}"
    padding: "12px 28px"
  button-secondary:
    backgroundColor: "transparent"
    textColor: "{colors.primary}"
    typography: "{typography.caption}"
    rounded: "{rounded.sm}"
    padding: "11px 27px"
  card:
    backgroundColor: "{colors.surface}"
    textColor: "{colors.text-primary}"
    rounded: "{rounded.lg}"
    padding: "{spacing.lg}"
  end-card:
    backgroundColor: "{colors.indigo-night}"
    textColor: "{colors.cream}"
    rounded: "{rounded.md}"
    padding: "{spacing.xl}"
---

## Overview

Under the Baobab is a griot sitting under the oldest tree in the village — unhurried, rooted, carrying stories that predate your grandparents. The visual language pulls from West African textile traditions: kente geometry, mudcloth pattern density, Adinkra symbolic weight. Warm ochre and terracotta are the dominant earth; deep indigo is the night sky where stories live. Gold appears like firelight — not decoration, signal. This brand should feel like heritage, not nostalgia. Ancient but alive.

Emotional intent: warmth, wonder, rootedness. The audience should feel seen and held, not lectured.

## Colors

**Primary — Terracotta Fire** `#C4622D`: active states, links, key highlights. Drawn from fired clay and kente weft threads. Never use on large backgrounds — it is an accent that earns attention.

**Gold — Firelight** `#D4A017`: section highlights, icon accents, animated elements. Not luxury gold — firelight gold. Used sparingly, it signals something worth paying attention to.

**Indigo Night** `#1B1F4A`: hero backgrounds, end-cards, video frame base. The night sky where the griot tells stories. Deep, still, holding.

**Baobab Brown** `#6B3E26`: borders, dividers, decorative textile motif elements. The color of the tree itself.

**Ochre** `#E8A838`: warm section backgrounds, callout highlights. Sahel sand, afternoon light.

**Cream** `#FAF3E8`: text on dark surfaces, light surface base. Not white — warm cream. White would break the organic palette.

**Text Primary** `#2C1810`: all body copy. Rich dark brown, not black. Warmer and less jarring against the cream/ochre surfaces.

## Typography

**Display — Fraunces 700:** Story titles, channel name lockup, hero headlines. Fraunces is an optical serif with ink-trap details — it has age and personality without being stiff. Pairs with the griot voice.

**Heading — Fraunces 600:** Section headers, episode titles, card titles. Same family, lighter weight for hierarchy.

**Body — Source Serif 4 400:** All narrative body copy, story descriptions, parenting-content prose. Serif for warmth and readability in longer reads.

**Caption / Eyebrow — Public Sans:** Metadata, region tags, episode numbers, platform labels. Clean sans for contrast against the editorial serif stack.

**Font import:**
```html
<link href="https://fonts.googleapis.com/css2?family=Fraunces:wght@600;700&family=Source+Serif+4:wght@400;600&family=Public+Sans:wght@400;500;600&display=swap" rel="stylesheet">
```

## Layout

12-column grid, max-width 1100px. Asymmetric layouts preferred — content-heavy left column, visual-right with textile pattern or illustration. Generous vertical spacing: minimum 64px between sections. Cards use staggered layout (not uniform grid) to echo organic, handcrafted feel. Never three equal columns in a row — it reads as SaaS, not storytelling.

## Elevation & Depth

Depth through layering, not shadows. Textile-pattern overlays at 8-12% opacity behind content blocks. Warm border instead of drop-shadow on cards (`1px solid #DCC4B0`). Video frames use an indigo-night background with a thin gold border (1px `#D4A017`) to signal the screen-as-stage metaphor.

## Shapes

**sm (4px):** tags, region badges, platform labels
**md (8px):** cards, image crops
**lg (16px):** hero image frames, feature cards
**xl (24px):** video thumbnail frames, full-bleed image containers
No pill buttons — rounded-full is reserved for avatar circles only.

## Components

**Buttons:** terracotta primary, small border-radius (4px). Never orange. The primary action is an invitation to listen, not a hard CTA. Copy: "Listen now", "Explore stories", "Watch this episode" — never "Get started" or "Subscribe now."

**Region/culture tags:** pill shape (`rounded-full`), background `#F5E6DC`, text `#C4622D`, font Public Sans 600 11px uppercase. Examples: `AKAN`, `WOLOF`, `YORUBA`. Mandatory on every story card.

**End-card:** indigo-night background, baobab silhouette illustration (bottom-aligned), channel name in Fraunces 700 cream, thin gold underline. Tagline below: "Stories from the roots."

**Animated intro/outro sting:** 3-second. Baobab silhouette grows from seed to full tree. Ochre → gold color transition. Drum sting audio. Never skip.

## Agent Prompt Guide

When generating visual output for Under the Baobab:
- Primary palette is earthy warm: terracotta, ochre, cream, indigo. No blues. No grays. No cold tones.
- MANDATORY: every story card must display a region/culture tag (AKAN, WOLOF, MANDE, YORUBA, BAMILEKE, BERBER, FULANI — match to story source)
- Typography is Fraunces for display/headings, Source Serif 4 for body. Never Inter. Never sans-serif headlines.
- Gold (`#D4A017`) is firelight — use it sparingly on one element per screen. Overuse kills the signal.
- Video backgrounds: indigo-night (`#1B1F4A`) only. Never white, never light gray.
- Indigo appears as the container; terracotta and gold appear as the light inside it.
- No stock photography. No generic "Africa" imagery. Illustrations and AI-generated stills only, region-motif matched.
- "Show your work" on cultural attribution: if the story has a source, surface it visibly.

## Do's and Don'ts

**Do:**
- Use textile-inspired geometric patterns as decorative layer (Adinkra symbols, kente stripe motifs, mudcloth geometry)
- Show region/tribe tag on every story record — it is the brand's authenticity signal
- Let Fraunces display type carry weight — it earns the headline position
- Use indigo night as the stage, warm colors as the light
- Keep cream as the text surface (not white) — warmth is structural, not decorative

**Don't:**
- Use Inter or any geometric sans for display or headings — it breaks the griot register
- Use red tones (no `#FF0000`, no fire-engine red — the warm palette already has heat)
- Use blue-toned "Africa" stock imagery (blue skies over savanna = generic; we want textile, village, elder)
- Show generic gradient backgrounds — flat terracotta or indigo-night only
- Mix kente geometry with Maasai beadwork patterns — region-motif match is mandatory
- Use pill-shaped CTA buttons — this brand is not a SaaS product
