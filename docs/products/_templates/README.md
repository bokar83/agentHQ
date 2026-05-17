# Product PDF Deliverable Templates

Shared HTML templates for generating per-SKU PDF deliverables across the humanatwork.ai catalog.

## Folder structure

| Path | Purpose |
|---|---|
| `template-v1-editorial.html` | V1 Editorial design system (Fraunces display + Spectral body + JetBrains Mono labels). Calm publishing-house feel. |
| `template-v2-mono.html` | V2 Operator Manual (JetBrains Mono everywhere + IBM Plex Sans display + brick accents). Technical field-guide feel. |
| `template-v3-magazine.html` | V3 Magazine Editorial (Fraunces display + drop caps + dossier grid + double-rule pull-quote). Curated publication feel. |
| `_samples/` | Sample-render PDFs for review (built from start-ai-24h content). Boubacar approved 2026-05-16. |
| `_archived/` | Iteration history. Never delete per `feedback_no_delete_archive_instead`. |

## Tier-to-template mapping (locked 2026-05-16)

| Tier | Price range | Template | SKUs |
|---|---|---|---|
| AI starter | $27 to $79 | **V3 Magazine** | start-ai-24h, paste-pack, ai-notion-stack |
| Job-hunt + career-pivot | $27 to $147 | **V1 Editorial** | resume-surgeon, interview-prep, salary-negotiation, layoff-survival, linkedin-profile-audit, career-os-notion, first-gen-playbook, hr-career-memoir, resume-dfy |
| Operator playbooks | $147 to $497 | **V2 Mono** | how-we-built-agentshq, ai-department-of-one, cw-pipeline, audit-pattern-catalog, ctq-quality-gate, cold-email-pack, failed-business-postmortem |
| Trades + content | $79 to $297 | **V2 Mono** | trade-business-ai, trade-seo-dfy, trade-phone-assistant-dfy, content-multiplier, website-teardown-audit |
| Bundles | $147 to $497 | **V1 Editorial** | solo-operator-bundle, catalyst-operator-bundle |
| DFY service | $2,997 | **V1 Editorial truncated** | ai-audit-smb-dfy (Calendly product, not file-deliverable) |

## Voice + brand rules (HARD)

- **First name only.** "Boubacar" not "Boubacar Barry".
- **No em-dashes anywhere.** Use commas, colons, periods.
- **No credential reciting.** No "14 years corporate HR", no "ex-corporate HR". Locked 2026-05-16 per `feedback_boubacar_ai_tenure.md`.
- **AI-operator-tenure signal:** use `Built in the trench. Sold from the trench.` (or equivalent proxy). Boubacar has been a paying AI user since 2023, ChatGPT user since Nov 2022. Don't use literal years.
- **Bio line (Option A, approved 2026-05-16):** `By Boubacar · Built in the trench. Sold from the trench. · humanatwork.ai`
- **No DRAFT badges, no single-letter brand-mark blocks.** Per `feedback_no_draft_or_letter_brand_marks.md`.
- **No fabricated lived moments.** Don't invent Boubacar's location, time, or kitchen-table stories. Per `feedback_never_fabricate_boubacar_lived_moments.md`.
- **No refund language above the fold.** Refund goes in FAQ tail only.
- **Verified stats only.** No fabricated metrics.
- **Single CTA per page.** Researcher finding (top Gumroad/LS sellers, 2026-05-16): single "I want this!" button wins.

## Design tokens (palette)

| Token | Hex | Where |
|---|---|---|
| Paper | #F4EFE6 (V1) / #FAFAF8 (V2) / #F7F2E9 (V3) | Body bg (suppressed in print) |
| Ink | #161513 (V1) / #0A0A0A (V2) / #1A1714 (V3) | Body text + dark CTA + prompt block bg |
| Brick | #A8341F (V1) / #C1442C (V2) / #B83520 (V3) | Accent + kicker + brick stripe + dots |
| Bone | #ECE5D6 (V1) / #EFE7D6 (V3) | Pull-quote bg + author-note bg + schedule sidebar (V3) |
| Gold | #C28E26 (V3 only) | Magazine accent for em + CTA highlights |

## Print behavior (locked 2026-05-16)

- Paper body bg is **hidden in print** via `@media print { html, body, .cover { background: white !important; } }`. Reason: saves buyer ink + cleaner page. Decided 2026-05-16.
- Dark CTA + dark prompt block + bone schedule/author-note/pull-quote BACKGROUNDS stay. Brick stripe stays.
- Orphan-words bound with `&nbsp;` on h1 closing phrases (e.g., `two&nbsp;years&nbsp;ago`).
- Per `feedback_headless_print_to_pdf_broken.md`: use Playwright Python `prefer_css_page_size=True` + `print_background=True` for paginated PDFs. NOT `--print-to-pdf` headless flag.

## Render command (Playwright Python)

```python
from playwright.sync_api import sync_playwright
from pathlib import Path
import time

src = Path("docs/products/_templates/template-v1-editorial.html").resolve()
out = Path("docs/products/<slug>/deliverable/<slug>.pdf").resolve()

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    page = browser.new_context().new_page()
    page.goto(f"file:///{src.as_posix()}", wait_until="networkidle", timeout=30000)
    page.evaluate("document.fonts.ready")
    time.sleep(0.5)
    page.pdf(
        path=str(out),
        prefer_css_page_size=True,
        print_background=True,
        format="Letter",
        margin={"top":"0","right":"0","bottom":"0","left":"0"},
    )
    browser.close()
```

## Production per-SKU rule

Each SKU has its own `docs/products/<slug>/deliverable/<slug>.pdf` (the file Gumroad delivers to buyers). The HTML used to generate that PDF lives ALONGSIDE the PDF in the SKU folder (so SKU-specific content edits don't pollute the shared template). Pattern:

```
docs/products/start-ai-24h/
  index.html                     # landing page
  deliverable/
    start-ai-24h.pdf             # production PDF (Gumroad delivers this)
    start-ai-24h-source.html     # PDF source HTML (V1 template clone w/ SKU content)
```

## Iteration policy

When updating templates:
1. Edit in `_templates/template-v*.html`
2. Re-render samples to `_samples/sample-template-v*.pdf`
3. Boubacar approves samples
4. Re-render production PDFs for affected SKUs
5. Old PDFs archived to `_archived/<reason>-<date>/`

## Cross-references

- `feedback_headless_print_to_pdf_broken.md` — Playwright Python is the canonical render path
- `feedback_no_delete_archive_instead.md` — always archive, never delete
- `feedback_no_em_dashes_in_chat.md` — voice rule
- `feedback_boubacar_ai_tenure.md` — AI-operator positioning, no creds reciting
- `feedback_stop_default_dot_logo_pattern.md` — don't lean on text+dot logo as default
- `docs/research/gumroad-ls-closer-patterns-2026-05-16.md` — listing template research
