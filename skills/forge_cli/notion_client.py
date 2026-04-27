import time
import httpx
from typing import Any, Dict, List, Optional


class NotionClient:
    """Rate-limited Notion API client. Max 3 requests/second."""

    BASE_URL = "https://api.notion.com/v1"

    def __init__(self, secret: str, version: str = "2022-06-28"):
        self.headers = {
            "Authorization": f"Bearer {secret}",
            "Content-Type": "application/json",
            "Notion-Version": version,
        }
        self._last_request_time = 0.0
        self._min_interval = 0.34  # ~3 req/sec

    def _throttle(self):
        elapsed = time.time() - self._last_request_time
        if elapsed < self._min_interval:
            time.sleep(self._min_interval - elapsed)
        self._last_request_time = time.time()

    def _request(self, method: str, endpoint: str, **kwargs) -> Dict[str, Any]:
        self._throttle()
        url = f"{self.BASE_URL}/{endpoint}"
        with httpx.Client(timeout=30.0) as client:
            response = getattr(client, method)(url, headers=self.headers, **kwargs)
            if response.status_code == 429:
                retry_after = int(response.headers.get("Retry-After", 1))
                time.sleep(retry_after)
                response = getattr(client, method)(url, headers=self.headers, **kwargs)
            response.raise_for_status()
            return response.json()

    def create_page(self, database_id: str, properties: Dict, children: Optional[List] = None) -> Dict:
        payload = {"parent": {"database_id": database_id}, "properties": properties}
        if children:
            payload["children"] = children
        return self._request("post", "pages", json=payload)

    def update_page(self, page_id: str, properties: Dict) -> Dict:
        return self._request("patch", f"pages/{page_id}", json={"properties": properties})

    def query_database(self, database_id: str, filter_obj: Optional[Dict] = None, sorts: Optional[List] = None) -> List[Dict]:
        payload = {}
        if filter_obj:
            payload["filter"] = filter_obj
        if sorts:
            payload["sorts"] = sorts
        result = self._request("post", f"databases/{database_id}/query", json=payload)
        return result.get("results", [])

    def get_page(self, page_id: str) -> Dict:
        return self._request("get", f"pages/{page_id}")

    def get_database_schema(self, database_id: str) -> Dict[str, Dict]:
        """Return the properties map for a database: {property_name: {id, type, ...}}.

        Used by writers that need to discover property types at runtime so they
        can skip fields that don't exist on a given database.
        """
        result = self._request("get", f"databases/{database_id}")
        return result.get("properties", {})

    def get_page_blocks(self, page_id: str) -> str:
        """Fetch all block children for a page and return them as plain text."""
        result = self._request("get", f"blocks/{page_id}/children", params={"page_size": 100})
        blocks = result.get("results", [])
        lines = []
        for block in blocks:
            btype = block.get("type", "")
            data = block.get(btype, {})
            rich = data.get("rich_text", [])
            text = "".join(seg.get("plain_text", "") for seg in rich)
            if text:
                lines.append(text)
        return "\n\n".join(lines)

    def append_blocks(self, block_id: str, children: List[Dict]) -> Dict:
        return self._request("patch", f"blocks/{block_id}/children", json={"children": children})

    def update_block(self, block_id: str, payload: Dict) -> Dict:
        return self._request("patch", f"blocks/{block_id}", json=payload)
