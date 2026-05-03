# PDF Design Addendum: "Humanized Standard"
**agentsHQ: PDF and Print Output Quality Gate**
*Supplements skill_design_human.md for all PDF, document, and slide outputs.*

---

## The PDF Problem

PDF outputs from agentsHQ suffer the same AI-slop issues as web builds, with additional print-specific failures:

1. **Gradient fills that don't print.** CSS gradients render beautifully on screen and vanish or corrupt in PDF export. Clients receive documents with blank backgrounds where branded gradients should appear.

2. **Inter for body text.** Inter is optimized for screen rendering at small sizes. At print resolutions (300 DPI, 11pt body copy), it lacks the typographic texture of a proper text serif. Reading a long document set in Inter is noticeably less comfortable than reading one set in Georgia or Source Serif 4.

3. **Box-shadows wasting space.** Box-shadow properties render as transparent in print, leaving extra whitespace where the shadow "area" was. This breaks layouts intended for screen.

4. **Misaligned columns in data tables.** Proportional-width numerals (the default in most fonts) cause columns to misalign. "100" and "99" do not line up correctly unless tabular figures are enabled.

5. **Chart colors that fail in grayscale.** When a client prints in black and white, a line chart with 5 colored lines becomes indistinguishable. No labels, no patterns, no alt text.

6. **Font sizes below 9pt.** Caption text, footnotes, and table headers at 7-8pt are readable on screen. On paper, they are not.

---

## PDF Base Stylesheet

File: `skills/frontend-design/components/pdf/pdf-base.css`

Import this in every HTML-to-PDF template. Place it after the web stylesheet so print rules override screen rules.

```css
/* PDF BASE: agentsHQ Humanized Standard */
/* Import after the web stylesheet: @import "./pdf-base.css" */

@media print {

  /* === Typography === */

  body {
    font-family: "Source Serif 4", "Tiempos Text", Georgia, "Times New Roman", serif;
    font-size: 11pt;
    line-height: 1.7;
    color: #1a1a1a;
    background: white !important;
  }

  h1 {
    font-family: var(--pdf-heading-font, "Neue Montreal", "DM Sans", Helvetica, Arial, sans-serif);
    font-size: 28pt;
    font-weight: 700;
    letter-spacing: -0.02em;
    line-height: 1.15;
    color: #0f0f11;
    margin-bottom: 0.5em;
    page-break-after: avoid;
  }

  h2 {
    font-family: var(--pdf-heading-font, "Neue Montreal", "DM Sans", Helvetica, Arial, sans-serif);
    font-size: 18pt;
    font-weight: 700;
    letter-spacing: -0.01em;
    line-height: 1.2;
    color: #0f0f11;
    margin-top: 1.5em;
    margin-bottom: 0.4em;
    page-break-after: avoid;
  }

  h3 {
    font-family: var(--pdf-heading-font, "Neue Montreal", "DM Sans", Helvetica, Arial, sans-serif);
    font-size: 13pt;
    font-weight: 600;
    color: #1a1a1a;
    margin-top: 1em;
    margin-bottom: 0.3em;
    page-break-after: avoid;
  }

  p {
    font-size: 11pt;
    line-height: 1.7;
    margin-bottom: 0.8em;
    orphans: 3;
    widows: 3;
  }

  /* Caption and footnote text */
  .caption,
  figcaption,
  .footnote,
  table caption {
    font-family: var(--pdf-heading-font, "DM Sans", Helvetica, Arial, sans-serif);
    font-size: 9pt;
    line-height: 1.4;
    color: #555;
    letter-spacing: 0.01em;
  }

  /* === Eliminate screen-only visual effects === */

  * {
    background-image: none !important;  /* No gradients in print */
    box-shadow: none !important;        /* No shadows in print */
    text-shadow: none !important;
    -webkit-print-color-adjust: exact;  /* Preserve background colors (for headers, chart fills) */
    print-color-adjust: exact;
  }

  /* === Numeric data === */

  table,
  .data-table,
  .chart-label,
  .metric,
  .stat {
    font-variant-numeric: tabular-nums;
    font-feature-settings: "tnum" 1;
  }

  /* === Page layout === */

  @page {
    margin: 2.5cm 2cm 2.5cm 2cm;
  }

  @page :first {
    margin-top: 3cm;
  }

  /* === Page breaks === */

  h1, h2, h3 { page-break-after: avoid; }
  table { page-break-inside: avoid; }
  figure { page-break-inside: avoid; }
  ul, ol { page-break-inside: avoid; }

  .page-break-before { page-break-before: always; }
  .page-break-after  { page-break-after: always; }
  .no-break          { page-break-inside: avoid; }

  /* === Links === */

  a[href]::after {
    content: " (" attr(href) ")";
    font-size: 9pt;
    color: #555;
  }

  a[href^="#"]::after,
  a[href^="javascript:"]::after {
    content: "";  /* Don't print internal/script links */
  }

}
```

---

## PDF Archetype Typography Map

| Web archetype | PDF heading font | PDF body font | Notes |
|---|---|---|---|
| CALM_PRODUCT | DM Sans 700 or Geist Sans 700 | Source Serif 4 400 or Georgia | Functional, clean, trustworthy for technical audiences |
| EDITORIAL_NARRATIVE | Tiempos Text or Playfair Display | Tiempos Text 400 | Off-white (#faf8f4) background if client printer allows it |
| CINEMATIC_AGENCY | Neue Montreal 700 or Clash Display | Neue Montreal 400 | Use generous margins (3cm+) and large display type on cover pages |
| DOCUMENTARY_DATA | IBM Plex Sans 600 | IBM Plex Sans 400 | Tabular figures mandatory; pattern fills on all charts |
| TRUST_ENTERPRISE | Garamond or Freight Display | Georgia 400 | Most traditional; Garamond at 12pt reads beautifully in print |
| ILLUSTRATIVE_PLAYFUL | Poppins 700 | Poppins 400 | Consider whether PDF is the right format for this archetype |
| BRUTALIST | Helvetica Neue 900 | Courier New 400 | Print renders this archetype's intent clearly |
| CONVERSION_FIRST | DM Sans 700 | DM Sans 400 | PDF is unusual for this archetype; use only for proposals |

---

## Chart Color System for PDF

### Screen + Color Print
Use the colorblind-safe palette from `craft-tokens.css`. Define these as CSS custom properties:

```css
--chart-1: #2563eb;  /* Blue */
--chart-2: #d97706;  /* Amber */
--chart-3: #16a34a;  /* Green */
--chart-4: #dc2626;  /* Red */
--chart-5: #7c3aed;  /* Purple */
--chart-6: #0891b2;  /* Cyan */
--chart-7: #c026d3;  /* Fuchsia */
```

**Avoid:** Red + Green pairs (8% of males are red-green colorblind). Avoid Tailwind defaults (indigo, slate) as they lose distinction in print.

### Black and White Print Fallback

Add pattern fills to all chart elements as a fallback for B&W printing. The pattern library:

```css
/* CSS pattern fills for charts: B&W safe */
.chart-fill-1 { fill: #000000; }                          /* solid black */
.chart-fill-2 { fill: url(#pattern-diagonal-right); }    /* diagonal lines right */
.chart-fill-3 { fill: url(#pattern-diagonal-left); }     /* diagonal lines left */
.chart-fill-4 { fill: url(#pattern-horizontal); }        /* horizontal lines */
.chart-fill-5 { fill: url(#pattern-dots); }              /* dots */
.chart-fill-6 { fill: url(#pattern-crosshatch); }        /* crosshatch */
.chart-fill-7 { fill: #888888; }                         /* gray */
```

Include SVG `<defs>` patterns in the HTML template and apply via CSS. Pattern fills survive export to PDF and render correctly in B&W print.

---

## PDF AI-Tells to Eliminate

| Tell | Signal in PDF | Fix |
|---|---|---|
| Inter body copy | Dense paragraphs set in Inter feel screen-native, not document-native | Replace with Source Serif 4 or Georgia for print |
| Gradient backgrounds | Blank or corrupt areas where gradient should appear | Remove all `background-image: linear-gradient()` in print stylesheet |
| Tailwind chart colors | Indigo line, violet bar, emerald accent: all look similar in B&W | Replace with the colorblind-safe + pattern fill system |
| No page breaks | Content split awkwardly mid-heading or mid-table | Add `page-break-before: always` on new sections; `page-break-after: avoid` on headings |
| Equal-column feature grids | Three identical boxes side by side with line spacing that does not survive print | Replace with numbered list or 2+1 layout |
| 7-8pt footnotes | Illegible after print from any consumer printer | Minimum 9pt for all printed text |
| Proportional numeral columns | Data columns misalign when numbers have different digit widths | Add `font-variant-numeric: tabular-nums` to all table and data elements |

---

## Slide-Specific Rules

For HTML slides generated via the `slides` skill:

1. **Slides are not PDFs.** They are designed to be presented on screen. The PDF export of slides (via print to PDF) must be tested separately.

2. **Font sizes in slides:** Minimum 24pt for body copy, minimum 36pt for section headings, minimum 48pt for slide titles. These sizes ensure readability at projection distance.

3. **Slide backgrounds:** Avoid pure white backgrounds for projected slides (causes eye strain in dark rooms). Use a warm off-white (`#f8f6f2`) or a dark base (`#0f0f11`) depending on the archetype.

4. **Animation in slides:** Use `@media (prefers-reduced-motion: no-preference)` to conditionally apply slide transitions. Always test with animations disabled (for printed or accessibility contexts).

5. **Chart readability in slides:** At least 18pt for axis labels. Use the colorblind-safe palette. Never rely on color alone to distinguish data series: always add a text label directly on or next to each series.

---

## PDF Verification Checklist

Before delivering any PDF to a client:

```
[ ] Print stylesheet is loaded (@media print rules apply)
[ ] No background-image properties in any printed element
[ ] No box-shadow properties in any printed element
[ ] Body font is a print-appropriate serif or high-quality sans
[ ] All numeric data uses tabular figures (font-variant-numeric: tabular-nums)
[ ] All chart colors pass colorblind safety check (no red-green pairs)
[ ] Pattern fills exist for B&W print scenario
[ ] No text below 9pt
[ ] Page breaks prevent headings from appearing orphaned at bottom of page
[ ] Links to external URLs print their href as visible text
[ ] Document renders correctly at 300 DPI (test at 1:1 zoom in browser before export)
[ ] Tested in: Chrome Print to PDF, and if budget allows, physical print from a consumer printer
```
