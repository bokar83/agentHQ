---
version: "1.1"
name: CW Typography Stack
description: Single source of truth for all Catalyst Works typography. Load this file first for any CW-branded output. Overrides all font references in other CW styleguide files.
typography:
  display:
    fontFamily: "Spectral"
    fontSize: "56px"
    fontWeight: 700
    lineHeight: 1.1
    letterSpacing: "-0.02em"
    note: "Display/hero headlines. Weights 500-800 available."
  h1:
    fontFamily: "Spectral"
    fontSize: "44px"
    fontWeight: 700
    lineHeight: 1.2
    letterSpacing: "-0.02em"
  h2:
    fontFamily: "Spectral"
    fontSize: "32px"
    fontWeight: 600
    lineHeight: 1.25
    letterSpacing: "-0.015em"
  h3:
    fontFamily: "Public Sans"
    fontSize: "22px"
    fontWeight: 700
    lineHeight: 1.3
    letterSpacing: "-0.01em"
  h4:
    fontFamily: "Public Sans"
    fontSize: "18px"
    fontWeight: 600
    lineHeight: 1.4
    letterSpacing: "0"
  body:
    fontFamily: "Public Sans"
    fontSize: "16px"
    fontWeight: 400
    lineHeight: 1.6
    letterSpacing: "0"
  body-lg:
    fontFamily: "Spectral"
    fontSize: "18px"
    fontWeight: 400
    fontStyle: "normal"
    lineHeight: 1.65
    letterSpacing: "0"
    note: "Long-form body, about page narrative"
  pull-quote:
    fontFamily: "Spectral"
    fontSize: "18px"
    fontWeight: 400
    fontStyle: "italic"
    lineHeight: 1.65
    letterSpacing: "0"
    note: "Use sparingly — once or twice per page max"
  label:
    fontFamily: "Public Sans"
    fontSize: "12px"
    fontWeight: 500
    lineHeight: 1.4
    letterSpacing: "0.1em"
    textTransform: "uppercase"
  caption:
    fontFamily: "Public Sans"
    fontSize: "11px"
    fontWeight: 400
    lineHeight: 1.4
    letterSpacing: "0"
  data:
    fontFamily: "JetBrains Mono"
    fontSize: "14px"
    fontWeight: 400
    lineHeight: 1.5
    letterSpacing: "0"
    note: "Data, code, numeric callouts — unchanged from v1.0"
fonts:
  retired:
    - "Inter"
    - "Plus Jakarta Sans"
    - "Source Serif 4"
    - "DM Sans"
    - "DM Serif Display"
    - "Space Grotesk"
    - "Syne"
    - "Outfit"
    - "Fraunces"
    - "Newsreader"
    - "Lora"
    - "Crimson"
    - "Cormorant"
    - "Playfair Display"
    - "Instrument Sans"
    - "Instrument Serif"
  import_html: "<link href=\"https://fonts.googleapis.com/css2?family=Spectral:ital,wght@0,500;0,600;0,700;0,800;1,400;1,700&family=Public+Sans:wght@400;500;600;700&family=JetBrains+Mono&display=swap\" rel=\"stylesheet\">"
---

# Current Typography Stack - Catalyst Works Consulting

**This is the single source of truth for CW typography.** Every other styleguide file (master, websites, PDF, slides, social) and every skill that produces CW-branded artifacts MUST load this file first and use the stack defined here. When typography changes, this file changes - no other file should hard-code the font names.

**Version:** 1.1
**Locked:** 2026-04-29
**Supersedes:** all v1.0 references to Inter, Plus Jakarta Sans, Source Serif 4 (RETIRED - reflex-reject per Impeccable design audit)

---

## Active stack

| Use | Font | Weights | Source | Why |
|---|---|---|---|---|
| **Display / Headlines** | **Spectral** | 500, 600, 700, 800; italic 400, 700 | Production Type, free via Google Fonts | Editorial display serif anchored in real publishing tradition. Confident, considered, magazine-weight. NOT on any AI reflex-reject list. |
| **Body / UI labels** | **Public Sans** | 400, 500, 600, 700 | U.S. Web Design System, free via Google Fonts | Civic, governmental, intentional. NOT SaaS-startup. NOT on reflex-reject list. Highly readable at all sizes. |
| **Pull-quotes / italic emphasis** | **Spectral italic** | italic 400, 700 | (same as display) | Use sparingly: once or twice per page max. |
| **Data / Code / Numeric callouts** | **JetBrains Mono** | 400 | JetBrains, free via Google Fonts | Retained from v1.0. |

---

## Drop-in import (HTML)

Always use this exact import for any CW-branded HTML artifact:

```html
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Spectral:ital,wght@0,500;0,600;0,700;0,800;1,400;1,700&family=Public+Sans:wght@400;500;600;700&family=JetBrains+Mono&display=swap" rel="stylesheet">
```

## Drop-in CSS tokens

```css
:root {
  --font-display: 'Spectral', Georgia, 'Times New Roman', serif;
  --font-body: 'Public Sans', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
  --font-mono: 'JetBrains Mono', 'Courier New', monospace;
}

body { font-family: var(--font-body); }
h1, h2 { font-family: var(--font-display); font-weight: 700; letter-spacing: -0.015em; }
h3, h4 { font-family: var(--font-body); font-weight: 700; }
.pull-quote, .display-italic { font-family: var(--font-display); font-style: italic; font-weight: 400; }
code, pre, .data, .numeric { font-family: var(--font-mono); }
```

---

## Letter-spacing rules

- Display + H1: `letter-spacing: -0.02em` (Spectral wants slightly less negative tracking than a sans does - serifs need less tightening to feel confident)
- H2 + H3: `letter-spacing: -0.015em / -0.01em`
- Labels / eyebrows (uppercase): `letter-spacing: 0.1em`
- Body text: always `letter-spacing: 0` - never touch body tracking

## Mobile

Scale display + h1 proportionally: display → 36-44px, h1 → 28-34px. H2 and below remain the same. Letter-spacing values stay the same on mobile.

---

## RETIRED fonts (DO NOT USE on CW artifacts)

These are on Impeccable's reflex-reject list. Using any of them on a CW-branded artifact is a P1 anti-pattern violation that will fail `/design-audit`.

- ~~Inter~~ (v1.0 body font, retired 2026-04-29 - appears on every AI-generated SaaS site)
- ~~Plus Jakarta Sans~~ (v1.0 display font, retired 2026-04-29 - default "friendly modern" pick)
- ~~Source Serif 4~~ (v1.0 long-form serif, retired 2026-04-29 - default "considered serif" pick)
- DM Sans, DM Serif Display, Space Grotesk, Syne, Outfit, Fraunces, Newsreader, Lora, Crimson, Cormorant, Playfair Display, IBM Plex *, Instrument Sans, Instrument Serif (also reflex-reject - never use on CW)

---

## How to reference this file

**In any styleguide:** Top-level statement: "Typography is locked in `docs/styleguides/CURRENT_TYPOGRAPHY.md` v1.1+. This file does not duplicate font names - load CURRENT_TYPOGRAPHY.md for the current stack."

**In any skill:** "For CW-branded output, always load `docs/styleguides/CURRENT_TYPOGRAPHY.md` first to get the latest typography stack. Do NOT hard-code font names in the skill - they will go stale."

**In any code generator:** Replace hard-coded `'Inter'` strings with a config variable that defaults to whatever `CURRENT_TYPOGRAPHY.md` lists. Example pattern:

```python
# Read the current display font from the styleguide
import re
from pathlib import Path

CURRENT_TYPO = Path("docs/styleguides/CURRENT_TYPOGRAPHY.md").read_text()
DISPLAY_FONT = re.search(r"\*\*Display / Headlines\*\* \| \*\*(\w+)\*\*", CURRENT_TYPO).group(1)
BODY_FONT = re.search(r"\*\*Body / UI labels\*\* \| \*\*([\w ]+)\*\*", CURRENT_TYPO).group(1)
```

---

## Changelog

- **v1.1 (2026-04-29):** Spectral + Public Sans + JetBrains Mono. Inter, Plus Jakarta Sans, Source Serif 4 retired.
- **v1.0 (2026-03-29):** Plus Jakarta Sans (display), Inter (body), Source Serif 4 (long-form), JetBrains Mono (data). RETIRED.
