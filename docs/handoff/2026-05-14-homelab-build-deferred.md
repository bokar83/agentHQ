# Session Handoff — Local AI Workstation Build Planning + Deferred — 2026-05-14

## TL;DR

Researched a complete RTX 3090 + Ryzen 7900X local AI workstation build spec (planning artifact, not a buy). Ran Sankofa Council and got a 3-way architecture split. User chose to defer the build 6+ months for personal-sovereignty reasons (not client-driven). Saved project + reference memory entries, created `homelab` roadmap, gate auto-merged. Cloud bridge approved as interim path. No hardware purchased.

## What was built / changed

Memory files (outside canonical tree, no commit needed):
- NEW: `~/.claude/projects/d--Ai-Sandbox-agentsHQ/memory/project_homelab_build_deferred.md`
- NEW: `~/.claude/projects/d--Ai-Sandbox-agentsHQ/memory/reference_local_ai_build_spec_2026-05-14.md`
- EDITED: `~/.claude/projects/d--Ai-Sandbox-agentsHQ/memory/MEMORY_ARCHIVE.md` (added project pointer under Project Entries, per routing rule — project_ entries go to MEMORY_ARCHIVE, NOT MEMORY.md)

Roadmap files (canonical tree, pushed via worktree, gate auto-merged):
- NEW: `docs/roadmap/homelab.md` — deferred status, parked until 2026-11-14+, Council verdict captured, trigger gates G1-G6 documented
- EDITED: `docs/roadmap/README.md` — codename registry row `homelab` added between harvest + lighthouse
- Commit: `c3d3da9e` on `feat/roadmap-homelab`
- Gate merge: `c41e2925` on main

Handoff file (this doc):
- NEW: `docs/handoff/2026-05-14-homelab-build-deferred.md` (via worktree `D:/tmp/wt-homelab-handoff`)

## Decisions made

1. **Defer build 6+ months minimum.** Boubacar 2026-05-14: "It's not a question of if but when. I want my own build eventually to have more control and to be able to do more testing and other things and not be at the mercy of the big organizations." Earliest reopen: 2026-11-14.

2. **Personal sovereignty, NOT client-driven.** This is personal-infrastructure capex, not revenue-tied. Do not pressure-test as a business decision when it reopens.

3. **Cloud bridge approved as INTERIM only, not destination.** Hostinger VPS for orchestration + OpenRouter for API work + RunPod Secure on-demand for occasional heavy jobs. User explicitly rejected cloud-only as permanent posture.

4. **6 hard triggers + 3 soft signals documented.** Build reopens only when time-gate (≥2026-11-14) AND one of: $5K MRR sustained, 100hr/mo inference logged, $200/mo cloud-GPU spend sustained, used 5090 < $1K, dual-3090 NVLink < $1.5K, or open-MoE under 50GB becomes daily-driver.

5. **Council 3-way split preserved, not resolved.** Spend-more (dual-3090 + collapsed NAS, $3,200), spend-less (Mac Mini + cloud rental, $2,500), spend-nothing-validate-first. Re-resolve at trigger time with then-current data, NOT now.

6. **No worktree mass-cleanup.** Audited 18 stale worktrees in D:/tmp/. Only 1 clean (`wt-nate-audit`). 17 others have dirty WIP or unpushed commits. User said "hold for now." Other sessions should shut themselves down via their own /tab-shutdown.

## What is NOT done (explicit)

- **Postgres memory write FAILED.** `memory_store.write` could not resolve hostname `agentshq-postgres-1` from laptop. All 6 writes returned non-fatal but did not persist to VPS Postgres. Per MEMORY.md line 33 the correct container hostname is `orc-postgres` not `agentshq-postgres-1`. Bug exists in `orchestrator/memory_store.py`. Out of scope this session. Flat-file memory (Step 2) is the fallback and has all the data.

- **Worktree cleanup deferred.** 18 stale worktrees in D:/tmp/, including the one created this session (`wt-homelab-handoff`, `wt-homelab-roadmap` already removed). User explicitly said hold. Not for this session to resolve.

- **No live deploy / VPS verify.** Roadmap docs are not runtime. No code shipped. Skip VPS pull.

- **No `/nsync` run.** Session-start audit flagged 1 PNG at repo root + 64 stale handoff docs. Out of scope this session.

## Open questions

- The `memory_store.py` Postgres hostname bug (`agentshq-postgres-1` vs `orc-postgres`) keeps causing silent failures. Worth a future RCA but not blocking.

- 17 stale worktrees in D:/tmp/ represent in-flight work from concurrent Claude sessions. No coordination mechanism currently exists to know if those sessions are alive. Future enhancement.

## Files changed this session

```
# Memory (outside canonical tree)
~/.claude/projects/d--Ai-Sandbox-agentsHQ/memory/project_homelab_build_deferred.md       NEW
~/.claude/projects/d--Ai-Sandbox-agentsHQ/memory/reference_local_ai_build_spec_2026-05-14.md  NEW
~/.claude/projects/d--Ai-Sandbox-agentsHQ/memory/MEMORY_ARCHIVE.md                       EDITED

# Canonical repo (via worktrees, pushed, gate-merged)
docs/roadmap/homelab.md      NEW       commit c3d3da9e / merge c41e2925
docs/roadmap/README.md       EDITED    same commit
docs/handoff/2026-05-14-homelab-build-deferred.md  NEW (this file, pending push)
```

## Postgres memory lessons (attempted; failed silently due to hostname bug)

Lessons captured this session, intended for VPS Postgres `memory` table:

1. **Sankofa Council 3-way splits are valid output.** Don't force convergence at decision time. Preserve all verdicts as session log for re-resolve at trigger time with then-current data.

2. **Never mass-clean worktrees.** Audit ahead/behind/dirty/pushed per worktree before any destructive action. Dirty files = assets per never-delete rule. Let originating sessions shut themselves down via tab-shutdown.

3. **Used GPU pricing: budget against wider band.** Sources disagree 30%+ (eBay tracker median vs r/hardwareswap floor). Include eBay sold + r/hardwareswap + local classifieds (KSL for Utah).

4. **Deferred-but-tracked pattern works.** Time-gate AND multi-condition trigger gates AND reopen protocol prevent losing project intent across long pauses. project_ memory routes to MEMORY_ARCHIVE.md per routing rule, NOT MEMORY.md.
