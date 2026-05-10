# Styleguide Index — Brand Routing Table

**Single lookup for all design-producing agents and skills.**

Before producing any visual output (HTML, slides, PDF, video, social graphic), read this file first. Find the brand slug. Load the files listed. Tokens and rules in those files override any defaults.

---

## Brand Registry

| Brand slug | Full name | Files to load | Notes |
|---|---|---|---|
| `cw` | Catalyst Works Consulting | `docs/styleguides/CURRENT_TYPOGRAPHY.md` + `docs/styleguides/styleguide_master.md` + `docs/styleguides/styleguide_websites.md` | Load all three for web. For PDF: replace `styleguide_websites.md` with `styleguide_pdf_documents.md`. For social: add `styleguide_linkedin.md` or `styleguide_x_twitter.md`. |
| `sw` | Signal Works / geolisted.co | `docs/styleguides/CURRENT_TYPOGRAPHY.md` + `docs/styleguides/styleguide_master.md` + `docs/styleguides/styleguide_websites.md` | SW builds inherit CW visual DNA. SW-specific overrides live in `docs/styleguides/signal-works.DESIGN.md` once created. |
| `utb` | Under the Baobab | `docs/styleguides/studio/under-the-baobab.DESIGN.md` | Full DESIGN.md spec. Earthy African palette. |
| `1stgen` | First Generation Money | `docs/styleguides/studio/first-generation-money.DESIGN.md` | Full DESIGN.md spec. Calm authority palette. |
| `aic` | AI Catalyst | `docs/styleguides/studio/ai-catalyst.DESIGN.md` | Full DESIGN.md spec. Dark mode, electric accent. |

---

## How to use this index

**In any skill before producing visual output:**
1. Identify the brand slug from context (project name, user request, channel name)
2. Load the file(s) listed for that slug
3. YAML token block (if present) = authoritative values. Extract values between the first `---` delimiters. Prose sections provide rationale and anti-patterns.
4. Never re-derive brand colors, fonts, or spacing from scratch — if the file exists, use it

**If brand is ambiguous:** default to `cw` for Catalyst Works / consulting / Boubacar personal brand work.

**If brand slug is not in this table:** check `docs/roadmap/studio/channels/` for a channel brief, then ask before inventing.

---

## File map

```
docs/styleguides/
  INDEX.md                              ← this file
  CURRENT_TYPOGRAPHY.md                 ← CW typography stack (source of truth)
  styleguide_master.md                  ← CW brand essence, voice, anti-patterns
  styleguide_websites.md                ← CW web tokens, components, layout
  styleguide_pdf_documents.md           ← CW PDF/document standards
  styleguide_linkedin.md                ← CW LinkedIn voice + format
  styleguide_x_twitter.md              ← CW X/Twitter voice + format
  styleguide_markdown.md                ← CW markdown document standards
  newsletter.md                         ← CW newsletter standards
  studio/
    under-the-baobab.DESIGN.md          ← UTB brand spec (DESIGN.md format)
    first-generation-money.DESIGN.md    ← 1stGen brand spec (DESIGN.md format)
    ai-catalyst.DESIGN.md               ← AIC brand spec (DESIGN.md format)
  design.md.template                    ← Template for new brand DESIGN.md files
```

---

## Verification criterion

After loading this index and the brand files: agent should be able to answer "what is the primary color hex for this brand?" without reading any other file or asking Boubacar.
