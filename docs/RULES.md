# Standing Rules for VPS Agents (RULES.md)

**Purpose:** VPS orchestrator container (`orc-crewai`) has no auto-memory access. This file = the curated subset of standing rules every autonomous agent on VPS must apply at every action boundary.

**Mounted at:** `/app/docs/RULES.md` (volume-mounted via `docker-compose.yml`).

**Updated by hand.** Not auto-synced from `~/.claude/projects/d--Ai-Sandbox-agentsHQ/memory/`. Boubacar curates this list. Last updated: 2026-05-11.

**Read this before any action.** This is referenced from every `AGENTS.md` and every CrewAI agent `backstory`. If the rule is not here, but you see it referenced elsewhere, ask before acting.

---

## 1. Email sending (immediate-external — wrong action is unrecoverable)

- **NEVER send an email without explicit per-batch authorization.** "Send this email" / "ship it" / "go ahead and send" / "fire it" only. Approval for one batch does NOT carry to the next.
- **Outbound CW = `boubacar@catalystworks.consulting`.** Path: cw OAuth + direct Gmail API (`/app/secrets/gws-oauth-credentials-cw.json` → oauth2/token → gmail/v1/users/me/messages/send). NOT gws CLI (rewrites From).
- **Always verify after send.** GET `gmail/v1/users/me/messages/<id>` and assert From-header. `labelIds:[SENT]` alone is NOT proof.
- **Email both addresses for internal sends to Boubacar:** `bokar83@gmail.com` AND `boubacar@catalystworks.consulting`. One comma-separated To.
- **Signal Works inbound replies go to `signal@catalystworks.consulting`** (alias routes to boubacar@). signal@ is NOT a valid From — Gmail rewrites it.

## 2. Deliverable format (deferred-visible — Boubacar will notice)

- **Final human-facing deliverables = HTML, served via localhost.** Anything Boubacar will review with his eyes. Reports, audits, briefings, memos, analysis docs, roadmap snapshots.
- **Agent-internal docs = MD.** Planning, version-controlled specs, registry logs, handoffs, skill source files.
- **Multi-step research / batch sessions = HTML email digest at close,** even if not asked. Email to both Boubacar inboxes via canonical cw OAuth path. See rule 1.
- **No Loom proposals.** HyperFrames pitch reel, screen-recorded MP4, or no video.

## 3. Content + brand (deferred-invisible — silent drift kills brand)

- **Never use the literal 3-letter acronym for First Generation Money.** Always "1stGen" or "1stGen Money". Channel code = `1stGen`.
- **First name only in published content.** "Boubacar" — not "Boubacar Barry" — in signature, byline, body.
- **Boubacar = Guinean, capital = Conakry.** Never Senegal/Dakar in cultural content.
- **Verified stats only.** Every stat in published content needs a source URL captured in Notion before publish.
- **No fabricated stories attributed to Boubacar.** No invented client scenes, no fake $X figures, no "last quarter I..." without his explicit input. Hypotheticals are OK ONLY if labeled "imagine X" / "consider Y" / "hypothetically." Real client stories require explicit Boubacar input.
- **No em dashes anywhere.** Not `--`, not `: `. Rewrite the sentence.

## 4. Git + commits (immediate-external — breaks coordination)

- **Push to main goes through Gate only.** Coding agents commit to feature branches, push with `[READY]` in commit message, then move on.
- **`git pull` does NOT reload Python modules in running container.** Always `docker compose restart orchestrator` after pulls touching `*.py`.
- **No `git filter-repo` while live remote branches exist.** Rotate secrets + bypass URL instead.
- **Hermes / autonomous committers: never `git add .`.** Use explicit safe paths only. `.env` push risk.
- **No --no-verify, no --no-gpg-sign** unless Boubacar explicitly asks.

## 5. Coordination (immediate-internal — breaks multi-agent flow)

- **Claim before edit. Complete after.** `from skills.coordination import claim, complete`. Use `try/finally: complete()` pattern. Phantom locks block other agents until reaped.
- **Coding agents push with `[READY]` in commit message.** Gate watches GitHub every 5 min. No manual signal needed.
- **Direct sessions (Boubacar present):** claim branch + file, skip [READY] commit + push (Boubacar pushes).

## 6. Asset + file discipline (immediate-internal — unrecoverable losses)

- **"Delete" is retired.** Move to `zzzArchive/<batch-name>/<original/path/>/` with MANIFEST.md line. Reversible.
- **Drive uploads via `gws drive files create`.** Set `anyone with link` reader for any file linked in outbound email. Use `orchestrator.drive_publish.publish_public_file()`.
- **Files live in `D:\Ai_Sandbox\agentsHQ`** (local) or `/root/agentsHQ` (VPS). Never C:.
- **No iteration artifacts at repo root.** Use `workspace/scratch/<topic>/` or `deliverables/<scope>/iterations/`.

## 7. Cost + safety (immediate-external — financial)

- **New hook/skill/heartbeat that makes LLM calls = canary checklist.** (a) which model + context size, (b) cost per firing at that context, (c) worst-case firing rate, (d) kill switch. If (b) × (c) > $0.10/min, do not register.
- **Global config writes** (`~/.claude/settings.json`, `~/.codex/config.toml`) require isolated test before any hook registration.
- **Pre-Write check (per CLAUDE.md 2026-05-11):** before any `Write` or `Edit` under `docs/`, `agent_outputs/`, `clients/`, `output/`, or date-stamped paths, state in chat: "Is this Boubacar-facing? If yes, format = HTML + localhost + email-if-important." Skipped gate = log violation to `docs/audits/memory-enforcement-violations.md`.

## 8. Hermes write boundaries (constitutional)

ALLOWED writes: `agent_outputs/`, `workspace/`, `docs/audits/`, `data/changelog.md`, `docs/roadmap/*.md` (append-only session log entries).

FORBIDDEN writes: `CLAUDE.md`, `AGENTS.md`, `docs/AGENT_SOP.md`, `docs/GOVERNANCE.md`, `docs/governance.manifest.json`, `.claude/settings.json`, `.vscode/settings.json`, `config/settings.json`, `.pre-commit-config.yaml`, `scripts/*.py`, `secrets/`, `.env`, `.env.*`, `orchestrator/*.py`, `skills/coordination.py`, `docs/RULES.md` (this file).

Wildcard rule: no `"*"` glob in any write/edit/delete.

---

## Why this file exists

2026-05-11 RCA confirmed VPS orchestrator container has zero memory loading. 166 feedback files in `~/.claude/projects/.../memory/` are invisible to VPS agents. Boubacar's directive: enforce memory usage on VPS without context bloat. Curated standing rules = the smallest sufficient set.

If a rule belongs here but is missing, surface it in chat. Do not edit this file unless Boubacar approves.

## Reference

Full memory index (local-only, do not load on VPS): `~/.claude/projects/d--Ai-Sandbox-agentsHQ/memory/MEMORY.md`.
Latest constitutional CLAUDE.md: `/app/CLAUDE.md`.
Latest AGENT_SOP.md: `/app/docs/AGENT_SOP.md`.
RCA: `/app/docs/handoff/2026-05-11-memory-enforcement-gap-rca.md` (when written).
