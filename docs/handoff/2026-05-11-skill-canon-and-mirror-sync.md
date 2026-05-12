# Session Handoff — Skill Canon + Local↔Repo Mirror Sync — 2026-05-11

## TL;DR

Rebuilt `boubacar-skill-creator/SKILL.md` as the authoritative architecture spec (374 lines, merges every prior source). Audited all 81 local + 75 repo skills — found 27 SKILL.md drifts, 4 silently-broken YAML descriptions, 6 ckm-namespaced skills, 8 universal skills missing from VPS (incl. `rca`), 2 structural gaps (`ui-ux-pro-max` + `frontend-design`), 3 placeholders w/ real nested content. Merged everything (never replaced, never deleted), mirrored local↔repo, fixed cascading references (routing-eval.jsonl, slash-commands, inventory, SKILLS_INDEX), fixed `.gitignore` rule that silently blocked `ui-ux-pro-max/data/` from shipping. Local + GitHub + VPS all synced at `f8e37c7`. Also: HyperFrames absorb (heygen-com/hyperframes-launch-video PROCEED — 2 patterns added to skills/hyperframes/patterns.md).

## What was built / changed

**Canonical spec (the load-bearing artifact):**
- `skills/boubacar-skill-creator/SKILL.md` — rebuilt 374 lines. Merges 2026-05-10 anthropic absorb (allowed-tools, compatibility, progressive disclosure 3-level, run_loop.py optimizer), 2026-05-10 skill-gate fix (routing-eval.jsonl), 2026-05-02 Folder Governance, prior LOCAL + REPO content. Added: Atomic Section Contract (5-section table), check_resolvable, gbrain conformance 11-item, routing-eval.jsonl Step 4.7, local↔repo mirror procedure Step 8c, Architecture Compliance 6-criterion audit (used by absorb Phase 2.5).

**27 SKILL.md drifts merged (preserved both sides' unique content):**
brand, clone-builder, clone-scout, ctq-social, design-system, design, engagement-ops, frontend-design, gsap, hostinger-deploy, hyperframes-cli, hyperframes-registry, hyperframes, karpathy, react-best-practices, roadmap, sankofa, scene-segmenter, signal-works-pitch-reel, tab-shutdown, transcribe, ui-styling, ui-ux-pro-max, vercel-launch, web-design-guidelines, website-to-hyperframes, youtube-10k-lens. 50 pre-merge files archived at `zzzArchive/skills-pre-merge-20260511/`.

**4 silently-broken YAML descriptions fixed:** clone-builder, clone-scout, design, signal-works-pitch-reel — invalid block scalars from prior auto-trigger-rewrite passes.

**6 ckm-namespaced skills renamed to match folder:** banner-design, slides, brand, design, design-system, ui-styling. Cascading fixes:
- 4 `routing-eval.jsonl` `expected:` fields (would have failed every eval)
- 4 slash-command refs in design body + references (`/ckm:NAME` → `/NAME`)
- `docs/agentsHQ_inventory.json` regenerated
- `docs/SKILLS_INDEX.md` regenerated

**Batch 1 (8 universal LOCAL-ONLY mirrored to repo):** banner-design, cold-outreach, deploy-to-vercel, design-audit, **rca** (urgent miss — referenced in CLAUDE.md but absent from VPS), slides, vercel-cli-with-tokens, webapp-testing.

**Batch 2 (structural gaps filled):**
- frontend-design: 9 → 21 files (added reference/ + templates/)
- ui-ux-pro-max: 2 → 36 files (added scripts/ + data/ — required `.gitignore` allowlist fix)

**3 placeholder rewrites (archive-then-rewrite-as-index):** active, library, CatalystWorksSkills — originals archived to `zzzArchive/skills-pre-merge-20260511/<name>.SKILL.md.placeholder`, rewritten as proper INDEX skills with full canonical structure pointing to real nested content (cole-templates, sheet-mint, agent-teams, etc.).

**`.gitignore` fix:** Added `!skills/ui-ux-pro-max/data/` allowlist after bare `data/` rule (line 128) — was silently blocking 33 CSV reference files.

**HyperFrames absorb (heygen-com/hyperframes-launch-video) PROCEED:**
- `skills/hyperframes/patterns.md` (179 lines) — added timeline-padding pattern (no-op tween prevents black-frame flashes when sub-comp GSAP timeline < master slot duration) + caption-track pattern (body-level `.cap clip` divs w/ unique high track indices 20+, z-index 9999, backdrop-blur card)

**Audit artifacts:**
- `docs/audits/2026-05-11-skill-mirror-audit.md` — 357-line full audit report (Phase 1 inventory, Phase 2 hidden agents, Phase 2.5 architecture compliance w/ Karpathy + Sankofa, Phase 3 sync punch list)
- `docs/audits/2026-05-11-skill-merge-log.md` — per-skill merge log + summary
- `docs/audits/REGISTRY.md` — entry for skill mirror audit

## Decisions made

- **Sankofa drift = MERGE not pick-a-side.** Kept LOCAL's COUNCIL ESCALATION CHECK + REPO's DEAD-PROJECT MODE + LOCAL's POST-RUN COUNCIL FLAG (128 lines).
- **Karpathy drift = repo wins** (LOCAL was strict subset — typography only + missing triggers; no unique data lost).
- **Placeholders never deleted** — archive then rewrite as proper INDEX. Boubacar's standing rule: never delete, always archive.
- **Folder Governance (every folder = AGENTS.md or README.md)** is the rule from 2026-05-02 cleanup, not a "use folders instead of subagents" rule. The newer convention is progressive disclosure (refs in `references/`, not subagent dispatch for everything).
- **`superpowers/` and `community/` left untouched** — full plugin clones / submodules, not authored content.
- **Routing-eval files MUST be updated when YAML name changes.** Without this, `expected:` field stale and every eval row fails.

## What is NOT done (explicit)

- **MEMORY.md is at 216 lines** (cap = 200). Was 214 at session start before my 2 new entries. Pre-existing condition; pruning deferred — needs Boubacar's call on which `project_*` pointers to move to `MEMORY_ARCHIVE.md`.
- **6 pre-existing top-level repo folders** still missing AGENTS.md (`_avast_`, `assets`, `dAi_SandboxagentsHQdocspatterns`, `loops`, `Python`, `reports`). Surfaced by `scripts/check_folder_purpose.py` but out of session scope.
- **`skills/community/`** is a git submodule — couldn't add SKILL.md from main repo. Submodule maintainer's call.
- **`backup-fix-gate-poll` branch** created at session end to preserve unrelated `gate_poll.py` dedup-sentinel work + `8ee1aa4` handoff doc commit. Not pushed. Other session's work, not mine to merge.
- **`scripts/gate_poll.py` modification on backup branch** — dedup-sentinel feature, not yet validated. Different session's purpose.

## Open questions

- Is `8ee1aa4 docs(handoff): 2026-05-11 PGA absorb + memory-enforcement session` ready to merge to main, or still WIP on its branch? It's on origin/main per VPS pull — confirm if Boubacar wants it explicitly in main or in branch only.
- `MEMORY.md` prune: which `project_*` entries to move to archive?
- Should `skills/community/SKILL.md` get an index file via the submodule maintainer flow, or stay un-indexed?

## Next session must start here

1. **Verify VPS skill state.** SSH `root@72.60.209.109` and run: `cd /root/agentsHQ && git log --oneline -5 && grep -rE 'ckm:' skills/ | head` — should show 0 ckm refs and tip at `f8e37c7` or later.
2. **Test rca skill from VPS.** Trigger `/rca` in a CrewAI agent context; verify the SKILL.md loads cleanly (now exists at `/root/agentsHQ/skills/rca/SKILL.md`).
3. **Test ui-ux-pro-max data access.** From VPS: `ls /root/agentsHQ/skills/ui-ux-pro-max/data/` — should show 33 CSV files. If 0, the `.gitignore` allowlist didn't ship.
4. **MEMORY.md prune** (ask Boubacar): currently 216 lines, cap 200. Pick 2-3 `project_*` pointers to move to `MEMORY_ARCHIVE.md`.
5. **Clean up `backup-fix-gate-poll` branch**: confirm whether to merge gate_poll dedup-sentinel work to main, push as feature branch with [READY], or keep parked.
6. **Followup verifications due by 2026-05-25:** Cole templates G3 + G4, Ghost Works G5 (1 booked call), G6 decision gate. Per `docs/reviews/absorb-followups.md`.

## Files changed this session

```
# Skill canon
skills/boubacar-skill-creator/SKILL.md (rebuilt, 374 lines)

# 27 SKILL.md merged (both sides preserved)
skills/{brand,clone-builder,clone-scout,ctq-social,design-system,design,
engagement-ops,frontend-design,gsap,hostinger-deploy,hyperframes-cli,
hyperframes-registry,hyperframes,karpathy,react-best-practices,roadmap,
sankofa,scene-segmenter,signal-works-pitch-reel,tab-shutdown,transcribe,
ui-styling,ui-ux-pro-max,vercel-launch,web-design-guidelines,
website-to-hyperframes,youtube-10k-lens}/SKILL.md

# 8 LOCAL-ONLY → repo
skills/banner-design/ (NEW in repo)
skills/cold-outreach/ (NEW in repo)
skills/deploy-to-vercel/ (NEW in repo)
skills/design-audit/ (NEW in repo)
skills/rca/ (NEW in repo — urgent)
skills/slides/ (NEW in repo)
skills/vercel-cli-with-tokens/ (NEW in repo)
skills/webapp-testing/ (NEW in repo)

# Gap fills
skills/frontend-design/{reference/*,templates/*} (12 + 2 files)
skills/ui-ux-pro-max/{scripts/*.py,data/*.csv,data/stacks/*.csv} (34 files)

# Placeholder rewrites
skills/active/SKILL.md (rewritten as INDEX)
skills/library/SKILL.md (rewritten as INDEX)
skills/CatalystWorksSkills/SKILL.md (rewritten as INDEX)
skills/community/SKILL.md (NEW — index for submodule mirror)

# Routing eval fixes (cascading rename)
skills/{brand,design,design-system,ui-styling}/routing-eval.jsonl

# Cold-outreach YAML fix
skills/cold-outreach/SKILL.md (added YAML frontmatter)
skills/cold-outreach/cold-outreach/SKILL.md (legacy nested duplicate, marked)

# Slash-command fixes
skills/design/SKILL.md (line 231 — /ckm: → /)
skills/design/references/social-photos-design.md (lines 60-62)

# HyperFrames absorb
skills/hyperframes/patterns.md (179 lines, added timeline-pad + caption-track patterns)

# .gitignore fix
.gitignore (added !skills/ui-ux-pro-max/data/ allowlist after line 128)

# Auto-regenerated docs
docs/agentsHQ_inventory.json (regen via inventory_snapshot.py)
docs/agentsHQ_inventory.md (regen)
docs/SKILLS_INDEX.md (regen via lint_and_index_skills.py)

# Audit + registry artifacts
docs/audits/2026-05-11-skill-mirror-audit.md (NEW, 357 lines)
docs/audits/2026-05-11-skill-merge-log.md (NEW, per-skill log)
docs/audits/REGISTRY.md (audit entry)
docs/reviews/absorb-log.md (HyperFrames + canon entries)
docs/reviews/absorb-followups.md (HyperFrames + canon DONE entries)
docs/roadmap/harvest.md (H1i warm-referrals task added)

# Memory entries (next-session inheritance)
~/.claude/projects/d--Ai-Sandbox-agentsHQ/memory/feedback_skill_canon_and_mirror.md (NEW)
~/.claude/projects/d--Ai-Sandbox-agentsHQ/memory/feedback_gitignore_data_blocks_skill_data.md (NEW)
~/.claude/projects/d--Ai-Sandbox-agentsHQ/memory/MEMORY.md (2 pointer entries added)

# Pre-merge backups (gitignored, local safety net)
zzzArchive/skills-pre-merge-20260511/*.{local,repo}.SKILL.md (50 files)
zzzArchive/skills-pre-merge-20260511/{active,library,CatalystWorksSkills}.SKILL.md.placeholder
```

## Commits this session (tip = f8e37c7)

```
f8e37c7 docs(audit+harvest): log skill-mirror audit + H1i warm-referrals task
eb1d448 fix(skills): strip ckm: prefix from 4 routing-eval.jsonl expected fields
9af0994 fix(skills): replace stale /ckm: + /ck: slash-command refs in design skill body
79ee56d fix(skills): rename 4 ckm-namespaced skills to match folder + regen inventory
a3d1913 feat(memory): 3-layer enforcement fix + GW absorb (ghost roadmap)
7a23df4 fix(skills): allowlist skills/ui-ux-pro-max/data/ in .gitignore
0351d45 feat(skills): canonicalize SKILL.md spec + merge 27 drifted skills + mirror 8 LOCAL-ONLY
9d64c4a feat(hyperframes): add patterns.md to repo skill mirror
0aea5f7 docs(absorb): heygen-com/hyperframes-launch-video PROCEED
```
