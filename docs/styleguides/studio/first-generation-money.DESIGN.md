---
version: alpha
name: First Generation Money
description: Faceless first-gen finance channel. Calm authority. Math-on-screen. No hype.
colors:
  primary: "#0A7C6E"
  primary-dark: "#085F54"
  primary-light: "#D6F0EC"
  amber: "#C97B2A"
  amber-light: "#F5E4C8"
  base: "#0D1F1C"
  base-lighter: "#152E29"
  surface: "#F4F9F8"
  surface-dark: "#1A3530"
  text-primary: "#0D1F1C"
  text-secondary: "#3D5A56"
  text-muted: "#6B8C87"
  text-on-dark: "#EAF4F2"
  text-on-dark-muted: "rgba(234,244,242,0.65)"
  border: "#C4DDD9"
  border-dark: "rgba(10,124,110,0.25)"
  highlight: "#FFD166"
typography:
  display:
    fontFamily: "DM Sans"
    fontSize: "52px"
    fontWeight: 700
    lineHeight: 1.1
    letterSpacing: "-0.025em"
  heading:
    fontFamily: "DM Sans"
    fontSize: "32px"
    fontWeight: 600
    lineHeight: 1.25
    letterSpacing: "-0.015em"
  body:
    fontFamily: "Public Sans"
    fontSize: "16px"
    fontWeight: 400
    lineHeight: 1.65
    letterSpacing: "0"
  number:
    fontFamily: "DM Mono"
    fontSize: "48px"
    fontWeight: 500
    lineHeight: 1.0
    letterSpacing: "-0.02em"
  caption:
    fontFamily: "Public Sans"
    fontSize: "13px"
    fontWeight: 500
    lineHeight: 1.4
    letterSpacing: "0.02em"
  eyebrow:
    fontFamily: "Public Sans"
    fontSize: "11px"
    fontWeight: 600
    lineHeight: 1.4
    letterSpacing: "0.1em"
rounded:
  sm: "4px"
  md: "8px"
  lg: "12px"
  xl: "20px"
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
    textColor: "#FFFFFF"
    typography: "{typography.caption}"
    rounded: "{rounded.md}"
    padding: "12px 28px"
  button-secondary:
    backgroundColor: "transparent"
    textColor: "{colors.primary}"
    typography: "{typography.caption}"
    rounded: "{rounded.md}"
    padding: "11px 27px"
  card:
    backgroundColor: "{colors.surface}"
    textColor: "{colors.text-primary}"
    rounded: "{rounded.lg}"
    padding: "{spacing.lg}"
  stat-card:
    backgroundColor: "{colors.base}"
    textColor: "{colors.text-on-dark}"
    rounded: "{rounded.lg}"
    padding: "{spacing.xl}"
  math-block:
    backgroundColor: "{colors.base-lighter}"
    textColor: "{colors.text-on-dark}"
    rounded: "{rounded.md}"
    padding: "{spacing.md}"
---

## Overview

First Generation Money is the finance teacher your family never had — calm, clear, showing their work. The brand is not a bro-finance hustle channel. It is not Wall Street. It is the older sibling who figured it out and is explaining it at the kitchen table. Deep teal is the anchor — it signals trust, money, competence, without the cold blue of corporate finance or the aggressive green of "wealth mindset" content. Amber provides warmth and human touch. Numbers are the visual hero — large, unambiguous, on dark surfaces.

Emotional intent: relief, clarity, "I can actually do this." The audience should feel smarter after watching, not overwhelmed.

## Colors

**Primary — Deep Teal** `#0A7C6E`: primary actions, links, active states, highlighted numbers. Financial trust without Wall Street cold. This is the brand's signature color.

**Amber** `#C97B2A`: warmth accent, human moments, callout borders, "earned wisdom" signal. Not hype-orange. Used sparingly as the second voice.

**Base** `#0D1F1C`: hero backgrounds, dark sections, video frame base. Almost-black with teal undertone — the brand's dark anchor.

**Highlight** `#FFD166`: animated number reveals, key stat callouts. Bright, draws the eye immediately to the math being shown.

**Surface** `#F4F9F8`: light section backgrounds. Slight teal tint, not pure white. Keeps the palette coherent in light mode.

**Text Primary** `#0D1F1C`: all body copy on light surfaces. Matches the dark base so the brand feels continuous.

## Typography

**Display + Heading — DM Sans 700/600:** Clean, modern, authoritative without being cold. At large sizes it has geometric confidence. At heading sizes it is readable and directive. This is the "teacher at the whiteboard" font.

**Body — Public Sans 400:** Civic, readable, trustworthy. Not SaaS. Pairs well with DM Sans. Used for all explanatory prose.

**Numbers — DM Mono 500:** Every key number, every stat, every dollar amount rendered in DM Mono. Monospace makes numbers align and feel precise. This IS the brand signature — math shown in monospace is the visual fingerprint.

**Eyebrow — Public Sans 600 uppercase:** Episode numbers, topic tags, platform labels.

**Font import:**
```html
<link href="https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;600;700&family=DM+Mono:wght@400;500&family=Public+Sans:wght@400;500;600&display=swap" rel="stylesheet">
```

## Layout

12-column grid, max-width 1140px. Clean, structured, tabular where appropriate — this brand shows its work. Number callouts get full-width dark panels. Explanation prose goes in clean two-column layouts (concept left, math right). No asymmetric artsy layouts — clarity is the aesthetic. White space is generous but purposeful, not decorative.

## Elevation & Depth

Dark panels for numbers, light panels for prose. Hard contrast, not gradients. Cards use a thin teal border (`1px solid #C4DDD9` on light, `1px solid rgba(10,124,110,0.25)` on dark). No drop shadows — this brand does not perform depth, it earns it through content hierarchy.

## Shapes

**sm (4px):** tags, badges, input fields
**md (8px):** buttons, standard cards
**lg (12px):** feature cards, stat panels
**xl (20px):** hero image containers
No pill shapes except avatar circles.

## Components

**Stat/KPI panel:** dark base background, number in DM Mono 700 48px in teal, label in Public Sans 14px muted. This is the most-used component — it appears in every video and every post.

**Math block:** dark surface, DM Mono for all numbers and formulas, teal for positive deltas, amber for attention-worthy items, highlight yellow for the single key number per block.

**"Show your work" annotation:** small Public Sans 11px caption below every major number, citing the source or explaining the calculation. Mandatory on every video slide containing a stat.

**End-card:** base-dark background, "First Generation Money" wordmark in DM Sans 700, teal underline, tagline "Built for first-gens. Pass it on." in Public Sans 400 16px. Subscribe prompt in teal.

## Agent Prompt Guide

When generating visual output for First Generation Money:
- Numbers are the hero. Every screen should have at least one large number (DM Mono, 48px+, teal or highlight)
- Dark mode is the default for video. Light mode for supplementary web content only.
- NEVER use gradient backgrounds. Flat dark base or flat light surface only.
- NEVER use hype-finance energy: no rocket emojis, no "CRUSH IT", no aggressive green color palette
- "Show your work": every stat needs a source label, every math calculation shows the formula
- Amber is warmth, not warning. Use it for human moments, not for errors or alerts.
- The brand tagline "Built for first-gens. Pass it on." appears on every end-card.
- No Boubacar branding anywhere on this channel. Zero connection to Catalyst Works or agentsHQ.

## Do's and Don'ts

**Do:**
- Show math visually: animated number builds, before/after comparisons, side-by-side scenarios
- Use DM Mono for every dollar amount, percentage, and year — consistency is the trust signal
- Keep dark panels for numbers, light panels for explanations — the contrast guides the eye
- Cite every stat inline ("Source: Federal Reserve 2025") — credibility is the moat
- Use the "kitchen table" framing: explaining, not selling

**Don't:**
- Use red anywhere — not for negative numbers, not for warnings. Use amber for caution.
- Use gradient-green "wealth mindset" aesthetics — that is the exact register this brand rejects
- Show generic stock of people holding money or pointing at charts
- Use Roboto, Inter, or any SaaS-default font — this brand needs its own typographic identity
- Let any video go out without the "Built for first-gens. Pass it on." end-card
- Fabricate numbers or stats — verified data only, source always shown
