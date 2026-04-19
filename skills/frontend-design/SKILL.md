---
name: frontend-design
description: Use when creating, updating, or reviewing any website, landing page, or HTML/CSS artifact — before writing any code
---

# Frontend Design Skill

## Rule

**No HTML/CSS before this skill completes. Every time. No exceptions.**

This applies to: new sites, redesigns, section updates, single-page tweaks, clones, and app UIs.

---

## Step 1 — Identify the project type

Is this Catalyst Works output?

Output is Catalyst Works branded if the request mentions: "catalyst works", "boubacar", "my consulting", "our brand", "cw", "catalystworks.consulting", or is for Boubacar's personal brand.

- **Yes → go to Step 2A**
- **No → go to Step 2B**

---

## Step 2A — Catalyst Works output

Load both files before writing any code:

```
docs/styleguides/styleguide_master.md
docs/styleguides/styleguide_websites.md
```

Key non-negotiables from the styleguide:
- Color: `#071A2E` (Midnight Navy) as dark anchor, `#B47C57` (Clay) as accent warmth, `#00B7C2` as primary action color
- Headlines: Plus Jakarta Sans (600/700/800) — never Inter at display scale
- Body: Inter (400/500/600)
- Data/code: JetBrains Mono
- No red tones anywhere, no purple gradients, no three-rounded-boxes-in-a-row
- First visible element leads with a specific claim, not a category description

Run the self-scoring checklist from `styleguide_master.md` before returning output.

---

## Step 2B — Non-Catalyst Works output

1. Read `docs/design-references/INDEX.md`
2. Pick the best-match brand reference for this project type using the table below
3. Read `docs/design-references/{brand}.md`

If the reference `.md` file is missing locally, run:
```bash
bash scripts/fetch_design_references.sh
```

### Quick reference picker

| Project type | Default reference |
|---|---|
| B2B SaaS / productivity | `linear.app` |
| Payments / premium trust | `stripe` |
| AI product with warmth | `claude` |
| Dev tool / dark mode | `cursor` or `warp` |
| No-code / consumer app | `lovable` |
| Deployment / infra | `vercel` |
| Docs / portal | `mintlify` |
| Analytics / data | `posthog` |
| Marketplace / hospitality | `airbnb` |
| General fallback | `resend` |

Apply the selected brand's: color system, typography, spacing, layout patterns, and tone throughout.

---

## Step 3 — Design brief before code

State out loud (one short paragraph) before writing any HTML:
- Which reference or styleguide was loaded
- The 3 most important design constraints that apply to this project
- Any anti-patterns to avoid

This is the proof the skill ran. Skip it = skill did not run.

---

## Step 4 — Mobile-first

Build at 375px first. Then 1280px desktop. Then 768px tablet. Verify all three before marking complete.

---

## Step 5 — Pre-launch checklist (for any site going live)

- [ ] Favicon wired
- [ ] OG image at 1200×630px
- [ ] `sitemap.xml` present
- [ ] `robots.txt` present
- [ ] GA4 wired
- [ ] `ads.txt` present (AdSense sites only)
- [ ] No placeholder text or broken links
- [ ] Schema.org JSON-LD present
- [ ] Forms wired (Formspree for static sites)
- [ ] GitHub push in same session as build

---

## Red flags — stop if you catch yourself thinking:

- "I'll load the reference after I get the structure down" → **stop, load it first**
- "This is just a small update, not a full redesign" → **still load it**
- "I know the brand well enough from memory" → **still read the file**
- "The user is in a hurry" → **still load it — takes 30 seconds**
