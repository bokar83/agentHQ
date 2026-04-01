import json
import subprocess
import os
from typing import List, Dict, Optional

class CLIHubTool:
    def __init__(self, registry_path: str):
        self.registry_path = registry_path
        self._load_registry()

    def _load_registry(self):
        with open(self.registry_path, "r") as f:
            self.data = json.load(f)
        self.clis = self.data.get("clis", [])

    def list_clis(self, category: Optional[str] = None) -> List[Dict]:
        """List all available CLIs, optionally filtered by category."""
        if category:
            return [cli for cli in self.clis if cli.get("category") == category]
        return self.clis

    def search_cli(self, query: str) -> List[Dict]:
        """Search for a CLI by name or description."""
        query = query.lower()
        results = []
        for cli in self.clis:
            if query in cli["name"].lower() or query in cli["description"].lower():
                results.append(cli)
        return results

    def get_install_instruction(self, cli_name: str) -> str:
        """Get the installation command for a specific CLI."""
        for cli in self.clis:
            if cli["name"] == cli_name:
                return cli["install_cmd"]
        raise ValueError(f"CLI '{cli_name}' not found in registry.")

    def install_cli(self, cli_name: str) -> Dict:
        """Execute the installation command for a CLI."""
        try:
            cmd = self.get_install_instruction(cli_name)
            # Use shell=True because some install commands might involve 'cd' or '&&'
            result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
            if result.returncode == 0:
                return {
                    "status": "success",
                    "message": f"Successfully installed {cli_name}.",
                    "output": result.stdout
                }
            else:
                return {
                    "status": "failed",
                    "message": f"Failed to install {cli_name}.",
                    "error": result.stderr
                }
        except Exception as e:
            return {"status": "error", "message": str(e)}

# Exported function for the tool registry
async def execute_cli_hub_action(action: str, **kwargs):
    registry_path = os.path.join("d:\\Ai_Sandbox\\agentsHQ\\external\\CLI-Anything", "registry.json")
    hub = CLIHubTool(registry_path)
    
    if action == "list":
        return hub.list_clis(kwargs.get("category"))
    elif action == "search":
        return hub.search_cli(kwargs.get("query", ""))
    elif action == "install":
        return hub.install_cli(kwargs.get("name", ""))
    else:
        return {"error": f"Unknown action: {action}"}
