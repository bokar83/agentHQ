# Session Handoff - ui-ux-pro-max Python Toolchain Absorb - 2026-05-02

## TL;DR
Absorbed `nextlevelbuilder/ui-ux-pro-max-skill` v2.5.0. The skill was already installed globally but had broken text-stub data/scripts entries (global install artifact: no Python toolchain on disk). Replaced both stubs with real directories (31 CSVs + 3 Python files). Verified the design system generator works from the global skill path. Mirrored to agentsHQ local copy. Added HARD RULE to SKILL.md so future agents auto-invoke the script instead of reasoning from static tables.

## What was built / changed
- `C:/Users/HUAWEI/.claude/skills/ui-ux-pro-max/data/`: replaced text stub with real dir (31 CSV files)
- `C:/Users/HUAWEI/.claude/skills/ui-ux-pro-max/scripts/`: replaced text stub with real dir (search.py, core.py, design_system.py)
- `D:/Ai_Sandbox/agentsHQ/skills/ui-ux-pro-max/data/`: same mirror
- `D:/Ai_Sandbox/agentsHQ/skills/ui-ux-pro-max/scripts/`: same mirror
- `C:/Users/HUAWEI/.claude/skills/ui-ux-pro-max/SKILL.md`: added HARD RULE block (run generator before any UI code)
- `D:/Ai_Sandbox/agentsHQ/skills/ui-ux-pro-max/SKILL.md`: synced
- `memory/reference_design_skills.md`: updated to v2.5.0, added invoke patterns
- `docs/reviews/absorb-log.md`: appended PROCEED entry
- `docs/reviews/absorb-followups.md`: appended follow-up entry
- Sandbox clone at `d:/Ai_Sandbox/agentsHQ/sandbox/.tmp/nextlevelbuilder-ui-ux-pro-max-skill/`: read-only, can be deleted

## Decisions made
- **Global install is SKILL.md-only by design**: the upstream CLI never copies data/ on global install; must be done manually from a clone
- **No alias/shortcut created**: Boubacar confirmed agents should invoke the script transparently; user just says "design xyz website"
- **VPS sync deferred**: Karpathy WARN: decide scope explicitly before touching VPS `/root/.claude/skills/ui-ux-pro-max/`
- **agentsHQ/skills/ is the secondary mirror**: global `~/.claude/skills/` is canonical

## What is NOT done (explicit)
- VPS sync (`/root/.claude/skills/ui-ux-pro-max/data/` and `scripts/`): deferred, needs explicit decision
- Sandbox clone not deleted: harmless, lives at `sandbox/.tmp/nextlevelbuilder-ui-ux-pro-max-skill/`
- Karpathy WARN 2 open: "script callable" != "script actually invoked in real sessions": verify in a future SW website build

## Open questions
- Should VPS get the Python toolchain too? Only matters if orc-crewai agents invoke the skill directly (unlikely today)

## Next session must start here
1. Next UI/UX task: just say "design X website": agent should auto-run `python3 ~/.claude/skills/ui-ux-pro-max/scripts/search.py "<industry>" --design-system` before writing any code
2. If VPS sync is needed: `scp -r C:/Users/HUAWEI/.claude/skills/ui-ux-pro-max/data root@agentshq.boubacarbarry.com:/root/.claude/skills/ui-ux-pro-max/` and same for scripts/
3. Delete sandbox clone when convenient: `rm -rf d:/Ai_Sandbox/agentsHQ/sandbox/.tmp/nextlevelbuilder-ui-ux-pro-max-skill/`

## Files changed this session
- `C:/Users/HUAWEI/.claude/skills/ui-ux-pro-max/data/` (new real directory)
- `C:/Users/HUAWEI/.claude/skills/ui-ux-pro-max/scripts/` (new real directory)
- `C:/Users/HUAWEI/.claude/skills/ui-ux-pro-max/SKILL.md` (HARD RULE added)
- `D:/Ai_Sandbox/agentsHQ/skills/ui-ux-pro-max/data/` (mirrored)
- `D:/Ai_Sandbox/agentsHQ/skills/ui-ux-pro-max/scripts/` (mirrored)
- `D:/Ai_Sandbox/agentsHQ/skills/ui-ux-pro-max/SKILL.md` (synced)
- `C:/Users/HUAWEI/.claude/projects/d--Ai-Sandbox-agentsHQ/memory/reference_design_skills.md`
- `d:/Ai_Sandbox/agentsHQ/docs/reviews/absorb-log.md`
- `d:/Ai_Sandbox/agentsHQ/docs/reviews/absorb-followups.md`
