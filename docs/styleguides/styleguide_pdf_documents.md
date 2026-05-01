# PDF Document Design System - Catalyst Works Consulting

**Version:** 2.2
**Last updated:** 2026-04-29
**Palette:** Coastal Clarity
**For:** Boubacar Barry, Founder - Catalyst Works Consulting

---

## ⚠️ TYPOGRAPHY OVERRIDE - READ FIRST (v2.2, 2026-04-29)

**Typography in this file is OBSOLETE.** All references to "Inter" and "Source Serif 4" below are v2.1 legacy and MUST be substituted per the current source of truth:

> **Load `docs/styleguides/CURRENT_TYPOGRAPHY.md` first. Use the stack defined there.**

Substitution rule for v2.1 → v2.2 transition (until full rewrite in v2.3):

| Where v2.1 says... | Use instead (per CURRENT_TYPOGRAPHY.md v1.1) |
|---|---|
| `Inter` (display, weights 700, 800) | `Spectral` (700) |
| `Inter` (body, weights 400, 500, 600) | `Public Sans` (same weight) |
| `Source Serif 4` (italic pull-quotes) | `Spectral italic` (400 or 700) |
| `font-family: 'Inter'` | `font-family: var(--font-body)` (Public Sans via CURRENT_TYPOGRAPHY.md tokens) |
| Heading `font-family: 'Inter'` | `font-family: var(--font-display)` (Spectral) |

**Cover page typography (gold bar, category tag, document title, subtitle, etc):**
- Category tag: ~~Inter 600 11pt~~ → **Public Sans 600 11pt**
- Document title: ~~Inter 700 44pt~~ → **Spectral 700 44pt**
- Subtitle: ~~Inter 400 17pt~~ → **Public Sans 400 17pt**
- "Prepared for" line + Date + Version: ~~Inter~~ → **Public Sans** (same weights/sizes)

**Hero italic in body:** ~~Source Serif 4 italic 400~~ → **Spectral italic 400**

The layout, color, spacing, gold bar, dimensions, cover page geometry - all v2.1 spec is RETAINED. Only the font names change. When generating PDFs after 2026-04-29, apply the substitution rule above and verify with `/design-audit <path-to-html>` before converting to PDF (target ≥17/20 for CW client-facing PDFs).

---

## PART 1 - COVER PAGE SPECIFICATION

The cover page is the first claim the document makes. It must communicate authority before the reader processes a single word. Build it exactly to this spec.

### Cover Page Layout (top to bottom, A4 - 210 × 297mm)

```text
┌─────────────────────────────────────────────────────────┐
│  [FULL-BLEED BACKGROUND: #1B2A4A]                       │
│                                                         │
│  [Logo placeholder]          ← top-left, 20mm from     │
│   22mm from top, 20mm left     top, 20mm from left      │
│                                                         │
│  ─────────────────────────────────────────────         │
│  [CATEGORY TAG]                                         │
│   Inter 600, 11pt, #C49A2E, letter-spacing 0.12em      │
│   uppercase - e.g. "DIAGNOSTIC REPORT"                  │
│   36mm from top                                         │
│                                                         │
│  [DOCUMENT TITLE]                                       │
│   Inter 700, 44pt, #FFFFFF, line-height 1.1             │
│   max 2 lines, left-aligned                             │
│   44mm from top                                         │
│                                                         │
│  ████ 4px gold rule (#C49A2E), full column width        │
│       immediately below title, 8mm gap above            │
│                                                         │
│  [SUBTITLE]                                             │
│   Inter 400, 17pt, rgba(255,255,255,0.75), 1 line max   │
│   8mm below gold rule                                   │
│                                                         │
│  [Prepared for: CLIENT NAME]                            │
│   Inter 500, 12pt, rgba(255,255,255,0.60)               │
│   16mm below subtitle                                   │
│                                                         │
│  ─ ─ ─ ─ ─ ─ ─ ─ ─ 0.5pt divider #E5E7EB 30% opacity  │
│                                                         │
│  [Date]                              [Version]          │
│   left                                right             │
│   Inter 400, 10pt, rgba(255,255,255,0.50)               │
│                                                         │
│                                                         │
│  ░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░         │
│  [Bottom color band: #2D4A7A, bottom 38% of page]       │
│  Optional: single photo at 20% opacity within band      │
└─────────────────────────────────────────────────────────┘
```

### Cover Page Element Specifications

| Element | Font | Size | Weight | Color | Position |
| --- | --- | --- | --- | --- | --- |
| Logo placeholder | - | 28mm wide max | - | White version | 20mm top, 20mm left |
| Category tag | Inter | 11pt | 600 | `#C49A2E` | 36mm from top, 20mm left |
| Document title | Inter | 44pt | 700 | `#FFFFFF` | 44mm from top, 20mm left |
| Gold accent bar | - | 4px tall, full column | - | `#C49A2E` | Below title, 8mm gap |
| Subtitle | Inter | 17pt | 400 | `rgba(255,255,255,0.75)` | 8mm below gold bar |
| "Prepared for" line | Inter | 12pt | 500 | `rgba(255,255,255,0.60)` | 16mm below subtitle |
| Thin divider | - | 0.5pt | - | `#E5E7EB` at 30% | 12mm below "prepared for" |
| Date (left) | Inter | 10pt | 400 | `rgba(255,255,255,0.50)` | 8mm below divider |
| Version (right) | Inter | 10pt | 400 | `rgba(255,255,255,0.50)` | Same line as date |

### Cover Page Rules

- Background: full-bleed `#1B2A4A`, no white margins visible
- Title: the diagnosis or deliverable name - never a project code or number
- No tagline ("Transforming organizations through...") - the title carries the message
- No more than one image on the cover
- No logo watermarked across the background at any opacity
- No stock photo of handshakes, diverse teams around laptops, or arrows pointing up
- Cover page has no running header or footer

---

## PART 2 - TYPOGRAPHY HIERARCHY

All measurements given for screen rendering (px) and print (pt). Use pt for print PDFs; px for web-rendered or HTML-to-PDF.

### Font Stack

```text
Headings:     Inter (Google Fonts) - weights 700, 600
Body:         Inter - weights 400, 500
Pull quotes:  Source Serif 4 (Google Fonts) - italic, weight 400
Monospace:    JetBrains Mono (Google Fonts) - weight 400
Fallbacks:    Inter → Outfit → -apple-system → sans-serif
              Source Serif 4 → Lora → Georgia → serif
              JetBrains Mono → Courier New → monospace
```

### Complete Type Scale

| Level | Font | Weight | Screen (px) | Print (pt) | Line-height | Color | Notes |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Display / Cover | Inter | 700 | 52px | 40pt | 1.10 | `#FFFFFF` | Cover page only |
| H1 | Inter | 700 | 28px / 22px mobile | 22pt | 1.15 | `#1B2A4A` | One per chapter |
| H2 | Inter | 600 | 22px | 17pt | 1.25 | `#1B2A4A` | Gold underbar |
| H3 | Inter | 600 | 17px | 13pt | 1.40 | `#2D4A7A` | No underbar |
| H4 | Inter | 500 | 15px | 11pt | 1.45 | `#2C2C2C` | Uppercase + tracking |
| Body | Inter | 400 | 14px | 11pt | 1.57 | `#2C2C2C` | All running text |
| Lead / intro | Inter | 400 | 16px | 12pt | 1.60 | `#2C2C2C` | First para of section |
| Small / caption | Inter | 400 | 12px | 9pt | 1.50 | `#6B7280` | Footnotes, source lines |
| Pull quote | Source Serif 4 | 400 italic | 18px | 14pt | 1.55 | `#C49A2E` | Left-bar decoration |
| Code / data | JetBrains Mono | 400 | 13px | 10pt | 1.50 | `#E8C86A` on dark bg | Code blocks only |
| Table header | Inter | 600 | 13px | 10pt | 1.40 | `#FFFFFF` | On `#1B2A4A` bg |
| Table body | Inter | 400 | 13px | 10pt | 1.45 | `#2C2C2C` | Alternating row bg |

### H2 Decoration Rule

H2 always carries a 2px solid `#C49A2E` border-bottom. Padding-bottom: 8px. Margin-bottom: 16px. This is non-negotiable - it is the primary visual anchor for section structure.

```css
h2 {
  font-family: 'Inter', sans-serif;
  font-weight: 600;
  font-size: 22px;
  line-height: 1.25;
  color: #1B2A4A;
  border-bottom: 2px solid #C49A2E;
  padding-bottom: 8px;
  margin-bottom: 16px;
  margin-top: 32px;
}
```

### H4 Decoration Rule

H4 is uppercase with letter-spacing. No underline. Use it for labels, field headers, table column names.

```css
h4 {
  font-family: 'Inter', sans-serif;
  font-weight: 500;
  font-size: 15px;
  line-height: 1.45;
  color: #2C2C2C;
  text-transform: uppercase;
  letter-spacing: 0.05em;
  margin-bottom: 12px;
  margin-top: 24px;
}
```

### Typography Rules (Non-Negotiable)

- Never mix more than 2 typefaces in one document
- Never use italic for emphasis - use bold. Italic is reserved for pull quotes, titles of works, and formal definitions
- Tracking: 0 for all body text; +0.05em for H4 uppercase labels only
- H1 color: always `#1B2A4A`
- H2 color: always `#1B2A4A` with gold underbar
- H3 color: always `#2D4A7A`
- Body text color: always `#2C2C2C` - never primary color for running text
- Paragraph spacing: 10px below each paragraph; 0 first-line indent

---

## PART 3 - PAGE LAYOUT

### Page Setup

| Spec | A4 (default) | US Letter |
| --- | --- | --- |
| Page size | 210 × 297mm | 8.5 × 11in |
| Margin top | 25mm | 1in |
| Margin bottom | 25mm | 1in |
| Margin left | 20mm | 1in |
| Margin right | 20mm | 1in |
| Text column width | 170mm | 6.5in |
| Gutter (2-col) | 8mm | 0.3in |

### Column Grid

| Layout | Columns | Column Width | Use For |
| --- | --- | --- | --- |
| Single column | 1 | 170mm / 6.5in | Reports, proposals, narrative sections |
| Two-column equal | 2 | 81mm each | Comparison tables, side-by-side analysis |
| Two-column wide+narrow | 1+1 | 110mm + 52mm | Body text + sidebar, annotation layout |
| Three-column | 3 | 51mm each | Icon callouts, 3-way comparisons |

### Spacing Scale - Print (base unit = 4mm)

| Token | Value | Use |
| --- | --- | --- |
| `xs` | 4mm | Paragraph spacing below (body) |
| `sm` | 8mm | Component internal padding |
| `md` | 12mm | Section header margin above |
| `lg` | 16mm | Major section separation |
| `xl` | 24mm | Page section break (visual white space) |

### Section Spacing - Screen Pixels (for HTML-to-PDF)

| Token | Value | Use |
| --- | --- | --- |
| Paragraph spacing | 10px | Below each body paragraph |
| H3 margin top | 24px | Before each H3 |
| H2 margin top | 32px | Before each H2 (major section) |
| H1 margin top | 40px | Chapter openers |
| Major section break | 48px | Between report sections |
| Component padding | 16px | Inside callout boxes, code blocks |

---

## PART 4 - COMPONENTS

### 4.1 Callout Box (General / Note)

```text
Background:     #F4F6F8
Left border:    4px solid #C49A2E
Padding:        16px (all sides)
Border-radius:  4px
Margin:         24px 0
```

Text inside: Inter 400, 14px, `#2C2C2C`. Label (e.g. "NOTE") in Inter 700, 12px, `#C49A2E`, uppercase.

### 4.2 Warning Box

```text
Background:     #FFF8F0
Left border:    4px solid #E07B2E
Padding:        16px
Border-radius:  4px
Margin:         24px 0
```

Label: Inter 700, 12px, `#E07B2E`, uppercase ("WARNING"). Text: Inter 400, 14px, `#2C2C2C`.

### 4.3 Success / Highlight Box

```text
Background:     #F0F7F4
Left border:    4px solid #2D6A4F
Padding:        16px
Border-radius:  4px
Margin:         24px 0
```

Label: Inter 700, 12px, `#2D6A4F`, uppercase ("KEY FINDING"). Text: Inter 400, 14px, `#2C2C2C`.

### 4.4 Pull Quote

```text
Left border:    4px solid #C49A2E
Padding-left:   16px
Padding-top:    8px
Padding-bottom: 8px
Margin:         32px 0
```

Text: Source Serif 4 italic, 18px, `#C49A2E`. Attribution line below (if any): Inter 400, 12px, `#6B7280`.

### 4.5 Table

```text
Header row background:    #1B2A4A
Header text:              Inter 600, 13px, #FFFFFF
Header cell padding:      10px 14px

Body row odd:             #FFFFFF
Body row even:            #F4F6F8
Body text:                Inter 400, 13px, #2C2C2C
Body cell padding:        10px 14px

Outer border:             1px solid #E5E7EB
Cell border:              1px solid #E5E7EB
Number columns:           right-aligned
Text columns:             left-aligned
Status columns:           center-aligned
```

### 4.6 Code Block

```text
Background:     #2C2C2C
Text color:     #E8C86A
Font:           JetBrains Mono, 13px, weight 400
Line-height:    1.6
Padding:        16px
Border-radius:  4px
Margin:         24px 0
Overflow:       horizontal scroll if needed (never wrap code)
```

### 4.7 Numbered List

```text
Item text:      Inter 400, 14px, #2C2C2C, line-height 1.57
Number:         Inter 700, 14px, #C49A2E
Number format:  1. 2. 3. (period, then space)
Left indent:    20px
Item gap:       8px between items
```

### 4.8 Bullet List

```text
Item text:      Inter 400, 14px, #2C2C2C, line-height 1.57
Bullet:         6px round dot, color #C49A2E
Left indent:    20px
Item gap:       6px between items
Max nesting:    2 levels (sub-bullet: 4px dot, #6B7280, indent +16px)
```

### 4.9 Divider (Horizontal Rule)

```text
Border:     1px solid #E5E7EB
Margin:     24px 0
Width:      100% of column
```

### 4.10 Data / KPI Callout Box

For single metrics that require visual emphasis - use in groups of 2-4.

```text
Background:    #1B2A4A
Padding:       24px
Border-radius: 4px
Min-width:     120px
Max-width:     200px

Metric value:  Inter 700, 36px, #C49A2E
Metric label:  Inter 500, 11px, rgba(255,255,255,0.70), uppercase
```

### 4.11 Section Chapter Opener Page

Used when starting a major new chapter/section (optional, formal reports only).

```text
Background:     #1B2A4A (full page or half-page band)
H1 text:        Inter 700, 32pt, #FFFFFF
Framing line:   Inter 400, 14pt, #C49A2E, max 1 sentence
Chapter number: Inter 700, 80pt, rgba(196,154,46,0.15) - top-right, decorative
```

---

## PART 5 - RUNNING HEADER AND FOOTER

### Running Header (all pages except cover and chapter openers)

```text
Left text:      "Catalyst Works Consulting" - Inter 400, 10pt, #6B7280
Right text:     Document title - Inter 400, 10pt, #6B7280
Separator:      1px solid #E5E7EB, below header, full margin width
Padding-bottom: 10px above separator
Position:       16mm from top of page
```

### Running Footer

```text
Left text:    "Catalyst Works Consulting" - Inter 400, 9pt, #6B7280
Center text:  Page number - Inter 600, 9pt, #C49A2E
Right text:   Document date (YYYY-MM-DD) - Inter 400, 9pt, #6B7280
Separator:    1px solid #E5E7EB, above footer, full margin width
Position:     16mm from bottom of page
```

---

## PART 6 - FILE NAMING CONVENTION

### Format

```text
YYYYMMDD_DocumentType_ClientOrProject_v1.pdf
```

### Document Type Values

| Code | Document Type |
| --- | --- |
| `REPORT` | Client diagnostic, research report, analysis |
| `PROPOSAL` | Engagement proposal, SOW |
| `BRIEF` | Executive briefing, situation summary |
| `PLAYBOOK` | Workshop workbook, operational guide |
| `DECK` | Presentation leave-behind |
| `FRAMEWORK` | Methodology reference document |

### Examples

```text
20260329_REPORT_OrgDesign_ACMEL_v1.pdf
20260401_PROPOSAL_ChangeReadiness_TECHCO_v2.pdf
20260115_PLAYBOOK_DecisionRights_Internal_v1.pdf
```

### Rules

- No spaces - use underscores
- Version number is mandatory on every file sent externally
- Date is the date of the version being sent, not the project start date
- Internal Catalyst Works documents use `Internal` as the client/project field

---

## PART 7 - PALETTE SELECTION BY DOCUMENT TYPE

This guide uses Coastal Clarity as default. For other document types, use the following palettes from the Catalyst Works brand system:

| Document type | Palette | Primary color | Accent color |
| --- | --- | --- | --- |
| Client deliverable, report | Coastal Clarity | `#1B2A4A` | `#C49A2E` |
| Proposal, investor brief | Indigo Olive Saffron | `#1F2A60` | `#F2A900` |
| Workshop workbook, playbook | Cobalt Grove | `#1E5AA6` | `#FFB000` |
| Keynote leave-behind, thought leadership | Baobab Nightfall | `#14213D` | `#2BD9C5` |

**Default if uncertain:** Coastal Clarity. Apply the Coastal Clarity values from this guide.

---

## PART 8 - XHTML2PDF LAYOUT RULES (PISA ENGINE)

These rules apply to all PDFs generated via xhtml2pdf (pisa). They override general CSS assumptions where xhtml2pdf behavior differs from browsers.

### Rule 1: Cover page must be a single full-bleed navy block

The cover page background is `#1B2A4A` applied to the `.cover` wrapper div. Every child element inside `.cover` must use `margin: 0 0 Xmm 0` (no `margin-top` except on the first element's `padding-top`). Using large `margin-top` values on child divs creates visible white gaps between elements against the navy background because xhtml2pdf renders each element's background independently.

**Correct pattern:**

```css
.cover { background-color: #1B2A4A; padding: 18mm 20mm; height: 297mm; width: 210mm; }
.cover-category { margin: 0 0 4mm 0; padding-top: 10mm; }
.cover-title    { margin: 0 0 4mm 0; }
.cover-gold-bar { margin: 0 0 4mm 0; height: 4px; background-color: #C49A2E; }
.cover-subtitle { margin: 0 0 5mm 0; }
.cover-prepared { margin: 0 0 3mm 0; }
.cover-meta     { margin: 0; }
```

**Anti-pattern (causes white gaps):**

```css
.cover-category { margin-top: 16mm; margin-bottom: 8mm; } /* wrong */
.cover-subtitle { margin-bottom: 12mm; }                  /* too large */
```

Total rendered height of all cover child elements must fit inside: `297mm - (top padding + bottom padding)`. If any element overflows, it creates a second page with a lone orphaned block on a white background.

### Rule 2: No orphaned heading at bottom of page

A heading that appears at the bottom of a page with no body content following it on the same page is an orphan. This is unprofessional and never acceptable in a final document.

**Required CSS for all headings in xhtml2pdf:**

```css
h1, h2, h3, h4 {
    page-break-after: avoid;
    -pdf-keep-with-next: true;
}
```

Both properties are required. `page-break-after: avoid` alone is insufficient in xhtml2pdf. `-pdf-keep-with-next: true` is the pisa-specific property that actually keeps the heading glued to the content that follows it. Never use one without the other.

**What is allowed:** A paragraph that begins on one page and continues on the next. Body text may break across pages. Only headings are subject to this rule.

### Rule 3: No lone block on an otherwise empty page

If a cover page, section header, or callout box is the only content on a page with nothing else following it on that page, it is an orphaned block. Fix by:

1. Reducing element sizes and margins so content fits on its intended page
2. Using `<pdf:nextpage />` deliberately only when you want a true page break with content immediately following on the next page
3. Never placing `<pdf:nextpage />` after content that already ends near a page boundary without verifying the next page has sufficient content

---

## PART 9 - PRODUCTION CHECKLIST

Before exporting or sending any PDF, verify every item:

- [ ] Cover page: full-bleed `#1B2A4A` background, no white margin showing
- [ ] Gold 4px accent bar present below cover page title
- [ ] Every H2 has gold underbar (2px solid `#C49A2E`)
- [ ] No italic used for emphasis (only bold for emphasis; italic for quotes and definitions)
- [ ] Body text is `#2C2C2C`, never a primary color
- [ ] Table header rows are `#1B2A4A` background with white text
- [ ] Code blocks use `#2C2C2C` background and `#E8C86A` text in JetBrains Mono
- [ ] Pull quotes use Source Serif 4 italic in `#C49A2E` with left border
- [ ] Running header and footer present on all pages except cover
- [ ] File name follows `YYYYMMDD_DocumentType_ClientOrProject_v1.pdf` format
- [ ] Version number present in filename
- [ ] No generic stock imagery (handshakes, diverse teams around laptops)
- [ ] Fonts embedded in PDF export (not outlined - embedded for accessibility)
