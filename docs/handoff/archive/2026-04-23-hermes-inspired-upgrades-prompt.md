# Hermes-Inspired Upgrades for agentsHQ: Handoff Prompt

**Paste everything below the line into a new Claude Code session running in `d:\Ai_Sandbox\agentsHQ\`.**

---

## Context

Boubacar runs **agentsHQ**, a personal AI agent system on Windows + a VPS. It already has:

- Auto-memory system (typed: user/feedback/project/reference) at `C:\Users\HUAWEI\.claude\projects\d--Ai-Sandbox-agentsHQ\memory\`
- Per-call LLM cost ledger (`project_token_economy.md`): chairman=Sonnet, reviews on cheap provider-family models, ~$0.05/council run
- Telegram bot interface (dual-bot pattern: agentsHQ + Remoat)
- Router with classification + LLM fallback (`router.py`); router_log shipped 2026-04-22
- ~70+ skills under `~/.claude/skills/` and `agentsHQ/skills/` (canonical location is `agentsHQ/skills/`, copy to `~/.claude/skills/` after)
- VPS-deployed CrewAI orchestrator
- Hard rule: read `docs/AGENT_SOP.md` first every session

A separate Claude session analyzed the **Hermes Agent** (Greg Isenberg podcast w/ Imran Yedwab, posted on X) and identified four upgrades worth shipping. Your job is to spec and implement them. The full Hermes claims and our gap analysis are below: read both before starting.

## Hermes claims, decoded (from Greg's post text)

1. Personal AI agent in your terminal, one-command install
2. Solves three OpenClaw pain points: no memory, gateway restarts, no token visibility
3. Every completed task saved to memory; agent searches past task logs to find solutions
4. Connect to OpenRouter; rotates free models weekly; one founder went $130/5d → $10/5d
5. Preloaded skills: Apple Notes, iMessage, Find My, browser, web search, image gen, cron
6. Connect Obsidian (vault), GStack (dev env), custom skills
7. **Have it write code once for recurring tasks, then run without burning tokens**
8. Run on Android via Telegram; name agents; talk to them like coworkers
9. Run bare metal, Docker, or Modal serverless

## Gap analysis vs agentsHQ

agentsHQ already matches or exceeds Hermes on: memory (typed > episodic-only), cost ledger (already shipped), Telegram (already shipped), tool surface (~70 skills > 40). Don't rebuild those.

The four real gaps Hermes exposes:

### Upgrade A: Promotion gate: recurring LLM tasks → deterministic scripts (HIGHEST ROI)

**Problem:** When the same task (scrape, report, classification, sync) runs through an LLM 3+ times with similar input/output shape, we're paying tokens to redo deterministic work. Hermes's framing: "stop paying an LLM to do the same scrape or report daily."

**Spec the build:**
- Detect recurrence in `router_log` (group by task signature: input shape + skill called + output shape over rolling 14 days)
- Surface candidates above a threshold (e.g., 3+ runs, total cost > $0.10, >80% output structural similarity)
- New skill `promote-to-script` that takes a candidate, generates a deterministic Python script for the deterministic parts, keeps the LLM as fallback only for the non-deterministic parts (e.g., summarization step inside an otherwise-scripted scrape)
- Log promotions back to `router_log` so future runs route to the script first

**Where it lives:** `orchestrator/promotion_gate.py` (detector) + `agentsHQ/skills/promote-to-script/` (the promotion workflow)

**Existing patterns to fit into:** `orchestrator/router.py`, `orchestrator/research_engine.py`, the router_log table. Don't create parallel structures: read the existing schema first.

**Highest-value first targets:** `clone-scout`, `clone-builder`, daily content board reorder pipeline. All are repeatable enough that 70-90% of their inner loop can be deterministic.

### Upgrade B: Episodic task log with retrieval

**Problem:** Auto-memory is typed (good for facts/preferences/state) but doesn't capture "what did I do last time I had a task like this." Hermes does episodic: every completed task with its solution path.

**Spec the build:**
- Extend the existing `router_log` (or add a sibling `task_outcomes` table) with `{task_signature, plan_summary, outcome, total_cost_usd, completed_at, success_bool}`
- Add a helper `find_similar_completed_tasks(signature, k=5)` that grep/embedding-searches the table
- Wire into the council/crew kickoff: before planning, retrieve top-k similar past tasks and inject the plan summary into the chairman's context
- Keep it small: no vector DB yet; start with FTS or trigram similarity on signatures

**Where it lives:** Supabase (per `feedback_no_airtable.md`: Supabase is the only DB). Migration in `db/migrations/`. Helper in `orchestrator/episodic_memory.py`.

**Don't:** rebuild auto-memory. This is complementary, not a replacement.

### Upgrade C: OpenRouter free-tier tier in router

**Problem:** Router today picks per-model class (Sonnet chairman, cheap reviews). Hermes-specific trick: opportunistically route to whatever's free this week on OpenRouter for non-critical tasks.

**Spec the build:**
- Add a new lowest-priority routing tier in `router.py`: `OPENROUTER_FREE`
- Eligible task classes: scraping summarization, low-stakes classification, content board metadata enrichment: NOT council reviews, NOT chairman, NOT anything that touches client deliverables
- Weekly cron pulls OpenRouter's free model list (their API exposes `pricing: {prompt: 0, completion: 0}`)
- Caches the free list in env or a config table; router consults the cache
- Fallback to current cheap tier if no free model available

**Don't break:** the 5 router rules in `feedback_llm_routing_architecture.md`. Read that memory first.

### Upgrade D: Coworker-name aliases on Telegram

**Problem:** Skills are addressed by function name ("clone-scout"). Hermes's UX is "named coworkers": DMing a person, not invoking a function.

**Spec the build:**
- Add an alias map in the Telegram bot: `{"Hermes": "general assistant", "Scout": "clone-scout", "Builder": "clone-builder", ...}`
- When a Telegram message starts with `@<Name>`, route to the mapped crew/skill
- Keep function-name routing as the fallback
- Persona file per name (1-2 sentence backstory, response tone) injected into system prompt

**Lowest priority of the four. Polish, not leverage.**

## What NOT to do

- Don't add Apple Notes / iMessage / Find My skills: Boubacar is on Windows + VPS
- Don't loosen the skill build filter (Sankofa Council gate) to chase Hermes's 40+ tools: agentsHQ already has more, and gating is a feature not a bug
- Don't add a "one-command install": agentsHQ is personal, not a distribution
- Don't touch n8n Docker / VPS infrastructure (hard rule, see `feedback_n8n_vps_restrictions.md`)

## Hard project rules (read before any code)

These are in agentsHQ's auto-memory and override default behavior:

- **No em dashes anywhere.** Pre-commit hook enforces. Rewrite the sentence.
- **No swearing**, including soft swears. Use heck/dang/darn.
- **Supabase is the only DB.** Never suggest Airtable.
- **Save point before big changes**: `nsync` and create a named git tag.
- **Always build both skill AND CrewAI crew**, unless told otherwise.
- **Subagent-driven execution** by default: never ask, just choose it.
- **CLI before MCP**: try gws/gh/autocli CLIs first; MCP is fallback (autocli was renamed from opencli-rs at v0.2.4).
- **Permanent fix over patch** when time allows.
- **Read `docs/AGENT_SOP.md` first.** No exceptions.

## Suggested execution order

1. Read `docs/AGENT_SOP.md` and the memory files referenced above (`project_token_economy.md`, `project_memory_architecture.md`, `feedback_llm_routing_architecture.md`, `project_telegram_polling_architecture.md`)
2. Use the `superpowers:brainstorming` skill on **Upgrade A** first: that's the highest-ROI item
3. Get Boubacar's design approval, then `superpowers:writing-plans`, then implement
4. Save point + git tag before each upgrade ships
5. After A ships, repeat for B → C → D in priority order

Don't bundle. New branch per upgrade (`feedback_new_branch_per_feature.md`).

## Success criteria

- **A:** First promoted script runs in production; before/after token cost on the same task class shows >70% reduction; promotion-gate detector emits at least one new candidate per week
- **B:** Council kickoff context includes "similar past tasks" section; at least one council run cites a retrieved past task in its plan
- **C:** At least one task class routes to a free OpenRouter model in production; weekly free-list refresh cron is green; no regressions in council quality (measured by review pass rate)
- **D:** Telegram routing by `@Name` works for at least 5 named coworkers; fallback to function name still works

## Questions to ask Boubacar before starting

- For Upgrade A: which 2-3 task classes should be the first promotion targets? (default: clone-scout inner loop, content board reorder, daily research engine summarization)
- For Upgrade B: SQLite local cache or Supabase table? (default: Supabase, per the no-Airtable rule and existing pattern)
- For Upgrade C: which task classes are *eligible* for free-tier routing? (default: scraping summarization, content metadata enrichment, low-stakes classification)
- For Upgrade D: ship names, or just the routing mechanism and let Boubacar name them? (default: ship the mechanism with 3 starter names: Scout, Builder, Hermes)
