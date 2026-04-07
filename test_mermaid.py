import json
import logging

import importlib.util
import sys

# Load from absolute path
spec = importlib.util.spec_from_file_location("mermaid_diagrammer", "d:/Ai_Sandbox/agentsHQ/skills/mermaid_diagrammer/skill.py")
module = importlib.util.module_from_spec(spec)
sys.modules["mermaid_diagrammer"] = module
spec.loader.exec_module(module)

mermaid_tool = module.mermaid_tool

mermaid_code = """
flowchart TD
    User([Telegram / HTTP]) --> Router[Router Agent]
    Router -->|Match found| Classify{Identify Task Type}
    
    Classify -- "website_build" --> CrewWeb[Web Builder Crew]
    Classify -- "app_build" --> CrewApp[App Builder Crew]
    Classify -- "consulting_deliverable" --> CrewConsult[Sankofa Council / Consulting]
    Classify -- "hunter_task" --> CrewHunter[Hunter Agent]
    Classify -- "Unknown" --> Escalation[Escalate to Boubacar via Telegram]
    
    CrewWeb --> Output[Deliverable + Save to /outputs/]
    CrewApp --> Output
    CrewConsult --> Output
    CrewHunter --> Output
    
    Output --> MemoryStore[(Qdrant Vector DB)]
    Output --> Archiver[(PostgreSQL)]
"""

payload = json.dumps({
    "mermaid_code": mermaid_code,
    "output_format": "png"
})

res = mermaid_tool._run(payload)
print(res)
