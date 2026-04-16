import sys
import os

sys.path.insert(0, 'd:/Ai_Sandbox/agentsHQ/orchestrator')

from dotenv import load_dotenv
load_dotenv('d:/Ai_Sandbox/agentsHQ/infrastructure/.env')

from council import SankofaCouncil

# Load the generated files
artifact_dir = "C:/Users/HUAWEI/.gemini/antigravity/brain/fccdec77-6ff1-4465-bf1c-d1d4e13e548d/artifacts"
try:
    with open(f"{artifact_dir}/ai_governance_report.md", "r", encoding="utf-8") as f:
        doc1 = f.read()
except FileNotFoundError:
    doc1 = "Document 1 not found."

try:
    with open(f"{artifact_dir}/ai_governance_toolkit.md", "r", encoding="utf-8") as f:
        doc2 = f.read()
except FileNotFoundError:
    doc2 = "Document 2 not found."

query = """
Review the attached AI Governance framework and toolkit. Please focus specifically on me (Boubacar Barry) and Catalyst Works Consulting. 
How does this material specifically help me to create revenue? 
How can I be a differentiator and set myself apart from others? 
How do I establish myself as the undisputed expert and the go-to person for AI governance? 
Crucially, how can I use AI Governance work as a 'foot in the door' to lead into broader consulting engagements around 'margin erosion' and operational leverage?
"""

context = f"--- DOCUMENT 1: AI Governance Foundation ---\n{doc1}\n\n--- DOCUMENT 2: AI Governance Toolkit ---\n{doc2}"

print("Invoking Sankofa Council...")
council = SankofaCouncil()
result = council.run(
    query=query,
    context=context,
    task_type="consulting_deliverable"
)

# Output results so the agent can read them
print("--- CHAIRMAN SYNTHESIS ---")
print(result["chairman_synthesis"])
print("\n--- NEXT STEP ---")
print(result["next_step"])
print("\n--- OPEN QUESTION ---")
print(result["open_question"])
print("\n--- HTML REPORT PATH ---")
print(result["html_file_path"])
