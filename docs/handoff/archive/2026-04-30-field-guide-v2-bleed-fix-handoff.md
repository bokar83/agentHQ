# Handoff - AI Governance Field Guide V2 (PDF bleed fix + ship)
**Date:** 2026-04-30
**Status:** Pages 8 and 12 still bleed. Fix, re-render at 180 dpi, then ship to LinkedIn Featured #4.

---

## What this is

The AI Governance Field Guide V2 is Catalyst Works' LinkedIn Featured #4 lead magnet. A digital-first A4 PDF, 13 pages, asymmetric editorial spread. The artifact reads like a Bloomberg Businessweek special issue, not a consulting deck.

**Format decision (locked):** A4 (210 × 297 mm), digital-first delivery. Recipients who print select "Fit to Page." Reasoning lives in `C:/Users/HUAWEI/.claude/projects/d--Ai-Sandbox-agentsHQ/memory/reference_pdf_us_letter_default.md` (dual-mode rule: Letter for print-primary, A4 for digital-first).

**Aesthetic stack (locked):**
- Display: Bodoni Moda (italic ampersand, kiln-orange accents at 92pt cover, 32pt sections, 80pt drop cap)
- Pull quotes: Spectral 500 italic at 22pt (NOT Bodoni Moda body - Didone hairlines failed at body weight)
- Body: Geist 10.5pt / 1.5
- Mono: Geist Mono (data callouts only)
- Palette: paper #F5F0E6 + ink #1A1A1F + kiln-orange #C4422E (5-6 places only - discipline)
- Layout: 38mm meta-rail (col-meta) + 1fr body (col-body); fixed 297mm page height with `overflow: hidden`

**Design audit:** 18/20 - Excellent. Full audit at `workspace/design-audits/field-guide-v2-audit.md`.

---

## The blocker

User saw the PDF and said: **"page 8 and page 12 bleed"**

I had declared all 13 pages clean based on 110 dpi snapshots. 180 dpi inspection revealed:

**Page 8** (`The Legal Map`)
- The closing paragraph after the regulations table sits on top of the 8mm footer hairline rule.
- Text: *"A December 2025 executive order directed the DOJ to challenge state AI laws. The landscape may shift. **The state laws change. The fundamentals do not.**"*
- Source: `field-guide-v2.html` lines 1397
- Root cause: Regulations table is 5 rows + the paragraph is 3 lines. The page can hold the table OR the paragraph cleanly, not both at current type sizes.

**Page 12** (`Your Move` - primary CTA)
- The secondary CTA grid (Calendar / Engage / Speak / Follow rows) bleeds at the bottom.
- The Follow row + the closing forwarding paragraph at line 1637 ("If you have a COO, head of operations...") clip below the footer.
- Source: `field-guide-v2.html` lines 1614-1637
- Root cause: cta-block contains H3 + intro + 4 cta-rows + a forward paragraph below the block. Too tall for 297mm minus padding minus footer.

---

## Fix plan (recommended - pick one per page)

### Page 8 - recommended: **delete the closing paragraph entirely**

Why: The section title "The legal map." plus the regulations table already carry the message. The closing paragraph is editorial flourish. The strongest cut.

Action: Delete lines 1397 (`<p>A December 2025 executive order...`).

Alternate (less drastic): Tighten `.data-table` cell padding from `2.5mm 4mm` to `2mm 3.5mm` to reclaim ~5mm vertical. Risk: rows look cramped. Try the cut first.

### Page 12 - recommended: **merge Follow into Speak, drop the forward paragraph**

Why: Follow and Speak both reference contact channels. The forward paragraph at line 1637 is good-but-cuttable copy that exists outside the cta-block.

Actions:
1. Delete the Follow cta-row (lines 1631-1634).
2. Add LinkedIn to the Speak row OR add a single line under cta-block: `<p style="font-size: 9.5pt; color: var(--ink-soft); margin-top: 4mm;">Follow on LinkedIn at <a href="https://linkedin.com/in/boubacarbarry">linkedin.com/in/boubacarbarry</a></p>`
3. Delete the forwarding paragraph at line 1637 entirely OR move its content to page 13 above the closing observation.

Alternate: Tighten `.cta-row` padding and font, but the structure-level cut is cleaner.

---

## Render command

Windows bash. The chrome.exe path may need adjustment - verify with `where chrome` or check `C:/Program Files/Google/Chrome/Application/chrome.exe`.

``bash
"/c/Program Files/Google/Chrome/Application/chrome.exe" \
  --headless=new --disable-gpu --no-pdf-header-footer \
  --print-to-pdf="d:/Ai_Sandbox/agentsHQ/deliverables/ai-governance/CW_Field-Guide_AI-Governance_v1.pdf" \
  --no-margins --virtual-time-budget=15000 \
  "file:///d:/Ai_Sandbox/agentsHQ/workspace/articles/2026-04-30-ai-governance-field-guide-assets/field-guide-v2.html"
``

---

## Verification - 180 dpi mandatory

Lower DPI hides sub-millimeter overlap. Always 180+.

``python
import fitz
pdf = fitz.open("d:/Ai_Sandbox/agentsHQ/deliverables/ai-governance/CW_Field-Guide_AI-Governance_v1.pdf")
print(f'Pages: {pdf.page_count}, Size: {pdf[0].rect.width/72:.2f} x {pdf[0].rect.height/72:.2f} in')
# Expected: 13 pages, 8.27 x 11.69 in (A4)
import os
out_dir = "d:/Ai_Sandbox/agentsHQ/workspace/articles/2026-04-30-ai-governance-field-guide-assets/_render-check"
os.makedirs(out_dir, exist_ok=True)
for i in range(pdf.page_count):
    pix = pdf[i].get_pixmap(dpi=180)
    pix.save(f'{out_dir}/page-{i+1:02d}.png')
print("Done - read every PNG and check footer area")
``

**Acceptance criteria:**
- Body content terminates above the 8mm footer hairline on every page.
- No clipping.
- All 13 pages: A4 (8.27 × 11.69 in).
- Read every snapshot at 180 dpi before declaring clean. Read pages 8 and 12 first.

---

## Hard rules in play

- `feedback_no_em_dashes.md` - no em dashes anywhere.
- `feedback_em_dash_first_pass_audit_required.md` - `grep -E '-|-|--' field-guide-v2.html` before declaring done. Expect zero hits.
- `reference_pdf_us_letter_default.md` - A4 digital-first is correct for this artifact. Do NOT switch to Letter.
- `feedback_no_em_dashes.md` applies to memory writes too.
- `feedback_visual_bug_debugging.md` - render and READ the snapshot, never CSS-edit blind.

---

## Key files

| Purpose | Path |
|---|---|
| HTML source | `d:/Ai_Sandbox/agentsHQ/workspace/articles/2026-04-30-ai-governance-field-guide-assets/field-guide-v2.html` |
| Output PDF | `d:/Ai_Sandbox/agentsHQ/deliverables/ai-governance/CW_Field-Guide_AI-Governance_v1.pdf` |
| Snapshots | `workspace/articles/2026-04-30-ai-governance-field-guide-assets/_render-check/page-NN.png` |
| Design audit | `workspace/design-audits/field-guide-v2-audit.md` |
| Memory rule (page size) | `C:/Users/HUAWEI/.claude/projects/d--Ai-Sandbox-agentsHQ/memory/reference_pdf_us_letter_default.md` |

Ignore `_render-check/render-pages.html` - failed iframe approach, do not edit.

---

## After the fix lands

1. **Ship the PDF** - Boubacar uploads to LinkedIn Featured slot #4. Title: `Field Guide: AI Governance for Mid-Market Firms`. Description: `12-section field guide for COOs, ops leads, and AI committee chairs. Real legal landscape. Real diagnostic questions. No frameworks for sale.`

2. **Closeout list** (deferred from previous session):
   - 12-post agentsHQ supporting content job - schedule via Blotato.
   - Telegram nudge to Boubacar with the Featured URL when live.
   - MEMORY.md index - verify the dual-mode A4/Letter rule entry is current.

3. **CTQ check on the artifact itself** - the field guide hits multiple CTQ targets. Skip another full council; the design audit (18/20) is sufficient for ship.

---

## What NOT to do

- Do NOT re-render at 110 dpi and call it clean. 180 dpi minimum.
- Do NOT change page size to Letter. A4 is locked. Memory rule was just updated.
- Do NOT add em dashes. Periods only.
- Do NOT redesign the page. Cut content, do not restructure.
- Do NOT touch other pages (1-7, 9-11, 13). They render clean at 180 dpi.
- Do NOT bundle "while I'm here" cleanup into this fix. Two pages, two surgical cuts, ship.

---

## Voice + brand checks (skim before any prose change)

- Boubacar is NOT a TOC consultant. Eight-lens diagnostic.
- Facilitator not hero. Partner, never savior.
- No fabricated client stories. The whole guide is operator framing, no "I worked with a firm that..."
- No coffee/alcohol props. No "Tuesday morning with your coffee."
- Direct, opinionated, earned voice.

---
