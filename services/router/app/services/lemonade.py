import httpx
from app.core.config import settings
from typing import Dict, List, Any

class LemonadeClient:
    def __init__(self, base_url: str = settings.LEMONADE_SERVER_URL):
        self.base_url = base_url

    async def get_health(self) -> bool:
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(f"{self.base_url}/api/v1/health", timeout=2.0)
                return response.status_code == 200
        except Exception:
            return False

    async def get_stats(self) -> Dict[str, Any]:
        """Fetch real-time performance metrics."""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(f"{self.base_url}/api/v1/stats", timeout=2.0)
                response.raise_for_status()
                return response.json()
        except Exception:
            return {}

    async def get_system_info(self) -> Dict[str, Any]:
        """Fetch hardware availability (iGPU, dGPU, NPU) and memory pressure."""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(f"{self.base_url}/api/v1/system-info", timeout=2.0)
                response.raise_for_status()
                return response.json()
        except Exception:
            return {}

    async def list_models(self) -> List[str]:
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(f"{self.base_url}/api/v1/list", timeout=2.0)
                response.raise_for_status()
                return response.json().get("models", [])
        except Exception:
            return []

lemonade_client = LemonadeClient()
