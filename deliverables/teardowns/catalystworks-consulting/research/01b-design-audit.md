# Phase 2: Design / UX / Accessibility Audit

**Target:** https://catalystworks.consulting/
**Audited:** 2026-05-01
**Source:** Vercel Web Interface Guidelines (https://github.com/vercel-labs/web-interface-guidelines) + agentsHQ project hard rules
**Method:** live DOM inspection at 1440x900 desktop and 390x844 mobile via Playwright

---

## Verdict at a glance

**Overall craft score: 68 / 100.** Strong on visual identity, voice, and offer architecture. Bleeds on accessibility, brand-rule violations (em-dashes, missing real logo), broken nav anchors, and unwired form. Most fixes are 1-line edits. Two are structural.

**Severity legend:**
- HIGH (ship-blocking, accessibility / brand violation, broken UX)
- MED (degrades quality, should be fixed in v2)
- LOW (polish, nice-to-have)

---

## Findings

### 1. (HIGH) Real CW logo not used in header (BRAND VIOLATION)

**Inherits HARD RULE #2 from `website-intelligence`.** The actual brand mark (`CatalystWorks_logo.jpg`, circular CW with cyan + clay arcs and orange accent dot) exists on the server as the favicon. The header renders a plain HTML text logotype ("Catalyst" white + "Works" cyan) instead. The text logotype reads as a placeholder. The real logo reads as a brand.

**Where:** site header, footer, OG card.
**Fix:** swap text-logotype for `<img src="CatalystWorks_logo.jpg" alt="Catalyst Works" class="brand-logo">` in header and footer. Use the JPG mark scaled to ~36px height in nav, ~48px in footer.

### 2. (HIGH) Nine em-dashes in body copy (BRAND VIOLATION)

The project has a hard "no em-dashes anywhere" rule. The site contains 9 em-dashes in visible body text. Examples seen: "...one named constraint, written, specific, and cross-functional, plus three friction signals..." in mid-page section bleeds and FAQ schema.

**Fix:** global find-and-replace em-dash with periods or commas depending on context. 5-minute fix. Critical surface: the FAQPage JSON-LD answers, which leak into Google rich snippets.

### 3. (HIGH) Two broken anchor links in main navigation

The nav contains a "How It Works" link pointing to `#offers`. **There is no element with `id="offers"` on the page.** Clicking it does nothing. This appears in the header nav AND in mobile menu, so it's broken in both places.

**Fix:** either rename the link to "Friction Audit" (id="audit" exists) and "Signal Session" (id="signal" exists), or add `id="offers"` to a parent section. The first option is cleaner since "Friction Audit" and "Signal Session" already appear separately.

### 4. (HIGH) `--text-dim` color fails WCAG AA contrast

`rgba(255,255,255,0.35)` on the navy `#071A2E` background gives roughly 3.0:1 contrast. WCAG AA for normal text requires 4.5:1. Any body text using `--text-dim` is non-compliant.

**Fix:** raise `--text-dim` to at least 50% white opacity (~4.4:1, still tight) or 55% (matches `--text-muted`, ~4.6:1). Keep dim only for icons or decorative elements, not paragraph text.

### 5. (HIGH) `<html>` is dark-themed but `color-scheme` not set

Browsers and form controls won't render dark-mode-aware native widgets. The `<select>` dropdowns, scrollbars, and form controls revert to light defaults inside the dark-themed page.

**Fix:** add `<html style="color-scheme: dark">` or `:root { color-scheme: dark }` in CSS. 1-line fix.

### 6. (HIGH) Submit button outside its form

The booking modal's submit button (`class="modal-submit"`, `type="submit"`) is **not inside a `<form>` element**. This breaks: Enter-to-submit, autofill compatibility with browsers, and accessibility expectations for screen readers announcing the form group.

**Fix:** wrap the modal field block in `<form id="signal-session-form">` and put the submit button inside it. Even if submission is JS-handled (Telegram or n8n hook), the form wrapper is still correct semantics.

### 7. (HIGH) Newsletter email input has no associated label

`#nl-email` (the newsletter signup) has no `<label for="nl-email">`. Screen readers will announce only the placeholder text "your@email.com," which is not a label.

**Fix:** add `<label for="nl-email" class="sr-only">Email address</label>` immediately before the input.

---

### 8. (MED) Form fields missing `name` attributes

All four form inputs (modal: name/email/company; newsletter: email) have empty `name=""`. Without `name`, browsers can't autofill, the form can't serialize, and any non-JS submission fallback is impossible.

**Fix:** add `name="name"`, `name="email"`, `name="company"` to the modal fields and `name="email"` to the newsletter input.

### 9. (MED) Form fields not marked `required`

The modal can submit empty. Even if JS validates, the HTML5 `required` attribute is best practice for screen readers and gives a free fallback if JS fails.

**Fix:** add `required` to `#m-name` and `#m-email`.

### 10. (MED) 10 non-button elements with `onclick` handlers

10 `<div>` or `<span>` elements have `onclick=` attributes. Per Vercel Guidelines: "Use `<button>` for actions; `<a>`/`<Link>` for navigation (not `<div onClick>`)."

**Fix:** convert click-handler `<div>`s to `<button type="button">` (or `<a>` for navigation). Adjust CSS to remove default button styling.

### 11. (MED) Sole `<img>` (founder photo) lacks explicit width/height

The Boubacar headshot has no `width=` or `height=` attributes. Causes Cumulative Layout Shift (CLS) when it loads.

**Fix:** add `width="320" height="320"` (or actual dimensions).

### 12. (MED) `--text-muted` (55% white opacity) on navy is borderline AA

Estimated 4.6:1 contrast, technically passes AA for normal text but fails AAA. Some users on dim phone screens will struggle.

**Fix:** raise to 65% opacity for body text, keep 55% for tertiary captions only.

### 13. (MED) Mobile section starts clipped under sticky nav

When mid-page sections come into view on mobile (e.g. the "Structured. Not intuitive." block), their first lines are clipped under the fixed header. Likely missing `scroll-margin-top` on section anchors.

**Fix:** add `section[id] { scroll-margin-top: 80px; }` (or whatever the nav height is).

---

### 14. (LOW) 35 straight quotes, should be curly quotes

Throughout body copy. Use curly quotes for typography polish.

**Fix:** global replace, or use `text-rendering: optimizeLegibility` + a smart-quote pass.

### 15. (LOW) No `<meta name="theme-color">`

Mobile browser chrome (Safari/Chrome address bar) won't match the navy background.

**Fix:** add `<meta name="theme-color" content="#071A2E">`.

### 16. (LOW) No `text-wrap: balance` or `text-pretty` on headings

Vercel guideline. Long H2s on mobile have ragged line endings.

**Fix:** `h1, h2 { text-wrap: balance; }`.

### 17. (LOW) Loading states / async feedback not audited

Modal submission probably triggers a "Request received." state (we saw an H3 with that text). Whether that update uses `aria-live="polite"` for screen readers was not confirmed in this audit. Likely missing.

**Fix:** add `aria-live="polite"` to the modal success container.

### 18. (LOW) Hero image absent

Pure text hero with subtle grid texture. Distinctive choice, but visually thinner than peers (see Phase 3 competitor analysis). Photograph of the founder OR a single high-quality "diagnostic in progress" image (whiteboard, notebook, hands at keyboard) would lift the hero without breaking the brand voice.

**Fix:** add a single right-aligned hero image at desktop (founder portrait or single signature photo). Mobile keeps text-only.

---

## Summary scorecard

| Category | Status |
|---|---|
| Brand identity (logo + palette + voice) | strong palette + voice, missing real logo in header |
| Typography craft | great pairing (Spectral + Public Sans), em-dash and quote violations |
| Accessibility (WCAG AA) | contrast fails (`--text-dim`), form labels missing, color-scheme not set |
| Forms / inputs | submit outside form, no `name`/`required`, label missing |
| Navigation integrity | 2 broken anchor links in nav |
| Mobile rendering | hero clean, mid-page section clipping |
| Performance hints | preconnect (2) and preload (1) ARE set; image format could move to WebP |
| Hero visual interest | text-only, no image |
| Voice + offer architecture | distinctive, single-CTA discipline, scarcity tag, $497 above fold |

## Top 5 fixes for client report (severity-ranked, fastest first)

1. **Replace text-logotype with real CW logo PNG in header + footer.** (5 min)
2. **Fix two broken nav links** (`How It Works` to `#offers` does not exist). (5 min)
3. **Scrub 9 em-dashes from body copy + FAQ JSON-LD.** (5 min)
4. **Wrap the booking modal in a `<form>` and add `required` + `name` attributes to all fields.** (10 min)
5. **Raise `--text-dim` to 50% opacity, set `color-scheme: dark`, add theme-color meta.** (5 min)

**Total time to close all 5 high-severity items: 30 minutes.** Translation: this is not a rebuild question, it's a polish-pass question.

End of Phase 2.
