# Session Handoff - M19 Native CRM Board - 2026-05-10

## TL;DR

Built and deployed the M19 native CRM board from scratch. Two FastAPI endpoints (`GET /atlas/crm/board`, `POST /atlas/crm/leads/{id}/status`) + kanban card in the Atlas dashboard. Discovered `sent` status (293 leads) was missing from the original status list — fixed. VPS main had diverged 1552 commits from origin/main; resolved with `git pull --rebase` + selective file checkout hotdeploy. M19 is live at commit `150c229`.

## What was built / changed

- `orchestrator/atlas_dashboard.py` — added `get_crm_board()` + `set_lead_status()` at bottom of file. Uses `get_crm_connection_with_fallback()`. `_CRM_STATUSES = ["new", "sent", "messaged", "replied", "qualified", "proposal", "closed_won", "closed_lost"]`. Normalizes status casing on load.
- `orchestrator/app.py` — added `GET /atlas/crm/board` + `POST /atlas/crm/leads/{lead_id}/status` with `_CrmStatusBody` Pydantic model. Auth-gated via `verify_chat_token`.
- `thepopebot/chat-ui/atlas.html` — CRM Pipeline card added to `#cards-col` with `data-card="crm"` and `data-color="lapis"`.
- `thepopebot/chat-ui/atlas.js` — `renderCrmBoard()`, `buildCrmCard()`, `refreshCrm()`. Kanban with prev/next status transition buttons. Wired into `refreshAll()`.
- `thepopebot/chat-ui/atlas.css` — `.card-crm`, `.crm-col`, `.crm-col-header`, `.crm-card`, `.crm-status-btns` — dark-mode kanban, per-status accent colors, scroll-x.
- `docs/roadmap/atlas.md` — M19 flipped to ✅ SHIPPED, Session-Start Cheat Block updated.

## Decisions made

- **`sent` status must be in CRM_STATUSES** — 293 Supabase leads have `status='sent'` (email outreach sent). Original spec used `messaged` as the first outreach stage; prod data uses `sent`. Both kept.
- **Status casing normalized on read** — 6 leads had `New` (capital N); `.lower()` applied on board load.
- **No full Supabase merge on VPS** — VPS main diverged 1552 commits; used `git pull --rebase` + `git checkout origin/feat/atlas-m19-crm -- <files>` for targeted hotdeploy rather than full merge.
- **Gate READY tip-commit rule** — after pushing a fix commit on a `[READY]` branch, must push an empty re-signal commit or Gate won't detect it.

## What is NOT done

- `GET /atlas/crm/leads/<id>` — single-lead detail view (planned in M19 spec, deferred to M20)
- `POST /atlas/crm/leads/<id>/note` — free-text notes append (M20)
- Postgres memory lessons — `memory_store.write()` fails from outside the container due to import path mismatch. Container has baked stale `memory_store.py` (expects `orchestrator.memory_models` but `/app` has no `orchestrator/` prefix). Needs container rebuild or entrypoint fix to resolve.

## Open questions

- **Postgres memory write failure** — container `/app/memory_store.py` does `from orchestrator.memory_models import _MemoryBase` but `/app` has no `orchestrator` package. Entrypoint syncs `.py` files but this import is baked. Next session: `docker exec orc-crewai python3 -c "import memory_store; print(memory_store.__file__)"` and check if entrypoint actually overwriting stale file.
- **Gate 18-branch backlog** — many READY branches queued. Some auto-rejected for skill quality failures. Gate is functional but slow to drain.

## Next session must start here

1. Check M19 is visible in Atlas dashboard at agentshq.boubacarbarry.com/atlas (CRM Pipeline card should show 2592 leads in 8 lanes)
2. If Postgres memory write is broken: check `docker exec orc-crewai python3 -c "from memory_store import write; print('ok')"` — if fails, needs container rebuild
3. Start M24 Hermes Self-Healing — check any parallel session for brainstorm/spec. If none: start brainstorm with `/brainstorming` skill
4. Or M20 single-lead detail: `GET /atlas/crm/leads/<id>` + notes append in same session

## Files changed this session

```
orchestrator/atlas_dashboard.py   — get_crm_board() + set_lead_status() added
orchestrator/app.py               — /atlas/crm/board + /atlas/crm/leads/{id}/status
thepopebot/chat-ui/atlas.html     — CRM Pipeline card
thepopebot/chat-ui/atlas.js       — renderCrmBoard, buildCrmCard, refreshCrm
thepopebot/chat-ui/atlas.css      — kanban board styles
docs/roadmap/atlas.md             — M19 SHIPPED, cheat block updated
memory/project_atlas_m19_shipped_2026-05-10.md  — new
memory/feedback_gate_ready_tip_commit.md         — new
memory/feedback_vps_main_divergence.md           — new
memory/MEMORY.md                  — 2 new entries, pruned to 201 lines
memory/MEMORY_ARCHIVE.md          — M19 pointer added
```
