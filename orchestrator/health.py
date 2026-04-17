import logging
from typing import Dict, List, Any
from datetime import datetime

logger = logging.getLogger("agentsHQ.health")

class HealthRegistry:
    def __init__(self):
        self.checks: Dict[str, Dict[str, Any]] = {}

    def register(self, component: str, status: str, message: str = "", metadata: Dict = None):
        self.checks[component] = {
            "status": status, # "healthy" | "unhealthy" | "missing"
            "message": message,
            "metadata": metadata or {},
            "last_check": datetime.utcnow().isoformat()
        }

    def get_report(self) -> Dict[str, Any]:
        overall = "GREEN"
        if any(c["status"] == "unhealthy" for c in self.checks.values()):
            overall = "RED"
        elif any(c["status"] == "missing" for c in self.checks.values()):
            overall = "YELLOW"
            
        return {
            "overall_status": overall,
            "timestamp": datetime.utcnow().isoformat(),
            "components": self.checks
        }

health_registry = HealthRegistry()
