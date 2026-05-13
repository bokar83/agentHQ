# Session Handoff — Atlas Recovery + Lighthouse Polish + nsync — 2026-05-13

## TL;DR
Boubacar reported the Atlas Mission Control dashboard at https://agentshq.boubacarbarry.com/atlas was broken after a quick aesthetic fix: nav bar gone, data not loading, frames raw, routes bouncing to login, Lighthouse inaccessible. RCA traced root cause to three compounding incidents on 2026-05-12: M8 commit (155ee4a) gutted 2243 lines of pre-M8 rich UI shell; pin-fix branch (810b4aa) was branched off pre-Lighthouse base and FF-merged into main, silently dropping the Lighthouse nav block; Lighthouse infrastructure (atlas-lighthouse.html, lighthouse.md) was stranded on fix/constraints-capture-agentshq-route, never merged to main. Recovery branch restored the pre-M8 rich shell (1064 CSS, 999 JS, 180 HTML), merged stranded Lighthouse infra, added unified 4-link nav (Dashboard / Spend / Roadmap / Lighthouse) across atlas.html / cost.html / roadmap.html / atlas-lighthouse.html, removed sub-page PIN gates (single PIN at /atlas only, sub-pages authGuard redirect), made A-J sections collapsible via native HTML5 details/summary. Polish round 2 dropped the L brand-mark + DRAFT badges, made the topbar sticky-floating like other pages, reordered nav so Lighthouse is always rightmost. /nsync swept canonical + GitHub + VPS into alignment at b5f8e9b.

## What was built / changed
- `thepopebot/chat-ui/atlas.html` — restored to pre-M8 rich shell (180 lines) + Lighthouse nav link + reordered to Dashboard/Spend/Roadmap/Lighthouse
- `thepopebot/chat-ui/atlas.css` — restored to pre-M8 1064 lines + appended M8-style var compat shim (`--c1` → `--terracotta`, `--bone` → `--ink`, etc.) so atlas-lighthouse.html renders against rich CSS without rewrite
- `thepopebot/chat-ui/atlas.js` — restored to pre-M8 999 lines (full card rendering, polling, CRM board, native chat panel)
- `thepopebot/chat-ui/atlas-lighthouse.html` — extracted from stranded `680371a` + polish round 2: removed "L" brand-mark, removed "DRAFT" badges (topbar + footer), converted to sticky `#topbar` layout matching atlas.html, nav reorder, removed standalone PIN gate, added authGuard redirect, converted 10 `lh-section` blocks to native `<details>`/`<summary>` with rotating chevron
- `thepopebot/chat-ui/cost.html` — added Lighthouse nav link, reordered to Dashboard/Spend/Roadmap/Lighthouse, removed standalone PIN gate, added authGuard redirect
- `thepopebot/chat-ui/roadmap.html` — added Lighthouse nav link, reordered to Dashboard/Spend/Roadmap/Lighthouse, added authGuard redirect
- `thepopebot/chat-ui/nginx.conf` — added `location = /atlas/lighthouse` block routing to `atlas-lighthouse.html` with no-cache headers
- `docs/roadmap/lighthouse.md` — extracted from stranded `dc745c0` (183 lines), now on main
- `docs/roadmap/atlas.md` — appended 2026-05-12-late session log entry: M8 rollback + M8.1 scoped (additive Action Stream card, ~150 LOC, target 2026-05-15)
- `.gitignore` — added `/atlas-*.png` `/lighthouse-*.png` patterns for Playwright browser-test artifacts
- `skills/outreach/SKILL.md` — picked up prior session uncommitted note about `AUTO_SEND_CONSTRAINTS_AI` env var + 3-touch constraints_ai pipeline
- `skills/constraints_ai_capture/SKILL.md` — NEW file. Module dir had no SKILL.md so pre-commit lint blocked all commits in that tree. Agent-internal frontmatter matching `skills/outreach/` pattern
- `docs/SKILLS_INDEX.md` — routing entry for `constraints_ai_capture` so `check_routing_gaps.py` passes
- `output/` submodule pointer — bumped to `feat/catalystworks-hyperframes` tip `414489d` (today's catalystworks-site `/api/orc` Traefik prefix capture endpoint fix preserved)
- `skills/nsync/SKILL.md` — added Step 6 guidance for `git submodule sync --recursive` on VPS before submodule update; documented the 2026-05-13 stale-URL incident
- 6 new memory files: `feedback_surgical_branch_rebase_before_merge.md`, `feedback_atlas_subpages_no_pin_redirect.md`, `feedback_atlas_nav_order_lighthouse_last.md`, `feedback_no_draft_or_letter_brand_marks.md`, `feedback_chat_ui_container_bind_mount_restart.md`, `feedback_vps_submodule_url_sync_after_gitmodules_change.md` (pointers added to MEMORY.md)

## Decisions made
- M8 UI rewrite REVERTED. Server-side endpoints (`/atlas/feed` SSE + `/atlas/intent/{id}/{approve|reject}`) survive in `orchestrator/app.py` lines 1280-1318. UI consumer was bad value/risk and was the source of the regression.
- M8.1 scoped as additive 9th card on the rich pre-M8 shell. Strictly additive — no shell rewrite. ~150 LOC. Subscribes to `/atlas/feed`, renders intent cards with approve/reject buttons. Target 2026-05-15.
- Atlas sub-pages NEVER show their own PIN gate (Boubacar rule 2026-05-13). Single PIN at `/atlas` only. Sub-pages run `authGuard()` that redirects to `/atlas` if `atlas_token` missing.
- Atlas top nav order locked: Dashboard / Spend / Roadmap / Lighthouse. Lighthouse always rightmost on all pages. Active page = `var(--terracotta)` inline color. If a 5th section is added, it goes between Roadmap and Lighthouse, NOT after.
- Production pages do not carry "DRAFT" badges. Once shipped, it is the operating plan, not a draft. Exception: literal drafts of emails / PRs / design v0.x.
- No single-letter brand-mark placeholder blocks ("L" next to "Lighthouse"). Use the real `compass.svg` logo or no icon.
- `/nsync` skill upgraded: now includes `git submodule sync --recursive` on VPS before `git submodule update` because `.gitmodules` URL change does NOT auto-propagate to existing submodule `.git/config`.

## What is NOT done (explicit)
- M8.1 (additive Action Stream card) NOT built this session. Scoped + logged on atlas.md roadmap. Server endpoints alive but headless.
- VPS Postgres memory write FAILED this session. Host name `agentshq-postgres-1` is the docker network name — not DNS-resolvable from laptop. Flat-file memory (Step 2) covered the 6 lessons + skill update. If second-brain queries need this session in the memory table, run the write from VPS side (or from a container with docker network access) using the same `AgentLesson`/`ProjectState`/`SessionLog` snippet from the tab-shutdown skill.
- Nested submodule `output/apps/attire-inspo-app-fresh` lacks `.gitmodules` entry. Warning shown by `git submodule update --recursive`. Not my scope this session — separate work by other agents. Does not block sync.
- Old worktrees still on disk: `D:/tmp/wt-pid-24488` (atlas-recovery, merged), `D:/tmp/wt-pid-atlas2` (lighthouse-polish, merged). Both branches deleted on remote. Can be `git worktree remove` next session.
- `skills/nsync/SKILL.md` update is uncommitted on canonical (M). Will commit + push at end of this skill close.

## Open questions
None. All five Boubacar requirements verified live on https://agentshq.boubacarbarry.com/atlas:
1. Aesthetic enhancements included ✅
2. Lighthouse included ✅
3. Navigation bar at top ✅ (Dashboard / Spend / Roadmap / Lighthouse)
4. Works (data loads, routes accessible) ✅
5. Login = `.env` `CHAT_UI_PIN`, no 6-char limit ✅

## Next session must start here
1. Verify Atlas dashboard prod still healthy: open https://agentshq.boubacarbarry.com/atlas in incognito (avoid local browser cache), enter env PIN, confirm 4-link nav + 8 cards + Lighthouse collapsible sections still render. Check console for new errors.
2. Decide whether to build M8.1 (additive Action Stream card on rich shell) next. Scope locked in `docs/roadmap/atlas.md` 2026-05-12-late entry. ~150 LOC, additive only, no shell rewrite. Target 2026-05-15.
3. If M8.1 not next: pick from Atlas roadmap default-next-moves: A9d-A Deep Memory Garden (target 2026-05-18), A3 Reconciliation Polling, A25 Event Bus.
4. Clean up stale worktrees: `git worktree remove D:/tmp/wt-pid-24488 && git worktree remove D:/tmp/wt-pid-atlas2 && git worktree prune` once safe.
5. Run Postgres memory write for this session from VPS or container side (see "What is NOT done" — 6 lessons + 1 project state + 1 session log are in flat memory + this handoff; second-brain DB does not have them yet).

## Files changed this session
- thepopebot/chat-ui/atlas.html
- thepopebot/chat-ui/atlas.css
- thepopebot/chat-ui/atlas.js
- thepopebot/chat-ui/atlas-lighthouse.html (new)
- thepopebot/chat-ui/cost.html
- thepopebot/chat-ui/roadmap.html
- thepopebot/chat-ui/nginx.conf
- docs/roadmap/lighthouse.md (new on main)
- docs/roadmap/atlas.md
- .gitignore
- skills/outreach/SKILL.md
- skills/constraints_ai_capture/SKILL.md (new)
- skills/nsync/SKILL.md
- docs/SKILLS_INDEX.md
- output/ submodule pointer → 414489d
- ~/.claude/projects/d--Ai-Sandbox-agentsHQ/memory/MEMORY.md (6 new pointers added)
- 6 new memory files (see Decisions section above)

## Commit chain to main
- `7a06ce7` — fix(atlas): restore rich pre-M8 shell + add Lighthouse + sub-page auth-guard [READY]
- `2d10388` — docs(atlas): log 2026-05-12 dashboard recovery + scope M8.1 Action Stream card [READY]
- `f2a8ba7` — merge(fix/atlas-recovery-nav-styling): gate auto-merge — tests green, no conflicts
- `f7900a4` — fix(atlas/lighthouse): polish — remove L mark + DRAFT, reorder nav, sticky topbar, collapsible sections [READY]
- `3b70d2e` — merge(fix/atlas-lighthouse-polish): gate auto-merge — tests green, no conflicts
- `b5f8e9b` — chore(nsync): cleanup pre-existing dirty state from prior sessions [READY]
