import sys
import os

# Insert paths to orchestrator
sys.path.insert(0, 'd:/Ai_Sandbox/agentsHQ/orchestrator')

from dotenv import load_dotenv
# Load root .env
load_dotenv('d:/Ai_Sandbox/agentsHQ/.env')

from council import SankofaCouncil

query = """
We have proposed four strategic weekend enhancements to run in parallel with the main M23 (Agent-to-Agent Spawning) and M24 (Hermes Self-Healing) builds:

1. **Highlight A: Echo M1 Slash Commands (`/propose`, `/ack`, `/reject`)**
   - Goal: Build the public commands, `.claude/commands/propose.md` shims, and wire them to Telegram interactive messages for single-keystroke approvals of Hermes/swarms.
   - Files involved: `orchestrator/handlers_commands.py`, `orchestrator/proposal.py`, Telegram command router.
   - Branch: `feat/echo-m1-slash-commands`

2. **Highlight B: Atlas M19 Native CRM Board (`/crm`)**
   - Goal: Build Fastify backend endpoints (`GET /atlas/crm/board`, `POST /atlas/crm/leads/<id>/status`) and React Kanban-style board in the Atlas frontend, reading directly from Supabase, as the Notion sync is now severed.
   - Files involved: `orchestrator/atlas_dashboard.py`, `ui/src/components/CrmBoard.tsx` (frontend).
   - Branch: `feat/atlas-m19-crm-board`

3. **Highlight C: Studio M3.4 Scene Motion Upgrade (Ken Burns → Video)**
   - Goal: Modify `studio_visual_generator.py` and `studio_render_publisher.py` to allow mixed motion. Scenes 0 & 5 use Kling/Seedance video; Scenes 1-4 use Ken Burns still clips.
   - Files involved: `orchestrator/studio_visual_generator.py`, `orchestrator/studio_render_publisher.py`, `orchestrator/studio_scene_builder.py`.
   - Branch: `feat/studio-m3.4-scene-motion`

4. **Highlight D: Compass M6 Configuration Audit**
   - Goal: Static review of `settings.json`, `CLAUDE.md`, and MCP servers list to lock down permissions, restrict file operations within workspace, and prevent runaway loops before Hermes gets write permissions.
   - Files involved: `config/settings.json`, `CLAUDE.md`, `.vscode/settings.json`.
   - Branch: `feat/compass-m6-audit`

### Strategic Questions for the Council:
1. **Parallelism & Concurrency:** Can these run in parallel to the main M23 and M24 builds without state, file-locking, or database conflicts?
2. **Structural Correctness:** Are the designs robust, minimal, and aligned with agentsHQ design principles?
3. **Claude Code Prompts:** Are the proposed CC prompts strong enough to execute without hallucinations or architectural regressions?
"""

# Context from our roadmap analysis
try:
    with open("C:/Users/HUAWEI/.gemini/antigravity/brain/f7a17189-423a-4d0d-b366-b4470ad1b492/roadmap_analysis.md", "r", encoding="utf-8") as f:
        context = f.read()
except Exception as e:
    context = f"Error reading roadmap analysis: {e}"

print("Invoking Sankofa Council on Weekend Proposals & Prompts...")
council = SankofaCouncil()
result = council.run(
    query=query,
    context=context,
    task_type="consulting_deliverable"
)

# Output results so the model can read them
print("\n=== CHAIRMAN SYNTHESIS ===")
print(result["chairman_synthesis"])
print("\n=== NEXT STEP ===")
print(result["next_step"])
print("\n=== OPEN QUESTION ===")
print(result["open_question"])
print("\n=== HTML REPORT PATH ===")
print(result["html_file_path"])
