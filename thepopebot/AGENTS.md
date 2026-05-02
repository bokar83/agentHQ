---
owner: production
status: active / live-mount
---

# thepopebot/ - thepopebot Sidecar Subsystem

thepopebot event handler + chat UI. Live container mount, path-watched by GitHub Actions. **Never move this folder without coordinating GitHub Actions + docker-compose + VPS in a single window.**

## What lives here

| Subfolder | Purpose |
| --- | --- |
| `chat-ui/` | thepopebot web chat UI (path-watched by `.github/workflows/deploy-agentshq.yml:8`) |
| `skills/` | thepopebot-specific skills (separate from agentsHQ `skills/`) |

## Live mount references

| Reference | Location |
| --- | --- |
| Path filter for deploy trigger | `.github/workflows/deploy-agentshq.yml:8` (`thepopebot/chat-ui/**`) |
| Container compose file | `docker-compose.thepopebot.yml` (root) |
| Rebuild workflow | `.github/workflows/rebuild-event-handler.yml` |
| Event handler container | `thepopebot-event-handler` (running on VPS) |

## What does NOT live here

- Main orchestrator code (`orchestrator/`)
- Main agentsHQ skills (`skills/`)
- Agent output (`outputs/` / `agent_outputs/`)

## Rules

- **DO NOT MOVE this folder.** Multi-system path coordination required (3 GH Actions workflows + docker-compose + VPS container restart). A future move to `ui/atlas/` or similar is tracked in `docs/reference/repo-structure.md` Live Mount Points but requires its own dedicated session.
- Runtime data subdirectories (`thepopebot/data/db/`, `thepopebot/data/workspaces/`, `thepopebot/data/clusters/`, `thepopebot/.tmp/`, `thepopebot/logs/`) are gitignored. Never commit them.
- per `feedback_n8n_vps_restrictions.md`: never restart the thepopebot Docker stack from a Claude session. Use the GH Actions workflows or coordinate with Boubacar.

## Cross-references

- Constitution: [`docs/GOVERNANCE.md`](../docs/GOVERNANCE.md)
- Folder Governance: [`docs/AGENT_SOP.md`](../docs/AGENT_SOP.md)
- Live mount inventory: [`docs/reference/repo-structure.md`](../docs/reference/repo-structure.md)
