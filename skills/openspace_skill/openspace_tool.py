import os
import asyncio
from typing import Dict, Any, Optional
from openspace.tool_layer import OpenSpace, OpenSpaceConfig
from crewai.tools import BaseTool
import logging

logger = logging.getLogger(__name__)

class OpenSpaceTool(BaseTool):
    """
    Wrapper for the OpenSpace Self-Evolving Skill system.
    This tool allows agents to trigger self-evolution or skill repair.
    """
    name: str = "openspace_tool"
    description: str = (
        "OpenSpace Self-Evolution engine. Use this to 'evolve' a skill from a task result "
        "or 'fix_skill' if a specific skill is broken. "
        "Evolution happens automatically in the background, but can be triggered manually if needed."
    )
    
    _openspace_instance: Optional[OpenSpace] = None

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # Initialization happens on first run or via a setup method

    async def _get_instance(self) -> OpenSpace:
        if not self._openspace_instance:
            # Configure OpenSpace for agentsHQ
            config = OpenSpaceConfig(
                llm_model=os.environ.get("OPENSPACE_MODEL", "google/gemini-2.0-flash-001"),
                skill_evolver_model="google/gemini-2.0-flash-001", # Cheap model for evolution
                workspace_dir=os.path.abspath("./outputs/openspace_workspace"),
                recording_log_dir=os.path.abspath("./logs/recordings"),
            )
            
            # Point to agentsHQ skill directories
            os.environ["OPENSPACE_HOST_SKILL_DIRS"] = os.path.abspath("./skills")
            
            self._openspace_instance = OpenSpace(config)
            await self._openspace_instance.initialize()
            
        return self._openspace_instance

    def _run(self, command: str, **kwargs) -> str:
        # CrewAI 0.28+ uses sync _run, but OpenSpace is async.
        # We use a helper to run async in sync context if needed, 
        # but in our orchestrator we prefer async.
        loop = asyncio.get_event_loop()
        if loop.is_running():
            # Schedule the task
            future = asyncio.run_coroutine_threadsafe(self.execute_async(command, **kwargs), loop)
            return "Evolution scheduled in the background."
        else:
            return asyncio.run(self.execute_async(command, **kwargs))

    async def execute_async(self, command: str, **kwargs) -> str:
        instance = await self._get_instance()
        
        if command == "evolve":
            task_instruction = kwargs.get("task_instruction")
            if not task_instruction:
                return "Error: Missing task_instruction for evolution."
            
            # Run the evolution engine on the task
            # OpenSpace.execute handles analysis and evolution internally
            result = await instance.execute(task_instruction)
            evolved = result.get("evolved_skills", [])
            
            if evolved:
                return f"Success: Evolved {len(evolved)} skills: {', '.join([s['name'] for s in evolved])}"
            return "No evolution suggestions generated for this task."
            
        elif command == "fix_skill":
            skill_name = kwargs.get("skill_name")
            error_log = kwargs.get("error_log")
            if not skill_name:
                return "Error: Missing skill_name."
            
            query = f"Fix the skill '{skill_name}' based on this error: {error_log}"
            result = await instance.execute(query)
            return f"Fix attempt complete. Status: {result.get('status')}"
            
        return f"Unknown command: {command}"

# Global instance for easy access
openspace_tool = OpenSpaceTool()
