# shadcn-style PDF generation

For structured business PDFs (invoice, statement, report, proposal, statement of work) where layout consistency and brand fidelity matter more than narrative design.

## Primary tool: pdfx

[github.com/akii09/pdfx](https://github.com/akii09/pdfx)

- Wraps `@react-pdf/renderer` in shadcn's copy-paste pattern
- Pre-built layouts: invoice, statement, report
- Brand color flows from your `globals.css` (use the theming reference for tokens)

## Quick start

```bash
npx pdfx add invoice
# or: npx pdfx add statement
# or: npx pdfx add report
```

Customize copy and brand color (use the tokens from `shadcn-theming.md`), ship.

## When to use this lane vs others

- **Structured business PDF** (invoice, SOW, statement, ops report): use `pdfx`. Layout matters more than narrative.
- **Narrative PDF** (CW client memo, thought-leadership doc, executive brief): use the `slides` skill or the `hyperframes` path. Storytelling matters more than layout.
- **Pitch deck**: use `slides` (Chart.js + design-system tokens) or `hyperframes` for video-driven decks.

## Routing

- `skills/design` sub-skill table points here for structured PDFs.
- `skills/clone-builder` can generate invoice/statement skeletons via `pdfx` if a clone target needs a billing surface.

Borrowed from awesome-shadcn-ui curation (2026-05-02 absorb).
