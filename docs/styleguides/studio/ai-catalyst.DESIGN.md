---
version: alpha
name: AI Catalyst
description: Faceless AI-displacement education channel. Dark mode. Electric. HR-insider authority inside a digital-native shell.
colors:
  primary: "#6C63FF"
  primary-dark: "#5549E8"
  primary-light: "#ECEAFF"
  electric: "#00E5FF"
  electric-dim: "rgba(0,229,255,0.15)"
  base: "#0E0E1A"
  base-lighter: "#161626"
  base-card: "#1C1C30"
  surface-light: "#F5F5FF"
  text-primary: "#F0F0FF"
  text-secondary: "rgba(240,240,255,0.7)"
  text-muted: "rgba(240,240,255,0.45)"
  text-on-light: "#0E0E1A"
  border: "rgba(108,99,255,0.2)"
  border-bright: "rgba(0,229,255,0.35)"
  amber-signal: "#F5A623"
  success: "#00C896"
typography:
  display:
    fontFamily: "Syne"
    fontSize: "54px"
    fontWeight: 800
    lineHeight: 1.05
    letterSpacing: "-0.03em"
  heading:
    fontFamily: "Syne"
    fontSize: "32px"
    fontWeight: 700
    lineHeight: 1.2
    letterSpacing: "-0.02em"
  body:
    fontFamily: "Public Sans"
    fontSize: "16px"
    fontWeight: 400
    lineHeight: 1.65
    letterSpacing: "0"
  data:
    fontFamily: "JetBrains Mono"
    fontSize: "14px"
    fontWeight: 400
    lineHeight: 1.5
    letterSpacing: "0"
  number:
    fontFamily: "JetBrains Mono"
    fontSize: "48px"
    fontWeight: 400
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
  lg: "14px"
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
    textColor: "{colors.electric}"
    typography: "{typography.caption}"
    rounded: "{rounded.md}"
    padding: "11px 27px"
  card:
    backgroundColor: "{colors.base-card}"
    textColor: "{colors.text-primary}"
    rounded: "{rounded.lg}"
    padding: "{spacing.lg}"
  data-card:
    backgroundColor: "{colors.base-lighter}"
    textColor: "{colors.text-primary}"
    rounded: "{rounded.md}"
    padding: "{spacing.md}"
  stat-card:
    backgroundColor: "{colors.base}"
    textColor: "{colors.electric}"
    rounded: "{rounded.lg}"
    padding: "{spacing.xl}"
---

## Overview

AI Catalyst is Boubacar's agentic meta-channel — the "Director of HR with global experience" who built a faceless channel that runs on AI and is showing you the receipts. The visual language is dark-mode digital-native: deep base, electric cyan accent, violet primary. It has the energy of the terminal and the authority of the boardroom. This is not a tech bro channel. It is not a startup pitch deck. It is a calm professional who understands AI better than your CHRO does and is explaining what that means for your job. The "agentic channel built by AI" meta-story is part of the brand — transparency about the system IS the moat.

Emotional intent: clarity, forward momentum, "I'm not scared of this anymore." Not hype. Not fear. Information that empowers.

## Colors

**Primary — Violet** `#6C63FF`: primary actions, links, active states. Distinct from corporate blue, distinct from consumer purple. Signal: AI-forward, thoughtful, not aggressive.

**Electric — Cyan** `#00E5FF`: data reveals, animated elements, key stat highlights, terminal-style callouts. Used sparingly — it is the signal that something important is being shown. At full opacity on dark base it reads electric. At 15% opacity it creates subtle UI depth.

**Base** `#0E0E1A`: video background, hero background, the default canvas. Near-black with a deep indigo undertone. This is not generic dark mode — the slight violet shift keeps it brand-specific.

**Amber Signal** `#F5A623`: human-context warmth, the HR-insider voice moments, career-reality callouts. The only warm color in the palette — when it appears, it signals something human inside the tech.

**Success** `#00C896`: positive outcomes, AI-proof strategies, "you can do this" moments.

**Text Primary** `#F0F0FF`: body copy on dark. Slightly blue-tinted white — warmer than pure `#FFFFFF`, less harsh.

## Typography

**Display + Heading — Syne 800/700:** Syne has geometric confidence and a slight mechanical edge without being cold. At large sizes it reads as authoritative. It was designed for display use and earns the space at 54px+. This is the channel's headline personality — precise, no-nonsense, modern.

**Body — Public Sans 400:** Civic, readable, not startup. Same family used in CW styleguide — connects to Boubacar's professional register.

**Data/Numbers — JetBrains Mono:** Terminal aesthetic for data, stats, job displacement numbers, AI capability benchmarks. Every significant number rendered in mono reinforces the "showing the receipts" brand stance. Same family as CW data font — Boubacar's data voice is consistent.

**Font import:**
```html
<link href="https://fonts.googleapis.com/css2?family=Syne:wght@700;800&family=Public+Sans:wght@400;500;600&family=JetBrains+Mono:wght@400&display=swap" rel="stylesheet">
```

## Layout

12-column grid, max-width 1120px. Data-forward layouts: tables, side-by-side comparisons, before/after job-risk panels. The "show the dashboard" content style means some screens are genuinely information-dense — that is intentional and on-brand. Use the electric border (`1px solid rgba(0,229,255,0.35)`) on data panels to signal "this is signal, not noise." Section spacing: 80px standard, 40px for tightly related content blocks.

## Elevation & Depth

Layered dark surfaces. Base (`#0E0E1A`) → base-lighter (`#161626`) → base-card (`#1C1C30`). Cards sit above base, not below. Glow effect on key data elements: `box-shadow: 0 0 20px rgba(0,229,255,0.15)` — subtle, not neon. No drop shadows on non-data elements.

## Shapes

**sm (4px):** tags, inline badges, terminal cursor elements
**md (8px):** buttons, form inputs
**lg (14px):** cards, data panels
**xl (20px):** hero containers, video frames
No pill shapes except progress indicators.

## Components

**Job-risk card:** base-card background, role name in Syne 600, risk level indicator (JetBrains Mono, colored: green=low, amber=medium, electric=high, — never red), automation timeline in mono. Core content type.

**Data reveal panel:** electric border, JetBrains Mono numbers, Public Sans labels, electric dim background. Used for "here's what AI is actually doing to this job category" content.

**Terminal callout block:** base-lighter background, electric cyan border-left (3px), JetBrains Mono text, monospace prompt symbol (`>`). Used for AI capability quotes, model benchmarks, system output examples.

**"Director of HR" attribution tag:** small Public Sans 11px, amber color, text "Director of HR — Global Experience". Appears in video lower-third on long-form content and in web footer.

**End-card:** base background, "AI Catalyst" in Syne 800, violet underline, subtitle line in Public Sans 400 electric-dim, meta-tagline "Built by the system it explains." Subscribe CTA.

## Agent Prompt Guide

When generating visual output for AI Catalyst:
- Dark mode only. No light mode for video content.
- Every data reveal should use JetBrains Mono — monospace is the brand fingerprint for facts
- Electric cyan (`#00E5FF`) is the signal color — one per screen, maximum. Overuse kills it.
- Violet (`#6C63FF`) is the brand anchor — CTAs, active states, primary UI always violet
- The meta-story IS content: when appropriate, surfacing the dashboard, the cost ledger, the agent prompts is on-brand and encouraged
- "Director of HR with global experience" attribution tag MUST appear on every long-form video lower-third
- Amber appears only for human/career moments — not for general warm accents
- No light backgrounds in video. `#0E0E1A` base only.
- NEVER link to or mention Catalyst Works, catalystworks.consulting, or agentsHQ in any public-facing output

## Do's and Don'ts

**Do:**
- Show the actual numbers: automation risk percentages, timeline projections, salary impact data
- Use terminal-style callouts for AI system outputs and benchmarks
- Let the "agentic channel" meta-story surface naturally — it is the moat
- Apply the electric glow effect selectively on the single most important data point per screen
- Keep Syne display headlines short and punchy — 5-7 words max at hero scale

**Don't:**
- Use fear-based framing ("AI will destroy your career") — reframe every risk as an actionable insight
- Use blue tones that read as generic tech (this palette has violet-shifted blue, not corporate blue)
- Use neon or cyberpunk aesthetics — subtle electric glow, not a rave
- Show generic "robot replacing human" stock imagery — data visualizations and screen recordings only
- Reference Boubacar by name in public-facing output — this channel is Boubacar-adjacent, not Boubacar-branded
- Use red anywhere — job risk levels use green/amber/electric, not traffic-light red
