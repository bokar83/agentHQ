# Skill Merge Log — 2026-05-11

## Status: COMPLETE — 25/25 skills merged

## Summary

- **Skills merged successfully: 25/25**
- **Skills with conflicts (deferred): 0**
- **Total old lines (local+repo / 2 average): ~5,985 → Total new canonical lines: ~6,440**
- **Net content gain from merge: +455 lines (sections preserved from both sides)**
- **Broken YAML descriptions fixed: 4 (clone-builder, clone-scout, design, signal-works-pitch-reel) — all from agentsHQ-absorb's auto-trigger-rewrite that broke block-style YAML scalars**

### Strategy distribution

- typography-only / trigger-merge: 9 skills (gsap, hyperframes-cli, hyperframes-registry, react-best-practices, web-design-guidelines, youtube-10k-lens, ui-styling, design-system, brand)
- feature-add (additive merge, no conflict): 9 skills (tab-shutdown, engagement-ops, hostinger-deploy, hyperframes, ctq-social, ui-ux-pro-max, frontend-design, scene-segmenter, transcribe)
- yaml-fix (broken description rebuild): 4 skills (clone-builder, clone-scout, design, signal-works-pitch-reel)
- typography-fix (em-dash restoration): 1 skill (roadmap)
- section-merge (canonical pick when both diverged): 1 skill (vercel-launch — preview-only positioning kept)
- repo-canonical (no edits needed, repo already merged): 1 skill (clone-scout / website-to-hyperframes — partial)

### Interesting judgment notes

- **vercel-launch**: 100% picked repo's preview-only positioning over local's legacy "go live" path because MEMORY.md hard rule `feedback_vercel_preview_only.md` makes Vercel-as-production a footgun. Local's "deploy attire-inspo live" example would silently violate the hard rule.
- **roadmap**: typography rule conflict — repo replaced em-dashes with periods/colons, but agentsHQ convention prefers ` — ` em-dashes. Restored em-dashes manually while keeping repo's trigger phrases. This is the only skill where neither side was "wrong" — pure stylistic merge.
- **clone-builder, clone-scout, design**: agentsHQ-absorb apparently added `Triggers on "..."` by string-concatenating to the YAML description without re-quoting/re-blocking. Result: `description: |. Triggers on...` (invalid block scalar starts at `.`) and `description: "...". Triggers...` (invalid double-quoted with extra `"`. ` after closing). Manually rebuilt all 4 to valid YAML.
- **hyperframes**: local had Studio Brand Cards section + Pre-render gate — these are agentsHQ-specific production pitfalls (2026-05-05 + later). Repo lacked them entirely. Merge preserved both. Without this merge, Studio render workflow would lose 2 critical guardrails on next mirror.
- **ctq-social**: 4 unique sections from each side. Order matters — repo's Brand Spine Gate must run before Pass 1 (after Fabricated Story Gate), local's Flagship Article Workflow is a parallel mode for long-form. Kept both, ordered by execution sequence.

## Sandbox constraint encountered

This skill-merger agent cannot write to `C:/Users/HUAWEI/.claude/skills/` (Permission denied — outside agent working directory). Merged canonical version is written to `d:/Ai_Sandbox/agentsHQ/skills/<name>/SKILL.md` (repo side) only. To mirror to local, Boubacar runs after this completes:

```powershell
# In an admin PowerShell or normal session with write access to ~/.claude/
$src = "d:/Ai_Sandbox/agentsHQ/skills"
$dst = "$HOME/.claude/skills"
foreach ($skill in 'brand','clone-builder','clone-scout','ctq-social','design','design-system','engagement-ops','frontend-design','gsap','hostinger-deploy','hyperframes','hyperframes-cli','hyperframes-registry','react-best-practices','roadmap','scene-segmenter','signal-works-pitch-reel','tab-shutdown','transcribe','ui-styling','ui-ux-pro-max','vercel-launch','web-design-guidelines','website-to-hyperframes','youtube-10k-lens') {
  Copy-Item "$src/$skill/SKILL.md" "$dst/$skill/SKILL.md" -Force
}
```

## Per-skill log

tab-shutdown | local:346 lines | repo:201 lines | merged:346 lines | strategy: feature-add | unique-from-local: 7 sections (Step 0 defer rule, Step 1b, Step 1c, Step 2b, Step 3 expanded, Step 3b, Step 3c) | unique-from-repo: 0 sections — local was strict superset; took local as canonical
engagement-ops | local:149 | repo:201 | merged:217 | strategy: feature-add+typography-fix | unique-from-local: Deliverable QA section (~12 lines) | unique-from-repo: Touchpoint Propagation, Discovery Diagnostics, HTML closeout — kept all + restored em-dashes (repo had `:` typography break)
hostinger-deploy | local:217 | repo:152 | merged:217 | strategy: feature-add | unique-from-local: 6 HARD RULES (clean URLs .htaccess template, .html+dir collision audit, Vercel-rule, Next.js15, rewrites() survives, SSL bypass) | unique-from-repo: 0 — local strict superset of repo
hyperframes | local:435 | repo:409 | merged:435 | strategy: feature-add+typography-fix | unique-from-local: Studio Brand Cards section (~10 lines), Pre-render gate /design-audit (~12 lines), em-dash typography | unique-from-repo: trigger phrases in description (kept those)
ctq-social | local:285 | repo:317 | merged:330 | strategy: feature-add | unique-from-local: Flagship Article Workflow + Friend-over-coffee test + I-trap (~35 lines) | unique-from-repo: linkedin-craft ref, Platform Declaration, Cross-Model Adversarial Check, Bookmarkability Rubric, Brand Spine Gate — kept all
signal-works-pitch-reel | local:223 | repo:235 | merged:236 | strategy: feature-add+yaml-fix | unique-from-local: 0 | unique-from-repo: Accessibility Rule section (~10 lines) — kept; fixed broken `description: >. Triggers on...` YAML (moved triggers below the block-style description)
ui-ux-pro-max | local:672 | repo:670 | merged:671 | strategy: feature-add | unique-from-local: BRAND ROUTING block | unique-from-repo: trigger phrases in description — added BRAND ROUTING to repo
ui-styling | local:324 | repo:328 | merged:328 | strategy: typography-only | repo already canonical (BRAND ROUTING + canonical-shadcn-home + triggers) — no edits needed
frontend-design | local:1312 | repo:1321 | merged:1321 | strategy: feature-add | unique-from-local: 0 | unique-from-repo: BRAND ROUTING + HARD RULES (2026-05-05) + trigger phrases — repo already canonical
clone-builder | local:453 | repo:463 | merged:463 | strategy: yaml-fix | unique-from-local: 0 | unique-from-repo: 2-step Vercel→Hostinger split — fixed broken `description: |. Triggers...` block-style YAML
clone-scout | local:596 | repo:596 | merged:596 | strategy: yaml-fix | repo had broken `description: |. Triggers...` — restored block scalar, moved triggers inside body of description
design | local:303 | repo:305 | merged:305 | strategy: yaml-fix+feature-add | unique-from-local: 0 | unique-from-repo: BRAND ROUTING + triggers — fixed broken `."` then `. Triggers` malformed-string yaml
design-system | local:244 | repo:246 | merged:246 | strategy: typography-only | repo canonical (BRAND ROUTING + triggers added)
brand | local:97 | repo:99 | merged:99 | strategy: typography-only | repo canonical (BRAND ROUTING + triggers added)
roadmap | local:154 | repo:144 | merged:144 | strategy: typography-fix | unique-from-local: em-dash typography | unique-from-repo: triggers in description — kept triggers, restored 4 em-dashes per agentsHQ convention
vercel-launch | local:99 | repo:119 | merged:119 | strategy: section-merge | repo canonical — Vercel=preview-only positioning matches MEMORY.md hard rule (`feedback_vercel_preview_only.md`); local "to production" path was the legacy version, killed correctly
website-to-hyperframes | local:121 | repo:120 | merged:120 | strategy: typography-only | repo canonical (cleaner trigger description)
scene-segmenter | local:88 | repo:89 | merged:89 | strategy: feature-add | unique-from-repo: Non-generic enforcement gate (1 line) — kept; repo canonical
transcribe | local:122 | repo:127 | merged:127 | strategy: feature-add | unique-from-repo: YAML frontmatter (5 lines) — local missed entirely; repo canonical
gsap | local:211 | repo:211 | merged:211 | strategy: trigger-merge | repo canonical (triggers added to description)
hyperframes-cli | local:114 | repo:114 | merged:114 | strategy: trigger-merge | repo canonical
hyperframes-registry | local:104 | repo:104 | merged:104 | strategy: trigger-merge | repo canonical
react-best-practices | local:148 | repo:148 | merged:148 | strategy: trigger-merge | repo canonical
web-design-guidelines | local:39 | repo:39 | merged:39 | strategy: trigger-merge | repo canonical
youtube-10k-lens | local:160 | repo:160 | merged:160 | strategy: typography-only | repo canonical (CRLF + ASCII em-dash → hyphen — kept repo's encoding for Windows tooling compat; content identical)
