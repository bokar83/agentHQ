# Session Handoff - Blotato RCA + M20 Roadmap - 2026-05-08

## TL;DR
Full RCA on 100% studio publish failure rate (YouTube/TikTok/Instagram). Root cause: Drive webViewLink passed to Blotato — files private + wrong URL format. Fixed with ensure_public + usercontent URL conversion. TikTok also needed CFR video fix. Backlog of 8 failed records staggered May 8-11. M20 (native social publisher to replace Blotato) added to atlas roadmap with full platform API research.

## What was built / changed
- `orchestrator/studio_blotato_publisher.py` — `_drive_file_id()`, `_to_direct_download_url()` helpers; `ensure_public()` + URL conversion before every `publish()` call (commits 7a03dd1)
- `orchestrator/drive_publish.py` — `audit_studio_pipeline_videos()` function + `audit-videos` CLI subcommand (commit 7a03dd1)
- `orchestrator/studio_render_publisher.py` — `-r {fps} -vsync cfr` added to `_concat_clips` ffmpeg command to fix TikTok VFR rejection (commit 31a1fe6)
- `docs/roadmap/atlas.md` — M20 added (commit 96e51b1) + updated with research findings (commit 8d757a5)
- `docs/handoff/2026-05-08-studio-blotato-rca.md` — RCA incident doc
- `~/.claude/skills/rca/SKILL.md` — Blotato publisher added to Phase 0 triage table + Known Pitfalls section added

## Decisions made
- **Keep Blotato** for now — all-or-nothing replacement strategy (no split routing)
- **M20 = monitor**, revisit in a few weeks after more Blotato usage data
- **M20 full replacement only feasible for YouTube + Instagram** natively; X/TikTok/LinkedIn stay on Blotato due to API cost/approval blockers
- **Backlog warming protocol**: 2 posts/day max during account warm-up; stagger across multiple days
- **audit-videos** must be run after any bulk Pipeline DB import

## What is NOT done (explicit)
- TikTok CFR fix not validated — applies to new renders only; existing VFR renders already in pipeline will still fail TikTok until new renders produced
- M20 build not started — research-gated, revisit in 2-3 weeks
- Instagram Business account switch (for future M20) — manual, Boubacar must do in Instagram app
- 10 handoff docs >3 days old in `docs/handoff/` root — need archiving (session audit warned)
- ENTRYPOINT FIX (`scripts/docker-entrypoint.sh`) shipped but rebuild not yet run — `docker cp` ritual still required until next `orc_rebuild.sh` run

## Open questions
- TikTok: will CFR fix resolve the "Unsupported frame rate" error on next render cycle? Validate May 9 tick.
- 1stGen IG (account 45755 = `1stgenmoneyz`): Boubacar confirmed Meta issue resolved. Validate on May 9 tick.
- May 6 Instagram failures ("not a confirmed user") — Boubacar reposted manually. Monitor if it recurs.

## Next session must start here
1. Check May 9 publisher tick results: `ssh root@72.60.209.109 "docker logs orc-crewai 2>&1 | grep -E 'BLOTATO poll|STUDIO PUBLISHER.*tick done' | tail -20"` — confirm TikTok CFR fix worked + 1stGen IG published
2. Archive old handoff docs: move everything >3 days old from `docs/handoff/` to `docs/handoff/archive/`
3. When ready for M20 spike: switch 3 studio IG channels to Business accounts (Boubacar action), then start Meta app review for `instagram_business_content_publish`

## Files changed this session
- `orchestrator/studio_blotato_publisher.py`
- `orchestrator/drive_publish.py`
- `orchestrator/studio_render_publisher.py`
- `docs/roadmap/atlas.md`
- `docs/handoff/2026-05-08-studio-blotato-rca.md`
- `~/.claude/skills/rca/SKILL.md`
- `~/.claude/projects/d--Ai-Sandbox-agentsHQ/memory/feedback_studio_blotato_drive_url.md`
- `~/.claude/projects/d--Ai-Sandbox-agentsHQ/memory/MEMORY.md`
