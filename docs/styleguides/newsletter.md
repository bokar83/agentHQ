# The Weekly Signal -- Newsletter Style Guide

Source of truth for every issue. Agents read this before generating any newsletter artifact.

---

## Identity

- **Name:** The Weekly Signal
- **Brand:** Catalyst Works
- **Sender:** Boubacar Barry `<boubacar@catalystworks.consulting>`
- **Cadence:** Weekly, Monday
- **Platform:** Listmonk (self-hosted, `mail.srv1040886.hstgr.cloud`)
- **List ID:** 3
- **List UUID:** `e78a3008-c023-4eb5-a03f-f4202bf7ce8c`
- **Archive:** `catalystworks.consulting/signal` (one page per issue at `/signal/issue-N`)
- **Audience:** Business operators (CEOs, COOs, ops managers, HR leaders) navigating AI adoption

---

## Voice Rules (non-negotiable)

Enforced by CTQ + BouB Voice Mastery before every send.

- **No em dashes. No en dashes. No double hyphens.** Rewrite the sentence.
- **No hedging.** Cut "might be", "perhaps", "one could argue".
- **No AI red-flag words.** Leverage, synergy, tapestry, delve, seamless, cutting-edge, notably, indeed.
- **No throat-clearing.** "In the realm of", "when it comes to", "it is important to note."
- **Sentence variety mandatory.** Short. Long. Short. Fragments allowed.
- **Specifics over generics.** Real numbers, cited sources, named scenes.
- **Colleague voice, not professor voice.** Start with the insight, not the context.
- **Fabricated story gate.** No invented anecdotes attributed to Boubacar. Confirm real or rewrite as explicit hypothetical.
- **Signature:** `Boubacar` only. No last name. No title. No em dash.

---

## Content Structure (every issue)

```
1. Subject line        -- sharp, stops scroll, states the tension
2. Preview text        -- one sentence, creates urgency (Listmonk preview field)
3. Opening scene       -- personal, specific, grounded in Boubacar's real operation
4. The insight         -- what operators miss, from practitioner POV
5. One stat            -- sourced, cited, makes them feel it
6. One thing to do     -- concrete action, 15 minutes or less
7. Sign-off            -- "Boubacar" only
8. Sources section     -- 2-3 URLs, real, no invented citations
```

Word count target: 450-650 words body. Forwardable. No padding.

---

## Email HTML Design System

Template file: `workspace/newsletter/issue-3.html` (canonical reference)

### Palette (email-safe, no CSS variables)

| Role | Hex | Usage |
|---|---|---|
| Header bg (dark) | `#0D2137` | Email header background start |
| Header bg (mid) | `#1B4F72` | Email header background end (gradient) |
| Accent orange | `#E87722` | Pull quote border, CTA labels, stat numbers |
| Accent orange light | `#F5A623` | Accent bar gradient end |
| Body bg | `#FFFFFF` | Main content area |
| Page bg | `#F5F3EF` | Outer wrapper background |
| Pull quote bg | `#FDF6EE` | Pull quote tinted background |
| Action box bg | `#F5F3EF` | "One thing to do" box |
| Sources bg | `#F0EDE8` | Sources strip |
| Footer bg | `#0D2137` | Footer background |
| Body text | `#1A1A2E` | All body paragraphs |
| Header text | `#FFFFFF` | Headline on dark header |
| Muted header text | `#A8C4D8` | Deck / secondary header text |
| Link color | `#1B4F72` | All links in body |
| Footer text | `#5B8BAA` | Footer text and links |

### Typography (email-safe)

| Element | Font | Size | Weight |
|---|---|---|---|
| Header h1 | Georgia, serif | 28px | normal (400) |
| Body paragraphs | Georgia, serif | 17px | normal |
| Pull quotes | Georgia, serif | 22px | normal, italic |
| Stat numbers large | Georgia, serif | 52px | normal |
| Stat numbers medium | Georgia, serif | 42px | normal |
| Labels/eyebrows | Helvetica Neue, Arial | 11px | 700, uppercase, 2px tracking |
| Source text | Helvetica Neue, Arial | 12px | normal |
| Signature name | Helvetica Neue, Arial | 15px | 700 |

### Layout Dimensions

- Max width: 600px
- Header padding: 44px 48px 36px (inner)
- Body padding: 44px 48px 8px (first block), 8px 48px (subsequent)
- Pull quote padding: 24px 28px
- Stat block padding: 32px 36px
- Action box padding: 28px 32px
- Footer padding: 28px 48px
- Mobile breakpoint: 620px

### Component Specs

**Header:**
- `linear-gradient(135deg, #0D2137 0%, #1B4F72 100%)`
- Logo img (36x36px, 4px border-radius) + wordmark
- Issue number top-right label
- Headline h1 (white, Georgia)
- Deck paragraph (muted blue, Helvetica)
- 4px orange accent bar at bottom: `linear-gradient(90deg, #E87722, #F5A623)`

**Pull quotes:**
- `border-left: 4px solid #E87722`
- Background: `#FDF6EE`
- Font: Georgia 22px italic, color `#0D2137`
- Padding: 24px 28px
- Border-radius: 0 4px 4px 0

**Stat block:**
- Background: `linear-gradient(135deg, #0D2137, #1B4F72)`
- Border-radius: 6px
- Eyebrow label: 11px, uppercase, `#5B8BAA`
- Stat number: Georgia 52px/42px, `#E87722`
- Stat label: Helvetica 14px, `#A8C4D8`
- Source: Helvetica 12px, `#5B8BAA`
- Divider between stats: `rgba(168,196,216,0.2)`

**Action box ("One thing to do"):**
- Background: `#F5F3EF`, border: `1px solid #E0DBD3`
- Border-radius: 6px
- Label: 11px uppercase orange `#E87722`
- Message template block: white bg, `border-left: 3px solid #1B4F72`, Helvetica 14px italic

**Signature:**
- Logo img 44x44px, border-radius 50%
- Name: Helvetica 15px bold `#0D2137` -- "Boubacar" only, no last name
- Sub-line: Helvetica 12px `#888`, with catalystworks.consulting link

**Footer:**
- Background: `#0D2137`, border-radius: 0 0 6px 6px
- Unsubscribe + view-in-browser links: `#5B8BAA`
- Use Listmonk template variable: `{{ UnsubscribeURL }}` (capital U, capital URL -- Listmonk v6 format)

---

## Web Archive Design System

Template files:
- Archive index: `output/websites/catalystworks-site/signal.html`
- Issue page: `output/websites/catalystworks-site/signal/issue-N.html`

Uses same CW token system as main site (`--ink`, `--paper`, `--amber`, `--cyan`, `--border`, `--card-bg`). Fonts: Spectral (serif, display) + Inter (sans, UI).

**Issue page structure:**
1. Fixed nav (logo left, "All issues" back link right)
2. Article meta (issue badge, date, category)
3. H1 title + italic deck
4. 48px amber accent line
5. Body: Spectral 19px, 1.8 line height
6. Pull quotes: border-left 3px amber, `var(--card-bg)` bg
7. Stat block: 2-col grid, `var(--card-bg)` bg, amber numbers
8. Action box: amber-tinted border + bg
9. Signature: circular logo, "Boubacar" + catalystworks.consulting
10. Sources strip
11. Issue prev/next nav
12. Subscribe CTA block (end of article)

**Accessibility requirements (P1 -- always ship with these):**
- Email inputs must have associated `<label>` (visually hidden is fine)
- Heading hierarchy must not skip levels (h1 -> h2, not h1 -> h3)
- All images need meaningful `alt` text

---

## Workflow (every issue)

```
Sunday 18:00 MT:   Orchestrator sends Telegram prompt for anchor topic
Monday 06:00 MT:   Trend scout selects fallback if no reply
Monday 12:00 MT:   Newsletter crew generates draft
                   -> CTQ review (2 passes minimum, target 9/10)
                   -> Fabricated story gate check
                   -> BouB Voice Mastery check
                   -> Design the HTML email (template above)
                   -> Create web archive page (signal/issue-N.html)
                   -> Design audit (target 16+/20, fix P1s before ship)
Monday approval:   Boubacar reviews, approves
On approval:       -> Listmonk campaign created + sent
                   -> Notion Content Board record created (Status: Published)
                   -> Web archive deployed to Hostinger (catalystworks-site repo)
                   -> sitemap.xml updated
```

---

## Listmonk Campaign Creation (API)

```python
import httpx, os

LISTMONK_URL = os.environ["LISTMONK_URL"]  # http://listmonk:9000
API_USER = "api_orchestrator"
API_TOKEN = os.environ["LISTMONK_API_TOKEN"]
LIST_ID = int(os.environ["LISTMONK_LIST_ID"])  # 3

payload = {
    "name": f"The Weekly Signal: Issue {N}",
    "subject": SUBJECT_LINE,
    "lists": [LIST_ID],
    "from_email": "Boubacar Barry <boubacar@catalystworks.consulting>",
    "type": "regular",
    "content_type": "html",
    "body": HTML_BODY,  # full email HTML (header through footer)
}

# Create campaign
r = httpx.post(f"{LISTMONK_URL}/api/campaigns", json=payload, auth=(API_USER, API_TOKEN))
campaign_id = r.json()["data"]["id"]

# Send immediately
httpx.put(f"{LISTMONK_URL}/api/campaigns/{campaign_id}/status",
          json={"status": "running"}, auth=(API_USER, API_TOKEN))
```

---

## Issue Archive (update each issue)

| Issue | Date | Title | Topic | URL |
|---|---|---|---|---|
| 1 | 2026-04-21 | Revenue is up. That is the problem. | AI Operations | /signal/issue-1 |
| 2 | 2026-04-28 | Before you buy another AI tool, read this | AI Strategy | /signal/issue-2 |
| 3 | 2026-05-07 | Your employees are already running AI you have not approved | AI Governance | /signal/issue-3 |
