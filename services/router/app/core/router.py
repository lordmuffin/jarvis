from app.services.observer import observer
from app.core.config import settings
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.db.models import QueryMetric
import logging

logger = logging.getLogger(__name__)

class IntelligentRouter:
    def __init__(self):
        pass

    async def decide_route(self, db: AsyncSession, model_requested: str) -> str:
        """
        Decides whether to route to 'lemonade' (local) or 'cloud'.
        """
        status = observer.get_status()
        
        # 1. Check Health
        if not status["is_healthy"]:
            logger.warning("Lemonade is unhealthy. Routing to Cloud.")
            return "cloud"

        # 2. Check Capacity (Memory Pressure)
        # Assuming system_info has a 'memory_pressure' field 0-100 or 'status'
        sys_info = status.get("system_info", {})
        if sys_info.get("memory_pressure", 0) > 90:
             logger.warning("High Memory Pressure. Routing to Cloud.")
             return "cloud"
             
        # 3. Check TTFT (Time To First Token) Trends
        # Get average TTFT for the last 5 minutes (simplified to last 10 queries for now)
        try:
            result = await db.execute(
                select(QueryMetric.ttft_ms)
                .where(QueryMetric.provider == "lemonade")
                .order_by(QueryMetric.timestamp.desc())
                .limit(10)
            )
            ttfts = result.scalars().all()
            
            if ttfts:
                avg_ttft = sum(ttfts) / len(ttfts)
                if avg_ttft > settings.MAX_TTFT_MS:
                     logger.warning(f"High TTFT ({avg_ttft}ms). Routing to Cloud.")
                     return "cloud"
        except Exception as e:
            logger.error(f"Error checking TTFT stats: {e}")

        # Default to Local
        return "lemonade"

router_logic = IntelligentRouter()
