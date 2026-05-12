# Craft Reference Library

These 9 files are the craft knowledge behind the rules in `frontend-design/SKILL.md`. Source: Impeccable design system (github.com/pbakaus/impeccable, MIT, fork of Anthropic's frontend-design).

The skill itself contains the *rules* (what's banned, what's required, the procedure). These references contain the *craft knowledge* an agent needs to make non-trivial decisions when the rules don't dictate the answer.

## When to load these

- **typography.md** — when picking fonts (after running the font procedure in SKILL.md), making type-scale decisions, or asking "what does this text want to feel like"
- **color-and-contrast.md** — when picking palette anchors, checking accessibility, or choosing how colors should interact
- **spatial-design.md** — when laying out a section that doesn't fit a standard archetype, working with whitespace, or picking spacing tokens
- **motion-design.md** — when adding animations, picking easing, or deciding between scroll-trigger / hover / page-load motion
- **interaction-design.md** — when building hover, focus, click, drag, or any user-input affordance
- **responsive-design.md** — when adapting a desktop design for tablet/mobile, picking breakpoints, or handling touch targets
- **ux-writing.md** — when writing button labels, error messages, empty states, microcopy, or any in-product text
- **cognitive-load.md** — when a page has many sections/elements and you need to decide what to cut, hide, or hierarchy-rank
- **heuristics-scoring.md** — when scoring a design against principles (this overlaps with `design-audit` skill)

## How to load

Read the relevant file(s) before making the decision. Don't read all 9 every time — that's noise. Pick the 1-2 that match the question you're answering.

## Provenance

Pulled 2026-04-29 from `https://raw.githubusercontent.com/pbakaus/impeccable/main/source/skills/impeccable/reference/`. Refresh by re-running:

```powershell
$base = "https://raw.githubusercontent.com/pbakaus/impeccable/main/source/skills/impeccable/reference"
@('typography','color-and-contrast','spatial-design','motion-design','interaction-design','responsive-design','ux-writing','cognitive-load','heuristics-scoring') | ForEach-Object {
  Invoke-WebRequest -Uri "$base/$_.md" -OutFile "$env:USERPROFILE\.claude\skills\frontend-design\reference\$_.md" -UseBasicParsing
}
```
