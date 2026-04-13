import os
import sys
import logging

# Ensure agentsHQ root is in path
root_dir = r"D:\Ai_Sandbox\agentsHQ"
if root_dir not in sys.path:
    sys.path.append(root_dir)
    sys.path.append(os.path.join(root_dir, "orchestrator"))

# Set working directory to root
os.chdir(root_dir)

# Mocking some environment variables if needed (orchestrator expects them)
os.environ["AGENTS_ROOT"] = root_dir
os.environ["AGENTS_OUTPUT_DIR"] = os.path.join(root_dir, "output")

from orchestrator.orchestrator import run_orchestrator

task = (
    "Use the 'launch_vercel_app' tool to deploy the 'practice-runner' app to PRODUCTION. "
    "The local folder is at 'output/apps/practice-runner-app'. "
    "Ensure all local changes are pushed to GitHub 'bokar83/practice-runner-app' "
    "and that the Vercel deployment is promoted to PRODUCTION. "
    "Final deliverable: The live production URL."
)

print(f"Triggering Orchestrator for task: {task}...")

try:
    result = run_orchestrator(task, from_number="system", session_key="deploy_trigger")
    print("\n--- ORCHESTRATOR RESULT ---")
    if result.get("success"):
        print(f"SUCCESS: {result.get('deliverable', 'No deliverable returned')}")
    else:
        print(f"FAILED: {result.get('result', 'Unknown error')}")
except Exception as e:
    print(f"CRITICAL ERROR: {str(e)}")
